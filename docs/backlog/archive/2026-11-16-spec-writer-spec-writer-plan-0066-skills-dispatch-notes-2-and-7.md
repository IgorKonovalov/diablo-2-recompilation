---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../specs/quirks/README.md
resolution: "Plan 0066 Phase 3, skills cluster (lane/n66sk): [skills/dispatch](../../specs/skills/dispatch.md) note 7 [C] (S2c) and note 2's unused-result half [C] on S5b's read, its floor half [I] (row 64's H2a route); Q262 and Q263 cite dispatch n2 and n7 again and the quirks Coverage table's weaker-duplicate column is empty for dispatch ([quirks](../../specs/quirks/README.md))."
---

Plan 0066 Phase 3, combat cluster (lane/n66y): combat/delivery's Reimplementation notes 13 (no caller tests SKILLS_PayCost's return) and 14 (the item effect flag is 1 only from handler 20 without ItemTgtDo) are now [C] on S5b's second-tool reads (run:2026-11-15-sweep2-s5b, combat/0001 § 18, delivery rows 65 and 66). skills/dispatch Reimplementation notes 2 and 7 state the same two claims at [I]: note 7 is raised by S2c (skills-dispatch row 194) and waits for the skills cluster's re-tag; note 2 (row 190) is routed to H2a there, though S5b's read of the three call sites settles its 'payment's result unused' half. Quirks Q262 and Q263 now take the combat notes alone, and skills/dispatch n2 and n7 sit in the quirks Coverage table's 'Weaker duplicate' column. At the skills cluster's Phase 3: raise n7 (and n2's unused-result half, its 'floor binds the payment' half by its own route), then cite them again from Q262 and Q263 and empty the column.
