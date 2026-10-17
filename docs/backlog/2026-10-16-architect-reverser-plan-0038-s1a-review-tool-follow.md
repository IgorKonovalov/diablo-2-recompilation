---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-16] from architect → reverser: plan 0038 S1a review, tool follow-ups (no row depends on them). In `tools/sweep_s1a.py`: (a) `survey`: print the empty-list breakdown by group, quality and ilvl (`affix_items_empty_main_list` is one number; the review needed a scratch script to see that 48 of 53 are ilvl-1 magic items); (b) `static`: pin the set-list loop (0x0062D8D4–0x0062D8F0: `shl eax, cl`, `test`, `[ecx*4+0x6e90b8]`) and the runeword pass (`0xab` at 0x0062D8C8), which the rows 98/99 ruling rests on; (c) the corpus admission for the `qit*` samples (edited CharStats and CubeMain) next to the props-forced one in the `corpus` notes. Context: [plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log) (S1a review)

*2026-10-17 (reverser, `lane/rbs3`):* **(b) done.** `sweep_s1a.py static` pins the runeword pass (`mov [ebp+0x14], 0xab` at 0x0062D8C8) and the set-list loop (0x0062D8D7–0x0062D8F0: `shl eax, cl`, `test edx, eax`, the `je`, `[ecx*4+0x6e90b8]` and the `0x2040` mask). That makes 45 pins, 45 matching (`workspace/logs/sweep-s1a-static-rbs3-2026-10-17.txt`, manifest `sweep-rbs3-manifest.txt`). (a), the survey's empty-list breakdown, and (c), the `qit*` corpus admission note, are still open.
