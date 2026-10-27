# 0013 — Catalogue batch `dru`: the druid start functions 56–58, do functions 114–124 and do-table entries 145 and 146

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 56, 57 and 58 (`srvstfunc`, `g_SkillStartFuncs`), do function
> 114–124 (`srvdofunc`, `g_SkillDoFuncs`) and do-table entry 145 and 146 (the States `srvactivefunc` of rows 144
> `hurricane` and 145 `armageddon`) of the druid batch do: which Skills and unit fields it reads, which states,
> summons, missiles and hits it makes, which draws it makes on which seed, what it returns, and which of that the
> emulator can confirm?
> **Date:** 2026-10-21   **Plan:** 0046 (Phase 1, batch `dru`)   **Status:** for review (`lane/p46m10`)

Static reading of the pinned `Game.exe` with objdump (and the lane's Ghidra copy `workspace/ghidra-p46m10` for the
emulation), then emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged, `286393aa…`) and the
`dru` families of `tools/skills_catalogue_emu.py` (§ 2; run:2026-10-21-cat-emu-dru in [experiments](experiments.md)).
Skills columns are named as in [Skills](../../tables/Skills.md). The machinery that calls a start or do function is
[skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart); the two tier-A entries of this
batch (do 114 Raven, do 117 Firestorm) were read by plan 0045 in [skills/0003 §§ 5, 7](0003-handlers.md#7-summons),
and both are emulated here. Entries 145 and 146 run from unit event 5 through `sub_0056D790_StateDoFunc`
([skills/0001 § Functions](0001-dispatch.md); the States machinery of [stats/0002](../stats/0002-states.md) and
[stats/states](../../specs/stats/states.md)), which this batch reads only as far as their arguments (§ 1). Stock values
come from `workspace/logs/skills-cat-dru/rows.txt` (`excel_bin.py dump` of the 25 Skills rows whose `srvstfunc` or
`srvdofunc` is one of the batch's, or whose `aurastate` names a state with `srvactivefunc` 145 or 146, by `rows.sh`
beside it).

**Tag convention for this finding** (as skills/0012). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a
function entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site
(the return address at ESP), with a site control that fails every matched boundary case, and where the boundary sits
inside a helper the batch function called, the helper's return address into the batch function is compared at its
absolute stack slot (ruling 1 of the `lane/p46m6` review, at each level of a helper chain; § 2 lists each compared
slot); (c) the model gives and the checker compares every argument the claim uses (registers the callee reads before
it writes them, stack words, and for a pointer the bytes it points to), every byte written before the call that the
claim uses (the caster's `+0xC4`, the used node's `+0x18`, frame and argument-slot words), and the state of **the
caster's and the target's seeds** at the boundary (both, in every case). Each such claim names the boundary it ends
at; **the callee and all code after it are not covered** and keep `[I]` (from the reading), marked "after, `[I]`" in
place, and what a callee makes of a compared argument is stated after the boundary (reverser review-fixes 13). No
claim rests on a callee-saved register that is not a boundary argument (ruling 1 of the `lane/p46m3` review). A plain
`[C]` rests on cases that return; a plain `[I]` is a code reading the emulator does not reach.
(run:2026-10-21-cat-emu-dru)

## Answer (summary)

- [C] **The batch.** 16 entries: start 56 `0x005C7690`, 57 `0x005C79E0`, 58 `0x005C7E00`; do 114 `0x005C6910`, 115
  `0x005C6A80`, 116 `0x005C6EC0`, 117 `0x005C7160`, 118 `0x005C72F0`, 119 `0x005C7390`, 120 `0x005C77C0`, 121
  `0x005C8AD0`, 122 `0x005C7F10`, 123 `0x005C8080`, 124 `0x005C8190`; do-table entries 145 `0x005C8380` and 146
  `0x005C8520`. Every one is `(ECX game, EDX unit; skill id, level)` with `ret 8`. All 16 are emulated.
  (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [C] **Two draws before the boundaries, both on the caster's seed.** Do 124 makes one `RNG_Range(caster+0x20,
  0x10000)` after its used-skill tests and stores the value at `ebp−0xC` before its `STATLIST_Alloc` or
  `StatListSetEnd`; do 123 makes one `RNG_Range(caster+0x20, 0x100)` after its cell test and stores the low byte in its
  first argument's slot before its `MissileCreate`. No other function of the batch steps the caster's or the target's
  seed before its boundary or return (8 400 cases, both seeds compared in each; the cases' calcs are constant programs
  that call no calc function, as in skills/0008–0012, so a calc function's own draws are not covered). (run:2026-10-21-cat-emu-dru,
  fn:sub_005C8190_SkillDo124PeriodicState@0x005C8190, fn:sub_005C8080_SkillDo123Volcano@0x005C8080)
- [C] (ADR-0021; § 3) **The summons.** Do 114, 115 and 119 test the record, take `sub_0056E620_SkillSummonClass(ECX
  caster, EDX 0; id, lvl, &mode, 0, 0)` (Skills `+0xBC`, the mode `+0xBF` in `[0, 16)` else 1), **refuse** a `pettype`
  byte that is negative (`movsx`) or at or past the PetType count (→ 0, bit 6 not set), set bit 6 of the caster's
  `+0xC4`, and end at `SpawnOwnedMonster(ECX game, EDX &block)` with the 10-word block `{0, caster, class, 0, w10, 0, 0,
  pettype, petmax, w24}`: do 114 `w10 = w24 = mode`; do 115 `w10 = 8`, `w24 = mode`; do 119 first needs
  `SKILLS_GetTargetXY` (none → 0 with bit 6 set), and has `w10 = mode`, `w24 = the target point's x`, the y in the
  frame word after the block (`ebp−0x14`). (run:2026-10-21-cat-emu-dru)
- [C] (ADR-0021; § 4) **The shape and timed-state functions.** Do 116 admits `aurastate` in `[0, States count)` (`jl`)
  and ends at `STATE_GroupClear(ECX caster, EDX aurastate; 1)` after bit 6. Do 120 and do 124 admit the same range,
  need `UNIT_GetUsedSkill` and `0x00643CE0(node)` (its record's `s16 +0x00`) equal to the id (else 0), set bit 6; do
  120 ends at `COMBAT_DeliverQueued(game, caster; target, 0)` with a target, returns 1 when the node's `+0x18` is 0, and
  else ends at `STATLIST_Alloc(game+0x1C, 2, frame + auralencalc, type, guid)` (no list of the state) or
  `StatListSetEnd(list, frame + auralencalc)`; do 124 draws (above), raises `auralencalc` to 1 and ends at the same
  two calls. (run:2026-10-21-cat-emu-dru)
- [C] (ADR-0021; § 5) **The periodic states, entries 145 and 146.** A record outside the table, a level ≤ 0, an
  `aurastate` outside `[0, States count)`, a caster without that state (`UNIT_HasState`), entry 146's
  `SrvMissileByCharge` ≤ 0 or no unit skill (`SKILLS_GetUnitSkill`), or an `aurarangecalc` ≤ 0 end at
  `UNIT_CancelEvents(ECX game, EDX caster; 5, id)` at the shared exit; a caster in a town room with Skills `+0x05` bit 0
  clear ends at `UNIT_UnlinkStatList(caster, list)` (a list of the state) or `STATE_Set(caster, aurastate, 0)`;
  otherwise both end at `UNIT_CancelEvents(game, caster; 5, id)` at their re-arm site, entry 145 having stored `frame +
  Param4` in its first argument's slot. (run:2026-10-21-cat-emu-dru)
- [C] (ADR-0021; § 6) **The melee functions.** Start 56 needs the used skill and a target and ends at
  `COMBAT_MeleeHitTest(target, SKILLS_GetToHit(caster, id, lvl), 0)` with a zeroed 0x70-byte packet; start 57 adds the
  node's id test, and for `aurastate` in range the caster's state (none → 0), writes 0 at the used node's `+0x18` and
  ends at the same call (no packet zeroed). Start 58 and do 122 (do 122 after bit 6) go through `0x0056E680(game,
  caster; target, rec, id, lvl, &packet, 0)`: **with `ResultFlags` bit 0 set there is no hit test**: the packet's
  `+0x04` gets `ResultFlags`, `+0x00` gets `2 | HitFlags`, `+0x60` a non-zero `HitClass`, start 58's `+0x0C` `calc1`,
  and both end at `COMBAT_BuildDamage(game, caster; target, &packet, 0, SrcDam)`; with it clear the case ends at
  `MeleeHitTest(target, GetToHit, 0)` inside `0x0056E680`. Do 121 needs the target, the node's id and a non-zero node
  `+0x18`, writes 0 there and ends inside `0x005C8980` at `MeleeHitTest(target, sum, 0)`, `sum` the 32-bit total of
  `SKILLS_GetToHit(caster, s, lvl)` over the states of the list at `DataTables+0x17C` (count `s16 +0x180`) that the
  caster has and whose list's stat 350 names a skill `s` in range, with the last such skill's non-zero `SrcDam` byte (0x80
  by default) at `ebp−0x8`. (run:2026-10-21-cat-emu-dru)
- [C] (ADR-0021; § 7) **The missiles.** Do 117 and 118 admit `SrvMissileByCharge`'s class in `[0, Missiles count)`,
  set bit 6 and need `calc1 > 0` (else 0); do 117 ends at `SkillMissileCreate(ECX game, EDX class; caster, id, lvl, 0,
  0, 0, 0, 0)`; do 118 calls `0x005C7040(game, caster; calc1, class, id, lvl, 0)`, which returns 1 without a target
  point and else ends at `MissileCreate` with `{flags 0x21, owner the caster, class, the caster's position, the target
  point, id, lvl, +0x54 0x005C9290, +0x58 0}`. Do 123 admits a class `> 0` with **no upper test**, needs the target
  point, and in `sub_0056E450_SkillTargetCellFree` reaches the fatal path's `0x00408090` for a class at or past the
  Missiles count; else, with the caster's room, `COLL_WHTest(room, x, y, Size, Size, 5)` (run here): a `Size` of 2 or
  more ends at `COLL_RectTest(room, &{x − Size/2, y − Size/2, …}; 5)`; 0 or 1 tests the cell word `& 5` through
  `COLL_CellTestNb` (0x27 without a room, map or word array), a busy cell → 0; a free one: bit 6, the draw, and
  `MissileCreate` with `{flags 1, owner the caster, class, x, y, id, lvl}`. (run:2026-10-21-cat-emu-dru)
- [I] After, from the reading: the summons' `SummonSetLevel` and `SummonInitStats` (do 115 sets stat 12 to
  `max(calc2, 1)` itself and state 150); do 116's list (no `max(…, 1)` on its length) and the remove callback
  `0x005C6C50`; do 120's stack count stat 169 `min(old + 1, calc2)` and **its `SKILLS_ApplyAuraStats` called with that
  count as the level**; do 124's list, then `UNIT_CancelEvents(5, id)` and **unit event 5 queued at `frame + Param4`
  with `(id, lvl)`**, and the drawn value stored at the used node's `+0x18`; entry 146's re-seed of **the caster's
  seed** from its unit skill's `+0x18`, a fresh `RNG_Range(1 000 000)` stored back there, and up to five pairs of
  `RNG_Range(2r + 1)` for a free point (x first); entry 145's `SkillRollPhys` and `SKILLS_RollElemDamage` (the
  caster's seed) into `AreaHitAt`; the hits' elemental rolls; do 117's and 118's further creations; do 123's
  `MISSDATA_SetSeedLow(missile, byte)`. Every callee boundary is listed per function.
  (fn:sub_005C8520_SkillDo146Armageddon@0x005C8520, 0x005C8354–0x005C835C)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005C7690` | `sub_005C7690_SkillSt56ShapeHit` | start 56 | I |
| `0x005C79E0` | `sub_005C79E0_SkillSt57Rabies` | start 57 | I |
| `0x005C7E00` | `sub_005C7E00_SkillSt58FireClaws` | start 58 | I |
| `0x005C6910` | `sub_005C6910_SkillDo114Summon` | (P1.3 name) do 114 | I |
| `0x005C6A80` | `sub_005C6A80_SkillDo115Vine` | do 115 | I |
| `0x005C6EC0` | `sub_005C6EC0_SkillDo116Shapeshift` | do 116 | I |
| `0x005C7160` | `sub_005C7160_SkillDo117Firestorm` | (P1.3 name) do 117 | I |
| `0x005C72F0` | `sub_005C72F0_SkillDo118Twister` | do 118 | I |
| `0x005C7390` | `sub_005C7390_SkillDo119Spirit` | do 119 | I |
| `0x005C77C0` | `sub_005C77C0_SkillDo120FeralMaul` | do 120 | I |
| `0x005C8AD0` | `sub_005C8AD0_SkillDo121Rabies` | do 121 | I |
| `0x005C7F10` | `sub_005C7F10_SkillDo122Hunger` | do 122 | I |
| `0x005C8080` | `sub_005C8080_SkillDo123Volcano` | do 123 | I |
| `0x005C8190` | `sub_005C8190_SkillDo124PeriodicState` | do 124 | I |
| `0x005C8380` | `sub_005C8380_SkillDo145Hurricane` | do-table entry 145, `srvactivefunc` of state 144 | I |
| `0x005C8520` | `sub_005C8520_SkillDo146Armageddon` | (P1.3 name) do-table entry 146, `srvactivefunc` of state 145 | I |
| `0x00643CE0` | `sub_00643CE0_SkillNodeId` | `(node, file, line)`, `ret 0xC`: 0 for no node, else the `s16` at the node record's `+0x00` | I |
| `0x004EFC80` | `sub_004EFC80_SkillGetParam4` | `(ECX id)`: Skills `+0x154`, 0 outside the table | I |
| `0x0056E680` | `sub_0056E680_SkillHitOrResultFlags` | `(ECX game, EDX unit; target, rec, id, lvl, &packet, last)`, `ret 0x18`: § 6 | I |
| `0x005C7040` | `sub_005C7040_SkillMissileSeries` | `(ECX game, EDX unit; n, class, id, lvl, first)`, `ret 0x14`: § 7 | I |
| `0x005C8980` | `sub_005C8980_RabiesShapeHit` | `(ECX game, EDX unit; lvl)`, `ret 4`: § 6 | I |
| `0x005C6C50` | `sub_005C6C50_ShapeRemoveCb` | do 116's list remove callback (not read beyond its calls) | I |
| `0x00625D00` | `sub_00625D00_StatListGetBaseStatJ` | a jump to `sub_00625350_StatListGetBaseStat` | I |

## Walkthrough

### 1. The table slots, the shared shape and entries 145 and 146

- [C] `g_SkillStartFuncs[56..58]` and `g_SkillDoFuncs[114..124, 145, 146]` are the Functions table's addresses (16
  entries compared, `table_entries=16`). (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0,
  `static.txt`)
- [C] `g_PlayerEventFuncs[5]` (`0x006E1824`) and `g_MonEventFuncs[5]` (`0x006E24A4`) both hold
  `sub_0056D790_StateDoFunc` (`0x0056D790`), read from the image (`static.txt`). (data:g_PlayerEventFuncs@0x006E1810,
  data:g_MonEventFuncs@0x006E2490)
- [I] `StateDoFunc(ECX game, EDX unit; id, lvl)` takes the id's Skills record (`0 < id < count`), its `aurastate`
  (`+0x80`, in `[0, States count)`), that state's States record `+0x36` (`srvactivefunc`, `[0, 0xBF)`), and calls
  `g_SkillDoFuncs[that](game, unit; id, lvl)` with the same id and level (0x0056D790–0x0056D805). So entries 145 and 146
  run with the skill id and level that queued unit event 5; do 124 queues it with its own `(id, lvl)` (§ 4). The stock
  rows: 250 Hurricane has `aurastate` 144 (`hurricane`, `srvactivefunc` 145); 249 Armageddon and 349 Diablogeddon have
  145 (`armageddon`, 146). (`rows.txt`, tbl:States.txt:srvactivefunc, tbl:Skills.txt:aurastate)
- [I] All 16 test `0 ≤ id < DataTables+0xBA0` and a non-null record (`DataTables+0xB98 + 0x23C · id`) first and return
  0 when it fails; entries 145 and 146 end that refusal at `UNIT_CancelEvents` instead (§ 5). (0x005C6918–0x005C6948,
  0x005C8389–0x005C83B9, 0x005C8529–0x005C8559)
- [I] **Stock rows** (`rows.txt`): do 114 on 221 Raven (`summon` 419 `druidhawk`, `pettype` 10); do 115 on 222 Plague
  Poppy, 231 Cycle of Life, 241 Vines (`aurastate` 150, `pettype` 14); do 116 on 223 Wearwolf (`aurastate` 139), 228
  Wearbear (140), 350 Delerium Change (177); do 117 on 225 Firestorm (`srvmissilea` 458); do 118 on 240 Twister (477),
  245 Tornado (478); do 119 on 226 Oak Sage, 227 Summon Spirit Wolf, 236 Heart of Wolverine, 237 Summon Fenris, 246
  Spirit of Barbs, 247 Summon Grizzly; start 56 and do 120 on 232 Feral Rage (`aurastate` 120), 233 Maul (117); start
  57 and do 121 on 238 Rabies (`ResultFlags` 1, `HitFlags` 2); start 58 (with do 2, skills/0012) on 239 Fire Claws;
  do 122 on 242 Hunger; do 123 on 244 Volcano (479); do 124 on 249 Armageddon (`srvmissilea..c` 577), 250 Hurricane,
  349 Diablogeddon (670). (`rows.txt`, tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc)
- [I] `0x005C7520`, between do 119 and start 56, is a fourth summon function of do 114's shape. The scan
  (`static.txt`: 0 and 0) is a linear objdump sweep of `.text` for any operand text naming `0x5c7520` (call and jump
  targets as objdump resolves them, immediates, memory operands) and a count of the little-endian dword in the whole
  file; both are 0, so it has **no direct reference** in the image (an address computed at run time is not excluded).
  Not read further.

### 2. Emulation: the `dru` families

The method is skills/0012's: each case calls the function with `ECX` = the game, `EDX` = the caster and the stack
`(id, lvl)`, and dumps the stack, the caster's and the target's seeds, the caster's `+0xC4`, the second argument's slot
and, where a claim writes them, the used node's `+0x18` (start 57, do 120, 121, 124) and the first argument's slot
(entry 145, do 123). Emulated, not observed: `0x00643CE0`, `SkillSummonClass` with
`sub_0063EA70_SkillSummonRec` (the `EDX` 0 path, as in skills/0009), `sub_006444A0_UnitSkillGet18`, `sub_00644560_UnitSkillSet18`,
`0x004EFC80`, `0x0056E680` up to its `MeleeHitTest`, `0x005C7040` up to its first `MissileCreate`, `0x005C8980` with
`STATLIST_GetBaseStat` (through `0x00625D00`) and `SKILLS_GetRecord`, and **`COLL_WHTest` (`0x0064D800`, a boundary in
skills/0008) with `COLL_CellTestNb` and `DUNGEON_GetCollMap`** up to `COLL_RectTest`; and the earlier batches' helpers
(`UNIT_GetTargetUnit`, `UNIT_GetUsedSkill`, `SKILLS_GetUnitSkill`, `SKILLS_GetTargetXY`, `SrvMissileByCharge`,
`SKILLS_GetToHit`, `UNIT_FindStatListByState`, `UNIT_HasState`, `RoomIsTown`, `RoomAtSubtile`, `SkillTargetCellFree`,
`RNG_Range`). Observed (new for this batch): `COMBAT_BuildDamage` (`0x0057B7D0`), `sub_006260B0_StatListSetEnd`,
`UNIT_UnlinkStatList`, `COLL_RectTest` (`0x0064CEB0`); the others as declared since skills/0008–0012 (`SpawnOwned`,
`GroupClear`, `DeliverQueued`, `StatListAlloc`, `StateSet`, `CancelEvents`, `MeleeHitTest`, `SkillMissileCreate`,
`MissileCreate`, the fatal path's `0x00408090`).

**Register arguments read before written** (ruling 1 of the `lane/p46m8` review): `STATE_GroupClear` (`mov edi, edx`,
`mov ebx, ecx` at `0x0056C749`/`0x0056C750`), `UNIT_CancelEvents` (`mov edi, ecx` then `mov ecx, edx` at
`0x00540E64`/`0x00540E66`), `sub_0056ECB0_SkillMissileCreate` (`mov edi, edx`, `mov ebx, ecx` at
`0x0056ECC1`/`0x0056ECC3`, before its `memset` call), `COMBAT_BuildDamage` (`mov edi, edx` at `0x0057B7D7`, `mov
[ebp−0x10], ecx` at `0x0057B7DB`), `COLL_RectTest` (`mov edi, edx` at `0x0064CEB8`; `ECX` unwritten up to its
`RoomAtSubtile(ECX, …)` call at `0x0064CEC0`); `MeleeHitTest`, `DeliverQueued`, `SpawnOwnedMonster` and `MissileCreate`
as in skills/0009–0012.

**Nested boundaries** (ruling 1 of the `lane/p46m6` review, at each level), each compared at its absolute stack slot:
start 58's return from `0x0056E680` (`0x005C7E7A` at `0x7FEFFF60`) and do 122's (`0x005C7F90` at `0x7FEFFF5C`)
(`0x0056E680` has five callers in the image: `0x005C7C5E`, `0x005C7E75`, `0x005C7F8B`, `0x005CD53F`, `0x005D15E0`);
do 121's return from `0x005C8980` (`0x005C8B5F` at `0x7FEFFFE0`; two callers, `0x0056CA69` and `0x005C8B5A`); do 118's
return from `0x005C7040` (`0x005C7375` at `0x7FEFFFD4`, with the five pushed arguments above it; one caller,
`0x005C7370`); do 123's return from `SkillTargetCellFree` (`0x005C80F1` at `0x7FEFFF80`; three callers) for the fatal
and the `RectTest` cases, and `SkillTargetCellFree`'s return from `COLL_WHTest` (`0x0056E4EF` at `0x7FEFFF4C`; 14
callers) for the `RectTest` cases (`static.txt` lists the call sites).

- [C] Four families, **8 400 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 3 967 matched boundary cases
  (33 function, boundary and return-address triples, each a `site` line) (`check.txt`; run:2026-10-21-cat-emu-dru):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `summon_dru` | do 114, 115, 119 | 1 500 | pet type kept as 0 (402); x into `+0x14`/`+0x18` (228); `+0x24` zero (735); do 115's `+0x10` the mode (257) | SpawnOwned @0x005C6A00, @0x005C6B71, @0x005C74A0; returns 0 |
  | `shape_dru` | do 116, 120, 124, 145, 146 | 2 500 | `aurastate` 0 refused (105); do 124 unclamped, do 120 clamped (132); no draw (202); no town branch (134); 145's slot without the frame (47) | GroupClear @0x005C6F25; DeliverQueued @0x005C786A; StatListAlloc @0x005C78D1, @0x005C8295; StatListSetEnd @0x005C7917, @0x005C82E1; CancelEvents @0x005C8443, @0x005C8481, @0x005C85E3, @0x005C8647; StateSet @0x005C8436, @0x005C85D6; UnlinkStatList @0x005C841D, @0x005C85BD; returns 0, 1 |
  | `melee_dru` | start 56, 57, 58, do 121, 122 | 2 400 | `ResultFlags` ignored (171); no `HitClass` (86); any node id (52); start 57 without the state test (47); first `SrcDam` kept (2); no `SrcDam` (80) | MeleeHitTest @0x005C7717, @0x005C7AAB, @0x005C8A9B (in `0x005C8980`), @0x0056E6B8 (in `0x0056E680`, from start 58 and do 122); CombatBuildDmg @0x005C7ED2, @0x005C7FE0; returns 0, 1 |
  | `miss_dru` | do 117, 118, 123 | 2 000 | `calc1` 0 admitted (156); flags 1 for 0x21 (123); do 123 with an upper test (75); cell mask 7 (15); no draw (72) | SkillMissileCreate @0x005C7206; MissileCreate @0x005C7140 (in `0x005C7040`), @0x005C814D; Fatal @0x0056E4A3 (in `SkillTargetCellFree`); RectTest @0x0064D866 (in `COLL_WHTest`); returns 0, 1 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 43 of 43 pins): the hash offsets, the `CALC_Eval` jump
  table, the skills calc function count `0x007457AC`, `g_BitMask32` and the town tables. The count's scan matches every
  operand naming the address (a `PTR` or `moffs` store, an immediate, a read): 0 stores, 0 immediates, 7 reads in
  `.text` (`ref_scan`, the condition of ruling 3 of the `lane/p46m5` review). Skills, Missiles, ItemStatCost, MonStats,
  the stat lists, the skill nodes, the state list at `DataTables+0x17C`, the rooms and their collision maps and the
  units are scratch records written one field per field read.
- [C] **Inputs set in the memory spec** (ADR-0015, S1e review ruling 3): `g_pDataTables`, pointed at a scratch
  DataTables, is an input of the claims (no writer scan is cited for it); the security cookie is written as in 9a. No
  other image global is set. (run:2026-10-21-cat-emu-dru)
- [C] **The weak controls and their deciding classes** (ruling 4 of the `lane/p46m5` review). `shape_dru`'s
  `p4_noframe` (47) fails on every entry-145 re-arm case whose game frame is non-zero (47 of the 48 at
  `@0x005C8481`); `melee_dru`'s `nostate57` (47) on every start 57 case with `aurastate` in range and the state's bit
  clear (the 47 `noshape` returns), `sd_first` (2) on the two do 121 cases with two counted skills whose non-zero
  `SrcDam` bytes differ, the first neither 0x80 nor equal to the last (the control keeps the first byte unless it is
  0x80: cases 383, bytes 235 then 3, and 2201, 222 then 128). The "last" reading rests on more than the control: recounted at the
  review from `melee_dru.json` with the lane's model, 8 of the 255 boundary cases count two or more distinct non-zero
  bytes (47, 75, 197, 317, 383, 1169, 1479, 2201), and among them a first-kept reading fails 7, a smallest one 5 and a
  largest one 3, so all three are separated from the last; `miss_dru`'s `mask7` (15) on the 15 do 123 cell cases
  whose word has bit 1 set and bits 0 and 2 clear. Each family has a control failing 90 or more (`w24_zero` 735, `notown` 134, `rf_ignored` 171, `c1_ge0` 156).
  Of the 255 do 121 boundary cases, 36 count two states and 4 count three, so the sum is separated from a single
  term. (run:2026-10-21-cat-emu-dru)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills columns `[C]` by
  layout; unit, node, stat-list, room and collision-map offsets `[I]`, skills/0001, skills/0008, stats/0002,
  drlg/0005), and nothing here says when the game runs these functions or on which seed state.
  (run:2026-10-21-cat-emu-dru)

### 3. The summons: do 114, 115, 119

```c
// fn:sub_005C6910_SkillDo114Summon@0x005C6910 (do 115 and 119 alike), trimmed to the tests and the block
cls = SkillSummonClass(ECX u, EDX 0; id, lvl, &mode, 0, 0); if (cls < 0) return 0;
pet = (s8)rec->pettype; if (pet < 0 || pet >= DataTables->nPetTypes) return 0;
u->c4 |= 0x40;                                       // do 119: if (!SKILLS_GetTargetXY(game, u; &x, &y)) return 0;
blk = {0, u, cls, 0, mode /* do 115: 8 */, 0, 0, pet, EvalCalc(petmax), mode /* do 119: x */};
m = SpawnOwnedMonster(game, &blk);
```

- [C] (ADR-0021; ends at `SpawnOwnedMonster` @0x005C6A00, @0x005C6B71 or @0x005C74A0) **Do 114, 115, 119**: the record
  (→ 0); `SkillSummonClass(ECX caster, EDX 0; id, lvl, &mode, 0, 0)`: with `EDX` 0, `SkillSummonRec` takes the skill
  path, the class Skills `+0xBC` (`s16`, in `[0, MonStats count)`) and the mode `+0xBF` (`movsx`, kept in `[0, 16)`,
  else 1); the `+0xBE` byte by `movsx; test; jl` (→ 0) and `cmp [DataTables+0xBF0]; jge` (→ 0), with bit 6 not set on
  either refusal; then bit 6; the block at `ebp−0x30` (do 119 `ebp−0x3C`), zeroed, `+0x04` the caster, `+0x08` the
  class, `+0x10` the mode (do 115: 8, `mov [ebp−0x20], 8` at `0x005C6B4B`), `+0x1C` the byte, `+0x20` `petmax`
  (`+0xC0`), `+0x24` the slot `SkillSummonClass` wrote the mode to (do 114, 115), or for do 119 `SKILLS_GetTargetXY`'s
  x (`ebp−0x18`), its y at `ebp−0x14` after the block (both compared); do 119 returns 0 with bit 6 set when there is
  no target point. The block is compared by content. (run:2026-10-21-cat-emu-dru `summon_dru`,
  fn:sub_005C6910_SkillDo114Summon@0x005C6910, fn:sub_005C6A80_SkillDo115Vine@0x005C6A80,
  fn:sub_005C7390_SkillDo119Spirit@0x005C7390)
- [I] Not run: `SkillSummonClass`'s refusal (a class outside the MonStats count gives `0x0058F710(caster)`'s fallback,
  which reads through a null pointer for a caster that is not a monster with data, then −1); the cases write a class
  in range (as skills/0009 did). (0x0056E641–0x0056E66C, 0x0058F710–0x0058F72C)
- [I] After the boundary: no unit → 0. Do 114: the summon's `+0xC4` bit 2 cleared, `UnitSetStat(m, 74, 0, 0)`,
  `sub_005C49E0_SummonSetLevel(ECX game, EDX caster; m, max(calc2, 1), lvl)`, `sub_005C4470_SummonInitStats(game,
  caster; m, id, lvl, 0)`. Do 115: `0x005B1900(ECX game, EDX m; 0, caster +0xD0)` (skills/0003 § 7's target-list
  add), `STATE_Set(m, 150, 1)`, `UnitSetStat(m, 12, max(calc2, 1), 0)` (no `SummonSetLevel`), `SummonInitStats`. Do 119:
  `0x005B1900`, `SummonSetLevel(m, max(calc2, 1), lvl)`, `SummonInitStats`. Each returns 1. What the spawn makes of the
  block's `+0x24` word (the mode, or do 119's x) is skills/0009's open question. (0x005C6A00–0x005C6A65,
  0x005C6B71–0x005C6BE1, 0x005C74A0–0x005C7505)

### 4. The shape and timed-state functions: do 116, 120, 124

- [C] (ADR-0021; ends at `STATE_GroupClear` @0x005C6F25) **Do 116** (`0x005C6EC0`): the record; `aurastate` (`movzx;
  test ax, ax; jl`, then `movsx; cmp [DataTables+0xC4]; jge`: `[0, count)`, else 0); bit 6; `STATE_GroupClear(ECX
  caster, EDX aurastate; 1)`. (run:2026-10-21-cat-emu-dru `shape_dru`, fn:sub_005C6EC0_SkillDo116Shapeshift@0x005C6EC0)
- [I] After do 116's boundary: a non-zero result → `sub_0056F020_SkillDelayFromCalc(ECX game, EDX caster; id, lvl)` and
  **0**; zero → `auralencalc` (`+0x60`, not raised to 1), `UNIT_FindStatListByState(caster, aurastate)` (found → 0),
  `STATLIST_Alloc(game+0x1C, 2, frame + length, type, guid)` (0 → 0), `STATLIST_SetState`, the remove callback
  `0x005C6C50`, `STATLIST_LinkToUnit`, `STATE_Set(caster, aurastate, 1)`, `UnitQueueEvent(game, caster; 12, frame +
  length, 0, 0)`, `SKILLS_ApplyAuraStats(ECX caster, EDX list; rec, id, lvl)`, the list's stats 350 = id and 351 = lvl,
  `SKILLS_GetUnitSkill(caster, id)` → `0x00644340(node, 10)`; returns 1. The callback `0x005C6C50` clears the group
  (`STATE_GroupClear(…, 1)`), reads the list's stat 350, and through that skill's node calls `0x005C6BF0(caster, 10)`,
  `0x00644340` and `STATE_Set(caster, state, 0)`. By the stock rows the state is the wereform (139 `wolf`, 140 `bear`,
  177 `delerium`). (0x005C6F25–0x005C7039, 0x005C6C50–0x005C6CA4)
- [I] Not run: a null caster (do 116, 120 and 124 skip bit 6 for it and pass type 6 and guid −1 to `STATLIST_Alloc`,
  `lea eax, [edi+0x6]; or ecx, −1`); every case has a caster of type 0 or 1, so `UNIT_HasState`'s type-3 branch is not
  run either. (0x005C6F69–0x005C6F7A, 0x005C78AC–0x005C78BD, 0x005C8270–0x005C8281)
- [C] (ADR-0021; ends at `COMBAT_DeliverQueued` @0x005C786A, `STATLIST_Alloc` @0x005C78D1 or `StatListSetEnd`
  @0x005C7917) **Do 120** (`0x005C77C0`): the record; `aurastate` in `[0, States count)` (`jl`, `jge`; else 0);
  `UNIT_GetUsedSkill(caster)` (0 → 0); `0x00643CE0(node, …, 0x2AF)` not equal to the id → 0; bit 6; a target →
  `DeliverQueued(ECX game, EDX caster; target, 0)`; no target: `UnitSkillGet18(node)` 0 → **1**; else `end = frame +
  auralencalc` (32-bit, **not** raised to 1); no list of the state on the caster (`UNIT_FindStatListByState`, 0 for
  state 0) → `STATLIST_Alloc(game+0x1C, 2, end, caster type, caster guid)`, else `StatListSetEnd(list, end)`.
  (run:2026-10-21-cat-emu-dru `shape_dru`, fn:sub_005C77C0_SkillDo120FeralMaul@0x005C77C0)
- [I] After do 120's boundaries: after `DeliverQueued`, `UnitSkillGet18(node)` as above, so a target run goes on to
  the list too; a new list: `STATLIST_SetState`, `STATE_DefaultRemoveCB`, `STATLIST_LinkToUnit`, `STATE_Set(caster,
  state, 1)`; then `StatListSetEnd(list, end)`, `UnitQueueEvent(game, caster; 12, end, 0, 0)`,
  `sub_00639E30_UnitSetStateBit(caster, state, 1)`, `v = calc2` (`+0x13C`), the list's stat 169 set to `min(old + 1,
  v)` (`0x00625D00(list, 169, 0) + 1`, `jl` against `v`), stats 350 = id and 351 = lvl,
  `SKILLS_ApplyAuraStats(ECX caster, EDX list; rec, id, that count)`: **the `aurastat` calcs evaluate at the count, not
  at the skill level**; returns 1 (1 also when the allocation fails). (0x005C786A–0x005C79CC)
- [C] (ADR-0021; ends at `STATLIST_Alloc` @0x005C8295 or `StatListSetEnd` @0x005C82E1) **Do 124** (`0x005C8190`): the
  record; `aurastate` in `[0, States count)`; the used skill and its id (as do 120; else 0); bit 6; **`r =
  RNG_Range(caster+0x20, 0x10000)`** (`mov edx, 0x10000` at `0x005C8228`; the caster's seed one step on, `r` at
  `ebp−0xC`); `end = frame + max(auralencalc, 1)` (`cmp eax, 1; jge`); `STATLIST_Alloc(game+0x1C, 2, end, type, guid)`
  without a list of the state, else `StatListSetEnd(list, end)`. (run:2026-10-21-cat-emu-dru `shape_dru`,
  fn:sub_005C8190_SkillDo124PeriodicState@0x005C8190)
- [I] After do 124's boundaries: `STATLIST_Alloc` giving 0 → **0** (`0x005C8299`; do 120 returns 1 there); else as
  do 120's list steps (`STATE_DefaultRemoveCB`), `StatListSetEnd`, event 12 at
  `end`, `SKILLS_ApplyAuraStats(caster, list; rec, id, lvl)`, stats 350/351; then `p = Param4` (`0x004EFC80`, Skills
  `+0x154`), `UNIT_CancelEvents(game, caster; 5, id)`, `UnitQueueEvent(game, caster; 5, frame + p, id, lvl)`, and
  **`UnitSkillSet18(used node, r)`**; returns 1. Unit event 5 runs `StateDoFunc` (§ 1), which, for the stock rows, runs
  entry 145 or 146 with this id and level. (0x005C8295–0x005C836C)

### 5. The periodic states: do-table entries 145 and 146

```c
// fn:sub_005C8520_SkillDo146Armageddon@0x005C8520 (entry 145 alike up to the re-arm), trimmed
if (!rec || lvl <= 0 || !(0 <= st && st < nStates) || !UNIT_HasState(u, st)) goto cancel;   // cancel: CancelEvents(game, u; 5, id); return 0
if (!(rec->f05 & 1) && (room = UnitGetRoom(u)) && RoomIsTown(room)) {
    if ((l = UNIT_FindStatListByState(u, st))) { UNIT_UnlinkStatList(u, l); STATLIST_FreeIfPlain(l); }
    STATE_Set(u, st, 0); goto cancel; }
if (SrvMissileByCharge(u, id) <= 0 || !(n = SKILLS_GetUnitSkill(u, id)) || EvalCalc(aurarangecalc) <= 0) goto cancel;
CancelEvents(game, u; 5, id); UnitQueueEvent(game, u; 5, frame + Param4, id, lvl);   // entry 145: no class, no node
```

- [C] (ADR-0021; ends at `UNIT_CancelEvents` @0x005C8443 / @0x005C85E3 or @0x005C8481 / @0x005C8647,
  `UNIT_UnlinkStatList` @0x005C841D / @0x005C85BD, or `STATE_Set` @0x005C8436 / @0x005C85D6) **Entry 145**
  (`0x005C8380`) and **entry 146** (`0x005C8520`), as the excerpt: no record, a level ≤ 0 (`cmp [ebp+0xC], 0; jle`), an
  `aurastate` outside `[0, States count)` (`jl`, `jge`) or `UNIT_HasState(caster, aurastate)` 0 →
  `UNIT_CancelEvents(ECX game, EDX caster; 5, id)` at the shared exit; with Skills `+0x05 & g_BitMask32[0]` clear and
  the caster's room a town room, the state's list (`UNIT_FindStatListByState`) → `UNIT_UnlinkStatList(caster, list)`,
  none → `STATE_Set(caster, aurastate, 0)`; else (entry 146: `SrvMissileByCharge(caster, id)` ≤ 0 or
  `SKILLS_GetUnitSkill(caster, id)` 0 → the shared exit) `aurarangecalc` (`+0x64`) ≤ 0 → the shared exit; else the
  re-arm `CancelEvents(game, caster; 5, id)`, entry 145 with `frame + Param4` stored at its first argument's slot
  (`[ebp+0x8]`, `0x005C8479`). (run:2026-10-21-cat-emu-dru `shape_dru`,
  fn:sub_005C8380_SkillDo145Hurricane@0x005C8380, fn:sub_005C8520_SkillDo146Armageddon@0x005C8520)
- [I] Not run: entry 146's `lea ecx, [esi+0x20]; test ecx, ecx; je` (0x005C860C–0x005C8613) is zero only for a caster
  at `−0x20`; every case passes it.
- [I] After the shared exit and the town branch: `STATLIST_FreeIfPlain(list)` and `STATE_Set(caster, aurastate, 0)`
  after the unlink, then `CancelEvents(5, id)`; **each returns 0**, so no new event 5 is queued and the period ends.
  (0x005C8416–0x005C844B, 0x005C85B6–0x005C85EB)
- [I] After entry 145's re-arm: `UnitQueueEvent(game, caster; 5, frame + Param4, id, lvl)`; without a room or in a town
  room → 0; else a zeroed packet, `sub_0056E170_SkillRollPhys(ECX caster, EDX &packet; id, lvl)`,
  `SKILLS_RollElemDamage(caster, &packet; id, lvl)` (both on the caster's seed, by their skills/0003 readings),
  `ResultFlags` ORed into `+0x04` and `HitFlags` into `+0x00`, and `sub_0056BAD0_AreaHitAt(ECX game, EDX caster; 0, 0,
  aurarangecalc, &packet, aurafilter)` (Skills `+0x50`); returns 1. (0x005C8481–0x005C8510)
- [I] After entry 146's re-arm: `UnitQueueEvent(5, frame + Param4, id, lvl)`; without a room or in a town room → 0;
  else **`RNG_SeedInit(caster+0x20, UnitSkillGet18(node))`**, `RNG_Range(caster, 1 000 000)` stored by
  `UnitSkillSet18(node, …)`, then up to five tries of `x = RNG_Range(caster, 2r + 1) − r + SubX`, `y =
  RNG_Range(caster, 2r + 1) − r + SubY` (`r` = `aurarangecalc`, x first), each needing
  `SKILLS_LineOfSightOk(x, y, caster, 0x805)`, `RoomAtSubtile(room, x; y)` and `COLL_CellTestAt(that room, x, y, 1)` 0;
  a free point → `sub_0056EDE0_MissileCreateAt(ECX game, EDX caster; id, lvl, class, x, y)` and
  `sub_00571AA0_UnitMsgA3(ECX caster, EDX 0; id, lvl, x, y, 0)`, returns 1; five failures → 0 (the event already
  re-queued). So the first period re-seeds the caster from do 124's `r` when `SKILLS_GetUnitSkill(caster, id)` and the
  used node are one node **and** no other writer of that node's `+0x18` runs between the cast and the first period
  (`sub_00644560_UnitSkillSet18` has 85 call sites, not followed; not run here). (0x005C8647–0x005C8779)

### 6. The melee functions: start 56, 57, 58, do 121, 122

- [C] (ADR-0021; ends at `COMBAT_MeleeHitTest` @0x005C7717) **Start 56** (`0x005C7690`): the record; the used skill
  (0 → 0); the target (0 → 0); a zeroed 0x70-byte packet at `ebp−0x78` (compared); `MeleeHitTest(ECX game, EDX caster;
  target, SKILLS_GetToHit(caster, id, lvl), 0)` (the 0 pushed before `GetToHit`, which is `ret 0xC`).
  (run:2026-10-21-cat-emu-dru `melee_dru`, fn:sub_005C7690_SkillSt56ShapeHit@0x005C7690)
- [I] After start 56's boundary: the result word at `+0x04`; on bit 0, with `EType` (`+0x1DC`) non-zero and `calc4`
  (`+0x144`) above 0, the conversion pair (`+0x65` the type, `+0x68` the percent), `calc1` at `+0x0C`; `SrcDam` (0
  read as 0x80); `COMBAT_ResolveAndQueue(game, caster; target, &packet, SrcDam)`; `UnitSkillSet18(node, 1)` on a hit,
  else 0; returns 1. (0x005C7717–0x005C77BB)
- [C] (ADR-0021; ends at `COMBAT_MeleeHitTest` @0x005C7AAB) **Start 57** (`0x005C79E0`): the record; the used skill (0 →
  0); `0x00643CE0(node, …, 0x2F1)` not the id → 0; the target (0 → 0); `aurastate` (`+0x80`) in `[0, States count)` and
  `UNIT_HasState(caster, aurastate)` 0 → 0 (out of range: no test); `UnitSkillSet18(node, 0)` (the node's `+0x18` 0,
  compared); `MeleeHitTest(ECX game, EDX caster; target, GetToHit(caster, id, lvl), 0)`, **no packet zeroed**.
  (run:2026-10-21-cat-emu-dru `melee_dru`, fn:sub_005C79E0_SkillSt57Rabies@0x005C79E0)
- [I] After start 57's boundary: the result word at `ebp−0x74`; bit 0 clear → **0**; set → `calc1` and (with `EType`)
  `calc4` evaluated with the results unused, `UnitSkillSet18(node, 1)`, returns 1. Stock 238 Rabies has no `aurastate`
  (65535), so the state test is skipped for it. (0x005C7AAB–0x005C7B01)
- [C] (ADR-0021; ends at `MeleeHitTest` @0x0056E6B8 inside `0x0056E680`, start 58's return `0x005C7E7A` and do 122's
  `0x005C7F90` compared, or at `COMBAT_BuildDamage` @0x005C7ED2 / @0x005C7FE0) **Start 58** (`0x005C7E00`) and **do
  122** (`0x005C7F10`): the record; the target (0 → 0); do 122 then bit 6 (start 58 none); a zeroed packet (start 58
  `ebp−0x74`, do 122 `ebp−0x78`); `0x0056E680(ECX game, EDX caster; target, rec, id, lvl, &packet, 0)`: `ResultFlags`
  (`+0x12E`, `test al, 1`) set → the packet's `+0x04` word = `ResultFlags`, return; clear → `MeleeHitTest(ECX game, EDX
  caster; target, GetToHit(caster, id, lvl), 0)` (the case's end). After the bit-0 return the caller tests `+0x04` bit
  0 and sets `+0x00 = 2 | HitFlags` (`+0x130`), `+0x60 = HitClass` (`+0x134`) when non-zero, start 58 `+0x0C = calc1`,
  do 122 `+0x04 |= ResultFlags`, then `COMBAT_BuildDamage(ECX game, EDX caster; target, &packet, 0, SrcDam)` (`+0x1A5`,
  `movzx`), the packet compared by content. (run:2026-10-21-cat-emu-dru `melee_dru`,
  fn:sub_0056E680_SkillHitOrResultFlags@0x0056E680, fn:sub_005C7E00_SkillSt58FireClaws@0x005C7E00,
  fn:sub_005C7F10_SkillDo122Hunger@0x005C7F10)
- [I] After `0x0056E680`'s `MeleeHitTest`: the result into `+0x04`, ORed with `ResultFlags` on a hit; the caller as
  above when bit 0 is set (a hit), else start 58 and do 122 return **1** with nothing queued. After `BuildDamage`:
  start 58 `SKILLS_RollElemDamage(caster, &packet; id, lvl)` and `ResolveAndQueue(game, caster; target, &packet, 0x80)`;
  do 122 the elemental roll, `+0x08 += MulDiv(+0x08, calc1, 100)` (`sub_00483360_MulDiv`), `calc2` added to `+0x38`
  and `calc3` (`+0x140`) to `+0x3C`, `ResolveAndQueue(…, 0x80)`, `COMBAT_DeliverQueued(game, caster; target, 0)`; both
  return 1. No stock row of either has `ResultFlags` bit 0: of the 357 Skills rows (recounted at the plan 0051 P0b review: `skills.txt` and the `.bin` count) only 239 has `srvstfunc` 58 and
  only 242 `srvdofunc` 122, and both have `ResultFlags` 0 (`rows.txt`, its 25-row selection checked complete against
  every row at the review; tbl:Skills.txt:ResultFlags); 238 Rabies (1) reaches
  `0x0056E680` only through `0x005C7C20` after do 121's boundary. (0x005C7E7A–0x005C7F02, 0x005C7F90–0x005C8070)
- [C] (ADR-0021; ends at `MeleeHitTest` @0x005C8A9B inside `0x005C8980`, do 121's return `0x005C8B5F` compared) **Do
  121** (`0x005C8AD0`): the record; the target (0 → 0); the used skill (0 → 0); its id (`0x00643CE0`, else 0);
  `UnitSkillGet18(node)` 0 → 0; `UnitSkillSet18(node, 0)` (compared); `0x005C8980(ECX game, EDX caster; lvl)`: the
  target; `sum = 0`, the byte `0x80` at `ebp−0x8`; for `i < (s16) DataTables+0x180` (`cmp word …, bx; jle`, then `jl`
  per pass): `s = (s16) DataTables+0x17C[i]`; skipped unless `UNIT_HasState(caster, s)`, `0 ≤ s < States count`, the
  States record `DataTables+0xBC + 0x3C · s` is non-null, `UNIT_FindStatListByState(caster, s)` is non-null and its
  stat 350 (`STATLIST_GetBaseStat(list, 350, 0)`) is a skill `k` in `[0, Skills count)`; then `sum += GetToHit(caster,
  k, lvl)` (32-bit) and a non-zero `SrcDam` of `k` replaces the byte; a zeroed packet at `ebp−0x80`;
  `MeleeHitTest(ECX game, EDX caster; target, sum, 0)`, the byte and the packet compared at their stack addresses.
  (run:2026-10-21-cat-emu-dru `melee_dru`, fn:sub_005C8AD0_SkillDo121Rabies@0x005C8AD0,
  fn:sub_005C8980_RabiesShapeHit@0x005C8980)
- [I] Not run: `0x005C8980`'s own no-target return 0 (do 121 has tested the same target first); `GetToHit` with a
  `ToHitCalc` other than −1 inside the loop (the cases write −1; the calc form is run in skills/0009); a States record
  base of 0. (0x005C8995–0x005C89AB, 0x005C8A09)
- [I] After do 121's boundary: the result into `+0x04`, `+0x60 = 1` (`mov [ebp−0x20], 1`),
  `ResolveAndQueue(game, caster; target, &packet, the byte)`, 0x005C8980 returns 1; then `DeliverQueued(game, caster;
  target, 0)`, `len = SKILLS_GetElemLen(caster, id, lvl, 1)`, `sub_005C7DB0_RabiesApply(ECX game, EDX caster; target,
  len, id, lvl)` (skills/0007's contagion) and `0x005C7C20` (`ECX` the record, `EAX` the id, `ESI` the caster; game,
  target, len, lvl): `0x0056E680` again, on a hit `HitFlags`, `HitClass`, `calc1`, `SKILLS_RollElemDamage`,
  `0x0056C840(caster, &packet; max(len, 10), id)`, `ResolveAndQueue(…, 0x80)` and `DeliverQueued`; do 121 returns 1.
  By the layout the list at `DataTables+0x17C` holds the shape-shift states, so the sum is the to-hit of the skills the
  wereform lists record. (0x005C8A9B–0x005C8AC3, 0x005C8B5F–0x005C8BB1, 0x005C7C20–0x005C7CDC)

### 7. The missiles: do 117, 118, 123

- [C] (ADR-0021; ends at `SkillMissileCreate` @0x005C7206) **Do 117** (`0x005C7160`): the record; `m =
  SrvMissileByCharge(ECX caster, EDX id)` (skills/0008 § 7), `jl` and `cmp [DataTables+0xB6C]; jge` (→ 0, bit 6 not
  set); bit 6; `calc1` (`+0x138`) ≤ 0 → 0 (bit 6 set); `SkillMissileCreate(ECX game, EDX m; caster, id, lvl, 0, 0, 0, 0,
  0)`. (run:2026-10-21-cat-emu-dru `miss_dru`, fn:sub_005C7160_SkillDo117Firestorm@0x005C7160)
- [I] After do 117's boundary: `n = calc1 − 1`; `n ≤ 0` → 1; else the block `{0x21, caster, +0x10 m, +0x14/+0x18 the
  caster's position (types 2, 4, 5 the path's `+0x0C`/`+0x10`, else `PathGetX/Y`, 0 without a path), +0x1C/+0x20
  SKILLS_GetTargetXY's point, +0x2C id, +0x30 lvl, +0x54 0x005C9290}`; no target point → 1; else `n` `MissileCreate`
  calls with `+0x58` = 0, 1, …, `n − 1`; returns 1. (0x005C7206–0x005C72DF)
- [C] (ADR-0021; ends at `MissileCreate` @0x005C7140 inside `0x005C7040`, do 118's return `0x005C7375` and its five
  arguments compared) **Do 118** (`0x005C72F0`): the record; `m` and its range as do 117; bit 6; `calc1` ≤ 0 → 0;
  `0x005C7040(ECX game, EDX caster; calc1, m, id, lvl, 0)`: the last argument 0 skips its first creation
  (`cmp [ebp+0x18], 0; je`); the block at `ebp−0x5C` `{0x21, caster, +0x10 m, the caster's position, +0x1C/+0x20 the
  target point, +0x2C id, +0x30 lvl, +0x54 0x005C9290, +0x58 0}`; no target point → 1 (do 118 returns it); else
  `MissileCreate(ECX game, EDX &block)`, compared by content. (run:2026-10-21-cat-emu-dru `miss_dru`,
  fn:sub_005C72F0_SkillDo118Twister@0x005C72F0, fn:sub_005C7040_SkillMissileSeries@0x005C7040)
- [I] Not run: `0x005C7040` with a non-zero last argument (its `SkillMissileCreate` first, then `n − 1`); its only call
  site (`0x005C7370`, do 118) passes 0. The caster types 2, 4, 5 (the static-path position) are not run.
  (0x005C7051–0x005C7085, `static.txt`)
- [I] After do 118's boundary: `calc1 − 1` more creations with `+0x58` = 1, 2, …; returns 1. (0x005C7140–0x005C7152)
- [C] (ADR-0021; ends at the fatal path's `0x00408090` @0x0056E4A3 or `COLL_RectTest` @0x0064D866, with do 123's
  return `0x005C80F1` from `SkillTargetCellFree` compared, and for `RectTest` `SkillTargetCellFree`'s `0x0056E4EF` from
  `COLL_WHTest`; or at `MissileCreate` @0x005C814D) **Do 123** (`0x005C8080`): the record; `m = SrvMissileByCharge`
  ≤ 0 → 0 (`test ebx, ebx; jle`; **no upper test**); `SKILLS_GetTargetXY` 0 → 0; `SkillTargetCellFree(ECX game, EDX
  caster; m)`: `UnitGetRoom(caster)`, a class at or past the Missiles count → the fatal path (`push 0x1281; call
  0x00408090`); no room or a zero x or y → 0; `COLL_WHTest(room, x, y, Size, Size, 5)` with `Size` the Missiles
  `+0x18A` byte: above 1 (`cmp ecx, 1; jg`) → `COLL_RectTest(ECX room, EDX &rect; 5)`, `rect = {x − Size/2, y −
  Size/2, x − Size/2 + Size − 1, y − Size/2 + Size − 1}` (`shr`, compared by content); else `COLL_CellTestNb`:
  `RoomAtSubtile(room, x; y)`, its `+0x20` map (`DUNGEON_GetCollMap`), the map's `+0x20` words (each missing → 0x27),
  else the word at `(y − y0) · width − x0 + x` (map `+0x04`, `+0x08`, `+0x00`) `& 5`; non-zero → do 123 returns 0;
  zero → bit 6, `r = RNG_Range(caster+0x20, 0x100)` (`mov edx, 0x100` at `0x005C8103`), its low byte at `[ebp+0x8]`,
  and `MissileCreate(ECX game, EDX &block)` with `{+0x00 1, +0x04 caster, +0x10 m, +0x14 x, +0x18 y, +0x2C id, +0x30
  lvl}` (compared by content; the caster's seed one step on). (run:2026-10-21-cat-emu-dru `miss_dru`,
  fn:sub_005C8080_SkillDo123Volcano@0x005C8080, fn:sub_0056E450_SkillTargetCellFree@0x0056E450)
- [I] After do 123's boundaries: no missile → 0; else `MISSDATA_SetSeedLow(missile, r & 0xFF)` and
  `sub_00571AA0_UnitMsgA3(ECX caster, EDX 0; id, lvl, x, y, [ebp+0x8])`, whose last argument is the id's slot with
  its low byte replaced by `r` (the upper three bytes the id's); returns 1. What follows `COLL_RectTest` is
  `SkillTargetCellFree`'s `neg ax; sbb; +1` on its result. (0x005C814D–0x005C818C, 0x0056E4EF–0x0056E4FD)

## Corrections to earlier findings

- skills/0003 § 5 (tier A), carried there as a dated note: do 114 and do 117 are now `[C]` up to their boundaries
  (ADR-0021). Do 114 refuses a `pettype` that is negative or at or past the PetType count **before** bit 6; do 117's
  class is `SrvMissileByCharge`'s (`srvmissilea` for the stock row), refused outside `[0, Missiles count)` before bit 6,
  and a `calc1` ≤ 0 returns 0 **with** bit 6 set. (fn:sub_005C6910_SkillDo114Summon@0x005C6910,
  fn:sub_005C7160_SkillDo117Firestorm@0x005C7160)
- skills/0003 § 9's re-seed table (the do 146 row), carried there as a dated note: the skill entry's `+0x18` that the
  first Armageddon period re-seeds the caster from is written by do 124 at the cast: `RNG_Range(caster+0x20, 0x10000)`
  (`[C]` up to do 124's boundary, § 4), stored by `UnitSkillSet18(used node, r)` after it (`[I]`, 0x005C8354–0x005C835C).
  This answers rng/seeds' open question on the first period in part (backlog to the spec-writer).

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `summon` (`+0xBC`), `pettype` (`+0xBE`), `summode` (`+0xBF`), `petmax`
(`+0xC0`), `aurastate` (`+0x80`), `auralencalc` (`+0x60`), `aurarangecalc` (`+0x64`), `aurafilter` (`+0x50`, after a
boundary), `calc1`, `calc2`, `calc3`, `calc4`, `Param4` (`+0x154`), `ResultFlags`, `HitFlags`, `HitClass`, `SrcDam`,
`EType`, `ToHit`, `LevToHit`, `ToHitCalc`, `srvmissilea..c` (through `SrvMissileByCharge`), `InTown` (`+0x05` bit 0);
`tbl:Missiles.txt:Size` (`+0x18A`); `tbl:States.txt:srvactivefunc` (`+0x36`, through `StateDoFunc`); DataTables
`+0xBC`, `+0xC4`, `+0xBF0`, `+0x17C`/`+0x180`; unit `+0x00`, `+0x0C`, `+0x20` seed, `+0x2C` path (`+0x02`, `+0x06`,
`+0x10`, `+0x12`, `+0x1C`, `+0x58`), `+0x5C` stat list (`+0x10`, `+0x3C`, `+0x40`, `+0x58`; a list's `+0x14`, `+0x24`,
`+0x28`, `+0x2C`), `+0xA8` skills (`+0x04` chain, `+0x10` used node; node `+0x00`, `+0x18`), `+0xC4` bit 6; room
`+0x20` (map `+0x00`, `+0x04`, `+0x08`, `+0x20`); game `+0x1C`, `+0xA8`.

## Dead ends

- None in the code. The first emulation (`dev/dev1`, kept under its own names) mismatched on 3 do 121 cases where the
  model walked the whole state list after the case had written a count of 0 (the model fixed), and one control did not
  fail because no case had a class past the Missiles count (the writer fixed); a second development run (`dev/dev2`)
  matched in full and only re-weighted the writers. No claim rests on either.

## Open questions

- [L] What `SpawnOwnedMonster` makes of do 119's `+0x24` word (the target point's x) and whether the summon is placed
  near the caster (block `+0x14`/`+0x18` 0) (§ 3), a harness check.
- [L] What `STATE_GroupClear`'s result means for a shape-shift (do 116 returns 0 and calls `SkillDelayFromCalc` when it
  is non-zero) (§ 4).
- [L] Who fills `DataTables+0x17C`/`+0x180` and with which states (§ 6): code, not layout (plan 0051 P0b: `states.bin` has no list field; data candidates in States § Open questions), plan 0051 Phase 1b item 3; and whether
  `SKILLS_GetUnitSkill(caster, id)` and the used node are the same node at Armageddon's first period, and whether any
  other writer of its `+0x18` runs between the cast and that period (§ 5).
- [L] Everything after each boundary (§§ 3–7), for a later batch or the harness.
