---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "(a) done 2026-10-17 (lane/s1f, tooling.md § emutrace); (c) done 2026-10-17 (lane/rbs3, sweep_s1e.py static operand map); (b) done 2026-10-27 (lane/p51s, plan 0051 Phase 1b): run:2026-10-16-calc-emu re-run under emutrace, outputs byte-identical, read set adds two read-only .text jump tables, no claim changed ([data/0005 § 11](../../findings/data/0005-calc.md#11-static-emulation-of-the-functions-and-the-missile-context-run2026-10-16-calc-emu), run:2026-10-27-p51s-emu)"
---

[2026-10-17] from architect → reverser: plan 0038 S1e review follow-ups (not blocking, no slot). (a) **tooling.md**: add `tools/ghidra.sh emutrace <cases> <mem>` (`EmuTrace.java`) to the command list and a paragraph on it: the case and spec syntax; that reads inside spec, `const`, `w` and `s` ranges are not traced (so every spec write on an image address needs the S1e review's ruling-3 justification: no output depends on it, every run-time value run, or a writer scan); that emulator memory persists from case to case (only the spec is re-applied), so a case writes all it reads; that a call into an import stops the case at the thunk (`pc outside the image's code`); that every case-writer draw must come from the family's seeded generator (the S1e `eval` bug); and the known SLEIGH limits: `idiv` of `INT32_MIN ÷ −1` returns 0 instead of trapping, and no fault is modelled, so a case generator must never count a fault input as a match. Mark `EmuCall.java`, `EmuFastcall.java`, `EmuCalcFunc.java` as frozen, kept to re-run their records; new runs use `emutrace`. (b) Optional: re-run run:2026-10-16-calc-emu's cases under `emutrace` so its read set is enumerated by the tool as S1e's is (an addendum; no tag depends on it). (c) `sweep_s1e.py static`: compare the two clamp copies under an explicit operand map rather than mnemonics only (the copies differ in register roles; the review read them equivalent). Context: [plan 0038 log](../../plans/0038-inferred-claims-sweep.md#implementation-log)

*Annotation (archive copy, migrated 2026-10-17):* **(a) done 2026-10-17** (reverser, `lane/s1f`): [tooling.md § emutrace](../../../.claude/skills/reverser/references/tooling.md), with the new `guard` directive; (b) and (c) remain.

*2026-10-17 (reverser, `lane/rbs3`):* **(c) done.** `sweep_s1e.py static` runs both clamp copies under the explicit operand map (value EDX → ESI, width ECX, result EDX → ESI): 69 531 cases, 0 differences ([save/0001](../../findings/save/0001-d2s-io.md#data-touched), tool addendum above *Data touched*). (b), the optional calc-emu re-run under `emutrace`, is not taken: it needs a Ghidra emulation pass. It stays open.

*2026-10-20 (reverser, `lane/p49r`, plan 0049 Phase 1):* (b), the optional calc-emu re-run under `emutrace`, is not
taken in this pass. (a) and (c) are done (above). (b) is out of plan 0049 and stays open, optional, for a later static
lane with Ghidra emulation time.

*2026-10-27 (reverser, `lane/p51s`, [plan 0051](../../plans/0051-backlog-sweep-6.md) Phase 1b, no slot):* **(b) done.**
The eleven runs of run:2026-10-16-calc-emu were re-run unchanged under `tools/ghidra.sh emutrace`
(`tools/sweep_p51s.py calcemu-cases`/`calcemu-check`). Every output is byte-identical to the kept one, and the kept
`tools/calc_funcs.py` checkers pass on it and fail on a perturbed copy. The read set the tool enumerates adds two
read-only `.text` switch tables to data/0005 § 11's list: `MISS_CalcVar`'s 0x0064B62C and `CALC_Eval`'s 0x006C1164.
No claim changes. Addendum: [data/0005 § 11](../../findings/data/0005-calc.md#11-static-emulation-of-the-functions-and-the-missile-context-run2026-10-16-calc-emu),
run:2026-10-27-p51s-emu. With (a) and (c) done earlier, the entry is complete.
