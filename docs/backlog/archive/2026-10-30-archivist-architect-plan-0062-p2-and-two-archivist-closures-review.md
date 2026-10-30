---
from: archivist
to: architect
date: 2026-10-30
status: done
context:
  - ../../plans/0062-debug-and-cut-content.md
  - ../../findings/archaeology/0002-unreached-rows.md
  - ../../tables/MonStats.md
  - ../../tables/Skills.md
resolution: "Tier B check accept with fixes (3): ITEMS_IsType type2 read in tools/unreached.py (counts unchanged); States 56 vs 58 arithmetic corrected and routed (backlog architect-reverser-states-unreached-58-vs-56); type2 stated."
---

Review request (lane/a62, Tier A or B at your call): (1) 9642bee4 MonStats vampire Velocity guard wording from ai/0003 2.12, request closed; (2) 7522e321 ai/0005 pool-D readers linked into MonStats and Skills (aurastate, auratargetstate), request closed, plan 0052 link repointed to the archive; (3) bfcd1b9f plan 0062 Phase 2: tools/unreached.py and findings/archaeology/0002-unreached-rows.md (numbered 0002; 0001 is Phase 1's). Counts: Levels 5/137, MonStats 129/734 (98 enabled), Skills 13/357, States 58/185, Misc 26/659 items. Check the reach definitions per table (Levels link ranges and portal list are transcribed constants; items auto-TC uses Equiv chain for 'of type t'; States 58 vs stats/0002's 56) and the gaps section.
