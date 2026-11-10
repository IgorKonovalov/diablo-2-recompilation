---
from: architect
to: spec-writer
date: 2026-11-10
status: done
context:
  - ../../findings/data/0006-loaded-tables-and-bundles.md
  - ../../plans/0068-game-files-coverage.md
resolution: "Plan 0068 Phase 4 (lane/n68w): (1) data/excel B1's 'the full sounds table loads in every run' withdrawn, with a new B1 note (no sounds.bin outside -txt [I], no sounds file in the -ns stock runs [C]) [../../specs/data/excel.md#b-loading-one-table]; (2) the skill-level bonus is skills/dispatch C8 at [I], its return in play [C] [../../specs/skills/dispatch.md#c-the-request-checks-skills_canuse]; (3) MonItemPercent in items/tc's reimplementation notes and Inputs [../../specs/items/tc.md#reimplementation-notes], the event ids, 4 and 8 never dispatched, id 13 and the registration bounds in skills/dispatch § K and stats/aggregate G3, the loader readers table in data/excel B1."
---

**Spec corrections from plan 0068 Phase 2 (carry in Phase 4).** (1) docs/specs/data/excel.md B1 (the 18th -txt-only call) says 'the full `sounds` table loads in every run'. data/0006 § 2.4 withdraws that clause: no stock run reads any `sounds` file (`-ns`), and the text read of 0x00481950 happens only with sound on. data/0001 carries a dated correction. (2) The skill-level bonus formula of data/0006 § 3.2 (`sub_00644180_SkillLevelBonus`: stats 127, 83, 188 with param 8*class + SkillPage - 1 only for a non-zero SkillPage, 97 capped at 3 on own-class skills, 126, 107, state 134) is a rule no spec states; skills/dispatch or data/calc must carry it at [I]. (3) The rest of the plan 0068 log's Phase 4 list (MonItemPercent no-reader sentence, Events dispatch ids, loader list).
