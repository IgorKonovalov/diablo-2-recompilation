# gdb Python logger for plan 0054 Phase 2 (path search, per-event reproduction). Sourced by tools/gdb/path.gdb after
# tools/gdb/pilot.py (the PLR/MON/CB/RL lines tools/d2pilot.py steers by). One line per event, "TAG {json}". Addresses
# refer to the pinned game.exe (image base 0x400000). Seeds are "low:high" hex. Every line carries "n", this logger's
# own line count; the lines of one plan share "k" (the PLN line's "n"). docs/findings/path/0001 § 13 is the design.
#
#   AGM   0x0052C312 (GAME_InitSeeds, EDI = game): the server game pointer; the caps restart (a case of a shared process)
#   PLN   sub_00649970_PathPlan entry (stdcall: [esp] return, path, unit, force) for a server unit within PATH_RADIUS
#         of the first player: u (type, class, id, mode, x, y of the unit's path), p (the path record address), ty (path
#         +0x3C), fl (+0x34), fo (force), ra (the caller's return address), s0 (the unit seed), fr (Game +0xA8), rec
#         (the 0x200-byte path record, zlib+base64), tg (the target unit at +0x58: type, class, id, mode, x, y, and for an
#         object its record bytes +0x13A / +0x13C), ar (the planning unit's area/level id from its room)
#   PLG   a room of the window, once per content hash: a (the DungeonRoom), r (x0, y0, w, h at room +0x4C), mr (the collision
#         map's x0, y0, w, h), nr (its near list), h
#         (crc32 of the cells), nh (crc32 of the near list: a room is dumped again when either changes), lid, z ({"cells": hex of w*h u16} or null): the LIVE cells at the planner call
#   PLC   0x00649BAE (the planner call `call eax`; ECX the PathPlanCtx): pl (the planner address, EAX), ctx (0x34
#         bytes hex), rec (the path record then), rm ([room, hash] of the window's rooms), s (the unit seed), and PLU
#   PLU   the units whose marks may lie in the window: [type, id, class, mode, x, y, room, size +0x44, pattern +0x48,
#         mark mask +0x4C, flags +0x34] for players, monsters and missiles (dynamic paths) within the rooms' bounding
#         box; objects as [2, id, class, x, y (static path +0x0C / +0x10), room (static path +0), mode, sizeX +0xD0, sizeY +0xD4, IsDoor +0x13A,
#         +0x13B, +0x167, +0x1B6 of the object record, rev 5: HasCollision[mode], the byte `+0x120 + mode` of the record, 0x006219D3]; "self" and "tgt" the planning unit's and the
#         target's (type, id)
#   PLX   PathPlan's six rets (0x00649984, 0x006499C2, 0x006499F0, 0x00649C5F, 0x00649C6E, 0x00649C8F): eax, the record's
#         +0x28, +0x24, +0x34, the points (+0x9C, +0x28 words pairs, at most 78), +0x10/+0x12, +0x18/+0x1A, s (the unit
#         seed), rec (the whole record after)
#   SEEDW the next write to the low dword of the seed of a unit after its type-10 plan (env PATH_CHAIN = how many per game; at most
#         3 watched at once): k (the plan), u, from (the seed at the plan's exit), to (the seed when the write has landed), pc, st (6 stack
#         words)
#   BRK   a break line: fn (the planner or function), side (srv / cli by the unit's pGame), ra (return address of the
#         hit), pra (the PathPlan caller's return address when a server plan is open), ty, ctl (1 for the control line
#         on a reached planner), c (rev 5: the hit's count in this game; the first 20 hits and each power of two print, as S3C). Planners of types 3, 11, 12 (0x00679E50, 0x00679FD0, 0x00679E60), the two type-16
#         functions (0x00663E00, 0x00663ED0), and the control: PathPlanGreedy (0x00679C80)
#   S3C   a store to [reg+0x3C] outside the path module (the 18 unresolved bases and 4 read-modify-write sites of
#         path/0003 § 12): site, base, v (the value stored or the new value), c (the hit count), hit (1 when v in 3, 0xB, 0xC)
#   SPX   rev 5, the spiral's stored products: x, y (the low dwords of [ebp-0x20] right after each `fistp qword [ebp-0x20]`, breaks 0x0067A1AF and
#         0x0067A1E0, one pair per iteration) of a logged type-14 plan: k, read-only
#   T1S   rev 5, a type-1 request site reached: the five AiPathOverrideSet(1) calls (0x005E3BCC, 0x005E4300, 0x005E5DD9, 0x005E5EE7, 0x005E5F40) and the two
#         PathSetType(path, 1) calls (0x005CD484 SkillDo103DiabRun, 0x005CBC44 SkillSt48SwarmMove): site, u, side, pra, c, fr; counted
#   L1M   rev 5, a reserved landing's mark (path/0005 L1): the COLL_PatternMark calls 0x005D9123, 0x005D9EF8, 0x005DA5D5, 0x005CB902: site, u, side, room, x, y,
#         pat, mask, c, fr
#   L1U   rev 5, its release: the COLL_PatternUnmark calls 0x005DA1F3, 0x005DA269, 0x005D94E8, 0x005CBA3B: the same fields
#   COR   rev 5, a UnitCorpseColl call, at its return (entry 0x00649F70, rets 0x00649FB2, 0x00649FE6): site (the call's address), u, side, arg, x, y, room, after
#         (the 5 x 5 of cells around x, y after the call, row by row, null off the grid), pat, mask (the path record's), fr, c
#   CAP   once per kind when its cap is reached
# Filter (ADR-0014 § Log volume): server units (Unit +0x80 = the server game) within PATH_RADIUS (80) subtiles of the first player on
# each axis, per-game caps: PATH_CAP_TYPE (250) plans that reach a planner per path type, PATH_CAP_REF (40) refusals per type,
# PATH_CAP_SESSION (3500) plans, PATH_CAP_UNITS (400) units per plan (rev 5: raised from 120; objects are listed first, so a cut takes missiles first; the
# PLC line's ucut says how many). PATH_CAP_LINES (300): L1M and COR lines per site per game. The record holds no marked-state field: whether a unit's mark is
# in the grid is the rules' answer (path/0005 O1, C1..C4, T1, L1, W1). Read-only: this logger never writes game memory or registers (ADR-0003).
import base64
import json
import os
import struct
import zlib

import gdb

REV = 5   # rev 1: the development logs (dev-*); rev 2: the near list is part of a room dump key; rev 3: the seed watchpoint PC, the spiral probe; rev 4: items in the unit list (PATH_ITEMS), the watchpoint control (PATH_CHAIN_CTL); rev 5: read-only: the spiral probe removed, SPX, T1S, L1M, COR, counted BRK, HasCollision on object entries, unit cap 400


def _path_main():
    inf = gdb.selected_inferior()
    CAP_TYPE = int(os.environ.get("PATH_CAP_TYPE", "250"))
    CAP_REF = int(os.environ.get("PATH_CAP_REF", "40"))
    CAP_SESSION = int(os.environ.get("PATH_CAP_SESSION", "3500"))
    CAP_UNITS = int(os.environ.get("PATH_CAP_UNITS", "400"))
    RADIUS = int(os.environ.get("PATH_RADIUS", "80"))
    CAP_LINES = int(os.environ.get("PATH_CAP_LINES", "300"))
    ITEMS = int(os.environ.get("PATH_ITEMS", "0"))              # rev 4: the items of the ground in the unit list
    CHAINCTL = int(os.environ.get("PATH_CHAIN_CTL", "0"))       # rev 4: the control of the seed watchpoints: monster units after a type-13 plan
    CHAIN = int(os.environ.get("PATH_CHAIN", "0"))              # type-10 plans per game whose unit seed is watched to its next write
    MAXROOMS = int(os.environ.get("PATH_MAXROOMS", "40"))
    st = {"game": 0, "n": 0, "line": 0, "stk": {}, "cur": None, "plr": 0, "reach": {}, "ref": {}, "tot": 0, "capped": set(),
          "rooms": {}, "brk": {}, "s3c": {}, "t1s": {}, "lines": {}, "cor": {}, "wps": [], "chain": 0, "chainctl": 0}
    # the +0x3C stores of path/0003 § 12: site -> (op, base register, source register or immediate)
    S3C = {
        0x00529481: ("mov", "eax", "edx"), 0x0052981A: ("mov", "eax", "edx"), 0x00529BD7: ("mov", "eax", "edx"),
        0x00529F12: ("mov", "eax", "edx"), 0x00559002: ("mov", "esi", "eax"), 0x0057C628: ("mov", "esi", "eax"),
        0x005B5389: ("mov", "edi", "eax"), 0x005BBC61: ("mov", "esi", "ecx"), 0x005FFF92: ("mov", "esi", "eax"),
        0x00600225: ("mov", "esi", "ebx"), 0x00600230: ("mov", "esi", "eax"), 0x006003B2: ("mov", "esi", "eax"),
        0x006242FF: ("mov", "edi", "ecx"), 0x00626E9D: ("mov", "esi", "edi"), 0x00670869: ("mov", "eax", "edx"),
        0x0068CFFB: ("mov", "ebp", "eax"), 0x006C3CF6: ("mov", "eax", "edi"), 0x006C3DE9: ("mov", "edi", "eax"),
        0x005BB82C: ("add", "ebx", 1), 0x0063D4CF: ("add", "esi", 1), 0x0063D54C: ("add", "esi", -1),
        0x0068CDCF: ("or", "ebp", -1),
    }
    BRK = {0x00679E50: 3, 0x00679FD0: 11, 0x00679E60: 12, 0x00663E00: 16, 0x00663ED0: 16, 0x00679C80: -1}
    # the type-1 request sites (path/0004 § 4): site -> the register holding the unit (AiPathOverrideSet) or None (PathSetType: [esp] the path)
    T1S = {0x005E3BCC: "esi", 0x005E4300: "esi", 0x005E5DD9: "esi", 0x005E5EE7: "esi", 0x005E5F40: "esi", 0x005CD484: None, 0x005CBC44: None}
    # the reserved landings (path/0005 L1): site of the COLL_PatternMark call -> the register holding the unit
    L1M = {0x005D9123: "esi", 0x005D9EF8: "edi", 0x005DA5D5: "esi", 0x005CB902: "esi"}
    L1U = (0x005DA1F3, 0x005DA269, 0x005D94E8, 0x005CBA3B)     # their release at the landing: the unit in edi
    RETS = (0x00649984, 0x006499C2, 0x006499F0, 0x00649C5F, 0x00649C6E, 0x00649C8F)

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

    def emit(tag, d):
        st["line"] += 1
        d["n"] = st["line"]
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))
        return st["line"]

    def zb(b):
        return base64.b64encode(zlib.compress(b, 6)).decode()

    def sd(u):
        return "%08x:%08x" % struct.unpack("<II", mem(u + 0x20, 8)) if u else None

    def frame():
        g = st["game"]
        return u32(g + 0xA8) if g else None

    def upos(u):
        """A unit's position: types 2, 4, 5 the static path's dwords +0x0C/+0x10, others the dynamic path's words."""
        t = u32(u)
        p = u32(u + 0x2C)
        if not p:
            return None
        if t == 2 or 4 <= t <= 5:
            return (u32(p + 0x0C), u32(p + 0x10))
        return (u16(p + 2), u16(p + 6))

    def player():
        g, p = st["game"], st["plr"]
        if p:
            try:
                if u32(p) == 0 and u32(p + 0x80) == g:
                    return p
            except gdb.MemoryError:
                pass
        st["plr"] = 0
        for u in struct.unpack("<128I", mem(g + 0x1120, 512)):
            if u:
                st["plr"] = u
                return u
        return 0

    def lid_of(room):
        try:
            d = u32(room + 0x10)
            return u32(u32(d + 0x58) + 0x1D0) if d else None
        except gdb.MemoryError:
            return None

    def room_rect(r):
        return struct.unpack("<iiii", mem(r + 0x4C, 16))

    def near_of(r):
        n = u32(r + 0x24)
        p = u32(r)
        if not p or n > 64:
            return []
        return [x for x in struct.unpack("<%dI" % n, mem(p, 4 * n)) if x]

    def unit_info(u):
        p = u32(u + 0x2C)
        pos = upos(u) if p else (None, None)
        return [u32(u), s32(u + 4), u32(u + 0x0C), u32(u + 0x10)] + list(pos or (None, None))

    def on_game():
        st["game"] = reg("edi")
        st["stk"], st["cur"], st["plr"] = {}, None, 0
        st["reach"], st["ref"], st["tot"], st["capped"], st["rooms"], st["brk"] = {}, {}, 0, set(), {}, {}
        st["t1s"], st["lines"], st["cor"] = {}, {}, {}
        emit("AGM", {"game": st["game"]})

    def cap(kind, d, key, lim):
        n = d.get(key, 0)
        if n >= lim:
            if (kind, key) not in st["capped"]:
                st["capped"].add((kind, key))
                emit("CAP", {"k": kind, "key": key, "n": n})
            return False
        d[key] = n + 1
        return True

    def counted(d, key, first=20):
        """A hit's count, and whether it prints: the first ones and each power of two, as S3C, so a line's count covers its whole window."""
        c = d.get(key, 0) + 1
        d[key] = c
        return c, c <= first or (c & (c - 1)) == 0

    def side_of(u):
        g = st["game"]
        try:
            return "srv" if g and u and u32(u + 0x80) == g else "cli"
        except gdb.MemoryError:
            return "?"

    def info_of(u):
        try:
            return unit_info(u) if u else None
        except (gdb.MemoryError, TypeError):
            return None

    def cell_at(room, x, y, hop=0):
        """A cell of the grid around a room: the room's own collision map, else one of its near rooms'. Read-only."""
        if not room:
            return None
        m = u32(room + 0x20)
        if m:
            mx, my, mw, mh = struct.unpack("<iiii", mem(m, 16))
            c = u32(m + 0x20)
            if c and mx <= x < mx + mw and my <= y < my + mh:
                return u16(c + 2 * ((y - my) * mw + (x - mx)))
        if hop:
            return None
        for r in near_of(room):
            v = cell_at(r, x, y, 1)
            if v is not None:
                return v
        return None

    # ---- the plan --------------------------------------------------------------------------------------------------
    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error
                gdb.write("LOGERR path %s %r\n" % (getattr(self.fn, "__name__", "?"), e))
            return False

    def on_pln():
        g = st["game"]
        if not g:
            return
        esp = reg("esp")
        ra = u32(esp)
        path, unit, force = struct.unpack("<3I", mem(esp + 4, 12))
        st["cur"] = None
        if not path or not unit or u32(unit + 0x80) != g:
            return
        pl = player()
        px, py = u16(path + 2), u16(path + 6)
        if pl and unit != pl:
            q = u32(pl + 0x2C)
            if q and (abs(u16(q + 2) - px) > RADIUS or abs(u16(q + 6) - py) > RADIUS):
                return
        rec = mem(path, 0x200)
        f = {"spx": [], "esp": esp, "ra": ra, "path": path, "unit": unit, "force": force, "rec": rec, "s0": sd(unit),
             "ty": struct.unpack_from("<i", rec, 0x3C)[0], "fl": struct.unpack_from("<I", rec, 0x34)[0], "emitted": False,
             "skip": False, "fr": frame(), "u": unit_info(unit)}
        t = struct.unpack_from("<I", rec, 0x58)[0]
        f["tg"] = None
        if t:
            try:
                f["tg"] = unit_info(t)
                if f["tg"][0] == 2:
                    d = u32(t + 0x14)
                    r = u32(d) if d else 0
                    f["tg"] += [u8(r + 0x13A), u8(r + 0x13C)] if r else [None, None]
            except gdb.MemoryError:
                f["tg"] = None
        try:
            f["ar"] = lid_of(struct.unpack_from("<I", rec, 0x1C)[0]) if struct.unpack_from("<I", rec, 0x1C)[0] else None
        except gdb.MemoryError:
            f["ar"] = None
        st["stk"][esp] = f
        st["cur"] = f

    def plan_head(f):
        d = {"u": f["u"], "p": f["path"], "ty": f["ty"], "fl": f["fl"], "fo": f["force"], "ra": f["ra"], "s0": f["s0"],
             "fr": f["fr"], "rec": zb(f["rec"]), "tg": f["tg"], "ar": f["ar"]}
        f["k"] = emit("PLN", d)
        f["emitted"] = True

    def room_set(ctx):
        """The window's rooms: the unit's room, the target's room, their near lists, and the near lists of those."""
        r0, r1 = u32(ctx + 8), u32(ctx + 0x0C)
        out = []
        seen = set()
        todo = [r for r in (r0, r1) if r]
        for hop in range(3):
            nxt = []
            for r in todo:
                if r in seen:
                    continue
                seen.add(r)
                out.append(r)
                if hop < 2:
                    nxt.extend(near_of(r))
            todo = nxt
        return out[:MAXROOMS]

    def dump_rooms(rooms):
        rm = []
        box = [10 ** 9, 10 ** 9, -10 ** 9, -10 ** 9]
        for r in rooms:
            x0, y0, w, h = room_rect(r)
            box = [min(box[0], x0), min(box[1], y0), max(box[2], x0 + w), max(box[3], y0 + h)]
            m = u32(r + 0x20)
            cells = None
            mr = None
            if m:
                mx, my, mw, mh = struct.unpack("<iiii", mem(m, 16))
                mr = [mx, my, mw, mh]
                c = u32(m + 0x20)
                if c and 0 < mw * mh <= 1 << 20:
                    cells = mem(c, 2 * mw * mh)
            hsh = zlib.crc32(cells) if cells is not None else 0
            nr = near_of(r)
            nh = zlib.crc32(struct.pack("<%dI" % len(nr), *nr))
            rm.append([r, hsh, nh])
            if st["rooms"].get(r) != (hsh, nh):
                st["rooms"][r] = (hsh, nh)
                emit("PLG", {"a": r, "r": [x0, y0, w, h], "mr": mr, "nr": nr, "h": hsh, "nh": nh, "lid": lid_of(r),
                             "z": zb(cells) if cells is not None else None})
        return rm, box

    def units_in(box, f):
        """The unit list, objects first so a cut at PATH_CAP_UNITS takes the last dynamic units (missiles) and never an object; returns the list and how many were cut."""
        g = st["game"]
        objs, out = [], []
        for u in struct.unpack("<128I", mem(g + 0x1520, 512)):
            k = 0
            while u and k < 512:
                k += 1
                try:
                    p = u32(u + 0x2C)
                    if p:
                        x, y = u32(p + 0x0C), u32(p + 0x10)
                        if box[0] - 4 <= x <= box[2] + 4 and box[1] - 4 <= y <= box[3] + 4:
                            d = u32(u + 0x14)
                            r = u32(d) if d else 0
                            mode = u32(u + 0x10)
                            e = [2, u32(u + 0x0C), s32(u + 4), x, y, u32(p), mode]
                            if r:
                                e += [u32(r + 0xD0), u32(r + 0xD4), u8(r + 0x13A), u8(r + 0x13B), u8(r + 0x167), u8(r + 0x1B6), u8(r + 0x120 + mode)]
                            objs.append(e)
                    u = u32(u + 0xE4)
                except gdb.MemoryError:
                    break
        for base, kinds in ((0x1120, 0), (0x1320, 1), (0x1720, 3)):
            for u in struct.unpack("<128I", mem(g + base, 512)):
                k = 0
                while u and k < 512:
                    k += 1
                    try:
                        p = u32(u + 0x2C)
                        if p:
                            x, y = u16(p + 2), u16(p + 6)
                            if box[0] - 4 <= x <= box[2] + 4 and box[1] - 4 <= y <= box[3] + 4:
                                out.append([kinds, u32(u + 0x0C), s32(u + 4), u32(u + 0x10), x, y, u32(p + 0x1C), s32(p + 0x44),
                                            s32(p + 0x48), u32(p + 0x4C), u32(p + 0x34)])
                        u = u32(u + 0xE4)
                    except gdb.MemoryError:
                        break
        if ITEMS:
            for u in struct.unpack("<128I", mem(g + 0x1920, 512)):
                k = 0
                while u and k < 512:
                    k += 1
                    try:
                        p = u32(u + 0x2C)
                        if p:
                            x, y = u32(p + 0x0C), u32(p + 0x10)
                            if box[0] - 4 <= x <= box[2] + 4 and box[1] - 4 <= y <= box[3] + 4:
                                out.append([4, u32(u + 0x0C), s32(u + 4), x, y, u32(p), u32(u + 0x10)])
                        u = u32(u + 0xE4)
                    except gdb.MemoryError:
                        break
        out = objs + out
        return out[:CAP_UNITS], max(0, len(out) - CAP_UNITS)

    def on_plc():
        f = st["cur"]
        if not f or f["skip"]:
            return
        ctx = reg("ecx")
        if u32(ctx + 0x30) != f["path"]:
            return
        ty = f["ty"]
        if st["tot"] >= CAP_SESSION or not cap("reach", st["reach"], ty, CAP_TYPE):
            f["skip"] = True
            return
        st["tot"] += 1
        plan_head(f)
        rooms = room_set(ctx)
        rm, box = dump_rooms(rooms)
        units, cut = units_in(box, f)
        emit("PLC", {"k": f["k"], "pl": reg("eax"), "ctx": mem(ctx, 0x34).hex(), "rec": zb(mem(f["path"], 0x200)),
                     "rm": rm, "s": sd(f["unit"]), "u": units, "ucut": cut, "ucap": CAP_UNITS, "self": [f["u"][0], f["u"][2]],
                     "tgt": [f["tg"][0], f["tg"][2]] if f["tg"] else None})

    def on_plx():
        esp = reg("esp")
        f = st["stk"].pop(esp, None)
        if f is None:
            return
        if st["cur"] is f:
            st["cur"] = None
        if f["skip"]:
            return
        if not f["emitted"]:
            if st["tot"] >= CAP_SESSION:
                return
            straight = bool(f["fl"] & 0x40000)
            if straight:
                if not cap("reach", st["reach"], f["ty"], CAP_TYPE):
                    return
            elif not cap("ref", st["ref"], f["ty"], CAP_REF):
                return
            st["tot"] += 1
            plan_head(f)
        p, u = f["path"], f["unit"]
        rec = mem(p, 0x200)
        n = struct.unpack_from("<i", rec, 0x28)[0]
        n = max(0, min(n, 78))
        pts = list(struct.unpack_from("<%dI" % n, rec, 0x9C)) if n else []
        emit("PLX", {"k": f["k"], "eax": reg("eax"), "n28": struct.unpack_from("<i", rec, 0x28)[0],
                     "n24": struct.unpack_from("<i", rec, 0x24)[0], "fl": struct.unpack_from("<I", rec, 0x34)[0], "pts": pts,
                     "t": struct.unpack_from("<HH", rec, 0x10), "f18": struct.unpack_from("<HH", rec, 0x18), "s": sd(u),
                     "rec": zb(rec), "fr": frame()})
        if f["spx"]:
            emit("SPX", {"k": f["k"], "x": f["spx"][0::2], "y": f["spx"][1::2]})
        if CHAIN and f["ty"] == 10 and f["fl"] & 0x40000:
            arm_chain(f)
        elif CHAINCTL and f["ty"] == 13 and f["u"][0] == 1 and not f["fl"] & 0x40000:
            arm_chain(f, 1)

    class SeedWatch(gdb.Breakpoint):
        """A hardware watchpoint on a unit's seed low dword after a type-10 plan: the next write is the next event on that seed."""

        def __init__(self, unit, k, exit_seed, ctl=0):
            super().__init__("*(unsigned int *) 0x%08X" % (unit + 0x20), gdb.BP_WATCHPOINT, gdb.WP_WRITE, internal=True)
            self.silent = True
            self.unit, self.k, self.exit_seed, self.done, self.ctl = unit, k, exit_seed, False, ctl

        def stop(self):
            try:
                if not self.done:
                    self.done = True
                    esp = reg("esp")
                    emit("SEEDW", {"ctl": self.ctl, "k": self.k, "u": self.unit, "from": self.exit_seed, "to": sd(self.unit), "pc": int(gdb.parse_and_eval("(unsigned long) $pc")) & 0xFFFFFFFF,
                                   "st": list(struct.unpack("<6I", mem(esp, 24))), "fr": frame()})
                    self.enabled = False
            except Exception as e:
                gdb.write("LOGERR path seedw %r\n" % (e,))
            return False

    def arm_chain(f, ctl=0):
        live = [w for w in st["wps"] if not w.done]
        for w in st["wps"]:
            if w.done:
                try:
                    w.delete()
                except Exception:
                    pass
        st["wps"] = live
        if len(live) >= 3 or st["chainctl" if ctl else "chain"] >= (CHAINCTL if ctl else CHAIN):
            return
        try:
            w = SeedWatch(f["unit"], f["k"], sd(f["unit"]), ctl)
        except Exception as e:
            gdb.write("LOGERR path watch %r\n" % (e,))
            st["chain"] = CHAIN
            return
        st["wps"].append(w)
        st["chainctl" if ctl else "chain"] += 1

    def on_brk(addr):
        def f():
            g = st["game"]
            ctx = reg("ecx")
            esp = reg("esp")
            side, ty = None, None
            try:
                path = u32(ctx + 0x30) if addr not in (0x00663E00, 0x00663ED0) else None
                if path:
                    unit = u32(path + 0x30)
                    side = "srv" if g and u32(unit + 0x80) == g else "cli"
                    ty = s32(path + 0x3C)
            except gdb.MemoryError:
                side = "?"
            ctl = BRK[addr] == -1
            c, show = counted(st["brk"], (addr, side))
            if not show:
                return
            cur = st["cur"]
            emit("BRK", {"fn": addr, "ty": ty, "side": side, "ra": u32(esp), "pra": cur["ra"] if cur else None,
                         "ctl": 1 if ctl else 0, "c": c, "fr": frame()})
        return f

    def on_s3c(site):
        op, base, src = S3C[site]
        def f():
            b = reg(base)
            if op == "mov":
                v = reg(src)
            else:
                try:
                    old = u32(b + 0x3C)
                except gdb.MemoryError:
                    old = None
                if op == "add":
                    v = None if old is None else (old + src) & 0xFFFFFFFF
                else:
                    v = None if old is None else (old | (src & 0xFFFFFFFF))
            c = st["s3c"].get(site, 0) + 1
            st["s3c"][site] = c
            hit = 1 if v in (3, 0xB, 0xC) else 0
            if c <= 20 or hit or (c & (c - 1)) == 0:
                emit("S3C", {"site": site, "base": b, "v": v, "c": c, "hit": hit, "fr": frame()})
        return f

    def on_spx():
        """After a FISTP of PathPlanSpiral: the stored product's low dword, read. Only the open plan's type 14 keeps it."""
        f = st["cur"]
        if f and f["ty"] == 14:
            f["spx"].append(s32(reg("ebp") - 0x20))

    def on_t1s(site):
        def f():
            esp = reg("esp")
            r = T1S[site]
            if r:
                u = reg(r)
            else:
                path = u32(esp)
                u = u32(path + 0x30) if path else 0
            c, show = counted(st["t1s"], site)
            if show:
                cur = st["cur"]
                emit("T1S", {"site": site, "u": info_of(u), "side": side_of(u), "pra": cur["ra"] if cur else None, "c": c, "fr": frame()})
        return f

    def on_l1(tag, site, unit_reg):
        """A call of COLL_PatternMark or COLL_PatternUnmark at its call instruction: stdcall (room, x, y, pattern, mask) on the stack."""
        def f():
            u = reg(unit_reg)
            if not cap(tag, st["lines"], site, CAP_LINES):
                return
            room, x, y, pat, mask = struct.unpack("<5I", mem(reg("esp"), 20))
            emit(tag, {"site": site, "u": info_of(u), "side": side_of(u), "room": room, "x": x, "y": y, "pat": pat, "mask": mask, "c": st["lines"][site], "fr": frame()})
        return f

    def on_cor_in():
        esp = reg("esp")
        ra, unit, arg = struct.unpack("<3I", mem(esp, 12))
        st["cor"][esp] = (ra - 5, unit, arg)

    def on_cor_out():
        e = st["cor"].pop(reg("esp"), None)
        if e is None:
            return
        site, u, arg = e
        if not cap("cor", st["lines"], ("cor", site), CAP_LINES):
            return
        p = u32(u + 0x2C)
        x, y = u16(p + 2), u16(p + 6)
        room = u32(p + 0x1C)
        after = [cell_at(room, x + dx, y + dy) for dy in range(-2, 3) for dx in range(-2, 3)]
        emit("COR", {"site": site, "u": info_of(u), "side": side_of(u), "arg": arg, "x": x, "y": y, "room": room, "after": after, "pat": s32(p + 0x48), "mask": u32(p + 0x4C),
                     "c": st["lines"][("cor", site)], "fr": frame()})

    Bp(0x0052C312, on_game)
    Bp(0x00649970, on_pln)
    Bp(0x00649BAE, on_plc)
    for a in RETS:
        Bp(a, on_plx)
    for a in BRK:
        Bp(a, on_brk(a))
    for a in S3C:
        Bp(a, on_s3c(a))
    Bp(0x0067A1AF, on_spx)
    Bp(0x0067A1E0, on_spx)
    for a in T1S:
        Bp(a, on_t1s(a))
    for a in L1M:
        Bp(a, on_l1("L1M", a, L1M[a]))
    for a in L1U:
        Bp(a, on_l1("L1U", a, "edi"))
    Bp(0x00649F70, on_cor_in)
    Bp(0x00649FB2, on_cor_out)
    Bp(0x00649FE6, on_cor_out)
    gdb.write("PATH logger armed rev %d\n" % REV)


_path_main()
