---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/save/0001-d2s-io.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play
  - ../findings/hirelings/0001-hirelings.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play
resolution: ""
---

**Held until the `lane/h1b` review releases it.** Phase 3 re-tag input for save/d2s and hirelings from plan 0038 batch
H1b (run:2026-10-27-sweep-d2s-play): the statements raised and raised in part are listed per row in the inventory § 2.6
H1b block and argued in the two findings' "Plan 0038 batch H1b" sections. For a raised-in-part row, only the half
marked `[C]` there moves; the rest stays `[I]`. Rows 77 and 78 are proposed d-none (they stay `[I]` as readings).

Points the spec text may need beyond a tag change:
- save/d2s § Entry points: the death path's save (`sub_0057FCA0_PlayerDeathModeEnd`, return 0x0057FD88) is now met in
  single player; the spec's list of `PLRSAVE_Save` callers can say so.
- save/d2s § D3–D5: `D2S_LoadFinish`'s stat 30 is the experience.txt row of the level L (the threshold of L + 1 in the
  spec's counting), shown not to be the character's experience by a save with experience above it.
- hirelings § F: the saved header of a mercenary hired in play is now met (the finding's § F sentence is `[C]`).
