# Both item loggers in one session (plan 0027 Phase 3): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by),
# tools/gdb/uniques.py (ItemCreateByQuality, the builders, the fallbacks), tools/gdb/affixes.py (the affix picks,
# rare names and count, superior and low rows, the APR0/APR1, STF0/STF1, ETB0/ETB1 and SCK0/SCK1 brackets),
# tools/gdb/props.py (ItemInitStats, ItemApplyProps with its slots, rolls and writes, ETH0/ETHR/ETHX, SOK*, the final
# stat lists) and the drop lines of tools/gdb/tc-drops.gdb (sourced last: it ends with `continue`).
# The two item loggers share no tag: the affix logger's ethereal bracket is ETB0/ETB1 (ETH0/ETH1 before plan 0027
# Phase 3), so props.py's ETH0/ETHR/ETHX are the only ETH* lines. Where both set a breakpoint on one address
# (0x0065FEC0, 0x00556CA0, 0x00556B60), gdb runs both handlers; each writes its own line.
# Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 3 --seed 2701 --gdb tools/gdb/items-chain.gdb --steps tools/gdb/uniques-hell.steps \
#       --after 900 --log workspace/logs/ichain-2701-hell.log
# Check with
#   python3 -I tools/items_chain.py both workspace/logs/ichain-*.log
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
source tools/gdb/uniques.py
source tools/gdb/affixes.py
source tools/gdb/props.py
source tools/gdb/tc-drops.gdb
