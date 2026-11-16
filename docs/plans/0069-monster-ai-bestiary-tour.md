# 0069 — Monster AI bestiary tour: the catalogue's harness rows of plan 0066

> **Status:** approved (2026-11-10, by the owner, as recommended: question 1 (a), question 2 (a)); Phase 1a done (`lane/n69a`, Tier B check: accept with fixes, 3; merged); Phase 1b done (`lane/n69b`, 29 of 29 entries modelled; Tier B check: accept, 0 fixes; merged); Phase 1c done pending merge (`lane/n69c`, 2026-11-15; 31 of 31 entries and the notes row modelled; Tier B check: accept with fixes, 3); Phase 2 done (`lane/n69d`, 2026-11-15; 12 Act I cases kept, 0 mismatches; Tier B check: accept with fixes, 1; merged); Phase 3a done pending review (`lane/n69e`, 2026-11-16; 17 Act II and III cases kept, 0 mismatches)
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
  - every one of the 241 rows (237 at the draft; 241 after 0066 S1d) has a case, or a move with its reason;
  - each staged pool's classes match `monpool.py`'s prediction for the chosen seed (a kept output);
  - every new block's call has a class (compared, rev 7, or fork);
  - the 38 kept logs reproduce S1b's `model-check.txt` byte for byte, apart from the added separation lines.
- **Review:** Tier B.

### Phase 1b — Models: H1a, H1b, H1d
- **Owner skill:** reverser (static; no slot)
- **What:** models for the 33 entries of H1a, H1b and H1d (29 after Phase 1a's moves to H1p: H1a 10, H1b 13, H1d 6),
  transcribed from the catalogue blocks.
- **Outputs:** `tools/ai_model_check.py` models with `MODELS` rows, and `tools/test_ai_model_check.py` cases.
- **Done when:**
  - each entry is modelled with its controls, or named with the reason it cannot be modelled (returned to its row);
  - each model passes its synthetic tests, which include one per branch that fails when the branch is reversed;
  - the 38 kept logs give 0 decisions for these entries and leave the S1b output unchanged.
- **Review:** Tier B.

### Phase 1c — Models: H1c, H1g, H1h
- **Owner skill:** reverser (static; no slot)
- **What:** the same work for the 38 unmodelled entries of H1c (20), H1g (13) and H1h (5), and the notes row of H1g
  (H1c is 13 after Phase 1a's moves to H1p, so 31 entries).
- **Outputs and Done when:** as Phase 1b, except that its third item reads: the 38 kept logs give 0 mismatches for these
  entries and leave the S1b output unchanged, with the decision counts per entry reported (Phase 1b's entries had no
  decisions in the logs; these hold some, which the check compares). The H1h models also take their rev 7 word as an
  input, and fall back to a fork without it. [Wording fixed at the `lane/n69c` Tier B check, 2026-11-15.]
- **Review:** Tier B.

### Phase 2 — Logger rev 7, the pilot and Act I
- **Owner skill:** reverser (harness; slot 2 once free, never slot 0)
- **What:**
  - build rev 7 from Phase 1a's list, teach `tools/ai.py` its lines, and feed its words to the H1h models of
    `ai_model_check.py` (gap 4);
  - give R54 (step 2) and R58 (step 3) `unit_set_event`'s `Unit+0xC4 |= 0x400` before their first Phase 2 log
    (Phase 1c modelled it for R32 only; a log reaching either arm would otherwise show a `c4` mismatch);
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

### 2026-11-10 — Scope note (orchestrator, at the merge of 0066 S1c and S1d)

- Plan 0066's batch S1d (`lane/n66d`) moved catalogue rows 13, 349, 460 and 468 (a-logs → b) into H1h, which now holds
  39 statements. The tour's scope is therefore **241** statements, not the 237 counted above at `4fb8b55f`. The
  figures above stay as drafted; Phase 1a recounts the scope from the inventory at its start, and the cost scales by
  about 2 %.

### 2026-11-10 — Owner decision

- **Approved as recommended:** question 1 (a), the tour as drafted (about 3.4M tokens; scope 241 after 0066 S1d);
  question 2 (a), the answer to plan 0066's question 3 (c) approves the tour by name, so the per-launch count does not
  gate it. Not started: work across the project is paused by the owner; Phase 1a starts when the owner resumes.

### 2026-11-15 — Phase 1a: placement, seeds, cases, the boundary audit and the checker gaps (reverser, `lane/n69a`)

Static; no slot, no game. `main` `f56ab708` merged (plan 0066 S1e and S2b in). Kept outputs in `workspace/logs/n69a/`
(`manifest.sha256`, 12 lines, passes `sha256sum -c` from that directory): `entries.txt`, `place.txt`, `seeds.txt`,
`pools.txt`, `rows.txt`, `routes.txt`, `cases.txt`, `audit.txt`, `conv.txt`, `regress.txt`,
`regress-model-check.txt`, `test-output.txt`. Tools: `tools/ai_tour.py` (new), `tools/test_ai_tour.py` (new),
`tools/ai_sessions.py` and `tools/test_ai_sessions.py` (the tour cases), `tools/ai_model_check.py` revision 3 and
`tools/test_ai_model_check.py`.

- **Scope, recounted** (`ai_tour.py entries`, the inventory at `f56ab708`): **241 statements, 241 rows, 90 entries**
  (89 catalogue entries and the *Reimplementation notes* row 517): H1a 38, H1b 45, H1c 59, H1d 16, H1g 44, H1h 39, as
  the scope note of 2026-11-10 said.
- **Placement** (`ai_tour.py place`). Per entry: its records (`ai_survey.py`'s tables); the Levels `mon` (Normal) and
  `nmon` levels of its records, with the waypoint (tab, row) of each; every DS1 preset unit of a record from the
  LvlPrest-named DS1s, through MonPreset to MonStats, a superunique (kind 2) or a MonPlace row the preset spawn turns into a
  class (4 `navi`, 5 `bloodraven`, 8 `maggotqueen1`, 10/11 `tentaclehead1`, from MonPlace § Interpretation notes), with
  the levels of its LvlPrest record (LevelId, or the levels of the level types whose files cover the DS1s, `tools/ds1.py`'s
  scoring); the MonStats `spawn`/`minion1`/`minion2` chains (maggot egg and larva, the tentacles); and a short table
  `CODE` of creators the findings name, each with its anchor (`navi` at the Blood Moor centre preset, drlg/0004; `rogue2` the
  Act I wanderer, monsters/spawn § K; the object trap monsters 326, 329, 330, 369, objects/0001; `evilhut`, monsters/0002
  spawn 42; Nihlathak, `A5Q3_NihlathakBossSpawn`; the hireling states 5 and 6, S5a/S6a; states 15 and 16, S15a/S16a; the
  kept cases that logged rows 1, 78, 79 and state 11).
  - **79 entries are placed** and aimed at by at least one case. **11 are not:** rows 46, 47, 62, 75, 76, 81, 82, 83, 87,
    113 and 121. For their classes `place.txt` shows no reach mark (`ai_survey.py`: no Levels `mon`/`nmon`/`umon` slot, no
    superunique, no Skills `summon` or PetType class, no hireling), no DS1 unit (every `.ds1` file under the tiles, the ones
    LvlPrest does not name listed with Def −1), no MonPlace row and no MonStats `spawn`/`minion` cell, and no finding names a
    creator. A code creator is not ruled out (the class-id
    immediates were not read), so the 30 rows go to **(b), batch H1p, out of this plan**, not to d-none (below).
- **Seeds** (`ai_tour.py seeds --group G --first 6901 --count 3000`, `seeds.txt`). One map seed per seed group (an act in
  Normal; Act V in Nightmare); the score is the number of the group's pool-aimed entries that some (case, level) of the group
  holds on the seed (`tools/monpool.py`'s model: the game seed's first draw, expansion), then the number of (case, level,
  entry) pairs held, then the lowest seed. Chosen: **Act I 7159** (7 of 7 entries, 13 pairs), **Act II 8723** (11 of 11, 17),
  **Act III 7842** (11 of 11, 19), **Act IV 7055** (8 of 8, 9), **Act V 6908** (10 of 10, 19), **Nightmare Act V 6927** (3 of
  3, 4). The four H1h reruns keep their kept cases' seeds: 5803 (`a1-stony`), 5602 (`a3-flayer-p8`), 5401
  (`s-barb-flayer`), 5802 (`s-necro-curse`).
- **The pools on those seeds** (`ai_tour.py pools`, `pools.txt`): every staged level's predicted pool, with the aimed
  entries it holds; **0 entries missed** in any group. A case's level may not hold every entry it lists (a pool keeps
  `NumMon` classes, so Cold Plains cannot hold five); the entry is then held by another case of its group, and the case table
  keeps the aim so a reader sees where else to look. This is the kept prediction the Done-when names; the comparison with the
  game's own pools is Phase 2's (the AID lines' classes of each case, or a `mon-pool.gdb` line beside the AI logger).
- **The cases: 45** (`ai_tour.py cases`, `TOUR` in the tool; `ai_sessions.py` builds them, each pinned to its group's seed,
  fresh by default). 41 tour cases (39 Normal, 2 Nightmare) and 4 H1h reruns. Route steps: a waypoint and Nova sweep, LvlWarp
  descents with `--descend-to` (checked against Levels `Vis`/`Warp`, `routes.txt`, 0 bad), a border walk (`explore
  --any-level`) where the next level is an open edge (Burial Grounds, Barracks, Valley of Snakes, the Outer Steppes,
  Chaos Sanctuary, the Bloody Foothills, the Blood Moor), a `hunt` with the Nova radius at 1 for a boss, a town walk (no
  Nova), a stay case (`t-a4-town`, whose stage gate passes only while the player stays in the start level, `STAY`), and a
  loot walk (`explore --loot`) for the object traps. Tests: `tools/test_ai_sessions.py` (21, 8 new), `tools/test_ai_tour.py`
  (9).

| Case | Diff | Seed | Route | Pool aims (level: entries) | All aims |
|---|---|---:|---|---|---|
| `t-a1-town` | N | 7159 | wp 1,1; border walk (40 hops) | – | R32, S5, S6, R58 |
| `t-a1-cold` | N | 7159 | wp 1,2, sweep 180 s; border walk (40 hops); hunt 267 | 3: R7, R36, R10 | R7, R36, R10, R59, R60, NOTES |
| `t-a1-stony` | N | 7159 | wp 1,3, sweep 200 s | 4: R43 | R43, R60 |
| `t-a1-darkwood` | N | 7159 | wp 1,4, sweep 200 s | 5: R14, R36, R10 | R14, R36, R10, R60 |
| `t-a1-marsh` | N | 7159 | wp 1,5, sweep 200 s | 6: R7, R43 | R7, R43, NOTES |
| `t-a1-barracks` | N | 7159 | wp 1,6, sweep 150 s; border walk (40 hops); hunt 402 | 27: R14, R10 | R14, R10, R98, R7 |
| `t-a1-catacombs` | N | 7159 | wp 1,9, sweep 200 s | 35: R4, R26 | R4, R26 |
| `t-h1h-a1-stony` | N | 5803 | rerun of `a1-stony` | – | R1 |
| `t-h1h-a3-flayer-p8` | N | 5602 | rerun of `a3-flayer-p8` | – | R78 |
| `t-h1h-s-barb-flayer` | N | 5401 | rerun of `s-barb-flayer` | – | R79 |
| `t-h1h-s-necro-curse` | N | 5802 | rerun of `s-necro-curse` | – | S11 |
| `t-a2-town` | N | 8723 | wp 2,1, walk | – | R32, R41, R42, S5, S6 |
| `t-a2-dryhills` | N | 8723 | wp 2,3, sweep 200 s | 42: R17, R18, R23, R95 | R17, R18, R23, R95 |
| `t-a2-oasis` | N | 8723 | wp 2,5, sweep 150 s; warp 47 to 62; warp 49 to 63; warp 49 to 64; hunt 284 | 43: R15, R23, R43 | R15, R23, R43, R38, R40, R66 |
| `t-a2-lostcity` | N | 8723 | wp 2,6, sweep 150 s; border walk (40 hops) | 44: R8, R17, R18, R95; 45: R16 | R8, R17, R18, R95, R16 |
| `t-a2-canyon` | N | 8723 | wp 2,9, sweep 150 s; warp 38 to 66 | 46: R7, R15, R18, R95 | R7, R15, R18, R95, R45, R94 |
| `t-a2-palace` | N | 8723 | wp 2,7, sweep 200 s | 52: R8, R11, R39 | R8, R11, R39 |
| `t-a2-arcane` | N | 8723 | wp 2,8, sweep 150 s; hunt 250 | – | R93, R53 |
| `t-a2-halls` | N | 8723 | wp 2,4, sweep 120 s; loot (60 hops) | 57: R95 | R95, R77, R92 |
| `t-a3-town` | N | 7842 | wp 3,1, walk | – | R32, R41, S5, S6 |
| `t-a3-spider` | N | 7842 | wp 3,2, sweep 200 s | 76: R24, R27, R11 | R24, R27, R11, R56, R57 |
| `t-a3-marsh` | N | 7842 | wp 3,3, sweep 200 s | 77: R25, R27, R52, R65 | R25, R27, R52, R65, R56, R57 |
| `t-a3-flayer` | N | 7842 | wp 3,4, sweep 200 s | 78: R23, R52, R65 | R23, R52, R65, R56, R57 |
| `t-a3-lower` | N | 7842 | wp 3,5, sweep 150 s; loot (60 hops) | 79: R11, R17, R23, R48 | R11, R17, R23, R48, R77, R80, R92 |
| `t-a3-bazaar` | N | 7842 | wp 3,6, sweep 200 s | 80: R27, R48, R49 | R27, R48, R49 |
| `t-a3-upper` | N | 7842 | wp 3,7, sweep 200 s | 81: R23, R27, R48, R49 | R23, R27, R48, R49 |
| `t-a3-travincal` | N | 7842 | wp 3,8, sweep 150 s; hunt 345 | 83: R49 | R49, R85 |
| `t-a3-durance` | N | 7842 | wp 3,9, sweep 100 s; warp 67,68 to 102; hunt 242 | 101: R39 | R39, R50, R85 |
| `t-a4-town` | N | 7055 | stay in town, walk | – | R32, R54 |
| `t-a4-steppes` | N | 7055 | border walk (60 hops); hunt 256 | 104: R72 | R72, R55 |
| `t-a4-cotd` | N | 7055 | wp 4,2, sweep 240 s | 106: R4, R68, R70, R71, R73 | R4, R68, R70, R71, R73 |
| `t-a4-river` | N | 7055 | wp 4,3, sweep 200 s; hunt 409 | 107: R39, R68, R70, R71, R73 | R39, R68, R70, R71, R73, R33, R98, R100 |
| `t-a4-chaos` | N | 7055 | wp 4,3, sweep 30 s; border walk (60 hops) | 108: R74, R70 | R74, R70 |
| `t-a5-town` | N | 6908 | wp 5,1, walk | – | R32, S5, S6 |
| `t-a5-foothills` | N | 6908 | wp 5,1; border walk (80 hops) | 110: R116, R120, R122 | R116, R120, R122, R123, R126, R129, S15, S16 |
| `t-a5-highlands` | N | 6908 | wp 5,2, sweep 200 s | 111: R115, R122 | R115, R122, S16, R129, R123, R126 |
| `t-a5-plateau` | N | 6908 | wp 5,3, sweep 200 s | 112: R116, R120 | R116, R120, S15, R123, R126 |
| `t-a5-crystal` | N | 6908 | wp 5,4, sweep 150 s; loot (60 hops) | 113: R124, R118 | R124, R118, R80 |
| `t-a5-glacial` | N | 6908 | wp 5,5, sweep 200 s | 115: R114, R124 | R114, R124 |
| `t-a5-tundra` | N | 6908 | wp 5,7, sweep 200 s | 117: R115, R122 | R115, R122, S16, R123, R126 |
| `t-a5-halls` | N | 6908 | wp 5,6, sweep 150 s; warp 77 to 124; hunt 526 | 123: R137, R114 | R137, R114, R128 |
| `t-a5-wsk1` | N | 6908 | wp 5,9, sweep 100 s; warp 81 to 128 | 128: R119, R137 | R119, R137, R136, S15 |
| `t-a5-wsk` | N | 6908 | wp 5,9, sweep 150 s; warp 82 to 130 | 129: R116, R117; 130: R137 | R116, R117, R137, S15, R136 |
| `nm-a5-crystal` | NM | 6927 | wp 5,4, sweep 200 s | 113: R142 | R142 |
| `nm-a5-wsk` | NM | 6927 | wp 5,9, sweep 150 s; warp 82 to 130 | 129: R142, R25; 130: R74 | R142, R25, R74 |
- **Every row has a case or a move** (`ai_tour.py rows`, `rows.txt`): **211 statements cased, 30 moved, 0 unplaced.**
- **The boundary audit** (`ai_tour.py audit`, `audit.txt`). For each entry's think, init and alt (the words of
  `g_MonAiTable` and the state rows in the pinned image), every call instruction (objdump, from the function's start to the
  next known function start in `re/symbols.csv` or the AI tables; a helper inside the logger's windows is followed and its
  calls listed under it) is classed: **compared** (a boundary of `tools/gdb/ai.py` `BND`, called from inside `THINK_LO`, with
  its return site in `ai-retsites.txt`: rev 6 logs it with its result), **rev 7** (a word or window the plan's rev 7 list
  names, or a boundary the windows miss), **run** (not a boundary, executed by the model: `ai_resume.EXEC` and the window
  helpers) or **fork** (not a boundary and not executed: the model forks on it). Totals over the 89 entries: **980 compared,
  9 rev 7, 215 run, 166 fork**. One entry has no compared call: **R1** (its think 0x005B0CD0 is outside the windows), which
  is H1h's rev 7 window. No other entry needs to go back to (b) or d-none for want of a compared call.

| Entry | Think | Model | Compared | Rev 7 | Run | Fork | Rev 7 calls; fork callees (first six) |
|---|---|---|---:|---:|---:|---:|---|
| R1 | `0x005B0CD0` | yes | 0 | 2 | 0 | 0 | rev 7: UnitGetRoom, MonAiIdle |
| R4 | `0x005EFF50` | yes | 12 | 0 | 3 | 0 | – |
| R7 | `0x005EFB80` | no | 7 | 0 | 0 | 0 | – |
| R8 | `0x005F0700` | no | 14 | 0 | 1 | 0 | – |
| R10 | `0x005F0B00` | no | 9 | 1 | 0 | 0 | rev 7: MonPlayerBonus |
| R11 | `0x005F0CD0` | no | 22 | 0 | 6 | 2 | fork: UnitSetStat |
| R14 | `0x005F1140` | no | 11 | 0 | 0 | 0 | – |
| R15 | `0x005F1800` | yes | 13 | 0 | 3 | 8 | fork: MonAiDelayEarlier, AiCtlParamGet |
| R16 | `0x005F1B60` | no | 9 | 0 | 2 | 0 | – |
| R142 | `0x005F1DE0` | no | 10 | 0 | 2 | 0 | – |
| R17 | `0x005F20A0` | no | 8 | 0 | 0 | 0 | – |
| R18 | `0x005F22B0` | no | 9 | 0 | 0 | 0 | – |
| R23 | `0x005F3170` | yes | 33 | 0 | 10 | 7 | fork: MonAiMoveToUnitDist, UNIT_GetSizeX, FreeNearFallback |
| R24 | `0x005F3730` | no | 10 | 0 | 0 | 0 | – |
| R25 | `0x005F39B0` | no | 23 | 0 | 17 | 16 | fork: 00681ef0, RoomUnitSearchInit, 0065ac70, AiCtlSetVar, 0065aa00, MonAiMoveToPointNoStop … |
| R26 | `0x005F4510` | yes | 17 | 0 | 4 | 0 | – |
| R27 | `0x005F4850` | no | 11 | 0 | 3 | 0 | – |
| R33 | `0x005F56D0` | no | 2 | 0 | 4 | 0 | – |
| R36 | `0x005F5D50` | no | 13 | 0 | 2 | 0 | – |
| R38 | `0x005F6220` | no | 4 | 0 | 0 | 0 | – |
| R39 | `0x005F6340` | no | 6 | 0 | 0 | 0 | – |
| R40 | `0x005F6530` | no | 5 | 0 | 0 | 0 | – |
| R43 | `0x005F6650` | yes | 6 | 0 | 2 | 0 | – |
| R45 | `0x005F6A10` | no | 6 | 0 | 2 | 0 | – |
| R46 | `0x005F6B70` | no | 8 | 0 | 1 | 0 | – |
| R47 | `0x005F6CA0` | no | 5 | 0 | 0 | 0 | – |
| R48 | `0x005F6E60` | no | 22 | 1 | 3 | 2 | rev 7: MonsterOwnerRef; fork: DRLG_ActFromLevelId, QUESTRECORD_GetState |
| R49 | `0x005F72D0` | no | 12 | 0 | 7 | 0 | – |
| R52 | `0x005F8260` | yes | 24 | 0 | 8 | 0 | – |
| R56 | `0x005F8F80` | no | 12 | 0 | 4 | 0 | – |
| R57 | `0x005F9270` | no | 8 | 0 | 1 | 0 | – |
| R65 | `0x005F9A80` | yes | 18 | 0 | 0 | 0 | – |
| R66 | `0x005F9CF0` | no | 8 | 0 | 2 | 0 | – |
| R68 | `0x005FA010` | yes | 10 | 0 | 0 | 0 | – |
| R70 | `0x005FA380` | yes | 14 | 0 | 2 | 0 | – |
| R71 | `0x005FA710` | no | 22 | 0 | 5 | 0 | – |
| R72 | `0x005FAA90` | no | 4 | 0 | 0 | 0 | – |
| R73 | `0x005FAB80` | no | 10 | 0 | 1 | 0 | – |
| R74 | `0x005FAF00` | no | 14 | 0 | 2 | 0 | – |
| R75 | `0x005FB2A0` | no | 8 | 0 | 0 | 0 | – |
| R76 | `0x005FB410` | no | 11 | 0 | 0 | 0 | – |
| R77 | `0x005FB5B0` | no | 3 | 0 | 0 | 0 | – |
| R78 | `0x005FB6C0` | yes | 4 | 1 | 0 | 2 | rev 7: AiTrapArrowKind; fork: UnitGetPos |
| R79 | `0x005FB7E0` | yes | 4 | 1 | 0 | 2 | rev 7: AiTrapArrowKind; fork: UnitGetPos |
| R80 | `0x005FB900` | no | 3 | 0 | 0 | 0 | – |
| R87 | `0x005FBA60` | no | 3 | 0 | 0 | 0 | – |
| R92 | `0x005FB9B0` | no | 3 | 0 | 0 | 0 | – |
| S5 | `0x005E7AC0` | no | 9 | 0 | 2 | 0 | – |
| S6 | `0x005E7C10` | no | 9 | 0 | 1 | 0 | – |
| R50 | `0x005F78B0` | no | 24 | 0 | 2 | 0 | – |
| R53 | `0x005F85C0` | no | 12 | 0 | 2 | 0 | – |
| R55 | `0x005F89B0` | no | 8 | 0 | 4 | 0 | – |
| R59 | `0x005E6320` | no | 32 | 0 | 10 | 0 | – |
| R82 | `0x005E0160` | no | 6 | 0 | 0 | 0 | – |
| R83 | `0x005E0260` | no | 5 | 0 | 2 | 0 | – |
| R85 | `0x005E0490` | no | 16 | 0 | 6 | 0 | – |
| R93 | `0x005E0F60` | no | 3 | 0 | 0 | 0 | – |
| R94 | `0x005E0980` | no | 11 | 0 | 6 | 0 | – |
| R95 | `0x005E1080` | yes | 7 | 0 | 0 | 0 | – |
| R98 | `0x005E3890` | no | 4 | 0 | 0 | 0 | – |
| R113 | `0x005E1860` | no | 6 | 0 | 0 | 0 | – |
| R114 | `0x005E1540` | yes | 7 | 0 | 1 | 0 | – |
| R115 | `0x005E1900` | no | 13 | 0 | 1 | 0 | – |
| R116 | `0x005E1B60` | no | 11 | 0 | 0 | 0 | – |
| R117 | `0x005E1D30` | no | 3 | 0 | 0 | 0 | – |
| R118 | `0x005E1E00` | yes | 14 | 1 | 1 | 0 | rev 7: StatListFindFlag |
| R119 | `0x005E2120` | no | 19 | 0 | 1 | 1 | fork: StatListFindFlag |
| R120 | `0x005E27A0` | no | 13 | 0 | 2 | 5 | fork: 00587900, MonHasSkill, UnitStoredUnit9C |
| R121 | `0x005E2BD0` | no | 5 | 0 | 0 | 0 | – |
| R122 | `0x005E2FF0` | no | 28 | 0 | 9 | 12 | fork: 00408090, 00408a60, 00681e09, OBJECTS_GetRecord, UnitsLineBlocked, 00681ef0 … |
| R123 | `0x005E34C0` | no | 2 | 0 | 0 | 0 | – |
| R124 | `0x005E3530` | yes | 9 | 0 | 0 | 0 | – |
| S15 | `0x005E1D30` | no | 3 | 0 | 0 | 0 | – |
| S16 | `0x005E2D80` | no | 21 | 0 | 12 | 12 | fork: 00408090, 00408a60, 00681e09, OBJECTS_GetRecord, UnitsLineBlocked, 00681ef0 … |
| R126 | `0x005EE040` | no | 6 | 0 | 6 | 7 | fork: FreeNearStep, 00408090, 00408a60, 00681e09, RoomRectGet, 0063ee10 … |
| R129 | `0x005E61B0` | no | 6 | 0 | 4 | 2 | fork: 00573520, MonRegionGet |
| R136 | `0x005EF710` | no | 5 | 0 | 2 | 0 | – |
| R137 | `0x005EFA90` | no | 7 | 0 | 0 | 0 | – |
| R128 | `0x005EE5D0` | no | 37 | 0 | 9 | 19 | fork: A5Q4_NihlathakSeen, SkillNodeMode, SkillNodeId, CorpsePickNear, MonHasSkill, 00408090 … |
| R32 | `0x005E7130` | no | 39 | 1 | 13 | 27 | rev 7: AiNearestPlayer; fork: 005bad20, 005bad40, 0059f570, A2Q4_GuardBlock, 0059b6e0, AiCtlParamGet … |
| R41 | `0x005E7540` | no | 18 | 0 | 8 | 9 | fork: AiCtlParamGet, MonAiWalkToPointCmd, PathSetDir, indirect |
| R42 | `0x005E9E00` | no | 2 | 0 | 0 | 0 | – |
| R54 | `0x005E73A0` | yes | 8 | 1 | 2 | 8 | rev 7: AiNearestPlayer; fork: PlayerIsBusy, NpcInteractAny, UnitSetEvent, 0059df50, 0059c750, 005b43f0 … |
| R58 | `0x005E7E20` | no | 6 | 0 | 1 | 4 | fork: NpcInteractAny, AiNearestPlayer, PlayerIsBusy, UnitSetEvent |
| R60 | `0x005E7AC0` | no | 9 | 0 | 2 | 0 | – |
| R62 | `0x005E7D60` | no | 3 | 0 | 0 | 0 | – |
| R81 | `0x005E7590` | no | 27 | 0 | 9 | 13 | fork: 0059b8b0, 0059b8f0, AiNearestPlayer, 0059aec0, AiCtlParamGet, NpcInteractHas … |
| R100 | `0x005E7F50` | yes | 2 | 0 | 0 | 0 | – |
| S11 | `0x005E8140` | yes | 15 | 0 | 0 | 8 | fork: MonForcedTargetClear, MonModeAllowed, MONSTATS_FlagTest, MonForcedTargetSet |
- **The rev 7 list, as the audit fixes it** (Phase 2 builds these, all read-only):
  1. a return-address window over R1's think 0x005B0CD0 (its 2 calls, `UnitGetRoom` and `Idle`);
  2. a line at `MonAiInit`'s init call: R43's init 0x005F6630 and state 11's 0x005E80E0 are called by `MonAiInit`, not by the
     think, so no call of theirs is in the audit;
  3. the calls inside `AiVileMotherSpawn` 0x005F9E30 (R68; it is a compared boundary, its own calls need `AI_NESTED` for it);
  4. the MonStats run and walk speed words (R70: no call, a data read);
  5. the return of `AiTrapArrowKind` 0x005FB650 and the region word `+0x2D4` it reads (R78 0x005FB749, R79 0x005FB869);
  6. the return of `StatListFindFlag` 0x00625760 (R118, 0x005E1E2F);
  7. the return of `AiNearestPlayer` 0x005DDF20 (R54 0x005E73B8; R32 through its helper 0x005E68F0, 0x005E6909);
  8. `MonPlayerBonus`'s block, 0x00573930 (R10, 0x005F0B32);
  9. R32's script and home words (data reads; R32 also forks on 27 calls of quest and NPC helpers, `audit.txt`);
  10. R48's owner record: the return of `MonsterOwnerRef` 0x0058F090 (0x005F6EE8), with `DRLG_ActFromLevelId` and
      `QUESTRECORD_GetState` after it (forks);
  11. R73's words: the audit finds no forking call (10 compared, 1 run), so its rev 7 words are data reads only, to be named
      from the block by Phase 1c's model.
- **Checker gaps.**
  - **Gap 2, `CONV`: closed for the audit's list.** The audit found 35 boundaries the tour's blocks call that `CONV` lacked
    (`CONV-MISSING`); revision 3 adds all 35 (`CONV_REV3`). Source: `ai_tour.py conv`, a caller read (ECX or EDX written,
    and the pushes, between the previous call and each call site in the windows; a register set at most sites is an argument).
    Checked against the 68 S1b entries, whose words matched the logged calls: **64 agree, 4 disagree** (`GetTargetUnit`,
    `WalkZ`, `SpawnClassCellTest`, `LogicRegionId`: arguments set before an earlier call, or fewer pushes than names;
    `conv.txt`). The names are positional (`c`, `d`, `s1`..`s6`), and a push count is an upper bound; a model that
    mismatches on a word corrects its entry with its own source.
  - **Gap 3, the boundary audit: closed** (above): every call of every new block has a class.
  - **Gap 5, the separation line: closed.** Each entry's report ends with `SEP <entry> outcomes N over M fork-free
    decisions`, an outcome being the sequence of the block's compared calls; the eight most common are listed. On S1b's logs:
    R4 6 outcomes over 353, R100 1 over 4, S11 1 over 66 (`regress-model-check.txt`).
  - **Gap 6, the regression guard: closed.** `ai_model_check.py regress` reruns S1b's check over its 38 logs with its 32
    entries and compares it, without the SEP lines, with `sweep2-s1b/model-check.txt`: **byte-identical** (`regress.txt`).
    Tests: `tools/test_ai_model_check.py` (13, 4 new).
- **Moves** (plan 0066 inventory; **merged `main` `f56ab708` first**, so n66e and n66f are in): catalogue 121–125,
  184–189, 204–205, 306–309, 311, 330–331, 333–334, 358–359, 361 and 475–479 **a-run → b, new batch H1p, out of this plan**
  (H1c 18, H1b 7, H1d 5): rows 46, 47, 62, 75, 76, 81, 82, 83, 87, 113, 121, reasons in the rows. README: § 1's catalogue line
  (a-run 172, b 124) and *All* line (a-run 328, b 424), the Phase 2 line, a § 3 bullet, § 4's H1b (38), H1c (41), H1d (11)
  and the new H1p row; gate W7 green. **The tour's scope is now 211 statements** (H1a 38, H1b 38, H1c 41, H1d 11, H1g 44, H1h
  39).
- **Judgment calls for the review:**
  1. The 11 unplaced entries go to **(b)**, not d-none: no source places them, but no code scan rules a creator out (rule 4
     of review-fixes). A d-none needs the class-id scan; H1p is that route. `rogue3` (R62) and `trap-melee` (R87) are named
     by MonPreset lists that no DS1 uses.
  2. **Placements that are likely, not certain**, kept as aims: the sarcophagus (R45) and the fire tower (R94) need a themed
     tomb room (`t-a2-canyon` takes the first tomb's warp, level 66); the claw vipers (R16), Doom Knights (R72), Oblivion
     Knights (R74), Blood Raven (R59), the Smith (R98), `navi` (R58) and the Bloody Foothills entries need a border walk,
     which may cross the wrong edge; the trap monsters (R77, R80, R92) need a trapped container and **a logger with
     `tools/gdb/objects.py`'s lines beside `ai.py`** (`--loot` reads them), which Phase 2 adds to the tour's gdb script;
     hireling states 5 and 6 need an unhired hireling to think near the player; `evilhut` (R129) is placed by DS1s LvlPrest
     does not name (`monsterspawner*.ds1`), known from the kept Act V logs.
  3. One seed per act, as the plan says, although each case is a fresh process and could take its own seed: one seed keeps
     an act's pools one prediction. The score counts entries, not (case, level, entry) pairs, because a pool keeps `NumMon` of
     its candidates and no seed can put five classes in one level.
  4. The audit's function ends are the next known start (`re/symbols.csv` and the AI table words), capped at the logger's
     window for the two callee windows; an unnamed function in between would be read as part of the one before it.
  5. The `CONV` additions are positional and come from a caller read that agrees with 64 of 68 S1b entries; Phases 1b and
     1c name the arguments as their blocks do and correct an entry on a mismatch.
  6. The NOTES row (517, row 7's second `aip(3)` draw) rides with R7's cases (`t-a1-cold`, `t-a1-marsh`).
- **Review request: Tier B** (plan § Phase 1a). Check against the kept outputs: the scope (241), the 30 moved rows and their
  reason, the seeds' scores and the pools (`pools.txt`, miss 0), the 45 cases' routes (`routes.txt`), the audit's classes
  on a sample of entries against the catalogue blocks, the 64-of-68 convention check, the SEP lines and the byte-identical
  regression, the README totals.
- **Next:** Phases 1b and 1c (the models) after this review; Phase 2 adds `objects.py` to the tour's gdb script with rev 7.

### 2026-11-15 — Phase 1a Tier B lane check (architect-check, `lane/n69a`)

- **Verdict: accept with fixes** (3 fixes: stale cross-reference 2, omission 1). Phase 1a's four *Done when* items hold
  against the kept outputs; the gate is green.
- **Done when, one by one.**
  - *Every row has a case or a move:* `ai_tour.py rows` regenerated, byte-identical to `rows.txt`: 211 cased, 30 moved, 0
    unplaced; the 30 moved rows are all class `b`, batch H1p in the catalogue file, and the 11 entries' other statements
    (rows 310, 332, 360, d-none or c-emu) were not a-run. The draft's 237 became 241 at 0066 S1d (scope note of
    2026-11-10); the lane's recount of 241 is right.
  - *The kept `pools.txt` matches the chosen seeds:* the six group seeds of `pools.txt` equal `seeds.txt`'s `best` lines and the
    plan's table; `ai_tour.py pools` regenerated, byte-identical; `seeds --group n4` re-run gives the same top three.
  - *Every call has a class:* `audit.txt` regenerated, byte-identical; the plan's table sums to 980 compared, 9 rev 7, 215 run, 166 fork over 89 entries;
    CONV-MISSING 0; `conv.txt` 68 checked, 64 agree, 35 entries in `CONV_REV3`.
  - *Regress:* run under `systemd-run --user --scope -p MemoryMax=4G`: "byte-identical", 32 entries, 38 logs, 32 SEP lines, and
    the output equals `regress-model-check.txt`. No-game tests (`python3 -I tools/test_ai_tour.py`, `test_ai_sessions.py`,
    `test_ai_model_check.py`): 9, 21, 13 ok. `place`, `routes`, `conv`, `cases`, `entries` also regenerate byte-identical.
- **Also checked.** `sha256sum -c manifest.sha256`: 12 of 12 OK. Inventory: 30 moved rows are `b` and H1p in the catalogue
  file; the file's class counts are a-run 172, b 124; the 29 files sum to a-run 328, b 424 (All row, Phase 2 752, Phase 1
  1 547 unchanged); H1b 38, H1c 41, H1d 11, H1p 30, tour scope 211 = 38 + 38 + 41 + 11 + 44 + 39. The (b) over d-none choice stands
  (review-fixes rule 4: no class-id scan, so no absence claim; `monsters/0004` agrees for `minionspawner1`, "placed by no DS1"). No `[L]` or
  `[C]` is added in the diff; the "likely, not certain" placements are aims, not claims.
- **Fixes (3).**
  1. *Stale cross-reference:* the plan's Phase 1b and 1c *What* lines still counted the entries before the moves (H1b 15, H1c
     20, H1d 8); now with the post-move counts (H1a 10, H1b 13, H1d 6 = 29; H1c 13, so 31), recounted from `entries.txt`.
  2. *Stale cross-reference:* Phase 1a's *Done when* said 237 rows; now 241 (237 at the draft).
  3. *Omission:* in `0066-inventory/README.md` § 3 the new 0069 bullet sat between S2b's bullet and its "After merging
     `main` with S1e" continuation, which read as the 0069 bullet's; the bullet moved below the continuation.
- **For the next phases (no fix).** The plan's *Lacks* section (the 71 entries, lines 195–202) and the cost table keep
  the draft figures, as the 2026-11-10 scope note says they stay; Phases 1b and 1c use the numbers in their *What* lines.
  `regress` reads its entry list from the kept `model-check.txt`, so a dropped entry would not show as a difference by
  itself (the byte comparison would still fail on the missing block). Phase 2 needs the `objects.py` line of the tour's gdb
  script (judgment call 2) and the rev 7 list.
- **Checked:** [C] added or raised 0; anchors `0x005FB650` (AiTrapArrowKind, R78/R79 rev 7), `0x00625760` (StatListFindFlag, R118), `0x005F6630`
  (AiNestInit, R43/R121 init) against `re/symbols.csv` and the audit; review-fixes rules 2, 3, 6 and 4 applied; request items all answered; disagreements
  routed 0; passes 7/8 skipped (no finding, table or format file in the diff).

### 2026-11-15 — Phase 1b: models for H1a, H1b and H1d (reverser, `lane/n69b`)

Static; no slot, no game, no Ghidra. Branched from `main` `7b7f20e9` (Phase 1a merged). Kept outputs in
`workspace/logs/n69b/` (`manifest.sha256`, 7 lines, passes `sha256sum -c` from that directory): `regress.txt`,
`regress-model-check.txt`, `new-entries-38.txt`, `shared-thinks-38.txt`, `branches.txt`, `audit.txt`, `test-output.txt`.
Tools: `tools/ai_model_check.py` revision 4 and `tools/test_ai_model_check.py`.

- **Scope:** the 29 entries of `entries.txt` (Phase 1a) in H1a (R8, R16, R142, R17, R18, R24, R25, R27, R72, R74), H1b (R115,
  R116, R117, S15, R119, R120, R122, R123, S16, R126, R129, R136, R137) and H1d (S5, S6, R41, R42, R58, R60). **All 29 are
  modelled; none is returned to its row.** Each model is the catalogue block at `b5999f5e` (the catalogue file is unchanged
  from there to `7b7f20e9`, `git diff --stat`), grouped per entry above `MODELS`, with its `MODELS` row (its think and inventory
  rows) after S1c's. Where a block names a table or callback by address only, the value is its finding's: the callbacks
  `AiNearAllyCb` 0x005F06B0 (R8), `AiSameBaseNearCb` 0x005B0D00 (R18), `AiOblivionKnightCb` 0x005FAE40 (R74), `AiImpNearCb`
  0x005E1720 (R115), `AiOverseerMinionCb` 0x005E26D0 (R120), `AiDefilerTargetCb` 0x005EFA50 (R137), from `re/symbols.csv`;
  `g_AiSpotterSkills` 0x006E3514 = 287, 288, 303, 304, 305 (R126, ai/0011). R25's tables `A`, `B`, `A5` are read from the
  catalogue's own listing at run time (`wisp_tables`; `B5` by its rule); rows 122 and state 16's fixed records 492..495 from
  the game's `monstats.bin` (`imp_rec`), so no table value is copied into `tools/`. S15 and R60 are their aliases' models (R117,
  S5).
- **Engine additions (revision 4), used only by the new models:** `_ecx`/`_edx` (a call on another unit: R25's
  `UnitQueueEvent(t, …)`, the near-self helper's game word); `Run.opaque` (a command that is neither a boundary nor executed and
  may move the seed: R25's `MoveToPointNoStop`, R41's `MonAiWalkToPointCmd`; the next call takes the logged seed, a draw before
  it stops the decision); `SELECT` (R117/S15 and R60/S5 share a think: each takes the decisions of its AI state, AID `st`, 0 for
  the table row; `check --no-select` lifts it).
- **Controls.** `run_check`'s per-entry controls apply to the new entries unchanged (FLIP of every named branch and store,
  `le`, `lecmp`, `d0`, ARM, EDGE, NEXT, VALS, SEP). The synthetic tests (`test_ai_model_check.py`, **47 tests, 34 new, OK**):
  - **a hand-built path per entry** (`Paths`, 29 tests; S15 rides on R117's model and R60 on S5's test): the callee, the
    words and the draw count before each call written from the block, with a wrong-word or wrong-branch case where the path
    has one;
  - **the branch controls** (`Branches`): a recorder runs each model on 1 500 seeded random inputs and writes the calls it
    makes as a logged decision with random oracle returns. Every recorded decision must match its model, and every named
    branch the decisions run must make at least one of them fail when that branch alone is reversed, the forked words held at
    the recorder's answers (as a rev 7 word would give them). **All 29 entries pass:** 317 named branches run, 314 separated by
    the recorder, the other 3 named in `EXEMPT`, each with its reason: R24 `2.1.aip(5)<v18` and R27 `5.v14<1` guard stores after
    the block's last call, which `run_check`'s FLIP sees at the next decision only; R25 `g.dead` (the grant is rarely reached by
    random inputs) is reversed by its hand path `test_r25_grant` (`branches.txt`, `test-output.txt`);
  - `Revision4` (3): the register override, the opaque seed's resync and stop, the state selection.
- **Regression:** `ai_model_check.py regress` under `systemd-run --user --scope -p MemoryMax=4G`: **byte-identical** to
  `sweep2-s1b/model-check.txt` without the SEP lines, 32 entries, 38 logs, 32 SEP lines (`regress.txt`), and its full output
  equals Phase 1a's `regress-model-check.txt` byte for byte (`cmp`).
- **The 38 kept logs give 0 decisions for every new entry** (`check --logs sweep2-s1b/logs.txt --rows` the 29,
  `new-entries-38.txt`), and 0 for the two shared thinks without the state split too (`--no-select`, `shared-thinks-38.txt`).
  `ai_tour.py audit` rerun: 48 entries `model yes` (19 + 29), the CALL lines unchanged from Phase 1a's `audit.txt`.
- **What the rev 6 logs can separate, per entry** (the forks are the Phase 1a audit's; `branches.txt` gives the recorder's
  fork-free share):
  - **Fork-free on most paths:** R8, R16, R142, R17, R18, R24, R27, R72, R115, R116, R117/S15, R122, R123, S16, R136, R137, S5/R60,
    S6, R42; R25 outside state 4's count and the grant's `STATLIST_Alloc`; R74 outside step 2's aura test and step 4's
    `MonsterData+0x0E`; R126 before its dead test and `FreeNearStep`; R129 outside the pick's region count.
  - **Every live decision forks, so none can count until its word is logged:** R119 (step 1's `StatListFindFlag(t, 0x20)` at
    0x005E2157 runs whenever `t ≠ 0`, which a kind-1 row always has), R120 (`AiStoredHostile`'s `U+0xC8` and stored unit at
    entry, `MonHasSkill` 0x005DD2D0), R58 (`NpcInteractAny` 0x00572DC0 at entry, `AiNearestPlayer`, `PlayerIsBusy`), R41 (the
    home word of `AiCtlParamGet(10)` at entry; then the kind-4, 5, 7 records' words and the path list). **For Phase 2's rev 7
    list:** the return of `StatListFindFlag` at R119's site 0x005E2157 (item 6 names R118's only); the return of
    `AiStoredHostile` 0x005DE830 at 0x005E27DA and of `MonHasSkill` at 0x005E2816, 0x005E29AF, 0x005E2A50 (R120); the return
    of `NpcInteractAny` at 0x005E7E45 and of `AiNearestPlayer` at 0x005E7E66 (R58; item 7 names R54's and R32's); R41's home and
    record words ride on item 9 (R32's script and home words; the same chain).
- **Judgment calls for the review:**
  1. **The recorder's branch test.** A per-branch hand test for 317 branches would be the model written twice; the recorder
     shows instead that each named branch is observable (reversing it changes the logged calls, words or seed) on inputs the
     model itself makes. It does not show the transcription right: that is the hand path per entry, and the review's read of
     the models against the blocks.
  2. **Calls the blocks imply but do not name**, modelled from the Phase 1a audit's call list: R25 state 4 begins with
     `UnitGetRoom(U)` (0x005F3E62, the room search's room); R126's `SpotterCatapultDead` makes one logged `UnitGetRoom(U)`
     (0x005EDF7F) before its forked result; S16's and R122's `AiUseSkillNearSelf` logs `UnitGetGame(U)` before its skill call
     (0x005DF96D, the block's "game of unit").
  3. **Words not compared, with the reason in each model's docstring:** R136's `UnitTeleport` (revision 3's caller read
     names three positional words, the block five, and no source maps them; the callee and the seed are compared); R74's
     `HasState` state (Skills' `auratargetstate`, not logged); R120's stored unit (not logged); R126's strike point (written by
     `FreeNearStep`, not a boundary); R8's wait outside Normal (`aidel` is logged for Normal only, AID `ad[0]`); R41's record
     words. R74's `FindHostile` out-slot is read, not compared before the call (the block: "not set before the call").
  4. **Non-boundary callees taken to draw nothing**, so the seed is compared through them: R120's quest hook 0x00587900,
     R58's `UnitSetEvent`, R25's room search and the grant's stat-list calls, R126's `SpotterCatapultDead` internals, R129's
     `MonRegionGet`. A draw in one would show as a seed mismatch at the next compared call, and the model is then corrected.
     The commands that may draw (`MoveToPointNoStop`, `MonAiWalkToPointCmd`) are opaque instead.
  5. **Arms that stop rather than guess:** R25's gather of four or five wisps (each found wisp's `AiCtlSetVar` and `Idle`,
     on other units), R25's dance with no target or an index outside the tables, S16's slot outside 0..7, R41's path action
     (an indirect call whose own calls the block does not give).
  6. R129's step 2 death arm is transcribed though the block says the pick returns 1 on every path, so it can never be taken
     (its branch `2.picked` is constant true; the recorder separates it only by its reverse).
- **Review request: Tier B** (plan § Phase 1b). Check against the kept outputs: each model against its block (the 29
  docstrings name what is not compared and why), the 47 tests, the 3 exemptions, the byte-identical regression, the 0
  decisions on the 38 logs, and the four always-forking entries with their rev 7 words proposed for Phase 2.
- **Next:** Phase 1c (H1c, H1g, H1h) on a branch cut after this one merges; its R32 reuses `npc_save_home`,
  `npc_script_step` and `npc_path_pick`.

### 2026-11-15 — Phase 1b Tier B lane check (architect-check, `lane/n69b`)

Tier B check of `lane/n69b` (head `6af73f90`, then `main` merged in; the catalogue file is unchanged from `b5999f5e`).

**Verdict: accept (0 fixes).** Gate GREEN, 0 errors.

- **Done when, one by one.** (1) All 29 entries modelled, none returned: `MODELS` holds all 29, and `Branches.test_every_entry_is_listed` names them.
  (2) `test_ai_model_check.py`: 47 tests OK, before and after the merge. The `report` shows 317 named branches, 314 separated by the
  recorder, the other 3 in `EXEMPT` (summed from `branches.txt`). (3) `regress` under `systemd-run --user --scope -p MemoryMax=4G`:
  byte-identical to `sweep2-s1b/model-check.txt` without the SEP lines, 32 entries, 38 logs; its stdout equals the kept
  `regress-model-check.txt` (`cmp`). The 29-entry check over the 38 logs reproduces `new-entries-38.txt` (`cmp`) with 0 decisions
  for all 29, and `check --no-select` on R117, S15, S5 and R60 reproduces `shared-thinks-38.txt` (`cmp`), 0 decisions.
  `sha256sum -c manifest.sha256` from `workspace/logs/n69b/`: 7 of 7 OK.
- **Transcription.** Read against the catalogue blocks: R16, R142, R17, R18 (H1a); R115, R116, R123 (H1b); S6, R42 (H1d). Steps, draw
  order, tests and constants match; the "dist > 10" and "p ≠ 0" forms are the same tests. S6's `U = 0` arm is left out, which its
  docstring says (S5's does the same).
- **Exemptions.** R24 `2.1.aip(5)<v18` and R27 `5.v14<1` guard stores after the block's last call (Ring; the second
  `Delay`/skill), so no later call in the decision can show them; both hold. R25 `g.dead` is reversed by `test_r25_grant`, which
  asserts the mismatch. Note for Phase 2: the first two are untested by anything until a log has a following decision.
- **Existing entries.** The engine diff holds three edits to old code (`want(spec, reg)` reads `_ecx`/`_edx` only when a model
  sets them; the seed compare is skipped only when `seed is None`, which only `opaque` sets). No old model uses either, and
  `regress` proves it.
- **Tables.** No table value copied into `tools/`: `wisp_tables` reads the catalogue text (`test_r25_tables_from_the_spec`), `imp_rec`
  reads `monstats.bin`, the tests use a synthetic `IMP`. The only literals are the five `g_AiSpotterSkills` ids and the six callback
  addresses (code-image constants, ADR-0031; the symbols are in `re/symbols.csv`).
- **Plan text.** The rev 7 words (R119, R120, R58, R41) appear only in this log as proposals; Phase 2's text is not edited.
- **Judgment calls 1 to 6: all accepted.** 1: the recorder shows each branch observable, not the transcription right; the hand
  path per entry and this read are the second leg. 2: the three implied calls (`UnitGetRoom` 0x005F3E62 and 0x005EDF7F,
  `UnitGetGame` 0x005DF96D) are in `audit.txt` as compared CALL lines. 3 and 4: stated per model; a draw in a "draws nothing" callee
  would show as a seed mismatch in the first log that reaches it. 5: stops rather than guesses. 6: constant branch, documented.
- **Routed.** Nothing disagrees with a document the lane does not own. Passes 7 and 8: the diff changes no finding, table or format doc.
- **For Tier A or the owner:** none.

### 2026-11-15 — Phase 1c checkpoint 1: resume note (reverser, `lane/n69c`)

Paused at the coordinator's request (owner reboot). Static; no slot, no game, no Ghidra started. Branched from `main` `684332ee`.

- **Done, uncommitted until this checkpoint:** `tools/ai_model_check.py` revision 5 (docstring not yet updated): models for all 31
  entries, H1c (R38, R45, R66, R77, R80, R92, R50, R53, R55, R59, R85, R94, R128), H1g (R7, R11, R14, R33, R36, R39, R40, R49, R56,
  R57, R71, R93, R98, and the notes row as `NOTES` on `m_r7`), H1h (R1 as `m_r1w`, which stops on a log below rev 7; R10, R32, R48,
  R73), with their `MODELS` rows; engine helpers `r7`/`known` (a rev 7 word from `dec["r7"]`, else a fork), `store_unknown`,
  `sweep_table` (R94's `SWEEP` read from the catalogue text) and `step_xy` (its `STEP` rule). `tools/test_ai_model_check.py`:
  `NEW5`, `R7WORDS` (the recorder gives the rev 7 words to half its decisions), 6 new `EXEMPT` reasons (R50 two, R93 two, R94, R32:
  stores after the last call), 35 new `Paths` tests, `Revision5` (3). The full suite last ran green at 82 tests, before `Revision5`.
- **Found while running the 38 kept logs** (development output kept as
  `workspace/logs/n69c/dev-new-entries-38-ckpt1.txt`, before the fix below). The logs **do** hold decisions for 9 of these
  entries (R7 14, NOTES 14, R40 6, R49 17, R71 9 all fork-free and matching; R1 4 stopped; R32 751, R48 121, R73 171), so the
  Done-when's "0 decisions" does not apply as written; report the counts instead.
  - R48: all 121 mismatched on `UnitGetPlayerData`'s word: the logs pass the player as the stack word (`s1`), ECX holds the
    level id. **Fixed** (`s1=p`), not yet rerun.
  - R73: 42 mismatches at step 7's `Ovr`: the logged byte word is the whole new low word with its low byte replaced (`0x9BBAEE07`
    for low `0x9BBAEE99`, `6 + (low & 1)` = 7), like R14a's ring argument. **To do:** compare `(low & ~0xFF) | (6 + (low & 1))`
    (or the low byte only) and say so in the docstring; the logged `HasState` state word there is 14 (a value for the proposed
    `R73.aurastate`).
  - R32: 1 mismatch (`s.find4` where the log has `Idle`@0x005E6A2C, inside `AiNpcNearPlayer`/`AiNpcHomeLeash`): to read; 160 stop at
    the path action, 590 forked.
- **Left:** the two fixes above and the R32 read; rerun the 38-log check into `workspace/logs/n69c/new-entries-38.txt`; `regress`
  under `systemd-run --user --scope -p MemoryMax=4G`; the recorder `report` into `branches.txt`; `ai_tour.py audit`; test output;
  `manifest.sha256`; revision 5 docstring; the Phase 1c log entry with the proposed rev 7 words (R56 `owner.mode` at 0x005F8FAC's
  return; R71 `found.mode` at 0x005FA76C and 0x005FA808; R85 `MissS1` and the missile `Range`; R128 the node's id and mode words,
  `CorpsePickNear`, `MonHasSkill`; R48 the act and quest returns), the Tier B request and the judgment calls.

### 2026-11-15 — Phase 1c: models for H1c, H1g and H1h (reverser, `lane/n69c`)

Static; no slot, no game, no Ghidra. Branched from `main` `684332ee`, checkpoint 1 at `9dfcc45d`, then `main` `fec1cc89`
merged (it touches none of the files below; the catalogue is unchanged from `b5999f5e`). Kept outputs in
`workspace/logs/n69c/` (`manifest.sha256`, 7 lines, passes `sha256sum -c` from that directory): `new-entries-38.txt`,
`rev4-entries-38.txt`, `regress.txt`, `regress-model-check.txt`, `branches.txt`, `audit.txt`, `test-output.txt`, all
written by the final revision 5 after the merge. The checkpoint's development output and the first test run are kept in
`workspace/logs/n69c/dev/` (its own `manifest.sha256`, 2 lines, passes from `dev/`). Tools: `tools/ai_model_check.py`
revision 5 (docstring names it) and `tools/test_ai_model_check.py`.

- **Scope:** the 31 entries of `entries.txt` (Phase 1a) in H1c (R38, R45, R66, R77, R80, R92, R50, R53, R55, R59, R85, R94,
  R128), H1g (R7, R11, R14, R33, R36, R39, R40, R49, R56, R57, R71, R93, R98) and H1h (R1, R10, R32, R48, R73), with H1g's
  Reimplementation notes row as `NOTES` (`m_r7`; the row is the block's step 3). **All 31 are modelled; none is returned to
  its row.** Each model is the catalogue block at `b5999f5e`, grouped per entry above `MODELS` like Phase 1b's. R1 is
  `m_r1w`: R100's block (`m_r1`), stopped on a log below rev 7, since the think 0x005B0CD0 is outside the rev 6 windows (rev 7
  item 1). R77, R80 and R92 share `trap_shot` (R80 and R92 are one block). R94's `SWEEP` and `STEP` are read from the catalogue text
  (`sweep_table`, `step_xy`), so no table value is copied into `tools/`.
- **Engine additions (revision 5), used only by the new models:** `r7`/`known` (a rev 7 word from the decision's `r7`
  map, else a fork: the H1h models' input, which Phase 2's `tools/ai.py` fills); `store_unknown` (a store of a word the log
  does not hold, compared only when flipped); `unit_set_event` (below).
- **Three fixes after checkpoint 1**, each found by the 38 kept logs (`dev/dev-new-entries-38-ckpt1.txt`):
  - **R48** (121 mismatches): `UnitGetPlayerData`'s player is the stack word (`s1`), ECX holds the level id. Fixed (`s1=p`).
  - **R73** (42 mismatches at step 7's `Ovr`): the logged byte argument is the whole new low word with its low byte replaced,
    `(low & 0xFFFFFF00) | (6 + (low & 1))` (`and al,1; add al,6` keeps EAX's upper 24 bits, R73a, 0x005FADB3–0x005FADC7; the
    form of R14a's ring argument). The model compares that word (docstring), and `Paths.test_r73_walk_override_word` fails on
    the low byte alone. The logged `HasState` state word at 0x005FAC0A is 14 in all 171 calls (a value for `R73.aurastate`).
  - **R32** (1 mismatch, `2026-11-03-ai-3-s2-5804-L4-fresh:a1-marsh.log` decision 1310): the log's `Idle(20)` at
    0x005E6A2C is `AiNpcNearPlayer` step 7's player arm, and its `c4` is 0x302240B against the AID line's 0x302200B.
    `UnitSetEvent` (0x00553380) ends with `or dword [esi+0xC4], 0x400` (0x005533B9, after its null-unit assert only), a
    store the catalogue's blocks do not name. The model's `unit_set_event` makes it, behind a fork on "p is a player"
    (`cmp [p], 0`, 0x005E6A11; the unit type is not logged). `Paths.test_r32_set_event_flag` and
    `Revision5.test_unit_set_event_flag` (the store flipped fails).
- **The 38 kept logs** (`check --logs sweep2-s1b/logs.txt --rows` the 32 names, `new-entries-38.txt`): **0 mismatches.**
  The logs hold decisions for 9 of the 32 names: fork-free and matching R7 14, NOTES 14, R40 6, R49 17, R71 9; forked and
  matching R32 591 (160 more stop at the path action), R48 121, R73 171; R1 4 stopped (rev 6). The other 23 have 0. Branches
  these logs cannot tell from their reverse (FLIP 0 of n): R7 `1.p.100<v` (0 of 9); R49 `2.Skill3>=0` (0 of 1), `2.St3or19`
  (0 of 16), `4.Skill1>=0` (0 of 16); R71's three `#e` stores (0 of 1 each).
- **Regression:** `regress` under `systemd-run --user --scope -p MemoryMax=4G`: byte-identical to
  `sweep2-s1b/model-check.txt` without the SEP lines, 32 entries, 38 logs (`regress.txt`); its output equals Phase 1a's and
  Phase 1b's `regress-model-check.txt` (`cmp`). The 29 revision 4 entries over the 38 logs (`rev4-entries-38.txt`) equal
  Phase 1b's `new-entries-38.txt` byte for byte (`cmp`). `ai_tour.py audit`: 78 entries `model yes` (48 + 30; R1 was already
  `yes` through R100's think), 11 not modelled (R46, R47, R75, R76, R87, R82, R83, R113, R121, R62, R81, the H1p moves), the
  CALL lines unchanged from Phase 1b's, `SUMMARY audit calls compared 980 rev7 9 run 215 fork 166 conv-missing 0`.
- **Controls** (`test_ai_model_check.py`, **88 tests, 41 new, OK**): `Paths`, 37 new (a hand path per entry, with a
  wrong-word or wrong-branch case where the path has one; R1 on a rev 6 and a rev 7 decision); `Revision5`, 4; the
  recorder (`Branches`, `NEW5`, 31 names, R1 left out: it stops on the recorder's rev 6 decisions and its block is
  `m_r1`, which S1b's logs check). The recorder gives the rev 7 words (`R7WORDS`) to half its decisions. **424 named branches
  run, 418 separated, the other 6 in `EXEMPT` with their reason** (R50 `c2.D100<50-L`, `c2.v14=0`; R93 `3.v18<1`, `5.v18<1`;
  R94 `8.aip(2)<v18`; R32 `n.v14<0`: each guards a store after the block's last call, which `run_check`'s FLIP sees at the
  next decision only) (`branches.txt`). R32's recorder decisions are all forked (0 fork-free).
- **Proposed rev 7 words** (for Phase 2's list; the model keys in `r7`'s docstring): R10 `MonPlayerBonus` (0x00573930,
  `pb.difficulty`); R48 `MonsterOwnerRef` (0x0058F090, the (guid, type) it writes) and the returns of `DRLG_ActFromLevelId`
  and `QUESTRECORD_GetState`; R32 `AiNearestPlayer` (0x005DDF20, (p, f)) **and p's unit type** (step 7's player test,
  0x005E6A11); R73 `R73.aurastate` (Skills `aurastate` of `Skill2`) and `R73.md0e` (`MonsterData+0x0E`); R56 `owner.mode`
  (the owner's mode at the return of 0x005F8FAC's call); R71 `found.mode` (at 0x005FA76C and 0x005FA808); R85 MonStats
  `MissS1` and the missile record's `Range`; R128 the skill node's id and mode words and the returns of `CorpsePickNear` and
  `MonHasSkill`. R1's is item 1 (the think's window).
- **Judgment calls for the review:**
  1. **Done-when wording.** Phase 1c's *Done when* is "as Phase 1b", whose third item is "the 38 kept logs give 0 decisions
     for these entries". For Phase 1c it does not hold as written: the logs hold decisions for 9 of the 32 names (above), all
     matching or stopped. The lane reports the counts and does not reinterpret the item; the review (or the plan's author)
     decides whether "0 mismatches, the counts reported" meets it.
  2. **`UnitSetEvent`'s store** is modelled from the binary (0x005533B9), not from the catalogue block, which names the call
     only. The same call sits in R54's step 2 (a revision 1 model, which sets `v18` unknown and leaves `c4` alone) and R58's
     step 3 (revision 4). Neither is changed here: R54 is under `regress`, and R58 has 0 decisions in the 38 logs, so a fix
     would be untested. A Phase 2 log reaching either arm will show the bit as a `c4` mismatch; the review may want both
     changed now, and the catalogue's three `UnitSetEvent` lines (R32, R54, R58) given the store (a spec-writer request).
  3. **R73's override word** is compared whole, as logged, though the block writes `6 + (new low & 1)`: the catalogue's
     R73a already says the byte is set in AL; the model states the upper bits' source.
  4. As Phase 1b: calls the blocks imply but do not name are taken from the Phase 1a audit's call list; non-boundary callees
     are taken to draw nothing (a draw would show as a seed mismatch); arms that run an indirect action stop (R32's path
     action, 160 of its decisions).
- **Review request: Tier B** (plan § Phase 1c). Check against the kept outputs: each model against its block (the 31
  docstrings name what is not compared and why), the 88 tests, the 6 exemptions, the byte-identical regression and revision 4
  check, the 0 mismatches on the 38 logs with the 9 non-zero counts, and the proposed rev 7 words.

### 2026-11-15 — Phase 2 checkpoint 1: resume note (reverser, `lane/n69d`)

Paused at the owner's request, at a case boundary (the 4th launch had not started; the batch runner was stopped between cases,
`slots.py stop 2`, slot 2 holds no process and no aside, `saves.py --slot 2 restore n69d` done). Harness work on slot 2 only;
branched from `main` `82eaa099`. Kept outputs in `workspace/logs/n69d/` (`manifest-ckpt1.sha256`, 13 lines, passes from that
directory): the raw logs, marks and the three case logs of `run:2026-11-15-ai-tour-1` (`t-a1-town` L1, `t-a1-cold` L2, `t-a1-stony` L3,
all seed 7159, fresh), `words-ckpt.txt` (`tools/ai_tour_words.py`), `model-check-ckpt.txt`, the runner's stdout. Development logs
(three smokes and a shared pair) are `workspace/logs/ai/dev-2026-11-15-*` and `workspace/logs/n69d/dev/`.

- **Done:**
  - Logger rev 7 (`tools/gdb/ai.py`, `REV = 7`): `R7W` word lines (MonPlayerBonus, MonsterOwnerRef, AiNearestPlayer with p's unit
    type, StatListFindFlag at R118 and R119, AiTrapArrowKind's region word, MonStats Velocity/Run for rows 48 and 70, row 73's
    `aurastate` and `+0x0E`), `AII`/`AIQ` at `MonAiInit`'s init call (row 43's and state 11's inits), the row 1 think window with
    its two return sites (`ai-retsites.txt` 2 287, `ai_retsites.py check` equals), the calls inside `AiVileMotherSpawn`. The rev 7
    call-site addresses of the Phase 1a audit are call sites; the breakpoints are at the return sites (+5), e.g. R54 0x005E73BD.
  - `tools/ai.py` fills `dec["r7"]` and `parse()["inits"]`; `tools/test_ai.py` 25 tests; `tools/ai_tour_words.py` (new).
  - `ai_model_check.py` revision 6 (docstring): the words feed R54, R32 (unit type), R70, R48, R78, R79, R118, R119; `UnitSetEvent`'s
    `Unit+0xC4 |= 0x400` is made by R54 step 2 (behind the fork `2.setevent`) and R58 step 3, the Phase 1c review item.
    `test_ai_model_check.py` 97 tests OK (`Revision6`, 9). `regress`: byte-identical, 32 entries, 38 logs; the 32 Phase 1c names
    over the 38 logs: identical to Phase 1c's `new-entries-38.txt`.
  - Predictions committed at `aafee9e3` (experiments.md, `run:2026-11-15-ai-tour-1`), before the first kept log.
  - Launch against switch (dev, shared pair on slot 2): launch to ready 18.6 s and 19.1 s, a switch 18.7 s: no saving, so the
    tour stays **fresh per case** (harness-play § Fresh process; ADR-0028 item 4 gives no reason to share).
  - Kept so far, checked: 3 cases, `check` over the three logs 0 mismatches (R1 37 decisions ok, fork-free; R10 178 fork-free with
    its word; R54 16, fork-free; R7 and the notes row 10; R36 21; R43 4 and 3 `AII`/`AIQ` pairs of 0x005F6630; R32 228, 210 ok,
    18 stopped at the path action); `tools/ai.py check` 0 mismatches.
- **Left (resume here):**
  - Launch the rest of the Act I batch fresh, same command (`ai_sessions.py run --slot 2 --tag n69d --saves
    workspace/logs/n69d/saves --run 2026-11-15-ai-tour-1 --fresh t-a1-darkwood t-a1-marsh t-a1-barracks t-a1-catacombs
    t-h1h-a1-stony t-h1h-a3-flayer-p8 t-h1h-s-barb-flayer t-h1h-s-necro-curse`; the saves are built by `ai_sessions.py build
    --saves workspace/logs/n69d/saves`, CombatSor `1d9de374…`). The launch numbers continue from L4 (a new run id or `--status`
    avoids overwriting `…s2.status.json`; the pinned seeds hold). Then the regression case `a2-oasis` seed 5201 in its own
    batch (its seed is `seed0 + launch 0`, so first in a batch).
  - Run `ai_model_check.py check --logs`, `ai.py check`, `ai_resume_flip.py` (H1g `r` lines), `regress`, `ai_tour_words.py` over all
    kept logs; the 38 kept logs' byte check; the `experiments.md` results, separation lines, decision counts per entry, case list
    with process and position, the final `manifest.sha256`; this plan's Phase 2 log entry; the Tier B request.
  - Prediction 3 so far: R7, R10, R36 (cold), R43 and its `AII` (stony) held; R59 not tested; `t-a1-town` gave R32 and R54 and R1
    (R60 not seen in the dev logs); S5/S6 not seen.
- **Not done in rev 7, on purpose:** R32's home and script words (no model key reads them), `objects.py`'s lines beside the
  logger (R77, R80, R92 are Act II and III), R56/R71/R85/R128's Phase 1c words (Acts III to V). **For Phase 3:** the R68 model must
  consume the calls now logged inside `AiVileMotherSpawn`, or an Act IV log shows a mismatch at the call after it.

### 2026-11-15 — Phase 2: Act I tour kept (reverser, `lane/n69d`)

Resumed from the checkpoint 1 note at its case boundary; slot 2 only, `--fresh`, `MemoryMax=4G` per launch, saves restored
(`saves.py --slot 2 restore n69d`), slot 2 holds no process. Record: `run:2026-11-15-ai-tour-1` and its Results section in
[experiments.md](../findings/ai/experiments.md); kept outputs `workspace/logs/n69d/manifest.sha256` (63 lines).

- **Done:** the 8 remaining Act I cases (`t-a1-darkwood`, `t-a1-marsh`, `t-a1-barracks`, `t-a1-catacombs`, `t-h1h-a1-stony`,
  `t-h1h-a3-flayer-p8`, `t-h1h-s-barb-flayer`, `t-h1h-s-necro-curse`) and the regression case `a2-oasis` (seed 5201) are kept,
  12 cases with the three of the checkpoint. `t-h1h-s-necro-curse` needed a second launch (the first, 90 decisions, was ended by
  the runner's relaunch; kept as L8, unchecked).
- **Checks:** `ai_model_check.py check` 0 mismatches over 95 entries, except the control `R79x` (2, as required); `ai.py check`
  over the 12 logs 5 153 decisions, 0 mismatches; `a2-oasis` 0; `regress` byte-identical (32 entries, 38 logs); the flip over
  the resume rows (`flip-rows.txt`, `flip-states.txt`). Tests: `test_ai_model_check.py` 98, `test_ai.py` 25.
- **One checker change.** The first check had 2 R23/R23x mismatches (flayer-p8, decisions 7525 and 8657): the logger's
  `OUT_LIMIT` (`AIL`, 601 calls made outside the think inside `FreeNearFallback`'s search) disarmed the boundary breakpoints, so
  the model's `Ovr` after it had no logged call. `Run.call` now stops such a decision as `finish` already did (`Stop("AIL")`);
  `regress` is unchanged. No model changed.
- **Predictions:** 1, 2, 4, 5 held; 3 held except R60 (not seen in any log), R59, R98 and R58 (conditional, not reached).
  Sharing decision: fresh per case.
- **Left for Phase 3:** the Act II to V batches; the R68 model must consume the calls logged inside `AiVileMotherSpawn`
  (checkpoint note). R60 stays untested.
- **Review request: Tier B** (backlog entry `2026-11-15-reverser-architect-plan-0069-p2-tier-b-review-request`).

### 2026-11-16 — Phase 3a: Acts II and III kept (reverser, `lane/n69e`)

Branched from `main` `34271870`; slot 2 only, `--fresh`, launches under `MemoryMax=4G`, saves restored
(`saves.py --slot 2 restore n69e`), slot 2 holds no process and no aside. Record: `run:2026-11-16-ai-tour-2` and its Results section in
[experiments.md](../findings/ai/experiments.md); kept outputs `workspace/logs/n69e/manifest.sha256` (86 lines, passes from that
directory). Predictions committed at `c29d96cc` before the first kept log.

- **Model prerequisites:** R68 needs no model change: `ai_resume.top_level` already drops the calls logged between a pending
  boundary's AIB and AIR lines, which includes the calls inside `AiVileMotherSpawn`; the test
  `Revision6.test_nested_calls_inside_a_pending_boundary_are_not_offered` (99 tests) states it. R77, R80 and R92 have models
  (`trap_shot`; their rows were not reached). No logger change (rev 7 kept): R56's `owner.mode`, R85's `MissS1` and `Range`, R32's home
  and script words stay unlogged, so R56 (76 decisions) and R32 and R41 are all-forked.
- **Done:** 17 cases kept: Act II `t-a2-town`, `t-a2-dryhills`, `t-a2-oasis`, `t-a2-lostcity`, `t-a2-canyon`, `t-a2-palace`,
  `t-a2-arcane`, `t-a2-halls` (seed 8723, one rerun: the first `t-a2-town` launch left the player in level 103 at the stage gate);
  Act III `t-a3-town`, `t-a3-spider`, `t-a3-marsh`, `t-a3-flayer`, `t-a3-lower`, `t-a3-bazaar`, `t-a3-upper`, `t-a3-travincal`,
  `t-a3-durance` (seed 7842). 7 143 decisions. `t-a3-town` is kept short (28 decisions, 27 s: the town walk ended at hop 1, "no target,
  level done"); its aims R41, S5 and S6 are held by `t-a2-town` (R41 200 decisions) or not reached.
- **Checks:** `ai_model_check.py check` over the 17 logs: 0 mismatches in every real entry, the controls `R78y` (8 of 13) and `R23x` (1)
  failing as controls do, R79x not reached (over the 29 logs: 2 of 10, as required); `ai.py check` 7 143 decisions, 0 mismatches;
  `regress` byte-identical (32 entries, 38 logs); the resume flip (`flip-rows.txt`, `flip-states.txt`: every two-way site fails alone
  except R23's site 0x005F356C, `nosep` in 11 decisions); `ai_tour_words.py`. Tests: `test_ai_model_check.py` 99, `test_ai.py` 25,
  `test_ai_sessions.py` 21, `test_ai_tour.py` 9.
- **Entries reached:** R3, R5, R7 and the notes row, R8, R11, R12, R15, R17, R18, R23, R24, R25, R27, R32, R38, R39, R40, R41, R42, R48, R49,
  R52, R54, R56, R57, R65, R78, R94, R95, R96. Decisions, fork-free count and separation line per entry are in the Results table.
  **Not reached** (Phase 3a aims with 0 decisions): R16, R43 (its `AII`/`AIQ` pair was logged 3 times in `t-a2-oasis`), R45, R50, R53,
  R66, R77, R80, R85, R92, R93, S5, S6. The hunts (Summoner, Mephisto, the council, the maggot queen) timed out with the class never
  seen; the loot walks sprang no trap. These go to a later rerun or to Phase 4's d-owner list, not to this lane's re-staging.
- **Predictions:** 1 and 2 held; 3 held except the cases and rows named in the Results (R43, R16, R48 and R49 at `t-a3-bazaar`, R27 at
  `t-a3-upper`, R41 at `t-a3-town`); 4 and 5 reported as printed. Sharing decision: fresh per case.
- **Contradictions:** none; nothing filed for the spec. **Observation for the out-of-plan batch H1p:** think 0x005E7590 (row 81)
  has 5 decisions in `t-a2-town`.
- **Left for Phase 3b:** Acts IV and V and the Nightmare cases (R68's Act IV logs; R118, R119, R128). The not-reached list above is
  the owner's call: one more Act II/III batch with a changed route for the timed-out hunts, or d-owner.
- **Review request: Tier B** (backlog entry `2026-11-16-reverser-architect-plan-0069-p3a-tier-b-review-request`).
