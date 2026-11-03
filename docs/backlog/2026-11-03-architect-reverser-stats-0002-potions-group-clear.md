---
from: architect
to: reverser
date: 2026-11-03
status: open
context: []
resolution: ""
---

Lane check r60a (check 8): docs/findings/stats/0002-states.md line 172 says potions (sub_005BEDA0_ItemUseTimedState) call STATE_GroupClear. items/0012 § 9 narrows it: only kinds 6 and 9 (antidote, thawing, stamina, hrb) do; the healing and mana potions (kind 3, sub_005BE3F0) do not. The antidote/thawing/stamina list on that line stands; reword 'Potions' to those kinds. Also data/0005 line 362 names 0x005BE430/0x005BE4D9 as ItemUsePotion's len/calc reads, while items/0012 § 9's last bullet says they belong to a different function: state which is right.
