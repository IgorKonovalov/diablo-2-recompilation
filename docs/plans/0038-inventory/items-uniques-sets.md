# Plan 0038 inventory: items/uniques-sets

Phase 0 of [plan 0038](../0038-inferred-claims-sweep.md), cluster (0a) items.

- **Spec:** [items/uniques-sets](../../specs/items/uniques-sets.md), status `reviewed`, read at commit `3b1433f` (on `main` at `e1c807a`).
  Front matter `I` = **52**; the *count* column below sums to 52.
- **Finding:** [items/0004](../../findings/items/0004-uniques-sets.md); run records in
  [findings/items/experiments.md](../../findings/items/experiments.md).
- **Columns.** *Section* links the spec section and lists the spec lines of the statements at that commit. *Anchor* is the
  finding number and the first code address of the statement. *Class*, *tier* and *batch* follow the plan's
  [Classes](../0038-inferred-claims-sweep.md#classes). A forced-run row is class `b` with a route that starts `forced:`.
  A `—` batch means the row is class (d) and no batch takes it.
- **Totals by class:** a-logs 23, a-run 3, b 1, c 4, d-edit 7, d-none 14.

| # | Section | Claim | Anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/items/uniques-sets.md#entry-points) (L54) | Vendors, gambling, cube, quests call the same builders | 0004 · `0x005566B0` | a-logs | vendors gamble windows and cube outputs reproduced by the same unique/set model | T2 | S2c | 1 |
| 2 | [Entry points](../../specs/items/uniques-sets.md#entry-points) (L59) | The cube changes the made set only through `reg` | 0004 · `0x00565AB0` | d-none | no stock CubeMain row has `reg` | T3 | — | 1 |
| 3 | [Tables](../../specs/items/uniques-sets.md#tables) (L86) | Nothing between entry and builder return reads ItemRatio | 0004 · `0x00637910` | c | full xref of g_pItemRatio and ITEMRATIO_Select | T1 | S2b | 1 |
| 4 | [Tables](../../specs/items/uniques-sets.md#tables) (L91) | The builder never reads carry1 or lvl req | 0004 · `0x00556895` | a-logs | uniques.py reproduces every candidate list without them | T1 | S2b | 1 |
| 5 | [Tables](../../specs/items/uniques-sets.md#tables) (L93) | No set level at run time | 0004 · `0x00634DC0` | c | loader read: sets.bin fields against SetItems.lvl reads | T3 | S2b | 1 |
| 6 | [Constants](../../specs/items/uniques-sets.md#constants) (L126) | SET_COW: set 29 only from a hellbovine source | 0004 · `0x005C264E` | a-logs | uniques.py over the cow session log (quests-s*-cows, 565 bovines): set builds with and without flag bit 0; else a-run (questcows) | T1 | S2b | 1 |
| 7 | [Inputs and oracles](../../specs/items/uniques-sets.md#inputs-and-oracles) (L150) | Superior and normal builders never reached from a failed unique or set | 0004 · `0x005C2AD0` | a-run | long items-chain hunt; failure chains need a failed rare after a failed unique | T3 | H2b | 1 |
| 8 | [Algorithm](../../specs/items/uniques-sets.md#algorithm) (L159) | Signed 32-bit arithmetic (header) | 0004 · `0x00557450` | a-logs | uniques.py check (every logged build) | T1 | S2b | 1 |
| 9 | [A. The item seed at entry](../../specs/items/uniques-sets.md#a-the-item-seed-at-entry) (L175) | Item seed at entry from two game-seed draws | 0004 · `0x00558D90` | a-logs | items-chain IC0/ICX lines and rng/seeds 7a; else b (log game.seed at ItemCreate) | T1 | S2b | 1 |
| 10 | [A. The item seed at entry](../../specs/items/uniques-sets.md#a-the-item-seed-at-entry) (L181) | Type 11 setup draws on the item seed first | 0004 · `0x0065E8E0` | a-run | items-chain session hunting a type-11 base (identify type 11 first) | T3 | H2b | 1 |
| 11 | [B. ItemCreateByQuality](../../specs/items/uniques-sets.md#b-itemcreatebyquality-the-creation-roll-the-overrides-and-the-switch) (L201) | B1: wrong unit type or no base returns 0 | 0004 · `0x00557450` | d-none | guard never fails | T3 | — | 1 |
| 12 | [B. ItemCreateByQuality](../../specs/items/uniques-sets.md#b-itemcreatebyquality-the-creation-roll-the-overrides-and-the-switch) (L202) | B2 clears auto affix, prefixes, suffixes, rare names | 0004 · `0x00557450` | a-logs | uniques.py/affixes model on every build | T1 | S2b | 1 |
| 13 | [B. ItemCreateByQuality](../../specs/items/uniques-sets.md#b-itemcreatebyquality-the-creation-roll-the-overrides-and-the-switch) (L207) | B4 overrides in order, writing item.quality only | 0004 · `0x005574E3` | a-logs | ICQ/ICJ lines: quality before and after the overrides | T1 | S2b | 1 |
| 14 | [B. ItemCreateByQuality](../../specs/items/uniques-sets.md#b-itemcreatebyquality-the-creation-roll-the-overrides-and-the-switch) (L226) | A later override wins; no ItemTypes record reads 0/0/1 | 0004 · `0x0062E9E0` | d-none | no observable on stock drops | T3 | — | 1 |
| 15 | [B. ItemCreateByQuality](../../specs/items/uniques-sets.md#b-itemcreatebyquality-the-creation-roll-the-overrides-and-the-switch) (L238) | On a drop no override changes the quality | 0004 · `0x005574E3` | a-logs | ICQ/ICJ lines over every kept drop | T1 | S2b | 1 |
| 16 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L250) | C2: no base returns false | 0004 · `0x005566B0` | d-none | guard never fails | T3 | — | 1 |
| 17 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L264, L323, L522) | A `unique` base with no candidate builds with no row | 0004 · `0x00556942` | d-none | no TC reaches a `unique` base | T3 | — | 3 |
| 18 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L272, L356) | A named row is taken with no draw | 0004 · `0x005568FC` | d-edit | only TC-named forced data names a row (run:2026-10-15-uniques-tcnamed-forced) | T3 | — | 2 |
| 19 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L276) | C7 row range and code check | 0004 · `0x005569E4` | d-none | guard never fails with stock data | T3 | — | 1 |
| 20 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L281, L325) | The unique builder clears the identified flag | 0004 · `0x00556A23` | a-logs | item flags in the WR/BLD lines of the kept unique builds; else b | T1 | S2b | 2 |
| 21 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L290) | Version 0 and restore paths of the unique builder | 0004 · `0x005566DE` | b | restore path: Larzuk or Anya on a unique (questservices recipe with a unique) with uniques.py; version 0 is d-none | T2 | H6d | 1 |
| 22 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L294) | Five tests in order; GetItemLevel raises ilvl to 1 | 0004 · `0x00556895` | a-logs | uniques.py candidate lists | T1 | S2b | 1 |
| 23 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L300) | Label, nobase and disabled rows never reached | 0004 · `0x005568AA` | a-logs | uniques.py candidate lists never hold them | T1 | S2b | 1 |
| 24 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L305) | Candidates live in g_UniqueCandidates, 8-byte pairs | 0004 · `0x008846F8` | c | second reader of g_UniqueCandidates | T3 | S2b | 1 |
| 25 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L315) | A quest base skips the made test | 0004 · `0x00556530` | d-none | no quest base reaches the unique builder | T3 | — | 1 |
| 26 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L318) | Bound test admits row 4096 | 0004 · `0x005569AD` | d-none | stock has 402 rows | T3 | — | 1 |
| 27 | [C. The unique builder](../../specs/items/uniques-sets.md#c-the-unique-builder) (L320) | nolimit blank; nothing clears a made bit but game creation | 0004 · `0x00556530` | c | data check of `nolimit`; xref of every write to Game+0x1B24 | T1 | S2b | 1 |
| 28 | [D. The set builder](../../specs/items/uniques-sets.md#d-the-set-builder) (L344, L376) | Set 29 filtered by record flag bit 0 (hellbovine) | 0004 · `0x005C264E` | a-logs | as SET_COW (cow session log) | T1 | S2b | 2 |
| 29 | [D. The set builder](../../specs/items/uniques-sets.md#d-the-set-builder) (L357) | Set builder writes the file index and clears identified | 0004 · `0x005C270D` | a-logs | set builds in the kept logs (WR/BLD) | T1 | S2b | 1 |
| 30 | [D. The set builder](../../specs/items/uniques-sets.md#d-the-set-builder) (L365) | Version 0 set builder | 0004 · `0x005C2940` | d-none | no drop makes version 0 | T3 | — | 1 |
| 31 | [D. The set builder](../../specs/items/uniques-sets.md#d-the-set-builder) (L368) | Set test order; ilvl read once; 256-pair stack list | 0004 · `0x005C2630` | a-logs | uniques.py set candidate lists | T1 | S2b | 1 |
| 32 | [D. The set builder](../../specs/items/uniques-sets.md#d-the-set-builder) (L371) | Set items take their set's version; classic sees 16 classic sets | 0004 · `0x00634DC0` | a-logs | set builds in classic logs (affixesc-*, tc-quality-3) if any; else a-run (classic items-chain session) | T1 | S2b | 1 |
| 33 | [D. The set builder](../../specs/items/uniques-sets.md#d-the-set-builder) (L373) | No enabled, ladder or once-per-game test for sets | 0004 · `0x005C2630` | a-logs | repeated set rows in one game in the kept logs; else c (no such read) | T1 | S2b | 1 |
| 34 | [D. The set builder](../../specs/items/uniques-sets.md#d-the-set-builder) (L383) | The set builder does not consult uniqueMade | 0004 · `0x005C25C0` | a-logs | made-set check after set builds | T1 | S2b | 1 |
| 35 | [E. Failure](../../specs/items/uniques-sets.md#e-failure-durability-and-the-fallback-chain) (L439) | Fallback steps past the first; Rare 0 fails at once | 0004 · `0x00557320` | a-run | as the failure-chain row (H2b) | T3 | H2b | 1 |
| 36 | [E. Failure](../../specs/items/uniques-sets.md#e-failure-durability-and-the-fallback-chain) (L443) | ClearAffixes resets the file index; fallback writes rec.quality | 0004 · `0x00557250` | a-logs | stock failed-set and made-unique fallbacks in the kept logs | T1 | S2b | 1 |
| 37 | [F. A row named by the TC](../../specs/items/uniques-sets.md#f-a-row-named-by-the-tc) (L449, L452) | TC-named rows resolve by name and pass every test | 0004 · `0x00654440` | d-edit | only edited TC cells name a row | T3 | — | 2 |
| 38 | [F. A row named by the TC](../../specs/items/uniques-sets.md#f-a-row-named-by-the-tc) (L463, L470) | Duplicated names: first row wins; named rows still tested | 0004 · `0x006BD490` | d-edit | the forced logs agree, but the edited cells are the claim's own input (ADR-0010) | T3 | — | 2 |
| 39 | [Draw order on the item seed](../../specs/items/uniques-sets.md#draw-order-on-the-item-seed) (L511) | Game and unit seeds untouched from entry to builder return | 0004 · `0x00557450` | a-logs | items-chain seed lines around ItemCreateByQuality | T1 | S2b | 1 |
| 40 | [Outputs](../../specs/items/uniques-sets.md#outputs) (L529) | After the join: set items never ethereal, uniques can be | 0004 · `0x00556CA0` | a-logs | props ETH0/ETHX lines for set and unique items in the kept logs | T1 | S2b | 1 |
| 41 | [Reimplementation notes](../../specs/items/uniques-sets.md#reimplementation-notes) (L651) | A TC-named unique still needs enabled and lvl ≤ ilvl | 0004 · `0x005568AD` | d-edit | only edited TC cells | T3 | — | 1 |
| 42 | [Reimplementation notes](../../specs/items/uniques-sets.md#reimplementation-notes) (L652) | Set items: version from their set; no enabled or once-per-game test | 0004 · `0x005C2630` | a-logs | as the set rows above | T1 | S2b | 1 |
| 43 | [Reimplementation notes](../../specs/items/uniques-sets.md#reimplementation-notes) (L654) | lvl comparisons are signed 16-bit | 0004 · `0x005568E3` | d-none | no stock `lvl` beyond 16 bits | T3 | — | 1 |
| 44 | [Reimplementation notes](../../specs/items/uniques-sets.md#reimplementation-notes) (L661) | Set weight 0 counts as 1, negative kept | 0004 · `0x005C26B6` | d-none | stock weights are 1, 3 and 7 | T3 | — | 1 |
| 45 | [Reimplementation notes](../../specs/items/uniques-sets.md#reimplementation-notes) (L663) | Item version 0 builds by other rules | 0004 · `0x005566DE` | d-none | no drop makes version 0 | T3 | — | 1 |
