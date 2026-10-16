# 0035 — Data: the calc formulas (`*code.bin`, the compiler and the evaluator)

> **Status:** in-progress (approved 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments

## TL;DR

**Question:** what bytecode does the excel compiler write into `itemscode.bin`, `misscode.bin`, `skillscode.bin` and
`skilldesccode.bin`, which columns point into it, and how does the evaluator compute a value from it (opcodes, operand
stack, integer width, division and rounding, the function calls that read stats and skill levels)? When it is done:
- `docs/formats/calc.md` gives the bytecode encoding, `[C]` by recompiling every stock formula cell;
- `docs/findings/data/0005-calc.md` names the compiler and the evaluator with their opcodes;
- `tools/calc.py` compiles a formula text into the game's bytes and evaluates them;
- `docs/specs/data/calc.md` is drafted.

This is a static plan: most of it needs neither the harness nor Ghidra at the same time as other reverser phases. It
fills the gaps between harness phases.

## Context

- Research-map row `data/calc`: `not started`. Dependency `data/excel` reviewed.
- Nothing reviewed waits on it: [items/properties](../specs/items/properties.md) § Inputs and boundaries states that no
  property handler evaluates a formula (`[C]`, run:2026-10-14-props). The later rows may need it: cube `mod` lines,
  runeword `T1Code` parameters, CharStats or Hireling skill levels, and Misc `calc1..3`/`len`. Each of those plans
  names a calc evaluation as a boundary if it meets one; this plan removes the boundary.
- What exists:
  - [excel-bin.md § calc columns](../formats/excel-bin.md#calc-columns-formulas) (`[C]`): the item formula columns
    (`misc` `calc1..3`, `len`, `spelldesccalc`) hold an s32 offset into `itemscode.bin`, −1 when blank, in record
    order; constants compile to `07 nn 00` or `08 lo hi 00`, and `00` ends the expression. All 45 non-blank misc
    cells are constants. Other opcodes are not known.
  - [data/0001 § 3](../findings/data/0001-excel-loader.md) (`[I]`): `DATATBLS_LoadCodeBin` `0x00613E90` and
    `DATATBLS_LoadCodeLists` `0x00612750`; under `-txt` the files are written after itemstatcost, missiles, skills and
    skilldesc are compiled; `skillcalc` and `misscalc` are loaded only under `-txt`.
  - [data/0004](../findings/data/0004-cell-converters.md) (`[I]`): the calc cell callback is type `0x19`
    (`sub_00631530_ItemCalcCell`), the expression compiler is `0x006C1AE0` (not named), and a missing cell or a
    compiler return ≤ 0 gives −1.
  - The backlog entry of 2026-10-11 (archivist → reverser) on the four files is scheduled here.
- Data: `skillcalc.txt` and `misscalc.txt` (the function names the formulas call), and the `.txt` sources of every
  formula column, are in `workspace/merged/`. The `.txt`/`.bin` pairs are the decisive data: recompiling every
  formula cell and matching the stock bytes corroborates the encoding (evidence rule 2).
- Leads: none registered. Phase 1b searches for formula syntax documentation (the operator set, `skillcalc`
  functions), never for decompiled code.

## Phases

### Phase 0 — Formula columns and the byte survey
- **Owner skill:** archivist
- **What:** list every formula column in Skills, SkillDesc, Missiles, ItemStatCost, Misc and any other table, pair
  each `.txt` cell with its `*code.bin` bytes, and document `skillcalc` and `misscalc`.
- **Outputs:**
  - `docs/formats/calc.md` (first draft): the four files, the columns that index each, the byte strings per cell, and
    the opcode bytes seen with the formula texts they come from, `[L]` for meanings;
  - `docs/tables/SkillCalc.md` and `docs/tables/MissCalc.md` (code → function name lists);
  - `tools/calc.py survey` that prints, per file, cells by distinct opcode and the unexplained bytes; registered as a
    gate survey with a baseline.
- **Done when:** every offset in every formula column points at a byte string that the survey attributes to exactly
  one cell; every byte of the four files is covered by some cell's string (or listed as padding); the survey's opcode
  table lists each distinct byte with at least one example text.

### Phase 1 — Read the compiler and the evaluator
- **Owner skill:** reverser
- **What:** read the expression compiler `0x006C1AE0` (tokens, precedence, the function-name lookups) and find and read
  the evaluator (opcode dispatch, operand stack, integer width, division and modulo semantics, the comparison and
  ternary operators, the function calls and the stat/skill references they resolve).
- **Outputs:** `docs/findings/data/0005-calc.md`; `re/symbols.csv` rows (subsystem `data/calc`); `tools/calc.py
  compile` and `eval`.
- **Done when:** the finding states, with addresses and `[I]` or better, the grammar, every opcode with its operand
  bytes and its effect, the integer semantics (width, overflow, division by zero, rounding), and each `skillcalc`
  /`misscalc` function's meaning at least as "reads X from Y". `calc.py compile` reproduces the bytes of every stock
  formula cell from its text, 0 mismatches. This is `[C]` for the encoding (code read plus data behaviour).
- The evaluator's semantics stay `[I]` unless a static check corroborates them. Phase 2 is the runtime check.

### Phase 2 — Evaluate at run time
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  one slot, short sessions)
- **What:** log the evaluator's calls during ordinary play (skills cast, missiles fired, item descriptions shown) and
  check `calc.py eval` against them.
- **Logging:** each evaluator call: the offset, the context it reads (the unit, skill and level), every function
  call's return, and the result.
- **Done when:** a run `run:YYYY-MM-DD-calc` reproduces at least 500 evaluations covering every opcode the stock
  files contain (each opcode not reached is named), with 0 mismatches. The function calls' returns are logged inputs
  where they read game state outside this row (a named ADR-0004 boundary).

### Phase 3 — Spec: data/calc
- **Owner skill:** spec-writer
- **What:** write `docs/specs/data/calc.md` (the encoding, the evaluator, the function table), and link it from the
  data README, excel-bin.md and every spec that names a calc boundary by then.
- **Done when:** the spec follows the template, and every statement is tagged. It has the opcode table, the evaluator
  as pseudocode, and two worked examples (a stock skill formula and a Misc `calc` cell) from the run. The architect's
  review passes.

## Open questions

- What the skill and missile formulas compute in combat is out of scope (ADR-0002); this row specifies the machine
  that computes them, so the in-scope rows can call it.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-15 — Drafted and approved.** The owner asked for a queue of plans to run unattended, and approved all of
  them in advance. Written in the architect worktree `lane/plans0028`.
- **2026-10-15 — Phase 1 landed (reverser, `lane/r35p1`).** [data/0005](../findings/data/0005-calc.md) reads the
  compiler `CALC_Compile` `0x006C1AE0` (tokenizer, shunting-yard with the precedence table `0x006FC874`, constant
  folding through the evaluator), the three per-context name callbacks, the four cell callbacks and the pool append,
  the evaluator `CALC_Eval` `0x006C0BC0`, the run-time entry points (skills, skilldesc, missiles, items), the 15
  formula functions and the 73 `skillcalc` / 43 `misscalc` variable cases. `tools/calc.py compile` recompiles every
  formula field of the six tables (30 217 fields, 1 790 compiled cells, 1 failed one-space cell) with **0
  mismatches**, and rebuilds all four pools byte for byte: the encoding and the compiler are `[C]`. The evaluator is
  `[I]` except the three opcodes the compile-time fold exercises. Opcodes in the stock pools: `00 01 02 04 07 08 0A
  0B 10 11 12 13 15 16`; `05 06 09 0C 0D 0E 0F 14` are code-only. Surprises: the precedence test compares with the
  incoming opcode (a comparison before `?` is emitted after it), `-` after `,`/`(`/`?`/a function name is binary
  (so `min(-1,lvl)` fails to compile), an unclosed `(` is emitted as byte `02` (one stock cell, Fire Wall
  `EDmgSymPerCalc`), `m2eo`/`me3o` read the wrong description missile, and missile `rand` draws on a stack address.
  `calc.py` ends with a `SURVEY calc …` line; registering it is Phase 0's survey slot (backlog).
- **2026-10-15 — Phase 1 accepted with fixes (architect).** data/0005 meets every Phase 1 *Done when* item:
  `calc.py compile` rerun in review (30 217 fields, 1 790 compiled, 1 failed, 0 mismatches, four pools identical),
  and it derives the bytes from the `.txt` text (the `.bin` is only the comparison). Three anchors re-read with r2
  (`CALC_PushOperator` 0x006C18DE compares `prec[top]` with the incoming opcode; the precedence bytes at
  0x006FC874; the zero-divisor test 0x006C0EC6 pushes 0; `g_SkillsCalcFuncs` 0x00745774 = min/max/rand/skill).
  Fixes: the opcode and operand-width `[C]` limited to the opcodes in the stock pools (`05 06 09 0C–0F 14` `[I]`);
  the compiler quirks no stock cell exercises (unknown name → 0, `-` after `,(?:` binary, the ternary) moved to an
  `[I]` bullet, with the real copy-me ternary behaviour added (`?:` binds tightest and `:` flushes nothing, so an
  operator in an unparenthesised then-branch fails and an unparenthesised else-branch takes the whole ternary as its
  left operand); the incoming-opcode test noted as unobservable with this table (the review swapped it for the
  conventional test: same output for every stock cell); the `m2eo`/`me3o` wording made unambiguous; after the merge
  `0x00622560` keeps main's name `sub_00622560_PlayerBaseToHit` (the duplicate data/calc row dropped, 71 rows);
  `datatables.h` section references corrected. Evaluator semantics stay `[I]` for Phase 2. **Survey ruling:** the
  `SURVEY calc` line of `calc.py compile` is Phase 0's gate survey (backlog).
- **2026-10-15 — Phase 0 landed (archivist, `lane/a34p0`, after plans 0034 and 0032 Phase 0), review requested.**
  [calc.md](../formats/calc.md) (first draft): the four pools, the 90 formula fields that point into them (partial
  `missiles` and `skilldesc` layouts added with the descriptor offsets of data/0005 § 1, checked over every record),
  every one of the 10 497 pool bytes in exactly one of 1 790 cell strings, each string walked as opcodes to its end,
  the 14 opcode bytes seen with an example each, and every variable operand a row of SkillCalc or MissCalc named in
  the cell's text. [SkillCalc](../tables/SkillCalc.md) and [MissCalc](../tables/MissCalc.md) (4-byte code lists;
  layouts 0 mismatches). `tools/calc_survey.py` (`cells`, `ops`, `summary`; gate survey `calc_bytes`, per the
  architect's ruling a separate tool name; `tools/calc.py` is the reverser's and is not created here);
  `excel_layout` baseline regenerated (57 tables on this branch). Surprise: within a record the strings follow the
  `.txt` column order, not the field offsets (60 pairs, e.g. misc `len` before `calc1`, as excel-bin.md had noted).
  The opcode meanings are data/0005's, cited by address; links to it and the `calc` gate survey wait for
  `lane/r35p1` to merge.
- **2026-10-15 — Phase 0 accepted with fixes (architect review, `lane/a34p0`).** Done when met: `calc_survey.py
  summary` rerun (1 790 strings over 10 497 bytes, `bad_offset=0`, `shared=0`, `gap=0`, `walk_bad=0` in all four
  pools; the one −1 non-blank cell explained), and the opcode table lists the 14 stock bytes with an example each.
  SkillCalc and MissCalc diff 0 mismatches. After merging main the `calc` survey (`tools/calc.py compile`) is
  registered with its baseline next to `calc_bytes` (both green), and data/0005 is linked from calc.md, SkillCalc.md
  and MissCalc.md. No doc contradicts data/0005. Fixes: calc.md's meaning column scoped to the compiler's encoding
  (`[C]`), the evaluator's semantics staying `[I]`; the compile-order bullet corrected (below). **Compile order:** the
  pools follow the `.txt` column order in all 60 pairs where it differs from the field offsets, but the loaders'
  descriptors list those columns in the same order, so the data does not settle data/0005's open question. Read in
  review (r2): the only pairs where the descriptor order and the `.txt` order differ are skills `perdelay`
  (0x0061673B) before `skpoints` (0x00616C03) and `delay` (0x00616D88), and no stock row fills `perdelay` together
  with either. Stock pools come out the same under both walks; the question stays open for the reverser (backlog).
- **2026-10-16 — Phase 2 landed (reverser, `lane/h35p2`, slot 3), review requested.**
  [run:2026-10-16-calc](../findings/data/experiments.md#run2026-10-16-calc), [data/0005 § 10](../findings/data/0005-calc.md):
  14 sessions (one character per class: the skill tree hovered skill by skill, the hotkey skills cast in Cold Plains,
  three potions drunk); `tools/calc.py check` replays **44 529 evaluations, 0 mismatches**, 1 188 distinct cells, all
  **14 stock opcodes** executed (`02` by Fire Wall's unclosed `(`; `0A` and `?:` on both sides; 25 inexact negative
  divisions settle truncation toward zero). Not in the stock pools, so not reached: `05 06 09 0C–0F 14`. Computed and
  compared beyond the replay: 38 076 row-only variable reads, 682 formula-valued reads (one nested evaluation of the
  field in the same context), `min` 979, `sklvl` 50. ADR-0004 boundary: the unit-state reads (`skill`, `miss`, `stat`,
  `sklvl` over unit variables, 21 unit-reading `skillcalc` codes) are logged value oracles; no seed passes through the
  evaluator (`rand` never called). Not reached: `max`, `rand`, the missile variable reader, 30 `skillcalc` codes, the
  zero divisor, wrap, empty and full stack. Tags: `CALC_Eval`, `SKILLS_EvalCalc`, `SKILLS_EvalDescCalc`, the skills
  variable reader, `min`, `sklvl`, `SKILLS_DimReturns`, `g_SkillsCalcFuncs`/count `I` → `C` (9 symbol rows); the
  finding's evaluator, skills-context, `min`/`sklvl` and reached-variable bullets `[I]` → `[C]` (scoped), the rest
  stays `[I]`. Corrected from the run: `SKILLS_CalcVar`, `GetElemMin/Max/Len` and `GetToHit` call `CALC_Eval`
  directly, not through `SKILLS_EvalCalc`; `ITEMS_EvalCalc` ran only when a potion was drunk (0x005BEDA0). Tools:
  `tools/gdb/calc.py` + `calc.gdb`/`calc-field.gdb` (logger), `tools/calc.py check`, `tools/calc_sessions.py`
  (14 recipes, hover and cast steps).
- **2026-10-16 — Phase 2 accepted with fixes (architect review, `lane/h35p2`).** Done when met: the 14 logs match
  `calc-manifest.txt`; `python3 -I tools/calc.py check workspace/merged/data/global/excel <14 logs>` rerun in review →
  44 529 evaluations (≥ 500), 0 mismatches, 1 188 cells, all 14 stock opcodes executed (none of `05 06 09 0C–0F 14`
  occurs in a stock pool, so "every opcode the stock files contain" is complete), and the boundary is named. The
  checker computes the value from the stock bytes and only takes the logged values of reads and calls, after
  matching their order, index and arguments; row-only reads, `min`, row-only `sklvl` and formula links are computed
  too. Spot-checked with r2 on the pinned `Game.exe`: `CALC_Eval` called directly at 0x00646A07 (`SKILLS_CalcVar`),
  0x00644E02/0x00644EE1/0x00645007 (`GetElemMin`/`Max`/`Len`) and 0x00644A79 (`GetToHit`); 0x00647EC5 →
  `SKILLS_EvalCalc`; 0x005BEDFF/0x005BEF11 → `ITEMS_EvalCalc`; 0x004EDEEC → `SKILLS_EvalDescCalc`; the division case's
  `jmp 0x006C0D9D` at 0x006C0ED1 (the logger's ESP test). Every `[C]` raise in data/0005 names run:2026-10-16-calc;
  `re/symbols.csv` has no duplicate address or name (1 714 rows). **Rulings:** (1) value oracles with no seed: naming
  them is enough. ADR-0004's entry-seed assertion guards RNG state crossing the boundary; the evaluator draws only
  through `rand`, which no evaluation called, so no seed crossed, and the `[C]` is scoped to the evaluator and the
  computed reads, not the callees. The spec must present `skill`, `miss`, `stat`, unit-reading `sklvl` and the 21
  unit-reading variables as inputs. (2) `max`, `rand` and `MISS_CalcVar` stay `[I]` and do not block: the Done-when
  counts opcodes, and `max`/`rand` are function-table entries reached only by monster-skill cells (combat, ADR-0002);
  filed to the backlog with the item caller. (3) The § 6 corrections hold (r2 above). **The *What* said "item
  descriptions shown"**: the run hovered every potion and saw no evaluation; `ITEMS_EvalCalc` ran only when a potion
  was drunk, from `0x005BEDA0`. So the item context was exercised by drinking, not by the description: that is the
  finding, not a gap in the run (an item description does not evaluate a `calc` cell in these sessions), recorded as
  `[I]` with the caller unread. **Fixes (applied):** the `SKILLS_DimReturns` cap `min(r, b)` was never reached (every
  computed `dm` value had `r ≤ b`, levels 1–20; checked in review by wrapping the model), so the cap stays `[I]` in § 7.1
  and the symbol table note; the § 7.1 table tags raised to `C` for the reached row-only and formula codes, split where
  a row mixes reached and unreached codes (`mps usmc` / `mana`, `len` / `rng`, `clc1 clc4` / `clc2 clc3`); run anchors
  added to § 10's *Variables* and *Functions* bullets. **Merge note:** `docs/backlog.md` and
  `.claude/skills/reverser/references/tooling.md` conflict with main (both append-only text); `re/symbols.csv` merges
  clean. Phase 3 (spec-writer) is next.
