# 0064 — Clean-room test: implement the chain from the specs alone and score it on the golden traces

> **Status:** approved (2026-11-10, by the owner, as recommended: ADR-0032 accepted, S4 in and last; not started: the owner starts it)
> **Created:** 2026-11-10
> **Owner skill(s):** human, archivist, none (clean-room implementer, ADR-0032), architect, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0023-review-tiers-and-gate-first-fixes, 0032-clean-room-implementation-test

## TL;DR

**Question:** can someone who has only `docs/specs/`, `docs/tables/`, `docs/formats/` and the game's own tables
reproduce what the golden traces expect? Where they cannot, which spec sentence failed them? Fresh agents with no
project knowledge implement four slices of the core chain in a sandbox (ADR-0032), and `tools/golden.py check` scores
each one against plan 0059's v1 set. When this plan is done, each slice has a first-pass score (before the
implementer saw any check output) and a final score, and `docs/plans/0064-cleanroom/` holds the gap ledger. Every
ledger row is triaged, and the spec defects among them are fixed in the specs. A second fresh implementer then
reaches 0 mismatches on the fixed fields, or the remainder is named. No code enters git.

## Context

- **Why now.** Every research-map row the slices touch is `reviewed`. Plan 0059 Phases 1 to 3 are accepted: the format
  ([fmt:golden-trace](../formats/golden-trace.md)), `tools/golden.py` (`emit`, `check`, `digest`), the v1 set of 5 073
  cases and the [conformance page](../specs/conformance/README.md), which maps every field to the spec section it tests.
- **The slices**, smallest first, each a set of golden field prefixes and the specs that should suffice:

  | Slice | Fields (`--fields`) | Specs the implementer should need |
  |---|---|---|
  | S1 seeds | `chain.A`, `chain.B` | rng, rng/seeds, chain § A–B, data/excel (Levels) |
  | S2 drops | `chain.G1` | items/tc, items/quality, data/excel, rng |
  | S3 pools | `monsters.pool` | monsters/pool, data/excel, rng/seeds |
  | S4 DRLG | `drlg.maze`, `drlg.outdoor` | drlg/overview, drlg/maze, drlg/outdoor, drlg/preset, drlg/room-tiles, formats ds1 and dt1 |

- **Observed and predicted.** Only observed fields test the specs against the game. Predicted fields (S3, and parts of
  S1) test the specs against the project's own model, so a mismatch there may be the set's fault. The ledger records
  the case kind of each row.
- **Measure.** The first-pass score is the main result: the implementer writes the slice from the specs and runs the
  check once. Afterwards it may iterate, but every change after the first check must cite the spec sentence it now
  reads differently. A change it cannot tie to a sentence is a ledger row ("guessed from the diff"), not a fix.

## Phases

### Phase 0 — Accept ADR-0032
- **Owner skill:** human
- **What:** the owner accepts, amends or rejects ADR-0032 (a clean-room lane outside the four skills; code in
  `workspace/cleanroom/`, gap ledger in git).
- **Done when:** ADR-0032's status is `accepted` (or the plan is abandoned).

### Phase 1 — The sandbox
- **Owner skill:** archivist (no Ghidra, no slot)
- **What:** `tools/cleanroom.py` with these commands:
  - `make SLICE` builds a sparse worktree holding only `docs/specs/`, `docs/tables/`, `docs/formats/` and
    `docs/glossary.md`. It adds `workspace/cleanroom/<slice>/data/` with the extracted excel tables (and, for S4,
    the DS1 and DT1 files the slice needs), and `workspace/cleanroom/<slice>/cases.jsonl` with the slice's cases, inputs
    only (expected fields stripped).
  - `score SLICE CANDIDATE` runs `golden.py check --fields` for the slice's prefixes against the full set.
  - `audit TRANSCRIPT` lists every path the lane read outside its allow-list.
  - Also write the clean-room lane's standing brief (`docs/plans/0064-cleanroom/brief.md`): the rules of ADR-0032,
    the measure above, and the ledger's columns (slice, case kind, field or spec section, what was missing or
    ambiguous, what the implementer guessed, first-pass or later).
- **Outputs:** `tools/cleanroom.py`, its no-game tests, `docs/plans/0064-cleanroom/brief.md`.
- **Done when:**
  - `make S1` builds a tree in which `docs/findings`, `re`, `tools`, `.claude` and `Game.exe` are absent.
  - `cases.jsonl` has no expected field.
  - `score` on the project's own `chain.py gen` output gives 0 mismatches for S1.
  - `audit` flags a planted read of `docs/findings/`.
  - Review: Tier B.

### Phase 2 — Clean-room runs
- **Owner skill:** none (clean-room implementer, ADR-0032); one fresh agent per slice, Opus, briefed by the brief and
  the slice's row only
- **What:** each lane implements its slice in any language inside `workspace/cleanroom/<slice>/`, writes the candidate
  output in the golden format ([fmt:golden-trace](../formats/golden-trace.md)), runs `score` once (first pass), may
  iterate under the measure's rule, and writes its ledger file `docs/plans/0064-cleanroom/<slice>.md`. Slices S1 and
  S2 run first, in parallel. S3 and S4 follow, so that S1's and S2's triage can fix shared specs (rng, data/excel)
  before them.
- **Outputs:** the four ledger files (in git), the code and candidate outputs (in `workspace/`, never in git).
- **Done when:** each slice has a ledger with its first-pass and final scores per field prefix, and every mismatch and
  guess is a row. `cleanroom.py audit` on the lane's transcript is clean. A lane that fails the audit is void and
  re-run.

### Phase 3 — Triage
- **Owner skill:** architect
- **What:** classify every ledger row into one of four classes:
  - spec defect (missing, ambiguous or wrong sentence);
  - missing finding (the spec states the gap honestly, but nothing fills it);
  - golden-set defect (a wrong or underspecified expected value, or a predicted field the model gets wrong);
  - implementer error (the spec was clear).

  Where a row is disputed between spec defect and implementer error, a second fresh implementer re-reads only that
  spec section and answers the one question. Spec defects go to the spec-writer as one backlog entry per spec, missing
  findings to the reverser, golden-set defects to the archivist.
- **Outputs:** a triage column in each ledger file; the backlog entries.
- **Done when:** every row has a class and, unless it is an implementer error, a backlog entry. The triage is
  delivered as a Tier A review of the Phase 2 ledgers.

### Phase 4 — Spec fixes
- **Owner skill:** spec-writer
- **What:** apply the spec-defect entries. Each fix states what the implementer could not know and cites the existing
  finding that already holds the answer. A fix that would need a new finding waits for the reverser's entry instead.
- **Outputs:** the specs named in the entries, their wiki pages where a restated sentence changed.
- **Done when:** every spec-defect entry is closed or routed. Review: Tier A.

### Phase 5 — Re-run
- **Owner skill:** none (clean-room implementer, ADR-0032)
- **What:** for each slice with fixed specs, a **new** fresh agent (not the Phase 2 one) implements only the fields
  whose rows were spec defects, from the fixed specs, under the same sandbox and measure.
- **Done when:** the fixed fields reach 0 mismatches on the first pass, or every remaining one is a new ledger row
  that Phase 3's rules triage. The plan's review records the per-slice first-pass scores before and after, and the
  plan closes.

## Open questions

- Whether S4 (DRLG) is in this plan or a follow-up. It needs the DS1 and DT1 readers to be built from `docs/formats`,
  which is a large job on its own. Recommended: in, but last, and cut first if S1 and S2 cost more than estimated.
- Whether the simulation events (plan 0059 Phase 4, v2) get a clean-room slice. Not until v2 exists.
- Model for the implementer: Opus by default. A Sonnet re-run of one slice would show whether a weaker reader needs
  more from the specs, but it is not required.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

### 2026-11-10 — Phase 1 (lane n64a, archivist)

Done: `tools/cleanroom.py` (`make`, `score`, `audit`, plus `reference` and `slices`), `tools/test_cleanroom.py` (14 no-game
tests), `docs/plans/0064-cleanroom/brief.md`.

- `make S1` builds `workspace/cleanroom/S1/` in 0.3 s: 163 files of docs/specs, tables, formats, glossary; `data/` with the
  184 excel files (copies; the S4 tiles are hard links); `cases.jsonl` (649 world cases, keys `id kind type inputs` only: no `expected`, `source`
  or `quirks`); `score.sh`; `MANIFEST.json`. `docs/findings`, `re`, `tools`, `.claude`, `.git` and any `Game.exe` are absent
  (checked at build). S2 (4 040 cases), S3 (612), S4 (384 cases, 2 539 DS1/DT1 files, 189 MB) build the same way.
- `score S1` on the project's own model (`cleanroom.py reference S1`, which calls `golden.world_expected`, i.e.
  `chain.py gen`): 62 035 fields compared, 0 different; S3 likewise 211 140 fields, 0 different. `audit` flags a planted
  Read of `docs/findings/`, a Bash `cat re/...`, a Grep with no path from a project cwd and a relative `../docs/findings`.
- Judgment calls: (1) the sandbox is a plain directory copied from the tracked files (no git worktree) with an empty git
  repository of its own (without it, `git show HEAD:docs/findings/...` run in the sandbox finds the project's history in
  the checkout above it; the check review found this, and `check_clean` now requires the sandbox to be its own top level),
  so there is no history or ref to read the findings from; the working tree is the source, so Phase 4 fixes show without a commit.
  (2) `docs/formats/golden/` (the committed sample, with expected values) is left out. (3) `score` cuts the full set to
  the slice (case types and field prefixes) before calling `golden.py check`, otherwise the other slices' cases count as
  missing; it logs each run to `<sandbox>/score-log.jsonl`, run 1 being the first pass, and refuses a malformed
  candidate without logging it. (4) `audit` assumed the Claude Code session shape (assistant lines with
  `message.content[].tool_use`, top-level `cwd`; checked on a real subagent transcript, 579 calls) and also reads bare
  `tool_use` lines and a JSON array; no tool calls found is exit 2. Relative Bash words are judged against the line's
  `cwd`, so a lane must use absolute sandbox paths (the brief says so); wild false positives are possible on odd shell
  words, false negatives on paths built by shell expansion or inside scripts the lane wrote and ran (the audit sees the
  command, not the script's own reads). The audit is a check, not enforcement (ADR-0032).
- Left: Phase 2 (clean-room runs). Before S1 and S2 start, `make` them and pass the brief plus the slice row only.
  Review: Tier B.

- **2026-11-10, Phase 2 slice S1 (orchestrator):** one fresh Opus implementer, 124 365 tokens, 19 tool uses. First pass
  62 035 fields, 0 different, 0 missing; final the same; ledger [S1](0064-cleanroom/S1.md), 6 rows, all `first` (4
  unstated conventions of the golden format guessed right, the broken `score.sh`, dead links). The first `score.sh`
  call failed (path of the removed `lane/n64a` worktree); the orchestrator repointed it, and no check output had been
  seen. `cleanroom.py audit --slice S1` reports VOID with 6 paths, all false: words inside two heredoc bodies (the
  implementer's Python source and its ledger text); with the ledger folder and the harness's tool-results folder
  allowed, a manual read of each flagged call finds no read outside the sandbox. Run ruled valid; tool fixes filed for
  the archivist. Caveat for the triage: the implementer's session loaded the project's `CLAUDE.md` (the harness loads it
  for every subagent), which is a project map, not a finding.

- **2026-11-10, Phase 2 slice S2 (orchestrator):** one fresh Opus implementer on a sandbox rebuilt from `main` at
  `39854e16` (own git repository), 239 684 tokens, 49 tool uses. First pass 32 320 fields, 1 573 different, 0 missing
  (nodrop 1 113, item 136, quality 136, end_seed 127, pick 22, select 18, subtc 12, count 9; all cases observed); final
  (run 6) 0 different, but only after **fitting the killer's magic find from the printed diffs** (472 expansion, 250
  classic): no `drop` case input and no document gives it, and the ledger records it as guessed from the diff. Ledger
  [S2](0064-cleanroom/S2.md), 16 rows. `cleanroom.py audit --slice S2` reports 4 paths: one shell variable assignment
  and three files the implementer wrote and read back in the shared session scratchpad (its own mismatch lists); a
  manual read of each finds no read of project material outside the sandbox. Run ruled valid. For the triage: the
  magic-find input (golden-set or spec defect) and the `nodrop` list shape (format doc, "per roll") carry 1 249 of the
  1 573 first-pass differences.
