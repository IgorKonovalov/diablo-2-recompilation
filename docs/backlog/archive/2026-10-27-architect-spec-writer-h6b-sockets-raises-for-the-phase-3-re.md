---
from: architect
to: spec-writer
date: 2026-10-27
status: done
context:
  - ../../findings/items/0007-sockets-runewords.md#plan-0038-batch-h6b-run2026-10-27-sweep-sockets
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: "done: lane/s38k, plan 0038 Phase 3 re-tag of [items/sockets-runewords](../../specs/items/sockets-runewords.md)"
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

*Annotation (spec-writer, 2026-10-27, `lane/s38k`, plan 0038 Phase 3, items/sockets-runewords cluster):* applied to
[items/sockets-runewords](../../specs/items/sockets-runewords.md): sock 10 `[C]` on the built state, with a note that no
stock item reaches either refusal (`[I]`); L438 now tests the state alone, `[C]`, and the `0x40` reading is an `[I]`
note; L237 `[C]` for the empty slot in the 29 inserts with `p5` 1 and `[I]` for the reason; L243 and L450 split into
the 252 timer (`[C]`, with the frame + 2500 ÷ v + 1 schedule; the truncation `[I]`) and the 253 timer (`[I]`, no stock
case at an insert), plus the timers at every item load and creation (scoped to the run's counts); L291 `p4`, `p6`,
`p7` `[C]`, `p5` `[I]`; L283 the copier's 0, 1, 0, 0 and its own unit as the player `[C]`; L481 *Leaf*'s `par`-0 row
`[C]`, the ranged half `[I]` with no stock case; L482 and L507 `[I]` with their reasons; rows 9 (d-2c) and 29 (d-none,
the socket path) `[I]` with theirs; sock 46 `[C]`; sock 14 `[C]` for the two cases, the general reason `[I]`.
