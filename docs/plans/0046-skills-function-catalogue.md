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
  `COMBAT_PrgFinisher` (start 25 at `0x005D6399` and `0x005D63E1`; do 42 `0x005D5A8C`, 50 `0x005D71F2`, 52
  `0x005D79DF`); the item, shrine and object batch reads which unit `ITEMSKILL_Cast` gives the `ItemTarget` 2 helper
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
