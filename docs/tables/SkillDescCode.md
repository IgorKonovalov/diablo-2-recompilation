# SkillDescCode (`data/global/excel/skilldesccode.bin`)

> **Source archive:** `.bin` patch_d2
> **sha256:** `.bin` `67c82fa8660fd2f74c46a5dc3cc60de29a60f7c104602270499a438cff2e467e`
> **Doc status:** shape complete (plan 0068 Phase 1); bytecode meaning in [data/0005](../findings/data/0005-calc.md)

## Purpose

The header-less pool of compiled formula strings of one table family (skilldesc). A formula cell of those tables (a damage, a range, a level-scaled value) is compiled into a short bytecode string at `.txt`-compile time; the strings are concatenated into this file and the table's record stores each string's offset (`s32`, -1 for none) ([calc.md](../formats/calc.md)). The file is read raw by `DATATBLS_LoadCodeBin` (with `skillscode`, `0x00617946`/`0x00617961`), not through the table loader ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300), `[I]`). The format, the opcode table and the evaluator are in [calc.md](../formats/calc.md), [data/0005](../findings/data/0005-calc.md) and [data/calc](../specs/data/calc.md); this doc exists so that every file in `data/global/excel/` has a table doc.

## Row identity

- `[C]` There are no rows and no count header: the file is 4 252 bytes of bytecode ([excel-bin.md](../formats/excel-bin.md)). The `excel` survey lists it under `no_count_header`.
- `[C]` 867 compiled strings, 9 282 formula fields checked, all pointing into the file (`python3 -I tools/calc_survey.py summary workspace/merged/data/global/excel`, [calc.md](../formats/calc.md)).

## Columns

None: the file is bytecode. The columns that point into it are the 42 formula columns of [SkillDesc](SkillDesc.md).

## Interpretation notes

- The count of formula fields, strings and the walk of every string are checked by the gate surveys `calc_bytes` and `calc` (`tools/calc_survey.py`, `tools/calc.py`), the pools being rebuilt from the `.txt` by the compiler model. No record count applies.

## Open questions

None for the file; the opcode meanings are in data/0005.

