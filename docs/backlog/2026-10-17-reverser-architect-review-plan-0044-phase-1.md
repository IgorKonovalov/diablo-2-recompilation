---
from: reverser
to: architect
date: 2026-10-17
status: done
context:
  - ../plans/0044-multiplayer-branches.md#implementation-log
  - ../findings/multiplayer/0001-cases.md
resolution: "Reviewed 2026-10-17: accept with fixes (4: omission, wrong anchor, overclaim, other). Rulings (a)-(g) in the plan 0044 log; the driver's live test is Phase 2's first step; the port-4000 precondition reworded to the owner's condition only."
---

Review plan 0044 Phase 1 (`lane/p44r` from `main` `1083b92`, static, not merged). [multiplayer/0001](../findings/multiplayer/0001-cases.md): 32 two-client cases (29 stageable, 3 not: more than two players, the clamp at 8, a roomless member); every d-2c row (14, kept count), the four partial halves, the eight Context questions, plans 0040–0043 and the contradicted hostility lead mapped to cases. New `[I]` readings to spot-check: both travel gates read the operator's own PlayerData `+0x160` (EDX = 0 at 0x0054C5F5 and 0x005848BA), which contradicts lane/p42r's 'own portal never delayed'; the hostility toggle `0x005A5E50` (town only, level 9 or more on both, a 60 s pair stamp); the portal's hostility test `0x00535B10`; the host binds `INADDR_ANY` IPv4 at both `bind` sites. Driver: `d2pilot.py join` (follow, party invite/accept/leave/hostile, leave, trade) from the host's new PLRS lines, 16 game-free tests. Points for the ruling: (a) one cross-cutting finding instead of sections in each owning finding, and its research-map placement; (b) the port-4000 precondition of § 5 (confirm by root listing or a non-loopback probe, add a ufw deny only if both fail), which needs the owner (human backlog); (c) the **open checkpoint**: the driver's live test on a non-zero slot is pending a free slot, so Phase 1's *Done when* is met except for that item; (d) cases without a prediction (MP25, MP31–MP32) count as staged observations.
