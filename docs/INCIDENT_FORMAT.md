# Authoring an incident

An incident is a directory under `incidents/` named by its id:

```
incidents/inc-012-race-oversell/
  incident.toml          metadata, hints, root cause, postmortem, scoring
  project/               what the user sees and edits; the bug lives here
    README.md            what the system is, how to run it, how to test it
    logs/                real-looking log files from the incident (evidence)
    <package>/           the code (3–8 files, a realistic miniature system)
    tests/               visible tests: they PASS on the broken code
    pytest.ini | ...     whatever the test runner needs
  hidden_tests/          regression tests: FAIL on project/, PASS with solution/
  solution/              only the files a correct fix changes, same relative paths
```

`scripts/verify_incidents.py <id>` is the gate. It runs everything in the real
sandbox and refuses an incident unless all of these hold:

1. `incident.toml` loads (see fields below) and `id` equals the directory name.
2. Visible tests pass on the broken project (the bug hides from them; that is the
   "why tests missed it" of the postmortem).
3. Hidden tests fail on the broken project. For concurrency incidents set
   `determinism_runs = 20`; every run must fail.
4. Visible and hidden tests pass with `solution/` copied over `project/`.
5. `commands.run` exits 0 on the fixed project (on the broken one it may exit
   non-zero, print the symptom, or both, but must not hang past 60 s).
6. `solution.files` equals the set of files that differ between `solution/` and `project/`.
7. No hint contains the basename of a solution file.

## incident.toml

```toml
id = "inc-012-race-oversell"          # == directory name
number = 12                           # unique, drives ordering
title = "Flash Sale Oversold"
severity = "critical"                 # low | medium | high | critical
difficulty = "advanced"               # beginner | intermediate | advanced
language = "python"                   # python | javascript | typescript | c
system = "Inventory Service"
categories = ["concurrency"]          # specialisations shown on the dashboard:
                                      # memory, concurrency, networking, algorithms,
                                      # state, caching, error-handling, database,
                                      # data-integrity, performance, resources
tags = ["race-condition"]             # free-form
determinism_runs = 20                 # optional, default 1
setup = ""                            # optional shell command run once after workspace creation

description = """multi-paragraph incident report. Enough to investigate,
not enough to know the fix. Never name the file or function."""
symptoms = ["observable fact 1", "observable fact 2"]
environment = """preformatted tree, rendered verbatim in monospace"""
expected_behavior = "one or two sentences"
broken_behavior = "one or two sentences; describe the effect, not the cause"
tools = ["logs", "tests", "runtime", "stack_trace"]   # which investigation tabs exist

[commands]
run = "python -m inventory"           # sh -c, cwd = workspace root
test = "pytest -q"                    # the engine appends junit flags (python/node) and a target path
build = ""                            # C only: compile the app, e.g. "cc -fsanitize=address,undefined -g -o build/app src/*.c"
hidden_test = ""                      # optional; default = test command pointed at .buglab/hidden
test_one = ""                         # optional; template with {file}; default = test command + file

[[hints]]                             # exactly three, in this order
level = "direction"                   # vague: where to look conceptually
text = "..."
cost = 50
[[hints]]
level = "subsystem"                   # narrows to a component or mechanism
text = "..."
cost = 100
[[hints]]
level = "area"                        # the specific operation, still not the line
text = "..."
cost = 200

[solution]
files = ["inventory/store.py"]
explanation = """what the fix is and why it works; shown after resolve/reveal"""

[postmortem]
root_cause = "..."
why_it_happened = "..."
why_tests_missed = "..."
prevention = "..."

[scoring]                             # all optional
base = 1000
par_seconds = 900                     # after this, −5 per minute, capped at overtime_cap
repro_bonus = 150
unnecessary_file_penalty = 40         # per changed file outside solution.files and tests/
solution_reveal_cap = 200
overtime_cap = 300
```

## Per-language conventions

**Python.** Package at the workspace root (`inventory/…`), `pytest.ini` with
`pythonpath = .` and `testpaths = tests`. Hidden tests import the package the
same way visible ones do. `run = "python -m <package>"`. pytest and the stdlib
are the only dependencies; nothing is pip-installed per incident.

**JavaScript / TypeScript.** Node 26, no npm install. Tests use the built-in
runner: set `test = "node --test"` (flags such as `--expose-gc` may follow) and
the engine appends the pattern `tests/**/*.test.*` (or `.buglab/hidden/**/*.test.*`
for hidden tests, or a single file). Files end in `.test.js` / `.test.ts`. TypeScript
runs directly via Node's type stripping (no `enum`, no decorators, no
`namespace`); use `.ts` for both source and tests and import with the `.ts`
extension. `package.json` with `"type": "module"` at the root. Hidden tests run
from `.buglab/hidden/`, two levels down, so they import `../../src/x.ts` where a
visible test imports `../src/x.ts`. For network
incidents, servers may bind `127.0.0.1` on an ephemeral port; nothing else
is reachable.

**C.** Apple clang, `-fsanitize=address,undefined -g`. There is no test
framework: `tests/harness.h` (copy it from `incidents/_templates/c/harness.h`)
gives `TEST(name)` / `CHECK(cond)` / `RUN_ALL()` and prints TAP. Commands:

```toml
build = "mkdir -p build && cc -fsanitize=address,undefined -g -Isrc -o build/app src/*.c"
test  = "mkdir -p build && cc -fsanitize=address,undefined -g -Isrc -o build/tests src/lib.c tests/test_lib.c && ./build/tests"
hidden_test = "mkdir -p build && cc -fsanitize=address,undefined -g -Isrc -o build/hidden src/lib.c .buglab/hidden/test_hidden.c && ./build/hidden"
test_one = "mkdir -p build && cc -fsanitize=address,undefined -g -Isrc -o build/one src/lib.c {file} && ./build/one"
```

Keep `main.c` separate from the library so tests can link the library without a
second `main`. Leak incidents measure with `mstats()` (`<malloc/malloc.h>`)
because ASan leak detection is unavailable on Apple Silicon. Memory-error
incidents rely on ASan aborting the test binary: a crash means the TAP output is
incomplete, which the parser reports as a failure with the ASan report in stderr.

## Writing guidance

- The project must feel like a real system: a README that explains what it is,
  logs that look like production logs, names that a team would use. No `foo`.
- Exactly one bug. Everything else must be correct, or the user learns the wrong lesson.
- The visible tests are part of the story: they pass, and the postmortem explains why they missed it.
- Hidden tests assert the *invariant* the incident describes, not the implementation.
- Hints go direction → subsystem → area. None of them says what to change.
- The postmortem teaches: root cause (mechanism), why it happened (the human/design reason), why tests missed it, prevention.
- Never invent numbers in the incident text that the project cannot reproduce: run the broken app, copy the real output into the description and logs.
