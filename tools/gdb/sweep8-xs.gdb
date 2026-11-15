# Plan 0065 exp-state kills logger (backlog 2026-11-04 a68-review exp-state-kill-in-play; player/0002 § 4):
# tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and tools/gdb/player.py revision 2 (XK0 with the killer's
# and the victim's exp-mask states "kxs"/"vxs", XC0..XCX, XA0/XAX, and the XpCreditPlayer steps XSO..XSR). Ready line
# "PLAYER logger armed". Run through
#   python3 -I tools/sweep8_sessions.py run --slot N --tag TAG --run RUN xs
# Check with
#   python3 -I tools/sweep8_check.py xs <log>
#   python3 -I tools/player.py check <log>
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
source tools/gdb/player.py
continue
