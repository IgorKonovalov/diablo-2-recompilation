# Common review fixes — architect (the reviewer's blind spots)

What later reviews or lanes had to correct in the architect's own plans and reviews. Check a plan or a
review against these before committing it. Categories are those of the [lane run ledger](../../../../docs/plans/metrics.md).

1. **Recount the items a phase lists** when drafting it. Seen: plan 0039 Phase 1 said 16 for P1a's 15
   and 20 for P1b's 18 ([0039](../../../../docs/plans/done/0039-backlog-sweep-4.md) P1a and P1b reviews).
2. **A claim settled at review gets the lane's scrutiny.** "Open wounds halve by `0x0C` only" was settled
   at the resume-lane review; the run could not tell it from "`0x0C` or `boss`" (Andariel carries both),
   and the `lane/p37t` review had to scope it ([0037](../../../../docs/plans/done/0037-combat-formulas.md)).
3. **Write a review fix into the document it changes**, not only into the review's fix list. Seen: S4a's
   preset 18 split, still "raised" in drlg/0004 at the `lane/p38s3` review ([0038](../../../../docs/plans/0038-inferred-claims-sweep.md)); the `lane/s38h2b` review's items/affixes count (I 28) missing from its research-map row, fixed at the `lane/s38h2c` review (0038); the `lane/h4a` review marking class 312's H4b piece met in monsters/0004 but not special 66's in monsters/0003, fixed at the `lane/p51r` review ([0051](../../../../docs/plans/done/0051-backlog-sweep-6.md)). The H4a raise of the wanderer list written into monsters/spawn only, lifecycle's Constants row left `[I]` until the `lane/sfx` review (0038).
4. **Read the whole branch region before ruling.** Seen: the Phase 2 review missed the moving player's
   `÷ 3`, found at Phase 3 (0037).
5. **Recompute totals once, over every reviewed batch, after merging `main`.** Two reviews computed in
   parallel each missed the other (S2b and S3a, fixed at the S4b review, 0038).
6. **After every lane merge, run `python3 -I tools/backlog.py archive`** (ADR-0019; it runs `migrate` first, then
   sweeps closed entries into `docs/backlog/archive/` and fixes links; on a conflict in `docs/backlog.md` keep both
   sides, migrate dedupes and keeps the strike). Before ADR-0018: dedupe by entry text, keep the struck copy. Seen: the S2b, S4b,
   H4b, `lane/p38s3` and S1e merges (0038).
7. **Label a plan's estimates as estimates.** "No logger change" in a batch recipe was a guess (H5a ruling
   4, 0038).
8. **Give every reviewed spec a wiki owner and every plan its research-map rows at the start.** Seen:
   "wiki: not part of this plan" (0037 P3 → `lane/wiki1` ruling, 0038); the stats rows due when plan 0041
   started ([0041](../../../../docs/plans/done/0041-stats-and-states.md) P1 review); the `skills/dispatch`, `skills/missiles` and
   `skills/catalogue` rows, due when plan 0045 started, added only at the `lane/p46m15` review
   ([0046](../../../../docs/plans/0046-skills-function-catalogue.md)); and keep a row's status current at each phase acceptance: the
   `skills/dispatch` and `skills/missiles` rows still read "Phase 2 and the spec not started" after the part 1 review
   (fixed at the `lane/p45k` review, [0045](../../../../docs/plans/0045-skills-missiles-machinery.md)). The `items/economy` row's counts left at `I 83 / L 12` while the front matter had moved to 84 / 12 (fixed at the `lane/s45p3` review, 0045). The `anim/timing` row still reading "P1.2 next" after the P1.2 review, and `anim/movement` "not started" (fixed at the `lane/p50d` review, [0050](../../../../docs/plans/0050-animation-frame-timing.md)).
