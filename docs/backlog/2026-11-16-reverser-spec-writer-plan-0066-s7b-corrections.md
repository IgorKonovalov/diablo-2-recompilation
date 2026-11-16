---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/frame/0007-frame-batch.md#plan-0066-batch-s7b-new-checks-over-the-kept-windows-2026-11-16-lanen66o
  - ../findings/drlg/0009-room-lifecycle.md#14-plan-0066-batch-s7b-the-frame-windows-room-and-timer-lines-2026-11-16-lanen66o
resolution: ""
---

Plan 0066 batch S7b (`lane/n66o`) contradicted one sim/frame statement in part and corrected three; each needs the spec
text changed after the review. Not blocking. Lines are `main` `b5999f5e`'s; match by text.

1. **Contradicted in part: sim/frame D6, line 281** ("Ranks 5, 6 and 10 to 13 hold no event in any counted window"; inventory
   row 33, class a-run, H7b, not this batch's). Town #2 of run:2026-11-04-frame, a counted window (§ K1), holds 86 players'
   every-frame `UE0` (rank 6, the walk), each before that frame's players' slot walk (86 pairs 6 → 7, 0 inversions;
   `check-s7b.txt` `ranks`). The statement needs "in any counted window with `XS`", or rank 6 dropped from it with the
   town window named; D1's rank 6 is then placed by one window.
2. **Correction: sim/frame J2, line 721**, kind (1) "the game seed: every unit creation …": `RoomPopulate`'s own loop steps
   the game seed (it loads `[game+0xD0]` at 0x0054ED90; 6 929 `XS` at 0x0054ED96 inside the windows' walks, each on the game
   seed's low word), a drawer the sentence does not name; [chain § D5](../specs/chain/README.md) has it.
3. **Correction (scope): sim/frame § K4's owner row, line 834.** "4 hits" (`MonCritDouble` 0x005A55BA with a missile event
   open) and "22 times" (`COMBAT_ToHitRoll` 0x0057DB38) are counts over the nine windows with `XS` (the seven counted, 5505 #1
   and 5509 #1); over the seven counted windows the column header names they are 3 and 19 (2 more in monsters' own events in
   both). The *Counted windows* cell, 3, is right.
4. **Wording: sim/frame A1, line 104**, "the open-server thread: the same three calls": it calls
   `ServerGamesFlush(0, 0)` only after a tick (0x0044CF6D–0x0044CF77) and then `Sleep(30)` (0x0044CF89–0x0044CF8B), unlike
   mode 0's `(1, 0)` after a tick and mode 1's `(0, 0)` always.

Phase 3 notes (no correction): D3 (line 266) has no instance in the windows (0 of 3 716 every-frame queues ran in their
frame), but E5a's 658 monster starts of run:2026-10-27-anim are D3's case for the monsters' every-frame list and may be
cited there.
