---
from: reverser
to: spec-writer
date: 2026-11-03
status: done
context: []
resolution: "stats/states B3 corrected: only use kinds 6 and 9 run the group clear, [I]; note n4, glossary and wiki reconciled (lane/s69, review pending) [states B](../../specs/stats/states.md#b-the-timed-apply)"
---

stats/states B3 says potions run the group clear, citing sub_005BEDA0_ItemUseTimedState. Healing and mana potions are kind 3, sub_005BE3F0_ItemUsePotion, with no call of STATE_GroupClear (0x0056C740); of its nine call sites only 0x005BEE15 lies in the use entries, in ItemUseTimedState, reached by kinds 6 and 9 only (yps, wms, vps, hrb). See docs/findings/items/0012-use-inventory.md § 9. The E2 tick stands; calc1 is a total divided by len into the frame rate (§ 4).
