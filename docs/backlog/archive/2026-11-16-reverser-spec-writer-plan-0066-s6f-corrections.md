---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/anim/0001-modes-frames.md
  - ../../findings/anim/0003-movement-gates.md
resolution: "Done in plan 0066 Phase 3 (lane/n66v): anim/timing B1 (the primary hand, the unwritten index [I]), G1 (the MonStats read with no null test and the uninitialised local, [I]), G2 (three lookups, 9 of 223 on another record); anim/movement B4 (flag 0x8 at every counted end) and B5 (PathStop's step pair 0x006EB7D4)."
---

Plan 0066 S6f (`lane/n66s`, run:2026-11-16-sweep2-s6f) found refinements to the anim specs (no contradiction). For
Phase 3, with the rows' raises; match by text (lines at `b5999f5e`). Not blocking.

1. **anim/timing B1 (line 170):** the dual classes are by the *primary* hand's class index and the other's (primary
   = `INV_GetPrimaryWeapon`'s, location 5 tested first; with none the right hand is written as primary at inventory
   `+0x1C`, 0x0063D1D0, a write). A right hand that is not an item unit returns 0 with the index unwritten
   (0x0064F121). anim/0001 § 2's S6f note.
2. **anim/timing G1 (line 380):** for any non-player unit `SkillSeqIndex` reads the MonStats record with no null test
   (0x00643D2A–0x00643D31); `[I]` reading, unexercised. And PlrSeqColumn's uninitialised local after item 1's
   unwritten index (anim/0001 § 5's S6f note).
3. **anim/timing G2 (line 387):** the record is looked up three times, the second and third after `+0x30` is set, so a
   player's column then comes from `+0x40`'s mode; `+0x34` and `+0x48` can come from another record than `+0x30`
   (9 of 223 cases).
4. **anim/movement B4 (line 212):** flag `0x8` is set at every unblocked end with at least one counted crossing, not
   only at the 10th (0x00650295–0x006502A2); the findings already say so (anim/0003 § 2).
5. **anim/movement B5 (line 221):** `PathStop` sets the step `+0x72`/`+0x76` from the `.rdata` pair 0x006EB7D4 (both 0).
