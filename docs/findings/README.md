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
