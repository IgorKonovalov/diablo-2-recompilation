# ElemTypes (`data/global/excel/ElemTypes.txt` → `elemtypes.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 13 (no `Expansion` marker)   **Record:** 4 B
> **sha256:** `.txt` `91addf64ff87abb19dcceba77f6da6ed84e9e4194d30eeb1d69d36edd55cdc15`, `.bin` `bdfbe77eccedf24d166e41af1dc3dea54f793b0fa3b0ddca0ccb3590c3021185`
> **Doc status:** layout complete (plan 0037 Phase 0); meanings `[I]` for the two attack-code switches ([combat/0001](../findings/combat/0001-formulas.md), plan 0039 A1)

## Purpose

The element codes: a code list whose row index is the **element number** that the element columns of other tables
store. [MonStats](MonStats.md) `El1Type`..`El3Type` (`+0x101..+0x103`, u8) and [Skills](Skills.md) `EType` (`+0x1DC`,
u8) name an element by its `Code` and the compiled record holds this table's row index. Readers expected:
`combat/formulas` (plan 0037), the element of a monster's elemental attack and of a skill's elemental damage.

## Row identity

- `[C]` The `.bin` is a u32 record count (13) and 13 four-byte records, one per `.txt` row in order: `Code` as a
  4-byte space-padded code; row 0 (`None`) has a blank code and stores four spaces.
  `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel elemtypes`: 13 records × 1 mapped field =
  **13 cells, 0 mismatches**; `excel_bin.py unknown … elemtypes` lists no uncovered byte. The record count equals the 13
  `.txt` data rows. (tbl:ElemTypes.txt:Code)
- `[C]` **The row index is the stored element number.** The MonStats `El<e>Type` and Skills `EType` fields diff with
  0 mismatches as indices into this table's `Code` rows (layouts `monstats` and `skills` in `tools/excel_layouts.py`,
  `excel_bin.py diff`, gate survey `excel_layout`); a blank cell stores 0, the row of `None`.
  (tbl:MonStats.txt:El1Type, tbl:Skills.txt:EType)
- `[I]` `elemtypes.bin` is loaded only under `-txt`, by `DATATBLS_LoadCodeLists` (call site `0x0061299E`, 4-byte
  record), to resolve the element columns while compiling `.txt`; a stock run never loads it, so the game knows the
  elements only as these numbers ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300),
  fn:DATATBLS_LoadCodeLists@0x00612750).
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` the game loads this table as one of
  the 15 code lists of `DATATBLS_LoadCodeLists` and writes an `elemtypes.bin` byte-identical to the shipped one, which
  ships in d2exp and patch_d2 ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3). That a stock run never loads it stays `[I]`: the file ships, so its absence could not show it (data/0001 §
  S1b row 30). (fn:DATATBLS_LoadCodeLists@0x00612750)

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Elemental Type` | str, 13 distinct, len ≤ 13 | — (not compiled) | editor name of the element | — | [C] (absence) |
| `Code` | str, 12 distinct codes of 3–4 characters, 1 blank (row 0) | `+0x0` 4-byte code, space padded (`mag `, blank = four spaces) | the element's code, the key other tables name it by | key of MonStats `El<e>Type`, Skills `EType` | [C] |

`[C]` The rows and their users (`python3 -I tools/combat_survey.py codes workspace/merged/data/global/excel`; a cell
counts once per non-blank `El<e>Type` or `EType` cell):

| Row | `Code` | `Elemental Type` | MonStats `El<e>Type` cells | Skills `EType` cells |
|---:|---|---|---:|---:|
| 0 | (blank) | None | 0 | 0 |
| 1 | `fire` | Fire | 57 | 35 |
| 2 | `ltng` | Lightning | 73 | 20 |
| 3 | `mag` | Magic | 21 | 13 |
| 4 | `cold` | Cold | 60 | 22 |
| 5 | `pois` | Poison | 76 | 8 |
| 6 | `life` | Life Drain | 1 | 0 |
| 7 | `mana` | Mana Drain | 19 | 0 |
| 8 | `stam` | Stamina Drain | 9 | 0 |
| 9 | `stun` | Stun | 11 | 2 |
| 10 | `rand` | Random | 6 | 0 |
| 11 | `burn` | Burning | 0 | 0 |
| 12 | `frze` | Freeze | 2 | 0 |

335 MonStats cells and 100 Skills cells; 11 of the 13 rows are named by some cell (`None` and `burn` by none).
(tbl:ElemTypes.txt:Code, tbl:MonStats.txt:El1Type, tbl:Skills.txt:EType)

## Code semantics (plan 0037 Phase 1, plan 0039 A1)

From [combat/0001 § 12b (d)](../findings/combat/0001-formulas.md#12b-answers-to-the-archivists-phase-0-questions-backlog-2026-10-16-ae) and
[§ 5](../findings/combat/0001-formulas.md#5-the-damage-build-combat_builddamage) (static reading). Two switches in the attack code read the row
number; nothing reads the code text at run time.

- `[I]` **`MonAttackStats`** (a monster's `El<e>` group at attack time, when its `El<e>Mode` matches and its `El<e>Pct`
  draw passes): 1 `fire`, 2 `ltng`, 3 `mag` set the element's min and max damage stats; 4 `cold` also sets stat 56
  (cold length) to the duration; 5 `pois` sets min and max `× 10` and stat 59 (poison length) to duration `× 2`; 6
  `life`, 7 `mana`, 8 `stam` set the drain stats 60/61, 62/63, 64/65; 9 `stun` sets only stat 66 (stun length) to the
  duration; 10 `rand` draws `RNG_Range(seed, 5) + 1`, a row 1–5, and uses duration 25 when the cell's is 0; 11 `burn`
  sets stats 316/317 and 315. **12 `frze` falls to the default and sets nothing**, so the two MonStats cells naming it
  have no effect there. (fn:sub_005A4F50_MonAttackStats@0x005A4F50, 0x005A5300–0x005A53D0, tbl:MonStats.txt:El1Type)
- `[I]` **The damage builder's conversion** (`convType`, step 9 of § 5): a share of physical damage moves to 1 fire,
  2 lightning or 3 magic; 4 cold with a cold length of at least 50; 5 poison (`/8`) with a length of at least 50; 10
  draws a row 1–5 (`RNG_Range(seed, 5) + 1`); 11 fire with a burn length of at least 50; 12 cold with a freeze length
  of at least 50. No writer of `convType` was found on the attack paths read. (fn:COMBAT_BuildDamage@0x0057B7D0,
  0x0057BCB2–0x0057BD71)
- `[I]` The five damage elements meet the defender's resistance rows of `g_DamageResistTable`: fire 39, lightning 41,
  cold 43, magic 37, poison 45 (the stat ids of the resistances; physical is 36), with absorb only for the first four
  ([§ 7](../findings/combat/0001-formulas.md#7-reductions-combat_applyreductions), data:g_DamageResistTable@0x00732980).

## Interpretation notes

- `[L]` What Skills `EType` does at run time (35 `fire` … 2 `stun` cells): its reader is not among those read.
- `[I]` MonStats `El<e>Type` `rand` (6 records) and `frze` (2) are the rows beyond the five damage elements a monster
  attack meets: `rand` picks one of rows 1–5, `frze` does nothing in `MonAttackStats` (§ Code semantics).
  (fn:sub_005A4F50_MonAttackStats@0x005A4F50)

## Open questions

- ~~The element-number switch in the attack code (what each row does to the defender)~~ answered `[I]` by combat/0001
  § 12b (d) ([§ Code semantics](#code-semantics-plan-0037-phase-1-plan-0039-a1)).
- `[L]` The reader of Skills `EType`, and whether any path writes `convType` (the builder's conversion).
