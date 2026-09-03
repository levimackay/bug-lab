"""Verify a user-written reproduction test.

A reproduction counts when the user's test file *fails* against the pristine
project (bug present) and *passes* against the user's current workspace
(bug fixed). Both runs happen inside the sandbox on real copies."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from engine import workspace
from engine.incidents import Incident
from engine.runner import TestRun, run_one_test_file
from engine.sandbox import Sandbox

WORK_BASE = workspace.WORKSPACES_DIR


@dataclass
class ReproResult:
    reproduced: bool
    verdict: str
    before: TestRun | None  # user's test on pristine code
    after: TestRun | None  # user's test on current workspace

    def to_dict(self) -> dict:
        return {
            "reproduced": self.reproduced,
            "verdict": self.verdict,
            "before": self.before.to_dict() if self.before else None,
            "after": self.after.to_dict() if self.after else None,
        }


def _pristine_with_user_tests(ws: Path, incident: Incident, test_dir: str) -> Path:
    WORK_BASE.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="repro-", dir=WORK_BASE))
    shutil.rmtree(tmp)
    shutil.copytree(incident.project_dir, tmp)
    (tmp / ".buglab").mkdir()
    user_tests = ws / test_dir
    if user_tests.is_dir():
        shutil.copytree(user_tests, tmp / test_dir, dirs_exist_ok=True)
    return tmp


def verify(sandbox: Sandbox, ws: Path, incident: Incident, rel_file: str) -> ReproResult:
    try:
        target = workspace.resolve(ws, rel_file)
    except workspace.PathOutsideWorkspace:
        return ReproResult(False, "path is outside the workspace", None, None)
    if not target.is_file():
        return ReproResult(False, f"{rel_file} does not exist", None, None)
    parts = Path(rel_file).parts
    if parts[0] not in ("tests", "test", "__tests__"):
        return ReproResult(False, "reproduction tests must live in the tests/ directory", None, None)

    pristine = _pristine_with_user_tests(ws, incident, parts[0])
    try:
        before = run_one_test_file(sandbox, pristine, incident, rel_file)
    finally:
        shutil.rmtree(pristine, ignore_errors=True)
    if not before.tests:
        return ReproResult(False, "the test did not run against the original code: " + (before.parse_error or "no tests collected"), before, None)
    if before.ok:
        return ReproResult(False, "the test passes on the original, buggy code, so it does not reproduce the incident", before, None)

    after = run_one_test_file(sandbox, ws, incident, rel_file)
    if not after.tests:
        return ReproResult(False, "the test did not run against your workspace: " + (after.parse_error or "no tests collected"), before, after)
    if not after.ok:
        return ReproResult(False, "the test fails on the original code (good) but still fails on your current code: the bug is reproduced, not yet fixed", before, after)
    return ReproResult(True, "fails before the fix, passes after it", before, after)
