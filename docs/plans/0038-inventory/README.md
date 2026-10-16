# Plan 0038 inventory: totals, batch list and priority order

Phase 0 of [plan 0038](../0038-inferred-claims-sweep.md), written by the architect on `lane/c38` from the four cluster
inventories: (0a) items, (0b) save, data and rng, (0c) monsters, hirelings and player, (0d) drlg and objects. The
cluster files read the specs at `main` `e1c807a`. Up to `551bee9` the only spec change is the name-only rename
`QUESTS_ObjectOperate` → `QUESTS_ObjectEvent` in items/quest-drops and objects, so every front-matter count still
holds.

**Status: awaiting the Phase 0 review.** No Phase 1 or Phase 2 batch starts before the review accepts this list, and
the review may move rows (plan, Phase 0 *Done when*).

How to read this file:
- **The per-spec files keep the class and batch the clusters gave each row.** This README is the authority where the
  two differ: it adds the [moves](#2-moves-after-the-clusters-read-the-specs) of § 2 and the
  [batch reconciliation](#4-batch-ids-reconciled-across-clusters) of § 4.
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

| Cluster | I | a-logs | a-run | b | c | c-emu | raised | d-none | d-edit | d-sim | d-2c | d-owner | d-0032 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0a | 523 | 155 | 26 | 139 | 54 | · | · | 104 | 27 | 1 | 11 | · | 6 |
| 0b | 380 | 63 | 2 | 113 | 69 | 74 | 8 | 19 | 25 | 7 | · | · | · |
| 0c | 317 | 69 | 44 | 80 | 17 | · | 2 | 71 | 14 | 8 | 3 | 7 | 2 |
| 0d | 306 | 89 | 100 | 19 | 44 | · | · | 45 | · | 8 | · | 1 | · |
| **All** | **1 526** | **376** | **172** | **351** | **184** | **74** | **10** | **239** | **66** | **24** | **14** | **8** | **8** |

The breakdown by batch:
- **1 156 statements are batched:**
  - 634 in ten static batches;
  - 522 in twenty-one harness batches, including the forced H2c.
- **1 statement is deferred** (data-calc 32).
- **10 are raised.**
- **359 are blocked (d):**
  - d-none 239;
  - d-edit 66;
  - d-sim 24;
  - d-2c 14;
  - d-owner 8;
  - d-0032 8.

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
- **d-sim, 24 statements.** They belong to plan 0037 or to a later ADR-0014 phase:
  - monsters/stats § H, the attack masks, the MonPlayerBonus attack callers;
  - the data/calc unit-state inputs, `blvl` among them;
  - hirelings `MERCAI_PickSkill`;
  - collision movement (7), and one row each in vendors and objects.
- **d-edit, 66 statements**, for example `evilhut`/`sparsePopulate`, the TC-named and upgrade-draw cells, forged
  socket packets and non-`eng` languages. § 2.1 lists the ones that emulation might still reach.
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
| **H2a** | `items-tc` | 15 | 10/0/5 | quality 20, 22–23; tc 1–2, 11, 22, 37, 45, 47, 59–60, 70–71 | `tc-drops.gdb` + `tc.py`. New lines: the caller, gold (stat 14), the MonDeathDrop exit. A Find Item barbarian, `/players 8` host and chests, Hell mfnecro, skeleton or Valkyrie kills | `findings/items/experiments.md` | ~6 |
| **H2b** | `items-chain` | 19 | 2/0/17 | affixes 5, 13, 17, 19–21, 24; properties 7, 20; uniques-sets 7, 10, 35 | `items-chain.gdb` + `items_chain.py both`. A classic hunt (classicsorc) and a long Hell hunt | `findings/items/experiments.md` | 6–10 |
| **H2c** | `items-forced` (id ends `-forced`) | 10 | 0/0/10 | properties 12, 14–15, 21; tc 10, 55–56 | **forced, pending the review's ruling** (§ 6): `items-chain.gdb` + `tc.py`, `props.py` on a loose `treasureclassex.bin` under `-direct` | `findings/items/experiments.md` | few |
| **H3b** | `data-load` | 25 | 0/16/9 | data/README 2–5; data/excel 1–8, 17–18, 20, 24–25, 27, 50, 71, 74; data/strings 2, 6, 22, 29 | **new** `excel`/startup logger that also sources `strings.py`. **Prerequisite:** a `d2run.py` mode that starts the game under gdb before `DATATBLS_LoadAll`; without it, 9 startup rows go to d-none. Covers `FindFile`, loose files without `-direct`, `-txt`, record-byte dumps, the rare-item hover, `STRTABLE_Unload` | `findings/data/experiments.md` | ~6 |
| **H4a** | `monsters-a` | 29 | 0/12/17 | pool 12; spawn 5, 11, 47–49; special 9–10, 25, 30–31, 35, 38, 46, 50–52, 54–56, 58–60, 68–69; stats 7, 18, 21 | `mon-stats.gdb` with `d2pilot.py` wp, `--descend`, `hunt`, `objop`: Radament, the Travincal council, the Chaos seals, Shenk, Nihlathak, Blood Raven, Andariel, Izual, a `flyingscimitar` level. The Ancients (b) need a quest-open recipe | `findings/monsters/experiments.md` | ~10 |
| **H4b** | `monsters-b` | 45 | 19/1/25 | hirelings 34; pool 1, 7, 19; spawn 3, 12, 42–44, 51; special 1–2, 5–7, 11, 15–16, 18, 20, 27, 29, 66–67, 71–72, 74; stats 5, 13–14, 17, 20, 23, 40, 42, 44, 46 | `mon-stats.gdb` extended (skill list, aura id and level, client names, restore lines, watchpoints) plus seeded-pool hunts picked with `monpool.py pool`, and a `/players 8` `MercNova` session | `findings/monsters/experiments.md` | ≤ 20 |
| **H5a** | `drlg-links` | 21 | 16/0/5 | maze 4–5, 15; preset 22; warps 3, 5–6, 8–9, 11–12 | `drlg-maze.gdb` (LNK0/LNK1/LK27) + `drlg.py gen`; map seeds chosen offline with the link-builder model; `-seed N -act A` starts and one Barracks entry | `findings/drlg/experiments.md` | few |
| **H5b** | `objects` | 33 | 12/2/19 | collision 27, 37; objects 3–6, 13, 15–17, 19–20, 23, 26–27, 35–36, 38–42, 45–46, 49–52 | `objects.gdb` + the objects checker, `d2pilot.py objop`, seeds from the populate model; the casket group and the orientation-2 shrine (plan 0023 ruling); new `OBJTRAP_ObjectCreate` fire lines and revisit restores | `findings/objects/experiments.md` | ≤ 20 |
| **H5c** | `roomk` | 32 | 24/0/8 | drlg/README 1–3, 5, 10; preset 31–32; room-tiles 1–2, 15, 27, 30–31, 33, 38; warps 1, 19; **rng/seeds 2, 4–10, 14** (ex H5r) | `drlg-roomk.gdb` and `collision.gdb` (LevelUnload, RoomTilesRelease, TINIT-exit flags, `LI0` caller, the act callback, WarpExitPos), plus `seed-tree.gdb` + `rng.py seedtree` (act-seed steps in `LevelLinkBuild`, `R+0x28`/`R+0x60` and `T+0x18`/`+0x20` at activation, flags at `0x0052D1C9`, `LEVEL` caller, client `UnitInit` (x, y), one `-seed -2147483648` session). rng/0002 cites the record | `findings/drlg/experiments.md` | ~10 |
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

## 6. Forced-run candidates (for the review to rule; nothing here is ruled)

Only cluster 0a proposed a forced batch, **H2c**, with two candidates. Clusters 0b, 0c and 0d proposed none:
- Their tool-built saves are ADR-0003 inputs under ADR-0013 § Neutral, not forced runs.
- Every 133–136 path is d-none by the plan 0027 Phase 3 ruling.

| # | Claims (rows) | Table and cells to edit | Where the ADR-0013 read lists must stand before the run | Stock companion | Point to rule on |
|---|---|---|---|---|---|
| 1 | Classic throwables: `THROW_RETRIES` 10 and the Long Sword `lsd` fallback (tc 10 ×2, 55, 56; 4 statements) | `treasureclassex.bin`, loose under `-direct`: the `Item1..n`, `Prob1..n` and `Picks` cells of one classic Act I TC a fixed recipe reaches (for example `Act 1 Cpot A`), set to classic throwables only, `Picks` ≥ 12 | [items/0001 § 5](../../findings/items/0001-tc-resolution.md#5-the-pick-loop--tc_resolvedrops-0x0055a6d0) and [§ 8](../../findings/items/0001-tc-resolution.md#8-item-pick-and-hand-off-0x0055ac5f0x0055af59) | the refund itself, already `[C]` (run:2026-10-13-quality, at most 3 refunds per call in 485 classic calls) | The resolver reads `Picks` and `Prob` of the edited row (data-indexed, so whole columns). Do the retry counter and the `lsd` substitution, which read only `ItemTypes.Throwable` and a call-local counter, count as code that reads none of the edited cells? If not, the 4 statements become d-edit. |
| 2 | TC-named uniques: funcs 12/36 put the roll in the param, func 23 ethereal, func 24, and Wraithflight made ethereal twice (properties 12 ×3, 14, 15, 21; 6 statements) | `treasureclassex.bin`: the `Item` cells of the Hell TCs that the run:2026-10-15-uniques-tcnamed-forced recipe reaches, naming *Ormus' Robes*, *Hellfire Torch*, *Ethereal Edge*, *Wraithflight* and a func-24 unique | [items/0006 § 4](../../findings/items/0006-properties.md#4-the-handlers-per-func) (the handlers read `Properties`, `UniqueItems` and the item's stats) and [items/0004 § 6](../../findings/items/0004-uniques-sets.md#6-a-tc-cell-that-names-a-unique-or-a-set-item) (the unique selection reads the named cell and stays `[I]`) | *Ormus' Robes* and the ethereal uniques only if a long Hell hunt meets one; **none for *Hellfire Torch*** (Uber Tristram cannot open) | Is a claim whose subject (the unique) the edited cell names barred, as in the TC-named reversal of ADR-0013? The handlers' own inputs (the property rows) are stock. ADR-0013's third negative consequence also applies: the item's stats must be shown stock at the handler's entry. |

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
| 1 | H5c | 24 | 0 | 32 | logger edits (roomk, collision, seed-tree) |
| 2 | H4b | 19 | 1 | 45 | logger extension; can pair with H5c |
| 3 | H5e | 16 | 0 | 22 | no logger change; after H5c (same family) |
| 4 | H5a | 16 | 0 | 21 | no logger change |
| 5 | H5b | 12 | 2 | 33 | |
| 6 | H6d | 10 | 5 | 17 | |
| 7 | H2a | 10 | 0 | 15 | |
| 8 | H5d | 6 | 0 | 16 | after H5c (`collision.gdb`) |
| 9 | H2b | 2 | 0 | 19 | |
| 10 | H6e2 | 0 | 23 | 24 | at the session cap |
| 11 | H1b | 0 | 22 | 46 | includes the reward-recipe loads |
| 12 | H6e1 | 0 | 20 | 22 | |
| 13 | H6b | 0 | 18 | 23 | |
| 14 | H6f | 0 | 17 | 23 | |
| 15 | H6a | 0 | 16 | 26 | |
| 16 | H3b | 0 | 16 | 25 | needs the `d2run.py` start mode first |
| 17 | H4a | 0 | 12 | 29 | after H4b (same family) |
| 18 | H6c | 0 | 11 | 13 | |
| 19 | H6g | 0 | 7 | 16 | |
| 20 | H1a | 0 | 2 | 45 | after H1b (same family) |
| 21 | H2c | 0 | 0 | 10 | forced; runs only if the review admits it |

Cluster 0d preferred H5a and H5e before H5c because they need no logger change. The plan's rule puts H5c first. The
review may swap them if logger edits are the scarcer resource.

## 8. Caps

- **Static, at most 100 statements:** every S batch fits. The largest is S4a at 89. 0d split S4 into S4a and S4b (133
  statements in all).
- **Harness, at most 60 statements and 20 sessions:** every H batch fits on statements. The largest are H1b (46),
  H1a (45) and H4b (45).
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
  - **H2c** has exactly 10 statements and stays its own batch, because forced runs never share a run id with stock
    sessions.

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

Rolled up from the four cluster reports. Each point is open until the review rules.

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
