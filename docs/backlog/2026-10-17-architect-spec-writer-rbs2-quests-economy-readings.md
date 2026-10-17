---
from: architect
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../findings/quests/0001-progression.md
  - ../findings/items/0011-economy.md
resolution: ""
---

`lane/rbs2` review follow-up: three new `[I]` readings for the Phase 3 passes of plans 0042 (quests) and 0043 (economy). Fold them when those phases open; not blocking. (a) quests/0001 § 3, *the flows behind `rejoin`*: `rejoin` = 1 only at the two new-character builders, and 0 at the two save readers. A character made from a header stub, or by the version < 92 reader, joins twice, first with 1 and then with 0. `PlayerLoad`'s no-save branch joins once. The double join is `[I]` until a Phase 2 log of 0x0056A072 and 0x005344EF. (b) items/0011, *the writer of `game+0x6A`*: `GameCreate` (0x00530CFF) takes the byte from the client's create message, built from `g_ClientGameMode` (0 → 3, 6 → 1, 8 → 2, else 0). The names of modes 6 and 8 stay `[L]`, under *Open questions* only. (c) quests/0002 § 9: PlayerData `+0x4C` is cleared by the client's packet 0x48 (0x0054C590 → 0x005350B0).
