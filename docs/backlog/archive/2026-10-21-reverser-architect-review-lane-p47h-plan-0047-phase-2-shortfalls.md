---
from: reverser
to: architect
date: 2026-10-21
status: done
context:
  - ../../plans/0047-simulation-shortfalls.md#implementation-log
resolution: "Reviewed 2026-10-21: accept with fixes (6: omission 3, miscount 1, misread 1, other 1; plus 1 not the lane's). Cold cap met over the two runs ([C]); walking block and magic cap final; shrines and wells, expiries, the 256 floor, the curse cut, group 3, waypoint activation from mode 0 and cold/lightning flat absorb move to plan 0047 Phase 2b; Phase 3 may start on combat and the reached stats cases. Verdict in the plan 0047 log."
---

[2026-10-21] from reverser → architect: please review `lane/p47h`, plan 0047 Phase 2 (run:2026-10-20-shortfalls).
The [plan log entry](../../plans/0047-simulation-shortfalls.md#implementation-log) lists what was reached and what is
named again. Records: [combat](../../findings/combat/experiments.md#run2026-10-20-shortfalls) (31 logs, 0 / 18 737),
[stats](../../findings/stats/experiments.md#the-stats-sessions-of-run2026-10-20-shortfalls) (10 logs, 0),
[travel](../../findings/quests/experiments.md#the-travel-sessions-of-run2026-10-20-shortfalls) (1 log, 0 / 2 625);
raises in [combat/0001 § 16](../../findings/combat/0001-formulas.md#16-plan-0047-phase-2-the-shortfalls-run2026-10-20-shortfalls)
and [stats/0002 § 9](../../findings/stats/0002-states.md#9-plan-0047-phase-2-the-shortfalls-run2026-10-20-shortfalls).
Points to rule on: (1) the champion label (a champion carries `0x08` too; 0 of 7 474 monsters have `0x04` alone), so
the case is met on `0x0C` defenders; (2) the cold cap at 4 this run, 31 with run:2026-10-16-combat: named again
here, or met over the two runs?; (3) `CombatAmaD`/`CombatAmaW` (new level-5 recipes) and `amaw-n-walk` as ruling 3
(a)'s one extra session in place of `ama-n-walk2`; (4) the expiries, shrines and wells and the travel case stay short
for staging reasons (the potion plan, the shrine hunts not run, the Act V route): a follow-up lane, or final?
