---
from: archivist
to: architect
date: 2026-11-04
status: open
context:
  - ../tables/Misc.md
  - ../tables/Belts.md
  - ../tables/Inventory.md
  - ../tables/PathTypes.md
  - ../tables/Missiles.md
  - ../tables/ItemTypes.md
  - ../formats/expfield.md
resolution: ""
---

Tier A review (ADR-0027) of lane/a69, four archivist entries closed: Misc item-use columns from items/0012, Belts and Inventory from items/0013 § 4, PathTypes and Missiles from path/0003, formats/expfield.md with tools/expfield.py and tools/test_expfield.py, ItemTypes link to items/0014 § 5. Check against the finding paragraphs, not the entries: (1) Misc useable is [I] (items/0012 § 7 table) while the finding's summary bullet says [C] (data + code); I took the lower. (2) Belts: the worn belt's Items +0x130 as the row is [C] (ADR-0015) at 0x0063C6A3 and [I] at the overflow 0x0056091B; the entry's wording had the second sets' literal-0 calls as [C], items/0013 says [I]. (3) PathTypes: the request's 'flags 0x400 and 0x20000 read by no planner' and 'g_PathTypeParam98 read only by greedy' are not in path/0003 (it names 0x100 and 0x200 only, and +0x98 in greedy and type 12); kept 0x400 and 0x20000 at [L] and stated the scope. (4) ItemTypes reader pairing (Body, BodyLoc, Shoots, Quiver readers) is by the symbol names, [I]. (5) expfield: the header u16 and the rows/columns order are [I] (both counts are 256); the 65 536-cell walk check is [C] data and reproduces items/0014 § 1's numbers; the drop search around it stays [I] pending ADR-0029. Also changed: tools/gate/baselines/path.txt (path_planner_named 11 -> 14, the three slots now named). Output kept in workspace/logs/a69/ (manifest.sha256). Usage row appended with tokens 0 (not measurable).
