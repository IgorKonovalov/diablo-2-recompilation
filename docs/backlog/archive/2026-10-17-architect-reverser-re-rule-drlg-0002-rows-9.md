---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../../plans/0039-backlog-sweep-4.md#implementation-log
resolution: "Re-ruled in [drlg/0002 § S4b](../../findings/drlg/0002-room-build-draws.md#plan-0038-batch-s4b-2026-10-16): row 20 [C] raised, row 9 raised in part ([C] fallback with no draw; fatal branch stays [I]); sweep_s4a.py pick re-run (1 280 fallbacks, 0 roomk mismatches over 36 logs)."
---

[2026-10-17] from architect → reverser: re-rule [drlg/0002](../../findings/drlg/0002-room-build-draws.md#plan-0038-batch-s4a-2026-10-16) rows 9 and 20 ([inventory drlg-room-tiles](../../plans/0038-inventory/drlg-room-tiles.md), spec L337 and L600). The S4b shortfall keeps them `[I]` because "showing that no stock key lacks a candidate needs the exact list of every room", but § S4a records the model taking the `(10, 0, 0)` fallback 1 280 times in the run:2026-10-14-collision and run:2026-10-15-objects logs, every room's k matched. So stock keys do lack candidates, and the fallback's no-draw half has a seed-checked second source. Re-rule both rows (the fatal branch stays as it is) and correct the shortfall bullet. Context: [plan 0039 log](../../plans/0039-backlog-sweep-4.md#implementation-log) (`lane/w1` review)
