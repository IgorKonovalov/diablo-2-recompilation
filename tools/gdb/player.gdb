# New character, starting items, experience and level-up logger (plan 0034 Phase 2, run:2026-10-16-player):
# tools/gdb/pilot.py (the lines tools/d2pilot.py steers by), tools/gdb/uniques.py and tools/gdb/props.py (each starting
# item's ItemCreateByQuality, ItemInitStats, ItemApplyProps, ethereal, sockets, final lists), tools/gdb/d2s-io.py (the
# save written at Save and Exit, and the save read) and tools/gdb/player.py (NewCharFromStub step by step, the
# starting items' creation records and placement, kill experience, PLAYER_AddExperience, PLAYER_LevelUp with the RNG
# calls inside it). Run through tools/d2run.py (tools/player_sessions.py newchar writes the steps), e.g.
#   python3 -I tools/d2run.py --slot 3 --seed 34100 --gdb tools/gdb/player.gdb --steps <newchar.steps> \
#       --after 3 --log workspace/scratch-h34p2/newchar/logs/newchar-34100.log
# Check with
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
continue
