---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../findings/objects/0001-object-population.md#h5b2-population-clusters-caps-themes-and-orientation-rows-3-13-1517-19-20-50-51
  - archive/2026-10-27-architect-reverser-h5b-shrine-cap-wording.md
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

Review request for `lane/rsw` (the H5b.2 shrine-cap wording entry, plan 0038 Phase 3, `lane/s38o` review ruling 1). objects/0001 § H5b.2's shrine-cap bullet now says the cap returned "before any placement draw (after the handler's `P100(S)` draw)"; the `= 10` sentence is kept, and a dated correction (2026-10-27) names the old wording and its anchors: the room-seed step with `0x6AC690C5` at 0x00552B9A–0x00552BBA, `OBJRGN_HealthShrineDue` called at 0x00552BC5, `OBJRGN_ShrineCapReached` called at 0x00552BF7, checked with objdump over 0x00552B50–0x00552C10 on the pinned `Game.exe`. The grep for "before any draw" over docs/findings found no other place in the shrine handler's text (items/0006:602 and skills/0003:594 are other functions; objects/0001 § 4's handler 2 already has the draw as step 1). No tag, symbol or spec change. Static only (objdump), no Ghidra, no harness.
