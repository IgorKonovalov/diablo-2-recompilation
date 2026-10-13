# MonStats2 (`data/global/excel/MonStats2.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 609 (610 data rows less one `Expansion` marker)   **Record:** 308 B (`0x134`)
> **sha256:** `.txt` `028483a664eec434d6d54fd933d3245d16ce7ee5271ff9fd1f4612da0e05cf7d`, `.bin` `9d605ca4a2039ce99d899a884fb6a44b4d6ad39d0286299bf5221472e8875d84`
> **Doc status:** columns listed, `.bin` layout complete, semantics partial (the columns the monster pool reads)

## Purpose

One row per monster *appearance* class: the graphics side of a monster (size, hit box, the composite
components and their variants, which animation modes exist, light, palette shift). A `MonStats` record
points at its row through `MonStatsEx` (`+0x018`, [MonStats](MonStats.md)). Plan 0012 needs it because the
level monster pool rolls each entry's appearance sets from this table's component counts, with draws on the
pool's seed between one level's pool and the next ([monsters/0001 § 4](../findings/monsters/0001-level-pool.md),
`monsters/pool`). Everything else here is graphics and client data; no other finding reads it yet.

## Row identity

- `[C]` Rows are addressed by position: the `.bin` record count (609) is the `.txt` data rows less the one
  `Expansion` marker row, and the first field (`+0x000`, u16) holds each record's own index, i.e. the `Id`
  column compiled as an index into this table. (tbl:MonStats2.txt:Id)
- `[C]` The loader reads `monstats2.bin` with 308-byte records
  ([data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), call site
  `0x00658422`).
- `[I]` A MonStats class reaches its record through MonStats `+0x018` (`sub_00451FE0_MonStats2Rec`).
  (fn:sub_00451FE0_MonStats2Rec@0x00451FE0)

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> monstats2` decodes
every record and compares it with every mapped cell: **609 records × 142 mapped fields = 86 478 cells, 0
mismatches** (layout `monstats2` in `tools/excel_layouts.py`). A field is `[C]` when a probe over every record
finds only that offset for the column; `[I]` when the column is constant or equal to a sibling, so its slot comes
from the stride of its group; "width `[I]`" when the bytes after a field are zero in every record, so a wider
integer would also fit. **Meaning:** names only, `[L]`, except the rows of § [What the monster pool reads](#what-the-monster-pool-reads).

Three special encodings (`tools/excel_bin.py` field types `tokcount`, `toklist`, `toksum`):

- `[C]` **Component lists.** Each of the sixteen `HDv` … `S8v` cells is a quoted comma list of component codes
  (`"lit,lit,lit,med,hvy,hvy,hvy"`). It compiles twice: its **count** of non-empty codes as a u8 at
  `+0x015 + k`, and the codes themselves as **twelve u8 row indices of [compcode](compcode.md)** (`nil` 0, `lit` 1,
  `med` 2, `hev` 3, `hvy` 4, …) at `+0x026 + 12·k`, `0xFF` past the last one. *k* is the column's position in
  `HDv, TRv, LGv, Rav, Lav, RHv, LHv, SHv, S1v … S8v`. A blank cell gives count 0 and twelve `0xFF`. A trailing
  empty code is dropped: `act2male` `S1v` = `"lit,nil,nil,fez,nil,nil,rol,nil,nil,"` stores 9. The longest lists
  (`S1v`, `S2v`) fill all 12 slots. (tbl:MonStats2.txt:HDv)
- `[C]` **`+0x025` is computed**, not a column: `Σ over the sixteen lists of max(count − 1, 0)`. It holds for all
  609 records (values 0 ×461, up to 49). (tbl:MonStats2.txt:HDv)
  `[I]` The compiler writes it in the list-column callback `sub_00657010_MonStats2CompList` while it handles
  the last list (`S8v`), capped at 254 (no stock value reaches the cap). ([data/0004](../findings/data/0004-cell-converters.md),
  fn:sub_00657010_MonStats2CompList@0x00657010)
- `[C]` **Bit groups indexed by position.** `HD` … `S8` are bits 0..15 of the u16 at `+0x0E8` in list order;
  `mDT` … `mRN` are bits 0..15 of `+0x0F0` and `dDT` … `dRN` the u8s `+0x0F4` … `+0x103`, both in
  `MonMode.txt` row order (`DT NU WL GH A1 A2 BL SC S1 S2 S3 S4 DD KB SQ RN`); the seven `*mv` columns
  are the bits of the same mode index at `+0x104` (`A1mv` bit 4, `A2mv` 5, `SCmv` 7, `S1mv` 8 …). Columns that
  are constant (`TR`, `A1mv`, `SCmv`, `S3mv`, `S4mv`) take the slot of that order `[I]`.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Id` | str, 609 distinct, len ≤ 17 | `+0x000` u16 index | self | [C] |
| `Height` | int 0..4 (5 distinct) | `+0x00B` u8 | — | [C] |
| `OverlayHeight` | int 0..4 (5 distinct) | `+0x00C` u8 | — | [C] |
| `pixHeight` | int 32..144 (11 distinct) | `+0x00D` u8 | — | [C] |
| `SizeX` | int 0..3 (4 distinct) | `+0x008` u8 | — | [I] |
| `SizeY` | int 0..3 (4 distinct) | `+0x009` u8 | — | [I] |
| `spawnCol` | int 1..3 (3 distinct), 589 blank | `+0x00A` u8 | — | [C] |
| `MeleeRng` | int 0..6 (6 distinct) | `+0x00E` u8 | — | [C] (width [I]) |
| `BaseW` | str, 8 distinct, len ≤ 3 | `+0x010` char[4] | — | [C] |
| `HitClass` | int 1..12 (3 distinct) | `+0x014` u8 | — | [C] |
| `HDv` | list of 1..7 codes (19 distinct), 465 blank | `+0x015` u8 count; `+0x025` u8 Σ(count − 1), all 16; `+0x026` u8[12] `compcode` rows | `compcode:code` | [C] |
| `TRv` | list of 1..7 codes (7 distinct), 13 blank | `+0x016` u8 count; `+0x032` u8[12] `compcode` rows | `compcode:code` | [C] |
| `LGv` | list of 1..4 codes (8 distinct), 516 blank | `+0x017` u8 count; `+0x03E` u8[12] `compcode` rows | `compcode:code` | [C] |
| `Rav` | list of 1..4 codes (11 distinct), 479 blank | `+0x018` u8 count; `+0x04A` u8[12] `compcode` rows | `compcode:code` | [C] |
| `Lav` | list of 1..4 codes (11 distinct), 484 blank | `+0x019` u8 count; `+0x056` u8[12] `compcode` rows | `compcode:code` | [C] |
| `RHv` | list of 1..11 codes (20 distinct), 523 blank | `+0x01A` u8 count; `+0x062` u8[12] `compcode` rows | `compcode:code` | [C] |
| `LHv` | list of 1..4 codes (16 distinct), 560 blank | `+0x01B` u8 count; `+0x06E` u8[12] `compcode` rows | `compcode:code` | [C] |
| `SHv` | list of 1..5 codes (5 distinct), 574 blank | `+0x01C` u8 count; `+0x07A` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S1v` | list of 1..12 codes (17 distinct), 360 blank | `+0x01D` u8 count; `+0x086` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S2v` | list of 1..12 codes (12 distinct), 467 blank | `+0x01E` u8 count; `+0x092` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S3v` | list of 1..4 codes (5 distinct), 539 blank | `+0x01F` u8 count; `+0x09E` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S4v` | list of 1..4 codes (8 distinct), 562 blank | `+0x020` u8 count; `+0x0AA` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S5v` | list of 1..4 codes (7 distinct), 577 blank | `+0x021` u8 count; `+0x0B6` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S6v` | list of 1..1 codes (1 distinct), 605 blank | `+0x022` u8 count; `+0x0C2` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S7v` | list of 1..1 codes (1 distinct), 597 blank | `+0x023` u8 count; `+0x0CE` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S8v` | list of 1..1 codes (1 distinct), 592 blank | `+0x024` u8 count; `+0x0DA` u8[12] `compcode` rows | `compcode:code` | [C] |
| `HD` | int, always 1, 463 blank | `+0x0E8` bit 0 | — | [C] |
| `TR` | int, always 1 | `+0x0E8` bit 1 | — | [I] |
| `LG` | int, always 1, 513 blank | `+0x0E8` bit 2 | — | [C] |
| `RA` | int, always 1, 477 blank | `+0x0E8` bit 3 | — | [C] |
| `LA` | int, always 1, 482 blank | `+0x0E8` bit 4 | — | [C] |
| `RH` | int, always 1, 509 blank | `+0x0E8` bit 5 | — | [C] |
| `LH` | int, always 1, 559 blank | `+0x0E8` bit 6 | — | [C] |
| `SH` | int, always 1, 574 blank | `+0x0E8` bit 7 | — | [C] |
| `S1` | int, always 1, 337 blank | `+0x0E9` bit 0 | — | [C] |
| `S2` | int, always 1, 463 blank | `+0x0E9` bit 1 | — | [C] |
| `S3` | int, always 1, 535 blank | `+0x0E9` bit 2 | — | [C] |
| `S4` | int, always 1, 562 blank | `+0x0E9` bit 3 | — | [C] |
| `S5` | int, always 1, 577 blank | `+0x0E9` bit 4 | — | [C] |
| `S6` | int, always 1, 605 blank | `+0x0E9` bit 5 | — | [I] |
| `S7` | int, always 1, 597 blank | `+0x0E9` bit 6 | — | [I] |
| `S8` | int, always 1, 578 blank | `+0x0E9` bit 7 | — | [C] |
| `TotalPieces` | int 1..11 (11 distinct) | `+0x0EC` u32 | — | [C] (width [I]) |
| `mDT` | int, always 1, 90 blank | `+0x0F0` bit 0 | — | [C] |
| `mNU` | int, always 1, 24 blank | `+0x0F0` bit 1 | — | [C] |
| `mWL` | int, always 1, 133 blank | `+0x0F0` bit 2 | — | [C] |
| `mGH` | int, always 1, 206 blank | `+0x0F0` bit 3 | — | [C] |
| `mA1` | int, always 1, 159 blank | `+0x0F0` bit 4 | — | [C] |
| `mA2` | int, always 1, 392 blank | `+0x0F0` bit 5 | — | [C] |
| `mBL` | int, always 1, 558 blank | `+0x0F0` bit 6 | — | [C] |
| `mSC` | int, always 1, 568 blank | `+0x0F0` bit 7 | — | [C] |
| `mS1` | int, always 1, 371 blank | `+0x0F1` bit 0 | — | [C] |
| `mS2` | int, always 1, 549 blank | `+0x0F1` bit 1 | — | [C] |
| `mS3` | int, always 1, 584 blank | `+0x0F1` bit 2 | — | [C] |
| `mS4` | int, always 1, 594 blank | `+0x0F1` bit 3 | — | [C] |
| `mDD` | int, always 1, 85 blank | `+0x0F1` bit 4 | — | [C] |
| `mKB` | int, always 1, 232 blank | `+0x0F1` bit 5 | — | [C] |
| `mSQ` | int, always 1, 225 blank | `+0x0F1` bit 6 | — | [C] |
| `mRN` | int, always 1, 552 blank | `+0x0F1` bit 7 | — | [C] |
| `dDT` | int 1..16 (4 distinct) | `+0x0F4` u8 | — | [C] |
| `dNU` | int 1..16 (4 distinct) | `+0x0F5` u8 | — | [C] |
| `dWL` | int 1..16 (4 distinct) | `+0x0F6` u8 | — | [C] |
| `dGH` | int 1..8 (3 distinct) | `+0x0F7` u8 | — | [C] |
| `dA1` | int 1..16 (4 distinct) | `+0x0F8` u8 | — | [C] |
| `dA2` | int 1..8 (3 distinct) | `+0x0F9` u8 | — | [I] |
| `dBL` | int 1..8 (3 distinct) | `+0x0FA` u8 | — | [I] |
| `dSC` | int 1..8 (3 distinct) | `+0x0FB` u8 | — | [I] |
| `dS1` | int 1..16 (4 distinct) | `+0x0FC` u8 | — | [C] |
| `dS2` | int 1..16 (4 distinct) | `+0x0FD` u8 | — | [C] |
| `dS3` | int 1..8 (3 distinct) | `+0x0FE` u8 | — | [I] |
| `dS4` | int 1..8 (3 distinct) | `+0x0FF` u8 | — | [I] |
| `dDD` | int 1..16 (4 distinct) | `+0x100` u8 | — | [C] |
| `dKB` | int 1..8 (3 distinct) | `+0x101` u8 | — | [I] |
| `dSQ` | int 1..8 (3 distinct) | `+0x102` u8 | — | [I] |
| `dRN` | int 1..16 (4 distinct) | `+0x103` u8 | — | [C] |
| `A1mv` | always blank | `+0x104` bit 4 | — | [I] |
| `A2mv` | int, always 1, 591 blank | `+0x104` bit 5 | — | [C] |
| `SCmv` | always blank | `+0x104` bit 7 | — | [I] |
| `S1mv` | int, always 1, 598 blank | `+0x105` bit 0 | — | [C] |
| `S2mv` | int, always 1, 605 blank | `+0x105` bit 1 | — | [C] |
| `S3mv` | always blank | `+0x105` bit 2 | — | [I] |
| `S4mv` | always blank | `+0x105` bit 3 | — | [I] |
| `noGfxHitTest` | int, always 1, 598 blank | `+0x004` bit 0 | — | [I] |
| `htTop` | int -150..-60 (4 distinct), 598 blank | `+0x10E` s16 | — | [C] (width [I]) |
| `htLeft` | int -80..-20 (5 distinct), 598 blank | `+0x110` s16 | — | [C] (width [I]) |
| `htWidth` | int 40..145 (5 distinct), 598 blank | `+0x112` s16 | — | [C] (width [I]) |
| `htHeight` | int 70..160 (4 distinct), 598 blank | `+0x114` s16 | — | [C] (width [I]) |
| `restore` | int 0..2 (3 distinct) | `+0x130` u32 | — | [C] (width [I]) |
| `automapCel` | int, always 1258, 608 blank | `+0x118` u32 | — | [C] (width [I]) |
| `noMap` | int, always 1, 592 blank | `+0x004` bit 1 | — | [C] |
| `noOvly` | int, always 1, 587 blank | `+0x004` bit 2 | — | [C] |
| `isSel` | int, always 1, 79 blank | `+0x004` bit 3 | — | [C] |
| `alSel` | int, always 1, 592 blank | `+0x004` bit 4 | — | [C] |
| `noSel` | int, always 1, 580 blank | `+0x004` bit 5 | — | [C] |
| `shiftSel` | int, always 1, 604 blank | `+0x004` bit 6 | — | [C] |
| `corpseSel` | int, always 1, 215 blank | `+0x004` bit 7 | — | [C] |
| `isAtt` | int, always 1, 122 blank | `+0x005` bit 1 | — | [C] |
| `revive` | int, always 1, 220 blank | `+0x005` bit 0 | — | [C] |
| `critter` | int, always 1, 599 blank | `+0x005` bit 5 | — | [C] |
| `small` | int, always 1, 534 blank | `+0x005` bit 2 | — | [C] |
| `large` | int, always 1, 435 blank | `+0x005` bit 3 | — | [C] |
| `soft` | int, always 1, 206 blank | `+0x005` bit 4 | — | [C] |
| `inert` | int, always 1, 524 blank | `+0x006` bit 1 | — | [C] |
| `objCol` | int, always 1, 606 blank | `+0x006` bit 2 | — | [C] |
| `deadCol` | int, always 1, 596 blank | `+0x006` bit 3 | — | [C] |
| `unflatDead` | int, always 1, 600 blank | `+0x006` bit 4 | — | [C] |
| `Shadow` | int, always 1, 21 blank | `+0x005` bit 6 | — | [C] |
| `noUniqueShift` | int, always 1, 503 blank | `+0x005` bit 7 | — | [C] |
| `compositeDeath` | int, always 1, 467 blank | `+0x006` bit 0 | — | [C] |
| `localBlood` | int 1..2 (2 distinct), 458 blank | `+0x11C` u8 | — | [C] |
| `Bleed` | int 1..2 (2 distinct), 290 blank | `+0x11D` u8 | — | [C] |
| `Light` | int 3..15 (9 distinct), 509 blank | `+0x11E` u8 | — | [C] |
| `light-r` | int 0..255 (9 distinct) | `+0x11F` u8 | — | [C] |
| `light-g` | int 0..255 (10 distinct) | `+0x120` u8 | — | [C] |
| `light-b` | int 0..255 (7 distinct) | `+0x121` u8 | — | [C] |
| `Utrans` | int 2..255 (3 distinct), 594 blank | `+0x122` u8 | — | [C] |
| `Utrans(N)` | int 3..255 (3 distinct), 594 blank | `+0x123` u8 | — | [C] |
| `Utrans(H)` | int 4..255 (3 distinct), 594 blank | `+0x124` u8 | — | [C] (width [I]) |
| `Heart` | str, always 'xxx' | `+0x128` char[4] | — | [I] |
| `BodyPart` | str, always 'xxx' | `+0x12C` char[4] | — | [I] |
| `InfernoLen` | int 1..14 (4 distinct) | `+0x108` u8 | — | [C] |
| `InfernoAnim` | int 6..11 (4 distinct), 584 blank | `+0x109` u8 | — | [C] |
| `InfernoRollback` | int 6..15 (4 distinct), 591 blank | `+0x10A` u8 | — | [C] |
| `ResurrectMode` | str, 3 distinct, len ≤ 2 | `+0x10B` u8 index | monmode:code | [C] |
| `ResurrectSkill` | str, always 'SkeletonRaise', 578 blank | `+0x10C` s16 index | skills:skill | [C] (width [I]) |
| `EOL` | int, always 0 | — (not compiled) | — | — |

### Fields with no `.txt` column

| offset | size | observed | tag |
|---|---|---|---|
| `+0x002` | 2 | 0 in every record | unknown (high half of a u32 `Id`, or padding) |
| `+0x007` | 1 | 0 | unknown; `+0x004`..`+0x006` bits 21..23 are also 0 in every record |
| `+0x00F` | 1 | 0 | unknown (padding before `BaseW`, or the high byte of `MeleeRng`) |
| `+0x025` | 1 | Σ(count − 1) of the component lists | `[C]` computed (above) |
| `+0x0E6` | 2 | 0 | unknown (after the last token slot) |
| `+0x0EA` | 2 | 0 | unknown (the high half of the component-flag u32) |
| `+0x0F2`, `+0x106`, `+0x116`, `+0x125` | 2, 2, 2, 3 | 0 | unknown (padding after a bit group or before an aligned field) |

## Record layout (308 bytes)

`+0x000` `Id` u16 · `+0x004` flags (`noGfxHitTest` … `unflatDead`, bits 0..20) · `+0x008` `SizeX`, `SizeY`,
`spawnCol`, `Height`, `OverlayHeight`, `pixHeight`, `MeleeRng` (u8) · `+0x010` `BaseW` char[4] · `+0x014`
`HitClass` u8 · `+0x015` 16 × u8 component counts · `+0x025` u8 Σ(count − 1) · `+0x026` 16 × 12 u8 component
codes · `+0x0E8` `HD`..`S8` bits · `+0x0EC` `TotalPieces` · `+0x0F0` `mDT`..`mRN` bits · `+0x0F4` `dDT`..`dRN` u8 ·
`+0x104` `*mv` bits · `+0x108` `InfernoLen`, `InfernoAnim`, `InfernoRollback`, `ResurrectMode` (u8) · `+0x10C`
`ResurrectSkill` s16 · `+0x10E` `htTop`, `htLeft`, `htWidth`, `htHeight` (s16) · `+0x118` `automapCel` u32 ·
`+0x11C` `localBlood`, `Bleed`, `Light`, `light-r/g/b`, `Utrans` ×3 (u8) · `+0x128` `Heart`, `BodyPart`
char[4] · `+0x130` `restore` u32. Every byte is either a mapped field or listed above.

## What the monster pool reads

From [monsters/0001](../findings/monsters/0001-level-pool.md) (plan 0012), with this doc's layout:

- `[C]` `+0x015`..`+0x024` are the sixteen component counts that `sub_005BDB20_MonVariantRoll` draws over: set 0
  takes `Range(R, count)` for each component with count ≥ 2 (0 otherwise), and further sets reroll one or two
  components with count > 1. These are exactly the counts of the `HDv` … `S8v` lists (data, above), so a
  reimplementation can compute them from the `.txt`. (monsters/0001 § 4, fn:sub_005BDB20_MonVariantRoll@0x005BDB20,
  tbl:MonStats2.txt:HDv, run:2026-10-12-mon-pool)
- `[I]` `+0x025` is the exponent of the variant cap, `cap = (1 << (b & 31)) − nVariants`. By data `b` = Σ(count − 1)
  of the lists, so a class with no list longer than one code (461 records) gets **one** appearance set, a class
  with exactly one extra code (Σ = 1) at most two, and Σ ≥ 2 never binds the three sets. The finding saw 0, 16 and
  49 in the logged regions, all values of this column. (monsters/0001 § 4, fn:sub_005BDB20_MonVariantRoll@0x005BDB20)
- `[I]` `+0x0EC` is `TotalPieces`: `sub_00547BC0_MonRegionFindAdd` adds a class not yet in its level's region only
  while the region has fewer than 13 entries **and `TotalPieces` > 2** (218 of 609 records). By data `TotalPieces`
  equals the number of set component flags `HD`..`S8` in 562 of 609 rows, not all. (monsters/0001 § 6,
  fn:sub_00547BC0_MonRegionFindAdd@0x00547BC0, tbl:MonStats2.txt:TotalPieces)

## Interpretation notes

- `[C]` `HD` … `S8` (component present) and the `*v` lists are not the same thing by data: `HD` is set in 146 rows
  and `HDv` non-blank in 144. Which one the client uses to draw is graphics code, not read.
- `[L]` By the names: `m*` = the monster has animation mode *, `d*` = that mode's direction count, `*mv` = the
  monster can move in that mode, `Utrans*` = palette shift per difficulty, `ht*` = hit box, `Inferno*`,
  `Resurrect*` = special animation and skill data. No code anchor (graphics and client side).

## Open questions

- `[L]` Meaning of every column outside § What the monster pool reads; owners are graphics and `monsters/spawn`.
- `[L]` The integer widths marked "width `[I]`" (`MeleeRng`, `TotalPieces`, `restore`, `automapCel`, the `ht*`
  quartet): only a reader of the record fixes them.
