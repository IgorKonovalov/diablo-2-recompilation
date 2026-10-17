---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../findings/items/0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16
resolution: ""
---

[2026-10-16] from architect → reverser: plan 0038 S2c review, static leftovers (the rows stay counted as S2c, raised in part). Trace the 45 `QUESTRECORD_SetState`/`ClearState` call sites that take the word or the bit from a register (the scripts' `Quest+0xE0` words, ten with a computed bit) and the 12 callers of the range clear `0x0065C3E0` (bits 2–11). This decides the remainders of quest-drops 10 ("only word 9 clears bit 15"), 19 ("Duriel's bit 5 is never cleared, his bit 1 never set") and 8 (what words 32 and 41 hold for objects 28 and 30 beyond the join path). Static, no slot; it can ride the next static batch that reads quest code (S3b or a backlog sweep under plan 0039). Context: [items/0010 § Plan 0038 batch S2c](../findings/items/0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16)
