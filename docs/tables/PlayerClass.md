# PlayerClass (`data/global/excel/PlayerClass.txt` → `playerclass.bin`)

> **Source archive:** `.txt` d2exp, `.bin` d2exp   **Rows:** 7 `.bin` records (= `.txt` data rows)   **Record:** 4 B
> **sha256:** `.txt` `0742f53a9ad6ef13937ed4bc0ec6ed6de314c8286579601fa38c3b747bf515e5`, `.bin` `ff300cf0227425544b919b926f032aa8ad92e82e66bc9972594a694ceb21e1cc`
> **Doc status:** complete for columns and layout (plan 0068 Phase 1)

## Purpose

The seven player classes in class order: Amazon `ama`, Sorceress `sor`, Necromancer `nec`, Paladin `pal`, Barbarian `bar`, Druid `dru`, Assassin `ass`; one `Expansion` marker row sits between Barbarian and Druid. Tables that name a class by its code store the row index: [ItemTypes](ItemTypes.md) `Class` and `StaffMods`, [CharTemplate](CharTemplate.md) `Class`, `magicprefix` `classspecific`, `magicsuffix` `class`, [Skills](Skills.md) `charclass`. [CharStats](CharStats.md) lists the same codes. Leads: none.

## Row identity

- `[C]` Rows are addressed by **row index**: 0 Amazon .. 6 Assassin, in the order above. The `Expansion` marker row takes no index: the `.bin` has 7 records for 8 `.txt` rows ([excel-bin.md](../formats/excel-bin.md)), so Druid is index 5 and Assassin 6, as in the d2s class byte (`tools/d2s.py` class list).
- `[I]` The `.bin` is read only under `-txt`: call site `0x00612833` is in `DATATBLS_LoadCodeLists` ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300), [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Player Class` | str, 7 distinct, len <= 11, 0 blank | not compiled | editor name of the class; not in the record | — | [C] shape |
| `Code` | str, 7 distinct, len <= 3, 0 blank | +0x000 4-char code | 3-letter code, stored as a 4-character space-padded code | read by ItemTypes `Class`, `StaffMods`; CharTemplate `Class`; magicprefix `classspecific`; magicsuffix `class`; Skills `charclass` | [C] |

## Interpretation notes

- `[C]` Layout: the 4-character code (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel playerclass`, 7 of 7 cells). The `Expansion` row (first field `Expansion`, no code) has no record.
- `[C]` Foreign keys: the columns named above hold only these 7 codes (set inclusion over every row of each table, in this phase); `chartemplate:Class` uses 5 of them (the classic five).
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- None for the data. The player-creation and save specs use the class index; their anchors are in [player/0001](../findings/player/0001-creation.md).

