# Quest NPC logger (plan 0038 batch H6e1, quest-npc): the lines of tools/gdb/quest-state.gdb (pilot.py, vendors.py,
# quests.py, questev.py: the pilot's lines, the town NPCs and objects, the quest seed and bit writes, the item
# services, the NPC dispatch events and Anya's reward draw), the item creation lines of uniques.py and affixes.py,
# and tools/gdb/quest-npc.py (QUESTS_GiveItem, the three service tests, the cursor item consumed, the shared tail).
# Run through tools/d2run.py by tools/h6e1_sessions.py; checked by tools/sweep_h6e1.py.
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
source tools/gdb/quests.py
source tools/gdb/questev.py
source tools/gdb/quest-npc.py
continue
