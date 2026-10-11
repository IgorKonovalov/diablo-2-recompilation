# Findings

Raw reverse-engineering notes from `reverser`, grouped by subsystem directory (`rng/`, `items/`,
`monsters/`, `drlg/`…). One file per topic: `NNNN-topic.md`, numbered within the directory. Findings
are the evidence layer that specs cite. They may hold decompile excerpts of *our* binary,
addresses, hypotheses and dead ends.

## Index

| Finding | Subsystem | Status |
|---|---|---|
| [rng/0001-rng-core](rng/0001-rng-core.md) | rng | answered: step, range and init `[C]` |
| [rng/0002-seed-tree](rng/0002-seed-tree.md) | rng/seeds | open: game → act → level → room → unit chain `[I]` |
| [rng/experiments](rng/experiments.md) | rng | `run:2026-10-11-rng-emu` |
