---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../findings/items/0008-cube.md#plan-0038-batch-h6a-run2026-10-27-sweep-cube
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: ""
---

Held until the `lane/h6a` review accepts. Phase 3 re-tag of items/cube from [items/0008 § Plan 0038 batch H6a](../findings/items/0008-cube.md#plan-0038-batch-h6a-run2026-10-27-sweep-cube): raise L48; L147, L543, L757; L276 (the higher-tier half); L331; L482; L490, L520; L491, L495, L524; L496, L528, L971; L548, L549, L562; L752, L772; L758; L968 (lines at spec commit `4543b18`), each naming run:2026-10-27-sweep-cube. In part: L54 (the 0x18 path; 0x17 and type ≠ 4 stay `[I]`), L283 (`exc`; `eli` input stays), L349 (the classic half d-none), L465 (`uns`; `rem` d-none). Shortfall: L707. d-none: L281, L550. Refinements to carry: an ItemCopy draws two more game-seed steps per child it copies (§ K / the seed table); the runeword copy brings the name id into prefix slot 0, which `uns` clears; `ItemInitStats` on an ethereal copy writes the plain base values (the mod line's MakeEthereal applies the bonus); InvPlaceItem sets flags bit 0 on an item holding items (`[I]`); the classic cow test is word 26, not word 40. S2c pieces: cube 49 (L681) case (b) `[C]`, case (a) d-none; items/affixes aff 14 (L331) level-window half met.
