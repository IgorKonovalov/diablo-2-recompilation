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
