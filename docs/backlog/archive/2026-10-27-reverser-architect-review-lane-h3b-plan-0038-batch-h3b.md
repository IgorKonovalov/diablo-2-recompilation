---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../findings/data/experiments.md#run2026-10-27-sweep-data-load
  - ../../findings/data/0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../../findings/data/0002-mpq-precedence.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../../findings/data/0003-string-tables.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../../findings/data/0004-cell-converters.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
  - ../../findings/player/0001-creation.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load
resolution: "Accepted with fixes (9) at the lane/h3b review, 2026-10-27: the clamp half of strings 29 / excel 50 is [I] d-edit (raised in part); TC_BuildChestTable for TC_LoadAll at 0x0065A33B; the sounds-call and levels-writer addresses; DRLG_LoadLevels C in data/0001; totals corrected to static 567, harness 521, blocked 419 (1 526); probe logs and screenshots bookkeeping; S1b row 42 G1 post-pass label. Ledger raised 16, in part 9, shortfall 0. Spec-writer entry released; data/excel, data/strings and data/README Phase 3 ready. See plan 0038 log."
---

Review plan 0038 batch H3b (`data-load`; data/README 2–5, data/excel 1–8, 17–18, 20, 24–25, 27, 50, 71, 74,
data/strings 2, 6, 22, 29, and the S1b remainders of data/README 1 and data/excel 30; `lane/h3b`),
run:2026-10-27-sweep-data-load. Seven program runs on slot 2 (stock, txt, loose, direct, dtxt, rus, clamp), gdb on the
game before its startup code. Manifests `workspace/logs/h3b/h3b-manifest.sha256` (`0b75400a…`; logs, dumps, driver outputs, `check/`; 88 files)
and `h3b-manifest-dev.sha256` (`73e35bff…`, from `workspace/logs/h3b/dev`). Re-run: `python3 -I tools/h3b_sessions.py
stage --slot 2` (recreates the loose files byte for byte; no game is started), `python3 -I tools/sweep_h3b.py check
--written workspace/logs/h3b/check/txt-written-bins-h3b-dtxt.txt <the seven logs>` (about 10 min, under
`MemoryMax=4G`; `check/check-h3b.txt`, `TOTAL bad=0`), `unstage --slot 2`; `txtfiles` and `tools/tbl.py check` outputs
are kept. Tool hashes in `check/tools-at-run*.sha256` and `check/tools-at-check.sha256`.

Ledger of the 25 statements: **raised 18, raised in part 7, shortfall 0** (inventory § 2.6 H3b block); the two S1b
remainders: README 1 raised, excel 30 raised in part with a correction. No class move.

Points for the ruling:
- (a) **Ruling 3's start mode:** `tools/d2run.py --early` (SIGSTOP once `game.exe` is mapped, then attach; the driver
  waits for the window). It works; a gdb file used with it needs `set displaced-stepping off` (the probe without it ended
  the game at its second breakpoint, exit code 5). Documented in the reverser tooling reference.
- (b) **README 5 / excel 8 correction:** `TC_GetByName` has no reference in the image and 0 hits; the name → TC map is
  `[C]` through the direct `EXCEL_FindName` callers. Filed raised in part with the dead half as a d-none remainder (the
  H4b `GameCreateA` precedent); whether the entry-point rows should instead name the real callers is the spec-writer's.
- (c) **Excel 30's correction:** `hitclass.bin` is read whole at every start by the character-graphics loader
  (0x0050448A), so "a stock run never loads them" holds only for `DATATBLS_LoadTable`; a 2-byte `sounds` call is an 18th
  `-txt`-only call.
- (d) **Excel 71's refinement:** levels `+0x033..+0x035` are also filled at load (model exact); the J4 list omits them.
- (e) **Excel 50 / strings 29 raised whole:** two loose `use` bytes under `-direct` (0x0B → 11, the run ends at the
  `CYR` font map; 0x0E → 0, a normal run) separate the byte read and the clamp, which the route had left code-read. The
  rus run also corrects data/0003 § Language ("would crash at `string.tbl`": it ends at the font map first). These two
  runs and the loose/direct pair use loose files the game reads or ignores; no claim rests on an edited table cell
  (ADR-0013): the loose `.bin` only adds 4 bytes after the records, and the `.tbl` variants are tbl_crc_case's.
- (f) **Excel 27 raised whole** with a `-direct -txt` run (dtxt) added to the plan's `-txt` case: one separating table
  (`monstats.bin`, the compile's two bytes) in each direction.
- (g) Symbols I → C (rule 14): 18 rows (the archive, lookup and load functions, `LNG_GetLanguageIndex`,
  `STRTABLE_LoadAll`/`Unload`, `DATATBLS_LoadAll`/`LoadCodeLists`, `ApplyTxtOption`, `InitFileIO`, `GEMS_Load`,
  `MONEQUIP_Load`, `DRLG_LoadLevels`, `RecWideNameFill`); `TC_GetByName` stays I.
- (h) The spec-writer entry
  [2026-10-27-reverser-spec-writer-h3b-data-load-raises-and-corrections](../2026-10-27-reverser-spec-writer-h3b-data-load-raises-and-corrections.md)
  is held for the review.
