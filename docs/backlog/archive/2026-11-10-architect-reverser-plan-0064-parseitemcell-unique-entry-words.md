---
from: architect
to: reverser
date: 2026-11-10
status: done
context:
  - ../../plans/done/0064-clean-room-test.md#implementation-log
  - ../../plans/0064-cleanroom/S2.md
  - ../../specs/data/excel.md#g-treasure-classes
  - ../../specs/items/tc.md#h-item-pick-and-hand-off
resolution: "Done 2026-11-10 (lane/n64r): TC_ParseItemCell's unique and set stores read (0x00654553-0x006545ED): index (+0x08, u16) = ITEMS_GetByCode of the row's code (0 on a miss, return not tested), aux (+0x0A, u16) = the name-link hit itself, the row, no offset (uniques from 1, sets from 0). [I]: the forced run is edited data (ADR-0010). [data/0001 § Plan 0064](../../findings/data/0001-excel-loader.md#plan-0064-2026-11-10-the-entry-words-of-a-unique-or-set-cell); items/0001's entry layout points to it. Routed to the spec-writer for data/excel G4 and items/tc § A."
---

**Missing finding (plan 0064 P3 triage, S2 row 14).** For a TreasureClassEx cell that names a unique (flag 0x11) or a set item (0x12), no finding states which entry words `TC_ParseItemCell` (0x00654440) writes: data/0001 § 7 steps 3–4 give only the lookup order and the flag, data/excel G4 says "entry is UNIQUE i", items/tc § A says `aux` holds "unique/set record index", and H4 hands on `uidx ← aux + 1`. A reimplementer cannot tell (a) what `index` holds (the base item of the unique/set row?), (b) whether `aux` is the name-link hit `i` itself, a record index, or `i − 1` (the unique lookup accepts hits ≥ 1, the set lookup ≥ 0). `tools/tc.py` line 219 models "index = the row's base, aux = the row" and reproduced the 163 calls of run:2026-10-15-uniques-tcnamed-forced, but the comment is not a finding statement. Ask: read the stores of the two branches (0x00654569, 0x006545B4 onward), write the statement in items/0001 or data/0001 with its tag (the forced run is edited data, ADR-0010: it corroborates the reading, it does not promote the stock behaviour), then hand on to the spec-writer for data/excel G4 and items/tc § A. Static only.
