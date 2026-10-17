# MonPlace (`data/global/excel/monplace.txt` → `monplace.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 37 (no `Expansion` marker)   **Record:** 2 B
> **sha256:** `.txt` `1bc9f2d3acf57b65eb7036641c54e7424e5f235bfcd79a71a4ec040b46bc0b75`, `.bin` `1a3a7ee8e4d2d03c0e192b5724794dc2ff238829ac87543078cd9bf1299bfab0`
> **Doc status:** complete for layout; what the preset spawn does for every row from monsters/0002 § 7 and monsters/0003 § 7 (plan 0039 P1c, `lane/rbs3`), other readers open

## Purpose

A list of 37 placement keywords (`place_nothing`, `place_champion`, `place_fallennest`, `place_group25`, …).
A row has no data besides its name. Its only consumer in the data is [MonPreset](MonPreset.md), whose
`Place` column names a MonPlace row (kind 0) where it does not name a monster class or a superunique.
Through MonPreset, DS1 preset monster entries can resolve to a MonPlace row
([drlg/0001 § Object entries](../findings/drlg/0001-ds1-dt1-readers.md#object-entries--preset-units)).
What the game does with such a preset unit is in § Interpretation notes (plan 0039 P1c). Leads:
no lead; derived from data.

## Row identity

- `[C]` Key column `code`, 37 distinct values, none blank. Rows are addressed by row index: MonPreset kind 0
  stores the MonPlace row index (`python3 -I tools/excel_bin.py diff <excel-dir> monpreset`, 0 mismatches).
- `[I]` In a stock run `monplace.bin` is **not loaded**. `DATATBLS_LoadCodeLists` loads it only under `-txt`, to
  resolve `code` names while compiling other `.txt` tables. ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300))
  The DS1 reader does not need it either: it turns a kind-0 MonPreset entry into `nMonStats + nSuperUniques + index`
  without reading MonPlace (fn:DS1_Parse@0x00665950, fn:SUPERUNIQUES_GetCount@0x00655710).
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` the game loads this table as one of
  the 15 code lists of `DATATBLS_LoadCodeLists` and writes a `monplace.bin` byte-identical to the shipped one, which
  ships in patch_d2 ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3). That a stock run never loads it stays `[I]`: the file ships, so its absence could not show it (data/0001 §
  S1b row 30). (fn:DATATBLS_LoadCodeLists@0x00612750)

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
  hand-placed special packs (fallen camps, nests, guards). Nothing in the data confirms any of this; the code
  reading below (`[I]`, by row) replaces this reading for the preset spawn.
- `[I]` **The preset spawn switches on the row index.** `sub_0054E600_PresetMonSpawn` takes a preset unit whose id is
  in the MonPlace range (`id ≥ nMonStats + nSuperUniques`) and branches on the MonPlace index `id − nMonStats −
  nSuperUniques` ([monsters/0002 § 7](../findings/monsters/0002-room-population.md#7-wanderers-monspcwalk-presets-and-superuniques), fn:sub_0054E600_PresetMonSpawn@0x0054E600). By row:
  - `[C]` 2 `place_unique_pack`: a class picked from the level's region, made a unique boss **at a random point of
    the room** away from warps (not the preset point), with 3..6 minions; 3 `place_champion`: the same class pick, a
    champion pack at the point, always champion mod 16 ([monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20), run:2026-10-14-mon-special).
  - Fixed classes at the point, `[C]` for the six cases logged at the branch (17, 18, 23, 29, 30 in level 111, 31;
    H4b special 65), `[I]` for 22, 32 and `deathmauler1` in level 110: 17 `place_fallen` → `fallen1`, 18 `place_fallenshaman` →
    `fallenshaman1`, 22 `place_fetish` → `fetish1`, 23 `place_fetishshaman` → `fetishshaman1`, 29 `place_deadminion`
    → `minion1`, 30 `place_deadimp` → `imp1` (`deathmauler1` in level 110), 31 `place_deadbarb` → `act5barb1`, 32
    `place_reanimateddead` → `reanimatedhorde3`, the last four in mode 12. Each class then goes through
    `sub_0063EC70_LevelClassVariant` and `sub_0054E2A0_PresetFallenVariant` (keyed on the class's `BaseId`: the
    act-1 fallen and fallen shaman variant by level id), and the unit is made at the point
    ([monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20), [monsters/0003 § Plan 0038 batch H4b](../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b), fn:sub_0054E2A0_PresetFallenVariant@0x0054E2A0).
  - `[I]` 24 `place_impgroup` and 26 `place_miniongroup` are Normal-only group spawns (`imp1`/`deathmauler1` by
    level 110, or `minion1`: a leader in the preset's box and `MinGrp − 1 + RangeB(…)` members around it); in Hell
    both placed nothing in the logs `[C]`. Outside Normal, 24 gives class 0 in the fixed-class table
    ([monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)). Rows 19–21
    never reach that table (next bullet), which corrects the earlier "19–21 class 0" reading.
  - `[I]` **Every other row, from the switch** ([monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20),
    bullet *Every MonPlace row, from the switch*; `lane/rbs3`, static). The MonPlace branch switches on `index − 2` with the
    bound `0x1E` (0x0054E76F–0x0054E782). Rows the code places, all at the preset point through `SpawnAtPos`:
    - 4 `place_rogue_warner` → class 266 `navi`, flags 0 (0x0054E919–0x0054E933);
    - 5 `place_bloodraven` → class 267 `bloodraven`, flags 0 (0x0054E808–0x0054E840);
    - 8 `place_tightspotboss` → class 284 `maggotqueen1`, flags 8 (0x0054E943–0x0054E95D);
    - 10 `place_tentacle_ns` (flags 4) and 11 `place_tentacle_ew` (flags 0) → class 261 `tentaclehead1` stepped along
      `NextInClass` by level id: `tentaclehead2` in levels 76–78 (Act 3 Jungle 1–3), `tentaclehead3` in 92 and 93 (Act 3
      Sewer 1–2), else `tentaclehead1` (0x0054E789–0x0054E7F8, fn:sub_0054DA60_MonClassChainStep@0x0054DA60).

    Rows that **place nothing** (the branch returns 0 with no call, `0x0054EAFE`): 0 `place_nothing`, 1 `place_npc_pack`,
    6 and 7 the river monsters, 9 `place_amphibian`, 12 `place_fallennest`, 13 `place_fetishnest`, 14 `place_talkingrogue`,
    15 `place_talkingguard`, 16 `place_dumbguard`, 19 `place_maggot`, 20 `place_maggotegg`, 21 `place_mosquitonest`,
    and **33–36 `place_group25` to `place_group100`** (rows 0, 1 and 33–36 fail the bound; the others have byte 8 in the
    case table). 25 `place_imp`, 27 `place_minion` and 28 `place_bloodlord` hit the fixed-class table's entry
    `0x0054EAB1`, which also returns 0. H4b's case-36 calls are this branch.

    **Scope.** "Place nothing" holds in `sub_0054E600_PresetMonSpawn` and its caller `PresetUnitDispatch`, which returns
    the result with no fallback (0x005558DD–0x005558EA). `PresetUnitDispatch` is reached from both the first spawn
    (`PresetUnitSpawn`, 0x00555949) and the restore of an inactive room (`RoomInactiveUnitsRestore`, 0x00542C29), so
    both go through this switch. Four other callers of `PresetMonSpawn` (0x00545C75, 0x0058A70D in
    `A5Q3_NihlathakBossSpawn`, 0x005AA231, 0x005ACB43) and any other reader of a room's kept preset monster units are
    not followed. For rows 33–35 the DRLG preset pass first keeps or drops the unit on a room-seed draw (0x0066777D,
    [drlg/preset](../specs/drlg/preset.md)); a kept group preset then places nothing here. (fn:sub_0054E600_PresetMonSpawn@0x0054E600,
    fn:sub_005B2F20_SpawnAtPos@0x005B2F20, tbl:MonStats.txt:NextInClass)

## Open questions

- ~~What a preset monster unit whose id lies in the MonPlace range does when the room is populated~~ answered `[I]`
  for every row in § Interpretation notes (plan 0039 P1c; the rest from the `PresetMonSpawn` switch, `lane/rbs3`,
  [monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)), including
  `place_group25..100`, which place nothing there.
- `[L]` Whether a "place nothing" row (0, 1, 6, 7, 9, 12–16, 19–21, 25, 27, 28, 33–36) does anything through the four
  unfollowed callers of `PresetMonSpawn` or another reader of the room's preset monster units (§ Interpretation notes,
  *Scope*).
