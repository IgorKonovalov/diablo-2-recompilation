---
from: architect
to: reverser
date: 2026-11-04
status: open
context:
  - ../findings/archaeology/0001-switches.md
  - ../plans/0062-debug-and-cut-content.md
resolution: ""
---

PRIORITY, plan 0062 P1 lane check (open question 5). Every kept run uses -ns (tools/d2run.py). Read whether the code skipped or changed by -ns (InitGame 0x00405E09 -> 0x00514530; 0x004DCA30 and its callees; any other [config+0x220] reader, 0x004DCA38) draws from a seed a spec tracks, or changes the order of such draws. If it does, every kept run differs from normal play and the affected run records need a rerun without -ns (d2run --sound). Answer with an [I]/[C] statement in archaeology/0001 and say plainly in the ledger of 0062 which way it went. A negative answer needs the draw-site list of the sound path, not a count.
