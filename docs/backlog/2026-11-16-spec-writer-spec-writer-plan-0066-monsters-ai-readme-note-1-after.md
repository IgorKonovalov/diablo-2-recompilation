---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../specs/quirks/README.md
resolution: ""
---

Plan 0066 Phase 3, frame cluster (lane/n66pf): sim/frame's Reimplementation note 8 (the AI's second entry: at a mode end it runs inside that mode-end event, so its draws come at that event's place) is now [C] on S7b's count of AI draws by event kind (447 in monsters' kind-0 events, 992 in kind-2; run:2026-11-04-frame2, run:2026-11-04-frame3, frame/0007 § Plan 0066 batch S7b, sim-frame row 124). monsters/ai/README's Reimplementation note 1 states the same at [I] (monsters-ai-README row 48, routed to H1n, the nine mode-end call sites). Quirk Q500 now cites sim/frame n8 alone at [C], and monsters/ai/README n1 sits in the quirks Coverage table's 'Weaker duplicate' column. At the monsters/ai cluster's Phase 3: raise n1's mode-end clause on the S7b count (its 'nine call sites' half by its own route, H1n), then cite it again from Q500 and empty the column. Not blocking.
