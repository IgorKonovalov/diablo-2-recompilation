---
from: reverser
to: architect
date: 2026-11-03
status: done
context:
  - ../../findings/path/0002-search.md
  - ../../plans/0054-path-search.md
resolution: "Tier B check 2026-11-03: accept with fixes (4). P1.3a may build on EmuScratch.java after a one-case negative probe and the U-line and U_OK fixes; largest-room entry filed to the archivist; merged into main."
---

Plan 0054 P1.2 for review. Finding path/0002, run:2026-11-03-path-emu-2 (2 236 cases, 0 mismatches). Points to read: the first item (types 1, 15 and greedy-near do not call the search; all go to P1.3a); the new script EmuScratch.java and the two accounted scratch reads (0x006831D7, 0x0067AB46); row and tries separated at type 0 only in open and rect (5, 2 cases each), none in real0 (§ 5); the frame overrun before the assert (§ 9), its stock reach open; the plan's byte-store range corrected to 0x0058929F-0x00594647 (§ 10); the image: near lists declared, the target's marks not tied to a flag (§ 11).
