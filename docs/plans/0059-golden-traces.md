# 0059 — Golden traces: seeds and their expected world, drops and events, as conformance tests for reimplementers

> **Status:** approved (owner, 2026-10-30: "approve all of them", every scoping question answered as recommended); drafted 2026-10-30 (architect, `lane/plans57`)
> **Created:** 2026-10-30
> **Owner skill(s):** archivist (phases 1, 2, 4), spec-writer (phase 3)
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0015-emulated-reproduction, 0022-scope-server-frame

## TL;DR

How does a reimplementer know they got it right without the binary? By running a published set of cases, each a seed
and its inputs, and comparing their output field by field with the expected values. The project already has the
pieces: `tools/chain.py gen` reproduces from `-seed N` alone the game seed, the act and level seeds, a populated level
and a drop ([chain § Worked example](../specs/chain/README.md#worked-example) says its rows "double as test vectors"),
`tools/chain.py check` replays 37 kept logs of run:2026-10-21-chain2 with 0 mismatches, every reviewed spec has a
worked example, and `tools/frame_corpus.py` (plan 0055 Phase 0) reads the frame-stamped logs of plans 0037–0052 as one
event stream per session. What is missing is a **format**, a **tool** that emits and checks it, a **set** a third
party can run, and a **page** that says which spec step each field tests. When this plan is done, those four exist,
for the chain (world and drops) first and the simulation events after plans 0052 and 0055 land.

## Context

- **Two kinds of case, never mixed:** *observed* (the expected values come from a kept log of the real game: the
  strongest form, `[C]` per case) and *predicted* (from the reviewed model alone, for seeds no run kept: as good as the
  spec, labelled so). The format carries the kind per case.
- **Game data never enters git** (CLAUDE.md). A trace holds seeds, indices, codes, coordinates, counts and digests,
  the way a worked example does, never table rows or file bytes. Whether the full set is committed or regenerated is
  owner question 1.
- **Dependencies:** chain reviewed (C 89 / I 7 / L 6); 0055·P0 merged (the frame corpus). The event traces (Phase 4)
  wait for 0052·P3a's and 0055·P3's reviews, so their expected fields have a reviewed spec to cite.

## Phases

### Phase 1 — The format and the tool
- **Owner skill:** archivist (no Ghidra, no slot)
- **What:** a versioned trace format (one JSON Lines file per case set: a header with the format version, the pinned
  `Game.exe` sha256 and the table set's digest; one line per case with its kind, its inputs (seed, difficulty,
  expansion, players, level, character), and its expected outputs, each field named by the spec step it tests, e.g.
  `chain.B3.level_seed`); and `tools/golden.py` with `emit` (from `chain.py gen` and from kept logs through
  `chain.py check` and `frame_corpus.py`), `check` (compare a candidate's output file with a set and report per field)
  and `digest` (canonical JSON, sha256, for bulky outputs such as a room grid).
- **Outputs:** `docs/formats/golden-trace.md`; `tools/golden.py`; `tools/test_golden.py`; gate survey `golden` if the
  gate's survey pattern fits.
- **Done when:** the tests pass with `python3 -I`, `golden.py emit` on run:2026-10-21-chain2's kept logs reproduces
  `chain.py check`'s 0 mismatches as a set that `golden.py check` passes against itself and fails on one altered field,
  and the format doc names every field with its spec step.

### Phase 2 — The v1 set: world and drops
- **Owner skill:** archivist
- **What:** the observed cases from the kept chain, items-chain and DRLG run logs that `chain.py check` and the
  replayers reproduce (run:2026-10-21-chain2, run:2026-10-15-items-chain, the DRLG replays of plans 0022 and 0026),
  plus a predicted grid (seeds × the three difficulties × classic and expansion) over the levels the chain covers.
- **Outputs:** the v1 set under the location question 1 settles; `docs/inventory.md` block (counts, digests); a
  section of `docs/formats/golden-trace.md` listing the set's coverage per spec step.
- **Done when:** every observed case comes from a named kept log and passes `golden.py check` against the model;
  coverage per spec step is counted; no field holds a table row or file bytes.

### Phase 3 — The conformance page
- **Owner skill:** spec-writer (Sonnet suffices)
- **What:** `docs/specs/conformance/README.md` (row `conformance`): what a reimplementer runs, the order (RNG → seeds
  → DRLG → population → drops), which spec section each field tests, how to read a mismatch, and what the two case
  kinds mean.
- **Done when:** every field of the format links a spec section, the gate is green, and a Tier A review accepts it.

### Phase 4 — v2: simulation events (after 0052·P3a and 0055·P3)
- **Owner skill:** archivist
- **What:** observed event cases from the frame corpus (AI decisions, skill and missile events, combat outcomes,
  frame windows): each an entry state, the frames, and the expected events with their seeds.
- **Done when:** each event case cites its kept log and a reviewed spec section, and `golden.py check` passes them
  against the models of `tools/ai.py`, `tools/combat.py` and the frame model.

## Resources and limits

- No harness slot, no Ghidra: everything comes from kept logs and the reviewed models. Replays of many logs run under
  `systemd-run --user --scope -p MemoryMax=4G`. The archivist is mostly free on 2026-10-30.
- **Estimate:** P1 one archivist run; P2 one; P3 one short spec-writer run; P4 one run after its gates.

## Owner questions (recommendations)

1. **What goes into git?** *Recommendation: the format, the tool and a small sample set* (about 20 cases, like the
   worked examples); the full set is regenerated locally by `golden.py emit` from the reader's own game files and our
   kept logs, with its digest committed so two people can check they have the same set.
2. **v1 scope.** *Recommendation: the chain (world and drops) only*; events wait for 0052 and 0055 (Phase 4).
3. **Predicted cases at all?** *Recommendation: yes, labelled `predicted`*, because they reach seeds and levels no run
   kept; an observed case always wins a disagreement and reopens the spec.
4. **Format.** *Recommendation: JSON Lines with a version header*; no binary format.
5. **Is a quirk a case?** *Recommendation: yes, where a quirk of plan 0057 changes an output*, tag the case with the
   quirk's index id so a failing reimplementation sees which trap it hit.

## Open questions

- _Closed at the Phase 1 review:_ no 852-site call-count field (tied to the binary's inlining; it tests the build, not a
  behaviour a reimplementation can match).

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans57`).** Status `draft`; rank 3 (high value to reimplementers, no slot,
  the archivist free); five owner questions.
- **2026-10-30 — Approved (owner; recorded by the architect, `lane/appr2`).** "Approve all of them": all five questions as recommended: the format, the tool and a sample set of about 20 cases in git, the full set regenerated locally with its digest committed; v1 the chain (world and drops) only; predicted cases in, labelled `predicted`, an observed case winning a disagreement; JSON Lines with a version header; a quirk that changes an output is a case tagged with its index id. **P1 starts now** (`lane/a59`, archivist). Status `approved`.
- **2026-10-30 — Phase 1 landed (archivist, `lane/a59`).** `docs/formats/golden-trace.md` (JSON Lines, version header,
  `observed`/`predicted` per case, reserved `quirks` list), `tools/golden.py` (`emit`, `check`, `digest`, `fields`,
  `sample`, `merge`), `tools/test_golden.py` (10 tests) and the 22-case sample `docs/formats/golden/sample-v1.jsonl`.
  `emit --chain-check` on run:2026-10-21-chain2's 37 kept logs: 37 observed world cases and 3 784 observed drop cases,
  0 failed, `chain.py check` exit 0; the set checks against itself. Full-set digest (local table set)
  `210523526edd1af5d56516ff46fb14bd78b655a96efbe0e972ef1a29a5288c85`. No survey added to the gate (no input files to
  survey; the tests cover it). Not in v1 fields: item seeds after the drop, room populations (chain § D–E); the
  852-site call-count field is left to the review.
- **2026-10-30 — Phase 1 check (architect, Tier B, `lane/a59`): accept with fixes (2, overclaim).** Rulings: (1) no
  call-count field, ever; (2) item seeds (G2/G3) and room populations go into a later set version, after Phase 2 (the
  format takes new fields without a version bump of the header; unknown fields in `expected` are the set's, so a
  candidate that omits them is a missing field, as `check` already reports); (3) no gate survey, agreed; (4) `quirks`
  stays reserved and empty until plan 0057 assigns ids, and `check` treats ids as opaque strings. Sample content: 6
  observed and 8 predicted world cases and 8 observed drop cases of derived values only (seeds, ids, counts, region
  pool class ids, digests); no strings except two `monster_flags` bytes, no table rows or file bytes, so it is not
  game data under the CLAUDE.md rule. Test run 10 OK; the sample checks against itself (22 cases, 0 different).
