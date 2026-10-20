# 0009 — Catalogue batch `ama`: the amazon start functions 4–10 and do functions 6–8 and 10–16

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 4–10 (`srvstfunc`, `g_SkillStartFuncs`) and do function 6, 7, 8
> and 10–16 (`srvdofunc`, `g_SkillDoFuncs`) of the amazon batch do: which Skills, Missiles and unit fields it reads,
> which states, missiles and monsters it creates, which draws it makes on which seed, what it returns, and which of
> that the emulator can confirm?
> **Date:** 2026-10-20   **Plan:** 0046 (Phase 1, batch `ama`)   **Status:** for review (`lane/p46m6`)

Static reading of the pinned `Game.exe` in Ghidra 12.1.2 (lane copy `workspace/ghidra-p46m6`, symbols replayed from
`re/symbols.csv`) and objdump, then emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged,
`286393aa…`) and the `ama` families of `tools/skills_catalogue_emu.py` (§ 2; run:2026-10-20-cat-emu-ama in
[experiments](experiments.md)). Skills columns are named as in [Skills](../../tables/Skills.md), Missiles columns as in
[Missiles](../../tables/Missiles.md). The machinery that calls a start or do function is
[skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart); the tier-A entries of this batch
(start 4, start 5, do 7, do 8) were read by plan 0045 in
[skills/0003 § 5](0003-handlers.md#5-tier-a-start-and-do-functions), and all four are emulated here too; the missile
functions the created missiles run are batches 9a–9d ([skills/0004](0004-missile-do-1-18.md)–[0007](0007-missile-hit-31-59.md)).
Do 6 passes the source path `.\SKILLS\SkillAma.cpp` (`0x006E32E4`) to `SKILLS_ForUnitsInRange`. Stock values come from
`workspace/logs/skills-cat-ama/rows.txt` (`excel_bin.py dump` of the 38 Skills rows whose `srvstfunc` is 4–10 or
whose `srvdofunc` is 6–8 or 10–16, by `rows.sh` beside it).

**Tag convention for this finding** (as skills/0008). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a
function entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site
(the return address at ESP), with a site control that fails every matched boundary case; (c) the model gives and the
checker compares every argument the claim uses (registers, stack words, and for a pointer into a frame the bytes it
points to), every byte written before the call that the claim uses (the unit's `+0xC4`, frame words of the batch
function when the boundary sits inside a helper it called, § 2), and the state of **the caster's and the target's
seeds** at the boundary (both, in every case). Each such claim names the boundary it ends at; **the callee and all
code after it are not covered** and keep `[I]` (from the reading), marked "after, `[I]`" in place, and what a callee
makes of a compared argument (an AR percent, a class, a guid to skip) is stated after the boundary (reverser
review-fixes 13). No claim rests on a callee-saved register that is not a boundary argument (ruling 1 of the
`lane/p46m3` review). A plain `[C]` rests on cases that return; a plain `[I]` is a code reading the emulator does not
reach. (run:2026-10-20-cat-emu-ama)

## Answer (summary)

- [C] **The batch.** 17 entries: start 4 `0x005DA8B0` to start 10 `0x005DB020` (seven, in address order); do 6
  `0x005DB1C0`, 7 `0x005DB2D0`, 8 `0x005DB410` and do 10 `0x005DB6D0` to do 16 `0x005DC1E0` (ten; do 9 `0x005D8E00`
  is not this batch's). Every one is `(ECX game, EDX unit; skill id, level)` with `ret 8`. All 17 are emulated.
  (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [C] **No draw before the boundaries.** No function of the batch steps the caster's or the target's seed before its
  boundary or return (8 300 cases, both seeds compared in each). Draws inside a boundary callee or after it are not
  covered: start 10's elemental `RNG_RangeB(caster seed, max − min)` comes after its `COMBAT_MeleeHitTest` (§ 4, after,
  `[I]`), and the hit tests, damage builds and creations draw in their callees. (run:2026-10-20-cat-emu-ama)
- [C] **Start 4** (the bows, crossbows and javelins: 18 rows) has no skill-record test: a caster that is not a player
  returns 1; a player with no inventory (`+0x60` = 0) ends at `sub_00580310_HandsRefresh(game, unit)` (ADR-0021,
  @0x005DA8CA); a player with one ends at the inventory call `0x0063C9B0` inside `UnitGetWeapon` (ADR-0021,
  @0x00535BF9). **Start 5** (Jab) returns whether `UNIT_GetTargetUnit` gives a unit, 0 without a record. (§ 3)
- [C] (ADR-0021; § 3) **Start 8** (Strafe) and **start 9** (Fend): the record, then the used skill (`UNIT_GetUsedSkill`,
  none → 0); start 8 the ammunition test of start 4 and `r = aurarangecalc`, start 9 `r = 0x00622870(unit) + 4` (a
  monster's MonStats2 `MeleeRng`; a player ends at the inventory call). Without a target unit, `NearestUnitInRange(game,
  caster; 0, 0, r, F, −1, &n)` with `n = 0`; with one, `0x0056BC80` → `SKILLS_ForUnitsInRange(game, caster; 0, 0, r,
  F | 0xA783, 0x0056BC70, &n, 0, file, 0x2E0)`; `F` is 3 for start 8 and `0x20003` for start 9. After, `[I]`: the
  count of units found clamped by the calcs into the used skill's node (`+0x18`), the target's type and guid
  (`+0x1C`, `+0x20`); start 8 then uses ammunition.
- [C] (ADR-0021; up to `COMBAT_MeleeHitTest`, `sub_005A4F50_MonAttackStats` or `UnitsHostile`'s `PlayerPairFlags`, § 4)
  **The melee starts and Jab.** Start 6 (Power Strike, Charged Strike), start 10 (Lightning Strike, after the used
  skill test) and start 7 (Impale, after `UnitsHostile`) and do 7 (Jab) zero a 0x70-byte packet and call
  `COMBAT_MeleeHitTest(game, caster; target, a, 0)` with `a = 0` for start 6 and 10 and `a = SKILLS_GetToHit(caster,
  id, lvl)` for start 7 and do 7: 0 for `lvl ≤ 0`, `(lvl − 1)·LevToHit + ToHit` (32-bit) when `ToHitCalc` is blank,
  else the calc. Do 7 with a monster caster ends first at `MonAttackStats(ECX caster, EDX 8)` with `a` already in its
  frame. After, `[I]`: `a` is the AR percent (combat/0001), so the `ToHit` columns of Power Strike (20/12),
  MonPowerStrike and MonIceSpear (20/15) on start 6 do not reach this test; the damage, `ResolveAndQueue`,
  `DeliverQueued`. (run:2026-10-20-cat-emu-ama `hit_ama`, fn:SKILLS_GetToHit@0x006449F0)
- [C] (ADR-0021; up to `SKILLS_ForUnitsInRange` @0x005DB2AD, § 5) **Do 6** (Inner Sight, Slow Missiles): with
  `auratargetstate` (`+0x82`, s16) in the States count and `aurastat1` (`+0x54`, s16) in the ItemStatCost count (a
  blank −1 refused), the block `{id, lvl, auralencalc, auratargetstate, aurastat1, aurastatcalc1}` and
  `ForUnitsInRange(game, caster; 0, 0, aurarangecalc, aurafilter, 0x005DB150, &block, 1, file, 0x20F)`. After, `[I]`:
  the callback hands each unit to `STATE_ApplyTimed`.
- [C] (ADR-0021; up to the first `MissileCreate`, the weapon's inventory call or `COMBAT_DeliverQueued`, § 6)
  **Creations.** Do 8 (Multiple Shot, Teeth, PrimePoisonball, Shock Wave) and do 10 (Guided Arrow, Bone Spirit) set bit
  6 of `+0xC4` first and need a target point. Do 8 (`n = calc1`) takes a step `(sx, sy)` perpendicular to the
  caster–point line (short vectors scaled up, then halved, truncating, until `sx² + sy² ≤ 3`) and passes its first
  creation the start point `point − (s·n)/2` (truncating) as target, `+0x44 = calc2`, and the flags of the first
  non-empty group of `g1 = (n − c3)/2` (outer, `0x10820`), `c3` (calc3, or `n` when 0; centre, `0x820`) and `n − g1 −
  c3` (outer); do 10 passes `{flags 0x20 (0x420 without a target unit), +0x0C the target unit, the point, +0x54
  callback 0x005DB6A0 when calc1 ≠ 0, +0x58 calc1}`. Both take `srvmissileb` (when ≥ 0) for a caster with no
  inventory; a caster with one ends at the inventory call inside `0x00623990`. Do 11 (Charged Strike, bit 6) and do
  14 (Lightning Strike, no bit 6) end at `COMBAT_DeliverQueued(game, caster; target, 0)` with a target unit, else
  return 0. After, `[I]`: do 8's other creations, group by group, each stepped by `(sx, sy)`; the weapon-class choice
  for an armed caster; the charged bolts and the lightning chain.
- [C] (ADR-0021; up to `UnitSetPathTargetUnit`, `InMeleeRange` or `NearestUnitInRange`, § 7) **Do 12** (Strafe) and
  **do 13** (Fend, Zeal, Fury) read the used skill's node: do 12 returns 0 at a count (`+0x18`) of 0; both look the
  last target up (`GameFindUnit(+0x1C type, +0x20 guid)`); found, do 12 ends at `UnitSetPathTargetUnit(caster,
  target)`, do 13 at `InMeleeRange(caster, target, 0)`; not found, `NearestUnitInRange(game, caster; 0, 0, r, F, guid,
  0)` with do 12's `r = aurarangecalc`, `F = 3` and do 13's `r = 0x00622870(caster) + 4`, `F = 0x20003`. After, `[I]`:
  one arrow or one hit per call, the count decremented, the next target recorded; **do 13 returns 0 on every path**.
- [C] (ADR-0021; up to `SpawnOwnedMonster` @0x005DC0DA or @0x005DC2BF, § 8) **Summons.** Do 15 (Dopplezon) and do 16
  (Valkyrie, a player caster only) take `summon` and the mode from `SkillSummonClass`, set bit 6 and pass the block
  `{0, caster, summon, 0, mode, 0, 0, pettype (0 when at or past the PetType count), petmax calc, w}` where the last
  word `w` (`+0x24`) is **the mode again** for do 15 and **the Skills record pointer** for do 16 (from objdump: no
  store fills it as a block word; the block spans the slot of `SummonClass`'s out-variable in do 15 and of the record
  pointer in do 16, § 8). After, `[I]`: what
  the spawn makes of `+0x24` (it is Hydra's end frame in skills/0008 § 6), the life, level, events and owner.
- [I] Not covered, from the reading: every callee boundary and what follows it (listed per function), what
  `0x0063C9B0` and `0x0064F380` return, and when the game runs these functions. (fn:sub_005DBC60_SkillDo13Fend@0x005DBC60)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005DA8B0` | `sub_005DA8B0_SkillSt04AmmoCheck` | (P1.3 name) start 4 | I |
| `0x005DA8F0` | `sub_005DA8F0_SkillSt05NeedTarget` | (P1.3 name) start 5 | I |
| `0x005DA940` | `sub_005DA940_SkillSt06Hit` | (P1.1 name) start 6 (Power Strike, Charged Strike, MonPowerStrike, MonIceSpear) | I |
| `0x005DAB40` | `sub_005DAB40_SkillSt07ImpaleHit` | (P1.1 name) start 7 (Impale) | I |
| `0x005DACD0` | `sub_005DACD0_SkillSt08Strafe` | start 8 | I |
| `0x005DAE30` | `sub_005DAE30_SkillSt09Fend` | start 9 | I |
| `0x005DB020` | `sub_005DB020_SkillSt10LightningStrike` | start 10 | I |
| `0x005DB1C0` | `sub_005DB1C0_SkillDo06AuraInRange` | do 6 (Inner Sight, Slow Missiles) | I |
| `0x005DB2D0` | `sub_005DB2D0_SkillDo07MeleeHit` | (P1.3 name) do 7 | I |
| `0x005DB410` | `sub_005DB410_SkillDo08MultiShot` | (P1.3 name) do 8 | I |
| `0x005DB6D0` | `sub_005DB6D0_SkillDo10GuidedMissile` | (9a name) do 10 | I |
| `0x005DB850` | `sub_005DB850_SkillDo11ChargedStrike` | do 11 | I |
| `0x005DBA40` | `sub_005DBA40_SkillDo12Strafe` | do 12 | I |
| `0x005DBC60` | `sub_005DBC60_SkillDo13Fend` | do 13 (Fend, Zeal, Fury) | I |
| `0x005DBE50` | `sub_005DBE50_SkillDo14LightningStrike` | do 14 | I |
| `0x005DC000` | `sub_005DC000_SkillDo15Dopplezon` | do 15 | I |
| `0x005DC1E0` | `sub_005DC1E0_SkillDo16Valkyrie` | do 16 | I |
| `0x0056C4E0` | `sub_0056C4E0_UnitAmmoTest` | `(ECX unit)`: 0 without a unit, 1 for a non-player, else `UnitGetWeapon` and the used skill (§ 3) | I |
| `0x00622870` | `sub_00622870_UnitMeleeReach` | `(unit)`, `ret 4`: a monster's MonStats2 `MeleeRng` (`+0x0E`) (0xFF: `0x0064F380`), a player's through `0x0063C9B0`, else 0; fatal path for no unit (§ 3) | I |
| `0x0056E510` | `sub_0056E510_UnitMeleeReachPlus4` | `(ECX unit)` → `0x00622870(unit) + 4` | I |
| `0x0056BC80` | `sub_0056BC80_CountUnitsInRange` | `(ECX game, EDX unit; x, y, r, filter)`, `ret 0x10`: `SKILLS_ForUnitsInRange` with `filter | 0xA783` and the counter callback, returns the count | I |
| `0x0056BC70` | `sub_0056BC70_CountUnitsCb` | `++*ctx[+0xC]`, returns 1 | I |
| `0x00623C60` | `sub_00623C60_UnitWeaponRecWord` | `(ECX unit)` → `0x00629FE0` of `0x00623990(unit, 1)`'s item (a word of its record), 0 without one (§ 6) | I |
| `0x0056D370` | `sub_0056D370_VecScaleShort` | `(ECX &x, EDX &y)`: `x² + y² < 4` → ×4; then `< 16` → ×2 (§ 6) | I |
| `0x0056D3B0` | `sub_0056D3B0_VecPerpSmall` | `(ECX &x, EDX &y)`: `(x, y) ← (y, −x)` halved, truncating, while the square exceeds 3 (§ 6) | I |
| `0x005DB150` | `sub_005DB150_SkillDo06UnitCb` | do 6's per-unit callback: `STATE_ApplyTimed` on a block from do 6's (read only) | I |
| `0x005DB6A0` | `sub_005DB6A0_MissCbAddStat25` | creation callback `(ECX missile, EDX v)`: stat 25 `+= v` when `v ≠ 0` (read only) | I |
| `0x00644500` | `sub_00644500_UnitSkillGet20` | `(node)` → node `+0x20` (assertion on null) | I |
| `0x006445E0` | `sub_006445E0_UnitSkillSet20` | `(node, v)`: node `+0x20 = v` (assertion on null) | I |

## Walkthrough

### 1. The table slots and the shared shape

- [C] `g_SkillStartFuncs[4..10]` and `g_SkillDoFuncs[6..8, 10..16]` are the Functions table's addresses (17 entries
  compared, `table_entries=17`; do 9 is `0x005D8E00`, outside the batch). (data:g_SkillStartFuncs@0x00732140,
  data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [I] Each function but start 4 tests `0 ≤ id < DataTables+0xBA0` and takes the Skills record `DataTables+0xB98 +
  0x23C · id`, 0 without it; the missile classes (`srvmissilea` `+0x48`, `srvmissileb` `+0x4A`, s16) are tested
  against the Missiles count `DataTables+0xB6C`. (fn:sub_005DB410_SkillDo08MultiShot@0x005DB410)
- [I] **Stock rows** (`rows.txt`): start 4 on 18 rows (the amazon bow and javelin skills, among them 12 Multiple Shot,
  22 Guided Arrow, 35 Lightning Fury, and the monster bows 339–343, 345); start 5 and do 7 on 10 Jab; start 6 on 14
  Power Strike, 24 Charged Strike, 344 MonPowerStrike, 347 MonIceSpear; start 7 on 19 Impale; start 8 and do 12 on 26
  Strafe (`srvmissilea` 682 `strafearrow`, `srvmissileb` 683 `strafebolt`); start 9 on 30 Fend; start 10 and do 14
  on 34 Lightning Strike; do 6 on 8 Inner Sight (`auratargetstate` 17, `aurastat1` 31 `armorclass`) and 17 Slow
  Missiles (87, 161); do 8 on 12 Multiple Shot (`srvmissilea` 213 `multipleshotarrow`, `srvmissileb` 214
  `multipleshotbolt`, calc3 2), 67 Teeth, 191 PrimePoisonball, 243 Shock Wave; do 10 on 22 Guided Arrow, 93 Bone
  Spirit, 211 MonBoneSpirit; do 11 on 24; do 13 on 30 Fend, 106 Zeal, 248 Fury; do 15 on 28 Dopplezon (`summon` 356,
  `pettype` 8); do 16 on 32 Valkyrie (`summon` 357, `pettype` 2, `ToHitCalc` set). (`rows.txt`,
  tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc)

### 2. Emulation: the `ama` families

The method is skills/0008's: each case calls the function with `ECX` = the game, `EDX` = the caster and the stack
`(id, lvl)`, and dumps the stack, the caster's and the target's seeds, the caster's `+0xC4` and the second argument's
slot. Emulated, not observed (new for this batch): `0x0056C4E0` with `UnitGetWeapon` up to its inventory call,
`0x00623C60` with `0x00623990` up to its inventory call, `0x00622870` with `sub_00451FE0_MonStats2Rec`, `0x0056E510`,
`0x0056BC80` up to its `ForUnitsInRange`, `SKILLS_GetToHit`, `GameFindUnit`, `UNIT_GetUsedSkill` and the node
getters, `0x0056D370`, `0x0056D3B0`, `sub_0056E620_SkillSummonClass` with `sub_0063EA70_SkillSummonRec`; skills/0008's
`UNIT_GetTargetUnit`, `SKILLS_GetTargetXY`, `UnitsHostile`, `SkillSrvMissileByCharge` and `SKILLS_EvalCalc` on
constant programs. Observed (new for this batch): `0x0063C9B0` and `0x0064F380` (the inventory calls),
`sub_00580310_HandsRefresh`, `COMBAT_MeleeHitTest`, `sub_005A4F50_MonAttackStats`, `COMBAT_DeliverQueued`,
`sub_00620C10_UnitSetPathTargetUnit`, `sub_00622C40_InMeleeRange`; skills/0008's stay declared (`MissileCreate`,
`NearestUnitInRange`, `SKILLS_ForUnitsInRange`, `SpawnOwnedMonster`, `PlayerPairFlags`, …), `0x00623990` excepted (it
runs emulated here). **New in the checker:** where a boundary sits inside a helper (the inventory call inside
`0x00623990` or `0x00622870`, the search inside `0x0056BC80`), the batch function's frame words written before it
(do 8's start point and step, do 10's count, target and point) are compared at their absolute stack address
(every function's `EBP` is `0x7FEFFFFC`).

- [C] Six families, **8 300 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 4 190 matched boundary cases
  (33 function, boundary and return-address triples, each a `site` line) (`check.txt`; run:2026-10-20-cat-emu-ama):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `start_ama` | start 4, 5, 8, 9 | 1 600 | ammunition result inverted (231); start 5 inverted (309); the filters swapped (335); reach without `+ 4` (155) | HandsRefresh @0x005DA8CA, @0x005DAD26; InvQuery @0x00535BF9 (in `UnitGetWeapon`), @0x006228FD (in `0x00622870`); MeleeInv @0x006228D2; NearestUnit @0x005DAD7B, @0x005DAEB3; ForUnitsInRange @0x0056BCBA (in `0x0056BC80`); returns 0, 1 |
  | `hit_ama` | start 6, 7, 10; do 7 | 1 600 | to-hit 0 (175); `lvl · LevToHit` (105); no hostility test (105) | MeleeHitTest @0x005DA9B4, @0x005DABCF, @0x005DB09A, @0x005DB371; PairFlags @0x00554297 (in `UnitsHostile`); MonAttackStats @0x005DB35D; returns 0 |
  | `aura_ama` | do 6 | 900 | state and stat swapped in the block (295); `auralencalc` as the radius (264) | ForUnitsInRange @0x005DB2AD; returns 0 |
  | `create_ama` | do 8, 10, 11, 14 | 1 800 | no short-vector scaling (51); floor for the halving (73); `srvmissilea` always (323); callback always (66) | MissileCreate @0x005DB5F1, @0x005DB628, @0x005DB661, @0x005DB7ED; InvQuery @0x006239BE (in `0x00623990`); DeliverQueued @0x005DB8B3, @0x005DBEAB; returns 0, 1 |
  | `node_ama` | do 12, 13 | 1 200 | do 12's guid as −1 (122); do 13's filter 3 (96) | NearestUnit @0x005DBAF4, @0x005DBD06; SetPathTarget @0x005DBB06; InMeleeRange @0x005DBCE5; InvQuery @0x006228FD; MeleeInv @0x006228D2; returns 0 |
  | `summon_ama` | do 15, 16 | 1 200 | `+0x24` zero (715); an out-of-range `pettype` refused (200) | SpawnOwned @0x005DC0DA, @0x005DC2BF; returns 0 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 34 of 34 pins): the hash offsets, the `CALC_Eval` jump
  table, the skills calc function count `0x007457AC` and `g_BitMask32` (as 9a–9d), the town tables (as `sor`). The
  count's scan matches every operand naming the address (a `PTR` or `moffs` store, an immediate, a read): 0 stores, 0
  immediates, 7 reads in `.text` (`ref_scan`, the condition of ruling 3 of the `lane/p46m5` review). Skills,
  Missiles, MonStats, MonStats2, the stat lists, rooms and units are scratch records written one field per field read.
- [C] **Inputs set in the memory spec** (ADR-0015, S1e review ruling 3): `g_pDataTables`, pointed at a scratch
  DataTables, is an input of every claim (the claims are maps from those bytes); the security cookie is written as in
  9a. No other image global is set. (run:2026-10-20-cat-emu-ama)
- [C] The smallest control, `nonorm` (51), decides the scaling of `0x0056D370` on the do 8 cases whose caster–point
  vector has `dx² + dy² < 16` (the writer puts half of the do 8 targets within 3 of the caster); every family has a
  control of 96 or more. (run:2026-10-20-cat-emu-ama `create_ama`)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills and
  Missiles columns `[C]` by layout; unit, path and skill-node offsets `[I]`, skills/0001, skills/0008), and nothing
  here says when the game runs these functions or on which seed state. (run:2026-10-20-cat-emu-ama)

### 3. Start 4, 5, 8 and 9: ammunition, a target, and the strafe and fend counts

```c
// fn:sub_0056C4E0_UnitAmmoTest@0x0056C4E0, trimmed
if (!unit) return 0;
if (unit->type != 0) return 1;                 // not a player
item = UnitGetWeapon(unit);                    // 0x00535BC0: unit->+0x60 inventory, 0 -> 0; else 0x0063C9B0(inv, …)
if (!item) return 0;
…                                              // the used skill and the item's ammunition (not read)
```

- [C] **Start 4** (`0x005DA8B0`; the same code as start 65, skills/0003 § 5): no skill test; `0x0056C4E0(unit)`
  non-zero → 1; zero → (ADR-0021, @0x005DA8CA) `HandsRefresh(game, unit)`. A player with an inventory ends at
  (ADR-0021, @0x00535BF9) `0x0063C9B0(inv, …)` inside `UnitGetWeapon`. After, `[I]`: `0x00580380` and 0 on the
  refusal path; the item and the used skill's ammunition. (run:2026-10-20-cat-emu-ama `start_ama`,
  fn:sub_005DA8B0_SkillSt04AmmoCheck@0x005DA8B0)
- [C] **Start 5** (`0x005DA8F0`): the record, then `UNIT_GetTargetUnit(game, unit) != 0`. (run:2026-10-20-cat-emu-ama
  `start_ama`, fn:sub_005DA8F0_SkillSt05NeedTarget@0x005DA8F0)
- [C] (ADR-0021; ends at `HandsRefresh` @0x005DAD26, the inventory call @0x00535BF9, `NearestUnitInRange` @0x005DAD7B
  or `SKILLS_ForUnitsInRange` @0x0056BCBA) **Start 8** (`0x005DACD0`): the record; `UNIT_GetUsedSkill(unit)` (the
  skill list `+0xA8`, its `+0x10`; none → 0); the ammunition test (0 → `HandsRefresh`); `r = aurarangecalc`; without
  a target unit `NearestUnitInRange(game, unit; 0, 0, r, 3, −1, &n)` (`n` = 0 at the call), with one
  `0x0056BC80(game, unit; 0, 0, r, 3)` → `ForUnitsInRange(game, unit; 0, 0, r, 3 | 0xA783, 0x0056BC70, &n, 0,
  0x006DAB88, 0x2E0)` with `n` = 0. After, `[I]`: `n` clamped (`min(calc1, calc3)` to `calc1`, as the reading gives
  it) into the node's `+0x18`; `+0x1C`/`+0x20` the first target's type and guid (`1`, −1 without one);
  `PLAYER_UseAmmo`; returns 1. (run:2026-10-20-cat-emu-ama `start_ama`, fn:sub_005DACD0_SkillSt08Strafe@0x005DACD0,
  tbl:Skills.txt:aurarangecalc)
- [C] (ADR-0021; ends at the inventory call @0x006228FD, `0x0064F380` @0x006228D2, `NearestUnitInRange` @0x005DAEB3 or
  `SKILLS_ForUnitsInRange` @0x0056BCBA) **Start 9** (`0x005DAE30`): the record; the used skill (none → 0); `r =
  0x00622870(unit) + 4` (`0x0056E510`), where `0x00622870` gives for a monster (type 1) its MonStats row's MonStats2
  row (`MonStatsEx`, `+0x18`, s16, in range) byte `MeleeRng` (`+0x0E`), 0 without a row, and for `0xFF` calls
  `0x0064F380(unit, inv, &v, −1, 1)`; for a player it calls `0x0063C9B0(inv, …)`; any other type 0; then the
  searches of start 8 with filter `0x20003` (`0x20003 | 0xA783` in the count). After, `[I]`: `0x0064F380`'s result
  gives 2 when its out-value is 6, else 0; no unit found → node `+0x18 = 0`, 1; else `+0x18 = min(n, calc1)`, the
  target's type and guid, 1. (run:2026-10-20-cat-emu-ama `start_ama`, fn:sub_005DAE30_SkillSt09Fend@0x005DAE30,
  fn:sub_00622870_UnitMeleeReach@0x00622870, 0x006228B5–0x006228E5, tbl:MonStats2.txt:MeleeRng)
- [I] Stock `MeleeRng` is 0 to 6 ([MonStats2](../../tables/MonStats2.md)), so the `0xFF` branch is reached by synthetic
  rows only. (tbl:MonStats2.txt:MeleeRng)
- [I] The `0xA783` bits added in the count's filter and what `NearestUnitInRange` does with the −1 are callee
  behaviour (skills/0008 § 5 reads the same slot as a guid to skip). (0x0056BC9C)

### 4. The melee hits: start 6, 7, 10 and do 7

- [C] (ADR-0021; ends at `COMBAT_MeleeHitTest` @0x005DA9B4) **Start 6** (`0x005DA940`): `UNIT_GetTargetUnit` (none → 0),
  then the record (none → 0), a zeroed 0x70-byte packet at `ebp−0x78`, `COMBAT_MeleeHitTest(game, caster; target, 0,
  0)`. (run:2026-10-20-cat-emu-ama `hit_ama`, fn:sub_005DA940_SkillSt06Hit@0x005DA940)
- [C] (ADR-0021; ends at `COMBAT_MeleeHitTest` @0x005DB09A) **Start 10** (`0x005DB020`): the record, the used skill,
  the target (each none → 0), the zeroed packet, `MeleeHitTest(target, 0, 0)`. (fn:sub_005DB020_SkillSt10LightningStrike@0x005DB020)
- [C] (ADR-0021; ends at `PlayerPairFlags` @0x00554297 inside `UnitsHostile`, or `COMBAT_MeleeHitTest` @0x005DABCF)
  **Start 7** (`0x005DAB40`): the record, the target, `UnitsHostile(game, caster; target)` (skills/0008 § 4's rule,
  emulated; 0 → 0), the zeroed packet at `ebp−0x7C`, `MeleeHitTest(target, SKILLS_GetToHit(caster, id, lvl), 0)`.
  (fn:sub_005DAB40_SkillSt07ImpaleHit@0x005DAB40, fn:sub_00554200_UnitsHostile@0x00554200)
- [C] (ADR-0021; ends at `MonAttackStats` @0x005DB35D or `COMBAT_MeleeHitTest` @0x005DB371) **Do 7** (`0x005DB2D0`):
  the record, the target, the zeroed packet, `a = SKILLS_GetToHit` into `[ebp−0xC]`; a monster caster (type 1) calls
  `MonAttackStats(ECX caster, EDX 8)` first; others `MeleeHitTest(target, a, 0)`.
  (fn:sub_005DB2D0_SkillDo07MeleeHit@0x005DB2D0)
- [C] **`SKILLS_GetToHit(unit, id, lvl)`** (emulated inside start 7 and do 7): `lvl ≤ 0` (signed `jg` at 0x00644A2A)
  → 0; `ToHitCalc` (`+0x1A0`) = −1 → `(lvl − 1)·LevToHit + ToHit` (`+0x19C`, `+0x198`; 32-bit, `lea eax, [edi−1]`
  at 0x00644A86); else the calc. (run:2026-10-20-cat-emu-ama `hit_ama`, fn:SKILLS_GetToHit@0x006449F0,
  tbl:Skills.txt:ToHit, tbl:Skills.txt:LevToHit, tbl:Skills.txt:ToHitCalc)
- [I] After the hit test (from the reading): on a hit (result bit 0) the packet gets `calc1` (do 7: the
  enhanced-damage word, skills/0003 § 5; start 7 through `COMBAT_RollPhysical`), the conversion when `+0x1DC` is
  set and `calc4 > 0`, `SKILLS_RollElemDamage`; start 10 instead rolls `SKILLS_GetElemMin + RNG_RangeB(caster+0x20,
  max − min)` into the packet; then `COMBAT_ResolveAndQueue(target, packet, SrcDam)` (start 6 SrcDam as is; start 7
  `0x80`; start 10 and do 7 SrcDam or `0x80` when 0) and, for do 7, `COMBAT_DeliverQueued(target, 0)`; start 7 on a
  hit also wears the weapon (`sub_005DAA40_SkillWeaponWear(game, calc2, calc3)` when it has durability). Every one
  returns 1 past the boundary. (0x005DA9B4–0x005DAA30, 0x005DABCF–0x005DACCB, 0x005DB09A–0x005DB144)
- [I] So, with the second argument as the AR percent (combat/0001), start 6 and start 10 hit-test with no skill
  to-hit at all: the `ToHit`/`LevToHit` of Power Strike (20/12), MonPowerStrike and MonIceSpear (20/15) do not reach
  this test; Impale (100/25) and Jab (10/9) do. Whether the attack mode adds them elsewhere is not read (Open
  questions). (`rows.txt`, 0x005DA9A5)

### 5. Do 6: Inner Sight and Slow Missiles

- [C] (ADR-0021; ends at `SKILLS_ForUnitsInRange` @0x005DB2AD) **Do 6** (`0x005DB1C0`): the record;
  `auratargetstate` (`+0x82`, `movzx` then s16 compare; pin 0x005DB1FF) in `[0, States count)` and `aurastat1`
  (`+0x54`, s16) in `[0, ItemStatCost count)`, else 0; the 24-byte block `{id, lvl, auralencalc, auratargetstate,
  aurastat1, aurastatcalc1}` at `ebp−0x20` (compared by content) and `ForUnitsInRange(game, caster; 0, 0,
  aurarangecalc, aurafilter (+0x50), 0x005DB150, &block, 1, 0x006E32E4, 0x20F)`. No bit 6. After, `[I]`: the callback
  builds `{context +0x04, unit, id, lvl, length, aurastat1, aurastatcalc1, auratargetstate}` and calls
  `STATE_ApplyTimed` (`0x0056E970`) per unit; returns 1. (run:2026-10-20-cat-emu-ama `aura_ama`,
  fn:sub_005DB1C0_SkillDo06AuraInRange@0x005DB1C0, fn:sub_005DB150_SkillDo06UnitCb@0x005DB150,
  tbl:Skills.txt:auratargetstate, tbl:Skills.txt:aurafilter, tbl:Skills.txt:aurastatcalc1)
- [I] Stock: Inner Sight puts state 17 `innersight` with `armorclass` (calc) on the units its filter (34 179) admits;
  Slow Missiles state 87 with `skill_handofathena` (161). (`rows.txt`, tbl:Skills.txt:auratargetstate)

### 6. Creations: do 8, 10, 11, 14

```c
// fn:sub_005DB410_SkillDo08MultiShot@0x005DB410, trimmed
unit->c4 |= 0x40;
if (!rec || !SKILLS_GetTargetXY(&x, &y)) return rec ? 1 : 0;
n = calc1;  dx = x - UnitX(unit);  dy = y - UnitY(unit);
VecScaleShort(&dx, &dy);  VecPerpSmall(&dx, &dy);              // the step (sx, sy)
x -= dx * n / 2;  y -= dy * n / 2;                              // signed, truncating
cls = srvmissilea;  if (UnitWeaponRecWord(unit) != 1 && srvmissileb >= 0) cls = srvmissileb;
if (cls < 0 || cls >= nMissiles) return 0;
c3 = calc3 ? calc3 : n;  g1 = (n - c3) / 2;  g3 = n - g1 - c3;
blk = {0x820 | 0x10000, unit, unit, cls, target (x, y), id, lvl, +0x44 calc2};
for g1: create, step;  flags &= ~0x10000;  for c3: create, step;  flags |= 0x10000;  for g3: create, step;
return 1;
```

- [C] (ADR-0021; ends at the inventory call @0x006239BE inside `0x00623990`, or the first `MissileCreate` @0x005DB5F1,
  @0x005DB628 or @0x005DB661) **Do 8** (tier A): bit 6 first; the record (none → 0); the target point (none → 1);
  `n = calc1`; `(dx, dy)` = the point less the caster's position (32-bit); `0x0056D370`: `dx² + dy² < 4` → both ×4,
  then `< 16` → both ×2; `0x0056D3B0`: `(a, b) = (−dx, dy)`, both halved (`cdq; sub; sar 1`, truncating) while `a² +
  b² > 3`, the step `(sx, sy) = (b, a)`; the start point `x0 = x − (sx·n)/2`, `y0 = y − (sy·n)/2` (truncating, pins
  0x005DB507, 0x005DB5D6); at the inventory call these five frame words (start point, step, `srvmissilea`) are
  compared. With no inventory the class is `srvmissileb` when ≥ 0, else `srvmissilea`; out of range → 0. The
  groups as above; the first creation is the first non-empty group's, block `{flags 0x10820 (outer) or 0x820
  (centre), owner and source the caster, cls, target (x0, y0), skill, lvl, +0x44 calc2}`; no group → 1.
  After, `[I]`: the further `n − 1` creations, each at the point stepped by `(sx, sy)`; a caster with an inventory
  takes `srvmissilea` when the weapon word is 1 (a bow, from the stock pair `multipleshotarrow`/`bolt`).
  (run:2026-10-20-cat-emu-ama `create_ama`, fn:sub_0056D370_VecScaleShort@0x0056D370,
  fn:sub_0056D3B0_VecPerpSmall@0x0056D3B0, tbl:Skills.txt:calc1, tbl:Skills.txt:calc2, tbl:Skills.txt:calc3,
  tbl:Skills.txt:srvmissileb)
- [C] (ADR-0021; ends at the inventory call @0x006239BE or `MissileCreate` @0x005DB7ED) **Do 10**: bit 6; the record;
  `t = UNIT_GetTargetUnit`; the target point (none → 0); `n = calc1`; the class as do 8 (frame words `n`, `t`, the
  point compared at the inventory call); the block `{flags 0x20, or 0x420 without t; owner and source the caster;
  +0x0C t; cls; target the point; skill, lvl; +0x54 0x005DB6A0 when n ≠ 0; +0x58 n}`. After, `[I]`: with a missile,
  `MISSDATA_SetSeedLow(m, t ? 1 : 2)` and `+0x2C` = the point less the caster's sub-position (packed y:x 16-bit);
  the callback adds `n` to the missile's stat 25; returns 1. (run:2026-10-20-cat-emu-ama `create_ama`,
  fn:sub_005DB6D0_SkillDo10GuidedMissile@0x005DB6D0, fn:sub_005DB6A0_MissCbAddStat25@0x005DB6A0)
- [C] (ADR-0021; ends at `COMBAT_DeliverQueued` @0x005DB8B3 or @0x005DBEAB) **Do 11** (bit 6 first) and **do 14** (no
  bit 6): the record, then a target unit (none → 0) and `COMBAT_DeliverQueued(game, caster; target, 0)`.
  (run:2026-10-20-cat-emu-ama `create_ama`, fn:sub_005DB850_SkillDo11ChargedStrike@0x005DB850,
  fn:sub_005DBE50_SkillDo14LightningStrike@0x005DBE50)
- [I] After do 11's call: `n = calc1` creations of `SkillSrvMissileByCharge`'s class from the target's position
  toward `(2·tx − ux, 2·ty − uy)` (the point beyond the target, mirrored from the caster), flags `0x21`, callback
  `0x005C9290` with the index (skills/0003 § 9's re-seed); returns 1. After do 14's: `NearestUnitInRange` from the
  target's position (`calc1` radius, filter 3, skipping the target's guid); with a unit, one creation `{flags 0x20,
  +0x08 the target, the class by charge, target = the caster's sub-position}` and `MISSDATA_SetSeedLow(m, calc2)`;
  returns 1, or 0 without a unit or class. (0x005DB8B3–0x005DBA3B, 0x005DBEAB–0x005DBFFD)

### 7. Do 12 and do 13: Strafe, Fend, Zeal and Fury

- [C] (ADR-0021; ends at `UnitSetPathTargetUnit` @0x005DBB06 or `NearestUnitInRange` @0x005DBAF4) **Do 12**: the
  record, the used skill (none → 0), `r = aurarangecalc`, the node's `+0x18` (0 → 0), `GameFindUnit(game; +0x1C type,
  +0x20 guid)`: found → `UnitSetPathTargetUnit(caster, target)`; else `NearestUnitInRange(game, caster; 0, 0, r, 3,
  guid, 0)`. (run:2026-10-20-cat-emu-ama `node_ama`, fn:sub_005DBA40_SkillDo12Strafe@0x005DBA40,
  fn:sub_00644500_UnitSkillGet20@0x00644500)
- [C] (ADR-0021; ends at the inventory call @0x006228FD, `0x0064F380` @0x006228D2, `InMeleeRange` @0x005DBCE5 or
  `NearestUnitInRange` @0x005DBD06) **Do 13**: the record, the used skill (none → 0), `r = 0x00622870(caster) + 4`
  (§ 3), the lookup: found → `InMeleeRange(caster, target, 0)`; else `NearestUnitInRange(game, caster; 0, 0, r,
  0x20003, guid, 0)`. (run:2026-10-20-cat-emu-ama `node_ama`, fn:sub_005DBC60_SkillDo13Fend@0x005DBC60)
- [I] After do 12's calls: no unit found → 1; else the target point, the class as do 8, one creation `{flags 0x21,
  the caster's sub-position, the point, skill, lvl, callback 0x005DB6A0, +0x58 calc2}`, the node's `+0x18` − 1, and
  while it stays above 0 the next nearest unit (skipping the one just shot) into `+0x1C`/`+0x20` with
  `SkillGetParam6` and `0x0056E210` (the next shot's timing, not read); returns 0 when the class is out of range or
  the count runs out, 1 otherwise. After do 13's: the hit of § 4 with `SKILLS_GetToHit` and `calc2`,
  `ResolveAndQueue(SrcDam or 0x80)`, `COMBAT_DeliverQueued(target, 4)`, the count − 1, the next target with
  `SkillGetParam2` and `0x0056E210`; **every path returns 0** (`xor eax, eax` at 0x005DBE3F, pinned).
  (0x005DBB06–0x005DBC4E, 0x005DBCE5–0x005DBE45)

### 8. Do 15 and do 16: Dopplezon and Valkyrie

- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005DC0DA) **Do 15**: the record; `SkillSummonClass(ECX caster, EDX 0;
  id, lvl, &mode, 0, 0)` (skills/0008 § 6's Skills path: `summon`, the mode `summode` 0..15 else 1) below 0 → 0;
  `pettype` (`+0xBE`, `movzx`) at or past the PetType count (signed compare, pin 0x005DC06C) becomes 0; bit 6; the
  block at `ebp−0x34`: `{+0x00 0, +0x04 caster, +0x08 summon, +0x0C 0, +0x10 mode, +0x14 0, +0x18 0, +0x1C pettype,
  +0x20 petmax (calc +0xC0), +0x24 mode}`. The last word is the `&mode` slot itself (`ebp−0x10`), which the block
  spans. (run:2026-10-20-cat-emu-ama `summon_ama`, fn:sub_005DC000_SkillDo15Dopplezon@0x005DC000)
- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005DC2BF) **Do 16**: the record, a player caster (type 0; else 0), the
  same summon and pet tests, bit 6, the block at `ebp−0x30` with the same words and `+0x24` = the Skills record
  pointer (the slot `ebp−0xC` the function stores it in at 0x005DC210, pinned). (run:2026-10-20-cat-emu-ama
  `summon_ama`, fn:sub_005DC1E0_SkillDo16Valkyrie@0x005DC1E0)
- [I] After the spawn: do 15 sets the owner, life and max life to `maxlife(caster) · calc3 / 100` (`MulDiv`), copies
  stat 12 (level), `SummonSetLevel`, `SummonInitStats(…, 0)`, queues event 7 at `frame + calc2`, applies mod `0x15`,
  overlay stat 171 and `0x005B1900`; do 16 `SummonSetLevel`, `SummonInitStats(…, calc2)`, cancels event 2 and
  queues it at `frame + 0x14`, sets state 93 and the owner and calls `0x005B1900`; both return 1 with a spawn, else 0.
  (0x005DC0DA–0x005DC1D4, 0x005DC2BF–0x005DC376)
- [I] Stock: Dopplezon spawns class 356 with `pettype` 8, Valkyrie 357 with `pettype` 2, both `petmax` 1 and
  `summode` 1. What `SpawnOwnedMonster` does with `+0x24` (Hydra's end frame, skills/0008 § 6) when it holds a mode
  (1) or a pointer is not read here (Open questions). (`rows.txt`, tbl:Skills.txt:summon, tbl:Skills.txt:pettype)

## Corrections to earlier findings

- skills/0003 § 5 (tier A), carried there as a dated note: start 4, start 5, do 7 and do 8 are now `[C]` up to their
  boundaries (ADR-0021), with three details: start 4 makes no skill-record test; do 8's step is perpendicular to the
  caster–point line (`0x0056D3B0` rotates it), not along it, and its start point is the point less half the fan;
  `srvmissileb` is taken for a caster whose weapon word is not 1, which includes a caster with no inventory.
- combat/0001 (skill melee hits), carried there as a dated note: not every skill hit passes `SKILLS_GetToHit`; start
  6 and start 10 pass 0 as `COMBAT_MeleeHitTest`'s second argument (§ 4).

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `srvmissilea`, `srvmissileb`, `auratargetstate`, `aurastat1`,
`aurastatcalc1`, `auralencalc`, `aurarangecalc`, `aurafilter`, `calc1`, `calc2`, `calc3`, `ToHit`, `LevToHit`,
`ToHitCalc`, `summon`, `pettype`, `summode`, `petmax`, `progressive` (do 11 and 14 after their calls, read only),
`SrcDam` (after, read only); `tbl:MonStats.txt:MonStatsEx`, `tbl:MonStats2.txt:MeleeRng` (the melee
reach byte); unit `+0x00`, `+0x04`, `+0x0C`, `+0x20` seed, `+0x2C` path (position; target point; the target link),
`+0x60` inventory, `+0xA8` skill list (`+0x10` used), `+0xC4` bit 6; unit skill node `+0x18`, `+0x1C`, `+0x20`.

## Dead ends

- The lane's first session was killed at 20:12 by the system's out-of-memory handler with six emulations run at
  once; it left the tool section and outputs uncommitted. The resumed lane regenerated the case files (identical),
  re-ran the six families one at a time (outputs byte-identical to the killed session's), and kept those.

## Open questions

- [L] Whether a Power Strike hit (or a monster row of start 6) adds the row's `ToHit` elsewhere (the attack mode's
  own hit, or `SKILL_AttackDo` run beside the start function), since start 6 and 10 pass 0 to the hit test (§ 4).
- [L] What `SpawnOwnedMonster` does with a block `+0x24` that holds the mode (do 15) or the Skills record pointer
  (do 16) (§ 8); a harness Valkyrie or Dopplezon would show whether either expires by it.
- [L] What `0x0063C9B0` (the inventory call of `UnitGetWeapon`, `0x00623990` and `0x00622870`) and `0x0064F380`
  return, and what `0x00629FE0`'s word is (the weapon class that picks arrow or bolt missiles).
- [L] Everything after each boundary (§§ 3–8), for a later batch or the harness.
