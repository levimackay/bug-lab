"""A run's workspace: a private copy of the incident's project on disk.

``var/workspaces/<run_id>/`` is the sandbox boundary (see ``sandbox.py``).
The ``.buglab/`` directory inside it is bookkeeping (run marker, junit output,
temporary hidden-test overlay) and is never listed to the user.
"""

from __future__ import annotations

import difflib
import json
import re
import shutil
from contextlib import contextmanager
from pathlib import Path

from engine.incidents import Incident

ROOT = Path(__file__).resolve().parent.parent
WORKSPACES_DIR = ROOT / "var" / "workspaces"

IGNORED_DIRS = {".buglab", ".tmp", "__pycache__", ".pytest_cache", "node_modules", "build", ".git"}
# runtime artifacts (compiled objects, sqlite files the apps create) are never
# part of a fix and never count as an edit
IGNORED_FILES = re.compile(r"(\.pyc|\.o|\.dSYM|\.DS_Store|\.db|\.sqlite3?|\.db-journal|\.db-wal|\.db-shm)$")
HIDDEN_DIR = ".buglab/hidden"


class PathOutsideWorkspace(ValueError):
    pass


def workspace_path(run_id: str) -> Path:
    return WORKSPACES_DIR / run_id


def create(run_id: str, incident: Incident) -> Path:
    ws = workspace_path(run_id)
    if ws.exists():
        shutil.rmtree(ws)
    shutil.copytree(incident.project_dir, ws)
    (ws / ".buglab").mkdir()
    (ws / ".buglab" / "run.json").write_text(json.dumps({"run_id": run_id, "incident": incident.id}))
    return ws


def destroy(run_id: str) -> None:
    ws = workspace_path(run_id)
    if ws.exists():
        shutil.rmtree(ws)


def resolve(ws: Path, rel: str) -> Path:
    """Resolve a user-supplied relative path, refusing escapes and bookkeeping dirs."""
    if rel.startswith("/") or ".." in Path(rel).parts:
        raise PathOutsideWorkspace(rel)
    p = (ws / rel).resolve()
    if p != ws.resolve() and ws.resolve() not in p.parents:
        raise PathOutsideWorkspace(rel)
    parts = p.relative_to(ws.resolve()).parts
    if parts and parts[0] in IGNORED_DIRS:
        raise PathOutsideWorkspace(rel)
    return p


def list_files(root: Path) -> list[str]:
    out: list[str] = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if any(part in IGNORED_DIRS for part in rel.parts) or IGNORED_FILES.search(p.name):
            continue
        if p.is_file():
            out.append(rel.as_posix())
    return out


def _read_text(p: Path) -> str | None:
    try:
        return p.read_text()
    except (UnicodeDecodeError, OSError):
        return None


def changed_files(ws: Path, pristine: Path) -> dict[str, str]:
    """Map of relative path -> 'modified' | 'added' | 'deleted' versus pristine."""
    now = set(list_files(ws))
    before = set(list_files(pristine))
    out: dict[str, str] = {}
    for rel in sorted(now | before):
        if rel in now and rel not in before:
            out[rel] = "added"
        elif rel in before and rel not in now:
            out[rel] = "deleted"
        elif (ws / rel).read_bytes() != (pristine / rel).read_bytes():
            out[rel] = "modified"
    return out


def unified_diff(ws: Path, pristine: Path, only: set[str] | None = None) -> str:
    chunks: list[str] = []
    for rel, kind in changed_files(ws, pristine).items():
        if only is not None and rel not in only:
            continue
        a = _read_text(pristine / rel) if kind != "added" else ""
        b = _read_text(ws / rel) if kind != "deleted" else ""
        if a is None or b is None:
            chunks.append(f"Binary file {rel} {kind}\n")
            continue
        chunks.append(
            "".join(
                difflib.unified_diff(
                    a.splitlines(keepends=True),
                    b.splitlines(keepends=True),
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                )
            )
        )
    return "".join(chunks)


def reference_diff(incident: Incident) -> str:
    """The intended fix, as a diff of solution/ over project/ (solution files only)."""
    chunks = []
    for rel in incident.solution_files:
        a = (incident.project_dir / rel).read_text().splitlines(keepends=True)
        b = (incident.solution_dir / rel).read_text().splitlines(keepends=True)
        chunks.append("".join(difflib.unified_diff(a, b, fromfile=f"a/{rel}", tofile=f"b/{rel}")))
    return "".join(chunks)


@contextmanager
def hidden_tests(ws: Path, incident: Incident):
    """Temporarily place the incident's hidden tests at ``.buglab/hidden/``."""
    target = ws / HIDDEN_DIR
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(incident.hidden_tests_dir, target)
    try:
        yield target
    finally:
        shutil.rmtree(target, ignore_errors=True)


def apply_solution(ws: Path, incident: Incident) -> None:
    for p in incident.solution_dir.rglob("*"):
        if p.is_file():
            dest = ws / p.relative_to(incident.solution_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
