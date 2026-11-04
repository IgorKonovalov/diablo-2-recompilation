# 0004 — Per-event reproduction of `PathPlan`: 13 893 server plans of 21 sessions against the models, the spiral's truncation, the seed after a type-10 plan, the grid tie

> **Subsystem:** path/search
> **Question:** when the game calls `sub_00649970_PathPlan` for one of its own server units, does the request's return, the points it leaves in the
> path record and the unit's exit seed equal what the planners of [path/0001](0001-pathplan-register.md), [path/0002](0002-search.md) and
> [path/0003](0003-short-planners.md) give from the live grids of the rooms around the unit; which types does the game's own play reach; and is
> the grid the planners read the built map plus the unit marks?
> **Date:** 2026-11-04   **Plan:** 0054 (Phase 2, first lane run)   **Status:** for review (`lane/p54`)

Harness work on slot 1 under gdb (no Ghidra). The logger is `tools/gdb/path.gdb` (`tools/gdb/pilot.py` + `tools/gdb/path.py`), the sessions
`tools/path_sessions.py`, the check `tools/path.py` with its no-game tests `tools/test_path.py` (12 tests). The run record, setup and the
boundary of every "0 mismatches" below are in [experiments.md](experiments.md) § run:2026-11-04-path; kept outputs under
`workspace/logs/path/` (manifest `manifest-2026-11-04-path.sha256`, 53 lines, passes from that directory; development logs in `dev/`
with `manifest-dev.sha256`, 51 lines). Tool revisions: commits `a501a7fa` (logger rev 3) and `178106ec` (rev 4, checker).

## Answer (summary)

- [C] **0 mismatches over 13 893 plans** (13 265 reached a planner or a straight type, 628 were refused before one) in 21 fresh-process
  sessions on a town (Act IV), outdoor levels (Stony Field, Far Oasis, Flayer Jungle, River of Flame, Glacial Trail) and maze levels (Jail 1,
  Halls of the Dead 2), in Acts 1 to 5: the return, the first `EAX` points of the record and the exit seed equal the model's, for the types
  2, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15 and the planners they reach. The boundary is the `Conclusion` of the run record: nothing else of the record is compared; type 0, type 1 and
  types 3, 11, 12, 16 had no server plan. (run:2026-11-04-path, 0x00649970, 0x00649BAE)
- [C] **The floors:** 2 000 plans in all (13 893), and per type 100: 2 (162), 4 (2 740), 7 (2 894), 8 (282), 10 (698), 13 (4 078), 15 (1 580); 30: 5
  (696), 6 (655), 9 (54), 14 (54, of which 44 on natural inputs and 10 on the probe's). **Short: type 1 with 0 plans** (floor 100). Type 0 had no plan
  (no floor). Callers by `ra`: all 13 893 are call sites of the register of path/0001 § 11 (`PathPlan` callers 0x0057F11C player, 0x005A62F4 and
  0x005D0118 mode machine / skill, 0x006503CE and 0x006503E2 `PathReplan`, 0x0059FDB6 the missile creation, 0x005DA00C the Leap, 0x005A7859 the monster knockback). (`2026-11-04-path-check.txt`)
- [C] **Types 3, 11, 12 and 16 were not requested by server code in 21 sessions:** the break lines on the planners of 3 and 12 and on the two
  type-16 functions fired 0 times on either side; type 11's fired 229 times, all with a client caller (`side=cli`), and the control on a reached
  planner (greedy, 0x00679C80) fired 2 100 times server side and 2 100 client side in the same sessions. A server-caller hit on a watched function: 0.
  (`BREAK LINES`; 0x00679FD0, 0x00679C80)
- [C] **The spiral truncates.** With the start's fraction set by the probe so that a product that truncates and one that rounds land on opposite
  sides of a subtile boundary (10 plans, 6 + 4), the game's point list equals the truncating model in 10 of 10 and the rounding model in 0
  of 10. The 44 natural spiral plans do not separate the readings (their products never straddle a boundary). The emulator's rounding `FISTP` was
  the emulator's, not the game's (path/0003 § 9). (`SPIRAL`, 0x0067A1A1, 0x0067A1CA)
- [C] **No later draw on a type-10 missile's own seed within its life:** of 70 watched seeds (hardware watchpoint on the low dword after the plan),
  none was written again by a draw before the unit's memory was released (the low dword then overwritten, the high dword as at the exit); the same
  mechanism saw 8 of 14 control draws on monster seeds after type-13 plans as the LCG step (§ 5). So the exit seed of `PathPlanRandomWalk` (698 of 698
  reproduced, `+0x91 >> 1` draws each) is the seed the missile keeps; "chained to the next event" has no draw to chain to for these missiles. **Short** of the plan's
  floor in that reading. (run:2026-11-04-path)
- [I] **The tie of the grid is not exact.** The live cells equal the built map plus the unit list's marks in 55 of 9 773 plans (100 with the corpse
  reading); in the first 10 plans of each session (210 plans, 1 890 rooms, 1 260 exact) the only residual is `0x400`: the model marks cells of
  object classes that live cells do not carry (§ 7). The checks of this run read the LIVE cells, so the residual does not enter them. (run:2026-11-04-path)
- [I] **Tail of `PathPlan`:** the model of the aim and the "every point at the position" refusal (path/0001 § 6) agrees in all 13 265 plans that reached a planner or a
  straight type; in 72 of the 9 773 plans with a planner call the planner's count was non-zero and the game returned 0 after the aim, as the model did. It stays `[I]` (the aim's writes
  are not compared). (run:2026-11-04-path)

## Leads used

No community source was compared (Phase 1b's). Located and read: [path/0001](0001-pathplan-register.md) §§ 1, 6, 13 (the log design), [path/0002](0002-search.md),
[path/0003](0003-short-planners.md) (the models), [drlg/0005](../drlg/0005-collision.md) § 6 (the u16 word, the corpse and item marks), [ai/0001](../ai/0001-machinery.md) § 8 (which AI rows
request which types; the sources of 2 and 1).

## Functions

| Address | Name | Scope of this run's comparison | Tag |
|---|---|---|---|
| `0x00649970` | `sub_00649970_PathPlan` | return, points, exit seed of server plans of types 2, 4–10 (not 3), 13–15 (13 893 plans); refusals: return 0 and seed unchanged (628) | C |
| `0x00649760` | `sub_00649760_PathPlanStraight` | types 4, 10, 14 (2 740, 698, 54) | C |
| `0x006492F0` | `sub_006492F0_PathPlanToUnit` | type 4 (2 740 plans, each 1 point) | C |
| `0x00679C80` | `sub_00679C80_PathPlanGreedy` | types 2, 5, 6, 13 (161, 696, 655, 3 851) | C |
| `0x00679ED0` | `sub_00679ED0_PathPlanGreedyNear` | type 7 (2 725 reached, 270 through the type-1 switch) | C |
| `0x0067A000` | `sub_0067A000_PathPlanKnockback` | type 8 (282) | C |
| `0x00679F70` | `sub_00679F70_PathPlanOnePoint` | type 9 (54) | C |
| `0x0067C2D0` | `sub_0067C2D0_PathPlanType15` | type 15 (1 349 that reached it) | C |
| `0x0067B850` | `sub_0067B850_PathPlanType1` | only through greedy-near's switch (270 plans); no type-1 request | C (through the switch) |
| `0x0067A140` | `sub_0067A140_PathPlanSpiral` | type 14, the truncation (10 separating plans) | C |
| `0x0067A240` | `sub_0067A240_PathPlanRandomWalk` | type 10 (698), already C (path/0003 § 10) | C |
| `0x0067AD00` | `sub_0067AD00_PathPlanSearch` | none (types 0 and 16 had no server plan) | I |
| `0x00679E50`, `0x00679FD0`, `0x00679E60` | `PathPlanType3`, `Type11`, `Type12` | break lines: no server caller | I |

## Walkthrough

### 1. The log and what is compared

- [I] **Hooks.** `PathPlan` entry 0x00649970 (`PLN`: the unit, its type, the 0x200-byte path record, the caller's return address, the unit seed, the target
  unit), the planner call 0x00649BAE (`PLC`: the planner address in `EAX`, the 0x34-byte `PathPlanCtx` in `ECX`, the record, the rooms' live cells `PLG` — the unit's room, the
  target's room, their near lists and the near lists of those — and the unit list `PLU`) and the six `ret 0xC` of `PathPlan` (`PLX`: `EAX`, the
  record, the seed). A plan is logged only for a server unit (`Unit +0x80` = the server game) within 80 subtiles of the first player; a
  room is dumped again when its cells **or its near list** change (rev 2 of the logger: the first development logs had stale near lists, which made two plans mismatch). (0x00649970, 0x00649BAE, 0x00649984, 0x006499C2, 0x006499F0, 0x00649C5F, 0x00649C6E, 0x00649C8F)
- [I] **Model.** The planner models of `tools/path_emu3.py`, `path_emu2.py` and `path_emu1.py` run on a memory built from the logged record (pointer fields
  remapped), the live cells, the logged context and the target unit's position; the tail is `PathAimNextPoint` (`path_emu1.aim`) and the refusal when `+0x24 >= count`
  after it. The model never sees the game's output before predicting: the comparison is `eax`, the first `eax` words of the record's points (read
  from the record **after** the call, so a refused aim keeps the points) and the exit seed (`PLX.s`; the model's seed is the entry seed unless the plan is type 10 or 16). (run:2026-11-04-path)
- [C] **A refused request** (no `PLC`): `EAX` is 0 and the seed unchanged in all 628; the reason is derived from the record only where it needs no
  grid: target = start 226 (types 7, 13, 15: 20 + 100 + 106), window `|d| > 100` 191, and 211 whose reason needs the town test, the room or the free-target step.
  (0x00649A96–0x00649AB8, run:2026-11-04-path)

### 2. What the game's own play reaches (the outcome mix)

| Type | Plans | Callers (server) | Planner | Return 0 / 1 / 2–5 / 6–20 / 21+ | Most points | Draws |
|---:|---:|---|---|---|---:|---:|
| 2 | 162 | mode machine 162 (classes 92 Scarab 158, 398 3, 101 1) | greedy | 9 / 74 / 77 / 1 / 0 | 6 | 0 |
| 4 | 2 740 | missile creation 2 740 | `PathPlanToUnit` | 0 / 2 740 / 0 / 0 / 0 | 1 | 0 |
| 5 | 696 | mode machine 591, `PathReplan` 105 | greedy, `+0x98` = 2 | 31 / 0 / 665 / 0 / 0 | 5 | 0 |
| 6 | 655 | mode machine 553, `PathReplan` 102 | greedy, `+0x98` = −2 | 36 / 0 / 619 / 0 / 0 | 5 | 0 |
| 7 | 2 894 | player 1 432, mode machine 1 462 | greedy-near | 53 / 1 867 / 765 / 39 / 1 | 21 | 0 |
| 8 | 282 | mode machine (monster knockback) 282 | knockback | 31 / 251 / 0 / 0 / 0 | 1 | 0 |
| 9 | 54 | skill 54 (0x005DA00C, the player's own unit, Leap) | one point | 0 / 54 / 0 / 0 / 0 | 1 | 0 |
| 10 | 698 | missile (the reseed callbacks) 698 | random walk | 0 / 0 / 0 / 0 / 698 | 39 | 698 |
| 13 | 4 078 | mode machine 3 477, `PathReplan` 601 | greedy | 583 / 2 231 / 1 014 / 23 / 0 | 20 | 0 |
| 14 | 54 | skill 54 (0x005D0118, the hammer missile's unit) | spiral | 0 / 0 / 0 / 0 / 54 | 77 | 0 |
| 15 | 1 580 | mode machine 1 552, `PathReplan` 28 | type 15 | 972 / 113 / 77 / 187 / 0 | 19 | 0 |

(`OUTCOME MIX`; the "Return" columns count the game's `EAX`.) Labels: greedy-near took the type-1 switch in 270 of its 2 725 plans; the type-1
search in those ran at most 200 nodes (the pool) and a propagation stack at most **3** deep, against 23 in the emulation (path/0003 § 11, `[I]`
200-slot bound: not approached). The largest returns stay far under the 78 point slots: 21 (type 7), 20 (13), 19 (15), 39 (10), 77 (14). Type 8 came
from the monster knockback start only (no player mode-19 plan); type 9 from the player's Leap (`SkillDo89Jump`); the AI test plans of
type 2 at 0x005DD580, 0x005E912D, 0x005FBFB7 were not met. (`OUTCOME LABELS`, 0x0057F11C, 0x005A62F4, 0x006503CE)

- [C] **The AI's no-draw prediction:** monster plans that reached a planner, reproduced with the unit seed unchanged at the exit: type 2 161, 5 696, 6 655, 7 1 313, 13 3 851,
  15 1 349 (floor 50 each; type 1: 0). (`AI NO-DRAW PREDICTION`) (run:2026-11-04-path)
- [C] **Replans of anim/movement G1** (`PathReplan`, owner movement): 836 reproduced, all 836 with a target unit (the target revalidation). Counts by type 5 105, 6 102,
  13 601, 15 28. (`REPLANS`, 0x006503CE)

### 3. Controls

- [C] Every control of `tools/path_emu1.py .. path_emu3.py`'s lists, run on the same plans: **0 passed a plan it separates** (30 lines, 24 of which separated at least one plan). Separating counts range from 6 (greedy `rev`) and 25 (type 15 `min2`)
  to 2 307 (greedy `order`); the comparator mutations (the return +1, the exit seed's low bit, one point's low bit changed in the
  logged line) were reported in 13 265 of 13 265, 13 265 of 13 265 and 11 550 of 11 550 plans; flipping the first cell a model
  tested changed its output in 7 603 of 9 605 plans that tested a cell (the model reads the live grid). (run:2026-11-04-path)
- **Controls that proved nothing in these logs (6 of 30, 0 separating plans):** greedy `ctxroom`, knockback `ctxroom`, one point `ctxroom`, near `le325`, near `noretry`, type 15 `lim50`
  (the context room differing from the path's room, the `dx² + dy² = 325` boundary, the retry after a failed type-1 switch and a limit above 80 did not occur). Their claims stay on
  path/0003's emulation.

### 4. The floors, plan by plan

| Type | Floor | Plans reproduced | Verdict |
|---:|---:|---:|---|
| any | 2 000 | 13 893 | met |
| 1 | 100 | 0 | **short** |
| 2, 4, 7, 8, 10, 13, 15 | 100 | 162, 2 740, 2 894, 282, 698, 4 078, 1 580 | met |
| 5, 6, 9, 14 | 30 | 696, 655, 54, 54 | met (14: 44 natural) |
| 0 | none | 0 | not reached |

Type 1: the request exists in the code at five `AiPathOverrideSet(1)` sites (0x005E3BCC `AiHireFollow`, 0x005E4300 `AiPetMove`, three in state 13), at `SkillDo103DiabRun`
and the second plan of `SwarmMove`; the 21 sessions had a mercenary (CombatSor), a golem and skeletons (`k-necro`) and swarms (classes 87–90 moved in `k-dru-oasis` and
`k-sor-oasis-3`: 138 plans of types 7, 13 and 15, no `Swarm Move` start), and met no type-1 request. Short, named; its claim stays at the emulated `[C]` of path/0003 § 6 and the switch above.

### 5. Draws on the missile's seed after a type-10 plan

- [C] Seed watchpoints (`PATH_CHAIN`, a hardware watchpoint on the unit's low seed dword after each of the first 60 type-10 plans per game, at most 3 live): 70 fired, all 70 at the unit's
  release (the low dword zeroed or overwritten by the allocator, the high dword as at the plan's exit): no draw on the missile's own seed between the plan and its death. (`CHAINED DRAWS`, `SEEDW` lines) (run:2026-11-04-path)
- [C] **The control:** the same watchpoint on 14 monster units after a type-13 plan (`PATH_CHAIN_CTL`, run `k4-dru-stony`): 8 fired as the LCG step of the
  exit seed (`lo' = lo × 0x6AC690C5 + hi`), 6 did not match that step as a plain draw (the watched write came from code that changes the low dword differently; left open, § Open questions). So the
  mechanism sees draws; the type-10 missiles had none. (run:2026-11-04-path `k4-dru-stony`, 0x6AC690C5)

### 6. The spiral

- [C] **Truncation.** The probe (`PATH_SPIRAL_PROBE`, 10 spiral plans) wrote the start's low fraction word so that, at an iteration whose product differs between truncation and rounding, the sum
  `(a + fx)` reaches `0xFFFF` for the truncated product; the two readings then keep different points. The game's list equals the truncating model's in 10 of 10, the rounding model's in 0 of 10
  (the probe's `fx`, `it` and the written fraction are in each `PLN.probe`). The control `swap` (cosine and sine exchanged) separates all 54 spiral plans and passes 0. (0x0067A1A1, 0x0067A1CA, `SPIRAL`)
- [C] The 44 natural plans are the same under both readings: the game's fraction `0x8000` start and the products never straddle a boundary there; they say nothing about the truncation. (run:2026-11-04-path)

### 7. The grid tie (scoping question 3)

- [I] **What was compared:** for every plan with a `PLC`, each dumped room's live cells at the planner call against the cells of the last `CB` dump (`COLL_MapBuild`, pilot.py) of that room plus the marks of the unit list
  (players and monsters by their record's pattern and mark mask, missiles by size, objects by `RectOrWH`, except the planning unit and, under flag `0x800`, its target; a
  unit in mode 0, 12 or 17 is not marked). **Rules written before the first kept launch and not changed since:** those. **Added after the development logs, before the first kept
  launch, reported as its own variant:** a mode-12 monster with mask `0x100` carries a 3×3 of `0x8000` (a corpse). **Added after the first kept batch, no effect:** ground items
  `0x200` (rev 4 logged no item). (run:2026-11-04-path)
- [I] **Result.** First 10 plans of each session: 210 plans, 1 890 rooms, 1 260 rooms exact, 2 730 cells differ, **all of them `0x400` that the model marks and the live cells lack**
  (object classes 374, and the classes whose Objects `SubClass` `+0x167` has bit 6: 119, 156, 157, 398). All plans: 9 773 plans with a built map, 102 847 rooms, 67 080 exact (72 557 with the corpse reading),
  1 096 132 cells differ (237 596 with it). The differing bits with the corpse reading: `0x8000` 55 099, `0x0400` 81 325, `0x0200` 80 768 (live has it, no unit near: a static source or ground items the logger does not list), `0x0100` 13 720, `0x0800` 7 509, `0x0004`
  7 634, `0x0002` 6 838, `0x0080` 1 239, `0x1000` 472, `0x0040` 148. A plan's `PLC` rooms and units are logged at the same planner call, so the check above never used the model's grid. (run:2026-11-04-path)
- [I] Reading: monster, player and object marks reproduce the live cells for most of what moves; corpses are a 3×3 for the dead monsters seen (not the plus the unit's own path fields
  hold); the remaining classes need the object classes' real rule, the ground items' list (the unit hash of items did not hold them: rev 4's `PATH_ITEMS` logged none) and the doors' state. The tie is a finding, not a claim for the spec. (run:2026-11-04-path)

### 8. Break lines

- [C] The break lines were armed in every session on 0x00679E50, 0x00679FD0, 0x00679E60 (types 3, 11, 12), 0x00663E00 and 0x00663ED0 (the type-16 functions), with greedy 0x00679C80 as the
  live control, and on the 22 `+0x3C` store sites of path/0003 § 12 (the 18 unresolved server bases and the 4 read-modify-write sites). Results: types 3, 12, 16: 0 hits; type 11: 229 client hits; control: 2 100 + 2 100;
  the store sites: 7 of 22 executed (0x0057C628, 0x005FFF92, 0x00600225, 0x00600230, 0x006003B2, 0x006242FF, 0x00626E9D), **none stored 3, 0xB or 0xC**; 15 sites never executed in these sessions. (`BREAK LINES`)
- [I] So the "no server code sets 3, 11 or 12" reading stands at `[I]` with 15 of the 22 candidate stores unobserved; no store of those values among the 7 observed. (run:2026-11-04-path)

### 9. Carried inputs of the P1.3 check

- Type 12's overflow past 78 points (path/0003 § 11): client-only, 0 plans: stays `[I]`. Type 1's stack depth: 3 in 270 plans (§ 2). The 78-slot bound: the largest return 77 (spiral, always), 39 (walk), 21 (type 7). (run:2026-11-04-path)

## Data touched

`workspace/logs/path/2026-11-04-path-*` (21 logs of 60.0 MB, 21 `marks.tsv`, three `status.json` with `info.json`, the pilot transcript and screenshots under `-shots/`, `2026-11-04-path-check.txt`, `2026-11-04-path-tools.sha256`, `manifest-2026-11-04-path.sha256`);
`workspace/logs/path/dev/` (the development logs, `manifest-dev.sha256`). No game data in git.

## Dead ends

- Development logs of rev 1 had a room's near list frozen at its first dump; two type-7 plans mismatched until the near list became part of the dump key (rev 2).
- The first tie rule "a unit in mode 12 is unmarked" leaves 928 944 cells of `0x8000` over the kept set; the 3×3 corpse reading leaves 55 099. A plus (the pattern the unit's path fields hold) was not the live shape.

## Open questions

- `[L]` The 6 control watchpoints that did not equal the LCG step (§ 5): another writer of the monster's low seed dword (a resync or a table copy) or a two-write draw whose first store the watchpoint saw.
- `[L]` The unmarked object classes of § 7 (374; `SubClass` bit 6) and the source of the `0x200` cells (ground items did not appear in the item hash at `Game +0x1920`).
- `[L]` Type 1 as a request: which stock situation reaches `AiPathOverrideSet(1)` (a mercenary far from its owner, a pet, The Countess).
- `[L]` Types 0 and 16: no plan (type 0 is requested after a get-hit; the sessions had no timed-out get-hit plan).
