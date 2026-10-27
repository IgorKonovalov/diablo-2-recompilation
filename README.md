# d2-recon

**A reimplementation-grade specification of Diablo II: Lord of Destruction 1.14d**: its file formats,
data tables and the algorithms in `Game.exe`, documented precisely enough to rebuild them, down to
RNG call order, integer arithmetic and table lookups.

This is a preservation project. The output is **documentation, not code**. No game data and no
decompiled source live in this repository.

## Start here

- **To understand how the game works**, read the [wiki](docs/wiki/README.md). It explains, in plain prose with
  diagrams, how the game builds a level, fills it with monsters and objects, and decides what drops. Every section
  links the spec it restates. The wiki is not published.
- **To reimplement a system**, read its spec from the [research map](docs/specs/README.md).
- **To see how the project decides what is true**, read [How we know](docs/wiki/how-we-know.md), then
  [ADR-0001](docs/adrs/0001-target-toolchain-evidence-sources.md).

### How to read this repository

Each layer explains the one above it and points to the one below:

1. **Wiki** ([`docs/wiki/`](docs/wiki/README.md)): plain prose for people. No claims of its own; each section links a
   spec section.
2. **Spec** ([`docs/specs/`](docs/specs/README.md)): the deliverable. Language-neutral pseudocode with the exact
   draw order and arithmetic, every statement tagged with its confidence and anchored. Its *Evidence* section names
   the findings.
3. **Finding** ([`docs/findings/`](docs/findings/README.md)): the reverse-engineering notes behind a spec: addresses,
   what the code does, and how it was checked. A finding names the runs it rests on.
4. **Run record** (`docs/findings/<subsystem>/experiments.md`, for example
   [items](docs/findings/items/experiments.md)): one experiment on the real game, written so it can be repeated: the
   command lines, what was logged, and the checker that reproduced it.

Table and format questions go to [`docs/tables/`](docs/tables/README.md) and [`docs/formats/`](docs/formats/README.md).
Terms are in the [glossary](docs/glossary.md).

## Scope

Three subsystems came first, all built on the game's RNG:

| Area | What gets specified |
|---|---|
| **Item creation** | treasure class resolution, quality rolls, affix/unique/set selection, ilvl/alvl, sockets |
| **Monster spawning** | per-level monster pools, packs and minions, champions/uniques/superuniques, monster level per difficulty |
| **Level generation (DRLG)** | preset, maze and outdoor generators, rooms, warps, object and population placement |

All three are reviewed, and [chain](docs/specs/chain/README.md) composes them from the game seed to a populated level
and a drop. [ADR-0002](docs/adrs/0002-scope-creation-paths-and-enablers.md) added the systems the core cannot be
reproduced without (enablers) and the other callers into the item and monster code (creation paths).
[ADR-0014](docs/adrs/0014-scope-game-simulation.md) added the game run over time (simulation) in five phases: combat
formulas, stats and states, skills and missiles ([ADR-0020](docs/adrs/0020-skills-phase-in-two-plans.md) splits it into
the machinery and the function catalogue), animation and frame timing, and monster AI (plan 0052, approved
2026-10-27). [ADR-0017](docs/adrs/0017-scope-quests-travel-economy.md) brought quest progression, travel and the item
economy in beside them (game rules). [ADR-0022](docs/adrs/0022-scope-server-frame.md) (accepted 2026-10-27) adds a
sixth simulation phase after monster AI: the server frame, composed so that simulation events chain across units.

## Status

Every row of the [research map](docs/specs/README.md), with its status and the `updated:` date of the spec's front
matter. The research map is authoritative: it adds the dependencies, key tables, tag counts and the plans behind
each row.

**Core**

| Subsystem | What it covers | Status | Date |
|---|---|---|---|
| [`rng`](docs/specs/rng/README.md) | seed state, step, range | reviewed | 2026-10-17 |
| [`items/tc`](docs/specs/items/tc.md) | treasure class resolution, picks, NoDrop, player-count scaling | reviewed | 2026-10-21 |
| [`items/quality`](docs/specs/items/quality.md) | the unique/set/rare/magic/superior/normal/low roll; magic find | reviewed | 2026-10-20 |
| [`items/affixes`](docs/specs/items/affixes.md) | alvl, prefix/suffix selection, rare affix counts, automagic | reviewed | 2026-10-27 |
| [`items/uniques-sets`](docs/specs/items/uniques-sets.md) | unique and set candidate selection, fallback rules | reviewed | 2026-10-27 |
| [`items/properties`](docs/specs/items/properties.md) | stat rolls, sockets, ethereal, durability, defense | reviewed | 2026-10-27 |
| [`monsters/pool`](docs/specs/monsters/pool.md) | which monster types a level can host | reviewed | 2026-10-27 |
| [`monsters/spawn`](docs/specs/monsters/spawn.md) | packs, density, placement, minions | reviewed | 2026-10-27 |
| [`monsters/special`](docs/specs/monsters/special.md) | champions, uniques, superuniques, mod rolls, unique name rolls | reviewed | 2026-10-27 |
| [`drlg/overview`](docs/specs/drlg/README.md) | act → level → room hierarchy, generator dispatch, room-type draws ([room tiles](docs/specs/drlg/room-tiles.md), 2026-10-27) | reviewed | 2026-10-21 |
| [`drlg/preset`](docs/specs/drlg/preset.md) | DS1 preset maps, their unit lists and keep/drop rolls, `LvlPrest` columns | reviewed | 2026-10-17 |
| [`drlg/maze`](docs/specs/drlg/maze.md) | maze generator (dungeons and caves) | reviewed | 2026-10-17 |
| [`drlg/outdoor`](docs/specs/drlg/outdoor.md) | wilderness generator, borders, paths, `LvlSub` substitutions | reviewed | 2026-10-20 |
| [`drlg/warps`](docs/specs/drlg/warps.md) | inter-level links and placement | reviewed | 2026-10-17 |
| [`objects`](docs/specs/objects/README.md) | object, shrine and chest placement and operation | reviewed | 2026-10-27 |
| [`chain`](docs/specs/chain/README.md) | seed to world: the core specs composed from the game seed to a populated level and a drop, with no oracle inside the chain | reviewed | 2026-10-21 |

**Enablers** ([ADR-0002](docs/adrs/0002-scope-creation-paths-and-enablers.md))

| Subsystem | What it covers | Status | Date |
|---|---|---|---|
| [`data/excel`](docs/specs/data/excel.md) | which form is loaded (`.bin`/`.txt`), record layout, code→index lookups ([overview](docs/specs/data/README.md), 2026-10-27) | reviewed | 2026-10-27 |
| [`data/calc`](docs/specs/data/calc.md) | the formula bytecode (`*code.bin`) and the columns that index into it | reviewed | 2026-10-17 |
| [`data/strings`](docs/specs/data/strings.md) | string-table lookup by key and index, as used by name rolls | reviewed | 2026-10-27 |
| [`rng/seeds`](docs/specs/rng/seeds.md) | game seed → act → level → room → unit seed derivation | reviewed | 2026-10-27 |
| [`drlg/collision`](docs/specs/drlg/collision.md) | room collision grid, logic regions, the placement tests used by spawning and objects | reviewed | 2026-10-27 |
| [`save/d2s`](docs/specs/save/d2s.md) | save layout, item bitstream, persisted seeds and quest state | reviewed | 2026-10-27 |
| [`drlg/lifecycle`](docs/specs/drlg/lifecycle.md) | room activation and release, the inactive records, the restore of monsters, objects and ground items, the wanderer tick | reviewed | 2026-10-27 |

**Creation paths** ([ADR-0002](docs/adrs/0002-scope-creation-paths-and-enablers.md))

| Subsystem | What it covers | Status | Date |
|---|---|---|---|
| [`items/vendors`](docs/specs/items/vendors.md) | store stock, refresh, vendor ilvl, gambling | reviewed | 2026-10-21 |
| [`items/cube`](docs/specs/items/cube.md) | recipe matching, input checks, output construction, rerolls | reviewed | 2026-10-27 |
| [`items/sockets-runewords`](docs/specs/items/sockets-runewords.md) | socket filling, gems, runes and jewels, runeword activation | reviewed | 2026-10-27 |
| [`items/quest-drops`](docs/specs/items/quest-drops.md) | quest-state TC switches, first-kill and special drops, quest rewards | reviewed | 2026-10-27 |
| [`monsters/stats`](docs/specs/monsters/stats.md) | HP, damage, AC and XP per difficulty and player count, mod effects | reviewed | 2026-10-27 |
| [`hirelings`](docs/specs/hirelings/README.md) | hireling stock, per-difficulty stats, name rolls | reviewed | 2026-10-20 |
| [`player/creation`](docs/specs/player/creation.md) | starting stats and items, experience curve, level-up | reviewed | 2026-10-21 |

**Simulation** ([ADR-0014](docs/adrs/0014-scope-game-simulation.md))

| Subsystem | What it covers | Status | Date |
|---|---|---|---|
| [`combat/formulas`](docs/specs/combat/README.md) | to-hit, damage, resistances, block, avoid, damage reduction, on-hit effects: the overview and its four parts, [to-hit](docs/specs/combat/to-hit.md) (the hit test, chance to hit and the defence rolls), [damage](docs/specs/combat/damage.md) (the attacker's damage build), [reductions](docs/specs/combat/reductions.md) (the defender's reductions) and [delivery](docs/specs/combat/delivery.md) (queue, delivery, on-hit effects and the life change), each 2026-10-21 | reviewed | 2026-10-27 |
| [`stats/aggregate`](docs/specs/stats/aggregate.md) | stat lists and their cache, the stat ops, the maxima and their rescale, item requirements, set bonuses ([overview](docs/specs/stats/README.md), 2026-10-21) | reviewed | 2026-10-20 |
| [`stats/states`](docs/specs/stats/states.md) | timed state apply, refresh, `group`, expiry, the regeneration ticks, auras, shrines and wells | reviewed | 2026-10-27 |
| [`skills/dispatch`](docs/specs/skills/dispatch.md) | the skill request, start checks, start and do function dispatch, charges, costs, the skill packet, event handlers, summons, monster skill use ([overview](docs/specs/skills/README.md), 2026-10-27) | reviewed | 2026-10-27 |
| [`skills/missiles`](docs/specs/skills/missiles.md) | missile creation, seed, motion, collision, hit, pierce, sub-missiles, end of life | reviewed | 2026-10-27 |
| `skills/catalogue` | every numbered skill and missile function a stock row uses (plan 0046) | findings in progress | — |
| `anim/timing` | unit modes and frame counts, event frames, attack, cast, hit-recovery and block rates and their breakpoints (plan 0050) | findings in progress | — |
| `anim/movement` | walk and run speed, the slowing states, the per-frame step along a path (plan 0050) | findings in progress | — |
| `monsters/ai` | the AI tick, target, mode and skill choice, following, the path request and its draws (plan 0052) | not started | — |

**Game rules** ([ADR-0017](docs/adrs/0017-scope-quests-travel-economy.md))

| Subsystem | What it covers | Status | Date |
|---|---|---|---|
| [`quests/progression`](docs/specs/quests/progression.md) | the quest registry and event dispatch, each quest's record bits per event and difficulty, quest timers, the quest seed's non-item draws ([overview](docs/specs/quests/README.md), 2026-10-20) | reviewed | 2026-10-21 |
| [`quests/travel`](docs/specs/quests/travel.md) | waypoints, act change, town portals, warps and their quest gates, death and join placement | reviewed | 2026-10-21 |
| [`items/economy`](docs/specs/items/economy.md) | buy, sell, gamble and repair prices; hire, resurrect and identify costs; gold; durability, quantity and charge wear | reviewed | 2026-10-27 |

### Plans

In flight ([plans index](docs/plans/README.md)):

- **[0038](docs/plans/0038-inferred-claims-sweep.md)**: the inferred-claims sweep, raising the reviewed specs'
  inferred points to confirmed where a run, a re-check of kept logs or a static second source allows; Phase 3
  re-tags the specs cluster by cluster.
- **[0046](docs/plans/0046-skills-function-catalogue.md)**: the skills and missiles function catalogue.
- **[0050](docs/plans/0050-animation-frame-timing.md)**: animation and frame timing.
- **[0052](docs/plans/0052-monster-ai.md)**: monster AI (approved 2026-10-27).

Done (each closed plan is in `docs/plans/done/`, listed in the [plans index](docs/plans/README.md)):

- **Foundations**: bootstrap and binary pinning (0001), the excel foundation (0002), the seed tree and the runtime
  harness (0003), prerequisite formats (0005), asset rendering tools (0006), the docs gate (0007), item art tools
  (0009), the two-client harness (0011).
- **Items**: treasure classes (0004), the quality roll and magic find (0010), uniques and sets (0019), affixes (0021),
  base stats and properties (0024), sockets and runewords (0029), the Horadric Cube (0030), vendors and gambling
  (0031), quest drops and rewards (0032).
- **Monsters**: the level pool and monster level (0012), room population (0014), special monsters (0018), monster
  stats (0025), hirelings (0033).
- **Levels and objects**: the DRLG overview and room seeds (0008), presets (0016), the collision grid (0017), the maze
  generator and warps (0022), objects (0023), the outdoor generators (0026), the room lifecycle (0040).
- **Data, saves and players**: save files (0013), string tables (0028), player creation (0034), calc formulas (0035).
- **Sweeps**: backlog sweeps 1–6 (0015, 0020, 0027, 0039, 0049, 0051), the multiplayer branches (0044), the
  simulation shortfalls (0047).
- **Reading**: the human wiki and this README (0036).
- **Simulation**: combat formulas (0037), stats and states (0041), the skills and missiles machinery (0045).
- **Game rules**: quests and travel (0042), the item economy (0043).
- **Composition**: seed to world (0048).

### Supporting material

- **Formats** ([`docs/formats/`](docs/formats/README.md)): installer, MPQ, excel `.bin`, TBL, DS1,
  DT1, D2S, palettes, DC6, DCC, COF.
- **Tables** ([`docs/tables/`](docs/tables/README.md)): one schema doc per excel table the specs use.
- **Symbols** ([`re/symbols.csv`](re/symbols.csv)): the named addresses in `Game.exe`, replayed into a disposable
  Ghidra project.

## How the evidence works

Every behavioural claim in a spec carries an **anchor** (an address in the pinned binary, a table column, an
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
[ADR-0001](docs/adrs/0001-target-toolchain-evidence-sources.md); every decision is in the
[ADR index](docs/adrs/README.md).

## Repository layout

```
docs/
  wiki/        plain-prose pages over the reviewed specs (start here; not published)
  specs/       THE DELIVERABLE: one directory per subsystem; README.md is the research map
  findings/    reverse-engineering notes: addresses, decompile excerpts, confidence, run records
  tables/      one schema doc per excel table (columns, types, semantics, foreign keys)
  formats/     binary/container formats (installer, MPQ, excel .bin, TBL, DS1/DT1, DC6/DCC/COF, .d2s)
  adrs/        durable decisions (append-only)
  plans/       research work in flight; done/ when closed
  inventory.md hashed list of every extracted file; the PINNED Game.exe
  sources.md   external documentation used as leads
  backlog/     cross-lane requests, one file per entry (closed ones in archive/; backlog.md is the frozen pre-2026-10-17 archive)
  glossary.md  D2 terms (ilvl, alvl, TC, DRLG, …)
re/
  symbols.csv  single source of truth for named addresses
  types/       recovered struct headers
  ghidra_scripts/  headless scripts (symbol round-trip, decompile, xrefs, RNG call graph)
  rngclass/    classification files for the RNG call-graph script
tools/         stdlib Python helpers (run with python3 -I), gdb command files, docs-gate code and baselines
workspace/     gitignored: installers, extracted files, MPQ dumps, Ghidra project, logs, renders, harness
```

## Reproducing the setup

You need a legally owned copy of Diablo II: Lord of Destruction.

**Toolchain:** `innoextract`, Ghidra (headless) on JDK 21, `radare2`, StormLib + `smpq`, `wine`,
`gdb`, Python 3, `openssl` and p11-kit `trust` (signature checks), and `node` (the docs gate's Mermaid
check). The runtime harness also needs a rootful Xwayland display for the game (step 7).

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
7. For runtime experiments, set up the harness as described in
   [`tooling.md` § Runtime harness](.claude/skills/reverser/references/tooling.md#runtime-harness-wine--gdb): the game
   directory `workspace/runtime/game/` (the pinned `game.exe` with the DLLs, `d2.lng` and MPQs the tooling notes
   list), a plain `wineboot -i` prefix in `workspace/wineprefix/`, and `tools/d2run.py`, which
   starts the game on its own hidden Xwayland display and hands it to gdb. Further copies run side by side in slots
   (`tools/slots.py`, [ADR-0011](docs/adrs/0011-harness-slots.md)).

| Tool | Purpose |
|---|---|
| `tools/inventory.py` | Markdown inventory (path, size, sha256, `file` type, class) |
| `tools/pe_info.py`, `tools/pe_authenticode.py` | PE facts; end-to-end Authenticode check plus PE checksum |
| `tools/mpq_verify.py`, `tools/mpq_dump.py` | MPQ signature status; dump the archives and build the merged tree |
| `tools/tree_diff.py` | sha256 diff of two extracted trees |
| `tools/excel_survey.py`, `tools/excel_bin.py`, `tools/excel_layouts.py`, `tools/excel_edit.py` | excel `.txt`/`.bin` survey, `.bin` decoding and cell-by-cell diff, edited tables for forced-path runs |
| `tools/tbl.py` | string tables and key → index resolution |
| `tools/ds1.py`, `tools/dt1.py` | preset maps and tile files: parse, survey, render |
| `tools/d2s.py`, `tools/d2s_samples.py`, `tools/d2sio.py` | character saves (header, stats, item bitstream); sample-save inputs; the save write/read log checker |
| `tools/*_survey.py` | table surveys per subsystem (monsters, uniques, affixes, properties, objects, outdoor, maze, sockets, vendors, quests, hirelings, players, calc) |
| `tools/palette.py`, `tools/dc6.py`, `tools/dcc.py`, `tools/cof.py`, `tools/render_all.py` | presentation decoders, tools only (ADR-0005); output in `workspace/render/` |
| `tools/item_art.py` | item → icon, drop animation and colour-transform index |
| `tools/rng.py` | reference RNG reimplementation and checker against emulator output |
| `tools/tc.py`, `tools/quality.py`, `tools/uniques.py`, `tools/affixes.py`, `tools/props.py`, `tools/items_chain.py` | item models (treasure classes, quality, uniques and sets, affixes, properties, the chained affix and property models), replayed against runtime logs |
| `tools/sockets.py`, `tools/cube.py`, `tools/vendors.py`, `tools/questdrops.py` | the other item creation paths, checked against runtime logs |
| `tools/drlg.py`, `tools/collision.py`, `tools/maze_replay.py`, `tools/outdoor_replay.py`, `tools/objects.py` | room seeds and generators, the collision grid, maze and outdoor replays, object population |
| `tools/monpool.py`, `tools/monspawn.py`, `tools/monspecial.py`, `tools/monstats.py` | monster pool, room population, special monsters and monster stats |
| `tools/hirelings.py`, `tools/player.py`, `tools/calc.py` | hirelings, new characters and level-ups, calc formulas |
| `tools/ghidra.sh` | headless Ghidra: build, symbol import/export, decompile, xrefs, searches, emulation |
| `tools/d2run.py`, `tools/xdrive.py`, `tools/slots.py`, `tools/gdb/` | runtime harness (ADR-0003, ADR-0011): the game under wine and gdb on its own X display, one per slot |
| `tools/d2pilot.py`, `tools/d2hunt.py` | screen-driven harness helpers: scripted exploration, kill loop, waypoint finder, play recorder |
| `tools/saves.py`, `tools/*_saves.py`, `tools/*_sessions.py`, `tools/d2s_recipes/` | set the saves directory aside, build and install the test characters and session plans of each run |
| `tools/gate.py`, `tools/test_gate.py`, `tools/mermaid_check.mjs` | docs gate (ADR-0006), its self-test, and the Mermaid syntax check it calls |

Untrusted binaries run only under wine in an isolated prefix (`workspace/wineprefix`). Python that
parses game files runs with `-I` from `tools/`.

## How the work is organised

The research runs as four lanes, each a Claude Code skill in `.claude/skills/`:

| Lane | Owns |
|---|---|
| `architect` | plans, ADRs, the research map, evidence rules, reviews before anything counts |
| `archivist` | extraction, inventory, format and table docs, parsers |
| `reverser` | Ghidra/radare2 analysis and runtime experiments on `Game.exe`, findings, `re/symbols.csv` |
| `spec-writer` | turns findings and table docs into `docs/specs/`, and keeps the wiki in step with them |

Lanes hand work over through [plans](docs/plans/README.md) and the [backlog](docs/backlog/README.md). Durable
decisions are recorded as [ADRs](docs/adrs/README.md). Commit hygiene (no game data, explicit staging, no history
rewrites, a green docs gate) is enforced by hooks in `.claude/hooks/`. [`CLAUDE.md`](CLAUDE.md) is the map for
agents.

## Legal

Diablo II and Lord of Destruction are trademarks of Blizzard Entertainment. This project is not
affiliated with or endorsed by Blizzard. It contains no game assets, executables or data tables
(short illustrative rows at most), only original documentation produced by analysing a legally
owned copy.
