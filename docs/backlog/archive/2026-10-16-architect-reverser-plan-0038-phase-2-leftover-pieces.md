---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: "Run in plan 0038 H1a's S1b session (run:2026-10-27-sweep-d2s-load, workspace/logs/h1a/h1a-s2-27210-s1b.log): data-calc 19's hover half met (7 CH lines, 312 entries, 0 hover evaluations, 8 drink evaluations live in the window), rng-seeds 11's caller 0x00569F53 met for both player loads (seedtree 1 884/1 884), four callers still unrun; notes in [data/0005](../../findings/data/0005-calc.md#plan-0038-batch-s1b-2026-10-16) and [rng/0002](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16); the rows stay S1b for the review"
---

[2026-10-16] from architect → reverser: plan 0038 Phase 2 leftover pieces from S1b (rows stay counted as S1b, raised in part): data-calc 19, a hover marker line in `calc.gdb` so that "hover evaluates nothing" can be checked (client caller 0x00486370); rng-seeds 11, a caller `ra` on `SUNITPRE` in `seed-tree.gdb`, with a character load and a re-seed in the session. Neither has an open harness batch; take them with the next session that loads either logger. data/README 1 and data-excel 30 went to H3b ([inventory § 5](../../plans/0038-inventory/README.md#harness-batches)). Context: [inventory § 2.6](../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews)

*2026-10-17 (reverser, `lane/rbs` static sweep):* skipped: needs harness; rides on the next plan 0038 harness session that loads calc.gdb or seed-tree.gdb (no open batch).

*2026-10-25 (reverser, `lane/p51r`, [plan 0051](../../plans/done/0051-backlog-sweep-6.md) Phase 1a, no slot):* **Both lines
written and tested off-slot; the session is assigned to plan 0038 H1a.**
- **data-calc 19, the hover marker.** `tools/gdb/calc.py` writes a `CH` line at the entry of the client function
  `0x00486370` (its one call is at `0x0048E978`), with the return address, the stack argument, EDI and, when EDI is
  not 0, EDI's byte `+0xB4`, word `+0xB6` and dword `+0xA4`. Only a change of (argument, EDI) writes a line, and `"n"`
  counts the folded entries, because the function runs once per drawn frame. `CALC_HOVER=0` leaves the marker out. The
  objdump scan of the pinned image finds three `ITEMS_EvalCalc` calls inside the function, at `0x0048642F`,
  `0x004864D0` and `0x00486506`, so an evaluation that hovering causes is a `CE` line whose `ra2` is `0x00486434`,
  `0x004864D5` or `0x0048650B`. `tools/calc.py hover <log>` counts those lines and the `CH` lines.
- **rng-seeds 11, the caller.** The `SUNITPRE` line of `tools/gdb/seed-tree-core.gdb` (sourced by `seed-tree.gdb` and
  `sweep-roomk.gdb`) gains `ra=` from `[EBP+4]`: `0x00552DF0` sets up its frame at its first two instructions, and the
  line sits at `0x00552E2F`. `tools/rng.py seedtree` prints a "server unit caller" line for each one. It names the call
  among the six direct calls of `0x00552DF0` in the objdump scan, by return address, and says when a return address is
  not one of the six or is not logged. None of the six calls is named by its function in the checker.
- **Tests** (`python3 -I tools/test_p51_staging.py`, 9 tests OK; outputs `workspace/logs/p51r/`, manifest
  `manifest.sha256`): gdb parses and arms both loggers against the pinned image with no process. The call sites are
  re-derived from objdump. On synthetic logs, the hover and caller counts come out as expected. On a kept
  run:2026-10-16-calc log with `CH` lines added, `calc.py check` writes the same `SURVEY` line as without them. On the
  11 kept run:2026-10-11 seed-tree logs, `rng.py seedtree` gives the same totals as `main`'s checker. Over the 14 kept
  run:2026-10-16-calc logs, `calc.py hover` reports no marker (those logs predate it), no evaluation from `0x00486370`,
  and all 56 itemscode evaluations from the drink sites `0x005BEE04`/`0x005BEF16` (`calc-hover-kept.txt`). That is a
  dry run and decides nothing.
- **Session, staged:** `tools/gdb/s1b-pieces.gdb` (`seed-tree-core.gdb` + `calc.py`) with
  `tools/gdb/s1b-pieces.steps`, which loads CalcSor (`tools/d2s_recipes/calc-sor.json`), rests the pointer off every
  item and then on each of seven potions, drinks three, saves and exits, and loads the same character again (a second
  game: the re-seed and the second load).
- **Assigned to H1a**, one extra session. No open batch of [inventory § 5](../../plans/0038-inventory/README.md#harness-batches)
  loads `calc.gdb` or `seed-tree.gdb`: H1a and H1b use `d2s-io.gdb`, H3b a new startup logger, H4a `mon-h4a.gdb`, H5d
  `collision.gdb`, and H6a–H6g and H7a their own loggers. H5c, the last batch with `seed-tree.gdb`, is done. H1a loads
  characters. Checks on the session's log: `rng.py seedtree`, `calc.py hover`, `calc.py check`. The rows stay
  counted as S1b. The entry stays open until H1a's session.
