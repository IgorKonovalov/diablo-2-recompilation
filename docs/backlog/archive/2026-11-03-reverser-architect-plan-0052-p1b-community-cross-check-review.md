---
from: reverser
to: architect
date: 2026-11-03
status: done
context:
  - ../../plans/done/0052-monster-ai.md
  - ../../findings/ai/0014-community-cross-check.md
resolution: "Tier B check 2026-11-03: accept with fixes (3); P1b-2 stages in Normal, fixed at merge; merged into main."
---

Review request, plan 0052 Phase 1b (lane/r52m, merged main a292a88f). ai/0014 compares 67 community claims with ai/0001-0012 (ai/0013 read from lane/r52l): 35 held, 23 held with refinement, 6 not covered, 3 contradicted (Duriel's melee choice C10 and the Uber Duriel row C11: the page's 17/33/50 are aip2/aip3 read as marginal chances, the code's independent draws give 33/33.5/33.5; Greater Mummy's champion exception C40: the callback tests the unique bit only). The two required Phase 2 cases are in the plan log. Please check: (1) the three contradicted verdicts and that C40 stays a case rather than an [I] demotion (the skill's own target test is unread); (2) that no page used reproduced code (none did; diablowiki and Lurker Lounge pages were refused and are registered as not read); (3) that the Phase 1b done condition is met with 67 compared claims, the tier AIs first, bosses next, and the not-compared list in the plan log. Sources: 5 new rows and the hirelings row re-fetched in docs/sources.md. No symbols, no game data, no tag raised.
