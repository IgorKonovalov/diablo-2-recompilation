# 0005 — Prerequisite formats: DS1, DT1, TBL, D2S

> **Status:** draft
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

- Phase 4 is blocked until plan 0003 Phase 2 can launch the game. Phases 1–3 aren't blocked.
- If a DS1/DT1 field is only explained by code, file a backlog entry to the reverser rather than
  guessing.

## Implementation log

_(lanes append dated entries as phases land)_
