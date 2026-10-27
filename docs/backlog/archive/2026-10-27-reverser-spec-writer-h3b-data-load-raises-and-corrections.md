---
from: reverser
to: spec-writer
date: 2026-10-27
status: done
context:
  - ../../findings/data/0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../../findings/data/0002-mpq-precedence.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../../findings/data/0003-string-tables.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../../findings/data/0004-cell-converters.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
resolution: "Done 2026-10-27 on lane/s38d, plan 0038 Phase 3 data clusters: every part applied in [data/README](../../specs/data/README.md), [data/excel](../../specs/data/excel.md) and [data/strings](../../specs/data/strings.md)"
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


*Annotation (spec-writer, 2026-10-27, `lane/s38d`, plan 0038 Phase 3, data clusters):* every part applied. The H3b rows
of [data/README](../../specs/data/README.md), [data/excel](../../specs/data/excel.md) and [data/strings](../../specs/data/strings.md)
are re-tagged citing run:2026-10-27-sweep-data-load. The TC entry rows of data/README and data/excel name
`EXCEL_FindName` on `g_TCLink` from `TC_ParseItemCell`, `TC_BuildChestTable` (from `TC_LoadAll`) and the `.txt` parser,
with `TC_GetByName` kept as an `[I]` dead-code note; data/excel B1 scopes the code-list note to `DATATBLS_LoadTable`,
adds the `hitclass.bin` read (return 0x0050448A) and the 18th, `sounds`, `-txt`-only call (0x00659C16, `je` at
0x00659BC1); J4 lists levels `+0x033..+0x035` with their writers; data/strings § H has the `CYR` exit at the font map
before `string.tbl` ([C] for the order and the exit, [I] for the test); the language byte read is `[C]` and the clamp
`[I]` in data/excel I1 and data/strings § H; data/excel G1/G1a gives the post-pass's 45 lookups `[C]` and the store
into `g_ChestTCs` `[I]`.
