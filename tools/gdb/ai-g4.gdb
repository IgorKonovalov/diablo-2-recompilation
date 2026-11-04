# Monster AI decision logger (plan 0052 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and
# tools/gdb/ai.py (the AI event of docs/findings/ai/0001-0010: one line per decision, its first boundary calls, the
# command, the path plan and the skill start). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 2 --seed 5201 --gdb tools/gdb/ai.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install p52a CombatSor.d2s --log workspace/logs/ai/<run>-<session>.log
# then drive the character with tools/ai_sessions.py. Check with
#   python3 -I tools/ai.py check workspace/logs/ai/<run>-*.log
# Caps and the player radius (env AI_CAP_ROW, AI_CAP_SESSION, AI_CAP_AIN, AI_RADIUS): see tools/gdb/ai.py.
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
source tools/gdb/ai-g4.py
source tools/gdb/ai-p1b2.py
continue
