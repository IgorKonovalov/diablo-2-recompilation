# Treasure-class drop logger for the pinned game.exe (plan 0004 Phase 2; quality-roll lines plan 0010 Phase 2).
# Run through tools/d2run.py; check with `python3 -I tools/tc.py replay <log>`.
# One line per event, values hex unless noted. Registers are the 32-bit views (wow64).
# Addresses: docs/findings/items/0001-tc-resolution.md (TC_ResolveDrops 0x0055A6D0 and its callees).
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass

# Seeds once, so a run can be tied to its -seed (as in seed-tree.gdb).
break *0x0052C312
commands
silent
printf "GAME override=%u seed=%08x:%08x\n", *(unsigned*)($edi+0x84), *(unsigned*)($edi+0xd0), *(unsigned*)($edi+0xd4)
continue
end

# TC_DropByIndex before TC_GetByIndex: base TC index and the upgrade level (0 = no upgrade).
break *0x0055AFED
commands
silent
printf "DROP base=%u lvl=%u src=%08x\n", *(unsigned short*)($ebp+0xc), $ebx, $esi
continue
end

# TC_ResolveDrops entry: ECX game, EDX source, stack (killer, tc, forcedQ, ilvl, noNoDrop, out, count*, max).
break *0x0055A6D0
commands
silent
printf "TCR src=%08x stype=%u sclass=%u seed=%08x:%08x killer=%08x tc=%u fq=%u ilvl=%u nonodrop=%u max=%d g6a=%u diff=%u exp=%u pover=%u", $edx, *(unsigned*)$edx, *(unsigned*)($edx+4), *(unsigned*)($edx+0x20), *(unsigned*)($edx+0x24), *(unsigned*)($esp+4), (*(unsigned*)($esp+8) - *(unsigned*)0x0096C5EC) / 0x2c, *(unsigned*)($esp+0xc), *(unsigned*)($esp+0x10), *(unsigned*)($esp+0x14), *(int*)($esp+0x20), *(unsigned char*)($ecx+0x6a), *(unsigned char*)($ecx+0x6d), *(unsigned*)($ecx+0x70), *(unsigned*)0x00883D70
if *(unsigned*)$edx == 1
printf " mflags=%02x suid=%u", *(unsigned char*)(*(unsigned*)($edx+0x14)+0x16), *(unsigned short*)(*(unsigned*)($edx+0x14)+0x26)
end
if *(unsigned*)($esp+4) != 0
printf " ktype=%u kclass=%u", *(unsigned*)(*(unsigned*)($esp+4)), *(unsigned*)(*(unsigned*)($esp+4)+4)
end
printf "\n"
continue
end

# NoDrop scaling inputs: party after the clamp, alive player count, monster_playercount cap.
break *0x0055A8EE
commands
silent
printf "PARTY party=%d\n", $edi
continue
end
break *0x0055A8F9
commands
silent
printf "PLAYERS players=%d\n", $eax
continue
end
break *0x0055A926
commands
silent
printf "CAP cap=%d\n", $eax
continue
end

# The NoDrop fild: n, NoDrop, total and the x87 control word.
break *0x0055A93B
commands
silent
printf "NDIN n=%d nd=%d total=%d fctrl=%04x\n", $edi, *(int*)($ebp-0x50c), *(int*)($ebp-0x508), $fctrl
continue
end

# Every positive-picks path joins here: NoDrop' (unscaled when n <= 1 or NoDrop = 0).
break *0x0055A9D9
commands
silent
printf "NDP ndp=%d total=%d\n", *(int*)($ebp-0x50c), *(int*)($ebp-0x508)
continue
end

# After the inlined guarded range draw on the source seed (EBX = source).
break *0x0055AA3F
commands
silent
printf "PICK range=%d roll=%u ndp=%d seed=%08x:%08x\n", *(int*)($ebp-0x510), $esi, $ecx, *(unsigned*)($ebx+0x20), *(unsigned*)($ebx+0x24)
continue
end

# Negative picks: the deterministic roll and the total it is compared with.
break *0x0055AAC2
commands
silent
printf "NEG roll=%d total=%d\n", $esi, $edi
continue
end

# Entry selected (both selection paths join; >= nEntries is a miss).
break *0x0055AB35
commands
silent
printf "SEL i=%d\n", $edi
continue
end

# Sub-TC pushed: TC_GetByIndex(e->index, 0) returned EAX.
break *0x0055AB75
commands
silent
printf "SUB tc=%u\n", ($eax - *(unsigned*)0x0096C5EC) / 0x2c
continue
end

# Oracle: sub_00558640_DropRollQuality entry, only when called from the resolver.
break *0x00558640
commands
silent
if *(unsigned*)$esp == 0x0055ADBF
printf "QIN item=%u ilvl=%u seed=%08x:%08x ratio=%u,%u,%u,%u,%u,%u\n", $eax, $ecx, *(unsigned*)(*(unsigned*)($esp+8)+0x20), *(unsigned*)(*(unsigned*)($esp+8)+0x24), *(unsigned short*)(*(unsigned*)($esp+0x10)), *(unsigned short*)(*(unsigned*)($esp+0x10)+2), *(unsigned short*)(*(unsigned*)($esp+0x10)+4), *(unsigned short*)(*(unsigned*)($esp+0x10)+6), *(unsigned short*)(*(unsigned*)($esp+0x10)+8), *(unsigned short*)(*(unsigned*)($esp+0x10)+10)
end
continue
end
# Inside the roll (plan 0010 Phase 2; docs/findings/items/0002-quality-roll.md sections 2 and 7). Both functions
# below have one caller each (0x0055ADBA -> 0x00558640, 0x00558714 -> 0x005585D0), so no return-address test.
# After ITEMRATIO_Select (call at 0x005586DB): EAX = row pointer or 0; row index from g_pItemRatio (0x0096CC4C),
# 0x44-byte records. Not reached on the three early returns.
break *0x005586E0
commands
silent
if $eax != 0
printf "QROW row=%d\n", ($eax - *(unsigned*)0x0096CC4C) / 0x44
else
printf "QROW row=-1\n"
end
continue
end
# sub_005585D0_DropMagicFind (ESI = killer), after its first sub_00625500_UnitGetStat(killer, 80, 0) (stdcall,
# ret 0xC): EAX = the killer's stat 80. Not reached when the killer is null or its type is above 1 (MF 0).
break *0x005585E4
commands
silent
printf "QKMF kmf=%d ktype=%u kclass=%u\n", $eax, *(unsigned*)$esi, *(unsigned*)($esi+4)
continue
end
# sub_0058F0D0_MonsterOwner returned a non-zero owner (EAX), about to read its stat 80.
break *0x005585F1
commands
silent
printf "QOWN otype=%u oclass=%u\n", *(unsigned*)$eax, *(unsigned*)($eax+4)
continue
end
# After UnitGetStat(owner, 80, 0): EAX = the owner's stat 80.
break *0x005585FB
commands
silent
printf "QOMF omf=%d\n", $eax
continue
end
# Back in the roll after sub_005585D0_DropMagicFind: EAX = the magic find the four tests use.
break *0x00558719
commands
silent
printf "QMF mf=%d\n", $eax
continue
end

# Oracle exit (also reached with a forced quality): EAX quality, EDI source.
break *0x0055ADBF
commands
silent
printf "QOUT q=%u seed=%08x:%08x\n", $eax, *(unsigned*)($edi+0x20), *(unsigned*)($edi+0x24)
continue
end

# Around sub_0055A550_DropCreateItem: ECX item, ESI source, stack (game, quality, uidx, flags).
break *0x0055AEE7
commands
silent
printf "CPRE item=%u q=%u uidx=%u up=%u seed=%08x:%08x\n", $ecx, *(unsigned*)($esp+4), *(unsigned*)($esp+8), *(unsigned*)($esp+12), *(unsigned*)($esi+0x20), *(unsigned*)($esi+0x24)
continue
end
break *0x0055AEEC
commands
silent
printf "CPOST unit=%08x seed=%08x:%08x", $eax, *(unsigned*)(*(unsigned*)($ebp-0x524)+0x20), *(unsigned*)(*(unsigned*)($ebp-0x524)+0x24)
if $eax != 0
printf " utype=%u uclass=%u", *(unsigned*)$eax, *(unsigned*)($eax+4)
end
printf "\n"
continue
end

# Common exit: output count and the final source seed.
break *0x0055AF80
commands
silent
printf "TCEND count=%d seed=%08x:%08x\n", *(int*)(*(unsigned*)($ebp-0x52c)), *(unsigned*)(*(unsigned*)($ebp-0x524)+0x20), *(unsigned*)(*(unsigned*)($ebp-0x524)+0x24)
continue
end

continue
