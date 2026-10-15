# Experience (`data/global/excel/experience.txt` → `experience.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 101 (no `Expansion` marker)   **Record:** 32 B
> **sha256:** `.txt` `a6f0f717bfdf4ab36ac2b55d5aa67b9a6e04d32c650facffbfcb00ed7e505c6d`, `.bin` `2cffe98258e40e45ed241747d5f4801f16904058302269378495f4cdc98e0e5d`
> **Doc status:** layout complete (plan 0034 Phase 0); semantics `[L]` except the save reader's `nextexp` use

## Purpose

The player experience table: a level cap per class, one experience value per level and class, and a per-level
`ExpRatio`. Readers: `player/creation` (plan 0034: experience to level, the level-up) and the save reader, which sets
`nextexp` (stat 30) from it ([save/0001](../findings/save/0001-d2s-io.md)). Mercenary levels come from
the Hireling table's `Exp/Lvl` (plan 0033), not from here. Leads: none registered.

## Form

`[C]` A compiled table like the others, not a `.txt`-only one: `experience.bin` ships next to `experience.txt` (both
patch_d2) and is loaded with 32-byte records
([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables),
`0x00613E41`), with no `-txt` marker. The plan's context said `experience` was not in the loader list; it is.

## Row identity

- `[C]` The `.bin` is a u32 record count (101) and 101 records of 32 bytes, the `.txt` rows in order
  ([excel-bin.md](../formats/excel-bin.md)). The `Level` column is not compiled: a record is found by its index.
- `[C]` Record 0 is the `.txt` row labelled `MaxLvl`; record L + 1 is the row labelled L (L = 0..99).
- `[L]` The row labelled L holds the experience at which level L + 1 begins (labels 1, 2, 3 hold 500, 1 500, 3 750),
  so the threshold of level N is record N. The only code anchor so far is the save reader's
  "`nextexp` = experience table at level + 1" ([save/0001](../findings/save/0001-d2s-io.md), `[I]`), which does not say
  whether the getter adds the `MaxLvl` record's offset.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel experience`: 101 records × 8
mapped fields = 808 cells, **0 mismatches**; no byte is left unmapped. Observed values are computed over the 101
`.txt` rows (`python3 -I tools/player_survey.py xp …`).

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Level` | `MaxLvl`, then 0..99 | — (not compiled) | row label | — | [C] |
| `Amazon`, `Sorceress`, `Necromancer`, `Paladin`, `Barbarian`, `Druid`, `Assassin` | int 0..3 837 739 017; record 0: 99 | `+0x000 + 4k` u32, k = 0..6 in `.txt` order | record 0: the class's level cap; else the experience value of the row `[L]` | — | [C] bytes; slot order by `.txt` order (notes) |
| `ExpRatio` | int: record 0: 10; labels 0–69: 1024; 70–99: 976 … 5 (30 distinct, falling) | `+0x01C` u32 | `[L]` (by name, an experience gain factor in 1/1024) | — | [C] |

## Interpretation notes

- **The seven class columns are identical** in every record (`player_survey.py summary`: `xp_class_cols_equal=100`
  of 100 level records, and the `MaxLvl` row is 99 for every class). So the data cannot say which slot is which class;
  the layout follows the `.txt` order, which is also the CharStats record order. `[L]`
- **Strictly increasing**: every class column grows from label 0 (0) to label 99 (3 837 739 017)
  (`xp_strictly_increasing=1`). `[C]`
- **u32, not s32.** Labels 93–99 hold values above 2³¹ − 1 (2 286 478 756 at label 93); the bytes are the values as
  unsigned. The save's experience stat (13) is 32 bits ([d2s.md](../formats/d2s.md)). How the game compares them
  (signed or unsigned) is for Phase 1. `[C]` bytes
- **The cap and the last row.** With a cap of 99, the row labelled 98 (3 520 485 254) is the threshold of level 99
  and the row labelled 99 (3 837 739 017) has no level to start; whether the game clamps experience to it is `[L]`.
- **`ExpRatio`** is 1024 for labels 0–69, then 976, 928, … (−48 a level to 256 at label 85), then 192, 144, 108, 81,
  61, 46, 35, 26, 20, 15, 11, 8, 6, 5 (`player_survey.py xp`, 31 runs). The `MaxLvl` row holds 10. How it is
  applied, and to which level (the row's label or label + 1), is `[L]`.

## Open questions

- `[L]` The level lookup (which record for which level, signed or unsigned compare, the cap), the `ExpRatio` use and
  the `MaxLvl` row's `ExpRatio` 10; reverser, plan 0034 Phase 1 ([backlog](../backlog.md)).
