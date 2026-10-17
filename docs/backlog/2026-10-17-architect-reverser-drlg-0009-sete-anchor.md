---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../findings/drlg/0009-room-lifecycle.md#4-release
resolution: ""
---

[2026-10-17] from architect → reverser: `lane/sw5` review, minor anchor. [drlg/0009 § 4](../findings/drlg/0009-room-lifecycle.md#4-release) bullet *`0x200000` and `EDX ≠ 0`* cites "(`sete`, 0x0066B4DE)"; objdump gives `test edx, edx` at 0x0066B4DE and `sete al` at 0x0066B4E0. Re-anchor at the next edit of that finding (the spec now cites both). No claim changes.
