# Plan 0038 inventory: rng/seeds

- **Spec:** [rng/seeds.md](../../specs/rng/seeds.md), status `reviewed`, read at `main` `e1c807a`; front-matter `I` = **17**, the *Count* column sums to 17.
- **Cluster:** 0b (save, data and rng), architect lane, [plan 0038](../0038-inferred-claims-sweep.md) Phase 0.
- **Classes, tiers and batches:** as defined in the plan. *Route* names the recipe and logger, the new piece, the second source, or the `d-` reason. Batch `—` = not batched (class d).

Every `[I]` statement of the spec in file order. The harness rows need logger lines added to `seed-tree.gdb`,
grouped as the proposed sub-batch **H5r** (record in `findings/rng/experiments.md`).

## Totals

| Class | Count |
|---|---|
| (a-logs) | 4 |
| (a-run) | 1 |
| (b) | 9 |
| (c) | 1 |
| d-none | 2 |
| **total** | **17** |

## Rows

| # | Spec section | Claim | Finding | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Constants](../../specs/rng/seeds.md#constants), l. 76 | No-override sentinel 0xFFFFFFFF is g_SeedOverride's initial value | [rng/0002](../../findings/rng/0002-seed-tree.md) | (c) | rule 1: the `.data` bytes at `0x00731004` and the compare in `GAME_InitSeeds` agree | T1 | S1b | 1 |
| 2 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 231 | Further act-seed draws inside DRLG_ActCreate are data-dependent | [rng/0002](../../findings/rng/0002-seed-tree.md) | (b) | `seed-tree.gdb` + `tools/rng.py seedtree`; **new** breakpoint on the act-seed steps of `LevelLinkBuild` (`0x00677493`–`0x006774F9`) and the Act III link code | T1 | H5r | 1 |
| 3 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 248 | DRLG room alloc dispatch by type; allocation only, no draw | [rng/0002](../../findings/rng/0002-seed-tree.md) | (a-logs) | run:2026-10-11-seed-tree: 3 102 room creations predicted with one level draw each; split the check by room type; addendum | T1 | S1b | 1 |
| 4 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 261 | Active-room flags: 4 if R+0x28 & 0x40000, else 1 if R+0x60 & 1 | [rng/0002](../../findings/rng/0002-seed-tree.md) | (b) | `seed-tree.gdb` + `tools/rng.py seedtree`; **new** log of `R[+0x28]`, `R[+0x60]` at step 6c | T1 | H5r | 1 |
| 5 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 282 | Client unit takes a room only when (x, y) ≠ (0, 0) | [rng/0002](../../findings/rng/0002-seed-tree.md) | (b) | `seed-tree.gdb` + `tools/rng.py seedtree`; **new** log of the (x, y) arguments of `UnitInit` | T3 | H5r | 1 |
| 6 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 303 | Seed ≥ 2^31 given as negative decimal; atol above 2^31−1 unchecked | [rng/0002](../../findings/rng/0002-seed-tree.md) | (a-run) | `seed-tree.gdb` + `tools/rng.py seedtree`; one session with `-seed -2147483648` (and `-seed 2147483648` for the CRT question) | T3 | H5r | 1 |
| 7 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 312 | Act seed stepped only by LevelLinkBuild (level 6, link 1/3) and Act III | [rng/0002](../../findings/rng/0002-seed-tree.md) | (b) | as the act-seed row above | T1 | H5r | 1 |
| 8 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 325 | Six callers create a level only if absent from the act | [rng/0002](../../findings/rng/0002-seed-tree.md) | (b) | `seed-tree.gdb` + `tools/rng.py seedtree`; **new** caller `ra` on the `LEVEL` line | T1 | H5r | 1 |
| 9 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 339 | T+0x18/T+0x20 are wall/floor counts; 6c draws iff tiles | [rng/0002](../../findings/rng/0002-seed-tree.md) | (b) | `seed-tree.gdb` + `tools/rng.py seedtree`; **new** log of `T[+0x18]`/`T[+0x20]` with the room's built tile counts (`drlg-roomk` logger) | T1 | H5r | 1 |
| 10 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 344 | flags bit 0 marks populated; population pass skips it | [rng/0002](../../findings/rng/0002-seed-tree.md) | (b) | `seed-tree.gdb` + `tools/rng.py seedtree`; **new** log of `flags` at `0x0052D1C9`; needs a room with bit 0 set | T1 | H5r | 1 |
| 11 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 362 | Five other UnitSeedInit callers pass game+0xD0 | [rng/0002](../../findings/rng/0002-seed-tree.md) | (a-logs) | run:2026-10-11-seed-tree-p1: 114 server unit seeds with parent `game+0xD0`; split by caller where logged, callers not hit → H5r | T1 | S1b | 1 |
| 12 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 372 | Draw counts of object regions, unit proxies, quests before draw 5 | [rng/0002](../../findings/rng/0002-seed-tree.md) | (b) | `seed-tree.gdb` + `tools/rng.py seedtree`; **new** log of each game-seed step with `ra` during `GameCreate` | T1 | H5r | 1 |
| 13 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 383 | Null parent: UnitSeedInit uses RNG_EntropySeed, non-reproducible | [rng/0002](../../findings/rng/0002-seed-tree.md) | d-none | no stock path seen to pass a null parent; non-reproducible by design | T3 | — | 1 |
| 14 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 389 | ClientRoomAt (0, 0) gives no room; seed stays {1, 666} | [rng/0002](../../findings/rng/0002-seed-tree.md) | (b) | as the client (x, y) row | T3 | H5r | 1 |
| 15 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 390 | Client type 4 draws nothing before the room draw | [rng/0002](../../findings/rng/0002-seed-tree.md) | (a-logs) | run:2026-10-11-seed-tree-p1: 739 client seeds predicted; confirm type-4 units among them; addendum | T3 | S1b | 1 |
| 16 | [Algorithm](../../specs/rng/seeds.md#algorithm), l. 392 | Client type 1 never goes through 0x00465FD0 | [rng/0002](../../findings/rng/0002-seed-tree.md) | (a-logs) | run:2026-10-11-seed-tree-p1: no type-1 unit among the logged `UnitInit` hits; addendum | T3 | S1b | 1 |
| 17 | [Reimplementation notes](../../specs/rng/seeds.md#reimplementation-notes), l. 448 | InitOne before Init is dead: no observable effect | [rng/0002](../../findings/rng/0002-seed-tree.md) | d-none | overwritten before any draw: no observable | T3 | — | 1 |
