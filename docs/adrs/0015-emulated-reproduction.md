# ADR-0015 — Emulated reproduction: the binary's own code under the p-code emulator, with a declared memory image

> **Status:** accepted
> **Date:** 2026-10-16
> **Amends:** [ADR-0003](0003-runtime-experiments.md) (its rejected alternative "extending the p-code emulator", narrowed)
> **Related plan(s):** [0035-data-calc](../plans/done/0035-data-calc.md) (its leftovers, run:2026-10-16-calc-emu); every later plan with code the harness can't reach

## Context

Evidence rule 4 (ADR-0001, `references/evidence-rules.md`) accepts bit-exact reproduction: a `tools/` model gives
identical outputs to the binary for recorded inputs. Since plan 0001 the binary's side has two forms. The harness
(ADR-0003) logs the unmodified game under wine. Ghidra's p-code emulator runs one function of the pinned image on
inputs we choose (run:2026-10-11-rng-emu, the RNG primitives). ADR-0003 kept the emulator "the method for pure
functions" and rejected it for structure-walking code, because that code "needs a faithful game state to start from,
which only the running game has".

run:2026-10-16-calc-emu goes past that line. `EmuCall.java` writes a declared memory image before each call
(`g_pDataTables` pointed at a scratch DataTables with missile records, a scratch unit), then runs `MISS_CalcVar` and
`MISS_EvalCalc` on it, with `CALC_Eval` and `SKILLS_DimReturns` reached as callees. Some records are random bytes, not
stock rows. The stock game never reached this code in a harness session, so emulation is the only route to `[C]` short
of a cast the plan did not budget.

Three things differ from a harness run. The memory is ours, so it shows what the code does with those bytes, not that
the game ever holds them. Ghidra's x86 semantics (SLEIGH) are a tool dependency, and the decompile we read is built
from the same p-code, so the emulator catches a misreading of the code, not a lifter error. The emulator does not
model faults, the operating system or x87 precision exactly.

## Decision

A run of the pinned image's own code under Ghidra's p-code emulator, compared bit for bit with a `tools/` model,
counts as evidence rule 4 when it meets these conditions. **(1) Unmodified code.** No instruction is patched or
stubbed: every callee the cases reach runs emulated, or is a logged boundary oracle under ADR-0004's rules. The memory
spec writes data only. **(2) Declared read set.** The finding names every memory the emulated code reads beyond its
arguments, the stack and the memory spec, and shows each one is image data no code writes at run time (a function
table, a constant), with the reference check that shows it. A read the record does not account for voids the claims
that depend on it. **(3) Scope of the `[C]`.** It covers the code as a map from its arguments, the bytes it reads and
the seed states to its return value, the bytes it writes, the seeds' exit states and the bytes it pops. It does not
cover what the game's memory holds at run time: the meaning of each offset read (a table column, a struct field)
carries its own tag, from a parser or column check (rule 2), a second code path or a run. It does not cover who calls
the code, when, or on which live seed in play. **(4) Synthetic inputs are admitted.** Random records and values are
admitted and preferred for coverage, since the code's output is a function of what it reads: a stock row is one point
of the same input space. Each branch a `[C]` claims is reached by at least one case, the record lists the branches
reached and not reached, and a negative control (a sibling function's output, or a perturbed model) shows the checker
fails when it should. A claim about the stock data itself ("no stock formula calls `rand`") remains a data claim,
checked against the stock table. **(5) Tool limits.** The record names the Ghidra version. Faults and exceptions
(divide error, access violation), x87 floating-point results, calls into imports and the operating system, and
self-modifying code are not evidenced by emulation and stay `[I]` unless a run shows them. Where a claim turns on an
instruction with subtle semantics (flags consumed across instructions, shifts by 32 or more, `rep` string forms,
segment-relative reads), the finding also cites that instruction from an r2 disassembly, so the claim does not rest
on the lifter alone. A known SLEIGH defect that touches a claim demotes it. **(6) Pure functions** (no memory spec
beyond a seed or argument block) were already the ADR-0003 method; conditions (3), (5) and the negative control of
(4) apply to them too from now on.

## Consequences

### Positive

- Code the stock game reaches rarely or never in a budgeted session (a monster skill, an unused missile column, an
  edge of 32-bit arithmetic) reaches `[C]` without a forced-path table edit (ADR-0013) and without the harness.
- Random inputs cover branches and wide values that stock data never exercises, so a reimplementer gets the code's
  behaviour, not only its behaviour on today's tables.
- Every emulated run is repeatable from the record alone: no wine, no timing, no slot.

### Negative

- **A shared blind spot with the decompile.** If Ghidra lifts an instruction wrongly, the decompile and the emulator
  agree on the wrong answer. The r2 citation of condition (5) narrows this for the subtle cases only; ordinary integer
  arithmetic, moves and branches rest on SLEIGH's x86 model.
- **The memory image is our reading.** A wrong struct offset in the memory spec and the same wrong offset in the model
  agree, and the run passes. That is why condition (3) leaves offset meanings to their own evidence; a reader of a
  `[C]` from emulation must check that the offsets it relies on are themselves `[C]`.
- **No run-time context.** An emulated `[C]` says nothing about when the code runs in play or with which seed. A spec
  that needs that (simulation, ADR-0014) still needs a harness event.
- **Unaccounted reads are not trapped by the tool.** Condition (2) is checked by reading the code, not by the emulator;
  `EmuCall.java` does not yet fail on a read outside the spec and the image.

### Neutral

- This is an operational reading of evidence rule 4, like ADR-0004, not a new evidence form; rules 1 to 3 and the
  harness method of ADR-0003 are unchanged. Structure-walking code that needs the live game state (a level, a room, a
  monster's AI) still goes to the harness: the conditions above are met only when the read set is small enough to
  declare.

## Alternatives considered

**Keep emulation to pure functions (ADR-0003 as written)** and leave `MISS_CalcVar` and `MISS_EvalCalc` at `[I]` until a
harness session casts the rare skills. Rejected because the harness would add nothing to the function's own claims:
the same code runs on the same bytes, and the run would only reach the handful of stock values one cast produces,
while the emulated cases reach every code and the wrap cases.

**Admit emulation only on stock tables.** Rejected because a stock row is one point of the same input space, and
random records are what make every offset distinguishable (a stock column holding 0 in every row can't tell two
offsets apart). The stock-data claims keep their own check under condition (4).

**Require a second emulator or disassembler to run the code** (unicorn, a native harness of the function). Rejected
for now as cost without a known defect to justify it; condition (5) covers the instruction classes where lifters are
known to differ, and a defect found later demotes the claims it touches.
