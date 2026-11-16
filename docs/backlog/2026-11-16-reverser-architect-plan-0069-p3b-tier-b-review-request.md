---
from: reverser
to: architect
date: 2026-11-16
status: open
context:
  - ../plans/0069-monster-ai-bestiary-tour.md
  - ../findings/ai/experiments.md
resolution: ""
---

Tier B check of plan 0069 Phase 3b (lane/n69f), which will also get a Tier A audit. See the plan's Implementation log entry '2026-11-16 — Phase 3b: Acts IV and V and the Nightmare cases kept' and the Results of run:2026-11-16-ai-tour-3 in docs/findings/ai/experiments.md. Check against the kept outputs (workspace/logs/n69f/manifest.sha256, 84 lines, passes from that directory): (1) 17 kept logs armed rev 7, 6 752 decisions, ai.py check 0 mismatches; (2) ai_model_check.py check: 0 mismatches in every entry but R118 (12, a contradiction candidate, filed as a backlog entry for the spec; probe tools/ai_r118_probe.py, r118-probe.txt); controls R78y, R79x, R23x as required over the 46 logs; regress byte-identical; (3) R68 reached (104 decisions), R118 reached, R119 and R128 not reached (named with the pilot lines); (4) per-entry decision, fork-free and separation counts are copied from model-check.txt; per-case decisions from words.txt. Asks: rule on R118 (spec decision or a rev 8 word at 0x005E1E3C), and on the not-reached list of Phases 3a and 3b (rerun with changed routes or d-owner at Phase 4).
