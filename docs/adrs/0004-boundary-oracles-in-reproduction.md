# ADR-0004 — Bit-exact reproduction across an out-of-scope callee: logged boundary oracles

> **Status:** accepted
> **Date:** 2026-10-11
> **Related plan(s):** 0004-items-treasure-classes (Phase 2); every later items/monsters plan

## Context

ADR-0001 accepts bit-exact reproduction as corroboration (evidence rule 4): a `tools/` model gives
the same outputs as the binary for recorded inputs. Plan 0004 Phase 2 asks `tools/tc.py` to reproduce
50 resolver calls including the **final seed state**. Phase 1 found that the resolver
(`TC_ResolveDrops` `0x0055A6D0`) calls the per-item quality roll (`ITEMS_DropRollQuality`)
in the middle of its own pick loop, and that the roll draws 0–6 times from the same source-unit seed
([items/0001 §8, §10](../findings/items/0001-tc-resolution.md)). Quality is scoped to `items/quality`,
a separate plan.

This nesting is the rule, not the exception. The quality roll feeds affix selection, monster
spawning calls special-monster rolls, and DRLG room code calls object placement. If a reproduction
must model every callee that shares a seed, each plan inherits the next one's scope, and the first
`[C]` arrives only when the whole chain is done.

The harness (ADR-0003) can log any register or memory value at any address, including the seed
before and after a callee and the callee's return value.

## Decision

A reproduction may treat a named out-of-scope callee as a **boundary oracle**. The experiment logs, for
every call of that callee, the shared seed state on entry and on exit, its arguments, and its return
value. The model predicts the seed state on entry and **asserts it equals the logged entry state**. It then
takes the logged exit state and return value as given and continues. A reproduction run with oracles
corroborates (`[C]`) the claims about the in-scope code that runs between oracle calls: draw order,
draw ranges, branch conditions and outputs. It corroborates nothing inside the oracle. The experiment
record names each oracle, and the finding lists the oracles a `[C]` depends on. When the callee's own
plan delivers a model, that plan re-runs the same recorded logs with the oracle replaced. The logs are
kept in `workspace/logs/`, and the checker takes the oracle as a switch. A boundary oracle never
replaces in-scope code, and the entry-state assertion is mandatory. A model that only resynchronises
from logged states, without asserting, proves nothing.

## Consequences

### Positive

- Each plan reaches `[C]` on its own scope without waiting for its callees' plans.
- The entry-state assertion still checks every in-scope draw: a missed or extra draw before the
  oracle call fails the check at that call.
- The recorded logs become the test set for the callee's plan, at no extra cost.
- Exit-state logging also shows unexpected draws. If a callee believed draw-free (item creation in
  items/0001) changes the shared seed, the log shows it.

### Negative

- **More breakpoints per call.** Each oracle adds an entry and an exit stop. On hot paths this pushes
  against ADR-0003's throughput limit.
- **The whole chain is not proven by one run.** A `[C]` resting on an oracle is `[C]` for its scope
  only. The spec has to say so, and the full chain is proven only when the last oracle is replaced.
- **Exit points must be found exactly.** An oracle needs every return path of the callee (or the
  instruction after the call site). A missed early return drops a log line, so the checker must
  treat a missing exit as a failure, not skip it.
- If an oracle's arguments are mis-identified, the in-scope model can still pass while the
  hand-off claims are wrong. Hand-off arguments stay `[I]` until the callee's plan consumes them.

### Neutral

- Purely in-scope helpers (no shared seed, or no draws) are modelled, never oracled.
- This is an operational reading of evidence rule 4, not a new evidence form. Rules 1–3 are unchanged.

## Alternatives considered

**Model the callee inside the current plan** (pull `items/quality`'s roll into plan 0004). Rejected
because the scope moves to the next plan each time, and the callee would then be specified from a
plan that never set out to study it, with no `items/quality` cross-check behind it.

**Pick inputs that avoid the callee** (only unique/set entries, forced quality). Rejected because
monster drops never force quality, and ordinary item entries are most of every TC. The test set would
not cover the code that matters.

**Resynchronise from logged seeds without asserting.** Rejected because it hides every draw-order
error before the callee. That is exactly what Phase 2 exists to catch.
