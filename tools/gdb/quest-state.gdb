# Quests and travel logger (plan 0042 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by),
# tools/gdb/vendors.py (NPC, OBJP, OBJS, TICK: the town NPCs and objects the driver walks to), tools/gdb/quests.py
# (plan 0032: QI0/QI1 the quest seed and game record, QS/QC every quest-bit write, the item services) and
# tools/gdb/questev.py (the dispatch, the join, the travel events with their seeds, the gates, the free-cell
# searches). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 4201 --gdb tools/gdb/quest-state.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install p42h QuestBookLost.d2s --log workspace/logs/quests/<run>-<session>.log
# then drive the character with tools/quest_sessions.py. Check with
#   python3 -I tools/quests.py check workspace/logs/quests/<run>-*.log
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
source tools/gdb/quests.py
source tools/gdb/questev.py
continue
