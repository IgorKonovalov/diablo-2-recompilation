---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: ""
---

[2026-10-16] from architect → reverser (H2b, H6a, H6b, H6c, H6e1 lanes): plan 0038 S2c review, harness pieces for remainders. The rows stay counted as S2c, raised in part, and each piece is named in [inventory § 5](../plans/0038-inventory/README.md#harness-batches).
- **H6a:** a crafting session at output ilvl ≤ 5 on `sst` (rows 72, 90), `lbt` (83) or `lgl` (84) for the crafted pick of 0 (cube 49). Case (b) faults the game, so it must be the session's last transmute. Row 17 on a magic tower shield also decides aff 14.
- **H6b:** an unidentified socketed parent's client flags before and after identifying it, with an insert tried each time (sock 14). The *Steel* load also gives the reader's `+0x38` store (sock 46).
- **H6c:** the stock item's store tab and grid cell (vend 22), and `+0x18`/`+0x28` of the store creation record at `IC0` (vend 26).
- **H6e1:** a cursor-item line at `sub_0055EEA0_CursorItemConsume` (qd 38).
- **H2b:** normal and rare drops requesting more than 3 and 4 sockets (sock 44).
- Context: [inventory § 2.6](../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews)

*2026-10-17 (reverser, `lane/rbs` static sweep):* skipped: needs harness; rides on plan 0038 harness batches H2b, H6a, H6b, H6c and H6e1.

*2026-10-25 (reverser, `lane/p51r`, [plan 0051](../plans/done/0051-backlog-sweep-6.md) Phase 1a, no slot):* **H2b piece
pruned.** H2b ran and was reviewed ([plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log), H2b
review ruling (d)): sock 44's piece met in part, the row stays raised in part as S2c filed it
([items/0007 § Plan 0038 batch H2b](../findings/items/0007-sockets-runewords.md#plan-0038-batch-h2b-2026-10-20)). Its
remainder (a drop that requests 4 or more sockets, so that a quality clamp acts) has no batch: out of this plan, and
the entry no longer carries it. **The four pieces left**, each still named in its batch row of
[inventory § 5](../plans/0038-inventory/README.md#harness-batches) (checked on `main` `9e221ed`): **H6a** the crafting
session at output ilvl ≤ 5 (cube 49, the session's last transmute) and row 17 on a magic tower shield (aff 14);
**H6b** the unidentified socketed parent's client flags around identifying, an insert tried each time (sock 14), and
the *Steel* load's `+0x38` store (sock 46); **H6c** the stock item's store tab and grid cell (vend 22) and `+0x18`/`+0x28`
of the store creation record at `IC0` (vend 26); **H6e1** the cursor-item line at `sub_0055EEA0_CursorItemConsume`
(qd 38). None of the four batches has a run on `main`. The entry stays open for them.
