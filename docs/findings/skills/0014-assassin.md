# 0014 — Catalogue batch `ass`: the assassin start functions 22–28, do functions 33–52 and 54, and the progressive entries 36–41 and 143

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 22–28 (`srvstfunc`, `g_SkillStartFuncs`), do function 33–52 and
> 54 (`srvdofunc`, `g_SkillDoFuncs`) and progressive entry 36–41 and 143 (`srvprgfunc`, the same table, run by
> `COMBAT_PrgFinisher`) of the assassin batch do: which Skills and unit fields it reads, which hits, states, summons and
> missiles it makes, which draws it makes on which seed, what it returns, and which of that the emulator can confirm?
> **Date:** 2026-10-21   **Plan:** 0046 (Phase 1, batch `ass`)   **Status:** for review (`lane/p46m11`)

Static reading of the pinned `Game.exe` with objdump and the lane's Ghidra copy `workspace/ghidra-p46m11`, then
emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged) and the `ass` families of
`tools/skills_catalogue_emu.py` (§ 2; run:2026-10-21-cat-emu-ass in [experiments](experiments.md)). Skills columns are
named as in [Skills](../../tables/Skills.md). The machinery that calls a start or do function is
[skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart); the progressive entries are called
by `COMBAT_PrgFinisher` ([skills/0001 § 12](0001-dispatch.md#12-progressive-charges)); the five tier-A entries of this
batch (start 23, do 35, entries 38, 39, 143) were read by plan 0045 in [skills/0003 §§ 1, 5](0003-handlers.md#1-progressive-entries-srvprgfunc-and-the-finishers-tail),
and all five are emulated here. Stock values come from `workspace/logs/skills-cat-ass/rows.txt` (`excel_bin.py dump`
of the 26 Skills rows that name one of the batch's entries in `srvstfunc`, `srvdofunc`, `srvprgfunc1..3` or
`ItemEffect`, by `rows.sh` beside it; the selection checked complete against all 357 rows by the `CHECK` lines of `rows.txt`).

**Tag convention for this finding** (as skills/0013). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a
function entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site
(the return address at ESP), with a site control that fails every matched boundary case, and where the boundary sits
inside a helper the batch function called, the helper's return address into the batch function is compared at its
absolute stack slot (§ 2 lists each compared slot); (c) the model gives and the checker compares every argument the
claim uses (registers the callee reads before it writes them, stack words, and for a pointer the bytes it points to),
every byte written before the call that the claim uses (the caster's `+0xC4`, the used node's `+0x18`, frame,
argument-slot and local-seed words), and the state of **the caster's and the target's seeds** at the boundary (both,
in every case). Each such claim names the boundary it ends at; **the callee and all code after it are not covered**
and keep `[I]` (from the reading), marked "after, `[I]`" in place, and what a callee makes of a compared argument is
stated after the boundary (reverser review-fixes 13). No claim rests on a callee-saved register that is not a boundary
argument. A plain `[C]` rests on cases that return; a plain `[I]` is a code reading the emulator does not reach.
(run:2026-10-21-cat-emu-ass)

## Answer (summary)

- [C] **The batch.** 29 entries: start 22 `0x005D30F0`, 23 `0x005D32F0`, 24 `0x005D5970`, 25 `0x005D6330`, 26
  `0x005D69D0`, 27 `0x005D7090`, 28 `0x005D7A00`; do 33 `0x005D3140`, 34 `0x005D3490`, 35 `0x005D35D0`, 42
  `0x005D5A30`, 43 `0x005D5D70`, 44 `0x005D6020`, 45 `0x005D6170`, 46 `0x005D6340`, 47 `0x005D6630`, 48 `0x005D68A0`,
  49 `0x005D6E70`, 50 `0x005D7180`, 51 `0x005D76E0`, 52 `0x005D7850`, 54 `0x005D7E10`; progressive entries 36
  `0x005D4DB0`, 37 `0x005D4E70`, 38 `0x005D3E80`, 39 `0x005D3F90`, 40 `0x005D5010`, 41 `0x005D5080`, 143 `0x005D4F40`.
  Every one is `(ECX game, EDX unit; skill id, level)` with `ret 8`. All 29 are emulated.
  (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [C] **Draws before the boundaries.** Entries 37, 39, 41 and 143 step **the caster's seed** once inline at entry,
  **before** their record test (a refused case returns with the seed one step on), and keep the stepped low word: 37
  and 143 hand it to their ring, which seeds a stack seed with it (`RNG_SeedInit`, high word `0x29A`) and steps that
  once before its first creation; 39 seeds a stack seed with it and draws two `RNG_Range(local, 2r)` per try until its
  first creation; 41 seeds a stack seed with it and steps it twice before its first creation. No other function of the
  batch steps the caster's or the target's seed before its boundary or return (8 700 cases, both seeds and the stack
  seeds compared in each; the cases' calcs are constant programs that call no calc function, as in skills/0008–0013,
  so a calc function's own draws are not covered). (run:2026-10-21-cat-emu-ass,
  fn:sub_005D4E70_SkillPrgDo37Ring@0x005D4E70, fn:sub_005D3F90_SkillPrgDo39Scatter@0x005D3F90,
  fn:sub_005D5080_SkillPrgDo41Scatter@0x005D5080, fn:sub_005D4F40_SkillPrgDo143Ring@0x005D4F40)
- [C] (ADR-0021; § 3) **The start functions.** Start 22 returns 1 for a target out of town whose type is 0 or 1 (and
  the caster out of town), else 0; start 25 returns whether there is a target; start 23 and 24 end at
  `InMeleeRange(caster, target, 0)` (24 after the used node, writing 0 at its `+0x18` and returning 0 without a
  target); start 26 ends at `StatListSetEnd(state 12's list, frame + 7)` or, after a `startmana` test against stat 8,
  at `STATLIST_Alloc(game+0x1C, 2, frame + 21, type, guid)`; start 27 at `0x0056E520(ECX caster, EDX Param4)`; start 28
  at `STATE_GroupClear(ECX caster, EDX aurastate; 0)` after the unit skill, the missile and `auralencalc`.
  (run:2026-10-21-cat-emu-ass)
- [C] (ADR-0021; § 4) **The hits and the finishing moves.** Do 34 ends at `MeleeHitTest(target, GetToHit, 0)` after
  `aurastate` and `aurastat1` range tests; do 35 ends at `InvGetBodyLocItem(inventory, 4)` or, with no inventory, sets
  or clears bit 6 by bit 8 of the caster's `+0x38` and runs do 34; do 33 ends at `SkillRollPhys` inside `0x0057E240`
  after start 22's test; do 46 at `MeleeHitTest(target, GetToHit + stat 325, 0)` inside `0x005D6200` (the parity told by
  the helper's return address); do 52 at that hit test for bit 8 set, else at `UnitTeleport(game, caster; 0, x, y, 0, 0)`
  or `0x006229F0(caster, x, y, 0x804)` by the caster's level's `Teleport` byte (`+0x04`: 0 → 0, 2 → the test); do 42,
  50 and do 46 (on a bad id) end at `COMBAT_PrgFinisher(game, caster; QueuedHitFind(caster, target))`, do 42 with **no
  null test** of the hit, do 50 after copying the 0x70-byte packet to its frame. (run:2026-10-21-cat-emu-ass)
- [C] (ADR-0021; § 5) **The progressive entries.** 36 ends at the first `MissileCreate` of
  `SkillNovaAtUnit(game, caster; target, m, id, lvl, MissileSpeedAtLevel(m, lvl) + calc1)` (the nova centred on **the
  target**); 37 and 143 at their ring's first `MissileCreate` (flags 3, the target point, the first direction
  `(30, 0)`, the callback `0x005D40F0` / `0x005D4680` with the stepped local low word), **with no test of the step
  count**; 38 at `DeliverQueued(game, caster; target, 0)` or, without a target, `SkillRollPhys` with the range stored in
  its first argument slot; 39 at its first in-circle point with a room, or returns 1 after `r²` tries; 40 at
  `MissileCreateAt(game, caster; id, lvl, m, x, y)` (no record test of its own); 41 at its first `MissileCreate`
  (flags 3, offsets `(low₁ mod 40 − 20, low₂ mod 40 − 20)`, `(0, 0)` made `(20, 0)`), or returns 1 for a negative
  count. (run:2026-10-21-cat-emu-ass)
- [C] (ADR-0021; § 6) **Traps, states, areas.** Do 44 and 45 end at `SpawnOwnedMonster` inside `0x005D5E10` with the
  nine-word block `{1, unit, class, 0, mode, x, y, pettype, petmax}`, where **a bad `pettype` becomes 0 instead of
  refusing**, a monster caster is replaced by its owner (`MonsterOwner`, none → 0), do 44's point is the caster's
  position, and the room and town tests use the unit it ends with; do 49 ends at `SpawnOwnedMonster` with `{0, caster, class, 0,
  mode, 0, 0, pettype (0 at or past the count, unsigned), petmax, mode}` after setting bit 6 first; do 47 at
  `STATE_ApplyTimed` with `{caster, caster, id, lvl, auralencalc, passivestat1, passivecalc1, aurastate,
  STATE_DefaultRemoveCB}` when the caster lacks the state; do 48 clears bit 6 and ends at its `MissileCreate` (flags
  `0x20`) while the unit skill's `+0x18` is before the frame, else at `0x00553C70(game, caster; 1)` under state 12, else
  returns 0; do 43 at `MissScatterAtTarget`; do 51 and do 54's `0x005D7CE0` at `SkillRollPhys` with the range stored in
  an argument slot (do 54 returns 1 in town without it). (run:2026-10-21-cat-emu-ass)
- [I] After, from the reading: the finisher and the deliveries; do 33's knock roll (**an inline step of the caster's
  seed**, `low % 100 <` a calc chosen by the target's kind) and its kill flag; do 42's `RNG_Range(caster, 100)` against
  a calc by the target's kind at the last charge; the hits' `SkillRollPhys`/`SKILLS_RollElemDamage` draws; the rings'
  remaining creations (an endless loop for a step count of 0, § 5); the summons' set-up and do 44's teleport of the
  trap to the caster; the area callbacks. Every boundary is listed per function.
- [I] **The data joins.** `ItemEffect` 36 (rows 44 Frost Nova and 48 Nova) makes an item cast of those skills run
  entry 36, a nova of the row's `srvmissilea` (119 `frostnova`, 90 `nova`) centred on the cast's target unit and
  nothing without one (skills/0001 § 10's effect flag, not re-read here). The five finishing-move calls of
  `COMBAT_PrgFinisher` are in do 42 (`0x005D5A8C`), **do 46** (`0x005D6399`, `0x005D63E1`, not start 25: start 25 is
  the 16-byte target test), do 50 (`0x005D71F2`) and do 52 (`0x005D79DF`). (`rows.txt`, `static.txt`)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005D30F0` | `sub_005D30F0_SkillSt22PsychicTest` | start 22; also called by do 33 | I |
| `0x005D32F0` | `sub_005D32F0_SkillSt23MeleeRange` | (P1.3 name) start 23 | I |
| `0x005D5970` | `sub_005D5970_SkillSt24DragonTalon` | start 24 | I |
| `0x005D6330` | `sub_005D6330_SkillSt25HasTarget` | start 25 | I |
| `0x005D69D0` | `sub_005D69D0_SkillSt26BladeFury` | (P1.3 name) start 26 | I |
| `0x005D7090` | `sub_005D7090_SkillSt27DragonTail` | start 27 | I |
| `0x005D7A00` | `sub_005D7A00_SkillSt28BladeShield` | start 28 | I |
| `0x005D3140` | `sub_005D3140_SkillDo33PsychicHammer` | do 33 | I |
| `0x005D3490` | `sub_005D3490_PrgChargeHitDo` | (P1.1 name) do 34 | I |
| `0x005D35D0` | `sub_005D35D0_PrgChargeHitDualDo` | (P1.1 name) do 35 | I |
| `0x005D4DB0` | `sub_005D4DB0_SkillPrgDo36NovaAtTarget` | (P1.3 name) entry 36; `ItemEffect` 36 | I |
| `0x005D4E70` | `sub_005D4E70_SkillPrgDo37Ring` | (P1.3 name) entry 37 | I |
| `0x005D3E80` | `sub_005D3E80_SkillPrgDo38AreaHit` | (P1.3 name) entry 38 | I |
| `0x005D3F90` | `sub_005D3F90_SkillPrgDo39Scatter` | (P1.3 name) entry 39 | I |
| `0x005D5010` | `sub_005D5010_SkillPrgDo40MissileAt` | (P1.3 name) entry 40 | I |
| `0x005D5080` | `sub_005D5080_SkillPrgDo41Scatter` | (P1.3 name) entry 41 | I |
| `0x005D4F40` | `sub_005D4F40_SkillPrgDo143Ring` | (P1.3 name) entry 143 | I |
| `0x005D5A30` | `sub_005D5A30_SkillDo42DragonTalon` | do 42 | I |
| `0x005D5D70` | `sub_005D5D70_SkillDo43ShockField` | do 43 | I |
| `0x005D6020` | `sub_005D6020_SkillDo44BladeSentinel` | do 44 | I |
| `0x005D6170` | `sub_005D6170_SkillDo45Sentry` | do 45 | I |
| `0x005D6340` | `sub_005D6340_SkillDo46DragonClaw` | do 46 | I |
| `0x005D6630` | `sub_005D6630_SkillDo47Cloak` | do 47 | I |
| `0x005D68A0` | `sub_005D68A0_SkillDo48BladeFury` | (P1.3 name) do 48 | I |
| `0x005D6E70` | `sub_005D6E70_SkillDo49Shadow` | do 49 | I |
| `0x005D7180` | `sub_005D7180_SkillDo50DragonTail` | do 50 | I |
| `0x005D76E0` | `sub_005D76E0_SkillDo51MindBlast` | do 51 | I |
| `0x005D7850` | `sub_005D7850_SkillDo52DragonFlight` | do 52 | I |
| `0x005D7E10` | `sub_005D7E10_SkillDo54BladeShield` | do 54 | I |
| `0x0057E240` | `sub_0057E240_SkillRollPhysElem` | `(ECX unit, EDX id; lvl, &packet)`, `ret 8`: `SkillRollPhys` then `SKILLS_RollElemDamage` | I |
| `0x005D3CB0` | `sub_005D3CB0_PrgAreaHitCb` | entry 38's `ForUnitsInRange` callback (skills/0003 § 1) | I |
| `0x005D5E10` | `sub_005D5E10_TrapSpawn` | `(ECX game, EDX unit; x, y, rec, id, lvl)`, `ret 0x14`: § 6 | I |
| `0x005D6200` | `sub_005D6200_DragonClawHit` | `(EBX id, ESI unit; game, target, lvl)`, `ret 0xC`: § 4 | I |
| `0x005D6520` | `sub_005D6520_CloakAreaCb` | do 47's `ForUnitsInRange` callback | I |
| `0x005D69B0` | `sub_005D69B0_BladeFuryRemoveCb` | start 26's list remove callback: `STATE_Set(unit, state, 0)`, bit 6 set | I |
| `0x005D7680` | `sub_005D7680_MindBlastAreaCb` | do 51's `ForUnitsInRange` callback (not read) | I |
| `0x005D7C40` | `sub_005D7C40_BladeShieldAreaCb` | `0x005D7CE0`'s `ForUnitsInRange` callback (not read) | I |
| `0x005D7CE0` | `sub_005D7CE0_BladeShieldArea` | `(ECX game, EDX unit; id, lvl)`, `ret 8`: § 6 | I |
| `0x006229F0` | `sub_006229F0_TeleportPointTest` | `(unit, x, y, mask)`, `ret 0x10`: do 52's test on a `Teleport` 2 level (not read) | I |

## Walkthrough

### 1. The table slots, the shared shape, the stock rows and the callers

- [C] `g_SkillStartFuncs[22..28]`, `g_SkillDoFuncs[33..52, 54]` and `g_SkillDoFuncs[143]` are the Functions table's
  addresses (29 entries compared, `table_entries=29`); `g_SkillDoFuncs[53]` is `0x005D7B60`, used by no stock row
  (skills/0001). (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [I] Start 24, 26, 27, 28, do 33, 38, 42, 43, 44, 45, 47, 50, 51, 52 and 54 test `0 ≤ id < DataTables+0xBA0` and a
  non-null record (`DataTables+0xB98 + 0x23C · id`) first and return 0 when it fails. Do 34 and entry 36 test the
  target first (36 also `lvl > 0`) and the record after; entries 37, 39, 41 and 143 step the caster's seed first and
  test the record after; do 49 sets bit 6 first; do 46 leaves the record test to `0x005D6200`, do 35 to do 34; do 48
  and entry 40 make no record test of their own (`SKILLS_GetUnitSkill` or `SKILLS_GetTargetXY` comes first, and
  `SrvMissileByCharge` gives −1 for a bad id); start 22, 23 and 25 never read the record. (0x005D3156–0x005D3175,
  0x005D6E88–0x005D6EAE, 0x005D68B0–0x005D68B4, 0x005D501A–0x005D5026, 0x005D6206–0x005D622E)
- [I] **Stock rows** (`rows.txt`): start 22 and do 33 on 253 Psychic Hammer; start 23 with do 34 on 254 Tiger Strike,
  265 Cobra Strike, 280 Royal Strike (entries 40/143/41, no `prgstack`) and with do 35 on 259 Fists of Fire
  (143/38/39, `prgstack`), 269 Claws of Thunder (−/36/37), 274 Blades of Ice (−/38/39); start 24 and do 42 on 255
  Dragon Talon; do 43 on 256 Shock Field; do 44 on 257 Blade Sentinel; do 45 on 261 Charged Bolt Sentry, 262 Wake of
  Fire Sentry, 271 Lightning Sentry, 272 Inferno Sentry, 276 Death Sentry; start 25 and do 46 on 260 Dragon Claw; do 47
  on 264 Cloak of Shadows; start 26 and do 48 on 266 Blade Fury (`startmana` 6); do 49 on 268 Shadow Warrior and 279
  Shadow Master; start 27 and do 50 on 270 Dragon Tail; do 51 on 273 Mind Blast; do 52 on 275 Dragon Flight (whose
  `srvstfunc` is 12, the sorceress's); start 28 and do 54 on 277 Blade Shield. `ItemEffect` 36 on 44 Frost Nova and 48
  Nova (`srvdofunc` 22; non-progressive, so entry 36's missile is `srvmissilea`, 119 and 90). Of the 357 rows no other
  names an entry of the batch. (`rows.txt`, tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc,
  tbl:Skills.txt:srvprgfunc1, tbl:Skills.txt:ItemEffect)
- [C] **The finisher's callers.** `COMBAT_PrgFinisher` (`0x005D5220`) has six direct calls in the image:
  `SKILL_AttackDo` (`0x0056F1CE`), do 42 (`0x005D5A8C`), do 46 (`0x005D6399`, `0x005D63E1`), do 50 (`0x005D71F2`) and
  do 52 (`0x005D79DF`) (`static.txt`, a scan of every `call` operand). Do 42's, do 46's and do 50's calls are reached
  as boundaries in the run with `QueuedHitFind(caster, target)`'s result as the one stack argument, `ECX` the game and
  `EDX` the caster, do 42's also with a null result (§ 4). (fn:COMBAT_PrgFinisher@0x005D5220, run:2026-10-21-cat-emu-ass)
- [I] Do 52's call (after its hit-test boundary) passes `QueuedHitFind`'s result with no null test, as do 42; do 46
  and do 50 call it only with a hit. The finisher returns at once for a null hit or one whose `+0x04` lacks bit 0
  (`0x005D5229`–`0x005D523B`). (0x005D79D1–0x005D79DF)

### 2. Emulation: the `ass` families

The method is skills/0013's: each case calls the function with `ECX` = the game, `EDX` = the caster and the stack
`(id, lvl)`, and dumps the stack, the caster's and the target's seeds, the caster's `+0xC4`, the second argument's
slot and, where a claim writes them, the used node's `+0x18` (start 24), the first argument's slot (entry 38) and
`0x005D7CE0`'s first argument's slot (do 54). Emulated, not observed: start 22's test (`0x005D30F0`, also inside do 33),
`0x0057E240`, `sub_005D3DA0_SkillPrgCalcByCharge`, `sub_00663270_MissileSpeedAtLevel`, `sub_0056D400_SkillNovaAtUnit`
up to its first `MissileCreate`, the rings `0x005D4150` and `0x005D4870` up to theirs, `0x005D5E10` with
`sub_0058F0D0_MonsterOwner` and `sub_00552F60_GameFindUnit`, `0x005D6200`, `0x005D7CE0`, `LEVELS_GetRecord` and
`sub_0061A1B0_RoomGetLevelId`, `STATS_GetUnitStat`, and the earlier batches' helpers (`UNIT_GetTargetUnit`,
`UNIT_GetUsedSkill`, `SKILLS_GetUnitSkill`, `SKILLS_GetTargetXY`, `SrvMissileByCharge`, `SKILLS_GetToHit`,
`QueuedHitFind`, `SkillSummonClass`, `UNIT_FindStatListByState`, `UNIT_HasState`, `UnitGetRoom`, `RoomIsTown`,
`RoomAtSubtile`, `UnitSkillGet18`/`Set18`). Observed (new for this batch): `COMBAT_PrgFinisher` (`0x005D5220`),
`sub_0063BDE0_InvGetBodyLocItem`, `sub_00554EA0_UnitTeleport`, `0x006229F0`; the others as declared since
skills/0008–0013 (`InMeleeRange`, `StatListSetEnd`, `StatListAlloc`, `AttackRate`, `GroupClear`, `RollPhys`,
`MeleeHitTest`, `DeliverQueued`, `MissileCreate`, `MissileCreateAt`, `ScatterAtTarget`, `SpawnOwned`, `ApplyTimed`,
`Sub553C70`).

**Register arguments read before written** (ruling 1 of the `lane/p46m8` review): `COMBAT_PrgFinisher` (`mov edi,
edx` at `0x005D522C`, `mov [ebp−0x18], ecx` at `0x005D522E`), `UnitTeleport` (`mov edi, edx` at `0x00554EA9`, `mov
[ebp−0x4], ecx` at `0x00554EAD`), `sub_0056E170_SkillRollPhys` (`mov [ebp−0x4], edx` at `0x0056E17B`, `mov edi, ecx`
at `0x0056E17E`; the `push ecx` at `0x0056E173` reserves the slot), `STATE_ApplyTimed` (`mov esi, ecx` at
`0x0056E978`), `0x00553C70` (`mov ebx, ecx` and `mov esi, edx` at `0x00553C7E`/`0x00553C80`), `MissileCreateAt`
(`mov esi, edx` at `0x0056EDE7`, `mov [ebp−0x4], ecx` at `0x0056EDEB`), `MissScatterAtTarget` (`mov esi, ecx` at
`0x005D5BF8`, `mov edi, edx` at `0x005D5C04`, `EDX` unwritten before); `InvGetBodyLocItem`, `InMeleeRange`,
`StatListSetEnd`, `StatListAlloc` and `0x006229F0` take stack arguments only; `GroupClear`, `AttackRate`, `MeleeHitTest`,
`DeliverQueued`, `SpawnOwnedMonster` and `MissileCreate` as in skills/0009–0013.

**Nested boundaries** (each compared at its absolute stack slot): do 33's return from `0x0057E240` (`0x005D31BF` at
`0x7FEFFF68`; one caller, `0x005D31BA`); do 35's from do 34 (`0x005D3648` at `0x7FEFFFE0`; one caller, `0x005D3643`),
with do 34's packet then at `0x7FEFFF64`; do 46's from `0x005D6200` (`0x005D6386` for bit 8 clear, `0x005D63CE` for it
set, at `0x7FEFFFDC`; two callers, `0x005D6381`, `0x005D63C9`); entry 36's from `SkillNovaAtUnit` (`0x005D4E58` at
`0x7FEFFFCC`; six callers in the image); entry 37's and 143's from their ring (`0x005D4F2E` / `0x005D4FFE` at
`0x7FEFFFB8`; one caller each), the ring's local seed at `0x7FEFFFAC`; do 44's and 45's from `0x005D5E10`
(`0x005D60AD` at `0x7FEFFFB0`, `0x005D61E3` at `0x7FEFFFD0`; two callers); do 54's from `0x005D7CE0` (`0x005D7E81` at
`0x7FEFFFE4`; one caller). The stack seeds of entries 39 and 41 are compared at `0x7FEFFFE4` and `0x7FEFFFE8`
(`static.txt` lists the call sites).

- [C] Four families, **8 700 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 3 020 matched boundary cases
  (37 function, boundary and return-address triples, each a `site` line) (`check.txt`; run:2026-10-21-cat-emu-ass):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `start_ass` | start 22–28 | 2 100 | no town test (41); start 25 inverted (300); node `+0x18` kept (54); mana `≤` (16); frame + 7 for + 21 (55); `EDX` 0 (41) | InMeleeRange @0x005D330B, @0x005D59DD; StatListAlloc @0x005D6A81; StatListSetEnd @0x005D6AED; AttackRate @0x005D70E6; GroupClear @0x005D7AA1; returns 0, 1 |
  | `hit_ass` | do 33, 34, 35, 42, 46, 50, 52 | 2 100 | `aurastat1` untested (64); parity inverted (350); no stat 325 (130); no town test (25); hit found by the caster alone (63) | RollPhys @0x0057E257 (in `0x0057E240`); MeleeHitTest @0x005D354B (do 34, and in do 34 from do 35), @0x005D6275 (in `0x005D6200`), @0x005D7982; InvBodyLoc @0x005D35EB; PrgFinisher @0x005D5A91, @0x005D639E, @0x005D63E6, @0x005D71F7; DeliverQueued @0x005D63AB, @0x005D63F3; Coll29F0 @0x005D7912; UnitTeleport @0x005D792D; returns 0, 1 |
  | `prg_ass` | entries 36–41, 143 | 2 100 | no step at entry (1 200); ring seed high word 0 (243); nova at the caster (45); x and y swapped (30); signed remainder (34); first charge's calc (7) | MissileCreate @0x0056D4CC (in NovaAtUnit), @0x005D4657, @0x005D4D77 (in the rings), @0x005D40D6, @0x005D51DA; DeliverQueued @0x005D3ED5; RollPhys @0x005D3F30; MissileCreateAt @0x005D5072; returns 0, 1 |
  | `trap_ass` | do 43, 44, 45, 47, 48, 49, 51, 54 | 2 400 | bad pet refused (75); bad pet kept (165); no owner swap (58); `≤` frame (6); other callback (65); no town test (24); packet `+0x00` 0 (118) | ScatterAtTarget @0x005D5DF9; SpawnOwned @0x005D5FB7 (in `0x005D5E10`, from do 44 and 45), @0x005D6F4A; ApplyTimed @0x005D6714; MissileCreate @0x005D696E; Sub553C70 @0x005D699E; RollPhys @0x005D7782, @0x005D7D75 (in `0x005D7CE0`); returns 0, 1 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 66 of 66 pins): the hash offsets, the `CALC_Eval` jump
  table, the skills calc function count `0x007457AC`, `g_BitMask32`, the town tables and NovaAtUnit's offsets. The
  count's scan matches every operand naming the address: 0 stores, 0 immediates, 7 reads in `.text` (`ref_scan`).
  Skills, Missiles, ItemStatCost, MonStats, the Levels records, the stat lists, the skill nodes, the queued hits, the
  rooms and the units are scratch records written one field per field read.
- [C] **Inputs set in the memory spec** (ADR-0015, S1e review ruling 3): `g_pDataTables`, pointed at a scratch
  DataTables, and the missile table and count `MissileSpeedAtLevel` reads (`0x0096C794`, `0x0096C79C`, as in batch
  `sor`) are inputs of the claims (no writer scan is cited for them); the security cookie is written as in 9a. No other
  image global is set. (run:2026-10-21-cat-emu-ass)
- [C] **The weak controls and their deciding classes** (ruling 4 of the `lane/p46m5` review; each class recounted from
  the case files with the lane's model). `start_ass`: `notown22` (41) fails on the 41 start 22 cases with a target of
  type 0 or 1 and a town room (the caster's or the target's); `keep18` (54) on the 54 start 24 cases with no target and
  a non-zero node `+0x18`; `mana_le` (16) on the 16 start 26 cases whose stat 8 equals `startmana · 256`; `st26_end7`
  (55) on all 55 `STATLIST_Alloc` cases; `st28_edx0` (41) on all 41 `GroupClear` cases (no case has `aurastate` 0
  there). `hit_ass`: `a1_any` (64) on the 64 do 34/35 cases with a target, a record and `aurastate` in range but
  `aurastat1` out of range; `notown22` (25) on the 25 such do 33 cases; `qhf_tgt` (63) on the 27 do 42 and 36 do 50
  cases where a node with the caster's words but another target comes first. `prg_ass`: `nova_caster` (45) on every
  nova case (the target's position differs from the caster's in all 45); `xy_swap` (30) on the scatter cases whose
  first hit has `dx ≠ dy` or moves; `dx_signed` (34) on the entry 41 creations whose first low word is `≥ 2³¹`;
  `prg_k1` (7) on the 7 cases on the progressive path with two or more charges (entries 38, 39, 41). `trap_ass`:
  `noowner` (58) on the 33 do 44 and 25 do 45 cases of a monster caster reaching the helper's owner step; `pet_refuse`
  (75) on the spawn cases with a bad `pettype`; `n18_le` (6) on the 6 do 48 cases whose node `+0x18` equals the frame;
  `cloak_cb` (65) on every `ApplyTimed` case; `town_any` (24) on every do 54 town case. Each family has a control failing
  90 or more (`st25_inv` 300, `parity_inv` 350, `noseed` 1 200, `pet_keep` 165). (run:2026-10-21-cat-emu-ass)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills and Levels
  columns `[C]` by layout; unit, node, stat-list, queued-hit and room offsets `[I]`, skills/0001, skills/0008,
  stats/0002, drlg/0005), and nothing here says when the game runs these functions or on which seed state.
  (run:2026-10-21-cat-emu-ass)

### 3. The start functions: 22–28

- [C] **Start 22** (`0x005D30F0`): `UNIT_GetTargetUnit` 0 → 0; `RoomIsTown(UnitGetRoom(caster))` → 0;
  `RoomIsTown(UnitGetRoom(target))` → 0; else `1 if target type ≤ 1 (unsigned) else 0` (`mov eax, 1; cmp eax, esi;
  sbb eax, eax; add eax, 1`). It reads neither the record nor its two stack words (`ret 8`). (run:2026-10-21-cat-emu-ass
  `start_ass`, fn:sub_005D30F0_SkillSt22PsychicTest@0x005D30F0)
- [C] **Start 25** (`0x005D6330`): `UNIT_GetTargetUnit(game, caster) ≠ 0` (`neg; sbb; neg`); the whole function is 16
  bytes (`push edx; push ecx; call UNIT_GetTargetUnit; neg eax; sbb eax, eax; neg eax; ret 8`).
  (run:2026-10-21-cat-emu-ass `start_ass`, fn:sub_005D6330_SkillSt25HasTarget@0x005D6330)
- [C] (ADR-0021; ends at `InMeleeRange` @0x005D330B) **Start 23**: no target → 0 (`EAX` the null); else
  `InMeleeRange(caster, target, 0)`, whose value it returns (after, `[I]`). (run:2026-10-21-cat-emu-ass `start_ass`,
  fn:sub_005D32F0_SkillSt23MeleeRange@0x005D32F0)
- [C] (ADR-0021; ends at `InMeleeRange` @0x005D59DD) **Start 24**: the record; `UNIT_GetUsedSkill` 0 → 0; no target →
  `UnitSkillSet18(node, 0)` (the `push 0` at `0x005D59BE` serves both calls) and 0; else `InMeleeRange(caster, target,
  0)`. (run:2026-10-21-cat-emu-ass `start_ass`, fn:sub_005D5970_SkillSt24DragonTalon@0x005D5970)
- [I] After start 24's boundary: out of range → 0; in range → `n = calc1 − 1` into the node's `+0x18`,
  `0x005D5880(ECX game, EAX caster, EDI id; target, rec, lvl, n == 0)` (not read), 1. (0x005D59DD–0x005D5A2C)
- [C] (ADR-0021; ends at `StatListSetEnd` @0x005D6AED or `STATLIST_Alloc` @0x005D6A81) **Start 26**: the record;
  `SrvMissileByCharge(caster, id)` < 0 → 0 (run on the non-progressive path only, `srvmissilea`); `SKILLS_GetUnitSkill`
  0 → 0; `UNIT_FindStatListByState(caster, 12)` found → `StatListSetEnd(list, frame + 7)`; none: `startmana`
  (`+0x184`, `cmp word …, ax; jle`, so only a positive value tests) and `STATS_GetUnitStat(caster, 8, 0) <
  startmana << 8` (`jl`) → 0; else `STATLIST_Alloc(game+0x1C, 2, frame + 21, caster type, guid)`.
  (run:2026-10-21-cat-emu-ass `start_ass`, fn:sub_005D69D0_SkillSt26BladeFury@0x005D69D0)
- [I] After start 26's boundaries: the existing list → event 12 at `frame + 7`; the unit skill's `+0x18` above the frame
  → `0x00553C70(game, caster; 1)` and 1; else do 48 (§ 6) and, on a non-zero result, `SKILLS_PayCost`; returns do 48's
  value. A new list → 0 → 0; event 12 at `frame + 21`, `STATLIST_LinkToUnit`, the remove callback `0x005D69B0`
  (`STATE_Set(unit, state, 0)` and bit 6 set), `STATLIST_SetState(list, 12)`, `STATE_Set(caster, 12, 1)`, the unit
  skill's `+0x18` = 0; 1. By the stock row (266 Blade Fury) state 12 is Blade Fury's own timed state.
  (0x005D6A81–0x005D6B55, 0x005D69B0–0x005D69C8)
- [C] (ADR-0021; ends at `0x0056E520` @0x005D70E6) **Start 27**: the record; `sub_0056E520_SkillAttackRateList(ECX
  caster, EDX Param4)` (`+0x154`). (run:2026-10-21-cat-emu-ass `start_ass`, fn:sub_005D7090_SkillSt27DragonTail@0x005D7090)
- [I] After start 27's boundary: no target → 0; a zeroed packet, `MeleeHitTest(target, GetToHit + stat 325, 0)`; no
  hit → 0; a hit → `0x005D54B0(game, &packet, target, id, lvl)` (not read), `ResolveAndQueue(…, SrcDam or 0x80)`, 1.
  (0x005D70E6–0x005D717B)
- [C] (ADR-0021; ends at `STATE_GroupClear` @0x005D7AA1) **Start 28**: the record; `SKILLS_GetUnitSkill` 0 → 0;
  `SrvMissileByCharge` ≤ 0 → 0; `auralencalc` (`+0x60`) ≤ 0 → 0; `aurastate` in `[0, States count)` (`jl`, `jge`; else
  0); `STATE_GroupClear(ECX caster, EDX aurastate; 0)` (`EDX` from the `movsx edx, ax` at `0x005D7A84`).
  (run:2026-10-21-cat-emu-ass `start_ass`, fn:sub_005D7A00_SkillSt28BladeShield@0x005D7A00)
- [I] After start 28's boundary: `STATE_ApplyTimed({caster, caster, id, lvl, auralencalc, −1, 0, aurastate, 0})` (0 →
  0), `SKILLS_ApplyAuraStats`, stats 350/351, `UnitSetStateBit(caster, aurastate, 1)`; 1. (0x005D7AA1–0x005D7B48)

### 4. The hits and the finishing moves: do 33, 34, 35, 42, 46, 50, 52

- [C] (ADR-0021; ends at `SkillRollPhys` @0x0057E257 inside `0x0057E240`, do 33's return `0x005D31BF` compared) **Do
  33** (`0x005D3140`): the record; start 22's test (`0x005D30F0`, § 3) 0 → 0; the target; a zeroed 0x70-byte packet
  (`ebp−0x7C`); `0x0057E240(ECX caster, EDX id; lvl, &packet)` → `SkillRollPhys(ECX caster, EDX &packet; id, lvl)`, the
  packet compared by content. (run:2026-10-21-cat-emu-ass `hit_ass`, fn:sub_005D3140_SkillDo33PsychicHammer@0x005D3140,
  fn:sub_0057E240_SkillRollPhysElem@0x0057E240)
- [I] After do 33's boundary: `SKILLS_RollElemDamage`; `COMBAT_ApplyDamage(target, 1, &packet)`; `+0x04 |= 1`; the
  target's stat 12 read twice and cancelled (`lvl + s − s`, so the level stays `lvl`); a calc by the target's kind
  (`calc4` for a player or a hireling, `calc3` for a boss, `calc2` for `MonTypeFlag(target, 8)`, else `calc1`); if it
  is above 0, **one inline step of the caster's seed** and `+0x04 |= 8` (knockback, by the layout) when `low % 100 <`
  it; `+0x04 |= 2` (killed) when the target's stat 6 has no bit above the low byte (`test eax, 0xFFFFFF00`); `COMBAT_GetHit(target, &packet)`; 1. (0x005D31BF–0x005D32E8)
- [C] (ADR-0021; ends at `MeleeHitTest` @0x005D354B) **Do 34** (`0x005D3490`): the target first (0 → 0); the record;
  `aurastate` in `[0, States count)` and `aurastat1` (`+0x54`) in `[0, ItemStatCost count)` (`jl`, `jge`; else 0); a
  zeroed packet at `ebp−0x78`; `MeleeHitTest(ECX game, EDX caster; target, SKILLS_GetToHit(caster, id, lvl), 0)` (the
  0 pushed before `GetToHit`, `ret 0xC`). (run:2026-10-21-cat-emu-ass `hit_ass`,
  fn:sub_005D3490_PrgChargeHitDo@0x005D3490)
- [I] After do 34's boundary: as skills/0001 § 12 (`ResolveAndQueue` with `SrcDam` or 0x80, `QueuedHitFind`, bit 0 →
  `SKILLS_AddProgressiveCharge(game; id, lvl, aurastate, aurastat1)`, `DeliverQueued`), 1. (0x005D354B–0x005D35BE)
- [C] (ADR-0021; ends at `InvGetBodyLocItem` @0x005D35EB, or at do 34's `MeleeHitTest` with do 35's return
  `0x005D3648` compared) **Do 35** (`0x005D35D0`): the inventory (`+0x60`) non-null → `InvGetBodyLocItem(inventory,
  4)`; null → bit 6 of `+0xC4` **set** when bit 8 of `+0x38` is set, **cleared** when it is clear (`sar 8; and
  0x80000001`), then do 34 with the same arguments; do 35 returns **1** where do 34 refuses with 0 (run), and its
  `mov eax, 1` after the call (`0x005D3648`) returns 1 after do 34's hit path too (`[I]`, after the boundary).
  (run:2026-10-21-cat-emu-ass `hit_ass`, fn:sub_005D35D0_PrgChargeHitDualDo@0x005D35D0)
- [I] After do 35's inventory boundary: the items at body locations 4 and 5; two different items that both pass
  `0x0062A4E0` (an item without the `+0x18` bits `0x100` or `0x4000`) and `ITEMS_UnitIsType(…, 0x2D)` take the parity
  path above; any other inventory sets bit 6 unconditionally; then do 34. (0x005D35EB–0x005D362D)
- [C] (ADR-0021; ends at `COMBAT_PrgFinisher` @0x005D5A91) **Do 42** (`0x005D5A30`): the record; the target (0 → 0);
  `QueuedHitFind(ECX caster, EDX target)`; `PrgFinisher(ECX game, EDX caster; hit)` with the hit's address (node
  `+0x14`) **or 0**. (run:2026-10-21-cat-emu-ass `hit_ass`, fn:sub_005D5A30_SkillDo42DragonTalon@0x005D5A30)
- [I] After do 42's boundary: `DeliverQueued`; the used node (0 → 0); `n = UnitSkillGet18(node) − 1` (< 0 → 0) stored
  back; `n > 0` → `0x005D5880(…, 0)`, `DeliverQueued`, bit 6 cleared, `0x0056E210(caster, 0x64)`, 1; `n = 0` (the last
  kick): a value `k` = 100, or for a player or hireling target `calc4`, for a boss `calc3`, for `MonTypeFlag(target,
  8)` `calc2` (a `k` ≤ 0 skips the draw); **`RNG_Range(caster+0x20, 100) < k`** → the flag 1; `0x005D5880(…, flag)`,
  `DeliverQueued`, 1. (0x005D5A91–0x005D5BE9)
- [C] (ADR-0021; ends at `MeleeHitTest` @0x005D6275 inside `0x005D6200`, do 46's return `0x005D6386` or `0x005D63CE`
  compared; or at `PrgFinisher` @0x005D639E / @0x005D63E6 or `DeliverQueued` @0x005D63AB / @0x005D63F3) **Do 46**
  (`0x005D6340`): the target (0 → 0); bit 8 of `+0x38` chooses one of two identical call sequences;
  `0x005D6200(EBX id, ESI caster; game, target, lvl)`: the record, a zeroed packet (`ebp−0x74`), `MeleeHitTest(ECX
  game, EDX caster; target, GetToHit(caster, id, lvl) + STATS_GetUnitStat(caster, 325, 0), 0)`; a bad id returns from
  the helper, and do 46 goes on to `QueuedHitFind(caster, target)`: found → `PrgFinisher(game, caster; hit)`, none →
  `DeliverQueued(game, caster; target, 0)`. Bit 6 is untouched before these calls. (run:2026-10-21-cat-emu-ass
  `hit_ass`, fn:sub_005D6340_SkillDo46DragonClaw@0x005D6340, fn:sub_005D6200_DragonClawHit@0x005D6200)
- [I] After do 46's hit test: on a hit `+0x00 |= 2`, `COMBAT_PrgHooksBeforeBuild`, `calc1` added to `+0x0C` (the
  enhanced-damage percent by the layout, `re/types/combat.h`), and with a non-zero `EType` the conversion pair (`+0x68 =
  calc4`, `+0x65 = EType` when `calc4 > 0`) and `SKILLS_RollElemDamage` (none without an `EType`),
  `COMBAT_BuildDamage(…, SrcDam)`,
  `COMBAT_PrgHooksAfterBuild`; then `ResolveAndQueue(…, 0x80)`; back in do 46 the finisher or the delivery as above,
  `DeliverQueued`, and bit 6 **cleared** (bit 8 clear) or **set** (bit 8 set); 1. (0x005D6275–0x005D631F,
  0x005D6386–0x005D6405)
- [C] (ADR-0021; ends at `PrgFinisher` @0x005D71F7) **Do 50** (`0x005D7180`): the record; the target (0 → 0);
  `QueuedHitFind` 0 → 0; the hit's 0x70 bytes copied to `ebp−0xEC` (`rep movs`, compared); `PrgFinisher(game,
  caster; hit)`. (run:2026-10-21-cat-emu-ass `hit_ass`, fn:sub_005D7180_SkillDo50DragonTail@0x005D7180)
- [I] After do 50's boundary: `DeliverQueued`; a living caster (`UnitIsDead` 0): a zeroed packet with `+0x10 =
  MulDiv(copy +0x08, calc1 + stat 329, 100)` and `+0x04 = 9`, `AreaHitAt(game, caster; the target's position,
  aurarangecalc, &packet, 0)`; 1. By the layout (`re/types/combat.h`) `+0x10` is the fire damage and `+0x08` the
  physical, so the area hit is fire of `calc1 + stat 329` percent of the kick's physical damage. (0x005D71F7–0x005D72A0)
- [C] (ADR-0021; ends at `MeleeHitTest` @0x005D7982, `0x006229F0` @0x005D7912 or `UnitTeleport` @0x005D792D) **Do 52**
  (`0x005D7850`): the record; the target (0 → 0); bit 8 of `+0x38` set → a zeroed packet, `MeleeHitTest(target,
  GetToHit + stat 325, 0)`; clear → the caster's room (0 → 0), **bit 6 cleared**, `SKILLS_GetTargetXY` (0 → 0),
  `LEVELS_GetRecord(RoomGetLevelId(room))` (`0 < lid < DataTables+0xC5C`, record `0x220`; 0 → 0), its `+0x04` byte
  (Levels `Teleport`): 0 → 0; 2 → `0x006229F0(caster, x, y, 0x804)`; any other → `UnitTeleport(ECX game, EDX caster;
  0, x, y, 0, 0)`. (run:2026-10-21-cat-emu-ass `hit_ass`, fn:sub_005D7850_SkillDo52DragonFlight@0x005D7850)
- [I] After do 52's boundaries: a hit → `+0x0C = SkillParamByLevel(id, lvl)`, `0x005D54B0`; then `ResolveAndQueue`,
  `QueuedHitFind` → `PrgFinisher` (no null test), `DeliverQueued`, 1; `0x006229F0` non-zero → 0; the teleport → 1.
  So Dragon Flight alternates by the frame parity between a kick (bit 8 set) and a teleport to the target point, and
  on a `Teleport` 2 level (Duriel's Lair, Levels § `Teleport`) the point must pass `0x006229F0` (not read).
  (0x005D7982–0x005D79FB, 0x005D7912–0x005D7938)

### 5. The progressive entries: 36–41 and 143

```c
// fn:sub_005D4E70_SkillPrgDo37Ring@0x005D4E70 (143 alike, ring 0x005D4870), trimmed
u->seed = step(u->seed); low = u->seed.lo;                  // before any test
if (!rec || (m = SrvMissileByCharge(u, id)) <= 0 || !SKILLS_GetTargetXY(game, u; &x, &y)) return 0;
n = PrgCalcByCharge(u, id; lvl) ?: EvalCalc(aurarangecalc);
// ring(EDX low; game, u, m, x, y, id, lvl, n):
RNG_SeedInit(&loc, low);  /* hi 0x29A */  dirs[64] on the frame;
for (i = 0; i < 64; i += n) { loc = step(loc); blk = {3, u, .cls m, x, y, .tx dx[i], .ty dy[i], id, lvl,
    .cb 0x005D40F0 /* 143: 0x005D4680 */, .arg loc.lo}; mis = MissileCreate(game, &blk); ... }
```

- [C] (ADR-0021; ends at `MissileCreate` @0x0056D4CC inside `SkillNovaAtUnit`, entry 36's return `0x005D4E58`
  compared) **Entry 36** (`0x005D4DB0`): the target (0 → 0); `lvl ≤ 0` → 0; the record; `m = SrvMissileByCharge(caster,
  id)` ≤ 0 → 0; `v = MissileSpeedAtLevel(m, lvl) + calc1` (`(VelLev · lvl) / 8 + Vel`, the bytes `+0x9B`, `+0x9A`,
  signed division); `SkillNovaAtUnit(ECX game, EDX caster; target, m, id, lvl, v)`: the block `{flags 3, | 4 with v ≠ 0,
  owner the caster, +0x10 m, +0x14/+0x18 the **target's** position (types 2, 4, 5 its static path `+0x0C`/`+0x10`, else
  `PathGetX/Y`, 0 without a path), +0x1C/+0x20 the first of the 64 offsets `0x006E1288`/`0x006E1388`, +0x28 v, +0x2C
  id, +0x30 lvl}`, compared by content. (run:2026-10-21-cat-emu-ass `prg_ass`,
  fn:sub_005D4DB0_SkillPrgDo36NovaAtTarget@0x005D4DB0, fn:sub_0056D400_SkillNovaAtUnit@0x0056D400)
- [C] (ADR-0021; ends at the ring's first `MissileCreate` @0x005D4657 / @0x005D4D77, the return `0x005D4F2E` /
  `0x005D4FFE` compared) **Entries 37 and 143**: one inline step of the caster's seed at entry (`mul 0x6AC690C5; add
  hi; adc`), its low word kept; the record (0 → 0, the seed already stepped); `m` ≤ 0 → 0; `SKILLS_GetTargetXY` 0 → 0;
  `n = PrgCalcByCharge(caster, id; lvl)`, or `aurarangecalc` when that is 0; the ring (`EDX` the low word; game,
  caster, m, x, y, id, lvl, n): `RNG_SeedInit(local, low)` (high `0x29A`), the 64 directions written on its frame (the
  first `(30, 0)`), **one step of the local seed**, the block `{3, caster, +0x10 m, +0x14/+0x18 the target point,
  +0x1C/+0x20 (30, 0), +0x2C id, +0x30 lvl, +0x54 0x005D40F0 (37) / 0x005D4680 (143), +0x58 the stepped local low}`
  and `MissileCreate(ECX game, EDX &block)`; the block by content and the local seed (`0x7FEFFFAC`) compared. **`n` is
  not tested** before the first creation. (run:2026-10-21-cat-emu-ass `prg_ass`, fn:sub_005D4150_SkillRing64LocalSeed@0x005D4150,
  fn:sub_005D4870_SkillRing64LocalSeedB@0x005D4870)
- [I] After the rings' first creation: the index steps by `4n` bytes (`add edi, edi` twice; `add esi, edi`; `cmp esi,
  0x100; jl`), so the ring makes `⌈64 / n⌉` missiles for `n > 0`, **never ends for `n = 0`** (a creation per pass, the
  index not moving) and reads below the table for `n < 0` until the signed index passes 0x100, which it does not
  (an endless loop as well); ring 37 then writes `MISSDATA_SetSeedLow(missile, SkillGetParam2(280) + 1)` with **no
  null test** of the missile, ring 143 the same only for a non-null missile of class 568
  (`royalstrikechainlightning`); `SkillGetParam2`'s argument is the immediate `0x118` (row 280 Royal Strike), whatever
  row runs the ring. Not run past the first creation. (0x005D4657–0x005D467D, 0x005D4D77–0x005D4DAA)
- [C] (ADR-0021; ends at `DeliverQueued` @0x005D3ED5 or `SkillRollPhys` @0x005D3F30) **Entry 38** (`0x005D3E80`): the
  record; a target → `DeliverQueued(ECX game, EDX caster; target, 0)`; none: `SKILLS_GetTargetXY` 0 → 0; `r =
  PrgCalcByCharge` or `aurarangecalc`, stored at `[ebp+0x8]` (compared); a zeroed packet; `SkillRollPhys(ECX caster,
  EDX &packet; id, lvl)`. (run:2026-10-21-cat-emu-ass `prg_ass`, fn:sub_005D3E80_SkillPrgDo38AreaHit@0x005D3E80)
- [I] After entry 38's boundaries: after the delivery the same path (target point, `r`, the rolls); after the rolls
  `+0x04 |= 1`, `+0x00 |= 1`, `SKILLS_ForUnitsInRange(game, caster; x, y, r, aurafilter, 0x005D3CB0, &packet, 0, file,
  0x304)`, as skills/0003 § 1; 1. (0x005D3ED5–0x005D3F82)
- [C] (ADR-0021; ends at `MissileCreate` @0x005D40D6) **Entry 39** (`0x005D3F90`): one inline step of the caster's seed
  at entry, the low word kept; the record; `SKILLS_GetTargetXY` 0 → 0; `m` ≤ 0 → 0; `r` (as entry 38); the block
  `{1, caster, +0x10 m, +0x2C id, +0x30 lvl}`; `RNG_SeedInit(local, low)`; `UnitGetRoom(caster)`; `r · r` (32-bit
  `imul`; ≤ 0 → returns 1) tries of `dx = r − RNG_Range(local, 2r)`, `dy = r − RNG_Range(local, 2r)` (x first; a
  `2r` ≤ 0 gives 0 without a step); a try with `dx² + dy² ≤ r²` and `RoomAtSubtile(room, x + dx; y + dy)` ends at
  `MissileCreate` with `+0x14 = x + dx`, `+0x18 = y + dy`; no such try → 1. The local seed (`0x7FEFFFE4`) and the
  block compared. (run:2026-10-21-cat-emu-ass `prg_ass`, fn:sub_005D3F90_SkillPrgDo39Scatter@0x005D3F90)
- [C] (ADR-0021; ends at `MissileCreateAt` @0x005D5072) **Entry 40** (`0x005D5010`): `SKILLS_GetTargetXY` 0 → 0;
  `lvl ≤ 0` → 0; `m = SrvMissileByCharge` ≤ 0 → 0 (−1 for a bad id: there is no record test of its own);
  `MissileCreateAt(ECX game, EDX caster; id, lvl, m, x, y)`. (run:2026-10-21-cat-emu-ass `prg_ass`,
  fn:sub_005D5010_SkillPrgDo40MissileAt@0x005D5010)
- [C] (ADR-0021; ends at `MissileCreate` @0x005D51DA) **Entry 41** (`0x005D5080`): one inline step of the caster's seed
  and `RNG_SeedInit(local, low)` before the record test; the record; `SKILLS_GetTargetXY` 0 → 0; `m` ≤ 0 → 0; `n =
  PrgCalcByCharge` 0 → 0; the zeroed block `{3, caster, +0x10 m, +0x14/+0x18 the target point, +0x2C id, +0x30 lvl}`;
  `n < 0` → 1; else two inline steps of the local seed, `dx = low₁ mod 40 − 20`, `dy = low₂ mod 40 − 20` (unsigned
  remainders by `0xCCCCCCCD`; both 0 → `dx = 20`) at `+0x1C`/`+0x20`, and `MissileCreate`. The local seed
  (`0x7FEFFFE8`) and the block compared. (run:2026-10-21-cat-emu-ass `prg_ass`, fn:sub_005D5080_SkillPrgDo41Scatter@0x005D5080)
- [I] After entries 39 and 41: 39's remaining tries; 41's `MISSDATA_SetSeedLow(missile, local low)` and
  `MISSDATA_SetParam2C(missile, dy << 16 | dx & 0xFFFF)` for each created missile, `n − 1` more; both return 1.
  (0x005D40D6–0x005D40E7, 0x005D51DA–0x005D5218)
- [I] **`PrgCalcByCharge`** (`0x005D3DA0`, emulated in every case above): no record → 0; Skills `+0x04` bit 2 clear, an
  `aurastate` or `aurastat1` out of range, or no list of the state on the caster → `prgcalc1` (`+0x38`); else the
  calc at `+0x34 + 4 · clamp(charges, 1, 3)` (`prgcalc1..3`), the charges being the list's `aurastat1` base stat.
  `[C]` as part of the entries' maps above (the `prg_k1` control). (fn:sub_005D3DA0_SkillPrgCalcByCharge@0x005D3DA0)

### 6. Traps, states and areas: do 43, 44, 45, 47, 48, 49, 51, 54

- [C] (ADR-0021; ends at `MissScatterAtTarget` @0x005D5DF9) **Do 43** (`0x005D5D70`): the record; `m =
  SrvMissileByCharge` < 0 → 0 (`jl`: class 0 admitted); `n = PrgCalcByCharge` ≤ 0 → 0; `MissScatterAtTarget(ECX game,
  EDX caster; caster, m, n, aurarangecalc, id, lvl)`, whose value it returns (after, `[I]`; skills/0007).
  (run:2026-10-21-cat-emu-ass `trap_ass`, fn:sub_005D5D70_SkillDo43ShockField@0x005D5D70)
- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005D5FB7 inside `0x005D5E10`, do 44's return `0x005D60AD` or do 45's
  `0x005D61E3` compared) **Do 44** (`0x005D6020`): the record; `SkillSummonClass(ECX caster, EDX 0; id, lvl, &mode, 0,
  0)` (a class in range in every case, as skills/0013); bit 6; `SKILLS_GetTargetXY` 0 → 0 (bit 6 set);
  `0x005D5E10(game, caster; 0, 0, rec, id, lvl)`. **Do 45** (`0x005D6170`): the record; bit 6; `SKILLS_GetTargetXY`
  0 → 0; `0x005D5E10(game, caster; x, y, rec, id, lvl)`. **`0x005D5E10`**: `SkillSummonClass` again (the class in
  `[0, MonStats count)` in every case); `pettype` (`movsx`) negative or at or past `DataTables+0xBF0` → **0, not a
  refusal**; `petmax`; an `x` or `y` of 0 → the caster's position (`PathGetX/Y` of its path; the cases' casters are of
  types 0 and 1); a monster caster replaced by its owner (`MonsterOwner`, none → 0; the owner a player in every case);
  an `x` or `y` still 0 → `SKILLS_GetTargetXY(game, that unit)` (0 → 0); `RoomAtSubtile(UnitGetRoom(that unit), x; y)` 0 → 0;
  `InTown` (`+0x05` bit 0) clear and `RoomIsTown` → 0; the nine words `{1, unit, class, 0, mode, x, y, pettype,
  petmax}` at `ebp−0x50` and `SpawnOwnedMonster(ECX game, EDX &block)`, compared by content (the tenth word `+0x24`,
  `ebp−0x2C`, is not written by the helper and not compared). (run:2026-10-21-cat-emu-ass `trap_ass`,
  fn:sub_005D6020_SkillDo44BladeSentinel@0x005D6020, fn:sub_005D6170_SkillDo45Sentry@0x005D6170,
  fn:sub_005D5E10_TrapSpawn@0x005D5E10)
- [I] Not run: `SkillSummonClass`'s refusal and the helper's own class-count refusal (`cmp ecx, [eax+0xA80]; jge`,
  `0x005D5E48`); a caster of type 2, 4 or 5 (its static path's `+0x0C`/`+0x10` as the position, `0x005D5E94`–`0x005D5EBB`);
  an owner that is itself a monster (the `MonsterOwner` loop's second pass). (0x005D5E36–0x005D5F04)
- [I] After the spawn: no unit → 0; `SummonSetLevel(game, owner; m, 0, lvl)`, `SummonInitStats(m, id, lvl, 0)`,
  `MonAlignSet(m, 2; 1)`, `MonCmdInit(m, …, buf)`, `MonSetMode(game, buf, 1)`, the unit returned. Do 44: stat 12 copied
  from the caster, `UnitTeleport(game, m; the caster's room and position, 0, 0)`, `0x0058EF40(game, m; &{0, 0, 0, the
  caster's position, the target point})`, `UNIT_CancelEvents(m; 2, 0)`, event 2 at `frame + 1`, the unit's `+0xC4` bit 3
  cleared; 1. Do 45: `m ≠ 0`. So a Blade Sentinel is spawned at the caster and moved, a sentry at the target point; the
  spawn's `+0x24` word is the helper's stack content (skills/0009's open question on that word). (0x005D5FB7–0x005D6012,
  0x005D60AD–0x005D616B)
- [C] (ADR-0021; ends at `STATE_ApplyTimed` @0x005D6714) **Do 47** (`0x005D6630`): the record; `aurastate` in
  `[0, States count)` (else 0); `UNIT_HasState(caster, aurastate)` non-zero → 0; the block `{caster, caster, id, lvl,
  auralencalc, passivestat1 (s16 +0x98), passivecalc1 (+0xA4), aurastate, 0x0056E900}` and `STATE_ApplyTimed(ECX
  &block)`, compared by content. (run:2026-10-21-cat-emu-ass `trap_ass`, fn:sub_005D6630_SkillDo47Cloak@0x005D6630)
- [I] After do 47's boundary: 0 → 0; `passivestat2..5` with the non-zero `passivecalc2..5` values, stats 350/351,
  `UnitSetStateBit(caster, aurastate, 1)`; `auratargetstate` (`+0x82`) in range → a block `{id, lvl, auralencalc,
  auratargetstate, aurastat1..6 and their aurastatcalc values}` and `SKILLS_ForUnitsInRange(game, caster; 0, 0,
  aurarangecalc, aurafilter, 0x005D6520, &block, 1, file, 0x874)`, whose callback gives each living unit the target state
  by `STATE_ApplyTimed` (callback `0x005C3370`, length −1 when not positive) with those stats, and for a monster that
  `0x0056E2F0(…, 10)` accepts calls `0x005B0E00(…, 10)`; 1. (0x005D6714–0x005D688A, 0x005D6520–0x005D6622)
- [C] (ADR-0021; ends at `MissileCreate` @0x005D696E or `0x00553C70` @0x005D699E) **Do 48** (`0x005D68A0`):
  `SKILLS_GetUnitSkill(caster, id)` 0 → 0; `m = SrvMissileByCharge` < 0 → 0; `n = PrgCalcByCharge − 1` ≤ 0 → 0; bit 6
  **cleared**; `SKILLS_GetTargetXY` 0 → 0; the unit skill's `+0x18` below the frame (signed `jge` skips) → the zeroed
  block `{0x20, caster, +0x08 caster, +0x10 m, +0x1C/+0x20 the target point, +0x2C id, +0x30 lvl}` and `MissileCreate`;
  otherwise `UNIT_HasState(caster, 12)` → `0x00553C70(ECX game, EDX caster; 1)`, else 0. (run:2026-10-21-cat-emu-ass
  `trap_ass`, fn:sub_005D68A0_SkillDo48BladeFury@0x005D68A0)
- [I] After do 48's creation: the unit skill's `+0x18 = frame + n`, then the same state-12 test; returns 1. So Blade
  Fury fires at most once per `n` frames (`n` = `prgcalc1 − 1` for the stock row) and ends under state 12.
  (0x005D696E–0x005D69A7)
- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005D6F4A) **Do 49** (`0x005D6E70`): bit 6 set first (a non-null
  caster); the record; `SkillSummonClass(ECX caster, EDX 0; id, lvl, &mode, 0, 0)`; `pettype` (`movzx`) at or past the
  count → 0; the block `{0, caster, class, 0, mode, 0, 0, pettype, petmax, mode}` (`+0x24` the slot the class call
  wrote the mode to, as do 114) and `SpawnOwnedMonster(ECX game, EDX &block)`. (run:2026-10-21-cat-emu-ass `trap_ass`,
  fn:sub_005D6E70_SkillDo49Shadow@0x005D6E70)
- [I] After do 49's boundary: no unit → 0; the caster's stat 12 copied, `0x005D6CF0(game, rec, id, lvl)`, a level from
  `SkillParam5ByLevel` capped by `ExpMaxLevel`, `MonEquipInit(m, id, lvl, that, 0)`, `UNIT_CancelEvents(2, 0)`, event 2
  at `frame + 20`, `aurastate` (0 < s < count) set on the summon, `UnitSetOwner(m, caster)`, `auralencalc` > 0 → event 7
  at `frame + len` and `ModAppendApply(0x15, 0)`, `0x005B1900(…, caster +0xD0)`; 1. (0x005D6F4A–0x005D7146)
- [C] (ADR-0021; ends at `SkillRollPhys` @0x005D7782) **Do 51** (`0x005D76E0`): the record; `SKILLS_GetTargetXY` 0 →
  0; `r = PrgCalcByCharge` or `aurarangecalc`, stored at `[ebp+0xC]` (compared); a zeroed packet; `SkillRollPhys(ECX
  caster, EDX &packet; id, lvl)`. (run:2026-10-21-cat-emu-ass `trap_ass`, fn:sub_005D76E0_SkillDo51MindBlast@0x005D76E0)
- [I] After do 51's boundary: `SKILLS_RollElemDamage`, `ResultFlags` into `+0x04`, `HitFlags` into `+0x00`, a block
  `{&packet, 0x00645C10(lvl, id), Param3, Param4}` and `SKILLS_ForUnitsInRange(game, caster; x, y, r, aurafilter,
  0x005D7680, &block, 0, file, 0xB43)`; 1. (0x005D7782–0x005D7840)
- [C] (ADR-0021; ends at `SkillRollPhys` @0x005D7D75 inside `0x005D7CE0`, do 54's return `0x005D7E81` compared) **Do
  54** (`0x005D7E10`): the record; `aurastate` in `[0, States count)`; `SKILLS_GetUnitSkill` 0 → 0; the caster's room a
  town room → **1** with nothing done; else `0x005D7CE0(game, caster; id, lvl)`: the record, `r = PrgCalcByCharge` or
  `aurarangecalc` stored at its first argument slot (`0x7FEFFFE8`, compared), a zeroed packet with `+0x00 = 2`,
  `SkillRollPhys(ECX caster, EDX &packet; id, lvl)`. (run:2026-10-21-cat-emu-ass `trap_ass`,
  fn:sub_005D7E10_SkillDo54BladeShield@0x005D7E10, fn:sub_005D7CE0_BladeShieldArea@0x005D7CE0)
- [I] After do 54's boundary: `SKILLS_RollElemDamage`, `HitClass` into `+0x60` when non-zero, a block `{&packet, the
  to-hit (`SKILLS_GetToHit` when `ResultFlags` bit 0 is clear), ResultFlags, HitFlags, SrcDam}` and
  `SKILLS_ForUnitsInRange(game, caster; 0, 0, r, aurafilter, 0x005D7C40, &block, 0, file, 0xC4F)`; 1. (0x005D7D75–0x005D7E07)

## Corrections to earlier findings

- skills/0001 § 12 (the Phase 1b note), carried there as a dated note: the two finisher calls at `0x005D6399` and
  `0x005D63E1` are in **do 46** (Dragon Claw's do function, `0x005D6340`), not in start 25: start 25 (`0x005D6330`) is the
  16-byte test `UNIT_GetTargetUnit ≠ 0` and calls nothing else (§ 1, § 3). The six callers are confirmed
  (`static.txt`). (fn:sub_005D6340_SkillDo46DragonClaw@0x005D6340, fn:sub_005D6330_SkillSt25HasTarget@0x005D6330)
- skills/0003 § 1, carried there as a dated note: entries 36–41 and 143 are now `[C]` up to their boundaries (§ 5);
  the rings' `MissileData+0x28` write is `SkillGetParam2(280) + 1` (the immediate `0x118`, Royal Strike's row, whatever
  row runs the ring), not the calling row's `Param2`; ring 37 does not test the missile for null; neither ring tests its
  step count (§ 5). § 9's sentence on `MissileData+0x28` as "a per-missile stored seed word" written by the rings is
  narrowed the same way. (0x005D4657–0x005D467D, 0x005D4D77–0x005D4DAA)
- skills/0003 § 5 (tier A), carried there as a dated note: start 23 and do 35 (the Fists of Fire row) are `[C]` up to
  their boundaries: do 35 sets or clears bit 6 by the caster's `+0x38` bit 8 only without an inventory, and returns 1
  where do 34 refuses (§ 4; after do 34's hit path 1 as well, `[I]`). (fn:sub_005D35D0_PrgChargeHitDualDo@0x005D35D0)

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `srvprgfunc1..3`, `ItemEffect`, `progressive` (`+0x04` bit 2),
`InTown` (`+0x05` bit 0), `prgcalc1..3` (`+0x38`–`+0x40`), `srvmissilea..c` (through `SrvMissileByCharge`),
`aurafilter` (after a boundary), `aurastat1` (`+0x54`), `auralencalc` (`+0x60`), `aurarangecalc` (`+0x64`),
`aurastate` (`+0x80`), `auratargetstate` (after a boundary), `passivestat1` (`+0x98`), `passivecalc1` (`+0xA4`),
`summon` (`+0xBC`), `pettype` (`+0xBE`), `summode` (`+0xBF`), `petmax` (`+0xC0`), `calc1`–`calc4` (`calc1` before a
boundary in entry 36), `Param4` (`+0x154`), `startmana` (`+0x184`), `ToHit`, `LevToHit`, `ToHitCalc`, `SrcDam`;
`tbl:Missiles.txt:Vel`, `VelLev`; `tbl:Levels.txt:Teleport` (`levels` `+0x004`); DataTables `+0xC4`, `+0xBD4`,
`+0xBF0`, `+0xA80`, `+0xC58`/`+0xC5C`; unit `+0x00`, `+0x0C`, `+0x14` (monster data `+0x28` owner link), `+0x20` seed,
`+0x2C` path, `+0x38` (bit 8), `+0x5C` stat list, `+0x60` inventory, `+0xA8` skills, `+0xAC` queued hits, `+0xC4`
bit 6; game `+0x1C`, `+0xA8`.

## Dead ends

- None in the code. The first emulation (`dev/dev1`, kept under its own names) mismatched on 131 do 46 and do 52 cases
  and one start 26 case where the model read the written stat values with integer keys from the case's json row, whose
  keys are strings (the model fixed); a second development run (`dev/dev2`) matched in full; the writers were
  re-weighted between the runs (`dev/notes.txt`). No claim rests on either.

## Open questions

- [L] What `0x005D5880` (start 24 and do 42's kick) and `0x005D54B0` (start 27 and do 52's hit) do with the packet,
  and what do 42's last-kick flag selects (§§ 3, 4).
- [L] Whether a stock progressive calc can make a ring's step count 0 or negative (an endless loop, § 5): Claws of
  Thunder's `prgcalc3` and Royal Strike's `prgcalc2` at their charge counts, or their `aurarangecalc` when those are 0,
  a harness or calc-table check.
- [L] What `0x006229F0` tests for Dragon Flight on a `Teleport` 2 level, and what `0x0058EF40` does with Blade
  Sentinel's path block (§§ 4, 6).
- [L] Everything after each boundary (§§ 3–6), for a later batch or the harness.
