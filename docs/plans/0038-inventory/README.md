# Plan 0038 inventory: totals, batch list and priority order

Phase 0 of [plan 0038](../0038-inferred-claims-sweep.md), written by the architect on `lane/c38` from the four cluster
inventories: (0a) items, (0b) save, data and rng, (0c) monsters, hirelings and player, (0d) drlg and objects. The
cluster files read the specs at `main` `e1c807a`. Up to `551bee9` the only spec change is the name-only rename
`QUESTS_ObjectOperate` → `QUESTS_ObjectEvent` in items/quest-drops and objects, so every front-matter count still
holds.

**Status: accepted with fixes (architect review, 2026-10-16).** The review's rulings and moves are in
[§ 2.5](#25-moves-made-by-the-phase-0-review) and [§ 6](#6-forced-run-candidates-ruled-at-the-review); the tables below
include them. Phase 1 and Phase 2 batches may start in the order of [§ 7](#7-priority-order).

How to read this file:
- **The per-spec files keep the class and batch the clusters gave each row.** This README is the authority where the
  two differ: it adds the [moves](#2-moves-after-the-clusters-read-the-specs) of § 2 (§ 2.5 holds the review's) and the
  [batch reconciliation](#4-batch-ids-reconciled-across-clusters) of § 4. A batch lane takes its rows from the § 5
  batch list, not from the per-spec files' *Batch* column.
- A row reference such as `tc 10` means row `#10` of [items-tc.md](items-tc.md). Counts are statements (the files'
  *Count* column), not rows.

## 1. Totals per spec and class, as filed by the clusters

Every file's *Count* column sums to its spec's front-matter `I` at the recorded commit, which gives 1 526 in all. All
four clusters checked that each spec's front matter matches its body count. `items/README` and `save/README` are
`draft` and out of scope. `player/README` has no tag.

| Spec (inventory file) | Cluster | I | a-logs | a-run | b | c | d-none | d-edit | d-sim | d-2c | d-owner | d-0032 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [items/tc](items-tc.md) | 0a | 76 | 38 | 1 | 16 | 9 | 5 | 4 | · | 3 | · | · |
| [items/quality](items-quality.md) | 0a | 36 | 16 | 3 | 1 | 3 | 13 | · | · | · | · | · |
| [items/affixes](items-affixes.md) | 0a | 45 | 16 | 11 | · | 6 | 12 | · | · | · | · | · |
| [items/uniques-sets](items-uniques-sets.md) | 0a | 52 | 23 | 3 | 1 | 4 | 14 | 7 | · | · | · | · |
| [items/properties](items-properties.md) | 0a | 35 | 13 | 5 | 6 | 3 | 8 | · | · | · | · | · |
| [items/cube](items-cube.md) | 0a | 82 | 13 | · | 26 | 7 | 36 | · | · | · | · | · |
| [items/sockets-runewords](items-sockets-runewords.md) | 0a | 77 | 18 | · | 23 | 9 | 11 | 16 | · | · | · | · |
| [items/vendors](items-vendors.md) | 0a | 37 | 9 | 2 | 11 | 6 | 3 | · | 1 | 5 | · | · |
| [items/quest-drops](items-quest-drops.md) | 0a | 83 | 9 | 1 | 54 | 8 | 2 | · | · | 3 | · | 6 |
| [save/d2s](save-d2s.md) | 0b | 144 | 17 | 1 | 79 | 43 | 4 | · | · | · | · | · |
| [data/excel](data-excel.md) | 0b | 100 | 31 | · | 17 | 26 | 9 | 17 | · | · | · | · |
| [data/calc](data-calc.md) | 0b | 67 | 4 | · | 5 | 41 | 1 | 10 | 6 | · | · | · |
| [data/strings](data-strings.md) | 0b | 39 | 6 | · | 4 | · | 9 | 20 | · | · | · | · |
| [data/README](data-README.md) | 0b | 5 | 1 | · | 4 | · | · | · | · | · | · | · |
| [rng](rng-README.md) | 0b | 8 | 1 | · | · | 5 | 2 | · | · | · | · | · |
| [rng/seeds](rng-seeds.md) | 0b | 17 | 4 | 1 | 9 | 1 | 2 | · | · | · | · | · |
| [monsters/pool](monsters-pool.md) | 0c | 29 | 15 | 1 | 4 | 2 | 4 | 3 | · | · | · | · |
| [monsters/README](monsters-README.md) | 0c | 1 | 1 | · | · | · | · | · | · | · | · | · |
| [monsters/spawn](monsters-spawn.md) | 0c | 64 | 23 | 9 | 2 | 6 | 15 | 9 | · | · | · | · |
| [monsters/special](monsters-special.md) | 0c | 91 | 14 | 20 | 23 | 1 | 28 | · | · | · | 3 | 2 |
| [monsters/stats](monsters-stats.md) | 0c | 54 | 10 | 8 | 6 | 3 | 17 | 1 | 7 | · | 2 | · |
| [hirelings](hirelings-README.md) | 0c | 39 | 3 | 6 | 23 | 2 | 2 | 1 | 1 | 1 | · | · |
| [player/creation](player-creation.md) | 0c | 39 | 5 | · | 22 | 3 | 5 | · | · | 2 | 2 | · |
| [player/README](player-README.md) | 0c | 0 | · | · | · | · | · | · | · | · | · | · |
| [drlg/README](drlg-README.md) | 0d | 18 | 8 | 1 | 5 | 2 | 2 | · | · | · | · | · |
| [drlg/room-tiles](drlg-room-tiles.md) | 0d | 46 | 19 | 6 | 6 | 11 | 4 | · | · | · | · | · |
| [drlg/preset](drlg-preset.md) | 0d | 44 | 18 | 5 | 2 | 14 | 4 | · | · | · | 1 | · |
| [drlg/maze](drlg-maze.md) | 0d | 26 | 5 | 16 | · | 2 | 3 | · | · | · | · | · |
| [drlg/outdoor](drlg-outdoor.md) | 0d | 22 | 5 | 5 | · | 3 | 9 | · | · | · | · | · |
| [drlg/warps](drlg-warps.md) | 0d | 31 | 4 | 17 | 3 | 2 | 5 | · | · | · | · | · |
| [drlg/collision](drlg-collision.md) | 0d | 55 | 22 | 18 | · | 5 | 3 | · | 7 | · | · | · |
| [objects](objects-README.md) | 0d | 64 | 8 | 32 | 3 | 5 | 15 | · | 1 | · | · | · |
| **All** | | **1 526** | **379** | **172** | **355** | **232** | **247** | **88** | **23** | **14** | **8** | **8** |

Cluster 0b filed its emulator rows (S1e) as (c). § 2.1 gives them their own route.

## 2. Moves after the clusters read the specs

Two changes landed on `main` after the clusters' read (`lane/rbl`, merged at `551bee9`).

### 2.1 ADR-0015: the emulation route `(c-emu)`

[ADR-0015](../../adrs/0015-emulated-reproduction.md) (accepted) admits a run of the pinned image's own code under
Ghidra's p-code emulator as evidence rule 4. It requires unmodified code and a declared read set, and it admits
synthetic records. This adds a route to the plan's [classes](../0038-inferred-claims-sweep.md#classes):

| Class | Meaning | Who raises it |
|---|---|---|
| **(c-emu)** | A pure or table-reading function, run under the emulator on synthetic or stock inputs and compared bit for bit with a `tools/` model, under ADR-0015's conditions 1 to 5. It covers the code's map from the bytes it reads. Faults, fatal-error calls, x87 results and OS or file calls are excluded, and so is the meaning of each offset, which carries its own evidence. | reverser, static batch S1e (no slot) |

**Applied only where it clearly fits.** The function must be pure, or read only table records and image data (no
walk of a unit, room or game structure beyond a scratch record). The branch must not be a fatal, a fault, a missing
file or another language. The claim must be about the code, not about the stock data.

- **42 statements relabelled (c) → (c-emu).** These are the S1e rows cluster 0b had already routed to emulation
  (47), less the 5 that `lane/rbl` raised (§ 2.2).
- **32 statements reclassified to (c-emu) from other classes:**
  - **data/calc, 10 statements:**
    - [data-calc](data-calc.md) 9, 16 and 37 (b → c-emu, out of H3a): the entry points' offset test (blank cell,
      offset ≥ size). `MISS_EvalCalc`'s pool-end case already ran in run:2026-10-16-calc-emu, and `EvalSkill` and
      `EvalItem` take the same pool image.
    - 31, six of its seven statements (d-edit → c-emu): `dm78`, `mana`, `clc2`/`clc3`/`rng`, `ast*`/`pst*`, `pets`/`skpt`
      and `m1rn`…`m3rn`. These are `SKILLS_CalcVar` reads of the skills record, run on a synthetic record as
      `MISS_CalcVar` was. The seventh, `blvl`, reads the unit's skill and becomes d-sim.
    - 40, `dm78` at level 0 (d-edit → c-emu).
  - **data/excel, 10 statements:**
    - [data-excel](data-excel.md) 16, 43, 44 and 56 (d-none → c-emu): the name-key length, code against TC-name
      resolution and its case rules, unique row 0 from a TC cell, and the key compile of string entry 0. These are the
      lookup functions S1e already emulates (`EXCEL_FindCode`/`AddCode`), run on synthetic keys.
    - 51, 52, 53, 60, 64 and 66 (d-edit → c-emu): the language-code table, index ≥ 20000 without `expansionstring`,
      entry past count, the integer byte ≥ 0x80, the failed-compile −1 of the item calc callback, and a key that
      matches nothing.
  - **data/strings, 12 statements:** [data-strings](data-strings.md) 4, 5, 12, 14, 16, 24, 25 and 32 (d-edit) and
    10, 17, 20 and 35 (d-none). They cover the index fallbacks (11078, entry 500, the `patchstring` 1078 landing),
    `CharCount` without a font map, the missing-`patchstring` fallback, and entry 0 against "not found" in
    `GetByKey`. Each is run on a scratch string-table image whose pointers the memory spec sets, as `g_pDataTables`
    was set in run:2026-10-16-calc-emu.
  - By origin: 3 from (b), 21 from d-edit and 8 from d-none.
- **27 statements are emulation candidates that were not reclassified.** The read set may not be declarable, or the
  function may reach callees outside the emulator. The review or the S1e lane decides each one:
  - monsters/pool 2, 25 and 26 (the pool build on a synthetic Levels row: leading-slot count, first blank, the u8
    `raritySum` wrap; 3 statements);
  - monsters/stats 4, 35 and 41 (the HP cap, `MonHpAddPct`'s two unreached branches, the signed halving, if the stat
    reads are not stat-list walks; 4);
  - items/uniques-sets 26, 43 and 44 (the bound at row 4096, the signed 16-bit `lvl`, set weight 0; 3);
  - items/affixes 6 and 12 (the 511-candidate cap; 2);
  - items/quality 2, 17 and 21 (negative magic find, if magic find enters as an argument or a declared stat read; 3);
  - items/tc 9, 54 and 65 (upgrade draws under `ce=`/`cg=` on a synthetic runtime TC, if the callees can be
    ADR-0004 oracles; 3);
  - data/excel 65, 69 and 70 (the loader's per-type writers and callback order on a synthetic descriptor; 7);
  - data/calc 8 and 33 (the compile order within a record, the description-missile index; 2).
  - The H2c forced claims (§ 6) are also possible emulation targets. Emulation would replace the table edit, but the
    property handlers write stat lists, so their read sets are not obviously small.

### 2.2 Raised on `lane/rbl`, awaiting the Phase 3 re-tag

run:2026-10-16-calc-emu ([data/0005 § 11](../../findings/data/0005-calc.md#11-static-emulation-of-the-functions-and-the-missile-context-run2026-10-16-calc-emu))
and the game-creation recount in
[rng/0002](../../findings/rng/0002-seed-tree.md#other-seed-sites-seen-not-yet-followed) raised these finding claims to
`[C]`. The architect accepted them in the `lane/rbl` review. The spec-writer entry of 2026-10-16 in the
[backlog](../../backlog.md) ("static follow-ups of `lane/rbl`") already asks for the re-tag. They are marked
**raised**, and no batch takes them:

| Row | Claim | Raised by |
|---|---|---|
| data-calc 17 | `EvalMissile`: type test, `missileId`/`lvl` defaults, context | calc-emu, `MISS_EvalCalc` with a NULL missile and with a missile unit |
| data-calc 21, 22, 28 | `max`, `rand`, the seed `rand` steps (unit `+0x20` or the missile frame's 8 bytes) | calc-emu, 45 000 calls |
| data-calc 29, 30 | the `DimReturns` cap, and "the cap was never reached in the run" (now reached 373 times; Phase 3 rewords it) | calc-emu |
| data-calc 35 (in part) | missile variables: codes 0–18 and 28–42, `lvl*2` of rows 245/246 | calc-emu. **Remainder:** codes 19–27 and the 12 `skill(…)` cells read unit state, so they are d-sim |
| rng-seeds 12 | draw counts of the object regions, unit proxies and quests before draw 5 | rng/0002: one draw each, draws 2, 3 (`NPCSTORE_CtlCreate`) and 4 (`QUESTS_InitGame`). Out of H5r |
| monsters-pool 5, 24 | later game-creation calls also step the game seed; the seed is shared | rng/0002, the same list. Out of S3a; Phase 3 cites rng/0002 |

That is 10 statements: 9 raised whole, and data-calc 35 in part. Three more rows changed because of `lane/rbl`:
- **items-quest-drops 1** (`QUESTS_ObjectOperate` dispatches by class; c, S2c). The static route it asked for was
  done: the function is object event 7, renamed `QUESTS_ObjectEvent`, and the Hellforge's slot 49 and event-7 waves
  are `[C]` ([items/0010 § 9](../../findings/items/0010-quest-drops.md#9-how-an-object-reaches-the-quest-scripts-the-operate-slot-and-object-event-7-backlog-2026-10-16-static)).
  The other object classes stay `[I]`. The row moves to **(b), H6e2**: a backtrace at `QUESTS_ObjectEvent` in the
  Wirt's body and quest-chest sessions that H6e2 already runs.
- **objects 47** (quest-object operates draw the quest seed) stays in S4a. Its evidence is the `QGS` recount per
  return address on `lane/rbl` (`QUESTS_GetSeed` → C), so S4a only cites that recount in objects/0001. The route text
  named the old function and was corrected (§ 9).
- **data-calc 2 and 19** (the potion caller `0x005BEDA0`; c, S1b). `lane/rbl` read it as code (data/0005 § 6,
  `[I]`), so S1b only states the second source: the static read plus the logged return address.

### 2.3 Other moves

- **data-calc 32** (`edma`, one stock cell; b, H3a) is **deferred**. After the moves above it is the only row left in
  H3a. It is unit state (a skill evaluation in play), and no other batch loads `calc.gdb`. If plan 0037 Phase 2
  evaluates an `edma` cell, it may log this row; otherwise the row stays `[I]`.
- **H5r is merged into H5c** (§ 5).

### 2.4 Totals after the moves

These totals include the review's moves of § 2.5. The deferred rows (data-calc 32, objects 5) have their own column.

| Cluster | I | a-logs | a-run | b | c | c-emu | raised | deferred | d-none | d-edit | d-sim | d-2c | d-owner | d-0032 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0a | 523 | 155 | 26 | 136 | 54 | · | · | · | 104 | 30 | 1 | 11 | · | 6 |
| 0b | 380 | 63 | 2 | 112 | 69 | 74 | 8 | 1 | 19 | 25 | 7 | · | · | · |
| 0c | 317 | 69 | 44 | 78 | 17 | · | 2 | · | 71 | 14 | 10 | 3 | 7 | 2 |
| 0d | 306 | 89 | 100 | 18 | 44 | · | · | 1 | 45 | · | 8 | · | 1 | · |
| **All** | **1 526** | **376** | **172** | **344** | **184** | **74** | **10** | **2** | **239** | **69** | **26** | **14** | **8** | **8** |

The breakdown by batch:
- **1 150 statements are batched:**
  - 634 in ten static batches;
  - 516 in twenty-one harness batches, including the forced H2c.
- **2 statements are deferred** (data-calc 32, objects 5).
- **10 are raised.**
- **364 are blocked (d):**
  - d-none 239;
  - d-edit 69;
  - d-sim 26;
  - d-2c 14;
  - d-owner 8;
  - d-0032 8.

### 2.5 Moves made by the Phase 0 review

The review (architect, 2026-10-16) moved 8 statements. The per-spec files keep the cluster's values for these rows;
this section and § 5 override them.

| Row | Was | Now | Why |
|---|---|---|---|
| monsters-stats 42, 46 (`UniqueDamageBonus` and `HireableBossDamagePercent` never read; 2) | b, H4b | **d-sim** (plan 0037) | Plan 0037 Phase 1 reads "the hireling and hireable-boss damage percents" on the attack path. A watchpoint in a monster-creation session cannot show "never read" while the combat code is unread; 0037·P1 settles it, and its Phase 2 logs it if a reader exists. |
| objects 5 (the revisit monster and item restores are not modelled; 1) | b, H5b | **deferred** | Raising it means modelling the inactive-unit restores of monsters/spawn and items in the objects checker: two subsystems' models, not a batch-sized logger or checker case. It stays `[I]` until a plan models the revisit. |
| items-properties 12, spec L403 and L416 (func 36 `randclassskill`, and the prose naming funcs 12 and 36 together; 2 of 3) | b, H2c | **d-edit** | Ruling 2 (§ 6): func 36's only carrier is *Hellfire Torch*, which stock single-player play never drops, so only edited data reaches it. L416 states both funcs; Phase 3 may split it and raise the func-12 half on H2c's evidence. Spec L390 (func 12) stays in H2c. |
| items-properties 21 (*Wraithflight* made ethereal twice; 1) | b, H2c | **d-edit** | Ruling 2 (§ 6): the claim is about the item the edited cell names, and its outcome passes through the TC-named build path, which stays `[I]` (uniques-sets § F). |

Rows not moved, with the review's reading:
- **save/d2s 1–3, 6, 18, 19** (one-client TCP/IP host): a TCP/IP game hosted by one client with no joiner is a
  one-client session. ADR-0008 governs a second client, so these rows stay (b) in H1b. save/d2s 72 (the corpse) stays
  in H1b; if scripted play cannot leave a corpse, the batch records a shortfall and the row becomes d-owner.
- **The 27 (c-emu) candidates of § 2.1** stay in their classes. Adding them would put S1e at 101, over the static cap.
  When S1e lands, its lane lists the candidates whose read set it can declare under ADR-0015 condition 2 as a
  proposed batch **S1f**, which the S1e review accepts or not.
- **The routes that rest on unchecked facts (§ 10 point 4)** stand as written. Each moves at its batch if the fact
  fails, and the batch section records the move.

### 2.6 Moves made by the batch reviews

Each Phase 1 or Phase 2 review records here the rows its batch returned to the inventory. As in § 2.5, the per-spec
files keep the cluster's values; this section and § 5 override them.

**S2a (review 2026-10-16, architect): 8 statements of items/tc.**

| Row | Was | Now | Why |
|---|---|---|---|
| items-tc 13 (`Picks` 0 stored as 1) | c, S2a | **d-none** | No loaded `treasureclassex` row has `Picks` 0 (852 rows); the route's own condition. |
| items-tc 15 (`Prob` < 1 dropped at load) | c, S2a | **d-none** | No stock item cell has `Prob` < 1 (3 404 cells). |
| items-tc 41 (classic skip, scan off the end) | a-logs, S2a | **d-none** | No observable for any table the loader builds: an expansion-only entry adds nothing to the classic sum, so a scan without the skip selects the same entry, and the last classic entry always stops the scan. Shown in items/0001 § Plan 0038 batch S2a and checked over 95 383 selections. |
| items-tc 74 (classic skip, run off the end, `version` reject) | a-logs, S2a | **d-none** | As row 41; and A2 flags every `version ≥ 100` entry expansion-only, so the classic scan never meets one. Raises stay d-edit, the Long Sword H2c. |
| items-tc 34 (negative-`Picks` stop; 2) | c, S2a | **b, H2a** | The stop is reachable on stock data, but only by the three `Countess` TCs (`Picks` −2, classic total 1) in a classic game. Route: a classic Countess kill on `tc-drops.gdb`. The `Picks = 0` half of L388 is d-none (row 13). |
| items-tc 58 (item seed from the game seed; classic `version` refusal) | a-logs, S2a | **b, H2b** | The `IC0` lines hold the item seed but not the game seed, so the route's condition fails. Route: log `game+0xD0` at `ItemCreate` entry and after `ItemSeedInit`. The classic refusal is d-none (row 74). |
| items-tc 68 (one creation call per item; game seed stepped) | a-logs, S2a | **b, H2b** | The game-seed steps need the same line as row 58. |

Net effect on § 2.4: a-logs −4, c −4, b +4, d-none +4. Static batches now hold 626 statements, harness batches 520
(H2a 17, H2b 21), and 368 are blocked (d-none 243).

**S4a (review 2026-10-16, architect): 12 statements of drlg.**

| Row | Was | Now | Why |
|---|---|---|---|
| room-tiles 4 (2), 14 (2), 28 (3), 37 (1) (merge row and orientation tables, 8/9 edge rule, remap, row −2, signed compares) | a-logs, S4a | **a-run, H5c** | The route's own fallback: none of the 39 096 logged bit-2 merges went through rows 0–5, returned on row −2 or met the 8/9 edge rule (drlg/0002 § Plan 0038 batch S4a). H5c needs walled levels where a remap happens. |
| warps 16 (pairing from `RoomNeighboursEnsure` per warp bit; Warp −1 marks) | a-logs, S4a | **b, H5c** | `WPR` is logged inside `WarpPairRoomFind` on success only. New piece: a line at `RoomNeighboursEnsure` (`0x0066C370`) with the room, its warp bits and each `WarpPairLink` call and outcome. |
| drlg/README 12 (no LvlPrest lookup tests `Expansion`) | a-logs, S4a | **d-none** | All 227 `Expansion` 1 records of `lvlprest` are Act V records, and a classic game builds no Act V level. |
| outdoor 10 (`PlaceFar` visits row `oy` and column `ox` twice) | a-logs, S4a | **d-none** | The strict `>` makes the second visit unable to change the result, ties included. |
| preset 5, the skip statement (`u.id = −1`, type 1 below DS1 version 5) | a-logs, S4a | **d-none** | No such entry in any of the 2043 DS1 files `lvlprest.bin` names. The row's other two statements are raised. |

Net effect on § 2.4: a-logs −12, a-run +8, b +1, d-none +3. Static batches now hold 614 statements, harness batches
529 (H5c 41), and 371 are blocked (d-none 246).
**S3a (batch 2026-10-16, reverser, `lane/s3a`; for the review): 30 statements of monsters/pool, spawn, special and
stats.** All were a-logs in S3a. The evidence is in the "Plan 0038 batch S3a" sections of
[monsters/0001](../../findings/monsters/0001-level-pool.md#plan-0038-batch-s3a-2026-10-16),
[0002](../../findings/monsters/0002-room-population.md#plan-0038-batch-s3a-2026-10-16),
[0003](../../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3a-2026-10-16) and
[0004](../../findings/monsters/0004-stats.md#plan-0038-batch-s3a-2026-10-16).
| monsters-pool 3 (`enabled` not tested) | a-logs, S3a | **d-none** | No Levels pool cell (831) names a disabled class. |
| monsters-pool 8 (classic Normal reads `mon`) | a-logs, S3a | **a-run, H4b** | The logged classic Normal levels (3, 4, 38, 103) and every level before 110 have `mon` = `nmon`, so the region seed does not separate them. Route: one classic Normal game start with `mon-pool.gdb` (its `MPR` lines cover levels 110–136). |
| monsters-pool 27 (duplicate test `tries = 0`) | a-logs, S3a | **c-emu**, S1f candidate | In 3040 regions `tries` never fell below 0, and a `≤ 0` model gives the same regions. `MonVariantRoll` reads only the entry, its MonStats2 record and the seed. |
| monsters-spawn 6 (the tick on a populated room) | a-logs, S3a | **b, H4b** | `RW0`/`RW1` are logged only for rooms with bit 0 clear. Piece: a line at the tick call 0x0052D1C4 / 0x0052D0F6 for every room. |
| monsters-spawn 10, 14, 26, 30, 33, 36 (3), 38, 39 (guards; 10) | a-logs, S3a | **d-none** | Each guard counted 0 over 2889 passes and 5516 creations; no snapshot had `nRooms` 0, no request a null room or radius 0. |
| monsters-spawn 8, 13, 29, 32, 34 (headers' tag mentions; 5) | a-logs, S3a | **d-none** | Mentions with no claim of their own (§ 3); Phase 3 rewords them. |
| monsters-spawn 45 (`lo ≥ hi`, no draw) | a-logs, S3a | **a-run, H4b** | Reachable: pool classes 141, 398, 659–661 have `minion1` with `PartyMin` = `PartyMax` (levels 34, 78, 88, 89, 91, 123, 127, 130). Route: a seeded hunt in one of them. |
| monsters-special 34 (rows 10, 11, 13–15 null) | a-logs, S3a | **a-run, H4a** | No applied list held them. Route as filed: Treehead WoodFist (`brute2`, 13). |
| monsters-special 41 (note on the `[I]` rows) | a-logs, S3a | **d-none** | A mention. |
| monsters-special 48 (placed bit stops a repeat) | a-logs, S3a | **a-run, H4a** | All 18 `SU0` lines have the placed bit 0. Route as filed: re-entry of a superunique level. |
| monsters-special 62 (fixed mods skip `ModEligible`) | a-logs, S3a | **d-none** | Every stock fixed mod passes `ModEligible` for its class except `thief`, which is dropped first. |
| monsters-special 65 (MonPlace `0x11`–`0x20`) | a-logs, S3a | **b, H4b** | The presets-window creations do not carry the MonPlace case. Piece: the `PM0` line for every `PresetMonSpawn` case. |
| monsters-stats 9, 11 (`MulDiv`'s other branches; 2) | a-logs, S3a | **c-emu**, S1f candidates | The only large-argument calls are 147 `MulDiv(v, 1, 2)`, where every branch agrees. `MulDiv` is pure. |
| monsters-stats 16 (hpregen overflow) | a-logs, S3a | **d-owner** | Only classes 704–709 (Uber Tristram) can pass the bound. |
| monsters-stats 26, 27 (53-bit precision, final truncation; 2) | a-logs, S3a | **d-sim** | Every creation-time stat-7 rescale is at full life, so the product is an integer (1085 calls); a fractional one needs a damaged monster (ADR-0014). |
Net effect on § 2.4: a-logs −30; d-none +18, a-run +4 (H4b 2, H4a 2), b +2 (H4b), c-emu candidates +3 (for the S1f
proposal of § 2.5, now 30), d-owner +1, d-sim +2. Static batches now hold 596 statements, harness batches 526 (H4a 31, H4b
47), and 389 are blocked (d-none 261, d-owner 9, d-sim 28).

## 3. Blocked rows, for the plan's open questions

- **d-2c, 14 statements** (items/tc 3, items/vendors 5, items/quest-drops 3, hirelings 1, player/creation 2). This is
  what accepting ADR-0008 would unlock now.
  - Partial rows add a few more halves: the trade part of sockets 22, the party half of player/creation 33, the
    n > 1 part of quest-drops 25.
  - Six save/d2s rows (1–3, 6, 18, 19) assume that a one-client TCP/IP host counts as one client. If the review
    rules otherwise, they become d-2c.
- **d-owner, 8 statements** outside the plan 0032 addendum:
  - ubermephisto, Baal Subject 2 and `poisonhit` (monsters/special and monsters/stats, 5);
  - the kill-experience clamp and the `ExpRatio` overflow (player/creation, 2);
  - the `worldstoneeffect` skip in the Worldstone Chamber (drlg/preset 1).
  - That is too few for an owner addendum of their own. The close may fold them into the plan 0032 addendum's
    sessions.
- **d-0032, 8 statements** (items/quest-drops 6, monsters/special 2: the Countess and the Cow King tails). They link
  the [backlog entry of the addendum](../../backlog.md) and no batch takes them.
- **d-sim, 26 statements.** They belong to plan 0037 or to a later ADR-0014 phase:
  - monsters/stats § H, the attack masks, the MonPlayerBonus attack callers, and (review, § 2.5) the unread
    `UniqueDamageBonus`/`HireableBossDamagePercent` rows 42 and 46;
  - the data/calc unit-state inputs, `blvl` among them;
  - hirelings `MERCAI_PickSkill`;
  - collision movement (7), and one row each in vendors and objects.
- **d-edit, 69 statements**, for example `evilhut`/`sparsePopulate`, the TC-named and upgrade-draw cells, forged
  socket packets, non-`eng` languages, and (review, § 2.5) func 36 and *Wraithflight*. § 2.1 lists the ones that
  emulation might still reach.
- **d-none, 239 statements:**
  - guards that stock data never fails, dead code and unreachable levels (133–136);
  - about 42 tag mentions in prose that make no claim of their own (0a 4, 0b 4, 0c about 25, 0d 9). Phase 3 rewords
    those with their referents.

## 4. Batch ids reconciled across clusters

Each cluster numbered its batches on its own. These ids collided or were left open, and the per-spec files were
corrected (§ 9):

| Cluster id | Final id | Why |
|---|---|---|
| 0c H6a (hirelings) | **H6f** | 0a uses H6a for the cube |
| 0c H6b (player) | **H6g** | 0a uses H6b for sockets |
| 0c "H1" share, 11 statements | **H1a** (hirelings 3, 30, 32, 33; player/creation 1, 8, 9, 11, 20, 34) and **H1b** (hirelings 24) | Loads of old-version, malformed and class-7 saves join the load batch. The merc header write on *Save and Exit* joins the play batch. |
| 0d "H6" (objects 48, 4 statements) | **H6e2** | The same `quests.gdb` sessions on tool-built quest saves operate the quest chests, Wirt's body, the item objects and the orifice |
| 0b H5r (rng/seeds) | **H5c** | Merged, § 5 (the files keep H5r; this README overrides) |
| 0b H3a | dissolved | § 2: three rows to S1e, one raised in part, one deferred |
| 0b H3b | **H3b** | Kept; there is no H3a |

## 5. Batch list

Kind: S = static (Phase 1, no slot, at most 100 statements); H = harness (Phase 2, at most 60 statements and 20
sessions, one logger family). Tiers are T1/T2/T3 statement counts. A static batch writes dated addenda to the named
runs, plus a "Plan 0038 batch S*n*" section in each finding. A harness batch writes `run:<date>-sweep-<slug>`.

### Static batches

| Batch | Stmts | T1/T2/T3 | Rows | Method | Record |
|---|---|---|---|---|---|
| **S1a** | 56 | 0/49/7 | save/d2s 5, 7–8, 11–16, 20, 24, 32, 45, 51, 58, 61, 63–64, 66, 69–71, 74–76, 79, 81, 84–87, 92–94, 96–101, 103–104, 109, 117, 119–121, 123–124, 128, 130–131, 135–138 | writer/reader pairs (rule 1); `d2s.py survey` over every game-written save (rule 2) | `findings/save`: addenda to run:2026-10-12-d2s-io, -10-14-props-forced, -10-16-calc |
| **S1b** | 76 | 7/53/16 | data/README 1; data/calc 1–2, 6–7, 18–19; data/excel 9–14, 19, 21, 23, 26, 28–31, 33–35, 38, 41–42, 45–49, 55, 57, 61–63, 67–68, 72–73, 75–78; data/strings 1, 3, 11, 21, 31, 33; rng 2, 4, 7; rng/seeds 1, 3, 11, 15–16 | the `tc.py` TC array against the tc-drops logs; item index ↔ code over kept item logs; archive precedence; `excel_bin.py survey`; strings, calc, seed-tree and rng-emu addenda | `findings/data`, `findings/rng` (addenda) |
| **S1e** | 74 | 0/4/70 | data/calc 4–5, 9–16, 20, 31 (6 of 7), 36–40; data/excel 16, 36–37, 40, 43–44, 51–53, 56, 60, 64, 66; data/strings 4–5, 10, 12, 14, 16–17, 20, 24–25, 32, 35; rng 3, 5; save/d2s 82, 122, 129, 133 | **(c-emu)**, ADR-0015: `tools/ghidra.sh emucall`/`emucalc` (from `lane/rbl`) on `CALC_Eval`, `CALC_Compile`, `SKILLS_CalcVar`, `SKILLS_DimReturns`, the calc entry points, `BITBUF_WriteClamped`, `EXCEL_FindCode`/`AddCode`, the excel cell parsers, the string-table lookups and `RNG_RangePow2Plus`, each against a `tools/` model. Each function's read set is declared, and each has a negative control. | `findings/data/experiments.md` **run:&lt;date&gt;-sweep-emu**; addendum to run:2026-10-11-rng-emu |
| **S2a** | 65 | 56/0/9 | quality 1, 5, 7, 10–11, 13–14, 18–19, 24–30, 33, 35; tc 3–5, 7, 12–16, 18–19, 21, 23–25, 28–36, 38–42, 48–52, 57–58, 61–62, 64, 66–69, 72–74 | `tc.py replay` (incl. `--quality model`) and `quality.py` over the kept tc-drops logs; classic counterfactual replays; xrefs; TreasureClassEx data checks | `findings/items`: addenda to run:2026-10-11-tc-drops, -10-13-quality, -10-14-uniques/-props |
| **S2b** | 58 | 48/0/10 | affixes 1, 3–4, 7–10, 15–16, 22, 27–28, 30, 34–35, 37; properties 1–2, 4–6, 8–9, 16, 18, 23–24; uniques-sets 3–6, 8–9, 12–13, 15, 20, 22–24, 27–29, 31–34, 36, 39–40, 42 | `items_chain.py`, `uniques.py`, `props.py`, `affixes.py` over ichain*, uniques-*, props*, quests-s*-cows; a new `ITEMS_RollStaffMods` checker case removes that oracle | `findings/items`: addenda to run:2026-10-15-items-chain, -10-14-uniques, -10-14-props |
| **S2c** | 86 | 1/64/21 | affixes 2, 11, 14; cube 6, 8, 10, 12–13, 17, 20–22, 24, 29, 45, 47, 49, 51–52, 55–56, 58; properties 19; quality 16; quest-drops 7–10, 14, 19–21, 28, 31, 37–38, 41, 47–49; sockets 2–6, 8, 14, 19–20, 25–28, 32, 34–36, 41–47; uniques-sets 1; vendors 3–4, 7–9, 11, 19–22, 24–28 | `cube.py`, `sockets.py`, `vendors.py`, `questdrops.py` over kept logs; a new `InvPlaceItem` case; second sources from save/d2s; xrefs | `findings/items`: addenda to run:2026-10-15-cube, -sockets, -vendors, -10-16-quest-drops |
| **S3a** | 69 | 32/13/24 | hirelings 4, 19, 26; monsters/README 1; player/creation 7, 10, 13–14, 26; pool 3–4, 8, 10–11, 13, 16–17, 20–22, 27–28; spawn 6, 8, 10, 13–15, 17, 21, 26, 29–30, 32–34, 36–39, 45–46, 54; special 3–4, 17, 21, 23, 28, 34, 39, 41, 48, 62, 64–65, 73; stats 2, 9, 11, 16, 25–27, 31, 36, 38 | new checks over monpool*, monspawn-s*, monspecial-s*, monstats-s*, berserkf-*, hire-run, player-run (`monpool.py`, `monspawn.py guard`, `monstats.py fpsens`, `hirelings.py`, `player.py`). A guard the logs never took goes to d-none and is not raised. | `findings/monsters`, `hirelings`, `player` (addenda) |
| **S3b** | 17 | 1/5/11 | hirelings 7–8; player/creation 16, 21, 36; pool 9, 23; spawn 1–2, 7, 41, 50, 52; special 43; stats 19, 30, 45 | second code paths; full-table checks of monstats2 `+0x025`, MonStats `SizeX` and reversed HP, MonProp, hireling.txt order, Experience `ExpRatio` | finding sections |
| **S4a** | 89 | 80/1/8 | collision 6–7, 12–13, 15–18, 20, 29, 31–33, 38, 41–44, 47, 49; drlg/README 6–9, 12, 14–16; maze 1, 3, 7–8, 16; objects 7–9, 11, 14, 28, 37, 47; outdoor 1, 6, 8, 10, 16; preset 1, 5, 7, 9–10, 16, 18, 20, 23–26, 28, 30, 38, 40; room-tiles 4–5, 8, 10, 12–14, 16, 18, 21, 24, 26, 28, 34, 37; warps 13–14, 16, 18 | `drlg.py gen/roomk`, `maze_replay.py`, `outdoor_replay.py`, `collision.py`, the objects checker, the `QGS` lines of run:2026-10-16-quest-drops | `findings/drlg`, `findings/objects` (addenda) |
| **S4b** | 44 | 9/0/35 | collision 2, 4, 10, 26, 39; drlg/README 11, 17; maze 2, 9; objects 1–2, 22, 25, 43; outdoor 3, 5, 19; preset 3, 6, 8, 11, 21, 27, 29, 33–34, 36–37, 39, 41; room-tiles 3, 7, 9, 17, 19–20, 23, 25, 29, 32, 35; warps 7, 20 | xrefs with a second tool, writer/reader pairs, full-table data checks, a `rngcallgraph` rerun with an r2 LCG scan | finding sections |

### Harness batches

Sessions are the clusters' estimates. A lane that counts more than 20 before its first session splits the batch with
a letter suffix and its own run id, as the plan requires.

| Batch | Slug | Stmts | T1/T2/T3 | Rows | Recipe, logger and checker; new pieces | Record | Sessions |
|---|---|---|---|---|---|---|---|
| **H1a** | `d2s-load` | 45 | 0/2/43 | save/d2s 9–10, 17, 22–23, 26–30, 36, 38, 44, 46–47, 49–50, 52–54, 59, 62, 65, 68, 80, 90–91, 105–107, 126, 132, 139–140; hirelings 3, 30, 32–33; player/creation 1, 8–9, 11, 20, 34 | `d2s-io.gdb` + `d2sio.py check`. Tool-built saves from `d2sio_saves.py`: bad magic or version, wrong name, class 7 and 8, act 5, status mismatches, waypoint markers, out-of-range unique and set ids, legacy v94 and versions 71 and 87 (builder support needed), item version < 93, ear, personalized, realm, > 8 KiB, checksum and size wrong; `MercMF` loaded | `findings/save/experiments.md` | ~18 |
| **H1b** | `d2s-play` | 46 | 0/22/24 | save/d2s 1–4, 6, 18–19, 21, 25, 31, 33–35, 37, 39–43, 48, 55–57, 60, 72–73, 77–78, 83, 88, 102, 108, 110–116, 118, 125, 127; hirelings 24 | same family. A one-client TCP/IP host, weapon swap, hotkeys, the hirelings mercenary saves (write side, dead flag), iron golem, corpse, runeword, the `questdiffcheck` item, `maxhp`/`maxmana` and poison items, the bit-13 case, and section writer, reader and join breakpoints. **Also:** load `questrewards` and `questrewardsh` (built `246515c5…`, `14c28526…`; backlog 2026-10-16, archivist `lane/abl`) and pin both in `tools/test_d2s.py` with the run id, as the plan 0032 recipes were pinned | `findings/save/experiments.md` | ~14–17 |
| **H2a** | `items-tc` | 17 | 10/0/7 | quality 20, 22–23; tc 1–2, 11, 22, 34 (2, from S2a), 37, 45, 47, 59–60, 70–71 | `tc-drops.gdb` + `tc.py`. New lines: the caller, gold (stat 14), the MonDeathDrop exit. A Find Item barbarian, `/players 8` host and chests, Hell mfnecro, skeleton or Valkyrie kills; a classic Countess kill (tc 34, § 2.6) | `findings/items/experiments.md` | ~6 |
| **H2b** | `items-chain` | 21 | 4/0/17 | affixes 5, 13, 17, 19–21, 24; properties 7, 20; tc 58, 68 (from S2a); uniques-sets 7, 10, 35 | `items-chain.gdb` + `items_chain.py both`. A classic hunt (classicsorc) and a long Hell hunt. New line (tc 58, 68, § 2.6): `game+0xD0` at `sub_00558D90_ItemCreate` entry and after `sub_00552E90_ItemSeedInit` | `findings/items/experiments.md` | 6–10 |
| **H2c** | `items-forced` (id ends `-forced`) | 7 | 0/0/7 | properties 12 (spec L390 only), 14–15; tc 10, 55–56 | **forced, admitted with conditions** (§ 6): `items-chain.gdb` + `tc.py`, `props.py` on a loose `treasureclassex.bin` under `-direct`; two edits (classic throwables; TC-named uniques), each its own `-forced` session set | `findings/items/experiments.md` | few |
| **H3b** | `data-load` | 25 | 0/16/9 | data/README 2–5; data/excel 1–8, 17–18, 20, 24–25, 27, 50, 71, 74; data/strings 2, 6, 22, 29 | **new** `excel`/startup logger that also sources `strings.py`. **First piece (review ruling 3):** a `d2run.py` mode that has gdb on the game before `DATATBLS_LoadAll`, built and tested off-slot; if it cannot be made to work, the 9 startup rows are a recorded shortfall and stay `[I]` (they have an observable, so not d-none). Covers `FindFile`, loose files without `-direct`, `-txt`, record-byte dumps, the rare-item hover, `STRTABLE_Unload` | `findings/data/experiments.md` | ~6 |
| **H4a** | `monsters-a` | 31 | 0/13/18 | pool 12; spawn 5, 11, 47–49; special 9–10, 25, 30–31, 34 (from S3a), 35, 38, 46, 48 (from S3a), 50–52, 54–56, 58–60, 68–69; stats 7, 18, 21 | `mon-stats.gdb` with `d2pilot.py` wp, `--descend`, `hunt`, `objop`: Radament, the Travincal council, the Chaos seals, Shenk, Nihlathak, Blood Raven, Andariel, Izual, a `flyingscimitar` level. The Ancients (b) need a quest-open recipe | `findings/monsters/experiments.md` | ~10 |
| **H4b** | `monsters-b` | 47 | 22/1/24 | hirelings 34; pool 1, 7, 8 (from S3a), 19; spawn 3, 6 (from S3a), 12, 42–45 (45 from S3a), 51; special 1–2, 5–7, 11, 15–16, 18, 20, 27, 29, 65 (from S3a), 66–67, 71–72, 74; stats 5, 13–14, 17, 20, 23, 40, 44 | `mon-stats.gdb` extended (skill list, aura id and level, client names, restore lines; from S3a: the tick line for every room, `PM0` for every MonPlace case) plus seeded-pool hunts picked with `monpool.py pool` (from S3a: a level holding class 141, 398 or 659–661), a `/players 8` `MercNova` session, and (from S3a) a classic Normal game start with `mon-pool.gdb` | `findings/monsters/experiments.md` | ≤ 20 |
| **H5a** | `drlg-links` | 21 | 16/0/5 | maze 4–5, 15; preset 22; warps 3, 5–6, 8–9, 11–12 | `drlg-maze.gdb` (LNK0/LNK1/LK27) + `drlg.py gen`; map seeds chosen offline with the link-builder model; `-seed N -act A` starts and one Barracks entry | `findings/drlg/experiments.md` | few |
| **H5b** | `objects` | 32 | 12/2/18 | collision 27, 37; objects 3–4, 6, 13, 15–17, 19–20, 23, 26–27, 35–36, 38–42, 45–46, 49–52 | `objects.gdb` + the objects checker, `d2pilot.py objop`, seeds from the populate model; the casket group and the orientation-2 shrine (plan 0023 ruling); new `OBJTRAP_ObjectCreate` fire lines and revisit restores | `findings/objects/experiments.md` | ≤ 20 |
| **H5c** | `roomk` | 41 | 33/0/8 | drlg/README 1–3, 5, 10; preset 31–32; room-tiles 1–2, 4 (2), 14 (2), 15, 27, 28 (3), 30–31, 33, 37, 38; warps 1, 16, 19; **rng/seeds 2, 4–10, 14** (ex H5r); room-tiles 4, 14, 28, 37 and warps 16 from S4a (§ 2.6) | `drlg-roomk.gdb` and `collision.gdb` (LevelUnload, RoomTilesRelease, TINIT-exit flags, `LI0` caller, the act callback, WarpExitPos), plus `seed-tree.gdb` + `rng.py seedtree` (act-seed steps in `LevelLinkBuild`, `R+0x28`/`R+0x60` and `T+0x18`/`+0x20` at activation, flags at `0x0052D1C9`, `LEVEL` caller, client `UnitInit` (x, y), one `-seed -2147483648` session). rng/0002 cites the record. From S4a (§ 2.6): a walled level whose bit-2 merges go through the remap rows 0–5, the row −2 return and the 8/9 edge (counted by `sweep_s4a.py roomk` on the batch's logs), and a `RoomNeighboursEnsure` line at `0x0066C370` (room, warp bits, each `WarpPairLink` call and outcome) | `findings/drlg/experiments.md` | ~10 |
| **H5d** | `collision` | 16 | 6/0/10 | collision 1, 5, 8–9, 11, 19, 21, 24, 30, 36, 45–46 | `collision.gdb` + `collision.py`: tombs (228), Act III (334), Act V (298, 528, baaltaunt), a non-town `Position` level, `spawnCol` 1, ground items, an entry-flag `0x80` cell | `findings/drlg/experiments.md` | ~8 |
| **H5e** | `drlg-mazes` | 22 | 16/0/6 | maze 6, 10–12; outdoor 7, 11, 13–14, 20; preset 2, 12–14 | `drlg-outdoor.gdb` (with the maze lines) + `drlg-preset.py`, `maze_replay.py`, `outdoor_replay.py`, `drlg.py gen`: unreached maze levels from waypoint saves, outdoor rare branches on chosen seeds, the Blood Moor centre monster | `findings/drlg/experiments.md` | 16–17 |
| **H6a** | `cube` | 26 | 0/16/10 | cube 1, 7, 15–16, 25, 32, 36, 38–40, 43–44, 53–54 | `cube.gdb` + `cube.py`; new `.plan` files (upgrades, eth/strip rows, ethereal or socketed inputs, repair, recharge, `qty`, Staff of Kings, Khalim's Will, unsocket, the cow portal outside level 1 and in classic); a UnitSetEvent line | `findings/items/experiments.md` | ≤ 20 |
| **H6b** | `sockets` | 23 | 0/18/5 | sockets 1, 9–10, 12–13, 16–18, 21, 29, 38 | `sockets.gdb` + `sockets.py`; child x/y and cursor lines; sock-refuse and sock-rw plans | `findings/items/experiments.md` | ≤ 20 |
| **H6c** | `vendors` | 13 | 0/11/2 | vendors 2, 5, 12, 14–15, 18, 29–30, 32–34, 36 | `vendors.gdb` + `vendors.py`; reopen store or gamble, Asheara's hire list first, walk out of town, level-up between opens, buy and sell; saves at clvl ≤ 9, ≥ 96, 99 in Hell | `findings/items/experiments.md` | ≤ 20 |
| **H6d** | `quest-b6` | 17 | 10/5/2 | quest-drops 11, 13, 16, 18, 22, 25, 27; tc 26–27; uniques-sets 21 | `quests.gdb` + tc-drops, `tc.py` b6_model, `questdrops.py`: Andariel or Duriel killed by a mercenary or summon, Diablo and Baal, Warriv's report, questfresh in Nightmare, Hell and classic, the forge with a stat-356-1 hammer, the unique restore path | `findings/items/experiments.md` | ≤ 20 |
| **H6e1** | `quest-npc` | 22 | 0/20/2 | quest-drops 2, 4–5, 32, 39–40, 42–46, 50–51 | `quests.gdb` + `d2pilot.py npc`: given items and service branches and refusals | `findings/items/experiments.md` | ≤ 20 |
| **H6e2** | `quest-items` | 24 | 0/23/1 | quest-drops 1, 30, 33–35; objects 48 | `quests.gdb` with `objop`/`hunt` on tool-built quest saves: the 16 quest items, chests, duplicates, the item-move gate; the quest objects ride the same sessions; a backtrace at `QUESTS_ObjectEvent` (quest-drops 1). objects/0001 cites the record | `findings/items/experiments.md` | ~20, at the cap |
| **H6f** | `hirelings` | 23 | 0/17/6 | hirelings 1–2, 5–6, 9–10, 14–18, 20–21, 23, 25, 27–29, 31, 35–37 | `hirelings.gdb` + `hireling_sessions.py`: Asheara's trade first, Greiz, classic lists, the free mercenary, the level floor, quest, level and gold gates, stash payment, `MERC_AddExp`, `merc_saves.py` saves, resurrection | `findings/hirelings/experiments.md` | ≤ 20 |
| **H6g** | `player` | 16 | 0/7/9 | player/creation 2–4, 12, 18, 22–23, 25, 27–30, 32–33, 35 | `player.gdb` + `player_sessions.py`: death loss, a stat point, stat 85, the level-99 cap and a level-98 save, the capped grant (trigger read statically first), client `+0x3D4`, the belt column, the monster's experience at the kill | `findings/player/experiments.md` | ≤ 20 |

**Logger-family conflicts.** Two batches may run at once only when they share no recipe save, logger file or checker
under edit. Inside one family the batches run one after the other:
- H1a and H1b;
- H2a, H2b and H2c;
- H4a and H4b;
- H5a, H5c, H5d and H5e (H5c edits `collision.gdb`, which H5d uses);
- H6d, H6e1 and H6e2.

Batches of different families may pair, for example H5c with H4b.

## 6. Forced-run candidates, ruled at the review

Only cluster 0a proposed a forced batch, **H2c**, with two candidates. Clusters 0b, 0c and 0d proposed none:
- Their tool-built saves are ADR-0003 inputs under ADR-0013 § Neutral, not forced runs.
- Every 133–136 path is d-none by the plan 0027 Phase 3 ruling.

The table keeps the cluster's proposal; the rulings follow it.

| # | Claims (rows) | Table and cells to edit | Where the ADR-0013 read lists must stand before the run | Stock companion | Point ruled on |
|---|---|---|---|---|---|
| 1 | Classic throwables: `THROW_RETRIES` 10 and the Long Sword `lsd` fallback (tc 10 ×2, 55, 56; 4 statements) | `treasureclassex.bin`, loose under `-direct`: the `Item1..n` and `Prob1..n` cells of one classic Act I TC a fixed recipe reaches (for example `Act 1 Cpot A`), set to classic throwables only; `Picks` and `NoDrop` only if the stock row needs it (see the ruling) | [items/0001 § 5](../../findings/items/0001-tc-resolution.md#5-the-pick-loop--tc_resolvedrops-0x0055a6d0) and [§ 8](../../findings/items/0001-tc-resolution.md#8-item-pick-and-hand-off-0x0055ac5f0x0055af59) | the refund itself, already `[C]` (run:2026-10-13-quality, at most 3 refunds per call in 485 classic calls) | Does the code of the counter and the `lsd` substitution read an edited cell? |
| 2 | TC-named uniques: funcs 12/36 put the roll in the param, func 23 ethereal, func 24, and Wraithflight made ethereal twice (properties 12 ×3, 14, 15, 21; 6 statements) | `treasureclassex.bin`: the `Item` cells of the Hell TCs that the run:2026-10-15-uniques-tcnamed-forced recipe reaches, naming *Ormus' Robes*, *Hellfire Torch*, *Ethereal Edge*, *Wraithflight* and a func-24 unique | [items/0006 § 4](../../findings/items/0006-properties.md#4-the-handlers-per-func) (the handlers read `Properties`, `UniqueItems` and the item's stats) and [items/0004 § 6](../../findings/items/0004-uniques-sets.md#6-a-tc-cell-that-names-a-unique-or-a-set-item) (the unique selection reads the named cell and stays `[I]`) | *Ormus' Robes* and the ethereal uniques only if a long Hell hunt meets one; **none for *Hellfire Torch*** (Uber Tristram cannot open) | Is a claim whose subject the edited cell names barred? |

**Ruling 1: admitted (4 statements stay in H2c).** The code the claims describe is `0x0055AE6E`–`0x0055AEC2`
(items/0001 § 8, lines 506–508 of the excerpt). It reads the picked item's type through `ITEMS_GetType` and
`ITEMTYPES_IsThrowable` (ItemTypes `+0x10`, data-indexed, so the whole `Throwable` column, which is stock), the
call-local `throwRetries`, the game's expansion flag, and the Items record of `lsd` through `ITEMS_GetByCode`. Its one
write to resolver state is `f->picksLeft++`, an increment of the frame's copy that does not depend on its value. None
of this reads a TreasureClassEx cell: `Picks` and `Prob` are read by the pick loop, which is the decision code, and the
claims say nothing about it. The edited cells choose *which* item is picked, the way the ItemRatio edits chose the
quality before the builders ran; the claims are about what happens to any throwable once picked, not about the pick.
Conditions:
- Before the run, items/0001 § 8 records the per-claim read list above, including the three callees, and shows that
  none of them reads `g_pTreasureClassEx` or a runtime TC entry.
- Because a refunded pick is not consumed, `Picks` needs no edit unless the chosen stock row has `Picks` ≤ 0 (a
  different pick mode) or a `NoDrop` that ends the call early. Edit those cells only if needed, and list every changed
  cell with `excel_bin.py bindiff`.
- Raised are only the bound of 10 and the `lsd` substitution (tc 10, 55, and the Long Sword half of 56). The refund's
  effect on later picks keeps its stock evidence. No count of throwables per call is a claim. The `version ≥ 100`
  half of tc 56 is d-none (A2 excludes those entries), so tc 56 as a statement is raised only if Phase 3 splits it.
- The stock companion is run:2026-10-13-quality, which already logged the refund branch.

**Ruling 2: split (3 statements stay in H2c, 3 become d-edit).** ADR-0013 bars a claim whose code reads an edited cell
or whose subject the edited cells name. The edited `Item` cells choose the UniqueItems row, as the ItemRatio edits
chose the quality. After that choice, the func handlers read stock `Properties` and `UniqueItems` rows and the item's
stats. A handler claim is a map from (property row, item state at entry) to the stats written, so its subject is the
handler, not the unique.
- **Admitted: func 12 (properties 12, spec L390), func 23 (14) and func 24 (15).** Each has a stock carrier that a
  stock drop can make (*Ormus' Robes*; *Ethereal Edge*, *Ghostflame*, *Shadowkiller* and the other ethereal uniques;
  the func-24 unique the lane picks must also be stock-droppable).
- **d-edit: func 36 (properties 12, spec L403) and the prose L416 that states funcs 12 and 36 together.** Func 36's only
  carrier is *Hellfire Torch*, which stock single-player play never drops. A claim only edited data reaches stays
  `[I]` (ADR-0010, kept by ADR-0013). Phase 3 may split L416 and raise its func-12 half.
- **d-edit: *Wraithflight* made ethereal twice (properties 21).** Its subject is the unique the edited cell names,
  and the outcome (the item's ethereal state and durability after both writes) passes through the TC-named build
  path, which stays `[I]` (uniques-sets § F).
- Conditions:
  - ADR-0013's third negative consequence: the props logger records each handler's entry state (the item's flags and
    the stats the handler reads) so that the input is shown, not assumed stock.
  - Before the run, items/0006 § 4 records the read list of funcs 12, 23 and 24 and their callees (the stat-list
    writer included), cell by cell.
  - The stock companion is the property dispatch logged on stock items in run:2026-10-14-props and
    run:2026-10-14-uniques (the same `g_PropFuncTable` path). H2b's long Hell hunt also checks for a stock func-12,
    23 or 24 carrier, and the record says whether it met one.
- Funcs 12, 23 and 24 are small, but they write through the stat-list code, so (c-emu) is not offered instead. If the
  H2b lane finds the writer's read set declarable, it may propose them for S1f.

## 7. Priority order

The plan's rule is T1 statements first, then T2. Ties go to the larger batch, then to the one with fewer new pieces.
Static and harness batches use different resources (Ghidra copies against slots), so each has its own queue.

**Static (Phase 1; parallel copies allowed):**

| Rank | Batch | T1 | T2 | Stmts |
|---|---|---|---|---|
| 1 | S4a | 80 | 1 | 89 |
| 2 | S2a | 56 | 0 | 65 |
| 3 | S2b | 48 | 0 | 58 |
| 4 | S3a | 32 | 13 | 69 |
| 5 | S4b | 9 | 0 | 44 |
| 6 | S1b | 7 | 53 | 76 |
| 7 | S2c | 1 | 64 | 86 |
| 8 | S3b | 1 | 5 | 17 |
| 9 | S1a | 0 | 49 | 56 |
| 10 | S1e | 0 | 4 | 74 |

**Harness (Phase 2; queue rules of the plan: 0037·P2 first, never more than two harness lanes, never slot 0):**

| Rank | Batch | T1 | T2 | Stmts | Note |
|---|---|---|---|---|---|
| 1 | H5c | 33 | 0 | 41 | logger edits (roomk, collision, seed-tree), made and regression-checked off-slot; +9 from S4a (§ 2.6), one more line (`RoomNeighboursEnsure`) |
| 2 | H4b | 22 | 1 | 47 | logger extension; pairs with H5c; +4 from S3a (§ 2.6) |
| 3 | H5e | 16 | 0 | 22 | no logger change; after H5c (same family) |
| 4 | H5a | 16 | 0 | 21 | no logger change; after H5e |
| 5 | H5b | 12 | 2 | 32 | objects family; may pair with any DRLG batch |
| 6 | H6d | 10 | 5 | 17 | |
| 7 | H2a | 10 | 0 | 17 | +2 from S2a (§ 2.6) |
| 8 | H5d | 6 | 0 | 16 | after H5c (`collision.gdb`) and H5a |
| 9 | H2b | 4 | 0 | 21 | +2 from S2a (§ 2.6) |
| 10 | H6e2 | 0 | 23 | 24 | at the session cap |
| 11 | H1b | 0 | 22 | 46 | includes the reward-recipe loads |
| 12 | H6e1 | 0 | 20 | 22 | |
| 13 | H6b | 0 | 18 | 23 | |
| 14 | H6f | 0 | 17 | 23 | |
| 15 | H6a | 0 | 16 | 26 | |
| 16 | H3b | 0 | 16 | 25 | the `d2run.py` start mode first (ruling 3) |
| 17 | H4a | 0 | 13 | 31 | after H4b (same family); +2 from S3a (§ 2.6) |
| 18 | H6c | 0 | 11 | 13 | |
| 19 | H6g | 0 | 7 | 16 | |
| 20 | H1a | 0 | 2 | 45 | after H1b (same family) |
| 21 | H2c | 0 | 0 | 7 | forced, admitted with the § 6 conditions; after H2b (same family) |

**Ruling 3 (order).** H5c stays ahead of H5e and H5a. It has the most T1 statements and the fewest sessions of the
three (about 10, against 16–17 for H5e), and it unblocks H5d. Its logger edits are static work: the lane makes them,
re-runs the existing `drlg-roomk`, `collision` and `seed-tree` checkers on their original logs with 0 mismatches,
and only then takes a slot. A slot is the scarce resource, not a logger edit. **H3b** keeps its rows as (b): a
`d2run.py` mode that puts gdb on the game before the tables load is a harness piece of the ADR-0003 kind, like a new
logger, and changes neither game code nor data. Rows that need it have an observable, so they are not d-none. The
lane builds the mode off-slot first. If it cannot, the 9 startup rows are a shortfall and stay `[I]`.

**Concurrency of static batches.** Static batches may run in parallel Ghidra copies, except where two would write the
same run record or finding section:
- S2a and S2b both write addenda to run:2026-10-14-uniques and run:2026-10-14-props, so S2b starts after S2a merges;
- S4a and S4b write the same drlg and objects findings, so S4b follows S4a;
- S1a, S1b and S1e are independent of S2–S4 and of each other, apart from the shared `findings/data` file of S1b and
  S1e. These two merge one at a time.

### First batches to run (review, 2026-10-16)

0037·P2 has not started (plan 0037 has closed only its Phase 0), so 0038 may use **two harness lanes** now. When 0037·P2 starts, it
takes its two slots and the running 0038 batches finish their current session, record what they have, and stop. Each
prompt gives the slots, and slot 0 is never used.
- **Static, first wave (parallel):** S4a and S2a. **Second wave:** S2b (after S2a merges) and S3a. Then S4b (after
  S4a), S1b, S2c, S3b, S1a and S1e, any two or three at a time within the concurrency rule above.
- **Harness, first pair:** H5c and H4b on two slots, after H5c's logger edits pass their regression checks. **Next:**
  H5e after H5c, then H5a; H4a after H4b. H5b may take whichever slot frees first after that.

## 8. Caps

- **Static, at most 100 statements:** every S batch fits. The largest is S4a at 89. 0d split S4 into S4a and S4b (133
  statements in all).
- **Harness, at most 60 statements and 20 sessions:** every H batch fits on statements. The largest are H1b (46),
  H1a (45) and H4b (43).
  - On sessions, H6e2 (about 20) and H1a (about 18) are near the cap.
  - 0a split H6e into H6e1 and H6e2 by session count.
  - If either batch counts more than 20 sessions before it starts, it splits again, H6e2 by act or H1a into
    malformed and old-version saves, each part with its own run id.
- **Batches under 10 statements:**
  - **H3a** (5) is dissolved by the moves of § 2: three rows go to S1e, one is raised in part and one is deferred.
  - **H5r** (10, then 9 once rng-seeds 12 was raised) is merged into **H5c**. The reasons:
    - its `seed-tree.gdb` lines watch the same room activation and level creation as H5c's new `drlg-roomk` lines;
    - rng/seeds 9 already needs the `drlg-roomk` logger;
    - the plan's H5 row counts the DRLG loggers as one family.
  - The **0c H1 share** (11) and the **0d H6 share** (4) were merged into H1a/H1b and H6e2 (§ 4).
  - **data-calc 32** (1) is deferred (§ 2.3).
  - **H2c** has 7 statements after ruling 2 and stays its own batch, because forced runs never share a run id with
    stock sessions.
  - **objects 5** (1) is deferred (§ 2.5).

## 9. Fixes made to the per-spec files

Only errors were fixed. Classes and routes the clusters chose are unchanged; § 2 records the moves.

- [items-tc.md](items-tc.md) rows 34 and 48 had unescaped `|` inside the cells (`|Picks|`, `max(1,|picks|)`). That
  split the rows into 11 cells and broke the table. Now escaped.
- [items-tc.md](items-tc.md) § Forced-run candidate named "rows 10, 51 and 52". The H2c rows are 10, 55 and 56.
- Batch ids changed per § 4:
  - [hirelings-README.md](hirelings-README.md): H6a → H6f; H1 → H1a or H1b, including the routes that named the
    batch.
  - [player-creation.md](player-creation.md): H6b → H6g; H1 → H1a.
  - [objects-README.md](objects-README.md) row 48: H6 → H6e2.
- [objects-README.md](objects-README.md) row 47's route said the `QGS` lines sat "under QUESTS_ObjectOperate". That
  function is not the operate route (renamed `QUESTS_ObjectEvent`, `lane/rbl`), so the route now reads per return
  address.

## 10. Points for the Phase 0 review

Rolled up from the four cluster reports. **All ruled at the review (2026-10-16):** 1 accepted, the 27 candidates
left for an S1f proposal (§ 2.5); 2 ruled in § 6; 3 one client (§ 2.5); 4 the routes stand and move at their batch;
5 objects 5 deferred (§ 2.5), rng-seeds 11's unhit callers go to H5c; 6 and 7 accepted as written; 8 and 9 are for
Phase 3 and the close.

1. **The (c-emu) class and the 32 reclassified statements** (§ 2.1), and whether any of the 27 candidates should
   join S1e now.
2. **The forced candidates** (§ 6): two rulings.
3. **One-client TCP/IP host** (save/d2s 1–3, 6, 18–19): does it count as one client, or are these rows d-2c? The
   corpse row (save/d2s 72) may need owner play.
4. **Routes that rest on facts nobody has checked.** If a fact fails, the row moves at the batch:
   - **0a:**
     - tc 669/768 and uniques-sets 175/511 (spec lines) assume the IC0/ICX lines hold the game seed; if not,
       → b;
     - quest-drops 47 falls back to H4 if no boss class is in the monpool logs.
   - **0c:**
     - pool 1 (the `GameCreateA` trigger may be d-2c);
     - player/creation 2 and 29 (the `ExpGrantCapped` trigger);
     - stats 19 (whether any MonStats row has a reversed HP range);
     - spawn 43 (tentaclehead may be preset-only);
     - special 64 (placed-bit repeats in the kept logs).
   - **0d:**
     - the a-logs rows that need tile pointers in `TL`/`CB`, the merge-table branches in the 69 activation dumps,
       and `Expansion` 1 LvlPrest records in classic sessions; if missing, → a-run in the named H5 batch;
     - the c rows that end as d-none if the data check finds no case (the 40-candidate cap, the (10, 0, 0)
       fallback, the "0" DT1 cell, size patterns above 1, zero-size `HasCollision` objects).
5. **Possible reclassifications:**
   - objects 5 (the revisit monster and item restores) is (b) in H5b but needs monsters/spawn and items modelling;
     0d suggests moving it out.
   - rng-seeds 11 (S1b) sends the callers the logs never hit to H5r, which is now H5c.
6. **Duplicates across clusters, one check each:**
   - save/d2s 83 and 102 are the same claim as items/sockets-runewords § G (the runeword u16);
   - data/excel 75 duplicates sockets-runewords L99 (runes `+0x82`);
   - data/excel 71 and data/strings 21 are one S1b check.
   - The batch reached first does the check, and the other cites it.
7. **Handoffs after the review:**
   - data/excel 24 and 27 need addenda to run:2026-10-15-cube-saves, a `docs/formats/experiments.md` record the
     archivist owns. A backlog entry is needed when S1b starts.
   - H3b needs a `d2run.py` start mode, a tooling piece for the reverser.
8. **Spec text, for Phase 3:**
   - items/tc B2–B6 says "no Hell call was recorded", but four runs replayed Hell calls (now an a-logs row in S2a);
   - about 42 statements are tag mentions in prose;
   - several statements mix reachable and unreachable parts and need splitting at re-tag:
     - tc L223, L244, L559, L657, L873, L876;
     - sockets L268;
     - quest-drops L392, L762;
     - cube L331/349;
     - outdoor L983;
     - room-tiles L635;
     - maze L434–452;
     - collision L441.
9. **Research map:** the rows for monsters/spawn (map 107/61/6, spec 109/64/6), monsters/special (102/85/7 against
   104/91/4) and drlg/warps (86/35/6 against 90/31/5) are stale. The architect updates them with the Phase 3 counts.
