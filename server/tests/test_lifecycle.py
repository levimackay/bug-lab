"""The whole loop against incident #001 through the real API and sandbox."""

INC = "inc-001-report-missing-last-row"


def test_incident_listing(client):
    r = client.get("/api/incidents")
    assert r.status_code == 200
    ids = [i["id"] for i in r.json()["incidents"]]
    assert INC in ids
    inc = client.get(f"/api/incidents/{INC}").json()
    assert inc["status"] == "unsolved" and inc["hint_count"] == 3
    assert "root_cause" not in inc and "postmortem" not in inc and "solution" not in inc


def test_full_loop(client):
    run = client.post(f"/api/incidents/{INC}/runs").json()
    rid = run["id"]
    assert run["status"] == "active" and run["solution"] is None
    # same active run is returned again
    assert client.post(f"/api/incidents/{INC}/runs").json()["id"] == rid

    files = client.get(f"/api/runs/{rid}/files").json()["files"]
    assert "report/summary.py" in files and not any("hidden" in f for f in files)
    assert client.get(f"/api/runs/{rid}/files/../etc/passwd").status_code in (400, 404)
    assert client.get(f"/api/runs/{rid}/files/.buglab/run.json").status_code == 400

    # app runs, tests pass on the broken project, submit fails on hidden tests
    app = client.post(f"/api/runs/{rid}/run").json()
    assert app["exec"]["exit_code"] == 0 and '"total": "41919.30"' in app["exec"]["stdout"]
    logs = client.get(f"/api/runs/{rid}/logs").json()
    assert logs["files"][0]["name"] == "app.log" and logs["last_run"]["exit_code"] == 0
    t = client.post(f"/api/runs/{rid}/test", json={}).json()
    assert t["ok"] and t["summary"]["passed"] == 4
    sub = client.post(f"/api/runs/{rid}/submit").json()
    assert sub["resolved"] is False and sub["hidden"]["summary"]["failed"] >= 1 and sub["score"] is None
    assert all("def " not in h["name"] for h in sub["hidden"]["tests"])

    # hints, hypothesis, reproduction
    h = client.post(f"/api/runs/{rid}/hints").json()
    assert h["hints_revealed"] == 1 and h["hints"][0]["level"] == "direction"
    assert client.put(f"/api/runs/{rid}/hypothesis", json={"text": "last day dropped"}).json()["hypothesis"] == "last day dropped"
    repro = (
        "from datetime import date\nfrom decimal import Decimal\nfrom report.loader import Sale\n"
        "from report.summary import daily_totals, period_total\n\n"
        "def test_last_day_counted():\n"
        "    daily = daily_totals([Sale(date(2026, 8, 31), 'A', Decimal('2.00'))])\n"
        "    assert period_total(daily, date(2026, 8, 1), date(2026, 8, 31)) == Decimal('2.00')\n"
    )
    assert client.put(f"/api/runs/{rid}/files/tests/test_repro.py", json={"content": repro}).json()["saved"]
    rp = client.post(f"/api/runs/{rid}/reproduce", json={"test_path": "tests/test_repro.py"}).json()
    assert rp["reproduced"] is False and "still fails" in rp["verdict"]

    # fix it
    src = client.get(f"/api/runs/{rid}/files/report/summary.py").json()["content"]
    assert "while day < end:" in src
    client.put(f"/api/runs/{rid}/files/report/summary.py", json={"content": src.replace("while day < end:", "while day <= end:")})
    rp = client.post(f"/api/runs/{rid}/reproduce", json={"test_path": "tests/test_repro.py"}).json()
    assert rp["reproduced"] is True
    sub = client.post(f"/api/runs/{rid}/submit").json()
    assert sub["resolved"] is True, sub
    score = sub["score"]
    assert score["hints_used"] == 1 and score["hint_penalty"] == 50 and score["reproduced"] and score["repro_bonus"] == 150
    assert score["unnecessary_edits"] == [] and score["tests_run"] == 1  # only explicit test runs count
    assert score["total"] == 1000 - 50 + 150
    pm = sub["postmortem"]
    assert "while day <= end" in pm["your_diff"] and "while day <= end" in pm["reference_diff"] and pm["root_cause"]
    run = client.get(f"/api/runs/{rid}").json()
    assert run["status"] == "resolved" and run["score"]["total"] == score["total"] and run["solution"] is not None

    # progress + persistence
    prog = client.get("/api/progress").json()
    assert prog["solved"] == 1 and prog["by_difficulty"]["beginner"]["solved"] == 1 and prog["recent"][0]["score"] == score["total"]
    assert client.get(f"/api/incidents/{INC}").json()["best_score"] == score["total"]

    # reset gives a fresh workspace and a new run
    new = client.post(f"/api/runs/{rid}/reset").json()
    assert new["id"] != rid and new["hints_revealed"] == 0
    assert "while day < end:" in client.get(f"/api/runs/{new['id']}/files/report/summary.py").json()["content"]
    assert client.get(f"/api/runs/{new['id']}/files").json()["files"].count("tests/test_repro.py") == 0


def test_terminal_websocket(client):
    rid = client.post(f"/api/incidents/{INC}/runs").json()["id"]
    with client.websocket_connect(f"/api/runs/{rid}/terminal") as ws:
        ws.send_text('{"type":"resize","cols":100,"rows":30}')
        ws.send_text("echo marker-$((6*7)) && ls\n")
        out = ""
        for _ in range(50):
            out += ws.receive_text()
            if "marker-42" in out and "report" in out:
                break
        assert "marker-42" in out and "pytest.ini" in out
