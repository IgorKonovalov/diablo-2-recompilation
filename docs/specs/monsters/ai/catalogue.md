---
spec: monsters/ai/catalogue
status: draft
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, monsters/ai/overview, monsters/ai/machinery, skills/dispatch, path/overview]
consumed_by: [monsters/ai/overview, monsters/ai/machinery, hirelings]
tags: {C: 222, I: 283, L: 7}
updated: 2026-11-04
---

# Monster AI: the catalogue, one entry per AI row

## Purpose

What the think function of each AI row does on an AI event: which `aip` slots it reads and what each means, its decision
tree, its draws in order. There are 148 rows in `g_MonAiTable` and 18 in `g_MonAiStateRows`, and each has one entry here
(`R<row>` and `S<state>`), grouped by the batches of [plan 0052](../../../plans/0052-monster-ai.md). The event around the
think, its seeds and the row kinds are [the overview](README.md); the helpers and the 18 tier AIs are
[machinery](machinery.md), and a tier row's entry here is one link to its § T entry.

## Entry points

| When | Function | Tag |
|---|---|---|
| An AI event reaches the think call | fn:sub_005B1740_MonAiEvent@0x005B1740, its call at 0x005B186F | [I] |
| A row's `init` and `alt` | fn:sub_005B0E00_MonAiInit@0x005B0E00 | [I] |

## Inputs

### Tables

| Anchor | Used for |
|---|---|
| tbl:MonStats.txt:AI | a class's row |
| tbl:MonStats.txt:aip1 | `aip1..8`, per difficulty; what each slot means is per row, below |
| tbl:MonStats.txt:Skill1, tbl:MonStats.txt:Sk1mode | the skills and modes a think uses |

### Runtime state

| State | Type | Source |
|---|---|---|
| the think's context | `AiCtx`: `t`, `dist`, `melee` | [README D3](README.md#d-the-ai-table-and-its-dispatch) |
| the AI control | `AiCtl`: `v14`, `v18`, `v1C`, the parameter list | [README § E](README.md#e-the-ai-state-on-the-unit), [machinery § E](machinery.md#e-following) |
| the unit's seed | `U+0x20/+0x24`, every `draw#k` below unless the entry says otherwise | [machinery § F](machinery.md#f-draws-and-seeds-of-the-helpers) |

### Constants

Each entry states its own. No constant is shared across entries.

### Notation

[Machinery § Notation](machinery.md#notation) applies throughout: `U`, `G`, `T`, `d`, `t`, `dist`, `melee`, `v14`, `v18`,
`v1C`, `aip(K)`, `D100()`, `chance(K)`, `Range(n)`, `draw#k` and the helpers named there, and the mode numbers. Added here, [I]
(fn:sub_005DD280_AiLifePct@0x005DD280, fn:sub_00621F20_UnitLifePct@0x00621F20, fn:sub_005DD2B0_AiMonState3or19@0x005DD2B0, fn:sub_0058EF40_AiParamsPush@0x0058EF40):

| Write | Means |
|---|---|
| `LifePct`, `UnitLifePct` | `AiLifePct` (0x005DD280) and `UnitLifePct` (0x00621F20), two different readers; each entry names the one its code calls |
| `rchance(K)` | `Range(100) < aip(K)`, one draw, the same test as `chance(K)` by another helper call |
| `St3or19` | `AiMonState3or19(U)`: `MonsterData+0x54` is 3 or 19 |
| `Head`, `Pop`, `Push(blk)` | `AiParamsHead`, `AiParamsPop`, `AiParamsPush` on `U`'s parameter list ([machinery E4](machinery.md#e-following)) |
| `UseSkillK(x)` | `MonAiUseSkill(SkKmode, SkillK, x, 0, 0)`: the record's K-th skill in its K-th mode |
| `DelayE(n)` | `MonAiDelayEarlier(n)` ([README C4](README.md#c-when-the-next-ai-event-comes)) |
| `State(n, v)` | `STATE_Set(U, n, v)` |

### How to read an entry

- [I] **`aip` meanings** are read from each think's code unless the entry says "table doc". A community source's meaning is not
  evidence and is not given above Open questions. The block is the code reading of the named finding: where it reads a
  word, the row reads that word for every record of the row, and a slot a record leaves at 0 is read as 0. (tbl:MonStats.txt:aip1)
- [I] **The row's `i` line** is the table's bytes and the MonAI index, data. **The `l` line** is the row's own logged count at the
  first boundary: the sum over the three kept batches of the `ROW` lines of each batch's check file, in order
  run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, and [README § G](README.md#g-the-first-boundary) says what the comparison is. A count
  that is `[C]` covers the first callee, its site, its words and its seed, and nothing past that call. (0x005B186F)
- [I] **The `r` line** is the resumed comparison over the rev 4 and rev 6 logs for the row's own think (other thinks of its classes,
  the state rows, are counted under the state's entry). It is a consistency check. **No entry outside machinery's table is under sentence
  H1**: nothing past the first boundary of any row here is `[C]`. No row's role, symbol or reading is raised by being resumed. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)
- [I] **The catalogue sample is short, by name:** batches 5, 7, 10, 11, 12 have no row that counts. Row 54 cannot fail (0 of 3 sites), row 99 has no call past the first, row 32 has a fork in all 199 decisions of the rev 4 logs, row 100 has 4 decisions. Row 130's map has not landed.
  (run:2026-11-04-ai-resume-flip)
- [C] **Emulated maps** are named per entry. Each runs the think on a declared image up to its first observed callee (ADR-0015, ADR-0021) and covers that code's map and no callee, and no store or command after it. (run:2026-10-30-ai-cat-emu-1)

## Algorithm

### Batch 0: the machinery rows

#### R0. Row 0 `None` (fn:sub_005B0CC0_AiNone@0x005B0CC0)

```
ret 4                                                                       [I] (fn:sub_005B0CC0_AiNone@0x005B0CC0)
```

Stub: no behaviour of its own; no MonStats record names it, and a class whose `AI` is outside 0..147 gets it ([README D1](README.md#d-the-ai-table-and-its-dispatch)).

- R0i. [C] As data: kind 0, no `init`, no `alt`; 0 records (—); reach none; `aip` set —; `aidel` —; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R0l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R1. Row 1 `Idle` (fn:sub_005B0CD0_AiIdle@0x005B0CD0)

```
if U has a room: Idle(200)                                                  [I] (fn:sub_005B0CD0_AiIdle@0x005B0CD0)
```

No draw; no `aip` read by this think, although records set slot 1 ([README D2](README.md#d-the-ai-table-and-its-dispatch)).

- R1i. [C] As data: kind 0, no `init`, no `alt`; 61 records (61 records, as the index lists them); reach S; `aip` set 1; `aidel` 0,15/0,14,15/0,13,15; skills Jab, Baal Taunt. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R1l. [I] Logged, not compared: 104 decisions (100 + 4) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R1r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 4 of its own think's decisions in the rev 4 and rev 6 logs, 4 resumed, 0 mismatches, 0 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### S0. State row 0 (zero row)

Zero row: the state word 0 selects the class's row instead ([README D1](README.md#d-the-ai-table-and-its-dispatch)). No think here. [I] (fn:sub_005B15D0_MonAiEntryGet@0x005B15D0)

- S0i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S1. State row 1 (fn:sub_005B0CD0_AiIdle@0x005B0CD0)

Alias of [row 1](#r1-row-1-idle-fnsub_005b0cd0_aiidle0x005b0cd0): the same think word. [I] (data:g_MonAiStateRows@0x0073D358, fn:sub_005B0CD0_AiIdle@0x005B0CD0)

- S1i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

### Batch 1: pool-A (acts I and II)

#### R2. Row 2 `Skeleton` (fn:sub_005EFCF0_AiSkeleton@0x005EFCF0)

Tier AI: [machinery § T2](machinery.md#t2-row-2-skeleton-fnsub_005efcf0_aiskeleton0x005efcf0), not repeated here.

#### R3. Row 3 `Zombie` (fn:sub_005EFE20_AiZombie@0x005EFE20)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | chance to run at the target once nearer than `aip(2)` |
| `aip(2)` | the distance below which that draw is made |
| `aip(4)` | A1 against A2 in melee range |

```
1. if melee: SetModeAtUnit(chance(4) ? 4 : 5, t); return     ; draw#1      [I] (0x005EFE20, 0x005EFF47)
2. if not St3or19:
     if not (dist < aip(2) and chance(1)):                   ; draw#1, only when dist < aip(2)
       if RoomGetLevelId(UnitGetRoom(U)) ≠ 17: Ring(3); return
3. Ovr(0, 100, 0);  RunToUnit(t)
```

- R3a. [I] So a zombie runs at its target (override parameter 100) when `MonsterData+0x54` is 3 or 19, when it is nearer than `aip(2)` and draws below `aip(1)`, or anywhere in level 17 (Levels `Id` 17); otherwise it wanders to a ring point of radius 3. (fn:sub_0061A1B0_RoomGetLevelId@0x0061A1B0, tbl:Levels.txt:Id, fn:sub_005DED20_MonAiRunToUnit@0x005DED20)
- R3b. [C] The map to its first callee, family `zombie`, 240 cases, 4 boundaries; the `≤` and Normal-column controls fail the 26 and 50 that separate them. It ends at `UnitGetRoom` on the level branch; the level test is a reading. (run:2026-10-30-ai-cat-emu-1)

- R3i. [C] As data: kind 1, no `init`, no `alt`; 5 records (5-9 zombie1..zombie5); reach PU; `aip` set 1,2,4; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R3l. [C] First boundary: 352 decisions compared (216 + 136), 0 mismatches, 4 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R3r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 136 of its own think's decisions in the rev 4 and rev 6 logs, 136 resumed, 0 mismatches, 0 stopped, 381 later calls matched, an unknown value deciding 0 of 381 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### R4. Row 4 `Bighead` (fn:sub_005EFF50_AiBighead@0x005EFF50)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | life percent at or above which it fights, below which it keeps away |
| `aip(2)` | keeping away: chance of a `T56` walk against an `Idle(10)` |
| `aip(3)` | fighting: chance of A2 at a target within 15 with a hostile found |
| `aip(4)` | keeping away: chance of A2 with a hostile found |

```
1. if not melee and St3or19: SetModeAtUnit(5, t); return                   [I] (0x005EFF50, 0x005F00CC)
2. life ← LifePct(U)
3. if life ≥ aip(1):
     if melee: SetModeAtUnit(4, t); return
     if dist < 15 and FindHostile(&dist, &m) and Range(100) < aip(3):      ; draw#1
       SetModeAtUnit(5, t); return
     Walk(t, 7); return
4. if dist < 3:
     Ovr(0, 50, 0)
     if not StepAway(t, 5, 1): SetModeAtUnit(5, t)
     return
5. if dist > 15: WalkStop(t, 6); return
6. if FindHostile(&dist, &m) and Range(100) < aip(4):                      ; draw#1
     SetModeAtUnit(5, t); return
7. if Range(100) < aip(2): T56(t, 3, 0)                                    ; draw#1, or #2 after step 6's
   else: Idle(10)
```

- R4a. [I] The A2 command is aimed at `t` even when the hostile `FindHostile` (search kind 6) found is another unit. The `dist` tests after a `FindHostile` read the distance from `ctx`, taken before the call. Below `aip(1)` percent life the bighead keeps 3–15 from its target. (fn:sub_005DDC30_MonAiFindHostile@0x005DDC30, fn:sub_005DD280_AiLifePct@0x005DD280)
- R4b. [C] The map up to `AiLifePct` or the `MonsterData+0x54` shortcut only: family `bighead`, 240 cases, two boundaries, no draw before them and no `aip` read, so no draw control separates it. (run:2026-10-30-ai-cat-emu-1)

- R4i. [C] As data: kind 1, no `init`, no `alt`; 10 records (10-14 bighead1..bighead5, 580-584 bighead6..bighead10); reach PU; `aip` set 1,2,3,4; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R4l. [C] First boundary: 913 decisions compared (560 + 342 + 11), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R4r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 353 of its own think's decisions in the rev 4 and rev 6 logs, 353 resumed, 0 mismatches, 0 stopped, 740 later calls matched, an unknown value deciding 0 of 740 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R5. Row 5 `BloodHawk` (fn:sub_005F00E0_AiBloodHawk@0x005F00E0)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | out of melee range: chance of the swoop |
| `aip(2)` | farther than 3: chance of the ring-4 retreat with override −50, else ring 3 with override 0 |
| `aip(3)` | in melee range: chance of A1 |
| `aip(4)` | the override parameter of the step away |
| `aip(5)` | the swoop's override parameter (100 in every record, as data) |

```
1. if v14 = 1 and melee: v14 ← 0;  SetModeAtUnit(4, t); return             [I] (0x005F00E0, 0x005F02AB)
2. v14 ← 0
3. if not melee:
     if chance(1):                         ; draw#1
       Ovr(0, aip(5), dist);  v14 ← 1;  Walk(t, 0); return
     if dist > 3:
       if chance(2):                       ; draw#2
         Ovr(0, −50, 0);  Ring(4); return
       Ovr(0, 0, 0);  Ring(3); return
   else if chance(3):                      ; draw#1
     SetModeAtUnit(4, t); return
4. Ovr(0, aip(4), 0)
   if not StepAway(t, 4, 1): SetModeAtUnit(4, t)
```

- R5a. [I] `v14` is the swoop flag: set after an approach walk with override parameter `aip(5)` and the override byte `dist` (capped at 77 by `MonAiPathOverride`); the next event in melee range attacks at once. (struct:AiCtl+0x14, fn:sub_005DE190_MonAiPathOverride@0x005DE190)
- R5b. [C] The map, `AiCtl+0x14` at the boundary included: family `bloodhawk`, 240 cases, 6 boundaries; the controls fail the 34 and 106 that separate them. (run:2026-10-30-ai-cat-emu-1)

- R5i. [C] As data: kind 1, no `init`, no `alt`; 8 records (15-18 foulcrow1..foulcrow4, 590-593 foulcrow5..foulcrow8); reach P; `aip` set 1,2,3,4,5; `aidel` 15/14,15/13,15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R5l. [C] First boundary: 399 decisions compared (128 + 271), 0 mismatches, 5 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F) 1 not comparable (the log's window).
- R5r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 272 of its own think's decisions in the rev 4 and rev 6 logs, 271 resumed, 0 mismatches, 1 stopped, 251 later calls matched, an unknown value deciding 0 of 251 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### R6. Row 6 `Fallen` (fn:sub_005F02C0_AiFallen@0x005F02C0)

Tier AI: [machinery § T6](machinery.md#t6-row-6-fallen-fnsub_005f02c0_aifallen0x005f02c0), not repeated here.

#### R7. Row 7 `Brute` (fn:sub_005EFB80_AiBrute@0x005EFB80)

| Slot | Meaning (code reading) |
|---|---|
| `aip(3)` | in melee range: chance to attack; on a miss, a second draw on the same slot for a `T56` walk |
| `aip(4)` | A1 against A2 |

```
1. if not melee:                                                           [I] (0x005EFB80, 0x005EFCE1)
     p ← clamp(UnitLifePct(U), 40, 100)
     Ovr(0, 100 − p, 0);  Walk13(t, 7); return
2. if chance(3):                                ; draw#1
     SetModeAtUnit(chance(4) ? 4 : 5, t); return ; draw#2
3. if chance(3): T56(t, 4, 0); return           ; draw#2, aip(3) again
4. Idle(15)
```

- R7a. [I] Out of melee range the override parameter is `100 − life%` with life clamped to 40..100: 0 at full life, 60 at 40 % and below. (fn:sub_00621F20_UnitLifePct@0x00621F20)
- R7b. [C] The melee map; out of melee range up to `UnitLifePct`: family `brute`, 240 cases, 5 boundaries; the controls fail the 29 and 37 that separate them. (run:2026-10-30-ai-cat-emu-1)

- R7i. [C] As data: kind 1, no `init`, no `alt`; 9 records (24-28 brute2..brute1, 446-449 snowyeti1..snowyeti4); reach PU; `aip` set 3,4; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R7l. [C] First boundary: 37 decisions compared (23 + 8 + 6), 0 mismatches, 5 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R7r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 14 of its own think's decisions in the rev 4 and rev 6 logs, 14 resumed, 0 mismatches, 0 stopped, 18 later calls matched, an unknown value deciding 0 of 18 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R8. Row 8 `SandRaider` (fn:sub_005F0700_AiSandRaider@0x005F0700)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | life percent below which it looks for an ally |
| `aip(2)` | farther than 4 and unarmed: chance of a `T56` walk |
| `aip(3)` | in melee range: chance of an attack |
| `aip(4)` | out of melee range, unarmed: chance to walk at `t` |
| `aip(5)` | the event count at which it arms |
| `aip(6)` | 1: state 90 and overlay 150; otherwise state 91 and overlay 46 (`sandraider2`, 4, 7, 9 have 1, the six others 0, as data) |
| `aip(7)` | A1 when `Range(100) ≥ aip(7)`, else A2 (50 in every record, as data), inverted against the other rows |

```
1. if v14 = 0: State(90, 0);  State(91, 0);  v18 ← 0                       [I] (0x005F0700, 0x005F0A17)
2. v14 ← v14 + 1;  n: i32 ← v14
3. if n = aip(5):
     UnitSetOverlayStat(U, aip(6) = 1 ? 150 : 46, 0);  Idle(aidel[d] + 1); return
4. if n > aip(5):
     State(aip(6) = 1 ? 90 : 91, 1);  v18 ← 1                  ; armed
5. if v1C < 7 and LifePct(U) < aip(1):
     best ← {0, 0x7FFFFFFF};  AiUnitSearch(G, U, &best, AiNearAllyCb, 1)
     if best.unit: Walk(best.unit, 0); return
     v1C ← v1C + 1
6. if dist > 4 and v18 = 0 and chance(2):                      ; draw#1
     T56(t, 0, 0); return
7. if not melee:
     if v18 ≠ 0 or chance(4): Walk(t, 0); return               ; draw#1 or #2, none when armed
     goto wait
8. if v18 = 1 and Skill1 ≥ 0:
     UseSkill1(t);  v14 ← 0;  v18 ← 0; return                  ; Fire Hit
9. if chance(3):
     SetModeAtUnit(Range(100) ≥ aip(7) ? 4 : 5, t); return
wait:
10. k ← max(24 − aip(5), 6)
    if v14 > aip(5) + k: v14 ← 0;  v18 ← 0
11. Idle(15)
```

- R8a. [I] `v14` counts the raider's AI events since its last Fire Hit; at `aip(5)` (18 … 4 by record and difficulty, as data) it shows an overlay and waits `aidel[d] + 1` frames, past it it holds the state and is armed: the next event in melee range uses `Skill1` and starts the count again. (tbl:MonStats.txt:Skill1, tbl:MonStats.txt:Sk1mode, tbl:MonStats.txt:aidel)
- R8b. [I] **The ally.** Below `aip(1)` percent life, up to 7 tries counted in `v1C`, which this function never resets, it walks to the nearest other monster of alignment 0 that is not in a death mode, by squared distance. `AiNearAllyCb`: candidate ≠ searcher, type 1, `UnitAlignGet` 0, `MonIsDeathMode` 0, `UnitDistSq` below the best; search kind 1 walks the near rooms' unit lists. No draw in the walk. `UnitDistSq` is `dx² + dy²`, 32-bit signed, and its wrap is out of reach on stock maps. (fn:sub_005F06B0_AiNearAllyCb@0x005F06B0, fn:sub_005B0BD0_UnitDistSq@0x005B0BD0, fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0)
- R8c. [I] The overlay is `UnitSetOverlayStat(unit, overlay, 0)`; the two values are rows 150 and 46 of Overlay.txt by row index, not followed further. (fn:sub_00621E40_UnitSetOverlayStat@0x00621E40)
- R8d. [I] Not emulated: the unit search lies before its draws. (0x005F0700, [ai/0002 § 3](../../../findings/ai/0002-pool-a.md#3-emulation-run2026-10-30-ai-cat-emu-1))

- R8i. [C] As data: kind 1, no `init`, no `alt`; 10 records (29-33 sandraider1..sandraider5, 599-603 sandraider6..sandraider10); reach PU; `aip` set 1,2,3,4,5,6,7; `aidel` 15/9,14/7,13; skills Fire Hit. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R8l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R9. Row 9 `Wraith` (fn:sub_005F0A20_AiWraith@0x005F0A20)

Tier AI: [machinery § T9](machinery.md#t9-row-9-wraith-fnsub_005f0a20_aiwraith0x005f0a20), not repeated here.

#### R10. Row 10 `CorruptRogue` (fn:sub_005F0B00_AiCorruptRogue@0x005F0B00)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | out of melee range, near: chance to approach at all, else `Idle(aip(2))` |
| `aip(2)` | the idle wait |
| `aip(3)` | in melee range: chance of A1 |
| `aip(4)` | the run's override parameter (100 in every record, as data) |
| `aip(5)` | near: chance of the run against a walk |

```
1. MonPlayerBonus(G, &pb, UnitGetRoom(U), U)                  ; for pb.difficulty, min(d, 2)   [I] (0x005F0B00, 0x005F0CB8)
2. if dist > 20 − 3·pb.difficulty:
     Ovr(13, aip(4), 0);  RunStop(t, 3); return
3. if melee:
     if chance(3): SetModeAtUnit(4, t); return                ; draw#1
     Idle(aip(2)); return
4. if not chance(1): Idle(aip(2)); return                     ; draw#1
5. if chance(5):                                              ; draw#2
     Ovr(13, aip(4), 0);  RunStop(t, 3); return
6. Walk(t, 7)
```

- R10a. [I] Beyond 20, 17 or 14 (Normal, Nightmare, Hell) the rogue runs in mode 15, type 13, stop distance 3. `MonPlayerBonus` is called for its difficulty word only (`[ebp−0x18]` at 0x005F0B37). `corruptrogue3`'s `CountessFirewall` is not used by this function. (fn:sub_00573930_MonPlayerBonus@0x00573930, fn:sub_005DEFB0_MonAiRunToUnitStop@0x005DEFB0)
- R10b. [I] Not emulated: `MonPlayerBonus` and the room lie before its first draw. (0x005F0B00, [ai/0002 § 3](../../../findings/ai/0002-pool-a.md#3-emulation-run2026-10-30-ai-cat-emu-1))

- R10i. [C] As data: kind 1, no `init`, no `alt`; 6 records (43-47 corruptrogue1..corruptrogue5, 721 corruptrogue6); reach PU; `aip` set 1,2,3,4,5; `aidel` 15/14/13; skills CountessFirewall. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R10l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R11. Row 11 `Baboon` (fn:sub_005F0CD0_AiBaboon@0x005F0CD0)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | life percent below which it may flee, only when `St3or19` |
| `aip(2)` | after an attack, on a failed `aip(3)` draw: chance of a `T56` walk |
| `aip(3)` | after an attack: chance to attack again |
| `aip(4)` | A1 against A2 (`baboon1` has 0, the others 15–50, as data, so `baboon1` draws A2) |
| `aip(5)` | the factor of the regeneration raise while fleeing |

```
1. life ← UnitLifePct(U)                                                   [I] (0x005F0CD0, 0x005F112E)
2. bonus: i32 ← 0
   if Velocity ≥ 1:
     q ← Run·100 ÷ Velocity             ; MonStats +0x32, +0x34, signed
     if q ≥ 100: bonus ← min(q − 100, 120)
3. if v14 = 0:
     if not melee: Walk13(t, 7); return
     if St3or19:
       if life < aip(1) and Range(100) < 50:                  ; draw#1
         v14 ← Range(5) + 2                                   ; draw#2: 2..6 events of flight
         s ← STATS_GetUnitStat(U, 74, 0)
         v1C ← s ≠ 0 ? (aip(5)·s) ÷ 8 : 0
         if s ≠ 0: UnitSetStat(U, 74, s + v1C, 0)
         Ovr(2, bonus, 0);  StepAway(t, 15, 0); return
       if v18 ≠ 0 and Range(100) < 20:
         T56(t, 3, 0);  v18 ← 0; return
     if v18 ≠ 0 and not chance(3):
       if Range(100) < aip(2): T56(t, 3, 0);  v18 ← 0
       Idle(15); return
     v18 ← 1;  SetModeAtUnit(chance(4) ? 4 : 5, t); return
4. v14 ← v14 − 1;  v18 ← 0                                    ; in flight
5. if v14 = 0 or life > 75: UnitSetStat(U, 74, STATS_GetUnitStat(U, 74, 0) − v1C, 0)
6. if not melee:
     if life > 75:
       v14 ← 0;  Ovr(13, bonus, 0);  Walk13(t, 7); return
   else if D100() < 33:
     SetModeAtUnit(chance(4) ? 4 : 5, t); return
7. if dist > 23 and not St3or19:
     if Range(100) < 33: T56(t, 4, 0)
     Idle(20); return
8. Ovr(2, bonus, 0)
   if not StepAway(t, 15, 1):
     if not melee: Ring(5); return
     SetModeAtUnit(Range(100) < aip(4) ? 4 : 5, t)
```

- R11a. [I] **The flight:** stat 74 (`hpregen`) is raised by `aip(5)·s ÷ 8`, a signed 32-bit product divided toward zero (`(x + (x >> 31 & 7)) >> 3`), and taken back when the count ends or life passes 75 %. The product wraps only for `|s| > 715 827 882` with the stock `aip(5)` ≤ 3. The bonus is `Run·100 ÷ Velocity − 100`, 0..120, and 0 for a `Velocity` below 1 or `Run < Velocity`. `v18` marks "attacked last time". (tbl:MonStats.txt:Velocity, tbl:MonStats.txt:Run, fn:STATS_GetUnitStat@0x00625480, fn:sub_00627260_UnitSetStat@0x00627260)
- R11b. [I] Not emulated: `UnitLifePct` comes first. (0x005F0CD0, [ai/0002 § 3](../../../findings/ai/0002-pool-a.md#3-emulation-run2026-10-30-ai-cat-emu-1))

- R11i. [C] As data: kind 1, no `init`, no `alt`; 8 records (48-52 baboon1..baboon5, 295 baboon6, 665-666 baboon7..baboon8); reach P; `aip` set 1,2,3,4,5; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R11l. [I] Logged, not compared: 17 decisions (17) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, 0x005B186F)

#### R12. Row 12 `Goatman` (fn:sub_005F12A0_AiGoatman@0x005F12A0)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | out of melee range: chance to walk at `t` |
| `aip(2)` | the idle wait |
| `aip(3)` | in melee range: chance of A1 |

```
1. if not melee:                                                           [I] (0x005F12A0, 0x005F1368)
     if chance(1): Walk(t, 7); return    ; draw#1
   else if chance(3):                    ; draw#1
     SetModeAtUnit(4, t); return         ; A1 only
2. Idle(aip(2))
```

- R12a. [I] Row 2's shape with no A2 draw, and its own code: `aip(4)` is not read. (fn:sub_005F12A0_AiGoatman@0x005F12A0)
- R12b. [C] The map, family `goatman`, 240 cases, 3 boundaries; the controls fail the 40 and 138 that separate them. (run:2026-10-30-ai-cat-emu-1)

- R12i. [C] As data: kind 1, no `init`, no `alt`; 10 records (53-57 goatman1..goatman5, 585-589 goatman6..goatman10); reach P; `aip` set 1,2,3; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R12l. [C] First boundary: 930 decisions compared (327 + 375 + 228), 0 mismatches, 3 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F) Outside it: 210 decisions of the row's classes with no model (another think, a state row, or a case the model refuses).
- R12r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 603 of its own think's decisions in the rev 4 and rev 6 logs, 603 resumed, 0 mismatches, 0 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R13. Row 13 `FallenShaman` (fn:sub_005F1440_AiFallenShaman@0x005F1440)

Tier AI: [machinery § T13](machinery.md#t13-row-13-fallenshaman-fnsub_005f1440_aifallenshaman0x005f1440), not repeated here.

#### R14. Row 14 `QuillRat` (fn:sub_005F1140_AiQuillRat@0x005F1140)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | the distance below which it shoots or steps away |
| `aip(2)` | within `aip(1)`: chance of A2 against the step |
| `aip(4)` | the step's length, and the ring's radius at 3 or more |

```
1. rec ← Head                                                              [I] (0x005F1140, 0x005F1299)
   if rec ≠ 0:
     if GameFindUnit(G, rec+0x0C, rec+0x10) ≠ 0:
       SetModeAtUnit(5, t);  Pop; return
     Pop
2. if melee: SetModeAtUnit(4, t); return
3. if St3or19: SetModeAtUnit(5, t); return
4. if dist < aip(1):
     if chance(2): SetModeAtUnit(5, t); return                ; draw#1
     if StepAway(t, aip(4) & 0xFF, 1): return
     if dist < 4: SetModeAtUnit(5, t); return
5. Ring(aip(4) < 3 ? 3 : aip(4) & 0xFF)                       ; signed word compare
```

- R14a. [I] A head record whose unit is found makes it shoot once and drop the record; the record's kind is not tested. The ring argument is the target pointer's stack slot with its low byte replaced (`mov byte [ebp+8]`, 0x005F127B and 0x005F1283), so its upper 24 bits are the target's, and `MonAiWanderRing` uses `r & 0xFF`. (fn:sub_0058F730_MonHelpBlock@0x0058F730, fn:sub_005DE200_MonAiWanderRing@0x005DE200)
- R14b. [C] The map, the ring argument's upper bits included: family `quillrat`, 240 cases, 6 boundaries; the controls fail the 5 and 44 that separate them. (run:2026-10-30-ai-cat-emu-1)

- R14i. [C] As data: kind 1, no `init`, no `alt`; 8 records (63-67 quillrat1..quillrat5, 605-607 quillrat6..quillrat8); reach PU; `aip` set 1,2,4; `aidel` 15/12,14/9,13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R14l. [C] First boundary: 25 decisions compared (25), 0 mismatches, 4 first-call outcomes. (run:2026-11-03-ai, 0x005B186F)

#### R15. Row 15 `SandMaggot` (fn:sub_005F1800_AiSandMaggot@0x005F1800)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | under the lay count: chance to walk or lay |
| `aip(2)` | with a hostile nearer than 15: chance of A2 at it |
| `aip(3)` | the lifetime lay count (2, or 3–4 in Nightmare and Hell for `sandmaggot6`, 7, as data) |
| `aip(4)` | in melee range: chance of A1 |
| `aip(5)` | the frames of cooldown after coming up or going down |

```
1. h ← FindHostile(&hd, 0);  ph ← v14                  ; ph: 1 up, 2 laying, 3 down   [I] (0x005F1800, 0x005F1B48)
2. if ph = 3 and v18 < G.frame and Skill1 ≥ 0:
     UseSkill1(t);  DelayE(25);  v18 ← G.frame + aip(5);  v14 ← 1; return  ; MagottUp
3. if ph = 3: DelayE(20); return
4. if LifePct(U) < 25 and Skill2 ≥ 0 and hd < 7 and v18 < G.frame and Range(100) < 20:
     UseSkill2(t);  DelayE(30);  v18 ← G.frame + aip(5);  v14 ← 3; return  ; MagottDown
5. if melee and chance(4): SetModeAtUnit(4, t); return
6. if h ≠ 0 and hd < 15 and Range(100) < aip(2): SetModeAtUnit(5, h); return
7. if D100() < 20: T56(t, 6, 0); return
8. if v1C < aip(3) and Range(100) < aip(1):
     if ph ≠ 2 or Skill3 < 0:
       T56(t, 6, 0);  v14 ← 2; return
     v1C ← v1C + 1;  v14 ← 1;  UseSkill3(t);  DelayE(20); return           ; MagottLay
9. DelayE(12)
```

The alt, [I] (fn:sub_005F1750_AiSandMaggotAlt@0x005F1750, fn:sub_0058EFA0_AiCtlParamGet@0x0058EFA0, fn:sub_005B0E00_MonAiInit@0x005B0E00, fn:UNIT_GetTargetUnit@0x00553540):

```
rec ← AiCtlParamGet(kind 14)                           ; finds or makes it
if rec+0x18 = 1 and Skill1 ≥ 0:
  UseSkill1(UNIT_GetTargetUnit(G, U));  delay 30;  rec+0x18 ← 0
else:
  MonAiInit(ctl, ctl.state)                            ; clears +0x14, +0x18, frees the records, installs the think
  restore v1C;  delay 1
```

- R15a. [I] The row is kind 4, so `t` is set; the function's branches for `t = 0` (a burrow with `Skill2` at no target when the hostile is absent or beyond 10, 0x005F1856–0x005F18A8) are not reached from the row. `hd` is the distance `FindHostile` returns, `0x7FFFFFFF` with no hostile. The A2 shot is aimed at `h`, not `t`. The AI event is re-queued by `DelayE` after each skill and wait. (fn:sub_005DE130_MonAiDelayEarlier@0x005DE130, tbl:MonStats.txt:Skill3)
- R15b. [I] The alt runs when `MonAiInit` is called for a maggot whose think is already the row's. The kind-14 record is made with `+0x18 = 0`; no writer of it was found, so its skill branch has no writer: Open questions. (0x005F175F)
- R15c. [I] Not emulated: `MonAiFindHostile` comes first. (0x005F1800, [ai/0002 § 3](../../../findings/ai/0002-pool-a.md#3-emulation-run2026-10-30-ai-cat-emu-1))

- R15i. [C] As data: kind 4, no `init`, `alt` 0x005F1750; 7 records (68-72 sandmaggot1..sandmaggot5, 679 sandmaggot6, 716 sandmaggot7); reach P; `aip` set 1,2,3,4,5; `aidel` 15/14/13; skills MagottUp, MagottDown, MagottLay. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R15l. [I] Logged, not compared: 181 decisions (73 + 63 + 45) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R15r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 107 of its own think's decisions in the rev 4 and rev 6 logs, 107 resumed, 0 mismatches, 0 stopped, 167 later calls matched, an unknown value deciding 0 of 167 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R16. Row 16 `ClawViper` (fn:sub_005F1B60_AiClawViper@0x005F1B60)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | in charge range: chance of the charge |
| `aip(2)` | the charge's range |
| `aip(3)` | in melee range: chance of an attack |
| `aip(4)` | A1 against A2 |
| `aip(5)` | the idle wait |
| `aip(6)` | 0 no state, 2 state 91, else state 90 |

```
1. if v14 ≠ 0 and aip(6) ≠ 0: State(aip(6) = 2 ? 91 : 90, 0)               [I] (0x005F1B60, 0x005F1DC9)
2. if melee:
     if not chance(3): Idle(aip(5)); return                   ; draw#1
     SetModeAtUnit(chance(4) ? 4 : 5, t); return              ; draw#2
3. if Skill1 ≥ 0 and dist < aip(2) and chance(1) and MonSkillTargetOk(Skill1, t, t.x, t.y):  ; draw#1
     UseSkill1(t)                                             ; SerpentCharge
     if aip(6) ≠ 0: State(aip(6) = 2 ? 91 : 90, 1)
     v14 ← 1; return
4. if D100() < 50: Walk(t, 7)                                 ; draw#1 or #2
   else: Idle(aip(5))
```

- R16a. [I] `v14` is set at the first charge and never cleared here, so from then on every event clears the state it set (when `aip(6) ≠ 0`). `t.x, t.y` are the target's subtile position. (fn:sub_005FD470_MonSkillTargetOk@0x005FD470, struct:AiCtl+0x14)
- R16b. [C] The map, family `viper`, 240 cases, 7 boundaries; the controls fail the 18 and 87 that separate them. (run:2026-10-30-ai-cat-emu-1)

- R16i. [C] As data: kind 1, no `init`, no `alt`; 5 records (73-77 clawviper1..clawviper5); reach PU; `aip` set 1,2,3,4,5,6; `aidel` 15/14/13; skills SerpentCharge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R16l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R142. Row 142 `ClawViperEx` (fn:sub_005F1DE0_AiClawViperEx@0x005F1DE0)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)`, `aip(2)`, `aip(5)`, `aip(6)` | as row 16 (`aip(6)` is 0 in `clawviper8`, 2 in `clawviper10`, 1 in the others, as data) |
| `aip(3)` | in melee range: chance of A2 |
| `aip(4)` | within `aip(7)`: chance of the A1 test |
| `aip(7)` | the A1 range (18–28, as data) |
| `aip(8)` | the frames of A1's cooldown (50, as data) |

```
1. if v14 ≠ 0 and aip(6) ≠ 0: State(aip(6) = 2 ? 91 : 90, 0)               [I] (0x005F1DE0, 0x005F2091)
2. if melee:
     if chance(3): SetModeAtUnit(5, t); return                ; draw#1
     Idle(aip(5)); return
3. if dist < aip(7) and chance(4):                            ; draw#1
     if v18 < G.frame:
       SetModeAtUnit(4, t);  v18 ← G.frame + aip(8); return
     Idle(aip(5)); return
4. if Skill1 ≥ 0 and dist < aip(2) and chance(1) and MonSkillTargetOk(Skill1, t, t.x, t.y):
     UseSkill1(t)                                             ; Charge
     if aip(6) ≠ 0: State(aip(6) = 2 ? 91 : 90, 1)
     v14 ← 1; return
5. if D100() < 50: Walk(t, 7)
   else: Idle(aip(5))
```

- R142a. [I] Unlike row 16, in melee range it uses A2 only; within `aip(7)` it uses A1 at most once per `aip(8)` frames. Steps 4 and 5 are the finding's "the row-16 charge and approach". (tbl:MonStats.txt:aip7, tbl:MonStats.txt:aip8)
- R142b. [C] The map up to the A1 command: family `viperex`, 240 cases, 8 boundaries; the controls fail the 28 and 114 that separate them. The `+0x18` store after it is a reading only. (run:2026-10-30-ai-cat-emu-1)

- R142i. [C] As data: kind 1, no `init`, no `alt`; 5 records (594-598 clawviper6..clawviper10); reach P; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills Charge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R142l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 2: pool-B (acts II and III)

#### R17. Row 17 `SandLeaper` (fn:sub_005F20A0_AiSandLeaper@0x005F20A0)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | below 5: chance of the leap (20–25 by difficulty, as data) |
| `aip(2)` | in melee range: chance of A2 |
| `aip(3)` | within 10, out of melee range: chance to walk at `t` |
| `aip(4)` | then: chance of a `T56` walk |

```
1. if Skill1 ≥ 0 and dist < 5 and chance(1) and MonSkillTargetOk(Skill1, t, 0, 0):   [I] (0x005F20A0, 0x005F22A8)
     UseSkill1(t); return                        ; draw#1 only when the two tests before it pass; Leap
2. if not melee:
     if dist > 10: Ovr(0, 75, 0);  WanderNear(t, 5); return       ; no draw
     if chance(3): Walk(t, 7); return            ; draw#1 or #2
     if chance(4): T56(t, 4, 0); return
   else if chance(2): SetModeAtUnit(5, t); return
3. Idle(10)
```

- R17a. [I] In melee range it only ever uses A2. (fn:sub_005DF530_MonAiWanderNearUnit@0x005DF530, tbl:MonStats.txt:Skill1)
- R17b. [C] The map, family `leaper`, 240 cases, 6 boundaries; the `≤` and Normal-column controls fail the 17 and 45 that separate them. (run:2026-10-30-ai-cat-emu-2)

- R17i. [C] As data: kind 1, no `init`, no `alt`; 7 records (78-82 sandleaper1..sandleaper5, 629-630 sandleaper6..sandleaper7); reach P; `aip` set 1,2,3,4; `aidel` 15/14/13; skills Leap. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R17l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R18. Row 18 `PantherWoman` (fn:sub_005F22B0_AiPantherWoman@0x005F22B0)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | out of melee range: chance of the fast approach |
| `aip(2)` | in melee range: chance of A1 |
| `aip(3)` | the distance to its nearest packmate past which it rejoins (8–24, as data) |
| `aip(4)` | the idle wait |

```
1. if melee:                                                               [I] (0x005F22B0, 0x005F2455)
     if chance(2): SetModeAtUnit(4, t); return   ; draw#1
     Idle(aip(4)); return
2. if chance(1):                                 ; draw#1
     Ovr(0, 75, 0);  Walk13(t, 7); return
3. s ← {unit 0, best 0x7FFFFFFF};  AiUnitSearch(G, U, &s, AiSameBaseNearCb, 1)
4. if s.unit ≠ 0 and aip(3)·aip(3) < s.best:
     Ovr(0, 75, 0);  Walk(s.unit, 7); return
5. if D100() < 25: T56(t, 3, 0)                  ; draw#2
   else: Idle(aip(4))
```

- R18a. [I] The callback takes a monster (`Unit+0x00` = 1) other than the searcher with the searcher's `MonBaseId`, not in a death mode, and keeps the nearest by `UnitDistSq`. The search block is a stack block `{+0x00 unit, +0x04 best}` at `EBP − 0x2C`. (fn:sub_005B0D00_AiSameBaseNearCb@0x005B0D00, fn:sub_00463860_MonBaseId@0x00463860, fn:sub_0063EA40_MonIsDeathMode@0x0063EA40)
- R18b. [C] The map up to the search, the block's two words included: family `panther`, 240 cases, 4 boundaries; the controls fail the 26 and 99 that separate them. (run:2026-10-30-ai-cat-emu-2)

- R18i. [C] As data: kind 1, no `init`, no `alt`; 6 records (83-86 pantherwoman1..pantherwoman4, 627-628 pantherwoman5..pantherwoman6); reach PU; `aip` set 1,2,3,4,5; `aidel` 15/13,14/12,13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R18l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R19. Row 19 `Swarm` (fn:sub_005F2460_AiSwarm@0x005F2460)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | out of melee range: chance to walk at `t` |
| `aip(2)` | the idle wait (12–20, as data) |
| `aip(3)` | in melee range: chance of A1 |

```
1. if not melee:                                                           [I] (0x005F2460, 0x005F252D)
     if chance(1): Walk(t, 7); return            ; draw#1
   else if chance(3):                            ; draw#1
     SetModeAtUnit(4, t); return
2. Idle(aip(2))
```

- R19a. [C] The map, family `swarm`, 240 cases, 3 boundaries; the controls fail the 34 and 120 that separate them. (run:2026-10-30-ai-cat-emu-2)

- R19i. [C] As data: kind 1, no `init`, no `alt`; 5 records (87-90 swarm1..swarm4, 715 swarm5); reach P; `aip` set 1,2,3; `aidel` 15/14/13; skills Swarm Move. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R19l. [C] First boundary: 193 decisions compared (71 + 82 + 40), 0 mismatches, 3 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R19r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 122 of its own think's decisions in the rev 4 and rev 6 logs, 122 resumed, 0 mismatches, 0 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R20. Row 20 `Scarab` (fn:sub_005F2540_AiScarab@0x005F2540)

Tier AI: [machinery § T20](machinery.md#t20-row-20-scarab-fnsub_005f2540_aiscarab0x005f2540), not repeated here.

#### R21. Row 21 `Mummy` (fn:sub_005F2850_AiMummy@0x005F2850)

Tier AI: [machinery § T21](machinery.md#t21-row-21-mummy-fnsub_005f2850_aimummy0x005f2850), not repeated here.

#### R22. Row 22 `GreaterMummy` (fn:sub_005F2B10_AiGreaterMummy@0x005F2B10)

Tier AI: [machinery § T22](machinery.md#t22-row-22-greatermummy-fnsub_005f2b10_aigreatermummy0x005f2b10), not repeated here.

#### R23. Row 23 `Vulture` (fn:sub_005F3170_AiVulture@0x005F3170)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | on the ground, in melee range: chance of A1 |
| `aip(2)` | the wait, by `Delay` |
| `aip(3)` | the percent of life at or below which a near unit makes it land |
| `aip(4)` | on the ground: chance of a `T56` walk against `Toward(t, 9, 0)` |
| `aip(5)` | on the ground: chance to move at all; skipped in the event after a landing |

`fly ← v14`: above 0 airborne events left, 0 on the ground, −1 just landed.

```
1. fly ← v14;  far ← UnitDistSq(U, t) > 144                                [I] (0x005F3170, 0x005F3190, 0x005F3340, 0x005F35C0, 0x005F3728)
2. if RoomOf(t) ≠ RoomOf(U) and far:
     if fly < 1: Toward(t, 9, 0); return
     if AiVultureLand(U):
       MoveToUnitDist(U, 9, 2, 3);  Delay(12);  v14 ← −1; return    ; the unit itself as the target
3. if fly = 0 and MonsterOwner(U) = 0 and far and Range(100) < 60:   ; take off
     AiVultureTakeOff(U);  v14 ← 24 + Pow2(8);  MoveToUnitDist(t, 8, 8, 8);  Delay(12); return
4. s ← {unit 0, bound 121, pct aip(3)};  AiUnitSearch(G, U, &s, AiWoundedNearCb, 1)
5. if fly ≥ 2:
     if s.unit ≠ 0 or (dist < 6 and Range(100) < 15):
       v14 ← 1;  goto land
     AiVultureTakeOff(U)
     if v18 = 0 or v1C = 0 or AiPathDistToPoint(U, v18, v1C) < 2:    ; a new circling point
       c ← fly + 8
       x ← tx − c + RangeB(2c);  y ← ty − c + RangeB(2c)
       r ← clamp(2c, 12, 36)
       while AiPathDistToPoint(U, x, y) < r:
         step x and y one away from U's position; if at it, both + 1
       v18 ← x;  v1C ← y;  Ovr(1, 0, 0);  MoveToPoint(x, y, 8);  Delay(12);  v14 ← v14 − 1; return
     FreeNearFallback(room of t, then of U, (v18, v1C), size, 0xFFFF, 1) → (v18, v1C) when found
     v14 ← v14 − 1;  Ovr(7, 0, 0);  MoveToPoint(v18, v1C, 8);  Delay(12); return
6. if fly = 1:
   land:
     if AiVultureLand(U):
       MoveToUnitDist(t, 9, 2, 3);  Delay(12);  v14 ← −1; return
     v14 ← 8;  Delay(12)                                             ; no room to land: fly 8 more
7. if melee:
     if chance(1): SetModeAtUnit(4, t); return
     Delay(aip(2)); return
8. if fly ≠ −1 and Range(100) ≥ aip(5): Delay(aip(2)); return
9. if Range(100) < aip(4): T56(t, 6, 0)
   else: Toward(t, 9, 0)
10. v14 ← 0;  Delay(12)
```

- R23a. [I] `v14` is the flight counter. A vulture with no owner, more than 12 subtiles from its target (squared 144), takes off on 60 % of events for 24–31 airborne events, circles points drawn around the target (`RNG_RangeB` twice, a square of half-side `fly + 8`) at least `clamp(2(fly + 8), 12, 36)` from itself, and lands when the counter reaches 1, when the callback finds a unit, or within 6 on 15 %. `v18` and `v1C` hold the circling point. Modes 8 and 9 are the move commands' modes here. (fn:sub_005F3170_AiVulture@0x005F3170, fn:sub_005F2EB0_AiVultureTakeOff@0x005F2EB0, fn:sub_005F2FC0_AiVultureLand@0x005F2FC0, fn:RNG_RangeB@0x0045C3E0, fn:RNG_RangePow2@0x00472210, struct:AiCtl+0x18)
- R23b. [I] **The callback** `AiWoundedNearCb`: a monster or player other than itself, not dying, `UnitDistSq` ≤ 121, stat 6 ≤ `UnitGetMaxHp ÷ 100 · aip(3)`, keeping the nearest. (fn:sub_005F30F0_AiWoundedNearCb@0x005F30F0, tbl:ItemStatCost.txt:hitpoints)
- R23c. [I] Not emulated: the first callee is `UnitDistSq` and the next two `UnitGetRoom`, before any draw. (0x005F31C4, 0x005F31DB, 0x005F31E3)
- R23d. [I] The 8 mismatches below all lie in the rev 4 logs, each stopping at 0x00620BB0 called at 0x005F33EC; the logger's limit of 600 non-think calls is the cause read, and rev 6's 256 decisions have 0, but only 2 `AIL` lines are this row's, so the reading is untested. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5, 0x005F33EC)

- R23i. [C] As data: kind 1, no `init`, no `alt`; 5 records (110-113 vulture1..vulture4, 608 vulture5); reach P; `aip` set 1,2,3,4,5; `aidel` 15/13,14/11,13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R23l. [I] Logged, not compared: 1062 decisions (375 + 431 + 256) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R23r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 687 of its own think's decisions in the rev 4 and rev 6 logs, 679 resumed, 8 mismatches, 0 stopped, 4284 later calls matched, an unknown value deciding 179 of 4284 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R24. Row 24 `Mosquito` (fn:sub_005F3730_AiMosquito@0x005F3730)

| Slot | Meaning (code reading) |
|---|---|
| `aip(3)` | in melee range: chance to keep attacking |
| `aip(4)` | chance of the skill against A1 |
| `aip(5)` | ring points of the retreat, less one (5 in every record, as data) |

```
1. if melee:                                                               [I] (0x005F3730, 0x005F394F)
     if chance(3) or v18 = 0:                 ; draw#1, always taken
       v18 ← v18 + 1
       if Skill1 ≥ 0 and chance(4): UseSkill1(t); return    ; the drain
       SetModeAtUnit(4, t); return
     if D100() > 20: Idle(15); return         ; draw#2
     v14 ← 2;  v18 ← 0
2. switch v14:
     0: Ovr(13, 100, 0);  Walk(t, 0)
     1: Ovr(0, 50, 0);  Ring(4);  v18 ← v18 + 1;  if v18 > aip(5): v14 ← 0;  v18 ← 0
     2: Ovr(2, 100, 0);  StepAway(t, 10, 1);  v14 ← 1;  v18 ← 0
     else: v14 ← 0;  v18 ← 0;  Idle(10)
```

- R24a. [I] An attack-and-retreat cycle: `v18` counts the attacks of a melee bout, the first free of the `aip(3)` test; a failed `aip(3)` draw then 21 % of the time starts the retreat, then `aip(5)` + 1 ring points, then the approach under override type 13. (struct:AiCtl+0x18)
- R24b. [C] The map, `AiCtl+0x14/+0x18` at the boundary included: family `mosquito`, 240 cases, 7 boundaries; the controls fail the 16 and 26 that separate them. (run:2026-10-30-ai-cat-emu-2)

- R24i. [C] As data: kind 1, no `init`, no `alt`; 4 records (114-117 mosquito1..mosquito4); reach P; `aip` set 3,4,5; `aidel` 15/14/13; skills Mosquito. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R24l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R25. Row 25 `WillOWisp` (fn:sub_005F39B0_AiWillOWisp@0x005F39B0)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | in the plain states: chance of S1, or of the cast out of melee range |
| `aip(2)` | in melee range: chance of A1 |
| `aip(3)` | chance to walk at `t` against a ring point |

`v14` is the state below: 0–3 plain, 4 the gather, 5 and 6–12 the dance. `v1C` is the gather cooldown frame outside the dance and the wisp's place in it.

```
gather trigger, at entry:                                                  [I] (0x005F3E0A, 0x005F3E46)
  if v1C < G.frame and UnitDistSq(U, t) < 1024 and v14 < 4 and Range(1000) ≤ d + 2: v14 ← 4

state 4:                                                                   [I] (0x005F3E5B, 0x005F4051)
  a room unit search of radius 32 around U (RoomUnitSearchInit, flags 0x583; AiWispCb)
  exactly 4 found: each gets v14 ← 6, v18 ← 0, v1C ← its index 1..4 (AiCtlSetVar), Idle(337 − G.frame mod 337)
  exactly 5 found: state 5 and indices 1..5, the same idle
  then U itself idles to the same frame
  any other count: v14 ← 2;  Idle(8)

the dance, states 5 and 6..12:                                             [I] (0x005F4054, 0x005F4366)
  point ← origin + the offset table's entry                 ; four wisps: index place + 4·state
  if AiPathDistToPoint(U, point) > 3:
    on 34 %: Ring(4)
    else: MoveToPointNoStop(x, y, 2)
  else:
    wait for a frame multiple of 67
    for three sub-steps: MonAiSetMode(7, x', y') at a second table's offset, when non-zero;  count v18
    after three, the four-wisp dance: next state; past 12 it ends (v14 ← 2, cooldown v1C ← G.frame + 1800)
    the five-wisp dance (state 5) ends after three sub-steps, with no grant

the grant, at each four-wisp advance, after Idle(337 − G.frame mod 337):    [I] (0x005F41AA, 0x005F4271)
  if t is a living player (Unit+0x00 = 0, not UnitIsDead):
    a new stat list on t (STATLIST_Alloc flags 2): stat 80 ← 50·(d + 1), ending at G.frame + 1 728 000 (StatListSetEnd)
    a unit event 12 queued on t at that frame;  the list linked to t

state 1 (after an approach):                                               [I] (0x005F4366, 0x005F4500)
  if v18 < 1:
    if melee: SetModeAtUnit(8, 0);  v14 ← 3
    else if chance(1): SetModeAtUnit(8, 0);  v14 ← 2
  else:
    v18 ← v18 − 1
    if Range(100) < aip(3): walk to t
    else: Ring(6);  v14 ← 1

states 0, 2, 3:                                                            [I] (0x005F4366, 0x005F4500)
  if not melee and (v14 = 2 or chance(1)): SetModeAtUnit(7, t);  v14 ← 0   ; SC, Chain Lightning by Skill1's mode
  else if melee and (v14 = 3 or chance(2)): A1;  v14 ← 0
  else:
    if Range(100) < aip(3): walk to t
    else: Ring(4)
    v14 ← 1;  v18 ← 3
```

- R25a. [I] The trigger's `Range(1000) ≤ d + 2` is 3, 4 or 5 in 1000. `AiWispCb`: a monster not dying whose `MonBaseId` is 118, `willowisp1`'s row. The stack table's entries are 8-byte `(x, y)` from `EBP − 0x2F4`. The four-wisp origin is the target's subtile position (0x005F407E–0x005F40AA). (fn:sub_005F3960_AiWispCb@0x005F3960, fn:sub_0058EC00_AiCtlSetVar@0x0058EC00, fn:sub_0065A950_RoomUnitSearchInit@0x0065A950)
- R25b. [I] Each of the four wisps grants on each of its seven advances: the end-of-dance reset is skipped over, not the grant. (fn:STATLIST_Alloc@0x006251F0, fn:STATLIST_LinkToUnit@0x00626E10, fn:sub_005417D0_UnitQueueEvent@0x005417D0, tbl:ItemStatCost.txt:item_magicbonus)
- R25c. [I] The finding states the dance in prose; this block is that prose in order, and the finding's walk of the plain states does not say what the A1 command's argument is beyond "attacks A1", so none is added. The offset tables' values, the five-wisp origin and what event 12 does are Open questions. Not emulated: `UnitDistSq` comes first on most events and the room search in state 4. (0x005F3E1C, 0x005F3F14)

- R25i. [C] As data: kind 1, no `init`, no `alt`; 8 records (118-121 willowisp1..willowisp4, 639-641 willowisp5..willowisp7, 733 willowisp8); reach PU; `aip` set 1,2,3; `aidel` 15/14/13; skills Chain Lightning. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R25l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R26. Row 26 `Arach` (fn:sub_005F4510_AiArach@0x005F4510)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | in melee range: chance of A1; while retreating, `aip(1) − 25` is the attack chance |
| `aip(2)` | life at or above `aip(5)`: chance of a `T56` walk |
| `aip(3)` | retreat over: chance to approach; cycle's approach draw |
| `aip(4)` | while retreating: the distance at or past which it stops |
| `aip(5)` | life percent below which it lays (25–45, as data) |

```
1. life ← UnitLifePct(U)                                                   [I] (0x005F4510, 0x005F4840)
2. if v14 = 1:                                       ; retreating after a lay
     v18 ← 0
     if life > 75:
       v14 ← 0
       if chance(3): v14 ← 2;  Walk13(t, 0); return
       T56(t, 6, 0); return
     if melee and aip(1) > 25 and Range(100) < aip(1) − 25: SetModeAtUnit(4, t); return
     if dist ≥ aip(4) and not St3or19: v14 ← 0;  T56(t, 12, 0); return
     StepAway(t, 4, 0); return
3. if not melee:
     if St3or19 or v18 = 1: v18 ← 1;  Walk13(t, 0); return
     v1C ← v1C + 1;  if v1C > 20: v1C ← 0
     v18 ← 0
     if v1C = 1 and Range(100) < aip(3): v18 ← 1;  Walk13(t, 0); return
     if Range(100) < 20: Ring(6); return
     Idle(15); return
4. v14 ← 2
5. if chance(1): SetModeAtUnit(4, t); return         ; draw#1
6. if life ≥ aip(5):
     if Range(100) < aip(2): T56(t, 4, 0); return
     Idle(15); return
7. v14 ← 1
8. if Skill1 ≥ 0 and not UNIT_HasState(U, 22): MonAiUseSkill(Sk1mode, Skill1, 0, 0, 0); return  ; SpiderLay, no target
9. StepAway(t, 8, 0)
```

- R26a. [I] Below `aip(5)` percent life a spider in melee range lays (state 22 `spiderlay` not yet set) and retreats until above 75 % life; `v1C` is a 21-event cycle that gives one approach draw per cycle out of melee range. (fn:UNIT_HasState@0x00639DF0, tbl:States.txt:spiderlay)
- R26b. [I] Not emulated: `UnitLifePct` is the first callee. (fn:sub_00621F20_UnitLifePct@0x00621F20)

- R26i. [C] As data: kind 1, no `init`, no `alt`; 7 records (122-126 arach1..arach5, 685 arach6, 717 arach7); reach PU; `aip` set 1,2,3,4,5; `aidel` 15/14/13; skills SpiderLay. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R26l. [I] Logged, not compared: 119 decisions (73 + 28 + 18) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R26r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 46 of its own think's decisions in the rev 4 and rev 6 logs, 46 resumed, 0 mismatches, 0 stopped, 91 later calls matched, an unknown value deciding 0 of 91 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R27. Row 27 `ThornHulk` (fn:sub_005F4850_AiThornHulk@0x005F4850)

| Slot | Meaning (code reading) |
|---|---|
| `aip(1)` | in melee range: chance to attack at all |
| `aip(2)` | a plain attack: A2 against A1 |
| `aip(3)` | on a failed `aip(1)`: chance of a `T56` walk |
| `aip(4)` | chance to start a frenzy bout |
| `aip(5)` | the frames added to the mode's first event as a delay |
| `aip(6)` | the bout's repeat count (3–5; 5 in `thornhulk5`, as data) |

```
1. if not melee: v14 ← 0;  Walk13(t, 7); return                            [I] (0x005F4850, 0x005F4A60)
2. if v14 < 1:
     if not chance(1):                               ; draw#1
       if Range(100) < aip(3): T56(t, 4, 0); return
       Idle(15); return
     if v18 < 1 and Range(100) < aip(4):             ; draw#2, only when v18 < 1
       MonAiUseSkill(5, Skill1, t, 0, 0)             ; MonFrenzy, in mode A2
       f ← UnitEventFirstFrame(G, U, 1)
       if G.frame < f: Delay(aip(5) − G.frame + f)
       v14 ← aip(6); return
     v18 ← v18 − 1
     SetModeAtUnit(Range(100) < aip(2) ? 5 : 4, t); return
3. MonAiUseSkill(5, Skill1, t, 0, 0)
4. f ← UnitEventFirstFrame(G, U, 1)
   if G.frame < f: Delay(aip(5) − G.frame + f)
5. v14 ← v14 − 1;  if v14 < 1: v18 ← 3
```

- R27a. [I] A frenzy bout: once started the hulk repeats the skill for `aip(6)` events, then `v18` = 3 makes the next three melee decisions plain attacks. The skill is always used in mode 5, not `Sk1mode`. `v18` keeps decreasing below 0 on further plain attacks. (fn:sub_005415A0_UnitEventFirstFrame@0x005415A0, tbl:MonStats.txt:aip6)
- R27b. [C] The map up to the first callee: family `thornhulk`, 240 cases, 7 boundaries; the controls fail the 28 and 42 that separate them. The `Delay` and the stores after the skill are readings. (run:2026-10-30-ai-cat-emu-2)

- R27i. [C] As data: kind 1, no `init`, no `alt`; 5 records (127-130 thornhulk1..thornhulk4, 609 thornhulk5); reach PU; `aip` set 1,2,3,4,5,6; `aidel` 15/13,14/12,13; skills MonFrenzy. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R27l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R28. Row 28 `Vampire` (fn:sub_005F4A70_AiVampire@0x005F4A70)

Tier AI: [machinery § T28](machinery.md#t28-row-28-vampire-fnsub_005f4a70_aivampire0x005f4a70), not repeated here.

#### R29. Row 29 `BatDemon` (fn:sub_005F5040_AiBatDemon@0x005F5040)

Tier AI: [machinery § T29](machinery.md#t29-row-29-batdemon-fnsub_005f5040_aibatdemon0x005f5040-alt-fnsub_005f4fd0_aibatdemonalt0x005f4fd0), not repeated here.

#### R30. Row 30 `Fetish` (fn:sub_005F53E0_AiFetish@0x005F53E0)

Tier AI: [machinery § T30](machinery.md#t30-row-30-fetish-fnsub_005f53e0_aifetish0x005f53e0), not repeated here.

### Batch 3: pool-C (ranged, maggots, the Zakarum, nests)

#### R33. Row 33 `HellMeteor` (fn:sub_005F56D0_AiHellMeteor@0x005F56D0)

**`aip`:** 1 chance to cast; 2 the idle wait; 3 half the side of the square around itself (10, as data).

```
1. if Skill1 ≥ 0 and chance(1):                 ; draw#1                   [I] (0x005F56D0, 0x005F5828)
     x ← U.x + RangeB(2·aip(3)) − aip(3)        ; draw#2
     y ← U.y + RangeB(2·aip(3)) − aip(3)        ; draw#3
     MonAiUseSkill(Sk1mode, Skill1, 0, x, y); return
2. Idle(aip(2))
```

- R33a. [I] The point runs from `−aip(3)` to `aip(3) − 1` off itself on each axis, with no target unit. The x getter runs before the first `RangeB` and the y getter between the two. Widths: `aip(3)` i16, `2·aip(3)` and the sums 32-bit, the position u16 zero-extended, so nothing wraps. (fn:RNG_RangeB@0x0045C3E0)
- R33b. [C] The map, family `meteor`, 240 cases, 157 with a draw, 2 boundaries; the `≤` and Normal-column controls fail the 16 and 151 that separate them. (run:2026-10-30-ai-cat-emu-3)

- R33i. [C] As data: kind 1, no `init`, no `alt`; 1 records (153 hellmeteor); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills HellMeteor. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R33l. [C] First boundary: 56 decisions compared (56), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, 0x005B186F)

#### R35. Row 35 `CorruptArcher` (fn:sub_005F5A20_AiCorruptArcher@0x005F5A20)

Tier AI: [machinery § T35](machinery.md#t35-row-35-corruptarcher-fnsub_005f5a20_aicorruptarcher0x005f5a20), not repeated here.

#### R36. Row 36 `CorruptLancer` (fn:sub_005F5D50_AiCorruptLancer@0x005F5D50)

**`aip`:** 1 out of melee range: chance to approach; 2 melee: chance to attack, skipped after a charge; 3 the idle wait; 4 chance to run against a walk (0 in Normal in every record, as data, so a lancer never runs to its target in Normal); 5 the charge distance; 6 chance of `Skill1`; 7 of `Skill2`; 8 of `Skill3`. `cr_lancer1..5` have no skills and `aip(6)`, `aip(7)` 0; `cr_lancer6..8` have `Jab` and a second skill and set them, as data.

```
1. if dist > aip(5):                                                       [I] (0x005F5D50, 0x005F6067)
     PathSetStopDist(U.path, MeleeRng);  Ovr(13, 100, 0);  RunStop(t, MeleeRng);  v14 ← 1; return   ; the charge
2. if not melee:
     if not chance(1): Idle(aip(3)); return                    ; draw#1
     PathSetStopDist(U.path, MeleeRng)
     if not chance(4): WalkStop(t, 3); return                  ; draw#2
     Ovr(13, 100, 0);  RunStop(t, MeleeRng); return
3. if v14 = 0 and not chance(2): Idle(aip(3)); return          ; draw#1
4. v14 ← 0
5. if Skill1 ≥ 0 and chance(6): UseSkill1(t); return           ; Jab
6. if Skill2 ≥ 0 and Range(100) < aip(7): UseSkill2(t); return
7. if Skill3 ≥ 0 and Range(100) < aip(8): UseSkill3(t); return
8. SetModeAtUnit(4, t)
```

- R36a. [I] `MeleeRng` is the MonStats2 byte `+0x0E`. After a charge the first melee decision attacks without the `aip(2)` draw. Up to four draws. (fn:sub_00649070_PathSetStopDist@0x00649070, tbl:MonStats2.txt:MeleeRng, struct:AiCtl+0x14)
- R36b. [C] The map, family `lancer`, 240 cases, 160 with a draw, 8 boundaries; the controls fail the 25 and 106 that separate them. (run:2026-10-30-ai-cat-emu-3)

- R36i. [C] As data: kind 1, no `init`, no `alt`; 9 records (165-169 cr_lancer1..cr_lancer5, 615-617 cr_lancer6..cr_lancer8, 723 cr_lancer8); reach P; `aip` set 1,2,3,4,5,6,7; `aidel` 15/13,14/12,13; skills Jab, MonPowerStrike, MonIceSpear. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R36l. [C] First boundary: 4 decisions compared (4), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, 0x005B186F) Outside it: 32 decisions of the row's classes with no model (another think, a state row, or a case the model refuses).

#### R37. Row 37 `SkeletonBow` (fn:sub_005F6070_AiSkeletonBow@0x005F6070)

Tier AI: [machinery § T37](machinery.md#t37-row-37-skeletonbow-fnsub_005f6070_aiskeletonbow0x005f6070), not repeated here.

#### R38. Row 38 `MaggotLarva` (fn:sub_005F6220_AiMaggotLarva@0x005F6220)

**`aip`:** 1 melee: chance of A1; 2 the wait in melee range; 3 out of melee range: chance to walk; 4 the wait out of it.

```
1. if not melee:                                                           [I] (0x005F6220, 0x005F6336)
     v14 ← 0
     if chance(3): Walk(t, 1); return     ; draw#1
     Idle(aip(4)); return
2. if v14 = 0 and chance(1):              ; draw#1, only when v14 = 0
     v14 ← 1;  SetModeAtUnit(4, t); return
3. v14 ← 0;  Idle(aip(2))
```

- R38a. [I] The larva alternates an attack with a wait: `v14` set by the attack, cleared by the next decision. (struct:AiCtl+0x14)
- R38b. [C] The map, family `larva`, 240 cases, 153 with a draw, 4 boundaries; the controls fail the 20 and 131 that separate them. (run:2026-10-30-ai-cat-emu-3)

- R38i. [C] As data: kind 1, no `init`, no `alt`; 6 records (180-184 maggotbaby1..maggotbaby5, 680 maggotbaby6); reach ·; `aip` set 1,2,3,4,5; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R38l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R39. Row 39 `PinHead` (fn:sub_005F6340_AiPinHead@0x005F6340)

**`aip`:** 1 melee after the first decision: chance to act; 2 the wait in melee range; 3 out of melee range: chance to walk; 4 the wait out of it; 5 chance of `Skill1`; 6 chance of `Skill2`.

```
1. if not melee:                                                           [I] (0x005F6340, 0x005F6529)
     v14 ← 0
     if chance(3): Walk(t, 7); return     ; draw#1
     Idle(aip(4)); return
2. if v14 ≠ 0 and not chance(1): Idle(aip(2)); return   ; draw#1, only when v14 ≠ 0
3. v14 ← 1
4. if Skill1 ≥ 0 and chance(5): UseSkill1(t); return    ; Smite
5. if Skill2 ≥ 0 and chance(6): UseSkill2(t); return
6. SetModeAtUnit(4, t)
```

- R39a. [I] It skips the `aip(1)` draw on its first melee decision (`v14` = 0) and makes it after that; the skill draws come after it either way. (struct:AiCtl+0x14)
- R39b. [C] The map, family `pinhead`, 240 cases, 237 with a draw, 6 boundaries; the controls fail the 23 and 116 that separate them. (run:2026-10-30-ai-cat-emu-3)

- R39i. [C] As data: kind 1, no `init`, no `alt`; 6 records (186-189 blunderbore1..blunderbore4, 618-619 blunderbore5..blunderbore6); reach P; `aip` set 1,2,3,4,5; `aidel` 15/13,14/12,13; skills Smite. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R39l. [C] First boundary: 202 decisions compared (202), 0 mismatches, 4 first-call outcomes. (run:2026-11-03-ai, 0x005B186F)

#### R40. Row 40 `MaggotEgg` (fn:sub_005F6530_AiMaggotEgg@0x005F6530)

**`aip`:** 1 the delay and the idle (the delay after hatching: 250 down to 150 in Normal, 200 above, as data); 2 chance to hatch.

```
1. if Skill1 ≥ 0 and v14 ≠ 1 and chance(2):             ; draw#1           [I] (0x005F6530, 0x005F661F)
     UseSkill1(t);  Delay(aip(1));  v14 ← 1; return      ; hatch
2. if v14 = 1: UnitKilled(G, U, UNIT_GetTargetUnit(G, U), 1)    ; no return
3. Idle(aip(1))
```

- R40a. [I] One hatch per egg: after it, the next event kills the egg with its own last target as the killer and still queues `Idle(aip(1))` (0x005F6601–0x005F6614, no jump between the two calls). (fn:UNIT_GetTargetUnit@0x00553540, fn:sub_0057CCB0_UnitKilled@0x0057CCB0)
- R40b. [C] The map up to the skill, `UNIT_GetTargetUnit` (its stack arguments `G`, `U` and `UnitKilled`'s pending 1) or the idle: family `egg`, 240 cases, 110 with a draw, 3 boundaries; the controls fail the 11 and 98 that separate them. (run:2026-10-30-ai-cat-emu-3)

- R40i. [C] As data: kind 1, no `init`, no `alt`; 6 records (190-194 maggotegg1..maggotegg5, 681 maggotegg6); reach ·; `aip` set 1,2; `aidel` 15/14,15/13,15; skills MaggotEgg. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R40l. [C] First boundary: 7 decisions compared (1 + 5 + 1), 0 mismatches, 1 first-call outcome. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R40r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 6 of its own think's decisions in the rev 4 and rev 6 logs, 6 resumed, 0 mismatches, 0 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R43. Row 43 `FoulCrowNest` (fn:sub_005F6650_AiFoulCrowNest@0x005F6650)

**`aip`:** 1 the frames between spawns (100/80/70, as data); 3 the spawn count (6–15 in Normal up to 15–24 in Hell, as data).

```
init 0x005F6630:  v14 ← T;  v18 ← 0                                        [I] (0x005F6630, 0x005F6649)

1. if dist > 20: Idle(25); return                                          [I] (0x005F6650, 0x005F67A9)
2. if v18 ≥ aip(3):
     U+0xC4 ← U+0xC4 | 0x20000;  MonAiSetMode(0, 0, 0); return             ; die
3. e ← |T − v14|                        ; 32-bit subtract, then neg if negative
4. if Skill1 ≥ 0 and e ≥ aip(1):
     v14 ← T
     cls ← MonStats count > 206 ? 206 : −1
     if SpawnClassCellTest(cls, UnitGetRoom(U), U.x, U.y, 0):
       v18 ← v18 + 1;  UseSkill1(t); return      ; Nest
5. Idle(20 + low mod 10)                ; draw#1
```

- R43a. [I] The nest moves its timer to `T` before the cell test, so a failed test waits a full `aip(1)` again. The class compare is inlined as `((count > C) − 1 & mask) + C`; row 206 is `crownest1`, for all four nest records. The only draw is the idle's, the inline `0xCCCCCCCD` divide, unsigned. `e` cannot wrap on a timer that holds a past frame; for `T − v14 = −2³¹` the `neg` leaves `−2³¹`, below any `aip(1)`. (fn:sub_005FD350_SpawnClassCellTest@0x005FD350, fn:sub_00620BB0_UnitGetRoom@0x00620BB0, struct:Unit+0xC4)
- R43b. [C] The map up to `SpawnClassCellTest` (its `ECX` class, `EDX` room and the position arguments), the death command (with `Unit+0xC4`) or an idle: family `nest`, 240 cases, 28 with a draw, 4 boundaries. `≤` cannot separate the draw, which is compared with nothing, and the Normal column separates 48; the draw is checked by its value (`Idle` argument and moved seed in all 28). Two controls at the lane check, the death compare flipped and the range test moved by one, fail all the 53 and 30 they separate. The `e ≥ aip(1)` edge has no control. (run:2026-10-30-ai-cat-emu-3)

- R43i. [C] As data: kind 1, `init` 0x005F6630, no `alt`; 4 records (206-209 crownest1..crownest4); reach P; `aip` set 1,3; `aidel` 15/15/15; skills Nest. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R43l. [C] First boundary: 32 decisions compared (32), 0 mismatches, 3 first-call outcomes. (run:2026-11-03-ai-3, 0x005B186F)
- R43r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 32 of its own think's decisions in the rev 4 and rev 6 logs, 32 resumed, 0 mismatches, 0 stopped, 8 later calls matched, an unknown value deciding 0 of 8 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### R45. Row 45 `Sarcophagus` (fn:sub_005F6A10_AiSarcophagus@0x005F6A10)

**`aip`:** 1 the frames between spawns (125/110/90, as data); 3 one less than the spawn count.

```
init 0x005F6630:  v14 ← T;  v18 ← 0                                        [I] (0x005F6630, 0x005F6649)

1. if dist > 25: Idle(25); return                                          [I] (0x005F6A10, 0x005F6B69)
2. if v18 > aip(3):
     U+0xC4 ← U+0xC4 | 0x20000;  MonAiSetMode(0, 0, 0); return             ; die
3. e ← |T − v14|                        ; 32-bit subtract, then neg if negative
4. if Skill1 ≥ 0 and e ≥ aip(1):
     cls ← MonStats count > 228 ? 228 : −1
     if SpawnClassCellTest(cls, UnitGetRoom(U), U.x, U.y, 0):
       v18 ← v18 + 1;  v14 ← T;  UseSkill1(t); return      ; Nest
5. Idle(20 + low mod 10)                ; draw#1
```

- R45a. [I] Row 43's code differs by these three: the bound (`>` against `≥`), the distance and class, and that the sarcophagus moves its timer only on success, so it tries again at the next event. Row 228 is `sarcophagus`. (fn:sub_005FD350_SpawnClassCellTest@0x005FD350, struct:Unit+0xC4)
- R45b. [C] The map up to the same three ends: family `sarco`, 240 cases, 79 with a draw, 4 boundaries, the draw checked by its value; `≤` separates none, the Normal column 84, and the two lane-check controls fail all the 72 and 24 they separate. The `e ≥ aip(1)` edge has no control. (run:2026-10-30-ai-cat-emu-3)

- R45i. [C] As data: kind 1, `init` 0x005F6630, no `alt`; 1 records (228 sarcophagus); reach ·; `aip` set 1,3; `aidel` 15/15/15; skills Nest. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R45l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R46. Row 46 `ElementalBeast` (fn:sub_005F6B70_AiElementalBeast@0x005F6B70)

**`aip`:** 1 chance of a walk against a ring (20, as data); 2 the distance at which it wakes (16–24, as data); 3 the idle wait.

```
switch v14:                                                                [I] (0x005F6B70, 0x005F6C9B)
  2: UnitKilled(G, U, t, 1)
  0: if dist < aip(2) or St3or19:
       SetModeAtUnit(8, t);  v14 ← 1
     else: Idle(aip(3))
  1: if melee:
       SetModeAtUnit(8, t);  UnitQueueEvent(G, U, 0, T + 1, 0, 0);  v14 ← 2
     else if Range(100) < aip(1): Walk(t, 0)     ; draw#1
     else: Ring(8)
  else: Idle(aip(3))
```

- R46a. [I] The orb casts S1 once when woken, flies at the target, in melee range casts S1 again and queues a kind-0 event (the mode frame event, code 0, index 0) at `T + 1`, then dies at the event after, the target as killer. (fn:sub_005417D0_UnitQueueEvent@0x005417D0, struct:AiCtl+0x14)
- R46b. [C] The map, family `beast`, 240 cases, 49 with a draw, 6 boundaries; the controls fail the 5 and 46 that separate them. (run:2026-10-30-ai-cat-emu-3)

- R46i. [C] As data: kind 1, no `init`, no `alt`; 4 records (230-233 firebeast..poisonorb); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R46l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R47. Row 47 `FlyingScimitar` (fn:sub_005F6CA0_AiFlyingScimitar@0x005F6CA0)

**`aip`:** 1 out of melee range, both approach draws (90, as data); 2 melee: chance of A1; 3 the idle wait; 4 melee: chance of a `T56` walk.

```
1. if not melee:                                                           [I] (0x005F6CA0, 0x005F6E17)
     if chance(1): Toward(t, 8, 1); return     ; draw#1
     if chance(1): Walk(t, 7); return          ; draw#2, aip(1) again
   else:
     if chance(2): SetModeAtUnit(4, t); return ; draw#1
     if chance(4): T56(t, 2, 0); return        ; draw#2
2. Idle(aip(3))
```

- R47a. [C] The map, family `scimitar`, 240 cases, all with a draw, 5 boundaries; the controls fail the 35 and 120 that separate them. (run:2026-10-30-ai-cat-emu-3)

- R47i. [C] As data: kind 1, no `init`, no `alt`; 1 records (234 flyingscimitar); reach ·; `aip` set 1,2,3,4; `aidel` 15/13/10; skills Charge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R47l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R48. Row 48 `ZakarumZealot` (fn:sub_005F6E60_AiZakarumZealot@0x005F6E60)

**`aip`:** 1 melee after an attack: chance to attack again; 2 chance of A2 against A1 (50–65, as data); 3 the life percent below which it steps away (35–50, as data); 4 out of melee range: `not chance(4)` walks, else runs (50–90, as data).

```
1. run: i32 ← 0                                                            [I] (0x005F6E60, 0x005F6F7D)
   if Velocity > 0:
     run ← Run·100 ÷ Velocity − 100       ; i16 fields, signed idiv
     if run < 1: run ← 0
     if run ≥ 120: run ← 120
2. life ← UnitLifePct(U)
3. if t ≠ 0:
     p ← t
     if t.type = 1:
       MonsterOwnerRef(t, &guid, &type)
       if type = 0: p ← GameFindUnit(G, 0, guid)
     if p ≠ 0 and p.type = 0 and DRLG_ActFromLevelId(RoomGetLevelId(UnitGetRoom(U))) = 2
          and QUESTRECORD_GetState(PlayerData(p).quests[d], 21, 0):
       Ovr(0, run, 0)
       if StepAwayXY(t, 8, 1): return
       Ring(6); return
4. if St3or19:                                                             [I] (0x005F6F7D, 0x005F722F)
     if v18 = 0 and life < aip(3):
       v14 ← 0;  Ovr(0, run, 0)
       if StepAwayXY(t, 8, 1): return
       v18 ← 5
     if COLL_CellTestAt(UnitGetRoom(U), U.x, U.y, 0x40):
       if melee: T56(t, 4, 0)
       else: Walk(t, 7)
       return
5. if v18 ≠ 0: v18 ← v18 − 1
6. if not melee:
     v14 ← 0
     if not chance(4): Walk(t, 7); return     ; draw#1
     Ovr(0, run, 0);  RunToUnit(t); return
7. if v14 ≠ 0 and not chance(1):              ; draw#1, only when v14 ≠ 0
     v14 ← 0
     if Range(100) < 80: Idle(10); return     ; draw#2
     T56(t, 4, 0); return
8. v14 ← 1
9. SetModeAtUnit(chance(2) ? 5 : 4, t)        ; draw#1 or #2
```

- R48a. [I] **The act III truce.** In an act III level (act index 2) a zealot whose target is a player, or a monster whose owner record names a player (`MonsterOwnerRef` type 0, found by GUID), steps 8 away from it and wanders when that player's quest record of the game's difficulty has quest word 21 bit 0, the word the Durance portal tests. (fn:sub_0058F090_MonsterOwnerRef@0x0058F090, fn:DRLG_ActFromLevelId@0x006427F0, fn:UNIT_GetPlayerData@0x006221A0, fn:QUESTRECORD_GetState@0x0065C310, tbl:MonStats.txt:Run, tbl:MonStats.txt:Velocity)
- R48b. [I] With `MonsterData+0x54` 3 or 19 and life below `aip(3)` it steps away once and then holds a five-decision cooldown in `v18`; with that state and a cell that fails mask `0x40` it moves. Up to two draws. Not emulated: `UnitLifePct` is the first call (0x005F6EC6). (fn:COLL_CellTestAt@0x0064CB30, struct:AiCtl+0x18, tbl:MonStats.txt:aip3)

- R48i. [C] As data: kind 1, no `init`, no `alt`; 5 records (235-237 zealot1..zealot3, 671-672 zealot4..zealot5); reach P; `aip` set 1,2,3,4; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R48l. [I] Logged, not compared: 321 decisions (200 + 121) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-04-ai-r5, 0x005B186F)
- R48r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 121 of its own think's decisions in the rev 4 and rev 6 logs, 121 resumed, 0 mismatches, 0 stopped, 702 later calls matched, an unknown value deciding 360 of 702 later steps. The row is not under sentence H1. (run:2026-11-04-ai-r5)

#### R49. Row 49 `ZakarumPriest` (fn:sub_005F72D0_AiZakarumPriest@0x005F72D0)

**`aip`:** 1 melee: chance of A1, and the blocked line's draw; 2 chance of the Blizzard; 3 chance of `Skill2`; 4 clear line: chance to cast; 5 the Blizzard's cooldown (120 frames, as data), and a quarter of the teleport's (480); 6 the heal search's distance.

```
1. life ← UnitLifePct(U)                                                   [I] (0x005F72D0, 0x005F76F1)
2. if melee or St3or19:
     if Skill3 ≥ 0 and life < 33 and T > v14:              ; MonTeleport
       v14 ← T + 4·aip(5)
       s ← melee ? 2 : 0
       x ← t.x + ((t.x − U.x) << s);  y ← t.y + ((t.y − U.y) << s)
       if MonSkillTargetOk(Skill3, 0, x, y):
         MonAiUseSkill(Sk3mode, Skill3, 0, x, y); return
     if melee and chance(1): SetModeAtUnit(4, t); return   ; draw#1
3. s ← {unit 0, count 0, best 0x7FFFFFFF, bound aip(6)²}
   AiUnitSearch(G, U, &s, AiZakarumHealCb, 1)
4. if Skill1 ≥ 0 and s.unit ≠ 0 and D100() < 25:           ; ZakarumHeal, unsigned compare
     UseSkill1(s.unit); return
5. if not AiLineClear(U, t):
     if chance(1) and Skill4 ≥ 0 and v18 < T and Range(100) < aip(2): goto blizzard
   else if chance(4):
     if Skill4 ≥ 0 and v18 < T and Range(100) < aip(2):
   blizzard:
       UseSkill4(t);  v18 ← T + aip(5); return             ; MonBlizzard
     if Skill2 ≥ 0 and v1C < T and Range(100) < aip(3):
       UseSkill2(t);  v1C ← T + 20; return                 ; ZakarumLightning
6. if D100() < 30: T56(t, 4, 0); return
7. Idle(20)
```

- R49a. [I] **The teleport** goes to the far side of the target: the target's point plus the unit-to-target offset, ×4 in melee range, ×1 otherwise. The first `GetSubX/Y` pair is the unit's, the second the target's (`ECX` = `[ebp−4]` then `[ebp+8]`, 0x005F7350–0x005F737B). The offset is a u16 difference, so `<< 2` cannot wrap. A blocked line (`AiLineClear` 0: `UnitLineBlocked(U, t, 4)` non-zero) allows only Blizzard. Up to six draws. Not emulated: `UnitLifePct` is the first call (0x005F72F9). (fn:sub_005FD470_MonSkillTargetOk@0x005FD470, fn:sub_005DD290_AiLineClear@0x005DD290, fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0, struct:AiCtl+0x1C)
- R49b. [I] **`AiZakarumHealCb`** takes a monster other than the searcher, `AlignSame02` with it, alignment not 2, not in a death mode, whose `MonClassCheck(MonBaseId)` is 235 (`zealot1`) or 238 (`cantor1`), with `UnitDistSq ≤ bound` and `UnitLifePct ≤ 60`; each such unit adds one to `+0x04` and becomes `+0x00`, since `+0x08` stays `0x7FFFFFFF` (written only when below 1) and every life is below it. It returns 0, so the search goes on: the unit kept is the last taken. Block `{+0x00 unit, +0x04 count, +0x08 best, +0x0C bound}` at `EBP − 0x4C`. (fn:sub_005F7240_AiZakarumHealCb@0x005F7240, fn:sub_00650D70_AlignSame02@0x00650D70, fn:sub_006259B0_UnitAlignGet@0x006259B0, fn:sub_00463900_MonClassCheck@0x00463900)

- R49i. [C] As data: kind 1, no `init`, no `alt`; 6 records (238-241 cantor1..cantor4, 673-674 cantor5..cantor6); reach P; `aip` set 1,2,3,4,5,6; `aidel` 15/14/13; skills ZakarumHeal, ZakarumLightning, MonTeleport, MonBlizzard. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R49l. [I] Logged, not compared: 74 decisions (57 + 17) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-04-ai-r5, 0x005B186F)
- R49r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 17 of its own think's decisions in the rev 4 and rev 6 logs, 17 resumed, 0 mismatches, 0 stopped, 65 later calls matched, an unknown value deciding 0 of 65 later steps. The row is not under sentence H1. (run:2026-11-04-ai-r5)

#### R52. Row 52 `FrogDemon` (fn:sub_005F8260_AiFrogDemon@0x005F8260)

**`aip`:** 1 melee: chance of A1, after `aip(2)`; 2 melee: chance of A2; 3 melee: chance of a `T56` walk; 4 chance of a `T56` walk out of it; 5 within `aip(6)`: chance of A2; 6 that distance; 7 the delay; 8 submerged: the distance at which it surfaces (9, as data).

`v1C`: 0 start, 1 submerged, 2 surfaced. `Skill1` is `Submerge`, `Skill2` `Emerge`.

```
1. if v1C = 0:                                                             [I] (0x005F8260, 0x005F85B8)
     if Skill1 ≥ 0 and dist > 12:
       UseSkill1(t);  Delay(8);  v1C ← 1;  AiVultureTakeOff(G, U); return
     if Skill2 ≥ 0 and AiVultureLand(G, U): goto emerge
     if not COLL_CellTestAt(UnitGetRoom(U), U.x, U.y, 0xC01): v1C ← 2
     Idle(12); return
2. if v1C = 1:
     if Skill2 ≥ 0 and ((dist < aip(8) and AiVultureLand(G, U))
                        or (dist < 20 and v18 > 64 and AiVultureLand(G, U))):
   emerge:
       MonAiUseSkill(Sk2mode, Skill2, U, 0, 0);  v1C ← 2; return
     AiVultureTakeOff(G, U);  Delay(24);  v18 ← v18 + 1;  v1C ← 1; return
3. if t = 0: Delay(32); return
4. if melee:
     if Range(100) < aip(2): SetModeAtUnit(5, t); return
     if Range(100) < aip(1): SetModeAtUnit(4, t); return
     if Range(100) < aip(3): T56(t, 3, 0); return
     Delay(aip(7)); return
5. if dist < aip(6):
     if Range(100) < aip(5): SetModeAtUnit(5, t); return
     if Range(100) < aip(4): T56(t, 4, 0); return
     Delay(aip(7)); return
6. if Range(100) < aip(4): T56(t, 3, 0); return
7. WalkStop(t, 4)
```

The alt, [I] (0x005F81D0, 0x005F8254, fn:sub_005B0E00_MonAiInit@0x005B0E00):

```
if ctl.state ≠ 10 and ctl.state ≠ 11 and Skill1 ≥ 0 and v1C ≥ 2:
  UseSkill1(t);  v1C ← 1;  AiVultureTakeOff(G, U); return
MonAiInit(G, U, ctl, ctl.state);  Delay(1)
```

- R52a. [I] The frog uses the vulture's take-off and landing helpers, the collision off and on, for its submerge and emerge. Each failed submerged event adds one to `v18`. Kind 5: with no target a surfaced frog delays 32. The `alt` runs when `MonAiInit` swaps the think: a surfaced frog whose state changes to anything but 10 or 11 submerges first. The skill's `x, y` are 0 (the pushed `EDX` is the zero `v1C`, 0x005F82A7). Up to three draws. (fn:sub_005F2EB0_AiVultureTakeOff@0x005F2EB0, fn:sub_005F2FC0_AiVultureLand@0x005F2FC0, struct:AiCtl+0x1C)
- R52b. [C] Both maps up to the first callee, the landing helper, the cell test (its stack arguments, room, `U.x`, `U.y`, `0xC01`), the take-off, the commands and delays: families `frog` (240 cases, 95 with a draw, 14 boundaries; the controls fail the 18 and 54 that separate them) and `frogalt` (240 cases, no draw, 2 boundaries, so no control separates it, and its `[C]` is the map of its state tests only). (run:2026-10-30-ai-cat-emu-3)

- R52i. [C] As data: kind 5, no `init`, `alt` 0x005F81D0; 3 records (247-249 frogdemon1..frogdemon3); reach P; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills Submerge, Emerge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R52l. [C] First boundary: 600 decisions compared (200 + 400), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R52r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 400 of its own think's decisions in the rev 4 and rev 6 logs, 400 resumed, 0 mismatches, 0 stopped, 406 later calls matched, an unknown value deciding 0 of 406 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### R56. Row 56 `Tentacle` (fn:sub_005F8F80_AiTentacle@0x005F8F80)

**`aip`:** 1 melee: chance of A1; 2 out of melee range: chance to submerge; 3 the submerged minimum, in 25-frame units (300–400 frames, as data); 4 the surfaced minimum, the same units; 5 the wait; 6 the distance past which it submerges and within which it surfaces.

`v1C`: 0 start, 1 submerged, 2 surfaced. `Skill1` is `Submerge`, `Skill2` `Emerge`.

```
1. o ← MonsterOwner(U)                                                     [I] (0x005F8F80, 0x005F9263)
2. if o = 0: UnitKilled(G, U, 0, 1); return
3. if o.mode = 12 and D100() < 40:              ; draw#1, unsigned
     UnitKilled(G, U, UNIT_GetTargetUnit(G, o), 1); return
4. if Skill1 ≥ 0:
     if v1C = 0: goto submerge8
     if v1C = 2 and v18 < T and (dist > aip(6) or (not melee and Range(100) < aip(2))
                                 or (o.mode = 14 and Range(100) < 50)):
   submerge8:
       UseSkill1(t);  Delay(8);  v18 ← T + 25·aip(3);  v1C ← 1; return
5. if Skill2 ≥ 0:
     if v1C ≠ 1: goto act
     if v18 < T and (melee or dist < aip(6) or (o.mode ≠ 14 and Range(100) < 5)):
       MonAiUseSkill(Sk2mode, Skill2, U, 0, 0);  v18 ← T + 25·aip(4);  v1C ← 2; return
6. if v1C = 1: Delay(aip(5)); return
act:
7. if melee and Range(100) < aip(1): SetModeAtUnit(4, t); return
8. Idle(aip(5))
```

- R56a. [I] A tentacle follows its owner, the head (row 57): it dies with none, and with 40 percent per event once the owner is in mode 12, the owner's target the killer; it submerges with 50 percent while the owner is in mode 14 and surfaces by itself (5 percent) only while it is not. `25·aip` is 32-bit and fits for every i16; the sum with `T` wraps only past frame `2³¹ − 819 176`. Up to four draws. Not emulated: `MonsterOwner`'s `GameFindUnit` comes before the first draw (0x005F8FAC). (fn:sub_0058F0D0_MonsterOwner@0x0058F0D0, struct:AiCtl+0x18)

- R56i. [C] As data: kind 2, no `init`, no `alt`; 3 records (258-260 tentacle1..tentacle3); reach ·; `aip` set 1,2,3,4,5,6; `aidel` 15/15/15; skills Submerge, Emerge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R56l. [I] Logged, not compared: 16 decisions (16) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, 0x005B186F)

#### R57. Row 57 `TentacleHead` (fn:sub_005F9270_AiTentacleHead@0x005F9270)

**`aip`:** as row 56 for 2, 3, 4, 5, 6 (`aip(6)` 12–14, as data), and 1 the chance of A1 at its own hostile.

```
1. if Skill1 ≥ 0:                                                          [I] (0x005F9270, 0x005F947E)
     if v1C = 0:
       UseSkill1(t);  Delay(8);  goto arm
     if v1C = 2 and v18 < T and (dist > aip(6) or (not melee and Range(100) < aip(2))):
       UseSkill1(t);  Delay(20)
   arm:
       v18 ← T + 25·aip(3);  v1C ← 1; return
2. if Skill2 ≥ 0 and v1C = 1 and v18 < T and (melee or dist < aip(6)):
     MonAiUseSkill(Sk2mode, Skill2, U, 0, 0);  v18 ← T + 25·aip(4);  v1C ← 2; return
3. if v1C = 1: Delay(aip(5)); return
4. r ← dist;  h ← FindHostile(&r, 0)
5. if chance(1): SetModeAtUnit(4, h); return      ; the draw after the search
6. Idle(aip(5))
```

- R57a. [I] The head surfaces only when the target is close, never by chance, and its A1 is aimed at its own hostile `h`, which may be 0 when `FindHostile` finds none: the call is made with it. Its later submerges delay 20, the first 8. (fn:sub_005DDC30_MonAiFindHostile@0x005DDC30)
- R57b. [C] The map up to the skills, the delay or `FindHostile` (the word at its pointer argument, `EBP − 4`, holding `dist`): family `thead`, 240 cases, 18 with a draw, 5 boundaries; the controls fail the 3 and 27 that separate them. (run:2026-10-30-ai-cat-emu-3)

- R57i. [C] As data: kind 2, no `init`, no `alt`; 3 records (261-263 tentaclehead1..tentaclehead3); reach ·; `aip` set 1,2,3,4,5,6; `aidel` 15/15/15; skills Submerge, Emerge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R57l. [C] First boundary: 8 decisions compared (8), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, 0x005B186F)

#### R63. Row 63 `GargoyleTrap` (fn:sub_005F9490_AiGargoyleTrap@0x005F9490)

**`aip`:** 1 the shooting range (24–28, as data); 2 chance to shoot (20/50/80, as data); 3 the idle after a shot (12/10/8 frames, as data); 4 the idle after no shot (15/7/0, as data).

```
1. if v14 > 0: Idle(v14);  v14 ← 0; return       ; the cooldown after a shot  [I] (0x005F9490, 0x005F96B0)
2. UnitSetPathTargetUnit(U, t)
3. dx ← t.x − U.x;  dy ← t.y − U.y
   (px, py) ← |dx| < |dy| ? (U.x, t.y) : (t.x, U.y)       ; on the unit's row or column
4. PathSetFacing(U.path, g_FacingOfClass4[g_FacingClass64[(u8) UnitDirToPoint(U, px, py)]])
5. if (|dx| ≤ 5 or |dy| ≤ 5) and Skill1 ≥ 0 and dist < aip(1) and chance(2):  ; draw#1
     UseSkill1(t);  v14 ← aip(3); return
6. Idle(aip(4))
```

- R63a. [I] The trap turns to one of four facings and shoots only at a target within 5 subtiles of its row or column. `UnitDirToPoint`'s low byte indexes the 64-byte table, whose quarter indexes the four bytes: directions 57–63 and 0–8 → 31, 9–24 → 49, 25–40 → 0, 41–56 → 17. (fn:sub_00621DC0_UnitDirToPoint@0x00621DC0, fn:sub_006488A0_PathSetFacing@0x006488A0, data:g_FacingClass64@0x006E3540, data:g_FacingOfClass4@0x006E353C)
- R63b. [C] The cooldown test up to `Idle` or `UnitSetPathTargetUnit` only: family `garg`, 240 cases, no draw before them, 2 boundaries, so no control separates it. (run:2026-10-30-ai-cat-emu-3)

- R63i. [C] As data: kind 1, no `init`, no `alt`; 1 records (273 gargoyletrap); reach ·; `aip` set 1,2,3,4; `aidel` 15/15/15; skills GargoyleTrap. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R63l. [C] First boundary: 145 decisions compared (91 + 54), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R63r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 54 of its own think's decisions in the rev 4 and rev 6 logs, 54 resumed, 0 mismatches, 0 stopped, 147 later calls matched, an unknown value deciding 0 of 147 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

### Batch 4: pool-D (`SkeletonMage` to the traps)

#### R64. Row 64 `SkeletonMage` (fn:sub_005F96C0_AiSkeletonMage@0x005F96C0)

Tier AI: [machinery § T64](machinery.md#t64-row-64-skeletonmage-fnsub_005f96c0_aiskeletonmage0x005f96c0), not repeated here.

#### R65. Row 65 `FetishShaman` (fn:sub_005F9A80_AiFetishShaman@0x005F9A80)

**`aip`:** 1 chance of the revive; 2 the revive filter (0/1/2 to 0/2/3, as data); 3 the **squared** distance past which it walks to the corpse (15/16/18 to 15/18/22, as data); 4 chance of a `T56` walk (66, as data); 5 the search radius (50, as data).

```
1. n ← 1                                                                   [I] (0x005F9A80, 0x005F9AAB, 0x005F9ADA, 0x005F9CE6)
   if Skill1 ≥ 0:
     s ← SkillFindByOwner(U, Skill1, −1)
     if s ≠ 0:
       lv ← SKILLS_GetSkillLevel(U, s, 1)
       if lv > 0: n ← lv
2. if Skill1 ≥ 0 and dist < n and not HasState(U, 12):
     blk.kind ← 1;  blk+0x0C ← t ≠ 0 ? t.guid : −1;  blk+0x10 ← t ≠ 0 ? t.type : 6
     MonHelpBlock(U, &blk)
     UseSkill1(t); return                                     ; the breath, FetishInferno
3. if HasState(U, 12): State(12, 0)
4. s ← {dead 0, deadD2 0x7FFFFFFF, r2 aip(5)·aip(5), live 0, liveD2 0x7FFFFFFF, count 0, filter aip(2)}
   AiUnitSearch(G, U, &s, AiFetishReviveCb, 1)
5. if s.dead ≠ 0 and chance(1) and MonSkillTargetOk(Skill3, s.dead, 0, 0):   ; draw#1
     blk.kind ← 14;  blk+0x0C ← s.dead.guid;  blk+0x10 ← 1
     MonHelpBlock(U, &blk)
     if s.deadD2 > aip(3): WanderNear(s.dead, 10); return
     MonAiUseSeqSkill(Skill3, s.dead, 0, 0); return           ; Resurrect2
6. if chance(4): T56(t, 4, 0); return                         ; draw#1 or #2
7. Idle(10)
```

The alt, [I] (0x005F9950, 0x005F9999, fn:STATE_Set@0x00639DB0, fn:sub_005B0E00_MonAiInit@0x005B0E00):

```
if HasState(U, 12): State(12, 0)         ; state 12 `inferno`
MonAiInit(ctl, ctl.state)
Idle(1)
```

- R65a. [I] The breath is used while the target is nearer than the skill's level, 7–11 in Normal by the records' `Sk1lvl` before any level bonus, or 1 when the unit has no such skill or the level is below 1. (fn:sub_006439B0_SkillFindByOwner@0x006439B0, fn:SKILLS_GetSkillLevel@0x006442A0, fn:sub_005FD470_MonSkillTargetOk@0x005FD470, fn:sub_0058F730_MonHelpBlock@0x0058F730, fn:sub_005DE000_MonAiUseSeqSkill@0x005DE000)
- R65b. [I] `aip(3)` is compared with a squared distance (`cmp [ebp-0x4c], aip3`, 0x005F9C41: `deadD2` from the callback's `UnitDistSq`). (fn:sub_005B0BD0_UnitDistSq@0x005B0BD0)
- R65c. [I] **`AiFetishReviveCb`** takes a candidate that is not the unit, is a monster (type 1) with `Unit+0xC4` bit `0x02`, is not in state set 33, and, when `s.filter` is 0, whose owner is the shaman (`MonsterOwner(cand) = U`); whose class by `MonClassCheck(MonBaseId(cand))` is 141 (`fetish1`), or 396 (`fetishblow1`) unless the filter is 1; of alignment 0; for a filter below 3 not of the `MonTypeFlag(cand, 12)` type; and within `UnitDistSq ≤ s.r2`. A candidate in mode 12 replaces `s.dead` when strictly nearer; any other counts in `s.count` and replaces `s.live` when strictly nearer. It returns 0, so the search goes on. The think reads only `s.dead` and `s.deadD2`. No draw. (fn:sub_005F99A0_AiFetishReviveCb@0x005F99A0, fn:sub_0063A770_UnitHasStateSet33@0x0063A770, fn:sub_0058F0D0_MonsterOwner@0x0058F0D0, fn:sub_00463900_MonClassCheck@0x00463900, fn:sub_005A0180_MonTypeFlag@0x005A0180)
- R65d. [I] So the filter widens with difficulty: 0 (Normal in every record) revives only the shaman's own minions, 1 any `fetish1`-based dead, 2 also the `fetishblow1` base, 3 (Hell in `fetishshaman4..8`) drops the type test. (0x005F99E8, 0x005F9A36, tbl:MonStats.txt:aip2)
- R65e. [I] The blocks' `+0x0C` and `+0x10` are the guid and the type, the order row 30 `Fetish` reads as `GameFindUnit(G, rec+0x10, rec+0x0C)`; the kind-14 block's `+0x10` = 1 is the monster type. `+0x14` and `+0x18` are left as the stack held them. Whether the call reaches fetish minions is Open questions. (0x005F9AE8, 0x005F9B0E, 0x005F9C14, 0x005F9C2C, 0x005F5424)
- R65f. [C] Two maps only: the skill-sign test up to `SkillFindByOwner(U, Skill1, −1)` (0x005F9AB2) or, for `Skill1 < 0`, `HasState(U, 12)` (0x005F9B4B), family `fetish`; and the alt's entry call `HasState(U, 12)` from 0x005F9965, family `fetishalt`. Each 240 cases, no draw and no compare before the calls, so no control separates them. (run:2026-10-30-ai-cat-emu-4)

- R65i. [C] As data: kind 1, no `init`, `alt` 0x005F9950; 8 records (278-282 fetishshaman1..fetishshaman5, 662-664 fetishshaman6..fetishshaman8); reach PU; `aip` set 1,2,3,4,5; `aidel` 15/14/13; skills FetishInferno, FetishAura, Resurrect2. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R65l. [C] First boundary: 104 decisions compared (15 + 27 + 62), 0 mismatches, 1 first-call outcome. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R65r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 89 of its own think's decisions in the rev 4 and rev 6 logs, 89 resumed, 0 mismatches, 0 stopped, 370 later calls matched, an unknown value deciding 0 of 370 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R66. Row 66 `SandMaggotQueen` (fn:sub_005F9CF0_AiSandMaggotQueen@0x005F9CF0)

**`aip`:** 1 the brood size (7/8/9 in `maggotqueen1` up to 11/12/13 in 5, as data); 2 the delay, and with 25 the idle (12 down to 4, as data).

```
1. if v1C ≠ 0: Idle(25·aip(2));  v1C ← 0; return                 ; i32 product  [I] (0x005F9CF0, 0x005F9E1E)
2. if v18 = 0:
     if v14 < aip(1):
       MoveToPoint(U.x, U.y, 8);  Delay(aip(2));  v18 ← 1
     return                                                      ; the brood is complete: no command
3. SpawnClassByBase(U, &cls, &x, &y, &mode, 0, MonLinkClass3C)
4. room ← RoomAtSubtile(UnitGetRoom(U), x, y)
   if room ≠ 0:
     m ← SpawnAtPos(G, room, x, y, cls, mode, 2, 0x42)
     if m ≠ 0: m+0xC4 ← m+0xC4 | 0x4000000;  v14 ← v14 + 1
5. Delay(aip(2));  v18 ← 0;  v1C ← 1
```

- R66a. [I] A three-event cycle while fewer than `aip(1)` young were spawned: a move at its own position with 8, then the spawn, then `Idle(25·aip(2))`. `v14` counts successful spawns only. No draw. The row is kind 0: the think runs with no target search. (fn:sub_005DE440_MonAiMoveToPoint@0x005DE440, fn:sub_0063EFA0_SpawnClassByBase@0x0063EFA0, fn:sub_00463740_RoomAtSubtile@0x00463740, fn:sub_005B2F20_SpawnAtPos@0x005B2F20)
- R66b. [C] The map of `AiCtl+0x14/+0x18/+0x1C` to `Idle` (0x005F9D1D), `MoveToPoint` (0x005F9D5D, `U.x`, `U.y` read through `UnitGetSubX/Y`), `SpawnClassByBase` (0x005F9DA8, its seven stack arguments) or the return: family `queen`, 240 cases, 3 boundaries and the return; the Normal-column and compare controls fail the 64 and 29 that separate them. The write of `v1C ← 0` after the `Idle` and every write after a boundary are not covered. (run:2026-10-30-ai-cat-emu-4)

- R66i. [C] As data: kind 0, no `init`, no `alt`; 5 records (284-288 maggotqueen1..maggotqueen5); reach U; `aip` set 1,2; `aidel` 15/15/15; skills MagottUp, MagottDown, MagottLay, QueenDeath. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R66l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R68. Row 68 `VileMother` (fn:sub_005FA010_AiVileMother@0x005FA010)

**`aip`:** 1 the lifetime count of spawn events (16–22, as data); 2 the most near children (5/6, as data); 3 chance to place; 4 melee: chance of A1 (80–95, as data); 5 `D100() ≥ aip(5)` gives the wander branch (70/60/50, as data); 6 chance of a `T56` walk (30, as data); 7 the wait in melee range.

```
1. pos ← MONSTATS_GetClassChainPos(U ≠ 0 ? U.class : −1, 0, 0)             [I] (0x005FA010, 0x005FA270)
2. child ← MonClassChainStep(count > 301 ? 301 : −1, pos)       ; 301 `vilechild1`
3. if v14 < aip(1) and UnitAlignGet(U) = 0 and chance(3):       ; draw#1
     s ← {child, 25, 0};  AiUnitSearch(G, U, &s, 0, 12)         ; kind 12: living `child` within 25
     if s.count < aip(2) and AiVileMotherSpawn(G, U, t, M):
       v14 ← v14 + 1; return
4. if melee:
     if chance(4): SetModeAtUnit(4, t); return                  ; draw#1 or #2
     Idle(aip(7)); return
5. if v14 < aip(1) and D100() ≥ aip(5):                         ; draw#1 or #2
     if chance(6): T56(t, 4, 0); return                         ; draw#2 or #3
     Idle(15); return
6. Walk(t, 7)
```

- R68a. [I] The mother's child class is the class at her own chain position in `vilechild1`'s chain. The `ECX` of `MonClassChainStep` is `(count > 0x12D) ? 0x12D : −1` (0x005FA052–0x005FA06A). (fn:MONSTATS_GetClassChainPos@0x006510C0, fn:sub_0054DA60_MonClassChainStep@0x0054DA60, fn:sub_006259B0_UnitAlignGet@0x006259B0)
- R68b. [I] **`AiVileMotherSpawn(game, unit, t, M)`:** the direction from the unit to the target (`UnitDirToPoint`, 64 steps) cut to eight (`Dir64To8`); for eight tries from that direction, the try's 8-direction index `k & 7` maps through the stack table `{6, 4, 2, 2, 2, 0, 6, 6}` to a `DirOffset` direction, the cell is the unit's position plus three times that offset, and when `Skill1 ≥ 0` and `SpawnClassCellTest` (class `MONSTATS_ValidId(298)`, `vilemother1`) accepts the cell, `MonAiUseSkill(Sk1mode, Skill1, 0, x, y)` and return 1; after eight refusals, 0. No draw. (fn:sub_005F9E30_AiVileMotherSpawn@0x005F9E30, fn:sub_00621DC0_UnitDirToPoint@0x00621DC0, fn:sub_0063E7A0_Dir64To8@0x0063E7A0, fn:sub_0063E7E0_DirOffset@0x0063E7E0, fn:MONSTATS_ValidId@0x004E6C50, fn:sub_005FD350_SpawnClassCellTest@0x005FD350)
- R68c. [C] The entry call `MONSTATS_GetClassChainPos(U.class, 0, 0)` from 0x005FA045 only, before any test: family `vmother`, 240 cases; no control separates it. (run:2026-10-30-ai-cat-emu-4)

- R68i. [C] As data: kind 1, no `init`, no `alt`; 5 records (298-300 vilemother1..vilemother3, 675-676 vilemother4..vilemother5); reach PU; `aip` set 1,2,3,4,5,6,7; `aidel` 15/14/13; skills Nest. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R68l. [C] First boundary: 150 decisions compared (71 + 79), 0 mismatches, 1 first-call outcome. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R68r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 79 of its own think's decisions in the rev 4 and rev 6 logs, 79 resumed, 0 mismatches, 0 stopped, 259 later calls matched, an unknown value deciding 0 of 259 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### R69. Row 69 `VileDog` (fn:sub_005FA280_AiVileDog@0x005FA280)

**`aip`:** 1 melee: chance of A1 (80/85/90, as data); 2 the melee wait (10, as data); 3 out of melee range: chance to walk (80/85/90, as data).

```
1. if v14 = 0: v14 ← 1;  Idle(5); return                ; the first event after the spawn  [I] (0x005FA280, 0x005FA37A)
2. if melee:
     if chance(1): SetModeAtUnit(4, t); return          ; draw#1
     Idle(aip(2)); return
3. if chance(3): Walk(t, 7); return                     ; draw#1
4. Idle(10)
```

- R69a. [C] The map, `AiCtl+0x14` included: family `vdog`, 240 cases, 200 with a draw, 5 boundaries; the controls fail the 34 and 69 that separate them. (run:2026-10-30-ai-cat-emu-4)

- R69i. [C] As data: kind 1, no `init`, no `alt`; 10 records (10 records, as the index lists them); reach ·; `aip` set 1,2,3; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R69l. [C] First boundary: 198 decisions compared (120 + 78), 0 mismatches, 5 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R69r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 78 of its own think's decisions in the rev 4 and rev 6 logs, 78 resumed, 0 mismatches, 0 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### R70. Row 70 `FingerMage` (fn:sub_005FA380_AiFingerMage@0x005FA380)

**`aip`:** 1 melee: chance of A1; 2 chance of `Skill1`, `FingerMageSpider`; 3 the life percent above which the flight ends (50–70, as data); 4 the life percent below which an ownerless mage flees (30–50, as data); 5 the skill range (15/20/26, as data); 6 the flight's most events (5, as data); 7 the walk's limit (40, as data); 8 the idle (12/10/8, as data).

```
1. life ← UnitLifePct(U)                                                   [I] (0x005FA380, 0x005FA68A)
2. p ← Velocity > 0 ? min(max(Run·100 ÷ Velocity − 100, 0), 120) : 0       ; i16 columns, idiv
3. if St3or19:
     v14 ← 0
     if melee: SetModeAtUnit(4, t); return
     if Skill1 ≥ 0 and dist < aip(5): UseSkill1(t); return
4. if v14 = 1:                                                             ; fleeing
     v18 ← v18 + 1
     if life > aip(3) or D100() < 25 or v18 > aip(6): v14 ← 0              ; draw#1, only when life ≤ aip(3)
     else if dist < 14:
       Ovr(0, p, 0);  StepAway(t, 14, 0); return
     Idle(15); return
5. if MonsterOwner(U) = 0 and life < aip(4):
     v14 ← 1;  v18 ← 0;  StepAway(t, 9, 0); return
6. if melee:
     if chance(1): SetModeAtUnit(4, t); return                             ; draw#1
     if Skill1 ≥ 0 and rchance(2): UseSkill1(t); return                    ; draw#2
     T56(t, 5, 0); return
7. if dist ≥ aip(5):
     if dist < aip(7): Walk(t, 7); return
     Idle(15); return
8. if Skill1 ≥ 0 and rchance(2): UseSkill1(t); return                      ; draw#1
9. if HasState(t, 84): Walk(t, 0); return                                  ; state 84 `fingermagecurse`
10. Idle(aip(8))
```

- R70a. [I] `p` is the run speed's excess over the walk speed in percent, 0–120: `q = Run·100 ÷ Velocity − 100` (signed `idiv`), `q ≤ 0 → 0`, `q ≥ 120 → 120` (0x005FA3B0–0x005FA3E7). (fn:sub_00621F20_UnitLifePct@0x00621F20, fn:sub_005DD2B0_AiMonState3or19@0x005DD2B0, tbl:MonStats.txt:Velocity, tbl:MonStats.txt:Run)
- R70b. [C] The entry call `UnitLifePct(U)` from 0x005FA3AB only, before any test: family `fmage`, 240 cases; no control separates it. (run:2026-10-30-ai-cat-emu-4)

- R70i. [C] As data: kind 1, no `init`, no `alt`; 5 records (304-306 fingermage1..fingermage3, 692-693 fingermage4..fingermage5); reach PU; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills FingerMageSpider. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R70l. [C] First boundary: 274 decisions compared (120 + 99 + 55), 0 mismatches, 1 first-call outcome. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R70r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 154 of its own think's decisions in the rev 4 and rev 6 logs, 154 resumed, 0 mismatches, 0 stopped, 481 later calls matched, an unknown value deciding 0 of 481 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R71. Row 71 `Regurgitator` (fn:sub_005FA710_AiRegurgitator@0x005FA710)

**`aip`:** 1 melee: chance of A1; 2 a corpse nearer than 9 (squared): chance to eat; 3 out of melee range: chance to walk at `t`; 4 the late chance to eat; 5 the second chance to eat; 6 the corpse radius.

`v14`: 0 idle, 1 looking, 2 walking, 3 eating, 4 after the meal, 5 stepping away. `v18` the corpse's guid; `v1C` a walk count, six at most.

```
clear ≝ v14 ← 0;  v18 ← 0;  v1C ← 0                                        [I] (0x005FA710, 0x005FAA8A)

1. switch v14:
     5: StepAway(t, 16, 1);  v14 ← 0; return
     2: m ← GameFindUnit(G, 1, v18)
        if m = 0 or m.mode ≠ 12: clear;  Ring(8); return
        if UnitDistSq(U, m) > 4:
          if v1C ≥ 6: clear;  Ring(8); return
          WalkStop(m, 1);  v1C ← v1C + 1
        v14 ← 3;  Idle(8); return
     3: m ← GameFindUnit(G, 1, v18)
        if Skill1 ≥ 0 and m ≠ 0 and m.mode = 12: UseSkill1(m);  v14 ← 4; return
        clear;  Ring(8); return
     4: if not melee: SetModeAtUnit(5, t);  v14 ← 5; return
        StepAway(t, 8, 1); return
2. s ← {0, aip(6)·aip(6)};  AiUnitSearch(G, U, &s, AiRegurgitatorCb, 1)
3. if v14 = 1:
     if s.found ≠ 0:
       v18 ← s.found.guid
       if UnitDistSq(U, s.found) > 2: WalkStop(s.found, 1);  v14 ← 2;  v1C ← 0; return
       Idle(8);  v14 ← 3;  v1C ← 0; return
     if Range(100) < 20: clear; return                       ; draw#1
     Ring(8); return
4. if s.found ≠ 0:
     if UnitDistSq(U, s.found) < 9 and rchance(2): goto eat  ; draw#1
     if rchance(5): goto eat                                 ; draw#1 or #2
5. r ← Range(100)                                            ; draw#1..#3
6. if melee:
     if r < aip(1): SetModeAtUnit(4, t); return
     Idle(15); return
7. if r < aip(3): Walk(t, 0); return
8. if s.found ≠ 0 and rchance(4): goto eat                   ; draw#2..#4
9. Idle(8); return
eat:
   WalkStop(s.found, 1);  v14 ← 2;  v18 ← s.found.guid;  v1C ← 0
```

- R71a. [I] Nothing in the function sets `v14` to 1: its twelve stores write 0, 2, 3, 4 or 5; only the search path tests it. Whether another path does is Open questions. Up to four `Range(100)` draws in one decision. The `GameFindUnit` type in `EDX` is 1, computed as `state − 1` and `state − 2` (0x005FA767, 0x005FA803). (fn:sub_00552F60_GameFindUnit@0x00552F60, fn:sub_005DE200_MonAiWanderRing@0x005DE200, fn:RNG_Range@0x0045C390)
- R71b. [I] **`AiRegurgitatorCb`** takes a monster other than the unit with `Unit+0xC4` bit `0x200` clear and bit `0x02` set, in a death mode, not in state set 33, of alignment 0, with the MonStats2 flag `MonStats2FlagTest` tests, within `UnitDistSq ≤ s.r2`; it keeps the last such candidate at or nearer than the current best (`jg` skips, so ties replace). No draw. (fn:sub_005FA690_AiRegurgitatorCb@0x005FA690, fn:sub_0063EA40_MonIsDeathMode@0x0063EA40, fn:sub_004638A0_MonStats2FlagTest@0x004638A0)
- R71c. [C] The state dispatch only: states 5, 2, 3 and 4 (both melee cases) to their first callee and the search's block (`{0, aip(6)²}` at `EBP−0x34`, callback 0x005FA690, kind 1) for every other value, no draw before them: family `regurg`, 240 cases, 6 boundaries; the Normal-column control fails the 77 it separates, the search radius. (run:2026-10-30-ai-cat-emu-4)

- R71i. [C] As data: kind 1, no `init`, no `alt`; 4 records (307-309 regurgitator1..regurgitator3, 694 regurgitator4); reach PU; `aip` set 1,2,3,4,5,6; `aidel` 15/14/13; skills RegurgitatorEat. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R71l. [C] First boundary: 53 decisions compared (44 + 9), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R71r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 9 of its own think's decisions in the rev 4 and rev 6 logs, 9 resumed, 0 mismatches, 0 stopped, 14 later calls matched, an unknown value deciding 0 of 14 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### R72. Row 72 `DoomKnight` (fn:sub_005FAA90_AiDoomKnight@0x005FAA90)

**`aip`:** 1 melee: chance of A1 (90/95/100, as data); 2 the melee wait (10/5/5, as data); 3 out of melee range: chance of the type-13 walk (80/85/90, as data); 4 the wait out of it (10, as data).

```
1. if not melee:                                                           [I] (0x005FAA90, 0x005FAB74)
     if chance(3): Walk13(t, 7); return     ; draw#1
     Idle(aip(4)); return
2. if chance(1): SetModeAtUnit(4, t); return ; draw#1
3. Idle(aip(2))
```

- R72a. [C] The map, family `dknight`, 240 cases, all with a draw, 4 boundaries; the controls fail the 27 and 136 that separate them. (run:2026-10-30-ai-cat-emu-4)

- R72i. [C] As data: kind 1, no `init`, no `alt`; 3 records (310 doomknight1, 699-700 dkfig1..dkfig2); reach P; `aip` set 1,2,3,4; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R72l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R73. Row 73 `AbyssKnight` (fn:sub_005FAB80_AiAbyssKnight@0x005FAB80)

**`aip`:** 1 the life percent below which it casts its armour (40/75/100, as data); 2 chance of that (80, as data); 3 melee: chance of A1 (90/94/97, as data); 4 the melee wait; 5 the distance inside which the countdown arms (6/6/5, as data); 6 the countdown (1/1/0, as data); 7 chance of the walk (70/65/50, as data); 8 the distance inside which it `T56` walks (40, as data).

```
1. life ← UnitLifePct(U)                                                   [I] (0x005FAB80, 0x005FAE32)
2. if Skill2 in [0, Skills count) and (st ← Skills[Skill2].aurastate) ≥ 0 and not HasState(U, st)
      and life < aip(1) and rchance(2):                  ; draw#1
     MonAiUseSkill(Sk2mode, Skill2, 0, 0, 0); return     ; MonBoneArmor
3. if melee:
     if chance(3): SetModeAtUnit(4, t); return           ; draw#1 or #2
     Idle(aip(4)); return
4. if dist < aip(5) and v14 ≤ 0: v14 ← aip(6)
5. if Skill1 ≥ 0 and v14 = 0 and not (U is a monster with MonsterData+0x0E ≥ 4):
     UseSkill1(t);  v14 ← aip(6); return                 ; DoomKnightMissile
6. if v14 > 0: v14 ← v14 − 1
7. if chance(7):                                         ; draw#1 or #2
     step U's seed                                       ; one more step
     Ovr(2, 0, 6 + (new low & 1));  Walk(t, 7); return
8. if dist < aip(8): T56(t, 3, 0); return
9. Idle(15)
```

- R73a. [I] The aura state is Skills `+0x080`, records at `DataTables+0xB98`, `0x23C` bytes each, count `+0xBA0`. The gate's `MonsterData+0x0E` is the appearance byte that class 311 draws as `Range(4)` at its creation, so 0–3 and always passing for the stock record. The override byte is the **low bit of the next step's low word**, not mod 100 (`and al,1; add al,6`, 0x005FADB3–0x005FADC7). Up to three steps. (fn:sub_00621F20_UnitLifePct@0x00621F20, fn:UNIT_HasState@0x00639DF0, tbl:Skills.txt:aurastate, tbl:MonStats.txt:Skill2)
- R73b. [C] The entry call `UnitLifePct(U)` from 0x005FABAF only, before any test: family `aknight`, 240 cases; no control separates it. (run:2026-10-30-ai-cat-emu-4)

- R73i. [C] As data: kind 1, no `init`, no `alt`; 1 records (311 doomknight2); reach P; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills DoomKnightMissile, MonBoneArmor, MonBoneSpirit. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R73l. [C] First boundary: 395 decisions compared (224 + 94 + 77), 0 mismatches, 1 first-call outcome. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R73r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 171 of its own think's decisions in the rev 4 and rev 6 logs, 171 resumed, 0 mismatches, 0 stopped, 384 later calls matched, an unknown value deciding 250 of 384 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R74. Row 74 `OblivionKnight` (fn:sub_005FAF00_AiOblivionKnight@0x005FAF00)

**`aip`:** 1 the near distance (6/7/8, as data); 2 the hostile's distance (25–27, as data); 3 the curses' frame timer (500/350/200, as data); 4 chance of `Skill6` (50, as data); 5 chance to cast at the hostile (80/85/90, as data); 6 chance of `Skill3` (30, as data); 7 chance to wander near (30, as data); 8 the distance past which it may (9/10/11, as data).

```
1. s ← {knight 0, weak 0, r2 2500, knightD2 0x7FFFFFFF, weakD2 0x7FFFFFFF}  [I] (0x005FAF00, 0x005FB28F)
   AiUnitSearch(G, U, &s, AiOblivionKnightCb, 1)
2. if dist < aip(1):
     if Skill4 > 0 and Skill4 < Skills count and (st ← Skills[Skill4].auratargetstate) > 0 and not HasState(t, st):
       goto curse4
     if s.knight ≠ 0 and UnitDistSq(s.knight, t) > dist·dist and Walk(s.knight, 4): return
     Ovr(2, 50, 0)
     if StepAway(t, 10, 1): return
     if Skill3 ≥ 0: UseSkill3(t); return
3. h ← FindHostile(&d2, 0)                   ; d2: the frame word EBP−0x10, not set before the call
4. if h ≠ 0 and d2 < aip(2):
     if Skill6 > 0 and v14 < T and rchance(4): goto curse6     ; draw#1
     if chance(5):                                             ; draw#1 or #2
       if Skill3 ≥ 0 and rchance(6): UseSkill3(h); return      ; draw#2 or #3
       if Skill1 ≥ 0 and not (U is a monster with MonsterData+0x0E ≥ 4): UseSkill1(h); return
5. if dist > aip(8) and chance(7): WanderNear(t, 6); return
6. if D100() > 69: Idle(10); return
7. T56(t, 3, 0); return
curse4:  UseSkill4(t);  v14 ← T + aip(3); return               ; Decrepify
curse6:  MonAiUseSkill(Sk6mode, Skill6, t, 0, 0);  v14 ← T + aip(3); return   ; MonCurseCast
```

- R74a. [I] Step 2's walk keeps a `doomknight1` between itself and the target: it walks to the knight when that knight is farther from the target than it is. Curse 6 is aimed at the event's target, while the other casts of step 4 go to the hostile. `Skill3` is `MonBoneSpirit`, `Skill1` `DoomKnightMissile`, gated as in row 73. Up to five draws. (fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0, tbl:Skills.txt:auratargetstate, tbl:MonStats.txt:Skill4)
- R74b. [I] **`AiOblivionKnightCb`:** a monster other than the unit, not in a death mode, with `Unit+0xC4` bit `0x02`, of base class 310 (`doomknight1`; `MonBaseId` in `[0, MonStats count)` and equal to `0x136`), within `UnitDistSq ≤ 2500`, on the unit's side (`AlignSame02`) and of alignment 0: the nearest strictly nearer goes to `s.knight`, the nearest below 40 percent life to `s.weak`; the think reads `s.knight` only. No draw. (fn:sub_005FAE40_AiOblivionKnightCb@0x005FAE40, fn:sub_00650D70_AlignSame02@0x00650D70, fn:sub_00463860_MonBaseId@0x00463860)
- R74c. [C] The entry call to the search only, from 0x005FAF4D with its block's five words, before any test: family `oknight`, 240 cases; no control separates it. (run:2026-10-30-ai-cat-emu-4)

- R74i. [C] As data: kind 1, no `init`, no `alt`; 4 records (312 doomknight3, 701-702 dkmag1..dkmag2, 713 dkmag3); reach PU; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills DoomKnightMissile, MonBoneArmor, MonBoneSpirit, Decrepify, Bestow, MonCurseCast. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R74l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R75. Row 75 `QuillMother` (fn:sub_005FB2A0_AiQuillMother@0x005FB2A0)

**`aip`:** 1 melee: chance of A1 (60–95, as data); 2 out of melee range: chance to walk (50–90, as data); 3 the melee wait (16 down to 6, as data); 4 the wait out of it (15, as data).

```
1. if St3or19:                                                             [I] (0x005FB2A0, 0x005FB402)
     blk.kind ← 1;  blk+0x0C ← t ≠ 0 ? t.type : 6;  blk+0x10 ← t ≠ 0 ? t.guid : −1
     MonHelpBlock(U, &blk)
     if melee: SetModeAtUnit(4, t); return
     Walk(t, 7); return
2. if not melee:
     if chance(2): Walk(t, 7); return            ; draw#1
     Idle(aip(4)); return
3. if chance(1): SetModeAtUnit(4, t); return     ; draw#1
4. Idle(aip(3))
```

- R75a. [I] The block's order, type then guid, is the order row 14 `QuillRat` reads as `GameFindUnit(G, rec+0x0C, rec+0x10)`, and the reverse of row 65's; `+0x14` and `+0x18` are left as the stack held them. Whether the call reaches quill rat minions is Open questions. (0x005FB2CA, 0x005FB2EE, 0x005F1173, fn:sub_0058F730_MonHelpBlock@0x0058F730)
- R75b. [C] The map, the group block's three words at `EBP−0x20` included: family `quill`, 240 cases, 137 with a draw, 5 boundaries; the controls fail the 17 and 75 that separate them. (run:2026-10-30-ai-cat-emu-4)

- R75i. [C] As data: kind 1, no `init`, no `alt`; 5 records (313-317 quillbear1..quillbear5); reach ·; `aip` set 1,2,3,4; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R75l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R76. Row 76 `EvilHole` (fn:sub_005FB410_AiEvilHole@0x005FB410)

**`aip`:** 1 the spawn stock (10; 3 for `demonhole`, as data); 2 the frames between spawns (50; 25, as data).

```
1. if v14 ≤ 0: v14 ← T + aip(2);  v18 ← aip(1)                  ; first event  [I] (0x005FB410, 0x005FB59E)
2. switch (U ≠ 0 ? U.mode : 0):
     1:  if dist > 5: Idle(5); return
         MonAiSetMode(10, 0, 0);  Delay(20); return             ; NU to S3
     10: MonAiSetMode(11, 0, 0);  Delay(20); return             ; S3 to S4
     11: if v18 > 0:
           if T > v14:
             v14 ← T + aip(2)
             SpawnClassByBase(U, &cls, &x, &y, &mode, 0, 0)
             room ← RoomAtSubtile(UnitGetRoom(U), x, y)
             if room ≠ 0:
               m ← SpawnAtPos(G, room, x, y, cls, mode, 2, 0x42)
               if m ≠ 0:
                 v18 ← v18 − 1;  m+0xC4 ← m+0xC4 | 0x4020000
                 if U.class = 711: STATE_Set(m, 184, 1);  UnitSetOverlayStat(m, 202, 0)   ; `demonhole`
           Delay(aip(2)); return
3. MonAiSetMode(0, 0, 0)                                        ; any other mode, or S4 with the stock spent
```

- R76a. [I] No draw. The stock counts down on each placed spawn, and the hole dies in mode 0 when it is spent. The `demonhole`'s spawns get state 184 (`uberminion`). `Skill1`, `Nest`, is not read. (fn:sub_005DDFC0_MonAiSetMode@0x005DDFC0, fn:sub_00621E40_UnitSetOverlayStat@0x00621E40, tbl:MonStats.txt:Skill1)
- R76b. [C] The map, the first event's `AiCtl+0x14/+0x18` and the re-armed `+0x14` before `SpawnClassByBase` included: family `ehole`, 240 cases, 5 boundaries; the Normal-column and compare controls fail the 75 and 67 that separate them. `SetMode`'s `Delay(20)` after it is not covered. (run:2026-10-30-ai-cat-emu-4)

- R76i. [C] As data: kind 1, no `init`, no `alt`; 6 records (321-325 evilhole1..evilhole5, 711 demonhole); reach ·; `aip` set 1,2; `aidel` 15/15/15; skills Nest. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R76l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R77. Row 77 `Trap-Missile` (fn:sub_005FB5B0_AiTrapMissile@0x005FB5B0)

**`aip`:** 1 the range (25/30/32, as data); 2 the shot count (1, as data); 3 the wait between (15, as data).

```
1. if t ≠ 0 and dist ≤ aip(1) and v14 < aip(2):                            [I] (0x005FB5B0, 0x005FB641)
     if v18 = 0:
       SetModeAtUnit(4, t);  v14 ← v14 + 1;  v18 ← 1; return     ; the shot, by A1
     v18 ← 0;  Idle(aip(3)); return
2. if U ≠ 0: U+0xC4 ← U+0xC4 | 0x20000
3. MonAiSetMode(0, 0, 0)
```

- R77a. [I] It shoots on every second event, then or when the target is gone or out of range it dies. Kind 2, so it also runs with no target; that path dies. No draw. Its records have no skill. (fn:sub_005DDFC0_MonAiSetMode@0x005DDFC0)
- R77b. [C] The map, `AiCtl+0x18` and `Unit+0xC4` before the boundaries included: family `tmissile`, 240 cases, 3 boundaries; the Normal-column and compare controls fail the 64 and 52 that separate them. The shot's stores come after its call and are not covered. (run:2026-10-30-ai-cat-emu-4)

- R77i. [C] As data: kind 2, no `init`, no `alt`; 2 records (326 trap-firebolt, 330 trap-lightning); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R77l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R78. Row 78 `Trap-RightArrow` (fn:sub_005FB6C0_AiTrapRightArrow@0x005FB6C0)

**`aip`:** 1 the near bound (5, as data); 2 the far bound (15, as data); 3 the frame timer (30/23/18, as data); 4 the frames written to a word nothing reads (200, as data).

```
1. if dist < aip(1) or dist > aip(2): Idle(40); return                     [I] (0x005FB6C0, 0x005FB7D9)
2. UnitGetPos(U, &u);  UnitGetPos(t, &v)
3. a: i32 ← u.x − v.x                                  ; |a| by jns, neg
4. if |a| ≤ 2 and T > v14:
     v14 ← T + aip(3)
     if AiTrapArrowKind(G, U) ≠ 1: SetModeAtUnit(4, t); return
     if Skill1 ≥ 0: v1C ← T + aip(4);  UseSkill1(t); return   ; PoisonBallTrap
5. Idle(30)
```

`AiTrapArrowKind`, [I] (0x005FB650, 0x005FB6B1, fn:sub_00547BB0_MonRegionGet@0x00547BB0, fn:RNG_RandLoHi@0x004BC500):

```
lvl ← RoomGetLevelId(UnitGetRoom(U))
r ← MonRegionGet(G + 0xF0, lvl)
if r+0x2D4 < 0:
  r+0x2D4 ← lvl < 40 ? 0 : RNG_RandLoHi(U's seed, 0, 3)     ; 0, 1 or 2: one step, low mod 3
return r+0x2D4
```

- R78a. [I] The trap shoots when the target is within 2 of its own **x** (the first word of `UnitGetPos`, 0x005FB716), between `aip(1)` and `aip(2)`, and its timer has passed; the timer re-arms before the kind is read. `v1C` is read by nothing in the function. Skill2 is not read. (fn:sub_00620870_UnitGetPos@0x00620870, tbl:MonStats.txt:Skill1)
- R78b. [I] One kind per level's monster region, chosen by the first arrow trap that shoots there, on that trap's own seed; 0 below level 40. `RNG_RandLoHi(seed, lo, hi)` returns `lo` for `hi ≤ lo` and otherwise steps once and returns `lo + low mod (hi − lo)`. `MonRegionsBuild` writes −1 at the region's creation, for levels 1 and up; any other writer is Open questions. (0x004BC500, 0x004BC54E, fn:sub_005479C0_MonRegionsBuild@0x005479C0, fn:sub_0061A1B0_RoomGetLevelId@0x0061A1B0)
- R78c. [C] The map, the kind helper and the region word included (the region word before and after, the step and its `mod 3`, the `lvl < 40` edge): family `trarrow`, 240 cases, 21 with a draw, 4 boundaries; the Normal-column, compare and `mod 4` controls fail the 71, 53 and 14 that separate them. (run:2026-10-30-ai-cat-emu-4)

- R78i. [C] As data: kind 1, no `init`, no `alt`; 1 records (327 trap-horzmissile); reach ·; `aip` set 1,2,3,4; `aidel` 15/15/15; skills PoisonBallTrap, CursedBallTrapRight. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R78l. [C] First boundary: 305 decisions compared (110 + 14 + 181), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F) Outside it: 20 decisions of the row's classes with no model (another think, a state row, or a case the model refuses).
- R78r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 199 of its own think's decisions in the rev 4 and rev 6 logs, 199 resumed, 0 mismatches, 0 stopped, 8 later calls matched, an unknown value deciding 4 of 8 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R79. Row 79 `Trap-LeftArrow` (fn:sub_005FB7E0_AiTrapLeftArrow@0x005FB7E0)

**`aip`:** as row 78.

```
1. if dist < aip(1) or dist > aip(2): Idle(40); return                     [I] (0x005FB7E0, 0x005FB8F9)
2. UnitGetPos(U, &u);  UnitGetPos(t, &v)
3. a: i32 ← u.y − v.y                                  ; |a| by jns, neg
4. if |a| ≤ 2 and T > v14:
     v14 ← T + aip(3)
     if AiTrapArrowKind(G, U) ≠ 1: SetModeAtUnit(4, t); return
     if Skill1 ≥ 0: v1C ← T + aip(4);  UseSkill1(t); return
5. Idle(30)
```

- R79a. [I] Row 78's code with **y** for x (the second word of `UnitGetPos`, 0x005FB836). The kind helper is [R78's](#r78-row-78-trap-rightarrow-fnsub_005fb6c0_aitraprightarrow0x005fb6c0). (fn:sub_005FB650_AiTrapArrowKind@0x005FB650)
- R79b. [C] The map as row 78's: family `tlarrow`, 240 cases, 24 with a draw, 4 boundaries; the controls fail the 78, 62 and 20 that separate them. (run:2026-10-30-ai-cat-emu-4)

- R79i. [C] As data: kind 1, no `init`, no `alt`; 1 records (328 trap-vertmissile); reach ·; `aip` set 1,2,3,4; `aidel` 15/15/15; skills PoisonBallTrap, CursedBallTrapLeft. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R79l. [C] First boundary: 79 decisions compared (40 + 18 + 21), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F) Outside it: 15 decisions of the row's classes with no model (another think, a state row, or a case the model refuses).
- R79r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 53 of its own think's decisions in the rev 4 and rev 6 logs, 53 resumed, 0 mismatches, 0 stopped, 28 later calls matched, an unknown value deciding 14 of 28 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R80. Row 80 `Trap-Poison` (fn:sub_005FB900_AiTrapPoison@0x005FB900)

**`aip`:** 1 the range (20, as data); 2 the shot count (1, as data); 3 the wait (15, as data).

```
1. if t ≠ 0 and dist ≤ aip(1) and v14 < aip(2):                            [I] (0x005FB900, 0x005FB9AB)
     if v18 = 0 and Skill1 ≥ 0:
       UseSkill1(t);  v14 ← v14 + 1;  v18 ← 1; return     ; PrimePoisonNova
     v18 ← 0;  Idle(aip(3)); return
2. if U ≠ 0: U+0xC4 ← U+0xC4 | 0x20000
3. MonAiSetMode(0, 0, 0)
```

- R80a. [I] Row 77's shape with a skill for the shot; a `Skill1 < 0` falls to the idle branch with `v18 = 0`. Kind 2, so it also runs with no target; that path dies. No draw. (fn:sub_005DDFC0_MonAiSetMode@0x005DDFC0)
- R80b. [C] The map as row 77's: family `tpoison`, 240 cases, 3 boundaries; the controls fail the 62 and 56 that separate them. (run:2026-10-30-ai-cat-emu-4)

- R80i. [C] As data: kind 2, no `init`, no `alt`; 1 records (329 trap-poisoncloud); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills PrimePoisonNova. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R80l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R87. Row 87 `Trap-Melee` (fn:sub_005FBA60_AiTrapMelee@0x005FBA60)

**`aip`:** 1 melee: chance of A1 (70, as data); 2 the wait (15, as data).

```
1. if not melee: Idle(40); return                                          [I] (0x005FBA60, 0x005FBAF1)
2. if chance(1): SetModeAtUnit(4, t); return     ; draw#1
3. Idle(aip(2))
```

- R87a. [C] The map, family `tmelee`, 240 cases, 117 with a draw, 3 boundaries; the controls fail the 13 and 71 that separate them. (run:2026-10-30-ai-cat-emu-4)

- R87i. [C] As data: kind 1, no `init`, no `alt`; 1 records (354 trap-melee); reach ·; `aip` set 1,2; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R87l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R92. Row 92 `Trap-Nova` (fn:sub_005FB9B0_AiTrapNova@0x005FB9B0)

**`aip`:** as row 80.

```
1. if t ≠ 0 and dist ≤ aip(1) and v14 < aip(2):                            [I] (0x005FB9B0, 0x005FBA5B)
     if v18 = 0 and Skill1 ≥ 0:
       UseSkill1(t);  v14 ← v14 + 1;  v18 ← 1; return     ; Trap Nova
     v18 ← 0;  Idle(aip(3)); return
2. if U ≠ 0: U+0xC4 ← U+0xC4 | 0x20000
3. MonAiSetMode(0, 0, 0)
```

- R92a. [I] Row 80's code, with this row's kind 1, so the think runs only with a target. No draw. (data:g_MonAiTable@0x0073CA18)
- R92b. [C] The map as row 77's: family `tnova`, 240 cases, 3 boundaries; the controls fail the 62 and 44 that separate them. (run:2026-10-30-ai-cat-emu-4)

- R92i. [C] As data: kind 1, no `init`, no `alt`; 1 records (369 trap-nova); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills Trap Nova. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R92l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 5: summons

#### R67. Row 67 `NecroPet` (fn:sub_005E4CF0_AiNecroPet@0x005E4CF0)

Tier AI: [machinery § T67](machinery.md#t67-row-67-necropet-and-state-7-fnsub_005e4cf0_ainecropet0x005e4cf0), not repeated here.

#### R84. Row 84 `BoneWall` (fn:sub_005E0400_AiBoneWall@0x005E0400)

<!-- body R84 -->

- R84i. [C] As data: kind 0, `init` 0x005E0390, no `alt`; 1 records (344 bonewall); reach S; `aip` set —; `aidel` 15/15/15; skills Bone Wall. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R84l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R86. Row 86 `Hydra` (fn:sub_005E9E60_AiHydra@0x005E9E60)

<!-- body R86 -->

- R86i. [C] As data: kind 2, no `init`, no `alt`; 3 records (351-353 hydra1..hydra3); reach S; `aip` set —; `aidel` 15/15/15; skills HydraMissile. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R86l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R101. Row 101 `AssassinSentry` (fn:sub_005EA3D0_AiAssassinSentry@0x005EA3D0)

<!-- body R101 -->

- R101i. [C] As data: kind 0, `init` 0x005EA290, no `alt`; 4 records (410-412 wakeofdestruction..lightningsentry, 415 infernosentry); reach S; `aip` set 1,2,3,4; `aidel` 15/15/15; skills Wake Of Destruction Sentry, BoltSentry, Shock Field, sentry lightning, mon inferno sentry, Wake of Fire Sentry. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R101l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R102. Row 102 `BladeCreeper` (fn:sub_005EA540_AiBladeCreeper@0x005EA540)

<!-- body R102 -->

- R102i. [C] As data: kind 0, `init` 0x005EA510, no `alt`; 1 records (413 bladecreeper); reach S; `aip` set —; `aidel` 15/15/15; skills Blade Sentinel. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R102l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R103. Row 103 `InvisoPet` (fn:sub_005EA7A0_AiInvisoPet@0x005EA7A0)

<!-- body R103 -->

- R103i. [C] As data: kind 0, no `init`, no `alt`; 1 records (414 invisopet); reach ·; `aip` set 1,2; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R103l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R104. Row 104 `DeathSentry` (fn:sub_005EA980_AiDeathSentry@0x005EA980)

<!-- body R104 -->

- R104i. [C] As data: kind 0, `init` 0x005EA290, no `alt`; 1 records (416 deathsentry); reach S; `aip` set 1,3,4; `aidel` 15/15/15; skills mon death sentry, death sentry ltng. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R104l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R105. Row 105 `ShadowWarrior` (fn:sub_005EAFA0_AiShadowWarrior@0x005EAFA0)

<!-- body R105 -->

- R105i. [C] As data: kind 2, `init` 0x005EAF50, no `alt`; 1 records (417 shadowwarrior); reach S; `aip` set 1,2,3,4,8; `aidel` 15/15/15; skills Fists of Fire, Blade Fury, Blades of Ice, Dragon Claw, Dragon Flight, Claws of Thunder, Attack. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R105l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R106. Row 106 `ShadowMaster` (fn:sub_005EB970_AiShadowMaster@0x005EB970)

<!-- body R106 -->

- R106i. [C] As data: kind 2, `init` 0x005EB490, no `alt`; 1 records (418 shadowmaster); reach S; `aip` set 1,2,3,8; `aidel` 15/15/15; skills Fists of Fire, Blade Fury, Blades of Ice, Dragon Claw, Dragon Flight, Claws of Thunder, Attack. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R106l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R107. Row 107 `Raven` (fn:sub_005ECC10_AiRaven@0x005ECC10)

<!-- body R107 -->

- R107i. [C] As data: kind 2, `init` 0x005ECB70, no `alt`; 1 records (419 druidhawk); reach S; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Raven. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R107l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R108. Row 108 `DruidWolf` (fn:sub_005ED710_AiDruidWolf@0x005ED710)

<!-- body R108 -->

- R108i. [C] As data: kind 0, no `init`, no `alt`; 2 records (420-421 spiritwolf..fenris); reach S; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Teleport 2, fenris rage. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R108l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R109. Row 109 `Totem` (fn:sub_005ED9E0_AiTotem@0x005ED9E0)

<!-- body R109 -->

- R109i. [C] As data: kind 0, no `init`, no `alt`; 3 records (422-424 spiritofbarbs..oaksage); reach S; `aip` set 1,2,3,4; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R109l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R110. Row 110 `Vines` (fn:sub_005EC6C0_AiVines@0x005EC6C0)

<!-- body R110 -->

- R110i. [C] As data: kind 2, `init` 0x005EC6A0, no `alt`; 1 records (425 plaguepoppy); reach S; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Vine Attack. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R110l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R111. Row 111 `CycleOfLife` (fn:sub_005EC8C0_AiCycleOfLife@0x005EC8C0)

<!-- body R111 -->

- R111i. [C] As data: kind 2, `init` 0x005EC6A0, no `alt`; 2 records (426-427 cycleoflife..vinecreature); reach S; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills CorpseCycler, VineCycler. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R111l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R112. Row 112 `DruidBear` (fn:sub_005ED730_AiDruidBear@0x005ED730)

<!-- body R112 -->

- R112i. [C] As data: kind 0, no `init`, no `alt`; 1 records (428 druidbear); reach S; `aip` set 1,2,3; `aidel` 15/15/15; skills BearSmite. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R112l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R143. Row 143 `ShadowMasterNoInit` (fn:sub_005EB970_AiShadowMaster@0x005EB970)

<!-- body R143 -->

- R143i. [C] As data: kind 2, `init` 0x005EB5C0, no `alt`; 0 records (—); reach none; `aip` set —; `aidel` —; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R143l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### S7. State row 7 (fn:sub_005E4CF0_AiNecroPet@0x005E4CF0)

<!-- body S7 -->

- S7i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

### Batch 6: hirelings

#### R61. Row 61 `Hireable` (fn:sub_005E52D0_AiHireable@0x005E52D0)

Tier AI: [machinery § T61](machinery.md#t61-row-61-hireable-and-state-4-fnsub_005e52d0_aihireable0x005e52d0), not repeated here.

#### S4. State row 4 (fn:sub_005E52D0_AiHireable@0x005E52D0)

<!-- body S4 -->

- S4i. [C] As data: kind 0, no `init`, `alt` 0x005E5280. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S5. State row 5 (fn:sub_005E7AC0_AiGoodNpcRanged@0x005E7AC0)

<!-- body S5 -->

- S5i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S6. State row 6 (fn:sub_005E7C10_AiHireUnowned@0x005E7C10)

<!-- body S6 -->

- S6i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

### Batch 7: bosses-A

#### R34. Row 34 `Andariel` (fn:sub_005F5830_AiAndariel@0x005F5830)

Tier AI: [machinery § T34](machinery.md#t34-row-34-andariel-fnsub_005f5830_aiandariel0x005f5830), not repeated here.

#### R44. Row 44 `Duriel` (fn:sub_005F67B0_AiDuriel@0x005F67B0)

<!-- body R44 -->

- R44i. [C] As data: kind 1, no `init`, no `alt`; 2 records (211 duriel, 708 uberduriel); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills Charge, Jab, Smite, Holy Freeze. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R44l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R50. Row 50 `Mephisto` (fn:sub_005F78B0_AiMephisto@0x005F78B0)

<!-- body R50 -->

- R50i. [C] As data: kind 1, no `init`, no `alt`; 1 records (242 mephisto); reach ·; `aip` set 1,2,3; `aidel` 15/10/6; skills PrimeLightning, PrimeBolt, PrimePoisonNova, MephistoMissile, MephFrostNova, Blizzard. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R50l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R53. Row 53 `Summoner` (fn:sub_005F85C0_AiSummoner@0x005F85C0)

<!-- body R53 -->

- R53i. [C] As data: kind 1, no `init`, no `alt`; 1 records (250 summoner); reach U; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/13/10; skills Glacial Spike, Frost Nova, Fire Ball, VampireFirewall, Weaken. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R53l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R55. Row 55 `Izual` (fn:sub_005F89B0_AiIzual@0x005F89B0)

<!-- body R55 -->

- R55i. [C] As data: kind 1, no `init`, no `alt`; 1 records (256 izual); reach ·; `aip` set 1,2,3,4,5,6; `aidel` 15/12/8; skills Frost Nova. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R55l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R59. Row 59 `BloodRaven` (fn:sub_005E6320_AiBloodRaven@0x005E6320)

<!-- body R59 -->

- R59i. [C] As data: kind 1, `init` 0x005E6300, no `alt`; 1 records (267 bloodraven); reach ·; `aip` set —; `aidel` 15/13/10; skills Nest, Quick Strike. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R59l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R90. Row 90 `Griswold` (fn:sub_005E5AC0_AiGriswold@0x005E5AC0)

<!-- body R90 -->

- R90i. [C] As data: kind 1, no `init`, no `alt`; 1 records (365 griswold); reach U; `aip` set —; `aidel` 15/13/10; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R90l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R144. Row 144 `UberIzual` (fn:sub_005F8C80_AiUberIzual@0x005F8C80)

<!-- body R144 -->

- R144i. [C] As data: kind 1, no `init`, no `alt`; 1 records (706 uberizual); reach ·; `aip` set 1,2,3,4,5,6; `aidel` 15/12/8; skills Frost Nova, Chilling Armor, MonTeleport. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R144l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R146. Row 146 `UberMephisto` (fn:sub_005F81C0_AiUberMephisto@0x005F81C0)

<!-- body R146 -->

- R146i. [C] As data: kind 1, no `init`, no `alt`; 1 records (704 ubermephisto); reach ·; `aip` set 1,2,3; `aidel` 15/10/6; skills PrimeLightning, PrimeBolt, PrimePoisonNova, MephistoMissile, MephFrostNova, Blizzard. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R146l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 8: pool-E (towers, turrets, javelins and blowguns, Venom Lords, the siege)

#### R82. Row 82 `InvisoSpawner` (fn:sub_005E0160_AiInvisoSpawner@0x005E0160)

<!-- body R82 -->

- R82i. [C] As data: kind 1, no `init`, no `alt`; 1 records (332 invisospawner); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R82l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R83. Row 83 `MosquitoNest` (fn:sub_005E0260_AiMosquitoNest@0x005E0260)

<!-- body R83 -->

- R83i. [C] As data: kind 0, no `init`, no `alt`; 4 records (334-337 suckernest1..suckernest4); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills Nest. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R83l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R85. Row 85 `HighPriest` (fn:sub_005E0490_AiHighPriest@0x005E0490)

<!-- body R85 -->

- R85i. [C] As data: kind 1, no `init`, no `alt`; 4 records (345-347 councilmember1..councilmember3, 557 baalhighpriest); reach U; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/13,14/12,13; skills Hydra, ZakarumHeal. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R85l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R89. Row 89 `Megademon` (fn:sub_005E0C80_AiMegademon@0x005E0C80)

Tier AI: [machinery § T89](machinery.md#t89-row-89-megademon-fnsub_005e0c80_aimegademon0x005e0c80), not repeated here.

#### R93. Row 93 `ArcaneTower` (fn:sub_005E0F60_AiArcaneTower@0x005E0F60)

<!-- body R93 -->

- R93i. [C] As data: kind 1, no `init`, no `alt`; 1 records (371 lightningspire); reach ·; `aip` set 1,2,3,4,5,6; `aidel` 15/15/15; skills ArcaneTower, Lightning. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R93l. [C] First boundary: 24 decisions compared (24), 0 mismatches, 3 first-call outcomes. (run:2026-11-03-ai, 0x005B186F)

#### R94. Row 94 `DesertTurret` (fn:sub_005E0980_AiDesertTurret@0x005E0980)

<!-- body R94 -->

- R94i. [C] As data: kind 1, no `init`, no `alt`; 4 records (348-350 turret1..turret3, 372 firetower); reach ·; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills DesertTurret. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R94l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R95. Row 95 `PantherJavelin` (fn:sub_005E1080_AiPantherJavelin@0x005E1080)

<!-- body R95 -->

- R95i. [C] As data: kind 1, no `init`, no `alt`; 9 records (373-376 slinger1..slinger4, 394-395 slinger5..slinger6, 610-612 slinger7..slinger9); reach P; `aip` set 1,2,3,4,5,6; `aidel` 15/13,14/12,13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R95l. [C] First boundary: 58 decisions compared (15 + 43), 0 mismatches, 1 first-call outcome. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R95r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 43 of its own think's decisions in the rev 4 and rev 6 logs, 43 resumed, 0 mismatches, 0 stopped, 48 later calls matched, an unknown value deciding 0 of 48 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### R96. Row 96 `FetishBlowgun` (fn:sub_005E1250_AiFetishBlowgun@0x005E1250)

<!-- body R96 -->

- R96i. [C] As data: kind 1, no `init`, no `alt`; 8 records (396-400 fetishblow1..fetishblow5, 659-661 fetishblow6..fetishblow8); reach P; `aip` set 1,2; `aidel` 15/14/13; skills SkeletonRaise. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R96l. [I] Logged, not compared: 179 decisions (61 + 61 + 57) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R96r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 118 of its own think's decisions in the rev 4 and rev 6 logs, 117 resumed, 0 mismatches, 1 stopped, 264 later calls matched, an unknown value deciding 0 of 265 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R97. Row 97 `Spirit` (fn:sub_005E3840_AiSpirit@0x005E3840)

<!-- body R97 -->

- R97i. [C] As data: kind 1, no `init`, no `alt`; 1 records (401 mephistospirit); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R97l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R98. Row 98 `Smith` (fn:sub_005E3890_AiSmith@0x005E3890)

<!-- body R98 -->

- R98i. [C] As data: kind 1, no `init`, no `alt`; 2 records (402 smith, 409 hephasto); reach U; `aip` set —; `aidel` 15/13/12; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R98l. [C] First boundary: 4 decisions compared (4), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, 0x005B186F)

#### R113. Row 113 `SiegeTower` (fn:sub_005E1860_AiSiegeTower@0x005E1860)

<!-- body R113 -->

- R113i. [C] As data: kind 1, no `init`, no `alt`; 1 records (435 barricadetower); reach ·; `aip` set 1; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R113l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R114. Row 114 `ReanimatedHorde` (fn:sub_005E1540_AiReanimatedHorde@0x005E1540)

<!-- body R114 -->

- R114i. [C] As data: kind 1, no `init`, no `alt`; 6 records (436-440 reanimatedhorde1..reanimatedhorde5, 698 reanimatedhorde6); reach PU; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills Self-resurrect, Charge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R114l. [C] First boundary: 43 decisions compared (12 + 31), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, run:2026-11-04-ai-r5, 0x005B186F)
- R114r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 31 of its own think's decisions in the rev 4 and rev 6 logs, 31 resumed, 0 mismatches, 0 stopped, 28 later calls matched, an unknown value deciding 0 of 28 later steps. The row is not under sentence H1. (run:2026-11-04-ai-r5)

#### R115. Row 115 `SiegeBeast` (fn:sub_005E1900_AiSiegeBeast@0x005E1900)

<!-- body R115 -->

- R115i. [C] As data: kind 1, no `init`, no `alt`; 5 records (441-445 siegebeast1..siegebeast5); reach PU; `aip` set 1,2,3,4,5,6,7; `aidel` 15/14/13; skills Siege Beast Stomp, Charge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R115l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 9: pool-F (act V minions)

#### R116. Row 116 `Minion` (fn:sub_005E1B60_AiMinion@0x005E1B60)

<!-- body R116 -->

- R116i. [C] As data: kind 1, no `init`, no `alt`; 11 records (453-460 minion1..minion8, 682-684 minion9..minion11); reach PU; `aip` set 1,2,3,4,5; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R116l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R117. Row 117 `SuicideMinion` (fn:sub_005E1D30_AiSuicideMinion@0x005E1D30)

<!-- body R117 -->

- R117i. [C] As data: kind 1, no `init`, no `alt`; 8 records (461-468 suicideminion1..suicideminion8); reach P; `aip` set 1,2,3,4; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R117l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R118. Row 118 `Succubus` (fn:sub_005E1E00_AiSuccubus@0x005E1E00)

<!-- body R118 -->

- R118i. [C] As data: kind 1, no `init`, no `alt`; 8 records (469-473 succubus1..succubus5, 634-635 succubus6..succubus7, 719 succubus8); reach PU; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills Defense Curse, Blood Mana, SuccubusBolt. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R118l. [I] Logged, not compared: 108 decisions (52 + 46 + 10) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R118r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 56 of its own think's decisions in the rev 4 and rev 6 logs, 56 resumed, 0 mismatches, 0 stopped, 12 later calls matched, an unknown value deciding 0 of 12 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R119. Row 119 `SuccubusWitch` (fn:sub_005E2120_AiSuccubusWitch@0x005E2120)

<!-- body R119 -->

- R119i. [C] As data: kind 1, no `init`, no `alt`; 9 records (9 records, as the index lists them); reach PU; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills Amplify Damage, Weaken, Defense Curse, Blood Mana, SuccubusBolt. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R119l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R120. Row 120 `Overseer` (fn:sub_005E27A0_AiOverseer@0x005E27A0)

<!-- body R120 -->

- R120i. [C] As data: kind 1, no `init`, no `alt`; 6 records (479-483 overseer1..overseer5, 724 overseer6); reach PU; `aip` set 1,2,3,4,5,6,7; `aidel` 15/14/13; skills Cry Help, Healing Vortex, Overseer Whip, Smite. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R120l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R121. Row 121 `MinionSpawner` (fn:sub_005E2BD0_AiMinionSpawner@0x005E2BD0)

<!-- body R121 -->

- R121i. [C] As data: kind 1, `init` 0x005F6630, no `alt`; 9 records (484-491 minionspawner1..minionspawner8, 710 demonspawner); reach ·; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills MinionSpawner. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R121l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R122. Row 122 `Imp` (fn:sub_005E2FF0_AiImp@0x005E2FF0)

<!-- body R122 -->

- R122i. [C] As data: kind 1, `init` 0x005E2FD0, no `alt`; 8 records (492-496 imp1..imp5, 688-689 imp6..imp7, 714 imp8); reach PU; `aip` set 1,2,3,4; `aidel` 15/14/13; skills Imp Teleport, ImpBolt, Imp Fireball, Imp Fire Missile, Imp Inferno, Imp Fire Missile Ex. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R122l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R123. Row 123 `Catapult` (fn:sub_005E34C0_AiCatapult@0x005E34C0)

<!-- body R123 -->

- R123i. [C] As data: kind 1, no `init`, no `alt`; 4 records (497-500 catapult1..catapult4); reach ·; `aip` set 1; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R123l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R124. Row 124 `FrozenHorror` (fn:sub_005E3530_AiFrozenHorror@0x005E3530)

<!-- body R124 -->

- R124i. [C] As data: kind 1, no `init`, no `alt`; 5 records (501-505 frozenhorror1..frozenhorror5); reach PU; `aip` set 1,2,3,4; `aidel` 15/14/13; skills Horror Arctic Blast. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R124l. [C] First boundary: 143 decisions compared (95 + 40 + 8), 0 mismatches, 1 first-call outcome. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R124r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 48 of its own think's decisions in the rev 4 and rev 6 logs, 48 resumed, 0 mismatches, 0 stopped, 144 later calls matched, an unknown value deciding 0 of 144 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R125. Row 125 `BloodLord` (fn:sub_005E36F0_AiBloodLord@0x005E36F0)

Tier AI: [machinery § T125](machinery.md#t125-row-125-bloodlord-fnsub_005e36f0_aibloodlord0x005e36f0), not repeated here.

#### S15. State row 15 (fn:sub_005E1D30_AiSuicideMinion@0x005E1D30)

<!-- body S15 -->

- S15i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S16. State row 16 (fn:sub_005E2D80_AiImpAttached@0x005E2D80)

<!-- body S16 -->

- S16i. [C] As data: kind 1, `init` 0x005E2CD0, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

### Batch 10: pool-G (act V rest, the Ancients, Baal's minions)

#### R126. Row 126 `CatapultSpotter` (fn:sub_005EE040_AiCatapultSpotter@0x005EE040)

<!-- body R126 -->

- R126i. [C] As data: kind 1, no `init`, no `alt`; 4 records (516-519 catapultspotter1..catapultspotter4); reach ·; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Catapult Charged Ball, Catapult Spike Ball, CatapultBlizzard, CatapultPlague, CatapultMeteor. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R126l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R127. Row 127 `NpcBarb` (fn:sub_005EDC50_AiNpcBarb@0x005EDC50)

<!-- body R127 -->

- R127i. [C] As data: kind 2, `init` 0x005EDC40, no `alt`; 2 records (522-523 act5barb1..act5barb2); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R127l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R129. Row 129 `GenericSpawner` (fn:sub_005E61B0_AiGenericSpawner@0x005E61B0)

<!-- body R129 -->

- R129i. [C] As data: kind 1, `init` 0x005E6190, no `alt`; 1 records (528 evilhut); reach ·; `aip` set 1,3; `aidel` 15/15/15; skills Nest. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R129l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R130. Row 130 `DeathMauler` (fn:sub_005EE260_AiDeathMauler@0x005EE260)

<!-- body R130 -->

- R130i. [C] As data: kind 1, no `init`, no `alt`; 6 records (529-533 deathmauler1..deathmauler5, 604 deathmauler6); reach PU; `aip` set 1,2,3,4; `aidel` 15/15/15; skills DeathMaul. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R130l. [I] Logged, not compared: 119 decisions (85 + 34) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-04-ai-r5, 0x005B186F)
- R130r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 34 of its own think's decisions in the rev 4 and rev 6 logs, 33 resumed, 0 mismatches, 1 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-r5)

#### R131. Row 131 `Wussie` (fn:sub_005EE3C0_AiWussie@0x005EE3C0)

<!-- body R131 -->

- R131i. [C] As data: kind 2, no `init`, no `alt`; 1 records (534 act5pow); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R131l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R132. Row 132 `AncientStatue` (fn:sub_005EEAA0_AiAncientStatue@0x005EEAA0)

<!-- body R132 -->

- R132i. [C] As data: kind 0, no `init`, no `alt`; 3 records (537-539 ancientstatue1..ancientstatue3); reach ·; `aip` set —; `aidel` 15/15/15; skills MinionSpawner. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R132l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R133. Row 133 `Ancient` (fn:sub_005EF1A0_AiAncient@0x005EF1A0)

<!-- body R133 -->

- R133i. [C] As data: kind 2, no `init`, no `alt`; 3 records (540-542 ancientbarb1..ancientbarb3); reach PU; `aip` set 1,2,3,4,5; `aidel` 15/13/11; skills Whirlwind, Shout, Leap Attack. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R133l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R134. Row 134 `BaalThrone` (fn:sub_005EF320_AiBaalThrone@0x005EF320)

<!-- body R134 -->

- R134i. [C] As data: kind 2, `init` 0x005EF310, no `alt`; 1 records (543 baalthrone); reach ·; `aip` set 1; `aidel` 15/15/15; skills Decrepify, Baal Corpse Explode, Defense Curse, Blood Mana. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R134l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R136. Row 136 `BaalTaunt` (fn:sub_005EF710_AiBaalTaunt@0x005EF710)

<!-- body R136 -->

- R136i. [C] As data: kind 1, no `init`, no `alt`; 1 records (545 baaltaunt); reach P; `aip` set 1,2,3; `aidel` 15/15/15; skills Baal Taunt. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R136l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R137. Row 137 `PutridDefiler` (fn:sub_005EFA90_AiPutridDefiler@0x005EFA90)

<!-- body R137 -->

- R137i. [C] As data: kind 1, no `init`, no `alt`; 5 records (546-550 putriddefiler1..putriddefiler5); reach P; `aip` set 1,2; `aidel` 15/15/15; skills Impregnate. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R137l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R139. Row 139 `BaalTentacle` (fn:sub_005EF820_AiBaalTentacle@0x005EF820)

<!-- body R139 -->

- R139i. [C] As data: kind 1, no `init`, no `alt`; 5 records (562-566 baaltentacle1..baaltentacle5); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R139l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R141. Row 141 `BaalMinion` (fn:sub_005EF910_AiBaalMinion@0x005EF910)

<!-- body R141 -->

- R141i. [C] As data: kind 1, no `init`, no `alt`; 3 records (571-573 baalminion1..baalminion3); reach U; `aip` set 1,2,3,4; `aidel` 15/14/13; skills Smite. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R141l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 11: bosses-B (Diablo, Nihlathak, the Baal rows, Uber Diablo and Baal)

#### R51. Row 51 `Diablo` (fn:sub_005E9170_AiDiablo@0x005E9170)

<!-- body R51 -->

- R51i. [C] As data: kind 1, no `init`, `alt` 0x005E8480; 2 records (243 diablo, 333 diabloclone); reach ·; `aip` set —; `aidel` 15/13/12; skills DiabLight, DiabCold, DiabFire, DiabWall, DiabRun, PrimeFirewall, DiabPrison, Diablogeddon. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R51l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R128. Row 128 `Nihlathak` (fn:sub_005EE5D0_AiNihlathak@0x005EE5D0)

<!-- body R128 -->

- R128i. [C] As data: kind 2, `init` 0x005EE5C0, `alt` 0x005E5280; 1 records (526 nihlathakboss); reach U; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Imp Teleport, Overseer Whip, NihlathakCorpseExplosion, Horror Arctic Blast, MinionSpawner. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R128l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R135. Row 135 `BaalCrab` (fn:sub_005FCFE0_AiBaalCrab@0x005FCFE0)

<!-- body R135 -->

- R135i. [C] As data: kind 0, no `init`, `alt` 0x005FCF30; 1 records (544 baalcrab); reach ·; `aip` set —; `aidel` 15/13/12; skills Baal Nova, Baal Inferno, Baal Tentacle, Baal Cold Missiles, Baal Teleport, Defense Curse, Blood Mana. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R135l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R138. Row 138 `BaalToStairs` (fn:sub_005EF620_AiBaalToStairs@0x005EF620)

<!-- body R138 -->

- R138i. [C] As data: kind 1, no `init`, no `alt`; 1 records (559 baalcrabstairs); reach ·; `aip` set 1; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R138l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R140. Row 140 `BaalCrabClone` (fn:sub_005FD210_AiBaalClone@0x005FD210)

<!-- body R140 -->

- R140i. [C] As data: kind 0, no `init`, `alt` 0x005FCF30; 1 records (570 baalclone); reach ·; `aip` set —; `aidel` 15/14/12; skills Baal Nova, Baal Inferno, Baal Tentacle, Baal Cold Missiles, Baal Clone Teleport, Defense Curse, Blood Mana. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R140l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R145. Row 145 `UberBaal` (fn:sub_005FD200_AiUberBaal@0x005FD200)

<!-- body R145 -->

- R145i. [C] As data: kind 1, no `init`, `alt` 0x005FCF30; 1 records (709 uberbaal); reach ·; `aip` set —; `aidel` 15/13/12; skills Baal Nova, Baal Inferno, Baal Tentacle, Baal Cold Missiles, Baal Teleport, Defense Curse, Blood Mana, Chilling Armor. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R145l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R147. Row 147 `UberDiablo` (fn:sub_005E9DF0_AiUberDiablo@0x005E9DF0)

<!-- body R147 -->

- R147i. [C] As data: kind 1, no `init`, `alt` 0x005E8480; 1 records (705 uberdiablo); reach ·; `aip` set —; `aidel` 15/13/12; skills DiabLight, DiabCold, DiabFire, DiabWall, DiabRun, PrimeFirewall, DiabPrison, Diablogeddon. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R147l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 12: towns, NPCs and the state rows

#### R31. Row 31 `NpcOutOfTown` (fn:sub_005E7880_AiNpcOutOfTown@0x005E7880)

<!-- body R31 -->

- R31i. [C] As data: kind 0, no `init`, no `alt`; 2 records (146 cain1, 527 drehyaiced); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R31l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R32. Row 32 `Npc` (fn:sub_005E7130_AiNpc@0x005E7130)

<!-- body R32 -->

- R32i. [C] As data: kind 0, no `init`, no `alt`; 35 records (35 records, as the index lists them); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R32l. [I] Logged, not compared: 1167 decisions (416 + 279 + 472) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R32r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 751 of its own think's decisions in the rev 4 and rev 6 logs, 591 resumed, 0 mismatches, 160 stopped, 1987 later calls matched, an unknown value deciding 766 of 2147 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R41. Row 41 `Towner` (fn:sub_005E7540_AiTowner@0x005E7540)

<!-- body R41 -->

- R41i. [C] As data: kind 0, no `init`, no `alt`; 6 records (195-197 act2male..act2child, 203 act2guard1, 294 act3male, 296 act3female); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R41l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R42. Row 42 `Vendor` (fn:sub_005E9E00_AiVendor@0x005E9E00)

<!-- body R42 -->

- R42i. [C] As data: kind 0, no `init`, no `alt`; 2 records (204-205 act2vendor1..act2vendor2); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R42l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R54. Row 54 `NpcStationary` (fn:sub_005E73A0_AiNpcStationary@0x005E73A0)

<!-- body R54 -->

- R54i. [C] As data: kind 0, no `init`, no `alt`; 4 records (251 tyrael1, 367 tyrael2, 406 izualghost, 521 tyrael3); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R54l. [I] Logged, not compared: 489 decisions (187 + 125 + 177) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R54r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 302 of its own think's decisions in the rev 4 and rev 6 logs, 302 resumed, 0 mismatches, 0 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R58. Row 58 `Navi` (fn:sub_005E7E20_AiNavi@0x005E7E20)

<!-- body R58 -->

- R58i. [C] As data: kind 0, no `init`, no `alt`; 1 records (266 navi); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R58l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R60. Row 60 `GoodNpcRanged` (fn:sub_005E7AC0_AiGoodNpcRanged@0x005E7AC0)

<!-- body R60 -->

- R60i. [C] As data: kind 0, no `init`, no `alt`; 1 records (270 rogue2); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R60l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R62. Row 62 `TownRogue` (fn:sub_005E7D60_AiTownRogue@0x005E7D60)

<!-- body R62 -->

- R62i. [C] As data: kind 1, no `init`, no `alt`; 1 records (272 rogue3); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R62l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R81. Row 81 `JarJar` (fn:sub_005E7590_AiJarJar@0x005E7590)

<!-- body R81 -->

- R81i. [C] As data: kind 0, no `init`, no `alt`; 1 records (331 act2guard2); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R81l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R88. Row 88 `7TIllusion` (fn:sub_005EA080_Ai7TIllusion@0x005EA080)

<!-- body R88 -->

- R88i. [C] As data: kind 1, no `init`, no `alt`; 1 records (355 seventombs); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R88l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R91. Row 91 `DarkWanderer` (fn:sub_005EA130_AiDarkWanderer@0x005EA130)

<!-- body R91 -->

- R91i. [C] As data: kind 1, no `init`, no `alt`; 1 records (368 darkwanderer); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R91l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R99. Row 99 `TrappedSoul` (fn:sub_005E9F10_AiTrappedSoul@0x005E9F10)

<!-- body R99 -->

- R99i. [C] As data: kind 1, no `init`, no `alt`; 2 records (403-404 trappedsoul1..trappedsoul2); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R99l. [I] Logged, not compared: 468 decisions (243 + 25 + 200) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R99r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 225 of its own think's decisions in the rev 4 and rev 6 logs, 225 resumed, 0 mismatches, 0 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R100. Row 100 `Buffy` (fn:sub_005E7F50_AiBuffy@0x005E7F50)

<!-- body R100 -->

- R100i. [C] As data: kind 0, no `init`, no `alt`; 1 records (408 malachai); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R100l. [I] Logged, not compared: 16 decisions (12 + 4) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R100r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 4 of its own think's decisions in the rev 4 and rev 6 logs, 4 resumed, 0 mismatches, 0 stopped, 4 later calls matched, an unknown value deciding 0 of 4 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### S2. State row 2 (fn:sub_005B14E0_AiSt2WanderNearTarget@0x005B14E0)

<!-- body S2 -->

- S2i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S3. State row 3 (fn:sub_005E5870_AiSt3GroupRoam@0x005E5870)

<!-- body S3 -->

- S3i. [C] As data: kind 1, `init` 0x005E5730, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S8. State row 8 (fn:sub_005E7DC0_AiSt8@0x005E7DC0)

<!-- body S8 -->

- S8i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S9. State row 9 (fn:sub_005E7F80_AiSt9@0x005E7F80)

<!-- body S9 -->

- S9i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S10. State row 10 (fn:sub_005E8020_AiSt10@0x005E8020)

<!-- body S10 -->

- S10i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S11. State row 11 (fn:sub_005E8140_AiSt11@0x005E8140)

<!-- body S11 -->

- S11i. [C] As data: kind 1, `init` 0x005E80E0, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S12. State row 12 (fn:sub_005E8340_AiSt12@0x005E8340)

<!-- body S12 -->

- S12i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S13. State row 13 (fn:sub_005E5C50_AiSt13@0x005E5C50)

<!-- body S13 -->

- S13i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S14. State row 14 (fn:sub_005E2610_AiSt14@0x005E2610)

<!-- body S14 -->

- S14i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S17. State row 17 (fn:sub_005E8020_AiSt10@0x005E8020)

<!-- body S17 -->

- S17i. [C] As data: kind 2, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

## Outputs

Per decision: the commands, mode changes and path requests the entry's block names, on the unit, and the seed advanced by its draws.

## Worked example

None of its own: the rows have no recorded seed-to-decision case outside the tier's. [Machinery § Worked example](machinery.md#worked-example) and [README § Worked example](README.md#worked-example) hold the tier's.

## Reimplementation notes

- [I] **A slot may be read twice.** Row 7's second `aip(3)` draw is a new draw on the same slot. Each `chance` is one step. (0x005EFB80)
- [I] **Two life readers.** Row 11 calls `UnitLifePct`, rows 4, 8 and 15 `AiLifePct`. Keep them apart. (fn:sub_00621F20_UnitLifePct@0x00621F20, fn:sub_005DD280_AiLifePct@0x005DD280)

## Evidence

- [ai/0002](../../../findings/ai/0002-pool-a.md), [ai/0003](../../../findings/ai/0003-pool-b.md), [ai/0004](../../../findings/ai/0004-pool-c.md), [ai/0005](../../../findings/ai/0005-pool-d.md): batches 1 to 4. [ai/0001](../../../findings/ai/0001-machinery.md): the rows 0 and 1 and the second table.
- [ai/0015](../../../findings/ai/0015-phase2-first-run.md), [ai/0017](../../../findings/ai/0017-phase2-second-run.md), [ai/0018](../../../findings/ai/0018-phase2-third-run.md): the three logged batches.
- [MonAI](../../../tables/MonAI.md), [MonStats](../../../tables/MonStats.md).

To check the count: every row has one heading `#### R<n>. Row <n> ` and every state row one heading `#### S<n>. State row <n> `: `grep -cE '^#### R[0-9]+\. Row ' docs/specs/monsters/ai/catalogue.md` gives 148 and `grep -cE '^#### S[0-9]+\. State row '` gives 18.

## Open questions

- [L] **Row 15's alt, the kind-14 record's `+0x18`:** no writer found; a direct store into a list record was not scanned. A scan or a log of the alt settles it. ([ai/0002](../../../findings/ai/0002-pool-a.md), fn:sub_005F1750_AiSandMaggotAlt@0x005F1750)
- [L] **Row 6's event 17, the `Unit+0xC4` bit `0x02` of the corpse callbacks** (rows 6, 13): what they show or mean is not read. ([ai/0002](../../../findings/ai/0002-pool-a.md))
- [L] **Row 25's dance:** the offset tables' `(x, y)` values (written on the stack at entry, 0x005F39E1–0x005F3E07), the five-wisp origin, and what unit event 12 on the player does at the grant's end. A dump of the stack after the prologue, or a logged dance, settles them. ([ai/0003](../../../findings/ai/0003-pool-b.md), fn:sub_005F39B0_AiWillOWisp@0x005F39B0)
- [L] **The killer of the self-kills** (rows 40, 46, 56): what `UnitKilled` does with it is not read, and a log of an egg hatching would settle whether its target is credited. ([ai/0004](../../../findings/ai/0004-pool-c.md), fn:sub_0057CCB0_UnitKilled@0x0057CCB0)
- [L] **The group calls of rows 65 and 75:** whether the shaman's reaches `Fetish` minions and the mother's `QuillRat` ones. The orders match those two readers; the group's class is not read from the spawn data. A log of a `fetishshaman` breath and of a `quillbear` in the 3-or-19 state settles it. ([ai/0005](../../../findings/ai/0005-pool-d.md), fn:sub_0058F730_MonHelpBlock@0x0058F730)
- [L] **Row 71's state 1:** tested but set by no code of the function; whether another path sets it, or the branch cannot be reached on stock data. ([ai/0005](../../../findings/ai/0005-pool-d.md), fn:sub_005FA710_AiRegurgitator@0x005FA710)
- [L] **Rows 73 and 74's gate on `MonsterData+0x0E < 4`:** classes 311 and 312 always pass; what the `dkmag1..3` records (classes 701, 702, 713) hold there is not read. **Rows 78 and 79:** whether any code but `MonRegionsBuild` writes the region's `+0x2D4`. ([ai/0005](../../../findings/ai/0005-pool-d.md), fn:sub_005FB650_AiTrapArrowKind@0x005FB650)
