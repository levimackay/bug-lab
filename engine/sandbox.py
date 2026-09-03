"""Sandboxed process execution.

Every program Bug Lab runs on behalf of a user (the incident's app, its tests,
the interactive terminal shell) goes through a ``Sandbox``. The only
implementation today is ``SeatbeltSandbox``, which wraps macOS ``sandbox-exec``:
no network except localhost, no writes outside the workspace, no reads of the
user's home directory outside the workspace and the shared Python venv, plus
POSIX resource limits and a hard wall-clock timeout.

There is deliberately no "unsandboxed" implementation. If ``sandbox-exec`` is
missing, ``SeatbeltSandbox`` refuses to construct and the server refuses to
start. Docker / gVisor / a remote microVM would be a second implementation of
the same Protocol.
"""

from __future__ import annotations

import fcntl
import os
import pty
import resource
import shutil
import signal
import struct
import subprocess
import termios
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parent.parent
PY_ENV = ROOT / "var" / "py"


def _sdkroot() -> str:
    """`cc` inside the sandbox is a symlink to the real clang (the xcrun shim
    wants a cache dir outside the workspace), so the SDK path is passed via env."""
    try:
        return subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


SDKROOT = _sdkroot()

OUTPUT_CAP = 1_000_000  # bytes per stream

# Seatbelt profile. Parameters: WORK (the run's workspace), PY (shared venv).
# Reads: everything except /Users, then the workspace and the shared venv are
# re-allowed. (An allowlist of system paths aborts dyld on this macOS; later
# rules win in seatbelt, so allow-all-then-deny-home is the reliable shape.)
# Writes: the workspace and /dev only. Network: localhost only.
PROFILE = r"""
(version 1)
(deny default)
(allow process-exec process-fork process-info*)
(allow signal (target same-sandbox))
(allow sysctl-read)
(allow mach-lookup)
(allow ipc-posix-shm)
(allow file-read*)
(deny file-read* (subpath "/Users"))
(allow file-read-metadata (subpath "/Users"))
(allow file-read* (subpath (param "WORK")) (subpath (param "PY")))
(allow file-write* (subpath (param "WORK")))
(allow file-write* file-ioctl (subpath "/dev"))
(allow network-bind (local ip "localhost:*"))
(allow network-inbound (local ip "localhost:*"))
(allow network-outbound (remote ip "localhost:*"))
"""


@dataclass(frozen=True)
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    timed_out: bool
    max_rss_kb: int

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


@dataclass(eq=False)
class ShellProcess:
    proc: subprocess.Popen
    master_fd: int

    def resize(self, cols: int, rows: int) -> None:
        fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

    def kill(self) -> None:
        _killpg(self.proc)
        try:
            os.close(self.master_fd)
        except OSError:
            pass


class Sandbox(Protocol):
    def exec(
        self,
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_s: int = 30,
        stdin: bytes = b"",
    ) -> ExecResult: ...

    def spawn_shell(self, *, cwd: Path, env: dict[str, str] | None = None, cols: int = 80, rows: int = 24) -> ShellProcess: ...


def _killpg(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _set_limits() -> None:
    # CPU seconds well above any wall-clock timeout we hand out; the wall clock
    # is the real guard, this stops a child that escapes the process group.
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    # ponytail: RLIMIT_NPROC is per-uid on macOS (counts every process the user
    # owns), so a small cap breaks fork() for the sandbox itself. Runaway forks are
    # contained by the process-group SIGKILL on timeout instead.
    resource.setrlimit(resource.RLIMIT_FSIZE, (50_000_000, 50_000_000))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
    # ponytail: RLIMIT_AS is not enforced on macOS; memory is measured (max RSS), not capped.


def base_env(workspace: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    tmp = workspace / ".tmp"
    tmp.mkdir(exist_ok=True)
    env = {
        "PATH": f"{PY_ENV}/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(workspace),
        "TMPDIR": str(tmp),
        "TERM": "xterm-256color",
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
        "VIRTUAL_ENV": str(PY_ENV),
        "SDKROOT": SDKROOT,
        "ASAN_OPTIONS": "detect_leaks=0:symbolize=1:abort_on_error=0",
        "UBSAN_OPTIONS": "print_stacktrace=1",
        "NODE_NO_WARNINGS": "1",
        "BASH_SILENCE_DEPRECATION_WARNING": "1",
    }
    if extra:
        env.update(extra)
    return env


class SeatbeltSandbox:
    def __init__(self, py_env: Path = PY_ENV) -> None:
        if shutil.which("sandbox-exec") is None:
            raise RuntimeError("sandbox-exec not found: Bug Lab only runs code inside a sandbox (macOS seatbelt)")
        if not (py_env / "bin" / "python").exists():
            raise RuntimeError(f"shared python venv missing at {py_env}; run `make setup`")
        self.py_env = py_env

    def _wrap(self, workspace: Path, argv: list[str]) -> list[str]:
        return [
            "sandbox-exec",
            "-D", f"WORK={workspace}",
            "-D", f"PY={self.py_env}",
            "-p", PROFILE,
            *argv,
        ]

    def exec(
        self,
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_s: int = 30,
        stdin: bytes = b"",
    ) -> ExecResult:
        workspace = _workspace_of(cwd)
        start = time.monotonic()
        proc = subprocess.Popen(
            self._wrap(workspace, argv),
            cwd=cwd,
            env=base_env(workspace, env),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            preexec_fn=_set_limits,
        )
        timed_out = threading.Event()

        def on_timeout() -> None:
            timed_out.set()
            _killpg(proc)

        timer = threading.Timer(timeout_s, on_timeout)
        timer.start()
        chunks: dict[str, bytes] = {}

        def pump(name: str, stream) -> None:
            buf = bytearray()
            while True:
                data = stream.read(65536)
                if not data:
                    break
                if len(buf) < OUTPUT_CAP:
                    buf += data[: OUTPUT_CAP - len(buf)]
            chunks[name] = bytes(buf)

        readers = [threading.Thread(target=pump, args=(n, s), daemon=True) for n, s in (("out", proc.stdout), ("err", proc.stderr))]
        for t in readers:
            t.start()
        try:
            proc.stdin.write(stdin)
        except (BrokenPipeError, OSError):
            pass
        finally:
            proc.stdin.close()
        # wait4 gives us rusage for this exact child (max RSS); Popen honours a
        # pre-set returncode and will not reap twice.
        _, status, ru = os.wait4(proc.pid, 0)
        proc.returncode = os.waitstatus_to_exitcode(status)
        timer.cancel()
        for t in readers:
            t.join(timeout=2)
        # A timed-out process may leave grandchildren holding the pipes; the
        # reader threads are daemons and the group was SIGKILLed, so move on.
        return ExecResult(
            stdout=chunks.get("out", b"").decode("utf-8", "replace"),
            stderr=chunks.get("err", b"").decode("utf-8", "replace"),
            exit_code=proc.returncode,
            duration_ms=int((time.monotonic() - start) * 1000),
            timed_out=timed_out.is_set(),
            max_rss_kb=ru.ru_maxrss // 1024,
        )

    def spawn_shell(self, *, cwd: Path, env: dict[str, str] | None = None, cols: int = 80, rows: int = 24) -> ShellProcess:
        workspace = _workspace_of(cwd)
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

        def preexec() -> None:
            _set_limits()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

        shell_env = base_env(workspace, env)
        shell_env["PS1"] = r"%F{blue}%~%f $ "
        proc = subprocess.Popen(
            self._wrap(workspace, ["/bin/zsh", "-f", "-i"]),
            cwd=cwd,
            env=shell_env,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            start_new_session=True,
            preexec_fn=preexec,
            close_fds=True,
        )
        os.close(slave)
        return ShellProcess(proc=proc, master_fd=master)


def _workspace_of(cwd: Path) -> Path:
    """The sandbox boundary is the run workspace, which is the directory that
    carries a ``.buglab`` marker; commands may run in any subdirectory of it."""
    cwd = cwd.resolve()  # seatbelt matches literal paths: /tmp must become /private/tmp
    for p in [cwd, *cwd.parents]:
        if (p / ".buglab").exists():
            return p
    raise ValueError(f"{cwd} is not inside a Bug Lab workspace (no .buglab marker)")
