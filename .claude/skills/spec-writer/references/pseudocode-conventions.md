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
- The gate also draws every block as GitHub would (rule E17): a block that fails there, or a label that does not reach the drawing, is an error. GitHub decodes HTML entities first, so write `#quot;`, `#lt;` and `#gt;` in labels, never `&quot;`, `&lt;` or `&gt;`. A `<word>` in a label is taken for an HTML tag and dropped. A node id keeps only its last label. A `;` ends a sequence message.
- "Unable to render rich display" on GitHub for a block that E17 passes, with no parse error in the box, is GitHub's diagram frame, not the block: reload later before changing anything (plan 0071, 2026-11-19).

## Illustrations (local site)

[ADR-0034](../../../../docs/adrs/0034-local-documentation-site.md) lets a page name an animated illustration that
`tools/site_build.py` builds on the reader's own machine from their own game files: a maze growing room by room, a
drop resolving from its treasure class. The picture is game art and never enters git, so the page names it with a
fenced block, never with a link or an image.

- **Illustrate only, like a diagram.** An illustration makes no claim of its own and carries no tag. Every caption,
  "How to read this" line and calculation line restates a tagged statement of a spec or finding, or shows a value the
  replay model computes for that statement. Where the illustration and the spec disagree, the spec wins and the
  illustration is a bug: file it to the archivist, who owns the generators.
- **Model values are labelled.** A number our model computes (`tools/maze_replay.py`, `tools/tc.py`, …) is said to be
  computed by our model, never presented as observed in the game.
- **Seeds.** `seed: illustrative` unless a recorded run or finding names the seed; then `seed` cites that record
  (`run:…` or the finding's section).
- **The block.** Info string `illustration`, one `key: value` line per key (a value may continue on indented lines),
  these six keys, and the optional `values`:

  | Key | Holds |
  |---|---|
  | `id` | unique across `docs/`, `[A-Za-z0-9][A-Za-z0-9_-]*`; the build writes `workspace/site/illustrations/<id>/` |
  | `tool` | a script name in `tools/` (`name.py`) |
  | `args` | the tool's arguments after the data root, which the builder supplies: a level id, a seed, a row name, flags; never game data. May be empty |
  | `seed` | `illustrative`, or the record that names it |
  | `illustrates` | the spec sections it shows, as relative links with `#anchor`s, separated by spaces or commas; a long list continues on indented lines |
  | `caption` | a short paragraph restating the sections named in `illustrates`, plus the model label and anything the tool leaves out that a reader could take for shown |
  | `values` | optional: `computed` (the default; the builder appends "Every value shown is computed by our model, not observed in the game.") or `restated`, for frames that restate a spec's list with no model behind them (the builder appends "The picture restates the spec; nothing shown is observed in the game."). `seed: none` is for a generator that draws on no seed |

  ````markdown
  ```illustration
  id: drlg-maze-level36
  tool: maze_anim.py
  args: 36 0xc0ffee
  seed: illustrative
  illustrates: ../specs/drlg/maze.md#c-random-growth
  caption: The maze grows one room at a time; …
  ```
  ````

- **Where.** On a wiki page, at the end of the section whose prose it illustrates. The prose must explain the step
  without the picture: a reader on GitHub, or one who has not built the site, sees only the block. A spec may carry a
  block after the heading it illustrates, as with a diagram, and only after the pseudocode, never in its place; the
  tool must then follow that section without a known disagreement.
- **Review.** A lane that places or edits a block, or writes a generator's caption or calculation text, writes
  explanatory statements over specs and takes Tier A ([ADR-0030](../../../../docs/adrs/0030-verdict-lanes-and-wiki-tier-a.md)).
- **The gate checks the block** (rule E19 of `evidence-rules.md`, `python3 -I tools/site_build.py check`): the six
  keys and nothing else, a valid unique `id`, a `tool` that exists, `illustrates` links whose file and `#anchor`
  resolve. It does not check that the caption restates the section; review does.
