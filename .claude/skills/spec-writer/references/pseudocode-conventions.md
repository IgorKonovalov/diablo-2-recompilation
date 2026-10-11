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
