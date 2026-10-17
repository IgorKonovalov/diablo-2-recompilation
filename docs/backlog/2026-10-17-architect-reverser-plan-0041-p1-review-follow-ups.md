---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../tables/Sets.md#bonus-blocks-plan-0041-phase-0
  - ../findings/stats/0002-states.md#phase-0-surprise-f-the-56-rows-no-data-names
resolution: "(a) [I] in [stats/0001 § Phase 0 surprises](../findings/stats/0001-aggregate.md#phase-0-surprises): a Sets param name resolves by table order (skills, montype, states) via sub_006336A0_PropParamCell, not by the property; sent to the archivist ([entry](2026-10-17-reverser-archivist-sets-param-lookup-by-table-order.md)). (b) [I] in [stats/0002 § Surprise (f) setters scan](../findings/stats/0002-states.md#surprise-f-setters-scan-plan-0041-p1-review-follow-up-b-2026-10-17) (tools/state_setters.py): setters named for 27 of the 34 rows; 6, 25, 29, 39, 116, 164, 171 none found ([L]). (c) optional, not taken: moved to [entry](2026-10-17-reverser-reverser-plan-0041-op-6-7-emulation.md)."
---

[2026-10-17] from architect → reverser: plan 0041 P1 review follow-ups (static, not blocking; any static batch, before 0041·P3 if convenient). (a) Phase 0 surprise (e): read the Sets compiler's field descriptor for the bonus params and say whether a param name resolves by the property (`skill` vs `state`) or by a table order; the answer goes to the archivist for `excel_bin.py`'s Sets lookup ([Sets § Bonus blocks](../tables/Sets.md#bonus-blocks-plan-0041-phase-0)). (b) Phase 0 surprise (f): scan for the setters of the 34 States rows left in [stats/0002 § Phase 0 surprise (f)](../findings/stats/0002-states.md#phase-0-surprise-f-the-56-rows-no-data-names) (`push <id>` before `STATE_Set`, `STATE_ApplyTimed`, `UNIT_FindStatListByState`), naming the function per row; rows set by skill functions may be left to phase 3 with their caller named. (c) Optional: an ADR-0015 emulation of `STAT_ByTimeValue` (0x0065CA30) and `sub_00626200_StatEvaluate` cases 6/7 over a declared image, the only route to settle the contradicted op 6/7 lead past `[I]` (no stock path reaches it).
