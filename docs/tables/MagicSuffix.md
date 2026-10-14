# MagicSuffix (`data/global/excel/MagicSuffix.txt` → `magicsuffix.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 747 (748 data rows − 1 `Expansion` marker)   **Record:** 144 B
> **Doc status:** documented together with MagicPrefix: see [MagicPrefix.md](MagicPrefix.md)

`MagicSuffix` has the columns and the 144-byte record of `MagicPrefix`, except that its `.txt` has no
`etype4`/`etype5` columns (the `.bin` holds `0xFFFF` there). The schema, the `.bin` layout, the value ranges
of both tables side by side and the generation survey are all in [MagicPrefix.md](MagicPrefix.md).

Suffix-only facts, each detailed there:

- `[C]` Record 0 is a real row (`of Health`); the 6 blank records are 4, 9, 62, 69, 100, 103.
  (tbl:MagicSuffix.txt:Name)
- `[C]` `class`/`classlevelreq` are filled on 205 rows (all group 44, first property `charged`);
  `classspecific` is blank in every row. (tbl:MagicSuffix.txt:class)
- `[C]` 27 named rows name no `itype`; 16 rows have `level` 0; 9 rows have `levelreq` > `level`.
  (tbl:MagicSuffix.txt:itype1, tbl:MagicSuffix.txt:level)
