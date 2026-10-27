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

*Annotation (spec-writer, 2026-10-20, `lane/s38h2b`, plan 0038 Phase 3, items/affixes cluster):* **done in part.** (h)–(n) applied to [items/affixes](../specs/items/affixes.md): `TYPE_JEWEL` and its *Constants* note, C5a (split from C5b, which stays `[I]`) and its two notes, D3, E3 and its note, R1, R3 and their note, the E2 name-failure fallback `[C]` with E5's "no affix" cause and the discard `[I]` (E5 restated as having no stock case). **Open:** (a)–(g) and (o)–(s), for items/tc (waits for H2c), items/uniques-sets (H1a), items/properties (H2c) and items/sockets-runewords (H6b).

*Annotation (spec-writer, 2026-10-21, `lane/s38h2c`, plan 0038 Phase 3, items/tc and items/properties clusters):* **done in part.** (a) the H7 seed note split (`[C]` by run:2026-10-20-sweep-items-chain, the classic refusal `[I]`) and (b) the *Outputs* creation-call bullet `[C]` in [items/tc](../specs/items/tc.md); (o) the F4 `tors` line and note `[C]`, (p) the `dur%` note kept `[I]` with the shortfall, (q) the A5 note restated as no stock case, the A5 and H3 lines `[I]`, in [items/properties](../specs/items/properties.md). **Open:** (c)–(g) for items/uniques-sets (H1a) and (r)–(s) for items/sockets-runewords (H6b).

*Annotation (spec-writer, 2026-10-27, `lane/s38s`, plan 0038 Phase 3, items/uniques-sets cluster):* (c)–(g) applied
to [items/uniques-sets](../specs/items/uniques-sets.md): the oracle table splits the superior builder (`[C]` as a
fallback entered at `{S, 666}`, `[I]` from a failed unique or set) from the normal builder (`[I]`); A1–A2 `[C]`; E2's
steps past the first `[C]` up to a successful superior step, the failing superior step, the normal step and `Rare` 0
`[I]`; the draw-order note on the game and unit seeds `[C]`; A3 stays `[I]` with no stock item of type 11. **Open:**
(r)–(s), for items/sockets-runewords (H6b).
