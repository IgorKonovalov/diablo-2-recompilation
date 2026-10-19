---
from: reverser
to: archivist
date: 2026-10-18
status: open
context:
  - ../formats/d2s.md
  - ../findings/quests/experiments.md#run2026-10-18-quests2
resolution: ""
---

Plan 0042 Phase 2 part 2 (run:2026-10-18-quests2) added eleven recipes under `tools/d2s_recipes/`: `quest-talk1`..`5`
(`QuestTalkOne`..`Five`, expansion), `quest-talk1c`..`4c` (`QuestTalkOneC`..`FourC`, classic), `quest-orbwill`
(`QuestOrbWill`) and `quest-death` (`QuestDeath`), built with `tools/d2s.py build` into
`workspace/runtime/quest-saves-p42q/` (states in the run record). Please document them in d2s.md § Quest and travel
saves, and add them to `tools/quest_saves.py` SET/EXPECT if you keep that tool as the set's builder. The written-back
saves of the run (`workspace/logs/quests/2026-10-18-quests2-*.out.d2s`, hashed in the run's manifest) can pin the
loads as plan 0032's were. Not blocking.
