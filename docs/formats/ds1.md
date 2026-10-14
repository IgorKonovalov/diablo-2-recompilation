# DS1 preset maps (`.ds1`)

Owned by `archivist`. A DS1 file is one preset map: a grid of tile cells in several layers (walls,
floors, shadow, substitution), plus lists of placed objects and monsters, substitution groups and NPC
walk paths. `LvlPrest` records name up to six DS1 files each ([LvlPrest.md](../tables/LvlPrest.md)).
How the game *uses* a DS1 (which layers it reads, how substitution and objects are applied) belongs
to `drlg/preset` and `drlg/collision`. This doc covers the bytes only.

Parser: `tools/ds1.py` (`survey`, `dump`, `lvlprest`, `units`). Lead for the layout: none.
The fetched editor manual (`src:siramy-ds1edit`, [sources.md](../sources.md)) is a user guide with no
byte layout, so every layout row below is derived from the files (no lead; derived from data). Tags follow
the data-format rule in the evidence rules: a field is `[C]` when the parser reads every file of the type and ends exactly at the last byte, *and* the values make sense. A
version threshold that falls between versions this game does not ship stays `[L]`.

**Scope of the tags.** A `[C]` here describes the **encoding**: where a field is and what values it
holds. It does not say what the game does with the field (which layers it reads, how a cell becomes a
tile, how objects are placed). Those claims need a code anchor in the drlg findings, and a drlg spec
cannot cite this doc for them.

## Files

- `[C]` **2276** `.ds1` files under `data/global/tiles/` in `workspace/merged/`: `act1` 597, `act2` 446,
  `act3` 521, `act4` 220, `expansion` 480, `guild` 10, `arena` 2.
- `[C]` LvlPrest names **2043** of them (2058 references); **233** are never referenced
  ([§ LvlPrest references](#lvlprest-references)).

### Version histogram

`python3 -I tools/ds1.py survey workspace/merged` (the `version` dword at `+0x00`):

| version | all files | parse cleanly | referenced by LvlPrest |
|---:|---:|---:|---:|
| 3 | 1 | 1 | 0 |
| 8 | 6 | 6 | 0 |
| 12 | 13 | 12 | 7 |
| 13 | 30 | 29 | 16 |
| 15 | 13 | 13 | 10 |
| 16 | 223 | 223 | 210 |
| 17 | 145 | 145 | 126 |
| 18 | 1845 | 1844 | 1674 |
| **total** | **2276** | **2273** | **2043** |

- `[C]` Versions 4–7, 9–11 and 14 do not occur. The files the game can reach through LvlPrest are
  versions 12, 13 and 15–18 only.
- `[C]` **2273 files parse with no leftover byte.** The other 3 are malformed, none of them is
  referenced by LvlPrest, and the parser reproduces each failure exactly
  ([§ Malformed files](#malformed-files)).

## Layout

Little-endian. Every field is a 32-bit integer except the file-name strings. The file is a header,
then the cell layers, then up to three lists, and the version decides which parts are present.

```mermaid
flowchart LR
  H[header] --> F[DT1 file list] --> L["layers: (size_x+1)·(size_y+1) u32 each"] --> O[objects] --> G[substitution groups] --> T["v12–13 trailer"] --> P[NPC paths]
```

### Header

| order | size | type | name | present when | meaning | tag |
|---:|---|---|---|---|---|---|
| 1 | 4 | s32 | `version` | always | format version, 3..18 | `[C]` |
| 2 | 4 | s32 | `size_x` | always | width in tiles. The cell grid is `size_x + 1` cells wide | `[C]` |
| 3 | 4 | s32 | `size_y` | always | height in tiles. The grid is `size_y + 1` cells tall | `[C]` |
| 4 | 4 | s32 | `act` | v ≥ 8 | 0-based act number; the reader clamps it to at most 4 and uses it only to pick the per-act preset-unit tables, it is not stored | layout `[C]`, meaning `[I]` |
| 5 | 4 | s32 | `tag_type` | v ≥ 10 | substitution mode, 0/1/2, stored by the reader. 1 or 2 makes the substitution layer and (v ≥ 12) the group list present | layout `[C]`, gates `[C]`, name `[L]` |
| 6 | 4 | s32 | `file_count` | v ≥ 3 | number of strings that follow | `[C]` |
| 7 | var | char[]×n | `files` | v ≥ 3 | NUL-terminated tile-file paths ([§ File list](#dt1-file-list)) | `[C]` |
| 8 | 8 | s32×2 | `unk_skip` | 9 ≤ v ≤ 13 | `(5000, 5000)` in all 41 such files | layout `[C]`, meaning unknown |
| 9 | 4 | s32 | `wall_layers` | v ≥ 4 | number of wall layers, 0..4 | `[C]` |
| 10 | 4 | s32 | `floor_layers` | v ≥ 16 | number of floor layers, 0..2. Before v16 it is implicitly 1 | `[C]` |

- `[C]` The cell grid is `(size_x + 1) × (size_y + 1)`. This rests on byte accounting: with that cell
  count per layer, all 2273 clean files end exactly at their last byte, and the wall/orient zero pairing
  holds in every pair ([§ Layers](#layers)). No other count does both.
- `[C]` `size_x`/`size_y` equal the `SizeX`/`SizeY` of the LvlPrest record that names the file, in
  **all 1995** references where the record's size is non-zero (63 references are from records with
  size 0). So the header field and the table column are the same quantity, in tiles. This match says
  nothing about the "+1", which comes from the byte accounting above. Grids run from 2×2 to 101×103 cells.
- `[C]` `act` against the directory the file sits in: `act1` → 0 (594), `act2` → 1 (344) or 0 (102),
  `act3` → 2 (519), 0 (1) or 3 (1), `act4` → 3 (218) or 0 (2), `expansion` → 4 (409), 5 (49), 3 (13)
  or 0 (8), `guild` → 4 (10), `arena` → 5 (2). So the value is 0-based and mostly matches the directory, but 0 also appears outside act 1.
  `[I]` The reader reads it (v ≥ 8, else 0), clamps it to 4 and uses it only to choose the per-act
  preset-unit mapping tables ([§ Objects](#objects-v--2)); it is not stored with the DS1
  (fn:DS1_Parse@0x00665950, [drlg/0001](../findings/drlg/0001-ds1-dt1-readers.md#ds1_parse-in-stream-order)).
- `[C]` `tag_type` is 0 in 2124 clean files, 1 in 71 and 2 in 78. Non-zero values occur in v13, v16,
  v17 and v18.
- `[I]` Thresholds that fall in a version gap of the data, as 1.14d's reader tests them: `act` v ≥ 8,
  `tag_type` v ≥ 10, `wall_layers` v ≥ 4, `file_count` and the file list v ≥ 3. `[C]` `unk_skip` is read
  for 9 ≤ v ≤ 13 (`(unsigned)(v − 9) < 5`), code anchor plus this parser's byte accounting
  (fn:DS1_Parse@0x00665950, [drlg/0001 § DS1_Parse](../findings/drlg/0001-ds1-dt1-readers.md#ds1_parse-in-stream-order)). Only the versions
  in the histogram matter for 1.14d data.
- Version 3 (one file, `act1/court/court1b.ds1`, unreferenced) has no `wall_layers` field. It
  carries exactly 5 layers ([§ Layers](#layers)).

### Layers

`n_cells = (size_x + 1) × (size_y + 1)`. Each layer is `n_cells` u32 values in row-major order (x
fastest).

| version | stream order | tag |
|---|---|---|
| v ≥ 4 | for each wall layer *i*: `wall[i]`, then `orient[i]`; then `floor[0..floor_layers−1]`; then `shadow`; then `subst` **only if `tag_type` is 1 or 2** | `[C]` |
| v < 4 | `wall`, `floor`, `orient`, `subst`, `shadow` (5 layers, always) | count `[C]`, order and names `[I]` (fn:DS1_Parse@0x00665950) |

- `[C]` The order for v ≥ 4 is pinned by the content, not only by the byte count:
  - In every wall/orient pair, a wall cell is 0 **exactly when** its orientation cell is 0
    (1 319 917 zero pairs, 173 411 non-zero pairs, no mixed pair). That cannot hold if the layers are
    misassigned.
  - Orientation cells hold only 0..19.
  - Floor, wall and shadow cells each have their own low-byte signature (below).
  - Substitution cells are small numbers that track the group count.
- `[C]` There is exactly **one** shadow layer, and the substitution layer exists only when `tag_type ∈ {1, 2}`.
  Any other choice desynchronises the following object list in some file.

#### Wall, floor and shadow cells

`[C]` Observed bit distribution over every non-zero cell of the clean files (`survey` prints the
full histograms):

| bits | wall (173 411 non-zero) | floor (696 511) | shadow (15 055) | name (`[L]`, no lead) |
|---|---|---|---|---|
| 0–7 | `0x81` ×170 211, `0x91`, `0x85`, `0x89`, `0x99` | `0xC2` ×656 897, `0x42` ×39 303, `0xC6`, `0xCA` | `0x80` ×15 054, `0x88` ×1 | `prop1`: flag byte |
| 8–13 | 63 distinct (0..63) | 64 distinct | 64 distinct | sub-index (`sequence`), `[C]` via DT1 |
| 14–19 | 0, 8, 12, 4 | 0, 8, 12, 4 | 0, 8, 12 | unknown |
| 20–25 | 46 distinct | 49 distinct | 15 distinct | main index (`style`), `[C]` via DT1 |
| 26–30 | 0, 4, 1, 8 | 0, 4, 1 | 2, 6, 15 | unknown |
| 31 | 1 in 2 744 | 1 in 6 690 | 1 in 7 | `hidden` |

- `[C]` A cell is either 0 (empty) or has a non-zero low byte: no non-zero cell has bits 0–7 clear.
- `[C]` The low byte differs by layer kind: wall cells always have `0x81` set, floor cells `0x42`, shadow
  cells `0x80`. So the low byte is a per-layer flag byte rather than an index.
- `[C]` **The main index is bits 20–25 and the sub-index bits 8–13.** Together with the orientation
  (from the paired `orient` layer for walls, 0 for floors, 13 for shadows) they form a DT1 tile key.
  Every shadow cell, 97.9 % of wall cells and 93.9 % of floor cells name a tile in the DS1's own DT1
  list, and every alternative bit split does far worse. Data behaviour across two formats
  ([dt1.md § DS1 cells → DT1 tiles](dt1.md#ds1-cells--dt1-tiles), plan 0005 Phase 2).
- `[C]` The floor cells with low byte `0x42` (39 303) all carry key (0, 30, 0), a tile of
  `act1/outdoors/blank.dt1` that no DS1 lists. `[I]` The game adds `blank.dt1` to every room's DT1 list
  itself, forces that floor key (0, 30, 0/1) hidden (bit 31), and copies cell bit 7 into runtime tile
  flag `0x1` (fn:sub_0066E9B0_RoomCellBuild@0x0066E9B0, fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20;
  [drlg/0001 § Per-cell decision](../findings/drlg/0001-ds1-dt1-readers.md#per-cell-decision)). What flag `0x1` does in the renderer is not read.
- `[I]` Bit 31 sets runtime tile flag `0x8` (clears it otherwise). The DRLG builds a bit-31 cell like
  any other, except that orientations 8–11 are diverted to other handlers; nothing in DRLG drops it.
  Low-byte bits 2, 3 and 7 and bits 16–19, 26, 28 and 29 also become runtime flags (table in
  drlg/0001); low-byte bits 0, 1 and 2 and bit 27 select which tiles are picked for the cell (floor,
  wall, the bit-2 path, shadow) (fn:sub_0066E9B0_RoomCellBuild@0x0066E9B0,
  fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20; [drlg/0001 § Per-cell decision](../findings/drlg/0001-ds1-dt1-readers.md#per-cell-decision)).
- `[L]` That runtime flag `0x8` makes the tile invisible: `src:siramy-ds1edit` § Advanced tile editing
  and § "Weird" Tiles say a cell carries a per-layer Hidden bit; the renderer's test is not read.
- `[L]` Orientation values 0..19: 0 means none, and the rest are wall, corner, roof and special
  orientations (no lead; derived from data). Observed counts are in the `survey` output.

#### Substitution cells

- `[C]` Values 0..255 occur. In 142 of the 149 files with a substitution layer, every value is at
  most the file's group count. In the other 7 the maximum is larger (for example 50 with 8 groups).
- `[L]` A cell names the substitution group it belongs to, 0 meaning none. The 7 exceptions argue
  against a plain index, so this is a code question.

### Objects (v ≥ 2)

| field | type | present when | observed | tag |
|---|---|---|---|---|
| `count` | s32 | v ≥ 2 | 0..181 | `[C]` |
| `type` | s32 | | 1 (×2 676) or 2 (×15 101) | layout `[C]`, meaning `[I]`: 1 monster, 2 object (the reader also knows 4, an item by code) |
| `id` | s32 | | type 1: 0..58 (57 distinct); type 2: 0..149 (146 distinct) | layout `[C]`, meaning `[I]`: an index into a per-act table (below) |
| `x`, `y` | s32 | | 17 697 of 17 777 lie inside `5·(size+1)`. Read as sub-tile coordinates | layout `[C]`, meaning `[L]` |
| `flags` | s32 | v ≥ 6 | 0 (×17 754) or 1 (×23, all v18) | layout `[C]`, meaning `[I]`: bit 0 = the server does not spawn the unit (below) |

- `[I]` `type` 1 is a monster: from v5, `id` indexes the act's `MonPreset` list, which maps it to a
  MonStats row, a SuperUniques row or a third range above both; type-1 entries of earlier versions are
  dropped. `type` 2 is an object: from v6, `id < 150` is translated through a 5 × 150 per-act table and
  `id ≥ 150` is the object row `id − 150`; below v6 the raw id is kept. The act is the header `act`
  (fn:DS1_Parse@0x00665950, fn:MONPRESET_GetActList@0x00659B40, data:g_Ds1ObjectIds@0x00748AD8;
  [drlg/0001 § Object entries](../findings/drlg/0001-ds1-dt1-readers.md#object-entries--preset-units)).
- `[L]` The coordinates are in sub-tiles, 5 per tile: almost every object fits in a grid of
  `5·(size_x+1)` × `5·(size_y+1)`. The 80 outside it are unexplained.
- `[I]` `flags` is read from v6 (`v > 5`) and OR-ed into the preset unit's `+0x1C` (fn:DS1_Parse@0x00665950).
- `[I]` Bit 0 of that field means **the server does not spawn the unit**: the server's preset walk
  `RoomPresetUnits` skips every unit with `+0x1C` bit 0, and only it. The client's river objects get the bit from
  `DRLG_PresetClientObjects`, so they exist on the client only. Other bits are not tested there. ([drlg/0004](../findings/drlg/0004-preset-units.md) § Answer,
  fn:sub_005559A0_RoomPresetUnits@0x005559A0, fn:DRLG_PresetClientObjects@0x006663C0, struct:PresetUnit+0x1C)
- `[I]` **Act rewrites.** After the MonPreset mapping, `DS1_Parse` turns six MonStats ids into objects: at act
  index 2 (Act III) 297 `natalya` → object 382 and 366 `compellingorb` → object 404; at act index 4 (Act V) 514
  `nihlathak` → object 461 and 537..539 `ancientstatue1..3` → objects 476..474 (`1013 − id`). Each rewritten unit
  becomes type 2 with mode 0. Only MonStats-range ids can match. ([drlg/0004](../findings/drlg/0004-preset-units.md) § Where the unit list comes from,
  fn:DS1_Parse@0x00665950, 0x00665CB2, fn:MONSTATS_ValidId@0x004E6C50)

### Substitution groups (v ≥ 12 and `tag_type` ∈ {1, 2})

| field | type | present when | observed | tag |
|---|---|---|---|---|
| `unk_group` | s32 | v ≥ 18 | 0 in all 117 v18 files that have the list | layout `[C]`, meaning unknown |
| `count` | s32 | | 0..134 | `[C]` |
| `x`, `y`, `w`, `h` | s32 ×4 | per group | a tile rectangle; every one lies inside the `(size_x+1) × (size_y+1)` grid | layout `[C]`, meaning `[L]` |
| `unk` | s32 | per group, v ≥ 13 | 0 (×781), 1 (×61), 2..16 | layout `[C]`, meaning unknown |

- `[C]` The list is absent when `tag_type` is 0 (the object list is followed directly by the
  paths), and the `v ≥ 18` extra dword is pinned between v17 (absent) and v18 (present).
- `[C]` Groups occur in v13 (2 files: `act2/outdoors/palm.ds1`, `scrub.ds1`, 4 groups each), v16 (10),
  v17 (20) and v18 (117). The v13 groups already carry the per-group `unk`.
- `[C]` Version 12: the reader's gates are groups from v12 (`v > 11`, with `tag_type` ∈ {1, 2}) and the
  per-group `unk` from v13 (`v > 12`), so v12 groups have 4 dwords. Code anchor plus data behaviour: the
  only v12 file with groups, the malformed `trees.ds1`, fits 4-dword groups (fn:DS1_Parse@0x00665950;
  [drlg/0001 § DS1_Parse](../findings/drlg/0001-ds1-dt1-readers.md#ds1_parse-in-stream-order), step 10).
- `[I]` In a DS1 that `LvlPrest` names, the groups and the substitution layer are **never read**: no code reads a
  preset instance's substitution layer or groups. The only group reader, `sub_006704E0_LvlSubLoadDs1`, reads the
  DS1 a `LvlSub` record names. So the 429 groups of LvlPrest files ([§ Substitution groups by file
  source](#substitution-groups-by-file-source)) are dead data. ([drlg/0004](../findings/drlg/0004-preset-units.md) § Answer, fn:sub_006704E0_LvlSubLoadDs1@0x006704E0)

### v12–13 trailer

- `[C]` Every version 12 and 13 file has **one more s32 at the end**, and it is 0 in all 41 clean
  ones. It comes after the object list: the v13 town maps (34–37 objects) parse with it last. It also
  comes after the group list: `palm.ds1` and `scrub.ds1` (v13, 4 groups) parse with it last.
- `[I]` The game never reads it: paths are read only from v14, and the reader stops after the group
  list for v12–13, so the dword is dead bytes to the game (fn:DS1_Parse@0x00665950).

### NPC paths (v ≥ 14)

| field | type | present when | observed | tag |
|---|---|---|---|---|
| `count` | s32 | v ≥ 14 | 0 in 2256 files; 1..31 in 17 (v17 and v18 only) | `[C]` |
| `points` | s32 | per path | 1..8 | `[C]` |
| `x`, `y` | s32 ×2 | per path | position of the walker | `[C]` |
| point `x`, `y` | s32 ×2 | per point | sub-tile coordinates | `[C]` |
| point `action` | s32 | per point, v ≥ 15 | 1 (×328), 2 (×105), 3 (×43), 4 (×34), 5 (×1) | layout `[C]`, meaning `[L]` |

- `[C]` Every one of the 136 paths starts at the `(x, y)` of an object in the same file.
- `[I]` The reader attaches a path to the **last** unit in file order (of any type) whose `x` and `y`
  equal the path's, and skips a path with no such unit. `action` is read from v15; before that every
  point gets action 1 (fn:DS1_Parse@0x00665950;
  [drlg/0001 § Object entries](../findings/drlg/0001-ds1-dt1-readers.md#object-entries--preset-units)).

## DT1 file list

- `[C]` 10 496 strings over the clean files, 1..24 per file. Each is an absolute path from the
  original build tree: prefix `\d2\` (10 425) or `C:\d2\` (71), then `data\global\tiles\…`. Extension
  `.tg1` (6 888) or `.dt1` (3 608).
- `[C]` Mapped to `data/global/tiles/…` with the extension replaced by `.dt1`, **10 462 of 10 496**
  name an existing file. The 34 misses are `expansion/siege/debris.dt1` (33) and
  `act1/caves/caves.dt1` (1), neither of which ships.
- `[I]` The game skips this list (string by string) and never opens these files. A room's tiles come
  from its level type's `LvlTypes` `File 1..32`, filtered by a 32-bit mask, plus the fixed `blank.dt1`,
  `inviswal.dt1` and `warp.dt1` (fn:DS1_Parse@0x00665950, fn:DRLG_LevelDt1ListBuild@0x0066F240;
  [drlg/0001 § Where a level's DT1 files come from](../findings/drlg/0001-ds1-dt1-readers.md#where-a-levels-dt1-files-come-from)). The `.tg1`
  name suggests an editor-side tile group `[L]`.

## LvlPrest references

`python3 -I tools/ds1.py lvlprest workspace/merged` reads `lvlprest.bin`, the form the game loads.
Its layout diffs clean against `LvlPrest.txt` ([LvlPrest.md](../tables/LvlPrest.md)).

- `[C]` **All 2058** non-blank `File1..6` cells (a `0` cell means none) resolve to an existing `.ds1`
  file, case-insensitively, with paths relative to `data/global/tiles/`. **No misses.**
- `[C]` They name 2043 distinct files. None of the three malformed files is referenced.
- `[C]` In 81 records `Files` differs from the number of non-blank `File1..6` cells (e.g. `Files = 0`
  with 4 files named), so `Files` is not a plain count. `[L]` Its meaning is the drlg plans'.

## Warp-slot cells (orientation 10/11)

- `[I]` A wall cell whose paired orientation is 10 or 11 is a marker that the preset scan reads by its main index
  *m* (bits 20–25): *m* < 8 with sub-index 0 or 4 (bits 8–15) or bit 31 is a warp slot (`Vis`*m*/`Warp`*m*), 8–29 a
  pop, 30–33 a level point ([drlg/0007 § 1](../findings/drlg/0007-warps.md), fn:DRLG_PresetMapScan@0x00667970).
- `[C]` `python3 -I tools/ds1.py warps workspace/merged` (gate survey `ds1_warps`) lists the slots, points and
  waypoint units of every file `lvlprest.bin` names: 360 slot cells, 151 non-qualifying *m* < 8 cells (always beside
  a qualifying cell of the same slot), 217 pop cells, 38 point cells. The per-record results are in
  [LvlPrest § Warp slots](../tables/LvlPrest.md#warp-slots-plan-0022-phase-2).
- `[C]` `python3 -I tools/ds1.py objects workspace/merged` (gate survey `ds1_objects`, plan 0023) lists, with the unit
  mapping of § Preset unit survey, the records whose DS1s place objects 269, 397, 455, 573 and the pseudo-objects
  574–582; results in [Objects § DS1 survey](../tables/Objects.md#ds1-survey-objects-269-397-455-and-the-pseudo-objects-plan-0023-phase-1-follow-up).

## Preset unit survey

`python3 -I tools/ds1.py units workspace/merged` (plan 0016 Phase 0) reads every DS1 that `lvlprest.bin`
`File1..6` names (2058 references, 2043 distinct files, exit 0) and every DS1 that `lvlsub.bin` `File` names.
It applies the unit mapping of `DS1_Parse` as [drlg/0001](../findings/drlg/0001-ds1-dt1-readers.md#object-entries--preset-units)
reads it:
- `act` is the header field clamped to at most 4;
- type 1 goes through the act's MonPreset list;
- the act rewrites ([§ Objects](#objects-v--2)): at act index 2 and 4, six MonStats ids become objects (type 2);
- type 2 ids below 150 go through `g_Ds1ObjectIds`, read from the pinned `game.exe`;
- a path goes to the last unit in file order at its `(x, y)`.

The counts are `[C]` as data: one full pass, no error. Where a count depends on that mapping, it is only as
good as the mapping, which is `[I]` (fn:DS1_Parse@0x00665950, data:g_Ds1ObjectIds@0x00748AD8,
fn:MONPRESET_GetActList@0x00659B40). The counts are over distinct files: a file named by two records counts once.
"Act" below is the clamped header act plus 1. Which generator a record feeds is in
[LvlPrest § Survey by generator kind](../tables/LvlPrest.md#survey-by-generator-kind-plan-0016-phase-0).

### Units per act and type

`[C]` 16 372 units: as stored, 2 267 type 1 and 14 105 type 2; after the act rewrites, 2 261 and 14 111. No type 4
(item) entry, no type-1 entry of a version below 5, and no type-2 entry of a version below 6 or with an id of 150 or
more. So every stored object goes through the per-act table. "npc" is a type-1 unit whose MonStats class has `npc` = 1
(a data split, not a game rule). The table counts units after the rewrites; the raw-id columns are by stored type, and
the last column is the table's output only (the rewrites add rows 382 and 404 in act 3, 461 and 474..476 in act 5).

| act | monster | npc | object | raw id (monster+npc) | raw id (object) | object row after the table |
|---:|---:|---:|---:|---|---|---|
| 1 | 349 | 67 | 1 736 | 0..46 | 0..112 (75 distinct) | 1..580 (74 distinct) |
| 2 | 120 | 67 | 1 396 | 0..58 | 0..134 (82) | 4..582 (81) |
| 3 | 799 | 18 | 3 801 | 0..38 | 0..115 (92) | 5..581 (91) |
| 4 | 58 | 5 | 1 682 | 0..27 | 0..65 (46) | 93..580 (46) |
| 5 | 775 | 3 | 5 496 | 2..49 | 0..149 (94) | 35..570 (90) |

- `[I]` The act-3 row is settled (it was provisional until plan 0020 Phase 1): `0x004E6C50` is
  `MONSTATS_ValidId`, and the two act-index-2 ids are MonStats 297 and 366 ([§ Objects](#objects-v--2), [drlg/0004](../findings/drlg/0004-preset-units.md)).
  Acts 1, 2 and 4 have no rewrite. (fn:DS1_Parse@0x00665950, fn:MONSTATS_ValidId@0x004E6C50)

- `[C]` No table entry a shipped DS1 reaches holds −1, so no object unit is dropped by the table.
- `[C]` Act rewrites: six units hit them, one per id. Act 3: `act3/docktown/docktown3.ds1` has 297 (`natalya`, an
  npc), which becomes object 382, and `act3/travincal/travn.ds1` has 366 (`compellingorb`), which becomes object 404.
  Act 5: `expansion/town/townwest.ds1` has 514 (`nihlathak`), which becomes object 461 (0x1CD), and
  `expansion/mountaintop/mtntop.ds1` has 537..539 (`ancientstatue1..3`), which become 476..474. All are npc units
  but `compellingorb`. (`ds1.py units`, line `act rewrites`)

### Monsters per MonPreset range

`[C]` Every type-1 entry of every clean file of version 5 or later (2 676) has an id below its act's MonPreset
count once the act is clamped. None passes through raw. This corrects [MonPreset](../tables/MonPreset.md#row-identity),
which counted the two `siege_32x32?boss.ds1` files (header act 5) as raw. Over the referenced files
(monster + npc units):

| act | MonStats | SuperUniques | MonPlace | total |
|---:|---:|---:|---:|---:|
| 1 | 113 (10 classes) | 28 (12 rows) | 275 | 416 |
| 2 | 150 (24) | 24 (9) | 13 | 187 |
| 3 | 394 (12) | 24 (11) | 399 | 817 |
| 4 | 54 (12) | 2 (1) | 7 | 63 |
| 5 | 199 (16) | 36 (11) | 543 | 778 |

- `[C]` The table counts type-1 units after the act rewrites, so the six rewritten units (act 3: 2, act 5: 4) are
  not in it; they were in the MonStats column before plan 0020 Phase 1.

- `[C]` The MonPlace range is 1 237 units over 34 distinct (act, row) pairs. The most used are `place_fetishshaman`
  (act 3, 187), `place_impgroup` (act 5, 140), `place_miniongroup` (act 5, 124), `place_fallenshaman` (act 1,
  118), `place_fallen` (act 1, 76) and `place_deadbarb` (act 5, 76). `place_champion` has 53 units in acts 1, 4 and 5 and
  `place_unique_pack` 35 in acts 1–2. `place_group25..100` has 106 units, and `place_nothing` 12 in acts 1–2.

### Object `flags`

- `[C]` Over the referenced files `flags` is 0 on every unit but one. The exception is a monster:
  `expansion/baallair/wstone01.ds1`, act-5 position 47 (`worldstoneeffect`), flags 1. The other 22 entries with
  `flags = 1` ([§ Objects](#objects-v--2)) are in files that LvlPrest does not name.

### Paths

- `[C]` 117 paths with 459 points, in 16 files: 12 named only by preset-level records and 4 only by outdoor-cell
  records. No maze-room file has a path. Every path finds an owner, and no unit owns more than one. The owners
  are 103 npc units, 10 other monsters and 4 objects. The objects are two per file in `act3/docktown/docktown3.ds1`
  and `expansion/town/townwest.ds1`: in each, one stored object (rows 379 and 543) and one rewritten npc (`natalya`
  → 382, `nihlathak` → 461), whose path comes from the monster entry. (Before plan 0020 Phase 1 the survey kept the
  rewritten units as npcs and counted 105 / 10 / 2.)
- `[C]` `action` over the 459 points: 1 ×304, 2 ×88, 3 ×36, 4 ×30, 5 ×1. Monster-owned paths use 1, 2 and 4.
  The four object-owned paths use 1, 2 and 4. Action 5 occurs once, on an act-4 npc. Per act: act 2 has the
  most points (230), act 1 has 95.
- `[L]` What `action` selects (a wait, an animation, a sequence step) is a code question (backlog → reverser).

### Substitution groups by file source

| files | tag_type | files with groups | groups | group `unk` | non-zero subst cells |
|---|---|---:|---:|---|---:|
| LvlPrest, maze room | 2 (65 files) | 65 | 93 | 0 ×56, 1 ×37 | 2 061 |
| LvlPrest, preset level | 2 (2 files) | 2 | 2 | 0 | 2 |
| LvlPrest, outdoor cell | 1 (27 files) | 27 | 334 | 0 | 4 355 |
| LvlPrest, maze or outdoor (unsettled) | — | 0 | 0 | — | 0 |
| LvlSub | 1 (28 files), 2 (5) | 33 | 307 | 0 ×253, 1 ×24, 5 ×10, 3, 10 ×5 each, 2 ×4, 6, 8 ×2 each, 7, 12 ×1 each | 3 459 |

- `[C]` `tag_type` 2 among LvlPrest files is exactly `act1/crypt/` (67 files: 65 maze rooms, 2 on preset-level
  records). `tag_type` 1 among LvlPrest files is `act2/outdoors` (18), `expansion/siege` (6) and
  `expansion/icecave` (3), all outdoor cells. 1 949 LvlPrest files (95.4 %) have `tag_type` 0 and no group list.
- `[C]` Data side of the plan's open question (do type-2 rooms read DS1 groups?): LvlPrest DS1s do carry groups,
  429 in 94 files, with 6 418 non-zero substitution cells. A group `unk` other than 0 occurs among LvlPrest files
  only in the crypt maze rooms (value 1). This does not show whether the code reads them.
- `[C]` The v18 `unk_group` dword is 0 in all 87 LvlPrest files and 18 LvlSub files that have it.

### Files shared between records (the `0x84` candidates)

`[C]` Six files are named by more than one `LvlPrest` record. In each case the records have the same `SizeX`/`SizeY`,
so **no file is named at two different sizes**. Eight more files are named twice by the same record
(`act2/maggot/magnew3.ds1` and others).

| file | records (Def, SizeX×SizeY, kind) |
|---|---|
| `act1/tristram/tri_town4.ds1` (43×48) | 300 (0×0, level 38), 1090 (0×0, level 136) |
| `act2/maggot/magw.ds1`, `mage`, `magn`, `mags` (10×10) | 482/505, 483/506, 489/508, 485/507 (10×10, maze) |
| `expansion/siege/lake1.ds1` (8×8) | 948, 950, 951 (8×8, outdoor) |

- `[C]` `tri_town4` is the only file in two **different levels**: Tristram (38, act 1) and level 136 (act 5),
  both with record size 0. So both take the instance size from the level, which is 43×48 in every difficulty for
  both. The DS1 header act is 0, so both read the act-1 unit tables.
- `[L]` If the room split depends only on the instance size, which drlg/0003 reads as the 8×8 split, then these
  shared files are always cut the same way, and no shipped preset has a cell that is a border in one view and
  interior in another. One case is left: one record used both as a single room and split (the maze
  `single = (w ≤ 12 && h ≤ 12)` test uses the maze room's size, not the record's). The data cannot rule it out.
  Backlog → reverser.

## Malformed files

The parser keeps these in `KNOWN_MALFORMED`. `survey` fails if they stop failing, or fail
differently.

| file | version | problem | referenced |
|---|---:|---|---|
| `act1/outdoors/swamp2.ds1` | 13 | after its 11 groups come 12 dwords: a copy of the last group, then `15` and six zeros. The parser takes the first as the trailer and reports 44 bytes left over | [LvlSub](../tables/LvlSub.md) record 13 (`Swamp Big`) |
| `act1/outdoors/trees.ds1` | 12 | group count says 14, but there is data for 13 groups plus the trailer | [LvlSub](../tables/LvlSub.md) record 11 (`Trees`); loaded by the game, see below |
| `expansion/siege/xtransition.ds1` | 18 | ends after the object count, so the NPC-path count is missing (4 bytes short) | no |

- `[C]` All three fail only in their trailing lists. Their header and layers decode like any other file.
- `[C]` No LvlPrest `File1..6` cell names any of the three. `LvlSub.txt` `File` names two of them
  (`Trees.ds1` record 11, `Swamp2.ds1` record 13); `xtransition.ds1` is named by neither table.
- `[C]` The game loads `Trees.ds1` through LvlSub (record 11, loaded on first use), and its DS1 reader
  reads the 14th group's y, w and h 12 bytes past the end of the file buffer. Seen in 27 logged loads.
  (fn:sub_006704E0_LvlSubLoadDs1@0x006704E0, fn:DS1_Parse@0x00665950, run:2026-10-11-drlg-roomk;
  [drlg/0002](../findings/drlg/0002-room-build-draws.md), `Trees.ds1` bullet). This is the loader path
  the Phase 1–2 review asked about.
- `[L]` What those 12 bytes hold is heap content, not file content: 26 of the 27 loads held zeros, one
  held garbage. The format doc does not model them; open in drlg/0002 *Open questions*.
- `[L]` Whether `Swamp2.ds1` (an LvlSub `Type` 6 row like `Trees`) is loaded the same way, and how the
  game reads its 12 extra dwords; whether anything loads `xtransition.ds1`.

## Unknown fields

| field | where | observed |
|---|---|---|
| `unk_skip` | header, v9–13 | `(5000, 5000)` in all 41 files |
| cell bits 14–19, 26–30 | wall/floor/shadow cells | small sets of values (table above) |
| cell low byte | wall/floor/shadow cells | per-layer constant flags (`0x81`/`0x42`/`0x80` always set) |
| object `flags` | v ≥ 6 | 0 or 1 |
| `unk_group` | group list, v18 | 0 |
| group `unk` | v ≥ 13 | 0..16 |
| v12–13 trailer | after groups | 0; never read by the game `[I]` |
| path point `action` | v ≥ 15 | 1..5 |

## Preview

Tooling only (ADR-0005). `python3 -I tools/ds1.py render workspace/merged` draws every DS1 that
`lvlprest.bin` names (`--all`: every DS1) as one isometric PNG under `workspace/render/ds1/`, from the
tiles of [dt1.md § Pixel data](dt1.md#pixel-data). **The preview illustrates the data. It says
nothing about DRLG behaviour** and is not evidence for any tag. What it simplifies:

- Tile choice: for each key it takes the **first** tile in the DS1's own DT1 list, else the first in
  any DT1. Rarity variants, animation frames and the game's real tile source (`LvlTypes`, `Dt1Mask`)
  are ignored.
- Layer order: all floor layers, then all wall layers, each row by row (`y` outer, `x` inner). No
  depth sorting of walls against each other, no roof lift (`roof_height`), no orientation 3/4 corner
  pairing.
- Not drawn: hidden cells (bit 31 set; `--hidden` draws them, and the skipped count is printed),
  shadow and substitution layers, objects, NPC paths, orientations 10 and 11. No lighting,
  no shadow or blend tables, flat palette lookup with the act-directory palette
  ([palette.md](palette.md)).
- Placement: cell (`x`, `y`) is drawn with its tile origin at (`(x − y)·80`, `(x + y)·40`) pixels.
  Presets over 60 M pixels are drawn at half scale (12 files).
- Cells whose key is in no DT1 are filled with a palette-index-255 diamond and counted.
- Hidden cells are mostly collision filler: wall key (1, 5, 0) of `act1/outdoors/river.dt1`, RLE
  tiles of the single colour index 233 (blue bands along the river), and `act1/barracks/inviswal.dt1`
  invisible walls (green strips in the Durance). Counts skipped by default: `act1/town/townn1` 43
  wall cells, `act1/tristram/tri_town4` 126 wall cells, `act3/travincal/mephcomp` 26 wall + 1 floor.
  A few unhidden filler cells remain and are drawn as data (8 of the 48 river-filler cells in
  `townn1`, 2 of 127 in `tri_town4`). Their cell low byte is `0x81`; whether the game hides them by
  that or another flag is a reverser question (Open questions).
- A DS1 that parses with leftover bytes (a known malformed file, e.g. `act1/outdoors/swamp2`, 44
  bytes, reached with `--all`) is rendered as far as it parses and named in a `NOTE` line.

Last full run: 2 043 named DS1, 0 failures. Floor cells 559 279 from the own list, 37 315 from
another DT1, 11 missing; wall cells 149 674 own, 2 084 other, 61 missing, 768 skipped
(orientation 10/11). Missing keys fall in 13 files, all under `expansion/`.

## Open questions

- Answered `[I]` in [drlg/0001](../findings/drlg/0001-ds1-dt1-readers.md#tile-choice-by-rarity): the tile among rarity variants is a
  rarity-weighted draw on the room seed, and a level's tiles come from `LvlTypes`. The preview still
  takes the first tile ([§ Preview](#preview)).
- `[L]` Whether the game hides wall cells without bit 31 (river filler with cell low byte `0x81`)
  by another flag. drlg/0001 shows both kinds get a wall entry that differs only in runtime flag `0x8`;
  which flag the renderer tests is not read ([§ Preview](#preview)).

- `[L]` Cell flag bits (low byte, bit 31, bits 14–19 and 26–30). The index split is settled by data
  ([dt1.md](dt1.md#ds1-cells--dt1-tiles)). How the game uses the flags goes to the reverser (backlog).
- `[L]` What the substitution cells and groups mean, and what `unk_skip` holds (backlog → reverser).
  The header reads, the object `id` tables and the v12–13 trailer are answered above from drlg/0001.
