# Clean-room lane: standing brief (plan 0064, ADR-0032)

You implement one slice of a game's rules from its written specification, in a sandbox, and say where the
specification failed you. You are the outsider: nobody will explain the game to you, and that is the point.

## Your inputs

Your sandbox is `workspace/cleanroom/<slice>/` (the slice row below names it; use its absolute path). It holds:

- `docs/specs/`, `docs/tables/`, `docs/formats/`, `docs/glossary.md`: the specification. Start at
  `docs/specs/README.md` and `docs/specs/conformance/README.md` (it maps each golden field to the spec section that
  tests it).
- `data/`: the game's own extracted tables (`data/global/excel/`; slice S4 also the DS1 and DT1 files).
- `cases.jsonl`: your cases, one JSON object per line: `id`, `kind` (`observed` or `predicted`), `type`, `inputs`.
  No expected values are given.
- `score.sh`: scores a candidate file (below).

You write your code anywhere inside the sandbox, in any language available on the machine.

## What you may read

Only files inside your sandbox. Nothing else: not `docs/findings/`, `re/`, `tools/`, `.claude/`, any `Game.exe`, any
other checkout of this project, the golden set itself, the source of `tools/golden.py` or `tools/cleanroom.py`, or the
web. Use absolute paths inside the sandbox in every tool call (a relative path is judged against the directory your
shell started in, which is outside it). If a spec sentence links to a path outside the sandbox, the link is dead for
you; that is a ledger row, not a reason to follow it.

Your transcript is audited (`python3 -I tools/cleanroom.py audit`). One read outside the sandbox voids the run: your
ledger is discarded and a fresh agent redoes the slice. When unsure whether a path is allowed, do not read it.

## The task

1. Implement the slice: for each case in `cases.jsonl`, compute the fields of your slice from the case's `inputs`, the
   specs and the tables.
2. Write the candidate file, JSON Lines, one object per case, `{"id": <case id>, "outputs": {<field>: <value>}}`
   (format: `docs/formats/golden-trace.md`, sections Fields and Checking). Field names, value forms (seeds as
   `low:high`, 8 hex digits each, lower case; digests as `golden.py digest --value` makes them: sha256 of the canonical
   JSON, keys sorted, separators `,` and `:`) are in that format doc.
3. Run `sh <sandbox>/score.sh <candidate>`. **The first run is your first pass and is recorded** (the score log line
   with `run` 1). Before you run it, do not look at any check output; do not run it "to see". Write the whole slice
   first.
4. You may iterate afterwards under this rule: **every change after the first check must cite the spec sentence you now
   read differently** (file, section, the sentence). A change you cannot tie to a sentence, one you guessed from the
   diff the check printed, is not a fix: log it as a ledger row ("guessed from the diff") and say what you changed.
5. Write your ledger, `docs/plans/0064-cleanroom/<slice>.md`, in the project checkout your caller names (the only
   file you write outside the sandbox, and you write it last, from your notes, without reading anything there).

## The measure

- **First-pass score**: the per-field-prefix result of run 1 (fields compared, fields different, cases missing). It is
  the main result. Report it exactly as `score.sh` printed it.
- **Final score**: the same after your last run.
- Observed cases test the spec against the game. Predicted cases test it against the project's own model, so a
  mismatch there may be the case's fault. Always record the case kind.

## The ledger

One markdown file per slice with a header (slice, date, your first-pass and final score lines copied from the score
log, the number of runs) and one table whose rows are:

| # | Slice | Case kind | Field or spec section | What was missing or ambiguous | What you guessed | Pass |
|---|---|---|---|---|---|---|

- **Slice**: S1 to S4.
- **Case kind**: `observed`, `predicted`, or `none` for a point not tied to a case.
- **Field or spec section**: a golden field pattern (`chain.B2.level_seed.N`) and/or a spec section
  (`rng/seeds § step 1`). Cite sections, never findings (you have none).
- **What was missing or ambiguous**: the sentence that was absent, unclear, contradicted by another sentence or by the
  data, or a value you needed that no document gives. Quote the sentence when there is one.
- **What you guessed**: what you did in its place, and why that guess. "Nothing, the spec was clear but I misread it"
  is a valid row: say so.
- **Pass**: `first` for a gap that showed before the first check (a guess you made while writing), `later` for one
  that showed after a check.

Rules for the rows: a row for **every** field prefix with a first-pass mismatch, and for **every** place you had to
guess, mismatching or not (a lucky guess is still a gap). Do not diagnose the specs beyond the row; the architect
triages. Do not edit any spec or any file of the sandbox's `docs/`. Say plainly if a slice cost you more than the spec
should have asked (for example a table column whose meaning you only found by trial).

## Slices

| Slice | Sandbox | Fields | Specs you should need |
|---|---|---|---|
| S1 seeds | `workspace/cleanroom/S1/` | `chain.A*`, `chain.B*` | rng, rng/seeds, chain § A-B, data/excel (Levels) |
| S2 drops | `workspace/cleanroom/S2/` | `chain.G1.*` | items/tc, items/quality, data/excel, rng |
| S3 pools | `workspace/cleanroom/S3/` | `monsters.pool.*` | monsters/pool, data/excel, rng/seeds |
| S4 DRLG | `workspace/cleanroom/S4/` | `drlg.maze.*`, `drlg.outdoor.*` | drlg/overview, drlg/maze, drlg/outdoor, drlg/preset, drlg/room-tiles, formats ds1 and dt1 |

"Specs you should need" is the plan's expectation, not a boundary: you may read anything in the sandbox. If you needed
a spec that is not in your row, that is a ledger row too.

## Ending

Report to your caller: the sandbox path, the first-pass and final score lines, the ledger path, and any read you made
outside the sandbox (an honest note makes a re-run cheaper than a discovered one).
