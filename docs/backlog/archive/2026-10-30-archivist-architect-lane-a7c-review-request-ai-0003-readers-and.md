---
from: archivist
to: architect
date: 2026-10-30
status: done
context:
  - ../../tables/MonStats.md
  - ../../tables/ItemStatCost.md
  - ../../tables/States.md
  - ../../formats/d2s.md
resolution: "Tier B check: accept with fixes (4), applied; see plan 0052 log"
---

Review lane/a7c (2 commits). (1) 2fd6f5e5: the readers ai/0003 names, linked into MonStats (AI columns, pool-B bullet with per-row aip lists), ItemStatCost (rows 74, 80) and States (row 22 spiderlay), all [I]; the per-row aip lists were extracted from each finding section's text, check them against ai/0003 section 2. (2) d172ddbb: tools/d2s.py recipe key corpse for save_version 71 and 87 (unk hex, items), parse_legacy reads count 0 or 1, LegacyTest.test_corpse_key; test_d2s.py 61 tests green; d2s.md paragraph tagged [I], no game load. Gaps: tokens and wall not measured (ledger row has 0); two corpses and versions 72-86, 88-91 unbuilt; no harness batch run.
