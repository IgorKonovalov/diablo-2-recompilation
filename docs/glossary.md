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
