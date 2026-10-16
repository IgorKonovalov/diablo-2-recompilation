# StorePage (`data/global/excel/StorePage.txt` → `storepage.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 4   **Record:** 4 B
> **sha256:** `.txt` `8f9cdd23c8b6a77dc0674ae2f2941b7e7e600ec0962ea96fc3c2e8a508aae690`, `.bin` `02bbf9112397903b0c5716a6096192a645606945337a550cfa3d49772665a2a9`
> **Doc status:** layout complete (plan 0031 Phase 0); the tab rule `[I]` from [items/0009](../findings/items/0009-vendors.md)

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
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` the game loads this table as one of
  the 15 code lists of `DATATBLS_LoadCodeLists` and writes a `storepage.bin` byte-identical to the shipped one, which
  ships in d2exp ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3). That a stock run never loads it stays `[I]`: the file ships, so its absence could not show it (data/0001 §
  S1b row 30). (fn:DATATBLS_LoadCodeLists@0x00612750)

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
- `[I]` **The tab rule** (`VENDOR_CreateStockItem`): a stocked item goes to the page its item type's `StorePage`
  names (`sub_0062E880_ItemStorePage`); a page of −1 (no page) destroys the item. When placing it on page 1 (`weap`)
  fails, the item tries page 2 (`mag`). Any other failed placement (page 0, 2 or 3, or page 2 after page 1) parks
  the item and counts the creation as failed. Item quality plays no part. Gamble items all go to page 0.
  ([items/0009 § 5](../findings/items/0009-vendors.md#5-one-stock-item-vendor_createstockitem-0x00576330),
  [§ 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790), fn:VENDOR_CreateStockItem@0x00576330,
  tbl:ItemTypes.txt:StorePage)
- **`mag` (row 2) is named by no item type.** `[I]` So it holds only the weapons that overflow page 1 (the tab rule
  above), whatever their quality.
- `[I]` **No inheritance.** `sub_0062E880_ItemStorePage` returns the item type record's own byte `+0x22`, or −1
  when it is `0xFF` (blank) or the type is out of range; it does not walk `Equiv1`/`Equiv2`. A type with a blank
  `StorePage` therefore has no tab, and its stock item is destroyed. ([items/0009 § 5](../findings/items/0009-vendors.md#5-one-stock-item-vendor_createstockitem-0x00576330),
  fn:sub_0062E880_ItemStorePage@0x0062E880, 0x00576555–0x0057657A)

## Open questions

- Answered `[I]` by [items/0009 § 5](../findings/items/0009-vendors.md#5-one-stock-item-vendor_createstockitem-0x00576330): the tab rule, and a blank `StorePage` gives −1 (no `Equiv` walk), above.
