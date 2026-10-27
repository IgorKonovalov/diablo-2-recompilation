# Plan 0038 batch H6g (run:2026-10-27-sweep-player): tools/gdb/player.gdb's files (pilot.py, uniques.py, props.py,
# d2s-io.py, player.py; unchanged) plus tools/gdb/h6g.py (client +0x3D4 after sub_00537970, the monster's experience
# at the kill, PLAYER_SpendStatPoint, the skill-point path and SKILLS_AddSkill, sub_0063C600_BeltFreeSlot, the death
# loss, the corpse and its pickup, the capped grant). Played by tools/h6g_sessions.py; checked by
#   python3 -I tools/sweep_h6g.py check <excel-dir> <log> [<log> ...]
#   python3 -I tools/player.py check <log> [<log> ...]
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
source tools/gdb/props.py
source tools/gdb/d2s-io.py
source tools/gdb/player.py
source tools/gdb/h6g.py
continue
