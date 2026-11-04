# ADR-0031 — Constants of the code image: a short table only where no exact rule gives it, and a survey checks every rule

> **Status:** accepted (owner, 2026-11-04)
> **Date:** 2026-11-04
> **Related plan(s):** 0054-path-search

## Context

A reimplementation needs some constant tables that live in `Game.exe`'s data and in no game file: direction tables, step tables, a distance table. They are constants of the code. They aren't excel, sprite or map data, and the non-negotiable "game data never enters git" didn't say what to do with them.

`lane/a54` wrote all 882 elements of the path planners' 15 tables into `docs/tables/PathDirTables.md`. The `lane/s60` review had already allowed 64 values of one table, on the test "can't do without". The `lane/a54` review found that most of the 882 don't pass that test, because a rule the survey can check gives each of them, and put the scale to the owner: the repository is public, [ADR-0009](0009-public-documentation-site.md) records that a full dump of a table is the more exposed form, and history is never rewritten, so a merge that gets pushed can't be taken back.

## Decision

A constant of the code image that a reimplementation needs may appear in `docs/` **only where no exact rule gives it**, as a short table with its address and its reader. **Anything a rule gives is written as the rule**, and a survey computes the rule's values and compares them with the pinned image element by element, so that the docs gate fails on any difference. Checksums stay in the survey. A rule states its width and rounding and gives bit-identical values. A rule found by matching data is `[C]` as an equality on the pinned image's elements and is no claim about how the table was generated. A rule here is a short expression, or a derivation from a table the same doc gives, and a fit that needs a case per group of rows or a patched exception doesn't count as one, so that nobody forces a rule to shrink a table. Excel, sprite and map data stay out whole, as before.

## Consequences

### Positive
- The public tree holds as few of the image's values as a reimplementation can work with, and loses nothing: each value can be computed from the doc alone.
- A rule can't drift from the image without the gate going red, which a listed value typed by hand can't promise.
- A later lane has a test to apply, not a size to argue about.

### Negative
- A rule is harder to read at a glance than a list, and the reader must trust or re-run the survey that it is exact.
- "A short expression" against "a fit" is a judgement. `g_DirOctant` has an exact four-case description and `g_PathDirTriples` an exact derivation with one exception, and both stay listed under this wording. The owner may read that line differently, and the review of each new table has to draw it again.
- A survey needs the pinned image to run, so the check only holds where that image is present, as for every other image survey.
- The values already pushed elsewhere in the docs aren't removed: this ADR rules on what is written from now on, and history is never rewritten.

### Neutral
- `CLAUDE.md`'s "Game data never enters git" bullet and the archivist skill's "never dump a whole table" line are to carry a pointer here; the wording is in [plan 0054](../plans/0054-path-search.md)'s log.
- `lane/s60`'s 64-value table in [items/inventory](../specs/items/inventory.md) is the kind this allows: no exact rule is known for it.

## Alternatives considered

**Keep all 882 values.** Simplest for a reader, and nothing to verify. It lost because 604 of them don't pass the "can't do without" test, and a pushed dump can't be withdrawn.

**No values in git; the reimplementer reads them from their own image.** The least exposure. It lost because the tables with no rule would then leave the doc unable to specify the planners on its own, for the sake of 278 small numbers.
