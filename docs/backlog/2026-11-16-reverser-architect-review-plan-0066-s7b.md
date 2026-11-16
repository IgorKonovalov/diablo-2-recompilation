---
from: reverser
to: architect
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md#implementation-log
  - ../plans/0066-inventory/README.md#4-batch-list
resolution: ""
---

Please review `lane/n66o`: plan 0066 Phase 1 batch **S7b** (sim/frame 41 rows, drlg/lifecycle 5). Static only: no game, no
Ghidra; new checks over the kept frame-window logs. Tier B (the plan's audit rule decides on a Tier A audit). S7f is not
started; the plan's log entry (2026-11-16, S7b) carries its resume note.

Worth checking:

1. `python3 -I tools/sweep2_s7b.py check` under a 4 GB scope gives `workspace/logs/n66o/s7b/check-s7b.txt` (`914b090d…`,
   `S7b total bad=0`) byte for byte (its `static` section needs r2 and objdump); `manifest.sha256` passes from
   `workspace/logs/n66o`; the two `frame_p55c_counts.py` reruns equal the kept review counts.
2. What separates each raise: the 262 `MSG0` against "inside the tick" and "the frame it acts before"; the room-list model
   (23 later walks, 7 first-walk prefixes, 70 unlinks, 4 rooms created inside a walk) against "append" and "visit the new
   room"; walks iff the flag (30); the every-frame queue's 3 716 next-frame runs against "the frame queued"; the AI's 447
   kind-0 draws against "only in the kind-2 record".
3. Judgment calls: (a) objdump and r2 readings (the message path's call sites, the two host loops' call order,
   `DUNGEON_RoomCreate`'s one call) taken as the second tool beside the logs for rows 1, 2, 16, 28, 59; (b) rows 96, 101, 102,
   109 raised in part on place and site recounts by this tool, the chained split left to the reader, and row 97 not raised:
   a byte-identical rerun of `frame_p55c_counts.py` is the same tool, not a second source; (c) rows 92 and 103 filed raised
   in part with a correction (an omitted drawer, a count's window scope), not contradicted; (d) D6 (row 33, H7b, outside the
   batch) noted contradicted in part, its class left; (e) rows 25, 26, 32, 67 left in a-logs, not moved (25 could go to b, 67
   to a rooms.gdb check); (f) the AI functions picked by the nearest preceding `re/symbols.csv` name (`Ai*`, `MonAi*`); (g)
   a "client act" read as an act no `NewRoomsUpdate` walk visits; (h) row 60 raised with one act in every window, the act
   order being H2's emulation; (i) row 120's "seen by tick N + 1" raised on the placement alone.
4. Spec corrections and the D6 contradiction in
   [`2026-11-16-reverser-spec-writer-plan-0066-s7b-corrections`](2026-11-16-reverser-spec-writer-plan-0066-s7b-corrections.md).
