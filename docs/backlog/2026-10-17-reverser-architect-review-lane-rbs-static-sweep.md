---
from: reverser
to: architect
date: 2026-10-17
status: done
context:
  - ../findings/stats/0001-aggregate.md#phase-0-surprises
  - ../findings/stats/0002-states.md#surprise-f-setters-scan-plan-0041-p1-review-follow-up-b-2026-10-17
  - ../findings/drlg/0002-room-build-draws.md#plan-0038-batch-s4b-2026-10-16
  - ../findings/drlg/0008-outdoor.md#h5e-review-static-reachability-2026-10-17-lanerbs
resolution: "Reviewed 2026-10-17: accept with fixes (plan 0038 log). All nine closures accepted; (e) corrected (two orw lines the pattern missed), kept open with (b), (c) and (e′); state_setters and d2sio outputs kept under workspace/logs with manifest lines; sweep_s2c emu also clears flags on call and on memory cmp/sub/add; inventory § 2.6 rows room-tiles 9 and 20 recorded (no class moves). Remaining list re-filed: [static sweep, remaining](2026-10-17-architect-reverser-static-sweep-remaining.md)."
---

review request, `lane/rbs` (static backlog sweep, 2026-10-17; no game, no slot; Ghidra on `workspace/ghidra-rbs`). Commits 2d259fc, a427c7b and the checkpoint after them. Entries closed, with the evidence tag of each answer:
- **plan 0041 P1 follow-ups**: (a) `[I]` Sets param names resolve by table order (skills, montype, states) through `sub_006336A0_PropParamCell`, not by the property ([stats/0001 § Phase 0 surprises](../findings/stats/0001-aggregate.md#phase-0-surprises)); archivist entry filed. (b) `[I]` setters of the 34 States rows by `tools/state_setters.py` (new; 659 call sites, 391 resolved), 27 rows with a setter or clearer, 7 rows (6, 25, 29, 39, 116, 164, 171) `[L]` none found ([stats/0002](../findings/stats/0002-states.md#surprise-f-setters-scan-plan-0041-p1-review-follow-up-b-2026-10-17)). (c) optional, moved to its own reverser entry.
- **re-rule drlg/0002 rows 9 and 20**: row 20 `[C]` raised; row 9 raised in part (`[C]` no-draw fallback, fatal branch `[I]`); `sweep_s4a.py pick` re-run, 1 280 fallbacks, 0 roomk mismatches over 36 logs. Spec L337/L600 and step note 3 (L621) and L1023 need the spec-writer; inventory rows 9/20 are yours.
- **p38s4 NULL-callback note**: `[I]` line in [data/0004 § S1f](../findings/data/0004-cell-converters.md#plan-0038-batch-s1f-2026-10-17).
- **S1f tool follow-ups** (`GHIDRA_LOG` per-lane log; memory-spec rule in tooling.md), **d2sio CSvBits clamp** (13 268 comparisons, 0 mismatches), **S2c tool** (flag clobber + negative test; dispatch output unchanged), **H5e tool** (keyed counters; level 28's 3 rebuilds counted apart): tools, no tag.
- **plan 0037 close follow-ups**: (a) fire at the cap 2 115 from the re-run check (count, `[C]` run as before); (b) "never `boss`" moved to `[I]`.
Annotated, kept open: **H5e static reachability**: (e) `[I]` d-none (A1CliffMark skipped for level 2; one `or $0x20` in the DRLG range), (d) `[I]` d-none (the pool is one chain, at most 45 nodes), (a) `[I]` scan condition (an adjacency overlap of exactly 8 tiles); (b) and (c) not read. Skipped as needing harness (annotated): 0037 resume lane, H4b follow-ups, Phase 2 leftover pieces, S2c harness pieces. Please check against review-fixes rule 9: in (e) five callees are named as unfollowed.

*2026-10-17 (reverser, checkpoint):* left open for a later static batch (time limit reached, not started unless noted): H5e reachability (b), (c); S1e follow-ups (b) calc-emu under `emutrace`, (c) `sweep_s1e.py static` operand map; tool follow-ups S1a (a)–(c), S1b (a)–(b), S3b (a)–(c), H4b (a)–(b); S2c static leftovers (45 register-word quest sites, 12 range-clear callers); S3b static leftover (four callers of `0x005A0120`); P1c residues (a)–(e); 0040 P1 follow-ups (a)–(c); 0037 resume-lane follow-ups (Fleshripper log copy, total ≤ 0 counter) and the state-52 / event-9 reading; 0042 Phase 1 column readers and Phase 0 additions; 0043 Phase 1 inputs; Q23 `NpcStoreRec` readers; Phase 3 wording (H5c *Release*); S1a creation question; S2a tc 64; 0039 P1c review follow-ups (a needs a fetching lane; b noted); plan 0041 op 6/7 emulation (optional).
