"""HTTP API. See docs/API.md for the contract. Everything the UI shows comes
from here; nothing here invents a number."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from engine import reproduce, runner, scoring, workspace
from engine.incidents import DIFFICULTIES, Incident
from engine.mentor import get_mentor
from engine.sandbox import ExecResult

router = APIRouter(prefix="/api")


def _iso(ts: float | None) -> str | None:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None


def _incident(req: Request, incident_id: str) -> Incident:
    inc = req.app.state.incidents.get(incident_id)
    if inc is None:
        raise HTTPException(404, f"no incident {incident_id}")
    return inc


def _run(req: Request, run_id: str):
    row = req.app.state.db.get_run(run_id)
    if row is None:
        raise HTTPException(404, f"no run {run_id}")
    inc = _incident(req, row["incident_id"])
    ws = workspace.workspace_path(run_id)
    if row["status"] != "abandoned" and not ws.exists():
        workspace.create(run_id, inc)
    return row, inc, ws


def _active(req: Request, run_id: str):
    row, inc, ws = _run(req, run_id)
    if row["status"] == "abandoned":
        raise HTTPException(409, "this run was reset; open the incident again")
    return row, inc, ws


def incident_summary(req: Request, inc: Incident) -> dict:
    db = req.app.state.db
    best = db.best_scores().get(inc.id)
    active = db.active_runs().get(inc.id)
    d = inc.public()
    d.update(
        status="solved" if best is not None else ("in_progress" if active else "unsolved"),
        best_score=best,
        active_run_id=active,
        attempts=db.attempt_counts().get(inc.id, 0),
    )
    return d


def run_payload(req: Request, row) -> dict:
    inc = _incident(req, row["incident_id"])
    db = req.app.state.db
    end = row["resolved_at"] or time.time()
    revealed = row["solution_revealed"] == 1 or row["status"] == "resolved"
    return {
        "id": row["id"],
        "incident_id": inc.id,
        "status": row["status"],
        "started_at": _iso(row["started_at"]),
        "resolved_at": _iso(row["resolved_at"]),
        "elapsed_seconds": int(end - row["started_at"]),
        "hints_revealed": row["hints_revealed"],
        "hints": [{"level": h.level, "text": h.text, "cost": h.cost} for h in inc.hints[: row["hints_revealed"]]],
        "solution_revealed": row["solution_revealed"] == 1,
        "solution": {
            "files": list(inc.solution_files),
            "explanation": inc.solution_explanation,
            "diff": workspace.reference_diff(inc),
        }
        if revealed
        else None,
        "hypothesis": row["hypothesis"],
        "reproduced": row["reproduced"] == 1,
        "repro_test_path": row["repro_test_path"],
        "tests_run": db.count_events(row["id"], "tests_run"),
        "score": json.loads(row["score_json"]) if row["score_json"] else None,
        "incident": incident_summary(req, inc),
    }


# --- incidents ----------------------------------------------------------------

@router.get("/health")
def health(req: Request):
    return {"ok": True, "incidents": len(req.app.state.incidents), "sandbox": "seatbelt"}


@router.get("/incidents")
def list_incidents(req: Request):
    return {"incidents": [incident_summary(req, inc) for inc in req.app.state.incidents.values()]}


@router.get("/incidents/{incident_id}")
def get_incident(req: Request, incident_id: str):
    return incident_summary(req, _incident(req, incident_id))


@router.post("/incidents/{incident_id}/runs")
def start_run(req: Request, incident_id: str):
    inc = _incident(req, incident_id)
    db = req.app.state.db
    row = db.active_run(inc.id)
    if row is None:
        row = db.create_run(inc.id)
        workspace.create(row["id"], inc)
        db.add_event(row["id"], "started")
        if inc.setup:
            req.app.state.sandbox.exec(["/bin/sh", "-c", inc.setup], cwd=workspace.workspace_path(row["id"]), timeout_s=120)
    return run_payload(req, row)


# --- runs ---------------------------------------------------------------------

@router.get("/runs/{run_id}")
def get_run(req: Request, run_id: str):
    row, _, _ = _run(req, run_id)
    return run_payload(req, row)


@router.post("/runs/{run_id}/reset")
def reset_run(req: Request, run_id: str):
    row, inc, _ = _run(req, run_id)
    db = req.app.state.db
    db.add_event(run_id, "reset")
    if row["status"] == "active":
        db.update_run(run_id, status="abandoned")
    req.app.state.terminals.kill(run_id)
    workspace.destroy(run_id)
    new = db.create_run(inc.id)
    workspace.create(new["id"], inc)
    db.add_event(new["id"], "started", {"reset_from": run_id})
    return run_payload(req, new)


class HypothesisBody(BaseModel):
    text: str


@router.put("/runs/{run_id}/hypothesis")
def put_hypothesis(req: Request, run_id: str, body: HypothesisBody):
    _active(req, run_id)
    db = req.app.state.db
    db.add_event(run_id, "hypothesis", {"length": len(body.text)})
    return run_payload(req, db.update_run(run_id, hypothesis=body.text[:10_000]))


@router.post("/runs/{run_id}/hints")
def reveal_hint(req: Request, run_id: str):
    row, inc, _ = _active(req, run_id)
    n = row["hints_revealed"]
    if n >= len(inc.hints):
        raise HTTPException(409, "no hints left")
    db = req.app.state.db
    db.add_event(run_id, "hint", {"level": inc.hints[n].level, "cost": inc.hints[n].cost})
    return run_payload(req, db.update_run(run_id, hints_revealed=n + 1))


class ConfirmBody(BaseModel):
    confirm: bool = False


@router.post("/runs/{run_id}/reveal-solution")
def reveal_solution(req: Request, run_id: str, body: ConfirmBody):
    _active(req, run_id)
    if not body.confirm:
        raise HTTPException(400, "confirm: true is required to reveal the solution")
    db = req.app.state.db
    db.add_event(run_id, "solution_revealed")
    return run_payload(req, db.update_run(run_id, solution_revealed=1))


# --- files --------------------------------------------------------------------

def _resolve(ws: Path, rel: str) -> Path:
    try:
        return workspace.resolve(ws, rel)
    except workspace.PathOutsideWorkspace:
        raise HTTPException(400, f"{rel} is outside the workspace")


@router.get("/runs/{run_id}/files")
def list_files(req: Request, run_id: str):
    _, _, ws = _active(req, run_id)
    return {"files": workspace.list_files(ws)}


@router.get("/runs/{run_id}/files/{path:path}")
def read_file(req: Request, run_id: str, path: str):
    _, _, ws = _active(req, run_id)
    p = _resolve(ws, path)
    if not p.is_file():
        raise HTTPException(404, f"{path} not found")
    data = p.read_bytes()
    try:
        content, binary = data.decode("utf-8"), False
    except UnicodeDecodeError:
        content, binary = "", True
    req.app.state.db.add_event(run_id, "file_opened", {"path": path})
    return {"path": path, "content": content, "binary": binary}


class FileBody(BaseModel):
    content: str


@router.put("/runs/{run_id}/files/{path:path}")
def write_file(req: Request, run_id: str, path: str, body: FileBody):
    _, _, ws = _active(req, run_id)
    p = _resolve(ws, path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body.content)
    req.app.state.db.add_event(run_id, "file_saved", {"path": path, "bytes": len(body.content)})
    return {"path": path, "saved": True}


@router.delete("/runs/{run_id}/files/{path:path}")
def delete_file(req: Request, run_id: str, path: str):
    _, _, ws = _active(req, run_id)
    p = _resolve(ws, path)
    if not p.is_file():
        raise HTTPException(404, f"{path} not found")
    p.unlink()
    req.app.state.db.add_event(run_id, "file_deleted", {"path": path})
    return {"path": path, "deleted": True}


@router.get("/runs/{run_id}/search")
def search(req: Request, run_id: str, q: str = ""):
    _, _, ws = _active(req, run_id)
    needle = q.lower()
    matches = []
    if needle:
        for rel in workspace.list_files(ws):
            try:
                lines = (ws / rel).read_text().splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(lines, 1):
                if needle in line.lower():
                    matches.append({"path": rel, "line": i, "text": line.strip()[:300]})
                    if len(matches) >= 200:
                        return {"matches": matches}
    return {"matches": matches}


# --- execution ----------------------------------------------------------------

def _record(req: Request, run_id: str, kind: str, r: ExecResult) -> None:
    req.app.state.db.add_exec(run_id, kind, r)


def _trace(ws: Path, *outputs: str) -> dict | None:
    """Parsed stack trace with frame paths relative to the workspace, so the UI
    can open them; paths outside the workspace (stdlib, runtime) stay absolute."""
    st = None
    for out in outputs:
        st = runner.parse_stack_trace(out)
        if st:
            break
    if not st:
        return None
    prefix = str(ws.resolve()) + "/"
    for f in st.frames:
        if f.file.startswith(prefix):
            f.file = f.file[len(prefix):]
    return st.to_dict()


def _exec_response(ws: Path, r: ExecResult | None) -> dict:
    if r is None:
        return {"exec": None, "stack_trace": None}
    return {"exec": r.__dict__, "stack_trace": _trace(ws, r.stderr, r.stdout)}


@router.post("/runs/{run_id}/run")
def run_app(req: Request, run_id: str):
    _, inc, ws = _active(req, run_id)
    r = runner.run_app(req.app.state.sandbox, ws, inc)
    _record(req, run_id, "run", r)
    req.app.state.db.add_event(run_id, "app_run", {"exit_code": r.exit_code, "timed_out": r.timed_out})
    return _exec_response(ws, r)


@router.post("/runs/{run_id}/build")
def build(req: Request, run_id: str):
    _, inc, ws = _active(req, run_id)
    r = runner.run_build(req.app.state.sandbox, ws, inc)
    if r is not None:
        _record(req, run_id, "build", r)
        req.app.state.db.add_event(run_id, "build", {"exit_code": r.exit_code})
    return _exec_response(ws, r)


class TestBody(BaseModel):
    target: str = ""


@router.post("/runs/{run_id}/test")
def run_tests(req: Request, run_id: str, body: TestBody | None = None):
    _, inc, ws = _active(req, run_id)
    target = (body.target if body else "") or ""
    if target:
        _resolve(ws, target)
    tr = runner.run_tests(req.app.state.sandbox, ws, inc, target=target)
    _record(req, run_id, "test", tr.exec)
    req.app.state.db.add_event(run_id, "tests_run", {"summary": tr.summary, "target": target})
    out = tr.to_dict()
    out["stack_trace"] = _trace(ws, tr.exec.stderr, tr.exec.stdout)
    return out


class ReproBody(BaseModel):
    test_path: str


@router.post("/runs/{run_id}/reproduce")
def reproduce_bug(req: Request, run_id: str, body: ReproBody):
    _, inc, ws = _active(req, run_id)
    res = reproduce.verify(req.app.state.sandbox, ws, inc, body.test_path)
    db = req.app.state.db
    for tr in (res.before, res.after):
        if tr is not None:
            _record(req, run_id, "reproduce", tr.exec)
    db.add_event(run_id, "reproduce", {"test_path": body.test_path, "reproduced": res.reproduced})
    if res.reproduced:
        db.update_run(run_id, reproduced=1, repro_test_path=body.test_path)
    return res.to_dict()


def _hidden_public(tr: runner.TestRun) -> dict:
    return {
        "ok": tr.ok,
        "summary": tr.summary,
        "tests": [
            {"name": t.name.replace(".buglab.hidden.", "").replace(workspace.HIDDEN_DIR + "/", ""), "status": t.status, "message": t.message[:1500]}
            for t in tr.tests
        ],
        "parse_error": tr.parse_error,
    }


def _postmortem(inc: Incident, ws: Path) -> dict:
    return {
        **inc.postmortem,
        "solution_explanation": inc.solution_explanation,
        "your_diff": workspace.unified_diff(ws, inc.project_dir),
        "reference_diff": workspace.reference_diff(inc),
    }


@router.post("/runs/{run_id}/submit")
def submit(req: Request, run_id: str):
    row, inc, ws = _active(req, run_id)
    sb, db = req.app.state.sandbox, req.app.state.db
    if inc.commands.build:
        b = runner.run_build(sb, ws, inc)
        _record(req, run_id, "build", b)
    vis = runner.run_tests(sb, ws, inc)
    _record(req, run_id, "test", vis.exec)
    with workspace.hidden_tests(ws, inc):
        hid = runner.run_hidden_tests(sb, ws, inc)
    _record(req, run_id, "hidden", hid.exec)
    resolved = vis.ok and hid.ok
    db.add_event(run_id, "submit", {"resolved": resolved, "visible": vis.summary, "hidden": hid.summary})

    score = json.loads(row["score_json"]) if row["score_json"] else None
    postmortem = json.loads(row["postmortem_json"]) if row["postmortem_json"] else None
    if resolved and row["status"] != "resolved":
        now = time.time()
        changed = workspace.changed_files(ws, inc.project_dir)
        s = scoring.compute(
            inc,
            scoring.ScoreInput(
                elapsed_seconds=int(now - row["started_at"]),
                hint_costs=[h.cost for h in inc.hints[: row["hints_revealed"]]],
                solution_revealed=row["solution_revealed"] == 1,
                reproduced=row["reproduced"] == 1,
                tests_run=db.count_events(run_id, "tests_run"),
                changed_files=changed,
                hidden_passed=hid.summary["passed"],
                hidden_total=hid.summary["total"],
                visible_passed=vis.summary["passed"],
                visible_total=vis.summary["total"],
            ),
        )
        score = s.to_dict()
        postmortem = _postmortem(inc, ws)
        row = db.update_run(run_id, status="resolved", resolved_at=now, score_json=json.dumps(score), postmortem_json=json.dumps(postmortem))
    elif resolved:
        postmortem = _postmortem(inc, ws)
    return {
        "resolved": resolved,
        "visible": vis.to_dict(),
        "hidden": _hidden_public(hid),
        "score": score if resolved else None,
        "postmortem": postmortem if resolved else None,
        "run": run_payload(req, db.get_run(run_id)),
    }


# --- evidence -----------------------------------------------------------------

@router.get("/runs/{run_id}/logs")
def logs(req: Request, run_id: str):
    _, _, ws = _active(req, run_id)
    files = []
    log_dir = ws / "logs"
    if log_dir.is_dir():
        for p in sorted(log_dir.iterdir()):
            if p.is_file():
                try:
                    files.append({"name": p.name, "content": p.read_text()[-200_000:]})
                except UnicodeDecodeError:
                    continue
    last = None
    for r in req.app.state.db.execs(run_id):
        if r["kind"] == "run":
            last = {"stdout": r["stdout"], "stderr": r["stderr"], "exit_code": r["exit_code"], "at": _iso(r["ts"])}
            break
    return {"files": files, "last_run": last}


@router.get("/runs/{run_id}/runtime")
def runtime(req: Request, run_id: str):
    _run(req, run_id)
    history = [
        {
            "kind": r["kind"],
            "at": _iso(r["ts"]),
            "exec": {
                "stdout": r["stdout"],
                "stderr": r["stderr"],
                "exit_code": r["exit_code"],
                "duration_ms": r["duration_ms"],
                "timed_out": bool(r["timed_out"]),
                "max_rss_kb": r["max_rss_kb"],
            },
        }
        for r in req.app.state.db.execs(run_id)
    ]
    return {"last": history[0] if history else None, "history": history}


# --- progress & misc ----------------------------------------------------------

@router.get("/progress")
def progress(req: Request):
    incidents: dict[str, Incident] = req.app.state.incidents
    db = req.app.state.db
    resolved = db.resolved_runs()
    best = db.best_scores()
    by_diff = {d: {"solved": 0, "total": 0} for d in DIFFICULTIES}
    by_cat: dict[str, dict] = {}
    cat_scores: dict[str, list[int]] = {}
    for inc in incidents.values():
        by_diff[inc.difficulty]["total"] += 1
        solved = inc.id in best
        by_diff[inc.difficulty]["solved"] += solved
        for c in inc.categories:
            by_cat.setdefault(c, {"solved": 0, "total": 0, "avg_score": None})
            by_cat[c]["total"] += 1
            if solved:
                by_cat[c]["solved"] += 1
                cat_scores.setdefault(c, []).append(best[inc.id])
    for c, scores in cat_scores.items():
        by_cat[c]["avg_score"] = round(sum(scores) / len(scores))
    recent = []
    total_hints = total_repro = 0
    score_sum = 0
    for r in resolved:
        inc = incidents.get(r["incident_id"])
        if inc is None:
            continue
        s = json.loads(r["score_json"]) if r["score_json"] else {}
        total_hints += r["hints_revealed"]
        total_repro += r["reproduced"]
        score_sum += s.get("total", 0)
        recent.append(
            {
                "run_id": r["id"],
                "incident_id": inc.id,
                "number": inc.number,
                "title": inc.title,
                "score": s.get("total", 0),
                "resolved_at": _iso(r["resolved_at"]),
                "elapsed_seconds": int((r["resolved_at"] or r["started_at"]) - r["started_at"]),
                "hints_used": r["hints_revealed"],
                "reproduced": r["reproduced"] == 1,
            }
        )
    weakest = sorted(
        by_cat,
        key=lambda c: (by_cat[c]["solved"] / by_cat[c]["total"] if by_cat[c]["total"] else 0, by_cat[c]["avg_score"] or 0),
    )
    return {
        "solved": len(best),
        "total": len(incidents),
        "by_difficulty": by_diff,
        "by_category": by_cat,
        "recent": recent[:20],
        "weakest": weakest,
        "totals": {
            "score_sum": score_sum,
            "avg_score": round(score_sum / len(recent)) if recent else None,
            "hints_used": total_hints,
            "reproduced": total_repro,
            "resolved_runs": len(recent),
        },
    }


@router.get("/settings")
def get_settings(req: Request):
    return req.app.state.db.settings()


@router.put("/settings")
def put_settings(req: Request, body: dict[str, str]):
    req.app.state.db.set_settings(body)
    return req.app.state.db.settings()


@router.get("/mentor")
def mentor():
    return {"enabled": get_mentor().enabled}
