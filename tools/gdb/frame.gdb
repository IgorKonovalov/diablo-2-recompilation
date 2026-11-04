# Frame-window logger (plan 0055 Phase 2b): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and
# tools/gdb/frame.py (FT0/FT1, FP, ACL, UE0/UE1, MSG0/MSG1, SYS, RU0/RU1, TM, TQ0/TQ1, RC, RR, QE/QF, SV0/SV1 and the
# WIN/WEND window lines; docs/findings/frame/0001 § 7, 0002 § 8, 0003 § 9). It never writes game memory or registers.
# Run through tools/frame_sessions.py (it sets FRAME_CTL / FRAME_WINDOWS), or by hand:
#   FRAME_WINDOWS=r300:250:town python3 -I tools/d2run.py --slot N --seed S --gdb tools/gdb/frame.gdb \
#       --steps tools/gdb/enter-normal.steps --after 1800 --log workspace/logs/frame/<run>-<session>.log
# Check with:  python3 -I tools/frame.py window workspace/logs/frame/<run>-*.log
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
source tools/gdb/frame.py
continue
