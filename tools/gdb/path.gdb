# Path plan logger (plan 0054 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and tools/gdb/path.py (one
# PLN / PLG / PLC / PLU / PLX group per PathPlan call of a server unit, break lines on the planners of types 3, 11, 12 and the type-16
# functions with a live control, and the +0x3C store sites). Run through tools/d2run.py, driven by tools/path_sessions.py. Check with
#   python3 -I tools/path.py check workspace/logs/path/<run>-*.log
# Caps and the player radius (env PATH_CAP_TYPE, PATH_CAP_REF, PATH_CAP_SESSION, PATH_CAP_UNITS, PATH_RADIUS): see tools/gdb/path.py.
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
source tools/gdb/path.py
continue
