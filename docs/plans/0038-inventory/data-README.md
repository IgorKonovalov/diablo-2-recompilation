# Plan 0038 inventory: data/README (data/overview)

- **Spec:** [data/README.md](../../specs/data/README.md), status `reviewed`, read at `main` `e1c807a`; front-matter `I` = **5**, the *Count* column sums to 5.
- **Cluster:** 0b (save, data and rng), architect lane, [plan 0038](../0038-inferred-claims-sweep.md) Phase 0.
- **Classes, tiers and batches:** as defined in the plan. *Route* names the recipe and logger, the new piece, the second source, or the `d-` reason. Batch `—` = not batched (class d).

Every `[I]` statement of the spec. The four entry-point rows are the startup loaders of data/excel § A–D.

## Totals

| Class | Count |
|---|---|
| (a-logs) | 1 |
| (b) | 4 |
| **total** | **5** |

## Rows

| # | Spec section | Claim | Finding | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Data flow](../../specs/data/README.md#data-flow), l. 50 | MPQ priority patch_d2 > d2exp > d2data; loose files only under `-direct` | [data/0002](../../findings/data/0002-mpq-precedence.md) | (a-logs) | as data/excel § A: the precedence re-check plus the `-direct` kept logs (d2sio-5, `-forced` runs); the no-`-direct` half joins H3b if the review splits it | T2 | S1b | 1 |
| 2 | [Entry points](../../specs/data/README.md#entry-points), l. 62 | Archives opened at startup, before the excel load | [data/0002](../../findings/data/0002-mpq-precedence.md) | (b) | **new** `excel`/startup logger (H3b): game started under gdb before the loaders; needs a `d2run.py` start mode, else reclass d-none | T2 | H3b | 1 |
| 3 | [Entry points](../../specs/data/README.md#entry-points), l. 63 | DATATBLS_LoadAll loads every table in a fixed sequence | [data/0001](../../findings/data/0001-excel-loader.md) | (b) | **new** `excel`/startup logger (H3b): game started under gdb before the loaders; needs a `d2run.py` start mode, else reclass d-none | T2 | H3b | 1 |
| 4 | [Entry points](../../specs/data/README.md#entry-points), l. 64 | Item code resolved through ITEMS_GetByCode → EXCEL_FindCode | [data/0001](../../findings/data/0001-excel-loader.md) | (b) | `excel` logger: breakpoints during play (cube, vendor) | T2 | H3b | 1 |
| 5 | [Entry points](../../specs/data/README.md#entry-points), l. 65 | TC name resolved through TC_GetByName → EXCEL_FindName | [data/0001](../../findings/data/0001-excel-loader.md) | (b) | `excel` logger: breakpoints at load and in play | T2 | H3b | 1 |
