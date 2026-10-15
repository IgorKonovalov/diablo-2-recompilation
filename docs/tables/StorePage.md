# StorePage (`data/global/excel/StorePage.txt` → `storepage.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 4   **Record:** 4 B
> **sha256:** `.txt` `8f9cdd23c8b6a77dc0674ae2f2941b7e7e600ec0962ea96fc3c2e8a508aae690`, `.bin` `02bbf9112397903b0c5716a6096192a645606945337a550cfa3d49772665a2a9`
> **Doc status:** layout complete (plan 0031 Phase 0); semantics `[L]`

## Purpose

A code list naming the tabs of a vendor's trade window: `armo` (Armor Page), `weap` (Weapons Page), `mag` (Magic
Page), `misc` (Misc Page). [ItemTypes](ItemTypes.md) `StorePage` (`+0x022`, u8) holds a row index into it. Reader:
`items/vendors` (plan 0031): which page a stocked item goes to.

## Row identity

- `[C]` The `.bin` is a u32 record count (4) and four 4-byte records, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The key is `Code`; ItemTypes stores its row index (a blank cell stores
  `0xFF`, [excel-bin.md § Cell encoding rules](../formats/excel-bin.md#cell-encoding-rules)).
- `[I]` **A stock run never loads `storepage.bin`.** It is one of the code lists that `DATATBLS_LoadCodeLists` loads
  only under `-txt`, to resolve ItemTypes `StorePage` cells while compiling `itemtypes.txt`
  ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300),
  `0x00612925`). At run time the page is the index stored in the ItemTypes record, and the codes here are not read.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel storepage`: 4 records × 1 mapped
field = 4 cells, **0 mismatches**.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Store Page` | str, 4 distinct | — (not compiled) | editor name of the page `[L]` | — | [C] |
| `Code` | str, 4 distinct: `armo`, `weap`, `mag`, `misc` | `+0x0` char[4] code, space-padded | the page code | referenced by [ItemTypes](ItemTypes.md) `StorePage` | [C] |

## Interpretation notes

- **Which item types name which page** ([ItemTypes](ItemTypes.md) `StorePage`, over its 103 rows): `armo` (row 0) on
  12 types (`shie`, `tors`, `boot`, `glov`, `belt`, `helm`, `head`, `ashd`, `phlm`, `pelt`, `cloa`, `circ`), `weap`
  (row 1) on 18 (`scep`, `wand`, `staf`, `bow`, `axe`, `club`, `swor`, `hamm`, `knif`, `spea`, `pole`, `xbow`, `mace`,
  `h2h`, `orb`, `abow`, `aspe`, `h2h2`), `misc` (row 3) on 45 (potions, scrolls, books, keys, quivers, gems, runes,
  jewels, charms, rings, amulets, throwing weapons and javelins among them), blank on 28 (the parent types such as
  `weap`, `armo`, `misc`, the class groups, `gold`, `ques`). `[C]`
- **`mag` (row 2) is named by no item type.** Whether the trade window's magic tab is filled by item quality rather
  than by type is a code question. `[L]`
- An item type's page is not inherited through `Equiv1`/`Equiv2` by the data alone: the parent types are blank. `[L]`
  for how the game resolves it.

## Open questions

- `[L]` Where the store puts a stocked item: the ItemTypes page of its type, a quality rule for the magic tab, or
  something else. Reverser, plan 0031 Phase 1.
