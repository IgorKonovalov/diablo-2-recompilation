---
from: reverser
to: spec-writer
date: 2026-11-04
status: open
context: []
resolution: ""
---

[items/0014](../findings/items/0014-ground-items.md) § 1 and § 6 correct specs/quests/travel.md B1 (COLL_FindFreeNear): each lookup's base room is the last non-null room found, the first lookup's result kept even when null; `other` is the origin of a walk along `expfield.d2` tested with maskB, not a second footprint. run:2026-11-04-ground-emu holds it for size 1, step 1; the portal's size 3 and step 5 were not run. Asked: carry it into B1 when the spec is next touched; plan 0060 Phase 3 will state the drop's use of it. Also for specs/drlg/lifecycle.md: the sweep frees a unit only with a non-zero item data `+0x24`, which items/0014 § 3 reads as 0 for a monster's drop until its room has deactivated (`[I]`, Phase 2 case 7).
