# ADR-0036 — Schematic illustrations in the public export: our own drawings may leave the machine, game art never (amends 0034, 0035)

> **Status:** accepted (owner, 2026-11-16: "for public export simplifications are fine btw, but diagrams and
> animations are needed"; asked how the export should draw the animations, the owner chose "Schematic")
> **Date:** 2026-11-16
> **Related plan(s):** [0070-redacted-public-export](../plans/0070-redacted-public-export.md)

## Context

[ADR-0034](0034-local-documentation-site.md) added animated illustrations to the local site. It ruled that they never
leave the machine, and that ADR-0009's export "carries no illustrations". The reason was game art: `maze_anim.py`
draws the level's floor and wall tiles from DT1/DS1 files in the game's palette, and `tc_anim.py` ends each drop with
the items' inventory icons, decoded from DC6 files. [ADR-0009](0009-public-documentation-site.md) keeps all game art
out of any export. [Plan 0070](../plans/0070-redacted-public-export.md) therefore dropped every illustration block
from the cut, and its publish check failed on any image (X8) and any file but Markdown (X11).

On 2026-11-16 the owner said: "for public export simplifications are fine btw, but diagrams and animations are
needed". Mermaid diagrams were already in the export. The animations were not. The owner was asked how the export
should draw them, given that the current ones show game art, and chose "Schematic".

What makes an animation useful is not the art. It is the sequence of steps, the draws on each step, the calculation
panel and the caption. All of that is ours: the replay models in `tools/`, the captions in reviewed Markdown, the 5×7
bitmap font in `tools/anim_common.py`. Only the tiles, the icons and the game palette are the game's.

## Decision

**The export may carry illustrations drawn in a schematic mode, with our own graphics only.** Game-art illustrations
still never leave the machine.

- **Schematic means no pixel from a game file.** The maze shows rooms as labelled boxes, with their doors and the
  entry and exit marks; no tiles and no DS1 floor or wall layout. A treasure-class drop shows each item as a name card
  coloured by its quality; no icons. Colours are our own fixed palette, never the game's. The steps, the calculation
  panels, the captions and the "How to read this" lines are the same as in the full mode.
- **Each generator gets a `--schematic` mode.** `tools/maze_anim.py` and `tools/tc_anim.py` first; a later generator
  joins the export only when it has one. In this mode the tool does not open any art file (DT1, DS1 tile layers, DC6,
  DCC, palettes) and does not import the modules that decode them. It still reads the tables its model needs, from the
  user's own files, at build time, as ADR-0034 allows.
- **A schematic output is marked.** The tool, in schematic mode only, writes a marker into each file it makes and a
  list of its files with their hashes. The export's builder runs illustration blocks in schematic mode only. The
  publish check allows exactly those files: an image or step-through page passes only when it sits in an illustration
  folder, carries the marker, and matches the list. Every other image still fails.
- **The illustration rules of ADR-0034 hold unchanged.** Illustrations make no claim of their own; captions restate a
  spec; computed values are labelled as computed by our model; seeds are labelled `illustrative`. A schematic
  illustration in the export follows the export's redaction too: its captions and calculation text pass the same
  check as the page around it.
- **Simplification is the plan's.** ADR-0009 leaves the redaction depth to the plan that builds the export. Plan 0070
  records the owner's "simplifications are fine": the redactor may drop whole sentences, bullets, rows or sections
  that fail the check, and logs each drop.

## Consequences

### Positive
- The export keeps what the owner asked for: diagrams and animations, beside the text.
- The animation's value, the order of the draws and the arithmetic, reaches readers without any game art.
- The allowlist is narrow and mechanical: a marker, a hash list, one folder per illustration.

### Negative
- **A schematic drawing teaches less at a glance.** A maze of boxes is less vivid than tiles; a name card is less
  recognisable than an icon. Readers who own the game can still build the full local site (ADR-0034).
- **The marker is our own promise, not proof.** A tool bug could mark a file that holds art. Three things narrow this:
  the schematic mode does not import the art decoders (a test proves it), the generators' lanes are reviewed at Tier
  A, and the export's redaction review looks at every illustration in the cut.
- **The export now holds files that are not Markdown.** The check's file-type rule is no longer "Markdown only". It
  is "Markdown, `cut.json`, and marked schematic files". Each exception is a place for a mistake.
- **The step-through page carries a small inline script.** The check otherwise bars scripts in the cut. The
  exception is the generator's own page template, marked and listed; it makes no network request.
- **Table values reach the export inside the drawings.** A drop's weights and a maze's room sizes are computed from
  the user's tables at cut time. They are short and illustrative, as ADR-0009 allows for tables. A frame never shows a
  whole table.

### Neutral
- The local site of ADR-0034 is unchanged. It keeps the full, game-art mode and is never shared.
- ADR-0035's hosting is unchanged. The illustrations are static files the Starlight site serves from its public
  folder; Mermaid is still drawn in the export repository's CI.
- ADR-0009's bans are unchanged: no game art, no logos, no text dumps.

## Alternatives considered

### Keep the export free of illustrations (ADR-0034 as written)
Simplest and the safest. It lost because the owner said the animations are needed.

### Publish the full illustrations, game art included
The most vivid. It lost because tiles, icons and the palette are game art, which ADR-0009 keeps out of any export.

### Hand-drawn diagrams in place of animations
Mermaid already covers the static shapes. It lost because a hand drawing can't show one seed's draws step by step,
and it would add drawings no model checks.
