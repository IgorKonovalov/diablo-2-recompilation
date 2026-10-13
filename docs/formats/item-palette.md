# Item colour shifts (`items/palette/*.dat`)

Owned by `archivist`. Tooling only (ADR-0005): no research-map row, no spec. Unique, set and magic
items are drawn in a colour other than their base art by a palette-index remap. The remap tables are
the eight `.dat` files under `data/global/items/palette/`; the colour is named by a row of
[colors](../tables/colors.md). Parser and helpers: `tools/palette.py` (`itempal`, `itemswatch`,
`shift_rgb`, `parse_shift`); renders: `dc6.py render --shift`, `dcc.py render --shift`,
`item_art.py tint`. Plan 0009 Phase 3. Leads: no lead; derived from data, then code ([items/0003](../findings/items/0003-item-graphics.md), plan 0015
Phase 4).

A layout claim is `[C]` when `palette.py itempal` reads every file and the data rules out the other
readings (evidence rules, data-format claims). Which file and which map the game uses for an item is
`[I]` from the code reading in [items/0003](../findings/items/0003-item-graphics.md) (static, no run). Rendered images are not evidence.

## Files

- `[C]` **8** files in `workspace/merged/`, all from d2data, all **5 376** bytes:

  | file | sha256 (first 16) | identity entries (of 5 376) |
  |---|---|---:|
  | `brown.dat` | `5e650fa99ec25211` | 4 201 |
  | `gold.dat` | `5e650fa99ec25211` | 4 201 |
  | `grey.dat` | `5e650fa99ec25211` | 4 201 |
  | `grey2.dat` | `a97b92287a4c1507` | 4 319 |
  | `greybrown.dat` | `5ffdd7b3e466ef85` | 2 858 |
  | `invgrey.dat` | `9f18595b3c7aaea5` | 4 261 |
  | `invgrey2.dat` | `87419d7570eaec8f` | 4 278 |
  | `invgreybrown.dat` | `3ded983b984547e3` | 1 948 |

- `[C]` `brown.dat`, `gold.dat` and `grey.dat` are byte-identical, so the eight files hold **6**
  distinct tables. (Identity entries: positions where the byte equals its index within its
  256-byte map, see below.)

## Layout

| offset | size | type | name | meaning | tag |
|---|---|---|---|---|---|
| `0x000 + 256·n` | 256 | u8[256] | `map[n]`, n = 0..20 | palette index → palette index | split `[C]`; use `[L]` (below) |

- `[I]` The game reads the first `0x1500` bytes of each file into its slot and takes map *c* as the
  256 bytes at `c·256`, for `c < 21`. (fn:ITEMGFX_LoadShiftFileB@0x006009C0, fn:ITEMGFX_GetShiftMap@0x00600C20)
- `[C]` Every file is exactly 21 × 256 bytes, with no header and no trailer, and `colors.txt` has
  21 rows: every byte belongs to one of 21 maps. The 256-byte split is the only one the data
  supports. Per file, the share of bytes equal to their offset mod *W* is 36.2–80.3 % at *W* = 256
  and at most 43.5 % for every other tried width (128, 192, 224, 384, 768), and the index-major
  reading (256 rows of 21 bytes) gives 0.4–0.5 %. A 768-byte reading (7 RGB palettes) is therefore
  ruled out as well. (`palette.py itempal`, verbose lines.)
- `[C]` Each map is a plausible remap: most entries are the identity (1 948–4 319 of 5 376 per
  file), and the changed entries are concentrated at the indices outside 40..159 (10 271 of the
  12 741 changed entries over all 168 maps). No map sends any index 1..255 to **0**. Entry 0 and
  entry 255 are changed in every map (0 → one of 15, 172, 174, 177, 180, 195, 208; 255 → one of 30,
  32, 112, 164, 171, 219, 221–224).
- `[L]` A map is applied to a sprite's pixel indices **before** the palette lookup: pixel *i* is
  drawn as `palette[map[i]]`. Basis: the identity-dominated shape above and renders that look
  tinted, not a code anchor. Our renderers do this by building a shifted palette (`shift_rgb`:
  entry *i* takes the colour of entry `map[i]`), which is equivalent for every *i* ≠ 0. They keep
  index 0 as the transparent index of DC6 and DCC renders, so the remapped value of entry 0 is
  never drawn. Whether the game remaps index 0 is open.

## Which map is which colour

- `[I]` Map *n* is the colour of `colors.txt` row *n* (`whit` = 0 … `bwht` = 20): the code indexes the
  map by the colour byte the item tables store, and that byte is the `colors.txt` row index
  ([colors](../tables/colors.md)). (fn:ITEMGFX_GetItemShift@0x0062C100, fn:ITEMGFX_GetShiftMap@0x00600C20,
  tbl:UniqueItems.txt:chrtransform)
- `[C]` A colour-family check agrees with that pairing in **159 of 168** maps. For each map, `itempal` averages the units-palette colour that
  the changed entries (source indices 1..254) map to, removes the luminance, and names a family (grey, red, green,
  blue, yellow, purple). The family is then compared with the one the code names (`whit`, `lgry`,
  `dgry`, `blac`, `bwht` grey; `oran`, `lgld`, `dgld` yellow). The 9 disagreements are all muted
  tables: `grey2` maps 7–9 (reds read as yellow-brown) and 17–18 (purples read as blue or grey),
  `invgrey` and `invgrey2` maps 7–8. `grey`/`gold`/`brown`, `greybrown` and `invgreybrown` agree in
  all 21. The check is a heuristic on the colours, not evidence of the pairing.
- In `palette.py itemswatch` output (one row of swatches per map, row 0 unshifted) the rows read, by
  eye, white, greys, black, three blues, three reds, three greens, yellows, golds, two purples,
  orange, bright white, in `colors.txt` order. That is a sanity check only (ADR-0005).

## Which file serves which item and view

- `[I]` Transform type *n* (1..8) in `Weapons`/`Armor`/`Misc` `Transform` and `InvTrans` (u8 at
  `+0x141`/`+0x142`, [Weapons](../tables/Weapons.md), [Armor](../tables/Armor.md)) selects file *n*
  in the order **grey, grey2, gold, brown, greybrown, invgrey, invgrey2, invgreybrown**, and type 0
  means no shift. The two loaders push the eight names in this order (`0x00505556`..`0x005055BF`,
  `0x00600B86`..`0x00600BEF`) with *n* = 1..8; slot 0 is never loaded. `tools/palette.py`
  `ITEM_SHIFT_FILES` encodes this order. (fn:ITEMGFX_LoadShiftFilesB@0x00600B80,
  fn:ITEMGFX_LoadShiftFilesA@0x00505550, fn:ITEMGFX_GetShiftMap@0x00600C20)
- `[I]` **`gold` and `brown` are never served.** Both map getters return no map for types 3 and 4 (and
  for type 0, type ≥ 9 and colour ≥ 21), although both loaders read all eight files. Of the three
  identical files only `grey` (type 1) can reach a pixel. (0x00600C37–0x00600C3F, 0x005038FB–0x00503903,
  fn:ITEMGFX_ShiftMapFromCode@0x005038D0)
- `[C]` Values in stock data: `Transform` 0, 1, 2, 5, 7, 8 (weapons 1, 2, 5; armour 1, 2, 5, 7, 8);
  `InvTrans` 0, 2, 5, 8; Misc is 0 in both. Under the order above, `InvTrans` selects only `grey2`,
  `greybrown` or `invgreybrown`, and `Transform` never selects `gold`, `brown` or `invgrey`. Armour
  `Transform` 7 and 8 would pick `invgrey2` and `invgreybrown` for the worn and ground views, so the
  `inv` prefix is not evidence that a file serves only the inventory.
- `[I]` The inventory icon is shifted by (base `InvTrans`, colour) and the ground animation and every
  worn layer by (base `Transform`, colour). For a unique or set item the colour is its row's
  `invtransform` (inventory) or `chrtransform` (ground, worn); a **blank colour gives no shift**, with
  no fallback to an affix colour. Magic and rare items take the first affix colour (suffixes 1–3, then
  prefixes 1–3), else the automagic affix's; other qualities a socketed gem's colour, else the automagic
  affix's; an active state with an item colour on the owner (worn paths) wins first, always with
  `Transform`. `item_art.py tint` renders the unique and set cases this way. ([items/0003](../findings/items/0003-item-graphics.md) § 3–4,
  fn:ITEMGFX_GetItemShift@0x0062C100, fn:sub_0046EE80_ItemCelDrawUi@0x0046EE80,
  fn:sub_00471EC0_UnitDraw@0x00471EC0)

## Tools

- `python3 -I tools/palette.py itempal workspace/merged`: per file, the period and transposition
  check, the identity count and the per-map colour family; then the byte-identical groups; last line
  `SURVEY itempal files=8 maps=168 codes=21 identity=30267 changed=12741 distinct_files=6
  family_ok=159 family_bad=9 errors=0` (registered in the gate, baseline
  `tools/gate/baselines/itempal.txt`). `errors` counts unreadable files, sizes that are not a multiple
  of 256, and map counts different from the `colors.txt` row count.
- `python3 -I tools/palette.py itemswatch workspace/merged workspace/render/items/palette`: one PNG per
  file, 22 rows (unshifted, then maps 0..20) of 256 swatches, units palette.
- `python3 -I tools/dc6.py render … --shift FILE:COLOUR` and `tools/dcc.py render … --shift FILE:COLOUR`
  (`FILE` a `.dat` name, `COLOUR` a `colors.txt` code or a map index, for example `invgrey:cred`):
  any DC6 or DCC tree rendered with one shift, to `<path>@<FILE>-<COLOUR>/`.
- `python3 -I tools/item_art.py tint workspace/merged`: from `workspace/render/items/index.tsv`,
  every unique and set row with a colour code gets its inventory icon (frame 0) and every frame of
  its drop animation rendered shifted, under `workspace/render/items/tint/<kind>/<row>_<id>/`, with a
  log `tint.tsv`. On the current tree: 414 rows, 287 icons, 312 drop animations (5 311 frames), 229
  views not rendered (91 with no colour code, 138 whose base transform type is 0), 0 errors.

## Open questions

- Answered `[I]` by [items/0003](../findings/items/0003-item-graphics.md): *Which map is which colour* and *Which file serves which item and view*.
- Whether index 0 is remapped by the game (items/0003 *Open questions*: the per-pixel loop is not read), and how the shift interacts with `.pl2` light and blend
  tables, is not modelled (plan 0006 left `.pl2` out).
- Why three of the eight files are identical is not known; it may be a placeholder in the data.
