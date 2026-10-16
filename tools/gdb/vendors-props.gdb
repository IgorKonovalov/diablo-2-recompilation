# Vendor stock and gamble logger with the property lines (plan 0031 Phase 2): as tools/gdb/vendors.gdb, with
# tools/gdb/props.py (base stats, ItemApplyProps, sockets, the final stat lists) in place of tools/gdb/affixes.py.
# Check with tools/vendors.py check and python3 -I tools/items_chain.py props <log>.
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
source tools/gdb/props.py
source tools/gdb/vendors.py
continue
