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

**Released by the `lane/h1b` review (2026-10-27, accept with fixes).** Phase 3 re-tag input for save/d2s and hirelings from plan 0038 batch
H1b (run:2026-10-27-sweep-d2s-play): the statements raised and raised in part are listed per row in the inventory § 2.6
H1b block and argued in the two findings' "Plan 0038 batch H1b" sections. For a raised-in-part row, only the half
marked `[C]` there moves; the rest stays `[I]`. Rows 77 and 78 are proposed d-none (they stay `[I]` as readings).

Points the spec text may need beyond a tag change:
- save/d2s § Entry points: the death path's save (`sub_0057FCA0_PlayerDeathModeEnd`, return 0x0057FD88) is now met in
  single player; the spec's list of `PLRSAVE_Save` callers can say so.
- save/d2s § D3–D5: `D2S_LoadFinish`'s stat 30 is the experience.txt row of the level L (the threshold of L + 1 in the
  spec's counting), shown not to be the character's experience by a save with experience above it.
- hirelings § F: the saved header of a mercenary hired in play is now met (the finding's § F sentence is `[C]`).

Added by the `lane/h1b` review (the fixes are in save/0001's H1b section):
- save/d2s § Entry points, the join row: the chain has a frame between `PlayerLoad` and the logged returns,
  `sub_005344B0_PlayerLoadFromFile` (file path) and `sub_00534520_PlayerLoadFromClient` (client path). The logged
  returns are `[C]`; the two `PlayerLoad` links are `[I]`.
- save/d2s § Entry points: the `[C]` bullet's "Nothing was written during play in the runs" holds for
  run:2026-10-12-d2s-io only. Single player writes the file at a death (hell-r3). Say so where the death caller is
  listed, and keep "no single-player autosave" (the death write is an event save).
- save/d2s § Entry points, the periodic row: only the outcome moves (callback 0 → no save). Which test stopped it (the
  `0x00730FFC` entry test at 0x0052D353, the time tests, the callback test at 0x0052D3D9) stays `[I]`. The spec may
  name the entry test as `[I]`.
- save/d2s § D5: write stat 30 so that it cannot be misread: the experience.txt row whose `Level` is L (the experience
  to reach L + 1); counting the `MaxLvl` row as index 0 that is index L + 1 (`EXP_GetThreshold` reads dword
  `class + 8·L + 8`, 0x00611814).
- Rows 3 and 19 and the callback halves of rows 2 and 18 stay `[I]` (shortfalls); a reverser entry may move them
  to d-none.
