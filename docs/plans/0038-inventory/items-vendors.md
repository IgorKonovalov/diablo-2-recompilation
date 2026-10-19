# Plan 0038 inventory: items/vendors

Phase 0 of [plan 0038](../0038-inferred-claims-sweep.md), cluster (0a) items.

- **Spec:** [items/vendors](../../specs/items/vendors.md), status `reviewed`, read at commit `ac0f5c2` (on `main` at `e1c807a`).
  Front matter `I` = **37**; the *count* column below sums to 37.
- **Finding:** [items/0009](../../findings/items/0009-vendors.md); run records in
  [findings/items/experiments.md](../../findings/items/experiments.md).
- **Columns.** *Section* links the spec section and lists the spec lines of the statements at that commit. *Anchor* is the
  finding number and the first code address of the statement. *Class*, *tier* and *batch* follow the plan's
  [Classes](../0038-inferred-claims-sweep.md#classes). A forced-run row is class `b` with a route that starts `forced:`.
  A `—` batch means the row is class (d) and no batch takes it.
- **Totals by class:** a-logs 9, a-run 2, b 11, c 6, d-2c 5, d-sim 1, d-none 3.

| # | Section | Claim | Anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/items/vendors.md#entry-points) (L64) | TownPlayerRemove → NPCSTORE_ActStale | 0009 · `0x00537580` | d-2c | leaving ends a single-player game; needs a second client | T3 | — | 1 |
| 2 | [Entry points](../../specs/items/vendors.md#entry-points) (L66) | PlayerInteractEnd → NpcStorePlayerLeave | 0009 · `0x00555500` | b | vendors.gdb: log the call on closing the store; any vendor session | T2 | H6c | 1 |
| 3 | [Entry points](../../specs/items/vendors.md#entry-points) (L68) | NPC_MenuAction actions and class lists | 0009 · `0x00579D60` | c | data check: the class lists against MonStats interact rows and Npc.txt | T2 | S2c | 1 |
| 4 | [Entry points](../../specs/items/vendors.md#entry-points) (L73) | No quest code reaches VENDOR_BuildStock or NPCSTORE_Reset | 0009 · `0x00578BCB` | c | full xref (the five call sites) | T2 | S2c | 1 |
| 5 | [Constants](../../specs/items/vendors.md#constants) (L123, L368) | MAX_FAILS 32; never reached | 0009 · `0x00576980` | a-run | existing vendors recipe at the longest stock lists (Hell, Anya and Larzuk) | T3 | H6c | 2 |
| 6 | [Constants](../../specs/items/vendors.md#constants) (L125) | CRACKED_TRIES 5 | 0009 · `0x00576330` | d-none | stock is never low quality | T3 | — | 1 |
| 7 | [Constants](../../specs/items/vendors.md#constants) (L126) | 64 store records of 0x44 bytes | 0009 · `0x00536070` | c | second reader (NPCSTORE_FindRec) of the record array | T3 | S2c | 1 |
| 8 | [Constants](../../specs/items/vendors.md#constants) (L127) | NPC slot table: 43 entries of 8 bytes | 0009 · `0x00731184` | c | data read of g_NpcStoreTable against its readers | T3 | S2c | 1 |
| 9 | [A. Store records and the store seed…](../../specs/items/vendors.md#a-store-records-and-the-store-seed-game-creation) (L136) | A2 store records per MonStats interact row | 0009 · `0x00536070` | a-logs | vendors.py over the 94 builds: record per class | T2 | S2c | 1 |
| 10 | [A. Store records and the store seed…](../../specs/items/vendors.md#a-store-records-and-the-store-seed-game-creation) (L160) | One stock per NPC class per game, shared by every player | 0009 · `0x00535EA0` | d-2c | the shared part needs two clients | T2 | — | 1 |
| 11 | [A. Store records and the store seed…](../../specs/items/vendors.md#a-store-records-and-the-store-seed-game-creation) (L181) | Nihlathak's record names list 15; never built into stock | 0009 · `0x00536271` | c | code read of the trade class list (second path) | T3 | S2c | 1 |
| 12 | [C. When stock is built, reset and ma…](../../specs/items/vendors.md#c-when-stock-is-built-reset-and-marked-stale) (L256) | Reopening a built, non-stale store keeps the stock | 0009 · `0x00579430` | b | vendor plan: open the same store twice within 240 s | T2 | H6c | 1 |
| 13 | [C. When stock is built, reset and ma…](../../specs/items/vendors.md#c-when-stock-is-built-reset-and-marked-stale) (L258) | `sole` from the interaction list; two players keep stale stock | 0009 · `0x00579E08` | d-2c | needs two clients | T3 | — | 1 |
| 14 | [C. When stock is built, reset and ma…](../../specs/items/vendors.md#c-when-stock-is-built-reset-and-marked-stale) (L261) | Asheara: hire list first builds the hirelings first | 0009 · `0x00576770` | b | vendor plan: open Asheara's hire list before trade | T2 | H6c | 1 |
| 15 | [C. When stock is built, reset and ma…](../../specs/items/vendors.md#c-when-stock-is-built-reset-and-marked-stale) (L272) | Walking out of a town calls TownLevelLeave like a waypoint | 0009 · `0x005380D0` | b | vendor plan: walk out of town between two opens | T2 | H6c | 1 |
| 16 | [C. When stock is built, reset and ma…](../../specs/items/vendors.md#c-when-stock-is-built-reset-and-marked-stale) (L275) | Leaving the game from Acts I–IV marks stale; Harrogath missing | 0009 · `0x00537580` | d-2c | needs a second client to keep the game | T3 | — | 1 |
| 17 | [C. When stock is built, reset and ma…](../../specs/items/vendors.md#c-when-stock-is-built-reset-and-marked-stale) (L281) | Stale branch with townEmpty and an interactor; multiplayer | 0009 · `0x00537230` | d-2c | needs two clients | T3 | — | 1 |
| 18 | [C. When stock is built, reset and ma…](../../specs/items/vendors.md#c-when-stock-is-built-reset-and-marked-stale) (L284) | Town entry, quest event, reopen, level-up rebuild nothing | 0009 · `0x00570880` | b | vendor plan: open, level up (levelup-load steps), re-enter, open again | T2 | H6c | 1 |
| 19 | [D. The stock build (VENDOR_BuildStock)](../../specs/items/vendors.md#d-the-stock-build-vendor_buildstock) (L312) | D1 buildTick ← now | 0009 · `0x00576980` | a-logs | the [C] stale-test records of run:2026-10-15-vendors hold buildTick | T2 | S2c | 1 |
| 20 | [D. The stock build (VENDOR_BuildStock)](../../specs/items/vendors.md#d-the-stock-build-vendor_buildstock) (L370) | Stock is normal, superior or magic, never low | 0009 · `0x00576900` | a-logs | 9206 logged stock items: count qualities | T2 | S2c | 1 |
| 21 | [E. One stock item (VENDOR_CreateStoc…](../../specs/items/vendors.md#e-one-stock-item-vendor_createstockitem) (L412) | E2 two creation passes | 0009 · `0x00576330` | a-logs | vendors.py: first pass on every logged stock item | T2 | S2c | 1 |
| 22 | [E. One stock item (VENDOR_CreateStoc…](../../specs/items/vendors.md#e-one-stock-item-vendor_createstockitem) (L420) | E3 page from the item type's StorePage | 0009 · `0x0062E880` | a-logs | vendors.py tab per stock item (348 no-room cases) | T2 | S2c | 1 |
| 23 | [E. One stock item (VENDOR_CreateStoc…](../../specs/items/vendors.md#e-one-stock-item-vendor_createstockitem) (L444) | Neither retry reached | 0009 · `0x00576505` | d-none | stock is never low quality; no code mismatch | T3 | — | 1 |
| 24 | [E. One stock item (VENDOR_CreateStoc…](../../specs/items/vendors.md#e-one-stock-item-vendor_createstockitem) (L446) | Tab mapping; no type names `mag`; storepage.bin unread | 0009 · `0x0062E880` | c | data check over ItemTypes.StorePage | T2 | S2c | 1 |
| 25 | [E. One stock item (VENDOR_CreateStoc…](../../specs/items/vendors.md#e-one-stock-item-vendor_createstockitem) (L452) | Repair-all before placement makes no draw | 0009 · `0x005761C0` | a-logs | vendors.py draw counts per stock item | T2 | S2c | 1 |
| 26 | [F. The creation record (ITEMS_Create…](../../specs/items/vendors.md#f-the-creation-record-items_createforstore-and-the-item-seeds) (L458) | F1 zeroed creation record | 0009 · `0x00559CE0` | a-logs | vendors.py (every stock creation) | T2 | S2c | 1 |
| 27 | [F. The creation record (ITEMS_Create…](../../specs/items/vendors.md#f-the-creation-record-items_createforstore-and-the-item-seeds) (L466) | F3 stock items are identified | 0009 · `0x00559CE0` | a-logs | item flags in the vendors logs; else b | T2 | S2c | 1 |
| 28 | [G. Gambling (GAMBLE_BuildInv)](../../specs/items/vendors.md#g-gambling-gamble_buildinv) (L487) | Gamble table: level, item index, qsort, countUpTo | 0009 · `0x00638AE0` | a-logs | vendors.py reproduces 325 gamble windows from this list | T2 | S2c | 1 |
| 29 | [G. Gambling (GAMBLE_BuildInv)](../../specs/items/vendors.md#g-gambling-gamble_buildinv) (L598) | Gamble open builds only without an existing inventory | 0009 · `0x00578AE0` | b | vendor plan: open the gamble window twice in one interaction | T2 | H6c | 1 |
| 30 | [G. Gambling (GAMBLE_BuildInv)](../../specs/items/vendors.md#g-gambling-gamble_buildinv) (L607) | Gamble lvl clamped to 5..99 | 0009 · `0x00578877` | b | new vendor saves at clvl ≤ 9 and ≥ 96 (tool-built, ADR-0013 Neutral) | T2 | H6c | 1 |
| 31 | [G. Gambling (GAMBLE_BuildInv)](../../specs/items/vendors.md#g-gambling-gamble_buildinv) (L620) | Gamble creation failure leaves an empty slot; placement failure ends | 0009 · `0x00578790` | d-none | no stock failure | T3 | — | 1 |
| 32 | [H. Gamble refresh and purchases](../../specs/items/vendors.md#h-gamble-refresh-and-purchases) (L642) | Gamble inventory freed at interaction end; same items within one | 0009 · `0x00555500` | b | as the reopen row | T2 | H6c | 1 |
| 33 | [H. Gamble refresh and purchases](../../specs/items/vendors.md#h-gamble-refresh-and-purchases) (L647) | A purchase copies the item and creates no replacement | 0009 · `0x0055A2A0` | b | pilot `npc` buy action on a gamble item | T2 | H6c | 1 |
| 34 | [H. Gamble refresh and purchases](../../specs/items/vendors.md#h-gamble-refresh-and-purchases) (L650) | Bought stock removed unless permanent; sold items added unless excluded | 0009 · `0x0055F590` | b | pilot buy and sell actions | T2 | H6c | 1 |
| 35 | [I. Named only](../../specs/items/vendors.md#i-prices-and-repair) (L658) | Buy, sell, gamble prices and repair | 0009 · `0x0062FDC0` | d-sim | game economy, out of scope (ADR-0002, a later ADR-0014 phase) | T3 | — | 1 |
| 36 | [Reimplementation notes](../../specs/items/vendors.md#reimplementation-notes) (L762) | Stock level not clamped to 99 in Nightmare and Hell | 0009 · `0x00576890` | b | new vendor save at clvl 99 in Hell | T2 | H6c | 1 |
