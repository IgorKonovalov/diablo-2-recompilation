# MissCalc (`data/global/excel/misscalc.txt` → `misscalc.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 43 (no `Expansion` marker)   **Record:** 4 B
> **sha256:** `.txt` `3aaaea44299543cc09ca5b23835fbb46182ce6365757d8ff838513e28f1422b0`, `.bin` `c19cdc632ae9fb97e346e54785ee936fff4209d8b59ce11dc56e3a14b500e961`
> **Doc status:** layout complete (plan 0035 Phase 0); meanings in data/0005 § 7.2 (plan 0035 Phase 1)

## Purpose

The variable names of the missile formulas: a bare name in a `missiles.txt` formula cell (`lvl`, `dl12`) compiles to
"push variable *i*", *i* = this table's row ([calc.md](../formats/calc.md)). Skill formulas reach it through
`miss(…)`. Readers: `data/calc`.

## Row identity

- `[C]` The `.bin` is a u32 record count (43) and 43 four-byte records, one per `.txt` row in order: `code` as a
  4-byte space-padded code. `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel misscalc`: 43
  cells, 0 mismatches; every byte mapped.
- `[C]` **The row index is the variable operand.** The 8 variable operands of `misscode.bin` are rows of this table
  whose code occurs in the cell's text: `lvl` (row 18) → `04 12`, `dl12` (row 41) → `04 29`
  (`tools/calc_survey.py summary`, `var_out_of_range=0`, `var_not_in_text=0`).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `code` | str, 43 distinct codes of 3–4 characters | `+0x0` 4-byte code | the variable's name in a missile formula | — | [C] |
| `*desc` | str, a phrase per row (`param1`, `missile level`, `elemental damage min`) | — (not compiled) | editor comment | — | [C] |

The codes by row: 0–4 `par1`..`par5`; 5–9 `cpa1`..`cpa5`; 10–12 `hpa1 hpa2 hpa3`; 13–15 `chp1 chp2 chp3`; 16–17
`dpa1 dpa2`; 18 `lvl`; 19–23 `edmn edmx edln edns edxs`; 24–27 `damn damx dmns dmxs`; 28 `rang`; 29–32 `sl12 sd12
sl34 sd34`; 33–36 `cl12 cd12 cl34 cd34`; 37–40 `shl1 shd1 chl1 chd1`; 41–42 `dl12 dd12`.

## Interpretation notes

- **Used in stock formulas**: only rows 18 (`lvl`) and 41 (`dl12`). `[C]`
- **What each code reads** (a missile's `Param`, `CltParam`, hit parameters, damage fields) is data/0005 § 7.2
  (`0x0064B340`, `[I]` there). The `*desc` text is only the editor's note. `[L]` here.

## Open questions

- Link data/0005 § 7.2 when the branches meet (plan 0035).
