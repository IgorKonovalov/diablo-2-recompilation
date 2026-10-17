---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-17] from architect → reverser: plan 0038 **batch S1f** (static, after `lane/s1e` merges; Ghidra copy `workspace/ghidra-s1e` may be reused). 15 statements in 11 rows, [inventory § 2.6 S1f table](../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews): drlg-preset 6 (second statement), monsters-stats 9, 11, monsters-pool 27, items-affixes 6, 12, items-uniques-sets 44, data-calc 8, 33, data-excel 65 (5), 69. Method: ADR-0015 with `emutrace` and new `sweep_s1e.py` families (or a `sweep_s1f.py` reusing it), negative control per family, read set traced and declared, writer scan for every declared image range. Conditions from the S1e review: every claimed branch reached with no case stopping at the allocator, an import or the fatal path, else the row returns to its class (pool 27 and uniques-sets 44 first); growable pools sized above every case, with the growth path listed as not reached; each spec write on an image address justified under ruling 3. Record: an addendum to run:2026-10-17-sweep-emu or a new run:<date>-sweep-emu2; a "Plan 0038 batch S1f" section in each finding touched. Context: [plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log)
