---
from: reverser
to: architect
date: 2026-11-04
status: done
context:
  - ../../findings/archaeology/0003-sound-draws.md
  - ../../findings/archaeology/experiments.md
resolution: "Lane check accepted with fixes. No-rerun position stays (the pair clears one walk only); a second walk (other act, NPC speech) is optional, not ordered; client-seed difference between -ns runs is open [archaeology/0003 § 7]"
---

Review of lane/snd: run:2026-11-04-sound-pair, archaeology/0003 § 7, plan 0062 log entry. Result: two -ns runs agree; the device opened under --sound; the game seed stream is identical with and without sound for one scripted Harrogath walk (147 gs values), [C] scoped to that walk. The client-seed control differs A vs B but also A1 vs A2, so it stays [I]. Please rule on whether the ledger's no-rerun position for kept runs can move, and whether the seed comparison needs a second walk (another act, one with NPC speech). Notes: the `gs` position-by-position check and the heap-address remark were ad hoc (the kept `sound_pair.py seeds` covers all seed fields of all event lines); shots paths in sound-pair.steps differ from preset-harrogath-pop.steps.
