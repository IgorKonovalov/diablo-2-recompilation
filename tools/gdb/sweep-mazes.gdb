# Plan 0038 batch H5e logger (run:2026-10-16-sweep-mazes): no new breakpoint, the existing DRLG files together.
# drlg-gen.py (generator tags), drlg-preset.py (preset-unit tags: PLD/PLDX for the Blood Moor centre monster and the
# client river objects, RSK), drlg-maze.py (maze window MZA/MZD/MZF, links, warp points, WPR, OBJP), drlg-outdoor.py
# (ODD/ODG outdoor windows) and pilot.py (its RL renamed PRL so that drlg-gen.py's RL stays the only one). It is
# drlg-outdoor.gdb plus drlg-preset.py, or drlg-preset-play.gdb plus drlg-outdoor.py. Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 9 --gdb tools/gdb/sweep-mazes.gdb --steps tools/gdb/enter-normal.steps \
#       --after 3600 --log workspace/logs/sweep-mazes-s1-9-normal.log
# Check with
#   python3 -I tools/drlg.py gen workspace/logs/sweep-mazes-s*.log
#   python3 -I tools/sweep_h5e.py all
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
source tools/gdb/drlg-preset.py
source tools/gdb/drlg-maze.py
source tools/gdb/drlg-outdoor.py
source tools/gdb/pilot.py
continue
