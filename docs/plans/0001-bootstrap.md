# 0001 — Bootstrap: extract, inventory, load the binary, first spec (RNG)

> **Status:** draft
> **Created:** 2026-10-11
> **Owner skill(s):** human, archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources

## TL;DR

Go from the installer files in `workspace/reference/installers/` to the first spec end to end. Extract the install, hash
and inventory every file, dump the MPQs, load `Game.exe` into a reproducible Ghidra project with
a symbol round-trip, locate the game RNG, and write `docs/specs/rng/`. The RNG comes first
because item, monster and DRLG behaviour all depend on its exact call order.

## Phases

### Phase 1 — Toolchain
- **Owner skill:** human
- **What:** Install `innoextract ghidra radare2 wine jdk21-openjdk` (pacman) and `stormlib smpq` (AUR).
- **Done when:** `innoextract --version`, `/opt/ghidra/support/analyzeHeadless` (or the path pacman installed), `r2 -v`, `smpq --version` and `wine --version` all run.

### Phase 2 — Unpack the installer
- **Owner skill:** archivist
- **What:** Extract the 1.14d installer into `workspace/install/`. Try innoextract first. If the payload
  is wrapped (ISDone/FreeArc/unarc, which innoextract can't open), install it under wine into
  `workspace/wineprefix` and copy the game directory out. Record which route worked in
  `docs/formats/installer.md`.
- **Done when:** `workspace/install/` holds `Game.exe` and the `*.mpq` set, and `docs/inventory.md`
  lists every file with size, sha256 and `file(1)` type. The `Game.exe` sha256 is marked **PINNED**
  there and `file Game.exe` reports a PE32 i386.

### Phase 3 — Dump the MPQs and identify the data tables
- **Owner skill:** archivist
- **What:** Extract every MPQ to `workspace/mpq/<archive>/`, then build `workspace/merged/`
  applying patch precedence. Verify the precedence empirically: find a file present in more than
  one archive and check which version the game uses (doc or wine test). Check whether
  `data/global/excel/` ships `.txt`, `.bin`, or both.
- **Done when:** `docs/formats/mpq.md` documents the archive set, listfile handling and
  precedence, each with a confidence tag. `docs/tables/README.md` lists every excel table found,
  with a row count and the archive it came from. If only `.bin` ships, `docs/formats/excel-bin.md`
  is opened as a stub with what's known.

### Phase 4 — Reproducible Ghidra project and symbol round-trip
- **Owner skill:** reverser
- **What:** Write `re/ghidra_scripts/` (import symbols from CSV, export renamed symbols to CSV,
  decompile a function to stdout) and `tools/ghidra.sh`, a wrapper around `analyzeHeadless`.
  Import and auto-analyse the pinned `Game.exe` into `workspace/ghidra/`.
- **Done when:** Deleting `workspace/ghidra/` and re-running the wrapper rebuilds the project and
  replays `re/symbols.csv`. `tools/ghidra.sh decompile <addr>` prints C for any function, and the
  analysis log is saved to `workspace/logs/`.

### Phase 5 — Locate the RNG and its seed lifecycle
- **Owner skill:** reverser
- **What:** Find the core random function (`[L]`: community docs describe a 64-bit seed
  advanced as `low * 0x6AC690C5 + high`). Find its range helper(s), where seeds are initialised
  (game, level/room, unit, item), and how a seed is derived from parent to child.
- **Done when:** `docs/findings/rng/` has notes with addresses and confidence, `re/symbols.csv` has
  the RNG functions named, and at least the step function is `[C]`, corroborated by e.g. a
  bit-for-bit Python reproduction (`tools/rng.py`) checked against a wine or emulated run.

### Phase 6 — Spec: RNG
- **Owner skill:** spec-writer
- **What:** Write `docs/specs/rng/README.md`: the state, the step, range reduction, the seed tree,
  and every consumer found so far.
- **Done when:** The spec follows the template, every statement is tagged, and the architect's
  review passes.

## Out of scope

Item, monster and DRLG specs. The architect plans them after this plan closes, ordered by the
research map in `docs/specs/README.md`.

## Implementation log

_(lanes append here as phases land)_
