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
  damaging result `MISSILE_BuildDamage` (up to seven `RNG_RangeB` draws on the **missile's** seed, every bound and
  mastery read on the missile, an inverted pair swapped before the mastery; § 6), the `pSrvDmgFunc`
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
  [backlog](../../backlog/archive/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md). *2026-10-25:* not reached by run:2026-10-25-skills (no `VelLev` row created; § 11). *2026-10-27:* 22 `spike2` creations at level 1 only, not separating (§ 12). *2026-11-15:* 3 `spike1` creations at level 1 separate it, 3 of 3 against the lead (§ 14).
- [L] src:d2dfg-blizzard: `MaxVel` caps the velocity. **held**
- [L] src:d2dfg-blizzard: `Accel` changes the velocity per frame. **contradicted**
  Detail: `Accel` is added on every **fifth** path step (R3: the counter `+0x8C` reaches 5), the result capped at
  `MaxVel << 8` (acceleration then stops) and floored at 0 (§ 4); 21 stock rows, Nova, Frost Nova and Howl in tier A.
  Phase 2 case C3, [backlog](../../backlog/archive/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md). *2026-10-25:* run:2026-10-25-skills: 278 fifth steps and 60 caps over 1 657
  accelerating steps, every step's velocity as read (§ 11).
- [L] src:d2dfg-blizzard: `Range` is the lifetime in frames. **held**
- [L] src:d2dfg-blizzard: `LevRange` adds to `Range` per caster level beyond 1. **contradicted**
  Detail: `LevRange · lvl + Range`, `lvl` the request's level, with no `− 1` (R2: `movsx [edx+0x98]; imul [esi+0x30]`);
  32 stock rows, none in tier A. Phase 2 case C4,
  [backlog](../../backlog/archive/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md). *2026-10-25:* not reached by run:2026-10-25-skills (Blaze cast 29 times, no `LevRange` row created; § 11). *2026-10-27:* met by run:2026-10-27-skills, 271 `blaze` creations at level 2 (§ 12).
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
  C5, [backlog](../../backlog/archive/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md). *2026-10-25:* run:2026-10-25-skills: 105 missed rolls, each result 2, 7 of them with a pierce left
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
| `0x005AE1F0` | `sub_005AE1F0_MissileMoveCollide` | do function 1: step, range, cells against the collide mask (its return against the end calls in 20 860 frames, § 13) | C |
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
| `0x005A8910` | `sub_005A8910_MissileElemRoll` | one element's `RangeB` with its mastery | C (the drawn fields, § 6; the mastery and the swap I) |
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
  *2026-11-15 (plan 0066 S4a, `lane/n66h`):* r2 reads all 33 values with no `?` and agrees (14 ones, 19 zeros; [items/experiments § Addendum 2026-11-15](../items/experiments.md#addendum-2026-11-15-plan-0066-batches-s4a-and-s4b-new-checks-over-the-kept-economy-and-inventory-logs-and-static-second-sources-lanen66h) `useammo`).
  The six monster sites are 0x005A26AD, 0x005A28BB, 0x005A2CAC, 0x005A4160, 0x005A6DB9 and 0x005A7181, in padded blocks from
  0x005A2620, 0x005A2840, 0x005A2C20, 0x005A3F97, 0x005A6D50 and 0x005A6FF0; the five entries named above do not hold them
  (0x005A35D0 is not an entry), so which monster functions they are stays `[I]`.
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
  *2026-11-16 (plan 0066 review):* the step and the acceleration are `[C]` for `k = 0x400` by emulation, with the ceiling clearing `+0x88` and the floor at 0 (anim/0003 § 11, run:2026-11-16-sweep2-s6e-2); this entry's tag is the earlier reading.
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
- [I] *2026-10-27 (lane/rbd, from the plan 0045 P3 review):* **every bound and the mastery are read on the missile.**
  `MISSILE_BuildDamage`'s first stack argument goes to `ESI` at `0x005A89B9`, the function's only write to `ESI` before
  its `pop esi` at `0x005A8C5E`; both physical reads (`STATS_GetUnitStat(ESI, 22, 0)` at `0x005A89C4`, `(ESI, 21, 0)` at
  `0x005A89D9`) and the six `sub_005A8910_MissileElemRoll` calls (`push esi`, `0x005A8A09` to `0x005A8AD3`) take it.
  `MissileElemRoll` keeps that unit in `EBX` (`0x005A8914`) for the maximum (`0x005A891C`, the stat id in `EAX`), the
  minimum (`0x005A8937`) and the mastery (`0x005A895F`). At `MISSILE_HitUnit`'s call (`0x005AE150`) the argument is
  `EDI`, the missile (`EDX` at the entry, `0x005ADF1C`, not rewritten before the call). The other seven callers (the
  area and chain hit functions at `0x005A9D31`, `0x005A9F47`, `0x005AACB2`, `0x005AC604`, `0x005ACD33`, `0x005ADE7D` and
  `0x005AFB0F`) are unfollowed. (fn:MISSILE_BuildDamage@0x005A89A0, fn:sub_005A8910_MissileElemRoll@0x005A8910,
  fn:MISSILE_HitUnit@0x005ADF10, fn:STATS_GetUnitStat@0x00625480)
- [I] *2026-10-27 (lane/rbd):* **the bounds are tested before the mastery, and an inverted pair is swapped.** The
  maximum is read first; each bound must be `> 0` (`jg` at `0x005A8925` and `0x005A8940`; physical `0x005A89CE`,
  `0x005A89E2`), or the field is 0 and nothing else is read. Then, if the minimum is above the maximum, the two are
  exchanged (`cmp esi, edi; jle; mov esi, edi; mov edi, eax` at `0x005A894B`–`0x005A8951`, `EAX` still holding the
  minimum; physical `0x005A89EB`–`0x005A89F1`). The mastery `MulDiv` follows on the swapped bounds (`0x005A8953`–`0x005A8982`,
  skipped for the id −1 and for a stat of 0), then `RangeB(seed +0x20 of the missile, hi − lo) + lo` (`0x005A8987`–`0x005A8993`),
  which draws nothing for a range ≤ 0 (`0x0045C3E3`). So the draw list above stands with this order: test both, swap,
  mastery, draw. (fn:sub_005A8910_MissileElemRoll@0x005A8910, fn:MISSILE_BuildDamage@0x005A89A0, fn:RNG_RangeB@0x0045C3E0)
- [I] *2026-10-27 (lane/rbd):* `tools/skills.py`'s `bd` reads every bound and mastery from the missile's own stat list
  (the `MH0` line) and now swaps an inverted pair before the mastery (`tools/test_skills.py` `test_bd_swap`: an inverted
  fire pair with mastery 50 passes swapped, and the unswapped reading fails it on the seed and the field). The re-check
  of both runs' 33 logs (`skills.py check 2026-10-25-skills-*.log 2026-10-27-skills-*.log --json rbd/rbd-skills-check.json
  > rbd/rbd-skills-check.txt` from `workspace/logs/skills` under a 4 GB scope; checker `cb0a13ac…`, tests `73224b19…`;
  `rbd/rbd-manifest.sha256` `3c6bdf04…`) gives 4 118 builds, 0 mismatches, and no inverted pair (the swap's counter
  stays absent); the swap is a code reading only, and so is the mastery's unit:
  none of the 54 655 `MH0` lists holds a mastery stat (329–332, 357; `rbd-mastery-scan.txt`, the control pattern
  finding stat 328 in 867), so no logged build separates the missile's mastery from the owner's.
  (run:2026-10-25-skills, run:2026-10-27-skills, fn:MISSILE_BuildDamage@0x005A89A0)

### 7. The function tables

- [I] `g_MissileSrvDoFuncs[n](ECX game, EDX m)` → 1 keep, 2 free; `g_MissileSrvHitFuncs[n](ECX game, EDX m; unit)` → the
  result flags; `g_MissileSrvDmgFuncs[n](ECX game, EDX m; unit, packet)`. Used numbers on stock data: do 34 (1..36; 4 and
  24 unused, 23 and 24 the same function `0x005AF790`), hit 49 (non-null and unused: 5, 6, 11, 23), damage 13 (6 unused).
  What each number does is plan [0046](../../plans/done/0046-skills-function-catalogue.md), tier A's at P1.3.
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
- [I] The remainder: the `VelLev` term (C2: no `spike1`–`spike4` created; *2026-11-15:* met at level 1, § 14) and the `LevRange` term (C4: no `LevRange`
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
  later Blood Moor log, [backlog](../../backlog/archive/2026-10-27-architect-reverser-plan-0045-c2-vellev-by-a-blood-moor.md).
  *2026-11-15:* done, § 14.
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

### 13. Plan 0066 batch S2b: the missile lines re-checked (2026-11-15, `lane/n66f`)

No session: `tools/skills_s2b.py` (`114b0f7d…`) over the 45 kept logs of run:2026-10-25-skills, run:2026-10-27-skills
and run:2026-10-30-skills-catalogue, 0 breaks (`workspace/logs/skills/2026-11-15-s2b-check.txt` `180157a2…`; the record
and the full table: [experiments § run:2026-10-27-skills, addendum 2026-11-15](experiments.md#addendum-2026-11-15-plan-0066-batch-s2b-the-missile-lines-of-the-three-kept-skills-runs-lanen66f)).
What it adds to §§ 4 and 5:

- [C] **Do function 1's return** (§ 4): in 20 860 windowed do-1 frames the frame returns its nested end call's 2 when
  the range is spent (823, frames left 0 after the decrement) or the step fails (65, before it), and 1 otherwise, the
  missile's next frame then at frame + 1; a missile ending at range spent ran exactly the frames left at its creation
  (823 of 823); its 230 unit hits came at frames left below the activate mark. No do-1 frame returned 2 without a hit
  call, so the own-cell and crossed-cell branches stay `[I]`; the log names no do-function address: table entry 1 reaches `sub_005AE1F0` through the thunk `0x005B0BC0` (skills/0004), read statically, and the run corroborates that chain by the frames running `sub_005AE1F0`'s own code order (the step's end before the decrement, the range's after it). `sub_005AE1F0_MissileMoveCollide` and `sub_005B0BC0_MissDo01Thunk` raised to `C` on the frame behaviour (Tier A ruling 2026-11-15, plan 0066).
  (fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0, fn:sub_005B0BC0_MissDo01Thunk@0x005B0BC0, data:g_MissileSrvDoFuncs@0x0073C768, fn:sub_005ADBB0_MissileDoFrame@0x005ADBB0, run:2026-10-27-skills)
- [C] **The `end` call's own branch** (§ 5): a row with no hit function builds nothing, keeps the missile's seed and
  returns 2 in 80 600 of 80 600 end calls; hit-function rows return 2 in 5 610. Unit calls of rows with no hit function
  run the to-hit roll, the build and `MissileApplyAndAc` in that order (18 170). (fn:MISSILE_HitUnit@0x005ADF10,
  run:2026-10-27-skills)
- [C] **The knockback roll** (§ 5): `KnockBack` 0 leaves the missile's seed across `MISSILE_ApplyDamage` (17 608);
  `KnockBack` 33 steps it once and sets packet `+0x04` bit 3 exactly when the roll is below 33 (5 of 5, the rolls 33
  and 48 clear). (fn:MISSILE_ApplyDamage@0x005AD730, run:2026-10-27-skills)
- [C] **The pair order of `MISSILE_BuildDamage`** (§ 6), for (phys, fire), (phys, poison) and (fire, cold): 143
  two-draw builds, each separating its pair, all in the code order. The other pairs never drew together. (fn:MISSILE_BuildDamage@0x005A89A0, run:2026-10-27-skills)
- [I] Left open: the hit function's result as a replacement (1 048 of 1 209 table-predicted builds not made separate it
  from an OR, not from an AND); the type and hostility filters (no refusal of a row with no hit function logged); state
  54 and stat 120. (fn:MISSILE_HitUnit@0x005ADF10)

### 14. Plan 0065 Phase 1: the `VelLev` term separated (case C2, run:2026-11-15-sweep8-single, `lane/n65h`)

- [C] One session (seed 3, Normal, a Sorceress walking the Blood Moor without casting) logged 3 creations of `spike1`
  (Missiles row 7, `Vel` 10, `VelLev` 8) at level 1, by `quillrat1`. `tools/skills.py check` on the log: 0 mismatches
  (`MC.vel`, `MC.range`, `MC.left`, `MC.owner`, `MC.seed` 3 each); `sweep8_check.py c2`: 3 of 3 separating, 0
  mismatches. The velocity is the one § 2 reads, `tdiv(((((8 * lvl) / 8) + 10) << 8) * 75, 100)` = 2112 at level 1; the
  lead's `VelLev * (lvl - 1) + Vel` gives 1920. At level 1 the term `(8 · lvl) / 8` is 1 under any order of the
  product and the division, so the run fixes the value of the term, not how it grows with `lvl` or how it rounds. This turns § 12's `VelLev` remainder from [I] to [C] for level 1; levels
  above 1 of `spike1` stay unobserved. (fn:sub_0059FA30_MissileCreate@0x0059FA30, tbl:Missiles.txt:VelLev, run:2026-11-15-sweep8-single)

### 15. Plan 0066 batch S2c part 1: second-tool table, call and data scans (2026-11-16, `lane/n66q`)

No session, no Ghidra. `tools/skills_s2c.py` (sections `tables s16 entries data consts calls`) reads every claimed
instruction with objdump and with r2, counts references three ways (raw rel32/abs32 bytes, objdump, r2), walks call
arguments twice, and reads each table cell from the `.txt` and from the `.bin` (through `tools/excel_bin.py`). Kept
output: `workspace/logs/n66q/s2c/check-s2c-p1.txt` (`S2c total bad=0`), under `manifest-s2c-p1.sha256` in that
directory. The rows, and what each raise covers, are in the plan 0066 inventory files `skills-*.md` (Route cells
"S2c 2026-11-16 (part 1)"). The statements below are the ones that rest on this run.

- [C] **Function tables.** The start table is bounded by `cmp ax, 0x5B` (0x0056F75D), and the do table by
  `cmp ax, 0xBF` (0x0056F911, 0x0056D7E8) and by `[0x006E1274]` = 0xBF (0x005D542C). The stat-event table is bounded
  by `cmp eax, 0x31; ja` (0x0056E746), and its non-null slots are exactly ids 1..31. The missile do, hit and damage
  counts are 53, 71 and 31 (0x0073C71C, 0x0073C83C, 0x0073C95C), each compared at its readers (0x005ADBFE; 0x005ADA19,
  0x005AE0A7, 0x005AE112, 0x005B02DB; 0x005AE164).
- [C] **The signed test.** Each hit, damage and do dispatch loads its record word (`+0xE`, `+0x10`, `+0xC`), then runs
  `test ax, ax; jle`, `movsx` and the count compare (0x005ADA0D, 0x005AE09B, 0x005AE106, 0x005B02CF, 0x005AE158,
  0x005ADBEE). Row 568 is the only Missiles row with a word above 0x7FFF in the three columns, so its hit function
  (64 948) never runs.
- [C] **Entries.** The 53 distinct hit entries all return with `ret 4`, and the 14 damage entries with `ret 8`.
  Do-table entry 1 is `jmp 0x005AE1F0` (0x005B0BC0). The 9a entries end in mdo 1 and return its result (mdo 18 does
  so after the stack-cookie check, 0x005AF521). mdo 20 and mdo 30 return 1 after mdo 1, mdo 32 ends in mdo 7
  (0x005B047F), and mdo 34 ends in mdo 3. Entries 23 and 24 are both 0x005AF790. Entry 37 (0x005B0AA0) is non-null,
  and no row names it.
- [C] **Collide types and directions.** `g_MissileCollideTypes` holds 9 × {filter, mask} from 0x0073C720 up to the do
  table. Types 0 and 4 are {0, 0}, and type 6 is {0, 0x0004}. Missiles.txt has 301, 0 and 24 rows of these three types.
  `PathDirection` indexes `g_PathDirTable` at (minor·0x7F)/major with a 12-byte stride (0x0064FCD3–0x0064FCE7), which
  gives 128 entries. Every point of `g_Circle64X/Y` equals trunc(30·cos, 30·sin) of i/64 turns, and the points are read
  at `i mod 64` (0x005AF106).
- [C] **Constants.** The delay state 121 is written by `SKILLS_SetDelayState` (three state calls) and read by
  `SKILLS_DelayOk` (0x00647908). The unit event is `UnitQueueEvent(12, …)` (0x0056F010). State 114 is used by PayCost,
  ManaOk, BloodManaPay and `sub_005D2B20_StateDo147Attached`. Both periodic sites clamp the calc to at least 5
  (0x0056CDFE, 0x0056CECE). The progressive charge is `min(old + 1, 3)` (0x005D3414–0x005D341C).
- [C] **Callers.** `SKILLS_SrvDo` has 8 callers. 7 pass effect 0, and `ITEMSKILL_Cast` passes its own `[ebp+0x2c]`
  (0x005FDC1E). Of the 10 item-cast calls below it, only handler 20's path with ItemTgtDo clear passes 1 (0x005C054E,
  after the test at 0x005C0524). `MonAttackStats` has 6 callers, `SkillWeaponWear` 1 (0x005DAC99),
  `SKILLS_GetMasteryBonus` 13, `MissileCreateAt` 17, `0x005C2FF0` 2 (do 31 and do 58), and `MissileEndHit` none, not
  even as abs32 data. `SKILLS_CanUse` has 16 callers, none of them in the monster mode path's functions. The four
  start refusals call `PlayerModeCmd(0, 5, 0, 0, 1)`, and only behind a type-0 test. `StartUsedSkill` calls
  `SkillAllyTest` only when TargetAlly is clear. It passes the same skill, and the test returns 0 when that bit is
  clear (0x0056FBB2–0x0056FBC4, 0x00554D62–0x00554DD0). `SkillMissileCreate` sets flag `0x1000` and `+0x48` only behind
  `cmp [owner], 1` (0x0056ED84–0x0056ED9E).
- [C] **Data.** Skills: 48 rows have a srvmissile and no srvdofunc, and 307 and 325 name only srvmissilea..c. The
  periodic rows are 57 and 277. The startmana rows are 41, 230 and 266, which are also the only repeat rows.
  ItemStatCost registers handlers 6–10, 13–21 and 28–31, Skills registers 1–5 and 22–27, and no row registers 11 or 12.
  `STATES_Load`'s list at g_DataTables+0x17C is built with bit 16 (0x00618C58), and the States rows with `disguise` are
  63, 93, 119, 139, 140, 176 and 177. The O8, P4 and Q6 joins of skills/catalogue hold.
- **Not raised here** (the remainders are in the rows): the entries' write sets; the conditions that return 2; any class
  test in the paladin batch; the defender's path to `SKILLS_CanUse` through the durability loss, where the scan cannot
  tell which unit the path runs for; the synergy calcs; the handler's unit for a draw.
- **Contradicted in part (missiles row 2):** no shrine function calls `MissileCreateAt`, and the row's list leaves out
  the two monster-AI callers. The refinements are in backlog
  [`2026-11-16-reverser-spec-writer-plan-0066-s2c-refinements`](../../backlog/2026-11-16-reverser-spec-writer-plan-0066-s2c-refinements.md).

### 16. Plan 0066 batch S2c part 2: bit 6, the flag bits, packets and the creators (2026-11-16, `lane/n66q`)

No session, no Ghidra. `tools/skills_s2c.py` gained the sections `bits` and `more` (revision `28ff8ac9…`; the part-1
sections are unchanged, so `check-s2c-p1.txt` stays tied to `13cda266…`). Kept output:
`workspace/logs/n66q/s2c/check-s2c-p2.txt` (`S2c total bad=0`), under `manifest-s2c-p2.sha256` in that directory. The
rows are the plan 0066 inventory files' Route cells "S2c 2026-11-16 (part 2)". The checks' labels are named below.

- [C] **Bit 6 of `Unit+0xC4`.** 124 `or …, 0x40` and 17 `and …, 0xFFFFFFBF`, objdump and r2 alike, 44 sets and 7 clears in
  client-range functions (D56). `SKILLS_SrvDo` sets it once its missile row exists (0x0056F97D–0x0056F98A) and
  `MonAiUseSkill` before `MonSetMode` (0x005DEB08). The server readers that skip the do when it is set are
  `PlrModeSkillFrame` (0x005804C2–0x005804E2) and `MonSeqFrame` (0x005A86FD–0x005A871A), each on a code 1 or 2.
- [C] **The monster modes (D57).** `g_MonModeRecords` (16-byte records, read by python and r2) gives
  `MonModeStartSkill` as the start of modes 4, 5, 7, 8, 9 and 16–20, all with `MonAttackFrame` as frame function. That
  start's direct-call closure (703 functions, 536 indirect calls unfollowed) reaches none of the 17 clears. With every
  start-table entry added as a root it reaches one, do 48's (0x005D68F5) through start 26, Blade Fury. `MonAttackFrame`
  runs the do when the skill's flag bit 0 is clear or the move step does not return 2 (0x005A7694–0x005A76E3), with no
  bit-6 test. Its one bit-6 test is behind `mode = 14` (0x005A76C9–0x005A76DD).
- [C] **Mode 14 is different (contradicts dispatch § E2 and its reimplementation note for that mode).** Its record's
  start, 0x005A7870 (`sub_005A7870_MonModeStartSeq`, new, `I`), calls `SUNIT_SetMode(14)`, **clears bit 6**
  (0x005A7884) and tail-jumps to `SKILLS_StartUsedSkill` (0x005A7891). Its frame function `MonSeqFrame` runs the do
  when `+0x4E` = 4 without a test, else when bit 6 is clear on code 1 or 2. This is the store that S2a's 566 mode-14
  starts with the bit clear were missing (backlog `2026-11-10-reverser-reverser-skills-mode-14-start-bit-6`, closed
  by this section).
- [C] **Smite (C58).** Do 150's body has no `+0xC4` operand. Its direct-call closure (2 085 functions, 622 indirect calls
  unfollowed) reaches one set site, `SKILLS_SrvDo` 0x0056F98A, by `COMBAT_DeliverQueued` → `COMBAT_DurabilityLoss` →
  `ITEMS_DurabilityLossRoll` → `HandsRefresh` → `PlayerSetSkill` → `AuraSelect` → `SKILLS_SrvDo`. Which unit that
  path sets the bit on is not followed.
- [C] **Do 10 and mdo 7 (C14).** Do 10 calls `MISSDATA_SetSeedLow(missile, target ? 1 : 2)` with `esi` the
  `UNIT_GetTargetUnit` result (0x005DB71B–0x005DB7FE). `SetSeedLow` and `GetSeedLow` store and load the same
  `MissileData+0x28` (0x0064A729, 0x0064A746), and mdo 7 tests its bit 0 (0x005AE806). `SetSeedLow` has 93 calls, so
  the word has other writers.
- [C] **The Skills flag bits (D76, D95).** Four mask-form tests of `+0x05` bit 3 (`repeat`, mask 0x006CE274): a client
  site, `MissileDoFrame` on a Missiles row (0x005ADBD9–0x005ADC43), and `STATLIST_CacheAdd/Write`, neither of which
  makes a Skills row. Fourteen tests of bit 1 (`Kick`, 0x006CE26C), nine of them server-range. Of those, only
  `GetPhysMin` (0x00647BF5) and `GetPhysMax` (0x00647D38) test a Skills row. The others test the row returned by
  `MonStats2Rec`, `ITEMSTATCOST_GetRecord`, `MissileRec` or a 0x144 or 0x134 stride, the call or stride just before
  each. The 15 immediate-form tests of either bit lie in no function that makes a Skills row. Kick rows are 1, 255, 270
  and 275, in both the .txt and the .bin. `SkillKickDamage` has one call (0x00647D41), `SkillKickPhysDamage` three and
  `DragonTalonHit` two. Of the 18 calls of each `GetPhysMin/Max`, 15 pass a variable skill id, not counting
  `SkillKickPhysDamage`'s own call. Start 2 and do 2's closure (2 062 functions, 622 indirect) reaches four of their
  sites: `SkillDamagePair` through `COMBAT_GetHit`'s monster stats, and `MissileDamageBlock` through the durability path.
- [C] **The conversion writers (D88).** 15 byte stores follow a read of the Skills row's `+0x1DC`. Each is to
  `[ebp−k]`, with `[ebp−(k+0x65)]` referenced near it. The function holding 0x005D8BED lies in
  `SkillDo75GrimWard`'s symbol range but after its `ret` (0x005D8B0D); this is the spec's 0x005D8B10.
- [C] **The skill packets (D1, D2, D25).** `g_SrvPacketTable` 0x05–0x11 (python and r2): 0x05/0x0C location, 0x06/0x0D
  unit with walk 1, 0x07/0x0E unit with walk 0, left (`GetLeftSkill`, SkillList+0x08) below 0x0B, right (+0x0C) above
  (data:g_SrvPacketTable@0x006E0D18, 0x006201B9, 0x00643953).
  0x08–0x0A and 0x0F–0x11 re-read the packet and call the matching direct handler. The direct handlers set base stat
  328 + 1 before calling `SkillAtXY` or `SkillAtUnit`. 0x0B has no call and no store. The forms are 5 bytes (x +1, y
  +3) and 9 bytes (type +1 below 6, guid +5).
- [C] **Other calls.** `SKILLS_SrvStart` has 4 callers, and only `ITEMSKILL_Cast` passes noCost 1 (D50).
  `PreventHealHook` tests attacker type 0, defender type 1, the attacker's stat 117 and the defender's class outside
  0x2C0–0x2C5 before `STATE_ApplyTimed` (0x0057D81A–0x0057D891) (D137). Smite's monster branch passes mode 5 and keeps
  the test's word (0x005CEBB6–0x005CEBEB) (C57). Dragon Talon's and Psychic Hammer's two stat-12 reads both push the
  target (C74, C75). The rings of prg 37 and 143 step `esi` by `4·calc` up to 0x100 with no test of the step, so a
  calc of 0 never ends (C108). `PathPlanSpiral` reads only the path and the sine table (M5).
- [C] **Missiles (M23, M25, M48, M70, M94, R24).** The `useAmmo` argument is 1 at 14 of the 33 line and lob call sites
  and 0 at 19. Six of the pushes are shared before a lob/line branch. Magicarrow takes the 0 site, item type 38 takes
  the lob, and `cmp [owner], 0` gates the use. `MissileCreate` has 97 calls, none from an `ITEM`/`INV` function and
  three from shrine functions. The `0x40` marks are written by `MissileCreate` (a `Collision` row's path mark mask,
  0x0059FD54–0x0059FD64), mdo 3 and mdo 5, and cleared by `HitUnit` (0x005AE1B1–0x005AE1CB) and mdo 31 (0x005B0325).
  Collide type 7 is the only type whose mask holds 0x40. No server-range word read at `+0x16` is in a function that
  makes a Missiles row. `MISSILE_BuildDamage` reads all 23 of its stats from the missile; its closure has 16 functions,
  no indirect call and no item or owner function. `MissileCritRoll`'s only references are two calls in
  `MissileDamageBlock`, which `COMBAT_BuildDamage`'s closure does not reach.
- **Remainder `[I]` of the two absence claims (architect check).** "No server reader" of `repeat` (dispatch 76, mask
  0x006CE274) and of
  `ExplosionMissile` (missiles 70, `check-s2c-p2.txt` M70, 0x004AD71C) rests on the function-type criterion above; a row passed as an argument to a function
  that makes none is not excluded, so both rows are raised in part.
- **Not settled:** dispatch 41 (the client's request sender is not located) and missiles 15 (`MissileCreate` reloads
  its block register and holds the flags in registers, which needs a data-flow read).
- **Contradicted in part:** dispatch 57 and 193 (mode 14, above), and missiles 23's "five monster functions": the six
  sites lie in six recursive-descent bodies (0x005A2620, 0x005A2840, 0x005A2C20, 0x005A3F30, 0x005A6D50, 0x005A6FF0).
  The rewordings are in the S2c refinements backlog.

### 17. Plan 0066 batch S2ae part 1: leaf functions emulated, earlier runs re-read, the routes (2026-11-16, `lane/n66sa`)

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (the skills dispatch and missiles
emulation batch), part 1. The emulated claims are maps of the named function on declared inputs (ADR-0015), compared with
`tools/skills_s2ae_emu.py`'s model over the kept run ([run:2026-11-16-sweep2-s2ae](experiments.md#run2026-11-16-sweep2-s2ae),
`check.txt`, 14 100 cases, 0 mismatches); brackets give separating control counts (`sep`, each with `passed` 0) and the
`ROWS` tallies. What each offset or column means keeps its own tag (ADR-0015 (3)). "d" rows are skills/dispatch's
inventory, "m" rows skills/missiles'.

- [C] *m35 (D4's clamp at 0).* `sub_006502D0_PathVelocityStep` (EAX path, ECX multiplier; `ret`): when `+0x88` (the
  acceleration) is non-zero, `+0x8C` is incremented and, when it is then **above 4** (signed), `+0x7C += +0x88`; if the
  sum is above `+0x84` it takes `+0x84` and `+0x88 ← 0`, **else** if it is below 0 it takes 0; `+0x8C ← 0`. Then
  `s = (+0x7C · m) >> 6` with `m` the multiplier (`0x400` when `m < 1`), and `+0x72 = (+0x6A · s) >> 12`,
  `+0x76 = (+0x6E · s) >> 12` (32-bit products, arithmetic shifts) [`v_lt0` 694, 523 cases clamped at 0;
  `v_gt_max` 880, `v_gt_max~` 119; `count_gt4` 1 201, `count_gt4~` 69, 160 cases entering with a count above 4;
  `mult_lt1` 536, `mult_lt1~` 124; `accel_nz` 1 500]. **Refinements:** the clamp at 0 is the `else` of the cap, so a
  sum above a negative maximum keeps that maximum [`spec_two_ifs`, D4's two separate tests, fails 111]; the step is
  taken at a count above 4, not equal to 5; the function **writes** the step to `+0x72`/`+0x76`, it does not add to the
  position (the move is its caller's). (fn:sub_006502D0_PathVelocityStep@0x006502D0, 0x006502D0–0x0065034C,
  run:2026-11-16-sweep2-s2ae)
- [C] *m38, m98 (D4's direction).* `sub_0064FC60_PathDirection` (ECX vector out, EDX index out; x1, y1, x2, y2;
  `ret 0x10`): with `dx`, `dy` the unsigned spans (larger minus smaller coordinate), the major axis is y when
  `dx ≤ dy` (signed), `i = (minor · 0x7F) ÷ major` (signed, truncating; 0 when `major` is 0) indexes the 12-byte rows of
  `g_PathDirTable` (0x006EB7E0, `.rdata`); the first two words are the vector, swapped when x is the major axis, whose
  third word `t` becomes `(−t − 1) & 0xF`; `y2 < y1` (unsigned) negates the y component and maps `u → (−u − 1) & 0x1F`;
  `x2 < x1` negates the x component and gives the index `(u + 8) & 0x3F`, else `((−u − 1) & 0x3F) + 8 & 0x3F`
  [`x2_lt_x1` 3 000, `y2_ge_y1` 1 967, `y2_lt_y1` 3 000, `dx_le_dy` 3 000, `dx_le_dy~` 1 405, `major0` 2 160; spans up
  to 2²³]. The step direction is a table lookup on image data, no arithmetic beyond the one division.
  (fn:sub_0064FC60_PathDirection@0x0064FC60, data:g_PathDirTable@0x006EB7E0, run:2026-11-16-sweep2-s2ae)
- [C] *m60–62, m65, m66 (F1's pair steps).* `sub_005A8910_MissileElemRoll` (EAX maximum stat; unit, minimum stat,
  mastery stat; `ret 0xC`): `hi = STATS_GetUnitStat(u, EAX, 0)`, 0 when `hi < 1`; `lo = STATS_GetUnitStat(u, min, 0)`,
  0 when `lo ≤ 0`; a pair with `lo > hi` is swapped; when the mastery id is not −1 and its stat on the same unit is
  non-zero, `lo += MulDiv(lo, k, 100)` and `hi += MulDiv(hi, k, 100)` on the swapped bounds; then
  `RangeB(u.seed, hi − lo) + lo`, no step when `hi − lo < 1` [`inverted` 1 363, 1 174 inverted pairs, 563 of them with
  a mastery; `spec_no_swap` 1 172; `m_set` 741, `m_nz` 741, 752 cases with a non-zero mastery; `hi_lt1` 1 877,
  `lo_gt0` 1 893, `lo_gt0~` 254, `n_gt0` 1 542, `n_gt0~` 179]. A mastery stat of 0 adds nothing. That the unit is the
  missile is the callers' reading (§ 6, `lane/rbd`). (fn:sub_005A8910_MissileElemRoll@0x005A8910,
  0x005A894B–0x005A8993, run:2026-11-16-sweep2-s2ae)
- [C] *d38 (C5, `restrict`).* `SKILLS_RestrictOk` (EAX entry, EBX unit): a null unit, entry or record (`entry+0`)
  refuses; with the record's byte `+0x228` = 0 it passes only when `0x0063A510` finds no restricted state; 1 passes;
  2 refuses unless a restricted state is set, then passes on the first of the three s16 ids at `+0x22A` the unit has
  (`UNIT_HasState`), a negative id ending the list; any other value passes [`rv0` 980, `rv1` 633, `rv2` 862,
  `restricted` 559, `has` 205, `st_neg` 102, `rec_nz` 846]. `0x0063A510` → `0x0063A130`: any common bit between the
  unit's state bits (only when its list has bit 31 of `+0x10`; no type test) and the mask words at DataTables
  `+0x110`, over `(states + 31) ÷ 32` words. **Refinement:** a null record refuses (C5's "any other value passes" is
  for a record). The mask's meaning (the restricted states) is the table's own tag. (fn:SKILLS_RestrictOk@0x00644060,
  0x0063A510, 0x0063A130, run:2026-11-16-sweep2-s2ae)
- [C] *d39 (C6, the map).* `SKILLS_StartManaOk` (ESI unit, EDI entry) returns 0 only for a non-null type-0 unit whose
  record's s16 `+0x184` is above 0, whose stat 8 is below `+0x184 · 256` (**signed** compare), and which lacks state
  12; else 1 [`m_lt` 203, `m_lt~` 17, `sm_gt0` 219, `st12` 235, `player` 288; `spec_unsigned` fails 12]. Not covered:
  which stock rows have `startmana` and when the game calls the check (the first frame of a channelled skill).
  (fn:SKILLS_StartManaOk@0x006440F0, run:2026-11-16-sweep2-s2ae)
- [C] *d69 (G2, the gate).* `SKILLS_DelayOk` (EDI unit; entry; `ret 4`) returns 1 for a null unit, a type other than
  0, a unit without state 121, or a null entry or record; otherwise its first call is `SKILLS_GetSkillLevel(unit,
  entry, 1)` from 0x00647931 (return address 0x00647936 checked) [`st121` 331, `entry` 277, `player` 271, `unit` 234;
  157 boundary cases]. Not covered (ADR-0021): the `SKILLS_EvalCalc` of the delay calc and its `< 1` test.
  (fn:SKILLS_DelayOk@0x006478F0, run:2026-11-16-sweep2-s2ae)
- [C] *d91 (I4, the kick maximum).* `sub_00644C20_SkillKickDamage` (ESI unit; flag; `ret 4`): `x = stat 2 + stat 0 −
  20` for a type-0 unit, else `3 · stat 12` (a null unit gives 0), floored at 1; flag non-zero → `(x ÷ 4) << 8`, flag 0
  → `(x ÷ 3) << 8` [`flag` 536, `player` 843, `x_lt1` 833]. `SKILLS_GetPhysMax` with the `Kick` bit loads `ESI` from
  its first argument, pushes 0 and tail-returns the call's `EAX` (0x00647D3D–0x00647D49; objdump in `static.txt`
  `physmax-kick`, and the Ghidra decompile of run:2026-10-20-cat-emu-9d), so the kick maximum is `(max(x, 1) ÷ 3) << 8`.
  (fn:sub_00644C20_SkillKickDamage@0x00644C20, fn:SKILLS_GetPhysMax@0x00647D00, run:2026-11-16-sweep2-s2ae)
- [C] *d149 (L5, the level gate and the class-364 path).* `sub_005C4430_SummonClassRoll` (ECX caster, EDX summon;
  id, lvl): a null summon or a class other than 363 and 364 returns with no step. Class 363 →
  `sub_005C4300_SkeletonParam1Roll`: at `lvl > 2` (signed) one inline step of the caster's seed and
  `flag = (low mod 100) < Skills[id] +0x148` (signed; 0 for an id out of the table), at `lvl ≤ 2` no step and flag 0;
  then `sub_005C4180_SummonSetDataBytes(EAX 1; flag, 0)`. Class 364 → `0x005C43D0` → `SummonSetDataBytes(EAX 1; 0, 1)`,
  which steps the caster's seed once (`EDI`), writes `low & 3` to MonsterData `+0x0F` and `+0x10` and calls
  `0x005B0D70` with `ECX` = the dword at MonsterData `+0x28`, `EDX` = 1 and the stack arguments 0, −666 (return
  address 0x005C42CE checked) [`c363` 1 274, `c364` 990, `lvl_gt2` 422, `lvl_gt2~` 44, `roll_lt` 165, `b_nz` 592; ROWS
  363 at `lvl ≤ 2` 194, above 228, 364 408]. With a type-1 summon and MonsterData, `SummonSetDataBytes` first copies
  row `EAX` (index clamped at 10) of the 9-byte rows at 0x00741940 to MonsterData `+4`, `+5`, `+0xC`, `+0xD`, `+6`,
  `+7`, `+8`, `+0x0B` only when its first argument is non-zero, and `+9` when it does not draw. The cases keep the
  caster's state 97 off (its stat-0x15F index path is not run). (fn:sub_005C4430_SummonClassRoll@0x005C4430,
  fn:sub_005C4300_SkeletonParam1Roll@0x005C4300, fn:sub_005C4180_SummonSetDataBytes@0x005C4180,
  run:2026-11-16-sweep2-s2ae)
- [C] *Earlier kept runs, re-read (no new run).* **m28:** combat/0001 § 22 emulated `MissileCritRoll`'s second and
  third steps (outcomes by steps 1/2/3: 1 216 / 1 475 / 309; run:2026-11-16-sweep2-s5fe), scoped to a unit with no
  used skill; the combat cluster's Tier A review takes it as this row's evidence. **m29, the call:** the same § 22's
  call site 0x0064BD15 (ESI = the block's third argument, weapon 0, only when it is non-null): no mastery step. That
  the branch is `SrcMissDmg`'s and the argument the source missile stays `[I]` with C1's block (part 2). **d138:**
  run:2026-11-16-sweep2-s5e's `phh` family ran `sub_0057D810_PreventHealHook` with attackers of types 0, 1, 2 and
  defender classes 703–710 [`att_player` 255, `cls_lt2c0` 217, `cls_gt2c5` 113]. **d122:**
  run:2026-11-16-sweep2-s5e2's `frz` family: handler 14 draws one inline step whenever stat 134 is above 0 (and its
  `ow` and `cb` families handlers 15 and 16; combat/0001 § 20). **m78:** run:2026-10-20-cat-emu-9a `scatter` (do 8,
  10, 17) and run:2026-10-20-cat-emu-9b `scatter25` (do 25): `0x005A9820` re-seeds the missile to `(SubX + elapsed,
  666)` and draws two `RangeB` (skills/0004 § 7). **m79, m80:** 9b `reseed9b`: do 28 re-seeds to `(+0x28, 666)`, draws
  two `Range(2r + 1)` and stores the low word in `+0x28` before its creation; do 34 re-seeds to `(SubX, 666)` and steps
  once (skills/0005 §§ 7, 8; the table's "path X" is `SubX`). **m81, in part:** do 35 re-seeds to `(+0x28, 666)` and
  steps once before `PathPlan`; its `+0x28 ← low` comes after that boundary (skills/0005 § 9) and stays `[I]`.
  (fn:sub_0064A850_MissileCritRoll@0x0064A850, fn:sub_0057D810_PreventHealHook@0x0057D810,
  fn:STATEVENT_Freeze@0x005BFC60, fn:sub_005A9820_MissSubNearReseed@0x005A9820, run:2026-11-16-sweep2-s5fe,
  run:2026-11-16-sweep2-s5e, run:2026-11-16-sweep2-s5e2, run:2026-10-20-cat-emu-9a, run:2026-10-20-cat-emu-9b)
- [I] *Routes (ruling R2, ADR-0021, ADR-0029; `routes.txt`, depth 4).* **m49 → b (H2a):** do 2 reaches its creation
  through `0x005A9720` (0x005AE469) → `MissileCreate` → `sub_00555230_SUnitCreate` (0x0059FC75), whose pool allocation
  0x0040B430 sits at 0x005553BE; do 1 follows at 0x005AE475, after the creation, so no emulation without a declared
  return reaches it. The other S2ae rows are left for part 2 (the plan's resume note).
  (fn:sub_005AE400_MissDo02SubMissile@0x005AE400, fn:sub_0059FA30_MissileCreate@0x0059FA30)

### 18. Plan 0066 batch S2ae part 2: the mana checks and the collide filters emulated (2026-11-16, `lane/n66sa`)

Part 2 of the batch. The claims are maps of the named functions on declared inputs (ADR-0015), compared with
`tools/skills_s2ae2_emu.py`'s model over the kept run
([run:2026-11-16-sweep2-s2ae2](experiments.md#run2026-11-16-sweep2-s2ae2), `check.txt`, 11 000 cases, 0 mismatches,
0 stops, 0 unaccounted reads or writes; no observed boundary, no import). Brackets give separating control counts
(`sep`, each with `passed` 0). What each offset means (lvlmana, CollideFriend, the alignment stat) keeps its own tag
(ADR-0015 (3)); every callee named runs whole.

- [C] *d36, d37 (C4).* `SKILLS_ManaOk` (EAX entry, ECX unit; `ret`): an entry whose `+0x34` is not −1 returns
  `+0x38 > 0` (signed) [`item` 1 250, `chg_gt0` 656, `chg_gt0~` 119]. Else, with a unit, `lvl = +0x28 +
  SkillLevelBonus(unit, entry)`, set to 0 when `≤ 0` and to `ExpMaxLevel(0)` when not below it (declared maxima 0, 1,
  20, 50, 99) [`lvl_le0` 222, `lvl_lt_max` 371, `unit` 232]; with no unit `lvl = 0`; then `lvl − 1`, floored at 0
  [`lvl_lt0` 354], and `cost = (s16 +0x18C · lvl + s16 +0x18A) << (+0x188 & 31)` (32-bit), F1's `max(lvl − 1, 0)`
  [`spec_no_minus1`, the level without the `− 1`, fails 428]. Under state 114 the answer is `stat 6 ≥ cost` (signed)
  [`st114` 630, `life_ge` 452]; else a record whose word `+0x2E` is 0x74 (116) passes when `Unit+0xC8` bit 3 is set
  (`0x0063A400`) [`sdf116` 248, `c8b3` 165]; else `stat 8 ≥ cost` (signed) [`mana_ge` 1 181, `mana_ge~` 309]: a cost
  equal to the mana passes. The record bytes are seeded random and the model has no `minmana` floor.
  (fn:SKILLS_ManaOk@0x00647540, 0x00647540–0x00647633, run:2026-11-16-sweep2-s2ae2)
- [C] *The level bonus both checks use.* `sub_00644180_SkillLevelBonus(entry)` (ESI unit): 0 for a null entry or
  record, or a record whose s16 `+0x00` lies outside the Skills count [`b_sid_ok` 328]; else the entry's `+0x2C`, + 2
  under state 134 (`ShrineSkillBonus`) [`b_shrine` 63], + stat 127; for a player whose class equals the record's signed
  byte `+0x0C` [`b_player` 33, `b_ownclass` 21]: + stat 83 at layer class, + stat 188 at layer `t + class · 8 − 1` when
  the signed byte `t` at `+2` of `SkillDescRec(id)` is non-zero [`b_tab` 3], + stat 97 at layer id capped at 3
  [`b_cap3` 15]; a player of another class adds stat 97 uncapped; a non-player adds stat 97 capped at 3 only when the
  entry's `+0x28` is above 0 (signed) [`b_cap3n` 25, `b_base_gt0` 11]; then + stat 126 at layer byte `+0x1DC` when it
  is non-zero [`b_elem` 17], and + stat 107 at layer id. Each is `STATS_GetUnitStat` (the layer's low 16 bits).
  (fn:sub_00644180_SkillLevelBonus@0x00644180, fn:sub_00644150_ShrineSkillBonus@0x00644150, run:2026-11-16-sweep2-s2ae2)
- [C] *d49 (D3).* `SKILLS_SrvManaCheck` (ECX unit; `ret`): a null unit or a non-player returns 1 [`unit` 442,
  `player` 624]; the entry is the skill list's `+0x10` (`UNIT_GetUsedSkill`), and none returns 0 [`used` 564]; an item
  entry returns `+0x38 > 0` [`item` 388]; a null record returns 0 [`rec` 421]; else
  `lvl = max(SKILLS_GetSkillLevel(unit, entry, 1) − 1, 0)` (the same bonus and clamp, run whole), the same cost, the
  `srvdofunc` 116 and bit-3 pass [`sdf116` 86, `c8b3` 67], and `stat 8 ≥ cost` [`mana_ge` 446]; **no** state-114
  branch [`spec_st114`, C4's branch put in, fails 56]. (fn:SKILLS_SrvManaCheck@0x0056C160, 0x0056C160–0x0056C206,
  fn:SKILLS_GetSkillLevel@0x006442A0, run:2026-11-16-sweep2-s2ae2)
- [C] *m47 (D6).* `sub_005A8730_CollideUnitFilter` (ESI candidate, EDI owner, EBX the Missiles record; game, missile;
  `ret 8`) returns 0 for a null candidate, or one whose `+0xC4` lacks bit 3 or bit 2 [`f_bit3` 1 555, `f_bit2` 1 568];
  for a record with byte `+0x188` non-zero, a candidate in state 86 [`f_nexthit` 300, `f_st86` 744]; a candidate
  `MISSDATA_IsLastHit` names [`f_lasthit` 1 431, `lh_match` 151]; and, **when the owner is not null** [`f_owner` 365],
  a candidate that `sub_00554200_UnitsHostile(owner, candidate)` calls not hostile while byte `+0x187` is 0
  [`f_hostile` 688, `f_friend` 650]; else 1. **Refinements:** with no owner the friend test is skipped; an owner that is
  the candidate counts as not hostile [`h_same` 383]. `MISSDATA_IsLastHit(missile, candidate)` needs a type-3 missile
  whose Missiles row has bit 0 of `+4`, missile data at `+0x14`, and data `+0x18`/`+0x1C` equal to the candidate's
  type and `+0x0C`. `UnitsHostile` (on these inputs: monster owners whose `MonsterOwner` chain ends in 0, no type-3
  owner with `+0xC8` bit 10) gives, for two players, `PlayerPairFlags(owner, candidate, 8)`: the `+4` word of the first
  node of the owner's player-data `+0x38` list (next at `+0x10`) whose `+0` is the candidate's `+0x0C`, masked with 8,
  or 0 [`p_id` 16, `spec_any_flag` (any non-zero word) 5]; otherwise hostile unless `AlignSame02(owner, candidate)`
  [`h_align` 608], which is 1 when both `UnitAlignGet` values are 0 or both 2. `UnitAlignGet` is 0 with no stat list,
  2 for a type above 1 (unsigned), else stat 172 of the first list in the `+0x3C`, then `+0x40` chain (next at `+0x2C`)
  whose `+0x14` is 0x69, and 0 when there is none or the list's flag bit 31 is clear.
  (fn:sub_005A8730_CollideUnitFilter@0x005A8730, fn:MISSDATA_IsLastHit@0x0064A470,
  fn:sub_00554200_UnitsHostile@0x00554200, fn:sub_0055B300_PlayerPairFlags@0x0055B300,
  fn:sub_00650D70_AlignSame02@0x00650D70, fn:sub_006259B0_UnitAlignGet@0x006259B0, run:2026-11-16-sweep2-s2ae2)
- [C] *m40, m41, m42, m46, m45 (the collide-type filters).* With ECX the candidate and EDX a context of four words
  (game, missile, owner, record), each returns 0 for a null context or record [`w_ctx` 134, 88, 219] or a null
  candidate, then: `sub_005A87F0_CollidePlayerOrAlly` passes a type-0 candidate, and a type-1 candidate whose
  `UnitAlignGet` is 2, to the filter, any other 0 [`w_player` 431, `w_mon` 191, `w_align2` 147];
  `sub_005A87B0_CollideMonster` a type-1 candidate only [`w_mon` 337]; `sub_005A8850_CollideUnit` a signed type 0 or 1
  [`w_ge0` 271, `w_ge0~` 105, `w_le1` 415, `w_le1~` 96]; each returns the filter's answer as 0 or 1.
  `sub_005A8890_CollideMissile` (ECX only) returns 1 for a type-3 unit whose signed class lies in the Missiles count
  and whose row has bit 4 of `+4` [`m_type3` 246, `m_ge0` 149, `m_lt_n` 179, `m_candestroy` 195]. The type table's
  filters and masks (`0x0084`, `0x0104`, `0x0184`, `0x0185`, `0x0040`, `0x0004`) read from the image as the spec gives
  them (`static.txt` `GCT`, `.data`), but of the four `.text` operands inside the table two are `lea`s (0x005AE30B,
  0x005AE355) whose uses were not followed for a store, so the mask cells keep their tags. *(Part 3, § 19: the two
  `lea`s followed, no store through them; the mask cells raised.)* (fn:sub_005A87F0_CollidePlayerOrAlly@0x005A87F0,
  fn:sub_005A87B0_CollideMonster@0x005A87B0, fn:sub_005A8850_CollideUnit@0x005A8850,
  fn:sub_005A8890_CollideMissile@0x005A8890, run:2026-11-16-sweep2-s2ae2)
- [I] *Not covered.* `MonsterOwner`'s game lookup (`0x00552F60`, a guard, never reached) and a type-3 owner with
  `+0xC8` bit 10: what `UnitsHostile` does for an owned monster or a missile's owner past these is a reading.
  Unseparated controls (10): nine strictness switches at an equality that gives the same value both ways (`lvl_le0~`,
  `lvl_lt0~`, `lvl_lt_max~` and `b_cap3~` in both families, `b_cap3n~`), and `spec_any_flag` in `cun` (none of its
  matched pair nodes had a word without bit 3; `filt` and `cpa` separate it on the same code).
  (fn:sub_0058F0D0_MonsterOwner@0x0058F0D0, run:2026-11-16-sweep2-s2ae2)

### 19. Plan 0066 batch S2ae part 3: the mask uses read, `CallDoFunc`, hit 27 and unique mod 29 emulated (2026-11-16, `lane/n66sa`)

Part 3 of the batch. The emulated claims are maps of the named functions on declared inputs (ADR-0015), compared with
`tools/skills_s2ae3_emu.py`'s model over the kept run
([run:2026-11-16-sweep2-s2ae3](experiments.md#run2026-11-16-sweep2-s2ae3), `check.txt`, 4 800 cases, 0 mismatches,
0 stops, 0 unaccounted reads or writes; no import). Brackets give separating control counts (`sep`, each with `passed`
0). The mask cells rest on a static read of the same run (`masks.txt`, `static.txt`).

- [C] *m40, m41, m42, m45, m46 (the mask cells; with § 18 these rows are whole).* `g_MissileCollideTypes` (0x0073C720,
  `.data`) holds the nine `(filter, mask)` pairs of § 18 in the image bytes (run2 `static.txt` `GCT`), and no `.text`
  instruction stores into it. The four operands that name it are two reads (0x0059FD73, 0x005AE303) and two `lea`s in
  `sub_005AE1F0_MissileMoveCollide`, now followed (`masks.txt`, `stores-through=0`): 0x005AE30B's `EAX` (the filter
  word) is spilled to `[ebp-0x20]` and dead at the call at 0x005AE325; that slot is written once and read once
  (0x005AE393), and the read is loaded through (`mov ecx,[eax]` at 0x005AE397, the filter passed to 0x00641CB0).
  0x005AE355's `EDX` (the mask word) is spilled to `[ebp-0x18]` and dead at 0x005AE375; after that write the slot is
  read only at 0x005AE370, loaded through at 0x005AE373 (the mask pushed to 0x0064D9B0); the only backward branch,
  0x005AE3BF, goes to 0x005AE361, after the write. The two frame addresses that leave the function are `[ebp-0x1C]`
  (to 0x00648F40, which writes one dword there: `static.txt` `pathlist`) and `[ebp-0x34]` (the filters' four-word
  context, § 18). (fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0, 0x005AE30B, 0x005AE355,
  data:g_MissileCollideTypes@0x0073C720, run:2026-11-16-sweep2-s2ae3)
- [C] *m73 (G1 table, grim wards).* Hit function 27 (0x005ABA00) returns 1 and pops one argument (`mov eax, 1;
  ret 4`), whatever `ECX`, `EDX` and the argument hold [`spec_ret0` 300]. (0x005ABA00, run:2026-11-16-sweep2-s2ae3)
- [C] *m69 (G2), raised in part.* `sub_0056D810_CallDoFunc` (`ECX`, `EDX`; `n`, `skill`, `lvl`; `ret 0xC`) calls
  `g_SkillDoFuncs[n]` (0x007322B0, `.data`, image bytes) when `n ≤ 0xBE` **unsigned** [`n_le_be` 1 312, `n_le_be~` 203,
  `spec_signed` (a signed bound) 268] and the entry is non-null [`entry_nz` 943], with `ECX` and `EDX` unchanged (the
  do function's game and unit: do 14 passes the missile in `EDX`, 0x005AEFFC) and the stack `(skill, lvl)`; `ESI`
  holds `skill` at the call. Otherwise it returns with `EAX` = `n` (past the bound) or 0 (a null entry). 132 of the
  152 distinct non-null entries were reached as observed boundaries. The direct-call scan finds two callers, 0x005AD03C
  (hit 23) and 0x005AF000 (do 14), and entry 30 is 0x005C37C0 (`SkillDo30Curse`); the five `.text` operands naming the
  table are reads (`static.txt` `CALLERS`, `DOF`, `DOF-REF`). (fn:sub_0056D810_CallDoFunc@0x0056D810,
  data:g_SkillDoFuncs@0x007322B0, run:2026-11-16-sweep2-s2ae3)
- [I] *m69's remainder.* What do 30 then does (the creator's `auratargetstate` around the missile's path target) is not
  run here: its direct calls reach no allocator to depth 4, but `SKILLS_EvalCalc` (0x00646CA0) brings 5 indirect calls
  (`sites.txt`). (fn:sub_005C37C0_SkillDo30Curse@0x005C37C0)
- [C] *m21 (B1), raised in part, to the first creation.* `sub_005A43B0_MissileOwnerUModEvent` (`ECX` game, `EDX`
  monster; missile; `ret 4`) does nothing for a null monster, a monster whose type is not 1, or a null missile
  [`e_mon` 2 256, `e_type1` 2 348, `e_arg` 2 222]; else `sub_005A4270_UModEventRun(game, missile, 5)` with `EBX` the
  monster: with monster data and a non-zero first unique-mod byte at data `+0x1C` [`r_data` 2 261, `r_first` 2 361], it
  walks **all nine** bytes (a 0 later in the list does not stop it) and calls each non-null
  `g_UModEventFns[6 · mod + 5]` [`r_fn` 2 377] with `ECX` game, `EDX` the missile and the stack `(mod, flag)`, `flag`
  being bit 3 of the monster data's byte `+0x16`; mods 19 (0x005A2E00) and 27 (0x005A30B0) were observed boundaries.
  Mod 29's function (0x005A3610) returns without creating unless `flag` is set, the missile is type 3, its owner
  (`UnitGetOwner`: `+0xC8` bit 10, then `GameFindUnit(game, +0x94, +0x98)`, a bucket walk by `+0x0C` along `+0xE4`) is
  found, its signed class lies in the Missiles count, the row's `+5` bit 4 is clear and the owner (a monster with data)
  lacks data `+0x16` bit 0x80 [`z_flag` 1 043, `z_type3` 994, `o_bit10` 1 039, `z_owner` 1 165, `z_cls_ge0` 1 037,
  `z_cls_lt` 1 060, `z_rowbit` 980, `z_busy` 1 018]. Then the point `(x0, y0)` is the owner's path target after
  `PathTargetRevalidate` (cleared when `GameFindUnit` by the path's `+0x5C`/`+0x60` finds another unit, or an item in
  mode 1 or 2; a target that is the owner counts as none) [`t_has` 380, `t_moved` 691, `t_item` 214, `t_mode12` 167,
  `t_self` 559, `z_tgt` 939], else the missile's path position (`+0x10`, `+0x12`). The local seed is
  `RNG_SeedInit(0x53454953)`, after which its high word is overwritten with the owner's `+0x0C`; nothing reads it
  before the first creation (the two words in the observed frame). `(dx, dy)` are the signs of the owner's
  sub-tile position minus `(x0, y0)`, both 0 for classes 0x3F–0x42 [`z_c3f` 771, `z_c42` 398, `spec_no_zero` 230]; a
  monster owner with data gets `+0x16 |= 0x80` [`z_ownmon` 727, `z_owndata` 510]; the first creation is
  `sub_0056ECB0_SkillMissileCreate(game, class; owner, MISSDATA_GetSkill (+0x0A), MISSDATA_GetLevel (+0x0C), 0, 0,
  x0 − dy, y0 + dx, 0)` [`spec_same_side` (the other side first) 709]. (fn:sub_005A43B0_MissileOwnerUModEvent@0x005A43B0,
  fn:sub_005A4270_UModEventRun@0x005A4270, 0x005A3610–0x005A37C8, fn:sub_00552F60_GameFindUnit@0x00552F60,
  fn:sub_00553490_PathTargetRevalidate@0x00553490, data:g_UModEventFns@0x0073C0B8, run:2026-11-16-sweep2-s2ae3)
- *m21's remainder → b (H2a).* The second creation (`x0 + dy, y0 − dx`, 0x005A37AB) and the clear of bit 0x80 after it
  come after the first creation's allocation: 0x005A377C → `SkillMissileCreate` → `MissileCreate` → `SUnitCreate`, pool
  allocation 0x0040B430 at 0x005553BE (`sites.txt`). Before 0x005A377C no call reaches the allocator or an import
  (`sites.txt`, to depth 3 below each call; each of those callees also ran whole in `uev` with no guard reached).
- [I] *Not covered.* A monster owner with no data block (every type-1 owner drawn had one: `reach.txt` `z_owndata`
  false 0), unique-mod bytes above 42 (the table rows past them are not read as code pointers here) and owner or
  target types above 5 (`GameFindUnit` reads address 0 for them). (run:2026-11-16-sweep2-s2ae3)

### 20. Plan 0066 batch S2ae part 4: the zig-zag callback and `MissileCreate` to its allocation emulated (2026-11-16, `lane/n66sa`)

Part 4 of the batch. The emulated claims are maps of the named functions on declared inputs (ADR-0015), compared with
`tools/skills_s2ae4_emu.py`'s model over the kept run
([run:2026-11-16-sweep2-s2ae4](experiments.md#run2026-11-16-sweep2-s2ae4), `check.txt`, 6 500 cases, 0 mismatches,
0 unaccounted reads or writes; the 369 stops are `zz` cases the model predicts at the fatal guard). Brackets give
separating control counts (`sep`, each with `passed` 0).

- [C] *m76 (H, re-seed sites: callback `0x005D4680`), whole.* `sub_005D4680_MissCbReseedZigzag` (`ECX` the new
  missile, `EDX` the argument; plain `ret`) returns at once for a null unit [`unit_nz` 2 500]. Otherwise: `n` is the
  missile data's range word (`+0x0E`, signed, through 0x0064A300: 0 unless the unit is type 3 with data) [`type3`
  1 853, `data_nz` 1 269]; at `n ≥ 78` it is 77 and both data words `+0x0E` and `+0x10` are set to 77 [`n_ge_4e`
  2 083, `n_ge_4e~` 122]. The seed at unit `+0x20` is `RNG_SeedInit(argument)` (low word = the argument, high word
  0x29A). The path is set to type 10 (`sub_00648CF0_PathSetType`: `+0x34 = (+0x34 & 0xFFF800FF) | 0x60000`, `+0x3C` =
  10, `+0x98` = 0; a path whose `+0x40` is 0xB or 8 then takes the fatal path [`f40_b` 2 271, `f40_8` 2 264]), path
  bytes `+0x90` and `+0x91` get `n`'s low byte, capped at 77 as an **unsigned** byte (a negative `n` gives 77)
  [`b_lt_4d` 1 563]. The start is the unit's sub-tile position (path dwords `+0x0C`/`+0x10` for types 2, 4, 5, else
  words `+2`/`+6`) [`static` 952] and the first direction `d` the low byte of `PathDirection` from it to the path's
  target words `+0x10`/`+0x12` (through `sub_00621DC0_UnitDirToPoint` and 0x0064FDC0; part 1's model). Then **two
  seed steps before any point**: the first step's low bit sets the sign (`+1` odd, `−1` even) [`odd` 939], the second
  (stored) gives the step size `lo mod 3 + 2` (the `.data` word 0x00741B10 = 2). For `i` = 0 … `n − 1` [`i_lt_n`
  2 083, `i_lt_n~` 1 345]: `d += size · sign`; the 8-way direction is the byte at `0x00745600 + (d & 0x3F)` (`.data`,
  64 bytes, 8 per direction); `x`, `y` advance by that direction's `.rdata` steps (0x006E32AC, 0x006E328C: ±2 or 0)
  and are stored as two u16 at path `+0x9C + 4i`; when `i mod 15 = 0` (`.data` word 0x00741B0C = 15) the sign flips
  and one more step gives a new size [`i_mod_per` 949, `spec_no_flip` (no flip) 938]. Last, path `+0x28` = `n`. So the
  callback steps the missile's seed `2 + ⌈n ÷ 15⌉` times for `n ≥ 1` (points 0, 15, 30, …) and twice for `n ≤ 0`;
  no other draw. (fn:sub_005D4680_MissCbReseedZigzag@0x005D4680, 0x005D4764–0x005D4854,
  fn:sub_00648CF0_PathSetType@0x00648CF0, run:2026-11-16-sweep2-s2ae4)
- [C] *m14, m16, m17, m18, m19 (B1), to the allocation.* `sub_0059FA30_MissileCreate` (`ECX` game, `EDX` the block
  `p`) returns 0 when `p.owner` (`+4`) is null, the class (`+0x10`) is outside `[0, nMissiles)` as a signed value, or
  the owner's type is neither 0 nor 1 [`owner_nz` 1 678, `cls_ge0` 1 790, `cls_lt_n` 2 007, `cls_lt_n~` 188, `owner_t0`
  921, `owner_t1` 1 226]. `(x, y)` is `(p +0x14, p +0x18)` when flag 1 is set, else the source's (`+8`) sub-tile
  position, 0 for a null source [`f1` 1 919, `src_nz` 1 071]. The room is `sub_00463740_RoomAtSubtile(room of the
  owner, x, y)`: the owner's room when `x0 ≤ x < x0 + w` and `y0 ≤ y < y0 + h` (signed; room `+0x4C`…`+0x58`), else the
  first non-null room of its neighbour list (`[room]`, count `room +0x24`) that holds the point, else 0, which refuses
  [`r_x0` 1 472, `r_y0` 1 470, `nb_nz` 196, `nb_x0` 139, `room_nz` 1 842]. `(tx, ty)` is `(x + p.tx, y + p.ty)` (32-bit
  adds) with flag 2, `(p.tx, p.ty)` with flag 0x20, else `(x, y)` [`f2` 1 563, `f20` 1 319]. The velocity: with flag 4,
  `p.vel` (`+0x28`) as is with flag 0x10, else `p.vel << 8` [`f4` 1 511, `f10` 221]; without flag 4,
  `((VelLev · lvl) ÷ 8 + Vel) << 8` with `VelLev` (`+0x9B`) and `Vel` (`+0x9A`) unsigned bytes, `lvl` the block's
  dword `+0x30`, the product a 32-bit signed one and the division signed toward zero [`spec_lvl_m1` (`lvl − 1`) 853,
  `spec_floor8` (rounding down) 112, `spec_udiv8` (unsigned) 112]. With the row's `CanSlow` (`+4` & 8, `g_BitMask32[3]`)
  and the owner in state 87 with a state list found by `UNIT_FindStatListByState`, `v ← stat161 · v ÷ 100` (the list's
  base stat 161, layer 0; 32-bit product, signed ÷ toward zero) [`canslow` 373, `st87` 204, `sl_found` 355,
  `spec_floor100_slow` 25]; then a non-zero `v` becomes `v · 75 ÷ 100`, signed toward zero [`v_nz` 1 128,
  `spec_floor100_75` 96]. With `v ≠ 0` [`v_nz2` 1 045]: no target and `(tx, ty) = (x, y)` → both `+1` [`t_nz` 1 049,
  `txy_eq` 415]; a target other than the owner on the owner's sub-tile → the target is dropped and both `+1` [`t_owner`
  274, `same_x` 204, `same_y` 210]; then the end point is the target's sub-tile position, else `(tx, ty)`, and the call
  refuses when `|ex − x| ≥ 100` or `|ey − y| ≥ 100` [`dx_ge100` 1 273, `dx_ge100~` 31, `dy_ge100` 1 251, `dy_ge100~`
  21]. The `|…|` is `neg` of a signed 32-bit difference: a difference of exactly `−2³¹` stays negative and does **not**
  refuse [`spec_abs` (a true absolute value) 2]. Otherwise the call at 0x0059FC75 is
  `SUnitCreate(ECX 3, EDX class; x, y, game, room, 1, row byte +0x183, 0)` with the frame's target, `x`, `y`, `v`, `tx`,
  `ty` and row as the model gives them (1 577 calls). (fn:sub_0059FA30_MissileCreate@0x0059FA30, 0x0059FA30–0x0059FC75,
  fn:sub_00463740_RoomAtSubtile@0x00463740, run:2026-11-16-sweep2-s2ae4)
- *After, `[I]` (ADR-0021).* What `SUnitCreate` does (its game-seed step, § C3) and every later line of B1 (the range
  with `LevRange` and the `SubLoop` loops, the activate mark, the path's target, masks and speed, the lob division,
  `MaxVel << 8`, the callback, damage, owner and the unique-mod hook) are past the boundary; the route crosses the pool
  allocation (0x0059FC75 → 0x00555230, `0x0040B430` at 0x005553BE; `sites.txt`), so those halves of m16, m17 (the
  `SubLoop` half) and m19 (the lob division and `MaxVel`) go to b (ruling R2). Before 0x0059FC75 no direct call reaches
  the allocator or an import (`sites.txt`, depth 3 below each call; each of them ran whole in `mcr` with no guard).
- [I] *Not covered.* Room bounds whose `x0 + w` wraps, and a point exactly on a room's right edge (`r_x1~`, `nb_x1~`
  separate no case: no point was drawn at `x = x0 + w`); `zz` coordinates whose unit-to-target difference exceeds
  250 sub-tiles (`PathDirection`'s product wraps past 258 and the index leaves `g_PathDirTable`); `ItemStatCost`
  flags on stat 161 (the records are declared zero). (run:2026-11-16-sweep2-s2ae4)

### 21. Plan 0066 batch S2ae part 5: `SKILLS_TargetCheck` and two re-seed callbacks emulated (2026-11-16, `lane/n66sa`)

Part 5 of the batch. The emulated claims are maps of the named functions on declared inputs (ADR-0015), compared with
`tools/skills_s2ae5_emu.py`'s model over the kept run
([run:2026-11-16-sweep2-s2ae5](experiments.md#run2026-11-16-sweep2-s2ae5), `check.txt`, 7 500 cases, 0 mismatches,
0 unaccounted reads or writes; the 655 stops are cases the model predicts at the fatal guard). Brackets give
separating control counts (`sep`, each with `passed` 0).

- [C] *d47 (D2), whole.* `SKILLS_TargetCheck` (`EAX` the skill, stack `game`, `unit`; `ret 8`) first takes the
  target from `UNIT_GetTargetUnit(game, unit)`: the unit's path (`+0x2C`; null takes the fatal path) holds a target at
  `+0x58` with its type and guid at `+0x5C`/`+0x60`; when it is set, `GameFindUnit(game, type, guid)` (the type's
  bucket, `guid & 0x7F`, walked by `+0x0C`, next `+0xE4`; type 5 one list at game `+0x1B20`) is compared with it, and
  the stored target is cleared (`+0x58` ← 0) when the unit found is another one, or when it is an item (type 4) in
  mode 1 or 2 [`gt_stored` 631, `gt_other` 2 206, `gt_found` 225, `gt_item` 539, `gt_mode1` 175, `gt_mode2` 170]; a
  target equal to the unit itself counts as none [`gt_self` 2 554]. No target → **1** [`t_nz` 3 408]. A skill outside
  `[0, nSkills)` (signed) → **0** [`sk_ge0` 1 889, `sk_ge0~` 32, `sk_lt_n` 2 122, `sk_lt_n~` 154]. With the row's
  `+6` & 0x10 (`g_BitMask32[4]`) [`tonly` 1 174] the call returns **0** unless one of three tests passes, in this order
  [`hostile` 700, `pet` 411, `ally` 422] (fn:SKILLS_TargetCheck@0x0056CC60, 0x0056CC60–0x0056CCEA,
  run:2026-11-16-sweep2-s2ae5):
  - `sub_00554200_UnitsHostile(game, unit, target)`: a type-1 unit is replaced by its owner (`MonsterOwner`
    0x0058F0D0: monster data `+0x28` record, `GameFindUnit(record +0x28, type +0x30, guid +0x2C)`), a type-3 unit
    with `+0xC8` bit 10 by `GameFindUnit(game, +0x94, +0x98)` when found; the target is replaced by its owner while
    it is a type-1 unit with an owner other than itself [`h_a_mon` 74, `h_a_owner` 83, `h_a_mis` 32, `h_a_c8` 49,
    `h_a_mis_owner` 44, `h_b_owner` 172]. The same unit → not hostile [`h_same` 302]; two players → the first one's
    `PlayerPairFlags` node for the second's guid, `flags & 8` [`h_pp` 391, `pp_id` 68]; otherwise hostile unless
    `AlignSame` (0x00650D70: both alignments 0, or both 2, with `UnitAlignGet` 2 for a type above 1 and else stat 172
    of the state-105 list, 0 without it) [`as_a0` 226, `as_b0` 82, `as_a2` 97, `as_b2` 159, `al_gt1` 164, `al_list`
    101].
  - `sub_005542C0_SkillPetTest(unit, target, skill)`: the row's `+7` & 2 (`g_BitMask32[1]`) and the target's owner
    record (`sub_0058F090_MonsterOwnerRef`) naming type 0 and the unit's guid [`pet_row2` 67, `pet_type0` 26,
    `pet_guid` 22]. Its first test (a non-player unit needs a type-1 target, `pet_u0`, `pet_t1`, `sep` 0 each) cannot
    change the result: a target that is not type 1 fails the owner test anyway.
  - `sub_00554D20_SkillAllyTest(game, unit, target, skill)`: a player unit, a type-0 or type-1 target, the row's `+7`
    & 4 (`g_BitMask32[2]`); a type-1 target is replaced by its owner record's (type, guid), which must name type 0
    [`al_u0` 24, `al_t0` 5, `al_t1` 19, `al_row4` 33, `al_owner` 19, `al_owner0` 19]; then the unit's party id
    (0x00554630 → 0x00540710: a player's guid, or with a client record at `+0x60` its `+0x24` when the record starts
    0x01020304 and −1 otherwise, searched in the parties at game `+0x1D2C`; 0xFFFF for none) must not be 0xFFFF, the
    player `GameFindUnit` finds for that (type, guid) must exist, and the two party ids (u16) must be equal
    [`al_party` 97, `pa_client` 108, `pa_magic` 2, `pa_list` 31, `pa_member` 50, `al_found` 24, `al_same` 36].
  
  Then the target's `+0xC4` bit 1 decides; the call returns **1** on every branch, and "cleared" is
  `sub_00620C10_UnitSetPathTargetUnit(unit, 0)` (path `+0x58` ← 0; a unit not of type 0, 1 or 3 takes the fatal path)
  [`dead` 909, `t_mon` 418, `t_mode12` 426, `corpse_a` 171, `corpse_b` 787]:

  | `+0xC4` bit 1 | type-1 target in mode 12 | `TargetCorpse` (`+7` & 1) | target | cases (`split.txt`) |
  |---|---|---|---|---:|
  | clear | either | either | cleared | 684 |
  | set | yes | set | kept | 73 |
  | set | yes | clear | cleared | 87 |
  | set | no | set | **cleared** | 329 |
  | set | no | clear | **kept** | 420 |

  (fn:SKILLS_TargetCheck@0x0056CC60, 0x0056CCF0–0x0056CD43, fn:UNIT_GetTargetUnit@0x00553540, 0x00553490–0x00553533,
  fn:sub_00554200_UnitsHostile@0x00554200, fn:sub_005542C0_SkillPetTest@0x005542C0,
  fn:sub_00554D20_SkillAllyTest@0x00554D20, fn:sub_00620C10_UnitSetPathTargetUnit@0x00620C10,
  run:2026-11-16-sweep2-s2ae5)
- [C] *d47, the contradiction.* Spec D2 reads `+0xC4` bit 1 as "dead": a dead target kept only by a `TargetCorpse`
  skill, otherwise cleared, any other target kept. The run gives otherwise in three of the five rows above: a target
  with the bit clear is always cleared, and a target with the bit set that is not a type-1 unit in mode 12 is cleared
  by a `TargetCorpse` skill and kept by any other. The spec reading as a control (`spec_d2`) changes 1 564 cases,
  `passed` 0; over the 1 593 cases that reach the bit test, it predicts the target's state wrongly in 1 433 (`split.txt`,
  every cell except the two mode-12 ones). Only the mode-12 rows agree with D2. What the bit means is not given by this
  code (review-fixes 1): the map above is the claim. Routed to the spec-writer (backlog
  [`2026-11-16-reverser-spec-writer-plan-0066-s2ae-part-5-refinements`](../../backlog/2026-11-16-reverser-spec-writer-plan-0066-s2ae-part-5-refinements.md)).
  (0x0056CCF0–0x0056CD35, run:2026-11-16-sweep2-s2ae5)
- [C] *m75 (H, callback `0x005D40F0`), to `PathPlan`.* `sub_005D40F0_MissCbReseedFromArg` (`ECX` the new missile,
  `EDX` the argument; plain `ret`) returns at once for a null unit [`unit_nz` 1 500]. Otherwise the range `r` (data
  `+0x0E` through 0x0064A300, 0 unless type 3 with data) is capped at 77 from 78 on, both data words set [`type3`
  1 111, `data_nz` 780, `r_ge_4e` 1 284, `r_ge_4e~` 76]; the seed at `+0x20` is `RNG_SeedInit(argument)`, the
  argument alone (`spec_plus_x`, `Init(path word +0x10 + argument)` as `0x005C9290` does, 1 284); the path is set to
  type 10 (as § 20; `+0x40` of 0xB or 8 takes the fatal path [`f40_b` 1 389, `f40_8` 1 358]) and its bytes `+0x90`,
  `+0x91` get `r`'s low byte capped at 77 unsigned [`b_lt_4d` 929]; then `PathPlan(path, missile, 0)` from 0x005D4141
  (1 284 calls, observed boundary). No seed step before that call. (fn:sub_005D40F0_MissCbReseedFromArg@0x005D40F0,
  0x005D40F0–0x005D4141, run:2026-11-16-sweep2-s2ae5)
- [C] *m77 (H, callback `0x005CD110`), to `PathPlan`.* `sub_005CD110_MissCbReseedRoll`: the same null test and range
  cap [`unit_nz` 2 000, `r_ge_4e` 1 713, `r_ge_4e~` 99]; the seed is `RNG_SeedInit(path word +0x10 + argument)` (the
  word zero-extended by 0x00648A00, a 32-bit add), then **one** inline step (`lo·0x6AC690C5 + hi`, stored)
  [`spec_no_step` 1 775]; when the new low dword **unsigned** mod 100 is at least 20 [`roll_ge20` 1 960, `roll_ge20~`
  22, `spec_smod` (signed) 766] the path is set to type 10, `+0x90`/`+0x91` to the capped range byte, and
  `PathPlan(path, missile, 0)` is called from 0x005CD1AE (1 332 calls); below 20 the callback returns with no path
  change (393 cases in `reach.txt`). (fn:sub_005CD110_MissCbReseedRoll@0x005CD110, 0x005CD110–0x005CD1B9,
  run:2026-11-16-sweep2-s2ae5)
- *After, `[I]` (ADR-0021).* What `PathPlan` does from these two entries is past the boundary. The entry state is the
  one in which `0x005C9290`'s `PathPlan` takes its random walk (H1, [C] there: type 10, `+0x91` the capped range), so
  the walk's steps of the new seed follow here too whenever `+0x91 ≥ 2`; the spec table's "Draws after" cells
  ("none" for `0x005D40F0`, "1 inline" for `0x005CD110`) leave them out (refinement, same backlog entry). Who passes
  the argument (do 37's ring word for `0x005D40F0`) is the caller's: the callbacks run inside `MissileCreate` after
  `SUnitCreate`'s pool allocation (0x0059FC75 → 0x00555230, `0x0040B430` at 0x005553BE; part 4's `sites.txt`), so
  that half of m75 goes to b (ruling R2). For m82 (H1, "the other re-seed callbacks … reach the same walk when they
  set type 10") these two entries are the `[C]` half: both callbacks set type 10 and call `PathPlan(path, missile, 0)`
  with `+0x90`/`+0x91` the capped range; the walk from there (PathPlan run whole, as run:2026-11-03-path-emu-3 ran it
  for `0x005C9290`) and the do functions (`0x005B0640` calls `PathPlan` at 0x005B0767) stay open.
- [I] *Not covered.* `tc`: the guard tests the three-way chain makes unreachable (`pet_u0`, `pet_t1`); owner chains
  longer than three units; party lists with more than two parties; the `ItemStatCost` flags on stat 172 (records
  declared zero). `rfa`, `rro`: a null path and the strictness of the byte cap at 77 (`b_lt_4d~`, as § 20).
  (run:2026-11-16-sweep2-s2ae5)

### 22. Plan 0066 batch S2ae part 6: six stat-event handlers and Kick's start emulated, the open routes read (2026-11-16, `lane/n66sa`)

Part 6 of the batch. The emulated claims are maps of the named functions on declared inputs (ADR-0015), compared with
`tools/skills_s2ae6_emu.py`'s model over the kept run
([run:2026-11-16-sweep2-s2ae6](experiments.md#run2026-11-16-sweep2-s2ae6), `check.txt`, 18 500 cases, 0 mismatches,
0 stops, 0 unaccounted reads or writes). Brackets give separating control counts (`sep`, each with `passed` 0). The
handlers take `ECX` the game, `EDX` the event id and five stack words (the handler's unit, the other unit, the packet,
the event word `stat << 16 | layer`, one unused here; `ret 0x14`); the handler's stat is
`sub_00625500_UnitGetStat(unit, word >> 16, word & 0xFFFF)`, which does not test the unit. Each observed call ends its
case (ADR-0021): what the callee does is past the claim.

- [C] *Handler 7 (knockback), whole.* A null unit, other unit or packet returns 0 [`u_nz` 799, `o_nz` 741, `pkt_nz`
  744], as does a stat ≤ 0 (signed) [`v_gt0` 1 767, `v_gt0~` 734]. The cap `c` is 64; for a type-1 other unit whose
  `sub_00451FE0_MonStats2Rec` (MonStats `+0x18`, signed, below the MonStats2 count) exists, its byte `+5` bit 3 gives 32
  and else bit 2 gives 128 [`o_mon` 103, `ms2_rec` 252, `b5_8` 108, `b5_4` 55]. One inline step of the unit's seed;
  `low & 0x7F < c` (signed compare) sets the packet's `+0x04` word bit 3 and returns 1, else 0 [`roll_lt_cap` 714,
  `roll_lt_cap~` 8; a `0xFF` mask, `spec_mask_ff`, 164]. 355 returns of 1, 1 645 of 0 (`reach.txt`).
  (fn:sub_005BF960_StatEv07Knockback@0x005BF960, 0x005BF960–0x005BFA03, run:2026-11-16-sweep2-s2ae6)
- [C] *Handler 8 (howl), to `sub_005DDD00_MonFleeFrom`.* Returns 0 for a null unit or other unit, an other unit not of
  type 1 [`u_nz` 515, `o_nz` 563, `o_mon` 777], one whose MonsterData `+0x16` word has a bit of `0x0C`
  (`sub_005A0180_MonTypeFlag`) [`mt_c` 813; the mask 4 alone, `spec_mask_4`, 132], or a stat ≤ 0 [`v_gt0` 1 192,
  `v_gt0~` 514]. Then `RNG_RangePow2(unit seed, 128)` (one step, `low & 0x7F`); below the stat (signed) it calls
  `MonFleeFrom` with `ECX` the game, `EDX` the handler's unit and stack (other unit, 0x82, 0x14, 0x14) from
  0x005BFA88 (296 calls), else returns 0 [`roll_lt_v` 472, `roll_lt_v~` 2]. (fn:sub_005BFA10_StatEv08Howl@0x005BFA10,
  0x005BFA10–0x005BFA98, run:2026-11-16-sweep2-s2ae6)
- [C] *Handler 9 (stupidity), to `0x005C39C0`.* Returns 0 for a null unit or other unit or an other unit not of type 1
  [`u_nz` 1 104, `o_nz` 1 180, `o_mon` 1 405], or a stat of 0 (a negative stat goes on) [`v_nz` 1 930]. The chance is
  `c = 5·(L_unit + 4·v − L_other + 6)` in 32-bit arithmetic, `L` each unit's stat 12 by `STATS_GetUnitStat`; for event id
  6 a positive `c` is divided by 3 (truncated) [`ev6` 81, `ch_gt0` 56, `spec_no_third` 56]; then `c ≤ 1` gives 1 and
  `c ≥ 99` gives 99 [`ch_gt1` 571, `ch_lt99` 633]. `r = RNG_Range(unit seed, 100)`; `r ≥ c` returns 0 [`roll_lt_ch`
  1 104, `roll_lt_ch~` 11]; else `n = (c − r) / 5 + 1` clamped to 1..20 [`n_gt1` 534, `n_lt20` 511] and
  `0x005C39C0` is called with `ECX` the game, `EDX` the unit and stack (other unit, `n`) from 0x005BFB88 (571 calls).
  (fn:sub_005BFAA0_StatEv09Stupidity@0x005BFAA0, 0x005BFAA0–0x005BFBA1, run:2026-11-16-sweep2-s2ae6)
- [C] *Handler 10 (lightning thorns), to `COMBAT_ApplyDamage`.* Returns 0 for a null unit or other unit, an other unit
  whose `+0xC4` bit 2 is clear [`u_nz` 523, `o_nz` 513, `o_c4_b2` 543], or a stat ≤ 0 [`v_gt0` 1 232, `v_gt0~`
  525]. Otherwise a zeroed 0x70-byte packet with `+0x04` word 0x4021, `+0x1C` = `stat << 8` (`spec_no_shift` 474) and
  `+0x60` = 0x4D, and `COMBAT_ApplyDamage` with `ECX` the game, `EDX` the handler's unit and stack (other unit, 1,
  packet) from 0x005BF7A2 (474 calls; the packet compared byte for byte). No seed step before that call.
  (fn:sub_005BF720_StatEv10ThornsLightning@0x005BF720, 0x005BF720–0x005BF7A2, run:2026-11-16-sweep2-s2ae6)
- [C] *Handler 18 (heal after a demon kill), to `sub_00627260_UnitSetStat`.* Returns 0 for a null unit or other unit
  or an other unit that `MONSTATS_IsDemon` rejects (type 1, a MonStats row, `+0x0D` & `g_BitMask32[5]`) [`u_nz` 347,
  `o_nz` 319, `demon` 1 123], and 0 for a stat of 0 [`v_nz` 867] (a negative stat goes on); returns 0 when the
  unit's life (stat 6) is not below `sub_00625D10_UnitGetMaxHp` (stat 7, layer 0) [`life_lt_max` 623, `life_lt_max~`
  68]. Else `x = life + (v << 8)` (32-bit), `x ≤ 0` gives 0 [`nl_le0` 262; no floor, `spec_no_floor`, 108], `x ≥ max`
  gives max [`nl_lt_max` 273], and `UnitSetStat(unit, 6, x, 0)` is called from 0x005C02DC (319 calls: 101 sums, 89 at
  the maximum, 129 at 0, `reach.txt`). No seed step before that call. (fn:sub_005C0260_StatEv18HealAfterDemonKill@0x005C0260,
  0x005C0260–0x005C02DC, run:2026-11-16-sweep2-s2ae6)
- [C] *Handler 31 (reanimate), to `UNIT_AddEvent`.* Returns 0 for a null unit or other unit, an other unit not of
  type 1 or one with MonsterData `+0x16` & 0x0C [`u_nz` 1 139, `o_nz` 1 214, `o_mon` 1 578, `mt_c` 2 047], or a stat
  ≤ 0 [`v_gt0` 1 619, `v_gt0~` 502]. `r = RNG_RangeB(unit seed, 100)`; `r ≥ v` returns 0 [`roll_lt_v` 472,
  `roll_lt_v~` 5]. Then the unit's player: the unit itself if of type 0, else `sub_0058F0D0_MonsterOwner` repeated
  until a type-0 unit, 0 ending the walk with a return of 0 [`is_player` 678, `p_found` 678]. `UNIT_AddEvent` is called
  with `ECX` the game, `EDX` the **other** unit and stack (0x0D, the event word's low 16 bits, the player's guid,
  `sub_005C07A0_SkillReviveDo`, 0, the player's guid) from 0x005C0A74 (299 calls). (fn:STATEVENT_Reanimate@0x005C09E0,
  0x005C09E0–0x005C0A74, run:2026-11-16-sweep2-s2ae6)
- [C] *d93 (dispatch I4), Kick's start, whole up to its one queue call.* `sub_0056CAF0_SkillSt02Kick` (`ECX` the game,
  `EDX` the unit, stack skill and level; `ret 8`) returns the target, 0, when `UNIT_GetTargetUnit` gives none
  [`t_nz` 1 500, with part 5's re-find tests: `gt_stored` 715, `gt_other` 933, `gt_found` 428, `gt_item` 346, `gt_mode1`
  292, `gt_mode2` 288, `gt_self` 785]. Otherwise a zeroed 0x70-byte packet with `+0x00` = 2, `+0x04` word 9, `+0x08` =
  `MinDam << (HitShift & 31)` (Skills `+0x1A8` and `+0x1A4`; `shl` takes the count mod 32: `spec_shift_full` 77;
  `MaxDam` `+0x1AC` in its place, `spec_maxdam`, 648) and `+0x60` = 1, then `COMBAT_ResolveAndQueue` with `ECX` the
  game, `EDX` the unit and stack (target, packet, 0x80) from 0x0056CB80 (648 calls; the packet compared byte for
  byte). Its three direct calls are 0x00553540, the memset 0x00681EF0 and 0x0057DBF0, with no indirect call, and its only
  record reads are `+0x1A4` and `+0x1A8` (`static.txt`, 0x0056CAF0–0x0056CB90): it calls neither `GetPhysMin` nor
  `GetPhysMax` and does not read `MaxDam`. (fn:sub_0056CAF0_SkillSt02Kick@0x0056CAF0, 0x0056CAFE, 0x0056CB42,
  0x0056CB54, 0x0056CB5A, 0x0056CB80, run:2026-11-16-sweep2-s2ae6)
- *After, `[I]` (ADR-0021).* What `MonFleeFrom` does with its arguments (spec K: "the monster flees"), what
  `0x005C39C0` does with `n`, the damage `ApplyDamage` and `0x0057CEE0` deal from handler 10's packet, the write
  `UnitSetStat` makes and handler 18's overlay call (stat 0x97, 0x005C02E9), and what the `SkillReviveDo` event does
  later are all past their calls. Every one of those callees reaches the pool on its route (`run5/sites.txt`:
  `MonFleeFrom` the free 0x0040B480 at 0x0058EE65 via 0x0058EDE0 ← 0x005B0E00; `0x005C39C0` the free at 0x005C0BC4 via
  0x005C0B50 ← 0x005C35C0; `ApplyDamage` the free at 0x005C0CDD via `UNIT_DispatchEvent`; `UNIT_AddEvent` the
  allocation at 0x005C0AF2; `UnitSetStat` 0x0040B4B0 at 0x00624E73 when the list grows), so the remainders that lie
  there go to b (ruling R2), except handler 18's write, which a declared stat 6 keeps off the allocator (c-emu).
- [C] *The open routes read (part 6 triage).* Each of the following was read in `static.txt` (objdump, the run's
  revision) against `run5/sites.txt`; the class follows ruling R2 (ADR-0029) on the actual route (run:2026-11-16-sweep2-s2ae6):
  - do 146 (d182, d184, spec P2): the re-seed `RNG_SeedInit` at 0x005C8688 and the `RNG_Range(1 000 000)` at 0x005C8694
    come after the unconditional call 0x005C8654 → `0x005417D0`, which reaches `EventBlockNew` 0x00540BB0 (at 0x00540C56
    via 0x00540C30 ← 0x00540DF0 ← 0x005416B0): both rows go to b (H2a). (0x005C8642–0x005C869B,
    fn:sub_005C8520_SkillDo146Armageddon@0x005C8520)
  - handlers 2 and 3 (d111, d112): the packet is built before `COMBAT_ApplyDamage` (0x005CACFD, 0x005CADE9), but from
    `SKILLS_EvalCalc` (0x005CACE6) and `SKILLS_RollElemDamage` (0x005CADCA), which need the calc pool run whole (part
    2's open d69 piece); their "draws none / 1 (2)" cells reach past `ApplyDamage` and `0x0057CEE0`. They stay c-emu
    for the packet; the draws past the call go to b.
  - handler 1 (d110): its target tests and parameter block precede `MissileCreate` at 0x005CAC1E (no other reaching
    call): c-emu to that boundary.
  - Firestorm (d172's remainder): bit 6 (`+0xC4` |= 0x40 at 0x005C71C8) and the `calc1 ≤ 0` return (0x005C71E5) both
    precede the first `SkillMissileCreate` (0x005C7201): c-emu with a constant calc pool.
  - missile do 3 and do 5 (m71, m72): the `0x40` mark (0x0064CB90, 0x0064EA00; no pool, no import) and do 5's frame
    loop precede the tail into do 1 (`MissileMoveCollide`, which reaches the pool free through 0x005ADF10): c-emu with
    a declared room.
  - `SkillWeaponWear` (d156, d181): its one step and the chance compare precede the reaching calls (`PLAYER_UseAmmo`
    0x005DAAA8, `UnitSetStat` 0x005DAB05, 0x0053D130 at 0x005DAB26): c-emu to those boundaries.
  - `ITEMSKILL_Cast` (d79's remainder): the `ItemTarget` helpers and `ItemCheckStart` precede `SKILLS_SrvStart`
    (0x005FDC15); the restore of the target (0x005FDC44) follows `SKILLS_SrvDo` (0x005FDC2F), which reaches
    `MissileCreate`'s allocation: the restore half goes to b, the rest stays c-emu.
  - `SummonInitStats` (d144): the passive stats reach the first setter (0x005C4536); `sumskill` (0x0056E740 →
    `UNIT_AddEvent`, allocating), the aura list (0x006251F0, allocating at 0x0062520B), the equipment init (0x005701B0,
    an import) and `sumumod` (0x005D6B60) lie past allocating calls. The row stays c-emu for the passive stats; the rest
    is b's.
  - start 6 (d89), `MonOwnerSkillDamage` (d153, d154), `AreaHitUnit`'s defence roll (m74): pool only through
    `InvPageGet` (a declared page, as S5e part 3); `AreaHitUnit`'s damage (0x0056BA5F onward) is b's.
  (run:2026-11-16-sweep2-s2ae6, static.txt; run:2026-11-16-sweep2-s2ae5, sites.txt)
- [I] *Not covered.* Handler 31's owner chains longer than two links; handler 9's `L` terms beyond `[−5, 99]` and
  random 32-bit words; `UnitGetStat`'s ItemStatCost cap (records declared zero); Kick with a skill id outside the table
  (the code reads a null record's `+0x1A4`); the strictness of the clamps at their bounds (`ch_gt1~`, `ch_lt99~`,
  `n_gt1~`, `n_lt20~`, `ch_gt0~`, `nl_lt_max~`: a value at the bound gives the bound either way).
  (run:2026-11-16-sweep2-s2ae6)

### 23. Plan 0066 batch S2ae part 7: `SKILLS_ItemChargesOk`, `SkillWeaponWear` and handlers 26 and 27 emulated (2026-11-16, `lane/n66sa`)

Four families under `tools/ghidra.sh emuboundary` with `tools/skills_s2ae7_emu.py` (record:
[run:2026-11-16-sweep2-s2ae7](experiments.md#run2026-11-16-sweep2-s2ae7)): 13 500 cases, 0 mismatches, 0 stops, 0
unaccounted reads or writes; 69 controls, 65 separating, `passed` 0. Each callee runs whole on the declared image
unless named as an observed boundary (ADR-0021); bracketed counts are the cases a reversed test changes
(`check.txt`).

- [C] *d40 (dispatch C7), `SKILLS_ItemChargesOk`, whole.* With `EAX` the unit and `EBX` the skill entry: a null unit
  or entry returns 0 [`u_nz` 2 412, `ent_nz` 2 438]; no inventory (`unit +0x60`) returns 1 [`inv_nz` 623], and so does
  an entry whose item guid `+0x34` is −1 [`item_skill` 535]. The layer is `skill · 64 + (level & 0x3F)` with `skill`
  the record's signed word `+0x00` and `level` from `SKILLS_GetSkillLevel(unit, entry, 0)`: the entry's `+0x28`
  floored at 0 and capped at `ExpMaxLevel(0)`, no bonus call with the flag 0 [`lvl_gt0` 614, `lvl_lt_max` 754; the
  mask: `spec_no_mask` 215]. The walk starts at `INV_GetFirstItem` (inventory magic 0x01020304, else none:
  [`inv_magic` 507]) and follows `INV_GetNextItem` (item data `+0x64`); a node that is not of type 4 is no item and
  also ends the walk [`node_item` 524]; the end of the list returns 1 [`node_nz` 999]. The first item whose guid
  `+0x0C` equals the entry's [`guid_eq` 663] decides: `STATS_GetUnitStat(item, 204, layer)` (word layer), and
  `test eax, 0xFF; setg al` returns 1 exactly when its low byte is non-zero [`low_nz` 1 366; the whole value's sign,
  `spec_full_value`, 358]. 676 returns of 0, 2 324 of 1. (fn:SKILLS_ItemChargesOk@0x00647840, 0x00647878, 0x0064788B,
  0x006478C6, 0x006478CB, run:2026-11-16-sweep2-s2ae7)
- [C] *d156, d181 (dispatch N2, P), `SkillWeaponWear` to its three calls.* `EBX` the item, `ESI` the unit, stack
  (game, chance, amount), `ret 0xC`. `ITEMS_UnitIsType(item, 45)` first: the item record's type `+0x11E`, then its
  second type `+0x120` when `> 0` and below the ItemTypes count [`is45` 1 412, `eq1` 1 232, `eq2` 50, `t2_gt0` 71,
  `t2_lt_n` 260]; not of type 45 returns with no step. A stackable record (`+0x132`) goes the quantity way [`stack`
  1 693]: stat 70 `> 0` [`q_gt0` 1 057], one step of the unit's seed, `low mod 100` (unsigned) `<` chance (signed)
  [`ra_lt_ch` 419, `ra_lt_ch~` 48], then `PLAYER_UseAmmo` with `ECX` the game argument and `EDX` the unit from
  0x005DAAA8 (189 calls). Otherwise `sub_00629930_ItemHasDurability` [`hasdur` 2 303]: type 4, record `+0x113` = 0
  and `+0x112` > 0, stat 73's base value (the list's `+0x24` array) non-zero and its value non-zero, stat 152 ≤ 0
  [`d_item` 867, `nodur0` 792, `dur_gt0` 771, `b73_nz` 1 057, `max_nz` 1 605, `indes_le0` 888]; then one step and the
  same roll [`rd_lt_ch` 759, `rd_lt_ch~` 75]. `d = stat 72 − amount` (32-bit): `js` or zero calls
  `sub_0055F850_ItemBreak` (`ECX` game, `EDX` unit, stack the item) from 0x005DAB36 (209 calls) [`d_sign` 291, `d_zero`
  192]; else `UnitSetStat(item, 72, d, 0)` from 0x005DAB05 (137 calls). The test is the sign of the wrapped
  difference, not `dur − amount ≤ 0` (`spec_math_le0`, 58 cases, all wrapped). One step on each way once its gates
  pass (also when the roll then fails), none before them, and none between the roll and the three calls. (fn:sub_005DAA40_SkillWeaponWear@0x005DAA40, 0x005DAA70–0x005DAA9D,
  0x005DAABC–0x005DAAE9, 0x005DAAF6, 0x005DAAF9, run:2026-11-16-sweep2-s2ae7)
- [C] *d130 (dispatch K 26), handler 26 to `UnitSetStat`.* Returns 0 for a null unit or packet or a unit not of type
  1 [`u_nz` 523, `pkt_nz` 515, `u_mon` 407], a packet `+0x4C` ≤ 0 [`dmg_gt0` 636, `dmg_gt0~` 87], no
  `MonsterOwner` [`p_found` 1 083] or a dead one (`sub_005541B0_UnitIsDead`: `+0xC6` bit 0, a player in mode 0 or
  17, a monster in mode 0 or 12, any other type) [`p_dead` 814, `dead_bit` 440, `dead_pmode` 455, `dead_mmode` 131],
  the owner's life (stat 6) below 256 [`life_ge256` 595, `life_ge256~` 35], no MonStats row [`ms_rec` 440] or a
  negative `+0x170` skill [`sk_ge0` 500]. The loss is `MulDiv(+0x4C, p, 100)` with `p` the skill's Skills `+0x158`
  (0 outside the table) [`sk_rec` 369; a plain 64-bit percentage, `spec_pct`, 31]; `life − loss` below 256 becomes 256
  [`nv_lt256` 394; no floor, `spec_no_floor`, 116]; `UnitSetStat(owner, 6, x, 0)` from 0x005C6731 (407 calls). No
  step. (fn:sub_005C6690_StatEv26BloodGolemDamaged@0x005C6690, 0x005C66B2, 0x005C66E3, 0x005C66F7, 0x005C6712,
  0x005C671B, run:2026-11-16-sweep2-s2ae7)
- [C] *d131 (dispatch K 27), handler 27 to `STATE_ApplyTimed`.* Returns 0 for a null unit or other unit [`u_nz`
  1 371, `o_nz` 1 370] or a zero stat 150 (`UnitGetStat`, layer 0) [`v_nz` 1 502]. `v` is capped at 50 for a type-0
  other unit [`o_player` 1 467] and for a type-1 one with MonsterData `+0x16` & 0x0C [`mt_c` 443], at 90 for any
  other type-1 unit [`o_mon` 1 495], and any other type returns 0; a negative `v` passes uncapped [`v_ge_cap` 1 183;
  the caps swapped, `spec_cap_swap`, 720]. `STATE_ApplyTimed` is called with `ECX` the stack block (unit, other, 0, 1,
  750, 0x43, `−v`, 0x18, 0) from 0x005C6819 (1 294 calls, the block compared byte for byte). No step.
  (fn:sub_005C6760_StatEv27ClayGolemSlow@0x005C6760, 0x005C6796–0x005C67CA, 0x005C67E9, 0x005C6819,
  run:2026-11-16-sweep2-s2ae7)
- *After, `[I]` (ADR-0021).* The ammunition `PLAYER_UseAmmo` uses, `ItemBreak`'s break, the writes `UnitSetStat` makes
  (stat 72 on the item, stat 6 on the owner), handler 26's packet reduction after its call (0x005C6736–0x005C6749),
  handler 27's stats 68 and 69 at `−v` (0x005C6835, 0x005C6840) and the overlay calls are past their calls.
  `STATE_ApplyTimed` reaches the pool (0x0040B4B0 at 0x00624CC8 via 0x00624C80 ← 0x006270B0 ← 0x00627150),
  `PLAYER_UseAmmo` (0x0040B430 at 0x0063AE2D via 0x0063ADD0 ← 0x0063BDE0) and `ItemBreak` (0x0040B4B0 at 0x00624E73
  via `UnitSetStat`) too (`run5/sites.txt`), so those remainders go to b (ruling R2); the two setter writes stay
  c-emu, as handler 18's (a declared stat present keeps the setter off the allocator).
- [I] *Not covered.* The callers' arguments (Impale's calc2 and calc3, the entry the request checks pass);
  `ItemChargesOk` chains longer than four items; `UnitGetStat`'s ItemStatCost caps (records declared zero); item
  classes past the items count and first types past the ItemTypes count (0x00628700's type is used unchecked); the
  strictness of a clamp at its own bound (`lvl_gt0~`, `lvl_lt_max~`, `nv_lt256~`, `v_ge_cap~`: the bound gives the
  bound either way). (run:2026-11-16-sweep2-s2ae7)
- *2026-11-16 (part 8, § 24):* the two setter writes and handler 26's packet reduction now run whole,
  run:2026-11-16-sweep2-s2ae8.

### 24. Plan 0066 batch S2ae part 8: the stat setter run whole, behind handlers 18, 26, `SkillWeaponWear` and in `MissileDamageToStats` (2026-11-16, `lane/n66sa`)

Five families under `tools/ghidra.sh emuboundary` with `tools/skills_s2ae8_emu.py` (record:
[run:2026-11-16-sweep2-s2ae8](experiments.md#run2026-11-16-sweep2-s2ae8)): 18 000 cases, 0 mismatches, 0 stops, 0
unaccounted reads or writes; 241 controls, 199 separating, `passed` 0. The world is a unit's whole stat list (base
array `+0x24`, cache `+0x48`, the client's changed-key array `+0x50`, the stat callback `+0x5C`/`+0x60`, a parent
chain `+0x34` of up to two lists) and declared ItemStatCost rows (`+0x04`, `+0x05`, `+0x50`..`+0x53`; the handlers'
and `MissileDamageToStats`' stats carry the shipped table's bytes there), after batch S4e part 5d's `addst` approach
(`lane/n66z`). The calls that allocate or leave the claim are observed boundaries (ADR-0021): `STATLIST_InsertEntry`
0x00624C80, the resize 0x0040B4B0, the callback 0x0055B800 and `sub_006266C0_StatRecompute`; the CRT memmove
0x00683840 runs whole. Bracketed counts are the cases a reversed test changes (`check.txt`).

- [C] *The setter (`set`, 6 000 cases), `sub_00627260_UnitSetStat(unit, stat, value, param)`, whole.* The key is
  `(stat << 16) + (param & 0xFFFF)` (32-bit, wrapping) [`sx_found` 5 663]. `STATLIST_SetStatEx` on the unit's
  `+0x5C` list: no list returns 0 [`sx_list` 4 740]; the key absent from the base array returns 0 for a value of 0
  [`sx_val` 690], else calls `InsertEntry` (observed, from 0x006270F2); `delta = value − old` (wrapping), 0 returns 0
  [`sx_delta` 4 774; adding instead of setting, `spec_add`, 4 539]. A value of 0 removes the entry
  (`STATLIST_RemoveEntry`: memmove of the tail [`rm_mid` 538], count − 1, and when `cap − count > 8` (signed words)
  the capacity − 4 written and the resize called with `(cap − 4) · 8` [`rm_shrink` 816, `rm_shrink~` 102]), any other
  value is written [`sx_zero` 4 032]. `STATLIST_Propagate(list, key, delta)`: a stat ≥ the ItemStatCost count
  [`pr_isc` 2 794] or list flag `0x2000` [`pr_2000` 3 207] stops; the walk starts at the list itself when `+0x10` bit
  31 is set, else at its parent [`pr_ext` 2 729]; per list, a row with `+0x51` or `+0x52` non-zero calls
  `StatRecompute` (observed) [`pr_op` 2 540], else `STATLIST_CacheAdd`; then the walk stops at a list with `0x2000`
  [`pr_stop` 684] or, for a row with `+0x04` bit 2, with `0x40000000` [`pr_nodmg` 416], else moves to `+0x34` until
  null [`pr_cur` 2 729]. `CacheAdd`: the key absent from the cache calls `InsertEntry` (from 0x006250D5) [`ca_found`
  2 071]; the cache value += delta; a result `> 0` (signed) with row `+0x53` sets list flag `0x20000000` [`ca_pos`
  370, `ca_pos~` 56, `ca_53` 775]; a result 0 removes the entry unless row `+0x50` is set [`ca_zero` 1 415, `ca_keep`
  334]; a callback with row `+0x05` bit 3 is called with `ECX` = `+0x60`, `EDX` = `+0x44` and (0, key, old, new)
  [`ca_cb` 665, `ca_cbbit` 1 211]. Then, for a list with bit 31 and `+0x08` = 0 [`sx_ext` 114, `sx_8` 164],
  `STATLIST_MarkClientDirty`: stats 6, 8, 10, 13 and 14 return at the switch 0x00624DFD, stats 7, 9, 11, 12 go on
  [`md_sw` 125; no switch, `spec_md_all`, 43]; a stat below the count [`md_isc` 381] whose row has `+0x05` bit 4
  [`md_send` 426] is inserted in the sorted int32 array at `+0x50` unless present, the array grown by 4 through the
  resize when full [`md_room` 167, `md_room~` 64]. Back in `UnitSetStat`, a changed value on a type-0 unit marks the
  key once more [`us_ret` 71, `us_player` 64]. 3 831 returns; 848 `InsertEntry`, 405 resize, 447 callback, 469
  `StatRecompute` calls. (fn:sub_00627260_UnitSetStat@0x00627260, fn:STATLIST_SetStatEx@0x006270B0,
  fn:STATLIST_RemoveEntry@0x00624D10, fn:STATLIST_Propagate@0x00626920, fn:STATLIST_CacheAdd@0x006250B0,
  fn:STATLIST_MarkClientDirty@0x00624DD0, run:2026-11-16-sweep2-s2ae8)
- [C] *d124 (dispatch K 18), the setter's write.* Part 6's `h18` with the setter run whole (`h18w`, 3 000 cases):
  with stat 6 in the base array and the cache, `UnitSetStat(unit, 6, x, 0)` writes `x` and adds `x − old` to the
  cache, and the handler goes on to `sub_00621E40_UnitSetOverlayStat(unit, 0x97, 0)` from 0x005C02E9 (1 876 cases,
  dumps compared). Row 6's shipped bytes (`+0x05` = 0x10, no callback, no op link) keep the callback and
  `StatRecompute` off; the switch keeps stat 6 off the changed-key array. A key absent from the base or cache (317
  `InsertEntry`) and an `x` of 0 with the shrink (367 resize) reach the allocator. (0x005C02DC, 0x005C02E9,
  run:2026-11-16-sweep2-s2ae8)
- [C] *d130 (dispatch K 26), the write and the packet's reduction.* Part 7's `h26` with the setter whole (`h26w`,
  3 000 cases): after `UnitSetStat(owner, 6, x, 0)` the packet word `+0x4C` becomes `max(0, +0x4C − loss)` (signed;
  `setle`/`sub 1`/`and`) and the handler returns 1 [`pk_pos` 1 949; no floor, `spec_no_zero_floor`, 281]. 2 633
  returns (both kinds), 364 `InsertEntry`, 3 resize. (0x005C6731, 0x005C6736–0x005C6749, run:2026-11-16-sweep2-s2ae8)
- [C] *d156 (dispatch N2), the setter's write.* Part 7's `wear` with the setter whole (`wearw`, 3 000 cases):
  `UnitSetStat(item, 72, d, 0)` writes `d` (row 72's shipped bytes: no callback, no send bit), then
  `sub_005531C0_PlayerGetClient` with `ECX` the unit, `EDX` 0x006E32E4 and the five words pushed for 0x0053D130
  (0x9B, 1, 0x48, `d`, 0) from 0x005DAB1D (2 091 cases). 398 `InsertEntry`, 15 resize. (0x005DAB05, 0x005DAB1D,
  run:2026-11-16-sweep2-s2ae8)
- [C] *m27, m95 (missiles C1), `sub_0064AC60_MissileDamageToStats(owner, missile, block, level)`, whole* (`mdts`,
  3 000 cases). A null missile or one not of type 3 returns [`mi_nz` 2 844, `mi_type3` 3 000]. The missile data's
  `+0x14` gets bit 0 for block flag 0x1 and bit 1 for 0x4 [`f_1` 1 305, `f_4` 1 340] (the data pointer tested
  [`mi_data` 2 844]). Then `UnitSetStat(missile, s, v, 0)` in this order: 12 = the fourth argument, then block words 1
  to 30 to 21, 22, 48, 49, 315, 50–59, 326, 60–66, 316, 317, **315**, 121, 122, 120, 25; 315 ends with word 26 (the
  burn length), not word 5 [`spec_315_once` 1 123; the calls in stat order, `spec_sorted`, 977]. Block flag 0x100,
  0x200, 0x400 and 0x2 set stats 103, 104, 106 and 141 to 1 [`fl_67` 994, `fl_68` 1 041, `fl_6a` 1 009, `fl_8d`
  1 010]. With an owner [`own_nz` 893], `sub_006261D0_StatListGetEntries(owner, 180, buf, 128)` reads only an
  extended list's cache [`ge_list` 836, `ge_ext` 890], from the lower bound of key `180 << 16` (0x00624C10) while
  the entry's stat is 180 [`ge_stat` 979] and fewer than 128 [`ge_max` 741], and each entry is set on the missile at
  its layer. 1 648 returns, 360 `InsertEntry`, 992 resize. (fn:sub_0064AC60_MissileDamageToStats@0x0064AC60,
  0x0064ACFD, 0x0064AE2F, 0x0064AE72–0x0064AEBD, 0x0064AEDC, fn:sub_006261D0_StatListGetEntries@0x006261D0,
  run:2026-11-16-sweep2-s2ae8)
- *After, `[I]` (ADR-0021).* `InsertEntry` (0x0040B4B0 at 0x00624CC8), the resize 0x0040B4B0 itself (from 0x00624D7E
  and 0x00624E73), the callback 0x0055B800 and `StatRecompute` are past their calls: a key absent from a list, a
  removal past 8 spare slots, a full changed-key array, a callback row or an op-linked row take the setter to the
  allocator or out of the claim, so those routes go to b (ruling R2). h18's overlay call and wear's client packet are
  past their calls.
- [I] *Not covered.* Rows with `+0x05` bit 2 (the getter's minimum, kept clear so parts 6 and 7's getters read as
  before); parent chains longer than two; the strictness of `idx < count − 1` (`rm_mid~`: the last entry moves 0
  bytes either way) and of `count < 128` (`ge_max~`: at most 8 entries declared); in `h18w`, `h26w`, `wearw` the
  callback, `+0x08` and player tests (rows 6 and 72 send nothing or stop at the switch, so those reversals change no
  case). (run:2026-11-16-sweep2-s2ae8)

### 25. Plan 0066 batch S2ae part 9: `SummonSetLevel` and handler 25 emulated with the setter whole; the batch closed (2026-11-16, `lane/n66sa`)

Two families under `tools/ghidra.sh emuboundary` with `tools/skills_s2ae9_emu.py` (record:
[run:2026-11-16-sweep2-s2ae9](experiments.md#run2026-11-16-sweep2-s2ae9)): 14 000 cases, 0 mismatches, 0 stops, 0
unaccounted reads or writes; 149 controls, 127 separating, `passed` 0. The setter world and its observed boundaries
are part 8's (§ 24: `STATLIST_InsertEntry` 0x00624C80, the resize 0x0040B4B0, the callback 0x0055B800,
`sub_006266C0_StatRecompute`), with part 8's ItemStatCost rows (`isc.bin`, the same bytes); two more boundaries:
`sub_0064C040_UnitMarkUpdated` (from 0x00639E76) and `STATE_Set` 0x00639DB0 (from 0x005C893F). Only the fields named
below are written in the units, lists and game, so any other read of them would be a traced, unaccounted read; no
MonStats image is loaded (the data table's `+0xA78` is 0). Bracketed counts are the cases a reversed test changes
(`check.txt`).

- [C] *`sub_006272B0_UnitAddStat(unit, stat, value, param)` → 0x00627030, whole.* A value of 0 returns at once
  [`ua_val` 4 237]; the unit is not tested (its `+0x5C` list is read); no list returns [`ax_list` 4 237]; the key
  `(stat << 16) + (param & 0xFFFF)` absent from the base array calls `InsertEntry` (from 0x0062706B) [`ax_found`
  4 237]; else the entry `+= value` (wrapping), a result of 0 removes it (`RemoveEntry`) [`ax_zero` 3 894], and
  `Propagate(list, key, value)` and, for a list with bit 31 and `+0x08` = 0, `MarkClientDirty` follow as in
  `SetStatEx` (§ 24). (fn:sub_006272B0_UnitAddStat@0x006272B0, 0x00627030–0x006270AA, run:2026-11-16-sweep2-s2ae9)
- [C] *d142, d143 (dispatch L2), `sub_005C49E0_SummonSetLevel(ECX game, EDX owner; summon, level, bonus)`, whole*
  (`ssl`, 6 000 cases; 3 711 return 1, 648 return 0, 1 413 `InsertEntry`, 228 resize). A level `> 0` (signed) is
  taken as given [`lv_pos` 5 546, `lv_pos~` 3 591]. Otherwise `L = STATS_GetUnitStat(owner, 12, 0)` (0 for no owner
  or no list), `n = trunc(s32(3L) / 4) + bonus` (32-bit, `cdq`/`and 3`/`sar 2`; a floor instead, `spec_floor`, 2; a
  ceiling, `spec_ceil`, 1 422), and the level is `L` when `max(n, 1) ≥ L` [`cap_ge` 4 100], else `max(n, 1)`
  [`n_gt1` 823, `n_gt1b` 2 036], that is `min(max(n, 1), L)`, the clamps binding on both sides. `3L` fits for
  −715 827 882 ≤ L ≤ 715 827 882 and wraps one past either end (`wrap.txt`: 3 · 715 827 883 = 2 147 483 649 →
  −2 147 483 647). A level of 0 is not written [`lvl_nz` 4 240]; any other is written by `UnitSetStat(summon, 12,
  level, 0)` (§ 24's setter, whole). Then the MonLvl index is the level clamped to `count − 1` (signed) [`ml_lt`
  4 506], and an index below 0 or not below the count returns 0 [`ml_ge0` 5 057, `ml_ge0~` 936, `ml_ltn` 4 409]. The
  difficulty is `game +0x6D` with 0 → 0, 1 → 1, ≥ 2 → 2 [`df_nz` 3 171, `df_ge2` 2 085]; the expansion is 1 when the
  byte `+0x6A` or the dword `+0x74` is non-zero [`x_6a` 2 168, `x_74` 2 100]. `UnitAddStat(summon, 31, row[d + 3x],
  0)` and `UnitAddStat(summon, 19, row[d + 3(x + 2)], 0)` follow, in that order, with the raw cells (the transposed
  layout, `spec_cells`, 4 011), and the function returns 1. The summon is declared at `+0x00` (the setter's player
  test) and `+0x5C` only and no MonStats image exists: no read of its class, its MonStats record or `noRatio` (0
  unaccounted reads). (fn:sub_005C49E0_SummonSetLevel@0x005C49E0, 0x005C4A02–0x005C4A2E, 0x005C4A40–0x005C4AAE,
  0x005C4AC6, 0x005C4ADF, run:2026-11-16-sweep2-s2ae9)
- [C] *d129 (dispatch K 25), `sub_005C87A0_StatEv25CycloneArmor(unit, –, packet, skill, –)`, to its boundaries*
  (`h25`, 8 000 cases; 312 return 1, 2 409 return 0). A null unit or packet returns 0 [`u_nz` 5 677, `pk_nz` 5 647];
  so does a skill outside `[0, count)` [`sk_ge0` 5 749, `sk_ltn` 5 733], a state word `+0x80` (signed 16) outside
  `[0, states)` [`st_ge0` 5 680, `st_ltn` 5 674], no list of that state [`sl_nz` 5 591] and a stat word `+0x56` or
  `+0x54` outside `[0, ItemStatCost count)` [`s56_ge0` 5 591, `s54_ge0` 5 708]. The list is
  `UNIT_FindStatListByState(unit, state)`: none when the unit's list lacks bit 31 [`fs_ext` 5 720] or the state is 0
  [`fs_state` 5 647], else the first list with `+0x14` = state in the `+0x3C` chain, then the `+0x40` chain, by
  `+0x2C` [`fs_eq` 6 560]. `max` = the list's base stat `+0x56` (0x00625350, the base array, not the cache); `max ≤ 0`
  returns 0 [`mx_pos` 6 219, `mx_pos~` 367]. The pool is the base stat `+0x54`; a pool of 0 goes to the off branch
  [`pool_nz` 4 521]. Otherwise the packet's `+0x10`, `+0x24` and `+0x1C`, in that order and each only when `> 0`
  [`pk10_pos` 3 935, `pk24_pos` 3 044, `pk1c_pos` 2 540; the order `+0x10`, `+0x1C`, `+0x24`, `spec_order`, 556],
  absorb: a pool larger than the field (signed) takes the field to 0 and keeps the difference, else the field
  loses the pool and the pool is 0 [`ab10` 2 347, `ab24` 2 335, `ab1c` 2 284] (0x005C8780). `STATLIST_SetStat(list,
  +0x54 stat, pool, 0)` follows (`SetStatEx` whole, no unit mark). A pool `≤ 0` goes to the off branch [`left_pos`
  2 605, `left_pos~` 1 403]: `STATE_Set(unit, state, 0)` (observed, 2 473 cases with the pool-0 entry). Else
  `pct = MulDiv(pool, 100, max)` and, when `pct − base stat 84 ≥ 5` (signed, wrapping) [`pct_ge5` 1 055], 
  `sub_00639E30_UnitSetStateBit(unit, state, 1)`: with the unit's list extended, the bit of `state` in the second of
  the two bit sets at `+0x58` (`(states + 31) / 32` words on) is set and `UnitMarkUpdated(unit)` called (observed,
  743 cases, the bit array dumped); a smaller change returns 1. (fn:sub_005C87A0_StatEv25CycloneArmor@0x005C87A0,
  0x005C8780, fn:UNIT_FindStatListByState@0x006256B0, fn:sub_00625650_StatListFindByState@0x00625650,
  fn:STATLIST_SetStat@0x00627150, 0x005C88CD–0x005C88FD, fn:sub_00639E30_UnitSetStateBit@0x00639E30,
  run:2026-11-16-sweep2-s2ae9)
- *After, `[I]` (ADR-0021).* d129: past `UnitMarkUpdated` (0x00639E71) the write of stat 84 = `pct`
  (`STATLIST_SetStat` at 0x005C891B) and the return 1; past `STATE_Set` (0x005C893F) `UNIT_UnlinkStatList` and
  `STATLIST_FreeIfPlain`, which for a list without bit 31 reaches the pool free 0x0040B480 (0x00626C20, through
  `STATLIST_Free` 0x00626CE3). Not settled in S2ae: `UnitMarkUpdated` needs a declared room (0x00620BB0 `UnitGetRoom`,
  0x0061AB60, 0x00619F90), and so does `STATE_Set`'s own mark (0x00639DD8); the plain list's free is R2's (→ b, H2a)
  once a run reaches it. Part 8's allocating routes as § 24.
- [I] *Not covered.* In `ssl`, the `+0x08`/bit-31 tests of `UnitAddStat`'s `MarkClientDirty` and the callback (rows 19
  and 31 of the declared table have no send or callback bit: `ax_8`, `ax_ext`, `ca_cb` change no case); the
  strictness of the clamps at their own bounds (`cap_ge~`, `n_gt1~`, `n_gt1b~`, `ml_lt~`, `df_ge2~`: the bound gives
  the same level either way) and `ml_ltn~` (the clamp leaves no index equal to the count); in `h25` the absorb
  compares at equality (`ab*~`: both sides give a field and pool of 0), the stat words at 0 (no case declares stat 0;
  `s54_*~`, `s56_*~`) and the state word at 0 (`st_ge0~`: state 0 finds no list either way),
  and the state-bit tests after a found list (`sb_*`: the list found implies the same bit 31). (run:2026-11-16-sweep2-s2ae9)

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
- [L] *2026-10-27 (lane/rbd):* whether a missile's stat list carries its owner's masteries (329–332, 357), so that
  § 6's mastery term is ever non-zero: no logged `MH0` list holds one. A logged build by a caster with a mastery
  (Fire Mastery's 329, say) would settle it.
- ~~`0x00645F00` (the unit's ranged missile and its level).~~ Answered 2026-10-20 in
  [skills/0003 § 10](0003-handlers.md#10-helpers-p12-left-unread).
