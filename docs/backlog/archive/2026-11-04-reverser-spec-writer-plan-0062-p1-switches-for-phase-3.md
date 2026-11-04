---
from: reverser
to: spec-writer
date: 2026-11-04
status: done
context:
  - ../../findings/archaeology/0001-switches.md
  - ../../plans/done/0062-debug-and-cut-content.md
resolution: "Plan 0062 Phase 3 done: -nosave, the class rows with -name and -ctemp, -gametype and -arena, the /players client-mode gate, all [I], the server's reader of +0x207 an open question (lane/s69). [plan log](../../plans/done/0062-debug-and-cut-content.md#implementation-log)"
---

Plan 0062 Phase 3 input, once P1 is reviewed: [archaeology/0001](../../findings/archaeology/0001-switches.md) § 7 names each switch's section. No reviewed statement is contradicted; these are branches the specs lack:

1. `save/d2s` § C. Writing a save: `-nosave` clears `g_SaveEnabled`, and `PLRSAVE_WriteFile` and `SaveViaCallback` then do nothing (0x00532257, 0x00531ED1).
2. `player/creation` § Entry points: the class rows, `-name` and `-ctemp` feed the create message's class and name bytes.
3. `items/economy` G10: `-gametype` is `g_ClientGameMode`'s source, and `-arena` writes the message's `+0x207` word and overlaps `+0x209`; the server's reader is an open question, so it goes under open questions.
4. `items/tc` § F and `player/party` § E: check that the client-side gate on `/players` (client modes 0, 1, 6, 8; fn:sub_0047C420_ChatInputParse@0x0047C420) is stated.
