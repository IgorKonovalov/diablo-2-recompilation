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

*2026-10-27 (reverser, `lane/h6b`, plan 0038 batch H6b):* **H6b pieces met.** sock 14: the unidentified socketed skull
cap's client flags were `0x00800000` (no bit 4, no bit 11, stat 194 0) and the insert was refused at the socketed
test; after a Scroll of Identify they were `0x00800811` (stat 194 2) and the same insert was accepted. sock 46: the
*Steel* sample's load logged the reader's store `0x509F` at `+0x38` (0x0062D1EA), and the client copies held the Name
index of their row ([items/0007 § Plan 0038 batch H6b](../findings/items/0007-sockets-runewords.md#plan-0038-batch-h6b-run2026-10-27-sweep-sockets),
run:2026-10-27-sweep-sockets). Both rows stay counted as S2c. **Left:** H6a (cube 49, aff 14) and H6c (vend 22, 26). The
entry stays open for them.

*2026-10-27 (reverser, `lane/h6a`, plan 0038 batch H6a, run:2026-10-27-sweep-cube):* **H6a pieces done.** Cube 49:
crafting at output ilvl 1 (clvl 1) on light boots faulted the game at its third transmute, the session's last; the
logger's `CNULL` at 0x005C2460 (record 0 of the picked id against a filled suffix slot) and the game's crash report
(`ACCESS_VIOLATION` at 0x005C2460) give case (b) `[C]`; case (a) is d-none on stock data (no crafted base, ilvl and
side whose first pick lacks a candidate). Aff 14: row 17 on a magic tower shield took *of Spikes* above the alvl, the
level-window half met; "only" has no separating stock case. Both rows stay counted as S2c, raised in part
([items/0008 § Plan 0038 batch H6a](../findings/items/0008-cube.md#plan-0038-batch-h6a-run2026-10-27-sweep-cube)).
The entry stays open for H6c (H6b's pieces met on `main`, `lane/h6b`).

*2026-10-27 (reverser, `lane/h6c`, plan 0038 batch H6c, run:2026-10-27-sweep-vendors):* **H6c pieces met.** Vend 22:
`sub_0062E880_ItemStorePage` returned the item type's StorePage byte for all 1 086 stock items, and the 901 placed items
lie on their tab, inside the 10 × 10 grid, none overlapping, tab 2 only after a failed tab-1 try (171) and 185 parked;
the cell search itself stays `[I]` (a column-major first fit gives 841 of 901), so the row stays raised in part. Vend
26: all 1 646 store creation records have `+0x18` = 4 and `+0x28` = 1 (and `+0x80` = 2) at
`ItemCreateByQuality`'s entry, proposed raised. Both rows stay counted as S2c
([items/0009 § Plan 0038 batch H6c](../findings/items/0009-vendors.md#plan-0038-batch-h6c-run2026-10-27-sweep-vendors)).
With H6a's and H6b's pieces met on `main`, every piece this entry carries has run; it can close at the `lane/h6c`
review.
