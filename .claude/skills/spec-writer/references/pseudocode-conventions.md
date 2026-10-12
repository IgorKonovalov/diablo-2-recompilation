# Pseudocode conventions

Specs use one small, language-neutral pseudocode. Keep it boring and unambiguous.

## Types

`u8 u16 u32 u64 i8 i16 i32 i64` for fixed widths, and `bool`. Write the width on the first use of
every variable: `count: i32 ← tbl.Picks`. Never write a bare "int".

## Operators

| Write | Means |
|---|---|
| `a ÷ b` | integer division, truncating toward zero (C semantics); state if floor is meant |
| `a mod b` | C `%` (sign follows the dividend); say so when an operand can be negative |
| `a × b` | multiplication; note overflow width when it matters: `(u64) a × b` |
| `a >> n`, `a << n`, `&`, `|`, `^` | bitwise; `>>` on signed values is arithmetic, say if not |
| `←` | assignment |
| `clamp(x, lo, hi)`, `min`, `max` | as usual |

## RNG draws

Every draw is visible, numbered within the algorithm, and names its seed object:

```
r ← RNG.Range(seed: item.seed, n: 100)      ; draw#3
```

When a draw is conditional, say so. When a value is drawn but unused on some branch, keep the draw:
reimplementations must consume the same number of draws.

## Tables

`Levels[levelId].MonLvl[difficulty]` for keyed access. State whether an index is a row index (and
whether separator rows count) or a key lookup.

## Control flow

`if / else if / else`, `for i in 0 ..< n` (exclusive), `for i in 0 ... n` (inclusive),
`while`, `return`. Indent by 2 spaces. Number top-level steps (`1.`, `2.`); sub-steps may be
`2a.`, `2b.`.

## Tags in pseudocode

Put the tag and anchors at the end of the line, aligned, as in the template. A block of several
lines from one function may share one tag on its first line, followed by `(all of 4a–4d)`.

## Diagrams (Mermaid)

**Draw whenever a section has a shape** (owner request, 2026-10-12). A spec reads top-down as
pictures first, pseudocode second. Each pseudocode section, record layout or lookup gets a fenced
` ```mermaid ` block when it has one of these shapes:

| Shape | Mermaid form |
|---|---|
| pipeline or data flow between stages | `flowchart LR` |
| decision order, branch ladder (superunique → champion → unique → else) | `flowchart TD` with decision nodes |
| tree of derived objects (seeds, rooms, TC picks) | `flowchart TD` |
| RNG call order across functions, who calls whom with which seed | `sequenceDiagram` |
| record or bit-field layout (file headers, item bit fields, struct offsets) | `packet-beta` (bit ranges), else `block-beta` |
| index space split into ranges, table → table lookups | `flowchart LR` or `block-beta` |
| states and transitions (flags set and cleared, game/room lifecycle) | `stateDiagram-v2` |

A spec of more than a page normally has an overview diagram near the top (the whole chain, inputs to
outputs) plus one per major section that has such a shape. Skip a diagram only where it would repeat
a three-line step or a plain list. Keep each diagram small enough to read without scrolling (about
25 nodes); split a larger one by section.

- **Pseudocode stays normative.** A diagram illustrates statements made elsewhere in the spec. It
  makes no claim of its own, so it carries no tags; every fact in it must also appear in a tagged
  step or note. If a diagram and the pseudocode disagree, the pseudocode wins and the diagram is a bug.
- Put it right after the heading it illustrates, followed by the pseudocode, never in its place.
- Use the same names as the pseudocode and `re/symbols.csv`. Addresses are optional in node labels.
- Prefer `flowchart` (LR for pipelines, TD for trees). Quote any label containing `( ) [ ] { } : ;`
  or a backslash: `A["DATA\GLOBAL\EXCEL\x.bin"]`.
- The docs gate parses every block (rule E9 of `evidence-rules.md`): a block Mermaid can't parse, such as a non-contiguous `packet-beta`, is an error at its `file:line` and denies the commit.
