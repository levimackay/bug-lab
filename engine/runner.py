"""Runs an incident's app, build and tests inside the sandbox and turns raw
output into structured results: per-test outcomes (junit / TAP) and parsed
stack traces (Python, Node, AddressSanitizer)."""

from __future__ import annotations

import re
import shlex
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

from engine.incidents import Incident
from engine.sandbox import ExecResult, Sandbox
from engine.workspace import HIDDEN_DIR

JUNIT_REL = ".buglab/junit.xml"
DEFAULT_TIMEOUT = 60


@dataclass(frozen=True)
class TestResult:
    name: str
    status: str  # passed | failed | error | skipped
    duration_ms: int
    message: str = ""


@dataclass
class TestRun:
    tests: list[TestResult]
    exec: ExecResult
    parse_error: str = ""

    @property
    def summary(self) -> dict[str, int]:
        s = {"passed": 0, "failed": 0, "error": 0, "skipped": 0, "total": len(self.tests)}
        for t in self.tests:
            s[t.status] = s.get(t.status, 0) + 1
        return s

    @property
    def ok(self) -> bool:
        return (
            bool(self.tests)
            and not self.parse_error
            and all(t.status in ("passed", "skipped") for t in self.tests)
            and not self.exec.timed_out
        )

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "summary": self.summary,
            "tests": [asdict(t) for t in self.tests],
            "exec": asdict(self.exec),
            "parse_error": self.parse_error,
        }


@dataclass
class Frame:
    file: str
    line: int
    function: str


@dataclass
class StackTrace:
    kind: str  # python | node | asan | ubsan
    header: str
    frames: list[Frame] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"kind": self.kind, "header": self.header, "frames": [asdict(f) for f in self.frames]}


# --- commands -----------------------------------------------------------------

SYMBOLIZER_NOISE = re.compile(r"^==\d+==WARNING: .*symbolizer.*\n?", re.M)


def _shell(sandbox: Sandbox, ws: Path, cmd: str, timeout_s: int) -> ExecResult:
    r = sandbox.exec(["/bin/sh", "-c", cmd], cwd=ws, timeout_s=timeout_s)
    # Sanitizers cannot spawn atos inside the sandbox; the in-process
    # symbolizer still names functions, so drop the warnings about it.
    if "symbolizer" in r.stderr:
        r = ExecResult(**{**r.__dict__, "stderr": SYMBOLIZER_NOISE.sub("", r.stderr)})
    return r


def _test_cmd(incident: Incident, target: str = "") -> str:
    """The incident's test command plus machine-readable output. ``target`` is
    appended (a path or directory) so the same command can run a subset."""
    base = incident.commands.test
    if incident.language == "python":
        cmd = f"{base} -p no:cacheprovider --junitxml={JUNIT_REL}"
        return f"{cmd} {shlex.quote(target)}" if target else cmd
    if incident.language in ("javascript", "typescript"):
        # `node --test` takes glob patterns, not directories; a file target runs
        # that file, a directory target (or none) runs every *.test.* under it.
        pattern = target if target and Path(target).suffix else f"{target or 'tests'}/**/*.test.*"
        return f"{base} --test-reporter=spec --test-reporter-destination=stdout --test-reporter=junit --test-reporter-destination={JUNIT_REL} {shlex.quote(pattern)}"
    cmd = base  # C: the incident's harness prints TAP on stdout
    return f"{cmd} {shlex.quote(target)}" if target else cmd


def run_app(sandbox: Sandbox, ws: Path, incident: Incident, timeout_s: int = DEFAULT_TIMEOUT) -> ExecResult:
    return _shell(sandbox, ws, incident.commands.run, timeout_s)


def run_build(sandbox: Sandbox, ws: Path, incident: Incident, timeout_s: int = DEFAULT_TIMEOUT) -> ExecResult | None:
    if not incident.commands.build:
        return None
    return _shell(sandbox, ws, incident.commands.build, timeout_s)


def run_tests(sandbox: Sandbox, ws: Path, incident: Incident, target: str = "", timeout_s: int = DEFAULT_TIMEOUT) -> TestRun:
    (ws / ".buglab").mkdir(exist_ok=True)
    junit = ws / JUNIT_REL
    junit.unlink(missing_ok=True)
    result = _shell(sandbox, ws, _test_cmd(incident, target), timeout_s)
    return _collect(incident, ws, result)


def run_hidden_tests(sandbox: Sandbox, ws: Path, incident: Incident, timeout_s: int = DEFAULT_TIMEOUT) -> TestRun:
    """Assumes ``workspace.hidden_tests`` has placed the files at .buglab/hidden."""
    (ws / JUNIT_REL).unlink(missing_ok=True)
    if incident.commands.hidden_test:
        cmd = incident.commands.hidden_test
        if incident.language in ("javascript", "typescript"):
            cmd = f"{cmd} --test-reporter=spec --test-reporter-destination=stdout --test-reporter=junit --test-reporter-destination={JUNIT_REL}"
        elif incident.language == "python":
            cmd = f"{cmd} -p no:cacheprovider --junitxml={JUNIT_REL}"
    else:
        cmd = _test_cmd(incident, HIDDEN_DIR)
    result = _shell(sandbox, ws, cmd, timeout_s)
    return _collect(incident, ws, result)


def run_one_test_file(sandbox: Sandbox, ws: Path, incident: Incident, rel_file: str, timeout_s: int = DEFAULT_TIMEOUT) -> TestRun:
    (ws / JUNIT_REL).unlink(missing_ok=True)
    if incident.commands.test_one:
        cmd = incident.commands.test_one.replace("{file}", shlex.quote(rel_file))
        if incident.language == "python":
            cmd = f"{cmd} -p no:cacheprovider --junitxml={JUNIT_REL}"
        elif incident.language in ("javascript", "typescript"):
            cmd = f"{cmd} --test-reporter=spec --test-reporter-destination=stdout --test-reporter=junit --test-reporter-destination={JUNIT_REL}"
    else:
        cmd = _test_cmd(incident, rel_file)
    result = _shell(sandbox, ws, cmd, timeout_s)
    return _collect(incident, ws, result)


def _collect(incident: Incident, ws: Path, result: ExecResult) -> TestRun:
    if incident.language == "c":
        tests, err = parse_tap(result.stdout)
    else:
        junit = ws / JUNIT_REL
        if junit.exists():
            tests, err = parse_junit(junit.read_text())
        else:
            tests, err = [], "no test report produced (did the test runner start?)"
    if result.timed_out:
        err = f"timed out after {result.duration_ms} ms" + (f"; {err}" if err else "")
    if not tests and not err:
        err = "no tests were collected"
    return TestRun(tests=tests, exec=result, parse_error=err)


# --- parsers ------------------------------------------------------------------

def parse_junit(xml: str) -> tuple[list[TestResult], str]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return [], f"unreadable junit report: {e}"
    out: list[TestResult] = []
    for tc in root.iter("testcase"):
        classname = tc.get("classname", "")
        name = tc.get("name", "?")
        full = f"{classname}::{name}" if classname and not name.startswith(classname) else name
        # node's junit reporter labels every case with classname "test"
        full = full.replace("\\", "/").removeprefix("test::")
        dur = int(float(tc.get("time", "0") or 0) * 1000)
        status, message = "passed", ""
        for child in tc:
            tag = child.tag.lower()
            if tag in ("failure", "error", "skipped"):
                status = {"failure": "failed"}.get(tag, tag)
                message = (child.get("message") or "") + ("\n" + child.text.strip() if child.text and child.text.strip() else "")
                break
        out.append(TestResult(name=full, status=status, duration_ms=dur, message=message.strip()[:4000]))
    return out, ""


TAP_LINE = re.compile(r"^(not ok|ok)\s+(\d+)\s*-?\s*(.*)$")
TAP_PLAN = re.compile(r"^(\d+)\.\.(\d+)$")


def parse_tap(text: str) -> tuple[list[TestResult], str]:
    out: list[TestResult] = []
    planned: int | None = None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if planned is None and (pm := TAP_PLAN.match(stripped)):
            planned = int(pm.group(2))
            continue
        m = TAP_LINE.match(stripped)
        if not m:
            continue
        ok, _, name = m.groups()
        status = "passed" if ok == "ok" else "failed"
        name = name.strip()
        if name.lower().startswith("# skip"):
            status = "skipped"
        message = ""
        if status == "failed":
            # the harness prints "# file:line: ..." diagnostics while the test
            # runs, i.e. on the lines *before* its result line
            diag: list[str] = []
            for prev in reversed(lines[:i]):
                p = prev.strip()
                if p.startswith("#"):
                    diag.append(p[1:].strip())
                else:
                    break
            message = "\n".join(reversed(diag))
        out.append(TestResult(name=name or f"test {m.group(2)}", status=status, duration_ms=0, message=message))
    if not out:
        return [], "no TAP output found (test binary crashed or did not print results)"
    if planned is not None and len(out) < planned:
        return out, f"incomplete TAP output: {len(out)}/{planned} tests reported (binary likely crashed mid-run)"
    return out, ""


PY_FRAME = re.compile(r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>.+)$')
NODE_FRAME = re.compile(r"^\s*at (?:(?P<func>[^(]+?) \()?(?:file://)?(?P<file>[^():]+):(?P<line>\d+):\d+\)?$")
ASAN_FRAME = re.compile(r"^\s*#\d+ 0x[0-9a-f]+ in (?P<func>\S+) (?:\S+ )?(?P<file>[^:\s]+):(?P<line>\d+)")
# Unsymbolized form (no external symbolizer inside the sandbox):
#   #1 0x1048d0 in dup2x+0x28 (/ws/build/tests:arm64+0x1000008d0)
ASAN_FRAME_RAW = re.compile(r"^\s*#\d+ 0x[0-9a-f]+ in (?P<func>[^\s+]+)\+0x[0-9a-f]+ \((?P<file>[^:]+):")


def _asan_frame(line: str) -> Frame | None:
    if m := ASAN_FRAME.match(line):
        return Frame(m["file"], int(m["line"]), m["func"])
    if m := ASAN_FRAME_RAW.match(line):
        func = m["func"]
        if func.startswith(("__", "wrap_", "start")) or "libclang_rt" in m["file"]:
            return None  # runtime / interceptor frames
        return Frame(m["file"], 0, func)
    return None


def parse_stack_trace(stderr: str) -> StackTrace | None:
    lines = stderr.splitlines()
    if any("Traceback (most recent call last)" in line for line in lines):
        start = max(i for i, line in enumerate(lines) if "Traceback (most recent call last)" in line)
        frames, header = [], ""
        for line in lines[start + 1 :]:
            m = PY_FRAME.match(line)
            if m:
                frames.append(Frame(m["file"], int(m["line"]), m["func"]))
            elif line and not line.startswith(" ") and not line.startswith("^"):
                header = line.strip()
        return StackTrace("python", header or "Traceback", frames)
    if any("AddressSanitizer" in line for line in lines):
        header = next((line.strip() for line in lines if "ERROR: AddressSanitizer" in line), "AddressSanitizer error")
        # only the first stack (the error site); ASan follows it with the
        # allocation/free stacks which would duplicate the frames
        frames: list[Frame] = []
        started = False
        for line in lines:
            f = _asan_frame(line)
            if f:
                frames.append(f)
                started = True
            elif started and line.strip() and not line.strip().startswith("#"):
                break
        return StackTrace("asan", re.sub(r"^==\d+==", "", header), frames)
    if any("runtime error:" in line for line in lines):
        header = next(line.strip() for line in lines if "runtime error:" in line)
        frames = [Frame(m["file"], int(m["line"]), m["func"]) for line in lines if (m := ASAN_FRAME.match(line))]
        return StackTrace("ubsan", header, frames)
    node_frames = [Frame(m["file"], int(m["line"]), (m["func"] or "<anonymous>").strip()) for line in lines if (m := NODE_FRAME.match(line))]
    if node_frames:
        header = next((line.strip() for line in lines if re.match(r"^\w*Error\b", line.strip())), "Error")
        return StackTrace("node", header, node_frames)
    return None
