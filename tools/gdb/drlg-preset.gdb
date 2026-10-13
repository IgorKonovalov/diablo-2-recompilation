# Preset-unit logger for the pinned game.exe (plan 0016 Phase 2): the generator tags of drlg-gen.py plus the
# preset-unit tags of drlg-preset.py. Run through tools/d2run.py:
#   python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/drlg-preset.gdb --steps tools/gdb/enter-sp.steps \
#       --after 15 --game-args "-act 2" --log workspace/logs/preset-12345-act2.log
# Check with
#   python3 -I tools/drlg.py gen workspace/logs/preset-*.log
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/drlg-gen.py
source tools/gdb/drlg-preset.py
continue
