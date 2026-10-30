---
from: architect
to: reverser
date: 2026-10-30
status: open
context:
  - ../findings/ai/0003-pool-b.md
  - ../tables/MonStats.md
resolution: ""
---

ai/0003 § 2.12 gives the vampire flee override parameter clamp(Run*100/Velocity - 100, 0, 120) without the guard 'only when Velocity > 0' that the 2026-10-30 readers request states. MonStats.md now carries the guard with a note that the finding lacks it. Confirm from the code at 0x005F4A70 and add it to § 2.12, or tell the archivist to drop it.
