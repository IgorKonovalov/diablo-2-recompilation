# gdb Python logger for plan 0022 Phase 2 (maze generator, act links, warp points). Sourced by
# tools/gdb/drlg-maze.gdb after tools/gdb/drlg-gen.py (whose LC0/LI0/LI1/RC/RL/PIC/MFR/PRC/MZ0/MZ1 lines it
# complements). One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000).
# Seeds are printed "lo:hi".
#
#   MZA   0x00673B41  maze build after its first DRLG_RoomCreate (ESI = level): the act fields the maze reads
#                     (+0x450 difficulty, +0x480 act index, +0x094/+0x484 the two tombs), the level's rect, and for
#                     level 28 the rect and preset index of level 27, for level 107 the rect of level 108
#   MZD   hardware write watchpoint on the level seed (+0x1C4) from MZA to MZ1: every level-seed step in the maze
#                     window, with $pc, [esp], [ebp+4] and the new seed
#   MZF   0x0066C100  DRLG_RoomFree entry (ECX = room) while a maze window is open: the room and its rect
#   LNK0  0x006772C0  sub_006772C0_LevelLinkBuild entry (ESI = act): table, act index, difficulty, act seed
#   LNKL  0x006774FC  after each level's rect (and town / level-27 index) write: level id, rect, preset index
#   LK27  0x006774F9  the level-27 index write (EAX index): act seed after the draw (drlg-preset.py logs it as L27X)
#   LNK1  0x006775B2  the builder's exit: the LinkBuild struct at [ebp-0x204] (seed copy, 15 rects, dir, dir0,
#                     step, flip0) and the act seed
#   LNKS  0x00642F31 / 0x0066B043  after sub_00678AD0_ActLinkInit returns: the act's +0x90 LevelLinks list
#   LWP   0x006424E8 / 0x00642500 / 0x00642518  sub_006424A0_LevelInit after sub_006423D0_LevelWarpPointsBuild
#                     (EDI = level): the room list in list order (rect, type, flags +0x28, preset Def and index)
#                     and the warp points +0x1E0 x[9], +0x204 y[9], +0x228 count
#   WPR   0x0066BF1C  sub_0066BE80_WarpPairRoomFind, before RoomWarpNodeAdd (EDI source room, ESI paired room, EBX the
#                     paired slot's flag 0x10 << j, [ebp+0xC] the source slot m): the pairing sub_0066C220 found
#   OBJP  0x0066EE40  at each room activation: server objects not listed yet (portal classes 59, 60, 342 each unit,
#                     every other class once per level)
#                     (game unit table +0x1520, type 2; static path +0x0C/+0x10), for the pilot to find the Act V
#                     red portals; nothing here feeds a model
import json
import struct

import gdb


def _maze_main():
    inf = gdb.selected_inferior()
    st = {"win": {}, "act": 0}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def rect(p):
        return list(struct.unpack("<iiii", mem(p, 16)))

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:
                gdb.write("LOGERR maze %r\n" % (e,))
            return False

    class SeedWatch(gdb.Breakpoint):
        def __init__(self, level):
            super().__init__("*(int *) 0x%08X" % (level + 0x1C4), gdb.BP_WATCHPOINT, gdb.WP_WRITE, internal=True)
            self.silent = True
            self.level = level

        def stop(self):
            try:
                esp, ebp = reg("esp"), reg("ebp")
                try:
                    r1 = u32(ebp + 4)
                except gdb.MemoryError:
                    r1 = None
                emit("MZD", {"level": self.level, "pc": int(gdb.parse_and_eval("$pc")) & 0xFFFFFFFF, "esp0": u32(esp),
                             "ret1": r1, "seed": sd(self.level + 0x1C4)})
            except Exception as e:
                gdb.write("LOGERR maze %r\n" % (e,))
            return False

    def level_by_id(act, lid):
        # the act's level list as sub_00642BB0_LevelEnsure walks it: head act +0x47C, next level +0x1AC
        lv = u32(act + 0x47C)
        k = 0
        while lv and k < 256:
            if u32(lv + 0x1D0) == lid:
                return lv
            lv = u32(lv + 0x1AC)
            k += 1
        return 0

    def on_mza():
        lv = reg("esi")
        act = u32(lv + 0x1B4)
        d = {"level": lv, "id": u32(lv + 0x1D0), "client": u32(act + 0x478), "diff": mem(act + 0x450, 1)[0],
             "acti": mem(act + 0x480, 1)[0], "tomb94": s32(act + 0x94), "tomb484": s32(act + 0x484),
             "rect": rect(lv + 0x1C), "seed": sd(lv + 0x1C4)}
        for nid in (27, 108):
            n = level_by_id(act, nid)
            if n:
                pd = u32(n + 0x14)
                d["l%d" % nid] = {"rect": rect(n + 0x1C), "drlg": u32(n),
                                  "idx": s32(pd + 4) if pd and u32(n) == 2 else None}
        emit("MZA", d)
        old = st["win"].pop(lv, None)
        if old:
            old.delete()
        st["win"][lv] = SeedWatch(lv)

    def on_mz1_end():
        lv = reg("esi")
        w = st["win"].pop(lv, None)
        if w:
            w.delete()

    def on_mzf():
        r = reg("ecx")
        lv = u32(r + 0x58)
        if lv in st["win"]:
            emit("MZF", {"level": lv, "room": r, "rect": rect(r + 0x34)})

    def on_lnk0():
        act = reg("esi")
        st["lnk"] = act
        emit("LNK0", {"act": act, "table": u32(reg("esp") + 4), "acti": mem(act + 0x480, 1)[0],
                      "diff": mem(act + 0x450, 1)[0], "client": u32(act + 0x478), "seed": sd(act)})

    def on_lnkl():
        lv = reg("ebx")
        pd = u32(lv + 0x14)
        emit("LNKL", {"act": reg("esi"), "id": u32(lv + 0x1D0), "rect": rect(lv + 0x1C), "drlg": u32(lv),
                      "idx": s32(pd + 4) if pd and u32(lv) == 2 else None, "aseed": sd(reg("esi"))})

    def on_l27x():
        act = reg("esi")
        eax = reg("eax")
        emit("LK27", {"act": act, "idx": eax - (1 << 32) if eax & 0x80000000 else eax, "pd": reg("ecx"), "seed": sd(act)})

    def on_lnk1():
        ebp = reg("ebp")
        b = ebp - 0x204
        rects = [list(struct.unpack_from("<iiii", mem(b + 8, 240), 16 * i)) for i in range(15)]
        arr = lambda off: list(struct.unpack("<15i", mem(b + off, 60)))
        emit("LNK1", {"act": reg("esi"), "bseed": sd(b), "rects": rects, "dir": arr(0xFC), "dir0": arr(0x138),
                      "step": arr(0x174), "flip0": arr(0x1B0), "seed": sd(reg("esi"))})

    def on_linkinit():
        st["act"] = reg("ecx")

    def on_lnks():
        act = st["act"]
        out, n, k = [], u32(act + 0x90), 0
        while n and k < 256:
            v = list(struct.unpack("<17i", mem(n, 0x44)))
            out.append([v[0], v[1:9], v[9:17]])
            n = u32(n + 0x44)
            k += 1
        emit("LNKS", {"act": act, "acti": mem(act + 0x480, 1)[0], "client": u32(act + 0x478), "seed": sd(act),
                      "links": out})

    def on_lwp():
        lv = reg("edi")
        rooms, r, k = [], u32(lv + 0x10), 0
        while r and k < 4096:
            pr = u32(r + 0x20) if u32(r + 0x48) == 2 else 0
            rooms.append([r, u32(r + 0x48)] + rect(r + 0x34) + [u32(r + 0x28), s32(pr) if pr else None,
                                                                 s32(pr + 4) if pr else None])
            r = u32(r + 0x24)
            k += 1
        n = s32(lv + 0x228)
        emit("LWP", {"level": lv, "id": u32(lv + 0x1D0), "client": u32(u32(lv + 0x1B4) + 0x478), "n": n,
                     "xs": list(struct.unpack("<9i", mem(lv + 0x1E0, 36))),
                     "ys": list(struct.unpack("<9i", mem(lv + 0x204, 36))), "rooms": rooms})

    def on_wpr():
        src, dst, ebp = reg("edi"), reg("esi"), reg("ebp")
        emit("WPR", {"src": src, "slv": u32(u32(src + 0x58) + 0x1D0), "m": mem(ebp + 0xC, 1)[0], "dst": dst,
                     "dlv": u32(u32(dst + 0x58) + 0x1D0), "dmask": reg("ebx"), "srect": rect(src + 0x34), "drect": rect(dst + 0x34)})

    seen = set()

    def on_game():
        st["game"] = reg("edi")

    def on_objp():
        g = st.get("game")
        if not g:
            return
        heads = struct.unpack("<128I", mem(g + 0x1520, 512))
        for u in heads:
            k = 0
            while u and k < 512:
                k += 1
                try:
                    cls = s32(u + 4)
                    sp = u32(u + 0x2C)
                    room = u32(sp) if sp else 0
                    lid = u32(u32(u32(room + 0x10) + 0x58) + 0x1D0) if room and u32(room + 0x10) else None
                    key = u if cls in (59, 60, 342) else (cls, lid)
                    if key not in seen:
                        seen.add(key)
                        emit("OBJP", {"unit": u, "cls": cls, "x": s32(sp + 0x0C) if sp else None, "y": s32(sp + 0x10) if sp else None,
                                      "mode": u32(u + 0x10), "lid": lid})
                except gdb.MemoryError:
                    pass
                u = u32(u + 0xE4)

    for a, f in [(0x0052C312, on_game), (0x0066EE40, on_objp), (0x0066BF1C, on_wpr), (0x00673B41, on_mza), (0x00673F44, on_mz1_end), (0x0066C100, on_mzf), (0x006772C0, on_lnk0),
                 (0x006774FC, on_lnkl), (0x006774F9, on_l27x), (0x006775B2, on_lnk1), (0x00678AD0, on_linkinit),
                 (0x00642F31, on_lnks), (0x0066B043, on_lnks), (0x006424E8, on_lwp), (0x00642500, on_lwp),
                 (0x00642518, on_lwp)]:
        Bp(a, f)
    gdb.write("MAZE logger armed\n")


_maze_main()
