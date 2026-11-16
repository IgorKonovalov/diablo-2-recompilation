---
from: reverser
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/combat/experiments.md
resolution: "Tier B check 2026-11-16: accept with fixes (6); S5e whole merged into main; README 35 named not settled."
---

Tier B review of plan 0066 Phase 1 batch S5e part 1 (`lane/n66t`): the combat reduction and to-hit leaf
functions. Emulation run:2026-11-16-sweep2-s5e (`tools/combat_s5e_emu.py`; `workspace/logs/n66t/s5e/run/check.txt`
`100ff7eb…`, `manifest.sha256` `44d94245…`, passes from that directory; 17 300 cases, 0 mismatches, 118 of 127
controls separating, the 9 others named). 23 of the batch's 52 statements settled; outcomes, the remainders, totals,
judgment calls and the resume note for part 2 are in the plan log entry of 2026-11-16 (S5e part 1). Corrections to the
spec-writer in [2026-11-16-reverser-spec-writer-plan-0066-s5e-corrections](../2026-11-16-reverser-spec-writer-plan-0066-s5e-corrections.md).
Not blocking.

**2026-11-16, reverser (`lane/n66t`), extended to S5e whole.** Part 2 is on the same branch: the stat events, the
player's life tick and `COMBAT_BuildDamage` with an unarmed attacker,
[combat/0001 § 20](../../findings/combat/0001-formulas.md#20-plan-0066-batch-s5e-part-2-stat-events-life-tick-and-the-damage-builder-run2026-11-16-sweep2-s5e2),
[run:2026-11-16-sweep2-s5e2](../../findings/combat/experiments.md#run2026-11-16-sweep2-s5e2), new tool
`tools/combat_s5e2_emu.py` (`156dae37…`; part 1's tool and run unchanged), kept outputs
`workspace/logs/n66t/s5e/run2/` (`check.txt` `03b6603a…`, `manifest.sha256` `a5a0335d…`, passes from there; 11 200
cases, 0 mismatches, 174 of 227 controls separating, the 53 others named in the record). 24 of the 29 statements
left by part 1 settled, 7 of its 10 remainders in whole or in part; 5 statements and 3 remainders not settled in
budget, named with reasons. Please review S5e as a whole (parts 1 and 2); the part 2 outcomes, judgment calls and
totals are in the plan log entry of 2026-11-16 (S5e part 2). New corrections are appended to the corrections entry.

**2026-11-16, reverser (`lane/n66t`), part 3: S5e is complete.** The eight items part 2 left:
[combat/0001 § 21](../../findings/combat/0001-formulas.md#21-plan-0066-batch-s5e-part-3-the-defence-roll-with-a-shield-unit_getdefense-and-the-delivery-prologue-run2026-11-16-sweep2-s5e3),
[run:2026-11-16-sweep2-s5e3](../../findings/combat/experiments.md#run2026-11-16-sweep2-s5e3), new tools
`tools/combat_s5e3_emu.py` (`5f7cb4a6…`) and `tools/combat_s5e3_mas.py` (`71109513…`; parts 1–2 and S6f's tools and
runs unchanged), kept outputs `workspace/logs/n66t/s5e/run3/` (`check.txt` `ddbca2be…`, `manifest.sha256`
`03b20edd…`, passes from there; 12 000 cases, 0 mismatches, 96 of 107 controls separating, the 11 others named).
Seven of the eight settled in whole or in part; README 35's remainder is named not settled. Please review S5e as a
whole (parts 1–3); outcomes, judgment calls and totals are in the plan log entry of 2026-11-16 (S5e part 3).
Corrections 11–13 are appended to the corrections entry.
