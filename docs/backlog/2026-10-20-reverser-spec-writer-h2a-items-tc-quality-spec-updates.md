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

items/quality: (j) M3 (L263) `[C]` for monster killers whose owner is a player (skeletons, a hireling, a Hydra); a missing owner, plain or minion monster killers and the killer type ≥ 2 return stay `[I]` (split). (k) D6 (L292) `[C]`; its step note (L308) is **wrong as written**: "It never acted in the runs … code-read only" becomes "the clamp acts" (667 rolls; it decides 138), `[C]`. (l) D4–D7 order (L303) `[C]` (minimum after magic find and before the ratio). Do not edit before the review ruling.
