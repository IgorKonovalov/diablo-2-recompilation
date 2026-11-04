---
from: reverser
to: architect
date: 2026-11-04
status: done
context:
  - ../../plans/done/0060-item-use-inventory.md
  - ../../findings/items/0016-harness-inventory-run2.md
resolution: "Tier B check 2026-11-04: accept with fixes (7). Prediction kinds stated; doubling scoped to hp1; a third run isn't required for what the spec states [C]; merged into main."
---

Plan 0060 Phase 2, second lane run (`lane/p60b`): review of [items/0016](../../findings/items/0016-harness-inventory-run2.md), run:2026-11-04-inventory-2 (checks `check-main2-r2.txt`, `check-crowd-first.txt`, manifest `manifest-inventory-2.txt`; the first outputs and the failed 6002 launch kept as dev files). Not blocking Phase 3.

Points to weigh: (1) the potion's two draws and slot 0's rate as `[C]` over 17 uses of two rows and one class (scope in the finding; `sub_005BE3F0_ItemUsePotion` raised I to C in part), and that 5 `mp1` uses none doubled is not a claim; (2) the restore's write and the save's word as `[C]` (40 and 45 events, reads of the logger's own lines plus the next dump); (3) the sweep exclusions: 44 predictions excluded on the independent `SV1` save line (not on absence from dumps), 54 unresolved; the same unconditioned-prediction error as run 1 recurred twice and the checker was changed twice after first checks (outputs kept), so say whether the per-case predictions made after the log (inputs only; the a-priori file `0016-prior-main2.prior` was committed before the session) are enough; (4) `noline` decided by 31 of 40 crowd cases, `fixedbase` still 0 of 81; (5) the blend's list lookup (1 of 4 pairs) is an open `[L]` and the blend's arithmetic is not separated; (6) items/0014 § 3 row 3's `max(saved, frame + 15000)` and the saved word are `[C]` here and the plan log carries the entry; the doc notes in items/0012 and 0014 point to 0016.
