# 0005 — Prerequisite formats: DS1, DT1, TBL, D2S

> **Status:** in-progress (approved)
> **Created:** 2026-10-11
> **Owner skill(s):** archivist
> **Related ADRs:** 0002-scope-creation-paths-and-enablers

## TL;DR

ADR-0002 lists four formats the core can't close without: DS1 (preset maps) and DT1 (tiles) for
`drlg/*` and `drlg/collision`, TBL (string tables) for unique-monster name rolls, and D2S (saves)
as the `[C]` harness for generated items. This plan documents each one in `docs/formats/` with a
parser in `tools/`, from the files alone. It's archivist work only. The code that *interprets* these
formats is planned with each subsystem. This plan keeps the archivist busy while the reverser
works on plans 0002–0004.

## Context

- Research map § Prerequisite formats: "DS1/DT1 and `d2s` come first". No format doc exists yet
  except `excel-bin` and `mpq`.
- Files are in `workspace/merged/` (`data/global/tiles/**.ds1|.dt1`, `data/local/lng/**.tbl`). There
  are no `.d2s` samples yet: Phase 4 needs saves written by the pinned game under the plan 0003
  harness (a fresh character per class, plus one with a few found items).
- Format claims follow the evidence rules: a field is `[C]` once a parser reads **every** file of
  that type without error *and* the decoded values make sense, or once the reading code is anchored.
- Leads: community format docs are allowed (register each in `docs/sources.md` before use, cite it
  `src:`). Decompiled code is not.

## Phases

### Phase 1 — DS1
- **Owner skill:** archivist
- **What:** Document and parse DS1: header and version variants, layers (walls, floors, shadow,
  substitution), the object and NPC-path lists, and the file and group references.
- **Outputs:** `docs/formats/ds1.md`, `tools/ds1.py`.
- **Done when:** `tools/ds1.py` parses every `.ds1` in `merged/` with no leftover bytes; a version
  histogram is recorded; every field is tagged; and fields with no known meaning are listed as such.
  Every `LvlPrest.txt` `File1..6` that names a DS1 resolves to an existing file (or the misses are
  listed).

### Phase 2 — DT1
- **Owner skill:** archivist
- **What:** Document and parse DT1: the header, tile records (orientation, main and sub index,
  rarity, the sub-tile flags used for collision), and the block headers. Pixel data only to the
  extent needed to skip it.
- **Outputs:** `docs/formats/dt1.md`, `tools/dt1.py`.
- **Done when:** `tools/dt1.py` parses every `.dt1` in `merged/` and accounts for every byte (pixel
  blocks may be skipped by length). The sub-tile flag byte is documented with the value
  distribution observed, and its meaning stays `[L]` until the collision plan anchors it.

### Phase 3 — TBL
- **Owner skill:** archivist
- **What:** Document and parse the `.tbl` string tables: the header, the hash table, and the
  key/value layout, including which tables override which (`string`, `expansionstring`, `patchstring`).
- **Outputs:** `docs/formats/tbl.md`, `tools/tbl.py`.
- **Done when:** `tools/tbl.py` dumps every `.tbl` (each language present) with key/value counts
  equal to the header's; a lookup by key returns the expected string for every
  `uniqueprefix`/`uniquesuffix`/`uniqueappellation` row; and the override order is tagged (`[L]`
  until the reverser anchors it).

### Phase 4 — D2S (header and item list)
- **Owner skill:** archivist
- **What:** From saves the pinned game writes, document the D2S header, checksum, and sections up to
  and including the item list. Decode the item bitstream fields that item specs need: code, ilvl,
  quality, the item seeds, sockets, ethereal, and the quality-specific IDs.
- **Outputs:** `docs/formats/d2s.md`, `tools/d2s.py` (read and re-checksum).
- **Done when:** `tools/d2s.py` reads every sample save; recomputing the checksum matches the
  stored one; an edited save (one changed byte, re-checksummed) loads in the game; and every item in
  the samples decodes to the end of its bitstream with no leftover bits. Property lists may stop at
  "length known" until `items/properties` documents `ItemStatCost` save bits.

## Open questions

- ~~Phase 4 is blocked until plan 0003 Phase 2 can launch the game.~~ Unblocked: the plan 0003 harness writes saves (implementation log, 2026-10-11). Phases 1–3 aren't blocked.
- If a DS1/DT1 field is only explained by code, file a backlog entry to the reverser rather than
  guessing.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-11 — Approved (human).** No phase started yet.
- **2026-10-11 — Phase 1 (DS1) landed (archivist).** [formats/ds1.md](../formats/ds1.md) and
  `tools/ds1.py` (`survey`, `dump`, `lvlprest`). The parser reads **2273 of the 2276** `.ds1` files in
  `merged/` and ends exactly at the last byte of each. The other 3 (`act1/outdoors/swamp2.ds1`,
  `act1/outdoors/trees.ds1`, `expansion/siege/xtransition.ds1`) are malformed in their trailing
  lists. None is referenced by LvlPrest, and `survey` checks that each still fails exactly as recorded
  (exit 0). Version histogram: 3:1 8:6 12:13 13:30 15:13 16:223 17:145 18:1845. The layout is `[C]`
  by data behaviour, with three corroborations from the content:
  - wall cell = 0 ⇔ orientation cell = 0 over all 1.49 M wall/orient pairs, which pins the layer order;
  - the DS1 `size_x`/`size_y` equal LvlPrest `SizeX`/`SizeY` in all 1995 references with a non-zero
    size, which pins the "+1" grid;
  - every NPC path starts on an object (136/136).

  Version thresholds that fall in a gap (4–7, 9–11, 14) stay `[L]` (`src:siramy-ds1edit`, newly
  registered). Cell bit meanings (main/sub index, flag byte), object `type`/`id`, the substitution
  cells and the DT1 list are `[L]` or unknown. Values are listed, backlog → reverser.

  **LvlPrest:** a full layout went into `tools/excel_layouts.py` (432 B, 23 fields, `excel_bin.py diff` 0
  mismatches over 25 093 cells, one unknown u32 at `+0x024`). [tables/LvlPrest.md](../tables/LvlPrest.md)
  is written, since it stayed small. All **2058** `File1..6` references in `lvlprest.bin` resolve to
  existing `.ds1` files, **no misses** (2043 distinct; 233 shipped DS1 are unreferenced). LvlPrest
  semantics are a backlog item for the drlg plans.

  **Surprises:**
  - Every v12/v13 file has an undocumented trailing dword (0), modelled as `unk_trailer`. It may be an
    NPC-path count read from v12.
  - In 81 records, `Files` differs from the number of named files.
  - The DS1 tile-file lists name `.tg1` paths in the build tree, which map to shipped `.dt1` files in
    10 462 of 10 496 cases.

  **Phase 2 hook:** DT1 can corroborate the `[L]` cell index split by checking that every
  (orientation, main, sub) triple names a tile in the DS1's DT1 files.
- **2026-10-11 — Phase 3 (TBL) status note (archivist).** `docs/formats/tbl.md` and `tools/tbl.py`
  already exist from plan 0002 Phase 1, so Phase 3 extends them and does not redo them. What they
  meet today:
  - **header and key/count check:** met for keys. All 20 `.tbl` under `data/local/lng/*/` read without
    error; every entry's index points at a used hash node whose back-pointer is that entry, and
    `file_size` matches. The parser reads keys only, and does not yet read or dump the string *values*.
  - **lookup by key for every `uniqueprefix`/`uniquesuffix`/`uniqueappellation` row:** not met.
    Key → compiled index is done (2278 item and monster cells match), but key → string is not.
  - **override order:** met for the compiled `.bin` indices, `[C]` by data behaviour
    (patchstring → expansionstring → string; 5382 = `dummy` when not found). The run-time order
    stays `[L]` (open in the backlog, `data/strings`).

  Left for Phase 3:
  - read and dump the values;
  - the unique-name lookup check;
  - the hash function, probing and `crc` (optional, `[L]` today).
- **2026-10-11 — Phase 4 (D2S) unblocked.** The plan 0003 harness writes saves under
  `workspace/wineprefix/.../Saved Games/Diablo II/` and can script new characters with
  `tools/xdrive.py` (backlog entry "from reverser → archivist: plan 0005 Phase 4 (D2S) can use the
  harness now"). The open question "Phase 4 is blocked until plan 0003 Phase 2 can launch the game" is
  answered.
- **2026-10-11 — Phase 2 (DT1) landed (archivist).** The human asked for Phase 2 straight after Phase 1,
  so the architect's review covers both. Outputs: [formats/dt1.md](../formats/dt1.md) and `tools/dt1.py`
  (`survey`, `dump`, `ds1keys`).

  **Byte accounting.** 263 `.dt1` files: **257 are version 7.6**, and every byte of them is accounted
  for (16 456 tiles, 361 484 blocks). Header, tile records and per-tile block areas tile each file
  exactly, isometric blocks are always 256 bytes, and every RLE block walks to exactly its length.
  `survey` exits 0. **Six are version 4.1** (`act1` barracks, gargtrap, catacombs, cathedrl, court,
  outdoor1). Only their header and pointer table are decoded. They are the stated exception to
  "every byte": no `LvlTypes` row and no DS1 list names them. LvlTypes' 230 DT1 references all exist
  and are all 7.6.

  **Sub-tile flags.** The flag byte's distribution is documented: bits 0, 1, 2, 4 and 5 occur, and 3,
  6 and 7 never do. The meaning stays `[L]`.

  **DS1 corroboration (the Phase 1 hook).** The key (orientation, cell bits 20–25, bits 8–13) names a
  tile in the DS1's own DT1 list for 100 % of shadow cells, 97.9 % of walls and 93.9 % of floors.
  Swapped or shifted splits score 7–88 % on shadows. So the DS1 index split is now `[C]` by data, and
  ds1.md is updated.

  **Surprises:**
  - Every floor cell with low byte `0x42` (39 303) is the `blank.dt1` tile, which no DS1 lists.
  - DS1 lists name `.tg1` files from the build tree, with some name drift (`caves.tg1` vs the shipped
    `cave.dt1`).
  - `orientation` → `direction` is a fixed mapping.
  - Some tile records carry pointer-like editor leftovers in `+0x58`.

  Backlog → reverser: the sub-tile flag bits and grid order, the tile source (LvlTypes vs the DS1
  list), rarity and animation, and the 4.1 files.
