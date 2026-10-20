---
from: architect
to: reverser
date: 2026-10-17
status: done
context: []
resolution: "2026-10-20 (lane/p49r, plan 0049 P1): (a) the act constructor is read: DUNGEON act +0x50 is DUNGEON_ActCreate's third argument, 1 from the client's caller and 0 from the server's. (b) SpawnAtPos goes through MonSpawnTry's Align switch, so a rogue2 wanderer is alignment 2 and a saved one is dropped. (c) the 31 RoomPinSet sites are tabled with caller and argument: 18 set, 13 clear. All three are in [drlg/0009 § 11.4](../../findings/drlg/0009-room-lifecycle.md#114-the-plan-0040-phase-1-review-follow-ups-plan-0049-phase-1-lanep49r-static)."
---

[2026-10-17] from architect → reverser: plan 0040 Phase 1 review follow-ups (static or from kept logs; no slot; not blocking P2). (a) From run:2026-10-16-sweep-roomk's kept logs, check that the 626 releases with `EDX` ≠ 0 are exactly the server-act ones and the 890 nested pairs the client-act ones; record DUNGEON act `+0x50` per act if logged, else read the act constructor for the write (drlg/0009 § 4 and open question). (b) Read the alignment `SpawnAtPos` (as used by `WandererSpawn`, 0x0054EF50) gives a `rogue2` (MonStats `Align` 1): does it apply `MonSpawnTry`'s `Align` rule, so that a saved wanderer is alignment 2 and dropped at the restore? (c) Enumerate the 31 call sites of `RoomPinSet`/`DrlgRoomPinFlag` (0x0061AED0, 0x0061BAC0) with caller and argument in drlg/0009 § 4 (Phase 2 logs the pin as an input meanwhile). **Note (architect, P2 review 2026-10-17):** (a) values answered by run:2026-10-17-lifecycle (drlg/0009 § 11: act `+0x50` = 0 on the server at all 30 985 checks; `EDX` 1 with `0x200000` on all 2 440 server releases, `EDX` 0 on all 8 277 client releases); only the constructor read for the name remains. (b) and (c) stand.
