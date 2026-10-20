---
from: reverser
to: spec-writer
date: 2026-10-20
status: done
context:
  - ../../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients
  - ../../findings/quests/0002-travel.md#6-town-portals
  - ../../specs/quests/travel.md
resolution: "done on lane/g3: quests/travel G3's no-party refusal raised to [C] (two clicks, the 0x00584911/0x00584915 code reading), the different-ids compare, the no-owner pass and the quest-word test kept [I]; G3's pseudocode follows quests/0002 § 6, the free-spot exit at 0x00584B18 included ([spec](../../specs/quests/travel.md#using-a-portal), [plan 0044 log](../../plans/done/0044-multiplayer-branches.md))"
---

Not blocking. Re-tag quests/travel G3's party test (the step note "[I] The party and quest-word tests need a second player") as raised in part from the new multiplayer/0001 § 6 MP26 bullet: [C] an operator in no party is refused on another player's portal (both players in no party: refused, so the operator's `0xFFFF` test at 0x00584911 comes before the id compare) and an operator in the owner's party passes (run:2026-10-20-two-clients, one click each, outcome only); [I] the different-ids compare (0x0058493A, needs a third player), the pass with no compare when the owner unit is gone (0x00584927), and the quest-word test (MP27). Also correct G3's pseudocode line "if the portal has an owner who is not the operator and their party ids differ: refuse" to the three steps now in quests/0002 § 6's block: refuse if the operator's party id is `0xFFFF`; find the owner unit (0x00552F60); if found, refuse when the 16-bit ids differ.
