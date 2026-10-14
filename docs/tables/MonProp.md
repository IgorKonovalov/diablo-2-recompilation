# MonProp (`data/global/excel/monprop.txt` → `monprop.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 13 (no `Expansion` marker)   **Record:** 312 B (`0x138`)
> **sha256:** `.txt` `2e7b22f19aa571f1ee3cca8426e219d146471b0b13a25c5fb70a452c2c8c9f4d`, `.bin` `bc85bf2f9607ec8fc0ccacf82e0b1c1e2fc02eda80d1dc81d2d66dc39cc92db9`
> **Doc status:** columns listed, `.bin` layout complete except the slots of `par` and `chance` (blank in every row, placed by choice), semantics pending

## Purpose

One row per set of item-style properties given to a monster class, per difficulty: up to six slots
(`prop`, `chance`, `par`, `min`, `max`) for normal, six for nightmare (`… (N)`) and six for hell (`… (H)`). The
`prop` cells are `Properties.txt` codes (`fade`, `thorns`, `extra-fire`, `cast2`, …). A MonStats class names its
row in `MonStats.MonProp`. Read by `monsters/stats` (plan 0025); which code applies a row, and when, is not known yet.

## Row identity

- `[C]` `Id` is compiled as the row's own index (u32 at `+0x000`, 0..12), and `MonStats.MonProp` (`+0x01A` u16)
  stores the index of the row whose `Id` matches its cell, `0xFFFF` when blank
  ([MonStats.md](MonStats.md), `excel_bin.py diff` on both tables). (tbl:MonProp.txt:Id, tbl:MonStats.txt:MonProp)
- `[C]` `Id` is unique. Eleven rows are named after the one MonStats class that uses them; `blunderbore` serves six
  classes (`blunderbore1..6`) and `mephisto` two (`mephisto`, `ubermephisto`). `irongolem` is named by **no**
  MonStats record (the `irongolem` class has `MonProp` blank). 18 MonStats records name a row in all
  (`mon_survey.py stats … all all`). (tbl:MonStats.txt:MonProp)
- `[C]` The loader reads `monprop.bin` with 312-byte records
  ([data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), call site
  `0x006594B3`); the record count (13) equals the `.txt` data rows.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> monprop` decodes every
record and compares it with every mapped cell (13 records × 91 fields = 1 183 cells, 0 mismatches). `[C]` when the
column's values pin its offset (probe finds no other offset that fits), `[I]` when the column is blank in every
row and the slot follows the pinned strides (`0x10` per slot, `0x60` per difficulty), `[L]` where two placements
fit the data equally (`par`, `chance`, below). Ranges are over the 13 rows, computed by script.

`d` is the difficulty (0 normal, 1 `(N)`, 2 `(H)`), `k` the slot 1..6. Field offsets:

| Column | `.bin` field | Layout tag |
|---|---|---|
| `Id` | `+0x000` u32, = row index | [C] |
| `prop<k>[ (N)/(H)]` | `+0x004 + 0x60·d + 0x10·(k−1)` s32: `Properties.txt` row index, blank −1 | [C] where set, [I] otherwise |
| `par<k>…` | `+0x008 + 0x60·d + 0x10·(k−1)` s32 | [L] |
| `min<k>…` | `+0x00C + 0x60·d + 0x10·(k−1)` s32 | [C] where set, [I] otherwise |
| `max<k>…` | `+0x010 + 0x60·d + 0x10·(k−1)` s32 | [C] where set, [I] otherwise |
| `chance<k>…` | `+0x124 + 6·d + (k−1)` u8 | [L] |
| `*eol` | — (end-of-line marker, always 0) | — |
| (no column) | `+0x136` u16, 0 in every record | — |

Observed values of the cells that are not blank everywhere (75 of the 91 compiled columns are blank in all 13 rows):

| Column | Observed type / range | References | Tag |
|---|---|---|---|
| `Id` | str, 13 distinct, 0 blank | — | [C] |
| `prop1` | str 2 distinct (`fade`, `stupidity`), 10 blank | `properties:code` | [C] |
| `min1` / `max1` | int −1..16 (3 distinct), 10 blank | — | [C] |
| `prop1 (N)` | str 6 distinct (`cast2`, `crush`, `extra-fire`, `fade`, `stupidity`, `thorns`), 1 blank | `properties:code` | [C] |
| `min1 (N)` / `max1 (N)` | int −1..60 (6 / 7 distinct), 1 blank | — | [C] |
| `prop2 (N)` | str, always `swing2`, 12 blank | `properties:code` | [C] |
| `min2 (N)` / `max2 (N)` | int, always 15, 12 blank | — | [C] |
| `prop1 (H)` | str 7 distinct (the six of `(N)` and `knock`), 0 blank | `properties:code` | [C] |
| `min1 (H)` / `max1 (H)` | int −1..120 (8 / 9 distinct), 0 blank | — | [C] |
| `prop2 (H)` | str, always `swing2`, 12 blank | `properties:code` | [C] |
| `min2 (H)` / `max2 (H)` | int, always 30, 12 blank | — | [C] |
| every `chance*`, every `par*`, slots 3..6 of every difficulty, slot 2 of normal | blank in all 13 rows | — | — |

- `[C]` Every `prop` cell resolves to a `Properties.txt` `code` (the diff looks each one up; a key not found would
  store −1). `fade` is row 262, whose `Properties.txt` comment cell says "only use on monprop". (tbl:MonProp.txt:prop1)
- `[C]` `min` ≤ `max` in every slot that is set; they are equal in all but the `thorns` rows (`quillrat6..8`:
  15..20 in nightmare, 30..40 in hell). The only negative values are `druidhawk`'s `stupidity` −1/−1 in all three
  difficulties. (tbl:MonProp.txt:min1)

## Record layout (312 bytes)

```
+0x000  u32  Id (row index)
+0x004  normal    : 6 slots × 16 B   { s32 prop; s32 par; s32 min; s32 max }
+0x064  nightmare : 6 slots × 16 B
+0x0C4  hell      : 6 slots × 16 B
+0x124  u8   chance[3][6]   (difficulty-major)
+0x136  u16  padding (0 in every record)
```

- `[C]` The strides are pinned: `prop1` at `+0x004`, `prop2 (N)` at `+0x074` and `prop2 (H)` at `+0x0D4` give `0x10`
  per slot and `0x60` per difficulty; `min1 (N)`/`max1 (N)` (`+0x06C`/`+0x070`) and `min1 (H)`/`max1 (H)`
  (`+0x0CC`/`+0x0D0`) pin `min` and `max` to the third and fourth dword of a slot. Widths: the slot is 16 bytes and
  holds four dwords (`prop` needs 9 bits, `min`/`max` are −1 in a row, so 32-bit signed is consistent) `[I]`.
- `[L]` **`par` and `chance` are blank in all 13 rows**, so the data cannot place them. Two layouts fit equally:
  (a) the one above, `par` the second dword of the slot and the 18 `chance` cells as u8 in a 20-byte tail with
  2 bytes left over; (b) `chance` the second dword and the 18 `par` cells in the tail. The layout uses (a) because
  `chance` reads as a percentage (fits a byte) and a property's `par` elsewhere is a dword (e.g. MagicPrefix `mod1param`), but only the
  loader's field descriptor or a reader settles it ([backlog](../backlog.md), archivist → reverser).
- `[C]` The 20 bytes `+0x124..+0x137` are 0 in every record, consistent with 18 blank u8 cells and 2 bytes of
  padding under (a). (`excel_bin.py unknown monprop`)

## Interpretation notes

- `[L]` Read by the names: when a monster of a class with a `MonProp` row is created in difficulty `d`, each slot
  of that difficulty with a `prop` adds the property `prop` with parameter `par` and a value in `min..max`, if a
  `chance` roll passes. **`chance` is blank (0) in every slot**, so if the code gates a slot on `chance` as a
  plain percentage, no slot would ever apply; the code must treat 0 differently (for example as "always") or ignore
  it. This is the first thing plan 0025 Phase 1 should read.
- `[C]` Data only: normal has a slot set in 3 rows only (`baboon6` `fade` 1, `irongolem` `fade` 16, `druidhawk`
  `stupidity` −1); nightmare in 12 rows (all but `bloodraven`); hell in all 13. `mephisto` is the only row with a
  second slot (`cast2` and `swing2`, 15 in nightmare, 30 in hell). (tbl:MonProp.txt:prop1 (N))
- `[L]` `tools/mon_survey.py stats <excel-dir> <class> <difficulty>` prints a class's row for one difficulty beside
  its MonStats and MonLvl cells.

## Open questions

- `[L]` The `par`/`chance` placement (above), when a row applies (at creation? for every monster of the class, or
  only some kinds?), how `chance` 0 is treated, and how the `irongolem` row is reached with no MonStats record
  naming it ([backlog](../backlog.md), archivist → reverser; plan 0025 Phase 1).
