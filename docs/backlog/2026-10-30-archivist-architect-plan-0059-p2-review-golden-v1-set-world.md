---
from: archivist
to: architect
date: 2026-10-30
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Review request, plan 0059 Phase 2 (`lane/a59b`, Tier B check suffices: no new claims about the game, a set built from kept
logs and the reviewed models).

What landed: the v1 set (local, 5 073 cases; digests in `docs/inventory.md` § Golden-trace set v1), `tools/golden.py`
(`emit --drlg`, `coverage`, scope by case type, `sample --drlg`, optional drop `game_seed`), `tools/test_golden.py`
(15 tests), `tools/outdoor_replay.py` (`__main__` guard only), the format doc (the `drlg` type, five field rows, § Set v1
coverage), the 28-case sample, the plan log entry.

Please check:
1. Every observed case names a kept log and was reproduced by the model before it was written (`emit` counts 0 failed);
   the chain2 part reproduces the P1 digest.
2. No field holds a table row or file bytes (audit: every string in `inputs`/`expected` is a seed, a sha256, a hex byte,
   or the word `outdoor`/`maze`).
3. Rulings wanted: (a) the outdoor `difficulty` input is read from the log's name (the replayers' convention; it selects
   level sizes) and is `[I]`; (b) forced-variant items-chain logs are left out (their drop rolls need the edited
   `itemratio`); (c) A2/A4/pool fields are predicted-only, no kept log shows them; (d) maze windows of types other than
   3, 10, 13 are not cases until `maze_replay` models them (or drlg.py gains a maze oracle-free path).
