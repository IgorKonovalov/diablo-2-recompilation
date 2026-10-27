# Plan 0038 batch H1b: tools/gdb/d2s-h1b.gdb plus the hirelings logger of run:2026-10-16-hirelings
# (tools/gdb/vendors.py, mon-pool.py, hirelings.py, as tools/gdb/hirelings.gdb sources them), for the sessions that
# hire a mercenary (tools/d2pilot.py npc ... hire) or watch one die (MFK) before Save and Exit.
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
source tools/gdb/d2s-io.py
source tools/gdb/d2s-h1b.py
continue
