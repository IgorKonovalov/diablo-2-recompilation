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

Bootstrap ([Plan 0001](docs/plans/done/0001-bootstrap.md)):

- [x] Toolchain installed and checked
- [x] Installer extracted, every file hashed ([`docs/inventory.md`](docs/inventory.md))
- [x] `Game.exe` 1.14d pinned; its Authenticode signature verifies, so the binary is unmodified
- [x] MPQ gameplay data verified byte-identical against Blizzard's 1.14b installers ([`docs/formats/installer.md`](docs/formats/installer.md))
- [ ] Dump the MPQs and catalogue the excel tables
- [ ] Reproducible Ghidra project with a symbol round-trip
- [ ] Locate the RNG and its seed lifecycle
- [ ] First spec: `docs/specs/rng/`

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
  specs/       THE DELIVERABLE: one directory per subsystem
  findings/    reverse-engineering notes: addresses, decompile excerpts, confidence
  tables/      one schema doc per excel table (columns, types, semantics, foreign keys)
  formats/     binary/container formats (installer, MPQ, DS1/DT1, DC6/DCC, .bin, .d2s)
  adrs/        durable decisions (append-only)
  plans/       research work in flight; done/ when closed
  inventory.md hashed list of every extracted file; the PINNED Game.exe
  backlog.md   cross-lane requests and open questions
  glossary.md  D2 terms (ilvl, alvl, TC, DRLG, …)
re/
  symbols.csv  single source of truth for named addresses
  types/       recovered struct headers
  ghidra_scripts/
tools/         stdlib Python helpers (run with python3 -I)
workspace/     gitignored: installers, extracted files, MPQ dumps, Ghidra project
```

## Reproducing the setup

You need a legally owned copy of Diablo II: Lord of Destruction.

**Toolchain:** `innoextract`, Ghidra (headless) on JDK 21, `radare2`, StormLib + `smpq`, `wine`,
Python 3, `openssl` and p11-kit `trust` (signature checks).

1. Put the installers in `workspace/reference/installers/` (`1.14d/`, `1.14b-d2/`, `1.14b-d2lod/`).
   This folder is never committed.
2. Extract and inventory, following [`docs/formats/installer.md`](docs/formats/installer.md).
3. Check the pinned binary:
   ```bash
   python3 -I tools/pe_authenticode.py workspace/install/app/game.exe   # expects VERDICT: UNMODIFIED
   sha256sum workspace/install/app/game.exe                              # must match the PINNED hash
   ```

| Tool | Purpose |
|---|---|
| `tools/inventory.py` | Markdown inventory (path, size, sha256, `file` type, class) |
| `tools/pe_info.py` | PE header, sections, imports and version resource |
| `tools/pe_authenticode.py` | end-to-end Authenticode check plus PE checksum |
| `tools/mpq_verify.py` | MPQ signature status and header fields (via StormLib) |
| `tools/tree_diff.py` | sha256 diff of two extracted trees |

Untrusted binaries run only under wine in an isolated prefix (`workspace/wineprefix`). Python that
parses game files runs with `-I` from `tools/`.

## How the work is organised

The research runs as four lanes, each a Claude Code skill in `.claude/skills/`:

| Lane | Owns |
|---|---|
| `architect` | plans, ADRs, the research map, evidence rules, reviews before anything counts |
| `archivist` | extraction, inventory, format and table docs, parsers |
| `reverser` | Ghidra/radare2 analysis of `Game.exe`, findings, `re/symbols.csv` |
| `spec-writer` | turns findings and table docs into `docs/specs/` |

Lanes hand work over through plans and [`docs/backlog.md`](docs/backlog.md). Commit hygiene (no game
data, explicit staging, no history rewrites) is enforced by hooks in `.claude/hooks/`.
[`CLAUDE.md`](CLAUDE.md) is the map for agents.

## Legal

Diablo II and Lord of Destruction are trademarks of Blizzard Entertainment. This project is not
affiliated with or endorsed by Blizzard. It contains no game assets, executables or data tables
(short illustrative rows at most), only original documentation produced by analysing a legally
owned copy.
