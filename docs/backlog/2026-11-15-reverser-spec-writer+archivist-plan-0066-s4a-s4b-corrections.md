---
from: reverser
to: spec-writer, archivist
date: 2026-11-15
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/items/experiments.md#addendum-2026-11-15-plan-0066-batches-s4a-and-s4b-new-checks-over-the-kept-economy-and-inventory-logs-and-static-second-sources-lanen66h
resolution: ""
---

Plan 0066 batches S4a and S4b (lane/n66h) found two corrections for Phase 3, and one table-doc line.

1. **items/economy F1 (line 485 at b5999f5e), contradicted in part.** "the 13 `nodurability` crossbows of a `Repair` type": the full-table check gives 13 bases of a `Repair` type with `nodurability` 1, but they are 12 crossbows (type `xbow`) and the Phase Blade `7cr` (type `swor`). Reword to "the 13 `nodurability` bases of a `Repair` type (12 crossbows and the Phase Blade `7cr`)". items/0011 § 5 and its table row carry the dated correction; docs/tables/Weapons.md line 510 already says it right.
2. **items/economy H3 (line 806).** The six monster-code sites that pass `useAmmo` 1 are 0x005A26AD, 0x005A28BB, 0x005A2CAC, 0x005A4160, 0x005A6DB9, 0x005A7181; skills/0002 § 2 named five entries that do not hold them (0x005A35D0 is not an entry). If the spec or skills/catalogue copies those five addresses, drop them; the values stay `[C]` (33 of 33, r2), the functions `[I]` (dated note in skills/0002 § 2).
3. **archivist:** docs/tables/ItemTypes.md line 181 repeats "the 13 `nodurability` crossbows"; correct it as in 1.

No owner decision is needed.

**2026-11-16 (spec-writer, `lane/n66si`, plan 0066 Phase 3, the stats/items cluster).** Items 1 and 2 applied in
items/economy: F1 now names the 13 `nodurability` bases of a `Repair` type as 12 crossbows and the Phase Blade `7cr`
(row 40, corrected); H3 lists the six monster-code `useAmmo` sites, values `[C]`, functions `[I]` (the spec never
copied skills/0002's five entries; no spec, wiki page or table doc names 0x005A35D0). Item 3 (ItemTypes.md line 181)
is the archivist's and keeps this entry open.
