# ADR-0021 — Observed boundaries in emulated reproduction: a case may end at a declared callee's entry

> **Status:** proposed (drafted by the architect at the `lane/p46m1` review, 2026-10-20; for the owner)
> **Date:** 2026-10-20
> **Amends:** [ADR-0015](0015-emulated-reproduction.md) (conditions (1) and (3))
> **Related plan(s):** [0046-skills-function-catalogue](../plans/0046-skills-function-catalogue.md) (Phase 1, batch 9a and later)

## Context

ADR-0015 condition (1) gives a callee that an emulated case reaches two treatments: it "runs emulated, or is a logged
boundary oracle under ADR-0004's rules". An ADR-0004 oracle logs the callee's entry state, arguments, exit state and
return value, and the model continues from the logged exit. Condition (3) scopes the `[C]` to the code as a map onto
"its return value, the bytes it writes, the seeds' exit states and the bytes it pops".

Plan 0046's catalogue functions mostly end in a call whose read set cannot be declared: `MissileCreate` (a unit
allocation), the path planner, a monster spawn, an item creation, the do-1 step. Batch 9a
([skills/0004 § 2](../findings/skills/0004-missile-do-1-18.md#2-emulation-boundaries-instead-of-callees),
run:2026-10-20-cat-emu-9a) used a third treatment: `EmuBoundary.java` (`EmuTrace.java` plus an `observe <addr>`
directive) ends a case when the program counter reaches a declared callee's entry and prints the registers and the
64 bytes at ESP (return address, then the stack arguments); the stack and spec memory are dumped as usual. Nothing is
patched and the callee never runs, so no output of the case depends on a callee's behaviour. But the case has no
return value, and its outputs are the arguments of a call, partly in registers, which neither condition names. Read
as written, the method meets neither half of (1); in substance it is ADR-0004's entry half (entry state and arguments
predicted and asserted) without the continuation, which is only needed for claims after the call.

## Decision

A case may end at an **observed boundary**: a callee entry named in the memory spec, at which the emulator stops
before executing the callee's first instruction and records the registers, the stack arguments and the memory dumps.
An observed boundary satisfies condition (1) when (a) no instruction is patched and the boundary is a function entry
reached by the program's own control flow; (b) the checker asserts, per case, which boundary was reached and from
which call site (the return address at ESP, or the case's own return sentinel for a tail jump), and fails a case that
reaches a different boundary, a different site, or returns when the model predicts a boundary (and the reverse);
(c) the model predicts and the checker compares every argument the claim uses, in registers and on the stack, every
byte written before the call that the claim uses, and the state of every seed the code touched, at the boundary. Under
condition (3) the `[C]` of such a case covers the code as a map from its inputs to the boundary reached, its call
site, those arguments, those bytes and those seed states; it covers **nothing after the call**: not the callee, not
the caller's code after the callee returns, not the caller's return value. The finding states, per claim, which
boundary it ends at, and lists the code after each boundary as not covered. Conditions (2), (4), (5) and (6) apply
unchanged; the boundary's arguments are hand-off values, and what they mean to the callee keeps its own tag
(ADR-0004's "hand-off arguments stay `[I]`").

## Consequences

### Positive

- Functions whose last act is an undeclarable call (most of the catalogue) reach `[C]` on everything they do before
  it, without a harness session and without stubbing the callee.
- The record is still repeatable from the cases and the memory spec alone; the callee's own plan can later replace
  the boundary with an emulated run or an ADR-0004 oracle and re-check the same cases.

### Negative

- **Code after a boundary stays `[I]`.** A function that calls two undeclarable callees in sequence is covered only up
  to the first one a case reaches; what it does between them needs other cases (a path that skips the first) or a
  run. Claims of the form "then do 1" after a creation are not covered on the creating path.
- **The call site matters.** A function that calls the same boundary from two sites could pass on the wrong one unless
  (b) is checked; batch 9a's checker tests the boundary but not the site (one site per function and boundary in its
  kept outputs, checked at the review), so later batches add the site to the checker.
- **No return value.** A claim about what the function returns on a boundary path ("returns do 1's value") is not
  evidenced by such a case.

### Neutral

- This is a further operational reading of evidence rule 4, like ADR-0004 and ADR-0015; it adds no evidence form.
- Until this ADR is accepted, claims that rest on observed boundaries are `[I]`; on acceptance they rise to `[C]`
  without a re-run, since the run record already meets (a) to (c) except the call-site check of (b), which the
  review of `lane/p46m1` made from the kept outputs.

## Alternatives considered

**Read ADR-0015 (1) as already admitting it** (the observed callee is never "reached" in the sense of being run). It
lost because condition (1) names exactly two treatments and condition (3)'s outputs do not include a call's register
arguments; widening an evidence rule by reading belongs in an ADR, not in a review.

**Require an ADR-0004 oracle at each boundary** (log or synthesise the callee's exit and continue). It lost because
under emulation there is no logged game exit to take: a synthesised return value would be a stub, which condition (1)
forbids, and the claims after the call would rest on it.

**Emulate the callees with a wider memory image.** Kept as the route for the code after each boundary, but not
required: `MissileCreate` and the spawns allocate units and walk rooms, whose read sets ADR-0015 already sends to the
harness.
