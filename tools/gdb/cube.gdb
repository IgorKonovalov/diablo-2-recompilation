# Horadric Cube transmute logger (plan 0030 Phase 2): tools/gdb/uniques.py (ItemCreateByQuality, the builders, the
# fallbacks), tools/gdb/props.py (ItemInitStats, ItemApplyProps with its slots, rolls and writes, ethereal, sockets,
# the final stat lists) and tools/gdb/cube.py (CUBE_Transmute: the cube's contents, the row scan, the outputs, the
# special outputs, ItemCopy, CubeModApply with its slots, the placement). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 3001 --gdb tools/gdb/cube.gdb --steps tools/gdb/cube-load-normal.steps \
#       --after 900 --install h30p2 workspace/scratch-h30p2/CubeRunes.d2s --log workspace/logs/cube-runes-s1-3001.log
# then drive the transmutes with tools/d2pilot.py cube. Check with
#   python3 -I tools/cube.py check workspace/logs/cube-*.log
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/uniques.py
source tools/gdb/props.py
source tools/gdb/cube.py
continue
