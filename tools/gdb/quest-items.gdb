# Quest items, quest chests and quest objects logger (plan 0038 batch H6e2, quest-items): the lines of
# tools/gdb/quests.gdb (pilot.py, uniques.py, affixes.py, vendors.py, mon-pool.py, quests.py) plus
# tools/gdb/quest-items.py (object event 7, QUESTS_GiveItem, the chest gold, PlayerFindItemByCode, ItemQuestGate,
# the orifice), and the drop lines of tools/gdb/tc-drops.gdb (sourced last: it ends with `continue`). Run through
# tools/d2run.py by tools/h6e2_sessions.py; checked by tools/sweep_h6e2.py.
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
source tools/gdb/quest-items.py
source tools/gdb/tc-drops.gdb
