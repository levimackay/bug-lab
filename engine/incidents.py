"""Incident definitions: ``incidents/<id>/incident.toml`` plus three directories.

    project/       what the user sees and edits (the bug lives here)
    hidden_tests/  regression tests run only at submit time, never exposed
    solution/      reference fixed files, same relative paths as project/

``Incident.public()`` is the only view the API may hand to the browser before
the incident is resolved; it strips root cause, postmortem, solution and hints.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_DIR = ROOT / "incidents"

SEVERITIES = ("low", "medium", "high", "critical")
DIFFICULTIES = ("beginner", "intermediate", "advanced")
LANGUAGES = ("python", "javascript", "typescript", "c")
TOOLS = ("logs", "stack_trace", "tests", "runtime")
HINT_LEVELS = ("direction", "subsystem", "area")


@dataclass(frozen=True)
class Hint:
    level: str
    text: str
    cost: int


@dataclass(frozen=True)
class Commands:
    run: str
    test: str
    build: str = ""
    hidden_test: str = ""  # default: `test` pointed at .buglab/hidden
    test_one: str = ""  # default: `test {file}`


@dataclass(frozen=True)
class Scoring:
    base: int = 1000
    par_seconds: int = 900
    repro_bonus: int = 150
    unnecessary_file_penalty: int = 40
    solution_reveal_cap: int = 200
    overtime_cap: int = 300


@dataclass(frozen=True)
class Incident:
    id: str
    number: int
    title: str
    severity: str
    difficulty: str
    language: str
    system: str
    categories: tuple[str, ...]
    description: str
    symptoms: tuple[str, ...]
    environment: str
    expected_behavior: str
    broken_behavior: str
    tools: tuple[str, ...]
    commands: Commands
    hints: tuple[Hint, ...]
    solution_files: tuple[str, ...]
    solution_explanation: str
    postmortem: dict[str, str]
    scoring: Scoring
    dir: Path
    determinism_runs: int = 1  # verify_incidents runs hidden tests this many times
    setup: str = ""  # optional one-off shell command after workspace creation
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def project_dir(self) -> Path:
        return self.dir / "project"

    @property
    def hidden_tests_dir(self) -> Path:
        return self.dir / "hidden_tests"

    @property
    def solution_dir(self) -> Path:
        return self.dir / "solution"

    def public(self) -> dict:
        return {
            "id": self.id,
            "number": self.number,
            "title": self.title,
            "severity": self.severity,
            "difficulty": self.difficulty,
            "language": self.language,
            "system": self.system,
            "categories": list(self.categories),
            "description": self.description,
            "symptoms": list(self.symptoms),
            "environment": self.environment,
            "expected_behavior": self.expected_behavior,
            "broken_behavior": self.broken_behavior,
            "tools": list(self.tools),
            "commands": {"run": self.commands.run, "test": self.commands.test, "build": self.commands.build},
            "hint_count": len(self.hints),
            "hint_costs": [h.cost for h in self.hints],
            "scoring": {"base": self.scoring.base, "par_seconds": self.scoring.par_seconds, "repro_bonus": self.scoring.repro_bonus},
            "tags": list(self.tags),
        }


class IncidentError(ValueError):
    pass


def _req(d: dict, key: str, path: Path):
    if key not in d:
        raise IncidentError(f"{path}: missing required field '{key}'")
    return d[key]


def _one_of(value, allowed, name: str, path: Path):
    if value not in allowed:
        raise IncidentError(f"{path}: {name}={value!r} must be one of {allowed}")
    return value


def load_incident(incident_dir: Path) -> Incident:
    path = incident_dir / "incident.toml"
    if not path.exists():
        raise IncidentError(f"{incident_dir}: no incident.toml")
    with path.open("rb") as f:
        d = tomllib.load(f)

    cmds = _req(d, "commands", path)
    hints_raw = d.get("hints", [])
    hints = tuple(Hint(level=_one_of(h["level"], HINT_LEVELS, "hint.level", path), text=h["text"], cost=int(h["cost"])) for h in hints_raw)
    sol = _req(d, "solution", path)
    pm = _req(d, "postmortem", path)
    for k in ("root_cause", "why_it_happened", "why_tests_missed", "prevention"):
        if k not in pm:
            raise IncidentError(f"{path}: postmortem missing '{k}'")
    tools = tuple(_one_of(t, TOOLS, "tools[]", path) for t in d.get("tools", list(TOOLS)))

    inc = Incident(
        id=_req(d, "id", path),
        number=int(_req(d, "number", path)),
        title=_req(d, "title", path),
        severity=_one_of(_req(d, "severity", path), SEVERITIES, "severity", path),
        difficulty=_one_of(_req(d, "difficulty", path), DIFFICULTIES, "difficulty", path),
        language=_one_of(_req(d, "language", path), LANGUAGES, "language", path),
        system=_req(d, "system", path),
        categories=tuple(d.get("categories", [])),
        description=_req(d, "description", path).strip(),
        symptoms=tuple(d.get("symptoms", [])),
        environment=d.get("environment", "").rstrip(),
        expected_behavior=d.get("expected_behavior", "").strip(),
        broken_behavior=d.get("broken_behavior", "").strip(),
        tools=tools,
        commands=Commands(
            run=_req(cmds, "run", path),
            test=_req(cmds, "test", path),
            build=cmds.get("build", ""),
            hidden_test=cmds.get("hidden_test", ""),
            test_one=cmds.get("test_one", ""),
        ),
        hints=hints,
        solution_files=tuple(sol.get("files", [])),
        solution_explanation=sol.get("explanation", "").strip(),
        postmortem={k: str(v).strip() for k, v in pm.items()},
        scoring=Scoring(**d.get("scoring", {})),
        dir=incident_dir,
        determinism_runs=int(d.get("determinism_runs", 1)),
        setup=d.get("setup", ""),
        tags=tuple(d.get("tags", [])),
    )
    if inc.id != incident_dir.name:
        raise IncidentError(f"{path}: id {inc.id!r} must match directory name {incident_dir.name!r}")
    for sub in ("project", "hidden_tests", "solution"):
        if not (incident_dir / sub).is_dir():
            raise IncidentError(f"{incident_dir}: missing {sub}/")
    if not any(inc.hidden_tests_dir.iterdir()):
        raise IncidentError(f"{incident_dir}: hidden_tests/ is empty")
    for rel in inc.solution_files:
        if not (inc.solution_dir / rel).exists():
            raise IncidentError(f"{incident_dir}: solution.files lists {rel} but solution/{rel} is missing")
        if not (inc.project_dir / rel).exists():
            raise IncidentError(f"{incident_dir}: solution.files lists {rel} but project/{rel} is missing")
    return inc


def load_all(root: Path = INCIDENTS_DIR) -> dict[str, Incident]:
    incidents = [load_incident(p) for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith((".", "_"))]
    numbers = [i.number for i in incidents]
    if len(set(numbers)) != len(numbers):
        raise IncidentError("duplicate incident numbers")
    return {i.id: i for i in sorted(incidents, key=lambda i: i.number)}
