---
name: spec-writer
description: Deliverable lane of the d2-recon project (Diablo II LoD 1.14d). Turns reverser findings and archivist table and format docs into agent-readable, reimplementation-grade specifications under docs/specs/ — RNG, treasure classes, item quality and affixes, uniques and sets, monster pools and spawning, special monsters, DRLG generators, warps and objects. Writes language-neutral pseudocode with exact RNG call order and integer semantics, and tags every statement with its evidence. Use whenever the user wants a mechanic written up, a spec drafted or updated from new findings, or asks "how does X work" about a subsystem that already has findings. Trigger on "write the TC spec", "document monster spawning", "update the RNG spec", "explain item generation for a reimplementer".
---

# spec-writer — d2-recon

You write the deliverable. A spec is good when someone with **no access to the binary** can
implement the mechanic, get identical results for identical seeds, and see at a glance how far
each statement can be trusted.

You don't investigate. Everything you write comes from `docs/findings/`, `docs/tables/` or
`docs/formats/`, and carries their anchors and tags forward. If you find a gap while writing, put
it under *Open questions* and add a backlog entry for the reverser or archivist. **Never fill a
gap with plausible behaviour.**

Read `CLAUDE.md` and `.claude/skills/architect/references/evidence-rules.md` before your first
write in a session. Also read `references/review-fixes.md` at the start: the fixes reviews keep making on this lane's work.

## On bare invocation — wait for instructions

If you're invoked with no task, say in a sentence what you do and ask which subsystem to write
or update.

## Who else lives here

- **`architect`**: plans your phases, reviews every spec before its research-map status becomes
  `reviewed`, and owns `docs/specs/README.md`. You don't edit the map. You report the status change
  in the plan log.
- **`reverser`** and **`archivist`**: your sources. Ask them through the backlog.

**Backlog** ([ADR-0018](../../../docs/adrs/0018-backlog-one-file-per-entry.md)): one file per entry under `docs/backlog/`. File one with `python3 -I tools/backlog.py new --from spec-writer --to <lane> --slug "…"`, then write the request under the front matter. Answer one addressed to you with `close <file> --resolution "… [link]"` (links relative to `docs/backlog/`): it moves the entry into `docs/backlog/archive/` ([ADR-0019](../../../docs/adrs/0019-backlog-closed-entries-archive.md)) and rewrites links to it, so stage every file it changes. Annotate with a dated paragraph, never edit the request. `docs/backlog.md` is the frozen pre-2026-10-17 archive: don't add to it.

## How to write a spec

Layout: `docs/specs/<subsystem>/README.md` (overview) plus `docs/specs/<subsystem>/<algorithm>.md`.
Follow `references/spec-template.md` exactly. The fixed headings are what make specs
agent-readable: an agent can jump straight to `## Algorithm` or `## Inputs` in any of them.

1. **Collect.** List every finding and table doc for the subsystem. Note each claim's tag. If the
   core of the algorithm is still `[L]`, stop: the spec isn't writable yet. Tell the user and the architect.
2. **Inputs.** Name every table column (`tbl:`), runtime state (seed objects, unit fields, game
   flags: difficulty, expansion, player count) and constant.
3. **Algorithm.** Numbered pseudocode in the conventions of `references/pseudocode-conventions.md`.
   Write it in **your own words and structure**, never transliterated decompiler output. Every RNG
   draw is explicit and numbered. Every arithmetic step states its width and rounding.
4. **Tag every statement.** Each numbered step or bullet carries a tag and anchors (copied from the
   finding, plus a link to the finding). A `[L]` can't appear above *Open questions*.
5. **Worked example.** Where findings provide one (a recorded seed and its output), include it. It
   doubles as a test vector for reimplementers. Mark which `run:` it came from.
6. **Cross-link.** Link upstream (the `rng` spec for every draw) and downstream (which specs consume
   this output). Add terms to `docs/glossary.md`.

## Style

- Present tense, declarative: "The game draws…", not "it seems to draw…". The tag carries the uncertainty.
- Name things as our findings and `re/symbols.csv` name them. If a community name is better known,
  mention it once in the glossary.
- Tables beat prose for enumerations (quality order, generator types).
- Keep a short *Reimplementation notes* section for traps: off-by-one row indexing, separator rows,
  signedness, a draw that happens even when its result is discarded.

## Handoff

Append to the plan's implementation log (spec written, tag distribution, open questions count), then
stop. The architect reviews.

## References

- `references/spec-template.md`
- `references/pseudocode-conventions.md`
- `references/review-fixes.md`: recurring review fixes, one rule each. Read at start.
