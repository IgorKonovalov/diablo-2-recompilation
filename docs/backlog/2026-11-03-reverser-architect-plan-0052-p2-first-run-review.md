---
from: reverser
to: architect
date: 2026-11-03
status: open
context:
  - ../findings/ai/0015-phase2-first-run.md
  - ../findings/ai/experiments.md
resolution: ""
---

Review request, plan 0052 Phase 2 first lane run (lane/p52a, run:2026-11-03-ai) and plan 0056 Phase 3 pilot. Finding ai/0015 and the run record: 14 645 decisions in 31 kept case logs, 12 614 compared, 0 mismatches, 15 not comparable (rev 2 window), all 18 tier AIs at least 50; 19 symbol rows raised I to C (first boundary only); PathPlan seed unchanged on 9 618 calls; SrvStart inside the event 899 of 899; state record: all 32 324 events state 0, no live control. To rule on: (1) the 'compared' scope (first boundary, five hand maps) for the tier floor; (2) the 15 unlogged Scarab decisions kept out of the compared count; (3) Fetish and Andariel chained pairs below 20; (4) the Done-when items left short (H1 331 gaps, Raven, P1b-1, P1b-2, state control, catalogue sample batches 5/7/10/11/12), named in the 0052 log with the resume note; (5) the 0056 pilot figures: launches per kept case 0.32 met, dev/rerun launches 53 percent missed, wall and tokens met, two fresh re-runs 0 mismatches; the prompt supplied the per-batch process-sharing opt-in (owner answer 2), Phase 3 names this batch. Kept manifests: workspace/logs/ai/manifest-run-2026-11-03-ai.sha256 (72 lines), manifest-dev.sha256 (44).
