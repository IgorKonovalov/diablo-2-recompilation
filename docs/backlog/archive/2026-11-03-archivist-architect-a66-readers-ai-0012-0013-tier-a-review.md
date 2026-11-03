---
from: archivist
to: architect
date: 2026-11-03
status: done
context:
  - ../../plans/0052-monster-ai.md
resolution: "Accept with fixes (16), Tier A review in [plan 0052](../../plans/0052-monster-ai.md); finding notes routed to the [reverser](2026-11-03-architect-reverser-a66-review-finding-notes-ai-0012-0013.md)."
---

Tier A review (ADR-0027) of lane/a66: the readers named by ai/0012 and ai/0013 linked into MonStats (two new blocks in AI columns), Skills (attackrank, aurastate, auratargetstate), SuperUniques (record 6, state 13) and MonAI (state-row setters). Check every bullet against its finding paragraph (tag, scope, sign-test direction, composed rules). Review points are listed in the plan 0052 log entry of lane/a66: row 140 and Skill5, row 128 Sk1mode, the aidist +0x50 offset in ai/0013 (reverser to confirm), the two [C] sign tests (bact u16 6, h5b70 u16 7), and the unnamed record in the interact callback. Not blocking.
