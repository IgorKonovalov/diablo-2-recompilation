# Plan 0038 batch H6f logger (run:2026-10-27-sweep-hirelings): tools/gdb/hirelings.gdb's four loggers (pilot.py,
# vendors.py, mon-pool.py, hirelings.py; unchanged) plus tools/gdb/h6f.py (the hire gates and refusals, PayGold, the
# free mercenary, MERC_Create's table write, the saved mercenary's name clamp and dead branch, PETS_OnDeath,
# MERC_Resurrect, the kill's experience award, MERC_CapExpGain, MERC_AddExp, the client's name string). Run through
# tools/h6f_sessions.py; check with python3 -I tools/sweep_h6f.py check <excel-dir> LOG...
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
source tools/gdb/vendors.py
source tools/gdb/mon-pool.py
source tools/gdb/hirelings.py
source tools/gdb/h6f.py
continue
