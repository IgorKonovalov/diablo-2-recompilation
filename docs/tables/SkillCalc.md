# SkillCalc (`data/global/excel/skillcalc.txt` → `skillcalc.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 73 (no `Expansion` marker)   **Record:** 4 B
> **sha256:** `.txt` `eb19168fd90095e39cd18515f7331011d4fd8df034c4efbe8c10b38eb930e032`, `.bin` `44271908723a5b72d5ef38f2397b4757ea52909d33236611c739ab8c93ace3b7`
> **Doc status:** layout complete (plan 0035 Phase 0); meanings in [data/0005 § 7.1](../findings/data/0005-calc.md#71-skillcalc-codes-skills_calcvarunit-code-skill-lvl-skill-out-of-range--0) (plan 0035 Phase 1)

## Purpose

The variable names of the skill formulas: a bare name in a `skills.txt` or `skilldesc.txt` formula cell (`lvl`,
`ln12`, `par3`) compiles to "push variable *i*", *i* = this table's row ([calc.md](../formats/calc.md)). Missile
formulas use it too, for the second argument of `skill(…)` (`skill('Inferno'.blvl)`). Readers: `data/calc`.

## Row identity

- `[C]` The `.bin` is a u32 record count (73) and 73 four-byte records, one per `.txt` row in order: `code` as a
  4-byte space-padded code. `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel skillcalc`: 73
  cells, 0 mismatches; every byte mapped.
- `[C]` **The row index is the variable operand.** All 1 598 variable operands (`04 i`) of `skillscode.bin` and
  `skilldesccode.bin` are rows of this table whose code occurs in the cell's text (`tools/calc_survey.py summary`,
  `var_out_of_range=0`, `var_not_in_text=0`), e.g. `lvl` (row 16) → `04 10`, `ln12` (row 0) → `04 00`.
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` the game loads this table as one of
  the 15 code lists of `DATATBLS_LoadCodeLists` and writes a `skillcalc.bin` byte-identical to the shipped one, which
  ships in patch_d2 ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3). That a stock run never loads it stays `[I]`: the file ships, so its absence could not show it (data/0001 §
  S1b row 30). (fn:DATATBLS_LoadCodeLists@0x00612750)

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `code` | str, 73 distinct codes of 3–4 characters | `+0x0` 4-byte code | the variable's name in a formula | — | [C] |
| `*desc` | str, 73 cells: a formula or a phrase (`a+lvl*b`, `((110*lvl) * (b-a))/(100 * (lvl+6)) + a`, `skill level`) | — (not compiled) | editor comment | — | [C] |

The codes by row: 0–7 `ln12 dm12 ln34 dm34 ln56 dm56 ln78 dm78`; 8–15 `par1`..`par8`; 16 `lvl`; 17–19 `edmn edmx
edln`; 20–25 `toht mana mps math madm macr`; 26–34 `m1en m1ex m1el m2en m2ex m2el m3en m3ex m3el`; 35–37 `m1rn
m2rn m3rn`; 38–42 `edns edxs ulvl blvl usmc`; 43–48 `m1eo m1ey m2eo m2ey me3o me3y`; 49–53 `enma exma edma enms
exms`; 54 `len`; 55–58 `clc1`..`clc4`; 59 `rng`; 60–65 `ast1`..`ast6`; 66–70 `pst1`..`pst5`; 71 `pets`; 72 `skpt`.

## Interpretation notes

- **Used in stock formulas** (`calc_survey.py`, data): skills use rows 0–6, 8–18, 20, 38, 40, 49–53; skilldesc rows
  0–6, 8–20, 22–27, 29, 30, 32, 33, 38, 39, 42–44, 49, 50, 54, 55, 58. The rest occur in no stock cell. `[C]`
- **What each code reads** (a skill's `Param`, a level-scaled value, a missile's damage, a stat) is the variable
  reader's switch, read in [data/0005 § 7.1](../findings/data/0005-calc.md#71-skillcalc-codes-skills_calcvarunit-code-skill-lvl-skill-out-of-range--0) (`0x00646460`, `[I]` there); the `*desc` text is only the editor's note
  and is not compiled. The naming pattern (`ln12` = `Param1 + lvl·Param2` by its `*desc`) is `[L]` here.

## Open questions

- None.
