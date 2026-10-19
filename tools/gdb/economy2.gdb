# Item economy logger, Phase 2b (plan 0043): economy.gdb plus tools/gdb/quests.py (the service lines IMBX, LZY, PZ
# that tools/d2pilot.py npc imbue|socket|personalize waits for, QDI/QDX around DropItemAtUnit, OOP for objop).
# Phase 2 logger (plan 0043 Phase 2): tools/gdb/pilot.py and tools/gdb/vendors.py (the lines tools/d2pilot.py
# steers by: PLR, RL, CB, NPC, TICK, OBJS) and tools/gdb/economy.py (prices, repair, gold, wear, ticks, the store
# record watchpoint). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 4301 --gdb tools/gdb/economy.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install p43h EconNova.d2s --log workspace/logs/economy-s1-4301-normal.log
# Check with
#   python3 -I tools/economy.py check workspace/merged/data/global/excel workspace/logs/economy-*.log
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
source tools/gdb/quests.py
source tools/gdb/economy.py
continue
