# 0049 — Backlog sweep 5: the static loose ends, the recipe register and the gate warnings

> **Status:** approved 2026-10-20 (owner)
> **Created:** 2026-10-20
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0006-docs-gate, 0007-fetched-leads-only, 0015-emulated-reproduction, 0018-backlog-one-file-per-entry

## TL;DR

**Question:** which open backlog entries can be closed by a reading, a tool fix or a recipe pass, with no harness slot?
When it is done, the entries listed below are closed (or carried with a stated reason), the save-recipe register and
its test match the recipes on disk, and the gate's outstanding W1 and W3 warnings outside `data/excel` are gone.

## Context

- **The backlog on 2026-10-20:** 55 open entries before this plan's triage closed three stale ones (the rng/seeds
  step-note-2 entry, the plan 0037 resume-lane entry and the plan 0037 Phase 4 wiki entry: each was done and merged).
  Of the 52 left, about half are plan 0038 Phase 3 re-tag inputs, each waiting for its cluster's harness batch; they
  stay with plan 0038. Plan 0044's, plan 0042's and the skills plans' entries stay with those plans. This sweep takes
  the rest that need no slot.
- **Plan 0039.** Its only remainder is the data/excel fold (P1b (a), P1c (a) and the 11 data/excel W1 warnings,
  backlog `2026-10-17-reverser-spec-writer-gate-w1-a-c-i-statement.md`), already tied to plan 0038's data/excel
  re-tag after batch H3b. Plan 0039 is **closed** (owner, 2026-10-20) and that fold is an item of plan 0038 Phase 3's
  data/excel cluster; this sweep does not take it.
- **The gate on 2026-10-20** (`python3 -I tools/gate.py`, fast tier GREEN): 22 warnings, 12 W1 (11 in
  `docs/specs/data/excel.md`, held as above, and `docs/findings/items/0001-tc-resolution.md:992`) and 10 W3 (symbols
  cited by no doc: `sub_0061A180_ActRoomsHead`, `INV_GetOtherWeapon`, `g_OptionApplyTable`, `g_nItemTypes`,
  `g_MonPropLink`, `g_nLevels`, `g_nDifficultyLevels`, `g_nWeapons`, `g_nArmor`, `g_nMisc`).

## Phases

### Phase 0 — The recipe register
- **Owner skill:** archivist
- **What:** one pass over the plan 0042 save recipes and one table question.
- **Items (5):**
  1. `2026-10-17-reverser-archivist-pin-the-plan-0042-save-loads.md`: pin the 18 quest and travel save loads;
  2. `2026-10-18-reverser-archivist-document-the-plan-0042-part-2-quest-recipes.md`: document the eleven part 2
     recipes;
  3. `2026-10-19-architect-archivist-register-the-plan-0042-quest-recipes-in-test.md`: register them in
     `tools/test_d2s.py` (`test_every_recipe_has_a_base` passes on `main`);
  4. the four `quest-p3*` recipes of plan 0042 part 3 (`lane/p42r`, merged 2026-10-20; its archivist entry), in the
     same pass;
  5. `2026-10-19-architect-archivist-unique-items-carry1-has-a-reader.md`: UniqueItems' `carry1` reader question.
- **Done when:** `python3 -I tools/test_d2s.py` passes with every recipe under `tools/d2s_recipes/` registered; each
  item's entry is closed with its resolution; the gate is green.

### Phase 1 — Static readings and tool fixes
- **Owner skill:** reverser (one static Ghidra lane, `-Xmx3G`; no slot)
- **What:** answer or close each entry below, in this order; an entry that turns out to need a slot is annotated with
  the plan that will take it and left open.
- **Entries (13):**
  1. `2026-10-17-architect-reverser-static-sweep-remaining.md`: prune first (its 0042 Phase 0/1, 0043 Phase 1 and
     Q23 items are done or moved), then work the rest;
  2. `2026-10-17-architect-reverser-monsters-0003-s7-stale-fixed-class-rows.md`: the stale *`0x11`–`0x20`* bullet;
  3. `2026-10-17-reverser-reverser-plan-0039-p1c-residues-not-blocking.md` (a)–(e) ((a), `0x005C09E0`, also feeds
     plan 0046);
  4. `2026-10-17-architect-reverser-plan-0039-p1c-review-follow-ups.md` (a), a fetch under ADR-0007 in this lane;
  5. `2026-10-17-architect-reverser-plan-0040-phase-1-review-follow.md` (a)–(c), the orphans of closed plan 0040;
  6. `2026-10-17-reverser-reverser-plan-0041-op-6-7-emulation.md` (optional: ops 6 and 7 under ADR-0015);
  7. `2026-10-16-architect-reverser-plan-0038-s1a-review-creation-question.md`;
  8. `2026-10-16-architect-reverser-plan-0038-s2c-review-static-leftovers.md`: check it against
     [quests/0001 § 1](../findings/quests/0001-progression.md) (1 592 record-function calls, the register bits by act
     section) and close what that answers;
  9. `2026-10-16-architect-reverser-plan-0038-phase-3-review-wording.md` (drlg/0002, the logic-record wording);
  10. `2026-10-16-architect-reverser-plan-0038-s1a-review-tool-follow.md` (a) and (c);
  11. `2026-10-16-architect-reverser-plan-0038-s1b-review-follow-ups.md` (commit the prototype as a new
      `tools/sweep_s1b.py` version with its sha256);
  12. `2026-10-16-architect-reverser-plan-0038-h4b-review-tool-follow.md`;
  13. `2026-10-17-architect-reverser-plan-0038-s1e-review-follow-ups.md` (b).
- **Gate warnings:** the W1 at `docs/findings/items/0001-tc-resolution.md:992` (an anchor or a tag change), and the
  three W1 the `lane/p42r` merge added (`docs/findings/quests/0001-progression.md` lines 2281 and 2283,
  `docs/findings/quests/0002-travel.md` line 577 on `main` `e3dce6f`); the ten
  W3 symbols, each cited where it is used or its row annotated (the gate's W3 rule).
- **Done when:** each entry is closed with a resolution or annotated with its destination; findings sections cite
  addresses; the gate's W1/W3 count outside `docs/specs/data/excel.md` is 0; the architect's review passes.

### Phase 2 — Spec wording
- **Owner skill:** spec-writer
- **Items (1):**
  1. `2026-10-17-architect-spec-writer-rbs4-town-follow-and-outdoor-7.md` (drlg/lifecycle's town-follow question,
     drlg/outdoor 7). (The rbs2 readings entry drafted here was closed at the `lane/p42r` review, 2026-10-20.)
- **Done when:** the entry closed; the specs' changes tagged; the architect's review passes.

## Resources and limits

- **Static:** Phase 1 holds **one** of the two static Ghidra lanes; Phases 0 and 2 need none.
- **Harness:** none.
- **Rotation:** past about 4 h the lane checkpoints; Phase 1 may be split at any item boundary.

## Open questions

- **Human entries.** `2026-10-11-archivist-architect+human-is-1-14d-s-patchd2-mpq.md` is parked by the owner
  (mechanics over patch nuance) and stays open (owner, 2026-10-20). The optional owner-play entries
  (`2026-10-17-architect-human-plan-0038-h6d-diablo-owner-pair.md`,
  `2026-10-17-architect-human-plan-0042-owner-play-boss-steps.md`) stay with their plans; the second closes when plan
  0042 closes.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-20 — Drafted (architect, `lane/plans45`).** Status `proposed`; three stale entries closed at the triage.
- **2026-10-20 — Approved (owner, via the orchestrator).** Plans 0045–0049 and ADR-0020 approved as proposed; the run
  order of the [plans index](README.md#run-order-unattended-queue-set-2026-10-20-plans-00380049) is the current queue.
- **2026-10-20 — Phase 0 landed (archivist, `lane/p49a`).** Items 1–5 done, no harness, no Ghidra.
  - **Register:** 16 plan 0042 Phase 2 recipes (`quest-tpc`; part 2's `quest-talk1`..`5`, `quest-talk1c`..`4c`,
    `quest-orbwill`, `quest-death`; part 3's four `quest-p3*`) added to `tools/quest_saves.py` SET and EXPECT (rows
    written from the run records; `check` 33 recipes 0 bad) and to `tools/test_d2s.py` `RECIPE_BASES`; the suite is
    green again (45 tests OK; `test_every_recipe_has_a_base` passes with all 213 recipes registered).
  - **Pins `[C]`:** today's build of each recipe equals the save the run installed: the 17 Phase 0/1 recipes and
    `quest-tpc` against `loads.txt`'s built prefixes (18 of 18), part 2 and 3 against the `<log>.in.d2s` hashes of
    their manifests (14 of 14 loaded). 32 pinned; `quest-talk2c` and `quest-talk3c` were never loaded and stay
    unpinned.
  - **Docs:** [d2s.md § Plan 0042 Phase 2 saves](../formats/d2s.md#plan-0042-phase-2-saves) (the loads' outcome, the
    part 2 and 3 tables, the hashes); the two "not loaded" sentences above it updated.
    [UniqueItems.md](../tables/UniqueItems.md) cites two `carry1` readers (`0x0055CA40` through the item-move gate, from
    items/0010; `0x00575FA0` in `NPC_SellItem`, from items/0011, with the Annihilus sale `[C]`); the open question
    keeps `lvl req` and a full xref of 0x006CE270.
  - **Surprise:** the classic `quests: all` sets no Act V word (EXPECT's `ALL_C`); a second reader (`0x0055CA40`)
    was already in items/0010, which the entry did not name.

