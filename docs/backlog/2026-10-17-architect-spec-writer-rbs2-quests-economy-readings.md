---
from: architect
to: spec-writer
date: 2026-10-17
status: done
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../findings/quests/0001-progression.md
  - ../findings/items/0011-economy.md
resolution: "Done: (b) in items/economy (lane/p43s, the writer of game+0x6A); (a) and (c) folded into quests/progression § C and quests/travel § E by lane/p42s. Closed at the lane/p42r review, 2026-10-20."
---

`lane/rbs2` review follow-up: three new `[I]` readings for the Phase 3 passes of plans 0042 (quests) and 0043 (economy). Fold them when those phases open; not blocking. (a) quests/0001 § 3, *the flows behind `rejoin`*: `rejoin` = 1 only at the two new-character builders, and 0 at the two save readers. A character made from a header stub, or by the version < 92 reader, joins twice, first with 1 and then with 0. `PlayerLoad`'s no-save branch joins once. The double join is `[I]` until a Phase 2 log of 0x0056A072 and 0x005344EF. (b) items/0011, *the writer of `game+0x6A`*: `GameCreate` (0x00530CFF) takes the byte from the client's create message, built from `g_ClientGameMode` (0 → 3, 6 → 1, 8 → 2, else 0). The names of modes 6 and 8 stay `[L]`, under *Open questions* only. (c) quests/0002 § 9: PlayerData `+0x4C` is cleared by the client's packet 0x48 (0x0054C590 → 0x005350B0).

**2026-10-19 (spec-writer, `lane/p43s`).** Part (b) folded into [items/economy § G](../specs/items/economy.md#g-gold-payment-caps-piles-and-the-death-loss)
(the G10 note on the game type, `[I]`; the names of modes 6 and 8 under *Open questions* as `[L]`). Parts (a) and (c)
wait for the plan 0042 Phase 3 quests spec; the entry stays open for them.

*2026-10-19 (spec-writer, `lane/p42s`):* the quests readings are folded: (a) the `rejoin` flows and the stub
character's double join (now `[C]` by run:2026-10-18-quests2) in [quests/progression § C](../specs/quests/progression.md#c-the-join-and-the-game-creators-history);
(c) packet 0x48 clearing `+0x4C` in [quests/travel § E](../specs/quests/travel.md#e-act-change-through-an-npc). Item (b)
belongs to the economy lane (`lane/p43s`); the entry stays open for whichever lane finishes last to close it.
