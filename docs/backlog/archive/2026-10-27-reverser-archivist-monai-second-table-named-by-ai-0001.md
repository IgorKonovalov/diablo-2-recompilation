---
from: reverser
to: archivist
date: 2026-10-27
status: done
context:
  - ../../findings/ai/0001-machinery.md#3-the-ai-table-and-its-dispatch
  - ../../plans/0052-monster-ai.md
resolution: "MonAI.md § The second table and its open question now cite ai/0001 § 3 with its [I] tags (callers, 18 rows, gate, setters); tools/ai_survey.py gained a states command and st_* summary keys (baseline updated) [MonAI](../../tables/MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review)"
---

Plan 0052 P1.1 (`lane/r52`) names the second table of `docs/tables/MonAI.md` § The second table at `0x0073D358`:
`g_MonAiStateRows`, 18 state rows indexed by the AI control's state word `AiCtl+0x00` (ai/0001 § 3). Once the lane
is accepted, please (a) link MonAI.md § The second table and its last *Open questions* bullet to ai/0001 § 3
(`MonAiEntryGet`'s three callers all pass a state word: 0x005B1663 the stored `AiCtl.state`, 0x005B0E81 the current
one, 0x005B0EBE the new one; the row count 18 from `MonAiInit`'s `< 18` test at 0x005B0E4D; the gate 0x00623470 for
states 10–12; who sets each state), keeping the tags the finding gives (`[I]`); (b) per the `lane/a52` review ruling
(e), add the 18 state rows to `tools/ai_survey.py` as the first table is read (the reverser's
`tools/ai_machinery_scan.py rows` prints them as `ST` lines, if a cross-check helps). Not blocking: P1.2 onward
reads the finding.
