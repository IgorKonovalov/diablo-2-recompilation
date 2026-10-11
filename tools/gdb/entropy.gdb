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

# Clock path of the seed initialisation (plan 0003 Phase 1): run with -seed 0, which is not applied.
# Prints the inputs and the result of every RNG_EntropySeed call, and the game seeds GAME_InitSeeds sets.

# RNG_EntropySeed 0x00650DE0, after GetTickCount: EAX = tick count, EDI = time(NULL), ESI = salt.
break *0x00650DF6
commands
silent
printf "ENTIN tick=%08x time=%08x salt=%08x ret=%08x\n", $eax, $edi, $esi, *(unsigned*)($esp+8)
continue
end

# RNG_EntropySeed before ret: EAX = result.
break *0x00650E22
commands
silent
printf "ENTOUT v=%08x\n", $eax
continue
end

# GAME_InitSeeds, no-override path, just before the map seed store (EAX = map seed): game in EDI.
break *0x0052C2E2
commands
silent
printf "GAMECLOCK override=%u map=%08x seed=%08x:%08x\n", *(unsigned*)($edi+0x84), $eax, *(unsigned*)($edi+0xd0), *(unsigned*)($edi+0xd4)
continue
end

# GAME_InitSeeds, -seed path (should not fire with -seed 0).
break *0x0052C312
commands
silent
printf "GAME override=%u map=%08x seed=%08x:%08x\n", *(unsigned*)($edi+0x84), *(unsigned*)($edi+0x7c), *(unsigned*)($edi+0xd0), *(unsigned*)($edi+0xd4)
continue
end

continue
