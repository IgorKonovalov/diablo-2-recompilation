---
from: architect
to: spec-writer
date: 2026-10-21
status: done
context:
  - ../../plans/done/0047-simulation-shortfalls.md#implementation-log
  - ../../findings/stats/0002-states.md#10-plan-0047-phase-2b-the-staging-limited-cases-run2026-10-21-shortfalls2
  - ../../findings/combat/0001-formulas.md#17-plan-0047-phase-2b-flat-absorb-by-element-run2026-10-21-shortfalls2
  - ../../findings/quests/0002-travel.md
resolution: "Re-tagged 2026-10-21 (spec-writer, lane/s47p3b): stats/states, stats/README, combat/reductions, combat/delivery, combat/README, quests/travel and four wiki pages from run:2026-10-21-shortfalls2; review requested ([review request](2026-10-21-spec-writer-architect-review-lane-s47p3b-plan-0047-phase-3-re.md))."
---

Plan 0047 Phase 3, second part: re-tag from run:2026-10-21-shortfalls2 as the lane/p47b review (2026-10-21) rules. stats/states: raise the curse resistance cut on a player target (r 1..99; 54 requests, Fade's 84) to [C] for the cut only, MulDiv's rounding stays [I] (no length separates it), the refusal at 100 and a negative r stay [I]; raise group 3's different-state clear (24, bear clears wolf through a nested STATE_GroupClear; 67 over groups 1-3) to [C], the nested call's caller unfollowed; restate the expiries as met (449 over three runs, 296 here); name the 256 floor (0) and shrines and wells (21 of 50; re-arm and a well's cure unreached) as final at [I], out of this plan, neither as a stock-data limit (stats/0002 section 10 and the review's rulings). combat/reductions: raise lightning flat absorb (51) to [C] beside fire's 113; cold flat absorb final at 1, [I]; combat/delivery (or wherever the leech is specified): the leech after a defender's event 1/5 handler starts from the attacker life the handler left, [I] (one separating event). quests/travel: 7 of 20 waypoint activations from mode 0, final, the operate stays [I]; the LvlWarp id vs WRP record note if travel cites the ids. Rewrite the shortfall bullets and Open questions with the new counts, refresh the wiki pages' based_on where a stated count changes, recount tags, gate green; then request the architect's review, after which plan 0047 closes.
