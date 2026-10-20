# 0046 — Skills and missiles, the function catalogue: every numbered skill and missile function (ADR-0014 phase 3, part 2)

> **Status:** approved 2026-10-20 (owner)
> **Created:** 2026-10-20
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0004-boundary-oracles-in-reproduction, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0015-emulated-reproduction, 0020-skills-phase-in-two-plans

## TL;DR

**Question:** what does each numbered skill function (`srvstfunc`, `srvdofunc`, `srvprgfunc`) and each numbered
missile function (server do, hit and damage) do: which states it applies, which missiles and units it creates, which
calcs and params it reads, and which draws it makes on which seed? When it is done, `docs/findings/skills/` holds one
catalogue section per function, raised to `[C]` by emulation (ADR-0015) or by harness events, and
`docs/specs/skills/catalogue.md` (or one file per class, as the spec-writer chooses at the start) specifies every
function a stock row uses on the machinery of plan [0045](0045-skills-missiles-machinery.md).

## Context

- **Why a separate plan:** [ADR-0020](../adrs/0020-skills-phase-in-two-plans.md). Skills.txt has 64
  distinct `srvstfunc` and 138 distinct `srvdofunc` values ([Skills](../tables/Skills.md)); the progressive functions
  and the missile functions come on top (counted by plan 0045's survey). Scripted play reaches few of them, so static
  reading and emulation carry this plan; the harness samples each family.
- **Research map row:** `skills/catalogue` in the Simulation band, added when plan 0045 starts (ADR-0020
  § Negative). Wiki owner: plan 0045's Phase 4 page gains a catalogue section here (Phase 4 below).
- **Gate.** Phase 0 and Phase 1 start after **0045·P1.3 is reviewed** (the machinery named and tier A fixed);
  Phase 2 after **0045·P3 is reviewed** (the model this plan's checker extends). This plan never gates phase (4)
  (ADR-0020).
- **Inputs from the backlog and specs:** stats/states' Holy Shield and progressive skills beyond tier A, the timed
  self-states (armours, shouts), the skill shrine's state 134 reader ([stats/states](../specs/stats/states.md)
  *Open questions*); the seven States rows with no immediate setter (6, 25, 29, 39, 116, 164, 171); objects' missile
  and monster shrines ([objects](../specs/objects/README.md) *Open questions*); the backlog's `0x005C09E0` question
  (`2026-10-17-reverser-reverser-plan-0039-p1c-residues-not-blocking.md` (a), if plan 0049 has not answered it).

## Phases

### Phase 0 — The function index
- **Owner skill:** archivist
- **What:** from plan 0045's survey, the per-function index: for each function number, the stock rows that use it, the
  params and calcs those rows fill, and the batch it belongs to.
- **Outputs:** [Skills](../tables/Skills.md) and `docs/tables/Missiles.md` § Function index; `tools/skills_survey.py
  --index` printing it.
- **Done when:** every function number used by a stock row is listed once, with its rows; the batch list below is
  filled with counts; the survey's `SURVEY` line matches; the gate is green.

### Phase 1 — Read the catalogue, in batches
- **Owner skill:** reverser
- **What:** read each function of a batch, then raise what the emulator can: one lane and one review per batch.
- **Batches** (counts from Phase 0): one per character class (seven), one for the monster-only skill functions, one
  for the missile do, hit and damage functions, one for the item, shrine and object callers of skills (`ctc`,
  charges, shrine missiles). Ten batches. *Filled 2026-10-20 (Phase 0, `lane/p46a`)*: entries of the start, do and
  missile tables by the rule of [Skills § Function index](../tables/Skills.md#function-index-plan-0046-phase-0)
  (`skills_survey.py --index`, `ix_batch_*`), with the tier-A entries plan 0045 already read in brackets:
  1. `ama` 17 (start 7, do 10; tier A 4);
  2. `sor` 18 (start 4, do 14; 5);
  3. `nec` 19 (start 7, do 12; 3);
  4. `pal` 15 (start 5, do 10; 3);
  5. `bar` 19 (start 7, do 12; 2);
  6. `dru` 16 (start 3, do 13, two of them States `srvactivefunc` 145 and 146; 2);
  7. `ass` 29 (start 7, do 22, the seven `srvprgfunc` entries among them; 5);
  8. `monster` 70 (start 20, do 50, `srvactivefunc` 147 among them; 0);
  9. `missile` 97 (do 34, hit 50 with row 568's uncalled 64 948, damage 13; 10);
  10. `item` 2 (do 113 for the scroll and book rows, do 151 for Chain Lightning's item cast; 0), plus the callers,
     which are code paths and not function numbers (the stat-event handlers 20, 21 and 30, charges, the shrine
     missiles of `g_ShrineEffects` 19, 21, 22, the object and quest `MissileCreateAt` sites, skills/0002 § 2).

  The eight `general` entries (rows 0–5: start 1, 2, 3, 65, do 1, 3, 4, 5) are tier A but Unsummon's start 3 and do 4,
  which this phase proposes to read with batch 10. 310 entries in all, 40 reached by tier A. Sizes for the review: the
  `monster` (70) and `missile` (97) batches are three to five times a class batch, more than one lane run of about
  4 h each; this phase proposes to split them (monster by start/do, missile into do and hit/damage) at the review.
- **Outputs:** `docs/findings/skills/0003-catalogue.md` (one section per batch, one sub-section per function);
  `re/symbols.csv` rows (subsystem `skills/catalogue`); emulation cases under `tools/` with their memory specs.
- **Done when**, per batch: each function has, with addresses and `[I]` or better: its params and calcs read, the
  states applied (with their durations' source), the missiles and units created, its draws in order and the seed of
  each, and any machinery path it takes that plan 0045 did not describe (filed back to 0045's spec as a correction,
  not changed here); the functions whose read set is declarable (ADR-0015 (2)) are emulated over synthetic and stock
  inputs with a negative control, and their maps `[C]`; the rest are named with the reason.

### Phase 2 — Harness sample
- **Owner skill:** reverser (agent-driven; **one slot**, given in the prompt)
- **What:** for each family with no tier-A member, log one representative skill on the machinery of
  `tools/skills.py`, so the catalogue's draws and outputs are checked in the game and not only under emulation.
- **Done when:** `run:YYYY-MM-DD-skills-catalogue` reproduces with **0 mismatches**; each family is reached by at least
  30 events of one member, or named as a shortfall with the reason (a targeted skill the pilot cannot cast, a monster
  skill no reachable monster uses); chained pairs as in plan 0045.

### Phase 3 — Spec: the catalogue
- **Owner skill:** spec-writer
- **What:** `docs/specs/skills/catalogue.md` (or per-class files), one entry per function on the machinery of
  `skills/dispatch` and `skills/missiles`; stats/states and objects updated where a function answers their questions.
- **Done when:** each entry has its pseudocode with draws in order and its tags; the spec never restates a 0045
  statement, it links it; the architect's review passes. Merges after any open 0045 spec change (ADR-0020 § Negative).

### Phase 4 — Wiki section
- **Owner skill:** spec-writer
- **What:** a catalogue section in `docs/wiki/skills.md`, by class.
- **Done when:** `based_on` current; the architect's review passes.

## Resources and limits

- **Static:** Phase 1 holds **one** Ghidra lane (`-Xmx3G`) at a time, batch after batch; it may take the second
  lane only when plans 0045, 0048 and 0049 hold none.
- **Harness:** Phase 2 takes **one slot from 1–2**; at most two games at once across all plans.
- **Rotation:** each batch is sized for one lane run of about 4 h; a batch that runs over checkpoints and resumes.
- **Estimate** (an estimate): ten static batches, one harness lane run.

## Open questions

- **Synthetic-only functions.** A function no stock row reaches is specified from the code and its emulation, and
  flagged as such; edited-data cases are ADR-0013's.
- **Monster AI.** Which monster uses which skill, and when, stays phase (4)'s.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-20 — Drafted (architect, `lane/plans45`).** Status `proposed`, with ADR-0020 (proposed).
- **2026-10-20 — Approved (owner, via the orchestrator).** Plans 0045–0049 and ADR-0020 approved as proposed; the run
  order of the [plans index](README.md#run-order-unattended-queue-set-2026-10-20-plans-00380049) is the current queue.
- **2026-10-20 — Phase 0 landed for review (archivist, `lane/p46a`, no harness, no Ghidra).** The function index:
  `tools/skills_survey.py --index`, [Skills § Function index](../tables/Skills.md#function-index-plan-0046-phase-0)
  (start table 64 entries; do table 149: `srvdofunc` 138, `srvprgfunc` 7, `ItemEffect` 2, States `srvactivefunc` 3)
  and [Missiles § Function index](../tables/Missiles.md#function-index-plan-0046-phase-0) (do 34, hit 50, damage 13),
  each entry with its rows, row kinds, the `Param`/`calc` cells its rows fill, tier A and batch; `[C]` as data. The
  batch list above is filled (310 entries, 40 reached by tier A). **`skills` baseline changed** (rerun of the survey):
  46 new `ix_*` keys, the old keys unchanged; `excel_layout` unchanged. Four reverser entries closed: the Skills,
  Missiles, ItemStatCost, States, PetType and MonStats meanings skills/0001–0003 anchor raised to their `[I]`, and
  MonPlace's row-24 sentence corrected. Surprises, in the batch list and the review request: the `monster` (70) and
  `missile` (97) batches outsize one lane run (a split proposed); `ItemEffect` 36 is Claws of Thunder's progressive
  entry 36; no Skills row has `srvdofunc` 146, which skills/0003 names so. Review request
  [to the architect](../backlog/2026-10-20-archivist-architect-lane-p46a-review-plan-0046-phase-0.md).
