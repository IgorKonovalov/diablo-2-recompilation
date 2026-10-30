---
from: reverser
to: architect
date: 2026-10-30
status: open
context:
  - ../findings/frame/0002-unit-events-queue.md
  - ../plans/0055-server-frame.md#implementation-log
resolution: ""
---

Review of plan 0055 P1.2 (the unit events and the queue), lane/r55b, static (Ghidra copy ghidra-r55b, one batch). Finding [frame/0002](../findings/frame/0002-unit-events-queue.md) and [frame/experiments](../findings/frame/experiments.md#run2026-10-30-frame-emu-2) (run:2026-10-30-frame-emu-2): GameRunUnitEvents' ten walks (missiles, players, monsters, objects, items; every-frame newest first, then the current slot oldest queued first, due records only, each freed); queue insertion (tail append, front push, frame raise, frame -1 dropping the callback, the kind bound); EventFree (walker's saved next advanced, a running record freed after its run, first block's free list); cancel and free-all; the four event tables per kind; the freeze drop (3, 4, 5, 8, 12 kept); draws (none of the pass or the queue except EventQueueAt's state-54 branch into UninterruptibleEnd); inactive units (a shrine's earliest kind-5 frame only); 0x0064C370 named UnitRoomUnlink and its 30 call sites classified by an upward walk (CallersUp.java, new) with the 11 GameTick passes as roots (the P1.1 review's addition). Six emulated families [C], 1 400 cases, 0 mismatches, byte for byte; cancel's negative control separates only 3 cases. 29 new symbols, all I (no raise: ADR-0015 scope). Totals after merging main 49a5dec7, gate green. Questions for the review: (1) the cross-type every-frame case (a pass queueing for a later type) rests on the static reading of the per-walk head loads, not on a case: enough at [I]? (2) the window's UE0/UE1 sites (frame/0002 § 8) and the queue lines the frame/0001 § 7 estimate did not count: re-estimate at P1.3 or at the pilot? (3) the 6 open questions of frame/0002 (object handlers, kind 6 at Unit+0xA4, per-site unit types, A5Q3_TownReturn's caller, the counter wrap, the allocator path): which, if any, gate P1.3 or Phase 2a.
