---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context: ["../plans/0066-simulation-inferred-claims-sweep.md", "../findings/skills/0002-missiles.md", "../specs/skills/dispatch.md", "../specs/skills/missiles.md"]
resolution: ""
---

Plan 0066 batch S2ae part 8 (`lane/n66sa`, run:2026-11-16-sweep2-s2ae8) ran `sub_00627260_UnitSetStat` whole on a
declared stat list and settled the setter writes of skills/dispatch rows 124, 130, 156 and skills/missiles rows 27
and 95 (C1). For Phase 3 to carry when the skills cluster is re-tagged (claims and anchors in
[skills/0002 § 24](../findings/skills/0002-missiles.md#24-plan-0066-batch-s2ae-part-8-the-stat-setter-run-whole-behind-handlers-18-26-skillweaponwear-and-in-missiledamagetostats-2026-11-16-lanen66sa)),
the spec says less than the code in these places:

1. **The setter** (wherever the specs cite `UnitSetStat`; it may belong to the stats spec): key `(stat << 16) +
   (param & 0xFFFF)`; an unchanged value does nothing; 0 removes the base entry (and shrinks the array by 4 slots
   when more than 8 are spare); the change `value − old` is added to the list's cache and up the parent chain (stops
   at `0x2000`, or at `0x40000000` for a damage-related row); a cache result of 0 removes the entry unless keepzero;
   a positive result on a row with `+0x53` sets list flag `0x20000000`; the stat callback runs for a row with
   `fCallback`; the client's changed-key list skips stats 6, 8, 10, 13 and 14 and takes a stat only with `Saved`
   (`+0x05` bit 4), and a player's change is marked a second time by `UnitSetStat`.
2. **K 26.** After the owner's write the packet's `+0x4C` becomes `max(0, +0x4C − loss)` and the handler returns 1.
3. **C1.** `MissileDamageToStats` also sets the missile data's `+0x14` bits 0 (block flag 0x1) and 1 (flag 0x4);
   stat 12 comes from its fourth argument; the stat-180 entries are the owner's extended-list cache entries only
   (none for a plain list), at most 128, each set at its own layer.

Not blocking.
