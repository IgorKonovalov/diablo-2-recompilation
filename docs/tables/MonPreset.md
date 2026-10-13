# MonPreset (`data/global/excel/monpreset.txt` → `monpreset.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 229 (no `Expansion` marker)   **Record:** 4 B
> **sha256:** `.txt` `c71ac39afa5e2046510d4f44d8f809828104aa7d20ae7e5dd11f9385eab87bce`, `.bin` `a61f484c591d4e76fb82dc9de467207a01cabb0996d38813ffae677bb79c0931`
> **Doc status:** complete for layout; `Place` kind and per-act indexing `[I]` (drlg/0001); what the game does with each kind open

## Purpose

The per-act translation list for **preset monsters in DS1 maps**. A DS1 object entry of `type` 1 carries a
small `id`; the reader looks that id up in the act's MonPreset list and gets either a monster class
(MonStats), a superunique (SuperUniques) or a placement keyword (MonPlace)
([drlg/0001 § Object entries](../findings/drlg/0001-ds1-dt1-readers.md#object-entries--preset-units),
[ds1.md](../formats/ds1.md)). Feeds `drlg/preset` and the preset-monster side of `monsters/spawn`. Leads:
no lead; derived from data and drlg/0001.

## Row identity

- `[C]` No key column. Rows are grouped by `Act` (1..5, in non-decreasing order over the file): act 1 has 47 rows,
  act 2 59, act 3 39, act 4 28, act 5 56.
- `[I]` A row is addressed by its **position within its act**: `MONPRESET_GetActList(act)` returns the act's
  records and count, and the DS1 entry's `id` indexes that list; an `id` at or past the count passes through raw
  (fn:MONPRESET_GetActList@0x00659B40, data:g_MonPresetLists@0x0096C6DC, data:g_MonPresetCounts@0x0096C6F0,
  fn:DS1_Parse@0x00665950).
- `[C]` Data behaviour agrees: over every clean DS1 file of version ≥ 5, **all 2 676** `type` 1 entries have an
  `id` below their act's MonPreset count, taking the act as `DS1_Parse` does (header `act`, clamped to at most 4;
  [drlg/0001](../findings/drlg/0001-ds1-dt1-readers.md#ds1_parse-in-stream-order) step 2). **(corrected)** This doc
  said before that the 4 entries in `siege_32x32eboss.ds1` and `siege_32x32sboss.ds1` (header `act` 5) pass
  through raw. With the clamp they index the act-5 list (position 5, `place_impgroup`). Act 1 DS1 files use 34
  of its 47 positions, act 2 39 of 59, act 3 33 of 39, act 4 15 of 28, act 5 44 of 56. The files LvlPrest names
  use 34, 37, 33, 15 and 41 (`python3 -I tools/ds1.py units`, plan 0016 Phase 0).

## Columns

`[C]` layout by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> monpreset` decodes every record and
compares it with every cell (`Place` twice, once per field), 687 cells, 0 mismatches. The layout is in
`tools/excel_layouts.py`; `Place` uses the `P` (tagref) field type.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Act` | int 1..5, 0 blank | `+0x000` u8 | the act whose list holds the row (1-based here; the DS1 header `act` is 0-based) | — | layout [C]; meaning [I] (fn:MONPRESET_GetActList@0x00659B40) |
| `Place` | str, 183 distinct, len ≤ 24, 0 blank | `+0x001` u8 kind: 0 MonPlace, 1 MonStats, 2 SuperUniques | which table the name was found in | `monplace:code`, `monstats:Id`, `superuniques:Superunique` | layout [C]; meaning [I] (fn:DS1_Parse@0x00665950) |
| `Place` | (same cell) | `+0x002` u16 index | the row in that table: a MonStats `Id` ordinal, a SuperUniques row, a MonPlace row | as above | layout [C]; meaning [I] (fn:DS1_Parse@0x00665950) |

## Interpretation notes

- `[C]` Kinds over the 229 rows: MonStats 104 (93 distinct classes), MonPlace 69 (34 distinct keywords),
  SuperUniques 56 (56 distinct). Per act (MonPlace / MonStats / SuperUniques): act 1 16/18/13, act 2 21/29/9,
  act 3 12/16/11, act 4 5/15/8, act 5 15/26/15.
- `[C]` Every `Place` value is found, with exact case, in exactly one of the three tables, so the data does not
  say in which order the compiler searches them. `Griswold` and `Radament` would also match MonStats `griswold`
  and `radament` ignoring case; they compile as superuniques (kind 2), so the compiler either compares with case
  or searches SuperUniques before MonStats `[L]`. The layout searches MonStats, SuperUniques, MonPlace.
- `[C]` SuperUniques rows never named: 10 of 66, `The Summoner`, `Ancient Barbarian 1..3`, `Nihlathak Boss` and
  `Baal Subject 1..5`. Those monsters are placed by other code (quests, level scripts), which is outside this table.
- `[C]` Repeats within an act: `place_nothing` (act 1 twice, act 2 nine times, act 5 five times), `place_fallen`
  and `place_fallenshaman` (act 1 twice each), and three MonStats classes (two in act 1, one in act 5). A repeat
  gives two DS1 ids the same meaning.
- `[I]` What the DS1 reader builds from a row: kind 1 → monster id = the MonStats index; kind 2 → `nMonStats +
  index`; kind 0 → `nMonStats + nSuperUniques + index`; any other kind → no unit (`id = −1`). So a preset monster
  unit's id is one number over three ranges, MonStats, SuperUniques, MonPlace. (fn:DS1_Parse@0x00665950,
  fn:SUPERUNIQUES_GetCount@0x00655710, data:g_nMonStats@0x0096C6B0)
- `[C]` Preset monster units per act and range over the DS1s LvlPrest names (MonStats / SuperUniques / MonPlace):
  act 1 113/28/275, act 2 150/24/13, act 3 396/24/399, act 4 54/2/7, act 5 203/36/543. No entry passes through
  raw. Details are in [ds1.md § Monsters per MonPreset range](../formats/ds1.md#monsters-per-monpreset-range).
- Illustrative rows: act 1 position 0 `gheed` (kind 1, MonStats 147); act 1 position 11 `place_fallenshaman`
  (kind 0, MonPlace 18); act 1 position 34 `Bishibosh` (kind 2, SuperUniques 0).

## Open questions

- `[L]` What the room population does with a preset unit in each of the three ranges (a MonStats class placed
  as is, a superunique with its group, a MonPlace keyword such as `place_champion`): backlog → reverser
  (plan 0014 Phase 1, preset monsters; `drlg/preset`).
- `[L]` The compiler's search order for `Place` (data cannot settle it; only matters to a modder who reuses a name).
