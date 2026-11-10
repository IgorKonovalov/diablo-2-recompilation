# Arena (`data/global/excel/Arena.txt` → `arena.bin`)

> **Source archive:** `.txt` d2exp, `.bin` d2exp   **Rows:** 1 `.bin` records (= `.txt` data rows)   **Record:** 28 B
> **sha256:** `.txt` `b16b41a899b7bc452d18770f798ede17f1801d475b6ba0962de5dcc7ce44d3ae`, `.bin` `f42a9864f70f01559d37ce2cde529ef56660c510d530b8a666094d2484a58e0b`
> **Doc status:** complete for columns and layout (plan 0068 Phase 1); cut content, readers not followed (plan 0062 owns the arena)

## Purpose

One row, `Deathmatch`: seven signed integers named for arena scoring: `Suicide`, `PlayerKill`, `PlayerKillPercent`, `MonsterKill`, `PlayerDeath`, `PlayerDeathPercent`, `MonsterDeath`. Arena is cut content in the shipped game (plan 0062); the table is loaded (call site `0x00664A98`, record 28, not `-txt`-only, [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)). Leads: none.

## Row identity

- `[C]` One row, one 28-byte record; no key besides its position. No `Expansion` row.

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Arena` | str, 1 distinct, len <= 10, 0 blank (`Deathmatch`) | not compiled | row name `Deathmatch`; not in the record | — | [C] shape |
| `Suicide` | int, -6..-6, 1 distinct, 0 blank | +0x000 s32 | by name the score for a suicide `[L]` | — | [C] layout, [L] meaning |
| `PlayerKill` | int, 2..2, 1 distinct, 0 blank | +0x004 s32 | by name the score for killing a player `[L]` | — | [C] layout, [L] meaning |
| `PlayerKillPercent` | int, 10..10, 1 distinct, 0 blank | +0x008 s32 | by name a percentage attached to a player kill `[L]` | — | [C] layout, [L] meaning |
| `MonsterKill` | int, 1..1, 1 distinct, 0 blank | +0x00C s32 | by name the score for killing a monster `[L]` | — | [C] layout, [L] meaning |
| `PlayerDeath` | int, -2..-2, 1 distinct, 0 blank | +0x010 s32 | by name the score for dying to a player `[L]` | — | [C] layout, [L] meaning |
| `PlayerDeathPercent` | int, -10..-10, 1 distinct, 0 blank | +0x014 s32 | by name a percentage attached to a player death `[L]` | — | [C] layout, [L] meaning |
| `MonsterDeath` | int, -1..-1, 1 distinct, 0 blank | +0x018 s32 | by name the score for dying to a monster `[L]` | — | [C] layout, [L] meaning |

## Interpretation notes

- `[C]` Layout: seven `s32` in column order (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel arena`, 7 of 7 cells). The stock values are -6, 2, 10, 1, -2, -10, -1.
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- `[L]` Every reader and the meaning of the two percentage columns: plan 0068 Phase 2 item 3 (the arena is out of the research core).

