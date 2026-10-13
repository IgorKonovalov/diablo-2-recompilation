# Plan 0016 Phase 2 required case (poppad): the preset-unit logger (drlg-preset.gdb) plus tools/gdb/drlg-preset-wp.py,
# Harrogath (Def 863) and Pandemonium Fortress (Def 797) PopPad watches. Run through tools/d2run.py as drlg-preset.gdb.
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
set can-use-hw-watchpoints 1
handle all nostop noprint pass
python WP_MODE = "poppad"; WP_DEFS = [863, 797]
source tools/gdb/drlg-gen.py
source tools/gdb/drlg-preset.py
source tools/gdb/drlg-preset-wp.py
continue
