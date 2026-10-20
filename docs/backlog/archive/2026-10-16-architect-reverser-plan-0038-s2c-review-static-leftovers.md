---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../../findings/items/0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16
resolution: "2026-10-20 (lane/p49r, plan 0049 P1): all 45 register sites and the 12 steps clears are traced (tools/sweep_p49r.py qsites, kept). qd 10: no other bit-15 write on a player record. qd 19: no write of word 14 bits 1 or 5 other than the sets. qd 8: word 41 is object 1's +0xE4 word, and word 32 has one write (bit 0, 0x005BD2AB). See [items/0010 § Plan 0049 Phase 1](../../findings/items/0010-quest-drops.md#plan-0049-phase-1-2026-10-20-static-the-s2c-static-leftovers). quests/0001 § 1's act sections agree with it."
---

[2026-10-16] from architect → reverser: plan 0038 S2c review, static leftovers (the rows stay counted as S2c, raised in part). Trace the 45 `QUESTRECORD_SetState`/`ClearState` call sites that take the word or the bit from a register (the scripts' `Quest+0xE0` words, ten with a computed bit) and the 12 callers of the range clear `0x0065C3E0` (bits 2–11). This decides the remainders of quest-drops 10 ("only word 9 clears bit 15"), 19 ("Duriel's bit 5 is never cleared, his bit 1 never set") and 8 (what words 32 and 41 hold for objects 28 and 30 beyond the join path). Static, no slot; it can ride the next static batch that reads quest code (S3b or a backlog sweep under plan 0039). Context: [items/0010 § Plan 0038 batch S2c](../../findings/items/0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16)
