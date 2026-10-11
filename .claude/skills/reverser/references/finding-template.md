# NNNN — <topic>

> **Subsystem:** rng | items/tc | … (a research-map row)
> **Question:** one line
> **Date:** YYYY-MM-DD   **Plan:** NNNN   **Status:** open | answered | superseded by NNNN

## Answer (summary)

Three to eight tagged bullet claims. This is what the spec-writer reads first.

- [I] … (fn:Name@0x00XXXXXX)
- [C] … (0x00XXXXXX, run:YYYY-MM-DD-slug)

## Leads used

- [L] `src:<id>`: what it claimed, and whether it held up for 1.14d.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|

## Walkthrough

The logic in prose and pseudocode, in execution order. Include short decompile excerpts from our
binary with renamed identifiers. Mark RNG draws explicitly (`draw#1 from item seed`), and state
integer widths and every branch on difficulty, expansion or player count.

```c
// fn:TC_Pick@0x00XXXXXX (trimmed)
```

Where a call graph, a branch structure or a struct relationship is easier to see than to read, add
a ` ```mermaid ` diagram (rules: `.claude/skills/spec-writer/references/pseudocode-conventions.md`
§ Diagrams). It illustrates tagged claims made in the text and makes none of its own.

## Data touched

`tbl:` anchors for every column read, and `struct:` anchors for fields read or written.

## Dead ends

What looked plausible and turned out wrong. This saves the next session from repeating it.

## Open questions

Each one says what would resolve it (an experiment idea, or code still to read).
