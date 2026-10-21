# 0017 — Catalogue batch 8b: the monster skill functions of Skills rows 190–289 (start 54, 55, 59, 60, 64, do 99–109, 112, 125–127, 141, 152)

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 54, 55, 59, 60, 64 (`srvstfunc`, `g_SkillStartFuncs`) and do
> function 99–109, 112, 125–127, 141 and 152 (`srvdofunc`, `g_SkillDoFuncs`) of plan 0046 batch 8b do (Diablo's
> skills, the act 4 and act 5 towers and sentries, the Mosquito and Regurgitator skills, the monster curse, Frenzy, the
> Imp and Suck Blood rows, Baal's corpse explosion): which Skills, Missiles, MonStats and unit fields it reads, what it
> makes, which draws it makes on which seed, what it returns, and which of that the emulator can confirm?
> **Date:** 2026-10-21   **Plan:** 0046 (Phase 1, batch 8b)   **Status:** for review (`lane/p46m14`)

Static reading of the pinned `Game.exe` with objdump and the lane's Ghidra copy `workspace/ghidra-p46m14`, then
emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged) and the `8b` families of
`tools/skills_catalogue_emu.py` (§ 2; run:2026-10-21-cat-emu-8b in [experiments](experiments.md)). Skills columns are
named as in [Skills](../../tables/Skills.md), Missiles's as in [Missiles](../../tables/Missiles.md), MonStats's as in
[MonStats](../../tables/MonStats.md). The dispatch that runs a start or do function is
[skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart); start 55 and do 109 were read before
(skills/0003), do 95 and start 53, which do 152 and start 59 repeat, in [skills/0016](0016-monster-8a.md) § 6. Stock
values come from `workspace/logs/skills-cat-8b/rows.txt` (`rows.sh` beside it: the 18 Skills rows that name one of the
batch's entries, checked complete against all 357 rows by its `CHECK` lines, and the five curse rows do 112 reads).

**Tag convention for this finding** (as skills/0016). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md):
(a) nothing is patched and each boundary is a function entry reached by the program's own flow; (b) the checker asserts
per case the boundary and its call site (the return address at ESP), with a site control that fails every matched
boundary case, and where the boundary sits inside a helper the function called, the helper's return address is
compared at its absolute stack slot (§ 2 lists each slot); (c) the model gives and the checker compares every argument
the claim uses (registers the callee reads before it writes them, stack words, and for a pointer the bytes it points
to), every byte written before the call that the claim uses (the caster's `+0xC4`, `+0x48`, the used node's words, the
path's `+0x10`/`+0x58`, the argument slots), and the state of **the caster's and the target's seeds** at the boundary
(both, in every case). Each such claim names the boundary it ends at; **the callee and all code after it are not
covered** and keep `[I]`, marked "after, `[I]`" in place (reverser review-fixes 13). No claim rests on a callee-saved
register that is not a boundary argument. A plain `[C]` rests on cases that return; a plain `[I]` is a code reading the
emulator does not reach. (run:2026-10-21-cat-emu-8b)

## Answer (summary)

- [C] **The batch.** Twenty-two entries, each `(ECX game, EDX unit; skill id, level)` with `ret 8`: start 54
  `0x005CD2C0`, 55 `0x005CD910`, 59 `0x005D1280`, 60 `0x005D1570`, 64 `0x005CDF00`; do 99 `0x005CCD10`, 100
  `0x005CCE80`, 101 `0x005CCFA0`, 102 `0x005CD1C0`, 103 `0x005CD380`, 104 `0x005CD5D0`, 105 `0x005CD6A0`, 106
  `0x005CD870`, 107 `0x005CDA00`, 108 `0x005CDC10`, 109 `0x005CDF10`, 112 `0x005CE2B0`, 125 `0x005D1170`, 126
  `0x005D1350`, 127 `0x005D16A0`, 141 `0x005D2E80`, 152 `0x005CC690` (`table_entries=22`). All twenty-two are emulated:
  four families, **9 200 cases, 0 mismatches**. (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0,
  `static.txt`, run:2026-10-21-cat-emu-8b)
- [C] **Draws before the boundaries.** Only **do 112** steps a unit's seed: one inline step of **the caster's seed**
  (`U+0x20`/`+0x24`), its new low word mod 5 picking the curse, made before any test (a refusal returns with the seed
  stepped). **Start 55** draws `RNG_RangeB(local, calc2 − calc1)` on a **local seed** made from the target's and the
  caster's guids, which no unit keeps. No other entry steps the caster's or the target's seed before its boundary or
  return. (run:2026-10-21-cat-emu-8b, fn:sub_005CE2B0_SkillDo112MonCurse@0x005CE2B0,
  fn:sub_005CD910_SkillSt55LocalSeed@0x005CD910)
- [C] (ADR-0021; § 3) **The missile casts.** Do 99 ends at the first of its `MissileCreate` calls (flags `0x1F`,
  `+0x28` = the missile's `Param1 << 6`, `+0x34` = calc1, target words `(0, 2)`, the first of sixteen `.rdata` pairs);
  do 101 at `0x00649EF0(path, Tx, Ty, 0)` with a target, else at `MissileCreate` (flags 3, the path point's offsets
  from the caster); do 102 at its first of calc1 `MissileCreate` calls (flags `0x21`, the target point, `+0x54` the
  callback `0x005CD110`); do 105 at the first of a row of calc1 missiles across the line to the target (flags 3, the
  step `(−2·sgn dy, 2·sgn dx)`, the row's start shifted back by `calc1 / 2` steps, the **position's y the caster's y plus
  the x offset over 6**); do 106 at `NovaAtUnit(caster, m, id, lvl, speed)` with the missile's speed at the level; do 125
  at `MissileCreate` (flags 2, `SrvMissileByCharge`'s missile, the target point's offsets); do 126 at
  `UnitSetPathTargetUnit` after writing the target's point into the caster's path, or with no target at `MissileCreate`
  (flags `0x25`, the path point as the target, the speed); **do 152 is do 95's code** (147 instructions, none
  different): `MissileCreate` with flags `0x25`, or `0x005CC3B0`'s `CancelEvents(0, 0)` with no target point.
  (run:2026-10-21-cat-emu-8b)
- [C] (ADR-0021; § 4) **The hits and the queued hits.** Do 100 ends at `SKILLS_RollElemDamage(ECX caster, EDX
  &packet; id, lvl)` with packet `+0x00` = `HitFlags`, `+0x04` = `1 | ResultFlags`, `+0x34` = the elemental length,
  `+0x60` = `HitClass` (no target → 1); do 103 at `0x006212C0(caster, Param2)` with `+0x48` = `Param1 << 8` (the node's
  bit 1), at `PathSetSpeed(path, MulDiv(max(calc1 << 8, 0x100), stat 67, 100))` (the frame = Param3), at
  `0x006212C0(caster, Param6)` with `+0x48` = `Param5 << 8` (the frame = Param4), or at `InMeleeRange(caster, the node's
  stored unit, 0)` (the caster's `+0x4E` byte 1), else 1; do 107 at `InMeleeRange(caster, the node's stored unit, 0)`;
  do 108 at the room removal `0x0061A270(room, 1, guid)` of a dead (mode 12) non-hireling monster target; do 109 at
  `QueuedHitRemove(target)`; do 127 at `DeliverQueued(target, 0)` for a queued hit without bit 0, or at
  `UnitSetStat(life unit, 6, …)` adding `MulDiv(min(hit damage, the target's life), calc1, 100)`, the life unit being a
  monster caster's owner (else the caster; **0 for a player caster**); start 60 at `0x0056E680`'s `MeleeHitTest`
  (ResultFlags bit 0 clear) or at `0x0057E270(target, id, lvl, &packet)` with `+0x00` = `2 | HitFlags`. (run:2026-10-21-cat-emu-8b)
- [C] (ADR-0021; § 5) **The node words, the prison, the corpses, the curse.** Start 54 returns 1 after writing the
  target's guid and type into the node (`+0x18`, `+0x1C`, `+0x0C` = 0) and its point into the caster's path (`+0x10`,
  `+0x12`, `+0x58` = 0); start 55 returns 1 with the node's `+0x18` = `max(calc1 + draw, 1)`, `+0x1C`/`+0x20` the
  target's guid and type; start 59 is start 53 with calc1 for calc2 (one instruction differs), ending at
  `STATE_Set(caster, 12, 1)`; start 64 returns whether there is a target; do 104 writes `SkillSummonClass`'s mode **into
  the level argument's slot** and ends at `0x005B34C0(ECX game, EDX room; 0, 0, unit, class, 0)` for the target or the
  object whose guid the path's `+0x10` holds when its `+0x12` is 2, unless that unit has no room or a town room; do 141
  ends at `0x0056DCC0(ECX game, EDX &block)` with a 0x24-byte block (`0x3002`, the caster, **skill 285 whatever the id**,
  its position, radius `(lvl − 1)·Param6 + Param5`, the level, the callback `0x005D2E50`); do 112 ends at
  `SkillForUnitsNearTarget(ECX game, EDX 3; caster, radius, 0x005C35C0, &block)` with the curse block of the drawn row.
  (run:2026-10-21-cat-emu-8b)
- [I] **The data joins.** DiabLight (193) runs start 53 and do 152, so its cast is the infernos' (skills/0016 § 6) with
  `diablight`. Baal Corpse Explode (285) has `Param5` 40 and `Param6` 0, a radius of 40 at every level. MonCurseCast
  (212) casts Amplify Damage (66), Weaken (72), Life Tap (82), Decrepify (87) or Lower Resist (91) one time in five each,
  at the caster's level, with the curse row's own target state, length and radius calcs; for row 91 the code fills
  Decrepify-like stats (velocity and attack rate at row 91's `Param7`, 0 in the stock file; damage and resist −50), and
  its resist branch (`0x005CE470`) is unreachable, the drawn index being at most 4. MonFrenzy (215) and
  BloodLordFrenzy (328) share do 109; DiabRun's (198) `Param3` 5 and `Param4` 13 are the two frames do 103 tests.
  (`rows.txt`, tbl:Skills.txt:srvdofunc, tbl:Skills.txt:Param7)
- [I] After, from the reading: do 99's other fifteen creations and its second ring when calc2 is above 1 (`Param2 << 6`); do 101's
  creation after `0x00649EF0`; do 102's calc1 creations with `+0x58` the index; do 105's further creations, the row
  stepping by `(A, B)`; do 103's path type 1, `PathPlan` and the node's bit 1, and the melee hit with physical and
  elemental rolls on the caster's seed; do 107's damage rolls (`SkillRollPhys`, `RollElemDamage`, three
  `RNG_RangeB(caster, max − min)` from the physical range `>> 8`), the heal by calc3 and its re-arm; do 108's unit free
  and the caster's heal by calc1 of the corpse's maximum life; do 109's restart and hit (`0x005CDD30`, `0x005CDDD0`);
  do 126's inferno repeat (`0x005CC440`, the node's end frame, state 12, a re-queue at frame + 3 or an end at frame +
  13). (0x005CCE25–0x005CCE62, 0x005CD294–0x005CD2A6, 0x005CD813–0x005CD85E, 0x005CDAAB–0x005CDBFF,
  0x005CDC9B–0x005CDD0A, 0x005D148E–0x005D154B)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005CD2C0` | `sub_005CD2C0_SkillSt54DiabRun` | start 54 (DiabRun) | I |
| `0x005CD910` | `sub_005CD910_SkillSt55LocalSeed` | start 55 (Mosquito; existing name, skills/0003) | I |
| `0x005D1280` | `sub_005D1280_SkillSt59ImpInferno` | start 59 (Imp Inferno) | I |
| `0x005D1570` | `sub_005D1570_SkillSt60SuckBlood` | start 60 (Suck Blood) | I |
| `0x005CDF00` | `sub_005CDF00_SkillSt64HasTarget` | start 64 (MonFrenzy) | I |
| `0x005CCD10` | `sub_005CCD10_SkillDo99PoisonNova` | do 99 (PrimePoisonNova) | I |
| `0x005CCE80` | `sub_005CCE80_SkillDo100DiabCold` | do 100 (DiabCold) | I |
| `0x005CCFA0` | `sub_005CCFA0_SkillDo101FingerMage` | do 101 (FingerMageSpider) | I |
| `0x005CD1C0` | `sub_005CD1C0_SkillDo102DiabWall` | do 102 (DiabWall) | I |
| `0x005CD380` | `sub_005CD380_SkillDo103DiabRun` | do 103 (DiabRun) | I |
| `0x005CD5D0` | `sub_005CD5D0_SkillDo104DiabPrison` | do 104 (DiabPrison) | I |
| `0x005CD6A0` | `sub_005CD6A0_SkillDo105DesertTurret` | do 105 (DesertTurret) | I |
| `0x005CD870` | `sub_005CD870_SkillDo106ArcaneTower` | do 106 (ArcaneTower) | I |
| `0x005CDA00` | `sub_005CDA00_SkillDo107Mosquito` | do 107 (Mosquito) | I |
| `0x005CDC10` | `sub_005CDC10_SkillDo108CorpseEat` | do 108 (RegurgitatorEat) | I |
| `0x005CDF10` | `sub_005CDF10_SkillDo109Frenzy` | do 109 (MonFrenzy, BloodLordFrenzy; existing name, skills/0003) | I |
| `0x005CE2B0` | `sub_005CE2B0_SkillDo112MonCurse` | do 112 (MonCurseCast) | I |
| `0x005D1170` | `sub_005D1170_SkillDo125WakeSentry` | do 125 (Wake Of Destruction Sentry) | I |
| `0x005D1350` | `sub_005D1350_SkillDo126ImpInferno` | do 126 (Imp Inferno) | I |
| `0x005D16A0` | `sub_005D16A0_SkillDo127SuckBlood` | do 127 (Suck Blood) | I |
| `0x005D2E80` | `sub_005D2E80_SkillDo141BaalCorpse` | do 141 (Baal Corpse Explode) | I |
| `0x005CC690` | `sub_005CC690_SkillDo152DiabLight` | do 152 (DiabLight; do 95's code) | I |
| `0x005CC2E0` | `sub_005CC2E0_InfernoMissileRange` | do 95's and do 152's after-creation helper (calc1 or `+0x3C` + lvl onto the path's `+0x90`) | I |
| `0x005CC440` | `sub_005CC440_InfernoAnim` | do 95's, 126's and 152's animation helper (`InfernoAnim`) | I |
| `0x005CDD30` | `sub_005CDD30_AnimNextEventByte` | do 109's test: a non-zero byte in the animation's frame list after the current frame | I |
| `0x00649EF0` | `sub_00649EF0_PathFaceXY` | `(path, x, y, flag)`: the direction from the path's fixed point to `(x, y)` | I |
| `0x0056DCC0` | `sub_0056DCC0_SkillAreaBlock` | `(ECX game, EDX &block)`: do 141's 0x24-byte area block | I |
| `0x005B34C0` | `sub_005B34C0_SpawnAtUnitClass` | `(ECX game, EDX room; a, b, unit, class, c)`: do 104's spawn (class 340 tested first) | I |
| `0x0057E270` | `sub_0057E270_SkillHitRecord` | `(EDX unit; target, id, lvl, &packet)`: start 60's hit after `0x0056E680` | I |
| `0x005D2E50` | `sub_005D2E50_BaalCorpseCb` | do 141's block callback | I |

## Walkthrough

### 1. The table slots, the stock rows and the callers

- [C] `g_SkillStartFuncs[54, 55, 59, 60, 64]` and `g_SkillDoFuncs[99..109, 112, 125..127, 141, 152]` are the
  Functions table's addresses (`table_entries=22`). (data:g_SkillStartFuncs@0x00732140,
  data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [I] **Stock rows** (`rows.txt`, 18 rows, the `CHECK` lines complete): do 99 on 192 PrimePoisonNova
  (`primepoisoncloud`, calc2 2); start 53 + do 152 on 193 DiabLight (`diablight`); do 100 on 194 DiabCold (EType `mag`);
  do 101 on 196 FingerMageSpider (`fingermagespider`); do 102 on 197 DiabWall (`diabwallmaker`); start 54 + do 103 on 198
  DiabRun (calc1 20, Params 8, 14, 5, 13, 16, 6, ResultFlags 5); do 104 on 199 DiabPrison (`summon` `boneprison1`);
  do 105 on 203 DesertTurret (`desertfireball`, calc1 3); do 106 on 204 ArcaneTower (`lightningtowernova`); start 55 +
  do 107 on 206 Mosquito (calc1 4, calc2 7, calc3 25); do 112 on 212 MonCurseCast; do 108 on 214 RegurgitatorEat
  (calc1 33); start 64 + do 109 on 215 MonFrenzy, do 109 also on 328 BloodLordFrenzy (start 37); do 125 on 281 Wake Of
  Destruction Sentry (`wake of destruction maker`); start 59 + do 126 on 282 Imp Inferno (`impinfernoflame1`); do 141
  on 285 Baal Corpse Explode; start 60 + do 127 on 289 Suck Blood. No row of the batch has the `lob` bit.
  (`rows.txt`, tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc)
- [I] **Callers.** No entry of the batch is called from outside the two tables: a scan of every `call`/`jmp` operand
  finds none, and each entry's address occurs once as a dword in the image file, its table slot (`entry_words=22`).
  `0x005CC3B0` is called four times: twice in do 95 (8a) and twice in **do 152**, at `0x005CC770` (no target point, or
  `MissileCreate` returning 0 at `0x005CC78C`) and `0x005CC827` (after a created missile, when the game frame is not
  below the node's `+0x18` or state 12 is not set); the first is emulated on its no-target path (§ 3), the second lies
  after `MissileCreate` (`[I]`). `0x005CC440` is called from do 95, do 152 and do 126 (`0x005D14D4`); `0x005CDD30` and
  `0x005CDDD0` only by do 109. (`static.txt` `calls of` lines, 0x005CC770, 0x005CC827)

### 2. Emulation: the `8b` families

The method is skills/0016's, with four families sharing one memory spec (`mem_8b`; `curse_8b` sets the Skills count
to 92 so that do 112's curse rows exist): `g_pDataTables` pointed at a scratch DataTables, and set in the spec the
Skills, Missiles (count 48), ItemStatCost, MonStats, MonStats2, States and PetType counts, the calc pool, DataTables
`+0xD4` and `+0xBC0`, `MONSTATS_GetClassChainPos`'s table and count, and `sub_00663270_MissileSpeedAtLevel`'s missile
table and count (`0x0096C794`/`0x0096C79C`); the allocator and the fatal path are guarded. Every case dumps the stack,
both seeds (caster and target `+0x20`), the caster's `+0xC4` and both argument slots; families add the node's `+0x0C`
and `+0x18`–`+0x27`, the caster's `+0x48` and its path's `+0x10` and `+0x58`. Each dumped byte is written by the case.

Emulated, not observed: `UNIT_GetTargetUnit` (its revalidation clearing a stale link's `+0x58`), `UNIT_GetUsedSkill`,
the node getters and setters, `SKILLS_EvalCalc` (constant programs), `SKILLS_GetTargetXY`, `SKILLS_GetElemLen`,
`SKILLS_GetToHit`, `UnitGetSubX/Y`, `UnitGetRoom`, `RoomIsTown`, the path getters, `sub_00648AD0_PathSetTargetPoint`,
`sub_00648B90_PathSetTargetUnit`, `UNIT_HasState`, `STATS_GetUnitStat`, `UnitGetMaxHp`, `MulDiv`, `GameFindUnit`,
`sub_0058F0D0_MonsterOwner`, `sub_0063EE90_HirelingType`, `sub_0057D690_QueuedHitFind`, `MissileRec`,
`sub_00663270_MissileSpeedAtLevel`, `sub_005D3CF0_SkillSrvMissileByCharge`, `SkillSummonClass` (its Skills path and the
`0x0058F710` fallback), `UNIT_GetAnimFrames` (`0x00621810`), `RNG_SeedInitOne`, `RNG_SeedInit`, `RNG_RangeB`,
`0x0056E680` up to its `MeleeHitTest`, `0x005CC3B0` up to its `CancelEvents`. Observed (new): `SKILLS_RollElemDamage`
`0x0056E0C0`, `sub_0057C9F0_QueuedHitRemove`, `0x005B34C0`, `0x0056DCC0`, `0x00649EF0`,
`sub_0056D400_SkillNovaAtUnit`, `0x0057E270`; `MissileCreate`, `InMeleeRange`, `0x006212C0`, `PathSetSpeed`,
`RoomUnitRemove` (`0x0061A270`), `DeliverQueued`, `MeleeHitTest`, `UnitSetStat`, `STATE_Set`, `CancelEvents`,
`UnitSetPathTargetUnit` (`0x00620C10`) and `SkillForUnitsNearTarget` as in earlier batches.

**Register arguments read before written** (ruling 1 of the `lane/p46m8` review): `SKILLS_RollElemDamage` (`mov [ebp−0x8],
edx` at `0x0056E0CE`, `mov esi, ecx` at `0x0056E0D1`), `QueuedHitRemove` (`mov edi, edx` at `0x0057C9F5`, `mov
[ebp−0x4], ecx` at `0x0057C9F9`), `0x005B34C0` (`mov ebx, edx` at `0x005B34CF`, `mov [ebp−0x4], ecx` at `0x005B34D1`),
`0x0056DCC0` (`mov esi, edx` at `0x0056DCC8`, `mov [ebp−0x4], ecx` at `0x0056DCCD`), `NovaAtUnit` (`mov edi, edx` at
`0x0056D411`, `mov ebx, ecx` at `0x0056D413`, before its `memset`), `0x0057E270` (`EDX` only: `mov edi, edx` at
`0x0057E27A`; its `ECX` is overwritten at `0x0057E27E` unread, so the game is not compared there); `0x00649EF0` takes
stack arguments only; the others as in skills/0008–0016.

**Nested boundaries** (each compared at its absolute stack slot): do 152's return from `0x005CC3B0` (`0x005CC775`) at
`0x7FEFFF84` (do 95's slot, the code being the same); start 60's return from `0x0056E680` (`0x005D15E5`) at
`0x7FEFFF5C`, its zeroed packet at `EBP − 0x78`.

- [C] Four families, **9 200 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other than
  at a boundary; every negative control fails, and the site control fails on all 3 698 matched boundary cases (27
  function, boundary and return-address triples, each a `site` line) (`check.txt`; run:2026-10-21-cat-emu-8b):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `miss_8b` | do 99, 101, 102, 105, 106, 125, 126, 152 | 3 200 | `Param1 << 4` (140); x and y swapped (146); no callback (86); y by the y offset (95); no half shift (95); speed without the level term (265); target words absolute (196); srvmissilea 0 accepted (65) | MissileCreate @0x005CCE1D, @0x005CD0EB, @0x005CD2A1, @0x005CD855, @0x005D1248, @0x005D148E, @0x005CC78A; PathFaceXY @0x005CD094; NovaAtUnit @0x005CD8EA; SetPathTarget @0x005D140D; CancelEvents @0x005CC415 (in 0x005CC3B0); returns 0, 1 |
  | `hit_8b` | do 100, 103, 107, 108, 109, 127, start 60 | 2 800 | no `| 1` (79); ResultFlags ignored (152); Param4 first (26); hirelings eaten (24); damage not capped (14); the caster's life always (79) | RollElem @0x005CCF38; 0x006212C0 @0x005CD3F7, @0x005CD4CC; PathSetSpeed @0x005CD481; InMeleeRange @0x005CD50E, @0x005CDA79; RoomUnitRemove @0x005CDC9B; QueuedHitRemove @0x005CDF4B; DeliverQueued @0x005D17E5; UnitSetStat @0x005D17D5; MeleeHitTest @0x0056E6B8 (in 0x0056E680); Hit57E270 @0x005D1625; returns 0, 1 |
  | `move_8b` | start 54, 55, 59, 64, do 104, 141 | 2 400 | start 64 inverted (400); radius `lvl·Param6` (202); state 12 ignored (76); seed without the caster's guid (111); count not floored at 1 (45); level slot kept (254); town ignored (41) | Spawn5B34C0 @0x005CD689; StateSet @0x005D130F; Area56DCC0 @0x005D2F6B; returns 0, 1 |
  | `curse_8b` | do 112 | 800 | index mod 4 (578); state past the count accepted (98); length and radius swapped (482) | NearTarget @0x005CE4C6; returns 0 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 64 of 64 pins): `g_BitMask32`, the hash offsets, the
  `CALC_Eval` jump table, the town-level tables, do 99's target words `0x006E31A8`/`0x006E31E8` (16 pairs, `.rdata`),
  do 112's curse ids `0x006E3228` (`.rdata`) and its jump table `0x005CE4DC` (`.text`, 5 entries), and the skills calc
  function count `0x007457AC` (`.data`: 0 stores, 0 immediates, 7 reads). Skills, Missiles, MonStats, MonStats2,
  ItemStatCost, the stat lists, the nodes, the queued hits, the paths, the rooms and the units are scratch records
  written one field per field read. (run:2026-10-21-cat-emu-8b)
- [C] **Every control and its deciding class** (ruling 4 of the `lane/p46m5` review; each class counted from the case
  files by a predicate on the written inputs, the 24 `CLASS` lines of `check.txt`, each equal to its control's
  failures). The thinnest: `dmg_nomin` (14) the do 127 leeches whose value capped at the target's life and uncapped
  differ (a wrong reading, no cap, reaches a different `UnitSetStat` value and cannot match by chance); `hire_any` (24)
  the dead hireling-class monster targets of do 108; `p4_first` (26) the do 103 cases whose frame equals both Param3 and
  Param4; `town_any` (41) the do 104 units in a town room; `n_floor0` (45) the start 55 counts below 1. Each family has a
  control failing 90 or more (`speed0` 265, `rf_ignored` 152, `t64_inv` 400, `k_mod4` 578). (run:2026-10-21-cat-emu-8b)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills, Missiles,
  MonStats columns `[C]` by layout; unit, path, node, packet and stat-list offsets `[I]`), and nothing here says when the
  game runs these functions or on which seed state. (run:2026-10-21-cat-emu-8b)

### 3. The missile casts: do 99, 101, 102, 105, 106, 125, 126, 152

- [C] (ADR-0021) **Do 99** (`0x005CCD10`, PrimePoisonNova): a bad id → 0; `srvmissilea` (s16) out of `[0, count)` → 0;
  bit 6 set; a block with flags `0x1F`, owner and source the caster, class `m`, position the caster's, level `+0x30`,
  `+0x34` = calc1, `+0x28` = the missile's `+0x38` (`Param1`) `<< 6`, then calc2 (`max(·, 1)`, used after); the first
  creation's target words `+0x1C`/`+0x20` = `(0, 2)` from `0x006E31E8`/`0x006E31A8`; `MissileCreate` at `0x005CCE1D`.
  The shift drops `Param1`'s top bits past 33 554 431 (`static.txt` `wrap` line). After, `[I]`: fifteen more creations
  through the sixteen pairs (`(0,2) (1,2) (2,2) … (−1,2)`), then `+0x28` = `Param2 << 6` (Missiles `+0x3C`) and, when
  calc2 is above 1, a second ring from the second pair stepping `calc2` pairs at a time. (run:2026-10-21-cat-emu-8b, 0x005CCDDA–0x005CCE18)
- [C] (ADR-0021) **Do 101** (`0x005CCFA0`, FingerMageSpider): a bad id or `srvmissilea` out of range → 0; bit 6; a block
  with flags 3, owner and source the caster, class, position, skill `+0x2C`, level, `+0x34` = calc1; with a target `T`:
  `0x00649EF0(caster's path, Tx, Ty, 0)` at `0x005CD094` (the block compared in the frame at `EBP − 0x64`); without:
  target words = the path point (`+0x10`/`+0x12`) minus the caster's position, `MissileCreate` at `0x005CD0EB`. After,
  `[I]`: with a target, the words `Tx − Ux`, `Ty − Uy` and the creation; 1 whatever the creation returns.
  (run:2026-10-21-cat-emu-8b, 0x005CD06E–0x005CD0E6)
- [C] (ADR-0021) **Do 102** (`0x005CD1C0`, DiabWall): a bad id or `srvmissilea` out of range → 0 (no record test); bit 6;
  `n` = calc1; `SKILLS_GetTargetXY` none → 0; `n ≤ 0` → 1; else a block with flags `0x21`, owner the caster, class,
  position, the target point, level, `+0x54` = `0x005CD110` (`sub_005CD110_MissCbReseedRoll`), `+0x58` = 0 (the index),
  `MissileCreate` at `0x005CD2A1`. After, `[I]`: `n − 1` more with the index. (run:2026-10-21-cat-emu-8b, 0x005CD275)
- [C] (ADR-0021) **Do 105** (`0x005CD6A0`, DesertTurret): a bad id or `srvmissilea` out of range → 0; bit 6;
  `SKILLS_GetTargetXY` none → 0; `dx, dy` = the point minus the caster's position, both 0 → 0; the step `(A, B)` =
  `(−2·sgn dy, 2·sgn dx)` (eight sign cases in the code at `0x005CD74C`–`0x005CD7BD`); `n` = calc1, written
  over the id argument's slot; `h = n / 2` (toward 0); `dx −= h·A`, `dy −= h·B`; `n ≤ 0` → 1; else a block with flags 3,
  owner the caster, class, level, target words `(dx, dy)`, **position `(dx / 6 + Ux, dx / 6 + Uy)`** (both from the x
  offset, the `0x2AAAAAAB` multiply toward 0), `MissileCreate` at `0x005CD855`. After, `[I]`: `n − 1` more, `(dx, dy)`
  stepped by `(A, B)`. (run:2026-10-21-cat-emu-8b, 0x005CD7E0–0x005CD84A)
- [C] (ADR-0021) **Do 106** (`0x005CD870`, ArcaneTower): a bad id or `srvmissilea` out of range → 0; bit 6; no target →
  0; `speed = sub_00663270_MissileSpeedAtLevel(m, lvl)` = `(VelLev·lvl) / 8 + Vel` (toward 0); `NovaAtUnit(ECX game,
  EDX caster; caster, m, id, lvl, speed)` at `0x005CD8EA`; after, `[I]`, 1. (run:2026-10-21-cat-emu-8b, 0x005CD8D3)
- [C] (ADR-0021) **Do 125** (`0x005D1170`, Wake Of Destruction Sentry): a bad id → 0; `m = SrvMissileByCharge(caster,
  id)` (skills/0008's model) out of range → 0; `SKILLS_GetTargetXY` writes its x **over the id argument's slot** (also on
  failure) and none → 0; bit 6; a block with flags 2, owner and source the caster, class `m`, skill (the id, kept
  before), level, target words the point minus the caster's position, no position; `MissileCreate` at `0x005D1248`.
  After, `[I]`: a created missile gets `MISSDATA_SetSeedLow(−dy)` and `MISSDATA_SetParam2C(dx)`, 1; none → 0.
  (run:2026-10-21-cat-emu-8b, 0x005D11B1–0x005D1243)
- [C] (ADR-0021) **Do 126** (`0x005D1350`, Imp Inferno): a bad id → 0; `srvmissilea` **0 or below** or past the count →
  0 (`jle` at `0x005D1399`); no used node → 0; a target and a caster path: `PathSetTargetPoint(path, Tx, Ty)` (path
  `+0x10`/`+0x12` the point, `+0x58` = 0), then `UnitSetPathTargetUnit(caster, T)` at `0x005D140D`; without a target:
  a block with flags `0x25`, owner the caster, position, class, skill, level, `+0x28` = `(VelLev·lvl) / 8 + Vel`, target
  words the path's `+0x10`/`+0x12`, `MissileCreate` at `0x005D148E` (the caster's `+0x58` as `UNIT_GetTargetUnit`
  left it). No bit 6. A target with no caster path falls to the block, whose `PathGetPosX` then reads through a null
  path (no case gives a caster without one, `[I]`). After, `[I]`: with a target the same block from the new path point; a created missile's range
  `calc2 + Missiles +0x3C` onto the path's `+0x90` and its range words; `0x005CC440`; then, while the game frame is
  below the node's `+0x18` and state 12 is set, `CancelEvents(1, 0)` and a re-queue at frame + 3, else
  `CancelEvents(0, 0)` and an event at frame + 13; 1. (run:2026-10-21-cat-emu-8b, 0x005D13D1–0x005D1489)
- [C] (ADR-0021) **Do 152** (`0x005CC690`, DiabLight): the same 147 instructions as do 95 (`static.txt`: 0 differ, jump
  targets inside each body taken relative), so skills/0016 § 6's do 95 holds for it word for word: a bad id → 0, no used
  node → 0, `srvmissilea` out of range → 0; the flags `0x25` block with `+0x28` = `(VelLev·lvl) / 8 + Vel`;
  `SKILLS_GetTargetXY` none → `0x005CC3B0` ending at `CancelEvents(ECX game, EDX caster; 0, 0)` at `0x005CC415` (its
  return `0x005CC775` at `0x7FEFFF84`); else `MissileCreate` at `0x005CC78A`. After, `[I]`: as do 95's (§ 1's second
  `0x005CC3B0` call). (run:2026-10-21-cat-emu-8b, 0x005CC690–0x005CC83A)

### 4. The hits and the queued hits: do 100, 103, 107, 108, 109, 127, start 60

- [C] (ADR-0021) **Do 100** (`0x005CCE80`, DiabCold): a bad id → 0; bit 6; no target → **1**; a 0x70-byte packet at
  `EBP − 0x74`: `+0x04` (u16) = `1 | ResultFlags`, `+0x00` = `HitFlags`, `+0x60` = `HitClass` when non-zero, `+0x34` =
  `SKILLS_GetElemLen(caster, id, lvl, 1)`; `SKILLS_RollElemDamage(ECX caster, EDX &packet; id, lvl)` at `0x005CCF38`.
  After, `[I]`: its `RNG_RangeB(caster, ElemMax − ElemMin)` (`0x0056E132`), `COMBAT_ApplyDamage(target, 1, &packet)`,
  bit 1 of `+0x04` when the target's life is 0, `COMBAT_GetHit`, the `srvoverlay` overlay, 1. (run:2026-10-21-cat-emu-8b,
  0x005CCEE3–0x005CCF33)
- [C] (ADR-0021) **Do 103** (`0x005CD380`, DiabRun): a bad id → 0; no used node → 0; the node's `+0x0C` with bit 1 →
  `+0x0C` = 0, the caster's `+0x48` = `Param1 << 8`, `0x006212C0(caster, Param2)` at `0x005CD3F7`; else the frame `f`
  (`+0x44 >> 8`, signed) = `Param3` → no caster path → 0, else `v = calc1 << 8` (32-bit: calc1 up to 8 388 607 gives
  2 147 483 392, 8 388 608 wraps to −2 147 483 648; `static.txt` `wrap` line) with `v ≤ 0x100` → `0x100`, then
  `PathSetSpeed(path, MulDiv(v, STATS_GetUnitStat(caster, 67, 0), 100))` at `0x005CD481`; `f = Param4` → `+0x48` =
  `Param5 << 8`, `0x006212C0(caster, Param6)` at `0x005CD4CC`; else the caster's `+0x4E` byte 1 and
  `GameFindUnit(game, node +0x1C, node +0x18)` found → `InMeleeRange(caster, it, 0)` at `0x005CD50E`; otherwise 1.
  Param3 is tested before Param4. After, `[I]`: `PathSetType(1)`, `PathPlan`, the node's bit 1 (the frame path); the
  melee path clears `+0x4E`, runs `0x0056E680`, and on a hit `HitFlags | 0x20`, `SkillRollPhys`, `RollElemDamage`,
  `ApplyDamage`, `GetHit`, 1. (run:2026-10-21-cat-emu-8b, 0x005CD3D2–0x005CD509)
- [C] (ADR-0021) **Do 107** (`0x005CDA00`, Mosquito): a bad id → 0; no used node → 0; `GameFindUnit(game, node +0x20,
  node +0x1C)` (start 55's type and guid) none → 0; `InMeleeRange(caster, it, 0)` at `0x005CDA79`. After, `[I]`: not
  in range → 0; else `k` = the node's `+0x18`, a packet, `lo = PhysMin >> 8`, `hi = PhysMax >> 8`, `SkillRollPhys`,
  `RollElemDamage`, three `RNG_RangeB(caster, hi − lo)` draws (`+0x28` = 2·(lo + r), `+0x3C` and `+0x40` = (lo + r) <<
  8), `+0x2C` = the elemental length, the caster healed by `MulDiv(packet +0x08, calc3, 100)` capped at its maximum,
  `ApplyDamage`, `GetHit`, then with `k − 1 > 0` the node's `+0x18` = `k − 1`, `0x006212C0(caster, Param1)` and the frame
  word's next frame. (run:2026-10-21-cat-emu-8b, 0x005CDA5F–0x005CDA74)
- [C] (ADR-0021) **Do 108** (`0x005CDC10`, RegurgitatorEat): a bad id → 0; no target, a target not a monster, a
  hireling (`sub_0063EE90_HirelingType` non-zero: classes 271, 338, 359, 560, 561) or a target not in mode 12 → 0;
  `UnitGetMaxHp(target)`; `0x0061A270(UnitGetRoom(target), 1, target guid)` at `0x005CDC9B` (three stack words; the
  `push` before `UnitGetRoom` is that call's own argument). After, `[I]`: `UnitFree(target)`, the caster's life +
  `MulDiv(the corpse's maximum, calc1, 100)` floored at 1 and capped at the caster's maximum, 1.
  (run:2026-10-21-cat-emu-8b, 0x005CDC5D–0x005CDC96)
- [C] (ADR-0021) **Do 109** (`0x005CDF10`, MonFrenzy, BloodLordFrenzy; no id test): no used node → 0; no target → 0;
  `QueuedHitRemove(ECX game, EDX caster; target)` at `0x005CDF4B`. After, `[I]`: bit 6, `SKILLS_SrvStart(id, lvl, 0)`
  when `0x005CDD30` finds a non-zero byte after the current frame, `sub_005CDDD0_SkillDo109Hit` (skills/0003), the node's
  `+0x18` read, `0x005D8C70(id, lvl)` when non-zero, 1. skills/0003's reading of the head holds. (run:2026-10-21-cat-emu-8b,
  0x005CDF41)
- [C] (ADR-0021) **Do 127** (`0x005D16A0`, Suck Blood): a bad id → 0; no target → 0; bit 6; `QueuedHitFind(caster,
  target)` none → 0; the hit's packet `+0x04` bit 0 clear → `DeliverQueued(target, 0)` at `0x005D17E5`; set → the life
  unit `o` = `MonsterOwner(caster)` for a monster caster (the caster when none), **0 for any other caster**;
  `d` = the packet's `+0x08`, the target's life when not above it (`d ≥ life` → life); `v = life(o) + MulDiv(d, calc1,
  100)`; `UnitSetStat(o, 6, max(v, 1) ≥ max(o) ? max(o) : max(v, 1), 0)` at `0x005D17D5` (with `o` = 0, life and maximum
  read 0, so the value is 0). After, `[I]`: `DeliverQueued(target, 0)` on both paths, 1. (run:2026-10-21-cat-emu-8b,
  0x005D1718–0x005D17CF)
- [C] (ADR-0021) **Start 60** (`0x005D1570`, Suck Blood): a bad id → 0; no target → 0; a packet zeroed at `EBP − 0x78`;
  `0x0056E680(ECX game, EDX caster; target, record, id, lvl, &packet, 0)`: `ResultFlags` bit 0 clear →
  `MeleeHitTest(target, SKILLS_GetToHit(caster, id, lvl), 0)` inside it (`0x0056E6B8`, its return `0x005D15E5` at
  `0x7FEFFF5C`); set → `+0x04` = `ResultFlags`, then `+0x00` = `2 | HitFlags`, `+0x60` = `HitClass` when non-zero,
  `0x0057E270(EDX caster; target, id, lvl, &packet)` at `0x005D1625`. After, `[I]`: on a hit, `+0x08 +=
  MulDiv(+0x08, calc1, 100)`, `+0x38 +=` calc2, `+0x3C +=` calc3, `COMBAT_ResolveAndQueue(target, &packet, 0x80)`, 1.
  (run:2026-10-21-cat-emu-8b, 0x005D15D1–0x005D1620)

### 5. The node words, the prison, the corpse explosion and the curse: start 54, 55, 59, 64, do 104, 141, 112

- [C] **Start 54** (`0x005CD2C0`, DiabRun; no id test): no used node → 0; no target → 0 (the caster's path `+0x58` as
  `UNIT_GetTargetUnit` left it: a stale or picked-up link cleared); else the node's `+0x0C` = 0, `+0x18` = the target's
  guid, `+0x1C` = its type, `PathSetTargetUnit(caster's path, 0)` (`+0x58` = 0), `PathSetTargetPoint(caster's path,
  Tx, Ty)` (`+0x10`/`+0x12` the point, `+0x58` = 0), and 1. The caster's path is used without a test (no case gives a
  caster without one, `[I]`). (run:2026-10-21-cat-emu-8b, fn:sub_005CD2C0_SkillSt54DiabRun@0x005CD2C0)
- [C] **Start 55** (`0x005CD910`, Mosquito): a bad id → 0; no used node → 0; no target → 0; a local seed
  `RNG_SeedInit(Tguid + Uguid)` (low the sum, high `0x29A`; the code takes −1 for the guid of a null caster, which no
  case gives, `[I]`); `n = calc1 +
  RNG_RangeB(local, calc2 − calc1)`, at least 1; the node's `+0x18` = `n`, `+0x1C` = the target's guid, `+0x20` = its
  type; 1. The local seed is compared through `n` (`seed_t` 111). (run:2026-10-21-cat-emu-8b, 0x005CD967–0x005CD9C8)
- [C] (ADR-0021) **Start 59** (`0x005D1280`, Imp Inferno): start 53 with calc1 (`+0x138`) for calc2 (`static.txt`: 63
  instructions each, one differing): a bad id → 0; no used node → 0; the node's `+0x18` = `game +0xA8 + max(calc1, 1)`;
  state 12 → 1; else `STATE_Set(caster, 12, 1)` at `0x005D130F`; after, `[I]`, 1. (run:2026-10-21-cat-emu-8b,
  0x005D12D5)
- [C] **Start 64** (`0x005CDF00`, MonFrenzy): `UNIT_GetTargetUnit(game, caster)` non-zero → 1, else 0 (`neg; sbb;
  neg`); no id test. (run:2026-10-21-cat-emu-8b, 0x005CDF07)
- [C] (ADR-0021) **Do 104** (`0x005CD5D0`, DiabPrison): a bad id → 0; `SkillSummonClass(ECX caster, EDX 0; id, lvl,
  &lvl slot, 0, 0)`: the Skills path for every caster (`summon` in `[0, MonStats count)` → that class and `summode`
  (0..15, else 1) **written over the level argument's slot**; else the monster fallback `0x0058F710` with the slot
  unwritten); −1 → 0; the target, or with none the unit `GameFindUnit(game, 2, path +0x10)` when the caster's path
  `+0x12` is 2 (an object whose guid the path holds), none → 0; `UnitGetRoom` none → 0; `RoomIsTown` → 0; else
  `0x005B34C0(ECX game, EDX room; 0, 0, unit, class, 0)` at `0x005CD689`. After, `[I]`, 1. The mode written into the
  slot is not passed on. (run:2026-10-21-cat-emu-8b, 0x005CD606–0x005CD684)
- [C] (ADR-0021) **Do 141** (`0x005D2E80`, Baal Corpse Explode; no id test before its block): a 0x24-byte block at
  `EBP − 0x24`: `+0x00` = `0x3002`, `+0x04` = the caster, `+0x08` = **285 (`0x11D`)**, `+0x0C`/`+0x10` = the caster's
  position (0 with no path), `+0x14` = `(lvl − 1)·Param6 + Param5` for a valid id and `lvl > 0`, else 0 (32-bit),
  `+0x18` = the level, `+0x1C` = 0, `+0x20` = `0x005D2E50`; `0x0056DCC0(ECX game, EDX &block)` at `0x005D2F6B`; after,
  `[I]`, 1. (run:2026-10-21-cat-emu-8b, 0x005D2E86–0x005D2F66)
- [C] (ADR-0021) **Do 112** (`0x005CE2B0`, MonCurseCast; no id read): the caster's seed stepped once inline (`low ·
  0x6AC690C5 + high`, no null test of the caster), `k` = the new low word mod 5 (unsigned, the `0xCCCCCCCD` multiply),
  the curse `cid` = `0x006E3228[k]` (66, 72, 82, 87, 91); its record's `auratargetstate` (`+0x82`, s16) below 0 or at
  the States count → 0 (seed stepped, no bit 6); bit 6; `r` = `aurarangecalc` (`+0x64`) and `len` = `auralencalc`
  (`+0x60`), both evaluated with `cid` and the caster's level; a 0x68-byte block at `EBP − 0x78`: `+0x00` the game,
  `+0x04` the caster, `+0x08` 0, `+0x0C` 0 (1 for `k` = 4), `+0x10` `cid`, `+0x14` the level, `+0x18` `len`, six stat
  ids −1 at `+0x1C` and six values 0 at `+0x34`, `+0x4C` the state; by `k` (jump table `0x005CE4DC`): 0 → stat 36 at
  −100; 1 → stat 25 at −50; 2 → `+0x50` = 5, `+0x5C` = 4; 3 → `+0x50` = 1, `+0x54` = 2, `+0x5C` = 5, `+0x60` = 5;
  4 → stats 67, 25, 36, 68 at `Param7`, −50, −50, `Param7` (the curse row's `+0x160`); then
  `SkillForUnitsNearTarget(ECX game, EDX 3; caster, r, 0x005C35C0, &block)` at `0x005CE4C6`. The default branch
  (`0x005CE470`: stats 37, 39, 41, 43, 45 at `−0x00645C10(…)`) is unreachable, `k` being at most 4 (`[I]`, read).
  (run:2026-10-21-cat-emu-8b, 0x005CE2BA–0x005CE4C1)

### 6. Wraps and widths

- [C] Do 103's `calc1 << 8` and do 99's `Param1 << 6` are 32-bit shifts; `static.txt`'s `wrap` lines compute the
  bounds: `8 388 607 << 8 = 2 147 483 392` fits and `8 388 608 << 8` is `−2 147 483 648` as an s32, which do 103's
  signed `cmp edi, 0x100; jg` (`0x005CD44E`) floors to `0x100`; `33 554 431 << 6 = 2 147 483 584` fits and
  `33 554 432 << 6` wraps (do 99 stores the word unread before its boundary). The cases draw calc1 and Param1 over the
  full 32 bits (`sor_calcs`, the do 99 writer), so both sides of each bound are reached. Do 105's `h·A`, `h·B` and do
  141's `(lvl − 1)·Param6 + Param5` wrap as 32-bit products, the model's `s32` matching on full-range inputs.
  (run:2026-10-21-cat-emu-8b, `static.txt`)

## Corrections to earlier findings

- None. skills/0003's readings of start 55 (`sub_005CD910_SkillSt55LocalSeed`) and do 109's head hold; the
  `lane/p46m13` review's carried item (do 152's two `0x005CC3B0` calls) is answered in § 1.

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `srvmissilea` (`+0x48`), `calc1` (`+0x138`), `calc2` (`+0x13C`), `calc3`
(`+0x140`, after), `Param1`–`Param7` (`+0x148`–`+0x160`), `summon` (`+0xBC`), `summode` (`+0xBF`), `auralencalc`
(`+0x060`), `aurarangecalc` (`+0x064`), `auratargetstate` (`+0x082`), `ResultFlags`/`HitFlags`/`HitClass`
(`+0x12E`/`+0x130`/`+0x134`), `ELen`/`ELevLen1..3` (`+0x214`–`+0x220`) and the ELen calc (`+0x224`),
`ToHit`/`LevToHit`/`ToHitCalc` (`+0x198`–`+0x1A0`), the by-charge columns (skills/0008); `tbl:Missiles.txt:Param1`
(`+0x38`), `Vel` (`+0x9A`), `VelLev` (`+0x9B`); `tbl:MonStats.txt` and `MonStats2` through `0x005CC3B0` (`InfernoLen`)
as in skills/0016; unit `+0x00`, `+0x04`, `+0x0C`, `+0x10` mode, `+0x14`, `+0x20` seed, `+0x2C` path (`+0x02`, `+0x06`,
`+0x0C`, `+0x10`, `+0x12`, `+0x1C`, `+0x58`–`+0x60`), `+0x44`, `+0x48`, `+0x4E`, `+0x5C` stat list, `+0xA8` skills,
`+0xAC` queued hits, `+0xC4` bit 6; the used node `+0x0C`, `+0x18`–`+0x20`; game `+0xA8`.

## Dead ends

- None in the code. The first emulation (`dev/dev1`) mismatched on 98 cases in two model errors (the stale-link
  clearing of the caster's path `+0x58` by `UNIT_GetTargetUnit`, which the item batch already models; `0x0061A270`'s
  three stack words) and one control (`half_floor`) that failed on no case; `dev/dev2`–`dev/dev4` added the deciding
  classes and tuned the writer for the thin ones. No claim rests on them (`dev/notes.txt`).

## Open questions

- [L] What every boundary callee does past its entry (§§ 3–5): `0x00649EF0`'s direction, `0x005B34C0`'s spawn with its
  class-340 test, `0x0056DCC0`'s area and the callback `0x005D2E50`, `0x0057E270`, `NovaAtUnit` for ArcaneTower.
- [L] Whether row 91's Decrepify-like block (§ 5) is what the game shows when a monster casts Lower Resist through do
  112, and whether any caster reaches do 127 as a player (its life unit then 0).
- [L] Everything after each boundary (§§ 3–5), for a later batch or the harness.
