---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/data/excel.md
  - ../specs/data/strings.md
  - ../specs/data/README.md
resolution: ""
---

Plan 0038 Phase 3 (`lane/s38d`), the **data/excel**, **data/strings** and **data/README** clusters: old and new
`{C, I, L}` for the research-map rows and the wiki's `based_on` dates (gate W4).

| Spec | Old | New | `updated:` |
|---|---|---|---|
| [data/README](../specs/data/README.md) (data/overview) | {C 3, I 5, L 0} | **{C 9, I 2, L 0}** | 2026-10-16 → 2026-10-27 |
| [data/excel](../specs/data/excel.md) | {C 42, I 100, L 8} | **{C 144, I 45, L 2}** | 2026-10-15 → 2026-10-27 |
| [data/strings](../specs/data/strings.md) | {C 60, I 42, L 3} | **{C 88, I 29, L 3}** | 2026-10-17 → 2026-10-27 |

- **Research map:** the data/excel and data/strings rows still give the H3b-ready notes and the old counts; the map has
  no data/README row of its own (data/overview). Rewrite the rows whole (spec-writer rule 6).
- **Wiki (W4, done on this lane):** [wiki/game-data](../wiki/game-data.md) `based_on` dates set to 2026-10-27 for the three
  specs, and its stale paragraphs restated (archive lookup and loose files, `-txt`, the mixed-archive tables, the
  lookups, the TC loader and auto TCs, monster positions, the language byte and `CYR`, the fallbacks, entry 0, `Lilith`,
  rare names, gems, the worked example's 5382 row, *What is not known yet*).
- **Not reflected, with the reason:** none of the clusters' accepted raises is left out. Kept `[I]` as the ledgers rule:
  the d-none and d-edit rows (data-excel 15, 22, 32, 39's "never fires", 43, 44, 54, 58, 59, 70, 79, 80; data-strings 7,
  8, 9, 13, 15, 18, 19, 23, 26–28, 30, 34, 36) and the remainders the batch sections name (raised in part).
