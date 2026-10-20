# 0011 — Catalogue batch `pal`: the paladin start functions 29, 31, 35, 36, 37 and do functions 64–67, 73, 79–82 and 150

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 29, 31, 35, 36 and 37 (`srvstfunc`, `g_SkillStartFuncs`) and do
> function 64–67, 73, 79–82 and 150 (`srvdofunc`, `g_SkillDoFuncs`) of the paladin batch do: which Skills, CharStats,
> MonStats and unit fields it reads, which states, missiles and hits it makes, which draws it makes on which seed, what
> it returns, and which of that the emulator can confirm?
> **Date:** 2026-10-20   **Plan:** 0046 (Phase 1, batch `pal`)   **Status:** for review (`lane/p46m8`)

Static reading of the pinned `Game.exe` with objdump (and the lane's Ghidra copy `workspace/ghidra-p46m8` for the
emulation), then emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged, `286393aa…`) and the
`pal` families of `tools/skills_catalogue_emu.py` (§ 2; run:2026-10-20-cat-emu-pal in [experiments](experiments.md)).
Skills columns are named as in [Skills](../../tables/Skills.md), CharStats and MonStats columns as in
[CharStats](../../tables/CharStats.md) and [MonStats](../../tables/MonStats.md). The machinery that calls a start or do
function is [skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart); the tier-A entries of
this batch (start 36, do 65, do 66) were read by plan 0045 in
[skills/0003 § 5](0003-handlers.md#5-tier-a-start-and-do-functions) and by plan 0041 in
[stats/0002 § 4](../stats/0002-states.md#4-auras-and-passives), and all three are emulated here. Do 65, 66, 81 and 82
pass the source path `0x006E323C` to `SKILLS_ForUnitsInRange` (lines `0x1F6`, `0x2BA`, `0x6BA`, `0x753`). Start 37
lies among the amazon functions (`0x005DAF40`, between start 9 and start 10). Stock values come from
`workspace/logs/skills-cat-pal/rows.txt` (`excel_bin.py dump` of the 35 Skills rows whose `srvstfunc` is 29, 31,
35–37 or whose `srvdofunc` is 64–67, 73, 79–82 or 150, plus the rows that share their start or do number, by
`rows.sh` beside it).

**Tag convention for this finding** (as skills/0010). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a
function entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site
(the return address at ESP), with a site control that fails every matched boundary case, and where the boundary sits
inside a helper the batch function called, the helper's return address into the batch function at its absolute stack
slot, or the helper's single call site is shown from objdump (ruling 1 of the `lane/p46m6` review as extended at the
`lane/p46m7` review; § 2); (c) the model gives and the checker compares every argument the claim uses (registers,
stack words, and for a pointer the bytes it points to), every byte written before the call that the claim uses (the
caster's `+0xC4`, the used-skill node's words, frame words of the batch function), and the state of **the caster's and
the target's seeds** at the boundary (both, in every case). Each such claim names the boundary it ends at; **the callee
and all code after it are not covered** and keep `[I]` (from the reading), marked "after, `[I]`" in place, and what a
callee makes of a compared argument is stated after the boundary (reverser review-fixes 13). No claim rests on a
callee-saved register that is not a boundary argument (ruling 1 of the `lane/p46m3` review). A plain `[C]` rests on
cases that return; a plain `[I]` is a code reading the emulator does not reach. (run:2026-10-20-cat-emu-pal)

## Answer (summary)

- [C] **The batch.** 15 entries: start 29 `0x005CE790`, 31 `0x005CF6B0`, 35 `0x005CFE10`, 36 `0x005D0180`, 37
  `0x005DAF40`; do 64 `0x005CE8E0`, 65 `0x005CF010`, 66 `0x005CF3A0`, 67 `0x005CF900`, 73 `0x005D0040`, 79
  `0x005D0350`, 80 `0x005D0670`, 81 `0x005D0920`, 82 `0x005D0E90`, 150 `0x005CE9F0`. Every one is `(ECX game, EDX
  unit; skill id, level)` with `ret 8`. All 15 are emulated. (data:g_SkillStartFuncs@0x00732140,
  data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [C] **No draw before the boundaries.** No function of the batch steps the caster's or the target's seed before its
  boundary or return (4 950 cases, both seeds compared in each). (run:2026-10-20-cat-emu-pal)
- [C] (ADR-0021; up to `AURA_ApplyToTarget` @0x0056B75F inside `0x0056B740`, or `SKILLS_ForUnitsInRange` @0x005CF229,
  § 3) **The aura functions.** Do 65, 66, 81 and 82 compute a cost `((lvl − 1) · lvlmana + mana) << (manashift & 31)`
  (`0x00644B10`), an end `SKILLS_NextPeriodicFrame + 1 − frame` (`p` = `perdelay` calc, 5 when it gives 5 or less), and a
  zeroed 0x50-byte block `{+0x00 state, +0x04 id, +0x08 lvl, +0x0C end, +0x10 five or six stats, +0x28 their values,
  +0x48, +0x4C}`; the values are evaluated unless the caster is a player (type 0) whose stat 8 is below the cost
  (signed). Then `0x0056B740(ECX game, EDX caster; 0x005CEDC0, &block)` builds `{game, caster, 0, &block}` and calls
  `AURA_ApplyToTarget(ECX &context, EDX caster)`. Do 65's block takes `aurastat1..6` (up to the first one below 0) with
  `aurastatcalc1..6`, `+0x48` = `passivestate` when it is above 0, and `+0x00` = `aurastate` when it is in `(0, States
  count)`; otherwise `auratargetstate` in `[0, States count)` and `SKILLS_ForUnitsInRange(game, caster; 0, 0,
  aurarangecalc, aurafilter, 0x005CEDC0, &block, 1, file, 0x1F6)`, and with neither it returns 1. Do 66, 81 and 82 refuse
  (0) an `aurastate` outside `[0, States count)`, and take `passivestat1..5` with `passivecalc1..5` (all five, no stop;
  do 82 skips the value of a stat below 0); do 81 puts `0x005D0770` at `+0x4C`.
- [C] (ADR-0021; § 4) **The melee functions.** Start 29 (Sacrifice) and do 150 (Smite) end at
  `sub_00622C40_InMeleeRange(caster, target, 0)`; start 35 (Vengeance) ends at `COMBAT_MeleeHitTest(target,
  SKILLS_GetToHit(caster, id, lvl), 0)` with a zeroed 0x70-byte packet and **no range test**; start 36 (Holy Shield)
  returns 0 without an inventory (`+0x60`) and reads **no skill record**, else ends at `0x0063C8F0(inventory, 0)`; start
  37 (Zeal, Fury, BloodLordFrenzy) runs `sub_0056E510_UnitMeleeReachPlus4` (skills/0009's ends) and, with a target,
  writes `calc1`, the target's type and guid into the used skill's `+0x18`/`+0x1C`/`+0x20` and returns 1, else ends at
  `sub_0056BD10_NearestUnitInRange(0, 0, reach + 4, 0x20003, −1, 0)`. Do 64 (Sacrifice) finds the caster's queued hit
  on the target (`sub_0057D690_QueuedHitFind`; none → 1) and ends at `COMBAT_ApplyDamage(game, caster; caster, 0,
  &packet)` with `{+0x00 0x1000, +0x08 and +0x4C = MulDiv(min(queued +0x08, target stat 6), calc2, 100)}`; do 79
  (Conversion) sets bit 6, and with a target and its queued hit on a non-hireling monster of alignment 0 ends at
  `0x0056E2F0(ECX target, EDX 0xB)` inside `0x005D02B0`, otherwise at `COMBAT_DeliverQueued(game, caster; target, 0)`.
- [C] (ADR-0021; § 5) **Charge and the missiles.** Start 31 (Charge, SerpentCharge) refuses without a used skill or a
  caster path; with a target it ends at `InMeleeRange(caster, target, 0)`; without one it writes 6, 0 and 7 into the
  used skill's `+0x18`, `+0x1C`, `+0x24` and ends at `sub_00648690_PathSetSpeed(path, MulDiv(base, max(stat 67, 50) +
  Param1, 100))`, `base` the CharStats byte `+0x41` `<< 8` (0x100 without a record), or for a monster whose MonStats
  record exists at `0x00649050(path)`. Do 67 (Charge) refuses without a used skill and ends at `0x006633B0(caster)`.
  Do 73 (Blessed Hammer) and do 80 (Fist of the Heavens) take `SrvMissileByCharge` and refuse a class of **0 or less**;
  do 73 needs the target point, sets bit 6 and ends at `MissileCreate` with `{flags 0x20, owner and source the caster,
  class, +0x1C/+0x20 the point, id, lvl}` (no start point); do 80 needs a target unit, does **not** set bit 6, and
  passes `{flags 1, owner, class, +0x14/+0x18 the target's position, id, lvl}`.
- [I] After, from the reading: the aura functions' target pass, its per-unit callbacks and the draws they make (do 66
  one `SKILLS_RollElemDamage` per run on the caster's seed, its packet copied to every unit; do 81's 20 % roll per unit
  on **the unit's** seed by an inline LCG step; do 82's `RNG_Range(caster, 100)` per unit `0x006456D0` accepts); start 35's weapon roll by
  an inline LCG step on the caster's seed (`0x005CFD20`); do 79's `RNG_Range(caster, 100)` against `calc1` inside
  `0x005D02B0`; and every callee boundary listed per function. Nothing in the batch tests the caster's class; no
  paladin function calls `0x005C2FF0` (skills/0010's class-3 self-hit; § 6).
  (fn:sub_005CF3A0_AuraHitDo@0x005CF3A0, fn:sub_005D07C0_HolyFreezeUnitCb@0x005D07C0)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005CE790` | `sub_005CE790_SkillSt29Sacrifice` | start 29 | I |
| `0x005CE8E0` | `sub_005CE8E0_SkillDo64SacrificeSelfHit` | do 64 | I |
| `0x005CE9F0` | `sub_005CE9F0_SkillDo150Smite` | do 150 | I |
| `0x005CF010` | `sub_005CF010_PalAuraDo` | (stats/0002 name) do 65 | I |
| `0x005CF3A0` | `sub_005CF3A0_AuraHitDo` | (stats/0002 name) do 66 | I |
| `0x005CF2A0` | `sub_005CF2A0_AuraHitUnitCb` | do 66's per-unit callback (read, § 3) | I |
| `0x005CF6B0` | `sub_005CF6B0_SkillSt31Charge` | start 31 | I |
| `0x005CF8C0` | `sub_005CF8C0_ChargeAnimIndex` | `(ECX unit)`: −1 when `0x006633B0`'s record has byte `+0x05` = 0 and `0x006633F0` is above 0, else 7 (the loop tests the one byte read before it; do 67) | I |
| `0x005CF900` | `sub_005CF900_SkillDo67Charge` | do 67 | I |
| `0x005CFD20` | `sub_005CFD20_VengeanceWeaponRoll` | `(ESI unit)`: the weapon damage roll by an inline LCG step (start 35, after its boundary) | I |
| `0x005CFE10` | `sub_005CFE10_SkillSt35Vengeance` | start 35 | I |
| `0x005D0040` | `sub_005D0040_SkillDo73BlessedHammer` | do 73 | I |
| `0x005D0180` | `sub_005D0180_SkillSt36NeedShield` | (P1.3 name) start 36 | I |
| `0x005D01A0` | `sub_005D01A0_ConversionRemoveCb` | do 79's state-list remove callback (not read beyond its calls) | I |
| `0x005D02B0` | `sub_005D02B0_ConversionTest` | `(EAX id, EBX target; caster, lvl, roll)`, `ret 0xC`: § 4 | I |
| `0x005D0350` | `sub_005D0350_SkillDo79Conversion` | do 79 | I |
| `0x005D0670` | `sub_005D0670_SkillDo80FistHeavens` | do 80 | I |
| `0x005D0770` | `sub_005D0770_HolyFreezeRemoveCb` | do 81's block `+0x4C` (not read beyond its calls) | I |
| `0x005D07C0` | `sub_005D07C0_HolyFreezeUnitCb` | do 81's per-unit callback (read, § 3) | I |
| `0x005D0920` | `sub_005D0920_SkillDo81HolyFreeze` | do 81 | I |
| `0x005D0D70` | `sub_005D0D70_RedemptionUnitCb` | do 82's per-unit callback (read, § 3) | I |
| `0x005D0E90` | `sub_005D0E90_SkillDo82Redemption` | do 82 | I |
| `0x005DAF40` | `sub_005DAF40_SkillSt37Zeal` | start 37 | I |
| `0x0056B740` | `sub_0056B740_SkillCallOnSelf` | `(ECX game, EDX unit; fn, arg)`, `ret 8`: `fn(ECX &{game, unit, 0, arg}, EDX unit)` | I |
| `0x00644B10` | `sub_00644B10_SkillManaCost` | `(id, lvl)`, `ret 8`: § 3 | I |
| `0x00644620` | `sub_00644620_UnitSkillSet24` | node `+0x24` = arg | I |
| `0x00644660` | `sub_00644660_UnitSkillSet0C` | node `+0x0C` = arg | I |
| `0x006446A0` | `sub_006446A0_UnitSkillGet0C` | node `+0x0C`, 0 without a node | I |
| `0x004C9460` | `sub_004C9460_SkillGetParam1` | `(ECX id)`: Skills `+0x148`, 0 for an id out of range | I |
| `0x0063C8F0` | `sub_0063C8F0_InvItemQuery` | `(inv, out)`: start 36's and do 150's inventory call (not read) | I |
| `0x006633B0` | `sub_006633B0_UnitAnimData` | `(unit)`: `0x00663310`'s record `+0x00` (the animation data; not read further) | I |
| `0x00649050` | `sub_00649050_PathOp9050` | `(path)`: start 31's monster path call (not read) | I |

## Walkthrough

### 1. The table slots and the shared shape

- [C] `g_SkillStartFuncs[29, 31, 35, 36, 37]` and `g_SkillDoFuncs[64..67, 73, 79..82, 150]` are the Functions table's
  addresses (15 entries compared, `table_entries=15`). (data:g_SkillStartFuncs@0x00732140,
  data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [I] Every function but start 36 tests `0 ≤ id < DataTables+0xBA0` and a non-null record (`DataTables+0xB98 + 0x23C
  · id`) first and returns 0 when it fails. Start 36 is `mov eax, [edx+0x60]; test; jne; ret 8`, then
  `0x0063C8F0(eax, 0)`, `neg; sbb; neg`. (0x005D0180–0x005D0198)
- [I] **Stock rows** (`rows.txt`): start 29 and do 64 on 96 Sacrifice; do 150 on 97 Smite; do 65 on 98 Might, 99
  Prayer (`mana` 16, `lvlmana` 3, `manashift` 4), 100 Resist Fire (`passivestate` 181 `passive_resistfire`), 103
  Thorns, 104 Defiance, 105 Resist Cold (182), 108 Blessed Aim (`passivestate` 67), 109 Cleansing, 110 Resist Lightning
  (183), 113 Concentration, 115 Vigor, 120 Meditation, 122 Fanaticism, 125 Salvation, 296 Barbs Aura, 297 Wolverine
  Aura, 298 Oak Sage Aura (`aurastate` the `…control` states 161–163, `auratargetstate` 147–149); do 66 on 102 Holy
  Fire, 118 Holy Shock (neither has an `auratargetstate`), 119 Sanctuary (`mana` 1), 123 Conviction; do 81 on 114 Holy
  Freeze (`aurastate` 43 `holywind`, `auratargetstate` 44 `holywindcold`); do 82 on 124 Redemption; start 31 and do 67 on
  107 Charge and 352 SerpentCharge (`Param1` 150 both); start 35 on 111 Vengeance; start 36 on 117 Holy Shield (do 18,
  skills/0008); start 37 on 106 Zeal, 248 Fury (do 13, skills/0009) and 328 BloodLordFrenzy (do 109); do 73 on 112
  Blessed Hammer (`srvmissilea` 92 `blessedhammer`); do 79 on 116 Conversion (start 32, the barbarian batch;
  `auratargetstate` 53 `conversion`); do 80 on 121 Fist of the Heavens (`srvmissilea` 233 `fistoftheheavensdelay`,
  `srvoverlay` 158). (`rows.txt`, tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc)

### 2. Emulation: the `pal` families

The method is skills/0010's: each case calls the function with `ECX` = the game, `EDX` = the caster and the stack
`(id, lvl)`, and dumps the stack, the caster's and the target's seeds, the caster's `+0xC4`, the second argument's slot
and, for start 29, 31, 35, 37 and do 67, the used skill's node words `+0x18..+0x27`. Emulated, not observed (new for
this batch): `0x0056B740`; `sub_0057D690_QueuedHitFind` with `sub_0044BE50_UnitGetType` and `sub_00451F50_UnitGetId`;
`0x005D02B0` with `sub_0063EE90_HirelingType` and `0x006259B0`; `0x00644B10`; `SKILLS_NextPeriodicFrame`; the node
setters `0x00644560`, `0x006445A0`, `0x006445E0`, `0x00644620`; `CHARSTATS_GetRecord`, `MONSTATS_GetRecord`,
`0x004C9460`, `sub_00483360_MulDiv`; skills/0008's, skills/0009's and skills/0010's emulated helpers
(`UNIT_GetUsedSkill`, `UNIT_GetTargetUnit`, `SKILLS_GetTargetXY`, `sub_005D3CF0_SkillSrvMissileByCharge`,
`SKILLS_GetToHit`, `sub_0056E510_UnitMeleeReachPlus4` with `sub_00622870_UnitMeleeReach`, `STATS_GetUnitStat`,
`SKILLS_EvalCalc` on constant programs). Observed (new for this batch): `AURA_ApplyToTarget`, `0x0063C8F0`,
`0x006633B0`, `sub_00648690_PathSetSpeed`, `0x00649050`; the others as declared since skills/0009 and skills/0010
(`InMeleeRange`, `COMBAT_MeleeHitTest`, `sub_0056BD10_NearestUnitInRange`, `COMBAT_ApplyDamage`,
`COMBAT_DeliverQueued`, `0x0056E2F0`, `SKILLS_ForUnitsInRange`, `MissileCreate`, the inventory calls
`0x0063C9B0`/`0x0064F380` inside `0x00622870`).

**Nested boundaries** (ruling 1 of the `lane/p46m6` review, both branches). The aura boundary sits inside
`0x0056B740`: its return address into each batch function is compared at its absolute stack slot (do 65 `0x005CF148`
at `0x7FEFFF80`, do 66 `0x005CF4FA` at `0x7FEFFEB8`, do 81 `0x005D0A80` at `0x7FEFFEBC`, do 82 `0x005D0FD2` at
`0x7FEFFF74`), and `static.txt` lists every call of it (`0x005CF143`, `0x005CF4F5`, `0x005D0A7B`, `0x005D0FCD`: one in
each). Do 79's `0x0056E2F0` sits inside `0x005D02B0`, whose return `0x005D03CC` is compared at `0x7FEFFFD4`; its one
call in the image is do 79's (`0x005D03C7`). Start 37's `InvQuery` and `MeleeInv` boundaries sit two helpers deep:
start 37 calls `0x0056E510` once (`0x005DAF81`, `static.txt`), and `0x0056E510` (`push ecx; call 0x00622870; add eax,
4; ret`) calls `0x00622870` once (`0x0056E511`); these return addresses are not compared.

- [C] Three families, **4 950 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 2 615 matched boundary cases
  (21 function, boundary and return-address triples, each a `site` line) (`check.txt`; run:2026-10-20-cat-emu-pal):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `aura_pal` | do 65, 66, 81, 82 | 1 600 | no mana gate (172); `perdelay` floor 6 (552); do 65 five stats (44); do 65 `aurastate` 0 admitted (27); do 82 values of stats below 0 (112) | AuraApply @0x0056B75F (in `0x0056B740`, ×4); ForUnitsInRange @0x005CF229; returns 0, 1 |
  | `melee_pal` | start 29, 35, 36, 37, do 64, 79, 150 | 1 750 | start 36 without inventory 1 (134); reach without `+4` (23); queued hit matched on the caster alone (29); no `min` with the target's life (20); any alignment (7) | InMeleeRange @0x005CE7F1, @0x005CEA46; MeleeHitTest @0x005CFE9A; InvShield @0x005D0192; InvQuery @0x006228FD, MeleeInv @0x006228D2 (in `0x00622870`); NearestUnit @0x005DAFAE; ApplyDamage @0x005CE9C1; MonTest2F0 @0x005D0305 (in `0x005D02B0`); DeliverQueued @0x005D03FF; returns 0, 1 |
  | `move_pal` | start 31, do 67, 73, 80 | 1 600 | base 0x100 for a player (34); no floor at 50 (33); class 0 admitted (90); do 73 with a start point (153); do 80 setting bit 6 (71) | InMeleeRange @0x005CF728; Path9050 @0x005CF82B; PathSetSpeed @0x005CF873; AnimSeq @0x005CF956; MissileCreate @0x005D00ED, @0x005D071B; returns 0 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 40 of 40 pins): the hash offsets, the `CALC_Eval` jump
  table, the skills calc function count `0x007457AC`, `g_BitMask32` and the town tables, as in skills/0010. The
  count's scan matches every operand naming the address (a `PTR` or `moffs` store, an immediate, a read): 0 stores, 0
  immediates, 7 reads in `.text` (`ref_scan`, the condition of ruling 3 of the `lane/p46m5` review). Skills, CharStats,
  MonStats, MonStats2, the stat lists, the queued hits, rooms and units are scratch records written one field per field
  read.
- [C] **Inputs set in the memory spec** (ADR-0015, S1e review ruling 3): `g_pDataTables`, pointed at a scratch
  DataTables, is an input of the claims (no writer scan is cited for it); the security cookie is written as in 9a. No
  other image global is set. (run:2026-10-20-cat-emu-pal)
- [C] **The weak controls and their deciding classes** (ruling 4 of the `lane/p46m5` review). `aura_pal`'s `len5`
  (44) fails exactly on do 65's gated cases whose first five `aurastat`s are 0 or more, `as0` (27) on do 65's cases
  with `aurastat` 0 and a valid `auratargetstate` or none; `melee_pal`'s `reach0` (23) on start 37's monster casters
  without a target, `qhf_tgt` (29) on do 64's and do 79's cases where a node with the caster's words but another
  target precedes the match or stands alone, `hp_nomin` (20) on do 64's cases whose target life is below the queued
  damage, `align_any` (7) on do 79's found non-hireling monsters with a non-zero alignment; `move_pal`'s `base100` (34)
  on start 31's players with a CharStats record and `v67_floor` (33) on its cases with stat 67 below 50. Each family has
  a control failing 134 or more (`npf6` 552, `inv_any` 134, `xy73` 153). (run:2026-10-20-cat-emu-pal)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills, CharStats and
  MonStats columns `[C]` by layout; unit, path, node, queued-hit and stat-list offsets `[I]`, skills/0001,
  skills/0008, combat/0001), and nothing here says when the game runs these functions or on which seed state.
  (run:2026-10-20-cat-emu-pal)

### 3. The aura functions: do 65, 66, 81, 82

```c
// fn:sub_005CF010_PalAuraDo@0x005CF010 (do 65), trimmed
cost = SkillManaCost(id, lvl);  mana = STATS_GetUnitStat(u, 8, 0);
blk = {0};  blk.id = id;  blk.lvl = lvl;  blk.end = NextPeriodicFrame(game, u; rec, id, lvl) + 1 - game->frame;
if ((s16)rec->passivestate > 0) blk.w48 = passivestate;
if (!(u->type == 0 && mana < cost))
    for (i = 0; i < 6 && (s = (s16)rec->aurastat[i]) >= 0; i++) { blk.stat[i] = s; blk.val[i] = EvalCalc(aurastatcalc[i]); }
if ((s16)rec->aurastate > 0 && aurastate < nStates) { blk.state = aurastate; SkillCallOnSelf(game, u; AURA_ApplyToTarget, &blk); … }
if ((s16)rec->auratargetstate >= 0 && < nStates) { blk.state = auratargetstate;
    SKILLS_ForUnitsInRange(game, u; 0, 0, EvalCalc(aurarangecalc), aurafilter, AURA_ApplyToTarget, &blk, 1, file, 0x1F6); … }
return 1;
```

- [C] **The cost and the end** (all four): `0x00644B10(id, lvl)` = `((lvl − 1) · lvlmana + mana) << cl` with `lvlmana`
  and `mana` read `movsx` from `+0x18C`/`+0x18A`, `cl` the byte at `+0x188` (`shl eax, cl`: 5 bits), 32-bit products;
  the end is `n + 1 − frame` with `n = ((frame + p − 1) / p) · p + 1` (`idiv`, truncating; `frame` the game's
  `+0xA8`), `p` the `+0x128` calc, raised to 5 when it is 5 or less (`cmp ecx, 5; jg`). The gate: a caster of type 0
  whose `STATS_GetUnitStat(caster, 8, 0)` is below the cost (`jl`) gets no values; any other caster gets them.
  (run:2026-10-20-cat-emu-pal `aura_pal`, fn:sub_00644B10_SkillManaCost@0x00644B10,
  fn:SKILLS_NextPeriodicFrame@0x0056CD50)
- [C] (ADR-0021; ends at `AURA_ApplyToTarget` @0x0056B75F inside `0x0056B740`, helper return `0x005CF148`, or at
  `SKILLS_ForUnitsInRange` @0x005CF229) **Do 65** (tier A): the record (→ 0); the block at `ebp−0x64` as above, `+0x48`
  = `passivestate` (`movzx; test ax, ax; jle`: above 0 only, pinned 0x005CF0AD); the stat loop stops at the first
  `aurastat` below 0 (`jl`, 0x005CF0DF) and stores up to six; `+0x00` = `aurastate` when `(s16) > 0` (`jle`,
  0x005CF117) and below the States count, and `0x0056B740(ECX game, EDX caster; 0x005CEDC0, &block)` reaches
  `0x005CEDC0` with `ECX` = its context `{game, caster, 0, &block}` and `EDX` = the caster (both compared, the context
  and block by content); otherwise `+0x00` = `auratargetstate` when `(s16) ≥ 0` (`jl`, 0x005CF1D8) and below the
  count, and `ForUnitsInRange(ECX game, EDX caster; 0, 0, aurarangecalc, aurafilter, 0x005CEDC0, &block, 1,
  0x006E323C, 0x1F6)`; with neither, returns 1. (run:2026-10-20-cat-emu-pal `aura_pal`,
  fn:sub_005CF010_PalAuraDo@0x005CF010, fn:sub_0056B740_SkillCallOnSelf@0x0056B740)
- [C] (ADR-0021; ends at `AURA_ApplyToTarget` @0x0056B75F, helper return `0x005CF4FA`, `0x005D0A80` or `0x005D0FD2`)
  **Do 66** (tier A), **do 81**, **do 82**: the record and `aurastate` in `[0, States count)` (`movzx; test ax, ax;
  jl`: 0 admitted), else 0; the block (`ebp−0xBC`, `ebp−0xB8`, `ebp−0x70`) with `+0x00` = `aurastate`, `+0x04` id,
  `+0x08` lvl, `+0x0C` the end, and for `i` = 0..4 `+0x10 + 4i` = `passivestat(i+1)` (`movsx`) and, under the gate,
  `+0x28 + 4i` = `passivecalc(i+1)`; do 82 leaves the value 0 for a stat below 0 (`jl`, 0x005D0F7C) and goes on; do 81
  stores `0x005D0770` at `+0x4C`; then `0x0056B740` as do 65. (run:2026-10-20-cat-emu-pal `aura_pal`,
  fn:sub_005CF3A0_AuraHitDo@0x005CF3A0, fn:sub_005D0920_SkillDo81HolyFreeze@0x005D0920,
  fn:sub_005D0E90_SkillDo82Redemption@0x005D0E90)
- [I] By the layouts, the self block's state is `aurastate`, its stats `aurastat1..6` for do 65 and `passivestat1..5`
  for the others; `AURA_ApplyToTarget` (stats/0002 § 4) applies the state timed to `+0x0C`, writes the stats onto the
  list, and removes the state named at `+0x48` (do 65: `passivestate`, so Resist Fire, Resist Cold and Resist
  Lightning's caster loses its `passive_resist…` list while the aura runs) and passes `+0x4C` to `STATE_ApplyTimed`
  as its callback (do 81's `0x005D0770`; `0x005CEC50` for the caster itself when it is 0). So a player paladin whose mana is below Prayer's cost (`mana` 16, `lvlmana` 3,
  `manashift` 4) gets the `prayer` state with no stat values. The play consequences are not run here.
  (tbl:Skills.txt:passivestate, tbl:Skills.txt:mana, fn:AURA_ApplyToTarget@0x005CEDC0)
- [I] After do 65's self call: with the value of `ApplyToTarget` (the list, block `+0x44`), stat 8 above the cost and
  `passivestate` 0 or less, `passivestat1..5`/`passivecalc1..5` (non-zero values, stats in `(0, ItemStatCost count)`)
  by `STATLIST_SetStat` onto that list; then the `auratargetstate` pass as above; then for a player with a cost above
  0, `STATE_Set(caster, 85, 1)` and `0x0056C110(caster, cost)` when the block's `+0x40` count is above 0, else
  `STATE_Set(caster, 85, 0)`; returns 1. (0x005CF148–0x005CF275)
- [I] After do 66's and 81's self call: the caster's room is a town room → 1; then a second 0x50-byte block
  (`auratargetstate`, and when it is in range `aurastat1..6` with `aurastatcalc1..6` under a mana-only gate: stat 8
  below the cost gives 0 whatever the caster's type; `+0x48` = 1 when a value is non-zero) and a 0x70-byte packet from
  **one** `SKILLS_RollElemDamage(caster, id, lvl)` per run (the caster's seed), with `ResultFlags |= 0xD` (or the Skills
  `+0x134` word), `HitFlags | 0x20`, `+0x130`, pointed to by the block's `+0x4C` when the roll gives non-zero; then
  `SKILLS_ForUnitsInRange(…, aurarangecalc, aurafilter, callback, &block2, 0, file, line)` and the state-85 tail of
  do 65. Do 82's target pass has no such block: `ForUnitsInRange(…, 0x005D0D70, &{id, lvl, count}, 1, file, 0x753)`, then
  the same tail. The callbacks: `0x005CF2A0` (do 66) applies the second block's first 0x40 bytes with
  `AURA_ApplyToTarget` when its `+0x48` is set and copies the packet to each unit for `COMBAT_ApplyDamage(…, 1, &copy)`
  and `COMBAT_GetHit`; `0x005D07C0` (do 81) returns 0 for a monster whose MonStats `+0x168 + difficulty` byte is 0 or
  more (signed), does the same, then steps **the unit's** seed inline (`× 0x6AC690C5`, carry) and sets state 107 when
  the new low word `% 100` is below 20, else clears it; `0x005D0D70` (do 82) takes a unit `0x006456D0` accepts,
  `RNG_Range(caster + 0x20, 100) < calc1`, raises stat 6 by `calc2 << 8` (capped at `UnitGetMaxHp`) and stat 8 by
  `calc3 << 8` (capped at `UNIT_GetMaxMana`), sets state 99, clears `+0xC4` bits 1–2 and counts.
  (0x005CF4FA–0x005CF69F, 0x005CF2A0–0x005CF397, 0x005D07C0–0x005D091F, 0x005D0D70–0x005D0E8F, 0x005D0FD2–0x005D1060)

### 4. The melee functions: start 29, 35, 36, 37, do 64, 79, 150

- [C] (ADR-0021; ends at `InMeleeRange` @0x005CE7F1) **Start 29** (`0x005CE790`): the record, the used skill and
  the target, each 0 → 0, then `InMeleeRange(caster, target, 0)`. After, `[I]`: a zeroed 0x70-byte packet,
  `MeleeHitTest(target, SKILLS_GetToHit, 0)`, on a hit `COMBAT_RollPhysical(…, calc1, …, SrcDam)` into `+0x08`, the
  `EType`/`calc4` conversion, `SKILLS_RollElemDamage`, `ResultFlags`/`HitFlags`; `COMBAT_ResolveAndQueue(…, 0x80)`;
  returns 1. (run:2026-10-20-cat-emu-pal `melee_pal`, fn:sub_005CE790_SkillSt29Sacrifice@0x005CE790)
- [C] (ADR-0021; ends at `InMeleeRange` @0x005CEA46) **Do 150** (`0x005CE9F0`): the record and the target (0 → 0),
  then `InMeleeRange(caster, target, 0)`. After, `[I]`: a player's `0x0063C8F0(inventory, &item)` and that item's
  record bytes `+0xFE`/`+0xFF` as the damage base, plus `SKILLS_GetPhysMin/Max` of the skill and level of a state-101
  list (`holyshield`) when the caster carries one; `COMBAT_RollPhysical(…, calc1, 0x80)`, `calc2` into `+0x44`, the
  elemental roll, `MeleeHitTest(target, 0, 0)`; a monster takes `MonAttackStats(ECX caster, EDX 5)` and `calc2`
  instead; `ResolveAndQueue(…, 0x80)` with `+0x60` = 0x65, `DeliverQueued`; returns 1. (fn:sub_005CE9F0_SkillDo150Smite@0x005CE9F0)
- [C] (ADR-0021; ends at `COMBAT_MeleeHitTest` @0x005CFE9A) **Start 35** (`0x005CFE10`): the record, the used skill
  and the target (0 → 0), a zeroed 0x70-byte packet at `ebp−0x80` (compared), `MeleeHitTest(game, caster; target,
  SKILLS_GetToHit(caster, id, lvl), 0)`; no `InMeleeRange` call precedes it. After, `[I]`: on a hit
  `COMBAT_RollPhysical(SrcDam)`, `0x005CFD20` (stats 21/22 or 23/24 by `0x0063D340`, an inline LCG step on the
  caster's seed), `calc1`, `calc2`, `calc3` each raised by `MulDiv(calc, stat 329 / 331 / 330, 100)` and taken as a
  percent of that roll into the fire, cold and lightning words, `SKILLS_GetElemLen`, the used skill's `+0x18` cycled
  `(+1) % 3` with flags `0x20`/`0x30`/`0x40`; `ResolveAndQueue(…, 0x80)`; returns 1.
  (fn:sub_005CFE10_SkillSt35Vengeance@0x005CFE10, fn:sub_005CFD20_VengeanceWeaponRoll@0x005CFD20)
- [C] (ADR-0021; ends at `0x0063C8F0` @0x005D0192) **Start 36** (tier A): `+0x60` = 0 returns 0; else
  `0x0063C8F0(inventory, 0)`; it reads no skill record. After, `[I]`: returns that value as 0 or 1.
  (run:2026-10-20-cat-emu-pal `melee_pal`, fn:sub_005D0180_SkillSt36NeedShield@0x005D0180)
- [C] (ADR-0021; ends at `InvQuery` @0x006228FD or `MeleeInv` @0x006228D2 inside `0x00622870`, or at
  `NearestUnitInRange` @0x005DAFAE) **Start 37** (`0x005DAF40`): the record and the used skill (0 → 0); `r =
  0x0056E510(caster)` (skills/0009 § 3's helper: a player ends at its inventory query, a monster takes the MonStats2
  byte `+0x0E`, `+ 4`); with a target,
  the node's `+0x18` = `calc1`, `+0x1C` = the target's type, `+0x20` = its guid, and returns 1 (compared); without one,
  `NearestUnitInRange(ECX game, EDX caster; 0, 0, r, 0x20003, −1, 0)`. After, `[I]`: a found unit fills the node the
  same way; none sets `+0x18` = 0 and returns 0. (run:2026-10-20-cat-emu-pal `melee_pal`,
  fn:sub_005DAF40_SkillSt37Zeal@0x005DAF40, fn:sub_00644560_UnitSkillSet18@0x00644560)
- [C] **`sub_0057D690_QueuedHitFind(ECX caster, EDX target)`**: walks the caster's `+0xAC` chain (next `+0x84`) for the
  first node whose `+0x04`, `+0x08`, `+0x0C`, `+0x10` are the caster's type and guid and the target's type and guid
  (`UnitGetType`, `UnitGetId`), and returns that node `+ 0x14`, else 0 (also for a null unit). (run:2026-10-20-cat-emu-pal
  `melee_pal`, fn:sub_0057D690_QueuedHitFind@0x0057D690)
- [C] (ADR-0021; ends at `COMBAT_ApplyDamage` @0x005CE9C1) **Do 64** (`0x005CE8E0`): the record and the target (0 →
  0); `q = QueuedHitFind(caster, target)`, none → 1; a zeroed 0x70-byte packet (compared by content) with `+0x00` =
  0x1000, `v` = `q+0x08` lowered to `STATS_GetUnitStat(target, 6, 0)` when that is smaller (signed `jge`, pinned
  0x005CE973), and `+0x08` = `+0x4C` = `MulDiv(v, calc2, 100)`; `ApplyDamage(ECX game, EDX caster; caster, 0,
  &packet)`. After, `[I]`: `COMBAT_GetHit(game, caster; caster, &packet)`, `COMBAT_DeliverQueued(game, caster; target,
  0)`; returns 1. (run:2026-10-20-cat-emu-pal `melee_pal`, fn:sub_005CE8E0_SkillDo64SacrificeSelfHit@0x005CE8E0,
  fn:sub_00483360_MulDiv@0x00483360)
- [I] So, by the layouts, Sacrifice's self-hit is `calc2` percent of the queued hit's `+0x08` word (the physical damage
  in 1/256, `re/types/combat.h`), capped at the target's current life, applied to the caster with the `0x1000` flag. Its
  packet has no `+0x04` result word, unlike skills/0010's `0x005C2FF0` (§ 6). (re/types/combat.h)
- [C] (ADR-0021; ends at `0x0056E2F0` @0x005D0305 inside `0x005D02B0`, helper return `0x005D03CC` compared, or at
  `COMBAT_DeliverQueued` @0x005D03FF) **Do 79** (`0x005D0350`): the record (→ 0), bit 6 of `+0xC4`, the target (0 →
  0, bit 6 kept); with `QueuedHitFind(caster, target)` non-zero, `0x005D02B0(EAX id, EBX target; caster, lvl, 1)`: the
  record, `HirelingType(target)` = 0 (classes 271, 338, 359, 560, 561 refused), type 1, `0x006259B0(target)` = 0 (the
  function of skills/0008 § 4), then `0x0056E2F0(ECX target, EDX 0xB)`; every other case (no queued hit, a refusal)
  ends at `DeliverQueued(game, caster; target, 0)`. (run:2026-10-20-cat-emu-pal `melee_pal`,
  fn:sub_005D0350_SkillDo79Conversion@0x005D0350, fn:sub_005D02B0_ConversionTest@0x005D02B0)
- [I] After do 79's test: `0x0056E2F0`'s result, then `RNG_Range(caster + 0x20, 100) < calc1` (`0x005D0326`; the
  caster's seed); a 1 with `auratargetstate` in range makes a stat list (`STATLIST_Alloc`, `0x802`) of that state with
  end `max(frame + auralencalc, frame + 1)` and remove callback `0x005D01A0` (or extends the existing one), links it,
  sets the state, queues event 12 at the end, `0x0056E580(target)`, `MonAlignSet(target, 2; 1)`, `0x005B1900`,
  clears the caster's path target, frees the target's flag-8 lists, and when the target's level (stat 12) is above
  the caster's, makes a state-109 list holding the old level and life and scales stats 12, 6 and 7 to the caster's
  level; returns 1. (0x005D03CC–0x005D0661)

### 5. Charge and the missiles: start 31, do 67, 73, 80

- [C] (ADR-0021; ends at `InMeleeRange` @0x005CF728, `0x00649050` @0x005CF82B or `PathSetSpeed` @0x005CF873) **Start
  31** (`0x005CF6B0`): the record, the used skill and the caster's path `+0x2C` (each 0 → 0); with a target,
  `InMeleeRange(caster, target, 0)`; without one, `Set18(node, 6)`, `Set1C(node, 0)`, `Set24(node, 7)` (the node's
  words compared), then `base`: a player's `CHARSTATS_GetRecord(class)` byte `+0x41` `<< 8` (0x100 without a record), a
  monster's `MONSTATS_GetRecord(class)` `+0x34` (`movsx`) `<< 8` and then `0x00649050(path)`, or 0x100 without a
  record; `v` = `STATS_GetUnitStat(caster, 67, 0)` raised to 50 when it is 50 or less (`jg`, 0x005CF842);
  `PathSetSpeed(path, MulDiv(base, v + Skills+0x148, 100))` (`0x004C9460`). (run:2026-10-20-cat-emu-pal `move_pal`,
  fn:sub_005CF6B0_SkillSt31Charge@0x005CF6B0, fn:sub_004C9460_SkillGetParam1@0x004C9460)
- [I] By the layouts, `+0x41` is CharStats `RunVelocity`, MonStats `+0x34` is `Run`, stat 67 `velocitypercent` and
  `+0x148` `Param1` (150 for Charge), so a player charges at `run × (max(velocitypercent, 50) + 150) / 100`. A monster of
  class 211 also gets `Set24(node, 0xF)` before the path call (`cmp edi, 0xD3`), not reached (the scratch MonStats has 4
  rows). After start 31's boundaries, `[I]`: a monster's `0x00648E70(path, 0x14)`; `sub_00649970_PathPlan(path, caster,
  0)`, `Set0C(node, 0x1001)`, `STATE_Set(caster, 18, 1)`; returns 1. With a target in melee range a player ends in
  `0x0056E230(game, caster; target)` and a monster in mode changes and `sub_005A7E60_MonCmdInit`/`MonSetMode`; out of
  range, a target without state 54 goes into the node (`+0x18` its type, `+0x1C` its guid) and the same speed code
  runs. (tbl:CharStats.txt:RunVelocity, tbl:MonStats.txt:Run, tbl:Skills.txt:Param1, 0x005CF72C–0x005CF89C)
- [C] (ADR-0021; ends at `0x006633B0` @0x005CF956) **Do 67** (`0x005CF900`): the record and the used skill (0 → 0),
  then `0x006633B0(caster)`. After, `[I]`: `0x006633F0`, `0x005CF8C0`, the node's `+0x18`/`+0x1C` (the charge target,
  `GameFindUnit` unless the type is 6) and `+0x0C` flags. With bit 0 set: the target in melee range ends the charge
  (`Set0C(node, 0)`, `0x00553DC0`, `0x00571B70`, returns 1); else with bit 1 a retarget by the nearest unit; else,
  when the frame less the path's `+0x44 >> 8` reaches `0x005CF8C0`'s value, `0x00553DC0` and `Set0C(node, 1)`, then
  the unit's events cancelled and requeued and `+0xC4` bit 6 cleared (returns 1). With bit 0 clear: the node reset,
  bit 6 set, the nearest unit when none was stored (none: events requeued, returns 0), and a live target in melee range
  takes `COMBAT_MeleeHitTest(target, SKILLS_GetToHit, 0) | 8` (a monster caster the word 9 without a test), `calc1`
  into the packet's `+0x0C`, the elemental roll, `MonAttackStats` for a monster, `ResolveAndQueue(SrcDam)`,
  `DeliverQueued` and `sub_00621E40_UnitSetOverlayStat(target, 147, 0)`; returns 1. (0x005CF956–0x005CFD19)
- [C] (ADR-0021; ends at `MissileCreate` @0x005D00ED) **Do 73** (`0x005D0040`): the record (→ 0); `m =
  SrvMissileByCharge(ECX caster, EDX id)` (skills/0008 § 6), `m ≤ 0` → 0 (`jle`, 0x005D008A: class 0 refused);
  `SKILLS_GetTargetXY` (none → 0); bit 6; `MissileCreate(ECX game, EDX &block)` with the 0x5C-byte block `{+0x00 0x20,
  +0x04 caster, +0x08 caster, +0x10 m, +0x1C x, +0x20 y, +0x2C id, +0x30 lvl}` (compared by content; `+0x14`/`+0x18`
  stay 0). (run:2026-10-20-cat-emu-pal `move_pal`, fn:sub_005D0040_SkillDo73BlessedHammer@0x005D0040)
- [C] (ADR-0021; ends at `MissileCreate` @0x005D071B) **Do 80** (`0x005D0670`): the record and `m` as do 73 (→ 0);
  the target (none → 0); no bit 6; the block `{+0x00 1, +0x04 caster, +0x10 m, +0x14 UnitGetSubX(target), +0x18
  UnitGetSubY(target), +0x2C id, +0x30 lvl}`. (run:2026-10-20-cat-emu-pal `move_pal`,
  fn:sub_005D0670_SkillDo80FistHeavens@0x005D0670)
- [I] After the creations: do 73 `sub_00648CF0_PathSetType(path, 0xE)`, `PathPlan(path, missile, 0)`, and when
  `0x006461D0(caster, id)` gives a value `v`, the missile's base stats 52 and 53 set to `MulDiv(base, v + 100, 100)`;
  do 80 `MISSDATA_SetSeedLow(missile, target type)`, `MISSDATA_SetParam2C(missile, target guid)` and
  `sub_00621E40_UnitSetOverlayStat(target, srvoverlay, 0)` for a `srvoverlay` in range; each returns 1 (0 when
  `MissileCreate` gives none). What `MissileCreate` makes of the flags and the empty start point is not read.
  (0x005D00ED–0x005D0171, 0x005D071B–0x005D0762)

### 6. Bearing on skills/0010's class-3 self-hit

- [I] `0x005C2FF0` is called only by do 31 and do 58 (skills/0010 `static.txt`, `0x005C4B3A`, `0x005C5751`); no
  function of this batch calls it, and none tests the caster's class. Sacrifice's own self-hit (do 64, § 4) builds a
  packet of the same shape (`+0x00 0x1000`, the amount at `+0x08` and `+0x4C`) without `0x005C2FF0`'s `+0x04 |= 4`,
  and passes it to `COMBAT_ApplyDamage(game, caster; caster, 0, …)` then `COMBAT_GetHit` exactly as `0x005C2FF0` does.
  That likeness is a reading only; it does not say why the necromancer's functions hit a class-3 caster.
  (fn:sub_005CE8E0_SkillDo64SacrificeSelfHit@0x005CE8E0, fn:sub_005C2FF0_SkillClass3SelfHit@0x005C2FF0)

## Corrections to earlier findings

- skills/0003 § 5 (tier A), carried there as a dated note: start 36, do 65 and do 66 are now `[C]` up to their
  boundaries (ADR-0021). Start 36 reads no skill record and returns 0 without an inventory; do 65's `aurastat` values
  are gated by the mana test as its `passivestat` writes are (a player below the cost gets the state with no values),
  and its `aurastate` must be above 0 while `auratargetstate` 0 is admitted; do 66's self block carries
  `passivestat1..5`, not `aurastat`, and refuses an `aurastate` out of range. (fn:sub_005D0180_SkillSt36NeedShield@0x005D0180,
  fn:sub_005CF010_PalAuraDo@0x005CF010, fn:sub_005CF3A0_AuraHitDo@0x005CF3A0)
- stats/0002 § 4, carried there as a dated note: the mana gate covers the `aurastat` evaluation of do 65, not only the
  `passivestat` writes; § 7's "once per hit" for Sanctuary's draw is one `SKILLS_RollElemDamage` per run of do 66 (its
  packet copied to each unit hit), `[I]` from the reading. (fn:sub_005CF2A0_AuraHitUnitCb@0x005CF2A0, 0x005CF5D5)

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `aurastate`, `auratargetstate`, `aurastat1..6`, `aurastatcalc1..6`,
`passivestate`, `passivestat1..5`, `passivecalc1..5`, `perdelay`, `mana`, `lvlmana`, `manashift`, `aurafilter`,
`aurarangecalc`, `calc1`, `calc2`, `Param1`, `srvmissilea` (through `SrvMissileByCharge`), `ToHit`, `LevToHit`,
`ToHitCalc`; `tbl:CharStats.txt:RunVelocity`; `tbl:MonStats.txt:Run`; unit `+0x00`, `+0x04`, `+0x0C`, `+0x2C` path,
`+0x5C` stat list, `+0x60` inventory, `+0xA8` skills (the used node `+0x18`, `+0x1C`, `+0x20`, `+0x24`), `+0xAC` queued
hits, `+0xC4` bit 6; game `+0xA8`.

## Dead ends

- None. The first emulation of each family matched; the only fix was in the tool (a model helper named like one of
  `sor`'s, caught by the reproduction of the earlier batches before any output was kept; the case files did not change).

## Open questions

- [L] What `0x0063C8F0` returns (start 36's shield test, do 150's item), what `0x006633B0`'s animation data is (do 67),
  and what `0x00649050` does to a monster's path (start 31) (§§ 4, 5).
- [L] What `MissileCreate` makes of do 73's block with no start point and do 80's with no target point (§ 5).
- [L] Whether Holy Freeze's 20 % state 107 (`0x005D07C0`) is the hard freeze, and why its callback skips monsters whose
  `coldeffect` is 0 or more (§ 3), a harness or later-batch check.
- [L] Everything after each boundary (§§ 3–5), for a later batch or the harness.
