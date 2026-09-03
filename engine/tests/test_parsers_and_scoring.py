from pathlib import Path

from engine import scoring
from engine.incidents import load_incident
from engine.runner import parse_junit, parse_stack_trace, parse_tap

ROOT = Path(__file__).resolve().parent.parent.parent


def test_parse_junit_pytest_shape():
    xml = """<testsuites><testsuite name="pytest"><testcase classname="tests.test_x" name="test_ok" time="0.01"/>
    <testcase classname="tests.test_x" name="test_bad" time="0.2"><failure message="assert 1 == 2">Traceback...</failure></testcase>
    <testcase classname="tests.test_x" name="test_skip"><skipped message="no"/></testcase></testsuite></testsuites>"""
    tests, err = parse_junit(xml)
    assert err == "" and [t.status for t in tests] == ["passed", "failed", "skipped"]
    assert tests[1].name == "tests.test_x::test_bad" and tests[1].message.startswith("assert 1 == 2") and tests[1].duration_ms == 200


def test_parse_junit_garbage():
    tests, err = parse_junit("<not xml")
    assert tests == [] and "unreadable" in err


def test_parse_tap_with_preceding_diagnostics():
    out = "1..3\nok 1 - push\n# tests/t.c:12: CHECK(x == 1) failed\nnot ok 2 - pop\nok 3 - # SKIP later\n"
    tests, err = parse_tap(out)
    assert err == "" and [t.status for t in tests] == ["passed", "failed", "skipped"]
    assert tests[1].message == "tests/t.c:12: CHECK(x == 1) failed"


def test_parse_tap_crash_is_reported():
    tests, err = parse_tap("1..3\nok 1 - a\n==123==ERROR: AddressSanitizer: heap-use-after-free")
    assert len(tests) == 1 and err == ""
    assert parse_tap("")[1]


def test_stack_traces():
    py = 'Traceback (most recent call last):\n  File "app/x.py", line 10, in main\n    run()\n  File "app/y.py", line 3, in run\n    1/0\nZeroDivisionError: division by zero\n'
    st = parse_stack_trace(py)
    assert st.kind == "python" and st.header == "ZeroDivisionError: division by zero" and st.frames[1].file == "app/y.py" and st.frames[1].line == 3
    node = "TypeError: x is not a function\n    at run (file:///w/src/a.js:12:5)\n    at /w/src/b.js:4:1\n"
    st = parse_stack_trace(node)
    assert st.kind == "node" and st.frames[0].function == "run" and st.frames[0].file == "/w/src/a.js" and st.frames[1].line == 4
    asan = "==4==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x1\n    #0 0x1 in main src/main.c:7\n    #1 0x2 in start+0x1 (dyld:arm64)\n"
    st = parse_stack_trace(asan)
    assert st.kind == "asan" and st.header.startswith("ERROR: AddressSanitizer") and st.frames == [type(st.frames[0])("src/main.c", 7, "main")]
    raw = "==5==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x1\n    #0 0x1 in strcpy+0x458 (/x/libclang_rt.asan_osx_dynamic.dylib:arm64e+0x3aa1c)\n    #1 0x2 in dup2x+0x28 (/ws/build/tests:arm64+0x1000008d0)\n    #2 0x3 in main+0x10 (/ws/build/tests:arm64+0x100001088)\n"
    st = parse_stack_trace(raw)
    assert [(f.function, f.file, f.line) for f in st.frames] == [("dup2x", "/ws/build/tests", 0), ("main", "/ws/build/tests", 0)]
    assert parse_stack_trace("all fine\n") is None


def test_scoring_from_measurements():
    inc = load_incident(ROOT / "incidents" / "inc-001-report-missing-last-row")
    base = scoring.ScoreInput(elapsed_seconds=100, hint_costs=[], solution_revealed=False, reproduced=False, tests_run=2,
                              changed_files={"report/summary.py": "modified"}, hidden_passed=3, hidden_total=3, visible_passed=4, visible_total=4)
    assert scoring.compute(inc, base).total == 1000
    s = scoring.compute(inc, scoring.ScoreInput(**{**base.__dict__, "hint_costs": [50, 100], "reproduced": True,
                                                   "changed_files": {"report/summary.py": "modified", "report/cli.py": "modified", "tests/test_repro.py": "added"},
                                                   "elapsed_seconds": inc.scoring.par_seconds + 600}))
    assert s.hint_penalty == 150 and s.repro_bonus == 150 and s.unnecessary_edits == ["report/cli.py"] and s.edit_penalty == 40 and s.time_penalty == 50
    assert s.total == 1000 - 150 + 150 - 40 - 50
    capped = scoring.compute(inc, scoring.ScoreInput(**{**base.__dict__, "solution_revealed": True}))
    assert capped.total == 200 and capped.solution_cap_applied


def test_incident_public_view_hides_answers():
    inc = load_incident(ROOT / "incidents" / "inc-012-race-oversell")
    pub = inc.public()
    text = str(pub)
    assert "postmortem" not in pub and "root_cause" not in text and inc.hints[2].text not in text and inc.solution_explanation not in text
