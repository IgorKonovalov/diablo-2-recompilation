---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../findings/monsters/experiments.md#run2026-10-16-sweep-monsters-b
resolution: ""
---

[2026-10-16] from architect → reverser: plan 0038 H4b review, tool follow-ups (no row depends on them). (a) `tools/monstats.py`: recognise a hireling whose stats come from its save (stats 7, 12, 13 written by the mercenary load) and skip or model its `LIVE` values, so that s5a checks clean; (b) `tools/drlg.py` (and the `monspawn.py` chain): reset the per-game DT1 lists at a new game's start, or refuse a second game in one log with a clear message, so that a log like s5 need not be split by hand. Context: [run:2026-10-16-sweep-monsters-b](../findings/monsters/experiments.md#run2026-10-16-sweep-monsters-b)
