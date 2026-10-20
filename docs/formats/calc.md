# Calc formula pools (`itemscode.bin`, `misscode.bin`, `skillscode.bin`, `skilldesccode.bin`)

> **Status:** first draft (plan 0035 Phase 0). Pairing and byte coverage `[C]` by data; the opcode meanings are the
> reverser's ([data/0005](../findings/data/0005-calc.md), plan 0035 Phase 1), cited by address with that finding's tags. The evaluator
> (plan 0035 Phase 2) and the spec over both: [specs/data/calc](../specs/data/calc.md).
> **Parser:** `tools/calc_survey.py` (pairing, walk, opcode table; gate survey `calc_bytes`). The compiler model is
> `tools/calc.py` (plan 0035 Phase 1; gate survey `calc`: `calc.py compile` rebuilds the four pools from the texts).

## Purpose and files

A formula cell of an excel table (a skill's damage, a missile's range, a description number, a Misc `calc1`) is
compiled into a short bytecode string. The strings of one table family are concatenated into one header-less pool
file, and the table's record holds the string's offset (s32) in that pool, or −1 for none
([excel-bin.md § Calc columns](excel-bin.md#calc-columns-formulas)). All four pools are in
`data/global/excel/` (patch_d2), with no count header ([excel-bin.md](excel-bin.md)).

| pool | bytes | tables whose fields point into it | formula fields per record | fields checked | strings |
|---|---|---|---|---|---|
| `itemscode.bin` | 158 | weapons, armor, misc (in that order) | 5: `len`, `calc1..3`, `spelldesccalc` | 3 295 | 45 |
| `misscode.bin` | 196 | missiles | 7: `SrvCalc1`, `CltCalc1`, `SHitCalc1`, `CHitCalc1`, `DmgCalc1`, `DmgSymPerCalc`, `EDmgSymPerCalc` | 4 788 | 25 |
| `skillscode.bin` | 5 891 | skills | 36 ([Skills](../tables/Skills.md) § Calc columns) | 12 852 | 853 |
| `skilldesccode.bin` | 4 252 | skilldesc | 42: `ddam calc1/2`, `p1..3dmmin`, `p1..3dmmax`, `desccalca/b1..6`, `dsc2calca/b1..4`, `dsc3calca/b1..7` | 9 282 | 867 |

Counts from `python3 -I tools/calc_survey.py summary workspace/merged/data/global/excel` (`[C]`). The field
offsets are in `tools/excel_layouts.py` (`K` fields): the item and skills ones were found by earlier plans; the
missiles and skilldesc ones are the loaders' descriptor offsets read in data/0005 § 1, and the layouts added here
(partial: formula fields only) check them over every record (`excel_bin.py diff … missiles` 4 788 cells,
`… skilldesc` 9 282 cells, 0 unexplained; one explained cell, below). Plan 0045 Phase 0 completed the missiles layout
around the same seven offsets ([Missiles](../tables/Missiles.md): 99 864 cells, 0 unexplained). `itemstatcost` has no formula column (data/0005).

## Pairing cells with bytes

`tools/calc_survey.py` reads every formula field of every record, sorts the non-negative offsets, and gives each
cell the bytes from its offset to the next one. Over the four pools:

- `[C]` **Every byte belongs to exactly one cell.** 1 790 strings cover 10 497 bytes; the first string of each pool
  starts at 0 and the last ends at the end of the file; no two fields share an offset (`shared=0`), none points
  outside its pool, and no blank cell has a string. Two equal texts are stored twice (no sharing).
- `[C]` **Record order, then `.txt` column order.** In each pool the strings follow the records in order
  (`record_order=1`; for the item pool weapons, then armor, then misc), and within a record the order of the columns
  in the `.txt` header (`column_order=1`), not the order of the field offsets: 60 same-record pairs over the four
  pools are stored against their field offsets (misc `len` `+0xB0` before `calc1` `+0xA4`; skills `+0x190` before
  `calc1` `+0x138`), and every one follows the `.txt` columns. This does not say whether the compiler walks the `.txt`
  columns or its descriptor list: the loaders' descriptors list these columns in the `.txt` order too. The only formula
  columns whose descriptor order differs from the `.txt` order are skills `perdelay` (descriptor entry at 0x0061673B)
  before `skpoints` (0x00616C03) and `delay` (0x00616D88), and no stock row fills `perdelay` together with either, so
  the stock pools are the same under both walks (architect review, plan 0035 Phase 0; the question is
  [data/0005](../findings/data/0005-calc.md)'s). `[L]`
- `[C]` **One non-blank cell has no string**: skilldesc record 95 (`revive`), `desccalcb2` is a single space, and
  its field is −1 (`minus1_nonblank=1`). data/0005 § 4 reads why: the space gives no token, and an empty compile
  stores −1 (0x006C1992).
- `[C]` **Every string walks** as opcodes to exactly its end, `00` last and nowhere earlier, with these operand
  sizes (`walk_bad=0`):

  | opcode | operand bytes after it |
  |---|---|
  | `01` | 1 (function index) |
  | `04` / `05` / `06` | 1 / 2 / 4 (variable index) |
  | `07` / `08` / `09` | 1 / 2 / 4 (signed constant, little-endian) |
  | every other | 0 |

  The sizes of `05`, `06` and `09` are data/0005's (0x006C19C0, 0x006C1A50, `[I]` there): no stock string has them,
  so the walk does not test them.
- `[C]` **Variable operands are rows of the variable lists.** Each of the 1 606 operands of `04` is a row index of
  [SkillCalc](../tables/SkillCalc.md) (skills, skilldesc) or [MissCalc](../tables/MissCalc.md) (missiles) whose code
  occurs in the cell's text (`var_out_of_range=0`, `var_not_in_text=0`): `lvl` is `04 10` in a skill (skillcalc row
  16) and `04 12` in a missile (misscalc row 18). The item pool has no variable.

## Opcodes seen

`python3 -I tools/calc_survey.py ops …`: the 14 opcode bytes the walk meets in the stock pools, with the number of
strings that hold each, and an example. The meaning column is data/0005's reading (§§ 4–5): the source token or
operation the compiler encodes as that byte, `[C]` there by recompiling every stock cell. What the evaluator computes
for each of these 14 opcodes (an int32 stack, `/` as `idiv` truncating toward zero, comparisons giving 0/1) is `[C]` in
data/0005 by run:2026-10-16-calc, 44 529 logged evaluations replayed on these pool bytes with 0 mismatches
([data/0005 § 10](../findings/data/0005-calc.md#10-the-evaluator-at-run-time-phase-2-run2026-10-16-calc)); the paths
that run did not reach stay `[I]` there. The evaluator as pseudocode is
[specs/data/calc § D](../specs/data/calc.md#d-the-evaluator--calc_eval). The data here shows only that the texts and
bytes line up as the examples do.

| byte | strings | example text → bytes | meaning (data/0005) | tag |
|---|---|---|---|---|
| `00` | 1 790 | `5` → `07 05 00` | end of the expression | [C] |
| `01` | 356 | `"min(24,ln12)"` → `07 18 04 00 01 00 00` | call function *f* (the next byte) on the values pushed before it | [C] |
| `02` | 1 | Fire Wall's `EDmgSymPerCalc` `(skill('Warmth'.blvl)*par8+skill('Inferno'.blvl)*par7` (no `)`) → `… 12 10 02 00` | an unclosed `(` flushed as a byte | [C] |
| `04` | 1 330 | `lvl` → `04 10 00` | push variable *i* (1-byte index) | [C] |
| `07` | 750 | `5` → `07 05 00` | push an s8 constant | [C] |
| `08` | 182 | `750` → `08 EE 02 00` | push an s16 constant | [C] |
| `0A` | 14 | `(lvl < 4) ?lvl:(2+lvl/3)` → `04 10 07 04 0A …` | `<` | [C] |
| `0B` | 1 | `(skill('summon fenris'.lvl) > 0) ? …` | `>` | [C] |
| `10` | 221 | `lvl+2` → `04 10 07 02 10 00` | `+` | [C] |
| `11` | 70 | `lvl-1` → `04 10 07 01 11 00` | binary `-` | [C] |
| `12` | 305 | `lvl*2` → `04 12 07 02 12 00` (missile) | `*` | [C] |
| `13` | 98 | `ln12/2` → `04 00 07 02 13 00` | `/` | [C] |
| `15` | 23 | `-edmn` → `04 11 15 00` | unary `-` | [C] |
| `16` | 15 | `(lvl < 4) ?lvl:(2+lvl/3)` → `… 13 10 16 00` | `?:` | [C] |

- The encoding is **postfix** (`lvl+2` → `lvl`, `2`, `+`), operands before their operator: `[C]` in data/0005 by
  recompiling every stock cell; here the examples show it. Per pool: the item pool holds only `00 07 08` (all 45
  item cells are constants); the missile pool `00 01 04 07 08 10 12`; the skills pool all but `0B`; the skilldesc
  pool all but `02`.
- **Opcodes no stock string holds**: `05 06 09 0C 0D 0E 0F 14` (`<=` `>=` `==` `!=` `^` and the wide operands),
  `[I]` in data/0005 from the code only. The opcode range ends at `16`; no stock byte in opcode position is above it.
- Function indices (the byte after `01`) are per family: `0 1 2 3 5` occur in skills, `0 3 4 6` in skilldesc, `3` in
  missiles (data/0005 § 3 names them: skills and skilldesc `min max rand skill miss stat sklvl`, missiles
  `min max rand skill miss`, items `min max rand stat`).

## Constants folded

`[C]` A text with no variable and no call is stored as one constant: `-100` is `07 9C 00` (3 cells), `-37` is
`07 DB 00`, not `07 64 15 00` (data/0005 § 4, the compile-time fold through the evaluator).

## Open questions

- ~~The evaluator's semantics (integer width, division, the functions) are `[I]` in data/0005 and are plan 0035 Phase 2's
  run.~~ Run in Phase 2 ([data/0005 § 10](../findings/data/0005-calc.md#10-the-evaluator-at-run-time-phase-2-run2026-10-16-calc),
  run:2026-10-16-calc): `[C]` for the 14 stock opcodes, the skills contexts and the variables and functions the run
  computed; the missile and item contexts and the unreached paths (`max`, `rand`, the missile variable reader, the code-only opcodes, the zero divisor, the 32-bit wrap,
  the stack limits) stay `[I]` there. Written up in [specs/data/calc](../specs/data/calc.md) (reviewed).
