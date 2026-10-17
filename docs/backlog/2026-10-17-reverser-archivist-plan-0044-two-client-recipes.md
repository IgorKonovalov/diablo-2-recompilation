---
from: reverser
to: archivist
date: 2026-10-17
status: open
context:
  - ../plans/0044-multiplayer-branches.md#implementation-log
  - ../findings/multiplayer/0001-cases.md#2-the-case-list
resolution: ""
---

Plan 0044 Phase 2 needs tool-built character pairs (host and joiner, distinct names, ADR-0008 inputs) for the cases of [multiplayer/0001 § 2](../findings/multiplayer/0001-cases.md#2-the-case-list): (a) a Nova pair, both at character level 9 or more (hostility needs it: MP23, MP24), the joiner weak enough to die on purpose (MP01, MP14); (b) an MF host (`uniqnova`, 472) with a no-MF joiner (MP19); (c) a host with a mercenary (`mercnova`) (MP04); (d) quest-word pairs from the plan 0032/0042 recipe pattern: forge (word 27 bits 0 and 1 clear on both; counter case bit 0 set on the joiner, MP12), Andariel with opposite word-6 states (MP13, MP14), Den of Evil open (MP28), word 21 bit 0 clear and set on the joiner with the Durance waypoint on the host (MP27), the Ancients at the summit with the joiner's word 39 bit 0 clear and base level 20 or more, plus one below it (MP17), a joiner holding `bks` (MP30), different finished quests on host and joiner (MP29); (e) a Paladin joiner with an aura (MP25); (f) a `cubeportal`-type pair for the cow portal in town (MP24). Build with `d2s.py`, list the hashes as Phase 0 of plan 0042 did.
