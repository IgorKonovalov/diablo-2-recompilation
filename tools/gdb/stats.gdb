# Stats and states logger (plan 0041 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and
# tools/gdb/stats.py (the stat-list, requirement, set, passive and tick events of docs/findings/stats/0001-aggregate.md
# and 0002-states.md). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 2 --seed 4101 --gdb tools/gdb/stats.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install s41 StatsBar.d2s --log workspace/logs/stats/<run>-<session>.log
# then drive the character with tools/stats_sessions.py. Check with
#   python3 -I tools/stats.py check workspace/logs/stats/<run>-*.log
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
source tools/gdb/stats.py
continue
