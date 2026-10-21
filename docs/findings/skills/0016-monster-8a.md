# 0016 — Catalogue batch 8a: the monster skill functions of Skills rows 156–189 (start 42–53, do 83–98, 110, 111)

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 42–53 (`srvstfunc`, `g_SkillStartFuncs`) and do function 83–98,
> 110 and 111 (`srvdofunc`, `g_SkillDoFuncs`) of plan 0046 batch 8a do (the acts 1–3 monster skills and the shared
> monster skills: Fire Hit, the maggots, Andariel's spray, Jump, Swarm Move, the nests, Quick Strike, the gargoyle
> trap, Submerge and Emerge, the infernos, the heals, Resurrect, MonTeleport, the monster and hireling missiles, the
> fetish aura): which Skills, MonStats, Missiles and unit fields it reads, what it makes, which draws it makes on which
> seed, what it returns, and which of that the emulator can confirm?
> **Date:** 2026-10-21   **Plan:** 0046 (Phase 1, batch 8a)   **Status:** for review (`lane/p46m13`)

Static reading of the pinned `Game.exe` with objdump and the lane's Ghidra copy `workspace/ghidra-p46m13` (six of the
twelve start entries have no Ghidra function: they were read from objdump), then emulation under ADR-0015 with
`re/ghidra_scripts/EmuBoundary.java` (unchanged) and the `8a` families of `tools/skills_catalogue_emu.py` (§ 2;
run:2026-10-21-cat-emu-8a in [experiments](experiments.md)). Skills columns are named as in
[Skills](../../tables/Skills.md), MonStats's as in [MonStats](../../tables/MonStats.md), Missiles's as in
[Missiles](../../tables/Missiles.md). The dispatch that runs a start or do function is
[skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart); do 83 and do 98 were read before
(skills/0003 § 4, drlg/0009). Stock values come from `workspace/logs/skills-cat-8a/rows.txt` (`rows.sh` beside it:
the 34 Skills rows that name one of the batch's entries, checked complete against all 357 rows by its `CHECK` lines;
the 52 MonStats rows with a `spawn`).

**Tag convention for this finding** (as skills/0014 and skills/0015). A claim marked **[C] (ADR-0021)** rests on
emulated cases that end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a
function entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site (the
return address at ESP), with a site control that fails every matched boundary case, and where the boundary sits inside
a helper the function called, the helper's return address is compared at its absolute stack slot (§ 2 lists each
slot); (c) the model gives and the checker compares every argument the claim uses (registers the callee reads before
it writes them, stack words, and for a pointer the bytes it points to), every byte written before the call that the
claim uses (the caster's `+0xC4`, `+0x3C`, `+0x4E`, the used node's words, the path's `+0x90`, the two argument
slots), and the state of **the caster's and the target's seeds** at the boundary (both, in every case). Each such claim
names the boundary it ends at; **the callee and all code after it are not covered** and keep `[I]`, marked "after,
`[I]`" in place (reverser review-fixes 13). No claim rests on a callee-saved register that is not a boundary argument.
A plain `[C]` rests on cases that return; a plain `[I]` is a code reading the emulator does not reach.
(run:2026-10-21-cat-emu-8a)

## Answer (summary)

- [C] **The batch.** Thirty entries, each `(ECX game, EDX unit; skill id, level)` with `ret 8`: start 42 `0x005CAE40`,
  43 `0x005CAF80`, 44 `0x005CB170`, 45 `0x005CB270`, 46 `0x005CB4D0`, 47 `0x005CB730`, 48 `0x005CBBF0`, 49
  `0x005CBD10`, 50 `0x005CBF30`, 51 `0x005CC1D0`, 52 `0x005CC220`, 53 `0x005CC240`; do 83 `0x005CAF30`, 84
  `0x005CAFA0`, 85 `0x005CB0C0`, 86 `0x005CB300`, 87 `0x005CB3C0`, 88 `0x005CB580`, 89 `0x005CB940`, 90 `0x005CBC80`,
  91 `0x005CBE00`, 92 `0x005CBF90`, 93 `0x005CC050`, 94 `0x005CC1F0`, 95 `0x005CC4E0`, 96 `0x005CC840`, 97
  `0x005CCB10`, 98 `0x005CCC80`, 110 `0x005CE1B0`, 111 `0x005CE670` (`table_entries=30`). All thirty are emulated:
  five families, **12 600 cases, 0 mismatches**. (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0,
  `static.txt`, run:2026-10-21-cat-emu-8a)
- [C] **Draws before the boundaries.** Only **do 96** (ZakarumHeal, Bestow) draws: `RNG_RangeB(caster+0x20, hi − lo)`
  with `hi = clamp(calc2, 0, 100)` and `lo = min(max(calc1, 0), hi)`, no step for `hi = lo`, before its `UnitSetStat`
  on the target. No other entry steps the caster's or the target's seed before its boundary or return.
  (run:2026-10-21-cat-emu-8a, fn:sub_005CC840_SkillDo96Heal@0x005CC840)
- [C] (ADR-0021; § 3) **The hits.** Start 42 runs **start 32** for a player caster (`0x005D7EA0`, its own
  record, target and town tests up to `0x0056E520`) and returns its result; for any other caster it zeroes a hit
  packet and ends at `COMBAT_MeleeHitTest(target, SKILLS_GetToHit(caster, id, lvl), 0)`. Do 83 and do 92 end at
  `COMBAT_DeliverQueued(target, 0)`, start 50 at `COMBAT_ResolveAndQueue(target, &zeroed packet, 0x80)`; no target
  returns 0 (do 92 and start 42 after their record test, do 83 and start 50 with none). Start 47 (Jump) refuses with
  no used node, no path or state 1, then takes the point `2·target − caster` (with a target) or the path's target point
  (without, writing −1 to the node's `+0x24` first), refuses when `RoomAtSubtile` of the caster's room finds none, and
  ends at `MeleeHitTest` (target) or `COLL_PatternMark(room, x, y, path+0x48, 0x100)` (none). Do 110 sets bit 6 and asks
  `0x00645F00`: a monster with stat 157 > 0 casts missile 27 and with stat 158 > 0 missile 41 **at the stat's value as
  the level** (written into the level argument's slot); otherwise `srvmissilea`, by `SkillMissileCreateLob` when the
  Skills `lob` bit is set, else `SkillMissileCreate`; a player's weapon class goes to the inventory query.
  (run:2026-10-21-cat-emu-8a)
- [C] (ADR-0021; § 4) **The moves and marks.** Start 43 clears `+0xC4` bits 1–3 and ends at `0x00649F70(caster, 1)`;
  start 44 at `UnitTeleport(room, x, y, 0, 0)` with the caster's own room and position; start 45 clears bits 1–3 and
  ends at `COLL_PatternUnmark(room, x, y, 5, 0x1000)`; start 46 writes the target's position into the used node's
  `+0x18`/`+0x1C` and returns 1; start 48 asserts the caster's path inside `UNIT_GetTargetUnit` (`Fatal`), refuses with
  no target or node, writes 5 to the path's `+0x90`/`+0x91` and ends at `PathSetType(path, 2)`; start 49 runs
  `SkillSummonClass(caster, 1)` (a monster's own MonStats `spawn`, `spawnx`/`spawny` offsets, `spawnmode`), writes the
  class, x, y, mode into the node's `+0x18`–`+0x24` and ends at `COLL_PatternMark(RoomAtSubtile(room, x, y), x, y, 1,
  0x100)`; start 51 clears and start 52 sets bits 1–3 and return 1; do 89 and do 91 end at `UNIT_CancelEvents(1, 0)`
  after their node (and path, do 89) tests; do 90 ends at `0x006212C0(caster, calc)` with calc2 (and the node's `+0x0C`
  zeroed) when that word has bit 1, else calc1; do 94 clears the caster's `+0x4E` byte, zeroes `+0x3C` when the frame
  word `+0x44 >> 8` is below 1, and returns 1; do 98 ends at `UnitTeleport(room, x, y, 0, 0)` with the path's target
  point and its room, or the monster owner's room when that point has none. (run:2026-10-21-cat-emu-8a)
- [C] (ADR-0021; § 5) **Spawns, heals and revives.** Do 84 (MaggotEgg) zeroes the caster's `+0x3C` and ends at
  `SpawnNearUnitNoBox(class, mode, −1, 0)` when calc1 > 0, else at `UnitKilled(caster, 1)`; do 86 (MagottDown) sets bit
  6, zeroes `+0x3C` when the frame word is not above 0, and with calc1 > 0 ends at `UnitSetStat(caster, 6, min(s6 +
  MulDiv(s6, calc1, 100), UnitGetMaxHp), 0)` with `s6` its stat 6; do 87 (MagottLay) ends at `SpawnAtPos(ECX game, EDX caster's room; x, y,
  class, mode, −1, 0)` one step from the caster in the direction of the target (§ 5's tables), the direction's byte left
  in the id's slot and the x offset in the level's; do 96 ends at `UnitSetStat(target, 6, …)` after its draw; do 97
  (Resurrect) refuses a target that is not a monster in mode 0 or 12, one with a state of the DataTables `+0xD4` set, or
  one with no room, and ends at `COLL_PatternTestBool(room, x, y, path+0x48, 0x3C01)`. (run:2026-10-21-cat-emu-8a)
- [C] (ADR-0021; § 6) **Missiles and the infernos.** Do 85 adds the caster's MonStats class-chain position (`+0x4B`) to
  `srvmissilea` and ends at `SkillMissileCreate`; do 88 ends at `MissileCreate` with flags `0x20`, owner and source the
  caster and the **target point** one or two table steps from the caster towards the node's point (or the target point
  when the node's is 0), the second step by the animation frame; do 93 ends at `MissileCreate` with flags 3, the
  position a sixth of the way to a point four steps from the caster towards the target, and that point's offsets as the
  target words; do 95 ends at `MissileCreate` with flags `0x25` from the caster's position to the target point with
  `+0x28` = `(VelLev · lvl) / 8 + Vel`, or, with no target point, at the `CancelEvents(0, 0)` of `0x005CC3B0`; start 53
  writes `frame + max(calc2, 1)` to the node's `+0x18` and ends at `STATE_Set(caster, 12, 1)` unless the caster has state
  12 (then 1); do 111 sets bit 6 and ends at the allocation inside `0x0056C210(Param4 + 2·lvl, target x, y)`.
  (run:2026-10-21-cat-emu-8a)
- [I] **The data joins.** Fire Hit (156) is the only start 42 row; Fire Hit has no `srvmissilea`, so do 83 makes no
  missile. Do 110's rows 183 MissileSkill1 and 202 HireableMissile have no `srvmissilea` (a monster casts them only by
  stats 157/158 or, a hireling, by its weapon class), 336 RogueMissile names `rogue1`. MaggotEgg (159), MagottLay (163)
  and the nests (167, 320) take their class from the caster's MonStats `spawn` row: `sandmaggot1..5` → `maggotegg1..5`
  with `spawnmode` S1, and so on (`rows.txt` `MONSPAWN`). The infernos (178, 311, 317, 319, 323, and 193 DiabLight) share
  start 53. (`rows.txt`, tbl:Skills.txt:srvdofunc, tbl:MonStats.txt:spawn)
- [I] After, from the reading: start 32's attack rate; the hit packet's `ResultFlags`/`HitFlags`/`HitClass` and calc1
  damage after `MeleeHitTest` (start 42, 47); do 83's `QueuedHitRemove` and its `SKILLS_SrvStart(id, lvl, 0)` (skills/0003
  § 4); do 84's up to four more spawns (`mode 8`, up to `2n` tries) and `UnitKilled`; the spawned units' `+0xC4` bit 26;
  Jump's and the nest's continuations after `CancelEvents` (do 89's state-2 landing and its path plan, do 91's spawn at
  the node's point with `sumoverlay`); do 95's frame and repeat logic (`0x005CC2E0`, `0x005CC440`, calc3's re-queue);
  do 97's path target and mode; do 111's loop over the units it lists (allies of classes 141–145 or 396–400 passing
  `0x005C3420` get `0x0056EBE0(id, lvl, 0x44, 0x19, 0)`). (0x005CAEDE–0x005CAF1C, 0x005CB027–0x005CB0AC,
  0x005CB982–0x005CBB9D, 0x005CBE62–0x005CBEE0, 0x005CC5DE–0x005CC62F, 0x005CCBE1–0x005CCC6A, 0x005CE6E9–0x005CE772)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005CAE40` | `sub_005CAE40_SkillSt42FireHit` | start 42 (Fire Hit) | I |
| `0x005CAF80` | `sub_005CAF80_SkillSt43MaggotEgg` | start 43 (MaggotEgg) | I |
| `0x005CB170` | `sub_005CB170_SkillSt44MaggotUp` | start 44 (MagottUp) | I |
| `0x005CB270` | `sub_005CB270_SkillSt45MaggotDown` | start 45 (MagottDown) | I |
| `0x005CB4D0` | `sub_005CB4D0_SkillSt46AndarielSpray` | start 46 (AndrialSpray) | I |
| `0x005CB730` | `sub_005CB730_SkillSt47Jump` | start 47 (Jump) | I |
| `0x005CBBF0` | `sub_005CBBF0_SkillSt48SwarmMove` | start 48 (Swarm Move) | I |
| `0x005CBD10` | `sub_005CBD10_SkillSt49Nest` | start 49 (Nest, EvilHutSpawner) | I |
| `0x005CBF30` | `sub_005CBF30_SkillSt50QuickStrike` | start 50 (Quick Strike) | I |
| `0x005CC1D0` | `sub_005CC1D0_SkillSt51Submerge` | start 51 (Submerge) | I |
| `0x005CC220` | `sub_005CC220_SkillSt52Emerge` | start 52 (Emerge) | I |
| `0x005CC240` | `sub_005CC240_SkillSt53Inferno` | start 53 (the infernos, DiabLight) | I |
| `0x005CAF30` | `sub_005CAF30_SkillDo83DeliverRestart` | do 83 (Fire Hit; existing name, skills/0003) | I |
| `0x005CAFA0` | `sub_005CAFA0_SkillDo84MaggotEgg` | do 84 | I |
| `0x005CB0C0` | `sub_005CB0C0_SkillDo85ChainMissile` | do 85 (UnHolyBolt, ShamanFire) | I |
| `0x005CB300` | `sub_005CB300_SkillDo86MaggotDownHeal` | do 86 | I |
| `0x005CB3C0` | `sub_005CB3C0_SkillDo87MaggotLay` | do 87 | I |
| `0x005CB580` | `sub_005CB580_SkillDo88AndarielSpray` | do 88 | I |
| `0x005CB940` | `sub_005CB940_SkillDo89Jump` | do 89 | I |
| `0x005CBC80` | `sub_005CBC80_SkillDo90SwarmMove` | do 90 | I |
| `0x005CBE00` | `sub_005CBE00_SkillDo91Nest` | do 91 | I |
| `0x005CBF90` | `sub_005CBF90_SkillDo92QuickStrike` | do 92 | I |
| `0x005CC050` | `sub_005CC050_SkillDo93GargoyleTrap` | do 93 | I |
| `0x005CC1F0` | `sub_005CC1F0_SkillDo94Submerge` | do 94 | I |
| `0x005CC4E0` | `sub_005CC4E0_SkillDo95Inferno` | do 95 (FetishInferno, the sentries, Baal's, Megademon's, Arctic Blast) | I |
| `0x005CC840` | `sub_005CC840_SkillDo96Heal` | do 96 (ZakarumHeal, Bestow) | I |
| `0x005CCB10` | `sub_005CCB10_SkillDo97Resurrect` | do 97 (Resurrect, Resurrect2) | I |
| `0x005CCC80` | `sub_005CCC80_SkillMonTeleportDo` | do 98 (existing name, drlg/0009) | I |
| `0x005CE1B0` | `sub_005CE1B0_SkillDo110MissileSkill` | do 110 (MissileSkill1, HireableMissile, RogueMissile) | I |
| `0x005CE670` | `sub_005CE670_SkillDo111FetishAura` | do 111 | I |
| `0x00621810` | `sub_00621810_UnitAnimFrames` | `(unit, &a, &b)`: `+0x44 >> 8` (s32), and `+0x48 >> 8` (an object: its mode table) | I |
| `0x00621DC0` | `sub_00621DC0_UnitDirToPoint` | `(unit, x, y)`: `0x0064FDC0` from the unit's path position | I |
| `0x0064FDC0` | `sub_0064FDC0_PathDirectionXY` | `(x0, y0, x1, y1)`: `PathDirection` on `v << 16 + 0x8000` | I |
| `0x0063E7A0` | `sub_0063E7A0_Dir64To8` | `(dir)`: the `.data` byte `0x00745600 + dir` | I |
| `0x0063E7E0` | `sub_0063E7E0_DirOffset` | `(b, &dx, &dy)`: the s8 offsets `0x006EA998 + b`, `0x006EA978 + b` | I |
| `0x0058F710` | `sub_0058F710_MonLinkClass3C` | SkillSummonClass's fallback: a monster's data `+0x28` link's `+0x3C` | I |
| `0x005CC3B0` | `sub_005CC3B0_InfernoEnd` | do 95's end without a target point (`ESI` unit, `EDI` game): `CancelEvents(0, 0)`, then a queued event | I |
| `0x0056C210` | `sub_0056C210_UnitListAround` | `(ECX game, EDX unit; r, x, y)`: allocates a list and searches the units round `(x, y)` | I |
| `0x0063A320` | `sub_0063A320_UnitHasStateInMaskD4` | `sub_0063A130_UnitHasStateInMask` with DataTables `+0xD4` | I |
| `0x00648E70` | `sub_00648E70_PathSetByte90` | `(path, n)`: `+0x90` and `+0x91` = `min(n, 0x4D)` | I |

## Walkthrough

### 1. The table slots, the stock rows and the callers

- [C] `g_SkillStartFuncs[42..53]` and `g_SkillDoFuncs[83..98, 110, 111]` are the Functions table's addresses
  (`table_entries=30`). Six start entries (43, 45, 46, 48, 51, 52) have no function in the Ghidra project; their code
  is read from objdump and emulated from their table address. (data:g_SkillStartFuncs@0x00732140,
  data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [I] **Stock rows** (`rows.txt`, 34 rows, the `CHECK` lines complete): start 42 + do 83 on 156 Fire Hit; do 85 on 157
  UnHolyBolt (`unholybolt1`) and 160 ShamanFire (`shafire1`); start 43 + do 84 on 159 MaggotEgg (calc1 set); start 44 on
  161 MagottUp; start 45 + do 86 on 162 MagottDown (calc1 10); do 87 on 163 MagottLay; start 46 + do 88 on 164
  AndrialSpray (`andarielspray`); start 47 + do 89 on 165 Jump; start 48 + do 90 on 166 Swarm Move (calc1 11, calc2
  19); start 49 + do 91 on 167 Nest and 320 EvilHutSpawner (`sumoverlay` none, `srvoverlay` `spawnedflames`); start 50 +
  do 92 on 168 Quick Strike; do 93 on 172 GargoyleTrap (`shafire3`); start 51 + do 94 on 176 Submerge; do 111 on 177
  FetishAura (Param4 10); start 53 + do 95 on 178, 311, 317, 319, 323, start 53 alone on 193 DiabLight (do 152, batch
  8b); do 96 on 179 ZakarumHeal (calc2 50) and 182 Bestow; start 52 on 180 Emerge; do 97 on 181 and 327; do 110 on 183,
  202, 336; do 98 on 184, 292, 329, 331. No row of the batch has the `lob` bit, `ResultFlags`, `HitFlags` or
  `HitClass`. (`rows.txt`, tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc)
- [I] **Callers.** No entry of the batch is called from outside the two tables but do 98, which do 129 (`0x005D1AB0`,
  batch 8c) calls directly at `0x005D1B75` (unfollowed here): a scan of every `call`/`jmp` operand finds no other
  site, and each entry's address occurs once as a dword in the image file, its table slot (`entry_words=30`). `0x005CC3B0` is called four times: twice in do 95 (`0x005CC5C0`, `0x005CC677`, after
  its missile) and twice in do 152 `0x005CC690` (DiabLight, batch 8b: `0x005CC770`, `0x005CC827`); `0x0056C210` only by do 111. (`static.txt`
  `calls of` lines, 0x005D1B75)

### 2. Emulation: the `8a` families

The method is skills/0015's, with five families sharing one memory spec (`mem_8a`): `g_pDataTables` pointed at a
scratch DataTables, and set in the spec: the Skills, Missiles (count 48 here, so do 110's rows 27 and 41 exist),
ItemStatCost, MonStats, MonStats2, States and PetType counts, the calc pool, DataTables `+0xD4` (do 97's state set),
`+0xBC0`, and `MONSTATS_GetClassChainPos`'s MonStats table and count (`0x0096C6A8`/`0x0096C6B0`); the allocator
`0x0040B430` is observed in `aura_8a` only and guarded elsewhere. Every case dumps the stack, both seeds (caster and
target `+0x20`), the caster's `+0xC4` and both argument slots; families add the node's `+0x0C` and `+0x18`–`+0x27`,
the caster's `+0x3C` and `+0x4C`, the path's `+0x90`. Each dumped byte is written by the case (the emulator keeps memory
between cases; the writer refuses a case otherwise).

Emulated, not observed: `UNIT_GetTargetUnit`, `UNIT_GetUsedSkill`, the node getters and setters, `SKILLS_EvalCalc`
(constant programs), `SKILLS_GetToHit`, `SKILLS_GetTargetXY`, `UnitGetSubX/Y`, `UnitGetRoom`, `RoomAtSubtile`, the
path getters `0x006488C0`/`0x00648900`/`0x00648A00`/`0x00648A10`/`0x00649180`, `UNIT_HasState`, `STATS_GetUnitStat`,
`UnitGetMaxHp`, `UnitGetStat`, `MulDiv`, `RNG_RangeB`, `MissileRec`, `MONSTATS_GetClassChainPos`,
`sub_0056E620_SkillSummonClass` with `sub_0063EA70_SkillSummonRec` and `0x0058F710`, `sub_0058F0D0_MonsterOwner`,
`GameFindUnit`, `MonIsDeathMode`, `0x0063A320` with `sub_0063A130_UnitHasStateInMask`, `0x00645F00`, the weapon
class `0x00623C60` up to its inventory query, `0x00621810`, `0x00621DC0` with `0x0064FDC0` and
`sub_0064FC60_PathDirection`, `0x0063E7A0`, `0x0063E7E0`, `0x00648E70`, start 32 inside start 42, `0x005CC3B0` up to
its `CancelEvents`, `0x0056C210` up to its allocation. Observed (new): `COLL_PatternMark` `0x0064EA90`,
`COLL_PatternUnmark` `0x0064EC10`, `sub_00649F70_UnitCorpseColl`, `sub_005B23C0_SpawnNearUnitNoBox`,
`sub_0057CCB0_UnitKilled`, `sub_005B2F20_SpawnAtPos`, `COMBAT_ResolveAndQueue` `0x0057DBF0`,
`sub_0056EE90_SkillMissileCreateLob`, the allocator `0x0040B430`; `UnitTeleport`, `MeleeHitTest`, `DeliverQueued`,
`CancelEvents`, `0x006212C0`, `PathSetType`, `STATE_Set`, `UnitSetStat`, `COLL_PatternTestBool` (`0x0064D910`),
`MissileCreate`, `SkillMissileCreate`, the inventory query, `0x0056E520` and `Fatal` as in earlier batches.

**Register arguments read before written** (ruling 1 of the `lane/p46m8` review): `SpawnNearUnitNoBox` (`mov esi,
edx` at `0x005B23CB`, `mov edi, ecx` at `0x005B23CD`), `UnitKilled` (`mov ebx, edx` at `0x0057CCB7`, `mov edi, ecx`
at `0x0057CCBC`), `SpawnAtPos` (`mov [ebp−0x24], edx` at `0x005B2F2C`, `mov [ebp−0x28], ecx` at `0x005B2F32`),
`COMBAT_ResolveAndQueue` (`mov edi, edx` at `0x0057DBF7`, `mov [ebp−0x4], ecx` at `0x0057DBFB`),
`SkillMissileCreateLob` (`mov edi, edx` at `0x0056EEA1`, `mov ebx, ecx` at `0x0056EEA3`), the allocator (`mov eax,
ecx` at `0x0040B437`; `EDX` passed on to `0x0040A080` unwritten), `UnitTeleport` (`mov edi, edx` at `0x00554EA9`, `mov
[ebp−0x4], ecx` at `0x00554EAD`); `0x00649F70`, `COLL_PatternMark`, `COLL_PatternUnmark` take stack arguments only;
the others as in skills/0008–0015.

**Nested boundaries** (each compared at its absolute stack slot): start 42's return from start 32 (`0x005CAEA3`) at
`0x7FEFFF70`; do 95's return from `0x005CC3B0` (`0x005CC5C5`) at `0x7FEFFF84`; do 111's return from `0x0056C210`
(`0x005CE6E9`) at `0x7FEFFFD0`, with that helper's three stack arguments above it; do 110's inventory query is reached
through `0x00645F00` and `0x00623C60` (the query's own return address `0x006239BE`, as in batch `ama`).

- [C] Five families, **12 600 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 5 135 matched boundary cases (31
  function, boundary and return-address triples, each a `site` line) (`check.txt`; run:2026-10-21-cat-emu-8a):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `hit_8a` | start 42, 47, 50, do 83, 92, 110 | 2 400 | packet flags `0x40` (249); player and monster swapped (189); state 1 ignored (27); no room test with a target (102); level kept (87); lob bit ignored (25) | AttackRate @0x005D7F16 (st 42 via st 32); MeleeHitTest @0x005CAED8, @0x005CB860; DeliverQueued @0x005CAF5A, @0x005CBFE2; ResolveQueue @0x005CBF76; PatternMark @0x005CB907; SkillMissileCreate @0x005CE23F; Lob @0x005CE295; InvQuery @0x006239BE; returns 0 |
  | `move_8a` | start 43–46, 48, 49, 51, 52, do 89–91, 94, 98 | 2 600 | Emerge sets bits 1–2 only (109); `≤ 1` for `< 1` (200); `+0x4E` kept (200); x and y swapped (101); speed 4 (106); bit 1 ignored (37); Skills path for the nest (112); no owner's room (88) | CorpseColl @0x005CAF93; UnitTeleport @0x005CB1E3, @0x005CCCE4; PatternUnmark @0x005CB2EA; CancelEvents @0x005CB982, @0x005CBE62; Fatal @0x005534A8; PathSetType @0x005CBC2E; 0x006212C0 @0x005CBCFE; PatternMark @0x005CBDD3; returns 0, 1 |
  | `summon_8a` | do 84, 86, 87, 96, 97 | 2 500 | `+0x3C` kept (251); spawn mode 8 (128); percent of the maximum (103); offsets swapped (131); no draw (94); state set ignored (33); mask `0x1C09` (55) | SpawnNearNoBox @0x005CB03E; UnitKilled @0x005CB0B1; UnitSetStat @0x005CB3AC, @0x005CC943; SpawnAtPos @0x005CB4AF; CollTestBool @0x005CCBD2; returns 0, 1 |
  | `miss_8a` | do 85, 88, 93, 95, start 53 | 2 500 | state 12 ignored (84); no chain position (124); axes swapped (162); frame uncapped (27); velocity floored (35) | SkillMissileCreate @0x005CB152; MissileCreate @0x005CB70D, @0x005CC1C1, @0x005CC5DA; CancelEvents @0x005CC415 (in 0x005CC3B0); StateSet @0x005CC2CF; returns 0, 1 |
  | `aura_8a` | do 111 | 600 | radius `Param4 + lvl` (409) | Alloc @0x0056C236 (in 0x0056C210); returns 0 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 52 of 52 pins): `g_BitMask32`, the hash offsets, the
  `CALC_Eval` jump table, the town-level tables, `UNIT_GetSizeX`'s jump table, `PathDirection`'s table `0x006EB7E0`
  (128 rows of 12 bytes, `.rdata`), `0x0063E7E0`'s offsets `0x006EA978`/`0x006EA998`, do 87's and do 88's direction
  bytes `0x006E3138`, `0x006E3140`, `0x006E3188` (all `.rdata`), and two `.data` reads: the skills calc function count
  `0x007457AC` (0 stores, 0 immediates, 7 reads) and `0x0063E7A0`'s byte map `0x00745600`, whose scan of every
  instruction naming `0x007455C0`–`0x007456FF` finds three reads and no store or immediate (the map's own and its two
  neighbours' `0x007455C0`, `0x00745640`). The map's 64 bytes are 0 ×4, 1 ×8, …, 7 ×8, 0 ×4 (`static.txt`). Skills,
  Missiles, MonStats, MonStats2, ItemStatCost, the stat lists, the nodes, the paths, the rooms and the units are scratch
  records written one field per field read. (run:2026-10-21-cat-emu-8a)
- [C] **The weak controls and their deciding classes** (ruling 4 of the `lane/p46m5` review; each class counted from
  the case files by a predicate on the written inputs, the `CLASS` lines of `check.txt`, each equal to its control's
  failures): `state1_any` (27) the start 47 cases with a node and a path, state 1 set, and no target or a target whose
  point beyond lies in a room; `lob_off` (25) the do 110 monster casts with stats 157 and 158 not above 0, `srvmissilea`
  in range and the lob bit; `lvl_keep` (87) the do 110 monster casts with stat 157 or 158 above 0 and other than the
  level; `bit1_off` (37) the do 90 cases with a node whose `+0x0C` has bit 1; `no_owner` (88) the do 98 cases whose path
  point has no room and whose monster caster's owner is found in a room; `d4_any` (33) the do 97 cases with a dead
  monster target in a room and a state of the set; `mask_1c09` (55) the same with no such state, every case reaching
  the collision test; `f_nocap` (27) the do 88 casts with the frame − 4 above 8 and the table byte at frame 8 not `0x63`;
  `vel_shift` (35) the do 95 casts with `VelLev · lvl` negative and not a multiple of 8. Each family has a control
  failing 90 or more (`q40` 249, `f_le1` 200, `keep3c` 251, `axis_swap` 162, `r_lvl1` 409). (run:2026-10-21-cat-emu-8a)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills, Missiles,
  MonStats, MonStats2 columns `[C]` by layout; unit, path, node and stat-list offsets `[I]`), and nothing here says
  when the game runs these functions or on which seed state. (run:2026-10-21-cat-emu-8a)

### 3. The hits: start 42, 47, 50, do 83, 92, 110

- [C] (ADR-0021) **Start 42** (`0x005CAE40`): a bad id → 0; `UNIT_GetTargetUnit` none → 0; a player caster (`[EDX]` =
  0) → start 32 with the same `(ECX, EDX; id, lvl)`, whose result it returns (start 32's record, target and town tests,
  then `0x0056E520(ECX caster, EDX calc3)` at `0x005D7F16`, as skills/0012 § 3); any other caster → a 0x70-byte packet
  zeroed at `[ebp−0x74]`, then `COMBAT_MeleeHitTest(ECX game, EDX caster; target, SKILLS_GetToHit(caster, id, lvl), 0)`
  at `0x005CAED8`, the 0 being the fourth word pushed for `SKILLS_GetToHit`, which pops three (`ret 0xC`). After,
  `[I]`: on a hit, `ResultFlags` and `HitFlags` ORed in, `HitClass` when non-zero, `sub_005A4F50_MonAttackStats`, then
  `COMBAT_ResolveAndQueue(target, &packet, 0x80)` and 1. (run:2026-10-21-cat-emu-8a, 0x005CAE8B–0x005CAF1C)
- [C] (ADR-0021) **Do 83** (`0x005CAF30`): no target → 0; else `COMBAT_DeliverQueued(ECX game, EDX caster; target, 0)`
  at `0x005CAF5A`. After, `[I]`: `QueuedHitRemove`, `SKILLS_SrvStart(id, lvl, 0)` (skills/0003 § 4). **Do 92**
  (`0x005CBF90`): a bad id → 0, no target → 0, else the same call at `0x005CBFE2`. After, `[I]`: `QueuedHitRemove`,
  then `srvmissilea` (or, below 0, a monster's `0x0063E6B0(unit, 1)`) in range → `SkillMissileCreate(…, 0, 0, 0, 0, 1)`
  and 1, else 0. **Start 50** (`0x005CBF30`): no target → 0; else a zeroed 0x70-byte packet at `[ebp−0x70]` and
  `COMBAT_ResolveAndQueue(ECX game, EDX caster; target, &packet, 0x80)` at `0x005CBF76`, then 1 `[I]`. No id test in
  start 50 or do 83. (run:2026-10-21-cat-emu-8a, fn:sub_005CBF90_SkillDo92QuickStrike@0x005CBF90)
- [C] (ADR-0021) **Start 47** (`0x005CB730`, Jump): a bad id → 0; no used node, the caster's `+0x2C` 0, or state 1 set
  (`UNIT_HasState(caster, 1)`) → 0. With a target `T`: the point `(2·Tx − Ux, 2·Ty − Uy)` (`UnitGetSubX/Y`), without:
  the path's `+0x10`/`+0x12` and the node's `+0x24` = −1 (`0x005CB7C5`). `RoomAtSubtile(UnitGetRoom(caster), x, y)`
  none → 0 (the −1 stays). With a target: a packet zeroed at `[ebp−0x84]` and `MeleeHitTest(target,
  SKILLS_GetToHit(caster, id, lvl), 0)` at `0x005CB860`; without: `COLL_PatternMark(room, x, y, path+0x48, 0x100)` at
  `0x005CB907`. After, `[I]`: the hit's flags and calc1 into the packet's `+0x0C`, `SKILLS_RollElemDamage` (`0x0056E0C0`), `ResolveAndQueue`, the
  target's type and guid into the node's `+0x20`/`+0x24`; then `PatternMark` (with a target too), `0x005544B0`, the node's
  `+0x18`/`+0x1C` = the point and `+0x0C` = `0x80`, 1. (run:2026-10-21-cat-emu-8a, 0x005CB829–0x005CB92A)
- [C] (ADR-0021) **Do 110** (`0x005CE1B0`): a bad id → 0, no target → 0; bit 6 set; `r = 0x00645F00(caster,
  &lvl)`: a non-player with `UnitGetStat(157, 0)` > 0 → `r` = 27 (`0x1B`) and the stat written over the level argument,
  else stat 158 > 0 → 41 (`0x29`) and the stat, else 0; a player → its weapon class (`0x00623C60`, ending at the
  inventory query `0x006239BE`; no inventory → class 0 → `r` = −1). `r` not 0 or 31: `MissileRec(r)` none → 0, else
  `SkillMissileCreate(ECX game, EDX r; caster, id, lvl, 0, 0, 0, 0, 0)` at `0x005CE23F`. `r` 0 or 31: `srvmissilea`
  (s16) out of `[0, count)` → 0; else Skills `+0x04` bit 1 (`lob`, tested with `g_BitMask32[1]`) →
  `SkillMissileCreateLob(ECX game, EDX m; caster, id, lvl, 0, 0, 0, 0, 0)` at `0x005CE295`, else `SkillMissileCreate`
  at `0x005CE23F`. A player's weapon class 1 or 7 runs the same stat tests (7 → 31 when both fail); others → −1.
  (run:2026-10-21-cat-emu-8a, fn:sub_00645F00_UnitRangedMissile@0x00645F00)

### 4. Moves and marks: start 43–46, 48, 49, 51, 52, do 89–91, 94, 98

- [C] (ADR-0021) **Start 43** (`0x005CAF80`): `+0xC4 &= ~0xE` (a null unit skips it), `0x00649F70(caster, 1)` at
  `0x005CAF93`; after, `[I]`, 1. **Start 44** (`0x005CB170`): the caster's position (a static path's `+0x0C`/`+0x10`
  for types 2, 4, 5, else `0x006488C0`/`0x00648900`, 0 with no path) and `UnitGetRoom` → `UnitTeleport(ECX game, EDX
  caster; room, x, y, 0, 0)` at `0x005CB1E3`; after, `[I]`: 0 when it fails, else `+0xC4 |= 0xE` and
  `COLL_PatternMark(room, x, y, 1, 0x1000)`, 1. **Start 45** (`0x005CB270`): `+0xC4 &= ~0xE`, then
  `COLL_PatternUnmark(room, x, y, 5, 0x1000)` at `0x005CB2EA`; after, `[I]`, 1. **Start 51** (`0x005CC1D0`) clears and
  **start 52** (`0x005CC220`) sets `+0xC4` bits 1–3, each returning 1 (plain `[C]`, cases that return).
  (run:2026-10-21-cat-emu-8a, 0x005CB1EF, 0x005CC229)
- [C] **Start 46** (`0x005CB4D0`): no target → 0; no used node → 0; else the node's `+0x18` = the target's x and
  `+0x1C` = its y (a static path's dwords for types 2, 4, 5, else its path's `+0x02`/`+0x06`, 0 with no path), and 1.
  (run:2026-10-21-cat-emu-8a, fn:sub_005CB4D0_SkillSt46AndarielSpray@0x005CB4D0)
- [C] (ADR-0021) **Start 48** (`0x005CBBF0`): `UNIT_GetTargetUnit` first, which with the caster's `+0x2C` 0 reaches
  `Fatal` from `0x005534A8` (its path revalidation); no target → 0; no path → 0; no used node → 0; else
  `0x00648E70(path, 5)` (path `+0x90` = `+0x91` = 5) and `PathSetType(path, 2)` at `0x005CBC2E`. After, `[I]`:
  `PathPlan(path, caster, 0)`; failed → type 1 and plan again; failed again → 0; else the node's `+0x0C` = 1 and 1.
  (run:2026-10-21-cat-emu-8a, 0x005CBC37–0x005CBC74)
- [C] (ADR-0021) **Start 49** (`0x005CBD10`): a bad id → 0; no used node → 0; `SkillSummonClass(ECX caster, EDX 1;
  id, lvl, &mode, &x, &y)`: for a monster its own MonStats row (`+0x20` `spawn` s16 as the class, `+0x22`/`+0x23` s8
  added to its position, `+0x24` s8 the mode, 1 outside `[0, 16)`), a class outside `[0, MonStats count)` replaced by
  `0x0058F710` (the data `+0x28` link's `+0x3C` when `0 < v < count`, else −1); for a non-monster the Skills `summon` and
  `summode` and its position; −1 → 0. Then the node's `+0x18`, `+0x1C`, `+0x20`, `+0x24` = class, x, y, mode and
  `COLL_PatternMark(RoomAtSubtile(UnitGetRoom(caster), x, y), x, y, 1, 0x100)` at `0x005CBDD3` (the room not tested).
  After, `[I]`: `0x005544B0`, `CancelEvents(1, 0)`, 1. (run:2026-10-21-cat-emu-8a, fn:sub_0063EA70_SkillSummonRec@0x0063EA70)
- [I] **SkillSummonClass faults** on a non-monster whose Skills class is refused (`0x0058F710` reads `[0x3C]`) and
  leaves its outs unwritten for a monster whose own class is out of range; the case writer admits neither (§ 2). No
  stock row reaches either: every batch row is a monster skill with a valid id. (0x0058F727, 0x0063EAAB)
- [C] (ADR-0021) **Do 89** (`0x005CB940`, Jump; no id test): no used node → 0; the caster's `+0x2C` 0 → 0; else
  `UNIT_CancelEvents(ECX game, EDX caster; 1, 0)` at `0x005CB982`. After, `[I]`: with the caster's `+0x4E` byte 2, it
  clears it and delivers the queued hit to the node's stored unit; else, by the node's `+0x0C` bit 8, the landing
  (`PatternUnmark`, mark mask `0x100`, collision mask `0x3C01`, path type `0x65`; class `0x4E` restarts the jump), or by
  bit 7 the walk to the node's point at `UnitWalkVelocity`. **Do 91** (`0x005CBE00`): a bad id → 0, no used node → 0,
  else `CancelEvents(1, 0)` at `0x005CBE62`; after, `[I]`: `0x005544B0`, `PatternUnmark` of the node's point, then
  `SpawnAtPos(x, y, class, mode, 1, 0)` from the node's words, bit 26 and 17 on the spawn and the `sumoverlay` overlay.
  (run:2026-10-21-cat-emu-8a, 0x005CB982–0x005CBB9D, 0x005CBE62–0x005CBEF0)
- [C] (ADR-0021) **Do 90** (`0x005CBC80`, Swarm Move): a bad id → 0; no used node → 0; the node's `+0x0C` with bit 1 →
  `+0x0C` = 0 and calc2, else calc1; `0x006212C0(caster, calc)` at `0x005CBCFE`; after, `[I]`, 1.
  (run:2026-10-21-cat-emu-8a, 0x005CBCC8)
- [C] **Do 94** (`0x005CC1F0`, Submerge): `0x00621810` (the caster's `+0x44 >> 8`, signed), the caster's `+0x4E` byte
  = 0, `+0x3C` = 0 when the frame is below 1, and 1; no id test. (run:2026-10-21-cat-emu-8a,
  fn:sub_005CC1F0_SkillDo94Submerge@0x005CC1F0)
- [C] (ADR-0021) **Do 98** (`0x005CCC80`, MonTeleport): the path's `+0x10`/`+0x12` (`0x00648A00`/`0x00648A10`), the room
  `RoomAtSubtile(UnitGetRoom(caster), x, y)`; none → the caster's monster owner (`sub_0058F0D0_MonsterOwner`) and, when
  found, `UnitGetRoom(owner)` (a room not tested against the point); then `UnitTeleport(ECX game, EDX caster; room, x,
  y, 0, 0)` at `0x005CCCE4`. No id test. After, `[I]`: 0 when it fails, else `0x0064C040(caster)`, `+0xC8 |= 0x10000`,
  1. drlg/0009's reading (no town test of its own) holds; the owner fallback is new. (run:2026-10-21-cat-emu-8a,
  0x005CCCE4–0x005CCCFF)

### 5. Spawns, heals and revives: do 84, 86, 87, 96, 97

- [C] (ADR-0021) **Do 84** (`0x005CAFA0`, MaggotEgg): a bad id → 0; `SkillSummonClass(caster, 1; id, lvl, &mode, 0,
  0)` −1 → 0; no used node → 0; the caster's `+0x3C` = 0; `n = calc1`; `n > 0` →
  `SpawnNearUnitNoBox(ECX game, EDX caster; class, mode, −1, 0)` at `0x005CB03E`; else `UnitKilled(ECX game, EDX
  caster; caster, 1)` at `0x005CB0B1`. After, `[I]`: a spawn's `+0xC4 |= 0x04000000`; up to `n − 1` more by
  `SpawnNearUnitNoBox(class, 8, k, 0)` with `k` from 1, `k` raised on each failure, at most `2n` tries and `k < 5`; then
  `UnitKilled(caster, 1)` and 1 on both paths. (run:2026-10-21-cat-emu-8a, 0x005CB042–0x005CB0AC)
- [C] (ADR-0021) **Do 86** (`0x005CB300`, MagottDown): a bad id → 0; bit 6 set; `0x00621810`'s frame not above 0 → the
  caster's `+0x3C` = 0; `n = calc1`; `n ≤ 0` → 1; else `s6 = STATS_GetUnitStat(caster, 6, 0)`, `max =
  UnitGetMaxHp(caster)` (stat 7's value), `v = s6 + MulDiv(s6, n, 100)`, `v ≥ max` → `max`, and `UnitSetStat(caster, 6, v,
  0)` at `0x005CB3AC`; after, `[I]`, 1. (run:2026-10-21-cat-emu-8a, 0x005CB38C–0x005CB3A7)
- [C] (ADR-0021) **Do 87** (`0x005CB3C0`, MagottLay): a bad id → 0; `SkillSummonClass(caster, 1; …, &mode, 0, 0)` −1
  → 0; no target → 0; `d = 0x00621DC0(caster, Tx, Ty)`: `PathDirection` from the caster's path position to the
  target's, each coordinate `v << 16 + 0x8000`, written as a byte over the id argument's slot; `b = 0x006E3138[map[d] &
  7]` with `map` the `.data` bytes `0x00745600`; `(dx, dy) = (s8 0x006EA998[b], s8 0x006EA978[b])`, `dx` written over
  the level argument's slot; the caster's `+0x4E` = 0; `SpawnAtPos(ECX game, EDX UnitGetRoom(caster); Ux + dx, Uy + dy,
  class, mode, −1, 0)` at `0x005CB4AF`. After, `[I]`: a spawn's `+0xC4 |= 0x04000000` and 1, else 0.
  (run:2026-10-21-cat-emu-8a, fn:sub_0064FC60_PathDirection@0x0064FC60)
- [C] (ADR-0021, through do 87's and do 88's boundary arguments) **`PathDirection`** (`0x0064FC60`), as the model
  runs it: the larger and smaller of the two x and of the two y
  (unsigned), the minor difference × `0x7F` over the major (signed `idiv`, 0 for a 0 major), that row of `0x006EB7E0`
  (12 bytes; its third word the value folded), folded by `(−1 − d) & 0xF` when y is the major axis, `& 0x1F` when the
  target's y is not the larger, `& 0x3F` when its x is not smaller, then `+ 8 & 0x3F`. The `(minor << 16) × 0x7F` wraps
  past a minor difference of 257 subtiles, and the ratio then leaves the table: the case writer keeps do 87's and do
  88's points within 250 subtiles (§ 2, `dev/notes.txt`). (run:2026-10-21-cat-emu-8a, 0x0064FCD3)
- [C] (ADR-0021) **Do 96** (`0x005CC840`, ZakarumHeal, Bestow): a bad id → 0; no target → 0; bit 6 set; `hi = calc2`,
  0 below 0, 100 above 99; `lo = calc1`, 0 below 0, at most `hi`; **`pct = lo + RNG_RangeB(caster+0x20, hi − lo)`**;
  `max = UnitGetMaxHp(target)`, `v = MulDiv(max, pct, 100) + STATS_GetUnitStat(target, 6, 0)`; `UnitSetStat(target,
  6, max(v, 1) ≥ max ? max : max(v, 1), 0)` at `0x005CC943`; after, `[I]`, 1. The draw is on **the caster's seed**,
  `noseed` failing 94. (run:2026-10-21-cat-emu-8a, 0x005CC8E5–0x005CC93E)
- [C] (ADR-0021) **Do 97** (`0x005CCB10`, Resurrect): a bad id → 0; no target → 0; bit 6 set; `MonIsDeathMode` (a
  monster in mode 0 or 12) false → 0; `0x0063A320` (the target's state words against the DataTables `+0xD4` set) true
  → 0; `UnitGetRoom(target)` none → 0; else `COLL_PatternTestBool(room, Tx, Ty, path+0x48, 0x3C01)` at `0x005CCBD2`
  (the mask `0x1C09` for a target of type 0, which the death test excludes). After, `[I]`: a free spot → the caster's
  path target, `0x005CC960`, a monster's command mode by `0x005FD7B0`, `srvoverlay`, 1; a blocked one → 0.
  (run:2026-10-21-cat-emu-8a, 0x005CCBB5–0x005CCBC5)

### 6. Missiles and the infernos: do 85, 88, 93, 95, 111, start 53

- [C] (ADR-0021) **Do 85** (`0x005CB0C0`): a bad id → 0; `srvmissilea` out of range → 0; bit 6 set;
  `MONSTATS_GetClassChainPos(class, 0, &arg1)` writes the class's MonStats `+0x4B` byte (0 for a class out of range)
  over the id argument's slot; `m = srvmissilea + that` out of range → 0; else `SkillMissileCreate(ECX game, EDX m;
  caster, id, lvl, 0, 0, 0, 0, 0)` at `0x005CB152`. So `unholybolt1` and `shafire1` stand for chains: the n-th class of
  a MonStats chain casts the n-th missile after the named one. (run:2026-10-21-cat-emu-8a, fn:MONSTATS_GetClassChainPos@0x006510C0)
- [C] (ADR-0021) **Do 88** (`0x005CB580`, AndrialSpray): a bad id or `srvmissilea` out of range → 0; no used node → 0;
  the point is the node's `+0x18`/`+0x1C` when both are non-zero, else `SKILLS_GetTargetXY` (none → 0); `d =
  map[0x00621DC0(caster, point)] & 7`; `(dx, dy)` of `0x006E3188[d]` from the caster's position; the frame `f =
  min(max((+0x44 >> 8) − 4, 0), 8)`; `0x006E3140[9d + f]` not `0x63` ('c') adds its offsets too; `MissileCreate(ECX game,
  EDX &block)` at `0x005CB70D` with the block's flags `0x20`, owner and source the caster, class `m`, **target point**
  `+0x1C`/`+0x20` = that point, level `+0x30`, everything else 0 (no skill id, no position: `MissileCreate`'s own
  defaults, after, `[I]`). (run:2026-10-21-cat-emu-8a, 0x005CB682–0x005CB6CD)
- [C] (ADR-0021) **Do 93** (`0x005CC050`, GargoyleTrap): a bad id or `srvmissilea` out of range → 0; bit 6 set; no target
  → 0; with `(Tx, Ty)`, `(Ux, Uy)` and `|Tx − Ux| < |Ty − Uy|` (signed): `ex` steps from `Ux` four times towards `Tx`,
  `ey = Ty`; else `ex = Tx`, `ey` steps from `Uy` four times towards `Ty`; `MissileCreate` at `0x005CC1C1` with flags 3,
  owner the caster, class `m`, position `((ex − Ux) / 6 + Ux − 1, (ey − Uy) / 6 + Uy − 1)` (division toward 0, the
  `0x2AAAAAAB` multiply), target words `+0x1C`/`+0x20` = `(ex − Ux, ey − Uy)`, skill and level. (run:2026-10-21-cat-emu-8a,
  0x005CC0E8–0x005CC1BC)
- [C] (ADR-0021) **Do 95** (`0x005CC4E0`, the infernos): a bad id → 0; no used node → 0; `srvmissilea` out of range →
  0; a block with flags `0x25`, owner the caster, class `m`, position the caster's, level, `+0x28` =
  `(VelLev · lvl) / 8 + Vel` (signed division toward 0; the velocity term of skills/0002 § 2's creation, unshifted,
  `[I]` as a meaning); `SKILLS_GetTargetXY` none → `0x005CC3B0`, ending at
  `CancelEvents(ECX game, EDX caster; 0, 0)` at `0x005CC415`; else the target point into `+0x1C`/`+0x20` and
  `MissileCreate` at `0x005CC5DA`. After, `[I]`: on `0x005CC3B0`, an event at `frame + MonStats2 InfernoLen` (default
  11) and 0; on a created missile, `0x005CC2E0` (a count from calc1, or the missile's `+0x3C` plus the level, onto the path's `+0x90` and the
  animation by `AnimLen`),
  `0x005CC440` (`InfernoAnim`), and while the game frame is below the node's `+0x18` (start 53's end frame) and state
  12 is set, `calc3` re-queues the do; else `0x005CC3B0`; 1. (run:2026-10-21-cat-emu-8a, 0x005CC58C–0x005CC5A8)
- [C] (ADR-0021) **Start 53** (`0x005CC240`): a bad id → 0; no used node → 0; the node's `+0x18` = `game+0xA8 +
  max(calc2, 1)`; with state 12 → 1; else `STATE_Set(caster, 12, 1)` at `0x005CC2CF`; after, `[I]`, 1.
  (run:2026-10-21-cat-emu-8a, 0x005CC29A–0x005CC2B4)
- [C] (ADR-0021) **Do 111** (`0x005CE670`, FetishAura): `SKILLS_GetTargetXY` none → 0; bit 6 set; **no id test**: the
  record at `id·0x23C` of the Skills table, or address 0 for an id out of range, whose `+0x154` (`Param4`) is read; then
  `0x0056C210(ECX game, EDX caster; Param4 + 2·lvl, x, y)` (its three stack words compared at `0x7FEFFFD4`), which
  ends at the allocator `0x0040B430(ECX game+0x1C, EDX 0x2C; 0x006DAB88, 0x44B, 0)` at `0x0056C236`. A bad id would read
  `[0x154]` (a fault); the case writer gives valid ids only. After, `[I]`: a `0x583` search block round `(x, y)` with
  radius `r`, `0x0065A950`, `0x0065AC70`, then the loop (Answer, *After*), `0x0056C2A0` frees it, 1.
  (run:2026-10-21-cat-emu-8a, 0x005CE6A5–0x005CE6E4)

## Corrections to earlier findings

- skills/0003 § 4, carried there as a dated note: do 83's `COMBAT_DeliverQueued(target, 0)` call is now emulated
  (`[C]` under ADR-0021, § 3); its `SkillMissileCreate`-free path and the restart stay `[I]`. (0x005CAF55)

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `lob` (`+0x04` bit 1), `srvmissilea` (`+0x48`), `calc1` (`+0x138`), `calc2`
(`+0x13C`), `calc3` (`+0x140`, after), `Param4` (`+0x154`), `summon` (`+0xBC`), `summode` (`+0xBF`), `ToHit`/`LevToHit`/
`ToHitCalc` (`+0x198`–`+0x1A0`), `ResultFlags`/`HitFlags`/`HitClass` (after); `tbl:MonStats.txt:spawn` (`+0x20`),
`spawnx`/`spawny` (`+0x22`/`+0x23`), `spawnmode` (`+0x24`), `+0x4B` (the chain position); `tbl:MonStats2.txt:InfernoLen`
(`+0x108`, after); `tbl:Missiles.txt:Vel` (`+0x9A`), `VelLev` (`+0x9B`); ItemStatCost (`+0x05`); DataTables `+0xD4`,
`+0xC4`; unit `+0x00`, `+0x04`, `+0x0C`, `+0x14`, `+0x20` seed, `+0x2C` path (`+0x02`, `+0x06`, `+0x0C`, `+0x10`,
`+0x12`, `+0x1C`, `+0x48`, `+0x58`–`+0x60`, `+0x90`/`+0x91`), `+0x3C`, `+0x44`, `+0x4E`, `+0x5C` stat list, `+0x60`
inventory, `+0xA8` skills, `+0xC4` bits 1–3 and 6; the used node `+0x0C`, `+0x18`–`+0x24`; game `+0x1C`, `+0xA8`.

## Dead ends

- None in the code. The first emulation (`dev/dev1`) mismatched on 35 start 42 cases (the start 32 return slot
  guessed), and two model errors stopped the check (do 98 modelled after an id test it does not make; do 87's and do
  88's `PathDirection` ratio out of its table for far points); `dev/dev2` hit the ratio once more (a target with no
  path sits at 0, 0); `dev/dev3` mismatched on 163 do 93 cases (its target words are offsets) before the model fix.
  No claim rests on them (`dev/notes.txt`).

## Open questions

- [L] What every boundary callee does past its entry (§§ 3–6), what `0x00649F70` (`UnitCorpseColl`) and `0x005544B0`
  do with their unit, and what `0x0056EBE0(id, lvl, 0x44, 0x19, 0)` gives do 111's fetishes.
- [L] Whether a monster's `PathDirection` point lies within 257 subtiles in play (do 87's target, do 88's node point);
  past that the code reads outside its table (§ 5).
- [L] The direct call of do 98 from do 129 (`0x005D1B75`, batch 8c) and do 152's two `0x005CC3B0` calls
  (`0x005CC690`, batch 8b).
- [L] Everything after each boundary (§§ 3–6), for a later batch or the harness.
