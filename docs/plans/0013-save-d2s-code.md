# 0013 — Save files: the code behind the `.d2s` format

> **Status:** approved (2026-10-11)
> **Created:** 2026-10-11
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments

## TL;DR

**Question:** which code writes and reads a `.d2s` save, and what in-memory state does each field come from and go
back to? [d2s.md](../formats/d2s.md) documents the bytes (`[C]` by 23 samples and a load test) but cites no code, so
every behaviour seen in the runs (checksum enforcement, the header level rewrite, `map_seed` reuse) is `[L]`. This plan
anchors the writer, the reader and the item bitstream in `Game.exe`, settles the backlog D2S (a)–(c) and (f), and maps
each persisted item field to the runtime item. When it's done, `docs/findings/save/0001-d2s-io.md` exists,
`d2s.md` cites code, and `docs/specs/save/d2s.md` is drafted for the container, header and the item common part. The
payoff for the core rows is a second evidence source: a saved item's seed, quality and ilvl become checkable against a
logged drop, which the `items/*` plans can use for their `[C]`s.

## Context

- Research-map row `save/d2s` (enabler), status `not started`; the map lists `items/properties` as its dependency.
  This plan therefore stops at the property-list *framing* (stat id, save bits, save add, from `ItemStatCost`) and
  leaves what each property means to `items/properties`. The row stays `draft spec` until that row lands.
- Format prerequisite done: plan 0005 Phase 4, accepted with fixes; `tools/d2s.py` parses and edits saves
  (`setstat`, `setwp`), 23 samples in `workspace/samples/`, a `-direct -txt` game directory from `tools/d2s_samples.py`.
- Backlog this plan absorbs: archivist → reverser *D2S fields only the save code can settle* (a) writer/reader,
  checksum, `CSvBits`, item bitstream, `.bin` vs `.txt` save-bit fields; (b) `map_seed` and the unknown header fields;
  (c) item `flags` bits 13 and 23 and the item `version`; (f) the item `seed` and the draw that creates it. (d) runeword
  id and (e) affix/name ids are named here only, for `items/sockets-runewords` and `items/affixes`. Also the reverser →
  archivist load-test entry (`difficulty` after a Nightmare game, max life recomputed on load).
- `rng/seeds` (reviewed) gives the unit seed (step 7); (f) asks whether the saved item seed is that value.
- Leads: `src:d2s-community-format` (version 96 notes) is registered; it covers bytes, not code.

## Phases

### Phase 1 — Anchor the save code
- **Owner skill:** reverser
- **What:** find and read the save writer and reader, the checksum, the bit writer/reader and the item serializer.
- **Outputs:** `docs/findings/save/0001-d2s-io.md`, `re/symbols.csv` rows (subsystem `save/d2s`), struct fields in
  `re/types/` for the player data the header comes from.
- **Done when:** the finding states, with addresses and `[I]` or better:
  - the writer and reader entry points, when each runs (save-and-exit, autosave, character select), and whether the
    reader validates the checksum, the size field and the version, with what happens on mismatch;
  - the checksum routine and the fields zeroed before it is computed;
  - the bit writer/reader (`CSvBits` or equivalent): bit order and width limits;
  - for every header field in `d2s.md`: the runtime field it is written from and read into, including `map_seed`
    (`+0xAB`) and whether a loaded game reuses it as the act map seed (backlog b), `level` (`0x02B`) vs stat 12, and
    `difficulty`/`progression`; the unknown `unk_29`, `unk_2c`, `unk_bf` named or marked unused by the code;
  - the stat stream: which stats are written, how `ItemStatCost` save bits/save add are read (`.bin` vs `.txt`,
    backlog a), and whether life/mana are recomputed on load;
  - the item common part and extended part: the runtime item field behind each bitstream field, item `flags` bits 13
    and 23 and the `version` value (backlog c), and the item `seed` (backlog f): which runtime field, and which draw
    created it on a dropped item (cross-reference `rng/seeds` step 7);
  - the property-list framing; property semantics and the runeword/affix id mappings (backlog d, e) named for their
    rows.

### Phase 2 — Round trips at run time
- **Owner skill:** reverser
- **What:** confirm Phase 1 by making the game write and read saves under gdb, per ADR-0003.
- **Logging:** a gdb script `tools/gdb/d2s-io.gdb` logging the checksum in and out, the header fields at write and
  after read, and, per item serialised, its runtime seed, quality, ilvl and the bit position where it starts.
- **Done when:** a run `run:YYYY-MM-DD-d2s-io` shows, with the logs and the saves hashed:
  - a save written by the game whose every header field and every item common-part field equals the logged runtime
    value, parsed by `tools/d2s.py`;
  - a save edited by `tools/d2s.py` (one stat, one header field) loaded and re-saved, with the logged reads matching;
  - a save with a wrong checksum, and one with a wrong size field: the logged reader behaviour;
  - a `-seed N` game: `map_seed` written, then a reload, with the act seed logged (backlog b);
  - one item picked up from a logged drop (plan 0004 harness, `tc-drops.gdb`) and saved: the saved seed, quality and
    ilvl equal the drop's logged values (backlog f).
  In-scope `d2s.md` lines are raised from `[L]` and given code anchors; the D2S backlog entries are struck through or
  narrowed to (d)/(e).

### Phase 3 — Spec: save/d2s
- **Owner skill:** spec-writer
- **What:** write `docs/specs/save/README.md` and `docs/specs/save/d2s.md`: write and read order, checksum, header
  semantics, the item bitstream as a function of the runtime item, the property-list framing.
- **Done when:** the spec follows the template, every statement is tagged, property semantics are listed under *Open
  questions* pointing at `items/properties`, and the architect's review passes.

## Open questions

- Is the multiplayer (Battle.net-style) character format in scope? No: ADR-0002 defers network; only single-player
  and TCP/IP local saves.
- Does the reader repair or reject inconsistent saves (header level vs stat 12)? Phase 2 records it.
- Shared stash and `.key`/`.ma*` files: not in 1.14d's save directory as far as the samples show; Phase 1 notes any
  other file the writer touches.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-11 — Drafted (architect).** From the open D2S backlog entries after plan 0005 Phase 4; gives the items
  plans a save-side check for their `[C]`s.
- **2026-10-11 — Approved (human).** No changes to the draft.
- **2026-10-12 — Phase 1 done (reverser), for review.** [save/0001](../findings/save/0001-d2s-io.md) anchors the
  writer (`PLRSAVE_Save` → `D2S_WriteSave`, section writers `0x00568F20`–`0x00569A00`), the reader
  (`PLRSAVE_ReadFile` → `D2S_ReadSave` → `D2S_ReadSaveV92`, section readers `0x0056A090`–`0x0056AF80`), the checksum
  (`D2S_Checksum` `0x00411130`), the bit I/O (`BITBUF_*` `0x00410E40`–`0x00411070`) and the item serialiser
  (`ITEMS_Serialize` `0x006313E0`, `ITEMS_WriteFull`/`ITEMS_ReadFull`, compact variants). Static only; everything
  `[I]` except four claims an earlier logged run already confirms (checksum enforcement and algorithm, the select screen
  skipping it, the header level written from stat 12, the right-skill slot `0x07C`), which are `[C]`. Settles backlog
  D2S (a), (b), (c), (f) at `[I]`: map seed reused only in single player without `-seed` and only for the difficulty
  last saved in; `unk_29` = 16 and 30, `unk_2c` a client pass-through, `unk_bf` = one client byte at `0xCF`; flags
  bit 23 forced by the writer, bit 13 cleared on load, item version = `game+0x78` (101 expansion, 2 classic); the
  saved item seed is `unit+0x28` (the game-seed draw of `sub_00552DF0_UnitSeedInit` for a drop). (d) and (e) are named
  (runeword = `Runes` `+0x82` u16; prefix ids rebased on the merged affix array) for their rows. 72 `re/symbols.csv`
  rows (subsystem `save/d2s`), `re/types/save.h` (Client, PlayerData, ItemData, ItemStatCostRec), Game/Unit fields in
  `re/types/game.h`. Corrections to d2s.md (simple items have no `n_filled`; waypoint field 14 bytes; tome bits before
  the runeword field) and its `[L]` lines the code settles went to the archivist through the backlog. Phase 2 cases
  proposed in the finding's *Open questions* and the review entry.
- **2026-10-12 — Phase 1 reviewed (architect): accept.** Checked: gate green; r2 at `D2S_Checksum` 0x00411130 (`setl`
  carry, so `rotl32(sum, 1) + byte`), `D2S_ReadHeader` 0x0056A090 (error 6 checksum, then 5 size, versions 92–96) and
  `PLRSAVE_WriteFile` 0x00532240 (`"%s%s.d2s"`, then `D2S_WriteSave` 0x00569AD0). The four `[C]` (checksum, no check at
  character select, header `level` from stat 12, right-mouse skill at `0x07C`) each cite run:2026-10-11-d2s-edit or the
  tc-drops fifth session as the second source. The lane's question, answered: writer/reader agreement is the same
  binary read twice, so it does not promote a field under rule 1; those fields stay `[I]` until Phase 2. The `.tbl`
  finding [data/0003](../findings/data/0003-string-tables.md) was read in the same lane (backlog, no plan); it is
  accepted as an `[I]` finding, its CRC case joins this plan's Phase 2. Phase 2 cases proposed in the lane's log
  entry are the starting list; `map_seed` reuse needs a run without `-seed`.
- **2026-10-12 — Phase 2 done (reverser), for review.** [run:2026-10-12-d2s-io](../findings/save/experiments.md#run2026-10-12-d2s-io):
  7 harness runs, no owner play, no memory write, no seed used as model input. Logger `tools/gdb/d2s-io.gdb`
  (`d2s-io.py`), checker `python3 -I tools/d2sio.py check`, test characters `tools/d2sio_saves.py`, `.tbl` dirs
  `tools/tbl_crc_case.py`; `tools/d2run.py --game-dir` and `tools/xdrive.py keydown/keyup` added. Results, all logs
  checked with 0 mismatches (1625 comparisons over 8 writes and 7 loads, after review F1): (1) *Save and Exit* writes the file twice,
  byte-identical (`sub_0052CA10_SaveGameClients`, then `sub_0052C900_SaveClients`, both through
  `PLRSAVE_WriteFile`); every header field and item common-part field compared equals its logged runtime source,
  and each saved file is the logged buffer; (2) an edited save (stat 9 = `8000 << 8`, `unk_2c` = `0x0BADF00D`) was
  read as logged and written back twice; (3) bad checksum → `D2S_ReadHeader` 6, bad size (checksum fixed) → 5, both
  mapped to 14, back to the main menu; only these codes were seen; (4) a `-seed 0` game saved its clock map seed and
  the next load reused it (same act seed in both games), with a `-seed 7` control that did not; (5) one Blood Moor
  drop (War Cry, Alt-label pickup), its `unit+0x28`, quality and ilvl at creation = the saved seed, quality, ilvl;
  (6) stat 9 unchanged through `D2S_LoadFinish`, the `8002 / 1072` was maximum / current mana; (7) `.tbl` crc
  checked with the CCITT-FALSE model, a wrong crc halts at start-up ("failed at (206)", crash report; not catchable
  under gdb). Found: item flags bit 13 is **not** "created in this session" (a fresh drop is saved without it); its
  setter is an open question. save/0001 and data/0003 re-tagged with run anchors; 13 `re/symbols.csv` rows to `C`,
  one new (`sub_0052CA10_SaveGameClients`). d2s.md and tbl.md lines go to the archivist through the backlog; backlog
  D2S narrowed to (d), (e) and the bit-13 setter. Not exercised: item `x`/`y`, property lists, mercenary/golem/corpse,
  hotkeys, the other reader codes, a classic game.
- **2026-10-12 — Phase 2 reviewed (architect): accept with fix F1, applied (6e0bf44, ef68191).** Checked:
  `tools/d2sio.py check` reruns on logs 1, 2-badsum, 3-badsize, 4-seed7 and 7-drop with the written saves, 1625
  comparisons, 0 mismatches; no seed taken from a log as input (the drop's `unit+0x28`, quality and ilvl are compared
  with the save, and the seed draw itself rests on rng/0002's `[C]`); r2 at `0x0052CA10` and `0x0052C900` (function
  starts), `0x00525957`–`0x0052596E` (crc compare, `push 0xCE` = 206, fatal call returning to `0x0052596E`); gate
  green. The reader-code `[C]` covers 0, 5, 6 and 14 only; the other codes stay `[I]`. F1: the checker printed but did
  not assert the error path; it now predicts 6/5/0 from the parsed file and asserts the return, the failure exit and
  the mapping to 14. The bit-13 reading refuted by the run is handled right (clear-on-load `[C]`, setter open, backlog).
  Test saves are tool-built copies (ADR-0003 input, recorded); no memory write. The `.tbl` CRC case closes the
  data/0003 item of this plan. Next: Phase 3 (spec-writer, `specs/save/d2s.md`), and the archivist's d2s.md/tbl.md
  re-tags from the backlog.
- **2026-10-12 — Phase 3 done (spec-writer), for review.** [specs/save/d2s](../specs/save/d2s.md) (draft, C 76 /
  I 113 / L 9) and [specs/save/README](../specs/save/README.md) (draft, C 4 / I 1 / L 1): write order and the
  two writes of *Save and Exit*, checksum, reader order and codes, every header field's runtime source and target
  (write and read tagged apart), map-seed reuse, `gf` stats, skills, item lists, the item bitstream from the
  runtime item (common part, simple tail, extended part, quality fields, load-side changes) and the property-list
  framing. `[C]` only where save/0001 has it, with its scope. Worked example from run:2026-10-12-d2s-io case 5
  (save3: header from the logged values, checksum trace, the dropped staff bit by bit), reproduced by
  `tools/d2s.py checksum`/`dump` and `tools/d2sio.py check` (664 comparisons, 0 mismatches). 9 open questions:
  property semantics → `items/properties`; runeword (d) and affix ids (e) named for their rows; framing details,
  `has_class`, ground positions, ear position and the bit-13 record discrepancy → backlog to the reverser.
  Glossary: `.d2s`, simple item, property list. Research-map status change for the architect: `save/d2s` →
  `draft spec`.
- **2026-10-12 — Phase 3 review fixes F1–F3 applied (spec-writer).** F1: the read clamps of `class` (> 7 → 4) and
  of the act (≥ 5 → 0) are a separate `[I]` note; the read destinations stay `[C]`. F2: J1/J2 framing `[C]` by code
  plus data behaviour, scoped to 25 game-written saves (140 extended items, 143 lists, 137 properties, 44 distinct ids,
  groups 17, 48, 50, 54); groups 52/57, other ids, the bound clamp, the shift kind, stat 326 and the version < 93
  paths stay `[I]`. F3: [specs/save/d2s](../specs/save/d2s.md) now C 83 / I 117 / L 9,
  [specs/save/README](../specs/save/README.md) C 5 / I 0 / L 1.
