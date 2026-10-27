---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../findings/save/0001-d2s-io.md#plan-0038-r1h-the-host-callback-setter-and-the-d2sio-model-2026-10-27
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (3). Rows 3/19 → d-none and the callback halves of rows 2/18 accepted; the 0x0052BFCF read does not change ruling (d); d-none with an [I] absence fits the class; totals static 567, harness 521, blocked 419 (d-none 293), 1 526. Plan 0038 log."
---

Review `lane/r1h`, the reverser follow-up to the `lane/h1b` review's rulings (d) and (i). It is static work and used no slot.

1. **Setter.** `tools/ghidra.sh findptr` (new, `re/ghidra_scripts/FindPointer.java`) finds nothing that reaches 0x0052C0E0 or 0x00534630 on six channels: references, VA/RVA bytes, immediates, raw relative branches, exports and fall-through. Each channel found its control in the same run (`workspace/logs/r1h/findptr-r1h.txt`). The absence is tagged `[I]`, since a target computed at run time is not excluded. Proposed: rows 3 and 19 shortfall → d-none, and the callback halves of rows 2 and 18 d-none as halves. Totals against `main` `2b087d2c`: static 567, harness 521, blocked 419 (d-none 293): 1 526. Symbols `sub_0052C0E0_SetHostSaveCallback` and `sub_00534630_PlrSaveWrapper` were added (I).
2. **d2sio.** `tools/d2sio.py` `2ac6e9f1…` → `29561293…` and `tools/sweep_h1b.py` `c0063a8b…` → `b2d9ac1a…`. The re-check `sweep-h1b-check-r1h.txt` (`c39fd4bd…`) gives 2 798 comparisons, 0 failing and 0 d2sio mismatches. Its diff against `sweep-h1b-check-r2.txt` is only the rt-r2 and hell-r3 D2SIO blocks. The run:2026-10-12 logs are unchanged (`d2sio-regress-r1h.txt`). Manifest: `workspace/logs/r1h/r1h-manifest.sha256` (`94f2b304…`), checked from that directory.
3. `tools/h1b_sessions.py` now keys its copies on the log stem.
4. A side finding, `[I]`: the callback is an object. Undisassembled code at 0x0052BFC0 jumps through `[0x00883D50]+0x3C`; its callers were not followed.
