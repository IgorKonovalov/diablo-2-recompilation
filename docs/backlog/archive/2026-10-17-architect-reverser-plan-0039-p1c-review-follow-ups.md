---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../../findings/player/0001-creation.md
resolution: "2026-10-20 (lane/p49r, plan 0049 P1): (a) src:arreat-summit-experience was re-fetched under ADR-0007 (sources.md row updated). The 75 % recovery is held with refinement: the base is the loss actually taken, the player-killer exemption is in the code, and the place is not a condition. A new verdict, Save and Exit forfeits the share, is held ([player/0001 § 10](../../findings/player/0001-creation.md#10-community-cross-check-phase-1b)). (b) was noted at the review. This lane keeps its scans in tools/sweep_p49r.py with a hashed manifest."
---

[2026-10-17] from architect → reverser: plan 0039 P1c review follow-ups (not blocking). (a) With the next lane that may fetch (ADR-0007), re-fetch src:arreat-summit-experience and update [player/0001](../../findings/player/0001-creation.md) *Leads used*: the corpse 75 % is now a code reading (§ Plan 0039 batch P1c), so the verdict line moves from "gap / not covered" to agrees or contradicted on the re-read page, with the base (the loss actually taken) and the player-killer exemption noted. (b) Keep the operand-scan scripts of a batch whose count a review must check (P1c's Q4 and bit-17 scans, Q26's fit) in `tools/` or name their exact patterns in the finding; this review re-ran the bit-17 scan (20 plain, 9 OR-immediates, 1 register OR) and the Q26 fit, and counted Q4's 194 operand sites (18 absolute, 176 `[reg+0xA78]`), but could not diff against the lane's own output.
