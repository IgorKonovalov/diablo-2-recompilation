# Events (`data/global/excel/events.txt` → `events.bin`)

> **Source archive:** `.txt` patch_d2, `.bin` patch_d2   **Rows:** 13 `.bin` records (= `.txt` data rows)   **Record:** 2 B
> **sha256:** `.txt` `c438f847029dfc5d80e2184bb96684bf226bcc5a42ef86904eff7f6265a7572c`, `.bin` `a5752635f978bbbabfe4563c569dda4efabc5d2e4eb3b6b551f9692382cfabca`
> **Doc status:** complete for columns and layout (plan 0068 Phase 1); the event dispatch is in the skills findings

## Purpose

The 13 event names that item stats and aura skills attach handlers to: `hitbymissile`, `damagedinmelee`, `damagedbymissile`, `attackedinmelee`, `doactive`, `domeleedamage`, `domissiledamage`, `domeleeattack`, `domissileattack`, `kill`, `killed`, `absorbdamage`, `levelup`. The only references are [ItemStatCost](ItemStatCost.md) `itemevent1`/`itemevent2` and [Skills](Skills.md) `auraevent1..3`, which store the row index. Leads: none.

## Row identity

- `[C]` Key column `event`, 13 distinct, none blank; rows are addressed by **row index** 0..12 in file order. No `Expansion` row.
- `[C]` The `.bin` record is the row index itself (`u16`): record `i` holds `i` (`python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel events`, 13 of 13).
- `[C]` The `.bin` is read only under `-txt`: call site `0x00612E8E` is in `DATATBLS_LoadCodeLists`, skipped unless `-txt` ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300), [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)); no `DATATBLS_LoadTable` call names it in the four stock-mode runs of [data/0001 § Plan 0038 batch H3b](../findings/data/0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load) (run:2026-10-27-sweep-data-load).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `event` | str, 13 distinct, len <= 16, 0 blank | +0x000 u16 row index into `events:event` | the event name; the key of the references | read by ItemStatCost `itemevent1`, `itemevent2`; Skills `auraevent1`, `auraevent2`, `auraevent3` | [C] |
| `*desc` | str, 13 distinct, len <= 21, 0 blank | not compiled | editor description of the event; not in the record | — | [C] shape |

## Interpretation notes

- `[C]` Foreign keys: `itemstatcost:itemevent1` (6 named values), `itemevent2` (3) and `skills:auraevent1` (5), `auraevent2` (2) are subsets of the 13 names (set inclusion over every row, in this phase).
- What a handler does when its event fires is in [skills/0003](../findings/skills/0003-handlers.md) and the dispatch spec, not here.
- `[I]` Readers (plan 0068 Phase 2, from [data/0006 § 2.3](../findings/data/0006-loaded-tables-and-bundles.md#23-events-event-id-012-and-what-is-dispatched)): the event id a table stores is the Events row index. Registration, `sub_0056E740_AddStatEvent` (11 calls): ItemStatCost `itemevent1`/`itemevent2` ids are read as `s16` and registered only when `> 0` (a blank, stored -1, is skipped; id 0 `hitbymissile` would be skipped too, and no stock stat uses it); Skills `auraevent1..3` are registered when `>= 0` (so `hitbymissile` registers, for skill 60 Chilling Armor); the fourth caller, `0x005C377B`, takes its id from a runtime record. Skills `auratgtevent`, `passiveevent` and States `cltevent` are read by none of the 11 calls (the two Skills columns are blank in every stock row). Dispatch, `UNIT_DispatchEvent` (17 call sites, each with a constant id): ids 0, 1, 2, 3, 5, 6, 7, 9, 10, 11, 12 are dispatched, from missile hits, `COMBAT_ApplyDamage`, `COMBAT_BuildDamage`, `COMBAT_DeliverQueued`, `COMBAT_ApplyReductions`, the experience functions and the monster death functions. **Ids 4 (`doactive`) and 8 (`domissileattack`) are never dispatched**, so a handler registered on them never runs: on stock data that is stat 195 `item_skillonattack`'s `itemevent2` (8). Id 13 is dispatched at a monster's death and has no Events row. (the full site table is in the finding)
- The record count is checked by the full-tier surveys: `excel` (`.bin` count against `.txt` data rows) and `excel_layout` (every `.bin` cell against its `.txt` cell, layout in `tools/excel_layouts.py`) (`python3 -I tools/gate.py --full`).

## Open questions

- `[L]` Whether a missile attack reaches event 7's call (`COMBAT_DeliverQueued`), and the id the runtime registrar `0x005C377B` passes: not followed (data/0006, open).
