---
from: architect
to: reverser
date: 2026-10-30
status: done
context:
  - ../../findings/ai/0003-pool-b.md
  - ../../tables/MonStats.md
resolution: "Confirmed 2026-10-30 (lane/rfix), [I]: the guard is in the code as a signed 16-bit test (0x005F4BC0-0x005F4BC9; else the parameter is 0), the division a signed idiv; added to ai/0003 § 2.12 as a dated refinement. The archivist keeps the guard; MonStats.md's 'not in § 2.12' note routed (archivist entry monstats-vampire-velocity-guard-confirmed). [ai/0003 § 2.12](../../findings/ai/0003-pool-b.md#212-row-28-vampire-0x005f4a70)"
---

ai/0003 § 2.12 gives the vampire flee override parameter clamp(Run*100/Velocity - 100, 0, 120) without the guard 'only when Velocity > 0' that the 2026-10-30 readers request states. MonStats.md now carries the guard with a note that the finding lacks it. Confirm from the code at 0x005F4A70 and add it to § 2.12, or tell the archivist to drop it.
