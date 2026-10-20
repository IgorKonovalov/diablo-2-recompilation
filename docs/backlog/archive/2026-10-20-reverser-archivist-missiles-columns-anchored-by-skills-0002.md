---
from: reverser
to: archivist
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0002-missiles.md
  - ../../tables/Missiles.md
resolution: "Done 2026-10-20 (archivist, lane/p46a, plan 0046 P0): 43 Missiles meaning cells raised to skills/0002's [I] with section links (LastCollide, SrcTown, Holy reworded to the code; 64 948 open question struck; HitClass byte from § Functions); KnockBack-as-byte not written, no sentence in skills/0002 [../tables/Missiles.md#columns]"
---

Not blocking. [skills/0002](../../findings/skills/0002-missiles.md) (plan 0045 P1.2) anchors the server readers of these Missiles columns; please link them in [Missiles](../../tables/Missiles.md) and raise their meanings from `[L]` to the finding's `[I]` (do not copy the finding's prose; point at the section):

- § 2 (creation): `Vel`, `VelLev` (`(VelLev · lvl) / 8 + Vel`, then `<< 8` and × 75/100), `MaxVel` (`<< 8`), `Accel` (raw, every fifth step), `Range`/`LevRange` (lifetime in frames), `Activate` (unit collision from that frame), `SubLoop`/`SubStart`/`SubStop` (loops on request), `CollideType` (the missile unit's mode; index of `g_MissileCollideTypes`), `Collision`, `CanDestroy`, `CanSlow` (state 87, stat 161), `LastCollide` (**the code reads it as "skip the last unit hit", the owner first**, not the table's plain "keeps colliding on its last frame"), `DamageRate` (stat 327).
- § 3 (damage at creation): `Skill`, `MissileSkill`, `SrcDamage` (`0xFF` = no weapon share for a skill missile), `SrcMissDmg`, `Half2HSrc`, `ApplyMastery`, `Holy` (bits 1/2/4 = bypass flags 0x100/0x200/0x400), `Pierce` (count from stat 328).
- § 4 (frame): `pSrvDoFunc` (s16 > 0 and < 53), `Town`, `SrcTown` (ends the missile when a monster owner is in town; a player owner always does).
- § 5 (hit): `pSrvHitFunc` and `pSrvDmgFunc` (s16 > 0 and < 71 / 31: **row 568's 64 948 is never called**, which answers the table doc's open question), `Explosion` (no damage without a hit function), `CollideKill`, `CollideFriend`, `NextHit`/`NextDelay` (state 86 `justhit` on the unit), `ToHit` (owner's to-hit roll with missile stat 19), `AlwaysExplode` (the hit function on a miss and on a unit-less call).
- § 4, do 2 and 14; § 8: `SubMissile1`, `SrvCalc1` (only tested > 0 by do 2), `Param1`/`Param2` (do 14), `sHitPar1` (hit 22).
- `ExplosionMissile` has no server reader by the pattern scan (one client site), § Dead ends.

Also the column `HitClass` is read as a byte (`+0x94`, `sub_0064A5A0_MissileHitClass`) and `KnockBack` as a byte (`+0xAE`). The Skills column readers `srvmissile` (`+0x46`, s16) and `lob` are § 2 of the same finding.
