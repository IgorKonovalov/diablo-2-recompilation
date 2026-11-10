# SkillDesc (`data/global/excel/skilldesc.txt` → `skilldesc.bin`)

> **Source archive:** `.txt` patch_d2, `.bin` patch_d2   **Rows:** 221 `.bin` records (= `.txt` data rows)   **Record:** 288 B
> **sha256:** `.txt` `cd1cd11cb1d85a5dda7a4e666f6e15dceacfd121e4e839e2842d0e25c44ed993`, `.bin` `52c96055cf6016b3cd2b45ba51106f1e13a089bd92be691d0d93770981b54740`
> **Doc status:** record layout complete for every column except the formula bytecode (plan 0068 Phase 1; formulas are in [calc.md](../formats/calc.md)); server readers in data/0006 § 3.2 (below)

## Purpose

221 skill-description rows: where the skill sits in the skill tree (page, row, column), its icon cel, the string keys of its name and texts, and the damage-description and line formulas (`ddam calc`, `p1..3dmmin/max`, `desccalca/b`, `dsc2calca/b`, `dsc3calca/b`) that the tooltip computes. [Skills](Skills.md) `skilldesc` names a row (all 221 rows are used). The calc columns are bytecode offsets into `skilldesccode.bin` ([calc.md](../formats/calc.md), [data/0005](../findings/data/0005-calc.md)). Loader call site `0x006178E1`, record 288, not `-txt`-only (a second 2-byte call at `0x00617842` is `-txt`-only; [data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300)). Leads: none.

## Row identity

- `[C]` Key column `skilldesc`: 221 rows, 221 distinct, none blank; [Skills](Skills.md) `skilldesc` names each row (221 distinct, set inclusion). The `.bin` record starts with the row's own index (`u16`).
- `[C]` No `Expansion` row; 221 `.txt` rows, 221 `.bin` records.

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `skilldesc` | str, 221 distinct, len <= 20, 0 blank | +0x000 u16 row index into `skilldesc:skilldesc` | row key | read by Skills `skilldesc` | [C] |
| tree position | int, -1..58, 34 distinct, 0 blank | +0x002, +0x003, +0x004, +0x005, +0x006, +0x007 (u8) | tree page, row, column, list row/pool and icon cel `[L]`; `SkillPage` (+0x002) is also the page of the server's tab bonus, 1–3 or 0 for none `[I]` (below) | — | [C] layout, [L] meaning (`SkillPage` [I]) |
| text keys | str, 883 distinct, len <= 17, 10 blank | +0x008, +0x00A, +0x00C, +0x00E, +0x010 (u16 string-table key) | string-table keys (`skillname0`, `skillsd0`, ...) of the name, short, long, alternate and mana texts | [tbl.md](../formats/tbl.md) string tables | [C] layout, [L] meaning |
| `descdam`, `descatt` | int, 1..24, 24 distinct, 283 blank | +0x012, +0x014 (u8) | description selector codes `[L]` | — | [C] layout, [L] meaning |
| `ddam calc1`, `ddam calc2` | str, 9 distinct, len <= 64, 420 blank | +0x018, +0x01C (s32 bytecode offset) | damage-description formulas (bytecode offsets into `skilldesccode.bin`) | [calc.md](../formats/calc.md) | [C] layout |
| element columns | str, 3 distinct, len <= 4, 651 blank (`cold`, `fire`, `ltng`) | +0x020, +0x021, +0x022 (u8 row index into `elemtypes:Code`) | damage element of part 1..3 `[L]` | [ElemTypes](ElemTypes.md) `Code` | [C] layout and reference, [L] meaning |
| damage min and max | str, 14 distinct, len <= 16, 1302 blank | +0x024, +0x030, +0x028, +0x034, +0x02C, +0x038 (s32 bytecode offset) | min and max damage formulas of part 1..3 (bytecode offsets) | [calc.md](../formats/calc.md) | [C] layout |
| `descmissile1..3` | str, 17 distinct, len <= 25, 646 blank | +0x03C, +0x03E, +0x040 (s16 row index into `missiles:Missile`) | a missile whose damage the description shows `[L]`; blank stores −1 | [Missiles](Missiles.md) `Missile` | [C] layout and reference, [L] meaning |
| description lines | int, 1..73, 62 distinct, 2622 blank | +0x042 .. +0x052, 17 fields (u8) | line-format selector of each tooltip line (`u8` each) `[L]` | — | [C] layout, [L] meaning |
| line texts | str, 289 distinct, len <= 22, 6126 blank | +0x054 .. +0x096, 34 fields (u16 string-table key) | string-table keys of the two text parts of each line, `a` parts first, then `b` parts, in the order description, `dsc2`, `dsc3` | [tbl.md](../formats/tbl.md) | [C] layout, [L] meaning |
| line formulas, `a` parts | str, 149 distinct, len <= 120, 2970 blank | +0x098 .. +0x0D8, 17 fields (s32 bytecode offset) | line formulas, first part (bytecode offsets) | [calc.md](../formats/calc.md) | [C] layout |
| line formulas, `b` parts | str, 26 distinct, len <= 72, 3722 blank | +0x0DC .. +0x11C, 17 fields (s32 bytecode offset) | line formulas, second part (bytecode offsets) | [calc.md](../formats/calc.md) | [C] layout |
| `eol` | int, 0..0, 1 distinct, 0 blank | not compiled | end-of-line marker column; not compiled | — | [C] |

## Interpretation notes

- `[C]` Layout: the calc columns were laid out in plan 0035 ([calc.md](../formats/calc.md)); plan 0068 Phase 1 added the rest (`skilldesc` `u16`, six `u8` tree fields, five `u16` string keys at +0x08..+0x10, `descdam` +0x12, `descatt` +0x14, three element bytes at +0x20..+0x22, three `s16` missile indices at +0x3C..+0x40, the 17 line selectors at +0x42..+0x52, the 34 text keys at +0x54..+0x97) (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel skilldesc`: 24 973 cells, 0 unexplained, 1 explained, the blank-cell `revive` formula in `desccalcb2`). The text-key order (all `a` parts, then all `b` parts) is the one that matches every record; both groups carry the same blank key `0x1506` in unused slots.
- `[C]` The 114 `.txt` columns are all compiled except `eol`; the only `.bin` bytes no column covers are +0x013, +0x015..+0x017, +0x023 and +0x053, 0 in every record (`excel_bin.py unknown`).
- `[I]` Server use (plan 0068 Phase 2, [data/0006 § 3.2](../findings/data/0006-loaded-tables-and-bundles.md#32-skilldesc-on-the-server-the-skill-level-bonus)): `SkillPage` (+0x02, reached through Skills `+0x194`) is the one SkillDesc column the server reads outside the calc variables: `sub_00644180_SkillLevelBonus` adds stat 188 (`item_addskill_tab`, param `8 * class + SkillPage - 1`) to a player's own-class skill only if `SkillPage` is 1-3 (non-zero). The row count (`+0xB94`) is read by `sub_00627AF0_SkillHasDesc` (1 iff the skill is a Skills row and `0 <= Skills.skilldesc < count`; its one caller drops legacy stats 107-109 and 181-187 when it fails), and the description missiles by `SKILLS_CalcVar` codes 43-48 (data/0005 § G). Every other column is read by the client skill tree only. The bonus formula as a whole is in data/0006 § 3.2 (`[I]`).
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- `[L]` Whether a column other than `SkillPage`, the count and the description missiles is read on the server: the client readers were not enumerated one by one (data/0006 § 3). The `calc` columns' use is in [data/calc](../specs/data/calc.md).
