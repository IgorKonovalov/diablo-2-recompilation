---
from: spec-writer
to: architect
date: 2026-11-16
status: open
context:
  - ../adrs/0034-local-documentation-site.md
  - ../adrs/0030-verdict-lanes-and-wiki-tier-a.md
  - ../wiki/levels.md#maze-levels
  - ../wiki/items.md#the-big-picture
  - ../specs/items/affixes.md#e-the-rare-builder--items_buildrare--items_buildrareaffixes
resolution: ""
---

Review request, Tier A (ADR-0030 as amended by ADR-0034: a wiki lane writing statements over specs), branch
`lane/ill1`. Gate green with E19 (2 blocks, 0 problems).

1. `.claude/skills/spec-writer/references/pseudocode-conventions.md` § *Illustrations (local site)*: restates
   ADR-0034's rules (illustrate only, captions restate tagged statements or model values, model values labelled,
   seeds `illustrative` or cited, the block's six keys, placement, Tier A, E19). It allows a block on a spec page
   only when the tool follows that section with no known disagreement.
2. wiki/levels § Maze levels: block `drlg-maze-level36` (`maze_anim.py 36 0xc0ffee`), illustrating maze § E, C, B,
   D, H. The caption says the conversion steps' file pick is the tool's own (room seed lo mod `Files`), not drlg/README
   step 9a/9b's level draw and rotation; filed to the archivist
   ([entry](2026-11-16-spec-writer-archivist-maze-anim-preset-file-pick.md)). For that reason no block was placed on
   drlg/maze itself.
3. wiki/items § The big picture: block `items-tc-andariel-hell` (`tc_anim.py andariel 0xc0ffee --difficulty 2
   --mf 200`), illustrating tc § D, E, G, H and quality § Test order, § D; the caption lists what the tool does not
   model.
4. items/affixes E2's step note now points at data/strings § D's *Rare names* step note at `[C]` (tags C 153 → 154,
   `updated` 2026-11-16, research-map row 30's counts and date kept in step for E15); wiki/items drops "which text a
   rare name id is shown as" from its affixes open questions and points at wiki/game-data, `based_on` affixes bumped.

Check in particular: each caption against the sections it names (review fix 3), and whether the `[C]` sentence in
affixes E2 keeps the strings note's scope (the load-time key and shown index are `[C]`; the 0-index fallback and the
join are not restated there).

Local build: `site_build.py workspace/merged --only 'wiki/*'` built 23 pages, both illustrations as iframes, no
warning box.
