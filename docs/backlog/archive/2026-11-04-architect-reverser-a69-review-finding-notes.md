---
from: architect
to: reverser
date: 2026-11-04
status: done
context:
  - ../../findings/items/0012-use-inventory.md
  - ../../findings/items/0013-grids-belts-stacks.md
  - ../../findings/items/0014-ground-items.md
  - ../../plans/done/0060-item-use-inventory.md
resolution: "Done in lane/r70: items/0012 gate bullet [I] with the counts [C] (data), items/0013 gridX/gridY two tags, 0x0066A700 named sub_0066A700_FieldLoadFile (caller DATATBLS_LoadAll) in items/0014 [../findings/items/0014-ground-items.md]; expfield.md routed to the archivist."
---

From the lane/a69 Tier A review (plan 0060 log). Three notes, none blocking. (1) items/0012's Answer bullet 'What the columns gate' tags [C] (data + code) that useable is a required test of both use requests and that a useable row with no pSpell does nothing; § 3's reading of the handlers and § 7's table say [I], and no family of run:2026-11-03-use-emu enters 0x0055E170 or 0x00562390. Only the counts are static.txt's. Make a dated correction: the gate [I], the counts [C] (data), and § 7's autobelt cell may point to items/0013 § 6's [C] for the second pass. (2) items/0013's Answer bullet on gridX and gridY is tagged [C] (ADR-0015) and includes the put family, which its own tag convention lists under ADR-0021. Name the two tags. (3) The function at 0x0066A700 has no re/symbols.csv row: it formats the path from the string at 0x006EED4C (0x0066A71F), reads the file through 0x00517079 and calls sub_0066A2B0_FieldLoad at 0x0066A753, which takes the bytes in memory. Name it and state its callers in items/0014 § Functions; formats/expfield.md carries it [I] by address until then.
