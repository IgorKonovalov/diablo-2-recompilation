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
| [data/0001-excel-loader](data/0001-excel-loader.md) | data/excel | answered: `.bin` always read (`-txt` compiles, `-direct -txt` to use it), 86/88 tables registered with matching record sizes `[C]`, TCEx is the live TC table `[C]`, code/name links `[I]` |
| [data/0002-mpq-precedence](data/0002-mpq-precedence.md) | data/excel | answered: MPQ order and priorities, loose files only under `-direct`, `data\local\use` = language id `[I]` |
| [items/0001-tc-resolution](items/0001-tc-resolution.md) | items/tc | open: drop path, TC choice, picks, NoDrop, recursion, hand-off `[I]`; runtime TC layout `[C]`; Phase 1b/2 pending |
