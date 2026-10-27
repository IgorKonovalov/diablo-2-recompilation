---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../findings/items/0009-vendors.md#plan-0038-batch-h6c-run2026-10-27-sweep-vendors
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (6). vendors 29 and 32 to d-2c; vendors 26 (S2c) raised; totals static 567, harness 511, blocked 429, deferred 2, raised 17: 1 526 against main a105ae13; items/vendors Phase 3 ready (plan 0038 log, inventory § 2.6 H6c block)."
---

[2026-10-27] from reverser → architect: please review `lane/h6c`, plan 0038 batch H6c (`vendors`, 13 statements of
items/vendors and the S2c pieces of vendors 22 and 26), run:2026-10-27-sweep-vendors.

- **Where:** [items/0009 § Plan 0038 batch H6c](../../findings/items/0009-vendors.md#plan-0038-batch-h6c-run2026-10-27-sweep-vendors)
  (the ledger), the run record in [items experiments](../../findings/items/experiments.md#run2026-10-27-sweep-vendors),
  the [inventory § 2.6 H6c block](../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews), the
  [plan log](../../plans/0038-inferred-claims-sweep.md#implementation-log).
- **Rerun:** from `/home/igor/Work/recompilcation-project-h6c`, the record's ten procedure commands, each under
  `systemd-run --user --scope -p MemoryMax=4G`; `manifest-run.sha256` (23 lines) and `manifest-shots.sha256` pass from
  `workspace/logs/h6c/`, `manifest-dev.sha256` from `workspace/logs/h6c/dev/`.
- **Ledger: raised 7, raised in part 2, shortfall 4** (13). No class move filed. Proposed: vendors 29 and 32 → d-2c;
  vendors 26 (S2c) → raised. Totals against `main` `ffa5b957` (merged): static 567, harness 513, c-emu 0, blocked
  427, deferred 2, raised 17: 1 526.
- **Corrections and refinements for Phase 3:** vend 14 (Asheara's hirelings come first at the interaction start; the
  trade-first order is never taken), vend 2 (the row is a player unit's free with an interaction open), vend 5 (the
  32-failure test sits after normal copies and permanent items only).
- **Points to rule on:** (a) vend 2 rests on two `PLEAVE`s of run:2026-10-20-two-clients's kept host logs (rescanned,
  manifest checked) plus this run's single-player `PIEND` without one; (b) the d-2c reasons of 29 and 32
  (0x00572FAF), read, with every single-player close logged as a cancel; (c) the built states (clvl 1 with every quest
  done, the experience one point short, clvl 99, clvl 19 in Nightmare), ADR-0013 § Neutral, backing only the code
  that reads them; (d) the `tools/vendors.py` branch for an `ITEMS_CreateForStore` call outside a build (4 gold piles
  at 0x0055A18D), with run:2026-10-15-vendors's regression unchanged; (e) the `larz` session's death at the first
  in-act waypoint (kept for its build and reset only).
- **Symbols:** `VENDOR_IsPermanent`, `sub_00576F50_StoreItemSold`, `sub_0062E880_ItemStorePage` I → C; new
  `sub_00554120_PlayerSetInteract`, `sub_00554190_PlayerClearInteract` (I).
- **Note:** after the merge of `main`, `tools/test_d2s.py`'s recipe-list test fails on the 134 `anim-*` recipes main
  added (plan 0050) without `RECIPE_BASES` rows; this lane's four `vend-h6c-*` rows are present and build.
- The S2c harness-pieces entry is annotated (every piece has now run) and can close at this review.
