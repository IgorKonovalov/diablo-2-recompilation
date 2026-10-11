# Glossary

Entries are added as lanes meet the terms. Keep each to a line or two and link the spec or table doc.

- **TC** (Treasure Class): a weighted, recursive drop table (`TreasureClassEx`).
- **ilvl**: item level, normally the level of the monster or area that dropped the item.
- **alvl**: affix level, derived from ilvl and the base item's qlvl/magic level; it gates which affixes can roll.
- **mlvl**: monster level; depends on area and difficulty (`Levels.MonLvl*`).
- **DRLG**: Dynamic Random Level Generator, D2's map generation system.
- **Act / Level / Room**: map hierarchy. A level (`Levels.txt` row) is built from rooms; tiles come from DT1 and presets from DS1.
- **Seed**: an 8-byte RNG state `{low, high}`. Every game object (game, act, level, room, unit…) owns one. See [findings/rng/0001](findings/rng/0001-rng-core.md).
- **Map seed**: the 32-bit value at game `+0x7C` from which every act's, and so every level's, seed is derived. It is set by `-seed` or from the clock. See [findings/rng/0002](findings/rng/0002-seed-tree.md).
- **Draw**: one step of one seed object, whether through `RNG_Range`, `RNG_RangePow2` or an inlined copy. Specs number draws per seed (`draw#k`). See [specs/rng](specs/rng/README.md).
- **Level seed base**: the act's `+0x470` value (the act seed's first draw). A level's seed is `Init(base + levelId)`. See [specs/rng/seeds](specs/rng/seeds.md).
- **`.bin` / `.txt` (excel)**: every table ships as tab-separated `.txt` source and compiled `.bin` (u32 count + fixed-size records). The game always loads the `.bin`; `-direct -txt` is the only way to run on `.txt` content. See [specs/data/excel](specs/data/excel.md).
- **Expansion marker**: a `.txt` row whose first field is `Expansion`; it has no `.bin` record, so later records sit one lower than their `.txt` row. See [formats/excel-bin](formats/excel-bin.md).
- **Link (excel)**: the game's lookup object for one table: a sorted `{code, index}` array (4-char codes, case-sensitive) or a name tree (lowercased, first match wins). See [specs/data/excel](specs/data/excel.md#e-code-links-4-character-codes).
- **Item index**: position in the combined weapons + armor + misc array. See [specs/data/excel](specs/data/excel.md#d-the-combined-item-table).
- **TC index**: 0 = empty TC, 1–160 = auto item-type TCs (`weap3`… style, built from `itemtypes`), 161 + r = `treasureclassex` record r. `monstats` stores TCs this way. See [specs/data/excel](specs/data/excel.md#g-treasure-classes).
- **Distinct-Id ordinal**: how compiled tables store a monster reference: the position of the `Id` among distinct `monstats` Ids. The game uses it as a record position. See [specs/data/excel](specs/data/excel.md#h-monster-references).
