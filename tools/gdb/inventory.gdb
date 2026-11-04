# Item use and inventory harness logger (plan 0060 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by)
# and tools/gdb/inventory.py (items/0012..0014's cases). Run through tools/d2run.py, driven by tools/inventory_sessions.py,
# checked by tools/inventory_check.py.
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
source tools/gdb/inventory.py
continue
