# RareSuffix (`data/global/excel/RareSuffix.txt` → `raresuffix.bin`)

> **Source archive:** mixed: `.txt` d2exp, `.bin` patch_d2   **Rows:** 155   **Record:** 72 B
> **Doc status:** documented together with RarePrefix: see [RarePrefix.md](RarePrefix.md)

`RareSuffix` has the columns and the 72-byte record of `RarePrefix`. The schema, the `.bin` layout, the value
ranges of both tables side by side and the comparison of the two forms are all in [RarePrefix.md](RarePrefix.md).

Suffix-only facts, each detailed there:

- `[C]` 155 distinct lower-case names, no blank row; every row names at least one `itype` and none an
  `etype`. (tbl:RareSuffix.txt:name, tbl:RareSuffix.txt:itype1)
- `[C]` Records 110..119 (`clasp` .. `cord`) are the `belt` words and the only rows with `add` = `multiply` =
  `divide` = 1, columns the record does not carry. (tbl:RareSuffix.txt:add)
- `[I]` `RareSuffix` comes first in the merged rare-name array, so record r has name id r + 1 (stored in `name2`); a
  `RarePrefix` record r has id 156 + r ([RarePrefix § Row identity](RarePrefix.md#row-identity),
  fn:sub_00633F40_LoadRareAffixes@0x00633F40).
