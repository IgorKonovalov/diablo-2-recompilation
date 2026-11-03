---
from: architect
to: reverser
date: 2026-11-03
status: open
context:
  - ../plans/done/0056-harness-runner-efficiency.md#implementation-log
resolution: ""
---

[2026-11-03] from architect → reverser: plan 0056 Phase 4 ruled that a stage not reached is a failure under harness-play.md § Fresh process rule 5, and that a batch sharing a process must check each case's stage before the switch. The check is in tools/ai_sessions.py only (level_of against the start level, added after launch 5202 ran on past two town cases). Move it into tools/harness_runner.py as a case gate the next runner must supply (a stage-check callback, or an explicit no-sharing), with no-game tests. Done when batch or next_case refuses to switch without one and tooling.md § The runner library says so. The next lane migrating or writing a sharing runner does it; no slot needed.
