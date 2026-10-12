# MonPlace (`data/global/excel/monplace.txt` → `monplace.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 37 (no `Expansion` marker)   **Record:** 2 B
> **sha256:** `.txt` `1bc9f2d3acf57b65eb7036641c54e7424e5f235bfcd79a71a4ec040b46bc0b75`, `.bin` `1a3a7ee8e4d2d03c0e192b5724794dc2ff238829ac87543078cd9bf1299bfab0`
> **Doc status:** complete for layout; semantics `[L]` (names only)

## Purpose

A list of 37 placement keywords (`place_nothing`, `place_champion`, `place_fallennest`, `place_group25`, …).
A row has no data besides its name. Its only consumer in the data is [MonPreset](MonPreset.md), whose
`Place` column names a MonPlace row (kind 0) where it does not name a monster class or a superunique.
Through MonPreset, DS1 preset monster entries can resolve to a MonPlace row
([drlg/0001 § Object entries](../findings/drlg/0001-ds1-dt1-readers.md#object-entries--preset-units)).
What the game does with such a preset unit belongs to `monsters/spawn` or `drlg/preset` and is open. Leads:
no lead; derived from data.

## Row identity

- `[C]` Key column `code`, 37 distinct values, none blank. Rows are addressed by row index: MonPreset kind 0
  stores the MonPlace row index (`python3 -I tools/excel_bin.py diff <excel-dir> monpreset`, 0 mismatches).
- `[I]` In a stock run `monplace.bin` is **not loaded**. `DATATBLS_LoadCodeLists` loads it only under `-txt`, to
  resolve `code` names while compiling other `.txt` tables. ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300))
  The DS1 reader does not need it either: it turns a kind-0 MonPreset entry into `nMonStats + nSuperUniques + index`
  without reading MonPlace (fn:DS1_Parse@0x00665950, fn:SUPERUNIQUES_GetCount@0x00655710).

## Columns

`[C]` layout by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> monplace` decodes every record and
compares it with every cell, 37 cells, 0 mismatches.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `code` | str, 37 distinct, len ≤ 24, 0 blank | `+0x000` u16: the row's own index (0..36) | the keyword's name; the record holds only its index, the key resolved against its own table | `monplace:code` (itself) | layout [C]; meaning [L] |

## Interpretation notes

- `[C]` Row order (index in brackets), first and last rows: `place_nothing` [0], `place_npc_pack` [1],
  `place_unique_pack` [2], `place_champion` [3], … `place_reanimateddead` [32], `place_group25` [33], `place_group50` [34],
  `place_group75` [35], `place_group100` [36]. The rows in between are hand-placement names (`place_bloodraven`,
  `place_fallennest`, `place_talkingguard`, `place_maggotegg`, `place_impgroup`, `place_deadbarb`, …).
- `[C]` MonPreset names 34 of the 37 rows (69 cells). The three it never names are `place_rogue_warner` [4],
  `place_rivermonster_right` [6] and `place_rivermonster_left` [7]. The most named is `place_nothing` (16 cells,
  in acts 1, 2 and 5), then `place_champion` (5, one per act) and `place_group25..100` (4 each, acts 1–4).
- `[L]` Reading the names: `place_champion` / `place_unique_pack` / `place_npc_pack` look like "spawn a random
  champion / unique pack here", `place_group25..100` like a group placed with a 25..100 % chance, the rest like
  hand-placed special packs (fallen camps, nests, guards). Nothing in the data confirms any of this.

## Open questions

- `[L]` What a preset monster unit whose id lies in the MonPlace range (`≥ nMonStats + nSuperUniques`) does when
  the room is populated: backlog → reverser (plan 0014 Phase 1, preset monsters).
