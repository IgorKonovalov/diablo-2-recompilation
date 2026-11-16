---
from: reverser
to: architect
date: 2026-11-16
status: open
context:
  - ../plans/0069-monster-ai-bestiary-tour.md
  - ../findings/ai/experiments.md
resolution: ""
---

Tier B check of the AI logger rev 8 (lane/n69h): see the plan's log entry 2026-11-16 Logger rev 8 and owner-session plan. Asks: (1) rule that the R118 contradiction candidate (backlog 2026-11-16-reverser-spec-writer+architect-plan-0069-p3b-r118-step-1-draw-contradiction) is the rev 7 word bug (w_eax read the dword at the address in EAX), so the row 347/348 stay [I] until a kept rev 8 run, not a spec change; (2) check the rev 8 words and sites (R118.cmp 0x005E1E45, R119.cmp 0x005E216D, R120.hasskill1..3 at 0x005E281B/0x005E29B4/0x005E2A55, owner.mode 0x005F8FD3, R48.act 0x005F6F21, R48.quest21 0x005F6F40) against the image; (3) tests (test_ai 25 OK, test_ai_model_check 100 OK, test_ai_resume/test_ai_tour fixed stale asserts), regress byte-identical (32 entries, 38 logs) and the check over the 84 logs byte-identical to n69g; (4) the owner-session plan workspace/logs/n69h/owner-sessions.md (manifest workspace/logs/n69h/manifest.sha256, passes from that directory).
