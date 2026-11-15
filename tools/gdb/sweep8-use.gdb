# Plan 0065 cases H2, H3 and B8 logger: tools/gdb/pilot.py (the lines tools/d2pilot.py steers by),
# tools/gdb/inventory.py (plan 0060's item-use and inventory lines: UP0..UP1, USS, PKT/PKR, GDI/GDO, IPG; its ready
# line INVRDY) and tools/gdb/use-sweep8.py (URM, UBL, UFL, UFM; T26.., T61.., IU0; CCR, CCN, CMB, BOV0/BOV1; ready line
# "USE8 logger armed"). Read-only: tools/sweep8_sessions.py never writes inventory.py's arm file. Run through
#   python3 -I tools/sweep8_sessions.py run --slot N --tag TAG --run RUN h2 h3 b8room b8full
# Check with
#   python3 -I tools/inventory_check.py <log>            (the potion uses and draws, plan 0060's model)
#   python3 -I tools/sweep8_check.py h2|h3|b8 <log>
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
source tools/gdb/inventory.py
source tools/gdb/use-sweep8.py
continue
