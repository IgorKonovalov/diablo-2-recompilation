---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../findings/objects/0001-object-population.md#h5b2-population-clusters-caps-themes-and-orientation-rows-3-13-1517-19-20-50-51
  - 2026-10-27-architect-reverser-h5b-shrine-cap-wording.md
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "accept with fixes (1): objdump of 0x00552B50–0x00552C10 on the pinned Game.exe confirms the seed step at 0x00552B9A–BBA, HealthShrineDue at 0x00552BC5, the % 100 test at 0x00552BDB–BF0 and the cap call at 0x00552BF7; wording matches objects/README Constants and E2; the grep finds no other copy; the % 100 range added to the correction note (omission) [plan 0038 log](../../plans/0038-inferred-claims-sweep.md#implementation-log)"
---

Review request for `lane/rsw` (the H5b.2 shrine-cap wording entry, plan 0038 Phase 3, `lane/s38o` review ruling 1). objects/0001 § H5b.2's shrine-cap bullet now says the cap returned "before any placement draw (after the handler's `P100(S)` draw)"; the `= 10` sentence is kept, and a dated correction (2026-10-27) names the old wording and its anchors: the room-seed step with `0x6AC690C5` at 0x00552B9A–0x00552BBA, `OBJRGN_HealthShrineDue` called at 0x00552BC5, `OBJRGN_ShrineCapReached` called at 0x00552BF7, checked with objdump over 0x00552B50–0x00552C10 on the pinned `Game.exe`. The grep for "before any draw" over docs/findings found no other place in the shrine handler's text (items/0006:602 and skills/0003:594 are other functions; objects/0001 § 4's handler 2 already has the draw as step 1). No tag, symbol or spec change. Static only (objdump), no Ghidra, no harness.
