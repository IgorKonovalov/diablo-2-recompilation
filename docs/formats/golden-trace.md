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
| `quirks` | list of strings | ids from the quirks catalogue ([plan 0057](../plans/done/0057-quirks-catalogue.md)) of the quirks that change an output of this case. Reserved: version 1 files carry `[]`, and `emit` never invents an id. A mismatch report prints a failing case's ids so the implementer sees which trap it hit |

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
  `fq`, `super_unique`, `killer_type`, `killer_class`, `g6a`, `players`, `party`, `cap`, `killer_mf`, `owner_mf` (the last five when the log
  shows them; § Conventions says what each means and what an absent one means). All are the `TCR` line's and its context
  lines' ([tc § D](../specs/items/tc.md#d-the-resolver--tc_resolvedrops)); the two magic-find values are the `QKMF` and `QOMF` lines'.

- `drlg`: `generator` (`outdoor` or `maze`), `map_seed` (the `-seed` of the log), `level` (the level id), `window_seed`
  (the level seed at the window's opening line, `OD0` or `MZ0`); outdoor adds `difficulty` (0 to 2; the replayer's, read from the
  log's name, since a log does not show it; it selects the level sizes) [I]: `hell` in the name is 2, `nightmare` 1, else 0, so the 67 outdoor cases of logs whose name carries neither word rest on the default (a wrong difficulty that changed a level size would not have reproduced; one that did not is unchecked), maze adds `first_room_seed` (`low:high`, the
  room seed the window starts the first room from, from the log's preceding `RC` line, as `tools/maze_replay.py` takes it: [drlg/maze](../specs/drlg/maze.md) B1's seed, `Init(window_seed.low)` then one `Step`, **before** any growth step; it is a function of `window_seed`, so a reimplementation may derive it). A maze case carries no `difficulty`: the 12 maze levels of the v1 set (8–12, 34–36, 47–49, 65) have equal `LvlMaze` `Rooms`, `Rooms(N)` and `Rooms(H)`, so the case holds for all three `[C]` (by script over `lvlmaze.txt`, 2026-11-10); a set with another maze level would need the input.
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
| `chain.B1.level_seed_base.N` | int | B1 `levelSeedBase` of act N (1 to 5) | chain, [rng/seeds](../specs/rng/seeds.md) |
| `chain.B2.level_seed.N` | `low:high` | B2 create seed of level N, `base + id` | chain, rng/seeds |
| `chain.B2.level_seeds_digest` | sha256 | B2 over `{level id: seed}` for every level with a seed (levels 1 to 136; § Conventions) | chain |
| `monsters.pool.mlvl.N`, `.den.N`, `.uniques.N`, `.region.N` | int, int, `[min, max]`, class ids | monster level, density, unique range, region pool of level N for the case's difficulty and game type | [monsters/pool](../specs/monsters/pool.md) |
| `monsters.pool.digest` | sha256 | the four values above, every level (1 to 136; § Conventions) | monsters/pool |
| `chain.G1.nodrop` | `[[NoDrop, total], ...]` | G1 NoDrop (after F's scaling) and total, one entry per positive pick (§ Conventions) | [items/tc § D4, F](../specs/items/tc.md) |
| `chain.G1.pick` | `[[range, roll], ...]` | G1 the pick draw per positive pick, `roll` before `− nd` | [items/tc § E](../specs/items/tc.md) |
| `chain.G1.select` | `[index, ...]` | G1 the entry each pick selects | items/tc § E |
| `chain.G1.subtc` | `[tc, ...]` | G1 sub-classes entered, in order | items/tc § G |
| `chain.G1.quality` | `[q, ...]` | G1 quality rolled per item | [items/quality](../specs/items/quality.md) |
| `chain.G1.item` | `[[base, quality, unique/set index], ...]` | G1 item hand-off | items/tc § H |
| `chain.G1.count` | int | G1 items made (`TCEND`) | items/tc |
| `chain.G1.end_seed` | `low:high` | G1 the dying unit's seed at `TCEND` | items/tc |
| `drlg.outdoor.seed_after` | `low:high` | the level seed after the outdoor window (`OD1`) | [drlg/outdoor](../specs/drlg/outdoor.md) |
| `drlg.outdoor.presets_digest`, `.preset_count` | sha256, int | the preset anchors `OutdoorRoomsCreate` makes, each `[def, x, y, file index, grid0 flags]` (`x`, `y` the preset rect origin the `PRC` line logs, in absolute tiles, as the room rects are), in order | drlg/outdoor |
| `drlg.outdoor.rooms_digest`, `.room_count` | sha256, int | the out rooms, each `[x, y]` (absolute tiles, `L.rect.x + 8·cx`, the rect origin the room-link line logs; [drlg/overview](../specs/drlg/README.md) step 8), in creation order, `x` and `y` absolute tiles | drlg/outdoor |
| `drlg.maze.seed_after` | `low:high` | the level seed after the maze window (`MZ1`) | [drlg/maze](../specs/drlg/maze.md) |
| `drlg.maze.rooms_digest`, `.room_count` | sha256, int | the rooms `[x, y, w, h, def, forced index]` in list order (newest first, [drlg/maze](../specs/drlg/maze.md) § Outputs), `x` and `y` absolute tiles minus the bounding box's minimum | drlg/maze |

Observed `world` cases hold only the fields their log shows (`GAME`, `OGC`, `LC0` lines); predicted ones
hold every `world` field, with the level singles for the levels they name. Both mean the same by a field name.
The field meanings carry the confidence of the spec rows they test (reviewed `[C]` in chain and items/tc);
a reimplementation that matches an observed case has matched the real game for that field. [C]
(run:2026-10-21-chain2, `golden.py emit`)

## Conventions

What `tools/golden.py` does where the field table is silent. A reimplementation that reads the table alone has to guess
these; each is the tool's behaviour (`world_expected`, `observed_world`, `drop_case`, `cmd_check`, `value_digest`), read
from the code and, where a drop input or list comes from a logger line, from `tools/gdb/tc-drops.gdb`. [C] (`tools/golden.py`;
the logger lines: `tools/gdb/tc-drops.gdb`, run:2026-10-21-chain2)

### World cases

- **The act index.** The `N` of `chain.B1.level_seed_base.N` is the **act number, 1 to 5**, not the 0-based act index of
  [rng/seeds](../specs/rng/seeds.md) (`world_expected` writes `a["act"]`, which `tools/chain.py gen` sets to the index plus 1). A level's act
  for an observed case is by id: levels below 40 are act 1, 40 to 74 act 2, 75 to 102 act 3, 103 to 108 act 4, 109 and above act 5
  (`chain.act_of`). The `N` of every other `.N` field is a level id.
- **Which acts and levels a case holds.** A predicted `world` case holds the `levelSeedBase` of **all five acts**, classic games
  too (`gen` loops `range(5)` whatever `expansion` is), and, for each id in its `levels` input that the pool builder has, the level
  singles (`level_seed.N`, `pool.mlvl.N`, `.den.N`, `.uniques.N`, `.region.N`); `level_seed.N` only when the level has a seed (all 136 do). An observed
  `world` case holds only what its log shows: `A1` game seed and map seed; `A3` when the log has an `OGC` line; the `levelSeedBase`
  of the acts of the levels its `LC0` lines name, each equal to the one `base` the log prints (a log that shows no `base` has none);
  `level_seed.N` for every level its `LC0` lines name. It holds no pool, digest, `A2` or `A4` field.
- **Extra fields are not compared.** `check` walks the case's `expected` fields only: a candidate output field the case does not
  hold is ignored, and a candidate case the set does not hold is a note, not a difference (§ Checking). So an implementation
  may emit every field it has for every case; only a field the case holds, missing or different, counts.
- **The digests' level set.** `chain.B2.level_seeds_digest` covers every level of `tools/chain.py gen` that has a seed, and
  `monsters.pool.digest` every level `gen` lists: both are **levels 1 to 136, 136 levels**, the same ids for both game types and all
  three difficulties (checked for seed 4802, both game types, Normal and Hell, by script). The digest does not depend on the case's
  `levels` input (a case's `levels` only picks the singles).
- **The digested object and its canonical form.** The object is a JSON dictionary with the level id as a **decimal string key**.
  B2: `{"1": "low:high", ...}`, the value the level's seed in `low:high`, 8 lower-case hex digits each. Pools: `{"1": [mlvl, den, uniques_min, uniques_max, [class id, ...]], ...}`
  (the region pool's class ids: the kept (`isSpawn`) entries in append order, [monsters/pool](../specs/monsters/pool.md) § C8 and § Outputs, as `.region.N` lists them; `mlvl` the `.mlvl.N` value, `den` the `.den.N` value).
  Canonical JSON: keys sorted (as strings, so `"10"` before `"2"`), separators `,` and `:` with no spaces, non-ASCII escaped (none occurs), UTF-8;
  the digest is the sha256 of those bytes as 64 lower-case hex digits (`golden.py digest --value` reads the object from standard input).

### Drop cases

Every list is built by `drop_case` from the call's logger lines, `TCR` to `TCEND`, in the order they were logged.

- **`chain.G1.nodrop`**: one entry **per positive pick**, `[NoDrop, total]`, from the `NDP` line (logged at `0x0055A9D9`, where every
  positive-picks path joins, with `noNoDrop` set too). `total` is the TC's `Prob` total for the game type
  (`T`); `NoDrop` is the value of [items/tc § D4](../specs/items/tc.md) as the range uses it: the TC's NoDrop after F's scaling
  (unscaled when the party count `n` is 1 or less) and **0 when the TC's NoDrop is 0** (the entry is then `[0, total]`; F is not
  called, and the pick still has its entry). It is not one entry per `ScaleNoDrop` call: a TC with NoDrop 0 contributes entries, and a pick that
  F scales and a pick it does not both contribute exactly one. Negative picks (no draw) contribute none.
- **`chain.G1.pick`**: one `[range, roll]` per positive pick (the `PICK` line): `range` the argument of the pick's `Range` draw (`T + nd`, or `T` with
  `noNoDrop`), `roll` its **raw result, before `− nd`**. A negative pick has no entry. A pick whose roll is below `nd` (a NoDrop) is listed.
- **`chain.G1.select`**: one index per `SEL` line, the entry index the pick's roll selects in the TC: NoDrop picks are not listed (they never reach the
  selection), negative picks are, and an index at or past the entry count (a miss: the pick is consumed, nothing is made) is recorded as it was.
- **`chain.G1.subtc`**: one TC index per `SUB` line, in the order the sub-TCs are entered (pushed); the TC the call starts with (`tc`) is not listed.
- **`chain.G1.quality`**: one code per `QOUT` line, i.e. per `DropRollQuality` exit, in call order. A pick of a classic throwable that the game
  refunds has rolled first and is listed; a unique or set entry makes no quality roll and is not (its quality is in `chain.G1.item`). A forced quality
  (`fq` not 0) also logs a `QOUT` (the logger's exit point is the join of both paths; `tools/tc.py` expects it), so it would be listed [I]; none of the v1 set's 4 040 calls has `fq` not 0, so no run exercised it.
- **`chain.G1.item`**: one `[base, quality, unique/set index]` per `CPRE` line (an item hand-off); `count` is the `TCEND` count and `end_seed` its seed.
- **Input `tc`** is the TC index the resolver is entered with (`TCR`'s `tc`), i.e. the resolver's `t0` of [items/tc § D1](../specs/items/tc.md)
  **after** the caller's level upgrade: there is no upgrade to apply before the draws. (`ilvl` is likewise the resolver's.)
- **`players`, `party`, `cap`.** `PLAYERS` (the alive player count, or the `/players` override when it is larger, F2), `PARTY` (the party count after the clamp, F1) and, only for a
  monster source (`source_type` 1), `CAP` (the cap F2 applies) are logged **at each positive pick whose TC has NoDrop not 0**, just before
  the scaling; the case keeps the last value of each in the call. An input is absent when no pick of the call had NoDrop
  not 0 (or, for `cap`, the source is an object): nothing in the call then reads it. A reimplementation derives it from the
  game state as F1–F2 say; a case that holds it gives the value the game used, so a harness can take it as given.
- **`killer_mf`, `owner_mf`.** The killer's own stat 80 (`QKMF`) and, when `MonsterOwner` returns a unit, **its owner's** stat 80 (`QOMF`):
  the two terms [items/quality M1–M4](../specs/items/quality.md) add (`DropMagicFind` = killer + owner; for a mercenary or a summon both are logged and the
  owner's is `owner_mf`, never folded into `killer_mf`). Both are inputs of every quality roll of the call, which has one killer, so `emit` requires every logged value of a call to agree
  and every logged `QMF` (the sum the roll uses) to equal `QKMF + QOMF`, and writes **no case** for a call that breaks either (it counts as failed). An input is **absent** when no
  roll read the stat: the call made no quality roll, or the killer is none or of a type above 1 (M1: the magic find is then 0 and the game does not read the stat), or, for `owner_mf`, the killer has no owner.
  A reimplementation uses 0 for an absent value. In the v1 set 486 of the 4 040 drop cases hold `killer_mf` (the value 472 in 309 expansion cases, 250 in 174 and 215 in 3 classic cases; every killer a player, `killer_type` 0) and none holds `owner_mf` (no call of the set has a roll with an owned killer) (`[C]`, by script).
- **Context only.** `game_seed`, `killer_type`, `killer_class`, `source_class`, `monster_flags`, `super_unique` and `source_type` identify the call; no step of D–H reads them once
  `tc`, `players`, `party`, `cap`, `killer_mf` and `owner_mf` are given [I]. The inputs the draws use are `tc`, `ilvl`, `unit_seed`, `difficulty`, `expansion`
  (which TC total and entry flags apply), `nonodrop`, `max`, `fq` and the five derived values above. `unit_seed` and `game_seed` are written `low:high`.
- **`g6a`** is the game's type byte, `Game+0x6A` (`game.type` in [items/tc § Runtime state](../specs/items/tc.md#runtime-state): 3 single-player, 2 a TCP/IP host). It gates the `/players`
  override in `players`; with `players` given, a reimplementation does not need it.

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
  `tools/maze_replay.py` does not model are counted and skipped. A log can therefore write no case without a fault: of the 133 logs with an `OD0` or `MZ0` line in the v1 build, 21 wrote none,
  the 2 skipped for their `-seed` and 19 whose outdoor windows (and duplicate or unmodelled maze windows) an earlier log of the list had already written (`[C]`, by script, 2026-10-30; which log writes a shared window depends on the order of the list).
- Predicted: `golden.py emit --predicted --seeds 4802,100-103 --diffs 0,1,2 --exps 0,1 --levels 1,57`.
- `merge` joins sets (cases by id; the scope is the union); `coverage` prints, per field pattern, the observed and predicted
  cases and the distinct levels reached.
- `sample` takes a spread subset (worlds by difficulty and game type, DRLG windows by generator and level (outdoor and maze half and half), drops by difficulty, game type, item or none,
  sub-class depth); `merge` joins sets of one header.

Nothing in a case is a table row or file bytes: seeds, indices, codes, counts, class ids of a region pool (as in the
chain worked example) and digests. This is by construction of the field list, which holds no string field, and the sample holds no string value except two `monster_flags` bytes. [I]

## Evidence

- `python3 -I tools/test_golden.py`: 16 tests, no game file.
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
