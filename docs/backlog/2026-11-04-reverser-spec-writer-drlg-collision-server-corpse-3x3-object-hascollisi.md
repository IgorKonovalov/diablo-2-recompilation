---
from: reverser
to: spec-writer
date: 2026-11-04
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

From lane/p54b ([path/0005](../findings/path/0005-grid-rules.md), [I], the next kept batch of plan 0054 is the hold-out, so write after its review). docs/specs/drlg/collision.md § F holds a reviewed [C] for the wrong copy. (1) Row "dead monster, deadCol 0: pattern 5 plus, 0x8000" and the state diagram's corpse0 hold for the client (0x004B05E3, 0x004B0A05); the server calls UnitCorpseColl(unit, 1) at 0x005A65D9, a 3x3 of 0x8000, mask and pattern unchanged, from mode 0 on, with no paired clear. The plus stays on the server only for a monster created or relocated dead (0x00555492, 0x00554B78). (2) § F's object row needs "marked while HasCollision[mode]" kept at every state change, with classes 374 and the waypoints as HasCollision 0. (3) New rows: the plan's target under flag 0x800 of any type (0x00649B25), the reserved landing of four skill starts (0x005D9123, 0x005D9EF8, 0x005DA5D5, 0x005CB902). The population pass is not affected as far as read: 0x8000 is in no spawn mask.
