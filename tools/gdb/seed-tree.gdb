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

# GAME_InitSeeds, -seed path, just before ret: game in EDI.
break *0x0052C312
commands
silent
printf "GAME override=%u g=%08x map=%08x seed=%08x:%08x\n", *(unsigned*)($edi+0x84), $edi, *(unsigned*)($edi+0x7c), *(unsigned*)($edi+0xd0), *(unsigned*)($edi+0xd4)
continue
end

# GAME_InitSeeds, no-override path (should not fire under -seed).
break *0x0052C2E2
commands
silent
printf "GAME override=%u map=%08x seed=%08x:%08x\n", *(unsigned*)($edi+0x84), $eax, *(unsigned*)($edi+0xd0), *(unsigned*)($edi+0xd4)
continue
end

# DRLG_ActCreate after the act-specific draws: act in ESI.
break *0x00642F1A
commands
silent
printf "ACT idx=%u map=%08x base=%08x seed=%08x:%08x tomb94=%u tomb484=%u bit474=%u\n", *(unsigned char*)($esi+0x480), *(unsigned*)($esi+0x458), *(unsigned*)($esi+0x470), *(unsigned*)($esi), *(unsigned*)($esi+4), *(unsigned*)($esi+0x94), *(unsigned*)($esi+0x484), *(unsigned*)($esi+0x474)
continue
end

# DRLG_ActCreate exit: act seed after 0x00641F60 / 0x0061B7E0 / 0x00678AD0 / initial level.
break *0x00642F61
commands
silent
printf "ACTEND idx=%u seed=%08x:%08x\n", *(unsigned char*)($esi+0x480), *(unsigned*)($esi), *(unsigned*)($esi+4)
continue
end

# DRLG_LevelCreate right after RNG_SeedInit: level in ESI, act in EBX, levelId in EDI.
break *0x00642B67
commands
silent
printf "LEVEL id=%u act=%u type=%u base=%08x seed=%08x:%08x\n", $edi, *(unsigned char*)($ebx+0x480), *(unsigned*)($esi), *(unsigned*)($ebx+0x470), *(unsigned*)($esi+0x1c4), *(unsigned*)($esi+0x1c8)
continue
end

# DRLG_RoomCreate after the room's first step: level in ESI, room in EDI, type at [EBP-4].
break *0x0066B47C
commands
silent
printf "ROOM level=%u type=%u lvlseed=%08x:%08x room=%08x:%08x r04=%08x\n", *(unsigned*)($esi+0x1d0), *(unsigned*)($ebp-4), *(unsigned*)($esi+0x1c4), *(unsigned*)($esi+0x1c8), *(unsigned*)($edi+0x14), *(unsigned*)($edi+0x18), *(unsigned*)($edi+4)
continue
end

# DUNGEON_ActCreate entry: who creates the act (return address), act byte, seed, flag arg 3 (dungeon act +0x50).
break *0x006194A0
commands
silent
printf "DACT ret=%08x act=%u seed=%08x arg3=%u clientact=%08x\n", *(unsigned*)$esp, *(unsigned char*)($esp+4), *(unsigned*)($esp+8), *(unsigned*)($esp+12), *(unsigned*)0x007a0634
continue
end

# 0x0066EE40 entry (runs just before DRLG_RoomActivate): DRLG room in ECX, seed before the re-init.
break *0x0066EE40
commands
silent
printf "RRESEED room=%08x r04=%08x seed=%08x:%08x type=%u\n", $ecx, *(unsigned*)($ecx+4), *(unsigned*)($ecx+0x14), *(unsigned*)($ecx+0x18), *(unsigned*)($ecx+0x48)
continue
end

# DRLG_RoomActivate just before its step: DRLG room in ESI, DRLG act in [EBP-8].
break *0x0064233A
commands
silent
printf "RACT room=%08x r04=%08x seed=%08x:%08x dact=%08x\n", $esi, *(unsigned*)($esi+4), *(unsigned*)($esi+0x14), *(unsigned*)($esi+0x18), *(unsigned*)(*(unsigned*)($ebp-8)+0x46c)
continue
end

# DRLG_RoomActivate after DUNGEON_RoomCreate: active room in EAX, DRLG room in ESI.
break *0x0064236E
commands
silent
printf "AROOM room=%08x aroom=%08x drlgseed=%08x:%08x aseed=%08x:%08x flags=%u\n", $esi, $eax, *(unsigned*)($esi+0x14), *(unsigned*)($esi+0x18), *(unsigned*)($eax+0x6c), *(unsigned*)($eax+0x70), *(unsigned*)($eax+0x34)
continue
end

# Server unit seed (0x00552DF0), parent-seed path: unit in EDI, parent seed pointer in ESI.
break *0x00552E2F
commands
silent
printf "SUNITPRE unit=%08x type=%u class=%u p=%08x pre=%08x:%08x\n", $edi, *(unsigned*)$edi, *(unsigned*)($edi+4), $esi, *(unsigned*)$esi, *(unsigned*)($esi+4)
continue
end
break *0x00552E55
commands
silent
printf "SUNIT unit=%08x p=%08x post=%08x:%08x useed=%08x:%08x u28=%08x\n", $edi, $esi, *(unsigned*)$esi, *(unsigned*)($esi+4), *(unsigned*)($edi+0x20), *(unsigned*)($edi+0x24), *(unsigned*)($edi+0x28)
continue
end
# Server unit seed, null-parent path (entropy): should be rare.
break *0x00552E7D
commands
silent
printf "SUNITENT unit=%08x type=%u useed=%08x:%08x\n", $edi, *(unsigned*)$edi, *(unsigned*)($edi+0x20), *(unsigned*)($edi+0x24)
continue
end

# Client unit constructor 0x00465FD0, room draw: active room in EDI, unit in ESI.
break *0x0046606A
commands
silent
printf "CUNITPRE unit=%08x type=%u aroom=%08x pre=%08x:%08x\n", $esi, *(unsigned*)$esi, $edi, *(unsigned*)($edi+0x6c), *(unsigned*)($edi+0x70)
continue
end
break *0x00466098
commands
silent
printf "CUNIT unit=%08x aroom=%08x post=%08x:%08x useed=%08x:%08x u28=%08x\n", $esi, $edi, *(unsigned*)($edi+0x6c), *(unsigned*)($edi+0x70), *(unsigned*)($esi+0x20), *(unsigned*)($esi+0x24), *(unsigned*)($esi+0x28)
continue
end

# 0x005BDFF0 (monster population step of the active-room seed +0x6C): ECX = &room->seed.
break *0x005BDFFB
commands
silent
printf "POPSTEP aroom=%08x pre=%08x:%08x\n", $ecx-0x6c, *(unsigned*)$ecx, *(unsigned*)($ecx+4)
continue
end

continue
