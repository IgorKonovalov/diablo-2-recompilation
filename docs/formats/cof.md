# COF composite descriptors (`.cof`)

Owned by `archivist`. Tooling only (ADR-0005): no research-map row, no spec. A COF file describes one
animation of a composite unit (a player class, monster or object) in one mode and weapon class: which
layers (components) take part, how many directions and frames it has, one byte per frame, and for
every direction and frame the order of the layers. The pixels themselves are in the layer DCCs
([dcc.md](dcc.md)).

Parser: `tools/cof.py` (`survey`, `dump`, `compose`). **Sources: no lead; derived from data.** No
external document was fetched or read for this format, and nothing is registered in
[sources.md](../sources.md) (ADR-0007). The field names are ours. Layout rows are `[C]` when
`cof.py survey` reads all 3 512 files that way with every byte accounted for (evidence rules,
data-format claims). No field has a code anchor. Every statement about what a field *means* is `[L]`,
and composed images are not evidence.

## Files

- `[C]` **3 512** `.cof` files under `data/global/` in `workspace/merged/`, 1 688 271 bytes in total:
  `chars` 756 (`ai` 139, `am` 95, `ba` 150, `dz` 93, `ne` 94, `pa` 91, `so` 94), `monsters` 1 295,
  `objects` 1 461. They sit in `<unit dir>/cof/`. The seven `monsters/vm/cof/vm/*.cof` files sit one
  directory deeper.
- `[C]` Since plan 0009 Phase 1 (2026-10-11) the merged tree includes `d2char.mpq` ([mpq.md](mpq.md)).
  Its 524 COFs (the classic classes) add 430 files; the other 94 are the `chars/ne` COFs that
  `d2exp` re-ships, which come from `d2exp`. Surveyed alone, `cof.py survey workspace/mpq/d2char` gives
  `SURVEY cof files=524 layers=4342 frames=99360 errors=0 leftover_bytes=0`, with no bad order group.
- `[C]` **Scope of the per-field statistics below.** Unless a line says otherwise, the value
  distributions in this document (file-name checks, header and layer-record counts, frame bytes,
  order-change counts) were tallied over the **3 082 files of the merged tree before `d2char` was
  added**, and the `d2char` COFs are counted separately where noted. The layout claims themselves hold
  for all 3 512 files (the survey line below).
- `[C]` Every file name is `<token><mode><wclass>.cof`: the unit directory's 2-character token,
  a 2-character mode token and a 3-character weapon-class code (for example `ska11hs` =
  `sk` + `a1` + `1hs`, `ainuhth` = `ai` + `nu` + `hth`). The mode token is in the `Token` or `Code`
  column of `excel/plrmode.txt`, `monmode.txt` or `objmode.txt` in 3 081 files (the other is
  `s0`). The weapon class is a `Code` of `excel/weaponclass.txt` in 3 065 files (the other 17 use
  `mgk` 9 and `fgt` 8).
- `[C]` `cof.py survey` over all of them:
  `SURVEY cof files=3512 layers=11295 frames=242312 errors=0 leftover_bytes=9` (exit 0). Before
  `d2char` was merged it read `files=3082 layers=7727 frames=161768`, same errors and leftover bytes. `frames`
  sums `directions × frames_per_dir`. The 9 leftover bytes are in three files (below).

## Layout

Little-endian. Offsets from the start of the file. With `L` layers, `F` frames per direction and
`D` directions:

```
file size = 28 + 9·L + F + D·F·L          (3 509 files exactly; 3 files have 3 more bytes)
```

```mermaid
flowchart LR
  H["header (28 B)"] --> R["layer records (9 B × L)"] --> FB["frame bytes (F B)"] --> O["layer order (D × F × L B)"]
```

- `[C]` This size equation holds for 3 509 of 3 512 files (3 079 of the earlier 3 082), and every piece is then checked by its
  content (below): each layer record's weapon-class field ends in NUL, and each order group is a
  permutation of the file's layer components. A 2-, 4- or 8-byte layer record, or a missing frame
  block, breaks the equation on the first sample files (`fablhth`: L = 4, F = 5, D = 8, 229 bytes;
  `faa2hth`: L = 4, F = 15, D = 8, 559 bytes).

### Header (28 bytes)

| offset | size | type | name | observed | tag |
|---|---|---|---|---|---|
| `0x00` | 1 | u8 | `layers` (L) | 1..11; 1 in 2 012 files, 2 in 410, 8 in 216, 9 in 128, 10 in 103 | `[C]` |
| `0x01` | 1 | u8 | `frames_per_dir` (F) | 1..(56 distinct values); 1 in 915 files, 8 in 298 | `[C]` |
| `0x02` | 1 | u8 | `directions` (D) | 1 (1 760 files), 8 (956), 16 (352), 4 (14) | `[C]` |
| `0x03` | 1 | u8 | `byte3` | 20 in all 3 082 files | layout `[C]`, meaning unknown |
| `0x04` | 1 | u8 | `byte4` | 0 (2 862), 1 (220) | layout `[C]`, meaning unknown |
| `0x05` | 3 | u8[3] | `bytes5_7` | 30 distinct triples: `f0 fd 7f` 1 014, `fc 12 00` 493, `9c 00 00` 429, `00 13 00` 368, … | layout `[C]`, meaning `[L]` (below) |
| `0x08` | 4 | s32 | `box0` | mostly negative (2 868), 0 in 147 | layout `[C]`, meaning `[L]` (below) |
| `0x0C` | 4 | s32 | `box1` | mostly positive (3 035) | layout `[C]`, meaning `[L]` |
| `0x10` | 4 | s32 | `box2` | mostly negative (3 008) | layout `[C]`, meaning `[L]` |
| `0x14` | 4 | s32 | `box3` | positive 2 760, 0 in 209, negative 113 | layout `[C]`, meaning `[L]` |
| `0x18` | 4 | s32 | `rate` | 256 in 2 364 files, 128 in 123; 39 distinct values | layout `[C]`, meaning `[L]` (below) |

- `[L]` `box0..box3` look like a bounding box (x min, x max, y min, y max) in the same pixel space as
  the DCC frame offsets: `box0 ≤ box1` in 3 019 files and `box2 ≤ box3` in 3 057, with signs that fit
  a sprite drawn above and around a ground point. Not checked against the DCC frame boxes. No lead;
  derived from data.
- `[L]` `rate` looks like an animation speed with 256 as the normal value. Playback is out of scope.
  No lead; derived from data.
- `[L]` `bytes5_7` vary with no visible relation to the rest of the file (`f0 fd 7f` looks like a
  memory address); the layout reads them as one unknown block. No lead; derived from data.

### Layer records (9 bytes × L, from `0x1C`)

| offset | size | type | name | observed | tag |
|---|---|---|---|---|---|
| `+0x00` | 1 | u8 | `component` | 0..15; distinct within each file (all 3 082). Counts: 1 in 3 080 files, 8 in 898, 9 in 589, 0 in 567 | `[C]` |
| `+0x01` | 1 | u8 | `b1` | 1 (7 450 layers), 0 (277) | layout `[C]`, meaning unknown |
| `+0x02` | 1 | u8 | `b2` | 1 (7 641), 0 (86) | layout `[C]`, meaning unknown |
| `+0x03` | 1 | u8 | `b3` | 0 (7 019), 1 (708) | layout `[C]`, meaning unknown |
| `+0x04` | 1 | u8 | `b4` | 5 (4 608), 0 (2 419), 3 (651), 6 (29), 1 (15), 2 (3), 4 (2) | layout `[C]`, meaning unknown |
| `+0x05` | 4 | char[4] | `wclass` | 3 characters + NUL (byte `+0x08` is 0 in all 7 727 records): `hth` 5 909, `1hs` 532, `2hs` 229, `2ht` 216, `stf` 202, `bow` 197, `xbw` 184, `1ht` 178, `ht2` 35, `ht1` 28, `mgk` 15, `att` 1, `eut` 1 | `[C]` |

- `[C]` A layer's `wclass` is not always the file's: it equals the weapon class in the file name in
  6 060 of 7 727 layers. Of the other 1 667, 1 393 are `hth` and 180 are `1hs`.
- `[L]` **`component` indexes the 16 rows of `excel/composit.txt`** (`HD`, `TR`, `LG`, `RA`, `LA`,
  `RH`, `LH`, `SH`, `S1`..`S8`, in that row order), and the row token names the layer's DCC
  directory (`<unit dir>/<token>/`). Evidence, data only: for 6 809 of 7 727 layers a DCC named
  `<unit token><layer token><3 chars><mode><layer wclass>.dcc` exists in that directory. Counting,
  for each component value, how many of its layers find such a DCC in each of the 16 directories,
  the directory named by the row is the strict maximum in 9 rows and tied for it in 6 (with `tr`,
  which exists for nearly every mode, and in row 13 also with `hd`, at 1 layer each). In row 12
  (`S5`) it is 11 against 13 for `s4`. So the data favours this mapping but does not rule out every
  alternative. The 918 misses are 777 player layers, nearly all `chars/ne` layers whose directory was
  absent from the merged tree before `d2char` was added, plus 124 monster and 17 object layers. No lead; derived from data.

### Frame bytes (F bytes)

| offset | size | type | name | observed | tag |
|---|---|---|---|---|---|
| `0x1C + 9L` | F | u8[F] | `frame_byte` | 0 (29 339), 1 (293), 2 (104), 3 (4) | layout `[C]`, meaning `[L]` |

- `[C]` 2 697 files have no non-zero frame byte, 376 have one, 8 have two and one file has nine.
  Non-zero bytes occur mostly in attack, cast, skill and kick modes (`a1`, `a2`, `sc`, `s1`..`s4`,
  `kk`, `th`), usually in the middle of the animation (for example frame 10 of 16 in `ska11hs`).
- `[L]` A non-zero byte marks a frame where something happens (an attack connects, a missile
  leaves), with the value naming the kind of event. Data only, no code anchor. No lead; derived from
  data.

### Layer order (D × F × L bytes, the last bytes of the file)

| offset | size | type | name | meaning | tag |
|---|---|---|---|---|---|
| `size − D·F·L` | D·F·L | u8[D·F][L] | `order` | D·F groups of L bytes; each group is a permutation of the file's `component` values | `[C]` |

- `[C]` Every one of the 161 768 groups is a permutation of the layer components of its file. The
  parser rejects a file otherwise, and none is rejected.
- `[L]` **Group index = direction × F + frame (direction-major).** Read that way, a group differs
  from the previous frame's group of the same direction 10 709 times over the corpus. Read
  frame-major (frame × D + direction), it differs 46 572 times. Layer order changes rarely from one
  frame to the next, so the data strongly favours direction-major, but it does not rule out the
  other reading. Per file: 589 files favour direction-major, 1 favours frame-major
  (`monsters/45/cof/45dthth.cof`, 9 changes against 8), 1 is a non-trivial tie
  (`monsters/pw/cof/pwdthth.cof`, 6 and 6), and the rest tie: the 1 760 files with D = 1 by
  construction, and 731 whose order never changes. The 524 `d2char` COFs give 11 231 against 55 351,
  and 514 files against 0. Because one file goes the other way, the reading stays `[L]`. No lead;
  derived from data.
- `[L]` **The first component in a group is drawn first (furthest back).** Composed frames look
  right with this reading (see *Composition*). No lead; derived from data.

### Three files with 3 extra bytes

- `[C]` `objects/f9/cof/f9nuhth.cof`, `f9onhth.cof` and `f9ophth.cof` are byte-identical in
  content, 42 bytes long, with L = F = D = 1 (39 bytes expected). Their one layer has component 1
  (`TR`, and `objects/f9/tr/` holds the matching DCCs). The bytes after the layer record are
  `00 00 00 00 01`: the last byte is the order group (the component 1), and the parser takes the
  frame byte right after the layer record. That leaves 3 zero bytes no field accounts for. These are
  the survey's `leftover_bytes=9`. Whether they belong to the frame block or are padding cannot be
  told from the data, since all four bytes are zero.

## Composition (renderer heuristic, not game behaviour)

`cof.py compose <root> <unit dir> <mode> <wclass> [out] [--dirs …] [--frame N] [--part LAYER=PART,…]`
draws one frame of one direction:

1. Read `<unit dir>/cof/<token><mode><wclass>.cof`.
2. Take the order group `direction × F + frame`.
3. For each component in the group, map it to a directory through the `composit.txt` row order. Pick
   the DCC `<token><layer><part><mode><layer wclass>.dcc`, where `<part>` is the `--part` choice for
   that layer, else `lit`, else the first in name order. Decode the same direction (scaled if the DCC
   has a different direction count) and the same frame index (clamped).
4. Paste each layer's frame at its `xmin`/`ymin` box from [dcc.md](dcc.md), in group order, with
   index 0 transparent. Use palette `units`.
5. Write `<out>/units/<token>/<mode>_<dir>.png`, cropped to the union of the layer boxes.

- `[L]` Every choice above is a heuristic: the component-to-directory mapping, the direction-major
  group index, back-to-front drawing, the part choice (which in the game depends on the unit's
  equipment or on `monstats2.txt`, and is not modelled), direction scaling, flat palette lookup and
  no shadow or blend modes. `b1`..`b4` are ignored. No lead; derived from data.

## Tools

- `python3 -I tools/cof.py survey workspace/merged`: parses every file, checks the size equation,
  the NUL-terminated weapon classes, distinct components and every order group, prints the
  histograms above, the direction-major/frame-major change counts and the `SURVEY` line. It exits 0
  iff there are no errors. Leftover bytes are printed as `NOTE` lines and pinned by the gate
  baseline. It takes under a second.
- `python3 -I tools/cof.py dump <file.cof>`: header, layer records, frame bytes and the order groups
  per direction (hex component per layer).
- `python3 -I tools/cof.py compose …`: the heuristic composition above.

## Open questions

- `[L]` What `byte3` (always 20), `byte4`, `bytes5_7`, the four `box` values, `rate`, the layer bytes
  `b1`..`b4` and the frame-byte values mean. Only code can say.
- `[L]` Whether the order block is direction-major (the data favours it) and whether the first
  component is drawn first. Both need code.
- `[L]` How the game maps `component` to a layer directory and picks the DCC part (`lit`, `hvy`, a
  weapon code…) for players (equipment) and monsters (`monstats2.txt` columns `HD`..`S8` and
  `HDv`..`S8v`).
- `[L]` What the 3 extra bytes in the three `objects/f9` files are, and whether the game reads them.
- **Not done (plan 0006 scope):** animation playback, timing (`animdata.d2`), colour shifts (`.pl2`
  tables and monster palette shifts), shadows and blend modes.
