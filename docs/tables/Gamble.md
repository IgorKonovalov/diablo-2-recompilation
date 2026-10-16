# Gamble (`data/global/excel/gamble.txt` → `gamble.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 125 (126 `.txt` data rows − 1 `Expansion` marker)   **Record:** 12 B
> **sha256:** `.txt` `46a41a1d55deffd66e7808b6a0903adc1dd98e41bf8127f1b97a8ae34833c694`, `.bin` `305c97d39afbe38019ee5dfe47f70d3c6f38b7cc8f35aa5fd5d9b19d966b98ec`
> **Doc status:** layout complete (plan 0031 Phase 0); semantics `[I]` from [items/0009](../findings/items/0009-vendors.md) (plan 0031 Phase 1)

## Purpose

The list of base items a gamble window can offer: one row per base, named by its item code. Reader:
`items/vendors` (plan 0031), the gamble roll ([items/0009 § 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790)).
The item records also carry a `gamble cost` (`+0x0D4`, [Weapons](Weapons.md)). Leads: `src:d2dfg-blizzard`
(§ Gamble.txt), `src:arreat-summit-magic-items` (§ Gambling), not yet fetched; nothing here comes from them.

- `[I]` **The only base list.** `GAMBLE_BuildInv` draws every slot's base from the list `GAMBLE_LoadTable` builds from
  this table (`g_GambleList`): no other table or item column decides which bases can be gambled. Slot 0 is then
  forced to `rin` and slot 1 to `amu`, after their draws. (fn:GAMBLE_LoadTable@0x00638AE0,
  fn:GAMBLE_BuildInv@0x00578790, data:g_GambleList@0x0096CAB0, tbl:Gamble.txt:code)
- `[I]` **Sorted at load.** Each row's `code` is resolved to an item index (an unknown code is fatal) and the base
  `level` (`+0x0FD`) is read; the list is sorted by that level with the CRT `qsort` (unsigned level, ties compare
  equal), and `countUpTo[L]` (L = 1..99) is the number of entries with `level` ≤ L. A slot of gamble level `lvl`
  draws uniformly among the first `countUpTo[lvl]` entries. The order of equal-level entries is what MSVC `qsort`
  leaves, not the `.txt` order. ([items/0009 § 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790), fn:GAMBLE_LoadTable@0x00638AE0)
- `[I]` **Classic redraw.** In a classic game a drawn base of item `version` ≥ 100 is rejected and the slot's level
  and base are drawn again, without advancing the slot. ([items/0009 § 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790), fn:GAMBLE_BuildInv@0x00578790)
- `[I]` The exceptional/elite upgrade of a gambled base reads the base's `ubercode`/`ultracode` and
  [DifficultyLevels](DifficultyLevels.md) `GambleUber`/`GambleUltra`, in an expansion game only
  (fn:GAMBLE_Upgrade@0x005786A0); `NightmareUpgrade`/`HellUpgrade` are read only by the stock path.

## Row identity

- `[C]` The `.bin` is a u32 record count (125) and 125 records of 12 bytes, one per `.txt` row in order, with the
  `Expansion` marker (after data row 107, the `Spiked Shield` row) dropped ([excel-bin.md](../formats/excel-bin.md)).
  The loader allocates 12-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x00638B25`).
- `[C]` `code` is unique (125 distinct) and every code names an item record: 75 weapons, 48 armors, 2 misc (`amu`,
  `rin`). `name` is not compiled.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel gamble`: 125 records × 1 mapped
field = 125 cells, **0 mismatches**. `excel_bin.py unknown … gamble` lists `+0x04..+0x0B`, 0 in every record.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `name` | str, 125 distinct; three cells end in a space (`Broad Axe `, `Long Sword `, `Studded Leather `) | — (not compiled) | editor name of the base `[L]` | — | [C] |
| `code` | str, 125 distinct, 0 blank | `+0x00` char[4] code, space-padded | the base item | [Weapons](Weapons.md), [Armor](Armor.md), [Misc](Misc.md) `code` | [C] |
| — | — | `+0x04` u32 | no column; 0 in every record; at load the base `level` (item record byte `+0xFD`), the sort key `[I]` ([items/0009 § 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790)) | [Weapons](Weapons.md) `level` | [C] value |
| — | — | `+0x08` u32 | no column; 0 in every record; at load the item index of `code` (`EXCEL_FindCode`) `[I]` ([items/0009 § 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790)) | — | [C] value |

## Interpretation notes

- **Which bases are listed.** Every listed weapon and armor is a normal-tier base (its `code` equals its `normcode`);
  `amu` and `rin` have no tier codes. By item type: `tors` 15, `swor` 14, `axe` 10, `bow` 8, `helm` 8, `shie` 8, `h2h`
  7, `pole` 6, and 5 or fewer of `spea`, `glov`, `boot`, `belt`, `jave`, `knif`, `xbow`, `mace`, `hamm`, `club`, `tkni`,
  `taxe`, `circ`, `amul`, `ring`. `[C]` (`python3 -I tools/vendor_survey.py gamble …`)
- **Which are not.** 48 normal-tier, spawnable weapon and armor bases are absent: every staff (`staf`), wand, sceptre
  and orb, every class-specific base (`abow`, `aspe`, `ajav`, `head`, `pelt`, `phlm`, `ashd`), and the six throwing
  potions (`tpot`). `[C]` for the list; `[I]` the game gambles only from this table (Purpose).
- **The 18 rows after the marker** are the throwing weapons and javelins (`tkf`, `tax`, `bkf`, `bal`, `jav`, `pil`,
  `ssp`, `glv`, `tsp`; item `version` 0), the seven katars and claws and the two circlets (`ci0`, `ci1`; `version`
  100). All 107 rows before the marker are `version` 0. The marker takes no record. `[C]` for the versions; `[I]` a
  classic game filters by the item `version` test (the redraw in Purpose), not by a row count.
- **Upgrades.** 80 of the 125 bases have a `NightmareUpgrade` that names an item and 72 a `HellUpgrade`
  ([Weapons § Vendor columns](Weapons.md#vendor-columns-plan-0031-phase-0)); `[I]` gambling does not read them: its
  upgrade is the `ubercode`/`ultracode` test of `GAMBLE_Upgrade` (Purpose).
- `[I]` **`+0x04..+0x0B`** are 8 bytes no column feeds, 0 in the file. `GAMBLE_LoadTable` writes them into these
  records: `+0x04` the base `level` (the item record's byte `+0xFD`, as a u32), `+0x08` the item index of `code`. It
  then sorts the records in place by `+0x04` and copies each sorted record's `+0x08` into a separate index array
  (`g_GambleList+4`). ([items/0009 § 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790), fn:GAMBLE_LoadTable@0x00638AE0)

## Open questions

- Answered `[I]` by [items/0009 § 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790): how the
  window draws from the list (14 slots, store seed), the gamble level, the quality roll (see
  [DifficultyLevels](DifficultyLevels.md)) and the classic filter.
- Answered `[I]` by [items/0009 § 7](../findings/items/0009-vendors.md#7-gambling-gamble_buildinv-0x00578790): `+0x04..+0x0B` hold the base level and the item index after the load
  (Interpretation notes).
- Answered `[C]` by [items/0009 § The gamble list order](../findings/items/0009-vendors.md#the-gamble-list-order-stock-data):
  the equal-level order MSVC `qsort` leaves on stock data, dumped (`VGL`) and the same in every run of
  run:2026-10-15-vendors; a reimplementation takes that order, not the `.txt` order.
