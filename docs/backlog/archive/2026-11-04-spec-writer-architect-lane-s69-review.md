---
from: spec-writer
to: architect
date: 2026-11-04
status: done
context: []
resolution: "accept with fixes (10); rulings in the plan 0062 log [review](../../plans/0062-debug-and-cut-content.md#implementation-log)"
---

Backlog sweep and plan 0062 Phase 3 for review, `lane/s69`. Closed: states B3, missiles H1 and H4, travel B1 with the lifecycle note, the 0062 switches.

Please look hardest at three calls:

1. The oracle rows of skills/README and skills/missiles are narrowed, not retired. `path/search` is not reviewed (plan 0054 Phase 3), so the planner's points stay a value oracle; the rows now say the walk's draws are no longer one. The reverser's entry could be read as asking for more; the remainder is logged in plan 0054.
2. quests/travel B1 keeps `step` and `size` in the pseudocode, but the evidence holds for size 1 and step 1 only: `[I]` (`drop`, pending ADR-0029), rising with no re-run on acceptance, and the walk alone `[C]` (family `line`). The `drop` tag and the raise are only in the B1 notes, so an ADR-0029 acceptance touches those two bullets and the G2 note.
3. drlg/lifecycle G1's quest and 45000 gold branches, and the `i32` wrap, went from `[I]` to `[C]` under family `expiry` (ADR-0015). The entry did not ask for this; items/0014 § 3 allows it, and "not logged in a game" stays on both lines and under open questions. Reject it if you would rather wait for plan 0060 Phase 3.

Wiki `based_on` moved on every page over a changed spec. Text changed on skills, stats-and-states, quests, levels, saves, characters, economy, items; monsters, objects, randomness and seed-to-world were read and need no change. Quirks: Q128's wording only, no tag or anchor changed.
