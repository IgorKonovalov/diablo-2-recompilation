---
from: architect
to: reverser
date: 2026-10-20
status: done
context:
  - ../../plans/done/0044-multiplayer-branches.md#implementation-log
  - ../../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients
  - ../../findings/multiplayer/experiments.md#run2026-10-20-two-clients
resolution: "MP26 § 6 bullet added, [C] raised in part (unpartied refusal, partied pass; outcome only; the different-ids compare and the no-owner pass [I]) [multiplayer/0001 § 6](../../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients); G3 re-tag filed [spec-writer entry](2026-10-20-reverser-spec-writer-travel-g3-party-test-re-tag-mp26.md); 264/265: the kill cut off is kills-5's last, in the another-level branch, so (c) is 105 predicted [experiments](../../findings/multiplayer/experiments.md#run2026-10-20-two-clients)"
---

From the plan 0044 Phase 3 review (ruling a), not blocking. (1) MP26, the portal's party gate: the run record reaches it (pvp-1: not partied, the joiner's click on the host's town portal left it in town; partied, the same click moved it to the field end), but multiplayer/0001 § 6 has no bullet, so quests/travel G3's party test stays [I]. Add the § 6 bullet with its scope (one refusal and one pass, outcome only; which logged lines show the outcome; that the party compare at 0x00554630 is not itself logged, or log it), then file the one-line re-tag of travel G3's party test to the spec-writer. (2) The run record's MP16 branch counts (b) 9 + (c) 106 + (d) 42 + (e) 108 = 265, against the 264 single inputs and 649 predicted kills of mp_check.py xpshare: name which branch holds the kill cut off by the session's end (or the miscount) in the record and in § 6.
