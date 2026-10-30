---
from: architect
to: reverser
date: 2026-10-30
status: open
context:
  - ../findings/frame/0003-timers-activation.md
  - ../plans/0055-server-frame.md#implementation-log
resolution: ""
---

Tools fix (plan 0055 P1 review, lane/r55c). frame/0003 Dead ends: a per-case memory-spec directive of 0x1000 bytes or more is not re-applied before each case by re/ghidra_scripts/EmuBoundary.java (dev/zerotest: 0x800 and 0xFFF re-zero, 0x1000 and 0x1800 at an aligned address do not; the previous case's writes stay). EmuTrace.java and EmuCall.java re-apply their specs the same way (EmulatorHelper.writeMemory per case), so they are presumed affected. (1) Fix the three scripts so a per-case directive is written in chunks that never cover a whole 4 KiB page (or find the emulator call that invalidates a page), with a no-case-dependence test in the kept form of dev/zerotest; const directives are written once by design and are not affected. (2) Re-run, with the fixed scripts, the six earlier kept emulations whose per-case specs hold such a directive, and compare each output byte for byte with the kept one: workspace/logs/sweep-s1e calcvar and eval, sweep-s1f calcvar2 and varroll, calc-emu/eval (EmuCall, a 0x46230-byte load at 0x7F800000) and p51s/emu/calcemu eval. The review's scan (python over every memory spec under workspace/logs: 421 specs) found no case 'w' write into any of those directives' ranges, so only a store by the emulated code itself into one could have carried between cases; these are calc and table readers, so no change is expected, but nothing excludes it until the re-run. No Ghidra slot is needed beyond one headless run per family; not blocking plan 0055 Phase 2a (a log replay, no emulation).
