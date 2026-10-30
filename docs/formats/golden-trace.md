# Golden trace (`.jsonl`)

Owned by `archivist`. A golden trace is a file of conformance cases: a seed and its inputs, with the values the
reviewed specs say follow from them. A reimplementer runs the cases, writes its own outputs in the same field names
and compares them with `tools/golden.py check`. This is our own format, not a game format; it has no
game-side evidence, only the evidence of the cases it holds ([plan 0059](../plans/0059-golden-traces.md) Phase 1).
Tool: `tools/golden.py`; tests: `tools/test_golden.py`. Sample set:
[golden/sample-v1.jsonl](golden/sample-v1.jsonl) (28 cases).

**Scope of version 1:** the chain's world (game creation, act and level seeds, monster-region pools), the drops
of `TC_ResolveDrops` calls and the observed DRLG windows of the outdoor and maze generators (scope string
`world,drops,drlg`; a set's scope names the case types it holds, in that order). Events (AI, skills, combat, frame windows) are version 2.

## File layout

JSON Lines, UTF-8, one canonical JSON object per line (keys sorted, no spaces, ASCII), `\n` line ends. Line 1 is the
header, every other line a case. A reader rejects a file whose first line is not a header or whose `version` it does
not know. [C] (`tools/golden.py read_set`, `tools/test_golden.py`)

### Header

| Key | Type | Meaning |
|---|---|---|
| `golden` | string | always `"trace"` |
| `version` | int | the format version, 1 |
| `set` | string | the set's name |
| `scope` | string | the case types the set holds, from `world,drops,drlg` in that order (`emit` and `merge` write it; a set of one type carries one word) |
| `game_exe_sha256` | string or null | the pinned `Game.exe` ([inventory](../inventory.md#pinned)); null when the inventory is not readable |
| `tables_digest` | string or null | sha256 over the sorted lines `<lower-case name> <sha256>` of every file of `data/global/excel`: the table set the cases were built on. Differs between table sets, so two people compare it before comparing results |
| `case_kinds` | list | `["observed", "predicted"]` |

The header holds no date or path, so a set's digest is reproducible.

### Case

| Key | Type | Meaning |
|---|---|---|
| `id` | string | unique: `world:o:<log>`, `drop:o:<log>:<call>`, `drlg:o:outdoor:<map seed>:d<diff>:l<level>:<window seed>`, `drlg:o:maze:l<level>:<window seed>` (observed), `world:p:<seed>:d<diff>:e<exp>` (predicted) |
| `kind` | `observed` or `predicted` | see below |
| `type` | `world`, `drop` or `drlg` | which inputs and fields the case has |
| `source` | object | observed: `log` (file name), `log_sha256` (first 16 hex of the kept log), `run` (the experiment record, when given), `call` (a drop's index among the log's TC calls), `window` (a DRLG case: the log line that opens the window, `OD0` or `MZ0`). Predicted: `model` (the tool that produced it) |
| `inputs` | object | what a reimplementation is given (below). Names are plain, not spec fields |
| `expected` | object | field name to value; only the fields in the table below |
| `quirks` | list of strings | ids from the quirks catalogue ([plan 0057](../plans/0057-quirks-catalogue.md)) of the quirks that change an output of this case. Reserved: version 1 files carry `[]`, and `emit` never invents an id. A mismatch report prints a failing case's ids so the implementer sees which trap it hit |

**Kinds, never mixed.** `observed`: the expected values are those of a kept log of the real game, and the
reviewed models reproduced them before the case was written (a case that does not reproduce is not written); a
failure against an observed case is a reason to reopen the spec. `predicted`: the expected values come from the
reviewed model alone, for seeds no run kept; as good as the spec. An observed case wins any disagreement with a
predicted one. (A format rule of this project, not a game fact; `emit` writes an observed case only after the models reproduce it, `tools/test_golden.py` `test_drop_case`.)

**Inputs by type.**

- `world`: `seed` (the `-seed` value), `difficulty` (0 Normal, 1 Nightmare, 2 Hell, null when the log shows none),
  `expansion` (0 classic, 1 expansion, null likewise), `levels` (the level ids given singly in `expected`).
- `drop`: `tc` (the treasure class resolved), `ilvl`, `unit_seed` and `game_seed` (`low:high`, hex), `difficulty`,
  `expansion`, `source_type` (1 monster, 2 object), `source_class`, `monster_flags` (hex byte), `nonodrop`, `max`,
  `fq`, `super_unique`, `killer_type`, `killer_class`, `g6a`, `players`, `party`, `cap` (the last three when the log
  shows them). All are the `TCR` line's and its context lines' ([tc § D](../specs/items/tc.md#d-the-resolver--tc_resolvedrops)).

- `drlg`: `generator` (`outdoor` or `maze`), `map_seed` (the `-seed` of the log), `level` (the level id), `window_seed`
  (the level seed at the window's opening line, `OD0` or `MZ0`); outdoor adds `difficulty` (0 to 2; the replayer's, read from the
  log's name, since a log does not show it; it selects the level sizes) [I]: `hell` in the name is 2, `nightmare` 1, else 0, so the 67 outdoor cases of logs whose name carries neither word rest on the default (a wrong difficulty that changed a level size would not have reproduced; one that did not is unchecked), maze adds `first_room_seed` (`low:high`, the
  room seed the window starts the first room from, from the log's preceding `RC` line, as `tools/maze_replay.py` takes it).
  The case holds the window's output, not the level: an outdoor window is the generator from `OD0` to the end of
  `OutdoorRoomsCreate`, a maze window `MZ0` to `MZ1` (before the placement shift). A DRLG case is observed only.

Seeds are written `low:high`, 8 hex digits each, lower case, as in the specs. (A format rule; `tools/test_golden.py` `test_canon`.)

## Fields

`expected` field names are `<spec>.<step>.<name>`, with a trailing `.N` index (an act number or a level id) where
shown. The step is the spec step the field tests; the pseudocode step letters are those of
[chain § Algorithm](../specs/chain/README.md#algorithm). `python3 -I tools/golden.py fields` prints this table from
the tool. A field value is a JSON scalar or list; a bulky value (every level's seed, every pool) is replaced by the
sha256 of its canonical JSON (`golden.py digest --value`), named `*_digest`.

| Field | Value | Spec step | Spec |
|---|---|---|---|
| `chain.A1.game_seed` | `low:high` | A1 game seed `Init(N)` | [chain](../specs/chain/README.md#algorithm) |
| `chain.A1.map_seed` | int | A1 map seed `N` | chain |
| `chain.A2.monster_regions_seed` | `low:high` | A2 game draw 1, `Init(low)` | chain |
| `chain.A3.object_region_seed` | `low:high` | A3 game draw 2, object-region seed `O` | chain |
| `chain.A3.game_seed_after` | `low:high` | A3 the game seed after draw 2 | chain |
| `chain.A4.store_seed`, `chain.A4.quest_seed` | `low:high` | A4 game draws 3 and 4 | chain |
| `chain.A4.game_seed_after_creation` | `low:high` | A4 the game seed after draw 4 | chain |
| `chain.B1.level_seed_base.N` | int | B1 `levelSeedBase` of act N | chain, [rng/seeds](../specs/rng/seeds.md) |
| `chain.B2.level_seed.N` | `low:high` | B2 create seed of level N, `base + id` | chain, rng/seeds |
| `chain.B2.level_seeds_digest` | sha256 | B2 over `{level id: seed}` for every level with a seed | chain |
| `monsters.pool.mlvl.N`, `.den.N`, `.uniques.N`, `.region.N` | int, int, `[min, max]`, class ids | monster level, density, unique range, region pool of level N for the case's difficulty and game type | [monsters/pool](../specs/monsters/pool.md) |
| `monsters.pool.digest` | sha256 | the four values above, every level | monsters/pool |
| `chain.G1.nodrop` | `[[NoDrop, total], ...]` | G1 NoDrop scaling per roll | [items/tc § F](../specs/items/tc.md) |
| `chain.G1.pick` | `[[range, roll], ...]` | G1 the pick draw per selection | [items/tc § E](../specs/items/tc.md) |
| `chain.G1.select` | `[index, ...]` | G1 the entry each pick selects | items/tc § E |
| `chain.G1.subtc` | `[tc, ...]` | G1 sub-classes entered, in order | items/tc § G |
| `chain.G1.quality` | `[q, ...]` | G1 quality rolled per item | [items/quality](../specs/items/quality.md) |
| `chain.G1.item` | `[[base, quality, unique/set index], ...]` | G1 item hand-off | items/tc § H |
| `chain.G1.count` | int | G1 items made (`TCEND`) | items/tc |
| `chain.G1.end_seed` | `low:high` | G1 the dying unit's seed at `TCEND` | items/tc |
| `drlg.outdoor.seed_after` | `low:high` | the level seed after the outdoor window (`OD1`) | [drlg/outdoor](../specs/drlg/outdoor.md) |
| `drlg.outdoor.presets_digest`, `.preset_count` | sha256, int | the preset anchors `OutdoorRoomsCreate` makes, each `[def, x, y, file index, grid0 flags]`, in order | drlg/outdoor |
| `drlg.outdoor.rooms_digest`, `.room_count` | sha256, int | the out rooms, each `[x, y]` (the rect origin the room-link line logs), in creation order | drlg/outdoor |
| `drlg.maze.seed_after` | `low:high` | the level seed after the maze window (`MZ1`) | [drlg/maze](../specs/drlg/maze.md) |
| `drlg.maze.rooms_digest`, `.room_count` | sha256, int | the rooms `[x, y, w, h, def, forced index]` in creation order, positions relative to the bounding box's minimum | drlg/maze |

Observed `world` cases hold only the fields their log shows (`GAME`, `OGC`, `LC0` lines); predicted ones
hold every `world` field, with the level singles for the levels they name. Both mean the same by a field name.
The field meanings carry the confidence of the spec rows they test (reviewed `[C]` in chain and items/tc);
a reimplementation that matches an observed case has matched the real game for that field. [C]
(run:2026-10-21-chain2, `golden.py emit`)

## Checking

`golden.py check SET CANDIDATE`: the candidate is JSON Lines, one `{"id": ..., "outputs": {field: value}}` per case
(a full case line of a set, with `expected`, is read the same way, so a set checks against itself). Values compare
as canonical JSON. The report counts compared and different fields per field pattern, prints the first differences of
each failing case (with its `kind` and `quirks`), and lists missing cases; exit 0 only when nothing differs and no
case is missing. `--fields PREFIX` restricts the comparison. [C] (`tools/test_golden.py`: pass against itself, fail on
one altered field, fail on a missing field and a missing case)

`golden.py digest SET` prints the set's identity: sha256 over the header's `golden`, `version`, `game_exe_sha256`,
`tables_digest` and `scope`, then the canonical case lines ordered by `id`. Two people with the same table set and
logs regenerate the same digest.

A reimplementation's `drlg.*.rooms_digest` is the digest of its own list in the same order and form: `golden.py digest
--value` over the JSON list (`[[x, y, ...], ...]`), so the digest is the whole comparison and a mismatch does not say which
room differs; the set's `inputs` and a replay of the kept log do. [I] (a convention of this format)

## Making a set

- Observed: `golden.py emit --out SET --run run:<id> LOG...` reads each kept log (`# d2run` header for the seed;
  `GAME`, `OGC`, `LC0` lines; the `TCR .. TCEND` calls through `tools/tc.py`), compares the world values with
  `tools/chain.py gen`, replays every drop call through `tools/tc.py` with the quality roll modelled, and writes only
  the cases that reproduce; any that does not is counted and makes the exit code 1. `--chain-check` also runs
  `tools/chain.py check` on the same logs and fails on a non-zero exit.
- DRLG: `golden.py emit --drlg --out SET LOG...` finds the `OD0 .. LI1` windows and the `MZ0 .. MZ1` windows of each
  log, replays each through `tools/drlg.py` (the outdoor generators with the act link builder, Act III's jungle layout
  included) or `tools/maze_replay.py`, and writes a case only when the model's seed after the window and its list agree
  with the log. A window already written from an earlier log (same map seed, difficulty, level and window seed; maze:
  same level and seed) is not written twice. A log whose `-seed` is 0, negative or past 2^31-1 is skipped: the game does
  not use it as the map seed (drlg experiments, `sweep-roomk` s9 and s10). Maze windows of level types
  `tools/maze_replay.py` does not model are counted and skipped.
- Predicted: `golden.py emit --predicted --seeds 4802,100-103 --diffs 0,1,2 --exps 0,1 --levels 1,57`.
- `merge` joins sets (cases by id; the scope is the union); `coverage` prints, per field pattern, the observed and predicted
  cases and the distinct levels reached.
- `sample` takes a spread subset (worlds by difficulty and game type, DRLG windows by generator and level (outdoor and maze half and half), drops by difficulty, game type, item or none,
  sub-class depth); `merge` joins sets of one header.

Nothing in a case is a table row or file bytes: seeds, indices, codes, counts, class ids of a region pool (as in the
chain worked example) and digests. This is by construction of the field list, which holds no string field, and the sample holds no string value except two `monster_flags` bytes. [I]

## Evidence

- `python3 -I tools/test_golden.py`: 15 tests, no game file.
- run:2026-10-21-chain2, 37 kept logs (`p2-s1-*.log` without the `raven-xn` one, `p2r2-s1-*.log`): `golden.py emit
  --chain-check` wrote 37 observed `world` cases and 3 784 observed `drop` cases (0 calls failed or cut off) and
  `tools/chain.py check` exited 0 with 37 logs, 0 sub-checks failed; `golden.py check` of that set against itself
  passes. The sample set was drawn from it and from a predicted grid (seeds 4802 and 12345, Normal and Hell, both game
  types, levels 1, 57, 103). The full set is regenerated locally; its digest is recorded in the plan log, not the
  set. [C]

## Set v1: coverage per spec step

The full set is built locally (`workspace/golden-v1-full.jsonl`, about 13 MB, never in git; the sample holds 28 cases of it,
and the 8 predicted worlds of the sample are in the grid). Counts are by `golden.py coverage` (`[C]`, by script; the
cases per field, a case counted once per pattern it holds). Its digest and the digests of its four parts are in
[the inventory](../inventory.md#golden-trace-set-v1-plan-0059-phase-2).

| Part | Cases | Source |
|---|---|---|
| observed `world` + `drop` | 37 + 3 784 | run:2026-10-21-chain2, 37 kept logs; `chain.py check` exit 0 |
| observed `drop` | 256 | run:2026-10-15-items-chain, the 8 stock logs with a drop (`ichain-2701..2709`; 9 logs checked, no creation in one) |
| observed `drlg` | 334 outdoor + 50 maze | 112 kept logs of the DRLG runs of plans 0022 and 0026 and later runs that log `OD0` or `MZ0` |
| predicted `world` | 612 | seeds 4802, 5001 to 5100 and 12345 x 3 difficulties x 2 game types, 86 levels (those the chain2 logs created) |

| Spec step (field pattern) | Observed | Predicted |
|---|---|---|
| A1 `game_seed`, `map_seed` | 37 | 612 |
| A2 `monster_regions_seed`; A4 `store_seed`, `quest_seed`, `game_seed_after_creation`; B2 `level_seeds_digest`; `monsters.pool.*` | 0 | 612 (pool singles: 86 levels each) |
| A3 `object_region_seed`, `game_seed_after` | 37 | 612 |
| B1 `level_seed_base.N` | 63 (5 acts) | 3 060 |
| B2 `level_seed.N` | 624 (86 levels) | 52 632 |
| G1 `nodrop`, `pick`, `select`, `subtc`, `quality`, `item`, `count`, `end_seed` | 4 040 each | 0 |
| `drlg.outdoor.*` | 334 each (27 levels: 2 to 7, 17, 39, 41 to 45, 76 to 81, 104 to 106, 108, 110 to 112, 117) | 0 |
| `drlg.maze.*` | 50 each (12 levels: 8 to 12, 34 to 36, 47 to 49, 65) | 0 |

Gaps, all stated: the chain2 logs do not show the A2 and A4 draws or the pool values, so those fields are predicted only
(a reimplementation matches the model, not a kept log); the drop cases are the calls that were logged (all three difficulties and both game types occur: Normal 742 classic and
1 436 expansion, Nightmare 478 and 752, Hell 169 and 463; items-chain is Hell expansion only), no more; the outdoor levels
not in the list are in no kept log that reproduces; maze windows of level types other than 3, 10 and 13 (the three
`tools/maze_replay.py` models: caves, catacombs, Act II sewers; 184 windows over the kept logs) are not cases; the forced-variant items-chain logs (`ichainf`, `ichainh`: edited `itemratio`) are not cases, since their drop
rolls hold only on the edited table; no DRLG case is predicted (the generators are checked against windows of logs
only); a window that fails to reproduce is never written (0 did in the full run). Item seeds after the drop and room
populations stay for a later set version.

## Open questions

- Version 1 has no field for the item seeds after the drop (G2/G3, the item's builder) or for room populations
  (chain § D–E); both are in the kept logs and can be added as fields in a later version of the set (not of the
  format). The drop's `chain.G1.item` stops at the base item and quality.
- `game_exe_sha256` and `tables_digest` are not checked by `check`; a mismatch of the table set is the reader's to
  compare.
