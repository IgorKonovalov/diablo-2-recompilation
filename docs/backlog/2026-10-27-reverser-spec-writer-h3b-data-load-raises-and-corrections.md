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

*(Held until the architect's review of `lane/h3b`.)* Phase 3 of plan 0038 for the data cluster: re-tag the H3b rows
of data/README, data/excel and data/strings as the "Plan 0038 batch H3b" sections of data/0001–0004 and player/0001
rule (run:2026-10-27-sweep-data-load), and carry four corrections:
- data/README and data/excel *Entry points*: `TC_GetByName` has no reference (dead code); TC names are resolved by
  `EXCEL_FindName` on `g_TCLink` from `TC_ParseItemCell`, `TC_LoadAll` and the `.txt` parser.
- data/excel B1 step note on the 15 code-list tables: true of `DATATBLS_LoadTable` only (`hitclass.bin` is read whole at
  every start by the character-graphics loader); add the 2-byte `sounds` call to the `-txt`-only calls.
- data/excel J4 *Record bytes no column fills*: add levels `+0x033..+0x035` (the leading non-negative `mon`/`nmon`/`umon`
  slot counts).
- data/strings § H (and data/0003 § Language): a `use` byte of 0x0B ends the program at the `CYR` font map, before
  `string.tbl`.
The data/excel cluster also folds plan 0039's remainder (plan 0038 Phase 3 note, 2026-10-20).

