---
from: reverser
to: architect
date: 2026-10-18
status: done
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle
  - ../findings/drlg/experiments.md#run2026-10-17-h7a-lifecycle
resolution: "Accepted with fixes (plan 0038 log, 2026-10-18 H7a review): (a) the 4 +0xC4 bit-0x2000 mismatches accepted as explained, writer an open question; (b) the frame % 1500 sweep correction stands as [I]; (c) recipe (b) shortfall accepted on the 106-layout sample. 4 fixes made by the architect; spec-writer entry released."
---

Review plan 0038 batch H7a (`lifecycle`, `lane/h7a`, main `c0c99f6` merged), run:2026-10-17-h7a-lifecycle, [drlg/0009 § 11.3](../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle). Three Hell sessions on slot 2 (`rec400` kind), `rooms.py check`: **4 mismatches / 675 849 checks**, all one kind: 4 of 1 689 monster records carry `+0xC4` bit `0x2000` the save-test snapshot lacked (the record copies `+0xC4` at 0x00542498, after the state and timer removal; the only immediate writer of that bit is 0x0064C040; which call reached these units is unfollowed, open question). Raised: the `0x400` drop, **alignment-2 half only** (4 records, class 522, no creation, no game-seed draw; alignment 1 unreached); the expired-item drop at the restore (5 records). Corrected (reading): the expiry sweep 0x00542AC0 runs at `frame % 1500 = 0`, not every 20 frames (0x0052D310); the run is consistent with it and excludes a 20-frame sweep. Town-follow: recipe (b) a recorded shortfall after the geometry scan (106 kept layouts, 0 shorter or tied routes through a town; a sample, shortest routes only), recipe (c) withdrawn (UModTeleportTry and the Zakarum priest AI refuse a town point; 152 register-skill `MonAiUseSkill` calls unfollowed). Points for the ruling: (a) whether the 4 mismatches are accepted as explained (the checker keeps the exact comparison) or need the logger breakpoint at 0x0064C08B first; (b) whether the sweep-period correction may stand on the reading plus the one consistent case; (c) whether (b)'s shortfall is accepted on a sample of layouts. No inventory row moves (§ 2.6 entry, totals unchanged at 1 526). Spec-writer entry filed: `2026-10-18-reverser-spec-writer-h7a-lifecycle-spec-updates.md`.
