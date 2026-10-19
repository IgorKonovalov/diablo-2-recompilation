# Item economy logger with the hireling logger (plan 0043 Phase 2, question 6): tools/gdb/economy.gdb's files plus
# tools/gdb/mon-pool.py and tools/gdb/hirelings.py (the hire lists and every HIRELING_RollEntry, whose price
# tools/hirelings.py check reproduces), so one log carries the hire price and the gold paid (PG0/PG1). Check with
#   python3 -I tools/hirelings.py check workspace/merged/data/global/excel <log>
#   python3 -I tools/economy.py check workspace/merged/data/global/excel <log>
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
set can-use-hw-watchpoints 1
handle all nostop noprint pass
source tools/gdb/pilot.py
source tools/gdb/vendors.py
source tools/gdb/mon-pool.py
source tools/gdb/hirelings.py
source tools/gdb/economy.py
continue
