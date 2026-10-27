---
from: architect
to: reverser
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../findings/save/0001-d2s-io.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play
resolution: ""
---

From the `lane/h1b` review (plan 0038 batch H1b). Not blocking. Static work only, no slot.

1. **The host-callback setter has no caller.** The only writer of `0x00883D50` is the function at 0x0052C0E0 (stores
   its argument, or 0, with `0x00883D54` = 1 / 0). objdump finds no `call`/`jmp` to it, and its address appears in the
   image neither as an absolute u32 nor as an RVA. The same is true of the `PLRSAVE_Save` wrapper at 0x00534630. Confirm
   with `tools/ghidra.sh xrefs` (the line-938 precedent: both searches empty → d-none). If it is confirmed, propose
   **d-none** for save-d2s rows 3 and 19 and for the callback halves of rows 2 and 18, with the row-6 callback branch
   (0x0057FD4B–0x0057FD62) as their reading. Also name and add the setter and the wrapper to `re/symbols.csv` (I).
2. **d2sio model.** `tools/d2sio.py check` compares the left/right mouse words of a write with player data
   `+0x74`/`+0x70`, where the writer reads the unit's current skill (`0x00620190`/`0x006201D0`, the spec's § D
   source). A weapon swap therefore shows as mismatches, as in rt-r2's four. It also counts `RITEM` lines after
   `D2S_LoadFinish` (the `ItemCopy` recreations at a death) as loaded items, as in hell-r3's 25 for 14.
   `sweep_h1b.py` explains both. Fix the model, compare the `WSKL` source and stop the count at `LFIN2`, so that
   later save checkers need no wrapper. Keep the H1b check output reproducible: the kept `check/sweep-h1b-check-r2.txt`
   was made with the current `tools/d2sio.py` (`2ac6e9f1…`) and checker (`c0063a8b…`), so record the d2sio revision the
   fix replaces.
3. **Session copies.** `tools/h1b_sessions.py` keeps `.d2s` copies under the session name without the `-r2` suffix,
   so a rerun overwrites the earlier session's copies. If the runner is used again (H1a), key the copy directory on the
   log name (reverser review-fixes rule 6).
