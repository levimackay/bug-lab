import os
import select
import time
from pathlib import Path

import pytest

from engine.sandbox import SeatbeltSandbox


@pytest.fixture(scope="module")
def sb():
    return SeatbeltSandbox()


@pytest.fixture
def ws(tmp_path):
    (tmp_path / ".buglab").write_text("")
    return tmp_path


def test_runs_python_and_captures_output(sb, ws):
    r = sb.exec(["python", "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)"], cwd=ws)
    assert r.stdout == "out\n" and r.stderr == "err\n" and r.exit_code == 3
    assert r.max_rss_kb > 0 and r.duration_ms >= 0 and not r.timed_out


def test_network_denied_except_localhost(sb, ws):
    code = """
import socket
try:
    socket.create_connection(("1.1.1.1", 80), timeout=2); print("external-ok")
except OSError as e: print("external-blocked")
s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(1)
c = socket.create_connection(s.getsockname()); print("local-ok")
"""
    r = sb.exec(["python", "-c", code], cwd=ws)
    assert "external-blocked" in r.stdout and "local-ok" in r.stdout, r.stderr


def test_home_write_and_read_denied(sb, ws):
    home = Path.home()
    r = sb.exec(["python", "-c", f"open('{home}/buglab-escape','w')"], cwd=ws)
    assert r.exit_code != 0 and "PermissionError" in r.stderr
    assert not (home / "buglab-escape").exists()
    r = sb.exec(["ls", str(home / "Developer")], cwd=ws)
    assert r.exit_code != 0


def test_workspace_write_allowed(sb, ws):
    r = sb.exec(["sh", "-c", "echo hi > out.txt && cat out.txt"], cwd=ws)
    assert r.stdout == "hi\n", r.stderr


def test_timeout_kills_process_group(sb, ws):
    t = time.monotonic()
    r = sb.exec(["sh", "-c", "python -c 'import time; time.sleep(30)' & sleep 30"], cwd=ws, timeout_s=1)
    assert r.timed_out and time.monotonic() - t < 5


def test_fork_bomb_capped(sb, ws):
    r = sb.exec(["python", "-c", "import os\nfor _ in range(200): os.fork()"], cwd=ws, timeout_s=10)
    assert r.exit_code != 0 or r.timed_out


def test_output_capped(sb, ws):
    r = sb.exec(["python", "-c", "print('x' * 3_000_000)"], cwd=ws)
    assert len(r.stdout) <= 1_000_000


def test_c_toolchain_with_asan(sb, ws):
    (ws / "m.c").write_text("#include <stdlib.h>\nint main(){int*a=malloc(4);a[2]=1;return 0;}")
    r = sb.exec(["cc", "-fsanitize=address", "-g", "m.c", "-o", "m"], cwd=ws)
    assert r.exit_code == 0, r.stderr
    r = sb.exec(["./m"], cwd=ws)
    assert "heap-buffer-overflow" in r.stderr


def test_node_available(sb, ws):
    r = sb.exec(["node", "-e", "console.log(1+1)"], cwd=ws)
    assert r.stdout == "2\n"


def test_shell_pty(sb, ws):
    sh = sb.spawn_shell(cwd=ws)
    try:
        time.sleep(0.5)
        os.write(sh.master_fd, b"echo marker-$((6*7)); pwd\n")
        out = b""
        for _ in range(40):
            r, _, _ = select.select([sh.master_fd], [], [], 0.25)
            if r:
                out += os.read(sh.master_fd, 4096)
            if b"marker-42" in out and str(ws).encode() in out:
                break
        assert b"marker-42" in out
        assert str(ws).encode() in out or str(ws.resolve()).encode() in out
    finally:
        sh.kill()
        assert sh.proc.wait(timeout=5) is not None
