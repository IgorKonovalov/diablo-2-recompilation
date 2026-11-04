---
spec: monsters/ai/catalogue
status: reviewed
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, monsters/ai/overview, monsters/ai/machinery, skills/dispatch, path/overview]
consumed_by: [monsters/ai/overview, monsters/ai/machinery, hirelings]
tags: {C: 330, I: 502, L: 19}
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
| `O` | `MonsterOwner(U)` |
| `Ovr(type, param, byte)` | as machinery's; each word is stored only when non-zero, so a 0 keeps what an earlier call set this event ([D2](machinery.md#d-the-path-request)) |
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
- [I] **The census of the 130 rows outside the tier,** by those lines. 28 have their first boundary compared, 15 are logged in a row with no model, so theirs is not raised, and 87 have no decision logged: `grep -cE` of `^- R[0-9]+l\. \[C\] First boundary`, `^- R[0-9]+l\. \[I\] Logged, not compared` and `^- R[0-9]+l\. \[I\] Not logged` gives each. 115 of the 130 name an emulated family for their think or init; the other 15 are rows 0, 1, 8, 10, 11, 15, 23, 25, 26, 48, 49, 56, 60, 145 and 147. 38 entries have an `r` line (`^- [RS][0-9]+r\.`), 4 of them state rows (10, 11, 12, 17). (0x005B186F, run:2026-11-04-ai-resume)
- [I] **The catalogue sample is short, by name:** batches 5, 7, 10, 11, 12 have no row that counts. Row 54 cannot fail (0 of 3 sites), row 99 has no call past the first, row 32 has a fork in all 199 decisions of the rev 4 logs, row 100 has 4 decisions. Row 130's map has not landed.
  (run:2026-11-04-ai-resume-flip)
- [I] **Which blocks were read against their instructions.** Each block restates a compact block or the prose of its finding, and those were wrong in places no earlier review caught. Read line by line against objdump of the pinned image, register and stack arguments included, at the `lane/s52b` review: rows 3, 4, 11, 16, 18, 25, 26, 48, 50, 59, 65, 70, 71, 73, 85, 91, 96, 104, 106 (steps 12 to 16 and `Use`), 108, 116, 122, 131, states 3 and 5, and the tables of rows 51 and 135. By that lane alone, with filtered listings on the longer functions: 105, 106's other steps, 110, 111, 112, 134, 137, 31, 32's chain, 54, 58, 81, 99, states 12 and 13. The tier rows' read set is machinery's. **At P3c, by `lane/s52c`, each listing whole:** rows 33, 36, 38, 39, 40, 43, 45, 46, 47, 49, 52, 56, 57, 63, 117, 118, 119, 120, 121, 123, 124, 66, 68, 69, 72, 74, 75, 76, 77, 78, 79, 80, 87, 92, 44, 53, 55, 90, 144, 146, 84, 86, 101, 102, 103, 107, 109, 5, 7, 8, 10, 12, 14, 15, 142, 17, 19, 23, 24, 27, 82, 83, 93, 94, 95, 97, 98, 113, 114, 115, states 15, 16, 7, 4, 6 (75 of P3c's 75; printed from objdump with only the inline seed steps and position getters collapsed by script to their base register; helpers named in a block's prose, rows 23's and 113's callbacks and the host, row 55's quest call, row 146's two functions and state 15's setter, read from a filtered listing of their calls and compares; row 94's tables are `lane/r71`'s; states 4 and 7 are aliases of machinery's tier rows). **Not read:** the other blocks of batches 10 to 12, whose findings wrote them from instructions. **Measured:** of the 19 blocks of batches 1 to 9 read at the review, 2 (rows 18, 59) held an error that changes a branch or a command's argument and 1 (row 104) an omitted argument; of 3 of batches 10 to 12, none. Of P3c's 75, 2 (rows 49, 74, `T56`'s flag is the record, never 0, so flags 4) held an error that changes a command's argument and 2 (rows 102, 107) an omitted argument. In all 94, none a draw's order or count; all corrected here. Reading does not raise a tag. Short by name: rows 106 and 143 (step 13's terms decide which skills draw) and rows 25 and 94 (their tables), Open questions. (0x005F2426, 0x005E63F8, 0x005E65E5, 0x005EAA11, 0x005F76CF, 0x005FB26C, 0x005EA65E, 0x005ECCCD)
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
| `aip(2)` | farther than 3: chance of the ring-4 retreat with override −50, else ring 3 |
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

- R5a. [I] `v14` is the swoop flag: set after an approach walk with override parameter `aip(5)` and the override byte `dist` (capped at 77 by `MonAiPathOverride`); the next event in melee range attacks at once. `Ovr(0, 0, 0)` before `Ring(3)` stores nothing ([machinery D2](machinery.md#d-the-path-request)). (struct:AiCtl+0x14, fn:sub_005DE190_MonAiPathOverride@0x005DE190)
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

- R7a. [I] Out of melee range the override parameter is `100 − life%` with life clamped to 40..100: 60 at 40 % and below, and at full life 0, which stores nothing ([machinery D2](machinery.md#d-the-path-request)). (fn:sub_00621F20_UnitLifePct@0x00621F20)
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
5. if D100() < 25: T56(t, 3, s.unit)             ; draw#2; the flag word is s.unit, not a constant
   else: Idle(aip(4))
```

- R18a. [I] The callback takes a monster (`Unit+0x00` = 1) other than the searcher with the searcher's `MonBaseId`, not in a death mode, and keeps the nearest by `UnitDistSq`. The search block is a stack block `{+0x00 unit, +0x04 best}` at `EBP − 0x2C`. Step 5's flag is `s.unit` (`push ebx` at 0x005F2426, `ebx` set from the block at 0x005F23B8), so with a packmate found within `aip(3)` the walk goes to `MonAiMove` with flags 4, and with none found with flags 0 ([machinery B11](machinery.md#b-the-command)). (0x005F2426, fn:sub_005B0D00_AiSameBaseNearCb@0x005B0D00, fn:sub_00463860_MonBaseId@0x00463860, fn:sub_0063EA40_MonIsDeathMode@0x0063EA40)
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
gather trigger, at entry:                                                  [I] (0x005F3C3D, 0x005F3E0A, 0x005F3E46)
  if t ≠ 0 and v1C < G.frame and UnitDistSq(U, t) < 1024 and v14 < 4 and Range(1000) ≤ d + 2: v14 ← 4   ; the draw only past the three tests

state 4:                                                                   [I] (0x005F3E5B, 0x005F4051)
  a room unit search of radius 32 around U (RoomUnitSearchInit, flags 0x583; AiWispCb)
  exactly 4 found: each gets v14 ← 6, v18 ← 0, v1C ← its index 1..4 (AiCtlSetVar), Idle(337 − G.frame mod 337)
  exactly 5 found: v14 ← 5 and indices 1..5, the same idle
  then U itself idles to the same frame; return
  any other count: v14 ← 2;  Idle(8); return

the dance, v14 = 5 (five wisps) or v14 ≥ 6 (four wisps):                   [I] (0x005F4054, 0x005F4366)
1. if v1C > 5 (v14 = 5) or v1C > 4 (v14 ≥ 6): v14 ← 2;  Idle(8); return     ; v1C still a cooldown frame
2. e ← v1C when v14 = 5, else v1C + 4·v14
   point ← t's subtile position + A[e]                        ; both dances; A5 for v14 = 5
3. if AiPathDistToPoint(U, point) > 3 (unsigned):
     if Range(100) < 34: Ring(4)
     else: MoveToPointNoStop(point.x, point.y, 2)
     return
4. if G.frame mod 67 ≠ 0: Idle(67 − G.frame mod 67); return
5. if v18 < 3:
     if B[e] = (0, 0):                                        ; B5 for v14 = 5
       v18 ← v18 + 1;  v14 = 5: Idle(337 − G.frame mod 337), else Idle(67)
     else:
       MonAiSetMode(7, t's subtile x + B[e].x, t's subtile y + B[e].y);  v18 ← v18 + 1
     return
6. v14 = 5: v14 ← 2;  v1C ← G.frame + 1800;  Idle(337 − G.frame mod 337); return     ; no grant
7. v14 ≥ 6: v14 ← v14 + 1;  v18 ← 0
     if v14 > 12: v14 ← 2;  v1C ← G.frame + 1800
     Idle(337 − G.frame mod 337)
     the grant

the grant:                                                                 [I] (0x005F41D6, 0x005F4271)
  if t ≠ 0, t is a player (t+0x00 = 0) and not UnitIsDead(t):
    l ← STATLIST_Alloc(flags 2, end G.frame + 1 728 000, t's type and id);  if l = 0: nothing more
    stat 80 ← 50·(d + 1) on l;  StatListSetEnd(l, end)
    UnitQueueEvent(t, 12, end, 0, 0);  STATLIST_LinkToUnit(t, l, 1)

state 1 (after an approach):                                               [I] (0x005F437D, 0x005F4435)
1. if v18 ≤ 0:
     if melee: SetModeAtUnit(8, 0);  v14 ← 3; return
     if chance(1): SetModeAtUnit(8, 0);  v14 ← 2; return     ; a failed draw falls through to step 2
2. v18 ← v18 − 1;  v14 ← 1                                   ; may go below 0
   if Range(100) < aip(3): Walk(t, 0)
   else: Ring(6)

states 0, 2, 3:                                                            [I] (0x005F4438, 0x005F4500)
1. if not melee and (v14 = 2 or chance(1)): SetModeAtUnit(7, t);  v14 ← 0; return    ; SC, Chain Lightning by Skill1's mode
2. if melee and (v14 = 3 or chance(2)): SetModeAtUnit(4, t);  v14 ← 0; return        ; the draw only when v14 is not the state named
3. v14 ← 1
   if Range(100) < aip(3): Walk(t, 0)
   else: Ring(4)
   v18 ← 3
```

- R25a. [I] The trigger's `Range(1000) ≤ d + 2` is 3, 4 or 5 in 1000. `AiWispCb`: a monster not in a death mode whose `MonBaseId` is 118, `willowisp1`'s row. The tables are 8-byte `(x, y)` entries in the frame: `A` from `EBP − 0x2F4`, `B` from `EBP − 0x214`, `A5` from `EBP − 0x38`, `B5` from `EBP − 0x64`, each indexed by `e`, written at every entry to the think (0x005F39E1–0x005F3E07). Both dances' origin is the target's subtile position (0x005F407E–0x005F40AA, 0x005F4291–0x005F42AE). (fn:sub_005F3960_AiWispCb@0x005F3960, fn:sub_0058EC00_AiCtlSetVar@0x0058EC00, fn:sub_0065A950_RoomUnitSearchInit@0x0065A950)
- R25b. [I] Each of the four wisps grants on each of its seven advances: the end-of-dance reset is skipped over, not the grant. (fn:STATLIST_Alloc@0x006251F0, fn:STATLIST_LinkToUnit@0x00626E10, fn:sub_005417D0_UnitQueueEvent@0x005417D0, tbl:ItemStatCost.txt:item_magicbonus)
- R25c. [I] The block was checked against its anchored instructions (the finding's prose differed; [ai/0003 § 2.9](../../../findings/ai/0003-pool-b.md) holds the dated correction). The table values and what event 12 does are Open questions. Not emulated: `UnitDistSq` comes first on most events and the room search in state 4. (0x005F3E1C, 0x005F3F14)

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
6. if D100() < 30: T56(t, 4, M); return    ; the flag word is the record M (push esi), never 0, so flags 4
7. Idle(20)
```

- R49c. [I] Step 6's third argument is `ESI`, the MonStats record loaded at 0x005F72DB and not written since, so a refused walk reaches `MonAiMove` with flags 4 and cancels the AI event ([machinery B6, B11](machinery.md#b-the-command)). (0x005F76CF, 0x005F72DB, fn:sub_005DF7D0_MonAiWalkToUnitType56@0x005DF7D0)
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
7. T56(t, 3, M); return                                        ; the flag word is the record M (push edi), never 0, so flags 4
curse4:  UseSkill4(t);  v14 ← T + aip(3); return               ; Decrepify
curse6:  MonAiUseSkill(Sk6mode, Skill6, t, 0, 0);  v14 ← T + aip(3); return   ; MonCurseCast
```

- R74d. [I] Step 7's third argument is `EDI`, the MonStats record loaded at 0x005FAF0C and not written since, so a refused walk reaches `MonAiMove` with flags 4 and cancels the AI event ([machinery B6, B11](machinery.md#b-the-command)). (0x005FB26C, 0x005FAF0C, fn:sub_005DF7D0_MonAiWalkToUnitType56@0x005DF7D0)
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

No `aip` read. `Skill1`'s `Param2` is its only table input.

```
init:                                                                      [C] (0x005E03A0, 0x005E03F1, run:2026-10-30-ai-cat-emu-5)
  if M ≠ 0 and (s: i16 ← Skill1) > 0:                ; movzx; test ax,ax; jle
    rec ← s < Skills count ? Skills + 0x23C·s : 0
    v14 ← T + (rec ≠ 0 ? rec.Param2 : 0)
think:                                               ; compare signed      [C] (0x005E040B, 0x005E0424, run:2026-10-30-ai-cat-emu-5)
  if v14 < T: MonAiSetMode(0, 0, 0)
  else: Idle(15)
```

- R84a. [I] The bone wall's life is its `Skill1`'s `Param2` in frames from its AI init. A `Sk lvl` of 0 on the record feeds no level this row reads. (tbl:Skills.txt:Param2, fn:sub_005E0390_AiBoneWallInit@0x005E0390, fn:sub_005E0400_AiBoneWall@0x005E0400)
- R84b. [C] Families `bwinit` (return, 240 cases; the compare and unsigned-`Skill1` controls fail the 51 and 94 that separate them) and `bwall` (240 cases, 2 outcomes; the compare control fails the 44 it separates). (run:2026-10-30-ai-cat-emu-5)

- R84i. [C] As data: kind 0, `init` 0x005E0390, no `alt`; 1 records (344 bonewall); reach S; `aip` set —; `aidel` 15/15/15; skills Bone Wall. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R84l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R86. Row 86 `Hydra` (fn:sub_005E9E60_AiHydra@0x005E9E60)

No `aip` read: the draw's bound is the constant 60.

```
if v14 < T: MonAiSetMode(0, 0, 0); return            ; signed              [C] (0x005E9E75, 0x005E9F01, run:2026-10-30-ai-cat-emu-5)
if t ≠ 0 and dist < 25 and D100() < 60:              ; one step, only when t is set and dist < 25
  UseSkill1(t); return
Idle(10)
```

- R86a. [I] The hydra's `v14` is not set by its row, which has no init: its writer is Open questions. (fn:sub_005E9E60_AiHydra@0x005E9E60)
- R86b. [C] Family `hydra`, 240 cases, 121 with a draw, 3 outcomes; the `≤` and compare controls fail the 21 and 58 that separate them, and `v14 < T`, `dist < 25` and the draw are each met at equality. (run:2026-10-30-ai-cat-emu-5)

- R86i. [C] As data: kind 2, no `init`, no `alt`; 3 records (351-353 hydra1..hydra3); reach S; `aip` set —; `aidel` 15/15/15; skills HydraMissile. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R86l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R101. Row 101 `AssassinSentry` (fn:sub_005EA3D0_AiAssassinSentry@0x005EA3D0)

**`aip`:** 1 chance to shoot (100 in all four records, as data, so the draw never refuses); 2 the idle after a refused draw; 3 the idle with no near hostile; 4 the hostile's distance (15, 25, 25, 13, as data).

`O` below is `MonsterOwner(U)`.

```
init 0x005EA290:  v14 ← T;  v18 ← −1                                       [C] (run:2026-10-30-ai-cat-emu-5, 0x005EA290)

charge(ctx, use) → 1 when the sentry was ended:                            [I] (0x005EA2B0, 0x005EA3C4)
  if O = 0 or UnitGetRoom(O) = 0 or InTown(O): MonAiSetMode(0, 0, 0); return 1
  if v18 < 0:
    if Skill1 is not a Skills row: goto end
    sk ← SKILLS_GetUnitSkill(U, Skill1)
    if sk = 0: MonAiSetMode(0, 0, 0); return 1
    v18 ← EvalCalc(U, calc4, Skill1, SkillLevel(U, sk, 1))
  if v18 > 0:
    if use: v18 ← v18 − 1
    return 0
  end: MonAiSetMode(0, 0, 0); return 1

think:                                                                     [I] (0x005EA3D0, 0x005EA507)
  if charge(ctx, 0): return
  sk ← SKILLS_GetUnitSkill(U, Skill1)
  if sk = 0: MonAiSetMode(0, 0, 0); return
  if HasState(U, 12): State(12, 0)
  h ← FindHostile(&d, &m)
  if h = 0 or d ≥ aip(4): Idle(aip(3)); return
  if Range(100) ≥ aip(1): Idle(aip(2)); return           ; draw#1
  if charge(ctx, 1): return
  UNIT_CancelEvents(2, 0)
  MonAiUseSkill(SkillMode(sk), Skill1, h, 0, 0)
```

- R101a. [I] `v18` is the shot count from `calc4` at the sentry's own level. The row uses `Skill1` only. (fn:sub_005EA2B0_AiSentryCharge@0x005EA2B0, tbl:Skills.txt:calc4)
- R101b. [C] The init's two stores and return, and the think's entry call only: `charge` reaches `MonsterOwner` from 0x005EA2C1 with `ECX` the unit, before any test. Families `sentinit`, `asentry`, 240 cases each; no control separates them. (run:2026-10-30-ai-cat-emu-5)

- R101i. [C] As data: kind 0, `init` 0x005EA290, no `alt`; 4 records (410-412 wakeofdestruction..lightningsentry, 415 infernosentry); reach S; `aip` set 1,2,3,4; `aidel` 15/15/15; skills Wake Of Destruction Sentry, BoltSentry, Shock Field, sentry lightning, mon inferno sentry, Wake of Fire Sentry. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R101l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R102. Row 102 `BladeCreeper` (fn:sub_005EA540_AiBladeCreeper@0x005EA540)

No `aip` read. The two points come from the head record of its parameter list.

```
init 0x005EA510:  v14 ← −1;  v18 ← 1;  v1C ← 0                             [C] (run:2026-10-30-ai-cat-emu-5, 0x005EA510)

1. s ← Skill1                                                              [C] (0x005EA58F, 0x005EA5A1, run:2026-10-30-ai-cat-emu-5)
   if s < 0 or s ≥ Skills count or rec(s) = 0: MonAiSetMode(0, 0, 0); return
   sk ← SKILLS_GetUnitSkill(U, s)
   if sk = 0: MonAiSetMode(0, 0, 0); return
2. lvl ← SkillLevel(U, sk, 1)                                              [I] (0x005EA5A6, 0x005EA79A)
3. if v14 < 0: v14 ← EvalCalc(U, calc4, s, lvl) + T
4. if T > v14: MonAiSetMode(0, 0, 0); return
5. if v1C = 0 and 0 ≤ srvmissilea < Missiles count:
     p ← O ≠ 0 ? O : U
     m ← MissileCreateAt(G, p, s, lvl, srvmissilea, U.x, U.y)     ; p the creating unit (EDX)
     if m ≠ 0:
       UnitSetOwner(m, U)
       UnitAddStat(U, 19, PlayerBaseToHit(p), 0)
       UnitAddStat(U, 119, p.stat119 + the mastery bonus of p's weapon, 0)
     v1C ← 1
6. prm ← Head;  if prm = 0: Idle(3); return
7. Ovr(15, 0, 20)
   MonAiWalkToPointOrStop to the point v18 ≠ 0 ? (prm+0x14, prm+0x18) : (prm+0x0C, prm+0x10)
   if refused: v18 ← not v18;  walk to the other
   if both refused and not WanderNear(O, 5): Idle(5)
```

- R102c. [I] The missile's creating unit is `p`, the owner when there is one (`EDX` = `EDI`, 0x005EA65E), with `U` as the missile's owner set after it. (0x005EA65E, 0x005EA660, 0x005EA669, fn:sub_0056EDE0_MissileCreateAt@0x0056EDE0)
- R102a. [I] The creeper shuttles between the two points of its parameter record until its `calc4` life passes. The stats 19 and 119 go on the missile's owner chain (the creeper), from the owner's to-hit. `Skill1` is sign-extended (`movsx`). (fn:sub_0058EE80_AiParamsHead@0x0058EE80, fn:sub_0056EDE0_MissileCreateAt@0x0056EDE0, fn:sub_005EA540_AiBladeCreeper@0x005EA540)
- R102b. [C] The init and the Skill1 bound only: families `bladeinit` and `blade`, 240 cases each; the compare and unsigned-`Skill1` controls fail the 12 and 46 that separate `blade`. (run:2026-10-30-ai-cat-emu-5)

- R102i. [C] As data: kind 0, `init` 0x005EA510, no `alt`; 1 records (413 bladecreeper); reach S; `aip` set —; `aidel` 15/15/15; skills Blade Sentinel. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R102l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R103. Row 103 `InvisoPet` (fn:sub_005EA7A0_AiInvisoPet@0x005EA7A0)

**`aip`:** 1 half the side of the square around the owner; 2 the frames between teleports.

```
1. O ← MonsterOwner(U);  r ← aip(1);  om ← O ≠ 0 ? O.mode : 0              [I] (0x005EA7A0, 0x005EA97C)
2. if om = 3: r ← r ÷ 2                         ; owner running; signed, toward zero
3. if T ≤ v14 and om ≠ 3 and not St3or19: Idle(aip(2)); return
4. x ← O.x + R(2r) − r                          ; one inline step
5. y ← O.y + R(2r) − r                          ; one inline step
6. MonAiUseSkill(9, 292, 0, x, y);  v14 ← T + aip(2)    ; 292 Teleport 2
```

- R103a. [I] `R(n)` is one inline step, `& (n−1)` when `n` is a power of 2, else mod `n`; 0 for `n < 1`. Two steps per teleport (0x005EA884, 0x005EA8A1, 0x005EA903). `r ÷ 2` is `cdq; sub; sar` (0x005EA7F2–0x005EA7F5). With no owner the function reads `*O` (`mov eax,[ebx]`, 0x005EA836), a fault on that path: whether it is reached is Open questions. (fn:sub_005EA7A0_AiInvisoPet@0x005EA7A0)
- R103b. [C] The entry call `MonsterOwner` from 0x005EA7C0 only, before any test: family `inviso`, 240 cases; no control separates it. (run:2026-10-30-ai-cat-emu-5)

- R103i. [C] As data: kind 0, no `init`, no `alt`; 1 records (414 invisopet); reach ·; `aip` set 1,2; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R103l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R104. Row 104 `DeathSentry` (fn:sub_005EA980_AiDeathSentry@0x005EA980)

**`aip`:** 2 the idle; 3 chance of `Skill2`; 4 the hostile's distance for it.

`init` and `charge` are [row 101's](#r101-row-101-assassinsentry-fnsub_005ea3d0_aiassassinsentry0x005ea3d0).

```
1. if charge(ctx, 0): return                                               [I] (0x005EA980, 0x005EAB14)
2. sk ← SKILLS_GetUnitSkill(U, Skill1);  lvl ← SkillLevel(U, sk, 1)
   if sk = 0 or lvl < 1: return
3. h ← FindHostile(&d, &m)
   if h = 0: Idle(aip(2)); return
4. c ← CorpsePickNear(h; Skill1, lvl);  r ← SkillParam3ByLevel(Skill1, lvl) ÷ 2     ; around the hostile; signed, toward zero
5. if c ≠ 0 and c.guid ≠ v14 and EdgeDist(h, c) < r:
     if charge(ctx, 1): return
     v14 ← c.guid
     MonAiUseSkill(9, Skill1, c, 0, 0); return
6. if d < aip(4) and Range(100) < aip(3):              ; draw#1
     if charge(ctx, 1): return
     MonAiUseSkill(14, Skill2, h, 0, 0); return
7. Idle(aip(2))
```

- R104a. [I] `v14` is the last corpse it exploded, so it never explodes the same corpse twice running. Its modes 9 and 14 are passed as immediates. (fn:sub_005EA980_AiDeathSentry@0x005EA980, fn:sub_005EA2B0_AiSentryCharge@0x005EA2B0)
- R104b. [C] The entry call only, as row 101's: family `dsentry`, 240 cases; no control separates it. (run:2026-10-30-ai-cat-emu-5)

- R104i. [C] As data: kind 0, `init` 0x005EA290, no `alt`; 1 records (416 deathsentry); reach S; `aip` set 1,3,4; `aidel` 15/15/15; skills mon death sentry, death sentry ltng. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R104l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R105. Row 105 `ShadowWarrior` (fn:sub_005EAFA0_AiShadowWarrior@0x005EAFA0)

**`aip`:** 1 the target's distance limit; 2 the owner's distance limit; 3 the base of the plain-attack chance; 4 the amount that decays `v18`; 8 three parameters by column: `aip8[n]` the skill read at init (268), `aip8[m]` the floor of the reset, `aip8[h]` the cap.

```
init (0x005EAF50):                                                         [I] (0x005EAF50, 0x005EAF72)
  v1C ← 1
  O ← MonsterOwner(U)
  if O ≠ 0: v1C ← the owner's level in skill aip8[n]     ; SKILLS_GetUnitSkill(O, aip8[n]), 268

think:                                                                     [I] (0x005EAFA0, 0x005EB41C)
1. UNIT_CancelEvents(2, 0)
2. if O = 0: Idle(100); return
3. cap ← clamp(aip8[h], 1, 256)
   v18 ← v18 + (−1 − aip(4))
   if v18 < 0 or v18 > 64·cap: v18 ← 0
4. if dist > aip(1) or UnitEdgeDistance(U, O) > aip(2): t ← 0
5. if AiPetGuard(t, O, melee, ctx, 0, 6): return
6. if t = 0: Idle(25); return
7. r ← O's right skill;  l ← O's left skill;  if r = 0 or l = 0: Idle(25); return
   add r's and l's ids to U at AiShadowWarriorSkLvl               ; v1C ÷ 3 + level ÷ 2, at least 1 (0x00647280)
   find both on U;  if either is missing: Idle(25); return
8. pick ← r when Range(2) = 0, else l                             ; draw#1
   p ← clamp(aip(3) − 2·max(v1C, 1), 5, 100)
   if melee and Range(100) < p: pick ← U's skill 0, id 0          ; draw#2, its attack, only in melee
9. if not AiShadowSkillRoll(pick):
     pick ← r when pick was l, else l                             ; after a skill-0 pick, l
     if not AiShadowSkillRoll(pick):
       pick ← U's skill 0;  when missing: add it at level 1 and find it again
10. if pick = 0: Idle(25); return
11. if RangeType(pick) = 1 and not melee: RunToUnit(t); return
    MonAiUseSkill(SkillMode(pick), id, t, 0, 0)
    v14 ← T + 18 + delay ÷ 3                    ; delay: the record's +0x190 calc at max(level, 1), signed, truncating
```

`AiShadowSkillRoll(owner, skill, id, melee, ctx)`, three draws per tried skill, [I] (0x005EAD50, 0x005EAEFA):

```
if the id is not the owner's class's skill (0x00645040(id) ≠ O+0x04) or AiShadowSkillFits refuses: return 0
if id = 0: return 1
q ← 0x006459F0(id, level)
if Range(100) > 100 − 160·q ÷ 100: return 0                ; draw
if T < v14: return 0
lo ← clamp(aip8[m], 1, 128)
if v18 is outside [lo, 32·clamp(aip8[h], 1, 256)]: v18 ← lo
a ← Range(v18);  b ← Range(100)                            ; draws
if b < a: return 0
v18 ← v18 + (320 − v1C)·q ÷ (v1C + 100)
return 1
```

- R105a. [I] The block was checked against its anchored instructions, and steps 5 to 10 corrected from them ([ai/0006 § 2.10](../../../findings/ai/0006-summons.md) holds the dated correction); the finding's source-file strings are `.\Ai\AiThink4.cpp` lines 0xB59 and 0xB5A at the skill adds. `AiPetGuard` and `PetMove` are [T67's](machinery.md#t67-row-67-necropet-and-state-7-fnsub_005e4cf0_ainecropet0x005e4cf0). (fn:sub_005EAFA0_AiShadowWarrior@0x005EAFA0, fn:sub_005EAD50_AiShadowSkillRoll@0x005EAD50, fn:sub_005EABF0_AiShadowSkillFits@0x005EABF0, fn:sub_005EAF00_AiShadowWarriorSkLvl@0x005EAF00, fn:sub_005E45D0_AiPetGuard@0x005E45D0)
- R105b. [C] The init's store of `v1C` and its `MonsterOwner` call (0x005EAF64); the think's first call `UNIT_CancelEvents(2, 0)` (0x005EAFCF), and no more: families `swinit`, `swarrior`, 240 cases each; no control separates them. (run:2026-10-30-ai-cat-emu-5)

- R105i. [C] As data: kind 2, `init` 0x005EAF50, no `alt`; 1 records (417 shadowwarrior); reach S; `aip` set 1,2,3,4,8; `aidel` 15/15/15; skills Fists of Fire, Blade Fury, Blades of Ice, Dragon Claw, Dragon Flight, Claws of Thunder, Attack. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R105l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R106. Row 106 `ShadowMaster` (fn:sub_005EB970_AiShadowMaster@0x005EB970)

**`aip`:** 2 three parameters by column (`aip2[h]` squared the owner's distance, `aip2[m]` a target's distance that holds it, `aip2[n]` the scoring draw's range, 20 for `shadowmaster`, as data); 3 the base of the plain-attack chance; 8 `aip8[n]` the skill read at init (279). `aip1[h]` is read by a score term (step 13).

```
init (0x005EB490):                                                         [C] (0x005EB4B4, run:2026-10-30-ai-cat-emu-5)
  v14 ← 0;  v18 ← 0;  v1C ← 1;  O ← MonsterOwner(U)
init, after that call:                                                     [I] (0x005EB490, 0x005EB5B8)
  if O is a player (O+0x00 = 0): v1C ← the owner's level in aip8[n]
  add the skill-0 entry at level 1 when missing;  set the left and right skills to 0
  copy every skill of the unit's class (0x00646140 count, 0x006460F0 per index)
    that AiShadowSkillAllowed admits, at AiShadowMasterSkLvl(O, v1C)       ; level ÷ 2 + v1C ÷ 2, in [1, 24]

think, entry:                                                              [C] (0x005EB9B8, 0x005EB9C8, run:2026-10-30-ai-cat-emu-5)
  if U+0xA8 = 0: Idle(100); return                                         ; the skill list head
  O ← MonsterOwner(U)

think:                                                                     [I] (0x005EB9D9, 0x005EC62E)
1. UNIT_CancelEvents(2, 0)
2. if O ≠ 0 and DistSq(U, O) > aip2[h]²:
     if AiPetGuard(0, O, melee, ctx, 0, 6): return
3. if v14 > 0:                                  ; a pending sequence, set at step 14
     t ← UNIT_GetTargetUnit(U) when non-zero
     if t = 0: v14 ← 0;  v18 ← 0
     else:
       v14 ← v14 − 1
       if Use(v18, melee, t): return
4. if dist > aip2[m]: t ← 0                     ; dist is the event's
5. if t = 0: for each of U's skills whose record exists:
     aitype 1, aurastate > 0, U lacks that state:
       if AiStateGroupHeld(U, aurastate) and Range(100) ≥ 4: next    ; draw only when held
       if D100() ≥ 60: next                                          ; inline step
       s ← the skill on U;  if s = 0: next
       if RangeType(s) = 1 and not melee: x ← RunToUnitFlags(0, 4)
       else: x ← MonAiUseSkill(SkillMode(s), id, 0, 0, 0)
       if x ≠ 0: return
     aitype 6, no left skill set:
       if D100() < 20: it becomes the left skill                     ; inline step, no command
6. o ← 0
   if O ≠ 0:
     g ← UNIT_GetTargetUnit(O);  if g ≠ 0, not dead and hostile to U: t ← g;  o ← g
     if DistSq(U, O) ≤ 144 and AiPetGuard(t, O, melee, ctx, 0, 6): return
7. if t = 0: Idle(25); return
8. p ← clamp(aip(3) − 2·max(v1C, 1), 5, 100)
   if melee and Range(100) < p and Use(0, melee, t): return          ; draw only in melee
9. AiUnitSearch(blk, AiShadowMasterCb, 1)       ; blk+0 = O, no draw; R106b
10. if not melee:
      if o ≠ 0: t ← o
      else if the hostile nearest O exists: t ← it
      else if a priority target exists and DistSq(U, it) < 1024: t ← it
      unless AiShadowPriorityTarget(U, t):
        w ← MonsterOwner(t);  if w ≠ 0, not dead and DistSq(U, w) < 1024: t ← w
11. n ← blk's count of hostiles within 10 of U
    if n > 3 and Range(32) < 2·n:
      if O ≠ 0 and DistSq(U, O) > 36: RunToUnit(O); return
      if StepAwayXY(t, 8, 1): return
12. L[0] ← (t, skill 0, score 0, 0, 0);  k ← 1
13. for each of U's skills whose record exists:
      score ← aibonus + reqlevel ÷ 4 + level − res ÷ 10
        ; res the stat of the target for the skill's EType, 36, 39, 41, 37, 43, 45
      by aitype (1–13): its terms and target, or next;  a kept one draws score ← score + Range(aip2[n])
      if score > L[k − 1].score: L[k] ← (target, id, score, 0, 0);  k ← k + 1
14. while k > 0:
      k ← k − 1;  one inline step                ; the seed's new low word
      if low word & 3 ≠ 0 and Use(L[k].id, InMeleeRange(U, L[k].target, 0), L[k].target):
        if the id's record has +0x2E = 19: v18 ← the id;  v14 ← 25
        return
15. if t ≠ 0 and Use(0, InMeleeRange(U, t, 0), t): return
16. Idle(15)

Use(id, m, x), AiShadowUseSkill:                                           [I] (0x005EB8B0, 0x005EB961)
  if x ≠ 0 and (x = O or x = U): return 0
  s ← the skill on U;  if s = 0: return 0
  if x ≠ 0 and (x+0xC4 bit 0x04 is clear or U's room is a town): return 0
  if RangeType(s) = 1 and not m: return RunToUnitFlags(x, 4)
  return MonAiUseSkill(SkillMode(s), id, x, 0, 0)
```

- R106a. [I] The block was checked against its anchored instructions, and steps 2 to 16 corrected from them ([ai/0006 § 2.11](../../../findings/ai/0006-summons.md) holds the dated correction): `L` is a rising list with no "five best", each entry kept only over the last one's score; the plain attack's and the pick's commands go through `Use`. The function has 3 inline steps and 14 `RNG_Range` sites. Step 13's per-`aitype` terms are read by no finding: Open questions. A score list's `+8` and `+0xC` words are stored 0 at the one store (0x005EC528, 0x005EC52F). (fn:sub_005EB970_AiShadowMaster@0x005EB970, fn:sub_005EB490_AiShadowMasterInit@0x005EB490, fn:sub_005EB420_AiShadowMasterSkLvl@0x005EB420, fn:sub_005EAB20_AiShadowSkillAllowed@0x005EAB20, fn:sub_005EB6D0_AiShadowMasterCb@0x005EB6D0, fn:sub_005EB650_AiShadowPriorityTarget@0x005EB650, fn:sub_005EB7F0_AiStateGroupHeld@0x005EB7F0, fn:sub_005EB8B0_AiShadowUseSkill@0x005EB8B0)
- R106b. [I] `AiShadowMasterCb` on a live unit with `+0xC4` bit `0x04`, hostile to `U`: with `blk+0` set, `DistSq(O, unit)` ≤ 100 counts `blk+0x18`, and the smallest is kept at `blk+0x10` and `blk+0x14`; then within `DistSq(U, unit)` ≤ 1024: `blk+0x1C` counts, ≤ 100 counts `blk+0xC`, the smallest is kept at `blk+4` and `blk+8`, and a unit passing `AiShadowPriorityTarget` goes to `blk+0x24`. An ally (`AlignSame02`) of base 410 to 416 but 414 only counts `blk+0x20`, by the callback's byte table. (0x005EB6D0, 0x005EB7D3)
- R106c. [C] Families `sminit` and `smaster` (the think, shared with row 143), 240 cases each; `smaster` has 2 outcomes, `Idle` 116 and `MonsterOwner` 124; no control separates them. (run:2026-10-30-ai-cat-emu-5)

- R106i. [C] As data: kind 2, `init` 0x005EB490, no `alt`; 1 records (418 shadowmaster); reach S; `aip` set 1,2,3,8; `aidel` 15/15/15; skills Fists of Fire, Blade Fury, Blades of Ice, Dragon Claw, Dragon Flight, Claws of Thunder, Attack. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R106l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R107. Row 107 `Raven` (fn:sub_005ECC10_AiRaven@0x005ECC10)

**`aip`:** 1 and 2 the far and near edge of the circling band (`mid ← (aip(2) + aip(1)) ÷ 2`); 3 the attack cooldown in tens of frames; 4 chance to act; 5 the target's distance limit.

```
init (0x005ECB70):                                                         [C] (0x005ECB70, run:2026-10-30-ai-cat-emu-5)
  v14 ← −1;  v18 ← aip(3) + 1;  v1C ← bit 0 of one seed step's low word    ; one inline step, no mod

think:                                                                     [I] (0x005ECC10, 0x005ECED6)
1. if O = 0 or M = 0: Idle(10); return
2. if v14 = −1:
     v14 ← 3
     if Skill1 ≥ 0: v14 ← SkillParam5ByLevel(Skill1, SkillLevel(O, SKILLS_GetUnitSkill(O, Skill1), 1))
   else if v14 = 0: UnitKilled(G, U, U, 1); return                ; hits used up; U its own killer
3. r ← Dist(U, O)
   if r > 50: PetMove(O; U, 3, 0, 0, 0); return
4. s ← the run speed term, as row 67's
   if r > 28: PetMove(O; U, 0, 0, s, 0); return
5. FindTarget(ctl, &e, &m');  mid ← (aip(2) + aip(1)) ÷ 2
6. if t ≠ 0 and v18 < T and Range(100) < aip(4) and dist < aip(5):        ; draw#1
     if melee: SetModeAtUnit(4, t);  v14 ← v14 − 1;  v18 ← T + 10·aip(3); return
     Walk(t, 0); return
7. if aip(1) ≥ r and r ≥ aip(2):
     AiRavenCircle(O, 4, v1C ≠ 0 ? 5 : 6), or flip v1C and circle again   ; each returns on a command
8. if not WalkAround(ctl, O, mid): PetMove(O; U, 1, 0, 0, 0)              ; 0x005DE6F0
```

- R107d. [I] The kill passes `U` as the killer too (`push edi`, 0x005ECCCD). (0x005ECCCD, fn:sub_0057CCB0_UnitKilled@0x0057CCB0)
- R107a. [I] `v14` is the raven's hit count, read from `Skill1` (`Raven`) at **the owner's** level in it, and the raven dies when it reaches 0. Every attack is `SetModeAtUnit(4, t)` through `MonSetMode`, whose `MonAttackStats` adds the owner pair (`SkillDamage` = `Raven`, the owner's level in it). (fn:sub_005ECC10_AiRaven@0x005ECC10, fn:sub_005ECB70_AiRavenInit@0x005ECB70, fn:sub_005ECBC0_AiRavenCircle@0x005ECBC0, fn:sub_005A7C20_MonSetMode@0x005A7C20, fn:sub_0056E050_MonOwnerSkillDamage@0x0056E050)
- R107b. [C] The 2 218 `MonAttackStats` calls of class 419 take the owner pair at level 20, for that one level and the sessions' one player, who cast them; which unit is the owner and the terms that level does not separate stay `[I]`. ([monsters/stats H1](../stats.md), run:2026-11-04-ai-resume, fn:sub_0056E050_MonOwnerSkillDamage@0x0056E050)
- R107c. [C] The init, its stores and one seed step, with `v18` = `aip(3)` (i16) + 1 by difficulty; the think's entry call `MonsterOwner` from 0x005ECC27 only: families `ravinit` (240 cases, all drawing; the Normal-column control fails the 153 it separates) and `raven` (240 cases; no control separates it). (run:2026-10-30-ai-cat-emu-5)

- R107i. [C] As data: kind 2, `init` 0x005ECB70, no `alt`; 1 records (419 druidhawk); reach S; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Raven. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R107l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R108. Row 108 `DruidWolf` (fn:sub_005ED710_AiDruidWolf@0x005ED710)

**`aip`:** 1 the delay after A1; 2 chance to wander, with no target; 3 the wolf: the edge distance past which it follows by the owner's mode; Fenris: `Range(100) ≥ aip(3)` with a target and `v14` = 0 skips the corpse (14/25, as data); 4 the distance limit, Fenris's follow distance too, and his corpse limit at half (20/24, as data); 5 the edge distance past which it moves at speed 100.

The row's think is a class dispatch: class 420 (`spiritwolf`, `cmp [edx+4],0x1a4; jne`) jumps to `AiSpiritWolf`, any other class to `AiFenris`.

```
spirit wolf (0x005ECEE0):                                                  [I] (0x005ECEE0, 0x005ED29A)
1. if O = 0:
     w ← GameFindUnit(0, v1C)                             ; only when v1C ≠ 0; the remembered owner
     if w ≠ 0 and Skill1 ≥ 0:
       MonAiUseSkill(Sk1mode, Skill1, 0, w's subtile x, w's subtile y)     ; its Teleport 2
       UnitQueueEvent(U, 0, T + 6, 0, 0);  Delay(8)
     else: Idle(10)
     return
2. v1C ← O's id (O+0x0C)
3. if in town: if not AiPetGuard(0, O, 0, ctx, 0, 6): Idle(33)
              return
4. t ← 0x005DDE50(ctl, &e, &m, aip(4));  if t ≠ 0 and not AiApproachPointTest(t): t ← 0
   g ← FindTarget as the owner (MonAiFindTarget with O)
   if t = 0 and g ≠ 0 and AiDistUnits(U, g) < aip(4) and AiApproachPointTest(g) = 0: t ← g   ; the test's sense reversed from t's
5. s ← 100;  if Velocity > 0: s ← min(Run·100 ÷ Velocity − 100, 100)
6. f ← UnitEdgeDistance(O, U)
   if Skill1 ≥ 0 and f > 50:
     MonAiUseSkill(Sk1mode, Skill1, 0, O's subtile x, O's subtile y)
     UnitQueueEvent(U, 0, T + 4, 0, 0);  Delay(10); return
7. if f > aip(5) and PetMove(O; U, 0, 1, 100, 0): return
8. if f > aip(3):
     O's mode 2 or 6: if PetMove(O; U, 0, 0, 0, 0): return
     O's mode 3:      if PetMove(O; U, 0, 1, 100, 0): return
9. if AiPetGuard(t, O, m, ctx, 1, 6): return
10. if t ≠ 0:
      if m: SetModeAtUnit(4, t);  Delay(aip(1))
      else if UnitEdgeDistance(O, t) < aip(4): Ovr(0, s, 0);  RunToUnit(t)
      else if f > 10: WalkToward(O, 8, 6)
      else: Idle(15)
11. else if Range(100) < aip(2): Ring(10)
    else: Idle(15)

Fenris (0x005ED2A0):                                                       [I] (0x005ED2A0, 0x005ED70A)
1. steps 1 to 3 as the wolf's, with Skill2 and Sk2mode as the teleport
2. step 4, but g is taken when the distance FindTarget returned for it is below aip(4) and AiApproachPointTest(g) ≠ 0
3. f ← UnitEdgeDistance(O, U)
   if t ≠ 0 and f > aip(4) and UnitEdgeDistance(O, t) > aip(4): t ← 0
4. s as the wolf's
5. if Skill2 ≥ 0 and f > 50:
     the teleport to O's subtile position;  UnitQueueEvent(U, 0, T + 2, 0, 0);  Delay(10); return
6. if f > aip(5) or (f > aip(4) and O's mode 3): PetMove(O; U, 0, 1, 100, 0); return
   if f > aip(4) and O's mode 2 or 6: PetMove(O; U, 0, 0, 0, 0); return
7. if AiPetGuard(t, O, m, ctx, 1, 6): return
8. skip ← state 138 set or Skill1 < 0
   if not skip:
     if Range(100) ≥ aip(3) and t ≠ 0 and v14 = 0: skip ← true      ; draw#1
   if skip: v14 ← 0
   else:
     c ← 0x005D2F80(O, 10)
     if c ≠ 0 and UnitEdgeDistance(c, U) < aip(4) ÷ 2:
       if InMeleeRange(U, c, 0): v14 ← 0;  UseSkill1(c); return
       if not m: RunToUnit(c);  v14 ← 1;  v18 ← c's id; return
9. if m: SetModeAtUnit(4, t);  Delay(aip(1)); return
10. if t ≠ 0: Ovr(0, s, 0);  RunToUnit(t); return
11. if Range(100) < aip(2): Ring(10)                                  ; draw#2
    else: Idle(15)
```

- R108a. [I] Fenris draws twice at most, the wolf once. The block was checked against its anchored instructions, which give the chain the finding only named, and differ from the finding's "then as the wolf" ([ai/0006 § 2.12](../../../findings/ai/0006-summons.md) holds the dated correction): the wolf's second target is kept when `AiApproachPointTest` returns 0 (0x005ED064), Fenris's and row 112's when it does not (0x005ED41C, 0x005ED8DB). (fn:sub_005ED710_AiDruidWolf@0x005ED710, fn:sub_005ECEE0_AiSpiritWolf@0x005ECEE0, fn:sub_005ED2A0_AiFenris@0x005ED2A0)
- R108b. [C] The class dispatch only, met at classes 419, 420 and 421, each path calling `MonsterOwner` first (0x005ECEFD, 0x005ED2BD): family `dwolf`, 240 cases, 91 and 149; no control moves that test. (run:2026-10-30-ai-cat-emu-5)

- R108i. [C] As data: kind 0, no `init`, no `alt`; 2 records (420-421 spiritwolf..fenris); reach S; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Teleport 2, fenris rage. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R108l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R109. Row 109 `Totem` (fn:sub_005ED9E0_AiTotem@0x005ED9E0)

**`aip`:** 1 chance to step away from a near hostile; 2 chance to drop the target; 3 the edge distance past which it teleports; 4 the edge distance past which it follows.

```
1. if O = 0: Idle(10); return                                              [I] (0x005ED9E0, 0x005EDBF5)
2. h ← OwnerNearHostile(ctl, &d, &m, 24)                      ; 0x005DDE50
3. if m ≠ 0 and h ≠ 0 and D100() < aip(1) and StepAway(h, 6, 1): return   ; draw#1, only when m and h are set
4. if D100() < aip(2): h ← 0;  m ← 0                          ; draw#1 or #2
5. e ← EdgeDist(U, O)
6. if e > aip(3) and UnitTeleport(room(O), O.x, O.y, 0, 0): Idle(25); return
7. if e > aip(4):
     owner mode 2 or 6: PetMove(kind 0)
     mode 3: PetMove(kind 0, speed 60)                        ; each returns on a command
8. if not AiPetGuard(h, O, m, ctx, 0, 6): Idle(25)
```

- R109a. [I] One or two inline steps (0x005EDA3D, 0x005EDA96). (fn:sub_005ED9E0_AiTotem@0x005ED9E0, fn:sub_00554EA0_UnitTeleport@0x00554EA0)
- R109b. [C] The entry call `MonsterOwner` from 0x005ED9EF only: family `totem`, 240 cases; no control separates it. (run:2026-10-30-ai-cat-emu-5)

- R109i. [C] As data: kind 0, no `init`, no `alt`; 3 records (422-424 spiritofbarbs..oaksage); reach S; `aip` set 1,2,3,4; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R109l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R110. Row 110 `Vines` (fn:sub_005EC6C0_AiVines@0x005EC6C0)

**`aip`:** 1 the frames between hits; 2 the hostile's distance limit; 3 the idle; 4 the step away's length; 5 the edge distance from the owner at which it moves.

```
init 0x005EC6A0:  v14 ← 0                                                  [C] (run:2026-10-30-ai-cat-emu-5, 0x005EC6A0)

1. O ← MonsterOwner(U);  if O = 0: Idle(25); return                        [I] (0x005EC6C0, 0x005EC8B5)
2. if UnitEdgeDistance(U, O) ≥ aip(5) and PetMove(O; U, 3, 0, 0, 6): return
3. in town: if not AiPetGuard(0, O, 0, ctx, 0, 6): Idle(aip(3))
            return
4. h ← the FindHostile target, with e and m;  if e ≥ aip(2): h ← 0         ; m kept
5. if AiPetGuard(h, O, m, ctx, 0, 6): return
6. if h = 0: Idle(aip(3)); return
7. if h is in state 2 or has stat 45 = 100: StepAway(h, (u8) aip(4), 0)
   else if not m: Walk(h, 7)
   else if Skill1 ≥ 0 and T > aip(1) + v18: UseSkill1(h);  v18 ← T
   else: Idle(aip(3))
```

- R110a. [I] No draw. The block was checked against its anchored instructions; step 2's `≥` and steps 3 to 7's returns come from them ([ai/0006 § 2.7](../../../findings/ai/0006-summons.md) holds the dated correction). (fn:sub_005EC6C0_AiVines@0x005EC6C0, fn:sub_005EC6A0_AiVinesInit@0x005EC6A0)
- R110b. [C] The init's store and the think's first call `MonsterOwner` (0x005EC6DD) only: families `vinit`, `vines`, 240 cases each; no control separates them. (run:2026-10-30-ai-cat-emu-5)

- R110i. [C] As data: kind 2, `init` 0x005EC6A0, no `alt`; 1 records (425 plaguepoppy); reach S; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Vine Attack. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R110l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R111. Row 111 `CycleOfLife` (fn:sub_005EC8C0_AiCycleOfLife@0x005EC8C0)

**`aip`:** 1 the frames between casts; 2 the corpse's edge distance limit; 3 the idle; 4 the step away's length; 5 the edge distance from the owner at which it moves.

```
init 0x005EC6A0:  v14 ← 0                                                  [C] (run:2026-10-30-ai-cat-emu-5, 0x005EC6A0)

1. O ← MonsterOwner(U);  if O = 0: return                ; no command      [I] (0x005EC8C0, 0x005ECB67)
2. if UnitEdgeDistance(U, O) ≥ aip(5) and PetMove(O; U, 3, 0, 0, 6): return
3. if t ≠ 0 and UnitIsDead(t): t ← 0;  melee ← 0
4. c ← 0;  e ← 0
   if Skill1 > 0, its record exists and U has the skill:
     r ← the record's aurarangecalc at U's level in it, clamped to [5, 50]
     c ← 0x005D2F80(O, r);  if c ≠ 0: e ← UnitEdgeDistance(U, c)
   mc ← 0
   if e ≥ aip(2): c ← 0
   else if c ≠ 0: mc ← InMeleeRange(U, c, 0)
5. if AiPetGuard(c, O, mc, ctx, 0, 6): return
6. short ← 1
   class 426: if O's stat 6 ≥ UnitGetMaxHp(O): short ← 0
   class 427: if O's stat 8 ≥ UNIT_GetMaxMana(O): short ← 0
7. if c ≠ 0, mc, short and T > aip(1) + v18: MonAiUseSkill(8, Skill1, c, 0, 0);  v18 ← T; return
8. if melee and t ≠ 0 and Range(100) < 25: StepAway(t, (u8) aip(4), 0); return      ; draw#1, only with both
9. if c ≠ 0: Walk(c, 7)
   else: Idle(aip(3))
```

- R111a. [I] The block was checked against its anchored instructions, which give steps 2, 3 and 5, step 6's classes (426 life, 427 mana; the finding did not say) and the `aip(5)` read ([ai/0006 § 2.7](../../../findings/ai/0006-summons.md) holds the dated correction). (0x005ECA58, 0x005ECA78, fn:sub_005EC8C0_AiCycleOfLife@0x005EC8C0, tbl:Skills.txt:aurarangecalc)
- R111b. [C] The init's store and the think's first call `MonsterOwner` (0x005EC8DD) only: families `vinit`, `cycle`, 240 cases each; no control separates them. (run:2026-10-30-ai-cat-emu-5)

- R111i. [C] As data: kind 2, `init` 0x005EC6A0, no `alt`; 2 records (426-427 cycleoflife..vinecreature); reach S; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills CorpseCycler, VineCycler. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R111l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R112. Row 112 `DruidBear` (fn:sub_005ED730_AiDruidBear@0x005ED730)

**`aip`:** 1 the delay after A1; 2 out of melee range: chance of the override; 3 in melee range: chance of `BearSmite`.

```
1. if O = 0:                                                               [I] (0x005ED730, 0x005ED9DA)
     w ← GameFindUnit(0, v1C)                 ; only when v1C ≠ 0
     if w ≠ 0: PetMove(w; U, 3, 0, 0, 0)
     else: Idle(10)
     return
2. v1C ← O's id (O+0x0C);  r ← AiDistUnits(U, O)
3. if r > 50: PetMove(O; U, 3, 0, 0, 0); return
4. s ← 100;  if Velocity > 0: s ← min(Run·100 ÷ Velocity − 100, 100)
5. if r > 28: PetMove(O; U, 0, 0, 100, 0); return
6. if r > 18:
     O's mode 2 or 6: if PetMove(O; U, 0, 0, 0, 0): return
     O's mode 3:      if PetMove(O; U, 0, 0, 100, 0): return
7. g ← FindTarget as the owner (MonAiFindTarget with O)
   t ← 0x005DDE50(ctl, &e, &m, 28)
   if t ≠ 0 and not AiApproachPointTest(t): t ← 0;  then g is tried
   if t = 0 and g ≠ 0 and AiDistUnits(U, g) < 28 and AiApproachPointTest(g) ≠ 0: t ← g
8. if t ≠ 0 and m:
     if Range(100) < aip(3): MonAiUseSeqSkill(Skill1, t, 0, 0)            ; draw#1, BearSmite
     else: SetModeAtUnit(4, t);  Delay(aip(1))
     return
9. if t ≠ 0:
     if Range(100) < aip(2): Ovr(0, s, 40)                                ; draw#1
     WalkZ(t); return
10. if r > 16: PetMove(O; U, 0, 0, 0, 0)
    else: Idle(15)
```

- R112a. [I] The block was checked against its anchored instructions, which give steps 1 and 6 to 10; `m` is the output of 0x005DDE50's call, whichever target is kept. `s` is used only at step 9's override; the moves at steps 5 and 6 pass 100, not `s` ([ai/0006 § 2.12](../../../findings/ai/0006-summons.md) holds the dated correction). (fn:sub_005ED730_AiDruidBear@0x005ED730, fn:sub_005DECA0_MonAiWalkToUnitOrZero@0x005DECA0)
- R112b. [C] The entry call `MonsterOwner` from 0x005ED747 only: family `bear`, 240 cases; no control separates it. (run:2026-10-30-ai-cat-emu-5)

- R112i. [C] As data: kind 0, no `init`, no `alt`; 1 records (428 druidbear); reach S; `aip` set 1,2,3; `aidel` 15/15/15; skills BearSmite. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R112l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R143. Row 143 `ShadowMasterNoInit` (fn:sub_005EB970_AiShadowMaster@0x005EB970)

The think is [row 106's](#r106-row-106-shadowmaster-fnsub_005eb970_aishadowmaster0x005eb970), the same word (0x005EB970). No MonStats record names this row. Its own init differs:

```
init (0x005EB5C0):                                                         [C] (0x005EB5D6, run:2026-10-30-ai-cat-emu-5)
  v1C ← 1;  O ← MonsterOwner(U)
init, after that call:                                                     [I] (0x005EB5C0, 0x005EB644)
  if O is a player (O+0x00 = 0): v1C ← the owner's level in aip8[n]
  add the skill-0 entry at level 1 when missing;  set the left and right skills to 0
```

- R143a. [I] Unlike row 106's init it stores no `v14` or `v18` and does not copy the class's skills. (fn:sub_005EB5C0_AiShadowMasterNoInitInit@0x005EB5C0)
- R143b. [C] Family `sm2init`, 240 cases; no control separates it. (run:2026-10-30-ai-cat-emu-5)

- R143i. [C] As data: kind 2, `init` 0x005EB5C0, no `alt`; 0 records (—); reach none; `aip` set —; `aidel` —; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R143l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### S7. State row 7 (fn:sub_005E4CF0_AiNecroPet@0x005E4CF0)

Tier: the think is row 67's, the same word, [machinery § T67](machinery.md#t67-row-67-necropet-and-state-7-fnsub_005e4cf0_ainecropet0x005e4cf0). [I] (fn:sub_005E4CF0_AiNecroPet@0x005E4CF0)

- S7i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

### Batch 6: hirelings

#### R61. Row 61 `Hireable` (fn:sub_005E52D0_AiHireable@0x005E52D0)

Tier AI: [machinery § T61](machinery.md#t61-row-61-hireable-and-state-4-fnsub_005e52d0_aihireable0x005e52d0), not repeated here.

#### S4. State row 4 (fn:sub_005E52D0_AiHireable@0x005E52D0)

Tier: the think and the alt are row 61's, the same words, [machinery § T61](machinery.md#t61-row-61-hireable-and-state-4-fnsub_005e52d0_aihireable0x005e52d0). [I] (fn:sub_005E52D0_AiHireable@0x005E52D0)

- S4i. [C] As data: kind 0, no `init`, `alt` 0x005E5280. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S5. State row 5 (fn:sub_005E7AC0_AiGoodNpcRanged@0x005E7AC0)

No `aip` read: the bounds are constants. `Skill1` is read for class 271 only. Also the think of [row 60](#r60-row-60-goodnpcranged-fnsub_005e7ac0_aigoodnpcranged0x005e7ac0).

```
1. if U = 0 or U.mode ≠ 1: Idle(5); return                                 [I] (0x005E7AC0, 0x005E7AD1, 0x005E7AF2)
2. if not InTown(U):
     h ← FindHostile(&e, &m)
     if h ≠ 0 and e < 20:                       ; signed jge
       if Range(100) < 30:                      ; draw#1
         if U.class = 271: UseSkill1(h)
         else: SetModeAtUnit(4, h)
         return
       if Range(100) < 30: T56(h, 4, 0); return ; draw#2
       Idle(10); return
3. if D100() < 20: Ring(5); return              ; inline step, 0x005E7BB5
4. Idle(10)
```

- S5a. [I] The state is set by row 61's own `MonAiInit(ctl, 5)`, for the unowned hireling, through the alt's one-event bridge ([T61](machinery.md#t61-row-61-hireable-and-state-4-fnsub_005e52d0_aihireable0x005e52d0)). A `rogue2`, row 60's one record, runs the same code with class ≠ 271, hence A1 in place of the skill. (fn:sub_005E7AC0_AiGoodNpcRanged@0x005E7AC0, fn:sub_005B0E00_MonAiInit@0x005B0E00, tbl:MonStats.txt:Sk1mode)
- S5b. [C] The map to `RoomIsTown` only. (run:2026-10-30-ai-cat-emu-6, fn:sub_005E7AC0_AiGoodNpcRanged@0x005E7AC0)

- S5i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S6. State row 6 (fn:sub_005E7C10_AiHireUnowned@0x005E7C10)

No `aip` read.

```
1. if U = 0 or U.mode ≠ 1: Idle(5); return                                 [I] (0x005E7C10, 0x005E7C37)
2. if not InTown(U):
     h ← FindTarget(ctl, &e, &m)
     if h ≠ 0:
       r ← Range(100)                           ; draw#1
       if m = 0:
         if r < 30: Walk(h, 7)
         else: Idle(10)
       else:
         if r < 80: SetModeAtUnit(4, h)
         else: Idle(10)
       return
3. if D100() < 20: Ring(5); return              ; inline step, 0x005E7CCD
4. Idle(10)
```

- S6a. [I] Set by row 61's `MonAiInit(ctl, 6)`, as state 5. (fn:sub_005E7C10_AiHireUnowned@0x005E7C10, fn:sub_005DD7F0_MonAiFindTarget@0x005DD7F0)
- S6b. [C] The map to `RoomIsTown` only. (run:2026-10-30-ai-cat-emu-6, fn:sub_005E7C10_AiHireUnowned@0x005E7C10)

- S6i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

### Batch 7: bosses-A

#### R34. Row 34 `Andariel` (fn:sub_005F5830_AiAndariel@0x005F5830)

Tier AI: [machinery § T34](machinery.md#t34-row-34-andariel-fnsub_005f5830_aiandariel0x005f5830), not repeated here.

#### R44. Row 44 `Duriel` (fn:sub_005F67B0_AiDuriel@0x005F67B0)

**`aip`:** 1 the level of the aura `Skill4` (5/5/6, as data); 2 melee: chance of `Skill3` (33, as data); 3 melee: chance of `Skill2` (50, as data); 4 melee: chance of A2 (0, as data); 5 out of melee range: chance of `Skill1` (0, as data).

```
1. if Skill4 ≥ 0 and UNIT_GetRightSkill(U) = 0:                            [I] (0x005F67E3, 0x005F680B)
     UnitSkillAdd(U, Skill4, aip(1), 1);  PlayerSetSkill(U, 0, Skill4, −1)  ; the aura, Holy Freeze
2. if not melee:                                                           [I] (fn:sub_005F67B0_AiDuriel@0x005F67B0)
     if Skill1 ≥ 0 and D100() < aip(5): UseSkill1(t); return     ; draw#1
     Ovr(13, 0, 0);  Walk(t, 7); return
3. if Skill3 ≥ 0 and D100() < aip(2): UseSkill3(t); return       ; draw#1, Smite
4. if Skill2 ≥ 0 and D100() < aip(3): UseSkill2(t); return       ; draw#2, Jab
5. if D100() < aip(4): SetModeAtUnit(5, t); return               ; draw#3
6. SetModeAtUnit(4, t)
```

- R44a. [I] With stock data the A2 and `Charge` arms are never taken (`draw < 0`), though each still makes its draw. So in melee range the code gives `Smite` 33 %, `Jab` 33.5 %, A1 33.5 %: a community disagreement that is under Open questions. (fn:UNIT_GetRightSkill@0x006201D0, fn:sub_0056DEB0_UnitSkillAdd@0x0056DEB0, fn:sub_005701B0_PlayerSetSkill@0x005701B0)
- R44b. [C] The map with `Skill4` < 0, to each first callee, and the `GetRightSkill` call with `Skill4` ≥ 0: family `duriel`, 240 cases, 149 with a draw, 7 outcomes; the `≤` and Normal-column controls fail the 27 and 44 that separate them, and each draw is met at equality. Past `GetRightSkill` stays `[I]`, as do the walks after `Ovr`. (run:2026-10-30-ai-cat-emu-6)

- R44i. [C] As data: kind 1, no `init`, no `alt`; 2 records (211 duriel, 708 uberduriel); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills Charge, Jab, Smite, Holy Freeze. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R44l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R50. Row 50 `Mephisto` (fn:sub_005F78B0_AiMephisto@0x005F78B0)

**`aip`:** 1 melee: `D100() ≤ aip(1)` gives state 2, else 3; 2 the pick: chance of the weakest (`+0x5C`); 3 the pick's second chance (`+0x62`), never reached from this row.

`L ← max(0, (100 − UnitLifePct(U)) ÷ 5)` (`imul 0x66666667; sar 1`, signed), and `life` is that percent. `v1C` is the stored state, `v14` the burst's remaining casts, `v18` the cast counter. `st` is the dispatch state.

```
1. L, life as above;  st ← v1C                                             [I] (0x005F78B0, 0x005F7960, 0x005F7B36, 0x005F7EEA)
2. if melee:
     if D100() > aip(1): st ← 3                        ; draw#1
     else: st ← 2;  v14 ← (step low mod 3) + 3         ; draw#2 (0xAAAAAAAB, shr 1)
   else if dist > 20: st ← 4
   else if v1C > 4: goto move                          ; unsigned
   else if v1C = 0:
     if life ≤ 20 and dist < 5 and D100() < 40: st ← 1 ; draw#1
     else if D100() < L + 50:                          ; draw
       st ← 2;  v14 ← (step low mod 3) + 3
     else:
     move:
       if D100() ≥ 65: v1C ← 0;  Idle(10); return
       if D100() ≥ 65 and dist ≤ 5: Ovr(0, 0, 4);  Walk(t, 7)
       else: T56(t, 4, 0)
       v1C ← 0; return
3. switch st:                                          ; g_AiMephistoStateJumps
   0: Idle(5);  v1C ← 4; return                        ; no path above dispatches 0
   1: Ovr(0, 50, 0)
      if StepAway(t, 8, 1): v1C ← 0; return
      if melee: UseSkill3(t);  v1C ← 0; return
      ; else fall into case 2 with st 0
   2: v14 ← v14 − 1;  if v14 = 0: st ← 0
      if v18 = 0:
        v18 ← 2
        if not T56(t, 3, 1): Ring(12)
        v1C ← st; return
      v18 ← v18 + 1
      t2 ← AiMephistoPickTarget(M, t)
      n ← the count of leading Skill1..8 ≥ 0
      if n ≤ 0: Ring(6)
      else:
        q ← 100 ÷ n;  r ← D100()
        if d > 0 and ((t2 ≠ 0 and UnitLineBlocked(U, t2, 4)) or dist > 30): UseSkill6(t2)
        else if dist < 15 and r < q and d > 0: UseSkill5(t2)
        else if r < 2·q: UseSkill4(t2)
        else if r < 3·q: UseSkill2(t2)
        else: UseSkill1(t2)
      if D100() < 50 − L: v18 ← 0
      v1C ← st; return
   3: st ← 0
      if Range(100) < L + 80:
        if Range(100) < 80 − L: SetModeAtUnit(4, t)
        else: UseSkill3(t)
      else:
        Ovr(0, 50, 0)
        if not T56(t, 3, 1): Ring(12)
      v1C ← 0; return
   4: st ← 0;  Ovr(0, 50, 0)
      if not WanderNear(t, 6):
        UNIT_CancelEvents(G, U, 2, 0)
        if not Toward(t, 12, 6): Ring(12)
      v1C ← 0; return
```

- R50a. [I] **The dispatch.** `jmp [eax*4 + 0x005F7EF0]` over five words. No path above dispatches 0: melee gives 2 or 3, `dist > 20` 4, a stored `v1C` of 1–4 itself, and a stored 0 takes the `v1C = 0` arm, so case 0 is not reached from this function. (0x005F7B36, data:g_AiMephistoStateJumps@0x005F7EF0, fn:sub_00621F20_UnitLifePct@0x00621F20)
- R50b. [I] **The casting burst.** `v18` counts casts and is cleared on `D100() < 50 − L`: the lower Mephisto's life, the longer the burst. The difficulty tests are `cmp byte [G+0x6D],0; jbe`: in Normal only `Skill4`, `Skill2` and `Skill1` are cast. Stock: six skills, so `n` = 6 and `q` = 16: in Normal `r < 32` `MephistoMissile`, `r < 48` `PrimeBolt`, else `PrimeLightning`. `Skill3` is cast only from cases 1 and 3, on `t`. (0x005F7C4B, 0x005F7C79, 0x005F7CBC, fn:sub_00622AA0_UnitLineBlocked@0x00622AA0, tbl:MonStats.txt:Skill6)
- R50c. [I] **The pick** `(game, unit, M, t)` runs `AiUnitSearch(G, U, &blk, 0x005F7700, 1)` with a ten-word block `{0, 0x7FFFFFFF, 0, 0, 0x7FFFFFFF, 0, 0x7FFFFFFF, 0, 0, 0}` at `EBP − 0x28`. The callback takes a living candidate other than the searcher with `Unit+0xC4` bit `0x4` that is hostile to it and within `UnitDistSq ≤ 1024`: `blk[7]++`, `blk[2]++` within 225, `blk[0..1]` the nearest, `blk[3..4]` the lowest `hitpoints >> 8` (stat 6, `sar`), and `blk[5..6]` the nearest only when the searcher's `Unit+0x00` is 0. The pick returns `blk[3]` on `D100() < aip(2)`, else, when `blk[5]` is set, a second draw `< aip(3)` returns `blk[3]` too; else `t`. Its one caller is this row, a monster, so `blk[5]` stays 0 and the second draw never happens. (0x005F7700, 0x005F78A3, 0x005F7BDE, fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0, fn:sub_005541B0_UnitIsDead@0x005541B0, fn:sub_00554200_UnitsHostile@0x00554200)
- R50d. [C] The entry call `UnitLifePct(U)` (0x005F78E6) and the pick's search call with its block only: families `mephisto`, `mpick`, 240 cases each; no control separates them. Its states stay `[I]`. (run:2026-10-30-ai-cat-emu-6)

- R50i. [C] As data: kind 1, no `init`, no `alt`; 1 records (242 mephisto); reach ·; `aip` set 1,2,3; `aidel` 15/10/6; skills PrimeLightning, PrimeBolt, PrimePoisonNova, MephistoMissile, MephFrostNova, Blizzard. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R50l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R53. Row 53 `Summoner` (fn:sub_005F85C0_AiSummoner@0x005F85C0)

**`aip`:** 1 chance to cast at all (85/93/98, as data); 2 chance of `Skill5` first (5, as data); 3 `D100() > aip(3)` flips the element (63, as data); 4 the nova's cooldown (40, as data); 5 `Skill4`'s cooldown (120/100/80, as data); 6 within 5: chance to step away (33/20/10, as data); 7 the nova's range (5/8/11, as data); 8 the bolt's range (40, as data).

`x, y` are always `t`'s, also when `t2` is the skill's target. `UseSkillK(a)` here is `MonAiUseSkill(SkKmode, SkillK, a, x, y)`.

```
1. if v14 = 0: A2Q5_BossSeen(G, U);  v14 ← 1                               [I] (0x005F85C0, 0x005F85ED, 0x005F8648, 0x005F89A0)
2. if dist < 5 and D100() < aip(6): StepAway(t, 6, 0)      ; draw#1, result not read
3. cold ← STATS_GetUnitStat(t, 43, 0) ≤ STATS_GetUnitStat(t, 39, 0)  ; coldresist ≤ fireresist
4. if D100() < aip(1):                                     ; draw#2
     if Skill5 ≥ 0 and D100() < aip(2): UseSkill5(t); return  ; Weaken; draw#3
     t2 ← FindHostile(&e, 0)
     if D100() > aip(3): cold ← not cold
     if cold:
       if Skill2 ≥ 0 and v18 < T and dist < aip(7): goto nova
       if Skill1 ≥ 0 and t2 ≠ 0 and dist < aip(8): UseSkill1(t2); return
     if Skill4 ≥ 0 and v1C < T: v1C ← T + aip(5);  UseSkill4(t); return
     if Skill3 ≥ 0 and t2 ≠ 0 and dist < aip(8): UseSkill3(t2); return
     if not cold and Skill2 ≥ 0 and v18 < T and dist < aip(7):
     nova:
       v18 ← T + aip(4);  UseSkill2(t); return
     if Skill5 ≥ 0: UseSkill5(t); return
5. Ring(4)
```

- R53a. [I] The step away does not end the event. The timers compare signed with `T`. Stock: `Skill1` `Glacial Spike`, `Skill2` `Frost Nova`, `Skill3` `Fire Ball`, `Skill4` `VampireFirewall`, `Skill5` `Weaken`. (fn:sub_0059C330_A2Q5_BossSeen@0x0059C330, fn:sub_005DEFE0_MonAiStepAway@0x005DEFE0, tbl:MonStats.txt:aip8)
- R53b. [C] The map up to the first `STATS_GetUnitStat(t, 43, 0)` only: family `summoner`, 240 cases, 93 with a draw, 3 outcomes; the `≤`, Normal-column and compare controls fail the 8, 16 and 36 that separate them. (run:2026-10-30-ai-cat-emu-6)

- R53i. [C] As data: kind 1, no `init`, no `alt`; 1 records (250 summoner); reach U; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/13/10; skills Glacial Spike, Frost Nova, Fire Ball, VampireFirewall, Weaken. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R53l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R55. Row 55 `Izual` (fn:sub_005F89B0_AiIzual@0x005F89B0)

**`aip`:** 1 melee: chance to attack (45/50/50, as data); 2 out of melee range: chance to walk (50, as data); 3 within 10: chance of the cast (66, as data); 4 melee: chance of the cast (0/75/100, as data, so in Normal the melee cast never happens); 5 the idle after a cast (20/5/0, as data); 6 the plain events after a cast (3/4/4, as data).

```
1. if v14 = 0: v14 ← 1;  A4Q1_IzualSeen(G)                                 [I] (0x005F89B0, 0x005B4390, 0x005B43C2)
2. if v18 ≠ 0: Idle(v18);  v18 ← 0; return
3. if melee:
     if v1C < 1 and not (D100() < aip(1)):            ; inline
       v1C ← 0
       if Skill1 < 0 or not (Range(100) < aip(4)): Idle(aidel); return
     cast:
       MonAiUseSkill(Sk1mode, Skill1, t, x, y);  v18 ← aip(5);  v1C ← aip(6); return
     if v1C > 0: v1C ← v1C − 1
     SetModeAtUnit(4, t); return
4. if Skill1 ≥ 0 and dist < 10:
     if v1C > 0: Walk(t, 7); return
     if Range(100) < aip(3): goto cast
5. if v1C < 1 and not (D100() < aip(2)):              ; inline
     if dist < 11: Idle(aidel)
     else: Toward(t, 6, 9)
     return
6. Walk(t, 7)
```

- R55a. [I] `A4Q1_IzualSeen(G)`: `QUESTS_FindById(G, 22)`; a record with `+0x09` non-zero and `+0x0B < 2` (unsigned) gets `+0x14 = 0` and `QUESTS_SetState(rec, 0, A4Q1_StepBits, 1)`. After a cast `v1C` = 3–4 melee events or walks follow with no draw. (fn:QUESTS_FindById@0x00543640, fn:QUESTS_SetState@0x00544300, fn:sub_005B3940_A4Q1_StepBits@0x005B3940, fn:sub_005DE6D0_MonAiWalkTowardUnit@0x005DE6D0, tbl:MonStats.txt:aidel)
- R55b. [C] The map with `v14` ≠ 0, and the quest call at `v14` = 0 with `v14` already 1 at it: family `izual`, 240 cases, 78 with a draw, 8 outcomes; the controls fail the 10, 40 and 51 that separate them. `Range(100) < aip(4)` is met at equality in no case, so its strictness is not tested. (run:2026-10-30-ai-cat-emu-6)

- R55i. [C] As data: kind 1, no `init`, no `alt`; 1 records (256 izual); reach ·; `aip` set 1,2,3,4,5,6; `aidel` 15/12/8; skills Frost Nova. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R55l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R59. Row 59 `BloodRaven` (fn:sub_005E6320_AiBloodRaven@0x005E6320)

No `aip` set. `Skill1` `Nest`, `Skill2` `Quick Strike`, as data.

```
init (0x005E6300):  v1C ← 0                                                [C] (run:2026-10-30-ai-cat-emu-6, fn:sub_005E6300_AiBloodRavenInit@0x005E6300)

1. h ← AiParamsFind(U, 10, 0)                                              [I] (0x005E6320, 0x005E6356, 0x005E67F4)
   if h = 0:
     Push({kind 10, U's own x, y});  h ← AiParamsFind(U, 10, 0)            ; the home point
2. hd ← 0
   if h ≠ 0:
     hd ← DistToPointSized(t, home)                                        ; the target's, ECX = t (0x005E63F8)
     if dist > 45: Idle(5); return
     if hd > 49 or DistToPointSized(U, home) > 50:                         ; second compare unsigned (jbe, 0x005E6433)
       v1C ← 1;  Ovr(7, 100, 0)
       if RunToPoint(h.x, h.y): return
       UNIT_CancelEvents(G, U, 2, 0)
     if v1C ≠ 0 and DistToPointSized(U, home) > 5:                         ; jbe, 0x005E648E
       Ovr(7, 100, 0)
       if RunToPoint(h.x, h.y): return
       UNIT_CancelEvents(G, U, 2, 0)
     v1C ← 0
3. if dist > 20 and hd < 50:
     dist ← max(12, dist >> 1);  Ovr(7, 100, 0)                            ; the local copy of dist
     if RunNearUnit(t, dist): return
     UNIT_CancelEvents(G, U, 2, 0)
4. v14 ← v14 + 3
5. if Skill1 ≥ 0 and not melee and v18 < 2·d + 8 and Range(100) < v14:     ; draw#1
     a ← Range(15) + 5                                                     ; draw#2
     if Pow2(2) = 0: dx ← RangeB(a);  dy ← a                               ; draw#3, #4
     else: dx ← a;  dy ← RangeB(a)
     if Pow2(2) ≠ 0: dx ← −dx                                              ; draw#5
     if Pow2(2) ≠ 0: dy ← −dy                                              ; draw#6
     MonAiUseSkill(Sk1mode, Skill1, 0, subX(t) + dx, subY(t) + dy)     ; around the target (0x005E65E5)
     v18 ← v18 + 1;  v14 ← 0; return
6. if dist > 5:
     if D100() < 5 and hd < 50: Ovr(7, 100, 0);  RunNearUnit(t, 12); return
     h2 ← FindHostile(&e, &hd)
     if h2 ≠ 0 and not St3or19 and Range(100) < 80:
       if Skill2 ≥ 0 and Range(100) < (d + 4)·10: UseSkill2(h2); return
       SetModeAtUnit(4, h2); return
     Ovr(0, 50, 0)
     if T56(t, 4, 1): return
7. if D100() < 30 and dist < 12:
     Ovr(7, 100, 0)
     if StepAwayXY(t, 12 − dist, 0): return
     UNIT_CancelEvents(G, U, 2, 0)
8. SetModeAtUnit(4, t)
```

- R59a. [I] The home point is parameter record kind 10, pushed with the unit's own static or dynamic path point when missing; its leash compares are signed except the two named. `hd` is **the target's** distance from home, so a target past 49 starts the run home and blocks the run near it; the two later compares are the raven's own. The raise's point is around the target too. The raise skill is cast at most `2d + 8` times (`lea ecx,[ecx+ecx*1+0x8]`, 0x005E653E: 8/10/12 by difficulty), with a chance `v14` that grows by 3 per event and resets on a cast. The `dist` of the later tests is the local copy, halved (at least 12) after a failed run near the target. The `hd` slot is reused: `FindHostile`'s melee pointer writes it (0x005E66A0–0x005E66AC). (fn:sub_0058EEF0_AiParamsFind@0x0058EEF0, fn:sub_0058EF40_AiParamsPush@0x0058EF40, fn:sub_005DC480_AiDistToPointSized@0x005DC480, fn:sub_005DF680_MonAiRunNearUnit@0x005DF680, fn:RNG_RangeB@0x0045C3E0, fn:sub_005DF140_MonAiStepAwayXY@0x005DF140)
- R59b. [C] The init's map and the think's entry call `AiParamsFind` (0x005E6356) only: families `brinit`, `braven`, 240 cases each; no control separates them. (run:2026-10-30-ai-cat-emu-6)

- R59i. [C] As data: kind 1, `init` 0x005E6300, no `alt`; 1 records (267 bloodraven); reach ·; `aip` set —; `aidel` 15/13/10; skills Nest, Quick Strike. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R59l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R90. Row 90 `Griswold` (fn:sub_005E5AC0_AiGriswold@0x005E5AC0)

No `aip` set: the bounds are constants.

```
1. if melee:                                                               [C] (run:2026-10-30-ai-cat-emu-6, fn:sub_005E5AC0_AiGriswold@0x005E5AC0)
     if D100() < 80: SetModeAtUnit(4, t); return   ; draw#1
   else if D100() < 50: Walk(t, 7); return         ; draw#1
2. Idle(10)
```

- R90a. [C] Family `griswold`, 240 cases, all with a draw, 3 outcomes (0x005E5B12, 0x005E5B4B, 0x005E5B5B); the `≤` control fails the 11 it separates, and each draw is met at equality. (run:2026-10-30-ai-cat-emu-6)

- R90i. [C] As data: kind 1, no `init`, no `alt`; 1 records (365 griswold); reach U; `aip` set —; `aidel` 15/13/10; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R90l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R144. Row 144 `UberIzual` (fn:sub_005F8C80_AiUberIzual@0x005F8C80)

**`aip`:** as row 55, with the same stock values.

```
1. if Skill2 valid and (st ← Skills[Skill2].aurastate) ≥ 0 and not UNIT_HasState(U, st):   [I] (fn:sub_005F8C80_AiUberIzual@0x005F8C80, tbl:Skills.txt:aurastate)
     MonAiUseSkill(Sk2mode, Skill2, 0, 0, 0); return     ; Chilling Armor
2. if UnitLineBlocked(U, t, 6): MonAiUseSkill(Sk3mode, Skill3, 0, x, y); return  ; MonTeleport
3. if v18 ≠ 0: Idle(v18);  v18 ← 0; return
4. if melee:
     if v1C < 1 and not (Range(100) < aip(1)):
       v1C ← 0
       if Skill1 < 0 or not (Range(100) < aip(4)): Idle(aidel); return
     cast:
       MonAiUseSkill(Sk1mode, Skill1, t, x, y);  v18 ← aip(5);  v1C ← aip(6); return
     if v1C > 0: v1C ← v1C − 1
     SetModeAtUnit(4, t); return
5. if Skill1 ≥ 0 and dist < 10:
     if v1C > 0: Walk(t, 7); return
     if Range(100) < aip(3): goto cast
6. if v1C < 1 and not (Range(100) < aip(2)):
     if dist < 11: Idle(aidel)
     else: Toward(t, 6, 9)
     return
7. Walk(t, 7)
```

- R144a. [I] Row 55 with steps 1 and 2 added, the quest call gone, and all four rolls through `Range`, where Izual draws two inline. Its `v14` is unused here. (0x005F8D5B, 0x005F8D90)
- R144b. [C] Up to its `UNIT_HasState` (0x005F8D5B) or `UnitLineBlocked` (0x005F8D90) call only: family `uizual`, 240 cases, no draw; the compare control fails the 30 it separates. (run:2026-10-30-ai-cat-emu-6)

- R144i. [C] As data: kind 1, no `init`, no `alt`; 1 records (706 uberizual); reach ·; `aip` set 1,2,3,4,5,6; `aidel` 15/12/8; skills Frost Nova, Chilling Armor, MonTeleport. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R144l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R146. Row 146 `UberMephisto` (fn:sub_005F81C0_AiUberMephisto@0x005F81C0)

Stub: the think is `ret 4` (0x005F81C0). A kind-1 event with a target commands nothing from the think; without a target `MonAiTargetOrIdle` idles. What moves and casts Uber Mephisto is under Open questions; with a target the boss sight pause fires once, then this event queues no next one ([monsters/special](../special.md)). [C] The return, `v14`, `v18`, `v1C` unchanged: family `umeph`, 240 cases. (run:2026-10-30-ai-cat-emu-6, fn:sub_005F81C0_AiUberMephisto@0x005F81C0)

- R146a. [I] Two functions beside it have no `call`, `jmp`, `push`, `mov` immediate or data-word reference in the image. 0x005F7F10: one step of the unit's seed, `k = low & 7`, a class from `{725, 725, 726, 726, 727, 728, 729, 730}[k]` spawned by `SpawnNearUnitNoBox(class, 8, 4, 0)` with `Unit+0xC4 |= 0x4000000` and state 184; its stack argument is the unit to spawn near, or 0 for the caller. 0x005F8010: over the eight player slots at `G+0x10F8`, a living player on the unit's level within 1020 of the unit's point (unsigned), one step per such player, the last kept when `w[class] + (low mod 20) > −1` (`w` = {35, 40, 30, 20, `EBX`, 25, 10}, slot 4 the register's value at 0x005F810C); a non-player unit there takes the fatal path. No driver is found: ai/0016. (0x005F7F10, 0x005F8010, fn:sub_005B23C0_SpawnNearUnitNoBox@0x005B23C0, [ai/0016](../../../findings/ai/0016-uber-event.md))

- R146i. [C] As data: kind 1, no `init`, no `alt`; 1 records (704 ubermephisto); reach ·; `aip` set 1,2,3; `aidel` 15/10/6; skills PrimeLightning, PrimeBolt, PrimePoisonNova, MephistoMissile, MephFrostNova, Blizzard. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R146l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 8: pool-E (towers, turrets, javelins and blowguns, Venom Lords, the siege)

#### R82. Row 82 `InvisoSpawner` (fn:sub_005E0160_AiInvisoSpawner@0x005E0160)

**`aip`:** 1 the stock (4, as data); 2 the distance (5, as data); 3 the frames between spawns (125, as data).

```
1. if v14 = 0: v18 ← aip(1)                  ; the stock, while no spawn has happened   [I] (0x005E0160, 0x005E025D)
2. if dist ≤ aip(2):
     if v18 ≤ 0: MonAiSetMode(0, 0, 0); return   ; stock spent: death
     if v14 ≤ T:
       c ← LevelClassVariant(UnitGetRoom(U), count > 96 ? 96 : −1)
       if SpawnPosPick(G, room, 0, c, &x, &y, 0) and SpawnAtPos(G, room, x, y, c, 1, 2, 0x42):
         v18 ← v18 − 1;  v14 ← T + aip(3)
3. Idle(15)
```

- R82a. [I] No draw. `v18` is reloaded whenever `v14` is 0, so only until the first spawn sets the timer. The class guard is `setg; sub 1; and; add` (0x005E01DC–0x005E01EC). (fn:sub_0063EC70_LevelClassVariant@0x0063EC70, fn:sub_0054DC40_SpawnPosPick@0x0054DC40, fn:sub_005B2F20_SpawnAtPos@0x005B2F20)
- R82b. [C] The map up to `SetMode(0, 0, 0)` (0x005E01B2), `LevelClassVariant` (0x005E01F1) or `Idle(15)` (0x005E0252), with `v18`'s reload before them: family `spawner`, 240 cases, 3 boundaries; the Normal-column and compare controls fail the 103 and 80 that separate them. (run:2026-11-03-ai-cat-emu-8)

- R82i. [C] As data: kind 1, no `init`, no `alt`; 1 records (332 invisospawner); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R82l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R83. Row 83 `MosquitoNest` (fn:sub_005E0260_AiMosquitoNest@0x005E0260)

**`aip`:** 1 the use count (16/17/21 up to 16/20/24, as data); 2 the distance; 3 the frames between uses (200/180/175, as data).

```
1. if dist ≤ aip(2):                                                       [I] (0x005E0260, 0x005E037F)
     if v18 > aip(1):
       U+0xC4 ← U+0xC4 | 0x20000;  MonAiSetMode(0, 0, 0); return
     if Skill1 ≥ 0 and T > v14 and SpawnClassCellTest(count > 334 ? 334 : −1, UnitGetRoom(U), U.x, U.y, 0):
       v18 ← v18 + 1;  v14 ← T + aip(3)
       UseSkill1(t); return                  ; Nest
2. Idle(25)
```

- R83a. [I] No draw. Class 334 is `suckernest1`'s own row. The row is kind 0, so the think runs with whatever target and distance the event's context holds: Open questions. (fn:sub_005E0260_AiMosquitoNest@0x005E0260, fn:sub_005FD350_SpawnClassCellTest@0x005FD350, fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0)
- R83b. [C] The map up to `SetMode(0, 0, 0)` (0x005E02B5) with `+0xC4`'s bit, `SpawnClassCellTest` (0x005E0322; `ECX` the class, `EDX` the room, stack `U.x, U.y, 0`) or `Idle(25)` (0x005E0374): family `nest`, 240 cases, 3 boundaries; the Normal-column, compare and unsigned-`Skill` controls fail the 59, 51 and 27 that separate them. (run:2026-11-03-ai-cat-emu-8)

- R83i. [C] As data: kind 0, no `init`, no `alt`; 4 records (334-337 suckernest1..suckernest4); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills Nest. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R83l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R85. Row 85 `HighPriest` (fn:sub_005E0490_AiHighPriest@0x005E0490)

**`aip`:** 1 first pass, melee: chance of A1; 2 chance of the heal search; 3 the shared cooldown after a heal; 4 chance of `Skill1`; 5 chance of S1; 6 second pass: chance to break off; 7 second pass: chance of S1; 8 the distance of `Skill1` and of the first pass's choice of walk. Values per council member, as data.

```
1. if v14 = 0:                                                             [I] (0x005E0490, 0x005E096E)
     if melee:
       if chance(1): v14 ← 1;  SetModeAtUnit(4, t); return     ; draw#1
       StepAway(t, 6, 1); return
     if Skill2 ≥ 0 and T > v18 and rchance(2):                 ; draw#1
       blk ← {0, 75, 2500};  AiUnitSearch(G, U, &blk, AiPriestHealCb, 1)
       if blk.unit ≠ 0:
         v18 ← T + aip(3);  UseSkill2(blk.unit); return        ; ZakarumHeal
     if Skill1 ≥ 0 and T > v18 and dist < aip(8) and rchance(4):  ; draw#1..#2
       k ← Pow2(4)                                             ; draw#2..#3, low & 3
       MonAiUseSkill(Sk1mode, Skill1, t, t.x + CORNER[k].x, t.y + CORNER[k].y)   ; Hydra
       v18 ← T + 100; return
     if aip(5) > 0 and MissS1 > 0 and (m ← MissileRec(MissS1)) ≠ 0 and dist < m.Range − 2 and rchance(5):
       SetModeAtUnit(8, t); return                             ; S1, highpriestlightning
     if D100() < 80:
       if dist ≤ aip(8): T56(t, 3, 0)
       else: WalkStop(t, 6)
       return
2. v14 ← 1
3. if melee:
     if chance(7): SetModeAtUnit(8, t); return
     if chance(6): StepAway(t, 6, 1);  v14 ← 0; return
     if Range(100) < 90: SetModeAtUnit(4, t); return
     Idle(10); return
4. if dist < 6 and chance(7): SetModeAtUnit(8, t); return
5. if chance(6): v14 ← 0;  Idle(10); return
6. if D100() < 70: Walk(t, 7); return
7. Ring(12)
```

- R85a. [I] `CORNER` is the table 0x006E337C of 8-byte rows: `(−5, −5)`, `(5, −5)`, `(5, 5)`, `(−5, 5)`. A draw of 80 or more falls into the second pass. At most seven draws in one decision. (fn:sub_0046ACE0_MissileRec@0x0046ACE0, fn:RNG_RangePow2@0x00472210, fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0, tbl:MonStats.txt:MissS1, tbl:Missiles.txt:Range)
- R85b. [I] **`AiPriestHealCb`** takes a monster, not in a death mode, `AlignSame02(U, cand)`, of alignment 0, within `UnitDistSq ≤ blk[2]` (2 500, 50 subtiles), with `UnitLifePct(cand) ≤ 75` and below `blk[1]` (75 at the start), keeping the lowest; it returns 0. No test excludes the priest itself. No draw. (fn:sub_005E0430_AiPriestHealCb@0x005E0430, fn:sub_0063EA40_MonIsDeathMode@0x0063EA40, fn:sub_00650D70_AlignSame02@0x00650D70, fn:sub_006259B0_UnitAlignGet@0x006259B0)
- R85c. [C] The map up to its fourteen boundary sites, with the block `{0, 0x4B, 0x9C4}` and the corner read from the image (all four met): family `priest`, 240 cases, 233 with a draw; the `≤`, Normal-column, compare and unsigned-`Skill` controls fail the 18, 83, 27 and 59 that separate them. The heal past the search and the S1 past `MissileRec` are not covered; the draws at the constants 80 and 70 and `rchance(2)` were met at equality in no case. (run:2026-11-03-ai-cat-emu-8, 0x005E051C, 0x005E0963)

- R85i. [C] As data: kind 1, no `init`, no `alt`; 4 records (345-347 councilmember1..councilmember3, 557 baalhighpriest); reach U; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/13,14/12,13; skills Hydra, ZakarumHeal. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R85l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R89. Row 89 `Megademon` (fn:sub_005E0C80_AiMegademon@0x005E0C80)

Tier AI: [machinery § T89](machinery.md#t89-row-89-megademon-fnsub_005e0c80_aimegademon0x005e0c80), not repeated here.

#### R93. Row 93 `ArcaneTower` (fn:sub_005E0F60_AiArcaneTower@0x005E0F60)

**`aip`:** 1 the `Skill1` uses per phase (1, as data); 2 the frames between them (150/125/75, as data); 3 the pause after (33/25/15, as data); 4 the A1 uses per phase (4, as data); 5 the pause after (150/125/75, as data); 6 the frames between A1s (50/33/25, as data).

```
1. if v18 = 0: v18 ← aip(1)                                                [I] (0x005E0F60, 0x005E106F)
2. if T < v1C: Idle(10); return
3. if Skill1 ≥ 0 and v14 = 0:
     UseSkill1(t)
     v18 ← v18 − 1
     if v18 < 1: v14 ← 1;  v18 ← aip(4);  v1C ← T + aip(3)
     else: v1C ← T + aip(2)
     return
4. SetModeAtUnit(4, t)
5. v18 ← v18 − 1
   if v18 < 1: v14 ← 0;  v18 ← aip(1);  v1C ← T + aip(5)
   else: v1C ← T + aip(6)
```

- R93a. [C] The map up to `Idle(10)` (0x005E0F94), `UseSkill` (0x005E0FC5) or `SetModeAtUnit(4, t)` (0x005E101E), with `v18`'s reload before them: family `arcane`, 240 cases, no draw, 3 boundaries; the controls fail the 42, 40 and 39 that separate them. The counter updates after the two commands are not covered. (run:2026-11-03-ai-cat-emu-8)

- R93i. [C] As data: kind 1, no `init`, no `alt`; 1 records (371 lightningspire); reach ·; `aip` set 1,2,3,4,5,6; `aidel` 15/15/15; skills ArcaneTower, Lightning. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R93l. [C] First boundary: 24 decisions compared (24), 0 mismatches, 3 first-call outcomes. (run:2026-11-03-ai, 0x005B186F)

#### R94. Row 94 `DesertTurret` (fn:sub_005E0980_AiDesertTurret@0x005E0980)

**`aip`:** 1 the frames between shots (10/7/3, as data); 2 the shots per burst (5–9, as data); 3 the rest (120/100/80, as data); 4 the range (30, as data); 5 the steps from itself (5, as data).

```
1. if Skill1 ≥ 0 and v14 = 0:                                              [I] (0x005E0980, 0x005E0C75)
     MonAiUseSkill(Sk1mode, Skill1, 0, 0, 0);  v1C ← 0;  v14 ← T; return   ; the turret's start
2. if T < v14: Idle(10); return
3. if dist > aip(4):
     if v18 > 0: v18 ← v18 − 1
     Idle(15); return
4. dir ← Dir64To8(UnitDirToPoint(U, t.x, t.y))
5. v1C ← SWEEP[(v1C mod 8) + 8·(dir & 7)]             ; signed mod, 0x005E0B0C–0x005E0B1E; i32 entries
6. x ← U.x + STEP[v1C].x·aip(5);  y ← U.y + STEP[v1C].y·aip(5)
7. UnitSetPathTargetUnit(U, t)
8. if Skill1 ≥ 0 and MonSkillTargetOk(G, U, Skill1, t, x, y) and MonSkillTargetOk(G, U, Skill1, t, t.x, t.y):
     MonAiUseSkill(Sk1mode, Skill1, 0, x, y);  PathSetTargetPoint(U.path, x, y)
     v18 ← v18 + 1
     if v18 > aip(2): v14 ← T + aip(3);  v18 ← 0
     else: v14 ← T + aip(1)
     return
9. if v18 > 0: v18 ← v18 − 1
10. Idle(10)
```

- R94a. [I] No draw. `SWEEP` is the table at 0x006E33E0, `STEP` the table at 0x006E33A0, 8 bytes a row: neither is in the finding, Open questions. The target's position comes from the inline getter shape: types 2, 4, 5 read the path's `+0x0C/+0x10`, others `PathGetX/Y`, 0 for no path (0x005E0A39–0x005E0AFB). (fn:sub_00621DC0_UnitDirToPoint@0x00621DC0, fn:sub_0063E7A0_Dir64To8@0x0063E7A0, fn:sub_005FD470_MonSkillTargetOk@0x005FD470, fn:sub_00648AD0_PathSetTargetPoint@0x00648AD0)
- R94b. [C] The map up to `UseSkill(…, 0, 0, 0)` (0x005E09CE), `Idle(10)` (0x005E09FE), `Idle(15)` (0x005E0A2B, with `v18`'s decrement) or `UnitDirToPoint` (0x005E0B07): family `turret`, 240 cases, no draw, 4 boundaries; the controls fail the 40, 58 and 71 that separate them. (run:2026-11-03-ai-cat-emu-8)

- R94i. [C] As data: kind 1, no `init`, no `alt`; 4 records (348-350 turret1..turret3, 372 firetower); reach ·; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills DesertTurret. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R94l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R95. Row 95 `PantherJavelin` (fn:sub_005E1080_AiPantherJavelin@0x005E1080)

**`aip`:** 1 chance to close in (70 in 1–6, 90 in 7–9, as data); 2 chance of A1; 3 the squared distance past which it rejoins (9–12, as data); 4 inside 8: chance to step away; 5 the idle; 6 the throw's range (20–28, as data).

```
1. d ← dist;  h ← FindHostile(&d, 0)             ; d is the frame word EBP+8  [I] (0x005E1080, 0x005E1240)
2. if d < 8 and chance(4): StepAway(t, 16, 1); return
3. if d > aip(6) − 6 and chance(1): WanderNear(t, 4); return
4. if h ≠ 0 and d < aip(6):
     if chance(2): SetModeAtUnit(4, h)
     else: Idle(aip(5))
     return
5. blk ← {0, 0x7FFFFFFF};  AiUnitSearch(G, U, &blk, AiSameBaseNearCb, 1)
6. if blk.unit ≠ 0 and blk.d2 > aip(3): Walk(blk.unit, 7); return
7. Idle(aip(5))
```

- R95a. [I] At most three draws. The callback is [row 18's](#r18-row-18-pantherwoman-fnsub_005f22b0_aipantherwoman0x005f22b0). (fn:sub_005DDC30_MonAiFindHostile@0x005DDC30, fn:sub_005B0D00_AiSameBaseNearCb@0x005B0D00)
- R95b. [C] The entry call `FindHostile(G, U, EBP+8, 0)` from 0x005E10A9 with `dist` in the frame word only, before any test: family `javelin`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-8)

- R95i. [C] As data: kind 1, no `init`, no `alt`; 9 records (373-376 slinger1..slinger4, 394-395 slinger5..slinger6, 610-612 slinger7..slinger9); reach P; `aip` set 1,2,3,4,5,6; `aidel` 15/13,14/12,13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R95l. [C] First boundary: 58 decisions compared (15 + 43), 0 mismatches, 1 first-call outcome. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R95r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 43 of its own think's decisions in the rev 4 and rev 6 logs, 43 resumed, 0 mismatches, 0 stopped, 48 later calls matched, an unknown value deciding 0 of 48 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### R96. Row 96 `FetishBlowgun` (fn:sub_005E1250_AiFetishBlowgun@0x005E1250)

**`aip`:** 1 the distance past which it closes in (20, as data); 2 chance of the retreat state (30, as data).

`v14`: 0 shooting, 1 walking in, 2 retreating. Row 96's records name `SkeletonRaise` as `Skill1`, which the think does not read.

```
clear ≝ v14 ← 0;  v18 ← 0                                                  [I] (0x005E1250, 0x005E152C)

1. p ← Head
   if p ≠ 0:
     if p.kind = 1 and (u ← GameFindUnit(G, p+0x10, p+0x0C)) ≠ 0:
       clear;  SetModeAtUnit(4, u);  Pop; return
     if p.kind = 14 and (u ← GameFindUnit(G, p+0x10, p+0x0C)) ≠ 0:
       clear;  Ovr(13, 50, 0);  Walk(u, 0);  Pop; return
     Pop
2. if not melee:
     if dist > aip(1): Ovr(0, 50, 0);  WanderNear(t, 6); return
     if dist ≥ 6: goto hunt
3. if chance(2): v14 ← 2                         ; draw#1
hunt:
4. h ← FindHostile(&d, 0)
5. switch v14:
     0: v18 ← v18 + 1
        if (step low mod 3) + 3 < v18: v14 ← 1;  v18 ← 0
        if h ≠ 0: SetModeAtUnit(4, h)
        else: T56(t, 4, 0)
     1: clear;  Ovr(0, 50, 0)
        if not T56(t, 6, 1): Idle(10)
     2: if dist < 13:
          Ovr(2, 50, 0)
          if not StepAway(t, 14, 1): SetModeAtUnit(4, h);  clear
          return
        if Range(100) < 20 and T56(t, 4, 1): return
        clear;  Idle(10)
     else: Idle(10)
```

- R96a. [I] The record's type is at `+0x10` and the guid at `+0x0C`, the word order row 65 writes; which poster's records reach a blowgun is not read. State 2's `SetModeAtUnit(4, h)` does not test `h`. At most two draws. (fn:sub_0058EE80_AiParamsHead@0x0058EE80, fn:sub_0058ED10_AiParamsPop@0x0058ED10, fn:sub_00552F60_GameFindUnit@0x00552F60)
- R96b. [C] The map up to `GameFindUnit` for kind 1 (0x005E129B) and kind 14 (0x005E12DC), `Pop` for any other kind (0x005E1322), `Ovr(0, 50, 0)` beyond `aip(1)` (0x005E1348) or `FindHostile` (0x005E13BD) with `v14` = 2 on the draw: family `blowgun`, 240 cases, 73 with a draw, 5 boundaries; the controls fail the 6, 33 and 11 that separate them. The switch after `FindHostile` is not covered. (run:2026-11-03-ai-cat-emu-8)

- R96i. [C] As data: kind 1, no `init`, no `alt`; 8 records (396-400 fetishblow1..fetishblow5, 659-661 fetishblow6..fetishblow8); reach P; `aip` set 1,2; `aidel` 15/14/13; skills SkeletonRaise. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R96l. [I] Logged, not compared: 179 decisions (61 + 61 + 57) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R96r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 118 of its own think's decisions in the rev 4 and rev 6 logs, 117 resumed, 0 mismatches, 1 stopped, 264 later calls matched, an unknown value deciding 0 of 265 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R97. Row 97 `Spirit` (fn:sub_005E3840_AiSpirit@0x005E3840)

No `aip`, no draw.

```
1. if v14 ≠ 0: Idle(50); return                                            [C] (0x005E3858, 0x005E3871, 0x005E387E, run:2026-11-03-ai-cat-emu-8)
2. if melee: v14 ← 1;  SetModeAtUnit(4, t); return
3. Idle(10)
```

- R97a. [I] One A1 at a target in melee, then `Idle(50)` on every later event: no code of the function clears `v14`. (fn:sub_005E3840_AiSpirit@0x005E3840)
- R97b. [C] Family `spirit`, 240 cases, 3 boundaries, no draw and no compare with a control. (run:2026-11-03-ai-cat-emu-8)

- R97i. [C] As data: kind 1, no `init`, no `alt`; 1 records (401 mephistospirit); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R97l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R98. Row 98 `Smith` (fn:sub_005E3890_AiSmith@0x005E3890)

No `aip`, no draw.

```
1. if melee: SetModeAtUnit(4, t); return                                   [I] (0x005E3890, 0x005E38F2)
2. L ← clamp(UnitLifePct(U), 0, 100)
3. Ovr(0, (100 − L) >> 1, 0);  Walk(t, 7)       ; sar 1 of a value in 0..100
```

- R98a. [C] The map up to `SetModeAtUnit(4, t)` (0x005E38A9) or `UnitLifePct(U)` (0x005E38B6) only: family `smith`, 240 cases, 2 boundaries. (run:2026-11-03-ai-cat-emu-8)

- R98i. [C] As data: kind 1, no `init`, no `alt`; 2 records (402 smith, 409 hephasto); reach U; `aip` set —; `aidel` 15/13/12; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R98l. [C] First boundary: 4 decisions compared (4), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, 0x005B186F)

#### R113. Row 113 `SiegeTower` (fn:sub_005E1860_AiSiegeTower@0x005E1860)

**`aip`:** 1 the idle.

```
1. o ← UnitGetOwner(G, U)                                                  [I] (0x005E1860, 0x005E18F0)
2. if (o = 0 or UnitIsDead(o)) and t ≠ 0:
     blk ← {400, 0}
     imp ← AiUnitSearch(G, U, &blk, AiImpNearCb, 1)
     if imp ≠ 0: AiImpSetHost(imp, U);  Idle(aip(1))
3. Idle(aip(1))
```

- R113a. [I] **The tower calls `Idle(aip(1))` twice** when the search finds one: the found branch has no return before the common idle (0x005E18D2, then 0x005E18E5). No draw. (fn:sub_00552FD0_UnitGetOwner@0x00552FD0, fn:sub_005541B0_UnitIsDead@0x005541B0)
- R113b. [I] **`AiImpNearCb`** takes a candidate that is not the searcher, a monster not in a death mode, whose `MonBaseId` is 492 (`imp1`, guarded `count > 492 ? 492 : −1`), `AlignSame02`, of alignment 0, while **the searcher** has no owner (0x005E1794–0x005E1799), whose `0x00541860(cand)+0x14` is −1, and returns it when `UnitDistSq(searcher, cand) ≤ blk[0]`, else 0. `0x00541860` is the AI-control getter (`unit+0x14 → +0x28`). No draw. (fn:sub_005E1720_AiImpNearCb@0x005E1720, fn:sub_00463860_MonBaseId@0x00463860, fn:sub_005B0BD0_UnitDistSq@0x005B0BD0)
- R113c. [I] **`AiImpSetHost(imp, host)`:** with `c` the imp's AI control, a host of 0 sets `c+0x14` = −1; else, when `GameFindUnit(UnitGetGame(imp), 1, c+0x14)` finds the old host and `UnitDistSq(imp, host) > UnitDistSq(imp, old)`, nothing changes, otherwise `c+0x14` = the host's guid. So the imp keeps the nearer host; [row 122](#r122-row-122-imp-fnsub_005e2ff0_aiimp0x005e2ff0) reads it. (fn:sub_005E17E0_AiImpSetHost@0x005E17E0, fn:sub_00554010_UnitGetGame@0x00554010)
- R113d. [C] The entry call `UnitGetOwner(G, U)` from 0x005E187B only, before any test: family `stower`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-8)

- R113i. [C] As data: kind 1, no `init`, no `alt`; 1 records (435 barricadetower); reach ·; `aip` set 1; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R113l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R114. Row 114 `ReanimatedHorde` (fn:sub_005E1540_AiReanimatedHorde@0x005E1540)

**`aip`:** 1 melee: chance of A1; 2 the melee idle (70 in `reanimatedhorde6`, else 20/15/12, as data); 3 the charge's range (10–18, as data); 4 chance of the charge; 5 chance to walk; 6 chance to walk toward; 7 the idle. `aip(8)` is not read.

```
1. U+0xC4 ← U+0xC4 | 0xE                                                   [I] (0x005E1540, 0x005E1719)
2. if melee:
     if chance(1): SetModeAtUnit(4, t)
     else: Idle(aip(2))
     return
3. if Skill2 ≥ 0 and AiApproachPointTest(U, t) and dist < aip(3) and dist > 5 and rchance(4):
     UseSkill2(t); return                       ; Charge
4. if chance(5): Walk(t, 0); return
5. if chance(6): Toward(t, 4, 0); return
6. Idle(aip(7))
```

- R114a. [I] Bits `0x2`, `0x4`, `0x8` of `+0xC4` are set on every event before any test. `Skill1`, `Self-resurrect`, is not read. At most three draws. (fn:sub_005DC640_AiApproachPointTest@0x005DC640, fn:sub_005DE6D0_MonAiWalkTowardUnit@0x005DE6D0, tbl:MonStats.txt:Skill1)
- R114b. [C] The map up to `SetModeAtUnit` (0x005E15BF), `Idle(aip(2))` (0x005E15D8), `AiApproachPointTest` (0x005E15F5), `Walk` (0x005E16A2), `Toward` (0x005E16F5) or `Idle(aip(7))` (0x005E170E), with `+0xC4 |= 0xE` before each: family `horde`, 240 cases, 168 with a draw, 6 boundaries; the `≤`, Normal-column and unsigned-`Skill` controls fail the 20, 90 and 52 that separate them. (run:2026-11-03-ai-cat-emu-8)

- R114i. [C] As data: kind 1, no `init`, no `alt`; 6 records (436-440 reanimatedhorde1..reanimatedhorde5, 698 reanimatedhorde6); reach PU; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills Self-resurrect, Charge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R114l. [C] First boundary: 43 decisions compared (12 + 31), 0 mismatches, 2 first-call outcomes. (run:2026-11-03-ai, run:2026-11-04-ai-r5, 0x005B186F)
- R114r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 31 of its own think's decisions in the rev 4 and rev 6 logs, 31 resumed, 0 mismatches, 0 stopped, 28 later calls matched, an unknown value deciding 0 of 28 later steps. The row is not under sentence H1. (run:2026-11-04-ai-r5)

#### R115. Row 115 `SiegeBeast` (fn:sub_005E1900_AiSiegeBeast@0x005E1900)

**`aip`:** 1 the squared search distance's root (625 squared, as data); 2 melee: chance of A1; 3 melee: chance of the stomp; 4 the melee idle; 5 inside the skill's `Param5`: chance of the stomp; 6 chance of the override; 7 the override, clamped (100, as data).

```
1. o ← UnitGetOwner(G, U)                                                  [I] (0x005E1900, 0x005E1B55)
2. if MonIsDeathMode(U): return                  ; no command
3. if o = 0 and UnitAlignGet(U) = 0:
     blk ← {aip(1)·aip(1)}
     imp ← AiUnitSearch(G, U, &blk, AiImpNearCb, 1)
     if imp ≠ 0: AiImpSetHost(imp, U)
4. if melee:
     if Skill1 ≥ 0 and chance(3): MonAiUseSkill(Sk1mode, Skill1, 0, 0, 0); return   ; the stomp, 0x005E19EC–0x005E19F6
     if chance(2): SetModeAtUnit(4, t)
     else: Idle(aip(4))
     return
5. if Skill1 ≥ 0 and dist < SkillGetParam5(Skill1) and rchance(5):
     MonAiUseSkill(Sk1mode, Skill1, 0, 0, 0); return
6. if AiApproachPointTest(U, t) and chance(6):
     Ovr(0, clamp(aip(7), 0, 127), 0);  Toward(t, 12, 0); return
7. Toward(t, 12, 0)
```

- R115a. [I] The callback and the host are [row 113's](#r113-row-113-siegetower-fnsub_005e1860_aisiegetower0x005e1860). (fn:sub_004E6C70_SkillGetParam5@0x004E6C70, tbl:Skills.txt:Param5)
- R115b. [C] The entry call `UnitGetOwner(G, U)` from 0x005E192B only, before any test: family `sbeast`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-8)

- R115i. [C] As data: kind 1, no `init`, no `alt`; 5 records (441-445 siegebeast1..siegebeast5); reach PU; `aip` set 1,2,3,4,5,6,7; `aidel` 15/14/13; skills Siege Beast Stomp, Charge. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R115l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 9: pool-F (act V minions)

#### R116. Row 116 `Minion` (fn:sub_005E1B60_AiMinion@0x005E1B60)

**`aip`:** 1 melee: chance to attack; 2 chance of A2, and the melee idle; 3 at range: chance to walk; 4 the idle at range. `aip(5)` is not read. Alike in all 11 records for those read, as data.

```
1. f ← 0                                                                   [I] (0x005E1B60, 0x005E1D28)
2. p ← Head
   if p ≠ 0:
     if p.kind = 1 and p+0x14 > T and (u ← GameFindUnit(G, p+0x0C, p+0x10)) ≠ 0 and not UnitIsDead(u):
       f ← 1
       if u ≠ t:
         t ← u;  UnitEdgeDistance(U, u);  melee ← InMeleeRange(U, u, 0)
     else: AiParamsPop(G, U)
3. if melee:
     if f = 0 and not chance(1): Idle(aip(2)); return    ; draw#1
     if chance(2): SetModeAtUnit(5, t)                   ; draw#1..#2
     else: SetModeAtUnit(4, t)
     return
4. if f = 0 and not chance(3): Idle(aip(4)); return      ; draw#1
5. Walk(t, 0)
```

- R116a. [I] A kind-1 record that has not expired (`+0x14` above the frame, signed) and whose unit is found alive makes that unit the target and skips the idle draws; a found record is not popped here. The lookup reads the type at `+0x0C` and the guid at `+0x10`, row 14's order (0x005E1BA5–0x005E1BA9). At most two draws. Who posts such records is Open questions. (fn:sub_0058EE80_AiParamsHead@0x0058EE80, fn:sub_00552F60_GameFindUnit@0x00552F60, fn:sub_005541B0_UnitIsDead@0x005541B0, fn:sub_006416D0_UnitEdgeDistance@0x006416D0, fn:sub_00622C40_InMeleeRange@0x00622C40, fn:sub_0058ED10_AiParamsPop@0x0058ED10)
- R116b. [C] The map up to `AiParamsPop` (0x005E1BEC), `UnitEdgeDistance` (0x005E1BD5), `Idle(aip(2))` (0x005E1C45), the two A commands (0x005E1C97, 0x005E1CAD), `Idle(aip(4))` (0x005E1D05) or `Walk(t, 0)` (0x005E1D1D), the lookups run on the image: family `minion`, 240 cases, 85 with a draw, 7 boundaries; the `≤`, Normal-column and compare controls fail the 12, 44 and 4 that separate them. (run:2026-11-03-ai-cat-emu-9)

- R116i. [C] As data: kind 1, no `init`, no `alt`; 11 records (453-460 minion1..minion8, 682-684 minion9..minion11); reach PU; `aip` set 1,2,3,4,5; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R116l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R117. Row 117 `SuicideMinion` (fn:sub_005E1D30_AiSuicideMinion@0x005E1D30)

**`aip`:** 2 the idle (5, as data); 3 chance to walk (50/60/70, as data); 5 the timer after the first melee event (0 in every stock record, as data). `aip(1)` and `aip(4)` are not read. Also the think of [state 15](#s15-state-row-15-fnsub_005e1d30_aisuicideminion0x005e1d30).

```
1. if v14 ≠ 0:                                                             [I] (0x005E1D30, 0x005E1DF7)
     if T > v14: SetModeAtUnit(0, t)
     else: Idle(aip(2))
     return
2. if melee: v14 ← T + aip(5);  Idle(aip(2)); return
3. if chance(3): Walk(t, 0)                     ; draw#1
   else: Idle(aip(2))
```

- R117a. [I] The minion dies by its own command, mode 0, whatever the distance then. What the death does is outside this function. At most one draw. (fn:sub_005E1D30_AiSuicideMinion@0x005E1D30)
- R117b. [C] The map up to `SetModeAtUnit(0, t)` (0x005E1D63), `Idle(aip(2))` (0x005E1D99, with `v14` written before it on the melee arm) or `Walk(t, 0)` (0x005E1DEC): family `suicide`, 240 cases, 44 with a draw, 3 boundaries; the controls fail the 6, 83 and 21 that separate them. (run:2026-11-03-ai-cat-emu-9)

- R117i. [C] As data: kind 1, no `init`, no `alt`; 8 records (461-468 suicideminion1..suicideminion8); reach P; `aip` set 1,2,3,4; `aidel` 15/14/13; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R117l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R118. Row 118 `Succubus` (fn:sub_005E1E00_AiSuccubus@0x005E1E00)

**`aip`:** 1 melee: chance of A1 (90–95, as data); 2 at range: chance to walk; 3 chance to curse; 4 the curse's range (15–25, as data); 5 the melee idle; 6 the idle at range; 7 the target's life percent at or above which `Skill1` goes; 8 the own life percent at or below which `Skill2` goes, and the bolt's chance (0 in Normal, as data, so never there).

```
1. if not StatListFindFlag(t, 0x20) and dist < aip(4) and chance(3):       ; draw#1     [I] (0x005E1E00, 0x005E2114)
     if Skill1 > 0 and UnitLifePct(t) ≥ aip(7): UseSkill1(t); return
     if Skill2 > 0 and UnitLifePct(U) ≤ aip(8): UseSkill2(t); return
     if Skill3 > 0 and (UnitGetMaxHp(t) > UNIT_GetMaxMana(t) or t = 0 or t.type ≠ 0): UseSkill3(t); return
     if Skill4 > 0 and t ≠ 0 and t.type = 0: UseSkill4(t); return
2. if melee:
     if chance(1): SetModeAtUnit(4, t)                                     ; draw
     else: Idle(aip(5))
     return
3. if Skill5 > 0 and aip(8) > 0 and (h ← FindHostile(&dist, 0)) ≠ 0 and Range(100) < aip(8):
     UseSkill5(h); return                                                  ; SuccubusBolt
4. if chance(2): Walk(t, 0)                                                ; draw
   else: Idle(aip(6))
```

- R118a. [I] The curses go to a target without the stat-list flag `0x20`; the skill tests are `> 0` (signed word, `cmp word, 0; jle`), so a skill id 0 is never used. With the stock slots, `Skill3` (Defense Curse) goes to a monster or to a player whose maximum life exceeds its maximum mana, `Skill4` (Blood Mana) to any other player. `t` is dereferenced by `StatListFindFlag` before the later null tests (0x005E1F4D, 0x005E1F91). At most three draws. (fn:sub_00625760_StatListFindFlag@0x00625760, fn:sub_00621F20_UnitLifePct@0x00621F20, fn:sub_00625D10_UnitGetMaxHp@0x00625D10, fn:UNIT_GetMaxMana@0x00625D60)
- R118b. [C] The map up to `UnitLifePct(t)` (0x005E1E9D), `UnitLifePct(U)` (0x005E1EE8), `UnitGetMaxHp(t)` (0x005E1F36), `UseSkill4` (0x005E1FB0), `SetModeAtUnit(4, t)` (0x005E200C), `Idle(aip(5))` (0x005E2025), `FindHostile` (0x005E2057), `Walk(t, 0)` (0x005E20F0) or `Idle(aip(6))` (0x005E2109): family `succubus`, 240 cases, 218 with a draw, 9 boundaries; the controls fail the 26, 125, 22 and 69 that separate them. (run:2026-11-03-ai-cat-emu-9)

- R118i. [C] As data: kind 1, no `init`, no `alt`; 8 records (469-473 succubus1..succubus5, 634-635 succubus6..succubus7, 719 succubus8); reach PU; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills Defense Curse, Blood Mana, SuccubusBolt. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R118l. [I] Logged, not compared: 108 decisions (52 + 46 + 10) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R118r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 56 of its own think's decisions in the rev 4 and rev 6 logs, 56 resumed, 0 mismatches, 0 stopped, 12 later calls matched, an unknown value deciding 0 of 12 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R119. Row 119 `SuccubusWitch` (fn:sub_005E2120_AiSuccubusWitch@0x005E2120)

**`aip`:** 1 melee: chance of A1; 2 chance to walk; 3 the curse chance and the step-away chance (0/0/0 in `succubuswitch1`, 0/25/35 in 2, 0/30/40 in 3, 0/30/50 in 4–9, as data: so `succubuswitch1` never does either by it, and no witch in Normal); 4 the curse's range, and its low byte the step's length; 5 chance of the bolt's first test, and of S2 without a bolt; 6 the idle; 7, 8 as row 118.

```
1. if t ≠ 0 and not StatListFindFlag(t, 0x20) and dist < aip(4) and chance(3):   ; draw#1   [I] (0x005E2120, 0x005E213C, 0x005E2607)
     if Skill1 > 0 and UnitLifePct(t) ≥ aip(7): UseSkill1(t); return
     if Skill2 > 0 and UnitLifePct(U) ≤ aip(8): UseSkill2(t); return
     if Skill3 > 0 and (UnitGetMaxHp(t) > UNIT_GetMaxMana(t) or t.type ≠ 0): UseSkill3(t); return    ; "Skill3 without the !t test"
     if Skill4 > 0 and t.type = 0: UseSkill4(t); return
2. if melee:
     if chance(3) and StepAway(t, aip(4) & 0xFF, 1): return                      ; draw
     if chance(1): SetModeAtUnit(4, t)                                           ; draw
     else: Idle(aip(6))
     return
3. if Skill5 ≥ 0 and aip(8) > 0 and chance(5) and (h ← FindHostile(&dist, 0)) ≠ 0 and Range(100) < aip(8):
     UseSkill5(h); return
4. if dist < aip(4) and chance(3) and StepAway(t, aip(4) & 0xFF, 1): return      ; dist: the slot FindHostile wrote
5. if Skill5 < 0 and (h ← FindHostile(&dist, 0)) ≠ 0 and chance(5): SetModeAtUnit(9, h); return
6. if chance(2): Walk(t, 0); return
7. if D100() < 50 and T56(t, 6, 1): return
8. Idle(aip(6))
```

- R119a. [I] The finding states step 1's four curses as "the four curses of row 118, Skill3 without the `!t` test" and groups no clause beyond that; step 1's Skill3 line keeps that wording. The step's length is `movzx eax, byte [edi+eax*2+0x68]` (0x005E2327, 0x005E24B7). The bolt's sign test is `≥ 0` (`jl`, 0x005E23BA) where the succubus has `> 0`. The distance compared after the first search (0x005E2477) is the frame word `FindHostile` was given. At most six draws. (fn:sub_005DEFE0_MonAiStepAway@0x005DEFE0, fn:sub_005DF7D0_MonAiWalkToUnitType56@0x005DF7D0, fn:sub_005E2120_AiSuccubusWitch@0x005E2120)
- R119b. [C] The map up to its thirteen boundary sites, null targets included (0x005E21C5, 0x005E2210, 0x005E225E, 0x005E22D4, 0x005E2338, 0x005E24C8, 0x005E238B, 0x005E23A4, 0x005E25FC, 0x005E241B, 0x005E24EA, 0x005E2599, 0x005E25E4): family `witch`, 240 cases, 223 with a draw; the controls fail the 40, 135, 20 and 64 that separate them. The bolt after the first search and the S2 after the second are not covered. (run:2026-11-03-ai-cat-emu-9)

- R119i. [C] As data: kind 1, no `init`, no `alt`; 9 records (9 records, as the index lists them); reach PU; `aip` set 1,2,3,4,5,6,7,8; `aidel` 15/14/13; skills Amplify Damage, Weaken, Defense Curse, Blood Mana, SuccubusBolt. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R119l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R120. Row 120 `Overseer` (fn:sub_005E27A0_AiOverseer@0x005E27A0)

**`aip`:** 1 `Skill1`'s cooldown (250, as data); 2 chance of `Skill2` (50–70, as data); 3 chance of `Skill3`; 4 the distance it keeps; 5 the band around it (`aip(4) ∓ aip(5)` 10 and 24, as data); 6 melee: chance to attack; 7 chance of A2 (Nightmare and Hell 30–55, as data). `aip(8)` is not read.

```
1. 0x00587900(G, U)                                ; the superunique-42 quest hook   [I] (0x005E27A0, 0x005E2B5E)
2. w ← AiStoredHostile(G, U)
3. if Skill1 ≥ 0 and St3or19 and T > v14 and w ≠ 0 and MonHasSkill(U, Skill1):
     UseSkill1(w);  v14 ← T + aip(1); return       ; Cry Help
4. if melee and chance(6):
     if chance(7): SetModeAtUnit(5, t)
     else: SetModeAtUnit(4, t)
     return
5. blk ← {576, 400, 50, 0, 0, 0};  AiUnitSearch(G, U, &blk, AiOverseerMinionCb, 1)
6. if Skill2 ≥ 0 and blk.weak ≠ 0 and chance(2) and MonHasSkill(U, Skill2): UseSkill2(blk.weak); return
7. if Skill3 ≠ 0 and blk.whip ≠ 0 and chance(3) and UnitAlignGet(U) ≠ 2 and MonHasSkill(U, Skill3):
     UseSkill3(blk.whip); return                   ; Overseer Whip
8. if blk.count ≠ 0:
     if dist < aip(4) − aip(5): StepAway(t, (u8)(aip(4) − dist), 0); return
     if dist > aip(4) + aip(5): Walk(t, 0); return
     if Range(100) < 50: T56(t, 5, 0)
     else: Idle(10)
     return
9. if D100() < 60: Walk(t, 0)
   else: Idle(10)
```

- R120a. [I] `AiStoredHostile`: `UnitStoredUnit9C` when `U+0xC8` has bit `0x20000`; a player not in mode 0 or 17, or a monster not in mode 0 or 12 that `UnitsHostile(G, U, w)` gives, else 0. `Skill3` is tested `≠ 0` (`je`, 0x005E29EB), not by sign. The step's byte is `sub dl, cl` (0x005E2AB1). At most four draws. (fn:sub_005DE830_AiStoredHostile@0x005DE830, fn:sub_00553010_UnitStoredUnit9C@0x00553010, fn:sub_005DD2D0_MonHasSkill@0x005DD2D0, fn:sub_006259B0_UnitAlignGet@0x006259B0)
- R120b. [I] **`AiOverseerMinionCb`:** a candidate that is not the searcher, a monster, of `MonBaseId` 453 (`minion1`), not in a death mode, not `UnitsHostile(G, searcher, cand)`, not in state 141 (`bloodlust`, the state Overseer Whip applies) is counted (`blk[5] += 1`); the first with `UnitDistSq ≤ blk[0]` and `UnitLifePct < blk[2]` becomes `blk[3]`, the first with `UnitDistSq ≤ blk[1]` and not unique (`MonTypeFlag(cand, 8)` 0) `blk[4]`; it returns 0. No draw. Row 128 pushes the same callback (0x005EE906). (fn:sub_005E26D0_AiOverseerMinionCb@0x005E26D0, fn:sub_00463860_MonBaseId@0x00463860, fn:sub_0063EA40_MonIsDeathMode@0x0063EA40, fn:sub_00554200_UnitsHostile@0x00554200, fn:UNIT_HasState@0x00639DF0, fn:sub_005A0180_MonTypeFlag@0x005A0180)
- R120c. [C] The map up to `UnitsHostile` (0x005DE85F, inside `AiStoredHostile`), `UseSkill1` (0x005E283C, a stored living player), the A commands (0x005E28EF, 0x005E2905) or the search (0x005E2943) with the block `{0x240, 0x190, 0x32, 0, 0, 0}`, on an image with no quest list, so the hook's other branches are not covered: family `overseer`, 240 cases, 132 with a draw, 5 boundaries; the controls fail the 13, 31 and 7 that separate them. Everything after the search is not covered. (run:2026-11-03-ai-cat-emu-9)

- R120i. [C] As data: kind 1, no `init`, no `alt`; 6 records (479-483 overseer1..overseer5, 724 overseer6); reach PU; `aip` set 1,2,3,4,5,6,7; `aidel` 15/14/13; skills Cry Help, Healing Vortex, Overseer Whip, Smite. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R120l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R121. Row 121 `MinionSpawner` (fn:sub_005E2BD0_AiMinionSpawner@0x005E2BD0)

**`aip`:** 1 the uses in all (100, as data); 2 the most minions counted, and the idle (25, as data); 3 the frames between uses (100, as data); 4 the range (20/22/25, as data). `aip(5)` is not read.

```
init 0x005F6630:  v14 ← T;  v18 ← 0                                        [I] (fn:sub_005F6630_AiNestInit@0x005F6630)

1. if v18 ≥ aip(1): return                       ; spent: no command        [I] (0x005E2BD0, 0x005E2BF8, 0x005E2CC7, 0x005E2CCD)
2. if dist > aip(4) or T < v14: Idle(aip(2)); return
3. n ← 0;  AiUnitSearch(G, U, &n, AiMinionCountCb, 1)
4. if Skill1 ≥ 0 and n < aip(2):
     v14 ← T + aip(3);  v18 ← v18 + 1;  UseSkill1(t); return    ; MinionSpawner
5. Idle(aip(2))
```

- R121a. [I] **`AiMinionCountCb`** counts (`*blk += 1`) a candidate that is not the searcher, a monster not in a death mode, of `MonBaseId` 453 or 461 (`minion1`, `suicideminion1`; `sub 0x1C5; je; sub 8; jne`), of alignment 0; it has no distance test and returns 0. No draw. (fn:sub_005E2B70_AiMinionCountCb@0x005E2B70, fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0)
- R121b. [C] The map up to the return (no call; `v14`, `v18` unchanged), `Idle(aip(2))` (0x005E2C13, 0x005E2C37) or the search (0x005E2C59) with the block `{0}`: family `spawner`, 240 cases, no draw, 4 boundaries; the Normal-column and compare controls fail the 120 and 107 that separate them. The use after the search is not covered. (run:2026-11-03-ai-cat-emu-9)

- R121i. [C] As data: kind 1, `init` 0x005F6630, no `alt`; 9 records (484-491 minionspawner1..minionspawner8, 710 demonspawner); reach ·; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills MinionSpawner. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R121l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R122. Row 122 `Imp` (fn:sub_005E2FF0_AiImp@0x005E2FF0)

**`aip`:** none of its own. Every slot is read from fixed records, whatever the imp's own: `R1..R4` are MonStats records 492..495 (`imp1..imp4`). `R1.aip(1)` the life percent of the hurt teleport (25); `R1.aip(2)` its radius (14); `R1.aip(3)` the chance of it (10); `R2.aip(1)` the host's distance (5, squared 25); `R3.aip(1)` the step's distance (10); `R3.aip(2)` the step's chance (40); `R3.aip(3)` the missile's near band (22); `R3.aip(4)` its chance (25/30/35); `R4.aip(3)` the far band (13); `R4.aip(4)` its chance (60/65/70), as data. `Skill1` and `Skill4` are the imp's own record's.

```
init 0x005E2FD0:  v14 ← −1                         ; no host                [C] (run:2026-11-03-ai-cat-emu-9, fn:sub_005E2FD0_AiImpInit@0x005E2FD0)

1. if v14 ≠ −1 and UnitAlignGet(U) = 0:                                     [I] (0x005E2FF0, 0x005E30A8, 0x005E3194, 0x005E34BC)
     h ← GameFindUnit(G, 1, v14)
     if h ≠ 0 and not UnitIsDead(h) and UnitGetOwner(G, h) = 0 and UnitAlignGet(h) = 0:
       if UnitDistSq(U, h) > R2.aip(1)·R2.aip(1): Walk(h, 0); return
       if Skill1 ≥ 0: UseSkill1(h); return          ; Imp Teleport onto the host
     else: v14 ← −1
2. if melee:
     if Skill1 ≥ 0 and LifePct(U) < R1.aip(1):
       AiUseSkillNearSelf(U, R1.aip(2), Skill1, (i8) Sk1mode); return
     if D100() < R3.aip(2) and StepAway(t, 5, 1): return
3. if Skill1 ≥ 0 and D100() < R1.aip(3):
     AiUseSkillNearSelf(U, R1.aip(2), Skill1, (i8) Sk1mode); return
4. if dist < R3.aip(1) and D100() < R3.aip(2): StepAway(t, 5, 0); return
5. if Skill4 ≥ 0 and (h ← FindHostile(&dist, 0)) ≠ 0:
     if dist < R3.aip(3):
       if Range(100) < R3.aip(4): UseSkill4(h); return
     else if dist < R4.aip(3) and Range(100) < R4.aip(4): UseSkill4(h); return
6. if D100() < 33: WalkStop(t, 4); return
7. if D100() < 20: Ring(8); return
8. Idle(10)
```

`AiUseSkillNearSelf(unit, r, skill, mode)`, [I] (0x005DF850, 0x005DF981, fn:sub_005DF850_AiUseSkillNearSelf@0x005DF850, fn:sub_00554010_UnitGetGame@0x00554010):

```
n: i32 ← 2·r                                         ; add edi, edi; cannot wrap for an i16 r
ox ← n > 0 ? one inline step: low & (n−1) when n is a power of two, else low mod n : 0     ; signed jg
oy ← the same, a second step
MonAiUseSkill(game of unit, unit, mode, skill, 0, X + ox − r, Y + oy − r)                  ; X, Y the unit's own position
```

- R122a. [I] A host found but with `Skill1 < 0` goes on with `v14` kept. Do 129's attach then sets [state 16](#s16-state-row-16-fnsub_005e2d80_aiimpattached0x005e2d80). The far band is smaller than the near one, so the second missile test can hold only when `R4.aip(3) > R3.aip(3)`, which no stock difficulty has. The helper's mode is the record byte sign-extended (`movsx edx, byte [eax+0x180]`, 0x005E31D2, 0x005E32A3) where `UseSkill` callers elsewhere zero-extend. At most six draws. (fn:sub_005DD280_AiLifePct@0x005DD280, fn:sub_00552FD0_UnitGetOwner@0x00552FD0, fn:sub_005DEF80_MonAiWalkToUnitStop@0x005DEF80, fn:sub_005DE200_MonAiWanderRing@0x005DE200)
- R122b. [C] The map up to `UnitAlignGet(U)` (0x005E30B6), `AiLifePct` (0x005E31BB), `StepAway(t, 5, 1)` (0x005E3246), the helper's `UseSkill` (0x005DF976, both jitter draws, `n` a power of two, another value and `≤ 0` all met), `StepAway(t, 5, 0)` (0x005E3328), `FindHostile` (0x005E3351), `WalkStop` (0x005E345C), `Ring(8)` (0x005E34A1) or `Idle(10)` (0x005E34B1), with the slots read from the records 492–495: families `impi` and `imp`, 240 cases each, `imp` 152 with a draw, 9 boundaries; the controls fail the 14, 69, 6 and 52 that separate them, and the "own record" control the 119 it separates. The host branch past `UnitAlignGet` and the missile past `FindHostile` are not covered. (run:2026-11-03-ai-cat-emu-9)

- R122i. [C] As data: kind 1, `init` 0x005E2FD0, no `alt`; 8 records (492-496 imp1..imp5, 688-689 imp6..imp7, 714 imp8); reach PU; `aip` set 1,2,3,4; `aidel` 15/14/13; skills Imp Teleport, ImpBolt, Imp Fireball, Imp Fire Missile, Imp Inferno, Imp Fire Missile Ex. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R122l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R123. Row 123 `Catapult` (fn:sub_005E34C0_AiCatapult@0x005E34C0)

**`aip`:** 1 chance of A1 (20/22/25, as data).

```
if chance(1): SetModeAtUnit(4, 0)               ; draw#1, a null target (push ebx, ebx = 0, 0x005E350D)   [I] (0x005E34C0, 0x005E3527)
else: Idle(15)
```

- R123a. [I] It reads neither its target nor its distance. (fn:sub_005E34C0_AiCatapult@0x005E34C0)
- R123b. [C] The map up to `SetModeAtUnit(4, 0)` (0x005E3510) or `Idle(15)` (0x005E351E): family `catapult`, 240 cases, all with a draw; the controls fail the 22 and 54 that separate them. (run:2026-11-03-ai-cat-emu-9)

- R123i. [C] As data: kind 1, no `init`, no `alt`; 4 records (497-500 catapult1..catapult4); reach ·; `aip` set 1; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R123l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R124. Row 124 `FrozenHorror` (fn:sub_005E3530_AiFrozenHorror@0x005E3530)

**`aip`:** 1 melee: chance of A1; 2 at range: chance to walk; 3 chance of the blast; 4 the idle.

```
1. lv ← 0                                                                   [I] (0x005E3530, 0x005E36ED)
   if Skill1 ≥ 0:
     s ← SKILLS_GetUnitSkill(U, Skill1)
     if s ≠ 0: lv ← SKILLS_GetSkillLevel(U, s, 1)
2. if Skill1 ≥ 0 and dist < max(lv, 0) and chance(3) and not HasState(U, 12):
     UseSkill1(t); return                       ; Horror Arctic Blast
3. if HasState(U, 12): State(12, 0)
4. if melee:
     if chance(1): SetModeAtUnit(4, t)
     else: Idle(aip(4))
     return
5. if chance(2): WalkZ(t)
   else: Idle(aip(4))
```

- R124a. [I] The skill's level as a distance, `Sk1lvl` 4–6, as row 89's test with `SKILLS_GetUnitSkill` in place of `SkillFindByOwner`, a default of 0 instead of 1 and the level clamped at 0 (`setl; sub 1; and`, 0x005E3593–0x005E359D). At most two draws. (fn:SKILLS_GetUnitSkill@0x006439F0, fn:SKILLS_GetSkillLevel@0x006442A0, fn:STATE_Set@0x00639DB0, fn:sub_005DECA0_MonAiWalkToUnitOrZero@0x005DECA0)
- R124b. [C] The skill-sign test up to `SKILLS_GetUnitSkill` (0x005E356D) or, for `Skill1 < 0`, `HasState(U, 12)` (0x005E361A), and nothing after: family `horror`, 240 cases; the unsigned-`Skill` control fails the 96 it separates. (run:2026-11-03-ai-cat-emu-9)

- R124i. [C] As data: kind 1, no `init`, no `alt`; 5 records (501-505 frozenhorror1..frozenhorror5); reach PU; `aip` set 1,2,3,4; `aidel` 15/14/13; skills Horror Arctic Blast. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R124l. [C] First boundary: 143 decisions compared (95 + 40 + 8), 0 mismatches, 1 first-call outcome. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R124r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 48 of its own think's decisions in the rev 4 and rev 6 logs, 48 resumed, 0 mismatches, 0 stopped, 144 later calls matched, an unknown value deciding 0 of 144 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R125. Row 125 `BloodLord` (fn:sub_005E36F0_AiBloodLord@0x005E36F0)

Tier AI: [machinery § T125](machinery.md#t125-row-125-bloodlord-fnsub_005e36f0_aibloodlord0x005e36f0), not repeated here.

#### S15. State row 15 (fn:sub_005E1D30_AiSuicideMinion@0x005E1D30)

Alias of [row 117](#r117-row-117-suicideminion-fnsub_005e1d30_aisuicideminion0x005e1d30): the same think word. [I] (data:g_MonAiStateRows@0x0073D358, fn:sub_005E1D30_AiSuicideMinion@0x005E1D30)

- S15a. [I] **Who sets it.** Do 131 (Overseer Whip) on a live monster target of base 453 draws `RNG_Range(caster, 100)`; at or above calc1 and with the target not in state 141 it calls `WhipChangeClass`, which changes the target's class along its chain to the skill's `summon` (461, `suicideminion1`), calls `MonAiInit(G, target, ctl, 15)` (0x005D1EB9–0x005D1EC0) and sets state 142; below calc1 it applies state 141. So a whipped minion turned suicide minion runs row 117's think. (fn:sub_005D1F70_SkillDo131OverseerWhip@0x005D1F70, fn:sub_005D1E10_WhipChangeClass@0x005D1E10)

- S15i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S16. State row 16 (fn:sub_005E2D80_AiImpAttached@0x005E2D80)

**`aip`:** of fixed records, not its own: `R1.aip(2)` the teleport radius (14), `R2.aip(2)` the near distance (25), `R2.aip(3)` the cast's chance (45/55/65), `R2.aip(4)` the discarded draws' range, as data. `R1` and `R2` as [row 122](#r122-row-122-imp-fnsub_005e2ff0_aiimp0x005e2ff0).

```
init (0x005E2CD0):                                                          [C] (run:2026-11-03-ai-cat-emu-9, fn:sub_005E2CD0_AiImpAttachedInit@0x005E2CD0)
  k ← low bit of one inline step
  for i in 0 ..< 2:
    k ← (k + 1) mod 2
    slot ← SLOTS[k].slot                         ; 0x006E34E0: {2, 0}, {4, 0}
    if SkillFindByOwner(U, M.Skill[slot + 1], −1):
      v18 ← slot;  v1C ← SLOTS[k].word; return
  v18 ← 0;  v1C ← 0

think:                                                                      [I] (0x005E2D80, 0x005E2FCA)
1. o ← UnitGetOwner(G, U)
2. if not HasState(U, 143) or o = 0:
     MonAiInit(G, U, ctl, 0);  Idle(1); return
3. if dist > 24 or UnitIsDead(o) or UnitAlignGet(o) ≠ 0 or v18 = 0:
     AiUseSkillNearSelf(U, R1.aip(2), R1.Skill1, (i8) R1.Sk1mode)     ; teleport off
     v14 ← −1; return
4. if dist < R2.aip(2) and Range(100) < R2.aip(3):
     UnitGetSubX(t);  UnitGetSubY(t)             ; results unused
     if v1C ≠ 0: Range(2·R2.aip(4));  Range(2·R2.aip(4))        ; results unused
     s ← R1.Skill[v18 + 1]
     if s ≥ 0: MonAiUseSkill(R1.Sk[v18 + 1]mode, s, t, 0, 0)
     else: Idle(20)
     return
5. if Range(100) < 50: SetModeAtUnit(8, t)
   else: Idle(20)
```

- S16a. [I] **Who sets it.** `ImpAttach` (do 129's attach): an imp of base 492 and a host of base 435 or 441 get state 143, each the other's owner (`0x00621CE0` twice), two link calls, the imp's `+0xC4 &= ~0xE`, then `MonAiInit(G, imp, ctl, 16)` (0x005D199D–0x005D19B9). (fn:sub_005D18E0_ImpAttach@0x005D18E0)
- S16b. [I] **The init** picks the first of the two slots, starting from the one the step's low bit selects, whose skill in the imp's **own** record the imp has: slot 2 (`Skill3`, Imp Fireball) or 4 (`Skill5`, Imp Inferno). The think casts `imp1`'s skill at the slot, not its own (`[ebx + v18·2 + 0x170]`, `ebx` the record 492, 0x005E2ECF). Teleporting off, do 129 detaches it; on a non-monster `U` the store goes through a null control (0x005E2F65–0x005E2F87). The init writes `v1C` = 0 on both rows, so the two draws of step 4 happen only if another writer sets it. At most three draws. (fn:sub_006439B0_SkillFindByOwner@0x006439B0, fn:sub_005D19D0_ImpDetach@0x005D19D0)
- S16c. [C] The init's map to its return: family `imp16i`, 240 cases, all with the step. The think's entry call `HasState(U, 143)` (0x005E2DB5) after `UnitGetOwner` only, nothing after it: family `imp16`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-9)

- S16i. [C] As data: kind 1, `init` 0x005E2CD0, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

### Batch 10: pool-G (act V rest, the Ancients, Baal's minions)

#### R126. Row 126 `CatapultSpotter` (fn:sub_005EE040_AiCatapultSpotter@0x005EE040)

**`aip`:** 1 chance to strike; 2 the frames between strikes, and the idle; 4 the strike's radius; 5 how many more strikes keep one skill index (10, as data).

```
1. if v1C = 0 or D100() < 3:                         ; the step only when v1C ≠ 0     [I] (0x005EE040, 0x005EE212)
     if SpotterCatapultDead(U): SetModeAtUnit(0, t); return
2. if v1C = 0: v1C ← 1
3. if aip(2) − T + v1C > 0: Idle(aip(2)); return     ; s32
4. if t = 0 or not chance(1): Idle(aip(2)); return   ; draw only with a target
5. if v18 > 0: k ← v14;  v18 ← v18 − 1
   else: k ← Range(5);  v14 ← k;  v18 ← aip(5)       ; draw
6. x ← Range(2·aip(4)) − aip(4) + t's x              ; draw, none when 2·aip(4) ≤ 0
   y ← Range(2·aip(4)) − aip(4) + t's y              ; draw, the same
7. if FreeNearStep(UnitGetRoom(U), &(x, y), 2, 0x805, 3) = 0: Idle(15); return
8. MonAiUseSkill(4, g_AiSpotterSkills[k], 0, x, y);  v1C ← T
```

- R126a. [I] A strike lands around the **target**, and one index holds for `aip(5) + 1` strikes. `2·aip(4)` is a 32-bit sum of the i16. `SpotterCatapultDead` (0x005EDF70) steps up to three times from the unit's room rectangle by its size times the negated offset pair 0x0063EE10 gives for the class-chain position (table 0x006EA9D0), and returns the first non-zero result of 0x005429B0(game, room; x, y, class − 19), which is 1 when the room at that point, or an inactive room record, holds a dead monster of that class: 497–500, `catapult1..4`, for classes 516–519. (0x005EDF7F, 0x005EE031, fn:sub_0064E7E0_FreeNearStep@0x0064E7E0, fn:sub_00619730_RoomRectGet@0x00619730)
- R126b. [C] The map up to its first observed callee, 3 boundaries: family `spotter`, 240 cases, 200 with a draw; controls `le`, `d0`, `cmp` and `self` (the strike point from the spotter's position) fail the 5, 123, 27 and 53 they separate. Equality met at `aip(2) − T + v1C > 0` 18 times, `v18 > 0` 17. (run:2026-11-03-ai-cat-emu-10)

- R126i. [C] As data: kind 1, no `init`, no `alt`; 4 records (516-519 catapultspotter1..catapultspotter4); reach ·; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Catapult Charged Ball, Catapult Spike Ball, CatapultBlizzard, CatapultPlague, CatapultMeteor. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R126l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R127. Row 127 `NpcBarb` (fn:sub_005EDC50_AiNpcBarb@0x005EDC50)

**`aip`:** 1 the delay after A1; 2 chance to run at a target; 3 the distance limit of that run.

```
init 0x005EDC40: ret 4                                                    [C] (run:2026-11-03-ai-cat-emu-10)

1. if U+0xD0 = 11: TargetListAdd(0, 8)                 ; the event goes on  [I] (0x005EDC50, 0x005EDF4A)
2. if t ≠ 0:
     if melee: SetModeAtUnit(4, t);  Delay(aip(1)); return
     if dist < aip(3) and chance(2): Ovr(0, 100, 0);  RunToUnit(t); return
3. a ← step();  b ← step()                              ; two inline steps, u32 low words
   if WalkPt(X + a mod 20 − 40, Y + b mod 20 − 10): return
4. a ← step();  b ← step();  c ← step()                 ; three more
   s ← 1 when a's low bit is set, else −1
   if WalkPt(X + b mod 20 − 10, Y + c mod 20 − 10 − 30·s): return
5. a ← step();  b ← step()                              ; two more
   if WalkPt(X + a mod 20 − 10, Y + b mod 20 − 10 + 30·s): return
6. Idle(15)
```

- R127a. [I] `U+0xD0` = 11 is no target list ([drlg/0009 § 4](../../../findings/drlg/0009-room-lifecycle.md)); the first walk point lies 21–40 subtiles towards −x. (fn:sub_005B1990_TargetListAdd@0x005B1990)
- R127b. [C] The init's return; the think up to the first walk: families `barbi` and `barb`, 240 cases each, `barb` 4 boundaries, 115 with a draw; controls `le`, `d0`, `cmp` fail the 4, 31, 15 they separate. Equality met at `dist < aip(3)` 15 times. The retries follow a boundary and stay `[I]`. (run:2026-11-03-ai-cat-emu-10)

- R127i. [C] As data: kind 2, `init` 0x005EDC40, no `alt`; 2 records (522-523 act5barb1..act5barb2); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R127l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R129. Row 129 `GenericSpawner` (fn:sub_005E61B0_AiGenericSpawner@0x005E61B0)

**`aip`:** 1 the frames between casts (80, as data); 3 how many casts (15, as data).

```
init 0x005E6190: AiNestInit (v14 ← T, v18 ← 0);  v3C ← −1                 [C] (run:2026-11-03-ai-cat-emu-10)

1. if t = 0: Idle(20); return                                             [I] (0x005E61B0, 0x005E62BC)
2. if v3C = −1 and not AiGenSpawnPickClass(&v3C):      ; the pick returns 1 on every path
     U+0xC4 ← U+0xC4 | 0x20000;  SetMode(0); return
3. if dist > 20: Idle(20); return
4. if v18 ≥ aip(3): U+0xC4 ← U+0xC4 | 0x20000;  SetMode(0, 0, 0); return
5. if |T − v14| < aip(1): Idle(20); return             ; negated, so 0x80000000 stays negative
6. v14 ← T
7. if SpawnClassCellTest(count > 528 ? 528 : −1, UnitGetRoom(U); X, Y, 0):
     v18 ← v18 + 1;  UseSeq(167, t, 0, 0); return      ; Nest
8. Idle(20)

AiGenSpawnPickClass (0x005E6020), the class's seed:                       [I] (0x005E6020, 0x005E6184)
  *out ← 453 (−1 when the MonStats count ≤ 453)
  r ← MonRegionGet(G+0xF0, 0x00573520(U));  n ← its byte +0x10
  if n > 0:
    i ← one draw of U's seed: low mod n                ; a power of two takes the mask
    if entry i's class (i16 at +0x14 + 0x34·i) is a record with +0x0E & [0x006CE27C] (0x20, genericSpawn): take it
    else: the first entry with that flag
    else: 496 (−1 when the count ≤ 496)
  return 1
```

- R129a. [I] The cell test is for the hut's own class 528 (`evilhut`), not the picked class; where the picked class goes (Nest's function) is not read here. (fn:sub_005E61B0_AiGenericSpawner@0x005E61B0, fn:sub_005F6630_AiNestInit@0x005F6630, fn:sub_005FD350_SpawnClassCellTest@0x005FD350, fn:sub_00547BB0_MonRegionGet@0x00547BB0, tbl:MonStats.txt:genericSpawn)
- R129b. [C] The init's return state; the think's map to its first callee, 4 boundaries: families `genspi`, `genspawn`, 240 cases each; controls `d0`, `cmp`, `abs` (without the absolute value) fail the 45, 54, 26 they separate. No case reaches the pick's draw. (run:2026-11-03-ai-cat-emu-10)

- R129i. [C] As data: kind 1, `init` 0x005E6190, no `alt`; 1 records (528 evilhut); reach ·; `aip` set 1,3; `aidel` 15/15/15; skills Nest. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R129l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R130. Row 130 `DeathMauler` (fn:sub_005EE260_AiDeathMauler@0x005EE260)

**`aip`:** 1 in melee range: chance of A1; 2 chance to walk; 3 Death Maul's range (15–21, as data); 4 its chance (50–90, as data).

```
1. if melee:                                                              [I] (0x005EE260, 0x005EE3A8)
     if chance(1): SetModeAtUnit(4, t)
     else: Idle(15)
     return
2. if Skill1 ≥ 0 and dist < aip(3) and chance(4): MonAiUseSkill(Sk1mode, Skill1, t, 0, 0); return
3. if chance(2): Walk(t, 0); return
4. Idle(15)
```

- R130a. [C] The whole map to its 4 boundaries: family `mauler`, 240 cases, all drawing; controls `le`, `d0`, `cmp`, `u16` fail the 33, 81, 34, 11 they separate. Equality met at `dist < aip(3)` 34 times, on draws `aip(4)` 16, `aip(2)` 10, `aip(1)` 8. (run:2026-11-03-ai-cat-emu-10, fn:sub_005EE260_AiDeathMauler@0x005EE260)

- R130i. [C] As data: kind 1, no `init`, no `alt`; 6 records (529-533 deathmauler1..deathmauler5, 604 deathmauler6); reach PU; `aip` set 1,2,3,4; `aidel` 15/15/15; skills DeathMaul. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R130l. [I] Logged, not compared: 119 decisions (85 + 34) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-04-ai-r5, 0x005B186F)
- R130r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 34 of its own think's decisions in the rev 4 and rev 6 logs, 33 resumed, 0 mismatches, 1 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-r5)

#### R131. Row 131 `Wussie` (fn:sub_005EE3C0_AiWussie@0x005EE3C0)

No `aip` slot read.

```
1. r ← 0x00588D60(&u)                 ; with A5Q2's data, U's cage (A5Q2_CageOfUnit) and that cage's byte +0xF8 set:   [I] (0x005EE3C0, 0x005EE5BC)
                                      ; the unit whose guid is at +0xEC + 4·cage
2. if r ≠ 0:
     if u = 0: Idle(25); return
     if the cage's counter +0x114 + 4·cage (0x00588830) = 0 and AiPathDistToPoint(U, u's position) ≥ 4:
       if D100() < 70: Walk(u, 7)
       else if Range(100) < 10: Ring(4)
       else: Idle(10)
       return
     0x00588880 adds 1 to the counter (past 4 it sets the cage's byte +0x108)
     U is taken out: path cleared (0x00648730), CancelEvents(2, 0), room entry, collision and room link removed, UnitFree; return
3. p ← AiNearestPlayer(0x005DDF20)    ; kind 2, callback 0x005DDE80; the searcher when none
   if p is not a player: Idle(25); return
4. if 0x00588E10 finds a dead prisondoor (class 434, mode 12) in the near rooms:
     A5Q2_CageFreed(U)
     if U+0xD0 = 11: TargetListAdd(0, 8)
     Idle(25); return
5. 0x00588DD0                         ; the quest step
   if Range(1000) < 100: a 6-byte packet 0x8A, 1, U's id to p's client
   Idle(25)
```

- R131a. [I] The block was checked against its anchored instructions (the finding's prose agrees). (fn:sub_005EE3C0_AiWussie@0x005EE3C0, fn:sub_005888D0_A5Q2_CageFreed@0x005888D0, fn:sub_00555600_UnitFree@0x00555600)
- R131b. [C] The entry call 0x00588D60 only: family `wussie`, 240 cases, 1 boundary; no control separates it. (run:2026-11-03-ai-cat-emu-10)

- R131i. [C] As data: kind 2, no `init`, no `alt`; 1 records (534 act5pow); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R131l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R132. Row 132 `AncientStatue` (fn:sub_005EEAA0_AiAncientStatue@0x005EEAA0)

No `aip` slot read.

```
if Quest35 is present with q+0x11 ≠ 0 (0x0058CFE0) and q+0x0C = 0 (0x0058CFB0) and U lacks state 146:     [I] (0x005EEAA0, 0x005EEAC0)
  RoomPinSet(UnitGetRoom(U), 0);  MonAiUseSkill(4, 302, 0, X, Y)
else: Idle(25)
```

- R132a. [C] The two quest tests and the `HasState` call (0x005EEAC0), 2 boundaries: family `statue`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-10, fn:sub_005EEAA0_AiAncientStatue@0x005EEAA0, fn:sub_0061AED0_RoomPinSet@0x0061AED0)

- R132i. [C] As data: kind 0, no `init`, no `alt`; 3 records (537-539 ancientstatue1..ancientstatue3); reach ·; `aip` set —; `aidel` 15/15/15; skills MinionSpawner. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R132l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R133. Row 133 `Ancient` (fn:sub_005EF1A0_AiAncient@0x005EF1A0)

**`aip`:** per class below; the class jump (`ancientbarb1`, 2, 3 are classes 540, 541, 542), any other class or no unit returning at once. Each Ancient begins with 0x0058CF90, `Quest35`'s `q+0x11` = 0, **no null test** of the quest record, and `Idle(25)` when it is 0.

```
pick: AiPickPlayerTarget(&score, &n, 0, AiSameLevelCb) (0x005E8F20)      [I] (0x005E8F20, 0x005EEB10)
  each of the eight player lists G+0x10F8 + 4i: each player cb admits is scored (AiPlayerThreatScore); the best kept
  the ninth list's units with the searcher's byte +0x18 are scored too
  if the tenth list's best lies within 5 of U and the best player is not in melee range:
    a type-2 path plan to that player;  on no point the tenth list's unit is taken
  AiSameLevelCb(a, b): RoomGetLevelId(a's room) = RoomGetLevelId(b's room); fatal on a null

ancientbarb1 (class 540), 0x005EEB70: 1 the whirl's edge limit; 2 its chance; 3 A1/A2's chance; 4 how far past the target:   [I] (0x005EEB70, 0x005EED0F)
1. if state 54: Idle(25); return
2. t ← t, or the pick when none;  none: Idle(25); return
3. m ← InMeleeRange(U, t);  e ← UnitEdgeDistance(U, t)
4. if Skill1 > 0 and MonHasSkill and e < aip(1) and Range(100) < aip(2):
     dx ← X(t) − X(U);  dy ← Y(t) − Y(U);  r ← UnitDistance(U, X(t), Y(t)), 1 when 0
     point ← (X(t) + aip(4)·dx ÷ r, Y(t) + aip(4)·dy ÷ r)
     MonCmdInit(U, (i8) Sk1mode);  UNIT_SetUsedSkill(Skill1);  PathSetStopDist(1);  MonSetMode to point, byte 100
     return
5. if not m: WalkZ(t);  Delay(10); return
6. if Range(100) < aip(3): SetModeAtUnit(Range(2) ≠ 0 ? 4 : 5, t); return    ; second draw
7. Idle(25)

ancientbarb2 (class 541), 0x005EEDA0: 1 the edge limit; 2 A1's chance; 3 the self skill's chance; 4 the step away's chance; 5 its length:   [I] (0x005EEDA0, 0x005EEF5E)
1. the pick (0x005EEB10);  none: Idle(25); return
2. m, e as above
3. if m and chance(4) and StepAway(t, (u8) aip(5), 1): Delay(25); return
4. if 0 < Skill1 < the Skills count and it has a record:           ; a ← aurastate, b ← auratargetstate
     if not (0 < a ≤ States count and U has a) and not (0 < b ≤ States count and t has b)
        and chance(3) and MonAiUseSkill(Sk1mode, Skill1, 0, 0, 0): return
5. if e < aip(1) and chance(2) and SetModeAtUnit(4, t): return
6. if e ≥ aip(1) and WalkStop(t, (u8)(e − aip(1))): return
7. Idle(10)

ancientbarb3 (class 542), 0x005EF010: 1 the edge limit; 2 the skill's chance; 3 A1/A2's chance:   [I] (0x005EF010, 0x005EF0D6)
1. the pick;  none: Idle(25); return
2. if Skill1 > 0 and e < aip(1) and Range(100) < aip(2) and MonHasSkill: UseSeq(Skill1, t, 0, 0); return
3. if not m: WalkZ(t);  Delay(10); return
4. if D100() < aip(3): SetModeAtUnit(Range(2) ≠ 0 ? 4 : 5, t); return
5. Idle(25)
```

- R133a. [I] The states of `ancientbarb2` are admitted up to the count itself (`jg`, 0x005EEED5, 0x005EEF01). The whirl ends `aip(4)` (8, as data) past the target along the line from the Ancient. The pick's path plan is [ai/0001](../../../findings/ai/0001-machinery.md) § 8's 0x005E912D, and the pick is not emulated. (fn:sub_005EF1A0_AiAncient@0x005EF1A0, fn:sub_005EEB70_AiAncientBarb1@0x005EEB70, fn:sub_005EEDA0_AiAncientBarb2@0x005EEDA0, fn:sub_005EF010_AiAncientBarb3@0x005EF010, fn:sub_005E8F20_AiPickPlayerTarget@0x005E8F20, fn:sub_005EEB10_AiSameLevelCb@0x005EEB10, fn:sub_005E8530_AiPlayerThreatScore@0x005E8530, tbl:Skills.txt:aurastate, tbl:Skills.txt:auratargetstate)
- R133b. [C] The class jump, classes 540 (62 cases), 541 (61), 542 (39) and 78 others, each jump up to `HasState(U, 54)` (0x005EEB93) or the pick's call (0x005EEDE4, 0x005EF055), 7 boundaries: family `ancient`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-10)

- R133i. [C] As data: kind 2, no `init`, no `alt`; 3 records (540-542 ancientbarb1..ancientbarb3); reach PU; `aip` set 1,2,3,4,5; `aidel` 15/13/11; skills Whirlwind, Shout, Leap Attack. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R133l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R134. Row 134 `BaalThrone` (fn:sub_005EF320_AiBaalThrone@0x005EF320)

**`aip`:** 1 the skill's chance.

```
init 0x005EF310: ret 4                                                    [C] (run:2026-11-03-ai-cat-emu-10)

1. if M = 0: Idle(10); return                                             [I] (0x005EF320, 0x005EF5DA)
2. if T < v1C: Idle(T − v1C); return               ; a negative count
3. w ← v14
4. AiUnitSearch(blk{0, 0x40, 0, 0x40} at EBP − 0x2C, 0, 3);  u ← blk+8    ; kind 3
5. if u ≠ 0:
     if Skill1 > 0, t ≠ 0, its record exists,
        (aurastate outside [0, States count) or U lacks it),
        (auratargetstate outside that range or t lacks it),
        and Range(100) < aip(1): MonAiUseSkill(Sk1mode, Skill1, t, 0, 0); return
     Idle(10); return
6. if v18 & 1 = 0:                                 ; the announce
     if w ≤ 4 (unsigned):
       r ← SuperUniqueGet(0x00586B30(g_AiBaalWaveSuperUniques[w]))
       if r = 0 or r+0x04 < 0: return              ; no command
       message 0xA4 with that word to U (0x00571C00)
       that word 62: a second with 0x17;  105: one with 0x17D
     MonAiUseSkill(10, 285, U, 0, 0);  v18 ← v18 | 1;  v1C ← T + 250;  UnitSetEvent(U, 0x10, 0); return
7. if w ≥ 5:                                       ; signed; the stairs
     MonChangeClass(559, 1);  MonAiInit(MonAiCtlGet(U), 0);  State(142, 1)
     l ← STATLIST_Alloc(flags 0, end 0, U's type and id)
     if l ≠ 0: linked to U;  state 142 on l;  stat 355 ← 559 on l
     Idle(5); return
8. AiBaalThroneWave(U, MonIdFromKind(2, 0x00586B30(g_AiBaalWaveSuperUniques[w])); ctx)

AiBaalThroneWave (0x005EF210):                                            [I] (0x005EF210, 0x005EF30B)
  add skill 286 at level 1 (0x00647280);  store the monster id in the skill (UnitSkillSet18)
  MonAiUseSkill(10, 286, 0, X, Y + 13);  v14 ← v14 + 1;  v1C ← T + 100;  v18 ← (v18 | 2) & ~1
```

- R134a. [I] The block was checked against its anchored instructions (the finding's "bit 1" is the mask 1, as written here). Each wave is an announce (285, 250 frames), then the spawn (286, 100 frames), then a wait for the room to clear; after the fifth spawn one more announce runs, with no message, and at the next clear room the throne becomes `baalcrabstairs` ([row 138](#r138-row-138-baaltostairs-fnsub_005ef620_aibaaltostairs0x005ef620)). `0x00586B30` returns the u16 at `DataTables+0xAE0 + 2k` for `k < 66`, else −1; the five codes are 61–65, the SuperUniques `hcIdx` of `Baal Subject 1..5`. (fn:sub_005EF320_AiBaalThrone@0x005EF320, fn:sub_005EF210_AiBaalThroneWave@0x005EF210, fn:sub_00574370_MonChangeClass@0x00574370, fn:sub_005B0E00_MonAiInit@0x005B0E00, data:g_AiBaalWaveSuperUniques@0x006E3528, tbl:SuperUniques.txt:hcIdx)
- R134b. [C] The init's return; steps 1 to 4 up to the search and its block, 3 boundaries: families `thronei`, `throne`, 240 cases each; control `cmp` fails the 19 it separates, at `T < v1C`. (run:2026-11-03-ai-cat-emu-10)

- R134i. [C] As data: kind 2, `init` 0x005EF310, no `alt`; 1 records (543 baalthrone); reach ·; `aip` set 1; `aidel` 15/15/15; skills Decrepify, Baal Corpse Explode, Defense Curse, Blood Mana. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R134l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R136. Row 136 `BaalTaunt` (fn:sub_005EF710_AiBaalTaunt@0x005EF710)

**`aip`:** 1 the walk's distance limit; 2 the count of still events before the taunt; 3 the teleport's distance limit.

```
1. if t = 0: Idle(25); return                                             [I] (0x005EF710, 0x005EF7F5)
2. still ← t's type is 0 or 1 and t's mode = 1
   fire ← false
   if still: v14 ← v14 + 1;  fire ← v14 > aip(2)
   if fire or not still: v14 ← 0
3. if fire: MonAiUseSkill(4, 284, t, 0, 0); return
4. if dist > aip(3) and UnitTeleport(UnitGetRoom(t), X(t), Y(t), 0, 0): Idle(25); return
5. if dist > aip(1): WalkZ(t); return
6. Idle(25)
```

- R136a. [I] The taunt fires on the `aip(2) + 1`-th event in a row (11th, as data) on which the target stands in mode 1. No draw. (fn:sub_005EF710_AiBaalTaunt@0x005EF710, fn:sub_00554EA0_UnitTeleport@0x00554EA0)
- R136b. [C] The whole map to its 4 boundaries: family `taunt`, 240 cases; controls `d0`, `cmp` fail the 72, 55 they separate. Equality met at `dist > aip(3)` 26, `dist > aip(1)` 18, `v14 > aip(2)` 17 times. (run:2026-11-03-ai-cat-emu-10)

- R136i. [C] As data: kind 1, no `init`, no `alt`; 1 records (545 baaltaunt); reach P; `aip` set 1,2,3; `aidel` 15/15/15; skills Baal Taunt. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R136l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R137. Row 137 `PutridDefiler` (fn:sub_005EFA90_AiPutridDefiler@0x005EFA90)

**`aip`:** 1 the distance under which it keeps away; 2 the step away's length.

```
1. if t ≠ 0 and melee: SetModeAtUnit(4, t); return                        [I] (0x005EFA90, 0x005EFB70)
2. u ← AiUnitSearch(blk{0, 25} at EBP − 0x30, AiDefilerTargetCb, 1)
3. if u ≠ 0:
     if InMeleeRange(U, u, 0): MonAiUseSkill(8, 300, u, 0, 0)             ; Impregnate, S1
     else: WalkZ(u)
     return
4. if dist < aip(1): StepAway(t, (u8) aip(2), 0)
   else: Idle(25)

AiDefilerTargetCb (a, b; u), ret 8:
  returns u when ImpregnateTest(b, u) and AiDistUnits(b, u) ≤ 25, else 0
```

- R137a. [I] No draw. The block was checked against its anchored instructions (the finding's prose agrees). (0x005EFA50, 0x005EFA86, fn:sub_005EFA90_AiPutridDefiler@0x005EFA90, fn:sub_005EFA50_AiDefilerTargetCb@0x005EFA50, fn:sub_005D2140_ImpregnateTest@0x005D2140)
- R137b. [C] Step 1 and the search up to its call, 2 boundaries: family `defiler`, 240 cases; no control separates it. (0x005EFAED, run:2026-11-03-ai-cat-emu-10)

- R137i. [C] As data: kind 1, no `init`, no `alt`; 5 records (546-550 putriddefiler1..putriddefiler5); reach P; `aip` set 1,2; `aidel` 15/15/15; skills Impregnate. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R137l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R139. Row 139 `BaalTentacle` (fn:sub_005EF820_AiBaalTentacle@0x005EF820)

**`aip`:** 1 chance of A1; 2 the idle; 3 half the life's length, in units of 25 frames (10, as data).

```
1. o ← UnitGetOwner(U)                     ; U+0xC8 bit 0x400, GameFindUnit(U+0x94, U+0x98)     [I] (0x005EF820, 0x005EF8FB)
2. if o = 0 or UnitIsDead(o): UnitKilled(0, 1); return
3. if v1C = 0: v1C ← T + 25·(Range(aip(3)) + aip(3))   ; draw, none when aip(3) ≤ 0; imul, 32-bit
4. if T > v1C: UnitKilled(0, 1); return
5. if melee and Range(100) < aip(1): SetModeAtUnit(4, t); return           ; draw
6. Idle(aip(2))
```

- R139a. [I] At stock `v1C − T₀` is 250, 275, … 475. An `aip(3)` ≤ 0 takes no draw: the tentacle dies at once for a negative value, at its next event for 0. `T + 25·(…)` fits in an i32 for every `T` ≤ 2 145 845 322. (fn:sub_005EF820_AiBaalTentacle@0x005EF820, fn:sub_0057CCB0_UnitKilled@0x0057CCB0)
- R139b. [C] The whole map to its 3 boundaries: family `tentacle`, 240 cases, 129 with a draw, the living owner 154 times; controls `le`, `d0`, `cmp` fail the 7, 99, 17 they separate. Equality met at `T > v1C` 17, the draw 7 times. (run:2026-11-03-ai-cat-emu-10)

- R139i. [C] As data: kind 1, no `init`, no `alt`; 5 records (562-566 baaltentacle1..baaltentacle5); reach ·; `aip` set 1,2,3; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R139l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R141. Row 141 `BaalMinion` (fn:sub_005EF910_AiBaalMinion@0x005EF910)

**`aip`:** 1 in melee range: chance to act; 2 out of it: chance to walk; 3 the skill's chance, and the idle; 4 the delay after every command.

```
1. if t ≠ 0 and melee:                                                    [I] (0x005EF910, 0x005EFA3B)
     if chance(1):
       if Skill1 ≥ 0 and Range(100) < aip(3): MonAiUseSkill(Sk1mode, Skill1, t, 0, 0)
       else: SetModeAtUnit(4, t)
     else: Idle(aip(3))
   else if chance(2): WalkZ(t)
2. Delay(aip(4))                           ; always
```

- R141a. [C] The map to its 5 boundaries: family `bminion`, 240 cases, all drawing; controls `le`, `d0`, `u16` fail the 41, 135, 4 they separate. The `Range(100) < aip(3)` compare has no case at equality, so no control moves it; `Delay` is the first boundary only when `chance(2)` fails. (run:2026-11-03-ai-cat-emu-10, fn:sub_005EF910_AiBaalMinion@0x005EF910, fn:sub_005DE0F0_MonAiDelay@0x005DE0F0)

- R141i. [C] As data: kind 1, no `init`, no `alt`; 3 records (571-573 baalminion1..baalminion3); reach U; `aip` set 1,2,3,4; `aidel` 15/14/13; skills Smite. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R141l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 11: bosses-B (Diablo, Nihlathak, the Baal rows, Uber Diablo and Baal)

#### R51. Row 51 `Diablo` (fn:sub_005E9170_AiDiablo@0x005E9170)

No `aip` slot read: the skills are fixed by slot, and the machinery's target only gates the event (kind 1); the think reads neither `t`, `dist` nor `melee`.

```
alt 0x005E8480 (and Baal's 0x005FCF30, the same instructions):             [I] (0x005E8480, 0x005E8525)
  h ← AiParamsFind(U, 10, 0);  x, y ← h's x, y, or 0 without h
  if state 12: State(12, 0)
  MonAiInit(ctl, ctl.state)                     ; the full path clears v14, v18, v1C and frees the parameter records
  if not AiParamsFind(U, 10, 0) and x ≠ 0 and y ≠ 0: Push({kind 10, x, y})
  Idle(1)

think:                                                                     [I] (0x005E9170, 0x005E96FE)
1. h ← AiParamsFind(U, 10, 0);  if h = 0: Push({kind 10, X, Y});  find it again      ; the home point
2. t ← AiPickPlayerTarget(&score, &n, h, AiDiabloPickCb)                  ; R133's walk; AiPlayerThreatScore
3. k ← AiDiabloDecide(ctl, U; t, score, n, h)
4. if k ≠ 5 and 0 ≤ Skill8 < Skills count and its aurastate a ≥ 0 and U lacks a
      and MonAiUseSkill(Sk8mode, Skill8, t, 0, 0): v14 ← 0; return
5. by k (1..16; 0, 11 and above 16 the default), then v14 ← 0:
     1:  Ovr(0, 20, 0);  WalkPt(X(t), Y(t))
     2, 3, 4:  SetModeAtUnit(4, t), SetModeAtUnit(5, t), SetModeAtUnit(11, t)
     5:  Skill1 < 0: Idle(2)
         state 12: State(12, 0);  Idle(2)
         else: MonAiUseSkill(Sk1mode, Skill1, t, 0, 0);  v14 ← 5; return       ; v14 stays 5
     6, 7, 8, 9, 10, 13:  Skill 3, 2, 4, 7, 5, 6 ≥ 0: MonAiUseSkill(its mode, it, t, 0, 0), else Idle(2)
     12: T56(t, 4, 0)
     14: Ovr(0, 50, 100);  if WalkPtStop(h.x, h.y): done
         CancelEvents(2, 0);  p ← AiPathDistToPoint(U, h.x, h.y)
         sx ← −1 when X < h.x, +1 when X > h.x, else 0;  sy likewise
         Ovr(0, 50, 100);  if WalkPtStop(h.x + (p >> 1)·sx, h.y + (p >> 1)·sy): done
         CancelEvents(2, 0);  Idle(2)
     15: if t = 0 or t is not a player: Idle(3)
         g ← PlayerPortalGet(t);  if GameFindUnit(2, g) = 0: Idle(2)
         else Skill7 ≥ 0: MonAiUseSkill(Sk7mode, Skill7, 0, g, 2), else Idle(2)
     16: Ovr(0, 20, 0);  Ring(5)
     default: Idle(d = 1 ? 8 : d = 2 ? 4 : 12)

AiDiabloDecide:                                                            [I] (0x005E8810, 0x005E8EA1)
1. if v14 ≠ 0: return v14
2. if t = 0:
     if COLL_PatternTestBool(U's room, X, Y, 2, 0x40): return 16
     return step mod 1000 ≥ 1 ? 11 : 4                 ; one step
3. p ← the unit of PlayerPortalGet(t), when t is a player
   P ← p ≠ 0 and p's level = 108 and UnitDistance(p, h.x, h.y) < 85    ; unsigned; h not tested for null
   L ← the left or right skill of t by AiUnitHasAreaSkill's rule      ; ids 59, 56; 51 above level 3; 27 above level 7
   far ← h ≠ 0 and AiDistToPointSized(t, h) > 85;  vfar ← the same > 105
   m ← InMeleeRange(U, t, 0);  lc ← AiLineClear(U, t);  f ← t's stat 39;  l ← t's stat 41
4. w[0..16] ← the table of m, else lc, else blocked, edited
5. if MonSkillTargetOk(199, t, 0, 0): w[9] ← 0
6. if w[15] ≠ 0 and p ≠ 0 and not MonSkillTargetOk(199, p, 0, 0): w[15] ← 0
7. return pick(w, 17), or 11
```

| Table | Start (non-zero) | Edits, in order |
|---|---|---|
| melee (`m`) | w2 40, w3 70, w5 40, w6 24, w7 40, w8 15 | life(t) < 20: w2 = 50; `cold`(t): w7 = w8 = 0; f > l: w6 −10, f < l: w6 +10; `!lc`: w5 = w6 = 0; P: w15 = 10 |
| ranged (`lc`) | w5 25, w6 25, w8 15, w9 20, w10 10, w12 20 | `AiDistUnits(U, t)` > 25: w8 −5, w10 = 20, w5 = 0; f > l: w6 −10, w8 −10, f < l: +10 each; n < 2: w6 −10; n > 3: w6 +5; score > 60: w9 +10; n < 2 and the difficulty < 2: w9 = 0; L and not far: w6 +10, w10 = 30, w13 = 15; far: w1 = 0, w12 = 10, w10 = 0, w13 = 15, w9 = 10 if 0; vfar: w9 = 20, w14 = 60; P: w15 = 15 |
| blocked | w4 5, w6 25, w8 25, w9 40, w12 25 | n < 2: w8 −5, w6 = 0, w1 = 25, w9 = 0; L and not far: w13 = 15; far: w1 = 0, w12 = 15, w13 = 25, w9 = 20 if 0, then −5 if n < 2; vfar: w14 = 60; P: w15 = 20 |

```
pick(w, n), one step when the sum is above 0:                              [I] (0x005FC130, 0x005FC1B8)
  sum ← the sum of the n > 0 words;  if sum ≤ 0: the fallback
  r ← step's low word mod sum                  ; a power of two takes the mask
  the first k whose running sum exceeds r (signed);  none: the fallback

AiPlayerThreatScore(c), with home (0x005E8530), and Baal's AiBaalThreatScore (0x005FBB00):   [I] (0x005E8530, 0x005E8804, 0x005FBB00, 0x005FBDBF)
  m ← InMeleeRange(U, c, 0)
  H ← home ≠ 0 and AiDistToPointSized(U, home) > 85 and AiDistToPointSized(c, home) < 85 ? 100 : 0      ; Baal: 75
  R ← (C43 + 4·(s36 + 2·s37) + s41 + s39) ÷ 15       ; C43 ← m ? s43 : 0; Baal: s43 always
  D ← ((s58 >> 8) + s55 + s53 + s51 + s49 + s22) ÷ 2
  K ← (lvl(left)·rank(left) + lvl(right)·rank(right)) ÷ 4     ; rank = attackrank, u8
  A ← m ? 100 : AiLineClear(U, c) ? 75 : 0
  if c is a monster and (class out of range or MonStats threat ≤ 1): return 0
  T ← 3·(life(c) < 20 ? 100 : 0) + R + 5·(H + A) + 2·(K + 2·(cold(c) ? 100 : 0) + D)
  return T ÷ 22, or 1 when that is 0
```

- R51a. [I] The three tables are read from the instructions by [ai/0012 § 2.3](../../../findings/ai/0012-batch11.md). `AiDiabloPickCb(a, b)` and `AiBaalPickCb`: fatal on a null, else `a+0x18 = b+0x18` and `AiDistToPoint(b, X(a), Y(a)) < 1020`, unsigned. `sN` is `STATS_GetUnitStat(c, N, 0)`; each division signed, truncating. A skill node out of the Skills range reads the byte at address `0x18E`. Weights 0, 11 and 16 stay 0 in every table. The score test is unsigned here. The difficulty is `MonPlayerBonus`'s `b+0x0C`. Case 15's `2` is a push meant for `Idle`, kept as the skill's `y` argument. `Skill8` is set only on `diabloclone` and `uberdiablo` at stock. (0x005E8D48, 0x005E8D6B, 0x005E9690, fn:sub_005E8EB0_AiDiabloPickCb@0x005E8EB0, fn:sub_005FC000_AiBaalPickCb@0x005FC000, fn:sub_00573930_MonPlayerBonus@0x00573930, fn:sub_005FD470_MonSkillTargetOk@0x005FD470, fn:sub_005FC0C0_AiUnitHasAreaSkill@0x005FC0C0, fn:sub_005E8530_AiPlayerThreatScore@0x005E8530, data:g_AiDiabloActJumps@0x005E9704, tbl:MonStats.txt:threat, tbl:Skills.txt:attackrank)
- R51b. [C] The maps to their first callee, and no more: `dalt` and `balt` to `HasState(U, 12)`; `diablo` to `AiParamsPush` or the pick; `ddec`: `v14 ≠ 0` returned, the collision test, `PlayerPortalGet(t)` or `UNIT_GetLeftSkill(t)`; `dcb`, `bcb` the callbacks whole, `wpick` the pick whole: twenty families in the batch, 240 cases each. (run:2026-11-03-ai-cat-emu-11)

- R51i. [C] As data: kind 1, no `init`, `alt` 0x005E8480; 2 records (243 diablo, 333 diabloclone); reach ·; `aip` set —; `aidel` 15/13/12; skills DiabLight, DiabCold, DiabFire, DiabWall, DiabRun, PrimeFirewall, DiabPrison, Diablogeddon. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R51l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R128. Row 128 `Nihlathak` (fn:sub_005EE5D0_AiNihlathak@0x005EE5D0)

**`aip`:** 1 in melee: chance of the teleport; 2 the teleport's range; 3 chance of the corpse explosion; 4 chance of the whip branch; 5 the distance under which it may step away.

```
init 0x005EE5C0: ret 4                                                     [C] (run:2026-11-03-ai-cat-emu-11)

think, six inline steps at most, each D100():                              [I] (0x005EE5D0, 0x005EEA93)
1. A5Q4_NihlathakSeen                ; quest 34: a record with +0x09 ≠ 0, +0x0B < 3 (u8) gets +0x14 ← 0, QUESTS_SetState(rec; 0, A5Q4_StepBits, 1)
2. if state 12: State(12, 0)
3. s1 ← SKILLS_GetUnitSkill(U, Skill1)
4. if t = 0:
     if s1 ≠ 0 and St3or19: AiUseSkillNearSelf(aip(2); id(s1), s1's +0x08 word); return
     Idle(25); return
5. if s1 ≠ 0 and melee and D100() < aip(1): AiUseSkillNearSelf(aip(2); id(s1), s1's +0x08 word); return     ; Imp Teleport
6. if dist < aip(5) and D100() < 40 and StepAway(t, 5, 1): return
7. if Skill3 > 0 and U has it and D100() < aip(3):
     c ← CorpsePickNear(t; Skill3, its level)
     if c ≠ 0 and MonAiUseSkill(Sk3mode, Skill3, c, 0, 0): return                ; corpse explosion
8. if Skill4 > 0 and U has it and D100() < 60 and dist < 14: MonAiUseSkill(Sk4mode, Skill4, t, 0, 0); return
9. if Skill2 > 0 and D100() < aip(4) and MonHasSkill(Skill2):
     blk ← {0, 625, 50, 0, 0, 0};  AiUnitSearch(blk, AiOverseerMinionCb, 1)
     if blk[4] ≠ 0: MonAiUseSkill(Sk2mode, Skill2, blk[4], 0, 0); return          ; Overseer Whip
     if Skill5 > 0 and SpawnClassCellTest(528 or −1, U's room; X, Y, 0):
       v3C ← LevelClassVariant(U's room, 453 or −1);  MonAiUseSkill(Sk5mode, Skill5, t, 0, 0); return    ; MinionSpawner
     Ring(6); return
10. if Skill4 > 0 and U has it and dist < 14: MonAiUseSkill(Sk4mode, Skill4, t, 0, 0); return             ; no draw this time
11. if D100() < 60: WalkZ(t)
12. Idle(5)                                         ; after the walk too
```

- R128a. [I] Draw order: `aip(1)`, 40, `aip(3)`, 60, `aip(4)`, 60, each at most once per event, each compared `jge` signed; with stock slots at most five fall in one event. Each draw's reach is the steps' `and` order above, so a step whose earlier test fails takes none. The search block admits no weak minion (`blk[0] = 0`) and keeps a non-unique one within squared distance 625. (0x005EE68F, 0x005EE713, 0x005EE786, 0x005EE828, 0x005EE89D, 0x005EEA46, fn:sub_0058BC40_A5Q4_NihlathakSeen@0x0058BC40, fn:sub_0056E390_CorpsePickNear@0x0056E390, fn:sub_005E26D0_AiOverseerMinionCb@0x005E26D0, fn:sub_005FD350_SpawnClassCellTest@0x005FD350, fn:sub_0063EC70_LevelClassVariant@0x0063EC70)
- R128b. [C] The init's return and the think through the quest step: to `QUESTS_SetState` with the node's `+0x14` = 0, or past it to `HasState(U, 12)` with the byte unchanged: families `nihli`, `nihl`, 240 cases each; control `cmp` fails the 25 it separates, at `+0x0B < 3`. (run:2026-11-03-ai-cat-emu-11)

- R128i. [C] As data: kind 2, `init` 0x005EE5C0, `alt` 0x005E5280; 1 records (526 nihlathakboss); reach U; `aip` set 1,2,3,4,5; `aidel` 15/15/15; skills Imp Teleport, Overseer Whip, NihlathakCorpseExplosion, Horror Arctic Blast, MinionSpawner. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R128l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R135. Row 135 `BaalCrab` (fn:sub_005FCFE0_AiBaalCrab@0x005FCFE0)

No `aip` slot read: the skills are fixed by id or slot. Row 135 is kind 0 (no search), and acts with no target too.

```
think:                                                                     [I] (0x005FCFE0, 0x005FD0DF)
1. t ← AiBaalPickTarget(&score, &n, 0, AiBaalPickCb)                       ; 0x005FBDD0: R133's walk, its own score; no home bonus
2. h ← the kind-10 record, pushed from U's own point when missing
3. k ← AiBaalDecide(ctl, t, score, n, h)
4. AiBaalAct(ctl, t, k, h)
5. Delay(25)

AiBaalDecide:                                                              [I] (0x005FC630, 0x005FC81F)
1. if v14 ≠ 0: return v14                                ; no writer in 0x005FBB00–0x005FD350
2. if t = 0:
     if COLL_PatternTestBool(U's room, X, Y, 2, 0x40): return 4
     return D100() < 8 ? 9 : 1
3. p ← the unit of PlayerPortalGet(t), when t is a player
   P ← p ≠ 0 and p's level = 132 and (h = 0 or UnitDistance(p, h.x, h.y) < 75)
   far ← h ≠ 0 and AiDistToPointSized(t, h) > 75;  vfar ← the same > 100
   m ← InMeleeRange(U, t, 0);  lc ← AiLineClear(U, t)
4. return pick(w, 16), or 1      ; R51's pick; w from melee if m, else ranged if lc, else blocked
```

| Table (`B` = (Normal ? `b₀` : `b₁`) + 100 − life(U)) | Start (non-zero) | Edits, in order |
|---|---|---|
| melee 0x005FC1C0 | w1 `B` (75/50), w8 20, w9 30, w10 150, w11 10, w12 10, w13 70 (Normal 45), w14 40 | life(t) < 33: w10 = 200; `cold`(t): w8 = w13 = w11 = 0; `!lc`: w11 = w13 = w12 = 0 |
| ranged 0x005FC450 | w1 `B` (125/100), w2 5, w3 5, w4 5, w6 5, w8 40, w9 40, w11 70, w12 80, w13 60 (Normal 40), w14 20, w15 max(0, 10·(2 − v18)) | `AiDistUnits(U, t)` > 35: w6 = 15, w13 = 0; > 25: w14 = 30, w11 = 0; n < 2: w11 −10; n > 3: w13 +25; score > 60: w8 = 70; n < 2 and the difficulty < 2: w8 = 0; S(t) and not far: w6 +30, w11 +10, w14 +15; far: w6 +25, w14 +35, w2 = 0, w3 = 25; vfar: w5 = 60; P: w7 = 0 |
| blocked 0x005FC300 | w1 `B` (125/100), w2 20 (45 if n < 2), w3 20, w4 20, w6 20, w8 80, w9 70, w10 0 (25 if n < 2) | S(t) and not far: w13 = w14 = 50; far: w2 = w6 = 0, w3 = 35, w11 = 25, w13 = 25; vfar: w5 = 60 |

```
AiBaalAct(ctl, t, k, h):                                                   [I] (0x005FCB60, 0x005FCEF0)
  if U = 0 or U's class is out of range: return
  by k:
    1:  Idle(d = 1 ? 15 : d = 2 ? 5 : 35); return
    2, 6: WalkToward(t, 12, 0); return
    3:  T56(t, 6, 1); return
    4:  Ring(16); return
    5:  if h ≠ 0: WalkPt(h.x, h.y); return;  else Idle(5)
    8:  if t = 0: restart with k = 0                                       ; to Idle(5)
        if Skill6 > 0 and (UnitGetMaxHp(t) > UNIT_GetMaxMana(t) or t is not a player): MonAiUseSkill(Sk6mode, Skill6, t, 0, 0); return     ; Defense Curse
        if Skill7 > 0 and t is a player: MonAiUseSkill(Sk7mode, Skill7, t, 0, 0); return             ; Blood Mana
        return                                                             ; no command
    9:  MonAiUseSkill(9, 315, t, 0, 0); return                             ; Baal Tentacle
    10: SetModeAtUnit(5, t); return
    11: add skill 316 at level 1 (0x00647280);  MonAiUseSkill(10, 316, t, 0, 0); return      ; Baal Nova
    12: MonAiUseSkill(8, 317, t, 0, 0); return
    13: MonAiUseSkill(4, 318, t, 0, 0); return
    14: if t = 0: AiBaalAct(ctl, 0, 0, h); return
        e ← UnitEdgeDistance(U, t), 1 when 0
        x ← X + 25·(X − X(t)) ÷ e;  y likewise                             ; away from t, signed
        if U's class = 709: MonAiUseSkill(Sk5mode, Skill5, 0, X(t), Y(t)); return
        if SpawnPosPick(U's room; 0, class, &x, &y, 0): MonAiUseSkill(Sk5mode, Skill5, 0, x, y); return
        AiBaalAct(ctl, t, 0, h); return
    15: BaalCloneSpawn;  then Idle(5)
    else (7, 0, above 15): Idle(5)

BaalCloneSpawn:                                                            [I] (0x005FC830, 0x005FCB56)
  nothing when a group member other than U lives (MonGroupForEach, 0x005FC830: non-null, mode not 0 or 12)
  nothing when U has a living owner (UnitGetOwner, UnitIsDead)
  class ← SpawnClassByBase(570 when the MonStats count > 570, else −1)      ; baalclone
  point ← UNIT_GetTargetUnit(U)'s position, or U's
  x ← point.x + step mod 24 − 12;  y ← point.y + step mod 24 − 12            ; two steps
  r ← RoomAtSubtile;  r = 0: nothing
  c ← SpawnAtPos;  c = 0: nothing
  c+0xC4 ← c+0xC4 | 0x4020000;  Delay(15) on c
  MonSetOwner both ways;  MonGroupAddMember
  c's stat 7 ← UnitGetMaxHp(U) ÷ 3;  c's stat 6 ← U's stat 6 ÷ 3;  c's stat 74 ← 0
  UnitSetEvent(U, 16, 0);  v18 ← v18 + 1
```

- R135a. [I] The three tables are read from the instructions by [ai/0012 § 2.8](../../../findings/ai/0012-batch11.md). Actions by weight: 1 idle, 2 walk toward, 3 `T56`, 4 ring 16, 5 home, 8 curse, 9 Tentacle, 10 A2, 11 Nova, 12 Inferno, 13 Cold Missiles, 14 teleport, 15 clone. `v18` counts the clones, so the clone weight falls from 20 to 0 after two. `P` only zeroes `w7`, already 0, so the portal flag has no effect on Baal's draw. `S(t)` is `AiUnitHasAreaSkill`: the target's right skill, else its left. Level 132 is the Worldstone Chamber. The block's clone was checked against its anchored instructions (the finding's prose agrees, and the room test is added). `Skill5`'s slot is used with no test. (0x005FC59E, 0x005FCDC6, 0x005FCB41, fn:sub_005FC1C0_AiBaalDecideMelee@0x005FC1C0, fn:sub_005FC450_AiBaalDecideRanged@0x005FC450, fn:sub_005FC300_AiBaalDecideBlocked@0x005FC300, fn:sub_005FC0C0_AiUnitHasAreaSkill@0x005FC0C0, data:g_AiBaalActJumps@0x005FCEF0, fn:sub_0054DC40_SpawnPosPick@0x0054DC40, fn:sub_0058F380_MonGroupForEach@0x0058F380, fn:sub_0063EFA0_SpawnClassByBase@0x0063EFA0, fn:sub_005B2F20_SpawnAtPos@0x005B2F20, fn:sub_005FC830_BaalCloneCountCb@0x005FC830)
- R135b. [C] Row 135's map to the pick; `AiBaalDecide`'s to its first callee, and each table at its first call with its start words, the blocked table's `n < 2` edits and the ranged table's clone weight included; `AiBaalAct`'s for every `k` (1–15, 0, 16, 100, `0xFFFFFFFF`), each action's first callee, and no more, so the curse choice, the teleport point and the clone stay `[I]`: families `bcrab`, `bdec`, `bmelee`, `bblock`, `branged`, `bact`, 240 cases each. (run:2026-11-03-ai-cat-emu-11)

- R135i. [C] As data: kind 0, no `init`, `alt` 0x005FCF30; 1 records (544 baalcrab); reach ·; `aip` set —; `aidel` 15/13/12; skills Baal Nova, Baal Inferno, Baal Tentacle, Baal Cold Missiles, Baal Teleport, Defense Curse, Blood Mana. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R135l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R138. Row 138 `BaalToStairs` (fn:sub_005EF620_AiBaalToStairs@0x005EF620)

**`aip`:** 1 the edge distance under which it leaves (4, as data).

```
1. blk ← {0, 25};  o ← AiUnitSearch(blk, AiBaalPortalCb, 1)                [I] (0x005EF5E0, 0x005EF708)
2. if o = 0: Idle(25); return
3. if UnitEdgeDistance(U, o) < aip(1):
     A5Q6_ChamberPortalOpen;  State(146, 1);  0x00648730(U's path);  CancelEvents(2, 0)
     RoomUnitOp(U's room, U's type, U's id);  UNIT_CollUnmarkRect(U);  UnitRoomUnlink(U);  UnitFree(U); return
4. Ovr(1, 0, 0);  WalkZ(o)

AiBaalPortalCb(cand, blk): cand ≠ 0, type 2, class 563 and UnitEdgeDistance(cand, searcher) ≤ blk[1] ? cand : 0
```

- R138a. [I] Object 563 is `baals portal`. No draw, and the think ignores the context's target. (fn:sub_0058E600_A5Q6_ChamberPortalOpen@0x0058E600, fn:sub_006416D0_UnitEdgeDistance@0x006416D0, fn:sub_00555600_UnitFree@0x00555600, tbl:Objects.txt:Id)
- R138b. [C] The think's map to its search (block `{0, 25}`) and the callback's to its distance call or its 0 return: families `stairs`, `pcb`, 240 cases each; no control separates them. (run:2026-11-03-ai-cat-emu-11)

- R138i. [C] As data: kind 1, no `init`, no `alt`; 1 records (559 baalcrabstairs); reach ·; `aip` set 1; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R138l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R140. Row 140 `BaalCrabClone` (fn:sub_005FD210_AiBaalClone@0x005FD210)

No `aip` slot read.

```
1. o ← MonsterOwner(U);  if o ≠ 0 and UnitIsDead(o): UnitKilled(0, 1); return    [I] (0x005FD210, 0x005FD343)
2. w ← UnitGetOwner(U);  if w = 0 or UnitIsDead(w): UnitKilled(0, 1); return
3. t ← the pick, as row 135's
4. h ← home, pushed from X, Y
5. k ← AiBaalDecide(…);  if k is 7, 9, 14 or 15: k ← 2
6. if t = 0: Idle(15); return
7. AiBaalAct(ctl, t, k, h);  Delay(25)
```

- R140a. [I] `AiBaalDecide` and `AiBaalAct` are [row 135's](#r135-row-135-baalcrab-fnsub_005fcfe0_aibaalcrab0x005fcfe0). `MonsterOwner` reads `AiCtl+0x28/+0x2C/+0x30`; `UnitGetOwner` the unit's `+0xC8` bit `0x400` and `+0x94/+0x98`. (fn:sub_0058F0D0_MonsterOwner@0x0058F0D0, fn:sub_00552FD0_UnitGetOwner@0x00552FD0, fn:sub_0057CCB0_UnitKilled@0x0057CCB0)
- R140b. [C] The map to `UnitKilled(0, 1)` or the pick, with both owner lookups and `UnitIsDead` run on the image: family `bclone`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-11)

- R140i. [C] As data: kind 0, no `init`, `alt` 0x005FCF30; 1 records (570 baalclone); reach ·; `aip` set —; `aidel` 15/14/12; skills Baal Nova, Baal Inferno, Baal Tentacle, Baal Cold Missiles, Baal Clone Teleport, Defense Curse, Blood Mana. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R140l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R145. Row 145 `UberBaal` (fn:sub_005FD200_AiUberBaal@0x005FD200)

`ret 4`, as [row 146](#r146-row-146-ubermephisto-fnsub_005f81c0_aiubermephisto0x005f81c0): a kind-1 event with a target commands nothing from the think. Its `alt` is Baal's, [row 51's block](#r51-row-51-diablo-fnsub_005e9170_aidiablo0x005e9170). [I] (fn:sub_005FD200_AiUberBaal@0x005FD200, fn:sub_005FCF30_AiBaalAlt@0x005FCF30)

- R145a. [I] What drives the event, and its limits, is [monsters/special](../special.md): with a target the boss sight pause fires once, then this event queues no next one. (fn:sub_005B1740_MonAiEvent@0x005B1740, fn:sub_005B1140_MonAiBossSightPause@0x005B1140)

- R145i. [C] As data: kind 1, no `init`, `alt` 0x005FCF30; 1 records (709 uberbaal); reach ·; `aip` set —; `aidel` 15/13/12; skills Baal Nova, Baal Inferno, Baal Tentacle, Baal Cold Missiles, Baal Teleport, Defense Curse, Blood Mana, Chilling Armor. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R145l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R147. Row 147 `UberDiablo` (fn:sub_005E9DF0_AiUberDiablo@0x005E9DF0)

`ret 4`, as [row 146](#r146-row-146-ubermephisto-fnsub_005f81c0_aiubermephisto0x005f81c0): a kind-1 event with a target commands nothing from the think. Its `alt` is Diablo's, [row 51's block](#r51-row-51-diablo-fnsub_005e9170_aidiablo0x005e9170). [I] (fn:sub_005E9DF0_AiUberDiablo@0x005E9DF0, fn:sub_005E8480_AiDiabloAlt@0x005E8480)

- R147a. [I] What drives the event, and its limits, is [monsters/special](../special.md): with a target the boss sight pause fires once, then this event queues no next one. (fn:sub_005B1740_MonAiEvent@0x005B1740, fn:sub_005B1140_MonAiBossSightPause@0x005B1140)

- R147i. [C] As data: kind 1, no `init`, `alt` 0x005E8480; 1 records (705 uberdiablo); reach ·; `aip` set —; `aidel` 15/13/12; skills DiabLight, DiabCold, DiabFire, DiabWall, DiabRun, PrimeFirewall, DiabPrison, Diablogeddon. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R147l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

### Batch 12: towns, NPCs and the state rows

#### R31. Row 31 `NpcOutOfTown` (fn:sub_005E7880_AiNpcOutOfTown@0x005E7880)

No `aip` slot read. `R3` is `AiCtlParamGet(3)`; `Pfx` below means the class's pair of quest calls: for class 527 the second name, for the others the first.

```
AiNpcOutOfTownInit (0x005E77A0), called first on every event:              [I] (0x005E77A0, 0x005E7880)
  if R3's two words are 0:
    (R3.x, R3.y) ← (X + 3, Y + 3)
    if Pfx(0x005944B0, 0x0058A940) = 0: Pfx(0x005944F0, 0x0058A980);  UnitSetStat(U, 6, 0, 0);  SetMode(12, X, Y)
    R3+0x14 ← 1;  R3+0x18 ← 0;  Idle(1);  returns 1
  returns 0

think:                                                                     [I] (0x005E7880, 0x005E7AAF)
1. if the init returned 1: return
2. class 527: 0x0058AA10
3. if NpcInteractAny(L): Idle(40); return          ; L when U is a monster with its data
4. if U's mode is 12: return
5. AiNpcNearPlayer                                 ; its result is not read
6. if no R3: the init again;  Idle(40); return
7. if R3+0x14 ≥ 2:
     R3+0x14 ← R3+0x14 + 1
     p ← Pfx(0x00594450, 0x0058A8D0);  if none: Idle(20); return
     if R3+0x14 < 8 and AiPathDistToPoint(U, p) > 0: WalkPt(p); return
     the partner, UnitSetStat(U, 6, 0, 0), SetMode(12, X, Y); return
8. if AiPathDistToPoint(U, R3) > 1 (signed) and R3+0x18 ≤ 5:
     R3+0x18 ← R3+0x18 + 1
     if class 527 and 0x0058A9F0 ≠ 0: Idle(20);  R3+0x18 ← 0; return
     WalkPt(R3); return
9. if R3+0x14 = 1:
     if Pfx(0x005943B0, 0x0058A820) = 0: R3+0x14 ← 1;  R3+0x18 ← 1;  Idle(20); return
     R3+0x14 ← 2
10. Idle(20)
```

- R31a. [I] No draw. `UnitSetStat(U, 6, 0, 0)` is `hitpoints`. The block was checked against its anchored instructions (the finding's prose agrees). (fn:sub_005E7880_AiNpcOutOfTown@0x005E7880, fn:sub_005E77A0_AiNpcOutOfTownInit@0x005E77A0, fn:sub_00627260_UnitSetStat@0x00627260)
- R31b. [C] The think to its first boundary, 6 reached, and the init, 4: families `oot`, `h77a0`, 240 cases each; no control separates them. (run:2026-11-03-ai-cat-emu-12)

- R31i. [C] As data: kind 0, no `init`, no `alt`; 2 records (146 cain1, 527 drehyaiced); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R31l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R32. Row 32 `Npc` (fn:sub_005E7130_AiNpc@0x005E7130)

No `aip` slot read: the town chain's words are the parameter records. `home` is `AiCtlParamGet(10)`, `R4`, `R5`, `R7` the kind-4, 5, 7 records, `L` the unit's interact list.

```
think:                                                                     [I] (0x005E7130, 0x005E733B)
1. if AiNpcSaveHome: return
2. by class, each going on to step 3 unless it says end:
     201 jerhyn:  if 0x0059F570 = 0: Idle(40); end
                  A2Q4_GuardBlock(&a, &b);  if a: Idle(20)
                  if b = 0: end
                  if 0x0059B6E0 ≠ 0 and home exists: home ← (X + 9, Y);  Idle(50); end
     254 alkor:   if 0x005BAD20 ≠ 0: SetMode(8, 0, 0);  0x005BAD40; end
     255 ormus:   if 0x005B9CA0(&p) ≠ 0:
                    if AiPathDistToPoint(U, p) > 3: WalkPt(p); end
                    SetMode(8, 0, 0);  0x005B9CD0; end
     265 cain5:   if 0x00594360(&p) ≠ 0:
                    if AiPathDistToPoint(U, p) > 2: WalkPt(p); end
                    0x005945F0
     512 drehya:  A5Q4_RedPortalCreateAI
3. if AiNpcNearPlayer: return
4. if AiNpcScriptStep: return
5. if AiNpcPathPick: return
6. Idle(8)

AiNpcSaveHome:                                                             [I] (fn:sub_005E6800_AiNpcSaveHome@0x005E6800)
  if home's +0x0C and +0x10 are both 0: home ← (X, Y);  Idle(20);  true
  false

AiNpcHomeLeash(n):                                                         [I] (fn:sub_005E6860_AiNpcHomeLeash@0x005E6860)
  no home: AiNpcSaveHome
  if the distance to home ≤ n (unsigned): false
  R4 ← {home, 12, 10} when it exists;  Idle(10);  true

AiNpcNearPlayer:                                                           [I] (0x005E6909, 0x005E6AD5)
1. p ← AiNearestPlayer(&f);  n ← AiDistUnits(U, p)
2. if no L: false
3. h ← NpcInteractHas(L, p), or 1 when p is a busy player
4. if NpcInteractAny(L) or h or v14 > 0:
     if AiPathDistToPoint(U, (v18, v1C)) > 2 and v14 > 36: WalkPt(v18, v1C)
     else if v14 > 0: clear the path flag;  Idle(8)
     v14 ← 0 when v14 < 0, else v14 − 1
     true
5. if p = 0 or p = U: false
6. if 3 ≤ n ≤ 23:
     if AiNpcHomeLeash(16): true
     Ovr(1, 0, 0);  WalkToward(p, n ≥ 5 ? 3 : n − 2, 2);  true
7. clear the path flag
   if v18 = 0: v18 ← 60;  a player p: UnitSetEvent(U, 18, p)
   else if v18 < 0: v18 ← 0
   else: v18 ← v18 − 1
   Idle(20);  true

AiNearestPlayer(&f):                                                       [I] (0x005DDF20, 0x005DDF85, 0x005DDE80, 0x005DDF19)
  no room: returns 0
  AiUnitSearch(U, {0, 0x7FFFFFFF}, AiNearestPlayerCb, 2);  none found: returns U
  found: the unit;  f ← 1 when its stored distance is below 4
  the callback keeps a candidate of type 0 with AiDistUnits ≤ 15:
    with the searcher's interact bit set: also 0x00544590(G, cand, U) ≠ 0 and nearer than the best
    clear, or a bad class or record: the last one kept wins

AiNpcScriptStep, true on a command:                                        [I] (0x005E6AE0, 0x005E6DD5)
1. if R4 and R4+0x14 > 0:
     (x, y) ← R4
     if x ≠ 0, y ≠ 0 and the distance > 3:
       Ovr(g_NpcScriptCounter mod 4 = 0 ? 5 : 1, 0, 0);  WalkPtCmd(x, y);  counter + 1
     else: Idle(R4+0x18)
     R4+0x14 ← R4+0x14 − 1;  true
2. if R5:
     a ← R5+0x0C
     if a > 0 and odd: Ring(byte R5+0x10);  a − 1;  true
     if a > 0 and even:
       if R5+0x14 > 0: Idle(R5+0x18);  a − 1;  R5+0x14 − 1;  true
       a − 1, and on to step 3
     else if R5+0x14 > 0: Idle(R5+0x18);  R5+0x14 − 1;  true
3. if R7 and m ← R7+0x0C ≠ 0:
     if m is not 8, 9, 10 or 11: m ← 0;  Idle(50);  true
     D ← the distance to (R7+0x10, R7+0x14)
     if D > 0 and R7+0x18 > 0:
       Ovr(7, 0, 0);  if not WalkPtCmd: Idle(25)
       R7+0x18 − 1;  true
     if D > 1: m ← 0
     the path facing 0x00648820(path, f): class 0x9A 0x38; 0x9B 0x34; 0xB2 4; 0x195 0x34 at m 8, 0x30 at m 9
     class 0x1FF: if Range(100) > 4: m ← 0;  Idle(50);  true
     if m ≠ 0:
       if U's mode = m: Idle(50);  true
       SetModeAtUnit(m, U);  m ← 0;  true
     class 0xB2: if Range(100) < 66: m ← 8
4. false

AiNpcPathPick:                                                             [I] (0x005E7080, 0x005E7123)
  list ← AiCtl+0x38                  ; {count, 12-byte nodes {action, x, y}}
  if no list: false                  ; no draw
  if D100() ≥ 66 or count = 0: false
  k ← RNG_RangeB(U's seed, count)
  action outside 0..6 (signed), or its table word 0 (actions 0, 6): false
  run the action (node)

the actions, a point with x = 0 or y = 0 giving false at once:             [I] (0x005E6DE0, 0x005E7075)
  1, 3:  distance 0: false;  else Ovr(7, 0, 0);  WalkPtCmd(x, y);  R4 ← {x, y, 12, 10};  true
  2:     as 1, then R4 ← {x, y, 20, 10}
  4:     as 1, then R7 ← {MonModeAllowed(class, 8) ? 8 : 1, x, y, 4};  R4 ← {x, y, 12, 10}
  5:     as 4, with mode 9
```

- R32a. [I] The blocks of `AiNpcNearPlayer`, `AiNpcScriptStep`, `AiNpcPathPick` were checked against their anchored instructions (the finding's prose agrees). `WalkPtCmd` is `MonAiWalkToPointCmd`. The `home` chain's quest words: `0x0059B6E0` reads quest 11's bytes `+0x0F` and `+0x10`, `0x005BAD20` quest 18's first byte, `0x005B9CA0` quest 17's `+0x06`, its point at `+0x10`. Stock path actions are 1–5. (fn:sub_005E7130_AiNpc@0x005E7130, fn:sub_005DEF30_MonAiWalkToPointCmd@0x005DEF30, data:g_NpcPathActions@0x00741D74, fn:sub_006660B0_PresetPathCopy@0x006660B0, tbl:MonStats.txt:interact)
- R32b. [C] Each function's map to its first command or boundary, and no further: `npc` 7 boundaries; `h6800`, `h6860`, `h6ae0` 13 (`cmp` 75, `arg` 69), `h7080` 5 (`le` 45, `arg` 226), `act1`–`act5`, `hp`, `hcb` (`cmp` 23), 240 cases each. `AiNearestPlayerCb` tests **the searcher's** class record: a reading from the candidate's separates all 32 cases that reach 0x00544590. (0x005DDEB6, run:2026-11-03-ai-cat-emu-12)
- R32c. [I] Row 32 has a fork in all 199 decisions of the rev 4 logs, so it does not count for the catalogue sample. (run:2026-11-04-ai-resume-flip)

- R32i. [C] As data: kind 0, no `init`, no `alt`; 35 records (35 records, as the index lists them); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R32l. [I] Logged, not compared: 1167 decisions (416 + 279 + 472) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R32r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 751 of its own think's decisions in the rev 4 and rev 6 logs, 591 resumed, 0 mismatches, 160 stopped, 1987 later calls matched, an unknown value deciding 766 of 2147 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R41. Row 41 `Towner` (fn:sub_005E7540_AiTowner@0x005E7540)

`AiNpcSaveHome`, `AiNpcScriptStep`, `AiNpcPathPick`, each ending the event on true, then `Idle(12)`: [row 32's chain](#r32-row-32-npc-fnsub_005e7130_ainpc0x005e7130) with no `AiNpcNearPlayer`. No `aip` read. [I] (fn:sub_005E7540_AiTowner@0x005E7540)

- R41a. [C] The chain to its first command: family `towner`, 240 cases, 17 boundaries, 72 with a draw; controls `le`, `cmp` fail the 15, 83 they separate. (run:2026-11-03-ai-cat-emu-12)

- R41i. [C] As data: kind 0, no `init`, no `alt`; 6 records (195-197 act2male..act2child, 203 act2guard1, 294 act3male, 296 act3female); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R41l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R42. Row 42 `Vendor` (fn:sub_005E9E00_AiVendor@0x005E9E00)

```
if D100() < 20: SetMode(8, 0, 0)                                           [I] (fn:sub_005E9E00_AiVendor@0x005E9E00)
else: Idle(30)
```

No `aip` read. [C] The whole map: family `vendor`, 240 cases, all drawing; control `le` fails the 62 it separates. (run:2026-11-03-ai-cat-emu-12)

- R42i. [C] As data: kind 0, no `init`, no `alt`; 2 records (204-205 act2vendor1..act2vendor2); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R42l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R54. Row 54 `NpcStationary` (fn:sub_005E73A0_AiNpcStationary@0x005E73A0)

No `aip` slot read.

```
1. p ← AiNearestPlayer(&f)                                                 [I] (0x005E73A0, 0x005E7533)
2. if p ≠ 0 and p ≠ U:
     n ← AiDistUnits(U, p)
     if p is a player and PlayerIsBusy(p) = 1: Idle(10); return
     if NpcInteractAny(L): Idle(10); return                ; L when U is a monster with its data
     if n < 24:
       if v18 = 0: v18 ← 60;  a player p: UnitSetEvent(U, 18, p)
       else: v18 ← v18 − 1
     else:
       if v18 ≤ 0: v18 ← 60
       v18 ← v18 − 1
     Idle(20); return
3. class 251: if 0x0059DF50 ≠ 0 and AiNpcMode0IfFree = 1: SetMode(0, 0, 0);  0x0059C750; return
   class 406: if 0x005B43F0 ≠ 0 and AiNpcMode0IfFree = 1: SetMode(0, 0, 0);  0x005B4440; return
4. Idle(20)
```

- R54a. [I] No draw. The block was checked against its anchored instructions (the finding's prose agrees). `AiNpcMode0IfFree` does its own `SetMode(0, 0, 0)`. Its first call cannot fail: 0 of 3 sites, so the row does not count for the catalogue sample. (fn:sub_005E73A0_AiNpcStationary@0x005E73A0, fn:sub_005E7350_AiNpcMode0IfFree@0x005E7350, run:2026-11-04-ai-resume-flip)
- R54b. [C] The map to its first call, `nstat`, 4 boundaries, and `AiNpcMode0IfFree`'s, `h7350`, 240 cases each; no control separates them. (run:2026-11-03-ai-cat-emu-12)

- R54i. [C] As data: kind 0, no `init`, no `alt`; 4 records (251 tyrael1, 367 tyrael2, 406 izualghost, 521 tyrael3); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R54l. [I] Logged, not compared: 489 decisions (187 + 125 + 177) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R54r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 302 of its own think's decisions in the rev 4 and rev 6 logs, 302 resumed, 0 mismatches, 0 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R58. Row 58 `Navi` (fn:sub_005E7E20_AiNavi@0x005E7E20)

No `aip` slot read.

```
1. if NpcInteractAny(L): Idle(10); return                                  [I] (0x005E7E20, 0x005E7F3F)
2. p ← AiNearestPlayer(&f)
3. if p ≠ 0, p is a player, not busy, Range(3) ≠ 0 and f ≠ 0:              ; draw only past the first three
     if v18 = 0: v18 ← 60;  UnitSetEvent(U, 18, p)
     else if v18 < 0: v18 ← 0
     else if v18 > 0: v18 ← v18 − 1
     Idle(20); return
4. u ← FindHostile(&dist, &melee)
5. if u ≠ 0 and dist < 25: SetModeAtUnit(4, u); return
6. Idle(50)
```

- R58a. [I] The block was checked against its anchored instructions (the finding's prose agrees). (fn:sub_005E7E20_AiNavi@0x005E7E20, fn:sub_005DDC30_MonAiFindHostile@0x005DDC30)
- R58b. [C] The map to its first boundary, 3 reached: family `navi`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-12)

- R58i. [C] As data: kind 0, no `init`, no `alt`; 1 records (266 navi); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R58l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R60. Row 60 `GoodNpcRanged` (fn:sub_005E7AC0_AiGoodNpcRanged@0x005E7AC0)

Alias of [state row 5](#s5-state-row-5-fnsub_005e7ac0_aigoodnpcranged0x005e7ac0): the same think word. No `aip`; `rogue2` is its one record. [I] (fn:sub_005E7AC0_AiGoodNpcRanged@0x005E7AC0)

- R60i. [C] As data: kind 0, no `init`, no `alt`; 1 records (270 rogue2); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R60l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R62. Row 62 `TownRogue` (fn:sub_005E7D60_AiTownRogue@0x005E7D60)

No `aip` slot read.

```
u ← FindHostile(&dist, &melee)             ; seeded with the context's words     [I] (fn:sub_005E7D60_AiTownRogue@0x005E7D60)
if u ≠ 0 and dist < 25 (signed): SetModeAtUnit(4, u)
else: Idle(50)
```

No draw. [State 8](#s8-state-row-8-fnsub_005e7dc0_aist80x005e7dc0) has the same 91 bytes but the low bytes of three call displacements. [C] The entry's first call only: family `trogue`, 240 cases. (run:2026-11-03-ai-cat-emu-12)

- R62i. [C] As data: kind 1, no `init`, no `alt`; 1 records (272 rogue3); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R62l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R81. Row 81 `JarJar` (fn:sub_005E7590_AiJarJar@0x005E7590)

No `aip` slot read.

```
1. AiNpcSaveHome                                       ; its result is not read      [I] (0x005E7590, 0x005E7798)
2. if 0x0059B8B0 = 0:
     p ← home;  f ← not 0x0059B8F0(&p)
     if home+0x18 < T and T − home+0x18 < 200: Idle(20); return
     if the distance to p > 1: WalkPt(p);  home+0x18 ← T; return
     if not f: Idle(20); return
     if AiNpcNearPlayer: home+0x18 ← T
     else: Idle(20)
     return
3. if no home: Idle(120); return
4. q ← AiNearestPlayer(&f);  n ← AiDistUnits(U, q)
5. if (0x0059AEC0 ≠ 0 and the distance to home > 2) or the distance to home > 7:
     WalkPt(home.x, home.y − 3); return
6. if AiNpcNearPlayer or q = 0 or q = U: Idle(120); return
7. if q is a player:
     if n < 12:
       if Range(1000) < 100: WanderNearUnit(q, 2)
       Idle(200); return
     Idle(20)
8. if Range(1000) < 50: Ring(3)
9. Idle(120)
```

- R81a. [I] The block was checked against its anchored instructions (the finding's prose agrees). At step 7 past `Idle(20)`, step 8 draws too, and both idles are queued. (fn:sub_005E7590_AiJarJar@0x005E7590)
- R81b. [C] The map to its first boundary, 2 reached: family `jarjar`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-12)

- R81i. [C] As data: kind 0, no `init`, no `alt`; 1 records (331 act2guard2); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R81l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R88. Row 88 `7TIllusion` (fn:sub_005EA080_Ai7TIllusion@0x005EA080)

No `aip` slot read.

```
if v18 = 1: U+0xC4 ← U+0xC4 | 0x20000;  SetMode(0, 0, 0)                   [I] (fn:sub_005EA080_Ai7TIllusion@0x005EA080)
else: SetMode(4, X − 10, Y);  v18 ← 1
```

No draw. [C] Both boundaries: family `illus`, 240 cases; no control separates it. (run:2026-11-03-ai-cat-emu-12)

- R88i. [C] As data: kind 1, no `init`, no `alt`; 1 records (355 seventombs); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R88l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R91. Row 91 `DarkWanderer` (fn:sub_005EA130_AiDarkWanderer@0x005EA130)

No `aip` slot read.

```
1. if A3Q7_WalkTarget(&p) = 0: Idle(10); return                            [I] (0x005EA130, 0x005EA260)
2. if v14 = 0: v14 ← 1;  v18 ← 0;  v1C ← 0
3. if t = 0: Idle(10); return
4. if dist ≥ 20: Idle(40); return
5. v14 = 1: WalkPt(p);  v14 ← 2; return
6. v14 = 2:
     if AiPathDistToPoint(U, p) < 2 (unsigned) or v18 ≥ 3:
       U+0xC4 ← U+0xC4 | 0x20000;  SetMode(0, 0, 0);  A3Q7_TimerStart; return
     v18 ← v18 + 1;  Ovr(1, 0, 0);  WalkPt(p); return
7. other v14: Idle(40)
```

- R91a. [I] No draw. The block was checked against its anchored instructions (the finding's prose agrees). (fn:sub_005EA130_AiDarkWanderer@0x005EA130, fn:sub_005BD0D0_A3Q7_WalkTarget@0x005BD0D0, fn:sub_005BD4A0_A3Q7_TimerStart@0x005BD4A0)
- R91b. [C] The first call only: family `dark`, 240 cases. (run:2026-11-03-ai-cat-emu-12)

- R91i. [C] As data: kind 1, no `init`, no `alt`; 1 records (368 darkwanderer); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R91l. [I] Not logged: no decision of this row in any of the three kept batches. Everything above is the code reading of its finding. (0x005B186F)

#### R99. Row 99 `TrappedSoul` (fn:sub_005E9F10_AiTrappedSoul@0x005E9F10)

No `aip` slot read.

```
1. U+0xC4 ← U+0xC4 | 0x20000                       ; every event             [I] (0x005E9F10, 0x005EA078)
2. if t = 0 or dist ≥ 5:
     if v14 ≠ 0: SetModeAtUnit(8, t)               ; t may be null
     else: Idle(15)
     return
3. if v14 = 0: v14 ← 1;  v18 ← T;  SetModeAtUnit(9, t); return
4. if not melee or T ≤ v18: SetModeAtUnit(8, t); return
5. by position, unsigned (UnitGetPos):
     Ux ≥ Tx and Uy ≤ Ty: SetModeAtUnit(4, t);  v18 ← T + 35
     else Ux > Tx or Uy < Ty: SetModeAtUnit(8, t);  v18 ← T + 5
     else: SetModeAtUnit(5, t);  v18 ← T + 35
```

- R99a. [I] No draw. The block was checked against its anchored instructions (the finding's prose agrees). (fn:sub_005E9F10_AiTrappedSoul@0x005E9F10, fn:sub_00620870_UnitGetPos@0x00620870)
- R99b. [C] The map to its first boundary, 7 reached: family `soul`, 240 cases; control `cmp` fails the 26 it separates, `dist < 5` met at equality 20 times. No call past the first in its logs, so the row does not count for the catalogue sample. (run:2026-11-03-ai-cat-emu-12, run:2026-11-04-ai-resume-flip)

- R99i. [C] As data: kind 1, no `init`, no `alt`; 2 records (403-404 trappedsoul1..trappedsoul2); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R99l. [I] Logged, not compared: 468 decisions (243 + 25 + 200) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, run:2026-11-04-ai-r5, 0x005B186F)
- R99r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 225 of its own think's decisions in the rev 4 and rev 6 logs, 225 resumed, 0 mismatches, 0 stopped, 0 later calls matched, an unknown value deciding 0 of 0 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

#### R100. Row 100 `Buffy` (fn:sub_005E7F50_AiBuffy@0x005E7F50)

```
if U has a room: Idle(200)                                                 [I] (fn:sub_005E7F50_AiBuffy@0x005E7F50)
```

Stub: no draw, no `aip`; with no room, a return. [C] Both boundaries: family `buffy`, 240 cases. 4 resumed decisions do not count for the catalogue sample. (run:2026-11-03-ai-cat-emu-12)

- R100i. [C] As data: kind 0, no `init`, no `alt`; 1 records (408 malachai); reach ·; `aip` set —; `aidel` 15/15/15; skills —. (data:g_MonAiTable@0x0073CA18, tbl:MonStats.txt:AI, [MonAI § The index](../../../tables/MonAI.md#the-index))
- R100l. [I] Logged, not compared: 16 decisions (12 + 4) in a row with no model, so the first boundary of this row is not raised. (run:2026-11-03-ai, run:2026-11-03-ai-3, 0x005B186F)
- R100r. [I] Past the first boundary, a consistency check only ([README H2](README.md#h-past-the-first-boundary)): 4 of its own think's decisions in the rev 4 and rev 6 logs, 4 resumed, 0 mismatches, 0 stopped, 4 later calls matched, an unknown value deciding 0 of 4 later steps. The row is not under sentence H1. (run:2026-11-04-ai-resume)

#### S2. State row 2 (fn:sub_005B14E0_AiSt2WanderNearTarget@0x005B14E0)

No setter passes 2: [S17's note](#s17-state-row-17-fnsub_005e8020_aist100x005e8020). Both draws are the low byte of a step, not mod 100.

```
1. if St3or19 or dist < 4: MonAiInit(ctl, 0);  Idle(10); return            [I] (fn:sub_005B14E0_AiSt2WanderNearTarget@0x005B14E0)
2. if dist > 10 and v14 = 0: v14 ← 1;  WanderNearUnit(t, 12); return
3. if step's low byte < 0x4D: Ring(4); return                              ; unsigned
4. if a second step's low byte < 0x1A: v14 ← 0
5. Idle(10)
```

- S2a. [C] The map to its 4 boundaries: family `st2`, 240 cases, 73 drawing; controls `le`, `cmp`, `lo8` fail the 13, 16, 47 they separate. (run:2026-11-03-ai-cat-emu-12)

- S2i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S3. State row 3 (fn:sub_005E5870_AiSt3GroupRoam@0x005E5870)

No setter passes 3: [S17's note](#s17-state-row-17-fnsub_005e8020_aist100x005e8020). Kind 8 is the head record's `+0x08`.

```
init (0x005E5730):                                                         [I] (0x005E5730, 0x005E5870)
  o ← MonsterOwner(U);  o = 0 is fatal (line 0xE17)
  v14 ← X − o's x;  v18 ← Y − o's y
  if o = U: v1C ← D100()                                                   ; one step

think:                                                                     [I] (0x005E5870, 0x005E5ABA)
1. if the parameter head has kind 8: 0x0058F160;  MonAiInit(ctl, 0);  Idle(10); return
2. MonGroupForEach(U, &f, AiGroupDeadCb)
3. if f or St3or19: MonHelpBlock kind 8;  0x0058F160;  MonAiInit(ctl, 0);  Idle(10); return
4. if MonsterOwner(U) ≠ U:                                                 ; not the leader
     if no head: Idle(15); return
     (x, y) ← (head.x + v14, head.y + v18);  Pop;  WalkPt(x, y); return
5. if D100() < 30: Idle(10); return
6. v ← v1C + 1, 0 at 100 or more
   r ← Range(10)
   if RNG_RangePow2(2) ≠ 0: r ← −r                                         ; one per branch below, same draw order
   v < 25: (x, y) ← (X + r, Y − 5)
   v < 50: (X + 5, Y + r)
   v < 75: (X + r, Y + 5)
   else:   (X − 5, Y + r)
7. if MonAiWalkToPointOrStop(x, y): MonHelpBlock kind 2 with the point;  v1C ← v
   else: v1C ← v + 25
```

- S3a. [I] The block was checked against its anchored instructions (the finding's prose agrees). (fn:sub_005E5730_AiSt3Init@0x005E5730, fn:sub_005E5870_AiSt3GroupRoam@0x005E5870, fn:sub_005E5710_AiGroupDeadCb@0x005E5710, fn:sub_0058F730_MonHelpBlock@0x0058F730)
- S3b. [C] The init's map, 98 drawing, and the think's to its first boundary: families `st3i`, `st3`, `h5710`, 240 cases each; no control separates them. (run:2026-11-03-ai-cat-emu-12)

- S3i. [C] As data: kind 1, `init` 0x005E5730, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S8. State row 8 (fn:sub_005E7DC0_AiSt8@0x005E7DC0)

[Row 62's code](#r62-row-62-townrogue-fnsub_005e7d60_aitownrogue0x005e7d60), 91 bytes equal but the low bytes of three call displacements: `FindHostile`, a unit under 25: `SetModeAtUnit(4, u)`, else `Idle(50)`. No setter passes 8: [S17's note](#s17-state-row-17-fnsub_005e8020_aist100x005e8020). [I] (fn:sub_005E7DC0_AiSt8@0x005E7DC0) [C] The first call only: family `st8`, 240 cases. (run:2026-11-03-ai-cat-emu-12)

- S8i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S9. State row 9 (fn:sub_005E7F80_AiSt9@0x005E7F80)

No setter passes 9: [S17's note](#s17-state-row-17-fnsub_005e8020_aist100x005e8020).

```
1. if the parameter head has kind 8: 0x0058F160;  MonAiInit(ctl, 0)        [I] (fn:sub_005E7F80_AiSt9@0x005E7F80, fn:sub_0058F730_MonHelpBlock@0x0058F730)
2. else:
     MonGroupForEach(U, &f, AiGroupDeadCb)
     if St3or19 or f or dist < 20: MonHelpBlock kind 8;  0x0058F160;  MonAiInit(ctl, 0)
3. Idle(10)
```

No draw. [C] The map to its first boundary, 2 reached: family `st9`, 240 cases. (run:2026-11-03-ai-cat-emu-12)

- S9i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S10. State row 10 (fn:sub_005E8020_AiSt10@0x005E8020)

The think of states 10 and 17, which differ by search kind only (1 and 2). Setters: `CloakAreaCb`, and `CurseSetAiState` for `auratargetstate` 23.

```
1. if melee and not (U's class in range with interact set) and MonModeAllowed(class, 4):   [I] (fn:sub_005E8020_AiSt10@0x005E8020, fn:sub_005D6520_CloakAreaCb@0x005D6520, fn:sub_005C34B0_CurseSetAiState@0x005C34B0)
     SetModeAtUnit(4, t); return
2. if D100() < 20: Ring(3)
   else: Idle(10)
```

- S10a. [C] The map to its 3 boundaries: family `st10`, 240 cases, 152 drawing; control `le` fails the 41 it separates. (run:2026-11-03-ai-cat-emu-12)
- S10r. [I] Own decisions at the think 0x005E8020, in the rows of classes that entered it, a consistency check only: 632 in the rev 4 and rev 6 logs, 632 resumed, 0 mismatches, 0 stopped, 632 calls matched, none past the first. The logs do not split 10 from 17; state control saw state 10 live and 17 not. Not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

- S10i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S11. State row 11 (fn:sub_005E8140_AiSt11@0x005E8140)

Setters: `MonFleeFrom`, and `CurseSetAiState` for `auratargetstate` 56. No draw in the function.

```
init (0x005E80E0):                                                         [I] (0x005E80E0, 0x005E8140)
  g ← UNIT_GetTargetUnit(U)
  g of type 0, 1 or 3: MonForcedTargetSet(U, kind 1, 2 or 4, g's id)

think:                                                                     [I] (0x005E8140, 0x005E8340)
1. if U lacks state 56:
     MonAiInit(ctl, 0);  CancelEvents(2, 0);  UnitQueueEvent(U, 2, T + 1, 0, 0)
2. if dist > (v14 ≠ 0 ? v14 : 30): Idle(10); return
3. p: i32 ← 0
   if Velocity > 0 (i16): q ← Run·100 ÷ Velocity (i32, truncating);  if q ≥ 100: p ← min(q − 100, 120)
4. if v1C = 0:
     v1C ← 1;  MonForcedTargetClear;  CancelEvents(2, 0);  Ovr(2, p, 0)
     MonModeAllowed(class, 15) ? MonAiStepAwayXY(t, 30, 0) : MonAiStepAway(t, 30, 0); return
5. if melee and not MONSTATS_FlagTest(class, 9) and mode 4 allowed: SetModeAtUnit(4, t); return
6. Ovr(2, p, 0)
   the same step away with flag 1;  on 0: Ring(6)
```

- S11a. [I] `Velocity` is loaded u16 but tested as i16, and `Run·100` cannot wrap. Stock `Velocity` 0..15 and `Run` 0..20 tell no widths apart. (0x005E81DA, 0x005E81EE, fn:sub_005E8140_AiSt11@0x005E8140, fn:sub_00573090_MonForcedTargetSet@0x00573090, fn:sub_005DDD00_MonFleeFrom@0x005DDD00, tbl:MonStats.txt:Velocity, tbl:MonStats.txt:Run)
- S11b. [C] The init's map and the think's first call (0x005E816F) only: families `st11i`, `st11`, 240 cases each. (run:2026-11-03-ai-cat-emu-12)
- S11r. [I] Own decisions at 0x005E8140, a consistency check only: 134 in the rev 4 and rev 6 logs, 134 resumed, 0 mismatches, 0 stopped, 394 calls matched, 260 past the first, an unknown value deciding 68 of those 260. Not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

- S11i. [C] As data: kind 1, `init` 0x005E80E0, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S12. State row 12 (fn:sub_005E8340_AiSt12@0x005E8340)

Setter: `CurseSetAiState` for `auratargetstate` 27.

```
1. t' ← UNIT_GetTargetUnit(U)                                              [I] (0x005E8340, 0x005E8476)
2. if t' = 0 or its room is a town:
     MonAiInit(ctl, 0);  CancelEvents(2, 0);  UnitQueueEvent(U, 2, T + 1, 0, 0); return
3. if v14 = 0: v14 ← 1;  MonAiWalkToUnitType13(t', 7); return
4. if InMeleeRange(U, t', 0): SetModeAtUnit(4, t'); return
5. u ← MonAiTargetOrIdle(ctl, &d, &m)
   if u ≠ 0 and m: v14 ← 0;  SetModeAtUnit(4, u); return
6. v14 ← 1;  UnitSetPathTargetUnit(U, t');  MonAiWalkToUnitType13(t', 7)
```

- S12a. [I] No draw. The block was checked against its anchored instructions (the finding's prose agrees). (fn:sub_005E8340_AiSt12@0x005E8340, fn:sub_005DE890_MonAiTargetOrIdle@0x005DE890)
- S12b. [C] The first call only: family `st12`, 240 cases. (run:2026-11-03-ai-cat-emu-12)
- S12r. [I] Own decisions at 0x005E8340, a consistency check only: 56 in the rev 4 and rev 6 logs, 56 resumed, 0 mismatches, 0 stopped, 286 calls matched, 230 past the first, an unknown value deciding 0 of them. Not under sentence H1. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

- S12i. [C] As data: kind 0, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S13. State row 13 (fn:sub_005E5C50_AiSt13@0x005E5C50)

The Countess's state: set by `SuperUniqueSpawn` for SuperUniques `+0x08` 6. `aip`: 1 the run's chance out of melee; 2 the idle; 3 with 10 added, the chance of A1.

```
AiPathSkillStep (0x005E5B70), `Skill1` at the next DS1 path point:         [I] (fn:sub_005E5B70_AiPathSkillStep@0x005E5B70)
  if the list exists and v14 < count:
    if the class is out of range, no record, or Skill1 is outside 0 .. Skills count − 1: return 0
    MonAiUseSkill(4, Skill1, 0, x[v14], y[v14])      ; the mode pushed 4, not Sk1mode
    v14 ← v14 + 1;  v18 ← T;  return 1
  if |T − v18| > 700: v14 ← 0
  return 0

think:                                                                     [I] (0x005E5C50, 0x005E6012)
RunHome: AiPathOverrideSet(pathctl, 1, 0, 0);  if MonAiRunToPoint(home): end the event;  else CancelEvents(2, 0)
1. if M = 0 or no room: return
2. home: absent, pushed from X, Y;  a zero word: refilled from X or Y
3. if LogicRegionIdAt(home) ≠ LogicRegionIdAt(U): RunHome
4. if LogicRegionIdAt(t) ≠ LogicRegionIdAt(home):
     if U stands exactly at home:
       if dist < 25 and AiPathSkillStep: return
       Idle(10); return
     RunHome
5. if AiPathDistToPoint(U, home) > 40 (unsigned): RunHome
6. if AiPathSkillStep: return
7. r ← Range(100)
8. if melee:
     if r < aip(3) + 10: SetModeAtUnit(4, t)
     else: Idle(aip(2))
   else:
     if r < aip(1): Ovr(0, 100, 0);  MonAiRunToUnit(t)
     else: Idle(aip(2))
```

- S13a. [I] The block was checked against its anchored instructions (the finding's prose agrees). `CountessFirewall` runs along her preset's DS1 path, once per point, again after 700 frames. (fn:sub_005E5C50_AiSt13@0x005E5C50, tbl:MonStats.txt:aip1, tbl:MonStats.txt:Skill1, fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0)
- S13b. [C] The map to its first boundary, 3 reached, and `AiPathSkillStep`'s, 2: families `st13`, `h5b70`, 240 cases each; `h5b70`'s controls `cmp`, `u16` fail the 45, 7 they separate. (run:2026-11-03-ai-cat-emu-12)
- S13c. [I] Short by name: two Countess launches did not reach her, so the state has no logged decision; it is not called dead. (run:2026-11-04-ai-r5)

- S13i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S14. State row 14 (fn:sub_005E2610_AiSt14@0x005E2610)

No setter passes 14: [S17's note](#s17-state-row-17-fnsub_005e8020_aist100x005e8020).

```
if melee:                                                                  [I] (fn:sub_005E2610_AiSt14@0x005E2610)
  if D100() < 95: step();  SetModeAtUnit(5, t); return                     ; the second step's value unused
else:
  if D100() < 89: MonAiWalkToUnit(t, 0); return
Idle(10)
```

[C] The map to its 3 boundaries: family `st14`, 240 cases, all drawing; control `le` fails the 29 it separates. (run:2026-11-03-ai-cat-emu-12)

- S14i. [C] As data: kind 1, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

#### S17. State row 17 (fn:sub_005E8020_AiSt10@0x005E8020)

The same think as [state 10](#s10-state-row-10-fnsub_005e8020_aist100x005e8020), on search kind 2. [I] (fn:sub_005E8020_AiSt10@0x005E8020)

- S17a. [I] **No setter, states 2, 3, 8, 9, 14, 17:** no direct call of `MonAiInit` passes these values and every indirect source is resolved, a reading of the image's callers. [C] None appeared in the 21 sessions of run:2026-11-03-ai-3 over 7 539 decisions and 10 721 events, for that window only. State 10 was live in the same window, a control that the logger sees a state; the setter reading stays `[I]` and these states are not called dead. (fn:sub_005B0E00_MonAiInit@0x005B0E00, [ai/0013 § 3](../../../findings/ai/0013-batch12.md))
- S17r. [I] Own decisions: the 632 of [S10r](#s10-state-row-10-fnsub_005e8020_aist100x005e8020), not split by state, none of which state control tied to state 17. (run:2026-11-04-ai-resume, run:2026-11-04-ai-r5)

- S17i. [C] As data: kind 2, no `init`, no `alt`. (data:g_MonAiStateRows@0x0073D358, [MonAI § The second table](../../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review))

## Outputs

Per decision: the commands, mode changes and path requests the entry's block names, on the unit, and the seed advanced by its draws.

## Worked example

None of its own: the rows have no recorded seed-to-decision case outside the tier's. [Machinery § Worked example](machinery.md#worked-example) and [README § Worked example](README.md#worked-example) hold the tier's.

## Reimplementation notes

- [I] **A refused move can queue nothing.** A helper reaching `MonAiMove` with flag 2 clear (`Walk(t, 0)`, `Walk(t, 1)`, `StepAway(…)`) returns 0 on refusal, with no idle and no draw; flag 1 sets `AiCtl` flag `0x40`, which forces the next search's line test on. Only flag 2 adds the draw and the ring or the idle. ([machinery B6](machinery.md#b-the-command), fn:sub_005DEB60_MonAiMove@0x005DEB60)
- [I] **A slot may be read twice.** Row 7's second `aip(3)` draw is a new draw on the same slot. Each `chance` is one step. (0x005EFB80)
- [I] **Two life readers.** Row 11 calls `UnitLifePct`, rows 4, 8 and 15 `AiLifePct`. Keep them apart. (fn:sub_00621F20_UnitLifePct@0x00621F20, fn:sub_005DD280_AiLifePct@0x005DD280)

## Evidence

- [ai/0002](../../../findings/ai/0002-pool-a.md), [ai/0003](../../../findings/ai/0003-pool-b.md), [ai/0004](../../../findings/ai/0004-pool-c.md), [ai/0005](../../../findings/ai/0005-pool-d.md), [ai/0006](../../../findings/ai/0006-summons.md), [ai/0007](../../../findings/ai/0007-hirelings.md), [ai/0008](../../../findings/ai/0008-bosses-a.md), [ai/0009](../../../findings/ai/0009-batch8.md), [ai/0010](../../../findings/ai/0010-batch9.md): batches 1 to 9. [ai/0001](../../../findings/ai/0001-machinery.md): the rows 0 and 1 and the second table.
- [ai/0015](../../../findings/ai/0015-phase2-first-run.md), [ai/0017](../../../findings/ai/0017-phase2-second-run.md), [ai/0018](../../../findings/ai/0018-phase2-third-run.md): the three logged batches.
- [MonAI](../../../tables/MonAI.md), [MonStats](../../../tables/MonStats.md).

To check the count: every row has one heading `#### R<n>. Row <n> ` and every state row one heading `#### S<n>. State row <n> `: `grep -cE '^#### R[0-9]+\. Row ' docs/specs/monsters/ai/catalogue.md` gives 148 and `grep -cE '^#### S[0-9]+\. State row '` gives 18.

## Open questions

- [L] **Row 15's alt, the kind-14 record's `+0x18`:** no writer found; a direct store into a list record was not scanned. A scan or a log of the alt settles it. ([ai/0002](../../../findings/ai/0002-pool-a.md), fn:sub_005F1750_AiSandMaggotAlt@0x005F1750)
- [L] **Row 6's event 17, the `Unit+0xC4` bit `0x02` of the corpse callbacks** (rows 6, 13): what they show or mean is not read. ([ai/0002](../../../findings/ai/0002-pool-a.md))
- [L] **Row 25's dance:** the values of the four offset tables `A`, `B`, `A5`, `B5` (written on the stack at entry, 0x005F39E1–0x005F3E07; [the entry](../../../backlog/archive/2026-11-04-spec-writer-reverser-plan-0052-row-25-offset-tables.md)), and what unit event 12 on the player does at the grant's end. ([ai/0003](../../../findings/ai/0003-pool-b.md), fn:sub_005F39B0_AiWillOWisp@0x005F39B0)
- [L] **The killer of the self-kills** (rows 40, 46, 56): what `UnitKilled` does with it is not read, and a log of an egg hatching would settle whether its target is credited. ([ai/0004](../../../findings/ai/0004-pool-c.md), fn:sub_0057CCB0_UnitKilled@0x0057CCB0)
- [L] **The group calls of rows 65 and 75:** whether the shaman's reaches `Fetish` minions and the mother's `QuillRat` ones. The orders match those two readers; the group's class is not read from the spawn data. A log of a `fetishshaman` breath and of a `quillbear` in the 3-or-19 state settles it. ([ai/0005](../../../findings/ai/0005-pool-d.md), fn:sub_0058F730_MonHelpBlock@0x0058F730)
- [L] **Row 71's state 1:** tested but set by no code of the function; whether another path sets it, or the branch cannot be reached on stock data. ([ai/0005](../../../findings/ai/0005-pool-d.md), fn:sub_005FA710_AiRegurgitator@0x005FA710)
- [L] **Rows 73 and 74's gate on `MonsterData+0x0E < 4`:** classes 311 and 312 always pass; what the `dkmag1..3` records (classes 701, 702, 713) hold there is not read. **Rows 78 and 79:** whether any code but `MonRegionsBuild` writes the region's `+0x2D4`. ([ai/0005](../../../findings/ai/0005-pool-d.md), fn:sub_005FB650_AiTrapArrowKind@0x005FB650)
- [L] **The hydra's `v14`** (row 86): its writer, the summoning skill's do function or `SpawnOwnedMonster`, is not read. **Row 103** reads its owner with no null test: whether an owner-less inviso pet can reach an AI event is not read. **`0x005DE6F0`'s walk around the owner** (row 107), and the `0x00574F40` term of `AiPetGuard`'s distance, are named by their calls only. ([ai/0006](../../../findings/ai/0006-summons.md), fn:sub_005E9E60_AiHydra@0x005E9E60)
- [L] **The Shadow Master's scoring loop** (row 106 step 13): the finding gives the score's inputs and the shape, not each `aitype`'s terms and target; a reimplementation cannot pick the same skill without them ([the entry](../../../backlog/archive/2026-11-04-spec-writer-reverser-plan-0052-row-106-scoring-terms.md)). ([ai/0006](../../../findings/ai/0006-summons.md), fn:sub_005EB970_AiShadowMaster@0x005EB970)
- [L] **Row 44, Duriel: a community disagreement, open.** src:arreat-summit-boss-pages gives Duriel "17 % Melee Attack 1, 33 % Smite, 50 % Jab" and the same for Über Duriel; the code read (R44) gives Smite 33 %, Jab 33.5 %, A1 33.5 %. The map is emulated, the case is open for owner play, and agreement or disagreement promotes nothing. ([README Open questions](README.md#open-questions), fn:sub_005F67B0_AiDuriel@0x005F67B0, [ai/0014](../../../findings/ai/0014-community-cross-check.md), run:2026-10-30-ai-cat-emu-6)
- [L] **Community claims, per row, with their verdicts from [ai/0014 § 2](../../../findings/ai/0014-community-cross-check.md).** Leads only: agreement raises nothing in this catalogue, and a verdict compares a claim with the code reading the entry states, itself a code reading unless the entry says otherwise. C10 and C11's disagreement is the row 44 bullet above; C40's is [the overview's open question](README.md#open-questions).
- [L] **src:d2mods-monstats-guide, src:wue-d2-ai-slides:** [R20](#r20-row-20-scarab-fnsub_005f2540_aiscarab0x005f2540): C05 held: d2mods: a boss scarab orders a raid with a chance given by `aip5` of the Scarab AI; C06 held with refinement: d2mods: while raiding, scarabs always use SK1 instead of A1 and A2. [R122](#r122-row-122-imp-fnsub_005e2ff0_aiimp0x005e2ff0): C04 held: d2mods: the Imp AI "is special and uses multiple rows". the machinery: C01 held: d2mods: the `AI` column tells the game which AI to use; C02 held with refinement: d2mods: the `aip1`–`aip8` cells "pass on parameters (in percentage)"; C03 held with refinement: d2mods: most AIs "will do absolutely nothing" without aip values; C07 held with refinement: slides: the AI is strongly distance-driven (a range switches the behaviour); C08 held with refinement: slides: typical behaviour is a random choice of skill 1, 2 or 3; C09 held: slides: some AIs also use the monster's current life. ([ai/0014](../../../findings/ai/0014-community-cross-check.md))
- [L] **src:arreat-summit-boss-pages:** [R34](#r34-row-34-andariel-fnsub_005f5830_aiandariel0x005f5830): C14 held: Andariel: a deadly poison attack she casts when you get up close; C15 held: Lilith (Über Andariel): skills Poison Spray, Poison Bolt. [R44](#r44-row-44-duriel-fnsub_005f67b0_aiduriel0x005f67b0): C10 contradicted: Duriel: "17% chance of selecting Melee Attack 1", 33 % Smite, 50 % Jab; C11 contradicted: Über Duriel: the same 17/33/50 (Hell); C12 held: Duriel "does not use Charge"; C13 held: Duriel: Holy Freeze level 5 in Normal and Nightmare, 6 in Hell. [R50](#r50-row-50-mephisto-fnsub_005f78b0_aimephisto0x005f78b0): C16 held with refinement: Mephisto uses Lightning, Charged Bolt, Poison Nova, Skull Missile, Frost Nova, Blizzard. [R51](#r51-row-51-diablo-fnsub_005e9170_aidiablo0x005e9170): C17 held with refinement: Diablo: Fire Nova, Red Lightning Hose, Cold Touch, Fire Wall, Firestorm, Bone Prison, Charge, Taunt; C18 held: Diablo casts Bone Prison around your Town Portals; C19 held: Diablo casts Bone Prison on you and your hirelings. [R53](#r53-row-53-summoner-fnsub_005f85c0_aisummoner0x005f85c0): C26 held: The Summoner: Glacial Spike, Frost Nova, Fire Ball, Fire Wall, Weaken. [R55](#r55-row-55-izual-fnsub_005f89b0_aiizual0x005f89b0): C25 held: Izual uses Frost Nova. [R90](#r90-row-90-griswold-fnsub_005e5ac0_aigriswold0x005e5ac0): C27 not covered: Griswold curses with Amplify Damage if he can hit you. [R128](#r128-row-128-nihlathak-fnsub_005ee5d0_ainihlathak0x005ee5d0): C23 held: Nihlathak: Summon Minion, Minion Frenzy, Corpse Explosion, Arctic Blast, Teleport; C24 held: Nihlathak explodes the corpses of your minions. [R135](#r135-row-135-baalcrab-fnsub_005fcfe0_aibaalcrab0x005fcfe0): C20 held: Baal can teleport; C21 held with refinement: Baal's clone is created with the same percentage of life as Baal; C22 held: Baal and the Succubus cast Defense Curse on a target with more Life than Mana, Blood Mana otherwise (page: "if you have more Life than Mana … Defense; Blood Mana only affects you if you have more Mana than Life"). [R145](#r145-row-145-uberbaal-fnsub_005fd200_aiuberbaal0x005fd200): C30 not covered: Über Baal summons Specters and Dark Lords; Vile Effigy follows Hoarfrost. [R146](#r146-row-146-ubermephisto-fnsub_005f81c0_aiubermephisto0x005f81c0): C29 not covered: Über Mephisto summons Returned, Horror Archers, Burning Dead and Horror Mages, Bone Mages. [R147](#r147-row-147-uberdiablo-fnsub_005e9df0_aiuberdiablo0x005e9df0): C28 not covered: Über Diablo "can summon Pit Lords", regenerates at twice the rate. ([ai/0014](../../../findings/ai/0014-community-cross-check.md))
- [L] **src:arreat-summit-bestiary:** [R6](#r6-row-6-fallen-fnsub_005f02c0_aifallen0x005f02c0): C31 held with refinement: Fallen "quickly retreat at the sight of one of their brethren falling"; C32 held with refinement: Fallen "may run away" (a chance). [R8](#r8-row-8-sandraider-fnsub_005f0700_aisandraider0x005f0700): C58 held: Sand Raiders have a Fire Hit attack like Enchant. [R13](#r13-row-13-fallenshaman-fnsub_005f1440_aifallenshaman0x005f1440): C33 held: Fallen Shamans raise Fallen; C34 held with refinement: Fallen Shamans shoot Firebolts. [R22](#r22-row-22-greatermummy-fnsub_005f2b10_aigreatermummy0x005f2b10): C38 held: Greater Mummy raises and heals other undead; C39 held with refinement: ... with Unique monsters an exception; C40 contradicted: ... with Champion monsters an exception; C41 held with refinement: Greater Mummy: Unholy Bolts from a distance, a poison breath close in. [R23](#r23-row-23-vulture-fnsub_005f3170_aivulture0x005f3170): C57 held with refinement: Vulture Demons must land to attack. [R28](#r28-row-28-vampire-fnsub_005f4a70_aivampire0x005f4a70): C42 held: Vampire: Life Steal Missile, Fireball, Fire Wall, Meteor. [R30](#r30-row-30-fetish-fnsub_005f53e0_aifetish0x005f53e0): C35 held: Fetishes use hit-and-run tactics. [R49](#r49-row-49-zakarumpriest-fnsub_005f72d0_aizakarumpriest0x005f72d0): C53 held with refinement: Zakarum Priests heal other monsters / wounded followers; C54 held: Zakarum Priest skills: Lightning, Heal, Teleport, Blizzard. [R65](#r65-row-65-fetishshaman-fnsub_005f9a80_aifetishshaman0x005f9a80): C36 held: Fetish Shamans revive their fallen kin; C37 held with refinement: Fetish Shaman skills: Resurrect, Inferno, Fetish Aura. [R68](#r68-row-68-vilemother-fnsub_005fa010_aivilemother0x005fa010): C52 held: Vile Mothers spawn offspring. [R71](#r71-row-71-regurgitator-fnsub_005fa710_airegurgitator0x005fa710): C51 held: Regurgitators walk to corpses to eat them. [R73](#r73-row-73-abyssknight-fnsub_005fab80_aiabyssknight0x005fab80): C56 held: Abyss Knights can use Bone Armor. [R74](#r74-row-74-oblivionknight-fnsub_005faf00_aioblivionknight0x005faf00): C55 held with refinement: Oblivion Knight: Bestow, Bone Armor, Bone Spirit, Decrepify, Lower Resist, Weaken, Life Tap, Amplify Damage. [R89](#r89-row-89-megademon-fnsub_005e0c80_aimegademon0x005e0c80): C50 held with refinement: Megademon: an Inferno-like attack it may use within melee range. [R118](#r118-row-118-succubus-fnsub_005e1e00_aisuccubus0x005e1e00): C43 held: Succubus: Defense Curse when you have more Life than Mana, Blood Mana when you have at least as much Mana as Life; C44 held with refinement: Succubi weaken from a distance with a curse, then close in. [R120](#r120-row-120-overseer-fnsub_005e27a0_aioverseer0x005e27a0): C45 held: Overseer's whip throws a minion into bloodlust, it mutates, charges and dies in an explosion; C46 held: Overseer creates a healing vortex that seeks damaged minions; C47 held: Overseer: Cry Help (Attract); C48 held with refinement: Overseer skills: Cry Help, Healing Vortex, Minion Frenzy, Smite. [R125](#r125-row-125-bloodlord-fnsub_005e36f0_aibloodlord0x005e36f0): C49 held: Blood Lord: Frenzy, strictly melee. ([ai/0014](../../../findings/ai/0014-community-cross-check.md))
- [L] **src:arreat-summit-summon-skills, src:arreat-summit-hirelings:** [R61](#r61-row-61-hireable-fnsub_005e52d0_aihireable0x005e52d0): C64 held: The Hireling follows you and automatically attacks monsters nearby; C65 held with refinement: A stuck hireling is brought to your side by a waypoint, portal or level change; C66 held: You cannot choose the hireling's spells; the set depends on the type; C67 held with refinement: Hirelings "fight to the death"; no retreat described. [R67](#r67-row-67-necropet-fnsub_005e4cf0_ainecropet0x005e4cf0): C59 held: Minions "may warp in around you if you get too far away"; C60 not covered: Minions "may disappear or no longer be under your power" when far; C61 held: Revived monsters "retain much of their original thoughts and tendencies". the machinery: C62 held with refinement: Wolves and the Grizzly draw monsters' attention from the Druid; C63 not covered: A Grizzly makes monsters target the Druid more than three Dire Wolves do. ([ai/0014](../../../findings/ai/0014-community-cross-check.md))
- [L] **Rows 145, 146, 147:** what moves and casts Uber Baal, Uber Mephisto and Uber Diablo, given thinks that command nothing. A scan for classes 704, 705, 709 and the state 184 outside the AI table is open beyond ai/0016. ([ai/0016](../../../findings/ai/0016-uber-event.md), fn:sub_005F81C0_AiUberMephisto@0x005F81C0)
- [L] **Row 83, kind 0:** what `dist` and `t` its context holds when no search ran, so whether `dist ≤ aip(2)` can fail on stock events. **Row 85:** whether `AiUnitSearch` passes the searcher to `AiPriestHealCb`, which does not exclude it. ([ai/0009](../../../findings/ai/0009-batch8.md), fn:sub_005E0260_AiMosquitoNest@0x005E0260)
- [L] **Row 94's two tables** at 0x006E33E0 and 0x006E33A0 are not transcribed in the finding; a reimplementation needs them ([the entry](../../../backlog/archive/2026-11-04-spec-writer-reverser-plan-0052-row-94-tables.md)). ([ai/0009](../../../findings/ai/0009-batch8.md), fn:sub_005E0980_AiDesertTurret@0x005E0980)
- [L] **Row 116:** who posts its kind-1 records, and with which expiry. **State 16:** whether any writer sets `v1C` non-zero, which would make its two discarded draws happen. **Row 122:** the far band below the near band makes the second missile test dead for the stock records; whether `R4.aip(3) > dist ≥ R3.aip(3)` was meant cannot be read from the code. ([ai/0010](../../../findings/ai/0010-batch9.md), fn:sub_005E2FF0_AiImp@0x005E2FF0)
