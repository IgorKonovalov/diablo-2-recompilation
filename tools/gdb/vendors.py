# gdb Python logger for plan 0031 Phase 2 (vendor stock and gambling): the store seed and every draw on it, the
# stock build and gamble build as read in docs/findings/items/0009-vendors.md, the triggers, the creation calls, and
# the NPC positions tools/d2pilot.py npc steers by. Sourced by tools/gdb/vendors.gdb after tools/gdb/pilot.py,
# tools/gdb/uniques.py and tools/gdb/affixes.py (or tools/gdb/props.py in vendors-props.gdb). One line per event,
# "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Seeds are "low:high" hex. "S" is the
# store seed (Game+0x1D24 -> +0x08), "gs" the game seed (Game+0xD0).
#
#   GAME     0x0052C312 (GAME_InitSeeds, EDI = game): "GAME override=.. seed=.." as tools/gdb/tc-drops.gdb writes it
#            (tools/uniques.py resets its made-uniques set there), then VGAME {game, diff, exp, gver}
#   VSC0     0x005360D2 NPCSTORE_CtlCreate before its game-seed step (EBX game): gs
#   VSC1     0x00536100 after RNG_SeedInit: S, gs
#   VGL      once per process, right after the first GB0: g_GambleList 0x0096CAB0 (nRows, the item index array, countUpTo[0..99])
#   MA       0x00579D60 NPC_MenuAction (ECX game, EDX player; action, npc id, arg)
#   TO       0x00579430 NPC_TradeOpen (ECX game, EDX player; npc, sole, gamble): npc class and id, the record's
#            opened, built, stale, hirelingsBuilt, buildTick, S
#   STALE    0x00537230 NPCSTORE_ActStale entry (stack game, act, townEmpty): ret, act, townEmpty, and the act's store
#            records [class, opened, built, stale, buildTick]; STALEX the same records after it (returns 0x00537402
#            from sub_00537340_TownLevelLeave, 0x005375FC from sub_00537580_TownPlayerRemove)
#   RESET    0x00536D10 NPCSTORE_Reset (ECX game, EDX record): the record's class, built and stale bytes, ret
#   PLEAVE 0x00536B50, GFREE 0x00537190, PIEND 0x00555500: ECX, EDX, three stack words, ret
#   BS0      0x00576980 VENDOR_BuildStock entry: npc class, S, gs, difficulty, expansion, item version, the record's
#            entries (hex of nEntries x 12 bytes) and permanent codes
#   BSL      0x005769DE after VENDOR_StockLevel: clvl [ebp-0x18], ilvl (EAX), S
#   VD       stock draws: k "cnt" 0x00576A41 (RandLoHi count, EAX), "nq" 0x00576A80 (VENDOR_PickNormalQuality, EAX),
#            "mx" 0x00576B02 (RandLoHi(1, 3), EAX, before the + 1), "mc" 0x00576B1E (RandLoHi magic count, EAX); entry index
#            [ebp-8], S after
#   CS0      0x00576330 VENDOR_CreateStockItem entry (EDX code; stack game, send, q, ilvl, clvl): S
#   CSU      0x005763AA (Nightmare) / 0x0057641A (Hell) after RNG_RangeB(S, 100000): u (EAX), S
#   CSW      0x005764A8 the chosen code [ebp-4] and item index [ebp+8]
#   CRK      0x00576505 a Cracked low-quality item destroyed; CMM 0x00576536 a code mismatch destroyed
#   CSX      0x00576A9B / 0x00576B41 / 0x00576B9E VENDOR_CreateStockItem's result in the build (EAX), S, gs
#   CF0      0x00559CE0 ITEMS_CreateForStore entry (ECX source, EDX item index; stack game, kind, q, noSockets,
#            noEthereal, ilvl): ret, gs
#   CFX      0x005764DB (stock) / 0x005789FE (gamble) its result: item, class, quality, start seed (ItemData+0x10),
#            gs
#   BSX      0x00578BD0 / 0x005794C7 / 0x0057911B after VENDOR_BuildStock: S, gs
#   HB0      0x00576070 HIRE_BuildStock entry: S;  HBX 0x005767F0 / 0x005770CE / 0x00578C04 after it: S
#   GB0      0x00578790 GAMBLE_BuildInv entry (ECX game, EDX npc; player): npc class, S, gs, difficulty, expansion,
#            the DifficultyLevels gamble columns are read at GCL
#   GCL      0x00578861 clvl (EAX, before its store to [ebp-0x14]), DifficultyLevels row +0x44..+0x54 ([ebp-0x18]), S
#   GLV      0x005788B2 lvl before the clamp (EAX), S;  GPK 0x00578919 pick (EDX), item index (EBX), lvl [ebp+8],
#            count countUpTo[lvl], S;  GU 0x00578727 / 0x0057877B in GAMBLE_Upgrade: k uber/ultra, r (EAX), bound
#            (ESI / EDI), S;  GUP 0x0057896F GAMBLE_Upgrade's result (EAX);  GQ 0x005789DD quality (EAX), r (ECX),
#            S;  GBX 0x00578B24 after GAMBLE_BuildInv: S, gs
#   TICK     at most every 0.5 s at 0x005380D0 (the server's per-frame player room check): a heartbeat; it stops while
#            the single-player game is paused (its menu open), which is how tools/d2pilot.py npc tells the game menu
#   NPC      at most every 0.5 s at any COLL_PatternMark 0x0064EA90 call (a unit moving, the NPCs included): every unit
#            of a town NPC class
#            in the server game's monster lists: class, id, mode, x, y
import json
import struct
import time

import gdb


def _vendors_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "t": 0.0, "vgl": False}
    G_GAMBLE = 0x0096CAB0
    # MonStats rows with the `interact` flag (+0x0D bit 1), stock data
    NPC_CLASSES = {146, 147, 148, 150, 154, 155, 175, 176, 177, 178, 198, 199, 200, 201, 202, 210, 244, 245, 246, 251,
                   252, 253, 254, 255, 257, 264, 265, 266, 297, 331, 367, 377, 378, 405, 406, 408, 511, 512, 513, 514,
                   515, 520, 521, 527, 537, 538, 539}

    WP_CLASSES = {119, 145, 156, 157, 237, 238, 288, 323, 324, 398, 402, 429, 494, 496, 511, 539}   # d2pilot.py

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    FLUSH = ("MA", "TO", "BSX", "GBX", "HBX", "GFREE", "PLEAVE", "PIEND", "RESET", "STALEX")

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))
        if tag in FLUSH:            # tools/d2pilot.py npc waits for these; the game may stand still afterwards
            gdb.flush()

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def S(game=None):
        g = game or st["game"]
        if not g:
            return None
        c = u32(g + 0x1D24)
        return sd(c + 8) if c else None

    def gs(game=None):
        g = game or st["game"]
        return sd(g + 0xD0) if g else None

    def ginfo(g):
        return {"diff": u8(g + 0x6D), "exp": u32(g + 0x70), "gver": u16(g + 0x78)}

    def rec_of(game, cls):
        c = u32(game + 0x1D24)
        if not c:
            return None
        recs = u32(c + 4)
        for i in range(64):
            r = recs + 0x44 * i
            if u32(r) == cls:
                return r
        return None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR vendors %r\n" % (e,))
            return False

    def on_game():
        g = reg("edi")
        st["game"] = g
        gdb.write("GAME override=%u seed=%s\n" % (u32(g + 0x84), sd(g + 0xD0)))
        emit("VGAME", dict({"game": g}, **ginfo(g)))

    def on_vsc0():
        g = reg("ebx")
        st["game"] = g
        emit("VSC0", {"game": g, "gs": sd(g + 0xD0)})

    def on_vsc1():
        g = reg("ebx")
        emit("VSC1", {"S": sd(reg("esi")), "gs": sd(g + 0xD0)})

    def on_ma():
        esp = reg("esp")
        emit("MA", {"player": reg("edx"), "action": s32(esp + 4), "npc": u32(esp + 8), "arg": s32(esp + 12)})

    def on_to():
        esp = reg("esp")
        g, npc = reg("ecx"), u32(esp + 4)
        st["game"] = g
        cls = s32(npc + 4)
        d = {"cls": cls, "id": u32(npc + 0xC), "sole": s32(esp + 8), "gamble": s32(esp + 12), "S": S(g)}
        r = rec_of(g, cls)
        if r:
            d.update(opened=u32(r + 0x1C), built=u8(r + 0x20), hb=u8(r + 0x21), act=u8(r + 0x22), store=u8(r + 0x23),
                     stale=u8(r + 0x27), tick=u32(r + 0x28), gambler=u32(r + 0xC))
        emit("TO", d)

    def on_regs(tag):
        def f():
            esp = reg("esp")
            emit(tag, {"ret": u32(esp), "ecx": reg("ecx"), "edx": reg("edx"), "a1": s32(esp + 4), "a2": s32(esp + 8),
                       "a3": s32(esp + 12), "S": S()})
        return f

    def recs_of_act(game, act):
        c = u32(game + 0x1D24)
        out = []
        if not c:
            return out
        recs = u32(c + 4)
        for i in range(min(64, s32(c))):
            r = recs + 0x44 * i
            if u8(r + 0x22) == act and u8(r + 0x23) == 1:
                out.append([s32(r), u32(r + 0x1C), u8(r + 0x20), u8(r + 0x27), u32(r + 0x28)])
        return out

    def on_stale():
        esp = reg("esp")
        g, act, empty = u32(esp + 4), s32(esp + 8), s32(esp + 12)
        st["stale"] = (g, act)
        emit("STALE", {"ret": u32(esp), "act": act, "empty": empty, "S": S(g),
                       "recs": recs_of_act(g, act)})

    def on_stalex():
        if "stale" in st:
            g, act = st.pop("stale")
            emit("STALEX", {"act": act, "recs": recs_of_act(g, act)})

    def on_reset():
        esp, rec = reg("esp"), reg("edx")
        emit("RESET", {"ret": u32(esp), "cls": s32(rec), "built": u8(rec + 0x20), "stale": u8(rec + 0x27), "S": S()})

    def on_bs0():
        esp = reg("esp")
        g, npc = reg("ecx"), u32(esp + 4)
        st["game"] = g
        built = u32(esp + 8)
        rec = built - 0x20
        n, np_ = s32(rec + 0x30), s32(rec + 0x38)
        ent = mem(u32(rec + 0x2C), 12 * n).hex() if 0 < n <= 512 else ""
        perm = list(struct.unpack("<%dI" % np_, mem(u32(rec + 0x34), 4 * np_))) if 0 < np_ <= 256 else []
        emit("BS0", dict({"cls": s32(npc + 4), "npc": npc, "S": S(g), "gs": gs(g), "act": u8(rec + 0x22),
                          "n": n, "ent": ent, "perm": perm}, **ginfo(g)))

    def on_bsl():
        ebp = reg("ebp")
        emit("BSL", {"clvl": s32(ebp - 0x18), "ilvl": sreg("eax"), "S": S()})

    def on_vd(k):
        def f():
            emit("VD", {"k": k, "v": sreg("eax"), "e": s32(reg("ebp") - 8), "S": S()})
        return f

    def on_cs0():
        esp = reg("esp")
        emit("CS0", {"code": struct.pack("<I", reg("edx")).decode("latin-1"), "q": s32(esp + 12),
                     "ilvl": s32(esp + 16), "clvl": s32(esp + 20), "S": S()})

    def on_csu():
        emit("CSU", {"u": reg("eax"), "S": S()})

    def on_csw():
        ebp = reg("ebp")
        emit("CSW", {"want": struct.pack("<I", u32(ebp - 4)).decode("latin-1"), "idx": s32(ebp + 8)})

    def on_tag(tag):
        def f():
            emit(tag, {"S": S()})
        return f

    def on_csx():
        emit("CSX", {"it": reg("eax"), "S": S(), "gs": gs()})

    def on_cf0():
        esp = reg("esp")
        g = u32(esp + 4)
        st["game"] = g
        emit("CF0", {"ret": u32(esp), "idx": sreg("edx"), "kind": s32(esp + 8), "q": s32(esp + 12),
                     "nosock": s32(esp + 16), "noeth": s32(esp + 20), "ilvl": s32(esp + 24), "gs": gs(g)})

    def on_cfx():
        it = reg("eax")
        d = {"it": it, "gs": gs()}
        if it:
            idata = u32(it + 0x14)
            d.update(cls=s32(it + 4), q=u32(idata), start=u32(idata + 0x10), seed=sd(idata + 4),
                     fl=u32(idata + 0x18))
        emit("CFX", d)

    def on_bsx():
        emit("BSX", {"S": S(), "gs": gs()})

    def on_gb0():
        esp = reg("esp")
        g, npc = reg("ecx"), reg("edx")
        st["game"] = g
        emit("GB0", dict({"cls": s32(npc + 4), "player": u32(esp + 4), "S": S(g), "gs": gs(g)}, **ginfo(g)))
        if not st["vgl"]:
            st["vgl"] = True
            n = s32(G_GAMBLE)
            items = list(struct.unpack("<%di" % n, mem(u32(G_GAMBLE + 4), 4 * n))) if 0 < n <= 1024 else []
            emit("VGL", {"n": n, "items": items, "cnt": list(struct.unpack("<100i", mem(G_GAMBLE + 8, 400)))})

    def on_gcl():
        ebp = reg("ebp")
        dl = u32(ebp - 0x18)
        emit("GCL", {"clvl": sreg("eax"), "dl": list(struct.unpack("<5i", mem(dl + 0x44, 20))), "S": S()})

    def on_glv():
        emit("GLV", {"lvl": sreg("eax"), "S": S()})

    def on_gpk():
        ebp = reg("ebp")
        lvl = s32(ebp + 8)
        emit("GPK", {"r": reg("edx"), "idx": sreg("ebx"), "lvl": lvl,
                     "cnt": s32(G_GAMBLE + 8 + 4 * lvl) if 0 <= lvl < 100 else None, "S": S()})

    def on_gu(k, b):
        def f():
            emit("GU", {"k": k, "r": sreg("eax"), "bound": sreg(b), "S": S()})
        return f

    def on_gup():
        emit("GUP", {"idx": sreg("eax")})

    def on_gq():
        emit("GQ", {"q": sreg("eax"), "r": sreg("ecx"), "S": S()})

    def on_gbx():
        emit("GBX", {"S": S(), "gs": gs()})

    def on_plr():
        now = time.time()
        if now - st["t"] < 0.5 or not st["game"]:
            return
        st["t"] = now
        g = st["game"]
        out = []
        heads = struct.unpack("<128I", mem(g + 0x1320, 512))
        for u in heads:
            k = 0
            while u and k < 256:
                k += 1
                try:
                    cls = s32(u + 4)
                    p = u32(u + 0x2C)
                    if cls in NPC_CLASSES and p:
                        out.append([cls, u32(u + 0xC), u32(u + 0x10), u16(p + 2), u16(p + 6)])
                except gdb.MemoryError:
                    pass
                u = u32(u + 0xE4)
        emit("NPC", {"n": out})
        heads = struct.unpack("<128I", mem(g + 0x1520, 512))         # objects: the town waypoint (OBJP), all (OBJS)
        objs = []
        for u in heads:
            k = 0
            while u and k < 512:
                k += 1
                try:
                    cls = s32(u + 4)
                    sp = u32(u + 0x2C)
                    if sp:
                        objs.append([cls, s32(sp + 0x0C), s32(sp + 0x10)])
                    if cls in WP_CLASSES:
                        room = u32(sp) if sp else 0
                        lid = u32(u32(u32(room + 0x10) + 0x58) + 0x1D0) if room and u32(room + 0x10) else None
                        if (cls, lid) not in st.setdefault("wps", set()):
                            st["wps"].add((cls, lid))
                            emit("OBJP", {"unit": u, "cls": cls, "x": s32(sp + 0x0C), "y": s32(sp + 0x10),
                                          "mode": u32(u + 0x10), "lid": lid})
                except gdb.MemoryError:
                    pass
                u = u32(u + 0xE4)
        if now - st.get("tobj", 0) >= 2.0:
            st["tobj"] = now
            emit("OBJS", {"o": objs})
        gdb.flush()

    Bp(0x0052C312, on_game)
    Bp(0x005360D2, on_vsc0)
    Bp(0x00536100, on_vsc1)
    Bp(0x00579D60, on_ma)
    Bp(0x00579430, on_to)
    Bp(0x00537230, on_stale)
    Bp(0x00537402, on_stalex)
    Bp(0x005375FC, on_stalex)
    Bp(0x00536D10, on_reset)
    Bp(0x00536B50, on_regs("PLEAVE"))
    Bp(0x00537190, on_regs("GFREE"))
    Bp(0x00555500, on_regs("PIEND"))
    Bp(0x00576980, on_bs0)
    Bp(0x005769DE, on_bsl)
    Bp(0x00576A41, on_vd("cnt"))
    Bp(0x00576A80, on_vd("nq"))
    Bp(0x00576B02, on_vd("mx"))
    Bp(0x00576B1E, on_vd("mc"))
    Bp(0x00576330, on_cs0)
    Bp(0x005763AA, on_csu)
    Bp(0x0057641A, on_csu)
    Bp(0x005764A8, on_csw)
    Bp(0x00576505, on_tag("CRK"))
    Bp(0x00576536, on_tag("CMM"))
    for a in (0x00576A9B, 0x00576B41, 0x00576B9E):
        Bp(a, on_csx)
    Bp(0x00559CE0, on_cf0)
    Bp(0x005764DB, on_cfx)
    Bp(0x005789FE, on_cfx)
    for a in (0x00578BD0, 0x005794C7, 0x0057911B):
        Bp(a, on_bsx)
    def on_hb0():
        st["hire"] = True
        emit("HB0", {"S": S()})

    def on_hbx():
        if st.get("hire"):           # 0x00578C04 is also the join of NPC_OpenStore's no-hireling branches
            st["hire"] = False
            emit("HBX", {"S": S()})

    Bp(0x00576070, on_hb0)
    for a in (0x005767F0, 0x005770CE, 0x00578C04):
        Bp(a, on_hbx)
    Bp(0x00578790, on_gb0)
    Bp(0x00578861, on_gcl)
    Bp(0x005788B2, on_glv)
    Bp(0x00578919, on_gpk)
    Bp(0x00578727, on_gu("uber", "esi"))
    Bp(0x0057877B, on_gu("ultra", "edi"))
    Bp(0x0057896F, on_gup)
    Bp(0x005789DD, on_gq)
    Bp(0x00578B24, on_gbx)
    def on_tick():
        now = time.time()
        if now - st.get("tick", 0) >= 0.5:
            st["tick"] = now
            gdb.write("TICK\n")
            gdb.flush()

    Bp(0x0064EA90, on_plr)
    Bp(0x005380D0, on_tick)
    gdb.write("VENDORS logger armed\n")


_vendors_main()
