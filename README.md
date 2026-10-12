# d2-recon

**A reimplementation-grade specification of Diablo II: Lord of Destruction 1.14d**: its file formats,
data tables and the algorithms in `Game.exe`, documented precisely enough to rebuild them, down to
RNG call order, integer arithmetic and table lookups.

This is a preservation project. The output is **documentation, not code**. No game data and no
decompiled source live in this repository.

## Scope

Three subsystems come first, all built on the game's RNG:

| Area | What gets specified |
|---|---|
| **Item creation** | treasure class resolution, quality rolls, affix/unique/set selection, ilvl/alvl, sockets |
| **Monster spawning** | per-level monster pools, packs and minions, champions/uniques/superuniques, monster level per difficulty |
| **Level generation (DRLG)** | preset, maze and outdoor generators, rooms, warps, object and population placement |

The order and status of each subsystem are tracked in the research map,
[`docs/specs/README.md`](docs/specs/README.md).

## Status

Reviewed specs so far (the full table, with every band and dependency, is the
[research map](docs/specs/README.md)):

| Spec | What it covers | Status |
|---|---|---|
| [`rng`](docs/specs/rng/README.md) | seed state, step, the two range reductions, initialisers | reviewed |
| [`rng/seeds`](docs/specs/rng/seeds.md) | game seed → act → level → room → unit seed derivation | reviewed |
| [`data/excel`](docs/specs/data/README.md) | which excel form is loaded (`.bin`/`.txt`), record layout, code→index lookups | reviewed |
| [`drlg/overview`](docs/specs/drlg/README.md) | act → level → room, `DrlgType` dispatch, room-creation order, preset file index | reviewed |
| [`drlg/room-tiles`](docs/specs/drlg/room-tiles.md) | DT1 list and mask, tile pick by rarity, the k room-seed draws | reviewed |

In flight ([plans index](docs/plans/README.md)):

- **Items: quality roll** ([plan 0010](docs/plans/0010-items-quality.md)): the drop roll read
  ([items/0002](docs/findings/items/0002-quality-roll.md)); bit-exact model with magic find next.

Done: bootstrap and binary pinning (0001), the excel foundation (0002), the seed tree and the
runtime harness (0003), prerequisite formats (0005), asset rendering tools (0006), the mechanical docs gate (0007),
the DRLG overview with the room-seed k (0008), the item art tools: index, colour shifts, per-item sheets (0009), the monster level pool with the
monster level ([specs/monsters/pool](docs/specs/monsters/pool.md), reviewed) (0012), and the save-file code with
round trips ([specs/save/d2s](docs/specs/save/d2s.md), draft until `items/properties`) (0013), the
two-client harness that settled the party count and the champion loot table for drops (0011), and treasure class
resolution ([specs/items/tc](docs/specs/items/tc.md), reviewed) (0004).

Supporting material already in place:

- **Formats** ([`docs/formats/`](docs/formats/README.md)): installer, MPQ, excel `.bin`, TBL, DS1,
  DT1, D2S, palettes, DC6, DCC, COF.
- **Tables** ([`docs/tables/`](docs/tables/README.md)): schema docs for Levels, LvlPrest, LvlSub,
  LvlTypes, LvlMaze, MonStats, TreasureClassEx, ItemRatio, ItemTypes, Weapons, Armor, Misc,
  UniqueItems, SetItems and a few smaller lookups.
- **Symbols** ([`re/symbols.csv`](re/symbols.csv)): a few hundred named addresses in `Game.exe`,
  replayed into a disposable Ghidra project.

## How the evidence works

Every behavioural claim carries an **anchor** (an address in the pinned binary, a table column, an
experiment id) and a **confidence tag**:

| Tag | Meaning |
|---|---|
| `[C]` confirmed | code we read **and** an independent corroboration (a second code path, data behaviour, a runtime experiment, or a bit-exact reproduction) |
| `[I]` inferred | code we read, not yet corroborated |
| `[L]` lead | external documentation or a hypothesis with no anchor yet, allowed only under *Open questions* |

All addresses refer to one binary, `Game.exe` 1.14d (sha256
`631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf`, image base `0x400000`).
In 1.14d every former DLL is merged into it.

**Sources policy.** Community documentation may be used as leads and is registered in
[`docs/sources.md`](docs/sources.md). Third-party decompiled or reconstructed game code (D2MOO and
similar) is never read, copied or paraphrased. Full rules:
[ADR-0001](docs/adrs/0001-target-toolchain-evidence-sources.md).

## Repository layout

```
docs/
  specs/       THE DELIVERABLE: one directory per subsystem; README.md is the research map
  findings/    reverse-engineering notes: addresses, decompile excerpts, confidence
  tables/      one schema doc per excel table (columns, types, semantics, foreign keys)
  formats/     binary/container formats (installer, MPQ, excel .bin, TBL, DS1/DT1, DC6/DCC/COF, .d2s)
  adrs/        durable decisions (append-only)
  plans/       research work in flight; done/ when closed
  inventory.md hashed list of every extracted file; the PINNED Game.exe
  sources.md   external documentation used as leads
  backlog.md   cross-lane requests and open questions
  glossary.md  D2 terms (ilvl, alvl, TC, DRLG, …)
re/
  symbols.csv  single source of truth for named addresses
  types/       recovered struct headers
  ghidra_scripts/  headless scripts (symbol round-trip, decompile, xrefs, RNG call graph)
  rngclass/    classification files for the RNG call-graph script
tools/         stdlib Python helpers (run with python3 -I), gdb command files, docs-gate baselines
workspace/     gitignored: installers, extracted files, MPQ dumps, Ghidra project, logs, renders
```

## Reproducing the setup

You need a legally owned copy of Diablo II: Lord of Destruction.

**Toolchain:** `innoextract`, Ghidra (headless) on JDK 21, `radare2`, StormLib + `smpq`, `wine`,
`gdb`, Python 3, `openssl` and p11-kit `trust` (signature checks).

1. Put the installers in `workspace/reference/installers/` (`1.14d/`, `1.14b-d2/`, `1.14b-d2lod/`).
   This folder is never committed.
2. Extract and inventory, following [`docs/formats/installer.md`](docs/formats/installer.md).
3. Check the pinned binary:
   ```bash
   python3 -I tools/pe_authenticode.py workspace/install/app/game.exe   # expects VERDICT: UNMODIFIED
   sha256sum workspace/install/app/game.exe                              # must match the PINNED hash
   ```
4. Dump the MPQs and build the merged data tree (`tools/mpq_dump.py names | extract | merge`,
   procedure in [`docs/formats/mpq.md`](docs/formats/mpq.md)).
5. Build the Ghidra project and replay the symbols: `tools/ghidra.sh build`.
6. Check the docs: `python3 -I tools/gate.py` (add `--full` to rerun the parser surveys against
   `workspace/`).

| Tool | Purpose |
|---|---|
| `tools/inventory.py` | Markdown inventory (path, size, sha256, `file` type, class) |
| `tools/pe_info.py`, `tools/pe_authenticode.py` | PE facts; end-to-end Authenticode check plus PE checksum |
| `tools/mpq_verify.py`, `tools/mpq_dump.py` | MPQ signature status; dump the archives and build the merged tree |
| `tools/tree_diff.py` | sha256 diff of two extracted trees |
| `tools/excel_survey.py`, `tools/excel_bin.py`, `tools/excel_layouts.py` | excel `.txt`/`.bin` survey, `.bin` decoding and cell-by-cell diff |
| `tools/tbl.py` | string tables and key → index resolution |
| `tools/ds1.py`, `tools/dt1.py` | preset maps and tile files: parse, survey, render |
| `tools/d2s.py`, `tools/d2s_samples.py` | character saves (header, stats, item bitstream); sample-save inputs |
| `tools/palette.py`, `tools/dc6.py`, `tools/dcc.py`, `tools/cof.py`, `tools/render_all.py` | presentation decoders, tools only (ADR-0005); output in `workspace/render/` |
| `tools/item_art.py` | item → icon, drop animation and colour-transform index |
| `tools/rng.py` | reference RNG reimplementation and checker against emulator output |
| `tools/ghidra.sh` | headless Ghidra: build, symbol import/export, decompile, xrefs, searches, emulation |
| `tools/d2run.py`, `tools/xdrive.py`, `tools/gdb/` | runtime harness (ADR-0003): the game under wine and gdb on its own X display |
| `tools/gate.py`, `tools/test_gate.py` | docs gate (ADR-0006) and its self-test |

Untrusted binaries run only under wine in an isolated prefix (`workspace/wineprefix`). Python that
parses game files runs with `-I` from `tools/`.

## How the work is organised

The research runs as four lanes, each a Claude Code skill in `.claude/skills/`:

| Lane | Owns |
|---|---|
| `architect` | plans, ADRs, the research map, evidence rules, reviews before anything counts |
| `archivist` | extraction, inventory, format and table docs, parsers |
| `reverser` | Ghidra/radare2 analysis and runtime experiments on `Game.exe`, findings, `re/symbols.csv` |
| `spec-writer` | turns findings and table docs into `docs/specs/` |

Lanes hand work over through plans and [`docs/backlog.md`](docs/backlog.md). Durable decisions are
recorded as [ADRs](docs/adrs/README.md). Commit hygiene (no game data, explicit staging, no history
rewrites, a green docs gate) is enforced by hooks in `.claude/hooks/`. [`CLAUDE.md`](CLAUDE.md) is
the map for agents.

## Legal

Diablo II and Lord of Destruction are trademarks of Blizzard Entertainment. This project is not
affiliated with or endorsed by Blizzard. It contains no game assets, executables or data tables
(short illustrative rows at most), only original documentation produced by analysing a legally
owned copy.
