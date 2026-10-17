# gdb Python logger for plan 0040 Phase 2 (room lifecycle): activation, release, the inactive records and the
# restore, and the wanderer gate, as docs/findings/drlg/0009-room-lifecycle.md reads them. Sourced by
# tools/gdb/rooms.gdb after tools/gdb/pilot.py (the PLR/MON/CB/RL lines tools/d2pilot.py steers by). One line per
# event, "TAG {json}"; every line carries "f", the game frame (game +0xA8) when the game pointer is known. Addresses
# refer to the pinned game.exe (image base 0x400000). Seeds are "low:high" hex. Rooms: "r" an active (DUNGEON) room,
# "d" a DRLG room, both as pointers. Only the server copy is logged unless a line says otherwise ("cl" = the DRLG
# act's +0x8C bit 0, 1 on the client act).
#
#   GP     0x0052C312 (GAME_InitSeeds, EDI = game): the game pointer (RP also sets it from its argument)
#   RM0    0x0061A12B (the DrlgRefMove call in its wrapper 0x0061A110: ECX old, EDX new DRLG room; caller [ebp+4]):
#          the DRLG rooms within four near-list steps of old and new, each [refs0..3, status, +0x28, +0x30, type
#          +0x48, level id, near list] ("s")
#   RMX    0x0061A130 (its return): the same snapshot over the RM0 rooms and the BFS from old and new again
#   RCB    the reference callbacks g_DrlgRefEnterFns 0x00744384 (e0 0x0061B2C0, e1 0x0061B2D0, e2 0x0061BB10,
#          e3 0x0061B320) and g_DrlgRefLeaveFns 0x00744394 (l0 0x0061B530, l1 0x0061B540, l2 0x0061B550,
#          l3 0x0061B560), ECX = DRLG room, at entry: refs, status, +0x28, +0x30, type; "in" = inside an RM0..RMX
#   ACTA   0x0061B190 RoomActivateA (ESI = DRLG room)
#   RAB    0x0061B730 RoomActivateB (ECX = DRLG room): +0x28, +0x30, status, caller (an input of the model)
#   DRA    0x006422A0 DRLG_RoomActivate (ECX = DRLG act, EDX = DRLG room)
#   CRC    0x00537BC6 in ClientRoomChange 0x00537B50 (ESI = client, [ebp+8] = new active room; old = client +0x1B4),
#          after the reference moves, when the function goes on (client +0x1A8 set, old != new): the near lists
#          DUNGEON_GetNearRooms gave for new ([ebp-0x10], [ebp-4]) and old ([ebp-0xC], [ebp-8])
#   CE/CL  0x0053A8E0 RoomClientEnter / 0x0053A9B0 RoomClientLeave (EDX = room, [esp+4] = client): +0x78 before
#   RP     0x0052D240 RoomsDeactivate entry ([esp+4] = game): per act (game +0xBC + 4 a, act +0x50) its active rooms
#          from act +0x10 (next +0x7C): [room, drlg, +0x0C idle, +0x78, +0x34, status, DRLG +0x28, level id, the
#          lowest status of the level's DRLG rooms (level +0x10, next +0x24) for a town or level 120, else null];
#          the game's difficulty (+0x6D) and expansion flag (+0x70)
#   RT     0x0052D289 the release test's result (EAX) for a room with idle > 10 (EDI)
#   FREE   0x0052D2BB ActiveRoomFree's call (EDI = room)
#   TR0    0x0066F1A0 RoomTilesRelease (ECX = DRLG room, EDX): cl, +0x28, +0x30; TRX 0x0066F239 its end: +0x28
#   US     0x00543403 InactiveUnitSaveTest after its room lookup (ESI = unit, EAX = room): type, class, id, mode,
#          +0xC4, +0xC8, +0xD0, x, y, room, level, room seed, monster flags, mods, stats 6 7 12 13
#   USD    the decision: monsters at 0x005433A7 (EDI save, [ebp-0xC] kept) with the sub-results of the save test as
#          inputs: dead 0x00543212, SaveMonsters 0x0054322F, the mode-12 draw 0x00543287 (remainder, seed out), udead
#          0x0054329D, alignment 0x005432A9, MonTypeFlag(0x18) 0x005432FB, owner 0x00543317, pet 0x0054332D,
#          MonStats2 restore 0x00543396; other units at 0x005434B4 / 0x005434D6 (kept) with SaveMonsters 0x00543430,
#          Objects Restore/RestoreVirgins 0x00543468, sparkle 0x00543478, state 7 0x005434D2
#   MREC   0x005424E1 the monster record (EDI, 0x5C bytes) and its room record x, y; "in": the alignment
#          (0x0054236D) and UnitGetMaxHp (0x005423E1) the record took, as value oracles
#   UREC   0x00543072 the unit record (ESI, 0x34 bytes)
#   IS0    0x00541B10 InactiveItemSave entry (EDI = item); IREC 0x00541B71 after ItemGroundExpiry: expiry, the
#          serialised bytes, and the expiry inputs (0x00558A1C quest, 0x00558A2B quality, 0x00558A4C base type,
#          0x00558A5B stat 14, 0x00558A76 socket filler)
#   RS0    0x00542B40 RoomInactiveUnitsRestore (ECX = game, EDX = room): game and room seeds; RSM 0x00542B58 after
#          the monsters; RSI 0x00542B78 after the items; RSX 0x00542B7F / 0x00542DD8 its returns
#   MR0    0x00542563 per monster record (EBX): the record bytes, game and room seeds
#   MP     the creation calls 0x00542689 (minion), 0x005426C3 (special), 0x005426E9 (exact), 0x00542717 (radius 5),
#          0x00542761 (SpawnPosPick), 0x005427B1 (free spiral)
#   MRC    0x005427B8 after creation (ESI = unit or 0): seeds, the unit's id, class, mode, x, y, seed, +0x28
#   MRS    0x0054284F after the stat writes: stats 6 7 12 13
#   MRE    0x00542954 before MonRegionUnitLeave: stats, +0xC4/+0xC8, alignment arg, region counts (game +0xF0)
#   MRX    0x00542959 the record's end (after MonRegionUnitLeave, or a dropped record): region counts
#   IL     0x00541AC0 InactiveItemsRestore entry (EAX = list): [rec, expiry, bytes] per record
#   IR0    0x00541990 per item restored (EAX = rec); IRC 0x005419C8 (EAX = item); IRX 0x00541A07 (expiry written)
#   UR0    0x00542B89 per unit record (EDI, 0x34 bytes); URC 0x00542C33 (ESI = created unit); URK 0x00542BB0 (kept)
#   WG     0x0054F089 the wanderer gate's draw (ESI = room; seed in from memory, out in EAX/EDX), +0x78, +0x34
#   WR     0x0054EFF0 WandererRoll entry; WS 0x0054EF50 WandererSpawn entry
#   POP    0x0054EC90 RoomPopulate entry (EDX = room)
#   PSU0   0x00555963 PresetUnitSpawn, type 1 (ESI = &preset +0x10, EAX = &AI control +0x38); PSUX 0x00555971 after
#          PtrMove: the preset's +0x10 and the AI control's +0x38
#   PIN    0x0061BAC0 DrlgRoomPinFlag (ECX = DRLG room, EDX: 0 set, else clear), callers
#   OBJP   every fifth RP: once per waypoint object (class, x, y, level), a harness helper for d2pilot.py wpchain
#   LOGERR on a handler exception (the game goes on)
import json
import struct

import gdb


def _rooms_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "inrm": False, "rm": None, "us": None, "is": None, "mr": None, "mre": None, "ir": None,
          "psu": None, "lv": {}}
    M32 = 0xFFFFFFFF

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
        return int(gdb.parse_and_eval("$" + n)) & M32

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def seed(a):
        return "%08x:%08x" % struct.unpack("<II", mem(a, 8)) if a else None

    def frame():
        g = st["game"]
        try:
            return u32(g + 0xA8) if g else None
        except gdb.MemoryError:
            return None

    def emit(tag, d):
        d["f"] = frame()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def level_info(lvl):
        """(level id, client flag) of a DRLG level pointer, cached."""
        v = st["lv"].get(lvl)
        if v is None:
            v = (s32(lvl + 0x1D0), u32(u32(lvl + 0x1B4) + 0x8C) & 1)
            st["lv"][lvl] = v
        return v

    def droom(d):
        """[refs0..3, status, +0x28, +0x30, type, level id, client, near list] of a DRLG room."""
        b = mem(d, 0x60)
        near, = struct.unpack_from("<I", b, 8)
        refs = list(struct.unpack_from("<4H", b, 0x0C))
        fl, nn, a30 = struct.unpack_from("<IiI", b, 0x28)
        status = b[0x44]
        ty, = struct.unpack_from("<I", b, 0x48)
        lvl, = struct.unpack_from("<I", b, 0x58)
        lid, cl = level_info(lvl) if lvl else (None, None)
        nl = list(struct.unpack("<%dI" % nn, mem(near, 4 * nn))) if near and 0 < nn <= 64 else []
        return refs + [status, fl, a30, ty, lid, cl, nl]

    def snap(seeds, extra=(), depth=4):
        out = {}
        front = [d for d in seeds if d]
        for d in front:
            out.setdefault(d, None)
        k = 0
        while front and k <= depth:
            nxt = []
            for d in front:
                if out.get(d) is None:
                    out[d] = droom(d)
                if k < depth:
                    for n in out[d][10]:
                        if n not in out:
                            out[n] = None
                            nxt.append(n)
            front = nxt
            k += 1
        for d in extra:
            if d and d not in out:
                out[d] = droom(d)
        for d in list(out):
            if out[d] is None:
                out[d] = droom(d)
        return {str(k): v for k, v in out.items()}

    def stats(u, ids=(6, 7, 12, 13)):
        """STATS_GetUnitStat-style reads (the full list when StatList +0x10 bit 31 is set, else the base list)."""
        lst = u32(u + 0x5C) if u else 0
        if not lst:
            return {}
        if u32(lst + 0x10) & 0x80000000:
            arr, n = u32(lst + 0x48), s16(lst + 0x4C)
        else:
            arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 2048:
            return {}
        want = {i << 16: i for i in ids}
        out = {}
        for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n)):
            if k in want:
                out[str(want[k])] = v
        return out

    def pos(u):
        t = u32(u)
        p = u32(u + 0x2C)
        if not p:
            return None, None
        if t in (2, 4, 5):
            return u32(p + 0x0C), u32(p + 0x10)
        return u16(p + 2), u16(p + 6)

    def regions(lids):
        g = st["game"]
        out = {}
        for lid in lids:
            if lid is None or not (0 <= lid < 0x400):
                continue
            r = u32(g + 0xF0 + 4 * lid)
            out[str(lid)] = list(struct.unpack("<3i", mem(r + 0x2C4, 12))) if r else None
        return out

    def room_level(r):
        d = u32(r + 0x10) if r else 0
        lvl = u32(d + 0x58) if d else 0
        return level_info(lvl)[0] if lvl else None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error
                gdb.write("LOGERR rooms 0x%08X %r\n" % (self.location_addr, e))
            return False

    def bp(addr):
        def deco(fn):
            b = Bp(addr, fn)
            b.location_addr = addr
            return fn
        return deco

    # ---- the game pointer
    @bp(0x0052C312)
    def _gp():
        st["game"] = reg("edi")
        st["lv"] = {}
        emit("GP", {"game": st["game"]})

    # ---- references and activation
    @bp(0x0061A12B)
    def _rm0():
        old, new = reg("ecx"), reg("edx")
        st["inrm"] = True
        s = snap([old, new])
        st["rm"] = (old, new, [int(k) for k in s])
        emit("RM0", {"old": old, "new": new, "caller": u32(reg("ebp") + 4), "s": s})

    @bp(0x0061A130)
    def _rmx():
        st["inrm"] = False
        if not st["rm"]:
            return
        old, new, keys = st["rm"]
        st["rm"] = None
        emit("RMX", {"old": old, "new": new, "s": snap([old, new], keys)})

    def cb(kind):
        def fn():
            d = reg("ecx")
            v = droom(d)
            if v[9]:
                return
            emit("RCB", {"k": kind, "d": d, "refs": v[:4], "st": v[4], "fl": v[5], "a30": v[6], "ty": v[7],
                        "lid": v[8], "in": st["inrm"]})
        return fn

    for a, k in ((0x0061B2C0, "e0"), (0x0061B2D0, "e1"), (0x0061BB10, "e2"), (0x0061B320, "e3"),
                 (0x0061B530, "l0"), (0x0061B540, "l1"), (0x0061B550, "l2"), (0x0061B560, "l3")):
        bp(a)(cb(k))

    @bp(0x0061B190)
    def _acta():
        d = reg("esi")
        v = droom(d)
        if not v[9]:
            emit("ACTA", {"d": d, "lid": v[8], "in": st["inrm"]})

    @bp(0x0061B730)
    def _rab():
        d = reg("ecx")
        v = droom(d)
        if not v[9]:
            emit("RAB", {"d": d, "lid": v[8], "fl": v[5], "a30": v[6], "st": v[4], "caller": u32(reg("esp")),
                         "in": st["inrm"]})

    @bp(0x006422A0)
    def _dra():
        d = reg("edx")
        v = droom(d)
        if not v[9]:
            emit("DRA", {"d": d, "lid": v[8], "pop": u32(d + 0x60), "caller": u32(reg("esp"))})

    # ---- client lists
    def lst(p, n):
        return list(struct.unpack("<%dI" % n, mem(p, 4 * n))) if p and 0 < n <= 64 else []

    @bp(0x00537BC6)
    def _crc():
        c, ebp = reg("esi"), reg("ebp")
        new = u32(ebp + 8)
        old = u32(c + 0x1B4)
        emit("CRC", {"c": c, "old": old, "new": new, "od": u32(old + 0x10) if old else 0,
                     "nd": u32(new + 0x10) if new else 0, "on": lst(u32(ebp - 0xC), s32(ebp - 8)),
                     "nn": lst(u32(ebp - 0x10), s32(ebp - 4)), "lid": room_level(new)})

    @bp(0x0053A8E0)
    def _ce():
        r = reg("edx")
        emit("CE", {"r": r, "c": u32(reg("esp") + 4), "n78": u32(r + 0x78)})

    @bp(0x0053A9B0)
    def _cl():
        r = reg("edx")
        emit("CL", {"r": r, "c": u32(reg("esp") + 4), "n78": u32(r + 0x78)})

    # ---- the release pass
    @bp(0x0052D240)
    def _rp():
        g = u32(reg("esp") + 4)
        if not st["game"]:
            st["game"] = g
        acts = []
        lvmin = {}
        for a in range(5):
            act = u32(g + 0xBC + 4 * a)
            if not act:
                acts.append(None)
                continue
            rooms = []
            r = u32(act + 0x10)
            k = 0
            while r and k < 2000:
                b = mem(r, 0x80)
                idle, d = struct.unpack_from("<II", b, 0x0C)
                fl34, = struct.unpack_from("<I", b, 0x34)
                n78, nxt = struct.unpack_from("<II", b, 0x78)
                db = mem(d, 0x60)
                status = db[0x44]
                fl28, = struct.unpack_from("<I", db, 0x28)
                lvl, = struct.unpack_from("<I", db, 0x58)
                lid = level_info(lvl)[0]
                mn = None
                if lid in (1, 40, 75, 103, 109, 120):
                    if lvl not in lvmin:
                        m, x, j = 9, u32(lvl + 0x10), 0
                        while x and j < 4000:
                            m = min(m, u8(x + 0x44))
                            x = u32(x + 0x24)
                            j += 1
                        lvmin[lvl] = m
                    mn = lvmin[lvl]
                rooms.append([r, d, idle, n78, fl34, status, fl28, lid, mn])
                r = nxt
                k += 1
            acts.append({"a50": u32(act + 0x50), "rooms": rooms})
        emit("RP", {"acts": acts, "diff": u8(g + 0x6D), "exp": u32(g + 0x70)})
        st["np"] = st.get("np", 0) + 1
        if st["np"] % 5 == 0:
            wp_scan(g)

    WP_CLASSES = {119, 145, 156, 157, 237, 238, 288, 323, 324, 398, 402, 429, 494, 496, 511, 539}

    def wp_scan(g):
        """Harness helper, not a model input: OBJP once per waypoint object (tools/d2pilot.py wpchain clicks it)."""
        for u in struct.unpack("<128I", mem(g + 0x1520, 512)):
            k = 0
            while u and k < 512:
                k += 1
                try:
                    cls = s32(u + 4)
                    if cls in WP_CLASSES:
                        sp = u32(u + 0x2C)
                        room = u32(sp) if sp else 0
                        lid = room_level(room) if room else None
                        if sp and (cls, lid) not in st.setdefault("wps", set()):
                            st["wps"].add((cls, lid))
                            emit("OBJP", {"unit": u, "cls": cls, "x": s32(sp + 0x0C), "y": s32(sp + 0x10),
                                          "mode": u32(u + 0x10), "lid": lid})
                except gdb.MemoryError:
                    pass
                u = u32(u + 0xE4)

    @bp(0x0052D289)
    def _rt():
        emit("RT", {"r": reg("edi"), "ok": reg("eax")})

    @bp(0x0052D2BB)
    def _free():
        r = reg("edi")
        emit("FREE", {"r": r, "d": u32(r + 0x10)})

    @bp(0x0066F1A0)
    def _tr0():
        d = reg("ecx")
        v = droom(d)
        emit("TR0", {"d": d, "edx": reg("edx"), "cl": v[9], "fl": v[5], "a30": v[6], "lid": v[8]})

    @bp(0x0066F239)
    def _trx():
        d = reg("esi")
        emit("TRX", {"d": d, "fl": u32(d + 0x28), "cl": droom(d)[9]})

    # ---- the save test
    @bp(0x00543403)
    def _us():
        u, r = reg("esi"), reg("eax")
        t = u32(u)
        x, y = pos(u)
        d = {"u": u, "t": t, "c": s32(u + 4), "id": u32(u + 0x0C), "m": u32(u + 0x10), "c4": u32(u + 0xC4),
             "c8": u32(u + 0xC8), "x": x, "y": y, "r": r, "lid": room_level(r), "rs": seed(r + 0x6C) if r else None}
        if t == 1:
            md = u32(u + 0x14)
            d["d0"] = s32(u + 0xD0)
            d["mf"] = u16(md + 0x16) if md else None
            d["mods"] = list(mem(md + 0x1C, 9)) if md else None
            d["st"] = stats(u)
        st["us"] = {"u": u, "t": t, "sub": {}}
        emit("US", d)

    def sub(name, fn):
        def h():
            if st["us"] is not None:
                st["us"]["sub"][name] = fn()
        return h

    bp(0x00543212)(sub("dead", lambda: reg("eax")))
    bp(0x0054322F)(sub("sm", lambda: reg("eax")))
    bp(0x00543287)(sub("draw", lambda: [reg("ecx"), seed(reg("edi"))]))
    bp(0x0054329D)(sub("ud", lambda: reg("eax")))
    bp(0x005432A9)(sub("al", lambda: reg("eax")))
    bp(0x005432FB)(sub("mt18", lambda: reg("eax")))
    bp(0x00543317)(sub("own", lambda: [reg("eax"), u32(reg("eax")) if reg("eax") else None]))
    bp(0x0054332D)(sub("pet", lambda: reg("eax")))
    bp(0x00543396)(sub("rb", lambda: reg("eax") & 0xFF))
    bp(0x00543430)(sub("sm", lambda: reg("eax")))
    bp(0x00543468)(sub("orow", lambda: [u8(reg("ebx") + 0x173), u8(reg("ebx") + 0x174)]))
    bp(0x00543478)(sub("spk", lambda: reg("eax") & 0xFF))
    bp(0x005434D2)(sub("s7", lambda: reg("eax")))

    def usd(kind):
        def h():
            e = st["us"]
            st["us"] = None
            if e is None:
                return
            d = {"u": e["u"], "t": e["t"], "k": kind, "sub": e["sub"]}
            ebp = reg("ebp")
            if kind == "mon":
                d["save"] = reg("edi")
                d["kept"] = u32(ebp - 0xC)
            elif kind == "oth":
                d["flag"] = u32(ebp - 4)
            emit("USD", d)
        return h

    bp(0x005433A7)(usd("mon"))
    bp(0x005434B4)(usd("oth"))
    bp(0x005434D6)(usd("kept"))

    # ---- records
    def msave(name):
        def h():
            st.setdefault("ms", {})[name] = reg("eax")
        return h

    bp(0x0054236D)(msave("al"))
    bp(0x005423E1)(msave("maxhp"))

    @bp(0x005424E1)
    def _mrec():
        rec, rr = reg("edi"), reg("eax")
        emit("MREC", {"rec": rec, "b": mem(rec, 0x5C).hex(), "rx": s32(rr), "ry": s32(rr + 4), "in": st.pop("ms", {})})

    @bp(0x00543072)
    def _urec():
        rec, rr = reg("esi"), reg("ebx")
        emit("UREC", {"rec": rec, "b": mem(rec, 0x34).hex(), "rx": s32(rr), "ry": s32(rr + 4)})

    @bp(0x00541B10)
    def _is0():
        it = reg("edi")
        x, y = pos(it)
        st["is"] = {"it": it, "sub": {}}
        emit("IS0", {"it": it, "id": u32(it + 0x0C), "c": s32(it + 4), "x": x, "y": y, "s": seed(it + 0x20),
                     "u28": u32(it + 0x28), "m": u32(it + 0x10)})

    def isub(name):
        def h():
            if st["is"] is not None:
                st["is"]["sub"][name] = reg("eax")
        return h

    for a, k in ((0x00558A1C, "quest"), (0x00558A2B, "q"), (0x00558A4C, "bt"), (0x00558A5B, "gold"),
                 (0x00558A76, "filler")):
        bp(a)(isub(k))

    @bp(0x00541B71)
    def _irec():
        e = st["is"]
        st["is"] = None
        ebp = reg("ebp")
        n = u16(ebp - 0x408)
        emit("IREC", {"it": e["it"] if e else None, "exp": reg("eax"), "n": n,
                      "b": mem(ebp - 0x406, n).hex() if 0 < n <= 0x400 else None, "sub": e["sub"] if e else None})

    # ---- the restore
    @bp(0x00542B40)
    def _rs0():
        g, r = reg("ecx"), reg("edx")
        emit("RS0", {"r": r, "d": u32(r + 0x10), "lid": room_level(r), "gs": seed(g + 0xD0), "rs": seed(r + 0x6C)})

    def rsx(tag, rreg):
        def h():
            g = st["game"]
            r = u32(reg("ebp") - 0x14) if rreg is None else reg(rreg)
            emit(tag, {"r": r, "gs": seed(g + 0xD0), "rs": seed(r + 0x6C) if r else None})
        return h

    bp(0x00542B58)(rsx("RSM", "esi"))
    bp(0x00542B78)(rsx("RSI", None))
    bp(0x00542B7F)(rsx("RSX", None))
    bp(0x00542DD8)(rsx("RSX", None))

    @bp(0x00542563)
    def _mr0():
        rec, g = reg("ebx"), reg("edi")
        r = u32(reg("ebp") + 8)
        st["mr"] = {"rec": rec, "path": [], "lid": room_level(r)}
        emit("MR0", {"rec": rec, "r": r, "b": mem(rec, 0x5C).hex(), "gs": seed(g + 0xD0), "rs": seed(r + 0x6C),
                     "lid": st["mr"]["lid"], "q23": u32(reg("ebp") - 0x18)})

    def mp(name):
        def h():
            if st["mr"] is not None:
                st["mr"]["path"].append(name)
        return h

    for a, k in ((0x00542689, "minion"), (0x005426C3, "special"), (0x005426E9, "exact"), (0x00542717, "r5"),
                 (0x00542761, "pick"), (0x005427B1, "spiral")):
        bp(a)(mp(k))

    @bp(0x005427B8)
    def _mrc():
        u, g = reg("esi"), st["game"]
        r = u32(reg("ebp") + 8)
        d = {"u": u, "gs": seed(g + 0xD0), "rs": seed(r + 0x6C), "path": st["mr"]["path"] if st["mr"] else None}
        if u:
            x, y = pos(u)
            md = u32(u + 0x14)
            d.update({"id": u32(u + 0x0C), "c": s32(u + 4), "m": u32(u + 0x10), "x": x, "y": y, "s": seed(u + 0x20),
                      "u28": u32(u + 0x28), "mf": u16(md + 0x16) if md else None,
                      "mods": list(mem(md + 0x1C, 9)) if md else None, "st": stats(u)})
        emit("MRC", d)

    @bp(0x0054284F)
    def _mrs():
        emit("MRS", {"u": reg("esi"), "st": stats(reg("esi"))})

    @bp(0x00542954)
    def _mre():
        u, esp = reg("esi"), reg("esp")
        cur, al, dead, f40 = struct.unpack("<iiii", mem(esp, 16))
        m58 = sreg("edx")
        md = u32(u + 0x14) if u else 0
        st["mre"] = (m58, cur)
        emit("MRE", {"u": u, "st": stats(u, (6, 7, 12, 13)), "c4": u32(u + 0xC4) if u else None,
                     "c8": u32(u + 0xC8) if u else None, "d0": s32(u + 0xD0) if u else None,
                     "mf": u16(md + 0x16) if md else None, "m58": m58, "cur": cur, "al": al, "dead": dead,
                     "f40": f40, "reg": regions([m58, cur])})

    @bp(0x00542959)
    def _mrx():
        e, st["mre"] = st["mre"], None
        st["mr"] = None
        emit("MRX", {"reg": regions(list(e)) if e else None, "dropped": e is None})

    @bp(0x00541AC0)
    def _il():
        lst = []
        x, k = reg("eax"), 0
        while x and k < 400:
            lst.append([x, s32(x + 4), u16(x + 0xC)])
            x = u32(x)
            k += 1
        emit("IL", {"recs": lst})

    @bp(0x00541990)
    def _ir0():
        rec = reg("eax")
        g = u32(reg("esp") + 4)
        n = u16(rec + 0xC)
        st["ir"] = rec
        emit("IR0", {"rec": rec, "exp": s32(rec + 4), "n": n, "b": mem(rec + 0xE, n).hex() if 0 < n <= 0x400 else None,
                     "gs": seed(g + 0xD0)})

    @bp(0x005419C8)
    def _irc():
        it = reg("eax")
        g = st["game"]
        d = {"rec": st["ir"], "it": it, "gs": seed(g + 0xD0)}
        if it:
            x, y = pos(it)
            d.update({"id": u32(it + 0x0C), "c": s32(it + 4), "x": x, "y": y, "s": seed(it + 0x20),
                      "u28": u32(it + 0x28), "m": u32(it + 0x10)})
        emit("IRC", d)

    @bp(0x00541A07)
    def _irx():
        it = reg("eax")
        emit("IRX", {"it": it, "exp": s32(u32(it + 0x14) + 0x24), "s": seed(it + 0x20)})

    @bp(0x00542B89)
    def _ur0():
        rec = reg("edi")
        emit("UR0", {"rec": rec, "b": mem(rec, 0x34).hex(), "gs": seed(st["game"] + 0xD0)})

    @bp(0x00542C33)
    def _urc():
        u = reg("esi")
        d = {"u": u}
        if u:
            x, y = pos(u)
            d.update({"t": u32(u), "c": s32(u + 4), "id": u32(u + 0x0C), "m": u32(u + 0x10), "x": x, "y": y})
        emit("URC", d)

    @bp(0x00542BB0)
    def _urk():
        u = reg("eax")
        d = {"u": u}
        if u:
            x, y = pos(u)
            d.update({"t": u32(u), "c": s32(u + 4), "id": u32(u + 0x0C), "m": u32(u + 0x10), "x": x, "y": y})
        emit("URK", d)

    # ---- the wanderer gate and the population
    @bp(0x0054F089)
    def _wg():
        r = reg("esi")
        sp = reg("ecx")
        emit("WG", {"r": r, "lid": room_level(r), "si": seed(sp), "so": "%08x:%08x" % (reg("eax"), reg("edx")),
                    "n78": u32(r + 0x78), "fl": u32(r + 0x34)})

    @bp(0x0054EFF0)
    def _wr():
        r = reg("eax")
        emit("WR", {"r": r, "rs": seed(r + 0x6C)})

    @bp(0x0054EF50)
    def _ws():
        r = reg("edi")
        emit("WS", {"r": r, "rs": seed(r + 0x6C) if r else None})

    @bp(0x0054EC90)
    def _pop():
        r = reg("edx")
        emit("POP", {"r": r, "rs": seed(r + 0x6C)})

    # ---- the preset path detach
    @bp(0x00555963)
    def _psu0():
        p = reg("esi")
        st["psu"] = (p, reg("eax"))
        emit("PSU0", {"pp": u32(p), "ai": reg("eax")})

    @bp(0x00555971)
    def _psux():
        e, st["psu"] = st["psu"], None
        if e:
            emit("PSUX", {"pp": u32(e[0]), "ai38": u32(e[1]) if e[1] else None})

    # ---- pins
    @bp(0x0061BAC0)
    def _pin():
        d = reg("ecx")
        esp = reg("esp")
        caller = u32(esp)
        outer = u32(reg("ebp") + 4) if caller == 0x0061AEE5 else None
        v = droom(d)
        emit("PIN", {"d": d, "arg": reg("edx"), "caller": caller, "outer": outer, "cl": v[9], "lid": v[8],
                     "fl": v[5]})

    gdb.write("ROOMS logger armed\n")


_rooms_main()
