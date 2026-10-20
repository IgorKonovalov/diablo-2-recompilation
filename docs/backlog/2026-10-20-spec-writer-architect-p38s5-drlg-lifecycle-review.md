---
from: spec-writer
to: architect
date: 2026-10-20
status: open
context:
  - ../specs/drlg/lifecycle.md
  - ../specs/drlg/outdoor.md
  - ../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

Review request, plan 0038 Phase 3, the drlg/lifecycle cluster (lane/p38s5, from main c4b4539). Sources: drlg/0009 § 11.2 and § 11.3 (H7a, accepted 2026-10-18), drlg/0008 § H5e (a) layout bound. Spec counts: **drlg/lifecycle** {C 80, I 73, L 7} → **{C 85, I 75, L 8}**; **drlg/outdoor** {C 180, I 19, L 2} unchanged (row 7 restated at [I]). Raised to [C] (5): § H H2 drop line, alignment-2 half of the 0x400 drop (run:2026-10-17-h7a-lifecycle); § H the 0x400 alignment-2 bullet (4 records, no creation, seed unchanged); H4's expired-item drop line ([I] → [C]); the H4 expired-item bullet (5 records); § G the record +0xC4 bullet, worded as the review ruled (value when 0x00542498 reads it). New [I] (3): § A the 1 500-frame expiry sweep from 0x0052D310 (correction of the 20-frame reading); H2 drop line, alignment-1 half; § G the 0x0064C040 store and the restore not copying bit 0x2000 back. One [I] removed (H4 drop line raised). New [L] (1): which call sets +0xC4 bit 0x2000. Restated, tags unchanged: the town-follow open question from § 11.2 and § 11.3 (H7a its route, (b) a recorded shortfall, (c) withdrawn, the 152/9/19 unfollowed counts, still a named shortfall of plan 0040 P2); the Unreached-branches bullet (expired-item drop and the 20-frame sweep out; alignment-1 half and the 1 500-frame sweep pass in); the alignment-1 half added to the existing [I] 'not reached' bullet of § H; the Evidence list gains run:2026-10-17-h7a-lifecycle. drlg/outdoor C5 [I] bullet and its Open-questions shortfall bullet split per the rbs4 entry (2): no stock case in Acts I, II, IV, V by the layout bound, Act III on the 600-seed sample. Wiki: levels (based_on outdoor and lifecycle 2026-10-20; town-follow, expired-item and vertex-merge paragraphs restated), monsters and objects (based_on date only, no contradicting text). Closed: the H7a spec-updates entry and the rbs4 town-follow/outdoor 7 entry. Spot-check suggestions: the 0x400 bullet vs § 11.3 (3), the +0xC4 bullet vs ruling (a), the § A sweep bullet vs ruling (b). Research-map rows: drlg/lifecycle counts change; drlg/outdoor counts unchanged.
