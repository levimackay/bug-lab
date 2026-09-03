"""Deterministic incident-resolution score from measured facts only.

Every input is something the server observed (event timestamps, hint reveals,
a real diff against the pristine project, a real reproduction check). Nothing
here is typed in by the user."""

from __future__ import annotations

from dataclasses import dataclass, asdict

from engine.incidents import Incident


@dataclass(frozen=True)
class ScoreInput:
    elapsed_seconds: int
    hint_costs: list[int]
    solution_revealed: bool
    reproduced: bool
    tests_run: int
    changed_files: dict[str, str]  # rel path -> modified|added|deleted
    hidden_passed: int
    hidden_total: int
    visible_passed: int
    visible_total: int


@dataclass(frozen=True)
class Score:
    total: int
    base: int
    hint_penalty: int
    time_penalty: int
    unnecessary_edits: list[str]
    edit_penalty: int
    repro_bonus: int
    solution_cap_applied: bool
    elapsed_seconds: int
    hints_used: int
    tests_run: int
    reproduced: bool
    tests_passed: int
    tests_total: int

    def to_dict(self) -> dict:
        return asdict(self)


def unnecessary_edits(changed: dict[str, str], incident: Incident) -> list[str]:
    """Changed files that are neither where the fix belongs nor test files."""
    allowed = set(incident.solution_files)
    out = []
    for rel in changed:
        top = rel.split("/", 1)[0]
        if rel in allowed or top in ("tests", "test", "__tests__"):
            continue
        out.append(rel)
    return sorted(out)


def compute(incident: Incident, s: ScoreInput) -> Score:
    cfg = incident.scoring
    hint_penalty = sum(s.hint_costs)
    overtime = max(0, s.elapsed_seconds - cfg.par_seconds)
    time_penalty = min(cfg.overtime_cap, (overtime // 60) * 5)
    edits = unnecessary_edits(s.changed_files, incident)
    edit_penalty = len(edits) * cfg.unnecessary_file_penalty
    repro_bonus = cfg.repro_bonus if s.reproduced else 0
    total = cfg.base - hint_penalty - time_penalty - edit_penalty + repro_bonus
    capped = False
    if s.solution_revealed and total > cfg.solution_reveal_cap:
        total, capped = cfg.solution_reveal_cap, True
    total = max(0, total)
    return Score(
        total=total,
        base=cfg.base,
        hint_penalty=hint_penalty,
        time_penalty=time_penalty,
        unnecessary_edits=edits,
        edit_penalty=edit_penalty,
        repro_bonus=repro_bonus,
        solution_cap_applied=capped,
        elapsed_seconds=s.elapsed_seconds,
        hints_used=len(s.hint_costs),
        tests_run=s.tests_run,
        reproduced=s.reproduced,
        tests_passed=s.hidden_passed + s.visible_passed,
        tests_total=s.hidden_total + s.visible_total,
    )
