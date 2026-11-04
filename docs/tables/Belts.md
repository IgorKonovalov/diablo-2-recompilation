# Belts (`data/global/excel/belts.txt` → `belts.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 14 (15 data rows − 1 `Expansion` marker)   **Record:** 264 B (`0x108`)
> **sha256:** `.txt` `55d680040663a8e6930863fc7687fe041b72c04cb98f97737794cc5bc0b41fb5`, `.bin` `cf8296500985694bc0327b5249a47bbe14558b65f956bd7a36b115f1a670e473`
> **Doc status:** layout complete (plan 0060 Phase 0, `python3 -I tools/excel_bin.py diff`: 14 records × 65 fields = 910 cells, 0 mismatches; in the gate's `excel_layout` survey); readers from player/0001 and [items/0013](../findings/items/0013-grids-belts-stacks.md) (plan 0060 Phase 1.2: the row, the second set, the rectangles)

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
  belts on the other screen layout. `[I]` **The second set is the client's, on this reading**: the record reader
  `sub_00660CB0_BeltsRecord(row, set, out)` copies the 264-byte record from `base + (7 * set + row) * 0x108` with no upper
  bound on the row (`[C]` (ADR-0015)); all 3 of its calls outside `0x4xxxxx` pass a literal set of 0, and the other 4,
  all in `0x4xxxxx`, take it from a register or a global (`0x007A5218` at `0x00483610`), the writers unfollowed
  ([items/0013 §§ Answer, 4](../findings/items/0013-grids-belts-stacks.md#answer-summary)). The belt search reads the
  first set: with the second set's counts declared unlike the first's, the control `secondset` fails 237 of 2 000
  `belt` cases `[C]` (ADR-0015). Which set the game reads on which screen mode is the client's (ADR-0025).
- `[C]` (ADR-0015) **The armor `belt` column indexes this table: `belts`' row is the worn belt's Items `+0x130`, or 2
  with no belt worn, in the first set; the count is the record's `+0x004`.** The belt search `BeltFreeSlot` passes the
  worn item's `+0x130` to `BeltsRecord` with set 0 at `0x0063C6A3`, and no worn belt gives row 2 (`0x0063C69B`). `[I]` The
  belt overflow `0x0056091B` (a smaller belt: each item at or above the new `numboxes` is removed and placed again) does
  the same, with row 2 at `0x0056093B`: that function is a reading, not one of the emulated families. The
  getter is `sub_00621ED0_ItemBeltByte`. ([items/0013 §§ Answer, 4, 6](../findings/items/0013-grids-belts-stacks.md#4-the-rows-the-tables-open-questions),
  fn:sub_0063C600_BeltFreeSlot@0x0063C600, fn:sub_00660CB0_BeltsRecord@0x00660CB0, fn:sub_00621ED0_ItemBeltByte@0x00621ED0,
  fn:sub_005608C0_BeltOverflow@0x005608C0, run:2026-11-04-inventory-emu)
- `[I]` The data match that led to it: `Armor.belt` (`+0x130`, 0..6) is 0 on `mbl` (Belt),
  1 on `lbl` (Sash), 3 on `hbl` (Girdle), 4 on `vbl` (Light Belt), 5 on `tbl` (Heavy Belt) and 6 on the ten
  elite and exceptional belts. Read as a row number in the first set it gives the right box count for each name
  (`belt` 12, `sash` 8, `girdle` 16, `light belt` 8, `heavy belt` 12, `uber belt` 16) and leaves row 2 (`default`, 4
  boxes) for no belt ([Armor](Armor.md), tbl:Armor.txt:belt).

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
- `[I]` The server's reading of this table, by direct calls, is the box count (`numboxes`) and the box order; the
  `left/right/top/bottom` values are the client's hit boxes. The rectangle reader `sub_00660D10_BeltsBoxRect` (`0x00660D10`,
  6 direct calls) is called only from `0x4xxxxx`, client code by the project's convention; `0x00660C70` has 0 direct
  calls, and table pointers to it are unfollowed, so this is a scope note over direct calls, not a full cross-reference.
  ([items/0013 § 4](../findings/items/0013-grids-belts-stacks.md#4-the-rows-the-tables-open-questions), `static.txt`)
- `[C]` (ADR-0015) **The belt search reads the box count only.** `BeltFreeSlot`: only a beltable 1 x 1 item; for each
  bottom box 0..3 that holds an item of the same class or the same list (`hp1..5`, `mp1..5`, `rvl`/`rvs`), the first free box
  up that column (`box, box + 4, ...` below `numboxes`); then, with `autobelt` ([Misc](Misc.md#belt-and-stack-columns)),
  the first free box of 0..3; else it returns 0. Controls: `walk1` (a column walk by 1) fails 192, `nogroup` 126, `noauto`
  337, `defaultbelt` 160, `secondset` 237 of 2 000 cases. `BeltPlace` ends at `InvGridPut(box, 0, 1, 0)` `[C]` (ADR-0021);
  after, `[I]`. `[I]` Packet `0x23` does not test `numboxes`: `BeltPutItem` needs 1 x 1, beltable and `box < 16`, and
  `InvGridPut` refuses an occupied box. (fn:sub_0063C600_BeltFreeSlot@0x0063C600, fn:sub_0063C790_BeltPlace@0x0063C790,
  fn:sub_0063C4F0_BeltPutItem@0x0063C4F0, [items/0013 § 6](../findings/items/0013-grids-belts-stacks.md#6-belts), run:2026-11-04-inventory-emu)

## Open questions

- Answered by [items/0013 § 4](../findings/items/0013-grids-belts-stacks.md#4-the-rows-the-tables-open-questions): the row of a worn belt is
  `BeltFreeSlot`'s `0x0063C6A3` (and `0x0056091B`, `[I]`); the second set (rows 7..13) is not indexed by any server call
  read (literal set 0), `[I]` over direct calls.
- `[L]` A box past `numboxes` by packet `0x23`: does it stay, and does a smaller belt's overflow take it? Phase 2 case 14
  (items/0013 Open questions).
- `[L]` The width of `numboxes` in the readers (u32 by stride; any integer width fits).
