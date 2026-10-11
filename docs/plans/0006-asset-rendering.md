# 0006 — Asset rendering: palettes, DT1 tiles, DC6, DCC (tools-only)

> **Status:** in-progress (approved): Phases 1 and 2 done, awaiting architect review
> **Created:** 2026-10-11
> **Owner skill(s):** archivist
> **Related ADRs:** 0002-scope-creation-paths-and-enablers, 0005-presentation-formats-tools-only

## TL;DR

How do the game's tiles and sprites look, as images? This plan decodes palettes, DT1 tile
graphics, DC6 and DCC into PNGs under `workspace/render/`, using standard-library decoders in
`tools/`. It also builds a DS1 preset preview for looking at DRLG data. When it's done,
`docs/formats/` has `palette.md`, `dc6.md` and `dcc.md`, plus a pixel section in `dt1.md`. Every
DT1, DC6 and DCC file decodes with every byte accounted for, and one command regenerates all the
images. None of this is a deliverable spec (ADR-0005). No image enters git.

## Context

- ADR-0005 brings these formats in as tooling only: no research-map row, and renders aren't
  evidence.
- Ready now: `tools/dt1.py` walks all 361 484 DT1 pixel blocks (`0x0001` 256-byte diamonds, the
  `0x1001`/`0x2005` RLE forms), and `tools/ds1.py` parses all 2 276 DS1 files.
- Files are in `workspace/merged/data/global/`: `palette/<name>/pal.dat` and `pal.pl2` (act1–act5,
  menu0–4, units, loading, sky, static, …), DC6 ×1 676, DCC ×12 233, COF ×3 082.
- Pillow isn't installed. PNG output uses a small shared writer (`zlib` + `struct`), either as
  `tools/png.py` or inside `tools/palette.py`.
- **Priority:** within the archivist lane, every phase yields to plan 0005 Phase 4 (D2S) and to any
  backlog entry a core plan is blocked on. Phase 1 is small enough to run first.
- Leads: `src:siramy-ds1edit` covers the DT1 block encoding. Before DC6/DCC work, register
  community format docs in `docs/sources.md` (descriptions only: no third-party decoder source,
  per ADR-0001).

## Phases

### Phase 1 — Palettes, PNG writer, DT1 tile render
- **Owner skill:** archivist
- **What:** Decode `pal.dat` (and record the `pal.pl2` layout as far as the file shows it), write
  PNGs, and render every DT1 tile by placing its blocks at their `x`/`y`.
- **Outputs:** `docs/formats/palette.md`, a *Pixel data* section in `docs/formats/dt1.md`,
  `tools/palette.py`, a `render` subcommand in `tools/dt1.py`, and
  `workspace/render/tiles/<dt1 path>/<orientation>_<main>_<sub>_<n>.png`. Index 0 is transparent,
  and the palette is picked by act directory.
- **Done when:** every `pal.dat` decodes to 256 colours (the size and component order checked
  against all of them); `dt1.py render` covers all 257 version 7.6 files with no exception and
  writes one PNG per tile (16 456); the floor, wall and roof orientations are each checked by eye on
  a sample, with the result logged below; and the per-file contact sheet (`_sheet.png`) opens.

### Phase 2 — DS1 preset preview
- **Owner skill:** archivist
- **What:** Stitch a DS1's floor and wall layers into one isometric image from its tiles, picking
  the first tile with each key.
- **Outputs:** a `render` subcommand in `tools/ds1.py`, `workspace/render/ds1/<path>.png`, and a short
  *Preview* note in `docs/formats/ds1.md` saying what the preview simplifies.
- **Done when:** every DS1 that `LvlPrest` names renders, and missing tile keys are drawn as
  a marker and counted. The doc states that tile choice among rarity variants, layer order and
  shadows are simplified, so the preview illustrates the data and says nothing about DRLG
  behaviour (`[L]` items go to *Open questions*). Three known presets (for example the Rogue
  Encampment, a Tristram piece, a Durance level) are checked by eye.

### Phase 3 — DC6
- **Owner skill:** archivist
- **What:** Document and decode DC6 (file header, frame pointers, frame headers, RLE pixel
  stream) and render every frame.
- **Outputs:** `docs/formats/dc6.md`, `tools/dc6.py` (`survey`, `render`),
  `workspace/render/dc6/<path>/<dir>_<frame>.png`.
- **Done when:** `dc6.py survey` reads all 1 676 files with every byte accounted for, including any
  trailing terminator bytes, which are documented; frame counts and sizes are histogrammed; and a
  sample of inventory icons and UI panels is checked by eye, each with the palette it needs
  (`units` vs. `act*` vs. menus) recorded.

### Phase 4 — DCC
- **Owner skill:** archivist
- **What:** Document and decode DCC (the header, direction offsets, the per-direction bit
  streams, frame headers and the pixel-buffer/cell process) and render every frame of every
  direction.
- **Outputs:** `docs/formats/dcc.md`, `tools/dcc.py` (`survey`, `render`), and
  `workspace/render/dcc/<path>/<dir>_<frame>.png`.
- **Done when:** `dcc.py survey` decodes all 12 233 files, and in every direction each stream is
  consumed to exactly its stated bit length; files that can't be decoded are listed with the
  reason (the target is zero); and a sample of monster, player-layer and object animations is
  checked by eye.

### Phase 5 — COF single-frame composition (optional)
- **Owner skill:** archivist
- **What:** Parse COF (layers, frames per direction, per-frame layer order) and compose one frame of
  a unit from its component DCCs.
- **Outputs:** `docs/formats/cof.md`, `tools/cof.py`, and
  `workspace/render/units/<token>/<mode>_<dir>.png`.
- **Done when:** every COF parses with no leftover bytes, and one monster and one player class
  compose correctly by eye in at least two directions. Animation playback, timing (`animdata.d2`)
  and colour shifts (`.pl2` and monster palette shifts) are not done and are listed under *Open
  questions*.

## Open questions

- How the game picks a palette for an asset (by act, the `units` palette, colour-shift tables) is
  code behaviour. It stays `[L]`, and the renderer's choice is a documented heuristic.
- Shadow, transparency and blend modes (`.pl2` light/trans tables) are not modelled. Renders use
  flat palette lookup.
- Phase 5 may be dropped if Phase 4 runs long. It is the most likely to pull towards animation.
- ~~One command to regenerate all of `workspace/render/`: decide in Phase 1.~~ Decided in Phase 1:
  `python3 -I tools/render_all.py workspace/merged` (see the implementation log).

## Implementation log

_(lanes append dated entries as phases land)_

### 2026-10-11 — Phase 1 (archivist)

- **Produced:** `tools/png.py` (indexed PNG writer: IHDR/PLTE/tRNS/IDAT/IEND, index 0 alpha 0),
  `tools/palette.py` (`survey`, `swatch`, `palette_for_tiles()`), a `render` subcommand in
  `tools/dt1.py` (additive; `survey`/`dump`/`ds1keys` unchanged), `tools/render_all.py`,
  `docs/formats/palette.md`, and a *Pixel data* section in `docs/formats/dt1.md`.
- **Palettes:** `palette.py survey` reads all 18 `pal.dat`: each 768 bytes = 256 × 3, entry 0 black,
  entry 255 white, all 18 distinct. In all 16 directories with a `pal.pl2`, its first 1 024 bytes are
  the same colours as 4-byte entries in reversed byte order with a zero pad. Size is `[C]`; the B, G, R
  order is `[L]` (basis in palette.md). Rest of `pal.pl2` not decoded.
- **DT1 render:** `dt1.py render workspace/merged` covers all 257 version 7.6 files with no
  exception: 16 456 tile PNGs (counted on disk, no name collisions) and 257 `_sheet.png`, ~35 s.
  Pixel geometry is `[L]` (`src:siramy-ds1edit`); byte accounting stays `[C]` as before.
- **Doc fix:** dt1.md said the isometric block was "2+4+…+32+…+4+2 = 256 pixels"; that sum is 512.
  Corrected to rows of 4, 8, …, 32, …, 8, 4.
- **Regenerate-all decision:** a Python script, `tools/render_all.py <root> [out]`, not a Makefile:
  it keeps to the `python3 -I` rule, needs no `make`, and later phases plug in by adding a
  `render(root, out)` function (it skips and names missing steps: today `ds1`, `dc6`, `dcc`).
  `workspace/render/` is disposable.
- **By eye (sanity, not evidence; viewed with the image reader):**
  - Floor, `act1/town/floor/_sheet.png`: 160×80 diamonds of grass and dirt, textures continuous
    across the block seams, colours natural (green grass, brown earth). Looks right.
  - Wall, `act1/town/fence/_sheet.png`: wooden palisade sections and stone footings, upright and
    unbroken; orientation-13 shadow tiles render as black silhouettes (flat lookup, no shadow
    blending). Looks right.
  - Roof, `act3/kurast/roofs/_sheet.png`: 185 orientation-15 tiles of stone and thatch roof pieces,
    coherent. The file's 20 orientation-10 tiles are each a single colour index (flat green
    diamonds); that is the data, not a decoding fault. Not judged: whether `roof_height` should
    offset roofs (ignored by the renderer).
  - Contact sheets open (three viewed above). Palette swatches written to `workspace/render/palette/`
    but not inspected.
- **Surprises:** none in decoding; the dt1.md sum error above.

### 2026-10-11 — Phase 2 (archivist)

- **Produced:** a `render` subcommand in `tools/ds1.py` (additive; `--all`, `--only SUBSTR`), a
  *Preview* section in `docs/formats/ds1.md` listing the simplifications, and an Open-questions bullet
  there. `render_all.py` now picks it up with no change.
- **Run:** all 2 043 DS1 files that `lvlprest.bin` names render, 0 failures, ~5 min. 12 presets over
  60 M pixels are drawn at half scale. Missing keys are filled with an index-255 diamond and counted:
  11 floor and 61 wall cells in 13 files, all `expansion/icecave/*_dirt` and `expansion/siege/brdr*`
  (consistent with the no-DT1 list in dt1.md). 2 084 wall and 37 315 floor cells came from a DT1
  outside the DS1's own list; 768 orientation-10/11 cells are skipped.
- **By eye (sanity, not evidence):**
  - Rogue Encampment, `act1/town/townn1.png`: the palisade camp with tents, wagons, the stone
    walls, tree line and the river along one edge. Fences join up and floor textures are
    continuous. Looks right.
  - Tristram, `act1/tristram/tri_town4.png`: burnt house shells, dirt roads, stone walls, trees and
    the river on two sides. Looks right; dark blotches around the houses are floor tiles drawn as
    is (no lighting model), not judged further.
  - In both, flat blue bands run along some river/map edges. Not judged: they are drawn from
    real tile keys (no marker), probably edge or special tiles that the game does not show as-is.
  - **Durance: not checked.** The candidates are `act3/travincal/meph*.png`; stopped at the time
    budget before viewing one.
- **Not done in this phase:** a third by-eye check (Durance), and no comparison against the game.
