# gdb Python logger for plan 0014 Phase 2 (random population of a room). Sourced by tools/gdb/mon-spawn.gdb after
# tools/gdb/drlg-gen.py and tools/gdb/drlg-roomk.py, whose tags it leaves unchanged (the room seed is predicted from
# the map seed through them). One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base
# 0x400000). Seeds are printed "lo:hi". "rs" is the active-room seed (+0x6C) of the room the code draws from, "gs" the
# game seed (+0xD0), "us" a unit seed (+0x20). See docs/findings/monsters/0002-room-population.md (section 9).
#
# Room driver (sub_0052D160_NewRoomsUpdate 0x0052D1C4.., sub_0052D0F0_RoomUpdateOne 0x0052D0F6..), rooms whose flag bit
# 0 is clear only:
#   RW0  before the wanderer tick: rs              RW1  after it (presets next): rs, gs
#   RW2  after RoomPresetUnits                      RW3  after RoomInactiveUnitsRestore
#   RW4  after RoomObjectsPopulate (the pass next)  (each: rs, gs; the three are seed oracles)
#   WRL  0x0054EFF0 sub_0054EFF0_WandererRoll entry (rare): rs
# The pass, sub_0054EC90_RoomPopulate:
#   P0   entry: room, level id, room rect (+0x4C), flags, DRLG room, rs, gs, the region before the gate
#   PG   0x0054ECAA gate result                     PR   0x0054ECDC the region after the gate
#   PB   0x0054ED03 each box: rect (+0x10), kind (+0x20), region id (+0x28)
#   PN   0x0054ED7E attempts of the box             PA   0x0054EDE0 an attempt that passed density: r, gs
#   PC   0x0054EDF2 first class pick: class, record PT   0x0054EE08 SpawnTypeRoll result
#   PSP  0x0054EE8A sparsePopulate roll (r, value)  PGR  0x0054EE9F SpawnGroup call: class, min, max
#   PGX  0x0054EEA4 SpawnGroup / FormationGroup return (leader)
#   PS2  0x0054EF10 special class pick              PSB  0x0054EF28 SpecialMonSpawn return (boss)
#   PCP  0x0054EF3B after ChampionPack              PDEAD 0x0054EEE4 the dead type-1 branch (must never log)
#   PX   0x0054EEDD exit: rs, gs, the region
# Position pick, sub_0054DC40_SpawnPosPick:
#   SP0  0x0054DC65 after SpawnBoxBounds: room, box, class, avoidWarp, x0, y0, w, h, rs
#   SPW0/SPW 0x0054DD2F/0x0054DD34 NearWarpTest (oracle): x, y, rs, gs / result
#   SPR0/SPR 0x0054DD44/0x0054DD49 LogicRegionIdAt (oracle): x, y, rs, gs / result
#   SPX  0x0054DDA3 found (x, y)                    SPF  0x0054DD98 20 tries failed
# sub_005B2A00_MonSpawnTry (nested calls are kept on a stack: "d" is the depth):
#   MT0  entry: the request (game, room, box, class, a10, a14, x, y, radius, flags), rs, gs
#   MTT0/MTT 0x005B2BB1/0x005B2BB6 SpawnPosOnTile (seed oracle): rs in / rs out, (x, y)
#   MR0/MR, MC0/MC, MK0/MK  0x005B2D7A/7F LogicRegionIdAt, 0x005B2D90/95 SpawnClassCellTest, 0x005B2DA8/AD CollisionTest
#        (value oracles): args, rs, gs / result, rs, gs
#   MU0  0x005B2E3D SUnitCreate call: x, y, mode, rs, gs   MU 0x005B2E44 after: unit, id, class, us, rs, gs
#   MUP  0x005B2EE4 after the post-create setup: us, rs, gs
#   MTX  0x005B2EFA / 0x005B2F03 exit: eax, rs, gs
# MonStats minions, sub_005B2830_MinionsSpawn:  MM0 entry (unit, us), MMN 0x005B2989 count, MMT 0x005B28FF tentacle count,
#   MMX 0x005B29F9 / 0x005B291C exit (us, rs)
# Normal group, sub_0054DF80_SpawnGroup:  G1 0x0054E040 after the leader (and the evilhut object): leader, us, gs
#   GK 0x0054E058 the member-count draw (RangeB result), us
# Special: SMPX 0x005A0BA6 / 0x005A0A1C SpecialMonPlace returns (boss, rs, gs, us); SMR0 0x005A0760 SpecialModsRoll entry
#   (unit, us, flags, mods); SMR1 0x005A082A the Range(100) result and the chance; SMRX 0x005A0868 / 0x005A0920 its exits
#   (us, flags, mods); SMA0 0x005A2120 SpecialModsApply entry (boss, us, rs); SMA1 0x005A213A after UniqueMinions; SMAX
#   0x005A21CA exit; UMN 0x005A0C58 unique minion count (eax), us; UMX 0x005A0CCF per minion after its setup (rs, gs, us
#   of the boss); CP0 0x0054E1E0 ChampionPack entry (boss, us); CPN 0x0054E221 pack count; CPM 0x0054E251 per member
#   Plan 0018: outside a pass (presets: superuniques, MonPlace 2 and 3) "rs" is the seed of the unit's own room (unit +0x2C
#   path, +0x1C room) and "gs" the game of the last request or pass; SMR0 also logs the game's difficulty and expansion
#   flag, and SMAX the unit (mods, flags) and its name seed (MonsterData +0x14).
# Special count +0x2C8: SCI 0x005A0362 increment (region, before), SCD 0x00547F15 decrement (region, before)
# MonWndr (plan 0014 F5): access watchpoints on Levels[l] +0x2E and region[l] +0x2BE for the level ids in
#   MONSPAWN_WATCH (default "2,8"), armed at the region build (0x005479C0 entry / 0x00547B1A per level):
#   WND {what, level, pc (the instruction after the access), value}
import json
import os
import struct

import gdb


def _monspawn_main():
    inf = gdb.selected_inferior()
    DT = 0x00744304
    stack = []              # open MonSpawnTry requests: [room, game]
    st = {"smr_unit": 0, "sma_boss": 0, "um_boss": 0, "cp_boss": 0, "mm_unit": [], "watch_lv": set(), "watch_rg": set()}
    watch_levels = [int(x) for x in os.environ.get("MONSPAWN_WATCH", "2,8").split(",") if x.strip()]

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

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8)) if p else None

    def rs(room):
        return sd(room + 0x6C) if room else None

    def gs(game):
        return sd(game + 0xD0) if game else None

    def us(unit):
        return sd(unit + 0x20) if unit else None

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
                "rsum": u8(r + 0x11), "ents": [[struct.unpack("<h", mem(r + 0x14 + 0x34 * i, 2))[0], u8(r + 0x16 + 0x34 * i)]
                                              for i in range(u8(r + 0x12))],
                "den": s32(r + 0x2B8), "umin": u8(r + 0x2BC), "umax": u8(r + 0x2BD), "wndr": u8(r + 0x2BE),
                "lid": s32(r + 0x2C0), "nwand": s32(r + 0x2C4), "nspec": s32(r + 0x2C8), "nmon": s32(r + 0x2CC)}

    def unit_info(u):
        if not u:
            return None
        md = u32(u + 0x14)
        d = {"u": u, "type": s32(u), "cls": s32(u + 4), "id": u32(u + 0xC), "us": us(u)}
        if s32(u) == 1 and md:
            d["mf"] = u16(md + 0x16)
            d["mods"] = list(mem(md + 0x1C, 9))
        return d

    last = {"game": 0}

    def uroom(u):
        p = u32(u + 0x2C) if u else 0
        return u32(p + 0x1C) if p else 0

    def srs(u):
        """The pass room's seed inside a pass, else the seed of the unit's own room (plan 0018)."""
        return rs(cur["room"] if cur["room"] else uroom(u))

    def sgs():
        return gs(cur["game"] if cur["game"] else last["game"])

    def top_room():
        return stack[-1][0] if stack else 0

    def top_game():
        return stack[-1][1] if stack else 0

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

    # --- room driver -------------------------------------------------------------------------------------------
    def rw(tag, need_clear):
        def f():
            room, game = reg("esi"), reg("edi")
            if need_clear and u32(room + 0x34) & 1:
                return
            emit(tag, {"room": room, "rs": rs(room), "gs": gs(game), "lid": level_of(room)})
        return f

    for a in (0x0052D1C4, 0x0052D0F6):
        Bp(a, rw("RW0", True))
    for a in (0x0052D1CE, 0x0052D101):
        Bp(a, rw("RW1", False))
    for a, t in ((0x0052D1D7, "RW2"), (0x0052D10A, "RW2"), (0x0052D1E0, "RW3"), (0x0052D113, "RW3"),
                 (0x0052D1E9, "RW4"), (0x0052D11C, "RW4")):
        Bp(a, rw(t, False))

    def on_wrl():
        room = reg("eax")
        emit("WRL", {"room": room, "rs": rs(room)})
    Bp(0x0054EFF0, on_wrl)

    # --- the pass ----------------------------------------------------------------------------------------------
    cur = {"game": 0, "room": 0, "region": 0}

    def on_p0():
        game, room = reg("ecx"), reg("edx")
        lid = level_of(room)
        cur.update(game=game, room=room)
        last["game"] = game
        emit("P0", {"game": game, "room": room, "lid": lid, "rect": list(struct.unpack("<4i", mem(room + 0x4C, 16))),
                    "flags": u32(room + 0x34), "dr": u32(room + 0x10), "rs": rs(room), "gs": gs(game),
                    "diff": u8(game + 0x6D), "exp": u32(game + 0x70), "reg": rsnap(region(game, lid))})

    def on_pg():
        emit("PG", {"r": reg("eax")})

    def on_pr():
        cur["region"] = reg("ecx")
        emit("PR", {"reg": rsnap(reg("ecx"))})

    def on_pb():
        b = reg("edi")
        emit("PB", {"box": b, "rect": list(struct.unpack("<4i", mem(b + 0x10, 16))), "kind": s32(b + 0x20),
                    "rid": s32(b + 0x28), "next": u32(b + 0x2C)})

    def on_pn():
        emit("PN", {"n": sreg("ecx")})

    def on_pa():
        emit("PA", {"r": reg("ecx"), "gs": gs(cur["game"]), "rs": rs(cur["room"])})

    def on_pc():
        emit("PC", {"cls": sreg("eax"), "rec": u32(reg("ebp") - 0xC), "rs": rs(cur["room"])})

    def on_pt():
        emit("PT", {"t": reg("eax"), "rs": rs(cur["room"]), "nspec": s32(cur["region"] + 0x2C8) if cur["region"] else None})

    def on_psp():
        emit("PSP", {"r": reg("ecx"), "v": reg("eax"), "gs": gs(cur["game"])})

    def on_pgr():
        ebp = reg("ebp")
        emit("PGR", {"cls": sreg("ebx"), "min": u8(ebp - 0x20), "max": u8(ebp - 0x1C), "rs": rs(cur["room"]),
                     "gs": gs(cur["game"])})

    def on_pgx():
        emit("PGX", {"leader": reg("eax"), "rs": rs(cur["room"]), "gs": gs(cur["game"])})

    def on_ps2():
        emit("PS2", {"cls": sreg("eax"), "rs": rs(cur["room"])})

    def on_psb():
        emit("PSB", {"boss": reg("eax"), "rs": rs(cur["room"]), "gs": gs(cur["game"]), "bu": unit_info(reg("eax"))})

    def on_pcp():
        emit("PCP", {"rs": rs(cur["room"]), "gs": gs(cur["game"]),
                     "nspec": s32(cur["region"] + 0x2C8) if cur["region"] else None})

    def on_pdead():
        emit("PDEAD", {"rs": rs(cur["room"])})

    def on_px():
        game, room = cur["game"], cur["room"]
        lid = level_of(room)
        emit("PX", {"room": room, "rs": rs(room), "gs": gs(game), "reg": rsnap(region(game, lid))})
        cur.update(game=0, room=0, region=0)

    for a, f in ((0x0054EC90, on_p0), (0x0054ECAA, on_pg), (0x0054ECDC, on_pr), (0x0054ED03, on_pb),
                 (0x0054ED7E, on_pn), (0x0054EDE0, on_pa), (0x0054EDF2, on_pc), (0x0054EE08, on_pt),
                 (0x0054EE8A, on_psp), (0x0054EE9F, on_pgr), (0x0054EEA4, on_pgx), (0x0054EF10, on_ps2),
                 (0x0054EF28, on_psb), (0x0054EF3B, on_pcp), (0x0054EEE4, on_pdead), (0x0054EEDD, on_px)):
        Bp(a, f)

    # --- SpawnPosPick ------------------------------------------------------------------------------------------
    sp = {"room": 0, "game": 0}

    def on_sp0():
        ebp = reg("ebp")
        room = u32(ebp - 4)
        sp.update(room=room, game=u32(ebp - 0xC))
        emit("SP0", {"room": room, "box": u32(ebp + 8), "cls": s32(ebp + 0xC), "warp": u32(ebp + 0x18),
                     "x0": s32(ebp - 0x20), "y0": s32(ebp - 0x24), "w": s32(ebp - 0x1C), "h": s32(ebp - 8),
                     "rs": rs(room), "gs": gs(sp["game"])})

    def spx(tag, res):
        def f():
            d = {"x": sreg("ebx"), "y": sreg("edi"), "rs": rs(sp["room"]), "gs": gs(sp["game"])}
            if res:
                d["r"] = sreg("eax")
            emit(tag, d)
        return f

    Bp(0x0054DC65, on_sp0)
    for a, t, r in ((0x0054DD2F, "SPW0", False), (0x0054DD34, "SPW", True), (0x0054DD44, "SPR0", False),
                    (0x0054DD49, "SPR", True), (0x0054DDA3, "SPX", False)):
        Bp(a, spx(t, r))
    Bp(0x0054DD98, lambda: emit("SPF", {"rs": rs(sp["room"])}))

    # --- MonSpawnTry -------------------------------------------------------------------------------------------
    def on_mt0():
        r = reg("ecx")
        game, room, box, cls, a10, a14, x, y, rad, flags = struct.unpack("<IIIiiiiiiH", mem(r, 0x26))
        stack.append([room, game])
        last["game"] = game
        emit("MT0", {"d": len(stack), "game": game, "room": room, "box": box, "cls": cls, "a10": a10, "a14": a14,
                     "x": x, "y": y, "rad": rad, "fl": flags, "rs": rs(room), "gs": gs(game)})

    def on_mtx():
        room, game = top_room(), top_game()
        emit("MTX", {"d": len(stack), "eax": reg("eax"), "rs": rs(room), "gs": gs(game)})
        if stack:
            stack.pop()

    def on_mtt0():
        emit("MTT0", {"rs": rs(top_room())})

    def on_mtt():
        ebp = reg("ebp")
        emit("MTT", {"rs": rs(top_room()), "x": s32(ebp - 0x20), "y": s32(ebp - 0x1C)})

    def pred(tag, entry, kind):
        def f():
            room = top_room()
            d = {"rs": rs(room), "gs": gs(top_game())}
            if entry:
                d.update(x=sreg("esi"), y=sreg("ebx"), room=reg("edi"))
                if kind == "K":
                    d.update(size=sreg("ecx"), mask=reg("edx"))
            else:
                d["r"] = reg("eax") & 0xFFFF if kind == "K" else sreg("eax")
            emit(tag, d)
        return f

    for a, t, e, k in ((0x005B2D7A, "MR0", True, "R"), (0x005B2D7F, "MR", False, "R"), (0x005B2D90, "MC0", True, "C"),
                       (0x005B2D95, "MC", False, "C"), (0x005B2DA8, "MK0", True, "K"), (0x005B2DAD, "MK", False, "K")):
        Bp(a, pred(t, e, k))

    def on_mu0():
        ebp = reg("ebp")
        emit("MU0", {"x": s32(ebp - 0x20), "y": s32(ebp - 0x1C), "mode": u32(reg("esp") + 0x10), "rs": rs(top_room()),
                     "gs": gs(top_game())})

    def on_mu():
        u = reg("edi")
        emit("MU", {"unit": unit_info(u), "rs": rs(top_room()), "gs": gs(top_game())})

    def on_mup():
        u = reg("edi")
        emit("MUP", {"unit": u, "us": us(u), "rs": rs(top_room()), "gs": gs(top_game())})

    for a, f in ((0x005B2A00, on_mt0), (0x005B2EFA, on_mtx), (0x005B2F03, on_mtx), (0x005B2BB1, on_mtt0),
                 (0x005B2BB6, on_mtt), (0x005B2E3D, on_mu0), (0x005B2E44, on_mu), (0x005B2EE4, on_mup)):
        Bp(a, f)

    # --- MinionsSpawn ------------------------------------------------------------------------------------------
    def on_mm0():
        u = reg("ebx")
        st["mm_unit"].append(u)
        emit("MM0", {"unit": u, "us": us(u)})

    def on_mmn(tag):
        def f():
            u = st["mm_unit"][-1] if st["mm_unit"] else 0
            emit(tag, {"n": sreg("eax"), "us": us(u)})
        return f

    def on_mmx():
        u = st["mm_unit"].pop() if st["mm_unit"] else 0
        emit("MMX", {"unit": u, "us": us(u), "rs": rs(top_room())})

    Bp(0x005B2830, on_mm0)
    Bp(0x005B2989, on_mmn("MMN"))
    Bp(0x005B28FF, on_mmn("MMT"))
    Bp(0x005B29F9, on_mmx)
    Bp(0x005B291C, on_mmx)

    # --- SpawnGroup --------------------------------------------------------------------------------------------
    def on_g1():
        u = reg("edi")
        emit("G1", {"leader": u, "us": us(u), "gs": gs(cur["game"]), "rs": rs(cur["room"])})

    def on_gk():
        emit("GK", {"r": sreg("eax"), "us": us(reg("edi"))})

    Bp(0x0054E040, on_g1)
    Bp(0x0054E058, on_gk)

    # --- specials ----------------------------------------------------------------------------------------------
    def on_smpx():
        u = reg("eax")
        emit("SMPX", {"boss": u, "bu": unit_info(u), "rs": srs(u), "gs": sgs()})

    def on_smr0():
        u = reg("ecx")
        st["smr_unit"] = u
        g = u32(reg("esp") + 4)
        emit("SMR0", {"unit": unit_info(u), "allow": u32(reg("esp") + 8), "diff": u8(g + 0x6D) if g else None,
                      "exp": u32(g + 0x70) if g else None})

    def on_smr1():
        emit("SMR1", {"r": reg("eax"), "c": s32(reg("ebp") - 0x10C), "us": us(st["smr_unit"])})

    def on_smrx():
        emit("SMRX", {"unit": unit_info(st["smr_unit"])})

    def on_sma0():
        b = u32(reg("esp") + 8)
        st["sma_boss"] = b
        emit("SMA0", {"boss": b, "us": us(b), "rs": srs(b), "gs": sgs(), "box": reg("edx")})

    def on_sma(tag):
        def f():
            b = st["sma_boss"]
            d = {"boss": b, "us": us(b), "rs": srs(b), "gs": sgs()}
            if tag == "SMAX":
                d["u"] = unit_info(b)
                md = u32(b + 0x14) if b else 0
                d["ns"] = u16(md + 0x14) if md else None
            emit(tag, d)
        return f

    def on_umn():
        b = reg("edi")
        st["um_boss"] = b
        emit("UMN", {"n": sreg("eax"), "us": us(b)})

    def on_umx():
        b = st["um_boss"]
        emit("UMX", {"us": us(b), "rs": srs(b), "gs": sgs()})

    def on_cp0():
        b = reg("esi")
        st["cp_boss"] = b
        emit("CP0", {"boss": b, "us": us(b), "mf": u16(u32(b + 0x14) + 0x16) if u32(b + 0x14) else None})

    def on_cpn():
        emit("CPN", {"n": sreg("ecx"), "us": us(st["cp_boss"])})

    def on_cpm():
        b = st["cp_boss"]
        if cur["region"]:
            rg = cur["region"]
        else:
            g = last["game"]
            rg = region(g, level_of(uroom(b))) if (g and b and uroom(b)) else 0
        emit("CPM", {"rs": srs(b), "gs": sgs(), "nspec": s32(rg + 0x2C8) if rg else None})

    for a, f in ((0x005A0BA6, on_smpx), (0x005A0A1C, on_smpx), (0x005A0760, on_smr0), (0x005A082A, on_smr1),
                 (0x005A0868, on_smrx), (0x005A0920, on_smrx), (0x005A2120, on_sma0), (0x005A213A, on_sma("SMA1")),
                 (0x005A21CA, on_sma("SMAX")), (0x005A0C58, on_umn), (0x005A0CCF, on_umx), (0x0054E1E0, on_cp0),
                 (0x0054E221, on_cpn), (0x0054E251, on_cpm)):
        Bp(a, f)

    def on_sci():
        r = reg("eax")              # 0x005A0362: add dword [eax+0x2C8], 1 (sub_005A0320_MonMarkSpecial)
        emit("SCI", {"reg": r, "lid": s32(r + 0x2C0), "before": s32(r + 0x2C8)})

    def on_scd():
        r = reg("esi")              # 0x00547F15: add dword [esi+0x2C8], -1 (sub_00547ED0_MonRegionUnitLeave)
        emit("SCD", {"reg": r, "lid": s32(r + 0x2C0), "before": s32(r + 0x2C8), "unit": reg("edi")})

    Bp(0x005A0362, on_sci)
    Bp(0x00547F15, on_scd)

    # --- MonWndr watchpoints (F5) ------------------------------------------------------------------------------
    class Watch(gdb.Breakpoint):
        def __init__(self, addr, what, lid):
            super().__init__("*(unsigned char *)0x%08X" % addr, gdb.BP_WATCHPOINT, gdb.WP_ACCESS, internal=True)
            self.silent = True
            self.what, self.lid, self.addr = what, lid, addr

        def stop(self):
            try:
                emit("WND", {"what": self.what, "lid": self.lid,
                             "pc": int(gdb.parse_and_eval("$pc")) & 0xFFFFFFFF, "v": u8(self.addr)})
            except Exception as e:
                gdb.write("LOGERR %r\n" % (e,))
            return False

    rwatches = []

    def on_regions_init():
        while rwatches:             # a new game in the same process: the old regions are gone
            rwatches.pop().delete()
        st["watch_rg"].clear()
        if st["watch_lv"]:
            return
        lv = u32(u32(DT) + 0xC58)
        for lid in watch_levels:
            try:
                Watch(lv + 0x220 * lid + 0x2E, "levels", lid)
                st["watch_lv"].add(lid)
            except Exception as e:
                gdb.write("LOGERR watch levels %d %r\n" % (lid, e))
        emit("WNDARM", {"levels": sorted(st["watch_lv"]), "base": lv})

    def on_region_built():
        r = reg("esi")
        lid = s32(r + 0x2C0)
        if lid in watch_levels and lid not in st["watch_rg"]:
            try:
                rwatches.append(Watch(r + 0x2BE, "region", lid))
                st["watch_rg"].add(lid)
                emit("WNDARM", {"region": lid, "r": r})
            except Exception as e:
                gdb.write("LOGERR watch region %d %r\n" % (lid, e))

    Bp(0x005479C0, on_regions_init)
    Bp(0x00547B1A, on_region_built)
    gdb.write("MONSPAWN logger armed\n")


_monspawn_main()
