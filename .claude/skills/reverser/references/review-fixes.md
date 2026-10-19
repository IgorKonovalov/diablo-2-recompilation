# Common review fixes — reverser

Fixes the architect's reviews keep making on reverser lanes. One rule each; check your finding against
all of them before you file the review request. Review entries are in the plan logs named; the
categories are those of the [lane run ledger](../../../../docs/plans/metrics.md).

1. **A new code reading is `[I]`.** `[C]` needs a named second source (a reproduction of logged calls, a
   writer/reader pair, a full-table check, an independent tool). Don't name a meaning the code does not
   give. Seen: S1e rows 51/64 ([0038](../../../../docs/plans/0038-inferred-claims-sweep.md), 2026-10-17); `0x400` "good/evil"
   ([0040](../../../../docs/plans/done/0040-drlg-room-lifecycle.md) P1 review).
2. **Recount every count from the binary with a kept command**, never from memory or a partial scan:
   writers, call sites, instructions, items. Seen: bit-17 writers 5 → 21
   ([0039](../../../../docs/plans/0039-backlog-sweep-4.md) P1b review); S4b row 17 short by 9, "7" instructions for 8 (0038).
3. **Take totals against `main` after merging it**, not against the totals your batch started from.
   Seen: S2c, S3b and S1a reviews (0038), each recomputed.
4. **"Never", "only", "no X": say what the run separates.** If one case carries both readings (Andariel has
   flag `0x08` and `boss`), that half stays `[I]`. Seen: resume-lane review
   ([0037](../../../../docs/plans/done/0037-combat-formulas.md)), re-scoped at the `lane/p37t` review.
5. **An existing reviewed symbol name wins.** Merge `main` and grep `re/symbols.csv` for every address
   before you name it; rename your side. Seen: six addresses named twice, `lane/p41r`
   ([0041](../../../../docs/plans/done/0041-stats-and-states.md) P1 review).
6. **Keep the tool behind every claim**: the script in `tools/` (seeded, if it generates cases), its
   output hashed, logs under `workspace/logs/` with a manifest line, one path base per manifest so `sha256sum -c` passes from one directory (H7a review, 0038), and every tool revision behind a cited output named. Seen: the unseeded `eval` case
   writer (S1e, 0038); the *Fleshripper* log left in session scratch (resume lane, 0037). An aborted session's
   partial log is kept as a development log, not deleted (0040 P2 review).
7. **A conclusion needs an address, `fn:` or `run:` anchor**, not a link to another finding (gate W1).
   Seen: the resume lane's experiments addendum (0037); `lane/w1`'s 104 W1 lines (0039).
8. **Split a raise where it has a remainder** and head the row "raised in part", in the ledger itself.
   Seen: special 65 (H4b), sock 14 (S2c), special 43 (S3b), all 0038; five `[C]` bullets of drlg/0009 § 11 with an
   unreached branch inside (the wanderer gate's `+0x78`, the item drop on expiry; [0040](../../../../docs/plans/done/0040-drlg-room-lifecycle.md) P2 review).
9. **Name the path for every claim about a caller**, or say "unfollowed" with the count. Seen: the
   superunique minion path (0039 P1b, Q19); the 8/9 case's `RoomTileSetFlags` call (0039 P1a).
10. **One case decides only if a wrong reading could not match it by chance.** Seen: aff 28's durability
    value, about one in eight (S2b, 0038).
11. **"Moved" names the destination plan**; otherwise write "out of this plan". Seen: status bit 1
    (0039 P1b ruling 4); a closed entry's "(3) deferred" with no home (H7a review, 0038).
