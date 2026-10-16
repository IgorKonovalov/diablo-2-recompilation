# Hireling logger (plan 0033 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by), tools/gdb/vendors.py
# (the NPC seed, the store and hire build boundaries, the NPC positions and the TICK heartbeat of d2pilot.py npc),
# tools/gdb/mon-pool.py (the MonStatsInit level, for tools/monpool.py check) and tools/gdb/hirelings.py (the hire
# table, every HIRELING_RollEntry, the hire, MERC_Init, MERC_SetLevel, the save's mercenary header, the magic find of
# a kill). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 3301 --gdb tools/gdb/hirelings.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install h33p2 VendorNova.d2s --log workspace/logs/hire-s1-3301-normal.log
# then drive the NPCs with tools/d2pilot.py npc / hire. Check with
#   python3 -I tools/hirelings.py check <excel-dir> workspace/logs/hire-*.log
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
continue
