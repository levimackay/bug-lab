# Bug Lab

An interactive debugging training environment. You get a realistic incident
report for a small but real software system, investigate it in an IDE-style
workspace with a real terminal, reproduce the bug, fix it, and get a scored
postmortem. Nothing is simulated: the code really has the bug, the tests
really run, the terminal really is a shell, and the score is computed from what
you actually did.

Languages in v1: Python (primary), JavaScript / TypeScript (async and
event-loop bugs), C (memory and resource bugs).

## Run it

Requirements: macOS (the sandbox is macOS `sandbox-exec`), Xcode command line
tools, Homebrew Python 3.14 at `/opt/homebrew/bin/python3.14`, `uv`, Node 22+.

```bash
git clone <this repo> bug-lab && cd bug-lab
make setup      # two venvs (app + sandboxed pytest), clang symlink, npm install
make dev        # API on :8000, UI on http://localhost:5173
```

`make serve` builds the frontend and serves everything from `:8000`.
`make verify` proves every incident is real (see below) and runs the test
suites, type check and lint.

## How it works

```
Incident ─▶ Workspace (your private copy) ─▶ Sandbox ─▶ Program / Tests ─▶ Results
```

- Every incident is a directory under `incidents/`: an `incident.toml`
  (report, hints, root cause, postmortem, scoring), a `project/` you edit,
  `hidden_tests/` that decide whether your fix is right, and a `solution/`
  used for the postmortem diff and for verification.
- Starting an incident copies `project/` to `var/workspaces/<run>/`. Every
  command you run (RUN, TESTS, the terminal, SUBMIT) executes inside a
  seatbelt sandbox rooted at that directory: no network except localhost, no
  writes outside the workspace, no reads of your home directory, CPU/file
  limits and a hard timeout.
- SUBMIT runs the visible tests and the hidden tests. If both pass the run is
  resolved and scored: base score minus hint costs, minus time over par, minus
  files you changed that had nothing to do with the fix, plus a bonus if you
  wrote a reproduction test that fails on the original code and passes on
  yours.
- Progress, scores, hints and hypotheses persist in `var/buglab.db` (SQLite).

`scripts/verify_incidents.py` is the content gate: for every incident it checks
that the visible tests pass on the broken code, the hidden tests fail on it,
everything passes with the reference solution applied, and (for concurrency
incidents) that the failure reproduces a set number of times in a row, per
the incident's `determinism_runs` (10-20 across the current incidents).

## Layout

```
engine/      sandbox, incident loader, workspace, runner (junit/TAP parsing, stack traces), reproduction check, scoring
server/      FastAPI: HTTP routes, WebSocket terminal bridge, sqlite persistence
frontend/    Vite + React + Monaco + xterm.js
incidents/   the challenge content
scripts/     verify_incidents.py
docs/        ARCHITECTURE.md, API.md, INCIDENT_FORMAT.md
DESIGN.md    the visual spec
```

## Writing an incident

Read `docs/INCIDENT_FORMAT.md`, copy the shape of an existing incident, and
run `.venv/bin/python scripts/verify_incidents.py <id>` until it says `ok`.

## Limits worth knowing

The sandbox is process-level isolation on macOS, not a VM. It stops programs
from touching your files or the network; it does not cap memory (macOS ignores
`RLIMIT_AS`), it measures it. The `Sandbox` protocol in `engine/sandbox.py`
is the place to plug in Docker, gVisor or a microVM if you need stronger
guarantees or Linux support.
