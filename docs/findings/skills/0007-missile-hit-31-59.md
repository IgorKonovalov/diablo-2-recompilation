# 0007 — Catalogue batch 9d: missile server hit functions 31–59 and hit 2

> **Subsystem:** skills/catalogue
> **Question:** what does each missile server hit function 31–59 (`pSrvHitFunc`, `g_MissileSrvHitFuncs`), and the
> tier-A hit 2 carried from batch 9c, do: which Missiles and Skills columns and `MissileData` words it reads, which
> missiles, monsters, rooms and stats it creates or touches, which draws it makes on which seed, what result it
> returns, and which of that the emulator can confirm? What does row 568's `pSrvHitFunc` 64 948 run?
> **Date:** 2026-10-20   **Plan:** 0046 (Phase 1, batch 9d)   **Status:** for review (`lane/p46m4`)

Static reading of the pinned `Game.exe` in Ghidra 12.1.2 (lane copy `workspace/ghidra-p46m4`, symbols replayed from
`re/symbols.csv`) and objdump, then emulation under ADR-0015 with `re/ghidra_scripts/EmuBoundary.java` (unchanged,
`286393aa…`) and the 9d families of `tools/skills_catalogue_emu.py` (§ 2; run:2026-10-20-cat-emu-9d in
[experiments](experiments.md)). Missiles columns are named as in [Missiles](../../tables/Missiles.md), Skills columns
as in [Skills](../../tables/Skills.md), MonStats2 flags as in [MonStats2](../../tables/MonStats2.md). The machinery
that calls a hit function and acts on its result is [skills/0002 § 5](0002-missiles.md#5-the-hit); batch 9c, whose
conventions this batch keeps, is [skills/0006](0006-missile-hit-1-29.md). Stock values come from
`workspace/logs/skills-cat-9d/rows.txt` (`9678d001…`, `excel_bin.py dump` of the 39 rows whose `pSrvHitFunc` is
31–59 or 64 948, and hit 2's six rows); row names from `missiles.txt`.

**Tag convention for this finding** (as skills/0006). A claim marked **[C] (ADR-0021)** rests on emulated cases that
end at an observed boundary (a declared callee's entry), under
[ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md): (a) nothing is patched and each boundary is a
function entry reached by the program's own flow; (b) the checker asserts per case the boundary and its call site
(the return address at ESP), with a site control that fails every matched boundary case; (c) the model gives and the
checker compares every argument the claim uses (registers, stack words, and for a pointer into the caller's frame
the bytes it points to), every byte written before the call, and the state of the missile's, the owner's and the
target's seeds at the boundary (all three, in every case). Each such claim names the boundary it ends at; **the
callee and all code after it are not covered** and keep `[I]` (from the reading), marked "after, `[I]`" in place. No
claim here rests on a callee-saved register that is not a boundary argument (ruling 1 of the `lane/p46m3` review). A
plain `[C]` rests on cases that return; a plain `[I]` is a code reading the emulator does not reach.
(run:2026-10-20-cat-emu-9d)

## Answer (summary)

- [C] **The batch.** 24 table entries are filled in 31–59: 31–33, 35–40, 43–45, 47, 48, 50–59 (30, 34, 41, 42, 46,
  49 and 60–70 are null; the table count is 71). Hit 44 is batch 9c's (skills/0006 § 4) and is not repeated; the
  other 23 and hit 2 are emulated here. Every hit function is `(ECX game, EDX missile; unit)` with `ret 4`.
  (data:g_MissileSrvHitFuncs@0x0073C840, `static.txt`)
- [C] **Draws before the boundaries, all three seeds compared.** Hit 31 rolls the missile's `EType` on the hit unit
  (`sub_005A8C70_MissileRollEType`, the missile's seed); hit 43 draws one `RNG_RangeB(missile seed, PhysMax −
  PhysMin)`; hit 58 re-seeds the missile's seed from its x (`RNG_SeedInit(m+0x20, x)`) and draws two `RNG_Range(2r +
  1)`, x first. No other function of the batch draws before its boundary or return, and no case steps the owner's or
  the target's seed (8 400 cases; a control that moves the missile's draws to the owner's seed fails 140 and 181
  cases). Draws inside a boundary callee (the scatter of hit 40, the spawns of hits 39 and 54, `BuildDamage`, the
  creations) are not covered. (§§ 3, 6, run:2026-10-20-cat-emu-9d)
- [C] (ADR-0021; up to `UnitSetStat`, `UnitSetOverlayStat` or the damage callees, § 3) **Heals and drains.** Hit 31
  (firehead) sets the owner's life to `min(life + max(roll, 0), max life)`; hit 43 (healing vortex) heals **any hit
  unit** (no owner, ally or type test) by `PhysMin + RangeB(PhysMax − PhysMin)`, capped at max life, or first sets the
  row's `ProgOverlay` on a unit that is not at full life; hit 55 (baal inferno) takes `max(MulDiv(mana, clamp(sHitPar1,
  1, 100), 100), 1)` (at most all of it) from a hit player's mana and returns 2 for any other unit.
  (run:2026-10-20-cat-emu-9d `heal9d`)
- [C] **Plain returns.** Hit 37 (blade creeper) returns 2 for a unit and 0 at the end of life; hit 50 (plague vines
  trail) returns 2 for a unit while `elapsed < range − sHitPar1` and 0 otherwise (1 without a record). (§ 4, run:2026-10-20-cat-emu-9d `heal9d`)
- [C] (ADR-0021; up to the first `MissileCreate` or `MissileCreateAt`, §§ 5, 6) **Creations.** Hit 2 (plague javelin,
  gas potions) and hit 59 (baal taunt poison) run `sub_005A9370_MissSubRing16`, whose first creation is direction
  `(0, 2)` with velocity `Param1 << 7` of the sub-missile's row, flags `0x1F` and `sHitPar3` loops when that is > 0,
  else `0x17`; hit 2 from the hit unit's position (the missile's at the end of life). Hit 36 creates `HitSubMissile1`
  at the end of life only (0 for a unit); hit 48 at the path's position words; hit 51 `HitSubMissile1` (then 2 and 3);
  hit 58 at a point `(x − r + Range(2r+1), y − r + Range(2r+1))`, `r = max(sHitPar1, 1)`. **Hit 52 (blade fury)
  tests `HitSubMissile1 ≥ 0` but never writes the block's class word, so it creates class 0 (`arrow`)** in steps of
  `max(sHitPar1, 1)` over 8 directions of length 16. (run:2026-10-20-cat-emu-9d `create9d`)
- [C] (ADR-0021; up to `MissileCreate`, the assertion call or the scatter, § 7) **Novas.** Hit 38 (catapult charged
  ball) and hit 45 (lightning javelins) call `sub_0056D4E0_MissNovaCreate` with `n` creations (38: `(lvl − 1) ·
  sHitPar2 + sHitPar1`, else `max(calc4, 1)`; 45: `sHitPar1`); **for `n ≥ 41` (`(n − 1) / 5 > 7`) it calls the
  assertion `0x00408090(0xF0D)` instead** (§ 7 on the stock rows). The first creation has
  flags 3, target offsets `(14, −14)` and creation callback `0x005AC040` (hit 38 always, hit 45 when `sHitPar2 ≠ 0`).
  Hit 40 (catapult spike ball) passes the same `n` and `n / 4` to `sub_005D5BF0_MissScatterAtTarget`.
  (run:2026-10-20-cat-emu-9d `nova9d`)
- [C] (ADR-0021; up to `MISSILE_BuildDamage` or `sub_005C7DB0_RabiesApply`, § 8) **Area and contagion.** Hit 47
  (molten boulder) rolls on through players and monsters that are not MonStats2 `large` (returns 2) and builds its
  damage for a `large` monster or at the end of life; hit 56 (armageddon and diablogeddon control) builds damage with
  no unit; hit 53 (rabies contagion) passes the contagion on when `10 ≤ end − frame ≤ ElemLen`.
  (run:2026-10-20-cat-emu-9d `area9d`)
- [C] (ADR-0021; up to the portal, room pin, mode, spawn or quest call, § 9) **Events.** Hit 32 (cairnstones) opens a
  permanent portal with `Param4` (stock 38) while `MissileData+0x28 == 0`; hits 33 (towerchestspawner) and 35 (orb
  mist) pin a room (35 the room of the object `MissileData+0x28` names, or else sets that object's mode to 1 when its
  mode is 0); hit 39 (imp spawn) calls `RoomSpawnLevelMon` at the missile on every call; hit 54 (baal spawn) calls
  `PresetMonSpawn` with the `+0x18` word of the owner's unit skill node; hit 57 (baalfx control) once sets `MissileData+0x28 = 1` and asks
  `QUESTS_IsActive(game, 0x24)`. (run:2026-10-20-cat-emu-9d `event9d`)
- [I] **Row 568** (`royalstrikechainlightning`, `pSrvHitFunc` 64 948, `*12` in the `.txt`): every read of the hit
  table (four sites) is behind a signed 16-bit test `test ax, ax; jle` of the function word, and 64 948 is −588 as an
  s16, so the row runs no server hit function. The scan of the four sites is `[C]` (`static.txt`); that the tested word
  is this row's `pSrvHitFunc` is the reading. (§ 10, data:g_MissileSrvHitFuncs@0x0073C840)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005A9D80` | `sub_005A9D80_MissHit02Ring` | (P1.3 name) hit 2 | I |
| `0x005ABD70` | `sub_005ABD70_MissHit31FireheadHeal` | hit 31 | I |
| `0x005ABE50` | `sub_005ABE50_MissHit32Portal` | hit 32 | I |
| `0x005ABEB0` | `sub_005ABEB0_MissHit33RoomPin` | hit 33 | I |
| `0x005ABEE0` | `sub_005ABEE0_MissHit35ObjectPin` | hit 35 | I |
| `0x005ABF70` | `sub_005ABF70_MissHit36SubAtEnd` | (P1.3 name) hit 36 | I |
| `0x005AC020` | `sub_005AC020_MissHit37UnitRet2` | hit 37 | I |
| `0x005AC0A0`, `0x005AC480` | `sub_005AC0A0_MissHit38Nova`, `sub_005AC480_MissHit45Nova` | hit 38, hit 45 | I |
| `0x005AC1D0` | `sub_005AC1D0_MissHit39SpawnMon` | hit 39 | I |
| `0x005AC250` | `sub_005AC250_MissHit40Scatter` | hit 40 | I |
| `0x005AC350` | `sub_005AC350_MissHit43HealVortex` | hit 43 | I |
| `0x005AC550` | `sub_005AC550_MissHit47Boulder` | hit 47 | I |
| `0x005AC6D0` | `sub_005AC6D0_MissHit48SubToPathPos` | hit 48 | I |
| `0x005AC800` | `sub_005AC800_MissHit50Elapsed` | hit 50 | I |
| `0x005AC870` | `sub_005AC870_MissHit51Subs3` | hit 51 | I |
| `0x005AC940` | `sub_005AC940_MissHit52Ring8` | hit 52 | I |
| `0x005ACA50` | `sub_005ACA50_MissHit53Rabies` | hit 53 | I |
| `0x005ACAF0` | `sub_005ACAF0_MissHit54SkillSpawn` | hit 54 | I |
| `0x005ACB60` | `sub_005ACB60_MissHit55ManaDrain` | hit 55 | I |
| `0x005ACC50` | `sub_005ACC50_MissHit56AreaSubAt` | hit 56 | I |
| `0x005AD970` | `sub_005AD970_MissHit57BaalFx` | hit 57 | I |
| `0x005ACDF0` | `sub_005ACDF0_MissHit58Reseed` | (P1.3 name) hit 58 | I |
| `0x005ACF20` | `sub_005ACF20_MissHit59Ring16` | hit 59 | I |
| `0x0056D4E0` | `sub_0056D4E0_MissNovaCreate` | `(ECX game, EDX n; block)`: the assertion for `(n−1)/5 > 7`, else `n` creations around the block's position, the first at offsets `(14, −14)` (§ 7) | I |
| `0x005D5BF0` | `sub_005D5BF0_MissScatterAtTarget` | `(ECX game, EDX m; owner, cls, n, n/4, skill, lvl)`, `ret 0x18`: re-seeds and draws, then creations (read in part, § 7) | I |
| `0x005B3570` | `sub_005B3570_RoomSpawnLevelMon` | `(ECX game, EDX room; x, y)`, `ret 8`: one `RNG_RangeB` and a spawn (read in part, § 9) | I |
| `0x005C7DB0` | `sub_005C7DB0_RabiesApply` | `(ECX game, EDX owner; unit, frames, skill, lvl)`, `ret 0x10` (not read past its tests, § 8) | I |
| `0x00644C20` | `sub_00644C20_SkillKickDamage` | `(ESI unit; flag)`: player `dex − 20 + str`, else `3 · level`, floor 1, then `/ 4 << 8` (flag ≠ 0) or `/ 3 << 8` (flag 0) (§ 3) | I |
| `0x00623990` | `sub_00623990_SkillSrcDamWeapon` | `(unit, 0)`, `ret 8`: called by `SKILLS_GetPhysMin/Max` when `SrcDam ≠ 0` (not read past its inventory read `+0x60`) | I |
| `0x006444A0` | `sub_006444A0_UnitSkillGet18` | `(node)` → the unit skill node's `+0x18` (assertion on null) | I |

## Walkthrough

### 1. The table slots and the shared shape

- [C] `g_MissileSrvHitFuncs[30..70]` are as `static.txt` lists them: 30, 34, 41, 42, 46, 49 and 60–70 null, the
  others as the Functions table (the 24 model addresses equal the table entries, `table_entries=25` with hit 2), count
  word `0x0073C83C` = 71. (data:g_MissileSrvHitFuncs@0x0073C840, `static.txt`)
- [I] Most functions read their record as `DataTables+0xB64 + 0x1A4 · Unit+0x04` after `0 ≤ class < DataTables+0xB6C`
  and stop with 1 without it (hit 2 with 3; hits 32, 33, 35, 37, 39, 53, 54, 57 have no record test or return 0
  either way); the creating ones then require `HitSubMissile1` (`+0x24`, s16) `≥ 0`. The missile's position is
  `PathGetX/Y` of its path (0 without one). (0x005ABD70–0x005ABDB4, fn:sub_005ABF70_MissHit36SubAtEnd@0x005ABF70)

- [I] **Stock rows** (`rows.txt`; `→` the row's `HitSubMissile1`): hit 2 on 43 plaguejavelin → 221, 436
  plaguejavelin2 → 437, 47–49 the gas potions → 222–224, 419 catapult plague ball → 420; hit 31 on 277 firehead;
  32 on 288 cairnstones (`Param4` 38); 33 on 332 towerchestspawner; 35 on 368 orbmist; 36 on 385 bomb in air → 386,
  388 shock field in air → 389, 412 catapult spike in air → 413, 496 sentryspikeinair → 497; 37 on 392 blade
  creeper; 38 on 407 catapultchargedball → 408; 39 on 409 imp spawn monsters; 40 on 411 catapult spike ball → 412;
  43 on 425 healing vortex; 45 on 431 lightingtrailingjavalin → 433, 438 advlighttrailingjav → 440; 47 on 452
  moltenboulder → 455; 48 on 453 moltenboulderemerge → 452; 50 on 475 plague vines trail (`sHitPar1` 15); 51 on 481
  volcano debris 2 → 483; 52 on 505, 507, 509 bladefury1–3 → bladefragment1–3 (`sHitPar1` 1); 53 on 516
  rabiescontagion; 54 on 550 baal spawn monsters; 55 on 554 baal inferno (`sHitPar1` 50); 56 on 577
  armageddoncontrol → 623, 670 diablogeddoncontrol → 674 (`sHitPar1` 3); 57 on 625 baalfx control; 58 on 654 baal
  taunt lightning control → 547 (`sHitPar1` 10); 59 on 655 baal taunt poison control → 549. Hit 52 creates class 0
  (§ 5), not the bladefragment rows its stock rows name. (`rows.txt`, tbl:Missiles.txt:pSrvHitFunc,
  tbl:Missiles.txt:HitSubMissile1)

### 2. Emulation: the 9d families

The method is 9c's (skills/0006 § 2): the call site of every observed boundary asserted with a site control, two or
more negative controls per family (one failing 50 cases or more), the three seeds written and compared in every case,
and the bytes behind a boundary's pointer argument compared (the `MissileCreate` block, 0x5C bytes, every creation;
hit 47's zeroed packet, 0x70 bytes). The boundaries added for 9d: `0x0061AED0` RoomPinSet, `0x00624690`
UNIT_SetMode, `0x005B3570` RoomSpawnLevelMon, `0x005D5BF0` ScatterAtTarget, `0x005C7DB0` RabiesApply, `0x0054E600`
PresetMonSpawn, `0x00623990` the `SrcDam` weapon call, `0x00644C20` the kick damage, `0x00408090` the assertion
message; 9c's stay declared (`MissileCreate`, `MissileCreateAt`, `MISSILE_BuildDamage`, `UnitSetStat`,
`UnitSetOverlayStat`, `PermPortalAtUnit`, `QUESTS_IsActive`, …). Emulated, not observed: `UnitGetOwner`,
`GameFindUnit`, `UnitGetRoom`, `SKILLS_EvalCalc` on constant programs, `SKILLS_GetPhysMin/Max`, `SKILLS_LevelBands`,
`SKILLS_GetElemLen`, `SKILLS_GetUnitSkill`, `MISSDATA_*`, `sub_005A8C70_MissileRollEType`, `STATS_GetUnitStat`,
`UnitGetMaxHp`, `sub_004638A0_MonStats2FlagTest`, `MulDiv`, `sub_005A9370_MissSubRing16` and
`sub_0056D4E0_MissNovaCreate` up to their first creation.

- [C] Five families, **8 400 cases, 0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; every negative control fails, and the site control fails on all 3 796 matched boundary cases
  (28 function, boundary and return-address triples, each a `site` line) (`check.txt` `9ec69cf5…`;
  run:2026-10-20-cat-emu-9d):

  | Family | Functions | Cases | Neg. controls (fails) | Outcomes reached (boundary @ return address) |
  |---|---|---:|---|---|
  | `heal9d` | hit 31, 37, 43, 50, 55 | 1 500 | hit 31 heal not floored (2); hit 43 cap dropped (73); hit 55 drain not floored (3); pct not capped at 100 (6); hit 50 `≤` for `<` (22); draws on the owner's seed (140) | UnitSetStat @0x005ABE1C, @0x005AC468, @0x005ACC29; OverlaySet @0x005AC452; KickDamage @0x00647D46 and SrcDamWeapon @0x00647C66 (in `GetPhysMax/Min`); returns 0, 1, 2 |
  | `create9d` | hit 2, 36, 48, 51, 52, 58, 59 | 2 100 | hit 2 ring from the missile for a unit (120); loops ignored (57); hit 52 with the class written (120); hit 58 offsets swapped (139); draws on the owner's seed (181) | MissileCreate @0x005A945D (in `MissSubRing16`, hits 2, 59), @0x005AC7E6, @0x005AC8FB, @0x005ACA0D, @0x005ACF0A; MissileCreateAt @0x005ABFF2; returns 0, 1, 3 |
  | `nova9d` | hit 38, 40, 45 | 1 500 | hit 45 callback always (65); `sHitPar1/2` swapped (344); assertion at `> 8` (53) | MissileCreate @0x0056D539, Fatal @0x0056D50C (both in `MissNovaCreate`); ScatterAtTarget @0x005AC334; returns 1 |
  | `area9d` | hit 47, 53, 56 | 1 500 | hit 53 `≤ 10` for `< 10` (24); `≥ len` for `> len` (29); hit 47 MonStats2 flag 10 for 11 (42); hit 56 passes the unit (378) | BuildDamage @0x005AC609, @0x005ACD38; RabiesApply @0x005ACAB9; returns 1, 2 |
  | `event9d` | hit 32, 33, 35, 39, 54, 57 | 1 800 | hit 32 `Param3` for `Param4` (86); hit 54 first match wins (19); hit 35 mode test inverted (106) | PermPortalAtUnit @0x005ABEA0; RoomPinSet @0x005ABECB, @0x005ABF25; SetMode @0x005ABF33; RoomSpawnLevelMon @0x005AC23E; PresetMonSpawn @0x005ACB48; QuestActive @0x005AD9A2; returns 0, 1 |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt` `d909b72d…`, 50 of 50 pins): 9c's (`g_UnitHashOffsets`,
  the `CALC_Eval` jump table, the skills calc function count, `g_BitMask32`, `0x005A8C70`'s `EType` jump table), and
  new: `MissSubRing16`'s directions (`0x006E2510` x / `0x006E24D0` y, `.rdata`; x `0 1 2 2 2 2 2 1 0 −1 −2 −2 −2 −2
  −2 −1`, y `2 2 2 1 0 −1 −2 −2 −2 −2 −2 −1 0 1 2 2`) and hit 52's (`0x006E2A58` x / `0x006E2A38` y, `.rdata`; x `16
  16 0 −16 −16 −16 0 16`, y `0 16 16 16 0 −16 −16 −16`). Skills, ItemStatCost, MonStats, MonStats2, the owner's skill
  list, the object and the hash buckets are scratch records written one field per field read.
- [C] The weak controls (hit 31's floor 2, hit 55's floor 3 and cap 6) each decide their claim deterministically (a
  negative roll, a drain under 1, a percent above 100), beside a control of 73 or more cases in the same family
  (reverser review-fixes 10; ruling 2 of the `lane/p46m3` review). The hit-2 ring from the missile itself is reached
  by 3 cases (the end of life is rare in `create9d`'s draws); the other 120 ring cases are from a unit.
  (run:2026-10-20-cat-emu-9d)
- [I] **Not reached** (from the reading): everything after each boundary (listed per function below); hit 48 without
  a path (`PathGetPosX` reads the path unchecked, a fault); hit 54 with a null node (the assertion of
  `sub_006444A0_UnitSkillGet18` is not reached: `GetUnitSkill` returns 0 first). (run:2026-10-20-cat-emu-9d)
- [I] ADR-0015 (3): the `[C]` claims, those marked ADR-0021 included, cover the code as a map. What the offsets mean
  keeps its own tag (Missiles and Skills columns `[C]` by layout; `MissileData` words `[I]`, skills/0002 § 1); nothing
  here says when the game runs these functions or on which seed state. (run:2026-10-20-cat-emu-9d)

### 3. Hit 31, 43 and 55: heals and drains

```c
// fn:sub_005ABD70_MissHit31FireheadHeal@0x005ABD70, trimmed
if (!rec || !(owner = UnitGetOwner(game, m)) || !unit) return 1;
memset(&pkt, 0, 0x70);
roll = MissileRollEType(game, m, unit, &pkt);             // EAX: the rolled elemental damage
max = UnitGetMaxHp(owner); life = STATS_GetUnitStat(owner, 6, 0) + (roll < 0 ? 0 : roll);
UnitSetStat(owner, 6, life < max ? life : max, 0);
return 2 + (rec->CollideKill != 0);
```

- [C] (ADR-0021; ends at `UnitSetStat` @0x005ABE1C) **Hit 31** as above: the owner's life (stat 6) becomes
  `min(life + max(roll, 0), max life)`, the roll being 9b's `EType` model (skills/0005 § 13) on the missile's seed.
  Without a record, an owner or a unit it returns 1. After, `[I]`: returns 2, or 3 with `CollideKill`.
  (run:2026-10-20-cat-emu-9d `heal9d`, 0x005ABD70–0x005ABE41, tbl:Missiles.txt:CollideKill)
- [C] (ADR-0021; ends at `UnitSetStat` @0x005AC468 or `UnitSetOverlayStat` @0x005AC452) **Hit 43** (`0x005AC350`):
  with a record, a unit and a Skills row (else 1; **no owner test, no type, ally or pet test**): `mn =
  SKILLS_GetPhysMin(owner, skill, lvl, 1)`, `mx = SKILLS_GetPhysMax(…)`, `h = mn + RNG_RangeB(m+0x20, mx − mn)`; when
  the unit's life ≠ its max life and `ProgOverlay` (`+0x36`, s16) > 0, `UnitSetOverlayStat(unit, ProgOverlay, 0)`
  (the boundary; after, `[I]`: the life write below); else `UnitSetStat(unit, 6, min(life + h, max life), 0)`. After,
  `[I]`: returns 1 with `CollideKill`, else 0 (0x005AC468–0x005AC47C). (run:2026-10-20-cat-emu-9d `heal9d`,
  fn:sub_005AC350_MissHit43HealVortex@0x005AC350, tbl:Missiles.txt:ProgOverlay)
- [C] (emulated inside hit 43; ends at the kick or weapon call where they are reached) **`SKILLS_GetPhysMin/Max`**
  with `Kick` (Skills `+0x05` bit 1) clear and `SrcDam` 0: `(MinDam + SKILLS_LevelBands(lvl, MinLevDam1..5))` (bands
  2–8, 9–16, 17–22, 23–28, 29+; 0 at `lvl ≤ 1`), plus `MulDiv(v, DmgSymPerCalc, 100)` when that calc is set and
  non-zero, then `<< HitShift` (the same with the `Max` columns). With `SrcDam ≠ 0`, `GetPhysMin` calls
  `sub_00623990_SkillSrcDamWeapon(owner, 0)` first (the boundary @0x00647C66). With `Kick`, `GetPhysMin` gives
  `max(dex − 20 + str, 1) / 4 << 8` for a player owner, `max(3 · level, 1) / 4 << 8` for another owner (the cases set `Kick` only with an owner),
  and `GetPhysMax` calls `sub_00644C20_SkillKickDamage(flag 0)` (the boundary @0x00647D46; ESI, its unit, is not
  compared). (run:2026-10-20-cat-emu-9d `heal9d`, fn:SKILLS_GetPhysMin@0x00647BC0, fn:SKILLS_GetPhysMax@0x00647D00,
  tbl:Skills.txt:Kick, tbl:Skills.txt:SrcDam, tbl:Skills.txt:MinDam, tbl:Skills.txt:DmgSymPerCalc)
- [I] `sub_00644C20_SkillKickDamage` divides by 4 when its flag is set and by 3 when it is 0 (`imul 0x55555556`), so
  the kick **maximum** is `max(…, 1) / 3 << 8`, not `/ 4` as the Skills table doc's `Kick` row has it for both.
  (0x00644C20–0x00644C8C)
- [C] (ADR-0021; ends at `UnitSetStat` @0x005ACC29) **Hit 55** (`0x005ACB60`): a unit that is not a player (type 0),
  or no unit, returns 2; without a record or with `sHitPar1 ≤ 0`, 1; with mana (stat 8) ≤ 0, 1; else `p = clamp(sHitPar1,
  1, 100)`, `d = max(MulDiv(mana, p, 100), 1)`, at most `mana`, and `UnitSetStat(unit, 8, mana − d, 0)`. After, `[I]`:
  returns 2. (run:2026-10-20-cat-emu-9d `heal9d`, fn:sub_005ACB60_MissHit55ManaDrain@0x005ACB60,
  tbl:Missiles.txt:sHitPar1)

### 4. Hit 37 and hit 50: plain returns

- [C] **Hit 37** (`0x005AC020`) is `neg; sbb; and 2`: 2 for any unit, 0 at the end of life, with no other read.
  (run:2026-10-20-cat-emu-9d `heal9d`, fn:sub_005AC020_MissHit37UnitRet2@0x005AC020)
- [C] **Hit 50** (`0x005AC800`): without a record 1; with a unit, 2 while `MISSDATA_GetElapsed(m) <
  MISSDATA_GetRange(m) − sHitPar1` (elapsed = range − frames left, s16 words `+0x0E` and `+0x10`), else 0; at the
  end of life 0.
  (run:2026-10-20-cat-emu-9d `heal9d`, fn:sub_005AC800_MissHit50Elapsed@0x005AC800, fn:MISSDATA_GetElapsed@0x0064A3B0)

### 5. Hit 2, hit 59 and hit 52: rings

- [C] (ADR-0021; ends at the first `MissileCreate` @0x005A945D inside `sub_005A9370_MissSubRing16`) **Hit 2**
  (`0x005A9D80`, tier A): without a record or with `HitSubMissile1 < 0` it returns 3; else it calls
  `MissSubRing16(ECX game, EDX owner; src, HitSubMissile1, skill, lvl, …, sHitPar3)` with `src` the hit unit (the
  missile at the end of life). The ring returns 0 without an owner or with the class outside the Missiles count (a
  null source, refused too, is not reached), and hit 2 then returns 3. Its first creation: block `{flags 0x1F, owner,
  source src, cls, x, y = src's SubX/SubY, skill, lvl, target (0, 2), +0x28 velocity Param1(cls) << 7, loops +0x34 =
  sHitPar3}` when `sHitPar3 > 0`, else flags `0x17` and no loops. After, `[I]`: the further directions and the return
  value 3. (run:2026-10-20-cat-emu-9d `create9d`, fn:sub_005A9D80_MissHit02Ring@0x005A9D80,
  fn:sub_005A9370_MissSubRing16@0x005A9370, tbl:Missiles.txt:Param1)
- [C] (ADR-0021; same boundary) **Hit 59** (`0x005ACF20`): with a record, `HitSubMissile1 ≥ 0` and an owner (else
  1): `MissSubRing16(game, owner; m, HitSubMissile1, skill, lvl, …, 0)`, so the first creation has flags `0x17` at
  the missile's position. After, `[I]`: returns 1.
  (fn:sub_005ACF20_MissHit59Ring16@0x005ACF20)
- [I] The ring's fifth and sixth arguments choose the later directions and do not change the first creation, so no
  case compares them: hit 2 passes `sHitPar1`, `sHitPar2` (skills/0003 § 6: every `sHitPar2`-th of 16 directions,
  a second ring at every `sHitPar1`-th with `Param2 · 128`), hit 59 `max(sHitPar1, 1)` and 2. (0x005A9DC3–0x005A9DFC,
  0x005ACF69–0x005ACF94)
- [C] (ADR-0021; ends at the first `MissileCreate` @0x005ACA0D) **Hit 52** (`0x005AC940`): with a record,
  `HitSubMissile1 ≥ 0` and an owner (else 1): block `{flags 2, owner, source m, skill, lvl, target (16, 0)}` and **the
  class word `+0x10` left 0** (the block is zeroed and no store reaches `+0x10`; a control that writes
  `HitSubMissile1` there fails 120 of 120 creation cases). After, `[I]`: the loop over the 8 directions in steps of
  `max(sHitPar1, 1)`, each created missile's `+0x28/+0x2C` set to that direction; returns 1. (run:2026-10-20-cat-emu-9d `create9d`, 0x005AC9A3–0x005ACA32,
  fn:sub_005AC940_MissHit52Ring8@0x005AC940)

### 6. Hit 36, 48, 51, 58: single creations

- [C] (ADR-0021; ends at `MissileCreateAt` @0x005ABFF2) **Hit 36** (`0x005ABF70`): with a record and `HitSubMissile1
  ≥ 0` (else 1); for a unit, 0; at the end of life `MissileCreateAt(ECX game, EDX owner; skill, lvl, HitSubMissile1,
  SubX, SubY)`. After, `[I]`: the new missile's `+0x28` = this one's; returns 1.
  (run:2026-10-20-cat-emu-9d `create9d`, fn:sub_005ABF70_MissHit36SubAtEnd@0x005ABF70)
- [C] (ADR-0021; ends at `MissileCreate` @0x005AC7E6) **Hit 48** (`0x005AC6D0`): with a record and `HitSubMissile1 ≥
  0` (else 1; no owner or unit test): `{flags 0x21, owner, cls, x, y, skill, lvl, target = PathGetPosX/Y (path +0x10,
  +0x12)}`. After, `[I]`: returns 1. (fn:sub_005AC6D0_MissHit48SubToPathPos@0x005AC6D0)
- [C] (ADR-0021; ends at the first `MissileCreate` @0x005AC8FB) **Hit 51** (`0x005AC870`): with a record and
  `HitSubMissile1 ≥ 0` (else 1; no owner test): `{owner, source m, cls HitSubMissile1, skill, lvl}`, flags 0. After,
  `[I]`: the same block with `HitSubMissile2` and then `HitSubMissile3` when each is ≥ 0; returns 1. (fn:sub_005AC870_MissHit51Subs3@0x005AC870)
- [C] (ADR-0021; ends at `MissileCreate` @0x005ACF0A) **Hit 58** (`0x005ACDF0`): with a record, `HitSubMissile1 ≥ 0`
  and an owner (else 1): `RNG_SeedInit(m+0x20, SubX)` (low = x, high = 666), `r = max(sHitPar1, 1)`, `tx = x − r +
  RNG_Range(m+0x20, 2r + 1)`, then `ty = y − r + RNG_Range(m+0x20, 2r + 1)`; block `{flags 0x20, owner, source m,
  cls, skill, lvl, target (tx, ty)}`; the missile's seed at the boundary is the state after the two draws. After,
  `[I]`: returns 1. (run:2026-10-20-cat-emu-9d
  `create9d`, fn:sub_005ACDF0_MissHit58Reseed@0x005ACDF0, fn:RNG_SeedInit@0x00650E40)

### 7. Hit 38, 45 and 40: novas and the scatter

```c
// fn:sub_005AC0A0_MissHit38Nova@0x005AC0A0, trimmed (hit 45 0x005AC480 and hit 40 0x005AC250 differ as below)
if (!rec || rec->HitSubMissile1 < 0 || !(owner = UnitGetOwner(game, m))) return 1;
memset(&blk, 0, 0x5C); blk.flags = 3; blk.x = SubX(m); blk.y = SubY(m); blk.owner = owner;
blk.cls = rec->HitSubMissile1; blk.skill = skill; blk.lvl = lvl; blk.cb = 0x005AC040;
n = (lvl - 1) * rec->sHitPar2 + rec->sHitPar1;
if (n <= 0) { if (!skillrec) return 1; n = max(SKILLS_EvalCalc(owner, skill->calc4, skill, lvl), 1); }
MissNovaCreate(game, n, &blk);                             // hit 40: MissScatterAtTarget(game, m; owner, cls, n, n / 4, skill, lvl)
return 1;
```

- [C] (ADR-0021; ends at `MissileCreate` @0x0056D539 or the assertion call @0x0056D50C inside
  `sub_0056D4E0_MissNovaCreate`) **Hit 38** as above: `MissNovaCreate` computes `(n − 1) / 5` (signed, truncating:
  `imul 0x66666667; sar 1`) and, when it is above 7 (`n ≥ 41`), calls `0x00408090(0xF0D)`, the assertion-message
  helper (after, `[I]`: `0x00408A60` and the exit `0x00681E09`); else it sets the block's target `(14, −14)` and
  creates. The block reaches the creation whole: `{flags 3, owner, cls, x, y, skill, lvl, target (14, −14), +0x54
  callback 0x005AC040}`. (run:2026-10-20-cat-emu-9d `nova9d`, fn:sub_005AC0A0_MissHit38Nova@0x005AC0A0,
  fn:sub_0056D4E0_MissNovaCreate@0x0056D4E0, tbl:Missiles.txt:sHitPar2, tbl:Skills.txt:calc4)
- [C] (ADR-0021; same boundaries) **Hit 45** (`0x005AC480`): with a record, `HitSubMissile1 ≥ 0` and `sHitPar1 > 0`
  (else 1; **no owner test**, the block's owner may be 0): `n = sHitPar1`, and the callback `0x005AC040` only when
  `sHitPar2 ≠ 0`. (fn:sub_005AC480_MissHit45Nova@0x005AC480)
- [C] (ADR-0021; ends at `sub_005D5BF0_MissScatterAtTarget` @0x005AC334) **Hit 40** (`0x005AC250`): the tests and
  `n` of hit 38, then `ScatterAtTarget(ECX game, EDX m; owner, HitSubMissile1, n, n / 4, skill, lvl)` (`n / 4`
  truncating, `cdq; and 3; sar 2`). After, `[I]`: the callee re-seeds a seed (`RNG_SeedInit`), draws two
  `RNG_RangeB` and creates; returns 1. (run:2026-10-20-cat-emu-9d `nova9d`, fn:sub_005AC250_MissHit40Scatter@0x005AC250)
- [I] After the first creation (0x0056D539–0x0056D5E2): `n − 1` more, in rings of up to 5 (target offsets products of
  the tables at `0x006E1510`/`0x006E14F4` and `0x006E14E4`/`0x006E14C8`). The callback `0x005AC040` re-seeds each new
  missile from its path x (`RNG_SeedInit`), sets path type 10, a range `min(MissileData range, 255)` and plans its
  path (`sub_005AC040_MissCbReseedPathX`, skills/0003 § 6).
- [I] On stock rows: hit 38's 407 catapultchargedball (`sHitPar1` 4, `sHitPar2` 2) gives `n = 2·lvl + 2`, so a
  missile level of 20 or more reaches the assertion (whether a catapult's missile level gets there is not read, Open
  questions); hit 45's rows give `n` 10 and 18 with the callback (`sHitPar2` 1). (`rows.txt`,
  fn:sub_0056D4E0_MissNovaCreate@0x0056D4E0, tbl:Missiles.txt:sHitPar1)

### 8. Hit 47, 56 and 53: area hits and the contagion

- [C] (ADR-0021; ends at `MISSILE_BuildDamage` @0x005AC609) **Hit 47** (`0x005AC550`): with a record and an owner
  (else 1); for a unit that is not a monster (type 1) or whose MonStats2 `large` flag (`MonStats2FlagTest(class,
  11)`, `+0x05` bit 3) is clear, 2 (damage, keep rolling); else (a `large` monster, or the end of life)
  `BuildDamage(ECX game, EDX owner; m, unit, packet)` on a zeroed 0x70-byte packet (compared). After, `[I]`
  (0x005AC609–0x005AC6BF): radius `sHitPar1 > 0 ? : max(aurarangecalc, 1)` (without a Skills row it returns 1 there), the
  `HitFlags`/`ResultFlags` OR's, `AreaHitAt(owner; x, y, radius, packet, 0)`, result 1, or 3 when it returns 0, then
  `sub_005AAA90_MissSubRing18(EAX m; game, HitSubMissile1, radius, max(sHitPar2, 1))` with no test of
  `HitSubMissile1`. (run:2026-10-20-cat-emu-9d `area9d`,
  fn:sub_005AC550_MissHit47Boulder@0x005AC550, fn:sub_004638A0_MonStats2FlagTest@0x004638A0, tbl:MonStats2.txt:large)
- [C] (ADR-0021; ends at `MISSILE_BuildDamage` @0x005ACD38) **Hit 56** (`0x005ACC50`): with a record and an owner
  (else 1), `BuildDamage(owner; m, 0, packet)` whatever the unit. After, `[I]`: radius as hit 47 (1 returned without a Skills row), the OR's,
  `AreaHitAt(owner; x, y, radius, packet, 0)`, and when `HitSubMissile1 ≥ 0`
  `MissileCreateAt(game, owner; skill, lvl, HitSubMissile1, x, y)`; returns 1. (fn:sub_005ACC50_MissHit56AreaSubAt@0x005ACC50)
- [C] (ADR-0021; ends at `sub_005C7DB0_RabiesApply` @0x005ACAB9) **Hit 53** (`0x005ACA50`): with an owner and a unit
  (else 1; no record test): `s = MissileData+0x28 − Game+0xA8` (signed); `s < 10` → 1; `s >
  SKILLS_GetElemLen(owner, skill, lvl, 1)` → 1 (`jg`; at the length it passes); else `RabiesApply(ECX game, EDX owner;
  unit, s, skill, lvl)`. `GetElemLen` as emulated: `ELen + bands` (`(lvl−1)·ELevLen1` to 8, `+ (lvl−8)·ELevLen2` to
  16, `+ (lvl−16)·ELevLen3` above), plus `MulDiv(v, ELenSymPerCalc, 100)` when that calc is set and non-zero; 0 at
  `lvl ≤ 0` or without a Skills row. After, `[I]`: returns 2.
  (run:2026-10-20-cat-emu-9d `area9d`, fn:sub_005ACA50_MissHit53Rabies@0x005ACA50, fn:SKILLS_GetElemLen@0x00644F20,
  tbl:Skills.txt:ELen, tbl:Skills.txt:ELenSymPerCalc)

### 9. Hit 32, 33, 35, 39, 54, 57: events

- [C] (ADR-0021; ends at `sub_005A9930_PermPortalAtUnit` @0x005ABEA0) **Hit 32** (`0x005ABE50`): with a record, no
  unit and `MissileData+0x28 == 0`, `PermPortalAtUnit(ECX game, EDX m; Param4)`; else 0. After, `[I]`: returns 0.
  (run:2026-10-20-cat-emu-9d `event9d`, fn:sub_005ABE50_MissHit32Portal@0x005ABE50,
  tbl:Missiles.txt:Param4)
- [C] (ADR-0021; ends at `sub_0061AED0_RoomPinSet` @0x005ABECB) **Hit 33** (`0x005ABEB0`): at the end of life, with a
  room (`UnitGetRoom(m)`), `RoomPinSet(room, 1)`; else 0. After, `[I]`: returns 0.
  (fn:sub_005ABEB0_MissHit33RoomPin@0x005ABEB0)
- [C] (ADR-0021; ends at `RoomPinSet` @0x005ABF25 or `UNIT_SetMode` @0x005ABF33) **Hit 35** (`0x005ABEE0`): for a unit
  0; `obj = GameFindUnit(game, 2, MissileData+0x28)`, none → 0; with `UnitGetRoom(obj)` (an object reads its static
  path's `+0x00`) `RoomPinSet(room, 1)`; without one, when the object's mode `+0x10` is 0 `UNIT_SetMode(obj, 1)`, and
  when it is not, 1. After, `[I]`: the mode test after the pin; after the mode set, `OBJECTS_GetRecord(obj+0x04)` and
  `sub_005417D0_UnitQueueEvent(game, obj; 1, Objects+0xDC >> 8 + Game+0xA8, 0, 0)`; returns 1.
  (fn:sub_005ABEE0_MissHit35ObjectPin@0x005ABEE0, fn:sub_00620BB0_UnitGetRoom@0x00620BB0)
- [C] (ADR-0021; ends at `sub_005B3570_RoomSpawnLevelMon` @0x005AC23E) **Hit 39** (`0x005AC1D0`): on every call (no
  record, unit or owner test), `RoomSpawnLevelMon(ECX game, EDX UnitGetRoom(m); x, y)`. After, `[I]`: returns 1; the
  callee draws one `RNG_RangeB`. (fn:sub_005AC1D0_MissHit39SpawnMon@0x005AC1D0)
- [C] (ADR-0021; ends at `sub_0054E600_PresetMonSpawn` @0x005ACB48) **Hit 54** (`0x005ACAF0`): for a unit or without
  an owner, 1; `node = SKILLS_GetUnitSkill(owner, skill)` (the node with that id and `+0x3C == 0`; a later match
  replaces the best when the best is unset or the match's `+0x34` is −1, is skipped when the best's `+0x34` is −1, and
  else wins on a higher `+0x28`, signed), none → 1; else `PresetMonSpawn(ECX game, EDX UnitGetRoom(m); node+0x18, x,
  y, 1)`. After, `[I]`: returns 1. (run:2026-10-20-cat-emu-9d `event9d`,
  fn:sub_005ACAF0_MissHit54SkillSpawn@0x005ACAF0, fn:SKILLS_GetUnitSkill@0x006439F0)
- [C] (ADR-0021; ends at `QUESTS_IsActive` @0x005AD9A2) **Hit 57** (`0x005AD970`): for a unit or with
  `MissileData+0x28 ≠ 0`, 0; else `MissileData+0x28 = 1` (compared at the boundary) and `QUESTS_IsActive(game, 0x24)`.
  After, `[I]`: when active `sub_0058E920_BaalFxSpawnTyrael(game, room; m)`, then `RoomPinSet(room, 1)` with
  `room = UnitGetRoom(m)`; returns 0. (fn:sub_005AD970_MissHit57BaalFx@0x005AD970)

### 10. Row 568's 64 948

- [C] `static --batch 9d` scans every `.text` read of `g_MissileSrvHitFuncs` (0x0073C840): four, at 0x005ADA21,
  0x005AE0AF, 0x005AE11A and 0x005B02E3, each with `test ax, ax; jle` within the 12 instructions before it (at
  0x005ADA11, 0x005AE09F, 0x005AE10A, 0x005B02D3). (`static.txt`)
- [I] The tested word is the record's `pSrvHitFunc` (u16 at the record, read as `ax`), so a value above 0x7FFF is
  negative and skips the call: row 568 royalstrikechainlightning (64 948, −588 as s16; the `.txt` cell is `*12`) has
  no server hit function. (fn:MISSILE_HitUnit@0x005ADF10, `rows.txt`)

## Corrections to earlier findings

- skills/0003 § 6 (tier A), carried there as a dated note: hit 2's map up to its first creation is now `[C]`
  (ADR-0021), with the ring's refusals (no owner, class outside the count) returning 3 through hit 2
  (fn:sub_005A9D80_MissHit02Ring@0x005A9D80).
- skills/0006 § 16: hit 2's emulation, carried to this batch, is done (dated note there).
- The Skills table doc's `Kick` row gives `/ 4` for both minimum and maximum; the maximum divides by 3 (§ 3, `[I]`);
  sent to the archivist with the column readers (fn:sub_00644C20_SkillKickDamage@0x00644C20).

## Data touched

`tbl:Missiles.txt:pSrvHitFunc`, `HitSubMissile1`..`HitSubMissile3`, `sHitPar1`, `sHitPar2`, `sHitPar3`, `HitFlags`,
`ResultFlags`, `EType`, `ProgOverlay`, `CollideKill`, `Param1` (the ring's sub-missile row), `Param3`, `Param4`;
`tbl:Skills.txt:Kick`, `SrcDam`, `HitShift`, `MinDam`, `MaxDam`, `MinLevDam1`..`5`, `MaxLevDam1`..`5`,
`DmgSymPerCalc`, `ELen`, `ELevLen1`..`3`, `ELenSymPerCalc`, `calc4`, `aurarangecalc`; `tbl:MonStats2.txt:large`;
ItemStatCost 0, 2, 6, 7, 8, 12; `struct:MissileData+0x0A`, `+0x0C`, `+0x0E`, `+0x10`, `+0x28` (hit 32/57 once flag,
hit 35 object guid, hit 53 end frame); `struct:Game+0xA8`; unit `+0x00`, `+0x04`, `+0x0C`, `+0x10` (object mode),
`+0x20` (seed), `+0x2C` (path; an object's static path `+0x00` room), `+0xA8` (skill list: `+0x04` first node; node
`+0x00` record, `+0x04` next, `+0x18`, `+0x28`, `+0x34`, `+0x3C`); path `+0x02`, `+0x06`, `+0x10`, `+0x12`, `+0x1C`.

## Dead ends

- A first `event9d` run left the object's type word 0, so `UnitGetRoom` took the path branch for it and 58 hit-35
  cases missed the pin; objects are type 2 (the static path `+0x00` is the room).
- A first `lenlt` control failed no case: no case had the rabies end frame at the length. The writer now puts 30 % of
  the hit-53 cases at the length or one off it.

## Open questions

- [L] Whether a monster's missile level reaches 20 for 407 catapultchargedball (hit 38's assertion at `n ≥ 41`), and
  what the assertion helper `0x00408090` prints for line `0xF0D`.
- [L] What `MissileData+0x28` holds for 368 orbmist (the object guid hit 35 finds) and who writes it; what the unit
  skill node's `+0x18` is (hit 54's monster id, by its use as `PresetMonSpawn`'s first argument).
- [L] Why hit 52 leaves the class 0: whether blade fury's fragments in the game are `arrow` missiles, or another
  path creates `bladefragment1..3` (a harness check).
- [L] Everything after each boundary (§§ 3–9), for a later batch or the harness.
