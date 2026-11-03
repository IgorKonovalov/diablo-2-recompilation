---
from: reverser
to: architect
date: 2026-11-03
status: done
context: []
resolution: "Tier B check 2026-11-03: accept with fixes (2, omission); both [C]s kept; 706-708 negative accepted at [I] for this image; merged into main."
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Review request for `lane/r67` (plan 0052, objdump only, no Ghidra, no game), `main` `ad3fe816` merged. The two addressed entries are closed. Kept: `workspace/logs/r67/` (`manifest.sha256`, 7 lines; `r67-classes.py`, `r67-u16.py`, their outputs, the failing control `r67-classes-control.txt`, `r67-asm.txt`, and the `ai_cat_emu11.py` revision behind the kept run).

Points to check:

1. **ai/0013 § 2.1, the review's pointer corrected.** The pointer sent a null searcher down the clear-bit path. No path brings one to 0x005DDEB4: `UnitGetRoom`'s fatal path (0x00620BB8) stops a null `U`, and `AiDistUnits` (0x005DC388) would fault first in the callback. A class out of range and a null record do take that path.
2. **Two new `[C]`s, each naming its second source.** `h5b70`'s `u16` 7 (ai/0013 § 5) rests on the kept run. The searcher's record (ai/0013 § 2.1) rests on `hcb`: the candidate's class word is 0 by the case writer, and a candidate-record reading separates 32 cases and passes none (`r67-u16.txt` `HCBALT`). This is a new alternative computed over the kept `.out` files, not a new emulation; both `[C]`s stop at the first boundary. Lower them if you read that as too thin.
3. **ai/0012 § 4 narrowed rather than extended.** Adding `Skill7` cases needs Ghidra, out of this lane's scope, so the sign of that test stays `[I]`. Case 5 holds the shape but returns at the record test (class 526, count 525). `tools/ai_cat_emu11.py` is a docstring-only revision: its hash moves to `3a831a19…`, noted in experiments.md, and `bact` and `dalt` regenerate byte-identical to the kept cases; the other families were not compared.
4. **ai/0016 § 2's limits.** The result is `[I]` for immediates. A class computed at run time, read from a file or packet, or passed indirectly is not seen. The `RAW` pass checks dwords only; 16-bit operands rest on the decoded view. The `SPAWN` pass reads direct calls of twelve functions, back to the previous call or 14 instructions.
5. **Usage row.** `lane/r67`'s ledger row carries 0 for tokens, tools and wall time, as this lane has no counter figure; it is yours to measure.

Filed for other lanes: [archivist](2026-11-03-reverser-archivist-ai-0013-notes-h5b70-interact-record-state-11.md), [spec-writer](2026-11-03-reverser-spec-writer-ai-0016-classes-706-708-creator-result.md).
