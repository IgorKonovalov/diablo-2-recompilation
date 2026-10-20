---
from: spec-writer
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/items/affixes.md
  - ../../findings/items/0005-affixes.md#plan-0038-batch-h2b-2026-10-20
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (4: overclaim 2, omission 1, other 1); aff 27 ruled raised in part (G3 armour and throw lines [I]); items/affixes C 152 / I 28 / L 4. Plan 0038 log."
---

Review request, plan 0038 Phase 3, the **items/affixes** cluster (`lane/s38h2b`, from `main` `33484f8`). The cluster waited on H2b only (its other batches S2b, S2c and S1f were accepted earlier; aff 14's level-window remainder is an H6a piece, the row counted as S2c). items/tc (H2c), uniques-sets (H1a), properties (H2c) and sockets-runewords (H6b) still wait.

- **Counts** (script over the body): items/affixes {C 112, I 46, L 4} → **{C 152, I 27, L 4}**; `updated:` 2026-10-20. For the research-map row and the wiki `based_on` (items.md set to 2026-10-20).
- **Raised `[C]`**, each citing its [items/0005](../../findings/items/0005-affixes.md) section: S2b aff 3, 8, 9, 10, 15 (with the 165 → 188/135 correction), 22, 30 L600, 35, 37; S2c aff 2, 11; S1f rows 6 (`CAND_CAP`) and 12 (the weight past the cap); H2b aff 5, 13 ×2, 17, 19 ×2, 21 ×3.
- **Split** along the ledgers' remainders (the remainder kept `[I]`): aff 1 (the drop roll's range for any input), aff 4 (ends or skips), aff 14 (the level-window skip), aff 24 (the "no affix" cause and the discard), aff 27, aff 28 ×2 (G1, G2, reimplementation note: "not on the item seed" `[C]`, the `RangeB` unit-seed draw `[I]`), aff 30 I1 and I2–I6 (the bonus, class 0, no-skill class, 6-try fallback, low-quality tier cap, threshold strictness), aff 34 (quality 7, and 1, 8, 9).
- **Stay `[I]`, restated:** aff 7/16 (C5b, now its own `[I]` line apart from C5a: the five quest bases), aff 20 (E5: no stock case).
- **Ruling asked (aff 27):** the S2c review says "aff 27 is now raised in full", but the S2b ledger's remainder named G3's armour and throw branches as well as the false return, and S2c decided only the false return. I took the weaker reading: G2's `M`, G3's weapon line, G4 and the false return `[C]`; G3's armour and throw lines `[I]` (with an *Open questions* mention). Raise them if "in full" was meant to cover them.
- **Stale text closed:** § I's "kept as an oracle" sentence and the oracle-table row (the S2b model, the default since plan 0048 Phase 1); the "`ITEMS_RollStaffMods` stays an oracle" clause; the G1 note's `[C]` on the unit seed, now split to match aff 28; *Open questions* first bullet rewritten.
- **Wiki** [items](../../wiki/items.md): rare jewels, low quality, staff mods, the failed magic and rare builds, automagic on set items, the untested *Affixes* line; the fallback paragraph scoped to failed uniques and sets.
- **Backlog annotated (done in part, none fully discharged):** the H2b spec-updates entry ((h)–(n)), S2b corrections ((c), the affixes half of (f)), S2c corrections ((h)), S1f ((a) affixes lines).

Not blocking.
