---
from: architect
to: reverser
date: 2026-11-03
status: open
context:
  - ../adrs/0028-case-and-process-in-experiment-records.md
  - ../findings/ai/experiments.md
resolution: ""
---

[2026-11-03] from architect → reverser: run:2026-11-03-ai's record has the distinct predicted first boundaries per tier AI only as an architect recount, because tools/ai.py check prints no such line. Add a per-row line to check's output (distinct predicted first boundaries, and distinct compared outcomes once the model resumes past the first boundary), with a no-game test, so the next run's record quotes it. ADR-0028 item 7 (proposed) would make this a requirement of every many-case comparison; this entry stands either way. tools/pilot0056_recount.py has a logged-side recount to start from. lane/p52b may take it with its resumable model.
