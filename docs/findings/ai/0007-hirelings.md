# 0007 — Catalogue batch 6 (hirelings): AI row 61 `Hireable`, state rows 4–6 and `MERCAI_PickSkill`

> **Subsystem:** monsters/ai
> **Question:** for batch 6 (table row 61 `Hireable`, its `alt`, and state rows 4, 5 and 6), what do the think
> functions do on an AI event: which `aip` slots, MonStats and Hireling columns they read, which AI-control words they
> keep, which draws they make on which seed and in which order, and which command, skill or path request they end in?
> And which skill list does row 61 use (plan 0052 P1.2: `roguehire` and `act2hire` also name MonStats skills)?
> **Date:** 2026-11-03   **Plan:** 0052 (Phase 1, batch P1.2, catalogue batch 6)   **Status:** reviewed (`lane/r52g`; plan 0052 closed 2026-11-04)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-r52g`, symbols replayed from
`re/symbols.csv`, then the scratch `__fastcall` signatures `b67-sym-scratch.csv` built by `b67-scratch.py`; a reading
aid, not symbol rows; decompiles `b67-decompile.c`, `b67-decompile2.c`, `b67-decompile3.c`) and objdump (`b67-asm.txt`:
the ranges `0x005E3930`–`0x005E3EA0`, `0x005E4D30`–`0x005E5710` and `0x005E7AC0`–`0x005E7D30` for this batch, which
hold no function of another batch), then emulation of the seven functions under ADR-0015/ADR-0021 (§ 4,
run:2026-10-30-ai-cat-emu-6, shared with batch 7, [ai/0008](0008-bosses-a.md)). Kept outputs are under
`workspace/logs/r52g/` (manifest `manifest.sha256`, one path base: that directory; the emulation under `emu/`, its own
manifest; the development run under `emu/dev-1/`, its own manifest and tool copy). Stock values come from
`b67-rows.txt` (`python3 -I tools/ai_survey.py rows workspace/merged/data/global/excel <row>`). Every register argument
quoted below was read from objdump; the multiplier sites and RNG calls per function are counted by `b67-draws.py`
(`b67-draws.txt`), the RNG call windows are `b67-rngsites.txt` (`b67-rngsites.py`), the callers of the batch's functions
are `b67-refs.txt` (`b67-refs.py`: every instruction of a whole-image objdump naming the address, and every file offset
holding it as a little-endian dword), and the table words are `b67-tblrows.txt` (`b67-peread.py`). The machinery is
[ai/0001](0001-machinery.md); the notation and the helpers of batches 1–5 are [ai/0002](0002-pool-a.md) § Notation and
§ 4, [ai/0005](0005-pool-d.md) and [ai/0006](0006-summons.md); names below are `re/symbols.csv` names.

**Notation** as ai/0006: `G`, `U`, `t` = `ctx+0x08`, `dist` = `ctx+0x14`, `melee` = `ctx+0x18`, `ctl` = `ctx+0x00`,
`M` = `ctx+0x1C`, `T` = `G+0xA8`, `d` = `G+0x6D`; `aipK` the s16 at `M + 0x56 + 6(K−1) + 2d`; `SkillK` the s16 at
`M + 0x170 + 2(K−1)`, `SkKmode` the byte at `M + 0x180 + (K−1)`; `draw` one inline step of the acting unit's seed
`U+0x20/+0x24`, low word mod 100; `Range(n)` = `RNG_Range` on the unit's seed, `Pow2(n)` = `RNG_RangePow2`; `v14`,
`v18`, `v1C` = `AiCtl+0x14/+0x18/+0x1C`. `O` = `MonsterOwner(U)`. Helpers: `SetModeAtUnit(m, u)`, `Idle(n)`,
`Walk(t, f)` (`MonAiWalkToUnit`), `T56(t, a, b)` (`MonAiWalkToUnitType56`), `Ovr(type, a, b)` (`MonAiPathOverride`,
`ECX` unit, `EDX` type, stack words in call order), `StepAway(o, n, f)`, `WanderRing(n)`, `WanderNear(o, n)`
(`MonAiWanderNearUnit`), `UseSkill(mode, skill, t, x, y)`, `FindHostile(&d, &m)`, `FindTarget(ctl, &d, &m)`,
`Dist(a, b)` (`AiDistUnits`). Hireling columns by offset ([Hireling](../../tables/Hireling.md)): `+0x01C` `Level`,
`+0x064` `DefaultChance`, `+0x078 + 4k` `Skill1..6`, `+0x090 + 4k` `Chance1..6`, `+0x0A8 + 4k` `ChancePerLvl1..6`,
`+0x0C0 + k` `Mode1..6`.

## Answer (summary)

- [I] **The batch.** Four entries for one table row and three state rows: row 61 `Hireable` and state row 4 share the
  think 0x005E52D0 and the `alt` 0x005E5280; state 5 is 0x005E7AC0 (also table row 60 `GoodNpcRanged`'s think); state
  6 is 0x005E7C10. All four rows are of kind 0 (no target search before the think; `b67-tblrows.txt`, ai/0001 § 4).
  Row 61's think reaches the fight step 0x005E5050 (one caller, 0x005E55BB) and the follow step 0x005E3930 (five
  calls, all in row 61's think, kinds 0, 1 and 3); the fight step calls `MERCAI_PickSkill` (0x005E51EA, 0x005E5229).
  The `alt` 0x005E5280 is also table row 128 `Nihlathak`'s `+C` word (`b67-refs.txt`, `b67-tblrows.txt`).
  (data:g_MonAiTable@0x0073CA18, data:g_MonAiStateRows@0x0073D358, fn:sub_005E52D0_AiHireable@0x005E52D0)
- [I] **Row 61, the hireling with an owner.** No player owner (`MonsterOwner` null or its `Unit+0x00` ≠ 0):
  `MonAiInit(ctl, 5)` for class 271 `roguehire`, else `MonAiInit(ctl, 6)`, then `Idle(10)`. Else it clears state 12
  (`inferno`) if set, returns with no command while the unit's mode is 2 or 15, and takes three distance bands from
  `v14`: for `16 < v14 < 20` (signed) far = `2·v14`, near = `v14`, n = `v14 >> 1`; otherwise 24, 16 and 5. With
  `e = Dist(U, O)` (unsigned compares): `e > 100` follow kind 3 (a teleport beside the owner); `e > far` kind 1 (the
  owner's trail); `e > near` and the owner in player mode 2 or 6, kind 0; in mode 3 kind 0 with the run flag. Then,
  in mode 1 only: a blocked cell (`COLL_PatternTestBool`, mask `0x40`) and `Pow2(128) < 6` (classes 338, 560, 561) or
  `< 12` (the others) → `WanderRing(5)`; out of town a hostile from `FindHostile` at distance `< 25` → the fight step;
  a blocked cell → `WanderRing(5)`; another logic region than the owner's → kind 0 with the run flag; `Dist ≤ 1` → step
  off the owner; else `Range(100) < 5` → `WanderNear(O, near)`, else `Idle(5)`. A unit not in mode 1 cancels its
  event-2 entries and idles 5. (0x005E52D0–0x005E5703, fn:sub_005E52D0_AiHireable@0x005E52D0)
- [I] **The fight step** `(ECX game, EDX U; class, owner, target, seed, ctx)`: a hit chance `c` = 98 for classes 338,
  560 and 561, else `min(95, v14 + 40 + 2·level)` (`STATS_GetUnitStat(U, 12, 0)`); no pet entry for the unit in the
  owner's list (`PETS_GetInfo`) → `Idle(10)`; one draw on the passed seed: `draw < c` sets `v14 = 0` (a hit), else
  `v14 += 10`. `aip1` = 0 (rows `roguehire`, `act3hire`) is the ranged branch: within 4, a second draw `< 50` backs off
  (`WanderNear(owner, 4)`, else `StepAway(t, 4, 1)`); `aip1` ≠ 0 (`act2hire`, `act5hire1`, `act5hire2`) is the melee
  branch: within 3 and `InMeleeRange`, else `PathSetStopDist(MonStats2 MeleeRng)` and `MonAiRunToUnitFlags(t, 1)`.
  A miss ends in `Idle(10)`, a hit in `MERCAI_PickSkill`. (0x005E5050–0x005E5260, fn:sub_005E5050_AiHireFight@0x005E5050)
- [I] **The skill list is the Hireling row's** (the plan's question). `MERCAI_PickSkill(ECX game, EDX U; class, id,
  target, seed)` takes `HIRELING_GetRecord(G+0x70, id, level)` with `id` the pet entry's `+8` word; with `δ = max(0,
  level − Level)`, it sums for each of `Skill1..6` (stopping at the first `< 1` or past the Skills count) that the unit
  holds at a level `> 0` (and, for a Skills `aitype` of 1, whose `aurastate` the unit is not in; for skill 41 `Inferno`
  only when the target's edge distance is at most `lvl/2 + 4`) the weight `Chance_k + (ChancePerLvl_k·δ)/4` (signed
  division, truncating) onto `DefaultChance`, keeping each running sum; then `r = draw mod (total + 1)` (a mask when
  `total + 1` is a power of two; no step when `total + 1 < 1`). `r < DefaultChance` falls back; else the first slot
  whose running sum is `≥ r`: an aura (Skills `+0x04` bit `0x20`) is set as the right skill
  (`PlayerSetSkill(U, 0, s, −1)`) and the unit idles 10, any other is used with `Mode_k` (`UseSkill(Mode_k, s, t, 0, 0)`).
  The fallback by class: 271 uses MonStats `Skill1` with `Sk1mode`; 338, 359, 560 and 561 attack (mode 4) in melee
  range; else `Idle(10)`. So MonStats `Skill1` is read only for the rogue's fallback (and by state 5); `act2hire`'s
  MonStats `Jab` is not read by any batch 6 function. (0x005E4D30–0x005E5040, fn:MERCAI_PickSkill@0x005E4D30,
  fn:HIRELING_GetRecord@0x006562F0, tbl:Hireling.txt:Chance1, tbl:Hireling.txt:ChancePerLvl1)
- [I] **States 5 and 6** (the unowned hireling; 5 also row 60): mode ≠ 1 → `Idle(5)`. Out of town, state 5 takes
  `FindHostile` within 20: `Range(100) < 30` → class 271 `UseSkill(Sk1mode, Skill1, t, 0, 0)`, any other class
  `SetModeAtUnit(4, t)`; else `Range(100) < 30` → `T56(t, 4, 0)`, else `Idle(10)`. State 6 takes `FindTarget`: one
  `Range(100)`; not in melee `< 30` → `Walk(t, 7)`; in melee `< 80` → `SetModeAtUnit(4, t)`; else `Idle(10)`. No target
  (or in town): `draw < 20` → `WanderRing(5)`, else `Idle(10)`. (fn:sub_005E7AC0_AiGoodNpcRanged@0x005E7AC0,
  fn:sub_005E7C10_AiHireUnowned@0x005E7C10)
- [C] **The decision maps of the seven functions** from their declared inputs to the first callee they reach (or the
  return) match the emulation in all 1 680 cases of 7 families: the callee, its call site, its register and stack
  arguments, the unit seed and `v14`/`v18`/`v1C`. Full maps: `MERCAI_PickSkill`'s class bounds, the fight step's class
  dispatch; states 5 and 6 up to `RoomIsTown`. Entry calls only: row 61 and its `alt`, the follow step. The `cmp`
  and site controls fail every case they separate. The `[C]` ends at that callee (ADR-0021).
  (run:2026-10-30-ai-cat-emu-6, § 4)
- [I] **Draws.** Every draw of the batch's functions is on the acting unit's seed: 5 multiplier-constant loads
  (`MERCAI_PickSkill` 1, the fight step 2, states 5 and 6 one each), 7 `RNG_Range` calls (the follow step 3, row 61 1,
  state 5 2, state 6 1) and 1 `RNG_RangePow2` call (row 61), each with `ECX` = `U + 0x20` (`b67-rngsites.txt` sites
  1–8: `lea ecx,[esi+0x20]` in the window, or a register set so at 0x005E7AF2 and 0x005E7C37); no `RNG_RangeB` or
  `RNG_RandLoHi` (`b67-draws.txt`); the fight step and `MERCAI_PickSkill` step the seed pointer passed by row 61, `U + 0x20`
  (`lea ecx,[esi+0x20]`, 0x005E55AD). Per event of row 61: at most `Pow2(128)`, the fight step's one or two draws and
  the pick's one, or `Range(100)` (the wander test), plus what the follow step's callees draw (its own `Range` calls,
  0x005E3ABC and 0x005E3C6D/0x005E3C7F, lie in kinds 1 and 2 behind a speed of 0 and kind 2, which row 61 never
  passes). (`b67-draws.txt`, § 3)

## Leads used

None. No community document was read; every claim is read from the code. P1.1 and batches 1–5 (ai/0001–0006) and
hirelings/0001 are cited by their anchors.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005E3930` | `sub_005E3930_AiHireFollow` | `(ECX game, EDX owner; unit, kind, run, speed, n)`: the hireling's move to its owner, kinds 0–5 | I (entry call `[C]`, § 4) |
| `0x005E4D30` | `MERCAI_PickSkill` | `(ECX game, EDX unit; class, id, target, seed)`: the Hireling row's weighted skill pick, the class fallback | I (class bounds `[C]`, § 4) |
| `0x005E5050` | `sub_005E5050_AiHireFight` | `(ECX game, EDX unit; class, owner, target, seed, ctx)`: the hit draw, the range test, then `MERCAI_PickSkill` | I (class dispatch `[C]`, § 4) |
| `0x005E5280` | `sub_005E5280_AiHireableAlt` | row 61's and state row 4's `alt` (also row 128's `+C`): clears state 12, `MonAiInit(ctl, ctl.state)`, `Idle(1)` | I (entry call `[C]`, § 4) |
| `0x005E52D0` | `sub_005E52D0_AiHireable` | row 61 `Hireable` and state row 4 think | I (entry call `[C]`, § 4); first boundary live `C`, ai/0015 |
| `0x005E7AC0` | `sub_005E7AC0_AiGoodNpcRanged` | state row 5 and table row 60 `GoodNpcRanged` think | I (map to `RoomIsTown` `[C]`, § 4) |
| `0x005E7C10` | `sub_005E7C10_AiHireUnowned` | state row 6 think | I (map to `RoomIsTown` `[C]`, § 4) |

## Walkthrough

### 1. The rows, their records and the skill lists

- [I] The rows (`b67-rows.txt`, `b67-tblrows.txt`): row 61 `Hireable` has five records, 271 `roguehire`, 338
  `act2hire`, 359 `act3hire`, 560 `act5hire1`, 561 `act5hire2`; `aidel` 1/1/1 on all; `aip1` 0 on 271 and 359, 1 on the
  other three, every other `aip` 0. MonStats skills: `roguehire` `Skill1` `RogueMissile` (`A1`), `act2hire` `Skill1`
  `Jab`; the other three none. Rows 61 and state 4 are `{0, 0, 0x005E52D0, 0x005E5280}`, state 5 `{0, 0, 0x005E7AC0,
  0}`, state 6 `{0, 0, 0x005E7C10, 0}`; row 60 is `{0, 0, 0x005E7AC0, 0}` and row 128 `{2, 0x005EE5C0, 0x005EE5D0,
  0x005E5280}` (values `[C]` as data). (tbl:MonStats.txt:AI, tbl:MonStats.txt:aip1, tbl:MonStats.txt:Skill1,
  data:g_MonAiTable@0x0073CA18, data:g_MonAiStateRows@0x0073D358)
- [I] **Which list.** The weighted pick reads only the Hireling row (`Skill_k`, `Chance_k`, `ChancePerLvl_k`, `Mode_k`,
  `DefaultChance`, § 2.4); MonStats `Skill1`/`Sk1mode` are read by `MERCAI_PickSkill`'s class-271 fallback (0x005E4FDC)
  and by state 5 for class 271 (0x005E7B4E); no batch 6 function reads MonStats `Skill2..8`, and `act2hire`'s `Jab`
  (its MonStats `Skill1`) is not read here (its fallback is a mode-4 attack). (fn:MERCAI_PickSkill@0x005E4D30,
  fn:sub_005E7AC0_AiGoodNpcRanged@0x005E7AC0, tbl:Hireling.txt:Skill1, tbl:MonStats.txt:Sk1mode)

### 2. The think functions

#### 2.1 Row 61 `Hireable` and state 4 (fn:sub_005E52D0_AiHireable@0x005E52D0)

```c
cls = U ? U->class : -1;
O = MonsterOwner(U);                                              // ECX U
if (!O || O->type != 0) { MonAiInit(ctl, cls == 271 ? 5 : 6); return Idle(10); }
if (UNIT_HasState(U, 12)) STATE_Set(U, 12, 0);                    // inferno
if (U->mode == 2 || U->mode == 15) return;                        // no command
AiParamsHead(U);                                                  // result not read
v = v14;
if (v > 16 && v < 20) { far = 2*v; near = v; n = v >> 1; } else { far = 24; near = 16; n = 5; }   // signed
e = Dist(U, O);                                                   // unsigned compares below
if (e > 100)  return Follow(O; U, 3, 0, 0, 0);
if (e > far)  return Follow(O; U, 1, 1, 60, 0);
if (e > near) { if (O->mode == 2 || O->mode == 6) return Follow(O; U, 0, 0, 0, 0);
                if (O->mode == 3) return Follow(O; U, 0, 1, 60, 0); }
if (U->mode != 1) { UNIT_CancelEvents(G, U, 2, 0); return Idle(5); }
ranged = !(cls == 338 || (cls > 559 && cls <= 561));
blocked = COLL_PatternTestBool(UnitGetRoom(U), subX(U), subY(U), UnitPathGet48(U), 0x40);
if (blocked && Pow2(128) < (ranged ? 12 : 6)) return WanderRing(5);                       // draw#1
if (!InTown(U) && (h = FindHostile(&e2, &m)) && e2 < 25)                                  // unsigned
    return HireFight(cls, O, h, &U->seed, ctx);
if (blocked) return WanderRing(5);
if (Region(O) != Region(U)) return Follow(O; U, 0, 1, 60, 0);
if (Dist(U, O) <= 1) { n -= 1;                                    // byte
    x, y = the owner's path point (0x00648A20/0x00648A30 on O->path);
    Ovr(7, 0, 0); if (WanderNear(O, n)) return;
    UNIT_CancelEvents(G, U, 2, 0); if (StepAway(O, n, 1)) return;
    Ovr(0, 0, 40); return WalkToPoint(x, y); }
if (Range(100) < 5) return WanderNear(O, near);                                          // draw#2
Idle(5);
```

- [I] The owner test reads `Unit+0x00` of the owner (`cmp [edi],0`, 0x005E5350): only a player owner (type 0) keeps
  row 61. The state change goes through `MonAiInit(ECX G, EDX U; ctl, state)` (0x005E5312, 0x005E5337, 0x005E536A,
  0x005E538F). (fn:sub_0058F0D0_MonsterOwner@0x0058F0D0, fn:sub_005B0E00_MonAiInit@0x005B0E00)
- [I] **The bands.** `cmp ecx,0x10; jle` and `cmp ecx,0x14; jge` (0x005E53F4–0x005E53FC) take 17, 18 and 19 to
  `2v`, `v`, `v >> 1` (`sar`), every other value to 24, 16, 5; the three distance compares are `jbe` (unsigned,
  0x005E5437, 0x005E5457, 0x005E5477), so a distance never compares below 0. The fight step writes `v14` as 0 or
  `v14 + 10` (§ 2.2), so from these functions' own writes `v14` is a multiple of 10 and the 17–19 arm needs another
  writer of `AiCtl+0x14` (open question). (0x005E53EE–0x005E5477)
- [I] **The owner's modes** read at `O+0x10` (player modes): 2 and 6 send kind 0 walking, 3 kind 0 with the run
  flag (`push 1`, 0x005E548C), any other mode falls through to the fight and idle part. (0x005E5479–0x005E54B0)
- [I] The crowding test runs before the town test and the search, so a hireling on a blocked cell can wander instead
  of fighting; `ranged` is 0 for 338, 560, 561 (`cmp eax,0x152; je`, `cmp eax,0x22F; jle`, `cmp eax,0x231; jle`,
  0x005E54EC–0x005E54FF) and its threshold `6` or `12` is compared signed with the `Pow2` result (`jge`, 0x005E5568).
  (fn:COLL_PatternTestBool@0x0064D910, fn:RNG_RangePow2@0x00472210)
- [I] The search is `MonAiFindHostile(&e2, &m)` (0x005E559A) with `e2 < 25` unsigned (`jae`, 0x005E55A7); the fight
  step gets `(class, O, h, U + 0x20, ctx)` (0x005E55A9–0x005E55BB). (fn:sub_005DDC30_MonAiFindHostile@0x005DDC30)

#### 2.2 The fight step (fn:sub_005E5050_AiHireFight@0x005E5050)

```c
c = (cls == 338 || (cls > 559 && cls <= 561)) ? 98
  : min(95, ctl->v14 + 40 + 2 * STATS_GetUnitStat(U, 12, 0));    // lea eax,[esi+eax*2]; cmp 0x5F; jl
e = Dist(U, t);
info = PETS_GetInfo(owner, U ? U->guid : -1);   if (!info) return Idle(10);
hit = step(seed) % 100 < c;                                        // draw#1 (signed jge)
if (hit) ctl->v14 = 0; else ctl->v14 += 10;
if (aip1 == 0) {                                                   // ranged
    if (e < 4 && step(seed) % 100 < 50) {                          // draw#2
        if (WanderNear(owner, 4)) return;
        UNIT_CancelEvents(G, U, 2, 0); if (StepAway(t, 4, 1)) return;
        return MERCAI_PickSkill(cls, info->w08, t, seed); }
    return hit ? MERCAI_PickSkill(cls, info->w08, t, seed) : Idle(10);
}
if (e < 3 && InMeleeRange(U, t, 0)) return hit ? MERCAI_PickSkill(cls, info->w08, t, seed) : Idle(10);
PathSetStopDist(U->path, ctx->pMonStats2->MeleeRng);  MonAiRunToUnitFlags(t, 1);
```

- [I] The level is stat 12 of the hireling (`push 0; push 0xC; push edi`, 0x005E508C–0x005E5094); the classes 338,
  560, 561 skip the stat read. The cap `95` and the `98` (0x005E509C–0x005E50AD) bound the hit chance; the draw is the
  low word of one step of `*seed` mod 100 (`0x51EB851F` and `shr 5`, 0x005E510D–0x005E511C), compared signed (`jge`).
  `aip1` is read at `M + 0x56 + 2d` (0x005E514A); the ranged back-off ends in the pick even after a miss when both
  back-off moves fail (`jmp 0x5E51D9`, 0x005E51CD). The melee approach reads MonStats2 `+0x0E` through `ctx+0x20`
  (0x005E523A–0x005E5246). (fn:STATS_GetUnitStat@0x00625480, fn:PETS_GetInfo@0x00574BD0,
  fn:sub_00622C40_InMeleeRange@0x00622C40, fn:sub_00649070_PathSetStopDist@0x00649070,
  fn:sub_005DED00_MonAiRunToUnitFlags@0x005DED00, tbl:MonStats2.txt:MeleeRng)

#### 2.3 The follow step (fn:sub_005E3930_AiHireFollow@0x005E3930)

- [I] `(ECX game, EDX owner; unit, kind, run, speed, n)` reads the owner's path point (0x00648A20/0x00648A30 on
  `O+0x2C`) and player data. Kind 0: from a start direction (`UnitDirToPoint` on the owner, reduced by `Dir64To8`) it tries
  up to eight directions in turn, each a point 8 subtiles from the owner's point in the owner's logic region, with `Ovr(0, speed, 40)` and
  `MonAiWalkToPointOrStop`; none works → `UNIT_CancelEvents(2, 0)` and `MonAiWanderRingDirect(owner, 4)`. Kind 1 with the
  owner in mode 2: `Ovr(0, 0, 100)` and a walk to the owner's point; in any other mode it walks back along the owner's
  20-entry trail (player data `+0xA0` the index, `+0xA8 + 8k` the points, newest first), skipping points within 5,
  with `Ovr(0, speed, 100)` and a walk, then `Ovr(15, speed, 100)` and a walk (a run with the run flag), then once per
  call `AiPathOverrideSet(speed, 100)` and the same move, and after 20 entries
  `MonAiWanderRingDirect(owner, max(4, Dist/4))`; a speed of 0 is replaced by `50 + Range(15)` (0x005E3ABC). Kind 3:
  a spawn position near the owner (`SpawnPosPick` with class 363 when the MonStats count exceeds 363, else −1),
  `UnitTeleport` there, `Unit+0xC8 |= 0x10000`, `Idle(5)`; it returns 0 on a failed pick, room or teleport. Kinds 2,
  4 and 5 (a ring walk on `Range(100) < 10` and `Range(3)`, a crowd count through the callback 0x005E3900, a wander
  near the owner) are not reached from row 61, whose five calls pass kinds 3, 1, 0, 0, 0 with speeds 0, 60, 60, 0, 60
  (0x005E5439–0x005E561C). (0x005E3930–0x005E3E9F, fn:sub_0054DC40_SpawnPosPick@0x0054DC40,
  fn:sub_00554EA0_UnitTeleport@0x00554EA0, fn:UNIT_GetPlayerData@0x006221A0)

#### 2.4 `MERCAI_PickSkill` (fn:MERCAI_PickSkill@0x005E4D30)

```c
if (cls < 0 || cls >= MonStatsCount || !(rec = MonStats + 0x1A8*cls)) return;
L = STATS_GetUnitStat(U, 12, 0);
h = HIRELING_GetRecord(G->w70, id, L);  if (!h) return;
dl = max(0, L - h->Level);  total = h->DefaultChance;
for (k = 0; k < 6; k++) {
    s = h->Skill[k];  if (s < 1 || s >= SkillsCount) break;
    sk = Skills + 0x23C*s;  cum[k] = 0;
    e = SkillFindByOwner(U, s, -1);
    if (!e || SKILLS_GetSkillLevel(U, e, 1) <= 0) continue;
    if (sk->aitype == 1 && sk->aurastate in [0, StatesCount) && UNIT_HasState(U, sk->aurastate)) continue;
    if (s == 41 && t && UnitEdgeDistance(U, t) > SKILLS_GetSkillLevel(U, e, 1) / 2 + 4) continue;
    total += h->Chance[k] + (h->ChancePerLvl[k] * dl) / 4;     // cdq; and edx,3; add; sar 2
    cum[k] = total;
}
r = (total + 1 < 1) ? 0 : ((total + 1) & total) == 0 ? step(seed) & total : step(seed) % (total + 1);   // draw#1
if (r >= h->DefaultChance) {
    for (k = 0; k < 6 && cum[k] < r; k++) ;                    // signed
    if (k < 6 && (s = h->Skill[k]) > 0) {
        if (Skills[s].flags04 & 0x20) { PlayerSetSkill(U, 0, s, -1); return Idle(10); }
        return UseSkill(h->Mode[k], s, t, 0, 0); } }
if (cls == 271) return UseSkill(rec->Sk1mode, rec->Skill1, t, 0, 0);
if ((cls == 338 || cls == 359 || cls == 560 || cls == 561) && InMeleeRange(U, t, 0)) return SetModeAtUnit(4, t);
Idle(10);
```

- [I] The record is looked up with `G+0x70` (the game's version word, hirelings/0001) and `id` the pet entry's `+8`
  (0x005E4D7F–0x005E4D8A, 0x005E50ED). The loop's `cum[k]` slots are stack words at `EBP − 0x34 + 4k`
  (0x005E4DF0, 0x005E4EA1); a skill that fails a test leaves 0, and the slots after the loop's break are not written.
  The `/4` is a signed division (`cdq; and edx,3; add edx,eax; sar edx,2`, 0x005E4E8A–0x005E4E93), a floor for `δ ≥ 0`.
  The draw's power-of-two test is `test esi,edx` with `esi = total + 1`, `edx = total` (0x005E4ED1–0x005E4ED6), the
  modulo an unsigned `div` (0x005E4EEC). The search compares `r` with each slot signed (`jle`/`jg`, 0x005E4F14,
  0x005E4F26). The aura bit is the byte at 0x006CE27C (`0x20`, `b67-tblrows.txt`) tested on Skills `+0x04`
  (0x005E4F55–0x005E4F5B; Skills `aura` is `+0x004` bit 5). The fallback dispatch is `cmp 0x167; jg; je`, `sub 0x10F; je`,
  `sub 0x43; je`, `cmp 0x230; jl`, `cmp 0x231; jg` (0x005E4FBF–0x005E5014); a class at or past the count becomes −1.
  (fn:sub_006439B0_SkillFindByOwner@0x006439B0, fn:SKILLS_GetSkillLevel@0x006442A0,
  fn:sub_006416D0_UnitEdgeDistance@0x006416D0, fn:sub_005701B0_PlayerSetSkill@0x005701B0, tbl:Skills.txt:aitype,
  tbl:Skills.txt:aurastate, tbl:Skills.txt:aura, tbl:Hireling.txt:DefaultChance, tbl:Hireling.txt:Mode1)
- [I] **When no weight was added** `total` = `DefaultChance` and only `r = DefaultChance` passes the first test; then
  every written slot is 0 `< r` and the search reads the slots after the break, which hold earlier stack contents, or
  (with six skills tested) reaches slot 6, the MonStats record pointer at `EBP − 0x1C`, and falls back. Which skill a
  stale slot selects is not read (open question). (0x005E4F0F–0x005E4F2B)

#### 2.5 The `alt` and states 5 and 6

```c
alt (0x005E5280):   if (UNIT_HasState(U, 12)) STATE_Set(U, 12, 0);  MonAiInit(ctl, ctl->state);  Idle(1);
state 5 (0x005E7AC0):
    if (!U || U->mode != 1) return Idle(5);
    if (!InTown(U) && (h = FindHostile(&e, &m)) && e < 20) {                  // signed jge
        if (Range(100) < 30) return U->class == 271 ? UseSkill(Sk1mode, Skill1, h, 0, 0) : SetModeAtUnit(4, h);
        if (Range(100) < 30) return T56(h, 4, 0);
        return Idle(10); }
    if (draw < 20) return WanderRing(5);  Idle(10);
state 6 (0x005E7C10):
    if (!U || U->mode != 1) return Idle(5);
    if (!InTown(U) && (h = FindTarget(ctl, &e, &m))) { r = Range(100);
        if (!m) return r < 30 ? Walk(h, 7) : Idle(10);
        return r < 80 ? SetModeAtUnit(4, h) : Idle(10); }
    if (draw < 20) return WanderRing(5);  Idle(10);
```

- [I] **The alt as a one-event bridge.** By `MonAiInit` (ai/0001 § 3), a call while `AiCtl.think` is the current row's
  think and that row has an `alt` sets the new state and installs the `alt`; the `alt` then calls `MonAiInit` with that
  state while `AiCtl.think` is the `alt`, so the full init runs (clearing `v14`/`v18`/`v1C`, the parameter records)
  and installs the state's think. Row 61's own `MonAiInit(ctl, 5 or 6)` calls (§ 2.1) are such calls. The `alt` reads
  `AiCtl+0x00` for the state (`mov edx,[ecx]`, 0x005E52AB). (0x005E5280–0x005E52C9,
  fn:sub_005B0E00_MonAiInit@0x005B0E00, fn:STATE_Set@0x00639DB0)
- [I] State 5 reads `M` from `ctx+0x1C` (0x005E7AD1) and is row 60's think too, so a `rogue2` (row 60's one record)
  runs the same code with class ≠ 271, hence `SetModeAtUnit(4, h)` in place of the skill. The `draw` steps are inline
  (0x005E7BB5, 0x005E7CCD); `RNG_Range` takes `ECX` = `U + 0x20` (`lea edi,[esi+0x20]` 0x005E7AF2, `lea
  ebx,[esi+0x20]` 0x005E7C37). (fn:sub_005DD7F0_MonAiFindTarget@0x005DD7F0, fn:sub_005DF7D0_MonAiWalkToUnitType56@0x005DF7D0)

### 3. Callers and the helpers

- [I] **Callers** (`b67-refs.txt`): the four entries have no code reference; row 61's think and `alt` are data words
  of `g_MonAiTable` (row 61 `+8`/`+C`) and `g_MonAiStateRows` (state 4 `+8`/`+C`), the `alt` also row 128's `+C`; state
  5's think is row 60's `+8` and state row 5's; state 6's state row 6's only. The follow step is called five times
  (0x005E5446, 0x005E5466, 0x005E5495, 0x005E54B0, 0x005E561C), the fight step once (0x005E55BB), `MERCAI_PickSkill`
  twice (0x005E51EA, 0x005E5229), all from this batch. The follow step's callback 0x005E3900 (`AiPetCrowdCb`, ai/0006)
  is pushed only from the follow step's kind 4 (0x005E3D8D) and from `AiPetMove` (0x005E44C4). `b67-refs.txt` scans
  `call`, `jmp`, `push` and `mov` immediates and raw dwords; a computed address is not scanned.
  (fn:sub_005E3900_AiPetCrowdCb@0x005E3900, fn:sub_005E3930_AiHireFollow@0x005E3930)
- [I] No function of the batch calls the action helpers 0x005DF850, 0x005DF990, 0x005DFA00 or 0x005DFBF0
  (`b67-draws.txt` `CALLEES` lines). (`b67-draws.txt`)

### 4. Emulation (run:2026-10-30-ai-cat-emu-6)

- [C] Seven families of this batch, 240 cases each, 1 680 cases, all matching, none stopped, no traced access outside
  the declared memory (`emu/check.txt`, the families `hire` … `follow`; the run's other eleven families are batch 7's,
  ai/0008 § 4; total 4 320 cases, `result=ok`). Each case runs one function on a declared image (the docstring of
  `tools/ai_cat_emu6.py`) and ends at the first observed callee or the return; the checker compares the callee, the
  call site, `ECX`/`EDX` where the callee takes them, the stack arguments, the unit seed and `v14`/`v18`/`v1C`.
  Controls: `le` (each draw with `<=`), `d0` (every `aip` from the Normal column), `cmp` (each non-draw compare with its
  strictness switched) fail every case they separate, and the site control (each call site one byte later) fails
  every case that ends at a callee (run:2026-10-30-ai-cat-emu-6):

  | family | function | outcomes (site: cases) | drew | `le` | `d0` | `cmp` | compares met at equality (`EDGES`) |
  |---|---|---|---:|---:|---:|---:|---|
  | `hire` | row 61, st 4 | `MonsterOwner` 0x005E52F7: 240 | 0 | 0 | 0 | 0 | — |
  | `hirealt` | alt | `UNIT_HasState` 0x005E529A: 240 | 0 | 0 | 0 | 0 | — |
  | `st5` | st 5, row 60 | `Idle` 0x005E7AE8: 132, `RoomIsTown` 0x005E7B00: 108 | 0 | 0 | 0 | 0 | — |
  | `st6` | st 6 | `Idle` 0x005E7C2D: 133, `RoomIsTown` 0x005E7C45: 107 | 0 | 0 | 0 | 0 | — |
  | `pick` | `MERCAI_PickSkill` | `STATS_GetUnitStat` 0x005E4D7F: 197, return: 43 | 0 | 0 | 0 | 25 | `cls<0` 17, `cls<count` 8 |
  | `fight` | fight step | `AiDistUnits` 0x005E50BE: 41, `STATS_GetUnitStat` 0x005E5099: 199 | 0 | 0 | 0 | 31 | `cls<=559` 18, `cls<=561` 13 |
  | `follow` | follow step | `UNIT_GetPlayerData` 0x005E3952: 240 | 0 | 0 | 0 | 0 | — |

  The `le` … `cmp` columns count the cases each control separates (it passed none); `site_control_passed=0` in every
  family. **Edges with no control:** the `==`/`!=` and null tests (the mode `== 1` test of states 5 and 6, the fight
  step's `== 338`, the pick's null record), whose wrong reading gives another site on the cases that hold the other
  value but whose edge no control moves; the sign test `cls < 0` is met at equality (`cls<0` 17, the value 0), so it has
  a strictness control. The entry families take no draw and no compare before their call: no control separates them,
  and their `[C]` is the call's site and arguments. Not covered: every callee and everything after it, so the bands,
  the draws and the skill pick (§ 2) stay `[I]`. (run:2026-10-30-ai-cat-emu-6)
- [I] **The development run** (rule 6): `emu/dev-1/` (the same 4 320 cases, all matching, every control failing every
  case it separates), checked by its own copy of the tool (`dev-1/ai_cat_emu6.py.rev`, sha256 `866f330d…`, the same
  bytes as `tools/ai_cat_emu6.py` at the kept run). The kept run regenerated the case and memory files (identical to
  dev-1's), ran the 18 `emuboundary` calls into `emu/` and wrote its own `check.txt` and `manifest.sha256` (73 lines);
  no kept output was written over a development one. (run:2026-10-30-ai-cat-emu-6)
- [I] Not emulated past their entry call: row 61 and its `alt` (a guid lookup in `MonsterOwner`, `UNIT_HasState`'s
  state list), the follow step (`UNIT_GetPlayerData`); Phase 2's logs reproduce row 61, the batch's tier AI.
  (fn:sub_0058F0D0_MonsterOwner@0x0058F0D0)

## Data touched

- tbl:MonStats.txt:AI (`+0x1E`), tbl:MonStats.txt:aip1 (`+0x56 + 2d`), tbl:MonStats.txt:Skill1 (`+0x170`),
  tbl:MonStats.txt:Sk1mode (`+0x180`), tbl:MonStats2.txt:MeleeRng (`+0x0E`), the MonStats, Skills and States counts
  (`g_pDataTables+0xA80`, `+0xBA0`, `+0xC4`) and the MonStats and Skills records (`+0xA78`, `+0xB98`).
- tbl:Hireling.txt:Level (`+0x01C`), tbl:Hireling.txt:DefaultChance (`+0x064`), tbl:Hireling.txt:Skill1 …
  Skill6 (`+0x078 + 4k`), tbl:Hireling.txt:Chance1 … Chance6 (`+0x090 + 4k`), tbl:Hireling.txt:ChancePerLvl1 …
  ChancePerLvl6 (`+0x0A8 + 4k`), tbl:Hireling.txt:Mode1 … Mode6 (`+0x0C0 + k`).
- tbl:Skills.txt:aura (`+0x004` bit 5), tbl:Skills.txt:aurastate (`+0x080`), tbl:Skills.txt:aitype (`+0x230`).
- struct:AiCtl+0x00, struct:AiCtl+0x14, struct:AiCtx+0x08, struct:AiCtx+0x18, struct:AiCtx+0x1C, struct:AiCtx+0x20,
  struct:Unit+0x00, struct:Unit+0x04, struct:Unit+0x0C, struct:Unit+0x10, struct:Unit+0x20, struct:Unit+0x2C,
  struct:Unit+0xC8, struct:Game+0x6D, struct:Game+0x70; player data `+0xA0`, `+0xA8` (the owner's trail).

## Dead ends

- Ghidra's decompile of the follow step and of the fight step drops their register arguments (`FUN_005e3930(unit, 3,
  …)` without the owner) and of `MonAiInit` in row 61's think (`(*ctx, 6)` only); objdump gives `EDX` = the owner
  (0x005E5442) and `ECX`/`EDX` = game and unit (0x005E530E–0x005E5312).

## Open questions

- Who else writes the hireling's `AiCtl+0x14`: from the fight step's writes (`0`, `+10`) it is a multiple of 10, so
  row 61's 17–19 band arm needs another writer (a scan of `[reg+0x14]` stores through an `AiCtl` pointer, or a Phase 2
  log of `v14` on a hireling).
- `MERCAI_PickSkill` with no weight added and `r = DefaultChance` reads stack slots the loop did not write (§ 2.4):
  whether any stock row reaches it (a Hireling row whose every skill is missing or blocked by its state) and what the
  stale words hold, by a Phase 2 log or an emulation of the whole pick with a declared stack.
- The follow step's kinds 2, 4 and 5 have no caller in row 61; whether another function reaches 0x005E3930 by a
  computed address is not scanned (`b67-refs.txt` finds five direct calls only).
