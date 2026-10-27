# Animation and frame timing logger (plan 0050 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and
# tools/gdb/anim.py (the mode, schedule, rate, step, get-hit and object events of docs/findings/anim/0001-0003). Run
# through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 2 --seed 5001 --gdb tools/gdb/anim.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install p50e AnimSor0.d2s --log workspace/logs/anim/<run>-<session>.log
# then drive the character with tools/anim_sessions.py. Check with
#   python3 -I tools/anim.py check workspace/logs/anim/<run>-*.log
# Per-kind caps per session (env ANIM_CAP_<KIND>), ANIM_WIN_FRAMES, ANIM_WINS: see tools/gdb/anim.py.
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
source tools/gdb/anim.py
continue
