# Maze, act-link and warp-point logger for the pinned game.exe (plan 0022 Phase 2): the generator tags of
# drlg-gen.py (plan 0008), the maze/link/warp tags of drlg-maze.py, and the pilot lines of pilot.py (its RL renamed
# PRL so that drlg-gen.py's RL stays the only one). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 4 --seed 22 --gdb tools/gdb/drlg-maze.gdb --steps tools/gdb/enter-normal.steps \
#       --after 3600 --log workspace/logs/maze-s1-22-normal.log
# Check with
#   python3 -I tools/drlg.py gen workspace/logs/maze-*.log
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
python import os; os.environ["PILOT_RL_TAG"] = "PRL"
source tools/gdb/drlg-gen.py
source tools/gdb/drlg-maze.py
source tools/gdb/pilot.py
continue
