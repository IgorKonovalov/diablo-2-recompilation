---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/items/sockets-runewords.md
  - ../../specs/items/properties.md
  - ../../wiki/items-other-paths.md
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (8: overclaim 4, misread 1, under-claim 1, omission 1, miscount 1). items/sockets-runewords {C 129, I 85, L 7}; items/properties {C 153, I 22, L 3}. Rulings: F6 stands (rule 8); E4's timers-outside-insert [C] scoped to the run's 300 entries, objdump's 11 outside call sites added; the code-read splits stand; the Malah-sale [I] kept without an inventory row, scoped to the logged sale; the 253 timer's call [C], its schedule [I]. Plan 0038 log, lane/s38k review."
---

Review request: plan 0038 Phase 3, the **items/sockets-runewords** cluster (S2c, H2b, H6b), on `lane/s38k` (from
`main` `ad8b8cd0`). items/sockets-runewords {C 80, I 83, L 7} → **{C 128, I 84, L 7}** (diff: +56 / −8 `[C]`, +47 /
−46 `[I]`, one `[L]` struck and one added), `updated:` 2026-10-27; items/properties {C 152, I 22, L 3} → **{C 153,
I 22, L 3}** (F6, rule 8). Wiki: items-other-paths refreshed (`based_on` sockets-runewords 2026-10-27), items
`based_on` properties 2026-10-27. Entries closed: the [H6b entry](2026-10-27-architect-spec-writer-h6b-sockets-raises-for-the-phase-3-re.md)
and the [H2b entry](2026-10-20-reverser-spec-writer-h2b-items-chain-spec-updates.md) ((r)–(s), the last
open items); the [S2c entry](2026-10-16-reverser-spec-writer-plan-0038-s2c-corrections-for-phase.md) annotated ((e),
(g) done; (a), (d), (f) open for cube and vendors). Counts entry:
[2026-10-27-spec-writer-architect-s38k-sockets-runewords-counts-for-the-research-map](2026-10-27-spec-writer-architect-s38k-sockets-runewords-counts-for-the-research-map.md).

Suggested spot-checks (statement → batch section of [items/0007](../../findings/items/0007-sockets-runewords.md)):
- § A, the rows 4, 5 and 7 and their three notes (H6b sock 10 and 12: the built gloves and ring, the broken cap; the
  "no stock item reaches refusal 4 or 5" note `[I]`, ruling 1);
- § B, B2's x / y / body-location line and the `p5` note (H6b sock 16, sock 17 L237 as re-scoped by ruling 3);
- § E, E1's state-171 line and the *Already applied* notes (H6b sock 35 and fix 1: the `0x40` is an `[I]` note);
- § E, E4 and its three notes (H6b sock 18: the 252 schedule `[C]`, the truncation and the 253 half `[I]`);
- § F, F1's header and inline `[I]` lines and the three new notes (H2b sock 42 as scoped at the `lane/h2b` review, and
  S2c/H2b sock 44).

Points for the reviewer:
1. **Rule 8 outside the inventory rows.** items/properties F6 said the quality clamps "do not apply to qualities 2 and
   3" `[I]`; that half is now `[C]` from H2b's sock 44 piece, and "only qualities 2 and 3 reach it from here" stays
   `[I]`.
2. **E4's "the timers also run outside the insert"** is `[C]` from the finding's 300 timer-entry lines (186 at the
   load, 114 at later creations), scoped to that run's counts; the entry asked for "every item load and creation",
   which the spec does not claim. The two 253 schedules outside an insert stay `[I]` (fix 4: not compared).
3. **Splits that add an `[I]`** (rule 2, a code-read part out of a `[C]` sentence): `+0x084` not written (sock 6),
   the `itype4..6`/`etype` reads (sock 4), the group ≥ 3 fatal line (now its own bullet beside sock 25's `[C]`), the
   classic-legal sentence (sock 34), E2's mode-6 sentence (sock 36 L472), the writer's `0xFFFF` (sock 46), the
   `hasinv` condition of `n_filled` (sock 47), B6's client-update queue (sock 20), B1's ethereal and item-version
   test (sock 21), Zod's func 20 (sock 26).
4. **One `[I]` bullet carried from the finding** that no inventory row names: the sale to Malah makes no copy
   (*Entry points*; items/0007 sock 1, `[I]`).
5. **Open questions:** the child-level question struck (sock 21); the not-exercised list rewritten (the copier ran;
   the version-71 sites routed to H1c); the finding's H6b `p5` question added as an `[L]`.
