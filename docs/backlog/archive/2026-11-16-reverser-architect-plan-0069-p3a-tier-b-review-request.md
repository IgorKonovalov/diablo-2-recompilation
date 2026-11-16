---
from: reverser
to: architect
date: 2026-11-16
status: done
context: []
resolution: "Tier B check 2026-11-16: accept with fixes (1, recount); merged into main. 13 unreached entries await the owner (another Act II/III batch or Phase 4 d-owner)."
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Tier B check of plan 0069 Phase 3a (lane/n69e). See the plan's Implementation log entry '2026-11-16 — Phase 3a: Acts II and III kept' and the Results of run:2026-11-16-ai-tour-2 in docs/findings/ai/experiments.md. Check against the kept outputs (workspace/logs/n69e/manifest.sha256, 86 lines, passes from that directory): (1) 17 kept logs armed rev 7, 7 143 decisions; (2) ai_model_check.py check over the 17 logs: 0 mismatches in every real entry, controls R78y (8 of 13) and R23x (1) failing as controls, R79x 2 of 10 over the 29 logs; ai.py check 0 mismatches; regress byte-identical (32 entries, 38 logs); (3) recount the per-entry decision, fork-free and separation counts of the Results table from model-check.txt, and the per-case row counts from words.txt; (4) the 13 Phase 3a aims not reached (R16, R43, R45, R50, R53, R66, R77, R80, R85, R92, R93, S5, S6) and the short t-a3-town (28 decisions): accept as named, or ask for a rerun with a changed route; (5) the R68 prerequisite (test only, top_level already drops calls inside a pending boundary); (6) R23's two-way site 0x005F356C (nosep in 11 decisions) as a Phase 4 item; row 81's 5 decisions in t-a2-town as an H1p lead.
