# 0001 — Bootstrap: extract, inventory, load the binary, first spec (RNG)

> **Status:** active
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

- **2026-10-11 — Phase 1 done (architect check).** All done-when commands run:
  innoextract 1.9, `/opt/ghidra/support/analyzeHeadless` (ghidra 12.1.2, OpenJDK 21.0.12),
  radare2 6.2.0, smpq 1.7 / stormlib 9.40, wine 11.17 (i386-windows DLLs present). rizin is not
  installed; r2 covers the same role per ADR-0001. `innoextract --info` reads the 1.14d installer (Inno
  5.5.6, not passworded, Russian-only setup) and `--list` shows plain entries under `app/`
  including `game.exe` (3.45 MiB) and the full MPQ set, so Phase 2 should take the innoextract
  route without needing wine.
- **Phase 2 caution (archivist):** the install bundles third-party mods next to the game:
  PlugY (`PlugY.dll/.exe`, `PlugY/`), SGD2FreeRes (`.dll/.mpq/.json`), d2gl (`d2gl.mpq`) and
  `ddraw.dll`/`glide3x.dll` wrappers. Inventory them but tag them `third-party` and **never**
  merge their MPQs into `workspace/merged/` (only `d2data`, `d2exp`, `patch_D2` and the other
  Blizzard archives). Before pinning `game.exe`, check it is the unmodified 1.14d build: PE
  timestamp, version resource (1.14.3.71), and whether any hash cited by community sources
  matches (record that as `[L]` with a `src:` entry). If it looks patched, stop and raise it
  in `docs/backlog.md` for the architect. The setup language is Russian, so diff the string
  tables (`*.tbl`) separately; that does not affect excel data, but note it.
- **2026-10-11 — Phase 2 done (archivist).** innoextract route, no wine: plain Inno 5.5.6
  payload, 2114 files in `workspace/install/app/`. `game.exe` **PINNED** at
  `631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf` (PE32 i386, base `0x400000`,
  FileVersion 1.14.3.71). `[C]` unmodified: the Authenticode signature verifies end to end (image
  digest, messageDigest, RSA, chain to DigiCert root, PE checksum) under *Blizzard Entertainment,
  Inc.*, so no community hash was needed. `docs/inventory.md` lists every file in four classes
  (`game` 4, `game-unverified` 13, `third-party` 27, `local-overrides` 2070). New tools:
  `tools/inventory.py`, `tools/pe_info.py`, `tools/pe_authenticode.py`, `tools/mpq_verify.py`.
  Route and install analysis: `docs/formats/installer.md`.
  **Surprises:** (1) no MPQ is signed, and the archives carry a Russian localisation, so MPQ
  content (excel tables included) is unverified. Backlog entry for the
  architect to decide on a clean reference before Phase 3. (2) Loose `data/local/` overrides
  (sfx wavs, videos, `Use` language byte) sit on disk; they hold no excel data.
  (3) `d2.lng` is a stock 1997 resource DLL, not a mod.
- **2026-10-11 — MPQ provenance check (archivist).** Blizzard 1.14b digital installers (D2 + D2LOD,
  Authenticode-valid `Installer.exe`/`Game.exe`) were extracted to `workspace/reference/extracted/`. The 1.14d install's
  `d2data`/`d2exp`/`patch_D2` `data/global/` content is byte-identical to them (about 20,700 files,
  all excel included). Present only in the 1.14d install: Russian `data/local/` files plus one stray
  `excel/TreasureClass.txt` in `patch_D2`, to exclude from `merged/`. Open: 1.14b vs 1.14d
  `patch_d2` content (backlog). New tool `tools/tree_diff.py`. Recommendation for Phase 3: build
  `merged/` from the Blizzard reference archives (`d2data`, `d2exp`, LOD `patch_d2`), which keeps
  out the install's additions entirely. The `data/global/` result is identical either way.
- **2026-10-11 — Installer set consolidated (archivist).** All installers are copied into
  `workspace/reference/installers/{1.14d,1.14b-d2,1.14b-d2lod}/` under neutral names (`setup.exe`,
  `setup-{1,2}.bin`; `innoextract -t` passes on the copy). Reference payloads were moved to
  `workspace/reference/extracted/`. Hashes are in `docs/formats/installer.md`.
