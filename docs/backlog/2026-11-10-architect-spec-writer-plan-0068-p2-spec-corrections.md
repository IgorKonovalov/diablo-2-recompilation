---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../findings/data/0006-loaded-tables-and-bundles.md
  - ../plans/0068-game-files-coverage.md
resolution: ""
---

**Spec corrections from plan 0068 Phase 2 (carry in Phase 4).** (1) docs/specs/data/excel.md B1 (the 18th -txt-only call) says 'the full `sounds` table loads in every run'. data/0006 § 2.4 withdraws that clause: no stock run reads any `sounds` file (`-ns`), and the text read of 0x00481950 happens only with sound on. data/0001 carries a dated correction. (2) The skill-level bonus formula of data/0006 § 3.2 (`sub_00644180_SkillLevelBonus`: stats 127, 83, 188 with param 8*class + SkillPage - 1 only for a non-zero SkillPage, 97 capped at 3 on own-class skills, 126, 107, state 134) is a rule no spec states; skills/dispatch or data/calc must carry it at [I]. (3) The rest of the plan 0068 log's Phase 4 list (MonItemPercent no-reader sentence, Events dispatch ids, loader list).
