---
from: spec-writer
to: architect
date: 2026-10-21
status: open
context:
  - ../plans/0047-simulation-shortfalls.md#implementation-log
  - archive/2026-10-21-architect-spec-writer-plan-0047-phase-3-re-tag-the-phase.md
resolution: ""
---

Review lane/s47p3b: plan 0047 Phase 3, second part, the re-tag from run:2026-10-21-shortfalls2 as the lane/p47b review rules (stats/0002 § 10, combat/0001 § 17, quests/0002). After this review plan 0047 can close. Not blocking.

Raised to [C] with run:2026-10-21-shortfalls2 cited (each split from its remainder):
- stats/states: B1 the curse resistance cut on a player target, 1 <= r <= 99 (54 requests under Fade's 84: 52 defense_curse 275 -> 44, two shrine curses 3 600 -> 576, 2 400 -> 384), in the pseudocode and a step note; MulDiv's rounding, the refusal at r >= 100 and a negative r in a separate [I] note. D1 group 3 (24 bear-clears-wolf, each holding the nested call at depth 2; 67 over groups 1-3); the nested call's caller in a separate [I] note. C1 the 300 expiries (449 over three runs, 296 here); the old shortfall note split into the [C] count and an [I] note keeping the client-copy sentence.
- combat/reductions: B3 lightning flat absorb 51 (13 + 25 + 13) beside fire's 113, in the pseudocode comment and the note.
- stats/README, combat/README: one [C] boundary paragraph each for the run (14 sessions; 2 527 events of 3 logs, the checker's attacker life after a defender handler stated as a value oracle).

Stay [I], final for plan 0047 (the review's rulings): the 256 floor (states E2, delivery E4: 0 in 1 431 poisoned ticks; the staged route's items, the higher-life route untried, no stock-data limit); shrines and wells (states § G intro: 21 of 50, a slot-time ruling, one session's yield, palc-wells2 not run); cold flat absorb (reductions B3: 1, the Done-when's condition, the Nightmare and Hell cold rows untried); the leech after a defender's event 1/5 handler (new delivery C1 [I] note: one separating event, 25 life); the waypoint activation from mode 0 (travel C1 note rewritten: 7 of 20, three Passage and three Highlands here, a tool reason with the fixes tried).

Also: a stale clause fixed in states G6 (the stamina shrine, code 14, was operated twice in run:2026-10-20-shortfalls, so only the combat shrine, the re-arm and a well's cure are unreached); the H table's expire and shrine rows and the entry-point table's group and shrine rows take the new counts (16 shrine operates). quests/travel cites no Act V LvlWarp ids (its H2 "rows 20 and 21, 64, 76" are already the record numbering), so no id/record note is needed; its Evidence lists the two shortfalls runs' travel sessions.

Open questions: states struck the Phase 2b bullet (expiries, group 3, curse cut reached) and rewrote the remainder as one [L] "final for plan 0047" bullet; reductions struck cold/lightning and added an [L] for cold; delivery adds an [L] for the leech's one separating event and rewrites the floor clause; combat/README's named-again bullet and stats/README's bullet rewritten whole.

Tags (before -> after, the gate's own counter): stats/states {C47 I52 L6} -> {C51 I53 L6}; stats/README {C15 I3 L3} -> {C16 I3 L3}; combat/reductions {C45 I25 L5} -> {C46 I25 L5}; combat/delivery {C80 I63 L3} -> {C80 I64 L4}; combat/README {C38 I42 L5} -> {C39 I42 L5}; quests/travel {C74 I86 L4} unchanged.

Wiki: stats-and-states.md, combat.md, quests.md (based_on already 2026-10-21, the specs' updated date), how-we-know.md (the further pass and the final shortfalls). Please update the research map rows for stats/states, combat and quests/travel.
