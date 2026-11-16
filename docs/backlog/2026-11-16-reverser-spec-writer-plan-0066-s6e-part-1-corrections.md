---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/anim/experiments.md
resolution: ""
---

Plan 0066 batch S6e part 1 (`lane/n66l`, 2026-11-16) corrections for Phase 3 in specs/anim/timing (lines at
`b5999f5e`, match by text). Record: findings/anim/experiments.md, run:2026-11-16-sweep2-s6e;
`workspace/logs/n66l/s6e/run/check.txt`. Not blocking.

1. **B2, line 157** ("fatal if longer than 8 characters"). `ANIMDATA_Find` tests the name's length inside its record
   loop (0x0066A941–0x0066A94B), so the fatal comes only when the name's block holds a record; a longer name whose
   block is empty returns none (and `ANIMDATA_Lookup` takes the fallback). The loop also fails fatally on a record
   name longer than 8 (0x0066A94D–0x0066A957), which no stock record has. The compare is of the first two dwords of
   the 8-byte buffers, bytes after the NUL included (read
   from the code; no stock name leaves room for such bytes). The run's `find:long` cases and the `namelen` control carry it.
2. **J3, line 660** (which branch a mode takes). The monster tables also give monster mode SQ (14) the skill-move and
   skill-attack flags, in both tables (`AnimRateIsMove` and `AnimRateIsAttack` decide it by the used skill, like
   S1–S4 from class 410); J3 does not list SQ for monsters. Below 410, S1–S4 carry the skill flags as well, but the
   move flag is tested first, so J3's "always moving" stands.
3. **J3, the predicates' other types.** `AnimRateIsMove` and `AnimRateIsAttack` fail fatally for a unit type other than
   0 or 1 (0x006214C5, 0x00621598); `AnimRateIsFixed`, `AnimRateIsCast` and the two mode tests 0x00621680 and
   0x006216B0 return 0. `AnimRateIsAttack`'s skill branch returns the masked byte (8), not 1.

*2026-11-16, S6e part 2 (`lane/n66l`):* two more for anim/timing B3 (line 183 at `b5999f5e`), from
run:2026-11-16-sweep2-s6e-2: (4) the gfxtype 2 map has the exception anim/0001 § 2 states and B3 omits: display class
6 in monster mode 4 takes player mode 12, not `g_MonToPlrMode[4]` (0x00645328–0x0064533E); (5) the fallback's steps
and the MonStats2 column names are now `[C]` (B3's second bullet can carry the tag). For anim/movement B6 (line 225):
a component of −4096 reaches −2³¹ at `v = 32 768` and wraps from 32 769 (0x00650336–0x00650345).
