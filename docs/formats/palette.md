# Palettes (`pal.dat`, `pal.pl2`)

Owned by `archivist`. Tooling only (ADR-0005): no research-map row, no spec. A palette maps the
8-bit colour indices of DT1, DC6 and DCC pixels to colours. Parser: `tools/palette.py`
(`survey`, `swatch`). PNG output: `tools/png.py` (indexed PNG, stdlib `zlib` + `struct`).

No field here has a code anchor. A layout row is `[C]` when `palette.py survey` reads every file of
the type and the values make sense (evidence rules, data-format claims). Rendered images are not
evidence.

## Files

- `[C]` **18** directories under `data/global/palette/` in `workspace/merged/`, each with a
  `pal.dat`: `act1`–`act5`, `endgame`, `endgame2`, `fechar`, `loading`, `menu0`–`menu4`, `sky`,
  `static`, `trademark`, `units`.
- `[C]` 16 of them also have a `pal.pl2`; `static` and `units` do not. 15 `pal.pl2` are 443 175
  bytes, `loading/pal.pl2` is 442 916.
- `[C]` All 18 `pal.dat` files differ from one another (distinct sha256).

## `pal.dat` layout

| offset | size | type | name | meaning | tag |
|---|---|---|---|---|---|
| `0x000` | 768 | u8[256][3] | `entries` | 256 colours, 3 bytes each, stored **B, G, R** | size `[C]`, component order `[L]` |

- `[C]` Every `pal.dat` is exactly 768 bytes = 256 × 3, with no header.
- `[C]` In all 18, entry 0 is (0, 0, 0) and entry 255 is (255, 255, 255).
- `[C]` In each of the 16 directories that have both files, the first 1 024 bytes of `pal.pl2` are the
  same 256 colours as 4-byte entries with the three colour bytes in the **reverse** order of
  `pal.dat`, and the fourth byte 0 in every entry (`palette.py survey`, 16/16).
- `[L]` The order is B, G, R in `pal.dat` (so R, G, B, 0 in `pal.pl2`). Basis: the reversal above,
  plus a run of 3-byte triples near the end of every 443 175-byte `pal.pl2` that read as recognisable
  colours only in R, G, B order (`ff ff ff`, `ff 4d 4d`, `00 ff 00`, `69 69 ff`, `c7 b3 77`, …), and
  renders that look right in this order. None of these is a code anchor, and the renders are not
  evidence; it stays `[L]` until the code that loads `pal.dat` is anchored (not planned).
- `[L]` Index 0 is drawn as transparent. The renderers write it with alpha 0 (PNG `tRNS`).

## `pal.pl2` layout (as far as the file shows)

| offset | size | name | meaning | tag |
|---|---|---|---|---|
| `0x0000` | 1 024 | `palette` | the `pal.dat` colours as (R, G, B, 0), see above | `[C]` |
| `0x0400` | rest | — | not decoded | — |

- The remaining 442 151 bytes (441 892 in `loading`) are mostly 256-byte index-to-index tables
  (light levels, blends, colour shifts) by reputation. That is not decoded here; the renderers use a
  flat palette lookup and model no shading or blending (plan 0006, *Open questions*). The size
  difference of `loading/pal.pl2` (259 bytes) is unexplained.

## Which palette an asset uses (renderer heuristic)

How the game picks a palette is code behaviour and stays `[L]`. The renderers use a documented
heuristic, `palette.palette_for_tiles()`, for DT1 and DS1 paths under `data/global/tiles/`:

| top directory | palette |
|---|---|
| `act1`, `act2`, `act3`, `act4` | same name |
| `expansion` | `act5` |
| `guild`, `arena`, anything else | `act1` |

## Tools

- `python3 -I tools/palette.py survey workspace/merged`: checks size, entries 0 and 255, and the
  `pal.pl2` prefix for every palette. Exit 0: 18 palettes, 0 failures.
- `python3 -I tools/palette.py swatch workspace/merged workspace/render/palette`: one 256×256 PNG
  per palette (16×16 swatches, index order row-major).
