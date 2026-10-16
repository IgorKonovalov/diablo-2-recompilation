# Plan 0038 inventory: rng (rng/core)

- **Spec:** [rng/README.md](../../specs/rng/README.md), status `reviewed`, read at `main` `e1c807a`; front-matter `I` = **8**, the *Count* column sums to 8.
- **Cluster:** 0b (save, data and rng), architect lane, [plan 0038](../0038-inferred-claims-sweep.md) Phase 0.
- **Classes, tiers and batches:** as defined in the plan. *Route* names the recipe and logger, the new piece, the second source, or the `d-` reason. Batch `—` = not batched (class d).

Every `[I]` statement of the spec in file order. Three of the eight concern the dead `RangePow2Plus`.

## Totals

| Class | Count |
|---|---|
| (a-logs) | 1 |
| (c) | 5 |
| d-none | 2 |
| **total** | **8** |

## Rows

| # | Spec section | Claim | Finding | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/rng/README.md#entry-points), l. 31 | RangePow2Plus has no callers: dead code | [rng/0001](../../findings/rng/0001-rng-core.md) | d-none | dead code: no observable | T3 | — | 1 |
| 2 | [Entry points](../../specs/rng/README.md#entry-points), l. 34, 38 | 852 multiplier immediates, all inside functions (837 + 4 + 11) | [rng/0001](../../findings/rng/0001-rng-core.md) | (c) | independent second scan: r2 `/x c590c66a` against Ghidra function bounds and the `tools/gdb/lcg-sites.txt` list | T1 | S1b | 2 |
| 3 | [Entry points](../../specs/rng/README.md#entry-points), l. 43 | RangePow2Plus: seed ECX, base EDX, n on the stack | [rng/0001](../../findings/rng/0001-rng-core.md) | (c) | rule 4 emu: `tools/ghidra.sh emu 0x00472240` (EmuFastcall extended for the stack argument) vs `tools/rng.py`; addendum to run:2026-10-11-rng-emu | T3 | S1e | 1 |
| 4 | [Tables](../../specs/rng/README.md#tables), l. 49 | The RNG reads no table | [rng/0001](../../findings/rng/0001-rng-core.md) | (a-logs) | run:2026-10-11-rng-emu ran every primitive in the emulator with no data tables mapped (5 000 cases); addendum | T1 | S1b | 1 |
| 5 | [Algorithm](../../specs/rng/README.md#algorithm), l. 101 | RangePow2Plus = (low & (n − 1)) + base after one step | [rng/0001](../../findings/rng/0001-rng-core.md) | (c) | rule 4 emu: `tools/ghidra.sh emu 0x00472240` (EmuFastcall extended for the stack argument) vs `tools/rng.py`; addendum to run:2026-10-11-rng-emu | T3 | S1e | 1 |
| 6 | [Algorithm](../../specs/rng/README.md#algorithm), l. 120 | RangePow2Plus is dead; no spec depends on it | [rng/0001](../../findings/rng/0001-rng-core.md) | d-none | dead code: no observable | T3 | — | 1 |
| 7 | [Reimplementation notes](../../specs/rng/README.md#reimplementation-notes), l. 161 | Inlined constant-modulus draws and RangePow2 are unguarded | [rng/0001](../../findings/rng/0001-rng-core.md) | (c) | second source: rng/seeds 3c unguarded `mod 7` `[C]` (run:2026-10-11-seed-tree) and step 3 `RangePow2` `[C]`; cite | T1 | S1b | 1 |
