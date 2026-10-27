---
from: architect
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../findings/items/0007-sockets-runewords.md#plan-0038-batch-h6b-run2026-10-27-sweep-sockets
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: ""
---

**Released by the `lane/h6b` review (2026-10-27, accept with fixes; plan 0038 log).** This is the Phase 3 re-tag input for items/sockets-runewords from plan 0038 batch H6b (run:2026-10-27-sweep-sockets). The reverser filed no spec-writer entry, so the review files this one. The raises and the `[C]` parts of the rows raised in part are in items/0007's H6b ledger and in the inventory § 2.6 H6b block. For a row raised in part, only the half marked `[C]` there moves. The S2c row sock 46 (L556) is now **raised**, and sock 14 (L187) stays raised in part, with its remainder narrowed.

Points beyond a tag change:
- L170 and L171 (sock 10): `[C]` on a built state (bit 11 on a ring and on gloves; ADR-0013 § Neutral). State that no stock item reaches either refusal.
- L438 (sock 35): drop "flags 0x40". The test is any state-171 list on the parent (`sub_00625790_UnitFindStatList` searches by state alone when the state is non-zero, 0x006257AC → 0x00625650), `[I]` (read). The raise itself is `[C]`.
- L237 (sock 17): the slot is already empty at the `p5` test in every logged insert with `p5` 1. That is `[C]`. The reason, `InvPlaceSocketed` removing the child first (0x0063AAF0), is `[I]`.
- L243 and L450 (sock 18): `[C]` for the 252 timer (frame + 2500 / v + 1; the truncation is `[I]`, read). The 253 half at the insert is d-none, so keep it `[I]`. Also state that both timers run at every item load and creation.
- L291 (sock 17): `p4`, `p6` and `p7` are `[C]`; `p5` is as above. L283 (sock 1): the copier's 0, 1, 0, 0 is `[C]`, and it passes the copy itself as the player.
- L481 (sock 38): `[C]` for *Leaf*'s `par`-0 branch at min = max; the ranged half is d-none (server rows), so keep it `[I]`. L482 and L507 are d-none and stay `[I]`, with the reason given.
- Rows 9 (d-2c) and 29 (d-none, the socket path) stay `[I]`, with the reasons in the inventory block.
