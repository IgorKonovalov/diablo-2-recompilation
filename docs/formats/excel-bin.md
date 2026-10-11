# Excel tables: `.txt` source and compiled `.bin`

Owned by `archivist`. **Stub** opened in Plan 0001 Phase 3. Per-table record layouts come later,
one table at a time, alongside its `docs/tables/<Table>.md`. Files live in
`data/global/excel/` of `workspace/merged/` ([mpq.md](mpq.md)). The inventory with counts is in
[tables/README.md](../tables/README.md). Survey tool: `tools/excel_survey.py`.

## `.txt` (tab-separated source)

- `[C]` Tab-separated, one header row of column names, CRLF line endings on every line (also the
  last), no BOM. Checked over all 92 `.txt` files.
- `[C]` Encoding is a single-byte Windows code page. Only two non-ASCII bytes occur in the whole
  set: `0x85` (×2, `objects.txt`) and `0x92` (×1, `uniqueitems.txt`). In CP1252 they are `…` and
  `’`, which fit their context. Read as bytes or latin-1, and split rows on `\n` **only**:
  Python's `str.splitlines()` also breaks on `\x85` and miscounts `objects.txt`.
- `[C]` 30 tables contain an **`Expansion` marker row**: first field `Expansion`, the rest usually
  empty but sometimes with a stray value (`Expansion\t\t0` in `ObjType`, `Expansion\tExpansion…`
  in `misc`). In all 30, the compiled `.bin` has no record for it (next section).
- `[C]` A **tab-only line is a record**. `uniqueitems.txt` ends with a line of 69 tabs and nothing
  else, and `uniqueitems.bin` has a matching empty-name record at index 401 (its last). Decoding the
  name field of every record and diffing against the `.txt` `index` column gives exactly that one
  insertion. So a row counter must skip only zero-length lines. For UniqueItems this means the
  game's record count (402) includes one blank row.
- `[C]` Blank cells do **not** compile to zero. Record 401 above has 54 non-zero bytes:
  `0x20202020` at +0x28 (four spaces, i.e. an empty 4-char item code) and runs of `0xFF` from +0x38
  on. `[L]` The `0xFF` runs are −1 "none" defaults for empty index columns (property and
  similar). Decoders must not treat zero as "empty".
- `[C]` Row identity is not always "row index". `objects.txt` has rows with duplicate `Id` (408 and 409
  appear twice, once on each side of the marker) and no row for Ids 411–412. Its 573 non-marker
  rows still equal the `.bin` count. How the game resolves those Ids is open.

## `.bin` (compiled form)

| offset | size | type | name | meaning | tag |
|---|---|---|---|---|---|
| `0x00` | 4 | u32 LE | `count` | number of records | `[C]` |
| `0x04` | `count × recsize` | bytes | records | fixed-size records, layout per table | `[C]` (fixed size) / unknown (fields) |

- `[C]` For all 88 `.bin` files with this header (87 with a `.txt` twin, plus `leveldefs.bin`),
  `(size − 4)` is an exact multiple of `count`, and `count` equals the twin's `.txt` data rows
  (57 tables), or those rows minus the `Expansion` markers (30 tables). Data-behaviour
  corroboration over every file; no code anchor yet.
- `[C]` Record sizes range from 2 bytes (`sounds`, `monai`, `uniqueprefix`…) to 1928 bytes
  (`LvlTypes`). Several 2- and 4-byte tables are single-column code lists (`bodylocs`, `colors`,
  `ElemTypes`…), so a record there is probably a code or a string-table index `[L]`.
- `[C]` `leveldefs.bin` has no `.txt`. It holds 137 records of 156 bytes, the same count as
  `levels.bin`. `[L]` It is the compiled half of `Levels.txt` that 1.10+ split out.
- `[C]` Four `.bin` files do **not** use this header: `itemscode.bin` (158 B), `misscode.bin` (196 B),
  `skillscode.bin` (5891 B), `skilldesccode.bin` (4252 B). Their leading u32 is nonsensical as a
  count. `[L]` They look like the bytecode for formula columns (calc expressions in
  `itemstatcost`/`missiles`/`skills`/`skilldesc`): short byte runs with recurring opcodes `0x04`, `0x07`
  followed by u16 operands. `compcode.bin` *does* have the count header (115 × 4 B).

## Open questions

- `[L]` Does the game load `.bin` and ignore `.txt` unless a command-line switch is set? `Game.exe` holds
  `%s\%s.bin` (`0x006E681C`), `DATA\GLOBAL\EXCEL` (`0x006D8ED4`), `.txt` (`0x006D48E0`) and
  `.\Src\Excel\Excel.cpp` (`0x006FC448`). → reverser (backlog).
- `[L]` Per-table record layouts: field offsets and how `.txt` columns map to them. Each one is
  done with its table doc, corroborated by decoding the `.bin` and matching every `.txt` cell.
- `[L]` Bytecode format of the `*code.bin` files and which columns reference offsets into them.
