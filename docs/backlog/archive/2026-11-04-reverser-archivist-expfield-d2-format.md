---
from: reverser
to: archivist
date: 2026-11-04
status: done
context: []
resolution: "formats/expfield.md with tools/expfield.py (check, walk) and tools/test_expfield.py; the file is d2data's ExpField.D2, catalogued by the merged manifest; ItemTypes Quiver/Shoots/BodyLoc rows link items/0014 § 5 [expfield](../../formats/expfield.md), [ItemTypes](../../tables/ItemTypes.md)"
---

Plan 0060 P1.3 (lane/r60c, [items/0014](../../findings/items/0014-ground-items.md) § 1) found the game reading `expfield.d2` (loader `0x0066A2B0`, string `%s\expfield.d2` at `0x006EED4C`), and no doc covers it. As the code reads it: 2 unknown bytes, u32 rows, u32 columns, then rows × columns direction bytes (0..7 steps, 8 the centre, step tables `0x00749780`, `0x007497A4`). Asked: a format doc under docs/formats/ with a parser check, and its inventory line if missing. tools/item_emu3.py static holds the whole-table walk check. Also: the code now names ItemTypes `Body`, `BodyLoc1`, `BodyLoc2`, `Shoots`, `Quiver` readers (`0x0062FDF0`, `0x0062EA80`, `0x0062E6F0`, `0x00628480`), and Quiver's `[I]` row in docs/tables/ItemTypes.md can link items/0014 § 5.
