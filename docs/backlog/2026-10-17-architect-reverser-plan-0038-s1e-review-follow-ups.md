---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-17] from architect → reverser: plan 0038 S1e review follow-ups (not blocking, no slot). (a) **tooling.md**: add `tools/ghidra.sh emutrace <cases> <mem>` (`EmuTrace.java`) to the command list and a paragraph on it: the case and spec syntax; that reads inside spec, `const`, `w` and `s` ranges are not traced (so every spec write on an image address needs the S1e review's ruling-3 justification: no output depends on it, every run-time value run, or a writer scan); that emulator memory persists from case to case (only the spec is re-applied), so a case writes all it reads; that a call into an import stops the case at the thunk (`pc outside the image's code`); that every case-writer draw must come from the family's seeded generator (the S1e `eval` bug); and the known SLEIGH limits: `idiv` of `INT32_MIN ÷ −1` returns 0 instead of trapping, and no fault is modelled, so a case generator must never count a fault input as a match. Mark `EmuCall.java`, `EmuFastcall.java`, `EmuCalcFunc.java` as frozen, kept to re-run their records; new runs use `emutrace`. (b) Optional: re-run run:2026-10-16-calc-emu's cases under `emutrace` so its read set is enumerated by the tool as S1e's is (an addendum; no tag depends on it). (c) `sweep_s1e.py static`: compare the two clamp copies under an explicit operand map rather than mnemonics only (the copies differ in register roles; the review read them equivalent). Context: [plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log)

*Annotation (archive copy, migrated 2026-10-17):* **(a) done 2026-10-17** (reverser, `lane/s1f`): [tooling.md § emutrace](../../.claude/skills/reverser/references/tooling.md), with the new `guard` directive; (b) and (c) remain.
