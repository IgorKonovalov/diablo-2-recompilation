# Overlay (`data/global/excel/overlay.txt` → `overlay.bin`)

> **Source archive:** `.txt` patch_d2, `.bin` patch_d2   **Rows:** 293 `.bin` records (= `.txt` data rows)   **Record:** 132 B
> **sha256:** `.txt` `a37e80510e8921d4b06c9e0559a56096586d86ba295345f6bd55b4c2254b036f`, `.bin` `7cd975a3bcb5b89a0e8b96b1d003fa679c0f682cb81abb128cf025b5ff028e9c`
> **Doc status:** columns and `.bin` layout complete (plan 0068 Phase 1); presentation: the server reads only the row count (data/0006 § 3.1, below)

## Purpose

293 spell and state visual effects ("overlays"): a name, a DCC/DC6 file name, frame count, animation rate, offsets, light radius, colour and a few flags. [States](States.md) (`overlay1..4`, `castoverlay`, `removerlay`, `pgsvoverlay`), [Skills](Skills.md) (`srvoverlay`, `sumoverlay`, `tgtoverlay`, `prgoverlay`, `castoverlay`, `cltoverlaya`, `cltoverlayb`, `ItemCastOverlay`) and [Missiles](Missiles.md) `ProgOverlay` name a row and store the row index. Mostly presentation (ADR-0005); whether any frame count or rate feeds a rule (for example a state's timing) is Phase 2 item 3. Loader call site `0x00664514`, record 132, not `-txt`-only ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)). Leads: none.

## Row identity

- `[C]` Key column `overlay`: 293 rows, 293 distinct, none blank; row 0 is `null`. Rows are addressed by **row index**; States/Skills/Missiles store it.
- `[C]` One `Expansion` marker row: 294 `.txt` rows, 293 `.bin` records.

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `overlay` | str, 293 distinct, len <= 30, 0 blank | +0x000 u16 row index into `overlay:overlay` | effect name, the key | read by States, Skills, Missiles overlay columns (above) | [C] |
| `Filename` | str, 255 distinct, len <= 31, 0 blank | +0x002 char[64] | art file name (stem), stored in a 64-byte char array at +0x02 | — | [C] layout, [L] meaning |
| `version` | int, 0..100, 2 distinct, 0 blank | +0x042 u16 | by name a format version of the art `[L]` | — | [C] layout, [L] meaning |
| `Frames` | int, 1..40, 27 distinct, 0 blank | +0x044 u32 | by name the frame count `[L]` | — | [C] layout, [L] meaning |
| `Character` | str, 15 distinct, len <= 9, 0 blank | not compiled | text naming a class or kind (`all`, `Monster`, class names, `?`); not compiled | — | [C] shape, [L] meaning |
| `PreDraw` | int, 0..1, 2 distinct, 0 blank | +0x048 u32 | by name draw before the unit `[L]` | — | [C] layout, [L] meaning |
| `1ofN` | int, 1..3, 3 distinct, 0 blank | +0x04C u32 | by name a "one of N" variant count `[L]` | — | [C] layout, [L] meaning |
| `Dir` | int, 0..0, 1 distinct, 0 blank | +0x050 u8 | by name a direction flag; 0 in every row `[L]` | — | [C] layout (one distinct value), [L] meaning |
| `Open`, `Beta` | int, 0..1, 2 distinct, 0 blank | +0x051, +0x052 (u8) | flags, one byte each `[L]` | — | [C] layout, [L] meaning |
| offsets and heights | int, -120..14, 20 distinct, 0 blank | +0x054, +0x058, +0x05C, +0x060, +0x064, +0x068 (s32) | screen offsets and heights of the art `[L]` | — | [C] layout, [L] meaning |
| `AnimRate` | int, 0..32, 15 distinct, 0 blank | +0x06C s32 | by name the animation rate `[L]`; units not known from data | — | [C] layout, [L] meaning |
| light | int, 0..255, 25 distinct, 0 blank | +0x070, +0x074, +0x07D, +0x07E, +0x07F (s32; u8) | light radii and colour `[L]` | — | [C] layout, [L] meaning |
| `LoopWaitTime` | int, 0..7000, 3 distinct, 0 blank | +0x078 s32 | by name the wait between loops `[L]` | — | [C] layout, [L] meaning |
| `Trans` | int, 0..8, 4 distinct, 0 blank | +0x07C u8 | by name a transparency mode `[L]` | — | [C] layout, [L] meaning |
| `NumDirections`, `LocalBlood` | int, 0..4, 3 distinct, 0 blank | +0x080, +0x081 (u8) | direction count; local-blood flag `[L]` | — | [C] layout, [L] meaning |

## Interpretation notes

- `[C]` Layout: `overlay` as the row's own index (`u16`), `Filename` as a char array at +0x02, then `version` (`u16`), `Frames`, `PreDraw`, `1ofN` as `u32`, small flag bytes, offsets, heights, rate, radii and wait as `s32`, `Trans`/`Red`/`Green`/`Blue`/`NumDirections`/`LocalBlood` as `u8` (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel overlay`, 7 325 of 7 325 cells). Two ranges are in no column: +0x053 (1 byte) and +0x082..+0x083 (2 bytes), 0 in every record (`excel_bin.py unknown`). The `Filename` array is wider than its longest value (31 characters); the 64-byte width is where `version` begins (+0x42), `[I]`.
- `[I]` Readers (plan 0068 Phase 2, [data/0006 § 3.1](../findings/data/0006-loaded-tables-and-bundles.md#31-overlays-count-on-the-server)): record columns are read by client drawing code only. The server reads the record count (`+0xBC0`) at 18 sites from `0x0056F23A` to `0x005DA7A5` and in `sub_00621E40_UnitSetOverlayStat` (the three examined bound an overlay id, `id < 0` or `id >= count` skips, before setting it on a unit or sending it), so no Overlay column (frames, timing) reaches a server rule; a reimplementation needs only the row count as that bound.
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- None for the rule-bearing columns; the rest is presentation (client only).
