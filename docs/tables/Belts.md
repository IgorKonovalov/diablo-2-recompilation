# Belts (`data/global/excel/belts.txt` → `belts.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 14 (15 data rows − 1 `Expansion` marker)   **Record:** 264 B (`0x108`)
> **sha256:** `.txt` `55d680040663a8e6930863fc7687fe041b72c04cb98f97737794cc5bc0b41fb5`, `.bin` `cf8296500985694bc0327b5249a47bbe14558b65f956bd7a36b115f1a670e473`
> **Doc status:** layout complete (plan 0060 Phase 0, `python3 -I tools/excel_bin.py diff`: 14 records × 65 fields = 910 cells, 0 mismatches; in the gate's `excel_layout` survey); readers `[I]` from player/0001, the rest left to plan 0060 Phase 1.2

## Purpose

One row per belt size: how many potion boxes a belt has and where each box sits on the screen. Row 2 is the
default belt, the one a character has with no belt item worn. The server's use is the box count and the box order
(the belt placement search); the rectangles are screen pixels, which the client reads (ADR-0025: the UI is out of
scope). Research-map row: `items/use` (plan 0060).

## Row identity

- `[C]` The `.bin` is a u32 count (14) and 14 records of 264 bytes ([excel-bin.md](../formats/excel-bin.md)); the
  `Expansion` marker row takes no record. The loader allocates 264-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x00660C22`).
- `[C]` Rows 0..6 are `belt`, `sash`, `default`, `girdle`, `light belt`, `heavy belt`, `uber belt` (before the
  marker); rows 7..13 are `belt2`, `sash2`, `default2`, `girdle2`, `light belt2`, `heavy belt2`, `uber belt` (after it).
  `name` is not compiled: the record holds 0 at `+0x000` in all 14, so a row is told apart by its position.
- `[C]` (data) Each pair `n` and `n + 7` has the same `numboxes` (12, 8, 4, 16, 8, 12, 16) and the same box
  geometry shifted by a constant (box 1 `left` 343 against 423, `top` 442 against 562): the second set is the same
  belts on the other screen layout. `[L]` Which set the game reads on which screen mode, and whether the server
  reads the second set at all: no reader found (Phase 1.2).
- `[I]` **The armor `belt` column indexes this table.** `Armor.belt` (`+0x130`, 0..6) is 0 on `mbl` (Belt),
  1 on `lbl` (Sash), 3 on `hbl` (Girdle), 4 on `vbl` (Light Belt), 5 on `tbl` (Heavy Belt) and 6 on the ten
  elite and exceptional belts. Read as a row number in the first set it gives the right box count for each name
  (`belt` 12, `sash` 8, `girdle` 16, `light belt` 8, `heavy belt` 12, `uber belt` 16) and leaves row 2 (`default`, 4
  boxes) for no belt. This is a data match; no function reading `+0x130` as a `belts` row has been named
  ([Armor](Armor.md), tbl:Armor.txt:belt).

## Columns

`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel belts` (layout `LAYOUTS["belts"]` in
`tools/excel_layouts.py`) decodes all 14 records; the 65 mapped fields compare equal to the `.txt` in every cell.
The probe pins each offset (the four-byte slots fit any integer width from the offset, so the u32 widths are the
slot sizes, `[I]` by stride).

| Column | Observed type / range | `.bin` field | Meaning | Tag |
|---|---|---|---|---|
| `name` | str, 13 distinct (`uber belt` twice) | — (not compiled; `+0x000` is 0 in all 14) | editor name | [C] (no field) |
| `numboxes` | int {4, 8, 12, 16} | `+0x004` u32 | the number of potion boxes of the belt | [C] offset; meaning `[I]` below |
| `boxwidth` | int, always 29 | — (not compiled) | box width in pixels; each box's right − left is 29 in every used box | [C] (no field) |
| `boxheight` | int, always 29 | — (not compiled) | as above for the height | [C] (no field) |
| `box<n>left`, `box<n>right`, `box<n>top`, `box<n>bottom` (n = 1..16) | int, 0 for n > `numboxes` | `+0x008 + 16·(n−1)` + 0, 4, 8, 12, each u32 | the screen rectangle of box n | [C] offset |

### Box order (data)

`[C]` (data, all 14 rows): box n sits in column `(n − 1) mod 4` and row `(n − 1) div 4` counted up from the bottom
row: the `left` offsets from box 1 are 0, 31, 62, 93 and the `top` offsets 0, −32, −64, −96. So a 4-box belt is
one row, an 8-box belt two, a 12-box belt three, a 16-box belt four, and the boxes past `numboxes` are all zero.
Box indices 0..`numboxes`−1 are the "boxes 0..3" the belt search of
[player/0001](../findings/player/0001-creation.md) walks.

## Interpretation notes

- `[C]` The default belt is row 2: `sub_0063C600_BeltFreeSlot` places the starting kits on a 4-box belt (`hp1` in
  boxes 0..3), and the belt search also ran on 8-box belts in the town session (player/0001 ledger row 18).
  ([player/0001 § Placement](../findings/player/0001-creation.md), fn:sub_0063C600_BeltFreeSlot@0x0063C600,
  fn:sub_0054D520_SrvPacket63Handler@0x0054D520)
- `[I]` The server's reading of this table is the box count (`numboxes`) and the box order; the `left/right/top/bottom`
  values are the client's hit boxes. The findings name no function reading a rectangle (a scope note, not a full cross-reference). The belt-search record fields
  (which bytes of the 264-byte record `BeltFreeSlot` reads, how it picks the row for a worn belt) are Phase 1.2's.

## Open questions

- `[L]` Which function turns a worn belt's `Armor.belt` into a row, and whether the second set (rows 7..13) is
  ever indexed on the server. Plan 0060 Phase 1.2 (reader survey; its Open question).
- `[L]` The width of `numboxes` in the readers (u32 by stride; any integer width fits).
