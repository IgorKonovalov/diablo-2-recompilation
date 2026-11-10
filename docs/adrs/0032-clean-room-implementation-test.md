# ADR-0032 — A clean-room implementation test of the specs: code outside git, its gaps inside

> **Status:** proposed
> **Date:** 2026-11-10
> **Related plan(s):** 0064-clean-room-test

## Context

The deliverable claims that someone can reimplement the game from `docs/specs/` alone (ADR-0001). Nothing tests that
claim yet. Every reviewed spec was written by a lane that had read its findings, and was reviewed by an architect who
had read them too. A gap that the findings fill in a reader's head does not show in either step.

Plan 0059 built the measuring stick: a versioned trace format, `tools/golden.py check`, a v1 set of 5 073 cases
(world and drops, regenerated locally) and a committed sample of 28. What is missing is a candidate that was built
without the project's other knowledge.

Two project rules bear on such a candidate. The project's output is "not code" (CLAUDE.md), so a reimplementation must
not become a second deliverable. And every lane belongs to one of four skills, each of which carries knowledge of the
findings, the tools or the binary in its own references, so no existing skill can play the outsider.

## Decision

A clean-room lane implements a named slice of the specs from `docs/specs/`, `docs/tables/`, `docs/formats/` and
`docs/glossary.md` only. It reads the extracted game tables, but not `Game.exe`, `docs/findings/`, `re/`, `tools/` or
any project skill. It may run `tools/golden.py check` but may not read its source. It works in a sandbox that the
plan's set-up phase builds: a sparse worktree holding only the allowed paths, and a data folder holding only the
extracted table files. It is briefed by its plan phase alone. Its code stays in `workspace/cleanroom/` (gitignored)
and never enters git. What enters git is its **gap ledger**: every golden-trace field it misses, and every point where
it had to guess, each with the spec section it was reading. The ledger is a plan artifact under
`docs/plans/<plan>-cleanroom/`, owned by the architect. The architect triages it into spec defects (to the
spec-writer), missing findings (to the reverser), golden-set defects (to the archivist) and implementer errors (no
action). A clean-room lane's transcript is checked for reads outside the allowed paths, and a lane that read one is
void: its ledger is discarded and the slice is re-run by a fresh agent.

## Consequences

### Positive
- The first direct test of the deliverable's central claim, measured field by field against observed traces.
- Gaps are found by the reader they would hurt, not by readers who already know the answer.
- No code enters git, so the "not code" rule holds; the specs stay the only deliverable.

### Negative
- A lane with no skill falls outside the four-lane table in CLAUDE.md. This ADR is the exception, and the plan must
  brief such a lane completely.
- The isolation rests on a sandbox and a transcript check, not on enforcement by the harness. A careless brief or a
  stray read voids a run, which costs a full lane.
- Implementer errors and spec defects look the same in a mismatch. Telling them apart costs architect review time, and
  a second independent implementer for disputed fields.
- The code is thrown away (or kept only locally), so later spec changes cannot be re-tested without a new run.

### Neutral
- The clean-room code may be kept in `workspace/cleanroom/` for re-runs. It carries no evidence weight and is never
  cited as an anchor.
- The ledger cites spec sections and golden field names, never findings, so it can be read by anyone.

## Alternatives considered

**Commit the reimplementation as a reference implementation.** It would make re-testing cheap, but it creates a second
deliverable that drifts from the specs and that later readers would trust over them. That conflicts with the project's
"not code" rule, and it lost on that.

**Let an existing lane (spec-writer or archivist) write the candidate.** It would need no new lane kind, but each skill's
references carry the findings, the tools or the binary layout, so the test would no longer be blind. It lost on that.

**Review the specs for reimplementability by reading only.** This is what the Tier A review already does (the
"Reimplementable" check). It is cheap but has not found the gaps a running implementation finds: missed fields only
show when the output is compared.
