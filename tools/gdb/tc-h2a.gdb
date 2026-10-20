# Plan 0038 batch H2a logger (run:2026-10-20-sweep-items-tc): the tools/gdb/quests.gdb chain (pilot.py, uniques.py,
# affixes.py, vendors.py, mon-pool.py, quests.py) plus the H2a lines below, then tools/gdb/tc-drops.gdb (sourced last:
# it ends with `continue`). Breakpoints only print and continue. Values hex unless noted.
# Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 2 --seed 3801 --gdb tools/gdb/tc-h2a.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install h2a UniqNova.d2s --log workspace/logs/h2a/items-tc-s2-3801-normal.log
# Check with python3 -I tools/sweep_h2a.py logs <logs> and python3 -I tools/tc.py replay <log>.
#
# New lines (addresses read in docs/findings/items/0001-tc-resolution.md § Plan 0038 batch H2a):
#   MDD0  0x005A6830 sub_005A6830_MonDeathDrop entry (EDX = event, [EDX+4] = the dying monster): return address,
#         monster, class, unit+0xC4
#   MDDB  0x005A686D after `shr eax, 0x11; and eax, 1`: the bit-17 test (1 = skip the drop)
#   MDDC  0x005A68A3 after the collision test (mask 0x801) at the monster's position: AX (non-zero = skip the drop)
#   MDDX  0x005A68D1 the MONSTER_DropItems call
#   MDI   0x005A6600 MONSTER_DropItems entry: return address, monster [esp+8], noNoDrop [esp+0xC]
#   MNN   0x005A8000 sub_005A8000_MonDropNoNoDrop entry: return address, ECX, EDX (the monster)
#   CFI   0x005D8780 sub_005D8780_CorpseFindItem entry: return address
#   GTY   0x0055AEFA after ITEMS_UnitIsType(unit, 4): unit, its class, EAX
#   GMUL  0x0055AF21 the mul= product: stat 14 (EAX, from STATS_GetUnitStat(unit, 14, 0)), the entry's mul word (ECX)
#   GMULX 0x0055AF2F the STATS_SetStat(unit, 14, v) call: v ([esp])
#   GMAX  0x0055AF4F after the count increment: count, max
#   GF0   0x005589A0 sub_005589A0_DropGoldFind entry (EBX killer, EDI unit): return address, killer, unit
#   GF1   0x005589AE the unit's own item type (EAX, from 0x0062B400)
#   GF2   0x005589BE the killer's stat 79 (EAX)
#   GF3   0x005589CA sub_0058F0D0_MonsterOwner(killer) (EAX, 0 = none)
#   GF4   0x005589D8 the owner's stat 79 (EAX)
#   GF5   0x005589E4 stat 14 (EAX) and the factor 100 + GF (ESI)
#   GF6   0x00558A02 the STATS_SetStat(unit, 14, v) call: v ([esp])
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
source tools/gdb/vendors.py
source tools/gdb/mon-pool.py
source tools/gdb/quests.py

break *0x005A6830
commands
silent
printf "MDD0 ret=%08x mon=%08x", *(unsigned*)$esp, *(unsigned*)($edx+4)
if *(unsigned*)($edx+4) != 0
printf " cls=%u c4=%08x", *(unsigned*)(*(unsigned*)($edx+4)+4), *(unsigned*)(*(unsigned*)($edx+4)+0xc4)
end
printf "\n"
continue
end
break *0x005A686D
commands
silent
printf "MDDB bit17=%u\n", $eax
continue
end
break *0x005A68A3
commands
silent
printf "MDDC coll=%04x\n", $eax & 0xffff
continue
end
break *0x005A68D1
commands
silent
printf "MDDX\n"
continue
end
break *0x005A6600
commands
silent
printf "MDI ret=%08x mon=%08x nonodrop=%u\n", *(unsigned*)$esp, *(unsigned*)($esp+8), *(unsigned*)($esp+0xc)
continue
end
break *0x005A8000
commands
silent
printf "MNN ret=%08x ecx=%08x mon=%08x\n", *(unsigned*)$esp, $ecx, $edx
continue
end
break *0x005D8780
commands
silent
printf "CFI ret=%08x\n", *(unsigned*)$esp
continue
end

break *0x0055AEFA
commands
silent
printf "GTY unit=%08x uclass=%u is4=%d\n", $edi, *(unsigned*)($edi+4), $eax
continue
end
break *0x0055AF21
commands
silent
printf "GMUL gold=%d mul=%u\n", $eax, $ecx
continue
end
break *0x0055AF2F
commands
silent
printf "GMULX v=%d\n", *(int*)$esp
continue
end
break *0x0055AF4F
commands
silent
printf "GMAX count=%d max=%d\n", *(int*)$eax, $ecx
continue
end
break *0x005589A0
commands
silent
printf "GF0 ret=%08x killer=%08x unit=%08x\n", *(unsigned*)$esp, $ebx, $edi
continue
end
break *0x005589AE
commands
silent
printf "GF1 type=%d\n", $eax
continue
end
break *0x005589BE
commands
silent
printf "GF2 kgf=%d\n", $eax
continue
end
break *0x005589CA
commands
silent
printf "GF3 owner=%08x\n", $eax
continue
end
break *0x005589D8
commands
silent
printf "GF4 ogf=%d\n", $eax
continue
end
break *0x005589E4
commands
silent
printf "GF5 gold=%d factor=%d\n", $eax, $esi
continue
end
break *0x00558A02
commands
silent
printf "GF6 v=%d\n", *(int*)$esp
continue
end

source tools/gdb/tc-drops.gdb
