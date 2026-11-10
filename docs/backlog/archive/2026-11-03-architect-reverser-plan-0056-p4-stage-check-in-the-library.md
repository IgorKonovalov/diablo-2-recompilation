---
from: architect
to: reverser
date: 2026-11-03
status: done
context:
  - ../../plans/done/0056-harness-runner-efficiency.md#implementation-log
resolution: "Plan 0063 Phase 2b (lane/n63s): tools/harness_runner.py batch() now requires stage= (NO_SHARING, or a callable stage(case) run after each kept try; a False fails the try 'stage not reached'), and next_case() raises HarnessError before any click unless the batch try just before was kept and passed it (one switch per pass; always under NO_SHARING; outside a batch only with stage_checked=True). ai_sessions passes its level check (left_start), the other batch runners NO_SHARING, probe0056 stage_checked=True. Tests: test_harness_runner.py StageGate and RunnersGate (60 pass). tooling.md § The runner library and harness-play.md § Fresh process rule 5 say so. [plan](../../plans/done/0063-backlog-sweep-7.md#implementation-log)"
---

[2026-11-03] from architect → reverser: plan 0056 Phase 4 ruled that a stage not reached is a failure under harness-play.md § Fresh process rule 5, and that a batch sharing a process must check each case's stage before the switch. The check is in tools/ai_sessions.py only (level_of against the start level, added after launch 5202 ran on past two town cases). Move it into tools/harness_runner.py as a case gate the next runner must supply (a stage-check callback, or an explicit no-sharing), with no-game tests. Done when batch or next_case refuses to switch without one and tooling.md § The runner library says so. The next lane migrating or writing a sharing runner does it; no slot needed.
