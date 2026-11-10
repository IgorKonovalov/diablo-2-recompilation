# WeaponClass (`data/global/excel/WeaponClass.txt`)

> **Source archive:** `.txt` d2exp   **Rows:** 15 `.txt` data rows
> **sha256:** `.txt` `bc6ba440ab9f9f7589dbd5ea096cea29f834b20085d1e072463e2801a9eacf3b`
> **Doc status:** columns complete (plan 0068 Phase 1); not loaded

## Purpose

A list of 15 weapon animation classes with their codes (`hth`, `1hs`, `1ht`, `2hs`, `2ht`, `stf`, `bow`, `xbw`, ...). Shipped as `.txt` only. [Weapons](Weapons.md) `wclass` and `2handedwclass` hold these codes. Leads: none.

## Row identity

- `[C]` Key column `Weapon Class` (15 rows, first is `None` with a blank code); rows are addressed by position only, since nothing stores an index.
- `[I]` Not loaded by the game: [data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300) lists it among the `.txt`-only tables with no loader (data/excel B1), and the table is shipped anyway. The absence of a loader is a statement about `Game.exe`, so a stock run reads nothing from this file.

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Weapon Class` | str, 15 distinct, len <= 23, 0 blank | none (no `.bin`) | editor name | — | [C] shape |
| `Code` | str, 14 distinct, len <= 3, 1 blank | none (no `.bin`) | weapon class code | values equal Weapons `wclass` (7 distinct), `2handedwclass` (8 distinct): set inclusion over every row | [C] data; [I] not read |

## Interpretation notes

- The record count is checked by the full-tier `excel` survey (the `.txt` data row count; there is no `.bin`, so no layout) (`python3 -I tools/gate.py --full`).

## Open questions

- None.

