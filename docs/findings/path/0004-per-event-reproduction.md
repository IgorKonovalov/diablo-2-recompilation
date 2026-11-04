# 0004 — Per-event reproduction of `PathPlan`: 13 893 server plans of 21 sessions against the models, the spiral's truncation, the seed after a type-10 plan, the grid tie

> **Subsystem:** path/search
> **Question:** when the game calls `sub_00649970_PathPlan` for one of its own server units, does the request's return, the points it leaves in the
> path record and the unit's exit seed equal what the planners of [path/0001](0001-pathplan-register.md), [path/0002](0002-search.md) and
> [path/0003](0003-short-planners.md) give from the live grids of the rooms around the unit; which types does the game's own play reach; and is
> the grid the planners read the built map plus the unit marks?
> **Date:** 2026-11-04   **Plan:** 0054 (Phase 2, first lane run)   **Status:** reviewed 2026-11-04 (`lane/p54`, Tier A): accepted with fixes, Phase 2 not done ([plan 0054 log](../../plans/done/0054-path-search.md#implementation-log))

Harness work on slot 1 under gdb (no Ghidra). The logger is `tools/gdb/path.gdb` (`tools/gdb/pilot.py` + `tools/gdb/path.py`), the sessions
`tools/path_sessions.py`, the check `tools/path.py` with its no-game tests `tools/test_path.py` (12 tests). The run record, setup and the
boundary of every "0 mismatches" below are in [experiments.md](experiments.md) § run:2026-11-04-path; kept outputs under
`workspace/logs/path/` (manifest `manifest-2026-11-04-path.sha256`, 53 lines, passes from that directory; development logs in `dev/`
with `manifest-dev.sha256`, 51 lines). Tool revisions: commits `a501a7fa` (logger rev 3) and `178106ec` (rev 4, checker). The review's figures are in `workspace/logs/path/review-p54/review.txt` (`tools/path_review.py`, manifest in that directory); `path.py check` rerun at the review gives the kept output byte for byte (`8f6951c3`). *Note 2026-11-04 (`lane/p54b`): `tools/path_review.py` is retired, its sections folded into `tools/path.py check`; the review's revision is at commit `e990dea0`, and the later check prints the same figures with the block write labelled ([path/0005](0005-grid-rules.md) § Tools).*

## Answer (summary)

- [C] **0 mismatches over 13 051 stock plans, on the game's own live grids** (12 427 reached a planner or a straight type, 624 were refused before one) in 21 fresh-process
  sessions on a town (Act IV), outdoor levels (Stony Field, Far Oasis, Flayer Jungle, River of Flame, Glacial Trail) and maze levels (Jail 1,
  Halls of the Dead 2), in Acts 1 to 5: the return, the first `EAX` points of the record and the exit seed equal the model's, for the types
  2, 4, 5, 6, 7, 8, 9, 10, 13, 15, the planners they reach, and type 14 with the limit of § 6. The log holds 13 893 plans, also 0 mismatches; the other 842 come after the probe's first write in `k-pal-stony` (532) and `k-pal-jail` (310) and are not stock (ADR-0003, § 6).
  **What this tests:** the planners, given the game's live cells, its context and its record at the planner call. It does not test a predicted grid: on the tie's grid the same model is wrong in 361 of 9 773 plans (§ 7). It does not test `PathPlan`'s head, and for 211 refusals it predicts nothing (§ 1). The boundary is the `Conclusion` of the run record: nothing else of the record is compared; type 0, type 1 and
  types 3, 11, 12, 16 had no server plan. (run:2026-11-04-path, 0x00649970, 0x00649BAE)
- [C] **The floors:** 2 000 plans in all (13 893), and per type 100: 2 (162), 4 (2 740), 7 (2 894), 8 (282), 10 (698), 13 (4 078), 15 (1 580); 30: 5
  (696), 6 (655), 9 (54), 14 (54 logged: 10 on the probe's write, 17 natural in the two sessions after a write, 27 in stock sessions). Without the plans after a write every floor still holds except **type 14: 27, short by 3**, and all its natural plans are one list relative to the start (§ 6). **Short: type 1 with 0 plans** (floor 100). Type 0 had no plan
  (no floor). Callers by `ra`: all 13 893 are call sites of the register of path/0001 § 11 (`PathPlan` callers 0x0057F11C player, 0x005A62F4 and
  0x005D0118 mode machine / skill, 0x006503CE and 0x006503E2 `PathReplan`, 0x0059FDB6 the missile creation, 0x005DA00C the Leap, 0x005A7859 the monster knockback). (`2026-11-04-path-check.txt`)
- [C] **Types 3, 11, 12 and 16: no server-caller line in the logs of 21 sessions.** The break lines on the planners of 3 and 12 and on the two
  type-16 functions printed 0 lines on either side; type 11's printed 229, all with a client caller (`side=cli`, 2 Barbarian sessions: 173 and 56; return 0x00649BB0), so that line is live in those two by itself.
  **The control's window:** greedy (0x00679C80) printed 100 lines per side per game, 2 100 + 2 100, which is the logger's cap and not a hit count. Its last server line lies at frame 19 197 of 62 321 summed over the sessions (6 % to 96 % per session), its last client line at 11 456. So the absence has a same-function control for that stretch `[C]`; from there to the last plan the process's other breakpoints (`PLC`, `S3C`) still print, and "no server caller" there is `[I]`. "No server code requests them" stays `[I]`.
  (`BREAK LINES`, `review-p54/review.txt` § 3; 0x00679FD0, 0x00679C80)
- [C] **The spiral truncates** (raised 2026-11-04 by the read-only stored products of run:2026-11-04-path-2, [path/0006](0006-holdout.md): 18 174 separating, 18 174 truncate; the probe's 10 below stay on a written input). The code sets the rounding field to 11 around each `FISTP` (`or eax, 0xC00` at 0x0067A1A1 and 0x0067A1CA, `fldcw`, `fistp` at 0x0067A1AC and 0x0067A1DD), and with the start's fraction **written by the probe** so that a truncating and a rounding product land on opposite
  sides of a subtile boundary (10 plans, 6 + 4), the game's point list equals the truncating model in 10 of 10 and the rounding model in 0
  of 10. Lowered from `[C]` at the review: ADR-0003, a breakpoint never writes game memory, § 6. The 27 stock and 17 later natural plans do not separate the readings (one list, § 6). The stored product logged read-only settles it: 78 of the 188 products of every natural plan differ between the readings (`review-p54/review.txt` § 16). (0x0067A1A1, 0x0067A1CA, run:2026-11-04-path)
- [C] **No later draw on the seed of a class-458 (`firestormmaker`) missile within its life, 68 watched.** Every watched seed's next write is a block write over the unit's memory (`rep stos` or `rep movs`; 0x00681F4F, 0x00682A1A, 0x0057CAE6; that this is the block's release or reuse is `[I]`), and in each the high dword still held the plan's exit value. A draw rewrites the high dword too, so that dword is a second source that does not rest on the watchpoint. The mechanism sees draws: of 14 control watchpoints on monsters, 8 lines are the LCG step, full seed, and 6 are the same release at 0x00681F4F (§ 5). Classes 195 and 225 had **one watched seed each**, `[I]`; class 225 (`buglightning`) makes 514 of the 698 plans.
  So for class 458 the exit seed of `PathPlanRandomWalk` is the seed the missile keeps, and "chained to the next event" has no draw to chain to. **The plan's floor is answered for class 458 (68 of 50), open for the two others.** (run:2026-11-04-path, `review-p54/review.txt` §§ 9, 15)
- [I] **The tie of the grid is not exact, and it matters.** The live cells equal the built map plus the unit list's marks in 55 of 9 773 plans (100 with the corpse
  reading) and 72 557 of 102 847 rooms with it. **Fed the tie's grid instead of the live cells, the planners' model is wrong in 361 of the 9 773 plans (3.7 %):** type 7 260, 13 71, 15 23, 8 7, and 0 of 2, 5, 6, 9; the corpse reading changes none of the 361; the `0x400` differences alone make 335 of them wrong, `0x1000` 25, `0x800` 8. In the first 10 plans of each session (210 plans, all in Act IV's town, 1 890 rooms, 1 260 exact) the only residual is `0x400`, 2 730 cells the model marks and the live cells lack (objects 374 and 398, § 7). The 0 mismatches above therefore say nothing about the predicted grids; **P1.1's ruling 3 is not met** (§ 7). (run:2026-11-04-path, `review-p54/review.txt` §§ 6, 7, 12)
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
| `0x00649970` | `sub_00649970_PathPlan` | return, points, exit seed of server plans of types 2, 4–10, 13–15, from the logged context and record (13 051 stock plans): the planner's result and the tail. The head that builds the context is an input here, not compared (§ 1); refusals: return 0 and seed unchanged (624) | C |
| `0x00649760` | `sub_00649760_PathPlanStraight` | types 4, 10, 14 (2 740, 698, 54) | C |
| `0x006492F0` | `sub_006492F0_PathPlanToUnit` | type 4 (2 740 plans, 2 658 stock, each 1 point; no control exists) | C |
| `0x00679C80` | `sub_00679C80_PathPlanGreedy` | types 2, 5, 6, 13 (161, 696, 655, 3 851) | C |
| `0x00679ED0` | `sub_00679ED0_PathPlanGreedyNear` | type 7 (2 725 reached, 270 through the type-1 switch) | C |
| `0x0067A000` | `sub_0067A000_PathPlanKnockback` | type 8 (282) | C |
| `0x00679F70` | `sub_00679F70_PathPlanOnePoint` | type 9 (54): the one-point return only, no control separated a plan and no output needs the grid (§ 3) | C |
| `0x0067C2D0` | `sub_0067C2D0_PathPlanType15` | type 15 (1 349 that reached it) | C |
| `0x0067B850` | `sub_0067B850_PathPlanType1` | only through greedy-near's switch (270 plans; its own controls separate up to 178, § 3); no type-1 request | C (through the switch) |
| `0x0067A140` | `sub_0067A140_PathPlanSpiral` | type 14: the list, 27 stock plans, one list relative to the start `0x8000`; `swap` separates it. The rounding is `[C]` by [path/0006](0006-holdout.md) | C |
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
- [I] **What the model takes from the game** (review): the planner's address (`PLC.pl`), the context and the record at the planner call. So the head of `PathPlan`, the target refresh, the free-target step, the town test, the context's fields and the type-to-planner slot are inputs or observations here, not predictions; they stay at path/0001's tags. One backwards test holds: none of the 9 773 plans with a `PLC` has a record-only refusal reason, and each context's start equals its record's. (`review-p54/review.txt` § 8, 0x00649970, 0x00649BAE)
- [C] **A refused request** (no `PLC`): `EAX` is 0 and the seed unchanged in all 628; the reason is derived from the record only where it needs no
  grid: target = start 226 (types 7, 13, 15: 20 + 100 + 106), window `|d| > 100` 191, and 211 whose reason needs the town test, the room or the free-target step. Those 211 are observed, not predicted: their "match" only says the game returned 0.
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
- [C] **Replans of anim/movement G1** (`PathReplan`, owner movement): 836 reproduced, all 836 with a target unit at `PathPlan`'s entry. Counts by type 5 105, 6 102,
  13 601, 15 28. The target revalidation is `PathReplan`'s own code before this call and is not compared here: `[I]`. (`REPLANS`, 0x006503CE)

### 3. Controls

- [C] Every control of `tools/path_emu1.py .. path_emu3.py`'s lists, run on the same plans: **0 passed a plan it separates** (30 lines, 24 of which separated at least one plan). Separating counts range from 6 (greedy `rev`) and 25 (type 15 `min2`)
  to 2 307 (greedy `order`); the comparator mutations (the return +1, the exit seed's low bit, one point's low bit changed in the
  logged line) were reported in 13 265 of 13 265, 13 265 of 13 265 and 11 550 of 11 550 plans; flipping the first cell a model
  tested changed its output in 7 603 of 9 605 plans that tested a cell (the model reads the live grid). (run:2026-11-04-path)
- **Controls that proved nothing in these logs (6 of 30, 0 separating plans):** greedy `ctxroom`, knockback `ctxroom`, one point `ctxroom`, near `le325`, near `noretry`, type 15 `lim50`
  (the context room differing from the path's room, the `dx² + dy² = 325` boundary, the retry after a failed type-1 switch and a limit above 80 did not occur). Their claims stay on
  path/0003's emulation.
- **Controls per type, and what each type's 0 is worth** (review; `review-p54/review.txt` §§ 4, 5, 10; "needs the grid" is the model's output changing on an empty grid). The check prints controls per family, so a family's count can hide its types: `greedy rev`'s 6 are all type 13.

| Type | Planner plans | Needs the grid | Controls that separate (count) | Controls at 0 | The 0 is |
|---:|---:|---:|---|---|---|
| 13 | 3 851 | 2 985 | `order` 1 012, `dist` 755, `limit` 492, `refresh` 302, `noflag` 226, `rev` 6 | `ctxroom` | **strong** |
| 7 | 2 725 | 897 | `order` 603, `noflag` 377 | `le325`, `noretry` | **strong**; the 324 boundary and the retry unobserved |
| 15 | 1 349 | 1 182 | `wswap` 352, `reduce` 271, `lim18`, `lim40` 269, `noswap` 180, `min2` 25 | `lim50` | **strong** on the 377 with points; 972 are the planner's own 0 |
| 10 | 698, straight | none | all five, 698 each | | **strong** for count and draws; classes 458, 225, 195; no grid |
| 7 through type 1 | 270 | | `h` 178, `cost` 159, `offs` 151, `list` 149, `min2` 3, `resort` 2, `gt0` 1 (the check never ran these) | `nostart`, `pool`, `max77` | **fair**; the switch only |
| 5, 6 | 696, 655 | 150, 192 | `param0` 686, 647; `order` 643, 587 | `dist`, `limit`, `noflag`, `refresh`, `rev`, `ctxroom` | **fair**: the `+0x98` walk, at most 5 points |
| 8 | 282 | 90 | `k` 218, `floor` 76 | `ctxroom` | **fair**: monster knockback only, 1 point at most |
| 2 | 161 | 161 | `order` 65, `limit` 48, `dist`, `refresh` 21, `noflag` 18 | `param0`, `rev`, `ctxroom` | **fair**: 158 of 162 one class (92 `scarab2`) |
| 9 | 54 | 0 | none | `ctxroom`, its only control | **weak**: one branch, 1 point, no grid |
| 4 | 2 740, straight | none | none exists | | **weak** for its size: one branch, 1 point |
| 14 | 54, straight | none | `swap` 54, `round` 10 (on the written plans only) | | **weak**: one list |

  The types' weak rows are also the ones with the least code: the models of types 4, 9 and 14 are short, and the emulated maps of path/0001 and path/0003 cover their other branches. Weak means these logs add little, not that a model failed. (run:2026-11-04-path)

### 4. The floors, plan by plan

| Type | Floor | Plans reproduced | Verdict |
|---:|---:|---:|---|
| any | 2 000 | 13 893 | met |
| 1 | 100 | 0 | **short** |
| 2, 4, 7, 8, 10, 13, 15 | 100 | 162, 2 740, 2 894, 282, 698, 4 078, 1 580 | met |
| 5, 6, 9 | 30 | 696, 655, 54 | met |
| 14 | 30 | 27 stock (54 logged) | **short by 3**, and one list (§ 6) |
| 0 | none | 0 | not reached |
| Missiles H1, the 450 re-walked | all | 654 of 654 (path/0003 § 10, `p3-h1log.txt`) | met, by run:2026-11-03-path-emu-3 |
| Missiles H1, 50 new plans chained | 50 | 68 class 458; 1 each 195, 225 | answered for 458 (§ 5), open for 195 and 225 |

Type 1: the request exists in the code at five `AiPathOverrideSet(1)` sites (0x005E3BCC `AiHireFollow`, 0x005E4300 `AiPetMove`, three in state 13), at `SkillDo103DiabRun`
and the second plan of `SwarmMove`; the 21 sessions had a mercenary (CombatSor), a golem and skeletons (`k-necro`) and swarms (classes 87–90 moved in `k-dru-oasis` and
`k-sor-oasis-3`: 138 plans of types 7, 13 and 15, no `Swarm Move` start), and met no type-1 request. Short, named; its claim stays at the emulated `[C]` of path/0003 § 6 and the switch above.

### 5. Draws on the missile's seed after a type-10 plan

- [C] Seed watchpoints (`PATH_CHAIN`, a hardware watchpoint on the unit's low seed dword after each of the first 60 type-10 plans per game, at most 3 live; sessions `k-dru-stony` 20, `k-dru-oasis` 38, `k4-dru-stony` 12): 70 fired, class 458 68, classes 195 and 225 one each. All 70 are block
  writes over the unit's memory, 65 at `rep stos` 0x00681F4F and 3 at `rep movs` 0x0057CAE6 (low dword 0), 2 at `rep movs` 0x00682A1A (low dword not 0), and in **all 70 the high dword equals the plan's exit value**: the trap comes after the block's first dword, before the high one. An LCG draw replaces the high dword with `(lo × 0x6AC690C5 + hi) >> 32`, so an unseen draw would show there. (`CHAINED DRAWS`, `SEEDW` lines, `review-p54/review.txt` §§ 9, 15) (run:2026-11-04-path)
- [C] **The control:** the same watchpoint on 14 monster units after a type-13 plan (`PATH_CHAIN_CTL`, run `k4-dru-stony` only, beside 12 of the 70): 8 lines (7 draws: two watchers shared one unit) are the LCG step, low and high dword both, at 0x0045C3BB, 0x0055AA1E, 0x0057E049, 0x005EFDF5. **The other 6 are not another writer:** each is the block write at 0x00681F4F with the high dword unchanged, the 70's own pattern, for a monster with no draw since its plan. So 14 of 14 fired as they should: the check's `NOT the LCG step` is a label on that write, not a miss. The two sessions without a control rest on the high dword. (run:2026-11-04-path `k4-dru-stony`, 0x6AC690C5, 0x00681F4F)

### 6. The spiral

- [I] **Truncation, by a written input.** The probe (`PATH_SPIRAL_PROBE`, 10 spiral plans) wrote the start's low fraction word from a breakpoint at `PathPlan`'s entry so that, at an iteration whose product differs between truncation and rounding, the sum
  `(a + fx)` reaches `0xFFFF` for the truncated product; the two readings then keep different points. The game's list equals the truncating model's in 10 of 10, the rounding model's in 0 of 10
  (the probe's `fx`, `it` and the written fraction are in each `PLN.probe`). (0x0067A1A1, 0x0067A1CA, `SPIRAL`)
- **Ruling (review), a recorded deviation from ADR-0003, as the `lane/p52b` review ruled P1b-2.** "A breakpoint prints and continues. It never writes game memory or registers." ADR-0010 and ADR-0013 admit table cells through a loose `.bin`, not memory, and even by analogy keep `[I]` a claim whose code reads the edited value, which `fx` is; ADR-0013's built saves are files loaded before play. This case differs in one way: the write is a vehicle for the instruction under test and asserts no game state, so the result is a strong `[I]` and no lead. It does not differ in the way that matters, since a read-only route exists and costs less than the write. No new ADR. The written plans and every plan after them in those two sessions (842) leave the stock counts.
- [C] The list, without the rounding: the 27 natural plans of stock sessions (and the 17 natural plans after a write) equal the model, and control `swap` separates them. **They are one case:** the start fraction is `0x8000` on both axes in all 44, the spiral reads no grid and draws nothing, so all 44 are one point list relative to the start. They say nothing about the truncation. (run:2026-11-04-path, `review-p54/review.txt` § 2, 0x0067A140)
- [I] **What settles it without a write:** a printing breakpoint at 0x0067A1AF and 0x0067A1E0, right after each `fistp qword [ebp-0x20]`, logging that dword per iteration, against the two readings computed from the image's table at 0x00707800 and `r`. The product is 78 of 188 times different between the readings in every natural plan, so one plan separates them many times over. (`review-p54/review.txt` § 16, 0x0067A1AC, 0x0067A1DD)

### 7. The grid tie (scoping question 3)

- [I] **What was compared:** for every plan with a `PLC`, each dumped room's live cells at the planner call against the cells of the last `CB` dump (`COLL_MapBuild`, pilot.py) of that room plus the marks of the unit list
  (players and monsters by their record's pattern and mark mask, missiles by size, objects by `RectOrWH`, except the planning unit and, under flag `0x800`, its target; a
  unit in mode 0, 12 or 17 is not marked). **Rules in `a501a7fa`, before the first kept launch, and not changed since:** those. **The corpse variant, reported on its own:** a mode-12 monster with mask `0x100` carries a 3×3 of `0x8000`. It is fitted, on the development logs by the lane's account; the commits cannot show it came first, since `a501a7fa` has no corpse code and it lands in `178106ec` at 02:14, after 20 of the 21 kept sessions (the last of the 20 ends 02:07). **Added after the first kept batch, no effect:** ground items
  `0x200` (rev 4 logged no item). Baseline: `CB` is the game's own built map, so this is built-to-live; predicted-to-built rests on drlg/collision's checks and is not re-run here. (run:2026-11-04-path)
- [I] **Result.** First 10 plans of each session: 210 plans, 1 890 rooms, 1 260 rooms exact, 2 730 cells differ, **all of them `0x400` that the model marks and the live cells lack**
  (objects of class 374, `+0x167` = 0, and class 398, `+0x167` = `0x40`; all 210 plans are in level 103, 204 of them type 7, and the unit lists hold 920 monsters' entries and no missile or corpse there, so these plans test the objects and little else). All plans: 9 773 plans with a built map, 102 847 rooms, 67 080 exact (72 557 with the corpse reading),
  1 096 132 cells differ (237 596 with it). The differing bits with the corpse reading: `0x8000` 55 099, `0x0400` 81 325, `0x0200` 80 768 (live has it, no unit near: a static source or ground items the logger does not list), `0x0100` 13 720, `0x0800` 7 509, `0x0004`
  7 634, `0x0002` 6 838, `0x0080` 1 239, `0x1000` 472, `0x0040` 148. A plan's `PLC` rooms and units are logged at the same planner call, so the check above never used the model's grid. (run:2026-11-04-path)
- [I] Reading: monster, player and object marks reproduce the live cells for most of what moves; the remaining classes need the object classes' real rule, the ground items' list (the unit hash of items did not hold them: rev 4's `PATH_ITEMS` logged none) and the doors' state. (run:2026-11-04-path)
- [I] **The corpse reading (review).** Each distinct mode-12 monster of the kept unit lists: 991 of 992 show a full 3×3 of `0x8000` in the live cells, with the unit's mask still `0x100` and its pattern 0, 1, 2 or 3, never 5; the one other is class 273 (`gargoyletrap`, `deadCol` 1), which keeps `0x100` as drlg/collision says. The development logs give 304 of 304. The figures with and without the reading are both printed by the check, and it changes none of the 361 wrong plans. **Stays `[I]`:** it was fitted, its caller was not read, and the next kept batch is its hold-out. The earlier sentence here, "not the plus the unit's own path fields hold", was wrong: those fields hold no plus. **It disagrees with a reviewed row:** [drlg/collision](../../specs/drlg/collision.md) gives a dead `deadCol` 0 monster "pattern 5 (plus), `0x8000`", `[C]` by run:2026-10-14-collision, whose dumps sit at the tests 0x004B05DB and 0x004B09FB; the arg-1 call at 0x005A65D9 (3×3 at 0x00649FD8, the unit's mask untouched) fits these server cells. Which copy each path serves is not settled here: [backlog entry](../../backlog/archive/2026-11-04-architect-reverser-plan-0054-corpse-mark-server-3x3-against-drlg.md). (`review-p54/review.txt` § 13, 0x00649F70, 0x00649FD8, 0x005A65D9, run:2026-11-04-path)
- **Ruling (review): P1.1's ruling 3 is not met, and neither is scoping question 3.** Context: met, `PLC` holds all 0x34 bytes. Unit list: not met as ruled. No field states "marked at the call" (the checker infers it from the mode), 221 plans stand at the 120-unit cap, and no ground item is listed. First 10 plans: dumped and compared, but all in Act IV's town and not exact. The tie that lets a predicted grid stand for the live one is therefore open, by a measured amount: 361 wrong plans of 9 773, 335 of them `0x400`. Next run, plan log. (`review-p54/review.txt` §§ 6, 7, 11, 12, run:2026-11-04-path)

### 8. Break lines

- [C] The break lines (the control's cap and window: Answer) were armed in every session on 0x00679E50, 0x00679FD0, 0x00679E60 (types 3, 11, 12), 0x00663E00 and 0x00663ED0 (the type-16 functions), with greedy 0x00679C80 as the
  live control, and on the 22 `+0x3C` store sites of path/0003 § 12 (the 18 unresolved server bases and the 4 read-modify-write sites). Results: types 3, 12, 16: 0 hits; type 11: 229 client hits; control: 100 lines per side per game, the cap;
  the store sites: 7 of 22 executed (0x0057C628, 0x005FFF92, 0x00600225, 0x00600230, 0x006003B2, 0x006242FF, 0x00626E9D), **none stored 3, 0xB or 0xC**; 15 sites never executed in these sessions. (`BREAK LINES`)
- [I] So the "no server code sets 3, 11 or 12" reading stands at `[I]` with 15 of the 22 candidate stores unobserved; no store of those values among the 7 observed. These lines test the value at every hit, and print a store of 3, 11 or 12 whatever the count, so the 7 sites' absence covers their hits. The 15 say nothing either way. (run:2026-11-04-path, 0x0057C628)

### 9. Carried inputs of the P1.3 check

- Type 12's overflow past 78 points (path/0003 § 11): client-only, 0 plans: stays `[I]`. Type 1's stack depth: 3 in 270 plans (§ 2). The 78-slot bound: the largest return 77 (spiral, always), 39 (walk), 21 (type 7). (run:2026-11-04-path)

## Data touched

`workspace/logs/path/2026-11-04-path-*` (21 logs of 60.0 MB, 21 `marks.tsv`, three `status.json` with `info.json`, the pilot transcript and screenshots under `-shots/`, `2026-11-04-path-check.txt`, `2026-11-04-path-tools.sha256`, `manifest-2026-11-04-path.sha256`);
`workspace/logs/path/dev/` (the development logs, `manifest-dev.sha256`). No game data in git.

## Dead ends

- Development logs of rev 1 had a room's near list frozen at its first dump; two type-7 plans mismatched until the near list became part of the dump key (rev 2).
- The first tie rule "a unit in mode 12 is unmarked" leaves 928 944 cells of `0x8000` over the kept set; the 3×3 corpse reading leaves 55 099 (§ 7).

## Open questions

- `[L]` The server's dead-monster mark against drlg/collision's plus (§ 7).
- `[L]` Whether a class-225 or class-195 missile draws on its own seed after its plan (one watched seed each, § 5).
- `[L]` The unmarked object classes of § 7 (374; 398, with `SubClass` bit 6) and the source of the `0x200` cells (ground items did not appear in the item hash at `Game +0x1920`).
- `[L]` Type 1 as a request: which stock situation reaches `AiPathOverrideSet(1)` (a mercenary far from its owner, a pet, The Countess).
- `[L]` Types 0 and 16: no plan (type 0 is requested after a get-hit; the sessions had no timed-out get-hit plan).
