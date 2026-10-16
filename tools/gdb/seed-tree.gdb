# Seed-tree logger for the pinned game.exe (plan 0003 Phase 2).
# Run through tools/d2run.py. One line per event; every value is hex unless noted.
# Registers are the 32-bit views ($esi...): the game is 32-bit code in a wow64 process.
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass

source tools/gdb/seed-tree-core.gdb

# 0x0066EE40 entry (runs just before DRLG_RoomActivate): DRLG room in ECX, seed before the re-init.
break *0x0066EE40
commands
silent
printf "RRESEED room=%08x r04=%08x seed=%08x:%08x type=%u\n", $ecx, *(unsigned*)($ecx+4), *(unsigned*)($ecx+0x14), *(unsigned*)($ecx+0x18), *(unsigned*)($ecx+0x48)
continue
end

# DRLG_RoomActivate just before its step: DRLG room in ESI, DRLG act in [EBP-8]; plan 0038 H5c adds the flags
# inputs +0x28 and +0x60, the flags [EBP-4] and the RoomTile counts T[+0x18], T[+0x20].
break *0x0064233A
commands
silent
printf "RACT room=%08x r04=%08x seed=%08x:%08x dact=%08x f28=%08x r60=%08x fl=%u nw=%u nf=%u\n", $esi, *(unsigned*)($esi+4), *(unsigned*)($esi+0x14), *(unsigned*)($esi+0x18), *(unsigned*)(*(unsigned*)($ebp-8)+0x46c), *(unsigned*)($esi+0x28), *(unsigned*)($esi+0x60), *(unsigned*)($ebp-4), *(unsigned*)(*(unsigned*)($esi+0x54)+0x18), *(unsigned*)(*(unsigned*)($esi+0x54)+0x20)
continue
end

# DRLG_RoomActivate after DUNGEON_RoomCreate: active room in EAX, DRLG room in ESI.
break *0x0064236E
commands
silent
printf "AROOM room=%08x aroom=%08x drlgseed=%08x:%08x aseed=%08x:%08x flags=%u\n", $esi, $eax, *(unsigned*)($esi+0x14), *(unsigned*)($esi+0x18), *(unsigned*)($eax+0x6c), *(unsigned*)($eax+0x70), *(unsigned*)($eax+0x34)
continue
end

continue
