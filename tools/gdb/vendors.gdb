# Vendor stock and gamble logger (plan 0031 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by),
# tools/gdb/uniques.py and tools/gdb/affixes.py (each created item's creation lines, for the item_chain affix model)
# and tools/gdb/vendors.py (the store seed, the stock and gamble builds, the triggers, the NPC positions). Run through
# tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 3101 --gdb tools/gdb/vendors.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install h31p2 VendorNova.d2s --log workspace/logs/vendors-s1-3101-normal.log
# then drive the NPCs with tools/d2pilot.py npc. Check with
#   python3 -I tools/vendors.py check workspace/logs/vendors-*.log
# tools/gdb/vendors-props.gdb is the same with tools/gdb/props.py in place of affixes.py (items_chain.py props).
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
continue
