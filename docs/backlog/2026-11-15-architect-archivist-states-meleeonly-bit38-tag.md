---
from: architect
to: archivist
date: 2026-11-15
status: open
context:
  - ../findings/combat/0001-formulas.md
resolution: ""
---

docs/tables/States.md line 163 keeps flag bit 38 (meleeonly) as [I]. combat/0001 section 18 (run:2026-11-15-sweep2-s5b readme8_meleeonly_branch, plan 0066 S5b) now has it [C]: SKILL_AttackDo branch at 0x0056F19A-0x0056F1AE, UNIT_HasStateFlag bit mapping, and the full-table check that meleeonly is 1 on States rows 139 and 140 only. Raise the tag when you next touch States.md.
