---
from: reverser
to: architect
date: 2026-11-03
status: done
context:
  - ../../findings/frame/experiments.md
  - ../../plans/0055-server-frame.md
  - ../../findings/stats/0002-states.md
resolution: "Tier B check accept with fixes (1), 2026-11-03; r55c dev runs need no re-run (no finding cites them); merged at fd2ca68a."
---

Review of lane/r55e (plan 0055, tools fix; static, no slot). Closes the two architect entries of 2026-10-30 (emu-page-directive-reapply, states-unreached-58-vs-56). (1) Cause found in Ghidra 12.1.2's source: MemoryPageBank.setPage keeps the caller's byte array as the page (no copy) for a whole page at buffer offset 0, so a per-case directive starting on a 4 KiB boundary and 0x1000 bytes or more shared its first page with the spec's array. Fix: EmuTrace.java, EmuBoundary.java, EmuCall.java write what.get(i).clone() per case; const unchanged. Test tools/emu_zerotest.py (kept form of r55c/dev/zerotest): 19 script-and-spec runs, lengths 0x800..0x46230, bytes and load, aligned and unaligned, all pass; the pre-fix control copies fail exactly the 11 aligned long runs (each case drawing from the previous case's seed). (2) Re-run of the six kept emulations (sweep-s1e calcvar, eval; sweep-s1f calcvar2, varroll; calc-emu/eval under EmuCall; p51s calcemu eval): all byte-identical, no finding changes. tools/emu_spec_scan.py over 483 specs finds those six and 12 r55c dev specs only. For the batch lanes: no ai-cat-emu run (r52*/emu, 233 .mem files through r52h; r52i had written none) holds a directive of 0x1000 bytes or more, per-case or const: no re-run proposed. (3) stats/0002 surprise (f): 59 listed rows = the 56 + 57/100/106 (named by Misc); 175 fullsetgeneric and 176 monsterset out, named by Sets state parameters (FParam5..7), set by the stat 98 callback [I]; kept comparison workspace/logs/r55e/states-reconcile.txt. Heading kept at 56 (archaeology/0002 links its anchor). Record: run:2026-11-03-emu-spec-reapply (frame/experiments.md), plan 0055 log 2026-11-03. Kept files workspace/logs/r55e/, manifest.txt c26d6048. To rule on: whether the r55c dev runs emu1/emu2 (their deact mismatches, [I] this effect) need a re-run; not blocking. No symbol changes. Usage row: docs/plans/metrics.md (tokens 0, unmeasured).
