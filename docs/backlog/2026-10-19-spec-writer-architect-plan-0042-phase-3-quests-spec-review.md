---
from: spec-writer
to: architect
date: 2026-10-19
status: open
context:
  - ../plans/0042-quests-travel.md
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Plan 0042 Phase 3 drafted on `lane/p42s` (spec-writer). **Per the plan, this review waits for Phase 2 part 3's review**
(`lane/p42r`); the statements part 3 targets are written `[I]` and get re-tagged from its reviewed raises first (the
inputs entry `2026-10-18-reverser-spec-writer-…-inputs-for.md` stays open for that).

**Files** (all `status: draft`):
- [quests/README](../specs/quests/README.md): C 9 / I 5 / L 2. Map, data flow, shared model, inputs and oracles,
  cross-references.
- [quests/progression](../specs/quests/progression.md): C 84 / I 327 / L 7. § A the record (bit grammar, loader rule,
  saved words, `ClearSteps`, packet 0x58, the game record); § B registry and dispatch; § C the join (deactivation pass,
  `rejoin`, the stub double join); § D shared script shapes; § E timers; § F NPC interaction; § G the draws; § H a section
  per quest: 41 word sections (Acts I–V, word 41, the four introduction objects), each with a bit table (setter
  site, trigger and condition, tag per row) and 35 state diagrams (none for words 29, 33 and the four word-42
  introduction objects, which write no record state); warp and portal gates; creation-path readers; three worked
  examples from the run logs (two NPC 331 talks with seeds, one NPC 266 talk, word 1's reward through the saved words).
- [quests/travel](../specs/quests/travel.md): C 55 / I 80 / L 4. § A placement (`ActLevelSpot`, `LevelPointFind`,
  `LevelPointPick`, `PlayerChangeLevel`/`Act`); § B `COLL_FindFreeNear`; § C waypoint activation (state diagram, the
  `Sync` 0 draw); § D waypoint travel; § E NPC act change (sequence diagram, packet 0x48); § F the Durance and other
  travel portals; § G town portals (open with its three draws as a sequence diagram, use, closing, class 60); § H warps
  and the walk command; § I resurrection and join; § J gates; draws per event kind; worked example: one portal open from
  session c-wp with every seed, and the level-seed chaining into the next open.

**Written `[I]` now, to re-tag from part 3** (ruling (c)): mode-0 waypoint activation, event 1 and the `Sync` 0 draw
(travel C1, C3, draws table); the stepping type-5 lookup (travel A3 note, E2, draws table); packet 0x48 and word 28's
branch (travel E3, E4); the quest timers (progression § E) and the unlogged quest-seed draws: eclipse (W11), cairn order
(W4), Anya (W37), Dark Wanderer (W32), Zoo (W40) and § G's rows; death and resurrection (travel § I1); level-entry and
item-use steps (the e3 and item-use rows of § H). Ruling (b)'s shortfalls are `[I]` for good.

**Points for the review.**
1. Tag scoping: `[C]` code blocks carry a "for …" scope on their tag line where part of the block is unreached (travel
   C1, E3, G2, G2a, H2; progression W12, W18, W29). Check that none overreaches.
2. **save/d2s E1 is now stale** against run:2026-10-18-quests2: it says the loader clears bits 13 and 14 only when bit 1
   is set, over 43 words; the run's `[C]` rule (progression A3) clears 13 and 14 on every word 0–41, sets 15 from bit 1,
   copies 42–47. I added only a link line under E1 (lane instruction: links only); the correction is a spec edit for a
   later pass or this review.
3. **quests/0002's summary** still lists "town portal creation: five" in its draws bullet (the § 6 bullet was corrected
   to three); the spec states three `[C]`. A finding fix for the reverser.
4. W4 (the cairn order) is written as the finding reads ("slots filled in draw order, classes 17–21 assigned in that
   order"); the other reading is an *Open question* `[L]`. Part 3 item 1 can settle it.
5. The eclipse period is written as 15 + `Range(2)` (15 or 16) from the finding's `RandLoHi = lo + R(hi − lo)`, although
   quests/0001's summary says "15–17".
6. Word 40 b10 at the join: observed in the save loads of run 1 but outside the checker's rules, kept `[I]`.

**Cross-links added** (one link each, no other edit): items/quest-drops (Purpose), objects (Open questions),
monsters/spawn (oracle row), monsters/special (oracle row), rng/seeds (Open questions), items/cube (Open questions),
drlg/collision (Open questions), save/d2s (§ E1 note), drlg/warps (§ G); glossary: game record, switched-off quest,
`Position` level, town portal pair.

**Research map** (`docs/specs/README.md`, architect's): rows `quests/progression` and `quests/travel` can read "draft ·
[quests/progression](../specs/quests/progression.md) / [quests/travel](../specs/quests/travel.md), overview [quests](../specs/quests/README.md);
review after Phase 2 part 3's review".

**Backlog:** the plan 0044 gates entry is closed (folded into travel § D, § G, § J); the rbs2 entry is annotated (its
quests items folded) and left open for the economy lane (`lane/p43s`) or whichever lane finishes last; the part 2 inputs
entry is annotated and left open for the re-tag.

Gate green at the lane's last commit.
