---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../specs/quirks/README.md#coverage
  - ../plans/done/0063-backlog-sweep-7.md#implementation-log
resolution: ""
---

`python3 -I tools/quirks.py check` reports 15 errors on main and on lane/n63w alike (found at the plan 0063 Phase 3 review, 2026-11-10); none comes from that lane. They are real drift, not tool faults. (1) Q2, 5 errors: drlg/collision's *Reimplementation notes* gained a ninth bullet ("The two copies mark a corpse differently", commit c22a55be, 2026-11-04), so NearWarpTest, SpawnPosOnTile and LogicBoxSingle are now n10, n11 and n12, while Q175, Q72 and Q271 still cite n9, n10 and n11. (2) Q3, 10 errors: the Coverage table has no row for eight specs whose notes were written or reviewed after plan 0057 P1 (items/inventory 8 notes, items/use 7, monsters/ai/README 4, monsters/ai/catalogue 3, monsters/ai/machinery 6, path/README 8, path/search 6, sim/frame 10), and its drlg/collision row says 11 notes for 12, with n12 neither cited nor skipped. Ask: re-point Q72, Q175 and Q271 to the current note numbers; harvest the new notes into quirks entries (new ids, ADR rules of plan 0057) or skip them by reason, and add the eight Coverage rows; bring `quirks.py check` to 0 errors. Suggestion for the architect afterwards: register `quirks.py check` in tools/gate.py so the drift cannot recur silently.
