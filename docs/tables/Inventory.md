# Inventory (`data/global/excel/inventory.txt` → `inventory.bin`)

> **Source archive:** `.txt` patch_d2, `.bin` d2exp (a mixed-archive pair, [README](README.md#source-and-shape): the `.bin` is the live one in a stock run; the two agree in every compiled cell)   **Rows:** 32 (33 data rows − 1 `Expansion` marker)   **Record:** 240 B (`0xF0`)
> **sha256:** `.txt` `45e9e49143b9f9c4fa5c8b4eef44b7113a2cd87ddd73a02b47a9503a1ca5524c`, `.bin` `1f294b790787957ef4e293e7a8dfddc0aa8200a5d29e06aa3e1232693024f049`
> **Doc status:** layout complete (plan 0060 Phase 0, `python3 -I tools/excel_bin.py diff`: 32 records × 72 fields = 2 304 cells, 0 mismatches; in the gate's `excel_layout` survey); which row a unit and page select, and which fields the server reads, are plan 0060 Phase 1.2's

## Purpose

One row per inventory page: the character classes' inventory with its grid and equipment slots, the monster page,
the vendor pages, the stash pages, the Horadric Cube's grid, the hireling. A row gives the grid's size in cells
(`gridX`, `gridY`) and, for a class row, the body-slot rectangles. The server's use is the cell counts: the placement
search ([player/0001 § Placement](../findings/player/0001-creation.md)) and the cube's output search
([items/0008](../findings/items/0008-cube.md)) run on a grid of that size. Every rectangle and the box size are
screen pixels, which the client reads (ADR-0025: the UI is out of scope). Research-map row: `items/use` (plan 0060).

## Row identity

- `[C]` The `.bin` is a u32 count (32) and 32 records of 240 bytes ([excel-bin.md](../formats/excel-bin.md)); the
  `Expansion` marker row takes no record. The loader allocates 240-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x0065C0F7`).
  The `class` cell is not compiled: a row is told apart by its position.
- `[C]` Rows (`.bin` index: `class` cell): 0 Amazon, 1 Sorceress, 2 Necromancer, 3 Paladin, 4 Barbarian, 5 Monster,
  6 Trade Page 1, 7 Trade Page 2, 8 Bank Page 1, 9 Transmogrify Box Page 1, 10 Guild Vault Page 1, 11 Trophy Case
  Page 1 (rows 0..11 stand before the marker), then, after it, 12 Big Bank Page 1, 13 Hireling, 14 Druid, 15
  Assassin, and 16..31 the same sixteen names with a `2` or `-2` suffix (`Amazon2` … `Assassin2`,
  `Trade Page 1-2`, `Bank Page2`, `Transmogrify Box2`, `Big Bank Page2`, `Hireling2`). Druid and Assassin
  (class ids 5, 6 by [CharStats](CharStats.md)) are rows 14 and 15, not 5 and 6, so a class id is not the row index
  for the expansion classes.
- `[C]` (data) Rows 16..31 repeat rows 0..15 on the other screen layout (e.g. `invLeft` 400 against 320). Their
  `gridX`, `gridY` equal the first set's for 15 of 16 pairs; the pair that differs is Hireling (row 13: 0 and 0;
  row 29: 255 and 255, from the blank cells `-1` stored in a byte), and the body slots are the same size. `[L]`
  Which set the server reads, and how it picks a row from a unit and a page: not read (Phase 1.2).

## Columns

`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel inventory` (layout `LAYOUTS["inventory"]`)
decodes all 32 records; the 72 mapped fields compare equal to the `.txt` in every cell. The two pad bytes after each slot's
width and height (`+0x03A`, `+0x04E`, … `+0x0EE`) are 0 in all 32 records (`excel_bin.py unknown`). Rectangle widths are
u32 (the stride from the probe, `[I]`), the counts and sizes are bytes.

| Column | Observed type / range | `.bin` field | Meaning | Tag |
|---|---|---|---|---|
| `class` | str, 32 distinct | — (not compiled) | page name | [C] (no field) |
| `invLeft`, `invRight`, `invTop`, `invBottom` | int; 0, 80, 320, 400 / 321, 401, 640, 720 / 0, 60, 220, 280 / 219, 279, 441, 442, 501, 502; −1 on the 2 Hireling rows | `+0x000`, `+0x004`, `+0x008`, `+0x00C` u32 | the page's screen rectangle | [C] offset |
| `gridX`, `gridY` | int; `gridX` {10, 6, 3, 0, 255}, `gridY` {4, 10, 8, 0, 255} | `+0x010`, `+0x011` u8 | the grid's width and height in cells; see below | [C] offset; meaning `[I]` |
| `gridLeft`, `gridRight`, `gridTop`, `gridBottom` | int, −1 on the Hireling rows | `+0x014`, `+0x018`, `+0x01C`, `+0x020` u32 | the grid's screen rectangle | [C] offset |
| `gridBoxWidth`, `gridBoxHeight` | int, always 29 | `+0x024`, `+0x025` u8 | one cell's size in pixels | [C] offset |
| `rArm`, `torso`, `lArm`, `head`, `neck`, `rHand`, `lHand`, `belt`, `feet`, `gloves` × (`Left`, `Right`, `Top`, `Bottom`, `Width`, `Height`) | int; −1 (and 255 for the two sizes) where the page has no such slot | slot k (k = 0..9 in this order) at `+0x028 + 0x14·k`: `Left`, `Right`, `Top`, `Bottom` u32 at +0, +4, +8, +12; `Width`, `Height` u8 at +16, +17 | the body slot's screen rectangle and size | [C] offset |

Body slots (`[C]` data): the 14 class rows (0..4, 14, 15, 16..20, 30, 31) have all ten; the two Hireling rows
have `rArm`, `torso`, `lArm` and `head` only (the other six are −1); the other 16 rows have none. Slot sizes in
pixels are the same in every row that has them (`rArm`, `lArm` 55 × 112; `torso` 56 × 82; `head` 54 × 51;
`neck`, `rHand`, `lHand` 23 × 24; `belt` 52 × 25; `feet` 54 × 52; `gloves` 54 × 53).

### Grid sizes (data)

`[C]` (data, first set, `gridX` × `gridY`): the five original class rows and Druid and Assassin 10 × 4 (the
inventory), Monster 10 × 10, Trade Page 1 and 2 10 × 4, Bank Page 1 6 × 4, Transmogrify Box Page 1 3 × 4,
Guild Vault Page 1 and Trophy Case Page 1 10 × 4, Big Bank Page 1 6 × 8, Hireling 0 × 0. `[C]` The cube's
output search ran on the Transmogrify Box row's 3 × 4 grid and the model reproduced every logged cell
([items/0008 § new check](../findings/items/0008-cube.md), 100 placements, 0 mismatches). `[I]` The inventory
grid is 10 × 4 for a player: the start-item placement (`Stock kits: tsc at (9, 3), isc at (9, 2)`) sits in column 9
of rows 2..3 ([player/0001](../findings/player/0001-creation.md)).

## Interpretation notes

- `[I]` The server's reading of this table is `gridX` and `gridY`: the placement search tests whether an item's
  cells fit inside the grid and are free (`sub_0063A8A0_InvGridFree`), scores spots by occupied or outside cells
  (`sub_0063B340_InvSpotScore`) and stores the item (`sub_0063AFD0_InvGridPut`). The findings name no reader of a
  rectangle, a body-slot size or `gridBox*` (a scope note, not a full cross-reference).
  (fn:sub_0063A8A0_InvGridFree@0x0063A8A0, fn:sub_0063B340_InvSpotScore@0x0063B340,
  fn:sub_0063AFD0_InvGridPut@0x0063AFD0)
- `[I]` The stash is not yet tied to a row: classic `Bank Page 1` is 6 × 4 and `Big Bank Page 1` is 6 × 8. Which one
  the game uses for a stash, and how `Trade Page`, `Guild Vault` and `Trophy Case` pages are reached, is unread.

## Open questions

- `[L]` The function that selects a row from a unit (class, monster, vendor, hireling) and a page, and whether the
  second set (rows 16..31) is indexed on the server. Plan 0060 Phase 1.2 (reader survey).
- `[L]` Whether `gridX`/`gridY` are read as bytes (the layout is byte-wide because the probe pins `+0x011`; a
  wider read of `+0x010` would see both). Phase 1.2.
