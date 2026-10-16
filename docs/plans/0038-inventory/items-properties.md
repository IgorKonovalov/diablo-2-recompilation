# Plan 0038 inventory: items/properties

Phase 0 of [plan 0038](../0038-inferred-claims-sweep.md), cluster (0a) items.

- **Spec:** [items/properties](../../specs/items/properties.md), status `reviewed`, read at commit `3b1433f` (on `main` at `e1c807a`).
  Front matter `I` = **35**; the *count* column below sums to 35.
- **Finding:** [items/0006](../../findings/items/0006-properties.md); run records in
  [findings/items/experiments.md](../../findings/items/experiments.md).
- **Columns.** *Section* links the spec section and lists the spec lines of the statements at that commit. *Anchor* is the
  finding number and the first code address of the statement. *Class*, *tier* and *batch* follow the plan's
  [Classes](../0038-inferred-claims-sweep.md#classes). A forced-run row is class `b` with a route that starts `forced:`.
  A `—` batch means the row is class (d) and no batch takes it.
- **Totals by class:** a-logs 13, a-run 5, b 6, c 3, d-none 8.

| # | Section | Claim | Anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/items/properties.md#entry-points) (L53) | Four callers of ItemApplyProps outside creation; mode 6 set bonuses | 0006 · `0x004C0D20` | c | full xref of ItemApplyProps | T3 | S2b | 1 |
| 2 | [Tables](../../specs/items/properties.md#tables) (L88) | ItemStatCost op columns, save columns, set and gem blocks not read | 0006 · `0x0065EA50` | a-logs | props.py reproduces every logged stat list without them (rule 4) | T1 | S2b | 1 |
| 3 | [Constants](../../specs/items/properties.md#constants) (L123) | STACK_CAP 511 for maxstack plus stat 254 | 0006 · `0x006295B0` | d-none | no stock stack reaches 511 | T3 | — | 1 |
| 4 | [Inputs and boundaries](../../specs/items/properties.md#inputs-and-boundaries) (L137, L671) | ITEMS_RollStaffMods is a seed oracle; staff mods follow the last ApplyProps | 0006 · `0x005C1260` | a-logs | staff-mod checker case of S2b over the STF brackets (removes the oracle) | T1 | S2b | 2 |
| 5 | [Inputs and boundaries](../../specs/items/properties.md#inputs-and-boundaries) (L149) | No func reaches the calc VM | 0006 · `0x0065EB30` | c | call-graph closure of the roll, writer and getters | T3 | S2b | 1 |
| 6 | [Algorithm](../../specs/items/properties.md#algorithm) (L157) | Signed 32-bit arithmetic; Range and RangeOffset | 0006 · `0x0045C390` | a-logs | props.py (every logged roll) | T1 | S2b | 1 |
| 7 | [A. Base stats on the unit seed](../../specs/items/properties.md#a-base-stats-on-the-unit-seed) (L213, L252, L647) | Type 11 setup draws on the item seed; never reached | 0006 · `0x0065E8E0` | a-run | items-chain session hunting a type-11 base (with uniques-sets A3) | T3 | H2b | 3 |
| 8 | [A. Base stats on the unit seed](../../specs/items/properties.md#a-base-stats-on-the-unit-seed) (L242) | Quantity-1 rule never fires on a drop; magic throwing weapons keep quantity | 0006 · `0x0062A0F0` | a-logs | magic and rare throwing weapons in the kept Hell logs (Example 3 is one) | T1 | S2b | 1 |
| 9 | [B. ItemApplyProps](../../specs/items/properties.md#b-itemapplyprops-modes-and-blocks) (L302) | Set rows with add func carry aprops; two blank ones too | 0006 · `0x0065FFE3` | c | data check over SetItems | T3 | S2b | 1 |
| 10 | [B. ItemApplyProps](../../specs/items/properties.md#b-itemapplyprops-modes-and-blocks) (L306) | Version 0 property table, two set blocks | 0006 · `0x0065FE10` | d-none | no drop makes version 0 | T3 | — | 1 |
| 11 | [E. The handlers per func](../../specs/items/properties.md#e-the-handlers-per-func) (L382, L387) | Funcs 4 and 9: no stock row uses them | 0006 · `0x0065EC80` | d-none | no stock row | T3 | — | 2 |
| 12 | [E. The handlers per func](../../specs/items/properties.md#e-the-handlers-per-func) (L390, L403, L416) | Funcs 12 and 36 put the roll in the param | 0006 · `0x0065FC40` | b | forced: TC-named run naming Ormus' Robes and Hellfire Torch; func code reads no TC cell | T3 | H2c | 3 |
| 13 | [E. The handlers per func](../../specs/items/properties.md#e-the-handlers-per-func) (L396, L512) | Func 18 by-time value packing; no drop reaches it | 0006 · `0x0065F870` | d-none | only spawnable-0 suffixes name it | T3 | — | 2 |
| 14 | [E. The handlers per func](../../specs/items/properties.md#e-the-handlers-per-func) (L401) | Func 23 makes the item ethereal | 0006 · `0x0065FD20` | b | forced: TC-named ethereal uniques (Ethereal Edge, Wraithflight) | T3 | H2c | 1 |
| 15 | [E. The handlers per func](../../specs/items/properties.md#e-the-handlers-per-func) (L402) | Func 24: v ← prev or Roll | 0006 · `0x0065F390` | b | forced: TC-named unique with a func-24 row | T3 | H2c | 1 |
| 16 | [E. The handlers per func](../../specs/items/properties.md#e-the-handlers-per-func) (L420) | Func 10 param packs class and tab | 0006 · `0x0065F3F0` | a-logs | props.py stat params of `skilltab` affixes in the kept Hell logs | T1 | S2b | 1 |
| 17 | [E. The handlers per func](../../specs/items/properties.md#e-the-handlers-per-func) (L438) | dmg-min/dmg-max clamp not reached on stock data | 0006 · `0x0065EE80` | d-none | no negative block in stock data | T3 | — | 1 |
| 18 | [E. The handlers per func](../../specs/items/properties.md#e-the-handlers-per-func) (L450, L454) | Func 7 +1 max-damage fallback when t ≤ 0; damage reset | 0006 · `0x00483360` | a-logs | search kept logs for weapons with max·dmg% < 100; else a-run (low-level magic weapons) | T1 | S2b | 2 |
| 19 | [F. Ethereal and sockets](../../specs/items/properties.md#f-ethereal-and-sockets) (L535, L549, L573) | Skip bits 0x02/0x08 and the order of draws around them | 0006 · `0x00556CA0` | a-logs | cube outputs (flags 0x0A) and imbues (0x22) in the cube and quest logs | T2 | S2c | 3 |
| 20 | [F. Ethereal and sockets](../../specs/items/properties.md#f-ethereal-and-sockets) (L547, L591) | Classic body armour makes no socket draw | 0006 · `0x00556C0F` | a-run | items-chain classic session (classicsorc): normal and superior `tors` drops | T1 | H2b | 2 |
| 21 | [F. Ethereal and sockets](../../specs/items/properties.md#f-ethereal-and-sockets) (L578) | An ethereal unique can be made ethereal twice (Wraithflight) | 0006 · `0x0065FD20` | b | forced: TC-named Wraithflight, enough drops for an r < 5 roll | T3 | H2c | 1 |
| 22 | [F. Ethereal and sockets](../../specs/items/properties.md#f-ethereal-and-sockets) (L587) | SetSockets quality clamps do not apply to qualities 2 and 3 | 0006 · `0x0062BC61` | d-none | no observable on this path | T3 | — | 1 |
| 23 | [Reimplementation notes](../../specs/items/properties.md#reimplementation-notes) (L802) | `sock` draws even when it writes nothing | 0006 · `0x0065F590` | a-logs | kept SOK lines with a cap below 1; else a-run | T1 | S2b | 1 |
| 24 | [Reimplementation notes](../../specs/items/properties.md#reimplementation-notes) (L823) | dur%: the +1 comes before the percentage | 0006 · `0x00556D41` | a-logs | kept superior items with dur% where the two orders differ; else a-run (long Hell items-chain hunt) | T1 | S2b | 1 |

## Forced-run candidate (batch H2c)

The func 12/36, 23, 24 and *Wraithflight* rows are reached only by uniques that stock drops make too rarely
(*Ormus' Robes*, the ethereal uniques) or never (*Hellfire Torch*). Proposed cells: the TC-named path of
run:2026-10-15-uniques-tcnamed-forced, `treasureclassex.bin` `Item1..n` cells of the Hell TCs that recipe reaches,
naming those uniques. The handlers read `Properties`, `UniqueItems` and the item's stats, none of the edited
`TreasureClassEx` cells; the unique selection itself stays `[I]` (it reads the named cell, uniques-sets § F). ADR-0013
read lists needed first in [items/0006 § 4](../../findings/items/0006-properties.md#4-the-handlers-per-func) (the func handlers) and
[items/0004 § 6](../../findings/items/0004-uniques-sets.md#6-a-tc-cell-that-names-a-unique-or-a-set-item). No stock companion reaches *Hellfire Torch*
(Uber Tristram cannot open); *Ormus' Robes* and the ethereal uniques have a stock path, logged only if a long Hell
hunt meets one.
