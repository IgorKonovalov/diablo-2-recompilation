---
from: reverser
to: archivist
date: 2026-10-30
status: done
context:
  - ../../tables/MonStats.md
  - ../../findings/ai/0003-pool-b.md
resolution: "MonStats.md Readers named by the pool-B batch, Velocity/Run bullet, now carries the finding's guard wording (s16 test, truncating idiv) [ai/0003 § 2.12](../../findings/ai/0003-pool-b.md#212-row-28-vampire-0x005f4a70)"
---

MonStats.md § Readers named by the pool-B batch, the Velocity/Run bullet (line ~941), says the guard 'only when Velocity > 0' is not in ai/0003 § 2.12. It now is (lane/rfix, 2026-10-30): the code tests Velocity as a signed 16-bit value (test cx, cx; jle, 0x005F4BC0-0x005F4BC9) and passes 0 otherwise; the division is a signed idiv. Please replace the note with the finding's wording: p = Velocity > 0 ? clamp(Run*100/Velocity - 100, 0, 120) : 0 (s16 test, truncating division). Not blocking.
