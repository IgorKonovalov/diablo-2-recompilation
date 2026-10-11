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
- **2026-10-11 — Phase 3 done (archivist), one done-when item handed on.** All 12 reference MPQs
  extracted to `workspace/mpq/<name>/` (3.0 GB). `workspace/merged/` was built from d2data → d2exp →
  LoD patch_d2: 20,569 files, 300 overrides logged in `workspace/logs/overrides.txt`, and a per-file
  manifest in `workspace/logs/merged-manifest.tsv`. Neither `patch_d2.mpq` has a listfile. A
  candidate list built from local listfiles (no community listfile) recovers 204/209 (LoD) and
  1137/1146 (classic), and every excel entry is named. **Both `.txt` and `.bin` ship:** 97 tables,
  87 as pairs, 5 txt-only, 5 bin-only (`leveldefs` + four header-less `*code.bin`). `[C]` All 87
  pairs agree on record count once two compiler rules are known: `Expansion` marker rows are
  dropped (30 tables), and tab-only lines become records (the last `uniqueitems` row). Docs:
  `docs/formats/mpq.md`, `docs/formats/excel-bin.md` (stub: count header, CP1252/CRLF text, the
  blank-cell defaults), `docs/tables/README.md` (full catalogue). New tools: `tools/mpq_dump.py`,
  `tools/excel_survey.py`.
  **Not met:** the precedence check "which version does the game use" is still `[L]`. No wine run
  was made, and the order needs a code anchor. The archive-name strings in `Game.exe` are listed
  for the reverser (backlog).
  **Surprises:** (1) five tables mix archives: patch_d2 updated only the `.bin` of `automagic`,
  `RarePrefix` and `RareSuffix`, and only the `.txt` of `inventory` and `PlrMode`. Which form the game
  reads decides which side is authoritative for item affixes (backlog). (2) `TreasureClass.txt` (txt
  only, 707 rows) ships next to `treasureclassex`. Which one is live is in the backlog. (3) `Game.exe`
  names `d2kfixup.mpq` and `d2delta.mpq`, which don't ship. (4) Python's `splitlines()` miscounts
  `objects.txt` (a `0x85` byte in a cell), so parsers must split on LF.
- **2026-10-11 — Phase 4 done (reverser).** `tools/ghidra.sh` wraps `analyzeHeadless` (Ghidra 12.1.2):
  `build`/`rebuild` (checks the PINNED sha256, imports as `x86:LE:32:default`/`windows`, full
  auto-analysis, replays `re/symbols.csv`), `import-symbols`, `export-symbols`, and read-only
  `decompile`, `xrefs`, `findstring`. Scripts in `re/ghidra_scripts/`: `ImportSymbols`, `ExportSymbols`,
  `Decompile`, `Xrefs`, `FindString` (Java). A build takes **~3 min 40 s** (16 cores, 8 GB heap), and
  each query ~10 s. Logs: `workspace/logs/ghidra-build-<UTC>.log` and `ghidra-last.log`.
  **Done-when checked:** `rebuild` (deleting `workspace/ghidra/`) with a 2-row test CSV (a function with
  a `__thiscall` signature, plus a data label) replays it, and `export-symbols` afterwards writes a
  byte-identical CSV. CSV → project → CSV is a fixed point after one pass. `decompile` prints C by address or
  name, with the `[tag] subsystem evidence` plate comment. The project was then rebuilt clean from the
  real (empty) `re/symbols.csv`.
  **Gotchas, built into the tools:** (1) Ghidra 12.1 writes script output *and script errors* to `-log`,
  `-scriptlog` stays empty, and a failing script does **not** make `analyzeHeadless` exit non-zero.
  The wrapper therefore checks the log for `ERROR` and truncates it per run. (2) `FunctionSignatureParser`
  rejects calling-convention keywords, so `ImportSymbols` strips `__xxx` and sets the convention
  separately. (3) For `__thiscall`, Ghidra forces the `this` parameter's type to `void *`, so a CSV
  signature `(uint * this)` exports as `(void * this)`. Typed `this` needs a struct from
  `re/types/` (`ImportTypes.java` is still planned). (4) `ImportSymbols` validates every row before
  touching the program and applies them in one transaction that is rolled back on failure.
  **Early Phase 5 lead:** the RNG multiplier `C5 90 C6 6A` occurs **852 times** in `.text` (r2 `/x`), so
  the step is mostly inlined. One out-of-line copy is at `0x0045C370`: a `__thiscall` on a
  `{u32 low; u32 high}` seed, `*(u64*)this = (u64)low * 0x6AC690C5 + high` (decompiled, not yet named).
- **2026-10-11 — Phase 5 done (reverser).** Findings `docs/findings/rng/0001-rng-core.md` (answered) and
  `0002-seed-tree.md` (first pass, open), plus experiment `run:2026-10-11-rng-emu`. **Done-when met:** the RNG
  functions are named in `re/symbols.csv` (22 rows), and the step **and** the range/init primitives are `[C]`.
  `tools/rng.py` matches the binary's own functions 5000/5000 on every primitive, run through Ghidra's
  p-code emulator (`re/ghidra_scripts/EmuFastcall.java`, `tools/ghidra.sh emu`). That is the "emulated run"
  route, so no wine was needed.
  **Results:** seed = `{u32 low, u32 high}`, step `low*0x6AC690C5 + high` (64-bit), `RNG_Range(n)` returns 0 **without
  drawing** when `(int)n < 1`, else `low % n`. Init sets `high = 666`. The step is inlined in 427 functions. The seed
  tree is `[I]`: game seed `+0xD0` and a separate **map seed** `+0x7C` (clock entropy, or the `-seed` override), act
  seed = map seed for every act, level seed = `act[+0x470] + levelId` (a sum, not a draw), room/active room/unit
  each = `init(step(parent).low)`. Act II draws two distinct Tal Rasha tombs (levels 66–72) right after act creation.
  **New tools:** `tools/rng.py`; Ghidra scripts `FindScalar`, `EmuFastcall`, `StringsIn` (+ `findscalar`, `emu`,
  `strings` wrapper commands).
  **Surprises:** (1) `-seed 0` can't be forced, because the option is applied only when non-zero. (2) Level seeds
  don't depend on creation order. (3) Inlined `% const` draws skip the `n < 1` guard, so specs must state the form
  per call site. **Next:** Phase 6 (spec-writer) can write `docs/specs/rng/` from 0001. 0002 stays open under
  the `rng/seeds` map row (ADR-0002). Its `[C]` path is a wine run with `-seed N`.
