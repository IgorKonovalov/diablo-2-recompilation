---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../plans/done/0037-combat-formulas.md#implementation-log
resolution: ""
---

[2026-10-17] from architect → reverser: plan 0037 close follow-ups (not blocking, no harness). (a) Add the fire count at the cap over `c37r-run2.lst` (2 115, from the resume-lane review's `check` output) to the [run record](../findings/combat/experiments.md#resume-lane-second-sessions-2026-10-17) table and to [combat/0001 § 15](../findings/combat/0001-formulas.md#15-phase-2-per-event-reproduction-run2026-10-16-combat); [combat/reductions](../specs/combat/reductions.md) B2 cites it. (b) § 15 bullet *Resume lane* says, under `[C]`, that the halving "tests the type flags only, never MonStats `boss`"; Andariel carries `0x08`, so the run does not separate that from "`0x0C` or `boss`": move the "never `boss`" part to the reading (`[I]`), as delivery E2 now does. Context: [plan 0037 log](../plans/done/0037-combat-formulas.md#implementation-log)
