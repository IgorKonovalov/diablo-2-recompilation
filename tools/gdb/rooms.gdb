# Room-lifecycle logger (plan 0040 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and
# tools/gdb/rooms.py (activation, release, the inactive records, the restore and the wanderer gate of
# docs/findings/drlg/0009-room-lifecycle.md). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 4001 --gdb tools/gdb/rooms.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1500 --install r40 ObjNova.d2s --log workspace/logs/rooms/<run>-<session>.log
# then drive the character with tools/rooms_sessions.py. Check with
#   python3 -I tools/rooms.py check workspace/logs/rooms/<run>-*.log
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
source tools/gdb/rooms.py
continue
