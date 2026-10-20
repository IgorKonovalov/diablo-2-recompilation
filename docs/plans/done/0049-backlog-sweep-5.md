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
- **Items (2):**
  1. ~~`2026-10-17-architect-spec-writer-rbs4-town-follow-and-outdoor-7.md` (drlg/lifecycle's town-follow question,
     drlg/outdoor 7).~~ Done by `lane/p38s5` (merged 2026-10-20), so nothing is left of it here. (The rbs2 readings
     entry drafted here was closed at the `lane/p42r` review, 2026-10-20.)
  2. `2026-10-20-reverser-spec-writer-plan-0049-phase-1-inputs-for-the-specs.md` (added at the Phase 1 review): the
     Phase 1 readings for monsters/special, drlg/room-tiles, drlg/lifecycle, items/quest-drops, player/creation,
     items/tc and quests/progression, and rng/seeds row 3, with the review's tags.
- **Done when:** the entries closed; the specs' changes tagged; the architect's review passes.

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
- **2026-10-20 — Phase 0 reviewed (architect, `lane/p49a` review): accept with fixes.** Re-run after merging `main`:
  `test_d2s.py` 45 tests OK, `quest_saves.py check` 33 recipes 0 bad. Pins spot-checked: 10 hashes against
  `quests2-manifest.sha256`, `quests3-manifest.sha256` and `loads.txt` (full-length matches for `quest-talk1` and
  `quest-p3wpact`; `quest-talk2c`/`3c` in no manifest, as stated). The three `carry1` rows (Gheed's Fortune, Annihilus,
  Hellfire Torch) recounted over the table; both readers resolve in `re/symbols.csv` and are tagged as their findings
  tag them. The classic `quests: all` note is right: it is `tools/d2s.py`'s documented rule (words 28 and 35–40 only
  in an expansion save), now said so. Fixes (4, made in the docs): d2s.md the written-back act bytes are
  `[0x80 | act, 0, 0]`; the word-40 bit-10 join is in Normal, the played difficulty; the classic note attributed to
  `d2s.py`'s keys; UniqueItems.md the gate refuses when another player of the game holds the copy too
  (items/0010 § 5). Phase 0 done.
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
- **2026-10-20 — Phase 1 reviewed (architect, `lane/p49r` review): accept with fixes.** `main` merged first (one
  conflict, this log; both sides kept); `backlog.py archive` clean. Kept outputs `sha256sum -c` clean (11 of 11), and the
  five tool hashes of the manifest match the files; `test_sweep_s1a.py` (5) and `test_sweep_s1b.py` (6) pass. Anchors
  read again with objdump on the pinned `Game.exe`: `AddStatEvent`'s bound and table (0x0056E746–0x0056E74B), entry 31
  = 0x005C09E0 at 0x0073262C, the missile dispatch at 0x005ADC97–0x005ADCA7 and entry 13 = 0x005AEDA0, `MissileCreateAt`
  calling `MissileCreate` (0x0056EE79), `STATEVENT_Reanimate`'s draw and event calls, `DUNGEON_ActCreate`'s store and
  both callers' third push, `StartItemCreate`'s `(4, 2)` and free, the MonPlace difficulty test at 0x0054EAA8, and the
  register-bit sites 0x005BB96B, 0x005BBA6F and 0x005BA2DB. `re/symbols.csv` after the merge: no duplicate address or
  name; the three new rows do not clash with `lane/p45r`'s (a reuse note for `lane/p45m` is filed:
  `2026-10-20-architect-reverser-plan-0045-p1-2-reuse-the-p49r-missile.md`). The re-fetch is recorded in
  `docs/sources.md`; no external decompiled code.
  - **Rulings.** (1) **qd 10 and qd 19 raised** (S2c: raised +2, raised in part −2). The trace is a closure over every
    call of the five record functions, the kind of objdump closure the S1b review accepted for "no draw", with S2c's
    logged writes behind it; its limits (a store outside the five functions, the A3Q4 party bit bounded by its quest's
    code window) are written beside qd 10. qd 8 stays raised in part; its remainder is answered `[I]`. (2) **Act
    `+0x50` settled `[C]`**: the writer and both callers' constants plus § 11's run values on both sides (30 985 server
    checks, 8 277 client releases) are two sources; the unscanned other writers are covered for the run's window
    only, as written. (3) **The tool's split is the kept split** (359 / 115 / 58 / 0): mechanical, reproducible, and
    larger on the residue side, so it claims less than the hand split; rows 3 and 15 now cite it. (4) **No S1a row
    counted the 5 rare items** as creations (the S1a review: rows 101 and 137 check only the 85 items with a list), so no
    row note is needed; the two sentences that called them cube outputs (save/0001, the S1a review entry in plan 0038's
    log) are corrected. (5) The optional items 6 and 13 stay open, out of this plan.
  - **Fixes (7, made in the docs):** items/0002 the dispatch is `mov eax, [eax*4+0x73c768]` then `call eax`, and
    Missiles now has a table doc (`tbl:` anchor); save/0001 the "rare cube outputs" sentence; rng/0002 rows 3 and 15
    carry the kept split; the qd 10/19 raise and the act `+0x50` `[C]` written into items/0010 and drlg/0009 (with the
    inventory § S2c note); the archivist entry's item (2) annotated as done by plan 0045 Phase 0; the spec-writer inputs
    entry annotated with the review's tags. Phase 2 gains that entry as its item 2 (its item 1 was done by `lane/p38s5`).
  - **Phase 1 done.** Phase 2 (spec-writer) can start.
- **2026-10-20 — Phase 2 landed (spec-writer, `lane/p49s`; review requested).** Item 2's entry folded and closed, with
  the review's tags; the orchestrator's extra item (the monsters/spawn object-marks row) done and closed; the
  combat/README A1 W1 (the finisher-peek comment) anchored.
  - **Specs** (front-matter tags before → after): monsters/special {107, 94, 4} → {107, 95, 3} (§ H rows 24 and 26:
    Normal-only groups, nothing outside Normal; the open question struck); drlg/lifecycle {85, 75, 8} → {86, 76, 8}
    (§ E act `+0x50` `[C]` for the run's window, the 31 pin sites; § H/§ I the wanderer's alignment 2, its open
    question narrowed; the `+0x50` meaning struck); items/quest-drops {84, 87, 2} → {86, 86, 2} (A3 and Duriel's bits
    `[C]` with the closure's limits beside them); quests/progression {114, 316, 6} → {114, 320, 6} (A7 and word 41 are
    object 1's second word, word 32's one write, `MissileCreateAt` W4c and missiles 288/332/625, the open question
    struck with a narrower `[L]` for the do-functions); player/creation {81, 45, 2} → {81, 48, 1} (A1 the mode word, E4
    the freed main list behind the ilvl-1 magic starting items, J3 the saved corpse; the open question struck);
    items/quality {64, 39, 2} → {64, 42, 2} (M3 `STATEVENT_Reanimate`, `FormationSpawn` case 5, `bonewallmaker`);
    rng/seeds {78, 9, 4} → {79, 10, 4} (step 5 note: the kept split 359/115/58/0, the 132/132 and 0/25 re-seed count);
    items/tc, monsters/spawn and combat/README wording only (counts unchanged).
  - **Nothing to change:** drlg/room-tiles already states the corrected release order (plan 0038 Phase 3 review); no
    spec carried the "rare cube outputs" wording (save/d2s I6's "cube outputs" is the bit-13 reading, not the 5 items).
  - **Plan 0038 note:** items/quest-drops, items/quality, items/tc, monsters/special, monsters/spawn and player/creation
    are 0038 Phase 3 re-tag specs; only the 0049 readings above were folded, and no 0038 inventory row was re-tagged.
    Its later rounds should see A3 and the Duriel bullet of items/quest-drops at `[C]` (the `lane/p49r` ruling), the
    new M3 notes of items/quality and the § H row-24/26 bullet of monsters/special.
  - **Gate:** green, 11 warnings (the 11 W1 of `docs/specs/data/excel.md`, held by plan 0038); the combat/README W1 is gone.
  - **Wiki:** characters (the ladder default, the saved corpse; the answered unknown removed), items (the `reanimate`
    owner and death-drop skip), monsters (the Normal-only group presets), quests (word 41's writer), saves (the saved corpse) changed;
    objects, randomness and items-other-paths checked and their `based_on` dates bumped.
