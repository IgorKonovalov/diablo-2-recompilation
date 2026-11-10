# 0069 — Monster AI bestiary tour: the catalogue's harness rows of plan 0066

> **Status:** proposed (drafted 2026-11-10, `lane/n69a`; Tier A review accepted with fixes 2026-11-10; the owner approves it, questions 1 and 2)
> **Created:** 2026-11-10
> **Owner skill(s):** reverser (every phase; the re-tag is plan 0066 Phase 3's, spec-writer)
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0021-observed-boundaries-in-emulation, 0023-review-tiers-and-gate-first-fixes, 0028-case-and-process-in-experiment-records

## TL;DR

**Question:** which of the monsters/ai/catalogue `[I]` statements that plan 0066 routed to a harness run (batches H1a
to H1d, H1g and H1h) does one tour of the bestiary raise to `[C]`? The tour logs AI decisions for most of the
monster classes, act by act, and checks them with the S1b block-model checker. Which statements stay `[I]`, and why?
The owner chose this route (plan 0066, question 3 (c)). When the plan is done:

- every one of the batches' 237 statements is raised, raised in part, or kept `[I]` with its reason in
  [`0066-inventory/monsters-ai-catalogue.md`](0066-inventory/monsters-ai-catalogue.md);
- the AI run records hold the tour's cases;
- plan 0066 Phase 3 has a ready list of line numbers to re-tag.

## Context

- **Scope, recounted** from the inventory at `main` `4fb8b55f` (a script over the per-spec files, summing each row's
  *Count* by batch). Every row is in monsters/ai/catalogue, and every row counts 1:

  | Batch | Class | Stmts | Catalogue entries | Entries the S1b checker models |
  |---|---|---|---|---|
  | H1a | a-run | 38 | 10 (rows 8, 16, 17, 18, 24, 25, 27, 72, 74, 142) | 0 |
  | H1b | a-run | 45 | 15 (rows 113, 115–117, 119–123, 126, 129, 136, 137; states 15, 16) | 0 |
  | H1c | a-run | 59 | 20 (rows 38, 45–47, 50, 53, 55, 59, 66, 75–77, 80, 82, 83, 85, 87, 92, 94, 128) | 0 |
  | H1d | a-run | 16 | 8 (rows 41, 42, 58, 60, 62, 81; states 5, 6) | 0 |
  | H1g | a-run | 44 | 24 and the *Reimplementation notes* (rows 4, 7, 11, 14, 15, 23, 26, 33, 36, 39, 40, 43, 49, 52, 56, 57, 65, 71, 93, 95, 98, 100, 114, 124) | 11 (rows 4, 15, 23, 26, 43, 52, 65, 95, 100, 114, 124) |
  | H1h | b | 35 | 13 (rows 1, 10, 32, 43, 48, 54, 68, 70, 73, 78, 79, 118; state 11) | 8 (rows 43, 54, 68, 70, 78, 79, 118; state 11); row 1 shares R100's block function |
  | **Total** | | **237** | | |

  The question 3 figure of about 214 predates the S1 moves. S1a moved 1 row into H1g and 4 into H1h, and S1b moved 8
  into H1g and 10 into H1h. These six batches leave 488 of plan 0066's 725 Phase 2 rows deferred (inventory § 3, after
  S2a).
- **What each batch needs** (inventory § 4, § 5 helper `ai1`):
  - **H1a to H1d:** rows that no kept log reaches ("Not logged"). They need a session in a level that holds the
    class, then a checker that models the block.
  - **H1g:** rows that only the rev 2 or rev 3 loggers logged, or that were logged too thinly. These are the block
    floor of 30 fork-free decisions and the `r` lines' H1 floor of 50. H1g also takes row 23's 8 mismatches, put down
    to the rev 4 logger.
  - **H1h:** rows whose decisions fork on a word the rev 6 logger does not log, which is class (b). They need a
    logger rev 7.
- **The checker.** S1b built `tools/ai_model_check.py` (`f2373e64`; addendum *plan 0066 batch S1b* under
  run:2026-11-04-ai-r5 in [findings/ai/experiments.md](../findings/ai/experiments.md)):
  - one model per catalogue entry, transcribed from the spec block;
  - the logged boundary returns as ADR-0004 oracles;
  - a call-by-call comparison, then the flip, `le`, `lecmp` and `d0` controls;
  - `--logs LIST` for any later run's case logs, and `--rows` to pick entries.

  `tools/ai_resume_flip.py` (S1a) checks the `r` lines against sentence H1.
- **The harness.** `tools/ai_sessions.py` on `tools/harness_runner.py`, logger `tools/gdb/ai.gdb` with
  `tools/gdb/ai.py` rev 6, character `CombatSor` (`tools/d2s_recipes/combatsor.json`: clvl 85 Sorceress, Teleport and
  Nova, all waypoints in all three difficulties, quest progression 15). Its existing cases:
  - `stage` (a waypoint, then a Nova sweep);
  - `catacombs` and `countess` (a waypoint, descents by warp, then a `hunt` with the Nova radius at 1);
  - the melee saves `s-*`.

  The 38 kept logs of S1a and S1b are run:2026-11-03-ai-3 (21, rev 4) and run:2026-11-04-ai-r5 (17, rev 6). Every
  case of both was a fresh process.
- **Pools are predictable.** `tools/monpool.py pool <excel> --seed N --diff D --level ID` gives a level's monster pool
  under `-seed N` (plan 0012, monsters/pool reviewed). `-seed N` holds for every game of a process (harness-play
  § Fresh process rule 4). A pool keeps `NumMon` (3 in 125 of the 137 `Levels` rows) of
  its 2 to 10 candidates. So a stage reaches a class only on a seed whose pool holds it, and the tour picks its seeds
  from the model rather than by luck.
- **Research-map row:** `monsters/ai` (reviewed). Plan 0066 Phase 3 re-tags it; this plan changes no spec.

## The tour's recipe

### Monsters, levels and difficulty

**Normal, except row 142.** Its records (`clawviper6` to `clawviper10`) appear only in the `nmon` slots of Act V
levels, so they need Nightmare. The `aip` of the game's difficulty is in the AID line, and the checker reads it from
there. A second difficulty adds no branch the models need.

The levels below come from `Levels` `mon`/`nmon` against the MonStats records whose `AI` is the row. They were read
for this draft with `tools/ai_survey.py`'s tables, from a scratch script. Phase 1a regenerates them with a kept tool
and adds what a pool cannot show. Rows with no pool mark place their monsters another way:
- presets: rows 33, 38, 40, 45–47, 56, 57, 75–77, 80, 82, 83, 87, 92–94, 113, 121, 123, 126, 129;
- town NPCs: rows 32, 41, 42, 54, 58, 60, 62, 81; states 5, 6;
- superuniques and quest bosses: rows 50, 53, 55, 59, 66, 85, 98, 100, 128, 136.

**Draft case list (an estimate; Phase 1a fixes it).** Act and town cases are `stage`, `catacombs`-like or `hunt`
cases of `tools/ai_sessions.py`:

| Case (draft name) | Stage (route) | Entries aimed at (batch) |
|---|---|---|
| `t-a4-town` | Pandemonium Fortress, the stay-in-town start that logged rows 32 and 54 | 32, 54 (H1h) |
| `t-a1-town` | Rogue Encampment by waypoint | 58, 60, 62 (H1d); 32 (H1h) |
| `t-a1-cold` | Cold Plains; Burial Grounds by warp, `hunt` Blood Raven | 7, 36 (H1g); 10 (H1h); 59 (H1c) |
| `t-a1-darkwood` | Dark Wood | 14, 36 (H1g); 10 (H1h) |
| `t-a1-stony` | Stony Field, then Black Marsh | 43's `r` line, 7 (H1g); 43's init (H1h) |
| `t-a1-barracks` | Outer Cloister, Barracks by warp, `hunt` the Smith | 98 (H1g); 10 (H1h) |
| `t-a1-catacombs` | Catacombs 2 to 4 (the existing route) | 4, 26 (H1g) |
| `t-a2-town` | Lut Gholein | 41, 42, 81; states 5, 6 (H1d); 32 (H1h) |
| `t-a2-dryhills` | Dry Hills | 17, 18 (H1a); 23, 95 (H1g) |
| `t-a2-oasis` | Far Oasis, Maggot Lair 1 to 3 by warp | 15, 23, 43 (H1g); 38, 40, 66 (H1c, H1g) |
| `t-a2-lostcity` | Lost City, Valley of Snakes, Claw Viper Temple | 8, 16, 17, 18 (H1a); 95 (H1g) |
| `t-a2-canyon` | Canyon of the Magi, a Tal Rasha's Tomb | 7, 15, 39, 95 (H1g); 18 (H1a); 45, 47 (H1c, if the presets place them) |
| `t-a2-palace` | Palace Cellar 1 to 3, Arcane Sanctuary, `hunt` the Summoner | 8 (H1a); 11, 39 (H1g); 53 (H1c) |
| `t-a3-town` | Kurast Docks | 41; states 5, 6 (H1d); 32 (H1h); 56, 57 (H1g, if near the river) |
| `t-a3-spider` | Spider Forest, Spider Cavern | 24, 27 (H1a); 11, 15, 26 (H1g) |
| `t-a3-marsh` | Great Marsh, Flayer Jungle | 25, 27 (H1a); 23, 52, 65 (H1g) |
| `t-a3-kurast` | Lower Kurast, Bazaar, Upper Kurast | 17, 27 (H1a); 11, 23, 49 (H1g); 48 (H1h) |
| `t-a3-travincal` | Travincal, `hunt` the council; Durance 3, `hunt` Mephisto | 49 (H1g); 85, 50 (H1c) |
| `t-a4-steppes` | Outer Steppes and Plains of Despair from the town, `hunt` Izual | 72 (H1a); 71 (H1g); 68, 70 (H1h); 55 (H1c) |
| `t-a4-cotd` | City of the Damned, River of Flame, `hunt` Hephasto | 71, 98 (H1g); 68, 70, 73 (H1h) |
| `t-a4-chaos` | Chaos Sanctuary | 74 (H1a); 70 (H1h); 33 (H1g, if placed there) |
| `t-a5-foothills` | Bloody Foothills, Frigid Highlands | 113, 116, 120–123, 126, 129 (H1b); 14 (H1g) |
| `t-a5-plateau` | Arreat Plateau, Frozen Tundra | 115, 116, 120, 122 (H1b) |
| `t-a5-crystal` | Crystalline Passage, Glacial Trail | 118 (H1h); 114, 124 (H1g) |
| `t-a5-halls` | Halls of Pain, Halls of Vaught, `hunt` Nihlathak | 137 (H1b); 114 (H1g); 128 (H1c) |
| `t-a5-wsk` | Worldstone Keep 1 to 3 | 116, 117, 119, 122, 137 (H1b) |
| `nm-a5-crystal` | Nightmare: Crystalline Passage, Glacial Trail, Frozen River | 142 (H1a); 25 (H1a, `nmon`) |
| `nm-a5-wsk` | Nightmare: Worldstone Keep 2 | 142, 74 (H1a) |

That is 28 cases. With a rerun allowance of about 10 % and ADR-0028 item 2's two fresh repeats, the estimate is about
**33 kept cases, which is 237 statements at about 7 per case**. Of the 89 entries, 70 are aimed at by a case above.
The other 19 have no case yet:
- presets that Phase 1a has not yet placed: rows 46, 75, 76, 77, 80, 82, 83, 87, 92, 93, 94, 100, 136, and states 15
  and 16;
- rows 1, 78, 79 and state 11 (H1h), which the kept rev 4 and rev 6 logs reached: Phase 1a names the kept case that
  logged each one, to be rerun with rev 7.

The H1b rows 113, 121, 123, 126 and 129 are aimed at by `t-a5-foothills`, but on a guess: 121 and 129 have records with
no pool mark, and 113, 123 and 126 are siege rows. Phase 1a places all of these, or names an entry unreachable on stock
play (it then goes to d-none or d-owner, with its reason).

### Cases per launch

ADR-0028 governs:
- a case is what a record cites;
- at most 8 games or 40 minutes per launch;
- sharing is opt-in per batch, with a stated reason;
- a switch saved about 0.4 s on the rev 4 AI logger, so sharing is not chosen for speed unless the batch's own
  launch measurably costs more than a switch.

The tour's default is therefore **a fresh process per case**, which makes about 33 launches. It opts in to sharing only
if Phase 2 measures the rev 7 launch costing more than a switch (item 4's "slower logger"). The block-model checker
reads no carried state: its inputs are each decision's AID words and the logged returns. If the tour does share, the
record therefore names the checker as one that "does not read carried state", repeats two cases fresh (item 2), and
keeps `/players` out of every case. The same 33 cases then fit in 5 to 7 launches, one seed per act. Owner question
3 (c) counted launches, and on that count the two ways differ: about 40 claims per shared launch clears the threshold of
20, but about 7 per fresh launch does not. The threshold is not one of item 4's reasons to share, so the default stays
fresh and the count is owner question 2. The token cost below is per lane and the same either way.

### The logger

**Rev 7** of `tools/gdb/ai.py`, built in Phase 2 on rev 6 and keeping every rev 6 line. It is a rev 6 superset, so
H1a to H1d and H1g need nothing new. H1h does: it adds the words the rows forked on and the windows they lacked
(inventory rows 12, 113, 163, 168, 169, 195, 197, 200, 347, 348, 350, 466, 467, 500 and the H1h rows 35–39, 126–131,
176–178, 450–461):
- the return-address window of row 1's think 0x005B0CD0 (outside `THINK_LO`);
- a line at `MonAiInit`'s init call, for the inits of row 43 and state 11;
- the calls made inside `AiVileMotherSpawn` (row 68; `AI_NESTED` for that function only);
- the MonStats run and walk speed words of row 70;
- the region word `+0x2D4` that `AiTrapArrowKind` reads (rows 78, 79);
- the return of `StatListFindFlag` 0x00625760 (row 118);
- the return of `AiNearestPlayer` (rows 54 and 32);
- `MonPlayerBonus`'s block (row 10);
- row 32's script and home words;
- row 48's owner record;
- row 73's unread words.

Each one is read-only (harness-play rule 17). Phase 1a's boundary audit fixes the list.

### The slot

**One harness slot, never slot 0.** Plan 0067 Phase 2 holds slots 1 and 2 tonight. Plan 0065 Phase 2 runs back to
back with it on both slots (one port-4000 set-up), and its Phase 1 takes one slot.

The tour therefore uses **slot 2** (display `:9`, `workspace/wineprefix-2`) once plans 0067 Phase 2 and 0065 Phase 2
have released it. If plan 0065 Phase 1 then holds slot 1, the tour keeps slot 2. If a two-slot phase of another plan
needs slot 2 back, the tour stops at a case boundary: never inside a launch, and with no case left half-run. The
static Phase 1 needs no slot and may run tonight.

Every launch runs inside `systemd-run --user --scope -p MemoryMax=4G`.

## How the S1b checker is reused, and what it lacks

**Reused unchanged:**
- the engine: the call-by-call comparison, oracle feeding, forks, exit seed, `SITE`, `ARM`, `EDGE`, `NEXT`, `VALS` and
  the controls;
- the 29 models already written. They cover 18 of the 36 entries of H1g and H1h (row 43 is in both): rows 4, 15, 23,
  26, 43, 52, 54, 65, 68, 70, 78, 79, 95, 100, 114, 118, 124 and state 11. Row 1 needs only a `MODELS` row on R100's
  block function `m_r1`;
- `--logs`, `--rows` and `--out`;
- `tools/ai_resume_flip.py` for the H1g `r` lines (sentence H1's rule: 0 mismatches, at least 50 fork-free decisions,
  a call past the first, every two-way site failing alone).

The S1b batch rule (at least 30 fork-free decisions, every raised branch and store failing alone, `<` against `≤`
only with an equal pair) carries over unchanged.

**Lacks** (the work of Phases 1a to 1c and 2):
1. **Models for 71 entries, plus the notes row.**
   - H1a: 10.
   - H1b: 15.
   - H1c: 20.
   - H1d: 8.
   - H1g: 13 (rows 7, 11, 14, 33, 36, 39, 40, 49, 56, 57, 71, 93, 98), plus the *Reimplementation notes* row, which
     gets a model only if its claim is a block's.
   - H1h: 5 (rows 10, 32, 48, 73, and row 1's `MODELS` row).

   S1b wrote 29 models in one lane. Each new model is transcribed from the spec block at a pinned commit, never from
   `ai_resume.py` or a decompile, and has synthetic tests in `tools/test_ai_model_check.py`.
2. **`CONV` entries** for the callees the new blocks name that the table lacks, such as the state, spawn, summon,
   overlay and NPC helpers. Each entry needs its convention source, as S1b's `CONV` came from the emulation families and
   machinery § B.
3. **A boundary audit.** For each new block, each call is classed in one of three ways:
   - logged by rev 6, so it is compared;
   - needs rev 7, so it goes to the Phase 2 list;
   - not a boundary, so it forks.

   This sets which statements a session can raise at all. A block whose deciding calls are none of the logged
   boundaries goes back to (b) or (d-none) before any session.
4. **Rev 7 words as inputs.** `tools/ai.py` parses the new lines. Where a model now forks on one of these words, it
   takes the logged value instead, and the S1b fork stays as the fallback for rev 6 logs.
5. **The separation line (ADR-0028 item 7).** The tool prints per-branch `ARM` lines but not the number of distinct
   predicted outcomes per entry. A record that compares over many cases must give that number.
6. **A regression guard.** Over the 38 kept logs, `model-check.txt` must stay byte-identical for the 29 existing
   entries after each change (S1b's output, `workspace/logs/ai/sweep2-s1b/manifest.sha256`).

## Phases

Order: the static preparation (placement, models), then the logger and the first cases, then the tour, then the
settle. Phases 1b and 1c start after Phase 1a's review, because their models need its `CONV` entries, its boundary
class for each call and its regression check; they may run in parallel with each other (a `CONV` entry 1a missed is
added by the model phase, with its convention source). Phase 2 needs 1a and the models of the Act I entries, from
both 1b and 1c. Phase 3 needs 2 and the models of its acts.

### Phase 1a — Placement, seeds, cases and the checker's engine gaps
- **Owner skill:** reverser (static; no slot)
- **What:**
  - place each tour entry, and pick a seed per act whose pools hold the staged classes;
  - write the cases;
  - audit every block's calls against the logger;
  - close the checker's gaps 2, 3, 5 and 6.
- **Outputs:**
  - a placement tool, `tools/ai_tour.py`. Per entry it gives the records, the levels (pool by `monpool.py` on the
    chosen seed, presets from the DS1 preset lists, superuniques), the route and the difficulty. It also has a `seeds`
    command that scores candidate seeds per act;
  - the `t-*` and `nm-*` cases in `tools/ai_sessions.py`, with `tools/test_ai_sessions.py`;
  - the boundary audit as a table in the plan's log, which becomes the rev 7 list;
  - `ai_model_check.py`: `CONV` additions, the separation line, the regression check;
  - inventory rows that the audit or the placement shows unreachable, moved with their reason (to d-none, d-owner or
    (b)). This happens only after `lane/n66d` has merged, because that lane is editing the inventory files.
- **Done when:**
  - every one of the 237 rows has a case, or a move with its reason;
  - each staged pool's classes match `monpool.py`'s prediction for the chosen seed (a kept output);
  - every new block's call has a class (compared, rev 7, or fork);
  - the 38 kept logs reproduce S1b's `model-check.txt` byte for byte, apart from the added separation lines.
- **Review:** Tier B.

### Phase 1b — Models: H1a, H1b, H1d
- **Owner skill:** reverser (static; no slot)
- **What:** models for the 33 entries of H1a, H1b and H1d, transcribed from the catalogue blocks.
- **Outputs:** `tools/ai_model_check.py` models with `MODELS` rows, and `tools/test_ai_model_check.py` cases.
- **Done when:**
  - each entry is modelled with its controls, or named with the reason it cannot be modelled (returned to its row);
  - each model passes its synthetic tests, which include one per branch that fails when the branch is reversed;
  - the 38 kept logs give 0 decisions for these entries and leave the S1b output unchanged.
- **Review:** Tier B.

### Phase 1c — Models: H1c, H1g, H1h
- **Owner skill:** reverser (static; no slot)
- **What:** the same work for the 38 unmodelled entries of H1c (20), H1g (13) and H1h (5), and the notes row of H1g.
- **Outputs and Done when:** as Phase 1b. The H1h models also take their rev 7 word as an input, and fall back to a fork
  without it.
- **Review:** Tier B.

### Phase 2 — Logger rev 7, the pilot and Act I
- **Owner skill:** reverser (harness; slot 2 once free, never slot 0)
- **What:**
  - build rev 7 from Phase 1a's list, teach `tools/ai.py` its lines, and feed its words to the H1h models of
    `ai_model_check.py` (gap 4);
  - run a regression case and measure launch against switch;
  - run the Act I and Rogue Encampment cases with committed predictions.
- **Outputs:**
  - `tools/gdb/ai.py` rev 7, with `tools/ai.py` and `tools/test_ai.py`;
  - `ai_model_check.py` reading the rev 7 words, with a synthetic test per word in `tools/test_ai_model_check.py`;
  - **run:<date>-ai-tour-1** in [findings/ai/experiments.md](../findings/ai/experiments.md). It records the
    predictions, committed before the first kept log (decisions expected per entry from the chosen pools), the case
    list with process and position (ADR-0028 item 1), the separation lines, and `manifest.sha256`;
  - the checker's outputs over the new logs.
- **Done when:**
  - every log says `AI logger armed rev 7`;
  - each H1h model takes its rev 7 word from a rev 7 log, and the 38 kept rev 4 and rev 6 logs still give S1b's
    `model-check.txt` byte for byte, apart from the separation lines (the fork fallback);
  - a rerun of a kept rev 6 case (`a2-oasis`, seed 5201) shows 0 first-boundary mismatches, and its rev 6 lines are
    unchanged in form;
  - launch and switch are measured, and the sharing decision is recorded with ADR-0028 item 4's reason, or "fresh";
  - the Act I cases are kept with 0 mismatches, or each mismatch is named as a contradiction (`ai_model_check.py` and
    `ai_resume_flip.py`).
- **Review:** Tier B.

### Phase 3 — The tour: Acts II to V and Nightmare
- **Owner skill:** reverser (harness; the same slot)
- **What:** the remaining cases of Phase 1a's table, in two lanes.
  - **3a:** Acts II and III, with the Lut Gholein and Kurast Docks cases.
  - **3b:** Acts IV and V, and the Nightmare cases.

  Each lane runs the checkers over its own logs.
- **Outputs:** run:<date>-ai-tour-2 and -3, as in Phase 2.
- **Done when:**
  - each case of the lane is kept, or named with its reason (not reached, failed, rerun fresh);
  - 0 mismatches, or each one named as a contradiction and filed in the backlog for the spec;
  - for each entry, the decision count, the fork-free count and the separation line are in the record.
- **Review:** Tier B per lane, with the audit rule.

### Phase 4 — Settle the 237 rows
- **Owner skill:** reverser (static; no slot)
- **What:** apply the S1b rule (blocks) and sentence H1's rule (`r` lines) over the tour's logs, together with the 38
  kept ones, and update the inventory.
- **Outputs:**
  - an addendum to run:<date>-ai-tour-3 with the check over all tour logs (`--logs`) and its manifest;
  - the inventory rows of H1a to H1d, H1g and H1h, each one raised, raised in part (with the half that stays), or kept
    `[I]` with its reason;
  - § 1, § 3 and § 4 of [the inventory README](0066-inventory/README.md), with the batch statuses;
  - a **ready list** for plan 0066 Phase 3 (catalogue line numbers at a pinned commit), in this plan's log and in
    plan 0066's.
- **Done when:**
  - every one of the 237 rows has its outcome;
  - the README totals match the files (gate W7);
  - the ready list names each line with its run, entry and the paths raised.
- **Review:** Tier B, with the audit rule. The re-tag is plan 0066 Phase 3's monsters/ai cluster, reviewed at Tier A
  there, which closes this plan with it.

## Cost estimate

The ledger means come from `python3 -I tools/metrics.py summary` on 2026-11-10 (680 runs):

| Kind | Mean tokens |
|---|---|
| reverser-static | 352 991 |
| reverser-harness | 341 596 |
| architect-check (Tier B) | 82 013 |
| architect-review (Tier A) | 164 178 |

| Item | Lanes | Estimate |
|---|---|---|
| Phase 1a, 1b, 1c (static) and their checks | 3 + 3 | 3 × (353k + 82k) ≈ 1.31M |
| Phase 2, 3a, 3b (harness) and their checks | 3 + 3 | 3 × (342k + 82k) ≈ 1.27M |
| Phase 4 (static) and its check | 1 + 1 | 353k + 82k ≈ 0.44M |
| This plan's Tier A review | 1 | ≈ 0.16M |
| Audits of the 7 Tier B checks (every fifth, expected 7 / 5) | ≈ 1.4 | ≈ 1.4 × 164k ≈ 0.23M |
| **Total** | 7 lanes, about 9.4 reviews | **≈ 3.4M** |

These are estimates from the means, not measurements. On the 237 statements that is about 14k tokens each, on the base
plan 0066 used (statements in scope): between Phase 1's 10k and Phase 2's 19k per claim. On the share that S1b raised
whole or in part (43 of 61, 70 %), it is about 20k per raised statement.

Question 3 (c)'s figure of about 1.3M (3 harness lanes and their checks, about 6k per statement) assumed the checker
could take the tour's logs as they are. It cannot: 71 of the tour's 89 catalogue entries have no model, H1h needs rev
7, and the seeds and placements are not yet kept. The harness part is still about 1.27M; the rest is the static
preparation (Phases 1a to 1c, about 1.31M), the settle (about 0.44M) and the reviews and audits (about 0.39M).

Slot time is about 33 cases of 4 to 9 minutes each (130 to 300 s of stage, about 150 s of start, longer for descents
and hunts): **about 3 to 5 hours on one slot** over three lanes.

## Open questions

- **Owner question 1, the size.** The tour costs about 3.4M, against question 3 (c)'s 1.3M. Question 3 (c) was
  recommended at "about Phase 1's cost per claim"; at about 14k per statement it now sits between Phase 1's 10k and
  Phase 2's 19k (§ Cost estimate gives the split):
  - (a) run the plan as drafted;
  - (b) drop H1c (59 statements, 20 entries, most of them bosses, traps and spawners that need `hunt` routes and preset
    placement): a Phase 1c of 18 models instead of 38 and five fewer cases, about 3.1M for 178 statements;
  - (c) defer the whole tour with plan 0066's other harness rows.

  The architect recommends **(a)**. The extra cost buys the models, and they are durable: every later AI run checks its
  blocks with them, the way S1b's models served this plan. H1c also holds the bosses that no kept log reaches at all.
- **Owner question 2, the threshold count.** Fresh processes are the default (ADR-0028 item 4), which gives about 33
  launches at about 7 claims each, below question 2's 20; sharing (5 to 7 launches, about 40 each) is open only if
  Phase 2 measures the rev 7 launch costing more than a switch. Options:
  - (a) read question 3 (c)'s answer as approving this tour by name, so the claims-per-launch count does not gate it;
  - (b) run only if Phase 2's measurement opens sharing, and otherwise stop after Phase 2.

  The architect recommends **(a)**: the owner chose the tour, not a launch count, and sharing for the count alone would
  need an ADR-0028 amendment. Phase 2 still measures and records its choice under item 4.
- **Preset rows** (76, 77, 80, 82, 83, 87, 92, 93, 94, 100, 136; states 15, 16; the siege rows 113, 121, 123, 126,
  129). Inventory helper `ai1` read their act and level from the monster names, not from `Levels` or the DS1 lists.
  Phase 1a places them or moves them (row 103's `invisopet` precedent).
- **Plan 0066 Phase 3 order.** The monsters/ai cluster could be re-tagged once for the S1 batches now and again after
  this plan, or once at the end. Plan 0066 Phase 3 decides; this plan only hands over its ready list.
- **The rev 7 list is Phase 1a's.** The words above are the inventory's routes, and the audit may add or drop some.
  A word whose read would need a write, or a breakpoint inside a pending callee, goes back to its row as (d-none) or a
  backlog entry, not into the logger.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

### 2026-11-10 — Draft (architect, `lane/n69a`)

- **Drafted** on the owner's answer to plan 0066 question 3 (c), after S1b's acceptance. The scope was recounted from
  the inventory at `4fb8b55f`: 237 statements, not about 214. The levels and the entries the checker models were read
  for this draft by scratch scripts, over `tools/ai_survey.py`'s tables and `ai_model_check.py`'s `MODELS`; Phase 1a
  regenerates them with a kept tool.
- **Judgment calls for the review:**
  1. The tour runs fresh processes by default, under ADR-0028 item 4, although question 3 (c) counted launches. The
     claims-per-launch figure is given both ways.
  2. The cost is about 2.5 times question 3 (c)'s figure, because of the missing models and rev 7. This is now owner
     question 1.
  3. Slot 2, after plans 0067 Phase 2 and 0065 Phase 2.
  4. Phase 4 writes 0066's inventory files, and Phase 1a does so only after `lane/n66d` has merged.
- **Next:** the Tier A review of this plan, then the owner's approval. No phase has started.

### 2026-11-10 — Tier A review (architect, Mode 3)

- **Verdict: accept with fixes** (8 fixes: overclaim 2, misread 1, miscount 1, omission 4). Checked: the 237 statements
  and the per-batch entry lists recounted from the inventory at `4fb8b55f` (38, 45, 59, 16, 44, 35; 10, 15, 20, 8, 24 and
  the notes row, 13 entries); the 29 models and the 18 tour entries they cover against `MODELS` in
  `tools/ai_model_check.py`; the 71 unmodelled entries; gaps 2 to 6 against the tool (no distinct-outcome count, no
  regression mode, `THINK_LO` without 0x005B0CD0); the ledger means (`tools/metrics.py summary`, 680 runs); the slot
  rule against plans 0065 and 0067; ADR-0028 items 2, 4 and 7. Every phase has a checkable Done-when and a tier. The
  research-map edit states the current state; the index row is updated for this review.
- **Fixes:**
  1. (overclaim) "clears the 20-per-session threshold either way": fresh launches give about 7 claims each. Stated, and
     the count made owner question 2 (the *Sharing* open question folded into it).
  2. (overclaim) "sharing is never chosen for speed": ADR-0028 item 4 allows it on a measured launch cost; reworded.
  3. (misread) the per-claim comparison set 19k per raised statement against plan 0066's 19k per statement in scope;
     now on one base (about 14k per statement, between Phase 1's 10k and Phase 2's 19k).
  4. (miscount) the no-case list missed rows 1, 78, 79, state 11 (H1h) and presets 46, 75, and listed the siege and
     no-pool rows that `t-a5-foothills` aims at; 70 of 89 entries aimed at, 19 not, recounted.
  5. (omission) the cost left out the audit rule's expected Tier A audits (about 0.23M): total about 3.4M; option (b)
     about 3.1M.
  6. (omission) owner question 1 did not say that question 3 (c)'s per-claim premise no longer holds, nor where the extra
     2.1M goes; the split is in § Cost estimate and the question cites it.
  7. (omission) the order let 1b and 1c start without 1a's `CONV`, boundary classes and regression check, and let Phase 2
     start without the Act I models; both stated.
  8. (omission) gap 4's checker side (the H1h models reading the rev 7 words) had no phase output; added to Phase 2's
     outputs and Done-when, with the fork fallback held byte-identical on the 38 kept logs.
- **Owner questions as they stand:** 1 (size: (a) as drafted, about 3.4M; (b) without H1c, about 3.1M; (c) defer;
  recommended (a)); 2 (threshold count: (a) the tour approved by name, the count does not gate it; (b) only if sharing
  opens; recommended (a)).
