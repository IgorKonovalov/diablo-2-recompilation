---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../findings/data/0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../findings/data/0002-mpq-precedence.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../findings/data/0003-string-tables.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../findings/data/0004-cell-converters.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
resolution: ""
---

*(Released at the `lane/h3b` review, 2026-10-27, accept with fixes; see the plan 0038 log.)* Phase 3 of plan 0038 for the data cluster: re-tag the H3b rows
of data/README, data/excel and data/strings as the "Plan 0038 batch H3b" sections of data/0001–0004 and player/0001
rule (run:2026-10-27-sweep-data-load), and carry these corrections and review additions:
- data/README and data/excel *Entry points*: `TC_GetByName` has no reference (dead code); TC names are resolved by
  `EXCEL_FindName` on `g_TCLink` from `TC_ParseItemCell`, `TC_BuildChestTable` (called from `TC_LoadAll`; the 45
  chest names) and the `.txt` parser. Review ruling: the entry rows name these callers, and `TC_GetByName` stays
  only as a note (no caller, `[I]`).
- data/excel B1 step note on the 15 code-list tables: true of `DATATBLS_LoadTable` only (`hitclass.bin` is read whole at
  every start by the character-graphics loader, return 0x0050448A); add the 2-byte `sounds` call (0x00659C16, gated
  at 0x00659BC1) to the `-txt`-only calls.
- data/excel J4 *Record bytes no column fills*: add levels `+0x033..+0x035` (the leading non-negative `mon`/`nmon`/`umon`
  slot counts, at most 25 each; written at 0x0061DB05, 0x0061DB20, 0x0061DB40 in `DRLG_LoadLevels`).
- data/strings § H (and data/0003 § Language): a `use` byte of 0x0B ends the program at the `CYR` font map, before
  `string.tbl`.
- data/strings § H and data/excel § I (the language byte): the byte read is `[C]`, but the clamp of values above 13
  stays `[I]` (review ruling: only a made-up `use` byte reaches it, d-edit as a half). Rows 29 and 50 are raised in part.
- data/excel G1 (the TC load's post-pass `0x0065A2C0`, S1b row 42): its 45 chest-name lookups are logged by H3b and
  match (data/0001 § Q2 and the row 42 note), the store into `g_ChestTCs` stays `[I]`.

The data/README cluster is ready too (its rows are S1b and H3b only). The data/excel cluster also folds plan 0039's remainder (plan 0038 Phase 3 note, 2026-10-20).

