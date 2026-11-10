# Sounds (`data/global/excel/sounds.txt` → `sounds.bin`)

> **Source archive:** `.txt` patch_d2, `.bin` patch_d2   **Rows:** 4699 `.bin` records (= `.txt` data rows)   **Record:** 2 B
> **sha256:** `.txt` `6ab753bceb4a314d8e755eabcd4d3f084da76a5564f5ba6734dffd4cc9eedc58`, `.bin` `c1eec066a08f6b3c728c2e4decb1269d593ca13e4c9d24267a0186d4843b2bc7`
> **Doc status:** columns and `.bin` layout complete (plan 0068 Phase 1); sound is out of scope, listed for the references into it

## Purpose

The sound catalogue: 4 699 rows (index 0..4698), each a named sound with a file name and playback flags. The columns of other tables listed under References name a sound by `Sound` and store its row index. The table is sound data, out of scope for the rules; it is documented because many tables point into it. Leads: none.

## Row identity

- `[C]` Key column `Sound`: 4 699 rows, 4 699 distinct names, row 0 blank. The `Index` column equals the row index in every row (0..4698) (`python3 -I tools/excel_bin.py diff` over `sounds`, 4 699 of 4 699 cells).
- `[C]` No `Expansion` row; 4 699 `.txt` rows, 4 699 `.bin` records of 2 bytes.
- `[C]` The 2-byte `.bin` call at `0x00659C16` is `-txt`-only: the function at `0x00659BB0` skips it when `g_DataTblsCompileTxt` is 0 (`je` at `0x00659BC1`), and it is called only in the `-txt` runs ([data/0001 § Plan 0038 batch H3b](../findings/data/0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load), run:2026-10-27-sweep-data-load).
- `[I]` `sounds.txt` and `soundenviron.txt` are read as text by `sub_00481950_SoundTablesLoad`, which fills the client's sound records ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300), [archaeology/0003](../findings/archaeology/0003-sound-draws.md)). The same H3b entry's "the full `sounds` table loads in every run" is withdrawn: [data/0006 § 2.4](../findings/data/0006-loaded-tables-and-bundles.md#24-sounds) finds no call that loads `sounds.bin` in a stock run `[I]` (below).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Sound` | str, 4698 distinct, len <= 35, 1 blank | not compiled | sound name; the key other tables use (blank in row 0) | [Armor](Armor.md)/[Weapons](Weapons.md)/[Misc](Misc.md) `dropsound`, `usesound`; [Missiles](Missiles.md) `TravelSound`, `HitSound`, `ProgSound`; [Skills](Skills.md) `stsound`, `stsoundclass`, `dosound`, `dosound a`, `dosound b`, `tgtsound`, `prgsound`, `ItemCastSound`; [States](States.md) `onsound`; MonSounds | [C] |
| `Index` | int, 0..4698, 4699 distinct, 0 blank | +0x000 u16 | the row index, written in the file | — | [C] |
| `FileName` | str, 4434 distinct, len <= 57, 0 blank | not compiled | wave file name under the sound archives | — | [C] shape, [L] meaning |
| playback columns | int, -1..7000000, 127 distinct, 0 blank | not compiled | playback flags and parameters named for the audio engine `[L]`; none compiled | — | [C] shape, [L] meaning |

## Interpretation notes

- `[C]` Layout: one `u16`, the `Index` (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel sounds`). No other column is in the `.bin`.
- `[C]` References by name, set inclusion over every row (this phase): the columns in the `Sound` row above, plus `soundenviron:Song` holding values in 0..4684, inside the index range `[I]` (it holds numbers, not names).
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- Answered (plan 0068 Phase 2, from the finding): `[I]` the only call that loads `sounds.bin` is the `-txt`-only one at `0x00659C16` (the `sounds` string at `0x006ED50C` has the one reference `0x00659C11`); `[C]` in the four stock-mode H3b runs no file named `sounds.bin`, `sounds.txt` or `soundenviron.txt` is opened (`-ns` by default), under `-txt` `sounds.txt` and `sounds.bin` are. `[I]` A stock run with sound on reads `sounds.txt` as text by `sub_00481950_SoundTablesLoad` and never `sounds.bin`. Sound playback itself is out of scope. ([data/0006 § 2.4](../findings/data/0006-loaded-tables-and-bundles.md#24-sounds))

