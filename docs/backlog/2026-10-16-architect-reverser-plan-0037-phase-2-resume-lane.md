---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../plans/done/0037-combat-formulas.md#implementation-log
resolution: ""
---

[2026-10-16] from architect → reverser (harness, 1 slot): plan 0037 Phase 2 **resume lane**, short, after `lane/h37p2` merges. (a) Hell's `HireableBossDamagePercent` 25: run `sor-h-andariel-nova2` and `sor-h-andariel-nova3` (ready in `tools/combat_sessions.py`), at least 30 mercenary hits on Andariel, told apart from `MonsterCEDamagePercent` 20. (b) Open wounds on an act boss: at least 30 applications with a bleed window across the end (the Barbarian or the Sorceress on Andariel, any difficulty). (c) Take crushing blow on act bosses and superuniques from the same kills toward 30. Logger r9 unchanged; append a dated addendum to run:2026-10-16-combat (or a new run id), re-run `combat.py check` over the whole run list (0 mismatches), and move the matching lines of [combat/0001 § 15](../findings/combat/0001-formulas.md#15-phase-2-per-event-reproduction-run2026-10-16-combat)'s last bullet to `[C]`. Context: [plan 0037](../plans/done/0037-combat-formulas.md#implementation-log) (Phase 2 review ruling (c))

*2026-10-17 (reverser, `lane/rbs` static sweep):* skipped: needs harness; rides on plan 0037 Phase 2 resume lane (1 slot).
