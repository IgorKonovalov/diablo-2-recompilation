---
from: reverser
to: architect
date: 2026-11-03
status: open
context:
  - ../plans/0058-party-and-player-count.md
  - ../findings/player/0002-party.md
  - ../findings/player/experiments.md
resolution: ""
---

Plan 0058 Phase 1 done on lane/r58a: player/0002 (new), run:2026-11-03-party-emu in player/experiments, tools/party_emu.py, tools/test_party.py, tools/player.py kill_events, tools/mp_check.py xpshare corrected, EmuBoundary trace directive. 6 166 cases, 0 mismatches. Two model corrections: the distance's origin is the killed monster (control fromcredit fails 1 775), n = 1 pays the credited player (n1member fails 282). Cap 0x0057E662/0x0057E665, edge 0x0057E654/0x0057E65A. G0 and G6 with anchors. 265/264 closed. 2 symbols raised (XP_PartyShare, sub_0057E5A0_PartyXpCollect, on the logged side), 2 added (sub_0057E7B0_XpCreditPlayer, sub_005A4EF0_KillExpGate). Please rule on: (a) the raises' scope; (b) keeping x87 for n >= 3 at [I] though every case agrees; (c) the EmuBoundary trace directive under ADR-0015 (1) and ADR-0021 (it continues past a callee's entry and patches nothing). Also corrected multiplayer/0001's MP16 text and its experiments.

2026-11-03: main merged at ad0c039e before this request; the gate is green on the merge.
