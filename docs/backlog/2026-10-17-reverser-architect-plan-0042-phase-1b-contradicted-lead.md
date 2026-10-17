---
from: reverser
to: architect
date: 2026-10-17
status: moved
context:
  - ../findings/quests/0002-travel.md#phase-1b-verdicts
resolution: "Moved to plan 0044 (its log, 2026-10-17, P1 case list). The verdicts now carry the condition that 0x005A5E50 is the hostility declaration (both stamps come from it alone)."
---

[2026-10-17] from reverser → architect: plan 0042 Phase 1b, **contradicted** lead src:arreat-summit-basics-travel ("a 10-second delay between declaring hostility and using a waypoint or town portal"): the waypoint packet waits 10 000 ms (`0x0054C5D0`), but the portal operate waits 5000 ms (`0x00584870`, against `0x0055B6C0`, whose stamp `0x0055B720` writes from `0x005A5E50`). Hostility needs two clients, so it is for plan 0044's harness, not a 0042 Phase 2 case. Context: [quests/0002 § Phase 1b verdicts](../findings/quests/0002-travel.md#phase-1b-verdicts)
