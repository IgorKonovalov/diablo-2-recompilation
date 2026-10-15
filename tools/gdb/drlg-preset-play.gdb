# Preset-unit logger for scripted play (plan 0020 Phase 4): the generator tags of drlg-gen.py, the preset-unit tags
# of drlg-preset.py (with its RSK row-skip counter), drlg-maze.py (its OBJP lines place the waypoints for
# d2pilot.py wpchain) and the pilot lines of pilot.py (its RL renamed PRL so that
# drlg-gen.py's RL stays the only one). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 4001 --gdb tools/gdb/drlg-preset-play.gdb \
#       --steps tools/gdb/enter-normal.steps --after 3600 --log workspace/logs/acts35/a35-s1-4001-normal.log
# Check with
#   python3 -I tools/drlg.py gen workspace/logs/acts35/a35-*.log
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
source tools/gdb/pilot.py
continue
