# gdb Python logger for plan 0041 Phase 2 (stats and states, per-event reproduction): the stat-list events of
# docs/findings/stats/0001-aggregate.md and the requirement, set and passive code around them, for the server's player
# unit and every list under it (its "tree"). Sourced by tools/gdb/stats.gdb after tools/gdb/pilot.py (the lines
# tools/d2pilot.py steers by). One line per breakpoint, "TAG {json}"; every line carries "fr" (game +0xA8, the server
# frame). A function's exit breakpoint sits on its ret instruction, where ESP equals the entry ESP, which pairs them.
# Addresses refer to the pinned game.exe (image base 0x400000). Seeds "low:high" hex.
#
# A list is in the tree when its parent chain (StatList +0x34) reaches the player's unit list (unit +0x5C); the player
# is the type-0 unit in the server game's unit table (game +0x1120, 128 heads, next = unit +0xE4).
# Entries are [key, value] with key = stat << 16 | param.
#
#   ISC     once per game (at GPTR): the loaded ItemStatCost run-time fields the model reads, zlib+base64 JSON:
#           per stat [flags +0x04, flags +0x05, ValShift +0x18, MinAccr +0x2C, keepzero +0x50, +0x51, +0x52, +0x53,
#           op +0x54, targets +0x58 (3 words), dependents +0x5E (until 0xFFFF), opIn +0x0DE (6-byte entries
#           [opBase, source, op, opParam] until op 0), the raw opBase words of opIn[0..2] (what StatRecompute's take
#           test reads, 0x006267C0)], and the flag masks at 0x006CE270 / 0x006CE274
#   TREE    the player's whole tree after each top-level list event, or once at the end of an EquipReqRefresh for
#           the events inside it (TREE0: the first one): zlib+base64 JSON of
#           the unit list, recursively: {p, f flags, s state, u +0x04, ct +0x08, cg +0x0C, x +0x18, sk +0x1C,
#           sl +0x20, own [[k, v]...], cache [[k, v]...] (extended), ow {u, t, c, q, fl, fi} (extended: owner +0x44),
#           ch [...] (+0x3C), off [...] (+0x40)}; also "inv": the player's items (Inventory +0x0C, next ItemData
#           +0x64): [unit, class, quality +0x00, flags +0x18, file index +0x28, body +0x44 byte, page +0x69,
#           stat list]; the player's seed and the game seed
#   LNK/LNX STATLIST_LinkToUnit 0x00626E10 (unit, list, withDamage) entry with the linked list's subtree and the
#           EBP-chain return addresses above the caller ("ra2", also on ULK) / its
#           returns 0x00626E8A, 0x00626FBF, 0x00627028 (matched by ESP)
#   ULK/ULX STATLIST_Unlink 0x006269F0 (list) entry / return 0x00626BEE
#   TGL/TGX UNIT_ToggleStatListByState 0x006279A0 (unit, state, off) entry / returns 0x006279AD, 0x006279FF,
#           0x00627A29, 0x00627A31; for a unit of the tree, or the item of the open TIP
#   PRP/PRX STATLIST_Propagate 0x00626920 (ECX list, EDX key, delta, srcItem) entry with the return address and the
#           list's own entry now / return 0x006269DF
#   CA      STATLIST_CacheAdd 0x006250B0 (EBX list; key, delta): old cache value; on a list of the tree or one being
#           unlinked from it (an open ULK)
#   CW      STATLIST_CacheWrite 0x00625150 (EBX list; key, new): old cache value (null when absent)
#   SCB     sub_0055B800_MonStatCallback entry for the player (EDX unit; key, old, new)
#   RD      sub_00624F60_StatListGetValue returns 0x00624F92 / 0x00624FD7 (EBX list, EDI key, EAX value, [esp+4] the
#           ISC record or 0) on the player's unit list, only in a window of 50 frames after each top-level list
#           event (at most STATS_READS_PER_WIN reads, default 1500)
#   RQ0     sub_0062EAF0_ItemReqCheck entry (item, unit, self) for the player: the item's class, flags, quality, its
#           base record's +0x10A/+0x10C; RQ91 0x0062EB80 (stat 91, EAX); RQS 0x0062EC0C (the item's own strength,
#           [ebp-0x14]); RQD 0x0062EC60 (own dexterity, [ebp+0x10]); RQL 0x0062EC88 (required level, EAX);
#           RQF 0x0062ECC5 (the strength, dexterity and level flags [ebp-4], [ebp-8], ECX and the identified bit
#           [ebp-0x10]); RQX the returns 0x0062EB37, 0x0062ED36, 0x0062ED41 (EAX)
#   EQR/EQX sub_0055DBC0_EquipReqRefresh entry (EDX unit) / return 0x0055DEF5
#   UOE/UOX SETS_UpdateOnEquip 0x00663CC0 (owner, item, mode, x) / returns; MSK 0x00663D09 (the mask, EAX)
#   TIP     SETS_ToggleItemAProps 0x00663A20 (ECX item, EDX mask); UOB SETS_UpdateOwnerBonusList 0x00663B40
#           (ECX owner, EDX item, mode); SBA/SBX sub_00660120_SetBonusApply (ECX owner, EDX item, state) / return
#           0x00660236 with the player's lists of that state ([pointer, flags, entries])
#   DMG     STATLIST_DisableDamageStats 0x00627A40 / STATLIST_EnableDamageStats 0x00627860 entries (unit, item)
#   PAS/PAX SKILLS_RefreshPassive 0x00646D60 (unit, skill) / returns 0x00646E19, 0x00646F10
#   TK0/TK1 sub_00580810_RegenEvent (ECX game, EDX unit) for the player / return 0x00580855: seeds, vitals, the
#           unit mode +0x10 and its states-on bits (at most STATS_TICKS per session, default 80)
#   STA0/1  STATE_ApplyTimed 0x0056E970 entry (ECX request: source, target, skill, level, duration, stat, value,
#           state, remove callback) for a target that is the player ("w": "p") or a hireling ("h"), with the
#           target's states-on bits and the game, target and source seeds / returns 0x0056E9C2, 0x0056EAD2,
#           0x0056EBCD, 0x0056EBDD (EAX the list: flags, state, expiry frame +0x18, skill, level, entries);
#           with STATS_MONSTA set (rev 9, plan 0047 Phase 2) also for a monster target ("w": "m", "mc" its class)
#   EXP0/1  EVENT_TimedListExpire 0x00580800 (ECX game, EDX unit) for the player: its +0x3C children [list,
#           flags, state, +0x18] and seeds / return 0x0058080D
#   AU0/1   EVENT_SelectedAuraTick 0x0056FCB0 ("sel") and EVENT_ItemAuraTick 0x0056FE40 ("item") (EDX unit) for the
#           player and a hireling / their returns: seeds
#   RNGA    while an AU0 .. AU1 run is open, every LCG multiplier site (tools/gdb/lcg-sites.txt, 852): its address,
#           [esp] and [ebp+4]
#   GRP/GRX STATE_GroupClear 0x0056C740 (ECX unit, EDX state, [esp+4]) for the player, its state bits / returns
#           (rev 10: nested calls kept on a stack, "dp" the depth, so every call has its GRX)
#   SHR0/1  OBJOP_Shrine 0x00583C70 (ECX context: +4 object, +8 unit) for the player: object class, ObjectData
#           +0x00..+0x1F, vitals, seeds / returns 0x00583CA4, 0x00583E65
#   WEL0/1  the well use 0x00585720 (ESI unit, [esp+8] the Objects record: Parm1 +0x17C, +0x180, Parm3 +0x184)
#           for the player: vitals and states before / return 0x0058589B
#   vitals  stats 6, 7, 8, 9, 10, 11, 26, 27, 28, 74 from the full cache (TK0/TK1, SHR, WEL)
#   OBJS    with STATS_OBJS set: the server's objects [class, x, y, mode] every 2 s (for tools/d2pilot.py objop)
import base64
import json
import os
import struct
import time
import zlib

import gdb


def _stats_main():
    inf = gdb.selected_inferior()
    DT_PTR = 0x00744304
    RD_CAP = int(os.environ.get("STATS_READS_PER_WIN", "1500") or 1500)
    TK_CAP = int(os.environ.get("STATS_TICKS", "80") or 80)
    st = {"game": 0, "plr": 0, "plist": 0, "frames": {}, "depth": 0, "win": 0, "nrd": 0, "ntk": 0, "isc": False,
          "tree0": False, "tk": {}, "unl": {}, "sta": {}, "au": {}}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def s8(a):
        return struct.unpack("<b", mem(a, 1))[0]

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

    def emit(tag, d):
        d["fr"] = frame()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def z(obj):
        return base64.b64encode(zlib.compress(json.dumps(obj, separators=(",", ":")).encode(), 6)).decode()

    def sd(a):
        return "%08x:%08x" % struct.unpack("<II", mem(a, 8)) if a else None

    def frame():
        g = st["game"]
        try:
            return u32(g + 0xA8) if g else None
        except gdb.MemoryError:
            return None

    def player():
        p = st["plr"]
        if p:
            try:
                if u32(p) == 0 and u32(p + 0x5C) == st["plist"] and st["plist"]:
                    return p
            except gdb.MemoryError:
                pass
        st["plr"], st["plist"] = 0, 0
        g = st["game"]
        if not g:
            return 0
        heads = struct.unpack("<128I", mem(g + 0x1120, 512))
        for h in heads:
            u, k = h, 0
            while u and k < 64:
                if u32(u) == 0:
                    st["plr"], st["plist"] = u, u32(u + 0x5C)
                    return u
                u = u32(u + 0xE4)
                k += 1
        return 0

    def seeds():
        p = player()
        return {"gs": sd(st["game"] + 0xD0) if st["game"] else None, "us": sd(p + 0x20) if p else None}

    def in_tree(lst):
        if not lst or not player():
            return False
        pl, x = st["plist"], lst
        for _ in range(10):
            if x == pl:
                return True
            x = u32(x + 0x34)
            if not x:
                return False
        return False

    def entries(arr, n):
        if not arr or n <= 0 or n > 4096:
            return []
        return [[k, v] for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n))]

    def lookup(lst, off, key):
        arr, n = u32(lst + off), s16(lst + off + 4)
        for k, v in entries(arr, n):
            if k == key:
                return v
        return None

    def item_info(it):
        d = {"u": it, "t": u32(it), "c": s32(it + 4)}
        if d["t"] == 4:
            idt = u32(it + 0x14)
            if idt:
                d.update(q=u32(idt), fl=u32(idt + 0x18), fi=s32(idt + 0x28), bl=u8(idt + 0x44), pg=s8(idt + 0x69))
        return d

    def tree(lst, depth=0):
        f = u32(lst + 0x10)
        d = {"p": lst, "f": f, "s": s32(lst + 0x14), "u": u32(lst + 0x04), "ct": s32(lst + 0x08), "cg": u32(lst + 0x0C),
             "x": s32(lst + 0x18), "sk": s32(lst + 0x1C), "sl": s32(lst + 0x20),
             "own": entries(u32(lst + 0x24), s16(lst + 0x28))}
        if f & 0x80000000 and depth < 6:
            d["cache"] = entries(u32(lst + 0x48), s16(lst + 0x4C))
            ow = u32(lst + 0x44)
            if ow:
                d["ow"] = item_info(ow)
            for off, name in ((0x3C, "ch"), (0x40, "off")):
                out, c, k = [], u32(lst + off), 0
                while c and k < 64:
                    out.append(tree(c, depth + 1))
                    c = u32(c + 0x2C)
                    k += 1
                d[name] = out
        return d

    def inventory(u):
        inv = u32(u + 0x60) if u else 0
        out = []
        if not inv or u32(inv) != 0x01020304:
            return out
        it, k = u32(inv + 0x0C), 0
        while it and k < 200:
            d = item_info(it)
            d["l"] = u32(it + 0x5C)
            out.append(d)
            idt = u32(it + 0x14)
            it = u32(idt + 0x64) if idt else 0
            k += 1
        return out

    def snap(tag="TREE"):
        p = player()
        if not p:
            return
        d = {"z": z({"t": tree(st["plist"]), "inv": inventory(p)}), "plr": p, "lvl": st["plist"]}
        d.update(seeds())
        emit(tag, d)

    def isc_dump():
        dt = u32(DT_PTR)
        base, n = u32(dt + 0xBCC), s32(dt + 0xBD4)
        rows = []
        raw = mem(base, n * 0x144)
        for i in range(n):
            r = raw[i * 0x144:(i + 1) * 0x144]
            deps = []
            for j in range(64):
                w = struct.unpack_from("<H", r, 0x5E + 2 * j)[0]
                if w == 0xFFFF:
                    break
                deps.append(w)
            ins = []
            for j in range(16):
                ob, src, op, opp = struct.unpack_from("<HHBB", r, 0xDE + 6 * j)
                if op == 0:
                    break
                ins.append([ob, src, op, opp])
            rows.append([r[4], r[5], r[0x18], struct.unpack_from("<i", r, 0x2C)[0], r[0x50], r[0x51], r[0x52], r[0x53],
                         r[0x54], list(struct.unpack_from("<3H", r, 0x58)), deps, ins,
                         [struct.unpack_from("<H", r, 0xDE + 6 * k)[0] for k in range(3)]])
        emit("ISC", {"n": n, "m270": u8(0x006CE270), "m274": u8(0x006CE274), "z": z(rows)})

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn, enabled=True):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn
            self.enabled = enabled

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR stats %s %r\n" % (getattr(self.fn, "__name__", "?"), e))
            return False

    rd_bps = []

    def rd_arm(on):
        for b in rd_bps:
            if b.enabled != on:
                b.enabled = on

    def on_game():
        st["game"] = reg("edi")
        st["plr"] = st["plist"] = 0
        st["tree0"] = False
        if not st["isc"]:
            st["isc"] = True
            try:
                isc_dump()
            except Exception as e:
                gdb.write("LOGERR stats isc %r\n" % (e,))

    # ---- frames: entry pushes (esp after return, tag); exit pops by ESP
    def open_frame(tag, key):
        top = st["depth"] == 0
        st["frames"][key] = (tag, top)
        st["depth"] += 1
        return top

    def close_frame(key):
        x = st["frames"].pop(key, None)
        if x is None:
            return None
        st["depth"] -= 1
        return x

    def end_top(tag):
        if st.get("eqr"):
            # inside sub_0055DBC0_EquipReqRefresh (every set item detached and attached again): one TREE at its end
            st["tree_due"] = True
            return
        if not st["tree0"]:
            st["tree0"] = True
            snap("TREE0")
            return
        snap()
        st["win"] = (frame() or 0) + 50
        st["nrd"] = 0
        rd_arm(True)

    def on_lnk():
        esp = reg("esp")
        unit, lst, dmg = u32(esp + 4), u32(esp + 8), u32(esp + 12)
        if not unit or not player():
            return
        ul = u32(unit + 0x5C)
        if not in_tree(ul):
            return
        top = open_frame("LNK", esp)
        d = {"u": unit, "ut": u32(unit), "ul": ul, "l": lst, "dmg": dmg, "top": top, "ra": u32(esp),
             "ra2": callers(), "sub": z(tree(lst))}
        if top:
            d.update(seeds())
        emit("LNK", d)

    def on_lnx():
        x = close_frame(reg("esp"))
        if not x:
            return
        d = {"top": x[1]}
        if x[1]:
            d.update(seeds())
        emit("LNX", d)
        if x[1]:
            end_top("LNK")

    def on_ulk():
        esp = reg("esp")
        lst = u32(esp + 4)
        if not lst or not in_tree(lst) or lst == st["plist"]:
            return
        top = open_frame("ULK", esp)
        st["unl"][esp] = lst
        d = {"l": lst, "pa": u32(lst + 0x34), "top": top, "ra": u32(esp), "ra2": callers(), "f": u32(lst + 0x10)}
        if top:
            d.update(seeds())
        emit("ULK", d)

    def on_ulx():
        st["unl"].pop(reg("esp"), None)
        x = close_frame(reg("esp"))
        if not x:
            return
        d = {"top": x[1]}
        if x[1]:
            d.update(seeds())
        emit("ULX", d)
        if x[1]:
            end_top("ULK")

    def on_tgl():
        esp = reg("esp")
        unit, state, off = u32(esp + 4), s32(esp + 8), s32(esp + 12)
        if not unit or not (in_tree(u32(unit + 0x5C)) or unit == st.get("tip")):
            return
        top = open_frame("TGL", esp)
        d = {"u": unit, "st": state, "off": off, "top": top, "ra": u32(esp)}
        if top:
            d.update(seeds())
        emit("TGL", d)

    def on_tgx():
        x = close_frame(reg("esp"))
        if not x:
            return
        d = {"top": x[1], "r": sreg("eax")}
        if x[1]:
            d.update(seeds())
        emit("TGX", d)
        if x[1]:
            end_top("TGL")

    def on_prp():
        lst = reg("ecx")
        if not in_tree(lst):
            return
        esp = reg("esp")
        key = reg("edx")
        top = open_frame("PRP", esp)
        d = {"l": lst, "k": key, "d": s32(esp + 4), "src": u32(esp + 8), "ra": u32(esp), "own": lookup(lst, 0x24, key),
             "top": top}
        if top:
            d.update(seeds())
        emit("PRP", d)

    def on_prx():
        x = close_frame(reg("esp"))
        if not x:
            return
        d = {"top": x[1]}
        if x[1]:
            d.update(seeds())
        emit("PRX", d)

    def callers(n=4):
        """The return addresses of the EBP frame chain at a function entry (the caller's frame onwards)."""
        out, bp = [], reg("ebp")
        for _ in range(n):
            if not bp or bp < 0x10000:
                break
            try:
                out.append(u32(bp + 4))
                bp = u32(bp)
            except gdb.MemoryError:
                break
        return out

    def tracked(lst):
        return in_tree(lst) or lst in st["unl"].values()

    def on_ca():
        lst = reg("ebx")
        if not tracked(lst):
            return
        esp = reg("esp")
        key = u32(esp + 4)
        emit("CA", {"l": lst, "k": key, "d": s32(esp + 8), "o": lookup(lst, 0x48, key)})

    def on_cw():
        lst = reg("ebx")
        if not tracked(lst):
            return
        esp = reg("esp")
        key = u32(esp + 4)
        emit("CW", {"l": lst, "k": key, "v": s32(esp + 8), "o": lookup(lst, 0x48, key)})

    def on_cb():
        u = reg("edx")
        if not u or u != player():
            return
        esp = reg("esp")
        emit("SCB", {"src": u32(esp + 4), "k": u32(esp + 8), "o": s32(esp + 12), "n": s32(esp + 16)})

    def on_rd():
        if reg("ebx") != st["plist"] or not st["plist"]:
            return
        fr = frame() or 0
        if fr > st["win"] or st["nrd"] >= RD_CAP:
            rd_arm(False)
            return
        st["nrd"] += 1
        esp = reg("esp")
        emit("RD", {"k": reg("edi"), "v": sreg("eax"), "r": 1 if u32(esp + 4) else 0})

    # ---- requirements
    def on_rq0():
        esp = reg("esp")
        it, unit, self_ = u32(esp + 4), u32(esp + 8), u32(esp + 12)
        if not unit or unit != player():
            return
        st["rq"] = esp
        d = {"it": item_info(it), "self": self_, "ra": u32(esp)}
        emit("RQ0", d)

    def rq_on():
        return st.get("rq") is not None

    def on_rq91():
        if rq_on():
            emit("RQ91", {"v": sreg("eax"), "rs": reg("edi"), "rd": s32(reg("ebp") - 0x18)})

    def on_rqs():
        if rq_on():
            emit("RQS", {"v": s32(reg("ebp") - 0x14)})

    def on_rqd():
        if rq_on():
            emit("RQD", {"v": s32(reg("ebp") + 0x10)})

    def on_rql():
        if rq_on():
            emit("RQL", {"v": sreg("eax")})

    def on_rqf():
        if rq_on():
            ebp = reg("ebp")
            emit("RQF", {"so": s32(ebp - 4), "do": s32(ebp - 8), "lo": sreg("ecx"), "id": s32(ebp - 0x10)})

    def on_rqx():
        if not rq_on() or st["rq"] != reg("esp"):
            return
        st["rq"] = None
        emit("RQX", {"r": sreg("eax")})

    def on_eqr():
        u = reg("edx")
        if u and u == player():
            st["eqr"] = reg("esp")
            emit("EQR", {})

    def on_eqx():
        if st.get("eqr") == reg("esp"):
            st["eqr"] = None
            emit("EQX", {})
            if st.pop("tree_due", False) and st["depth"] == 0:
                end_top("EQR")

    # ---- sets
    def on_uoe():
        esp = reg("esp")
        owner, it = u32(esp + 4), u32(esp + 8)
        if not owner or owner != player():
            return
        st["uoe"] = esp
        emit("UOE", {"it": item_info(it), "mode": s32(esp + 12), "x": s32(esp + 16), "inv": z(inventory(owner))})

    def on_uox():
        if st.get("uoe") == reg("esp"):
            st["uoe"] = st["tip"] = None
            emit("UOX", {})

    def on_msk():
        if st.get("uoe"):
            emit("MSK", {"m": reg("eax")})

    def on_tip():
        if st.get("uoe"):
            st["tip"] = reg("ecx")
            emit("TIP", {"it": reg("ecx"), "m": reg("edx")})

    def on_uob():
        if st.get("uoe") or reg("ecx") == player():
            emit("UOB", {"it": reg("edx"), "mode": s32(reg("esp") + 4)})

    def on_sba():
        if reg("ecx") == player():
            esp = reg("esp")
            st["sba"] = (esp, s32(esp + 4))
            emit("SBA", {"it": reg("edx"), "st": s32(esp + 4)})

    def on_sbx():
        x = st.get("sba")
        if x and x[0] == reg("esp"):
            st["sba"] = None
            out = []
            for off in (0x3C, 0x40):
                c, k = u32(st["plist"] + off), 0
                while c and k < 64:
                    if s32(c + 0x14) == x[1]:
                        out.append([c, u32(c + 0x10), entries(u32(c + 0x24), s16(c + 0x28))])
                    c = u32(c + 0x2C)
                    k += 1
            emit("SBX", {"st": x[1], "lists": out})

    def on_dmg(tag):
        def f():
            esp = reg("esp")
            unit = u32(esp + 4)
            if unit and unit == player():
                emit("DMG", {"k": tag, "it": u32(esp + 8)})
        return f

    # ---- passives
    def on_pas():
        esp = reg("esp")
        unit = u32(esp + 4)
        if unit and unit == player():
            st["pas"] = esp
            emit("PAS", {"sk": s32(esp + 8)})

    def on_pax():
        if st.get("pas") == reg("esp"):
            st["pas"] = None
            emit("PAX", {"r": sreg("eax")})

    # ---- the regeneration tick
    def vit(u):
        lst = u32(u + 0x5C)
        return [lookup(lst, 0x48, k << 16) for k in (6, 7, 8, 9, 10, 11, 26, 27, 28, 74)]

    OBJS = bool(os.environ.get("STATS_OBJS"))

    def objs_scan():
        """OBJS (as tools/gdb/vendors.py writes them, for tools/d2pilot.py objop): every object of the server game
        (game +0x1520, 128 heads, next = unit +0xE4) as [class, x, y, mode], at most every 2 s."""
        now = time.time()
        if now - st.get("tobj", 0) < 2.0 or not st["game"]:
            return
        st["tobj"] = now
        objs = []
        for h in struct.unpack("<128I", mem(st["game"] + 0x1520, 512)):
            u, k = h, 0
            while u and k < 512:
                k += 1
                try:
                    sp = u32(u + 0x2C)
                    if sp:
                        objs.append([s32(u + 4), s32(sp + 0x0C), s32(sp + 0x10), u32(u + 0x10)])
                except gdb.MemoryError:
                    pass
                u = u32(u + 0xE4)
        emit("OBJS", {"o": objs})

    def on_tk0():
        u = reg("edx")
        if OBJS and u and u == player():
            objs_scan()
        if not u or u != player() or st["ntk"] >= TK_CAP:
            return
        st["ntk"] += 1
        esp = reg("esp")
        st["tk"][esp] = True
        d = {"m": u32(u + 0x10), "v": vit(u), "sb": state_bits(u)}
        d.update(seeds())
        emit("TK0", d)

    def on_tk1():
        if st["tk"].pop(reg("esp"), None):
            u = player()
            d = {"v": vit(u)}
            d.update(seeds())
            emit("TK1", d)

    HIRE = {271, 338, 359, 560, 561}

    def who(u):
        if not u:
            return None
        if u == player():
            return "p"
        try:
            if u32(u) == 1 and s32(u + 4) in HIRE:
                return "h"
        except gdb.MemoryError:
            return None
        return None

    def state_bits(u):
        """The unit list's states-on bit-set (+0x58: two sets of ceil(n/32) dwords, the first is 'on')."""
        lst = u32(u + 0x5C)
        if not lst:
            return []
        bs = u32(lst + 0x58)
        if not bs:
            return []
        n = (s32(u32(DT_PTR) + 0xC4) + 31) // 32
        out = []
        for i, w in enumerate(struct.unpack("<%dI" % n, mem(bs, 4 * n))):
            for b in range(32):
                if w >> b & 1:
                    out.append(32 * i + b)
        return out

    MONSTA = bool(os.environ.get("STATS_MONSTA"))   # plan 0047 Phase 2 (attract): requests on monsters too

    def on_sta0():
        blk = reg("ecx")
        v = struct.unpack("<9i", mem(blk, 36))
        tgt = v[1] & 0xFFFFFFFF
        w = who(tgt)
        if not w and MONSTA and tgt:
            try:
                if u32(tgt) == 1:
                    w = "m"
            except gdb.MemoryError:
                w = None
        if not w:
            return
        src = v[0] & 0xFFFFFFFF
        esp = reg("esp")
        st["sta"][esp] = (tgt, w)
        d = {"w": w, "t": tgt, "src": src, "srct": u32(src) if src else None, "srcc": s32(src + 4) if src else None,
             "sk": v[2], "sl": v[3], "len": v[4], "stat": v[5], "val": v[6], "state": v[7], "rm": v[8] & 0xFFFFFFFF,
             "sb": state_bits(tgt), "gs": sd(st["game"] + 0xD0), "us": sd(tgt + 0x20), "ss": sd(src + 0x20) if src
             else None}
        if w == "m":
            d["mc"] = s32(tgt + 4)                   # the monster's MonStats class
        emit("STA0", d)

    def on_sta1():
        esp = reg("esp")
        x = st["sta"].pop(esp, None)
        if not x:
            return
        tgt, w = x
        lst = reg("eax")
        d = {"w": w, "r": lst, "gs": sd(st["game"] + 0xD0), "us": sd(tgt + 0x20)}
        if lst:
            d.update(f=u32(lst + 0x10), s=s32(lst + 0x14), x=s32(lst + 0x18), sk=s32(lst + 0x1C), sl=s32(lst + 0x20),
                     own=entries(u32(lst + 0x24), s16(lst + 0x28)), pa=u32(lst + 0x34))
        emit("STA1", d)

    def on_exp0():
        u = reg("edx")
        if who(u) != "p":
            return
        st["exp"] = reg("esp")
        d = {"x": [[c, u32(c + 0x10), s32(c + 0x14), s32(c + 0x18)] for c in children(st["plist"])]}
        d.update(seeds())
        emit("EXP0", d)

    def on_exp1():
        if st.get("exp") == reg("esp"):
            st["exp"] = None
            d = {}
            d.update(seeds())
            emit("EXP1", d)

    def children(lst):
        out, c, k = [], u32(lst + 0x3C), 0
        while c and k < 128:
            out.append(c)
            c = u32(c + 0x2C)
            k += 1
        return out

    lcg_bps = []

    def lcg_arm(on):
        for b in lcg_bps:
            if b.enabled != on:
                b.enabled = on

    def on_lcg(addr):
        def f():
            if not st["au"]:
                return
            esp, ebp = reg("esp"), reg("ebp")
            emit("RNGA", {"pc": addr, "ra": u32(esp), "ra2": u32(ebp + 4) if ebp else None,
                          "w": [x[1] for x in st["au"].values()]})
        return f

    def on_au0(kind):
        def f():
            u = reg("edx")
            w = who(u)
            if not w:
                return
            esp = reg("esp")
            st["au"][esp] = (u, w, kind)
            lcg_arm(True)
            emit("AU0", {"k": kind, "w": w, "u": u, "a": s32(esp + 4), "gs": sd(st["game"] + 0xD0),
                         "us": sd(u + 0x20)})
        return f

    def on_au1():
        x = st["au"].pop(reg("esp"), None)
        if not st["au"]:
            lcg_arm(False)
        if x:
            emit("AU1", {"k": x[2], "w": x[1], "gs": sd(st["game"] + 0xD0), "us": sd(x[0] + 0x20)})

    def on_grp():
        u = reg("ecx")
        if who(u) != "p":
            return
        esp = reg("esp")
        # rev 10 (plan 0047 Phase 2b): a stack of open calls, since STATE_GroupClear is re-entered (the Druid's
        # Werebear clear of Werewolf calls it again for 139 before it returns); rev 9 kept one, so a nested call's
        # exit cleared it and the outer call logged no GRX
        st.setdefault("grp", []).append(esp)
        emit("GRP", {"st": sreg("edx"), "self": s32(esp + 4), "sb": state_bits(u), "dp": len(st["grp"])})

    def on_grx():
        stk = st.get("grp") or []
        if stk and stk[-1] == reg("esp"):
            stk.pop()
            emit("GRX", {"sb": state_bits(player()), "dp": len(stk) + 1})

    def on_shr0():
        ctx = reg("ecx")
        obj, unit = u32(ctx + 4), u32(ctx + 8)
        if unit != player():
            return
        st["shr"] = reg("esp")
        od = u32(obj + 0x14)
        d = {"o": obj, "oc": s32(obj + 4), "od": mem(od, 0x20).hex() if od else None, "v": vit(unit)}
        d.update(seeds())
        emit("SHR0", d)

    def on_shr1():
        if st.get("shr") == reg("esp"):
            st["shr"] = None
            d = {"r": sreg("eax"), "v": vit(player())}
            d.update(seeds())
            emit("SHR1", d)

    def on_wel0():
        u = reg("esi")
        if u != player():
            return
        esp = reg("esp")
        rec = u32(esp + 8)
        st["wel"] = esp
        d = {"rec": rec, "p": [s32(rec + 0x17C), s32(rec + 0x180), s32(rec + 0x184)] if rec else None, "v": vit(u),
             "sb": state_bits(u)}
        d.update(seeds())
        emit("WEL0", d)

    def on_wel1():
        if st.get("wel") == reg("esp"):
            st["wel"] = None
            d = {"r": sreg("eax"), "v": vit(player()), "sb": state_bits(player())}
            d.update(seeds())
            emit("WEL1", d)

    Bp(0x0052C312, on_game)
    Bp(0x00626E10, on_lnk)
    for a in (0x00626E8A, 0x00626FBF, 0x00627028):
        Bp(a, on_lnx)
    Bp(0x006269F0, on_ulk)
    Bp(0x00626BEE, on_ulx)
    Bp(0x006279A0, on_tgl)
    for a in (0x006279AD, 0x006279FF, 0x00627A29, 0x00627A31):
        Bp(a, on_tgx)
    Bp(0x00626920, on_prp)
    Bp(0x006269DF, on_prx)
    Bp(0x006250B0, on_ca)
    Bp(0x00625150, on_cw)
    Bp(0x0055B800, on_cb)
    for a in (0x00624F92, 0x00624FD7):
        rd_bps.append(Bp(a, on_rd, enabled=False))
    Bp(0x0062EAF0, on_rq0)
    Bp(0x0062EB80, on_rq91)
    Bp(0x0062EC0C, on_rqs)
    Bp(0x0062EC60, on_rqd)
    Bp(0x0062EC88, on_rql)
    Bp(0x0062ECC5, on_rqf)
    for a in (0x0062EB37, 0x0062ED36, 0x0062ED41):
        Bp(a, on_rqx)
    Bp(0x0055DBC0, on_eqr)
    Bp(0x0055DEF5, on_eqx)
    Bp(0x00663CC0, on_uoe)
    for a in (0x00663CCF, 0x00663D33, 0x00663D3B):
        Bp(a, on_uox)
    Bp(0x00663D09, on_msk)
    Bp(0x00663A20, on_tip)
    Bp(0x00663B40, on_uob)
    Bp(0x00660120, on_sba)
    Bp(0x00660236, on_sbx)
    Bp(0x00627A40, on_dmg("off"))
    Bp(0x00627860, on_dmg("on"))
    Bp(0x00646D60, on_pas)
    for a in (0x00646E19, 0x00646F10):
        Bp(a, on_pax)
    Bp(0x00580810, on_tk0)
    Bp(0x00580855, on_tk1)
    Bp(0x0056E970, on_sta0)
    for a in (0x0056E9C2, 0x0056EAD2, 0x0056EBCD, 0x0056EBDD):
        Bp(a, on_sta1)
    Bp(0x00580800, on_exp0)
    Bp(0x0058080D, on_exp1)
    Bp(0x0056FCB0, on_au0("sel"))
    for a in (0x0056FD4D, 0x0056FD64, 0x0056FE26, 0x0056FE3C, 0x0056FEAA, 0x0056FED5, 0x0056FEFF):
        Bp(a, on_au1)
    Bp(0x0056FE40, on_au0("item"))
    # every LCG site (tools/gdb/lcg-sites.txt), enabled only while an aura run (AU0 .. AU1) is open: RNGA lines
    with open(os.path.join(os.path.dirname(os.path.abspath("tools/gdb/lcg-sites.txt")), "lcg-sites.txt")) as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if line:
                a = int(line, 16)
                lcg_bps.append(Bp(a, on_lcg(a), enabled=False))
    Bp(0x0056C740, on_grp)
    for a in (0x0056C82F, 0x0056C83A):
        Bp(a, on_grx)
    Bp(0x00583C70, on_shr0)
    for a in (0x00583CA4, 0x00583E65):
        Bp(a, on_shr1)
    Bp(0x00585720, on_wel0)
    Bp(0x0058589B, on_wel1)
    emit("STATSLOG", {"rev": 10})
    gdb.write("STATS logger armed\n")


_stats_main()
