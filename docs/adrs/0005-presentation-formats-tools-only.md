# ADR-0005 — Presentation formats: tile and sprite decoding, tools-only, output stays in `workspace/`

> **Status:** accepted
> **Date:** 2026-10-11
> **Related plan(s):** 0006-asset-rendering; amends ADR-0002 in part (presentation formats only)

## Context

ADR-0002 put presentation formats (DC6/DCC/COF, palettes, fonts, sound, video) out of scope
because seed-for-seed generation doesn't need them. It also said a later ADR could bring them in.
The owner now wants to extract the image assets and tiles from their copy of the game. There's a
practical reason on our side as well: rendering DS1 presets and generated levels as pictures
would make DRLG work much easier to check by eye.

The marginal cost is low. `tools/dt1.py` already walks every DT1 pixel block: the fixed 256-byte
isometric diamonds and both run-length formats, 361 484 blocks with every byte accounted for
([formats/dt1.md](../formats/dt1.md)). All the palettes are in `workspace/merged/data/global/palette/`
(`pal.dat` and `pal.pl2` for each act and menu). The merged tree also holds 1 676 DC6, 12 233 DCC and
3 082 COF files. Pillow isn't installed, but PNG can be written with `zlib` from the standard
library.

There are two risks. One is drift: the archivist is the only lane on plan 0005, and D2S (Phase 4)
gates every `[C]` promotion for items. The other is that rendered images are game data, the same
as the files they come from.

## Decision

We decode **DT1 tile graphics, palettes, DC6 and DCC** into images, and **COF** as far as
composing a unit's layers needs. This is **tools-only** work in the archivist lane. Each format
gets a doc under `docs/formats/`, and the decoders live in `tools/`, use only the standard library
and run with `python3 -I`. Format docs follow the usual file-only rule: a layout row is `[C]` when
the decoder reads every file of that type and accounts for every byte. A rendered image that
looks right is a sanity check recorded in the implementation log. **It is not evidence**, and it
doesn't promote any tag. **Every rendered output goes under `workspace/render/`** and never enters
git. Docs may describe images but don't embed them. Presentation formats get **no research-map
row and no spec**: they are tooling, not part of the deliverable. A DS1 or level preview built from
these tools illustrates the data and proves nothing about DRLG behaviour. Fonts, sound and video
stay out of scope. Within the archivist lane, this work yields to anything a core or enabler plan
is waiting on (today, plan 0005 Phase 4).

## Consequences

### Positive
- The owner gets the tiles and sprites as viewable images from their own copy.
- DRLG plans get a visual check: a preset or a generated level can be looked at, not just diffed.
- DT1 pixel decoding is already done, so the first useful output costs little.

### Negative
- **Archivist time.** DCC is a real format: variable-width bit fields, several streams, frame and
  direction caches. Writing and checking a decoder for 12 233 files takes days of a lane that
  plan 0005 also needs. Making this work yield to plan 0005 contains the cost but doesn't remove it.
- **No code anchors.** Palette indices, transparency (index 0), shadow and blend modes, and
  monster colour shifts (`.pl2`) are known only from files and community docs. Renders may be
  subtly wrong in ways a format doc can't tag `[C]`, and we accept that for tooling.
- **Pull towards out-of-scope systems.** Correct animation needs `animdata.d2` (timing, deferred by
  ADR-0002) and COF layer order. Plan 0006 stops at decoding frames and composing a single frame.
  Animation playback stays out of scope.
- Rendered output grows large (tens of thousands of PNGs). It is regenerable, so
  `workspace/render/` may be deleted at any time.

### Neutral
- ADR-0002's deferral of game simulation (combat, skills, AI, timing) and of fonts, sound and
  video is unchanged. The evidence rules and sources policy are unchanged. Community format docs are
  leads under `docs/sources.md` as usual.
- Hooks already keep `workspace/` out of git, so no new guard is needed.

## Alternatives considered

### Keep presentation formats out of scope
Rejected because the owner asked for it, the DT1 half is nearly free, and level previews pay
back directly in DRLG review.

### Full scope: give presentation formats research-map rows and specs, with code anchors
Rejected because nothing in seed-deterministic generation reads pixels. Reverser time spent on
renderer code would come straight out of items, monsters and DRLG.

### Use Pillow or an external extractor
Rejected because a third-party extractor is an untrusted binary or foreign code, against the
spirit of ADR-0001. Writing PNG with `zlib` is a few dozen lines, while Pillow adds a dependency
for no gain.
