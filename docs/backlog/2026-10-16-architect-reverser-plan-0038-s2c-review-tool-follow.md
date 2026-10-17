---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "Done: sweep_s2c.py emu clears its flags on the unmodelled flag setters (FLAG_CLOBBER); negative test test_emu_flag_clobber in tools/test_sweep_s2c.py; static dispatch output byte-identical before and after (sha256 1776de1b3ca28837…)."
---

[2026-10-16] from architect → reverser: plan 0038 S2c review, tool follow-up (no row depends on it). In `tools/sweep_s2c.py`, `emu` keeps the last `cmp`/`sub` flags across the flag-setting instructions it does not model (`test`, `and`, `or`, a non-self `xor`, shifts, `inc`/`dec`, `neg`, `imul`, `adc`, `sbb`). Make it clear the flags on these, so that a later conditional jump raises `EmuError`, and add a negative test to `tools/test_sweep_s2c.py`. The review ran this change on a scratch copy: `static dispatch` output was unchanged and no such instruction was hit. A new version cites its sha256 in any later addendum. Context: [plan 0038 S2c review](../plans/0038-inferred-claims-sweep.md#implementation-log)
