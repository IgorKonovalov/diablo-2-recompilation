# Common review fixes — architect (the reviewer's blind spots)

What later reviews or lanes had to correct in the architect's own plans and reviews. Check a plan or a
review against these before committing it. Categories are those of the [lane run ledger](../../../../docs/plans/metrics.md).

1. **Recount the items a phase lists** when drafting it. Seen: plan 0039 Phase 1 said 16 for P1a's 15
   and 20 for P1b's 18 ([0039](../../../../docs/plans/0039-backlog-sweep-4.md) P1a and P1b reviews).
2. **A claim settled at review gets the lane's scrutiny.** "Open wounds halve by `0x0C` only" was settled
   at the resume-lane review; the run could not tell it from "`0x0C` or `boss`" (Andariel carries both),
   and the `lane/p37t` review had to scope it ([0037](../../../../docs/plans/done/0037-combat-formulas.md)).
3. **Write a review fix into the document it changes**, not only into the review's fix list. Seen: S4a's
   preset 18 split, still "raised" in drlg/0004 at the `lane/p38s3` review ([0038](../../../../docs/plans/0038-inferred-claims-sweep.md)).
4. **Read the whole branch region before ruling.** Seen: the Phase 2 review missed the moving player's
   `÷ 3`, found at Phase 3 (0037).
5. **Recompute totals once, over every reviewed batch, after merging `main`.** Two reviews computed in
   parallel each missed the other (S2b and S3a, fixed at the S4b review, 0038).
6. **After a merge that touches `docs/backlog.md`, run `python3 -I tools/backlog.py migrate`** (ADR-0018; on a
   conflict keep both sides, migrate dedupes and keeps the strike). Before ADR-0018: dedupe by entry text, keep the struck copy. Seen: the S2b, S4b,
   H4b, `lane/p38s3` and S1e merges (0038).
7. **Label a plan's estimates as estimates.** "No logger change" in a batch recipe was a guess (H5a ruling
   4, 0038).
8. **Give every reviewed spec a wiki owner and every plan its research-map rows at the start.** Seen:
   "wiki: not part of this plan" (0037 P3 → `lane/wiki1` ruling, 0038); the stats rows due when plan 0041
   started ([0041](../../../../docs/plans/0041-stats-and-states.md) P1 review).
