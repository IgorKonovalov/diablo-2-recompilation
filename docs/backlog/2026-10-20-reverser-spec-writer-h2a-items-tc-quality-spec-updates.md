---
from: reverser
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../findings/items/0001-tc-resolution.md#plan-0038-batch-h2a-2026-10-20
  - ../findings/items/0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20
  - ../specs/items/tc.md
  - ../specs/items/quality.md
resolution: ""
---

After the architect accepts H2a (run:2026-10-20-sweep-items-tc; the ledgers are the "Plan 0038 batch H2a" sections of [items/0001](../findings/items/0001-tc-resolution.md#plan-0038-batch-h2a-2026-10-20) and [items/0002](../findings/items/0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20)), for the Phase 3 re-tag of [items/tc](../specs/items/tc.md) and [items/quality](../specs/items/quality.md) (items/tc also waits on H2b and H2c; items/quality on H2a only). Spec lines are those of the inventories' commits (tc `a398945`, quality `f9f28e9`).

items/tc: (a) *Entry points* L28 and L29 `[C]` (the death-event chain; the Find Item re-drop with `noNoDrop = 1`). (b) *Constants* L86 `GOLD_TYPE` = itemtypes record 4 `[C]`. (c) B1 (L201): the bit-17 and collision skips `[C]`, the `bonewall` fatal error stays `[I]` (split). (d) D3 pseudocode L361 `[C]`; the D3 step note L388 is **out of date**: the stop fired on the classic Countess, so "never fired in the run … code-read only" becomes `[C]` for the stop, `Picks = 0` staying `[I]` (d-none). (e) D4 `noNoDrop` (L395) `[C]`. (f) F2 (L517): "no run typed `/players` there" is **out of date**: the override applies in a lone TCP/IP host (game type 2), `[C]`. (g) F2 (L523) the cap only for a monster source `[C]`. (h) H8 (L671) `[C]`; H8–H9 (L674): `mul=` and gold find on own type 4 `[C]`; the equivalence half is d-none on stock data (only `gld` is of type 4 by any route), signedness stays `[I]` (split). (i) Reimplementation notes: L861 `/players` as a floor `[C]` for game types 2 and 3 with a lone player, type 1, other types and the multi-player case stay `[I]` (split); L869 `max` global and the sixth item without gold find `[C]`.

items/quality: (j) M3 (L263) `[C]` for monster killers whose owner is a player (skeletons, a hireling, a Hydra); a missing owner, plain or minion monster killers and the killer type ≥ 2 return stay `[I]` (split). (k) D6 (L292) `[C]`; its step note (L308) is **wrong as written**: "It never acted in the runs … code-read only" becomes "the clamp acts" (667 rolls; it decides 138), `[C]`. (l) D4–D7 order (L303) `[C]` (minimum after magic find and before the ratio).

**Added at the review (architect, 2026-10-20; line numbers of `main` `5a7feb3`).** The same corrections reach three more
places the entry left out: (m) items/quality *Open questions* L638, the `[L]` "the `*Min` clamp (D6) and its place after
magic find. No logged chance came near a minimum": answered (the clamp is reached in 667 rolls and decides 138; its
place is `[C]`); keep only the unique test's minimum, which no roll reached, if it is to stay open. (n) items/tc
*Open questions* L968–L970, the `[L]` on `game.type`: whether `/players` takes effect in a TCP/IP game is answered
(it does, game type 2, lone host); value 1 and the override below a larger live player count stay open. (o) The wiki
[items](../wiki/items.md) page: L220 ("this clamp never acted in any run"), L177–L179 and L542 (`/players` in a
multiplayer or TCP/IP game) and L548 (the minimum clamp among the untested), restated from the re-tagged specs.

**Released (architect, 2026-10-20, `lane/h2a` review: accept with fixes).** Rulings in the
[plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log): the 15 rows, 17 statements stand as filed
(12 raised, 5 in part); tc 34's L388 stop half is `[C]` and its `Picks = 0` half stays `[I]` (d-none as tc 13); quality 20
counts the 5 hireling rolls of the aborted H6d log. Apply (a)–(o) with the items/quality Phase 3 round now; items/tc's
part waits for H2b and H2c.
