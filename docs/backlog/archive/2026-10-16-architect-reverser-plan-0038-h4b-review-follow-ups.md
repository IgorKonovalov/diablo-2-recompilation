---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../../findings/monsters/0002-room-population.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b
  - ../../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b
  - ../../findings/monsters/0004-stats.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b
resolution: "Closed at the lane/h5d review (architect, 2026-10-27; plan 0038 log). The H5d piece is settled: spawn 42's 228 met and reproduced in the tomb-r2 session (run:2026-10-27-sweep-collision), 334 d-none (no stock creation source; the MosquitoNest AI's 334 is a cell-test argument on the nests themselves); spawn 42 raised in part, still counted as H4b. The pieces H4a did not take were ruled out of this plan at the plan 0051 Phase 1a review."
---

[2026-10-16] from architect → reverser (H4a lane, and H5d): plan 0038 H4b review follow-ups; the rows stay counted as H4b ([inventory § 5](../../plans/0038-inventory/README.md#harness-batches), § 2.6). **H4a** (same logger, `mon-stats.gdb` with `mon-extra.py`; check with `sweep_h4b.py` and `monstats.py`): (a) `doomknight3` (312) in the Chaos Sanctuary: the `Range(4)` result in appearance bytes 10 and 11 (stats 13, 14); (b) a `willowisp` champion or unique with `strong`, `champion` or `berserk` (stats 40, shortfall; seed 4805 normal level 105, or 4801 levels 86/87); (c) Blood Raven's client name, mod 12 and string 3111 (special 66); (d) an aura special at level ≤ 15 so that `k` clamps to 1 (special 27); (e) if a seed places one, a Shrines code-20 shrine operated with `objop`, `MMS0` logged (special 2 d-owner, special 74's remainder); else it stays with the owner; (f) optional: the camel at `/players` 8 (stats 23 is raised on `cow`). Conditions for using the logger are in the [plan log](../../plans/0038-inferred-claims-sweep.md#implementation-log) (H4b review, ruling 4). **H5d**: its tomb (class 228, the Act II tombs) and Act III (`suckernest1`, 334) sessions decide spawn 42's remainder with `monspawn.py check` on the `MC` lines (`collision.gdb` sources `mon-spawn.py`). Context: [monsters/0002](../../findings/monsters/0002-room-population.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b), [0003](../../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b), [0004](../../findings/monsters/0004-stats.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b)

*2026-10-17 (reverser, `lane/rbs` static sweep):* skipped: needs harness; rides on plan 0038 harness batches H4a and H5d.

*2026-10-25 (reverser, `lane/p51r`, [plan 0051](../../plans/done/0051-backlog-sweep-6.md) Phase 1a, no slot):* **With H4a.**
`lane/h4a` has not landed: it is paused at the owner's request (its second pause, 2026-10-21, resume note in its own
plan 0038 log entry on that branch), with no statement claimed, no § 2.6 entry and no review request. So pieces (a)–(f)
are not checked off here. Its resume note names (c) Blood Raven's client name (special 66) as met, and (a) the
doomknight3 piece as part of its Chaos Sanctuary session, both before review. (b), (d), (e) and (f) are not named
there. The H5d piece (spawn 42's remainder in the tomb and `suckernest1` sessions, `monspawn.py check` on the `MC`
lines) is still in H5d's row of [inventory § 5](../../plans/0038-inventory/README.md#harness-batches), and no H5d run is on
`main`. The entry stays open; the H4a review annotates which pieces the batch took.

*2026-10-27 (architect, [plan 0051](../../plans/done/0051-backlog-sweep-6.md) Phase 1a review, after merging `main` `cf25f22`):*
`lane/h4a` has landed and was accepted
([plan 0038 log](../../plans/0038-inferred-claims-sweep.md#implementation-log), `lane/h4a` review). **H4a took (a) and (c):**
(a) `doomknight3` (312), 63 creations, both appearance bytes one `Range(4)` (stats 14 and 13 raised whole, still counted
as H4b; H4a review ruling (e), [monsters/0004](../../findings/monsters/0004-stats.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a));
(c) Blood Raven's client name, mod 12 to string 3111 (special 35 and 68 raised in H4a; special 66's remainder marked
met in [monsters/0003](../../findings/monsters/0003-special-monsters.md) § Plan 0038 batch H4b). **Not met by H4a, and out of
this plan** (no harness batch left loads `mon-stats.gdb` for them): (b) stats 40 stays a shortfall counted as H4b;
(d) special 27's clamp at 1 stays its `[I]` remainder; (e) no Shrines code-20 shrine was operated, so special 2 stays
`d-owner` and special 74's remainder stays, as this entry's own "else it stays with the owner" says; (f) optional,
not run, dropped. **Still open for H5d only:** spawn 42's remainder (the tomb and `suckernest1` sessions,
`monspawn.py check` on the `MC` lines), in H5d's row of
[inventory § 5](../../plans/0038-inventory/README.md#harness-batches). The entry closes with H5d's review.

*2026-10-27 (reverser, `lane/h5d`, plan 0038 batch H5d, run:2026-10-27-sweep-collision):* **The H5d piece.** 228
(`sarcophagus`) met in the tomb session (tomb-r2, level 70): `monspawn.py`'s presets-window prediction holds on its four
offset-cell `MC` tests, and the logger's before/after cells reproduce all six calls
([monsters/0002 § H5d](../../findings/monsters/0002-room-population.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision)).
334 (`suckernest1`) has no stock creation source (tables and code,
[drlg/0005 § H5d](../../findings/drlg/0005-collision.md#plan-0038-batch-h5d-run2026-10-27-sweep-collision)): proposed d-none, so
no Act III session was run. Left open for the H5d review to close.
