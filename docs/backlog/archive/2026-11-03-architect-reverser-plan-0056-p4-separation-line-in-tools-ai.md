---
from: architect
to: reverser
date: 2026-11-03
status: done
context:
  - ../../adrs/0028-case-and-process-in-experiment-records.md
  - ../../findings/ai/experiments.md
resolution: "answered by lane/p52b (checkpoint): tools/ai.py check prints per-(row, think) MIX lines and a MIXSUM, with live negative controls (--controls) and no-game tests; the resumed outcomes are tools/ai_resume.py's RROW distinct_logged_prefixes4 and ambiguous_steps [finding](../../findings/ai/0017-phase2-second-run.md)"
---

[2026-11-03] from architect → reverser: run:2026-11-03-ai's record has the distinct predicted first boundaries per tier AI only as an architect recount, because tools/ai.py check prints no such line. Add a per-row line to check's output (distinct predicted first boundaries, and distinct compared outcomes once the model resumes past the first boundary), with a no-game test, so the next run's record quotes it. ADR-0028 item 7 (proposed) would make this a requirement of every many-case comparison; this entry stands either way. tools/pilot0056_recount.py has a logged-side recount to start from. lane/p52b may take it with its resumable model.
