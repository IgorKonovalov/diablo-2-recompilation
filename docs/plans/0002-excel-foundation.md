# 0002 — Excel foundation: which data the game actually reads

> **Status:** draft
> **Created:** 2026-10-11
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers

## TL;DR

Every table-driven spec rests on four open questions: whether the game reads the `.bin` or the `.txt`
form of each table, which treasure-class table is live, the MPQ precedence order, and how a code
(`"weap"`, `"hax"`, a TC name) becomes a record index. This plan answers them, and documents the
record layouts of the tables `items/tc` needs. When it's done, `docs/findings/data/0001-excel-loader.md`
answers the backlog questions, `docs/tables/` holds one doc per item-drop table with every `.txt` column
mapped to its `.bin` offset, and `docs/specs/data/excel.md` is drafted.

## Context

- Research-map row `data/excel` (ADR-0002 enabler), status `not started`. Its only dependency is
  the merged data tree from plan 0001 Phase 3 (`[C]` counts, layouts unknown).
- Backlog questions this plan closes (all from archivist → reverser, 2026-10-11): `.bin` vs `.txt`
  and the five mixed-archive tables; `TreasureClass` vs `treasureclassex`; MPQ open order and
  `d2kfixup`/`d2delta`; loose files and `-direct`; the `data\local\use` byte. The `*code.bin`
  question goes to `data/calc`, a later plan, unless the loader answers it in passing.
- It also answers an open question in finding `rng/0002`: which table column the level-definition
  `+0x30` (generator type 1/2/3) and `+0x34` fields are.
- The table set in Phase 1 is the `items/tc` set (plan 0004). Later plans add their own tables
  using the decoder this plan builds.
- Leads: none registered. The 1.10+ split of `Levels` into `leveldefs.bin` is `[L]` (excel-bin.md).

## Phases

Phases 1 and 2 are independent and can run in parallel. Phase 2's corroboration step uses
Phase 1's record sizes, which the survey already has.

### Phase 1 — Record layouts and table docs for the item-drop tables
- **Owner skill:** archivist
- **What:** Build a generic `.bin` record decoder and map every `.txt` column to its `.bin` offset and
  type for `treasureclassex`, `itemratio`, `itemtypes`, `weapons`, `armor`, `misc`, `monstats`,
  `levels` and `leveldefs`. Diff the `.bin` and `.txt` of `automagic`, `RarePrefix` and `RareSuffix`
  cell by cell.
- **Outputs:** `tools/excel_bin.py` (layout-driven decoder plus a txt↔bin cell diff),
  `docs/tables/<Table>.md` for the nine tables (template: `table-doc-template.md`), and updated
  `docs/formats/excel-bin.md` (encoding rules for strings, codes, blank cells, the `0xFF` defaults).
- **Done when:** for each of the nine tables, `tools/excel_bin.py diff` reports zero unexplained cell
  mismatches over every record, which makes each mapped field `[C]` by data behaviour. Fields with
  no `.txt` column (runtime-filled or derived) are listed as unknown, not guessed. `leveldefs` `+0x30`
  and `+0x34` are matched to a `Levels.txt` column, or reported as having no match. The three
  mixed-archive diffs are written up, with the changed cells listed.

### Phase 2 — The excel loader, TC table choice, MPQ precedence
- **Owner skill:** reverser
- **What:** Find the loader behind `.\Src\Excel\Excel.cpp` / `%s\%s.bin` and the table-registration
  list it walks, plus the MPQ open sequence. Answer the backlog questions from the code.
- **Outputs:** `docs/findings/data/0001-excel-loader.md`, `docs/findings/data/0002-mpq-precedence.md`,
  and `re/symbols.csv` rows (subsystem `data/excel`) for the loader, the registration list, the
  code→index lookup and the per-table global pointers of the nine Phase 1 tables.
- **Done when:**
  - `.bin` vs `.txt`: answered, including any switch that changes it, and the authoritative side named
    for each of the five mixed-archive tables. `[I]` minimum.
  - TC table: which of `treasureclass` / `treasureclassex` is loaded into the structure the drop code
    reads. `[I]` minimum. Plan 0004 starts only after this.
  - Record sizes: for every table the loader registers, the record size in its descriptor equals the
    archivist's `.bin` record size from `docs/tables/README.md`. Check all 88. That corroboration takes
    the "fixed-size record" claim and the table-to-pointer mapping to `[C]`.
  - Code→index lookup: the function that turns a 4-char item code or a TC name into an index is named,
    with its collision behaviour (first match wins? hash?) stated.
  - MPQ order: open order and priority, `d2kfixup`/`d2delta`, loose files and `-direct`, and the
    `use` byte, each answered `[I]` or better, or recorded as a dead end with what was tried.
  - The five backlog entries are struck through, each with a link to its answer.

### Phase 3 — Spec: data/excel
- **Owner skill:** spec-writer
- **What:** Write `docs/specs/data/excel.md`: which form is loaded, MPQ precedence, how records are
  addressed, the code→index lookup, the blank-cell defaults, and which TC table is live. Per-table
  layouts stay in `docs/tables/` and are linked from the spec, not copied.
- **Outputs:** `docs/specs/data/README.md`, `docs/specs/data/excel.md`.
- **Done when:** the spec follows the template, every statement is tagged, and the architect's review
  passes.

## Open questions

- Deferred: the `*code.bin` bytecode (`data/calc`). If Phase 2 sees how a formula column is resolved,
  record it in the finding, but don't chase the VM.
- Deferred: layouts for every other table. Each later plan adds the tables it needs through
  `tools/excel_bin.py`.
- `objects.txt` duplicate and missing `Id`s: out of scope here, belongs to the `objects` plan.

## Implementation log

_(lanes append dated entries as phases land)_
