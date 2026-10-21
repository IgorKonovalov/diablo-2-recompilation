# 0012 — Catalogue batch `bar`: the barbarian start functions 32–34 and 38–41 and do functions 2, 9, 68–72 and 74–78

> **Subsystem:** skills/catalogue
> **Question:** what does each server start function 32, 33, 34, 38, 39, 40 and 41 (`srvstfunc`, `g_SkillStartFuncs`)
> and do function 2, 9, 68–72 and 74–78 (`srvdofunc`, `g_SkillDoFuncs`) of the barbarian batch do: which Skills,
> MonStats2 and unit fields it reads, which states, missiles and hits it makes, which draws it makes on which seed,
> what it returns, and which of that the emulator can confirm?
> **Date:** 2026-10-21   **Plan:** 0046 (Phase 1, batch `bar`)   **Status:** for review (`lane/p46m9`)

Static reading of the pinned `Game.exe` with objdump (and the lane's Ghidra copy `workspace/ghidra-p46m9` for the
emulation), then emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged, `286393aa…`) and the
`bar` families of `tools/skills_catalogue_emu.py` (§ 2; run:2026-10-21-cat-emu-bar in [experiments](experiments.md)).
Skills columns are named as in [Skills](../../tables/Skills.md), MonStats2 columns as in
[MonStats2](../../tables/MonStats2.md). The machinery that calls a start or do function is
[skills/0001 §§ 4–6](0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart); the two tier-A entries of this
batch (start 32, do 2) were read by plan 0045 in [skills/0001 § 11](0001-dispatch.md#11-the-skill-packet), and both are
emulated here. Stock values come from `workspace/logs/skills-cat-bar/rows.txt` (`excel_bin.py dump` of the 28 Skills
rows whose `srvstfunc` or `srvdofunc` is one of the batch's, by `rows.sh` beside it).

**Tag convention for this finding** (as skills/0011). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a
function entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site
(the return address at ESP), with a site control that fails every matched boundary case, and where the boundary sits
inside a helper the batch function called, the helper's return address into the batch function is compared at its
absolute stack slot, or the helper's single call site is shown from objdump (ruling 1 of the `lane/p46m6` review, at
each level of a helper chain; § 2); (c) the model gives and the checker compares every argument the claim uses
(registers the callee reads before it writes them, stack words, and for a pointer the bytes it points to), every byte
written before the call that the claim uses (the caster's `+0xC4`, node, path and frame words), and the state of **the
caster's and the target's seeds** at the boundary (both, in every case). Each such claim names the boundary it ends
at; **the callee and all code after it are not covered** and keep `[I]` (from the reading), marked "after, `[I]`" in
place, and what a callee makes of a compared argument is stated after the boundary (reverser review-fixes 13). No
claim rests on a callee-saved register that is not a boundary argument (ruling 1 of the `lane/p46m3` review). A plain
`[C]` rests on cases that return; a plain `[I]` is a code reading the emulator does not reach.
(run:2026-10-21-cat-emu-bar)

## Answer (summary)

- [C] **The batch.** 19 entries: start 32 `0x005D7EA0`, 33 `0x005D80C0`, 34 `0x005D8760`, 38 `0x005D8F50`, 39
  `0x005D97F0`, 40 `0x005D9D50`, 41 `0x005DA540`; do 2 `0x0056F1F0`, 9 `0x005D8E00`, 68 `0x005D83E0`, 69
  `0x005D81C0`, 70 `0x005D8470`, 71 `0x005D8570`, 72 `0x005D8780`, 74 `0x005D88B0`, 75 `0x005D89B0`, 76
  `0x005D9580`, 77 `0x005DA370`, 78 `0x005DA7E0`. Every one is `(ECX game, EDX unit; skill id, level)` with `ret 8`.
  All 19 are emulated. (data:g_SkillStartFuncs@0x00732140, data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [C] **No draw before the boundaries.** No function of the batch steps the caster's or the target's seed before its
  boundary or return (6 800 cases, both seeds compared in each). (run:2026-10-21-cat-emu-bar)
- [C] (ADR-0021; § 3) **The melee functions.** Start 32 tests the record, the target and the target's room (a town
  room → 0), then ends at `0x0056E520(ECX caster, EDX calc3)`; start 39 ends at `COMBAT_MeleeHitTest(target,
  SKILLS_GetToHit(caster, id, lvl), 0)` with a zeroed 0x70-byte packet. Do 2 (with `0 < srvoverlay ≤
  DataTables+0xBC0`) needs a target (→ 0) and a node of the caster's `+0xAC` chain naming the caster and the target
  (`QueuedHitFind`; none → **1, no delivery**) and ends at
  `sub_00621E40_UnitSetOverlayStat(target, srvoverlay, 0)` when the packet's `+0x04` bit 0 is set; then (with
  `auratargetstate` in `[0, States count)`) the same two tests and, on bit 0, `end = frame + max(auralencalc, 1)` and
  `STATLIST_Alloc(game+0x1C, 2, end, target type, guid)` for a target with no list of that state, else
  `sub_005417D0_UnitQueueEvent(ECX game, EDX target; 0xC, end, 0, 0)`; then (with `aurastate` in `(0, States count)`)
  `STATLIST_Alloc(game+0x1C, 4, 0, caster type, guid)` or `STATE_Set(caster, aurastate, 1)`; else bit 6 and
  `COMBAT_DeliverQueued(game, caster; target, 0)` (no target → 0). Do 9 and do 70 test **bit 8 of the caster's
  `+0x38`** (`sar 8; and 0x80000001`): do 9 ends at `DeliverQueued(target, 0)` from two sites, setting bit 6 only when
  the bit is 1; do 70 with the bit 1 sets bit 6 and ends at `sub_0056BD10_NearestUnitInRange(0, 0, reach + 4, 0x20003,
  target guid, 0)` (or the reach helper's inventory calls), and with it 0 calls start 32 (its boundary, the return
  address compared) and, when start 32 returns, `DeliverQueued(target, 0)`. (run:2026-10-21-cat-emu-bar)
- [C] (§ 4) **The corpse tests.** Start 34 returns `0x006455E0(target)`: 1 for a type-1 unit in mode 12 outside the
  `DataTables+0x150` set whose MonStats2 flag 7 is set, else 0. Start 33 returns `0x00645590(target)` (the same, and
  MonStats2 flag 12 through `0x00621F60`), or 0 when the target has state 118; neither reads a skill record.
  (run:2026-10-21-cat-emu-bar)
- [C] (ADR-0021; § 4) **The corpse do functions.** Do 69 and do 72 add the record test to start 33's and start 34's
  tests and end at `STATE_Set(target, 118, 1)`; do 75 ends at `sub_0064E7B0_FreeNearFallback(RoomAtSubtile(target
  room, x; y), &{x, y}, 2, 0x1000, 1)` with the target's position. (run:2026-10-21-cat-emu-bar,
  fn:sub_005D89B0_SkillDo75GrimWard@0x005D89B0)
- [C] (ADR-0021; § 5) **The warcries and Taunt.** Do 68 sets bit 6 **before** its record test, takes
  `SrvMissileByCharge` and admits a class in `[0, Missiles count)` (**class 0 admitted**), then ends at `NovaAtUnit`'s
  first `MissileCreate` with `{flags 3, owner the caster, class, +0x14/+0x18 the caster's position, +0x1C/+0x20 the
  first offset pair, id, lvl}` (velocity argument 0). Do 71 needs `auratargetstate` in `[0, States count)`; a type-1
  target ends at `0x0056E2F0(ECX target, EDX 0xC)` inside `0x005D8510`; any other target or none ends at
  `SKILLS_ForUnitsInRange(game, caster; 0, 0, 0x14, 0x8783, 0x0056BB20, &{0, 0x7FFFFFFF, x, y, 0x005D8510}, 0,
  0x006DAB88, 0x2B8)` inside `0x0056BBC0`. (run:2026-10-21-cat-emu-bar)
- [C] (ADR-0021; § 6) **Whirlwind, the leaps, Double Throw.** Start 38, 41 and do 76–78 find the node with
  `SKILLS_GetUnitSkill(caster, id)` (start 41 and do 78 with no record test); start 40 the used skill. Start 38 ends at
  `STATE_Set(caster, 0x12, 0)` inside `0x00571B70` (no node, no target point), returns 0 with state 12, ends at
  `InMeleeRange(caster, target, 0)`, or stores 0xC01 at the path's `+0x50` and ends at `PathSetType(path, 7)` with
  0x1C09 (a player) or 0x3C01 at `ebp−0x14`. Start 40: a monster with a target ends at
  `sub_005D9C80_MonSkillAttackDo(game)`; a monster without one stores −1 at the node's `+0x24` and ends at
  `FreeNearFallback(room, &point, UNIT_GetSizeX(caster), 0x3C01, 0)`; a player needs the target point in a room it
  reaches (not a town room unless Skills `+0x05` bit 0) and ends at `FreeNearFallback(RoomAtSubtile(…), &point, size,
  0x1C09, 1)` inside `0x005D9A10` with **the point pulled in to `aurarangecalc`**: for `d = max(UnitDistance, 1) >
  range`, `x = (x − ux) · range / d + ux` (32-bit, truncating), `y` alike. Start 41 ends at `InMeleeRange` inside
  `0x00645CA0` with a target; without one it takes the path's target point `(px, py)` and `d = UnitDistance`, 0 → 0,
  else ends at `COLL_PatternTestBool(room, (px − ux) · 2 / d + px, (py − uy) · 2 / d + py, path +0x48, 0x1C09)`. Do 74
  ends at `UnitGetWeapon`'s inventory query (no inventory → 0); do 76 at `0x005D9460(node, id, +0x18, +0x1C)` (a
  word 0, or `+0x0C & 3 == 3`), at `0x00553DC0(game, caster; 3)` (a live player with bit 0) or `0x006212C0(caster, 0)`
  (another live caster); do 77 at `UNIT_CancelEvents(game, caster; 1, 0)`; do 78 at `0x005DA120` (`+0x0C` bit 8),
  `0x005D9F70` (bit 7), `0x005DA660` (bit 9), in that order, else stores 0x1000 at `+0x0C` and returns 1.
  (run:2026-10-21-cat-emu-bar)
- [I] After, from the reading: the hits' rolls (start 32's and 39's elemental `SKILLS_RollElemDamage` on the caster's
  seed after `MeleeHitTest`); do 69's `RNG_Range(caster, 100) < calc1` and the potion pick `0x005D8100` (an inline
  LCG step on **the caster's** seed); do 72's two `RNG_Range(caster, 100)` (the second picks the quality by the
  `Param1..4` bands, `sub_005A8000_MonDropNoNoDrop`); do 68's 64 creations and `sub_005D8290_UnitApplyAuraState`;
  every callee boundary listed per function. (fn:sub_005D81C0_SkillDo69FindPotion@0x005D81C0,
  fn:sub_005D8780_CorpseFindItem@0x005D8780)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005D7EA0` | `sub_005D7EA0_SkillSt32Hit` | (P1.1 name) start 32 | I |
| `0x005D80C0` | `sub_005D80C0_SkillSt33CorpseTest` | start 33 | I |
| `0x005D8760` | `sub_005D8760_SkillSt34CorpseTest` | start 34 | I |
| `0x005D8F50` | `sub_005D8F50_SkillSt38Whirlwind` | start 38 | I |
| `0x005D97F0` | `sub_005D97F0_SkillSt39Berserk` | start 39 | I |
| `0x005D9D50` | `sub_005D9D50_SkillSt40Leap` | start 40 | I |
| `0x005DA540` | `sub_005DA540_SkillSt41LeapAttack` | start 41 | I |
| `0x0056F1F0` | `SKILL_MeleeDeliverDo` | (P1.1 name) do 2 | I |
| `0x005D8E00` | `sub_005D8E00_SkillDo09Frenzy` | do 9 | I |
| `0x005D83E0` | `sub_005D83E0_SkillDo68Warcry` | do 68 | I |
| `0x005D81C0` | `sub_005D81C0_SkillDo69FindPotion` | do 69 | I |
| `0x005D8470` | `sub_005D8470_SkillDo70DoubleSwing` | do 70 | I |
| `0x005D8570` | `sub_005D8570_SkillDo71Taunt` | do 71 | I |
| `0x005D8780` | `sub_005D8780_CorpseFindItem` | (items/0001 name) do 72 | C |
| `0x005D88B0` | `sub_005D88B0_SkillDo74DoubleThrow` | do 74 | I |
| `0x005D89B0` | `sub_005D89B0_SkillDo75GrimWard` | do 75 | I |
| `0x005D9580` | `sub_005D9580_SkillDo76Whirlwind` | do 76 | I |
| `0x005DA370` | `sub_005DA370_SkillDo77Leap` | do 77 | I |
| `0x005DA7E0` | `sub_005DA7E0_SkillDo78LeapAttack` | do 78 | I |
| `0x00645590` | `sub_00645590_CorpseTestF12` | `(unit)`, `ret 4`: `0x006455E0`'s tests, then `0x00621F60` | I |
| `0x006455E0` | `sub_006455E0_CorpseTest` | `(unit)`, `ret 4`: type 1, mode 12, not in the `DataTables+0x150` set, MonStats2 flag 7 | I |
| `0x00621F60` | `sub_00621F60_MonStats2Flag12` | `(unit)`, `ret 4`: a type-1 unit's MonStats2 flag 12 | I |
| `0x00571B70` | `sub_00571B70_SkillState18Clear` | `(ECX unit, EDX id)`: `STATE_Set(unit, 0x12, 0)`, then an event allocation (not read further) | I |
| `0x00643990` | `sub_00643990_SkillListSetUsed` | `(ECX list, EDX node)`: list `+0x10` = node (`UNIT_SetUsedSkill`'s) | I |
| `0x005D9CE0` | `sub_005D9CE0_LeapRoomTest` | `(EAX id; unit, x, y)`, `ret 0xC`: § 6 | I |
| `0x005D9A10` | `sub_005D9A10_LeapPoint` | `(EAX id; unit, lvl, &x, &y)`, `ret 0x10`: § 6 | I |
| `0x00645CA0` | `sub_00645CA0_LeapAttackPoint` | `(unit, target, &x, &y)`, `ret 0x10`: § 6 | I |
| `0x00649180` | `sub_00649180_UnitPathGet48` | `(unit)`: the path's `+0x48` | I |
| `0x005D8510` | `sub_005D8510_TauntTargetTest` | `(EDX unit)`: type 1, then `0x0056E2F0(unit, 0xC)`, `UnitIsDead`, `0x0058F090` (§ 5) | I |
| `0x0056BBC0` | `sub_0056BBC0_NearestByFilter` | `(ECX game, EDX unit; radius, filter fn)`, `ret 8`: § 5 | I |
| `0x005D8100` | `sub_005D8100_FindPotionPick` | `(EAX unit; game, id)`, `ret 8`: an inline LCG step on the unit's seed (§ 4, after do 69's boundary) | I |
| `0x005D9460` | `sub_005D9460_WhirlwindEnd` | do 76's boundary (not read beyond its first calls) | I |
| `0x005DA120` | `sub_005DA120_LeapAttackLand` | do 78's boundary for `+0x0C` bit 8 (not read beyond its calls) | I |
| `0x005D9F70` | `sub_005D9F70_LeapAttackPath` | `(EDI unit; node)`: do 78's boundary for bit 7 (not read beyond its calls) | I |
| `0x005DA660` | `sub_005DA660_LeapAttackHit` | `(EAX unit; game, id, lvl)`: do 78's boundary for bit 9 (not read beyond its calls) | I |

## Walkthrough

### 1. The table slots and the shared shape

- [C] `g_SkillStartFuncs[32, 33, 34, 38, 39, 40, 41]` and `g_SkillDoFuncs[2, 9, 68..72, 74..78]` are the Functions
  table's addresses (19 entries compared, `table_entries=19`). (data:g_SkillStartFuncs@0x00732140,
  data:g_SkillDoFuncs@0x007322B0, `static.txt`)
- [I] Start 32, 38, 39, 40 and do 2, 68, 69, 71, 72, 74, 75, 76, 77 test `0 ≤ id < DataTables+0xBA0` and a non-null
  record (`DataTables+0xB98 + 0x23C · id`) first and return 0 when it fails (do 68 after setting bit 6). Start 33, 34,
  41 and do 9, 70, 78 read no skill record of their own (start 41 and do 78 pass the id to `SKILLS_GetUnitSkill`).
  (0x005D80C0–0x005D80F6, 0x005D8760–0x005D877A, 0x005DA540–0x005DA568, 0x005D8E00–0x005D8E1B, 0x005D8470–0x005D848D,
  0x005DA7E0–0x005DA7F8)
- [I] **Stock rows** (`rows.txt`): start 32 on 116 Conversion (do 79, skills/0011), 126 Bash, 139 Stun, 144
  Concentrate (`srvoverlay` 54, `aurastate` 15 `concentrate`) and 326 BearSmite; do 2 on 1 Kick, 14 Power Strike, 19
  Impale, 111 Vengeance, 126, 139, 144, 152 Berserk (`aurastate` 95), 239 Fire Claws (`srvoverlay` 81), 326, 344
  MonPowerStrike and 347 MonIceSpear; start 33 on 131 Find Potion (do 69) and 150 Grim Ward (do 75, `auratargetstate`
  56); start 34 and do 72 on 142 Find Item; start 38 and do 76 on 151 Whirlwind (`aurastate` 174); start 39 on 152
  Berserk; start 40 and do 77 on 132 Leap (`srvmissilea` 346); start 41 and do 78 on 143 Leap Attack (`srvoverlay`
  147); do 9 on 147 Frenzy (`aurastate` 94); do 68 on 138 Shout, 146 Battle Cry, 149 Battle Orders, 154 War Cry and 155
  Battle Command (their `srvmissilea` 149, 219, 237, 235, 236); do 70 on 133 Double Swing; do 71 on 137 Taunt
  (`auratargetstate` 27); do 74 on 140 Double Throw. (`rows.txt`, tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc)

### 2. Emulation: the `bar` families

The method is skills/0011's: each case calls the function with `ECX` = the game, `EDX` = the caster and the stack
`(id, lvl)`, and dumps the stack, the caster's and the target's seeds, the caster's `+0xC4`, the second argument's slot
and, where a claim writes them, the path's `+0x50` (start 38), the used node's `+0x24` and the skill list's `+0x10`
(start 40) and the three unit-skill nodes' `+0x0C` (do 78). Emulated, not observed (new for this batch): `0x00645590`
and `0x006455E0` with `0x00621F60`, `UNIT_HasState` (`0x00639DF0`, `UNIT_TestStateBit`), `SKILLS_GetUnitSkill`
(`SKILLS_FindUnitSkill`), `0x00571B70` up to its `STATE_Set`, `UNIT_SetUsedSkill` with `0x00643990`, `0x005D9CE0`,
`0x005D9A10` up to its free-spot call, `0x00645CA0` up to its collision test, `sub_006417F0_UnitDistance`,
`UNIT_GetSizeX`, the path getters `0x006488C0`, `0x00648900`, `0x00648A00`, `0x00648A10`, `0x00649180`,
`sub_00648CE0_PathSetCollMask`, `0x005D8510` up to `0x0056E2F0`, `0x0056BBC0` up to `SKILLS_ForUnitsInRange`,
`sub_00535BC0_UnitGetWeapon` up to its inventory query, and the earlier batches' helpers (`UNIT_GetTargetUnit`,
`UNIT_GetUsedSkill`, `SKILLS_GetTargetXY`, `SrvMissileByCharge`, `NovaAtUnit` up to its first `MissileCreate`,
`QueuedHitFind`, `UNIT_FindStatListByState`, `UnitIsDead`, `RoomIsTown`, `RoomAtSubtile`, the node getters and
setters, `sub_0056E510_UnitMeleeReachPlus4` with `0x00622870`). Observed (new for this batch): `0x0056E520`,
`UnitQueueEvent`, `FreeNearFallback`, `PathSetType`, `MonSkillAttackDo`, `COLL_PatternTestBool`, `0x005D9460`,
`0x00553DC0`, `0x006212C0`, `0x005DA120`, `0x005D9F70`, `0x005DA660`; the others as declared since skills/0009–0011
(`InMeleeRange`, `COMBAT_MeleeHitTest`, `NearestUnitInRange`, `COMBAT_DeliverQueued`, `UnitSetOverlayStat`,
`STATLIST_Alloc`, `STATE_Set`, `0x0056E2F0`, `SKILLS_ForUnitsInRange`, `MissileCreate`, `UNIT_CancelEvents`, the
inventory calls `0x0063C9B0`/`0x0064F380`, the fatal path's `0x00408090`).

**Nested boundaries** (ruling 1 of the `lane/p46m6` review, at each level). Compared at the helper's return slot: do 70's
call of start 32 (`0x005D84F3` at `0x7FEFFFE4`; start 32 has two callers in the image, `0x005CAE9E` and `0x005D84EE`);
start 38's `0x00571B70` (`0x005D8F9B` at `0x7FEFFFAC`, the call at `0x005D8F96` that the no-node and the
no-target-point paths share; five calls in start 38, and no case reaches the no-path call at `0x005D9027`); do 68's `NovaAtUnit`
(`0x005D844A` at `0x7FEFFFD4`); do 71's `0x005D8510` (`0x005D85E2` at `0x7FEFFF74`) and `0x0056BBC0` (`0x005D8606` at
`0x7FEFFF6C`); start 40's `0x005D9A10` (`0x005D9EC9` at `0x7FEFFFC8`); start 41's `0x00645CA0` (`0x005DA583` at
`0x7FEFFFD0`); do 74's `UnitGetWeapon` (`0x005D88F6` at `0x7FEFFFE8`). Single call sites (`static.txt`): `0x005D9A10`,
`0x005D8510` and `0x0056BBC0` each have one call in the image (`0x005D9EC4`, `0x005D85DD`, `0x005D8601`; `0x005D8510`
is also pushed as an immediate at `0x005D85F8`); `0x00645CA0` two (`0x004C8DFA`, `0x005DA57E`), one in start 41;
`UnitGetWeapon` one in do 74 (`0x005D88F1`); `NovaAtUnit` one in do 68 (`0x005D8445`); do 70's reach chain:
`0x0056E510` once in do 70 (`0x005D84B7`), and `0x0056E510` calls `0x00622870` once (`0x0056E511`).

- [C] Four families, **6 800 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 2 397 matched boundary cases
  (39 function, boundary and return-address triples, each a `site` line) (`check.txt`; run:2026-10-21-cat-emu-bar):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `hit_bar` | start 32, 39, do 2, 9, 70 | 1 750 | town admitted (42); parity on bit 0 (224); overlay `<` count (15); no `max(…, 1)` (15); do 9 even with bit 6 (61) | AttackRate @0x005D7F16 (also from do 70); MeleeHitTest @0x005D9867; OverlaySet @0x0056F273; StatListAlloc @0x0056F326, @0x0056F3DC; QueueEvent @0x0056F344; StateSet @0x0056F414; DeliverQueued @0x0056F44F, @0x005D8E3E, @0x005D8E90, @0x005D84FF; NearestUnit @0x005D84D5; InvQuery @0x006228FD, MeleeInv @0x006228D2 (in `0x00622870`); returns 0, 1 |
  | `corpse_bar` | start 33, 34, do 69, 72, 75 | 2 500 | state 118 ignored (88); MonStats2 flag 12 ignored (109); point x/y swapped (36) | StateSet @0x005D8230, @0x005D87ED; FreeNear @0x005D8A43; returns 0, 1 |
  | `cry_bar` | do 68, 71 | 800 | do 68 without bit 6 (72); class 0 refused (72); velocity 1 (257); context x/y swapped (141) | MissileCreate @0x0056D4CC (in `NovaAtUnit`); MonTest2F0 @0x005D8537 (in `0x005D8510`); ForUnitsInRange @0x0056BC65 (in `0x0056BBC0`); returns 0 |
  | `move_bar` | start 38, 40, 41, do 74, 76, 77, 78 | 1 750 | no `+0x34` rule (33); size 2 for any caster (41); no range pull (22); mask swapped (27); factor 1 for 2 (90); bit 9 first (23) | StateSet @0x00571B80 (in `0x00571B70`); InMeleeRange @0x005D8FE2, @0x00645CBD (in `0x00645CA0`); PathSetType @0x005D9060; MonSkillAtk @0x005D9DFD; FreeNear @0x005D9E66, @0x005D9BAE (in `0x005D9A10`); CollTest910 @0x00645E1A, Fatal @0x00645DEE (in `0x00645CA0`); InvQuery @0x00535BF9 (in `UnitGetWeapon`); Ww9460 @0x005D97D6, @0x005D9621; Mode553DC0 @0x005D9659; Mode6212C0 @0x005D9663; CancelEvents @0x005DA3D0; Leap5DA120 @0x005DA810; Leap5D9F70 @0x005DA86D; Leap5DA660 @0x005DA890; returns 0, 1 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt`, 45 of 45 pins): the hash offsets, the `CALC_Eval` jump
  table, the skills calc function count `0x007457AC`, `g_BitMask32`, the town tables, the `UNIT_GetSizeX` jump table
  and `NovaAtUnit`'s offsets. The count's scan matches every operand naming the address (a `PTR` or `moffs` store, an
  immediate, a read): 0 stores, 0 immediates, 7 reads in `.text` (`ref_scan`, the condition of ruling 3 of the
  `lane/p46m5` review). Skills, MonStats, MonStats2, the stat lists, the queued hits, the skill nodes, rooms and units
  are scratch records written one field per field read.
- [C] **Inputs set in the memory spec** (ADR-0015, S1e review ruling 3): `g_pDataTables`, pointed at a scratch
  DataTables, is an input of the claims (no writer scan is cited for it); the security cookie is written as in 9a. No
  other image global is set. (run:2026-10-21-cat-emu-bar)
- [C] **The weak controls and their deciding classes** (ruling 4 of the `lane/p46m5` review). `hit_bar`'s `town_any`
  (42) fails exactly on start 32's and do 70's even-parity cases whose target room is a town room, `ovl_lt` (15) on do
  2's cases with `srvoverlay` equal to the overlay count, `end_nomax` (15) on do 2's `auratargetstate` cases whose
  `auralencalc` is below 1; `corpse_bar`'s `pt_swap` (36) on every do 75 case that reaches the free-spot call (x ≠ y in
  each); `move_bar`'s `sk34` (33) on the cases where a node's `+0x34` of −1 decides the node, `size2` (41) on start 40's
  monster free-spot cases whose MonStats2 size is not 2, `noscale` (22) on start 40's player cases farther than the
  range, `mask_swap` (27) on every start 38 `PathSetType` case, `f200` (23) on do 78's cases with bit 9 and bit 7 or 8
  set. Each family has a control failing 90 or more (`par_low` 224, `no12` 109, `vel1` 257, `x1` 90).
  (run:2026-10-21-cat-emu-bar)
- [I] ADR-0015 (3): the claims cover the code as a map. What the offsets mean keeps its own tag (Skills and MonStats2
  columns `[C]` by layout; unit, path, node, queued-hit and stat-list offsets `[I]`, skills/0001, skills/0008,
  combat/0001), and nothing here says when the game runs these functions or on which seed state.
  (run:2026-10-21-cat-emu-bar)

### 3. The melee functions: start 32, 39, do 2, 9, 70

```c
// fn:SKILL_MeleeDeliverDo@0x0056F1F0 (do 2), trimmed to its tests
if ((s16)rec->srvoverlay > 0 && srvoverlay <= DataTables->nOverlays) {
    if (!(t = UNIT_GetTargetUnit(game, u))) return 0;
    if (!(q = QueuedHitFind(u, t))) return 1;
    if (q->result & 1) UnitSetOverlayStat(t, srvoverlay, 0); }
if ((s16)rec->auratargetstate >= 0 && < nStates) {
    if (!(t = UNIT_GetTargetUnit(game, u))) return 0;
    if (!(q = QueuedHitFind(u, t))) return 1;
    if (q->result & 1) { end = game->frame + max(EvalCalc(auralencalc), 1);
        if (!(l = FindStatListByState(t, ats)) && !(l = STATLIST_Alloc(game->pool, 2, end, t->type, t->guid))) return 1;
        UnitQueueEvent(game, t; 12, end, 0, 0); STATE_Set(t, ats, 1); … ApplyAuraStats; } }
if ((s16)rec->aurastate > 0 && < nStates) { own list (flags 4) or STATLIST_Alloc(game->pool, 4, 0, …); STATE_Set(u, …, 1); … }
u->c4 |= 0x40;  if ((t = UNIT_GetTargetUnit(game, u))) { COMBAT_DeliverQueued(game, u; t, 0); } return t ? 1 : 0;
```

- [C] (ADR-0021; ends at `0x0056E520` @0x005D7F16) **Start 32** (tier A): the record, the target (each 0 → 0) and
  `RoomIsTown(UnitGetRoom(target))` (a town room → 0), then `0x0056E520(ECX caster, EDX SKILLS_EvalCalc(caster, calc3,
  id, lvl))` (both registers read at its entry before any write: `mov edi, ecx`, `mov ebx, edx`).
  (run:2026-10-21-cat-emu-bar `hit_bar`, fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0)
- [I] After start 32's boundary: `0x0056E520` makes a list (`STATLIST_Alloc(0, 4, 0, type, guid)`), links it and sets
  stat 68 to the value; then skills/0001 § 11's packet, `MeleeHitTest`, on a hit `calc1`, the `EType`/`calc4`
  conversion and `SKILLS_RollElemDamage` (the caster's seed), `COMBAT_ResolveAndQueue(…, SrcDam or 128)`, `calc2 << 8`
  added to the queued hit, the `aurastate` list; returns 1. (0x005D7F16–0x005D80AF, fn:sub_0056E520_SkillAttackRateList@0x0056E520)
- [C] (ADR-0021; ends at `COMBAT_MeleeHitTest` @0x005D9867) **Start 39** (`0x005D97F0`): the record and the target
  (0 → 0), a zeroed 0x70-byte packet at `ebp−0x7C` (compared), `MeleeHitTest(ECX game, EDX caster; target,
  SKILLS_GetToHit(caster, id, lvl), 0)`. (run:2026-10-21-cat-emu-bar `hit_bar`,
  fn:sub_005D97F0_SkillSt39Berserk@0x005D97F0)
- [I] After start 39's boundary: on a hit the packet as start 32's (no `calc3`, no `calc2` on the queued hit), the
  elemental roll, `ResolveAndQueue`; with `aurastate` in range, `end = frame + calc2` (`frame + 10` when that is not
  later), a timed list (flags 2) of the state with that end, `STATE_Set`, `StatListSetEnd`, event 12 at the end,
  `SKILLS_ApplyAuraStats`; returns 1. (0x005D9867–0x005D99FF)
- [C] (ADR-0021; ends at `UnitSetOverlayStat` @0x0056F273, `STATLIST_Alloc` @0x0056F326 or @0x0056F3DC,
  `UnitQueueEvent` @0x0056F344, `STATE_Set` @0x0056F414, or `COMBAT_DeliverQueued` @0x0056F44F) **Do 2** (tier A), as
  the excerpt: `srvoverlay` (`movzx; test ax, ax; jle`, then `movsx; cmp [DataTables+0xBC0]; jg`: in `(0, count]`);
  each of the overlay and `auratargetstate` blocks returns 0 without a target and **1 when `sub_0057D690_QueuedHitFind(caster,
  target)` finds no node** of the caster's `+0xAC` chain naming both (no delivery, bit 6 not set), and acts only when
  the found node's packet `+0x04` bit 0 is set; `auratargetstate` by `test ax, ax; jl` (0 admitted), `aurastate` by `jle` (0 refused); the end `frame +
  max(auralencalc, 1)` (`cmp eax, 1; jl`); `STATLIST_Alloc`'s first argument is the game's `+0x1C`; the
  `auratargetstate` list is looked up on the target and the `aurastate` list on the caster; with neither state block
  taken, bit 6 of the caster's `+0xC4`, then `DeliverQueued(ECX game, EDX caster; target, 0)`, or 0 without a target
  (bit 6 set). (run:2026-10-21-cat-emu-bar `hit_bar`, fn:SKILL_MeleeDeliverDo@0x0056F1F0)
- [I] After do 2's boundaries: the overlay block goes on to the `auratargetstate` test; the `auratargetstate` block's
  event, `STATE_Set(target, state, 1)`, the list's state, link and remove callback and `SKILLS_ApplyAuraStats` (a new
  list, then the event); the `aurastate` block's list (flags 4), `STATE_Set(caster, state, 1)` and
  `SKILLS_ApplyAuraStats`; then bit 6 and the delivery as above; returns 1 (1 also when an allocation fails). So, by the
  layouts, a skill with an overlay (Concentrate, Fire Claws) or a target state (none of the stock do-2 rows has one)
  delivers nothing when the caster has no queued hit on the target. (0x0056F273–0x0056F45A, `rows.txt`)
- [C] (ADR-0021; ends at `COMBAT_DeliverQueued` @0x005D8E3E or @0x005D8E90) **Do 9** (`0x005D8E00`, no record test):
  the target (none → 0); `(caster+0x38 >> 8) % 2` (signed, `sar 8; and 0x80000001; jns; dec; or −2; inc`): 0 →
  `DeliverQueued(ECX game, EDX caster; target, 0)` at the first site, bit 6 unchanged; non-zero → bit 6, then the
  second site. (run:2026-10-21-cat-emu-bar `hit_bar`, fn:sub_005D8E00_SkillDo09Frenzy@0x005D8E00)
- [I] After do 9's boundaries: parity 0: `sub_0057C9F0_QueuedHitRemove(target)`, `HandsRefresh`, `0x00580380`,
  `0x005D8C70(id, lvl)` (skills/0003 § 4's reading: `aurastate` for `auralencalc`, stat 169 counting up to `lvl`)
  and `0x005D8B10(target, id, lvl)` (the next hit); parity 1: `HandsRefresh`, `0x00580380`, `0x005D8C70`, then
  `NearestUnitInRange(0, 0, reach + 4, 0x20003, target guid, 0)` and `0x005D8B10` on what it finds. The function is
  `void`. (0x005D8E3E–0x005D8EEF)
- [C] (ADR-0021; ends at `NearestUnitInRange` @0x005D84D5, `InvQuery` @0x006228FD or `MeleeInv` @0x006228D2 inside
  `0x00622870`, start 32's `0x0056E520` @0x005D7F16 with do 70's return `0x005D84F3` compared, or `DeliverQueued`
  @0x005D84FF) **Do 70** (`0x005D8470`, no record test): the target (none → 0); parity 1: bit 6, `r =
  0x0056E510(caster)` (skills/0009 § 3's reach, `+ 4`), `NearestUnitInRange(ECX game, EDX caster; 0, 0, r, 0x20003,
  target guid, 0)`; parity 0: start 32 with `(ECX game, EDX caster; id, lvl)`, and when it returns, `DeliverQueued(ECX
  game, EDX caster; target, 0)`. (run:2026-10-21-cat-emu-bar `hit_bar`, fn:sub_005D8470_SkillDo70DoubleSwing@0x005D8470)
- [I] After do 70's boundaries: a found unit becomes the caster's path target (`sub_00620C10_UnitSetPathTargetUnit`),
  start 32 builds the hit on it and `DeliverQueued(found, 0)` delivers it (none → 0); returns 1. (0x005D84D5–0x005D8508)

### 4. The corpse functions: start 33, 34, do 69, 72, 75

- [C] **`0x006455E0(unit)`** gives 1 for a unit of type 1 in mode 12 (`+0x10`), outside the `DataTables+0x150` set
  (`sub_0063A770_UnitHasStateSet33`), whose MonStats2 flag 7 is set (`sub_004638A0_MonStats2FlagTest(class, 7)`), else
  0; **`0x00645590(unit)`** runs the same tests, then `0x00621F60(unit)` = flag 12 for a type-1 unit.
  **`UNIT_HasState(unit, 118)`** on a type-1 unit (the only type that reaches it after the corpse tests): its stat
  list's `+0x10` bit 31, then word 3 bit 22 of its `+0x58` array; that types 0 and 3 pass the type test too
  (0x00639DFA–0x00639E08) is not run here, `[I]`. (run:2026-10-21-cat-emu-bar `corpse_bar`, fn:sub_006455E0_CorpseTest@0x006455E0,
  fn:sub_00645590_CorpseTestF12@0x00645590)
- [C] **Start 34** (`0x005D8760`): no target → 0, else `0x006455E0(target)` (`neg; sbb; neg`). **Start 33**
  (`0x005D80C0`): no target → 0; `v = 0x00645590(target)`; `v` and state 118 → 0; else `v`. Neither tests the skill
  id. (run:2026-10-21-cat-emu-bar `corpse_bar`, fn:sub_005D80C0_SkillSt33CorpseTest@0x005D80C0,
  fn:sub_005D8760_SkillSt34CorpseTest@0x005D8760)
- [C] (ADR-0021; ends at `STATE_Set` @0x005D8230 or @0x005D87ED) **Do 69** and **do 72**: the record, the target
  (0 → 0), `0x00645590` (do 69) or `0x006455E0` (do 72) (0 → 0), state 118 (→ 0), then `STATE_Set(target, 118, 1)`.
  (run:2026-10-21-cat-emu-bar `corpse_bar`, fn:sub_005D81C0_SkillDo69FindPotion@0x005D81C0,
  fn:sub_005D8780_CorpseFindItem@0x005D8780)
- [I] After do 69's boundary: `0x0064C040(target)`, `v = calc1`, `RNG_Range(caster + 0x20, 100) < v` (`0x005D8255`,
  the caster's seed) → `0x005D8100(EAX caster; game, id)`: a byte `a` from the caster's room (`0x0061A1B0`, then
  `0x006427F0`; above 4 → 0) plus `5 ·` the game's `+0x6D` byte gives a row; an inline LCG step on **the caster's
  seed** (`× 0x6AC690C5` with carry, low word unsigned `% 100`) below `Param3` (`0x004EFC50`: Skills `+0x150`) gives
  column 1, below `Param3 + Param4` (`0x004EFC80`: `+0x154`) column 2, else 0; the word at `0x00741B58 + 4 · (3 · row
  + column)` (a row above `[0x00741B54]` → 0), then `0x0056DAB0(ECX game, EDX target; that word, 2)`; returns 1
  whether or not the roll passes. Stock Find Potion has `Param3` 30 and `Param4` 10. (0x005D8230–0x005D8284,
  0x005D8100–0x005D81B9, 0x004EFC50–0x004EFCAA)
- [I] After do 72's boundary: `0x0064C040(target)`, `RNG_Range(caster + 0x20, 100)` (`0x005D8814`) **not below**
  `calc1` → returns 0; else a second `RNG_Range(caster + 0x20, 100)` (`0x005D882F`) `r` gives the quality: 1, then 2
  for `Param1 ≤ r < Param1 + Param2`, 3 for the next band of `Param3`, 4 for the next of `Param4` (Skills `+0x148..+0x154`,
  signed compares); `sub_005A8000_MonDropNoNoDrop(ECX game, EDX target; caster, quality)`; returns 1.
  (0x005D87ED–0x005D889F)
- [C] (ADR-0021; ends at `FreeNearFallback` @0x005D8A43) **Do 75** (`0x005D89B0`): the record, the target and
  `0x00645590(target)` (each 0 → 0); `x, y` = the target's `UnitGetSubX/Y`; its room (0 → 0), `RoomAtSubtile(room, x;
  y)` (0 → 0); `FreeNearFallback(that room, &{x, y}, 2, 0x1000, 1)` (the point at `ebp−0x10`, compared by content).
  (run:2026-10-21-cat-emu-bar `corpse_bar`, fn:sub_005D89B0_SkillDo75GrimWard@0x005D89B0)
- [I] After do 75's boundary: with a spot and a type-1 target, its MonStats2 record's `+0x05` bit 3 picks
  `srvmissilec` (`+0x4C`), else bit 2 `srvmissileb` (`+0x4A`), else `srvmissilea` (`+0x48`); a class in `[0, Missiles
  count)` → `MissileCreate` with `{flags 1, owner the caster, class, +0x14/+0x18 the spot, id, lvl}`,
  `STATE_Set(target, 0x68, 1)`, `STATE_Set(target, 118, 1)`, `0x0064C040(target)`, returns 1; otherwise 0.
  (0x005D8A43–0x005D8AFF)
- [I] By the layouts ([MonStats2](../../tables/MonStats2.md)): flag 7 of `0x004638A0` is `+0x004` bit 7, `corpseSel`,
  and flag 12 is `+0x005` bit 4, `soft`; do 75's `+0x05` bits 3 and 2 are `large` and `small`. So Find Item needs a
  selectable corpse, Find Potion and Grim Ward a selectable `soft` one, and Grim Ward takes `srvmissilec` on a `large`
  corpse, `srvmissileb` on a `small` one and `srvmissilea` (stock `grimwardmediumstart`) otherwise. The play
  consequences are not run here. (tbl:MonStats2.txt:corpseSel, tbl:MonStats2.txt:soft, tbl:MonStats2.txt:large,
  tbl:MonStats2.txt:small)

### 5. The warcries and Taunt: do 68, 71

- [C] (ADR-0021; ends at `MissileCreate` @0x0056D4CC inside `NovaAtUnit`, do 68's return `0x005D844A` compared)
  **Do 68** (`0x005D83E0`): bit 6 of the caster's `+0xC4` first; the record (→ 0, bit 6 kept); `m =
  SrvMissileByCharge(ECX caster, EDX id)` (skills/0008 § 7), `m < 0` or `≥ DataTables+0xB6C` → 0 (`jl`, `jge`: class
  0 admitted); `NovaAtUnit(ECX game, EDX caster; caster, m, id, lvl, 0)`, whose first creation passes the 0x5C-byte
  block `{+0x00 3, +0x04 caster, +0x10 m, +0x14/+0x18 the caster's position, +0x1C/+0x20 the words at 0x006E1288 and
  0x006E1388, +0x2C id, +0x30 lvl}` (compared by content; with the last argument 0, no `+0x04` flag and no `+0x28`).
  (run:2026-10-21-cat-emu-bar `cry_bar`, fn:sub_005D83E0_SkillDo68Warcry@0x005D83E0,
  fn:sub_0056D400_SkillNovaAtUnit@0x0056D400)
- [I] After do 68's boundary: `NovaAtUnit`'s 63 further creations (the offsets at a stride of 4 up to 0x100 bytes),
  then `sub_005D8290_UnitApplyAuraState(ECX game, EDX caster; caster, id, lvl)`; returns 1. By the layouts the
  creations are the `srvmissilea` rows the stock rows name (`shout`, `battlecry`, `battleorders`, `warcry`,
  `battlecommand`), whose hit functions skills/0006 and the damage function skills/0005 read. (0x005D844A–0x005D8460)
- [C] (ADR-0021; ends at `0x0056E2F0` @0x005D8537 inside `0x005D8510`, do 71's return `0x005D85E2` compared, or at
  `SKILLS_ForUnitsInRange` @0x0056BC65 inside `0x0056BBC0`, return `0x005D8606` compared) **Do 71** (`0x005D8570`):
  the record and `auratargetstate` in `[0, States count)` (`test ax, ax; jl`; else 0); a target of type 1 →
  `0x005D8510(EDX target)` → `0x0056E2F0(ECX target, EDX 0xC)`; a target of another type → `0x005D8510` gives 0, and,
  as with no target, `0x0056BBC0(ECX game, EDX caster; 0x14, 0x005D8510)` → `SKILLS_ForUnitsInRange(ECX game, EDX
  caster; 0, 0, 0x14, 0x8783, 0x0056BB20, &ctx, 0, 0x006DAB88, 0x2B8)` with the 20-byte `ctx = {0, 0x7FFFFFFF, the
  caster's x, y, 0x005D8510}` (compared by content). (run:2026-10-21-cat-emu-bar `cry_bar`,
  fn:sub_005D8570_SkillDo71Taunt@0x005D8570, fn:sub_0056BBC0_NearestByFilter@0x0056BBC0)
- [I] After do 71's boundaries: `0x005D8510` returns 1 for a live (`UnitIsDead` 0) type-1 unit that `0x0056E2F0(unit,
  0xC)` accepts and whose `0x0058F090` pair has its first word −1 or its second non-zero; then `UnitsHostile(caster, target)`; a
  refused target goes to the search, whose result is the context's first word (`0x0056BB20` keeps the nearest unit
  the filter accepts, by the `0x7FFFFFFF` start). With a unit: `auralencalc`, a 0x68-byte block `{game, …, 1, flag,
  id, lvl, length, aurastat1..6 with aurastatcalc1..6 (a stat below 0 or past the ItemStatCost count ends the list
  with −1), state}` (the flag set when a stat's ItemStatCost `+0x05` bit 1 is), `sub_005C35C0_CurseApplyCb` on the
  unit, `0x005B0D70(−666, −666)`, `0x005DD330`, `UNIT_CancelEvents(2, 0)`, event 2 at `frame + 1`, and the unit's
  path target set to the caster; returns 1. No draw is read in do 71. (0x005D8510–0x005D8569, 0x005D860B–0x005D8755)

### 6. Whirlwind, the leaps and Double Throw: start 38, 40, 41, do 74, 76, 77, 78

- [C] **`SKILLS_GetUnitSkill(ECX unit, EDX id)`** (`SKILLS_FindUnitSkill`): the caster's `+0xA8` list (0 → 0), its
  chain from `+0x04` (next `+0x04`); a node qualifies when the s16 at its record `[node+0x00]` equals the id (32-bit
  compare of the `movsx`) and its `+0x3C` is 0; the first is kept, a later one replaces it when its `+0x34` is −1, or,
  when the kept one's `+0x34` is not −1, when its `+0x28` is greater (signed). (run:2026-10-21-cat-emu-bar `move_bar`,
  fn:SKILLS_FindUnitSkill@0x00643810)
- [C] (ADR-0021; ends at `STATE_Set` @0x00571B80 inside `0x00571B70`, return `0x005D8F9B` compared, at
  `InMeleeRange` @0x005D8FE2 or at `PathSetType` @0x005D9060) **Start 38** (`0x005D8F50`): the record (→ 0); no node or
  no target point (`SKILLS_GetTargetXY`) → `0x00571B70(ECX caster, EDX id)` → `STATE_Set(caster, 0x12, 0)`;
  `UNIT_HasState(caster, 12)` → 0; with a target, `InMeleeRange(caster, target, 0)`; without one, `ebp−0x14` = 0x1C09
  for a caster of type 0, else 0x3C01 (`sete; neg; sbb; and 0xFFFFE008; add 0x3C01`), the path's `+0x50` = 0xC01
  (`PathSetCollMask`), `PathSetType(path, 7)`. (run:2026-10-21-cat-emu-bar `move_bar`,
  fn:sub_005D8F50_SkillSt38Whirlwind@0x005D8F50)
- [I] After start 38's boundaries: `PathPlan(path, caster, 0)` (0: `0x00571B70` and the mask put back), the speed
  `sub_0056E5B0_UnitWalkVelocity` into `PathSetSpeed`, the mask 0x401, `0x006487D0`'s point list (none: as a failed
  plan), its last point into `COLL_PatternMark(room, x, y, …, 0x80 or 0x100)`, `0x005544B0`, `STATE_Set(caster, 0x12,
  1)`, the node's `+0x0C` = 1, `+0x18`/`+0x1C` the point, `+0x20` = −1, `+0x24` = 0; with `aurastate` in range
  `STATE_GroupClear(0)`, `STATE_ApplyTimed` for `auralencalc`, `SKILLS_ApplyAuraStats`, `0x005C6DC0`, stats 350/351,
  the `auraevent`s, `UnitSetStateBit`; returns 1. With a target in melee range: `0x00571B70`, `0x0056E230(game,
  caster; target)` returned. A target **not** in melee range takes the no-target branch (`je 0x005D9006`), the path
  move to the target point. Not run: a caster with no path (`+0x2C` 0) on that branch calls `0x00571B70` at
  `0x005D9027` and returns 0. (0x005D8FE2–0x005D92C8, 0x005D9006–0x005D902C)
- [C] (ADR-0021; ends at `MonSkillAttackDo` @0x005D9DFD, `FreeNearFallback` @0x005D9E66, or `FreeNearFallback`
  @0x005D9BAE inside `0x005D9A10`, return `0x005D9EC9` compared) **Start 40** (`0x005D9D50`): the record and the used
  skill (0 → 0). A caster of type 1 with a target: `sub_005D9C80_MonSkillAttackDo(game)`; without one, the target
  point (none → `UNIT_SetUsedSkill(caster, 0)`, the list's `+0x10` = 0, return 0), the node's `+0x24` = −1,
  `FreeNearFallback(UnitGetRoom(caster), &{x, y}, UNIT_GetSizeX(caster), 0x3C01, 0)`. Any other caster: the target
  point (none → 0); `0x005D9CE0`: the caster's room (0 → 0), `RoomAtSubtile(room, x; y)` (0 → 0), and unless Skills
  `+0x05` & `g_BitMask32[0]`, a town room → 0; then `0x005D9A10`: `range` = `aurarangecalc` (Skills `+0x64`), `d =
  UnitDistance(caster, x, y)` raised to 1, and for `d > range` the point becomes `((x − ux) · range / d + ux, (y − uy) ·
  range / d + uy)` (`imul`, `cdq; idiv`); `FreeNearFallback(RoomAtSubtile(caster room, x; y), &{x, y}, size, 0x1C09,
  1)`. `UNIT_GetSizeX` is 2 for type 0 and the MonStats2 `+0x08` byte (`movsx`) for type 1 (0 without a row);
  `UnitDistance` is `(min + 2 · max) / 2` of `|dx|`, `|dy|` (truncating); its `jge` that takes a negative absolute
  value as 0 is reached only by `INT_MIN`, not run, `[I]`.
  (run:2026-10-21-cat-emu-bar `move_bar`, fn:sub_005D9D50_SkillSt40Leap@0x005D9D50,
  fn:sub_005D9A10_LeapPoint@0x005D9A10, fn:sub_006417F0_UnitDistance@0x006417F0)
- [I] By the layouts, `aurarangecalc` is the leap's range, so a player's leap lands at most that far along the line to
  the target point (stock 132 Leap fills `aurarangecalc`). After start 40's boundaries: `0x005D9A10` tries the spot,
  `COLL_PatternTestBool`, `0x00645910` and the distance again for up to three points, the second and third shifted by
  the clamped `(±2, ±2)` steps, returning 0 when none fits; then `COLL_PatternMark(room, x, y, …, 0x80)`,
  `0x005544B0`, `STATE_Set(caster, 0x12, 1)`, the node's `+0x18`/`+0x1C` the point, for a monster with a target `+0x20`
  its type and `+0x24` its guid, `+0x0C` = 0x80; returns 1. (0x005D9B2F–0x005D9C6E, 0x005D9ECD–0x005D9F64)
- [C] (ADR-0021; ends at `InMeleeRange` @0x00645CBD, `COLL_PatternTestBool` @0x00645E1A or the fatal path's
  `0x00408090` @0x00645DEE inside `0x00645CA0`, return `0x005DA583` compared) **Start 41** (`0x005DA540`): no node → 0;
  `0x00645CA0(caster, target, &x, &y)`: with a target, `InMeleeRange(caster, target, 0)`; without one, `(px, py)` the
  caster's path words `+0x10`/`+0x12`, `d = UnitDistance(caster, px, py)`, 0 → 0 (start 41 then returns 0), else `x =
  2 (px − ux) / d + px`, `y = 2 (py − uy) / d + py` (`add eax, eax; cdq; idiv`), the caster's room (none → the fatal
  path) and `COLL_PatternTestBool(room, x, y, path +0x48, 0x1C09)`. (run:2026-10-21-cat-emu-bar `move_bar`,
  fn:sub_005DA540_SkillSt41LeapAttack@0x005DA540, fn:sub_00645CA0_LeapAttackPoint@0x00645CA0)
- [I] After start 41's boundaries: a target **not** in melee range (`InMeleeRange` 0) makes `0x00645CA0` take
  `(px, py)` from the target's position (the same getters as the caster's: the path's `+0x0C`/`+0x10` for types 2, 4
  and 5, else `0x006488C0`/`0x00648900`) instead of the caster's path words, then go on as without a target
  (0x00645D2B–0x00645D88). When `COLL_PatternTestBool` gives 0 the extended point is kept; when it gives non-zero,
  `0x00645CA0` calls `FreeNearFallback(room, &{px, py}, UNIT_GetSizeX(caster), 0x1C09, 0)` around the unextended
  point (0 → 0) and stores the spot it finds (0x00645E1A–0x00645E53); start 41 then marks the pattern, fills the node (`+0x18`/`+0x1C` the point, `+0x20`/`+0x24`
  the target's type and guid, or `+0x20` = 6), `+0x0C` = 0x1080, `STATE_Set(caster, 0x12, 1)`, and for a target in
  state 54 `0x00570420(target, 100)`; returns 1. A target in melee range: `0x0056E230(game, caster; target)`, returns
  1. (0x00645E1A–0x00645E80, 0x005DA5B0–0x005DA654)
- [C] (ADR-0021; ends at `InvQuery` @0x00535BF9 inside `UnitGetWeapon`, return `0x005D88F6` compared) **Do 74**
  (`0x005D88B0`): the record (→ 0); `UnitGetWeapon(ECX caster)`: no inventory (`+0x60`) → 0 → do 74 returns 0; else
  its inventory query. (run:2026-10-21-cat-emu-bar `move_bar`, fn:sub_005D88B0_SkillDo74DoubleThrow@0x005D88B0)
- [I] After do 74's boundary: the weapon's `0x006288A0` value (the item record's `+0xFA` word for an item unit, −1
  otherwise) in `(0, Missiles count)`, else 0; `ITEMS_UnitIsType(weapon, 0x26)` picks `SkillMissileCreateLob` or
  `SkillMissileCreate(…, 1)` with that class; the missile gets stat 19 = `SKILLS_GetToHit` and stat 25 = `calc1`
  (`UnitAddStat`); returns 1. (0x005D88F6–0x005D89A8)
- [C] (ADR-0021; ends at `0x005D9460` @0x005D97D6 or @0x005D9621, `0x00553DC0` @0x005D9659 or `0x006212C0`
  @0x005D9663) **Do 76** (`0x005D9580`): the record and the node (0 → 0); the node's `+0x18` or `+0x1C` 0 →
  `0x005D9460(ECX game, EDX caster; node, id, +0x18, +0x1C)` at the second site; `+0x0C & 3 == 3` → the same call at the
  first site; `+0x0C` bit 0 clear → 0; `UnitIsDead(caster)` → 0; a caster of type 0 → `0x00553DC0(ECX game, EDX
  caster; 3)`, else `0x006212C0(caster, 0)`. (run:2026-10-21-cat-emu-bar `move_bar`,
  fn:sub_005D9580_SkillDo76Whirlwind@0x005D9580)
- [I] After do 76's boundaries: `0x005D9460` clears the node's `+0x0C`, calls `0x005544B0` and `0x00571B70`, unmarks the
  pattern, restores the mask and removes a state's list (`STATE_Set`, `UNIT_UnlinkStatList`, `STATLIST_FreeIfPlain`);
  in the hit branch a monster's `+0x48` = 0x400, then `0x005D9320` gives a count of passes, each taking
  `NearestUnitInRange(0, 0, 5, 3, node +0x20, 0)`, storing its guid at `+0x20` (none: −1 and stop), `MeleeHitTest(unit,
  SKILLS_GetToHit, 0)`, on a hit the flags, `calc1`, `SKILLS_RollElemDamage` (the caster's seed),
  `ResolveAndQueue(SrcDam or 128)` and `DeliverQueued`, and toggling `+0x0C` bit 13; returns 1. Do 76 itself returns 0
  after the call at the word-0 site (`0x005D97D6`, `xor eax, eax`) and 1 after the `+0x0C & 3 == 3` site
  (`0x005D9621`). (0x005D9460–0x005D957F, 0x005D9663–0x005D97C4, 0x005D9621–0x005D962C, 0x005D97D6–0x005D97DE)
- [C] (ADR-0021; ends at `UNIT_CancelEvents` @0x005DA3D0) **Do 77** (`0x005DA370`): the record and the node (0 → 0),
  then `UNIT_CancelEvents(ECX game, EDX caster; 1, 0)`. (run:2026-10-21-cat-emu-bar `move_bar`,
  fn:sub_005DA370_SkillDo77Leap@0x005DA370)
- [I] After do 77's boundary: node `+0x0C` bit 8 → `0x005DA120(game, node)`, and for a caster not of type 1 a zeroed
  0x70-byte packet with `+0x04` = 9 into `sub_0056BAD0_AreaHitAt(0, 0, calc1, &packet, 0)`; bit 7 → `0x005D9F70(node)`
  returned; otherwise a non-monster caster's `+0x0C` = 0; returns 1. (0x005DA3D0–0x005DA46F)
- [C] (ADR-0021; ends at `0x005DA120` @0x005DA810, `0x005D9F70` @0x005DA86D or `0x005DA660` @0x005DA890) **Do 78**
  (`0x005DA7E0`): no node → 0; `f` = the node's `+0x0C`: bit 8 → `0x005DA120(EAX caster; game, node)`; else bit 7
  (`test al, al; jns`) → `0x005D9F70(EDI caster; node)`; else bit 9 → `0x005DA660(EAX caster; game, id, lvl)`; else
  `+0x0C` = 0x1000 and 1. Each register named is read by the callee before it writes it (`mov edi, eax`, `mov esi,
  [edi+0x2C]`, `mov esi, eax`). (run:2026-10-21-cat-emu-bar `move_bar`, fn:sub_005DA7E0_SkillDo78LeapAttack@0x005DA7E0)
- [I] After do 78's boundaries (not read in full): `0x005DA120` unmarks the pattern, restores the mask and type, and
  calls `0x005DA020`, the event functions, `0x00571B70` and `UnitDistance`; when it gives non-zero, `0x005DA490` (the
  target in melee range, or the nearest unit) decides `0x00553DC0(game, caster; 0x10)` and 1, or the events cancelled
  and requeued at `frame + 4` and 0; `0x005D9F70` sets the node's `+0x0C` to 0x1101, the path's mask and target point
  (the node's `+0x18`/`+0x1C`), its type, a speed from the MonStats or CharStats record, `PathSetSpeed` and
  `PathPlan`; `0x005DA660` makes a hit (`MeleeHitTest`, `calc1`, the elemental roll on the caster's seed,
  `ResolveAndQueue`, `DeliverQueued`, `UnitSetOverlayStat(target, srvoverlay, 0)`, the state list removed). Do 78
  returns 1 when `0x005DA120` gives 0 (`je 0x005DA8A2`), and returns `0x005D9F70`'s or `0x005DA660`'s value on the
  bit-7 and bit-9 paths. (0x005DA810–0x005DA8AB, 0x005DA120–0x005DA35F, 0x005D9F70–0x005DA01F, 0x005DA660–0x005DA7D5)

## Corrections to earlier findings

- skills/0001 § 11 and skills/0003 § 5 (tier A), carried there as dated notes: start 32 and do 2 are now `[C]` up to
  their boundaries (ADR-0021). Do 2's overlay and `auratargetstate` blocks each return **1 without delivering** when
  `QueuedHitFind(caster, target)` finds no `+0xAC` node naming both, and act only when the found node's packet `+0x04`
  bit 0 is set; its overlay test is
  `0 < srvoverlay ≤ DataTables+0xBC0`, `auratargetstate` admits 0 and `aurastate` refuses it.
  (fn:SKILL_MeleeDeliverDo@0x0056F1F0, fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0)
- items/0001's Functions row for `sub_005D8780_CorpseFindItem`, carried there as a dated note: its rolls are on **the
  caster's** seed (`EDX` → `edi` at `0x005D878D`, `add edi, 0x20; mov ecx, edi` at `0x005D8808`), two `RNG_Range(…, 100)` at `0x005D8814` and
  `0x005D882F`, not the monster's, `[I]` from the reading. (0x005D878D, 0x005D8808–0x005D882F)

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `srvoverlay`, `aurastate`, `auratargetstate`, `auralencalc`,
`aurarangecalc`, `calc1`, `calc2`, `calc3`, `Param1..4`, `srvmissilea..c` (through `SrvMissileByCharge` and do 75),
`ToHit`, `LevToHit`, `ToHitCalc`, Skills `+0x05`; `tbl:MonStats2.txt` flags 7 and 12 and the `+0x08` byte; unit
`+0x00`, `+0x04`, `+0x0C`, `+0x10`, `+0x2C` path (`+0x02`, `+0x06`, `+0x10`, `+0x12`, `+0x1C`, `+0x48`, `+0x50`),
`+0x38`, `+0x5C` stat list, `+0x60` inventory, `+0xA8` skills (`+0x04` chain, `+0x10` used node; node `+0x0C`,
`+0x18`, `+0x1C`, `+0x24`, `+0x28`, `+0x34`, `+0x3C`), `+0xAC` queued hits, `+0xC4` bit 6, `+0xC6`; game `+0x1C`,
`+0xA8`.

## Dead ends

- None in the code. The first emulation of `corpse_bar` and `move_bar` showed three tool faults, fixed before any
  output was kept: no dumps of the path, node and list words the models compare; do 76's `+0xC6` byte written over the
  `+0xC4` word the model compared; and too few points inside rooms to reach do 75's and start 40's free-spot calls.

## Open questions

- [L] What `0x0056E520`'s stat 68 list does to the attack (start 32), and what `0x0056E2F0(unit, 0xC)` tests (do 71)
  (§§ 3, 5).
- [L] Whether bit 8 of the caster's `+0x38` is the animation's alternating hand, as do 9's and do 70's two branches
  suggest (§ 3), a harness check.
- [L] What `0x005D9460`, `0x00553DC0`, `0x006212C0`, `0x005DA120`, `0x005D9F70` and `0x005DA660` do in full (§ 6).
- [L] Everything after each boundary (§§ 3–6), for a later batch or the harness.
