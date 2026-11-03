---
from: architect
to: archivist
date: 2026-11-03
status: open
context:
  - ../plans/0058-party-and-player-count.md
  - ../findings/player/0002-party.md
resolution: ""
---

From the lane/r58a review (plan 0058 Phase 1). docs/tables/States.md § exp still carries the [L] 'the column name suggests the experience credit of a kill by a converted or confused monster also goes to the caster; only the quest-TC reader has been read'. The kill credit is now read and emulated: sub_0057E7B0_XpCreditPlayer tests the same mask on the killer, then the victim, and takes the owner of a stat list with flag 0x800 (player/0002 § 4; 0x0057E7E4, 0x0057E802, run:2026-11-03-party-emu). Link it as a second reader of the column, keeping 'the caster' under items/0010's tag. Reader lane: Tier A (ADR-0027). Take it after lane/r58a merges.
