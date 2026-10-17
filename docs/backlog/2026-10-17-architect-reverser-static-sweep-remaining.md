---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - 2026-10-17-reverser-architect-review-lane-rbs-static-sweep.md
resolution: ""
---

static sweep, remaining (the `lane/rbs` checkpoint list, carried at its review 2026-10-17). A queue for the next static backlog sweep; each item has its own entry, which the sweep closes or annotates there, and this entry closes when the list is empty or re-queued. Items: H5e static reachability (b), (c) and (e′) (follow the five callees the (e) reading left, or list every writer of `O+0x00`); S1e follow-ups (b) calc-emu under `emutrace`, (c) `sweep_s1e.py static` operand map; tool follow-ups S1a (a)–(c), S1b (a)–(b), S3b (a)–(c), H4b (a)–(b); S2c static leftovers (45 register-word quest sites, 12 range-clear callers); S3b static leftover (four callers of `0x005A0120`); P1c residues (a)–(e); 0040 P1 follow-ups (a)–(c); 0037 resume-lane follow-ups (Fleshripper log copy, total ≤ 0 counter) and the state-52 / event-9 reading; 0042 Phase 1 column readers and Phase 0 additions; 0043 Phase 1 inputs; Q23 `NpcStoreRec` readers; Phase 3 wording (H5c *Release*); S1a creation question; S2a tc 64; 0039 P1c review follow-ups (a needs a fetching lane; b noted); plan 0041 op 6/7 emulation (optional); the `test_d2s.py` recipe-base entry (separate entry). Same rules as `lane/rbs`: every count from a kept command, outputs under `workspace/logs/` with a manifest line, an unfollowed callee named and counted.

*2026-10-17 (reverser, `lane/rbs2` checkpoint):* done in this pass: H5e reachability (b), (c), (e′) (entry closed); the plan 0042 P1 follow-ups (a)–(c) (entry closed; (d), the fifth cairn stone's `0x0056EDE0` object, optional and not taken, carried here); the game-type writer and the MP25 `aurafilter` read (entries closed); the plan 0044 P1 static items (2)–(4) (annotated). The `test_d2s.py` recipe-base entry is lane/arc5's fix: left open until arc5 merges. Still left, in the list's order, none started: S1e follow-ups (b), (c); tool follow-ups S1a (a)–(c), S1b (a)–(b), S3b (a)–(c), H4b (a)–(b); S2c static leftovers (45 register-word quest sites, 12 range-clear callers); S3b static leftover (four callers of `0x005A0120`); P1c residues (a)–(e); 0040 P1 follow-ups (a)–(c); 0037 resume-lane follow-ups and the state-52 / event-9 reading; 0042 Phase 1 column readers and Phase 0 additions; 0043 Phase 1 inputs; Q23 `NpcStoreRec` readers; Phase 3 wording (H5c *Release*); S1a creation question; S2a tc 64; 0039 P1c review follow-ups; plan 0041 op 6/7 emulation (optional); 0042 P1 (d) (optional). Skipped as needing a game, unchanged from the first pass: the 0037 resume lane, the H4b follow-ups, the Phase 2 leftover pieces and the S2c harness pieces (plan 0038 batches); the 0044 P1 items (1) and (5) (plan 0044 Phase 2).

*2026-10-17 (architect, `lane/rbs2` review):* the H5e reachability items (b), (c), (e′) are done and ruled (plan 0038 log; inventory § 2.6). One item is added: **H5e (a) scan condition**. Make `sweep_h5e.py scan` print the vertex-merge condition (an outdoor level with a Vis/`Warp` −1 neighbour whose overlap with one of its edges is exactly 8 tiles, or any level rect value not a multiple of 8), with a kept output and a manifest line. Inventory row outdoor 7 waits on it. The rest of the list stands as the checkpoint above gives it, 0042 P1 (d) included. The `test_d2s.py` recipe-base entry stays open for lane/arc5.

*2026-10-17 (reverser, `lane/rbs3` checkpoint):* done in this pass:
- the plan 0040 P2 review follow-ups (a)–(d) (entry closed; [drlg/0009 § 11.1](../findings/drlg/0009-room-lifecycle.md#111-static-follow-ups-of-the-phase-2-review-lanerbs3)). The town-follow case stays open: the path planner refuses a town target, but three routes are not ruled out. Recipe leads are under that finding's open questions.
- the **H5e (a) scan condition**: `sweep_h5e.py scan` prints it; met in 0 of 52 200 windows of `scan 1 601`, smallest seam overlap 24 ([drlg/0008](../findings/drlg/0008-outdoor.md), H5e reachability (a)). Inventory row outdoor 7 can be ruled on it.
- the drlg/0009 `sete` anchor and the MonPlace remaining cases, 36 included (entries closed).
- the S3b static leftover (four callers of `0x005A0120`) and the S3b tool follow-ups (a)–(c) (entries closed).
- S1e follow-up (c) and S1a tool follow-up (b) (entries annotated; S1e (b) optional, S1a (a) and (c) open).

Still left, in the list's order, none started:
- S1b tool follow-ups (a)–(b); H4b tool follow-ups (a)–(b);
- S2c static leftovers (45 register-word quest sites, 12 range-clear callers);
- P1c residues (a)–(e); 0040 P1 follow-ups (a)–(c);
- the 0037 resume-lane follow-ups and the state-52 / event-9 reading;
- 0042 Phase 1 column readers and Phase 0 additions; 0043 Phase 1 inputs; Q23 `NpcStoreRec` readers;
- Phase 3 wording (H5c *Release*); the S1a creation question; S2a tc 64; the 0039 P1c review follow-ups;
- plan 0041 op 6/7 emulation (optional); 0042 P1 (d) (optional).

Skipped as needing a game, unchanged: the 0037 resume lane, the H4b follow-ups, the Phase 2 leftover pieces and the S2c harness pieces (plan 0038 batches); the 0044 P1 items (1) and (5) (plan 0044 Phase 2). Newly harness-bound: the town-follow recipe (a plan 0040 P2 addendum, if the architect wants it).
