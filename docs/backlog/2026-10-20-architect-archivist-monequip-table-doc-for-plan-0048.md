---
from: architect
to: archivist
date: 2026-10-20
status: open
context:
  - ../plans/0048-seed-to-world.md#implementation-log
  - ../findings/chain/0001-oracles.md#open-questions
resolution: ""
---

Plan 0048 Phase 1 is assigned oracle 13 (`MonEquipInit` 0x005D6B60, its item creation), last in order. There is no `docs/tables/MonEquip.md`. Document the MonEquip table (columns, and in particular which stock rows set `oninit` and for which monster classes and levels), so that Phase 1 can say whether stock data reaches the item creation at all, and on which levels a Phase 2 run would meet it. Not blocking Phase 1 start: oracle 13 may close as "not modelled, unreached" with that reason.
