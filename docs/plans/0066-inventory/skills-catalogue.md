# Plan 0066 inventory: skills/catalogue

- **Spec:** [skills/catalogue](../../specs/skills/catalogue.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 109; the *Count* column sums to 109.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 44 | Entry points | A missile's frame — g_MissileSrvDoFuncs[pSrvDoFunc] (missiles § D) | `data:g_MissileSrvDoFuncs@0x0073C768` | ? | ? | ? | 1 |
| 2 | 46 | Entry points | A missile's damage packet is built — g_MissileSrvDmgFuncs[pSrvDmgFunc] (missiles § F) | `data:g_MissileSrvDmgFuncs@0x0073C960` | ? | ? | ? | 1 |
| 3 | 80 | Constants | g_Circle64X, g_Circle64Y — 64 s32 each: points on a radius-30 circle | `0x006E2B78` | ? | ? | ? | 1 |
| 4 | 100 | A. How an entry is written | unit's overlay. | `data:g_MissileSrvHitFuncs@0x0073C840` | ? | ? | ? | 1 |
| 5 | 118 | A. How an entry is written | draws are theirs. | `fn:sub_0056D940_SpawnOwnedMonster@0x0056D940` | ? | ? | ? | 1 |
| 6 | 121 | A. How an entry is written | this spec names them in their batch and links there. | `fn:SKILL_AttackDo@0x0056F070` | ? | ? | ? | 1 |
| 7 | 170 | B. Every draw, by seed | do 140 — for the count and the tries ; the arm | `0x0063F473` | ? | ? | ? | 1 |
| 8 | 184 | B. Every draw, by seed | (prg 37) and (prg 143) are read, | `0x005CD110` | ? | ? | ? | 2 |
| 9 | 194 | B. Every draw, by seed | Range(caster, 100) at the last charge; do 107's three RangeB(caster, max − min). | `0x005CFD20` | ? | ? | ? | 1 |
| 10 | 215 | C. Missile do entries (mdo 1–36) | … 7 and mdo 34 in mdo 3; a missing record, owner or sub-missile returns 2. | `fn:sub_005B0BC0_MissDo01Thunk@0x005B0BC0` | ? | ? | ? | 1 |
| 11 | 216 | C. Missile do entries (mdo 1–36) | ) mdo 1, 3, 5 and 23 are tier A: missiles § G. | `0x005AE1F0` | ? | ? | ? | 1 |
| 12 | 228 | C. Missile do entries (mdo 1–36) | after: mdo 1 | `0x005AE680` | ? | ? | ? | 1 |
| 13 | 232 | C. Missile do entries (mdo 1–36) | with bit 0 set and a live hostile target: re-plan the path to it | `0x005AE780` | ? | ? | ? | 1 |
| 14 | 233 | C. Missile do entries (mdo 1–36) | bit 0 is written by do 10 when cast at a unit | `fn:sub_005DB6D0_SkillDo10GuidedMissile@0x005DB6D0` | ? | ? | ? | 1 |
| 15 | 240 | C. Missile do entries (mdo 1–36) | after: refused on a non-zero result, else SubMissile1 at the point; mdo 1 | `0x005A9820` | ? | ? | ? | 1 |
| 16 | 246 | C. Missile do entries (mdo 1–36) | C6. mdo 13 (, Bone Wall): | `fn:sub_005AEDA0_MissileSpawnOwnedMonster@0x005AEDA0` | ? | ? | ? | 1 |
| 17 | 261 | C. Missile do entries (mdo 1–36) | after: the +/+ stores | `0x005AF170` | ? | ? | ? | 1 |
| 18 | 264 | C. Missile do entries (mdo 1–36) | … is gone; after a found chest's drop the store follows the boundary ; that store | `0x005AF300` | ? | ? | ? | 1 |
| 19 | 267 | C. Missile do entries (mdo 1–36) | after: the gold pile at that spot | `0x005AF300` | ? | ? | ? | 1 |
| 20 | 273 | C. Missile do entries (mdo 1–36) | without it; the roll and the heal | `0x005B0940` | ? | ? | ? | 1 |
| 21 | 278 | C. Missile do entries (mdo 1–36) | … and mdo 1; the return value, 1 after mdo 1 or 2 after the hit | `0x005AF540` | ? | ? | ? | 1 |
| 22 | 284 | C. Missile do entries (mdo 1–36) | after: the second creation, at the negated offset | `0x005AF620` | ? | ? | ? | 1 |
| 23 | 305 | C. Missile do entries (mdo 1–36) | two SubMissile1 at ±(+, +); after: the second | `0x005B01F0` | ? | ? | ? | 1 |
| 24 | 314 | C. Missile do entries (mdo 1–36) | after: the tyrael3 spawn (class 521) and the room pin | `0x005B0A40` | ? | ? | ? | 1 |
| 25 | 320 | C. Missile do entries (mdo 1–36) | Missiles § Function index. | `0x005AF790` | ? | ? | ? | 1 |
| 26 | 349 | D. Missile damage entries (mdmg 1–14) | after: the overlay as stat 178 on the unit's flag- list | `fn:sub_00621E40_UnitSetOverlayStat@0x00621E40` | ? | ? | ? | 1 |
| 27 | 363 | E. Missile hit entries 1–29 | AreaHitAt(owner; x, y, radius, packet, 0); return 1 ; the return | `0x005A9A70` | ? | ? | ? | 1 |
| 28 | 372 | E. Missile hit entries 1–29 | callee-saved register | `0x005A9BF0` | ? | ? | ? | 1 |
| 29 | 378 | E. Missile hit entries 1–29 | … (≥ 0 path): stat 134 ← 0, the disc , the area hit, return 3 | `0x005AA2FA` | ? | ? | ? | 1 |
| 30 | 386 | E. Missile hit entries 1–29 | any monster or player when sHitPar2 = 0), else 4 ; the refused-ally return | `0x005A9FB0` | ? | ? | ? | 1 |
| 31 | 400 | E. Missile hit entries 1–29 | after: each bolt's +/+ ← its direction | `0x005ABB00` | ? | ? | ? | 1 |
| 32 | 403 | E. Missile hit entries 1–29 | after: the next bolt and its count − 1 | `0x005AA730` | ? | ? | ? | 1 |
| 33 | 440 | F. Missile hit entries 31–59 and row 568 | after the overlay: the life write; the return, 1 with CollideKill else 0 | `0x005AC452` | ? | ? | ? | 1 |
| 34 | 456 | F. Missile hit entries 31–59 and row 568 | after: HitSubMissile2, then 3 | `0x005AC870` | ? | ? | ? | 1 |
| 35 | 462 | F. Missile hit entries 31–59 and row 568 | word as the class, so the missiles are row 0 (arrow) | `0x005AC940` | ? | ? | ? | 1 |
| 36 | 487 | F. Missile hit entries 31–59 and row 568 | the reading. | `data:g_MissileSrvHitFuncs@0x0073C840` | ? | ? | ? | 1 |
| 37 | 515 | G. Sorceress (st 11–14; do 17–29, 144) | after: the packet's result /= 9 (a stun) when the flag is set | `0x005C98F0` | ? | ? | ? | 1 |
| 38 | 521 | G. Sorceress (st 11–14; do 17–29, 144) | a srvmissilea at the unit found, MISSILE_HitUnit, node + ← its guid | `0x005CA4D0` | ? | ? | ? | 1 |
| 39 | 528 | G. Sorceress (st 11–14; do 17–29, 144) | … 1 at (x, y) and summon + 2 at (x + 1, y − 1) | `0x005CA910` | ? | ? | ? | 1 |
| 40 | 537 | G. Sorceress (st 11–14; do 17–29, 144) | after: the cell's meaning and do 24's three creations | `0x005C9EA0` | ? | ? | ? | 1 |
| 41 | 565 | H. Amazon (st 4–10; do 6–8, 10–16) | st 8 uses ammunition | `0x0056BC80` | ? | ? | ? | 1 |
| 42 | 574 | H. Amazon (st 4–10; do 6–8, 10–16) |  | `fn:SKILLS_GetToHit@0x006449F0` | ? | ? | ? | 1 |
| 43 | 579 | H. Amazon (st 4–10; do 6–8, 10–16) | after: the callback hands each unit to STATE_ApplyTimed | `0x005DB150` | ? | ? | ? | 1 |
| 44 | 585 | H. Amazon (st 4–10; do 6–8, 10–16) | after: the other creations, group by group, stepped by (sx, sy) | `0x005DB410` | ? | ? | ? | 1 |
| 45 | 593 | H. Amazon (st 4–10; do 6–8, 10–16) | after: the charged bolts and the lightning chain | `fn:sub_005DB850_SkillDo11ChargedStrike@0x005DB850` | ? | ? | ? | 1 |
| 46 | 600 | H. Amazon (st 4–10; do 6–8, 10–16) |  | `fn:sub_005DBC60_SkillDo13Fend@0x005DBC60` | ? | ? | ? | 1 |
| 47 | 605 | H. Amazon (st 4–10; do 6–8, 10–16) | after: what the spawn makes of +, the life, level, events and owner | `0x005DC1E0` | ? | ? | ? | 1 |
| 48 | 639 | I. Necromancer (st 15–21; do 30–32, 55–63) | after: the callbacks apply the state per unit | `0x005C3F20` | ? | ? | ? | 1 |
| 49 | 648 | I. Necromancer (st 15–21; do 30–32, 55–63) | … 55's one RangeB on the target's seed (the corpse's damage roll) and its area hit | `0x005C4DF0` | ? | ? | ? | 1 |
| 50 | 651 | I. Necromancer (st 15–21; do 30–32, 55–63) | after: do 58's one RangeB on the target's seed | `0x005C56C0` | ? | ? | ? | 1 |
| 51 | 663 | I. Necromancer (st 15–21; do 30–32, 55–63) | after: the summons' levels and stats | `0x005C5100` | ? | ? | ? | 1 |
| 52 | 665 | I. Necromancer (st 15–21; do 30–32, 55–63) | (class 3 is the paladin in PlayerClass order) | `fn:sub_005C2FF0_SkillClass3SelfHit@0x005C2FF0` | ? | ? | ? | 1 |
| 53 | 672 | J. Paladin (st 29, 31, 35–37; do 64–67, 73, 79–82, 150) | paladin entry calls . | `0x005C2FF0` | ? | ? | ? | 1 |
| 54 | 687 | J. Paladin (st 29, 31, 35–37; do 64–67, 73, 79–82, 150) | after: the target pass and its per-unit draws (§ B2) | `fn:sub_005CF3A0_AuraHitDo@0x005CF3A0` | ? | ? | ? | 1 |
| 55 | 720 | J. Paladin (st 29, 31, 35–37; do 64–67, 73, 79–82, 150) |  | `0x005CEFD5` | ? | ? | ? | 1 |
| 56 | 725 | J. Paladin (st 29, 31, 35–37; do 64–67, 73, 79–82, 150) | ResolveAndQueue treats a word with both is not followed. | `fn:sub_005CE9F0_SkillDo150Smite@0x005CE9F0` | ? | ? | ? | 1 |
| 57 | 730 | J. Paladin (st 29, 31, 35–37; do 64–67, 73, 79–82, 150) | result. | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | ? | ? | ? | 1 |
| 58 | 732 | J. Paladin (st 29, 31, 35–37; do 64–67, 73, 79–82, 150) | callees past COMBAT_ResolveAndQueue and COMBAT_DeliverQueued are unfollowed. | `0x005CE9F0` | ? | ? | ? | 1 |
| 59 | 746 | K. Barbarian (st 32–34, 38–41; do 2, 9, 68–72, 74–78) | after: st 32's and st 39's elemental SKILLS_RollElemDamage on the caster's seed | `0x005D97F0` | ? | ? | ? | 1 |
| 60 | 769 | K. Barbarian (st 32–34, 38–41; do 2, 9, 68–72, 74–78) |  | `fn:sub_005D81C0_SkillDo69FindPotion@0x005D81C0` | ? | ? | ? | 1 |
| 61 | 776 | K. Barbarian (st 32–34, 38–41; do 2, 9, 68–72, 74–78) | after: the 64 creations and sub_005D8290_UnitApplyAuraState | `0x005D83E0` | ? | ? | ? | 1 |
| 62 | 807 | K. Barbarian (st 32–34, 38–41; do 2, 9, 68–72, 74–78) | missiles B2's "no to-hit for a player's skill missile". | `0x005D8943` | ? | ? | ? | 1 |
| 63 | 824 | L. Druid (st 56–58; do 114–124; entries 145, 146) | after: SummonSetLevel, SummonInitStats; do 115 sets stat 12 ← max(calc2, 1) and state 150 | `0x005C6A80` | ? | ? | ? | 1 |
| 64 | 827 | L. Druid (st 56–58; do 114–124; entries 145, 146) | after: its list (no max(…, 1) on its length) and the remove callback | `0x005C6C50` | ? | ? | ? | 1 |
| 65 | 838 | L. Druid (st 56–58; do 114–124; entries 145, 146) | r stored at the used node's + (rng/seeds' Armageddon cast draw) | `fn:sub_005C8190_SkillDo124PeriodicState@0x005C8190` | ? | ? | ? | 1 |
| 66 | 849 | L. Druid (st 56–58; do 114–124; entries 145, 146) | Range(caster, 2r + 1) for a free point, x first | `fn:sub_005C8520_SkillDo146Armageddon@0x005C8520` | ? | ? | ? | 1 |
| 67 | 865 | L. Druid (st 56–58; do 114–124; entries 145, 146) |  | `fn:STATES_Load@0x00618100` | ? | ? | ? | 1 |
| 68 | 870 | L. Druid (st 56–58; do 114–124; entries 145, 146) | after: the further creations | `0x005C7040` | ? | ? | ? | 1 |
| 69 | 879 | L. Druid (st 56–58; do 114–124; entries 145, 146) | after: MISSDATA_SetSeedLow(missile, b) | `fn:sub_005C8080_SkillDo123Volcano@0x005C8080` | ? | ? | ? | 1 |
| 70 | 926 | M. Assassin (st 22–28; do 33–35, 42–52, 54; progressive 36–4 | charge; the deliveries and the finisher | `0x005D31BF` | ? | ? | ? | 1 |
| 71 | 947 | M. Assassin (st 22–28; do 33–35, 42–52, 54; progressive 36–4 | after: the rings' remaining creations, an endless loop for a step count of 0 | `0x005D4657` | ? | ? | ? | 1 |
| 72 | 962 | M. Assassin (st 22–28; do 33–35, 42–52, 54; progressive 36–4 | … the summons' set-up, do 44's teleport of the trap to the caster, the area callbacks | `0x005D5FB7` | ? | ? | ? | 1 |
| 73 | 964 | M. Assassin (st 22–28; do 33–35, 42–52, 54; progressive 36–4 | srvmissilea (119 frostnova, 90 nova) centred on the cast's target unit; nothing without one | `0x005D4DB0` | ? | ? | ? | 1 |
| 74 | 968 | M. Assassin (st 22–28; do 33–35, 42–52, 54; progressive 36–4 | so its chance computes level(target) + slvl − level(target). | `0x005D5AEB` | ? | ? | ? | 1 |
| 75 | 970 | M. Assassin (st 22–28; do 33–35, 42–52, 54; progressive 36–4 | M2. Psychic Hammer's do has the same form: both reads are push ebx, the target. | `0x005D31D9` | ? | ? | ? | 1 |
| 76 | 1012 | N. Item, charge and shrine callers (st 3, do 4, 113, 151) | after: both reach sub_005BF240_ItemUse | `0x005BF240` | ? | ? | ? | 1 |
| 77 | 1016 | N. Item, charge and shrine callers (st 3, do 4, 113, 151) | after: MISSDATA_SetSeedLow(missile, calc1) | `0x005CA330` | ? | ? | ? | 1 |
| 78 | 1033 | N. Item, charge and shrine callers (st 3, do 4, 113, 151) | … further tries, helper 3's corpse pick, the restore on the other paths and the messages | `0x005FDC3B` | ? | ? | ? | 1 |
| 79 | 1056 | N. Item, charge and shrine callers (st 3, do 4, 113, 151) | after: shrine 19's life loss and sixteen fireballs; 21/22's potions and six missiles | `0x00582E72` | ? | ? | ? | 1 |
| 80 | 1061 | N. Item, charge and shrine callers (st 3, do 4, 113, 151) | on-death, on-level-up, the item-use entries or charges; no other call of SKILLS_SrvDo passes 1. | – | ? | ? | ? | 1 |
| 81 | 1065 | N. Item, charge and shrine callers (st 3, do 4, 113, 151) | links. | `0x005FDB96` | ? | ? | ? | 1 |
| 82 | 1068 | N. Item, charge and shrine callers (st 3, do 4, 113, 151) | maximum from the player's skills and calls PetLimit. | `fn:sub_00575900_PetLimitRefresh@0x00575900` | ? | ? | ? | 1 |
| 83 | 1087 | O. Monster skills, Skills rows 156–189 (st 42–53; do 83–98,  | after: do 83's QueuedHitRemove and SKILLS_SrvStart(id, lvl, 0) | `0x005CAF30` | ? | ? | ? | 1 |
| 84 | 1111 | O. Monster skills, Skills rows 156–189 (st 42–53; do 83–98,  | … 89's state-2 landing and path plan; do 91's spawn at the node's point with sumoverlay | `0x005CB982` | ? | ? | ? | 1 |
| 85 | 1126 | O. Monster skills, Skills rows 156–189 (st 42–53; do 83–98,  | … spawns (mode 8, up to 2n tries) and UnitKilled; do 97's path target and mode | `0x005CB027` | ? | ? | ? | 1 |
| 86 | 1140 | O. Monster skills, Skills rows 156–189 (st 42–53; do 83–98,  | classes 141–145 or 396–400 passing get (id, lvl, , , 0) | `0x005CC5DE` | ? | ? | ? | 1 |
| 87 | 1144 | O. Monster skills, Skills rows 156–189 (st 42–53; do 83–98,  | spawn row (sandmaggot1..5 → maggotegg1..5, spawnmode S1) | tbl:Skills.txt:srvdofunc | ? | ? | ? | 1 |
| 88 | 1169 | P. Monster skills, Skills rows 190–289 (st 54, 55, 59, 60, 6 | re-queue at frame + 3 or an end at frame + 13) | `0x005CCE25` | ? | ? | ? | 1 |
| 89 | 1188 | P. Monster skills, Skills rows 190–289 (st 54, 55, 59, 60, 6 |  | `0x005CDAAB` | ? | ? | ? | 1 |
| 90 | 1207 | P. Monster skills, Skills rows 190–289 (st 54, 55, 59, 60, 6 | P4. the data joins: | tbl:Skills.txt:srvdofunc | ? | ? | ? | 1 |
| 91 | 1247 | Q. Monster skills, Skills rows 290–338 (st 61–63; do 128–137 | Baal's arm (base 544, baalcrab, also Uber Baal's; ): | `0x0063F473` | ? | ? | ? | 1 |
| 92 | 1255 | Q. Monster skills, Skills rows 290–338 (st 61–63; do 128–137 | turns on a word an earlier call left on the stack | `0x005D2C20` | ? | ? | ? | 1 |
| 93 | 1265 | Q. Monster skills, Skills rows 290–338 (st 61–63; do 128–137 | through the remaining tries (more draws, several tentacles); 1 | `0x005D2E0E` | ? | ? | ? | 1 |
| 94 | 1275 | Q. Monster skills, Skills rows 290–338 (st 61–63; do 128–137 | after: the class change | `0x005D1E10` | ? | ? | ? | 1 |
| 95 | 1286 | Q. Monster skills, Skills rows 290–338 (st 61–63; do 128–137 | +/seed word from the offsets; st 63's missile and | `0x005D1C88` | ? | ? | ? | 1 |
| 96 | 1296 | Q. Monster skills, Skills rows 290–338 (st 61–63; do 128–137 | roll and area hit; do 137's and | `0x005D21B0` | ? | ? | ? | 1 |
| 97 | 1308 | Q. Monster skills, Skills rows 290–338 (st 61–63; do 128–137 | other's owner) and detach ; do 135's second try (mode argument 4); start 61's revive | `0x005D18E0` | ? | ? | ? | 1 |
| 98 | 1312 | Q. Monster skills, Skills rows 290–338 (st 61–63; do 128–137 | Impregnate (300) summon 551 (painworm1) | tbl:Skills.txt:srvmissilea | ? | ? | ? | 1 |
| 99 | 1318 | Q. Monster skills, Skills rows 290–338 (st 61–63; do 128–137 | That the stock row 301 takes that exit is Q6's data join. | tbl:Skills.txt:srvmissilea | ? | ? | ? | 1 |
| 100 | 1347 | R. In the game: the Phase 2 sample | … pass the callback (mhit 38 , mhit 45 ) made these creations is not logged. | `0x005AC14B` | ? | ? | ? | 1 |
| 101 | 1352 | R. In the game: the Phase 2 sample | … which draw is not read. The handler where the unit survives stays a no-draw check. | – | ? | ? | ? | 1 |
| 102 | 1355 | R. In the game: the Phase 2 sample | … not check them, so the no-draw for handler 4 does not extend to a kill. | – | ? | ? | ? | 1 |
| 103 | 1360 | R. In the game: the Phase 2 sample | … hit that § P's P2 leaves to the reading); the other logged monster rows none. | – | ? | ? | ? | 1 |
| 104 | 1375 | Worked example | spec, not a recorded case. | `0x005D2C20` | ? | ? | ? | 1 |
| 105 | 1395 | Reimplementation notes | for do 55, 58, 81 | `0x005C4DF0` | ? | ? | ? | 1 |
| 106 | 1400 | Reimplementation notes | ); | `0x005AC940` | ? | ? | ? | 1 |
| 107 | 1408 | Reimplementation notes | ); | `fn:sub_005DBC60_SkillDo13Fend@0x005DBC60` | ? | ? | ? | 1 |
| 108 | 1413 | Reimplementation notes | … and 143 do not test their step count; a count of 0 loops for ever. | – | ? | ? | ? | 1 |
