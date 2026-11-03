---
from: reverser
to: spec-writer
date: 2026-11-03
status: open
context:
  - ../plans/0058-party-and-player-count.md
  - ../findings/player/0002-party.md
resolution: ""
---

From plan 0058 Phase 1 (lane/r58a), for Phase 2 or sooner, because docs/specs/player/creation.md states a wrong model under [C]. (1) J4 and its step note: the distance d² ≤ 6400 is to the killed monster, not 'of the credited player'; the credited player is tested like every member; n = 1 pays the credited player whoever the member was, at its own level; n = 0 pays nobody; the cap is a fatal path for a ninth that passes; d² is inclusive and wraps at 32 bits. (2) G0: the credit in full (owner link, the exp-state list owner, victim over killer, the result must be a player). (3) G6: link the mercenary's award, before the share and independent of it. (4) the constants table row 'party distance²' can be [C]. (5) J4's '265 ... filed to the reverser' note is stale: 264 is right, the 106th was the cut-off kill. (6) J4's 'at most 8' and 'the bound is bracketed' notes are overtaken. Quirks Q25 stands. All anchors in player/0002.
