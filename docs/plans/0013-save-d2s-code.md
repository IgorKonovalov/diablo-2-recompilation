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
