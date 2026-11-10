# MonSounds (`data/global/excel/monsounds.txt` → `monsounds.bin`)

> **Source archive:** `.txt` patch_d2, `.bin` patch_d2   **Rows:** 141 `.bin` records (= `.txt` data rows)   **Record:** 148 B
> **sha256:** `.txt` `d0da7ef1c3b34d575c27f4a56a3755fd2a4038afce632257220625644e858880`, `.bin` `86b603e84427a180b6d0894e2fc6e1c0b29a3cff3d0f211c8deed00c06c49b56`
> **Doc status:** columns and `.bin` layout complete (plan 0068 Phase 1); sound is out of scope unless a column changes a rule, readers are Phase 2

## Purpose

One row per monster sound set: attack, weapon, hit and death sounds with their delays and probabilities, four skill sounds, footstep columns, neutral/init/taunt/flee sounds and three "convert" triples (a mode, a skill and a target mode). [MonStats](MonStats.md) `MonSound` and `UMonSound` and [SuperUniques](SuperUniques.md) `MonSound` name a row by `Id`. Every sound column names a row of [Sounds](Sounds.md). The table is sound data: it is in scope only if a column changes a rule (research map, out-of-scope list). Loader call site `0x00656F45`, record 148, not `-txt`-only ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)). Leads: none.

## Row identity

- `[C]` Key column `Id`: 141 rows, all distinct, row 0 blank (140 names). Other tables name a row by `Id` and their `.bin` stores the row index (MonStats `MonSound`, `UMonSound` use 136 and 137 distinct names; SuperUniques `MonSound` 3): set inclusion over every row, this phase.
- `[C]` No `Expansion` row; 141 `.txt` rows, 141 `.bin` records.

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Id` | str, 140 distinct, len <= 15, 1 blank | +0x000 u32 row index into `monsounds:Id` | row key | read by MonStats `MonSound`, `UMonSound`; SuperUniques `MonSound` | [C] |
| sound columns | str, 443 distinct, len <= 28, 1471 blank | +0x004 .. +0x078, 16 fields (u32 row index into `sounds:Sound`) | a sound played on the named occasion `[L]`; a blank cell stores 0 (the `sounds` row 0, `none.wav`); the `.bin` slot is 4 bytes, the high half is 0 | `sounds:Sound` | [C] layout and reference, [L] meaning |
| delays | int, 0..12, 12 distinct, 339 blank | +0x008, +0x014, +0x020, +0x02C, +0x038, +0x040 (s32) | delay before the matching sound `[L]` (units not known from data; frames or ticks is a Phase 2 question) | — | [C] layout, [L] meaning |
| probabilities and volumes | int, 60..255, 14 distinct, 285 blank | +0x00C, +0x018, +0x024, +0x030 (s32) | probability / volume of the attack and weapon sounds `[L]` | — | [C] layout, [L] meaning |
| footstep counters | int, 0..100, 9 distinct, 153 blank | +0x05C, +0x060, +0x064 (s32) | footstep count, offset and probability `[L]` | — | [C] layout, [L] meaning |
| `NeuTime` | int, 90..1800, 6 distinct, 79 blank | +0x06C s32 | by name the period of the neutral sound `[L]` | — | [C] layout, [L] meaning |
| convert modes | str, 7 distinct, len <= 2, 820 blank | +0x07C, +0x07D, +0x084, +0x085, +0x08C, +0x08D (u8 row index into `monmode:code`) | a monster mode and a target mode of a convert rule `[L]`; blank stores 0xFF (−1) in one byte | [MonMode](MonMode.md) `code` | [C] layout and reference, [L] meaning |
| convert skills | str, 6 distinct, len <= 10, 412 blank | +0x080, +0x088, +0x090 (s32 row index into `skills:skill`) | a skill of a convert rule `[L]`; blank stores −1 in 4 bytes | [Skills](Skills.md) `skill` | [C] layout and reference, [L] meaning |
| `EOL` | int, 0..0, 1 distinct, 0 blank | not compiled | end-of-line marker column; not compiled | — | [C] |

## Interpretation notes

- `[C]` Layout: the record is 37 four-byte slots; the `.txt` order is not the record order (each `Attack` slot is followed by its delay and probability, each `Weapon` slot by its delay and volume), and each convert triple is two `u8` (`CvtMo`, `CvtTgt`), two pad bytes (0 in every record) and an `s32` skill index (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel monsounds`, 5 640 of 5 640 cells; the three pads are the only bytes with no column).
- `[C]` Every sound reference resolves to a `sounds.txt` row (a cell that did not resolve would store −1 and fail the diff); `Sounds` is therefore read by this table, see [Sounds](Sounds.md).
- `[I]` Readers (plan 0068 Phase 2, [data/0006 § 3](../findings/data/0006-loaded-tables-and-bundles.md#3-composit-overlay-skilldesc-arena-plan-item-3-with-monsounds-and-automap)): the table is read through two getters (`0x00656F90`, `0x00656FC0`) called only from the client (`0x004CA410`, `0x004F4F40`); the server reads none: presentation.
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- `[L]` The units of the delays and probabilities and what a convert triple selects: sound, out of scope; no server-side reader (above).
