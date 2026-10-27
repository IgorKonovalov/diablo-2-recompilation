---
from: reverser
to: spec-writer
date: 2026-10-27
status: done
context:
  - ../../findings/items/0008-cube.md#plan-0038-batch-h6a-run2026-10-27-sweep-cube
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: "done: lane/s38c, plan 0038 Phase 3 re-tag of [items/cube](../../specs/items/cube.md) and items/affixes C4i (aff 14's window half)"
---

Released by the `lane/h6a` review (2026-10-27, accept with fixes; corrected below). Phase 3 re-tag of items/cube from [items/0008 § Plan 0038 batch H6a](../../findings/items/0008-cube.md#plan-0038-batch-h6a-run2026-10-27-sweep-cube): raise L48; L147, L543, L757; L276 (the higher-tier half); L331; L482; L490, L520; L495; L496, L971; L548, L549, L562; L752, L772; L758 (lines at spec commit `4543b18`), each naming run:2026-10-27-sweep-cube. In part: L54 (the 0x18 path; 0x17 and type ≠ 4 stay `[I]`), L283 (`exc`; `eli` input stays), L349 (the classic half d-none), L465 (`uns`; `rem` d-none), L491 (the repair and the stackable `min` as logged; which stat 73 it reads, evaluated or base, and the 255 side stay `[I]`), L524 (the repair and a one-entry refill; "every stat-204 entry" stays `[I]`), L528 (the max-stack side; the 255 side stays `[I]`), L968 (the level window; "only" stays `[I]`, d-none on stock data). Shortfall: L707. d-none: L281, L550. Refinements to carry: an ItemCopy with one child draws two more game-seed steps (`[C]`; per child `[I]`, from the copy's child loop) (§ K / the seed table); the runeword copy brings the name id into prefix slot 0, which `uns` clears (the writer/reader path `[I]`, items/0007 H6b); `ItemInitStats` on an ethereal copy writes the plain base values (the mod line's MakeEthereal applies the bonus); InvPlaceItem sets flags bit 0 on a placed output holding items (`[C]`, raised at the review); the classic cow test is word 26, not word 40. S2c pieces: cube 49 (L681) case (b) `[C]`, case (a) d-none; items/affixes aff 14 (L331) level-window half met.

*Annotation (spec-writer, 2026-10-27, `lane/s38c`, plan 0038 Phase 3, items/cube cluster):* applied to
[items/cube](../../specs/items/cube.md), each naming run:2026-10-27-sweep-cube. Raised: the entry table row and the
`0x18` chain (cube 1 L48, L54's `[C]` half; `0x17` and type ≠ 4 a separate `[I]` bullet); the event codes in
*Constants*, G3 and the L2 refusal, with a G3 note (cube 7); B5 a′'s higher tier (cube 15); f′ `exc` `[C]`, split
from a new f″ `eli` `[I]` (cube 17); the C2 `eli` branch `[C]`, the classic version gate `[I]` with its no-stock reason
(cube 25); E3–E4 the copy's children without `uns` and with it `[C]`, `rem` `[I]` (cube 32); F1's strip (cube 36);
F2's `MakeEthereal` line and note, with an E3 note for the plain values (cube 38); F3–F4 `[C]` with inline `[I]` on
the stat-73 reading, the `qty` side of the min and the entries past the first, and four notes (cube 39); F5's `qty=N`
line and note `[C]`, the 255 side `[I]`, and the reimplementation note (cube 40); G4's two hooks and their note, the
rest of the hooks' writes `[I]` (cube 43); L1a and its note (cube 53); the classic word-26 test moved into L1 in the
code's order (0x0059419E before 0x005941BE) with its note, the old L3 removed and L4 renumbered L3 (cube 54); the
reimplementation note's level-window half `[C]`, "only" `[I]` (cube 58). Kept `[I]` with their no-stock reasons: e′
`eth` (cube 16), G5 `rem` (cube 44), J2–J3 (cube 51, shortfall). Refinements: K4 (a copied child, two game-seed steps,
`[C]` for one, `[I]` per child) with § M's rows, sequence diagram and reimplementation note; K3's runeword name id
`0x509F` `[C]`, the writer/reader path `[I]`; G4's flags bit 0 `[C]`. S2c pieces: cube 49 case (b) `[C]` (I4), case (a)
`[I]` with its reason; aff 14's level-window half raised in [items/affixes](../../specs/items/affixes.md) C4i too
(rule 8), "only" `[I]`.
