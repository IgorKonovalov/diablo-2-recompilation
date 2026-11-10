# Plan 0066 inventory: skills/missiles

- **Spec:** [skills/missiles](../../specs/skills/missiles.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 99; the *Count* column sums to 99.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 43 | Entry points | A skill creates its srvmissile or a line or … | `fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0` | a-logs | the 31 391 `MC` lines of run:2026-10-25-skills by creator (line, lob): flags, start and target against B2, B3 | S2b | 1 |
| 2 | 44 | Entry points | A missile is created at a point (quests, shrines, … | `fn:sub_0056EDE0_MissileCreateAt@0x0056EDE0` | a-logs | the Meteor `MC` lines (creation at the target point) of run:2026-10-25-skills sor sessions | S2b | 1 |
| 3 | 46 | Entry points | Do function 1, the common step | `fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0` | a-logs | the `MF0`/`MF1` frames of the 493 followed missiles (do 1) in run:2026-10-25-skills | S2b | 1 |
| 4 | 47 | Entry points | A missile reaches a unit, or ends its life — for a missed to-hit ( 105), and for the … | `fn:MISSILE_HitUnit@0x005ADF10` | a-logs | the `MH` lines of hit-function rows in run:2026-10-30-skills-catalogue against the catalogue's hit emulation models | S2b | 1 |
| 5 | 84 | Inputs and oracles | the grid a plan reads, and the cells a … — a value oracle, counted: path/overview §§ F2, F3. Types … | `fn:sub_00648F40_PathStepCells@0x00648F40` | c | the type switch of `sub_00648F40_PathStepCells` read with r2: types 4, 10, 14 read no cell (the grid is path's claim) | S2c | 1 |
| 6 | 85 | Inputs and oracles | the numbered do, hit and damage functions outside § … — value oracles of the checker; specified in the catalogue … | `data:g_MissileSrvDoFuncs@0x0073C768` | d-none | a boundary declaration: the functions are the catalogue's | – | 1 |
| 7 | 86 | Inputs and oracles | the result of a hit that does not miss — logged as the hit's return in | `fn:MISSILE_HitUnit@0x005ADF10` | d-none | a boundary declaration: the hit's result is a logged input | – | 1 |
| 8 | 87 | Inputs and oracles | the room collision word — drlg/collision | `fn:sub_00648EB0_PathCellCollision@0x00648EB0` | d-none | a boundary pointer: the collision word is drlg/collision's | – | 1 |
| 9 | 93 | Constants | do table — g_MissileSrvDoFuncs, bound 53 | `data:g_MissileSrvDoFuncs@0x0073C768` | c | the do table's bound `g_MissileSrvDoFuncCount` and its compare read with r2 | S2c | 1 |
| 10 | 94 | Constants | hit table — g_MissileSrvHitFuncs, bound 71 | `data:g_MissileSrvHitFuncs@0x0073C840` | c | as row 9, the hit table | S2c | 1 |
| 11 | 95 | Constants | damage table — g_MissileSrvDmgFuncs, bound 31 | `data:g_MissileSrvDmgFuncs@0x0073C960` | c | as row 9, the damage table | S2c | 1 |
| 12 | 96 | Constants | collide types — g_MissileCollideTypes, 9 × {filter, mask} | `data:g_MissileCollideTypes@0x0073C720` | c | `g_MissileCollideTypes` read with r2 and its reader in `MissileMoveCollide` | S2c | 1 |
| 13 | 97 | Constants | direction table — g_PathDirTable, 128 × 12 bytes (image data a reimplementation … | `data:g_PathDirTable@0x006EB7E0` | c | `g_PathDirTable` read with r2 and its reader `PathDirection` (second tool) | S2c | 1 |
| 14 | 99 | Constants | distance refusal — a target 100 or more sub-tiles from the start … | `0x0059FC2E` | c-emu | `MissileCreate` with a target 100 or more sub-tiles away (the refusal) and its map to the alloc boundary | S2ae | 1 |
| 15 | 154 | B. Creation | The block's layout and its flags are as above. | `fn:sub_0059FA30_MissileCreate@0x0059FA30` | c | the block's writers (the creators) against its reader `MissileCreate` (writer/reader pair, rule 1) | S2c | 1 |
| 16 | 157 | B. Creation | B1. MissileCreate(game, p) → missile: | `fn:sub_0059FA30_MissileCreate@0x0059FA30` | c-emu | `MissileCreate` to its boundaries with the slow-missiles state, `SubLoop` rows and the refusal | S2ae | 1 |
| 17 | 202 | B. Creation | reading. | run:2026-10-25-skills | c-emu | as row 16 | S2ae | 1 |
| 18 | 208 | B. Creation | were all at level 1, where (7 · 1) ÷ 8 is 0 either way. | `0x0059FB18` | c-emu | `MissileCreate` with `VelLev` rows at levels above 1 (the term separates at level 8) | S2ae | 1 |
| 19 | 211 | B. Creation | … ÷ 100; the lob division is unsigned; MaxVel << 8 is a byte times 256. | `0x0059FB18` | c-emu | as row 18 with negative inputs: signed and unsigned divisions | S2ae | 1 |
| 20 | 214 | B. Creation | collision starts when left ≤ R − Activate. | `fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0` | a-logs | the 493 followed missiles of run:2026-10-25-skills: frames run against the range, first `MH` frame against `Activate` | S2b | 1 |
| 21 | 216 | B. Creation | constant and creates two side missiles beside this one. | – | c-emu | unique mod 29's function (`sub_005A43B0_MissileOwnerUModEvent`) from the constant seed to its creation boundaries | S2ae | 1 |
| 22 | 220 | B. Creation | B2. SkillMissileCreate(game, cls, unit, skill, lvl, dx, dy, tx, ty, useAmmo): (line) | `fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0` | a-logs | the `MC` flags, start and target of the line, lob and at-point creations in the kept skills logs | S2b | 1 |
| 23 | 237 | B. Creation | else, SKILLS_SrvDo included. The use acts only for a player owner. | `fn:SKILL_AttackDo@0x0056F070` | c | the 33 call sites' `useAmmo` argument read with r2 (exhaustive) | S2c | 1 |
| 24 | 243 | B. Creation | unfollowed. | `fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0` | a-logs | the `MH0` missile stats of run:2026-10-25-skills: no stat 19 on player-owned missiles, present on monster-owned | S2b | 1 |
| 25 | 248 | B. Creation | ITEMSKILL_Cast → SKILLS_SrvDo. | `data:g_ShrineEffects@0x006E1850` | c | an exhaustive xref scan of the missile creators with r2 (97 sites in 82 functions) | S2c | 1 |
| 26 | 256 | C. The damage the missile carries | C1. MissileDamageBlock(blk, owner, source, m, lvl): | `fn:sub_0064B860_MissileDamageBlock@0x0064B860` | c-emu | `sub_0064B860_MissileDamageBlock` with a synthetic owner and Missiles rows (a new block model) | S2ae | 1 |
| 27 | 298 | C. The damage the missile carries | = 1 for a critical; then the owner's stat-180 entries. | `fn:sub_0064AC60_MissileDamageToStats@0x0064AC60` | c-emu | `sub_0064AC60_MissileDamageToStats`: the stat order, 315 overwritten | S2ae | 1 |
| 28 | 305 | C. The damage the missile carries | creation drew twice: the second and third steps are the reading. | `0x0064A864` | c-emu | `sub_0064A850_MissileCritRoll` with stat 141 and a mastery chance non-zero (second and third steps) | S2ae | 1 |
| 29 | 307 | C. The damage the missile carries |  | `fn:sub_0064B860_MissileDamageBlock@0x0064B860` | c-emu | `MissileDamageBlock` with a `SrcMissDmg` row and a source missile | S2ae | 1 |
| 30 | 317 | C. The damage the missile carries | skill requests the owner has made, not on any game seed. | `0x00549D50` | a-logs | as dispatch row 25: stat 328 against the request count, run:2026-10-27-skills | S2b | 1 |
| 31 | 323 | D. Each frame | before any player or monster acts. | `fn:sub_005414D0_GameRunUnitEvents@0x005414D0` | a-logs | run:2026-11-03-frame-order's check over the corpus: the unit lists' order per frame | S2b | 1 |
| 32 | 325 | D. Each frame | The insertion into the every-frame list is not read. | `fn:sub_0059F8A0_MissileUnitInit@0x0059F8A0` | d-none | a scope note: the list insertion is not read | – | 1 |
| 33 | 328 | D. Each frame | D2. MissileDoFrame(game, m): | `fn:sub_005ADBB0_MissileDoFrame@0x005ADBB0` | a-logs | the `MF0`/`MF1` frames of run:2026-10-25-skills: the do call per frame and the free | S2b | 1 |
| 34 | 336 | D. Each frame | D3. MissileMoveCollide(game, m) → 1 keep, 2 free: (do function 1, 551 stock rows) | `fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0` | a-logs | the followed missiles' frames: collisions and ends at walls against D3 | S2b | 1 |
| 35 | 360 | D. Each frame | if v < 0: v ← 0 ; | run:2026-10-25-skills | c-emu | `sub_006502D0_PathVelocityStep` with a negative acceleration (pure) | S2ae | 1 |
| 36 | 366 | D. Each frame | … Entries 4 and 38..52 of the do table are null, used by no stock row. | – | b | a pilot step casting then taking a waypoint to town while the missile flies; `MF` lines (null entries: Missiles over every row) | H2a | 1 |
| 37 | 370 | D. Each frame | CollisionTest(room, x, y, size, ) at its point. | `fn:sub_00648EB0_PathCellCollision@0x00648EB0` | a-logs | followed missiles ending at their own cell with no hit call in the kept `MF`/`MH` lines | S2b | 1 |
| 38 | 379 | D. Each frame | table's third word folded by the same octant rules. | `fn:sub_0064FC60_PathDirection@0x0064FC60` | c-emu | `sub_0064FC60_PathDirection` over all octants and deltas (pure, table-reading) | S2ae | 1 |
| 39 | 390 | D. Each frame | 0 — none | `data:g_MissileCollideTypes@0x0073C720` | c | `g_MissileCollideTypes` entry 0 read with r2; `CollideType` counted over every Missiles row | S2c | 1 |
| 40 | 391 | D. Each frame | 1 — a player, or a monster for which returns 2 | `fn:sub_005A87F0_CollidePlayerOrAlly@0x005A87F0` | c-emu | `sub_005A87F0_CollidePlayerOrAlly` with synthetic units | S2ae | 1 |
| 41 | 392 | D. Each frame | 2, 5 — a monster | `fn:sub_005A87B0_CollideMonster@0x005A87B0` | c-emu | `sub_005A87B0_CollideMonster` with synthetic units | S2ae | 1 |
| 42 | 393 | D. Each frame | 3 — a player or a monster | `fn:sub_005A8850_CollideUnit@0x005A8850` | c-emu | `sub_005A8850_CollideUnit` with synthetic units | S2ae | 1 |
| 43 | 394 | D. Each frame | 4 — none | `data:g_MissileCollideTypes@0x0073C720` | c | as row 39, entry 4 | S2c | 1 |
| 44 | 395 | D. Each frame | 6 — no filter: walls only | `data:g_MissileCollideTypes@0x0073C720` | c | as row 39, entry 6 | S2c | 1 |
| 45 | 396 | D. Each frame | 7 — a CanDestroy missile | `fn:sub_005A8890_CollideMissile@0x005A8890` | c-emu | `sub_005A8890_CollideMissile` with a `CanDestroy` missile | S2ae | 1 |
| 46 | 397 | D. Each frame | 8 — a player or a monster | `fn:sub_005A8850_CollideUnit@0x005A8850` | c-emu | as row 42, mask `0x0185` | S2ae | 1 |
| 47 | 400 | D. Each frame | NextHit row, the last unit hit, and an owner-friendly unit unless CollideFriend. | – | c-emu | `sub_005A8730_CollideUnitFilter` with synthetic units (flags, state 86, last hit, friend) | S2ae | 1 |
| 48 | 405 | D. Each frame | the placement readers are drlg/collision § F's. | – | c | an exhaustive scan of the `0x40` cell writers and readers with r2 | S2c | 1 |
| 49 | 411 | D. Each frame | creation is the reading. | `fn:sub_005B0BC0_MissDo01Thunk@0x005B0BC0` | c-emu | extend run:2026-10-20-cat-emu-9a past do 2's creation into do 1 (path calls as boundaries) | S2ae | 1 |
| 50 | 416 | E. The hit | E1. MISSILE_HitUnit(game, m, unit, end) → 1 keep, 2 free: | `fn:MISSILE_HitUnit@0x005ADF10` | a-logs | the `MH0`/`MH1` lines of the kept skills logs: the returns before the build (filters) and the order of the steps | S2b | 1 |
| 51 | 449 | E. The hit |  | `0x005ADA0D` | c | Missiles.txt over every row: only row 568 above 0x7FFF; the s16 compare read with r2 | S2c | 1 |
| 52 | 454 | E. The hit | life (end 1) the hit function runs with no unit and no damage is built. | `fn:sub_005ADA80_MissilePierceUse@0x005ADA80` | a-logs | the `MH` lines: pierce taken before `THR`, the `end` 1 calls | S2b | 1 |
| 53 | 466 | E. The hit |  | run:2026-10-27-skills | a-logs | the 64 hit-function hits, the 1 203 early returns and the `end` calls of the kept `MH` lines, with the catalogue's hit models | S2b | 1 |
| 54 | 471 | E. The hit | stat 19 as arPct. | `fn:COMBAT_ToHitRoll@0x0057D9B0` | a-logs | the 269 `THR` rolls of run:2026-10-25-skills: the chance against combat/to-hit with the missile's stat 19 | S2b | 1 |
| 55 | 473 | E. The hit | to-hit A2. | `fn:MISSILE_HitUnit@0x005ADF10` | a-logs | monster-owned missile `THR` lines of run:2026-10-30-skills-catalogue: stat 19 counted twice | S2b | 1 |
| 56 | 475 | E. The hit | (unit event 12), so any NextHit missile skips that unit until then. | – | a-logs | `STA` state 86 inside `MH` spans for `NextHit` rows in the kept skills logs | S2b | 1 |
| 57 | 480 | E. The hit | monster's defence (stat 31) += it, floored at 0. | `fn:sub_005ADCD0_MissileApplyAndAc@0x005ADCD0` | a-logs | the `MA0`/`MA1` lines of the kept skills logs: knockback step on the missile's seed, defence on the defender's | S2b | 1 |
| 58 | 483 | E. The hit | in the image: unreached. | `fn:sub_005AD9D0_MissileEndHit@0x005AD9D0` | c | an exhaustive xref and pointer scan with r2 for `sub_005AD9D0_MissileEndHit` | S2c | 1 |
| 59 | 492 | F. The packet at the hit (MISSILE_BuildDamage) | (316, 317, 329, + burn)]: ; this order: | `0x005A89A0` | a-logs | the 13 881 `BD` builds of run:2026-10-30-skills-catalogue: the pair order in builds with two or more draws | S2b | 1 |
| 60 | 495 | F. The packet at the hit (MISSILE_BuildDamage) | if a > b: swap(a, b) ; | `0x005A894B` | c-emu | `sub_005A8910_MissileElemRoll` with an inverted pair (pure) | S2ae | 1 |
| 61 | 496 | F. The packet at the hit (MISSILE_BuildDamage) | k: i32 ← mastery ? stat(m, mastery) : 0 ; | `0x005A895F` | c-emu | as row 60 with a mastery stat on the missile | S2ae | 1 |
| 62 | 497 | F. The packet at the hit (MISSILE_BuildDamage) | if k ≠ 0: a += MulDiv(a, k, 100); b += MulDiv(b, k, 100) ; | `0x005A8953` | c-emu | as row 61 | S2ae | 1 |
| 63 | 501 | F. The packet at the hit (MISSILE_BuildDamage) | … 25 + stat 121 (demon) + stat 122 (undead) + matching stat-180 entries, −90) ; | `fn:MISSILE_BuildDamage@0x005A89A0` | c-emu | `MISSILE_BuildDamage` with stat-180 entries | S2ae | 1 |
| 64 | 512 | F. The packet at the hit (MISSILE_BuildDamage) | … is separated only by the 19 two-draw builds, and the stat-180 entries were not checked. | – | a-logs | as row 59 | S2b | 1 |
| 65 | 515 | F. The packet at the hit (MISSILE_BuildDamage) | … a mastery stat (329–332, 357), so every logged mastery term is 0 and adds nothing. | – | c-emu | as row 61 | S2ae | 1 |
| 66 | 522 | F. The packet at the hit (MISSILE_BuildDamage) | either run had an inverted pair, so the swap rests on the code alone. | `fn:sub_005A8910_MissileElemRoll@0x005A8910` | c-emu | as row 60 | S2ae | 1 |
| 67 | 524 | F. The packet at the hit (MISSILE_BuildDamage) | F1. Combat's missile oracle is this build: combat/overview § B3. | – | d-none | a cross-reference note: names which spec holds combat's missile packet | – | 1 |
| 68 | 531 | G. The function tables | hit 49, damage 13. | `data:g_MissileSrvDoFuncs@0x0073C768` | c | Missiles.txt over every row: the used do, hit, damage numbers (34, 49, 13) | S2c | 1 |
| 69 | 536 | G. The function tables | … 14 runs one: skill do 30 applies the creator's auratargetstate around the missile's path target. | – | c-emu | `sub_0056D810_CallDoFunc` bound and null test, with do 14 (run:2026-10-20-cat-emu-9a) as the caller | S2ae | 1 |
| 70 | 545 | G. The function tables | firebolt (58), nova (90), frostnova (119), multipleshotarrow, firestorm (457), … — D3; ExplosionMissile has no server reader | `fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0` | c | an exhaustive xref scan of the `ExplosionMissile` column offset with r2 | S2c | 1 |
| 71 | 548 | G. The function tables | plaguejavcloud (221) — 3 | `fn:sub_005AE480_MissDo03CloudMark@0x005AE480` | c-emu | do 3 (`sub_005AE480_MissDo03CloudMark`) to its boundaries | S2ae | 1 |
| 72 | 552 | G. The function tables | meteorfire (240) — for damage 3 ; do 5 | `fn:sub_005AE520_MissDo05Loop@0x005AE520` | c-emu | do 5 (`sub_005AE520_MissDo05Loop`) with its `RangeB` loops on the missile seed | S2ae | 1 |
| 73 | 554 | G. The function tables | grim wards (250, 253, 256) — G2; hit 27 returns 1 | `fn:sub_005AEF70_MissDo14PeriodicDo@0x005AEF70` | c-emu | hit 27 to its return | S2ae | 1 |
| 74 | 557 | G. The function tables | with no block, then the damage. | `fn:sub_0056B9C0_AreaHitUnit@0x0056B9C0` | c-emu | `sub_0056B9C0_AreaHitUnit` and hit 14 to their boundaries | S2ae | 1 |
| 75 | 567 | H. Re-seed sites | callback (ring 37) — the ring's local low word | `fn:sub_005D40F0_MissCbReseedFromArg@0x005D40F0` | c-emu | `sub_005D40F0_MissCbReseedFromArg` to its return | S2ae | 1 |
| 76 | 568 | H. Re-seed sites | callback (ring 143) — inline steps for a zig-zag path | `fn:sub_005D4680_MissCbReseedZigzag@0x005D4680` | c-emu | `sub_005D4680_MissCbReseedZigzag` to its return | S2ae | 1 |
| 77 | 570 | H. Re-seed sites | callback — path + + the argument | `fn:sub_005CD110_MissCbReseedRoll@0x005CD110` | c-emu | `sub_005CD110_MissCbReseedRoll` to its return | S2ae | 1 |
| 78 | 572 | H. Re-seed sites | (do 8, 10, 17, 25) — SubX + elapsed | `0x005A9820` | c-emu | `0x005A9820` to its return | S2ae | 1 |
| 79 | 574 | H. Re-seed sites | do 28 () — 2 Range, then + ← low | `0x005AFB80` | c-emu | do 28 (`0x005AFB80`) to its return | S2ae | 1 |
| 80 | 575 | H. Re-seed sites | do 34 () — the missile | `0x005B04A0` | c-emu | do 34 (`0x005B04A0`) to its return | S2ae | 1 |
| 81 | 576 | H. Re-seed sites | do 35 () — 1 inline, + ← low | `0x005B0640` | c-emu | do 35 (`0x005B0640`) to its return | S2ae | 1 |
| 82 | 606 | H. Re-seed sites | the same walk when they set type 10, and are not rerun. | `fn:sub_0059FA30_MissileCreate@0x0059FA30` | c-emu | the other re-seed callbacks with the `PathPlan` walk (as run:2026-11-03-path-emu-3 did `0x005AC040`) | S2ae | 1 |
| 83 | 608 | H. Re-seed sites | … seeds, short of the floor of 50, with one more each in the earlier run. | `0x00681F4F` | a-run | the path logger of run:2026-11-04-path watching more class 225 and 195 seeds (Firestorm, `lightunique`) to the floor of 50 | H2b | 1 |
| 84 | 610 | H. Re-seed sites | before the damage block (B1). | `fn:sub_0059FA30_MissileCreate@0x0059FA30` | a-logs | the `MCB0`/`MCB1` lines inside `MC` spans before the crit draw (`MCM`) in run:2026-10-25-skills | S2b | 1 |
| 85 | 614 | H. Re-seed sites | The call at was among | run:2026-10-25-skills | c-emu | `0x005ACDF0`, `0x005D40F0`, `0x005D5BF0` to their returns (`0x00645390` has no reference: an r2 scan) | S2ae | 1 |
| 86 | 625 | H. Re-seed sites | Which of the two hit entries passing the callback made these creations is not read. | – | a-logs | the enclosing `MH0` line (row, hit function) of the 36 class-408 creations in cat-a5-1, cat-a5-2 | S2b | 1 |
| 87 | 639 | I. Draws and seeds per event kind | hit — missile, area units | `data:g_MissileSrvHitFuncs@0x0073C840` | d-none | a pointer: the hit and damage functions are the catalogue's, inventoried there | – | 1 |
| 88 | 640 | I. Draws and seeds per event kind | hit — knockback 1; defence, delivery | `fn:MISSILE_ApplyDamage@0x005AD730` | a-logs | the `MA0`/`MA1` spans: knockback step on the missile's seed, the defender's roll | S2b | 1 |
| 89 | 641 | I. Draws and seeds per event kind | end — the hit function's | `fn:MISSILE_HitUnit@0x005ADF10` | a-logs | the `end` 1 `MH` calls of the kept skills logs | S2b | 1 |
| 90 | 646 | I. Draws and seeds per event kind | measures. | `fn:sub_0064A850_MissileCritRoll@0x0064A850` | a-logs | the caster chain between `MC` and `THR` (as dispatch § P) over run:2026-10-27-skills | S2b | 1 |
| 91 | 651 | Outputs | the cell marks for drlg/collision; sub-missiles. | – | a-logs | the kept skills logs: missile stats at `MH0`, `BD` packets, sub-missile `MC` lines | S2b | 1 |
| 92 | 663 | Worked example | the reading. | `fn:sub_005C7160_SkillDo117Firestorm@0x005C7160` | a-logs | the `MCB0` argument order 0, 1, … across each Firestorm cast's 442 sub-missiles in run:2026-10-25-skills | S2b | 1 |
| 93 | 667 | Reimplementation notes | … the function numbers as s16, > 0 first: row 568's hit function must not run. | `0x005ADA0D` | c | as row 51 | S2c | 1 |
| 94 | 669 | Reimplementation notes |  | `fn:sub_0064B860_MissileDamageBlock@0x0064B860` | c | `MISSILE_BuildDamage`'s stat reads all on the missile (r2 scan of its `GetUnitStat` calls): no owner weapon read at the hit | S2c | 1 |
| 95 | 672 | Reimplementation notes | The fire length is overwritten by the burn length in stat 315 (C1). | `0x0064AE2F` | c-emu | as row 27 | S2ae | 1 |
| 96 | 674 | Reimplementation notes | first frame ; | `fn:sub_005414D0_GameRunUnitEvents@0x005414D0` | a-logs | as row 31 | S2b | 1 |
| 97 | 679 | Reimplementation notes | A freed missile at a bit-0 or bit-2 own cell does not explode. | `fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0` | a-logs | as row 37 | S2b | 1 |
| 98 | 680 | Reimplementation notes | Keep g_PathDirTable as data. The step direction is a table lookup, not a trigonometric function. | – | c-emu | as row 38 | S2ae | 1 |
| 99 | 707 | Open questions | … bit 0 and not bit 2; neither is shown by a run, and D3 stays | src:pk-walkable-flags-overview` | d-none | a quoted tag inside an open question; the D3 claim is row 34's | – | 1 |

**Totals by class:** a-logs 30, a-run 1, b 1, c 19, c-emu 41, d-none 7 (sum 99).
