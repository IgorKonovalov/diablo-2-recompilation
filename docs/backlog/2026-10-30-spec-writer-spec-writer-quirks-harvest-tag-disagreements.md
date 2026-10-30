---
from: spec-writer
to: spec-writer
date: 2026-10-30
status: open
context:
  - ../specs/quirks/README.md#coverage
  - ../specs/combat/README.md#reimplementation-notes
  - ../specs/anim/README.md#reimplementation-notes
resolution: ""
---

Plan 0057 Phase 1 harvest (lane/s57): three overview notes keep a statement at [I] that another reviewed spec states [C]; the quirks index takes the raised statement (owning spec wins) and routes the weaker ones here for a fix of the owning overview, not a second version in the index. (1) combat/README note 4 ('its entries draw') keeps entries 37, 39, 41 and 143 stepping the attacker's seed at [I], while combat/delivery note 9 and skills/dispatch note 4 state it [C] (ADR-0021, run:2026-10-21-cat-emu-ass); entry 38's draws stay [I] in all three. (2) combat/README note 5 keeps 'a weapon-share missile always steps its owner's seed once for stat 337' at [I], and skills/README note 2 ('drawn at 0') at [I], while skills/missiles note 3 states it [C] (run:2026-10-25-skills); the deadly-strike and mastery clause stays [I]. (3) anim/README note 2 keeps the breakpoint tables' N = n - 1 and the server's start at the request at [I], while anim/timing note 1 states both [C] (run:2026-10-27-anim). Fix: split each overview note, raising the clause the owning spec raises (review-fixes rule 8), then re-run python3 -I tools/quirks.py check (the index cites combat/README n4 and n5 and skills/README n2 for their [I] clauses; anim/README n2 is listed as a weaker duplicate in the coverage table and would then become a citation).
