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
  charges, shrine missiles). Ten batches, fifteen after the review's split. *Filled 2026-10-20 (Phase 0, `lane/p46a`)*: entries of the start, do and
  missile tables by the rule of [Skills § Function index](../tables/Skills.md#function-index-plan-0046-phase-0)
  (`skills_survey.py --index`, `ix_batch_*`), with the tier-A entries plan 0045 already read in brackets:
  1. `ama` 17 (start 7, do 10; tier A 4);
  2. `sor` 18 (start 4, do 14; 5);
  3. `nec` 19 (start 7, do 12; 3);
  4. `pal` 15 (start 5, do 10; 3);
  5. `bar` 19 (start 7, do 12; 2);
  6. `dru` 16 (start 3, do 13, two of them States `srvactivefunc` 145 and 146; 2);
  7. `ass` 29 (start 7, do 22, the seven `srvprgfunc` entries among them; 5);
  8. `monster` 70 (start 20, do 50, `srvactivefunc` 147 among them; 0), **split at the review** (below) into 8a–8c;
  9. `missile` 97 (do 34, hit 50 with row 568's uncalled 64 948, damage 13; 10), **split at the review** into 9a–9d;
  10. `item` 2 (do 113 for the scroll and book rows, do 151 for Chain Lightning's item cast; 0), plus the callers,
     which are code paths and not function numbers (the stat-event handlers 20, 21 and 30, charges, the shrine
     missiles of `g_ShrineEffects` 19, 21, 22, the object and quest `MissileCreateAt` sites, skills/0002 § 2), plus
     **Unsummon's start 3 and do 4** (ruled at the review), the two `general` entries plan 0045 did not read.

  The eight `general` entries (rows 0–5: start 1, 2, 3, 65, do 1, 3, 4, 5) are tier A but Unsummon's start 3 and do 4,
  which batch 10 reads. 310 entries in all, 40 reached by tier A. Batch 7 also states the data join of `ItemEffect`
  36: it is Claws of Thunder's `srvprgfunc2` entry, so the Nova and Frost Nova item casts run progressive entry 36
  (for a non-progressive row its missile is `srvmissilea`, skills/0003 § 1).

  **Split (architect ruling, `lane/p46a` review, 2026-10-20).** A class batch is 15–29 entries; `monster` (70) and
  `missile` (97) are cut to that size. The monster batch goes by the lowest Skills row that uses the entry (for
  States `srvactivefunc` 147, the row whose `aurastate` is `attached`, 330 Imp Teleport), so a skill's start and do
  entries mostly fall in one sub-batch; the missile batch goes by table and number, so each sub-batch reads one kind
  of function. Counts from `skills_survey.py --index` (tier A in brackets):
  - **8a** monster rows 156–189 (acts 1–3 monsters and the shared monster skills): 30 entries, start 42–53, do 83–98,
    110, 111 (0). Start 53 is also 193 DiabLight's, whose do 152 is 8b's.
  - **8b** monster rows 190–289 (Diablo, act 4 and act 5 towers, curses, the Wake and Imp rows): 22 entries, start 54,
    55, 59, 60, 64, do 99–109, 112, 125–127, 141, 152 (0).
  - **8c** monster rows 290–338 (act 5 monsters and Baal): 18 entries, start 61–63, do 128–137, 139, 140, 147–149 (0).
  - **9a** missile do 1–18 (17 numbers; 4 unused): 17 entries (3: do 1, 3, 5).
  - **9b** missile do 19–36 (17 numbers; 24 unused) and damage 1–14 (13 numbers; 6 unused): 30 entries (2: do 23,
    damage 3).
  - **9c** missile hit 1–29 (25 numbers): 25 entries (4: hit 2, 3, 14, 17).
  - **9d** missile hit 31–59 (24 numbers) and row 568's 64 948 (uncalled, stated as such): 25 entries (1: hit 36).

  Fifteen batches in all (7 class, 3 monster, 4 missile, item), 310 entries; each one lane run and one review.
  **Order for the static lane** (one batch at a time; plan 0048 holds the other Ghidra lane): 9a, 9b, 9c, 9d (the
  missile functions every class skill creates, so the class batches can cite them), then 2 `sor`, 1 `ama`, 3 `nec`,
  4 `pal`, 5 `bar`, 6 `dru`, 7 `ass` (tier-A count first, then PlayerClass order; `ass` last as the largest, with the
  progressive entries), then 10 `item` (with Unsummon), then 8a, 8b, 8c (monster AI is phase (5), after animation;
  its plan may pull a monster sub-batch forward, or take the function as a boundary oracle under ADR-0020).
  *Carried from plan 0045's P1b review (2026-10-20):* the Assassin batch reads the five finishing-move calls of
  `COMBAT_PrgFinisher` (do 46 at `0x005D6399` and `0x005D63E1`, written "start 25" until the `lane/p46m11` review;
  do 42 `0x005D5A8C`, 50 `0x005D71F2`, 52 `0x005D79DF`); the item, shrine and object batch reads which unit `ITEMSKILL_Cast` gives the `ItemTarget` 2 helper
  `0x005FD850` (it draws 2–20 steps on that unit's seed), whether helpers 3 `0x005FD9C0` and 4 `0x005FDA10` draw (and gives the three
  helpers `re/symbols.csv` rows: none has one), and
  what removes pets when `petmax` falls (a skill shrine wearing off). Each is filed back to plan 0045's spec as a
  correction.
- **Outputs:** one finding per batch, `docs/findings/skills/NNNN-<batch>.md` numbered in landing order from 0004
  (batch 9a is [skills/0004](../findings/skills/0004-missile-do-1-18.md); 0003 is P1.3's handlers; ruled at the
  `lane/p46m1` review), one sub-section per function;
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
- **Estimate** (an estimate): fifteen static batches (ten, with 8 and 9 split at the Phase 0 review), one harness
  lane run.

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
  [to the architect](../backlog/archive/2026-10-20-archivist-architect-lane-p46a-review-plan-0046-phase-0.md).
- **2026-10-20 — Phase 0 reviewed: accept (architect, `lane/p46a` review).** Reran `gate.py --full=skills,excel_layout`
  (green) and `skills_survey.py --index`: the `skills` baseline is the survey's own output byte for byte (regenerated,
  not hand-edited; 46 `ix_*` keys added, none changed). An independent join over Skills, States and Missiles gives the
  same entry sets: start 64 (id 30 the only gap), do 149 (`srvdofunc` 138, `srvprgfunc` 7 disjoint from it, `ItemEffect`
  above 1 adds 151, States 145–147; 53, 138 and 142 unused, as skills/0001 § Answer), missile do 34, hit 50 (the `*12`
  cell is the 64 948 record), damage 13; both docs list each entry once (310, no duplicate numbers per table). Meanings
  raised in Skills, Missiles, ItemStatCost, States, PetType, MonStats and MonPlace match their findings' `[I]` (spot
  checks: `Holy`, `SrcTown`, `LastCollide`, `repeat`/`weapsel`/`leftskill`, `TgtPlaceCheck`, `SkillDamage`, `group`,
  `itemeventfunc` 31, rows 24/26); anchors `g_SkillStartFuncs`, `g_SkillDoFuncs`, `g_StatEventFuncs`,
  `STATEVENT_Reanimate`, `PetAdd`, `StateDoFunc`, `MonOwnerSkillDamage` resolve in `re/symbols.csv`. No values dumped
  (row names and cell counts only). Rulings: the `monster` and `missile` batches split into 8a–8c and 9a–9d and the
  static order set (Phase 1 above); Unsummon's start 3 and do 4 go with batch 10; the `ItemEffect` 36 join is batch
  7's. The skills/0003 Functions-table label of `0x005C8520` ("`srvdofunc` 146") was a pure wording fix the review made
  itself after checking the data (no Skills row has `srvdofunc` 146; Armageddon and Hurricane both have 124; entry 146
  is state 145 `armageddon`'s `srvactivefunc`). Point (4) of the request (the `KnockBack` byte) stays as laid out.
- **2026-10-20 — Phase 1 batch 9a landed for review (reverser, `lane/p46m1`, static, no harness).** Missile server do
  functions 1–18: 17 entries, 14 read ([skills/0004](../findings/skills/0004-missile-do-1-18.md); do 1, 3, 5 tier A,
  cited). Draws: only `sub_005A9820_MissSubNearReseed` (do 8, 10, 17: the missile seed re-seeded from its position
  plus the elapsed frames, then two `RNG_RangeB`) and do 18 (two `RNG_RangeB` per gold drop). Raised by emulation
  (run:2026-10-20-cat-emu-9a, `tools/skills_catalogue_emu.py`, new `EmuBoundary.java`): 13 functions in nine families,
  13 800 cases, 0 mismatches; do 7 in part, do 13 not emulated (named). Surprises: entry 1 is a thunk; do 17 and 18
  read the raw `Range` column; Frozen Orb's `+0x28` is a direction index, not a seed word; the cairnstones portal and
  the Countess chest gold answer quests/0001's open question. Review request
  [to the architect](../backlog/archive/2026-10-20-reverser-architect-lane-p46m1-review-plan-0046-batch-9a.md) (two rulings:
  the `observe` boundary under ADR-0015, and the finding's file name).
- **2026-10-20 — `lane/p46m1` review (architect): batch 9a accepted with fixes (3: the boundary tags, the call-site check, the plan's output name).** Spot checks: objdump of
  `sub_005A9820_MissSubNearReseed` (`RNG_SeedInit(m+0x20, SubX + elapsed)` at 0x005A9877, then two
  `RNG_RangeB(m+0x20, 2(r − 1))` at 0x005A98C2 and 0x005A98D1, x first) and do 18 (two `RNG_RangeB(m+0x20,
  2·Param3 + 1)`, `Param3` = record `+0x40`, at 0x005AF43A and 0x005AF44E, x then y) agree with the finding;
  `g_Circle64X/Y` read at 0x005AF116/0x005AF11D and start `(30, 0), (29, 2)`; `sha256sum -c manifest.sha256` passes
  (48 files); `check homing scatter` re-run from the kept outputs gives `check.txt`'s lines, and `cases homing`
  regenerates the kept case and memory files byte for byte; `EmuTrace.java` is unchanged (`3255db0c…`, as on `main`).
  **Ruling (1):** a case that ends at an `observe` boundary does not meet ADR-0015 (1) and (3) as written (two
  treatments of a reached callee; no register arguments among (3)'s outputs). The method is sound, so the architect
  drafted [ADR-0021](../adrs/0021-observed-boundaries-in-emulation.md), **proposed for the owner**; until it is
  accepted the boundary claims of skills/0004 (Answer, §§ 3–11, the Functions table, the dated notes in skills/0002
  §§ 4 and 8, experiments) are `[I]`, and the refusal paths that return are `[C]` (§ 2). ADR-0021 (b) needs the call
  site checked: the review checked it from the kept outputs (`workspace/logs/skills-cat-9a-review/callsites.txt`
  `8ea8058b…`, one site per function and boundary); **from batch 9b the checker asserts the return address of each
  observed boundary.** **Ruling (2):** one finding file per batch, numbered in landing order (Outputs above).
  Negative controls: homing's 22 failures of 1 500 (sizes left out of the distance) are enough to show its checker
  live (ADR-0015 (4)), since the size term decides the threshold only near `Param2`; the step's sign and `max(Param3,
  1)` are separated by the 208 step cases, not by the control. From 9b, a family whose control fails fewer than 50
  cases adds a second perturbation on another claim. Batch 9b may start now (with the call-site check); its boundary
  claims follow ADR-0021's fate like 9a's.
- **2026-10-20 — Phase 1 batch 9b landed for review (reverser, `lane/p46m2`, static, no harness).** Missile server do
  functions 19–36 and damage functions 1–14: 30 entries, 28 read and the two tier-A ones (do 23, damage 3) emulated
  too ([skills/0005](../findings/skills/0005-missile-do-19-36-damage.md)). Draws before the boundaries: do 28 (re-seed
  from `+0x28`, two `RNG_Range`), do 30 (two `RNG_Range` on the **target unit's** seed), do 34 and 35 (re-seed, one
  inline step), do 25 (9a's `0x005A9820`); damage 3, 5, 12, 13, 14 on the missile seed; no other. Raised by emulation
  (run:2026-10-20-cat-emu-9b, `tools/skills_catalogue_emu.py --batch 9b`): 13 families, 17 100 cases, 0 mismatches,
  every family with two failing negative controls; **the checker asserts each observed boundary's call site** (a site
  control fails all 8 762 matched boundary cases). Tags as the `lane/p46m1` ruling: the damage functions (all but
  damage 8's overlay call) and the do functions' refusal paths that return are `[C]`; the do functions' maps up to
  their boundary are `[I]` marked "(ADR-0021)" in the finding, to flip on the owner's acceptance. Surprises: do 21,
  22, 23, 25, 26 test `SubMissile1 != 0` (a blank −1 passes); do 28's debris point goes in the creation's target words;
  damage 1/12's 100 cap, which the decompile drops, matters only for a negative physical share; a rabies contagion
  carries an end frame (`+0x28 − frame` is its poison length); do 19 runs Redemption's corpse callback, do 36 spawns
  `tyrael3` under quest 36. Review request
  [to the architect](../backlog/archive/2026-10-20-reverser-architect-lane-p46m2-review-plan-0046-batch-9b.md); column
  readers [to the archivist](../backlog/2026-10-20-reverser-archivist-plan-0046-9b-missiles-skills-column-readers.md).
- **2026-10-20 — `lane/p46m2` review (architect): batch 9b accepted with fixes (5: misread 3, overclaim 2).**
  Checks (kept in `workspace/logs/skills-cat-9b-review/`, `manifest.sha256` `02466fbf…`): the run's
  `sha256sum -c manifest.sha256` passes (68 files); `check rabies reseed9b` from the kept outputs gives `check.txt`'s
  lines (site lines, both controls, outcomes); `cases --batch 9a` and `--batch 9b` regenerate every kept case file byte
  for byte, and `check`/`static --batch 9a` reproduce 9a's kept files byte for byte (tool `540cf98e…`);
  `EmuBoundary.java` (`286393aa…`) and `EmuTrace.java` (`3255db0c…`) are as on `main`. Objdump: do 28
  `RNG_SeedInit(m+0x20, MISSDATA_GetSeedLow(m))` at 0x005AFCB7, two `RNG_Range(m+0x20, 2r + 1)` at 0x005AFCC5 and
  0x005AFCD7 (x first); do 30 its two `RNG_Range(2·Param2 + 1)` at 0x005B0163 and 0x005B0172 with ECX =
  `GameFindUnit`'s result `+ 0x20` (the target's seed); damage 14 `RNG_Range(m+0x20, 100)` at 0x005AD688 and `or WORD
  PTR [pkt+4], 0x8` on `<` chance. **Fixes, made in skills/0005:** (1) do 28 stores `+0x28 = RNG_GetLow` *before* its
  `MissileCreate` (0x005AFCEB, and the checker compares it), not after (misread); (2) damage 14 sets result `0x8`, not
  "bit 8" (misread); (3) do 30 does not reset the frames left as do 20 does; the summary's "does the same" is narrowed
  (misread); (4) the return values of do 20 and 30, do 19's and do 36's code after their calls and do 27's third
  argument (not compared) were inside boundary claims that would have flipped whole; split out as `[I]` (overclaim);
  (5) damage 12 "replaces the whole packet" narrowed to the fields `PacketClearDamage` zeroes (overclaim).
  **Ruling (do 31's control):** the `CollideKill` control in place of `Explosion` is accepted: the `Explosion` term sets
  only bit 1 of a value whose bit 0 alone is tested (0x005B02F9) and which the hit function's value replaces, so no
  output depends on it; the case writer varies the flag at random and every case matches. The term stays `[I]` (a
  code reading with no observable effect), now its own bullet in § 10. **Ruling (requested checks):** damage 12's
  reading is accepted as narrowed in (5); the stat-list `+0x18` end-frame reading stays `[L]` (open question; no
  writer of that word was read). **ADR-0021** (accepted by the owner 2026-10-20): every "(ADR-0021)" claim of
  skills/0005 meets (a) (no patch; `observe` entries reached by the program's flow), (b) (boundary and return address
  asserted per case, the site control failing 8 762 of 8 762) and (c) (blocks compared whole, 0x5C bytes; registers and
  stack arguments; `MissileData` masked to the written words; the seeds the code steps); for do 30 the untouched
  seeds (missile, owner, decoy) are not in the model, so the review checked them from the kept `rabies.out` (270 of
  270 unchanged over the 90 creation cases). **18 claims raised to `[C]`** (the Answer's four boundary bullets and
  §§ 3 (two), 4, 5, 6, 7, 8, 9, 10, 11, 12, 14 (damage 8's call), 17, 18), each now naming its boundary and call
  site; the code after each boundary is not covered and stays `[I]` (raised in part: do 22's and do 31's second
  creation, do 20/30's return values and do 20's path-case `SetRemaining`, do 28/34/35's code after the creation or
  `PathPlan`, do 30's state copy, do 27's area hit, do 19's callbacks, do 36's spawn and room pin, do 27's packet
  pointer). Kept `[I]`: the `Explosion` term (no output), the Functions table's names, the stock-row bullets, and the
  reading-only bullets of §§ 6, 17 and 18. skills/0003 § 6's dated note and the experiments conclusion updated.
  Review request closed
  ([archive](../backlog/archive/2026-10-20-reverser-architect-lane-p46m2-review-plan-0046-batch-9b.md)); ledger rows
  added. **Batch 9c may start** (missile hit 1–29), with 9b's checker conventions (call site asserted, two controls per
  family) and the untouched-seed check added to the model wherever a family writes seeds it should not step.
- **2026-10-20 — ADR-0021 accepted by the owner (architect, `lane/adr21`, no run).** The owner accepted
  [ADR-0021](../adrs/0021-observed-boundaries-in-emulation.md) (observed boundaries in emulated reproduction; amends
  ADR-0015 (1) and (3)). As the 9a review specified, the batch 9a claims held at `[I]` pending it return to `[C]`
  without a re-run, (b) supplied by the review's call-site check (`callsites.txt` `8ea8058b…`), each naming its
  boundary and covering nothing after it: [skills/0004](../findings/skills/0004-missile-do-1-18.md) Answer 6 bullets
  (draws, sub-missiles, Frozen Orb, scatter, towerchestspawner, homing), §§ 3–11 11 statements (§ 3 1, § 4 1, § 5 1,
  § 6 1, § 7 2, § 8 1, § 9 2, § 10 1, § 11 1), the Functions table 16 rows (do 7's row stays `I`, gates `[C]`, re-plan
  `[I]`), with § 2 recording the acceptance and the return address of every boundary; the dated notes in skills/0002
  §§ 4 and 8; the experiments conclusion; the spec-writer backlog entry on quests/0001's open question. Kept `[I]`:
  do 7's re-plan, do 13, what follows `COLL_CellTestAt` in `0x005A9820`, the gold item after the free spot, do 16's
  stores after the plan, do 18's return value, and everything after a boundary. Batch 9b's `[I] (ADR-0021)` claims are
  its own review's. Evidence rules and the reverser's `emuboundary` text now cite ADR-0021.
- **2026-10-20 — Phase 1 batch 9c landed for review (reverser, `lane/p46m3`, static, no harness).** Missile server
  hit functions 1–29: 25 entries, all read ([skills/0006](../findings/skills/0006-missile-hit-1-29.md); hit 2, 3, 14,
  17 tier A, 3, 14, 17 emulated too, 2 not). Draws before the boundaries: hits 1, 9, 13 roll the missile's `EType` on
  its seed; hit 7's heal one `RNG_RangeB` (and the `MissileElemRoll` fallback) on the missile's seed; no other; no
  case steps the owner's or the target's seed. Raised by emulation (run:2026-10-20-cat-emu-9c,
  `tools/skills_catalogue_emu.py --batch 9c`): five families, 8 400 cases, 0 mismatches, the call site of every
  boundary asserted (site control 3 941 of 3 941), two to six negative controls per family, **the three seeds
  compared in every case** (the untouched-seed check of the `lane/p46m2` review, with a control on it) and the packet
  or context behind a pointer argument compared by content. Returning paths `[C]`; the maps up to `AreaHitAt`,
  `BuildDamage`, `MissileCreate`, `STATLIST_Alloc`, the flee call and the other boundaries `[C]` (ADR-0021), code
  after them `[I]`. Surprises: hit 44 takes a negative `sHitPar1` as its radius and has no owner test; hit 7 heals
  only the owner's pets (`TargetPet`) or allies, ending without damage, and passes through non-undead (4); hit 29
  returns 2 (damage, flies on) until its frames run out; hits 16/19 apply the aura stats to the search's result, 0
  for a new list; hit 21's state test admits the States count; hit 4 reads all four `HitSubMissile` slots (the
  stride the table doc had as `[L]`). Corrections in skills/0003 § 6 (hits 2, 3, 14, 17, 22, 44). Review request
  [to the architect](../backlog/archive/2026-10-20-reverser-architect-lane-p46m3-review-plan-0046-batch-9c.md) (three
  rulings: register values at a boundary, two weak controls, hit 2 unemulated); column readers
  [to the archivist](../backlog/2026-10-20-reverser-archivist-plan-0046-9c-missiles-skills-column-readers.md).
- **2026-10-20 — `lane/p46m3` review (architect): batch 9c accepted with fixes (2: overclaim 1, other 1).**
  Checks (kept in `workspace/logs/skills-cat-9c-review/`, `manifest.sha256` `b3761c63…`): the run's
  `sha256sum -c manifest.sha256` passes (28 files); the lane's tool (`412e3e5c…`) regenerates every kept case, memory
  and expectation file of 9a (27), 9b (39) and 9c (15) byte for byte and reproduces the three batches' `check.txt` and
  `static.txt` byte for byte from their kept outputs; `re/ghidra_scripts/` is as on `main` (`EmuBoundary.java`
  `286393aa…`). Objdump: hit 7's heal `RNG_RangeB(ECX = m+0x20, EDX = (calc2 << 8) − (calc1 << 8))` at 0x005AA0A6
  (calc1 at Skills `+0x138`, calc2 at `+0x13C`, both `shl 8`), `+ lo`, and on `≤ 0` (`jg` at 0x005AA0B1)
  `sub_005A8910_MissileElemRoll(EAX 22; m, 21, −1)` at 0x005AA0BD, then `UnitSetStat(unit, 6, min(stat 6 + h, max
  life), 0)` at 0x005AA0E7; hit 44's `mov edi, [rec+0x4C]; test; jne` at 0x005A9E63–0x005A9E6D (non-zero, no owner
  test: EBX = `UnitGetOwner` is never tested), EDI the radius and EBX the y position at `BuildDamage` 0x005A9F47;
  hit 3 passes ECX/EDX through to hit 44 with unit 0 and returns 0 for a unit; hit 29's frames-left `test; je` at
  0x005ABB5A (`!= 0` returns 2 before the owner test). From the kept cases: 7 of hit 44's 33 negative-`sHitPar1`
  cases have no Skills row, so the non-zero test is decided by the boundary reached, not only by EDI. **Gate:** the
  lane's files carry no W1 warning (the gate's W1 check over `docs/findings/skills/` gives none); the 11 W1 warnings
  of the fast tier are `main`'s, in `docs/specs/data/excel.md`, outside this lane. **Ruling (1), register values:**
  ADR-0021 (c) admits "every argument the claim uses, in registers and on the stack" and every byte written before
  the call; a callee-saved register that is not an argument of the boundary is neither, and condition (3)'s map does
  not list it. Its use as `AreaHitAt`'s radius also needs `BuildDamage` to preserve it, which is callee behaviour. So
  the radius values of hits 24, 44 and 14 stay `[I]`, compared and matching in every case. The tests that choose
  between returning and reaching the boundary stay `[C]` (ADR-0021). Route to `[C]`: a run that reaches `AreaHitAt`
  (with `BuildDamage` emulated, or the harness); widening (c) to non-argument registers would take an amendment the
  owner accepts, not a review. **Ruling (2), weak controls:** enough. The 9a rule asks a family whose control fails
  fewer than 50 cases for a second perturbation; `holy9c` has `always2` (112) and `create9c` has `vel` (146), `ge0`
  (80) and `count0` (54). The 8 (undead mask `0x18` against `0x08`) and the 4 (`left != 0` against `> 0`) cases each
  decide their claim deterministically, not by chance (reverser review-fixes 10); `holy9c`'s hit-7 monster cases carry
  mask values `0x08`, `0x10` and `0x18` alike (37 to 44 each). No re-run. **Ruling (3), hit 2:** accepted for this batch.
  It is tier A, read by plan 0045, and tagged `[I]` here and in skills/0003 § 6, so nothing is raised on it. Its ring
  of `MissileCreate` calls fits the same observed-boundary method as hits 25 and 29, so the "the rest are named with
  the reason" clause of Phase 1 is met only by deferral. **Its emulation is carried to batch 9d.** **Fixes, made in
  the documents:** (1) the three radius values split out of their `[C]` (ADR-0021) bullets into one `[I]` bullet
  (skills/0006 § 3, § 4's hit 44 and hit 14, the Answer, skills/0003 § 6's 9c note, the experiments conclusion)
  (overclaim); (2) hit 2's non-emulation given its destination (batch 9d) in skills/0006 § 16 and the experiments
  conclusion (other). Review request closed
  ([archive](../backlog/archive/2026-10-20-reverser-architect-lane-p46m3-review-plan-0046-batch-9c.md)); ledger rows
  added. **Batch 9d may start** (missile hit 31–59 and row 568's 64 948), with 9c's conventions (call site asserted,
  three seeds compared, pointed-to bytes compared, two controls per family). It also emulates hit 2, and it tags any
  value read from a non-argument register at a boundary `[I]`.
- **2026-10-20 — Phase 1 batch 9d checkpoint (reverser, `lane/p46m4`, static, no harness; paused for the owner, resume
  note).** Read from objdump and the lane's Ghidra copy (`workspace/ghidra-p46m4`): all 24 hit functions 31–59 of the
  batch (table entries checked: 30, 34, 41, 42, 46, 49 and 60–70 are null, count 71) and hit 2 (tier A, carried from
  9c), with their callees `0x0056D4E0` (a nova of creations, fatal path for `(n − 1)/5 > 7`), `sub_005A9370_MissSubRing16`,
  `SKILLS_GetPhysMin/Max`, `SKILLS_GetElemLen`, `SKILLS_FindUnitSkill`, `0x005D5BF0`, `0x005B3570`, `0x005C7DB0`.
  Draws before the boundaries found so far: hit 31 (the `EType` roll, missile seed), hit 43 (one `RNG_RangeB` of
  `PhysMax − PhysMin`, missile seed), hit 58 (re-seed from `SubX`, two `RNG_Range(2r + 1)`); hit 40's callee re-seeds
  and draws (after its boundary). Surprise to confirm: hit 52 tests `HitSubMissile1` but leaves the block's class
  word 0. Tool: the 9d section of `tools/skills_catalogue_emu.py` (`--batch 9d`; families `heal9d`, `create9d`,
  `nova9d`, `area9d`, `event9d`, 8 400 cases; static pins and the hit-table read scan for row 568) is written and its
  case writers run; `cases --batch 9c` still regenerates 9c's kept files byte for byte. **Not yet done:** the
  emulation runs, the check (models untested against the emulator), the 9a/9b check/static reproduction, the finding
  (`docs/findings/skills/0007-missile-hit-31-59.md`), symbols, review request, gate. Kept so far:
  `workspace/logs/skills-cat-9d/rows.txt` (stock rows) with `manifest.sha256`. **Resume:** run the five families
  under EmuBoundary (procedure of 9c, `GHIDRA_PROJ_DIR=workspace/ghidra-p46m4`), fix model mismatches, then write the
  finding and the rest as the batch prompt lists.
- **2026-10-20 — Phase 1 batch 9d landed for review (reverser, `lane/p46m4`, static, no harness; resumed from the
  checkpoint above).** Missile server hit functions 31–59: the 24 filled entries (30, 34, 41, 42, 46, 49 and 60–70
  null, count 71), all read; 23 emulated (hit 44 is 9c's) and **hit 2** (tier A, carried from 9c by ruling 3)
  ([skills/0007](../findings/skills/0007-missile-hit-31-59.md)). Draws before the boundaries: hit 31 (the `EType`
  roll), hit 43 (one `RNG_RangeB(PhysMax − PhysMin)`), hit 58 (re-seed from x, two `RNG_Range(2r + 1)`), all on the
  missile's seed; no case steps the owner's or the target's. Raised by emulation (run:2026-10-20-cat-emu-9d,
  `tools/skills_catalogue_emu.py --batch 9d`, `check.txt` `9ec69cf5…`, `manifest.sha256` `6fa68cd0…`): five
  families, 8 400 cases, 0 mismatches, 28 boundary/call-site triples asserted (site control 3 796 of 3 796), the three
  seeds compared in every case, the `MissileCreate` block and hit 47's packet compared by content, two to six
  negative controls per family (each family has one failing 53 or more); no model compares a non-argument register
  (ruling 1 of the 9c review). Fixes during the run: `event9d`'s object lacked its type word (58 hit-35 cases), the
  rabies length edge was never hit (writer now targets it), `area9d` had no control reaching 50 (`unit56` added), one
  static pin off by one instruction. The same tool regenerates 9a/9b/9c's case files and reproduces their `check.txt`
  and `static.txt` byte for byte (`repro.txt`). Surprises: **hit 52 (blade fury) creates Missiles class 0 (`arrow`)**,
  its block's class word never written; hit 38/45's nova helper asserts (`0x00408090(0xF0D)`) for `n ≥ 41`, which
  stock hit 38 reaches at missile level 20; hit 43 (healing vortex) heals any hit unit with no owner or ally test;
  hit 47 (molten boulder) explodes only on MonStats2 `large` monsters or at the end of life; hit 39 spawns on every
  call; the Skills `Kick` maximum divides by 3, not 4 (`[I]`). Row 568's 64 948: the four hit-table reads sit behind a
  signed `test ax, ax; jle` (scan `[C]`, meaning `[I]`). Tags: 38 `[C]`, 10 `[I]`, 4 `[L]` bullets; 28 symbols added
  (`I`). Dated notes in skills/0003 § 6 and skills/0006 § 16. Review request
  [to the architect](../backlog/archive/2026-10-20-reverser-architect-lane-p46m4-review-plan-0046-batch-9d.md); column
  readers [to the archivist](../backlog/2026-10-20-reverser-archivist-plan-0046-9d-missiles-skills-column-readers.md).
- **2026-10-20 — `lane/p46m4` review (architect): batch 9d accepted with fixes (4: overclaim 2, misread 1, miscount
  1).** Merged `main` (`9ef5f84`) first; no conflict, `backlog.py archive` moved nothing; 28 new symbols, no address
  or name twice in `re/symbols.csv` after the merge. **Re-run:** `sha256sum -c manifest.sha256` passes (29 files);
  `check --batch 9d` and `static --batch 9d` from the lane's tool (`da004a4b…`) regenerate `check.txt` (`9ec69cf5…`)
  and `static.txt` (`d909b72d…`) byte for byte; tag counts 38 `[C]`, 10 `[I]`, 4 `[L]` recounted. **Read against
  objdump:** hit 52 (0x005AC940–0x005ACA4F), hit 2 (0x005A9D80–0x005A9E05), `MissNovaCreate`'s head
  (0x0056D4E0–0x0056D539), `0x00408090`, `sub_00644C20_SkillKickDamage` (flag 0 divides by 3: `imul 0x55555556`),
  and the four hit-table reads (each straight-line: `movzx eax, word [rec+0x0E]; test ax, ax; jle; movsx; cmp
  [0x0073C83C]; jge; read`). **Ruling (1), hit 52:** the block word is `[C]` (ADR-0021): the block sits at
  `ebp−0x60`, is zeroed, and no instruction stores to `ebp−0x50` (`+0x10`); the emulated block matches in all 173
  creation cases. The control `cls52` fails all 120 cases with `HitSubMissile1 ≠ 0`; in the other 53 the word is 0
  and the two readings agree (the finding said "120 of 120 creation cases"). That the missiles are row 0 (`arrow`)
  is `MissileCreate`'s reading of `+0x10` (skills/0002 § 2), callee behaviour after the boundary, so it stays `[I]`
  under ADR-0021's "what they mean to the callee keeps its own tag". Whether the game shows arrows stays under Open
  questions (a harness check). **Ruling (2), the nova helper:** `[C]` up to the call accepted (boundary `Fatal` at
  return address 0x0056D50C, 153 cases; control `fatal8` 53). But `0x00408090` is not an assertion-message helper: it
  is `mov eax, [esp]; ret`, which returns its own return address. The `0xF0D` pushed before it is the third argument
  of `0x00408A60(0x006CC837, that address, 0xF0D)`, which is followed by `0x00681E09(−1)`. All of that is after the
  boundary, `[I]`. The finding now says "the fatal path's `0x00408090`" throughout, as rng/0002 and the data
  findings name the trio. **Ruling (3), weak controls and hit 2's ring:** enough, under 9c ruling 2. `nofloor31` (2),
  `nofloor55` (3) and `pct100` (6) each fail on every case whose input decides the claim (a negative roll, a drain
  under 1, a percent above 100), deterministically (reverser review-fixes 10), beside `nocap43` 73 and `ownseed` 140
  in `heal9d`. Hit 2's source choice is one `test ebx, ebx; jne; mov ebx, edi` (0x005A9DBF–0x005A9DC3). The 3
  end-of-life cases compare the source pointer and its position, which a wrong reading could not match by chance,
  and `ring_self` fails all 120 unit cases. No re-run. **Ruling (4), row 568:** the split holds. The scan
  (`tabread_scan`, every `.text` operand naming `0x73c840`, lea and push included) is `[C]`; my read of the four
  sites agrees. That the tested word is that row's `pSrvHitFunc` stays `[I]`: the layout (`+0x0E` u16) is `[C]` in
  [Missiles](../tables/Missiles.md), but which record reaches sites 2–4 (`[ebp−4]`, `[edi]`) is the reading. Route to
  `[C]`: an emulated `MISSILE_HitUnit` case with the word at 64 948. **Ruling 1 of the 9c review held:** no claim
  rests on a non-argument register. ESI at the kick boundary is an argument and is not claimed. **Fixes, made in the
  documents:** (1) the Answer's creation bullet no longer carries hit 52's "creates class 0 (`arrow`)", nor hit 51's
  and hit 52's later creations, under `[C]`; they are marked after, `[I]` (overclaim); (2) § 5's hit 52 bullet moves
  the row-0 meaning after the boundary, citing skills/0002 § 2 (overclaim); (3) `0x00408090` is described as what it
  is in the Answer, § 2, the Functions table, the `nova9d` row, § 7 and Open questions, and in the experiments
  conclusion (misread); (4) `cls52`'s count is "120 of the 120 with `HitSubMissile1 ≠ 0`, of 173" (miscount). Review
  request closed
  ([archive](../backlog/archive/2026-10-20-reverser-architect-lane-p46m4-review-plan-0046-batch-9d.md)); ledger rows
  added. **The next batch (sorceress) may start**, with 9c and 9d's conventions. One addition: a meaning that a
  boundary callee gives to a compared argument or block word (a class, a mode, a monster id) is stated after the
  boundary, `[I]`, and is never part of the `[C]` sentence.
- **2026-10-20 — Phase 1 batch `sor` landed for review (reverser, `lane/p46m5`, static, no harness).** The sorceress
  start functions 11–14 and do functions 17–29 and 144: 18 entries, all read; 17 emulated (do 27 Teleport read only)
  with the Inferno helpers `0x005C8CA0` and `0x005C8E30` ([skills/0008](../findings/skills/0008-sorceress.md); tier A
  do 18, 20, 22, 28 emulated too). Draws before the boundaries: do 21 (Telekinesis) only, one
  `RNG_Range(caster seed, 100)` against `Param2`; no case steps the target's seed. Raised by emulation
  (run:2026-10-20-cat-emu-sor, `tools/skills_catalogue_emu.py --batch sor`, `check.txt` `961ccef7…`,
  `manifest.sha256` `83d7c0f9…`): six families, 8 500 cases, 0 mismatches, 27 boundary/call-site triples asserted
  (site control 2 977 of 2 977), the caster's and the target's seeds compared in every case, the blocks passed by
  pointer compared by content, two to six negative controls per family (each family has one failing 79 or more);
  `UnitsHostile` and `UnitsSameParty` run emulated with the alignment rule. The same tool reproduces 9a–9d's kept
  files byte for byte (`repro.txt`). Surprises: by the alignment rule (`0x00650D70`) a player and a monster with no
  state-105 list are not hostile (open question); Inferno's channel lives in state 12's list and the used skill's
  `+0x18` (a monster's end frame `frame + calc2`); Thunder Storm's node `+0x18`/`+0x1C` hold the last struck guid and
  the re-arm switch; Hydra spawns classes `summon + 0..2`; do 22's velocity is read through a second missile table at
  `0x0096C794`; start 11's mana test covers any caster type. Tags: 34 `[C]`, 10 `[I]`, 4 `[L]` bullets; 25 symbols
  added (`I`). Dated note in skills/0003 § 5. Review request
  [to the architect](../backlog/archive/2026-10-20-reverser-architect-lane-p46m5-review-plan-0046-batch-sor.md); column
  readers [to the archivist](../backlog/2026-10-20-reverser-archivist-plan-0046-sor-skills-missiles-column-readers.md).
- **2026-10-20 — Batch `sor` reviewed (architect, on `lane/p46m5` at `d240aa5`): accept with fixes.** `main` had not
  moved past `43d534c`, so no merge. Re-run from the lane's tool (`7525830c…`): `check --batch sor` and
  `static --batch sor` reproduce `check.txt` `961ccef7…` and `static.txt` `91a6de74…` byte for byte;
  `sha256sum -c manifest.sha256` (`83d7c0f9…`) passes. Spot reads against objdump: do 21's draw and flag
  (`0x005C99C0`–`0x005C99DC`: `RNG_Range(caster+0x20, 0 + 0x64)`, `SkillGetParam2`, `jge` past the flag), `UnitsHostile`
  (`0x00554200`), the alignment rule (`0x00650D70`, `0x006259B0`), `0x00663270` and do 27 (`0x005CA360`–`0x005CA3DD`)
  all match the finding; the 27 site lines and every control are in `check.txt`; tags recounted 34 `[C]` / 10 `[I]` /
  4 `[L]` bullets as filed. **Rulings:**
  (1) **Do 21's draw holds at `[C]`.** The model compares the flag `[ebp−8]` as a pre-call byte at the `SkillRollPhys`
  boundary and both seeds; the writer puts 35 % of the reaching cases at `Param2` or one off it and draws `Param2` from
  negative and full 32-bit values too, so `stun_le` (23) decides `<` against `≤` at the edge and the signed compare
  is exercised; `tseed` fails all 93 draw cases. What the flag does (`|= 9`, a stun) is after, `[I]`, as filed.
  (2) **`UnitsHostile` and `UnitsSameParty` emulated is accepted**: they read only declared records (unit, owner link,
  stat lists) and call nothing undeclared, so running them is condition (1)'s first treatment, and the 9c boundary
  list is a list, not a rule. The alignment reading is right by objdump: `0x006259B0` gives 0 for no unit or no
  stat list, 2 for a type above 1, else stat 172 of the state-105 list (0 without one); `0x00650D70` calls two units
  allied when both are 0 or both 2, and `UnitsHostile` returns the negation. The consequence for a player and a
  monster without the list stays `[I]` plus its Open question, which is enough for the finding; **no harness check is
  needed for the finding, but the Phase 3 spec may not state the play consequence** ("Telekinesis refuses
  monsters") until a static read of who allocates the state-105 list (its writers) says which units carry it in play;
  the spec states the rule as a map only. One wording fix: the missile-owner branch of `UnitsHostile`, never
  exercised, sat inside the `[C]` bullet.
  (3) **The `.data` inputs are admitted, but not on the writer scan.** Under the S1e review's ruling 3 (last
  sentence), tables set on purpose as inputs of a claim that is a map from their bytes need no justification; that
  is the ground here. The writer scan cited for them is wrong: `static_sor` (like 9a's and 9b's scans) matches only
  `PTR`-form stores, so it misses `mov ds:0x0096C794, eax` (`0x00663139`, `DATATBLS_LoadTable("missiles", 0x1A4)`'s
  result) and `mov ds:0x0096C8AC, eax` (`0x006180C5`), and the counts written through pushed pointers (`0x00663115`,
  `0x00617FF8`). 9a's and 9b's scans of the calc function counts `0x007457AC`/`0x00745848` stand: a full objdump grep
  finds only reads of either address, no `moffs` store and no address taken. **Condition for the next batch:** any
  writer scan it cites also matches the `moffs` store form and immediate pushes or `mov reg, imm` of the address,
  or it does not cite one.
  (4) **The weak controls are accepted.** Each fails exactly on the edge class the finding names (`nostate`,
  `town14`, `dist_ge`, `ign1c`, `charge_a`), the writer places that class on purpose, and a wrong reading of the
  claim could not match those cases by chance; every family also has a control of 79 or more. A weak control stays
  admissible only with its deciding class named, as here.
  **Do 27 (§ 9) read only is accepted at `[I]`.** The reading matches objdump; the stated reason is thin
  (`LEVELS_GetRecord` is a table read the emulator could serve, and a boundary at `0x006229F0`/`UnitTeleport` would
  give `[C]` on the `Teleport` byte test), so Phase 3 keeps § 9 `[I]` or a later batch emulates it; not a fix.
  **Earlier rulings held:** no claim rests on a non-argument register (9c ruling 1); callee meanings sit after the
  boundary in the body and the Answer (9d ruling, reverser review-fixes 13).
  **Fixes, made in the finding:** (1) § 2's inputs bullet no longer rests on the writer scan; it cites ruling 3 and
  says why the scan is no justification (misread); (2) a new § 2 `[I]` bullet records the load-time writers of
  `0x0096C794` and `g_pDifficultyLevels`, and the `0x0096C794` Open question narrows to whether the second
  `missiles` load equals `DataTables+0xB64` (counted with (1)); (3) `UnitsHostile`'s missile branch moves out of the
  `[C]` sentence as not exercised (overclaim); (4) § 7 states `Vel` and `VelLev` are read unsigned (`movzx`) and
  § 9 that do 27 returns `UnitTeleport`'s value, 0 without a room or a Levels record (omission). Counted: 3
  (misread 1, overclaim 1, omission 1). Tags after the
  review: 34 `[C]`, 11 `[I]`, 4 `[L]` bullets. Review request closed
  ([archive](../backlog/archive/2026-10-20-reverser-architect-lane-p46m5-review-plan-0046-batch-sor.md)); ledger rows
  added. **The next batch (amazon) may start**, with 9c, 9d and `sor`'s conventions and ruling 3's condition on
  writer scans.
- **2026-10-20 — Phase 1 batch `ama` landed for review (reverser, `lane/p46m6`, static, no harness; resumed after the
  first session was killed by the system's out-of-memory handler, no commit lost).** The amazon start functions 4–10
  and do functions 6, 7, 8 and 10–16: 17 entries, all read and all emulated ([skills/0009](../findings/skills/0009-amazon.md);
  tier A start 4, start 5, do 7, do 8 emulated too). Draws before the boundaries: none; no case steps the caster's or
  the target's seed (start 10's elemental `RNG_RangeB` comes after its hit test). Raised by emulation
  (run:2026-10-20-cat-emu-ama, `tools/skills_catalogue_emu.py --batch ama`, `check.txt` `03a40fde…`,
  `manifest.sha256` `6a3181d8…`): six families, 8 300 cases, 0 mismatches, 33 boundary/call-site triples asserted
  (site control 4 190 of 4 190), both seeds compared in every case, blocks and packets compared by content and, where
  a boundary sits inside a helper, the batch function's frame words compared at their stack address; two to four
  negative controls per family (each family has one failing 96 or more; the smallest, `nonorm`, 51). The calc count's
  writer scan matches `moffs` stores and immediates too (ruling 3's condition): 0 and 0. The same tool reproduces
  9a–9d and `sor` byte for byte (`repro.txt`). Surprises: **start 6 and start 10 pass 0 as `COMBAT_MeleeHitTest`'s
  AR argument** (Power Strike's `ToHit` 20/12 does not reach it; combat/0001 note); **do 15 and
  do 16 leave `SpawnOwnedMonster`'s `+0x24` word unwritten**, so it carries the mode (Dopplezon) or the Skills record
  pointer (Valkyrie); **do 13 (Fend, Zeal, Fury) returns 0 on every path**; do 8's fan steps perpendicular to the
  caster–point line, not along it (skills/0003 § 5 note); start 4 has no skill-record test. Tags: 31 `[C]`, 13 `[I]`,
  4 `[L]` bullets; 22 symbols added (`I`). Review request
  [to the architect](../backlog/archive/2026-10-20-reverser-architect-lane-p46m6-review-plan-0046-batch-ama.md); column
  readers [to the archivist](../backlog/2026-10-20-reverser-archivist-plan-0046-ama-skills-column-readers.md).
- **2026-10-20 — Batch `ama` reviewed (architect, on `lane/p46m6` at `a6eaf75`): accept with fixes.** `main` had not
  moved past `9b5dfa8`, so no merge. Re-run from the lane's tool (`69c01d13…`, unchanged since the checkpoint
  `9d0263c` that committed the killed session's tool section): `check --batch ama` and `static --batch ama` reproduce
  `check.txt` `03a40fde…` and `static.txt` `b1b51e31…` byte for byte; `sha256sum -c manifest.sha256` (`6a3181d8…`,
  37 files) passes. Spot reads against objdump: start 6 and start 10 push `0, 0` before `COMBAT_MeleeHitTest`
  (`0x005DA9A5`, `0x005DB08E`); start 10's `RNG_RangeB(caster+0x20, max − min)` (`0x005DB0C7`) sits inside the
  hit branch after the test; start 4 (`0x005DA8B0`–`0x005DA8E1`) has no record test; do 8's fan
  (`0x005DB4E8`–`0x005DB676`: the perpendicular step, the truncating halves, `0x820` with `0x10000` set for the first
  outer group and cleared for the centre, `+0x44` = calc2); do 6's block (`0x005DB1FF`–`0x005DB2A8`); do 15's and do
  16's blocks (`ebp−0x34`/`ebp−0x30`, the last word the `&mode` slot `ebp−0x10` and the record slot `ebp−0xC`
  stored at `0x005DC210`; no other store reaches either); do 13's every exit runs through `xor eax, eax` at
  `0x005DBE3F` (seven jumps to `0x005DBE3D`/`0x005DBE3E`, one `ret`). The calc count's scan: a full objdump grep of
  `0x7457ac` gives the seven `mov reg, ds:` reads and nothing else, so the scan meets ruling 3's condition of the
  `sor` review. Tags recounted 31 `[C]` / 13 `[I]` / 4 `[L]` bullets as filed; the 22 symbol rows are new addresses
  and names, all `I`, evidence 0009; gate green. **Rulings:**
  (1) **Frame words at a nested boundary are admissible as filed.** A word the batch function wrote to its own frame
  before calling the helper that reaches the boundary is a "byte written before the call that the claim uses"
  (ADR-0021 (c)); the case fixes the entry `ESP`, so the absolute address is the `EBP`-relative slot, and a function
  whose frame sat elsewhere would fail the compare, not pass it. One gap: the site check (b) names the boundary's
  return address inside the helper, not the batch function's call of the helper. It holds here because each batch
  function calls each such helper from one site (objdump: `0x00623C60` once in do 8, do 10 and do 12; `0x0056E510`
  once in start 9 and do 13; `0x0056C4E0` once in start 4 and start 8; `0x0056BC80` once in start 8 and start 9).
  **Condition from the next batch on:** a nested boundary's case also compares the helper's return address into
  the batch function at its absolute stack slot, or the finding shows from objdump that the helper has one call
  site in that function. The words' later use (the creations' targets on the armed path) stays after, `[I]`.
  (2) **Start 6 and start 10's `0` is `[C]` as a value**, with the AR-percent meaning and its consequence for
  Power Strike's `ToHit` `[I]` after the boundary plus the Open question, in the body and in the Answer (reverser
  review-fixes 13). The combat/0001 dated note is right and scoped (the argument values `[C]` for start 6, 7, 10 and
  do 7; do 13's `SKILLS_GetToHit` is a reading, past `InMeleeRange`).
  (3) **The summons' `+0x24` word is `[C]` as a value.** The block is compared by content at `SpawnOwnedMonster`, the
  writer varies the mode and the record pointer is a scratch address, and `w24_zero` fails 715 cases; "no store
  fills it" agrees with objdump. What the spawn makes of it stays the Open question.
  (4) **`srvmissileb` is `[C]` for a caster with no inventory only, as filed.** With `+0x60` = 0, `0x00623990`
  returns 0 before its inventory call and `0x00623C60` gives word 0; no case gives word 1, so the `cmp eax, 1` stays
  `[I]`. The skills/0003 note had put "taken for a weapon word ≠ 1" inside its `[C]` sentence (fix 1).
  **Also checked:** start 10's elemental draw is `[I]` in the Answer, § 4 and the run record; the Answer's
  "do 13 returns 0 on every path" sits under "After, `[I]`" (the emulated refusal paths return 0 too; the all-paths
  claim is the objdump reading above). **Earlier rulings held:** no claim rests on a non-argument register (9c
  ruling 1); callee meanings sit after the boundary (9d ruling); `sor`'s conventions and its ruling 3.
  **Fixes, made in the documents:** (1) skills/0003 § 5's dated note and skills/0009's Corrections scope
  `srvmissileb` to word 0 and leave the test against 1 `[I]` (overclaim); (2) skills/0003 § 5's Multiple Shot row
  still said "start points stepped along it"; the row now says perpendicular, from the point less half the fan,
  pointing at the note (reverser review-fixes 12; stale cross-reference); (3) skills/0009 § 6's after-text named the
  weapon word "a bow" from the stock missile names, a meaning from data alone; it now points at the Open question
  (overclaim); (4) the archivist column-reader entry called `calc1` "the missile count" under a `[C]` that covers
  the first creation only, and `aurarangecalc` the "search radius" `[C]`; both now split the value (`[C]`) from the
  meaning (`[I]`) (overclaim). Counted: 4 (overclaim 3, stale cross-reference 1). Tags after the review: 31 `[C]`,
  13 `[I]`, 4 `[L]` bullets (no tag moved). Review request closed
  ([archive](../backlog/archive/2026-10-20-reverser-architect-lane-p46m6-review-plan-0046-batch-ama.md)); the
  archivist entry stays open for its lane; ledger rows added. **The next batch (necromancer, `nec`) may start**, with
  9c, 9d, `sor` and `ama`'s conventions, ruling 3 of the `sor` review on writer scans, and ruling 1's condition on
  nested boundaries.
- **2026-10-20 — Phase 1 batch `nec` landed for review (reverser, `lane/p46m7`, static, no harness).** The necromancer
  start functions 15–21 and do functions 30–32 and 55–63: 19 entries, all read and all emulated
  ([skills/0010](../findings/skills/0010-necromancer.md); tier A start 15, do 30, do 31 emulated too). Draws before the
  boundaries: none; no case steps the caster's or the target's seed (do 55's damage roll and do 58's life roll draw on
  the target's seed after their boundaries). Raised by emulation (run:2026-10-20-cat-emu-nec,
  `tools/skills_catalogue_emu.py --batch nec`, `check.txt` `10fec33a…`, `manifest.sha256` `792c0cb4…`): four families,
  6 100 cases, 0 mismatches, 17 boundary/call-site triples asserted (site control 1 891 of 1 891), both seeds compared
  in every case, blocks and packets compared by content; **where a boundary sits inside a helper, the helper's return
  address into the batch function is compared at its stack slot** (ruling 1's condition of the `ama` review), and
  `static` lists every call of each helper; two to seven negative controls per family (each family has one failing 76
  or more; the weak ones named with their deciding class). The calc count's writer scan matches `moffs` stores and
  immediates (0 and 0). The same tool reproduces 9a–9d, `sor` and `ama` byte for byte (`repro.txt`). Surprises:
  **`0x005C2FF0`, run by Raise Skeleton and Revive before anything else, hits a player caster of class 3 for `maxhp /
  8`** (the paladin in PlayerClass order, `[I]`); do 30's `aurastat1` test admits −1 and its length is divided by
  `AiCurseDivisor` only for states 23 and 56 (Dim Vision, Terror), Confuse's always, and Confuse's block skips
  `aurastat1`; do 63 returns 1 when `srvmissilea` is out of range; seven do functions test `id ≠ 0` and not the
  record; do 31 reads `pettype` signed; the corpse test also refuses a `udead`-set state and a MonStats `+0x32` of 0;
  the spawn blocks' `+0x24` is the game pointer (do 56, 60), a frame word do 57 does not write before the call, or the mode (do 62) (wording fixed at the review).
  Tags: 28 `[C]`, 11 `[I]`, 5 `[L]` bullets; 31 symbols added (`I`). Dated note in skills/0003 § 5 (row 70 kept in
  step).
- **2026-10-20 — Batch `nec` reviewed (architect, on `lane/p46m7` at `4118630`): accept with fixes.** `main` had not
  moved past `9183232`, so no merge. Re-run from the lane's tool (`27b93f23…`): `check --batch nec` and
  `static --batch nec` reproduce `check.txt` `10fec33a…` and `static.txt` `c8bdc9e9…` byte for byte;
  `sha256sum -c manifest.sha256` (`792c0cb4…`, 28 files) passes; 17 `site` lines, site control 236 + 630 + 268 + 757 =
  1 891. Spot reads against objdump: start 20 (`0x005C32A0`–`0x005C32F2`) has one call of `0x00629CC0`
  (`0x005C32C3`), and `0x00629CC0` one call of `0x00408090` (`0x00629CD5`, return `0x00629CDA`); do 57's block
  (`ebp−0x34`…`ebp−0x14` stored at `0x005C52EE`–`0x005C5350`, `ebp−0x10` first written after the spawn, through
  `0x0062EA80` at `0x005C53B9`); `0x005C2FF0` (type 0, class 3, `cdq; and edx, 7; add; sar 3`, the packet words at
  `ebp−0x68`/`ebp−0x24`, then `COMBAT_GetHit` at `0x005C305A`); do 30's `cmp ax, 0xFFFF; jl` (`0x005C3803`) and
  `0x005C3400` (0x17 or 0x38); do 61's `lea ecx, [edi+0x56]` and `esi = 1`; do 63's two range jumps to `0x005C5EFC`;
  do 31's `movsx` of `+0xBE` (`0x005C4B97`) against do 56's and do 57's `movzx` with the stored 0; the seven `id ≠ 0`
  tests at the seven addresses § 1 lists; `0x00645510`'s `+0x32` word compare and `0x0063A770`'s `DataTables+0x150`.
  From the kept `corpse_nec.json` through the tool's own model, the eight class-3 cases have `maxhp` −9, 7 and 8,
  so −9 separates truncation from `sar`'s floor and the "signed, truncating" `[C]` holds. **Rulings:**
  (1) **Do 57's fatal path meets ruling 1's condition** by its second branch: each helper on the path has one call
  site in its caller (do 57 → start 20 once, `0x005C5265`, the only call in the image; start 20 → `0x00629CC0` once;
  `0x00629CC0` → `0x00408090` once, the site compared). A chain of single-site helpers needs no stack-slot compare;
  the finding now says so with the addresses (§ 2).
  (2) **Do 57's `+0x24` is `[C]` as a value**: the map from the slot's bytes at entry to the block word (19 cases,
  a random word, `w24_zero` 741). What the game leaves in that slot when it runs do 57 is not covered (it is the
  previous callee frames' residue), and what the spawn makes of it stays the Open question. The finding's Open
  question said do 57 "never wrote" the slot; it writes it after the call (fix 3).
  (3) **The class-3 self-hit stands as filed**: `[C]` up to `COMBAT_ApplyDamage` with the packet by content and the
  helper return address `0x005C4B3F` compared; the paladin and the 1/8-life hit `[I]`; the play consequence an Open
  question. The after-text omitted the `COMBAT_GetHit` call that follows (fix 5).
  (4) **The weak controls are enough**, under the `sor` review's ruling 4: each names its deciding class, and each
  family has one control failing 76 or more.
  (5) **`0x0056E2F0` as a boundary is admitted**; start 21, do 58 and do 59 are `[C]` up to their target tests
  (start 21's and do 58's shared site `0x005C3340` told apart by the helper return addresses `0x005C3366` and
  `0x005C5738`), and their results, Revive's life roll and Attract's state after, `[I]`.
  **Also checked:** do 55's and do 58's `RNG_RangeB` on the target's seed sit after their boundaries under
  "after, `[I]`"; the tags recount 28 `[C]` / 11 `[I]` / 5 `[L]` bullets; the 31 symbol rows are new addresses, all
  `I`, evidence 0010; skills/0003 § 5's dated note and its Raise Skeleton row agree. **Earlier rulings held:** no
  claim rests on a non-argument register (9c ruling 1); callee meanings sit after the boundary (9d ruling, reverser
  review-fixes 13); `sor`'s conventions and its ruling 3; `ama`'s rulings.
  **Fixes, made in the documents:** (1) § 3's start 15 `[C]` and § 4's do 30 `[C]` carried the meaning anchors
  `tbl:MonStats2.txt:corpseSel`, `tbl:MonStats.txt:Velocity` and `tbl:DifficultyLevels.txt:AiCurseDivisor`; they now
  sit on the `[I]` layout bullets beside them (overclaim); (2) § 6's do 56 said an out-of-range `pettype` "→ 0", the
  finding's notation for a refusal; the code stores 0 and goes on (`pet_keep`), and the text now says so (misread);
  (3) the Open question and the landing entry above said do 57 "never" writes `ebp−0x10`; now "not before the call"
  (overclaim); (4) the Answer sent the after-boundary draws to "§§ 5, 6"; both are § 5 (wrong anchor); (5) § 5's
  after-text now names `COMBAT_GetHit(game, caster; caster, &packet)` after `COMBAT_ApplyDamage` (omission);
  (6) § 3 now states that `0x00645510` reads `+0x32` through a null record for a class outside the MonStats count
  (`0x0064557F`), unmodelled, as § 1 does for the ids (omission); (7) § 2 names the single call sites behind
  ruling 1 (other); (8) the archivist entry's context now links MonStats and States, which it asks about (other).
  Counted: 8 (overclaim 2, misread 1, wrong anchor 1, omission 2, other 2). Tags after the review: 28 `[C]`,
  11 `[I]`, 5 `[L]` bullets (no tag moved). Review request closed
  ([archive](../backlog/archive/2026-10-20-reverser-architect-lane-p46m7-review-plan-0046-batch-nec.md)); the
  archivist entry stays open for its lane; ledger row added. **The next batch (paladin, `pal`) may start**, with
  9c, 9d, `sor`, `ama` and `nec`'s conventions, ruling 3 of the `sor` review on writer scans, and ruling 1's
  condition of the `ama` review on nested boundaries (a stack-slot compare or a single call site shown at each
  level of a helper chain).
- **2026-10-20 — Phase 1 batch `pal` landed for review (reverser, `lane/p46m8`, static, no harness).** The paladin
  start functions 29, 31, 35, 36, 37 and do functions 64–67, 73, 79–82 and 150: 15 entries, all read and all emulated
  ([skills/0011](../findings/skills/0011-paladin.md); tier A start 36, do 65, do 66 emulated too). Draws before the
  boundaries: none; no case steps the caster's or the target's seed (the aura target passes, start 35's weapon roll
  and do 79's conversion roll draw after their boundaries, `[I]`). Raised by emulation (run:2026-10-20-cat-emu-pal,
  `tools/skills_catalogue_emu.py --batch pal`, `check.txt` `989e5367…`, `manifest.sha256` `12c8d5c0…`): three
  families, 4 950 cases, 0 mismatches, 21 boundary/call-site triples asserted (site control 2 615 of 2 615), both seeds
  compared in every case, blocks, the aura context and packets compared by content; nested boundaries by the helper's
  return address at its stack slot (`0x0056B740`, `0x005D02B0`) or single call sites listed by `static`
  (`0x0056E510`, `0x00622870`); five negative controls per family (each family has one failing 134 or more; the weak
  ones named with their deciding class). The calc count's writer scan matches `moffs` stores and immediates (0 and 0).
  The same tool reproduces 9a–9d, `sor`, `ama` and `nec` byte for byte (`repro.txt`). Surprises: the aura functions
  reach `AURA_ApplyToTarget` through `0x0056B740` (a context `{game, unit, 0, &block}` and an indirect call), the
  boundary of this batch; do 65's `aurastat` values are gated by mana as its `passivestat`s are, `aurastate` 0 is
  skipped and `auratargetstate` 0 admitted; do 66 rolls `SKILLS_RollElemDamage` once per run, not per unit (`[I]`,
  stats/0002 § 7 note); start 36 reads no skill record; start 35 has no range test; do 73 and do 80 refuse missile
  class 0; do 81's callback rolls a 20 % state 107 on each unit's own seed. Class-3 self-hit (skills/0010): nothing in
  the batch tests the class or calls `0x005C2FF0`; Sacrifice's own self-hit has the same packet shape without the
  result word (`[I]`). Tags: 25 `[C]`, 12 `[I]`, 4 `[L]` bullets; 29 symbols added (`I`). Dated notes in skills/0003 § 5
  (rows 98, 102, 117 in step) and stats/0002 §§ 4, 7. Review request
  [to the architect](../backlog/archive/2026-10-20-reverser-architect-lane-p46m8-review-plan-0046-batch-pal.md); column
  readers [to the archivist](../backlog/2026-10-20-reverser-archivist-plan-0046-pal-skills-charstats-column-readers.md).
- **2026-10-20 — Batch `pal` reviewed (architect, on `lane/p46m8` at `d8c384b`): accept with fixes.** `main` had not
  moved past `e345eaf`, so no merge. Re-run from the lane's tool (`c1630af4…`): `check --batch pal` and
  `static --batch pal` reproduce `check.txt` `989e5367…` and `static.txt` `5fd43532…` byte for byte;
  `sha256sum -c manifest.sha256` (`12c8d5c0…`) passes; 21 `site` lines, site control 915 + 853 + 847 = 2 615.
  Spot reads against objdump: `0x0056B740` (`0x0056B740`–`0x0056B762`: the context `{ECX, EDX, 0, [ebp+0xC]}` at
  `ebp−0x10`, `lea ecx`, EDX untouched, `call [ebp+8]`); `AURA_ApplyToTarget`'s entry reads both registers before
  writing either (`mov esi, [ecx+0xC]`, `mov ebx, edx`, `mov ecx, [ecx+4]`, 0x005CEDE2–0x005CEDF0); do 65's gate
  (0x005CF0B5–0x005CF0C4: a null caster or a non-zero type word skips the test, `jl` against the cost), `aurastate`'s
  `test ax, ax; jle` (0x005CF117) and `auratargetstate`'s `jl` (0x005CF1D8), the self call at 0x005CF143 and the
  target pass reached only when `aurastate` fails; do 66's one `SKILLS_RollElemDamage` at 0x005CF5D5 after the town
  test and before its `ForUnitsInRange` (0x005CF64E), its second block's mana-only gate (0x005CF56B); do 81's callback
  (`0x005D07C0`: the unit's `+0x20`/`+0x24` stepped by `0x6AC690C5` with carry, an unsigned `% 100` against 20, state
  107 set or cleared); start 29, do 150 and start 35 up to their boundaries (start 35: used skill, target, a zeroed
  packet, `SKILLS_GetToHit`, `COMBAT_MeleeHitTest`, no `InMeleeRange`); start 36 (`0x005D0180`–`0x005D0198`, no
  record read); do 64's packet (`or [ebp−0x78], 0x1000`, `+0x08`/`+0x4C`, no `+0x04` write; then `COMBAT_ApplyDamage`,
  `COMBAT_GetHit`, `COMBAT_DeliverQueued`) against `0x005C2FF0`'s (`or word [ebp−0x6C], 4` at 0x005C3028); do 73's and
  do 80's `jle` (0x005D008A, 0x005D06BE), do 73's `or [edi+0xC4], 0x40` (0x005D00A6) and none in do 80 before its
  creation; start 31's speed code (0x005CF7D8–0x005CF873); `0x005CF8C0`'s byte read once at 0x005CF8DC before the loop;
  `sub_0063EE90_HirelingType`'s five classes. Tags recounted 25 `[C]` / 12 `[I]` / 4 `[L]` bullets as filed; the 29
  symbol rows are new addresses and new names, all `I`, evidence 0011; the `hireling` helper rename leaves 9a–`nec`'s
  case files and outputs byte for byte (`repro.txt`). **Rulings:**
  (1) **The aura boundary's ECX and EDX are arguments, so `[C]`.** `AURA_ApplyToTarget` is a register-argument callee
  that reads ECX (the context) and EDX (the unit) at entry before it writes either; that is ADR-0021 (c)'s "every
  argument the claim uses, in registers", not 9c ruling 1's case (a callee-saved register the callee does not take
  and must preserve). The context is a byte block written before the call (by `0x0056B740`) and compared by content,
  with the block it points at; the indirect `call [ebp+8]` reaches the entry the batch function pushed
  (`0x005CEDC0`), which is (a)'s own control flow; the site is the helper's return `0x0056B75F`, and the helper's
  return into each batch function is compared at its slot (ama ruling 1, nec ruling 1). What the callee does with
  the block stays after, `[I]`.
  (2) **The thin claims are admitted.** Do 67's `[C]` is the record test, the used-skill test and the argument of
  `0x006633B0`; start 29's, do 150's and start 31's target path are the record (and used skill) tests and
  `InMeleeRange`'s three arguments. Each is true as a map and each names its boundary; Phase 3 keeps everything after
  them `[I]`, as filed. Routes to more: a boundary later in do 67 (with `0x006633B0`/`0x006633F0` served from declared
  records), or the harness.
  (3) **stats/0002 § 7's `[C]` was not right as worded.** run:2026-10-17-stats counted 865 drawing Sanctuary runs and
  865 steps: one draw per drawing run. It did not count units per run, so it cannot tell "one per unit hit" from "one
  per run"; "once per hit" read as per unit is not separated, and the code (0x005CF5D5, before the target pass, the
  packet copied by `rep movs` at 0x005CF367) makes one call per run. The `[C]` now states the count the run made
  (Answer, § 7 bullet and table row, § 8), and once per run whatever the number hit stays `[I]` (the dated note, no
  check of its own needed for the finding). The stats spec and the wiki repeat "per hit" (`states.md` asks a
  reimplementation to "consume one draw per hit"): carried to the spec-writer
  ([backlog](../backlog/archive/2026-10-20-architect-spec-writer-stats-aura-draw-once-per-run.md)). A run with two or more
  units in range of one Sanctuary run would raise the per-run reading; not required.
  (4) **Do 81's 20 % roll stays `[I]`.** The seeds are compared at the self-call boundary, before `ForUnitsInRange`
  ever runs the callback `0x005D07C0`, so no case executes the LCG step; the seed compare says nothing about it.
  Route to `[C]`: emulate `0x005D07C0` as its own entry (ECX the context, EDX a unit with a declared seed and
  MonStats row): with the block's `+0x48` and packet pointer `+0x4C` both 0 it skips `AURA_ApplyToTarget` and the two
  `COMBAT_*` calls (the tests at 0x005D081F and 0x005D088A–0x005D088F) and reaches the step, ending at `STATE_Set(unit, 107, …)` as a
  boundary with the seed compared; with them set, those calls come first; a later batch or Phase 2.
  (5) **Do 65's gate and the 0 handling hold** (`nogate` 172, `as0` 27 on the `aurastate`-0 class), and so do do 73/80's
  `jle` (`m0` 90), do 80's missing bit 6 (`bit6_80` 71), start 35's missing range test and start 36's missing record
  read (both by objdump above and by cases that end at the predicted boundary). `0x005CF8C0`'s pre-loop byte read is a
  reading, `[I]` in the Functions table, as filed.
  (6) **Sacrifice's self-hit and the class-3 self-hit:** § 6 stands at `[I]`; the packet shape agrees by objdump.
  (7) **The weak controls are enough**, under the `sor` review's ruling 4 (each names its deciding class; each family
  has one failing 134 or more).
  **Also checked:** the dated notes in skills/0003 § 5 agree with rows 98, 102 and 117; the stats/0002 § 4 note put
  `AURA_ApplyToTarget`'s removal of the `+0x48` state inside its `[C]` sentence (fix 2). **Earlier rulings held:** no
  claim rests on a non-argument register (9c ruling 1, ruling 1 above); callee meanings sit after the boundary (9d
  ruling, reverser review-fixes 13); `sor`'s conventions and its ruling 3 (the calc count's scan: 0 stores, 0
  immediates); ama ruling 1 at each level (`0x0056E510` once in start 37, `0x00622870` once in `0x0056E510`, both in
  `static.txt`). **Fixes, made in the documents:** (1) stats/0002's Answer, § 7 bullet and table row and § 8 "once
  per hit" narrowed to the run's count, one draw per drawing run, with the per-run reading `[I]` (overclaim);
  (2) stats/0002 § 4's dated note: the removal of the `+0x48` state moved after the boundary, `[I]` (overclaim);
  (3) the archivist entry's `Param1` and `RunVelocity` items named "the charge speed" and "its base speed" under
  `[C]`; the value is now `[C]` and the meaning `[I]` (overclaim); (4) skills/0011's Answer said do 64 "finds the
  caster's queued hit on the target" in a `[C]`; it now names the `+0xAC` chain node the code matches (overclaim);
  (5) § 3 states that do 81's callback takes the new low seed word unsigned `% 100` (omission); (6) the spec and wiki
  repetition of "per hit" filed to the spec-writer (omission). Counted: 6 (overclaim 4, omission 2). The meaning
  word in a column-reader entry's `[C]` is the second such fix (after `lane/p46m6`'s fix 4); added as a "Seen" line to
  reverser review-fixes rule 1. Tags after the review: 25 `[C]`, 12 `[I]`, 4 `[L]` bullets (no tag moved in
  skills/0011). Review request closed
  ([archive](../backlog/archive/2026-10-20-reverser-architect-lane-p46m8-review-plan-0046-batch-pal.md)); the
  archivist entry stays open for its lane; ledger row added. **The next batch (barbarian, `bar`) may start**, with
  9c, 9d, `sor`, `ama`, `nec` and `pal`'s conventions, ruling 3 of the `sor` review on writer scans, and ruling 1's
  condition of the `ama` review at each level of a helper chain.
- **2026-10-21 — Two spec carries from the `pal` and 9a reviews landed for review (spec-writer, `lane/s46a`, static
  docs only).** (1) stats: Sanctuary's draw is one `RNG_RangeB` per drawing run `[C]` and once per run whatever the
  number of units hit `[I]`, in [stats/README](../specs/stats/README.md#draw-order), [states § H](../specs/stats/states.md#h-draws-per-event-kind)
  and the wiki (stats/overview I 2 → 3, stats/states I 47 → 50). (2) [quests/progression](../specs/quests/progression.md)
  W4c: missile do 17 and do 18 up to their boundary calls `[C]` and their stock rows `[I]` from skills/0004 §§ 7, 8;
  the open question narrowed to do 36 (C 116 → 117, I 321 → 322, L 6). Both backlog entries closed; review request
  [to the architect](../backlog/archive/2026-10-21-spec-writer-architect-lane-s46a-review-stats-aura-draw-and-quests.md).
- **2026-10-21 — `lane/s46a` review (architect): accept with fixes.** Checked against stats/0002 § 7, skills/0011 § 3
  and skills/0004 §§ 7, 8 (do 17's portal test at 0x005AF2BA–0x005AF2DD re-read: it sits outside the scatter window,
  as W4c says). The `[C]` in stats/README and states § H is one `RNG_RangeB` per drawing run and the units-per-run
  reading is `[I]`; W4c's `[C]` stops at each boundary call and names what is not covered; the one new `[L]` (do 36)
  is under *Open questions*; the tag counts held. **Fixes, made in the documents:** (1) states' *Runtime state*
  unit-seed row said the unit seed is "drawn only by a damaging aura's run"; skills/0011 § 3 has Holy Freeze's
  callback step each hit unit's own seed: the row is scoped to the run and a new § H `[I]` note states do 81's
  per-unit step, and the wiki's "once per run" bullet says it, read from the code (overclaim); (2) the wiki quests
  paragraph called the missiles "invisible", which no spec says, and ran the stones' and the chests' missiles into
  one count (overclaim); (3) W4c's `[C]` gave do 18's gold period "from that frame, every `max(4·Param2, 1)`
  frames"; the code tests `left % max(4·Param2, 1) == 0` in the gold phase (stock: first pile at `left` 248, not
  250) (misread); (4) W4c's `[C]` now states the helper's re-seed `(SubX + elapsed, 666)`, its period test and
  owner/room gate, both draw ranges and their offsets, do 18's `left == 1` unit event `0x5C` and the gold phase set
  when the chest is gone (omission); (5) "the aura's hit" left in stats/README § Draw order and as the states
  reimplementation note's heading (stale cross-reference). Counted: 5 (overclaim 2, misread 1, omission 1, stale
  cross-reference 1). Tags after the review: stats/overview {C 14, I 3, L 3}, stats/states {C 44, I 51, L 6},
  quests/progression {C 117, I 322, L 6}. Research map: the stats/states row (counts, the drawing-run wording, Holy
  Freeze), the quests/progression row (counts, the 9a carry) and the overview's stale count in the stats/aggregate
  row (C 13 / I 4 → C 14 / I 3, the architect's). Review request closed; ledger row added. Not merged here.
- **2026-10-21 — Phase 1 batch `bar` landed for review (reverser, `lane/p46m9`, static, no harness).** The barbarian
  start functions 32–34 and 38–41 and do functions 2, 9, 68–72 and 74–78: 19 entries, all read and all emulated
  ([skills/0012](../findings/skills/0012-barbarian.md); tier A start 32 and do 2 emulated too). Draws before the
  boundaries: none; no case steps the caster's or the target's seed (do 69's and do 72's `RNG_Range` and do 69's
  inline step draw on the caster's seed after their `STATE_Set` boundary, `[I]`). Raised by emulation
  (run:2026-10-21-cat-emu-bar, `tools/skills_catalogue_emu.py --batch bar`, `check.txt` `13b1a4d2…`,
  `manifest.sha256` `737c8b4f…`): four families, 6 800 cases, 0 mismatches, 39 boundary/call-site triples asserted
  (site control 2 397 of 2 397), both seeds compared in every case, blocks, points and contexts compared by content,
  register arguments compared where the callee reads them first (pal ruling 1); nested boundaries by the helper's
  return address at its stack slot (eight helpers) or single call sites listed by `static` (do 70's reach chain); three
  to six negative controls per family (each family has one failing 90 or more; the weak ones named with their deciding
  class). The calc count's writer scan matches `moffs` stores and immediates (0 and 0). The same tool reproduces
  9a–9d, `sor`, `ama`, `nec` and `pal` byte for byte (`repro.txt`). Surprises: do 2's overlay and target-state blocks
  return 1 without delivering when the caster has no queued hit on the target; do 9 and do 70 branch on bit 8 of the
  caster's `+0x38`; do 68 sets bit 6 before its record test and admits missile class 0; Find Potion and Grim Ward's
  corpse test adds MonStats2 flag 12 (`soft`, by the layout) to Find Item's; start 40 pulls a player's leap point in to
  `aurarangecalc`; start 41 aims two steps past the path's target point; do 72's rolls are on the caster's seed
  (items/0001 note). Tags: 31 `[C]`, 22 `[I]`, 4 `[L]` bullets; 32 symbols added (`I`). Dated notes in skills/0001
  § 11, skills/0003 § 5 (the Kick row in step) and items/0001. Review request
  [to the architect](../backlog/archive/2026-10-21-reverser-architect-lane-p46m9-review-plan-0046-batch-bar.md); column
  readers [to the archivist](../backlog/2026-10-21-reverser-archivist-plan-0046-bar-skills-monstats2-column-readers.md).
- **2026-10-21 — `lane/p46m9` review (architect): accept with fixes.** Main (`8d9ecb5`) merged first (one conflict in
  this log, both sides kept; `backlog.py archive` moved nothing more). `check --batch bar` and `static --batch bar`
  from the lane's tool reproduce the kept `check.txt` (`13b1a4d2…`) and `static.txt` (`4808f177…`) byte for byte;
  `sha256sum -c manifest.sha256` (`737c8b4f…`) passes. Recounted from `check.txt`: 6 800 cases, the per-family control
  sums (357, 233, 542, 236), 39 `site` lines summing to 2 397, the site controls 933 + 185 + 469 + 810. Read against
  objdump: start 32, 38, 39, 41, do 2, 9, 68, 70, 71, 72, 74, 76, 77, 78 and the helpers `0x0056E510`, `0x005D8510`,
  `0x005D9A10`, `0x00645CA0`, `0x0057D690`. **Rulings.** (1) **The register arguments are admitted** under the `pal`
  review's ruling 1: `0x0056E520` reads `ECX` (`mov edi, ecx`) and `EDX` (`mov ebx, edx`) before any write;
  `0x005DA120` reads `EAX` (`mov edi, eax` at `0x005DA128`; the `push edi` before it saves the caller's `EDI`, not an
  argument); `0x005D9F70` reads `EDI` first (`mov esi, [edi+0x2C]` at `0x005D9F74`, no save or write before it), and do 78
  sets it to the caster at `0x005DA7E6` and never writes it before the call; `0x005DA660` reads `EAX` at `0x005DA66D`
  after writing only `EDX` and `ESP`; `0x0056E2F0` reads `ECX` and `EDX` at `0x0056E2F1`/`0x0056E2F6`. (2) **The thin
  claims stand as `[C]`**, each for what precedes its boundary only: do 77 (the record, the node, then
  `UNIT_CancelEvents(game, caster; 1, 0)`, objdump `0x005DA370–0x005DA3CB`), do 74 (the record, `UnitGetWeapon`'s
  null and `+0x60` tests, its query), start 39 (`SKILLS_GetToHit` is `ret 0xC`, so the trailing 0 is
  `MeleeHitTest`'s third argument, as written), do 71 with a type-1 target (the record, the `auratargetstate` range,
  the type test in `0x005D8510`; what `0x0056E2F0` tests is an open question, as filed). (3) **The weak controls are
  enough** under the `sor` review's ruling 4: each names its deciding class, and the classes match the outcome
  counts where they can be read off (`town_any` 42 = `town` 42, `pt_swap` 36 = `freenear` 36, `mask_swap` 27 =
  `settype` 27; `size2` 41 of 47 monster free-spot cases, `noscale` 22 of 38 player ones, `f200` 23 of the 69 bit-7/8
  cases); each family has one failing 90 or more. (4) **The corrections are sound as dated notes.** items/0001's row
  keeps `C` for its role (the call into `MonDropNoNoDrop`, on its harness logs) and the seed is `[I]` from objdump
  (`mov edi, edx` at `0x005D878D`, `add edi, 0x20` at `0x005D8808`, the two `RNG_Range` at `0x005D8814` and
  `0x005D882F`): the split is sound. No spec relies on the monster's seed ([items/tc](../specs/items/tc.md) names only
  the call chain, `[I]`), so no spec-writer entry is filed. **Also checked:** do 69's and do 72's draws are in `[I]`
  bullets after their `STATE_Set` boundary; do 2's `QueuedHitFind` 0 jumps to `0x0056F44F` (after the delivery call:
  1, bit 6 not set), and the found pointer is the node `+ 0x14`, so "the packet's `+0x04`" is right; do 9's and do 70's
  `sar 8; and 0x80000001` remainder is non-zero exactly when bit 8 is set, whatever the sign; do 68 sets bit 6 (for a
  non-null caster) before its record test and admits class 0 by `jl`, against do 73/80's `jle`; flag 12 is `[C]` as a
  bit test and `soft` only in the `[I]` layout bullet; start 40's pull is `imul`/`cdq; idiv` with `d` raised to 1 and
  tested `> range` (`range` the `aurarangecalc` value); start 41's point is `2 (p − u) / d + p`; do 70's chain
  (`0x0056E510` once in do 70 at `0x005D84B7`, its single call of `0x00622870` at `0x0056E511`) is in `static.txt`;
  the archivist entry's `[C]` items carry values and tests only (meanings `[I]`); the 32 symbols are new and the gate
  is green after the merge. **The development runs:** the record is honest (it says the first `corpse_bar` and
  `move_bar` outputs mismatched on three tool faults and were overwritten by the kept run, and no claim rests on them),
  and no new evidence rule is needed, but reverser review-fixes rule 6 already asks that a development log be kept,
  not lost; a "Seen" line is added there (later batches write development outputs under their own names). **Fixes,
  made in the documents:** (1) § 2 listed `0x005D902C` as a compared return of start 38's `0x00571B70`; the model
  compares only `0x005D8F9B`, and no case reaches the no-path call at `0x005D9027` (overclaim); (2) start 38's
  after-bullet now says a target not in melee range takes the path branch and that the no-path return 0 is not run
  (omission); (3) start 41's after-bullet now says a target not in melee range gives `(px, py)` from the target's
  position, and that the free-spot search after a non-zero pattern test is around the unextended point (omission);
  (4) do 76's and do 78's own return values after their boundaries (0 at the word-0 site, 1 at the `& 3` site; 1 when
  `0x005DA120` gives 0, the callee's value on bits 7 and 9) (omission); (5) § 2's "a control failing 72 or more" made
  "90 or more", as the request and this log say (other). Counted: 5 (overclaim 1, omission 3, other 1). Tags after the
  review: 31 `[C]`, 22 `[I]`, 4 `[L]` bullets (the fixes extend existing `[I]` bullets). Review request closed
  ([archive](../backlog/archive/2026-10-21-reverser-architect-lane-p46m9-review-plan-0046-batch-bar.md)); the
  archivist entry stays open for its lane; ledger row added. **The next batch (druid, `dru`) may start**, with 9c, 9d,
  `sor`, `ama`, `nec`, `pal` and `bar`'s conventions, and development outputs kept under their own names.
- **2026-10-21 — Phase 1 batch `dru` landed for review (reverser, `lane/p46m10`, static, no harness).** The druid
  start functions 56–58, do functions 114–124 and do-table entries 145 and 146 (the States `srvactivefunc` of 144
  `hurricane` and 145 `armageddon`, run by `sub_0056D790_StateDoFunc` on unit event 5 with the event's skill id and
  level): 16 entries, all read and all emulated ([skills/0013](../findings/skills/0013-druid.md); tier A do 114, do 117
  emulated too). Draws before the boundaries: do 124's `RNG_Range(caster, 0x10000)` and do 123's `RNG_Range(caster,
  0x100)`, both on the caster's seed; no case steps the target's seed (entry 146's re-seed of the caster and its point
  draws, entry 145's damage rolls and the hits' elemental rolls are after their boundaries, `[I]`). Raised by emulation
  (run:2026-10-21-cat-emu-dru, `tools/skills_catalogue_emu.py --batch dru`, `check.txt` `592baf51…`, `manifest.sha256`
  `d1a77e1f…`): four families, 8 400 cases, 0 mismatches, 33 boundary/call-site triples asserted (site control 3 967
  of 3 967), both seeds compared in every case, blocks, packets and the `RectTest` rectangle compared by content,
  register arguments where the callee reads them first; nested boundaries by the helper's return address at its stack
  slot (`0x0056E680`, `0x005C8980`, `0x005C7040`, `SkillTargetCellFree`, `COLL_WHTest`); four to six negative controls
  per family (each family has one failing 134 or more; the weak ones named with their deciding class); `COLL_WHTest`
  runs emulated (a boundary in `sor`) so do 123's draw is reached. The calc count's writer scan matches `moffs` stores
  and immediates (0 and 0). The same tool reproduces 9a–9d, `sor`, `ama`, `nec`, `pal` and `bar` byte for byte
  (`repro.txt`); the two development runs are kept under their own names in `dev/`. Surprises: a `ResultFlags` bit-0
  skill makes no hit test in start 58 and do 122; do 123 has no upper test on its class (the fatal path in
  `SkillTargetCellFree`); do 119 puts the target point's x in the spawn block's `+0x24`; do 120 evaluates its
  `aurastat` calcs at the stack count (`[I]`); do 124's draw is the word Armageddon's first period re-seeds from
  (`[I]` after the boundary; skills/0003 § 9 note, rng/seeds open question to the spec-writer). Tags: 25 `[C]`, 25 `[I]`,
  4 `[L]` bullets; 20 symbols added (`I`). Dated notes in skills/0003 § 5 (the Firestorm row in step) and § 9. Review
  request [to the architect](../backlog/archive/2026-10-21-reverser-architect-lane-p46m10-review-plan-0046-batch-dru.md); column
  readers [to the archivist](../backlog/2026-10-21-reverser-archivist-plan-0046-dru-skills-missiles-column-readers.md);
  [to the spec-writer](../backlog/archive/2026-10-21-reverser-spec-writer-rng-seeds-armageddon-first-period.md) on rng/seeds.
- **2026-10-21 — `lane/p46m10` review (architect): accept with fixes.** Main (`f8f1e9f`) merged first (clean, no
  markers; `backlog.py archive` moved nothing). `check --batch dru` and `static --batch dru` from the lane's tool
  (`11b763dd…`) reproduce the kept `check.txt` (`592baf51…`) and `static.txt` (`d2c98496…`) byte for byte;
  `sha256sum -c manifest.sha256` (`d1a77e1f…`, 69 lines) passes. Read against objdump: do 116, 119, 120, 123, 124,
  start 57, entry 146 up to its point draws, `0x0056E680`, `0x005C8980`'s loop, `SkillTargetCellFree`,
  `COLL_WHTest`, `0x004EFC80`, `0x00625D00`, and the entries of the five new boundaries. **Rulings.** (1) **`COLL_WHTest`
  run emulated is admissible.** ADR-0015 (1) names "runs emulated" as one of a callee's treatments and the choice is
  per run, declared in the memory spec; this run declares its reads (0 undeclared in `miss_dru`), so the `[C]` covers
  `COLL_WHTest`'s code on the paths reached from `SkillTargetCellFree`, which always passes width = height = `Size`
  (the separate height test at `0x0064D811` is not separated from the width test). The three `0x27` branches and the
  word test are each reached (recounted at the review from `miss_dru.json` with the lane's model: no room at the
  point 88, no map 14, no word array 6, a busy word 33, a free one 72). The `sor` batch is unaffected: its claims end
  at `COLL_WHTest`'s entry, nothing here re-runs or raises its functions' code after that call, which stays `[I]`.
  (2) **The two draws are `[C]`** under ADR-0021 (c): the drawn value is a byte written before the call that the
  claim uses, compared at its absolute stack address, with the caster's seed state compared and `seed_none` (202) and
  `noseed` (72) failing; do 124's `CALC_Eval` of `auralencalc` between the draw and the boundary runs on constant
  programs. What the value becomes (`UnitSkillSet18`, `MISSDATA_SetSeedLow`, `UnitMsgA3`'s last argument) is after,
  `[I]` (objdump `0x005C8228`/`0x005C823C`, `0x005C8103`/`0x005C8115`). (3) **Entries 145 and 146 stand as mapped**:
  every map ends at `UNIT_CancelEvents` (the shared exit at `0x005C85D6` is also where the town branch's `STATE_Set`
  returns), `UNIT_UnlinkStatList`/`STATE_Set`, or the re-arm; entry 146's re-seed (`0x005C8688`) and point draws are
  inline after `UnitQueueEvent` with no callee to stop at, so they stay `[I]` until a wider image or a run. (4) **The
  register arguments are admitted**: `STATE_GroupClear` (`mov edi, edx` `0x0056C749`, `mov ebx, ecx` `0x0056C750`),
  `UNIT_CancelEvents` (`mov edi, ecx; mov ecx, edx` `0x00540E64`), `SkillMissileCreate` (`0x0056ECC1`/`0x0056ECC3`;
  the `memset` arguments are pushed, not registers), `COMBAT_BuildDamage` (`0x0057B7D7`, `0x0057B7DB`) and
  `COLL_RectTest` (`mov edi, edx` `0x0064CEB8`, `ECX` unwritten up to `0x0064CEC0`) each read before any write. (5)
  **The weak controls are enough**, each with its deciding class, but `sd_first`'s class was misstated: the control
  keeps the first byte unless it is `0x80`, so it fails only where the first is neither `0x80` nor the last (cases 383
  and 2201), not on "the cases with two differing bytes" (8 of the 255 boundary cases). The "last" reading does not
  rest on 2: over those 8, first-kept fails 7, smallest 5, largest 3, so it is separated from all three. `nostate57` 47 =
  `noshape` 47, `p4_noframe` 47 of 48 (one frame 0) and `mask7` 15 are as stated. (6) **The corrections are sound as
  dated notes**: skills/0003 § 5's note and the Firestorm row agree with objdump; § 9's row and note needed the
  condition of fix 1. **Also checked:** do 123 has no upper test (`test ebx, ebx; jle` only, `0x005C80C8`) and
  `SkillTargetCellFree` takes the fatal path on a null record (`0x0056E497`), before its room test; `0x0056E680` tests
  `ResultFlags` bit 0 first (`0x0056E68E`) and on it returns with `+0x04 = ResultFlags`; the "no stock row" fact is now
  a full-table statement (fix 6; 25 rows in the batch, the lane's `rows.sh` selection complete); do 119's `+0x24` is
  the block slot `ebp−0x18` that `SKILLS_GetTargetXY` writes x to (no store names it), stated as such in § 3; do 120's
  count is `min(old + 1, calc2)` (`jl` at `0x005C796A`) passed to `SKILLS_ApplyAuraStats` as its level (`[I]`, after
  the boundary); do 116 returns 0 after `SkillDelayFromCalc` on a non-zero `GroupClear` (`0x005C6F27`–`0x005C6F40`);
  start 57 zeroes no packet (no `memset` before `0x005C7AA6`); the dev runs are under `dev/dev1`, `dev/dev2` with
  their own `dev<N>-` names (its `notes.txt` writes dev1 `miss_dru` as "match=1800 bad=1" for a control that did not
  fail, a wording slip in a workspace note, left); 25 `[C]`, 25 `[I]`, 4 `[L]` bullets recounted (unchanged by the
  fixes); the 20 symbol rows are new and the gate passes E7 after the merge. **Fixes, made in the documents:** (1)
  Armageddon's first period uses do 124's `r` only if `SKILLS_GetUnitSkill(caster, id)` is the used node **and** no
  other writer of its `+0x18` runs between (`UnitSkillSet18` has 85 call sites, not followed): § 5, Open questions,
  skills/0003 § 9's row and note, and the spec-writer entry (overclaim); (2) the archivist entry's `InTown` and
  `aurarangecalc` items said "loses the state", "the period ends" inside `[C]`; now the branch and its boundary calls,
  the meaning `[I]` (overclaim; reverser review-fixes rule 1); (3) `0x005C7520`: the scan form stated (a linear sweep of
  `.text` operand text, call targets included, and the file's dwords) and "no reference" narrowed to "no direct
  reference" (overclaim); (4) `sd_first`'s deciding class, and the 8-case separation of the "last" byte, in § 2
  (misread); (5) do 124 returns 0 when `STATLIST_Alloc` gives 0, unlike do 120 (omission); (6) the `ResultFlags` table
  fact over all 358 rows with `tbl:Skills.txt:ResultFlags` (omission); (7) the Answer's "no other draw before a
  boundary" scoped to constant calc programs (omission). Counted: 7 (overclaim 3, misread 1, omission 3). Tags after
  the review: 25 `[C]`, 25 `[I]`, 4 `[L]` bullets. Review request closed
  ([archive](../backlog/archive/2026-10-21-reverser-architect-lane-p46m10-review-plan-0046-batch-dru.md)); the
  archivist and spec-writer entries stay open for their lanes; ledger row added. **The last class batch (assassin,
  `ass`) may start**, with 9c, 9d, `sor`, `ama`, `nec`, `pal`, `bar` and `dru`'s conventions; a callee that an earlier
  batch observed may run emulated when its reads are declared, and the finding then says which paths of it were
  reached.
- **2026-10-21 — The `dru` spec carry landed for review (spec-writer, `lane/srng`, static docs only).**
  [rng/seeds](../specs/rng/seeds.md) *Reimplementation notes*, *Armageddon's cast draw*: do 124's
  `RNG_Range(caster+0x20, 0x10000)` `[C]` (ADR-0021, run:2026-10-21-cat-emu-dru); the store with
  `UnitSkillSet18(used node, r)`, the node identity and the absence of another `+0x18` writer `[I]`; the open question
  narrowed to those two conditions until a run logs a first period (C 79 → 80, I 12 → 13, L 4). Wiki randomness
  updated. Backlog entry closed
  ([archive](../backlog/archive/2026-10-21-reverser-spec-writer-rng-seeds-armageddon-first-period.md)); review request
  [to the architect](../backlog/archive/2026-10-21-spec-writer-architect-lane-srng-review-rng-seeds-armageddon-cast-draw.md).
- **2026-10-21 — `lane/srng` review (architect): accept with fixes.** Read against skills/0013 §§ 1, 4, 5 and the
  Answer, skills/0003 § 9's dated note, run:2026-10-21-cat-emu-dru and the `lane/p46m10` review's rulings 2 and 3 and
  fixes 1, 5 and 7. The `[C]` paragraph of *Armageddon's cast draw* stops at do 124's `STATLIST_Alloc` @0x005C8295 or
  `StatListSetEnd` @0x005C82E1 (ADR-0021) and carries fix 7's constant-program scope; the store, the
  `STATLIST_Alloc`-gives-0 return (fix 5), the event 5 queue, entry 146's `Init` of the node's `+0x18` and both
  conditions of fix 1 are `[I]`; Hurricane's and Diablogeddon's states match § 1's rows; the `[L]` stays only under
  *Open questions*, narrowed to the node identity and the other writer. The wiki states the draw as a run, the store as
  read from the code and the first firing as open, with no claim the spec lacks. Tags recounted by script: 80 `[C]`,
  13 `[I]`, 4 `[L]`, as the front matter. **Fixes, made in rng/seeds:** (1) the draw's preconditions left out the
  setting of bit 6 of the caster's `+0xC4` before the draw (omission); (2) the `[I]` store paragraph went from the
  `STATLIST_Alloc` test straight to the event 5 cancel, leaving out the list steps (`StatListSetEnd`, event 12,
  `SKILLS_ApplyAuraStats`, stats 350/351) in between (omission). Counted: 2 (omission 2). Spec-writer review-fixes rule
  4 gains this case. Research map rng/seeds row rewritten (updated 2026-10-21; C 80 / I 13 / L 4, the stale I 10
  replaced; the `dru` carry named). Review request closed
  ([archive](../backlog/archive/2026-10-21-spec-writer-architect-lane-srng-review-rng-seeds-armageddon-cast-draw.md));
  ledger row added (the lane's; the review's usage is the orchestrator's to add at the merge).
- **2026-10-21 — Phase 1 batch `ass` landed for review (reverser, `lane/p46m11`, static, no harness).** The assassin
  start functions 22–28, do functions 33–52 and 54, and the progressive entries 36–41 and 143 (`srvprgfunc`, run by
  `COMBAT_PrgFinisher`; 36 also `ItemEffect` 36): 29 entries, all read and all emulated
  ([skills/0014](../findings/skills/0014-assassin.md); tier A start 23, do 35, entries 38, 39, 143 emulated too). Draws
  before the boundaries: entries 37, 39, 41 and 143 step the caster's seed once inline at entry, before their record
  test, then draw on a stack seed seeded from the stepped low word (the ring's one step, 39's `RNG_Range(local, 2r)`
  pairs, 41's two steps) up to their first creation; no case steps the target's seed (do 33's knockback step and do
  42's `RNG_Range(caster, 100)` are after their boundaries, `[I]`). Raised by emulation (run:2026-10-21-cat-emu-ass,
  `tools/skills_catalogue_emu.py --batch ass`, `check.txt` `dd6ed294…`, `manifest.sha256` `04f487b6…`): four families,
  8 700 cases, 0 mismatches, 37 boundary/call-site triples asserted (site control 3 020 of 3 020), both seeds and the
  stack seeds compared in every case, blocks and packets compared by content, register arguments where the callee reads
  them first; nested boundaries by the helper's return address at its stack slot (`0x0057E240`, do 34 from do 35,
  `0x005D6200`, `SkillNovaAtUnit`, the two rings, `0x005D5E10`, `0x005D7CE0`); five to seven negative controls per
  family (each family has one failing 165 or more; the weak ones named with their deciding class). The calc count's
  writer scan matches `moffs` stores and immediates (0 and 0). The same tool reproduces 9a–9d, `sor`, `ama`, `nec`,
  `pal`, `bar` and `dru` byte for byte (`repro.txt`); the two development runs are kept under their own names in
  `dev/`. The carried items: the five finishing-move calls of `COMBAT_PrgFinisher` are do 42's, do 46's (two, one per
  frame parity; **not start 25's**, which is the 16-byte target test), do 50's and do 52's, each with
  `QueuedHitFind`'s hit (do 42 and 52 without a null test); the `ItemEffect` 36 join is entry 36, a nova of the row's
  `srvmissilea` centred on the cast's target unit. Surprises: the rings never test their step count (0 never ends,
  `[I]`) and store Royal Strike's `Param2 + 1` in every missile's `+0x28`; the trap helper makes a bad `pettype` 0
  instead of refusing; Dragon Flight alternates kick and teleport by the frame parity and reads Levels `Teleport`; do
  35 returns 1 where do 34 refuses (and after its hit path, `[I]`). Tags: 39 `[C]`, 28 `[I]`, 4 `[L]` bullets; 27 symbols added (`I`). Dated notes
  in skills/0001 § 12 and skills/0003 §§ 1, 5, 9. Review request
  [to the architect](../backlog/archive/2026-10-21-reverser-architect-lane-p46m11-review-plan-0046-batch-ass.md); column
  readers [to the archivist](../backlog/2026-10-21-reverser-archivist-plan-0046-ass-skills-levels-column-readers.md);
  [to the spec-writer](../backlog/archive/2026-10-21-reverser-spec-writer-combat-delivery-a3-finisher-callers-and-progressiv.md)
  on combat/delivery A2/A3.
- **2026-10-21 — `lane/p46m11` review (architect): accept with fixes.** Reviewed on the lane (head `a943188`), main not
  merged (it moved to `f805cdf` with the `srng` and `h2c` merges; neither touches skills findings or these symbols, and
  none of the 27 addresses or names is on main's side). From the lane's tool (`b38bba31…`), under a 4 GB scope,
  `cases --batch ass`, `check --batch ass` and `static --batch ass` reproduce the kept case files, `cases.txt`,
  `check.txt` (`dd6ed294…`) and `static.txt` (`fcf4be4f…`) byte for byte; `repro.sh` rerun into the review's scratch
  gives the kept `repro.txt` (`43e65419…`) byte for byte (9a–9d and the six earlier classes); `sha256sum -c
  manifest.sha256` (`04f487b6…`, 70 lines) passes. Read against objdump: start 25 and do 46 whole (`0x005D6330`–
  `0x005D6405`), the six `call 0x5d5220` sites (a full-image grep), do 35 up to its do 34 call, `PrgCalcByCharge`
  (`0x005D3DA0`), ring 37's loop tail (`0x005D4605`–`0x005D467D`), entry 41's two steps and remainders
  (`0x005D5160`–`0x005D51DA`), the trap helper's class and `pettype` tests (`0x005D5E36`–`0x005D5E74`), do 48's frame test
  (`0x005D691A`), start 26's `startmana` test and `STATLIST_Alloc` call, and do 52's `Teleport` branch. Tags recounted:
  39 `[C]`, 28 `[I]`, 4 `[L]` bullets (unchanged by the fixes). **Rulings.** (1) **Start 25 vs do 46: do 46.** Start 25
  is the 16 bytes `push edx; push ecx; call UNIT_GetTargetUnit; neg; sbb; neg; ret 8`; both finisher calls lie in do 46
  (`0x005D6340`), one per parity of the caster's `+0x38` bit 8, each after `QueuedHitFind` and its `je`. Plan 0045's
  P1b note had the function boundary wrong, not the sites. This plan's Phase 1 carried-item text is fixed (the
  architect's own text, not counted on the lane), and skills/0001's *Leads used* detail with it (fix 2). (2) **The
  ring's step count 0 loop stays `[I]`**, correctly placed after the first creation: `add esi, edi` with `edi = 4n` and a
  signed `jl 0x100` never moves for `n = 0`; no case runs past the boundary, so neither the loop nor its count is
  covered. The lane's negative branch was wrong (fix 1): a negative `4n` reads below the direction tables each pass and
  the signed index leaves the loop only by wrapping past −2³¹; `4n` wraps for `|n| ≥ 2²⁹` too, so the `⌈64 / n⌉` count
  holds for `0 < n < 2²⁹`. Whether a stock calc reaches 0 or a negative count stays the `[L]` under *Open questions*
  (a calc-table check or the harness). (3) **The weak controls are enough, each with its deciding class.** `prg_k1` (7)
  and `n18_le` (6) are thin but each is a whole class (the progressive path with two or more charges reaching a compared
  value; a node `+0x18` equal to the frame), and a wrong reading cannot match a member by chance. The review also ran
  scratch variants of the kept checker on the kept outputs (not kept; supporting this ruling only, no finding claim
  rests on them): `prg_k1` applied to the trap family's `PrgCalcByCharge` readers (do 43, 48, 51, 54) fails 16 more;
  a cap at 2 for 3 fails 3 + 12, an unsigned clamp 3 + 5, no lower clamp 16 + 27, and an unsigned do 48 frame test 1,
  so the clamp's bounds and signedness are each separated, thinly. A later batch that reuses `PrgCalcByCharge` applies
  its control in every family that reads it. (4) **The four new observed boundaries and the register arguments are
  admitted** as cited in § 2 (`COMBAT_PrgFinisher` `mov edi, edx` / `mov [ebp−0x18], ecx`, `UnitTeleport` alike;
  `InvGetBodyLocItem` and `0x006229F0` stack only); the earlier boundaries' register reads are as `dru`'s ruling 4.
  (5) **Helpers run emulated are admissible** (the `dru` ruling 1); § 2 names the paths reached and § 6 the trap
  helper's unreached branches. (6) **The draws before the boundaries are `[C]`** under ADR-0021 (c): the caster's seed
  stepped at entry before the record test (`noseed` fails all 1 200 cases of the four entries) and the stack seeds
  compared as frame words at their absolute slots (`ring_noinit` 243); do 33's knock step and do 42's
  `RNG_Range(caster, 100)` are after their boundaries, `[I]`. (7) **The corrections stand as dated notes** in skills/0001
  § 12 and skills/0003 §§ 1, 5, 9; skills/0003 § 1's "`n < 0` reads below the table" is right as written. **Fixes, made
  in the documents:** (1) § 5's ring bullet and *Open questions*: a negative step count is not an endless loop (the
  wrap above), the `⌈64 / n⌉` range bounded (misread); (2) skills/0001's *Leads used* detail (src:arreat-summit-skill-trees)
  still named start function 25 for Dragon Claw's two sites after the § 12 note corrected it (stale cross-reference;
  reverser review-fixes rule 12 gains this Seen line); (3) § 4's do 46 after-bullet read as two deliveries on the
  no-hit path; now the finisher only on a hit, then one `DeliverQueued(target, 0)` on either path (other); (4) the
  Answer's "After, from the reading" bullet had no anchor (gate W1); the after-boundary ranges of do 33, do 42, ring 37
  and the trap helper added (wrong anchor). Counted: 4 (misread 1, stale cross-reference 1, wrong anchor 1, other 1). Review request closed
  ([archive](../backlog/archive/2026-10-21-reverser-architect-lane-p46m11-review-plan-0046-batch-ass.md)); the
  [archivist entry](../backlog/2026-10-21-reverser-archivist-plan-0046-ass-skills-levels-column-readers.md) and the
  [spec-writer entry](../backlog/archive/2026-10-21-reverser-spec-writer-combat-delivery-a3-finisher-callers-and-progressiv.md)
  (combat/delivery A2/A3, the five finisher callers and the entries' raises) are **released**, the latter with the
  negative-count and do 46 wording of fixes 1 and 3; lane ledger row added (the review's row is the orchestrator's at
  the merge). **Phase 1 status:** the seven class batches and 9a–9d are accepted, eleven of fifteen batches and 230 of
  the 310 entries (the other 80: batch 10's 4, 8a–8c's 70, and the six `general` tier-A entries plan 0045 read). Phase 1
  is **not** complete. **Next for 0046:** batch 10 `item` (do 113, do 151, Unsummon's start 3 and do 4, and the callers:
  stat-event handlers 20, 21, 30, charges, the shrine missiles, the object and quest `MissileCreateAt` sites, with the
  carried `ITEMSKILL_Cast` helper items), on all the class batches' conventions; then 8a, 8b, 8c, unless the
  monster-AI plan pulls one forward. Phase 2 still waits for 0045·P3's review.
- **2026-10-21 — The `ass` spec carry landed for review (spec-writer, `lane/s46c`, static docs only).**
  [combat/delivery](../specs/combat/delivery.md) A2/A3 from [skills/0014](../findings/skills/0014-assassin.md) §§ 1, 4,
  5 and run:2026-10-21-cat-emu-ass, with the `lane/p46m11` review's wording: the finisher's six callers and the
  finishing moves' calls `[C]` (do 46 runs it only on a hit, then one `DeliverQueued` on either path, `[I]` after the
  call); entries 36–41 and 143 `[C]` up to their first creation, the rest `[I]`; a ring count of 0 endless `[I]`, a
  negative count ending by the index wrap `[I]`, the stock values an `[L]` under *Open questions*. Tags {C59 I49 L3} →
  {C74 I58 L4}; open questions 3 → 4 `[L]`. Entry closed
  ([archive](../backlog/archive/2026-10-21-reverser-spec-writer-combat-delivery-a3-finisher-callers-and-progressiv.md));
  review request [to the architect](../backlog/archive/2026-10-21-spec-writer-architect-lane-s46c-review-combat-delivery-finisher-callers.md).
- **2026-10-21 — `lane/s46c` review (architect): accept with fixes.** Reviewed on the lane (head `b3c7c03`), main not
  merged (it moved to `945f2f7` with the items/tc and items/properties re-tag, which touches no combat file). Every new
  or changed claim of combat/delivery A2/A3 read against skills/0014 §§ 1, 4, 5, run:2026-10-21-cat-emu-ass (§ 2's
  family table and `static.txt`'s line `calls of 0x005D5220: 6 in the image`), skills/0001 § 12, skills/0003 §§ 1, 9,
  ADR-0021 and the `lane/p46m11` rulings. The pseudocode of entries 36–41 and 143 follows § 5's anchored order step for
  step (record, missile, target point, count; 40's point before its level test; 41's `n < 0` after the block); the
  diagram's finisher node restates A2 and A3 and adds no claim. **Rulings.** (1) **Do 52's finisher call is a static
  call site only**, `[C]` as one of the six `static.txt` calls and `[I]` as a call (it follows do 52's hit-test
  boundary); the lane has it so. Do 33's knock step and do 42's last-kick draw stay `[I]` (after their boundaries). (2)
  **"Six" counts calls, not callers**: six `call 0x5d5220` sites in five functions (`SKILL_AttackDo`, do 42, 46, 50,
  52), as the `lane/p46m11` review's "five finishing-move calls plus `SKILL_AttackDo`". (3) **Do 46's calls are `[C]`
  on the run's path only**: the run reaches `PrgFinisher` @0x005D639E / @0x005D63E6 and `DeliverQueued` @0x005D63AB /
  @0x005D63F3 where `0x005D6200` returns for a bad id (skills/0014 Answer, § 4); on a valid id the same instructions
  follow the `MeleeHitTest` boundary and are `[I]`. (4) **combat/README B5 gets a pointer**: B5's normal-attack text
  stays true, but a reader of the draw order should know the finisher has other callers; one untagged sentence
  pointing at delivery § A2 (no tag of its own; the claim is A2's). (5) Research map: the combat row's figure is
  C 230 / I 185 / L 24 (the five front matters summed by script, unchanged by the fixes), with the plan 0046 `ass`
  clause, skills/0014 and the plan link. **Fixes, made in the documents:** (1) A2 "six direct callers" for six calls in
  five functions, and § Evidence's "six callers" (miscount); (2) the do 46 `[C]` in A2, the entry-points row and the
  reimplementation note scoped to its bad-id path, the valid-id call `[I]` (overclaim); (3) A3's "no entry draws up to
  its first creation" `[C]`: boundary named per entry (38's delivery or roll is not a creation) and the constant-calc
  caveat added, as skills/0014's Answer states (overclaim); (4) the ring-count bullet's `[C]` sentence said "before and
  after the first creation" (overclaim); (5) A2's bold "each finishing move delivers once" against do 42's second
  delivery in the same bullet (misread). Counted: 5 (overclaim 3, miscount 1, misread 1). Spec-writer review-fixes
  rule 2 gains this Seen line (a `[C]` boundary reached on one path stated for all). Review request closed
  ([archive](../backlog/archive/2026-10-21-spec-writer-architect-lane-s46c-review-combat-delivery-finisher-callers.md));
  lane ledger row added (the review's row is the orchestrator's at the merge). Gate fast tier green.
- **2026-10-21 — Phase 1 batch 10 `item` landed for review (reverser, `lane/p46m12`, static, no harness).** Unsummon's
  start 3 and do 4, do 113 (rows 217–220) and do 151 (row 53's `ItemEffect`), and the callers: `ITEMSKILL_Cast` with
  its `ItemTarget` helpers 2–4 and its two callers, the stat-event handlers 20, 21, 30, `SKILLS_PayCost`'s charge path,
  the shrine functions 19, 21, 22 and the object and quest `MissileCreateAt` sites
  ([skills/0015](../findings/skills/0015-item.md)). All four entries and the ten callers emulated (the three helpers inside the cast)
  (run:2026-10-21-cat-emu-item, `tools/skills_catalogue_emu.py --batch item`, `check.txt` `22402718…`,
  `manifest.sha256` `3e974e32…`): five families, 12 000 cases, 0 mismatches, 31 boundary/call-site triples (site
  control 4 936 of 4 936), three seeds compared in every case; five to nine negative controls per family, the thin
  ones equal to their deciding classes on the `CLASS` lines. The quest sites and `0x0058C8D0` are read and pinned, not
  emulated (inside quest handlers). The same tool reproduces 9a–9d and the seven class batches byte for byte
  (`repro.txt`). **Carried items:** `ITEMSKILL_Cast` gives the `ItemTarget` 2 helper **its own caster**
  (`0x005FDB9B`), the handler's unit or, for handler 20 with `ItemTgtDo` (Teleport), the event's other unit; helpers 3
  and 4 do not draw (run and static closures); `sub_00575900_PetLimitRefresh`, run by `STATE_DefaultRemoveCB` and the
  skill shrine's remove callback, recomputes the pet limits and removes pets above a lowered `petmax` (`[I]`);
  helpers' symbols added. Draws before the boundaries: handlers 20/30 one inline step and 21 `RNG_RangeB(100)` on the
  handler's unit, helper 2 two steps on the caster's seed, shrines 21/22 `RNG_RangeB(Arg1 − Arg0)` on the shrine's.
  Surprises: the item effect flag is 1 only from handler 20 without `ItemTgtDo`; `ItemTarget`'s low byte only; the
  exploding and poison shrines drop 5–9 potions; Unsummon's `PetRemove` flag is a `push 1` left across
  `UnitSkillGet18`. Tags: 29 `[C]`, 22 `[I]`, 4 `[L]` bullets; 26 symbols added (`I`). Dated notes in skills/0001
  § 10 and skills/0003 §§ 2, 3. Review request
  [to the architect](../backlog/archive/2026-10-21-reverser-architect-lane-p46m12-review-plan-0046-batch-item.md); column
  readers [to the archivist](../backlog/2026-10-21-reverser-archivist-plan-0046-item-skills-pettype-books-shrines-column.md);
  [to the spec-writer](../backlog/archive/2026-10-21-reverser-spec-writer-combat-delivery-e5-item-cast-helpers-and-effect.md)
  on combat/delivery E5.
- **2026-10-21 — `lane/p46m12` review (architect): accept with fixes.** Reviewed on the lane (head `bcdb4ca`), main not
  merged (it moved to `483728e` with the items/tc, items/properties and combat/delivery A2/A3 merges; none touches a
  skills finding, and none of the 26 addresses or names is on main's side; main's own appends to this log will meet
  this entry at the merge, keep both). `sha256sum -c manifest.sha256` (`3e974e32…`, 118 lines) passes. From the lane's
  tool (`904fe25e…`), under a 4 GB scope, `cases --batch item`, `check --batch item` and `static --batch item`
  reproduce the 15 case files, `cases.txt`, `check.txt` (`22402718…`) and `static.txt` (`55299029…`) byte for byte;
  `repro.sh` rerun into the review's scratch gives the kept `repro.txt` (`41e54f5b…`) byte for byte (9a–9d and the
  seven classes). Recounted from `check.txt`: 12 000 cases, 0 bad, 0 undeclared, 0 stopped; site controls 934 + 1 317
  + 386 + 1 800 + 499 = 4 936 over 4 + 12 + 7 + 5 + 3 = 31 `site` lines; the ten `CLASS` lines equal their controls.
  Read against objdump: `ItemCastAtUnit` whole (`0x005FDCA0`–`0x005FDD1C`), the cast's helper 2 call (`0x005FDB9B`–
  `0x005FDBA4`), handler 20 (`0x005C0470`–`0x005C058B`), do 4 whole, `STATE_DefaultRemoveCB`'s tail (`0x0056E940`–
  `0x0056E965`) and `0x00583BD0`'s head, `PetLimitRefresh`'s loops (`0x00575990`–`0x00575A7B`), shrine 21 up to its
  missiles (`0x005830E0`–`0x00583299`), `SKILLS_PayCost`'s mana path and its three call sites, and the eight
  `call 0x56f7f0` sites of `SKILLS_SrvDo` with a byte search of the image for the four cast-path addresses (none).
  Tags 29 `[C]`, 22 `[I]`, 4 `[L]` bullets as filed (the fixes add none). **Rulings.** (1) **The handler → helper 2
  chain stays `[I]`.** Each `[C]` ends at its boundary (ADR-0021), and the handler family observes `ItemCastAt*` while
  the cast family starts from its own inputs, so the join is a composition of two maps over different case sets, which
  neither ADR-0015 nor ADR-0021 covers. The cast family already runs caller → cast → helper 2 in one case (the 45
  `PatternTest` cases from `0x005FDCA0`/`0x005FDD60`), so the open seam is handler → caller only. Path to `[C]`, not
  required: a family running handler 20 with `ItemCastAtUnit` emulated through to `COLL_PatternTest` (the `dru`
  ruling 1 lets a callee observed in one batch run emulated in another), or a Phase 2 sample with an item Teleport.
  (2) **`PetLimitRefresh` `[I]` by static reading is admitted.** It is no catalogue entry; the carried item asked what
  removes the pets, and § 10 answers it with addresses, read here at its two loops and at both remove callbacks.
  The `PetLimit` it calls is not emulated in any batch, so an emulated `PetLimitRefresh` would end at that boundary
  and say nothing about removal; the harness (a skill shrine wearing off with extra skeletons) is the raise path. The
  extra-skeletons *Leads used* verdict "held" stands as a verdict; it raises nothing. (3) **"`ItemEffect` 36/151 only
  on attack, kill or hit" holds, `[I]`, with the review's addition.** It joins the handlers' `[C]` effect words with
  static call-site reads; the lane named `ITEMSKILL_Cast`'s callers but not `SKILLS_SrvDo`'s other seven calls, which
  all pass 0 (fix 1). (4) **skills/0003 § 2's correction is right**: `ItemCastAtUnit` pushes its entry `EDX`
  (`[ebp−0x8]`) as the cast's first stack word (the id) and `[ebp+0x8]` as the second (the level), `ret 0xC`; the
  dated note sat under the next bullet and is moved to the one it corrects (fix 4). (5) **5–9, not 5–10**: `n = Arg0 +
  low mod (Arg1 − Arg0)` is `[C]` (the count compared at `[ebp−0x98]`; `count_inc` fails 667), so 5 to 9 for the stock
  5 and 10; the 5–10 is the Shrines `Effect` editor text. `n` counts potion tries, though: a try with no free spot makes
  none and still counts (fix 3). (6) **The quest and object `MissileCreateAt` sites are admitted as named with the
  reason** (the Done-when's "the rest are named with the reason"): they are no skill functions, each passes skill 0
  and level 1 with its argument words pinned in `static.txt`, and their callers are quest handlers whose reads are
  quests/0001's. Emulating them, `0x0058C8D0` included (a small whole function whose read set looks declarable), is
  out of this plan. (7) **Reverser review-fixes rule 14 does not reach the catalogue's symbol rows.** The rule asks a
  raise when the game's own logged return (a runtime log or a reproduction on game data) agrees with a model or a
  table row. An ADR-0015/0021 emulation over a declared scratch image confirms the code's map, not the role a name
  states (ADR-0015 (3): what the offsets mean keeps its own tag), so the 26 rows stay `I`, as the 343 catalogue rows
  before them; rule 14 gains this scope sentence. **Fixes, made in the documents:** (1) § 6's effect-flag bullet and
  the Answer: `SKILLS_SrvDo`'s seven other calls pass 0 as the fifth word (`0x0056FD34` with `EAX` 0 after its
  `jne`), and no dword of the image holds the address of `SKILLS_SrvDo`, `ITEMSKILL_Cast` or its two callers
  (omission); (2) § 7: `SKILLS_PayCost`'s 0 for a row with `mana` and `lvlmana` both 0 refuses nothing, since none of
  its three calls (`0x0056F7AA` in `SKILLS_SrvStart`, `0x0056FA7A` in `SKILLS_SrvDo`, `0x005D6B48`) tests the return
  (omission); (3) § 8's after-bullet: `n` potion tries, a try with no free spot (`0x005831D0` → `0x00583270`) making
  none and still counting, so `n` is the most potions (misread; carried to the archivist entry); (4) skills/0003 § 2:
  the `EDX`-the-skill note moved onto the first bullet, which still said `EDX` the level, with "the three call sites
  lie in the item-use entries" for "callers are … `ItemUse`" (stale cross-reference; reverser review-fixes rule 12
  gains this Seen line); (5) § 2's weak-controls bullet credited `mark_caster` (74) and `tgtdo_unit` (49) to `CLASS`
  lines, which hold neither: they are whole-path classes, the `use_item` `outcomes` line's `marked=74` and the `site`
  line of `0x005C053B` (wrong anchor); (6) the spec-writer entry stated do 151's start at the target unit with no tag,
  where § 4 has it `[I]` after the boundary (overclaim). Counted: 6 (overclaim 1, misread 1, omission 2, wrong anchor
  1, stale cross-reference 1). Promoted: fixes 1 and 2 are both a claim about callers with a caller path unnamed,
  reverser review-fixes rule 9 gains them as Seen lines. Review request closed
  ([archive](../backlog/archive/2026-10-21-reverser-architect-lane-p46m12-review-plan-0046-batch-item.md)); the
  [archivist entry](../backlog/2026-10-21-reverser-archivist-plan-0046-item-skills-pettype-books-shrines-column.md)
  (Skills, PetType, Books, Shrines and Misc column readers, with fix 3's wording) and the
  [spec-writer entry](../backlog/archive/2026-10-21-reverser-spec-writer-combat-delivery-e5-item-cast-helpers-and-effect.md)
  (combat/delivery E5, with fixes 1, 2 and 6 and ruling 1's `[I]` for the composed chain) are **released**; lane
  ledger row added (the review's row is the orchestrator's at the merge). **Phase 1 status:** the seven class batches,
  9a–9d and batch 10 are accepted, twelve of fifteen batches and 234 of the 310 entries (the other 76: 8a–8c's 70 and
  the six `general` tier-A entries plan 0045 read). Phase 1 is **not** complete. **Next for 0046:** batch 8a (monster
  rows 156–189: 30 entries, start 42–53, do 83–98, 110, 111), then 8b and 8c, on the class batches' conventions, unless
  the monster-AI plan pulls one forward or takes a function as a boundary oracle (ADR-0020). Phase 2 still waits for
  0045·P3's review.
- **2026-10-21 — combat/delivery E5 from batch `item` landed for review (spec-writer, `lane/s46d`).** The released
  [spec-writer entry](../backlog/archive/2026-10-21-reverser-spec-writer-combat-delivery-e5-item-cast-helpers-and-effect.md)
  done: [combat/delivery](../specs/combat/delivery.md) E5 rewritten from [skills/0015](../findings/skills/0015-item.md)
  §§ 4–7 with the `lane/p46m12` review's fixes 1, 2, 6 and ruling 1 (handlers 20/21/30, the callers, `ITEMSKILL_Cast`,
  helper 2's first try and do 151 `[C]` to their boundaries; the composed handler → helper chain, the effect flag only
  from handler 20 without `ItemTgtDo`, do 151 starting at the target unit `[I]`), A3's entry-36 bullet scoped, a
  `SKILLS_PayCost` reimplementation note, the helpers open question struck. Tags `{C: 74, I: 58, L: 4}` →
  `{C: 80, I: 63, L: 3}`; open questions with `[L]` 3. Review request
  [to the architect](../backlog/archive/2026-10-21-spec-writer-architect-lane-s46d-review-combat-delivery-e5-item-cast.md).
- **2026-10-21 — `lane/s46d` review (architect): accept with fixes.** Reviewed on the lane (head `0a87a81`), main not
  merged (it moved to `0e760e1` with the p48r2 merge, which touches no combat spec or skills finding). Every new or
  changed E5, A3, reimplementation-note, Inputs, Evidence and open-question claim read against
  [skills/0015](../findings/skills/0015-item.md) §§ 4–7, run:2026-10-21-cat-emu-item (`check.txt`: `event_item` 3 000
  cases, outcomes `nounit=92 nochance=1328 norec=158 nobit2=332 nobit5=208 tgtdo=49 tgtdo_none=13`; `cast_item`
  `nogame=71 notarget=36 state54=184 PatternTest=163`), skills/0003 § 2, ADR-0021 and the `lane/p46m12` review's fixes
  and rulings; objdump read of handler 21 (`0x005C05A0`–`0x005C0668`), handler 30's head (`0x005C0670`–`0x005C06F9`)
  and the heads of `ItemCastAtUnit` (`0x005FDCA0`–`0x005FDD04`) and `ItemCastAtXY` (`0x005FDD60`–`0x005FDD89`). Tags
  recounted: `{C: 80, I: 63, L: 3}`, unchanged by the fixes; the five combat front matters sum to C 236 / I 190 / L 23.
  **Rulings.** (1) **The handler → helper 2 chain stays `[I]`** as the lane wrote it (the `lane/p46m12` ruling 1); the
  rewritten `[L]` names its two raise paths. (2) **The struck `[L]` is answered**: helper 2 is given the cast's own
  caster and steps its seed (`[C]`, first try), helpers 3 and 4 step no seed (`[C]` before their boundaries); what
  remains, whose unit that caster is per handler, is the composition carried by the run bullet. (3) **The restore
  `[C]` is right as scoped** to helper 2's no-room refusal (the only refusal after the aim the cases reached; the
  finding's Answer keeps the restore on other paths `[I]`). (4) **The "draws nothing of its own" bullet's `[I]` is not
  an under-claim**: its draw-free part before the boundaries is already the `[C]` bullet above it, and the rest runs
  through the start and do functions and closures whose indirect calls were not followed. (5) skills/0015 § 5's `[I]`
  bullet still says "within ±20"; the `[C]` formula beside it is exact, so no entry: the reverser corrects it at its
  next touch of § 5. **Fixes, made in the spec:** (1) helper 2's first test "at the caster's position" covered caster
  types 2, 4 and 5, which no case had (static-path dwords, the finding's `[I]`): the `[C]` sentence scoped to types 0,
  1 and 3, the static-path reading moved to the `[I]` bullet after it with `0x005FD89E–0x005FD8A4` (overclaim);
  (2) `ItemCastAtUnit` refused "a unit with no game" where the game is the caster's (`0x005FDCC1`, `ECX` = the
  caster), and `ItemCastAtXY` "makes the same tests", where it has no target to test: now the game and state tests
  (misread); (3) "a free point within ±20" for offsets `low mod 40 − 20`, −20 to +19 on each axis (misread);
  (4) handlers 21 and 30 lost the no-unit and chance ≤ 0 exits with no draw (`0x005C05C8`, `0x005C0698`), so handler
  30 read as stepping its seed for any chance, and all three lost the no-record exit (handler 30's skill range test
  too): stated once for the three (omission). Counted: 4 (overclaim 1, misread 2, omission 1). **Research-map** combat
  row rewritten: C 236 / I 190 / L 23, the batch `item` clause, skills/0015 among the findings, plan 0046's `item`
  carry. Review request closed
  ([archive](../backlog/archive/2026-10-21-spec-writer-architect-lane-s46d-review-combat-delivery-e5-item-cast.md));
  lane ledger row added. Promoted: fix 1 as a Seen line on spec-writer rule 2 (a boundary reached on one path) and
  fix 4 on rule 3 (re-read each restated condition); both rules had earlier Seen lines.
- **2026-10-21 — Phase 1 batch 8a landed for review (reverser, `lane/p46m13`, static, no harness).** The monster skill
  functions of Skills rows 156–189: start 42–53, do 83–98, 110, 111, 30 entries, all read and all emulated
  ([skills/0016](../findings/skills/0016-monster-8a.md); six start entries have no Ghidra function and were read from
  objdump). Raised by emulation (run:2026-10-21-cat-emu-8a, `tools/skills_catalogue_emu.py --batch 8a`, `check.txt`
  `b06f25a1…`, `static.txt` `f4ed00d9…`, `manifest.sha256` `10a8ce1f…`): five families, 12 600 cases, 0 mismatches, 31 boundary/call-site triples
  (site control 5 135 of 5 135), both seeds compared in every case, every dumped byte written by its case; one to eight
  negative controls per family, each family with one failing 162 or more, the nine thin ones equal to their deciding
  classes on the `CLASS` lines. New emulated helpers: `PathDirection` with its `.rdata` table, the `.data` byte map
  `0x00745600` (scanned: no store), `0x0063E7E0`, `SkillSummonClass`'s MonStats path, `MONSTATS_GetClassChainPos`,
  `0x00645F00`; the allocator observed in do 111's family only. The same tool reproduces 9a–9d, the seven class batches
  and `item` byte for byte (`repro.txt`); three development runs kept in `dev/`. Draws before the boundaries: only do 96
  (`RNG_RangeB(caster, hi − lo)`, ZakarumHeal and Bestow). Case-writer restrictions named with the reason (§§ 4–6):
  `SkillSummonClass`'s fault for a refused non-monster class, do 111's missing id test, `PathDirection`'s overflow past
  257 subtiles (an `[L]`). Surprises: do 110 casts missile 27 or 41 at stat 157's or 158's value as the level; do 85
  adds the MonStats chain position to `srvmissilea`; do 93's target words are offsets; do 98 falls back to the owner's
  room; thirteen entries make no id test. Tags: 34 `[C]`, 6 `[I]`, 4 `[L]` bullets; 38 symbols added (`I`). Dated
  note in skills/0003 § 4 (do 83). Review request
  [to the architect](../backlog/archive/2026-10-21-reverser-architect-lane-p46m13-review-plan-0046-batch-8a.md); column readers
  [to the archivist](../backlog/2026-10-21-reverser-archivist-plan-0046-8a-skills-monstats-missiles-column-reade.md).
  No spec-writer entry: no spec states these functions yet (Phase 3 takes the finding).
- **2026-10-21 — `lane/p46m13` review (architect): accept with fixes.** Reviewed on the lane (head `53060fe`), main not
  merged (it moved to `bce3d86` with the p48r2 and s46d merges; neither touches a skills finding, and none of the 38
  addresses or names is on main's side; main's appends to this log and to the ledger will meet this entry at the merge,
  keep both). `sha256sum -c manifest.sha256` (`10a8ce1f…`, 106 lines) passes. From the lane's tool (`e2f67728…`), under
  a 4 GB scope, `cases --batch 8a`, `check --batch 8a` and `static --batch 8a` reproduce the 15 case files, `cases.txt`,
  `check.txt` (`b06f25a1…`) and `static.txt` (`f4ed00d9…`) byte for byte; `repro.sh` rerun into the review's scratch
  gives the kept `repro.txt` (`485fdbef…`) byte for byte (9a–9d, the seven classes and `item`). Recounted from
  `check.txt`: 12 600 cases, 0 bad, 0 undeclared, 0 stopped; site controls 1 041 + 1 459 + 970 + 1 159 + 506 = 5 135
  over 8 + 10 + 6 + 6 + 1 = 31 `site` lines; negative controls 6 + 8 + 7 + 5 + 1, the nine `CLASS` lines equal to their
  controls. Read against objdump: do 96 whole (`0x005CC840`–`0x005CC94E`), do 110 whole (`0x005CE1B0`–`0x005CE2AB`),
  do 111 whole (`0x005CE670`–`0x005CE782`), do 93's step and sixth (`0x005CC0E8`–`0x005CC1CC`), do 95's tail
  (`0x005CC5A8`–`0x005CC687`) and `PathDirection` up to its first fold (`0x0064FC60`–`0x0064FD2D`); a scan of the
  thirty bodies (`0x005CAE40`–`0x005CCD20`, `0x005CE1B0`–`0x005CE790`) for a call of `RNG_Step`, `RNG_Range`,
  `RNG_RangeB`, `RNG_RangePow2*`, `RNG_RangeOffset`, `RNG_RandLoHi` or the multiplier `0x6AC690C5` finds one call,
  `0x005CC8ED` in do 96 (the multiplier's one hit, `0x005CE2C0`, lies in the next function `0x005CE2B0`, outside the
  batch). Tags 34 `[C]`, 6 `[I]`, 4 `[L]` bullets as filed (the fixes add none). **Rulings.** (1) **The six start
  entries with no Ghidra function are admitted.** A Ghidra function boundary is no evidence; the entry is the table
  dword (`table_entries=30`, `entry_words=30`), the code was read from objdump, and the emulator runs from that
  address by the program's own flow (ADR-0015 needs no Ghidra function). Their symbol rows stand at `I`. (2) **The
  first-time helpers are admitted as emulated.** `PathDirection`'s direction is compared directly (do 87 writes it as a
  byte over the id slot, dumped and compared) and its `.rdata` table is a declared image read; `0x00745600` is a
  `.data` input of a map claim, admitted on the `sor` ruling 3 ground (an input set on purpose needs no writer scan),
  and the scan cited does meet that ruling's condition (every instruction naming `0x007455C0`–`0x007456FF`, which takes
  in `moffs` stores and immediates); that the running game holds the file's 64 bytes stays outside the `[C]`
  (ADR-0015 (3), § 2's last bullet). `SkillSummonClass` with `0x0058F710`, `MONSTATS_GetClassChainPos` (its table
  pointer set in the spec), `0x0063E7E0` and `0x00645F00` are emulated callees like the class batches'. (3) **The
  allocator observed in `aura_8a` only and guarded elsewhere is right**: a guard stops a case that reaches it, and
  `stopped=0` in the other four families shows none did. (4) **Start 48's `Fatal` as an outcome is admitted** on the
  `nec` ruling 2 precedent (`Fatal` a boundary, 16 cases, call site `0x005534A8` asserted); its own no-path refusal
  stays `[I]`, as the self-check wrote. (5) **The case-writer restrictions are admitted as named with the reason.**
  `SkillSummonClass`'s fault and unwritten outs and do 111's `[0x154]` read are faults or undefined outs no model can
  compare (ADR-0015 leaves faults out), and no stock row reaches them; `PathDirection`'s bound is a real wrap, but it
  is 258, not 257 (fix 2), and the `[L]` stays under *Open questions*. (6) **Thin coverage is admitted.** Do 88's
  `SKILLS_GetTargetXY` refusal has one case (`noxy=1`, `miss_8a`): it decides under reverser rule 10, since the
  wrong readings (no refusal, a default point) reach `MissileCreate` and could not return 0 by chance; the count is now
  in § 6 (fix 4). Do 97's collision test has 55 cases, every one comparing the mask, point and path pointer, and
  `mask_1c09` fails all 55: enough for a constant mask. (7) **"The only pre-boundary draw is do 96" holds** in the
  Answer's scope (the caster's and the target's seeds, compared in every case), and the review's call scan backs it
  for every seed inside the thirty bodies; draws inside emulated helpers (start 32 within start 42) are covered only by
  the two compared seeds, as the sentence says. (8) **The unfollowed callers are named with their counts** (do 98 from
  do 129 at `0x005D1B75`, `0x005CC3B0` twice from do 152) and go to 8c and 8b, as reverser rule 9 asks. (9) **No
  spec-writer entry is right**: no spec states these functions; Phase 3 takes skills/0016. **Fixes, made in the
  documents:** (1) § 5 `PathDirection`: the `(−1 − d) & 0xF` fold applies when **x** is the major axis (`jg` at
  `0x0064FCB3`, the swap branch sets the flag), not y; the model has it right (misread); (2) § 5 and *Open questions*:
  the `× 0x7F` product fits for a minor difference up to 258 subtiles (258 · 2¹⁶ · 127 = 2 147 352 576) and wraps from
  259, "257" before; the tool's `near8` docstring ("below 258") carries the same slip and is left for the next tool
  revision, the hash being cited (misread); (3) § 1 and § 6: `0x005CC5C0` is do 95's call with no target point **or a
  failed `MissileCreate`** (`0x005CC5DC`), not "after its missile"; § 6's after-bullet gains that path and the two
  `CancelEvents` before the re-queue (misread); (4) § 6 do 88: the refusal's one case named (omission); (5) § 3 do 110:
  `MissileRec(m)` none → 0 on the `srvmissilea` path (`0x005CE264`) (omission). Counted: 5 (misread 3, omission 2).
  Promoted: fix 2 and the `lane/p46m11` review's ring-count wrap are both an integer wrap bound stated without the
  computation, reverser review-fixes rule 15. Review request closed
  ([archive](../backlog/archive/2026-10-21-reverser-architect-lane-p46m13-review-plan-0046-batch-8a.md)); the
  [archivist entry](../backlog/2026-10-21-reverser-archivist-plan-0046-8a-skills-monstats-missiles-column-reade.md)
  (Skills `Param4`, `lob`, `summon`/`summode`, MonStats `spawn*` and `+0x4B`, Missiles `Vel`/`VelLev`, MonStats2
  `InfernoLen`/`InfernoAnim` readers; read against § 3–6, no fix touches it) is **released**; lane ledger row added (the
  review's row is the orchestrator's at the merge). **Phase 1 status:** the seven class batches, 9a–9d, batch 10 and
  8a are accepted, thirteen of fifteen batches and 264 of the 310 entries (the other 46: 8b–8c's 40 and the six
  `general` tier-A entries plan 0045 read). Phase 1 is **not** complete. **Next for 0046:** batch 8b (it takes do 152's
  two `0x005CC3B0` calls), then 8c (do 129's direct call of do 98), on the class batches' conventions, unless the
  monster-AI plan pulls one forward or takes a function as a boundary oracle (ADR-0020). Phase 2 still waits for
  0045·P3's review.
- **2026-10-21 — Phase 1 batch 8b landed for review (reverser, `lane/p46m14`, static, no harness).** The monster skill
  functions of Skills rows 190–289: start 54, 55, 59, 60, 64, do 99–109, 112, 125–127, 141, 152, 22 entries, all read
  and all emulated ([skills/0017](../findings/skills/0017-monster-8b.md)). Raised by emulation
  (run:2026-10-21-cat-emu-8b, `tools/skills_catalogue_emu.py --batch 8b`, `check.txt` `2f000a04…`, `static.txt`
  `4c181a27…`, `manifest.sha256` `1c9c42ff…`): four families, 9 200 cases, 0 mismatches, 27 boundary/call-site triples
  (site control 3 698 of 3 698), both seeds compared in every case, every dumped byte written by its case; three to
  eight negative controls per family, each family with one failing 152 or more, every control equal to its deciding
  class on the 24 `CLASS` lines. The same tool reproduces 9a–9d, the seven class batches, `item` and 8a byte for byte
  (`repro.txt` `948be1e1…`); four development runs and a first repro kept in `dev/`. **Carried item:** do 152's two
  `0x005CC3B0` calls are `0x005CC770` (no target point, or `MissileCreate` returning 0) and `0x005CC827` (after a created
  missile, the game frame not below the node's end frame, or no state 12); do 152 is do 95's code instruction for instruction
  (`static.txt`: 147 each, 0 differ), its first call emulated to `CancelEvents`. Draws before the boundaries: do 112's
  inline step of the caster's seed (the curse index, low word mod 5) and start 55's `RNG_RangeB` on a local seed from the
  two guids; no other. Surprises: do 112 casts one of five fixed curse rows (66, 72, 82, 87, 91) from their own columns,
  row 91 (Lower Resist) with a Decrepify-like block and an unreachable resist branch; do 141 puts skill 285 into its block
  whatever the id; do 104 writes `summode` over its level argument and never uses it; do 105's missiles take their y
  position from the x offset; do 127's life unit is 0 for a player caster; start 59 is start 53 with calc1 for calc2.
  Tags: 32 `[C]`, 5 `[I]`, 3 `[L]` bullets; 28 symbols added (`I`). Review request
  [to the architect](../backlog/archive/2026-10-21-reverser-architect-lane-p46m14-review-plan-0046-batch-8b.md); column readers
  [to the archivist](../backlog/2026-10-21-reverser-archivist-plan-0046-8b-skills-missiles-column-readers.md). No
  spec-writer entry: no spec states these functions yet (Phase 3 takes the finding).
- **2026-10-21 — `lane/p46m14` review (architect): accept with fixes.** Reviewed on the lane (head `f4e5227`), main not
  merged (it moved to `a12993b`: plan 0048 closed and moved to `plans/done/` with its links rewritten; none of it
  touches a skills finding, and none of the 28 new addresses or names is on main's side; main's appends to this log and
  to the ledger will meet this entry at the merge, keep both). `sha256sum -c manifest.sha256` (`1c9c42ff…`, 118 lines)
  passes. From the lane's tool (`ba63f2a8…`), each step under its own 4 GB scope, `cases --batch 8b`, `check --batch 8b`
  and `static --batch 8b` reproduce the twelve case, memory and expectation files, `cases.txt`, `check.txt`
  (`2f000a04…`) and `static.txt` (`4c181a27…`) byte for byte; `repro.sh` rerun into the review's scratch gives the kept
  `repro.txt` (`948be1e1…`) byte for byte (9a–9d, the seven classes, `item` and 8a, 13 `REPRO` lines, every one
  `differ=0 check=same static=same`). Recounted from `check.txt`: 9 200 cases, 0 bad, 0 undeclared, 0 stopped; site
  controls 1 296 + 1 172 + 703 + 527 = 3 698 over 27 `site` lines; 24 `CLASS` lines. `re/symbols.csv`: the 28 rows are
  the only change (the 3 437 base rows kept in order and unchanged, each new row between its neighbours by address, the
  11 order breaks the file already had unchanged). Read against objdump: do 112 whole (`0x005CE2B0`–`0x005CE4D8`),
  do 127 whole (`0x005D16A0`–`0x005D17F0`), start 55's seed and count (`0x005CD94A`–`0x005CD9DF`), do 105's row
  (`0x005CD7BD`–`0x005CD860`), do 152's tail (`0x005CC740`–`0x005CC83A`), do 104's argument slots and do 141's block
  constants; a scan of the batch's bodies for a call of `RNG_Step`, `RNG_Range`, `RNG_RangeB`, `RNG_RangePow2*`,
  `RNG_RangeOffset`, `RNG_RandLoHi`, `RNG_SeedInit*` or the multiplier `0x6AC690C5` finds start 55's three calls, do
  107's three `RNG_RangeB` (after its `InMeleeRange` boundary), do 112's inline step and the callback `0x005CD110`'s
  pair (do 102 passes it as a pointer and does not call it): no other. Tags 32 `[C]`, 5 `[I]`, 3 `[L]` bullets (the
  fixes add none). **Rulings.** (1) **`repro.sh`'s per-step scopes are admissible**, and the earlier reviews' repro
  claims stand. The change moves the scope boundary only: what each step runs and what it compares are unchanged. An
  out-of-memory end can only make a step print nothing and read `DIFF` (as `dev/repro-dev1.txt` shows for `ass`); it
  cannot print `same`, which needs a byte-equal file, so a `same` under the old script was never a false one, and this
  review reproduced every earlier batch's line under the new one. (2) **Do 152 = do 95 is admitted** on the
  147-instruction comparison (`static.txt`, 0 differ, in-body jump targets relative), backed by do 152's own emulated
  cases at `0x005CC78A` and `0x005CC415`. Its first `0x005CC3B0` call (`0x005CC770`, reached with no target point or a
  failed `MissileCreate` at `0x005CC78C`) is `[C]` up to `CancelEvents` (nested return `0x005CC775` at `0x7FEFFF84`);
  the second (`0x005CC827`, after a created missile, the game frame not below the node's end frame or no state 12) is
  `[I]` after `MissileCreate`, as filed. The 8a carried item is closed. (3) **Do 112's draw is admitted as `[C]`.** The
  inline step (`0x005CE2BA`–`0x005CE2E0`) is the first code, with no caster test; `k` is the stepped low word (the seed's
  low 32 bits, the spec's usage) mod 5 by the `0xCCCCCCCD` multiply; both seeds are compared in all 800 cases and
  `k_mod4` (578) equals its class. The five fixed rows are read from `.rdata` `0x006E3228` (a pin), the block's five
  branches match the jump table, and row 91's resist branch (`0x005CE470`, stats 37–45) is unreachable by arithmetic
  (`k ≤ 4`, `ja` at `0x005CE3CA`): `[I]` as filed is right, since no case reaches it. (4) **Start 55's local seed is
  admitted** as a map: `RNG_SeedInitOne` then `RNG_SeedInit(Tguid + Uguid)` (`0x005CD96A`–`0x005CD984`), compared
  through the count (no unit's seed changes, both compared); `seed_t` (111) is the deciding class of the cases where
  the caster's guid changes the count, which a wrong seed could match only by chance on a small range, and 111 is
  enough. (5) **The thin controls decide** under reverser rule 10: `dmg_nomin` (14) — the uncapped reading reaches a
  different `UnitSetStat` value in every one; `hire_any` (24) — the wrong reading reaches `RoomUnitRemove` instead of
  returning 0; `p4_first` (26) — the wrong order reaches the other boundary (`0x006212C0` at `0x005CD4CC` against
  `PathSetSpeed` at `0x005CD481`). None can match by chance. (6) **The four case-writer-unreached paths stay `[I]`**:
  do 126's target without a caster path and start 54's path used untested are null reads ADR-0015 leaves out; start
  55's −1 guid for a null caster sits behind two calls that take the caster first; do 112's default branch is
  unreachable (ruling 3). (7) **The surprises are code readings inside the map and stand**: do 141's `0x11D` is an
  immediate (`0x005D2F15`); do 104's slot write is `SkillSummonClass`'s out pointer `&lvl` (`lea eax, [ebp+0xC]`,
  `0x005CD60D`), and the slot is not read after it; do 105's y position from `dx / 6` (`0x005CD81B`–`0x005CD838`, both
  position words from `esi`); do 127's life unit 0 for a non-monster caster (`0x005D1724`–`0x005D1743`). What the game
  shows for them stays under *Open questions*. (8) **The archivist entry is released**
  ([entry](../backlog/2026-10-21-reverser-archivist-plan-0046-8b-skills-missiles-column-readers.md); read against
  §§ 3–5, no fix touches a column it names). **No spec-writer entry** is right: no spec states these functions;
  Phase 3 takes skills/0016 and 0017. (9) The tool's `near8` docstring still says "below 258" (the `lane/p46m13` review
  fix 2 left it to the next revision); it is carried to 8c's tool revision, the hash here being cited. `dev/notes.txt`
  counts dev1's "99 mismatches" with the `half_floor` control's line; the finding's 98 cases (16 + 46 + 36) is right,
  and the hashed development note is left as it is. **Fixes, made in the documents:** (1) § 6: do 105's `h·A`, `h·B`
  cannot wrap on a path that uses them (`n > 0` gives `|h·A| ≤ 2 147 483 646`; the `n ≤ 0` wrap at `h·(−2)` = 2³¹ returns
  1 first); the subtraction `dx − h·A` is what wraps; do 141's sum is modulo 2³² with two free inputs (misread; reverser
  rule 15); (2) this log's lane entry: do 152's second call is at a game frame **not below** the node's end frame, not
  "past" it (misread); (3) § 5 do 112: `cid` below 0, at the Skills count or with no record → 0 (`0x005CE2F4`–
  `0x005CE31A`) (omission); (4) § 4 do 127: the cap reworded to `min(d, life)` from "the target's life when not above
  it" (other). Counted: 4 (misread 2, omission 1, other 1). Promoted: fix 1 is a third Seen line on reverser rule 15
  (name the operation that wraps and whether a wrapping path reaches a use). Review request closed
  ([archive](../backlog/archive/2026-10-21-reverser-architect-lane-p46m14-review-plan-0046-batch-8b.md)); lane ledger
  row added (the review's row is the orchestrator's at the merge). **Phase 1 status:** the seven class batches, 9a–9d,
  batch 10, 8a and 8b are accepted, fourteen of fifteen batches and 286 of the 310 entries (the other 24: 8c's 18 and
  the six `general` tier-A entries plan 0045 read). Phase 1 is **not** complete. **Next for 0046:** batch 8c, carrying
  do 129's direct call of do 98 (`0x005D1B75`) and the `near8` docstring, on the class batches' conventions, unless the
  monster-AI plan pulls one forward or takes a function as a boundary oracle (ADR-0020). Phase 2 still waits for
  0045·P3's review.
- **2026-10-21 — Phase 1 batch 8c paused at the owner's request (reverser, `lane/p46m15`, static, no harness).** Done
  and committed: the monster skill functions of Skills rows 290–338, start 61–63, do 128–137, 139, 140, 147–149, 18
  entries, all read and all emulated ([skills/0018](../findings/skills/0018-monster-8c.md), draft for review); run
  run:2026-10-21-cat-emu-8c (`tools/skills_catalogue_emu.py --batch 8c`, tool `8911d02a…`, `check.txt` `500b673c…`,
  `static.txt` `873640da…`, `manifest.sha256` `9dc63588…`): four families, 8 800 cases, 0 mismatches, 23
  boundary/call-site triples (site control 2 376 of 2 376), every control equal to its deciding class (18 `CLASS`
  lines); `repro.txt` (`2a44bd63…`) reproduces 9a–9d, the seven class batches, `item`, 8a and 8b byte for byte. Carried
  items done: do 129's direct call of do 98 (`0x005D1B75`, emulated to that call; skills/0016's open question
  annotated), the tool's `near8` docstring (258 fits, 259 wraps). 30 symbols added (`I`); experiments record appended.
  Draws: do 131's `RNG_Range(caster, 100)`, do 140's inline steps of the caster's seed; Baal's arm of `0x0063EFA0`
  (not emulated, § 7) adds two or three `RNG_Range` on the caster's seed. Tags as drafted: 27 `[C]`, 10 `[I]`, 3 `[L]`
  bullets. **Next (resume):** (1) run `python3 -I tools/gate.py` (it was red only on the then-untracked 0018 links;
  recheck the W3 warnings for the new symbols once 0018 is tracked); (2) self-check 0018 against
  `.claude/skills/reverser/references/review-fixes.md` rules 1–15 (in particular rule 13's "after, `[I]`" in the
  Answer and rule 2's counts against the kept `check.txt`); (3) file the archivist entry (column readers: Skills
  `aurastate`/`auratargetstate` as gates in do 129/131/137, `summon`/`summode`, `sumumod`, `sumoverlay`, `srvoverlay`,
  `lob`, `ResultFlags`/`HitFlags`/`HitClass` in do 134, MonStats `BaseId` tests 453/546/551, the monster data bytes
  `+0x0E`/`+0x0F`) and the review request to the architect (modelled on the archived p46m14 request); (4) append the
  lane-landed log entry. **What remains of Phase 1 after 8c:** batch 8c's review, and the six `general` tier-A entries
  plan 0045 read (start 1, 2, 65, do 1, 3, 5 of rows 0–5; Unsummon's start 3 and do 4 went to batch 10) — read by plan
  0045, not re-read by a 0046 batch; the architect to rule whether they count as covered for Phase 1's close.
