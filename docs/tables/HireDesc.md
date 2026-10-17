# HireDesc (`data/global/excel/hiredesc.txt` → `hiredesc.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 9   **Record:** 4 B
> **sha256:** `.txt` `f987819ccb450b4a5938ee67fe6ceee9509589039cd0cafeb86d464cde1072c6`, `.bin` `d05efadf2986625dc10c8ebd05bf083505ab37e2efb293f937a3af345649e4ed`
> **Doc status:** layout complete (plan 0033 Phase 0); use by Hireling from [hirelings/0001](../findings/hirelings/0001-hirelings.md); the text source from its § Plan 0039 batch P1c

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
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` the game loads this table as one of
  the 15 code lists of `DATATBLS_LoadCodeLists` and writes a `hiredesc.bin` byte-identical to the shipped one, which
  ships in d2exp ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3). That a stock run never loads it stays `[I]`: the file ships, so its absence could not show it (data/0001 §
  S1b row 30). (fn:DATATBLS_LoadCodeLists@0x00612750)

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
  turns it into text ([hirelings/0001 § 4](../findings/hirelings/0001-hirelings.md#4-an-entry-type-level-price-and-the-displayed-stats), fn:HIRELING_RollEntry@0x006637F0).
- `[I]` **The text comes from a hard-coded table, indexed by the row.** The client hire list passes the entry's
  index to `HIRELING_DescString` (`0x00663720`), which returns the string of `g_HireDescStrIdx[index]` (u16 at
  `0x006EE410`) for an index 0..8 with a non-zero word, else nothing; `hiredesc.txt`/`.bin` are not used for it.
  `[C]` (data) The nine words are 0, 3371, 3372, 11090, 11088, 11089, 3377, 3376, 3375, which read in the English
  tables as none, "Fire Arrow", "Cold Arrow", "Combat", "Defensive", "Offensive", "Fire", "Cold", "Lightning": rows
  `None`, `farw`, `carw`, `comb`, `def`, `off`, `fire`, `cold`, `ltng` in order, so a Barbarian (row 0) gets no
  description. ([hirelings/0001 § Plan 0039 batch P1c](../findings/hirelings/0001-hirelings.md#plan-0039-batch-p1c-2026-10-17),
  fn:HIRELING_DescString@0x00663720, data:g_HireDescStrIdx@0x006EE410, tbl:HireDesc.txt:Code)

## Open questions

- ~~The hire list's description text: where it comes from at run time~~: answered `[I]` (§ Interpretation notes,
  plan 0039 P1c).
