# 0005 — Prerequisite formats: DS1, DT1, TBL, D2S

> **Status:** in-progress (Phases 1, 2 and 4 accepted with fixes, fixes done; Phase 3 (TBL) next)
> **Created:** 2026-10-11
> **Owner skill(s):** archivist
> **Related ADRs:** 0002-scope-creation-paths-and-enablers

## TL;DR

ADR-0002 lists four formats the core can't close without: DS1 (preset maps) and DT1 (tiles) for
`drlg/*` and `drlg/collision`, TBL (string tables) for unique-monster name rolls, and D2S (saves)
as the `[C]` harness for generated items. This plan documents each one in `docs/formats/` with a
parser in `tools/`, from the files alone. It's archivist work only. The code that *interprets* these
formats is planned with each subsystem. This plan keeps the archivist busy while the reverser
works on plans 0002–0004.

## Context

- Research map § Prerequisite formats: "DS1/DT1 and `d2s` come first". No format doc exists yet
  except `excel-bin` and `mpq`.
- Files are in `workspace/merged/` (`data/global/tiles/**.ds1|.dt1`, `data/local/lng/**.tbl`). There
  are no `.d2s` samples yet: Phase 4 needs saves written by the pinned game under the plan 0003
  harness (a fresh character per class, plus one with a few found items).
- Format claims follow the evidence rules: a field is `[C]` once a parser reads **every** file of
  that type without error *and* the decoded values make sense, or once the reading code is anchored.
- Leads: community format docs are allowed (register each in `docs/sources.md` before use, cite it
  `src:`). Decompiled code is not.

## Phases

### Phase 1 — DS1
- **Owner skill:** archivist
- **What:** Document and parse DS1: header and version variants, layers (walls, floors, shadow,
  substitution), the object and NPC-path lists, and the file and group references.
- **Outputs:** `docs/formats/ds1.md`, `tools/ds1.py`.
- **Done when:** `tools/ds1.py` parses every `.ds1` in `merged/` with no leftover bytes; a version
  histogram is recorded; every field is tagged; and fields with no known meaning are listed as such.
  Every `LvlPrest.txt` `File1..6` that names a DS1 resolves to an existing file (or the misses are
  listed).

### Phase 2 — DT1
- **Owner skill:** archivist
- **What:** Document and parse DT1: the header, tile records (orientation, main and sub index,
  rarity, the sub-tile flags used for collision), and the block headers. Pixel data only to the
  extent needed to skip it.
- **Outputs:** `docs/formats/dt1.md`, `tools/dt1.py`.
- **Done when:** `tools/dt1.py` parses every `.dt1` in `merged/` and accounts for every byte (pixel
  blocks may be skipped by length). The sub-tile flag byte is documented with the value
  distribution observed, and its meaning stays `[L]` until the collision plan anchors it.

### Phase 3 — TBL
- **Owner skill:** archivist
- **What:** Document and parse the `.tbl` string tables: the header, the hash table, and the
  key/value layout, including which tables override which (`string`, `expansionstring`, `patchstring`).
- **Outputs:** `docs/formats/tbl.md`, `tools/tbl.py`.
- **Done when:** `tools/tbl.py` dumps every `.tbl` (each language present) with key/value counts
  equal to the header's; a lookup by key returns the expected string for every
  `uniqueprefix`/`uniquesuffix`/`uniqueappellation` row; and the override order is tagged (`[L]`
  until the reverser anchors it).

### Phase 4 — D2S (header and item list)
- **Owner skill:** archivist
- **What:** From saves the pinned game writes, document the D2S header, checksum, and sections up to
  and including the item list. Decode the item bitstream fields that item specs need: code, ilvl,
  quality, the item seeds, sockets, ethereal, and the quality-specific IDs.
- **Outputs:** `docs/formats/d2s.md`, `tools/d2s.py` (read and re-checksum).
- **Done when:** `tools/d2s.py` reads every sample save; recomputing the checksum matches the
  stored one; an edited save (one changed byte, re-checksummed) loads in the game; and every item in
  the samples decodes to the end of its bitstream with no leftover bits. Property lists may stop at
  "length known" until `items/properties` documents `ItemStatCost` save bits.

## Open questions

- ~~Phase 4 is blocked until plan 0003 Phase 2 can launch the game.~~ Unblocked: the plan 0003 harness writes saves (implementation log, 2026-10-11). Phases 1–3 aren't blocked.
- If a DS1/DT1 field is only explained by code, file a backlog entry to the reverser rather than
  guessing.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-11 — Approved (human).** No phase started yet.
- **2026-10-11 — Phase 1 (DS1) landed (archivist).** [formats/ds1.md](../formats/ds1.md) and
  `tools/ds1.py` (`survey`, `dump`, `lvlprest`). The parser reads **2273 of the 2276** `.ds1` files in
  `merged/` and ends exactly at the last byte of each. The other 3 (`act1/outdoors/swamp2.ds1`,
  `act1/outdoors/trees.ds1`, `expansion/siege/xtransition.ds1`) are malformed in their trailing
  lists. None is referenced by LvlPrest, and `survey` checks that each still fails exactly as recorded
  (exit 0). Version histogram: 3:1 8:6 12:13 13:30 15:13 16:223 17:145 18:1845. The layout is `[C]`
  by data behaviour, with three corroborations from the content:
  - wall cell = 0 ⇔ orientation cell = 0 over all 1.49 M wall/orient pairs, which pins the layer order;
  - the DS1 `size_x`/`size_y` equal LvlPrest `SizeX`/`SizeY` in all 1995 references with a non-zero
    size, which pins the "+1" grid;
  - every NPC path starts on an object (136/136).

  Version thresholds that fall in a gap (4–7, 9–11, 14) stay `[L]` (`src:siramy-ds1edit`, newly
  registered). Cell bit meanings (main/sub index, flag byte), object `type`/`id`, the substitution
  cells and the DT1 list are `[L]` or unknown. Values are listed, backlog → reverser.

  **LvlPrest:** a full layout went into `tools/excel_layouts.py` (432 B, 23 fields, `excel_bin.py diff` 0
  mismatches over 25 093 cells, one unknown u32 at `+0x024`). [tables/LvlPrest.md](../tables/LvlPrest.md)
  is written, since it stayed small. All **2058** `File1..6` references in `lvlprest.bin` resolve to
  existing `.ds1` files, **no misses** (2043 distinct; 233 shipped DS1 are unreferenced). LvlPrest
  semantics are a backlog item for the drlg plans.

  **Surprises:**
  - Every v12/v13 file has an undocumented trailing dword (0), modelled as `unk_trailer`. It may be an
    NPC-path count read from v12.
  - In 81 records, `Files` differs from the number of named files.
  - The DS1 tile-file lists name `.tg1` paths in the build tree, which map to shipped `.dt1` files in
    10 462 of 10 496 cases.

  **Phase 2 hook:** DT1 can corroborate the `[L]` cell index split by checking that every
  (orientation, main, sub) triple names a tile in the DS1's DT1 files.
- **2026-10-11 — Phase 3 (TBL) status note (archivist).** `docs/formats/tbl.md` and `tools/tbl.py`
  already exist from plan 0002 Phase 1, so Phase 3 extends them and does not redo them. What they
  meet today:
  - **header and key/count check:** met for keys. All 20 `.tbl` under `data/local/lng/*/` read without
    error; every entry's index points at a used hash node whose back-pointer is that entry, and
    `file_size` matches. The parser reads keys only, and does not yet read or dump the string *values*.
  - **lookup by key for every `uniqueprefix`/`uniquesuffix`/`uniqueappellation` row:** not met.
    Key → compiled index is done (2278 item and monster cells match), but key → string is not.
  - **override order:** met for the compiled `.bin` indices, `[C]` by data behaviour
    (patchstring → expansionstring → string; 5382 = `dummy` when not found). The run-time order
    stays `[L]` (open in the backlog, `data/strings`).

  Left for Phase 3:
  - read and dump the values;
  - the unique-name lookup check;
  - the hash function, probing and `crc` (optional, `[L]` today).
- **2026-10-11 — Phase 4 (D2S) unblocked.** The plan 0003 harness writes saves under
  `workspace/wineprefix/.../Saved Games/Diablo II/` and can script new characters with
  `tools/xdrive.py` (backlog entry "from reverser → archivist: plan 0005 Phase 4 (D2S) can use the
  harness now"). The open question "Phase 4 is blocked until plan 0003 Phase 2 can launch the game" is
  answered.
- **2026-10-11 — Phase 2 (DT1) landed (archivist).** The human asked for Phase 2 straight after Phase 1,
  so the architect's review covers both. Outputs: [formats/dt1.md](../formats/dt1.md) and `tools/dt1.py`
  (`survey`, `dump`, `ds1keys`).

  **Byte accounting.** 263 `.dt1` files: **257 are version 7.6**, and every byte of them is accounted
  for (16 456 tiles, 361 484 blocks). Header, tile records and per-tile block areas tile each file
  exactly, isometric blocks are always 256 bytes, and every RLE block walks to exactly its length.
  `survey` exits 0. **Six are version 4.1** (`act1` barracks, gargtrap, catacombs, cathedrl, court,
  outdoor1). Only their header and pointer table are decoded. They are the stated exception to
  "every byte": no `LvlTypes` row and no DS1 list names them. LvlTypes' 230 DT1 references all exist
  and are all 7.6.

  **Sub-tile flags.** The flag byte's distribution is documented: bits 0, 1, 2, 4 and 5 occur, and 3,
  6 and 7 never do. The meaning stays `[L]`.

  **DS1 corroboration (the Phase 1 hook).** The key (orientation, cell bits 20–25, bits 8–13) names a
  tile in the DS1's own DT1 list for 100 % of shadow cells, 97.9 % of walls and 93.9 % of floors.
  Swapped or shifted splits score 7–88 % on shadows. So the DS1 index split is now `[C]` by data, and
  ds1.md is updated.

  **Surprises:**
  - Every floor cell with low byte `0x42` (39 303) is the `blank.dt1` tile, which no DS1 lists.
  - DS1 lists name `.tg1` files from the build tree, with some name drift (`caves.tg1` vs the shipped
    `cave.dt1`).
  - `orientation` → `direction` is a fixed mapping.
  - Some tile records carry pointer-like editor leftovers in `+0x58`.

  Backlog → reverser: the sub-tile flag bits and grid order, the tile source (LvlTypes vs the DS1
  list), rarity and animation, and the 4.1 files.
- **2026-10-11 — Review of Phases 1 (DS1) and 2 (DT1) (architect): accept with fixes.** Both phases
  were reviewed together because the human asked for Phase 2 right away. Reproduced: `ds1.py survey`
  and `dt1.py survey` exit 0, and `dt1.py ds1keys` gives the same counts (shadow 15 055/15 055, wall
  169 774, floor 654 186). Commits 393730b, ea20c4e, 38e9c9b, 6589120.

  Rulings:
  - **"Every file / every byte" is met.** The 3 malformed DS1 files and the 6 DT1 v4.1 files are
    acceptable exceptions. Each one is listed with its cause, none of them is reachable through data
    (LvlPrest, LvlTypes, DS1 lists), and `survey` fails if an exception changes. Reopen only if the
    reverser finds a loader path to them (backlog DT1 (d)).
  - **Data-only `[C]`s are allowed for format claims.** The evidence rules' data-format clause allows
    them. A data-only `[C]` describes the **bytes**. It does not cover what the game **does** with them.
    No drlg spec may cite `fmt:ds1`/`fmt:dt1` for a resolution or placement behaviour without its own
    code anchor.
    - Cell index split (bits 20–25 main, 8–13 sub): `[C]` stands. Shadows match 100 %, and every
      other bit split does far worse. The leftover wall and floor misses must be broken down, though:
      2 222 of the 3 637 wall misses are orientation 12, which points to special tiles that are resolved
      elsewhere (fix F2).
    - "+1" grid: `[C]` stands, but the stated reason is wrong. Agreement with LvlPrest only shows that
      `size_x` is the same quantity as `SizeX`. The "+1" comes from byte accounting: `(size+1)²` cells per
      layer is the only reading that ends all 2273 files exactly and keeps the wall/orient zero pairing
      (fix F1).
  - **`src:siramy-ds1edit` from memory is acceptable as a lead.** No tag rests on it alone: every
    layout row was checked against the files, and the gap thresholds stay `[L]`. A reviewer can't check
    a recalled source, though. Re-read it before it is cited for anything that isn't checked by data.
  - **`unk_trailer`** is modelled correctly. Backlog DS1 (b) already asks the reverser about it.
  - **Lane hygiene:** the ADR-0004 file and the plan 0004 edit were architect work, committed in
    eb4e506. Nothing is stranded.

  Fixes (backlog → archivist, not blocking): F1 rewrite the "+1" reason; F2 a per-orientation table of
  DT1 key misses, plus the files holding the 340 cells that match no tile anywhere; F3 tag
  inconsistencies (object `x`/`y` table row says `[C]` for the meaning, the bullet says `[I]`; NPC path
  "belongs to the object" is `[I]`, only the position match is `[C]`); F4 one scope sentence in each of
  ds1.md and dt1.md saying that the `[C]` tags describe the encoding, not game behaviour.

  **Next: Phase 4 (D2S), then Phase 3 (TBL).** This reverses the README's suggested P3 → P4 order:
  - The research map puts `d2s` first. It is the save-inspection corroboration for every item `[C]`
    after `items/tc`, and the plan 0003 harness can now write saves.
  - TBL serves only `monsters/special` name rolls, which are not planned yet. Phase 3 extends the
    existing `tbl.md`/`tbl.py` (status note above) and is small enough to follow.

  `drlg/overview` planning (plan 0006) waits until the reverser is past plan 0004 Phase 2, because a
  plan with no free lane only goes stale. It will take the open LvlPrest-semantics backlog entry and
  backlog DS1 (a)/(c) and DT1 (b)/(c).
- **2026-10-11 — Review fixes F1–F4 done (archivist).** Struck through in the backlog.
  - **F1:** the "+1" grid now rests on byte accounting.
  - **F2:** the per-orientation miss table and the files with no-match cells are in dt1.md, and
    `dt1.py ds1keys` now prints both. Orientation 12 makes up 61 % of wall misses. 1 840 of those are
    the keys (12, 0, 0..2), which ship in many DT1s (`[L]` generic special tiles).
  - **F3:** two tags demoted to `[I]`.
  - **F4:** scope paragraphs added.
- **2026-10-11 — Phase 4 (D2S) landed (archivist).** Outputs: [formats/d2s.md](../formats/d2s.md),
  `tools/d2s.py` (`survey`, `dump`, `checksum`, `setstat`), and `tools/d2s_samples.py`.

  **Samples.** 23 saves written by the pinned game under the plan 0003 harness (in
  `workspace/samples/`, hashes in d2s.md):
  - 2 creation stubs (335 B);
  - 7 fresh characters, one per class, on stock data;
  - 10 item saves from a separate game directory run with `-direct -txt` and two edited tables
    (CharStats: extra starting items; CubeMain: one class-only recipe → three chosen items);
  - 4 edited or re-saved files.

  Across 228 items, the item saves cover every quality (low … crafted), ethereal, sockets, a runeword
  with two socketed runes, stackables and a tome.

  **Done when:**
  - every sample reads: met, `survey` exits 0;
  - the recomputed checksum matches: met, 23/23 (rotate-left-1 and add);
  - an edited save loads: met. Strength 30 → 45 via `setstat` loads and shows 45. A one-byte edit
    without re-checksum is refused ("generic bad file"), and the same bytes re-checksummed load.
    So the refusal is the checksum's (run:2026-10-11-d2s-edit in d2s.md);
  - every item decodes with no leftover bits: met. All 228 items end exactly where the next record
    starts, with 0–7 zero padding bits. **Property lists are fully decoded**, not just "length known":
    `itemstatcost.txt` save bits, and the grouped stats 17, 50, 54 are observed.

  The layout is `[C]` by data plus the load test. Fields no sample exercises stay `[L]`: ears,
  personalized names, class affixes, mercenary/golem/corpse lists, quest bits, stats above id 12.

  **Deviations for the review:**
  - The item samples come from edited tables, which change which items exist, not how they are
    saved. The stock `smp*` saves decode under the same layout.
  - The two run records are in d2s.md § Experiments, not `docs/findings/*/experiments.md`, which is
    the reverser's.
  - `tools/xdrive.py` gained an `rclick` command, needed to open the cube.
  - `src:d2s-community-format` was used from memory, like `siramy-ds1edit`.

  **Surprises:**
  - The game writes a 335-byte header-only stub at character creation.
  - The select screen shows the header level without checking the checksum. The game rewrites that
    level from the stats on save.
  - Stored `maxdur` is the base value. A superior sword stores 44/49, because its +12 % max-durability
    property applies.
  - Cube uniques/sets requested at item level 1 came out rare/magic.
  - The *Steel* runeword is stored as id 159, but it is Runes.txt row 18 (`Runeword134`).

  Backlog → reverser for the code-only questions.
- **2026-10-11 — Review of Phase 4 (D2S) (architect): accept with fixes.** Commits a24f94d (F1–F4 of
  the Phase 1–2 review), 20486d7 (tools), 2ab1bec (docs). Reproduced: `d2s.py survey` over the 23
  saves exits 0 (`saves 23, bad 0`, leftover bytes 0, item pad value 0 = 228). An independent
  rotate-left-1-and-add checksum written for this review matches 23/23 and rejects only the
  deliberately corrupted `d2s-edited/smpsor.d2s`. The F1–F4 fixes to ds1.md/dt1.md are as described,
  and that backlog entry stays struck through. Every *Done when* clause is met, and property lists go
  past "length known".

  Rulings:
  - **Item samples from the `-direct -txt` directory are acceptable evidence for the encoding.** The
    save writer is in the unmodified pinned `Game.exe`. Only CharStats and CubeMain were edited, and
    they choose *which* items exist. The 7 stock-data saves decode under the same layout, which
    corroborates the header, the stat stream and the simple/normal item encoding on stock data. One
    limit follows: under `-txt` the game compiled every table from `.txt`, so the property widths
    observed are the `.txt` ones. Whether stock `itemstatcost.bin` carries the same save columns is a
    data question (fix F4), not a reason to distrust the layout. When plan 0004 Phase 2 yields a
    stock-data save with dropped magic or rare items, run `survey` on it. No new phase is needed.
  - **Run records: they move to a new archivist-owned `docs/formats/experiments.md`** (fix F1). They
    don't belong in `docs/findings/`, which is the reverser's. They don't belong inside d2s.md either,
    because ADR-0003 puts records in an `experiments.md`, and gate rule E3 resolves `run:` anchors only
    there, so the first spec to cite `run:2026-10-11-d2s-edit` would fail. evidence-rules § Anchors,
    § Experiments and E3 now name `docs/formats/experiments.md` as a second home, for runs whose claim
    is a format claim. No ADR change: ADR-0003 says "`experiments.md`" and fixes no directory. The
    records also fall short of ADR-0003's "reproducible from the record alone": no Setup or Conclusion
    in `d2s-samples`, and no exact command lines or steps files for the menu driving.
  - **The `rclick` edit to `tools/xdrive.py` is accepted.** It is additive and backward-compatible (5
    lines). It was disclosed in the log, and the backlog entry asks the reverser to add it to
    tooling.md. In future, a change to a harness tool (`d2run.py`, `xdrive.py`, `tools/gdb/`) goes
    through a backlog entry first, unless it is additive like this one and is disclosed the same way.
  - **`src:d2s-community-format` from memory is acceptable as a lead.** This is the same ruling as
    `siramy-ds1edit`. Every row was checked against the saves, and the only claims that rest on the
    lead alone (grouped stats 48/52/57, alternating rare affix slots, the ear/personalized/class-affix
    branches) are `[L]`. Re-read it before anything unchecked is promoted.
  - **Data-plus-load-test `[C]` for the checksum, the stat stream and the item bitstream stands.**
    It's the data-format clause, as for DS1/DT1, and stronger here: every item's end bit lands on the
    next record, and the game accepted a parser-written save. The same scope limit applies: the tags
    describe bytes. Four statements in d2s.md are **game behaviour**, though, not encoding, and are
    tagged `[C]` on one run with no code anchor (fix F2):
    - the select screen doesn't check the checksum;
    - entering the game refuses a bad checksum;
    - the save rewrites header `level` from stat 12;
    - a requested unique or set above what the item level supports comes out rare or magic.
    The checksum *algorithm* stays `[C]` either way, because it holds over 23 files by data.
  - **ItemStatCost `.txt` vs `.bin` `[I]`:** the caveat is right, but the tag is wrong. `[I]` needs a
    code anchor, and this is an open data check. Fix F4 settles it by data.
  - **The `status` bit 5 = expansion claim is `[L]` in the header table** but serves as the `[C]`
    condition for the `jf`/`kf` trailer (fix F3).
  - **Gate (ADR-0006, plan 0007):** the fast tier landed on `main` during this review (f387831). It
    is green with d2s.md included: 0 errors, and the warnings are all in older findings and specs.
    For a format doc only E2 and E8 apply. E3 is the rule F1 heads off.

  Fixes (backlog → archivist, not blocking):
  - **F1:** create `docs/formats/experiments.md` with both records as `## run:` headings in the
    evidence-rules shape (Question, Setup, Procedure, Observed, Conclusion). Each record needs the exact
    command lines (d2run/wine launch, `d2s_samples.py`, `d2s.py setstat`), the `xdrive` steps file or
    the literal command sequence, and the raw-log path, or a statement that none was kept. d2s.md
    § Experiments becomes a link list. In the same commit, extend gate E3 in `tools/gate.py` to also
    read `docs/formats/experiments.md` (rule text amended), with a fixture.
  - **F2:** re-tag the four behaviour statements above `[L]`, each citing its run, and point them at
    backlog D2S (a). The unique/set downgrade also goes under *Open questions*, as `items/quality`
    material.
  - **F3:** state the trailer as observed `[C]` (all 21 full saves have `status` `0x20` and end with
    `6A 66 6B 66 00`), and the bit 5 condition as `[L]`.
  - **F4:** add the save columns of ItemStatCost (`Save Bits`, `Save Add`, `Save Param Bits`, `CSvBits`,
    `CSvParam`, `CSvSigned`) to `tools/excel_layouts.py` and run `excel_bin.py diff` against
    `itemstatcost.bin`. With 0 mismatches, the d2s.md caveat becomes a `[C]` by data, citing the diff.
    This is a partial layout only: the full `tables/ItemStatCost.md` belongs to `items/properties`.

  **Next for the archivist: the Phase 4 fixes (F1 together with the E3 extension), then plan 0007
  Phase 2 (survey baselines), then Phase 3 (TBL), then the plan 0005 close.** Phase 3 stays in scope,
  because ADR-0002 lists TBL for `monsters/special` name rolls, so the plan can't close without it.
  It still waits, for two reasons:
  - Its only consumer, `monsters/special`, isn't planned.
  - Plan 0007 Phase 2 baselines the `d2s.py` survey accepted here, along with `ds1`/`dt1`/excel, so any
    later parser change shows up as a count diff. That protects more than TBL unlocks.

  Phase 3 then extends the existing `tbl.md`/`tbl.py` (status note above).
- **2026-10-11 — Phase 4 review fixes F1–F4 done (archivist).** F1: run records moved to
  [formats/experiments.md](../formats/experiments.md) (Question/Setup/Procedure/Observed/Conclusion,
  command lines, raw log "none kept"; the click coordinates of the creation and cube screens were not
  recorded and the record says so), d2s.md § Experiments is links, gate E3 reads that file and flags
  duplicate ids (fixture `E3-dup`). F2: the four behaviour statements are `[L]` citing the run; the
  unique/set downgrade is also an open question. F3: `jf`/`kf` trailer `[C]` as observed, bit 5
  condition `[L]`. F4: partial `itemstatcost` layout in `tools/excel_layouts.py`; `excel_bin.py diff`
  shows 0 mismatches over 359 records for `CSvBits`, `Save Bits`, `Save Add` and `Save Param Bits`,
  so the `.txt` vs `.bin` caveats are `[C]` by data (`CSvParam`/`CSvSigned` are all blank or 0 and
  can't be placed). Also: `tools/d2s_samples.py` variants `a`/`b`/`lvl1` reproduce every item sample
  (`b` byte-identical to the `game-mod` tables), and sources.md names the README's JS/Go checksum
  snippets (`d2s.py` not derived from them).
