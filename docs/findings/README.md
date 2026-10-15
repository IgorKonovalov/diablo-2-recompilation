# Findings

Raw reverse-engineering notes from `reverser`, grouped by subsystem directory (`rng/`, `items/`,
`monsters/`, `drlg/`…). One file per topic: `NNNN-topic.md`, numbered within the directory. Findings
are the evidence layer that specs cite. They may hold decompile excerpts of *our* binary,
addresses, hypotheses and dead ends.

## Index

| Finding | Subsystem | Status |
|---|---|---|
| [rng/0001-rng-core](rng/0001-rng-core.md) | rng | answered: step, range and init `[C]` |
| [rng/0002-seed-tree](rng/0002-seed-tree.md) | rng/seeds | open: game → act → level → room → unit chain `[I]` |
| [rng/experiments](rng/experiments.md) | rng | `run:2026-10-11-rng-emu` |
| [data/0001-excel-loader](data/0001-excel-loader.md) | data/excel | answered: `.bin` always read (`-txt` compiles, `-direct -txt` to use it), 86/88 tables registered with matching record sizes `[C]`, TCEx is the live TC table `[C]`, code/name links `[I]` |
| [data/0002-mpq-precedence](data/0002-mpq-precedence.md) | data/excel | answered: MPQ order and priorities, loose files only under `-direct`, `data\local\use` = language id `[I]` |
| [items/0001-tc-resolution](items/0001-tc-resolution.md) | items/tc | open: drop path, TC choice, picks, NoDrop, recursion, hand-off `[I]`; runtime TC layout `[C]`; Phase 1b/2 pending |
| [save/0001-d2s-io](save/0001-d2s-io.md) | save/d2s | open: `.d2s` writer, reader, checksum, bit I/O, header/stat/item field ↔ runtime map; Phase 2 round trips (run:2026-10-12-d2s-io) make the write path, header sources, `gf` stream, item common part, seed/ilvl/quality, checksum/size codes, map-seed reuse and the drop seed `[C]`; rest `[I]`; Phase 2 under review; plan 0015 Phase 3: property framing, fixed fields, `has_class`, ear position, bit-13 clear sites `[I]` (§8) |
| [save/0002-quest-words](save/0002-quest-words.md) | save/d2s | open: quest record = bit `16q+s`, block *d* = difficulty *d* and act-travel words 7/15/23/28 (bits 0+13) `[C]` from two played saves; waypoint act tabs gated by words 7/15/23/26 (+28 to select Act V) `[I]`; server waypoint travel tests only the waypoint bit `[I]`; `build` recipe |
| [data/0003-string-tables](data/0003-string-tables.md) | data/strings | open: `.tbl` load (CRC checked, fatal), index → text with fallbacks, key lookup order patch → expansion → string, probing to `max_probes`, missing tables crash `[I]`; CRC check and its fatal halt `[C]` (run:2026-10-12-d2s-io); the excel 5382 rule `[C]` by data (plan 0015) |
| [data/0004-cell-converters](data/0004-cell-converters.md) | data/excel | answered: `.txt` compiler converters, missing-column defaults, key not-found −1, string keys → 5382 `[C]` where a named survey cell exercises them, the rest `[I]`; no-column fields of items/monstats/levels named padding or runtime-filled `[I]` (plan 0015 Phase 2) |
| [save/experiments](save/experiments.md) | save/d2s | `run:2026-10-12-d2s-io` |
| [drlg/0001-ds1-dt1-readers](drlg/0001-ds1-dt1-readers.md) | drlg/files | open: DS1 parser (no version check) and DT1 reader fields per offset; DS1 (a)–(d) and DT1 (a)–(d) answered, DS1 (c) bits 14–15/30, DS1 (e), object `flags`/group `unk`/path `action` and the collision bit meanings open |
| [drlg/0002-room-build-draws](drlg/0002-room-build-draws.md) | drlg/overview | open: room-seed draws between the re-seed and the activation draw (k) `[C]` by run:2026-10-11-drlg-roomk; bit-2 merge re-pick on the neighbour's seed `[C]` |
| [drlg/0003-generator-dispatch](drlg/0003-generator-dispatch.md) | drlg/overview | open: the two `DrlgType` dispatches, level-seed re-init, room-creation order and the preset file index `[C]` by run:2026-10-12-drlg-gen for all three generators |
| [drlg/0004-preset-units](drlg/0004-preset-units.md) | drlg/preset | answered: DS1 unit list, act rewrites, keep/drop rolls (two seeds), `PresetUnitsToRoom`, server handover, `LvlPrest` columns; `[C]` by run:2026-10-13-drlg-preset (0 mismatches), unreached branches `[I]` |
| [drlg/0005-collision](drlg/0005-collision.md) | drlg/collision | answered (Phase 1, static): grid build at activation from the tiles of the room and its active near rooms, unit marks (patterns, masks, at creation), the u16 bits by writer and reader, `CollisionTest` sizes 0–3, logic-region flood, `SpawnClassCellTest`, `NearWarpTest` (level warp points, waypoint side effects); all `[I]`; boundary B recommended for Phase 2 |
| [drlg/experiments](drlg/experiments.md) | drlg | `run:2026-10-11-drlg-roomk`, `run:2026-10-12-drlg-gen`, `run:2026-10-13-drlg-preset` |
| [hirelings/0001-hirelings](hirelings/0001-hirelings.md) | hirelings | open (plan 0033 Phase 1, static): hire table per NPC per game (`n + 10` NPC-seed draws, 10 distinct names), entry roll (type, level = player level − 5 + 0..4), hire and pet info, stats per level band, save level from experience, classes and E2, owner magic find; `[I]`, record layout and `ExpForLevel` `[C]` |
