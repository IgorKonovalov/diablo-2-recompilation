---
from: spec-writer
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../plans/0066-inventory/README.md
resolution: "Tier A review: accept with fixes (3): misread 1, omission 2; plan 0066 log, Phase 3 stats/items cluster review"
---

Please review `lane/n66si`: plan 0066 Phase 3, the stats/items cluster (stats/aggregate, stats/states, stats/README,
items/economy, items/use, items/inventory; batches S4a–S4e). Tier A. Blocking the cluster's merge.

Worth checking:

1. The six inventory files' new *Phase 3* lines partition their rows (aggregate 42, states 54, stats/README 3, economy
   86, use 64, inventory 101; 350 in all: whole 122, split 70, corrected 6, kept 152), and § 6's six rows match each
   spec's front matter.
2. The six corrected rows against their findings: aggregate 20 (F2's floor, stats/0001 § 11) and 42 (the 136 note,
   stats/experiments § S4d part 2), states 5 (A2's unit types, § S4d part 2), economy 40 (F1's 12 crossbows and
   `7cr`, items/0011 § 5) and 46 (`D2S_WriteCorpses`' arguments, items/0013 § 19 and the Tier B note in items/0011),
   inventory 60 (the `0x22` return 3, items/0013 § 1).
3. The emulation raises from run:2026-11-16-sweep2-s4e-emu: the price core (economy B–H), the take test and ops
   (aggregate C5, D1, F2), the request handlers, pickup, belt and stack paths (use, inventory §§ C–H), and each scope
   at its declared boundary.
4. The overclaim splits against filed raises (judgment call 1 in the plan log) and economy 78 raised past its S4a route
   on row 11's emulation (judgment call 3).
5. Quirks: Q369, Q490, Q514 to `[C]`; Q391 reworded to the act clock pass and `[C]`; Q49 kept `[I]`.
6. The owner's note on the move conventions of inventory 61, states 46 and aggregate 41: left as filed, recorded in
   the log entry and in the inventory lines.

Gate fast and `--full` green at the commit; `tools/quirks.py check` 0 errors. Judgment calls are in the plan log entry.
