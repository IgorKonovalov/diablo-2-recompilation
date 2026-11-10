---
from: architect
to: reverser
date: 2026-11-10
status: done
context:
  - ../../plans/done/0064-clean-room-test.md#implementation-log
  - ../../plans/0064-cleanroom/S4.md
  - ../../findings/drlg/0008-outdoor.md
  - ../../findings/drlg/0007-warps.md
resolution: "Done 2026-11-10 (lane/n64r): (a) A1CliffMark's rule as pseudocode with addresses, [C] by the model tools/drlg.py and the kept run:2026-10-15-drlg-outdoor check, re-scored with a transcription of the code (tools/cliff_cover.py, 0 mismatches, branch counts); (b) g_A1SearchDx corrected in place to +1, 0, -1, 0 (dir 0 E); (c) OneOrTwo's s step in the else branch only; (d) LevelBorderAdj's Vis != 0 test, with a separating control (22 600 mismatches without it). [drlg/0008 § Plan 0064 statements](../../findings/drlg/0008-outdoor.md#plan-0064-statements-2026-11-10); drlg/0007's table row raised. Spec changes routed to the plan-0064-drlg-outdoor items 1-4 and drlg-warps-border-adj."
---

**Missing and wrong finding statements, drlg/0007 and drlg/0008 (plan 0064 P3 triage, S4 rows 6, 13, 14, 15, 16). Static only, no slot.** (a) **`A1CliffMark` (0x00680070) has no rule in any finding**: drlg/0008 gives only "vertex type 1 on non-seam up/right runs; O.flags |= 0x20" (§ 3 table row, line 485). Write the rule as reviewed pseudocode: which vertex starts a run (the turn test against the previous and next vertex, the seam bits of both), where a run ends, which vertices get type 1, when 0x20 is set, and the ring walk's start and stop. This alone carries the 22 Act I cases (levels 4–7) the clean-room S4 implementer could not reproduce: the triage swapped only the implementer's cliff mark for `tools/drlg.py` `a1_cliff_mark` and the slice scored 0 different of 1 820 (probe in the plan log). Lead, not a statement: that model's walk. (b) **`g_A1SearchDx` is wrong in drlg/0008 (line 1019)**: the finding says `−1, 0, +1, 0`; the bytes at 0x006F2854 are `01 00 FF 00` (`+1, 0, −1, 0`), so dir 0 is E, 1 S, 2 W, 3 N, consistent with `g_DirOctant` (`(+1, 0)` → 0). `g_A1SearchDy` `0, +1, 0, −1` is right. Correct the statement and its "dir 0 W" gloss. (c) **`A1PlaceOneOrTwo` (0x006804E0)**: drlg/0008 line 541 writes "`r & 3 == 0 ? Near(d) ×2 : Near(d), then if s: …`", which reads as the `s` step following both branches; the model the replay reproduces with, and the clean-room run (all level-3 cases), have the `s` step and `Near(49)` only in the else branch. State the branch structure from the code. (d) **`LevelBorderAdj` (0x00677680)**: drlg/0007 (§ table row, `I`) and drlg/0008 say "a node per `Vis` slot with `Warp` −1"; an empty slot is also `Warp` −1 (drlg/0007 line 328). State the `Vis ≠ 0` test if the code has it. Then the spec-writer entries plan-0064-drlg-outdoor (H1, H6d, H7, § C) and plan-0064-drlg-warps follow.
