# 0006 — Catalogue batch 9c: missile server hit functions 1–29

> **Subsystem:** skills/catalogue
> **Question:** what does each missile server hit function 1–29 (`pSrvHitFunc`, `g_MissileSrvHitFuncs`) do: which
> Missiles and Skills columns and `MissileData` words it reads, which missiles, states and units it creates or
> touches, which draws it makes on which seed, what result it returns, and which of that the emulator can confirm?
> **Date:** 2026-10-20   **Plan:** 0046 (Phase 1, batch 9c)   **Status:** for review (`lane/p46m3`)

Static reading of the pinned `Game.exe` in Ghidra 12.1.2 (lane copy `workspace/ghidra-p46m3`, symbols replayed from
`re/symbols.csv`) and objdump, then emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged,
`286393aa…`) and the 9c families of `tools/skills_catalogue_emu.py` (§ 2; run:2026-10-20-cat-emu-9c in
[experiments](experiments.md)). Missiles columns are named as in [Missiles](../../tables/Missiles.md), Skills columns
as in [Skills](../../tables/Skills.md), packet fields as in `re/types/combat.h` (`DamagePacket`). The machinery that
calls a hit function and acts on its result is [skills/0002 § 5](0002-missiles.md#5-the-hit); batches 9a and 9b are
[skills/0004](0004-missile-do-1-18.md) and [skills/0005](0005-missile-do-19-36-damage.md). Stock values come from
`workspace/logs/skills-cat-9c/rows.txt` (`eaec0e1a…`, `excel_bin.py dump` of the 60 rows whose `pSrvHitFunc` is
1–29).

**Tag convention for this finding** (as skills/0005). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md) (accepted by the owner 2026-10-20): (a) nothing is
patched and each boundary is a function entry reached by the program's own flow; (b) the checker asserts per case the
boundary and its call site (the return address at ESP), with a site control that fails every matched boundary case;
(c) the model gives and the checker compares every argument the claim uses (registers, stack words, and for a pointer
into the caller's frame the bytes it points to), every byte written before the call, and **the state of the
missile's, the owner's and the target's seeds** at the boundary (all three, in every case: the untouched-seed
comparison of the `lane/p46m2` review). Each such claim names the boundary it ends at; **the callee and all code after
it are not covered** and keep `[I]` (from the reading), marked "after, `[I]`" in place. A plain `[C]` rests on cases
that return; a plain `[I]` is a code reading the emulator does not reach. (run:2026-10-20-cat-emu-9c)

## Answer (summary)

- [I] **The batch.** 25 entries: hit 1–4, 7–10, 12–22, 24–29 (the numbers a stock row names; 5, 6, 11, 23 are table
  entries no row uses). Hit 2, 3, 14 and 17 are tier A (skills/0003 § 6); 3, 14 and 17 are emulated here too, 2 is
  not. Every hit function is `(ECX game, EDX missile; unit)` with `ret 4` and returns the result word of
  skills/0002 § 5 (bit 0 end, bit 1 damage, bit 2 keep and return at once). (data:g_MissileSrvHitFuncs@0x0073C840,
  `static.txt`)
- [C] **Draws before the boundaries, all three seeds compared.** Hits 1, 9 and 13 roll the missile's `EType` into a
  fresh packet (`sub_005A8C70_MissileRollEType`, one `RNG_RangeB` on the missile's seed per element roll whose two
  stats are ≥ 1); hit 7's heal draws one `RNG_RangeB(missile seed, (calc2 << 8) − (calc1 << 8))` and, when the sum is
  ≤ 0, one more through `sub_005A8910_MissileElemRoll` (stats 22/21). No other hit function of the batch draws before
  its boundary or return, and no case steps the owner's or the target's seed (8 400 cases; a control that moves the
  missile's draws to the owner's seed fails on every case that drew). Draws in a boundary callee (`BuildDamage`,
  `AreaHitAt`, the creations) are not covered. (§§ 3, 4, 6, run:2026-10-20-cat-emu-9c)
- [C] (ADR-0021; up to `AreaHitAt` or `MISSILE_BuildDamage`, §§ 3–5) **Area hits.** Hit 1 (fireballs): with an owner,
  radius `sHitPar1 > 0 ? sHitPar1 : max(calc1, 1)`, the `EType` roll on the hit unit, `HitFlags` OR'ed into packet
  `+0x00` and `ResultFlags` into `+0x04`, then `AreaHitAt(owner; x, y, radius, packet, 0)`; returns 1 (after, `[I]`).
  Hit 13 (glacial spike, hell meteor): radius from `aurarangecalc`, and `sHitPar2 > 0 ? sHitPar2 : auralencalc`, when
  above 0, as the length field of the `EType` (`0x005A8F20`: cold 4 `+0x30`, poison 5 `+0x2C`, 9 `+0x44`, 11 `+0x18`,
  freeze 12 `+0x34`). Hit 24 (pantherpotorange) and hit 3 → 44 (fire potions, bomb) and tier-A hit 14 (meteors) build
  the packet with `MISSILE_BuildDamage(owner; m, unit, packet)` instead. Hit 44 takes any **non-zero** `sHitPar1`
  (negative included) as its radius and has no owner test; hit 3 runs hit 44 only at the end of life (unit 0) and
  returns 0 for a unit. Hit 9 (immolation arrow) first clears the missile's stats 56 and 134 (`UnitSetStat`, the
  boundary) when `HitSubMissile1 ≥ 0`. (§§ 3–5, run:2026-10-20-cat-emu-9c `area9c`)
- [C] (§ 6) **Hit 7 (holy bolt)** heals a unit that is the owner's pet (`TargetPet` set, the unit a monster whose owner
  reference is the owner player's guid): `life = min(stat 6 + heal, max life)` (`UnitSetStat(unit, 6, …)`, ADR-0021),
  else asks `SkillAllyTest` (the boundary); with `sHitPar1 == 0` or no owner, or for a refused ally (after, `[I]`), it
  returns 3 (end, damage) against undead (or demons when `sHitPar2 == 2`, any monster or player when `sHitPar2 == 0`)
  and 4 (keep going) otherwise. **Hit 8 (blaze)** returns 0 (no damage) for its owner in state 13 `blaze`, else 2
  (damage, no end). (§ 6, run:2026-10-20-cat-emu-9c `holy9c`)
- [C] (ADR-0021; up to the first `MissileCreate` or the search, §§ 7–9) **Sub-missiles.** Hit 4 (exploding and
  freezing arrows, royal strike meteor) creates each of `HitSubMissile1..4` that is > 0 (the four words at `+0x24`,
  stride 2) with `{owner, source m, skill, lvl}`; hit 15 (spider goo lay) `HitSubMissile1` at the missile; hit 25
  (pantherpotgreen) 8 directions `(0,2) (2,2) (2,0) (2,−2) (0,−2) (−2,−2) (−2,0) (−2,2)` in steps of `sHitPar1`
  from the unit (or the missile), flags `0x1F`, velocity `Param1 << 7` of the sub-missile's row, loops `lvl − 1`;
  hit 26 (grim ward start) `HitSubMissile1` with flags `0x8001` and range `sHitPar1 > 0 ? : max(calc1, 5)`; hit 29
  (frozen orb) at frames left 0 a ring of 64 directions (radius 30) in steps of `sHitPar1` (stock 4: 16 bolts) whose
  `+0x28/+0x2C` get the direction after the creation (after, `[I]`). Hit 12 (chain lightning) with `MissileData+0x28 > 1`
  searches the nearest unit (`0x0056BD10(owner; x, y, radius, 0x88583, unit guid, 0)`); the next bolt and its count
  `− 1` follow the search (after, `[I]`). (§§ 7–9, run:2026-10-20-cat-emu-9c `create9c`)
- [C] (ADR-0021; up to `STATLIST_Alloc`, `SKILLS_ApplyAuraStats`, the flee call, the unit filter or the party test,
  §§ 10–12) **States and control.** Hit 16 (spider goo, vines) and hit 19 (finger mage spider) put `auratargetstate`
  on the unit for `max(calc4, 5)` (16) or `max(auralencalc, 5)` (19) frames: a new timed list ending at
  `frame + length`, owned by the owner, or the unit's existing list of that state (`ApplyAuraStats` on it). Hit 17
  (howl, tier A) and hit 28 (grim ward scare) make a monster flee: `0x005DDD00(owner or ward; unit, skill, a, b)` with
  `a, b = Param3 + (lvl−1)·Param4, Param5 + (lvl−1)·Param6` (17, when the monster's level is below `owner level +
  Param2 + lvl` and it lacks the state) or `Param5, Param6` (28, when the unit is closer than
  `Param1 + (lvl−1)·Param2` to the ward found by `MissileData+0x28`). Hit 21 (battle cry) tests the unit with
  `SkillUnitFilter(owner, unit; aurafilter ? 0xA783 : 0)` and accepts a state index equal to the States count; hit 18
  (shout, battle orders, battle command) asks `UnitsSameParty(owner, unit)` first. (§§ 10–12, run:2026-10-20-cat-emu-9c
  `state9c`)
- [C] (ADR-0021; up to `ForUnitsInRange`, `BuildDamage`, `CollisionTest` or the re-target, §§ 13–15) **Chains and
  homing.** Hit 20 (lightning fury) calls `SKILLS_ForUnitsInRange(owner; x, y, radius, aurafilter or 0xA783,
  0x005AB2A0, ctx, 1, …)` with `ctx = {owner, m, skill, lvl, sHitPar2 > 0 ? : max(calc1, 1), HitSubMissile1}`;
  hit 22 (fist of the heavens delay) finds the unit `MissileData+0x28/+0x2C` names (none: returns 0) and builds its
  damage. Hit 10 (guided arrow, bone spirit) returns 1 in town, 1 at the end of life when `+0x28` bit 2 or the cell's
  collision bit 2 is set, and with a unit 3 if it is the path's target and 4 (keep going) if not (`+0x28` bit 0), or,
  with bit 1, 3/4 by bit 2 while frames are left and the re-target `0x005AA5B0` at 0. Hit 27 returns 1. (§§ 13–16,
  run:2026-10-20-cat-emu-9c `range9c`)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005A9A70` | `sub_005A9A70_MissHit01AreaEType` | hit 1 | I |
| `0x005A9D80` | `sub_005A9D80_MissHit02Ring` | (P1.3 name) hit 2 | I |
| `0x005A9F90`, `0x005A9E10` | `sub_005A9F90_MissHit03EndArea`, `sub_005A9E10_MissHit44AreaHit` | (P1.3 names) hit 3, hit 44 | I |
| `0x005B07A0` | `sub_005B07A0_MissHit04HitSubs` | hit 4 | I |
| `0x005A9FB0` | `sub_005A9FB0_MissHit07HolyBolt` | hit 7 | I |
| `0x005AA180` | `sub_005AA180_MissHit08Blaze` | hit 8 | I |
| `0x005AA250` | `sub_005AA250_MissHit09Immolation` | hit 9 | I |
| `0x005AA650` | `sub_005AA650_MissHit10Guided` | hit 10 | I |
| `0x005AA730` | `sub_005AA730_MissHit12Chain` | hit 12 | I |
| `0x005AA8B0` | `sub_005AA8B0_MissHit13AreaLen` | hit 13 | I |
| `0x005AABB0` | `sub_005AABB0_MissHit14AreaHitSub` | (P1.3 name) hit 14 | I |
| `0x005AAD40` | `sub_005AAD40_MissHit15SubAt` | hit 15 | I |
| `0x005AAE10`, `0x005AB110` | `sub_005AAE10_MissHit16TargetState`, `sub_005AB110_MissHit19TargetState` | hit 16, hit 19 | I |
| `0x005AAFB0` | `sub_005AAFB0_MissHit17Howl` | (P1.3 name) hit 17 | I |
| `0x005AB0B0` | `sub_005AB0B0_MissHit18PartyState` | hit 18 | I |
| `0x005AB370` | `sub_005AB370_MissHit20UnitsInRange` | hit 20 | I |
| `0x005AB500` | `sub_005AB500_MissHit21BattleCry` | hit 21 | I |
| `0x005ADD20` | `sub_005ADD20_MissHit22Chain` | (P1.3 name) hit 22 | I |
| `0x005A9BF0` | `sub_005A9BF0_MissHit24AreaBuild` | hit 24 | I |
| `0x005AB820`, `0x005AB700` | `sub_005AB820_MissHit25Ring8`, `sub_005AB700_MissSubRing8` | hit 25 and its 8-direction helper | I |
| `0x005AB8D0` | `sub_005AB8D0_MissHit26SubRange` | hit 26 | I |
| `0x005ABA00` | `sub_005ABA00_MissHit27End` | (P1.3 name) hit 27 | I |
| `0x005ABA10` | `sub_005ABA10_MissHit28WardScare` | hit 28 | I |
| `0x005ABB00` | `sub_005ABB00_MissHit29Ring64` | hit 29 | I |
| `0x005542C0` | `sub_005542C0_SkillPetTest` | `(ECX game, EDX owner; unit, skill)`: the unit is the owner's pet and the skill has `TargetPet` (§ 6) | I |
| `0x005A8F20` | `sub_005A8F20_PacketSetLenByEType` | `(ECX game, EDX m; packet, v)`: the length field of the missile's `EType` = v (§ 4) | I |
| `0x005A9530` | `sub_005A9530_MissSubDisc` | hit 9's fire: `HitSubMissile1` on every free, non-town cell of a disc (read only, § 5) | I |
| `0x0056BD10` | `sub_0056BD10_NearestUnitInRange` | `(ECX game, EDX unit; x, y, radius, flags, guid, out)`: `ForUnitsInRange` with flags `| 0xA783` and a nearest-unit callback (read only) | I |
| `0x005AB2A0`, `0x005AB630` | `sub_005AB2A0_FuryChainCb`, `sub_005AB630_FistChainCb` | hit 20's and hit 22's per-unit creation callbacks (read only, §§ 13, 14) | I |
| `0x005AA5B0`, `0x005AA460` | `sub_005AA5B0_GuidedRetarget`, `sub_005AA460_GuidedSetTarget` | hit 10's re-target at frames left 0 (`EAX` m; read only, § 15) | I |
| `0x005D8290` | `sub_005D8290_UnitApplyAuraState` | hit 18's timed `aurastate` on the unit (read only, § 12) | I |
| `0x005DDD00` | `sub_005DDD00_MonFleeFrom` | the flee call of hits 17 and 28 (not read; skills/0003 § 6's name) | I |
| `0x004EFC20`, `0x004E6C70`, `0x004F4110` | `sub_004EFC20_SkillGetParam2`, `sub_004E6C70_SkillGetParam5`, `sub_004F4110_SkillGetParam6` | `(ECX skill)` → Skills `+0x14C` / `+0x158` / `+0x15C`, 0 when invalid | I |
| `0x004CC7C0`, `0x004EFCB0` | `sub_004CC7C0_SkillParam3ByLevel`, `sub_004EFCB0_SkillParam5ByLevel` | `(ECX skill, EDX lvl)` → `Param3 + (lvl−1)·Param4` / `Param5 + (lvl−1)·Param6`, 0 when invalid or lvl ≤ 0 | I |
| `0x006492A0` | `sub_006492A0_DistSq` | `(x1, y1, x2, y2)` → `(y2−y1)² + (x2−x1)²`, 32-bit, `ret 0x10` | I |
| `0x00639E30`, `0x006260B0` | `sub_00639E30_UnitSetStateBit`, `sub_006260B0_StatListSetEnd` | the state bit on the unit; list `+0x18` = end frame (`+0x10` bit 1 when > 0) | I |

## Walkthrough

### 1. The table slots and the shared shape

- [I] `g_MissileSrvHitFuncs[1..29]` are as the Functions table (`static.txt` lists entries 0–30: 5 `0x005ABC40`, 6
  `0x005AA1C0`, 11 `0x005B0870`, 23 `0x005ACFC0` are filled but named by no row; 30 is null). Each function reads its
  record as `DataTables+0xB64 + 0x1A4 · Unit+0x04` after `0 ≤ class < DataTables+0xB6C`, and its Skills row as
  `DataTables+0xB98 + 0x23C · skill` after `0 ≤ skill < DataTables+0xBA0`, where it needs one; the missile's position
  is `PathGetX/Y` of its path (0 without one; the static `+0x0C/+0x10` words for unit types 2, 4, 5, which a missile
  never is). The result word goes back to `MISSILE_HitUnit` (skills/0002 § 5), which replaces its own with it.
  (`static.txt`, 0x005A9A70–0x005A9AB8, fn:MISSILE_HitUnit@0x005ADF10)

### 2. Emulation: the 9c families

The method is 9b's (skills/0005 § 2), with the call site of every observed boundary asserted and a site control, two
or more negative controls per family on different claims, and two additions the `lane/p46m2` review asked for: **the
untouched-seed comparison** (every case writes the missile's, the owner's and the target's seeds and dumps all three;
the model gives all three at every boundary and every return, so a step on a seed the model leaves alone fails), and,
for a boundary argument that points into the caller's frame (a packet, a context block), **the bytes it points to**.
The boundaries added for 9c: `0x0056BAD0` AreaHitAt, `0x00554D20` SkillAllyTest, `0x0056BD10` the nearest-unit
search, `0x006251F0` STATLIST_Alloc, `0x005C6CC0` SKILLS_ApplyAuraStats, `0x005DDD00` the flee call, `0x0056B3E0`
SkillUnitFilter, `0x00554DE0` UnitsSameParty, `0x0056B7E0` SKILLS_ForUnitsInRange, `0x005AA5B0` hit 10's re-target,
`0x0064D9B0` the cell collision test; 9b's stay declared. Emulated, not observed: `UnitGetOwner`, `GameFindUnit`,
`SKILLS_EvalCalc` on constant programs, `MISSDATA_*`, `sub_005A8C70_MissileRollEType`, `sub_005A8910_MissileElemRoll`,
`STATS_GetUnitStat`, `UnitGetMaxHp`, `MONSTATS_IsUndead/IsDemon`, `UNIT_HasState`, `UNIT_FindStatListByState`,
`sub_005542C0_SkillPetTest` with `MonsterOwnerRef`, `UNIT_GetTargetUnit` (9a's target link), `PathCellCollision`,
`RoomIsTown`, the Skills parameter getters and `DistSq`.

- [C] Five families, **8 400 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 3 941 matched boundary cases (27
  function, boundary and return-address triples, each a `site` line) (`check.txt` `733ad44a…`; run:2026-10-20-cat-emu-9c):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `area9c` | hit 1, 3 (→ 44), 9, 13, 14, 24 | 1 800 | hit 1 radius from `aurarangecalc` (40); `ResultFlags` dropped (405); hit 44 radius only when > 0 (30); hit 9's stat 134 first (144); hit 13's length dropped (55); draws on the owner's seed (155) | AreaHitAt @0x005A9BE1, @0x005AA44D, @0x005AAA7C; BuildDamage @0x005A9D36, @0x005A9F4C, @0x005AACB7; UnitSetStat @0x005AA2FA; returns 0 and 1 |
  | `holy9c` | hit 7, 8 | 1 500 | heal cap dropped (46); undead mask `0x08` only (8); no fallback roll (13); hit 8 always 2 (112); draws on the owner's seed (39) | AllyTest @0x005AA053; UnitSetStat @0x005AA0EC (heal); returns 0, 1, 2, 3, 4 |
  | `create9c` | hit 4, 12, 15, 25, 26, 29 | 1 800 | hit 4 `≥ 0` for `> 0` (80); hit 12 count `> 0` for `> 1` (54); hit 25 velocity not shifted (146); hit 29 `left > 0` for `!= 0` (4) | MissileCreate @0x005B0838, @0x005AADF5, @0x005AB7FD (in `0x005AB700`), @0x005AB9ED, @0x005ABBED; NearestUnit @0x005AA819; returns 1, 2, 3 |
  | `state9c` | hit 16, 17, 18, 19, 21, 28 | 1 800 | hit 21 state `<` count (18); hit 28 `≤` for `<` (21); hit 17 without `lvl` (16); hit 16/19 calcs swapped (98) | StatListAlloc @0x005AAEF9, @0x005AB1F6; ApplyAuraStats @0x005AAF58, @0x005AB24E; Flee @0x005AB09B, @0x005ABAF0; UnitFilter @0x005AB599; SameParty @0x005AB0E0; returns 0, 1 |
  | `range9c` | hit 10, 20, 22, 27 | 1 500 | hit 10's 3/4 swapped (84); re-target at `left < 0` (16); hit 20 count from `calc4` (42); hit 22 no unit → 1 (40) | ForUnitsInRange @0x005AB4D6; BuildDamage @0x005ADE82; CollisionTest @0x00648ED9 (in `PathCellCollision`); GuidedRetarget @0x005AA6ED; returns 1, 3, 4 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt` `1644c5cb…`, 26 of 26 pins): 9b's (`g_UnitHashOffsets`,
  the `CALC_Eval` jump table, the skills calc function count, `g_BitMask32`, `0x005A8C70`'s `EType` jump table), 9a's
  town tables (`0x006426C0/0x006426C8`, hit 10), and new: `0x005A8F20`'s `EType` jump table (`0x005A8F84`, 9 entries,
  `.text`), `g_BitMask32` up to index 31 (state bits, `TargetPet`), hit 25's offsets (`0x006E25F8/0x006E2618`, 8 each,
  `.rdata`) and hit 29's (`0x006E2638/0x006E2738`, 64 each, `.rdata`; the same radius-30 circle values as 9a's
  `0x006E2A78/0x006E2B78`). Stat lists, ItemStatCost, MonStats, Skills (`+0x07`, `+0x50`, `+0x82`, `+0x148..+0x15C`,
  the calc offsets), the state chains and the hash buckets are scratch records written one field per field read.
- [I] **Not reached** (from the reading): everything after each boundary (listed per function below); hit 2 (tier A,
  not emulated); unit types 2, 4, 5 as the missile itself (a missile is type 3); `MonsterOwnerRef` on a monster without
  MonsterData or with a null `+0x28` reference (a read of address `0x28`, a fault; ADR-0015 (5)); hit 22 with a type
  above 5 (`GameFindUnit` faults); hit 25 from a type 2/4/5 unit without a path (the static path is read unchecked). (run:2026-10-20-cat-emu-9c,
  fn:sub_005AB700_MissSubRing8@0x005AB700)
- [I] ADR-0015 (3): the `[C]` claims, those marked ADR-0021 included, cover the code as a map. What the offsets mean
  keeps its own tag (Missiles and Skills columns `[C]` by layout; `MissileData` words `[I]`, skills/0002 § 1; packet
  fields `[I]`, combat/0001); nothing here says when the game runs these functions or on which seed state.
  (run:2026-10-20-cat-emu-9c)

### 3. Hit 1 and hit 24: an area hit at the missile

```c
// fn:sub_005A9A70_MissHit01AreaEType@0x005A9A70 (hit 24 0x005A9BF0 differs in one line), trimmed
if (!rec || !(owner = UnitGetOwner(game, m))) return 1;
r = rec->sHitPar1;
if (r <= 0) { if (!skillrec) return 1; r = max(SKILLS_EvalCalc(owner, skill->calc1, skill, lvl), 1); }
x = PathGetX(m->path); y = PathGetY(m->path);             // 0 without a path
memset(&pkt, 0, 0x70);
MissileRollEType(game, m, unit, &pkt);                     // hit 24: MISSILE_BuildDamage(game, owner, m, unit, &pkt)
pkt.flags |= rec->HitFlags; pkt.result |= rec->ResultFlags; // +0x00 u32, +0x04 u16
AreaHitAt(game, owner, x, y, r, &pkt, 0);
return 1;
```

- [C] (ADR-0021; ends at `AreaHitAt` @0x005A9BE1) **Hit 1** as above: the packet `AreaHitAt` receives is compared
  whole (0x70 bytes): the `EType` roll of 9b's model (skills/0005 § 13) on the hit unit (0 at the end of life), then
  the two OR's; the roll's draws are the only step of any seed. Without a record or an owner it returns 1, and with
  `sHitPar1 ≤ 0` and no Skills row too. After, `[I]`: the return value 1 (end, no damage from `MISSILE_HitUnit`: the
  area hit is the damage). (run:2026-10-20-cat-emu-9c `area9c`, 0x005A9A70–0x005A9BEC,
  fn:sub_005A9A70_MissHit01AreaEType@0x005A9A70, fn:sub_0056BAD0_AreaHitAt@0x0056BAD0)
- [C] (ADR-0021; ends at `MISSILE_BuildDamage` @0x005A9D36) **Hit 24**: the same tests, then
  `MISSILE_BuildDamage(ECX game, EDX owner; m, unit, packet)` on the zeroed packet, with the radius in EBX at the call
  (compared). No seed is stepped before it. After, `[I]`: the OR's, `AreaHitAt` with that radius, return 1.
  (run:2026-10-20-cat-emu-9c `area9c`, 0x005A9BF0–0x005A9D6E, fn:sub_005A9BF0_MissHit24AreaBuild@0x005A9BF0)
- [I] Stock: hit 1 on 62 fireball (`sHitPar1` 4), 129 vampirefireball (3), 283 desertfireball (2), 404 impfireball
  (5), 416 catapult cold ball (0: `calc1` of its creator), 441 sucfireball (3), 656 explodingarrowexp2 (5), 657
  freezingarrowexp3 (5, `EType` 12); `HitFlags` 2 and `ResultFlags` 5 on most. Hit 24 on 238 pantherpotorange (0,
  `ResultFlags` 5). (`rows.txt`, tbl:Missiles.txt:sHitPar1, tbl:Missiles.txt:HitFlags, tbl:Missiles.txt:ResultFlags)

### 4. Hit 13, hit 3 → 44, hit 14

- [C] (ADR-0021; ends at `AreaHitAt` @0x005AAA7C) **Hit 13** (`0x005AA8B0`): with a record and a Skills row (else 1;
  no owner test): radius `sHitPar1 > 0 ? : max(aurarangecalc, 1)`, length `sHitPar2 > 0 ? sHitPar2 : auralencalc`
  (no floor), the `EType` roll, then when the length is above 0 `0x005A8F20(packet, length)`: by the missile's `EType`
  (Missiles `+0xE4`), 4 cold → `+0x30`, 5 poison → `+0x2C`, 9 → `+0x44`, 11 → `+0x18`, 12 freeze → `+0x34` (the field
  is replaced, not added; other types nothing); then the OR's and `AreaHitAt(owner; x, y, radius, packet, 0)`. After,
  `[I]`: returns 1 when `AreaHitAt` returns non-zero, else 3. (run:2026-10-20-cat-emu-9c `area9c`,
  0x005AA8B0–0x005AAA8C, fn:sub_005AA8B0_MissHit13AreaLen@0x005AA8B0, fn:sub_005A8F20_PacketSetLenByEType@0x005A8F20)
- [C] **Hit 3** (`0x005A9F90`) returns 0 (no end, no damage) for any unit, without a record test; with unit 0 it calls
  hit 44 with unit 0 (a `call`, not a tail jump). [C] (ADR-0021; ends at `MISSILE_BuildDamage` @0x005A9F4C) **Hit 44**
  (`0x005A9E10`): with a record (else 1); **no owner test** (the owner may be 0); radius `sHitPar1` when it is
  **non-zero** (`jne`: a negative value is taken as it is), else, with a Skills row (else 1), `max(aurarangecalc, 1)`
  (EDI at the call, compared); then `BuildDamage(owner; m, 0, packet)`. After, `[I]`: the OR's, `AreaHitAt`, return 1
  when it returns non-zero, else 3. (run:2026-10-20-cat-emu-9c `area9c`, 0x005A9E10–0x005A9FA7,
  fn:sub_005A9F90_MissHit03EndArea@0x005A9F90, fn:sub_005A9E10_MissHit44AreaHit@0x005A9E10)
- [C] (ADR-0021; ends at `MISSILE_BuildDamage` @0x005AACB7) **Hit 14** (tier A, `0x005AABB0`): a Skills row and **an
  owner** are required (else 1); radius `sHitPar1 > 0 ? : max(aurarangecalc, 1)` (ESI at the call, compared); then
  `BuildDamage(owner; m, unit, packet)`. After, `[I]` (0x005AACB7–0x005AAD3B): the OR's; `AreaHitAt`; result 1 when
  it returns non-zero, else 3; then, when `HitSubMissile1 ≥ 0`, `sub_005AAA90_MissSubRing18(EAX m; game,
  HitSubMissile1, Param3 + (lvl−1)·Param4, max(sHitPar2, 1))`, whose third argument, when above 0, gives each fire
  flags `0x8001` and range `+0x4C` = that value (0x005AAB2E–0x005AAB47). (fn:sub_005AABB0_MissHit14AreaHitSub@0x005AABB0,
  fn:sub_005AAA90_MissSubRing18@0x005AAA90, fn:sub_004CC7C0_SkillParam3ByLevel@0x004CC7C0)
- [I] Stock: hit 13 on 96 glacialspike and 271 monglacialspike (`EType` 12, the freeze length from `auralencalc`),
  336 hellmeteordown (`sHitPar1` 5, `sHitPar2` 1); hit 3 on 44–46 the fire potions (`sHitPar1` 2, 3, 6) and 386 bomb
  on ground (0: `aurarangecalc` of Fire Trauma, its `Skill`); hit 14 on 101 meteorcenter, 133 vampiremeteorcenter
  (`sHitPar2` 1: all 18 fires), 422 catapult meteor ball, 563 royalstrikemeteor. (`rows.txt`, tbl:Missiles.txt:sHitPar2)

### 5. Hit 9: immolation arrow

- [C] (ADR-0021; ends at `UnitSetStat` @0x005AA2FA or `AreaHitAt` @0x005AA44D) With a record and a Skills row (else
  1; no owner test): when `HitSubMissile1 ≥ 0`, `UnitSetStat(m, 56, 0, 0)` (the boundary); when it is negative, the
  radius `sHitPar2 > 0 ? : max(calc2, 1)`, the `EType` roll, the OR's and `AreaHitAt(owner; x, y, radius, packet, 0)`.
  After the first boundary, `[I]` (0x005AA2FA–0x005AA458): `UnitSetStat(m, 134, 0, 0)`; the disc radius `sHitPar1 > 0
  ? : max(calc1, 1)`; `fire = MISS_EvalCalc(m, owner, SHitCalc1, class, lvl)`; `sub_005A9530_MissSubDisc(game, m;
  radius, HitSubMissile1, fire)`; then the area hit as on the negative path; returns 3. (run:2026-10-20-cat-emu-9c
  `area9c`, fn:sub_005AA250_MissHit09Immolation@0x005AA250)
- [I] `sub_005A9530_MissSubDisc`: with the missile in a room, one `MissileCreate` (flags 1, `| 0x8000` and the value
  at `+0x4C` when `fire > 0`, a negative `fire` taken as 0) of `HitSubMissile1` per cell `(x + dx, y + dy)` with
  `dx² + dy² ≤ radius²` that passes a `COLL_LineTest` (mask 4) and lies in a room that is not a town. Stock 85
  immolationarrow → 230 immolationfire, `SHitCalc1` `100`. ItemStatCost 56 is `coldlength` and 134 `item_freeze`
  (`itemstatcost.txt` rows): the arrow clears the cold and freeze stats it carries before its fire.
  (0x005A9530–0x005A96F0, `rows.txt`)

### 6. Hit 7 (holy bolt) and hit 8 (blaze)

```c
// fn:sub_005A9FB0_MissHit07HolyBolt@0x005A9FB0, trimmed
if (!rec || !unit) return 1;
owner = UnitGetOwner(game, m);
if (rec->sHitPar1 && owner && (SkillPetTest(game, owner, unit, skill) || SkillAllyTest(game, owner, unit, skill))) {
    if (!(s = SKILLS_GetRecord(skill))) return 1;
    lo = EvalCalc(owner, s->calc1, skill, lvl) << 8;  hi = EvalCalc(owner, s->calc2, skill, lvl) << 8;
    h = RNG_RangeB(&m->seed, hi - lo) + lo;                     // draw 1 (none when hi - lo <= 0)
    if (h <= 0) h = MissileElemRoll(m, 22, 21, -1);             // draw 2 when both stats >= 1
    v = STATS_GetUnitStat(unit, 6, 0) + h;  if (v >= UnitGetMaxHp(unit)) v = UnitGetMaxHp(unit);
    UnitSetStat(unit, 6, v, 0);
    if (rec->ProgOverlay > 0) UnitSetOverlayStat(unit, rec->ProgOverlay, 0);
    return 1;
}
switch (unit->type) {
case 0: return rec->sHitPar2 == 0 ? 3 : 4;
case 1: if (rec->sHitPar2 == 0) return 3;
        return (rec->sHitPar2 == 2 ? MONSTATS_IsDemon(unit) : MONSTATS_IsUndead(unit)) ? 3 : 4;
default: return 4;
}
```

- [C] As above on the cases that return (no unit; no record; `sHitPar1 == 0`; no owner; every unit type, `sHitPar2`
  0, 1, 2 and others, undead (MonStats `+0x0D & 0x18`) and demon (`& 0x20`)); the heal up to `UnitSetStat` @0x005AA0EC
  (ADR-0021: the value, both draws on the missile's seed and only there, the cap at `UnitGetMaxHp`, all compared);
  the ally branch up to `SkillAllyTest` @0x005AA053 (ADR-0021). `SkillPetTest` (`0x005542C0`, emulated): owner and
  unit present, the owner a player or the unit a monster, Skills `+0x07` bit 1 (`TargetPet`), and
  `MonsterOwnerRef(unit)` giving owner type 0 and the owner's guid. The arithmetic is 32-bit: `(calc << 8)` by `shl`,
  the range `hi − lo` wraps. After, `[I]`: what `SkillAllyTest` returns (the party test of skills/0001 § 4, `TargetAlly`
  bit 2) and the code after it, which on a refusal falls to the switch; the overlay and the return 1 after the heal.
  (run:2026-10-20-cat-emu-9c `holy9c`, 0x005A9FB0–0x005AA172, fn:sub_005542C0_SkillPetTest@0x005542C0,
  fn:sub_00554D20_SkillAllyTest@0x00554D20)
- [I] So a holy bolt heals the owner's pets (and party allies, by the reading of `SkillAllyTest`) for `calc1..calc2`
  in 8.8 fixed point (stock Holy Bolt, `ProgOverlay` 26 healing) and ends there without damage (return 1); it damages
  undead and ends (3, stock `sHitPar2` 1) and passes through everything else (4, keep).
  (fn:sub_005A9FB0_MissHit07HolyBolt@0x005A9FB0, tbl:Missiles.txt:ProgOverlay)
  Stock 55 holybolt and 234 fistoftheheavensbolt (`sHitPar1` 1, `sHitPar2` 1). (`rows.txt`)
- [C] **Hit 8** (`0x005AA180`): returns 0 when the unit is the missile's owner and the owner is in state 13 (`blaze`;
  `UNIT_HasState`, owner type 0 or 1 here), else 2 (damage, no end); no record test. (run:2026-10-20-cat-emu-9c
  `holy9c`, 0x005AA180–0x005AA1B1, fn:sub_005AA180_MissHit08Blaze@0x005AA180, tbl:States.txt:state)
- [I] Stock 67 blaze (Skills 46 Blaze): the sorceress's own trail does not burn her while Blaze is on. (`rows.txt`,
  fn:sub_005AA180_MissHit08Blaze@0x005AA180)

### 7. Hit 4, 15, 26: sub-missiles on the hit

- [C] (ADR-0021; ends at the first `MissileCreate` @0x005B0838) **Hit 4** (`0x005B07A0`): with a record (else 1; no
  owner or skill test), for each of the four words at `+0x24, +0x26, +0x28, +0x2A` (`HitSubMissile1..4`) that is > 0
  (s16; 0 and −1 skipped), a block `{owner, source m, cls, skill, lvl}` (flags 0) to `MissileCreate`; when no word is
  > 0 it returns 3. The four slots are read at stride 2 (the cases reach the first creation at slot 1, 2, 3 and 4).
  After, `[I]`: per created missile, when `sHitPar1 > 0`, `MISSILE_HitUnit(game, new; unit, 1)` (it hits the same unit
  at once); then the next slot; return 3. (run:2026-10-20-cat-emu-9c `create9c`, 0x005B07A0–0x005B0865,
  fn:sub_005B07A0_MissHit04HitSubs@0x005B07A0, tbl:Missiles.txt:HitSubMissile1)
- [C] (ADR-0021; ends at `MissileCreate` @0x005AADF5) **Hit 15** (`0x005AAD40`): `HitSubMissile1 ≥ 0` and an owner
  (else 1): `{flags 1, owner, x, y, cls HitSubMissile1, skill, lvl}`. After, `[I]`: returns 0.
  (fn:sub_005AAD40_MissHit15SubAt@0x005AAD40)
- [C] (ADR-0021; ends at `MissileCreate` @0x005AB9ED) **Hit 26** (`0x005AB8D0`): `HitSubMissile1 ≥ 0`, an owner, a
  Skills row (else 1): `{flags 0x8001, owner, cls, x, y, skill, lvl, range +0x4C = sHitPar1 > 0 ? : max(calc1, 5)}`.
  After, `[I]`: returns 1. (fn:sub_005AB8D0_MissHit26SubRange@0x005AB8D0)
- [I] Stock: hit 4 on 41 explodingarrow → 656 (hit 1), 87 freezingarrow → 657 (hit 1), 564 royalstrikemeteorcenter →
  563 royalstrikemeteor (`sHitPar1` 1: the meteor hits the unit at once, hit 14); hit 15 on 143 spidergoolay → 146
  spidergoo (hit 16); hit 26 on 249/252/255 grimward*start → 250/253/256 (hit 27, do 14). (`rows.txt`,
  tbl:Missiles.txt:HitSubMissile1)

### 8. Hit 25 and hit 29: rings

- [C] (ADR-0021; ends at the first `MissileCreate` @0x005AB7FD inside `sub_005AB700_MissSubRing8`) **Hit 25**
  (`0x005AB820`): `HitSubMissile1 ≥ 0` and an owner (else 1); the source is the unit, or the missile at the end of
  life; `sub_005AB700_MissSubRing8(ECX game, EDX owner; src, HitSubMissile1, skill, lvl, max(sHitPar1, 1))`, which
  returns 0 without a record for the sub-missile (hit 25 returns 3 either way) and else fills `{flags 0x1F, owner,
  source src, cls, x, y = src's position, tx, ty = the first offset, +0x28 = Param1 << 7 of the sub-missile's row,
  skill, lvl, loops +0x34 = lvl − 1}`. The 8 offsets (`static.txt`; data:g_HitRing8X@0x006E2618, data:g_HitRing8Y@0x006E25F8): `(0,2) (2,2) (2,0) (2,−2) (0,−2) (−2,−2)
  (−2,0) (−2,2)`. After, `[I]`: one creation per `step`-th offset (`i += 4·step` bytes while `< 0x20`), return 1 from
  the helper, 3 from hit 25. (run:2026-10-20-cat-emu-9c `create9c`, 0x005AB700–0x005AB80F,
  fn:sub_005AB820_MissHit25Ring8@0x005AB820, fn:sub_005AB700_MissSubRing8@0x005AB700)
- [C] (ADR-0021; ends at the first `MissileCreate` @0x005ABBED) **Hit 29** (`0x005ABB00`): `HitSubMissile1 ≥ 0`
  (else 1); **frames left `!= 0` returns 2** (damage, no end: the orb flies on) before the owner test; an owner (else 1); the
  block `{flags 2, owner, source m, cls, skill, lvl, tx, ty = (30, 0)}` (the 64-entry circle at `0x006E2738/0x006E2638`, data:g_HitRing64X@0x006E2738, data:g_HitRing64Y@0x006E2638).
  After, `[I]`: per created bolt `+0x28 = tx`, `+0x2C = ty` (the direction do 15's bolts read, skills/0004 § 7),
  the next of every `max(sHitPar1, 1)`-th direction; return 3. (fn:sub_005ABB00_MissHit29Ring64@0x005ABB00)
- [I] Stock: hit 25 on 239 pantherpotgreen → 222 rancidgascloud (`sHitPar1` 1: 8 clouds); hit 29 on 260 frozenorb →
  262 frozenorbnova (`sHitPar1` 4: 16 bolts), so the burst comes only from a call with frames left 0, the end-of-life
  call (`AlwaysExplode` 1). (`rows.txt`, tbl:Missiles.txt:AlwaysExplode)

### 9. Hit 12: chain lightning

- [C] (ADR-0021; ends at `sub_0056BD10_NearestUnitInRange` @0x005AA819) With a record (else 1), an owner, a unit and
  `MissileData+0x28 > 1` (signed; else 3): radius `sHitPar1 > 0 ? : max(aurarangecalc, 1)` (no Skills row: 3), then
  `0x0056BD10(ECX game, EDX owner; x, y, radius, 0x88583, unit guid (+0x0C), 0)`. After, `[I]` (0x005AA819–0x005AA8A0):
  when it finds a unit other than the hit one, `{flags 0x21, owner, target +0x0C = found, cls = this missile's class,
  start = the missile, +0x1C/+0x20 = the found unit's position, skill, lvl}` to `MissileCreate` and the new bolt's
  `+0x28 = count − 1`; return 3. (run:2026-10-20-cat-emu-9c `create9c`, 0x005AA730–0x005AA81D,
  fn:sub_005AA730_MissHit12Chain@0x005AA730, fn:sub_0056BD10_NearestUnitInRange@0x0056BD10)
- [I] `0x0056BD10` is `SKILLS_ForUnitsInRange(x, y, radius, flags | 0xA783, 0x0056BCD0, ctx, 0, …)` with the guid to
  skip in its context and the first or nearest unit as its result (the callback not read). Stock 93 chainlightning,
  267 chainlightning2 (`sHitPar1` 10), 232 lightningstrike; the count `+0x28` is set at the cast (skills/0003, not here).

### 10. Hit 16 and hit 19: a timed state on the unit

- [C] (ADR-0021; ends at `STATLIST_Alloc` @0x005AAEF9 / @0x005AB1F6 or `SKILLS_ApplyAuraStats` @0x005AAF58 /
  @0x005AB24E) A Skills row and an owner (else 1); a unit (hit 16: else 0; hit 19: else 1); `auratargetstate`
  (Skills `+0x82`, s16) in `[0, States count)` (else 1); length `max(calc4, 5)` (16) or `max(auralencalc, 5)` (19);
  `UNIT_FindStatListByState(unit, state)` (emulated: the unit's list `+0x10` bit 31, then the `+0x3C` and `+0x40`
  chains by `+0x14`, next `+0x2C`; state 0 is never found). Not found: `STATLIST_Alloc(game+0x1C, 2, frame + length,
  owner type, owner guid)`. Found: `SKILLS_ApplyAuraStats(ECX unit, EDX list; skillrec, skill, lvl)`. After, `[I]`
  (0x005AAEF9–0x005AAF9D, 0x005AB1F6–0x005AB292): a new list gets the state, `STATE_DefaultRemoveCB`, links to the
  unit, `STATE_Set(unit, state, 1)`; then `ApplyAuraStats` with EDX = the **search's** result (0 for a new list: EAX
  is reloaded from `[ebp−0xC]`, 0x005AAF42, 0x005AB239), the state bit, `0x006260B0` on that same value (a no-op on 0,
  so a new list keeps the end frame `STATLIST_Alloc` got; an existing one is refreshed to `frame + length`) and
  `UnitQueueEvent(game, unit; 12, frame + length)`; hit 16 returns 0, hit 19 returns 3.
  (run:2026-10-20-cat-emu-9c `state9c`, fn:sub_005AAE10_MissHit16TargetState@0x005AAE10,
  fn:sub_005AB110_MissHit19TargetState@0x005AB110, fn:UNIT_FindStatListByState@0x006256B0)
- [I] Stock: hit 16 on 146 spidergoo, 472 vines trail, 473 vines wither (no `Skill` column: the skill is the one the
  missile carries); hit 19 on 177 fingermagespider (`ProgOverlay` 126). (`rows.txt`, tbl:Skills.txt:auratargetstate)

### 11. Hit 17 (howl) and hit 28 (grim ward scare): flee

- [C] (ADR-0021; ends at `0x005DDD00` @0x005AB09B) **Hit 17** (tier A): a Skills row and an owner (else 1); a monster
  unit (else 0); `auratargetstate` in range (else 1); not in that state (`UNIT_HasState`, else 0); when
  `Param2 + (owner level + lvl) > unit level` (stat 12, signed 32-bit): `0x005DDD00(ECX game, EDX owner; unit, skill,
  Param3 + (lvl−1)·Param4, Param5 + (lvl−1)·Param6)` (both 0 when lvl ≤ 0); else 0. After, `[I]`: returns 0.
  (run:2026-10-20-cat-emu-9c `state9c`, 0x005AAFB0–0x005AB0A3, fn:sub_005AAFB0_MissHit17Howl@0x005AAFB0)
- [C] (ADR-0021; ends at `0x005DDD00` @0x005ABAF0) **Hit 28** (`0x005ABA10`): a Skills row, an owner, a monster unit
  (else 1); the ward `GameFindUnit(game, 3, MissileData+0x28)` (else 1); `r = Param1 + (lvl−1)·Param2`; when
  `(uy − wy)² + (ux − wx)² < r·r` (32-bit, signed): `0x005DDD00(ECX game, EDX ward; unit, skill, Param5, Param6)`;
  else 1. After, `[I]`: returns 1. (fn:sub_005ABA10_MissHit28WardScare@0x005ABA10, fn:sub_006492A0_DistSq@0x006492A0)
- [I] So howl's two numbers are level-scaled (Param3/4 and Param5/6) and the ward's are the flat Param5/Param6; what
  `0x005DDD00` does with them (a flee length and distance) is the monster AI's (not read). Stock 148 howl, 259
  grimwardscare. (`rows.txt`)

### 12. Hit 21 (battle cry) and hit 18 (shouts)

- [C] (ADR-0021; ends at `SkillUnitFilter` @0x005AB599) **Hit 21** (`0x005AB500`): an owner and a unit, a Skills row,
  `auratargetstate` with `0 ≤ state ≤ States count` (`jg`: the count itself passes), else 1; then
  `SkillUnitFilter(ECX owner, EDX unit; aurafilter != 0 ? 0xA783 : 0)` (the column's value is not passed, only
  whether it is set). After, `[I]` (0x005AB599–0x005AB610): on a pass, a 0x24 block `{owner, unit, skill, lvl, length
  = auralencalc (no floor), …, state}` to `STATE_ApplyTimed`, then `ApplyAuraStats` on its list; returns 0. With
  filter 0 `SkillUnitFilter` refuses every unit type (its switch tests a bit of the filter per type), so a battle cry
  row without `aurafilter` applies nothing. (run:2026-10-20-cat-emu-9c `state9c`,
  fn:sub_005AB500_MissHit21BattleCry@0x005AB500, fn:sub_0056B3E0_SkillUnitFilter@0x0056B3E0)
- [C] (ADR-0021; ends at `UnitsSameParty` @0x005AB0E0) **Hit 18** (`0x005AB0B0`): an owner (else 1), a unit (else 0),
  then `UnitsSameParty(ECX game, EDX owner; unit)`. After, `[I]`: on the same party,
  `sub_005D8290_UnitApplyAuraState(ECX game, EDX unit; owner, skill, lvl)`: with `aurastate` (Skills `+0x80`) in range,
  the length `auralencalc + frame`, a new timed list (owner type 6, guid −1 when there is no owner) or the existing one,
  the state bit, the end frame, event 12, `ApplyAuraStats` and `0x0056DE40`; returns 0. Stock 149 shout, 236
  battlecommand, 237 battleorders; 219 battlecry (hit 21). (fn:sub_005AB0B0_MissHit18PartyState@0x005AB0B0,
  fn:sub_005D8290_UnitApplyAuraState@0x005D8290)

### 13. Hit 20: lightning fury

- [C] (ADR-0021; ends at `SKILLS_ForUnitsInRange` @0x005AB4D6) With a record, `HitSubMissile1 ≥ 0`, a Skills row and
  an owner (else 1): `SKILLS_ForUnitsInRange(ECX game, EDX owner; x, y, sHitPar1 > 0 ? : max(aurarangecalc, 1),
  aurafilter or 0xA783 when 0, 0x005AB2A0, &ctx, 1, ".\MISSILES\MissMode.cpp", 0xEC3)` with
  `ctx = {owner, m, skill, lvl, sHitPar2 > 0 ? : max(calc1, 1), HitSubMissile1}` (compared by content). After, `[I]`:
  returns 3; the callback `0x005AB2A0`, while the iterator's count `+0x08` is below `ctx+0x10`, creates
  `{flags 0x20, owner, source m, cls, target = the unit's position, skill, lvl}` and returns 1.
  (run:2026-10-20-cat-emu-9c `range9c`, 0x005AB370–0x005AB4EE, fn:sub_005AB370_MissHit20UnitsInRange@0x005AB370,
  fn:sub_005AB2A0_FuryChainCb@0x005AB2A0)
- [I] Stock 206 lightningfury → 231 furylightning: one bolt per unit in range up to `calc1` units. (`rows.txt`,
  fn:sub_005AB2A0_FuryChainCb@0x005AB2A0)

### 14. Hit 22: fist of the heavens delay

- [C] (ADR-0021; ends at `MISSILE_BuildDamage` @0x005ADE82) With a record, `HitSubMissile1 ≥ 0`, an owner and a
  Skills row (else 1): the unit `GameFindUnit(game, MissileData+0x28 type, +0x2C guid)`; none: **returns 0**; else
  `BuildDamage(ECX game, EDX owner; m, that unit, packet)` (the packet is not cleared first, unlike hits 1–24's).
  After, `[I]` (0x005ADE82–0x005ADEFD): `MissileApplyAndAc`, then `ForUnitsInRange(x, y, sHitPar1 > 0 ? :
  max(aurarangecalc, 1), aurafilter or 0xA683, 0x005AB630, ctx, 0, …, 0xF65)` with `ctx` as hit 20's but the count
  `sHitPar2 > 0 ? : max(calc4, 1)`; its callback creates a bolt per unit while the count is not reached; returns 1. (run:2026-10-20-cat-emu-9c `range9c`, fn:sub_005ADD20_MissHit22Chain@0x005ADD20,
  fn:sub_005AB630_FistChainCb@0x005AB630)
- [I] So the delay hits the unit the cast stored (not the unit the missile touches) and then sends `calc4` holy bolts;
  skills/0003 § 6's correction row stands, refined. Stock 233 fistoftheheavensdelay → 234. (`rows.txt`,
  fn:sub_005AB630_FistChainCb@0x005AB630)

### 15. Hit 10: guided arrow and bone spirit

- [C] As follows on the returning cases, and (ADR-0021) up to `CollisionTest` @0x00648ED9 or `0x005AA5B0` @0x005AA6ED:
  in a town room (`RoomIsTown`) 1; `s = MissileData+0x28`; at the end of life (unit 0) with `s & 4`, 1; the cell's
  collision word (`PathCellCollision`: path `+0x54`, or `0x0064D9B0(room, x, y, +0x44, 0x7FFF)` when path `+0x7C`
  is 0, the boundary); at the end of life with that word's bit 2, 1; then with `s & 1`: unit 0 → 3, the path's target
  unit (`UNIT_GetTargetUnit`) → 3, another unit → 4 (keep going); with `s & 2`: frames left ≤ 0 →
  `0x005AA5B0(EAX m; game)`, else `s & 4 ? 3 : 4`; otherwise 3. After, `[I]`: the re-target's result non-zero (refused)
  gives 1, 0 (a new target set) gives 4.
  (run:2026-10-20-cat-emu-9c `range9c`, 0x005AA650–0x005AA720, fn:sub_005AA650_MissHit10Guided@0x005AA650)
- [I] `0x005AA5B0` (EAX m): without a record, with `s & 4` or without an owner it returns 1; else the nearest unit
  within `Param2` (Missiles `+0x3C`) by `0x0056BD10(…, 3, −1, 0)`, then `sub_005AA460_GuidedSetTarget` (ESI m), and
  returns 0: range and frames left `Range + (lvl−1)·LevRange`,
  and either the unit as the path's target (`+0x28 = 5`) or the point `+0x2C` packs (low word x, high y, as offsets;
  `+0x28 = 6`), then `PathPlan` when the distance is below 25. So an arrow that has spent its frames picks a new target
  once. Stock 86 guidedarrow, 193 bonespirit, 329 monbonespirit (`Param1` 5). (0x005AA460–0x005AA5A6, 0x005AA5B0–0x005AA640)

### 16. Hit 27 and the tier-A hit 2

- [C] **Hit 27** (`0x005ABA00`) is `mov eax, 1; ret 4` (end, no damage) on every input (`range9c`). Stock 250, 253,
  256 the grim wards (their do 14 runs skill do 30, skills/0004 § 9).
- [I] **Hit 2** (tier A, not emulated): skills/0003 § 6 stands; in addition, a missing record or `HitSubMissile1 < 0`
  returns 3 as the ring path does, and the ring's owner (EDX) is `UnitGetOwner(m)`. (0x005A9D80–0x005A9E05,
  fn:sub_005A9D80_MissHit02Ring@0x005A9D80)

## Corrections to earlier findings

- skills/0003 § 6 (tier A), carried there as a dated note: hit 44's radius is any non-zero `sHitPar1` and it has no
  owner test; hit 14 needs an owner and passes `Param3 + (lvl−1)·Param4` to the 18-ring as the fires' range; hit 17's
  flee call takes two level-scaled values (`Param3/4` and `Param5/6`), not one length; hit 3 returns 0 for a unit.

## Data touched

`tbl:Missiles.txt:pSrvHitFunc`, `HitSubMissile1`..`HitSubMissile4`, `sHitPar1`, `sHitPar2`, `SHitCalc1`, `HitFlags`,
`ResultFlags`, `EType`, `ProgOverlay`, `Param1` (hit 25's sub-missile), `Param2` (hit 10's re-target), `Range`,
`LevRange`; `tbl:Skills.txt:calc1`, `calc2`, `calc4`, `aurarangecalc`, `auralencalc`, `aurafilter`, `aurastate`,
`auratargetstate`, `Param1`..`Param6`, `TargetPet`, `TargetAlly`; `tbl:MonStats.txt` `+0x0D` (undead, demon);
`tbl:States.txt:state` (13 `blaze`); ItemStatCost 6, 7, 12, 56, 134; `struct:MissileData+0x0A`, `+0x0C`, `+0x10`,
`+0x28` (hit 10 flags, hit 12 count, hit 22 type, hit 28 ward guid), `+0x2C` (hit 22 guid, hit 10 point);
`struct:DamagePacket+0x00`, `+0x04`, `+0x18`, `+0x2C`, `+0x30`, `+0x34`, `+0x44`; `struct:Game+0x1C`, `+0xA8`; unit
`+0x00`, `+0x04`, `+0x0C`, `+0x14` (MonsterData `+0x28` → owner reference `+0x28/+0x2C/+0x30`), `+0x20` (seed),
`+0x2C`, `+0x5C`; stat list `+0x10` bit 31, `+0x3C`, `+0x40` (chains, `+0x14` state, `+0x2C` next), `+0x58` (state
bits); path `+0x02`, `+0x06`, `+0x1C`, `+0x44`, `+0x54`, `+0x58`..`+0x60`, `+0x7C`.

## Dead ends

- Ghidra's decompile of these `__fastcall`-with-stack functions without signatures shows the stack unit as
  `param_1` and drops the ECX/EDX arguments of most callees (`UnitGetOwner()`, `MISSILE_BuildDamage(in_EDX, param_1,
  …)`); every argument above is read from objdump.
- A first run modelled hit 44's EBX as the owner; it holds the y position at the call (EDI holds the radius).
- A hash-chain collision between the owner and hit 22's stored unit (a shared decoy) made early hit-22 cases miss the
  owner; the case writer now keeps their buckets and decoys apart.

## Open questions

- [L] What `0x005DDD00` does with its two values (hits 17, 28), and what `AreaHitAt`'s return value means (hits 13,
  14, 44 return 1 or 3 by it).
- [L] What `SKILLS_ApplyAuraStats` does with a null list (hits 16, 19 on a new list, § 10).
- [L] The nearest-unit callback `0x0056BCD0` and the `0x88583` / `0xA783` / `0xA683` filter bits (skills/0001 § 4's
  `SkillUnitFilter` reading covers some).
- [L] Everything after each boundary (§§ 3–15), for a later batch or the harness.
