# gdb Python logger for plan 0030 Phase 2 (the Horadric Cube transmute): docs/findings/items/0008-cube.md.
# Sourced by tools/gdb/cube.gdb after tools/gdb/uniques.py and tools/gdb/props.py (ItemCreateByQuality, ItemInitStats,
# the builders, ItemApplyProps with its slots, ethereal, sockets, the final lists), whose lines it leaves unchanged.
# One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Seeds are
# "low:high" hex. Every line carries "th" (the gdb thread number). Events between CUB0 and CUBX belong to that
# transmute (thread-local); "gs" is the game seed (Game+0xD0) at the event.
#
#   CUB0  0x005665F0 CUBE_Transmute entry ([esp+4] game, ESI player): the game seed, Game +0x6A, +0x6D (difficulty),
#         +0x70 (expansion), +0x74 (ladder), +0x78 (item version); the player's class, its base stat entries (level
#         12 among them); every item of the player's inventory list (Unit+0x60 -> +0x0C, next ItemData+0x64) whose
#         page (ItemData+0x45) is 3, in list order, as UNIT
#   CMI   0x00566A6A the call of sub_005658C0_CubeMatchInputs: the row index ([ebp-4]); CMIR 0x00566A6F its result
#   CROW  0x00566A99 the call of sub_00565AB0_RecipeOutputCreate: row index, the 9 slot dwords at [ebp-0x50]
#         ({unit, classId, ilvl} for outputs A, B, C)
#   CPORT 0x00565D45 a special output's handler call (g_CubePortalFns): the output index ([ebp-0x8c]), the kind (output
#         +0x08), gs; CPORTR 0x00565D47 its result (EAX), gs
#   COWT  CUBE_CowPortalOpen's tests: q4_11 (0x00594159, the game's quest record), p4_10 (0x00594179), p26_0
#         (0x0059419E), p40_0 (0x005941C3) (the player's record of the difficulty), room (0x005941D1), level
#         (0x005941DD), spot (0x0059420C: found, x, y, gs), portal (0x0059422D: EAX, gs), ret (0x0059424A 1,
#         0x00594260 0); COW0 0x00594140 entry (gs)
#   PAN   0x00594270 / 0x00594280 the two Pandemonium handlers' entries (k 2 / 3)
#   CCP0  the ItemCopy calls 0x00565DA2 (mod), 0x00565E8C (useitem), 0x0056618E (rem children): source unit (EDX), the
#         children flag ([esp+4]), gs; CCPX after them: the copy as UNIT, gs
#   CPT0  the CubePickItemOfType calls 0x00565DFB (mod) / 0x00565FE0 (created): ilvl (EDX), type ([esp]), gs;
#         CPTX after: the class (AX), gs
#   CREC  0x005660C0 the ItemCreate call: the creation record at EDX (+0x0C ilvl, +0x14 index, +0x18, +0x28, +0x2A,
#         +0x30 quality, +0x40 row+1, +0x68 forced prefixes, +0x74 forced suffixes, +0x80 flags), the output index,
#         gs; CRECX 0x005660C5 the new item as UNIT, gs
#   CMOD  0x00660240 sub_00660240_CubeModApply entry from 0x00566274: the item, the line {prop, par, min, max,
#         chance}, the expansion argument, PDT once; the item as UNIT; CMODX at its return 0x00566279: the item as UNIT
#   SLOT / SLOTR / ROLL / ROLLR / WR / EVD  as tools/gdb/props.py, while a CMOD is open (the item seed is the CMOD
#         item's)
#   CSOCK 0x005663B6 the ITEMS_SetSockets call of an output `sock=N`: the count ([esp+4]), the item as UNIT
#   CDES  0x0056642C the destroy call (sub_00564F30_CubeDestroyContents), gs
#   CPL   0x00566481 a placement call (sub_00560200_InvPlaceItem): the output (ESI) as UNIT, gs; CPLR 0x00566486 EAX
#   ROCX  RecipeOutputCreate's returns 0x00566579 / 0x0056658E: gs
#   CUBX  CUBE_Transmute's returns 0x00566A8A / 0x00566AA3: gs, the page-3 items as UNIT
# UNIT = {"u", "type", "cls", "id", "mode", "useed" (Unit+0x20), "q", "seed" (ItemData+0x04), "start" (+0x10),
#        "fl" (+0x18), "fi" (+0x28), "ilvl" (+0x2C), "ver" (+0x30), "page" (+0x45), "p" (+0x38, 3 u16), "s" (+0x3E),
#        "rn" (+0x32, +0x34), "auto" (+0x36), "kids" [[unit, cls], ...], "b"/"sub" the stat lists as props.py}
import json
import struct

import gdb


def _cube_main():
    inf = gdb.selected_inferior()
    tx = {}        # thread -> {"game", "player"} while a transmute is open
    cm = {}        # thread -> item while a CubeModApply call is open
    pdt = {"done": False}
    DT_PTR = 0x00744304

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

    def emit(tag, d):
        d["th"] = thn()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def idata(it):
        return u32(it + 0x14)

    def entries(lst):
        arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 1024:
            return []
        return [[k >> 16, k & 0xFFFF, v] for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n))]

    def lists(it):
        lst = u32(it + 0x5C)
        if not lst:
            return {"b": None, "sub": []}
        sub = []
        if u32(lst + 0x10) & 0x80000000:
            for head in (0x3C, 0x40):
                node, guard = u32(lst + head), 0
                while node and guard < 64:
                    sub.append([u32(node + 0x14), u32(node + 0x10), entries(node)])
                    node, guard = u32(node + 0x2C), guard + 1
        return {"b": entries(lst), "sub": sub}

    def kids(it):
        inv = u32(it + 0x60)
        if not inv:
            return []
        out, c, guard = [], u32(inv + 0x0C), 0
        while c and guard < 16:
            out.append([c, s32(c + 4)])
            d = idata(c)
            c, guard = (u32(d + 0x64) if d else 0), guard + 1
        return out

    def unit(u):
        if not u:
            return None
        out = {"u": u, "type": u32(u), "cls": s32(u + 4), "id": u32(u + 0x0C), "mode": u32(u + 0x10),
               "useed": sd(u + 0x20)}
        d = idata(u)
        if out["type"] == 4 and d:
            out.update({"q": u32(d), "seed": sd(d + 4), "start": u32(d + 0x10), "fl": u32(d + 0x18),
                        "fi": s32(d + 0x28), "ilvl": s32(d + 0x2C), "ver": u16(d + 0x30), "page": u8(d + 0x45),
                        "p": list(struct.unpack("<3H", mem(d + 0x38, 6))),
                        "s": list(struct.unpack("<3H", mem(d + 0x3E, 6))),
                        "rn": [u16(d + 0x32), u16(d + 0x34)], "auto": u16(d + 0x36)})
            out["kids"] = kids(u)
            out.update(lists(u))
        return out

    def cube_items(player):
        inv = u32(player + 0x60)
        out = []
        if not inv:
            return out
        c, guard = u32(inv + 0x0C), 0
        while c and guard < 256:
            d = idata(c)
            if d and u8(d + 0x45) == 3:
                out.append(unit(c))
            c, guard = (u32(d + 0x64) if d else 0), guard + 1
        return out

    def cur():
        return tx.get(thn())

    def gs():
        c = cur()
        return sd(c["game"] + 0xD0) if c else None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR cube %r\n" % (e,))
            return False

    # ---- the transmute
    def on_cub0():
        game, player = u32(reg("esp") + 4), reg("esi")
        if not player:
            return
        tx[thn()] = {"game": game, "player": player}
        pl = lists(player)
        emit("CUB0", {"game": game, "player": player, "gs": sd(game + 0xD0), "g6a": u8(game + 0x6A),
                      "diff": u8(game + 0x6D), "exp": u32(game + 0x70), "ladder": u32(game + 0x74),
                      "iver": u16(game + 0x78), "pcls": s32(player + 4), "pb": pl["b"],
                      "items": cube_items(player)})

    def on_cubx():
        c = tx.pop(thn(), None)
        if not c:
            return
        emit("CUBX", {"gs": sd(c["game"] + 0xD0), "items": cube_items(c["player"])})

    def on_cmi():
        if cur():
            emit("CMI", {"row": s32(reg("ebp") - 4)})

    def on_cmir():
        if cur():
            emit("CMIR", {"r": sreg("eax")})

    def on_crow():
        if cur():
            ebp = reg("ebp")
            emit("CROW", {"row": s32(ebp - 4), "slots": list(struct.unpack("<9i", mem(ebp - 0x50, 36))),
                          "gs": gs()})

    def on_cport():
        if cur():
            ebp = reg("ebp")
            o = u32(ebp - 0x90)
            emit("CPORT", {"s": s32(ebp - 0x8C), "kind": u8(o + 8), "fn": reg("eax"), "gs": gs()})

    def on_cportr():
        if cur():
            emit("CPORTR", {"r": sreg("eax"), "gs": gs()})

    def on_cow0():
        if cur():
            emit("COW0", {"gs": gs()})

    def on_cowt(name, how):
        def f():
            if not cur():
                return
            if how == "eax":
                v = sreg("eax")
            elif how == "ebx":
                v = reg("ebx")
            elif how == "spot":
                ebp = reg("ebp")
                v = [s32(ebp - 4), s32(ebp - 0xC), s32(ebp - 8)]
            else:
                v = how
            emit("COWT", {"t": name, "v": v, "gs": gs()})
        return f

    def on_pan(k):
        def f():
            if cur():
                emit("PAN", {"k": k, "gs": gs()})
        return f

    def on_ccp0(where):
        def f():
            if cur():
                emit("CCP0", {"at": where, "src": reg("edx"), "kids": u32(reg("esp") + 4), "gs": gs()})
        return f

    def on_ccpx(where):
        def f():
            if cur():
                emit("CCPX", {"at": where, "it": unit(reg("eax")), "gs": gs()})
        return f

    def on_cpt0(where):
        def f():
            if cur():
                emit("CPT0", {"at": where, "ilvl": sreg("edx"), "type": s32(reg("esp")), "gs": gs()})
        return f

    def on_cptx(where):
        def f():
            if cur():
                emit("CPTX", {"at": where, "cls": reg("eax") & 0xFFFF, "gs": gs()})
        return f

    def on_crec():
        if not cur():
            return
        r = reg("edx")
        emit("CREC", {"s": s32(reg("ebp") - 0x8C), "src": u32(r), "ilvl": s32(r + 0x0C), "idx": s32(r + 0x14),
                      "k18": s32(r + 0x18), "w28": u16(r + 0x28), "ver": u16(r + 0x2A), "q": s32(r + 0x30),
                      "row1": s32(r + 0x40), "pre": list(struct.unpack("<3i", mem(r + 0x68, 12))),
                      "suf": list(struct.unpack("<3i", mem(r + 0x74, 12))), "rfl": u32(r + 0x80), "gs": gs()})

    def on_crecx():
        if cur():
            emit("CRECX", {"it": unit(reg("eax")), "gs": gs()})

    def on_cmod():
        c = cur()
        if not c or u32(reg("esp")) != 0x00566279:
            return
        esp = reg("esp")
        it, line = u32(esp + 4), u32(esp + 8)
        cm[thn()] = it
        dt = u32(DT_PTR)
        if not pdt["done"] and dt:
            pdt["done"] = True
            emit("PDT", {"c6c": u32(dt + 0xC6C), "c70": u32(dt + 0xC70)})
        emit("CMOD", {"line": [s32(line), s32(line + 4), s32(line + 8), s32(line + 0xC)], "exp": u32(esp + 0xC),
                      "it": unit(it), "gs": gs()})

    def on_cmodx():
        it = cm.pop(thn(), None)
        if it is None:
            return
        emit("CMODX", {"it": unit(it), "gs": gs()})

    def in_cm():
        return cm.get(thn()) is not None

    def iseed():
        return sd(idata(cm[thn()]) + 4)

    def on_slot():
        if not in_cm():
            return
        ebp, edi, esi = reg("ebp"), reg("edi"), reg("esi")
        dt = u32(DT_PTR)
        prow = (edi - u32(dt + 0xA4)) // 0x2E
        blk = u32(ebp + 0x20)
        b = list(struct.unpack("<iiii", mem(blk, 16))) if blk else None
        func = u8(edi + 0x18 + esi)
        out = {"k": esi, "prop": prow, "func": func, "set": u8(edi + 0x2 + esi), "stat": u16(edi + 0x20 + 2 * esi),
               "val": s16(edi + 0xA + 2 * esi), "prev": sreg("ebx"), "blk": b, "st": u32(ebp + 0x24),
               "fl": u32(ebp + 0x28), "seed": iseed()}
        if func in (11, 19) and b is not None and 0 <= b[1] < s32(dt + 0xBA0):
            sk = u32(dt + 0xB98) + 0x23C * b[1]
            out["req"] = s16(sk + 0x174)
            out["maxlvl"] = s16(sk + 0x12C)
        emit("SLOT", out)

    def on_slotr():
        if in_cm():
            emit("SLOTR", {"r": sreg("eax"), "seed": iseed()})

    def on_roll():
        if in_cm():
            emit("ROLL", {"min": sreg("edx"), "max": s32(reg("esp") + 4), "seed": iseed()})

    def on_rollr():
        if in_cm():
            emit("ROLLR", {"v": sreg("eax"), "seed": iseed()})

    def on_wr():
        if not in_cm():
            return
        esp = reg("esp")
        emit("WR", {"stat": s16(esp + 0x10), "param": s32(esp + 0x14), "v": s32(esp + 0x18), "set": s32(esp + 0xC),
                    "st": u32(esp + 0x1C), "fl": reg("edx")})

    def on_evd():
        if in_cm():
            emit("EVD", {"at": "f13", "v": sreg("eax")})

    def on_csock():
        if cur():
            esp = reg("esp")
            emit("CSOCK", {"n": s32(esp + 4), "it": unit(u32(esp)), "gs": gs()})

    def on_cdes():
        if cur():
            emit("CDES", {"gs": gs()})

    def on_cpl():
        if cur():
            emit("CPL", {"it": unit(reg("esi")), "gs": gs()})

    def on_cplr():
        if cur():
            emit("CPLR", {"r": sreg("eax"), "gs": gs()})

    def on_rocx():
        if cur():
            emit("ROCX", {"gs": gs()})

    Bp(0x005665F0, on_cub0)
    for a in (0x00566A8A, 0x00566AA3):
        Bp(a, on_cubx)
    Bp(0x00566A6A, on_cmi)
    Bp(0x00566A6F, on_cmir)
    Bp(0x00566A99, on_crow)
    Bp(0x00565D45, on_cport)
    Bp(0x00565D47, on_cportr)
    Bp(0x00594140, on_cow0)
    for a, name, how in ((0x00594159, "q4_11", "eax"), (0x00594179, "p4_10", "eax"), (0x0059419E, "p26_0", "eax"),
                         (0x005941C3, "p40_0", "eax"), (0x005941D1, "room", "ebx"), (0x005941DD, "level", "eax"),
                         (0x0059420C, "spot", "spot"), (0x0059422D, "portal", "eax"), (0x0059424A, "ret", 1),
                         (0x00594260, "ret", 0)):
        Bp(a, on_cowt(name, how))
    Bp(0x00594270, on_pan(2))
    Bp(0x00594280, on_pan(3))
    for a, w in ((0x00565DA2, "mod"), (0x00565E8C, "useitem"), (0x0056618E, "rem")):
        Bp(a, on_ccp0(w))
        Bp(a + 5, on_ccpx(w))
    for a, w in ((0x00565DFB, "mod"), (0x00565FE0, "created")):
        Bp(a, on_cpt0(w))
        Bp(a + 5, on_cptx(w))
    Bp(0x005660C0, on_crec)
    Bp(0x005660C5, on_crecx)
    Bp(0x00660240, on_cmod)
    Bp(0x00566279, on_cmodx)
    Bp(0x0065FDF5, on_slot)
    Bp(0x0065FDF7, on_slotr)
    Bp(0x0065E9E0, on_roll)
    for a in (0x0065E9F3, 0x0065EA24, 0x0065EA3F):
        Bp(a, on_rollr)
    Bp(0x0065EA50, on_wr)
    Bp(0x0065FCF4, on_evd)
    Bp(0x005663B6, on_csock)
    Bp(0x0056642C, on_cdes)
    Bp(0x00566481, on_cpl)
    Bp(0x00566486, on_cplr)
    for a in (0x00566579, 0x0056658E):
        Bp(a, on_rocx)
    gdb.write("CUBE logger armed\n")


_cube_main()
