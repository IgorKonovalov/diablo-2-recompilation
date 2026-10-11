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
printf "GAME override=%u map=%08x seed=%08x:%08x\n", *(unsigned*)($edi+0x84), *(unsigned*)($edi+0x7c), *(unsigned*)($edi+0xd0), *(unsigned*)($edi+0xd4)
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

continue
