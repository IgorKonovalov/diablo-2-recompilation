---
from: reverser
to: spec-writer
date: 2026-10-16
status: done
context:
  - ../../specs/data/excel.md#i-string-table-keys
  - ../../specs/rng/README.md#entry-points
  - ../../specs/data/strings.md#worked-example
resolution: "Done 2026-10-27: (a), (c), (d) on lane/s38d ([data/excel](../../specs/data/excel.md), [data/strings](../../specs/data/strings.md)); (b) and the calc/rng half of (d) on lane/p38s4"
---

[2026-10-16] from reverser → spec-writer: plan 0038 S1b, for Phase 3 (after the S1b review): (a) [data/excel § I](../../specs/data/excel.md#i-string-table-keys): the `Lilith` exception is answered (data/0004 S1b section); (b) [rng § Entry points](../../specs/rng/README.md#entry-points): 14 LCG sites lie in 9 functions with no static reference, `RangePow2Plus` among them (rng/0001 S1b section); (c) [data/strings worked example](../../specs/data/strings.md#worked-example) and reimplementation notes: `not used` is not a duplicate key; (d) restate the d-none and d-edit parts the ledgers name (TC growth, the 0xFFFE fatal, inner quotes, byte/dword lookups, archive ties).

*Annotation (archive copy, migrated 2026-10-17):* **Partly done 2026-10-17 (spec-writer, `lane/p38s4`, Phase 3 round 4):** (b) in [rng § Entry points](../../specs/rng/README.md#entry-points) step note 4 (the 9 unreferenced bodies, `RangePow2Plus` among them, `[I]`); (d) for data/calc and rng (the d-none meta row dropped; hover and the used item kept `[I]` with their reasons). **Open:** (a), (c) and (d) for data/excel and data/strings, which wait for H3b.

*Annotation (spec-writer, 2026-10-27, `lane/s38d`, plan 0038 Phase 3, data clusters):* the open parts are applied.
(a) [data/excel](../../specs/data/excel.md) I2: the pinned compiler stores 11154 in the `Lilith` cell (`[C]`), the shipped
file's 5382 an inference about how it was made (`[I]`); open question struck, data/strings § F updated. (c)
[data/strings](../../specs/data/strings.md) *Reimplementation notes*: `not used` is held once, no duplicate case. (d) the
d-none and d-edit parts are restated `[I]` beside each raise in data/excel and data/strings (TC growth, the `0xFFFE`
fatal, inner quotes, byte/dword lookups, the d2kfixup/d2delta places, the stock-data "never fires"); the archive tie
rule is now live and `[C]` (A2 note, H3b).
