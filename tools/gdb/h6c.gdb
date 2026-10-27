# Plan 0038 batch H6c (vendors) logger: tools/gdb/vendors.gdb (pilot.py, uniques.py, affixes.py, vendors.py: the
# plan 0031 lines tools/vendors.py checks) plus tools/gdb/h6c.py (the town-leave caller, the level-up note, the
# interaction set and clear, the hireling build's caller, each stock item's tab and grid cell, the inventories at the
# opens and builds, the creation record's +0x18/+0x28, the purchases and sales). Run by tools/h6c_sessions.py; check
# with tools/vendors.py check and tools/sweep_h6c.py logs.
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
source tools/gdb/affixes.py
source tools/gdb/vendors.py
source tools/gdb/h6c.py
continue
