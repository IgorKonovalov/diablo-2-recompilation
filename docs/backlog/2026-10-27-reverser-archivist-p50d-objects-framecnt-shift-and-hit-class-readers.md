---
from: reverser
to: archivist
date: 2026-10-27
status: open
context:
  - ../findings/anim/0003-movement-gates.md#65-objects-the-operate-frames
  - ../findings/anim/0003-movement-gates.md#7-the-hit-class
  - ../tables/Objects.md
  - ../tables/MonStats.md
  - ../tables/HitClass.md#open-questions
resolution: ""
---

Three table-doc links from plan 0050 P1.3 ([anim/0003](../findings/anim/0003-movement-gates.md)). Not blocking.

1. **Objects `FrameCnt0..7`.** The loader `sub_0063F690_ObjectsLoad` shifts the eight `FrameCnt` dwords left by 8
   after loading (`0x00640E33`–`0x00640E64`), so in memory they are frames << 8 (anim/0003 § 6.5, `[I]`). The
   [Objects](../tables/Objects.md) § Timing rows give the file's values (right as data); please add the load-time
   shift and the operate end (`OBJOP_Chest` queues object event 1 at `frame + FrameCnt1 + 1`; event 1 sets mode 2 when
   `Mode2` is set, without an animation start) with the finding's tags, and link anim/0003.
2. **HitClass open question.** [HitClass](../tables/HitClass.md#open-questions) asks what the server does with the
   class and how Weapons `hit class`, MonStats2 `HitClass` and the packet's `+0x60` relate: anim/0003 § 7 answers
   it (`[I]`): the low nibble from the attacker (weapon, 1 without; MonStats2; Missiles `HitClass`), an element
   nibble added in `COMBAT_GetHit`, and the server gate is `GetHitRoll`'s divisor (8 for 2, 6, 10, 11; 32 for 4, 8;
   64 for 5; 16 otherwise). Please link it there and in the Weapons, MonStats2 and Missiles § Timing rows.
3. **MonStats § Timing's `[L]` on the `9A`/`E9` walk base.** anim/0003 § 1.1 reads it (`[I]`): `MonStatsSpeeds`'
   lookup returns the fallback record, speed 256, so those rows get walk base `+0x036` 256 (run `+0x038` 128 below
   410). Please replace the `[L]` with the finding's reading and link it.
