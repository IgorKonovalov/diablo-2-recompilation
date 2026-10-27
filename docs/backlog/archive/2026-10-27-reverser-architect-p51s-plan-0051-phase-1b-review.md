---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0051-backlog-sweep-6.md#implementation-log
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (6). Rulings (a)-(e) and the fixes in the plan 0051 log, Phase 1b review entry."
---

Review plan 0051 Phase 1b (branch `lane/p51s`, from `main` `7ff8d98`; no slot, one headless Ghidra on `workspace/ghidra-p51s`, `-Xmx3G`; no game). Items: (1) the op 6/7 emulation entry (closed): run:2026-10-27-p51s-emu, [stats/0001 § 10](../../findings/stats/0001-aggregate.md#10-op-6-and-7-under-emulation-run2026-10-27-p51s-emu-plan-0051-phase-1b), 9 000 calls, 0 mismatches, `[C]` as a code map; (2) the S1e follow-ups (b) (closed): the calc-emu re-run under emutrace, byte-identical outputs, two read-only .text jump tables added to [data/0005 § 11](../../findings/data/0005-calc.md#11-static-emulation-of-the-functions-and-the-missile-context-run2026-10-16-calc-emu); (3) the MP31/MP32 forwards: [multiplayer/0002](../../findings/multiplayer/0002-trade-and-party-gold.md) (new, `[I]`), the plan 0044 shortfalls entry annotated, still open. Record in [stats experiments](../../findings/stats/experiments.md#run2026-10-27-p51s-emu); tool `tools/sweep_p51s.py`; outputs `workspace/logs/p51s/emu/` (manifest `b16c2780…`) and `workspace/logs/p51s/static/`. 15 symbols added (I). **Points to rule on:** (a) op 6/7's `[C]` is a map only (ADR-0015 (3)); the contradicted lead stays contradicted for the code, with its play meaning not covered: is that the right wording for the lead verdict? (b) The calc-emu negative control is the kept checkers failing on a perturbed copy (EAX + 1) plus the sibling-output counts, not a new perturbed model: enough for an addendum on which no tag depends? (c) `PartyGoldShare`'s payment loop tests the picker's mode (`mov ecx, esi` at 0x00540A73/0x00540A7E), so a dead member is paid but not counted; the decompile shows the member. Read from the disassembly only, `[I]`; it needs three or more players to observe. (d) The MP31 prediction leaves the copy's unit id to be logged (`ItemCopy` not followed). Context: [plan 0051 log](../../plans/0051-backlog-sweep-6.md#implementation-log)

*2026-10-27 (reverser, `lane/p51s`), after merging `main` `0e3f501`:* **item 3a added** (named at the P0b review).
`DataTables+0x17C`/`+0x180` is filled by `STATES_Load` with the States rows of flag bit 16, `disguise`, `[I]`
([skills/0013 § 6](../../findings/skills/0013-druid.md#6-the-melee-functions-start-56-57-58-do-121-122)); the archivist's
States bullet has its own [entry](2026-10-27-reverser-archivist-states-0x17c-list-is-the-disguise-flag.md). (e) Point
to rule on: "no other writer" is not claimed, since four `[esi+0x17c]` stores in 0x00538D64–0x0053A1F2 have unfollowed
base registers. Static outputs: `workspace/logs/p51s/static/manifest.txt` `7436cda5…`.
