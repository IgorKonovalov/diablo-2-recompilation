# HireDesc (`data/global/excel/hiredesc.txt` → `hiredesc.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 9   **Record:** 4 B
> **sha256:** `.txt` `f987819ccb450b4a5938ee67fe6ceee9509589039cd0cafeb86d464cde1072c6`, `.bin` `d05efadf2986625dc10c8ebd05bf083505ab37e2efb293f937a3af345649e4ed`
> **Doc status:** layout complete (plan 0033 Phase 0); use by Hireling from [hirelings/0001](../findings/hirelings/0001-hirelings.md); the text source `[L]`

## Purpose

A code list of hireling descriptions: `None` (blank code), `farw` Fire Arrow, `carw` Cold Arrow, `comb` Combat,
`def` Defensive Auras, `off` Offensive Auras, `fire` Fire Spells, `cold` Cold Spells, `ltng` Lightning Spells.
[Hireling](Hireling.md) `HireDesc` (`+0x0D2`, u8) holds a row index into it; the `.txt` holds the row's `Code`, and
`-txt` compilation turns the code into that index `[C]` (the loader's descriptor declares `+0x0D2` a u8 `hiredesc`
row, and the 120 Hireling records decode to it, [hirelings/0001 § 1](../findings/hirelings/0001-hirelings.md#1-the-table-and-its-lookups)). Reader: `hirelings` (plan 0033), the
hire list's description line.

## Row identity

- `[C]` The `.bin` is a u32 record count (9) and nine 4-byte records, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). Row 0 (`None`) has a blank code, so a blank Hireling `HireDesc` cell
  stores 0 (the first-match rule of [excel-bin.md § Cell encoding rules](../formats/excel-bin.md#cell-encoding-rules)).
- `[I]` **A stock run never loads `hiredesc.bin`.** It is one of the code lists that `DATATBLS_LoadCodeLists` loads
  only under `-txt`, to resolve Hireling `HireDesc` cells while compiling
  ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300),
  `0x00612AE8`). At run time the description is the index stored in the Hireling record.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel hiredesc`: 9 records × 1 mapped
field = 9 cells, **0 mismatches**.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Hireling Description` | str, 9 distinct | — (not compiled) | editor name of the description | — | [C] |
| `Code` | str, 8 distinct and one blank (row 0) | `+0x0` char[4] code, space-padded (row 0: four spaces) | the description code | referenced by [Hireling](Hireling.md) `HireDesc` | [C] |

## Interpretation notes

- **Use by Hireling** (`[C]`, `python3 -I tools/hireling_survey.py rows …`): `farw` and `carw` on the Rogue Ids (Fire,
  Ice), `comb`, `def`, `off` on the Act II Ids, `fire`, `cold`, `ltng` on the Act III Ids, blank (row 0) on every
  Barbarian row. Every row is used.
- `[I]` `HIRELING_RollEntry` copies the Hireling record's index byte into the hire-list entry; no code path read
  turns it into text ([hirelings/0001 § 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats), fn:HIRELING_RollEntry@0x006637F0). How the client shows the
  description (a string key per row?) is `[L]`; this record holds only the code.

## Open questions

- `[L]` The hire list's description text: where it comes from at run time, given that this table is not loaded in a
  stock run. Not read by plan 0033 Phase 1 (its Phase 2 boundary leaves the display out).
