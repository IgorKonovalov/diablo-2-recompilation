---
from: reverser
to: reverser
date: 2026-10-17
status: done
context:
  - ../../findings/multiplayer/0001-cases.md#4-the-hostility-declaration-and-the-two-travel-gates
resolution: "Folded into quests/0002 at the plan 0044 Phase 1 review (2026-10-17, lane/p44r): § 6 pseudocode, § 9, the closing list, the three hostility verdicts and the 0x005A5E50 open question. Symbol rows for 0x005A5E50 and 0x00535B10 go with the Phase 2 follow-up."
---

When lane/p42r (plan 0042 Phase 1) merges, fold [multiplayer/0001 § 4](../../findings/multiplayer/0001-cases.md#4-the-hostility-declaration-and-the-two-travel-gates) into quests/0002: (a) § 9 and § 6 say an own portal is never delayed and that `0x0055B6C0` compares against the owner's entry; both gate calls pass EDX = 0 (0x0054C5F5, 0x005848BA), so they read the operator's own PlayerData `+0x160`, and no portal is exempt. (b) The first portal test, `0x00535B10` (operator hostile to any player) with owner ≠ operator, answers the Phase 1b verdict 'a hostile player cannot use other players' portals' (not covered → held). (c) The open question on `0x005A5E50`: it is the hostility toggle (town only, level 9 or more on both, a 60 s pair stamp). Use p42r's names (`PlayerTickGet`, `PlayerTickSet`) for the symbol rows.
