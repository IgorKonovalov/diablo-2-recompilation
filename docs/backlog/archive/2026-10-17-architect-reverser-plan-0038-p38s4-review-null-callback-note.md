---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "[I] line added to [data/0004 § Plan 0038 batch S1f](../../findings/data/0004-cell-converters.md#plan-0038-batch-s1f-2026-10-17) (0x006BDFFC–0x006BE001: an absent 0x17–0x19 entry with no link is skipped)."
---

[2026-10-17] from architect → reverser: plan 0038 Phase 3 round 4 review (`lane/p38s4`), ruling on S1f review addition (g). The NULL-callback skip of `EXCEL_ParseTxt` on a 0x17–0x19 descriptor entry (`mov ebx, [ecx+0x10]; test ebx, ebx; je 0x006BE022` at 0x006BDFFC–0x006BE001, re-read in objdump at this review) is stated only in the plan log and a backlog entry, so data/excel J3 cannot cite it yet. If J3 is to state it, add one `[I]` line to [data/0004 § Plan 0038 batch S1f](../../findings/data/0004-cell-converters.md#plan-0038-batch-s1f-2026-10-17) (a code reading the run did not reach, as the S1f review said) before the data/excel Phase 3 round (after H3b). Optional: J3 may also leave it out. Context: [plan 0038](../../plans/0038-inferred-claims-sweep.md#implementation-log)
