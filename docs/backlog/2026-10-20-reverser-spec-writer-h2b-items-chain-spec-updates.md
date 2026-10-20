---
from: reverser
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../findings/items/0001-tc-resolution.md#plan-0038-batch-h2b-2026-10-20
  - ../findings/items/0004-uniques-sets.md#plan-0038-batch-h2b-2026-10-20
  - ../findings/items/0005-affixes.md#plan-0038-batch-h2b-2026-10-20
  - ../findings/items/0006-properties.md#plan-0038-batch-h2b-2026-10-20
  - ../findings/items/0007-sockets-runewords.md#plan-0038-batch-h2b-2026-10-20
resolution: ""
---

After the architect accepts H2b (run:2026-10-20-sweep-items-chain; the ledgers are the "Plan 0038 batch H2b" sections of [items/0001](../findings/items/0001-tc-resolution.md#plan-0038-batch-h2b-2026-10-20), [0004](../findings/items/0004-uniques-sets.md#plan-0038-batch-h2b-2026-10-20), [0005](../findings/items/0005-affixes.md#plan-0038-batch-h2b-2026-10-20), [0006](../findings/items/0006-properties.md#plan-0038-batch-h2b-2026-10-20) and [0007](../findings/items/0007-sockets-runewords.md#plan-0038-batch-h2b-2026-10-20)), for the Phase 3 re-tag. Spec lines are those of the inventories' commits (tc `a398945`; affixes, uniques-sets, properties `3b1433f`; sockets-runewords `c3167c6`).

items/tc: (a) H7 (L669) the item seed of a drop from the game seed `[C]`; the classic `version ≥ 100` refusal stays `[I]` (split). (b) L768 one creation call per item, `game.seed` stepped `[C]`.

items/uniques-sets: (c) L150 the superior builder as a fallback oracle `[C]` (after a failed rare and magic step); "never reached from a failed unique or set" stays `[I]`, the normal builder too (split; the "in the runs" wording is out of date for the superior builder). (d) A1–A2 (L175) `[C]`. (e) E2 (L439) the steps past the first `[C]` up to a successful superior step; a failing superior step, the normal step and `Rare` 0 stay `[I]` (split; "were not reached" is out of date). (f) L511 `[C]`. (g) A3 (L181) stays `[I]`, d-none ("None was logged" can say no stock item is of type 11).

items/affixes: (h) Constants L124 `TYPE_JEWEL` `[C]`. (i) C5a (L293) and its note (L341) `[C]`. (j) D (L384) `[C]`. (k) E3 (L415) and its note (L466) `[C]`. (l) R1 (L442), R3 (L447) and the note (L463) `[C]`. (m) L483 the fallback to magic with `{S, 666}` `[C]`; the "no affix" cause and the discard stay `[I]` (split). (n) E5 (L431) stays `[I]`, d-none.

items/properties: (o) F4's tors line (L547) and the F4 note (L591) `[C]`; F4's "not reached in the runs" is **out of date**. (p) L823 stays `[I]` (shortfall, no superior ethereal `dur%` item). (q) A5 line (L213), A5 note (L252), H3 (L647) stay `[I]`, d-none.

items/sockets-runewords: (r) F1 (L521) `[C]` for the cap's steps (size and 6, quality for normal and superior, `ItemMaxSockets`) and their order; the write's clamp (`max(n, 1)`, then the cap) stays `[I]`, since every request lay in `1..cap` (review scope, 2026-10-20), as do the quality branches and `cap < 1` (split). (s) L544 ("the run did not execute its clamps") is **out of date** for the drop path; normal and superior get no quality clamp `[C]`; row 44's own S2c status otherwise unchanged. *Released at the `lane/h2b` review (2026-10-20, accepted with fixes); item (r) as scoped there.*
