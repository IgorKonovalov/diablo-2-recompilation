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
  `classspecific` is blank in every row, so the pick's class test never refuses a suffix on stock data (the test
  itself: [MagicPrefix § Code semantics](MagicPrefix.md#code-semantics-items0005), `[C]` for prefixes by
  run:2026-10-14-affixes). (tbl:MagicSuffix.txt:class)
- `[C]` 27 named rows name no `itype`; 16 rows have `level` 0; 9 rows have `levelreq` > `level`.
  (tbl:MagicSuffix.txt:itype1, tbl:MagicSuffix.txt:level)
- `[I]` `MagicSuffix` comes first in the merged affix array, so record r has affix id r + 1 and record 0 (`of Health`)
  is id 1; the 27 rows with no `itype` are never picked ([MagicPrefix § Row identity](MagicPrefix.md#row-identity),
  [§ Code semantics](MagicPrefix.md#code-semantics-items0005), fn:sub_00633730_LoadMagicAffixes@0x00633730).
- `[C]` **Price** (plan 0043 Phase 0): `divide`, `multiply` and `add` (`+0x084`, `+0x088`, `+0x08C`) are 0 in every
  suffix row; only 21 prefixes (the all-resistance rows) carry a price term
  ([MagicPrefix § Price](MagicPrefix.md#price-plan-0043-phase-0), `economy_survey.py affixes`). `[I]` `divide` is
  never read by the price path; `multiply`/`add` are read as for the prefixes ([items/0011 § 3](../findings/items/0011-economy.md#3-the-value-terms)).
