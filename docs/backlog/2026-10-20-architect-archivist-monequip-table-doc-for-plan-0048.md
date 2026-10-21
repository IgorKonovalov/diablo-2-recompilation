---
from: architect
to: archivist
date: 2026-10-20
status: open
context:
  - ../plans/done/0048-seed-to-world.md#implementation-log
  - ../findings/chain/0001-oracles.md#open-questions
resolution: ""
---

Plan 0048 Phase 1 is assigned oracle 13 (`MonEquipInit` 0x005D6B60, its item creation), last in order. There is no `docs/tables/MonEquip.md`. Document the MonEquip table (columns, and in particular which stock rows set `oninit` and for which monster classes and levels), so that Phase 1 can say whether stock data reaches the item creation at all, and on which levels a Phase 2 run would meet it. Not blocking Phase 1 start: oracle 13 may close as "not modelled, unreached" with that reason.

**2026-10-20 (reverser, `lane/p48r`, plan 0048 Phase 1).** For the table doc: a `monequip` record (0x1C bytes) has
the s16 `monster` at `+0x00`, the s16 `level` at `+0x02` and the `oninit` byte at `+0x04` (`MonEquipInit` 0x005D6B60
tests `(char) row[+4]`); MonStats `+0x2A` is written at load by `MONEQUIP_Load` and is 0 in the `.bin`. On the stock
table two classes have an `oninit` first row, 234 and 267. Phase 1 models the draws as `[I]`, unreached
([chain/0002 § 11](../findings/chain/0002-retirements.md#11-oracle-13-monequips-items)); the entry stays open for
the table doc.
