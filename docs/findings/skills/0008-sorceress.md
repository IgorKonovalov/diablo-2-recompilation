# 0008 — Catalogue batch `sor`: the sorceress start functions 11–14 and do functions 17–29 and 144

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 11–14 (`srvstfunc`, `g_SkillStartFuncs`) and do function 17–29
> and 144 (`srvdofunc`, `g_SkillDoFuncs`) of the sorceress batch do: which Skills, Missiles and unit fields it reads,
> which states, missiles and monsters it creates, which draws it makes on which seed, what it returns, and which of
> that the emulator can confirm?
> **Date:** 2026-10-20   **Plan:** 0046 (Phase 1, batch `sor`)   **Status:** for review (`lane/p46m5`)

Static reading of the pinned `Game.exe` in Ghidra 12.1.2 (lane copy `workspace/ghidra-p46m5`, symbols replayed from
`re/symbols.csv`) and objdump, then emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged,
`286393aa…`) and the `sor` families of `tools/skills_catalogue_emu.py` (§ 2; run:2026-10-20-cat-emu-sor in
[experiments](experiments.md)). Skills columns are named as in [Skills](../../tables/Skills.md), Missiles columns as in
[Missiles](../../tables/Missiles.md). The machinery that calls a start or do function (`SKILLS_SrvStart`,
`SKILLS_SrvDo`, the cost and the srvmissile after the do function) is [skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart);
the tier-A entries of this batch (do 18, 20, 22, 27, 28) were read by plan 0045 in
[skills/0003 § 5](0003-handlers.md#5-tier-a-start-and-do-functions); the missile functions the created missiles run
are batches 9a–9d ([skills/0004](0004-missile-do-1-18.md)–[0007](0007-missile-hit-31-59.md)). Stock values come from
`workspace/logs/skills-cat-sor/rows.txt` (`excel_bin.py dump` of the 54 Skills rows whose `srvstfunc` is 11–14 or
whose `srvdofunc` is 17–29 or 144).

**Tag convention for this finding** (as skills/0007). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a
function entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site
(the return address at ESP), with a site control that fails every matched boundary case; (c) the model gives and the
checker compares every argument the claim uses (registers, stack words, and for a pointer into the caller's frame the
bytes it points to), every byte written before the call that the claim uses (the unit's `+0xC4`, the unit skill
node's words, the second argument slot), and the state of **the caster's and the target's seeds** at the boundary
(both, in every case). Each such claim names the boundary it ends at; **the callee and all code after it are not
covered** and keep `[I]` (from the reading), marked "after, `[I]`" in place, and what a callee makes of a compared
argument (a class, a mode, a state) is stated after the boundary (reverser review-fixes 13; the `lane/p46m4` review's
addition). No claim rests on a callee-saved register that is not a boundary argument (ruling 1 of the `lane/p46m3`
review). A plain `[C]` rests on cases that return; a plain `[I]` is a code reading the emulator does not reach.
(run:2026-10-20-cat-emu-sor)

## Answer (summary)

- [C] **The batch.** 18 entries: start 11 `0x005C8FA0`, 12 `0x005C9030`, 13 `0x005C91C0`, 14 `0x005C9220`; do 17
  `0x005C9300` to do 29 `0x005CA4D0` (thirteen, in address order) and do 144 `0x005CA910`. Every one is
  `(ECX game, EDX unit; skill id, level)` with `ret 8`. Do 18, 20, 22, 27 and 28 are tier A (skills/0003 § 5); 18, 20,
  22 and 28 are emulated here too, 27 is not (§ 9). (data:g_SkillStartFuncs@0x00732140,
  data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [C] **One draw before the boundaries.** Do 21 (Telekinesis) draws one `RNG_Range(caster seed, 100)` after its
  hostility and town tests, and sets the flag `[ebp−8]` to 1 when the draw is below `Param2` (signed; after, `[I]`:
  the packet's result `|= 9`, a stun); no other function of
  the batch draws before its boundary or return, and no case steps the target's seed (8 500 cases; a control that
  moves the draw to the target's seed fails 93). Draws inside a boundary callee (the creations, `SkillRollPhys`, the
  spawn) are not covered. (§ 4, run:2026-10-20-cat-emu-sor `tk_sor`)
- [C] (ADR-0021; up to `0x005C8E30`, `0x005C8CA0` or their callees, § 3) **Inferno and Arctic Blast.** Start 11
  refuses a caster outside state 12 whose mana (stat 8) is below `startmana << 8` (signed), and a `srvmissilea`
  outside the Missiles count, else calls `0x005C8E30(id, lvl, srvmissilea)`; do 19 calls `0x005C8CA0(id, lvl,
  srvmissilea)` with the same class test. `0x005C8CA0` passes `MissileCreate` the block `{flags 0x8020, owner and
  source the caster, the class, target the skill target point, skill, level, +0x4C = max(calc1, 1)}` while the used
  skill's `+0x18` is not 0; at 0 it sets it to 1 and calls `0x00553C70(1)`, or for a monster sets `+0x44 = 0xB00` and
  calls `0x005C8C10` or `UNIT_CancelEvents(1, 0)`. `0x005C8E30` sets a monster's used skill `+0x18 = frame +
  max(calc2, 1)`, then calls `STATLIST_Alloc(game+0x1C, 2, frame + 0x14, type, guid)` when the caster has no state-12
  list, else `0x00553C70(1)`. (run:2026-10-20-cat-emu-sor `start_sor`, `inferno_sor`)
- [C] **Start 12** (Telekinesis, Dragon Flight): with a target unit, refuses one farther than `aurarangecalc`
  (`dx² + dy² > r²`, 32-bit, signed), accepts any target that is not a player or monster (type above 1, unsigned),
  and for a player or monster needs `UnitsHostile` and neither unit in a town room. (§ 4, run:2026-10-20-cat-emu-sor
  `start_sor`; the two-player case ends at `PlayerPairFlags`, ADR-0021)
- [C] **Thunder Storm.** Start 13 sets the caster's unit skill node `+0x18 = −1`, `+0x1C = 1`. Do 29 (ADR-0021)
  passes `STATE_ApplyTimed` the block `{caster, caster, id, lvl, auralencalc, −1, 0, aurastate, 0}` unless the caster
  has the state and the node's `+0x1C` is 0; then it calls `NearestUnitInRange(game, caster; 0, 0, Param7, 3,
  node+0x18, 0)`. After, `[I]`: the strike (a `srvmissilea` at the unit found, `MISSILE_HitUnit`, the node's `+0x18` =
  that unit's guid). (§ 5, run:2026-10-20-cat-emu-sor `start_sor`, `state_sor`)
- [C] **Hydra.** Start 14 accepts a target point whose room (`RoomAtSubtile` from the caster's room and its near
  rooms) exists and is not a town. Do 144 (ADR-0021; up to the first `SpawnOwnedMonster`) tests the summon, `pettype`
  and the same room, takes a hireling caster's owner as the owner, and passes `{1, owner, summon, 0, summode (0..15,
  else 1), x − 1, y − 1, pettype, petmax, frame + Param1 + (lvl − 1)·Param2}`. After, `[I]`: two more spawns of the
  classes `summon + 1` and `summon + 2` at `(x, y)` and `(x + 1, y − 1)`. (§ 6, run:2026-10-20-cat-emu-sor `start_sor`,
  `hydra_sor`)
- [C] (ADR-0021; up to the first `MissileCreate`, `COLL_WHTest`, `SkillMissileCreate` or `SKILLS_ForUnitsInRange`,
  § 7) **Creations.** Do 17 (Charged Bolt) passes `{flags 0x21, owner, the caster's position, class, target point,
  skill, level, callback 0x005C9290, +0x58 index 0}` when calc1 > 0 and the target point is set (else returns 1);
  do 22 (Nova, Frost Nova) passes NovaAtUnit's first block `{flags 3 | 4 when vel ≠ 0, owner, class, position, target
  (30, 0), +0x28 vel, skill, level}` with `vel = Vel + VelLev·lvl / 8` (truncating, from the table at `0x0096C794`) +
  calc1; both take `srvmissileb`/`srvmissilec` instead of `srvmissilea` for a `progressive` row whose `aurastate`
  list holds `aurastat1` at 2 or 3+. Do 24 (Fire Wall) and do 28 (Meteor) end at `COLL_WHTest(room, target point,
  Size, Size, 5)`; do 26 (Chain Lightning) at `SkillMissileCreate(srvmissilea; caster, id, lvl, 0…)` with calc1 left
  in its second argument's slot; do 20 (Static Field) at `ForUnitsInRange(0, 0, aurarangecalc, aurafilter,
  0x005C96A0, {calc2, calc1, the difficulty record's +0x40 when game+0x70 ≠ 0 else 0, elemental length, EType})`.
  After, `[I]`: each creation's missile functions, the cell's meaning (free or not) and do 24's three creations.
  (run:2026-10-20-cat-emu-sor `create_sor`)
- [C] (ADR-0021; up to `STATE_GroupClear` or `STATE_ApplyTimed`, § 8) **Timed states.** Do 18 (the armours) ends at
  `STATE_GroupClear(caster, aurastate; 1)`; do 23 (Blaze, Energy Shield) and do 25 (Enchant) pass `{caster, unit,
  id, lvl, auralencalc, −1, 0, aurastate, 0}` to `STATE_ApplyTimed`, with `aurastat1 ≥ −1` (signed 16-bit) and
  `aurastate` in range; do 25's unit is its target when `UnitsSameParty` says so, else the caster.
  (run:2026-10-20-cat-emu-sor `state_sor`)
- [C] **Do 21 by target type** (§ 4): a player caster not busy; a missile or a type above 4 returns 1; an object ends
  at `OBJ_OperateDispatch(2, guid)`, an item at its first `ITEMS_UnitIsType(item, 0x16)` (ADR-0021); a player or
  monster as in the draw bullet, ending at `SkillRollPhys(id, lvl)` with a zeroed 0x70-byte packet (ADR-0021).
  (run:2026-10-20-cat-emu-sor `tk_sor`)
- [I] Not covered, from the reading: every callee boundary and what follows it (listed per function), do 27 (§ 9),
  `0x00553C70`, `0x005C8C10`, and when the game runs these functions. (fn:sub_005CA360_SkillTeleportDo@0x005CA360)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005C8FA0` | `sub_005C8FA0_SkillSt11Inferno` | start 11 (Inferno, Arctic Blast) | I |
| `0x005C9030` | `sub_005C9030_SkillSt12TargetInRange` | start 12 (Telekinesis, Dragon Flight) | I |
| `0x005C91C0` | `sub_005C91C0_SkillSt13StormArm` | start 13 (Thunder Storm) | I |
| `0x005C9220` | `sub_005C9220_SkillSt14PointOutOfTown` | start 14 (Hydra) | I |
| `0x005C9300` | `sub_005C9300_SkillDo17ChargedBolt` | do 17 | I |
| `0x005C9480` | `sub_005C9480_SkillDo18TimedSelfState` | (P1.3 name) do 18 | I |
| `0x005C9640` | `sub_005C9640_SkillDo19Inferno` | do 19 | I |
| `0x005C9800` | `sub_005C9800_SorSkillStaticMin` | (combat name) do 20 | I |
| `0x005C98F0` | `sub_005C98F0_SkillDo21Telekinesis` | do 21 | I |
| `0x005C9B50` | `sub_005C9B50_SkillDo22NovaAtSelf` | (P1.3 name) do 22 | I |
| `0x005C9C10` | `sub_005C9C10_SkillDo23TimedState` | do 23 | I |
| `0x005C9EA0` | `sub_005C9EA0_SkillDo24FireWall` | do 24 | I |
| `0x005CA030` | `sub_005CA030_SkillDo25Enchant` | do 25 | I |
| `0x005CA1B0` | `sub_005CA1B0_SkillDo26ChainLightning` | do 26 | I |
| `0x005CA360` | `sub_005CA360_SkillTeleportDo` | (P1.1 name) do 27 | I |
| `0x005CA3E0` | `sub_005CA3E0_SkillDo28MissileAtTarget` | (P1.3 name) do 28 | I |
| `0x005CA4D0` | `sub_005CA4D0_SkillDo29ThunderStorm` | do 29 | I |
| `0x005CA910` | `sub_005CA910_SkillDo144Hydra` | do 144 | I |
| `0x005C8CA0` | `sub_005C8CA0_InfernoCreate` | `(ECX game, EDX unit; id, lvl, cls)`, `ret 0xC`: the creation, or the end of the cast (§ 3) | I |
| `0x005C8E30` | `sub_005C8E30_InfernoStart` | `(ECX game, EDX unit; id, lvl, cls)`, `ret 0xC`: state 12's list (§ 3) | I |
| `0x005C8C10` | `sub_005C8C10_InfernoEndMonster` | `(ESI unit, EDI game)`: `STATE_Set(unit, 12, 0)`, `UNIT_CancelEvents(0, 0)`, event 1 at `frame +` MonStats2 `+0x108` (1 without a record) (§ 3; read only) | I |
| `0x005C8BF0` | `sub_005C8BF0_InfernoRemoveCb` | state 12's remove callback: `STATE_Set(unit, state, 0)`, bit 6 of `+0xC4` | I |
| `0x005C8BC0` | `sub_005C8BC0_SkillGetParam7` | `(ECX id)` → Skills `+0x160` (`Param7`), 0 without a record | I |
| `0x005CA470` | `sub_005CA470_StormStrikeAt` | `(EDI caster, ESI unit; game, cls, id, lvl)`: both out of town, `MissileCreateAt` at the unit (§ 5; read only) | I |
| `0x005C96A0` | `sub_005C96A0_StaticFieldCb` | do 20's per-unit callback (after its boundary; not read past its first tests) | I |
| `0x005C9420` | `sub_005C9420_SkillDo18RemoveCb` | do 18's state remove callback (read only) | I |
| `0x00663270` | `sub_00663270_MissileSpeedAtLevel` | `(cls, lvl)` → `VelLev·lvl / 8 + Vel` from the table at `0x0096C794` (§ 7) | I |
| `0x00644560` | `sub_00644560_UnitSkillSet18` | `(node, v)`: node `+0x18 = v` (assertion on null) | I |
| `0x006445A0` | `sub_006445A0_UnitSkillSet1C` | `(node, v)`: node `+0x1C = v` (assertion on null) | I |
| `0x006444D0` | `sub_006444D0_UnitSkillGet1C` | `(node)` → node `+0x1C` (assertion on null) | I |

## Walkthrough

### 1. The table slots and the shared shape

- [C] `g_SkillStartFuncs[11..14]` and `g_SkillDoFuncs[17..29, 144]` are the Functions table's addresses (17 entries
  compared, `table_entries=17`). (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [I] Each function starts with `0 ≤ id < DataTables+0xBA0` and the Skills record `DataTables+0xB98 + 0x23C · id`,
  and returns 0 without it; the missile classes they read (`srvmissilea` `+0x48` and the others, s16) are tested
  against the Missiles count `DataTables+0xB6C`, `aurastate` (`+0x80`, s16) against the States count
  `DataTables+0xC4`, `aurastat1` (`+0x54`) against the ItemStatCost count `DataTables+0xBD4`.
  (fn:sub_005C8FA0_SkillSt11Inferno@0x005C8FA0, fn:sub_005CA4D0_SkillDo29ThunderStorm@0x005CA4D0)
- [I] **Stock rows** (`rows.txt`): start 11 on 41 Inferno and 230 Arctic Blast (`startmana` 6, `calc2` 20); start 12
  on 43 Telekinesis (`Param2` 35) and 275 Dragon Flight; start 13 and do 29 on 57 Thunder Storm (`aurastate`
  `thunderstorm`, `Param7` 17); start 14 and do 144 on 62 Hydra (`summon` 351 `hydra1`, `pettype` `hydra`, `summode`
  S2, `petmax` 99, `Param1` 250, `Param2` 0); do 17 on 38 Charged Bolt and three monster bolts; do 18 on the eleven
  armour rows (skills/0003 § 5); do 19 on 41 and 230; do 20 on 42 Static Field (`aurafilter` 34 691); do 21 on 43;
  do 22 on 44, 48 and seven monster or other-class rows; do 23 on 46 Blaze, 58 Energy Shield, 173, 187; do 24 on 51
  Fire Wall (`srvmissilea` 68 `firewallmaker`, `srvmissileb` 69 `firewall`) and three monster rows; do 25 on 52
  Enchant (`aurastat1` `firemindam`); do 26 on 53 Chain Lightning; do 27 on 54 Teleport; do 28 on 56 Meteor, 59
  Blizzard and ten monster rows. No stock row of the batch sets the `progressive` bit. (`rows.txt`,
  tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc)

### 2. Emulation: the `sor` families

The method is 9d's (skills/0007 § 2) with the skill functions' calling shape: each case calls the function with
`ECX` = the game, `EDX` = the caster and the stack `(id, lvl)` (the two Inferno helpers are called directly with
`(id, lvl, cls)`), and dumps the caster's and the target's seeds, the caster's `+0xC4` and the second argument's
slot. Emulated, not observed: `UNIT_GetTargetUnit` with `sub_00553490_PathTargetRevalidate` (hash lookup, stale
targets and picked-up items dropped), `SKILLS_GetTargetXY`, `UnitGetRoom`, `RoomIsTown`, `sub_00463740_RoomAtSubtile`
with `DUNGEON_GetNearRooms`, `UNIT_HasState`, `UNIT_FindStatListByState`, the stat-list reads, `STATS_GetUnitStat`,
`SKILLS_EvalCalc` on constant programs, `SKILLS_GetUnitSkill`, `UNIT_GetUsedSkill`, `SKILLS_GetElemLen`,
`sub_00611D30_DifficultyRec`, `sub_005D3CF0_SkillSrvMissileByCharge`, `0x00663270`, `sub_0056D400_SkillNovaAtUnit`
and `sub_0056E450_SkillTargetCellFree` up to their boundary, `sub_00535060_PlayerIsBusy`, `sub_0063EA70_SkillSummonRec`,
`sub_0063EE90_HirelingType`, `sub_0058F0D0_MonsterOwner`, and `sub_00554200_UnitsHostile` and
`sub_00554DE0_UnitsSameParty` with the alignment rule `0x00650D70` / `0x006259B0` (state 105's list, stat 172).
Observed (new for this batch): `0x005C8E30`, `0x005C8CA0` (from start 11 and do 19), `0x00553C70`,
`UNIT_CancelEvents`, `0x005C8C10`, `STATE_ApplyTimed`, `STATE_GroupClear`, `sub_0055B300_PlayerPairFlags`,
`COLL_WHTest`, `sub_0056ECB0_SkillMissileCreate`, `sub_0056D940_SpawnOwnedMonster`, `sub_0056E170_SkillRollPhys`,
`OBJ_OperateDispatch`, `ITEMS_UnitIsType`, `sub_00540710_PartyIdOfUnit`; 9d's stay declared (`MissileCreate`,
`STATLIST_Alloc`, `NearestUnitInRange`, `SKILLS_ForUnitsInRange`, …).

- [C] Six families, **8 500 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 2 977 matched boundary cases
  (27 function, boundary and return-address triples, each a `site` line) (`check.txt`; run:2026-10-20-cat-emu-sor):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `start_sor` | start 11, 12, 13, 14; do 19 | 1 500 | state 12 ignored (8); mana `≤` (25); first skill node wins (34); start 14 on the caster's room (6); range `≥` (9); start 14's result inverted (138) | Inf8E30 @0x005C9019; Inf8CA0 @0x005C9685; PairFlags @0x00554297 (in `UnitsHostile`); returns 0, 1 |
  | `inferno_sor` | `0x005C8CA0`, `0x005C8E30` | 1 200 | calc2 not floored (105); `+0x18` test inverted (141) | MissileCreate @0x005C8D8D; Sub553C70 @0x005C8DAC, @0x005C8F51; Inf8C10 @0x005C8E14; CancelEvents @0x005C8DE8; StatListAlloc @0x005C8EE2; returns 0 |
  | `create_sor` | do 17, 20, 22, 24, 26, 28 | 1 800 | `StaticFieldMin` without the expansion test (75); `srvmissilea` always (17); index 1 (68); the level in the slot (170) | MissileCreate @0x005C9400, @0x0056D4CC (in NovaAtUnit); WHTest @0x0056E4EF (in TargetCellFree, do 24 and 28); SkillMissileCreate @0x005CA230; ForUnitsInRange @0x005C98E2; returns 0, 1 |
  | `state_sor` | do 18, 23, 25, 29 | 1 600 | `aurastat1 ≥ 0` (79); any target (60); `+0x1C` ignored (14) | GroupClear @0x005C94F9; ApplyTimed @0x005C9CD4, @0x005CA11E, @0x005CA672; PartyId @0x00554E4C, @0x00554E6F (in `UnitsSameParty`); NearestUnit @0x005CA5AA; returns 0 |
  | `tk_sor` | do 21 | 1 200 | stun on `≤` (23); the draw on the target's seed (93) | RollPhys @0x005C9A0B; ObjOperate @0x005C9B18; ItemIsType @0x005C9A8C; PairFlags @0x00554297; returns 0, 1 |
  | `hydra_sor` | do 144 | 1 200 | no hireling swap (33); `lvl · Param2` (195) | SpawnOwned @0x005CAAA1; returns 0 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 35 of 35 pins): the hash offsets, the `CALC_Eval` jump
  table and the skills calc function count, `g_BitMask32`, the town tables (as 9a–9d), and new: NovaAtUnit's 64
  offsets (`0x006E1288` x / `0x006E1388` y, `.rdata`; the first `(30, 0)`), do 144's offsets (`0x006E312C` x `−1 0 1`,
  `0x006E3120` y `−1 0 −1`, `.rdata`) and do 21's jump table (`0x005C9B34`, `.text`: types 0 and 1 `0x005C9985`, 2
  `0x005C9B05`, 3 `0x005C9B18`, 4 `0x005C9A84`). Skills, Missiles, ItemStatCost, the stat lists, rooms, levels and
  units are scratch records written one field per field read.
- [C] **Inputs set in the memory spec** (ADR-0015, S1e review ruling 3): `g_pDataTables`, the missile table pointer
  and count `0x0096C794`/`0x0096C79C` that `0x00663270` reads, and `g_pDifficultyLevels`/`g_nDifficultyLevels`
  (`0x0096C8AC`/`0x0096C8B0`) are inputs of the claims, pointed at scratch tables: inputs set on purpose, which the
  S1e ruling 3 admits with no justification beyond the claim's own domain (the claims are maps from those tables'
  bytes, not statements of what the game stores there). The kept writer scan (`static.txt`) is no justification: it
  matches only `PTR`-form stores and misses the `mov ds:moffs, eax` form and addresses passed as out-parameters
  (architect review of `lane/p46m5`). The security cookie is written as in 9a.
- [I] Those globals are written at load (from the reading; objdump, architect review): `0x0096C794` takes
  `DATATBLS_LoadTable`'s result for the file `missiles` with record size `0x1A4` (`0x0066312C`, stored at
  `0x00663139`; the count through the pointer `0x0096C79C` pushed at `0x00663115`; `0x0096C798` beside it at
  `0x0066311A`), and is zeroed with its count at the table free (`0x0066325F`); `g_pDifficultyLevels` takes
  `DATATBLS_LoadTable`'s result at `0x006180C5`, its count through the pointer pushed at `0x00617FF8`.
  (fn:DATATBLS_LoadTable@0x006122F0, 0x00663139, 0x006180C5)
- [C] The weak controls each decide their claim deterministically: `nostate` (8) on the cases with state 12 on and
  mana below `startmana`; `town14` (6) on a caster's room and point room of different town status; `dist_ge` (9) on
  the cases exactly at `r²` (the writer places 45 % of the near targets at `r` or one off); `ign1c` (14) on the
  stormed casters with `+0x1C ≠ 0`; `charge_a` (17) on the `progressive` cases with a charge of 2 or more; each family
  has a control of 79 or more beside them (reverser review-fixes 10; ruling 2 of the `lane/p46m3` review).
  (run:2026-10-20-cat-emu-sor)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills and
  Missiles columns `[C]` by layout; unit and path offsets `[I]`, skills/0001, skills/0004 § 9), and nothing here says
  when the game runs these functions or on which seed state. (run:2026-10-20-cat-emu-sor)

### 3. Inferno and Arctic Blast: start 11, do 19, `0x005C8E30`, `0x005C8CA0`

```c
// fn:sub_005C8FA0_SkillSt11Inferno@0x005C8FA0, trimmed
if (!rec) return 0;
if (!UNIT_HasState(unit, 12) && STATS_GetUnitStat(unit, 8, 0) < rec->startmana << 8) return 0;
if (rec->srvmissilea < 0 || rec->srvmissilea >= nMissiles) return 0;
return InfernoStart(game, unit; id, lvl, rec->srvmissilea);          // 0x005C8E30; do 19 calls InfernoCreate
```

- [C] (ADR-0021; ends at `0x005C8E30` @0x005C9019) **Start 11** as above: the mana test (`movsx`, `shl 8`, signed
  `jl`) is skipped while `UNIT_HasState(unit, 12)` (a unit of type 0, 1 or 3 with the state bit); the class test is
  signed. (run:2026-10-20-cat-emu-sor `start_sor`, tbl:Skills.txt:startmana, tbl:Skills.txt:srvmissilea)
- [C] (ADR-0021; ends at `0x005C8CA0` @0x005C9685) **Do 19**: the record and the class test, then `0x005C8CA0(id, lvl,
  srvmissilea)`. (fn:sub_005C9640_SkillDo19Inferno@0x005C9640)
- [C] (ADR-0021; ends at `MissileCreate` @0x005C8D8D, `0x00553C70` @0x005C8DAC, `0x005C8C10` @0x005C8E14 or
  `UNIT_CancelEvents` @0x005C8DE8) **`0x005C8CA0`**: without a record, the class out of range, a target point
  (`SKILLS_GetTargetXY`: the target unit's position, else the path's target point; both non-zero) or a used skill
  (`UNIT_GetUsedSkill`: the skill list `+0xA8`, its `+0x10`), 0. With the node's `+0x18 ≠ 0`: block `{flags 0x8020,
  owner unit, source unit, cls, target (x, y), skill, lvl, +0x4C = max(calc1, 1)}` (x and y left 0). With `+0x18 ==
  0`: `+0x18 = 1`; a non-monster goes to `0x00553C70(game, unit; 1)`; a monster gets `+0x44 = 0xB00`, then
  `0x005C8C10` while `frame ≥ 1` (signed), else `UNIT_CancelEvents(1, 0)` when it has state 12 and `0x005C8C10`
  when not. After, `[I]`: on the creating path, `+0x18 = 1` and the same end branches; returns 1.
  (run:2026-10-20-cat-emu-sor `inferno_sor`, fn:sub_005C8CA0_InfernoCreate@0x005C8CA0)
- [C] (ADR-0021; ends at `STATLIST_Alloc` @0x005C8EE2 or `0x00553C70` @0x005C8F51) **`0x005C8E30`**: for a monster
  caster (type 1) the used skill's `+0x18 = frame + max(calc2, 1)` (stock 20: the monster's flame lasts 20 frames);
  then, without a state-12 list on the caster, `STATLIST_Alloc(game+0x1C, 2, frame + 0x14, type, guid)`, else
  `0x00553C70(1)`. After, `[I]`: the new list queues event 12 at `frame + 0x14`, is linked with the remove callback
  `0x005C8BF0` and state 12 set, the used skill's `+0x18 = 0`; with a list, its end becomes `frame + 6`, event 12 is
  queued there and `0x005C8CA0` runs; returns 1. (run:2026-10-20-cat-emu-sor `inferno_sor`,
  fn:sub_005C8E30_InfernoStart@0x005C8E30, tbl:Skills.txt:calc2)
- [I] So a player's Inferno holds state 12 for its channel: the first start allocates the list (20 frames); each later
  start (the `repeat` row restarts the skill) extends it to `frame + 6` and creates; `+0x18` of the used skill is the
  "create" switch the do function reads. Whether the do or the start creates on a given frame is the dispatch's
  (skills/0001 § 9), not read here. (0x005C8EB7–0x005C8F94)

### 4. Start 12 and do 21: Telekinesis and Dragon Flight

- [C] **Start 12** (`0x005C9030`): `t = UNIT_GetTargetUnit(game, unit)` (none → 0), the record (none → 0), `r =
  aurarangecalc`, then `DistSq(unit, t) = (tx − ux)² + (ty − uy)²` (32-bit `imul`; types 2, 4 and 5 give the static
  path's `+0x0C`/`+0x10`, others their path's position, 0 without a path) `> r · r` (signed `jg`) → 0; a target of
  type above 1 (unsigned `ja`: object, missile, item, tile) → 1; else `UnitsHostile(game, unit; t)` 0 → 0, a town room
  for the target or the caster → 0, else 1. (run:2026-10-20-cat-emu-sor `start_sor`, fn:sub_006492A0_DistSq@0x006492A0,
  tbl:Skills.txt:aurarangecalc)
- [C] (emulated inside start 12 and do 21; ends at `PlayerPairFlags` @0x00554297 for two players)
  **`UnitsHostile(game, a; b)`**: `a` a monster with an owner (`MonsterData+0x28` → a link `{+0x28 game, +0x2C guid,
  +0x30 type}` found by `GameFindUnit`) is replaced by it; `b` by its owner while it is a monster with one; the same
  unit → 0; two players → `PlayerPairFlags(a, b; 8)`; else 1 unless `0x00650D70` calls them allied: both alignments 0
  or both 2, where a unit's alignment (`0x006259B0`) is 0 without a stat list, 2 for a type above 1, else the stat
  172 of its state-105 list (0 without one). (run:2026-10-20-cat-emu-sor `start_sor`, `tk_sor`,
  fn:sub_00554200_UnitsHostile@0x00554200)
  Not exercised, so outside the `[C]`: `a` a missile with bit 10 of `+0xC8` is replaced by the unit `GameFindUnit`
  finds from its `+0x94`/`+0x98` (its owner, from the reading; 0x0055421C–0x00554245).
- [I] By that rule a player and a monster that carry no state-105 list are both alignment 0 and **not** hostile;
  which units carry the list in play is not read here (Open questions). (0x00650D70–0x00650DC8, 0x006259B0)
- [C] **Do 21** (`0x005C98F0`): the record; a caster that is not a player (type 0), or `PlayerIsBusy` (the unit's
  `+0x6C` byte, a cursor item in an inventory `+0x60` whose `+0x00` is `0x01020304`, or the player data's `+0x4C`),
  or without a target unit → 0. Then bit 6 of `+0xC4` and by the target's type: above 4 or 3 → 1; 2 →
  `OBJ_OperateDispatch(game, unit; 2, guid, &local)` (ADR-0021, @0x005C9B18); 4 → `ITEMS_UnitIsType(item, 0x16)`
  (ADR-0021, @0x005C9A8C); 0 or 1 → `UnitsHostile` (0 → 0), a town room for the target or the caster → 0, then
  `RNG_Range(caster+0x20, 100)`, stun flag `[ebp−8] = draw < Param2` (signed `jge`), and (ADR-0021, @0x005C9A0B)
  `SkillRollPhys(ECX caster, EDX packet; id, lvl)` with the 0x70-byte packet zeroed; the caster's seed at the boundary
  is the state after the one draw, the target's unchanged. After, `[I]`: `SKILLS_RollElemDamage`, the packet's result
  `|= ResultFlags`, flags `|= HitFlags`, `HitClass` when non-zero, result `|= 9` when stunned, `COMBAT_ApplyDamage(t,
  1, packet)`, `COMBAT_GetHit(t, packet)`; returns 1. The item branch, after its first type test: types 4, 0x26, 0x38,
  9, 0x29 too, then `UnitSetEvent(unit, 0x13)` for none of them or `0x00563560` (a pick-up to the cursor) for one;
  returns 1. (run:2026-10-20-cat-emu-sor `tk_sor`, fn:sub_005C98F0_SkillDo21Telekinesis@0x005C98F0,
  tbl:Skills.txt:Param2, tbl:Skills.txt:ResultFlags)
- [I] Stock: Telekinesis `Param2` 35, so a 35 % stun (draw 0–34 of 100) on a hit actor. Dragon Flight (275) shares
  start 12 only. (`rows.txt`, tbl:Skills.txt:Param2)

### 5. Thunder Storm: start 13 and do 29

- [C] **Start 13** (`0x005C91C0`): the record; `node = SKILLS_GetUnitSkill(unit, id)` (skills/0007 § 9's rule), none →
  0; `node+0x18 = −1`, `node+0x1C = 1`; returns 1. (run:2026-10-20-cat-emu-sor `start_sor`,
  fn:sub_005C91C0_SkillSt13StormArm@0x005C91C0, fn:SKILLS_GetUnitSkill@0x006439F0)
- [C] (ADR-0021; ends at `STATE_ApplyTimed` @0x005CA672 or `NearestUnitInRange` @0x005CA5AA) **Do 29**: the record,
  `srvmissilea` and `aurastate` in range, a unit skill node (else 0). When `UNIT_HasState(caster, aurastate)` and
  `node+0x1C == 0`: `NearestUnitInRange(game, caster; 0, 0, Param7, 3, node+0x18, 0)`; else the block `{caster,
  caster, id, lvl, auralencalc, −1, 0, aurastate, 0}` to `STATE_ApplyTimed`. After, `[I]`: on the state path, stats
  350/351 = id and level on the list, then `node+0x1C = 0`; on the search path, with a unit `0x005CA470` (both rooms
  out of town, `MissileCreateAt(game, caster; id, lvl, srvmissilea, the unit's position)`), and with a missile
  `MISSILE_HitUnit(missile, unit, 1)`, `UnitFree(missile)`, `0x00571AA0`, then `node+0x18` = the unit's guid; without
  a unit `node+0x18 = −1`; then `node+0x1C = 0`; returns 1. (run:2026-10-20-cat-emu-sor `state_sor`,
  fn:sub_005CA4D0_SkillDo29ThunderStorm@0x005CA4D0, tbl:Skills.txt:Param7, tbl:Skills.txt:auralencalc)
- [I] So the cast (start 13 sets `+0x1C`) puts the state on, and each later run of do 29 under the state strikes the
  nearest unit within `Param7` (stock 17) other than the last one struck, recording it. Who runs do 29 again while
  the state lasts is not read (the state's events or the periodic queue, skills/0001 § 9).
  (fn:sub_005CA4D0_SkillDo29ThunderStorm@0x005CA4D0)

### 6. Hydra: start 14 and do 144

- [C] **Start 14** (`0x005C9220`): the caster's room (`UnitGetRoom`; none → 0), the target point (0 → 0), `r =
  RoomAtSubtile(room, x; y)` — the room itself when `x0 ≤ x < x0 + w` and `y0 ≤ y < y0 + h` (signed; room `+0x4C`,
  `+0x50`, `+0x54`, `+0x58`), else the first of its near rooms (`+0x00` array, `+0x24` count) that holds the point, else
  0 → 0; then `!RoomIsTown(r)`. (run:2026-10-20-cat-emu-sor `start_sor`, fn:sub_00463740_RoomAtSubtile@0x00463740)
- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005CAAA1) **Do 144**: the record; `summon = SkillSummonRec(caster, 0;
  id, lvl, &mode, 0, 0)` (the Skills path: `summon` `+0xBC` in the MonStats count, `mode` = `summode` `+0xBF` as s8 when
  0..15, else 1); `pettype` (`+0xBE`, s8) below 0 or at the PetType count → 0; start 14's room tests → 0; the owner is
  the caster, or a hireling caster's owner (a monster of class 271, 338, 359, 560 or 561 with an owner found);
  then the first block `{+0x00 1, +0x04 owner, +0x08 summon, +0x0C 0, +0x10 mode, +0x14 x − 1, +0x18 y − 1, +0x1C
  pettype, +0x20 petmax (calc, the owner's), +0x24 frame + (lvl > 0 ? Param1 + (lvl − 1)·Param2 : 0)}`. After, `[I]`:
  for each spawn `UnitSkillAdd(lvl, 1)`, `SummonInitStats`, the end frame written to `+0x14` of its monster data's
  `+0x28` record (`0x005B0D70`), and for a monster owner its alignment set on the spawn; the next two blocks with class `summon + i` and offsets `(0, 0)`, `(+1, −1)`;
  returns 1 when any spawned. (run:2026-10-20-cat-emu-sor `hydra_sor`, fn:sub_005CA910_SkillDo144Hydra@0x005CA910,
  fn:sub_0063EA70_SkillSummonRec@0x0063EA70, tbl:Skills.txt:summon, tbl:Skills.txt:pettype, tbl:Skills.txt:petmax)
- [I] Stock: Hydra (62) summons classes 351–353 (`hydra1`–`hydra3`, one each) for 250 frames at every level
  (`Param2` 0). A caster whose `summon` is out of range takes `0x0058F710`, which reads `[0 + 0x3C]` for a non-monster
  (a fault); no stock row reaches it. (`rows.txt`, 0x0056E653–0x0056E66C, 0x0058F727)

### 7. Creations: do 17, 22, 24, 26, 28 and do 20

- [C] **`SkillSrvMissileByCharge`** (emulated inside do 17 and 22): `srvmissilea`, except for a row with the
  `progressive` bit (`+0x04` bit 2), `aurastate` and `aurastat1` in range and a caster list of that state whose base
  `aurastat1` is 2 (`srvmissileb`) or 3 and more (`srvmissilec`). (run:2026-10-20-cat-emu-sor `create_sor`,
  fn:sub_005D3CF0_SkillSrvMissileByCharge@0x005D3CF0, tbl:Skills.txt:progressive)
- [C] (ADR-0021; ends at `MissileCreate` @0x005C9400) **Do 17**: bit 6 of `+0xC4` first (before the record test);
  the class; `n = calc1`; block `{flags 0x21, owner caster, cls, x, y = the caster's position, skill, lvl, +0x54
  callback 0x005C9290, +0x58 0}` with the target point in `+0x1C`/`+0x20`; no creation and 1 when `n ≤ 0` or the point
  is not set. After, `[I]`: `n` creations, `+0x58` the index; the callback re-seeds each bolt from its path x plus the
  index (skills/0003 § 9); returns 1. (fn:sub_005C9300_SkillDo17ChargedBolt@0x005C9300, tbl:Skills.txt:calc1)
- [C] (ADR-0021; ends at `MissileCreate` @0x0056D4CC inside `sub_0056D400_SkillNovaAtUnit`) **Do 22** (tier A): bit 6
  first; the class; `vel = 0x00663270(cls, lvl) + calc1`, where `0x00663270` is `VelLev · lvl / 8` (signed, truncating:
  `cdq; and 7; sar 3`) `+ Vel` of the record in the table at `0x0096C794` (Missiles `+0x9A`, `+0x9B`, both read as
  unsigned bytes, `movzx`), 0 out of
  range; `NovaAtUnit(game, caster; caster, cls, id, lvl, vel)`'s first block `{flags 3, or 7 when vel ≠ 0, owner
  caster, cls, the caster's position, target (30, 0), +0x28 vel, skill, lvl}`. After, `[I]`: 63 more creations over
  the offsets of `0x006E1288`/`0x006E1388`; returns 1. (fn:sub_005C9B50_SkillDo22NovaAtSelf@0x005C9B50,
  fn:sub_00663270_MissileSpeedAtLevel@0x00663270, tbl:Missiles.txt:Vel, tbl:Missiles.txt:VelLev)
- [C] (ADR-0021; ends at `COLL_WHTest` @0x0056E4EF inside `sub_0056E450_SkillTargetCellFree`) **Do 24** (no bit 6)
  and **do 28** (tier A; bit 6 after the class test): `srvmissilea` in range; with a caster room and a target point
  with both coordinates non-zero, `COLL_WHTest(room, x, y, Size, Size, 5)` (Missiles `Size`, `+0x18A` u8); else 0.
  After, `[I]`: do 28 `MissileCreateAt` at the point when the cell is free (skills/0003 § 5); do 24: the point is the
  target unit's position or the path's target point, the room at it (no null test) must not be a town, then two
  `srvmissilea` creations `{flags 0x21, owner, cls, the point}` with targets perpendicular to the caster–point line,
  `(px − (uy − py), py + (ux − px))` and `(px + (uy − py), py − (ux − px))`, and a third, `srvmissileb` at the point
  (flags 1), when in range; returns 1. (fn:sub_005C9EA0_SkillDo24FireWall@0x005C9EA0,
  fn:sub_005CA3E0_SkillDo28MissileAtTarget@0x005CA3E0, tbl:Missiles.txt:Size)
- [C] (ADR-0021; ends at `SkillMissileCreate` @0x005CA230) **Do 26**: `srvmissilea` in range, bit 6, `c = calc1` kept
  in the second argument's slot, `SkillMissileCreate(ECX game, EDX srvmissilea; caster, id, lvl, 0, 0, 0, 0, 0)`.
  After, `[I]`: with a missile, `MISSDATA_SetSeedLow(missile, c)`, the word chain lightning's missile functions read
  as its count; returns 1. (fn:sub_005CA1B0_SkillDo26ChainLightning@0x005CA1B0)
- [C] (ADR-0021; ends at `SKILLS_ForUnitsInRange` @0x005C98E2) **Do 20** (tier A): the record; `d =
  DifficultyRec(game+0x6D)` (`max(byte, 0)` capped at the table count − 1); the block `{calc2, calc1, d+0x40 when
  game+0x70 ≠ 0 else 0, SKILLS_GetElemLen(caster, id, lvl, 1), EType}` (20 bytes, compared) and
  `ForUnitsInRange(game, caster; 0, 0, aurarangecalc, aurafilter, 0x005C96A0, &block, 0, file, 0x273)`. That
  `d+0x40` is `StaticFieldMin` and `game+0x70` the expansion flag is combat/0001's reading (`[I]`). After, `[I]`: the
  callback per unit. (fn:sub_005C9800_SorSkillStaticMin@0x005C9800, fn:sub_00611D30_DifficultyRec@0x00611D30)

### 8. Timed states: do 18, 23, 25

- [C] (ADR-0021; ends at `STATE_GroupClear` @0x005C94F9) **Do 18** (tier A): the record and `aurastate` (s16) in
  range, then bit 6 and `STATE_GroupClear(ECX caster, EDX aurastate; 1)`. After, `[I]`: the block with callback
  `0x005C9420` (skills/0003 § 5). (fn:sub_005C9480_SkillDo18TimedSelfState@0x005C9480)
- [C] (ADR-0021; ends at `STATE_ApplyTimed` @0x005C9CD4) **Do 23**: `aurastat1` from −1 (a blank cell) to below the
  ItemStatCost count (`cmp ax, 0xffff; jl`, signed 16-bit), `aurastate` in range; the block at ECX `{caster, caster, id,
  lvl, auralencalc, −1, 0, aurastate, 0}` (no bit 6, no group clear). After, `[I]`: the passive stats (`0x005C6DC0`),
  stats 350/351, the `auraevent`s; returns 1, or 0 without a list. (fn:sub_005C9C10_SkillDo23TimedState@0x005C9C10)
- [C] (ADR-0021; ends at `STATE_ApplyTimed` @0x005CA11E, or `PartyIdOfUnit` @0x00554E4C/@0x00554E6F for two players
  with a party word `+0x80`) **Do 25**: the tests of do 23; the unit is the target when `UNIT_GetTargetUnit` gives
  one and `UnitsSameParty(game, caster; t)` (owners resolved as in `UnitsHostile`; the same unit 1; two players by
  their party ids, 0 when neither has a `+0x80` word; else the alignment rule's allied), else the caster; the block
  `{caster, unit, id, lvl, auralencalc, −1, 0, aurastate, 0}`. After, `[I]`: each `aurastat1..6` in range with a
  non-zero calc set on the list, the state bit on the unit; returns 1. (fn:sub_005CA030_SkillDo25Enchant@0x005CA030,
  fn:sub_00554DE0_UnitsSameParty@0x00554DE0)

### 9. Do 27: Teleport (tier A, not emulated)

- [I] `sub_005CA360_SkillTeleportDo`: the target point, the caster's room's level `Teleport` byte (`LEVELS_GetRecord`
  `+0x04`; 0 → 0), for 2 a line test `0x006229F0(caster, x, y, 0x804)` that refuses, then `UnitTeleport(game, caster;
  0, x, y, 0, 0)` as drlg/0009 § 11 reads it, whose value it returns; no room or no Levels record also gives 0. Not
  emulated: its first test needs `LEVELS_GetRecord` and its call
  `UnitTeleport`, whose room search is the route; the ending call would be its only claim. (0x005CA360–0x005CA3DD,
  tbl:Levels.txt:Teleport)

## Corrections to earlier findings

- skills/0003 § 5 (tier A), carried there as a dated note: do 18, 20, 22 and 28 are now `[C]` up to their boundaries
  (ADR-0021), and two details are added: do 20's `StaticFieldMin` term is 0 outside an expansion game (`game+0x70`),
  and do 22's velocity is `0x00663270(cls, lvl)` (Missiles `Vel` + `VelLev · lvl / 8`) plus calc1.
- The Skills table doc's `startmana` row says a **player** is refused below `startmana · 256` unless in state 12
  (`SKILLS_CanUse`); start 11 makes the same test for any caster (§ 3). Sent to the archivist with the column readers.

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `progressive`, `srvmissilea`, `srvmissileb`, `srvmissilec`, `aurastate`,
`aurastat1`, `auralencalc`, `aurarangecalc`, `aurafilter`, `startmana`, `calc1`, `calc2`, `Param2`, `Param7`,
`Param1`, `summon`, `pettype`, `summode`, `petmax`, `EType`, `ELen`, `ELevLen1`..`3`, `ELenSymPerCalc`;
`tbl:Missiles.txt:Vel`, `VelLev`, `Size`; `tbl:Levels.txt:Teleport` (do 27, read only); ItemStatCost 8, 172; unit
`+0x00`, `+0x04`, `+0x0C`, `+0x10`, `+0x14` (monster data `+0x28` owner link; player data `+0x4C`), `+0x20` seed,
`+0x2C` path (`+0x02`, `+0x06` position; `+0x10`, `+0x12` target point; `+0x1C` room; `+0x58`–`+0x60` target link;
static path `+0x00` room, `+0x0C`, `+0x10`), `+0x44`, `+0x5C` stat list, `+0x60` inventory, `+0x64`–`+0x6C`,
`+0x80`, `+0xA8` skill list (`+0x04` first node, `+0x10` used), `+0xC4` bit 6; unit skill node `+0x00`, `+0x04`,
`+0x18`, `+0x1C`, `+0x28`, `+0x34`, `+0x3C`; room `+0x00`, `+0x10`, `+0x24`, `+0x4C`–`+0x58`; `struct:Game+0x1C`,
`+0x6D`, `+0x70`, `+0xA8`.

## Dead ends

- The first `start_sor` and `tk_sor` checks failed on the model's own tuple (the `PlayerPairFlags` registers taken
  from the wrong slot); the first `state_sor` run observed `UnitsSameParty` (9c declares it a boundary), so the batch
  removes it from its list and runs it emulated; the first `create_sor` check could not read do 26's slot (the stack
  dump stops at the entry ESP; the batch dumps `0x7FF00008`). Three first controls failed no case (`dist_ge`,
  `stun_le`, `charge_a`): the writer now places targets at `r`, draws at `Param2` and charged lists on purpose.

## Open questions

- [L] Which units carry a state-105 list with stat 172 in play: without one a player and a monster are both
  alignment 0, which `UnitsHostile` calls not hostile (§ 4), so Telekinesis and Dragon Flight would refuse them.
- [L] What `0x00553C70(game, unit; 1)` does (the end of an Inferno cast and the restart branch) and what `0x005C8C10`'s
  mode event is; which frames run do 19 against start 11 for a channelled skill.
- [L] Whether the second load of `missiles` at `0x0096C794` (§ 2, freed at `0x00663240`) holds the same records as
  `DataTables+0xB64` at run time.
- [L] Everything after each boundary (§§ 3–8), for a later batch or the harness.
