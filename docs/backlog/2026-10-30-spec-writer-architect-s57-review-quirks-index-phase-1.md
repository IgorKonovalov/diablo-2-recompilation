---
from: spec-writer
to: architect
date: 2026-10-30
status: open
context:
  - ../plans/0057-quirks-catalogue.md#implementation-log
  - ../specs/quirks/README.md
resolution: ""
---

Review request: lane/s57, plan 0057 Phase 1 (Tier A, with Phase 3 per the plan; Phase 1 can be reviewed alone). docs/specs/quirks/README.md: 435 entries in nine classes (C 334 / I 101 / L 0), each restating one tagged statement of a reviewed spec with its tag and anchors and a link to the owning section; coverage table over all 47 specs with a Reimplementation notes section (439 notes: 410 taken, 29 skipped by reason). New tool tools/quirks.py (harvest, check: tag in each tagged source, every anchor in one of them, coverage n1..nN). For the reviewer: (1) the class boundaries, notably the wide data-dependent class (save/load round-trip rules sit there) and bounds holding the comparison off-by-ones; (2) the two skip reasons added to the plan's three: wall-clock (owner question 2) and weaker duplicate (anim/README n2, routed); (3) untagged notes taken through the section that holds their tagged form, and the 12 table-rule skips of data/excel and data/calc; (4) entries merged across specs only where they state one site (two combat seeds, discarded draws, the finisher, stat 328, ItemEffect, store seed, cr_lancer8, language 13); per-site Range(1) draws stay one entry each; (5) the machine-readable form (plan open question). Plan log entry dated 2026-10-30; ledger row added (tokens and wall unknown, 0).
