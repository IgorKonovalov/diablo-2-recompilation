# 0018 — Catalogue batch 8c: the monster skill functions of Skills rows 290–338 (start 61–63, do 128–137, 139, 140, 147–149)

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 61, 62, 63 (`srvstfunc`, `g_SkillStartFuncs`) and do function
> 128–137, 139, 140, 147, 148 and 149 (`srvdofunc`, `g_SkillDoFuncs`; 147 is States `srvactivefunc`) of plan 0046
> batch 8c do (the act 5 monsters and Baal: Cry Help, the imps, the vines and cyclers, the overseers' whip, the
> defilers, the siege beast, the minion spawners, the death maulers, Fenris, Baal's tentacles and cold missiles, the
> doom knights and necromages): which Skills, Missiles, MonStats and unit fields it reads, what it makes, which draws
> it makes on which seed, what it returns, and which of that the emulator can confirm?
> **Date:** 2026-10-21   **Plan:** 0046 (Phase 1, batch 8c)   **Status:** for review (`lane/p46m15`)

Static reading of the pinned `Game.exe` with objdump and the lane's Ghidra copy `workspace/ghidra-p46m15`, then
emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged) and the `8c` families of
`tools/skills_catalogue_emu.py` (§ 2; run:2026-10-21-cat-emu-8c in [experiments](experiments.md)). Skills columns are
named as in [Skills](../../tables/Skills.md), Missiles's as in [Missiles](../../tables/Missiles.md), MonStats's as in
[MonStats](../../tables/MonStats.md). The dispatch that runs a start or do function is
[skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart); do 98, which do 129 calls
directly, is [skills/0016](0016-monster-8a.md) § 4's. Stock values come from `workspace/logs/skills-cat-8c/rows.txt`
(`rows.sh` beside it: the 17 Skills rows that name one of the batch's entries, checked complete against all 357 rows by
its `CHECK` lines, the States row whose `srvactivefunc` is 147, and the row names).

**Tag convention for this finding** (as skills/0016 and 0017). A claim marked **[C] (ADR-0021)** rests on emulated
cases that end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a function
entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site (the return
address at ESP), with a site control that fails every matched boundary case, and where the boundary sits inside a
helper the function called, the helper's return address is compared at its absolute stack slot (§ 2 lists each slot);
(c) the model gives and the checker compares every argument the claim uses (registers the callee reads before it
writes them, stack words, and for a pointer the bytes it points to), every byte written before the call that the claim
uses (the caster's `+0xC4`, the used node's words, the argument slots, the frame words named), and the state of **the
caster's and the target's seeds** at the boundary (both, in every case). Each such claim names the boundary it ends at;
**the callee and all code after it are not covered** and keep `[I]`, marked "after, `[I]`" in place (reverser
review-fixes 13). No claim rests on a callee-saved register that is not a boundary argument. A plain `[C]` rests on
cases that return; a plain `[I]` is a code reading the emulator does not reach. (run:2026-10-21-cat-emu-8c)

## Answer (summary)

- [C] **The batch.** Eighteen entries, each `(ECX game, EDX unit; skill id, level)` with `ret 8`: start 61
  `0x005D1BF0`, 62 `0x005D2420`, 63 `0x005D2A10`; do 128 `0x005D1800`, 129 `0x005D1AB0`, 130 `0x005D1CD0`, 131
  `0x005D1F70`, 132 `0x005D2090`, 133 `0x005D2250`, 134 `0x005D2320`, 135 `0x005D2490`, 136 `0x005D25B0`, 137
  `0x005D26F0`, 139 `0x005D2940`, 140 `0x005D2C20`, 147 `0x005D2B20`, 148 `0x005CDFB0`, 149 `0x005CE0B0`
  (`table_entries=18`). All eighteen are emulated: four families, **8 800 cases, 0 mismatches**.
  (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0, `static.txt`, run:2026-10-21-cat-emu-8c)
- [C] **Draws before the boundaries.** Two entries step a unit's seed, both **the caster's** (`U+0x20`/`+0x24`):
  **do 131** draws `RNG_Range(caster, 100)` once, only for a live monster target whose MonStats base is 453
  (`minion1`), against calc1; **do 140** steps it inline once for its try count (`difficulty + low mod 3 + 2`) and then
  twice per try (an x and a y offset, each `low mod 18 − 9`) until a try's point lies in a room near the caster's.
  No other entry steps the caster's or the target's seed before its boundary or return. Between do 140's count step and
  its tries, `0x0063EFA0` runs on the caster; the cases reach only its default arm, which draws nothing; Baal's arm
  draws two or three `RNG_Range` on the caster's seed (§ 7, `[I]`). (run:2026-10-21-cat-emu-8c,
  fn:sub_005D1F70_SkillDo131OverseerWhip@0x005D1F70, fn:sub_005D2C20_SkillDo140BaalTentacle@0x005D2C20)
- [C] (ADR-0021; § 3) **The missile casts.** Do 130 ends at the first of calc1 `MissileCreate` calls of its helper
  `0x005D1C30` (flags 3, the target point, target words `(0, 1)` the first of four `.rdata` offsets, `+0x54` the
  callback `0x005C9290`); do 132 at `SkillMissileCreate(srvmissilea + the caster's class chain position)`; do 136 at
  `MissileCreateAt(caster; id, lvl, srvmissilea, 0, 0)`; do 139 at `SkillMissileCreate(srvmissilea)`; do 148 and 149 at
  `SkillMissileCreateLob` (the `lob` bit) or `SkillMissileCreate` with `srvmissilea` plus the caster's monster-data byte
  `+0x0E` (do 148) or `+0x0F` (do 149) — the two bodies differ in that one byte only; start 63 at `STATE_Set(target,
  118, 1)` for a monster caster with an owner and a target not in state 118. (run:2026-10-21-cat-emu-8c)
- [C] (ADR-0021; § 4) **The hits, the curses and the states.** Do 128 ends at `0x0058F730(ECX game, EDX caster; &block)`
  with the block's words `1`, the target's type and guid, and `game +0xA8 + max(calc1, 1)`; do 134 at
  `SkillRollPhys(ECX caster, EDX &packet; id, lvl)` with `+0x00` = `1 | HitFlags`, `+0x04` = `ResultFlags`, `+0x60` =
  `HitClass`; do 137 at `STATE_Set(target, 104, 1)` for a target that passes `0x00645590`; do 131 at
  `STATE_ApplyTimed` with the timed block (caster, target, id, level, `auralencalc`, −1, 0, `auratargetstate`, no
  callback) through its helper `0x005D1D70`, or, for a drawn value not below calc1 and a target not yet in the state,
  at its class-change helper `0x005D1E10` (observed); do 133 at `STATE_ApplyTimed` with state 110, length 0 and the
  callback `0x005D21B0`, for a live monster target of no base 546 or 551, not in state 110, alignment not 2.
  (run:2026-10-21-cat-emu-8c)
- [C] (ADR-0021; § 5) **Moves, spawns and links.** Start 61 ends at `UnitSetStat(caster, 6, stat 7, 0)` inside
  `0x005CC960` (a monster caster with a room) or at `PATH_SetMarkMask(path, 0x100)` after clearing `+0xC4` bits 1–3
  (no room); start 62 returns 1 with `SkillSummonClass(caster, 1)`'s class, x, y and mode in the used node's `+0x18`,
  `+0x1C`, `+0x20`, `+0x24`; do 135 ends at `SpawnAtPos(ECX game, EDX room; x, y, class, mode, −1, 0)` from those four
  node words when `RoomAtSubtile` finds a room; do 129 ends at `UnitTeleport(caster; 0, the target point, 0, 0)` for a
  caster with an owner, at **do 98 called directly** (`0x005D1B75`, same arguments) for a caster with neither owner
  nor target, or at `UnitTeleport(caster; the target's room and position, 1, 0)` for a live ownerless target; do 140 at
  `SpawnAtPos(game, room; x, y, 0, 1, −1, 0)` (the class and mode from `0x0063EFA0`'s default arm); do 147 at
  `0x006505E0(unit, its owner)`. (run:2026-10-21-cat-emu-8c)
- [I] **The data joins.** Siege Beast Stomp (301) has `srvmissilea` −1, so do 134 returns 0 for the stock row before
  its packet (its `srvmissilea` is a gate only, never created). Imp Teleport (330) has `aurastate` 143 (`attached`),
  whose `srvactivefunc` is 147: do 129 tests its `aurastate` only as a gate, its attach and detach helpers set and clear
  state 143 by the constant `0x8F`. Overseer Whip (295) has `auratargetstate` 141 (`bloodlust`), calc1 `par1` (65),
  `summon` 461 (`suicideminion1`), `summode` 8; Impregnate (300) `summon` 551 (`painworm1`). The bases do 131 and 133
  test are MonStats rows 453 `minion1`, 546 `putriddefiler1` and 551 `painworm1`. Baal (`baalcrab` 544, `baalclone`
  570, `uberbaal` 709) and the stock users of the other rows are in § 1. (`rows.txt`, tbl:Skills.txt:srvmissilea,
  tbl:MonStats.txt:BaseId)
- [I] After, from the reading: do 128's overlay on the target; do 129's attach (`0x005D18E0`: an imp, base 492,
  and a base-435 or 441 target (`barricadetower`, `siegebeast1`): state 143 on, each the other's owner) and detach
  (`0x005D19D0`); do 130's further vines (index `i & 3`); do 131's class change (`0x005D1E10`); do 133's end callback
  (`0x005D21B0`: the painworm spawn from a dead unit); do 134's elemental roll and area hit; do 135's second spawn try
  (mode argument 4) and the spawn's flags, owner and `sumoverlay`; do 136's range from calc1 and the distance; do 137's
  `0x0064C040` and `0x00570590`; do 139's missile `+0x2C`/seed word from the offsets; do 140's spawn flags and owner;
  start 61's revive after `UnitSetStat`; start 63's missile and `0x00571AA0`. (0x005D18C1, 0x005D18E0–0x005D1AAC,
  0x005D1C88–0x005D1CC1, 0x005D1E10–0x005D1F64, 0x005D21B0–0x005D2249, 0x005D23CB–0x005D23FE, 0x005D2539–0x005D25A1,
  0x005D2642–0x005D26B8, 0x005D2777–0x005D2793, 0x005D29F0–0x005D29FB, 0x005D2E0E–0x005D2E2A, 0x005CC996–0x005CCA5C,
  0x005D2AB2–0x005D2AF8)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005D1BF0` | `sub_005D1BF0_SkillSt61SelfResurrect` | start 61 (Self-resurrect) | I |
| `0x005D2420` | `sub_005D2420_SkillSt62MinionSpawner` | start 62 (MinionSpawner) | I |
| `0x005D2A10` | `sub_005D2A10_SkillSt63CorpseCycler` | start 63 (CorpseCycler, VineCycler) | I |
| `0x005D1800` | `sub_005D1800_SkillDo128CryHelp` | do 128 (Cry Help) | I |
| `0x005D1AB0` | `sub_005D1AB0_SkillDo129ImpTeleport` | do 129 (Imp Teleport) | I |
| `0x005D1CD0` | `sub_005D1CD0_SkillDo130VineAttack` | do 130 (Vine Attack) | I |
| `0x005D1F70` | `sub_005D1F70_SkillDo131OverseerWhip` | do 131 (Overseer Whip) | I |
| `0x005D2090` | `sub_005D2090_SkillDo132ImpFireMissile` | do 132 (Imp Fire Missile) | I |
| `0x005D2250` | `sub_005D2250_SkillDo133Impregnate` | do 133 (Impregnate) | I |
| `0x005D2320` | `sub_005D2320_SkillDo134SiegeStomp` | do 134 (Siege Beast Stomp) | I |
| `0x005D2490` | `sub_005D2490_SkillDo135MinionSpawn` | do 135 (MinionSpawner) | I |
| `0x005D25B0` | `sub_005D25B0_SkillDo136DeathMaul` | do 136 (DeathMaul) | I |
| `0x005D26F0` | `sub_005D26F0_SkillDo137FenrisRage` | do 137 (fenris rage) | I |
| `0x005D2940` | `sub_005D2940_SkillDo139BaalColdMissiles` | do 139 (Baal Cold Missiles) | I |
| `0x005D2C20` | `sub_005D2C20_SkillDo140BaalTentacle` | do 140 (Baal Tentacle) | I |
| `0x005D2B20` | `sub_005D2B20_StateDo147Attached` | do 147 (States `srvactivefunc` of 143 `attached`) | I |
| `0x005CDFB0` | `sub_005CDFB0_SkillDo148DoomKnightMissile` | do 148 (DoomKnightMissile) | I |
| `0x005CE0B0` | `sub_005CE0B0_SkillDo149NecromageMissile` | do 149 (NecromageMissile) | I |
| `0x005D18E0` | `sub_005D18E0_ImpAttach` | do 129's attach `(ECX game, EDX imp; target, id, lvl)` | I |
| `0x005D19D0` | `sub_005D19D0_ImpDetach` | do 129's detach `(ECX game, EDX imp; owner, id, lvl)` | I |
| `0x005D1C30` | `sub_005D1C30_VineCreateRow` | do 130's helper `(EAX caster, EDI game, EBX n; m, id, lvl)` | I |
| `0x005D1D70` | `sub_005D1D70_WhipApplyState` | do 131's timed state `(ECX target, EDI id, EBX lvl; caster)` | I |
| `0x005D1E10` | `sub_005D1E10_WhipChangeClass` | do 131's class change `(EAX id, EBX game, ESI target; caster, lvl)` | I |
| `0x005D2140` | `sub_005D2140_ImpregnateTest` | do 133's target test `(EDX target)` | I |
| `0x005D21B0` | `sub_005D21B0_ImpregnateEndCb` | do 133's state callback (the painworm spawn) | I |
| `0x005CC960` | `sub_005CC960_MonReviveInPlace` | start 61's helper (also called from do 97, `0x005CCBF5`) | I |
| `0x0063EFA0` | `sub_0063EFA0_SpawnClassByBase` | do 140's class, point and mode by the caster's MonStats base (4 callers) | I |
| `0x006505E0` | `sub_006505E0_PathFollowUnit` | `(unit, other)`: the unit's path to the other's point (5 callers) | I |
| `0x0058F730` | `sub_0058F730_MonHelpBlock` | `(ECX game, EDX monster; &block)`: do 128's boundary (10 callers) | I |
| `0x00574370` | `sub_00574370_MonChangeClass` | `(ECX game, EDX monster; class, mode)`: called by `0x005D1E10` | I |

## Walkthrough

### 1. The table slots, the stock rows and the callers

- [C] `g_SkillStartFuncs[61..63]` and `g_SkillDoFuncs[128..137, 139, 140, 147..149]` are the Functions table's
  addresses (`table_entries=18`). (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [I] **Stock rows** (`rows.txt`, 17 rows, the `CHECK` lines complete; users from MonStats `Skill1`–`Skill8`): do 128
  on 290 Cry Help (calc1 `ln12`, Params 100, 20; the overseers); start 61 on 293 Self-resurrect; do 130 on 294 Vine
  Attack (`plague vines`, calc1 `min(24,ln12)`); do 131 on 295 Overseer Whip (the overseers, Nihlathak); do 132 on 299
  Imp Fire Missile (`impmiss21`, calc1 `lvl-1`; the imps); do 133 on 300 Impregnate (the putrid defilers); do 134 on 301
  Siege Beast Stomp (`srvmissilea` none); start 62 + do 135 on 302 MinionSpawner (the minion spawners, the ancient
  statues, Nihlathak); start 63 on 307 CorpseCycler (`recycler delay`, `cycleoflife`) and 325 VineCycler (`vine recycler
  delay`); do 136 on 308 DeathMaul (`death mauler`, calc1 96); do 137 on 314 fenris rage (`aurastate` 138); do 140 on
  315 Baal Tentacle and do 139 on 318 Baal Cold Missiles (`baal cold maker`; Baal, his clone, Uber Baal); do 129 on 330
  Imp Teleport (the imps, Nihlathak); do 148 on 335 DoomKnightMissile (`undeadmissile1`; doom knights 2, 3 and the
  `dkmag`s); do 149 on 338 NecromageMissile (`necromage1`). States row 143 (`attached`) is the one with
  `srvactivefunc` 147. No row of the batch has the `lob` bit. (`rows.txt`, tbl:Skills.txt:srvstfunc,
  tbl:Skills.txt:srvdofunc, tbl:States.txt:srvactivefunc)
- [I] **Callers.** No entry of the batch is called from outside the two tables: a scan of every `call`/`jmp` operand
  finds none, and each entry's address occurs once as a dword in the image file (`entry_words=18`). **Do 98
  (`0x005CCC80`) has one direct caller, do 129 at `0x005D1B75`** (the `lane/p46m13` review's carried item); its
  table slot is its other way in. The batch's own helpers have one caller each but `0x005D2140` (also `0x005EFA5E`) and
  `0x005CC960` (also do 97, `0x005CCBF5`); `0x005D21B0` is called by no instruction and taken as an operand once
  (`0x005D22F7`, do 133's block). (`static.txt` `calls of` lines)

### 2. Emulation: the `8c` families

The method is skills/0016's and 0017's, with four families on one memory spec (`mem_8c`): `g_pDataTables` pointed at a
scratch DataTables, and set in the spec the Skills (count 3), Missiles (count 48), ItemStatCost, MonStats (count 4, or
**600 in `curse_8c`** so that `MonClassCheck` admits 453, 546 and 551), MonStats2, States and PetType counts, the calc
pool, DataTables `+0xD4`, `+0x150` and `+0xBC0`, `MONSTATS_GetClassChainPos`'s table and count and
`MissileSpeedAtLevel`'s missile table and count; the allocator and the fatal path are guarded. Every case dumps the
stack, both seeds (caster and target `+0x20`), the caster's `+0xC4` and both argument slots; `move_8c` adds the used
node's `+0x18`–`+0x27` for start 62. Each dumped byte is written by the case.

Emulated, not observed: the helpers of 8a and 8b (`UNIT_GetTargetUnit`, `SKILLS_GetTargetXY`, `UNIT_GetUsedSkill` and
the node getters and setters, `SkillSummonClass` with its MonStats path and `0x0058F710`,
`MONSTATS_GetClassChainPos`, `RoomAtSubtile`, `UnitGetRoom`, `UnitGetSubX/Y`, `UnitIsDead`, `UNIT_HasState`,
`0x006259B0`, `0x00645590`/`0x006455E0` with the state set at `+0x150` and MonStats2 flags 7 and 12,
`sub_0058F0D0_MonsterOwner`, `STATS_GetUnitStat`, `RNG_Range`, `SKILLS_EvalCalc` with constant programs, `GameFindUnit`,
`memset`), and new here: `sub_00552FD0_UnitGetOwner` on the caster and the target (`+0xC8` bit 10, `+0x94`, `+0x98`),
`sub_00463860_MonBaseId` with `sub_00463900_MonClassCheck`, `sub_0046ACE0_MissileRec`, and the batch's helpers
`0x005D1C30` (up to its first `MissileCreate`), `0x005D1D70` (up to `STATE_ApplyTimed`), `0x005D2140`, `0x005CC960`
(up to `UnitSetStat`), and `0x0063EFA0` in its default arm only (§ 5). Observed (new): `0x0058F730`, do 98
`0x005CCC80`, `PATH_SetMarkMask` `0x00648C30`, `0x006505E0`, and the batch's own `0x005D1E10`; `MissileCreate`,
`SkillMissileCreate`, `SkillMissileCreateLob`, `MissileCreateAt`, `SkillRollPhys`, `STATE_Set`, `STATE_ApplyTimed`,
`UnitSetStat`, `UnitTeleport` and `SpawnAtPos` as in earlier batches.

**Register arguments read before written** (ruling 1 of the `lane/p46m8` review): `0x0058F730` (`test edx, edx` at
`0x0058F734`, `mov [ebp−0x4], ecx` at `0x0058F736`); do 98 as an entry (`mov esi, edx` at `0x005CCC88`, `mov [ebp−0x8],
ecx` at `0x005CCC8F`); `0x005D1E10` (`test eax, eax` at `0x005D1E16`, `ESI` at `0x005D1E69`, `EBX` at `0x005D1E9C`,
none written before, the calls between it and its entry preserving `EBX` and `ESI`); `PATH_SetMarkMask` and
`0x006505E0` take stack arguments only; the others as in skills/0008–0017.

**Nested boundaries** (each compared at its absolute stack slot): do 130's return from `0x005D1C30` (`0x005D1D5C`) at
`0x7FEFFFDC`; do 131's from `0x005D1D70` (`0x005D2051`) at `0x7FEFFFE0`; start 61's from `0x005CC960` (`0x005D1C09`)
at `0x7FEFFFF8`.

- [C] Four families, **8 800 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other than
  at a boundary; every negative control fails, and the site control fails on all 2 376 matched boundary cases (23
  function, boundary and return-address triples, each a `site` line; 892 + 370 + 227 + 887) (`check.txt`;
  run:2026-10-21-cat-emu-8c):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `miss_8c` | do 130, 132, 136, 139, 148, 149, start 63 | 3 200 | no chain position (77); bytes `+0x0E`/`+0x0F` swapped (152); `lob` inverted (271); offset tables swapped (67); state 118 ignored (38) | MissileCreate @0x005D1CBA (in 0x005D1C30); SkillMissileCreate @0x005D2113, @0x005D29E1, @0x005CE090, @0x005CE190; SkillMissileCreateLob @0x005CE06F, @0x005CE16F; MissileCreateAt @0x005D263B; StateSet @0x005D2AB2; returns 0, 1 |
  | `hit_8c` | do 128, 134, 137 | 1 200 | calc1 not floored at 1 (73); no `1 |` (87); corpse test ignored (100) | 0x0058F730 @0x005D18A7; RollPhys @0x005D23CB; StateSet @0x005D2777; returns 0 |
  | `curse_8c` | do 131, 133 | 2 000 | the draw test inverted (47); no draw (63); bases 546/551 accepted (75); alignment 2 accepted (19) | ApplyTimed @0x005D1DF0 (in 0x005D1D70), @0x005D2303; 0x005D1E10 @0x005D206F; returns 0 |
  | `move_8c` | start 61, 62, do 129, 135, 140, 147 | 2 400 | count by `low mod 4` (286); try x and y swapped (145); owner ignored (54); mode and x swapped (359); no-room spawn (175); `+0xC4` bits kept (90) | UnitSetStat @0x005CC996 (in 0x005CC960); SetMarkMask @0x005D1C1E; do 98 @0x005D1B7A; UnitTeleport @0x005D1B42, @0x005D1BBC; SpawnAtPos @0x005D2535, @0x005D2E0C; 0x006505E0 @0x005D2B33; returns 0, 1 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 68 of 68 pins): `g_BitMask32` (with the `lob` mask byte
  `0x006CE26C`), the hash offsets, the `CALC_Eval` jump table, do 130's offsets `0x006E3254`/`0x006E3264` (`.rdata`,
  `(0,1) (0,−1) (1,0) (−1,0)`), and the skills calc function count `0x007457AC` (`.data`, as in 8b). Skills, Missiles,
  MonStats, MonStats2, the stat lists and state words, the nodes, the paths, the rooms and the units are scratch records
  written one field per field read. (run:2026-10-21-cat-emu-8c)
- [C] **Every control and its deciding class** (ruling 4 of the `lane/p46m5` review; each class counted from the case
  files by a predicate on the written inputs, the 18 `CLASS` lines of `check.txt`, each equal to its control's
  failures). The thinnest: `align_any` (19) the do 133 live monster targets of another base, not in state 110, with
  alignment 2 (a wrong reading, no alignment test, reaches `STATE_ApplyTimed` where the code returns 0, and cannot match
  by chance); `st118_any` (38) the start 63 targets in state 118 (the same: `STATE_Set` against a return); `draw_inv`
  (47) the do 131 draws with the target not in the state (the inverted test reaches the other boundary,
  `0x005D1E10` against `0x005D1D70`'s `STATE_ApplyTimed`). Three families have a control failing 90 or more (`lob_inv` 271,
  `corpse_any` 100, `mode_x` 359); `curse_8c`'s largest are `base_any` 75 and `seed_none` 63, each deciding under
  reverser rule 10 (the wrong reading reaches a `STATE_ApplyTimed` where the code returns 0, or a seed compared in every
  case). (run:2026-10-21-cat-emu-8c)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills, Missiles,
  MonStats columns `[C]` by layout; unit, path, node, packet, state-word and stat-list offsets `[I]`), and nothing here
  says when the game runs these functions or on which seed state. (run:2026-10-21-cat-emu-8c)

### 3. The missile casts: do 130, 132, 136, 139, 148, 149 and start 63

- [C] (ADR-0021) **Do 130** (`0x005D1CD0`, Vine Attack): a bad id → 0; `srvmissilea` `m` (s16) not in `(0, count)` → 0;
  bit 6 set; `n` = calc1, `n ≤ 0` → 0; else `0x005D1C30(EAX caster, EDI game, EBX n; m, id, lvl)` and 1 whatever it
  does. The helper zeroes a 0x5C-byte block and writes flags 3, owner the caster, class `m`, skill, level, `+0x54` =
  `0x005C9290` (`sub_005C9290_MissCbReseedPathXPlusArg`); `SKILLS_GetTargetXY` writes the point into `+0x14`/`+0x18`,
  none → return; else, for `i` from 0, target words `+0x1C`/`+0x20` = `0x006E3254[i & 3]`, `0x006E3264[i & 3]`, `+0x58` =
  `i`, `MissileCreate` at `0x005D1CBA` (the helper's return `0x005D1D5C` at `0x7FEFFFDC`). After, `[I]`: `n − 1` more
  through the four offsets. (run:2026-10-21-cat-emu-8c, 0x005D1C30–0x005D1CB5)
- [C] (ADR-0021) **Do 132** (`0x005D2090`, Imp Fire Missile): a bad id or `m` not in `(0, count)` → 0; bit 6;
  `MONSTATS_GetClassChainPos(caster's class, 0, &pos)` with the out pointer **the id argument's slot**, then
  `SkillMissileCreate(ECX game, EDX m + pos; caster, id, lvl, 0, 0, 0, 0, 0)` at `0x005D2113` (the id from a register,
  not the overwritten slot; `m + pos` not range-tested). The caster's class is read whatever its type (a null caster
  would give −1; the entry is never called with one in the cases). As 8a's do 85. (run:2026-10-21-cat-emu-8c,
  0x005D20E6–0x005D210E)
- [C] (ADR-0021) **Do 136** (`0x005D25B0`, DeathMaul): a bad id or `m` not in `(0, count)` → 0; `SKILLS_GetTargetXY`
  none → 0 (no bit 6); bit 6; `MissileCreateAt(ECX game, EDX caster; id, lvl, m, 0, 0)` at `0x005D263B`. After, `[I]`:
  calc1 above 0 to `0x00621780(missile, calc1)`; the range `r` from `MISSDATA_GetRange` rescaled by the distance `d`
  to the point (`UnitDistance`; below 1 taken as 1): `d·r / 24 + r / 2` for `d` below 10, `d·r / 12` from 10 (each
  division toward 0, the `0x2AAAAAAB` multiply), into `SetRange` and `SetRemaining`. (run:2026-10-21-cat-emu-8c, 0x005D2602–0x005D2636)
- [C] (ADR-0021) **Do 139** (`0x005D2940`, Baal Cold Missiles): a bad id or `m` not in `(0, count)` → 0; bit 6;
  `SKILLS_GetTargetXY` none → 0; `SkillMissileCreate(ECX game, EDX m; caster, id, lvl, 0, 0, 0, 0, 0)` at `0x005D29E1`.
  After, `[I]`: a created missile gets `MISSDATA_SetSeedLow(missile, −dy)` and `MISSDATA_SetParam2C(missile, dx)`,
  `(dx, dy)` the point minus the caster's position. (run:2026-10-21-cat-emu-8c, 0x005D298B–0x005D29DC)
- [C] (ADR-0021) **Do 148** (`0x005CDFB0`, DoomKnightMissile) and **do 149** (`0x005CE0B0`, NecromageMissile): a bad
  id → 0; no target → 0; `m` (s16) not in `[0, count)` → 0 (0 admitted); `m' = m + b`, `b` the byte `+0x0E` (do 148) or
  `+0x0F` (do 149) of a monster caster's data (`U+0x14`; 0 for another type or no data); `m' ≥ count` → 0;
  `MissileRec(m')` none → 0; bit 6; Skills `+0x04` `lob` bit (the mask byte `0x006CE26C`) → `SkillMissileCreateLob`,
  else `SkillMissileCreate`, both `(ECX game, EDX m'; caster, id, lvl, 0, 0, 0, 0, 0)` (do 148 at `0x005CE06F` /
  `0x005CE090`, do 149 at `0x005CE16F` / `0x005CE190`). `static.txt`: 101 instructions each, one differing (the byte
  offset). (run:2026-10-21-cat-emu-8c, 0x005CE012–0x005CE08B, 0x005CE112–0x005CE18B)
- [C] (ADR-0021) **Start 63** (`0x005D2A10`, CorpseCycler, VineCycler): a caster not a monster → 0; a bad id or `m` not
  in `(0, count)` → 0; `MonsterOwner(caster)` none → 0; no target → 0; the target in state 118 → 0; else
  `STATE_Set(target, 118, 1)` at `0x005D2AB2`. After, `[I]`: `0x0064C040(target)`, a zeroed block with owner the
  caster's owner, source the target, class `m`, skill, level, `MissileCreate`, then `0x00571AA0(ECX caster, EDX target;
  id, 1, 0, 0, 0)` and 1. (run:2026-10-21-cat-emu-8c, 0x005D2A81–0x005D2AAD)

### 4. The hits, the curses and the states: do 128, 131, 133, 134, 137

- [C] (ADR-0021) **Do 128** (`0x005D1800`, Cry Help): a bad id → 0; no target, or a caster not a monster → 0; else
  frame words at `EBP − 0x18`…`−0x0C`: `1`, the target's type (`T+0x00`), its guid (`T+0x0C`), `game +0xA8 +
  max(calc1, 1)` (a 32-bit sum, § 6); `0x0058F730(ECX game, EDX caster; EBP − 0x20)` at `0x005D18A7` (the block's first
  two words unwritten). After, `[I]`: Skills `srvoverlay` (`+0x4E`) in `(0, overlay count)` →
  `UnitSetOverlayStat(target, ovl, 0)`; 1. (run:2026-10-21-cat-emu-8c, 0x005D185D–0x005D18A2)
- [C] (ADR-0021) **Do 131** (`0x005D1F70`, Overseer Whip): a bad id or `auratargetstate` (`+0x82`, s16) not in
  `[0, States count)` → 0; no target, or a dead one → 0; for a monster target with
  `MonClassCheck(MonBaseId(target)) = 453`: `r = RNG_Range(caster's seed, 100)` and, when `r` is not below calc1 and the
  target is not in the state, `0x005D1E10(EAX id, EBX game, ESI target; caster, lvl)` at `0x005D206F` (observed); in
  every other case `0x005D1D70(ECX target, EDI id, EBX lvl; caster)`, which writes the timed block (caster, target, id,
  lvl, `auralencalc` (`+0x60`) evaluated, −1, 0, `auratargetstate`, 0) and calls `STATE_ApplyTimed(ECX &block)` at
  `0x005D1DF0` (the helper's return `0x005D2051` at `0x7FEFFFE0`). The compare is signed (`setl`), so a calc1 of 0 or
  below never applies the state by the draw. After, `[I]`: `SKILLS_ApplyAuraStats` on the timed list; the class change
  (§ 4 last bullet). (run:2026-10-21-cat-emu-8c, 0x005D1FAA–0x005D206A, 0x005D1D70–0x005D1DEB)
- [C] (ADR-0021) **Do 133** (`0x005D2250`, Impregnate): a bad id → 0; bit 6 (a non-null caster); no target → 0;
  `0x005D2140(target)`: a monster, alive, `MonClassCheck(MonBaseId)` neither 546 nor 551, not in state 110 (`0x6E`), and
  `0x006259B0(target)` (its alignment) not 2, else 0; then `STATE_ApplyTimed` with the block (caster, target, id, lvl,
  0, −1, 0, 110, `0x005D21B0`) at `0x005D2303`; after, `[I]`, 1. (run:2026-10-21-cat-emu-8c, 0x005D2289–0x005D22FE,
  0x005D2140–0x005D219C)
- [C] (ADR-0021) **Do 134** (`0x005D2320`, Siege Beast Stomp): a bad id or `m` not in `(0, count)` → 0; bit 6; a
  zeroed 0x70-byte packet at `EBP − 0x74` with `+0x00` = `1 | HitFlags` (`+0x130`), `+0x04` (word) = `ResultFlags`
  (`+0x12E`), `+0x60` = `HitClass` (`+0x134`) when not 0; `SkillRollPhys(ECX caster, EDX &packet; id, lvl)` at
  `0x005D23CB`. After, `[I]`: `SKILLS_RollElemDamage`, the radius `aurarangecalc` (`+0x64`), `AreaHitAt(ECX game, EDX
  caster; 0, 0, radius, &packet, 0)`, 1. (run:2026-10-21-cat-emu-8c, 0x005D2382–0x005D23C6)
- [C] (ADR-0021) **Do 137** (`0x005D26F0`, fenris rage): a bad id or `aurastate` (`+0x80`) not in `[0, States count)`
  → 0; bit 6; no target → 0; `0x00645590(target)` (a corpse of MonStats2 flags 7 and 12, mode 12, outside the state set
  `+0x150`) 0 → 0; else `STATE_Set(target, 104, 1)` at `0x005D2777`. After, `[I]`: `0x0064C040(target)`,
  `0x00570590(ECX game, EDX caster; caster, aurastate, id, lvl)` (a timed self-state with a stat list), 1.
  (run:2026-10-21-cat-emu-8c, 0x005D2728–0x005D2772)
- [I] **Do 131's class change** (`0x005D1E10`, read, after the boundary): `SkillSummonClass(ECX caster, EDX 0; id, lvl,
  &lvl slot, 0, 0)` (the Skills `summon`, stock 461, and `summode` into its level slot); for a monster target the class
  steps along its chain from its own position (`MONSTATS_GetClassChainPos`, `MonClassChainStep`), then
  `0x00574370(ECX game, EDX target; class, mode)`, `0x005B0E00(…, 0xF)`, a monster command and mode, `STATE_Set(target,
  142, 1)`, a stat list in state 142 with stat 355 = the class, and `sumumod` (`+0xE4`) in `(0, 43)` applied.
  (0x005D1E47–0x005D1F5B)

### 5. Moves, spawns and links: start 61, 62, do 129, 135, 140, 147

- [C] (ADR-0021) **Start 61** (`0x005D1BF0`, Self-resurrect; no id test): a caster not a monster → 0; else
  `0x005CC960(ECX game, EDX caster)`: with a room (`UnitGetRoom`), `UnitSetStat(caster, 6, STATS_GetUnitStat(caster, 7,
  0), 0)` at `0x005CC996` (the helper's return `0x005D1C09` at `0x7FEFFFF8`); with none it returns at once and start 61
  clears `+0xC4` bits 1–3 and calls `PATH_SetMarkMask(path, 0x100)` at `0x005D1C1E`. After, `[I]`: the helper's `+0xC4`
  bits, `0x00573780`, the quest hook, the path mask and pattern; 1. (run:2026-10-21-cat-emu-8c, 0x005D1BF7–0x005D1C19,
  0x005CC960–0x005CC991)
- [C] **Start 62** (`0x005D2420`, MinionSpawner; no id test of its own): no used node → 0; else
  `SkillSummonClass(ECX caster, EDX 1; id, lvl, &mode, &x, &y)` (8a's model: a monster's own MonStats `spawn` class,
  offsets and mode, its link fallback; another caster's Skills `summon`/`summode` at its position) and the node's
  `+0x18` = the class, `+0x1C` = x, `+0x20` = y, `+0x24` = the mode; 1. A non-monster caster with a bad id leaves the
  three outs unwritten (stack words), a case the writer does not make (§ 7). (run:2026-10-21-cat-emu-8c,
  0x005D243E–0x005D2483)
- [C] (ADR-0021) **Do 135** (`0x005D2490`, MinionSpawner): a bad id → 0; no used node → 0; the node's class, x, y, mode
  (`+0x18`–`+0x24`); `RoomAtSubtile(UnitGetRoom(caster), x; y)` none → 0; `SpawnAtPos(ECX game, EDX room; x, y, class,
  mode, −1, 0)` at `0x005D2535`. After, `[I]`: a failed spawn retried with 4 for −1; a spawn gets `+0xC4 |= 0x4020000`,
  the caster as owner and `sumoverlay` (`+0xE6`); 1. (run:2026-10-21-cat-emu-8c, 0x005D24E0–0x005D2530)
- [C] (ADR-0021) **Do 129** (`0x005D1AB0`, Imp Teleport): a bad id or `aurastate` (`+0x80`) not in `[0, States count)`
  → 0; `owner = UnitGetOwner(game, caster)`; with an owner: `SKILLS_GetTargetXY` (its result not tested) and
  `UnitTeleport(ECX game, EDX caster; 0, x, y, 0, 0)` at `0x005D1B42`; without one and with no target: **do 98
  (`sub_005CCC80_SkillMonTeleportDo`) called directly** with `(ECX game, EDX caster; id, lvl)` at `0x005D1B7A`, its
  result returned; a target with an owner, or a dead one → 0; else `UnitTeleport(ECX game, EDX caster; the target's
  room, x, y, 1, 0)` at `0x005D1BBC` (the position from `UnitGetSubX/Y`). After, `[I]`: the detach (owner) or attach
  (target, the teleport succeeding) helper, 1. What do 98 does is skills/0016 § 4's `[C]`; that do 129's no-owner,
  no-target path ends as do 98 does composes the two and stays `[I]`. (run:2026-10-21-cat-emu-8c,
  0x005D1AE9–0x005D1BB7)
- [C] (ADR-0021) **Do 140** (`0x005D2C20`, Baal Tentacle; no id test): no caster → 0; one inline step of the caster's
  seed, `n = difficulty + low mod 3 + 2` (difficulty the game's byte `+0x6D`, the `0xAAAAAAAB` multiply);
  `0x0063EFA0(caster, &class, &x, &y, &mode, difficulty, 0)`; the base point: the target's (types 2, 4, 5 the static
  path `+0x0C`/`+0x10`; others the path position, 0 without a path), else the caster's; then up to `n` tries, each
  two inline steps: `x = low mod 18 + X − 9`, `y = low' mod 18 + Y − 9` (the `0x38E38E39` multiply), and
  `RoomAtSubtile(UnitGetRoom(caster), x; y)`; the first try with a room: `SpawnAtPos(ECX game, EDX room; x, y, class,
  mode, −1, 0)` at `0x005D2E0C`, the remaining count `n − i` compared at `EBP − 0x14`; no room in `n` tries → 1 with
  the seed stepped `1 + 2n` times. **In every case `0x0063EFA0` runs its default arm** (class 0 when MonStats has rows,
  x 0, y 0, mode 1; § 7). After, `[I]`: a spawn gets `+0xC4 |= 0x4020000`, `0x005DE0F0(…, 0xF)`, the caster as owner;
  the loop goes on through all `n` tries (several tentacles); 1. (run:2026-10-21-cat-emu-8c, 0x005D2C3D–0x005D2E07)
- [C] (ADR-0021) **Do 147** (`0x005D2B20`, state 143 `attached`; no id test): `UnitGetOwner(game, unit)` none → 1;
  else `0x006505E0(unit, owner)` at `0x005D2B33`; after, `[I]`, 1. `0x006505E0` (read): the unit's path flags `+0x34`
  bit 3 (the points differ) and bit 0 (the rooms differ), then `PathSetPoint` to the owner's point and room — the
  imp riding its tower or beast. (run:2026-10-21-cat-emu-8c, 0x005D2B23–0x005D2B2E, 0x006505E0–0x00650652)

### 6. Wraps and widths

- [C] Do 128's `game +0xA8 + max(calc1, 1)` (`add edx, eax` at `0x005D1897`) is a 32-bit sum stored as it is: it wraps
  once the frame plus the value passes `0xFFFFFFFF` (`static.txt` `wrap` line: `0xFFFFFFFF + 1` = 0; as s32,
  `0x7FFFFFFF + 1` = −2 147 483 648); the cases draw the frame up to 2³¹ and calc1 over the full 32 bits, and the model
  takes the sum modulo 2³². No compare reads it before the boundary. Do 140's count `n` is at most 255 + 2 + 2 = 259
  (a byte plus a residue below 3), with no wrap; its try offsets `low mod 18 − 9` lie in `[−9, 8]`, added to a 16-bit
  path position or a static path's 32-bit word, the sum taken modulo 2³² (no wrap for a position below 2³¹ − 9).
  (run:2026-10-21-cat-emu-8c, `static.txt`, 0x005D1897, 0x005D2C60–0x005D2C70)

### 7. Case-writer restrictions and what stays unreached

- [I] **`0x0063EFA0`'s switch arms.** The helper switches on the caster's MonStats base: the bases 206, 228, 267, 284,
  298 and 321 through the byte table `0x0063F5BC` (base − 206, 116 entries, `static.txt`), 334 (`suckernest1`) by a
  direct test, and 484, 526, 528, 537 and 544 through a second byte table at `0x0063F644` (base − 484, 61 entries; jump
  table `0x0063F630`), every other base to the default arm. With 4 MonStats rows no case reaches an arm. Baal's base 544
  (`baalcrab`, also Uber Baal's) takes arm `0x0063F473`: unless the class out word already holds 570 (`baalclone`;
  the word is do 140's `EBP − 0x1C`, which do 140 does not write before the call), `RNG_Range(caster's seed, 2)` plus the
  difficulty steps the chain from class 562 (`baaltentacle1`; `MonClassChainStep`) into the class out and the mode is 4; then two
  `RNG_Range(caster's seed, 24)`, `x = SubX + r − 12`, `y = SubY + r' − 12` (outs do 140 overwrites in its tries); with
  the out word 570, only the two position draws and mode 1. So for stock Baal, do 140's draws on the caster's seed are:
  its count step, two or three `RNG_Range` here, then two steps per try. Named here; do 140's own map is covered with
  the default arm's outputs, and this arm is a reading. (0x0063EFF1–0x0063F019, 0x0063F310–0x0063F326,
  0x0063F473–0x0063F566)
- [I] **Start 62 with a non-monster caster and a bad id**: `SkillSummonClass` leaves its outs unwritten, so the node
  gets stack words; the writer gives such a caster a valid id (a value no model can compare; stock casters are
  monsters). (0x005D2459)
- [I] **Null pointers the cases do not give**: do 132's caster class for a null caster (−1, `0x005D2121`); start 61's
  path for a monster without one; do 140's target without a path is covered (0), a caster without a path is not.
- [I] Thin outcomes, each deciding under reverser rule 10 (the wrong reading reaches another boundary or a return):
  do 131's class-change boundary (27 cases), do 129's target teleport (30), do 137's `STATE_Set` (40), do 133's
  `STATE_ApplyTimed` (41). (run:2026-10-21-cat-emu-8c, `check.txt` `site` lines)

## Corrections to earlier findings

- None. The `lane/p46m13` review's carried item (do 129's direct call of do 98 at `0x005D1B75`) is answered in §§ 1
  and 5: it is do 98's only direct caller, reached for a caster with no owner and no target.

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `srvmissilea` (`+0x48`), `calc1` (`+0x138`), `auralencalc` (`+0x060`),
`aurarangecalc` (`+0x064`, after), `aurastate` (`+0x080`), `auratargetstate` (`+0x082`), `srvoverlay` (`+0x04E`,
after), `summon` (`+0xBC`), `summode` (`+0xBF`), `sumumod` (`+0xE4`, after), `sumoverlay` (`+0xE6`, after), `lob`
(`+0x04` bit 1), `ResultFlags`/`HitFlags`/`HitClass` (`+0x12E`/`+0x130`/`+0x134`); `tbl:States.txt:srvactivefunc`;
`tbl:MonStats.txt:BaseId` (`+0x02`), `spawn` and its offsets and mode (`+0x20`–`+0x24`), the chain position (`+0x4B`),
MonStats2 flags 7 and 12; unit `+0x00`, `+0x04`, `+0x0C`, `+0x10` mode, `+0x14` data (`+0x0E`, `+0x0F` bytes, `+0x28`
link), `+0x20` seed, `+0x2C` path (`+0x02`, `+0x06`, `+0x0C`, `+0x10`, `+0x1C`, `+0x58`), `+0x5C` stat list (state
words, the state-105 list's stat 172), `+0xA8` skills, `+0xC4`, `+0xC6`, `+0xC8` bit 10 with `+0x94`/`+0x98` (the
owner); the used node `+0x18`–`+0x24`; game `+0x6D`, `+0xA8`.

## Dead ends

- None in the code. The first emulation (`dev/dev1`) mismatched on 9 do 129 cases from a case-writer error (the
  caster's and the target's owners written as one unit, the second guid overwriting the first); `dev/dev2` and
  `dev/dev3` corrected two deciding classes and tuned the writer for the thin controls. No claim rests on them
  (`dev/notes.txt`).

## Open questions

- [L] What every boundary callee does past its entry (§§ 3–5): `0x0058F730`'s help call, `0x006505E0`'s path follow,
  `0x005D1E10`'s class change, `0x0063EFA0`'s arms for Baal and the other spawners.
- [L] Whether Siege Beast Stomp does anything on the server for the stock row (do 134 returns 0 at its `srvmissilea`
  gate, § 1).
- [L] Everything after each boundary (§§ 3–5), for the harness or the monster-AI plan.
