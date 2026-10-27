---
from: archivist
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0050-animation-frame-timing.md#implementation-log
  - ../formats/animdata.md
  - ../tables/MonSeq.md
  - ../tables/HitClass.md
resolution: ""
---

Please review plan 0050 Phase 0 on `lane/p50z`: [formats/animdata](../formats/animdata.md) with `tools/animdata.py` (gate survey `animdata`) and the COF comparison in [cof](../formats/cof.md#animdatad2-against-the-cof-fields-data-only); the new [MonSeq](../tables/MonSeq.md) and [HitClass](../tables/HitClass.md) docs with their `monseq` and `hitclass` layouts (`excel_layout` baseline regenerated, 71 tables, 0 unexplained); the § Timing sections of PlrMode, MonMode, ObjMode, CharStats, MonStats, MonStats2, Weapons, Skills, States, ItemStatCost and Objects; and `tools/anim_survey.py` (gate survey `anim`) with the token-to-record joins and their misses. Meanings stay `[L]` unless a finding or a reviewed spec anchors them. Five surprises for Phase 1.1 are listed in the [plan log](../plans/0050-animation-frame-timing.md#implementation-log) rather than written into its *Done when* (the lane was told to keep its plan edits to a log entry); please fold them in if you agree. No archivist entry from lane/p50a was open at the start. Not blocking.
