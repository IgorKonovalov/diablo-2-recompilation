# Quest drops, quest rewards and special drops logger (plan 0032 Phase 2): tools/gdb/pilot.py (the lines
# tools/d2pilot.py steers by), tools/gdb/uniques.py and tools/gdb/affixes.py (each created item's creation lines),
# tools/gdb/vendors.py (TICK and NPC for d2pilot.py npc; the store lines too), tools/gdb/mon-pool.py (MPS, MPR, MLV:
# the monster level at creation, for the boss case), tools/gdb/quests.py (the quest seed, quest-bit writes, B6, the
# scripted drops and the NPC item services) and the drop lines of tools/gdb/tc-drops.gdb (sourced last: it ends with
# `continue`). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 3 --seed 3301 --gdb tools/gdb/quests.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install h32p2 QuestFresh.d2s --log workspace/logs/quests-s3-3301-normal.log
# Check with
#   python3 -I tools/questdrops.py check workspace/logs/quests-*.log
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
source tools/gdb/mon-pool.py
source tools/gdb/quests.py
source tools/gdb/tc-drops.gdb
