# <Table> (`data/global/excel/<Table>.txt`)

> **Source archive:** patch_d2.mpq (after precedence)   **Rows:** N (excluding header and `Expansion` separator rows)
> **sha256:** …   **Doc status:** columns listed | semantics partial | complete

## Purpose

One paragraph: what one row represents, and which subsystem(s) read it (link the research-map rows).

## Row identity

The key column(s) and how other tables reference a row (by name? by row index? by code?). Note any
separator rows (e.g. `Expansion`) and whether they take up an index. **This matters**: code often
indexes by row number. `[L]`/`[I]`/`[C]`

## Columns

| Column | Observed type / range | Meaning | References | Tag |
|---|---|---|---|---|
| `Name` | str, unique, 0 empty | … | — | [L] |
| `Picks` | int, −6..7 | … | — | [L] |

Generate the observed type and range columns with a script. Never type them by hand.

## Interpretation notes

Anything a reimplementer needs that isn't per-column: computed columns, groups of columns that
work together (`Item1..10`/`Prob1..10`), and the code findings that define the semantics (as links).

## Open questions

`[L]` items waiting on the reverser, each with a backlog link.
