# 0005 — Catalogue batch 9b: missile server do functions 19–36 and damage functions 1–14

> **Subsystem:** skills/catalogue
> **Question:** what does each missile server do function 19–36 (`pSrvDoFunc`, `g_MissileSrvDoFuncs`) and each
> missile damage function 1–14 (`pSrvDmgFunc`, `g_MissileSrvDmgFuncs`) do: which Missiles and Skills columns and
> `MissileData` words it reads, which missiles and units it creates or touches, which draws it makes on which seed,
> and which of that the emulator can confirm?
> **Date:** 2026-10-20   **Plan:** 0046 (Phase 1, batch 9b)   **Status:** reviewed 2026-10-20 (accept with fixes, `lane/p46m2`; 9c–9d follow)

Static reading of the pinned `Game.exe` in Ghidra 12.1.2 (lane copy `workspace/ghidra-p46m2`, symbols replayed from
`re/symbols.csv`) and objdump, then emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged
from batch 9a, `286393aa…`) and the 9b families of `tools/skills_catalogue_emu.py` (§ 2;
run:2026-10-20-cat-emu-9b in [experiments](experiments.md)). Missiles columns are named as in
[Missiles](../../tables/Missiles.md), Skills columns as in [Skills](../../tables/Skills.md), packet fields as in
`re/types/combat.h` (`DamagePacket`). The machinery (creation, the frame step, the hit and its damage call) is
[skills/0002](0002-missiles.md); batch 9a's functions are [skills/0004](0004-missile-do-1-18.md). Stock values below come
from `workspace/logs/skills-cat-9b/rows.txt` (`9152e7da…`, `excel_bin.py dump` of the batch's 43 rows) and, for Skills,
`skills.txt` cells named in place.

**Tag convention for this finding.** A claim marked **[C] (ADR-0021)** rests on emulated cases that end at an observed
boundary (a declared callee's entry), under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md) (accepted by
the owner 2026-10-20): (a) nothing is patched and each boundary is a function entry reached by the program's own flow;
(b) the checker asserts per case the boundary and its call site (§ 2, with a site control); (c) the model gives and the
checker compares every argument, written byte and seed state the claim uses (do 30's untouched seeds were checked at
the review from the kept outputs, § 6). Each such claim names the boundary it ends at; **the callee and all code after
it are not covered** and keep `[I]` (from the reading), marked "after, `[I]`" in place. A plain `[C]` rests on cases
that return; a plain `[I]` is a code reading the emulator does not reach. Raised at the `lane/p46m2` review without a
re-run. (run:2026-10-20-cat-emu-9b)

## Answer (summary)

- [I] **The batch.** 30 entries: do 19–36 (17 numbers; 24 is 23's function `0x005AF790` and unused) and damage 1–14
  (13 numbers; 6 is unused). Do 23 and damage 3 are tier A (skills/0003 § 6); both are emulated here too. Every do
  function ends in do 1 (`sub_005AE1F0_MissileMoveCollide`), except do 20 and 30 (return 1 after do 1), do 32 (ends in
  do 7) and do 34 (ends in do 3); a missing record returns 2. The damage functions are
  `(ECX game, EDX missile; unit, packet)`, `ret 8`, and change only the packet, the missile's seed and (damage 8) the
  unit's overlay. (data:g_MissileSrvDoFuncs@0x0073C768, data:g_MissileSrvDmgFuncs@0x0073C960, `static.txt` tables,
  fn:sub_005AF880_MissDo25ScatterBySkill@0x005AF880)
- [C] **Damage functions (all but 8's overlay call are reproduced on returning cases).** 1: `v = min(DmgCalc1, 100)`
  (when > 0) percent of the physical damage moves to the missile's `EType` field; 12: the same share plus a fresh roll
  of the `EType` element replaces the packet's damage (the fields `PacketClearDamage` zeroes, § 13); 2: freeze length = `MulDiv(stat 56, max(dParam1, 0), 100)`, cold
  length 0; 3: one step of the missile seed, `low & 0x7F < dParam1` sets result `0x4000`; 4: freeze = cold length, cold
  0; 10: freeze = cold length; 5: the `EType` roll, plus `dParam1` % of it against undead and `dParam2` % against
  demons; 13: against a monster only, the owner's stat 25 percent added to the physical damage, then 5; 7 and 9: stun
  length = `dParam1`, else Skills `Param1 + (lvl − 1)·Param2` (7) or `Param2` (9), hit class `0x60`; 11: poison length
  = `MissileData+0x28 − frame` when in `[10, ELen(owner)]`, else poison 0; 14: knockback (result `|= 0x8`, a 16-bit OR at `+0x04`) on
  `RNG_Range(missile seed, 100) <` a chance from `dParam1`, `dParam2` and the target's MonStats2 `small`/`large`.
  (run:2026-10-20-cat-emu-9b `dmgconv`, `dmgelem`, `dmgpkt`, `knock`; §§ 13–16)
- [C] (ADR-0021; each up to its `MissileCreate`, `PathPlan`, do-3 or `COLL_CellTestAt` boundary, §§ 6–9) **Draws.**
  Do 28 re-seeds the missile seed to `(MissileData+0x28, 666)`, draws two `RNG_Range(2r + 1)` offsets and stores the
  new low word in `+0x28`, all before its `MissileCreate`; do 30 draws two `RNG_Range(2·Param2 + 1)` offsets on the
  **target unit's** seed (the unit `MissileData+0x28/+0x2C` names), leaving the missile's, the owner's and a decoy's
  seeds as they were (on its path-less cases only: with a path the re-target boundary comes first); do 34
  re-seeds to `(SubX, 666)` and steps once to pick a sub-missile on every frame from `Param1` on; do 35 re-seeds to
  `(MissileData+0x28, 666)` and steps once for the turn's sign; do 25 goes through 9a's
  `sub_005A9820_MissSubNearReseed`. No other do function of the batch draws before its boundary (in the families
  whose cases write no seed, no unit seed is read: 0 undeclared reads). Draws after a boundary are not covered. `[C]` on returning
  cases: damage 3 (one inline step), damage 5/12/13 (one `RNG_RangeB` per element roll whose two stats are ≥ 1),
  damage 14 (one `RNG_Range(100)` when the chance is above 0), all on the missile's seed. (§ 3, §§ 7–9, §§ 13–16, run:2026-10-20-cat-emu-9b)
- [C] (ADR-0021; up to the first creation call, §§ 3, 4, 10) **Sub-missile makers.** Do 21 (distraction) `MissileCreateAt` of `SubMissile1` on a path-flag-8 frame,
  then do 20; do 22 (lightning trailing javelins) two `SubMissile1` at offsets `±(−dy, dx)` perpendicular to its path
  target, set while `elapsed < 2`; do 23 (firestormmaker, sucfireball) one per flag-8 frame with `Param1` loops; do 26
  (vines) `MissileCreateAt` every `Param1` frames; do 31 (wake of destruction, baal cold maker) two at `±(+0x28, +0x2C)`;
  do 32 (tiger fury) one per flag-8 frame, then do 7. Do 21, 22, 23, 25 and 26 test `SubMissile1 != 0`, so a blank
  (−1) passes; the others test `≥ 0`. The second creation of do 22 and do 31 follows the first boundary and is `[I]`.
  (§ 3, § 4, § 10, run:2026-10-20-cat-emu-9b)
- [C] (ADR-0021; up to the re-target, `MISSILE_HitUnit`, `UnitSetStat` or do-1 boundary, §§ 5, 6, 11) **Owner-bound
  missiles.** Do 20 (blade creeper) re-targets its path to the owner's position (`0x005A99E0`) and sets frames left to
  10 while the owner is alive, else ends itself with an end-of-life hit; do 30 (rabies plague) re-targets and ends
  itself the same way (it does not reset the frames left; it ends on `left < 0`) and spreads `SubMissile1` from the
  infected unit; do 29/33 (recycler delays) at `elapsed == Param1` heal the owner's life/mana by
  `MulDiv(max, calc1, 100)`, capped at the maximum. The return values after those calls (1 or 2) are `[I]`. (§ 5,
  § 6, § 11)
- [C] (ADR-0021; up to `MISSILE_BuildDamage`, the units-in-range call and `QUESTS_IsActive`, §§ 12, 17, 18) **Periodic
  area and control missiles.** Do 27 (tornado) builds its damage packet every `Param1` (or
  `calc4`) frames; do 19 (radament death) runs Redemption's corpse callback on the units around it while 2 ≤ frames
  left ≤ 24 and once more, without the chance roll, at 1 (the roll and the heal are the callback's, `[I]`); do 36
  (baalfx control) at ≤ 100 frames left sets `+0x28 = 1` and asks whether quest 36 is active (the spawn of `tyrael3`,
  class 521, and the room pin after it are `[I]`). (§ 12, § 17, § 18, run:2026-10-20-cat-emu-9b)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005B0940` | `sub_005B0940_MissDo19Redemption` | do 19 | I |
| `0x005AF540` | `sub_005AF540_MissDo20FollowOwner` | do 20 | I |
| `0x005AF590` | `sub_005AF590_MissDo21SubThenDo20` | do 21 | I |
| `0x005AF620` | `sub_005AF620_MissDo22SideTrails` | do 22 | I |
| `0x005AF790` | `sub_005AF790_MissDo23SubPerCell` | (P1.3 name) do 23 and 24 | I |
| `0x005AF880` | `sub_005AF880_MissDo25ScatterBySkill` | do 25 | I |
| `0x005AF980` | `sub_005AF980_MissDo26PeriodicSubAt` | do 26 | I |
| `0x005AFA30` | `sub_005AFA30_MissDo27PeriodicAreaHit` | do 27 | I |
| `0x005AFB80` | `sub_005AFB80_MissDo28Reseed` | (P1.3 name) do 28 | I |
| `0x005AFD70`, `0x005AFEC0` | `sub_005AFD70_MissDo29OwnerLife`, `sub_005AFEC0_MissDo33OwnerMana` | do 29, do 33 | I |
| `0x005B0010` | `sub_005B0010_MissDo30Contagion` | do 30 | I |
| `0x005B01F0` | `sub_005B01F0_MissDo31SidePair` | do 31 | I |
| `0x005B03E0` | `sub_005B03E0_MissDo32SubThenDo07` | do 32 | I |
| `0x005B04A0` | `sub_005B04A0_MissDo34Reseed` | (P1.3 name) do 34 | I |
| `0x005B0640` | `sub_005B0640_MissDo35Reseed` | (P1.3 name) do 35 | I |
| `0x005B0A40` | `sub_005B0A40_MissDo36BaalFx` | do 36 | I |
| `0x005AD050`, `0x005AD0F0` | `sub_005AD050_MissDmg01ConvertPct`, `sub_005AD0F0_MissDmg12ConvertAll` | damage 1, 12 | I |
| `0x005AD1B0` | `sub_005AD1B0_MissDmg02FreezeLen` | damage 2 | I |
| `0x005AD220` | `sub_005AD220_MissDmg03Flag4000` | (P1.3 name) damage 3 | I |
| `0x005AD290`, `0x005AD2B0` | `sub_005AD290_MissDmg04ColdToFreeze`, `sub_005AD2B0_MissDmg10FreezeCopy` | damage 4, 10 | I |
| `0x005AD2F0`, `0x005AD5C0` | `sub_005AD2F0_MissDmg05UndeadDemon`, `sub_005AD5C0_MissDmg13OwnerEd` | damage 5, 13 | I |
| `0x005AD3E0`, `0x005AD4A0` | `sub_005AD3E0_MissDmg07Stun`, `sub_005AD4A0_MissDmg09StunParam2` | damage 7, 9 | I |
| `0x005AD450` | `sub_005AD450_MissDmg08Overlay` | damage 8 | I |
| `0x005AD530` | `sub_005AD530_MissDmg11PoisonLeft` | damage 11 | I |
| `0x005AD630` | `sub_005AD630_MissDmg14KnockBySize` | damage 14 | I |
| `0x005A8C70` | `sub_005A8C70_MissileRollEType` | the roll of the missile's `EType` into the packet (§ 13) | I |
| `0x005A91C0`, `0x005A9270` | `sub_005A91C0_PacketClearDamage`, `sub_005A9270_PacketAddEType` | clear the damage fields; add to the `EType` field | I |
| `0x0064B0C0` | `sub_0064B0C0_MissileGetEType` | Missiles `+0xE4` (`EType`) of a class, 0 out of range | I |
| `0x004E6CA0` | `sub_004E6CA0_SkillParamByLevel` | `(ECX skill, EDX lvl)` → `Param1 + (lvl − 1)·Param2`, 0 when invalid or lvl ≤ 0 | I |
| `0x005A99E0` | `sub_005A99E0_MissRetargetOwner` | `(ECX game, EBX m)`: path target = the owner's room and position | I |
| `0x00650BE0` | `sub_00650BE0_PathTargetRoomXY` | `(path, unit, room, x, y)`: `0x00650910(room, x, y)`, then path `+0x28` = 0 | I |
| `0x0056DDE0` | `sub_0056DDE0_UnitsInRangeCall` | builds a 0x24 block for `0x0056DCC0` (units around a point, a callback each) | I |
| `0x005AD8F0`, `0x005AD910` | `sub_005AD8F0_RedemptionChanceCb`, `sub_005AD910_RedemptionAlwaysCb` | `0x005D0C40(unit, 124, lvl, 0 / 1)` | I |
| `0x005D0C40` | `sub_005D0C40_RedemptionCorpse` | Redemption's per-corpse step (read only, § 17) | I |
| `0x0058E920` | `sub_0058E920_BaalFxSpawnTyrael` | a free spot near the missile, then monster 521 (§ 18) | I |
| `0x00621E40` | `sub_00621E40_UnitSetOverlayStat` | `(unit, overlay, 0)`: stat 178 (`0xB2`) = the overlay on the unit's flag-`0x80` list (read only) | I |

## Walkthrough

### 1. The table slots and the shared shape

- [I] `g_MissileSrvDoFuncs[19..36]` and `g_MissileSrvDmgFuncs[1..14]` are as the Functions table (`static.txt`: 24 and
  23 share `0x005AF790`; damage 6 is `sub_005AD3A0_MonSetNoDeathDrop`, a function no Missiles row names, and 0 and 15
  are null). Do functions are `(ECX game, EDX m) → 1 keep / 2 free`; each reads its record as
  `DataTables+0xB64 + 0x1A4 · Unit+0x04` after `0 ≤ class < DataTables+0xB6C`, and its Skills row, where it needs one,
  as `DataTables+0xB98 + 0x23C · skill` after `0 ≤ skill < DataTables+0xBA0` (`MISSDATA_GetSkill`). (`static.txt`,
  0x005AF880–0x005AF8FC)

### 2. Emulation: the 9b families, with the call site asserted

The method is batch 9a's (skills/0004 § 2): a case runs the function's own code on a declared memory image, and a
case that reaches a declared callee's entry (`observe`) ends there with its registers and the 64 bytes at ESP. New in
9b, as the `lane/p46m1` review asked: **the checker asserts the return address at ESP** of every observed boundary
(the call site plus the call's length, or EmuBoundary's sentinel `0x7EEE0000` for a tail jump) and fails a case that
reaches another boundary, another site, or returns when a boundary is predicted (and the reverse). A built-in site
control re-checks every matched boundary case with the expected return address changed; every one fails. Each family
has **two** negative controls on different claims, and each must fail. The boundaries added for 9b:
`0x0056EDE0` MissileCreateAt, `0x00650BE0` the owner re-target, `0x005ADF10` MISSILE_HitUnit, `0x005A89A0`
MISSILE_BuildDamage, `0x00627260` UnitSetStat, `0x00621E40` the overlay set, `0x005ADB00` JustHitState, `0x0064EBA0`
COLL_SizeUnmark, `0x005AE780` do 7, `0x005AE480` do 3, `0x005444B0` QUESTS_IsActive, `0x0056DDE0` the units-in-range
call, and (do 21's cases only) `0x005AF540` do 20; 9a's nine stay declared.

- [C] Thirteen families, **17 100 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped
  other than at a boundary; every negative control fails, and the site control fails on all 8 762 matched boundary
  cases (40 function, boundary and return-address triples, each listed as a `site` line) (`check.txt` `7b5c1f6f…`; run:2026-10-20-cat-emu-9b):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `create9b` | do 21, 22, 23, 26, 32 | 1 500 | `SubMissile1 > 0` for `!= 0` (92); do 22's negation dropped, do 23's loops dropped (207) | MissileCreateAt @0x005AF612, @0x005AFA0E; MissileCreate @0x005AF749, @0x005AF859, @0x005B047B; do 1 @0x005AF772, @0x005AF862, tail; do 20 tail; do 7 @0x005B0484; return 2 |
  | `vines` | do 20 | 1 200 | owner's `+0xC6` bit ignored (319); frames left 9 (178) | HitUnit @0x005AF587; re-target @0x005A9A66; do 1 @0x005AF572 |
  | `rabies` | do 30 | 1 200 | draws on the missile seed (90); `left > 0` (152) | HitUnit @0x005B01DE (no target, no owner, dead, left < 0); re-target @0x005A9A66; MissileCreate @0x005B0187 (targets of types 0–5); do 1 @0x005B01C4; return 2 |
  | `reseed9b` | do 28, 34, 35 | 1 500 | do 28's offsets swapped (43); do 35's parity swapped (304) | MissileCreate @0x005AFD50, @0x005B0614; do 1 @0x005AFD5A, @0x005B06A9; do 3 @0x005B0530; PathPlan @0x005B076C; return 2 |
  | `scatter25` | do 25 | 900 | cell mask 5 for `0x45` (113); calcs swapped (184) | CellTestAt @0x005A9908 (0 and 2 draws); do 1 @0x005AF96A (period 0, off-beat, no owner, no room); return 2 |
  | `wake` | do 31 | 1 200 | `CollideKill` ignored (152); offsets swapped (351) | MissileCreate @0x005B03A0; do 1 @0x005B03C1; JustHitState @0x005B02C0; SizeUnmark @0x005B032A; return 2 |
  | `regen` | do 29, 33 | 1 200 | cap dropped (55); `MulDiv` on the current value (129) | UnitSetStat @0x005AFE7A, @0x005AFFCA; do 1 @0x005AFEAD, @0x005AFFFD; return 2 |
  | `tornado` | do 27 | 900 | `calc1` for `calc4` (225); `Param1 ≥ 0` (140) | BuildDamage @0x005AFB14; do 1 @0x005AFB75; return 2 |
  | `fx` | do 19, 36 | 1 200 | upper bound 23 (98); `< 100` (82) | UnitsInRange @0x005B0A2F (both callbacks); QuestActive @0x005B0A76; do 1 tail |
  | `dmgconv` | damage 1, 12 | 1 500 | cap dropped (36); dmg 1 keeps the physical damage (340); `EType` 4 also clears the cold length (45) | returns only: every `EType` 0–13 and 255, calc ≤ 0, calc out of the pool, no record |
  | `dmgelem` | damage 5, 13 | 1 200 | undead mask `0x08` only (12); dmg 13's percent dropped (125) | returns only: undead and demon bonuses, not a monster, every `EType` |
  | `dmgpkt` | damage 2, 3, 4, 7, 8, 9, 10, 11 | 2 400 | dmg 3 with `& 0xFF` (17); dmg 7 with `lvl` for `lvl − 1` (53) | returns, and OverlaySet @0x005AD498 (dmg 8) |
  | `knock` | damage 14 | 1 200 | `small`/`large` swapped (60); ×3 for ×2 (2) | returns only: player, monster small/medium/large for `dParam1` < 1, 1, ≥ 2, other types, not a missile |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt` `16672f27…`): 9a's (`g_UnitHashOffsets`, the `CALC_Eval` and
  `UNIT_GetSizeX` jump tables, the two calc function counts with 0 stores in `.text`), plus `g_BitMask32`
  (`0x006CE268`, `.rdata`, `1 << i`: the ISC mask `0x006CE270` `StatListGetValue` tests, do 31's `Explosion` mask
  `0x006CE26C`, `MonStats2FlagTest`'s masks) and the three `EType` jump tables in `.text` (`0x005A8EE8`, `0x005A9240`,
  `0x005A9334`). Stat lists, ItemStatCost, MonStats, MonStats2, Skills and the calc pools are scratch records written
  one field per field read. `MISS_EvalCalc(m, owner, DmgCalc1, −1, −1)` reads the missile's `MissileData+0x0C` (a
  development run traced it; the cases then wrote it).
- [I] **Not reached** (from the reading): everything after each boundary (listed per function below); the
  `StatListGetValue` floor (`fMin`) branch (every ISC record's `+0x05` is 0); `GameFindUnit` with a type above 5 (do 30
  with `MissileData+0x28` > 5 reads address 0, a fault; ADR-0015 (5)); a do-35 missile without a path. (run:2026-10-20-cat-emu-9b)
- [I] ADR-0015 (3): the `[C]` claims, those marked ADR-0021 included, cover the code as a map. What the offsets mean keeps its own tag
  (Missiles columns `[C]` by layout; `MissileData` words `[I]`, skills/0002 § 1; packet fields `[I]`, combat/0001);
  nothing here says when the game runs these functions or on which seed state. (run:2026-10-20-cat-emu-9b)

### 3. Do 21, 23, 26, 32: one sub-missile

- [C] (ADR-0021; ends at `MissileCreateAt` @0x005AF612 or at do 20's entry, a tail jump) **Do 21** (`0x005AF590`): with a record, when `SubMissile1 != 0` (s16) and path flag 8:
  `MissileCreateAt(ECX game, EDX owner; skill, lvl, SubMissile1, SubX, SubY)` (owner may be 0); then a tail jump to
  do 20 (§ 5), which has no record test. (run:2026-10-20-cat-emu-9b `create9b`,
  0x005AF5C9–0x005AF619, fn:sub_005AF590_MissDo21SubThenDo20@0x005AF590)
- [C] (ADR-0021; ends at `MissileCreate` @0x005AF859 / do 1 @0x005AF862 (do 23), `MissileCreateAt` @0x005AFA0E / do 1
  tail (do 26), `MissileCreate` @0x005B047B / do 7 @0x005B0484 (do 32); the code after each creation is not covered)
  **Do 23** (`0x005AF790`): `SubMissile1 != 0`; on flag 8 a block `{flags 1, owner, start = SubX/SubY,
  skill, lvl, SubMissile1}`, flags 9 and loops `Param1` when `Param1 > 0` (skills/0003 § 6's reading, now emulated);
  then do 1. **Do 26** (`0x005AF980`): `SubMissile1 != 0`; when `elapsed % max(Param1, 1) == 0`, `MissileCreateAt` as
  do 21; then do 1 (tail jump). **Do 32** (`0x005B03E0`): `SubMissile1 ≥ 0`; on flag 8 a block `{flags 1, owner,
  source = m, skill, lvl, SubMissile1}` (no start point), then **do 7** (Guided
  Arrow's homing, skills/0004 § 10) instead of do 1. (0x005AF7D6–0x005AF85D, 0x005AF9B8–0x005AFA15, 0x005B041E–0x005B047F,
  fn:sub_005AF980_MissDo26PeriodicSubAt@0x005AF980, fn:sub_005B03E0_MissDo32SubThenDo07@0x005B03E0)
- [I] Stock: 393 distraction → 394 distractionfog (do 21); 441 sucfireball → 443 (`Param1` 3: flags 9), 458
  firestormmaker → 457 (`Param1` 0: flags 1) (do 23); 471 vines → 472, 474 plague vines → 475, `Param1` 9 (do 26); 520
  tigerfury → 521 tigerfurytrail (do 32). (`rows.txt`, tbl:Missiles.txt:SubMissile1, tbl:Missiles.txt:Param1)

### 4. Do 22: the trailing javelins' side trails

```c
// fn:sub_005AF620_MissDo22SideTrails@0x005AF620, trimmed
if (!rec || rec->SubMissile1 == 0 || !(path = m->path)) return 2;
x = SubX(m); y = SubY(m);
if (MISSDATA_GetElapsed(m) < 2) {                       // the first two frames
    MISSDATA_SetSeedLow(m, -(PathGetPosY(path) - y));    // +0x28 = -dy   (path +0x12: the target point)
    MISSDATA_SetParam2C(m, PathGetPosX(path) - x);       // +0x2C =  dx   (path +0x10)
}
if (PathFlag08(path)) {
    p = {flags 0xB, owner, cls SubMissile1, x, y, skill, lvl, loops Param1, tx +0x28, ty +0x2C};
    MissileCreate(game, &p);                             // boundary
    p.tx = -(+0x28); p.ty = -(+0x2C); MissileCreate(game, &p);
}
return MissileMoveCollide(game, m);
```

- [C] (ADR-0021; ends at the first `MissileCreate` @0x005AF749, or do 1 @0x005AF772 off flag 8) As above up to the
  first creation: the stored pair is the direction to the path target turned by 90°
  (32-bit differences of the u16 positions), written on frames 0 and 1 only. The second creation, with the pair
  negated, follows the boundary and is `[I]`. (run:2026-10-20-cat-emu-9b `create9b`, 0x005AF674–0x005AF749,
  fn:sub_005AF620_MissDo22SideTrails@0x005AF620)
- [I] Stock: 431 lightingtrailingjavalin → 432, 438 advlighttrailingjav → 439, `Param1` 3. (`rows.txt`, tbl:Missiles.txt:Param1)

### 5. Do 20: blade creeper

- [C] (ADR-0021; ends at `0x00650BE0` @0x005A9A66, `MISSILE_HitUnit` @0x005AF587 or do 1 @0x005AF572) With an owner
  that `UnitIsDead` calls alive (`+0xC6` bit 0 clear, type 0 or 1, mode neither 0 nor the death mode):
  `sub_005A99E0_MissRetargetOwner(ECX game, EBX m)`, which with the missile's path calls
  `0x00650BE0(path, m, UnitGetRoom(owner), owner x, owner y)`; without a path the re-target is skipped and the frames
  left are 10 at do 1. Without an owner, or with a dead one (any type but 0 and 1 counts as dead):
  `MISSILE_HitUnit(game, m; 0, 1)` (the end-of-life hit). [I] After the boundaries (from the reading, 0x005AF561–0x005AF588):
  on the path case `SetRemaining(m, 10)` and do 1 follow the re-target; the function returns **1** after do 1 (not do
  1's value) and 2 after the hit. (run:2026-10-20-cat-emu-9b `vines`, 0x005AF540–0x005AF58E, 0x005A99E0–0x005A9A6B,
  fn:sub_005AF540_MissDo20FollowOwner@0x005AF540, fn:sub_005A99E0_MissRetargetOwner@0x005A99E0,
  fn:sub_00650BE0_PathTargetRoomXY@0x00650BE0)
- [I] So a blade creeper lives as long as its owner, always 10 frames from its end. Stock 392 blade creeper
  (`Range` 10, `LevRange` 5; Skills 257 BladeSentinel). What `0x00650910` does with the room and point is the path
  code's (not read). (`rows.txt`)

### 6. Do 30: rabies plague (contagion)

```c
// fn:sub_005B0010_MissDo30Contagion@0x005B0010, trimmed
if (!rec || rec->SubMissile1 < 0 || !skillrec) return 2;
t = GameFindUnit(game, MISSDATA_GetSeedLow(m) /*type*/, MISSDATA_GetParam2C(m) /*guid*/);
owner = UnitGetOwner(game, m);
if (!t || !owner || UnitIsDead(owner) || MISSDATA_GetRemaining(m) < 0) { MISSILE_HitUnit(game, m, 0, 1); return 2; }
sub_005A99E0_MissRetargetOwner(game, m);                     // boundary when the missile has a path
if (MISSDATA_GetElapsed(m) % max(Param1, 1) == 0) {
    p = {flags 2, owner t, source m, cls SubMissile1, skill, lvl};
    p.tx = RNG_Range(&t->seed, 2*Param2 + 1) - Param2;      // draw 1, the target's seed
    p.ty = RNG_Range(&t->seed, 2*Param2 + 1) - Param2;      // draw 2
    n = MissileCreate(game, &p);                             // boundary
    if (skill->auratargetstate > 0 && (l = UNIT_FindStatListByState(owner, state)) && n)
        MISSDATA_SetSeedLow(n, l->+0x18);
}
MissileMoveCollide(game, m); return 1;
```

- [C] (ADR-0021; ends at `MISSILE_HitUnit` @0x005B01DE, the re-target @0x005A9A66, or, without a path, `MissileCreate`
  @0x005B0187 or do 1 @0x005B01C4; the return values after them, the creation and the state copy are not covered) As
  above up to the re-target, or (no path) to `MissileCreate`: the infected unit is the one
  `MissileData+0x28` (type) and `+0x2C` (guid) name; the new missile's owner is that unit and its two offsets are drawn
  on **that unit's** seed, `RNG_Range` (no step when `2·Param2 + 1 < 1`); the missile's, the owner's and a decoy
  unit's seeds are left as they were (the checker compares the target's seed; the other three were checked at the
  review from the kept `rabies.out`, 270 of 270 unchanged over the 90 creation cases, `workspace/logs/skills-cat-9b-review/seeds-do30.txt`).
  (run:2026-10-20-cat-emu-9b `rabies`, 0x005B009B–0x005B0187; objdump `add ecx,0x20` on the `GameFindUnit` result at
  0x005B0158)
- [I] After the creation (from the reading): the owner's stat list of the skill's `auratargetstate` gives the new
  missile's `+0x28` its `+0x18` word, which damage 11 reads as an end frame (§ 15); `[L]` that `+0x18` is the
  state's expiry frame. Stock 515 rabiesplague (`Param1` 4, `Param2` 7) → 516 rabiescontagion. (`rows.txt`,
  fn:UNIT_FindStatListByState@0x006256B0)

### 7. Do 28: volcano debris

- [C] (ADR-0021; ends at `MissileCreate` @0x005AFD50 or do 1 @0x005AFD5A; the creation and do 1 are not covered) With a
  record, `SubMissile1 ≥ 0` and a Skills row: without an owner, do 1. Else `r = Param2 > 0 ?
  Param2 : max(aurarangecalc, 1)`, `period = Param1 > 0 ? Param1 : max(calc4, 1)` (`SKILLS_EvalCalc(owner, …, skill,
  lvl)`); when `Param3 < elapsed < Param4` and `elapsed % period == 0`: `RNG_SeedInit(&m->seed, +0x28)`,
  `dx = RNG_Range(2r + 1) − r`, `dy` the same (x first), then `+0x28 = RNG_GetLow` (before the call: the checker
  compares `+0x28` at the boundary; the review's correction of "after"), and a block
  `{flags 0x520, owner, source m, tx = SubX + dx, ty = SubY + dy, +0x24 = Param5, skill, lvl, SubMissile1}` to
  `MissileCreate`. The point goes in the **target** words (`+0x1C`, `+0x20`), not the start. (run:2026-10-20-cat-emu-9b
  `reseed9b`, 0x005AFBC8–0x005AFD4B; objdump `lea edx,[edx+edx*1+0x1]` at 0x005AFCBF, `call 0x64a710`
  `MISSDATA_SetSeedLow` at 0x005AFCEB before `call 0x59fa30` at 0x005AFD4B)
- [I] Stock: 479 volcano (`Param3` 2, `Param4` 128, `Param5` 30) → 481 volcano debris 2; Skills Volcano `aurarangecalc`
  `par1` (12), `calc4` `par2` (2): a debris every 2 frames within ±12 between frames 3 and 127. `+0x28`'s first value
  is its creator's (Skills Volcano's start or do function, not read). (`rows.txt`, tbl:Skills.txt:aurarangecalc,
  tbl:Skills.txt:calc4)

### 8. Do 34: the Baal taunt control

- [C] (ADR-0021; ends at do 3 @0x005B0530 or `MissileCreate` @0x005B0614; what follows the creation is not covered)
  `n` = the count of leading pairs `(SubMissile_k ≥ 0, Param_{k+2} > 0)`, k = 1..3 (`SubMissile1..3`,
  `Param2..4`); `n == 0` → 2. While `elapsed < Param1`, do 3 (`sub_005AE480_MissDo03CloudMark`). From then on, every
  frame: `RNG_SeedInit(&m->seed, SubX)`, one step, `k = low & (n − 1)` when `n` is a power of two, else
  `low % n` (unsigned); when `elapsed % Param_{k+2} == 0` a block `{flags 0, owner, source m, skill, lvl,
  SubMissile_k}` to `MissileCreate`, then (after, `[I]`) `MISSILE_HitUnit(game, new; 0, 1)` on the new missile and do 3;
  else do 3 (call site 0x005B0530, which the checker separates from the after-creation site 0x005B062E).
  (run:2026-10-20-cat-emu-9b `reseed9b`, 0x005B04E6–0x005B060F; objdump `div edi` at 0x005B058E, `and esi,eax` at
  0x005B05B7)
- [I] Stock: 546 baal taunt control (`Param1` 25, `Param2` 3, `Param3` 45; 654 lightning and 655 poison controls):
  `n = 2`, so the pick is `low & 1` and the seed is re-initialised from the same x on every frame, so the pick repeats
  while the missile does not move. (`rows.txt`, tbl:Missiles.txt:SubMissile2)

### 9. Do 35: royal strike chaos ice

- [C] (ADR-0021; ends at `PathPlan` @0x005B076C or do 1 @0x005B06A9; the stores after `PathPlan` are not covered) With
  a record: off the `max(Param1, 1)` period, do 1. On it: `RNG_SeedInit(&m->seed, +0x28)`;
  `(a, b)` = the s16 halves of `+0x2C` (low, high); one step; with `low & 1`: `x' = (4a − b) / 4`, `y' = (4b + a) / 4`,
  else `x' = (4a + b) / 4`, `y' = (4b − a) / 4` (truncating; 0 becomes 1); path target = `(SubX + x', SubY + y')`
  (u16), `PathPlan(path, m, 0)`; then (after, `[I]`) `+0x28 = RNG_GetLow`, `+0x2C = (y' << 16) | (x' & 0xFFFF)` and
  do 1. A turn of about ±14° per period, its sign drawn. (run:2026-10-20-cat-emu-9b `reseed9b`, 0x005B0683–0x005B0767;
  objdump `and edx,0x3` at 0x005B0712, `sar edi,0x2` at 0x005B0725)
- [I] Stock: 569 royalstrikechaosice (`Param1` 3). The starting `+0x28`/`+0x2C` are its creator's (the Royal Strike
  finisher, batch 7). (`rows.txt`, tbl:Missiles.txt:Param1)

### 10. Do 31: the wake makers

- [C] (ADR-0021; ends at the first `MissileCreate` @0x005B03A0, do 1 @0x005B03C1, `JustHitState` @0x005B02C0 or
  `COLL_SizeUnmark` @0x005B032A; return 2 where no boundary is reached) `SubMissile1 ≥ 0`. With an owner, on flag 8: a block `{flags 2, owner, source m, SubMissile1, skill,
  lvl, tx +0x28, ty +0x2C}` to `MissileCreate` (the second, negated, after the boundary), then do 1. Without one, the
  missile ends inline: `c = (Explosion ? 0 : 2) | (CollideKill ? 1 : 0)`; with `AlwaysExplode`, `JustHitState(m)`
  (then, `[I]`, the hit event and the hit function, whose bit 2 returns 2 at once); else, when `c & 1` and the missile
  has a room, `COLL_SizeUnmark(room, SubX, SubY, size, 0x40)`; return 2 in every case. (run:2026-10-20-cat-emu-9b
  `wake`, 0x005B023B–0x005B03B0, fn:sub_005B01F0_MissDo31SidePair@0x005B01F0)
- [I] The `Explosion` term: the code sets bit 1 of `c` from it (0x005B0289–0x005B029A), but only bit 0 is ever
  tested and the hit function's value replaces `c` on the `AlwaysExplode` path, so no output of do 31 depends on it.
  The cases vary the flag byte at random and every output matches regardless, so a control on it cannot fail; the
  `CollideKill` control replaced it (ruled acceptable at the review). The term itself is a code reading.
  (run:2026-10-20-cat-emu-9b `wake`; objdump `test BYTE PTR [ebp-0x4],0x1` at 0x005B02F9)
- [I] This repeats `MISSILE_HitUnit`'s end of life (skills/0002 § 5) without the to-hit and damage parts. Stock 517
  wake of destruction maker → 518, 589 baal cold maker → 590 (neither `CollideKill` nor `AlwaysExplode`). (`rows.txt`, fn:MISSILE_HitUnit@0x005ADF10)

### 11. Do 29, 33: the recycler delays

- [C] (ADR-0021; ends at `UnitSetStat` @0x005AFE7A / @0x005AFFCA or do 1 @0x005AFEAD / @0x005AFFFD) With a record, a
  Skills row, and an owner alive: when `elapsed == Param1`, `hp = stat(owner, 6) >> 8`,
  `max = maxhp(owner) >> 8` (arithmetic shifts; do 33: stats 8 and 9, `UNIT_GetMaxMana`); when `hp < max`,
  `hp' = min(hp + MulDiv(max, calc1(owner, skill, lvl), 100), max)` and `UnitSetStat(owner, 6, hp' << 8, 0)`; then
  (after, `[I]`) the `ProgOverlay` overlay on the owner when it is a valid Overlay row; then do 1. (run:2026-10-20-cat-emu-9b
  `regen`, 0x005AFE0B–0x005AFE75, 0x005AFF5B–0x005AFFC5, fn:sub_005AFD70_MissDo29OwnerLife@0x005AFD70,
  fn:sub_005AFEC0_MissDo33OwnerMana@0x005AFEC0, fn:sub_00621E40_UnitSetOverlayStat@0x00621E40)
- [I] Stock: 498 recycler delay (`ProgOverlay` 151 steallife), 540 vine recycler delay (152 stealmana), `Param1` 45.
  (`rows.txt`, tbl:Missiles.txt:ProgOverlay)

### 12. Do 27: tornado

- [C] (ADR-0021; ends at `MISSILE_BuildDamage` @0x005AFB14 or do 1 @0x005AFB75) With a record and a Skills row:
  `period = Param1 > 0 ? Param1 : max(calc4, 1)`; on it, `MISSILE_BuildDamage(ECX game, EDX owner; m, 0, &pkt)` (the
  third argument, a local's address, is not compared: `[I]`); then (after, `[I]`) `radius = Param2 > 0 ? Param2 :
  max(aurarangecalc, 1)`, `pkt.flags |= HitFlags`, `pkt.result |= ResultFlags`, and `sub_0056BAD0_AreaHitAt(game, m;
  0, 0, radius, &pkt, aurafilter)`; then do 1. (run:2026-10-20-cat-emu-9b `tornado`, 0x005AFA74–0x005AFB66,
  fn:sub_005AFA30_MissDo27PeriodicAreaHit@0x005AFA30)
- [I] Stock: 478 tornado (`HitFlags` 2, `ResultFlags` 5), Skills Tornado `calc4` `par1` (15), `aurarangecalc` `par2` (3),
  `aurafilter` 42371. (`rows.txt`, tbl:Skills.txt:aurafilter)

### 13. Damage 1, 12 and the `EType` helpers

```c
// fn:sub_005AD050_MissDmg01ConvertPct@0x005AD050 (ECX game, EDX m; unit, pkt), trimmed; 12 at 0x005AD0F0
v = MISS_EvalCalc(m, owner, rec->DmgCalc1, -1, -1);
if (v <= 0) return;
if (v >= 100) v = 100;                                   // the cap the Ghidra decompile drops (0x005AD0A0)
d = MulDiv(pkt->phys, v, 100);  if (!(d < pkt->phys)) d = pkt->phys;
// damage 1:
pkt->phys -= d;  PacketAddEType(m, pkt, d);
// damage 12:
e = MissileRollEType(game, m, unit, pkt);  PacketClearDamage(m, pkt);  PacketAddEType(m, pkt, d + e);
```

- [C] As above. `sub_005A9270_PacketAddEType`: `EType` 0 → `phys`, 1 fire, 2 light, 3 magic, 4 cold, 5 poison, 6–9 the
  life, mana, stamina steal and stun fields, 11 burn: added; 12: the cold field **set**; 10 and ≥ 13: nothing.
  `sub_005A91C0_PacketClearDamage`: `flags &= ~0x700`; the damage, steal and burn fields 0; the lengths by `EType`
  (4, 12: poison and burn lengths; 5: cold and freeze lengths and burn; 11: cold, freeze and poison lengths; else all
  four). (run:2026-10-20-cat-emu-9b `dmgconv`, fn:sub_005A9270_PacketAddEType@0x005A9270,
  fn:sub_005A91C0_PacketClearDamage@0x005A91C0, fn:sub_0064B0C0_MissileGetEType@0x0064B0C0,
  fn:sub_005AD0F0_MissDmg12ConvertAll@0x005AD0F0)
- [C] `sub_005A8C70_MissileRollEType` (on the missile's own stats, `MissileElemRoll` as skills/0002 § 6): `EType` 0
  rolls stats 21/22 into `phys`, then, with a unit, `phys += phys·pct / 100` (32-bit product, truncating) with
  `pct = stat 25 (+ 121 vs a demon, + 122 vs an undead)` floored at −90, and stat 141 doubles it and sets `0x2000`;
  returns `phys`; 1–5, 11, 12 roll their stat pairs with masteries 329, 330, 357, 331, 332, 329, 331, store the length
  (4: cold length = stat 56; 12: **freeze** length = stat 56; 5: poison length = stat 59, `/ stat 326` when > 1;
  11: burn length = stat 315) and return the value (5 and 11: × 25); 6–9 copy stats 60, 62, 64, 66 and return 0; 10
  and ≥ 13 return 0. One `RNG_RangeB` on the missile seed per roll whose two stats are ≥ 1. (run:2026-10-20-cat-emu-9b
  `dmgconv`, `dmgelem`, 0x005A8C70–0x005A8EE0, fn:sub_005A8C70_MissileRollEType@0x005A8C70)
- [C] For `phys > 0` and a calc of 100 or more, both the capped and the uncapped share give `d = phys`; the cap
  changes the result only where the uncapped share would fall below `phys` (a negative physical value, or a share
  that wraps in 32 bits; 36 cases of its control). (`check.txt` `dmgconv`, run:2026-10-20-cat-emu-9b)
- [I] Stock: damage 1 on 12 firearrow (fire), 27 magicarrow (magic), 40 coldarrow (cold), each with a `DmgCalc1`;
  damage 12 on 205 lightningjavelin (lightning). (`rows.txt`, tbl:Missiles.txt:DmgCalc1, tbl:Missiles.txt:EType)

### 14. Damage 2, 3, 4, 7, 8, 9, 10

- [C] **2** (`0x005AD1B0`): with a record, `freezeLen = MulDiv(stat(m, 56), max(dParam1, 0), 100)`, `coldLen = 0`.
  **3** (`0x005AD220`): with a record, one inline LCG step of the missile seed; `(low & 0x7F) < dParam1` (signed)
  sets result `0x4000` (raises skills/0003 § 6's tier-A reading). **4** (`0x005AD290`): no record test; `freezeLen =
  coldLen`, `coldLen = 0`. **10** (`0x005AD2B0`): with a record, `freezeLen = coldLen` (cold length kept).
  **7** (`0x005AD3E0`): with a record, `stunLen = dParam1 > 0 ? dParam1 : sub_004E6CA0(skill, lvl)` (`Param1 +
  (lvl − 1)·Param2` of the missile's skill; 0 for an invalid skill or `lvl ≤ 0`), `hitClass = 0x60`. **9**
  (`0x005AD4A0`): `stunLen = dParam1 > 0 ? dParam1 : (valid skill ? Skills Param2 : 0)`, `hitClass = 0x60`.
  (run:2026-10-20-cat-emu-9b `dmgpkt`; objdump `setl cl` at 0x005AD1EE, `and eax,0x7f` at 0x005AD267;
  fn:sub_005AD1B0_MissDmg02FreezeLen@0x005AD1B0, fn:sub_005AD290_MissDmg04ColdToFreeze@0x005AD290,
  fn:sub_005AD2B0_MissDmg10FreezeCopy@0x005AD2B0, fn:sub_005AD3E0_MissDmg07Stun@0x005AD3E0,
  fn:sub_005AD4A0_MissDmg09StunParam2@0x005AD4A0, fn:sub_004E6CA0_SkillParamByLevel@0x004E6CA0)
- [C] **8** (`0x005AD450`) returns without a call when the record, the unit or `ProgOverlay > 0` (s16) is missing;
  [C] (ADR-0021; ends at `0x00621E40` @0x005AD498) else it calls `0x00621E40(unit, ProgOverlay, 0)` (which, `[I]` from the reading, puts the overlay as
  stat 178 on the unit's flag-`0x80` stat list). (run:2026-10-20-cat-emu-9b `dmgpkt`,
  fn:sub_005AD450_MissDmg08Overlay@0x005AD450)
- [I] Stock: 2 on 28 icearrow, 569 royalstrikechaosice (`dParam1` 100); 3 on the six fire-wall rows (`dParam1` 19);
  4 on 91 iceblast; 7 on 235 warcry (Skills War Cry `Param1` 25, `Param2` 5) and 511 shockwave (40, 15); 8 on 462/463
  erruption cracks (`ProgOverlay` 81 fire_hit); 9 on 477 twister (Skills Twister `Param2` 10); 10 on 561
  bladesoficecubes (`EType` 12). (`rows.txt`, tbl:Missiles.txt:dParam1, tbl:Skills.txt:Param2)

### 15. Damage 11: rabies contagion

- [C] With an owner and a unit: `v = MissileData+0x28 − Game+0xA8` (the frame); when `10 ≤ v ≤
  SKILLS_GetElemLen(owner, skill, lvl, 1)`, `poisonLen = v`; else `poison = poisonLen = 0` (also without an owner or a
  unit). No record test. `SKILLS_GetElemLen`: `ELen` plus the level bands of `ELevLen1..3` (`(lvl − 1)·L1` below 9,
  `(lvl − 8)·L2 + 7·L1` below 17, `(lvl − 16)·L3 + 8·L2 + 7·L1` from 17), then `+ MulDiv(len, ELenCalc, 100)` when that
  calc is in the pool and non-zero; 0 for an invalid skill or `lvl ≤ 0`. (run:2026-10-20-cat-emu-9b `dmgpkt`,
  0x005AD530–0x005AD5B7, fn:SKILLS_GetElemLen@0x00644F20, fn:sub_005AD530_MissDmg11PoisonLeft@0x005AD530)
- [I] So a contagion carries an end frame, not a length: the poison it passes on lasts what is left of the infection,
  and none when less than 10 frames are left. Stock 516 rabiescontagion, Skills Rabies `ELen` 100, `ELevLen1` 10.
  (`rows.txt`, tbl:Skills.txt:ELen)

### 16. Damage 5, 13, 14

- [C] **5** (`0x005AD2F0`): with a record, `e = MissileRollEType(…)`; when `dParam1 > 0` and the unit is undead
  (MonStats `+0x0D` & `0x18`, a monster), `PacketAddEType(MulDiv(e, dParam1, 100))`; when `dParam2 > 0` and a demon
  (`& 0x20`), the same with `dParam2`. **13** (`0x005AD5C0`): only for a unit of type 1; with an owner, `phys += phys ·
  stat(owner, 25) / 100` (32-bit product, truncating); then damage 5 (13 has no record test of its own; 5's applies). (run:2026-10-20-cat-emu-9b
  `dmgelem`; objdump `mov eax,0x51eb851f` at 0x005AD5F8; fn:sub_005AD2F0_MissDmg05UndeadDemon@0x005AD2F0,
  fn:sub_005AD5C0_MissDmg13OwnerEd@0x005AD5C0)
- [C] **14** (`0x005AD630`): only for a missile unit (type 3) with a record and a unit. Chance: a player, `dParam2` when
  `dParam1 ≥ 1` (else none); a monster, by MonStats2 `small` (flag 10) and `large` (flag 11) through MonStats `+0x18`:
  `dParam1 < 1`: `dParam2` if small, else none; `dParam1 == 1`: small 2·`dParam2`, large none, else `dParam2`;
  `dParam1 ≥ 2`: small 3·`dParam2`, large `dParam2`, else 2·`dParam2`; other unit types none. With a chance above 0,
  `RNG_Range(missile seed, 100) < chance` sets result `|= 0x8` (knockback; `or WORD PTR [eax+0x4],0x8` at 0x005AD694). (run:2026-10-20-cat-emu-9b `knock`,
  0x005AD630–0x005AD72A, fn:sub_004638A0_MonStats2FlagTest@0x004638A0,
  fn:sub_005AD630_MissDmg14KnockBySize@0x005AD630)
- [I] Stock: 5 on 92 blessedhammer (`EType` magic, 50/50); 13 on 640 blessedhammerex (`dParam1` 50, `EType` 0); 14 on 452
  moltenboulder (`dParam1` 1, `dParam2` 50: 100 % on small monsters, 50 % on medium, none on large, 50 % on players).
  (`rows.txt`, tbl:MonStats2.txt:small, tbl:MonStats2.txt:large)

### 17. Do 19: radament death

- [C] (ADR-0021; ends at `sub_0056DDE0_UnitsInRangeCall` @0x005B0A2F or do 1 by tail jump; do 1 after the call is not
  covered) With `r` = frames left: when `2 ≤ r ≤ 24` (unsigned `r − 2 ≤ 22`),
  `sub_0056DDE0_UnitsInRangeCall(ECX game, EDX 0x3002; SubX, SubY, m, 124, 1, 0x005AD8F0)`; when `r == 1` the same with
  `0x005AD910`; then do 1 (tail jump). No record test. (run:2026-10-20-cat-emu-9b `fx`, 0x005B0940–0x005B0A36,
  fn:sub_005B0940_MissDo19Redemption@0x005B0940, fn:sub_0056DDE0_UnitsInRangeCall@0x0056DDE0)
- [I] From the reading: the call's radius is `sub_004E6CA0(124, 1)`, Redemption's `Param1` (16 on stock data), and each
  unit found gets `0x005D0C40(unit, 124, 1, 0 / 1)`: with 0, `SKILLS_EvalCalc(calc1) > RNG_Range(seed, 100)` first;
  then life `+ calc2 << 8` and mana `+ calc3 << 8` (capped) on the unit `0x005D0C40` gets in EDX, and state 99
  (`redeemed`) on the corpse; so the last frame redeems without the roll. Which unit is in EDX at the callback is not
  read (open question). Stock 347 radamentdeath (`Range` 400). (0x0056DCFE–0x0056DD0B, 0x005D0C40–0x005D0D40,
  fn:sub_005AD8F0_RedemptionChanceCb@0x005AD8F0, fn:sub_005AD910_RedemptionAlwaysCb@0x005AD910,
  fn:sub_005D0C40_RedemptionCorpse@0x005D0C40)

### 18. Do 36: baalfx control

- [C] (ADR-0021; ends at `QUESTS_IsActive` @0x005B0A76 or do 1 by tail jump) With `r` = frames left: when `+0x28 == 0`
  and `r ≤ 100` (signed): `+0x28 = 1`, then `QUESTS_IsActive(game, 36)`; otherwise do 1 (tail jump); after the quest
  test, `[I]`, the spawn below, the room pin and do 1. No record test. (run:2026-10-20-cat-emu-9b `fx`, 0x005B0A40–0x005B0A93,
  fn:sub_005B0A40_MissDo36BaalFx@0x005B0A40)
- [I] After (from the reading): when quest 36 (`a5q6`, quests/0001 word 40) is active, `sub_0058E920_BaalFxSpawnTyrael`
  runs a free-spot search (`0x00545340`) from the missile's position offset by (−5, −5) and spawns monster 521
  (`tyrael3`, `sub_005B2F20_SpawnAtPos`); then `RoomPinSet(room, 1)`. Stock 625
  baalfx control (`Range` 650): once, 100 frames before its end. (fn:sub_0061AED0_RoomPinSet@0x0061AED0,
  fn:QUESTS_IsActive@0x005444B0, fn:sub_0058E920_BaalFxSpawnTyrael@0x0058E920)

## Data touched

`tbl:Missiles.txt:pSrvDoFunc`, `pSrvDmgFunc`, `SubMissile1`, `SubMissile2`, `SubMissile3`, `Param1`..`Param5`,
`dParam1`, `dParam2`, `DmgCalc1`, `EType`, `ProgOverlay`, `HitFlags`, `ResultFlags`, `Explosion`, `CollideKill`,
`AlwaysExplode`, `Size`; `tbl:Skills.txt:calc1`, `calc2`, `calc4`, `aurarangecalc`, `aurafilter`, `auratargetstate`,
`Param1`, `Param2`, `ELen`, `ELevLen1`..`3`, `ELenCalc`; `tbl:MonStats.txt` `+0x0D` (undead, demon), `+0x18`;
`tbl:MonStats2.txt:small`, `large`; ItemStatCost `+0x05`; `struct:MissileData+0x0A`, `+0x0C`, `+0x0E`, `+0x10`,
`+0x28` (do 22 −dy, do 28/35 seed word, do 30 target type, do 36 done flag, damage 11 end frame), `+0x2C` (do 22 dx,
do 30 target guid, do 31 offset, do 35 packed step); `struct:DamagePacket+0x04`, `+0x08`..`+0x44`, `+0x60`;
`struct:Game+0xA8`; unit `+0x00`, `+0x04`, `+0x10`, `+0x20` (seed), `+0x2C`, `+0x5C` (stat list), `+0xC6`;
stat list `+0x10` bit 31, `+0x24`/`+0x28`, `+0x48`/`+0x4C`; path `+0x02`, `+0x06`, `+0x10`, `+0x12`, `+0x1C`, `+0x34` bit 3,
`+0x58`.

## Dead ends

- Ghidra's decompile of damage 1 and 12 drops the `min(v, 100)` cap (0x005AD0A0–0x005AD0A5, 0x005AD14C–0x005AD151) and
  shows `MulDiv` with one argument; the registers are read from objdump.
- Do 31's `Explosion` bit sets bit 1 of the end result, which no path up to a boundary reads, so a control on it could
  not fail; the `CollideKill` control replaced it.
- Do 28's point looked like the start (`+0x14`); the emulated block shows the target words (`+0x1C`, `+0x20`).

## Open questions

- [L] What `0x00650910` does with the owner's room and point (do 20, 30), and what the flags `0x520` (do 28) and `0xB`
  (do 22) give the creation (skills/0002 § 2 reads bits 0–3; `0x20`, `0x100`, `0x400` not read here).
- [L] Which unit `0x005D0C40` heals at do 19's callbacks (its EDX), and so whether a radament death heals anything.
- [L] That stat list `+0x18` is a state's end frame (do 30 → damage 11).
- [L] Everything after each boundary (§§ 3–12, 17, 18), for a later batch or the harness.
