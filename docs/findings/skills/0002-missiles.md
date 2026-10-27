# 0002 — Missiles: creation, the per-frame step, collision, the hit and the function tables

> **Subsystem:** skills/missiles
> **Question:** how does the server create a missile (for a skill, an item cast, a monster, a shrine or a quest), which
> seed and damage does it carry, how does it move and collide each frame, what happens when it hits, and how does it
> end?
> **Date:** 2026-10-20   **Plan:** 0045 (Phase 1, batch P1.2)   **Status:** open (P1.3 handlers, summons, re-seeds and
> tier A follow; the numbered do, hit and damage functions are plan 0046)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-p45m`, which carries P1.1's analysis)
and objdump. Counts, table contents and the instruction windows cited below come from `tools/skills_missiles_scan.py`
(sha256 `15666a49…`), kept under `workspace/logs/skills/` with `p45m-manifest.sha256` (`missiles-scan.txt` `d196acf9…`,
`missiles-rows.txt` `5c5dc112…`, `missiles-ghidra-xrefs.txt` `74401088…`, the Ghidra xrefs of the twelve first
targets). Missiles columns are named as in [Missiles](../../tables/Missiles.md), Skills columns as in
[Skills](../../tables/Skills.md); offsets are record offsets. P1.1's [skills/0001](0001-dispatch.md) is the dispatch
this batch continues from.

## Answer (summary)

- [I] **Creation.** Every server missile is made by `sub_0059FA30_MissileCreate(game, params)` from a 0x5C-byte
  parameter block (flags, owner, source unit, target unit, missile class, start and target points, velocity, skill,
  level, loops, range and activate overrides, to-hit, a callback). 97 call sites in 82 functions: the three skill
  creators `SkillMissileCreate` (line), `SkillMissileCreateLob` and `MissileCreateAt` (at a point), two more skills
  helpers, four shrine and quest functions, three monster functions, 30 missile functions (sub-missiles) and 40 skill
  functions. The owner must be a player or a monster. (fn:sub_0059FA30_MissileCreate@0x0059FA30, `missiles-scan.txt`
  `CALLS`, `missiles-ghidra-xrefs.txt`)
- [I] **What creation sets.** The start room and cell; velocity `((VelLev · lvl) / 8 + Vel) << 8`, scaled by the slow
  missiles state 87 for `CanSlow` rows and then by 75/100; `MaxVel << 8` and `Accel` into the path; range
  `LevRange · lvl + Range` (plus loops of the `SubLoop` range on request); unit collision from the `Activate`-th frame;
  the `0x40` mark when `Collision` is set; the collide mask of `CollideType`; the owner as the first "last hit unit"
  for `LastCollide` rows; and the damage as the missile's own stats. A target point more than 99 sub-tiles from the
  start in x or y gives no missile. (0x0059FA79–0x0059FC48, 0x0059FC84–0x0059FEC3)
- [I] **The missile's seed and draws at creation.** The missile unit is made by `SUnitCreate` (type 3), which seeds it
  from the game seed as for every non-player unit (rng/0002's `[C]` reading of `SUnitCreate`). The damage block then
  draws on the **owner's** seed (`+0x20`) when the missile takes weapon damage (`SrcDamage`): one inline step tests
  stat 337 (critical strike) even when it is 0, then one for stat 141 (deadly strike) when it is non-zero, then one for
  the weapon mastery's critical chance when it is non-zero, stopping at the first success, which doubles the physical
  damage at the hit (stat 141 on the missile). The pierce count uses a **local** seed made from the owner's base stat 328
  (`pierce_idx`, P1.1's per-request counter): no game or unit seed is drawn. (fn:sub_0064A850_MissileCritRoll@0x0064A850,
  fn:sub_0059F940_MissilePierceCount@0x0059F940, fn:sub_00555230_SUnitCreate@0x00555230)
- [I] **Each frame** the missile's every-frame event (queued at creation, frame −1, on the missile list that
  `sub_005414D0_GameRunUnitEvents` runs first) calls `sub_005ADBB0_MissileDoFrame`: town tests (`SrcTown`, a player
  owner in town, `Town`), then the `pSrvDoFunc` entry of `g_MissileSrvDoFuncs` (`0x0073C768`, 53 slots, bound dword
  `0x0073C71C`; the table's name and its entry 13, `sub_005AEDA0_MissileSpawnOwnedMonster`, are items/0002's on `main`);
  a return of 2 frees the missile. Do function 1 (551 stock rows) is `sub_005AE1F0_MissileMoveCollide`:
  one path step, the range countdown, then the collision test of the cells the step crossed against the `CollideType`
  mask and unit filter. (fn:sub_005ADBB0_MissileDoFrame@0x005ADBB0, data:g_MissileSrvDoFuncs@0x0073C768,
  fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0)
- [I] **Motion** is the path's: speed `v` in 1/256 units, every fifth step `v += Accel`, capped at `MaxVel << 8` (the
  acceleration then stops) and floored at 0; the step moves `(dir · ((v · 0x400) >> 6)) >> 12` in 16.16 fixed point.
  (fn:sub_006502D0_PathVelocityStep@0x006502D0)
- [I] **The hit** (`MISSILE_HitUnit(missile, unit, end)`): the `NextHit`/`justhit` (state 86), last-hit and
  `CollideType` unit filters, the hostility test (`CollideFriend`), the pierce use, the `ToHit` roll on the owner's
  seed, event 0 (`hitbymissile`) on the unit, the `pSrvHitFunc` entry (its return replaces the result flags), then for a
  damaging result `MISSILE_BuildDamage` (up to seven `RNG_RangeB` draws on the **missile's** seed), the `pSrvDmgFunc`
  entry and `MISSILE_ApplyDamage`; a result with "end" and no pierce left unmarks the `0x40` mark and frees the missile.
  At the end of life (range out, blocked path, a wall cell) the hit function runs with no unit. (fn:MISSILE_HitUnit@0x005ADF10)
- [I] **Row 568's hit function 64 948 is never called.** All four reads of `g_MissileSrvHitFuncs` (`0x0073C840`,
  bound 71; one of them in `sub_005AD9D0_MissileEndHit`) read `pSrvHitFunc` as a word and test it signed (`test ax,ax;
  jle`) before the bound: 64 948 is −588 as s16 and skips the call, so `royalstrikechainlightning` behaves as a row with
  no hit function. The damage table's one read (`0x0073C960`, bound 31) and the do table's (§ 4) are tested the same
  way. (hit: 0x005ADA0D–0x005ADA1F, 0x005AE09B–0x005AE0AD, 0x005AE106–0x005AE118, 0x005B02CF–0x005B02E1; damage:
  0x005AE158–0x005AE16A; do: 0x005ADBEE–0x005ADBFE; `missiles-scan.txt` `TABREAD`; *corrected at review 2026-10-20:*
  the five sites first listed counted the damage read as a hit read)
- [C] **As data** (table bytes read from the image against `missiles.bin`, all 684 rows): every non-zero
  `pSrvDoFunc`, `pSrvHitFunc` and `pSrvDmgFunc` that is positive as s16 is below its table's bound and names a non-null
  entry (0 out of table); one cell (row 568 `pSrvHitFunc`) is ≤ 0 as s16. Non-null entries: do 36 (ids 1..37, 4 null;
  23 and 24 the same function), hit 53 (ids 1..59), damage 14 (ids 1..14). Which column indexes which table is the code
  reading above, `[I]`. (`missiles-rows.txt`, `missiles-scan.txt` `SCAN tables`, data:g_MissileSrvHitFuncs@0x0073C840,
  data:g_MissileSrvDmgFuncs@0x0073C960, tbl:Missiles.txt:pSrvHitFunc)
- [I] **Skills.** `SKILLS_SrvDo` creates the `srvmissile` with `useAmmo` 0 (§ 2); a skill with no `srvdofunc` gets its
  missile only there, because entry 0 of `g_SkillDoFuncs` is null: 48 stock rows, among them the tier-A rows 36 Fire
  Bolt, 251 Fire Trauma (lob) and 25 Plague Javelin (whose `decquant` takes the javelin). The `ItemEffect` aim offset
  of an item cast moves the start of a line missile to the target point and its target as far again; a lob keeps the
  caster as its start. (fn:SKILLS_SrvDo@0x0056F7F0, 0x0056F9D0–0x0056FA29, `missiles-rows.txt`)
- [I] **The two `CallDoFunc` missile callers** run a **skill** do function with the missile as the unit: hit function
  23 calls `g_SkillDoFuncs[sHitPar1]` (no stock row uses hit function 23, so it never runs on stock data; first written
  "22", see the correction below), and do function 14 (the three grim wards) calls `g_SkillDoFuncs[Param2]` (30) every `Param1` (6) frames.
  (fn:sub_005ACFC0_MissHit23CallDo@0x005ACFC0, fn:sub_005AEF70_MissDo14PeriodicDo@0x005AEF70)
  *Corrected 2026-10-20 (P1.3, [skills/0003](0003-handlers.md)):* `0x005ACFC0` is entry **23** of
  `g_MissileSrvHitFuncs` (`0x0073C89C`), a number no stock row uses; row 233's hit function 22 is `0x005ADD20`
  (`0x0073C898`), a chained area hit that calls no skill do function. So on stock data only do function 14 runs a skill
  do function with a missile as the unit. The symbol is renamed `sub_005ACFC0_MissHit23CallDo`.
  (data:g_MissileSrvHitFuncs@0x0073C840, fn:sub_005ADD20_MissHit22Chain@0x005ADD20)
- [I] **The `0x40` mark's readers.** The only stock missile reader would be `CollideType` 7 (mask `0x40`, filter: a
  `CanDestroy` missile), which no stock row uses; do function 3 (26 rows: the clouds, blizzards, `plaguejavelin`) also
  **writes** `0x40` on its cell each frame while its path is not moving. The placement masks (`0x01C0`) stay drlg/collision's.
  (data:g_MissileCollideTypes@0x0073C720, fn:sub_005AE480_MissDo03CloudMark@0x005AE480, `missiles-scan.txt` `COLLMASK`)

## Leads used

No community document was opened for P1.1–P1.3. *Phase 1b (plan 0045), 2026-10-20:* the pages below were fetched and
read in that session (ADR-0007), after the batch's sections were written, and none shows code. One verdict per compared
claim. The verdict words are evidence-rules' (`held`, `held with refinement`, `contradicted`, `not covered`). A
claim from another game version that differs from 1.14d for that reason only would be marked *version-different* in
its detail. None is marked: no source says its claim is version-specific, and none of their versions can be checked
here. Two sources are Resurrected-era (src:d2dfg-blizzard, src:purediablo-piercing), so a contradiction from them
may be a Resurrected change; the Phase 2 case settles 1.14d only. Agreement adds nothing to a tag. The quick objdump re-reads behind a contradiction or a gap are `tools/skills_crosscheck_reread.py`
(sha256 `8361a4c1…`), kept under `workspace/logs/skills/` (`p45b-manifest.sha256`: `p45b-reread.txt` `427ca8d7…`, the
code windows R1–R7; `p45b-rows.txt` `cbf9c64a…`, the stock-row values compared).

- [L] src:d2dfg-blizzard: velocity is `Vel` plus `VelLev` per caster level beyond 1. **contradicted**
  Detail: `((VelLev · lvl) / 8 + Vel) << 8`, `lvl` the request's level (R1: `imul [esi+0x30]`, `cdq; and edx,7;
  sar 3`); four stock rows (`spike1`–`spike4`). Phase 2 case C2,
  [backlog](../../backlog/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md). *2026-10-25:* not reached by run:2026-10-25-skills (no `VelLev` row created; § 11). *2026-10-27:* 22 `spike2` creations at level 1 only, not separating (§ 12).
- [L] src:d2dfg-blizzard: `MaxVel` caps the velocity. **held**
- [L] src:d2dfg-blizzard: `Accel` changes the velocity per frame. **contradicted**
  Detail: `Accel` is added on every **fifth** path step (R3: the counter `+0x8C` reaches 5), the result capped at
  `MaxVel << 8` (acceleration then stops) and floored at 0 (§ 4); 21 stock rows, Nova, Frost Nova and Howl in tier A.
  Phase 2 case C3, [backlog](../../backlog/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md). *2026-10-25:* run:2026-10-25-skills: 278 fifth steps and 60 caps over 1 657
  accelerating steps, every step's velocity as read (§ 11).
- [L] src:d2dfg-blizzard: `Range` is the lifetime in frames. **held**
- [L] src:d2dfg-blizzard: `LevRange` adds to `Range` per caster level beyond 1. **contradicted**
  Detail: `LevRange · lvl + Range`, `lvl` the request's level, with no `− 1` (R2: `movsx [edx+0x98]; imul [esi+0x30]`);
  32 stock rows, none in tier A. Phase 2 case C4,
  [backlog](../../backlog/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md). *2026-10-25:* not reached by run:2026-10-25-skills (Blaze cast 29 times, no `LevRange` row created; § 11). *2026-10-27:* met by run:2026-10-27-skills, 271 `blaze` creations at level 2 (§ 12).
- [L] src:d2dfg-blizzard: `Activate` is the frame count before the missile collides. **held**
- [L] src:d2dfg-blizzard: `CollideType` codes 0–8, 7 being missile collision. **held with refinement**
  Detail: 7's mask is `0x40` with a `CanDestroy` filter, and no stock row uses it (§ 2).
- [L] src:d2dfg-blizzard: a `CollideKill` missile is destroyed when it collides. **held with refinement**
  Detail: unless a pierce succeeds or the hit function's return replaces the result (§ 5).
- [L] src:d2dfg-blizzard: `CollideFriend` lets the missile hit friendly units. **held**
- [L] src:d2dfg-blizzard: `LastCollide` keeps the missile from hitting its last unit twice. **held with refinement**
  Detail: the owner is the first last-hit unit, and the unit is recorded before the type and hostility filters (§ 5).
- [L] src:d2dfg-blizzard: `NextHit` with `NextDelay` frames before the same unit can be hit again. **held**
  Detail: state 86 on the unit for `NextDelay` frames, tested for any `NextHit` missile (§ 5).
- [L] src:d2dfg-blizzard: `SrcTown` destroys the missile when its caster is in town; `Town` 0 destroys it in town.
  **held** (§ 4)
- [L] src:d2dfg-blizzard: `ToHit` 1 tests the caster's attack rating, 0 always hits. **held with refinement**
  Detail: `COMBAT_ToHitRoll` on the owner's seed with the missile's stat 19; a miss ends the missile (§ 5).
- [L] src:d2dfg-blizzard: `AlwaysExplode` runs the hit function when the missile ends. **held with refinement**
  Detail: also on a missed hit, where a hit-function return with bit 2 keeps the missile (§ 5).
- [L] src:d2dfg-blizzard: `CanSlow` rows obey the slow-missiles state. **held** (state 87, § 2)
- [L] src:d2dfg-blizzard: `Pierce` 1 lets the pierce modifier work; `MissileSkill`/`Skill` take a skill's damage;
  `ApplyMastery` adds the elemental masteries; `SrcDamage` in 128ths; `Half2HSrc` halves it with a two-handed weapon.
  **held with refinement**
  Detail: the masteries enter at creation and again at the hit; `SrcDamage` 0xFF on a skill missile means no weapon
  share; the three stock `−1` rows all name a `Skill` (§§ 3, 6).
- [L] src:arreat-summit-amazon-passive: Pierce gives a missile a chance to continue through its victim. **held**
- [L] src:purediablo-piercing: at most 4 pierces, 5 targets. **held**
  Detail: at most four steps of the count (§ 3).
- [L] src:purediablo-piercing: the chance is checked at each target, the chain ending at the first failure.
  **held with refinement**
  Detail: the same distribution, drawn once at **creation** on a local seed from the owner's base stat 328, up to four
  steps while `low % 100 < p`; no game or unit seed is drawn (§ 3).
- [L] src:purediablo-piercing: pierce happens only after a successful hit. **held with refinement**
  Detail: the pierce charge is taken before the to-hit roll, so a miss spends one (§ 5).
- [L] src:purediablo-piercing: a missile that misses but pierces "keeps traveling but doesn't deal any damage".
  **contradicted**
  Detail: a `ToHit` missile whose roll fails returns 2 and is freed at that unit, pierce or not (§ 5). Phase 2 case
  C5, [backlog](../../backlog/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md). *2026-10-25:* run:2026-10-25-skills: 105 missed rolls, each result 2, 7 of them with a pierce left
  and one pierce spent (§ 11).
- [L] src:purediablo-piercing: a blocked hit still pierces. **held**
  Detail: the pierce result is fixed before `MISSILE_ApplyDamage`'s defence roll (§ 5).
- [L] src:purediablo-piercing: pierce sources add up and above 100 % do nothing more. **held**
  Detail: `p = stat 166 + stat 156`, `low % 100 < p` (§ 3).
- [L] src:purediablo-piercing: pierce works for ranged physical attacks only; Bone Spear and Lightning always pass
  through, Fire Bolt stops at its first target. **held with refinement**
  Detail: the row's `Pierce` flag decides (60 rows, `lightningfury` among them), not the attack type; a row without
  `CollideKill` continues (`bonespear`, `lightningbolt`), a `CollideKill` row ends (`firebolt`) (`p45b-rows.txt`).
- [L] src:arreat-summit-skill-trees: Guided Arrow does not work with Pierce. **held**
  Detail: `guidedarrow` has no `Pierce` flag (`p45b-rows.txt`).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0059FA30` | `sub_0059FA30_MissileCreate` | create a missile from a parameter block (31 391 logged exits, § 11) | C |
| `0x0059F8A0` | `sub_0059F8A0_MissileUnitInit` | type-3 branch of `SUnitCreate`: missile data, the every-frame event | I |
| `0x0064A100`, `0x0064A150` | `sub_0064A100_MissileDataAlloc`, `sub_0064A150_MissileDataFree` | the 0x34-byte missile data at `Unit+0x14` | I |
| `0x0059F900` | `sub_0059F900_MissileInitDamage` | damage block, then the missile's stats | I |
| `0x0064B860` | `sub_0064B860_MissileDamageBlock` | the creation-time damage (Missiles or Skills columns, weapon, mastery) | I |
| `0x0064A850` | `sub_0064A850_MissileCritRoll` | critical / deadly / mastery critical, inline steps on a unit's seed (§ 11) | C |
| `0x0064ABA0` | `sub_0064ABA0_ElemMasteryBonus` | `MulDiv(x, mastery of EType, 100)` for `ApplyMastery` | I |
| `0x0064A930`, `0x0064AA60` | `sub_0064A930_AddOwnerElemDamage`, `sub_0064AA60_ScaleElemDamage` | the owner's elemental item damage, scaled by `SrcDamage`/128 | I |
| `0x0064AC60` | `sub_0064AC60_MissileDamageToStats` | the block into missile stats 12, 21, 22, 25, 48–66, 120–122, 315–317, 326 | I |
| `0x0059F940` | `sub_0059F940_MissilePierceCount` | pierce count from a local seed of stat 328 (§ 11) | C |
| `0x0056ECB0` | `sub_0056ECB0_SkillMissileCreate` | (P1.1 name) skill missile in a line | I |
| `0x0056EE90` | `sub_0056EE90_SkillMissileCreateLob` | (P1.1 name) skill missile, lobbed | I |
| `0x0056EDE0` | `sub_0056EDE0_MissileCreateAt` | skill missile created at a point (quests, shrines, missiles) | I |
| `0x0056F460`, `0x0056F550` | `sub_0056F460_SkillThrowDo`, `sub_0056F550_SkillThrowLeftDo` | `srvdofunc` 3 (Throw), 5 (Left Hand Throw) | I |
| `0x00552FD0`, `0x00621CE0` | `sub_00552FD0_UnitGetOwner`, `sub_00621CE0_UnitSetOwner` | owner by guid, `Unit+0xC8` bit 10 | I |
| `0x005ADCC0` | `sub_005ADCC0_MissileFrameEvent` | the missile list's default event callback | I |
| `0x005ADBB0` | `sub_005ADBB0_MissileDoFrame` | town tests, do function, free on 2 (13 335 logged frames, § 11) | C |
| `0x005AE1F0` | `sub_005AE1F0_MissileMoveCollide` | do function 1: step, range, cells against the collide mask | I |
| `0x005AE400` | `sub_005AE400_MissDo02SubMissile` | do function 2: `SubMissile1` per new cell, then do 1 | I |
| `0x005AE480` | `sub_005AE480_MissDo03CloudMark` | do function 3: the `0x40` cell mark while still, then do 1 | I |
| `0x005AEF70` | `sub_005AEF70_MissDo14PeriodicDo` | do function 14: a skill do function every `Param1` frames | I |
| `0x005ACFC0` | `sub_005ACFC0_MissHit23CallDo` | hit function 23 (*corrected 2026-10-20*, was "22"): retarget, a skill do function by `sHitPar1` | I |
| `0x005ADF10` | `MISSILE_HitUnit` | (combat name) the hit: filters, pierce, to-hit, hit/damage functions (105 missed returns, § 11) | C |
| `0x005ADA40` | `sub_005ADA40_MissileHitTypeFilter` | `CollideType` 0 none, 1 players, 2 monsters, other all | I |
| `0x005ADA80` | `sub_005ADA80_MissilePierceUse` | stat 328 − 1 on a `Pierce` row (checked, § 12) | C |
| `0x005ADB00` | `sub_005ADB00_MissileJustHitState` | state 86 on the hit unit for `NextDelay` frames | I |
| `0x005ADCD0` | `sub_005ADCD0_MissileApplyAndAc` | `MISSILE_ApplyDamage`, then stat 120 against a monster's defence | I |
| `0x005AD9D0` | `sub_005AD9D0_MissileEndHit` | hit function with no unit, then free; no reference found | I |
| `0x005A8910` | `sub_005A8910_MissileElemRoll` | one element's `RangeB` with its mastery | I |
| `0x005A8730` | `sub_005A8730_CollideUnitFilter` | the shared unit test of the collide filters | I |
| `0x005A87B0`, `0x005A87F0`, `0x005A8850`, `0x005A8890` | `sub_005A87B0_CollideMonster`, `sub_005A87F0_CollidePlayerOrAlly`, `sub_005A8850_CollideUnit`, `sub_005A8890_CollideMissile` | the collide-type filters | I |
| `0x00641CB0` | `sub_00641CB0_FindUnitAtCell` | a unit whose footprint covers a cell, through a filter | I |
| `0x00648EB0`, `0x00648F40` | `sub_00648EB0_PathCellCollision`, `sub_00648F40_PathStepCells` | the path's cell collision word; the cells of the last step | I |
| `0x00648690`, `0x006486C0`, `0x006486D0`, `0x00648700`, `0x00648CE0` | `sub_00648690_PathSetSpeed`, `sub_006486C0_PathGetSpeed`, `sub_006486D0_PathSetMaxSpeed`, `sub_00648700_PathSetAccel`, `sub_00648CE0_PathSetCollMask` | path fields `+0x7C`, `+0x84`, `+0x88`, `+0x50` | I |
| `0x006502D0` | `sub_006502D0_PathVelocityStep` | acceleration and the step vector (§ 11) | C |
| `0x0064A190`, `0x0064A1C0` | `MISSDATA_GetFlags`, `MISSDATA_SetFlags` | `MissileData+0x14` | I |
| `0x0064A1E0`, `0x0064A210` | `MISSDATA_SetLevel`, `MISSDATA_GetLevel` | `+0x0C` (s16) | I |
| `0x0064A240`, `0x0064A280` | `MISSDATA_SetSkill`, `MISSDATA_GetSkill` | `+0x0A` (s16, set 0 when < 1) | I |
| `0x0064A2B0`, `0x0064A300` | `MISSDATA_SetRange`, `MISSDATA_GetRange` | `+0x0E` (s16, clamped) | I |
| `0x0064A330`, `0x0064A380` | `MISSDATA_SetRemaining`, `MISSDATA_GetRemaining` | `+0x10` (s16, clamped) | I |
| `0x0064A3B0` | `MISSDATA_GetElapsed` | `+0x0E − +0x10` | I |
| `0x0064A400`, `0x0064A470` | `MISSDATA_SetLastHit`, `MISSDATA_IsLastHit` | `+0x18`/`+0x1C`, `LastCollide` rows only | I |
| `0x0064A5F0`, `0x0064A640` | `MISSDATA_SetActivate`, `MISSDATA_GetActivate` | `+0x08` (s16, clamped) | I |
| `0x0064A5A0` | `sub_0064A5A0_MissileHitClass` | the `HitClass` byte | I |
| `0x0073C720` | `g_MissileCollideTypes` | 9 × {filter, mask} by `CollideType` | I |
| `0x0073C768`, `0x0073C71C` | `g_MissileSrvDoFuncs`, `g_MissileSrvDoFuncCount` | do table, 53 | I |
| `0x0073C840`, `0x0073C83C` | `g_MissileSrvHitFuncs`, `g_MissileSrvHitFuncCount` | hit table, 71 | I |
| `0x0073C960`, `0x0073C95C` | `g_MissileSrvDmgFuncs`, `g_MissileSrvDmgFuncCount` | damage table, 31 | I |

## Walkthrough

### 1. The missile unit and its data

- [I] `SUnitCreate(type 3, class, x, y, game, room, 1, mode = CollideType, 0)` makes the unit; its type-3 branch
  `sub_0059F8A0_MissileUnitInit` allocates the missile data (0x34 bytes, `Unit+0x14`), clears `Unit+0xC4` bits 1 and 3,
  stores its argument at `Unit+0x0C` and queues an event record with frame −1 on the missile list (`sub_005415E0`: the
  list at `game+0xB8 → +0xA04 + 4 · listIndex(type)`, the "every frame" list). So a missile's **mode** (`Unit+0x10`) is
  its `CollideType`. (0x0059FC51–0x0059FC75, fn:sub_0059F8A0_MissileUnitInit@0x0059F8A0, 0x005415E0–0x0054164A)
- [I] The missile's seed `Unit+0x20` is set by `SUnitCreate` for every type but 0 (`sub_00552DF0_UnitSeedInit` from the
  game seed); [rng/0002](../rng/0002-seed-tree.md) has that `[C]` for server units, and this path reaches it with type 3.
  (fn:sub_00555230_SUnitCreate@0x00555230, fn:sub_00552DF0_UnitSeedInit@0x00552DF0)
- [I] The missile data (`MissileData`, `re/types/skills.h`): `+0x08` activate mark (s16, `range − activate`), `+0x0A`
  skill (s16, 0 when < 1, capped 0x7FFF), `+0x0C` level (s16), `+0x0E` range (s16, total frames), `+0x10` frames left
  (s16), `+0x14` flags (bit 0 weapon damage, bit 1 from the block's bit 2 or the creation flag `0x10000`), `+0x18`/`+0x1C`
  the last unit hit (type, guid; −1 when none), `+0x20`/`+0x24` a second unit reference, `+0x28`, `+0x2C`, `+0x30` used by
  functions of the catalogue. The accessors clamp s16 writes to −0x8000..0x7FFF. `MISSDATA_GetElapsed` is
  `range − frames left`. (fn:MISSDATA_GetRemaining@0x0064A380, fn:MISSDATA_GetElapsed@0x0064A3B0, struct:MissileData+0x10)
- [I] The owner: `sub_00621CE0_UnitSetOwner(missile, owner)` stores it and sets `Unit+0xC8` bit 10;
  `sub_00552FD0_UnitGetOwner` finds the unit by the stored guid only when that bit is set. (fn:sub_00552FD0_UnitGetOwner@0x00552FD0)

### 2. Creation

The parameter block (`MissileParams`, 0x5C bytes, zeroed by every caller):

| Offset | Field | Used when |
|---|---|---|
| `+0x00` | flags | below |
| `+0x04` | owner (a player or a monster, else no missile) | always |
| `+0x08` | source unit (start position when flag 1 is clear; the `SrcMissDmg` source) | flag 1 clear |
| `+0x0C` | target unit | when set, the path aims at it |
| `+0x10` | missile class (row) | always; must be < the row count |
| `+0x14`, `+0x18` | start x, y | flag `0x1` |
| `+0x1C`, `+0x20` | target x, y: an offset from the start (flag `0x2`) or absolute (flag `0x20`); else the start | |
| `+0x28` | velocity: `<< 8` (flag `0x4`), as is (flags `0x4` and `0x10`) | flag `0x4` |
| `+0x2C`, `+0x30` | skill, level | always |
| `+0x34` | loops of the `SubStart..SubStop` range | flag `0x8` and `SubLoop` |
| `+0x40` | frames already run: range −= it, `Unit+0x44 = it << 8` | flag `0x200` |
| `+0x44` | activate override | flag `0x800` |
| `+0x48` | missile stat 19 (to-hit) | flag `0x1000` |
| `+0x4C` | range override | flag `0x8000` |
| `+0x54`, `+0x58` | callback `(ECX missile, EDX +0x58)`, run before the damage block | non-null |
| flag `0x400` | lob: frames left = `dist · 65536 / (16 · v)` | |
| flag `0x10000` | missile data flag bit 1 | |

```c
// fn:sub_0059FA30_MissileCreate@0x0059FA30 (ECX game, EDX params), trimmed
if (!p->owner || p->cls < 0 || p->cls >= nMissiles || p->owner->type > 1 || !(rec = MissileRec(p->cls))) return 0;
(x, y) = (p->flags & 1) ? (p->x, p->y) : p->source ? UnitSubXY(p->source) : return 0;
room = RoomAtSubtile(UnitGetRoom(p->owner), x, y);  if (!room) return 0;
(tx, ty) = (p->flags & 2) ? (x + p->tx, y + p->ty) : (p->flags & 0x20) ? (p->tx, p->ty) : (x, y);
v = (p->flags & 4) ? ((p->flags & 0x10) ? p->vel : p->vel << 8) : ((rec->VelLev * p->lvl) / 8 + rec->Vel) << 8;
if ((rec->b04 & 8 /*CanSlow*/) && HasState(p->owner, 87) && (l = StatListByState(p->owner, 87)))
    v = ListStat(l, 161) * v / 100;
if (v) v = v * 75 / 100;
t = p->target;
if (v) {
    if (!t && tx == x && ty == y) { tx++; ty++; }
    else if (t && t != p->owner && UnitSubXY(t) == UnitSubXY(p->owner)) { t = 0; tx++; ty++; }
    (ex, ey) = t ? UnitSubXY(t) : (tx, ty);
    if (abs(ex - x) >= 100 || abs(ey - y) >= 100) return 0;
}
m = SUnitCreate(3, p->cls, x, y, game, room, 1, rec->CollideType, 0);  if (!m) return 0;
range = (p->flags & 0x8000) ? p->range : rec->LevRange * p->lvl + rec->Range
        + ((p->flags & 8) && rec->SubLoop ? (rec->SubStop - rec->SubStart) * p->loops : 0);
if (p->flags & 0x200) { range -= p->ran; m->u44 = p->ran << 8; }
MISSDATA_SetRange(m, range);  MISSDATA_SetRemaining(m, range);
MISSDATA_SetActivate(m, range - ((p->flags & 0x800) ? p->activate : rec->Activate));
path = m->path;  PathSetSpeed(path, 0);
t ? PathSetTargetUnit(path, t) : PathSetTargetXY(path, tx, ty);
PATH_SetMarkMask(path, rec->Collision ? 0x40 : 0);
PathSetCollMask(path, g_MissileCollideTypes[rec->CollideType].mask);
if (rec->b04 & 0x10 /*CanDestroy*/) m->c4 |= 4;
if (v) { PathSetSpeed(path, v); PathPlan(path, m, 0); }
MISSDATA_SetLastHit(m, p->owner);                       // only for LastCollide rows
PathSetAccel(path, rec->Accel);  PathSetMaxSpeed(path, rec->MaxVel << 8);
if (p->flags & 0x400) MISSDATA_SetRemaining(m, ((max(UnitDistance(m, tx, ty), 1)) << 16) / (v << 4));   // 0 when v = 0
UnitStatListCreate(m);  if (p->cb) p->cb(m, p->cbArg);
MISSDATA_SetSkill(m, p->skill);  MISSDATA_SetLevel(m, p->lvl);
MissileInitDamage(p->source; ESI p->owner, EBX m, EDI p->lvl);                          // § 3
UnitSetOwner(m, p->owner);  m->c4 &= ~8;  MissilePierceCount(EAX p->owner, m);          // § 3
if (p->flags & 0x1000) SetStat(m, 19, p->toHit);
if (p->flags & 0x10000) MISSDATA_SetFlags(m, MISSDATA_GetFlags(m) | 2);
sub_005A43B0(game, p->owner, m);                        // a monster owner only (0x005A4270(…, 5)); not read
SetStat(m, 327, rec->DamageRate);
return m;
```

- [I] As above. Integer semantics: `(VelLev · lvl) / 8` is a signed division rounding toward zero (`cdq; and edx,7;
  sar 3`); the slow and the 75 % scalings are signed `/ 100`; the lob division is unsigned. `MaxVel << 8` is built with
  `mov dh` (a byte times 256). The distance test is on the start and the target point (or the target unit's position),
  `≥ 100` in either axis refuses. (0x0059FB18–0x0059FBAB, 0x0059FC2E–0x0059FC48, 0x0059FDD4–0x0059FDDE, 0x0059FE02–0x0059FE12)
- [I] **The skill creators** (all `ECX` game, `EDX` missile class, `ret 0x20`; stack `unit, skill, lvl, dx, dy, tx, ty,
  useAmmo`; fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0, fn:sub_0056EE90_SkillMissileCreateLob@0x0056EE90):
  - `SkillMissileCreate`: flags `0x21`; start = the unit's position (`path+0x0C/+0x10` for types 2, 4, 5, else
    `PathGetX/Y`) plus `(dx, dy)`; target = `(tx, ty)` when both are non-zero, else `SKILLS_GetTargetXY` (no missile
    when that fails or gives 0); for a **monster** owner with stat 19 ≠ 0, flag `0x1000` and that to-hit. With
    `useAmmo` and a player, `PLAYER_UseAmmo` must return ≥ 1 or there is no missile.
  - `SkillMissileCreateLob`: flags `0x420`; source = the unit (flag 1 clear: the start is the unit's own position, the
    `(dx, dy)` start it computes is unused); target as above, `GetTargetXY`'s points not tested for 0; no to-hit flag.
  - `sub_0056EDE0_MissileCreateAt(ECX game, EDX unit; skill, lvl, cls, x, y)` (`ret 0x14`; the name and reading of
    plan 0049 Phase 1, quests/0001 on `main`, which this reading agrees with): with `x` and `y` both 0 it takes the point
    from `SKILLS_GetTargetXY`; it refuses no point or a point more than 100 from the unit (`UnitDistance`, unsigned
    `> 100`), then flags 1, start `(x, y)`, no target (so a moving missile aims at `(x + 1, y + 1)`). (fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0, fn:sub_0056EE90_SkillMissileCreateLob@0x0056EE90,
    fn:sub_0056EDE0_MissileCreateAt@0x0056EDE0, 0x0056ED84–0x0056EDB7, 0x0056EEBB–0x0056EEC5)
- [I] **`useAmmo` at the 33 call sites** of the line and lob creators (`AMMO` lines, the eight `?` read by hand in the
  `SITE` windows): 1 at `SKILL_AttackDo` (`srvdofunc` 1) unless the unit's ranged missile (`0x00645F00`) is 27
  (`magicarrow`), at the Throw and Left Hand Throw do functions 3 and 5 (lob for a weapon of item type 38, else line;
  the thrown item is the hand item that is throwable or has stat 125), at five monster functions, six sites (`0x005A21D0`
  twice, `0x005A29A0`, `0x005A35D0` once (its two other calls pass 0), `0x005A6D50`, `0x005A6EB0`; *recounted at review
  2026-10-20, lane/msw: the sites push 1 in objdump; first written "four"*), at `0x005CBF90` and at both calls of `0x005D88B0`; 0
  everywhere else, `SKILLS_SrvDo` included. The ammunition use only acts for a player owner. (`missiles-scan.txt` `AMMO`,
  fn:SKILL_AttackDo@0x0056F070, fn:sub_0056F460_SkillThrowDo@0x0056F460, fn:PLAYER_UseAmmo@0x0056C3F0)
- [I] **`SKILLS_SrvDo`'s missile** (P1.1 § 6): `(rec->lob ? Lob : Line)(unit, id, lvl, dx, dy, tx, ty, 0)` with
  `EDX = srvmissile` (`+0x46`). With an item cast's effect flag, `dx = tx − x`, `dy = ty − y` and the target becomes
  `(tx + dx, ty + dy)`: the line missile starts at the target point and flies on in the same direction to twice the
  distance; a lob starts at the caster and aims at the doubled point. (0x0056F9D0–0x0056FA29)
- [I] **No `srvdofunc`.** 48 stock Skills rows have a `srvmissile` and no `srvdofunc`; `g_SkillDoFuncs[0]` is null, so
  their only server action at the do frame is this missile (3 of them lob, 10 have `decquant`). Two more rows (307
  `CorpseCycler`, 325 `VineCycler`) name only `srvmissilea..c` and get no missile from `SKILLS_SrvDo`. The tier-A rows:
  36 Fire Bolt (`firebolt`, line), 251 Fire Trauma (`bomb in air`, lob), 25 Plague Javelin (`plaguejavelin`, line; its
  `decquant` uses the javelin through `SKILLS_SrvDo`'s `PLAYER_UseAmmo`, and `srvstfunc` 4 runs at the start).
  (`missiles-rows.txt` `ROWS skills`, tbl:Skills.txt:srvmissile, tbl:Skills.txt:lob, tbl:Skills.txt:decquant)
- [I] **The other creators** (Ghidra's 82 calling functions; `missiles-ghidra-xrefs.txt`): skills core `0x0056D400`,
  `0x0056D4E0` and the three above; shrine functions 19, 21 and 22 of `g_ShrineEffects` (`0x00582DA0`, `0x005830E0`,
  `0x00583410`, reached only through that table) and `0x0058C8D0` (from `sub_0058C9A0_A5Q5_AncientDeath`); monster
  functions `0x005A29A0`, `0x005A2EE0`, `0x005A3490`; 30 functions in the missile range (the sub-missile helpers
  `0x005A9370` (a ring of 16 from the direction tables `0x006E2510`/`0x006E24D0`), `0x005A9530` (a disc), `0x005A9720`,
  `0x005A9820`, and the numbered functions); 40 skill functions. `MissileCreateAt` is called by
  `sub_0058DF20_A5Q6_BaalDeath`, `sub_00593710_A1Q4_StoneOperate`, `sub_005954F0_A1Q5_DeathSpawn` and 14 more sites.
  The quest calls pass missiles 288 `cairnstones`, 332 `towerchestspawner` and 625 `baalfx control`, as quests/0001
  reads them on `main` (plan 0049 Phase 1). Items create missiles only through `ITEMSKILL_Cast` → `SKILLS_SrvDo`.
  (fn:sub_0056EDE0_MissileCreateAt@0x0056EDE0, data:g_ShrineEffects@0x006E1850, tbl:Missiles.txt:Id)

### 3. The damage the missile carries

```c
// fn:sub_0064B860_MissileDamageBlock@0x0064B860 (blk, owner, source, missile, lvl), trimmed
memset(blk, 0, 0x7C);
if (rec->Skill < 1 && !(rec->b05 & 0x80 /*MissileSkill*/)) {            // damage from the Missiles columns
    src = rec->SrcDamage; srcMiss = rec->SrcMissDmg;
    min = MISS_GetDamMin(missile, owner, cls, lvl);  max = MISS_GetDamMax(…);  et = rec->EType;
    emin = MISS_GetElemMin(…); emax = MISS_GetElemMax(…); elen = MISS_GetElemLen(…);
    if (rec->b05 & 1 /*ApplyMastery*/) { emin += ElemMastery(owner, et, emin); emax += ElemMastery(owner, et, emax); }
} else {                                                                  // damage from the Skills row
    sk = rec->Skill;  if (rec->b05 & 0x80) { s = MISSDATA_GetSkill(missile); if (s > 0) sk = s; }
    srec = SKILLS_GetRecord(sk);  if (!srec) return;
    src = srec->SrcDam; srcMiss = 0;  if (rec->SrcDamage == 0xFF) src = 0;
    min = SKILLS_GetPhysMin(owner, sk, lvl, 0);  max = SKILLS_GetPhysMax(owner, sk, lvl, 0);  et = srec->EType;
    emin = SKILLS_GetElemMin(owner, sk, lvl, 1); emax = …Max(…, 1); elen = …Len(…, 1);
}
if (rec->Holy & 1) blk->flags |= 0x100;  if (rec->Holy & 2) |= 0x200;  if (rec->Holy & 4) |= 0x400;
ed = minPct = maxPct = 0;  wmin = wmax = 0;
if (src) {
    blk->flags |= 1;
    w = owner player ? weapon(owner, 1) : owner monster with +0x60 ? weapon(owner) : 0;
    if (MissileCritRoll(ESI owner, w)) blk->flags |= 2;                   // draws on the owner's seed
    if (w && w->type == ITEM) {
        if ((rec->b05 & 0x40 /*Half2HSrc*/) && sub_006289C0(w)) src /= 2;
        ed = SKILLS_GetMasteryBonus(owner, w, 0, 1) + str · StrBonus(w) / 100 + dex · DexBonus(w) / 100;
        (lo, hi) = Throwable(w) ? (159, 160) : (owner+0x60 && sub_0063D340(owner, +0x60) == 2) ? (23, 24) : (21, 22);
        wmin = stat(owner, lo) << 8;  wmax = stat(owner, hi) << 8;
        if (ITEMS_UnitIsType(w, 57)) blk->undeadPct += 50;
    } else {
        if (owner monster && hireling) ed = stat(owner, 2);
        wmin = stat(owner, 21) << 8;  wmax = stat(owner, 22) << 8;
    }
    wmin = wmin * src / 128;  wmax = wmax * src / 128;                    // signed, toward zero
    ed += stat(owner, 25);  minPct = stat(owner, 18);  maxPct = stat(owner, 17);
    blk->demonPct += stat(owner, 121); blk->undeadPct += stat(owner, 122); blk->acDmg += stat(owner, 120);
    bypass flags 0x100/0x200/0x400 from owner stats 103/104/106;
} else if (srcMiss && source) {
    if (MissileCritRoll(ESI source, 0)) blk->flags |= 2;                  // draws on the source's seed
    wmin = stat(source, 21) * srcMiss / 128;  wmax = stat(source, 22) * srcMiss / 128;
    ed = stat(source, 25); minPct = stat(source, 18); maxPct = stat(source, 17); (demon, undead, ac) from source;
}
ed += stat(missile, 25) + max(minPct, maxPct);  blk->edPct = max(ed, -90);
blk->min = wmin + min;  blk->max = wmax + max;
store (emin, emax, elen) by et: 1 fire, 2 lightning, 3 magic, 4/12 cold, 5 poison, 6/7/8 life/mana/stamina steal,
                               9 stun (length), 11 burn;
if (src)  { AddOwnerElemDamage(blk, owner, shift 8); ScaleElemDamage(blk, src); }
else if (srcMiss && source) { AddOwnerElemDamage(blk, source, shift 0); ScaleElemDamage(blk, srcMiss); }
```

- [I] As above (0x0064B8CE–0x0064BF19; the element switch is the jump table at `0x0064BF24`). `SrcDamage` is `+0x12D`
  (−1 stored `0xFF` means "no weapon share" for a skill missile), `SrcMissDmg` `+0x12E`, `Holy` `+0x12F`. The weapon
  terms are taken **at creation**; `edPct` is stored as missile stat 25 and applied at the hit (§ 6). The block is then
  written as missile stats by `sub_0064AC60_MissileDamageToStats`: 12 = level, 21/22 = min/max, 48/49 fire, 315 fire
  length, 50/51, 52/53, 54/55/56, 57/58/59, 326 poison count, 60–66 steals and stun, 316/317 burning, **315 again from the
  burn length** (the fire length is overwritten, 0x0064ACFD then 0x0064AE2F), 121, 122, 120, 25; stat 103/104/106 = 1 for
  the bypass flags, stat 141 = 1 for a critical; then the owner's stat-180 entries (`damage_vs_montype`).
  (fn:sub_0064AC60_MissileDamageToStats@0x0064AC60, tbl:Missiles.txt:SrcDamage, tbl:Missiles.txt:Skill,
  tbl:Missiles.txt:ApplyMastery, tbl:Skills.txt:SrcDam)
- [I] **The mastery bonus on the missile path** (P1.1's `0x0064B860` question): `SKILLS_GetMasteryBonus(owner, weapon,
  0, 1)` is added to the missile's enhanced damage percent when the weapon is an item and the row takes weapon damage;
  `(…, 0, 2)` is the third critical chance of `MissileCritRoll`; the elemental masteries (stats 329 fire, 330 lightning,
  331 cold for types 4 and 12, 332 poison) enter only `ApplyMastery` rows through `sub_0064ABA0_ElemMasteryBonus`, and
  again at the hit through `sub_005A8910_MissileElemRoll` (§ 6). (0x0064BB1D–0x0064BB29, 0x0064A8E5–0x0064A8EB,
  0x0064B971–0x0064B99C, fn:SKILLS_GetMasteryBonus@0x00645830)
- [I] **`MissileCritRoll(ESI unit, weapon)`**: `c = stat(unit, 337)`; step the unit's seed inline
  (`low' = low · 0x6AC690C5 + high`, `high'` = the carry), `if (low' % 100 < c) return 1` (the remainder is unsigned,
  compared signed); then, only when `UnitGetStat(unit, 141)` ≠ 0, one more step against it; then, with a weapon and
  `SKILLS_GetMasteryBonus(unit, weapon, 0, 2)` ≠ 0, one more. So 1 to 3 draws on the owner's seed per missile that takes
  weapon damage (an arrow, a javelin, a `SrcDam` skill missile), the first unconditional. This is not the melee
  build's chain (combat/0001 § 5: mastery critical, stat 337, stat 141, each only when > 0): the order differs and the
  stat-337 draw happens at 0 (*review note 2026-10-20*). (0x0064A850–0x0064A92D, 0x0064A864–0x0064A890)
- [I] **The pierce count** (`MissilePierceCount(EAX owner, missile)`): for an owner of type 0 or 1 and a `Pierce` row
  (`+0x04` bit 2), `p = stat(owner, 166) + UnitGetStat(owner, 156)`; when `p` ≠ 0, a **local** seed
  `RNG_SeedInit(baseStat(owner, 328))` is stepped up to four times while `low % 100 < p`, and the count is the missile's
  stat 328. Since P1.1 found stat 328 raised by 1 on every skill request, the count depends on the owner's request
  count, not on any game seed. (fn:sub_0059F940_MissilePierceCount@0x0059F940, tbl:Missiles.txt:Pierce)

### 4. Each frame

```c
// fn:sub_005ADBB0_MissileDoFrame@0x005ADBB0 (EDI missile, [ebp+8] game), trimmed
if (!rec || rec->pSrvDoFunc <= 0 /*s16*/ || rec->pSrvDoFunc >= g_MissileSrvDoFuncCount /*53*/) return;
room = UnitGetRoom(m) ?: RoomAtSubtile(0, SubX(m), SubY(m));
owner = UnitGetOwner(game, m);
if ((rec->b05 & 8 /*SrcTown*/) && owner && UnitGetRoom(owner) && RoomIsTown(…)) goto free;
if (owner && owner->type == 0 && UnitGetRoom(owner) && RoomIsTown(…))          goto free;
if (!(rec->b05 & 4 /*Town*/) && RoomIsTown(room))                               goto free;
if (g_MissileSrvDoFuncs[rec->pSrvDoFunc](game, m) == 2) free: UnitFree(game, m);
```

- [I] As above: a player's missile ends as soon as the player stands in town; a monster's only with `SrcTown`; any
  missile in a town room without `Town`. The do-table call has no null test (entries 4 and 38..52 are null, used by no
  stock row). This settles P1.1's `repeat` scan hit at `0x005ADC43`: it is this `SrcTown` test, a Missiles bit.
  (0x005ADBEE–0x005ADCB3, data:g_MissileSrvDoFuncCount@0x0073C71C, tbl:Missiles.txt:SrcTown, tbl:Missiles.txt:Town)
- [I] The frame pass: `sub_005414D0_GameRunUnitEvents` calls `0x00541240` first with the missile "every frame" list
  (`+0xA0C`) and then with the missile bucket of the current frame (`+0x204 + 4 · (frame & 63)`); a record without a
  callback calls `sub_005ADCC0_MissileFrameEvent` → `MissileDoFrame`. Where the missile pass sits against the other
  unit types' passes is the order of the calls that follow (`0x00540F60` …), not read here. (0x005414EE–0x00541508,
  0x0054129F, 0x005412F6) *2026-10-27 (plan 0050 P1.1):* the missile pass runs first, then players, monsters,
  objects and items ([anim/0001 § 6](../anim/0001-modes-frames.md#6-the-event-queue-and-the-frame-order)).

```c
// fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0 (ECX game, EDX m) — do function 1, trimmed
if (!rec) return HitUnit(m, 0, end 1);
if (PathGetSpeed(m->path) && UnitMoveStep(game, m) == 2) return HitUnit(m, 0, 1);       // the step did not move
left = MISSDATA_GetRemaining(m) - 1;  MISSDATA_SetRemaining(m, left);
if (left <= 0) return HitUnit(m, 0, 1);                                                 // range spent
ct = m->mode;  if (!ct) return 1;                                                       // CollideType 0
if (!room || !path) return 2;
c = PathCellCollision(path);  if (c & 5) return 2;                                      // freed, no hit function
if (ct == 6) return 1;
if (MISSDATA_GetRemaining(m) > MISSDATA_GetActivate(m) || c == 0) return 1;
if (!g_MissileCollideTypes[ct].filter) return 2;
ctx = { game, m, UnitGetOwner(game, m), rec };  size = UNIT_GetSizeX(m);
for each cell (x, y) of PathStepCells(path):
    k = CollisionTest(room, x, y, size, g_MissileCollideTypes[ct].mask);
    if (k) { u = FindUnitAtCell(room, x, y, filter, &ctx, size); if (u) return HitUnit(m, u, 0);
             if (k & 4) { HitUnit(m, 0, 1); return 2; } }
return 1;
```

- [I] As above (0x005AE1F0–0x005AE3FA). So the range is counted in do-function calls: a missile created with range `R`
  runs `R` frames at most; unit collision starts when `left ≤ R − Activate`. A cell word with bit 0 or 2 at the missile's
  own cell frees it **without** the hit function (no explosion); a crossed cell with bit 2 (`0x4`) but no unit runs the
  end-of-life hit. `PathCellCollision` is the path's cached `CollisionTest(room, x, y, size, 0x7FFF)` at its point
  (recomputed when the path is still). (fn:sub_00648EB0_PathCellCollision@0x00648EB0, fn:sub_00648F40_PathStepCells@0x00648F40)
- [I] **The collide types** (`g_MissileCollideTypes`, by `CollideType`; filter, mask): 0 none; 1 `CollidePlayerOrAlly`
  `0x0084` (a player, or a monster for which `0x006259B0` returns 2); 2 and 5 `CollideMonster` `0x0104`; 3 `CollideUnit`
  `0x0184` (a player or a monster); 4 none; 6 no filter, `0x0004` (walls only: the step ends at them); 7 `CollideMissile`
  `0x0040` (a missile whose row has `CanDestroy`); 8 `CollideUnit` `0x0185`. The shared unit test
  `sub_005A8730_CollideUnitFilter` requires the candidate's `Unit+0xC4` bits 2 and 3, refuses a unit in state 86 for a
  `NextHit` row, the last unit hit, and an owner-friendly unit unless `CollideFriend`. Stock use: 0 × 301, 1 × 6, 3 × 339,
  6 × 24, 8 × 14. (`missiles-scan.txt` `COLL`, `missiles-rows.txt` `ROWS collidetype`, 0x005A8730–0x005A88D1)
- [I] **Motion** (`sub_006502D0_PathVelocityStep`, from the path step with `ECX = 0x400`): with `accel` ≠ 0 a counter
  counts steps and on the fifth `v += accel` (then `v = max` and `accel = 0` when above the maximum, `v = 0` when
  negative) and the counter restarts; then `s = (v · 0x400) >> 6` and the step is `(dir.x · s) >> 12`, `(dir.y · s) >> 12`
  (arithmetic shifts) added to the 16.16 position. `v` starts as the creation velocity, the maximum is `MaxVel << 8`
  and `accel` is the raw `Accel` (s16). (0x006502D0–0x0065034C, 0x00554CCF, fn:sub_00650840_PathStep@0x00650840)
- [I] **Do function 2** (4 rows: `poisonjav` …): when `SubMissile1` ≥ 0, evaluate `SrvCalc1` and call
  `sub_005A9720(SubMissile1, 0, value)`, which, when `0x006505C0(path)` is non-zero, creates the sub-missile at the
  parent's position with velocity 0 (flags 5), the parent as source, the parent's skill and level, and loops `2 · lvl −
  2` when the value is > 0 (the value itself is not stored: 0x005A9770 then 0x005A97FD); then do function 1.
  **Do function 3** (26 rows) ORs `0x40` into its cell (`COLL_CellOrAt`) when its path is not moving, then do function 1.
  **Do function 14** is § 8. (fn:sub_005AE400_MissDo02SubMissile@0x005AE400, fn:sub_005AE480_MissDo03CloudMark@0x005AE480,
  fn:COLL_CellOrAt@0x0064CB90)
  *2026-10-20 (plan 0046 batch 9a, [skills/0004](0004-missile-do-1-18.md)):* do 2's map up to `MissileCreate` is
  `[C]` by emulation (run:2026-10-20-cat-emu-9a `sublob`) under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md) (accepted 2026-10-20): the case ends at that call
  (its boundary), and do 1 after a creation is not covered; the loop count `2·lvl − 2` is written whether or not the
  value is above 0, and only flag 8 depends on it. Table entry 1 is a thunk, `0x005B0BC0` → `jmp 0x005AE1F0`
  (fn:sub_005B0BC0_MissDo01Thunk@0x005B0BC0).

### 5. The hit

```c
// fn:MISSILE_HitUnit@0x005ADF10 (ECX game, EDX m; unit, end) -> 1 keep, 2 free
owner = UnitGetOwner(game, m);
c = (rec->b04 & 2 /*Explosion*/) ? 0 : 2;  p = 3;                 // c: bit0 end, bit1 damage, bit2 keep; p: pierce
if (unit) {
    if (rec->NextHit && HasState(unit, 86)) return 1;
    if (MISSDATA_IsLastHit(m, unit)) return 1;                   // LastCollide rows only
    MISSDATA_SetLastHit(m, unit);
    if (!MissileHitTypeFilter(unit, m->mode)) return 1;
    if (owner && !UnitsHostile(game, owner, unit) && !rec->CollideFriend) return 1;
}
if (owner && unit && (rec->b04 & 4 /*Pierce*/) && (stat(owner, 166) || UnitGetStat(owner, 156)))
    p = MissilePierceUse(m);                                     // 2 and stat 328 - 1 when it is > 0, else 3
if (rec->CollideKill) c |= 1;
if (unit) {
    if (rec->ToHit && !COMBAT_ToHitRoll(owner, unit, stat(m, 19), 1)) {        // draws on the owner's seed
        JustHitState(m, unit); UNIT_DispatchEvent(game, 0 /*hitbymissile*/, unit, m, 0);
        if (rec->AlwaysExplode && hitfn(rec) && (hitfn(game, m, unit) & 4)) return 1;
        return 2;                                                // a missed missile ends
    }
} else if (!end && !rec->AlwaysExplode) goto last;
if (p & 2) {
    JustHitState(m, unit); UNIT_DispatchEvent(game, 0, unit, m, 0);
    if (hitfn(rec)) { c = hitfn(game, m, unit); if (c & 4) return 1; }
}
if (unit && (c & 2)) {
    MISSILE_BuildDamage(game, m, unit, &pkt);  if (dmgfn(rec)) dmgfn(game, m, unit, &pkt);
    MissileApplyAndAc(game, m, unit, &pkt);
}
last:
if (((c & 1) || end) && (p & 1)) { COLL_SizeUnmark(room, SubX(m), SubY(m), UNIT_GetSizeX(m), 0x40); return 2; }
return 1;
```

`hitfn(rec)` is `g_MissileSrvHitFuncs[pSrvHitFunc]` when `0 < pSrvHitFunc` (s16) `< 71`; `dmgfn` the same for
`pSrvDmgFunc` and 31.

- [I] As above (0x005ADF10–0x005AE1E9). Order matters for a reimplementation: the last-hit unit is recorded before the
  type and hostility filters refuse; the pierce charge is taken before the to-hit roll, so a missed piercing missile has
  used one and still ends; a hit function's return value **replaces** the result (bit 0 end, bit 1 damage, bit 2 keep
  and return at once); without a hit function the result is `(Explosion ? 0 : 2) | (CollideKill ? 1 : 0)`; a successful
  pierce (`p` = 2) clears bit 0 of `p`, so the missile continues even with `CollideKill`. At the end of life (`end` 1)
  the hit function runs with no unit and no damage is built. (fn:sub_005ADA80_MissilePierceUse@0x005ADA80,
  fn:sub_005ADA40_MissileHitTypeFilter@0x005ADA40, tbl:Missiles.txt:CollideKill, tbl:Missiles.txt:AlwaysExplode)
- [I] **`justhit`** (`sub_005ADB00_MissileJustHitState`): for a `NextHit` row, a timed stat list of state 86 on the
  hit unit ending at `frame + NextDelay` (unit event 12), so any `NextHit` missile skips that unit until then.
  (0x005ADB00–0x005ADBA8, tbl:Missiles.txt:NextHit, tbl:Missiles.txt:NextDelay, tbl:States.txt:state)
- [I] `MissileApplyAndAc`: `MISSILE_ApplyDamage` (combat/0001: the knockback `RNG_Range(missile seed, 100) <
  KnockBack` when the unit is not in state 54, the defence roll, `COMBAT_ApplyDamage`, `COMBAT_GetHit`), then for a
  non-hireling monster with missile stat 120 ≠ 0, the monster's stat 31 (defence) += it, floored at 0.
  (fn:sub_005ADCD0_MissileApplyAndAc@0x005ADCD0, fn:MISSILE_ApplyDamage@0x005AD730)
- [I] **The 64 948 cell** (Phase 0's question): the four hit-table reads, `sub_005AD9D0_MissileEndHit`'s among them
  (Ghidra: `if (0 < sVar1 && sVar1 < DAT_0073c83c)`), read the word with `movzx` and test `test ax,ax; jle` before
  `movsx` and the bound; −588 fails the first test, so row 568 never calls a hit function: a bounds test of the signed
  value, not an out-of-table call. (`missiles-scan.txt` `TABREAD`, `missiles-rows.txt` `ROWSKIP`,
  data:g_MissileSrvHitFuncCount@0x0073C83C, fn:sub_005AD9D0_MissileEndHit@0x005AD9D0, tbl:Missiles.txt:pSrvHitFunc)

### 6. The packet at the hit (`MISSILE_BuildDamage`)

- [I] Draw order on the **missile's** seed (`RNG_RangeB(seed, hi − lo) + lo`, a draw only when both stats are ≥ 1):
  physical (stats 21, 22) → `+0x08`; fire (48, 49; mastery 329) → `+0x10`; magic (52, 53; 357) → `+0x20`; lightning
  (50, 51; 330) → `+0x1C`; cold (54, 55; 331) → `+0x24`; poison (57, 58; 332) → `+0x28`; burn (316, 317; 329) →
  `+0x14`. Between them, without draws: cold length 56 → `+0x30`, poison length 59 → `+0x2C` (divided by stat 326 when
  > 1), 62 → `+0x3C`, 60 → `+0x38`, 64 → `+0x40`, 315 → `+0x18`, 66 → `+0x44`. With a mastery stat ≠ 0 both bounds get
  `MulDiv(bound, mastery, 100)` added before the draw. Then `phys += phys · pct / 100` with `pct = stat 25 + 121 (demon) +
  122 (undead) + the stat-180 entries matching the target's monster type`, floored at −90; stat 141 doubles `phys` and
  sets packet flag `0x2000`; stats 103/104/106 set the bypass flags. (0x005A89A0–0x005A8C6F, fn:sub_005A8910_MissileElemRoll@0x005A8910)
  combat/0001 § 2 already names the call; this is its draw list. Phase 2 should log the missile seed at the hit.

### 7. The function tables

- [I] `g_MissileSrvDoFuncs[n](ECX game, EDX m)` → 1 keep, 2 free; `g_MissileSrvHitFuncs[n](ECX game, EDX m; unit)` → the
  result flags; `g_MissileSrvDmgFuncs[n](ECX game, EDX m; unit, packet)`. Used numbers on stock data: do 34 (1..36; 4 and
  24 unused, 23 and 24 the same function `0x005AF790`), hit 49 (non-null and unused: 5, 6, 11, 23), damage 13 (6 unused).
  What each number does is plan [0046](../../plans/0046-skills-function-catalogue.md), tier A's at P1.3.
  (`missiles-scan.txt` `DO`/`HIT`/`DMG`, `missiles-rows.txt` `ROWS`)

### 8. `CallDoFunc` from missiles

- [I] `sub_0056D810_CallDoFunc(n, skill, lvl)` (ECX/EDX passed through) calls `g_SkillDoFuncs[n]` when `n ≤ 0xBE`
  (unsigned) and the entry is non-null. Its two callers pass the **missile** in `EDX`: hit function 23 (`0x005ACFC0`;
  *corrected 2026-10-20, P1.3: first written "22"; number 23 is used by no stock row, row 233's 22 is `0x005ADD20`*:
  with an owner, a skill and a level > 0, `0x00620C10(m, unit)` when there is a unit, then `n = sHitPar1` (`+0x4C`);
  ~~row 233 holds 0 and entry 0 is null~~ *(review 2026-10-20: row 233 does not use this function)*) and do function 14 (`0x005AEF70`: `n = Param2` (`+0x3C`) when `elapsed %
  max(Param1, 1)` is 0, then do function 1; the grim wards hold `Param1` 6, `Param2` 30, `g_SkillDoFuncs[30]` =
  `0x005C37C0`). So a skill do function can run with a missile as its unit; what 30 does there is read in
  [skills/0003 § 8](0003-handlers.md#8-skill-do-30-with-a-missile-as-its-unit-missile-do-14) (a curse state around the
  missile's target point).
  (0x0056D810–0x0056D835, 0x005AD012–0x005AD03C, 0x005AEFAF–0x005AF009, tbl:Missiles.txt:sHitPar1, tbl:Missiles.txt:Param2)
  *2026-10-20 (plan 0046 batch 9a):* do 14's call is `[C]` by emulation up to `CallDoFunc` (its boundary under
  ADR-0021, accepted 2026-10-20; do 1 after it is not covered), and with a skill or a level ≤ 0 it returns 2 without calling do 1 (`[C]`: those cases
  return) (run:2026-10-20-cat-emu-9a `periodic`, [skills/0004 § 11](0004-missile-do-1-18.md#11-do-14)).

### 9. Draws, seeds and the chaining reading (ADR-0014)

| Event | Entry | Draws (this batch) | Seed |
|---|---|---|---|
| create | `MissileCreate` | `SUnitCreate`: one step of the game seed (rng/0002); `MissileCritRoll` 1–3 for weapon or source damage; pierce: a local seed, none on game state | game; owner (or source missile); local |
| frame | `MissileDoFrame` | the do function's (do 1: none of its own; the path step's planner not read) | — |
| hit | `MISSILE_HitUnit` | `ToHit` roll; the hit function's (catalogue); `BuildDamage` ≤ 7; the damage function's; knockback 1; defence; `COMBAT_ApplyDamage` (combat/0001) | owner; missile; missile; defender |
| end | `MISSILE_HitUnit(…, 0, 1)` | the hit function's | — |
| sub-missile | `0x005A9820` | re-seeds the parent's seed from `SubX + elapsed`, then 2 `RangeB` (P1.3's re-seed census) | parent missile |

- [I] Reading for Phase 2: a missile is a chain of events on **three** seeds: the owner's at creation (critical) and
  at the hit (to-hit), the missile's own from its creation (game seed) through its hits, and the defender's. The owner's
  seed is shared with everything else the owner does between creation and hit (other attacks, its own defence rolls),
  which is ADR-0014's chaining question; the missile seed is private to the missile except where a function re-seeds it
  (`0x005A9820`; the others are P1.3's). (fn:sub_0064A850_MissileCritRoll@0x0064A850, fn:COMBAT_ToHitRoll@0x0057D9B0,
  fn:MISSILE_BuildDamage@0x005A89A0)

### 10. Branches

- [I] Player against monster owner: the to-hit flag of `SkillMissileCreate` is monsters' only; ammunition is players'
  only; the town end of § 4 applies to every player owner and to monster owners with `SrcTown`; the hireling branch of
  the damage block uses stat 2 as the enhanced damage of a weaponless hireling. No difficulty, expansion or player-count
  test in the functions of §§ 1–6 as read. (fn:sub_0059FA30_MissileCreate@0x0059FA30, fn:sub_0064B860_MissileDamageBlock@0x0064B860)

### 11. Plan 0045 Phase 2: the run (run:2026-10-25-skills)

18 sessions of eight tier-A characters on slot 2 (the record:
[experiments § run:2026-10-25-skills](experiments.md#run2026-10-25-skills)); `tools/skills.py check` over the 18 logs:
**0 mismatches** (`workspace/logs/skills/2026-10-25-skills-check.txt`), coverage from `…-tally.txt`. Raises of the
Answer's bullets, each split where the run leaves a remainder (raised in part):

- [C] **Creation, raised in part** (§ 2): in 31 391 creations the stored velocity is `(Vel << 8) · 75 / 100` (or the
  caller's, then `· 75/100`), the path's `Accel` and `MaxVel << 8` as read, the range `Range` less the frames already
  run (30 941; 450 taken after a creation callback), the frames left equal to it (30 922; 19 lob counts taken), the
  activate mark, skill and level. (fn:sub_0059FA30_MissileCreate@0x0059FA30, run:2026-10-25-skills)
- [I] The remainder: the `VelLev` term (C2: no `spike1`–`spike4` created) and the `LevRange` term (C4: no `LevRange`
  row created; *2026-10-27:* C4 met by part 2, § 12), the slow-missiles scaling (no `CanSlow` row's owner slowed), the `SubLoop` loops, the 99-sub-tile
  refusal. (run:2026-10-25-skills)
- [C] **The missile's seed** (§ 2): `SUnitCreate` steps the game seed once and the missile's seed is
  `Init(post.low)` in 31 391 of 31 391 creations (`MC.gameseed`, `MC.seed`), the game seed chaining from one creation
  of a do event to the next in 21 860 pairs. (fn:sub_00555230_SUnitCreate@0x00555230, run:2026-10-25-skills)
- [C] **The owner's critical draws, raised in part** (§ 3): one inline step of the owner's seed per creation of a row
  that takes weapon damage, none for any other row: 984 creations with one draw, 30 407 with none (`MC.owner`).
  (fn:sub_0064A850_MissileCritRoll@0x0064A850, run:2026-10-25-skills)
- [I] The second and third draws (stat 141, the mastery's chance) are not reached: no creation drew twice.
  (run:2026-10-25-skills)
- [C] **The pierce count** (§ 3): from a local seed `Init(owner base stat 328)` in 1 066 creations of `Pierce` rows
  (856 with draws), the owner's and the game seeds untouched. (fn:sub_0059F940_MissilePierceCount@0x0059F940,
  run:2026-10-25-skills)
- [C] **Motion** (§ 4, case C3): in 11 413 logged frames of 493 followed missiles the velocity takes `Accel` on every
  fifth path step (278 fifth steps over 1 657 accelerating steps), is capped at `MaxVel << 8` with the acceleration
  stopping (60 caps), and the position moves `(dir · ((v · 0x400) >> 6)) >> 12` on both 16.16 axes; frames left drop by
  1 per frame (13 335). (fn:sub_006502D0_PathVelocityStep@0x006502D0, fn:sub_005ADBB0_MissileDoFrame@0x005ADBB0,
  run:2026-10-25-skills)
- [I] The floor at 0 is not reached (no velocity fell below 0). (run:2026-10-25-skills)
- [C] **The first frame** (P1.3's open question): each of the 493 followed missiles first runs its do function on
  the frame after its creation. (run:2026-10-25-skills)
- [C] **A frame's seed** (§§ 4, 5): the do function of a followed frame leaves the missile's seed unchanged, except
  by the hits inside it (37 frames, 110 checks: the hit's entry seed is the frame's, its exit the build's, the
  `MISSILE_ApplyDamage` boundary moving it in none of 36). (fn:sub_005ADBB0_MissileDoFrame@0x005ADBB0, run:2026-10-25-skills)
- [C] **The packet at the hit, raised in part** (§ 6): `MISSILE_BuildDamage` draws `RangeB(hi − lo) + lo` on the
  missile's seed once per stat pair with both bounds ≥ 1 and `hi − lo ≥ 1`, the mastery `MulDiv` on both bounds
  first, in 778 builds (39 with no draw, 720 with one, 19 with two), every drawn elemental field (594), the physical
  field with its percent and critical doubling (164) and the cold and burn lengths (24) as read. (fn:MISSILE_BuildDamage@0x005A89A0,
  run:2026-10-25-skills)
- [I] The order of the seven pairs is separated only by the 19 two-draw builds; the stat-180 entries are not checked.
  (run:2026-10-25-skills)
- [C] **A missed to-hit** (§ 5, case C5): `COMBAT_ToHitRoll`'s roll is the owner's next draw `low % 100` (269 rolls),
  and a failed roll returns 2 and frees the missile at that unit, a `Pierce` row having spent one pierce first: 105
  misses, 7 with a pierce left. (fn:MISSILE_HitUnit@0x005ADF10, fn:COMBAT_ToHitRoll@0x0057D9B0, run:2026-10-25-skills)
- [I] Not checked by the run: the result of a hit that does not miss (31 257 calls returned 2, oracles), a pierce
  used at a hit (*2026-10-27:* both checked for the rows with no hit function, § 12), the hit and damage functions, the sub-missile site `0x005A9820`.

### 12. Plan 0045 Phase 2 part 2: the run (run:2026-10-27-skills)

15 sessions, logger rev 4/5 (the record: [experiments § run:2026-10-27-skills](experiments.md#run2026-10-27-skills));
`tools/skills.py` (`c09f9419…`) over part 2's logs and part 1's re-checked: **0 mismatches**
(`workspace/logs/skills/2026-10-27-skills-check.txt` `f6e4df6c…`, `…-part1-check.txt` `82688917…`). § 11's checks
again over 19 667 creations, 5 660 moving frames of 414 followed missiles (238 fifth steps, 48 caps), 3 340 builds
(43 with two draws) and 124 missed to-hits; and two of § 11's remainders:

- [C] **The `LevRange` term** (§ 2, case C4): 271 `blaze` creations (row 67, `LevRange` 25, `Range` 90) at level 2,
  made by Blaze while the Sorceress walks, each with range and frames left `LevRange · lvl + Range` = 140 (`MC.range`,
  `MC.left`). The lead's `LevRange · (lvl − 1) + Range` would give 115: every one separates.
  (fn:sub_0059FA30_MissileCreate@0x0059FA30, tbl:Missiles.txt:LevRange, run:2026-10-27-skills)
- [I] The `VelLev` term (C2) is still not separated: 22 `spike2` creations (Normal Dark Wood's quill rats), all at
  level 1, where `(VelLev · 1) / 8` is 0 for `VelLev` 7; the two Nightmare sessions met no quill rat. *Review
  2026-10-27:* a `spike1` (`VelLev` 8) separates at level 1 already (velocity 11 against the lead's 10); carried to a
  later Blood Moor log, [backlog](../../backlog/2026-10-27-architect-reverser-plan-0045-c2-vellev-by-a-blood-moor.md).
  (run:2026-10-27-skills)
- [C] **The end of a damaging hit, raised in part** (§ 5): for a row with no hit function, on the 3 876 hit calls that
  reached `MISSILE_BuildDamage` (3 166 in part 2's logs, 710 in part 1's), the result and the missile's stat 328 are
  as § 5 reads them: a pierce used when the row has `Pierce`, the owner stat 166 or 156 (its value at the creation
  line) and stat 328 > 0, stat 328 falling by 1 and the missile kept (130: 12 + 118); otherwise the missile ends at
  the unit when the row has `CollideKill` (276: 137 + 139) and is kept when it has not (3 470: 3 017 + 453).
  (fn:MISSILE_HitUnit@0x005ADF10, fn:sub_005ADA80_MissilePierceUse@0x005ADA80, tbl:Missiles.txt:CollideKill,
  tbl:Missiles.txt:Pierce, run:2026-10-27-skills, run:2026-10-25-skills)
- [I] The remainder: the 64 hits of rows with a hit function (its result replaces the end bit: a boundary), the
  1 203 calls that returned before the build (the last-hit, type and hostility filters, not separated from each
  other), the `end` call's own branch, `AlwaysExplode`, and an owner whose pierce stats changed after the creation.
  (run:2026-10-27-skills, run:2026-10-25-skills)

## Data touched

`tbl:Missiles.txt:Id`, `pSrvDoFunc`, `pSrvHitFunc`, `pSrvDmgFunc`, `Vel`, `VelLev`, `MaxVel`, `Accel`, `Range`,
`LevRange`, `Activate`, `SubLoop`, `SubStart`, `SubStop`, `CollideType`, `Collision`, `CollideKill`, `CollideFriend`,
`LastCollide`, `NextHit`, `NextDelay`, `Size`, `Pierce`, `CanDestroy`, `CanSlow`, `AlwaysExplode`, `Explosion`, `Town`,
`SrcTown`, `ToHit`, `GetHit`, `SoftHit`, `MissileSkill`, `Skill`, `SrcDamage`, `SrcMissDmg`, `Half2HSrc`, `ApplyMastery`,
`Holy`, `KnockBack`, `HitClass`, `DamageRate`, `EType`, `SubMissile1`, `Param1`, `Param2`, `sHitPar1`, `SrvCalc1`;
`tbl:Skills.txt:srvmissile`, `lob`, `decquant`, `srvdofunc`, `SrcDam`, `EType`; `tbl:ItemStatCost.txt` stats 2, 12, 17,
18, 19, 21–25, 31, 48–66, 103, 104, 106, 120–122, 125, 141, 156, 159–161, 166, 180, 315–317, 326–332, 337, 357;
`tbl:States.txt` rows 54, 86, 87; `struct:MissileData+0x10`, `struct:MissileParams+0x00`, `Unit+0x10` (the collide type),
`Unit+0x14`, `Unit+0x20`, `Unit+0xC4` bits 2 and 3, `Unit+0xC8` bit 10, path `+0x50`, `+0x7C`, `+0x84`, `+0x88`, `+0x8C`.

## Dead ends

- Ghidra's decompile of `SkillMissileCreate` dropped the `EDX` missile class and put `useAmmo`'s test on `param_8`
  without the register arguments; the objdump window (`SITE`) is the reading used.
- A first pass took `MissileCreate`'s `0x0064A400` (last hit) for an owner store: it writes only for `LastCollide` rows;
  the owner is `sub_00621CE0_UnitSetOwner`.
- `ExplosionMissile` (`+0x16`) has no server reader by the pattern scan (`LINKS`: one client site, `0x004D2DB1`); the
  server's explosions are the hit functions' (they read `HitSubMissile1`, 22 server sites).

## Open questions

- ~~`0x0064FC60`, the step direction (`dir` of § 4) and its scale.~~ Answered 2026-10-20 in
  [skills/0003 § 10](0003-handlers.md#10-helpers-p12-left-unread) (a 128-entry slope table, `g_PathDirTable`).
- ~~`0x006505C0` (do function 2's "new cell" test) and `0x00620C10` (hit function 22) were not read.~~ Answered
  2026-10-20 in [skills/0003 § 10](0003-handlers.md#10-helpers-p12-left-unread) (path `+0x34 & 8`; the path's target
  unit); `0x00620C10`'s caller is hit function 23, not 22.
- ~~`0x005A43B0` → `0x005A4270(…, 5)` for a monster owner at the end of creation.~~ Answered 2026-10-20 in
  [skills/0003 § 10](0003-handlers.md#10-helpers-p12-left-unread) (unique-mod event slot 5).
- ~~Where the missile pass sits among the unit-type passes of the frame.~~ Answered 2026-10-20 in
  [skills/0003 § 11](0003-handlers.md#11-the-frame-pass) (missiles first).
- ~~`sub_005AD9D0_MissileEndHit` reachability.~~ Settled 2026-10-20 in [skills/0003 § 10](0003-handlers.md#10-helpers-p12-left-unread):
  no call, `jmp`, immediate or 4-byte pointer in the file; unreached.
- [L] The numbered do, hit and damage functions outside tier A (plan 0046). *2026-10-20:* tier A's and the re-seed
  sites `0x005ACDF0`, `0x005AC073` (inside the callback `0x005AC040`), `0x005A9820` and the others of rng/0002 are read
  in [skills/0003 §§ 6, 9](0003-handlers.md#9-re-seed-sites-rng0002--the-other-initialiser-sites).
- ~~`0x00645F00` (the unit's ranged missile and its level).~~ Answered 2026-10-20 in
  [skills/0003 § 10](0003-handlers.md#10-helpers-p12-left-unread).
