# Plan 0065 case P12 logger (backlog 2026-11-04 0054-p12; skills/missiles D3): tools/gdb/pilot.py (PLR, CB, RRESEED:
# the lines tools/d2pilot.py steers by, and the room grids the cell pick reads) and tools/gdb/p12.py (MMC, MMR: a Nova
# missile's own-cell word in sub_005AE1F0_MissileMoveCollide and the function's exit). Ready line "P12 logger armed".
# Run through tools/sweep8_sessions.py (session p12), e.g.
#   python3 -I tools/sweep8_sessions.py run --slot N --tag TAG --run RUN p12
# Check with
#   python3 -I tools/sweep8_check.py p12 <log>
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
source tools/gdb/p12.py
continue
