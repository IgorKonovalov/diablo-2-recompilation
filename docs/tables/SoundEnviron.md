# SoundEnviron (`data/global/excel/SoundEnviron.txt`)

> **Source archive:** `.txt` patch_d2   **Rows:** 50 `.txt` data rows
> **sha256:** `.txt` `d69131977215f8d3ac91326ffa708fad24eeddb61efae3965cf4b4d9d41de90c`
> **Doc status:** columns complete (plan 0068 Phase 1); text-read by the client sound code, no table loader; out of scope (sound)

## Purpose

50 sound environments (`ESOUNDENVIRON_NONE`, `ESOUNDENVIRON_TOWN_1`, `ESOUNDENVIRON_TRISTRAM`, ...): a song, day and night ambience and event sounds, material codes and EAX reverb parameters. Shipped as `.txt` only. Sound data, out of scope (research map). Leads: none.

## Row identity

- `[C]` Key column `Handle`: 50 rows, 50 distinct; the `Index` column holds a number per row.
- `[I]` No table loader; `soundenviron.txt` is read as text by the client sound code at `0x00481950` ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300)).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Handle` | str, 50 distinct, len <= 29, 0 blank | none (no `.bin`) | environment handle name | — | [C] shape |
| `Index` | int, 0..49, 50 distinct, 0 blank | none (no `.bin`) | environment number | — | [C] shape, [L] meaning |
| `Song` | int, 0..4684, 28 distinct, 0 blank | none (no `.bin`) | by name a song; the values fall in the `sounds` index range (0..4684 of 0..4698) `[I]` | [Sounds](Sounds.md) `Index` | [I] |
| ambience and events | int, 0..800, 54 distinct, 0 blank | none (no `.bin`) | ambient and event sounds, event delay, indoor flag, material codes `[L]` | — | [C] shape, [L] meaning |
| EAX parameters | int, -10000..100000, 86 distinct, 0 blank | none (no `.bin`) | reverb parameters named for the EAX audio API `[L]` | — | [C] shape, [L] meaning |

## Interpretation notes

- The record count is checked by the full-tier `excel` survey (the `.txt` data row count; there is no `.bin`, so no layout) (`python3 -I tools/gate.py --full`).

## Open questions

- None; sound is out of scope.

