# gdb Python logger for plan 0018 Phase 2 (special monsters: mod picks, handlers, minion transfer, superuniques,
# MonPlace presets 2 and 3, the client name roll). Sourced by tools/gdb/mon-special.gdb after drlg-gen.py,
# drlg-roomk.py, mon-spawn.py and collision.py, whose tags it leaves unchanged. One line per event, "TAG {json}".
# Addresses refer to the pinned game.exe (image base 0x400000). "us" is a unit seed (+0x20), "rs" the seed (+0x6C) of
# the unit's own room (unit +0x2C path, +0x1C room), "gs" the game seed (+0xD0) of the last game seen. See
# docs/findings/monsters/0003-special-monsters.md.
#
# Mod picks:
#   MTI  0x005A0419 after each MonTypeIsA call in ModEligible: class, type t (word [esi]), result
#   MPK  after the draw: ChampionModPick 0x005A05C1 (k "c": x = EAX, total [ebp-4]) and UniqueModPick 0x005A070F
#        (k "u": x = EDX, total [ebp-8]); n candidates (ESI) with their rows and weights from the stack, unit seed
# Handlers (sub_005A2120_SpecialModsApply):
#   HD0/HDX  around the handler call 0x005A2153/0x005A2155 (mods 1..4) and 0x005A21AC/0x005A21AE (the list): mod
#            (ESI), unit (EDI), us, rs, gs; HDX only after an HD0 (the exit address is also a null handler's jump target)
#   TH0/TH1  around the group-walk thunk's call 0x005A2113/0x005A2115: member (ECX), mod (EDX), us, rs, gs
#   AUR  0x005A172C in UModAura after Range(local, n): unit, name seed (BX), n (ESI), level ([ebp+8]), r (EAX)
#   AUR2 0x005A1748: the index after the Lord De Seis override (EAX)
#   XF   0x005A0C94 after ModsXferCopy in UniqueMinions: minion (ESI) and its mods, boss (EDI) and its mods
# Superuniques (sub_005A49B0_SuperUniqueSpawn):
#   SU0  entry: game (ECX), room (EDX), x, y, id (stack), diff, exp, placed bit, rs, gs, room rect, level, region
#   SU1  0x005A4B88 before SpecialModsApply: unit, mods, min (ECX), max (EAX), us
#   SUT  0x005A4BE4 the tail switch: record +0x08 (EAX), us, rs, gs
#   SUX  0x0054E683 the return in PresetMonSpawn: unit (EAX) with mods, flags and name seed, us, rs, gs
# MonPlace presets (sub_0054E600_PresetMonSpawn):
#   PM0  case 2 0x0054E850 / case 3 0x0054E8A0: game, room, x, y, mode, rs, gs, diff, exp, room rect, level, region
#   PMC  after the class pick 0x0054E878 / 0x0054E8C8: class (EAX), record
#   PMX  0x0054E895 / 0x0054E90E / 0x0054EAB1 / 0x0054EAFE while a PM0 is open: EAX, rs, gs
# Harness helper (not a model input): PLR at COLL_PatternMark 0x0064EA90 with mask 0x80 (a player's mark): thread, room,
#   level, x, y, gf (the game frame, game +0xA8, of the last game seen; plan 0048 Phase 2 log volume); emitted when the position moved by 2 or more sub-tiles on that thread, and flushed at once so that
#   tools/d2pilot.py can steer the scripted Teleport from the live log.
# Client name (sub_004AC870_ClientMonNameBuild; the client thread):
#   CN0  0x004AC9C7 before RNG_SeedInit(unit +0x20, nameSeed): client unit, id, class, mod, name seed (EDX)
#   CNR  0x00653EE6 / 0x00653F26 / 0x00653F66: prefix / suffix / appellation index (EAX) of the unit seen at entry
#   CNH  0x004ACB2E: the Range(100) result
import json
import struct

import gdb


def _monspecial_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "pm": None, "su": None, "th": {}, "cn": {}, "hd": {}}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def s16(a):
        return struct.unpack("<h", mem(a, 2))[0]

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

    def uroom(u):
        p = u32(u + 0x2C) if u else 0
        return u32(p + 0x1C) if p else 0

    def us(u):
        return sd(u + 0x20) if u else None

    def rs_of(room):
        return sd(room + 0x6C) if room else None

    def gs():
        return sd(st["game"] + 0xD0) if st["game"] else None

    def seeds(u):
        return {"us": us(u), "rs": rs_of(uroom(u)), "gs": gs()}

    def mods(u):
        md = u32(u + 0x14) if u else 0
        return list(mem(md + 0x1C, 9)) if md else None

    def uinfo(u):
        if not u:
            return None
        md = u32(u + 0x14)
        d = {"u": u, "cls": s32(u + 4), "id": u32(u + 0xC), "us": us(u)}
        if s32(u) == 1 and md:
            d.update(mf=u16(md + 0x16), mods=list(mem(md + 0x1C, 9)), ns=u16(md + 0x14), su=s16(md + 0x26))
        return d

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def level_of(room):
        dr = u32(room + 0x10) if room else 0
        return s32(u32(dr + 0x58) + 0x1D0) if dr else None

    def region(game, lid):
        return u32(game + 0xF0 + 4 * lid) if (game and lid is not None and 0 <= lid < 256) else 0

    def rsnap(r):
        if not r:
            return None
        return {"r": r, "calls": s32(r + 4), "popd": s32(r + 8), "nrooms": s32(r + 0xC), "npool": u8(r + 0x10),
                "rsum": u8(r + 0x11), "ents": [[s16(r + 0x14 + 0x34 * i), u8(r + 0x16 + 0x34 * i)]
                                              for i in range(u8(r + 0x12))],
                "den": s32(r + 0x2B8), "umin": u8(r + 0x2BC), "umax": u8(r + 0x2BD), "wndr": u8(r + 0x2BE),
                "lid": s32(r + 0x2C0), "nwand": s32(r + 0x2C4), "nspec": s32(r + 0x2C8), "nmon": s32(r + 0x2CC)}

    def roomd(game, room):
        lid = level_of(room)
        return {"game": game, "room": room, "lid": lid, "rect": list(struct.unpack("<4i", mem(room + 0x4C, 16))),
                "rs": rs_of(room), "gs": sd(game + 0xD0), "diff": u8(game + 0x6D), "exp": u32(game + 0x70),
                "reg": rsnap(region(game, lid))}

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR %r\n" % (e,))
            return False

    # --- picks -------------------------------------------------------------------------------------------------
    def on_mti():
        u = reg("ebx")
        emit("MTI", {"cls": s32(u + 4) if u else None, "t": s16(reg("esi")), "r": 1 if reg("eax") else 0})

    def on_mpk(kind):
        def f():
            ebp, n = reg("ebp"), sreg("esi")
            if kind == "c":
                rows, x, total = ebp - 0x818, reg("eax"), s32(ebp - 4)
            else:
                rows, x, total = ebp - 0x81C, reg("edx"), s32(ebp - 8)
            c = [list(struct.unpack("<ii", mem(rows + 8 * i, 8))) for i in range(max(0, min(n, 256)))]
            emit("MPK", {"k": kind, "n": n, "total": total, "x": x, "c": c, "us": us(reg("ebx"))})
        return f

    Bp(0x005A0419, on_mti)
    Bp(0x005A05C1, on_mpk("c"))
    Bp(0x005A070F, on_mpk("u"))

    # --- handlers ----------------------------------------------------------------------------------------------
    def on_hd(tag):
        def f():
            t = thn()
            if tag == "HD0":
                st["hd"][t] = True
            elif not st["hd"].pop(t, False):
                return              # 0x005A2155 / 0x005A21AE are also the jump targets of a null handler
            u = reg("edi")
            d = {"m": reg("esi"), "u": u}
            d.update(seeds(u))
            emit(tag, d)
        return f

    for a in (0x005A2153, 0x005A21AC):
        Bp(a, on_hd("HD0"))
    for a in (0x005A2155, 0x005A21AE):
        Bp(a, on_hd("HDX"))

    def on_th0():
        u = reg("ecx")
        st["th"][thn()] = u
        d = {"u": u, "m": reg("edx")}
        d.update(seeds(u))
        emit("TH0", d)

    def on_th1():
        u = st["th"].pop(thn(), 0)
        d = {"u": u}
        d.update(seeds(u))
        emit("TH1", d)

    Bp(0x005A2113, on_th0)
    Bp(0x005A2115, on_th1)

    def on_aur():
        ebp = reg("ebp")
        emit("AUR", {"u": reg("edi"), "ns": reg("ebx") & 0xFFFF, "n": sreg("esi"), "lvl": s32(ebp + 8), "r": reg("eax")})

    def on_aur2():
        emit("AUR2", {"u": reg("edi"), "idx": sreg("eax")})

    Bp(0x005A172C, on_aur)
    Bp(0x005A1748, on_aur2)

    def on_xf():
        m, b = reg("esi"), reg("edi")
        emit("XF", {"m": m, "mods": mods(m), "b": b, "bmods": mods(b)})

    Bp(0x005A0C94, on_xf)

    # --- superuniques ------------------------------------------------------------------------------------------
    def on_su0():
        game, room, esp = reg("ecx"), reg("edx"), reg("esp")
        x, y, i = s32(esp + 4), s32(esp + 8), s32(esp + 0xC)
        st["game"] = game
        st["su"] = room
        d = {"x": x, "y": y, "id": i,
             "placed": 1 if (i >= 0 and u8(game + 0x1D30 + (i >> 3)) & (1 << (i & 7))) else 0}
        d.update(roomd(game, room))
        emit("SU0", d)

    def on_su1():
        u = reg("edi")
        emit("SU1", {"u": u, "mods": mods(u), "min": sreg("ecx"), "max": sreg("eax"), "us": us(u)})

    def on_sut():
        u = reg("edi")
        d = {"u": u, "idx": sreg("eax")}
        d.update(seeds(u))
        emit("SUT", d)

    def on_sux():
        u = reg("eax")
        room = st["su"]
        emit("SUX", {"u": uinfo(u), "rs": rs_of(room), "gs": gs()})
        st["su"] = None

    Bp(0x005A49B0, on_su0)
    Bp(0x005A4B88, on_su1)
    Bp(0x005A4BE4, on_sut)
    Bp(0x0054E683, on_sux)

    # --- MonPlace 2 and 3 --------------------------------------------------------------------------------------
    def on_pm0(case):
        def f():
            ebp = reg("ebp")
            game, room = u32(ebp - 4), reg("ebx")
            st["game"] = game
            st["pm"] = room
            d = {"case": case, "x": s32(ebp + 0xC), "y": s32(ebp + 0x10), "mode": s32(ebp + 0x14)}
            d.update(roomd(game, room))
            emit("PM0", d)
        return f

    def on_pmc(off):
        def f():
            emit("PMC", {"cls": sreg("eax"), "rec": u32(reg("ebp") + off)})
        return f

    def on_pmx():
        room = st["pm"]
        if room is None:
            return
        emit("PMX", {"eax": reg("eax"), "rs": rs_of(room), "gs": gs()})
        st["pm"] = None

    Bp(0x0054E850, on_pm0(2))
    Bp(0x0054E8A0, on_pm0(3))
    Bp(0x0054E878, on_pmc(0xC))
    Bp(0x0054E8C8, on_pmc(-8))
    for a in (0x0054E895, 0x0054E90E, 0x0054EAB1, 0x0054EAFE):
        Bp(a, on_pmx)

    # MonSpawnTry requests carry the game (keeps "gs" right outside a pass)
    def on_mt():
        st["game"] = u32(reg("ecx"))

    Bp(0x005B2A00, on_mt)

    # --- the client name roll ----------------------------------------------------------------------------------
    def on_cn0():
        u = reg("esi")
        emit("CN0", {"u": u, "id": u32(u + 0xC), "cls": s32(u + 4), "mod": s32(reg("ebp") - 4), "ns": reg("edx") & 0xFFFF})

    def on_cne():
        st["cn"][thn()] = reg("ecx")

    def on_cnr(k):
        def f():
            emit("CNR", {"k": k, "u": st["cn"].get(thn(), 0), "idx": sreg("eax")})
        return f

    def on_cnh():
        emit("CNH", {"u": reg("esi"), "r": sreg("eax")})

    Bp(0x004AC9C7, on_cn0)
    for a in (0x00653ED0, 0x00653F10, 0x00653F50):
        Bp(a, on_cne)
    Bp(0x00653EE6, on_cnr("P"))
    Bp(0x00653F26, on_cnr("S"))
    Bp(0x00653F66, on_cnr("A"))
    Bp(0x004ACB2E, on_cnh)
    plr = {}

    def on_plr():
        esp = reg("esp")
        room, x, y, _pat, mask = struct.unpack("<IiiII", mem(esp + 4, 20))
        if mask != 0x80:
            return
        t = thn()
        last = plr.get(t)
        if last and abs(last[0] - x) < 2 and abs(last[1] - y) < 2 and last[2] == room:
            return
        plr[t] = (x, y, room)
        emit("PLR", {"th": t, "room": room, "lid": level_of(room), "x": x, "y": y,
                     "gf": u32(st["game"] + 0xA8) if st["game"] else None})
        gdb.flush()

    Bp(0x0064EA90, on_plr)
    gdb.write("MONSPECIAL logger armed\n")


_monspecial_main()
