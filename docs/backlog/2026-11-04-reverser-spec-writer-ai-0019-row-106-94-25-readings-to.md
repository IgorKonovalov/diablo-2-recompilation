---
from: reverser
to: spec-writer
date: 2026-11-04
status: open
context: []
resolution: ""
---

**Asked:** carry [ai/0019](../findings/ai/0019-row-tables-and-scoring.md), as reviewed, into [catalogue](../specs/monsters/ai/catalogue.md) R106, R143, R94 and R25, in P3c's pass (the owner's decision, plan 0052's log). Blocks the plan's close, not P3c's start. Take the catalogue after `lane/r71` is merged; this lane edited nothing in it but two archive links. The tag of everything below is `[I]` unless it says `[C]`; don't raise it (the review's evidence ruling).

**R106.**
- `aip` line: replace "`aip1[h]` is read by a score term (step 13)" with § 5 point 2: `aip1[n]` squared in cases 4 and 12, `aip1[m]` added in 4, 12, 13, `aip1[h]` in the `state` word and case 4; each by column, not by difficulty (§ 1.1).
- Step 13: replace with § 1.2's loop, § 1.1's table of inputs (`melee` is the event's word and is not recomputed; "hostile" is the callback's whole gate, R106b), § 1.3's cases with `Aura()`, § 1.4's draw table and the `EType` map (byte 12 → 43; a blank cell is byte 0 and reads stat 36; `stun` is byte 9 and reads nothing). "A kept one draws" is wrong: the draw comes before the list's test. Case 6's draw is `Range(100)`, and cases 9 and 10 draw nothing. Step 13's `− res ÷ 10` and § 1.2's `res ÷ −10` are the same value under truncation; write § 1.2's.
- Steps 12, 14 to 16 hold as written; add to 14 that `L[0]` is walked last and the zero words go to `Use`'s last two (§ 1.5).
- R106a: `+8`/`+0xC` become the record's `+0xC`/`+0x10`, `+8` being the score (§ 5 point 3); drop its "per-`aitype` terms are read by no finding".
- New lettered bullets: § 1.3's "self-targets cannot command"; § 1.3's wrap paragraph as reviewed; § 1.2's room for 48 records and no cap on `k`; § 1.6's check, named as a check of the reading, with its limits: every callee stubbed, `RNG_Range` included, `use1_held`'s lower side resting on its instruction, the 6 one-way branches.
- `[C]` here is the data only: the stock `aitype`s 1, 2, 3, 4, 5, 10, 11, 12, 13, 32 rows, so no stock skill reaches cases 6, 7, 8 (tbl:Skills.txt:aitype).
- Open questions: delete "The Shadow Master's scoring loop". Strike rows 106 and 143 wherever the catalogue names them short of the Done-when. R106l stands.

**R143.** Nothing but the link to R106: its think is the same word. § 4: no MonStats record names it, as R143 says.

**R94.**
- R94a: replace "neither is in the finding, Open questions" with `SWEEP` listed and `STEP` by rule (§ 2), each with its address and reader. Copy `SWEEP`'s table exactly, header line included: `tools/ai_const_survey.py` compares any copy of that form in the catalogue with the image. `STEP`'s two formulas with `j`, `k`, `clamp`. The `[C]` of each is § 2's, an equality on the image's elements (ADR-0031), and not how the table was made. `[I]` each `SWEEP` value is 0 to 7.
- Open questions: delete "Row 94's two tables". Add as `[L]` § Open questions' two: `SWEEP`'s odd cell, and `STEP[i]` against `Dir64To8`'s index.
- R94l stands. Row 94 is also in P3c's batch 8: read the block as that pass does.

**R25.**
- R25a: add `A5` as listed (§ 3's line, exactly), `B5[p] = A5[((p + 1) mod 5) + 1]`, and `A` and `B` as listed in § 3's two blocks. Copy them exactly, first line included (the survey compares that form too): `python3 -I tools/gate.py --full` goes red on a mistyped value. The tables' `[C]` as an equality on the image's stores goes with them, with `run:2026-11-04-r71-sm`; don't state a rule for `A` or `B`, as none is known.
- Dance step 5: `B[e]` = `(0, 0)` at `v14` = 12, place 4 only; `B5` has none, so that arm with `v14` = 5 is reached by no value of the image.
- R25c: replace "The table values and what event 12 does are Open questions" with § 3's event 12, `[I]`: at the end frame `EVENT_TimedListExpire` frees the list by [stats/states C1](../specs/stats/states.md); the grant has no state, so C2 has no part; death may free it first (C3). The think holds the tables on the stack at each entry, none depends on an input, and a reimplementation may hold them as constants.
- Open questions: delete "Row 25's dance". R25l stands; add § 4's reach as data under it: `[C]` the levels and the superunique, since 0 lines is coverage, not reach.

**Not taken:** `tools/`, the checksums, the rule scan's detail (one clause at most: none of those forms gives `A` or `B`), and any count of listed constants.
