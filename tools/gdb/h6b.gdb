# Socket logger of plan 0038 batch H6b (sockets): tools/gdb/pilot.py and tools/gdb/vendors.py (the pilot's lines, the
# town NPCs, TICK), tools/gdb/quests.py (the NPC service lines the pilot waits for: PZ), tools/gdb/sockets.py (the
# plan 0029 Phase 2 socket and runeword lines, unchanged) and tools/gdb/h6b.py (child x/y, the cursor clear, the
# stat-list link branch, the replenish timers, the reader's runeword store, ItemCopy, the client's runeword field).
# Run through tools/d2run.py by tools/h6b_sessions.py; checked by tools/sweep_h6b.py and tools/sockets.py check.
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
source tools/gdb/sockets.py
source tools/gdb/h6b.py
continue
