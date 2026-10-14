# SuperUniques (`data/global/excel/superuniques.txt` → `superuniques.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 66 (67 `.txt` rows minus the `Expansion` marker)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `a2f954f2ca3e27353d8895650263928845cf8e9378e41fd4005a1a6b3f27320a`, `.bin` `239ac86c98186a4e0a7f7ab65531658e87e2b780f36387a1a141d545f083e0e1`
> **Doc status:** complete for layout and value ranges; semantics `[I]` for the columns the spawn path and the client name
> read ([monsters/0003](../findings/monsters/0003-special-monsters.md)), the TC columns `[I]`/`[C]` (items/0001), `Stacks` `[I]` (monsters/0002 § 7);
> `EClass`, `Replaceable`, `Utrans*`, `MonSound` `[L]`

## Purpose

One row per named "superunique" monster (Bishibosh, Rakanishu, The Countess, … Nihlathak): its base
monster class, its fixed modifiers, group size, colour transform and a treasure class per difficulty.
Read by the drop code for the monster's TC ([items/0001 §3](../findings/items/0001-tc-resolution.md#3-monster-tc-selection--monster_dropitems-0x005a6600));
the spawning side is `sub_005A49B0_SuperUniqueSpawn` ([monsters/0003 § 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn)); generation columns below. Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` starts with a u32 record count (66) followed by 66 records of 52 bytes
  ([excel-bin.md](../formats/excel-bin.md)). The `Expansion` marker (`.txt` row 42) takes no record, so
  the 24 rows after it have record index = `.txt` data row − 1.
- `[C]` Both `hcIdx` and the self-reference of the key column `Superunique` hold the record index
  (0..65) in every record, at `+0x000` (u16) and `+0x008` (u32).
- `[I]` The game gets a record by superunique index (the monster's `+0x26` superunique id) through
  `sub_006556E0_SuperUniqueGet`, which returns 0 when there is none
  ([items/0001 Functions](../findings/items/0001-tc-resolution.md#functions), `0x006556E0`).

## Columns

`[C]` `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel superuniques`: 66 records ×
20 mapped fields = 1 320 cells, **0 mismatches**. With the two zero fields below every byte of the
record is accounted for. Observed ranges are over the 67 `.txt` rows (the marker row is blank).

| Column | Observed type / range | `.bin` field | Meaning (`[L]` unless stated) | References | Layout tag |
|---|---|---|---|---|---|
| `Superunique` | str, 67 distinct, len ≤ 24 | `+0x008` u32 (own row index) | key; the internal name. `[I]` The `+0x08` field selects the record's hard-coded spawn tail, [§ 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn) | — | [C] value, [L] which of the two index fields |
| `Name` | str, 66 distinct, len ≤ 24, 1 blank | `+0x002` u16 string index | display-name key in the `.tbl` files ([tbl.md](../formats/tbl.md)); `[I]` the client's name for the superunique (5382 when 0), [§ 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll) | string tables | [C] |
| `Class` | str, 62 distinct, len ≤ 16, 1 blank | `+0x004` u32 record index | base monster class; `[I]` the class placed, no spawn when < 0, [§ 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn) | `monstats:Id` | [C] |
| `hcIdx` | int 0..65 | `+0x000` u16 | row number; `[I]` not read on the spawn path, [Data touched](../findings/monsters/0003-special-monsters.md#data-touched) | — | [C] value, [L] which of the two index fields |
| `MonSound` | str, 3 distinct, 64 blank | `+0x018` u32 record index, blank 0 | sound set override (`countess`, `smith`, `smithdemon`); `[I]` not read on the spawn path | `monsounds:Id` | [C] |
| `Mod1`, `Mod2`, `Mod3` | int 0..30, 0..30, 0..24; set on 62 / 44 / 4 records | `+0x00C`, `+0x010`, `+0x014` u32, blank 0 | `[I]` fixed mods, written into the mod list as they are up to the first 0 (`thief` 24 dropped), without `ModEligible`, [§ 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn) | [MonUMod](MonUMod.md) `id` (= row index) `[I]` | [C] |
| `MinGrp`, `MaxGrp` | int 0..9 each; equal on 65 records, 5..6 on Frozenstein; 0..0 on 16 | `+0x01C`, `+0x020` u32 | `[I]` minion count `MinGrp + d .. MaxGrp + d` (`d` = difficulty, added only when both are non-zero), one `RangeB` draw, [§ 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn) | — | [C] |
| `AutoPos` | int 0..1; 1 on 40 records (all of rows 0–41 but Rakanishu and Coldworm) | `+0x024` u8 | `[I]` ≠ 0 = placed at a random point of the room instead of the preset point, [§ 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn) | — | [C] |
| `EClass` | int 0..1; 1 on 22 records (records 42–65 less Baal Subject 1, 2) | `+0x025` u8 | expansion superunique (by the rows); `[I]` not read on the spawn path | — | [C] |
| `Stacks` | int 0..1; 1 on 10 records (Siege Boss, Ancient Barbarian 1–3, Nihlathak Boss, Baal Subject 1–5) | `+0x026` u8 | may be placed again once placed `[I]` (below) | — | [C] |
| `Replaceable` | int 1, 57 blank (set on 10 rows: Rakanishu, Treehead WoodFist, Griswold, …) | `+0x027` u8 | —; `[I]` not read on the spawn path | — | [C] |
| `Utrans`, `Utrans(N)`, `Utrans(H)` | int 4..38 (31 distinct), the three equal in every record | `+0x028`, `+0x029`, `+0x02A` u8 | colour transform per difficulty; `[I]` not read on the spawn path | — | [C] bytes; [L] which byte is which difficulty (the three are equal in every row) |
| `TC`, `TC(N)`, `TC(H)` | str, 26 distinct each, 4 blank | `+0x02C`, `+0x02E`, `+0x030` u16: TreasureClassEx row + 161, blank 0 | treasure class per difficulty, see below | `treasureclassex:Treasure Class` | [C] |
| `*eol` | always 0 | — (end-of-line marker; not compiled) | — | — | — |

### Fields with no `.txt` column

| offset | type | observed | tag |
|---|---|---|---|
| `+0x02B` | u8 | 0 in every record | [C] value; padding by position `[L]` |
| `+0x032` | u16 | 0 in every record | [C] value; padding by position `[L]` |

## Interpretation notes

- `[C]` TC cells use the same encoding as [MonStats](MonStats.md) `TreasureClass*`: the TreasureClassEx
  row + 161 (the runtime TC index; 0 is the empty TC, 1–160 the auto item-type TCs,
  [data/0001 §7](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time)). The 3 blank TC
  rows are `Ancient Barbarian 1..3`, stored as 0.
- `[I]` A superunique's drop TC is this record's `TC` field for the game's difficulty, `+0x2C + 2·diff`;
  when the record is missing the monster's `TreasureClass3` is used instead. A quest TC (`TreasureClass4`)
  can still replace it. `[C]` for Normal and Nightmare by the logged drops (Bishibosh → `Act 1 Super A`
  in Normal, among 317/317 base TCs predicted). (fn:MONSTER_DropItems@0x005A6600, tbl:SuperUniques.txt:TC,
  run:2026-10-11-tc-drops; [items/0001 §3](../findings/items/0001-tc-resolution.md#3-monster-tc-selection--monster_dropitems-0x005a6600))
- `[C]` `Name` = `Superunique` in 65 rows; `Nihlathak Boss` has `Name` `Nihlathak`, and the marker row
  has none.

## Generation columns (plan 0018 Phase 0)

`[C]` from `python3 -I tools/mon_survey.py superuniques workspace/merged/data/global/excel`, decoded from the `.bin`
(last line `SURVEY mon_superuniques records=66 mod1_set=62 mod2_set=44 mod3_set=4 mod_gap=0 min_gt_max=0 grp_zero=16
minion1_none=55 autopos=40 eclass=22 stacks=10 replaceable=10 utrans_differ=0 monpreset_named=56`). The survey prints
one line per record (class, mods by MonUMod name, group, flags, the class's MonStats `minion1`, MonPreset count).

- `[C]` **Fixed mods.** Mods fill from `Mod1` with no gap (a set `ModN` always follows a set `ModN−1`). Per record: 0 mods
  on 4 (Ancient Barbarian 1–3, Nihlathak Boss), 1 on 18, 2 on 40, 3 on 4 (Boneash, Ancient Kaa the Soulless, Lord De Seis,
  Vinvear Molech). Mods named: `strong` (19 cells), `fast` 18, `curse` 11, `resist` 12, `fire` 12, `cold` 12, `lightning` 8,
  `spectralhit` 5, `teleport` 3, `manahit` 3, `aura` 3, `stoneskin` 1, and three that have no unique pick weight in
  [MonUMod](MonUMod.md): `rndname` (1, `Mod1` of Megaflow Rectifier), `poisonhit` (23, `Mod1` of Baal Subject 2) and
  `thief` (24, `enabled` 0, `Mod3` of Lord De Seis). No record names a champion mod (`champion`, `ghostly`, …).
- `[C]` **Groups.** `MinGrp` ≤ `MaxGrp` everywhere; the pairs are (0,0) ×16, (2,2) ×7, (3,3) ×6, (4,4) ×8, (5,5) ×12,
  (5,6) ×1 (Frozenstein), (6,6) ×7, (7,7) ×2, (8,8) ×4, (9,9) ×3. Only 11 of the 66 base classes have a MonStats
  `minion1` (e.g. Bishibosh → `fallen1`, Radament → `skeleton4`, Lord De Seis → `doomknight1`). `[I]` A superunique's minions are
  of its class's `minion1`, or of its own class when there is none; a record with `MinGrp` = `MaxGrp` = 0 still costs one
  `RangeB(1)` draw and makes no minion (fn:sub_005A0C00_UniqueMinions@0x005A0C00, [monsters/0003 § 5](../findings/monsters/0003-special-monsters.md#5-minions-and-xfer), [§ 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn)).
- `[C]` **Flags.** `AutoPos` = 1 on 40 records, all classic (rows 0–41) except Rakanishu and Coldworm the Burrower, which
  are 0; every row from 42 on is 0. `EClass` = 1 on 22 of the 24 records after the `Expansion` marker (42–65), all but Baal Subject 1 and 2. `Stacks` = 1 on ten
  records (Siege Boss, Ancient Barbarian 1–3, Nihlathak Boss, Baal Subject
  1–5). `Replaceable` = 1 on ten (Rakanishu, Treehead WoodFist, Griswold, Beetleburst, Dark Elder, Stormtree, Sarina the
  Battlemaid, Dac Farren, Megaflow Rectifier, Sharp Tooth Sayer).
- `[C]` **MonPreset.** 56 of the 66 records are named by a [MonPreset](MonPreset.md) `Place` cell (kind 2). The ten not
  named are The Summoner, Ancient Barbarian 1–3, Nihlathak Boss and Baal Subject 1–5.
- `[I]` **`Stacks` has a reader.** `sub_005A49B0_SuperUniqueSpawn` skips a superunique whose "placed" bit in
  `game+0x1D30` is set **and** whose record `+0x26` is 0 ([monsters/0002 § 7](../findings/monsters/0002-room-population.md#7-wanderers-monspcwalk-presets-and-superuniques));
  `+0x026` is the `Stacks` byte by the layout above (`[C]`). So the ten `Stacks` records can be placed again after the
  first time; the others once per game. (fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0, tbl:SuperUniques.txt:Stacks)

## Spawn path (plan 0018 Phase 1)

`[I]` `sub_005A49B0_SuperUniqueSpawn` builds a superunique from its record; it never calls the random special-mod roll
(fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0, [monsters/0003 § 6](../findings/monsters/0003-special-monsters.md#6-superuniques-superuniquespawn)). In order:

1. `[I]` `Class` (< 0 → nothing), the `Stacks`/placed-bit test, `AutoPos`, then placement; the unit gets the superunique
   id at `MonsterData+0x26`.
2. `[I]` `Mod1`–`Mod3` appended as MonUMod rows (stop at the first 0; `thief` dropped; `aura` kept and its handler run a
   second time after the minions), then `difficulty` extra unique picks (0 / 1 / 2) on the unit seed, never repeating a
   fixed mod. `[C]` for the counts by run:2026-10-13-mon-spawn (2 extra draws in hell, 0 in normal).
3. `[I]` Minions from `MinGrp`/`MaxGrp` as in the column table, then the hard-coded tail keyed by the `+0x08` record index
   (records 6, 10, 26, 27, 29, 36–39, 42–45, 60, 62: Countess, Radament's escort with one `Range(unit.seed, 5)` draw,
   council and seal bosses, Cow King, Siege Boss, Ancient Barbarians, Nihlathak, Baal Subject 2), and finally mod 22
   `questcomplete` on every record.

`[I]` Not read on this path: `hcIdx` (`+0x00`), `EClass`, `Replaceable`, `Utrans*`, `MonSound`
([monsters/0003 § Data touched](../findings/monsters/0003-special-monsters.md#data-touched)). `Name` is read by the client name builder ([§ 8](../findings/monsters/0003-special-monsters.md#8-names-server-seed-client-roll)).

## Open questions

- `[L]` Who reads `EClass`, `Replaceable`, `Utrans*` and `MonSound`, if anything; none is read on the spawn path
  ([monsters/0003 § Data touched](../findings/monsters/0003-special-monsters.md#data-touched)).
- `[L]` Which of `+0x000` and `+0x008` is `hcIdx` and which is the key's row index, and the order of the
  three `Utrans` bytes, cannot be told from the data.
