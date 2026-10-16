# Plan 0038 inventory: data/strings

- **Spec:** [data/strings.md](../../specs/data/strings.md), status `reviewed`, read at `main` `e1c807a`; front-matter `I` = **39**, the *Count* column sums to 39.
- **Cluster:** 0b (save, data and rng), architect lane, [plan 0038](../0038-inferred-claims-sweep.md) Phase 0.
- **Classes, tiers and batches:** as defined in the plan. *Route* names the recipe and logger, the new piece, the second source, or the `d-` reason. Batch `—` = not batched (class d).

Every `[I]` statement of the spec in file order. Most remaining `[I]` are fallbacks and fatal paths that a stock
LoD install (with `d2exp.mpq`, English tables) never reaches: `d-edit` when an edited or missing file or a
non-`eng` language reaches them, `d-none` when they guard a programming error. The two harness rows join the
proposed H3b data-loader batch; the plan's H6 lists data/strings, but its creation recipes do not reach these rows.

## Totals

| Class | Count |
|---|---|
| (a-logs) | 6 |
| (b) | 4 |
| d-edit | 20 |
| d-none | 9 |
| **total** | **39** |

## Rows

| # | Spec section | Claim | Finding | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/data/strings.md#entry-points), l. 43 | GetStringByKey is the text-only key lookup (0x00524E35) | [data/0003](../../findings/data/0003-string-tables.md) | (a-logs) | run:2026-10-15-strings kept logs: the 906 `SKEY` with `ra` `0x00524E35` behave as `GetByKey`; addendum | T2 | S1b | 1 |
| 2 | [Entry points](../../specs/data/strings.md#entry-points), l. 45 | Release by reference count through STRTABLE_Unload | [data/0003](../../findings/data/0003-string-tables.md) | (b) | `strings.gdb`; **new** breakpoint on `STRTABLE_Unload` (game exit) | T3 | H3b | 1 |
| 3 | [Entry points](../../specs/data/strings.md#entry-points), l. 50 | GetStringByKey is a thin key → text call | [data/0003](../../findings/data/0003-string-tables.md) | (a-logs) | as row 1 | T2 | S1b | 1 |
| 4 | [Constants](../../specs/data/strings.md#constants), l. 83 | Expansion index without expansionstring → 11078 | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs `d2exp.mpq` absent | T3 | — | 1 |
| 5 | [Constants](../../specs/data/strings.md#constants), l. 84 | Entry past count → 500 | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | only edited or foreign-language tables | T3 | — | 1 |
| 6 | [A. Loading — STRTABLE_LoadAll, STRTABLE_LoadFile](../../specs/data/strings.md#a-loading--strtable_loadall-strtable_loadfile), l. 114 | LoadAll: refcount, font map, three tables, UTF-16 conversion | [data/0003](../../findings/data/0003-string-tables.md) | (b) | **new** `excel`/startup logger (H3b, sources `strings.py`): game started under gdb before `STRTABLE_LoadAll`; needs a `d2run.py` start mode, else reclass d-none | T2 | H3b | 1 |
| 7 | [A. Loading — STRTABLE_LoadAll, STRTABLE_LoadFile](../../specs/data/strings.md#a-loading--strtable_loadall-strtable_loadfile), l. 127 | Node offset past file size is fatal at load | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | guards a corrupt file | T3 | — | 1 |
| 8 | [A. Loading — STRTABLE_LoadAll, STRTABLE_LoadFile](../../specs/data/strings.md#a-loading--strtable_loadall-strtable_loadfile), l. 128 | Missing file: header read faults, no `eng` fallback | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs a missing table file | T3 | — | 1 |
| 9 | [A. Loading — STRTABLE_LoadAll, STRTABLE_LoadFile](../../specs/data/strings.md#a-loading--strtable_loadall-strtable_loadfile), l. 143 | With d2exp.mpq a missing table crashes before the NULL tests | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs a missing table file | T3 | — | 1 |
| 10 | [B. Text conversion — UNICODE_Utf8ToUtf16](../../specs/data/strings.md#b-text-conversion--unicode_utf8toutf16), l. 163 | CharCount without a font map returns strlen | [data/0003](../../findings/data/0003-string-tables.md) | d-none | the font map always loads first in `LoadAll` | T3 | — | 1 |
| 11 | [B. Text conversion — UNICODE_Utf8ToUtf16](../../specs/data/strings.md#b-text-conversion--unicode_utf8toutf16), l. 180 | Font map layout; latin ranges make 0x7F–0x9F two-byte | [data/0003](../../findings/data/0003-string-tables.md) | (a-logs) | run:2026-10-15-strings kept logs: `CharCount` model over the latin map matched (key `\x7f\x02` lost two characters); addendum | T2 | S1b | 1 |
| 12 | [C. Index → text — STRTABLE_GetByIndex](../../specs/data/strings.md#c-index--text--strtable_getbyindex), l. 208 | Index ≥ 20000 unloaded expansionstring → 11078, not reached | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs `d2exp.mpq` absent | T3 | — | 1 |
| 13 | [C. Index → text — STRTABLE_GetByIndex](../../specs/data/strings.md#c-index--text--strtable_getbyindex), l. 210 | string not loaded at GetByIndex: fatal 0x246 | [data/0003](../../findings/data/0003-string-tables.md) | d-none | guards a programming error | T3 | — | 1 |
| 14 | [C. Index → text — STRTABLE_GetByIndex](../../specs/data/strings.md#c-index--text--strtable_getbyindex), l. 213 | Entry ≥ count → 500, not reached | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | only edited or foreign-language tables | T3 | — | 1 |
| 15 | [C. Index → text — STRTABLE_GetByIndex](../../specs/data/strings.md#c-index--text--strtable_getbyindex), l. 215 | Unused node or NULL text is fatal | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | guards a corrupt file | T3 | — | 1 |
| 16 | [C. Index → text — STRTABLE_GetByIndex](../../specs/data/strings.md#c-index--text--strtable_getbyindex), l. 226 | 11078 unreachable on stock; would land on patchstring 1078 | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs `d2exp.mpq` absent | T3 | — | 1 |
| 17 | [C. Index → text — STRTABLE_GetByIndex](../../specs/data/strings.md#c-index--text--strtable_getbyindex), l. 228 | Without patchstring, 10000–19999 falls back to entry 500 | [data/0003](../../findings/data/0003-string-tables.md) | d-none | `patchstring` is always loaded | T3 | — | 1 |
| 18 | [C. Index → text — STRTABLE_GetByIndex](../../specs/data/strings.md#c-index--text--strtable_getbyindex), l. 230 | Other languages show other text for one index | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs a non-`eng` language | T3 | — | 1 |
| 19 | [D. Key → index — STRTABLE_GetByKey](../../specs/data/strings.md#d-key--index--strtable_getbykey), l. 249, 250 | GetByKey fatals: tables not loaded, NULL key | [data/0003](../../findings/data/0003-string-tables.md) | d-none | guard a programming error | T3 | — | 2 |
| 20 | [D. Key → index — STRTABLE_GetByKey](../../specs/data/strings.md#d-key--index--strtable_getbykey), l. 271 | string entry 0 is indistinguishable from not found | [data/0003](../../findings/data/0003-string-tables.md) | d-none | no stock caller looks up `WarrivAct1IntroGossip1` by key | T3 | — | 1 |
| 21 | [D. Key → index — STRTABLE_GetByKey](../../specs/data/strings.md#d-key--index--strtable_getbykey), l. 286 | Gems keys miss; every gem stores 0 at +0x2C | [data/0003](../../findings/data/0003-string-tables.md) | (a-logs) | run:2026-10-15-strings kept logs: 136 `SKEY` from `0x0063721C` return 0, keys = gem record bytes `+0x28..+0x2A`; addendum | T3 | S1b | 1 |
| 22 | [D. Key → index — STRTABLE_GetByKey](../../specs/data/strings.md#d-key--index--strtable_getbykey), l. 294 | Rare names: load-time key into +0x0C; client shows index or raw name | [data/0003](../../findings/data/0003-string-tables.md) | (b) | `strings.gdb`; **new** pilot action: hover a rare item (`SIDX` from `0x0048C5C1`–`0x0048C726`); the load half is already in the kept logs (394 `SKEY` from `0x006341F4`) | T2 | H3b | 1 |
| 23 | [E. Hash probing — STRTABLE_FindInTable, STRTABLE_Hash](../../specs/data/strings.md#e-hash-probing--strtable_findintable-strtable_hash), l. 324 | Matched node with NULL text: fatal 0x296 | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | guards a corrupt file | T3 | — | 1 |
| 24 | [G. Index bases, fallbacks and fatal paths](../../specs/data/strings.md#g-index-bases-fallbacks-and-fatal-paths), l. 370 | Fallback table: index ≥ 20000 without expansionstring | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs `d2exp.mpq` absent | T3 | — | 1 |
| 25 | [G. Index bases, fallbacks and fatal paths](../../specs/data/strings.md#g-index-bases-fallbacks-and-fatal-paths), l. 371 | Fallback table: entry ≥ count | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | only edited or foreign-language tables | T3 | — | 1 |
| 26 | [G. Index bases, fallbacks and fatal paths](../../specs/data/strings.md#g-index-bases-fallbacks-and-fatal-paths), l. 376, 377, 378 | Fallback table: corrupt-file fatals | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | guard a corrupt file | T3 | — | 3 |
| 27 | [G. Index bases, fallbacks and fatal paths](../../specs/data/strings.md#g-index-bases-fallbacks-and-fatal-paths), l. 379 | Fallback table: programming-error fatals | [data/0003](../../findings/data/0003-string-tables.md) | d-none | guard a programming error | T3 | — | 1 |
| 28 | [G. Index bases, fallbacks and fatal paths](../../specs/data/strings.md#g-index-bases-fallbacks-and-fatal-paths), l. 380 | Fallback table: table file missing | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs a missing table file | T3 | — | 1 |
| 29 | [H. Language](../../specs/data/strings.md#h-language), l. 384 | Language code from first byte of `data\local\use` | [data/0003](../../findings/data/0003-string-tables.md) | (b) | **new** `excel`/startup logger (H3b, sources `strings.py`): game started under gdb before `STRTABLE_LoadAll`; needs a `d2run.py` start mode, else reclass d-none (`LNG_GetLanguageIndex`) | T3 | H3b | 1 |
| 30 | [H. Language](../../specs/data/strings.md#h-language), l. 390 | Non-`eng` languages would crash at expansionstring | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs a non-`eng` language | T3 | — | 1 |
| 31 | [Worked example](../../specs/data/strings.md#worked-example), l. 421 | Worked example index lookups other than the first row | [data/0003](../../findings/data/0003-string-tables.md) | (a-logs) | run:2026-10-15-strings kept logs: find the example indices among the 201 logged `SIDX`; those absent → H3b hover | T3 | S1b | 1 |
| 32 | [Reimplementation notes](../../specs/data/strings.md#reimplementation-notes), l. 445 | Edited tables: entry past count shows entry 500 | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | only edited tables | T3 | — | 1 |
| 33 | [Reimplementation notes](../../specs/data/strings.md#reimplementation-notes), l. 448 | Hash walk returns the first-inserted node of a key | [data/0003](../../findings/data/0003-string-tables.md) | (a-logs) | run:2026-10-15-strings kept logs: `not used` (duplicate key) resolved to entry 5384; check it is the first-inserted; addendum | T2 | S1b | 1 |
| 34 | [Reimplementation notes](../../specs/data/strings.md#reimplementation-notes), l. 455 | Other languages: other entries at the same position | [data/0003](../../findings/data/0003-string-tables.md) | d-edit | needs a non-`eng` language | T3 | — | 1 |
| 35 | [Reimplementation notes](../../specs/data/strings.md#reimplementation-notes), l. 456 | string entry 0 ≡ not found through GetByKey | [data/0003](../../findings/data/0003-string-tables.md) | d-none | no stock caller looks it up by key | T3 | — | 1 |
| 36 | [Open questions](../../specs/data/strings.md#open-questions), l. 477 | Meta: fallbacks and fatals stay `[I]` above | [data/0003](../../findings/data/0003-string-tables.md) | d-none | a tag in meta prose, not a claim (see the cluster issues) | T3 | — | 1 |
