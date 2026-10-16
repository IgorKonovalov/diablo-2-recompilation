# Seed-tree breakpoints for the pinned game.exe (plan 0003 Phase 2), without gdb settings and without the room
# activation lines RRESEED / RACT / AROOM, so that a logger which also loads tools/gdb/drlg-roomk.py (whose JSON
# lines carry those tags) can source it: tools/gdb/seed-tree.gdb sources it and adds the three in this file's plain
# format; tools/gdb/sweep-roomk.gdb (plan 0038 H5c) sources it after the Python loggers. tools/rng.py seedtree reads
# both forms. One line per event; every value is hex unless noted.
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
printf "ACT idx=%u map=%08x base=%08x seed=%08x:%08x tomb94=%u tomb484=%u bit474=%u actp=%08x\n", *(unsigned char*)($esi+0x480), *(unsigned*)($esi+0x458), *(unsigned*)($esi+0x470), *(unsigned*)($esi), *(unsigned*)($esi+4), *(unsigned*)($esi+0x94), *(unsigned*)($esi+0x484), *(unsigned*)($esi+0x474), $esi
continue
end

# DRLG_ActCreate exit: act seed after 0x00641F60 / 0x0061B7E0 / 0x00678AD0 / initial level.
break *0x00642F61
commands
silent
printf "ACTEND idx=%u seed=%08x:%08x\n", *(unsigned char*)($esi+0x480), *(unsigned*)($esi), *(unsigned*)($esi+4)
continue
end

# DRLG_LevelCreate right after RNG_SeedInit: level in ESI, act in EBX, levelId in EDI; ra = the caller's return
# address (three pushes after the entry), actp = the act (plan 0038 H5c).
break *0x00642B67
commands
silent
printf "LEVEL id=%u act=%u type=%u base=%08x seed=%08x:%08x ra=%08x actp=%08x\n", $edi, *(unsigned char*)($ebx+0x480), *(unsigned*)($esi), *(unsigned*)($ebx+0x470), *(unsigned*)($esi+0x1c4), *(unsigned*)($esi+0x1c8), *(unsigned*)($esp+12), $ebx
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

# Plan 0038 batch H5c. LevelLinkBuild 0x006772C0, level 6's link value 3 (0x006774BB) or 1 (0x006774D6), just
# before the step of the act seed itself (ESI = act); ACTSTEPX after it (EAX = the value written to level 27's data).
break *0x006774BB
commands
silent
printf "ACTSTEP idx=%u link=3 seed=%08x:%08x\n", *(unsigned char*)($esi+0x480), *(unsigned*)($esi), *(unsigned*)($esi+4)
continue
end
break *0x006774D6
commands
silent
printf "ACTSTEP idx=%u link=1 seed=%08x:%08x\n", *(unsigned char*)($esi+0x480), *(unsigned*)($esi), *(unsigned*)($esi+4)
continue
end
break *0x006774F9
commands
silent
printf "ACTSTEPX idx=%u seed=%08x:%08x v=%u\n", *(unsigned char*)($esi+0x480), *(unsigned*)($esi), $edx, $eax
continue
end

# Client unit constructor 0x00465FD0 (plan 0038 H5c): the (x, y) arguments (EBX, [EBP+0x10]) and the type,
# before the room lookup; CUNITRM the room 0x00465420 returned; CUNITEND the unit seed before the type switch
# (EDI = the active room or 0).
break *0x00465FFF
commands
silent
printf "CUNITXY unit=%08x type=%u x=%d y=%d\n", $esi, *(unsigned*)($ebp+0x14), $ebx, *(int*)($ebp+0x10)
continue
end
break *0x0046602C
commands
silent
printf "CUNITRM unit=%08x aroom=%08x\n", $esi, $eax
continue
end
break *0x0046609B
commands
silent
printf "CUNITEND unit=%08x type=%u aroom=%08x useed=%08x:%08x\n", $esi, $eax, $edi, *(unsigned*)($esi+0x20), *(unsigned*)($esi+0x24)
continue
end

# Server room driver (plan 0038 H5c): the active room's flags at the bit-0 test, sub_0052D160_NewRoomsUpdate
# 0x0052D1C9 and sub_0052D0F0_RoomUpdateOne 0x0052D0FB (ESI = active room).
break *0x0052D1C9
commands
silent
printf "NRF room=%08x flags=%u at=1c9 rs=%08x:%08x\n", $esi, *(unsigned*)($esi+0x34), *(unsigned*)($esi+0x6c), *(unsigned*)($esi+0x70)
continue
end
break *0x0052D0FB
commands
silent
printf "NRF room=%08x flags=%u at=0fb rs=%08x:%08x\n", $esi, *(unsigned*)($esi+0x34), *(unsigned*)($esi+0x6c), *(unsigned*)($esi+0x70)
continue
end
