# SuperUniques (`data/global/excel/superuniques.txt` → `superuniques.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 66 (67 `.txt` rows minus the `Expansion` marker)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `a2f954f2ca3e27353d8895650263928845cf8e9378e41fd4005a1a6b3f27320a`, `.bin` `239ac86c98186a4e0a7f7ab65531658e87e2b780f36387a1a141d545f083e0e1`
> **Doc status:** complete for layout; semantics `[L]` except the TC columns (`[I]`/`[C]`, items/0001)

## Purpose

One row per named "superunique" monster (Bishibosh, Rakanishu, The Countess, … Nihlathak): its base
monster class, its fixed modifiers, group size, colour transform and a treasure class per difficulty.
Read by the drop code for the monster's TC ([items/0001 §3](../findings/items/0001-tc-resolution.md#3-monster-tc-selection--monster_dropitems-0x005a6600));
the spawning side is monster-spawning work (plan 0012 and later). Leads: no lead; derived from data.

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
| `Superunique` | str, 67 distinct, len ≤ 24 | `+0x008` u32 (own row index) | key; the internal name | — | [C] value, [L] which of the two index fields |
| `Name` | str, 66 distinct, len ≤ 24, 1 blank | `+0x002` u16 string index | display-name key in the `.tbl` files ([tbl.md](../formats/tbl.md)) | string tables | [C] |
| `Class` | str, 62 distinct, len ≤ 16, 1 blank | `+0x004` u32 record index | base monster class | `monstats:Id` | [C] |
| `hcIdx` | int 0..65 | `+0x000` u16 | row number | — | [C] value, [L] which of the two index fields |
| `MonSound` | str, 3 distinct, 64 blank | `+0x018` u32 record index, blank 0 | sound set override (`countess`, `smith`, `smithdemon`) | `monsounds:Id` | [C] |
| `Mod1`, `Mod2`, `Mod3` | int 0..30, 0..30, 0..24 | `+0x00C`, `+0x010`, `+0x014` u32 | fixed monster modifiers (`monumod` row indices by the name) | — | [C] |
| `MinGrp`, `MaxGrp` | int 0..9 each | `+0x01C`, `+0x020` u32 | minion group size range | — | [C] |
| `AutoPos` | int 0..1 | `+0x024` u8 | — | — | [C] |
| `EClass` | int 0..1 | `+0x025` u8 | — | — | [C] |
| `Stacks` | int 0..1 | `+0x026` u8 | — | — | [C] |
| `Replaceable` | int 1, 57 blank (set on 10 rows: Rakanishu, Treehead WoodFist, Griswold, …) | `+0x027` u8 | — | — | [C] |
| `Utrans`, `Utrans(N)`, `Utrans(H)` | int 4..38 (31 distinct) | `+0x028`, `+0x029`, `+0x02A` u8 | colour transform per difficulty | — | [C] bytes; [L] which byte is which difficulty (the three are equal in every row) |
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

## Open questions

- `[L]` Everything the spawner reads (`Class`, `Mod*`, `MinGrp`/`MaxGrp`, `AutoPos`, `EClass`, `Stacks`,
  `Replaceable`, `Utrans*`) waits for the monster-spawning findings (plan 0012 and later).
- `[L]` Which of `+0x000` and `+0x008` is `hcIdx` and which is the key's row index, and the order of the
  three `Utrans` bytes, cannot be told from the data.
