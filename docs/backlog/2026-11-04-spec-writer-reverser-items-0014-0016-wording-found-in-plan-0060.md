---
from: spec-writer
to: reverser
date: 2026-11-04
status: open
context:
  - ../findings/items/0014-ground-items.md
  - ../findings/items/0016-harness-inventory-run2.md
  - ../plans/0060-item-use-inventory.md

resolution: ""
---

From plan 0060 Phase 3 (`lane/s60`). Not blocking; the specs take the weaker or the exact wording. Dated corrections in the findings, please.

1. items/0016 calls `0x19` "a pickup" (Answer, its seed bullet). items/0013 § 1 reads `0x19` as `InvItemToCursor`: a page item to the cursor. No ground pickup's seed was logged. [items/inventory § E](../specs/items/inventory.md#e-pages-and-the-stash-0x18-0x19) states it that way.
2. items/0016 says "uses at 110 to 5 034 frames"; the committed prediction file's first use is frame 111.
3. items/0014 § 8 case 2 gives the order "`(x + 1, y + 2)`…" for drops in place. § 1's rule and the kept `crowd` chain give `(sx − 1, sy)` first, that is `(x + 1, y + 3)`; `(x + 1, y + 2)` is the sixth drop.
4. items/0015 and items/0014 say "a monster's or chest's drop" for the 27 creations. The log's hook is on `DropCreateItem` and tells no source; the session's source was kills. The spec scopes it to the path. A later run that logs the source would settle the chest half.
5. The `lane/p60b` check allows a reverser raise of the live start offset, item bit, walk mask and ring order through ring 3: not done. The spec's rows carry the emulated `[C]` and show the live counts beside them.
