---
from: architect
to: spec-writer
date: 2026-11-03
status: done
context:
  - ../../specs/quirks/README.md
  - ../../specs/skills/catalogue.md#reimplementation-notes
  - ../../plans/done/0057-quirks-catalogue.md#implementation-log
resolution: "Done (lane/s64): skills/catalogue's 8 notes harvested, 7 taken (Q436–Q444 new, Q136 and Q50 also cite n1 and n8), n5 skipped as not a trap; coverage row, Total (447 / 418) and skipped counts updated; quirks.py check 0 errors. [quirks](../../specs/quirks/README.md#coverage)"
---

tools/quirks.py check fails on main with one error (Q3: skills/catalogue.md has 8 Reimplementation notes but no coverage row in quirks/README). skills/catalogue (plan 0046 Phase 3, commit 2b68bf75) gained its Reimplementation notes after the Phase 1 harvest (4063e701), so the index never took or skipped them; the tool counts 447 notes while the coverage Total row says 439. Add the skills/catalogue coverage row, take each of its 8 notes into an entry (owning spec's tag, no second version of a statement another spec holds) or skip it with a reason, and update the Total row, the skipped counts and the research-map quirks row. Found at the lane/s63 Tier A review (2026-11-03).
