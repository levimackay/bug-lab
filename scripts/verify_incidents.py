"""Quality gate for incident content. For every incident:

  1. incident.toml loads and validates
  2. visible tests pass on the broken project (the bug is hidden from them)
  3. hidden tests FAIL on the broken project (the bug is real)
  4. visible + hidden tests PASS with solution/ applied (the fix is real)
  5. the app's run command exits non-zero or prints the symptom on the broken
     project and exits 0 on the fixed one (skipped when `symptom_exit` is
     absent: some incidents only manifest through tests)
  6. solution.files matches the set of files that differ between project/ and
     solution/
  7. concurrency incidents repeat step 3 and 4 `determinism_runs` times

Usage: .venv/bin/python scripts/verify_incidents.py [incident-id ...]
"""

from __future__ import annotations

import shutil
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import runner, workspace  # noqa: E402
from engine.incidents import Incident, load_all  # noqa: E402
from engine.sandbox import SeatbeltSandbox  # noqa: E402


def check(cond: bool, msg: str, failures: list[str]) -> None:
    if not cond:
        failures.append(msg)


def verify(inc: Incident, sb: SeatbeltSandbox) -> list[str]:
    f: list[str] = []
    run_id = f"verify-{inc.id}-{uuid.uuid4().hex[:6]}"
    ws = workspace.create(run_id, inc)
    try:
        if inc.commands.build:
            b = runner.run_build(sb, ws, inc)
            check(b is not None and b.ok, f"build failed on broken project: {b.stderr[-800:] if b else ''}", f)

        vis = runner.run_tests(sb, ws, inc)
        check(vis.ok, f"visible tests do not pass on broken project: {vis.summary} {vis.parse_error} {vis.exec.stderr[-600:]}", f)

        for i in range(inc.determinism_runs):
            with workspace.hidden_tests(ws, inc):
                hid = runner.run_hidden_tests(sb, ws, inc)
            check(bool(hid.tests), f"hidden tests produced no results on broken project: {hid.parse_error} {hid.exec.stderr[-600:]}", f)
            check(not hid.ok, f"hidden tests PASS on broken project (run {i + 1}/{inc.determinism_runs}): bug is not real", f)
            if f:
                break

        app = runner.run_app(sb, ws, inc)
        check(not app.timed_out, "run command timed out on broken project", f)

        # diff hygiene
        sol_only = {
            rel for rel in workspace.list_files(inc.solution_dir)
            if not (inc.project_dir / rel).exists() or (inc.project_dir / rel).read_bytes() != (inc.solution_dir / rel).read_bytes()
        }
        check(sol_only == set(inc.solution_files), f"solution.files {sorted(inc.solution_files)} != files differing {sorted(sol_only)}", f)

        workspace.apply_solution(ws, inc)
        if inc.commands.build:
            b = runner.run_build(sb, ws, inc)
            check(b is not None and b.ok, f"build failed on fixed project: {b.stderr[-800:] if b else ''}", f)
        vis2 = runner.run_tests(sb, ws, inc)
        check(vis2.ok, f"visible tests fail on fixed project: {vis2.summary} {vis2.exec.stderr[-600:]}", f)
        for i in range(inc.determinism_runs):
            with workspace.hidden_tests(ws, inc):
                hid2 = runner.run_hidden_tests(sb, ws, inc)
            check(hid2.ok, f"hidden tests fail on fixed project (run {i + 1}): {hid2.summary} {[t.message[:200] for t in hid2.tests if t.status != 'passed']} {hid2.exec.stderr[-600:]}", f)
            if f:
                break
        app2 = runner.run_app(sb, ws, inc)
        check(app2.exit_code == 0 and not app2.timed_out, f"run command fails on fixed project: exit {app2.exit_code} {app2.stderr[-600:]}", f)

        for h in inc.hints:
            for rel in inc.solution_files:
                check(Path(rel).name not in h.text, f"hint names the fix file {rel}", f)
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    return f


def main(argv: list[str]) -> int:
    incidents = load_all()
    wanted = argv[1:] or list(incidents)
    sb = SeatbeltSandbox()
    bad = 0
    for iid in wanted:
        inc = incidents[iid]
        t = time.monotonic()
        failures = verify(inc, sb)
        status = "ok " if not failures else "BAD"
        print(f"[{status}] #{inc.number:03d} {inc.id} ({inc.language}, {inc.difficulty}) {time.monotonic() - t:.1f}s")
        for msg in failures:
            print(f"        - {msg}")
        bad += bool(failures)
    print(f"\n{len(wanted) - bad}/{len(wanted)} incidents verified")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
