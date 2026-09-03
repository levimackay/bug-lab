# Architecture

```
browser (React, Monaco, xterm.js)
   │  HTTP /api/*            WS /api/runs/{id}/terminal
   ▼
server/            FastAPI: routes.py (HTTP), ws_terminal.py (PTY bridge), db.py (sqlite3)
   │
engine/            pure Python, no FastAPI imports, unit-tested on its own
   ├── incidents.py   incident.toml → Incident (tomllib)
   ├── workspace.py   var/workspaces/<run>/ : copy, list, diff, hidden-test overlay
   ├── runner.py      run / build / test commands; junit + TAP parsing; stack traces
   ├── reproduce.py   "fails on pristine, passes on yours" check
   ├── scoring.py     score from measured facts
   ├── mentor.py      Mentor Protocol (disabled in v1)
   └── sandbox.py     Sandbox Protocol; SeatbeltSandbox (macOS sandbox-exec + rlimits + PTY)
   │
incidents/<id>/    incident.toml, project/, hidden_tests/, solution/
var/               buglab.db, workspaces/, py/ (shared pytest venv)   — gitignored
```

## Execution path

```
Incident ─▶ workspace.create() ─▶ runner.run_tests() ─▶ Sandbox.exec(["/bin/sh","-c", cmd])
                                                              │
                                             sandbox-exec -p <profile> (seatbelt)
                                             rlimits (CPU, FSIZE, NOFILE), setsid, wall-clock timer
                                                              │
                                                        program / pytest / node --test / cc
                                                              │
                                    ExecResult(stdout, stderr, exit, ms, timed_out, max_rss)
                                                              │
                                     parse_junit / parse_tap ─▶ TestRun(tests[], summary)
```

Nothing in `server/` executes code; it only calls `engine.runner`. Nothing in
`engine/` knows about HTTP.

## The sandbox boundary

`SeatbeltSandbox` runs every command under a seatbelt profile parameterised on
the workspace path:

- reads: everything except `/Users`; then the workspace and `var/py` are re-allowed
- writes: the workspace and `/dev` only
- network: `localhost` only (bind, inbound, outbound); nothing else
- env: a fixed allowlist (`PATH` starting with the shared venv, `HOME`=workspace, `TMPDIR`=workspace/.tmp)
- limits: `RLIMIT_CPU` 120 s, `RLIMIT_FSIZE` 50 MB, `RLIMIT_NOFILE` 256, wall-clock timeout → `SIGKILL` to the process group, 1 MB output cap per stream
- measurement: `os.wait4` rusage → max RSS

Known ceiling of this platform: macOS does not enforce `RLIMIT_AS`, and
`RLIMIT_NPROC` is per-user rather than per-sandbox, so memory is measured, not
capped, and a fork bomb is contained by the process-group kill rather than a
count. A Docker/gVisor `Sandbox` would lift both; it is a second implementation
of the same two-method Protocol (`exec`, `spawn_shell`).

If `sandbox-exec` is not present the server refuses to start. There is no
unsandboxed mode.

## Terminal

`WS /api/runs/{id}/terminal` spawns `zsh -f -i` under the same profile inside a
pty (`pty.openpty`, `TIOCSCTTY`). The event loop reads the master fd with
`add_reader` and forwards bytes as text frames; keystrokes go the other way;
`{"type":"resize"}` frames call `TIOCSWINSZ`. Closing the socket (or resetting
the run) kills the process group.

## Runs, events, scoring

A `run` is one attempt at an incident. Every action the user takes through the
API becomes an `events` row (`started`, `file_opened`, `file_saved`, `app_run`,
`tests_run`, `hint`, `hypothesis`, `reproduce`, `submit`, `reset`, `terminal_opened`).
Every sandbox execution becomes an `execs` row (the runtime tab). The score is
computed once, at the first successful submit, from:

- elapsed time: `started_at` → submit time
- hint costs: the incident's costs for the hints actually revealed
- reproduction: the last `POST /reproduce` that returned `reproduced: true`
- unnecessary edits: `workspace.changed_files()` vs the pristine project, minus solution files and `tests/`
- solution reveal: caps the score

## Adding a language

1. `engine/runner.py`: how the test command gets a machine-readable report (junit or TAP) and how a single file is targeted.
2. `engine/runner.py::parse_stack_trace`: a frame regex for the runtime.
3. `docs/INCIDENT_FORMAT.md`: the per-language conventions.
4. Nothing in `server/` or the frontend changes: the editor picks syntax by extension.
