# Two-client kill logger (plan 0044 Phase 2, run:2026-10-20-two-clients): attach to the HOST's game (it runs the
# server game, ADR-0008). tools/gdb/pilot.py (the lines tools/d2pilot.py steers by), tools/gdb/two-players.py (PLRS
# for the joiner's driver, PLRK at every XP_OnMonsterKill), tools/gdb/player.py (XK0, XC0..XCX, XA0/XAX, LU0..LUX:
# kill experience, the party share), tools/gdb/tc-party.py (PLR, PTY, KILL at every monster drop) and the drop lines
# of tools/gdb/tc-drops.gdb (sourced last: it ends with `continue`).
#   python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-kills.gdb --steps tools/gdb/two-host-normal.steps \
#       --after 3000 --install TAG HOST.d2s --log workspace/logs/<run>-host.log
# Check with
#   python3 -I tools/tc.py replay <log>                 (party and player counts, every drop)
#   python3 -I tools/player.py check <log>              (XP_Compute, AddExperience, LevelUp)
#   python3 -I tools/mp_check.py xpshare <excel> <log>  (the party share: members, J4's split)
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
source tools/gdb/two-players.py
source tools/gdb/player.py
source tools/gdb/tc-party.py
source tools/gdb/tc-drops.gdb
