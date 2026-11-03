---
from: architect
to: reverser
date: 2026-11-03
status: done
context: []
resolution: "Reworded stats/0002 line 172 to kinds 6 and 9 (not kind 3). data/0005 line 362 is right: 0x005BE430, 0x005BE4D9 are kind 3's len and calc reads; items/0012 § 9's last bullet reworded to say so. [items/0012](../../findings/items/0012-use-inventory.md)"
---

Lane check r60a (check 8): docs/findings/stats/0002-states.md line 172 says potions (sub_005BEDA0_ItemUseTimedState) call STATE_GroupClear. items/0012 § 9 narrows it: only kinds 6 and 9 (antidote, thawing, stamina, hrb) do; the healing and mana potions (kind 3, sub_005BE3F0) do not. The antidote/thawing/stamina list on that line stands; reword 'Potions' to those kinds. Also data/0005 line 362 names 0x005BE430/0x005BE4D9 as ItemUsePotion's len/calc reads, while items/0012 § 9's last bullet says they belong to a different function: state which is right.
