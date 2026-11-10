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

### 2026-11-10 — Phase 3 triage, slices S1 and S2 (lane n64t, architect; Tier A review of the Phase 2 ledgers)

**Verdict on the S1 and S2 ledgers: accept, 0 fixes.** Every first-pass difference of S2 is a row (rows 1 and 2 carry
`nodrop` 1 113 and quality 136; `item`, `end_seed`, `count`, `pick`, `select` and `subtc` run on after a wrong quality
roll on the same seed, and all reached 0 with rows 1 to 3 applied); S1 had none. The triage is the new last column of
[S1](0064-cleanroom/S1.md) and [S2](0064-cleanroom/S2.md). "Implementer error" is used as the plan defines it, *the
spec was clear*: in all five such rows the guess was right, and no row is a mistake by the implementer.

| Slice | Spec defect | Missing finding | Golden-set defect | Implementer error (no defect) | Rows |
|---|---|---|---|---|---|
| S1 | 0 | 0 | 5 (1 sandbox tool, already fixed; 4 format) | 1 | 6 |
| S2 | 1 | 1 | 10 (3 set, 7 format) | 4 | 16 |

Rulings on the two large S2 rows:

- **Magic find (rows 2 and 3): golden-set defect, to the archivist.** The specs are right: chain § Algorithm row G
  lists the killer's magic find as an input, and items/quality M1–M3 says how it is composed (stat 80, plus the
  owner's for a hireling). The kept logs hold it: `QKMF kmf=472` in every expansion chain2 log checked and
  `kmf=250` in the classic ones (`p2r2-s1-4861-r2-xn1`, `-4891-r2-cn1`, `-4901-r2-cm1`), with `QMF` agreeing, and
  `tools/quality.py` reads those lines, which is why the project's own replay never missed them. `tools/golden.py`
  `drop_case` reads only `TCR`, `PLAYERS`, `PARTY` and `CAP`, so the case drops the input. The implementer's fitted
  472 and 250 are the logged values. The conformance page's "the call's inputs (… source and killer) are given" is a
  wrong sentence until the set carries them (spec-writer entry, dependent on the archivist's).
- **`nodrop` shape (row 1): format defect (golden-set class), to the archivist.** items/tc D4 states correctly that
  `ScaleNoDrop` runs only when `NoDrop ≠ 0`; the field is not that call but the logger's `NDP` line at 0x0055A9D9,
  which every positive pick reaches, so a `NoDrop` 0 pick logs `[0, total]`. The format's "NoDrop scaling per roll",
  linked to items/tc § F, describes the scaling and not the list. Not disputed: the field is the format's to define.

Other rulings: S2 row 11 (the type test) is the one spec defect: items/quality S2 sends the reader to items/tc for
`IsType`, items/tc uses the test in I1 and H8 without defining it, and data/excel G2 likewise; the answer is in the
findings (items/0001 symbol table, archaeology/0002) and in items/affixes' C5c–C5d note. S2 row 14 is a missing
finding, not a spec defect: no finding states which words `TC_ParseItemCell` writes for a unique or set cell
(`tools/tc.py` models "index = the row's base, aux = the row", but a tool comment is not a statement). S1 rows 2 to 5
and S2 rows 4 to 10 are conventions the format leaves to `golden.py`; all were guessed right.

Backlog entries filed (7):

- archivist: [drop-cases-magic-find](../backlog/archive/2026-11-10-architect-archivist-plan-0064-drop-cases-magic-find.md)
  (S2 rows 2–3: add the inputs, re-emit the set); [golden-trace-field-conventions](../backlog/archive/2026-11-10-architect-archivist-plan-0064-golden-trace-field-conventions.md)
  (S1 rows 2–5, S2 rows 1 and 4–10, items (a) to (k)). S1 row 1 was already fixed and closed:
  [cleanroom-score-path-and-audit-heredocs](../backlog/archive/2026-11-10-architect-archivist-cleanroom-score-path-and-audit-heredocs.md).
- spec-writer (one per spec): [items-tc-type-test](../backlog/archive/2026-11-10-architect-spec-writer-plan-0064-items-tc-type-test.md),
  [items-quality-type-test-link](../backlog/archive/2026-11-10-architect-spec-writer-plan-0064-items-quality-type-test-link.md),
  [data-excel-type-test-link](../backlog/archive/2026-11-10-architect-spec-writer-plan-0064-data-excel-type-test-link.md),
  [conformance-drop-inputs](../backlog/2026-11-10-architect-spec-writer-plan-0064-conformance-drop-inputs.md)
  (waits for both archivist entries).
- reverser: [parseitemcell-unique-entry-words](../backlog/2026-11-10-architect-reverser-plan-0064-parseitemcell-unique-entry-words.md)
  (S2 row 14; static only; data/excel G4 and items/tc § A follow).

**Disputed rows, for a second fresh implementer** (the orchestrator runs it; this lane did not spawn one):

- S2 row 12, provisional class implementer error. Give the implementer items/quality § S1 (`cls`) and
  `docs/tables/ItemTypes.md` only, with the sandbox's `ItemTypes.txt` and `PlayerClass.txt`. Question: "For an
  ItemTypes row whose `Class` cell is `ama`, and for one whose `Class` cell is blank, what value does the record's
  `Class` byte hold, and is `Class < 7` true for each? Quote the sentence you used." If the answer needs a guess,
  the row becomes a spec defect for items/quality (name the `playerclass` index space beside S1).

No other row is disputed: rows where the format (an archivist document) is unclear are golden-set defects by the
plan's own class, not spec-versus-implementer questions.

**What S3 and S4 wait for.** None of the spec-writer entries touches a spec S3 or S4 reads: the data/excel change is
in § G (treasure classes), which neither slice uses, and rng and rng/seeds have no defect. So **no spec fix gates
S3 or S4.** They should wait for the archivist's format entry, items **(b)** (which fields a case holds; extra
candidate fields are not compared) and **(c)** (the digest's level set and canonical form): S3's `monsters.pool.*.N`
and `monsters.pool.digest` and S4's `*_digest` fields rest on exactly the conventions S1 had to guess. Rebuild the S3
and S4 sandboxes (`cleanroom.py make`) after that entry lands, and after the magic-find re-emit if it lands first, so
the sandbox's format doc and the full set match what `score` reads.

Left: Phase 4 (spec-writer, the four entries; the conformance one after the archivist's two), the archivist's two
entries, the reverser's one, the row 12 question; then S3 and S4 Phase 2 runs and their own triage. Phase 5 for S2
re-runs the `chain.G1.*` fields after the magic-find re-emit and the format entry, and for S1 the B1/B2 fields after
the format entry.

- **2026-11-10, Phase 3 disputed row S2-12 (orchestrator):** a fresh Opus reader given only items/quality § B,
  `tables/ItemTypes.md`, `itemtypes.txt` and `playerclass.txt` answered `ama` → 0, `< 7` true; blank → 0xFF, `< 7`
  false, but needed two guesses: `ama` = 0 from row order, and the compare's signedness (S1's "signed type,
  bounds-checked" is ambiguous for `Class`). It also found ItemTypes.md's Row identity rule ("a blank reference cell …
  stores 0") contradicting the layout's "blank → 0xFF". Row 12 reclassified **spec defect** (items/quality) plus a
  table-doc defect; entries `plan-0064-items-quality-s1-class-compare` (spec-writer) and
  `plan-0064-itemtypes-blank-class-vs-row-identity` (archivist).

- **2026-11-10 — Phase 3 follow-up: the two archivist entries (archivist, `lane/n64g`).** (1) *Magic find.*
  `tools/golden.py` `drop_case` now reads the `QKMF`, `QOMF` and `QMF` lines between each `QIN` and `QOUT` and writes
  `killer_mf` (the killer's stat 80) and `owner_mf` (its owner's, M3; a mercenary's or summon's own and owner's stay two
  inputs) into the case's inputs; the values must agree across the rolls of a call and `QMF` must equal `QKMF + QOMF`, or
  `emit` writes no case and counts the call failed. Re-emit: chain2 3 784 and items-chain 256 drop calls, 0 failed,
  `chain.py check` exit 0; every case id and expected value is as before (0 differ), 486 cases gain `killer_mf` (472 x 309
  expansion, 250 x 174 and 215 x 3 classic) and none has `owner_mf`. The v1 set joins to 5 073 cases, digest
  `878ea350…c1c0` (was `d73f29f6…9e08`; chain2 `c53820f3…8e03`, items-chain `98e27ab9…4213`, DRLG and predicted parts
  unchanged; the old parts merged still give the old digest, so the change is the inputs alone). The committed sample's
  one affected drop case gained its input. The reference scores 0 different: `cleanroom.py reference` S1 (62 035 fields)
  and S3 (211 140 fields) from `golden.world_expected`; the tool offers a reference for world slices only, so S2 and S4
  were scored with the new set as candidate (0 different, 32 320 and 1 820 fields). `test_golden.py` 16 tests OK
  (`test_drop_case_magic_find`). (2) *Conventions.* `docs/formats/golden-trace.md` § Conventions states items a–k from
  the code: the act number base 1, the acts and levels of observed and predicted worlds, that `check` ignores extra
  candidate fields, the digests' level set (levels 1 to 136) and canonical form, and the drop lists (`nodrop` one entry per
  positive pick, `[0, total]` for NoDrop 0: in all 4 040 calls `len(nodrop) = len(pick)`, 1 113 hold a NoDrop-0 entry; `pick`, `select`, `subtc`, `quality`),
  inputs `tc`, `players`/`party`/`cap`, `killer_mf`/`owner_mf`, context-only inputs and `g6a`. One difference from the
  entry's wording: the `quality` list holds a forced quality (`QOUT` is logged for it, `tools/tc.py`), though no v1 case has one. Both entries closed; the conformance entry
  is annotated, not closed. **Handoff:** the orchestrator rebuilds the S2 sandbox's `cases.jsonl` (`cleanroom.py make S2
  --force`) before the Phase 5 re-run, and rebuilds S1 for the new format text. Review tier B. Note for the reviewer: the
  first `cleanroom.py score` calls of this lane, run without `--out`, each appended a line to the default sandboxes'
  `score-log.jsonl` (S1, S2: the last line; S3, S4: the file did not exist before); see the lane report.

- **2026-11-10, Phase 2 slice S3 (orchestrator):** one fresh Opus implementer on a sandbox rebuilt from `main` at
  `41ef2867`, 111 116 tokens, 22 tool uses. Score log run 1 is lane `n64g`'s reference test (09:21 UTC, kept by
  `make --force`); the implementer's first pass is run 2: 211 140 fields, 0 different, 0 missing (all 612 cases
  predicted); no later run. Ledger [S3](0064-cleanroom/S3.md), 6 rows, all `first`; the two that matter: the
  conformance page sends `mlvl.N` to monsters/pool § E while the value is § B4's region copy, and step C1's candidate
  counts are load-time bytes (0 in the shipped file). Audit: 1 path, an `ls` of the ledger folder after scoring (file
  names only, none opened); the harness's tool-results Read is allowed by the tool. Run ruled valid.

### 2026-11-10 — Phase 4 spec fixes, slices S1 and S2 (lane n64w, spec-writer)

Four spec-defect entries closed, each with what the implementer could not know and the finding that already held the
answer; no new finding was needed for any of them.

- **items/tc § K, the item-type test** (S2 row 11). The definition sat only in items/affixes C5c–C5d, outside the
  slice. § K now defines the closure, `ITEMS_IsType` (`type` then `type2` through `Equiv1`/`Equiv2`, `[I]`, items/0001
  symbol table, archaeology/0002 § 5) and `ITEMS_UnitIsType` (`[C]`, items/0005 tests (c)–(d) and the `GOLD_TYPE` run),
  and a blank `Equiv` storing record 0 (`[C]`, data/0004), which no test of these specs asks for (`[I]`). I1 and H8 call
  it by name. The walk's form (depth, a cycle, record 0 in the set) is a new `[L]` under *Open questions*, filed to the
  reverser ([entry](../backlog/2026-11-10-spec-writer-reverser-itemtypes-equiv-walk-form.md)); no stock test depends on it.
- **items/quality S2 and data/excel G2** link § K and name the function; S2 contrasts it with A2–A5 and S1.
- **items/quality S1** (S2 row 12): the `Class` byte is the `playerclass` row index `[C]` (PlayerClass § Row identity);
  it is a u8, so a blank `0xFF` is not `< 7` (reading `[I]`, items/0002 § 2; outcome `[C]`, the 1607 logged rows of
  quality 13), and "signed, bounds-checked" is the test of `rec.type`. The stored values are only 0–6 and `0xFF`, so
  the width and the logged rows decide the compare for every value the game can hold; no reverser entry was routed.
- **Quirks drift** (not a plan 0064 entry, done in the same lane): `quirks.py check` went from 46 errors (the 15 named,
  plus plan 0068 P4's new items/tc n1 and skills/dispatch n9–n10) to 0. Q72, Q175, Q271 and twelve items/tc citations
  re-pointed; Q475–Q527 (53 entries, C 19 / I 34) taken from the eight uncovered specs and the added notes; two notes
  skipped as not a trap. Registering the check in `tools/gate.py` is ready for the architect.

Wiki: items (S1's class key, the auto-TC "of that type"), game-data (the same), quirks (the counts). Research-map rows
of items/tc, items/quality, data/excel and quirks updated for their dates and counts. Tags: items/tc C 123 / I 66 /
L 7, items/quality C 72 / I 41 / L 1, data/excel C 146 / I 59 / L 2, quirks C 374 / I 162 / L 3.

Not done here: [conformance-drop-inputs](../backlog/2026-11-10-architect-spec-writer-plan-0064-conformance-drop-inputs.md)
waits for the archivist's golden-set entries (lane n64g). Review: Tier A. Next: Phase 5 re-runs the S2 type-test and
class-key fields from the fixed specs.

### 2026-11-10 — Phase 4 review (architect, Tier A): accept with fixes (2)

Reviewed `lane/n64w` after merging `main` (n64g and plan 0068's close; the two conflicts, this log and S2.md rows 1–11,
kept both sides: main's archived golden-set links, the lane's archived type-test links). Mode 3 in full, with the
promotion re-check of the new `[C]`s: items/tc K1 (data/0004, 2026-10-12), K3 (items/0005 tests (c)–(d), 2026-10-14;
items/0001 tc 11, H2a), items/quality S1's row index (PlayerClass § Row identity) and outcome (items/0002 quality 13,
S2a): each rests on an earlier reviewed statement that says what the sentence says. The new `[L]` (how the walk is
built) sits under *Open questions* and its entry is addressed to the reverser. Anchors spot-checked with r2 on the pinned
`Game.exe`: `ITEMS_IsType` 0x00629A90, `ITEMS_UnitIsType` 0x00629BB0, `ITEMS_IsClassSpecific` 0x00629F70, all as named.

- **S1 signedness, the lane's judgment call: upheld.** 0x00629FCE is `cmp byte [eax + 0x21], 7`, then `sbb eax, eax;
  neg eax`: a carry test, unsigned below, so a blank `0xFF` gives 0; the signed, bounds-checked test is `rec.type`'s
  (`movsx word [rec + 0x11E]`, `jl`, `jge` against the count, 0x00629F9F–0x00629FB6). No reverser entry is needed. Fix
  (omission): the S1 note now names the compare and its address. What the implementer could not know: whether `0xFF`
  is −1 (`< 7`) or 255; items/0002 § 2 holds the reading.
- **Quirks sample**, 17 of the 53 new entries (Q475, Q476, Q477, Q478, Q481, Q488, Q489, Q493, Q497, Q498, Q499, Q503,
  Q508, Q510, Q521, Q525, Q527) against their notes: every tag matches. Fix (overclaim): Q488's "agrees with every live
  search on open ground" restored to the note's count, "all 118 live searches".
- **§ K, a lead for the reverser entry** (not a fix): r2 shows the test reads a precomputed bit matrix, skips a zero
  `type2` and returns 0 for an out-of-range `t`; written into
  [itemtypes-equiv-walk-form](../backlog/2026-11-10-spec-writer-reverser-itemtypes-equiv-walk-form.md) as a lead.
- **Gate:** `tools/quirks.py check` is clean after the merge (527 entries, 0 errors, about 0.2 s) and is registered as
  fast-tier rule E18 in `tools/gate.py` (each `quirks:` line one error, at its file line); `test_gate.py` passes.

Fix count: overclaim 1, omission 1. The conformance-drop-inputs entry the lane left waiting is unblocked now that n64g is
on `main`. Not merged; plan 0064 stays open for Phase 5.

- **2026-11-10, Phase 2 slice S4 (orchestrator):** one fresh Opus implementer on a sandbox rebuilt from `main` at
  `41ef2867`, 402 305 tokens, 101 tool uses. Score log run 1 is lane `n64g`'s reference test; the first pass is run 2:
  1 820 fields, 381 different, 0 missing (maze rooms_digest 50/50; outdoor preset_count 46, presets_digest 84,
  room_count 47, rooms_digest 84, seed_after 70; all 384 cases observed). Final run 12: 106 different, maze all right,
  22 outdoor cases (Act I levels 4–7) still differ. 12 runs, several fixes guessed or partly guessed from the diff (§ H6d
  road search, § H7 `OneOrTwo`, § H1 `A1CliffMark`). Ledger [S4](0064-cleanroom/S4.md), 24 rows; notable: maze room
  order ("creation order" in golden-trace vs "newest first" in maze § Outputs), the `first_room_seed` input disagreeing
  with B1 in 45 of 50 cases, and the slice needing warps § A–C and rng/seeds step 3 outside its row. Audit clean.
