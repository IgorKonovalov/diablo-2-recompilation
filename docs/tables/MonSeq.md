# MonSeq (`data/global/excel/monseq.txt` → `monseq.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 1 010 (no `Expansion` marker)   **Record:** 6 B
> **sha256:** `.txt` `5a042af5d3411ed337c71b014125ceae608a7b8f76c7ab437539553e14bc6992`, `.bin` `09fae7cb918e426b46f2fbb62c80883b509ecdda9c5f63a89edc3b4a1919e277`
> **Doc status:** layout complete (plan 0050 Phase 0, every byte placed); meanings `[L]`

## Purpose

The monster **animation sequences**: each sequence is a run of rows with the same `sequence` name, one row per step,
and each step names a [MonMode](MonMode.md) mode, a frame of that mode's animation and an event code. A monster whose
[MonStats](MonStats.md) `Sk<k>mode` cell names a `seq_*` value uses that sequence for its skill `k`; the cell stores
mode 14 (`xx`, `sequence`) and the sequence's ordinal ([MonStats § Columns](MonStats.md#columns)). Readers expected:
`anim/timing` (plan 0050 Phase 1.1: the monster sequence mode, `sub_005A8670_MonSeqFrame` and `Unit+0x4E`,
[skills/0001 § 5](../findings/skills/0001-dispatch.md#5-the-frame-when-the-do-function-runs)). Leads: no lead;
derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (1 010) and 1 010 records of 6 bytes, one per `.txt` row in order; the count
  equals the 1 010 `.txt` data rows. `[I]` The stock loader reads it with record size 6 (call site `0x00659D24`,
  [data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables)).
- `[C]` **60 sequences**, each one contiguous run of rows (the 60 distinct `sequence` values form 60 runs; no name comes
  back after another). Row 0 has a blank `sequence` (mode `NU`, frame 0) and is sequence ordinal 0. The other 59 are
  `seq_pinheadsmite` (ordinal 1) … `seq_crlancerjab` (ordinal 59), in row order.
- `[C]` **The stored sequence number is the ordinal of the name among the distinct values**, the same index MonStats
  `Sk<k>seq` (`+0x188 + 2k`) stores: the layout's `distinct=True` reference gives 0 mismatches over the 1 010 records,
  and a repeated name stores its first occurrence's ordinal ([data/0004](../findings/data/0004-cell-converters.md)).
  (tbl:monseq.txt:sequence, tbl:MonStats.txt:Sk1mode)

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel monseq`: 1 010 records × 5 mapped
fields = **5 050 cells, 0 mismatches**; `excel_bin.py unknown … monseq` lists no uncovered byte. Values from the
`.bin`; blanks from the `.txt`.

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `sequence` | str, 60 distinct (1 blank row), len ≤ 21 | `+0x000` u16, ordinal among distinct names, 0..59 | sequence the row belongs to | key of MonStats `Sk<k>mode` (`seq_*`) | [C] |
| `mode` | str, 10 distinct: `S1` 289, `A1` 200, `A2` 186, `DT` 97, `SC` 92, `S2` 57, `WL` 46, `RN` 33, `S4` 9, `NU` 1; 0 blank | `+0x002` u8, MonMode row | the mode whose animation the step plays | `monmode:code` | [C] |
| `frame` | int 0..30, 0 blank | `+0x003` u8 | the frame of that mode's animation shown at this step | — | [C] |
| `dir` | blank in all 1 010 rows | `+0x004` u8, 0 in every record | direction (by the name) | — | [C] value; the slot is the one left between `frame` and `event` |
| `event` | int {1: 118, 2: 24, 3: 4, 4: 14}, 850 blank | `+0x005` u8, blank → 0 | event code of the step | — | [C] |
| `eol` | int 0 (all) | — (not compiled) | end-of-line marker | — | [C] (absence) |

- `[C]` `dir` is blank everywhere, so its byte is 0 in every record and the data cannot place it except by elimination:
  `frame` and `event` diff at `+0x003` and `+0x005`, and `+0x004` is the only byte left.
- `[C]` `event` 4 appears only here: `animdata.d2` event bytes take the values 1, 2 and 3
  ([animdata](../formats/animdata.md#event-bytes)).

## Sequences

`[C]` per sequence (`python3 -I tools/anim_survey.py monseq workspace/merged`): rows, the modes in step order with
their frames, the steps with an event, and the MonStats rows whose `Sk<k>mode` names it. A few rows to show the shape
(all 60 are in the tool's output):

| Ordinal | `sequence` | Rows | Modes and frames (step order) | Event steps (`step=mode frame:event`) | MonStats rows naming it |
|---:|---|---:|---|---|---:|
| 1 | `seq_pinheadsmite` | 15 | `A1` 0..14 | `#8=A1 8:1` | 7 |
| 2 | `seq_serpentcharge` | 14 | `WL` 0,2,4…14, `A2` 3..11 (not every frame) | `WL` 0, 2 … 14 `:1`, `#9=A2 7:1` | 10 |
| 8 | `seq_skeletonraise` | 11 | `DT` 10..0 (backwards) | — | 41 |
| 16 | `seq_andarielspray` | 18 | `SC` 0..17 | `SC` 4..12 `:2` (nine steps) | 2 |
| 28 | `seq_diablorun` | 22 | `RN` 0..21 | `RN` 5..13 `:2`, `#18=RN 18:1` | 3 |
| 39 | `seq_queendeath` | 54 | `DT`, frames 0..30 with repeats | `#22`, `#38`, `#53` `:1` | 5 |

- `[C]` **Counts.** 160 event steps in 60 sequences (event 1: 118, 2: 24, 3: 4, 4: 14). 54 sequences are named by
  319 MonStats `Sk<k>mode` cells; six by none (`(blank)`, `seq_summonerskill`, `seq_diablofirewall`,
  `seq_tightspotguard`, `seq_swdragonbreath`, `seq_wakeofinferno`).
- `[C]` **A sequence is not always the animation in order.** 23 sequences play a mode's frames in another order: backwards
  (`seq_skeletonraise`, `seq_fethisraise`, `seq_maggotdown`, `seq_tentaclesubmerge`, `seq_tentheadsubmerge`,
  `seq_diablofirewall`), skipping (`seq_serpentcharge`), holding (`seq_maggotlay` shows frame 11 for most steps,
  `seq_siegebeastcharge` shows each `WL` frame twice) or repeating. 8 chain two modes: `WL` then `A2` (3), `A1` then
  `A2` (2), `RN` then `A2`, `A2` then `S4`, `SC` then `A1`.
- `[C]` **Frames against the user's animation.** For each MonStats row naming a sequence, each step's mode was joined
  with the row's `animdata.d2` record (Code + mode token + `BaseW`, else `HTH`; the join rule is
  [MonStats § Timing](MonStats.md#timing-plan-0050-phase-0)): 5 408 steps checked, every one has a record, and 249 name a frame
  at or past the record's frame count: `flyingscimitar` (`ST`, `seq_pinheadsmite`, frames 12..14 of a 12-frame `A1`),
  the six `overseer` rows (`OS`, `seq_genericspawner`, `S1` frames 16..21 of 16), and `shadowwarrior`/`shadowmaster`
  (`K9`, four sequences, against 2-frame `K9` records). Survey keys `seq_user_frames_checked`, `seq_user_frame_past_record`.
- `[C]` **The step's event against the record's event byte at the same frame** (the 5 159 steps within the record):
  both set and equal 81, both 0 4 354, only the step set 559, only the record set 153, both set and different 12. So
  a sequence's events are mostly its own, not a copy of the animation's (keys `seq_ev_*`).

## Interpretation notes

- `[L]` A sequence is the frame list a monster in mode 14 steps through, one row per frame tick, showing the named mode's
  frame; `event` marks the steps where something happens. `[I]` `sub_005A8670_MonSeqFrame` runs the do function when
  `Unit+0x4E` is 4, or when no move-first do ran, `Unit+0xC4` bit 6 is clear and `Unit+0x4E` is 1 or 2
  ([skills/0001 § 5](../findings/skills/0001-dispatch.md#5-the-frame-when-the-do-function-runs),
  fn:sub_005A8670_MonSeqFrame@0x005A8670). That `Unit+0x4E` holds this table's `event` of the current step is
  `[L]`: the values 1, 2 and 4 agree, and no finding reads where `+0x4E` comes from. Plan 0050 Phase 1.1.
- `[L]` By the names, `seq_*` sequences of a monster skill: the `Skills` rows with `monanim` `xx` (214, [Skills § Timing](Skills.md#timing-plan-0050-phase-0)) are the
  skills a monster plays as a sequence; which sequence is the MonStats cell's, not the Skills row's.

## Open questions

- `[L]` Whether `Unit+0x4E` is the current step's `event`, how a step advances (one per frame, or at the animation's
  rate), what the game does with a frame at or past the record's frame count (the 249 steps above) and with `dir`.
  Plan 0050 Phase 1.1.
- `[L]` What events 3 and 4 do. Event 4 is set once in each of 14 sequences (`seq_summonerskill`, `seq_maggotegg`,
  `seq_maggotup`, `seq_swarmmove`, `seq_nestlay`, `seq_bloodravencast`, `seq_gargoyletrap`, `seq_desertturret`,
  `seq_arcanetower`, `seq_tightspotguard`, `seq_mummyspawn`, `seq_genericspawner`, `seq_impinferno`,
  `seq_baalinferno`). Plan 0050 Phase 1.1.
