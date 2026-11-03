---
from: spec-writer
to: reverser
date: 2026-11-03
status: open
context:
  - ../findings/ai/0012-batch11.md
  - ../findings/ai/0002-pool-a.md
  - ../findings/player/0002-party.md
resolution: ""
---

From plan 0058 Phase 2 (lane/s67), a disagreement between documents, not blocking. ai/0012 (0x005E8D61-0x005E8D72, and 0x005FC542-0x005FC552 for Baal) calls MonPlayerBonus's word b+0x0C 'the player count', and its Diablo table tests 'the player count < 2' on it. re/types/monstats.h and monsters/stats C1 give +0x0C as the difficulty and +0x10 as the players, and ai/0002 section 2.9 reads the same +0x0C as the difficulty in AiCorruptRogue (0x005F0B37). player/0002 section 7 lists the four think functions as re-reading a changed /players, and left what each does with it to ai/. Please read the two load sites and state which word they take; if it is the difficulty, ai/0012's table row and its model reading need a dated correction, and 'n < 2 and the player count < 2' becomes a difficulty test. docs/specs/player/party.md section E and its Open questions hold the question at [L].
