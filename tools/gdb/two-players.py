# gdb Python helper for two-client sessions (plan 0044 Phase 1): every player unit of the HOST's server game, so that
# tools/d2pilot.py can steer either client from the host's log (the joiner runs without a debugger, ADR-0008). Source
# it after tools/gdb/pilot.py (or alone); nothing here feeds a model. One line per event, "TAG {json}".
# Addresses refer to the pinned game.exe (image base 0x400000).
#
#   PLRS  at most every 0.25 s, at COLL_PatternMark 0x0064EA90 with mask 0x80 (a player's mark; pilot.py's PLR
#         breakpoint), at PATH_SetMarkMask 0x00648C30 (any new path) and at the server frame sub_0052D870_GameTick
#         (plan 0044 Phase 2 live test: without it the line stopped while both players stood, so a party or hostility
#         change made standing still never reached the log):
#         "p": one entry per player unit in the game's player lists (game +0x1120, 128 heads, next = unit +0xE4):
#           id (unit +0x0C), cls (+0x04), mode (+0x10), x, y (dynamic path unit +0x2C: +0x02, +0x06), room (path
#           +0x1C), lid (room +0x10 -> DRLG room +0x58 -> level +0x1D0), dead (+0xC6 bit 0), as tools/gdb/tc-party.py
#           reads them (plan 0011, [I]);
#           tk: PlayerData (unit +0x14) +0x160, the tick the travel gates read (0x0055B6C0 with no other player:
#           waypoint packet 0x0054C5FC + 10000 ms, portal operate 0x005848BC + 5000 ms), written with
#           GetTickCount() by 0x0055B720 (called from 0x005A5F51 in 0x005A5E50);
#           hl: the PlayerData +0x38 list, [other player's unit id (+0x00), stamp (+0x08)] per entry, next +0x10
#           (0x0055B6F3-0x0055B710; 0x005A5F41 writes GetTickCount() + 60000 for the pair);
#         "pty": the party list (game +0x1D2C -> +4 first; party +0 u16 id, +4 member list {unit id, next}, +8 next),
#           as tc-party.py reads it.
#   "u" is the unit pointer (the XC0/XA0 lines of tools/gdb/player.py name players by pointer).
#   PLRK  the same list, unthrottled, at XP_OnMonsterKill entry 0x0057E990 (plan 0044 Phase 2: the party share check).
#   HD0 HDR HDS HDO  the hostility declaration 0x005A5E50 (entry; the pair-stamp compare 0x005A5F20; the new stamp
#         0x005A5F4C; the early refusal 0x005A5FDE); GW GWR GWP the waypoint gate (0x0054C60F compare, 0x0054C614
#         refused, 0x0054C633 passed); PH PO GP GPR GPP the portal operate (0x00584894 hostile-to-any result,
#         0x005848AF operator id vs owner id, 0x005848CD gate compare, 0x005848D1 refused, 0x005848E7 passed).
#         Checked by tools/mp_check.py gates (case MP24).
#   The game pointer comes from GAME_InitSeeds 0x0052C312 (EDI), as pilot.py's GPTR line.
#   Readings: docs/findings/multiplayer/0001-cases.md.
import json
import struct
import time

import gdb


def _two_players_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "t": 0.0}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def player(u):
        d = {"id": u32(u + 0x0C), "u": u, "cls": u32(u + 0x04), "mode": u32(u + 0x10), "dead": mem(u + 0xC6, 1)[0] & 1,
             "x": None, "y": None, "room": 0, "lid": None, "tk": None, "hl": []}
        path = u32(u + 0x2C)
        if path:
            d["x"], d["y"], d["room"] = u16(path + 2), u16(path + 6), u32(path + 0x1C)
            dr = u32(d["room"] + 0x10) if d["room"] else 0
            d["lid"] = s32(u32(dr + 0x58) + 0x1D0) if dr else None
        pd = u32(u + 0x14)
        if pd:
            d["tk"] = u32(pd + 0x160)
            e, k = u32(pd + 0x38), 0
            while e and k < 16:
                d["hl"].append([u32(e), u32(e + 8)])
                e = u32(e + 0x10)
                k += 1
        return d

    def scan(tag="PLRS"):
        game = st["game"]
        if not game:
            return
        out = []
        for i in range(128):
            u, n = u32(game + 0x1120 + 4 * i), 0
            while u and n < 64:
                out.append(player(u))
                u = u32(u + 0xE4)
                n += 1
        pty = []
        plist = u32(game + 0x1D2C)
        p, n = (u32(plist + 4) if plist else 0), 0
        while p and n < 16:
            ids, m, k = [], u32(p + 4), 0
            while m and k < 16:
                ids.append(u32(m))
                m = u32(m + 4)
                k += 1
            pty.append({"id": u16(p), "m": ids})
            p = u32(p + 8)
            n += 1
        gdb.write("%s %s\n" % (tag, json.dumps({"t": round(time.time(), 2), "p": out, "pty": pty}, separators=(",", ":"))))
        gdb.flush()

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR two-players %r\n" % (e,))
            return False

    def on_game():
        st["game"] = reg("edi")

    def on_mark():
        if struct.unpack("<I", mem(reg("esp") + 20, 4))[0] != 0x80:
            return
        on_tick()

    def on_tick():
        now = time.time()
        if now - st["t"] >= 0.25:
            st["t"] = now
            scan()

    Bp(0x0052C312, on_game)
    Bp(0x0064EA90, on_mark)
    Bp(0x00648C30, on_tick)
    Bp(0x0052D870, on_tick)
    # PLRK: the same list, unthrottled, at XP_OnMonsterKill entry 0x0057E990 (ECX game), so a kill's credited player,
    # the party and every position are logged right before the kill's XK0 line (tools/mp_check.py xpshare).
    Bp(0x0057E990, lambda: scan("PLRK"))

    # ---- MP24 (plan 0044 Phase 2): the hostility declaration and the two travel gates, as multiplayer/0001 § 4 reads
    # them. Each line names the player by unit id; "now" is GetTickCount()'s value the code compares with.
    def uid(u):
        return u32(u + 0x0C) if u else None

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))
        gdb.flush()

    def on_hd0():
        sp = reg("esp")
        emit("HD0", {"p": uid(reg("edx")), "o": uid(u32(sp + 4)), "hostile": u32(sp + 8)})

    def on_hdr():       # 0x005A5F20 cmp ebx, eax: the pair's stamp (PlayerTickGet(P, O)) against now
        emit("HDR", {"p": uid(reg("esi")), "o": uid(reg("edi")), "stamp": reg("ebx"), "now": reg("eax")})

    def on_hds():       # 0x005A5F4C push eax: the new pair stamp, now + 60000, about to be written by 0x0055B720
        emit("HDS", {"p": uid(reg("esi")), "o": uid(reg("edi")), "stamp": reg("eax")})

    def on_hdo():       # 0x005A5FDE: the early refusal (not in a town, or a base level below 9): *out <- 1
        emit("HDO", {})

    def on_gw():        # 0x0054C60F cmp [ebp+8], eax: the waypoint gate, +0x160 + 10000 against now
        emit("GW", {"id": uid(reg("edi")), "lim": u32(reg("ebp") + 8), "now": reg("eax")})

    def on_gwr():       # 0x0054C614: refused (message 0x13)
        emit("GWR", {"id": uid(reg("edi"))})

    def on_gwp():       # 0x0054C633: passed
        emit("GWP", {})

    def on_ph():        # 0x00584894 test eax, eax: PlayerHostileToAny(game, operator)
        emit("PH", {"id": uid(u32(reg("esi") + 8)), "hostile": reg("eax")})

    def on_po():        # 0x005848AF cmp edi, eax: the operator's id against the portal owner's id
        emit("PO", {"op": reg("edi"), "owner": reg("eax")})

    def on_gp():        # 0x005848CD cmp edi, eax: the portal gate, +0x160 + 5000 against now
        emit("GP", {"id": uid(u32(reg("esi") + 8)), "lim": reg("edi"), "now": reg("eax")})

    def on_gpr():       # 0x005848D1: refused (message 0x13)
        emit("GPR", {})

    def on_gpp():       # 0x005848E7: passed
        emit("GPP", {})

    for a, f in ((0x005A5E50, on_hd0), (0x005A5F20, on_hdr), (0x005A5F4C, on_hds), (0x005A5FDE, on_hdo),
                 (0x0054C60F, on_gw), (0x0054C614, on_gwr), (0x0054C633, on_gwp),
                 (0x00584894, on_ph), (0x005848AF, on_po), (0x005848CD, on_gp), (0x005848D1, on_gpr),
                 (0x005848E7, on_gpp)):
        Bp(a, f)
    gdb.write("TWO-PLAYERS logger armed\n")


_two_players_main()
