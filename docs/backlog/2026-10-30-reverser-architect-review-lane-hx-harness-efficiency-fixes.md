---
from: reverser
to: architect
date: 2026-10-30
status: open
context: []
resolution: ""
---

Review lane/hx (owner-approved 2026-10-30 harness efficiency fixes; tooling and skill text only, no claims, no game session). Commits 0337e9f3 (tools) and aa597c3f (skills).

1. Readiness wait. tools/h1a_sessions.py and tools/h1c_sessions.py waited for three TBL lines, which only the runner's first load writes (their steps file stays at the menu): the first case mark of the kept H1a log workspace/logs/h1a/h1a-s2-27201-main.marks.jsonl sits at line 17, before the first TBL (line 18), so every session ran out the 120 s timeout. tools/gdb/d2s-h1a.gdb and d2s-h1c.gdb now echo 'RDY {"logger":...}' after every source and before continue; a shared wait_ready (in h1a_sessions, imported by h1c) returns on RDY, on the driver's exit (then the runner stops), or at the timeout; the 8 s settle after it is kept (steps start up to --attach-wait 5 s after the gdb exec). Static check: tools/test_h1_ready.py, 9 tests green (a kept-log-shaped prefix, the old predicate failing on it, the .gdb files' RDY-before-continue). Not yet run live: the next H1a/H1c session is the smoke session for this logger revision (d2s-h1a.gdb, d2s-h1c.gdb hashes recorded in docs/findings/save/experiments.md are the old revision).
   Sweep of every other tools/*_sessions.py: no other runner keys on a case-only line. h1b, h2a, h2b, h2c, h4a, h5b, h5d, h6b, h6c, h6d, h6e1, h6e2, h6g, player, quest, combat, rooms and economy wait for PLR, which their enter-*.steps produce before the first case; h6a waits for 'CUBE logger armed'; h3b waits for PLR or the game's exit. Runners in use by running lanes, read but left untouched: tools/anim_sessions.py (lane/p50g; :772 PLR, then :789 the logged server frame "fr" past 75) and tools/skills_sessions.py (lane/p46h; :202 and :220, the same two waits), as is tools/stats_sessions.py (:445, :465). Both lines appear in game before the first step, so none needs the RDY fix; they relaunch after 150 s without PLR.
   None of these runners returns early when the driver dies during the wait; only h1a/h1c do now. Optional follow-up for the other runners.
2. .claude/skills/reverser/references/harness-play.md: new sections 'Before the batch' (one smoke session per logger revision; pilot targets pre-checked in a dev session; survivable recipes, no corpse runs; dev logs apart from kept logs) and 'Running a batch unattended' (the ready-wait rule; the whole batch launched in the background in one command; one wait via Monitor until-loop or tail --pid; draft while waiting; the checker once at the end; long outputs in files, summaries read back).
3. .claude/skills/reverser/references/review-fixes.md: item 16 (a runner's ready wait keys on a line that appears before the first case).
