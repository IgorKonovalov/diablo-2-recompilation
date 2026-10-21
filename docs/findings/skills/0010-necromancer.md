# 0010 — Catalogue batch `nec`: the necromancer start functions 15–21 and do functions 30–32 and 55–63

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 15–21 (`srvstfunc`, `g_SkillStartFuncs`) and do function 30, 31,
> 32 and 55–63 (`srvdofunc`, `g_SkillDoFuncs`) of the necromancer batch do: which Skills, MonStats, MonStats2, item
> and unit fields it reads, which states, missiles and monsters it creates, which draws it makes on which seed, what it
> returns, and which of that the emulator can confirm?
> **Date:** 2026-10-20   **Plan:** 0046 (Phase 1, batch `nec`)   **Status:** for review (`lane/p46m7`)

Static reading of the pinned `Game.exe` in Ghidra 12.1.2 (lane copy `workspace/ghidra-p46m7`, symbols replayed from
`re/symbols.csv`) and objdump, then emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged,
`286393aa…`) and the `nec` families of `tools/skills_catalogue_emu.py` (§ 2; run:2026-10-20-cat-emu-nec in
[experiments](experiments.md)). Skills columns are named as in [Skills](../../tables/Skills.md), MonStats and
MonStats2 columns as in [MonStats](../../tables/MonStats.md) and [MonStats2](../../tables/MonStats2.md). The machinery
that calls a start or do function is [skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart);
the tier-A entries of this batch (start 15, do 30, do 31) were read by plan 0045 in
[skills/0003 §§ 5, 7](0003-handlers.md#5-tier-a-start-and-do-functions), and all three are emulated here. Start 20
passes the source path `.\SKILLS\SkillNec.cpp` (`0x006E3034`) to `ITEMS_CheckFlags`, do 55 to
`SKILLS_ForUnitsInRange`. Stock values come from `workspace/logs/skills-cat-nec/rows.txt` (`excel_bin.py dump` of
the 26 Skills rows whose `srvstfunc` is 15–21 or whose `srvdofunc` is 30–32 or 55–63, by `rows.sh` beside it).

**Tag convention for this finding** (as skills/0009). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a
function entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site
(the return address at ESP), with a site control that fails every matched boundary case, and **where the boundary
sits inside a helper the batch function called, the helper's return address into the batch function at its absolute
stack slot** (the condition of ruling 1 of the `lane/p46m6` review; § 2); (c) the model gives and the checker
compares every argument the claim uses (registers, stack words, and for a pointer into a frame the bytes it points
to), every byte written before the call that the claim uses (the unit's `+0xC4`, frame words of the batch function),
and the state of **the caster's and the target's seeds** at the boundary (both, in every case). Each such claim names
the boundary it ends at; **the callee and all code after it are not covered** and keep `[I]` (from the reading),
marked "after, `[I]`" in place, and what a callee makes of a compared argument (a state, a mode, a damage word) is
stated after the boundary (reverser review-fixes 13). No claim rests on a callee-saved register that is not a
boundary argument (ruling 1 of the `lane/p46m3` review). A plain `[C]` rests on cases that return; a plain `[I]` is a
code reading the emulator does not reach. (run:2026-10-20-cat-emu-nec)

## Answer (summary)

- [C] **The batch.** 19 entries: start 15 `0x005C3070` to start 21 `0x005C3350` (seven, in address order); do 30
  `0x005C37C0`, 31 `0x005C4B00`, 32 `0x005C4CD0`, 55 `0x005C4DF0`, 56 `0x005C5100`, 57 `0x005C5250`, 58
  `0x005C56C0`, 59 `0x005C3B90`, 60 `0x005C58B0`, 61 `0x005C3F20`, 62 `0x005C5D00`, 63 `0x005C5E60` (twelve). Every
  one is `(ECX game, EDX unit; skill id, level)` with `ret 8`. All 19 are emulated. (data:g_SkillStartFuncs@0x00732140,
  data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [C] **No draw before the boundaries.** No function of the batch steps the caster's or the target's seed before its
  boundary or return (6 100 cases, both seeds compared in each). Draws after a boundary are not covered: do 55 and
  do 58 each draw one `RNG_RangeB` on **the target's** seed after theirs (§ 5, after, `[I]`).
  (run:2026-10-20-cat-emu-nec)
- [C] **The target tests** (§ 3). Start 15 returns `0x00645510(target, 0)` for a target outside town, start 17
  `0x00645680(target)`; start 19 returns whether the target's room is not a town room; start 18 returns 1 with no
  read; start 21 runs `0x005C3300` and ends at `0x0056E2F0(ECX target, EDX 7)` (ADR-0021, @0x005C3340); start 20
  admits an item target (type 4) in mode 3 whose record has `+0xDC` bit 1, whose data flags have `0x10` and whose
  `STATLIST_GetOwnerUnit` is 0 (an item class at or past the item count ends at the fatal path's `0x00408090`,
  ADR-0021, @0x00629CDA). Each but start 18 refuses (0) without a target. `0x00645510(u, f)` is 1 for a monster (type 1) in mode 12
  (or mode 0 when `f ≠ 0`) carrying no state of `DataTables+0x150`'s bit-set, whose MonStats2 row has flag bit 7 and
  whose MonStats `+0x32` word is non-zero; `0x00645680(u)` is 1 for a monster in mode 12, no such state, flag bit 7.
  `0x005C3300(u)` needs a monster, MonStats2 flag bit 8, `UnitIsDead` and `0x00645510(u, 0)`.
- [C] (ADR-0021; up to `COMBAT_MeleeHitTest` @0x005C3130 or `COMBAT_DeliverQueued` @0x005C4CFD, §§ 3, 4) **Start 16**
  (Poison Dagger) refuses a target in town, then hit-tests with `SKILLS_GetToHit(caster, id, lvl)` and a zeroed
  0x70-byte packet; **do 32** sets bit 6 of `+0xC4` and calls `COMBAT_DeliverQueued(game, caster; target, 0)`.
- [C] (ADR-0021; up to `sub_0056E780_SkillForUnitsNearTarget` @0x005C39A3 or @0x005C40AF, § 4) **Do 30** (the eight
  necromancer curses, Defense Curse, Blood Mana) and **do 61** (Confuse) admit `aurastat1` in `[−1, ItemStatCost
  count)` (a blank −1 passes) and `auratargetstate` in `[0, States count)`, set bit 6 and pass `ForUnitsNearTarget(ECX
  game, EDX aurafilter; caster, aurarangecalc, callback, &block)` a 0x68-byte block `{game, caster, f, s, id, lvl,
  len, aurastat[6], aurastatcalc[6], auratargetstate, auraevent1..3, auraeventfunc1..3}`: do 30's `len` is
  `auralencalc`, divided (`idiv`, truncating) by the difficulty record's `+0x1C` when `auratargetstate` is 23 or 56
  (`f` = 1 then); do 61's is always divided, `f` is 0, its stat list starts at `aurastat2` (word 0 stays 0) and its
  event words stay 0; `s` is 1 when one listed stat's ItemStatCost byte `+5` has bit 1. After, `[I]`: the callbacks
  apply the state per unit.
- [C] (ADR-0021; § 5) **Do 31, 55, 58, 59, 63.** Do 31 (Raise Skeleton, Raise Skeletal Mage) tests `0x00645510(target,
  0)`, then calls `0x005C2FF0`, which for a player caster of class 3 ends at `COMBAT_ApplyDamage(game, caster; caster,
  0, &packet)` with the packet `{+0x00 0x1000, +0x04 4, +0x08 maxhp / 8, +0x4C the same}` (signed, truncating;
  @0x005C3051); otherwise do 31 tests the record, `SkillSummonClass` and a **signed** `pettype` in `[0, PetType
  count)`, and ends at `0x0061A270(room, type, guid)` of the target (@0x005C4BE2) with the class, mode, the target's
  position and the pet type in its frame. Do 55 (Corpse Explosion) and do 63 (Poison Explosion) end at
  `STATE_Set(target, 0x68 / 0x76, 1)` after `0x00645680` (@0x005C4E29, @0x005C5EDA); do 63 first takes `srvmissilea` in
  `[0, Missiles count)`, **returning 1** when it is not. Do 58 (Revive) and do 59 (Attract) end at `0x0056E2F0` inside
  `0x005C3300` (`EDX 7`) and `0x005C31F0` (`EDX 0x13`, after an alignment of 0, `0x006259B0`).
- [C] (ADR-0021; up to the first `SpawnOwnedMonster`, § 6) **The summons.** Do 56 (Clay, Blood, Fire Golem), do 57
  (IronGolem, after re-running start 20's test), do 60 (Bone Wall) and do 62 (Bone Prison, through `0x005C5BC0`)
  pass the 10-word block `{w0, caster, summon, 0, mode, x, y, pettype (0 at or past the PetType count), petmax calc,
  w24}`: do 56 `w0` 0, position 0, `summon` tested itself (`[0, MonStats count)`), mode `summode` below 16 else 1, and
  `w24` **the game pointer**; do 57 `w0` 1, the target item's position, and `w24` **the frame slot `ebp−0x10`, which
  do 57 does not write before the call**; do 60 `w0` 9, the target point inside a non-town room, `w24` the game
  pointer; do 62 `w0` 9, the target point plus the first of twelve offsets (`0x006E304C`/`0x006E307C`) whose room is
  not a town room, `w24` the mode again. Do 56, 57, 58, 60, 62 and 63 refuse id 0 (`test` of the id, not of the
  record).
- [I] After, from the reading: a class-3 player caster of Raise Skeleton or Revive takes 1/8 of its maximum life as
  a get-hit (class 3 is the paladin in PlayerClass order); the curses' per-unit callbacks, the summons' levels and
  stats, the corpse explosion's damage roll on the corpse's seed and its area hit; and every callee boundary listed per
  function. (fn:sub_005C2FF0_SkillClass3SelfHit@0x005C2FF0)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005C3070` | `sub_005C3070_SkillSt15CorpseTarget` | (P1.3 name) start 15 | I |
| `0x005C30A0` | `sub_005C30A0_SkillSt16PoisonDagger` | start 16 | I |
| `0x005C31C0` | `sub_005C31C0_SkillSt17CorpseExpl` | start 17 (Corpse Explosion, Poison Explosion, NihlathakCorpseExplosion) | I |
| `0x005C3260` | `sub_005C3260_SkillSt18Attract` | start 18: `mov eax, 1; ret 8` | I |
| `0x005C3270` | `sub_005C3270_SkillSt19NotTown` | start 19 (Bone Prison) | I |
| `0x005C32A0` | `sub_005C32A0_SkillSt20ItemTarget` | start 20 (IronGolem); called by do 57 | I |
| `0x005C3350` | `sub_005C3350_SkillSt21Revive` | start 21 | I |
| `0x005C37C0` | `sub_005C37C0_SkillDo30Curse` | (P1.3 name) do 30 | I |
| `0x005C4B00` | `sub_005C4B00_SkillDo31RaiseSkeleton` | (P1.3 name) do 31 | I |
| `0x005C4CD0` | `sub_005C4CD0_SkillDo32PoisonDagger` | do 32 | I |
| `0x005C4DF0` | `sub_005C4DF0_SkillDo55CorpseExpl` | do 55 (Corpse Explosion, mon death sentry, NihlathakCorpseExplosion) | I |
| `0x005C5100` | `sub_005C5100_SkillDo56Golem` | do 56 | I |
| `0x005C5250` | `sub_005C5250_SkillDo57IronGolem` | do 57 | I |
| `0x005C56C0` | `sub_005C56C0_SkillDo58Revive` | do 58 | I |
| `0x005C3B90` | `sub_005C3B90_SkillDo59Attract` | do 59 | I |
| `0x005C58B0` | `sub_005C58B0_SkillBoneWallDo` | (items/0002 name) do 60 | I |
| `0x005C3F20` | `sub_005C3F20_SkillDo61Confuse` | do 61 | I |
| `0x005C5D00` | `sub_005C5D00_SkillBonePrisonDo` | (items/0002 name) do 62 | I |
| `0x005C5E60` | `sub_005C5E60_SkillDo63PoisonExpl` | do 63 | I |
| `0x00645510` | `sub_00645510_MonCorpseTest` | `(unit, flag)`, `ret 8`: § 3 | I |
| `0x00645680` | `sub_00645680_MonCorpseTestDead` | `(unit)`, `ret 4`: § 3 | I |
| `0x0063A770` | `sub_0063A770_UnitHasStateSet33` | `(unit)`: `UnitHasStateInMask(unit, DataTables+0x150)` | I |
| `0x005C3300` | `sub_005C3300_ReviveTargetTest` | `(ESI unit)`: start 21's and do 58's test (§ 3) | I |
| `0x005C31F0` | `sub_005C31F0_AttractTargetTest` | `(ECX game, EDX caster; unit)`, `ret 4`: do 59's test (§ 5) | I |
| `0x0056E2F0` | `sub_0056E2F0_MonTestN` | `(ECX unit, EDX n)`: base class 492 with state 143 → 0, else `0x005DD480(unit, n)` (not read) | I |
| `0x00629CC0` | `sub_00629CC0_ItemRecFlag2` | `(class)`, `ret 4`: `ITEMS_GetRecord(class)+0xDC & 2`, fatal path without a record | I |
| `0x005C2FF0` | `sub_005C2FF0_SkillClass3SelfHit` | `(ECX game, EDX caster; id, lvl)`, `ret 8`: § 5 | I |
| `0x005C3400` | `sub_005C3400_CurseStateDiffFlag` | `(ECX state)` → 1 for 23 or 56 | I |
| `0x005C37A0` | `sub_005C37A0_DiffDivide` | `(AL difficulty, ESI v)` → `v / DifficultyRec(d)+0x1C` when non-zero, else `v` | I |
| `0x005C3DE0` | `sub_005C3DE0_ConfuseApplyCb` | do 61's per-unit callback (not read) | I |
| `0x005C4D10` | `sub_005C4D10_CorpseExplUnitCb` | do 55's per-unit callback (read only, § 5) | I |
| `0x005C5430` | `sub_005C5430_Do58TargetOp` | `(ESI unit; game)`, `ret 4`: do 58's call after its test (not read beyond its calls) | I |
| `0x005C5BC0` | `sub_005C5BC0_BonePrisonPiece` | `(EAX caster, EBX id; game, x, y, lvl)`, `ret 0x10`: one piece (§ 6) | I |
| `0x0061A270` | `sub_0061A270_RoomUnitOp` | `(room, type, guid)`: called on the target before do 31's and do 57's spawn (not read) | I |
| `0x006E304C`, `0x006E307C` | `g_BonePrisonOffX`, `g_BonePrisonOffY` | do 62's twelve offsets x `−1 1 3 4 4 3 −1 1 −3 −4 −4 −3`, y `−4 −4 −3 −1 1 3 4 4 3 −1 1 −3` (.rdata) | I |

## Walkthrough

### 1. The table slots and the shared shape

- [C] `g_SkillStartFuncs[15..21]` and `g_SkillDoFuncs[30..32, 55..63]` are the Functions table's addresses (19 entries
  compared, `table_entries=19`). (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [I] Two record tests occur. Start 16, do 30, 31, 59 and 61 test `0 ≤ id < DataTables+0xBA0` and a non-null record
  (`DataTables+0xB98 + 0x23C · id`). Do 55, 56, 57, 58, 60, 62 (in `0x005C5BC0`) and 63 compute the record (0 for an
  id out of range) but test **only `id ≠ 0`** before reading it, so an out-of-range non-zero id reads through a null
  record (a fault the emulator does not model; the case writers give these functions ids in range or 0).
  (0x005C4E60, 0x005C5144, 0x005C52A7, 0x005C5701, 0x005C5944, 0x005C5BEF, 0x005C5E98)
- [I] **Stock rows** (`rows.txt`): start 15 and do 31 on 70 Raise Skeleton (`summon` 363 `necroskeleton`, `pettype` 4)
  and 80 Raise Skeletal Mage (364, 5); start 16 and do 32 on 73 Poison Dagger; start 17 on 74 Corpse Explosion, 83
  Poison Explosion and 351 NihlathakCorpseExplosion; do 55 on 74, 312 mon death sentry and 351; do 63 on 83
  (`srvmissilea` 217 `poisonexplosioncloud`); start 18 and do 59 on 86 Attract (state 57 `attract`); start 19 and do
  62 on 88 Bone Prison (`summon` 344 `bonewall`, `pettype` 0, `summode` 1); start 20 and do 57 on 90 IronGolem (291,
  `pettype` 3); start 21 and do 58 on 95 Revive (`pettype` 6); do 30 on 66 Amplify Damage (state 9), 71 Dim Vision (23
  `dimvision`), 72 Weaken (19), 76 Iron Maiden (55), 77 Terror (56 `terror`), 82 Life Tap (58), 87 Decrepify (60), 91
  Lower Resist (61), 309 Defense Curse (113), 310 Blood Mana (114); do 56 on 75 Clay Golem (289), 85 BloodGolem (290),
  94 FireGolem (292), each `pettype` 3 and `petmax` 1; do 60 on 78 Bone Wall (344, `pettype` 0, `srvmissilea` 207
  `bonewallmaker`); do 61 on 81 Confuse (59 `confuse`). (`rows.txt`, tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc)

### 2. Emulation: the `nec` families

The method is skills/0009's: each case calls the function with `ECX` = the game, `EDX` = the caster and the stack
`(id, lvl)`, and dumps the stack, the caster's and the target's seeds, the caster's `+0xC4` and the second argument's
slot. Emulated, not observed (new for this batch): `0x00645510`, `0x00645680`, `0x0063A770` with
`sub_0063A130_UnitHasStateInMask`, `sub_004638A0_MonStats2FlagTest`, `sub_005541B0_UnitIsDead`, `0x005C3300`,
`0x005C31F0` with `0x006259B0`, start 20's item test (`ITEMS_GetRecord`, `0x00629CC0`, `ITEMS_CheckFlags`,
`STATLIST_GetOwnerUnit`), `0x005C2FF0` up to its `COMBAT_ApplyDamage` with `sub_00625D10_UnitGetMaxHp`,
`0x005C3400`, `0x005C37A0` with `sub_00611D30_DifficultyRec`, `ITEMSTATCOST_GetRecord`, `0x005C5BC0`; skills/0008's and
skills/0009's `UNIT_GetTargetUnit`, `SKILLS_GetTargetXY`, `sub_00620BB0_UnitGetRoom`, `sub_0061AB00_RoomIsTown`,
`sub_00463740_RoomAtSubtile`, `UnitGetSubX/Y`, `sub_0056E620_SkillSummonClass` and `SKILLS_EvalCalc` on constant
programs. Observed (new for this batch): `sub_0056E780_SkillForUnitsNearTarget`, `COMBAT_ApplyDamage`, `0x0061A270`,
`STATE_Set`, `0x0056E2F0`; skills/0009's stay declared (`COMBAT_MeleeHitTest`, `COMBAT_DeliverQueued`,
`SpawnOwnedMonster`, the fatal path's `0x00408090`, …). **New in the checker:** where a boundary sits inside a helper
the batch function called, the helper's return address into the batch function is compared at its absolute stack
slot (start 21 `0x005C3366` at `0x7FEFFFF8`, do 58 `0x005C5738` at `0x7FEFFFA4`, do 59 `0x005C3BE1` at `0x7FEFFF98`,
do 31 `0x005C4B3F` at `0x7FEFFFA8`, do 62 `0x005C5D69` at `0x7FEFFFC8`); `static.txt` also lists every call of each
helper (`0x005C2FF0`: do 31 and do 58 once each; `0x005C3300`: start 21 and do 58 once each; `0x005C31F0`: do 59 and
the callback `0x005C3B30` once each; `0x005C5BC0`: do 62 once; start 20: do 57 once). Do 57's fatal-path cases end two
helpers deep (start 20, then `0x00629CC0`); each is called once on that path (`static.txt`, objdump `0x005C32C3`), and
their return addresses are not compared. Ruling 1's condition is met by the single-site branch: do 57 calls start 20
  once (`static.txt`, `0x005C5265`, its only call in the image) and start 20 calls `0x00629CC0` once (objdump,
  `0x005C32C3`, the only call in `0x005C32A0`–`0x005C32F2`; `0x00629CC0` calls `0x00408090` once, `0x00629CD5`).

- [C] Four families, **6 100 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 1 891 matched boundary cases
  (17 function, boundary and return-address triples, each a `site` line) (`check.txt`; run:2026-10-20-cat-emu-nec):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `start_nec` | start 15–21, do 32 | 1 600 | the town test inverted (274); state set 33 ignored (7); MonStats2 flag 7 for 8 (5); any item mode (9) | MeleeHitTest @0x005C3130; Fatal @0x00629CDA (in `0x00629CC0`); MonTest2F0 @0x005C3340 (in `0x005C3300`); DeliverQueued @0x005C4CFD; returns 0, 1 |
  | `curse_nec` | do 30, 61 | 1 400 | no division for states 23/56 (90); do 61 reading `aurastat1` (319); `aurastat1` −1 refused (76) | NearTarget @0x005C39A3, @0x005C40AF; returns 0 |
  | `corpse_nec` | do 31, 55, 58, 59, 63 | 1 500 | the dead test inverted (44); set 33 ignored (13); `maxhp / 4` (8); a refused `pettype` taken as 0 (12); any alignment (77); `0x00645510`'s flag 1 (4); do 63's range exit 0 (80) | ApplyDamage @0x005C3051 (in `0x005C2FF0`); RoomUnitRemove @0x005C4BE2; StateSet @0x005C4E29, @0x005C5EDA; MonTest2F0 @0x005C3340 (in `0x005C3300`), @0x005C321E (in `0x005C31F0`); returns 0, 1 |
  | `summon_nec` | do 56, 57, 60, 62 | 1 600 | `w24` zero (741); `pettype` kept at or past the count (269); do 62's offsets swapped (322) | SpawnOwned @0x005C51E8, @0x005C537C, @0x005C59F0, @0x005C5CBA (in `0x005C5BC0`); Fatal @0x00629CDA; returns 0, 1 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 38 of 38 pins): the hash offsets, the `CALC_Eval` jump
  table, the skills calc function count `0x007457AC` and `g_BitMask32` (as 9a–9d), the town tables (as `sor`), do 62's
  offsets. The count's scan matches every operand naming the address (a `PTR` or `moffs` store, an immediate, a
  read): 0 stores, 0 immediates, 7 reads in `.text` (`ref_scan`, the condition of ruling 3 of the `lane/p46m5`
  review). Skills, ItemStatCost, MonStats, MonStats2, item records, the stat lists, the bit-set, rooms and units are
  scratch records written one field per field read.
- [C] **Inputs set in the memory spec** (ADR-0015, S1e review ruling 3): `g_pDataTables`, pointed at a scratch
  DataTables, and the `.data` words `g_pDifficultyLevels`/`g_nDifficultyLevels` (`0x0096C8AC`/`0x0096C8B0`) and
  `ITEMS_GetRecord`'s count and table (`0x0096CA58`/`0x0096CA5C`) are inputs of the claims (the claims are maps from
  those bytes; no writer scan is cited for them); the security cookie is written as in 9a. No other image global is
  set. (run:2026-10-20-cat-emu-nec)
- [C] **The weak controls and their deciding classes** (ruling 4 of the `lane/p46m5` review). `start_nec`'s
  `set33_skip` (7), `flag7` (5) and `item_mode` (9) fail exactly on the cases whose target carries a set-33 state
  while passing the rest, whose MonStats2 bits 7 and 8 differ, and whose item is in a mode other than 3 while passing
  the rest; `corpse_nec`'s `set33_skip` (13), `hp4` (8, the class-3 cases whose `maxhp / 8` and `maxhp / 4` differ),
  `pet_zero` (12, a refused `pettype`) and `flag1` (4, a mode-0 target passing the rest) likewise. Each family has a
  control failing 76 or more (`town_inv` 274, `aura1_read` 319, `nomiss0` 80 and `align_any` 77, `w24_zero` 741).
  (run:2026-10-20-cat-emu-nec)
- [C] **Do 57's `w24`.** The case writer puts a random word in the slot `ebp−0x10` (`0x7FEFFFEC`) before the call;
  the block's `+0x24` matches it in all 19 spawn cases, and `w24_zero` fails them. (run:2026-10-20-cat-emu-nec
  `summon_nec`)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills, MonStats2,
  DifficultyLevels and ItemStatCost columns `[C]` by layout; unit, path, item and stat-list offsets `[I]`, skills/0001,
  skills/0008), and nothing here says when the game runs these functions or on which seed state.
  (run:2026-10-20-cat-emu-nec)

### 3. The start functions: 15, 17, 18, 19, 20, 21

```c
// fn:sub_00645510_MonCorpseTest@0x00645510, trimmed
if (!u || u->type != 1) return 0;
if (u->mode != 12 && !(flag && u->mode == 0)) return 0;
if (UnitHasStateSet33(u)) return 0;                     // DataTables+0x150, (nStates + 31) / 32 words
if (!MonStats2FlagTest(u->class, 7)) return 0;          // MonStats2 +0x04 bit 7
return MonStats[u->class].w32 != 0;                     // +0x32
```

- [C] **Start 15** (`0x005C3070`, tier A): `t = UNIT_GetTargetUnit` (none → 0); `RoomIsTown(UnitGetRoom(t))` → 0;
  else `0x00645510(t, 0)` as above. **Start 17** (`0x005C31C0`): the same with `0x00645680(t)`: type 1, mode 12, no
  set-33 state, MonStats2 flag bit 7 → 1. **Start 19** (`0x005C3270`): no target → 0, else `RoomIsTown(…) ? 0 : 1`
  (`neg; sbb; add 1`). **Start 18** (`0x005C3260`) returns 1. (run:2026-10-20-cat-emu-nec `start_nec`,
  fn:sub_00645510_MonCorpseTest@0x00645510, fn:sub_00645680_MonCorpseTestDead@0x00645680,
  fn:sub_0063A130_UnitHasStateInMask@0x0063A130)
- [I] By the layouts, MonStats2 `+0x04` bit 7 is `corpseSel` and bit 8 (`+0x05` bit 0) `revive`
  ([MonStats2](../../tables/MonStats2.md)); MonStats `+0x32` is `Velocity`; set 33 is the States flag `udead`
  ([States](../../tables/States.md)); mode 12 is a monster's death mode as skills/0003 § 5 reads it. Why the corpse
  test reads `Velocity` is not read. A class outside `[0, MonStats count)` makes `0x00645510` read `+0x32` through a
  null record (0x0064557F), a fault the emulator does not model (the case writers give classes in range).
  (tbl:States.txt:udead, tbl:MonStats2.txt:corpseSel, tbl:MonStats.txt:Velocity, 0x00645554)
- [C] **Start 20** (`0x005C32A0`): the target (none → 0) must be type 4 with `+0x10` = 3; `0x00629CC0(class)` returns
  `ITEMS_GetRecord(class)+0xDC & 2` (0 → refuse), and with no record (class at or past `0x0096CA58`, unsigned) ends at
  the fatal path (ADR-0021, `0x00408090` @0x00629CDA, its pushed word `0x104A`); `ITEMS_CheckFlags(t, 0x10, 0x100,
  file)` (the data `+0x14`, its `+0x18 & 0x10`, 0 without data); then returns `STATLIST_GetOwnerUnit(t, 0) == 0`
  (`+0x5C` → `+0x34` → with `+0x10` bit 31 its `+0x44`, else 0). (run:2026-10-20-cat-emu-nec `start_nec`,
  fn:sub_005C32A0_SkillSt20ItemTarget@0x005C32A0, fn:sub_00629CC0_ItemRecFlag2@0x00629CC0,
  fn:ITEMS_CheckFlags@0x006280A0, fn:STATLIST_GetOwnerUnit@0x00625820)
- [C] (ADR-0021; ends at `0x0056E2F0` @0x005C3340, helper return `0x005C3366` compared) **Start 21** (`0x005C3350`):
  the target (none → 0), then `0x005C3300` with the target in `ESI`: type 1, `MonStats2FlagTest(class, 8)`,
  `UnitIsDead(t)` **non-zero** (`+0xC6` bit 0, or a monster in mode 0 or 12), `0x00645510(t, 0)`, each 0 → 0; then
  `0x0056E2F0(ECX t, EDX 7)`. After, `[I]`: its result (`neg; sbb; neg`) is the start's; `0x0056E2F0` gives 0 for
  base class 492 carrying state 143, else `0x005DD480(t, 7)`, not read. (run:2026-10-20-cat-emu-nec `start_nec`,
  fn:sub_005C3300_ReviveTargetTest@0x005C3300, fn:sub_005541B0_UnitIsDead@0x005541B0)
- [I] So, with the layouts, Raise Skeleton and the corpse explosions take a dead, `corpseSel` monster not carrying a
  `udead` state, outside town; Revive also needs `revive`; IronGolem an item of a record with `+0xDC` bit 1 lying in
  mode 3. Which item column `+0xDC` bit 1 is, and what mode 3 is, are not read here. (`rows.txt`,
  tbl:MonStats2.txt:revive, fn:sub_00645680_MonCorpseTestDead@0x00645680)

### 4. Start 16, do 32 and the curses (do 30, do 61)

- [C] (ADR-0021; ends at `COMBAT_MeleeHitTest` @0x005C3130) **Start 16** (`0x005C30A0`): the target (none → 0), the
  town test (→ 0), the record (→ 0), a zeroed 0x70-byte packet at `ebp−0x78`, `MeleeHitTest(game, caster; target,
  SKILLS_GetToHit(caster, id, lvl), 0)` (skills/0009 § 4's rule). After, `[I]`: on a hit `calc1` into the packet's
  `+0x0C`, the `EType`/`calc4` conversion, `SKILLS_RollElemDamage`, `COMBAT_ResolveAndQueue(SrcDam or 0x80)`; returns
  1. (run:2026-10-20-cat-emu-nec `start_nec`, fn:sub_005C30A0_SkillSt16PoisonDagger@0x005C30A0)
- [C] (ADR-0021; ends at `COMBAT_DeliverQueued` @0x005C4CFD) **Do 32** (`0x005C4CD0`): bit 6 first, then the target
  (none → 0) and `DeliverQueued(game, caster; target, 0)`; it reads no record. After, `[I]`: returns 1.
  (fn:sub_005C4CD0_SkillDo32PoisonDagger@0x005C4CD0)

```c
// fn:sub_005C37C0_SkillDo30Curse@0x005C37C0, trimmed
if (!rec || (s16)rec->aurastat1 < -1 || rec->aurastat1 >= nISC || rec->auratargetstate outside [0, nStates)) return 0;
unit->c4 |= 0x40;
f = CurseStateDiffFlag(auratargetstate);            // 23 or 56
r = EvalCalc(aurarangecalc);  len = EvalCalc(auralencalc);  if (f) len = DiffDivide(game->diff, len);
blk = {game, unit, f, 0, id, lvl, len};
for (i = 0; i < 6; i++) { s = aurastat[i]; if (s < 0 || s >= nISC) { blk.stat[i] = -1; break; }
                          if (ISC[s].b5 & 2) blk.s = 1;  blk.stat[i] = s;  blk.val[i] = EvalCalc(aurastatcalc[i]); }
blk.state = auratargetstate;  blk.ev[0..2] = auraevent1..3;  blk.evf[0..2] = auraeventfunc1..3;   // movsx
return SkillForUnitsNearTarget(game, aurafilter; unit, r, 0x005C35C0, &blk);
```

- [C] (ADR-0021; ends at `ForUnitsNearTarget` @0x005C39A3) **Do 30** (tier A): as above. The `aurastat1` test is a
  16-bit signed `cmp ax, 0xFFFF; jl` (pinned 0x005C3803), so −1 passes; `f` is `0x005C3400(state)`: 1 for 23 or 56;
  `DiffDivide` takes the game's `+0x6D` byte (`movzx`), `sub_00611D30_DifficultyRec` clamps it to `[0, count − 1]`,
  and divides by the record's `+0x1C` (`idiv`, truncating) when that word is non-zero. Block (0x68 bytes at `ebp−0x7C`,
  compared by content): `+0x00` game, `+0x04` caster, `+0x08 f`, `+0x0C s`, `+0x10` id, `+0x14` lvl, `+0x18` len,
  `+0x1C` six stats (the first out-of-range one −1, the rest 0), `+0x34` six values, `+0x4C` `auratargetstate`,
  `+0x50..+0x64` `auraevent1..3` and `auraeventfunc1..3` (each `movsx`). `ECX` game, `EDX` `aurafilter` (`+0x50`),
  stack `(caster, aurarangecalc, 0x005C35C0, &block)`. (run:2026-10-20-cat-emu-nec `curse_nec`,
  fn:sub_005C3400_CurseStateDiffFlag@0x005C3400, fn:sub_005C37A0_DiffDivide@0x005C37A0,
  tbl:Skills.txt:auratargetstate, tbl:Skills.txt:aurastat1)
- [C] (ADR-0021; ends at `ForUnitsNearTarget` @0x005C40AF) **Do 61** (`0x005C3F20`): the same tests and bit 6; `len`
  divided always; the block at `ebp−0x78` with `+0x08` 0, `+0x0C s`, the stat loop from `aurastat2` (`lea ecx,
  [edi+0x56]`, `esi = 1`, pinned) into words 1–5 (word 0 stays 0) with `aurastatcalc2..6`, `+0x4C` the state, no event
  words; callback `0x005C3DE0`. (run:2026-10-20-cat-emu-nec `curse_nec`, fn:sub_005C3F20_SkillDo61Confuse@0x005C3F20)
- [I] Stock: the length division applies to Dim Vision (23 `dimvision`) and Terror (56 `terror`) among do 30's rows,
  and always to Confuse; `+0x1C` is `AiCurseDivisor` (1/2/4 by difficulty, [DifficultyLevels](../../tables/DifficultyLevels.md)).
  ItemStatCost byte `+5` bit 1 is `UpdateAnimRate` by the layout (Decrepify's `velocitypercent`). After, `[I]`: the
  callbacks (`sub_005C35C0_CurseApplyCb`, skills/0003 § 5; `0x005C3DE0`, not read) apply the state per unit.
  (tbl:ItemStatCost.txt:UpdateAnimRate, tbl:DifficultyLevels.txt:AiCurseDivisor)

### 5. Corpses: do 31, 55, 58, 59, 63

- [C] (ADR-0021; ends at `COMBAT_ApplyDamage` @0x005C3051 inside `0x005C2FF0`, helper return `0x005C4B3F` compared, or
  at `0x0061A270` @0x005C4BE2) **Do 31** (tier A): the target (none → 0) and `0x00645510(t, 0)` (0 → 0); then
  `0x005C2FF0(game, caster; id, lvl)`: for a caster of type 0 and class (`+0x04`) 3, a zeroed 0x70-byte packet with
  `+0x00 |= 0x1000`, `+0x04 |= 4` (u16), `+0x08` and `+0x4C` = `UnitGetMaxHp(caster) / 8` (`cdq; and edx, 7; add; sar
  3`, truncating), and `COMBAT_ApplyDamage(game, caster; caster, 0, &packet)`; any other caster returns. Then the
  record (→ 0), `SkillSummonClass(ECX caster, EDX 0; id, lvl, &mode, 0, 0)` (below 0 → 0), `pettype` read **`movsx`**
  (pinned 0x005C4B97) and refused below 0 or at or past the PetType count, the target's position
  (`UnitGetSubX/Y`), and `0x0061A270(UnitGetRoom(t), t→type, t→guid)` with the frame words record, class, mode, x, y
  and pet type (`ebp−0x4` to `ebp−0x18`) compared. After, `[I]`: `sub_00555600_UnitFree(t)`, the block `{1, caster,
  class, 0, mode, x, y, pettype, petmax}`, `SpawnOwnedMonster`, skills/0003 § 7's level and stats; returns 1.
  (run:2026-10-20-cat-emu-nec `corpse_nec`, fn:sub_005C2FF0_SkillClass3SelfHit@0x005C2FF0,
  fn:sub_00625D10_UnitGetMaxHp@0x00625D10, tbl:Skills.txt:pettype)
- [I] What the packet means to `COMBAT_ApplyDamage`: `+0x08` the physical damage and `+0x4C` the life removed
  (1/256 units, `re/types/combat.h`), result 4 a get-hit; after `COMBAT_ApplyDamage` returns, `0x005C2FF0` calls
  `COMBAT_GetHit(ECX game, EDX caster; caster, &packet)` with the same packet (0x005C305A); class 3 is the paladin in the PlayerClass order the Skills
  `charclass` codes follow. So a paladin casting Raise Skeleton, Raise Skeletal Mage or Revive (an item charge) loses
  1/8 of its maximum life as a hit on itself; no other class does. (`rows.txt`, re/types/combat.h,
  fn:COMBAT_ApplyDamage@0x0057C6C0, fn:COMBAT_GetHit@0x0057CEE0)
- [C] (ADR-0021; ends at `STATE_Set` @0x005C4E29 or @0x005C5EDA) **Do 55** (`0x005C4DF0`): the target (none → 0),
  `0x00645680(t)` (0 → 0), `STATE_Set(t, 0x68, 1)`. **Do 63** (`0x005C5E60`): id 0 → 0; `srvmissilea` (`+0x48`, s16)
  outside `[0, Missiles count)` → **1** (both tests jump to the `mov eax, 1` exit at 0x005C5EFC); the target (none →
  0), `0x00645680(t)` (0 → 0), `STATE_Set(t, 0x76, 1)`. (run:2026-10-20-cat-emu-nec `corpse_nec`,
  fn:sub_005C4DF0_SkillDo55CorpseExpl@0x005C4DF0, fn:sub_005C5E60_SkillDo63PoisonExpl@0x005C5E60)
- [I] After do 55's call: `0x0064C040(t)`, the record (id 0 → 0), the corpse's base `maxhp` (stat 7); for a monster
  corpse, the level-row value `(a + b) << 7` of `sub_006538A0_MonLvlStats`; `lo = MulDiv(calc1, life, 100)`, `hi =
  MulDiv(calc2, life, 100)` and `RNG_RangeB(t + 0x20, hi − lo) + lo` **on the corpse's seed**; scaled by caster level /
  corpse level when the corpse's is higher; `calc3` (0..100) of it moved to `EType` (`0x0056C8E0`); then
  `SKILLS_ForUnitsInRange(x, y, (r + 1)/2, aurafilter, 0x005C4D10, …)` with `r = aurarangecalc`, whose callback drops
  the physical share for units beyond `r/2` and calls `COMBAT_ApplyDamage` and `COMBAT_GetHit`; returns 1. After do
  63's: `0x0064C040(t)` and `sub_005A9370_MissSubRing16(t, srvmissilea, id, lvl, 0, 2, 0)` (skills/0007); returns 1.
  (0x005C4E29–0x005C509C, 0x005C5EDA–0x005C5F07)
- [C] (ADR-0021; ends at `0x0056E2F0` @0x005C3340 inside `0x005C3300`, helper return `0x005C5738` compared) **Do 58**
  (`0x005C56C0`): id 0 → 0; `pettype` (`movzx`) at or past the PetType count stored as 0 in the frame byte `ebp−0x1`
  (compared); the target (none → 0); start 21's test (§ 3) → 0 when it fails. After, `[I]`: `0x005C2FF0` (the class-3
  hit above), `0x005C5430(game; ESI t)`, the life `RNG_RangeB(t + 0x20, max − min + 1) + min` from
  `MonLvlStats` **on the target's seed**, `<< 8` into stats 7 and 6; when the target's level (stat 12) is above the
  caster's, the life scaled by caster level / target level (at least 1) and stat 12 set to the caster's;
  `SummonInitStats`, `sub_005C55C0_SummonFinish`, `PetAdd(pettype, petmax)`, the target list;
  returns 1. (run:2026-10-20-cat-emu-nec `corpse_nec`, fn:sub_005C56C0_SkillDo58Revive@0x005C56C0,
  0x005C5747–0x005C58A8)
- [C] (ADR-0021; ends at `0x0056E2F0` @0x005C321E inside `0x005C31F0`, helper return `0x005C3BE1` compared) **Do 59**
  (`0x005C3B90`): the record (→ 0); the target; `0x005C31F0(game, caster; t)`: no target → 0, `0x006259B0(t)` (the
  alignment of skills/0008 § 4) non-zero → 0, then `0x0056E2F0(ECX t, EDX 0x13)`. (run:2026-10-20-cat-emu-nec
  `corpse_nec`, fn:sub_005C31F0_AttractTargetTest@0x005C31F0)
- [I] After do 59's test: `0x0056E2F0`'s result, then `UnitIsDead`, the town test and `UnitsHostile` (each 0 → 0);
  the `aurastat1`/`auratargetstate` range tests, bit 6, `sub_005543B0_MonAlignSet(t, 1; 1)`, the target list (9),
  `0x0056E580(t)`, the radius and the divided length, `ForUnitsNearTarget(…, 0x005C3B30, …)`, and
  `STATE_ApplyTimed(t, auratargetstate)` with callback `0x005C3B00`; returns 1. (0x005C3BE1–0x005C3D3B)

### 6. Summons: do 56, 57, 60, 62

- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005C51E8) **Do 56** (`0x005C5100`): bit 6 first; id 0 → 0; `summon`
  (`+0xBC`, a signed 16-bit compare with 0, then against the MonStats count) out of range → 0; `pettype` (`movzx`) at or
  past the count becomes 0 (stored, not refused; pinned by `pet_keep`); `summode` (unsigned byte) 16 or more → 1 (pinned 0x005C5186); the block at `ebp−0x28`: `{0,
  caster, summon, 0, mode, 0, 0, pettype, petmax, game}`, the last word being the slot `ebp−0x4` where the function
  stored `ECX` at 0x005C510F (pinned). (run:2026-10-20-cat-emu-nec `summon_nec`, fn:sub_005C5100_SkillDo56Golem@0x005C5100)
- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005C537C, or at the fatal path @0x00629CDA inside start 20) **Do 57**
  (`0x005C5250`): start 20's test (§ 3; 0 → 0), bit 6, id 0 → 0, `SkillSummonClass` (→ 0 below 0), `pettype` as do
  56; the position first the caster's, then the target item's (`UnitGetSubX/Y`: its static path `+0x0C`/`+0x10`); the
  block at `ebp−0x34`: `{1, caster, class, 0, mode, x, y, pettype, petmax, w}` where `w` is the slot `ebp−0x10`, which
  no instruction of do 57 writes before the call. (run:2026-10-20-cat-emu-nec `summon_nec`,
  fn:sub_005C5250_SkillDo57IronGolem@0x005C5250)
- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005C59F0) **Do 60** (`0x005C58B0`): `SKILLS_GetTargetXY` (none → 0);
  `RoomAtSubtile(UnitGetRoom(caster), x; y)` none → 0; a town room → 0; bit 6; id 0 → 0; `SkillSummonClass`;
  `pettype` as do 56; the block at `ebp−0x38`: `{9, caster, class, 0, mode, x, y, pettype, petmax, game}` (the game
  stored at `ebp−0x14` at 0x005C58C9, pinned). (fn:sub_005C58B0_SkillBoneWallDo@0x005C58B0)
- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005C5CBA inside `0x005C5BC0`, helper return `0x005C5D69` compared)
  **Do 62** (`0x005C5D00`): `SKILLS_GetTargetXY` (none → 0); bit 6; for `i` = 0..11 (frame word `ebp−0x8` = `4i`,
  compared) `0x005C5BC0(EAX caster, EBX id; game, x + dx[i], y + dy[i], lvl)`: id 0 → 0; `SkillSummonClass`;
  `pettype` as do 56; `RoomIsTown(RoomAtSubtile(UnitGetRoom(caster), X; Y))` (a null room is not a town room) → 0 and
  the next `i`; else the block at the helper's `ebp−0x30`: `{9, caster, class, 0, mode, X, Y, pettype, petmax, mode}`
  (the last word the mode slot `ebp−0xC`). No piece reached → 1. (run:2026-10-20-cat-emu-nec `summon_nec`,
  fn:sub_005C5BC0_BonePrisonPiece@0x005C5BC0, data:g_BonePrisonOffX@0x006E304C, data:g_BonePrisonOffY@0x006E307C)
- [I] After the spawns: do 56 `0x005C50C0` (`SummonSetLevel`, `SummonInitStats`, `0x005C40D0`), an event and the target
  list; do 57 calls `0x0061A270`, `0x00623830`, `0x0064C370`, `0x0062EA80` and `SetMode(4)` on the item and
  `0x005606B0(golem, item guid, …)` before `0x005C50C0`; do 60 sets the owner, mod 15, `SummonInitStats`, the target list, and
  outside town with `calc2 / 2 > 1` and `srvmissilea` in range makes two `MissileCreate` calls (flags `0x21`) aimed
  at the piece's position offset by `(−dy, dx)` and `(dy, −dx)`, `(dx, dy)` the caster less the piece; do 62 links each later piece to the first (`MonSetOwner`, `0x0058F100`), places it (`0x0064FDC0`) and
  continues the loop over the twelve offsets; each returns 1 with a spawn. What `SpawnOwnedMonster` makes of `+0x24`
  (the game pointer, a stale frame word, the mode) is not read (Open questions). (0x005C51E8–0x005C523A,
  0x005C537C–0x005C542C, 0x005C59F0–0x005C5BA6, 0x005C5CBA–0x005C5E52)

## Corrections to earlier findings

- skills/0003 § 5 (tier A), carried there as a dated note: start 15, do 30 and do 31 are now `[C]` up to their
  boundaries (ADR-0021) with four refinements: start 15's corpse test also refuses a monster carrying a state of the
  `DataTables+0x150` bit-set and one whose MonStats `+0x32` word is 0; do 30's `aurastat1` test admits −1; its block
  carries the `+0x08` difficulty-division flag and the `+0x0C` stat flag; do 31 runs `0x005C2FF0` (a class-3 player
  caster's self-hit) before its record test, and reads `pettype` signed.

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `srvmissilea`, `aurafilter`, `aurastat1..6`, `aurastatcalc1..6`,
`auralencalc`, `aurarangecalc`, `auratargetstate`, `auraevent1..3`, `auraeventfunc1..3`, `summon`, `pettype`,
`summode`, `petmax`, `ToHit`, `LevToHit`, `ToHitCalc`, `calc1..3`, `EType`, `SrcDam` (after, read only);
`tbl:MonStats.txt:MonStatsEx`, `Velocity`; `tbl:MonStats2.txt:corpseSel`, `revive`;
`tbl:DifficultyLevels.txt:AiCurseDivisor`; `tbl:ItemStatCost.txt:UpdateAnimRate`; `tbl:States.txt:udead` (the
bit-set); item records `+0xDC`; unit `+0x00`, `+0x04`, `+0x0C`, `+0x10` mode, `+0x14` data, `+0x20` seed, `+0x2C`
path, `+0x5C` stat list (`+0x34`, `+0x58` state words), `+0xC4` bit 6, `+0xC6` bit 0; game `+0x6D`.

## Dead ends

- None. The first emulation of each family ran once with model faults (do 63's range exit, do 31's room-call
  arguments, the fatal path's return address), fixed in the models and re-run; the kept outputs are the re-runs'.

## Open questions

- [L] What `0x0056E2F0` (its `0x005DD480`) tests for the codes 7 and `0x13`, and so which monsters Revive and Attract
  refuse (§§ 3, 5).
- [L] What `SpawnOwnedMonster` does with a block `+0x24` holding the game pointer (do 56, 60), a frame word do 57
  had not written before the call (it writes it after, through `0x0062EA80`), or the mode (do 62) (§ 6; skills/0009's Open question on `+0x24`).
- [L] Whether the class-3 self-hit of § 5 is seen in play (a paladin with Raise Skeleton or Revive charges), a
  harness check.
- [L] Which item column `+0xDC` bit 1 is and what item mode 3 is (start 20), and why the corpse test reads MonStats
  `+0x32` (§ 3).
- [L] Everything after each boundary (§§ 3–6), for a later batch or the harness.
