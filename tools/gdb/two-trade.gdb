# Two-client trade logger (plan 0067 Phase 2, cases T1-T13 of docs/findings/multiplayer/0003-trade.md § 11):
# tools/gdb/two-pilot.gdb's files (pilot.py: PLR, RL, RRESEED, CB, MON; two-players.py: PLRS for the joiner's driver)
# plus tools/gdb/two-trade.py (the trade module's entries and returns, read-only, ADR-0003). Attach it to the HOST
# (it runs the server game, ADR-0008). The runner's ready line is TRDY (review-fix 16).
#   tools/ufwcheck.sh <session> workspace/logs/p44h-run/ufw-baseline.sha256 <ufw log> || exit 1
#   python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-trade.gdb --steps tools/gdb/two-host-normal.steps \
#       --after 4000 --install TAG HOST.d2s --log workspace/logs/<run>/<session>-host.log
# Check with
#   python3 -I tools/trade_check.py check workspace/logs/<run>/<session>-host.log --excel workspace/merged/data/global/excel
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
source tools/gdb/two-trade.py
continue
