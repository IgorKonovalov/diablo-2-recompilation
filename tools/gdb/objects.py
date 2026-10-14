# gdb Python logger for plan 0023 Phase 2 (object population, placement, creation rolls and the chest operate path,
# docs/findings/objects/0001-object-population.md). Sourced by tools/gdb/objects.gdb after the loggers of
# tools/gdb/mon-special.gdb, whose tags it leaves unchanged (mon-spawn.py's RW lines carry "os" since this plan).
# One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Seeds are "lo:hi":
# "rs" the active-room seed (+0x6C) of the room the code works on, "os" the object-region seed (*(game +0x10F0) +0x00),
# "gs" the game seed (+0xD0), "us" a unit seed (+0x20).
#
# Object region:
#   OGC  0x00546CE4 OBJRGN_Create after RNG_SeedInit(objrgn, low): game, region, os, gs. Arms the watchpoint below.
#   OD   hardware write watchpoint on the region seed's low dword: pc (the instruction after the write), lo. One line
#        per object-region draw, wherever it is made.
# Populate pass (sub_00552610_RoomObjectsPopulate):
#   OG   0x00552660 after OBJ_PopulateGate: room, level, result, and the gate's inputs as the gate saw them:
#        f (0x0061A210 room-flag test), pop (RoomPopLevelId), pre (preset test 0x0061ABB0), town (0x0061AB00),
#        cnt (LevelRoomCount when first read), th (theme roll result); the level counters after the gate; rs, os, gs
#   OS   0x005526FF per slot: k, group g, r after the forced rule, the population level and its counters
#        (vis +0x04, cnt +0x08, hs +0x10, nsh +0x14, nwl +0x18) as read by the forced test
#   OK   0x0055275C the member-pick draw r2
#   OH0/OHX  0x005527EE / 0x005527F0 around the PopulateFn call: fn index, density, class, rs, os, gs / rs, os, gs
# Position tests (COLL_WHTest 0x0064D800 at its seven call sites in the object code):
#   OT   site, room, x, y, w, h, mask, result (ax)
# Unit creation:
#   OPU0/OPUX  PresetUnitDispatch 0x005557D0 entry / its two rets: type, id, x, y, mode, room, rs, os, gs / eax, seeds
#   OU0/OUX    SUnitCreate 0x00555230 entry / exits (0x005554DD, 0x005554A8, 0x00555278, 0x0055529C), for type 2
#              always and for any type inside an object scope (handler, InitFn, operate): type, class, x, y, flags, mode,
#              room, rs, os, gs / unit, id, us, mode, interact (ObjectData +4), sparkle (+0x78), flags +0xC4, seeds
#   OI0/OIX    OBJ_ServerInit's InitFn call 0x0054F6F9 / 0x0054F6FB: fn, unit, class, x, y, rs, os, gs / interact,
#              sparkle, mode, us, rs, os, gs
#   OGP0/OGPX  InitFn 28's gold drop 0x0054F9B0 / 0x0054F9B5 (seed oracle): x, y, us, os, gs
# Operate:
#   OO0/OOX    OBJ_OperateDispatch's OperateFn call 0x0058450E / 0x00584510: unit, class, fn, mode, interact, sparkle,
#              player, us, os, gs / eax and the same fields after
#   OC0        ObjectChestDrop entry 0x00585B90: forced quality (EDX), unit, us, os, gs
#   OCT        0x00585CD2 the TC_ResolveDrops call: tc index ((tc - *0x0096C5EC) / 0x2C), tier (EDI), quality and the
#              fourth argument from the stack, us, os, gs
#   OCX        0x00585CD7 / 0x00585BF9 after it: first item, its quality (ItemData +0x00), us, os, gs
import json
import struct

import gdb


def _objects_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "rgn": 0, "watch": None}
    scope = {}              # thread -> depth of open object scopes (handler, InitFn, operate)
    opu = {}                # thread -> stack of open PresetUnitDispatch esp values
    ouc = {}                # thread -> stack of open SUnitCreate frames (ebp-to-be)
    flags = {}              # (thread, key) -> payload for paired lines
    POPFN = 0x00731D00

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8)) if p else None

    def rs(room):
        return sd(room + 0x6C) if room else None

    def gs(game=None):
        g = game or st["game"]
        return sd(g + 0xD0) if g else None

    def os_(game=None):
        g = game or st["game"]
        r = u32(g + 0x10F0) if g else 0
        return sd(r) if r else None

    def us(u):
        return sd(u + 0x20) if u else None

    def seeds(room, game=None):
        return {"rs": rs(room), "os": os_(game), "gs": gs(game)}

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def level_of(room):
        dr = u32(room + 0x10) if room else 0
        return s32(u32(dr + 0x58) + 0x1D0) if dr else None

    def lvl_counters(L):
        if not L:
            return None
        return {"vis": s32(L + 4), "cnt": s32(L + 8), "u0c": s32(L + 0xC), "hs": s32(L + 0x10), "nsh": s32(L + 0x14),
                "nwl": s32(L + 0x18)}

    def uroom(u):
        p = u32(u + 0x2C) if u else 0
        return u32(p + 0x1C) if p else 0

    def objinfo(u):
        if not u:
            return {"u": 0}
        od = u32(u + 0x14)
        return {"u": u, "type": s32(u), "cls": s32(u + 4), "id": u32(u + 0xC), "mode": s32(u + 0x10), "us": us(u),
                "it": u8(od + 4) if (od and s32(u) == 2) else None, "sp": u8(u + 0x78) if s32(u) == 2 else None,
                "uf": u32(u + 0xC4)}

    def push_scope():
        t = thn()
        scope[t] = scope.get(t, 0) + 1

    def pop_scope():
        t = thn()
        scope[t] = max(0, scope.get(t, 0) - 1)

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR objects %r\n" % (e,))
            return False

    class Watch(gdb.Breakpoint):
        def __init__(self, addr):
            super().__init__("*(unsigned int *)0x%08X" % addr, gdb.BP_WATCHPOINT, gdb.WP_WRITE, internal=True)
            self.silent = True
            self.addr = addr

        def stop(self):
            try:
                emit("OD", {"pc": reg("pc"), "lo": "%08x" % u32(self.addr)})
            except Exception as e:
                gdb.write("LOGERR objects watch %r\n" % (e,))
            return False

    # --- the object region ----------------------------------------------------------------------------------
    def on_ogc():
        game, rgn = reg("esi"), reg("edi")
        st["game"], st["rgn"] = game, rgn
        if st["watch"] is not None:
            try:
                st["watch"].delete()
            except Exception:
                pass
            st["watch"] = None
        try:
            st["watch"] = Watch(rgn)
            armed = True
        except Exception as e:
            gdb.write("LOGERR objects watch arm %r\n" % (e,))
            armed = False
        emit("OGC", {"game": game, "rgn": rgn, "os": sd(rgn), "gs": gs(game), "watch": armed})

    Bp(0x00546CE4, on_ogc)

    # --- the populate pass ----------------------------------------------------------------------------------
    def gate_set(k, regname="eax"):
        def f():
            flags.setdefault((thn(), "gate"), {})[k] = sreg(regname)
        return f

    def on_gate_entry():
        flags[(thn(), "gate")] = {}

    Bp(0x00552560, on_gate_entry)
    Bp(0x00552569, gate_set("f"))
    Bp(0x0055257E, gate_set("pop"))
    Bp(0x00552593, gate_set("pre"))
    Bp(0x005525AA, gate_set("town"))
    Bp(0x005525CB, gate_set("cnt"))
    Bp(0x005525EC, gate_set("th"))

    def on_og():
        ebp = reg("ebp")
        game, room = u32(ebp - 0x18), u32(ebp - 0x14)
        st["game"] = game
        g = flags.pop((thn(), "gate"), {})
        d = {"room": room, "lid": level_of(room), "res": reg("eax"), "rect": list(struct.unpack("<4i", mem(room + 0x4C, 16)))}
        d.update(g)
        pop = g.get("pop")
        rgn = u32(game + 0x10F0)
        if pop and rgn and 0 < pop < 0x400:
            d["L"] = lvl_counters(u32(rgn + 0x48 + 4 * pop))
        d.update(seeds(room, game))
        emit("OG", d)

    Bp(0x00552660, on_og)

    def on_os_pop():
        flags[(thn(), "spop")] = reg("edx")

    def on_os_l():
        flags[(thn(), "sl")] = lvl_counters(reg("eax"))

    def on_os():
        ebp = reg("ebp")
        t = thn()
        emit("OS", {"k": s32(ebp - 4), "g": reg("edi"), "r": s32(ebp - 0xC), "pop": flags.get((t, "spop")),
                    "L": flags.get((t, "sl"))})

    Bp(0x005526C7, on_os_pop)
    Bp(0x005526CC, on_os_l)
    Bp(0x005526FF, on_os)

    def on_ok():
        emit("OK", {"r2": sreg("ecx")})

    Bp(0x0055275C, on_ok)

    def on_oh0():
        ebp = reg("ebp")
        game, room = reg("ecx"), reg("edx")
        fp = reg("eax")
        fn = None
        for i in range(10):
            if u32(POPFN + 4 * i) == fp:
                fn = i
                break
        flags[(thn(), "oh")] = room
        push_scope()
        d = {"fn": fn, "room": room, "den": reg("ebx"), "cls": reg("edi"), "k": s32(ebp - 4)}
        d.update(seeds(room, game))
        emit("OH0", d)

    def on_ohx():
        room = flags.pop((thn(), "oh"), None)
        if room is None:
            return          # 0x005527F0 is also the jump target of the skip paths
        pop_scope()
        d = {"room": room, "eax": reg("eax")}
        d.update(seeds(room))
        emit("OHX", d)

    Bp(0x005527EE, on_oh0)
    Bp(0x005527F0, on_ohx)

    # --- position tests -------------------------------------------------------------------------------------
    def ot_before(site):
        def f():
            esp = reg("esp")
            flags[(thn(), "ot")] = (site,) + struct.unpack("<IiiiiI", mem(esp, 24))
        return f

    def ot_after():
        v = flags.pop((thn(), "ot"), None)
        if v is None:
            return
        site, room, x, y, w, h, m = v
        emit("OT", {"site": site, "room": room, "x": x, "y": y, "w": w, "h": h, "m": m, "res": reg("eax") & 0xFFFF})

    for a in (0x0054F99D, 0x0055029E, 0x005502BA, 0x00550355, 0x005504B3, 0x0055062D, 0x00550B89):
        Bp(a, ot_before(a))
        Bp(a + 5, ot_after)

    # --- unit creation --------------------------------------------------------------------------------------
    def on_opu0():
        esp = reg("esp")
        typ, uid, x, y, mode = struct.unpack("<iiiii", mem(esp + 4, 20))
        game, room = reg("ecx"), reg("edx")
        st["game"] = game
        opu.setdefault(thn(), []).append((esp, room))
        d = {"type": typ, "id": uid, "x": x, "y": y, "mode": mode, "room": room}
        d.update(seeds(room, game))
        emit("OPU0", d)

    def on_opux():
        esp = reg("esp")
        stk = opu.get(thn(), [])
        if not stk or stk[-1][0] != esp:
            return
        _e, room = stk.pop()
        d = {"eax": reg("eax"), "o": objinfo(reg("eax")) if reg("eax") else None}
        d.update(seeds(room))
        emit("OPUX", d)

    Bp(0x005557D0, on_opu0)
    for a in (0x005558BE, 0x0055590C):
        Bp(a, on_opux)

    def on_ou0():
        typ = reg("ecx")
        t = thn()
        if typ != 2 and not scope.get(t):
            return
        esp = reg("esp")
        x, y, game, room, fl, mode = struct.unpack("<iiIIii", mem(esp + 4, 24))
        if game:
            st["game"] = game
        ouc.setdefault(t, []).append((esp - 4, room, game))
        d = {"type": typ, "cls": sreg("edx"), "x": x, "y": y, "fl": fl, "mode": mode, "room": room}
        d.update(seeds(room, game))
        emit("OU0", d)

    def on_oux():
        stk = ouc.get(thn(), [])
        ebp = reg("ebp")
        if not stk or stk[-1][0] != ebp:
            return
        _e, room, game = stk.pop()
        u = reg("esi") if reg("pc") in (0x005554DD, 0x005554A8) else 0
        d = {"o": objinfo(u)}
        d.update(seeds(room, game))
        emit("OUX", d)

    Bp(0x00555230, on_ou0)
    for a in (0x005554DD, 0x005554A8, 0x00555278, 0x0055529C):
        Bp(a, on_oux)

    def on_oi0():
        u = reg("esi")
        room = reg("ebx")
        ebp = reg("ebp")
        flags[(thn(), "oi")] = (u, room)
        push_scope()
        d = {"fn": reg("edx"), "u": u, "cls": s32(u + 4), "x": s32(ebp - 0xC), "y": s32(ebp - 8), "room": room,
             "us": us(u)}
        d.update(seeds(room))
        emit("OI0", d)

    def on_oix():
        v = flags.pop((thn(), "oi"), None)
        if v is None:
            return
        pop_scope()
        u, room = v
        d = {"o": objinfo(u)}
        d.update(seeds(room))
        emit("OIX", d)

    Bp(0x0054F6F9, on_oi0)
    Bp(0x0054F6FB, on_oix)

    def on_ogp0():
        ebp = reg("ebp")
        esi = reg("esi")
        u = u32(esi + 4)
        flags[(thn(), "ogp")] = u
        emit("OGP0", {"x": s32(ebp - 0x10), "y": s32(ebp - 0xC), "us": us(u), "os": os_(), "gs": gs()})

    def on_ogpx():
        u = flags.pop((thn(), "ogp"), None)
        if u is None:
            return
        emit("OGPX", {"us": us(u), "os": os_(), "gs": gs()})

    Bp(0x0054F9B0, on_ogp0)
    Bp(0x0054F9B5, on_ogpx)

    # --- operate --------------------------------------------------------------------------------------------
    def on_oo0():
        ebp = reg("ebp")
        game, u, pl = reg("ebx"), reg("esi"), reg("edi")
        st["game"] = game
        flags[(thn(), "oo")] = u
        push_scope()
        d = {"fn": reg("edx"), "cls": s32(ebp + 8), "player": pl, "room": uroom(u)}
        d.update(objinfo(u))
        d.update(seeds(uroom(u), game))
        emit("OO0", d)

    def on_oox():
        u = flags.pop((thn(), "oo"), None)
        if u is None:
            return
        pop_scope()
        d = {"eax": reg("eax")}
        d.update(objinfo(u))
        d.update(seeds(uroom(u)))
        emit("OOX", d)

    Bp(0x0058450E, on_oo0)
    Bp(0x00584510, on_oox)

    def on_oc0():
        ctx = reg("ecx")
        u = u32(ctx + 4)
        flags[(thn(), "oc")] = u
        emit("OC0", {"q": sreg("edx"), "u": u, "us": us(u), "os": os_(), "gs": gs()})

    def on_oct():
        u = flags.get((thn(), "oc"), 0)
        base = u32(0x0096C5EC)
        esp = reg("esp")
        tc, q, a4 = struct.unpack("<Iii", mem(esp + 4, 12))
        emit("OCT", {"tc": (tc - base) // 0x2C if tc >= base else None, "tier": sreg("edi"), "q": q, "a4": a4,
                     "us": us(u), "os": os_(), "gs": gs()})

    def on_ocx():
        u = flags.pop((thn(), "oc"), None)
        if u is None:
            return
        it = u32(reg("ebp") - 0x28) if reg("pc") == 0x00585CD7 else 0
        q = None
        if it:
            idata = u32(it + 0x14)
            q = s32(idata) if idata else None
        emit("OCX", {"item": it, "q": q, "us": us(u), "os": os_(), "gs": gs()})

    Bp(0x00585B90, on_oc0)
    Bp(0x00585CD2, on_oct)
    Bp(0x00585CD7, on_ocx)
    Bp(0x00585BF9, on_ocx)
    gdb.write("OBJECTS logger armed\n")


_objects_main()
