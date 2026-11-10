# Plan 0066 inventory: stats/README

- **Spec:** [stats/README](../../specs/stats/README.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 3; the *Count* column sums to 3.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 54 | Entry points | An item is equipped, unequipped, or the requirements are … — for the refresh ( 972 refreshes); for the attach … | `fn:ITEMS_AttachToOwner@0x0055C2C0` | a-logs | the LNK/ULK lines with their `ra2` caller chains in the s1017 logs of run:2026-10-17-stats: each attach and detach's link sequence against H1, H2 | S4d | 1 |
| 2 | 59 | Entry points | A shrine or a well is operated — (15 operates over and , a named shortfall) | run:2026-10-17-stats | a-run | `stats.gdb` with `stats_sessions.py` `objop` sessions at more shrines and wells (16 and 5 operates, under 20) | H4e | 1 |
| 3 | 100 | Draw order | The draw is one per run whatever the number of units hit: do 66 makes … | – | b | a new line in `AuraHitUnitCb` counting the units each Sanctuary run hits, with the caster's seed (a crowd field session) | H4e | 1 |

**Totals by class:** a-logs 1, a-run 1, b 1 (sum 3).
