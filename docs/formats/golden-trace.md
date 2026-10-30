# Golden trace (`.jsonl`)

Owned by `archivist`. A golden trace is a file of conformance cases: a seed and its inputs, with the values the
reviewed specs say follow from them. A reimplementer runs the cases, writes its own outputs in the same field names
and compares them with `tools/golden.py check`. This is our own format, not a game format; it has no
game-side evidence, only the evidence of the cases it holds ([plan 0059](../plans/0059-golden-traces.md) Phase 1).
Tool: `tools/golden.py`; tests: `tools/test_golden.py`. Sample set:
[golden/sample-v1.jsonl](golden/sample-v1.jsonl) (22 cases).

**Scope of version 1:** the chain's world (game creation, act and level seeds, monster-region pools) and the drops
of `TC_ResolveDrops` calls (scope string `world,drops`). Events (AI, skills, combat, frame windows) are version 2.

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
| `scope` | string | the subsystems the cases cover, `"world,drops"` in version 1 |
| `game_exe_sha256` | string or null | the pinned `Game.exe` ([inventory](../inventory.md#pinned)); null when the inventory is not readable |
| `tables_digest` | string or null | sha256 over the sorted lines `<lower-case name> <sha256>` of every file of `data/global/excel`: the table set the cases were built on. Differs between table sets, so two people compare it before comparing results |
| `case_kinds` | list | `["observed", "predicted"]` |

The header holds no date or path, so a set's digest is reproducible.

### Case

| Key | Type | Meaning |
|---|---|---|
| `id` | string | unique: `world:o:<log>`, `drop:o:<log>:<call>` (observed), `world:p:<seed>:d<diff>:e<exp>` (predicted) |
| `kind` | `observed` or `predicted` | see below |
| `type` | `world` or `drop` | which inputs and fields the case has |
| `source` | object | observed: `log` (file name), `log_sha256` (first 16 hex of the kept log), `run` (the experiment record, when given), `call` (a drop's index among the log's TC calls). Predicted: `model` (the tool that produced it) |
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

## Making a set

- Observed: `golden.py emit --out SET --run run:<id> LOG...` reads each kept log (`# d2run` header for the seed;
  `GAME`, `OGC`, `LC0` lines; the `TCR .. TCEND` calls through `tools/tc.py`), compares the world values with
  `tools/chain.py gen`, replays every drop call through `tools/tc.py` with the quality roll modelled, and writes only
  the cases that reproduce; any that does not is counted and makes the exit code 1. `--chain-check` also runs
  `tools/chain.py check` on the same logs and fails on a non-zero exit.
- Predicted: `golden.py emit --predicted --seeds 4802,100-103 --diffs 0,1,2 --exps 0,1 --levels 1,57`.
- `sample` takes a spread subset (worlds by difficulty and game type, drops by difficulty, game type, item or none,
  sub-class depth); `merge` joins sets of one header.

Nothing in a case is a table row or file bytes: seeds, indices, codes, counts, class ids of a region pool (as in the
chain worked example) and digests. This is by construction of the field list, which holds no string field, and the sample holds no string value except two `monster_flags` bytes. [I]

## Evidence

- `python3 -I tools/test_golden.py`: 10 tests, no game file.
- run:2026-10-21-chain2, 37 kept logs (`p2-s1-*.log` without the `raven-xn` one, `p2r2-s1-*.log`): `golden.py emit
  --chain-check` wrote 37 observed `world` cases and 3 784 observed `drop` cases (0 calls failed or cut off) and
  `tools/chain.py check` exited 0 with 37 logs, 0 sub-checks failed; `golden.py check` of that set against itself
  passes. The sample set was drawn from it and from a predicted grid (seeds 4802 and 12345, Normal and Hell, both game
  types, levels 1, 57, 103). The full set is regenerated locally; its digest is recorded in the plan log, not the
  set. [C]

## Open questions

- Whether an observed case should also carry the 852-site RNG call counts (a strong check, tied to the binary's
  inlining): the plan's open question, for the Phase 1 review.
- Version 1 has no field for the item seeds after the drop (G2/G3, the item's builder) or for room populations
  (chain § D–E); both are in the kept logs and can be added as fields in a later version of the set (not of the
  format). The drop's `chain.G1.item` stops at the base item and quality.
- `game_exe_sha256` and `tables_digest` are not checked by `check`; a mismatch of the table set is the reader's to
  compare.
