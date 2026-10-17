---
from: reverser
to: architect
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.
review request, `lane/rbs2` (static backlog sweep, second pass, 2026-10-17; no game, no slot; Ghidra on `workspace/ghidra-rbs2`). Commits f1ffd11, f3b75cd, eb3359f + its revert e25627d (the `test_d2s.py` fix is lane/arc5's), 3d3186e and the checkpoint. Kept outputs: `workspace/logs/sweep-rbs2-manifest.txt` (four lines). Entries closed, with the tag of each answer:
- **H5e static reachability** (`[I]`, [drlg/0008 § H5e reachability, second pass](../findings/drlg/0008-outdoor.md#h5e-reachability-second-pass-2026-10-17-lanerbs2)): (e′) no writer of `O+0x00` in the callee closure (new `tools/callee_writes.py`: 46 functions, 12 indirect sites resolved by hand, 21 bare-register writes classified), Blood Moor `0x20` d-none; (c) at most 4 road endpoints on every stock level (nodes + 1 cave + ≤ 1 bridge; `sweep_h5e.py stampdefs` shows no stamp can add a cave), 5 and 6 d-none; (b) no static bound, scan condition printed (fewest free interior cells, minimum 12 of 64 over 52 200 windows). Please check the remainder of (e′): an out-of-range grid index is not excluded, only not computed.
- **plan 0042 P1 follow-ups**: (a) 31 W1 lines anchored (gate W1 53 → 22); (b) `[I]` `rejoin` = 1 at the two new-character builders, 0 at the two save readers; a stub character joins twice (first 1, then 0), a new reading for the spec-writer; (c) `[I]` the clear is the client's packet 0x48 (`0x0054C590` → `0x005350B0`); (d) optional, not taken.
- **game-type writer** (`[I]`, items/0011): GameCreate 0x00530CFF from the client's create message, built from `g_ClientGameMode` (0 → 3, 6 → 1, 8 → 2, else 0); the network names of 6 and 8 `[L]`.
- **MP25 aurafilter** (`[I]`, multiplayer/0001 § 4): `0x10000` same party, `0x8000` the pair's hostile bit, `0x2000` town rooms skipped; prediction written.
Annotated: plan 0044 P1 follow-ups ((2)–(4) done, (1) and (5) Phase 2); static-sweep-remaining (the list left). Left open: the `test_d2s.py` entry (lane/arc5). New symbols: 12 rows (`I`).
