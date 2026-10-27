# gdb Python logger for plan 0038 batch H1b (run:2026-10-27-sweep-d2s-play): the save pieces the d2s-io logger
# (tools/gdb/d2s-io.py, sourced first) does not log. Sourced by tools/gdb/d2s-h1b.gdb / d2s-h1b-hire.gdb after
# d2s-io.py. Every name here starts with h1b_ so that it shares no global with the other loggers of the session.
# One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000); names are those of
# docs/findings/save/0001-d2s-io.md. Check with python3 -I tools/sweep_h1b.py check.
#
# Who saves:
#   PSV2  0x00532400 PLRSAVE_Save entry: ret, game type (game +0x6A), host callback (0x00883D50)
#   SVCB  0x00531EB0 sub_00531EB0_SaveViaCallback entry: ret;  SVCL 0x00532340 (the game-type 1/2 client-buffer
#         branch) entry: ret;  SHUT 0x0052E9C0 sub_0052E9C0_SaveAllOnShutdown entry: ret
#   AUTO  0x0052D350 sub_0052D350_AutosaveTick entry: the first call, then one line every 500 calls: calls so far,
#         host callback
#   JCH   entries of the join load chain: 0x00539760 ClientAddPlayerToGame, 0x005345A0 PlayerLoad, 0x005343A0
#         PLRSAVE_ReadFile, 0x00534330 D2S_ReadSave: fn, ret
# Sections:
#   WSEC  D2S_WriteSave (0x00569AD0) at each section-writer call site and after the last: sec, pass ("pre" for the
#         header..skills calls, "scratch" for the first item/corpse/merc/golem pass into [ebp-0x8004], "final" for the
#         second), off = cursor - output buffer ([ebp-0x8018]); the scratch pass gives its offset in the scratch buffer
#   RSEC  D2S_ReadSaveV92 (0x0056B180) at each reader call site: sec, off = cursor ([ebp-0x4]) - buffer (its [ebp+8]
#         at entry, logged by RBASE 0x0056B1B1)
#   MRX   0x0056B318 after D2S_ReadMercHeader: eax (the mercenary unit or 0), the header bytes 0xAF..0xBE;  M5726 the
#         0x005726C0 call (0x0056B343): its push 1
# Header:
#   HOTK  0x00568F5C (as WHDR): the client's 16 hotkey slots (+0x3DC + 8 i: s16 skill, u8 flag at +0x3DE, u32 item
#         at +0x3E0);  HREF 0x0056912E: slot (EBX) and the u16 item ref the writer stores (AX)
#   WSKL  the mouse-skill sources the writer reads: left 0x0056915B and right 0x00569191 (AX: the skill id of
#         0x00620190 / 0x006201D0's skill through 0x00643CE0), swap A 0x005691C2 and swap B 0x005691FB (the u16 that
#         0x00623220 / 0x00623290 wrote to [ebp-0x160])
#   GFX   0x00569283 after 0x0063E510 in D2S_WriteHeader: the 32 header bytes 0x88..0xA7 of the image ([ebp-0xCC])
#   MHW0  0x00568E60 D2S_WriteMercHeader entry: hdr ([esp+4]);  MHW1 0x00568EA9 after the hireling record lookup:
#         merc unit (EDI), mercenary info (EBX: 12 bytes hex), record (EAX) +0x114 / +0x116 (u16), merc base stats
#         12 and 13;  MHWD 0x00568EFC: the dead test (EAX), merc mode;  MHW2 0x00568F0A: hdr bytes 0xAF..0xBE
# LoadFinish:
#   LFG   0x0056AFC0 gold (EDI) and its maximum (EAX);  LFB 0x0056AFF5 goldbank (EDI) and its maximum (EAX);
#   LFS   0x0056B01A stamina maximum (EAX);  LFX0 0x0056B151 class, level pushed to 0x00611800;  LFX 0x0056B156 its
#         result (EAX);  LFE 0x0056B3C8 (as LFIN2): the unit's whole base stat list
# Items:
#   RIST  0x00558D28 (as RITEM): the item's base and full stat arrays, item data +0x38 (u16), flags
#   SBX   0x006312B0 (as SBIT, inside d2s-io's save window): the same for an item being serialised
#   RWW   0x00630887 ITEMS_WriteFull after 0x0062BED0: the Runes record (EAX), its +0x82 (u16), the item (EDI)
#   RWR   0x0062D1DA ITEMS_ReadFull after the 16-bit runeword read: EAX, the item (ESI)
# Item flag bit 13 (0x2000):
#   B13S  0x00558E9B sub_00558D90_ItemCreate, the set call (EDI item; create params +0x2C = 0 here)
#   B13C  0x00553357 sub_00553220_UnitFrameReset, the clear call (ESI unit), logged when the item has the bit: unit,
#         id, mode, flags, in_tick (inside GameTick's 0x0052D900 call of sub_0053B000_ActUnitsFrameReset, flag set at
#         0x0052D900 and cleared at 0x0052D905), ret (UnitFrameReset's return address, [ebp+4])
#   GOLD  0x00559482 sub_00559300_DropGoldPile's clear call;  COPY 0x0055A360 / 0x0055A438 sub_0055A2A0_ItemCopy's
#   SETF  0x006280D0 ITEMS_SetFlag entry with mask & 0x2000, when the call changes the bit: item, id, set, ret
#   WTCH  with H1B_WATCH=1 in the environment only: a hardware write watchpoint on the item-data flags of the first
#         CPOST item (WTCH0 when armed; at most 400 hits): pc, flags
import json
import os
import struct

import gdb

h1b_INF = gdb.selected_inferior()
h1b_WATCH = os.environ.get("H1B_WATCH") == "1"  # the watchpoint is armed only when the session asks for it
h1b_HOSTCB = 0x00883D50
h1b_ST = {"auto": 0, "rbase": None, "tick": 0, "watch": None, "whits": 0, "watched": None}


def h1b_mem(a, n):
    return bytes(h1b_INF.read_memory(a, n))


def h1b_u8(a):
    return h1b_mem(a, 1)[0]


def h1b_u16(a):
    return struct.unpack("<H", h1b_mem(a, 2))[0]


def h1b_s16(a):
    return struct.unpack("<h", h1b_mem(a, 2))[0]


def h1b_u32(a):
    return struct.unpack("<I", h1b_mem(a, 4))[0]


def h1b_reg(r):
    return int(gdb.parse_and_eval("$" + r)) & 0xFFFFFFFF


def h1b_emit(tag, d):
    gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))


def h1b_stats(unit):
    """The unit's base stat array (unit +0x5C list, +0x24 array, +0x28 count): [[id, param, value], ...]."""
    lst = h1b_u32(unit + 0x5C)
    if not lst:
        return None
    arr, n = h1b_u32(lst + 0x24), h1b_s16(lst + 0x28)
    if not arr or n <= 0 or n > 1024:
        return []
    return [[k >> 16, k & 0xFFFF, v] for k, v in struct.iter_unpack("<Ii", h1b_mem(arr, 8 * n))]


def h1b_full(unit):
    """The unit's full stat array (stat list +0x48 array, +0x4C count, kept when list +0x10 bit 31 is set): the
    item's own property lists folded together; None when the list keeps none."""
    lst = h1b_u32(unit + 0x5C)
    if not lst or not h1b_u32(lst + 0x10) & 0x80000000:
        return None
    arr, n = h1b_u32(lst + 0x48), h1b_s16(lst + 0x4C)
    if not arr or n <= 0 or n > 1024:
        return []
    return [[k >> 16, k & 0xFFFF, v] for k, v in struct.iter_unpack("<Ii", h1b_mem(arr, 8 * n))]


def h1b_item(it):
    d = {"unit": it, "id": h1b_u32(it + 0x0C), "cls": h1b_u32(it + 4), "mode": h1b_u32(it + 0x10)}
    idt = h1b_u32(it + 0x14)
    if idt:
        d.update(flags=h1b_u32(idt + 0x18), rw38=h1b_u16(idt + 0x38))
    return d


# --- who saves -------------------------------------------------------------------------------------------------

def h1b_psv2():
    g = h1b_reg("ecx")
    h1b_emit("PSV2", {"ret": h1b_u32(h1b_reg("esp")), "gtype": h1b_u8(g + 0x6A) if g else None,
                      "hostcb": h1b_u32(h1b_HOSTCB)})


def h1b_ret(tag):
    def f():
        h1b_emit(tag, {"ret": h1b_u32(h1b_reg("esp")), "hostcb": h1b_u32(h1b_HOSTCB)})
    f.__name__ = "h1b_" + tag
    return f


def h1b_auto():
    h1b_ST["auto"] += 1
    n = h1b_ST["auto"]
    if n == 1 or n % 500 == 0:
        h1b_emit("AUTO", {"calls": n, "ret": h1b_u32(h1b_reg("esp")), "hostcb": h1b_u32(h1b_HOSTCB)})


def h1b_jch(name):
    def f():
        h1b_emit("JCH", {"fn": name, "ret": h1b_u32(h1b_reg("esp"))})
    f.__name__ = "h1b_jch_" + name
    return f


# --- sections --------------------------------------------------------------------------------------------------

def h1b_wsec(sec, pas):
    def f():
        ebp = h1b_reg("ebp")
        base = h1b_u32(ebp - 0x8018)
        if pas == "scratch":
            cur = h1b_u32(ebp - 0x800C)
            off = cur - (ebp - 0x8004)
        else:
            cur = h1b_u32(ebp - 0x8008)
            off = cur - base
        h1b_emit("WSEC", {"sec": sec, "pass": pas, "off": off})
    f.__name__ = "h1b_wsec_" + sec + "_" + pas
    return f


def h1b_rbase():
    h1b_ST["rbase"] = h1b_u32(h1b_reg("ebp") + 8)


def h1b_rsec(sec):
    def f():
        ebp = h1b_reg("ebp")
        b = h1b_ST["rbase"]
        h1b_emit("RSEC", {"sec": sec, "off": (h1b_u32(ebp - 4) - b) if b is not None else None})
    f.__name__ = "h1b_rsec_" + sec
    return f


def h1b_mrx():
    b = h1b_ST["rbase"]
    h1b_emit("MRX", {"eax": h1b_reg("eax"), "hdr": h1b_mem(b + 0xAF, 16).hex() if b is not None else None})


def h1b_m5726():
    h1b_emit("M5726", {"arg": h1b_u32(h1b_reg("esp")), "unit": h1b_reg("edx")})


# --- header ----------------------------------------------------------------------------------------------------

def h1b_hotk():
    c = h1b_reg("eax")
    h1b_emit("HOTK", {"slots": [[h1b_s16(c + 0x3DC + 8 * i), h1b_u8(c + 0x3DE + 8 * i), h1b_u32(c + 0x3E0 + 8 * i)]
                                for i in range(16)]})


def h1b_href():
    h1b_emit("HREF", {"slot": h1b_reg("ebx"), "ref": h1b_reg("eax") & 0xFFFF})


def h1b_wskl(slot, src):
    def f():
        if src == "ax":
            v = h1b_reg("eax") & 0xFFFF
        else:
            v = h1b_u32(h1b_reg("ebp") - 0x160) & 0xFFFF
        h1b_emit("WSKL", {"slot": slot, "skill": v})
    f.__name__ = "h1b_wskl_" + slot
    return f


def h1b_gfx():
    h1b_emit("GFX", {"bytes": h1b_mem(h1b_reg("ebp") - 0xCC, 32).hex()})


def h1b_mhw0():
    h1b_ST["mhdr"] = h1b_u32(h1b_reg("esp") + 4)
    h1b_emit("MHW0", {"hdr": h1b_ST["mhdr"], "unit": h1b_reg("edx")})


def h1b_mhw1():
    merc, info, rec = h1b_reg("edi"), h1b_reg("ebx"), h1b_reg("eax")
    st = h1b_stats(merc) or []
    h1b_emit("MHW1", {"merc": merc, "mcls": h1b_u32(merc + 4), "info": h1b_mem(info, 12).hex(),
                      "r114": h1b_u16(rec + 0x114), "r116": h1b_u16(rec + 0x116),
                      "s12": next((v for i, p, v in st if i == 12 and p == 0), None),
                      "s13": next((v for i, p, v in st if i == 13 and p == 0), None)})


def h1b_mhwd():
    h1b_emit("MHWD", {"dead": h1b_reg("eax"), "mode": h1b_u32(h1b_reg("edi") + 0x10)})


def h1b_mhw2():
    h = h1b_ST.get("mhdr")
    h1b_emit("MHW2", {"hdr": h1b_mem(h + 0xAF, 16).hex() if h else None})


# --- LoadFinish ------------------------------------------------------------------------------------------------

def h1b_lfg():
    h1b_emit("LFG", {"gold": h1b_reg("edi"), "max": h1b_reg("eax")})


def h1b_lfb():
    h1b_emit("LFB", {"bank": h1b_reg("edi"), "max": h1b_reg("eax")})


def h1b_lfs():
    h1b_emit("LFS", {"max": h1b_reg("eax")})


def h1b_lfx0():
    esp = h1b_reg("esp")
    h1b_emit("LFX0", {"cls": h1b_u32(esp), "level": h1b_u32(esp + 4)})


def h1b_lfx():
    h1b_emit("LFX", {"exp": h1b_reg("eax")})


def h1b_lfe():
    h1b_emit("LFE", {"stats": h1b_stats(h1b_reg("edi"))})


# --- items -----------------------------------------------------------------------------------------------------

def h1b_rist():
    it = h1b_reg("esi")
    d = h1b_item(it)
    d["stats"] = h1b_stats(it)
    d["full"] = h1b_full(it)
    h1b_emit("RIST", d)


def h1b_sbx():
    import __main__
    if not __main__.STATE.get("insave"):
        return
    it = h1b_reg("ecx")
    d = h1b_item(it)
    d["stats"] = h1b_stats(it)
    d["full"] = h1b_full(it)
    h1b_emit("SBX", d)


def h1b_rww():
    rec = h1b_reg("eax")
    h1b_emit("RWW", {"rec": rec, "r82": h1b_u16(rec + 0x82) if rec else None, "item": h1b_reg("edi")})


def h1b_rwr():
    h1b_emit("RWR", {"eax": h1b_reg("eax"), "item": h1b_reg("esi")})


# --- item flag bit 13 ------------------------------------------------------------------------------------------

def h1b_b13s():
    it = h1b_reg("edi")
    d = h1b_item(it)
    d["p2c"] = h1b_u32(h1b_reg("esi") + 0x2C)
    h1b_emit("B13S", d)


def h1b_b13c():
    u = h1b_reg("esi")
    if h1b_u32(u) != 4:
        return
    d = h1b_item(u)
    if not d.get("flags", 0) & 0x2000:
        return
    d.update(in_tick=h1b_ST["tick"], ret=h1b_u32(h1b_reg("ebp") + 4))
    h1b_emit("B13C", d)


def h1b_flag(key, v):
    def f():
        h1b_ST[key] = v
    f.__name__ = "h1b_%s_%d" % (key, v)
    return f


def h1b_site(tag, r):
    def f():
        u = h1b_reg(r)
        d = h1b_item(u) if u and h1b_u32(u) == 4 else {"unit": u}
        h1b_emit(tag, d)
    f.__name__ = "h1b_site_" + tag
    return f


def h1b_setf():
    esp = h1b_reg("esp")
    it, mask, st = h1b_u32(esp + 4), h1b_u32(esp + 8), h1b_u32(esp + 12)
    if not mask & 0x2000 or not it or h1b_u32(it) != 4:
        return
    idt = h1b_u32(it + 0x14)
    if not idt:
        return
    fl = h1b_u32(idt + 0x18)
    if bool(fl & 0x2000) == bool(st):
        return
    h1b_emit("SETF", {"item": it, "id": h1b_u32(it + 0x0C), "mode": h1b_u32(it + 0x10), "set": st, "mask": mask,
                      "flags": fl, "ret": h1b_u32(esp), "in_tick": h1b_ST["tick"]})


class h1b_Watch(gdb.Breakpoint):
    def __init__(self, addr, unit):
        super().__init__("*(unsigned int *)0x%08X" % addr, gdb.BP_WATCHPOINT, gdb.WP_WRITE, internal=True)
        self.silent = True
        self.addr, self.unit = addr, unit

    def stop(self):
        try:
            h1b_ST["whits"] += 1
            h1b_emit("WTCH", {"unit": self.unit, "pc": h1b_reg("eip"), "flags": h1b_u32(self.addr),
                              "in_tick": h1b_ST["tick"], "n": h1b_ST["whits"]})
            if h1b_ST["whits"] >= 400:
                h1b_emit("WTCHX", {"reason": "cap"})
                self.enabled = False
        except Exception as e:
            gdb.write("LOGERR h1b_watch %r\n" % (e,))
        return False


def h1b_cpost():
    it = h1b_reg("eax")
    if not h1b_WATCH or not it or h1b_ST["watched"] is not None:
        return
    idt = h1b_u32(it + 0x14)
    if not idt:
        return
    h1b_ST["watched"] = it
    try:
        h1b_ST["watch"] = h1b_Watch(idt + 0x18, it)
        h1b_emit("WTCH0", {"unit": it, "id": h1b_u32(it + 0x0C), "addr": idt + 0x18, "flags": h1b_u32(idt + 0x18)})
    except Exception as e:
        h1b_emit("WTCH0", {"unit": it, "error": repr(e)})


class h1b_Bp(gdb.Breakpoint):
    def __init__(self, addr, fn):
        super().__init__("*0x%08X" % addr, internal=True)
        self.silent = True
        self.fn = fn

    def stop(self):
        try:
            self.fn()
        except Exception as e:  # never stop the game on a logger error; log it instead
            gdb.write("LOGERR %s %r\n" % (self.fn.__name__, e))
        return False


h1b_WRITE_SITES = ((0x00569B38, "header", "pre"), (0x00569B51, "quests", "pre"), (0x00569B6A, "waypoints", "pre"),
                   (0x00569B83, "npcs", "pre"), (0x00569B9C, "stats", "pre"), (0x00569BB5, "skills", "pre"),
                   (0x00569BE9, "items", "scratch"), (0x00569C1F, "corpses", "scratch"),
                   (0x00569C46, "merc", "scratch"), (0x00569C68, "golem", "scratch"),
                   (0x00569CB7, "items", "final"), (0x00569CD5, "corpses", "final"), (0x00569CF4, "merc", "final"),
                   (0x00569D0E, "golem", "final"), (0x00569D17, "end", "final"))
h1b_READ_SITES = ((0x0056B1BB, "header"), (0x0056B20B, "quests"), (0x0056B22A, "waypoints"), (0x0056B249, "npcs"),
                  (0x0056B270, "stats"), (0x0056B2AF, "skills"), (0x0056B2D3, "items"), (0x0056B2F6, "corpses"),
                  (0x0056B313, "merc_header"), (0x0056B32D, "merc_items"), (0x0056B343, "merc_5726c0"),
                  (0x0056B358, "golem"), (0x0056B3C3, "loadfinish"))

for _a, _f in ((0x00532400, h1b_psv2), (0x00531EB0, h1b_ret("SVCB")), (0x00532340, h1b_ret("SVCL")),
               (0x0052E9C0, h1b_ret("SHUT")), (0x0052D350, h1b_auto),
               (0x00539760, h1b_jch("ClientAddPlayerToGame")), (0x005345A0, h1b_jch("PlayerLoad")),
               (0x005343A0, h1b_jch("PLRSAVE_ReadFile")), (0x00534330, h1b_jch("D2S_ReadSave")),
               (0x0056B1B1, h1b_rbase), (0x0056B318, h1b_mrx), (0x0056B343, h1b_m5726),
               (0x00568F5C, h1b_hotk), (0x0056915B, h1b_wskl("left", "ax")), (0x00569191, h1b_wskl("right", "ax")),
               (0x005691C2, h1b_wskl("swapA", "out")), (0x005691FB, h1b_wskl("swapB", "out")), (0x0056912E, h1b_href), (0x00569283, h1b_gfx),
               (0x00568E60, h1b_mhw0), (0x00568EA9, h1b_mhw1), (0x00568EFC, h1b_mhwd), (0x00568F0A, h1b_mhw2),
               (0x0056AFC0, h1b_lfg), (0x0056AFF5, h1b_lfb), (0x0056B01A, h1b_lfs), (0x0056B151, h1b_lfx0),
               (0x0056B156, h1b_lfx), (0x0056B3C8, h1b_lfe),
               (0x00558D28, h1b_rist), (0x006312B0, h1b_sbx), (0x00630887, h1b_rww), (0x0062D1DA, h1b_rwr),
               (0x00558E9B, h1b_b13s), (0x00553357, h1b_b13c),
               (0x0052D900, h1b_flag("tick", 1)), (0x0052D905, h1b_flag("tick", 0)),
               (0x00559482, h1b_site("GOLD", "esi")), (0x0055A360, h1b_site("COPY", "edi")),
               (0x0055A438, h1b_site("COPY2", "esi")), (0x006280D0, h1b_setf), (0x0055AEEC, h1b_cpost)):
    h1b_Bp(_a, _f)
for _a, _s, _p in h1b_WRITE_SITES:
    h1b_Bp(_a, h1b_wsec(_s, _p))
for _a, _s in h1b_READ_SITES:
    h1b_Bp(_a, h1b_rsec(_s))
