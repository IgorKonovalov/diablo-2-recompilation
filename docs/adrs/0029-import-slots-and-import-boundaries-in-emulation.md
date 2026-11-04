# ADR-0029 — Imports in emulated reproduction: a declared stand-in in an import slot, and a stop at an import's call

> **Status:** accepted (owner, 2026-11-04); drafted by the architect at the `lane/r60c` review
> **Date:** 2026-11-04
> **Amends:** [ADR-0015](0015-emulated-reproduction.md) (conditions (1) and (5)), [ADR-0021](0021-observed-boundaries-in-emulation.md) (condition (a))
> **Related plan(s):** [0060-item-use-inventory](../plans/0060-item-use-inventory.md) (Phase 1.3)

## Context

ADR-0015 (1) says "no instruction is patched or stubbed: every callee the cases reach runs emulated, or is a logged
boundary oracle", and (5) says calls into imports are not evidenced by emulation. ADR-0021 added a third treatment, a
stop at a callee's entry, and rejected a synthesised return value as "a stub, which condition (1) forbids". None of the
three treats an import that sits in the middle of the code a claim is about, where the image holds no code to run.

run:2026-11-04-ground-emu meets this twice. `GroundDropCell` allocates 8 bytes through the shared pool on every call
(`0x00555DEA`, `0x0064DEE8`), before its search, and the allocator calls `EnterCriticalSection` and
`LeaveCriticalSection`. The `drop` family writes `0x0066A250` into their import slots (`0x006CC218`, `0x006CC214`), and
those bytes are `C2 04 00`, `ret 4`, in the image. The spec writes data only and no instruction changes, but in
substance the two callees are stubbed, so the family does not meet (1) as written. A stop at the first lock would end
the case before the search. The `dispatch` family stops at `0x0054D7DC`, the `call` of the `IsBadCodePtr` import, which
is not the "function entry" of ADR-0021 (a). `tools/path_emu1.py` observed the same import at its slot's value.

This is not new. run:2026-10-30-frame-emu-3's `timers` family gives the `IsBadCodePtr` slot a game function that
returns `EAX` = 0 and pops one argument (`0x004BAD70`), stated in its record and raised in frame/0003, and the
`lane/r55c` review accepted it without a ruling. There the caller branches on the value, so it is the stronger case.

ADR-0021's first alternative already answers how to settle it: "widening an evidence rule by reading belongs in an ADR,
not in a review". So a limit stated in a finding is not enough, however harmless the stand-in looks.

## Decision

An emulated case may pass through an import, or stop at it, on these terms; ADR-0015 and ADR-0021 are otherwise
unchanged. **(a) A no-result import may hold a pop-only stand-in.** A memory spec may write an import slot with the
address of an image instruction that only pops that import's stdcall arguments (`ret n`), when the import's documented
prototype returns nothing. The finding cites the slot's import name from the PE import table, the stand-in's bytes from
a disassembly, and `n`; and a kept scan over every call of that slot in the functions the cases can reach shows that no
code reads `EAX`, `ECX` or `EDX` before writing it. **(b) A result-returning import may hold a stand-in only as a
declared input.** The stand-in is an image function with the import's pop count that returns one constant; the case's
`[C]` reads "given the import returned `v`", and `v` itself, and every branch on another value, stay `[I]`. **(c) A stop
at an import's call.** An observed boundary on an import may be the `call` instruction itself, or the slot's value. The
checker asserts that the case reached that address and compares what the claim uses in the registers and on the stack,
and ADR-0021's "nothing after the call" holds. **(d) Stated per family.** The finding's head and the run record name each
slot, its stand-in and the families that use it, and the head lists what is not evidenced: what the import does
(mutual exclusion, another thread's order, a wait, a fault), and any code run only because of it on a declared state, such
as the allocator on a declared pool page, which reaches `[C]` for no state and no branch of its own. The `[C]` holds only
where no output of the claim depends on those, so the checker compares no address the allocator chose. **(e) Which
imports.** Rule (a) admits synchronisation imports with no result. Rule (b) admits a test whose result only selects a
fatal path, like `IsBadCodePtr`. Neither admits a file, time, thread or memory import whose result a claim would use. A
new slot in a later run is a reviewer's check under these rules, and a new ADR only when it falls outside them.

## Consequences

### Positive

- `GroundDropCell` runs through its real allocator to its return, so the search's rings, base room and walk are checked
  jointly (4 000 cases, 15 controls). Without this they rest on Phase 2's cases 1 to 6 and on the `line` family for the
  walk alone.
- The statements of items/0014 headed `[I] (drop, pending ADR-0029)`, and `dispatch`'s passing half, rise to `[C]` with no
  re-run on acceptance: the scan of (a) was made at the review (25 lock calls in `0x00409770..0x0040A080`, none reads a
  volatile register first), but it must be kept as a lane tool output when the raise is made.
- frame/0003's `timers` `[C]` gets the ruling it did not have, as case (b).

### Negative

- **The allocator is left unevidenced where it runs.** A reader could take "runs its own code" for coverage of it; rule (d)
  says it is not. Any claim about pool behaviour needs its own evidence.
- **A stand-in is a stub by another name, within narrow limits.** The rule rests on the claim's output not depending on
  the import; a wrong dependency analysis is not caught by the emulator. The scan covers registers, not a shared memory
  effect, so a lock that guards memory the claim reads would be a hole; the declared image has no second thread, so any
  such dependency is invisible in the run. A game run (Phase 2) is the only check on it.
- **(b) lets a return value in**, which ADR-0021 rejected for the code after a callee. It is narrower here: the value is
  named in the claim, and other branches stay `[I]`.

### Neutral

- A further operational reading of evidence rule 4, like ADR-0004, ADR-0015 and ADR-0021. On acceptance,
  `references/evidence-rules.md` § the emulator paragraph gains one sentence, and that edit is Tier A.
- Until acceptance, claims that rest on (a) or (c) are `[I]`, as ADR-0021 did for its own. `frame/0003`'s `timers` keeps
  its tag meanwhile, since this review did not re-read that lane.
- If the owner rejects this, items/0014's `drop` statements stay `[I]` until Phase 2, and `timers` drops to `[I]`.

## Alternatives considered

**A stated limit, with no ADR.** The lane's own proposal. It lost on condition (1)'s word "stubbed": a slot write that
makes a callee return at once does what a stub does, and ADR-0021 already held that reading a condition wider is an
ADR's job.

**Enter `COLL_FindFreeNear` with `other` null, which allocates nothing, and leave the walk to `line`.** Covers the rings
and masks with no stand-in, but never joins them: every control that needs a walk inside a ring (`noline`, `lineroom0`,
`linecellmask`) would lose its meaning, and `GroundDropCell` always passes an origin. Kept as what a re-run would do if
the owner rejects and Phase 2 cannot reach a claim.

**An observed boundary at the first lock.** Ends each case before its first cell test, so it says nothing about the search.

**Model the lock instead of skipping it** (a counter in the spec). The image holds no such code to run, and a model of the
OS in the spec would be our reading presented as the binary's behaviour.
