---
from: reverser
to: archivist
date: 2026-10-19
status: open
context:
  - ../formats/d2s.md
  - ../findings/quests/experiments.md#run2026-10-19-quests3
resolution: ""
---

Plan 0042 Phase 2 part 3 (run:2026-10-19-quests3) added four recipes under `tools/d2s_recipes/`: `quest-p3entry`
(`QuestEntry`: Act I start, every quest done but words 4, 11, 12 and 37, all waypoints, a tome and the decoded scroll
`bkd `), `quest-p3anya` (`QuestAnya`: Act V start, word 37 = b1, b8, b15, a tome and `tr2 `), `quest-p3meshif`
(`QuestMeshifW`: Act III start, every quest done) and `quest-p3wpact` (`QuestWpAct`: Act I start, the towns'
waypoints only, a tome), built with `tools/d2s.py build` on `workspace/samples/d2s-owner/smpsor-l50.d2s` into
`workspace/runtime/quest-saves-p42r/`. Please document them in d2s.md § Quest and travel saves beside part 2's (the
2026-10-18 entry). The written-back saves (`workspace/logs/quests/2026-10-19-quests3-*.out.d2s`, hashed in the run's
manifest) can pin the loads. Not blocking.
