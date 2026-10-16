# Plan 0038 inventory: items/quality

Phase 0 of [plan 0038](../0038-inferred-claims-sweep.md), cluster (0a) items.

- **Spec:** [items/quality](../../specs/items/quality.md), status `reviewed`, read at commit `f9f28e9` (on `main` at `e1c807a`).
  Front matter `I` = **36**; the *count* column below sums to 36.
- **Finding:** [items/0002](../../findings/items/0002-quality-roll.md); run records in
  [findings/items/experiments.md](../../findings/items/experiments.md).
- **Columns.** *Section* links the spec section and lists the spec lines of the statements at that commit. *Anchor* is the
  finding number and the first code address of the statement. *Class*, *tier* and *batch* follow the plan's
  [Classes](../0038-inferred-claims-sweep.md#classes). A forced-run row is class `b` with a route that starts `forced:`.
  A `—` batch means the row is class (d) and no batch takes it.
- **Totals by class:** a-logs 16, a-run 3, b 1, c 3, d-none 13.

| # | Section | Claim | Anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/items/quality.md#entry-points) (L42) | TC_ResolveDrops at 0x0055ADBA is the only call site of the drop roll | 0002 · `0x0055ADBA` | c | full xref of ITEMS_DropRollQuality | T1 | S2a | 1 |
| 2 | [Constants](../../specs/items/quality.md#constants) (L105) | mf ≤ −100 skips the unique, set, rare and magic tests | 0002 · `0x0055871F` | d-none | no stock source gives magic find ≤ −100 | T3 | — | 1 |
| 3 | [Constants](../../specs/items/quality.md#constants) (L106) | Fatal 0xE8D when no itemratio row matches | 0002 · `0x005586E6` | d-none | every stock (uber, class) pair has a row | T3 | — | 1 |
| 4 | [Constants](../../specs/items/quality.md#constants) (L107) | Fatal 0x61D for a version argument other than 0 or 100 | 0002 · `0x00637910` | d-none | callers pass only 0 or 100 | T3 | — | 1 |
| 5 | [Algorithm](../../specs/items/quality.md#algorithm) (L115) | Signed 32-bit arithmetic, truncating division, ×128 | 0002 · `0x00558640` | a-logs | quality.py over every QIN/QOUT of the kept logs (Normal to Hell, classic): count rolls | T1 | S2a | 1 |
| 6 | [A. Early returns (no draw, no row)](../../specs/items/quality.md#a-early-returns-no-draw-no-row) (L151) | No item record returns 0 | 0002 · `0x00558660` | d-none | a TC never names a missing item record | T3 | — | 1 |
| 7 | [A. Early returns (no draw, no row)](../../specs/items/quality.md#a-early-returns-no-draw-no-row) (L152) | The roll reads the item's own type | 0002 · `0x0055866B` | a-logs | quality.py replay (every roll) | T1 | S2a | 1 |
| 8 | [A. Early returns (no draw, no row)](../../specs/items/quality.md#a-early-returns-no-draw-no-row) (L156) | A base with `unique` returns 7 | 0002 · `0x005586AA` | d-none | no TC (auto TCs included) reaches the 18 `unique` bases | T3 | — | 1 |
| 9 | [A. Early returns (no draw, no row)](../../specs/items/quality.md#a-early-returns-no-draw-no-row) (L157) | A Magic type with a quest base returns 7 | 0002 · `0x005586B3` | d-none | `vip` is reachable from no TC | T3 | — | 1 |
| 10 | [A. Early returns (no draw, no row)](../../specs/items/quality.md#a-early-returns-no-draw-no-row) (L162) | A2–A5 read the own type, not type2 nor the Equiv chain | 0002 · `0x0055866B` | c | data check: bases whose type2/Equiv flags differ from their own type; if any is in the kept logs, a-logs | T3 | S2a | 1 |
| 11 | [A. Early returns (no draw, no row)](../../specs/items/quality.md#a-early-returns-no-draw-no-row) (L169) | Stock: 18 `unique` bases, `vip` the only Magic-plus-quest base; never taken | 0002 · `0x00558640` | c | data check over Weapons/Armor/Misc and the TC closure (rule 2) | T3 | S2a | 1 |
| 12 | [B. The itemratio row](../../specs/items/quality.md#b-the-itemratio-row--itemratio_select) (L186) | No itemratio row is fatal 0xE8D | 0002 · `0x005586E6` | d-none | unreachable with stock data | T3 | — | 1 |
| 13 | [B. The itemratio row](../../specs/items/quality.md#b-the-itemratio-row--itemratio_select) (L188) | ITEMRATIO_Select S1–S4 | 0002 · `0x00637910` | a-logs | QROW lines asserted by tc.py `--quality model` over the kept logs | T1 | S2a | 1 |
| 14 | [B. The itemratio row](../../specs/items/quality.md#b-the-itemratio-row--itemratio_select) (L212) | Uber is IsType weap/armo against exceptional or elite bases | 0002 · `0x0062B4D0` | a-logs | QROW rows of exceptional and elite bases in the Hell logs (uniques-*, props*, ichain*) | T1 | S2a | 1 |
| 15 | [B. The itemratio row](../../specs/items/quality.md#b-the-itemratio-row--itemratio_select) (L215) | Later row wins a tie; no match impossible with stock data | 0002 · `0x0063798F` | d-none | one row per key and version in stock data | T3 | — | 1 |
| 16 | [B. The itemratio row](../../specs/items/quality.md#b-the-itemratio-row--itemratio_select) (L218) | Version 0 rows reachable only through the creation-side roll | 0002 · `0x00556FD9` | a-logs | cube logs (run:2026-10-15-cube): quality-0 outputs' creation roll rows | T2 | S2c | 1 |
| 17 | [C. Shared terms and magic find](../../specs/items/quality.md#c-shared-terms-and-magic-find) (L227) | mf ≤ −100 jumps to E1 | 0002 · `0x0055871F` | d-none | no stock source | T3 | — | 1 |
| 18 | [C. Shared terms and magic find](../../specs/items/quality.md#c-shared-terms-and-magic-find) (L232) | M1: no killer or killer type > 1 gives MF 0 | 0002 · `0x005585D0` | a-logs | QMF lines: calls with no killer (objects, cows) and merc killers (1303 `ktype=1` calls in tc-quality-2) | T1 | S2a | 1 |
| 19 | [C. Shared terms and magic find](../../specs/items/quality.md#c-shared-terms-and-magic-find) (L245) | d is signed and may be negative; rec.level is u8 | 0002 · `0x0055872F` | a-logs | count logged rolls with qlvl > ilvl reproduced by quality.py | T1 | S2a | 1 |
| 20 | [C. Shared terms and magic find](../../specs/items/quality.md#c-shared-terms-and-magic-find) (L263) | M3: other monster killers use their owner; objects and missiles give 0 | 0002 · `0x0058F0D0` | b | new recipe: kills by a necromancer's skeletons or a Valkyrie; QMF/QKMF lines | T1 | H2a | 1 |
| 21 | [C. Shared terms and magic find](../../specs/items/quality.md#c-shared-terms-and-magic-find) (L270) | Negative MF −99..−1 raises every chance | 0002 · `0x0055871F` | d-none | no stock source of negative magic find | T3 | — | 1 |
| 22 | [D. Unique, set, rare and magic tests](../../specs/items/quality.md#d-unique-set-rare-and-magic-tests) (L292, L308) | D6 clamp c ← max(c, min) never acted | 0002 · `0x00558767` | a-run | tc-quality recipe at high MF (mfnecro) in Hell, `--mf` from the save: pre-clamp chance below the row minimum | T1 | H2a | 2 |
| 23 | [D. Unique, set, rare and magic tests](../../specs/items/quality.md#d-unique-set-rare-and-magic-tests) (L303) | Order: base, MF, minimum, ratio, draw | 0002 · `0x00558740` | a-run | same session as the D6 clamp | T1 | H2a | 1 |
| 24 | [D. Unique, set, rare and magic tests](../../specs/items/quality.md#d-unique-set-rare-and-magic-tests) (L315) | Signed idiv truncates toward zero; a zero divisor faults | 0002 · `0x0055872F` | a-logs | as negative d (count truncations of negative quotients); the zero divisor part is d-none | T1 | S2a | 1 |
| 25 | [E. Superior, normal, low](../../specs/items/quality.md#e-superior-normal-low) (L347) | Superior c < 1 wins with no draw | 0002 · `0x00558930` | a-logs | Hell logs replayed with `--quality model` (ilvl − qlvl ≥ 72 is common there): count E2 no-draw wins | T1 | S2a | 1 |
| 26 | [E. Superior, normal, low](../../specs/items/quality.md#e-superior-normal-low) (L353) | Low-quality bounds by record pair | 0002 · `0x00558921` | a-logs | count logged low-quality outcomes by d and record | T1 | S2a | 1 |
| 27 | [F. Boundaries (named only)](../../specs/items/quality.md#f-boundaries-named-only) (L362) | The creation-side roll runs on every drop and draws nothing | 0002 · `0x005574CC` | a-logs | items-chain IC* lines: seed unchanged across the creation-side roll on every drop | T1 | S2a | 1 |
| 28 | [F. Boundaries (named only)](../../specs/items/quality.md#f-boundaries-named-only) (L376) | Pre-switch overrides in ItemCreateByQuality | 0002 · `0x0062E9E0` | a-logs | items-chain ICQ/ICJ lines: quality unchanged on every drop (see uniques-sets B4) | T1 | S2a | 1 |
| 29 | [F. Boundaries (named only)](../../specs/items/quality.md#f-boundaries-named-only) (L387) | Builders and fallbacks per code | 0002 · `0x00557450` | a-logs | cite run:2026-10-15-items-chain (items_chain.py both, 0 mismatches) | T1 | S2a | 1 |
| 30 | [F. Boundaries (named only)](../../specs/items/quality.md#f-boundaries-named-only) (L397) | Creation draws on the game, unit and item seeds after the roll | 0002 · `0x00552E90` | a-logs | as row above (items-chain end-to-end replays) | T1 | S2a | 1 |
| 31 | [Outputs](../../specs/items/quality.md#outputs) (L442) | Output 0: no item record or type out of range | 0002 · `0x00558660` | d-none | unreachable from a TC | T3 | — | 1 |
| 32 | [Outputs](../../specs/items/quality.md#outputs) (L455) | No value outside 0–7; 0 and the early 7s code-read | 0002 · `0x00558660` | d-none | early returns unreachable with stock data | T3 | — | 1 |
| 33 | [Reimplementation notes](../../specs/items/quality.md#reimplementation-notes) (L537) | Truncation, not floor, for negative d | 0002 · `0x0055872F` | a-logs | as negative d | T1 | S2a | 1 |
| 34 | [Reimplementation notes](../../specs/items/quality.md#reimplementation-notes) (L540) | A zero divisor is fatal | 0002 · `0x0055872F` | d-none | no stock row has a zero divisor | T3 | — | 1 |
| 35 | [Reimplementation notes](../../specs/items/quality.md#reimplementation-notes) (L542) | The difficulty passed to ITEMRATIO_Select is unused | 0002 · `0x00637910` | a-logs | QROW keys across Normal, Nightmare and Hell logs: same rows for the same (uber, class, version) | T1 | S2a | 1 |
