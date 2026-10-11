# 0006 — Asset rendering: palettes, DT1 tiles, DC6, DCC (tools-only)

> **Status:** done (closed 2026-10-11)
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
  - In both, flat blue bands run along some river/map edges. Not judged at the time; the review
    identified them as hidden (bit 31) collision-filler cells, see the review-fix entry below.
  - Durance (`act3/travincal/mephcomp.png`, checked in review): reads correctly as a temple complex
    with ornate pillared walls, round floor plates and a central blood-red channel and cross. Its
    green strips are 26 hidden invisible-wall cells (`act1/barracks/inviswal.dt1`), fixed by fix 1.
- **Not done in this phase:** no comparison against the game.

### 2026-10-11 — Phases 1–2 review fixes (archivist)

Architect review: accept with fixes. Applied fixes 1–4:

1. **Hidden cells:** `ds1.py render` skips bit-31 cells by default (`--hidden` draws them) and counts
   them. Re-rendered: `townn1` 43 wall cells skipped, `tri_town4` 126 wall, `mephcomp` 26 wall + 1
   floor. In `townn1` the river bands are gone apart from a few short unhidden filler pieces (viewed),
   which ds1.md now records as data plus a reverser open question (cell low byte `0x81`).
2. **DT1 geometry:** `dt1.py render` prints a `geometry:` line and exits non-zero unless both counters
   are zero. Over all 257 files: RLE runs past column 32 = **0**; iso-only floor tiles 7 686 (all 25
   blocks), overlapping pixels = **0**. The isometric row shape, the RLE cursor rule and placement at
   header `(x, y)` are promoted to `[C]` in dt1.md; transparency of index 0 and the B,G,R order stay `[L]`.
3. **Malformed DS1s:** `ds1.py render` prints a `NOTE` for any file with leftover bytes
   (`act1/outdoors/swamp2.ds1`: leftover 44, under `--all`).
4. **Bookkeeping:** Durance check recorded in the Phase 2 entry, status and README row updated.

### 2026-10-11 — Phase 3 (archivist)

- **Produced:** `tools/dc6.py` (`survey`, `dump`, `render`), `docs/formats/dc6.md`, renders of all
  24 527 frames under `workspace/render/dc6/<path>/<dir>_<frame>.png` (24 527 PNGs, no path
  collision). `render` is wired as the `dc6` step of `render_all.py`.
- **Sources:** none. The layout was derived from the data and checked by byte accounting; nothing
  was read or registered in `docs/sources.md`.
- **Survey:** `SURVEY dc6 files=1676 frames=24527 errors=0 leftover_bytes=0`, exit 0. Header
  (24 B), pointer table, frame headers (32 B), RLE streams and 3 trailing bytes per frame tile every
  file exactly; every stream decodes to exactly `height` rows no wider than `width`. Layout `[C]`.
- **Trailer finding:** each frame is followed by 3 bytes that are not part of any field. They equal
  the header `terminator` byte ×3 in 24 047 frames, are `00 00 00` in 173 and other values in 307
  (59 files, mostly UI). Documented as padding `[I]`, not an end marker.
- **Surprise:** `next_block` (frame header `+0x18`) is not a file offset in any frame of 281 files
  (4 816 frames, values like `0x006F007C`, mostly `flp*` item-drop animations). The parser ignores
  it and uses `frame_ptr` + `length`. A first parser that trusted it failed those 281 files.
- **Histograms:** 705 files have 1 frame, 291 have 2, 258 have 17; the largest is 1 499 frames
  (`ui/automap/maximap*.dc6`). Directions: 1 in 1 640 files, 8 in 34, 4 and 16 in one each. Most
  common frame sizes 8×16, 16×32, 72×86, 2×2, 48×48; largest 256×256 (max width 319). `flip` = 1 in
  140 frames, all in `items/inv1x1`, `inv1x2`, `inv2x2`, `inv2x3`; `unk_14` = 0 everywhere.
- **By eye (sanity, not evidence)**, palette comparison sheets made in the scratchpad:
  - Inventory icons (ring mail, cap, axe, bow, red/blue potion, gem, bone shield): correct shapes
    and colours with `units`; `act1` and `act3` look the same; `menu0` breaks them into speckle.
  - Panels (`invchar6`, `800ctrlpnl7`, `hlthmana`, `questbackground`): correct with `units` and
    `act1`, text and frames right way up; `menu0` wrong.
  - Loading screen: correct only with `loading` (with `units`/`sky` it is speckled).
  - Front-end backgrounds (`gameselectscreenexp`, `charselectbckg`): coherent with `units` and
    `sky` (bluer); not decided. `menu0`–`menu4`, `static`, `trademark`, `fechar` are clearly
    wrong; `act5` is wrong on the game-select scene.
  - Fire logo, `local/ui/eng/exitd2` ("EXIT DIABLO" reads correctly), `blizz`: fine with `units`,
    `sky`, `act1`; the logo also with `act5`.
  - A flip = 1 frame (`inv2x3` frame 0, a shield) reads upright when drawn top-down.
  - No `menu*` palette fitted any DC6 sampled; which DC6s, if any, use them was not found.
- **Heuristic:** `palette_for_dc6()`: `loading` for `global/ui/loading/`, else `units`.
- **Not done:** no comparison against the game; front-end palette left undecided; monsters,
  objects, overlays and fonts were rendered but not viewed.

### 2026-10-11 — Phase 3 review fixes (archivist)

Phase 3 reviewed (architect), accepted with fixes 1–5; fixes applied:

1. **Frame trailer** (dc6.md): split into `[C]` (the parser never needs the bytes to find a frame
   end; their content is not constant) and `[L]` (padding the game does not read; debug-fill reading).
2. **Retagged `[L]`** (data-only interpretations): the header `terminator` meaning, `next_block`
   "stale memory", right-padding of short rows (a renderer convention).
3. **Row order:** new `dc6.py rows` check over the 14 `local/font/latin` fonts (glyph index =
   character code). T's widest row is above L's in all 14; the descender test is `ok` in 7
   (`font6`, `font8`, `fontformal10`–`12`, `fontingamechat`, `reallythelastsucker`), inconclusive
   in 7 display fonts, contradicted in none: `ROWS dc6 fonts=14 t_above_l=14 descenders_ok=7
   descenders_inconclusive=7 descenders_contradict=0`, exit 0. "flip = 0 → stream row 0 is the
   bottom" promoted to `[C]` as an encoding claim; flip = 1 and `offset_x`/`offset_y` stay `[L]`.
4. **ds1.md:** object `x`/`y` sub-tile meaning (table and bullet) and "a path belongs to the object
   at its start" retagged `[I]` → `[L]` (data only, no code anchor).
5. This entry. The `render_all.py` docstring fix is left to the Phase 4 (DCC) work.

### 2026-10-11 — Phase 4 (archivist)

- **Produced:** `tools/dcc.py` (`survey`, `dump`, `render`, parallel with `--jobs`),
  `docs/formats/dcc.md`, renders of every frame under `workspace/render/dcc/<path>/<dir>_<frame>.png`
  (1 396 764 PNGs from 12 233 files, 0 failures, about 3 min). `dcc.render` is the `dcc` step of `render_all.py`, whose docstring now names the
  steps that actually run.
- **Source:** registered `src:siramy-dcc` (Paul Siramy's DCC write-up) in `docs/sources.md` before
  use, as a description lead. It was recalled, not fetched or re-read; no decoder code was read. A web search
  only located the project page for the URL. Nothing was rejected.
- **Survey:** `SURVEY dcc files=12233 directions=119448 frames=1396764 errors=0 leftover_bits=0`,
  exit 0, about 2.5 min on 16 cores. No undecodable files. In every direction the `equal_cell`,
  `pixel_mask`, `encoding_type` and `raw_pixel` streams are consumed to exactly their 20-bit stated
  lengths. The `pixel_code` stream (no length field) leaves 0–7 bits at the direction end in all
  119 448 directions, which is byte padding. The header, direction header, frame fields, cell split and per-step bit
  costs are `[C]` by this accounting.
- **`[L]` by design:** the stage 1 slot order (newest value first), the equal-cell copy and clear,
  image orientation, and the `bottom_up` = 1 and optional-data branches (no file uses them;
  `variable0`, `optional_bytes`, `bottom_up` are 0 everywhere). These change pixel values but not
  bit counts, so the accounting cannot pin them. Unknown meanings: header `tag` (always 1) and
  `total`, direction `outsize_coded` (equal to the frame-area sum in only 73 directions), frame
  `coded_bytes`.
- **Histograms:** directions 16 (5 001 files), 8 (4 359), 1 (2 768), 4 (56), 32 (49);
  `frames_per_dir` 1..200; `compression` 0/1/2/3 = 46 287 / 10 808 / 31 239 / 31 114 directions;
  pixel key 1..224 entries; 448 distinct field-width combinations.
- **By eye (sanity, not evidence)**, contact sheets with the `units` palette, in the scratchpad:
  - Monsters: Fallen torso `fa/tr/fatrlita1hth` (red imp, horns, club arm, coherent across frames
    and two directions); skeleton torso `sk/tr/sktrhvya11hs` (bony torso, both directions);
    `su/summonerteleport` rendered without error.
  - Player layers: assassin torso `ai/tr/aitrhvya11hs` (dark armour with red trim) and a druid head
    `dz/hd` layer (grey wolf-like helm). Plausible, but small single layers are hard to judge
    without COF composition.
  - Objects: Rogue fountain `fn/tr/fntrlitnuhth` (archer statues on a round basin, sharp, upright)
    and gibbet `gi/tr/gitrlitonhth` (cage swinging across frames). Clearly correct.
  - Frames read upright with top-down canvas rows. No cell seams or smear between frames, which
    supports the equal-cell copy.
- **Not done:** no comparison against the game; missiles and overlays rendered but not viewed;
  palette choice (`units` everywhere) not explored; `variable0`, `coded_bytes`, `outsize_coded` and `total` not
  explained.

### 2026-10-11 — Phase 4 review fixes F1–F3, F5 (archivist)

The architect accepted Phase 4 with fixes. Its sources judgement was "suspicious provenance": the
decoder did not look transliterated, but the recorded source was false.

1. **F1: the record, corrected.** The Phase 4 entry above says the bitstream description came from
   `src:siramy-dcc` ("Paul Siramy's DCC write-up") and that a web search "only located the project
   page". Both are wrong. The PDF ("Extracting Diablo II Animations") is a user tutorial with no
   bitstream description and no code. It credits "Bilian Belchev, Doc on DCC format". The URL I
   registered (`allegro.cc/depot/DiabloIIAnimationExtractor`) is a source-code download page, not
   the PDF, which lives under `paul.siramy.free.fr/_divers2/`. The bitstream description in
   `dcc.md` was **recalled from an unidentified source**. `siramy-dcc` is now re-scoped to the
   tutorial, and `dcc.md` no longer cites it as a lead. I searched for Belchev's document (three
   web searches and two fetches) and **did not find it**. The only pointer, a d2mods file-database
   link, returned no usable page, and one search summary said it came with "a sample decoder". It is
   registered as `belchev-dcc`: not found, not read, and to be checked for code before any reading.
   `dcc.md` says the field names are "recalled community terminology, source unidentified".
2. **F2: zero-bit rules.** With no located document, each has **no legitimate lead**: the
   equal-cell copy and clear, the scan order within a cell, the canvas orientation, and the
   key-bit-to-palette mapping and its order. All four stay `[L]`. Under ADR-0007 (merged with
   `main`) they read "no lead; derived from data". `siramy-dcc` is marked "not a lead": this lane never
   fetched it.
3. **F3: mutations.** New `dcc.py mutations` subcommand. I wrote it myself, after reading the
   reviewer's method. It decodes every direction with each deliberately wrong rule and counts the
   directions whose bit accounting fails. Full corpus (119 448 directions): base 0 failing; `slot_from_start` 78 456, `mask_bits_reversed` 109 813, `fill_rule_v2v3` 116 049, `nbit_rule_v2v3` 114 400, `no_absorb_split` 106 170, `offset_y_top` 100 743, `no_early_stop` 119 437; `equal_clear_always`, `scan_column_major` and `key_descending` 0 each (about 15 min on a loaded machine).
   The stage 1 slot order and the mask-bit-to-slot mapping are promoted to `[C]`: stage 2 takes
   its bit cost from slot comparisons, so they set bit counts. The key row is split (width and
   the in-range check `[C]`, mapping and order `[L]`). The within-cell scan order is tagged `[L]`.
   The key-size line now shows the exact range 1..205 (the earlier "1..224" was a rounded bucket bound, not a maximum), which `survey` prints.
4. **F5: gate.** Merged `main` (a `docs/plans/README.md` conflict: main's rows kept for
   0005 and 0007, this branch's for 0006; resolution recorded by `rerere`). `dc6` and `dcc` are
   registered in `SURVEYS` with baselines. `dcc` is `opt_in`: it takes about 2.5 min and is already
   parallel, so `--jobs` cannot bring it under 60 s. After a second merge of `main` (ADR-0007), `gate.py --full` is GREEN: ds1, dt1, d2s, excel and
   dc6 ok, with dcc opt-in. `gate.py --full=dcc`: GREEN (dcc ok, 106 s)..
- **2026-10-11 — Phases 3 and 4 reviewed (architect).** Phase 3 (DC6) accepted with fixes 1–5, applied
  in `9815ef8`. Phase 4 (DCC) accepted with fixes: F1–F3 and F5 applied (`a2c807a`, `9d263d6`, log
  `10a1eb6`), F4 is this entry. Sources judgement: the DCC bitstream description was recalled from an
  unidentified source and no fetched lead exists (Belchev's document not found). Under ADR-0007 that is
  "no lead"; the review found nothing transliterated, every bit-cost rule is pinned by `dcc.py
  mutations` over all 119 448 directions (each wrong variant fails 78 456–119 437 of them), and the four
  zero-cost rules (equal-cell copy, scan order, orientation, key mapping) stay `[L]` with "no lead".
  dc6 and dcc are registered in the gate's full tier (dcc opt-in, 106 s).

### 2026-10-11 — Phase 5 (archivist)

- **Produced:** `tools/cof.py` (`survey`, `dump`, `compose`), `docs/formats/cof.md`, a row in
  `docs/formats/README.md`, `cof` registered in the gate's `SURVEYS` with
  `tools/gate/baselines/cof.txt`. Composed frames are under `workspace/render/units/sk/a1_{0,2,4,6}.png`
  and `workspace/render/units/ai/nu_{0,2,4,6}.png`. `compose` is per-unit and is not a
  `render_all.py` step.
- **Sources:** none. No lead; derived from data (ADR-0007). Nothing fetched, nothing registered.
- **Survey:** `SURVEY cof files=3082 layers=7727 frames=161768 errors=0 leftover_bytes=9`, exit 0,
  under 1 s. Layout pinned by byte accounting: `size = 28 + 9·L + F + D·F·L` holds exactly in 3 079
  files, with L, F and D the first three header bytes. Each 9-byte layer record ends in a
  NUL-terminated 3-character weapon class (all 7 727), components are distinct per file, and every
  one of the 161 768 order groups is a permutation of its file's components. Header, layer records,
  frame bytes and order block are `[C]` as layout.
- **Done-when gap:** "no leftover bytes" holds in 3 079 of 3 082 files. The three identical
  `objects/f9/cof/f9{nu,on,op}hth.cof` have 3 extra zero bytes between the layer record and the final
  order byte. They are documented, counted (`leftover_bytes=9`) and pinned by the baseline. The
  survey exits 0 on them and non-zero only on errors.
- **`[L]` by design (data favours, does not rule out alternatives):** the component index follows the
  `excel/composit.txt` row order (6 809 of 7 727 layers find their DCC in that directory; the row's
  directory is the maximum or tied in 15 of 16 rows); the order block is direction-major (10 709
  frame-to-frame changes against 46 572 frame-major); the first component is drawn furthest back.
  Meanings of `byte3` (always 20), `byte4`, `bytes5_7`, the four box values, `rate`, the layer bytes
  `b1`..`b4` and the frame bytes (non-zero mostly in attack and cast modes) are unknown or `[L]`.
- **Part heuristic `[L]`:** `--part LAYER=PART`, else `lit`, else the first DCC in name order. Assassin
  run: `--part tr=hvy,lg=hvy,ra=hvy,la=hvy`; that gave `rh` = `axe`, `sh` = `bsh`, `lh` = `lit`.
- **By eye (sanity, not evidence)**, 3× contact sheets in the scratchpad, palette `units`:
  - Monster, skeleton `sk a1 1hs` frame 0, directions 0, 2, 4, 6: a whole skeleton with
    skull, ribcage, arms, legs, an axe and a round shield. The joints meet in all four directions,
    and the shield and axe swap in front of and behind the body as the direction turns. Looks right.
  - Player, assassin `ai nu 1hs` frame 0, directions 0, 2, 4, 6: a whole figure in dark armour with
    a red sash, a large bone shield and an axe on a long haft. Limbs, head and torso line up in all
    four directions, and the shield and axe occlude plausibly. Looks right. The part mix is a
    heuristic, so the outfit is not one the game would necessarily show.
- **Surprise:** in the merged tree only `ai` and `dz` have full layer directories. `am`, `ba`, `pa`
  and `so` have no COFs and only a few DCCs, and `ne` has COFs but only an `s3` layer directory. So a
  classic class cannot be composed from the merged tree.
- **Not done:** animation playback, timing (`animdata.d2`), colour shifts (`.pl2`, monster palette
  shifts), shadow and blend modes, and part selection from equipment or `monstats2.txt`. All are listed
  under *Open questions* in cof.md. No comparison against the game.
- **2026-10-11 — Phase 5 review fixes (archivist).** Correction to the *Surprise* bullet above: the
  classic-class art is not missing from the install. It is in the extracted `d2char`
  (`workspace/mpq/d2char/`: am 1 919 files, ba 2 645, ne 1 711, pa 2 003, so 1 727), which the merge
  leaves out by design (mpq.md "Not merged"). Its 524 COFs parse with the same layout (0 errors,
  0 leftover bytes, 0 bad order groups), now recorded in cof.md. The per-file direction-major split
  was added to cof.md. A backlog entry asks for d2char to be added to the merge.
- **2026-10-11 — Phase 5 reviewed (architect): accepted with fixes 1–2 (applied `4522d20`).** Survey and
  size formula independently reproduced: 3 079 files exact plus 3 documented `f9` exceptions;
  `leftover_bytes=9` accepted as documented, so Phase 5's *Done when* holds with those three exceptions.
  The three favoured readings stay `[L]` (`45dthth` favours frame-major). The `d2char.mpq` omission from
  the merged tree went to the archivist backlog. Gate `--full` GREEN. **Plan closed:** all five phases
  accepted with fixes; tools-only per ADR-0005, so no research-map row changes.

