# Bug Lab — visual spec

Binding. Change this file before diverging from it.

## The conceit

**An incident console that happens to contain an editor.**

Everything on screen is instrumentation. The chrome is a status board: the
incident number, severity, clock and run status are always pinned; panels are
hard-edged instruments separated by hairlines, not cards floating on a page.
Colour is reserved for *state* (operational, warning, failure, success,
severity). Nothing decorative is coloured. If a thing is not telling you the
state of the system, it is grey.

References: VS Code's density and panel model, PagerDuty/incident.io's
severity strip, a Bloomberg terminal's refusal to waste pixels. Steal the
structure, never the surface.

## Tokens

```yaml
family: incident-console
mode: dark-only
ground: "#0b0d10"        # page
panel: "#111418"         # panel surfaces
raised: "#161a20"        # hover rows, active tab
line: "#1f242b"          # every hairline
line-strong: "#2c333c"   # focused panel border, resize handles on hover
ink: "#d6dbe3"
ink-dim: "#8b94a3"
ink-faint: "#5c6572"
state:
  operational: "#3fb950"
  success: "#3fb950"
  warning: "#d29922"
  failure: "#f85149"
  info: "#58a6ff"
  running: "#58a6ff"
severity:
  low: "#8b94a3"
  medium: "#d29922"
  high: "#f0883e"
  critical: "#f85149"
focus-ring: "#58a6ff"
selection: "rgba(88,166,255,0.18)"
radius: 0px               # everywhere; no rounded cards
shadow: none
type:
  ui: "IBM Plex Sans"     # @fontsource/ibm-plex-sans 400/500/600
  mono: "JetBrains Mono"  # @fontsource/jetbrains-mono 400/500/700 — editor, terminal, evidence, numbers
  scale: [11, 12, 13, 14, 16, 20, 28]   # px; 13 is body, 12 is panel chrome, 11 is metadata
  tracking-caps: 0.08em   # for the few uppercase labels (panel titles, status words)
spacing: [4, 8, 12, 16, 24, 32]
motion:
  mount: "panels appear with a 90ms stagger, 160ms ease-out, translateY(4px)->0"
  state: "colour changes 120ms; test rows tick in with 30ms stagger"
  reduced-motion: "everything instant"
```

## Layout

Workspace (desktop-first, min 1180px wide before panels collapse):

```
┌ status strip (36px) ─────────────────────────────────────────────────────────┐
│ BUG LAB   INCIDENT #012  ● CRITICAL  Flash Sale Oversold      18:42  ACTIVE │
├ files 240px ┬ editor (flex) ───────────────────────┬ investigation 360px ─────┤
│             │ tabs                                  │ INCIDENT LOGS TRACE      │
│             │                                       │ TESTS RUNTIME HYPOTHESIS │
│             │ Monaco                                │ HINTS                    │
│             │                                       │                          │
├─────────────┴───────────────────────────────────────┴──────────────────────────┤
│ terminal (240px, resizable)                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ RUN   BUILD   TESTS   REPRODUCE   SUBMIT                          RESET       │ 40px
└────────────────────────────────────────────────────────────────────────────────┘
```

- All dividers are 1px `line`. Drag handles are 4px wide hit areas that turn `line-strong` on hover.
- Panel titles: 11px uppercase mono, `ink-faint`, tracking 0.08em, 8px padding. That is the *only* place uppercase labels appear besides state words (ACTIVE, RESOLVED, PASSED, FAILED).
- Buttons: 28px tall, 1px `line` border, transparent fill, uppercase mono 11px. The primary action of the moment (SUBMIT when tests pass, TESTS otherwise) gets an `ink` border. Never a filled coloured button except SUBMIT after resolution turns `success`.
- Test rows: 24px, status glyph (✓ ✗ ○) in state colour, name in mono 12px, duration right-aligned `ink-faint`. Failed rows expand to show the assertion message in a `panel` block with a 2px `failure` left edge.
- Terminal: xterm.js with the palette above; background `ground`; cursor block `ink`.
- Severity dot: 8px circle in severity colour with a 1px darker ring; the dot pulses (opacity 1→0.6, 2s) only for `critical` and only while the run is active. No other ambient animation.

Dashboard and incident browser share the strip and the panel grammar. Progress bars are 6px tall, `line` track, `ink` fill (not a state colour: progress is not a state). Specialisation bars use the same. Numbers are always mono.

Incident report page: the report reads like the incident report in the brief, in a 720px column: number and severity on the first line, title at 28px, then description, symptoms as a plain list with `ink-faint` bullets, environment as a mono block on `panel`, expected/broken behaviour as two labelled paragraphs. One button: START INVESTIGATION / RESUME.

Resolved screen (after submit): the score table from the brief, mono, two columns, hairline between rows, then the postmortem in four labelled sections, then two diffs side by side (yours, reference) in mono with `success`/`failure` tinted lines at 12% opacity.

## Signature to avoid (checked in review)

Gradients, glows, shadows, radius, Inter/Geist/Space Grotesk, icon libraries, emoji, cards-in-cards, three-feature rows, centred hero, confetti or badges on success, purple anything, coloured text that is not a state.

## Copy voice

Terse, engineering. "Tests: 4 passed, 1 failed." not "Oops, some tests failed!". Errors say what happened and what to do: "Sandbox timed out after 60 s. The app is probably blocked on a lock; run it from the terminal to watch."
