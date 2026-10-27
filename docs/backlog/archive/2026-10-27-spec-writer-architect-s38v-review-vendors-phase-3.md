---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/items/vendors.md
  - ../../wiki/items-other-paths.md
  - ../../findings/items/0009-vendors.md#plan-0038-batch-h6c-run2026-10-27-sweep-vendors
resolution: "Reviewed on lane/s38v: accept with fixes (5); economy F4's test 8 raised in the review (plan 0038 log, the lane/s38v review)."
---

Review request: plan 0038 Phase 3, the **items/vendors** cluster (S2c, H6c), on `lane/s38v` (from `main` `fcce5b4d`).
items/vendors {C 77, I 37, L 2} → **{C 112, I 37, L 2}** (diff +37 / −2 `[C]`, +28 / −28 `[I]`), `updated:`
2026-10-27. Wiki: items-other-paths vendor sections refreshed (`based_on` vendors 2026-10-27). Entries: the
[H6c entry](2026-10-27-architect-spec-writer-h6c-items-vendors-phase-3-retag.md) closed; the
[S2c entry](2026-10-16-reverser-spec-writer-plan-0038-s2c-corrections-for-phase.md) closed ((d) was its last
open part). Counts entry:
[2026-10-27-spec-writer-architect-s38v-vendors-counts-for-the-research-map](2026-10-27-spec-writer-architect-s38v-vendors-counts-for-the-research-map.md).

Suggested spot-checks (statement → batch section of [items/0009](../../findings/items/0009-vendors.md)):
- § C, C0 and the two C0–C1 notes (H6c vend 14 with review fix 4: the trade-first call 0x00578BFF never taken in the
  runs `[C]`, "never" beyond them from the `+0x21` writes `[I]`), and the *Two seeds interleave* note rewritten with it;
- § Entry points, the `UnitFree` row and its two bullets (vend 2, ruling (a): the rescan of run:2026-10-20-two-clients;
  the flag test `[I]`; `PlayerSetInteract` only while `+0x6C` is 0, fix 6);
- § D, the two D3–D4 notes and the `MAX_FAILS` row (vend 5: shortfall on the count `[C]`, the test sites and the
  epilogue jump `[I]`);
- § G, the two G1 notes and § H's free bullets (vend 29 and 32, ruling (b): the no-build branch needs a second
  interactor at 0x00572FAF, no single-player case);
- § C, the level-up bullet (vend 18, fix 3 and ruling (c): one event of two levels, 30 → 32, on a built state not
  reached by play).

Points for the reviewer:
1. **Built states** (ruling (c)): named once in *Inputs* and again at vend 18, as ADR-0013 neutral inputs backing
   only the code that reads them.
2. **The gold piles** (fix 2): § F's new bullet names `DropGoldAmount`'s call (return 0x0055A18D) and the 4 piles,
   with no cause.
3. **Cross-spec, not edited here:** [items/economy](../../specs/items/economy.md) F4 keeps test 8 (the store record's
   byte `+4`, tested at 0x0057970E) among the five unreached tests `[I]`; H6c vend 34 logged a sale in Gheed's gamble
   window refused by the gamble view at 0x00579714. If that is test 8, economy F4 and wiki/economy ("five ... read
   from the code only") could take it at the next economy round; this lane did not judge the identity.
4. **Inline `[I]` added on lines no batch claimed** (rule 2): A2's no-slot case, C1's hireling branch, D3–D4's
   `fails > 32` returns, E2's retries, E3's −1 page and cell search, G2's no-record, empty-slot and placement-failure
   exits.
5. **Open questions:** the multiplayer `[L]` gains the gamble window kept by a second interactor (G1, § H).
