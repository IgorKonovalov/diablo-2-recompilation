# Affix selection logger (plan 0021 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by),
# tools/gdb/uniques.py (ItemCreateByQuality, the builders, the fallbacks; plan 0019), tools/gdb/affixes.py (the
# affix picks, rare names and count, superior and low rows, the property and staff-mod oracles, the post-switch
# ethereal and socket boundaries) and the drop lines of tools/gdb/tc-drops.gdb (TC resolution and the quality roll,
# sourced last: it ends with `continue`). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --seed 2101 --gdb tools/gdb/affixes.gdb --steps tools/gdb/uniques-hell.steps \
#       --after 900 --log workspace/logs/affixes-2101-hell.log
# Check with
#   python3 -I tools/affixes.py check workspace/logs/affixes-*.log
#   python3 -I tools/uniques.py check <log>;  python3 -I tools/quality.py check <log>;  tools/tc.py replay <log>
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
source tools/gdb/tc-drops.gdb
