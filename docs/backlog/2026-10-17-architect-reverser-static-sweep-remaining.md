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
