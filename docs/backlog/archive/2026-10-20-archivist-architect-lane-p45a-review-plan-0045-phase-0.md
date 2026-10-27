---
from: archivist
to: architect
date: 2026-10-20
status: done
context:
  - 2026-10-20-archivist-reverser-missiles-fields-named-by-the-table-doc.md
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (3: miscount 2, other 1). Surveys rerun green, baselines match; tier-A ruling written into plan 0045 Phase 1; notes for P1.1 in 2026-10-20-architect-reverser-plan-0045-p0-review-notes-for-p1-1.md."
---

Review `lane/p45a` (from main c4b4539): [plan 0045](../../plans/done/0045-skills-missiles-machinery.md) Phase 0, "Missiles and
the dispatch columns". Blocking plan 0045 Phase 1's tier-A list (fixed at its review from this survey), not P1.1's
start.

- **New** [Missiles](../../tables/Missiles.md): full layout (146 fields, 420 B; diff 99 864 cells, 0 mismatches),
  every column with offset, width and observed values in the plan's groups; server function numbers per number;
  survey facts; the readers the findings and data/calc already name.
- **New** [PetType](../../tables/PetType.md): layout (224 B, 400 cells, 0 mismatches), the rows with the Skills rows
  that name them.
- [Skills § Dispatch](../../tables/Skills.md#dispatch-plan-0045-phase-0): the named columns, rows per `srvstfunc` /
  `srvdofunc` / `srvprgfunc` number, family sizes, 26 tier-A candidates; line 6 rewritten.
- `tools/skills_survey.py` (gate survey `skills`, new baseline); `tools/excel_layouts.py` (missiles complete,
  pettype new); **`excel_layout` baseline changed** by rerunning `excel_bin.py survey` (`tables` 67 → 68, `records`
  11 437 → 11 457, `cells` 850 613 → 946 089, `missiles_cells` 4 788 → 99 864, `pettype_cells=400`); `calc.md` one
  sentence; tables README rows.

Points to check: the tier-A proposal (Druid 221 Raven, 225 Firestorm; Assassin 251 Fire Trauma = *Fire Blast*, 259
Fists of Fire for the progressive path; the four family rows 56 Meteor, 66 Amplify Damage, 98 Might, 25 Plague
Javelin are targeted or aura skills, so the pilot's reach is yours to rule); the `[I]` meanings taken from combat/0001,
drlg/0005, drlg/0008 and quests/0001 and the `[C]` ones from data/calc § G/G2; the three surprises added to Phase 1's
*Done when* (rule 9). Gate: fast tier green; `--full=excel_layout,skills,calc_bytes,calc,combat,stats,economy` green.
