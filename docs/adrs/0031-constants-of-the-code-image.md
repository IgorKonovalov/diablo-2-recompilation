# ADR-0031 — Constants of the code image: a short table only where no exact rule gives it, and a survey checks every rule (amends 0009)

> **Status:** accepted (owner, 2026-11-04)
> **Date:** 2026-11-04
> **Related plan(s):** 0054-path-search

## Context

A reimplementation needs some constant tables that live in `Game.exe`'s data and in no game file: direction tables, step tables, a distance table. They are constants of the code. They aren't excel, sprite or map data, and the non-negotiable "game data never enters git" didn't say what to do with them.

`lane/a54` wrote all 882 elements of the path planners' 15 tables into `docs/tables/PathDirTables.md`. The `lane/s60` review had already allowed 64 values of one table, on the test "can't do without". The `lane/a54` review found that most of the 882 don't pass that test, because a rule the survey can check gives each of them, and put the scale to the owner: the repository is public, [ADR-0009](0009-public-documentation-site.md) records that a full dump of a table is the more exposed form, and history is never rewritten, so a merge that gets pushed can't be taken back.

The owner ruled on 2026-11-04: "keep the 343 values no rule can produce, and write the other 539 as rules the survey checks against the image; nothing is lost, checksums stay in the survey, and `CLAUDE.md` gets a short exception that [the architect approves]." Writing the rules, `lane/a54b` found a one-line rule for 65 of the 343, so the tree holds 278 listed and 604 by rule. That is the ruling's own test applied to what is now known, in the less exposed direction, and not a change to it.

## Decision

A constant of the code image that a reimplementation needs may appear in `docs/` **only where no exact rule gives it**, as a short table with its address and its reader. **Anything a rule gives is written as the rule**, and a survey computes the rule's values and compares them with the pinned image element by element, so that the docs gate's full tier fails on any difference. Checksums stay in the survey. A rule states its width and rounding and gives bit-identical values. A rule found by matching data is `[C]` as an equality on the pinned image's elements and is no claim about how the table was generated. Excel, sprite and map data stay out whole, as before. Whether a description by cases, or one with a stated exception, counts as a rule is not decided here: the ruling doesn't say, and it is the owner's (Consequences, Negative).

## Consequences

### Positive
- For these tables the public tree holds only the listed values and loses nothing: every other value can be computed from the doc alone.
- A rule can't drift from the image without the gate going red, which a listed value typed by hand can't promise.
- A later lane has a test to apply, not a size to argue about.

### Negative
- A rule is harder to read at a glance than a list, and the reader must trust or re-run the survey that it is exact.
- **What a rule excludes (owner, 2026-11-04).** A description by cases, or one with a patched exception, does not count as a rule here: a table that needs one stays listed. `g_DirOctant` (75) and `g_PathDirTriples` (75) each equal such a description on every element of the pinned image, the first in four cases (the centre, an axis cell, a diagonal, the rest), the second alike with one cell's two directions swapped, and they stay listed, as the owner's 343 named them. The tree holds 278 listed and 604 by rule.
- A survey needs the pinned image to run, so the check only holds where that image is present, as for every other image survey.
- The values already pushed elsewhere in the docs aren't removed: this ADR rules on what is written from now on, and history is never rewritten.

### Neutral
- This amends [ADR-0009](0009-public-documentation-site.md) on one point: its Context says `docs/tables/` holds schema, semantics and short illustrative rows, and it now also holds these listed constants, which the export plan's publish check has to treat as data. ADR-0001, which that Context names beside `CLAUDE.md`, has no sentence on this to amend.
- `CLAUDE.md`'s "Game data never enters git" bullet and the archivist skill's "never dump a whole table" line carry a pointer here; the wording is in [plan 0054](../plans/0054-path-search.md)'s log.
- **Note, 2026-11-04 (`lane/a70`).** The counts above, 882 elements in 15 tables with 278 listed and 604 by rule, are of the tables `lane/a54` documented. `g_PathFaceStep` (64 elements at `0x006EB548`) is a sixteenth, given by one exact rule and checked by the survey, so [PathDirTables](../tables/PathDirTables.md) now holds 16 tables, 946 elements, 278 listed and 668 by rule. The decision is unchanged; the 278 listed gained nothing.
- `lane/s60`'s 64-value table in [items/inventory](../specs/items/inventory.md) is the kind this allows: no exact rule is known for it.

## Alternatives considered

**Keep all 882 values.** Simplest for a reader, and nothing to verify. It lost because 604 of them don't pass the "can't do without" test, and a pushed dump can't be withdrawn.

**No values in git; the reimplementer reads them from their own image.** The least exposure. It lost because the tables with no rule would then leave the doc unable to specify the planners on its own, for the sake of 278 small numbers.
