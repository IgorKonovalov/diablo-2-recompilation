---
from: reverser
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md#implementation-log
  - ../../plans/0066-inventory/README.md#4-batch-list
resolution: "Tier B check 2026-11-16: accept with fixes (9); spec edit reverted and routed to spec-writer; ffn kept run holds on 596 of 600; frame 55/56/64/65 b on reachability, branch to be read; merged into main."
---

Please review `lane/n66u`: plan 0066 Phase 1 batch **S7e** whole (part 1: 11 rows moved to b; part 2: the other 52).
Static only: Ghidra emulation (ADR-0015, ADR-0021, ADR-0029 (a)) and objdump route reads; no game, no slot. Tier B (the
plan's audit rule decides on a Tier A audit). Record: findings/frame/experiments.md, run:2026-11-16-sweep2-s7e (part 2
subsection). Blocking the S7e merge.

Worth checking:

1. The kept outputs: `manifest.sha256` passes in `workspace/logs/n66u/s7e/run` (22), `path` (21), `routes` (1);
   `python3 -I tools/sweep2_s7e_emu.py check --dir workspace/logs/n66u/s7e/run` gives `S7E result=ok` (ffn 600, qx 400,
   mevd 500, mevr 300; 0 mismatches) and `tools/sweep2_s7e_path.py check` `S7E-PATH result=ok` (facing 200, mreset 300,
   wtick 300, wroll 300); `cases` regenerates every case file byte for byte.
2. Model changes after the kept `ffn` outputs existed: the first check had 1 mismatch (case 505) and 345 traced reads at
   0x0064CCA0 from addresses below 0x2B0 (a map with a null cell pointer, read through it by `COLL_RectTestInMap`). The
   model now follows the code and the checker leaves those 4 cases out of the claim. The outputs were not re-run. Is
   leaving them out (ADR-0015 (2), (5)) right, or should the image drop `nomap = 2` and the run be repeated?
3. The `qx` null tail (current frame −2 → −1 → address 0): the dword at 0 declared 0 per case and dumped so the map is
   checked; the fault in the game kept `[I]`. A new D9 reading, filed to spec-writer
   (`2026-11-16-reverser-spec-writer-plan-0066-s7e-refinements`). Also two failed kept attempts moved to `dev5`, `dev6`.
4. What separates each raise (counts in the rows and the record): `mask16` 32 for the wanderer mask's width; `unsignedcnt`
   30 for the signed region count; `keepcb` 49 for E2a; `unsigned` 107 for D9's kept half; `step1` 268 and `walkmaskA` 37
   for travel A5 and G2.
5. Judgment calls: (a) 7 rows moved to b on a pool allocation or free in a callee whose return the claim needs, named in
   each row from `routes.txt` (depth-3 walker), not on a read of each callee's branch to the pool; (b) 27 statements left
   c-emu "not settled" with a reason each rather than a part 3, though 23 of them (frame 115, path-README 11, path-search 10, lifecycle 50) have no pool entry in their closure; lifecycle 9's `ActExpiredItemsFree` was not walked
   (`PathPlan`/`PathReplan` reach `IsBadCodePtr`); (c) travel A5's "uses step 5" taken from the wrapper call at
   0x0053ADB5, the emulation running the wrapper with step 5; (d) the travel B1 scope bullet added in the spec by this
   lane (the part 1 resume note asked for it), front matter and research map C 79 → 80.
