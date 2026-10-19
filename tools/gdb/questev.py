# gdb Python logger for plan 0042 Phase 2 (quests and travel): the quest dispatch and its callbacks, the join, the
# travel events bracketed at entry and exit with the seeds, the two real-time gates, the level-point lookups and the
# free-cell searches of a travel event, as docs/findings/quests/0001-progression.md and 0002-travel.md read them.
# Sourced by tools/gdb/quest-state.gdb after tools/gdb/pilot.py, tools/gdb/vendors.py and tools/gdb/quests.py (QS/QC:
# every quest-bit write; QI1: the quest seed and the game record). One line per event, "TAG {json}"; every line
# carries "f", the game frame (game +0xA8). Addresses refer to the pinned game.exe (image base 0x400000). Seeds are
# "low:high" hex: "gs" the game seed (game +0xD0), "qs" the quest seed (game +0x10F4 -> +0x18), "ps" the player's unit
# seed (unit +0x20). Units are [type, class, id].
#
#   EV     one line at the entry ("ph": 0) and one at each return ("ph": 1) of an event function, matched by the stack
#          pointer (the return instructions are the function's own `ret`s, listed from objdump of the pinned image:
#          `objdump -d --no-show-raw-insn -M intel game.exe`, from the function start to its int3 padding). "k" names
#          the event; both lines carry gs, qs, ps; the entry line the event's inputs, the exit line its outputs.
#     k        entry       rets                                    inputs (ECX/EDX/stack)
#     de       0x005438E0  0x00543974 (its ret 8)                  EDI block; [esp+4] force, [esp+8] act filter; also
#                                                                  every quest object [id, act, +0x09, +0x0A, +0x0B,
#                                                                  word] in list order and the ids whose slot is set
#                                                                  ("slots"); for NPC 331 quest 11's private +0x0E
#     due      0x005439A0  0x00543A05                              EDI block; [esp+4] force
#     join     0x00546270  0x0054666F 0x005466A4                   ECX game, EDX player, [esp+4] rejoin
#     p49      0x0054C5D0  0x0054C5E7 0x0054C630 0x0054C675 0x0054C68A  ECX game, EDX player, [esp+4] packet
#     p48      0x0054C590  0x0054C5A3 0x0054C5B9 0x0054C5C7        ECX game, EDX player
#     p58      0x0054C9C0  0x0054C9F9 0x0054CA04                   ECX game, EDX player, [esp+4] packet (u16 word +1)
#     p41      0x0054C0E0  0x0054C0FC 0x0054C148 0x0054C293        ECX game, EDX player
#     wpop     0x00584E30  0x00584F51                              ECX ctx {game, object, player}
#     wptr     0x00584F60  0x00585113                              ECX game, EDX player, [esp+4] object id, [esp+8] level
#     portal   0x00584870  0x005848E6 0x00584A38 0x00584CF3        ECX ctx (OperateFn 15)
#     lvlportal 0x00584D00 0x00584E22                              ECX ctx (OperateFn 43)
#     arcane   0x005846B0  0x00584707 0x0058472A 0x0058474D        ECX ctx (OperateFn 34)
#     durance  0x00584750  0x00584817                              ECX ctx (OperateFn 46)
#     orb      0x005BB980  0x005BBB55 0x005BBB6B                   ECX ctx (OperateFn 53): mode, weapon code, counter
#     tp       0x005BE290  0x005BE2AC 0x005BE3CB 0x005BE3E3        ECX game, EDX player (g_ItemUseFns[2].use)
#     pocreate 0x0056D130  0x0056D1BF 0x0056D283 0x0056D2BC        PortalObjectCreate: [esp+4] room, x, y, dest, &out,
#                                                                  class, noSearch (seven stack arguments, ret 0x1C)
#     npcmove  0x0054B830  0x0054B883 0x0054B8FE 0x0054B916        ECX game, EDX player, [esp+4] level, [esp+8] type
#     npcact   0x005467E0  0x005468D5 0x00546982 0x00546A40 0x00546AB4  ECX game, EDX player, [esp+4] npc
#     chlevel  0x0053AEC0  0x0053AF5A 0x0053AFA2                   ECX game, EDX player, [esp+4] level, [esp+8] type
#     chact    0x0053ACC0  0x0053AEB1                              [esp+4] level, [esp+8] type (the player from the join)
#     warp     0x005550B0  0x00555223                              ECX game, EDX player, [esp+4] warp unit
#     door     0x0058D6A0  0x0058D725 0x0058D73C 0x0058D755 0x0058D761  ECX ctx (OperateFn 71, the summit door 120 ->
#                                                                  118): mode, quest 35 [+0x09, +0x0A, private +0x00
#                                                                  "done in this game", +0x48, +0x60]
#     warpgate 0x00545B80  0x00545BA4 0x00545BAE 0x00545BBF 0x00545BC9 0x00545BD0  [esp+4] source, [esp+8] dest
#     place    0x005394A0  0x0053975C                              ECX game, EDX player, [esp+4] given position
#     spot     0x0061B060  0x0061B118 0x0061B121                   ActLevelSpot: [esp+8] level, [esp+0xC] type,
#                                                                  [esp+0x10] &x, [esp+0x14] &y, [esp+0x18] size
#     lpf      0x0066B2B0  0x0066B321 0x0066B33E 0x0066B3CE 0x0066B3D9  LevelPointFind: EDX level id, [esp+4] type,
#                                                                  [esp+8] &tx, [esp+0xC] &ty; the level and its seed
#                                                                  (level +0x1C4) from LPL below
#   LPL    0x0066B2E4 in LevelPointFind after the level lookup (EAX level; "ls0" its seed then) and 0x0066B2F2 after
#          the level init that runs when level +0x10 is 0 ("init"; ESI level): the level, its id, its seed ("ls"),
#          and its points (level +0x1D8 count; +0x2C + 12 i: x, y, type) that LevelPointPick 0x0066AC40 chooses from
#   GT     the two real-time gates: 0x0054C60F (packet 0x49: [ebp+8] = stamp + 10000, EAX = GetTickCount()) and
#          0x005848CD (portal use: EDI = stamp + 5000, EAX = GetTickCount()); the stamp, the tick, pass
#   QCB    0x00543965 / 0x005439F9 a quest callback about to run (ESI / ECX quest object, EAX function): id, act +0x08,
#          active +0x09, +0x0A, the event
#   PU     the portal pair's seeds: 0x0056D24E after the field end's SUnitCreate (EAX), 0x0056D261 after its
#          SetMode(1) (ESI), 0x0056D097 after the partner's SUnitCreate (EAX), 0x0056D10C after its SetMode(2) (ESI):
#          the object, its seed (+0x20) and start seed (+0x28), gs; "roomupdate" at 0x0056CF82, after
#          RoomUpdateOne(the town end's room) in PortalPartnerCreate (a room it populates draws gs: an oracle): gs
#   FF0    0x0064DEA0 COLL_FindFreeNear entry, only inside a travel event: room, pos, other, size, maskA, maskB,
#          fallback, radius, step and the collision cells of the active rooms (game +0xBC + 4·act, list +0x10, next
#          +0x7C; map +0x20 = {x0, y0, w, h, ..., +0x20 cells u16}) in the square pos ± 12 (row-major, null when no
#          map holds the cell); FFX at its returns (0x0064DF75 0x0064E22A 0x0064E24A 0x0064E255): room (EAX), pos
#   NPCQ   at most every 0.5 s at a PLR-rate site (0x0064EA90): the server units of the NPC classes 155, 175, 210, 264,
#          266, 331, 367, 377, 520 (a driver helper, as vendors.py's NPC line; nothing here feeds a model)
#   QOBJ   at the join's exit and on request: every quest object (id, act, +0x09, +0x0A, +0x0B, word +0xE0)
#   LOGERR on a handler exception (the game goes on)
import json
import struct
import time

import gdb


def _questev_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "plr": 0, "pend": {}, "travel": 0, "t": 0.0, "lpl": {}}
    NPCQ = {155, 175, 210, 264, 266, 331, 367, 377, 520}
    TRAVEL = {"p49", "wptr", "portal", "lvlportal", "arcane", "durance", "tp", "pocreate", "npcmove", "chlevel",
              "chact", "warp", "place", "p41", "spot"}

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

    def seed(a):
        return "%08x:%08x" % (u32(a), u32(a + 4))

    def unit(u):
        if not u:
            return 0
        return [u32(u), s32(u + 4), u32(u + 0xC)]

    def frame():
        g = st["game"]
        try:
            return u32(g + 0xA8) if g else None
        except gdb.MemoryError:
            return None

    def emit(tag, d):
        d["f"] = frame()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def upos(u):
        if not u:
            return None
        t = u32(u)
        p = u32(u + 0x2C)
        if not p:
            return None
        if t in (2, 4, 5):
            return [u32(p + 0x0C), u32(p + 0x10)]
        return [u16(p + 2), u16(p + 6)]

    def room_level(r):
        d = u32(r + 0x10) if r else 0
        lvl = u32(d + 0x58) if d else 0
        return u32(lvl + 0x1D0) if lvl else None

    def unit_level(u):
        p = u32(u + 0x2C) if u else 0
        r = u32(p + 0x1C) if p else 0
        return room_level(r) if r else None

    def pdata(p):
        return u32(p + 0x14) if p else 0

    def diff():
        g = st["game"]
        return u8(g + 0x6D) if g else 0

    def rec_words(p):
        pd = pdata(p)
        rec = u32(pd + 0x10 + 4 * diff()) if pd else 0
        bits = u32(rec) if rec else 0
        return list(struct.unpack("<48H", mem(bits, 96))) if bits else None

    def grec_words():
        g = st["game"]
        qc = u32(g + 0x10F4) if g else 0
        rec = u32(qc + 0x0C) if qc else 0
        bits = u32(rec) if rec else 0
        return list(struct.unpack("<48H", mem(bits, 96))) if bits else None

    def seeds(p=None):
        g = st["game"]
        p = p or st["plr"]
        d = {}
        if g:
            d["gs"] = seed(g + 0xD0)
            qc = u32(g + 0x10F4)
            d["qs"] = seed(qc + 0x18) if qc else None
        if p:
            d["ps"] = seed(p + 0x20)
        return d

    def quest_objs():
        g = st["game"]
        qc = u32(g + 0x10F4) if g else 0
        q = u32(qc) if qc else 0
        out = []
        k = 0
        while q and k < 64:
            b = mem(q, 0x0C)
            out.append([u32(q), b[8], b[9], b[10], b[11], u32(q + 0xE0)])
            q = u32(q + 0xF4)
            k += 1
        return out

    def quest_slots(ev):
        """The ids, in list order, of the quest objects whose callback slot +0xA0 + 4·ev is set."""
        g = st["game"]
        qc = u32(g + 0x10F4) if g else 0
        q = u32(qc) if qc else 0
        out = []
        k = 0
        while q and k < 64:
            if u32(q + 0xA0 + 4 * ev):
                out.append(u32(q))
            q = u32(q + 0xF4)
            k += 1
        return out

    def quest_obj(qid):
        g = st["game"]
        qc = u32(g + 0x10F4) if g else 0
        q = u32(qc) if qc else 0
        k = 0
        while q and k < 64:
            if u32(q) == qid:
                return q
            q = u32(q + 0xF4)
            k += 1
        return 0

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR questev 0x%08X %r\n" % (self.location, e) if isinstance(self.location, int)
                          else "LOGERR questev %s %r\n" % (self.location, e))
            return False

    # ---- event brackets
    def bracket(name, entry, rets, ctx, out=None):
        def on_entry():
            esp = reg("esp")
            d = ctx(esp) or {}
            p = d.pop("_plr", None) or st["plr"]
            keep = d.pop("_keep", {})
            d.update({"k": name, "ph": 0, "ret": "%08x" % u32(esp)})
            d.update(seeds(p))
            st["pend"][(name, esp)] = (p, keep)
            if name in TRAVEL:
                st["travel"] += 1
            emit("EV", d)

        def on_ret():
            esp = reg("esp")
            key = (name, esp)
            if key not in st["pend"]:
                return
            p, keep = st["pend"].pop(key)
            if name in TRAVEL:
                st["travel"] = max(0, st["travel"] - 1)
            d = {"k": name, "ph": 1, "eax": reg("eax")}
            if out:
                d.update(out(keep) or {})
            d.update(seeds(p))
            emit("EV", d)

        Bp(entry, on_entry)
        for r in rets:
            Bp(r, on_ret)

    def ctx_block(esp):
        b = reg("edi")
        p = u32(b + 0x0C)
        if p and u32(p) == 0:
            st["plr"] = st["plr"] or p
        u = u32(b + 0x08)
        d = {"ev": u32(b + 4), "force": u8(esp + 4), "actf": u8(esp + 8), "unit": unit(u), "plr": unit(p),
             "p14": u32(b + 0x14), "p18": u32(b + 0x18), "_plr": p if p and u32(p) == 0 else None}
        if u and u32(u) == 1:
            d["ucls"] = s32(u + 4)
            if d["ucls"] == 331:       # quest object 11's private +0x0E: the palace is open (the e0 draw's test)
                q = quest_obj(11)
                pr = u32(q + 0x18) if q else 0
                d["q11e"] = u8(pr + 0x0E) if pr else None
        ev = d["ev"]
        d["qobj"] = quest_objs()
        d["slots"] = quest_slots(ev) if ev < 16 else None
        d["lid"] = unit_level(p) if p and u32(p) == 0 else None
        return d

    def ctx_ublock(esp):
        b = reg("edi")
        p = u32(b + 0x0C)
        u = u32(b + 0x08)
        return {"ev": u32(b + 4), "force": u8(esp + 4), "unit": unit(u), "plr": unit(p),
                "_plr": p if p and u32(p) == 0 else None}

    def ctx_join(esp):
        g, p = reg("ecx"), reg("edx")
        st["game"] = st["game"] or g
        st["plr"] = p
        qc = u32(g + 0x10F4)
        return {"plr": unit(p), "rejoin": u32(esp + 4), "ready": u32(qc + 8) if qc else None,
                "b150c": u8(0x0073150C), "rec": rec_words(p), "grec": grec_words(), "diff": diff(),
                "exp": u32(g + 0x70), "qobj": quest_objs(), "_plr": p}

    def out_join(keep):
        return {"qobj": quest_objs(), "grec": grec_words(), "rec": rec_words(st["plr"])}

    def ctx_gp(esp):          # ECX game, EDX player
        p = reg("edx")
        d = {"plr": unit(p), "_plr": p, "lid": unit_level(p), "pos": upos(p)}
        return d

    def out_pos(keep):
        p = st["plr"]
        return {"lid": unit_level(p), "pos": upos(p)}

    def ctx_p49(esp):
        p = reg("edx")
        pk = u32(esp + 4)
        return {"plr": unit(p), "_plr": p, "obj": u32(pk + 1), "lvl": u16(pk + 5), "len": u32(esp + 8),
                "lid": unit_level(p), "pos": upos(p)}

    def ctx_p58(esp):
        p = reg("edx")
        pk = u32(esp + 4)
        w = u16(pk + 1)
        rw = rec_words(p)
        return {"plr": unit(p), "_plr": p, "w": w, "len": u32(esp + 8),
                "old": rw[w] if rw and w < 48 else None, "_keep": {"w": w, "p": p}}

    def out_p58(keep):
        rw = rec_words(keep["p"])
        w = keep["w"]
        return {"new": rw[w] if rw and w < 48 else None}

    def ctx_p48(esp):
        p = reg("edx")
        pd = pdata(p)
        return {"plr": unit(p), "_plr": p, "len": u32(esp + 8), "c4c": u32(pd + 0x4C) if pd else None,
                "_keep": {"p": p}}

    def out_p48(keep):
        pd = pdata(keep["p"])
        return {"c4c": u32(pd + 0x4C) if pd else None}

    def ctx_op(esp):         # OperateFn context {game, object, player, ?, class}
        c = reg("ecx")
        g, o, p = u32(c), u32(c + 4), u32(c + 8)
        st["game"] = st["game"] or g
        d = {"obj": unit(o), "omode": u32(o + 0x10) if o else None, "os": seed(o + 0x20) if o else None,
             "oinit": "%08x" % u32(o + 0x28) if o else None, "opos": upos(o), "plr": unit(p), "_plr": p,
             "lid": unit_level(p), "pos": upos(p), "_keep": {"o": o, "p": p}}
        if o:
            od = u32(o + 0x14)
            d["odest"] = u8(od + 4) if od else None
        pd = pdata(p)
        if pd:
            d["own"] = u32(pd + 0x48)
            d["c4c"] = u32(pd + 0x4C)
            d["wp"] = mem(u32(pd + 0x1C + 4 * diff()) + 2, 6).hex() if u32(pd + 0x1C + 4 * diff()) else None
        return d

    def out_op(keep):
        o, p = keep["o"], keep["p"]
        d = {"lid": unit_level(p), "pos": upos(p)}
        try:
            d["omode"] = u32(o + 0x10)
            d["os"] = seed(o + 0x20)
        except gdb.MemoryError:
            d["omode"] = None
        pd = pdata(p)
        if pd:
            d["own"] = u32(pd + 0x48)
            d["c4c"] = u32(pd + 0x4C)
            d["wp"] = mem(u32(pd + 0x1C + 4 * diff()) + 2, 6).hex() if u32(pd + 0x1C + 4 * diff()) else None
        return d

    def ctx_orb(esp):
        d = ctx_op(esp)
        c = reg("ecx")
        p = u32(c + 8)
        inv = u32(p + 0x60) if p else 0
        q = quest_obj(0x13)
        pr = u32(q + 0x18) if q else 0
        d["cnt"] = s32(pr + 0x38) if pr else None
        d["q19"] = [u8(q + 9), u8(q + 10)] if q else None
        # the primary weapon's code, as 0x005BB9A0/0x005BB9AE read it (0x0063BEF0 inventory -> item; item +0x04 the
        # class; the code is the items-table record's +0x80 code via 0x00628590 -- read here from ItemsTxt by class)
        d["inv"] = inv
        d["_keep"]["q"] = pr
        return d

    def out_orb(keep):
        d = out_op(keep)
        pr = keep.get("q")
        d["cnt"] = s32(pr + 0x38) if pr else None
        return d

    def ctx_tp(esp):
        g, p = reg("ecx"), reg("edx")
        st["game"] = st["game"] or g
        pd = pdata(p)
        return {"plr": unit(p), "_plr": p, "lid": unit_level(p), "pos": upos(p),
                "own": u32(pd + 0x48) if pd else None, "_keep": {"p": p}}

    def out_tp(keep):
        p = keep["p"]
        pd = pdata(p)
        return {"own": u32(pd + 0x48) if pd else None, "lid": unit_level(p), "pos": upos(p)}

    def ctx_poc(esp):
        return {"room": u32(esp + 4), "x": u32(esp + 8), "y": u32(esp + 0x0C), "dest": u32(esp + 0x10),
                "cls": u32(esp + 0x18), "nosearch": u32(esp + 0x1C), "plr": unit(reg("edx")),
                "_keep": {"out": u32(esp + 0x14)}}

    def ctx_npcmove(esp):
        d = ctx_gp(esp)
        d.update({"lvl": u32(esp + 4), "type": u32(esp + 8)})
        return d

    def ctx_npcact(esp):
        d = ctx_gp(esp)
        n = u32(esp + 4)
        d["npc"] = unit(n)
        d["rec"] = rec_words(reg("edx"))
        return d

    def out_npcact(keep):
        d = out_pos(keep)
        d["rec"] = rec_words(st["plr"])
        pd = pdata(st["plr"])
        d["c4c"] = u32(pd + 0x4C) if pd else None
        d["wp"] = mem(u32(pd + 0x1C + 4 * diff()) + 2, 6).hex() if pd and u32(pd + 0x1C + 4 * diff()) else None
        return d

    def ctx_chact(esp):        # PlayerChangeAct: the player is not in EDX here; the level and type are
        return {"lvl": u32(esp + 4), "type": u32(esp + 8)}

    def ctx_warp(esp):
        d = ctx_gp(esp)
        w = u32(esp + 4)
        d["warp"] = unit(w)
        d["wpos"] = upos(w)
        return d

    def ctx_wgate(esp):
        return {"src": u32(esp + 4), "dst": u32(esp + 8), "q35": [u8(quest_obj(35) + 9), u8(quest_obj(35) + 10),
                                                                     u8(u32(quest_obj(35) + 0x18))]
                if quest_obj(35) else None}

    def ctx_place(esp):
        d = ctx_gp(esp)
        d["given"] = u32(esp + 8)
        return d

    def ctx_spot(esp):
        return {"lvl": u32(esp + 8), "type": u32(esp + 0x0C), "size": u32(esp + 0x18),
                "_keep": {"px": u32(esp + 0x10), "py": u32(esp + 0x14)}}

    def out_spot(keep):
        return {"x": u32(keep["px"]), "y": u32(keep["py"])}

    def ctx_lpf(esp):
        return {"lvl": reg("edx"), "type": u32(esp + 4), "_keep": {"px": u32(esp + 8), "py": u32(esp + 0x0C),
                                                                     "esp": esp}}

    def out_lpf(keep):
        lv = st["lpl"].pop(keep["esp"], 0)
        return {"tx": s32(keep["px"]), "ty": s32(keep["py"]), "ls": seed(lv + 0x1C4) if lv else None}

    def on_lpl():
        lv = reg("eax")
        esp0 = reg("ebp") + 4          # the entry esp (push ebp; mov ebp, esp)
        st["lpl"][esp0] = lv
        st["lpl0"] = (lv, seed(lv + 0x1C4), u32(lv + 0x10))

    def on_lpl2():                     # 0x0066B2F2: after the level init (0x006424A0) when +0x10 was 0
        lv = reg("esi")
        lv0, s0, i0 = st.get("lpl0", (0, None, None))
        n = u32(lv + 0x1D8)
        pts = [list(struct.unpack_from("<iiI", mem(lv + 0x2C + 12 * i, 12))) for i in range(min(n, 64))]
        emit("LPL", {"lv": lv, "lid": u32(lv + 0x1D0), "ls0": s0 if lv0 == lv else None, "init": int(not i0),
                     "ls": seed(lv + 0x1C4), "pts": pts})

    bracket("de", 0x005438E0, [0x00543974], ctx_block)
    bracket("due", 0x005439A0, [0x00543A05], ctx_ublock)
    bracket("join", 0x00546270, [0x0054666F, 0x005466A4], ctx_join, out_join)
    bracket("p49", 0x0054C5D0, [0x0054C5E7, 0x0054C630, 0x0054C675, 0x0054C68A], ctx_p49, out_pos)
    bracket("p48", 0x0054C590, [0x0054C5A3, 0x0054C5B9, 0x0054C5C7], ctx_p48, out_p48)
    bracket("p58", 0x0054C9C0, [0x0054C9F9, 0x0054CA04], ctx_p58, out_p58)
    bracket("p41", 0x0054C0E0, [0x0054C0FC, 0x0054C148, 0x0054C293], ctx_gp, out_pos)
    bracket("wpop", 0x00584E30, [0x00584F51], ctx_op, out_op)
    bracket("wptr", 0x00584F60, [0x00585113], ctx_gp, out_pos)
    bracket("portal", 0x00584870, [0x005848E6, 0x00584A38, 0x00584CF3], ctx_op, out_op)
    bracket("lvlportal", 0x00584D00, [0x00584E22], ctx_op, out_op)
    bracket("arcane", 0x005846B0, [0x00584707, 0x0058472A, 0x0058474D], ctx_op, out_op)
    bracket("durance", 0x00584750, [0x00584817], ctx_op, out_op)
    bracket("orb", 0x005BB980, [0x005BBB55, 0x005BBB6B], ctx_orb, out_orb)
    bracket("tp", 0x005BE290, [0x005BE2AC, 0x005BE3CB, 0x005BE3E3], ctx_tp, out_tp)
    bracket("pocreate", 0x0056D130, [0x0056D1BF, 0x0056D283, 0x0056D2BC], ctx_poc,
            lambda k: {"field": unit(u32(k["out"])) if k["out"] else None})
    bracket("npcmove", 0x0054B830, [0x0054B883, 0x0054B8FE, 0x0054B916], ctx_npcmove, out_pos)
    bracket("npcact", 0x005467E0, [0x005468D5, 0x00546982, 0x00546A40, 0x00546AB4], ctx_npcact, out_npcact)
    bracket("chlevel", 0x0053AEC0, [0x0053AF5A, 0x0053AFA2], ctx_npcmove, out_pos)
    bracket("chact", 0x0053ACC0, [0x0053AEB1], ctx_chact, out_pos)
    def ctx_door(esp):
        d = ctx_op(esp)
        q = quest_obj(35)
        pr = u32(q + 0x18) if q else 0
        d["q35"] = [u8(q + 9), u8(q + 10), u8(pr), u8(pr + 0x48), u32(pr + 0x60)] if q and pr else None
        return d

    bracket("door", 0x0058D6A0, [0x0058D725, 0x0058D73C, 0x0058D755, 0x0058D761], ctx_door, out_op)
    bracket("warp", 0x005550B0, [0x00555223], ctx_warp, out_pos)
    bracket("warpgate", 0x00545B80, [0x00545BA4, 0x00545BAE, 0x00545BBF, 0x00545BC9, 0x00545BD0], ctx_wgate)
    bracket("place", 0x005394A0, [0x0053975C], ctx_place, out_pos)
    bracket("spot", 0x0061B060, [0x0061B118, 0x0061B121], ctx_spot, out_spot)
    bracket("lpf", 0x0066B2B0, [0x0066B321, 0x0066B33E, 0x0066B3CE, 0x0066B3D9], ctx_lpf, out_lpf)
    Bp(0x0066B2E4, on_lpl)
    Bp(0x0066B2F2, on_lpl2)

    def on_orbw():          # 0x005BB9B3: EAX the operator's primary weapon code (0x00628590), compared with 'qf2 '
        v = reg("eax")
        emit("ORBW", {"code": struct.pack("<I", v).decode("latin1") if v else 0})

    Bp(0x005BB9B3, on_orbw)

    # ---- the real-time gates
    def on_gt49():
        tick, lim = reg("eax"), u32(reg("ebp") + 8)
        emit("GT", {"k": "p49", "tick": tick, "stamp": (lim - 10000) & 0xFFFFFFFF, "pass": int(lim <= tick)})

    def on_gtpo():
        tick, lim = reg("eax"), reg("edi")
        emit("GT", {"k": "portal", "tick": tick, "stamp": (lim - 5000) & 0xFFFFFFFF, "pass": int(lim <= tick)})

    Bp(0x0054C60F, on_gt49)
    Bp(0x005848CD, on_gtpo)

    # ---- quest callbacks
    def on_qcb(rq):
        def f():
            q = reg(rq)
            b = reg("edi")
            emit("QCB", {"id": u32(q), "act": u8(q + 8), "a9": u8(q + 9), "aA": u8(q + 10), "ev": u32(b + 4),
                         "fn": "%08x" % reg("eax"), "unit": "due" if rq == "ecx" else "de"})
        return f

    Bp(0x00543965, on_qcb("esi"))
    Bp(0x005439F9, on_qcb("ecx"))

    # ---- the portal pair's seeds
    def on_pu(tag, r):
        def f():
            o = reg(r)
            g = st["game"]
            emit("PU", {"at": tag, "obj": unit(o), "os": seed(o + 0x20) if o else None,
                        "oinit": "%08x" % u32(o + 0x28) if o else None, "omode": u32(o + 0x10) if o else None,
                        "opos": upos(o), "gs": seed(g + 0xD0) if g else None})
        return f

    def on_ru():                       # 0x0056CF82: after RoomUpdateOne(the town end's room) in PortalPartnerCreate
        g = st["game"]
        emit("PU", {"at": "roomupdate", "gs": seed(g + 0xD0) if g else None})

    Bp(0x0056CF82, on_ru)
    Bp(0x0056D24E, on_pu("field", "eax"))
    Bp(0x0056D261, on_pu("field1", "esi"))
    Bp(0x0056D097, on_pu("partner", "eax"))
    Bp(0x0056D10C, on_pu("partner2", "esi"))

    # ---- free-cell searches inside a travel event
    def cells_window(x0, y0, rad=12):
        g = st["game"]
        n = 2 * rad + 1
        out = [None] * (n * n)
        for a in range(5):
            act = u32(g + 0xBC + 4 * a)
            if not act:
                continue
            r = u32(act + 0x10)
            k = 0
            while r and k < 3000:
                k += 1
                m = u32(r + 0x20)
                if m:
                    mx, my, mw, mh = struct.unpack("<iiii", mem(m, 16))
                    lx, hx = max(mx, x0 - rad), min(mx + mw - 1, x0 + rad)
                    ly, hy = max(my, y0 - rad), min(my + mh - 1, y0 + rad)
                    c = u32(m + 0x20)
                    if c and lx <= hx and ly <= hy:
                        for yy in range(ly, hy + 1):
                            row = mem(c + 2 * ((yy - my) * mw + (lx - mx)), 2 * (hx - lx + 1))
                            vals = struct.unpack("<%dH" % (hx - lx + 1), row)
                            base = (yy - (y0 - rad)) * n
                            for i, v in enumerate(vals):
                                out[base + lx + i - (x0 - rad)] = v
                r = u32(r + 0x7C)
        return out

    def on_ff0():
        if st["travel"] <= 0:
            return
        esp = reg("esp")
        pp = u32(esp + 8)
        x, y = s32(pp), s32(pp + 4)
        oth = u32(esp + 0x0C)
        st["pend"][("ff", esp)] = (pp, None)
        emit("FF0", {"room": u32(esp + 4), "x": x, "y": y, "other": [s32(oth), s32(oth + 4)] if oth else None,
                     "size": u32(esp + 0x10), "ma": u32(esp + 0x14), "mb": u32(esp + 0x18),
                     "fb": u32(esp + 0x1C), "rad": u32(esp + 0x20), "step": u32(esp + 0x24),
                     "w": 12, "cells": cells_window(x, y)})

    def on_ffx():
        esp = reg("esp")
        v = st["pend"].pop(("ff", esp), None)
        if not v:
            return
        pp = v[0]
        emit("FFX", {"room": reg("eax"), "x": s32(pp), "y": s32(pp + 4)})

    Bp(0x0064DEA0, on_ff0)
    for a in (0x0064DF75, 0x0064E22A, 0x0064E24A, 0x0064E255):
        Bp(a, on_ffx)

    # ---- NPC positions for the driver (tools/quest_sessions.py)
    def on_npcq():
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
                    if cls in NPCQ and p:
                        out.append([cls, u32(u + 0xC), u32(u + 0x10), u16(p + 2), u16(p + 6)])
                except gdb.MemoryError:
                    pass
                u = u32(u + 0xE4)
        emit("NPCQ", {"n": out})

    Bp(0x0064EA90, on_npcq)

    def on_game():
        st["game"] = reg("edi")

    Bp(0x0052C312, on_game)
    gdb.write("QUESTEV logger armed\n")


_questev_main()
