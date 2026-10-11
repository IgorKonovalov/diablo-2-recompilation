# 0001 — DS1 and DT1 readers

> **Subsystem:** drlg/files (feeds drlg/preset and drlg/collision)
> **Question:** Which DS1 and DT1 fields does the game's reader code consume, at which offset, under which version test?
> **Date:** 2026-10-11   **Plan:** 0005 (backlog answers for Phases 1–2)   **Status:** open

Answers the two archivist → reverser backlog entries "DS1 fields that only the reader code can settle"
and "DT1 fields that only code can settle". Part (a) of each is answered in full; the cell bit fields,
substitution cells, sub-tile flags and `rarity` need the room/tile consumers and stay open.

## Answer (summary)

- [I] One function parses a DS1 in place: `DS1_Parse` loads the whole file (`FILE_LoadWhole`, tag
  `.\DRLG\Preset.cpp`) and keeps pointers into the buffer. It has **no version check**: any version is
  accepted, and each optional part is gated by its own version test (table in the walkthrough).
  (fn:DS1_Parse@0x00665950, fn:FILE_LoadWhole@0x00517079)
- [I] DS1 header: `act` is read when `version ≥ 8` (else 0), clamped to at most 4, and used **only** to
  choose the per-act preset-unit mapping tables; it is not stored. `tag_type` is read when `version ≥ 10`
  (else 0) and stored. (fn:DS1_Parse@0x00665950)
- [I] The DS1's own DT1 file list (`version ≥ 3`) is **skipped** with a `strlen` loop, never stored or
  opened. A level's tiles come from `LvlTypes` `File 1..32` of the level's type, filtered by a 32-bit
  mask at DRLG level `+0x50`, plus three fixed files (`Act1\Outdoors\Blank.dt1`,
  `Act1\Barracks\InvisWal.dt1`, `Act1\Barracks\Warp.dt1`). (fn:DS1_Parse@0x00665950,
  fn:DRLG_LevelDt1ListBuild@0x0066F240)
- [C] `unk_skip` is two dwords skipped when `9 ≤ version ≤ 13` (`version − 9 < 5`, unsigned). Code
  anchor plus data behaviour: the archivist's parser, using the same gate, ends all 2273 clean files
  exactly. (fn:DS1_Parse@0x00665950, fmt:ds1#header)
- [I] The v12–13 trailing dword is **never read**. Paths are read only when `version ≥ 14`, and the
  parser stops after the group list for v12–13, so the trailer is dead bytes to the game.
  (fn:DS1_Parse@0x00665950)
- [I] Object list: `type` 1 is a monster, mapped through the act's `MonPreset` list (v ≥ 5; earlier
  type-1 entries are dropped); `type` 2 is an object, mapped through a 5×150 per-act id table for
  `id < 150` (v ≥ 6); `flags` (v ≥ 6) is OR-ed into the preset unit's `+0x1C`. Path `action` is read
  when `version ≥ 15`, else every point gets action 1. (fn:DS1_Parse@0x00665950,
  data:g_Ds1ObjectIds@0x00748AD8, fn:MONPRESET_GetActList@0x00659B40)
- [I] The DT1 reader accepts only `version_major == 7`. A file with any other major (the six 4.1 files)
  is a fatal error if it is ever opened. `version_minor` is reused as a runtime state word.
  (fn:DT1_Relocate@0x0060A390)
- [I] DT1 tiles are indexed by the key (`orientation` `+0x14`, `main_index` `+0x18`, `sub_index` `+0x1C`)
  in a 128-bucket hash; tiles sharing a key go on one list, and the lookup returns up to N of them.
  Which one is chosen (`rarity`) is decided by the lookup's callers, not read here. (fn:sub_0060CFA0_TileIndexAdd@0x0060CFA0,
  fn:TILE_FindByKey@0x0060D040)

## Leads used

- [L] src:siramy-ds1edit: used only to name fields while locating the reader. No behavioural claim is
  compared here (the version thresholds below come from the code).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00665950` | `DS1_Parse` | parse one DS1 buffer into the 0x5C-byte DS1 record | I |
| `0x00665F40` | `DS1_LoadCached` | name-keyed, ref-counted cache in front of `DS1_Parse` (critical section) | I |
| `0x0066BF30` | `sub_0066BF30_PresetUnitCreate` | allocate one preset unit (`.\DRLG\DrlgRoom.cpp`) | I |
| `0x0066D7F0` | `sub_0066D7F0_Ds1OldOrientMap` | remap one orientation cell of a v < 7 file through a table | I |
| `0x00659B40` | `MONPRESET_GetActList` | `MonPreset` records and count for an act 0..4 | I |
| `0x00655710` | `SUPERUNIQUES_GetCount` | returns the SuperUniques record count | I |
| `0x0061E4A0` | `sub_0061E4A0_TilePathPrefix` | `/`→`\`, then `"%s\%s"` prefix on a tile path in place | I |
| `0x0061E520` | `DRLG_LoadLvlTypes` | load `lvltypes` (0x788-byte records, `File 1..32` at 0x3C stride) | I |
| `0x0061EAA0` | `LVLTYPES_GetRecord` | `g_pLvlTypes + i·0x788` | I |
| `0x0061EBB0` | `DRLG_LoadLvlPrest` | load `lvlprest` (0x1B0-byte records); optionally preload every DS1 | I |
| `0x00667890` | `sub_00667890_PresetRoomLoadDs1` | open the chosen DS1 of a preset room | I |
| `0x00667970` | `sub_00667970_PresetMapScan` | open the chosen DS1 of a preset level and scan its wall cells | I |
| `0x0066F240` | `DRLG_LevelDt1ListBuild` | build a level's DT1 list from `LvlTypes` + mask + 3 fixed files | I |
| `0x00641F60` | `sub_00641F60_TownDt1Add` | add one town DT1 by act 0/1/2 | I |
| `0x00604A40` | `DT1_ListAdd` | load a DT1 into the first free slot of a 32-slot list; fatal when full | I |
| `0x00600790` | `DT1_LoadCached` | name-keyed DT1 cache; read file, relocate, index | I |
| `0x0060A390` | `DT1_Relocate` | check version, fix up pointers in place | I |
| `0x0060A440` | `sub_0060A440_Dt1IndexTiles` | allocate the tile index and add every tile to it | I |
| `0x0060CDB0` | `sub_0060CDB0_TileIndexAlloc` | 0x200-byte bucket array (128 lists) | I |
| `0x0060CFA0` | `sub_0060CFA0_TileIndexAdd` | add one tile under its (orientation, main, sub) key | I |
| `0x0060D040` | `TILE_FindByKey` | copy up to N tiles of one key into a caller buffer | I |

| Address | Global | Role | Tag |
|---|---|---|---|
| `0x0096C9F0` | `g_pLvlTypes` | `lvltypes` records | I |
| `0x0096C9FC` | `g_nLvlTypes` | `lvltypes` count | I |
| `0x0096C894` | `g_pLvlPrest` | `lvlprest` records | I |
| `0x0096C898` | `g_nLvlPrest` | `lvlprest` count (`g_DataTables+0xC68`) | I |
| `0x0096D60C` | `g_Ds1Cache` | head of the DS1 cache list | I |
| `0x0096D610` | `g_Ds1CacheLock` | critical section for it | I |
| `0x008ADBB4` | `g_Dt1Cache` | head of the DT1 cache list | I |
| `0x006EEF20` | `g_Ds1OldOrientMap` | u32 table, old orientation → current, for v < 7 | I |
| `0x00748AD8` | `g_Ds1ObjectIds` | s32[5][150]: per-act DS1 object id → object row | I |
| `0x0096C6DC` | `g_MonPresetLists` | `MonPreset` record pointer per act (5) | I |
| `0x0096C6F0` | `g_MonPresetCounts` | `MonPreset` record count per act (5) | I |
| `0x0096C704` | `g_pSuperUniques` | SuperUniques records (0x34 bytes) | I |
| `0x0096C70C` | `g_nSuperUniques` | SuperUniques count | I |

## Walkthrough

### Where DS1 files are opened

- [I] `DRLG_LoadLvlPrest` loads `lvlprest` (0x1B0-byte records) and, for each record, rewrites the six
  `File1..6` cells (`+0x44`, stride 0x3C) in place through `sub_0061E4A0_TilePathPrefix`: `/` becomes
  `\` and the cell gets a `"%s\%s"` prefix. When its EDX argument is non-zero it also preloads every
  cell longer than one character through `DS1_LoadCached`, skipping records whose `Expansion` (`+0x20`)
  is set unless an expansion test passes (`0x00408F20`). (fn:DRLG_LoadLvlPrest@0x0061EBB0,
  fn:sub_0061E4A0_TilePathPrefix@0x0061E4A0, tbl:LvlPrest.txt:File1, tbl:LvlPrest.txt:Expansion)
- [I] At level build, the preset code opens `record + 0x44 + i·0x3C`, where `record` is the LvlPrest
  record and `i` the chosen file index, both held in the preset-room data. So the DS1 path is exactly
  the LvlPrest cell; how `i` is drawn is not read yet. (fn:sub_00667890_PresetRoomLoadDs1@0x00667890,
  fn:sub_00667970_PresetMapScan@0x00667970)
- [I] `DS1_LoadCached` walks a singly linked list (`+0x10C` next) comparing names; a hit increments the
  ref count (`+0x104`) and returns the stored record (`+0x108`). A miss allocates a 0x110-byte cache node
  and a 0x5C-byte zeroed DS1 record, then calls `DS1_Parse`. (fn:DS1_LoadCached@0x00665F40,
  data:g_Ds1Cache@0x0096D60C, data:g_Ds1CacheLock@0x0096D610)

### `DS1_Parse`, in stream order

The DS1 record (dword index → meaning): `[0]` tag_type, `[1]` file buffer, `[3]` size_x, `[4]` size_y,
`[5]` wall-layer count, `[6]` floor-layer count, `[7..10]` orient layers, `[11..14]` wall layers,
`[15..16]` floor layers, `[17]` shadow, `[18]` substitution layer, `[19]` group count, `[20]` groups,
`[21]` preset-unit list. Layer pointers point into the file buffer: cells are not copied.

| step | field | gate in the code | what the code does | tag |
|---|---|---|---|---|
| 1 | `version`, `size_x`, `size_y` | always | stored (`[3]`, `[4]`); version kept in a local | I |
| 2 | `act` | `v > 7` | read, `if act > 4: act = 4`; local only. Default 0 | I |
| 3 | `tag_type` | `v > 9` | stored in `[0]`. Default 0 | I |
| 4 | `file_count` + strings | `v > 2` | skipped string by string (`strlen + 1`) | I |
| 5 | `unk_skip` | `(unsigned)(v − 9) < 5` | 8 bytes skipped | C |
| 6a | layers, v < 4 | `v < 4` | wall `[11]`, floor `[15]`, orient `[7]`, subst `[18]`, shadow `[17]`, in that stream order; wall count 1, floor count left 0 | I |
| 6b | `wall_layers` | `v ≥ 4` | stored `[5]`, **not clamped** | I |
| 6c | `floor_layers` | `v ≥ 16` | stored `[6]`; else 1 | C |
| 6d | per wall layer | `v ≥ 4` | wall `[11+i]`, then orient `[7+i]` | C |
| 6e | floors, shadow | `v ≥ 4` | floor `[15+i]` per floor layer, then shadow `[17]` | C |
| 7 | orientation remap | `v < 7` | every orient cell replaced by `g_Ds1OldOrientMap[cell]`, in the buffer | I |
| 8 | substitution layer | `(unsigned)(tag_type − 1) < 2` | `[18]` = next layer | C |
| 9 | objects | `v > 1` | count, then per object `type, id, x, y` and `flags` when `v > 5` | I |
| 10 | groups | `v > 11` and `tag_type ∈ {1,2}` | `v > 17`: skip one dword; count `[19]`; per group `x, y, w, h` and `unk` when `v > 12` | C (gates), I (use) |
| 11 | NPC paths | `v > 13` | count; per path `points, x, y`; per point `x, y` and `action` when `v > 14`, else action 1 | I |

- [C] Steps 5, 6c–6e, 8 and the group gates of step 10 agree with the archivist's byte-accounting result
  (every clean file ends exactly, fmt:ds1#layers). That is a code anchor plus data behaviour.
  (fn:DS1_Parse@0x00665950)
- [I] Nothing follows step 11. A v12–13 file has no paths (`v > 13` fails), so its last dword is not
  read. The thresholds the archivist could not pin (act 4..8, tag_type 9..12, file_count 1..3,
  flags 3..8, path action) are, in 1.14d's reader: act ≥ 8, tag_type ≥ 10, file list ≥ 3, `wall_layers`
  ≥ 4, object `flags` ≥ 6, groups ≥ 12, group `unk` ≥ 13, paths ≥ 14, point `action` ≥ 15.
  (fn:DS1_Parse@0x00665950)
- [I] Version 3 reads the five layers in the order wall, floor, orient, subst, shadow, and stores a
  substitution layer even though `tag_type` is 0 for it. (fn:DS1_Parse@0x00665950)

### Object entries → preset units

```c
// fn:DS1_Parse@0x00665950, object loop (trimmed, renamed)
for (n = count; n; n--, p += (v > 5) ? 5 : 4) {
  type = p[0]; id = p[1]; mode = 0;
  if (type == 1) {                                   // monster
    mode = 1;
    if (v > 4) {
      list = MONPRESET_GetActList(act, &cnt);
      if (list && id < cnt) {
        kind = list[id].b1; id = list[id].w2;        // 4-byte records: u8 @+1, u16 @+2
        if      (kind == 0) id += nMonStats + SUPERUNIQUES_GetCount();
        else if (kind == 2) id += nMonStats;
        else if (kind != 1) id = -1;
      }
      // act-specific rewrites into objects: see Open questions
    }
  } else if (type == 2) {                            // object
    if (v < 6) { if (id == 0x23D) id = -1; }
    else if (id < 150) id = g_Ds1ObjectIds[act][id];
    else id -= 150;
  } else if (type == 4) {                            // item, by code; mode 3
    ...
  }
  flags = (v > 5) ? p[4] : 0;
  if (id >= 0 && (type != 1 || v > 4)) {
    u = PresetUnitCreate(type, id, mode, p[2] /*x*/, p[3] /*y*/);
    u->next = ds1[21]; ds1[21] = u;  u->flags |= flags;   // +0x1C
  }
}
```

- [I] Monster ids: `kind 1` is a `MonStats` row, `kind 2` a SuperUniques row (encoded above
  `nMonStats`), `kind 0` a third range above both (`nMonStats + nSuperUniques + index`). `nMonStats` is
  `g_DataTables+0xA80` (= `g_nMonStats`). An `id` at or past the act's `MonPreset` count passes through
  raw. (fn:MONPRESET_GetActList@0x00659B40, fn:SUPERUNIQUES_GetCount@0x00655710,
  data:g_nMonStats@0x0096C6B0, data:g_MonPresetLists@0x0096C6DC, data:g_MonPresetCounts@0x0096C6F0)
- [I] Objects: `id < 150` is translated per act through `g_Ds1ObjectIds[act·150 + id]`; `id ≥ 150`
  becomes `id − 150`, a direct object row. Files below v6 keep the raw id and drop 0x23D (573).
  (data:g_Ds1ObjectIds@0x00748AD8)
- [I] The preset unit (0x20 bytes): `+0x00` mode (0 object, 1 monster, 3 item), `+0x04` id, `+0x08` x,
  `+0x0C` next, `+0x10` path, `+0x14` type, `+0x18` y, `+0x1C` flags. Units are prepended, so the list is
  in reverse file order. (fn:sub_0066BF30_PresetUnitCreate@0x0066BF30)
- [I] Path ownership: a path with `points ≠ 0` is attached (at unit `+0x10`) to the **first unit in the
  list** whose `x` and `y` equal the path's, of any type. Since the list is reversed, that is the last
  matching unit in the file. A path with no matching unit is skipped. Each point is 12 bytes:
  `+0` action, `+4` x, `+8` y. (fn:DS1_Parse@0x00665950)
- [I] Groups are 0x18-byte records: `+0x00` x, `+0x04` y, `+0x08` w, `+0x0C` h, `+0x14` unk (v ≥ 13);
  `+0x10` is not written by the parser. (fn:DS1_Parse@0x00665950)

### Where a level's DT1 files come from

```c
// fn:DRLG_LevelDt1ListBuild@0x0066F240 (trimmed, renamed)
file = LVLTYPES_GetRecord(level->def[+0x1C0]);      // File 1 at +0x00, 0x3C apart
for (mask = level[+0x50], i = 0; mask && i < 32; i++, mask >>= 1, file += 0x3C)
  if (mask & 1) DT1_ListAdd(level + 0x68, file);
DT1_ListAdd(level + 0x68, "DATA\GLOBAL\Tiles\Act1\Outdoors\Blank.dt1");
DT1_ListAdd(level + 0x68, "DATA\GLOBAL\Tiles\Act1\Barracks\InvisWal.dt1");
DT1_ListAdd(level + 0x68, "DATA\GLOBAL\Tiles\Act1\Barracks\Warp.dt1");
level[+0x28] |= 0x1000000;
```

- [I] Bit *i* of the DRLG level's `+0x50` selects `LvlTypes` `File i+1` of the type index read from the
  level-definition record (`level+0x58`, field `+0x1C0`). `LvlTypes` paths were prefixed at load like
  the LvlPrest cells. The three fixed files are always added, which accounts for the `blank.dt1` floor
  tile (key 0, 30, 0) that no DS1 lists. (fn:DRLG_LevelDt1ListBuild@0x0066F240,
  fn:DRLG_LoadLvlTypes@0x0061E520, fn:LVLTYPES_GetRecord@0x0061EAA0)
- [I] `DT1_ListAdd` fills the first empty slot of a 32-pointer list and is fatal when all 32 are full.
  (fn:DT1_ListAdd@0x00604A40)
- [I] A second path adds one town DT1 by the act byte at `+0x480`: 0 → `Act1\Town\Floor.dt1`,
  1 → `Act2\Town\Ground.dt1`, 2 → `ACT3\Kurast\sets.dt1`. (fn:sub_00641F60_TownDt1Add@0x00641F60)

### DT1 load

- [I] `DT1_LoadCached` reads the file into a zeroed buffer, calls `DT1_Relocate`, then
  `sub_0060A440_Dt1IndexTiles`, and caches the result in a 0x110-byte node (`+0x104` file, `+0x108`
  index, `+0x10C` next). (fn:DT1_LoadCached@0x00600790, data:g_Dt1Cache@0x008ADBB4)
- [I] `DT1_Relocate`: requires dword `+0x00 == 7`, else fatal. If bit 1 of `+0x04` (the minor, 6) is
  set, it adds the buffer base to `tile_ptr` (`+0x110`), copies the file name into `+0x08` (the 260-byte
  header area the archivist found zero), and for each tile stores a pointer to that name at tile `+0x58`.
  It is fatal if tile `+0x54` or `+0x5C` is non-zero. Then it clears bit 1 and sets bit 2 of `+0x04`, so
  the minor marks "relocated". (fn:DT1_Relocate@0x0060A390)
- [I] So `unk_008` is the runtime name buffer, and `unk_54` dword 1 (`+0x58`) is the runtime name
  pointer. The pointer-like values the archivist found there are stale editor memory, overwritten on
  load. Dwords 0 and 2 must be zero. (fn:DT1_Relocate@0x0060A390)
- [I] Indexing: each tile is added under the key (`+0x14` orientation, `+0x18` main, `+0x1C` sub). Key
  nodes are 0x14 bytes (`+0` main, `+4` sub, `+8` orientation, `+0xC` tile list, `+0x10` next); the
  bucket is chosen by a hash of the orientation alone (`0x0060CD70`). `TILE_FindByKey(n, orient, main,
  sub)` copies up to *n* tile pointers of that key, in list order (newest first).
  (fn:sub_0060CFA0_TileIndexAdd@0x0060CFA0, fn:TILE_FindByKey@0x0060D040,
  fn:sub_0060CDB0_TileIndexAlloc@0x0060CDB0)

## Data touched

- tbl:LvlPrest.txt:File1 (`+0x44`, 6 × 0x3C), tbl:LvlPrest.txt:Expansion (`+0x20`), record size 0x1B0.
- `LvlTypes` (no table doc yet): `File 1..32` at `+0x00`, stride 0x3C; record size 0x788.
- fmt:ds1#header, fmt:ds1#layers, fmt:ds1#objects-v--2, fmt:dt1#header-276-bytes, fmt:dt1#tile-record-96-bytes.

## Dead ends

- `.\SRC\FindTiles.cpp` names only the index allocator, free and add helpers; the tile *choice*
  (rarity) is not in that module.
- `FUN_0061F500` also references `DATA\GLOBAL\TILES` and calls `DS1_LoadCached`; not read (likely a
  second LvlPrest-driven loader).

## Open questions

- DS1 cell bits (backlog (c)): the low flag byte, bits 14–19, 26–30 and 31. `sub_00667970_PresetMapScan`
  reads wall cells through `0x0067C570` and tests `(cell >> 20) & 0x3F` (main index), `(cell >> 8) & 0xFF`
  and bit 31, for orientations 10 and 11 only. Reading `0x0067C570` and the room tile builder will settle
  the rest.
- Draw decision for wall cells (architect request): wall cells with key (1, 5, 0) from
  `act1/outdoors/river.dt1` and `act1/barracks/inviswal.dt1`, mostly with bit 31 set but some with low
  byte 0x81 and bit 31 clear. `DS1_Parse` tests no cell bit (it only stores layer pointers), so the
  decision sits in the room tile builder. Not read yet: which of bit 31 and low-byte 0x80 the
  builder tests. Lead: the only cell test seen so far, in `sub_00667970_PresetMapScan`, reads bit 31
  together with `(cell >> 8) & 0xFF`, for preset-map scanning, not for drawing.
- Substitution cells and groups (backlog (e)) and the group `unk`: consumers not read.
- Object `flags` at unit `+0x1C` and path `action`: consumers not read.
- Act-specific monster → object rewrites in `DS1_Parse`: act index 2 turns two monster ids (from
  `0x004E6C50`) into objects 0x17E and 0x194; act index 4 turns monster 0x202 into object 0x1CD and
  0x219..0x21B into `0x3F5 − id`. `0x004E6C50` not read.
- `type 4` entries take a code from a string-pointer table at `0x00748AD4`, which overlaps
  `g_Ds1ObjectIds`; check the disassembly before naming it. No shipped DS1 has `type 4`.
- Where the DRLG level's `+0x50` mask is written (lead: `LvlPrest.Dt1Mask` at `+0x1AC`), and how the
  preset file index `i` is drawn (`Files`, RNG).
- DT1 (a) sub-tile flags and (c) `rarity`/`animated`: the callers of `TILE_FindByKey` and the collision
  builder are not read.
