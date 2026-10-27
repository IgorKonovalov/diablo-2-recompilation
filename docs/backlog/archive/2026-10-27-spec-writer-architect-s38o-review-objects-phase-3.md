---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/objects/README.md
  - ../../wiki/objects.md
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (8); rulings and fixes in the plan 0038 log, lane/s38o review entry."
---

Review request: plan 0038 Phase 3, the **objects** cluster, on `lane/s38o` (from `main` `1e61473c`). objects {C 139, I 72,
L 5} → **{C 188, I 56, L 4}**, `updated:` 2026-10-27; wiki/objects refreshed, wiki/seed-to-world's date. Entries closed:
H5b objects spec updates, S4b corrections ((a), the last part), S2a tc 64 ((b)'s objects § J3, the last part); the H6e2
entry annotated (objects parts done) and left open for items/quest-drops after H6e1.

Suggested spot-checks (statement → batch section):
- C1's test-order bullet (S4a row 9: 46 / 315 / 35 / 110 / 759 of 1265);
- E2's forced conversion (H5b.2, cotd2: class 231 code 14 → 96, the discarded `ShrinePick(2, level 1)`);
- K2's rewrite (H5b.1: the remap, the function table, 162 then **160** at `x + 1`, the 35-frame queue; types 8/9 `[I]`);
- J3's tier and `ilvl` raise (items/0001 § 2 and items/tc J1; the guards kept `[I]`);
- § L's Khalim row (items/0010 H6e2, `heart4`: gold, then `qhr`, then `ObjectChestDrop`; eye and brain `[I]`).

Points for the reviewer:
1. **Shrine cap wording.** H5b.2 says the cap "returned before any draw of the handler"; E2's pseudocode (and
   objects/0001 § 4 step 1) draws `P100(S)` before the cap test. The spec says "returned at the cap with no placement
   attempt" and leaves the order as written. If H5b meant that no room draw at all was made at the cap, E2's order
   and § E's `1 + 2a` count would need a reverser entry.
2. **Super-chest counts.** I2's new `[C]` cites S4a's "7 DS1 580 super chests" (experiments, S4a addendum); § I's 580
   row keeps the run's original "4 super chests" (the containers line of run:2026-10-15-objects). Not reconciled here;
   the 7 may count re-creations or windows twice.
3. **Row 52 split.** The ledger raises the reimplementation note "a trap fires later" whole; its clause on the types
   8 and 9 object-region draw is unreached (H5b.1 `[I]`), so the note is `[C]` for the queue and the 35 frames and
   `[I]` for that draw (rule 2). A new note states the level remap (`[C]` type 4 in level 35, `[I]` the rest).
4. **Row 7.** B4's SaveTest was already `[C]` from run:2026-10-17-lifecycle; S4a's 190 restores are added as a second
   `[C]` bullet, with the unmet refusals kept `[I]` as before.
5. **Rule 8 beyond the inventory:** § K's event-7 route for classes 268 and 367 (items/quest-drops qd 1's H6e2 raise).
6. **Wiki cross-page:** wiki/items-other-paths still says a quest chest gives "its quest item, then its ordinary chest
   drop, then 5 to 9 gold piles" for every chest; that is items/quest-drops § E1, which moves with the H6e1 round (noted in
   the H6e2 entry). wiki/objects already states the Khalim order.

Counts recounted with the gate's own tag reader (`RE_TAG` over every body line, fenced included).
