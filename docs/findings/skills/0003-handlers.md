# 0003 — Skill handlers: progressive entries, stat-event handlers, item-event casts, tier-A functions, re-seeds, summons

> **Subsystem:** skills/dispatch, skills/missiles
> **Question:** what do the progressive entries (`srvprgfunc` 36–41, 143), the stat-event handlers 1–31 and the
> item-event casts do, which numbered start, do, missile and hit functions of tier A run, which skill and missile code
> re-seeds a seed, how is a summon created and limited, and where does the missile pass sit in the frame?
> **Date:** 2026-10-20   **Plan:** 0045 (Phase 1, batch P1.3)   **Status:** open (Phase 1b and Phase 2 follow; the
> numbered functions outside tier A are plan 0046)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-p45h`, which carries P1.1's and P1.2's
analysis) and objdump. Counts, table contents and instruction windows come from `tools/skills_handlers_scan.py`
(sha256 `39b09e52…`), kept under `workspace/logs/skills/` with `p45h-manifest.sha256` (`handlers-scan.txt` `6c2a2739…`,
`handlers-rows.txt` `dd52e147…`). Skills, Missiles, ItemStatCost and States columns are named as in their table docs;
offsets are record offsets. This batch continues [skills/0001](0001-dispatch.md) (P1.1) and
[skills/0002](0002-missiles.md) (P1.2).

## Answer (summary)

- [I] **Progressive entries.** `srvprgfunc` numbers index `g_SkillDoFuncs`: 36 a 64-missile nova at the target, 37 and
  143 a ring of missiles each re-seeded from a local seed, 38 an area hit around the target point, 39 a scatter of
  missiles on a local seed, 40 one missile at the target point, 41 a scatter with two inline local steps per missile.
  The missile is `srvmissilea`, `srvmissileb` or `srvmissilec` by the charge count (1, 2, 3) and the count or radius is
  `prgcalc1..3` by the same count. **37, 39, 41 and 143 step the attacker's seed once at entry, before any test**; 38
  draws on it through the physical and elemental rolls (`RangeB(unit seed, max − min)` at `0x0056E1C4`), and each
  unit of its area draws its own defence roll. (fn:sub_005D3CF0_SkillSrvMissileByCharge@0x005D3CF0,
  fn:sub_005D3DA0_SkillPrgCalcByCharge@0x005D3DA0, 0x005D4E80, 0x005D3F90, 0x005D5080, 0x005D4F40)
- [I] **`0x00571AA0`** builds unit message `0xA3` (skill, level, unit, target, the finisher's peeked value, charge
  count) for the clients and changes no game state; the peek exists for it. (fn:sub_00571AA0_UnitMsgA3@0x00571AA0,
  0x005D5465)
- [I] **The stat-event table** `g_StatEventFuncs` holds 31 handlers (ids 1..31, bound `0x32`). ItemStatCost
  `itemeventfunc` registers 18 of them (6–10, 13–21, 28–31) and Skills `auraeventfunc` 11 (1–5, 22–27); 11 and 12 are
  named by no stock row. Handlers that draw on a unit's seed: 7 knockback, 14 freeze, 15 open wounds, 16 crushing blow,
  20 skill on attack/hit/kill and 30 skill on death/level-up (one inline step each), 8 howl (`RangePow2`), 9 stupidity
  (`Range`), 21 skill on get-hit and 31 reanimate (`RangeB`), 3 shiver armor (the elemental roll); 1 creates a missile.
  The others draw nothing of their own. (data:g_StatEventFuncs@0x007325B0, `handlers-scan.txt` `DRAW`)
- [I] **The event-9 handler `0x005C01D0`** is function 28 (`item_healafterkill`, stat 86): life `+= stat · 256`,
  capped at the maximum, overlay 151; **no draw**. (fn:sub_005C01D0_StatEv28HealAfterKill@0x005C01D0)
- [I] **State 52 is applied inside `COMBAT_ToHitRoll`** on a successful roll (`0x0057DB80`), by
  `sub_0057D810_PreventHealHook`: a player attacker with stat 117 and a monster defender whose class is not 704–709 get
  `STATE_ApplyTimed` of state 52 for 120 000 frames with stat 31 = 0; no draw. So it sits between the to-hit draw and
  the defence roll. (fn:sub_0057D810_PreventHealHook@0x0057D810, 0x0057D879–0x0057D891)
- [I] **Re-seed sites** (rng/0002's open rows): the missile-creation callbacks `0x005D40F0`, `0x005D4680`,
  `0x005C9290`, `0x005CD110` and `0x005AC040` set the **new missile's** seed from a value the creator passes (a local
  seed's low word, or the path position plus an index); missile do 28 and 35 re-seed the missile from the low word
  kept in `MissileData+0x28` and store the new low word back; hit 58, do 34 and `0x005A9820` re-seed the missile from
  its position. Two re-seed a **unit's** seed: Armageddon's periodic function (do 146, `0x005C8520`) re-seeds the caster
  from `SkillEntry+0x18` and stores a fresh `RNG_Range(1 000 000)` there, and `0x00645390` (no reference in the image).
  The rest are local seeds. (§ 9; `handlers-scan.txt` `DRAW`, `REF`)
- [I] **Summons and the pet limit.** `sub_0056D940_SpawnOwnedMonster` → `sub_00575D90_PetAdd(owner, pet, pettype,
  max)`: a pet type with a `group` removes the owner's pets of the other types of that group, then the owner's pets of
  the type are removed oldest first while their count exceeds `max`, except pet type 7. (fn:sub_00575720_PetGroupClear@0x00575720,
  fn:sub_00575850_PetLimit@0x00575850, tbl:PetType.txt:group)
- [I] **The frame pass** (`sub_005414D0_GameRunUnitEvents`) runs the unit-event lists in this order: missiles, players,
  monsters, objects, then a fifth list; each first its every-frame list, then the current frame's bucket. So every
  missile steps before any player or monster acts in a frame. (0x005414EE–0x00541589)
- [I] **Corrections.** P1.2's hit function 22 is `0x005ADD20` (row 233's chained area hit); the `CallDoFunc` caller
  `0x005ACFC0` is hit **23**, which no stock row uses. The ally test in `SKILLS_StartUsedSkill` never refuses: it reads
  the same skill, which the caller has just found without `TargetAlly`. `TgtPlaceCheck` has one server reader, the
  monster AI's target test. (data:g_MissileSrvHitFuncs@0x0073C840, 0x00554D56–0x00554D6B, 0x0056FBB2–0x0056FBC4,
  fn:sub_005FD470_MonSkillTargetOk@0x005FD470)

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

- [L] src:arreat-summit-skill-trees: one golem of any type at a time; a new golem replaces the old. **held**
  Detail: the four golem rows share pet type 3 with `petmax` 1; `PetLimit` removes the oldest (§ 7).
- [L] src:arreat-summit-skill-trees: skeleton and skeletal-mage counts 1, 2, 3, 3, 3, 4, … 8 by skill level, raised
  by item skill bonuses. **held**
  Detail: `petmax` `(lvl < 4) ? lvl : (2 + lvl/3)` gives the page's 20 values (`p45b-rows.txt` `PET`); `PetAdd` takes
  the evaluated count as `max` (§ 7).
- [L] src:arreat-summit-skill-trees: extra skeletons disintegrate when a skill shrine wears off. **not covered**
  Detail: § 7 reads the limit at `PetAdd` only; what removes pets when `petmax` falls is unread (src:d2dfg-blizzard's
  `basemax`, "when skill levels are reset or changed", points the same way). A gap, in *Open questions*.
- [L] src:arreat-summit-skill-trees: golems, skeletons and skeletal mages are "generated at the caster's level".
  **contradicted** (for Raise Skeleton)
  Detail: do 31 calls `SummonSetLevel(m, 0, lvl)`, which gives `min(max(L · 3/4 + skill level, 1), L)` with `L` the
  owner's stat 12 (R4: `lea eax,[ecx+ecx*2]`, `sar 2`, the clamps); so the caster's level only when the skill level is
  at least `L/4`. Golems and mages are not read (plan 0046). Phase 2 case C1,
  [backlog](../../backlog/2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md).
- [L] src:arreat-summit-skill-trees: a Druid has one spirit and one vine at a time, and spirit wolves, dire wolves and
  a grizzly exclude each other. **held**
  Detail: the totem and vine rows have `petmax` 1; `group` 1 on `spiritwolf`, `fenris` and `grizzly` makes
  `PetGroupClear` remove the other two types (§ 7).
- [L] src:d2dfg-blizzard: pet types of one `group` allow only one pet of the group alive. **held with refinement**
  Detail: one **type** of the group at a time; within it the count is the type's `max` (up to five spirit wolves), as
  src:arreat-summit-skill-trees puts it (§ 7).
- [L] src:d2dfg-blizzard: `petmax` is how many summons the skill allows at a time. **held** (§ 7)
- [L] src:arreat-summit-skill-trees: Revived monsters expire after 180 seconds; minions far from the owner disappear.
  **not covered**
  Detail: Revive is plan 0046's; the `warp`/`range` bits of PetType have no reader here.
- [L] src:arreat-summit-skill-trees: a skeleton's life is `((level − 3) · 0.5 + 1) · base` above level 3.
  **held with refinement**
  Detail: `SummonInitStats` adds `maxhp · calc1 / 100` to the maximum life; `calc1`'s values were not evaluated.
- [L] src:arreat-summit-skill-trees: a raised skeleton has a 5 % chance of a shield. **not covered**
  Detail: a summon's components and equipment are monsters/stats' (the spawn and `sub_005D6B60_MonEquipInit`), not
  read for summons here.
- [L] src:arreat-summit-skill-trees: the Blood Golem heals itself and the Necromancer from its attacks. **held with refinement**
  Detail: handler 23 heals both (§ 3); the page's 70 / 30 split is not read.
- [L] src:d2dfg-blizzard: `TgtPlaceCheck` serves monster skills that spawn units; `repeat` repeats the mode on the
  client; `leftskill` lists the skill for the left button. **held**
  Detail: one server reader of `TgtPlaceCheck`, the monster AI's target test; `repeat` and `leftskill` have client
  readers only (§ 12).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005D3CF0` | `sub_005D3CF0_SkillSrvMissileByCharge` | `srvmissilea`, or by the progressive charge count `srvmissileb`/`c` | I |
| `0x005D3DA0` | `sub_005D3DA0_SkillPrgCalcByCharge` | `prgcalc1`, or by the charge count `prgcalc2`/`3` | I |
| `0x0056E170` | `sub_0056E170_SkillRollPhys` | one `RangeB` between the skill's physical min and max into the packet | I |
| `0x005D4DB0` | `sub_005D4DB0_SkillPrgDo36NovaAtTarget` | `srvprgfunc` 36 | I |
| `0x005D4E70` | `sub_005D4E70_SkillPrgDo37Ring` | `srvprgfunc` 37 | I |
| `0x005D3E80` | `sub_005D3E80_SkillPrgDo38AreaHit` | `srvprgfunc` 38 | I |
| `0x005D3F90` | `sub_005D3F90_SkillPrgDo39Scatter` | `srvprgfunc` 39 | I |
| `0x005D5010` | `sub_005D5010_SkillPrgDo40MissileAt` | `srvprgfunc` 40 | I |
| `0x005D5080` | `sub_005D5080_SkillPrgDo41Scatter` | `srvprgfunc` 41 | I |
| `0x005D4F40` | `sub_005D4F40_SkillPrgDo143Ring` | `srvprgfunc` 143 | I |
| `0x005D4150`, `0x005D4870` | `sub_005D4150_SkillRing64LocalSeed`, `sub_005D4870_SkillRing64LocalSeedB` | rings of 37 and 143 | I |
| `0x0056D400` | `sub_0056D400_SkillNovaAtUnit` | 64 missiles from a unit's position (do 22, prg 36) | I |
| `0x00571AA0` | `sub_00571AA0_UnitMsgA3` | unit message `0xA3` to the clients | I |
| `0x005717C0`, `0x00571840` | `sub_005717C0_UnitMsg99`, `sub_00571840_UnitMsg9A` | the item-cast messages (at a unit, at a point) | I |
| `0x005FDCA0`, `0x005FDD60` | `sub_005FDCA0_ItemCastAtUnit`, `sub_005FDD60_ItemCastAtXY` | `ITEMSKILL_Cast` callers | I |
| `0x005CAB40` … `0x005C0670` | `sub_005CAB40_StatEv01MissileAtSource` … (table in § 3) | stat-event handlers | I |
| `0x005D40F0`, `0x005D4680`, `0x005C9290`, `0x005CD110`, `0x005AC040` | `sub_…_MissCbReseed…` (§ 9) | missile-creation callbacks that re-seed the missile | I |
| `0x005CAF30` | `sub_005CAF30_SkillDo83DeliverRestart` | `srvdofunc` 83 (Fire Hit) | I |
| `0x005CDF10`, `0x005CDDD0` | `sub_005CDF10_SkillDo109Frenzy`, `sub_005CDDD0_SkillDo109Hit` | `srvdofunc` 109 (MonFrenzy, BloodLordFrenzy) | I |
| `0x005D69D0`, `0x005D68A0` | `sub_005D69D0_SkillSt26BladeFury`, `sub_005D68A0_SkillDo48BladeFury` | Blade Fury's start and do | I |
| `0x0056CAF0` | `sub_0056CAF0_SkillSt02Kick` | `srvstfunc` 2 | I |
| `0x005DA8B0`, `0x0056CAB0` | `sub_005DA8B0_SkillSt04AmmoCheck`, `sub_0056CAB0_SkillSt65AmmoCheck` | `srvstfunc` 4 and 65 (same code) | I |
| `0x005DA8F0`, `0x005C3070`, `0x005D32F0`, `0x005D0180` | `sub_005DA8F0_SkillSt05NeedTarget`, `sub_005C3070_SkillSt15CorpseTarget`, `sub_005D32F0_SkillSt23MeleeRange`, `sub_005D0180_SkillSt36NeedShield` | tier-A start tests | I |
| `0x005CD910` | `sub_005CD910_SkillSt55LocalSeed` | `srvstfunc` 55 (a local seed; § 9) | I |
| `0x005DB2D0`, `0x005DB410` | `sub_005DB2D0_SkillDo07MeleeHit`, `sub_005DB410_SkillDo08MultiShot` | `srvdofunc` 7, 8 | I |
| `0x005C9480` | `sub_005C9480_SkillDo18TimedSelfState` | `srvdofunc` 18 (Bone Armor, Holy Shield, …) | I |
| `0x005C9B50`, `0x005CA3E0` | `sub_005C9B50_SkillDo22NovaAtSelf`, `sub_005CA3E0_SkillDo28MissileAtTarget` | `srvdofunc` 22, 28 | I |
| `0x005C37C0`, `0x005C35C0` | `sub_005C37C0_SkillDo30Curse`, `sub_005C35C0_CurseApplyCb` | `srvdofunc` 30 and its per-unit callback | I |
| `0x005C4B00`, `0x005C6910` | `sub_005C4B00_SkillDo31RaiseSkeleton`, `sub_005C6910_SkillDo114Summon` | `srvdofunc` 31, 114 | I |
| `0x005C7160` | `sub_005C7160_SkillDo117Firestorm` | `srvdofunc` 117 | I |
| `0x005C8520` | `sub_005C8520_SkillDo146Armageddon` | do-table entry 146, reached only as the `armageddon` state's `srvactivefunc` (no Skills row has `srvdofunc` 146; Armageddon's is 124) | I |
| `0x005C4470`, `0x005C49E0` | `sub_005C4470_SummonInitStats`, `sub_005C49E0_SummonSetLevel` | the summon's stats and level | I |
| `0x0056E620`, `0x0063EA70` | `sub_0056E620_SkillSummonClass`, `sub_0063EA70_SkillSummonRec` | `summon`, `summode` (or the monster's own) | I |
| `0x0056E780` | `sub_0056E780_SkillForUnitsNearTarget` | callback on units within a radius of the target point | I |
| `0x0056E450` | `sub_0056E450_SkillTargetCellFree` | the target point's cell against the missile's size (do 28) | I |
| `0x0056B9C0`, `0x0056BAD0` | `sub_0056B9C0_AreaHitUnit`, `sub_0056BAD0_AreaHitAt` | defence roll and damage per unit of an area | I |
| `0x00575D90`, `0x00575720`, `0x00575850` | `sub_00575D90_PetAdd`, `sub_00575720_PetGroupClear`, `sub_00575850_PetLimit` | the pet list and its limit | I |
| `0x005AE520`, `0x005AF790` | `sub_005AE520_MissDo05Loop`, `sub_005AF790_MissDo23SubPerCell` | missile do 5, 23 | I |
| `0x005AFB80`, `0x005B04A0`, `0x005B0640` | `sub_005AFB80_MissDo28Reseed`, `sub_005B04A0_MissDo34Reseed`, `sub_005B0640_MissDo35Reseed` | missile do 28, 34, 35 | I |
| `0x005A9D80`, `0x005A9F90`, `0x005A9E10` | `sub_005A9D80_MissHit02Ring`, `sub_005A9F90_MissHit03EndArea`, `sub_005A9E10_MissHit44AreaHit` | missile hit 2, 3, 44 | I |
| `0x005AABB0`, `0x005AAFB0` | `sub_005AABB0_MissHit14AreaHitSub`, `sub_005AAFB0_MissHit17Howl` | missile hit 14, 17 | I |
| `0x005ADD20`, `0x005ABA00`, `0x005ABF70` | `sub_005ADD20_MissHit22Chain`, `sub_005ABA00_MissHit27End`, `sub_005ABF70_MissHit36SubAtEnd` | missile hit 22, 27, 36 | I |
| `0x005ACDF0`, `0x005AD220` | `sub_005ACDF0_MissHit58Reseed`, `sub_005AD220_MissDmg03Flag4000` | missile hit 58, damage 3 | I |
| `0x005A9370`, `0x005A9820`, `0x005AAA90` | `sub_005A9370_MissSubRing16`, `sub_005A9820_MissSubNearReseed`, `sub_005AAA90_MissSubRing18` | sub-missile helpers | I |
| `0x0064A710`, `0x0064A730`, `0x0064A760`, `0x0064A780` | `MISSDATA_SetSeedLow`, `MISSDATA_GetSeedLow`, `MISSDATA_SetParam2C`, `MISSDATA_GetParam2C` | `MissileData+0x28`, `+0x2C` | I |
| `0x0064FC60` | `sub_0064FC60_PathDirection` | unit step vector and 64-direction index from two points | I |
| `0x006505C0` | `sub_006505C0_PathFlag08` | path `+0x34 & 8` | I |
| `0x00620C10`, `0x00648B90` | `sub_00620C10_UnitSetPathTargetUnit`, `sub_00648B90_PathSetTargetUnit` | path `+0x58` (unit), `+0x5C`/`+0x60` (type, guid) | I |
| `0x00648A00`, `0x00648A10` | `sub_00648A00_PathGetPosX`, `sub_00648A10_PathGetPosY` | path `+0x10`, `+0x12` (u16) | I |
| `0x005A43B0`, `0x005A4270` | `sub_005A43B0_MissileOwnerUModEvent`, `sub_005A4270_UModEventRun` | the owner monster's unique-mod hook at missile creation | I |
| `0x00645F00` | `sub_00645F00_UnitRangedMissile` | the unit's arrow missile from stats 157/158 | I |
| `0x00645390` | `sub_00645390_UnitSeedFromEntry` | re-seeds a unit from a skill entry; no reference in the image | I |
| `0x006EB7E0` | `g_PathDirTable` | 128 × {x, y, dir} for `0x0064FC60` | I |
| `0x006CE268` | `g_BitMask32` | 32 dwords `1 << k`, the flag-test masks | I |

## Walkthrough

### 1. Progressive entries (`srvprgfunc`) and the finisher's tail

`COMBAT_PrgFinisher` (P1.1 § 12) calls `g_SkillDoFuncs[srvprgfunc k]` with `(id, lvl)` of the charge state, after
setting the charge stat to `k` under `prgstack`. The entries read here:

```c
// fn:sub_005D3CF0_SkillSrvMissileByCharge@0x005D3CF0 (ECX unit, EDX id), trimmed
if (rec->b04 & 4 /*progressive*/ && valid(rec->aurastate) && valid(rec->aurastat1)
    && (l = UNIT_FindStatListByState(unit, rec->aurastate))) {
    c = ListStat(l, rec->aurastat1);
    if (c > 1) return c > 2 ? rec->srvmissilec : rec->srvmissileb;     // +0x4C, +0x4A
}
return rec->srvmissilea;                                                // +0x48; -1 for a bad id
// fn:sub_005D3DA0_SkillPrgCalcByCharge@0x005D3DA0 (ECX unit, EDX id; lvl): the same test, then
//   EvalCalc(prgcalc[clamp(c, 1, 3)]) (+0x38, +0x3C, +0x40); prgcalc1 when the state or list is missing
```

- [I] As above. Non-progressive do functions call `SrvMissileByCharge` too (do 22 Nova, 48 Blade Fury, 117 Firestorm,
  146 Armageddon among them): for a row without `progressive` it is simply `srvmissilea`. (0x005D3CF0–0x005D3D91)
- [I] **36** (`0x005D4DB0`, Claws of Thunder charge 2): with a target and `lvl > 0`, `m = SrvMissileByCharge`; if `m >
  0`, `sub_0056D400_SkillNovaAtUnit(target, m, id, lvl, v)` with `v = ((VelLev · lvl) / 8 + Vel) + calc1` (the Missiles
  bytes `+0x9B`, `+0x9A`, `0x00663270`): 64 missiles from the target's position toward the 64 offsets of the tables
  `0x006E1388`/`0x006E1288`, flags 3 (start and target offset), velocity `v` (flag 4) when non-zero. No draw of its own.
- [I] **37** (`0x005D4E70`, Claws of Thunder charge 3) and **143** (`0x005D4F40`, Fists of Fire charge 1, Royal Strike
  charge 2): **step the unit's seed inline at entry** (`0x005D4E80`, `0x005D4F50` region; before the record test),
  then `m = SrvMissileByCharge > 0`, the target point, `n = PrgCalcByCharge` or, when 0, `aurarangecalc`, and call the
  ring `0x005D4150` / `0x005D4870` with `EDX` = the stepped low word (`0x005D4F26`). The ring: `RNG_SeedInit(local,
  EDX)`; for every `n`-th of 64 directions (a table built on the stack, `+0x24`/`+0x28` of the parameter block) one
  inline step of the local seed, its low word as the creation callback's argument, `MissileCreate` (flags 3, start at
  the target point), then `MissileData+0x28 = Param2 + 1` (always for 37; for 143 only when the missile is 568
  `royalstrikechainlightning`). The callbacks `0x005D40F0` (37) and `0x005D4680` (143) re-seed the new missile (§ 9).
- [I] **38** (`0x005D3E80`, Fists of Fire and Blades of Ice charge 2): `COMBAT_DeliverQueued(target, 0)` first; then
  a packet with `sub_0056E170_SkillRollPhys` (one `RangeB` on the **unit's** seed, `SKILLS_GetPhysMin/Max(…, 0)`) and
  `SKILLS_RollElemDamage` (one more, two for `EType` 10), result and flags bit 0; `SKILLS_ForUnitsInRange(target point,
  r, aurafilter, 0x005D3CB0)` with `r` = `PrgCalcByCharge` or `aurarangecalc`; the callback copies the packet and calls
  `sub_0056B9C0_AreaHitUnit`: `COMBAT_DefenceRoll(unit, 1, 0)` (block, avoid, evade bits), then
  `sub_005A5560_MonCritDouble`, `COMBAT_ApplyDamage` on a hit, `COMBAT_GetHit`. (0x005D3E80–0x005D3F82)
- [I] **39** (`0x005D3F90`, Fists of Fire and Blades of Ice charge 3): one inline step of the unit's seed, `low` kept;
  `m`, the target point, `r = PrgCalcByCharge` (or `aurarangecalc`); `RNG_SeedInit(local, low)`; `r²` iterations of
  `dx = r − RNG_Range(local, 2r)`, `dy = r − RNG_Range(local, 2r)`, and a missile (flags 1) at `(tx + dx, ty + dy)` when
  `dx² + dy² ≤ r²` and that point has a room. (0x005D3F90–0x005D40E7)
- [I] **40** (`0x005D5010`, Royal Strike charge 1): `sub_0056EDE0_MissileCreateAt(id, lvl, m, tx, ty)`. No draw.
- [I] **41** (`0x005D5080`, Royal Strike charge 3): one inline step of the unit's seed; `RNG_SeedInit(local, low)`;
  needs `n = PrgCalcByCharge ≠ 0`; `n` missiles (flags 3, start at the target point), each with two inline local
  steps `dx = low % 40 − 20`, `dy = low' % 40 − 20` (unsigned remainders; `dx = 20` when both are 0), then
  `MissileData+0x28 = RNG_GetLow()` and `+0x2C = dy << 16 | dx & 0xFFFF`. (0x005D5080–0x005D5218)
- [I] **The finisher's tail.** After the last entry it calls `sub_00571AA0_UnitMsgA3(skill, lvl, peeked, 0, n)`: a
  `0xA3` message record (`.\UNIT\SUnitMsg.cpp`) with the two unit references, queued on the unit's message list
  (`Unit+0xEC`/`+0xF0`). Its other four callers are skill functions (`0x005C817C`, `0x005C8769` in Armageddon,
  `0x005CA5F0`, `0x005D2AF8`). (fn:sub_00571AA0_UnitMsgA3@0x00571AA0, `handlers-scan.txt` `REF 0x00571AA0`)
- [I] **Stock use** (`handlers-rows.txt` `ROWS prg`): Fists of Fire 143/38/39 with `prgstack`; Claws of Thunder −/36/37
  and Blades of Ice −/38/39 with `prgstack` (their first entry 0 runs nothing: the finisher's `0 < n < 0xBF` test);
  Royal Strike 40/143/41 without `prgstack` (only the entry of the current count runs). So a Fists of Fire finisher at
  three charges runs 143 (a step on the attacker's seed, then nothing: its `srvmissilea` is empty), 38 (delivery and
  two or three `RangeB` on the attacker's seed and the area's defence rolls) and 39 (a step, then the local seed).
  (fn:COMBAT_PrgFinisher@0x005D5220, 0x005D53E0–0x005D5490)

### 2. Item-event casts

- [I] `sub_005FDCA0_ItemCastAtUnit(skill, target, effect)` (`ECX` caster, `EDX` level): nothing when the caster has
  state 54 (`uninterruptable`); `ITEMSKILL_Cast(…, target, 0, 0, …, effect)`; on success the message
  `sub_005717C0_UnitMsg99` (skill, the aimed unit). `sub_005FDD60_ItemCastAtXY(skill, x, y, effect)` is the same at a
  point with `sub_00571840_UnitMsg9A`. Their callers are the handlers 20, 21 and 30 (§ 3) and `sub_005BF240_ItemUse`
  (`0x005BF1AF`, `0x005BF1D7`, `0x005BF229`). (`handlers-scan.txt` `REF 0x005FDCA0`, `REF 0x005FDD60`)
- [I] No draw in the two helpers or in `ITEMSKILL_Cast` itself (`DRAW` lines: `lcg=0`, no RNG call); the draws of an
  item cast are the handler's chance step and whatever the cast skill's do function and missile draw.
  (fn:ITEMSKILL_Cast@0x005FDA80, fn:sub_005FDCA0_ItemCastAtUnit@0x005FDCA0, fn:sub_005FDD60_ItemCastAtXY@0x005FDD60)
  *2026-10-20 (Phase 1b):* this misses one draw path. `ITEMSKILL_Cast` calls the `ItemTarget` helpers, and helper 2
  (`0x005FD850`, an item Teleport) steps the seed at `+0x20` of the unit it is given 2 to 20 times
  ([skills/0001 § 10](0001-dispatch.md#10-item-granted-skills); `p45b-reread.txt` R5). Helpers 3 and 4 are unread.
  (0x005FD900–0x005FD98A)

### 3. The stat-event handlers

`UNIT_DispatchEvent(unit, other, packet)` (`EDX` the event id) runs every handler record of the unit whose event
matches, newest first, as `handler(unit, other, packet, +0x0C, +0x10)` with the event id still in `EDX`; a record
flagged for removal (`+0x02` bit 1) or with no list (`+0x04` = 0) is unlinked and freed after its call. The record's
`+0x0C`/`+0x10` are what the registrar passed: `(stat << 16 | layer, …)` for an item stat
(`sub_0055B800_MonStatCallback`, `sub_005C4470_SummonInitStats`), `(skill, level)` for a skill's `auraevent`
(`sub_005C9480_SkillDo18TimedSelfState`, `0x005C9C10`, `0x005D8F50`, `sub_005C35C0_CurseApplyCb`).
(fn:UNIT_DispatchEvent@0x005C0C30, fn:sub_0056E740_AddStatEvent@0x0056E740, 0x0055B897, 0x005C95FA)

| # | Address | Registered by (stock) | Event | What it does | Draws |
|---|---|---|---|---|---|
| 1 | `0x005CAB40` | Chilling Armor (60) | `hitbymissile` | when the incoming missile's owner is hostile, the skill's `srvmissilea` from the unit toward the owner's position (flags `0x20`), if a Missiles row (register-passed, not resolved) has `+0x05` bit 1 | the creation's |
| 2 | `0x005CAC50` | Frozen Armor (40) | `damagedinmelee` | a packet with result `0x20` and `+0x34 = calc1` applied to the attacker, overlay `cltoverlaya` | none |
| 3 | `0x005CAD40` | Shiver Armor (50) | `attackedinmelee` | `SKILLS_RollElemDamage` into a packet (result `0x4021`, `+0x60` bits `0x0D`), applied to the attacker | 1 (2 for `EType` 10) |
| 4 | `0x005C5F50` | Iron Maiden (76) | `domeleedamage` | the cursed attacker takes back a `MulDiv(…, 100)` share of its damage, by the curse caster's calc: calc1 for a monster attacker, calc2 (player defender) or calc3 (other) for a player or hireling attacker | none |
| 5 | `0x005C61E0` | Life Tap (82) | `damagedinmelee`, `damagedbymissile` | the attacker heals `MulDiv(damage, calc1, 100)`, capped | none |
| 6 | `0x005BF670` | stat 78 | `damagedinmelee` | physical `stat << 8` to the attacker (result `0x4021`, hit class `0x8D`) | none |
| 7 | `0x005BF960` | stat 81 | `domeleedamage`, `domissiledamage` | knockback: `low & 0x7F < c` sets result bit 3; `c` 64, or 32/128 by MonStats2 flags | 1 inline (the attacker's seed) |
| 8 | `0x005BFA10` | stat 112 | as 7 | howl: `RangePow2(seed, 128) < stat` → the monster flees (`0x005DDD00`, 20, 20) | 1 |
| 9 | `0x005BFAA0` | stat 113 | as 7 | stupidity: `c = clamp(((alvl + 4·stat − dlvl) + 6)·5 [/3 missile], 1, 99)`, `r = Range(seed, 100)`, `r < c` → `0x005C39C0` for `clamp((c − r)/5 + 1, 1, 20)` | 1 |
| 10 | `0x005BF720` | stat 128 | `damagedinmelee` | lightning `stat << 8` to the attacker (hit class `0x4D`) | none |
| 11 | `0x005BF7D0` | none | — | fire `stat << 8` to the other unit (hit class `0x2D`) | none |
| 12 | `0x005BF880` | none | — | cold `stat << 8`, length `25 + 10·(alvl − dlvl)` when above (hit class `0x3D`) | none |
| 13 | `0x005BFBB0` | stat 114 | `damagedinmelee`, `damagedbymissile` | a player hit with packet `+0x4C` > 0 gains mana by a `MulDiv(…, 100)` of it and the stat (register-passed), capped, overlay 152 | none |
| 14–16 | | stats 134–136 | as 7 | freeze, open wounds, crushing blow (combat/0001 § 10) | 1 inline each |
| 17 | `0x005C0130` | stat 138 | `kill` | mana `+= stat · 256`, capped, overlay 152 | none |
| 18 | `0x005C0260` | stat 139 | `kill` | for a demon victim, life `+= stat · 256`, capped, overlay 151 | none |
| 19 | `0x005C0310` | stat 150 | as 7 | slow: `STATE_ApplyTimed` with stats 68, 69 = `−v`, `v` capped at 50 (players, bosses, hirelings, `MonTypeFlag`), 75 or 90 | none |
| 20 | `0x005C0470` | stats 195, 196, 198 | attack, kill, hit events | skill on event: with no packet or packet `+0x00` bit 5, one inline step, `low % 100 < stat` → item cast (§ 2): without `ItemTgtDo` at the other unit, or at the unit's path point when none, effect 1; with `ItemTgtDo` only at the other unit, effect 0 | 1 inline |
| 21 | `0x005C05A0` | stat 201 | `damagedinmelee`, `damagedbymissile` | skill on get-hit: packet result bit 2 needed; `RangeB(seed, 100) < stat` → cast, effect 0 | 1 |
| 22 | `0x005C6370` | Bone Armor (68) | `absorbdamage` | absorbs `packet+0x08` from `aurastat1`, removes the state at 0 | none |
| 23 | `0x005C6530` | Blood Golem (85) | `domeleedamage` | the golem's damage heals it and its owner (`0x005C5F10`) | none |
| 24 | `0x005CA6C0` | Energy Shield (58) | `absorbdamage` | per element of `0x006E30E0`, `MulDiv` share of the packet moved to mana; state removed at 0 mana | none |
| 25 | `0x005C87A0` | Cyclone Armor (235) | `absorbdamage` | absorbs fire, cold, lightning from `aurastat1` | none |
| 26 | `0x005C6690` | Blood Golem (85) | `damagedinmelee`, `damagedbymissile` | the owner loses life with the golem, floor 256 | none |
| 27 | `0x005C6760` | Clay Golem (75) | `damagedinmelee` | slow by its stat 150 (as 19, cap 50/90) | none |
| 28 | `0x005C01D0` | stat 86 | `kill` | life `+= stat · 256`, capped, overlay 151 | none |
| 29 | `0x005C0770` | stat 108 | `kill` | state 172 on the victim | none |
| 30 | `0x005C0670` | stats 197, 199 | `killed`, `levelup` | skill on death/level-up: skill `= layer >> shift`, level `= layer & mask`; one inline step, `low % 100 < stat` → cast, effect 0 | 1 inline |
| 31 | `0x005C09E0` | stat 155 | `kill` | reanimate (items/0002) | 1 |

- [I] Handler names (`re/symbols.csv`): 1 `sub_005CAB40_StatEv01MissileAtSource`, 2 `sub_005CAC50_StatEv02CalcHitAttacker`,
  3 `sub_005CAD40_StatEv03ElemHitAttacker`, 4 `sub_005C5F50_StatEv04ReturnDamage`, 5 `sub_005C61E0_StatEv05LifeTap`,
  6 `sub_005BF670_StatEv06ThornsPhys`, 7 `sub_005BF960_StatEv07Knockback`, 8 `sub_005BFA10_StatEv08Howl`,
  9 `sub_005BFAA0_StatEv09Stupidity`, 10 `sub_005BF720_StatEv10ThornsLightning`, 11 `sub_005BF7D0_StatEv11ThornsFire`,
  12 `sub_005BF880_StatEv12ThornsCold`, 13 `sub_005BFBB0_StatEv13DamageToMana`, 14 `STATEVENT_Freeze`,
  15 `STATEVENT_OpenWounds`, 16 `STATEVENT_CrushingBlow`, 17 `sub_005C0130_StatEv17ManaAfterKill`,
  18 `sub_005C0260_StatEv18HealAfterDemonKill`, 19 `sub_005C0310_StatEv19Slow`, 20 `sub_005C0470_StatEv20SkillOnEvent`,
  21 `sub_005C05A0_StatEv21SkillOnGetHit`, 22 `sub_005C6370_StatEv22BoneArmorAbsorb`, 23 `sub_005C6530_StatEv23BloodGolemHit`,
  24 `sub_005CA6C0_StatEv24EnergyShield`, 25 `sub_005C87A0_StatEv25CycloneArmor`, 26 `sub_005C6690_StatEv26BloodGolemDamaged`,
  27 `sub_005C6760_StatEv27ClayGolemSlow`, 28 `sub_005C01D0_StatEv28HealAfterKill`, 29 `sub_005C0770_StatEv29RestInPeace`,
  30 `sub_005C0670_StatEv30SkillOnDeathOrLevel`, 31 `STATEVENT_Reanimate`. (data:g_StatEventFuncs@0x007325B0)
- [I] The table and its registrations: `handlers-scan.txt` `EV` lines (31 non-null, highest 31) and `handlers-rows.txt`
  `ROWS itemeventfunc` / `ROWS auraeventfunc` (`unused_in_1_31=11,12`). The draw column is the `DRAW` line of each
  handler (`lcg` and RNG calls inside the body); "1 inline" is one LCG step on the **handler's unit** (`param_1`, the
  unit that owns the event: the attacker for the `do…` events, the defender for `damaged…`/`attacked…`).
  (data:g_StatEventFuncs@0x007325B0, 0x005BF9CF, 0x005C04D4, 0x005C06BB)
- [I] **Order inside delivery** (combat/0001 § 8): on a melee hit the attacker's `domeleedamage` handlers run before the
  defender's `damagedinmelee` ones; on a kill the defender's `killed` before the attacker's `kill`. Newest record
  first. So an attacker's `kill` handlers (28 heal after kill, 31 reanimate) run inside `COMBAT_ApplyDamage`; 28
  changes the attacker's life and draws nothing, 31 draws one `RangeB` on the attacker's seed.
  (0x0057C8DD–0x0057C970, fn:STATEVENT_Reanimate@0x005C09E0)
- [I] **State 52** (backlog `2026-10-17-reverser-reverser-a-read-which-call-applies-the.md` (a)): not an event handler.
  `COMBAT_ToHitRoll` calls `sub_0057D810_PreventHealHook` when its roll succeeds (`0x0057DB80`, after the `cmp esi,edi`
  of the draw); the hook (`EDI` attacker, `ESI` defender) needs a player attacker, a monster defender with class
  outside 704–709 and `UnitGetStat(attacker, 117) ≠ 0`, then `STATE_ApplyTimed(state 52, 120 000 frames, stat 31 =
  0)` (the block at `0x0057D869`–`0x0057D88A`). No RNG call in the hook (`DRAW 0x0057D810`: `lcg=0`, no RNG call).
  This is why the logged state-52 apply precedes the defence roll. (fn:sub_0057D810_PreventHealHook@0x0057D810,
  fn:COMBAT_ToHitRoll@0x0057D9B0)

### 4. `SKILLS_SrvStart` and `SKILLS_PayCost` inside do functions

- [I] **Do 83** (`0x005CAF30`, Fire Hit): with a target, `COMBAT_DeliverQueued(target, 0)`, `sub_0057C9F0_QueuedHitRemove`,
  then `SKILLS_SrvStart(id, lvl, noCost 0)` (`0x005CAF72`): the skill's start function 42 runs again, building the
  next hit, and the cost is paid again (Fire Hit has no mana). (fn:sub_005CAF30_SkillDo83DeliverRestart@0x005CAF30)
- [I] **Do 109** (`0x005CDF10`, MonFrenzy, BloodLordFrenzy): with a used skill and a target, removes the queued hit,
  sets bit 6, and when `0x005CDD30` finds a non-zero byte in the animation's frame list after the current frame,
  `SKILLS_SrvStart(id, lvl, 0)` (`0x005CDF70`); then `sub_005CDDD0_SkillDo109Hit`: to-hit `SKILLS_GetToHit`,
  `COMBAT_MeleeHitTest`, on a hit `ResultFlags`, `HitFlags`, `HitClass`, `edPct`-like `+0x0C = calc2`, the elemental
  roll; `COMBAT_ResolveAndQueue(…, 128)`, `COMBAT_DeliverQueued`, and `SkillEntry+0x18` = 1 on a hit, 0 on a miss; then
  with `+0x18` set, `0x005D8C70` (a timed state of `aurastate` for `auralencalc`, stat 169 counting up to `lvl`).
  (fn:sub_005CDF10_SkillDo109Frenzy@0x005CDF10, fn:sub_005CDDD0_SkillDo109Hit@0x005CDDD0)
- [I] **`0x005D69D0`** is `srvstfunc` 26 (Blade Fury, `INV` line): with a state-12 list it extends the list to `frame
  + 7`, and while `SkillEntry+0x18 ≤ frame` runs `sub_005D68A0_SkillDo48BladeFury` and, when it returns non-zero,
  `SKILLS_PayCost(id, lvl)` (`0x005D6B48`, result unused); without the list it refuses when mana `< startmana · 256`,
  else creates state 12 for 21 frames (event 12) and sets `+0x18 = 0`. Do 48 creates one `srvmissilea` toward the
  target point (flags `0x20`) when `PrgCalcByCharge − 1 > 0` and `+0x18 < frame`, then `+0x18 = frame + calc − 1`.
  So Blade Fury pays per fragment from its start function. (fn:sub_005D69D0_SkillSt26BladeFury@0x005D69D0,
  fn:sub_005D68A0_SkillDo48BladeFury@0x005D68A0)

### 5. Tier A: start and do functions

| Row | `srvstfunc` | `srvdofunc` | Reading | Draws (own) |
|---|---|---|---|---|
| 0 Attack, 5 Left Hand Swing | 1 `SKILL_AttackStart` | 1 `SKILL_AttackDo` | P1.1 § 11, P1.2 § 2 | melee chain or missile |
| 1 Kick | 2 `0x0056CAF0`: a packet result 9, flags 2, physical `MinDam << HitShift`, hit class 1, `ResolveAndQueue(…, 128)` | 2 `SKILL_MeleeDeliverDo` | start builds, do delivers | the builder's |
| 2 Throw, 4 Left Hand Throw | 65 `0x0056CAB0` | 3, 5 (P1.2) | start: `0x0056C4E0(unit)` (the thrown item) or the two refusal calls `0x00580310`/`0x00580380`, return 0 | none |
| 25 Plague Javelin, 12 Multiple Shot | 4 `0x005DA8B0` (the same code as 65) | — / 8 | 8: `n = calc1` missiles (`srvmissilea`, `srvmissileb` for a weapon class ≠ 1) fanned across the line to the target: offsets `(dx, dy)` from the unit to the target, start points stepped perpendicular to it from the point less half the fan (corrected 2026-10-20, note below), flags `0x820` (`0x10000` on the outer groups), activate `calc2`, `calc3` (or `n`) centre missiles | the creations' |
| 10 Jab | 5 `0x005DA8F0`: a target | 7 `0x005DB2D0` | to-hit `SKILLS_GetToHit` (and `MonAttackStats` for a monster), `edPct = calc1`, conversion `EType`/`calc4`, elemental roll, `ResolveAndQueue(SrcDam or 128)`, `DeliverQueued` | to-hit, defence, build, 1–2 |
| 70 Raise Skeleton | 15 `0x005C3070`: a target not in town that `0x00645510` accepts (a monster corpse in mode 12 with no state of the `DataTables+0x150` set, whose MonStats2 flag 7 and MonStats `+0x32` allow it; refined 2026-10-20, note below) | 31 `0x005C4B00` | § 7; first `0x005C2FF0` (note below) | none |
| 259 Fists of Fire | 23 `0x005D32F0`: target in melee range | 35 (P1.1 § 12) | finisher § 1 | as § 1 |
| 117 Holy Shield | 36 `0x005D0180`: inventory `0x0063C8F0(inv, 0)` (a shield); no skill record read, 0 without an inventory (note below) | 18 `0x005C9480` | 18: bit 6, `STATE_GroupClear(1)`, `STATE_ApplyTimed(aurastate, auralencalc)`, `SKILLS_ApplyAuraStats`, `0x005C6DC0` (`passivestat`s), stats 350/351, the `auraevent`s registered | none |
| 68 Bone Armor | — | 18 | as above; event 22 | none |
| 42 Static Field | — | 20 `sub_005C9800_SorSkillStaticMin` | `ForUnitsInRange(aurarangecalc, aurafilter, 0x005C96A0)` with calc1, calc2, elemental length, `EType` and the difficulty's `+0x40` (combat/0001) | callback's |
| 48 Nova, 44 Frost Nova, 130 Howl | — | 22 `0x005C9B50` | bit 6; `m = SrvMissileByCharge` (`srvmissilea`); `NovaAtUnit(unit, m, id, lvl, vel + calc1)` | the creations' |
| 54 Teleport | — | 27 `sub_005CA360_SkillTeleportDo` | P1.1 name; target point, room checks, `0x006229F0` | none |
| 56 Meteor | — | 28 `0x005CA3E0` | bit 6; `srvmissilea` at the target point (`MissileCreateAt`) when `0x0056E450` finds the target cell free for the missile's size (`COLL_WHTest(…, 5)`) | the creation's |
| 66 Amplify Damage | — | 30 `0x005C37C0` | bit 6; radius `aurarangecalc`, length `auralencalc` (divided by the difficulty's `+0x1C` when `0x005C3400` is true), `aurastat1..6` and the `auraevent`s into a block; `sub_0056E780_SkillForUnitsNearTarget(radius, CurseApplyCb)`: units within the radius of the target point in the near rooms (town rooms skipped with `aurafilter` bit `0x2000`) that pass `sub_0056B3E0_SkillUnitFilter`; the callback applies `auratargetstate` (`STATE_ApplyTimed`), the stats and the events | none |
| 98 Might | — | 65 `sub_005CF010_PalAuraDo` | stats/0002; the `aurastat` values too need the mana test for a player, `aurastate` must be above 0 (note below) | none |
| 102 Holy Fire | — | 66 `sub_005CF3A0_AuraHitDo` | stats/0002; the self block carries `passivestat1..5`; one `SKILLS_RollElemDamage` per run, its packet copied to each unit (note below) | 1 per run |
| 221 Raven | — | 114 `0x005C6910` | § 7 | none |
| 225 Firestorm | — | 117 `0x005C7160` | the class `SrvMissileByCharge`'s (`srvmissilea`, `firestormmaker`, for the stock row), refused outside the Missiles count before bit 6 (2026-10-21 note below); bit 6; with `calc1 > 0` one `SkillMissileCreate` of it, then `calc1 − 1` more by `MissileCreate` (flags `0x21`, callback `0x005C9290` with the index 0, 1, …) toward the target point | the creations' |
| 36 Fire Bolt, 251 Fire Trauma | — | — | `SKILLS_SrvDo`'s `srvmissile` (P1.2 § 2) | the creation's |

- [I] As above; each row's function is the `ST`/`DO` line of `handlers-scan.txt` and its draws the `DRAW` line.
  (fn:sub_005DB410_SkillDo08MultiShot@0x005DB410, fn:sub_005C37C0_SkillDo30Curse@0x005C37C0,
  fn:sub_005C7160_SkillDo117Firestorm@0x005C7160, fn:sub_0056E780_SkillForUnitsNearTarget@0x0056E780)
  *2026-10-20 (plan 0046 batch `sor`), emulated:* do 18, 20, 22 and 28 are reproduced up to their boundaries (`[C]`
  under ADR-0021; [skills/0008](0008-sorceress.md) §§ 7–8): do 18 up to `STATE_GroupClear(caster, aurastate; 1)`;
  do 20 up to `SKILLS_ForUnitsInRange`, whose block is `{calc2, calc1, the difficulty record's +0x40, elemental
  length, EType}` with the third word 0 when `game+0x70` is 0 (refinement: the row above has the `+0x40` term
  always); do 22 up to `NovaAtUnit`'s first creation, its `vel` being `0x00663270(cls, lvl)` (Missiles `Vel` +
  `VelLev · lvl / 8`) plus calc1; do 28 up to `COLL_WHTest(room, target point, Size, Size, 5)` inside
  `0x0056E450`. Do 27 is not emulated. Everything after those calls stays as read above, `[I]`.
  (fn:sub_005C9800_SorSkillStaticMin@0x005C9800, fn:sub_005C9B50_SkillDo22NovaAtSelf@0x005C9B50)
  *2026-10-20 (plan 0046 batch `ama`), emulated:* start 4, start 5, do 7 and do 8 are reproduced up to their
  boundaries (`[C]` under ADR-0021; [skills/0009](0009-amazon.md) §§ 3, 4, 6): start 4 makes **no skill-record
  test** and returns 1 for any non-player caster, ending at `0x00580310` for a player without an inventory; do 7 up to
  `COMBAT_MeleeHitTest(target, SKILLS_GetToHit, 0)` (a monster first at `MonAttackStats(ECX unit, EDX 8)`); do 8 up to
  its first `MissileCreate`, with two corrections to the row above: the step between the fanned missiles is
  **perpendicular** to the caster–point line (`0x0056D370` scales a short vector, `0x0056D3B0` rotates it to `(dy,
  −dx)` and halves it to a square of 3 or less), and the first start point is the target point less `step · n / 2`
  (truncating); `srvmissileb` (when ≥ 0) is taken for a caster with no inventory (weapon word 0); the test against 1
  itself (`cmp eax, 1` at `0x005DB52C`) stays `[I]`, since only word 0 is emulated (an armed caster ends at the
  inventory call). Everything after those calls stays as read above, `[I]`. (fn:sub_005DB410_SkillDo08MultiShot@0x005DB410,
  fn:sub_0056D3B0_VecPerpSmall@0x0056D3B0)
  *2026-10-20 (plan 0046 batch `nec`), emulated:* start 15, do 30 and do 31 are reproduced up to their boundaries
  (`[C]` under ADR-0021; [skills/0010](0010-necromancer.md) §§ 3–5): start 15 returns `0x00645510(target, 0)`, which
  also refuses a monster carrying a state of the `DataTables+0x150` bit-set (refinement of the Raise Skeleton row);
  do 30 up to `sub_0056E780_SkillForUnitsNearTarget`, its `aurastat1` test admitting −1 and its block carrying the
  `0x005C3400` flag at `+0x08` and an ItemStatCost-byte flag at `+0x0C`; do 31 calls `0x005C2FF0` before its record
  test (a player caster of class 3 ends there at `COMBAT_ApplyDamage` with a packet of `maxhp / 8`) and reads
  `pettype` signed, ending at `0x0061A270` before its spawn. Everything after those calls stays as read above, `[I]`.
  (fn:sub_005C37C0_SkillDo30Curse@0x005C37C0, fn:sub_005C2FF0_SkillClass3SelfHit@0x005C2FF0)
  *2026-10-20 (plan 0046 batch `pal`), emulated:* start 36, do 65 and do 66 are reproduced up to their boundaries
  (`[C]` under ADR-0021; [skills/0011](0011-paladin.md) §§ 3–4): start 36 reads **no skill record** and returns 0
  without an inventory word (`+0x60`), else ends at `0x0063C8F0(inventory, 0)`; do 65 and do 66 end at
  `AURA_ApplyToTarget(ECX &{game, caster, 0, &block}, EDX caster)` through `0x0056B740`, the 0x50-byte block holding
  the state, id, level, the end `SKILLS_NextPeriodicFrame + 1 − frame` and the stats with their values, the values
  evaluated unless the caster is a player whose stat 8 is below the cost `((lvl − 1) · lvlmana + mana) << (manashift &
  31)` (refinement of the Might row: the `aurastat` values are gated as well); do 65 takes `aurastat1..6` up to the
  first below 0 and needs `aurastate` above 0 (else its `auratargetstate` pass, `SKILLS_ForUnitsInRange`), and puts
  `passivestate` at `+0x48`; do 66 refuses an `aurastate` outside `[0, States count)` and takes `passivestat1..5` (the
  Holy Fire row). From the reading, `[I]`: do 66 makes one `SKILLS_RollElemDamage` per run, its packet copied to every
  unit of the target pass (correction of the Holy Fire row's "per unit"). Everything after those calls stays as read
  above, `[I]`. (fn:sub_005CF010_PalAuraDo@0x005CF010, fn:sub_005CF3A0_AuraHitDo@0x005CF3A0)
  *2026-10-21 (plan 0046 batch `bar`), emulated:* do 2 (the Kick row) is reproduced up to its boundaries (`[C]` under
  ADR-0021; [skills/0012](0012-barbarian.md) § 3). For a row with no `srvoverlay`, `auratargetstate` or `aurastate`
  (Kick) it sets bit 6 and ends at `COMBAT_DeliverQueued(game, unit; target, 0)`, or returns 0 without a target, as the
  row says; for rows that fill those columns its overlay and target-state blocks return 1 without delivering when
  `QueuedHitFind(caster, target)` finds no `+0xAC` node naming both (skills/0001 § 11 note). Everything after those calls stays as read above,
  `[I]`. (fn:SKILL_MeleeDeliverDo@0x0056F1F0)
  *2026-10-21 (plan 0046 batch `dru`), emulated:* do 114 (Raven) and do 117 (Firestorm) are reproduced up to their
  boundaries (`[C]` under ADR-0021; [skills/0013](0013-druid.md) §§ 3, 7). Do 114 ends at `SpawnOwnedMonster` with the
  block `{0, caster, class, 0, mode, 0, 0, pettype, petmax, mode}`, after refusing a `pettype` byte that is negative or
  at or past the PetType count (→ 0) **before** bit 6; do 117 takes its class from `SrvMissileByCharge`, refuses one
  outside `[0, Missiles count)` before bit 6, returns 0 **with** bit 6 set for `calc1 ≤ 0`, and ends at
  `SkillMissileCreate(game, class; caster, id, lvl, 0, 0, 0, 0, 0)` (the Firestorm row now says so). Everything after
  those calls stays as read above, `[I]`. (fn:sub_005C6910_SkillDo114Summon@0x005C6910,
  fn:sub_005C7160_SkillDo117Firestorm@0x005C7160)

### 6. Tier A: missile do, hit and damage functions

| Missile (row) | do | hit | dmg | Reading |
|---|---|---|---|---|
| `firebolt` (58) | 1 | — | — | P1.2 § 4; `ExplosionMissile` `fireexplode` has no server reader (P1.2) |
| `nova` (90), `frostnova` (119), `multipleshotarrow`/`bolt`, `firestorm` (457), `fistsoffirefirewall` (557) | 1 | — | — | P1.2 § 4 |
| `howl` (148) | 1 | 17 `0x005AAFB0` | — | a monster target without `auratargetstate`, whose level is below `owner level + Param2 + lvl`, flees (`0x005DDD00(owner; unit, skill, Param3 + (lvl−1)·Param4, Param5 + (lvl−1)·Param6)`, corrected by batch 9c below); returns 0 (no damage, no end) |
| `plaguejavelin` (43) | 3 | 2 `0x005A9D80` | — | do 3 (P1.2); hit 2: `HitSubMissile1` (`plaguejavcloud`) by `sub_005A9370_MissSubRing16` from the hit unit (or the missile): every `sHitPar2`-th of 16 directions at velocity `Param1 · 128` of the sub-missile row, a second ring at every `sHitPar1`-th (none when 0) at `Param2 · 128`, `sHitPar3` loops; returns 3 (end, damage) |
| `plaguejavcloud` (221) | 3 | — | — | do 3 |
| `bomb in air` (385) | 1 | 36 `0x005ABF70` | — | at the end of life only (`unit` 0): `MissileCreateAt(HitSubMissile1 = bomb on ground)` at its position, the new missile's `+0x28` = its own; returns 1 |
| `bomb on ground` (386) | 1 | 3 `0x005A9F90` | — | at the end only: hit 44 (`0x005A9E10`): `MISSILE_BuildDamage` (missile seed) and an area hit of radius `sHitPar1` when non-zero (else `max(aurarangecalc, 1)`; no owner test; batch 9c below) with the row's `HitFlags`/`ResultFlags` (`sub_0056BAD0_AreaHitAt` → `AreaHitUnit` per unit: defence roll, damage) |
| `meteorcenter` (101) | 1 | 14 `0x005AABB0` | — | with an owner, the area hit as hit 44 with radius `sHitPar1` when > 0 (else `max(aurarangecalc, 1)`), then `HitSubMissile1` (`meteorfire`) by `sub_005AAA90_MissSubRing18` at every `sHitPar2`-th of 18 offsets (`0x006E2598`/`0x006E2550`), range `Param3 + (lvl−1)·Param4` (batch 9c below) |
| `meteorfire` (240) | 5 `0x005AE520` | — | 3 `0x005AD220` | do 5: marks `0x40` on its cell each frame (`COLL_SizeMark`), loops its frame counter `Unit+0x44` between `SubStart` and `SubStop` with one `RangeB(missile seed, SubStop − SubStart)` per loop, then do 1; damage 3: one inline step of the missile seed, `low & 0x7F < dParam1` sets packet result `0x4000` |
| `firestormmaker` (458) | 23 `0x005AF790` | — | — | when the path flag `0x006505C0` (path `+0x34` bit 3) is set, `SubMissile1` (`firestorm`) at its position (flags 1, or 9 with `Param1` loops), then do 1 |
| `fistoftheheavensdelay` (233) | 1 | 22 `0x005ADD20` | — | (not tier A; the correction) the unit stored at `MissileData+0x28` (type) and `+0x2C` (guid; none: returns 0), `BuildDamage`, `MissileApplyAndAc`, then `ForUnitsInRange` with callback `0x005AB630` (`HitSubMissile1` chain) |
| grim wards (250, 253, 256) | 14 | 27 `0x005ABA00` | — | hit 27 returns 1 (end, no damage); do 14 runs skill do 30 every 6 frames (§ 8) |

- [I] As above (`MDO`/`MHIT`/`MDMG` lines of `handlers-scan.txt` give each function, `DRAW` its calls). The ring
  helpers create through `MissileCreate` only, so their draws are the creations' (P1.2 § 3).
  (fn:sub_005ABF70_MissHit36SubAtEnd@0x005ABF70, fn:sub_005AABB0_MissHit14AreaHitSub@0x005AABB0,
  fn:sub_005AE520_MissDo05Loop@0x005AE520, fn:sub_005AD220_MissDmg03Flag4000@0x005AD220)
  *2026-10-20 (plan 0046 batch 9b):* damage 3 is reproduced by emulation on returning cases (`[C]`: one inline step
  of the missile seed, `(low & 0x7F) < dParam1` signed, with a record); do 23's creation up to `MissileCreate` too
  (`[C]` under ADR-0021, accepted 2026-10-20, raised at the `lane/p46m2` review; the creation itself and do 1 after it
  not covered), and its test is `SubMissile1 != 0`, so a blank (−1) passes
  (run:2026-10-20-cat-emu-9b, [skills/0005 § 3, § 14](0005-missile-do-19-36-damage.md#3-do-21-23-26-32-one-sub-missile)).
  *2026-10-20 (plan 0046 batch 9c), corrections to the rows above:* **hit 3** returns 0 for any unit (no record
  test) and runs hit 44 only with unit 0 (`[C]`); **hit 44** takes any non-zero `sHitPar1` as its radius (a negative
  one included; 0 gives `max(aurarangecalc, 1)`) and has no owner test, and builds the damage with
  `MISSILE_BuildDamage(owner; m, 0, packet)` before any draw (`[C]` under ADR-0021, up to that call; the radius value,
  held in EDI at that call and not an argument, `[I]`); **hit 14** needs an owner (else 1, `[C]` under ADR-0021, up to
  `BuildDamage`), its radius is `sHitPar1 > 0 ? : max(aurarangecalc, 1)` (`[I]`: ESI at that call, the same ruling of
  the `lane/p46m3` review), and after the area hit (`[I]`) it passes `Param3 + (lvl−1)·Param4` to the 18-ring, which gives each
  fire flags `0x8001` and that range; **hit 17**'s flee call is `0x005DDD00(owner; unit, skill, Param3 + (lvl−1)·Param4,
  Param5 + (lvl−1)·Param6)`, two level-scaled values, not "its `0x004EFCB0` length" alone (`[C]` under ADR-0021, up to
  that call); **hit 2** also returns 3 without a record or with `HitSubMissile1 < 0` (`[I]`); **hit 22** finds its unit
  by `MissileData+0x28` (type) and `+0x2C` (guid) and returns 0 when there is none (`[C]`)
  (run:2026-10-20-cat-emu-9c, [skills/0006 §§ 4, 11, 14, 16](0006-missile-hit-1-29.md#4-hit-13-hit-3--44-hit-14)).
  *2026-10-20 (plan 0046 batch 9d), emulated:* **hit 2** returns 3 without a record or with `HitSubMissile1 < 0`, and
  3 when the ring refuses (no owner, class outside the Missiles count) (`[C]`, was `[I]` above); its ring's first
  creation is `{flags 0x1F and loops sHitPar3 when > 0, else 0x17; owner; source = the hit unit, or the missile at the
  end of life; cls; that source's position; skill, lvl; direction (0, 2); velocity Param1 << 7}` (`[C]` under
  ADR-0021, up to that `MissileCreate`; the later directions and the return 3 after it stay `[I]`); **hit 36**
  returns 0 for a unit and creates at the end of life only (`[C]`, up to `MissileCreateAt`); **hit 58** re-seeds the
  missile from its x and draws its two offsets before the creation (`[C]`, up to `MissileCreate`)
  (run:2026-10-20-cat-emu-9d, [skills/0007 §§ 5, 6](0007-missile-hit-31-59.md#5-hit-2-hit-59-and-hit-52-rings)).

### 7. Summons

```c
// fn:sub_005C6910_SkillDo114Summon@0x005C6910 (Raven: id, lvl; EDX unit), trimmed
cls = SkillSummonClass(id, lvl, &mode);              // Skills summon (+0xBC) and summode (+0xBF), or the monster's own
if (cls < 0 || !valid(rec->pettype)) return 0;
unit->c4 |= 0x40;
max = EvalCalc(rec->petmax);                          // into the spawn block
m = SpawnOwnedMonster(block);                         // position: the target point, or the block's
if (m) { m->c4 &= ~4; SetStat(m, 74, 0); SummonSetLevel(m, max(calc2, 1), lvl); SummonInitStats(m, id, lvl, 0); }
```

- [I] As above; do 31 (Raise Skeleton) is the same after the corpse test: the target's corpse is removed
  (`0x0061A270`, `UnitFree`), and after the spawn `SummonSetLevel(m, 0, lvl)` (level `owner level · 3/4 + lvl`,
  capped at the owner's level, below), `0x005C4430` (classes 363, 364), `SummonInitStats`, `0x005C40D0` (stat 349 as
  resistances) and `0x005B1900` (a target-list add, `.\GAME\Targets.cpp`). (fn:sub_005C4B00_SkillDo31RaiseSkeleton@0x005C4B00, fn:sub_005C49E0_SummonSetLevel@0x005C49E0)
- [I] `sub_005C49E0_SummonSetLevel(m, lvl, skillLvl)` (`EDX` the owner): `lvl ≤ 0` → `L = owner stat 12`, `lvl =
  min(max(L · 3 / 4 + skillLvl, 1), L)` (signed `/ 4`), left unset when `L` is 0; stat 12 = lvl;
  then the MonLvl row (`DataTables+0xB70`, 0x78 bytes, capped at the last row) adds defence (stat 31) and to-hit
  (stat 19) by difficulty (`game+0x6D`, 0/1/2) and by the expansion/ladder pair (`+0x6A`, `+0x74`).
  (fn:sub_005C49E0_SummonSetLevel@0x005C49E0)
- [I] `sub_005C4470_SummonInitStats(m, id, lvl, n)`: `passivestat1..5` with `passivecalc` added to the summon, then
  `aurastat1..6` into a list (each stat's `itemevent` registered on the summon), `aurastate` set, max life `+=
  maxhp · calc1 / 100` (64-bit when large), `sumskill1..5` with `sumsk*calc`, `sumumod` (`sub_005A4850_ModAppendApply`),
  `sumoverlay`, and `sub_005D6B60_MonEquipInit`. (fn:sub_005C4470_SummonInitStats@0x005C4470)
- [I] **The created unit's seed** is `sub_005B2F20_SpawnAtPos`'s (monsters/spawn): `SpawnOwnedMonster` calls it with
  mode `0x42` at the point, and once more with mode 4 when the first fails and the block's flag 4 is clear; the owner
  is set (`sub_0058F030_MonSetOwner`), `Unit+0xC4 |= 0x20000`, and the AI event 2 queued at `frame + 25`. No draw of
  its own besides the spawn. (fn:sub_0056D940_SpawnOwnedMonster@0x0056D940, fn:sub_005B2F20_SpawnAtPos@0x005B2F20)
- [I] **The pet limit** (`sub_0056D8D0` → `sub_00575D90_PetAdd(m, block+0x1C, max(block+0x20, 1))`, players only):
  `PetGroupClear(type)` removes, for every other pet type with the same non-zero `group` (`PetType+0x08`), the owner's
  pets of that type; `PetLimit(type, max)` stores `max` and, while the owner's count of the type is above it and the
  type is not 7, removes the first pet of the list (`0x005747B0`, `0x005750E0`); type 1 keeps its stored maximum unless
  `max` is 1. (fn:sub_00575D90_PetAdd@0x00575D90, 0x0056D92D, tbl:PetType.txt:group, tbl:Skills.txt:petmax)

### 8. Skill do 30 with a missile as its unit (missile do 14)

- [I] Missile do 14 calls `CallDoFunc(Param2 = 30, missile skill, missile level)` with the missile in `EDX` (P1.2 § 8).
  In `sub_005C37C0_SkillDo30Curse` the unit is then the missile: bit 6 is set on the missile, the calcs evaluate with
  the missile as the unit, `SKILLS_GetTargetXY` gives the missile's path target, and `ForUnitsNearTarget` applies the
  skill's `auratargetstate` to the units around that point. For the grim wards the skill is the creator's (150 Grim
  Ward: `auratargetstate` `terror`, radius `ln12`, length `par6`); no draw. Which unit filter bits a missile unit
  passes in `sub_0056B3E0_SkillUnitFilter` was not read. (fn:sub_005AEF70_MissDo14PeriodicDo@0x005AEF70,
  tbl:Skills.txt:auratargetstate)

### 9. Re-seed sites (rng/0002 § The other initialiser sites)

| Site | Writes | From | Draws after | Reached by |
|---|---|---|---|---|
| `0x005D40F0` (callback) | new missile `+0x20` | the creator's argument (ring 37's local low word) | none | `0x005D4150` (do 37) |
| `0x005D4680` (callback) | new missile `+0x20` | the argument (ring 143's local low word) | inline steps on the new seed for a zig-zag path: 2 at the start (a sign from `low & 1`, a step size `low % 3 +` a global), 1 more at every `*0x00741B0C`-th path point | `0x005D4870` (do 143) |
| `0x005C9290` (callback) | new missile `+0x20` | path `+0x10` (u16) + the argument (an index) | none; range capped at 77 | do 117 Firestorm, `0x005C7040`, `0x005C9300`, `0x005D1C30`, `0x005DB850`, monsters `0x005A29A0`, `0x005A2EE0`, `0x005A3490` |
| `0x005CD110` (callback) | new missile `+0x20` | path `+0x10` + the argument | 1 inline: `low % 100 > 19` → path type 10 | `0x005CD1C0` |
| `0x005AC040` (callback) | new missile `+0x20` | path `+0x10` | none | `0x005AC14B`, `0x005AC525` (missile hit functions) |
| `0x005A9820` | parent missile `+0x20` | `SubX + elapsed` | 2 `RangeB` | missile do 8, 10, 17, 25 |
| `0x005ACDF0` (hit 58) | missile `+0x20` | `SubX` | 2 `Range` | row 654 |
| `0x005AFB80` (do 28) | missile `+0x20` | `MissileData+0x28` | 2 `Range`, then `+0x28 = RNG_GetLow` | rows with do 28 |
| `0x005B04A0` (do 34) | missile `+0x20` | path X | 1 inline | rows with do 34 |
| `0x005B0640` (do 35) | missile `+0x20` | `+0x28` | 1 inline, `+0x28 = RNG_GetLow` | rows with do 35 |
| `0x005C8520` (do 146) | **caster** `+0x20` | `SkillEntry+0x18` (at the first period the word do 124 stored, 2026-10-21 note below) | `RNG_Range(10^6)` into `+0x18`, then up to 5 × 2 `Range` for a free point | Armageddon (`srvactivefunc` 146) |
| `0x00645390` | a unit's `+0x20` | a skill entry's `+0x18`/`+0x1C` (+7 on a repeat) | none | no reference in the image |
| `0x005C276A` | an item's seed | its own saved low word (restored on failure) | 1 inline | `sub_005C2740_ItemBuildSetV0` |
| local seeds | a stack seed | constant `0x53454953` (`0x005A3610`, `0x005A6B70`), stat 328 (`0x0059F940`, P1.2), the target and unit guids (`0x005CD910`, start 55), a stepped low word (do 37, 39, 41, 143) | as read | — |

- [I] The callbacks' names: `sub_005D40F0_MissCbReseedFromArg`, `sub_005D4680_MissCbReseedZigzag`,
  `sub_005C9290_MissCbReseedPathXPlusArg`, `sub_005CD110_MissCbReseedRoll`, `sub_005AC040_MissCbReseedPathX`; each is
  stored at the parameter block's `+0x54` and called by `MissileCreate` with the new missile in `ECX` and `+0x58` in
  `EDX` before the damage block (P1.2 § 2). (fn:sub_005D40F0_MissCbReseedFromArg@0x005D40F0,
  fn:sub_005AC040_MissCbReseedPathX@0x005AC040)
- [I] As above (`DRAW` lines: `SeedInit` and `lcg` per site; `REF` lines: the callbacks' only references are the
  `mov [ebp−…], callback` stores of their creators). So the server re-seeds a **unit** seed only at do 146 among the
  reached sites; every other server site re-seeds a missile or a stack seed. (fn:sub_005C8520_SkillDo146Armageddon@0x005C8520,
  0x005C8688–0x005C8694, fn:sub_005C9290_MissCbReseedPathXPlusArg@0x005C9290)
  *2026-10-21 (plan 0046 batch `dru`):* the `+0x18` word of the first Armageddon period is written at the cast by do
  124: one `RNG_Range(caster+0x20, 0x10000)` after its used-skill tests (`[C]` under ADR-0021, up to its
  `STATLIST_Alloc` or `StatListSetEnd`; [skills/0013](0013-druid.md) § 4), stored by `UnitSkillSet18(used node, r)`
  after unit event 5 is queued at `frame + Param4` (`[I]`, 0x005C8354–0x005C835C). Do 146 reads `SKILLS_GetUnitSkill(caster,
  id)`'s node, so the first period uses `r` when that node is the used node (`[I]`, not run).
  (fn:sub_005C8190_SkillDo124PeriodicState@0x005C8190)
- [I] `MissileData+0x28` is a per-missile stored seed word: written by `MISSDATA_SetSeedLow` (`0x0064A710`) at creation
  by do 37/143's rings, do 41, hit 36 and do 28/35 after their draws, read back by `MISSDATA_GetSeedLow` (`0x0064A730`)
  to re-seed. `+0x2C` holds a packed offset or a unit guid (`0x0064A760`/`0x0064A780`; hit 22 finds a unit by it).

### 10. Helpers P1.2 left unread

- [I] **`sub_0064FC60_PathDirection(x1, y1, x2, y2)`** (`ECX` out vector, `EDX` out index): with `dx`, `dy` the axis
  spans, `i = (minor · 127) / major` (0 when `major` is 0); the vector is `g_PathDirTable[i]`'s two components with the
  axes swapped when `dx` is the minor axis and negated by the signs of the deltas; the 64-direction index is the
  table's third word folded by the same octant rules (`(… + 8) & 0x3F`). The table is image data (`0x006EB7E0`, 128 ×
  12 bytes) that a reimplementation must carry. (0x0064FC60–0x0064FD69)
- [I] `sub_006505C0_PathFlag08(path)` = path `+0x34 & 8` (set by the path step; when it is set is the path code's,
  not read). `sub_00620C10_UnitSetPathTargetUnit(unit, target)` → `sub_00648B90_PathSetTargetUnit`: path `+0x58` =
  the unit, `+0x5C`/`+0x60` its type and guid (players, monsters and missiles only, else a fatal error).
  (fn:sub_006505C0_PathFlag08@0x006505C0, fn:sub_00648B90_PathSetTargetUnit@0x00648B90)
- [I] `sub_005A43B0_MissileOwnerUModEvent(game, owner, missile)`: for a monster owner, `sub_005A4270_UModEventRun(…, 5)`
  runs slot 5 of `g_UModEventFns` for each of its up to 9 unique mods; the slot is non-null for mods 19, 27 and 29
  (`UMOD5` line; the higher numbers hold no code address). Mod 29's function is `0x005A3610`: a local seed from the
  constant `0x53454953` and two `SkillMissileCreate` side missiles beside the created one. (data:g_UModEventFns@0x0073C0B8, 0x005A43B0–0x005A43D1)
- [I] `sub_00645F00_UnitRangedMissile(unit, &lvl)`: stat 157 > 0 → missile 27 (`magicarrow`) with its level, stat 158
  > 0 → 41, else 0; a player whose weapon class (`0x00623C60`) is neither 1 nor 7 gets −1, class 7 with neither stat 31. So
  `SKILL_AttackDo`'s `useAmmo` 0 applies to the magic-arrow stat only. (0x00645F00–0x00645FA1)
- [I] **`sub_005AD9D0_MissileEndHit`** has no call, no `jmp`, no immediate and no 4-byte pointer anywhere in the file
  (`REF 0x005AD9D0 calls=0 imm=0 ptrs=0`); with no computed-address idiom in the code read it is unreached.

### 11. The frame pass

```c
// fn:sub_005414D0_GameRunUnitEvents@0x005414D0 (ECX game), trimmed
lists = game->b8;  lists->bucket = frame & 63;
RunList(lists->a0c, every); RunList(lists->bucket[2], frame);     // missiles  (default 0x005ADCC0)
RunList(lists->a04, every); RunList(lists->bucket[0], frame);     // players   (default 0x00581220)
RunList(lists->a08, every); RunList(lists->bucket[1], frame);     // monsters  (default 0x005A7F80)
RunList(lists->a10, every); RunList(lists->bucket[3], frame);     // objects   (OBJ_EventDispatch)
RunList(lists->a14, every); RunList(lists->bucket[4], frame);     // fifth list (default 0x00562DA0, not read)
```

- [I] As above (`SITE frame pass order`; buckets at `+0x04 + 0x100 · k`). A bucket run fires only records whose
  frame equals the game frame. So in one game frame every missile's do function runs before any player's or monster's
  skill frame; a missile created by a player's or monster's do function is first stepped on a later pass, which frame
  exactly depends on how a new record enters the every-frame list (not read: a Phase 2 measurement).
  (0x005414EE–0x00541589, fn:sub_005ADCC0_MissileFrameEvent@0x005ADCC0, fn:OBJ_EventDispatch@0x00586AD0)

### 12. Routed questions from P1.1

- [I] **`repeat`** (`+0x05` bit 3) is set on exactly the three `startmana` rows (Inferno, Arctic Blast, Blade Fury;
  `ROWS skills repeat`). Its only flag tests by the bit-mask pattern are the client's (`0x004AEB32`, `0x004AF008`,
  `0x004C6417`), Missiles `SrcTown` at `0x005ADC43` and stat-list code at `0x00625129`/`0x006251CF` (another record);
  no server Skills reader. (`FLAG repeat` lines, data:g_BitMask32@0x006CE268)
- [I] **The ally test.** `SKILLS_StartUsedSkill` calls `sub_00554D20_SkillAllyTest(target, id)` with `ECX = [ebp+0xC]`
  the same `id` (`EBX`, whose record `EDI` it has just tested): it calls only when `TargetAlly` (`+0x07` bit 2) is clear,
  and the test returns false unless that bit is set. So this refusal never fires from `StartUsedSkill`; its other
  callers (`0x0056CCDB` in `SKILLS_TargetCheck`, `0x005AA04E` in a missile hit function) are where it matters.
  (0x0056FBB2–0x0056FBC4, 0x00554D56–0x00554D6B)
- [I] **`TgtPlaceCheck`** (`+0x08` bit 0; Resurrect, Resurrect2): one server reader, `sub_005FD470_MonSkillTargetOk`
  (`0x005FD4B9`): with the flag, the target must be dead (`+0xC4` bit 1) and its cell free for its pattern
  (`COLL_PatternTestBool(…, 0x3C01) == 0`). It is a monster AI target test (phase (5)), not a player start check.
- [I] **`weapsel`** (`+0x168`): no server read of a Skills `+0x168` (the 11 `[r+0x168]` operands are other records:
  `PlayerData+0x168` in the packet handlers, `0x006222A3`, …). **`leftskill`** (`+0x07` bit 6): one test, client
  (`0x004AA498`). Both are client choices on stock data. (`FLAG weapsel`, `FLAG leftskill`)
- [I] **The twelve unmapped `EType` stores** (P1.1 § 11): each of the 15 byte stores of `EType` that skills/0001's
  `CONV` lines list writes the cleared 0x70-byte packet's `+0x65` (the packet base is the `lea r,[ebp−N]` next to
  the function's `push 0x70`; `CONV` lines, `at_plus_0x65=15`): start functions 6, 7, 10, 16, 29, 32, 39, 56, do
  functions 7, 13, 67, 150 and the helpers `0x005D6200`, `0x005D8B10`, `0x005DA660`. So all 15 are conversion writers.
  (0x005C3175, 0x005DBD87, `handlers-scan.txt` `CONV`)
- [L] `Unit+0x38` stays open (§ Open questions).

### 13. Draws, seeds and the chaining reading (ADR-0014)

| Event | Entry | Draws found in this batch | Seed |
|---|---|---|---|
| progressive finisher | `COMBAT_PrgFinisher` → entries | 37, 39, 41, 143: 1 inline step each at entry; 38: `RangeB` ×2 (3 for type 10) on the attacker, then one defence roll per unit of the area on that unit's seed; 39, 41: local seeds (none on game state) | attacker; area units; local |
| stat-event handler | `UNIT_DispatchEvent` | 7, 14, 15, 16, 20, 30: 1 inline; 8, 9, 21, 31: 1 call; 3: the elemental roll | the handler's unit |
| state 52 | `PreventHealHook` | none | — |
| item cast | `ITEMSKILL_Cast` | none of its own | — |
| missile create (rings, Firestorm) | the callbacks of § 9 | re-seed of the new missile; `0x005D4680` and `0x005CD110` then step it | missile |
| missile frame | do 5, 28, 34, 35 | 1 `RangeB` per loop (5); re-seed then 2 `Range` (28), 1 inline (34, 35) | missile |
| missile damage 3 | `MISSILE_HitUnit` | 1 inline | missile |
| periodic (Armageddon) | do 146 | re-seed of the caster's seed from `SkillEntry+0x18` | caster |
| summon | `SpawnOwnedMonster` | the spawn's (monsters/spawn) | game seed |

- [I] Reading for Phase 2: the attacker's seed gains draws inside a finisher and in its `do…` event handlers
  (7–9, 14–16, 20) between the to-hit and the delivery steps, and in its `kill` handler 31; a defender's seed gains the
  `attacked…`/`damaged…` handlers' (3, 21) and its `killed` handler's (30). *Review 2026-10-20:* first written "7,
  14–16, 20" and "the defender's kill/killed handlers (30, 31)"; 8 and 9 run on the `do…` events too, and 31 is a `kill`
  handler on the killer (§ 3's table). These are the extra chained pairs the stat-event kind needs. A missile seed is
  private except where § 9 re-seeds it, after which the missile's draws are a function of the creator's value, not of
  the game seed. (`handlers-scan.txt` `DRAW`, fn:sub_005BF960_StatEv07Knockback@0x005BF960, fn:COMBAT_PrgFinisher@0x005D5220)

### 14. Boundary recommendation for Phase 2

- [I] **Event entry points to log** (each with the seeds it touches on entry and exit): `SKILLS_SrvStart` and
  `SKILLS_SrvDo` (the unit's seed; P1.1), `COMBAT_PrgFinisher` (the attacker's seed before the peek and after the last
  entry; the charge count), `sub_0059FA30_MissileCreate` (the owner's and the new missile's seeds, the class, the
  start, target and velocity; the callback, if any), `sub_005ADBB0_MissileDoFrame` (the missile's seed and position,
  windowed), `MISSILE_HitUnit` (the owner's, the missile's and the unit's seeds, the result), `UNIT_DispatchEvent`
  (the event id, each handler record's function number, the handler unit's seed before and after),
  `sub_0057D810_PreventHealHook`, `sub_0056D940_SpawnOwnedMonster` (the created unit and its seed) and
  `sub_00575D90_PetAdd` (removals), and the § 9 re-seed sites (the value passed to `RNG_SeedInit`). These are the
  functions of this batch and P1.1/P1.2 with an entry in the tables or a single caller, so a breakpoint each covers the
  event kind. (data:g_SkillDoFuncs@0x007322B0, data:g_StatEventFuncs@0x007325B0)
- [I] **Value oracles** (logged, not modelled): the frame on which a skill's do function runs (event code 1/2,
  `Unit+0x4E`; phase (4)); the AI's skill and target choice (phase (5)); every numbered function outside tier A
  (plan 0046), taking the logged exit seeds; the path planner's points (`sub_00649970_PathPlan`, path types 7 and 10)
  and the path step's cell list; `sub_0056B3E0_SkillUnitFilter` and `SKILLS_ForUnitsInRange`'s unit order, logged as
  the list of units the callback ran on; the pet chosen for removal. (fn:sub_0056B3E0_SkillUnitFilter@0x0056B3E0,
  fn:SKILLS_ForUnitsInRange@0x0056B7E0, fn:sub_00575850_PetLimit@0x00575850)
- [I] **Modelled in `tools/skills.py`**: the tier-A start and do functions of § 5 and missile functions of § 6, the
  progressive entries 36–41 and 143 (their draw counts are fixed by § 1), the stat-event handlers 1–31 (§ 3), state 52,
  `PathDirection` with `g_PathDirTable` read from the image (data, not code), the velocity step (P1.2 § 4) and the
  creation-time damage (P1.2 § 3). (fn:sub_0064FC60_PathDirection@0x0064FC60, data:g_PathDirTable@0x006EB7E0)
- [I] **Log windows** (ADR-0014 § Log volume): missile positions every frame only for a sampled window (for example the
  first 300 missiles of a session followed from creation to removal), creation, hit and end events for all; the
  frame pass of § 11 fixes the order inside a frame (missiles before players and monsters), so a window opened at a
  frame boundary sees each missile's step before the skill uses of that frame. The first step of a new missile (the
  insertion into the every-frame list) is measured in the window, not assumed.
  (fn:sub_005414D0_GameRunUnitEvents@0x005414D0)
- [I] **Chaining (ADR-0014)**: the kinds that draw on a shared seed are skill start (to-hit, build), skill do
  (delivery), the finisher (§ 1), missile create (P1.2's critical draws), the hit (to-hit), the stat-event handlers
  of § 3 on the handler unit's seed, and Armageddon's re-seed of the caster; each needs its 20 chained pairs. The
  missile seed's draws are private to the missile and chain only within it (§ 9). (fn:sub_0064A850_MissileCritRoll@0x0064A850,
  fn:sub_005C8520_SkillDo146Armageddon@0x005C8520)

## Kept outputs

`workspace/logs/skills/` (manifest `p45h-manifest.sha256`, one path base; `sha256sum -c` from that directory):
`handlers-scan.txt` `6c2a2739…` (the default sections, `python3 -I tools/skills_handlers_scan.py
workspace/install/app/game.exe`) and `handlers-rows.txt` `dd52e147…` (`… rows workspace/mpq/patch_d2/data/global/excel`),
both from `tools/skills_handlers_scan.py` sha256 `39b09e52…`. P1.1's `dispatch-scan.txt` and P1.2's `missiles-scan.txt`
are cited where the claim is theirs.

## Data touched

`tbl:Skills.txt:srvprgfunc1..3`, `prgstack`, `prgcalc1..3`, `srvmissilea..c`, `progressive`, `aurastate`, `aurastat1`,
`auratargetstate`, `aurarangecalc`, `auralencalc`, `aurafilter`, `auraevent1..3`, `auraeventfunc1..3`, `passivestat1..5`,
`summon`, `pettype`, `petmax`, `summode`, `sumskill1..5`, `sumumod`, `sumoverlay`, `calc1..3`, `Param2`, `MinDam`,
`HitShift`, `ItemTgtDo`, `TgtPlaceCheck`, `repeat`, `leftskill`, `weapsel`, `startmana`, `cltoverlaya`, `prgoverlay`;
`tbl:Missiles.txt:SubMissile1`, `HitSubMissile1`, `sHitPar1..3`, `Param1`, `Param2`, `dParam1`, `SubStart`, `SubStop`,
`Vel`, `VelLev`; `tbl:ItemStatCost.txt:itemevent1..2`, `itemeventfunc1..2` (stats 78, 81, 86, 108, 112–114, 117, 128,
134–139, 150, 155, 157, 158, 195–199, 201); `tbl:States.txt:srvactivefunc` (states 12, 52, 54, 172);
`tbl:PetType.txt:group`; `struct:MissileData+0x28`, `struct:MissileData+0x2C`, `struct:SkillEntry+0x18`,
`Unit+0x20`, `Unit+0x44`, `Unit+0xC4` bits 1, 6, `Unit+0xEC`/`+0xF0`, path `+0x10`, `+0x34`, `+0x58`–`+0x60`.

## Dead ends

- A first flag scan for `repeat`, `leftskill` and `TgtPlaceCheck` looked for an immediate mask and found nothing: the
  compiler tests these bits with a mask loaded from `g_BitMask32`; the kept scan matches both forms.
- `0x005C3070`, `0x005D32F0`, `0x005D0180`, `0x0056CAB0`, `0x005DA8B0` and `0x005ABA00` have no Ghidra function; they
  were read from objdump.

## Open questions

- [L] What `Unit+0x38` holds (SrvDo's sequence gate and do 35's parity); `0x005CDD30` reads `+0x38`, `+0x44`, `+0x48`
  of a unit as 8.8 frame counters, which suggests an animation field, not read further.
- [L] The frame on which a missile created by a player's or monster's do function first runs its do function (the
  every-frame list's insertion, `sub_005415E0`), for Phase 2's position windows.
- [L] `sub_0056B3E0_SkillUnitFilter` for a missile as the unit (the grim wards), and `0x005C3400`'s register argument
  in do 30.
- [L] The fifth unit-event list of the frame pass (default `0x00562DA0`).
- [L] What `SkillEntry+0x18` holds at Armageddon's first period, before do 146 has stored its `RNG_Range(1 000 000)`:
  the setter `0x00644560` has 85 call sites (objdump, review 2026-10-20) and the writers before the first period were
  not followed. The caster's seed after that period is a function of this word alone.
- [L] *2026-10-20 (Phase 1b):* what removes pets when `petmax` falls, for example extra skeletons when a skill shrine
  wears off (src:arreat-summit-skill-trees). § 7 reads the limit at `PetAdd` only; PetType `basemax`'s reader is
  not read.
- [L] Pet type 1's and type 7's special cases in `sub_00575850_PetLimit` (which rows they are), and where `SpawnOwnedMonster`'s
  block `+0x1C`/`+0x20` are filled by do 31 and 114 (register-passed; read as `pettype` and `petmax` by their use).
