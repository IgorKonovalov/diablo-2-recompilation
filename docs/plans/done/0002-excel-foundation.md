# 0002 — Excel foundation: which data the game actually reads

> **Status:** done
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

- **2026-10-11 — Approved (human).** No phase started yet.
- **2026-10-11 — Phase 1 landed (archivist).** `tools/excel_bin.py` (+ `excel_layouts.py`, `tbl.py`):
  `diff` reports 0 unexplained mismatches over every record of the nine tables (one explained: the
  monstats `Lilith` string key). Every column mapped `[C]` by data, `[I]` where constant; unknown
  fields listed per table doc. `leveldefs +0x30 = DrlgType`, `+0x34 = LevelType`. automagic/rare
  `.bin` differ from d2exp in record format only, not content. Surprises: TC items stored as text;
  monster refs use the distinct-Id position (duplicate `cr_lancer8` shifts later monsters);
  monstats TCs are row + 161. Encoding rules in `excel-bin.md`; four reverser questions in the backlog.
- **2026-10-11 — Phase 2 done (reverser).** Findings [data/0001](../../findings/data/0001-excel-loader.md)
  and [data/0002](../../findings/data/0002-mpq-precedence.md). The game always reads `.bin` `[C]`; `-txt`
  recompiles `.txt` to loose `.bin` files, which only `-direct` picks up `[I]`. `treasureclassex` is the
  only TC source `[C]`: its numbering (0 empty, 1–160 generated, then TCEx rows) matches all 4362
  monstats TC cells. Record sizes 86/88 match with 0 mismatches; `cubemod` and `cubetype` are never
  loaded. MPQ precedence patch_d2 (5000) > d2exp (3000) > d2kfixup/d2delta/d2data (1000) `[I]`.
  `leveldefs` +0x30/+0x34 = `DrlgType`/`LevelType` `[C]`. 87 symbols under `data/excel` and `data/mpq`.
- **2026-10-11 — Phase 3 drafted (spec-writer).** [specs/data/README.md](../../specs/data/README.md) and
  [specs/data/excel.md](../../specs/data/excel.md) from data/0001–0002, the format docs and the nine table
  docs. excel.md tags C 20 / I 70 / L 8, all `[L]` under Open questions (runtime `-direct`/`-txt` check,
  monster-reference readers, auto-TC filter and naming, string lookup…). Backlog entries to reverser
  and archivist. Awaiting architect review.
- **2026-10-11 — Reviewed and closed (architect).** Verdict: **accept with fixes**; no blocking finding.
  Phase 1: `tools/excel_bin.py diff` re-run over the nine tables plus `automagic`: 0 unexplained
  mismatches everywhere, one explained (monstats `uberandariel` `NameStr`). Phase 2: anchors re-read in
  the disassembly. `g_DataTblsLoadBin` `0x00744308` is initialised to 1 and has 30 references, all `cmp`;
  `-txt` → `0x0044D9C0` → `0x006125A0` stores `cfg[0x215] != 0`. `EXCEL_FindCode`/`EXCEL_AddCode` use an
  unsigned compare, and a duplicate code goes to `code + 1` and is retried. `TC_BuildAutoTCs` allocates `""`
  first and loops the levels 3..96. `TC_LoadTreasureClassEx` stops at the first empty name and the first empty
  `ItemN`, sets `picks` 0 to 1 and adds the auto-type count to a non-zero `group`. `TC_ParseItemCell` tries an
  item code (≤ 4 chars), then a TC (≥ 1), a unique (≥ 1) and a set (≥ 0). The MPQ open order and priorities match
  the code: 7 × `0x3E8`/`0x1388`/`0xBB8` pushes, and a tie is inserted at the first node with `prio ≤ new`. The
  monstats getter at `0x006538A0` indexes `idx × 0x1A8` with a count bound. All 56 distinct `fn:`/`data:` anchors in the
  findings and specs resolve in `re/symbols.csv`. No game data and no provenance wording in tracked files.
  Follow-ups are in the backlog. **spec-writer:** small precision fixes in `excel.md` (quote handling in G4,
  the return value of F4, the G2 filter list) and the frontmatter set to `reviewed`. **reverser:** the
  `TC_BuildAutoTCs` details for plan 0004. **archivist:** remove the `[L]` lines that these findings
  superseded. Research map `data/excel` → `reviewed`.
