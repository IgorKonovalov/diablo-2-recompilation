# Plan 0038 batch H6g (run:2026-10-27-sweep-player), the Ancients session: tools/gdb/h6g.gdb plus tools/gdb/vendors.py
# (TICK, NPC, OBJP, OBJS: the lines tools/quest_sessions.py act and tools/d2pilot.py objop steer by). Checked as
# h6g.gdb by tools/sweep_h6g.py check.
#   python3 -I tools/player.py check <log> [<log> ...]
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
source tools/gdb/uniques.py
source tools/gdb/props.py
source tools/gdb/d2s-io.py
source tools/gdb/player.py
source tools/gdb/vendors.py
source tools/gdb/h6g.py
continue
