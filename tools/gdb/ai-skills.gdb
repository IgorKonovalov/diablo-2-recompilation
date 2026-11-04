# The monster AI logger (tools/gdb/ai.py, plan 0052 Phase 2) and the skills and missiles logger (tools/gdb/skills.py,
# plan 0045 Phase 2) in one game, for the H1 oracle replacement: the AI's decisions (AID, AIR, AIB lines) beside the
# skill starts, hits and seeds of the same monsters, so that a gap between two skill events of one monster can be
# walked through the decisions between them. pilot.py is loaded once; neither logger writes game memory or registers,
# and tools/gdb/ai-p1b2.py (the corpse writer) is not loaded. Caps: env AI_CAP_ROW, AI_CAP_SESSION, AI_CAP_AIN,
# AI_RADIUS (tools/gdb/ai.py) and SKILLS_CAP_<KIND>, SKILLS_WIN (tools/gdb/skills.py). Run through tools/d2run.py
# (tools/ai_sessions.py --gdb, tools/skills_sessions.py --gdb) and check with tools/ai.py and tools/skills.py.
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/pilot.py
source tools/gdb/ai.py
source tools/gdb/skills.py
continue
