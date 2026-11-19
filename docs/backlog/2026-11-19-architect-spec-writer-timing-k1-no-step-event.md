---
from: architect
to: spec-writer
date: 2026-11-19
status: open
context:
  - ../specs/anim/timing.md#k-breakpoints-derived
  - ../specs/anim/timing.md#e-the-schedule
resolution: ""
---

anim/timing K1 writes `N(r) ← n(r) − 1` with `n(r) = max(2, ⌈256 (F − S) / r⌉)`, while E2 writes `N = ⌈256 (F − S) / r⌉ − 1` and says that with no step (`r ≥ 256 (F − S)`) no frame event fires, not even frame S's. In the no-step case K1's form gives N = 1 and fires frame S at T + 1, which E1's loop (and tools/anim_rates.py sched_len) does not. State K1's N as E2's (`⌈256 (F − S) / r⌉ − 1`, or note the no-step exception). Found at the lane/x16a review (plan 0070 Phase 11 batch 3): the breakpoints widget followed K1 and fired an event in a one-step action; the widget and its twin now follow E2 and E1's loop.
