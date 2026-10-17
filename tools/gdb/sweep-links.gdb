# Plan 0038 batch H5a logger (run:2026-10-17-sweep-links): drlg-maze.gdb (drlg-gen.py generator tags, drlg-maze.py
# maze/link/warp tags with LNK0/LNKL/LK27/LNK1/LNKS, pilot.py with its RL renamed PRL) plus drlg-links.py (new: LNKP
# after each link pick, LNKC after each check, LNKW the Act1B widened test, LNKT/LNKU LevelSeamsByTouch's RectTouch).
# Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 82 --gdb tools/gdb/sweep-links.gdb --steps tools/gdb/enter-normal.steps \
#       --after 3600 --log workspace/logs/sweep-links/sweep-links-s1-82-normal.log
# Check with
#   python3 -I tools/sweep_h5a.py logs
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
source tools/gdb/drlg-links.py
source tools/gdb/pilot.py
continue
