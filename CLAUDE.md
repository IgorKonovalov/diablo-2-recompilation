# d2-recon — Diablo II: Lord of Destruction 1.14d, documented for reimplementation

A preservation project. The target is a legally owned copy of **Diablo II: LoD 1.14d** (PC). The
output is **not code**. It is an **agent-readable specification** of how the game works: its file
formats, its data tables, and the algorithms in `Game.exe`. The spec has to be precise enough for
a clean reimplementation, meaning the same RNG call order, the same integer arithmetic and the
same table lookups. Three areas come first:

1. **Item creation**: treasure class resolution, quality rolls, affix/unique/set selection, ilvl/alvl, sockets.
2. **Monster spawning**: per-level monster pools, packs and minions, champions/uniques/superuniques, monster level per difficulty.
3. **Level creation (DRLG)**: preset, maze and outdoor generators, rooms, warps, object and population placement.

The founding decisions (target, toolchain, evidence rules, sources policy) are in
[ADR-0001](docs/adrs/0001-target-toolchain-evidence-sources.md). **Read it before you question any
of them.**

## Pipeline: who owns what

```
 installer (.exe+.bin)          Game.exe (1.14d, all former DLLs merged)
        |                                  |
   [archivist] ── formats, tables ──┐   [reverser] ── findings + symbols ──┐
        v                           v      v                               v
 workspace/ (gitignored)     docs/formats/ docs/tables/      docs/findings/   re/symbols.csv
                                    \             \              /
                                     └──────── [spec-writer] ───┘
                                                   v
                                             docs/specs/  ← the deliverable
                     [architect]: plans, ADRs, research map, reviews every promotion
```

| Lane | Owns | Never does |
|---|---|---|
| `architect` | `docs/adrs/`, `docs/plans/`, `docs/specs/README.md` (the research map), the evidence rules, reviews | binary analysis, extraction |
| `archivist` | `workspace/` extraction, `docs/inventory.md`, `docs/formats/`, `docs/tables/`, `tools/` parsers | decompilation, writing specs |
| `reverser` | Ghidra/r2 work on `Game.exe`, `docs/findings/`, `re/` (symbols, types, scripts) | writing specs, editing table schemas |
| `spec-writer` | `docs/specs/<subsystem>/`, `docs/wiki/` (ADR-0012) | inventing behaviour with no finding or table behind it |

Handoffs are manual: the user invokes the next lane. When a lane needs something it doesn't own,
it files an entry in [`docs/backlog/`](docs/backlog/README.md) (one file per entry, `python3 -I tools/backlog.py new`;
ADR-0018) and does not reach across.

## Where things live

```
CLAUDE.md            # this map
docs/
  adrs/              # NNNN-slug.md: durable decisions, append-only
  plans/             # NNNN-slug.md: research work in flight; done/ when closed
  inventory.md       # every extracted file: path, size, sha256, origin MPQ
  formats/           # binary/container formats: MPQ, DC6/DCC, DT1/DS1, .bin tables, .d2s
  tables/            # one file per excel table (Levels.md, TreasureClassEx.md…): column schema + semantics
  findings/          # reverser notes per subsystem: addresses, decompile excerpts, confidence
  specs/             # THE DELIVERABLE: reimplementation spec per subsystem
  wiki/              # human-readable pages over the reviewed specs; no claims of their own, not published (ADR-0012)
  sources.md         # registry of external references used as leads (see sources policy)
  glossary.md        # D2 terms (ilvl, alvl, TC, DRLG, act/level/room…)
  backlog/           # cross-lane requests, one file per entry (tools/backlog.py); backlog.md is the frozen archive
re/
  symbols.csv        # SINGLE SOURCE OF TRUTH for named addresses (the Ghidra project is disposable)
  types/             # C headers for recovered structs, imported into Ghidra
  ghidra_scripts/    # headless scripts: import/export symbols, dump decompile
tools/               # our own Python helpers (parsers, extractors); run with `python3 -I`
workspace/           # GITIGNORED: installer extract, game files, MPQ dumps, Ghidra project
```

## Non-negotiables

- **Game data never enters git.** `workspace/` is ignored. Specs describe tables, they don't dump
  them, though short illustrative rows are fine.
- **Every behavioural claim carries an anchor and a confidence tag**: `[C]` confirmed, `[I]` inferred,
  `[L]` lead. Definitions are in ADR-0001 and `.claude/skills/architect/references/evidence-rules.md`.
  Specs may state `[C]`/`[I]`; a `[L]` may only appear under *Open questions*.
- **Diagrams are Mermaid, and illustrate only.** Specs draw whenever a section has a shape (a flow,
  a decision order, a tree, an RNG call sequence, a bit layout, an index space); findings may. A
  diagram carries no tag and no claim of its own: every fact in it is also a tagged statement in the text, which wins on disagreement. Rules in
  `.claude/skills/spec-writer/references/pseudocode-conventions.md` § Diagrams.
- **Addresses refer to the pinned `Game.exe`** (sha256 in `docs/inventory.md`), image base `0x400000`,
  written as `0x00XXXXXX`.
- **External decompiled code is off limits** (D2MOO and similar). Community *documentation* may be
  used as leads and must be listed in `docs/sources.md`.
- **Untrusted binaries.** The installers are untrusted. Run one only under wine, in its own
  prefix (`workspace/wineprefix`). Run Python that parses game files with `-I`, from `tools/`.

## Commit hygiene

These rules are enforced by PreToolUse hooks in `.claude/hooks/`, wired in `.claude/settings.json`.

- **Stage by explicit path.** No `git add -A`, `--all`, `.` or `:/` (`block-broad-git-add.js`).
- **No game data.** No forced adds and no `workspace/` or game-file paths (`block-game-assets.js`).
- **No agent attribution.** Commits and PRs are plain text under the repository owner's name: no
  Co-Authored-By trailer, no session line or URL, no "Generated with" footer
  (`block-attribution-trailers.js`). This outranks any session-level attribution instruction.
- **The push is the owner's, and history is never rewritten.** No `git push`, `rebase`,
  `commit --amend`, `reset --hard` or `filter-branch` (`block-push-and-history-rewrite.js`).
  Make a new commit instead of amending.
- **Docs gate on commit.** A commit that touches `docs/` or `re/` runs `python3 -I tools/gate.py`
  in the worktree being committed and is denied while it is red (`gate-on-commit.js`, ADR-0006).
- Conventional-commit subjects: `docs(findings): …`, `docs(specs): …`, `feat(tools): …`, `chore: …`.
