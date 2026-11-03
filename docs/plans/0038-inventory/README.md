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

**After the batch reviews (§ 2.6: S2a, S4a, H5c, S2b, S3a, S4b, S1b, H4b, S2c, S3b, plan 0039 P1a, S1a, H5e; recomputed
once at the H5e review).** The reviews move 92 statements between classes; the per-cluster rows above keep the
clusters' values.

| Moves | a-logs | a-run | b | c | c-emu | raised | deferred | d-none | d-edit | d-sim | d-2c | d-owner | d-0032 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S2a | −4 | · | +4 | −4 | · | · | · | +4 | · | · | · | · | · |
| S4a | −12 | +8 | +1 | · | · | · | · | +3 | · | · | · | · | · |
| S2b | −9 | +1 | +2 | · | · | · | · | +6 | · | · | · | · | · |
| S3a | −30 | +4 | +2 | · | +3 | · | · | +18 | · | +2 | · | +1 | · |
| S4b | · | +1 | · | −5 | +1 | · | · | +3 | · | · | · | · | · |
| S1b | −1 | · | · | · | · | · | · | +1 | · | · | · | · | · |
| H4b | · | · | −2 | · | · | · | · | +1 | · | · | · | +1 | · |
| S2c | −8 | +5 | +2 | −2 | · | · | · | +3 | · | · | · | · | · |
| S3b | · | +2 | · | −2 | · | · | · | · | · | · | · | · | · |
| P1a (0039) | · | −11 | · | · | · | · | · | · | +11 | · | · | · | · |
| S1a | · | · | +2 | −2 | · | · | · | · | · | · | · | · | · |
| H5e | · | · | · | · | · | · | · | · | · | · | · | · | · |
| **All, now** | **312** | **182** | **355** | **169** | **78** | **10** | **2** | **278** | **80** | **28** | **14** | **10** | **8** |

- **1 092 statements are batched:** 555 in static batches (a-logs 312, c 169, and the 74 c-emu of S1e) and 537 in
  harness batches (a-run 182, b 355).
- **4 are c-emu awaiting the S1f proposal** (pool 27, stats 9 and 11 from S3a; preset 6's second statement from S4b).
- **2 are deferred, 10 raised, 418 blocked** (d-none 278, d-edit 80, d-sim 28, d-2c 14, d-owner 10, d-0032 8).

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

**H5c (review 2026-10-16, architect): no class moves; two outcomes recorded here.**

| Row | Was | Now | Why |
|---|---|---|---|
| rng-seeds 6 (seed ≥ 2³¹ given as a negative decimal) | a-run, H5c | **contradicted, Phase 3 correction** | Not a raise. The command-line parser stops a switch's text at the next `-` (`0x00405784`, read with r2 at the review), so `-seed -2147483648` gives no override (s9), and `2147483648` saturates at `0x7FFFFFFF` (s10). rng/0002 marks the old `[I]` contradicted; the spec-writer rewrites step note 2. |
| room-tiles 4 (2), 14 (2), 15 (2), 28 (3), 30 (1), 37 (1) (merge remap rows 0–5, row −2, the 8/9 edge rule, signed compares, orientation 3) | a-run, H5c | **a-run, shortfall; S1f candidates** | No remap in 50 586 stock merges (S4a 39 096, H5c 11 490). The class stays until the S1e lane's S1f proposal (§ 2.5) says whether `Bit2TileMerge`'s read set can be declared under ADR-0015. A forced run cannot back `[C]` (ADR-0013: the edit would be the wall cells the merge reads). Ruling in the plan log. |

Room-tiles 27 is raised in part (the level-133 part is d-none, as its route said). § 2.4 and § 5 do not change.

**S2b (review 2026-10-16, architect): 9 statements of items/affixes, items/properties and items/uniques-sets.** The reasons and checks are in the "Plan 0038 batch S2b" sections of
[items/0004](../../findings/items/0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
[items/0005](../../findings/items/0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
[items/0006](../../findings/items/0006-properties.md#plan-0038-batch-s2b-2026-10-16).

| items-affixes 7, 16 (`STAT_SOCKETS`; the socket test refuses `sock` rows; 2) | a-logs, S2b | **d-none** | Full table, ilvl 1–99, both game types: the test alone refuses a `sock` row inside the level window only on the five quest bases `d33`, `g33`, `hdm`, `hst`, `msf`, which have `unique` and are in no TC. No logged pick was refused by it. |
| items-properties 23 (`sock` draws even when it writes nothing; 1) | a-logs, S2b | **d-none** | No stock `sock` block runs with a cap below 1: no unique or set `sock` row has a cap-0 base at a reachable ilvl, and the magic `sock` rows are refused on such bases (affixes 7). The 7 logged func-14 slots all have a cap ≥ 1. |
| items-properties 24 (`dur%`: the `+1` before the percentage; 1) | a-logs, S2b | **a-run, H2b** | The 3 logged superior ethereal `dur%` items (IR) do not separate the two orders. The route's own fallback is a long Hell items-chain hunt. |
| items-uniques-sets 8 (signed 32-bit arithmetic, header; 1) | a-logs, S2b | **d-none** | Every value of this spec's arithmetic is non-negative and small on stock data (`rarity` 1..20, `lvl` ≤ 110), so signedness has no observable. |
| items-uniques-sets 22 (the five unique tests in order; `GetItemLevel` raises ilvl to 1; 1) | a-logs, S2b | **d-none** | The tests are pure. The only side effect needs ilvl < 1, and no logged creation (5 075 stock, 4 319 IR) has one. |
| items-uniques-sets 31 (the set test order; ilvl read once; 256-pair list; 1) | a-logs, S2b | **d-none** | Pure tests, one ilvl read with no side effect, and at most 9 `setitems` rows per base code (`amu`), far below 256. |
| items-uniques-sets 9, 39 (the item seed from two game-seed draws; game and unit seeds untouched; 2) | a-logs, S2b | **b, H2b** | As tc 58 and 68 (S2a): no log holds the game seed (or the unit seed) around `ItemCreateByQuality`. Route: the H2b line `game+0xD0` at `ItemCreate` entry and after `ItemSeedInit`, plus `Unit+0x20` at `IC0` and `ICJ`. |

Net effect on § 2.4 (S2b): a-logs −9, d-none +6, b +2, a-run +1. After S2a, S4a and S2b, static batches hold 605
statements, harness batches 532 (H2b 24, H5c 41), and 377 are blocked (d-none 252). (The lane's figures, 617, 523 and
374, were computed before S4a merged; corrected at the review.)

**S3a (review 2026-10-16, architect): 30 statements of monsters/pool, spawn, special and stats.** All were a-logs in
S3a; the lane filed them and the review accepted them as filed. The evidence is in the "Plan 0038 batch S3a" sections of
[monsters/0001](../../findings/monsters/0001-level-pool.md#plan-0038-batch-s3a-2026-10-16),
[0002](../../findings/monsters/0002-room-population.md#plan-0038-batch-s3a-2026-10-16),
[0003](../../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3a-2026-10-16) and
[0004](../../findings/monsters/0004-stats.md#plan-0038-batch-s3a-2026-10-16).

| Row | Was | Now | Why |
|---|---|---|---|
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

Net effect on § 2.4 (after S4a and H5c): a-logs −30; d-none +18, a-run +4 (H4b 2, H4a 2), b +2 (H4b), c-emu +3,
d-owner +1, d-sim +2. The 3 c-emu rows leave S3a and wait, unbatched, for the S1f proposal of § 2.5, which now has 41
candidates (the 27 of § 2.1, the 11 room-tiles statements of H5c and these 3). Static batches now hold 584 statements,
harness batches 535 (H4a 31, H4b 47, H5c 41), 3 are c-emu awaiting S1f, and 392 are blocked (d-none 264, d-owner 9,
d-sim 28).

**S4b (review 2026-10-16, architect): 5 statements of drlg/collision, room-tiles and preset.** The lane filed them and the
review accepted them as filed. The evidence is in the "Plan 0038 batch S4b" sections of
[drlg/0002](../../findings/drlg/0002-room-build-draws.md#plan-0038-batch-s4b-2026-10-16),
[0004](../../findings/drlg/0004-preset-units.md#plan-0038-batch-s4b-2026-10-16) and
[0005](../../findings/drlg/0005-collision.md#plan-0038-batch-s4b-2026-10-16).

| Row | Was | Now | Why |
|---|---|---|---|
| collision 4 (any size above 3 → pattern 1) | c, S4b | **d-none** | On the server only players (2), monsters (MonStats2 `SizeX` 0–3) and missiles (0–3) reach `PATH_PatternFromSize`. |
| collision 39 (an object of size 0 with `HasCollision`) | c, S4b | **a-run, H5b** | Twelve stock Objects records have it (131, 399, 564–567 among them); the objects run created none. |
| room-tiles 3, 35 (the 40-candidate cap) | c, S4b | **d-none** | The upper bound over all masks a level type can meet is 28 candidates per key. |
| preset 6, second statement (`MONSTATS_ValidId` is a range check) | c, S4b | **c-emu (S1f proposal)** | A pure 8-instruction function (it reads only `nMonStats`), best shown under the emulator. |

Net effect on § 2.4 (S4b): c −5; d-none +3, a-run +1 (H5b, now 33 statements), c-emu +1. The c-emu row waits, unbatched,
for the S1f proposal, which now has 42 candidates (the 41 above and this one).

**Totals after S2a, S4a, H5c, S2b, S3a and S4b, recomputed once (S4b review).** The S2b and S3a lines above were each
computed from the S4a totals without the other batch, so their static, harness and blocked figures do not add up. Taken
together, the six reviews move 64 statements (S2a 8, S4a 12, S2b 9, S3a 30, S4b 5; H5c none). **Static batches hold 570
statements, harness batches 539, 4 are c-emu awaiting S1f, and 401 are blocked** (d-none 273, d-edit 69, d-sim 28, d-2c
14, d-owner 9, d-0032 8), with 2 deferred and 10 raised: 1 526 in all. The class table is in
[§ 2.4](#24-totals-after-the-moves), the batch sizes in § 5 and § 7.

**S1b (review 2026-10-16, architect): 1 statement of data/excel.** The lane filed it and the review accepted it as
filed. The evidence is in the "Plan 0038
batch S1b" sections of [data/0001](../../findings/data/0001-excel-loader.md#plan-0038-batch-s1b-2026-10-16),
[0002](../../findings/data/0002-mpq-precedence.md#plan-0038-batch-s1b-2026-10-16),
[0003](../../findings/data/0003-string-tables.md#plan-0038-batch-s1b-2026-10-16),
[0004](../../findings/data/0004-cell-converters.md#plan-0038-batch-s1b-2026-10-16),
[0005](../../findings/data/0005-calc.md#plan-0038-batch-s1b-2026-10-16),
[rng/0001](../../findings/rng/0001-rng-core.md#plan-0038-batch-s1b-2026-10-16) and
[rng/0002](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16).

| Row | Was | Now | Why |
|---|---|---|---|
| data-excel 28 (the `.bin` side of the five mixed-archive tables is authoritative) | a-logs, S1b | **d-none** | The pinned game's `-direct -txt` compile of the `.txt` the archives rank first gives `.bin` files byte-identical to the shipped `automagic`, `rareprefix`, `raresuffix`, `inventory` and `plrmode` (run:2026-10-15-cube-saves), so either side loads the same records. |

Remainders of rows raised in part (the rows stay counted as S1b, raised in part; no class moves). The review accepted
the lane's routing: data/README 1 and data-excel 30 ("only under `-direct`", "a stock run never loads them") become
pieces of H3b, whose startup logger already carries data/README 2–5 and data-excel 24; data-calc 19 (hover: a hover
marker in `calc.gdb`) and rng-seeds 11 (which caller: a caller `ra` on `SUNITPRE` in `seed-tree.gdb`) are filed as
Phase 2 leftover pieces (backlog), since no open harness batch owns those loggers; data-calc 18 (offset test),
data-excel 41 F1 and 62 (31-byte cut), 57 (case) and data-strings 31 (the `sp` row) are already S1e c-emu rows; the
rest is d-none or d-edit as each ledger says.

Net effect on § 2.4 (S1b): a-logs −1, d-none +1.

**Totals after S2a, S4a, H5c, S2b, S3a, S4b and S1b (S1b review; the S4b recomputation plus S1b's one move).** Static
batches hold 569 statements, harness batches 539, 4 are c-emu awaiting S1f, and 402 are blocked (d-none 274, d-edit
69, d-sim 28, d-2c 14, d-owner 9, d-0032 8), with 2 deferred and 10 raised: 1 526 in all.

**H4b (review 2026-10-16, architect): 2 statements of monsters/pool and special.** The lane filed them and the review
accepted them as filed. The evidence is in the "Plan 0038 batch H4b" sections of
[monsters/0001](../../findings/monsters/0001-level-pool.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b) and
[0003](../../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b).

| Row | Was | Now | Why |
|---|---|---|---|
| monsters-pool 1 (the second game-creation path, `GameCreateA`) | b, H4b | **d-none** | `0x00530930` has no reference in the image: no rel32 call or jump and no absolute pointer (`tools/xrefscan.py`, 0 hits; Ghidra xrefs none). Dead code has no observable; the statement stays `[I]` as a reading. |
| monsters-special 2 (`MonMakeSpecial` from `0x00583050`) | b, H4b | **d-owner** | The only reference is the jump at `0x005830CC` in the Shrines code-20 function (shrine-function table entry 20, `0x006E1940`). Stock play reaches it only by operating that shrine, which no scripted session has done. An owner session, or an `objop` on such a shrine if a seed places one (H4a may try, backlog), settles it; the logger line `MMS0` is ready. |

Not class moves, recorded for Phase 3: stats 40 is a shortfall (no `willowisp` special met; it stays `[I]` and goes to
H4a as an a-run piece); special 27's remainder splits into d-none (the clamp at 99, row 7) and an H4a a-run piece (the
clamp at 1); spawn 42's remainder (classes 228 and 334) rides H5d's tomb and Act III sessions, whose `collision.gdb`
carries the `MC` lines; spawn 42's 528 half, filed "stays d-edit", was reached on stock data (now raised). Rows that
rest on kept logs re-read (spawn 3, 43, 44 and the 528 half of spawn 42; special 20's below-20 half) count as H4b
raises, a-logs in effect.

Net effect on § 2.4 (H4b): b −2; d-none +1, d-owner +1.

**Totals after S2a, S4a, H5c, S2b, S3a, S4b, S1b and H4b (H4b review; the S1b totals plus H4b's two moves).** Static
batches hold 569 statements, harness batches 537, 4 are c-emu awaiting S1f, and 404 are blocked (d-none 275, d-edit
69, d-sim 28, d-2c 14, d-owner 10, d-0032 8), with 2 deferred and 10 raised: 1 526 in all.
**S2c (review 2026-10-16, architect): 10 statements of items/cube, items/quest-drops and items/sockets-runewords.** The
lane filed them and the review accepted them as filed. The evidence is in the "Plan 0038 batch S2c" sections of [items/0007](../../findings/items/0007-sockets-runewords.md#plan-0038-batch-s2c-2026-10-16),
[items/0008](../../findings/items/0008-cube.md#plan-0038-batch-s2c-2026-10-16) and
[items/0010](../../findings/items/0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16).

| Row | Was | Now | Why |
|---|---|---|---|
| items-cube 17 (`exc`/`eli` inputs) | a-logs, S2c | **a-run, H6a** | The `exc` inputs of rows 131, 132, 135, 136 met 104 cube items in the logs, and the flag decided none. Route: an elite upgrade with an exceptional-tier and a normal-tier base of the same type. |
| items-cube 20 (a stackable base relaxes the count) | a-logs, S2c | **d-none** | `numinputs` = the summed `qty` on every row (cube 21) and no row has two stackable inputs: a stackable input can claim more than `qty` only when another input is then short. |
| items-cube 24 (`sock=N` not an input keyword) | c, S2c | **d-none** | No stock input cell holds `sock=N` (389 cells). |
| items-cube 51 (the random item of a type: skipped record, cap, empty case) | a-logs, S2c | **a-run, H6a** | Row 19 (`pole`) has 18 candidates and `lvl` 50, so the cap and the empty case are d-none; the skipped record needs more row-19 transmutes. |
| items-cube 58 (a forced row skips only the level window) | a-logs, S2c | **a-run, H6a** | All 12 logged forced picks lie inside their windows. Stock data reaches the case once: row 17 on a magic tower shield (alvl 19 against *of Spikes*' level 21). |
| items-quest-drops 48 (the other 24 `boss` classes) | a-logs, S2c | **a-run, H4a** | No kept log creates a `boss` class other than Andariel in an expansion Nightmare or Hell game (the route's own fallback). |
| items-sockets-runewords 35 (a parent already holding a 171 list; 2) | a-logs, S2c | **b, H6b** | No log re-inserts the children of a loaded runeword. Piece: load the *Steel* sample under `sockets.gdb`. |
| items-sockets-runewords 36, L442 (the first blank ends the lines; 1 of 2) | c, S2c | **d-none** | No stock `runes` row has a gap or an unknown code (169 rows), so "ends" and "skips" give the same lines. L472 is raised. |
| items-sockets-runewords 42 (`ITEMS_SetSockets`' clamps) | a-logs, S2c | **a-run, H2b** | No clamp bound in the 23 logged calls. Route: H2b's long Hell hunt (magic drops requesting 5 or 6). |

Remainders of rows raised in part (the rows stay counted as S2c, raised in part; no class moves). The review routed
them as follows. Harness pieces, named in § 5 so that the batch lane sees them: cube 49 (cases (a) and (b) of a
crafted pick of 0: a crafting session at output ilvl ≤ 5 on `sst`, `lbt` or `lgl`; case (b) faults the game, so it is
the session's last transmute) and affixes 14 (with cube 58) to **H6a**; sockets 14 (split at the review: the client's
bit 11 before and after identifying an unidentified socketed parent) and sockets 46 (the reader's store at `+0x38`,
with the *Steel* load of sockets 35) to **H6b**; vendors 22 (the store tab and grid placement) and vendors 26 (`+0x18`
and `+0x28` of the store creation record at `IC0`) to **H6c**; quest-drops 38 (a cursor line at
`sub_0055EEA0_CursorItemConsume`) to **H6e1**; sockets 44 (normal and rare drops requesting more than 3 and 4) to
**H2b** with sockets 42. Static leftovers (backlog, reverser): quest-drops 8, 10 and 19 (the 45 register-word
`SetState`/`ClearState` sites and the 12 callers of the range clear `0x0065C3E0`). *Closed at the `lane/p49r` review (plan 0049 Phase 1, 2026-10-20):* quest-drops 10 and 19 are **raised** (the
record-function closure, its limits stated in items/0010 qd 10); quest-drops 8 stays raised in part, its remainder
answered `[I]` (word 41 is object 1's `+0xE4` word). No class moves; the rows stay counted as S2c. The other remainders are d-none or
d-edit as each ledger says (sockets 4, 6, 43, 47; cube 47; properties 19 L573), or have no further route and stay `[I]`
in Phase 3 (quality 16, the version-0 rows; sockets 2, 26; cube 55 L829, the portal object's oracle; vendors 11, 21,
24, 28; quest-drops 21).

Net effect on § 2.4 (S2c): a-logs −8, c −2; a-run +5 (H6a 3, H4a 1, H2b 1), b +2 (H6b), d-none +3.

**Totals after S2a, S4a, H5c, S2b, S3a, S4b, S1b, H4b and S2c, recomputed once (S2c review).** The lane computed its
line against the S4b totals, before S1b and H4b were reviewed. Taken together, the nine reviews move 77 statements
(S2a 8, S4a 12, S2b 9, S3a 30, S4b 5, S1b 1, H4b 2, S2c 10; H5c none). **Static batches hold 559 statements, harness
batches 544, 4 are c-emu awaiting S1f, and 407 are blocked** (d-none 278, d-edit 69, d-sim 28, d-2c 14, d-owner 10,
d-0032 8), with 2 deferred and 10 raised: 1 526 in all. The class table is in [§ 2.4](#24-totals-after-the-moves), the
batch sizes in § 5 and § 7.

**S3b (review 2026-10-16, architect): 2 statements of player/creation and monsters/spawn.** The evidence is in the
"Plan 0038 batch S3b" sections of [player/0001](../../findings/player/0001-creation.md#plan-0038-batch-s3b-2026-10-16) and
[monsters/0002](../../findings/monsters/0002-room-population.md#plan-0038-batch-s3b-2026-10-16). Both moves accepted as filed.

| Row | Was | Now | Why |
|---|---|---|---|
| player/creation 16 (an existing skill entry raised by 1 below the maximum) | c, S3b | **a-run, H6g** | No stock creation reaches the branch: no CharStats record repeats a skill in `Skill 1..10` or names Attack (7 records). Stock play reaches it by the skill-point path (`newskills` spent, then `SKILLS_AddSkill` on the same skill, 0x0057011A), which no kept log covers. Route: spend two points on one class skill under `player.gdb`; with H6g's level-98 save, one skill to its maximum. |
| monsters-spawn 41 (`CollisionTest` sizes 0, 1 and others) | c, S3b | **a-run, H5d** | Sizes other than 0–3 are d-none (no MonStats2 record has one, 609 records). Sizes 0 and 1 are reachable: `baaltaunt` (545, size 0) is in level 123's `umon`, `sarcophagus` (228, size 1) is placed in the tombs. H5d's tomb and Act V sessions settle both from the `MK0` lines (as drlg/collision 24). |

Not class moves, recorded for Phase 3 and the harness lanes (the rows stay counted as S3b, raised in part or raised):
- **monsters-stats 30**, remainder contradicted in part. A Druid's Raven (`druidhawk`) reads its Normal MonProp row in a
  Normal game, so "no Normal row reachable" does not hold. H4a piece: a Druid casting Raven in a Normal game under
  `mon-stats.gdb`.
- **monsters-stats 19 and 45** are raised by composition (review ruling 1). The `mephistospirit` visit (401, Durance of
  Hate Level 3, level 102, reversed in Normal) stays in H4a as an optional corroboration; no row depends on it.
- **monsters-special 43** split at the review: raised in part. The packet half is `[C]`. The remainder, "what other code
  reads", stays `[I]`: the four callers of 0x005A0120 other than the packet builder (0x005423F8, 0x005428A9, 0x00597C87,
  0x005A4A5F) are named, not read. Static leftover (backlog, reverser).
- pool 9's cap and hirelings 8's three fatal branches are d-none and d-edit remainders, as routed.

Net effect on § 2.4 (S3b): c −2; a-run +2 (H6g 1, H5d 1).

**Totals after S2a, S4a, H5c, S2b, S3a, S4b, S1b, H4b, S2c and S3b, recomputed once (S3b review).** The lane computed
its line against the H4b totals, before S2c was reviewed. Taken together, the ten reviews move 79 statements (S2a 8,
S4a 12, S2b 9, S3a 30, S4b 5, S1b 1, H4b 2, S2c 10, S3b 2; H5c none). **Static batches hold 557 statements, harness
batches 546, 4 are c-emu awaiting S1f, and 407 are blocked** (d-none 278, d-edit 69, d-sim 28, d-2c 14, d-owner 10,
d-0032 8), with 2 deferred and 10 raised: 1 526 in all. The class table is in [§ 2.4](#24-totals-after-the-moves), the
batch sizes in § 5 and § 7.

**Plan 0039 P1a (review 2026-10-16, architect): the 11 room-tiles merge rows of H5c.** The static question the H5c
review set (plan 0038 log, H5c ruling 4) is answered no in
[drlg/0002 § Plan 0039 batch P1a](../../findings/drlg/0002-room-build-draws.md#plan-0039-batch-p1a-2026-10-16). Every
wall and shadow cell of the 2077 DS1s a room can load has bit 7 (`[C]`, re-counted at the review), no grid writer
adds one without it (`[I]`), and the H5c logs show every wall and shadow merge ending at flag `0x1` (`[C]`). Floors
merge only into orientation-0 floor entries and never reach the branches.

| Row | Was | Now | Why |
|---|---|---|---|
| room-tiles 4 (2), 14 (2), 15 (2), 28 (3), 30 (1), 37 (1) (merge remap rows 0–5, row −2, the 8/9 edge rule, signed compares, orientation 3) | a-run, shortfall; S1f candidates | **d-edit** | Only an edited DS1 or `LvlSub`/`LvlPrest` row can give a wall or shadow without bit 7, so only edited data reaches these branches (ADR-0013 still bars a forced run). They leave the S1f candidates: emulating them would confirm code that stock data never runs. The spec keeps them as `[I]` code readings and states, `[I]`, that they are unreachable on stock data. |

Net effect: harness batches −11 (H5c's shortfall rows), d-edit +11; S1f candidates 42 → 31. **Static batches hold
557 statements, harness batches 535, 4 are c-emu awaiting S1f, and 418 are blocked** (d-none 278, d-edit 80, d-sim 28,
d-2c 14, d-owner 10, d-0032 8), with 2 deferred and 10 raised: 1 526 in all. § 2.4's class table is not re-drawn.

**S1a (review 2026-10-16, architect): 2 statements of save/d2s.** The evidence is in the "Plan 0038 batch S1a"
section of [save/0001](../../findings/save/0001-d2s-io.md#plan-0038-batch-s1a-2026-10-16). Both moves accepted as filed.

| Row | From | To | Reason |
|---|---|---|---|
| save-d2s 117 (`written[]` zeroed per list) | c, S1a | **b, H1b** | No item of the 146 game-written saves repeats a follower's value in two lists, so nothing shows the zeroing. Piece: a set item whose main list and a bonus list hold the same damage group. |
| save-d2s 124 (a follower read alone takes the default path) | c, S1a | **b, H1b** | No lone follower in the corpus; stock properties write one (`fire-max` alone, stat 49). Piece: an item with such a property, saved and reloaded under `d2s-io.gdb`. |

Remainders of rows raised in part (the rows stay counted as S1a; no class moves). Harness pieces for **H1b**: a hired
mercenary (row 20), a swapped weapon set (24), a hotkey bound to a left-button skill (32), an item on the cursor at the
save (71), a class item with an automagic affix (86, 103), an item with magic damage, group 52 (123, 130, 138), a lone
`fire-min` (128, with 124's piece). d-none: "no `ValShift`" on the fixed fields and followers (92, 104, 120, 135; every
such stat has `ValShift` 0), a non-zero value that shifts to 0 (119), the clamp bounds and stat 326 (130). d-edit: the
version < 93 paths (130). Stays `[I]` with no route: the refusal flag of row 71 (its setter is not read).

The review adds one d-edit remainder to row 130's: the reader's per-version base adjustment for item versions 72–88
(0x0062CDC4–0x0062CE10), seen while reading row 87. No row moves for it.

Net effect on § 2.4 (S1a): c −2; b +2 (H1b, now 48 statements).

**Totals after S2a, S4a, H5c, S2b, S3a, S4b, S1b, H4b, S2c, S3b, plan 0039 P1a and S1a, recomputed once (S1a
review).** The lane computed its line against the S2c totals, before S3b and P1a were reviewed. Taken together, the
eleven batch reviews and P1a move 92 statements (S2a 8, S4a 12, S2b 9, S3a 30, S4b 5, S1b 1, H4b 2, S2c 10, S3b 2,
P1a 11, S1a 2; H5c none). **Static batches hold 555 statements, harness batches 537, 4 are c-emu awaiting S1f, and 418
are blocked** (d-none 278, d-edit 80, d-sim 28, d-2c 14, d-owner 10, d-0032 8), with 2 deferred and 10 raised: 1 526
in all. The class table is in [§ 2.4](#24-totals-after-the-moves), the batch sizes in § 5 and § 7.

**H5e (review 2026-10-16, architect): 22 statements of drlg/maze, outdoor and preset.** run:2026-10-16-sweep-mazes, 6
sessions. The lane filed 18 raised, 2 raised in part, 2 shortfall; the review accepts them as filed. The evidence is in
the "Plan 0038 batch H5e" sections of [drlg/0004](../../findings/drlg/0004-preset-units.md),
[0006](../../findings/drlg/0006-maze.md) and [0008](../../findings/drlg/0008-outdoor.md). No row changes class.

| Row | Was | Now | Why |
|---|---|---|---|
| outdoor 13, the swapped cliff-cave scan's non-square half | a-run, H5e | **d-none** (the half only; the row stays counted as H5e, raised in part) | Of the Act I wilderness levels 2–7 only the Blood Moor is non-square in cells (12×7 or 7×12; 3–7 are 10×10 in every seed), and flag `0x20` was set only on levels 4–6, never on the Blood Moor, in the 1 800 Blood Moor windows of the scan and the lane's seeds 1–2 999. Accepted on that evidence, with the Blood Moor's `0x20` added to the static reachability question (backlog); if the outline can set it there, the half returns to a-run. |
| outdoor 14, roads with 5 or 6 endpoints and an exhausted pool | a-run, H5e | **a-run, shortfall** (raised in part: the failed search) | None in the logs or the offline scan. Static reachability question first (backlog); no more seeds until it is answered. |
| outdoor 7 (vertex merge), 11 (waypoint with no free cell) | a-run, H5e | **a-run, shortfall** | As row 14. |

Not class moves, recorded for Phase 3: maze 10's level 10 rests on kept logs (od-s2, a35-s1; re-run at the review, 4
windows), and tombs 69 and 72 rest on a static reading (drlg/0006, `[I]`: the tomb finisher has no test on either id;
the roles true, Kaa and plain were all built). Jail 31 and the lava levels 126, 127 were built on the server copy only;
a window carries every draw, so one copy is enough.

Net effect on § 2.4 (H5e): none.

**Totals after the twelve batch reviews and plan 0039 P1a, recomputed once (H5e review).** H5e moves nothing, so the 92
moves stand. **Static batches hold 555 statements, harness batches 537, 4 are c-emu awaiting S1f, and 418 are blocked**
(d-none 278, d-edit 80, d-sim 28, d-2c 14, d-owner 10, d-0032 8), with 2 deferred and 10 raised: 1 526 in all.

**H5a (lane, 2026-10-17; reviewed 2026-10-17, accepted with fixes): 21 statements of drlg/maze, preset and warps.** run:2026-10-17-sweep-links, 9
sessions on slot 1 (map seeds chosen offline with `tools/sweep_h5a.py scan`). New logger lines (`tools/gdb/drlg-links.py`:
every pick and check of `LevelLinkBuild`, the Act1B widened test, `LevelSeamsByTouch`'s `RectTouch`), replayed against
the unchanged link-builder model: 128 builds, 0 mismatches; `drlg.py gen` 99 288 checks, 0 mismatches. The evidence is
in the "Plan 0038 batch H5a" sections of [drlg/0007](../../findings/drlg/0007-warps.md),
[0006](../../findings/drlg/0006-maze.md) and [0004](../../findings/drlg/0004-preset-units.md). The lane files **16
raised, 0 in part, 0 shortfall, 5 reclassified**:

| Row | Ruling | Evidence |
|---|---|---|
| maze 4, 5 (`MazeFindWest`) | raised | Reachable after all: level 27 keeps its create-time index (`Files` 3) when Black Marsh ends on side 0, and index 2 sends the Barracks to `g_BarracksFinders[2]`. Map seed 58, two level-28 windows matched with their probe draws; `MazeFindWest` I → C. |
| maze 15 (Barracks `k` 0 and 2) | raised | `k` 0 four windows (s2 drawn, s9 create-time), `k` 2 two windows (s3), attach, translation and rect as modelled. |
| warps 3 (×10, the unreached choices) | raised | Every choice ended a logged build (`LNK1`), except `0x00676450` (0, 1) and (2, 0), which are placed and logged (`LNKP`, 6 each, rects as the table) but never kept: the Rogue side table has no nonzero index with `d + 4f` = 2 or 4. |
| warps 5, the Burial Grounds reject | raised | 6 rejects (s2, s6, s7) with the plain test passing, the next choice accepted. |
| warps 5, the Act1B widening deciding a check | **d-none** | Never on stock data: the table's outcome depends only on the difficulty and the first choices of Black Marsh and Dark Wood; the scan holds all 16 pairs at each difficulty, and the 3 600 widened tests with the plain test passed all accept (72 logged, all accept). |
| warps 6 (a Rogue-table 0 reject) | raised | 30 rejects at 15 distinct indices. |
| warps 8 (the widening's axis) | raised | `LNKW`: rect[0] is the model's with `y − 200`, `h + 200` in all 72 widened tests. |
| warps 9, 12; preset 22 (level 27's index 2 from side 1) | **d-none** | Unreachable: Black Marsh's first choice and the level-27 draw read the same `r` (first step of the copy and of the act seed), side 1 is kept only from a first choice of 1 at every difficulty, so `r & 1` = 1, index 1 (drlg/0007 § H5a; the logged side-1 builds s4, s7 index 1). |
| warps 11 (`RectTouch` false branches, `t` = 0) | **d-none** | One call site, `push −1`; Act V's seam rects take 4 forms per difficulty, all in the scan, and every pair shares an edge (5 400 tests; 48 logged, all true). |

Not class moves, for Phase 3: the Barracks' `k` is the create-time index whenever Black Marsh ends on side 0 (drlg/0006
§ H5a corrects § 7 step 1), and Rogue Encampment ends on six of its eight `(d, f)` only.

Net effect on § 2.4 (H5a): a-run −5, d-none +5.

**H5a review (architect, 2026-10-17): accept with fixes; the five d-none stand.** The manifest matches the nine logs;
`sweep_h5a.py logs` (128 builds, 0 mismatches; gen 99 288 checks, 0 mismatches), `scan 1 301 0,1,2 0 82,52` and the unit
tests re-run identically, and `drlg.py gen` on s2, s3 and s9 alone gives 0 mismatches. The review also enumerated every
draw value of tables `0x006F0840` and `0x006F0DE0` directly (8 values per draw, 64 leaves per difficulty, not map
seeds): Black Marsh's first draw is the copy's first step in all, its outcomes are 0 → 0, 1 → 1, 2 → 3, 3 → 3, no
backtrack, no widened reject, and every Act V seam pair shares an edge. The d-none rows rest on that and on the code:
the copy is taken from the act seed at entry (`0x0067730E`), the picks step only the copy, and the level-27 draw at
`0x006774D6` is the act seed's next step, with `2 − (r & 1)` from `and al, 1; neg al; sbb eax, eax; add eax, 2`; the
model that assumes no act-seed step in between predicted every logged `LK27` and act seed after. `RectTouch` has one
call (`0x00677606`, `push −1` at `0x006775FE`) and no stored pointer; `MazeFindWest` has no call and one pointer
(`g_BarracksFinders[2]` at `0x006F0470`). `0x00676450` (0, 1) and (2, 0) rest on the logged rect at the pick's return
(`LNKP`, the same quantity `LNK1` checks); the B2 rule asked for a build to end on a choice only because no per-pick line
existed, and the Rogue table's 16 nonzero indices (`0x006F1158`: 0, 1, 9, 19, 21, 24, 30, 31, 33, 39, 41, 53, 54, 56,
62, 63) leave residues 2 and 4 out, with the index `d + 4f + 8·dir[a] + 32·flip[a]` read at `0x00676E7B`. Fixes: the
drlg/0007 section says its counts are over both act objects (distinct: 15 Rogue rejects, 3 Burial Grounds, 36 widened
tests, 24 `RectTouch` tests); drlg/0006 § 7 step 1 points at the correction.

**Totals after the thirteen batch reviews and plan 0039 P1a, recomputed once (H5a review).** H5a moves 5 rows from
a-run to d-none. **Static batches hold 555 statements, harness batches 532, 4 are c-emu awaiting S1f, and 423 are
blocked** (d-none 283, d-edit 80, d-sim 28, d-2c 14, d-owner 10, d-0032 8), with 2 deferred and 10 raised: 1 526 in all.
Every batch carrying drlg/maze, drlg/preset or drlg/warps statements is now accepted (S4a, S4b, H5c, H5e, H5a), so the
three clusters are ready for the Phase 3 re-tag.


**S1e (filed 2026-10-17, reverser; reviewed 2026-10-17, accepted with fixes): 3 statements of data/calc and data/excel.** run:2026-10-17-sweep-emu
(the Ghidra p-code emulator under ADR-0015, `tools/sweep_s1e.py`, new script `re/ghidra_scripts/EmuTrace.java`). The
evidence is in the "Plan 0038 batch S1e" sections of [data/0001](../../findings/data/0001-excel-loader.md#plan-0038-batch-s1e-2026-10-17),
[0002](../../findings/data/0002-mpq-precedence.md#plan-0038-batch-s1e-2026-10-17),
[0003](../../findings/data/0003-string-tables.md#plan-0038-batch-s1e-2026-10-17),
[0004](../../findings/data/0004-cell-converters.md#plan-0038-batch-s1e-2026-10-17),
[0005](../../findings/data/0005-calc.md#plan-0038-batch-s1e-2026-10-17),
[rng/0001](../../findings/rng/0001-rng-core.md#plan-0038-batch-s1e-2026-10-17) and
[save/0001](../../findings/save/0001-d2s-io.md#plan-0038-batch-s1e-2026-10-17).

| Row | Was | Now (proposed) | Why |
|---|---|---|---|
| data-calc 14 (`INT32_MIN ÷ −1` raises the divide error; 1) | c-emu, S1e | **d-edit** | ADR-0015 condition 5 excludes faults (the emulator even returned 0 there); only an edited formula with a variable divisor reaches it. The instruction reading stays `[I]`, re-pinned by objdump. |
| data-excel 43, 44 (a 4-character name both code and TC resolves to the item; unique row 0 cannot be named from a TC; 2) | c-emu, S1e | **d-none** (as filed by 0b) | `TC_ParseItemCell` calls `TC_AddEntry` → `TC_GrowEntries` → the pool allocator 0x0040B4B0 on every resolved cell, so no case reaching either claim runs under ADR-0015 condition 1. The lookups they rest on are now `[C]`. |

Remainders of rows raised in part (the rows stay counted as S1e; no class moves): data-calc 13's L305 (the same
divide error as row 14, d-edit); data-excel 51's id 13, which the batch **contradicts** (an unmatched id below 14 reads
the 0x18 bytes after the language table, whose pointers are 0x4D/0x42/0x54, and the string-table load faults; a `use`
byte of 13 needs an edited file: d-edit; spec-writer backlog).

**Proposal S1f (§ 2.5), for the review.** Of the 31 candidates, the lane can declare the read set of 15 statements
(11 rows), from the objdump call closures (`sweep_s4b` graph) and the S1e families that already cover their callees:
drlg-preset 6 second statement (`MONSTATS_ValidId`, one function, no callee); monsters-stats 9, 11 (`MulDiv`, two
functions, no allocation or import); items-affixes 6, 12 (`sub_005C0D00_AffixCandAdd`, one function); data-calc 8 (the
compile order within a record: `EXCEL_ParseTxt` with a calc cell callback, as the S1e `parsetxt` and `compile`
families run them) and 33 (`SKILLS_CalcVar` codes 43–48 through `MISS_GetElemMin`/`Max` on synthetic records, as the
`calcvar` family); data-excel 65 (5, the absent-column defaults: `EXCEL_ParseTxt`'s defaults pass with descriptor
entries that have no column) and 69 (callback order, the same run with two calc columns and an absent one); and,
conditionally, monsters-pool 27 (`MonVariantRoll`) and items-uniques-sets 44 (`ITEMS_BuildSetPick`'s weight), whose
static closures reach the allocator and the fatal path (421 and 433 functions): the S1f lane keeps them only if the
emulation trace shows the claimed branches stay off those paths, else they return to their classes. The other 16 keep
their classes: monsters-pool 2, 25, 26 (`DRLG_LoadLevels` allocates); monsters-stats 4, 35, 41 (unit and stat-list
reads); items-uniques-sets 26, 43 (`ITEMS_BuildUnique` takes the game and item units); items-quality 2, 17, 21 (the
drop's unit and game reads); items-tc 9, 54, 65 (`TC_ResolveDrops`: an ADR-0004 oracle needs logged values, and there
are none for edited cells); data-excel 70 (the descriptor is built on the stack by each table loader, which allocates).
**The lane recommends that S1f run**, 15 statements, static, with `tools/sweep_s1e.py` and `EmuTrace.java` reused.

Net effect on § 2.4 (S1e): static −3 (S1e's c-emu rows); d-edit +1, d-none +2. (The lane's totals were computed
before H5a's review; they are recomputed below.)

**S1e review (architect, 2026-10-17): accept with fixes; the three moves stand.** The manifest matches its 53 files;
`sweep_s1e.py static` and the unit tests re-run identically; the kept `lang` and `calcvar` cases re-run under the
lane's Ghidra copy give byte-identical outputs, and `eval`, regenerated after the review fixed an unseeded draw in its
case writer, gives 6 000/6 000 (run record, review re-run). data-calc 14 → d-edit: the divide error is a fault, which
ADR-0015 condition 5 leaves out, and only an edited formula reaches it; row 13's L305 is the same claim and stays
counted as S1e, not raised. data-excel 43, 44 → d-none: `TC_AddEntry` calls `TC_GrowEntries` unconditionally
(0x0065408A), and that calls the pool allocator 0x0040B4B0 (0x00654036), so no case reaching either claim can run
under condition 1; read in objdump at the review. data-excel 51's id-13 remainder is d-edit, counted as S1e; its
`[C]` covers the index map only, since entry 13's low words are written at run time (data/0002 review note).

**S1f (created by the S1e review): 15 statements in 11 rows, the lane's proposal as filed.** S1f is a static batch
under ADR-0015 with `tools/sweep_s1e.py` (new families) and `EmuTrace.java`. It takes the 4 c-emu rows awaiting it and
11 statements from blocked classes:

| Row | Was | Now | Why |
|---|---|---|---|
| drlg-preset 6, second statement; monsters-stats 9, 11; monsters-pool 27 (4) | c-emu, awaiting S1f | **c-emu, S1f** | As § 2.6 S3a and S4b routed them. `MONSTATS_ValidId` (0x004E6C50) reads only `g_pDataTables`; `sub_00483360_MulDiv` calls one CRT helper (0x00684240). Pool 27 is conditional (below). |
| items-affixes 6, 12 (2) | d-none | **c-emu, S1f** | `sub_005C0D00_AffixCandAdd` is seven instructions with the `cmp eax, 0x1ff` cap and no call; read at the review. |
| data-calc 8, 33 (2) | d-edit | **c-emu, S1f** | The compile order within a record (`EXCEL_ParseTxt` with a calc cell callback, as S1e's `parsetxt` and `compile` ran) and `SKILLS_CalcVar` codes 43–48 through `MISS_GetElemMin`/`Max` on synthetic records (as `calcvar`). |
| data-excel 65 (5), 69 (1) | d-edit | **c-emu, S1f** | `EXCEL_ParseTxt`'s defaults pass (descriptor entries with no column) and the callback order with two calc columns and an absent one. |
| items-uniques-sets 44 (1) | d-none | **c-emu, S1f** | `ITEMS_BuildSetPick`'s weight 0; conditional (below). |

Conditions, set by the review: (a) every S1f claim needs a case that reaches its branch with no case stopping (a call
into an import or the allocator stops a case at the import thunk, `pc outside the image's code`); a row whose claimed
branch cannot be reached without the allocator, an import or the fatal path returns to its class, recorded at the
batch, and this applies to pool 27 and uniques-sets 44 first, whose static closures reach the allocator and the fatal
path; (b) a pool or array the code may grow gets a capacity above every case, and the record says the growth path is
not reached; (c) every spec write to an image address is listed in the finding with its ruling-3 justification (S1e
review, plan log). The other 16 candidates keep their classes, as the lane filed them. S1f writes the same data
findings as S1e and starts after S1e merges.

Net effect on § 2.4 (S1f created): static +15; c-emu awaiting −4; d-none −3, d-edit −8.

**Totals after the fourteen batch reviews and plan 0039 P1a, recomputed once (S1e review).** S1e moves 3 statements
(static −3; d-edit +1, d-none +2) and creates S1f (static +15 from c-emu 4, d-none 3, d-edit 8). **Static batches hold
567 statements (S1f 15 included), harness batches 532, none is c-emu awaiting a batch, and 415 are blocked** (d-none
282, d-edit 73, d-sim 28, d-2c 14, d-owner 10, d-0032 8), with 2 deferred and 10 raised: 1 526 in all.

**S1f (filed 2026-10-17, reverser; reviewed 2026-10-17, accepted with fixes): 15 statements in 11 rows.** run:2026-10-17-sweep-emu2 (the
Ghidra p-code emulator under ADR-0015, `tools/sweep_s1f.py`, `EmuTrace.java` with a new `guard` directive). The
evidence is in the "Plan 0038 batch S1f" sections of [drlg/0004](../../findings/drlg/0004-preset-units.md#plan-0038-batch-s1f-2026-10-17),
[monsters/0004](../../findings/monsters/0004-stats.md#plan-0038-batch-s1f-2026-10-17),
[monsters/0001](../../findings/monsters/0001-level-pool.md#plan-0038-batch-s1f-2026-10-17),
[items/0005](../../findings/items/0005-affixes.md#plan-0038-batch-s1f-2026-10-17),
[items/0004](../../findings/items/0004-uniques-sets.md#plan-0038-batch-s1f-2026-10-17),
[data/0005](../../findings/data/0005-calc.md#plan-0038-batch-s1f-2026-10-17) and
[data/0004](../../findings/data/0004-cell-converters.md#plan-0038-batch-s1f-2026-10-17). **All 15 raised; no row
returns to its class.** The two conditional rows meet condition (a): monsters-pool 27's `MonVariantRoll` reaches the
fatal path only on a NULL seed or entry, and items-uniques-sets 44's success path runs `ItemApplyProps` mode 4 to its
end on property-less set rows; every S1f memory spec guards the fatal path and the allocator entries, and no case of
any family stopped. Condition (b): the one growable pool reached (itemscode, `parsetxt2`) has capacity 0x10000 against
178 bytes at most, and `EXCEL_AddCode` is not reached (no registration column present). Condition (c): every spec
write on an image address is listed in the finding with its ruling-3 justification (cookie (a), SSE2 flag (b),
`__locale_changed` (c); `g_pDataTables`, the DataTables fields read, the itemstatcost link and the pool header as
arguments). No class moves; the totals of the S1e review stand (static 567 including S1f).

**S1f review (architect, 2026-10-17): accept with fixes; all 15 raises stand, no class moves.** The manifest matches its
38 files; `sweep_s1f.py static` (65 of 65 pins, the writer scan) and `test_sweep_s1f.py` (7 tests) re-run identically;
`cases` regenerates every kept input byte for byte; under the lane's Ghidra copy the `muldiv`, `setpick` and
`pickaffix` cases gave `.out` files byte-identical to the lane's (run record, review re-run). The `guard` directive
plus the static call closures is accepted as the mechanical check of condition (a) (plan log, ruling 1), and both
conditional rows meet it. Totals unchanged: **static 567 (S1f's 15 included), harness 532, c-emu awaiting a batch 0,
blocked 415** (d-none 282, d-edit 73, d-sim 28, d-2c 14, d-owner 10, d-0032 8), **deferred 2, raised 10: 1 526.**

**Plan 0039 P1c (review 2026-10-17, architect): drlg-preset 18's `id = 573` remainder.** The row was raised in part at
S4a (the logged dispatch branches `[C]`, the `id = 573` branch `[I]`; plan 0038 log, round-3 review ruling 1). The
survey in [drlg/0004 § Plan 0039 batch P1c](../../findings/drlg/0004-preset-units.md#plan-0039-batch-p1c-2026-10-17)
shows no stock unit reaches it: only Act IV DS1 ids 5–7 map to 573 in `g_Ds1ObjectIds` (re-read at the review: those
three cells, no −1), no shipped DS1 uses them (2 274 of 2 276 parsed, all 2 043 `lvlprest` files included), and the
other `PresetUnitCreate` callers add no 573.

| Row | Was | Now | Why |
|---|---|---|---|
| drlg-preset 18, the `id = 573` remainder | raised in part (S4a), remainder `[I]` | **d-none** (remainder) | No stock case; the spec keeps the branch as an `[I]` code reading and says "no stock case". |

Net effect: none on the totals. The row stays counted as S4a, as data-excel 51's id-13 remainder stays counted as S1e.

**H6d (filed 2026-10-17, reverser, `lane/h6d`; reviewed 2026-10-17, accepted with fixes): 17 statements of items/quest-drops, tc and
uniques-sets.** run:2026-10-17-sweep-quest-b6, 19 sessions on slot 2. The lane files 5 raised, 9 raised in part, 2
shortfall and 1 reclassified. The evidence is in the "Plan 0038 batch H6d" sections of
[items/0010](../../findings/items/0010-quest-drops.md#plan-0038-batch-h6d-2026-10-17),
[0001](../../findings/items/0001-tc-resolution.md#plan-0038-batch-h6d-2026-10-17) and
[0004](../../findings/items/0004-uniques-sets.md#plan-0038-batch-h6d-2026-10-17).

| Row | Was | Now (proposed) | Why |
|---|---|---|---|
| items-uniques-sets 21 (the restore path `rec+0x2C` ≠ 0) | b, H6d | **b, H1a** (accepted, review ruling 4) | Larzuk's and Anya's copies go through `ItemCopy` → `ItemCreateFromSave` and never reach `ItemCreateByQuality` (no `IC0` in the 30 services of run:2026-10-16-quest-drops). The only writer of the flag is `ItemCreateFromOldRec`, reached from the version-`0x47` item-list reader. Route: H1a's legacy loads with a unique in such a list, under `uniques.py`. Version 0 stays d-none. |

Not class moves, for Phase 3 and later lanes (the rows stay counted as H6d):
- **quest-drops 13 and 16**: raised in part on Baal; Diablo is a shortfall (one session reached the Chaos Sanctuary, no
  seal operated). **quest-drops 25**: shortfall (three sessions stopped at the same River of Flame lava edge). An
  owner-played addendum for the three is proposed in the run record (Diablo fresh and done, the Nightmare forge).
- **quest-drops 11 and tc 27**: the `exp`-state remainder is a shortfall with a route (Attract, Confuse or Conversion
  on a monster that kills a quest boss). The party half of tc 27 stays d-2c.

Net effect on § 2.4 (H6d): none. The b row moves from H6d to H1a, which then holds 46 statements. Harness
batches hold the same 532 (the lane's draft said 537, the H5e-era figure).

**H6d review (architect, 2026-10-17): accept with fixes; 5 raised, 9 raised in part, 2 shortfall, us 21 → b, H1a.**
The manifest matches its 19 logs; `sweep_h6d.py logs` and `static` re-run byte-identical to the lane's reports,
`copies` and the 8 tests re-run, `questdrops.py` 0 mismatches, and `tc.py replay` on five sessions (493 calls) gives
the lane's counts (run record, review re-run). The lane's 1 388 calls were 1 322 counted with the classic 66 twice.
Rulings (plan log): qd 18 and the Hydra kill stand on session 6's game-written save, now kept with a manifest; qd 22
is raised for the code path in four difficulty and game-type states, the party clause of its statement stays `[I]`;
qd 13's Diablo half stays `[I]` and its static "no special mode-0 record" sentence is `[I]` (the run reached two of
the five targets); us 21's route to H1a is accepted with a reach condition. The Diablo remainders of qd 13 and 16
are **d-owner candidates** (one owner pair, Diablo fresh and done), and qd 25 stays a shortfall: its boundary is
already `[C]` from the owner's Hell session.

| Row | Was | Now | Why |
|---|---|---|---|
| items-quest-drops 13 and 16, the Diablo remainders | raised in part (H6d), remainder `[I]` | **d-owner** (remainder, candidate) | The scripted pilot reached the Chaos Sanctuary but cannot operate the seals. The owner pair proposed in the run record (Diablo fresh, Diablo done) turns both remainders into raises. |

Net effect on the totals: none. The rows stay counted as H6d, as drlg-preset 18's remainder stays counted as S4a.

**Totals after the batch reviews, plan 0039 P1a and P1c, recomputed once (H6d review).** H6d moves one b row between
harness batches. **Static 567, harness 532, c-emu awaiting a batch 0, blocked 415** (d-none 282, d-edit 73, d-sim 28,
d-2c 14, d-owner 10, d-0032 8), **deferred 2, raised 10: 1 526.**

**`lane/rbs` (review 2026-10-17, architect): room-tiles 9 and 20 re-ruled.** The S4b review left both rows a shortfall,
read as "no stock key lacks a candidate". The `lane/w1` review asked for a re-rule: the S4a run already showed stock keys
without a candidate, and the claim is about what the code does then. `sweep_s4a.py pick`, re-run on the lane and its
output hash checked at this review, counts 1 280 picks with no candidate over the 36 logs with `TL` and `TINIT` lines
(run:2026-10-14-collision, run:2026-10-15-objects), and 0 roomk mismatches. A draw in any of them would have moved that
room's k, so a wrong reading could not match by chance. The evidence is in
[drlg/0002 § Plan 0038 batch S4b](../../findings/drlg/0002-room-build-draws.md#plan-0038-batch-s4b-2026-10-16).

| Row | Was | Now | Why |
|---|---|---|---|
| room-tiles 20 (the `(10, 0, 0)` fallback makes no draw) | c, S4b, shortfall | **raised** | 1 280 fallbacks, k matched in every room. |
| room-tiles 9 (no candidate: fallback with no draw, else fatal) | c, S4b, shortfall | **raised in part** | The fallback half as row 20. Remainder `[I]`: the fatal branch (neither the key nor `(10, 0, 0)` has a candidate), met in no log. |

Net effect: none on the totals. Both rows stay counted as S4b, and no class moves. The spec's L337, L600, step note 3
(L621) and L1023 are re-tagged by the spec-writer (backlog).

**`lane/rbs2` (review 2026-10-17, architect): the H5e outdoor remainders, after the static reachability reads.** The
`lane/rbs` and `lane/rbs2` sweeps answered the H5e review's static question for rows 7, 11, 13 and 14, all `[I]`, in
[drlg/0008 § H5e reachability](../../findings/drlg/0008-outdoor.md#h5e-reachability-second-pass-2026-10-17-lanerbs2)
(first pass (a), (d), (e); second pass (b), (c), (e′)). The review re-ran `callee_writes.py` (both outputs), `sweep_h5e.py
stampdefs` and `scan 1 601`; every output matches the manifest `workspace/logs/sweep-rbs2-manifest.txt`.

| Row | Was | Now | Why |
|---|---|---|---|
| outdoor 13, the non-square half (the Blood Moor's `0x20`) | d-none (half), H5e review, on the scan and a condition | **d-none** (half), condition met | (e) and (e′): no writer of `O+0x00` between the cliff-mark skip and the test at 0x0068023B, over the whole callee closure (46 functions, 12 indirect sites read by hand, 21 bare-register writes classified). The remainder is an out-of-range grid index landing on `O`, which nothing on the path computes. It stays a caveat in the finding and does not reopen the half. |
| outdoor 14, 5 or 6 endpoints and the exhausted pool | a-run (H5e), raised in part (the failed search), remainder a shortfall | **d-none** (remainder) | (c): at most 4 endpoints on every stock level (nodes + one cave + at most one bridge; the scan gives 3, 4, 2, 2, 3, 3 on levels 2–7). (d): at most 45 pool nodes against 900. |
| outdoor 11, a waypoint pass with no free cell | a-run (H5e), shortfall | **a-run, shortfall** (unchanged) | (b): no static bound; scan condition printed (fewest free interior cells, minimum 12 of 64 over 52 200 windows). A seed with 0 would take the branch. |
| outdoor 7, a vertex merge | a-run (H5e), shortfall | **a-run, shortfall** (unchanged) | (a): needs an adjacency overlap of exactly 8 tiles or a rect off the 8-tile grid; the condition is stated but not printed by the scan, whose ring-merge counter is 0 over 52 200 windows. Left for the next static sweep (backlog). |

Net effect: none on the totals. Rows 13 and 14 stay counted as H5e, as drlg-preset 18's remainder stays counted as S4a.
The spec's L693 and L866 are reworded by the spec-writer (backlog).

**Totals after the batch reviews, plan 0039 P1a and P1c, `lane/rbs` and `lane/rbs2`, recomputed once (`lane/rbs2`
review).** Neither sweep moves a class. **Static 567, harness 532, c-emu awaiting a batch 0, blocked 415** (d-none 282,
d-edit 73, d-sim 28, d-2c 14, d-owner 10, d-0032 8), **deferred 2, raised 10: 1 526.**

**`lane/rbs3` (review 2026-10-17, architect): outdoor 7 after the printed scan condition.** `sweep_h5e.py scan 1 601`
now tests drlg/0008's vertex-merge condition per window (re-run at the review: identical to the kept output but for the
`systemd-run` banner).

| Row | Was | Now | Why |
|---|---|---|---|
| outdoor 7, a vertex merge | a-run (H5e), shortfall | **a-run, shortfall** (unchanged) | Condition met in 0 of 52 200 windows; the smallest seam overlap is 24 tiles (a multiple of 8 on all 125 seams seen), against the 8 the branch needs. That is a scan of 600 map seeds, not a bound: the overlaps come from the seed-dependent outdoor layout, which no static reading bounds yet. Ruled as row 11 was at the `lane/rbs2` review. A static bound on the layout's level offsets (overlap never 8, origins and sizes on the 8-tile grid) would make it d-none (static sweep queue). |

Net effect: none on the totals. No class moves; the `lane/rbs2` totals stand after merging `main` (`78b96a9`), which
moved no row: **static 567, harness 532, c-emu awaiting a batch 0, blocked 415** (d-none 282, d-edit 73, d-sim 28,
d-2c 14, d-owner 10, d-0032 8), **deferred 2, raised 10: 1 526.**

**`lane/rbs4` (review 2026-10-17, architect): outdoor 7 after the layout bound.** `sweep_rbs4.py layouts` enumerates
each draw of the act link builder (`drlg.act_links`) over the bits it is masked with, independently, a superset of the
layouts any map seed gives; re-run at the review, identical to the kept output (`sweep-rbs4-layouts-2026-10-17.txt`,
manifest `sweep-rbs4-manifest.txt`). The condition is met 0 times over Acts I, II, IV and V and the three
difficulties; the smallest seam overlap is 24 tiles (15 of 288 seams). Act III's jungle layout draws ranged values and
restarts, so it is not enumerated.

| Row | Was | Now | Why |
|---|---|---|---|
| outdoor 7, a vertex merge | a-run (H5e), shortfall | **split: d-none (Acts I, II, IV, V half); a-run, shortfall (Act III half)** | The enumeration is a bound, not a sample, outside Act III ([drlg/0008, H5e (a) layout bound](../../findings/drlg/0008-outdoor.md#h5e-reachability-a-the-layout-bound-2026-10-17-lanerbs4), `[I]`: the link model is `[C]`, the merge rule a code reading). Act III levels 76–83 keep the 600-seed scan (0 of 52 200 windows), a sample. A whole-row d-none would claim Act III on a sample. |

Net effect: none on the totals. The row is one statement and stays counted as H5e (a-run), as outdoor 13's half did at
the `lane/rbs2` review. No other row moves; after merging `main` (`af90ea8`), which moved no inventory row, the totals
stand: **static 567, harness 532, c-emu awaiting a batch 0, blocked 415** (d-none 282, d-edit 73, d-sim 28, d-2c 14,
d-owner 10, d-0032 8), **deferred 2, raised 10: 1 526.** The town-follow case and the `0x400` drop are not inventory
rows; they go to the new harness batch **H7a** (§ 5, § 7).

**H7a (`lifecycle`, run:2026-10-17-h7a-lifecycle, accepted with fixes at the `lane/h7a` review).** H7a holds no inventory row (§ 5); its claims are
plan 0040 Phase 2 shortfalls of [drlg/0009 § 11](../../findings/drlg/0009-room-lifecycle.md#11-phase-2-run2026-10-17-lifecycle),
reported in [§ 11.3](../../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle):
the `0x400` drop raised in part (the alignment-2 half; alignment 1 unreached), the expired-item drop at the restore
raised, the expiry sweep's period corrected (1 500 frames, a reading), the town-follow case's recipe (b) a recorded
shortfall after the geometry scan and recipe (c) withdrawn on the static read. `rooms.py check`: 4 mismatches over
675 849 checks, one kind (the record's `+0xC4` bit `0x2000`, § 11.3 (5)).

Net effect: none on the totals. After merging `main` (`c0c99f6`), which moved no inventory row, they stand: **static
567, harness 532, c-emu awaiting a batch 0, blocked 415** (d-none 282, d-edit 73, d-sim 28, d-2c 14, d-owner 10,
d-0032 8), **deferred 2, raised 10: 1 526.**

**H5b (`objects`, run:2026-10-19-h5b-objects, accepted with fixes at the `lane/h5b` review, 2026-10-20).** 28 rows,
33 statements ([objects/0001 § Plan 0038 batch H5b](../../findings/objects/0001-object-population.md#plan-0038-batch-h5b-run2026-10-19-h5b-objects),
[drlg/0005 § Plan 0038 batch H5b](../../findings/drlg/0005-collision.md#plan-0038-batch-h5b-run2026-10-19-h5b-objects)):
raised 10 rows (collision 27, 39; objects 13, 16, 17, 40, 45, 50, 51, 52), raised in part 11 (collision 37; objects 3,
4, 15, 23, 26, 27, 36, 38, 41, 42), shortfall 7 (objects 6, 19, 20, 35, 39, 46, 49). `objects.py check` re-run at the
review: 234 315 checks, 1 failure (the cave log's logger error, kept), and 150 314, 0 mismatches, on the 29 older logs.

| Row | Was | Now | Why |
|---|---|---|---|
| objects 20 (orientation-2 shrine placement) | a-run, H5b, shortfall | **d-none** | `OBJ_PlaceByOrientation` has one call (`0x00552C32`, no other reference in the image), which passes the ObjGroup member's `Orientation`; of the 88 `PopulateFn`-2 member slots none has 2 (`sweep_h5b.py static`). |
| collision 37 and objects 23, the `0x804` half | a-run, H5b | **d-none** (half) | `UNIT_GetCollMask` returns `0x804` only for a door with `BlocksVis` 0 and `BlockMissile` non-zero; the 7 stock `IsDoor` records with `BlocksVis` 0 all have `BlockMissile` 0. The `0x400` half is raised. |
| objects 38, the "after a `PreOperate`" half | a-run, H5b | **d-none** (half) | Neither class 371 nor any class the 581 handler draws has `PreOperate`. The level-25 `SetMode(0)` half is raised. |

Net effect: objects 20 is one statement: harness −1, d-none +1. The three halves are of one-statement rows and stay
counted as H5b, as outdoor 13's half did at the `lane/rbs2` review. After merging `main` (`f8de60b`), which moved no
inventory row since H7a, the totals are: **static 567, harness 531, c-emu awaiting a batch 0, blocked 416** (d-none 283,
d-edit 73, d-sim 28, d-2c 14, d-owner 10, d-0032 8), **deferred 2, raised 10: 1 526.**

**H2a (filed 2026-10-20, reverser, `lane/h2a`; accepted with fixes at the `lane/h2a` review, 2026-10-20): 15 rows, 17 statements of items/tc and items/quality.**
run:2026-10-20-sweep-items-tc, 12 sessions on slot 2, stock data, 0 mismatches (`sweep_h2a.py logs` 0 bad, `tc.py
replay` 873/873, `quality.py` 720/720, `uniques.py` 1022/1022). The lane files **12 raised, 5 raised in part, 0
shortfall, 0 reclassified**. The evidence is in the "Plan 0038 batch H2a" sections of
[items/0001](../../findings/items/0001-tc-resolution.md#plan-0038-batch-h2a-2026-10-20) and
[items/0002](../../findings/items/0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20).

- **Raised (12):** tc 1, 2, 11, 34 (L361), 37, 45, 47, 59, 71; quality 22 (2), 23.
- **Raised in part (5):** tc 22 (remainder the `bonewall` fatal error, shortfall), tc 34 (L388; remainder `Picks = 0`,
  d-none as row 13), tc 60 (the type-equivalence half d-none on stock data, signedness `[I]`), tc 70 (game type 1,
  types outside 1–3, a floor below the live count), quality 20 (a missing owner, plain and minion monster killers,
  killer type ≥ 2).
- **Correction carried (rule 12):** quality 22's "the clamp never acted" held for the plan 0010 runs only; the clamp
  acts in 667 rolls of the later item runs and the H2a logs, and decides 138 of them.

The review re-ran the checkers on the kept logs (same outputs) and moved no row: tc 34's `Picks = 0` half is the
statement of tc 13 (already d-none) and stays counted as H2a, as the H5b halves did; quality 20's 5 hireling rolls from
the aborted H6d log under `failed/` count (kept, hashed, in the H6d run list; the raise stands without them).

Net effect on the totals: none (no class moves; the remainders stay counted as H2a). Recomputed at the review, after
merging `main` (`5a7feb3`, the H5b review above; nothing newer), they stand: **static 567, harness 531, c-emu awaiting a batch 0, blocked 416** (d-none 283,
d-edit 73, d-sim 28, d-2c 14, d-owner 10, d-0032 8), **deferred 2, raised 10: 1 526.**

**Plan 0044 Phase 3 (`lane/p44s`, accepted with fixes at its review, 2026-10-20): the d-2c rows raised by
run:2026-10-20-two-clients.** No batch of this plan ran them; plan 0044's two-client run and re-tag did
([plan 0044 log](../done/0044-multiplayer-branches.md#implementation-log), Phase 3 review ruling (c);
[multiplayer/0001 § 6](../../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients)). They
leave the blocked count for the raised column, labelled *raised by plan 0044*; Phase 3 of this plan has nothing left to
re-tag for them.

- **Raised (7 statements, d-2c → raised):** tc 46 (`/players` with real players, items/tc F2); vendors 1 (the
  `TownPlayerRemove` entry row), 10 (the shared stock, A2), 13 (`sole` with two interactors, C1), 16 (the game leave
  and Harrogath, C2); hirelings 11 (one table per game, § C); player/creation 31 (J4 for two members).
- **Raised in part, stay d-2c for the remainder (3):** tc 43 (the dead member and the monster killer's owner raised;
  three or more players and the clamp at 8 remain), tc 44 (the dead member raised; a member without a room remains),
  player/creation 6 (the 89/256 bonus raised; the 6400 bound's edge remains).
- **Not raised (stay d-2c):** vendors 17 (MP11, the branch with an interactor, kept `[I]`: the stale byte is not
  logged). The partial halves stay as § 3 lists them: player/creation 33's party half (MP17), tc 27's party half
  (MP13), quest-drops 6, 12, 36 and 25's n > 1 part (MP12–MP14), the trade part of sockets 22 (MP18); all are named
  shortfalls of plan 0044, routed to the owner-play and reverser entries.

Net effect, recomputed once at the review over every reviewed batch above, after merging `main` (up to date at
`26d8978`; the H2a totals were the last): d-2c 14 → 7, raised 10 → 17. **Static 567, harness 531, c-emu awaiting a
batch 0, blocked 409** (d-none 283, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17:
1 526.**

**H2b (filed 2026-10-20, reverser, `lane/h2b`; accepted with fixes at the `lane/h2b` review, 2026-10-20): 25 statements of items/affixes, tc, uniques-sets,
properties and sockets-runewords.** run:2026-10-20-sweep-items-chain, 13 kept sessions on slot 2 (17 launches of 20),
stock data, 0 mismatches (`sweep_h2b.py logs` 0 bad, `tc.py replay` 1 118/1 118, `items_chain.py both`, `uniques.py`
and the seed model 1 043/1 043, `quality.py` 1 022/1 022, `cube.py` 26/26). The lane files **14 raised, 5 raised in
part, 1 shortfall, 5 reclassified (d-none)**. The evidence is in the "Plan 0038 batch H2b" sections of
[items/0001](../../findings/items/0001-tc-resolution.md#plan-0038-batch-h2b-2026-10-20),
[0004](../../findings/items/0004-uniques-sets.md#plan-0038-batch-h2b-2026-10-20),
[0005](../../findings/items/0005-affixes.md#plan-0038-batch-h2b-2026-10-20),
[0006](../../findings/items/0006-properties.md#plan-0038-batch-h2b-2026-10-20) and
[0007](../../findings/items/0007-sockets-runewords.md#plan-0038-batch-h2b-2026-10-20).

- **Raised (14):** tc 68; uniques-sets 9, 39; affixes 5, 13 (2), 17, 19 (2), 21 (3); properties 20 (2).
- **Raised in part (5):** tc 58 (the classic `version ≥ 100` refusal, d-none as row 74), uniques-sets 7 (entry from a
  failed unique or set; the normal builder), uniques-sets 35 (a failed superior step and the normal step; `Rare` 0),
  affixes 24 (the "no affix" cause, d-none as aff 20; the discard of a rare's draws), sockets 42 (the quality branches,
  a request above the final cap, the `cap < 1` return; scoped at the review: every logged request lay in `1..cap`, so
  `max(n, 1)` and the clamp of the write are in the remainder too).
- **Shortfall (1):** properties 24 (no superior ethereal `dur%` item in 1 043 creations).
- **S2c's piece of sockets 44** (the row stays S2c's, raised in part): normal and superior unclamped `[C]`; no request of
  4 or more and no low-quality call, so the piece is met in part.
- **H2c companion** (§ 6): no func 12, 23 or 24 slot in the run's creations.

| Row | Was | Now | Why |
|---|---|---|---|
| items-uniques-sets 10 (type-11 setup draws on the item seed first; 1) | a-run, H2b | **d-none** | `ItemInitStats` calls the setup only for base type 11 (`cmp eax, 0xB` at 0x00557DE7, an exact test). Type 11 is `elix`, one record `elx`: no TreasureClassEx cell names it, `elix` has `TreasureClass` 0, no cubemain output names it or its type, no vendor cell, no other table (`sweep_h2b.py static`). |
| items-properties 7 (the type-11 setup, A5 line, A5 note, H3; 3) | a-run, H2b | **d-none** | The same function and the same full-table check. |
| items-affixes 20 (rare build fails with no prefix and no suffix, E5; 1) | a-run, H2b | **d-none** | `sweep_h2b.py rareboth`: the only base x version x ilvl with both names and no affix on either side is `jew` at item version 1 (99 cases), a jewel in a classic game, which no stock path makes; the classic throwables fail at the names first (aff 21). |

Net effect on the totals: harness −5 (531 → 526), d-none +5 (283 → 288), blocked 409 → 414; the remainders of the
raised-in-part rows and the shortfall stay counted as H2b. The review merged `main` (`9ef5f84`, the plan 0044 Phase 3
totals above; nothing newer) into `lane/h2b` and moved no further row; the three moves stand (the static check of
`elix` extended at the review to the pinned image: no `elx` code in it, run:2026-10-20-sweep-items-chain *Review
checks*). Recomputed once over every reviewed batch above: **static 567, harness 526, c-emu awaiting a batch 0,
blocked 414** (d-none 288, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**

**H2c (filed 2026-10-21, reverser, `lane/h2c`; forced; accepted with fixes at the `lane/h2c` review, 2026-10-21): 7
statements of items/tc and items/properties.** run:2026-10-21-throw-forced (three sessions, classic Normal, `Act 1 Junk` naming `tkf`, `tax`,
`jav`) and run:2026-10-21-tcnamed-props-forced (seven sessions, Hell, Eldritch's and Hephasto's TCs naming *Ormus'
Robes*, *Ethereal Edge* and the func-24 carrier *Tomb Reaver*), slot 2, 12 launches, 10 kept logs, each table a loose
`treasureclassex.bin` under `-direct` (§ 6 rulings 1 and 2; the read lists committed before the run). 0 mismatches
(`sweep_h2c.py logs` 0 failed, `tc.py replay` 677/677, `items_chain.py both`, `uniques.py` and `props.py` 580/580,
`quality.py` 1 496/1 496). The lane files **4 raised, 2 raised in part, 1 shortfall** (7 statements in six rows; tc 10
counts two). The evidence is in the "Plan 0038 batch H2c" sections of
[items/0001](../../findings/items/0001-tc-resolution.md#plan-0038-batch-h2c-2026-10-21) and
[items/0006](../../findings/items/0006-properties.md#plan-0038-batch-h2c-2026-10-21).

- **Raised (4 statements):** tc 10 (2: the bound of 10 per call and the Long Sword `lsd`), tc 55 (the type test after
  the quality roll, classic only, with the stock expansion control), properties 12 (spec L390, func 12).
- **Raised in part (2):** tc 56 (the Long Sword half; the `version ≥ 100` reject d-none, as ruling 1 said), properties
  14 (func 23's make branch; the two skips, an item already ethereal or without durability, not reached).
- **Shortfall (1):** properties 15 (func 24: no Hephasto met, so no *Tomb Reaver*; heph-c and heph-e stopped short of
  the Hellforge, heph-d and heph-f died).

Net effect on the totals: none proposed (no class moves; the remainders and the shortfall stay counted as H2c). Taken
against `main` after merging it into the lane (`3d1cc99`; the H2b review's totals above are the latest in this
section): **static 567, harness 526, c-emu awaiting a batch 0, blocked 414** (d-none 288, d-edit 73, d-sim 28, d-2c 7,
d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.** The review found `main` moved to `20c33d7` (`lane/srng`,
plan 0046 and rng/seeds only, no inventory row); the merge of `main` into the lane was refused by the session's
permission layer and is left to the orchestrator's merge. No row moved; the totals stand as filed. The review raised
`sub_00633680_ItemIndexByCode` I → C (symbols only, no row) and scoped prop 14's `[C]` wording (no `PROP_WriteStat`
call; the weapon base-stat changes of `ITEMS_MakeEthereal` are in the list check). prop 15 stays an H2c shortfall,
counted as harness; its open route is an owner-played Hellforge session or a pilot that reaches the room.

**H4a (filed 2026-10-25, reverser, `lane/h4a`; accepted with fixes at the `lane/h4a` review, 2026-10-25): 32 statements of monsters/pool, spawn, special, stats and
items/quest-drops.** run:2026-10-21-sweep-monsters-a, twelve kept sessions on slot 1 (expansion Nightmare, `UniqNova`;
nine development logs of the Chaos Sanctuary attempts kept apart), stock data. `sweep_h4a.py check` bad 0 in every part
on the twelve logs and on 63 kept logs of the earlier monster runs and run:2026-10-20-chain; `monstats.py` 0 mismatches
on all twelve (the chained `monspawn.py` and DRLG models' mismatches on three logs, none on a tag these rows rest on,
are listed in the record). The lane files **16 raised, 8 raised in part, 8 shortfall**; the review moves special 54 to raised in part
(**15 raised, 9 raised in part, 8 shortfall**). The evidence is in the "Plan
0038 batch H4a" sections of
[monsters/0001](../../findings/monsters/0001-level-pool.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a),
[0002](../../findings/monsters/0002-room-population.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a),
[0003](../../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a),
[0004](../../findings/monsters/0004-stats.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a) and
[items/0010](../../findings/items/0010-quest-drops.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a).

- **Raised (15):** pool 12; quest-drops 48; stats 7, 18; spawn 5, 49 (the operand route of S2c ruling 2: the class
  list read at 0x00731B2C/0x00731B30 with objdump and r2, three readers and no writer); special 30, 35, 48 (on the
  kept logs: three refusals), 50 (the aura half, with an extra-pick control), 51, 55, 58, 60, 68.
- **Raised in part (9):** special 54 (review: filed raised; r = 0 only, so the `+ r` of the `skeleton5` count stays
  `[I]`; the draw's place holds for any r); stats 21 (one stock row per class; the level skip, a second row, `n` 2 or 3 and an occupied
  location are d-none on stock data, as the chain run's review found); spawn 47 (the tick's gate, the roll's one step
  and the no-spawn branch, on the one roll met; the mask's width, room `+0x78` and the spawn branch remain) and spawn 48
  (**with a correction:** the roll did fire, once, in the Chaos Sanctuary); special 34 (rows 10 and 13; 11, 14 and 15
  in no logged list), 46 and 52 (records 10, 26, 27, 29, 36, 38, 42 and 60, and the no-tail records; tails 6, 37, 39,
  43–45 and 62 not met), 56 (records 36 and 38; 37 not met), 69 (156, 242 and 256; the other fixed-name classes not met).
- **Shortfall (8):** spawn 11 (91 gate calls in level 108, all with byte 0 and an open gate; the closed state needs
  the three seal bosses dead); special 9, 10, 25, 31, 38 and 50's thief half (all need Lord De Seis: seal 394 was
  logged but never operated, the pilot finding no hop towards it); special 59 (no Ancients recipe). Route for the seven
  De Seis and gate rows: an owner-played Chaos Sanctuary session with `tools/gdb/mon-h4a-obj.gdb`; for 59, a
  quest-open recipe or owner play.
- **H4b pieces met** (the rows stay counted as H4b): stats 14 and 13's class 312 (`doomknight3`, 63 creations, both
  appearance bytes = `Range(4)`, every value 0–3 met); special 66's mod 12 (Blood Raven's client name). Not met: a
  `willowisp` special (stats 40), an aura special at level ≤ 15 (special 27's clamp at 1), a Shrines code-20 shrine
  (special 2, 74), the camel at `/players` 8 (stats 23). S3b pieces (Druid Raven in Normal; Durance 3 in Normal): not
  run.

Net effect on the totals: none proposed (no class moves; the remainders and the shortfalls stay counted as H4a). Taken
against `main` after merging it into the lane (`e3ac907`; the H2c review's totals above are the latest in this
section): **static 567, harness 526, c-emu awaiting a batch 0, blocked 414** (d-none 288, d-edit 73, d-sim 28, d-2c 7,
d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**

**`lane/h4a` review (architect, 2026-10-25): accept with fixes.** The checks were re-run on the review side
(`check/run-checks.sh` into the review's scratch, under `MemoryMax=4G`): `sweep-check.txt`, `check-kept-final.txt`,
`monstats-h4a.txt`, `aura-control.txt` and `doomknight3-app.txt` byte-identical to the kept files; both manifests pass
`sha256sum -c`; the tool hashes cited in the record match the lane's tree. Spot reads of the pinned `Game.exe` with
objdump: `WandererSpawn`'s act bound and the three readers of 0x00731B2C/0x00731B30 (bytes `0e010000 0001 0000 0000
0000 0000`), `RoomWandererTick`'s `test eax, 0x7FFF` and `WandererRoll`'s `mod 100` against 3, the gate's `cmp eax, 0x6C`
and quest call (0x0054EC1B–0x0054EC29), the `boss`/`noRatio` masks at 0x00573E2E (`.rdata` 0x40 and 0x04), Radament's
`add ebx, 2` loop (0x005A4CD1), class 312's one `Range(4)` stored at `+0x0E` and `+0x0F`, and the 43 slots of
`g_UModHandlers` in the image (null rows as the run's memory read). Fixes: special 54 moved from raised to **raised in
part** (only r = 0 met, so the `+ r` of the `skeleton5` count is not separated); pool 12's "six of the 25" corrected to
five, and pool 12 and quest-drops 48 now say how the `(H)` half rests (the branch, and Andariel's hell creation); the H4b
section's class-312 remainder marked met. Rulings: the seven De Seis and gate shortfalls stay harness, counted as H4a, and
are a candidate for the plan's `d-owner` addendum at the close (Open questions), not routed to the owner now; a pilot that
reaches seal 394 is the other route. Stats 14 and 13 are raised whole by the class-312 piece (still counted as H4b, a
Phase 3 note, not a class move). The three chained-model mismatches go to their own reverser entry
([2026-10-25-architect-reverser-h4a-chained-model-mismatches-council-nihl2](../../backlog/archive/2026-10-25-architect-reverser-h4a-chained-model-mismatches-council-nihl2.md)).
*(`lane/rbd` review, 2026-10-27: all three resolved as model or logger gaps; no row, class or total moves; special
§ J's 526 case is a Phase 3 split of row 73's remainder. See the plan 0038 log.)*
**Ledger: raised 15, raised in part 9, shortfall 8.** No class move; totals unchanged and recounted against `main`
`9e221ed` after merging it (no inventory change since `e3ac907`): **static 567, harness 526, c-emu awaiting a batch 0,
blocked 414** (d-none 288, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**

**H5d (filed 2026-10-27, reverser, `lane/h5d`; accepted with fixes at the `lane/h5d` review, 2026-10-27): 17 statements of drlg/collision and monsters/spawn 41.**
run:2026-10-27-sweep-collision, nine kept sessions on slot 1 (expansion Normal, `UniqNova`; the 2026-10-25 launch
stopped at start kept in `dev/`), stock data, logger `tools/gdb/collision-h5d.gdb` with before / after cell pairs.
`collision.py check` on the nine logs: collision 26 913 checks, 0 mismatches; monspawn 3 mismatches, none on these rows
(two session ends cut by the slot stop, one `objects.py` operate of the Rogue Encampment waypoint, created in mode 1 and in mode 2 at its one operate with no
logged line between: corrected at the review, which routes it to a reverser entry). The evidence is in
the "Plan 0038 batch H5d" sections of
[drlg/0005](../../findings/drlg/0005-collision.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision) and
[monsters/0002](../../findings/monsters/0002-room-population.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision).

- **Raised (11):** collision 5 (on 1 330 kept logs and the sessions: `spawnCol` 1 → `0x01C0` on 271 tests, 3 → `0` on
  837), 8 (Harrogath, 1 044 cells only the `0x04` OR explains, two kept logs), 19 and 36 (271 item marks, one cell
  `0x200`), 24 (sizes 0 and 1, 36 presets-window tests, 5 separating), 30's two statements (patterns 3 and 4, marks and
  unmarks before / after), 45's 228, 298-with-flag-0 and 528 statements (each with separating cases); spawn 41.
- **Raised in part (3):** collision 1 (the call from `Bit2TileMerge` with an active room, 37 calls; its write into an
  active neighbour not reached), 21 (bit 13's writers, **with a correction**: `MonIsNpc` is `npc` **or** `inTown`, 0
  mismatches on 38 338 creation marks against 254 for `npc` alone; the unit `+0xC4` bit 31 branch stays `[I]`), 46
  (levels 46, 74 and 125: one level-seed step per lookup; the operand, `n` ≥ 2, not separated).
- **Shortfall (2):** collision 9 and 11 (B1's clear and re-stamp): no call had its tile in a reachable room.
- **Proposed d-none (1):** collision 45's 334 statement (`suckernest1`): no table names a class 334–337 as a creation,
  and none of the 81 `.text` immediates 334–337 passes one to a creation (`sweep_h5d.py static`).
- **H4b piece** (spawn 42, still counted as H4b): 228 met (4 presets-window offset-cell tests predicted); 334 as above.
  The H4b follow-ups entry's H5d piece is annotated.

| Row | Was | Now (proposed) | Why |
|---|---|---|---|
| drlg-collision 45, the 334 statement (`SpawnClassCellTest` for `suckernest1`) | a-run, H5d | **d-none** | No stock creation source of a `BaseId` 334 class (tables and code; drlg/0005 § H5d). The statement stays `[I]` as a reading. |

Net effect on the totals (proposed): harness −1, d-none +1. Taken against `main` after merging it into the lane
(`0e3f501`; the H4a review's totals above are the latest in this section): **static 567, harness 525, c-emu awaiting
a batch 0, blocked 415** (d-none 289, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17:
1 526.**

**`lane/h5d` review (architect, 2026-10-27): accept with fixes.** The checks were re-run on the review side
(`check/run-checks.sh` into the review's scratch, under `MemoryMax=4G`, and `sweep_h5d.py static`): all seven outputs
byte-identical to the kept files; both manifests pass `sha256sum -c` and hash as the record cites (`f9f6c4c4…`,
`1b3aba39…`); the eight tool hashes cited match the lane's tree. Spot reads of the pinned `Game.exe` with objdump:
`MonIsNpc` (0x0063E89A–0x0063E8BD: `+0x0D` & `.rdata` 0x006CE268 = 1, then & 0x006CE270 = 4, then `+0xC4` bit 31),
`PATH_PatternFromSize`'s flag-9 test and 1 → 3, 2 → 4 (0x006485B0–0x006485D7), `g_CollPatternBySize` {0, 1, 1, 2},
`MonSpawnTry`'s `spawnCol` 1 branch (0x005B2B7E; 0x102–0x107 and 0x99 to the ring at 0x005B2B90–0x005B2BA6), the
`SpawnClassCellTest` callers 0x005B2D90, 0x005F6AE5, 0x005F9F9D and 0x005E62BC, the `MK0` call at 0x005B2DA8, the
`TileCollisionUpdate` call returning to 0x0066E91B, `UNIT_CollMarkRect`'s `RectOrWH` call at 0x00620ACA, and the
`MosquitoNest` AI's 334 at 0x005E02E8–0x005E0322 (a `SpawnClassCellTest` argument, then `MonAiUseSkill`; only classes
334–337 carry that AI). Fixes: (1) collision 21's `npc` half is `[I]`: the five stock rows with `npc` and without
`inTown` (406, 527, 537–539) all have `interact`, so an `inTown`-only reading also scores 0 on the 38 338 marks; the
`[C]` of the correction is its `inTown` half (drlg/0005 § 5, the summary and § H5d rewritten to the corrected rule,
an open question added); (2) spawn 41 moved from raised to **raised in part** (its "others" half, `0xFFFF`, is d-none
as drlg/collision row 3); (3) the record's 318 pattern-5 creations recounted to 360 (`check/patterns.txt`); (4) the
rogue mismatch's description corrected (no second click: the unit left its creation in mode 1 and was in mode 2 at its
one operate); (5) collision 5's refinement names 260 and 263 as not met; (6) drlg/0005's Functions-table row for
`COLL_RectOrWH` / `COLL_RectClearWH` scoped to C / I. Rulings: rows 5 and 8 count as H5d raises, a-logs in effect (as
H4b's kept-log raises); collision 45's 334 statement moves to **d-none**, and no Act III session is owed; spawn 42 is
raised in part (206, 228, 298, 528 `[C]`, 334 d-none), still counted as H4b, a Phase 3 note; collision 46 stays raised in
part (with one match per lookup every operand picks the same point; the remainder stays `[I]`, counted as H5d); the
rogue mismatch goes to its own reverser entry
([2026-10-27-architect-reverser-h5d-objects-py-waypoint-mode-after-arrival](../../backlog/2026-10-27-architect-reverser-h5d-objects-py-waypoint-mode-after-arrival.md)).
**Ledger: raised 10, raised in part 4, shortfall 2, d-none 1.** One class move (collision 45's 334, harness −1, d-none
+1); totals recounted against `main` `0e3f501` (no inventory change on `main` since): **static 567, harness 525, c-emu
awaiting a batch 0, blocked 415** (d-none 289, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2,
raised 17: 1 526.**

**H1b (filed 2026-10-27, reverser, `lane/h1b`): 48 statements of save/d2s and hirelings.** run:2026-10-27-sweep-d2s-play,
13 kept sessions on slot 1 (expansion; Normal, Hell, one TCP/IP host), tool-built characters and two game-written
samples, logger `tools/gdb/d2s-h1b.gdb` in two revisions (the record gives the difference; rw-r2 was rerun under
revision 2 at the resume for the write-side runeword check). `sweep_h1b.py check` on the 13 logs: **2 798 comparisons,
0 failing** (`check/sweep-h1b-check-r2.txt`, manifest `h1b-manifest-r2.sha256`). The evidence is in the "Plan 0038
batch H1b" sections of [save/0001](../../findings/save/0001-d2s-io.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play)
and [hirelings/0001](../../findings/hirelings/0001-hirelings.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play). The
batch is 46 inventory statements (save-d2s 45, hirelings 1) and rows 117 and 124, moved c → b into H1b at the S1a
review.

- **Raised (25):** save-d2s 4, 21, 25, 33 (2), 34 (2), 35, 37, 39 (2), 40, 41, 42, 43, 55, 56, 57, 108, 111, 112, 113,
  125, 127; hirelings 24.
- **Raised in part (14):** save-d2s 2 (the no-callback half), 6 (the death caller 0x0057FD88 and no single-player
  autosave; `0x0052E2A0` not reached), 18 (the file and client-buffer branches; no callback), 31 (item refs 0 only), 48
  (the name reset past `+0x116`: the builder refuses it), 60 (negative gold), 72 (one corpse; count ≥ 2 and the first
  u32), 73 (no golem item), 83 (356 only; gold and realm), 88 (`+0x82` only; `0xFFFF`), 102 (no low-quality item), 115
  (the copy; no socketed copy), 116 (no pickup of an item with the bit), 118 (no negative value: arithmetic not
  separated).
- **Shortfall (7):** save-d2s 1, 3, 19 (no host callback; the shutdown save found no game), 110 (the watchpoint logged
  no hit: no working control), 114 (no gold pile), 117 (no separating case), 124 (the builder refuses a lone follower;
  archivist entry). *(2026-10-27, `lane/r1h` review: rows 3 and 19 moved to d-none, so 5 shortfalls remain, below.)*
- **Proposed d-none (2):** save-d2s 77 and 78, by their own route ("else reclass d-none"): no item record in mode 3 or
  5 in any write or read of the run.
- **S1a pieces met** (the rows stay S1a): 20, 24, 32; 123, 130 and 138 in part (group 52). Not met: 71, 86, 103, 128.

| Row | Was | Now (proposed) | Why |
|---|---|---|---|
| save-d2s 77 (modes 3/5: world position) | b, H1b | **d-none** | No save path of the run holds a mode 3/5 item record, the corpse session included; the row's route names d-none for that case. The statement stays `[I]` as a reading. |
| save-d2s 78 (modes 3/5: no body and no store) | b, H1b | **d-none** | As row 77. |

Net effect on the totals (proposed): harness −2, d-none +2. Taken against `main` after merging it into the lane
(`e88e8e2`; the `lane/h5d` review's totals above are the latest in this section, and no inventory change has landed on
`main` since): **static 567, harness 523, c-emu awaiting a batch 0, blocked 417** (d-none 291, d-edit 73, d-sim 28,
d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**

**`lane/h1b` review (2026-10-27, architect): accept with fixes (6).** The ledger stands as filed: **raised 25, raised in
part 14, shortfall 7, d-none 2** (rows 77 and 78 moved; no other class move). Recounted against `main` after merging it
into the lane (`3c90008`; no inventory change on `main` since `e88e8e2`): **static 567, harness 523, c-emu awaiting a
batch 0, blocked 417** (d-none 291, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17:
1 526.** Fixes: (1) row 4's chain names the frames between `PlayerLoad` and the logged returns,
`sub_005344B0_PlayerLoadFromFile` and `sub_00534520_PlayerLoadFromClient` (each with one call site, 0x005345DB and
0x005345FB); (2) row 2's `[C]` is scoped to the outcome: the run does not show which of `AutosaveTick`'s tests stopped
the save (the entry test of `0x00730FFC` at 0x0052D353, the time tests, or the callback test at 0x0052D3D9); (3)
`D2S_WriteMercItems` raised I → C with `D2S_ReadMercItems` (rule 14, row 73); (4) the record's dev manifest is
checked from `workspace/logs/h1b/dev`, not `workspace/logs/h1b`; (5) the record names every overwritten save copy
(rt-r2, qr-r2, qrh-r2, rw-r2 and drop 27111, under the session names without the suffix); (6) row 1's "game list
already empty" is a reading, since the `SHUT` line does not log the list. Rulings: the seven revision-1 logs are
accepted as they stand; the death save is an event save, so the spec's caller list is not contradicted; rows 1, 3 and
19 stay shortfalls, not d-2c, and rows 3 and 19 (with the callback halves of 2 and 18) are candidates for d-none, since
the only writer of the host callback, 0x0052C0E0, has no call site or pointer in the image (reverser entry); row 110's
shortfall is right, because a watchpoint that missed a logged clear is no control; row 39's read half and row 56's
raise stand; stat 30 = experience.txt row L (index L + 1 counting `MaxLvl`; `EXP_GetThreshold` indexes `class + 8L +
8`, 0x00611814).

**`lane/r1h` (2026-10-27, reverser): the host-callback setter, ruling (d) of the `lane/h1b` review.** Ghidra
(`tools/ghidra.sh findptr`, references of any type) and a raw byte scan of the image (the VA or RVA at any alignment,
instruction immediates, relative branches in disassembled and undisassembled bytes, exports, fall-through) find
nothing that reaches `sub_0052C0E0_SetHostSaveCallback`, the only writer of the host callback `0x00883D50`. Each
channel found its control in the same run, and the callback starts at 0 (zero-filled `.data`)
([save/0001 § Plan 0038 r1h](../../findings/save/0001-d2s-io.md#plan-0038-r1h-the-host-callback-setter-and-the-d2sio-model-2026-10-27)).
Proposed (accepted at the `lane/r1h` review, below):

| Row | Was | Now (proposed) | Why |
|---|---|---|---|
| save-d2s 3 (hosted save through the callback) | b, H1b, shortfall | **d-none** | The callback is never set on this image: its setter has no caller (`findptr` 0 on all six channels). The statement stays `[I]` as a reading. |
| save-d2s 19 (`SaveViaCallback`'s masked comparison) | b, H1b, shortfall | **d-none** | As row 3: `sub_00531EB0_SaveViaCallback` runs only with the callback set. |
| save-d2s 2, the callback half | raised in part (H1b), remainder `[I]` | **d-none** (the half only; the row stays counted as H1b, raised in part) | As row 3. |
| save-d2s 18, the callback branch | raised in part (H1b), remainder `[I]` | **d-none** (the half only; the row stays counted as H1b, raised in part) | As row 3. |

Net effect on the totals (proposed): harness −2, d-none +2. Taken against `main` `2b087d2c`, the lane's base: no
inventory change has landed on `main` since the `lane/h1b` review totals above. **static 567, harness 521, c-emu
awaiting a batch 0, blocked 419** (d-none 293, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2,
raised 17: 1 526.** H1b's ledger becomes raised 25, raised in part 14, shortfall 5 (rows 1, 110, 114, 117, 124),
d-none 4 (rows 3, 19, 77, 78): 48.

**`lane/r1h` review (2026-10-27, architect): accept with fixes (3).** The four moves above are **accepted**: rows 3
and 19 shortfall → d-none, and the callback halves of rows 2 and 18 d-none as halves, with both rows still counted as
H1b, raised in part. The statements stay `[I]`. d-none with an `[I]` absence fits the class. The class is "no
observable (dead code, …)", and it raises nothing, so its reason may be a reading, as at tc 41 and outdoor 10. The
reason is recorded, and finding a caller of 0x0052C0E0 (a computed target included) moves rows 3 and 19 back to (b).
The undisassembled read at 0x0052BFCF does not change ruling (d). It runs only when `0x00883D54` is non-zero, which only
the setter writes, and a raw scan finds nothing that reaches 0x0052BFC0. **H1b's ledger: raised 25, raised in part
14, shortfall 5, d-none 4: 48.** Recounted against `main` after merging it into the lane (`2637b081`; `lane/p50b`
changed no inventory row): **static 567, harness 521, c-emu awaiting a batch 0, blocked 419** (d-none 293, d-edit 73,
d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**
**H3b (filed 2026-10-27, reverser, `lane/h3b`): 25 statements of data/README, data/excel and data/strings, plus the S1b
remainders of data/README 1 and data/excel 30.** run:2026-10-27-sweep-data-load, seven program runs on slot 2 (stock,
`-txt`, loose files, `-direct`, `-direct -txt`, `-direct` with a loose `use` byte of 0x0B and of 0x0E), stock tables,
gdb on the game **before its startup code**: review ruling 3's start mode, `tools/d2run.py --early`, built and tested
first (a stopped dummy process, then probe runs on slot 2), works (the stop 0.50–0.57 s after launch; every startup
global still 0 at the attach). Logger `tools/gdb/excel.gdb` (pilot.py, strings.py and the new excel.py); checker
`tools/sweep_h3b.py check` over the seven logs: 0 mismatches; `tools/tbl.py check`: 0. The evidence is in the "Plan 0038
batch H3b" sections of [data/0001](../../findings/data/0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load),
[data/0002](../../findings/data/0002-mpq-precedence.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load),
[data/0003](../../findings/data/0003-string-tables.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load),
[data/0004](../../findings/data/0004-cell-converters.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load) and
[player/0001](../../findings/player/0001-creation.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load).

- **Raised (18):** data/README 2, 3, 4; data/excel 1, 2, 3, 4, 5, 6, 7, 17, 18, 20, 24, 25 (with a refinement: the
  character-graphics loader and the `*code.bin` reads also go through `FILE_LoadWhole`), 27 (`-txt` alone: the 191
  excel reads are the archive copies, `monstats.bin` separating; `-direct -txt`: the 95 reads of written files from
  disk, the compiled `monstats` in memory), 50; data/strings 29 (50 and 29: the bytes 0x0B → 11 and 0x0E → 0 separate
  the byte read and the clamp).
- **Raised in part (7):** data/README 5 and data/excel 8 (the name → TC map through `EXCEL_FindName` on `g_TCLink`, 3 728
  lines; **correction**: `TC_GetByName` has no reference and no hit, so its half is dead code, d-none as a remainder);
  data/excel 71 (the filled fields and the padding over 60 dumps; the values of monstats `+0x036`/`+0x038`,
  `+0x04A`/`+0x04B` not modelled; **refinement**: levels `+0x033..+0x035` are filled too), 74 (the not-found fallback
  not reached); data/strings 2 and 6 (no count above 1: the release that keeps the tables and the load that only counts
  not reached), 22 (the raw name for a stored index 0 not reached).
- **Shortfall (0).** The 9 startup rows need no shortfall: the start mode worked.
- **S1b remainders** (counted as S1b): data/README 1's "only under `-direct`" **raised** (the loose run reads none of
  its three loose files; the direct run reads all three); data/excel 30's "a stock run never loads them" **raised in
  part** (no code-list `DATATBLS_LoadTable` call in four stock-mode runs) **with a correction**: `hitclass.bin` is read
  whole at every start by the character-graphics loader (return 0x0050448A); a 2-byte `sounds` call is an 18th
  `-txt`-only call.

No class moves (the d-none halves are remainders of rows raised in part). Totals against `main` after merging it into
the lane (`2637b08`; the `lane/h1b` review's are the latest above): **static 567, harness 523, c-emu awaiting a batch
0, blocked 417** (d-none 291, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**

**`lane/h3b` review (2026-10-27, architect): accept with fixes (9).** One ledger change. **data/strings 29 and
data/excel 50 move from raised to raised in part.** The byte read is `[C]`: the archive's `00`, the direct run's
`00 00 00 00` and the shipped `Use_rus` byte `0B` (which the install's Russian launcher script copies over `Use`) →
0, 0 and 11. The clamp of values above 13 stays `[I]`, d-edit as a half. No shipped file holds such a byte, so only
the made-up `0E` reaches it, and a claim only edited data reaches stays `[I]` (ADR-0010, ADR-0013). The clamp run is
kept as seen, not counted. **H3b's ledger: raised 16** (data/README 2, 3, 4; data/excel 1–7, 17, 18, 20, 24, 25, 27),
**raised in part 9** (data/README 5; data/excel 8, 50, 71, 74; data/strings 2, 6, 22, 29), **shortfall 0: 25.** The S1b
remainders stand as filed. data/README 1 is raised, and data/excel 30 is raised in part with its correction. S1b row 42
G1's post-pass half loses its d-none label. H3b logs its 45 chest-name lookups (0x0065A33B, in `TC_BuildChestTable`),
and they match. It stays `[I]` for the store into `g_ChestTCs`, with no count change. No class moves. Recounted against `main` after merging it
into the lane (`550d2dcc`). The filed totals predate the `lane/r1h` review's moves (harness −2, d-none +2), so they are
corrected here: **static 567, harness 521, c-emu awaiting a batch 0, blocked 419** (d-none 293, d-edit 73, d-sim 28,
d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.** The 25 H3b rows are all (b) and batch H3b in the
cluster tables (data-excel 17, data-README 4, data-strings 4).

**H1a (filed 2026-10-27, reverser, `lane/h1a`): 46 statements of save/d2s, hirelings, player/creation and
items-uniques-sets.** run:2026-10-27-sweep-d2s-load, 5 kept sessions on slot 2 (expansion, Normal, Nightmare
and Hell, single player), tool-built saves from `tools/h1a_saves.py` swapped in after the character screen read its
list, logger `tools/gdb/d2s-h1a.gdb`; plus the S1b session (CalcSor, `tools/gdb/s1b-pieces.gdb`; data-calc 19 and
rng-seeds 11 stay counted as S1b). `sweep_h1a.py check` on the kept logs: **410 comparisons over 38 cases, 0 failing**, every log's `d2sio.py` part 0 mismatches (`check/sweep-h1a-check.txt`,
manifest `h1a-manifest.sha256`). The evidence is in the "Plan 0038 batch H1a" sections of
[save/0001](../../findings/save/0001-d2s-io.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load),
[hirelings/0001](../../findings/hirelings/0001-hirelings.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load) and
[player/0001](../../findings/player/0001-creation.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load). The batch is
45 statements filed (save-d2s 35 in 34 rows, hirelings 4, player-creation 6) and items-uniques-sets 21 from H6d.

- **Raised (32):** save-d2s 9, 22, 26, 27, 28, 29, 30, 36, 38, 44 (2), 46, 47, 49, 52, 53, 54, 59, 62, 65, 68, 80, 90,
  91, 105, 106, 107, 132; hirelings 32; player-creation 8, 9, 11.
- **Raised in part (4):** save-d2s 23 (91 → legacy, 94 and 96 accepted, 97 → 7; 92, 93, 95 not loaded), 50 (every
  status code met; the ladder test and the classic progression bounds not), 139 (the item param half; the `gf` half
  has no stock case), 140 (the reader half; no write above 8 KiB).
- **Shortfall (8):** save-d2s 10, 17 (no write above 8 KiB), 126 (no version-92 item list in the 1.09 widths);
  hirelings 3, 30, 33, player-creation 1, items-uniques-sets 21 (no save in the version 71 or 87 layout: no builder,
  no format doc; archivist entry).
- **Proposed d-none (2):** player-creation 20 and 34. A class-7 player is never made: a class-7 full save and a
  class-7 stub both pass the header, then halt the game at the null-unit test (line 1210) when the player unit is made,
  so no code reads a class-7 CharStats row or experience column.
- **Halves proposed d-none (the rows stay counted as H1a, raised in part):** save-d2s 139's `gf` half (no
  `ItemStatCost` row with `CSvBits` has a `CSvParam`), save-d2s 50's ladder test (it runs only with the host callback
  set, `0x00883D54`, which the r1h ruling holds is never set on this image).

| Row | Was | Now (accepted at review) | Why |
|---|---|---|---|
| player-creation 20 (class outside 0..6 reads column 0) | b, H1a | **d-none** | No class-7 player unit is made: both loads halt at `sub_00553180`'s null-unit test (1210), per the two crash reports. The statement stays `[I]` as a reading of `EXP_GetThreshold`. |
| player-creation 34 (class 7 gets nothing; class 0 experience column) | b, H1a | **d-none** | As row 20. |

Net effect on the totals (proposed): harness −2, d-none +2. Taken against `main` after merging it into the lane
(`ee8273b7`; no inventory change on `main` since the `lane/r1h` review totals above): **static 567, harness 519, c-emu
awaiting a batch 0, blocked 421** (d-none 295, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2,
raised 17: 1 526.** H1a's ledger: raised 32, raised in part 4, shortfall 8, d-none 2: 46.

**`lane/h1a` review (2026-10-27, architect): accept with fixes (5).** The ledger stands as filed: **raised 32, raised in
part 4, shortfall 8, d-none 2: 46**, and the two moves (player-creation 20 and 34, b → d-none) are accepted with a
reach condition (a null-unit call at any `EXP_GetThreshold` caller, whose inlined test passes −1, moves row 20 back to
(b)). The swap is ruled a stock-path observation of the server's reader (ADR-0013 § Neutral: no table, memory or code
edit; it bypasses the client's list filter only), so each raise carries a reach note in single player. The two d-none
halves (save-d2s 139's `gf` half, 50's ladder half) are accepted; the legacy rows stay shortfalls (a 1.07/1.08-era save
is a real input, not edited data). S1b leftovers (counted as S1b): data-calc 19 **in part → raised** (the hovered
potions return on `+0xB4` = 0 before the evaluation sites); rng-seeds 11 stays in part (four callers unhit, H5c route).
No class moves beyond the lane's. Recounted against `main` `6ad383c4` after merging it into the lane (`lane/h3b`,
`lane/a3f` and `lane/rbd` merged since the lane's base; none moved a row after the r1h totals): **static 567, harness
519, c-emu awaiting a batch 0, blocked 421** (d-none 295, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8),
**deferred 2, raised 17: 1 526.** § 5 marks H1a done, and H1b, H3b, H4a, H5c, H5d and H7a, accepted earlier, too.
**Phase 3 ready:** save/d2s (S1a, S1e, H1b, H1a) and items/uniques-sets (S2b, S2c, S1f, H2b, H6d, H1a). Not ready:
hirelings (H6f, 22 rows) and player/creation (H6g, 15 rows).

**H6e2 (filed 2026-10-27, reverser, `lane/h6e2`; accepted with fixes at the `lane/h6e2` review, 2026-10-27): 24 statements of items/quest-drops (rows 1, 30, 33, 34, 35) and
objects (row 48).** run:2026-10-27-sweep-quest-items, 11 kept sessions on slot 1 (19 launches, 8 development logs;
Normal, one Nightmare; tool-built quest saves, the Act II and III ones starting in the Act IV town), logger
`tools/gdb/quest-items.gdb`, checker `tools/sweep_h6e2.py check` over the 11 kept logs: **chest 6, object 2, event7 19,
dup 8, gate 8; 0 mismatches** (`check-final.txt`, manifests `manifest-final.sha256` and `manifest-ckpt1.sha256`). The
evidence is in [items/0010 § Plan 0038 batch H6e2](../../findings/items/0010-quest-drops.md#plan-0038-batch-h6e2-run2026-10-27-sweep-quest-items),
whose ledger table gives each statement's `[C]` part and remainder.

- **Raised (3):** quest-drops 30 `box` (made without a cube, refused with one); 30 Wirt's gold (already `[C]` in the
  spec from run:2026-10-19-economy2; met again, 18 piles by event 7); objects 48 Wirt's body row.
- **Raised in part (14):** quest-drops 1 (classes 268 and 367; the other event-7 classes), 30 `leg`, `bks`, `ass`,
  `tr1`, `msf`, `qhr`/`qey`/`qbr` (`qhr` only; all three after the follow-up below), `j34` (the creations; the refusal halves), 33 (E1 for `box`, `tr1`,
  `msf`; **corrected** for the Khalim chests, gold first, met on `qhr`; `vip`, `qey`, `qbr` stay), 34 (a held cube
  refuses in Normal; a Normal staff does not count in Nightmare; the cursor branch and "only" stay), 35 (8 gate
  cases, as at checkpoint 1); objects 48 chests row (as 33, with the correction), item-objects row (`leg`, `bks`),
  orifice row (the bits, from the kept log `quests-s3-3364-duriel-normal.log`; the `hst` gate stays).
- **Shortfall (7):** quest-drops 30 `bkd`, `hdm`, `vip`, `bbb`, `g33`, `g34`/`xyz`, `qf1`: not run (launch cap), or
  the route failed (the tome's warp led to the Disused Fane). *(Follow-up below: `bbb` raised in part, shortfall 6.)*
- Eleven symbols I → C (rule 14): `QUESTS_ObjectEvent`, `A1Q4_WirtGold`, `WirtLegDrop`, `A1Q4_InifussDrop`, the
  scroll, staff, cube and heart chests, `DropItemCodeAt`, `PlayerFindItemByCode`, `ItemQuestGate`.

No class move is proposed. Net effect on the totals: none. Taken against `main` after merging it into the lane
(`147e5ca3`; no inventory row moved on `main` since the `lane/h1a` review totals above): **static 567, harness 519,
c-emu awaiting a batch 0, blocked 421** (d-none 295, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred
2, raised 17: 1 526.** H6e2's ledger: raised 3, raised in part 14, shortfall 7: 24.

*Review (2026-10-27):* the ledger stands. Wirt's gold stays counted **raised** under H6e2 with no class move (the
`lane/p49r` precedent for quest-drops 10 and 19): plan 0043 raised it first (run:2026-10-19-economy2, map seed 4506),
this run met it again on an independent seed (3811); Phase 3 adds the run anchor only. Recounted against `main`
`507a6f5c` after merging it (`lane/rk` moved no inventory row): totals as above. **Phase 3 ready:** objects (S4a,
S4b, H5b, H6e2; its 13 "—" rows have no batch). Not ready: items/quest-drops (H6e1 open).
*Follow-up (2026-10-27, reverser, `lane/h6e2f`; the `lane/rdp` review's ruling 7):* the reruns `eye4c`, `tome4c`
and `brain4c` under run:2026-10-27-sweep-quest-items (addendum *Follow-up*), 3 launches and 3 kept sessions on slot 1
with `d2pilot.py --descend-to` and `--all-copies`, the RL line's new `f28` key; checker over the 14 kept logs: **chest
8, object 3, event7 19, dup 8, gate 8, gold 57, death 6 (listed); 0 mismatches** (`check-followup.txt`, manifest
`manifest-followup.sha256`, 18 lines). Ledger moves inside H6e2, no class move:
- quest-drops 30 `bbb`: **shortfall → raised in part** (`tome4c`: the creation with word 17 clear; the refusal stays);
- quest-drops 30 `qhr`/`qey`/`qbr`, 30 `j34`, 33 and objects 48 chests and item-objects rows stay **raised in part**,
  with more met: `qey` and `qbr` in the corrected Khalim order (gold first; `k` 5 and 7 on their logged seeds, the
  heart chest's 8), so E1's correction holds for all three Khalim chests and only `vip` and the held-part refusal
  stay; `bbb` joins `leg` and `bks`; three more `j34` kills;
- the brain chest's open question: with its room active in both copies the chest is listed and opens (`[C]`; scoped
  at the review, `brain4`'s activation in the other copy alone listed nothing); which copy the listing follows stays
  `[I]` (an order match over three logs; `brain4c` had the room active in both copies).

Symbols `sub_005B7A60_A3Q1_TomeDrop`, `sub_005B8940_A3Q2_EyeChest`, `sub_005B8A20_A3Q2_BrainChest` I → C (rule 14:
each one's logged calls compared with the checker's model). H6e2's ledger: **raised 3, raised in part 15, shortfall
6: 24.** Net effect on the totals: none. Taken against `main` `1573a48f` (the lane's base; no inventory row moved on
`main` since the `lane/s38s` review's totals): **static 567, harness 519, c-emu awaiting a batch 0, blocked 421**
(d-none 295, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.** Review-fixes pass
(reverser 1–15): the new `[C]` bullets each carry a `run:` anchor and an address; the copy identification stays `[I]`
(1, 4); every count copied from the kept outputs (2); totals against `main` (3); logs, outputs and the 8 screenshots in
one manifest, the `--warps` replay kept as a tool mode (6); the remainders named in the ledger rows (8); three
separating seeds for `k` (10); the correction carried into § Static reads' Khalim bullet, the eye/brain `[I]`
sub-bullet, the open questions and the `h6e2_sessions.py` comment (12); `bbb`'s quality 7 as After `[I]` (13); the
three symbols raised in `re/symbols.csv` and the Functions table (14).
**`lane/h6e2f` review (2026-10-27, architect): accept with fixes (2).** The ledger moves stand: `bbb` shortfall →
raised in part, H6e2 **raised 3, raised in part 15, shortfall 6: 24**, no class move, three symbols I → C. The brain
chest's `[C]` is scoped to "with its room active in both copies" (in `brain4` the room activated in the other copy
alone and the chest was not listed); the copy order lines are now in a kept output (`copies-review.txt`). Recounted
against `main` `dcf6c210` after merging it into the lane (`lane/rlg` and `lane/h6e1` merged since the lane's base;
neither moved a class): **static 567, harness 519, c-emu awaiting a batch 0, blocked 421** (d-none 295, d-edit 73,
d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**
**`lane/s38s` review (2026-10-27, architect, Phase 3 of save/d2s and items/uniques-sets): three S1a rows completed by
H1b's kept check.** The H1b ledger listed the S1a pieces it met and left the rows as S1a. Two of those pieces carry a
compared line in the kept check output (`workspace/logs/r1h/sweep-h1b-check-r1h.txt`, 0 failing), so they move here,
with no class change:

| Row | Was | Now | Why |
|---|---|---|---|
| save-d2s 24 (`weapon_set` bit 0 from client `+0x45C`) | S1a, raised in part (value 0) | **S1a, raised** | rt-r2's four writes after `w`: bit 0 = 1, equal to the logged `+0x45C` (`tools/d2sio.py`'s `weapon_set bit 0` check). |
| save-d2s 123 (groups 52 and 57 framed like the others) | S1a, raised in part (57) | **S1a, raised** | `9cr` 52/53 = 50/120 read three times with stats 52 and 53 equal to the file's group values (`group 52 stats 52/53 = file`), the second rt-r2 read on the file the game wrote. One item. |
| save-d2s 138 (groups 52 and 57 read the same way) | S1a, raised in part | **S1a, raised** | As row 123. |
| save-d2s 130 (unseen ids, groups, clamp bounds, stat 326, version < 93) | S1a, raised in part | S1a, raised in part | The group-52 remainder is met; the clamp bounds (d-none), stat 326 (d-none here; its own row 125 raised by H1b) and version < 93 (d-edit) are as before. |

Rows 20 (the pet-type-7 test) and 32 (the read side's `& 0xFFF` mask) stay as filed: no compared line covers them (the
H1b hotkey check compares the written words only). S1a's ledger is now **raised 42, raised in part 12, returned 2**
(56). Totals unchanged: **static 567, harness 519, c-emu awaiting a batch 0, blocked 421** (d-none 295, d-edit 73, d-sim
28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**

*Rows 20 and 34 of player/creation (ruling).* The class-7 halt and the two d-none rows are different statements. The
halt (a class-7 file passes the class test and the game stops at the null-unit test, 1210) is player-creation row 11,
raised by H1a on the logged `RCST`/`RMAP` lines and the two crash reports, so a spec states it `[C]`. Rows 20 and 34
(what a class-7 player's experience lookup and starting kit would be) need a class-7 player, which the halt shows
never exists; they are d-none and stay `[I]` readings. The halt is the reason for the d-none, not a contradiction of it.

**H6e1 (filed 2026-10-27, reverser, `lane/h6e1`; accepted with fixes at the `lane/h6e1` review, 2026-10-27): 22 statements of items/quest-drops (rows 2, 4, 5, 32, 39, 40,
42–46, 50, 51) and the S2c piece of row 38.** run:2026-10-27-sweep-quest-npc, 14 kept sessions on slot 1 (17
launches, 3 development logs; Normal, Nightmare and Hell, all in town; tool-built saves in the Act V and Act I towns,
one three-game chain on the saves the game wrote), logger `tools/gdb/quest-npc.gdb`, checker `tools/sweep_h6e1.py check`
over the 14 kept logs: **69 service-test calls, 9 sockets, 2 imbues, 18 consumed cursor items, 18 tails, 20 given
items, 3 Anya draws; 0 mismatches** (`check-final.txt`, manifests `manifest-final.sha256`, `manifest-shots-final.sha256`,
`manifest-dev-final.sha256`). The evidence is in [items/0010 § Plan 0038 batch H6e1](../../findings/items/0010-quest-drops.md#plan-0038-batch-h6e1-run2026-10-27-sweep-quest-npc),
whose ledger table gives each statement's `[C]` part and remainder.

- **Raised (11):** quest-drops 2 (L36, L299), 4 (L78, L680, L684), 5 (L79, L682), 39, 45 (L678, L679), 51.
- **Raised in part (11):** quest-drops 2 (L278: the durability write and the drop when full), 5 (L690: the clvl
  halves, game type 3 only), 32 and 46 (`tr2`, created at quality 7; `ice` not given), 40 (refinement: the throwable
  test skipped for every item; gold, `0x1000`, quality 9), 42 (L621, L639: quality 9; `0x1000`, type 4, "0 sockets
  now"), 43 (type 4, ears, `0x1000`), 44 (refinement: an imbued item repaired when created identified; charges, the
  broken flag, the attach), 45 (L686: the Ancients and Nihlathak), 50 (the scripted half).
- **Shortfall (0).** The qd 38 piece is met (18 consumed items, each the player's cursor item); qd 38 stays counted
  as S2c (raised in part there); its remainder, the cursor line, is met here.
- Corrections carried into items/0010 § 6: `tr2` and `g34` are created at quality 7 (base `unique`), the asked 2 in
  the table; the throwable and the imbue-repair notes.
- Symbols I → C (rule 14): `QUESTS_GiveItem`, the five NPC message handlers, the three service tests,
  `CursorItemConsume`, `ItemRepairAll`, `ItemIdentifyAttach`, `ITEMS_GetType`, `ITEMS_GetCode`, `ITEMS_GetQuality`;
  new rows `sub_0062A270_ItemHoldsItem` and `sub_0062A2B0_ItemCompactSave` (C), `sub_00578610_PlayerCursorItemIs` (I).

No class move is proposed. Net effect on the totals: none. Taken against `main` after merging it into the lane
(`44cfbcb5`; no inventory row moved on `main` since the `lane/h6e2` review totals above): **static 567, harness 519,
c-emu awaiting a batch 0, blocked 421** (d-none 295, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred
2, raised 17: 1 526.** H6e1's ledger: raised 11, raised in part 11, shortfall 0: 22.

**`lane/h6e1` review (2026-10-27, architect): accept with fixes. The ledger stands, and one S2c row is completed.**
H6e1's 22 rows stay as filed: raised 11, raised in part 11, shortfall 0. The 11 rows raised in part each have a
`[C]` half the kept check compares, and a remainder no stock single-player game reaches, or that this run did not
reach. Malah's `ice` (qd 32, 46) needs quest state 4, and the clvl halves of qd 5 L690 need a game type other than 3.
qd 45 L686 needs the Ancients and Nihlathak. Those halves stay `[I]` in Phase 3. The piece H6e1 met for S2c has a
compared line (`CIC`/`CICR`, 18 calls), so the row moves here, with no class change:

| Row | Was | Now | Why |
|---|---|---|---|
| quest-drops 38 (`NPC_MenuAction` consumes the cursor item) | S2c, raised in part | **S2c, raised** | Its remainder (the consumed item is the cursor item) is met: in all 18 `CursorItemConsume` calls (imbue 2, socket 9, personalize 7) the item is `[[player+0x60]+0x20]`, and each call returns 1. |

S2c's quest-drops tally (16) is now raised 13 (with `lane/p49r`'s qd 10 and 19), raised in part 2 (qd 8 and 21),
reclassified 1. Symbols: the review raises `ITEMS_CheckFlags` and `sub_00628110_ItemGetFlags` as well, on the same `CAN`
steps (rule 14). That makes **17 I → C** (the lane's list has 15, its request said 14) and 3 new rows. No class
moves. Recounted against `main` `92b811df` after merging it into the lane (`lane/s38s`, `lane/rdp`, `lane/s38o`,
`lane/a71`, `lane/rsw` and `lane/rlg` merged since the lane's base; only `lane/s38s` moved rows, with no class change): **static
567, harness 519, c-emu awaiting a batch 0, blocked 421** (d-none 295, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032
8), **deferred 2, raised 17: 1 526.** § 5 marks H6e1 done. **Phase 3 ready:** items/quest-drops (S2c, H6d, H6e2 and
H6e1, all accepted).

**`lane/s38q` review (2026-10-27, architect, Phase 3 of items/quest-drops): one H6e2 line completed by H6e1's compared
calls.** H6e2 counted qd 30's `g34`/`xyz` line a shortfall (not run by H6e2). H6e1's checker compares both gifts
(`QGV` → `CF0` → `QGC`, 0 mismatches): Meshif's `g34` with `j34` held (Nightmare, created at quality 7) and Alkor's
`xyz` with word 20 bit 1 set (Normal), each at clvl. A met piece with a compared line moves at the review that finds it
(the `lane/s38s` and `lane/h6e1` precedents), with no class change:

| Row | Was | Now | Why |
|---|---|---|---|
| items-quest-drops 30, the `g34`/`xyz` line | H6e2, shortfall | **H6e2, raised in part** | The two gifts in the logged word-20 states, compared by H6e1's check; the other word-20 states stay `[I]`. |

H6e2's ledger is now **raised 3, raised in part 16, shortfall 5: 24.** The operate-slot sentence of § Entry points
(slots 33, 12, 28, 39–41, 57–59 `[C]`) is part of row 1's original statement (`QUESTS_ObjectOperate` dispatches by
class); its slots are on H6e2's compared `QOW` lines, so it is reflected with row 1 (raised in part, the other classes
stay) and moves nothing. Totals unchanged: **static 567, harness 519, c-emu awaiting a batch 0, blocked 421** (d-none
295, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**
**H6b (filed 2026-10-27, reverser, `lane/h6b`; accepted with fixes at the `lane/h6b` review, 2026-10-27): 25 statements of items/sockets-runewords (rows 1, 9, 10, 12, 13, 16–18,
21, 29, 35 ×2 from S2c, 38) and the S2c pieces of rows 14 and 46.** run:2026-10-27-sweep-sockets, 5 kept sessions on
slot 1 (10 launches, 5 development logs; expansion, Normal, in town; the game-written *Steel* sample and four
tool-built saves), logger `tools/gdb/h6b.gdb`, checks over the 5 kept logs: `tools/sockets.py check` **35 inserts and
37 client verdicts reproduced, 0 failed** (`check-sockets.txt`), `tools/sweep_h6b.py logs` **773 counted checks, 0 bad**
(`check-sweep_h6b.txt`); the regression of run:2026-10-15-sockets still 351 and 357, 0 failed. The evidence is in
[items/0007 § Plan 0038 batch H6b](../../findings/items/0007-sockets-runewords.md#plan-0038-batch-h6b-run2026-10-27-sweep-sockets),
whose ledger gives each statement's `[C]` part and remainder.

- **Raised (9):** sockets 10 (L170, L171; built states), 12 (L173; built state), 16 (L236, L274), 21 (L262), 35
  (L438, L470), 38 (L490).
- **Raised in part (9):** sockets 1 (L51, L283, L288: the copier; the golem reader and the other reader sites not
  run), 13 (L181: `hasinv`, `ItemMaxSockets`, `0x100` now seen failing), 17 (L291: `p4`, `p6`, `p7`), 18 (L243, L450:
  the 252 timer; no stock runeword parent carries 253), 38 (L481: *Leaf*'s `par`-0 branch at min = max; L505).
- **Shortfall (7):** sockets 1 L284 (0x00563441's callers: a trade, `0x00568770`), 9 (UI states 10 and 11: the
  player-trade window, `[I]`), 12 L174 (no target without a client inventory reached the test), 17 L237 (the cursor slot is already
  empty at the `p5` test, a correction), 29 (the enable-bit branch never taken; no socket filler has durability), 38
  L482 (func 24: only *Faith*, a `server` row) and L507 (func 7's `+1` fallback: no observable). Fewer than half are
  raised; the finding's ledger says why.
- **Pieces met:** sockets 14 (the unidentified socketed parent's client flags `0x00800000` before and `0x00800811` after
  a Scroll of Identify; refused, then inserted) and 46 (the reader's store at `+0x38`, `0x509F`, and the client copies'
  Name indexes). Both rows stay counted as S2c, raised in part there.
- **Proposed for the review** (not filed as moves): sockets 9 → d-2c; sockets 18's 253 half, 29, 38 L481's ranged
  half, L482 and L507 → d-none.
- Symbols I → C (rule 14): `sub_00558530_ItemReplenishDurTimer`, `sub_00629900_ItemBaseHasInv`.

No class move is filed. Net effect on the totals: none. Taken against `main` after merging it into the lane
(`fd841611`; `lane/a72` and `lane/h6e2f` merged since the lane's base, neither moved a class): **static 567, harness
519, c-emu awaiting a batch 0, blocked 421** (d-none 295, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8),
**deferred 2, raised 17: 1 526.** H6b's ledger: raised 9, raised in part 9, shortfall 7: 25.

**`lane/h6b` review (2026-10-27, architect): accept with fixes (6).** The raises stand. Four shortfalls move, and one
S2c row is completed. sock 10's two raises rest on a tool-built save on stock tables (ADR-0013 § Neutral, not a
forced-path run). They back the client test's order and its refusal at `hasinv` and at `ItemMaxSockets` on a target
with bit 11, and nothing about how an item gets bit 11. No stock item reaches either refusal, and Phase 3 says so.
The two half-moves (sock 18's 253 half, sock 38 L481's ranged half) are labelled d-none for Phase 3. Their statements
stay counted here, raised in part, as the H2b review did with tc 58's half.

| Row | Was | Now | Why |
|---|---|---|---|
| items-sockets-runewords 9 (the client refuses UI states 10 and 11; 1) | b, H6b | **d-2c** | The only stores of 10 and 11 are the immediates in `0x00489360`, whose four callers test UI panel 23 and send packet `0x4F` (the player-trade window, `[I]`). Of the seven register stores, five store constants (0, 6, 1, 0, 1) and two copy the slot table at 0x007BC9E4 (unfollowed). The word was 0 or 14 at all 45 + 357 logged tests. |
| items-sockets-runewords 29 (the owner branch and the `0x100` child on the socket path; 1) | b, H6b | **d-none** | In all 35 inserts the child's list had owner 0 and the link branch ran. To be owned by the parent, a child must already be linked to it, and no stock path takes a child back out. No socket filler has durability (69 rows), so none can carry `0x100`. Scoped to the socket path: the function's other 44 call sites are outside this spec. |
| items-sockets-runewords 38 L482 (func 24; 1) | b, H6b | **d-none** | Its one stock row, *Faith*, has `server` 1, and single player is never ladder (the same reason as row 23). |
| items-sockets-runewords 38 L507 (func 7's `+1` fallback; 1) | b, H6b | **d-none** | The fallback sits on the weapon branch, and the handlers' item is the rune, which is never a weapon: no observable. |
| items-sockets-runewords 46 (the runeword field; S2c) | S2c, raised in part | **S2c, raised** | Both remainder parts are compared in the kept check: the reader's store `0x509F` (0x0062D1EA) and the Name index in six client copies. |

sock 14 (S2c) stays raised in part: its piece is met, and its remainder is narrower. Fixes, each written into the
document it changes:
(1) *misread:* `RUNEWORD_Apply`'s already-applied test does not read `0x40`. `sub_00625790_UnitFindStatList` searches
by state alone when the state is non-zero (0x006257AC → 0x00625650). The model now tests the state alone
(`tools/sockets.py` `af5c8279`, both outputs byte-identical), and spec L438's "flags 0x40" is a correction for Phase 3.
(2) *stale cross-reference:* "ADR-0010 § built states" becomes ADR-0013 § Neutral (items/0007 sock 10, the run record).
(3) *miscount:* sock 9 has seven register stores of the UI word, not six, and five of them resolve.
(4) *omission:* two 253-timer schedules outside an insert (`v` 10 and 5) were not stated and are not compared by the
checker, so `sub_00558580_ItemReplenishQtyTimer` stays I. The truncation in 2500 / `v` is the `idiv` (read): every
logged schedule divides exactly.
(5) *omission:* sock 1's version-71 sites have a builder route since `lane/a72`. The piece is routed to H1c (§ 5).
(6) *overclaim:* sock 17 L237's reason (`0x0063AAF0` empties the slot) is a reading, `[I]`. The `[C]` is the empty slot
at the test in the 29 inserts with `p5` 1.

Net effect on the totals: harness −4 (519 → 515), d-2c +1 (7 → 8), d-none +3 (295 → 298), blocked 421 → 425. H6b's
ledger: **raised 9, raised in part 9, shortfall 3, reclassified 4: 25.** Recounted once, against `main` `fd841611`
merged into the lane (no inventory row moved on `main` since the `lane/h6e1` review totals): **static 567, harness 515,
c-emu awaiting a batch 0, blocked 425** (d-none 298, d-edit 73, d-sim 28, d-2c 8, d-owner 10, d-0032 8), **deferred
2, raised 17: 1 526.** § 5 marks H6b done. **Phase 3 ready:** items/sockets-runewords (S2c, H2b and H6b, all
accepted).

**H6a (filed 2026-10-27, reverser, `lane/h6a`): 29 statements of items/cube (rows 1, 7, 15–17, 25, 32, 36, 38–40,
43, 44, 51, 53, 54, 58) and the S2c pieces of cube 49 and aff 14.** run:2026-10-27-sweep-cube, 8 sessions on slot 1,
all kept (one game each; expansion and classic, Normal, in town; tool-built saves, one with the Act IV act byte, one
at clvl 1 in its own game directory for the expected fault), logger `tools/gdb/cube.gdb` with `tools/gdb/cube.py` r4,
checker `tools/sweep_h6a.py check` over the 8 logs: **26 transmutes reproduced by `tools/cube.py`, 27 call chains,
23 `UnitSetEvent` calls, 0 mismatches** (`check-final.txt`, manifests `manifest-final.sha256`, `manifest-shots.sha256`,
`manifest-dev.sha256`). The evidence is in [items/0008 § Plan 0038 batch H6a](../../findings/items/0008-cube.md#plan-0038-batch-h6a-run2026-10-27-sweep-cube).

- **Raised (22):** cube 1 L48; 7 (3); 15; 25 L331; 36; 38 (2); 39 (3); 40 (3); 43 (3); 53 (2); 54; 58.
- **Raised in part (4):** cube 1 L54 (button `0x17` and a type other than 4 not sent), 17 (no stock `eli` input), 25
  L349 (the version gate's classic half: rows 129–136 are all version 100, d-none part), 32 (no stock `rem` row).
- **Shortfall (1):** cube 51, three row-19 transmutes, the skipped record `start − 1` a candidate in none (10 in 659 per
  transmute).
- **Pieces:** cube 49 (stays counted as S2c, raised in part): case (b) met, the fault at 0x005C2460 logged and in the
  game's crash report; case (a) d-none (no crafted base, ilvl and side whose first pick lacks a candidate, 0 of 40 194).
  aff 14 (stays S2c, raised in part): the level-window half met (cube 58); "only" has no separating stock case.
- Refinements carried into items/0008: an `ItemCopy` draws two more game-seed steps per child it copies; the runeword
  copy's prefix slot 0 holds the name id; `InvPlaceItem` sets flags bit 0 on an item holding items; `ItemInitStats` on
  an ethereal copy writes the plain base values (the open question answered).
- Symbols I → C (rule 14): `g_SrvPacketTable`, `SrvPacketDispatch`, `Pkt4FButton`, `PktInteractButton`,
  `PlayerGetInteract`, `CubeButton`, `ItemRemoveRuneword`, `ItemRepairBroken`, `QuestStaffMade`,
  `QuestKhalimWillMade` (10); new `sub_0055F590_ItemInvNonEmpty` (I).

Proposed class moves (two rows):

| Row | Was | Now | Why |
|---|---|---|---|
| items-cube 16 (`eth` input) | b, H6a | **d-none** | 0 of the 389 compiled stock inputs has `eth` (`tables.txt`); `noe`, the same `ITEMS_IsEthereal` test, refused an ethereal sword at row 137. |
| items-cube 44 (the `rem` children placed) | b, H6a | **d-none** | No stock output has `rem` (only row 141 has `uns`), so the second placement loop counts 0 in every stock transmute. |

Net effect on the totals: harness −2, d-none +2. Taken against `main` `fd841611` (the lane's base; no inventory row
moved on `main` since the `lane/h6e1` review totals above): **static 567, harness 517, c-emu awaiting a batch 0,
blocked 423** (d-none 297, d-edit 73, d-sim 28, d-2c 7, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**
H6a's ledger: raised 22, raised in part 4, reclassified 2, shortfall 1: 29.

**`lane/h6a` review (2026-10-27, architect): accept with fixes (7).** Both moves stand, checked from the tables with
`python3 -I` at review: 0 of the 389 stock inputs carry `eth` (4 carry `noe`), no stock output carries `rem` (`uns` row
141 only), and 0 of the 40 194 crafted (row, base, output ilvl, side) cases has a side without a candidate (203 row-base
pairs × 99 × 2; recounted with a looser filter, every level 1–99 against `level`/`maxlevel`, which can only add empty
sides). Four raises have a half the run does not separate, and move to raised in part:

| Row | Filed | Now | The half not separated |
|---|---|---|---|
| items-cube 39 L491 (`rep`) | raised | **raised in part** | evaluated against base stat 73 (both 24, no durability modifier on the swords; `STATS_GetUnitStat(it, 73)` read at 0x005662F1), and the 255 side of the stackable `min` |
| items-cube 39 L524 (repair and refill) | raised | **raised in part** | "every stat-204 count": one charge entry; stock items with 2–4 exist (*Spellsteel*, *Wisp*) |
| items-cube 40 L528 (`min(255, max stack)`) | raised | **raised in part** | the 255 side: max stack 160 < 255; a 200-stack throwing weapon with *Dense* reaches it on stock data |
| items-cube 58 L968 (a forced row skips only the window) | raised | **raised in part** | "only", as aff 14: d-none part, the 8 stock forced ids pass every other C4 test |

No class move beyond the lane's two. H6a's ledger: **raised 18, raised in part 8, reclassified 2, shortfall 1: 29.**
Net effect on the totals: harness −2 (515 → 513), d-none +2 (298 → 300), blocked 425 → 427. Recounted once, against
`main` `ad8b8cd0` merged into the lane (`lane/h6b`'s four moves and `lane/s38q`, which moved none): **static 567,
harness 513, c-emu awaiting a batch 0, blocked 427** (d-none 300, d-edit 73, d-sim 28, d-2c 8, d-owner 10, d-0032 8),
**deferred 2, raised 17: 1 526.** § 5 marks H6a done. **Phase 3 ready:** items/cube (S2c and H6a, both accepted).

**H6c (filed 2026-10-27, reverser, `lane/h6c`): 13 statements of items/vendors (rows 2, 5 ×2, 12, 14, 15, 18, 29, 30,
32, 33, 34, 36) and the S2c pieces of vendors 22 and 26.** run:2026-10-27-sweep-vendors, 6 kept sessions on slot 1 (8
launches, 2 development logs; expansion; Normal, Nightmare and Hell; tool-built saves at clvl 1, 19, 30 and 99),
logger `tools/gdb/h6c.gdb` (`vendors.gdb`'s files and the new `h6c.py`), checks over the 6 kept logs:
`tools/vendors.py check` **17 stock builds, 40 gamble windows, 1 646 creations through the item chain, 0 mismatches**
(`check-vendors.txt`), `tools/sweep_h6c.py logs` **9 616 counted checks, 0 bad** (`check-sweep_h6c.txt`); the
regression of run:2026-10-15-vendors still 0 mismatches; rescans of run:2026-10-20-two-clients (`check-pairs.txt`) and
run:2026-10-15-vendors (`check-hb.txt`, `check-fails-vendors-run.txt`). The evidence is in
[items/0009 § Plan 0038 batch H6c](../../findings/items/0009-vendors.md#plan-0038-batch-h6c-run2026-10-27-sweep-vendors),
whose ledger gives each statement's `[C]` part and remainder.

- **Raised (7):** vendors 2 (L66, with a refinement: the path runs at a player unit's free, and is reached only when a
  client leaves with an interaction open: 2 of run:2026-10-20-two-clients's leaves), 12 (L256), 14 (L261, with a
  correction: the interaction start builds Asheara's hirelings before any menu action, so the trade-first order is
  never taken), 15 (L272), 30 (L607), 33 (L647), 36 (L762).
- **Raised in part (2):** vendors 18 (L284: a town entry, a reopen and a level-up; no quest event), 34 (L650: the
  purchases, and sales copied or refused by the permanent test, its clause outside Normal and the gamble view; the
  refusals by `Cracked`, base type 7, flag `0x1000000` and `0x0055F590` not reached).
- **Shortfall (4):** vendors 5 L123 and L368 (no build passed 32 failures: at most 27, Larzuk in Hell at ilvl 104;
  the limit is tested only after a normal copy and a permanent item, a refinement), 29 (the gamble open with an
  inventory left) and 32 (the free at a player's removal at a gambler; the same items within one interaction).
- **Pieces:** vendors 22 (stays counted as S2c, raised in part): the tab of all 1 086 stock items, 901 cells, tab 2 only
  after a failed tab-1 try, met; the cell search stays `[I]` (a column-major first fit gives 841 of 901). vendors 26: the
  1 646 store creation records' `+0x18` = 4 and `+0x28` = 1, met.
- **Proposed for the review** (not filed as moves): vendors 29 and 32 → d-2c (with one player every close sends the
  cancel, and `NpcInteractRemove` frees the gamble inventory when the list empties, 0x00572FAF); vendors 26 (S2c) →
  raised.
- Symbols I → C (rule 14): `VENDOR_IsPermanent`, `sub_00576F50_StoreItemSold`, `sub_0062E880_ItemStorePage`; new
  `sub_00554120_PlayerSetInteract`, `sub_00554190_PlayerClearInteract` (I).

No class move is filed. Net effect on the totals: none. Taken against `main` after merging it into the lane
(`a105ae13`, merged at `e21e840a`; the lane named `ffa5b957`, corrected at the review; the `lane/h6a` review's two moves are the last on `main`): **static 567, harness 513, c-emu awaiting a
batch 0, blocked 427** (d-none 300, d-edit 73, d-sim 28, d-2c 8, d-owner 10, d-0032 8), **deferred 2, raised 17:
1 526.** H6c's ledger: raised 7, raised in part 2, shortfall 4: 13. If the two d-2c proposals stand: harness 511, d-2c
10, blocked 429.

**`lane/h6c` review (2026-10-27, architect): accept with fixes (6).** The six kept logs, their pilot outputs and the 11
checks pass `manifest-run.sha256` (23 lines), the 62 screenshots `manifest-shots.sha256`, the 25 development files
`dev/manifest-dev.sha256` (which does not list itself); the ten procedure commands, rerun under `systemd-run --user
--scope -p MemoryMax=4G`, give byte-identical outputs (`vendors.py check` 0 mismatches, `sweep_h6c.py logs` 9 616
checks 0 bad, the run:2026-10-15-vendors regression 0 mismatches). run:2026-10-20-two-clients's
`workspace/logs/p44h-run/manifest.sha256` passes; its host logs hold 7 `PIEND` lines (return 0x005555CB) and 2 `PLEAVE`
(return 0x00555562), Kashya's (class 150 by `MLV`) and Akara's (148 by `BS0`). Both d-2c proposals stand
(objdump: `NpcInteractRemove` skips `GambleInvFree` at 0x00572FAF while the NPC's list is not empty; `GambleEnsure`
skips the build when the list holds the player's id, 0x00578AFC–0x00578B18):

| Row | Filed | Now | Reason |
|---|---|---|---|
| items-vendors 29 (a gamble open with an inventory left) | b, H6c | **d-2c** | the branch needs the NPC's interaction list non-empty at a close; with one player every close and menu Escape sends the cancel (`NIR`, `ICLR` at each of the run's closes) |
| items-vendors 32 (the free at a player's removal at a gambler; the same items within one interaction) | b, H6c | **d-2c** | the free needs a client leaving with a gamble window open, the second half is row 29's branch |

S2c pieces: vendors 26 is raised (it stays counted as S2c); vendors 22 stays raised in part with the cell search as its
remainder. H6c's ledger: **raised 7, raised in part 2, reclassified 2, shortfall 2: 13.** Net effect on the totals:
harness −2 (513 → 511), d-2c +2 (8 → 10), blocked 427 → 429. Recounted once, against `main` `a105ae13` (merged into
the lane; no inventory row moved on `main` since the `lane/h6a` review): **static 567, harness 511, c-emu awaiting a
batch 0, blocked 429** (d-none 300, d-edit 73, d-sim 28, d-2c 10, d-owner 10, d-0032 8), **deferred 2, raised 17:
1 526.** § 5 marks H6c done. **Phase 3 ready:** items/vendors (S2c and H6c, both accepted).

**H6f (filed 2026-10-27, reverser, `lane/h6f`; reviewed 2026-10-27, accept with fixes): 23 statements of hirelings (rows 1–2, 5–6, 9–10, 14–18, 20–21, 23,
25, 27–29, 31, 35–37; row 28 counts 2).** run:2026-10-27-sweep-hirelings, 19 launches on slot 2, 15 kept and 4
development (the classic Greiz attempts), logger `tools/gdb/h6f.gdb` (`hirelings.gdb`'s four loggers plus
`tools/gdb/h6f.py`), checker `tools/sweep_h6f.py check` over the 15 kept logs: **603 comparisons, 0 failing**, and
`tools/hirelings.py check` on the same logs 0 mismatches (`check/check-final.txt`, manifests `manifest-final.sha256`,
`manifest-shots.sha256`, `dev/manifest-dev.sha256`). The evidence is in
[hirelings/0001 § Plan 0038 batch H6f](../../findings/hirelings/0001-hirelings.md#plan-0038-batch-h6f-run2026-10-27-sweep-hirelings).

- **Raised (12):** 5, 6, 10, 14, 15, 16, 20, 27 (built state: the name id past the range), 28 (2), 31, 37.
- **Raised in part (8):** 2 and 35 (the Act I gift in expansion; the Act III gift and the classic pet test not run),
  17, 18 and 21 (the stock level, the quest reads and the passes; the stock client offered no hire line with the quest
  open, so the two refusal tails were never sent: d-none parts), 23 (no classic Greiz hire), 25 (the `L ≥ 98` return
  with a gain > 0), 36 (resurrection at Kashya here and Qual-Kehk in run:2026-10-17-economy; Greiz, Asheara, Tyrael).
- **Shortfall (1):** 29, `MERC_Create` with a hire table present: every call came from the load, before any NPC
  interaction, and the act changes made none. The lane proposes d-2c (a client joining a game whose table was built);
  left as a shortfall for the review. **Review: the shortfall stands; d-2c not accepted** (the third caller,
  `sub_005394A0_PlayerPlaceInAct`, walks a list whose writer is unread; reverser entry filed).
- Refinements carried into hirelings/0001: `MERC_AddExp` adds twice the gain (its level loop's bound of 98, not the
  owner's level, is a reading); a kill by another unit gives the mercenary `·86 >> 8` of its gain; `HIRE_Hire` returns no value
  (`tools/hirelings.py` now counts a hire by `MERC_Init`, its output on run:2026-10-16-hirelings unchanged).
- Symbols I → C (rule 14): `HIRE_GiveFreeMerc`, `MERC_AddExp`, `MERC_CapExpGain`, `PETS_OnDeath`, `MERC_Resurrect`,
  `MERC_ResurrectCost`, `sub_00576D90_PayGold`, `sub_004B5C60_ClientHireListDraw`, `sub_004B1090_ClientMercInit` (9).

Class moves (two rows; accepted at the `lane/h6f` review, the reach re-read with objdump at 0x00572C10–0x00572D04,
0x005767D5–0x005767EB and 0x00578BD3–0x00578C04):

| Row | Was | Now | Why |
|---|---|---|---|
| hirelings 1 (trade at Asheara before any interaction built the table) | a-run, H6f | **d-none** | `sub_00572C10_NpcInteractStart` calls `HIRE_SendList` (0x00572CFF) on every new interaction, which builds while `+0x21` is 0, so a trade never finds the flag clear; logged: the build from 0x005767F0 and `NPC_OpenStore`'s test reading 1 (0x00578BD3) |
| hirelings 9 (`NPC_OpenStore` would also build the table) | a-run, H6f | **d-none** | the same reach: its call at 0x00578BFF runs only with `+0x21` 0 |

Net effect on the totals: harness −2 (513 → 511), d-none +2 (300 → 302), blocked 427 → 429. Taken against `main`
`a105ae13` merged into the lane (no inventory row moved on `main` since the `lane/h6a` review totals): **static 567,
harness 511, c-emu awaiting a batch 0, blocked 429** (d-none 302, d-edit 73, d-sim 28, d-2c 8, d-owner 10, d-0032 8),
**deferred 2, raised 17: 1 526.** H6f's ledger: raised 12, raised in part 8, shortfall 1, reclassified 2: 23.

**`lane/h6f` review (2026-10-27): accept with fixes (6), ledger as filed.** Rechecked: the three manifests pass
`sha256sum -c`; `sweep_h6f.py check` (603, 0 failing), `monpool.py check` and `hirelings.py check` reproduce
`check/check-final.txt`, `check/monpool.txt` and `check/regress-hire-run.txt` byte for byte under `MemoryMax=4G`; the
`main` revision of `hirelings.py`, run from a `git archive` of `main`'s `tools/`, gives on the 48 logs of
run:2026-10-16-hirelings output byte-identical to the branch's, and on the 15 H6f logs one mismatch (`qk`: the refused
hire counted, "paid 0, price 2650"), which is the change's reason. The d-none parts of rows 17, 18 and 21 are
accepted on a condition (the client's menu test to be read; reverser entry); row 27 stands raised on its built
state under ADR-0013's Neutral rule (the clamp only); rows 3, 30 and 33 stay H1c's. Recounted once against `main`
`a105ae13` (unmoved since the lane merged it; `lane/h6c` and `lane/a4t` not merged): **static 567, harness 511,
c-emu awaiting a batch 0, blocked 429** (d-none 302, d-edit 73, d-sim 28, d-2c 8, d-owner 10, d-0032 8), **deferred 2,
raised 17: 1 526.** § 5 marks H6f done. **Phase 3 ready:** hirelings (S3a, S3b, H4b, H1b, H1a, H6f accepted), rows 3,
30 and 33 left `[I]` for H1c's re-tag.

**Merge recount (2026-10-27, `lane/h6f` merged after `lane/h6c`).** The two reviews each counted against `main` `a105ae13`; their moves are disjoint (H6c: harness −2, d-2c +2; H6f: harness −2, d-none +2). Combined: **static 567, harness 509, c-emu awaiting a batch 0, blocked 431** (d-none 302, d-edit 73, d-sim 28, d-2c 10, d-owner 10, d-0032 8), **deferred 2, raised 17: 1 526.**

**H6g (filed 2026-10-27, reverser, `lane/h6g`): 17 statements of player/creation (rows 2-4, 12, 16, 18, 22, 23, 25, 27, 28
x2, 29, 30, 32, 33, 35).** run:2026-10-27-sweep-player, 9 kept logs on slot 2 (expansion; Normal, Nightmare, Hell;
tool-built saves), logger `tools/gdb/h6g.gdb` (`player.gdb`'s files and the new `h6g.py`), checks over the 9 kept logs:
`tools/player.py check` 0 failed (4 new characters, 145 kills, 1 level-up), `tools/sweep_h6g.py check` **0 mismatches**
(`check-final.txt`), `static` 31 pins 0 failing. The evidence is in
[player/0001 § Plan 0038 batch H6g](../../findings/player/0001-creation.md#plan-0038-batch-h6g-run2026-10-27-sweep-player),
whose ledger gives each statement's `[C]` part and remainder.

- **Raised (7):** player/creation 4 and 32 (the four stat spends), 18 (the belt's column, free and none paths), 22 (145
  kills: the input is the monster's base stat 13), 25 (73 kills with stat 85 = 10), 28 x2 (`T(98)` exactly, level 99).
- **Raised in part (8):** 3 and 30 (the death loss on three difficulties, the clamp, the corpse share; the pickup
  unreached after four `deathnm` sessions), 12 (bit 0 is set before the `or`), 16 (the at-the-maximum side: the client
  sends no request), 23 and 35 (the cap return; the non-positive input never met), 27 (the clamp and the overflow still
  not reached, d-owner rows 5 and 24), 33 (J2 not run).
- **Open, shortfall (2):** 2 and 29 (`ExpGrantCapped`): two tries of the Ancients route did not reach the altar (no warp
  76 on seed 6718, no object 546 at level 120 on seed 4314); filed to the architect for a route ruling (d-owner or a
  further route with the summit door of class 564).
  (2026-10-30, `lane/h6ga`: run since; rows 2 and 29 raised in part, the Normal amount, the cut and both loop branches
  `[C]`, the 20 000 000 and 40 000 000 immediates open; [player/0001](../../findings/player/0001-creation.md#plan-0038-h6g-rows-2-and-29-the-ancients-grant-session-run2026-10-30-h6ga-anc). Totals unchanged.)

No row changed class: the 17 stay in (b) until the review, so the totals stand on `main`'s: **static 567, harness 509,
c-emu awaiting a batch 0, blocked 431** (d-none 302, d-edit 73, d-sim 28, d-2c 10, d-owner 10, d-0032 8), **deferred 2,
raised 17: 1 526.** (Recounted after merging `main` at `5c7f1c5e`; any reclassification of rows 2, 29 or 23's
remainder is the review's.)

**H1c (filed 2026-10-30, reverser, `lane/h1c`): 6 statements, the H1a shortfalls (hirelings 3, 30, 33; player/creation 1;
items/uniques-sets 21; save/d2s 126), plus the piece of sock 1 routed by the `lane/h6b` review.** run:2026-10-27-sweep-d2s-legacy,
7 kept sessions on slot 1 (the five `lane/a72` recipes, and `leg71sock` and `leg71act2` added here), logger
`tools/gdb/d2s-h1c.gdb` (H1a's files and `d2s-h1c.py`), `tools/sweep_h1c.py check` **272 comparisons, 0 failing**
(`check/sweep-h1c-check.txt`). The evidence is in the "Plan 0038 batch H1c" sections of
[save/0001](../../findings/save/0001-d2s-io.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy),
[hirelings/0001](../../findings/hirelings/0001-hirelings.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy),
[player/0001](../../findings/player/0001-creation.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy),
[items/0004](../../findings/items/0004-uniques-sets.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy) and
[items/0007](../../findings/items/0007-sockets-runewords.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy).

- **Raised (3):** hirelings 3 (`ReadMercOldSave`, both forms), items/uniques-sets 21 (the restore branch, rows 0 and 1;
  the version-0 half stays the d-none half), save/d2s 126 (the 1.09 widths and per-id overrides on a version-92 item).
- **Raised in part (3):** hirelings 30 (the Id `0xFFFF` and its result 1; "the act's first row" not separated by an
  Act II file), hirelings 33 (the version-87 conversion and the version-71 absence; the 89 cutoff needs a 90 or 91
  file), player/creation 1 (`NewCharLegacy` reached by the legacy reader and the new character built; the
  `PlayerLoad` caller not met).
- **Open:** none of the six. Sock 1's piece: the first version-71 insert site ran twice, the second (0x005313F0, the
  corpse path) not (the builder writes no corpse; archivist entry filed); the row stays counted in H6b.

No row changed class: the totals stand on `main`'s (`c0ee3e05`, merged before this entry): **static 567, harness 509,
c-emu awaiting a batch 0, blocked 431, deferred 2, raised 17: 1 526**; any move of the in-part rows is the review's.

## 3. Blocked rows, for the plan's open questions

- **d-2c, 14 statements** (items/tc 3, items/vendors 5, items/quest-drops 3, hirelings 1, player/creation 2). This is
  what accepting ADR-0008 would unlock now. *(2026-10-20: 7 of them raised by plan 0044, and tc 43, 44 and
  player/creation 6 raised in part; d-2c is now 7: [§ 2.6, Plan 0044 Phase 3](#26-moves-made-by-the-batch-reviews).)*
  *(2026-10-27, `lane/h6b` review: sockets 9, the UI states 10 and 11 of the player-trade window, joins; d-2c is now 8.)*
  *(2026-10-27, `lane/h6c` review: vendors 29 and 32, a gamble window left open by a second interactor; d-2c is now 10.)*
  - Partial rows add a few more halves: the trade part of sockets 22, the party half of player/creation 33, the
    n > 1 part of quest-drops 25.
  - Six save/d2s rows (1–3, 6, 18, 19) assume that a one-client TCP/IP host counts as one client. If the review
    rules otherwise, they become d-2c. *(2026-10-27, `lane/h1b` review: a one-client TCP/IP host counts as one client. None of the six becomes
    d-2c. Rows 1, 3 and 19 are H1b shortfalls; rows 3 and 19 are candidates for d-none, § 2.6 H1b block.)* *(2026-10-27,
    `lane/r1h`: rows 3 and 19 proposed d-none, § 2.6 H1b block.)*
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
| **S1a** | 54 (56 filed; 2 returned, § 2.6) | 0/49/5 | save/d2s 5, 7–8, 11–16, 20, 24, 32, 45, 51, 58, 61, 63–64, 66, 69–71, 74–76, 79, 81, 84–87, 92–94, 96–101, 103–104, 109, 117, 119–121, 123–124, 128, 130–131, 135–138 | writer/reader pairs (rule 1); `d2s.py survey` over every game-written save (rule 2) | `findings/save`: addenda to run:2026-10-12-d2s-io, -10-14-props-forced, -10-16-calc |
| **S1b** | 75 (76 filed; 1 returned, § 2.6) | 7/52/16 | data/README 1; data/calc 1–2, 6–7, 18–19; data/excel 9–14, 19, 21, 23, 26, 28–31, 33–35, 38, 41–42, 45–49, 55, 57, 61–63, 67–68, 72–73, 75–78; data/strings 1, 3, 11, 21, 31, 33; rng 2, 4, 7; rng/seeds 1, 3, 11, 15–16 | the `tc.py` TC array against the tc-drops logs; item index ↔ code over kept item logs; archive precedence; `excel_bin.py survey`; strings, calc, seed-tree and rng-emu addenda | `findings/data`, `findings/rng` (addenda) |
| **S1e** | 71 (74 filed; 3 returned, § 2.6) | 0/4/67 | data/calc 4–5, 9–16, 20, 31 (6 of 7), 36–40; data/excel 16, 36–37, 40, 43–44, 51–53, 56, 60, 64, 66; data/strings 4–5, 10, 12, 14, 16–17, 20, 24–25, 32, 35; rng 3, 5; save/d2s 82, 122, 129, 133 | **(c-emu)**, ADR-0015: `tools/ghidra.sh emutrace` (`EmuTrace.java`) and `tools/sweep_s1e.py` on `CALC_Eval`, `CALC_Compile`, `SKILLS_CalcVar`, `SKILLS_DimReturns`, the calc entry points, `BITBUF_WriteClamped`, `EXCEL_FindCode`/`AddCode`, the excel cell parsers, the string-table lookups and `RNG_RangePow2Plus`, each against a `tools/` model. Each function's read set is declared, and each has a negative control. | `findings/data/experiments.md` **run:2026-10-17-sweep-emu**; addendum to run:2026-10-11-rng-emu |
| **S1f** | 15 (created at the S1e review, § 2.6) | 0/2/13 | drlg/preset 6 (second statement); monsters/stats 9, 11; monsters/pool 27 (conditional); items/affixes 6, 12; items/uniques-sets 44 (conditional); data/calc 8, 33; data/excel 65 (5), 69 | **(c-emu)**, ADR-0015: `tools/ghidra.sh emutrace` and `tools/sweep_s1f.py` (reusing `tools/sweep_s1e.py`) on `MONSTATS_ValidId`, `sub_00483360_MulDiv`, `sub_005BDB20_MonVariantRoll`, `sub_005C0D00_AffixCandAdd`, `ITEMS_BuildSetPick`, `EXCEL_ParseTxt` (defaults pass, callback order) and `SKILLS_CalcVar` codes 43–48; the S1e review's conditions (§ 2.6) | `findings/data/experiments.md` **run:2026-10-17-sweep-emu2** (15 raised; reviewed 2026-10-17, accepted with fixes) |
| **S2a** | 57 (65 filed; 8 returned, § 2.6) | 51/0/6 | quality 1, 5, 7, 10–11, 13–14, 18–19, 24–30, 33, 35; tc 3–5, 7, 12–16, 18–19, 21, 23–25, 28–36, 38–42, 48–52, 57–58, 61–62, 64, 66–69, 72–74 | `tc.py replay` (incl. `--quality model`) and `quality.py` over the kept tc-drops logs; classic counterfactual replays; xrefs; TreasureClassEx data checks | `findings/items`: addenda to run:2026-10-11-tc-drops, -10-13-quality, -10-14-uniques/-props |
| **S2b** | 49 (58 filed; 9 returned, § 2.6) | 39/0/10 | affixes 1, 3–4, 8–10, 15, 22, 27–28, 30, 34–35, 37; properties 1–2, 4–6, 8–9, 16, 18; uniques-sets 3–6, 12–13, 15, 20, 23–24, 27–29, 32–34, 36, 40, 42 (returned: affixes 7, 16; properties 23, 24; uniques-sets 8, 9, 22, 31, 39) | `items_chain.py`, `uniques.py`, `props.py`, `affixes.py` over ichain*, uniques-*, props*, quests-s*-cows; a new `ITEMS_RollStaffMods` checker case removes that oracle | `findings/items`: addenda to run:2026-10-15-items-chain, -10-14-uniques, -10-14-props |
| **S2c** | 76 (86 filed; 10 returned, § 2.6) | 1/57/18 | affixes 2, 11, 14; cube 6, 8, 10, 12–13, 17, 20–22, 24, 29, 45, 47, 49, 51–52, 55–56, 58; properties 19; quality 16; quest-drops 7–10, 14, 19–21, 28, 31, 37–38, 41, 47–49; sockets 2–6, 8, 14, 19–20, 25–28, 32, 34–36, 41–47; uniques-sets 1; vendors 3–4, 7–9, 11, 19–22, 24–28 (returned: cube 17, 20, 24, 51, 58; quest-drops 48; sockets 35 ×2, 36 (L442), 42) | `cube.py`, `sockets.py`, `vendors.py`, `questdrops.py` over kept logs; a new `InvPlaceItem` case; second sources from save/d2s; xrefs | `findings/items`: addenda to run:2026-10-15-cube, -sockets, -vendors, -10-16-quest-drops |
| **S3a** | 39 (69 filed; 30 returned, § 2.6) | 26/10/3 | hirelings 4, 19, 26; monsters/README 1; player/creation 7, 10, 13–14, 26; pool 3–4, 8, 10–11, 13, 16–17, 20–22, 27–28; spawn 6, 8, 10, 13–15, 17, 21, 26, 29–30, 32–34, 36–39, 45–46, 54; special 3–4, 17, 21, 23, 28, 34, 39, 41, 48, 62, 64–65, 73; stats 2, 9, 11, 16, 25–27, 31, 36, 38 | new checks over monpool*, monspawn-s*, monspecial-s*, monstats-s*, berserkf-*, hire-run, player-run (`monpool.py`, `monspawn.py guard`, `monstats.py fpsens`, `hirelings.py`, `player.py`). A guard the logs never took goes to d-none and is not raised. | `findings/monsters`, `hirelings`, `player` (addenda) |
| **S3b** | 15 (17 filed; 2 returned, § 2.6) | 1/4/10 | hirelings 7–8; player/creation 16, 21, 36; pool 9, 23; spawn 1–2, 7, 41, 50, 52; special 43; stats 19, 30, 45 (returned: player/creation 16; spawn 41) | second code paths; full-table checks of monstats2 `+0x025`, MonStats `SizeX` and reversed HP, MonProp, hireling.txt order, Experience `ExpRatio` | finding sections |
| **S4a** | 77 (89 filed; 12 returned, § 2.6) | 69/1/7 | collision 6–7, 12–13, 15–18, 20, 29, 31–33, 38, 41–44, 47, 49; drlg/README 6–9, 12, 14–16; maze 1, 3, 7–8, 16; objects 7–9, 11, 14, 28, 37, 47; outdoor 1, 6, 8, 10, 16; preset 1, 5, 7, 9–10, 16, 18, 20, 23–26, 28, 30, 38, 40; room-tiles 4–5, 8, 10, 12–14, 16, 18, 21, 24, 26, 28, 34, 37; warps 13–14, 16, 18 | `drlg.py gen/roomk`, `maze_replay.py`, `outdoor_replay.py`, `collision.py`, the objects checker, the `QGS` lines of run:2026-10-16-quest-drops | `findings/drlg`, `findings/objects` (addenda) |
| **S4b** | 39 (44 filed; 5 returned, § 2.6) | 9/0/30 | collision 2, 4, 10, 26, 39; drlg/README 11, 17; maze 2, 9; objects 1–2, 22, 25, 43; outdoor 3, 5, 19; preset 3, 6, 8, 11, 21, 27, 29, 33–34, 36–37, 39, 41; room-tiles 3, 7, 9, 17, 19–20, 23, 25, 29, 32, 35; warps 7, 20 | xrefs with a second tool, writer/reader pairs, full-table data checks, a `rngcallgraph` rerun with an r2 LCG scan | finding sections |

### Harness batches

Sessions are the clusters' estimates. A lane that counts more than 20 before its first session splits the batch with
a letter suffix and its own run id, as the plan requires.

| Batch | Slug | Stmts | T1/T2/T3 | Rows | Recipe, logger and checker; new pieces | Record | Sessions |
|---|---|---|---|---|---|---|---|
| **H1a** (done) | `d2s-load` | 46 (45 filed; uniques-sets 21 from H6d, § 2.6) | 0/3/43 | save/d2s 9–10, 17, 22–23, 26–30, 36, 38, 44, 46–47, 49–50, 52–54, 59, 62, 65, 68, 80, 90–91, 105–107, 126, 132, 139–140; hirelings 3, 30, 32–33; player/creation 1, 8–9, 11, 20, 34; uniques-sets 21 (from H6d) | `d2s-io.gdb` + `d2sio.py check`. Tool-built saves from `d2sio_saves.py`: bad magic or version, wrong name, class 7 and 8, act 5, status mismatches, waypoint markers, out-of-range unique and set ids, legacy v94 and versions 71 and 87 (builder support needed; from H6d, a version-`0x47` item list holding a unique, under `uniques.py`, if a version-71 load reaches `0x00533350`), item version < 93, ear, personalized, realm, > 8 KiB, checksum and size wrong; `MercMF` loaded. From S1b (one extra session, staged by plan 0051 Phase 1a; the rows stay counted as S1b, § 2.6): `tools/gdb/s1b-pieces.gdb` + `s1b-pieces.steps` on CalcSor, the hover marker `CH` (data-calc 19) and the `SUNITPRE` caller `ra` with a second load (rng-seeds 11), checked with `rng.py seedtree`, `calc.py hover` and `calc.py check` | `findings/save/experiments.md` | ~19 |
| **H1b** (done) | `d2s-play` | 48 | 0/22/26 | save/d2s 1–4, 6, 18–19, 21, 25, 31, 33–35, 37, 39–43, 48, 55–57, 60, 72–73, 77–78, 83, 88, 102, 108, 110–116, 117 (from S1a), 118, 124 (from S1a), 125, 127; hirelings 24 | same family. A one-client TCP/IP host, weapon swap, hotkeys, the hirelings mercenary saves (write side, dead flag), iron golem, corpse, runeword, the `questdiffcheck` item, `maxhp`/`maxmana` and poison items, the bit-13 case, and section writer, reader and join breakpoints. **Also:** load `questrewards` and `questrewardsh` (built `246515c5…`, `14c28526…`; backlog 2026-10-16, archivist `lane/abl`) and pin both in `tools/test_d2s.py` with the run id, as the plan 0032 recipes were pinned. From S1a (§ 2.6; 117 and 124 counted here, the other pieces stay counted as S1a): a set item with one damage group in its main and a bonus list; a lone `fire-max` and a lone `fire-min`; magic damage (group 52); a hired mercenary, a swapped weapon set, a left-button hotkey, an item on the cursor and a class item with an automagic affix at *Save and Exit* | `findings/save/experiments.md` | ~14–17 |
| **H1c** | `d2s-legacy` | 0 new (the 6 H1a shortfall rows, counted in H1a, no class move) | — | hirelings 3, 30, 33; player/creation 1; uniques-sets 21; save/d2s 126 | `d2s-io.gdb` (H1a's logger) on the staged `lane/a72` builds `leg87merc`, `leg87new`, `leg71merc`, `leg71uniq`, `leg92props` (base `smpsor-l50.d2s`); each load logged at the legacy reader's or `D2S_ReadSaveV92`'s return and checked by the game's version-96 write-back field by field (`lane/a72` review rulings 2–3, plan 0038 log). From the `lane/h6b` review (piece; sockets 1 stays counted as H6b): a `leg71` build holding a socketed item with a child, loaded with `sockets.gdb`'s `INS` lines, for the version-71 reader's inserts at 0x005311B5 and 0x005313F0 | run id `sweep-d2s-legacy` | 5 (estimate) |
| **H2a** (done) | `items-tc` | 17 | 10/0/7 | quality 20, 22–23; tc 1–2, 11, 22, 34 (2, from S2a), 37, 45, 47, 59–60, 70–71 | `tc-drops.gdb` + `tc.py`. New lines: the caller, gold (stat 14), the MonDeathDrop exit. A Find Item barbarian, `/players 8` host and chests, Hell mfnecro, skeleton or Valkyrie kills; a classic Countess kill (tc 34, § 2.6) | `findings/items/experiments.md` | ~6 |
| **H2b** (done) | `items-chain` | 25 (5 to d-none, § 2.6) | 7/1/17 | affixes 5, 13, 17, 19–21, 24; properties 7, 20, 24 (from S2b); sockets 42 (from S2c); tc 58, 68 (from S2a); uniques-sets 7, 9, 10, 35, 39 (9, 39 from S2b) | `items-chain.gdb` + `items_chain.py both`. A classic hunt (classicsorc) and a long Hell hunt (also a superior ethereal `dur%` item where the two orders differ, properties 24; magic drops requesting 5 or 6 sockets, sockets 42; from the S2c review, a piece with the row counted as S2c: normal and rare drops requesting more than 3 and 4, sockets 44). New line (tc 58, 68, uniques-sets 9, 39; § 2.6): `game+0xD0` at `sub_00558D90_ItemCreate` entry and after `sub_00552E90_ItemSeedInit`, and `Unit+0x20` with the game seed at `IC0` and `ICJ` | `findings/items/experiments.md` | 6–10 |
| **H2c** (done) | `items-forced` (id ends `-forced`) | 7 | 0/0/7 | properties 12 (spec L390 only), 14–15; tc 10, 55–56 | **forced, admitted with conditions** (§ 6): `items-chain.gdb` + `tc.py`, `props.py` on a loose `treasureclassex.bin` under `-direct`; two edits (classic throwables; TC-named uniques), each its own `-forced` session set | `findings/items/experiments.md` | few |
| **H3b** (done) | `data-load` | 25 | 0/16/9 | data/README 2–5; data/excel 1–8, 17–18, 20, 24–25, 27, 50, 71, 74; data/strings 2, 6, 22, 29 | **new** `excel`/startup logger that also sources `strings.py`. **First piece (review ruling 3):** a `d2run.py` mode that has gdb on the game before `DATATBLS_LoadAll`, built and tested off-slot; if it cannot be made to work, the 9 startup rows are a recorded shortfall and stay `[I]` (they have an observable, so not d-none). Covers `FindFile`, loose files without `-direct`, `-txt`, record-byte dumps, the rare-item hover, `STRTABLE_Unload`. From the S1b review (§ 2.6, rows stay counted as S1b): the remainders of data/README 1 ("only under `-direct`") and data/excel 30 (the code-list tables' names at `DATATBLS_LoadTable` in a stock start) | `findings/data/experiments.md` | ~6 |
| **H4a** (done) | `monsters-a` | 32 | 0/14/18 | pool 12; quest-drops 48 (from S2c); spawn 5, 11, 47–49; special 9–10, 25, 30–31, 34 (from S3a), 35, 38, 46, 48 (from S3a), 50–52, 54–56, 58–60, 68–69; stats 7, 18, 21 | `mon-stats.gdb` with `d2pilot.py` wp, `--descend`, `hunt`, `objop`: Radament, the Travincal council, the Chaos seals, Shenk, Nihlathak, Blood Raven, Andariel, Izual (Blood Raven, Izual or Radament in an expansion Nightmare or Hell game for quest-drops 48), a `flyingscimitar` level. The Ancients (b) need a quest-open recipe. From the H4b review (pieces; the rows stay counted as H4b, § 2.6): `doomknight3` (312) in the Chaos Sanctuary (stats 13, 14), a `willowisp` champion or unique (stats 40), Blood Raven's client name (special 66, mod 12), an aura special of level ≤ 15 (special 27, the clamp at 1); if a seed places one, a Shrines code-20 shrine operated with `objop` (special 2, 74; `MMS0`); optionally the camel at `/players` 8 (stats 23). From S3b (pieces; the rows stay counted as S3b, § 2.6): a Druid casting Raven in a Normal game (stats 30, the `druidhawk` Normal MonProp row), and, optionally (the S3b review raised the rows without it; no row depends on it), a Normal visit to the Durance of Hate Level 3 (`mephistospirit`, stats 19 and 45). Checked with `sweep_h4b.py` and `monstats.py` | `findings/monsters/experiments.md` | ~10 |
| **H4b** (done) | `monsters-b` | 45 (47 filed; 2 returned, § 2.6) | 22/1/22 | hirelings 34; pool 1, 7, 8 (from S3a), 19; spawn 3, 6 (from S3a), 12, 42–45 (45 from S3a), 51; special 1–2, 5–7, 11, 15–16, 18, 20, 27, 29, 65 (from S3a), 66–67, 71–72, 74; stats 5, 13–14, 17, 20, 23, 40, 44 | `mon-stats.gdb` extended (skill list, aura id and level, client names, restore lines; from S3a: the tick line for every room, `PM0` for every MonPlace case) plus seeded-pool hunts picked with `monpool.py pool` (from S3a: a level holding class 141, 398 or 659–661), a `/players 8` `MercNova` session, and (from S3a) a classic Normal game start with `mon-pool.gdb` | `findings/monsters/experiments.md` | ≤ 20 |
| **H5a** (done) | `drlg-links` | 16 (21 filed; 5 to d-none, § 2.6) | 16/0/5 | maze 4–5, 15; preset 22; warps 3, 5–6, 8–9, 11–12 | `drlg-maze.gdb` (LNK0/LNK1/LK27) + `drlg.py gen`; map seeds chosen offline with the link-builder model; `-seed N -act A` starts and one Barracks entry | `findings/drlg/experiments.md` | few |
| **H5b** (done) | `objects` | 32 (33 filed; 1 to d-none, § 2.6) | 12/2/19 | collision 27, 37, 39 (from S4b); objects 3–4, 6, 13, 15–17, 19–20, 23, 26–27, 35–36, 38–42, 45–46, 49–52 | `objects.gdb` + the objects checker, `d2pilot.py objop`, seeds from the populate model; the casket group and the orientation-2 shrine (plan 0023 ruling); from S4b (§ 2.6), one object of size 0 with `HasCollision` set (class 131, 399 or 564–567) created on `objects.gdb`; new `OBJTRAP_ObjectCreate` fire lines and revisit restores | `findings/objects/experiments.md` | ≤ 20 |
| **H5c** (done) | `roomk` | 41 | 33/0/8 | drlg/README 1–3, 5, 10; preset 31–32; room-tiles 1–2, 4 (2), 14 (2), 15, 27, 28 (3), 30–31, 33, 37, 38; warps 1, 16, 19; **rng/seeds 2, 4–10, 14** (ex H5r); room-tiles 4, 14, 28, 37 and warps 16 from S4a (§ 2.6) | `drlg-roomk.gdb` and `collision.gdb` (LevelUnload, RoomTilesRelease, TINIT-exit flags, `LI0` caller, the act callback, WarpExitPos), plus `seed-tree.gdb` + `rng.py seedtree` (act-seed steps in `LevelLinkBuild`, `R+0x28`/`R+0x60` and `T+0x18`/`+0x20` at activation, flags at `0x0052D1C9`, `LEVEL` caller, client `UnitInit` (x, y), one `-seed -2147483648` session). rng/0002 cites the record. From S4a (§ 2.6): a walled level whose bit-2 merges go through the remap rows 0–5, the row −2 return and the 8/9 edge (counted by `sweep_s4a.py roomk` on the batch's logs), and a `RoomNeighboursEnsure` line at `0x0066C370` (room, warp bits, each `WarpPairLink` call and outcome) | `findings/drlg/experiments.md` | ~10 |
| **H5d** (done) | `collision` | 17 | 6/0/11 | collision 1, 5, 8–9, 11, 19, 21, 24, 30, 36, 45–46; spawn 41 (from S3b) | `collision.gdb` + `collision.py`: tombs (228), Act III (334), Act V (298, 528, baaltaunt), a non-town `Position` level, `spawnCol` 1, ground items, an entry-flag `0x80` cell. From the H4b review (piece; the row stays counted as H4b): the tomb (228) and `suckernest1` (334) sessions also decide spawn 42's remainder, by `monspawn.py check` on the presets-window `SpawnClassCellTest` (`MC`) lines. From S3b (§ 2.6): a `sarcophagus` (228, size 1) and a `baaltaunt` (545, size 0) creation with their `MK0` lines (spawn 41) | `findings/drlg/experiments.md` | ~8 |
| **H5e** (done) | `drlg-mazes` | 22 | 16/0/6 | maze 6, 10–12; outdoor 7, 11, 13–14, 20; preset 2, 12–14 | `drlg-outdoor.gdb` (with the maze lines) + `drlg-preset.py`, `maze_replay.py`, `outdoor_replay.py`, `drlg.py gen`: unreached maze levels from waypoint saves, outdoor rare branches on chosen seeds, the Blood Moor centre monster | `findings/drlg/experiments.md` | 16–17 |
| **H6a** (done) | `cube` | 29 (2 reclassified, § 2.6) | 0/18/11 | cube 1, 7, 15–16, 17 (from S2c), 25, 32, 36, 38–40, 43–44, 51 (from S2c), 53–54, 58 (from S2c) | `cube.gdb` + `cube.py`; new `.plan` files (upgrades, eth/strip rows, ethereal or socketed inputs, repair, recharge, `qty`, Staff of Kings, Khalim's Will, unsocket, the cow portal outside level 1 and in classic; from S2c: an elite upgrade with an exceptional-tier and a normal-tier base, more row-19 transmutes, row 17 on a magic tower shield, which also decides affixes 14's remainder); a UnitSetEvent line. From the S2c review (piece; cube 49 stays counted as S2c): a crafting session at output ilvl ≤ 5 with `sst` (rows 72, 90), `lbt` (83) or `lgl` (84) on a tool-built low-level save, for the crafted pick of 0; case (b) faults the game, so it is the session's last transmute | `findings/items/experiments.md` | ≤ 20 |
| **H6b** (done) | `sockets` | 25 (4 reclassified, § 2.6) | 0/20/5 | sockets 1, 9–10, 12–13, 16–18, 21, 29, 35 ×2 (from S2c), 38 | `sockets.gdb` + `sockets.py`; child x/y and cursor lines; sock-refuse and sock-rw plans; a save holding a runeword (the *Steel* sample) loaded under the logger (sockets 35; with it the reader's `+0x38` store of sockets 46). From the S2c review (piece; sockets 14 stays counted as S2c): an unidentified socketed parent's client flags before and after identifying it, with an insert tried each time | `findings/items/experiments.md` | ≤ 20 |
| **H6c** (done) | `vendors` | 13 (2 reclassified, § 2.6) | 0/11/2 | vendors 2, 5, 12, 14–15, 18, 29–30, 32–34, 36 | `vendors.gdb` + `vendors.py`; reopen store or gamble, Asheara's hire list first, walk out of town, level-up between opens, buy and sell; saves at clvl ≤ 9, ≥ 96, 99 in Hell. From the S2c review (pieces; vendors 22 and 26 stay counted as S2c): the stock item's store tab and grid cell, and `+0x18`/`+0x28` of the store creation record at `IC0` | `findings/items/experiments.md` | ≤ 20 |
| **H6d** (done) | `quest-b6` | 16 (17 filed; uniques-sets 21 to H1a, § 2.6) | 10/5/2 | quest-drops 11, 13, 16, 18, 22, 25, 27; tc 26–27; uniques-sets 21 | `quests.gdb` + tc-drops, `tc.py` b6_model, `questdrops.py`: Andariel or Duriel killed by a mercenary or summon, Diablo and Baal, Warriv's report, questfresh in Nightmare, Hell and classic, the forge with a stat-356-1 hammer, the unique restore path | `findings/items/experiments.md` | ≤ 20 |
| **H6e1** (done) | `quest-npc` | 22 | 0/20/2 | quest-drops 2, 4–5, 32, 39–40, 42–46, 50–51 | `quests.gdb` + `d2pilot.py npc`: given items and service branches and refusals. From the S2c review (piece; quest-drops 38 stays counted as S2c): a cursor-item line at `sub_0055EEA0_CursorItemConsume` in each service branch | `findings/items/experiments.md` | ≤ 20 |
| **H6e2** (done) | `quest-items` | 24 | 0/23/1 | quest-drops 1, 30, 33–35; objects 48 | `quests.gdb` with `objop`/`hunt` on tool-built quest saves: the 16 quest items, chests, duplicates, the item-move gate; the quest objects ride the same sessions; a backtrace at `QUESTS_ObjectEvent` (quest-drops 1). objects/0001 cites the record | `findings/items/experiments.md` | ~20, at the cap |
| **H6f** (done) | `hirelings` | 23 (2 reclassified, § 2.6) | 0/17/6 | hirelings 1–2, 5–6, 9–10, 14–18, 20–21, 23, 25, 27–29, 31, 35–37 | `hirelings.gdb` + `hireling_sessions.py`: Asheara's trade first, Greiz, classic lists, the free mercenary, the level floor, quest, level and gold gates, stash payment, `MERC_AddExp`, `merc_saves.py` saves, resurrection | `findings/hirelings/experiments.md` | ≤ 20 |
| **H6g** | `player` | 17 | 0/8/9 | player/creation 2–4, 12, 16 (from S3b), 18, 22–23, 25, 27–30, 32–33, 35 | `player.gdb` + `player_sessions.py`: death loss, a stat point, two skill points on one skill and one skill to its maximum (16, § 2.6), stat 85, the level-99 cap and a level-98 save, the capped grant (trigger read statically first), client `+0x3D4`, the belt column, the monster's experience at the kill | `findings/player/experiments.md` | ≤ 20 |
| **H7a** (done) | `lifecycle` | 0 inventory rows (plan 0040 P2 shortfalls, `lane/rbs4` review) | — | none: drlg/lifecycle open questions, the town-follow case and the `0x400` drop ([drlg/0009 § 11.2](../../findings/drlg/0009-room-lifecycle.md#112-the-town-follow-static-remainder-lanerbs4), § 11) | `rooms.gdb` + `rooms.py check`, `rooms_sessions.py` (run:2026-10-17-lifecycle's family). (1) Town-follow, recipe (b): a chaser in the Blood Moor whose planned route to the player crosses a Rogue Encampment room; then the player leaves until the camp's rooms release, and the save rule's `SaveMonsters` 0 half is checked. Its map seed and points come from an offline geometry check made before a slot is taken (reverser entry [rbs4 review static remainders](../../backlog/archive/2026-10-17-architect-reverser-rbs4-review-static-remainders.md) (1)); if no stock layout allows the route, (b) is a recorded shortfall. Recipe (c), a teleporting unique chasing a player inside the camp, only if that entry's (2) shows an AI teleport target can lie in a town room. (2) The `0x400` drop: re-enter an `h-highlands` room holding a class 522 record with flags `0x540`. | `findings/drlg/experiments.md` | ~4 (estimate) |

**Logger-family conflicts.** Two batches may run at once only when they share no recipe save, logger file or checker
under edit. Inside one family the batches run one after the other:
- H1a, H1b and H1c;
- H2a, H2b and H2c;
- H4a and H4b;
- H5a, H5c, H5d and H5e (H5c edits `collision.gdb`, which H5d uses);
- H6d, H6e1 and H6e2.

H7a is its own family (`rooms.gdb`) and may pair with any batch.

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
| 1 | S4a (done) | 69 | 1 | 77 |
| 2 | S2a (done) | 51 | 0 | 57 |
| 3 | S2b (done) | 39 | 0 | 49 |
| 4 | S3a (done) | 26 | 10 | 39 |
| 5 | S4b (done) | 9 | 0 | 39 |
| 6 | S1b (done) | 7 | 52 | 75 |
| 7 | S2c (done) | 1 | 57 | 76 |
| 8 | S3b (done) | 1 | 4 | 15 |
| 9 | S1a (done) | 0 | 49 | 54 |
| 10 | S1e (done, reviewed: accepted with fixes) | 0 | 4 | 71 |
| 11 | S1f (done, reviewed: accepted with fixes) | 0 | 2 | 15 |

**Harness (Phase 2; queue rules of the plan: 0037·P2 first, never more than two harness lanes, never slot 0):**

| Rank | Batch | T1 | T2 | Stmts | Note |
|---|---|---|---|---|---|
| 1 | H5c | 33 | 0 | 41 | logger edits (roomk, collision, seed-tree), made and regression-checked off-slot; +9 from S4a (§ 2.6), one more line (`RoomNeighboursEnsure`) |
| 2 | H4b (done) | 22 | 1 | 45 | logger extension; pairs with H5c; +4 from S3a, −2 at its review (§ 2.6) |
| 3 | H5e (done) | 16 | 0 | 22 | no logger change; after H5c (same family); reviewed, no class move (§ 2.6) |
| 4 | H5a (done) | 16 | 0 | 21 | after H5e; a new logger file (`drlg-links.py`), 9 sessions; reviewed, 5 to d-none (§ 2.6) |
| 5 | H5b | 12 | 2 | 33 | objects family; may pair with any DRLG batch; +1 from S4b (§ 2.6) |
| 6 | H6d (done) | 10 | 5 | 17 | 19 sessions; reviewed, us 21 to H1a, the Diablo remainders d-owner candidates (§ 2.6) |
| 7 | H2a | 10 | 0 | 17 | +2 from S2a (§ 2.6) |
| 8 | H2b | 7 | 1 | 25 | +2 from S2a, +3 from S2b, +1 from S2c (§ 2.6) |
| 9 | H5d | 6 | 0 | 17 | after H5c (`collision.gdb`) and H5a; +1 from S3b (§ 2.6) |
| 10 | H6e2 | 0 | 23 | 24 | at the session cap |
| 11 | H1b | 0 | 22 | 48 | includes the reward-recipe loads; +2 from S1a (§ 2.6) |
| 12 | H6b | 0 | 20 | 25 | +2 from S2c (§ 2.6); ahead of H6e1 on size |
| 13 | H6e1 | 0 | 20 | 22 | |
| 14 | H6a | 0 | 18 | 29 | +3 from S2c (§ 2.6) |
| 15 | H6f | 0 | 17 | 23 | |
| 16 | H3b | 0 | 16 | 25 | the `d2run.py` start mode first (ruling 3) |
| 17 | H4a | 0 | 14 | 32 | after H4b (same family); +2 from S3a, +1 from S2c (§ 2.6) |
| 18 | H6c | 0 | 11 | 13 | |
| 19 | H6g | 0 | 8 | 17 | +1 from S3b (§ 2.6) |
| 20 | H1a | 0 | 3 | 46 | after H1b (same family); +1 from H6d (§ 2.6) |
| 21 | H2c | 0 | 0 | 7 | forced, admitted with the § 6 conditions; after H2b (same family) |
| 22 | H7a | 0 | 0 | 0 | plan 0040 P2 shortfalls, not inventory rows (`lane/rbs4` review); its static prep first (reverser entry (1), (2)); may pair with any batch |

**Order from 2026-10-20 (owner).** The harness ranks above are superseded for the batches left: H5b (in flight) →
H2a → H2b → H2c → H4a → H5d → H1b → H1a → H3b, then H6e2 → H6e1 → H6b → H6a → H6c → H6f → H6g. The family rules
below and in the notes still hold ([plan 0038 log](../0038-inferred-claims-sweep.md#implementation-log)).

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
- S1f writes the data findings and the run record S1e wrote, so it starts after `lane/s1e` merges (S1e review).

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
  - On sessions, H6e2 (about 20) and H1a (about 19, with the S1b session plan 0051 Phase 1a staged) are near the cap.
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
