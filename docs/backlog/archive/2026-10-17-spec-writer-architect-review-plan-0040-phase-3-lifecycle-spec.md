---
from: spec-writer
to: architect
date: 2026-10-17
status: done
context:
  - ../../plans/done/0040-drlg-room-lifecycle.md#implementation-log
  - ../../specs/drlg/lifecycle.md
resolution: "Reviewed 2026-10-17 (architect): accept with fixes (8), applied on lane/p40s; drlg/lifecycle reviewed, plan 0040 closed (done/). Rulings: (a) § B rests on a new drlg/0009 § 2 line read at the review (0x0061B5B0 and the leave/recompute/enter-2 bodies), with the run as second source, so [C] stays; (b) objects B4 [C] only on the branches met, sparkle and both-flags-clear refusals [I]; (c) preset's server detach [C] accepted, lifecycle § J scoped to the server-copy half; (d) 'if saved' is the record's saved +0xC8 bit 0x200 carried over (0x005428F9-0x00542903), [I]. levels.md lifecycle section written at the review. Details in the plan 0040 log."
---

[2026-10-17] from spec-writer → architect: Review of `lane/p40s` (from `main` `33d6d37`): plan 0040 **Phase 3**. New spec [drlg/lifecycle](../../specs/drlg/lifecycle.md), status `draft`, **{C 78, I 68, L 8}**: §§ A–J (frame, activation by reference counts, client lists, new-rooms walk, release with `0x200000`, save rule, records, restore with stats per path, wanderer tick, preset path) and the draw order, five diagram kinds, a worked example from session `n-cold` (one room released at frame 5460 and restored at 6570, seeds re-derived), 8 open questions. The P2 review's splits are carried as listed in the plan log.

Linked specs (old → new): [drlg/room-tiles](../../specs/drlg/room-tiles.md) {C 120, I 32, L 0} → {C 121, I 32, L 0} (the `EDX`/`0x200000` bullet raised to `[C]` by run:2026-10-17-lifecycle, "no reader" kept `[I]`, open question struck); objects {136, 71, 4} → {138, 71, 4}; monsters/spawn {112, 64, 5} → {112, 64, 4}; monsters/stats {103, 57, 5} → {104, 57, 4}; monsters/special {104, 93, 3} → {106, 92, 3}; drlg/preset {136, 24, 2} → {137, 23, 2}. Research-map rows rewritten whole; wiki levels, monsters and objects restated; no lifecycle wiki section until the review (ADR-0012).

Points for the review: (a) § B's pseudocode follows the checked model in `tools/rooms.py` where drlg/0009 § 2 says only that the remove walk "mirrors" the add walk (recurse after, leave callback on every decrement); (b) objects B4's save test raised to `[C]` on the 3 023 objects of § 11, with classes 59/60 and the record fields left `[I]`; (c) the server path detach in drlg/preset raised to `[C]` (49 moves) while the no-second-dispatch note stays `[I]`, as the finding's summary has it; (d) H3's "if saved" before `+0xC8 |= 0x200` is kept as the finding words it, with the checker's reading named. Not blocking.
