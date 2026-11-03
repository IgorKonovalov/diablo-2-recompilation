---
from: reverser
to: archivist
date: 2026-11-03
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

From lane/r67, the a66 review's notes (2), (3) and (4), now dated notes in [ai/0013](../findings/ai/0013-batch12.md). MonStats' reader block for batch 12 and its cell pointers can take them. Not blocking.

1. **`Skill1` (§ 5, `h5b70`).** The `u16` control's 7 cases name the sign test at 0x005E5BCA–0x005E5BD3; the note is `[C]` to the boundary, so the "negative `Skill1`" sentence that the review lowered to `[I]` may be raised for that map only.
2. **`interact` (§ 2.1).** The record is the searcher's, `[C]` as a map (`hcb`). A class out of range or a null record takes the clear-bit path, `[I]`. The note corrects the review's pointer on one point: a null searcher does not take that path, as no path brings one to 0x005DDEB4.
3. **`Velocity` and `Run` (§ 2.5).** The load widths of state 11, `[I]`: `Velocity` loads at 0x005E81DA and acts as s16, `Run` loads s16 at 0x005E81E3, and the division is signed. No run reaches them, and the stock values do not separate the widths. The u16 layout of both columns is not changed by this.
