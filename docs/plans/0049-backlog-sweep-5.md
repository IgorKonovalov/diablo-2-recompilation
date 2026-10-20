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
- **2026-10-20 — Phase 1 landed (reverser, `lane/p49r`; review requested).** Static only: no slot. Ghidra ran on its
  own project copy (`-Xmx3G`), with objdump as the second tool. Kept outputs are under `workspace/logs/p49r/` (manifest
  `p49r-manifest.txt`, `sha256sum -c` clean); the new tool is `tools/sweep_p49r.py` (`tables`, `excel`, `qsites`).
  - **Entries:** 12 of the 13 are closed, and the queue entry (item 1) is pruned and closed. Items 6 (op 6/7 emulation)
    and 13 (S1e (b)) are optional, not taken, and annotated as out of this plan.
  - **Readings** (all `[I]`):
    - MonPlace rows 19–21, 24–28 ([monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)).
    - `0x005C09E0` = `STATEVENT_Reanimate`, the item property `reanimate`, not a skill; `FormationSpawn` case 5 is never
      reached; `MissileSpawnOwnedMonster` = `bonewallmaker` ([items/0002](../findings/items/0002-quality-roll.md#plan-0049-phase-1-2026-10-20-static)).
    - Mode word 1 = *Battle.net*; a saved corpse loses its stat 13; the starting items' freed property list explains the
      48 empty lists, and the other 5 are `d2s.py`-built ([player/0001](../findings/player/0001-creation.md#plan-0049-phase-1-2026-10-20-static)).
    - The 45 register sites and 12 steps clears are traced for qd 8, 10 and 19 ([items/0010](../findings/items/0010-quest-drops.md#plan-0049-phase-1-2026-10-20-static-the-s2c-static-leftovers)).
    - Act `+0x50`, the wanderer's alignment, the 31 pin sites ([drlg/0009 § 11.4](../findings/drlg/0009-room-lifecycle.md#114-the-plan-0040-phase-1-review-follow-ups-plan-0049-phase-1-lanep49r-static)).
    - The H5c release order ([drlg/0002](../findings/drlg/0002-room-build-draws.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)).
    - `0x0056EDE0` = `MissileCreateAt`: missiles 288, 332 and 625 ([quests/0001 § 7](../findings/quests/0001-progression.md)).
    - The src:arreat-summit-experience re-fetch (ADR-0007): two verdicts, held with refinement and held.
  - **Tools:** `sweep_s1a.py` (breakdown, admission note), `sweep_s1b.py` (indirect-call split 359/115/58/0;
    re-seeds 132/132 and 0/25), `monstats.py` (hireling `LIVE`), `drlg.py` (refuses a second game in one log).
  - **Gate:** the W1 at items/0001:992 and the three `lane/p42r` W1 got anchors. The ten W3 symbols are now cited where
    they are used. The W1/W3 count outside `docs/specs/data/excel.md` is 0.
  - **Symbols:** 3 new `I` rows (`sub_0056EDE0_MissileCreateAt`, `STATEVENT_Reanimate`, `g_MissileSrvDoFuncs`); none
    in lane A's skills-dispatch area.
  - **Surprise:** the "five rare cube outputs" were never game creations.
