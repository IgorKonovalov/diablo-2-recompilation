"""Model of the random population of a room, checked against runtime logs (plan 0014 Phase 2; plan 0017 Phase 2).

Usage:
  python3 -I tools/monspawn.py check <run.log> [...] [--excel DIR] [--root workspace/merged] [-v]

<run.log> is written by tools/d2run.py with tools/gdb/mon-spawn.gdb (tags of tools/gdb/drlg-gen.py,
tools/gdb/drlg-roomk.py and tools/gdb/mon-spawn.py, header "# d2run seed=N"). Tables are the .bin files the game
loads, read by position (levels, monstats, monstats2, monumod) from --excel (default
workspace/merged/data/global/excel); the DRLG models read --root.

The model is docs/findings/monsters/0002-room-population.md, written from the code. Per room:

  * Room seed from the map seed: `tools/drlg.py gen` predicts each DRLG room's +0x04 from the level seed (act base
    = step(Init(N)).low, checked at every LC0), `tools/drlg.py roomk` predicts k and the active-room seed at AROOM
    (both with their own boundary oracles: the maze and outdoor generators, Orient89). A room counts as "predicted"
    when both models predicted its chain and the first population-window line (RW0) carries that seed.
  * Room driver: the wanderer tick is one room-seed step (RW0 -> RW1; a wanderer roll, WRL, is a seed oracle); the
    preset units, the inactive-unit restore and the object population are seed oracles (RW1 -> RW4: room and game
    seed taken from the log), and RW4 must equal the pass entry (P0). The pass-entry room seed is predicted end to
    end only where the room was predicted and that window drew nothing (RW1 rs = RW4 rs); those rooms, and the
    populated ones among them, are counted and listed. Plan 0023: in a log written with tools/gdb/objects.gdb (RW lines
    with "os"), tools/objects.py models the window, and every RW4 it reached with the room, object-region and game seeds
    predicted from RW1 is no longer an oracle; any mismatch of tools/objects.py on the log is one here.
  * The pass (sub_0054EC90_RoomPopulate): the gate (a closed MonDen gate is predicted; RoomPopLevelId, the room count
    and the Chaos quest test are DRLG oracles, the result PG taken from the log otherwise), the logic-box list (DRLG
    state, from the PB lines), attempts ((5h/3)(5w/3), signed truncation), density on the game seed, the class pick and
    the spawn substitution, SpawnTypeRoll on the room seed with the live special count (+0x2C8, from the region at
    PR, then tracked), groups (MinGrp/MaxGrp, fallen/scarab 1/1, sparsePopulate), the special branch (second pick,
    SpecialMonPlace, the champion roll Range(boss.seed, 100) < MonUMod rec 0 +0x1C, unique minions 3 + RangeB(4),
    champion pack seed mod 3 + 1), MonStats minions (RandRangeIncl(PartyMin, PartyMax), minion1/minion2 alternating).
  * Positions (sub_0054DC40_SpawnPosPick, sub_005B2A00_MonSpawnTry): every draw, the ring walk and the cell order,
    PtInRect on the box or room rectangle. The position predicates CollisionTest (MK), LogicRegionIdAt (MR, SPR),
    SpawnClassCellTest (MC), NearWarpTest (SPW) and SpawnPosOnTile (MTT, spawnCol 1) are predicted by tools/collision.py
    (plan 0017) when the log holds the pass-entry grid snapshot (SN, tools/gdb/collision.gdb); the logged results stay
    as checks, and the room and game seed are asserted unchanged across each call. Without a snapshot (plan 0014 logs)
    they are ADR-0004 value oracles as before (SpawnClassCellTest is predicted for the classes it passes outright),
    counted under "oracle". The creation marks (two UNIT_CollMark, then the post-create pattern refresh) are checked
    against the CM lines. Seed oracles: SUnitCreate (the game seed draw is predicted, one step;
    the new unit's seed is taken from MU, and the number of unit-seed steps after Init(step(game).low) is reported,
    with the creations that differ from 2 listed).
  * Special monsters (plan 0018, tools/monspecial.py, docs/findings/monsters/0003-special-monsters.md): no oracle is
    left on the special path. SpecialModsRoll (the champion roll, ChampionModPick / UniqueModPick with ModEligible and
    MonTypeIsA, Range(1)), the unique-minion count, ModsXferCopy, the mod handlers (rndname's unit-seed step and the
    name seed, the aura index on its local seed) and the champion-pack members are predicted, and the unit, room and
    game seeds are asserted at SMRX and SMAX. Logs written with tools/gdb/mon-special.gdb add, and the checker then
    requires: every MonTypeIsA call (MTI), the candidate list, total and draw of every pick (MPK), every handler call
    with its seeds (HD0/HDX; any seed change other than rndname's step is a mismatch) and the same handler on each
    group member (TH0/TH1), the aura draw (AUR/AUR2), each minion's mods after the transfer (XF), and the specials of
    the presets window: superuniques (SU0 .. SUX: placement incl. AutoPos, fixed mods, the difficulty extra picks,
    MinGrp+d .. MaxGrp+d minions, the tail incl. Radament's Range(5) + 2 escorts, mod 22) and the MonPlace 2 / 3
    presets (PM0 .. PMX), each modelled from the room and game seeds at its entry line. The client name roll
    (CN0/CNR/CNH) is checked against the server's predicted name seed for the same unit id (low byte only, see
    monspecial.client_name_seed).
  * The region at P0 is checked against tools/monpool.py built from the -seed N value (first game-seed draw).

Exit 0 only if every check holds. Stdlib only. Read-only.
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import collision  # noqa: E402
import drlg  # noqa: E402
import monpool  # noqa: E402
import monspecial  # noqa: E402
import monstats  # noqa: E402
import mon_sweep  # noqa: E402
import objects  # noqa: E402
from excel_bin import find_file, read_bin  # noqa: E402
from rng import INIT_HIGH, MASK, step  # noqa: E402

DEFAULT_EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
SPAWN_TAGS = {"P0", "PG", "PR", "PB", "PN", "PA", "PC", "PT", "PSP", "PGR", "PGX", "PS2", "PSB", "PCP", "PDEAD", "PX",
              "SP0", "SPW0", "SPW", "SPR0", "SPR", "SPX", "SPF", "MT0", "MTT0", "MTT", "MR0", "MR", "MC0", "MC", "MK0",
              "MK", "MU0", "MU", "MUP", "MTX", "MM0", "MMN", "MMT", "MMX", "G1", "GK", "SMPX", "SMR0", "SMR1", "SMRX",
              "SMA0", "SMA1", "SMAX", "UMN", "UMX", "CP0", "CPN", "CPM",
              # plan 0018 (tools/gdb/mon-special.py)
              "MTI", "MPK", "HD0", "HDX", "TH0", "TH1", "AUR", "AUR2", "XF", "SU0", "SU1", "SUT", "SUX", "PM0", "PMC", "PMX"}
CLIENT_TAGS = {"CN0", "CNR", "CNH"}
SIDE_TAGS = {"SCI", "SCD", "WND", "WNDARM", "WRL", "RW0", "RW1", "RW2", "RW3", "RW4", "LC0", "RL", "AROOM",
             "RRESEED", "OPU0", "OPUX", "OI0", "OIX", "OU0"} | collision.COLL_TAGS | CLIENT_TAGS
# plan 0048 Phase 1: the unit seed at MU is predicted (oracle 14); False restores the plan 0014 seed oracle
UNIT_SEED_MODEL = True
STATE_FROZEN = None       # a counterfactual (tools/chain.py --cf state-stale): a room's first seed is kept for good
ROOM_STATE_MODEL = True   # plan 0048 oracle 21: another room's seed from the chain state (False: taken from MT0)
GAME_L = 1          # monsters/stats input L: game +0x6A or +0x74 not 0 (1 in every logged single-player game)
MASK_BY_SPAWNCOL = {0: 0x3C01, 1: 0x01C0, 2: 0x3F11, 3: 0}     # jump table 0x005B2F04
# Plan 0014 FS2: the guard exits of the spec's [C] blocks, counted and printed even at 0 (counters only, no effect
# on any check). A closed gate is classified from the region state at P0 and PX: +0x0C (nRooms) is read only past
# the lvl test, so -1 at PX means the lvl = 0 exit.
GUARDS = [
    "B1 gate: region = none", "B1 gate: lvl = 0 (nRooms still -1 at PX)",
    "B1 gate: lvl = 0 (MonDen and nRooms not 0, level not 108)", "B1 gate: lvl = 0 or Chaos quest (level 108)",
    "B1 gate: MonDen = 0 (lvl not 0: nRooms read in this call)", "B1 gate: nRooms = 0 (lvl not 0: nRooms read in this call)",
    "B1 gate: lvl = 0, MonDen = 0 or nRooms = 0 (nRooms read earlier)",
    "C1 no logic box", "C1 box skipped: regionId = 0 or kind not 0", "C1 box skipped: left = right = 0",
    "D1 special pick: umon count c = 0", "D1 nPool = 0",
    "F2 min = 0 or max = 0 or max < min", "F2 SpawnPosPick failed", "F2 leader = none",
    "G2 SpawnPosPick failed", "G2 boss = none", "G5 not a champion: return",
    "H1 20 tries failed", "H1 try rejected: NearWarpTest", "H1 try rejected: LogicRegionIdAt",
    "H2 class not valid or no MonStats2 record", "H2 smax < s", "H2 no cell found", "H2 unit = none",
    "H2 cell skipped: outside the rectangle", "H2 cell skipped: LogicRegionIdAt", "H2 cell skipped: SpawnClassCellTest",
    "H2 cell skipped: CollisionTest",
    "I1 minion1 not a valid class: return", "I1 lo >= hi: no draw",
]
F_NEVERCOUNT, F_PLACESPAWN, F_SETBOSS = 0x04, 0x80, 0x10        # 0x006CE270, 0x006CE284, 0x006CE278
WND_PCS = {0x00547A9D: "region build reads Levels +0x2E (0x00547A99)", 0x00547AA3: "region build writes +0x2BE (0x00547A9D)",
           0x0054F0AE: "wanderer tick reads Levels +0x2E (0x0054F0AA)"}


def seed_t(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def fmt(s):
    return "%08x:%08x" % s


class Mismatch(Exception):
    pass


class S:
    """A mutable seed."""
    def __init__(self, t):
        self.lo, self.hi = t

    def t(self):
        return self.lo, self.hi

    def step(self):
        self.lo, self.hi = step(self.lo, self.hi)
        return self.lo

    def rangeb(self, n):                       # RNG_Range / RNG_RangeB, and the inlined copies
        if n & 0x80000000 or n == 0:
            return 0
        return self.step() % n


class Tables:
    def __init__(self, d):
        self.lv, sz = read_bin(find_file(d, "levels", ".bin"))
        assert sz == 0x220
        self.ms, sz = read_bin(find_file(d, "monstats", ".bin"))
        assert sz == 0x1A8
        self.ms2, sz = read_bin(find_file(d, "monstats2", ".bin"))
        assert sz == 0x134
        mu, sz = read_bin(find_file(d, "monumod", ".bin"))
        self.champ_chance = struct.unpack_from("<I", mu[0], 0x1C)[0] if mu else 0
        self.pool = monpool.Tables(d)
        self.ld, _ = read_bin(find_file(d, "leveldefs", ".bin"))
        self.mi, _ = read_bin(find_file(d, "missiles", ".bin"))

    def position(self, lid):
        """Levels.txt Position (leveldefs +0x90)."""
        return struct.unpack_from("<I", self.ld[lid], 0x90)[0] if 0 <= lid < len(self.ld) else 0

    def missile_collision(self, c):
        """Missiles.txt Collision (+0x184)."""
        return self.mi[c][0x184] if 0 <= c < len(self.mi) else 0

    def valid(self, c):
        return 0 <= c < len(self.ms)

    def m(self, c, off, fmt_):
        return struct.unpack_from(fmt_, self.ms[c], off)[0]

    def m2(self, c):
        ex = self.m(c, 0x18, "<h")
        return self.ms2[ex] if 0 <= ex < len(self.ms2) else None


class Room:
    """Model state of one pass."""
    def __init__(self, p0):
        self.p0 = p0


class Pass:
    def __init__(self, chk, ev, t, path):
        self.chk, self.ev, self.t, self.path = chk, ev, t, path
        self.i = 0
        self.units = {}            # unit pointer -> (room, x, y, cls)
        self.other_rs = {}         # room -> seed, for requests on a room other than the pass room
        self.stats = chk.stats

    # --- cursor ------------------------------------------------------------------------------------------------
    def take(self, tag):
        while self.i < len(self.ev):
            tg, d, ln = self.ev[self.i]
            self.i += 1
            if tg in SIDE_TAGS and tg != tag:
                self.side(tg, d, ln)
                continue
            if tg != tag:
                raise Mismatch("line %d: expected %s, log has %s %s" % (ln, tag, tg, json.dumps(d)[:200]))
            return d
        raise Mismatch("log ends, expected %s" % tag)

    def peek(self):
        j = self.i
        while j < len(self.ev) and self.ev[j][0] in SIDE_TAGS:
            j += 1
        return self.ev[j][0] if j < len(self.ev) else None

    def side(self, tg, d, ln=0):
        if tg in collision.COLL_TAGS or tg == "RRESEED":
            self.chk.world.event(tg, d, ln, self.path)
            return
        if tg in CLIENT_TAGS:
            self.chk.client.append((tg, d, ln))
        elif tg == "SCI":
            self.sci.append(d)
        elif tg == "SCD":
            self.chk.fail_("%s: SCD (special count decrement) inside a pass: %s" % (self.path, d))
        elif tg == "WND":
            self.chk.wnd(d)
        elif tg == "AROOM":
            self.chk.on_aroom(d)

    def guard(self, k):
        self.stats["guard " + k] += 1

    # --- plan 0017: the position predicates from tools/collision.py ----------------------------------------------
    def snap(self):
        W = self.chk.world
        return W.P is not None and W.P["room"] == self.room

    def pred(self, name, logged, fn, need_snap=True):
        """Predict a former ADR-0004 value oracle with the collision model; the logged result stays as the check.
        Without a pass snapshot (plan 0014 logs) or when the model needs a room outside it, the logged value is
        taken and counted as an oracle call."""
        if need_snap and not self.snap():
            self.chk.oracle(name + " (no grid snapshot in the log)")
            return logged
        try:
            v = fn()
        except collision.NotLogged as e:
            self.chk.oracle("%s (model needs %s)" % (name, str(e).split(" of room")[0]))
            return logged
        self.eq(name + " (collision model)", logged, v)
        k = "predicted by the collision model: " + name
        self.stats[k] = self.stats.get(k, 0) + 1
        return v

    def eq(self, what, got, want):
        if got != want:
            raise Mismatch("%s: log %s, model %s" % (what, got, want))
        self.chk.checks += 1

    def seeds(self, d, what, room=True, game=True):
        if room:
            self.eq(what + " rs", d["rs"], fmt(self.rs.t()))
        if game:
            self.eq(what + " gs", d["gs"], fmt(self.gs.t()))

    # --- the pass ----------------------------------------------------------------------------------------------
    def run(self):
        p0 = self.take("P0")
        self.room, self.game = p0["room"], p0["game"]
        self.rs, self.gs = S(seed_t(p0["rs"])), S(seed_t(p0["gs"]))
        self.diff = p0["diff"]
        self.exp = p0["exp"]
        self.rect = p0["rect"]
        self.lid = p0["lid"]
        self.sci = []
        reg = p0["reg"]
        self.chk.region_check(self.path, reg, self.diff, p0["exp"])
        self.chk.region_snapshot(self, reg)
        pg = self.take("PG")
        if reg is None or reg["den"] == 0:
            self.eq("gate (no region or MonDen 0)", pg["r"], 0)
            if reg is not None:
                self.stats["closed gate (MonDen 0)"] = self.stats.get("closed gate (MonDen 0)", 0) + 1
                self.chk.closed_levels.add(self.lid)
        else:
            self.stats["gate result from DRLG oracles (%d)" % pg["r"]] = self.stats.get("gate result from DRLG oracles (%d)" % pg["r"], 0) + 1
        if pg["r"] == 0:
            px = self.take("PX")
            self.seeds(px, "PX (gate closed)")
            if reg is None:
                self.guard("B1 gate: region = none")
            elif px["reg"]["nrooms"] < 0:
                self.guard("B1 gate: lvl = 0 (nRooms still -1 at PX)")
            elif reg["den"] != 0 and px["reg"]["nrooms"] != 0:
                self.guard("B1 gate: lvl = 0 or Chaos quest (level 108)" if self.lid == 108 else
                           "B1 gate: lvl = 0 (MonDen and nRooms not 0, level not 108)")
            elif reg["nrooms"] < 0:
                self.guard("B1 gate: MonDen = 0 (lvl not 0: nRooms read in this call)" if reg["den"] == 0 else
                           "B1 gate: nRooms = 0 (lvl not 0: nRooms read in this call)")
            else:
                self.guard("B1 gate: lvl = 0, MonDen = 0 or nRooms = 0 (nRooms read earlier)")
            return "gate"
        pr = self.take("PR")
        R = pr["reg"]
        self.eq("gate counts the call (+0x04)", R["calls"], reg["calls"] + 1)
        self.region = R
        self.nspec = R["nspec"]
        den = min(R["den"], 10000)
        populated = False
        self.groups = []
        if self.peek() != "PB":
            self.guard("C1 no logic box")
        while self.peek() == "PB":
            box = self.take("PB")
            if box["rid"] == 0 or box["kind"] != 0:
                self.guard("C1 box skipped: regionId = 0 or kind not 0")
                continue
            l, t_, r, b = box["rect"]
            if l == 0 and r == 0:
                self.guard("C1 box skipped: left = right = 0")
                continue
            l, t_, r, b = 5 * l, 5 * t_, 5 * r, 5 * b
            n = drlg_div3(b - t_) * drlg_div3(r - l)
            self.eq("attempts", self.take("PN")["n"], n)
            while n > 0:
                n -= 1
                low = self.gs.step()
                rr = low % 100000
                if rr > den:
                    continue
                pa = self.take("PA")
                self.eq("density r", pa["r"], rr)
                self.seeds(pa, "PA")
                cls, rec = self.pick_class(20, False)
                pc = self.take("PC")
                self.eq("class pick", pc["cls"], cls)
                self.eq("class pick rec != 0", pc["rec"] != 0, rec)
                self.eq("PC rs", pc["rs"], fmt(self.rs.t()))
                if not rec:
                    px = self.take("PX")
                    self.seeds(px, "PX (no record)")
                    return "norec"
                ty = self.type_roll()
                pt = self.take("PT")
                self.eq("type roll", pt["t"], ty)
                self.eq("PT rs", pt["rs"], fmt(self.rs.t()))
                self.eq("PT special count", pt["nspec"], self.nspec)
                if ty == 1:
                    ty = 2
                if ty == 0:
                    cls2, _ = self.pick_class(0, True)
                    ps2 = self.take("PS2")
                    self.eq("special class pick", ps2["cls"], cls2)
                    self.eq("PS2 rs", ps2["rs"], fmt(self.rs.t()))
                    boss = self.special_spawn(box, cls2)
                    psb = self.take("PSB")
                    self.eq("special boss", psb["boss"], boss or 0)
                    self.seeds(psb, "PSB")
                    if boss:
                        self.champion_pack(boss, box, cls2)
                        pcp = self.take("PCP")
                        self.seeds(pcp, "PCP")
                        self.eq("special count after the pack (+0x2C8)", pcp["nspec"], self.nspec)
                        populated = True
                else:
                    if self.t.m(cls, 0x02, "<h") in (19, 91):
                        mn, mx = 1, 1
                    else:
                        mn, mx = self.t.m(cls, 0x2F, "<B"), self.t.m(cls, 0x30, "<B")
                    sp = self.t.m(cls, 0x31, "<B")
                    if sp:
                        r2 = self.gs.step() % 100
                        psp = self.take("PSP")
                        self.eq("sparsePopulate r", psp["r"], r2)
                        self.stats["sparsePopulate rolls"] = self.stats.get("sparsePopulate rolls", 0) + 1
                        if r2 > sp:
                            continue
                    pgr = self.take("PGR")
                    self.eq("group class/min/max", (pgr["cls"], pgr["min"], pgr["max"]), (cls, mn, mx))
                    self.seeds(pgr, "PGR")
                    leader = self.spawn_group(box, cls, mn, mx)
                    pgx = self.take("PGX")
                    self.eq("group leader", pgx["leader"], leader or 0)
                    self.seeds(pgx, "PGX")
                    if leader:
                        populated = True
        px = self.take("PX")
        self.seeds(px, "PX")
        self.eq("populated rooms (+0x08)", px["reg"]["popd"], R["popd"] + (1 if populated else 0))
        self.eq("special count at exit", px["reg"]["nspec"], self.nspec)
        return "populated" if populated else "empty"

    # --- picks -------------------------------------------------------------------------------------------------
    def pick_class(self, threshold, special):
        R, t = self.region, self.t
        if special and self.diff == 0:
            um = t.pool.slots(R["lid"], 0x9A)       # Levels +0x35 is filled at load (DRLG_LoadLevels): slots to the first blank
            if not um:
                self.guard("D1 special pick: umon count c = 0")
                return 0, False
            cls = um[self.rs.rangeb(len(um))]
            self.stats["special class from umon (normal)"] = self.stats.get("special class from umon (normal)", 0) + 1
            return cls, t.valid(cls)
        if R["npool"] == 0:
            self.guard("D1 nPool = 0")
            return 0, False
        w = self.rs.rangeb(R["rsum"]) + 1
        i = 0
        while i < R["npool"]:
            w -= R["ents"][i][1]
            if w <= 0:
                break
            i += 1
        cls = R["ents"][i][0]
        if t.valid(cls) and t.m(cls, 0x20, "<h") >= 0 and t.m(cls, 0x0E, "<B") & F_PLACESPAWN:
            r = self.rs.step() % 100
            k = "spawn substitution (threshold %d) %s" % (threshold, "taken" if r > threshold else "kept")
            self.stats[k] = self.stats.get(k, 0) + 1
            if r > threshold:
                cls = t.m(cls, 0x20, "<h")
        return cls, t.valid(cls)

    def type_roll(self):
        R = self.region
        u = self.nspec & 0xFF
        rec = {"u": u, "umin": R["umin"], "umax": R["umax"], "draws": []}
        res = None
        if u < R["umin"] and R["nrooms"] != 0:
            r = self.rs.step() % 100
            lim = int((R["calls"] * 100) / R["nrooms"])         # i32 idiv, both positive here
            rec["draws"].append(("umin", r, lim))
            if r < lim:
                res = 0
        if res is None and u < R["umax"]:
            r = self.rs.step() % 100
            rec["draws"].append(("umax", r))
            if r <= 5:
                res = 0
        if res is None:
            r = self.rs.step() % 100
            rec["draws"].append(("last", r))
            res = 2 if r > 35 else 1
        rec["res"] = res
        self.chk.type_rolls.append(rec)
        return res

    # --- positions ---------------------------------------------------------------------------------------------
    def spawn_pos_pick(self, room, box, cls, warp):
        sp0 = self.take("SP0")
        if box:
            l, t_, r, b = [5 * v for v in box["rect"]]
            x0, y0, w, h = l + 1, t_ + 1, r - (l + 1), b - (t_ + 1)
        else:
            rx, ry, rw, rh = self.room_rect(room)
            x0, y0, w, h = rx + 1, ry + 1, rw - 1, rh - 1
        self.eq("SP0 room/box/class/warp", (sp0["room"], sp0["box"], sp0["cls"], sp0["warp"]),
                (room, box["box"] if box else 0, cls, warp))
        self.eq("SP0 bounds", (sp0["x0"], sp0["y0"], sp0["w"], sp0["h"]), (x0, y0, w, h))
        self.seeds(sp0, "SP0")
        for _ in range(20):
            x = x0 + self.rs.rangeb(w)
            y = y0 + self.rs.rangeb(h)
            if warp:
                a = self.take("SPW0")
                self.eq("NearWarpTest args", (a["x"], a["y"]), (x, y))
                self.seeds(a, "SPW0")
                a = self.take("SPW")
                self.seeds(a, "SPW (exit)")
                self.pred("NearWarpTest", a["r"], lambda: self.chk.world.near_warp_test(room, x, y, self.lid))
                if a["r"]:
                    self.guard("H1 try rejected: NearWarpTest")
                    continue
            if box:
                a = self.take("SPR0")
                self.eq("LogicRegionIdAt args", (a["x"], a["y"]), (x, y))
                self.seeds(a, "SPR0")
                a = self.take("SPR")
                self.seeds(a, "SPR (exit)")
                self.pred("LogicRegionIdAt (pos pick)", a["r"], lambda: self.chk.world.logic_region_id_at(room, x, y))
                if a["r"] != box["rid"]:
                    self.guard("H1 try rejected: LogicRegionIdAt")
                    continue
            ok = self.spawn_try(room, box, cls, 1, 0, x, y, -1, 0x01)
            if ok:
                a = self.take("SPX")
                self.eq("SPX", (a["x"], a["y"]), (x, y))
                return x, y
        self.take("SPF")
        self.guard("H1 20 tries failed")
        return None

    def room_rect(self, room):
        if room == self.room:
            return self.rect
        r = self.chk.room_rects.get(room)
        if r is None:
            raise Mismatch("rect of room %08x not logged" % room)
        return r

    def spawn_try(self, room, box, cls, a10, a14, cx, cy, rad, fl):
        """sub_005B2A00_MonSpawnTry; returns the unit pointer, 1 (probe) or 0."""
        t = self.t
        mt = self.take("MT0")
        self.eq("request", (mt["game"], mt["room"], mt["box"], mt["cls"], mt["a10"], mt["a14"], mt["x"], mt["y"], mt["rad"], mt["fl"]),
                (self.game, room, box["box"] if box else 0, cls, a10, a14, cx, cy, rad, fl))
        rsd = self.room_seed(room, mt)
        self.eq("MT0 rs", mt["rs"], fmt(rsd.t()))
        self.eq("MT0 gs", mt["gs"], fmt(self.gs.t()))
        res = self.spawn_try_body(room, box, cls, a10, a14, cx, cy, rad, fl, rsd)
        mx = self.take("MTX")
        self.eq("MonSpawnTry result", mx["eax"], res)
        self.eq("MTX rs", mx["rs"], fmt(rsd.t()))
        self.eq("MTX gs", mx["gs"], fmt(self.gs.t()))
        return res

    def room_seed(self, room, mt):
        """The seed a request draws from is its room's (+0x6C). A request on another room (a frog demon placed on a
        tile of a neighbour room, then its group or minions) takes that room's seed from the log the first time in
        a pass (seed oracle, counted); the draws after it are predicted."""
        if room == self.room:
            return self.rs
        s = self.other_rs.get(room)
        if s is None:
            st = self.chk.room_state.get(room) if self.chk.room_state_model else None
            if st is not None:
                # plan 0048 Phase 1, oracle 21: that room's seed carried as chain state (its activation seed, or its
                # seed at the end of its last pass, as the model predicted it); MT0's rs is the check
                s = self.other_rs[room] = S(st)
                k = "seed of another room at its first request in a pass, from the chain state (oracle 21)"
                self.stats[k] = self.stats.get(k, 0) + 1
            else:
                s = self.other_rs[room] = S(seed_t(mt["rs"]))
                self.chk.oracle("seed of another room at its first request in a pass (taken from MT0)")
        return s

    def spawn_try_body(self, room, box, cls, a10, a14, cx, cy, rad, fl, rsd):
        t = self.t
        if not t.valid(cls):
            self.guard("H2 class not valid or no MonStats2 record")
            return 0
        m2 = t.m2(cls)
        if m2 is None:
            self.guard("H2 class not valid or no MonStats2 record")
            return 0
        scol = m2[0x0A]
        mask = MASK_BY_SPAWNCOL.get(scol, 0x3C01)
        if box:
            L, T, Rt, B = [5 * v for v in box["rect"]]
        else:
            rx, ry, rw, rh = self.room_rect(room)
            L, T, Rt, B = rx, ry, rx + rw, ry + rh
        if not room:
            return 0
        if rad < 0:
            s, smax = 0, 0
        else:
            s, smax = 3, 3 * rad
        found = None
        if scol == 1 and not (0x102 <= cls <= 0x107) and cls != 0x99:
            return self.spawn_on_tile(room, box, cls, a10, a14, fl, rsd)
        if s > smax:
            self.guard("H2 smax < s")
            return 0
        size = struct.unpack("b", m2[0x08:0x09])[0]
        while s <= smax and found is None:
            if rsd.step() & 1:
                dx, dy, dirx, diry = s, rsd.rangeb(s), 0, 1
            else:
                dx, dy, dirx, diry = rsd.rangeb(s), s, 1, 0
            if rsd.step() & 1:
                dx = -dx
            if rsd.step() & 1:
                dy = -dy
            x, y = cx + dx, cy + dy
            l, r = cx - s, cx + s
            tp, bt = cy - s, cy + s
            cnt = 8 * s if 8 * s else 1
            while cnt > 0:
                if x == l and y == tp:
                    dirx, diry = 1, 0
                if x == r:
                    if y == tp:
                        dirx, diry = 0, 1
                    if y == bt:
                        dirx, diry = -1, 0
                if x == l:
                    if y == bt:
                        dirx, diry = 0, -1
                    if y == tp and x == r and y == bt:
                        dirx, diry = 0, 0
                y += diry
                x += dirx
                cnt -= 1
                if not (L <= x < Rt and T <= y < B):
                    self.guard("H2 cell skipped: outside the rectangle")
                    continue
                if box:
                    a = self.take("MR0")
                    self.eq("LogicRegionIdAt args", (a["room"], a["x"], a["y"]), (room, x, y))
                    self.eq("MR0 rs", a["rs"], fmt(rsd.t()))
                    a = self.take("MR")
                    self.eq("MR rs (exit)", a["rs"], fmt(rsd.t()))
                    self.pred("LogicRegionIdAt (ring)", a["r"], lambda: self.chk.world.logic_region_id_at(room, x, y))
                    if a["r"] != box["rid"]:
                        self.guard("H2 cell skipped: LogicRegionIdAt")
                        continue
                a = self.take("MC0")
                self.eq("SpawnClassCellTest args", (a["room"], a["x"], a["y"]), (room, x, y))
                self.eq("MC0 rs", a["rs"], fmt(rsd.t()))
                a = self.take("MC")
                self.eq("MC rs (exit)", a["rs"], fmt(rsd.t()))
                self.eq("MC gs (exit)", a["gs"], fmt(self.gs.t()))
                special = t.m(cls, 0x02, "<h") in collision.CLASS_CELL
                self.pred("SpawnClassCellTest", 1 if a["r"] else 0,
                          lambda: self.chk.world.spawn_class_cell_test(cls, room, x, y, 1), need_snap=special)
                if not a["r"]:
                    self.guard("H2 cell skipped: SpawnClassCellTest")
                    continue
                a = self.take("MK0")
                self.eq("CollisionTest args", (a["room"], a["x"], a["y"], a["size"], a["mask"]), (room, x, y, size, mask))
                self.eq("MK0 rs", a["rs"], fmt(rsd.t()))
                self.eq("MK0 gs", a["gs"], fmt(self.gs.t()))
                a = self.take("MK")
                self.eq("MK rs (exit)", a["rs"], fmt(rsd.t()))
                self.eq("MK gs (exit)", a["gs"], fmt(self.gs.t()))
                self.pred("CollisionTest", a["r"], lambda: self.chk.world.collision_test(room, x, y, size, mask))
                if self.snap():
                    self.coll_cases(room, x, y, size, mask, a["r"])
                if a["r"] != 0 and not (fl & 0x80):
                    self.guard("H2 cell skipped: CollisionTest")
                    continue
                if a["r"] != 0:
                    self.stats["CollisionTest bypassed by R.flags & 0x80"] = self.stats.get("CollisionTest bypassed by R.flags & 0x80", 0) + 1
                found = (x, y)
                break
            s += 3
        if found is not None and (found[0] == 0 or found[1] == 0):
            self.stats["MonSpawnTry exit on x = 0 or y = 0"] = self.stats.get("MonSpawnTry exit on x = 0 or y = 0", 0) + 1
        if found is None:
            self.guard("H2 no cell found")
        if found is None or found[0] == 0 or found[1] == 0:
            return 0
        if fl & 0x01:
            return 1
        x, y = found
        return self.create(room, cls, x, y, fl, rsd)

    def spawn_on_tile(self, room, box, cls, a10, a14, fl, rsd):
        """spawnCol 1 (frog demons): sub_005B2700_SpawnPosOnTile, then RoomAtSubtile; no other test (0x005B2BB1..0x005B2BC7)."""
        W = self.chk.world
        a = self.take("MTT0")
        self.eq("MTT0 rs", a["rs"], fmt(rsd.t()))
        pos = None
        modelled = False
        if self.snap():
            r0 = rsd.t()
            try:
                pos = W.spawn_pos_on_tile(room, rsd)
                modelled = True
            except collision.NotLogged as e:
                rsd.lo, rsd.hi = r0
                self.chk.oracle("SpawnPosOnTile (model needs %s)" % str(e).split(" of room")[0])
        else:
            self.chk.oracle("SpawnPosOnTile (seed oracle, no grid snapshot in the log)")
        b = self.take("MTT")
        if modelled:
            self.eq("SpawnPosOnTile (collision model) x, y", (b["x"], b["y"]), pos if pos else (0, 0))
            self.eq("SpawnPosOnTile rs", b["rs"], fmt(rsd.t()))
            k = "predicted by the collision model: SpawnPosOnTile"
            self.stats[k] = self.stats.get(k, 0) + 1
        else:
            rsd.lo, rsd.hi = seed_t(b["rs"])
            pos = (b["x"], b["y"])
        x, y = pos if pos else (0, 0)
        if x == 0 or y == 0:
            self.guard("H2 no cell found")
            return 0
        if fl & 0x01:
            return 1
        room2 = room
        if self.snap():
            try:
                room2 = W.room_at(room, x, y)
            except collision.NotLogged:
                self.chk.oracle("RoomAtSubtile after SpawnPosOnTile (room outside the snapshot)")
        self.stats["spawnCol 1 creations on a tile"] = self.stats.get("spawnCol 1 creations on a tile", 0) + 1
        return self.create(room2, cls, x, y, fl, rsd)

    def coll_cases(self, room, x, y, size, mask, r):
        """Counters for the plan 0017 required cases (R2, the size mix); no effect on any check."""
        W = self.chk.world
        st = self.stats
        k = "CollisionTest calls by (size, mask): (%d, 0x%04x)" % (size, mask)
        st[k] = st.get(k, 0) + 1
        for b in range(16):
            if r & (1 << b):
                k = "CollisionTest rejections with result bit %2d (0x%04x)" % (b, 1 << b)
                st[k] = st.get(k, 0) + 1
        if r == 0x27:
            st["CollisionTest results 0x27 (a footprint cell in no room)"] = st.get("CollisionTest results 0x27 (a footprint cell in no room)", 0) + 1
        try:
            fp = W.footprint(x, y, size)
            vals = [W.cell_value(room, fx, fy) for fx, fy in fp]
            if r == 0:
                if any(v is not None and v & 0x100 and not v & mask for v in vals):
                    st["R2: accepted placements on a cell with 0x100 and no masked bit"] = st.get(
                        "R2: accepted placements on a cell with 0x100 and no masked bit", 0) + 1
                if any(v == 0x100 for v in vals):
                    st["R2: accepted placements on a cell whose value is exactly 0x100"] = st.get(
                        "R2: accepted placements on a cell whose value is exactly 0x100", 0) + 1
                return
            r0 = W.collision_test_pristine(room, x, y, size, mask)
            if r0 == 0:
                sizes = sorted({s_ for f in fp for s_ in W.P["marks"].get(f, [])})
                k = "tests rejected only by in-pass marks: test size %d, marking sizes %s" % (size, sizes)
                st[k] = st.get(k, 0) + 1
        except collision.NotLogged:
            pass

    def create(self, room, cls, x, y, fl, rsd):
        mu0 = self.take("MU0")
        self.eq("SUnitCreate x, y, mode", (mu0["x"], mu0["y"], mu0["mode"]), (x, y, 3 if fl & 0x20 else 1))
        self.eq("MU0 rs", mu0["rs"], fmt(rsd.t()))
        self.eq("MU0 gs", mu0["gs"], fmt(self.gs.t()))
        g_after = step(self.gs.lo, self.gs.hi)
        mu = self.take("MU")
        u = mu["unit"]
        n_eq = 0
        if u and u["cls"] == cls:
            # plan 0048: the unit seed first (oracle 14); MonEquipInit's items (oracle 13, [I]) step the game seed twice
            # each inside the creation
            n_eq = self.chk.unit_seed(self, cls, (g_after[0], INIT_HIGH), u["us"]) or 0
        g_end = g_after
        for _ in range(2 * n_eq):
            g_end = step(*g_end)
        self.eq("SUnitCreate game-seed draw (one step%s)" % (", and two per MonEquip item" if n_eq else ""), mu["gs"],
                fmt(g_end))
        self.gs = S(g_end) if self.gs is not None else None
        self.eq("MU rs", mu["rs"], fmt(rsd.t()))
        if not u:
            self.guard("H2 unit = none")
            return 0
        self.eq("created class", u["cls"], cls)
        if self.snap() and not isinstance(self, PresetMonPass):
            try:
                self.chk.world.creation_mark(room, x, y, cls, self.path, self.ev[self.i - 1][2])
            except collision.NotLogged as e:
                self.chk.oracle("creation mark (model needs %s)" % str(e).split(" of room")[0])
        us0 = (g_after[0], INIT_HIGH)
        j = drlg_steps(us0, seed_t(u["us"]))
        self.chk.unit_steps[j] = self.chk.unit_steps.get(j, 0) + 1
        if j != 2:
            self.chk.unit_steps_odd.append((self.path, self.ev[self.i - 1][2], self.lid, cls, j))
        self.chk.creations.append((self.path, self.lid, cls, x, y, u["id"], fl))
        mods = list(u.get("mods") or [0] * 9)
        for m in monspecial.post_create_mods(self.chk.sp, cls):    # MonPostCreateMods, after MU (no draw)
            monspecial.mod_append(mods, m)
        self.units[u["u"]] = {"u": u["u"], "id": u["id"], "room": room, "x": x, "y": y, "cls": cls, "us": S(seed_t(u["us"])),
                              "mods": mods}
        U = self.units[u["u"]]
        mup = self.take("MUP")
        if self.snap() and not isinstance(self, PresetMonPass):
            try:
                self.chk.world.creation_remark(room, x, y, cls, self.path, self.ev[self.i - 1][2])
            except collision.NotLogged as e:
                self.chk.oracle("creation re-mark (model needs %s)" % str(e).split(" of room")[0])
        self.eq("post-create setup: unit seed unchanged", mup["us"], fmt(U["us"].t()))
        self.eq("post-create setup: rs unchanged", mup["rs"], fmt(rsd.t()))
        self.eq("post-create setup: gs unchanged", mup["gs"], fmt(self.gs.t()))
        if not fl & 0x40:
            self.minions(u["u"], fl)
        return u["u"]

    def near_unit(self, unit, box, cls, a10, rad, fl):
        U = self.units[unit]
        return self.spawn_try(U["room"], box, cls, a10, 0, U["x"], U["y"], rad, fl)

    TENTACLE_XY = None

    def tentacles(self, unit, fl, m1):
        """plan 0038 batch H4b: MinionsSpawn's BaseId-261 branch (0x005B28C1..0x005B291C) and sub_005B2570 (named
        TentacleMinionsSpawn in monsters/0002). The count is RandRangeIncl(PartyMin, PartyMax) on the head's seed
        (0x005B28FA, logged as MMT); o = not(request flags bit 2) (0x005B2903..0x005B290A); the branch steps the head's
        seed once more, j = low % 6 (unsigned), and places each limb at the head's cell plus row o*6 + j of the
        offset table 0x006E2CF0 (3 x 6 pairs of i32), j <- (j + 5) % 6, with MonSpawnTry(no box, minion1, a10 1,
        radius -1, flags 0x40) from the head's room."""
        t = self.t
        U = self.units[unit]
        cls = U["cls"]
        if Pass.TENTACLE_XY is None:
            Pass.TENTACLE_XY = struct.unpack("<36i", drlg.exe_read(drlg.DEFAULT_EXE, 0x006E2CF0, 144))
        lo, hi = t.m(cls, 0x2C, "<B"), t.m(cls, 0x2D, "<B")
        if lo >= hi:
            self.guard("I1 lo >= hi: no draw")
        n = lo if lo >= hi else lo + U["us"].rangeb(hi - lo + 1)
        mm = self.take("MMT")
        self.eq("tentacle count", mm["n"], n)
        self.eq("MMT us", mm["us"], fmt(U["us"].t()))
        o = (~(fl >> 2)) & 1
        j = U["us"].step() % 6
        self.stats["tentacle heads (0x005B2570), o = %d" % o] = self.stats.get("tentacle heads (0x005B2570), o = %d" % o, 0) + 1
        for _ in range(max(n, 0)):
            dx, dy = Pass.TENTACLE_XY[2 * (o * 6 + j)], Pass.TENTACLE_XY[2 * (o * 6 + j) + 1]
            self.spawn_try(U["room"], None, m1, 1, 0, U["x"] + dx, U["y"] + dy, -1, 0x40)
            self.stats["tentacle limbs created or tried"] = self.stats.get("tentacle limbs created or tried", 0) + 1
            j = (j + 5) % 6

    def minions(self, unit, fl=0):
        t = self.t
        U = self.units[unit]
        cls = U["cls"]
        m0 = self.take("MM0")
        self.eq("MinionsSpawn unit, us", (m0["unit"], m0["us"]), (unit, fmt(U["us"].t())))
        m1 = t.m(cls, 0x26, "<h")
        if t.valid(cls) and 0 <= m1 < len(t.ms):
            if t.m(cls, 0x02, "<h") == 261:
                self.tentacles(unit, fl, m1)            # plan 0038 batch H4b: the separate branch, then the exit
                mx = self.take("MMX")
                self.eq("MMX unit, us (tentacle branch)", (mx["unit"], mx["us"]), (unit, fmt(U["us"].t())))
                return
            lo, hi = t.m(cls, 0x2C, "<B"), t.m(cls, 0x2D, "<B")
            if lo >= hi:
                self.guard("I1 lo >= hi: no draw")
            n = lo if lo >= hi else lo + U["us"].rangeb(hi - lo + 1)
            mm = self.take("MMN")
            self.eq("MonStats minion count", mm["n"], n)
            self.eq("MMN us", mm["us"], fmt(U["us"].t()))
            m2 = t.m(cls, 0x28, "<h")
            two = 0 <= m2 < len(t.ms)
            k = 0
            for _ in range(max(n, 0)):
                mc = (m1, m2)[k]
                self.near_unit(unit, None, mc, 1, 4, 0x40)
                self.stats["MonStats minions created or tried"] = self.stats.get("MonStats minions created or tried", 0) + 1
                k = k + 1
                if k > (1 if two else 0):
                    k = 0
        else:
            self.guard("I1 minion1 not a valid class: return")
        mx = self.take("MMX")
        self.eq("MMX unit, us", (mx["unit"], mx["us"]), (unit, fmt(U["us"].t())))

    def spawn_group(self, box, cls, mn, mx):
        if mn == 0 or mx == 0 or mx < mn:
            self.guard("F2 min = 0 or max = 0 or max < min")
            return 0
        pos = self.spawn_pos_pick(self.room, box, cls, 1)
        if pos is None:
            self.guard("F2 SpawnPosPick failed")
            return 0
        leader = self.spawn_try(self.room, box, cls, 1, 0, pos[0], pos[1], -1, 0)
        if not leader:
            self.guard("F2 leader = none")
            return 0
        if cls == 528:
            raise Mismatch("evilhut object (0x0054E03B) not modelled")
        U = self.units[leader]
        g1 = self.take("G1")
        self.eq("G1 leader, us", (g1["leader"], g1["us"]), (leader, fmt(U["us"].t())))
        k = U["us"].rangeb(mx - mn + 1)
        gk = self.take("GK")
        self.eq("group size draw", gk["r"], k)
        self.eq("GK us", gk["us"], fmt(U["us"].t()))
        k += mn - 1
        self.groups.append(("normal", cls, 1 + k))
        self.chk.group_sizes.append((cls, mn, mx, 1 + k))
        for _ in range(max(k, 0)):
            self.near_unit(leader, box, cls, 1, 3, 0)
        return leader

    def mark_special(self, unit, mf_before_has8):
        sci = self.sci.pop(0) if self.sci else None
        if mf_before_has8:
            if sci is not None:
                raise Mismatch("special count incremented for a unit already flagged 0x08")
            return
        if sci is None:
            raise Mismatch("MonMarkSpecial: no increment of +0x2C8 logged")
        self.eq("special count before the increment", sci["before"], self.nspec)
        self.nspec += 1
        self.chk.nspec_incr += 1

    # --- plan 0018: special monsters (tools/monspecial.py) -------------------------------------------------------
    def opt(self, tag):
        """Take a plan 0018 tag when the log was written with tools/gdb/mon-special.py (required then), else None."""
        if not self.chk.new_tags:
            return None
        return self.take(tag)

    def note(self, k, n=1):
        self.stats[k] = self.stats.get(k, 0) + n

    def picks_check(self, picks):
        """The MTI and MPK lines of the mod picks, against the model's records."""
        for p in picks:
            self.note("mod picks: %s" % p["kind"])
            for cls, t, r in p["isa"]:
                a = self.opt("MTI")
                if a is not None:
                    self.eq("MonTypeIsA (class, type, result)", (a["cls"], a["t"], a["r"]), (cls, t, r))
                self.note("MonTypeIsA calls modelled (matrix builder 0x00658460)")
                if r:
                    self.note("MonTypeIsA exclusions (lightning x sandleaper)")
            a = self.opt("MPK")
            if a is not None:
                self.eq("mod pick kind", a["k"], "c" if p["kind"] == "champion" else "u")
                self.eq("mod pick seed after the draw", a["us"], fmt(p["us"]))
                self.eq("mod pick candidates (row, weight)", [tuple(c) for c in a["c"]], [tuple(c) for c in p["cands"]])
                self.eq("mod pick total", a["total"], p["total"])
                self.eq("mod pick draw", a["x"], p["x"])
            if p["res"]:
                k = "mods drawn (%s pick), difficulty %d: %d" % (p["kind"], self.diff, p["res"])
                self.chk.mods_drawn[k] = self.chk.mods_drawn.get(k, 0) + 1

    def roll(self, U, mods, cls, allow):
        """SpecialModsRoll from SMR0 to SMRX: every draw predicted (no oracle)."""
        sp = self.chk.sp
        r0 = self.take("SMR0")
        self.eq("SpecialModsRoll unit, us, allowChampion", (r0["unit"]["u"], r0["unit"]["us"], r0["allow"]),
                (U["u"], fmt(U["us"].t()), allow))
        self.eq("SpecialModsRoll mods on entry", r0["unit"].get("mods"), mods)
        if r0.get("exp") is not None:
            self.eq("SMR0 difficulty, expansion", (r0["diff"], r0["exp"]), (self.diff, self.exp))
        state = {}

        def hook(ev, d):
            if ev == "r100":
                r1 = self.take("SMR1")
                self.eq("champion roll Range(100)", r1["r"], d)
                self.eq("champion chance (MonUMod rec 0 +0x1C)", r1["c"], self.t.champ_chance)
                self.eq("SMR1 us", r1["us"], fmt(U["us"].t()))
                state["r"] = d
        out = sp.mods_roll(U["us"], mods, self.diff, self.exp, cls, allow, hook)
        self.picks_check(out["picks"])
        rx = self.take("SMRX")
        self.eq("SMRX champion flag 0x04", bool(rx["unit"]["mf"] & 4), out["champion"])
        self.eq("SpecialModsRoll mods (model)", rx["unit"]["mods"], mods)
        self.eq("SpecialModsRoll exit us (model)", rx["unit"]["us"], fmt(U["us"].t()))
        if allow and "r" in state:
            self.chk.champ_rolls.append((state["r"], out["champion"]))
        self.note("special mods rolls predicted (SMR0..SMRX)")
        return out["champion"]

    def handlers(self, U, mods, what):
        """SpecialModsApply after the minions (SMA1 .. SMAX): the handler of every mod in 1..4 + the list; rndname
        steps the unit seed and sets the name seed, aura draws on Init(nameSeed); everything else is asserted to
        keep the unit, room and game seeds (with flag 0 on each group member too)."""
        sp = self.chk.sp
        for m in sp.handler_seq(mods, every=True):
            if not sp.handler[m]:
                # development logs only: an HDX at a null handler's jump target (logger fixed before the record)
                if self.chk.new_tags and self.peek() == "HDX" and self.ev[self.i][1].get("m") == m:
                    self.take("HDX")
                continue
            h0 = self.opt("HD0")
            if h0 is not None:
                self.eq("handler mod, unit", (h0["m"], h0["u"]), (m, U["u"]))
                self.eq("handler entry us", h0["us"], fmt(U["us"].t()))
            if m == monspecial.M_RNDNAME:
                U["us"].step()
                U["ns"] = U["us"].lo & 0xFFFF
                self.note("rndname steps (unit seed, name seed)")
            if m == monspecial.M_AURA:
                self.aura(U)
            if h0 is not None:
                hx = self.take("HDX")
                self.eq("handler exit mod", hx["m"], m)
                self.eq("handler exit us (model)", hx["us"], fmt(U["us"].t()))
                self.eq("handler keeps the room and game seeds (seed-asserted callees)", (hx["rs"], hx["gs"]),
                        (h0["rs"], h0["gs"]))
                self.note("handler calls seed-asserted (%s): mod %d" % (what, m))
                while self.peek() == "TH0":
                    t0 = self.take("TH0")
                    t1 = self.take("TH1")
                    self.eq("group member handler mod", t0["m"], m)
                    self.eq("group member handler (flag 0) keeps its seeds", (t1["u"], t1["us"], t1["rs"], t1["gs"]),
                            (t0["u"], t0["us"], t0["rs"], t0["gs"]))
                    self.note("group-member handler calls seed-asserted")
                    if t0["u"] == U["u"]:
                        self.note("group walk reached the special itself")

    def aura(self, U):
        """UModAura's draw (local seed); the level is MonStatsInit's (monsters/0001 section 5) + 3 (leveladd)."""
        a = self.opt("AUR")
        lvl_model = monpool.monster_level(self.t.pool, U["cls"], self.lid, self.diff, self.exp)[0] + 3
        if a is None:
            return
        self.eq("aura unit, name seed", (a["u"], a["ns"]), (U["u"], U.get("ns")))
        # the level is a monsters/stats input (MonStatsInit, then leveladd): compared and reported, not gating; the
        # draw itself is predicted from the modelled level
        k = "aura level %s MonStatsInit + 3 (%s)" % ("=" if a["lvl"] == lvl_model else "!=", "expansion" if self.exp else "classic")
        self.note(k)
        if a["lvl"] != lvl_model:
            self.chk.aura_level_diff.append((self.path, self.ev[self.i - 1][2], U["cls"], self.diff, self.exp, a["lvl"], lvl_model))
        n, r, idx = self.chk.sp.aura(U["ns"], lvl_model, U.get("su", -1))
        self.eq("aura n, Range(Init(nameSeed), n)", (a["n"], a["r"]), (n, r))
        a2 = self.take("AUR2")
        self.eq("aura index", (a2["u"], a2["idx"]), (U["u"], idx))
        self.note("aura draws predicted")
        k = "aura index %d (n %d)" % (idx, n)
        self.chk.mods_drawn[k] = self.chk.mods_drawn.get(k, 0) + 1

    def apply_exit(self, U, mods, what):
        a = self.take("SMAX")
        self.eq("SMAX us (model)", a["us"], fmt(U["us"].t()))
        if "u" in a and a["u"] is not None:
            self.eq("SMAX mods", a["u"]["mods"], mods)
            self.eq("SMAX name seed (model)", a["ns"], U.get("ns"))
            if U.get("ns") is not None:
                self.chk.ns_pred[(self.path, a["u"]["id"])] = (U["ns"], what, self.diff)
        return a

    def unique_minions(self, U, box, mcls, n, mods):
        made = 0
        for _ in range(n):
            res = self.near_unit(U["u"], box, mcls, 1, 3, 0x40)
            if res and res != 1:
                made += 1
                M = self.units[res]
                want = monspecial.xfer_copy(self.chk.sp, M["mods"], mods)
                xf = self.opt("XF")
                if xf is not None:
                    self.eq("ModsXferCopy minion, boss", (xf["m"], xf["b"]), (res, U["u"]))
                    self.eq("ModsXferCopy minion mods (model)", xf["mods"], want)
                gained = [m for m in want if m and m not in M["mods"]]
                if gained:
                    self.note("minions with a transferred mod")
                    for m in gained:
                        self.note("transferred mod %d" % m)
                M["mods"] = want
            ux = self.take("UMX")
            self.eq("UMX us (boss)", ux["us"], fmt(U["us"].t()))
            if res and res != 1:
                self.eq("UMX rs", ux["rs"], fmt(self.rs.t()))
                self.eq("UMX gs", ux["gs"], fmt(self.gs.t()))
        return made

    def special_spawn(self, box, cls, allow=1, warp=1):
        pos = self.spawn_pos_pick(self.room, box, cls, warp)
        if pos is None:
            self.guard("G2 SpawnPosPick failed")
            smp = self.take("SMPX")
            self.eq("SpecialMonPlace failed", smp["boss"], 0)
            return 0
        boss = self.spawn_try(self.room, box, cls, 1, 0, pos[0], pos[1], -1, 0x40)
        if not boss:
            self.guard("G2 boss = none")
            smp = self.take("SMPX")
            self.eq("SpecialMonPlace boss", smp["boss"], 0)
            return 0
        U = self.units[boss]
        self.place_exit(boss)
        mods = list(U["mods"])
        champ = self.roll(U, mods, cls, allow)
        a = self.take("SMA0")
        self.eq("SpecialModsApply boss, us", (a["boss"], a["us"]), (boss, fmt(U["us"].t())))
        self.seeds(a, "SMA0")
        if not champ:
            mcls = self.chk.sp.minion_class(cls)
            n = 3 + U["us"].rangeb(4)
            um = self.take("UMN")
            self.eq("unique minion count", um["n"], n)
            self.eq("UMN us", um["us"], fmt(U["us"].t()))
            self.unique_minions(U, box, mcls, n, mods)
            self.groups.append(("unique", cls, 1 + n))
            self.chk.uniques.append((self.path, self.lid, cls, n, self.diff, self.exp, "pass" if allow else "MonPlace 2"))
        a = self.take("SMA1")
        self.seeds(a, "SMA1")
        self.eq("SMA1 us", a["us"], fmt(U["us"].t()))
        self.handlers(U, mods, "champion" if champ else "unique")
        a = self.apply_exit(U, mods, "champion" if champ else "unique")
        self.seeds(a, "SMAX: the mod handlers keep the room and game seeds")
        U["mods"] = mods
        return boss

    def place_exit(self, boss):
        U = self.units[boss]
        smp = self.take("SMPX")
        self.mark_special(boss, False)
        self.eq("SpecialMonPlace boss", smp["boss"], boss)
        self.seeds(smp, "SMPX")
        self.eq("SMPX boss seed", smp["bu"]["us"], fmt(U["us"].t()))
        self.eq("SMPX boss flags 0x08|0x01", smp["bu"]["mf"] & 0x09, 0x09)

    def member_mark(self, u, mod):
        """sub_005A48C0_ChampionMemberMark: special, flags 0x05, the mod appended, SpecialModsApply (no minions: a
        champion), the handlers predicted."""
        M = self.units[u]
        a0 = self.take("SMA0")
        self.mark_special(u, False)
        self.eq("ChampionMemberMark SpecialModsApply unit, us", (a0["boss"], a0["us"]), (u, fmt(M["us"].t())))
        self.seeds(a0, "SMA0 (champion member)")
        mods = list(M["mods"])
        monspecial.mod_append(mods, mod)
        a1 = self.take("SMA1")
        self.seeds(a1, "SMA1 (champion member)")
        self.eq("SMA1 us (champion member)", a1["us"], fmt(M["us"].t()))
        self.handlers(M, mods, "champion member")
        ax = self.apply_exit(M, mods, "champion member")
        self.seeds(ax, "SMAX (champion member): mod handlers keep the room and game seeds")
        M["mods"] = mods

    def champion_pack(self, boss, box, cls):
        U = self.units[boss]
        c = self.take("CP0")
        self.eq("ChampionPack boss, us", (c["boss"], c["us"]), (boss, fmt(U["us"].t())))
        if not (c["mf"] & 4):
            self.guard("G5 not a champion: return")
            return
        n = U["us"].step() % 3 + 1
        cn = self.take("CPN")
        self.eq("champion pack count", cn["n"], n)
        made = 0
        for _ in range(n):
            u = self.near_unit(boss, box, cls, 1, 4, 0)
            if u:
                made += 1
                self.member_mark(u, monspecial.M_CHAMPION)
            cm = self.take("CPM")
            self.seeds(cm, "CPM")
            self.eq("special count after a pack member", cm["nspec"], self.nspec)
        self.groups.append(("champion", cls, 1 + made))
        self.chk.champions.append((self.path, self.lid, cls, n, made, self.diff, self.exp))


RETRY_NONE = {229, 284, 285, 286, 287, 288, 392, 393}   # sub_0054E3A0: the byte table 0x0054E3E0 gives 0 (no retry)


class NotModelled(Exception):
    pass


class PresetMonPass(Pass):
    """Plan 0048 Phase 1, oracle 16: one preset monster of the presets window with a MonStats class id (OPU0 type 1
    .. OPUX), sub_0054E600_PresetMonSpawn's class case 0x0054E490, read in the disassembly: class 434 starts one cell
    to the left and takes mode 12 when QUESTS_IsActive(game, 0x20) is 0 (quest state: the mode is taken from the MT0
    request and counted); a class with MonStats2 flag 13 (sub_004638A0_MonStats2FlagTest(class, 13)) is not placed;
    flags = 8 when MonStats +0x0E & 4 (neverCount); SpawnAtPos(x, y, class, mode, radius -1, flags), and when that
    places nothing and sub_0054E3A0 allows it (every class but 229, 284-288, 392, 393), the same with radius 4. After a
    placement, a class with MonStats2 flag 18 that is 432 or whose sub_00463900_MonClassCheck is 433 creates an object
    under it (SUnitCreate type 2, class 571 for 432): that object's creation is tools/objects.py's and is not chained
    here (NotModelled, the window keeps the oracle). The room and game seeds start from OPU0 (which tools/objects.py
    predicts) and are compared at OPUX. The position predicates run on the activation model (no pass snapshot in the
    presets window); a predicate the model cannot answer is taken from the log and counted."""

    def run(self):
        d = self.take("OPU0")
        self.room, self.lid = d["room"], d["lid"]
        self.rs, self.gs = S(seed_t(d["rs"])), S(seed_t(d["gs"]))
        self.diff, self.exp = self.chk.game_de.get(self.path, (None, None))
        if self.diff is None:
            raise NotModelled("difficulty and game type not logged in this log")
        mt = next((x[1] for x in self.ev if x[0] == "MT0"), None)
        self.game = mt["game"] if mt else None
        # the room's rect from its activation dump (CB, this process); chk.room_rects spans logs, and room pointers
        # are reused across game processes
        self.rect = self.chk.world.rects.get(self.room)
        if self.rect is None:
            raise NotModelled("room rect not known")
        self.rect = list(self.rect)
        self.sci, self.groups, self.region, self.nspec = [], [], None, 0
        t = self.t
        cls, x, y, mode = d["id"], d["x"], d["y"], d["mode"]
        if cls >= len(t.ms):
            return self.fixed_row(d, cls - len(t.ms) - self.chk.n_super, x, y, mode, mt)
        if not t.valid(cls):
            raise NotModelled("class %d not valid" % cls)
        if cls == 434:
            x -= 1
            if mt is not None and mt["a10"] != mode:
                self.chk.oracle("preset class 434 mode (QUESTS_IsActive(game, 0x20): quest state)")
                mode = mt["a10"]
        m2 = t.m2(cls)
        flag = lambda k: bool(m2 is not None and m2[4 + (k >> 3)] & (1 << (k & 7)))  # noqa: E731
        if flag(13):
            u = 0
            self.guard_preset("MonStats2 flag 13: not placed")
        else:
            fl = 8 if t.ms[cls][0x0E] & F_NEVERCOUNT else 0
            u = self.spawn_try(self.room, None, cls, mode, 0, x, y, -1, fl)
            if not u and cls not in RETRY_NONE:
                u = self.spawn_try(self.room, None, cls, mode, 0, x, y, 4, fl)
                self.guard_preset("retry with radius 4")
            if u and flag(18) and cls in (432, 433):
                # 0x0054E562..0x0054E5EF (oracle 22, the Orient89Unit catapults): class 432 creates object 571, 433
                # object 572 (sub_00463900 returns the class itself), SUnitCreate(2, class, UnitGetSubX/Y(unit), game,
                # room, 1, 0, 0) at the monster's cell: one game-seed step here; its InitFn, PreOperate and mark are
                # tools/objects.py's, which models that creation inside the window
                U = self.units[u]
                ou = self.take("OU0")
                ocls = 571 if cls == 432 else 572
                self.eq("object under class %d" % cls, (ou["type"], ou["cls"], ou["x"], ou["y"], ou["room"]),
                        (2, ocls, U["x"], U["y"], U["room"]))
                self.eq("OU0 gs (object under the catapult)", ou["gs"], fmt(self.gs.t()))
                self.gs = S(step(self.gs.lo, self.gs.hi))
                self.guard_preset("the object under class %d (Orient89Unit catapult) created" % cls)
        px = self.take("OPUX")
        self.seeds(px, "OPUX")
        self.guard_preset("placed" if u else "nothing placed")
        if self.sci:
            raise Mismatch("%d special-count increments not modelled" % len(self.sci))
        return "preset class"

    # sub_0054E600 0x0054E973..0x0054EA9D: MonPlace rows 17..32, the fixed-class table 0x0054EB74 (index row - 17)
    FIXED = {17: (19, False), 18: (58, False), 22: (141, False), 23: (278, False), 29: (453, True),
             30: (None, True), 31: (522, True), 32: (438, True)}      # class, mode 12

    def fixed_row(self, d, row, x, y, mode, mt):
        t = self.t
        if row not in self.FIXED:
            raise NotModelled("MonPlace row %d" % row)
        cls, m12 = self.FIXED[row]
        if row == 30:
            cls = 529 if self.lid == 110 else 492            # 0x0054E9A7: neg/sbb on lid - 0x6E
        if m12:
            mode = 12
        cls = self.level_class_variant(cls)
        cls = self.fallen_variant(cls)
        fl = 8 if t.ms[cls][0x0E] & F_NEVERCOUNT else 0
        u = self.spawn_try(self.room, None, cls, mode, 0, x, y, -1, fl)
        if not u:
            u = self.spawn_try(self.room, None, cls, mode, 0, x, y, 4, fl)
            self.guard_preset("MonPlace fixed row: retry with radius 4")
        if u and cls == 438:
            # 0x0054EA5F: Range(unit seed, 50) for the AI timer event (sub_005417D0), after the creation
            self.units[u]["us"].rangeb(50)
            self.guard_preset("MonPlace fixed row: reanimatedhorde3 Range(unit seed, 50)")
        px = self.take("OPUX")
        self.seeds(px, "OPUX")
        self.guard_preset("MonPlace fixed row %d: %s" % (row, "placed" if u else "nothing placed"))
        if self.sci:
            raise Mismatch("%d special-count increments not modelled" % len(self.sci))
        return "preset fixed row"

    def level_class_variant(self, cls):
        """sub_0063EC70_LevelClassVariant(room, class): with Levels +0x33 entries in the level's `mon` list (+0x36,
        s16): the entry whose BaseId equals the class's BaseId; else from the BaseId record's NextInClass (+0x04), up to
        MonStats +0x4A steps (MONSTATS_GetClassChainPos), each accepted while its Level (+0xAA) <= Levels +0x16 + 1."""
        t = self.t
        lv = t.lv[self.lid]
        mon = t.pool.slots(self.lid, 0x36)        # Levels +0x36 `mon`, its count +0x33 filled at load
        n = len(mon)
        if n == 0:
            return cls
        base = t.m(cls, 0x02, "<h") if t.valid(cls) else cls
        if not (0 <= base < len(t.ms)):
            return cls
        for e in mon:
            eb = t.m(e, 0x02, "<h") if t.valid(e) else e
            if eb == base:
                return e
        nxt = t.m(base, 0x04, "<h")
        pos = self.chain_len(cls)                 # MonStats +0x4A, filled at load by sub_00651040_MonClassChain
        lim = struct.unpack_from("<h", lv, 0x16)[0] + 1
        cur = cls
        for _ in range(pos):
            if not (0 <= nxt < len(t.ms)):
                return cur
            if t.m(nxt, 0xAA, "<h") > lim:
                return cur
            cur = nxt
            nxt = t.m(nxt, 0x04, "<h")
        return cur

    def chain_len(self, cls):
        """sub_00651040_MonClassChain: the number of records on the BaseId -> NextInClass walk (<= 256 steps; the walk
        ends on a record that is its own next or a negative next)."""
        t = self.t
        if not t.valid(cls):
            return 0
        sv = t.m(cls, 0x02, "<h")
        k = 0
        while True:
            nx = t.m(sv, 0x04, "<h") if 0 <= sv < len(t.ms) else -1
            k += 1
            if sv == nx or k >= 0x100 or nx < 0:
                break
            sv = nx
        return k & 0xFF

    def fallen_variant(self, cls):
        """sub_0054E2A0_PresetFallenVariant(class, level id)."""
        t = self.t
        base = t.m(cls, 0x02, "<h") if t.valid(cls) else cls
        n = len(t.ms)
        if base == 0x13:
            if self.lid == 6:
                return 0x14 if n > 0x14 else -1
            if self.lid in (7, 12, 16):
                return 0x15 if n > 0x15 else -1
        elif base == 0x3A:
            if self.lid in (6, 7):
                return 0x3B if n > 0x3B else -1
            if self.lid in (12, 16):
                return 0x3C if n > 0x3C else -1
        return cls

    def guard_preset(self, k):
        k = "preset monsters (class case): " + k
        self.stats[k] = self.stats.get(k, 0) + 1

    def snap(self):
        return False        # no pass snapshot: the predicates go to the activation model (pred below)

    def overlay(self):
        """The activation model with the window's marks so far (the CM lines since the last pass entry, pre_cm) on
        copies of the rooms' cells: the marks of the earlier preset monsters and objects of the window. The model
        itself is left as it is (the pass's R3 comparison applies the window marks itself)."""
        W = self.chk.world
        key = (id(W.model), len(W.pre_cm))
        if getattr(self.chk, "_ov_key", None) == key:
            return self.chk._ov
        maps = {r: collision.Map(m.x0, m.y0, m.w, m.h, list(m.c) if m.c is not None else None)
                for r, m in W.model.items()}
        for cm, _ln in W.pre_cm:
            try:
                W.apply_cm(cm, maps, W.model_near)
            except collision.NotLogged:
                pass
        self.chk._ov_key, self.chk._ov = key, maps
        return maps

    def pred(self, name, logged, fn, need_snap=True):
        W = self.chk.world
        # the cell of the predicate (its MK0 / MC0 / MR0 / SPW0 line): when an activated room of this process (W.rects)
        # holds the cell and the model has no cells for it, the model cannot answer
        a = next((dd for tg, dd, _ in reversed(self.ev[:self.i]) if tg in ("MK0", "MC0", "MR0", "SPW0", "SPR0")), None)
        if a is not None and "x" in a:
            ov = self.overlay()
            for r, (x0, y0, w, h) in W.rects.items():
                if x0 <= a["x"] < x0 + w and y0 <= a["y"] < y0 + h and (r not in ov or ov[r].c is None):
                    self.chk.oracle("presets window %s (the cell's room has no cells in the model)" % name)
                    return logged
        try:
            maps = self.overlay()
            W.maps_override, W.nears_override = maps, W.model_near
            try:
                v = fn()
            finally:
                W.maps_override = W.nears_override = None
        except collision.NotLogged as e:
            self.chk.oracle("presets window %s (model needs %s)" % (name, str(e).split(" of room")[0]))
            return logged
        except IndexError:
            # a cell the copied map does not hold (the model's room list differs from the game's at this cell)
            self.chk.oracle("presets window %s (the model holds no cell there)" % name)
            return logged
        self.eq(name + " (collision model, presets window)", logged, v)
        k = "predicted by the collision model (presets window): " + name
        self.stats[k] = self.stats.get(k, 0) + 1
        return v


class RequestPass(PresetMonPass):
    """Plan 0048 Phase 1, oracle 17: one MonSpawnTry request (MT0 .. MTX) made by a caller tools/objects.py models
    (InitFn 46's SpawnAtPos calls): the request's arguments and its entry room and game seeds are the caller model's,
    asserted there against MT0; this predicts the request from MT0 to MTX (the draws, the creation, the unit seed)."""

    def run(self):
        mt = self.ev[0][1]
        self.room, self.game = mt["room"], mt["game"]
        self.lid = self.chk.room_lid_cur.get(self.room)
        self.rs, self.gs = S(seed_t(mt["rs"])), S(seed_t(mt["gs"]))
        self.diff, self.exp = self.chk.game_de.get(self.path, (None, None))
        if self.diff is None or self.lid is None:
            raise NotModelled("difficulty, game type or level not known")
        self.rect = self.chk.world.rects.get(self.room)
        if self.rect is None:
            raise NotModelled("room rect not known")
        self.rect = list(self.rect)
        self.sci, self.groups, self.region, self.nspec = [], [], None, 0
        u = self.spawn_try(self.room, None, mt["cls"], mt["a10"], mt["a14"], mt["x"], mt["y"], mt["rad"], mt["fl"])
        if self.sci:
            raise Mismatch("%d special-count increments not modelled" % len(self.sci))
        return u


class PresetPass(Pass):
    """Plan 0018: a special spawned in the presets window (RW1 -> RW2): a superunique (SU0 .. SUX) or a MonPlace 2 or 3
    preset (PM0 .. PMX). The room and game seeds are taken at the entry line (the window before it stays a seed
    oracle); every draw after it is predicted like the pass's."""

    def run(self):
        tg = self.ev[0][0]
        d = self.take(tg)
        self.room, self.game = d["room"], d["game"]
        self.rs, self.gs = S(seed_t(d["rs"])), S(seed_t(d["gs"]))
        self.diff, self.exp, self.rect, self.lid = d["diff"], d["exp"], d["rect"], d["lid"]
        self.chk.room_rects[self.room] = self.rect
        self.sci = []
        self.region = d["reg"]
        self.chk.region_snapshot(self, d["reg"])
        self.nspec = d["reg"]["nspec"] if d["reg"] else 0
        self.groups = []
        if tg == "SU0":
            res = self.superunique(d)
        else:
            res = self.monplace(d)
        if self.sci:
            raise Mismatch("%d special-count increments not modelled" % len(self.sci))
        return res

    def monplace(self, d):
        cls, rec = self.pick_class(0, True)
        pc = self.take("PMC")
        self.eq("MonPlace class pick", (pc["cls"], pc["rec"] != 0), (cls, rec))
        if not rec:
            px = self.take("PMX")
            self.seeds(px, "PMX (no record)")
            return "monplace-norec"
        if d["case"] == 2:
            boss = self.special_spawn(None, cls, allow=0, warp=1)
            self.chk.presets.append((self.path, self.lid, 2, cls, boss != 0, self.diff, self.exp))
        else:
            u = self.spawn_try(self.room, None, cls, d["mode"], 0, d["x"], d["y"], -1, 0)
            if u:
                self.member_mark(u, monspecial.M_CHAMPION)
                self.champion_pack(u, None, cls)
            self.chk.presets.append((self.path, self.lid, 3, cls, bool(u), self.diff, self.exp))
        px = self.take("PMX")
        self.seeds(px, "PMX")
        return "monplace %d" % d["case"]

    def superunique(self, d):
        sp = self.chk.sp
        i = d["id"]
        rec = sp.su_rec(i)
        if self.diff > 2 or rec is None or rec["cls"] < 0 or (rec["stacks"] == 0 and d["placed"]):
            sx = self.take("SUX")
            self.eq("SuperUniqueSpawn returns no unit", sx["u"], None)
            self.chk.supers.append((self.path, self.lid, i, None, self.diff, self.exp, "not placed"))
            return "superunique-none"
        cls = rec["cls"]
        x, y = (0, 0) if rec["autopos"] else (d["x"], d["y"])
        u = 0
        pos = (x, y)
        if x == 0 and y == 0:
            pos = self.spawn_pos_pick(self.room, None, cls, 0)
            self.note("AutoPos superuniques placed by SpawnPosPick")
        if pos is not None:
            u = self.spawn_try(self.room, None, cls, 1, 0, pos[0], pos[1], -1, 0x40)
            if not u:
                u = self.spawn_try(self.room, None, cls, 1, 0, pos[0], pos[1], 5, 0x40)
        if not u:
            smp = self.take("SMPX")
            self.eq("SpecialMonPlace failed", smp["boss"], 0)
            sx = self.take("SUX")
            self.eq("SuperUniqueSpawn returns no unit", sx["u"], None)
            self.chk.supers.append((self.path, self.lid, i, None, self.diff, self.exp, "placement failed"))
            return "superunique-none"
        self.place_exit(u)
        U = self.units[u]
        U["su"] = i
        mods = list(U["mods"])
        k = monspecial.mod_count(mods)
        info = {"id": i, "cls": cls, "pos": (U["x"], U["y"]), "autopos": rec["autopos"], "preset": (d["x"], d["y"])}
        if k >= 5:
            self.note("superuniques with >= 5 mods at creation (no mods, minions or tail)")
        else:
            have, aura = set(), False
            for m in rec["mods"]:
                if m == 0:
                    break
                if m == monspecial.M_AURA:
                    aura = True
                elif m == monspecial.M_THIEF:
                    self.note("superunique fixed mod thief (24) skipped")
                    continue
                mods[k] = m
                k += 1
                have.add(m)
            picks = []
            for _ in range(self.diff):
                m, prec = sp.pick(U["us"], self.diff, self.exp, cls, False, have)
                picks.append(prec)
                if m == 0:
                    break
                mods[k] = m
                k += 1
                have.add(m)
            self.picks_check(picks)
            info["extra"] = [p["res"] for p in picks]
            mn, mx = rec["min"], rec["max"]
            if mn and mx:
                mn, mx = mn + self.diff, mx + self.diff
            s1 = self.take("SU1")
            self.eq("SU1 unit, mods, min, max, us (model)", (s1["u"], s1["mods"], s1["min"], s1["max"], s1["us"]),
                    (u, mods, mn, mx, fmt(U["us"].t())))
            a = self.take("SMA0")
            self.eq("SpecialModsApply superunique, us", (a["boss"], a["us"]), (u, fmt(U["us"].t())))
            self.seeds(a, "SMA0 (superunique)")
            mcls = sp.minion_class(cls)
            n = 0
            if sp.valid(mcls):
                n = mn + U["us"].rangeb(mx - mn + 1)
                um = self.take("UMN")
                self.eq("superunique minion count MinGrp+d .. MaxGrp+d", um["n"], n)
                self.eq("UMN us", um["us"], fmt(U["us"].t()))
                if n > 0:
                    self.unique_minions(U, None, mcls, n, mods)
            info["minions"] = (n, mn, mx)
            a = self.take("SMA1")
            self.eq("SMA1 us (superunique)", a["us"], fmt(U["us"].t()))
            self.seeds(a, "SMA1 (superunique)")
            self.handlers(U, mods, "superunique")
            a = self.apply_exit(U, mods, "superunique")
            self.seeds(a, "SMAX (superunique): the mod handlers keep the room and game seeds")
            if aura:
                self.aura(U)
                self.note("superunique aura handler run a second time")
            t = self.take("SUT")
            self.eq("superunique tail switch (record +0x08)", t["idx"], rec["idx"])
            self.eq("SUT seeds", (t["us"], t["rs"], t["gs"]), (fmt(U["us"].t()), fmt(self.rs.t()), fmt(self.gs.t())))
            if rec["idx"] == monspecial.SU_TAIL_RADAMENT:
                r = U["us"].rangeb(5) + 2
                info["radament"] = r
                self.note("Radament escorts Range(5) + 2")
                for c in [4] * r + list(monspecial.RADAMENT_ESCORTS):
                    self.near_unit(u, None, c, 1, 4, 0x40)
            elif rec["idx"] in monspecial.SU_TAIL_ESCORT_FIXED:
                c, rad, n, fl = monspecial.SU_TAIL_ESCORT_FIXED[rec["idx"]]
                self.note("superunique EscortSpawn tails (%d)" % rec["idx"])
                for _ in range(n):              # sub_005B24E0_EscortSpawn: n x SpawnNearUnitNoBox(c, 1, rad, fl)
                    self.near_unit(u, None, c, 1, rad, fl)
            elif rec["idx"] in monspecial.SU_TAIL_ESCORT:
                raise Mismatch("superunique %d: EscortSpawn of LevelClassVariant(minion) not modelled" % rec["idx"])
            elif rec["idx"] in monspecial.SU_TAIL_NO_DRAW:
                self.note("superunique tails with quest hooks (seed-asserted)")
            monspecial.mod_append(mods, monspecial.M_QUESTCOMPLETE)
        sx = self.take("SUX")
        self.eq("SuperUniqueSpawn unit", sx["u"]["u"], u)
        self.eq("SUX mods, flags 0x02, superunique id", (sx["u"]["mods"], sx["u"]["mf"] & 2, sx["u"]["su"]), (mods, 2, i))
        self.eq("SUX us (model)", sx["u"]["us"], fmt(U["us"].t()))
        self.eq("SUX rs, gs", (sx["rs"], sx["gs"]), (fmt(self.rs.t()), fmt(self.gs.t())))
        if U.get("ns") is not None:
            self.eq("SUX name seed", sx["u"]["ns"], U["ns"])
        U["mods"] = mods
        info["mods"] = [m for m in mods if m]
        self.chk.supers.append((self.path, self.lid, i, info, self.diff, self.exp, "placed"))
        return "superunique"


def drlg_div3(v):
    """Signed i32 division by 3, truncating toward zero (imul 0x55555556, add the sign bit)."""
    q = abs(v) // 3
    return q if v >= 0 else -q


def drlg_steps(start, target, limit=64):
    lo, hi = start
    for j in range(limit + 1):
        if (lo, hi) == target:
            return j
        lo, hi = step(lo, hi)
    return None


class Checker:
    def __init__(self, excel, root, verbose):
        self.t = Tables(excel)
        self.excel = excel
        self.root, self.verbose = root, verbose
        self.checks = self.fail = 0
        self.stats, self.oracles = {}, {}
        self.append_src, self.unit_seed_taken = {}, {}      # plan 0048 Phase 2: oracle 14 remainder per class
        self.populated_clean, self.populated_unclean = [], {}  # plan 0048 Phase 2: oracle-free room populations
        # F8: MonSpawnTry branches that are counted, printed even at 0
        self.stats["CollisionTest bypassed by R.flags & 0x80"] = 0
        self.stats["MonSpawnTry exit on x = 0 or y = 0"] = 0
        for k in GUARDS:
            self.stats["guard " + k] = 0
        self.type_rolls, self.champ_rolls, self.creations, self.group_sizes = [], [], [], []
        self.champions, self.uniques = [], []
        self.unit_steps = {}
        self.unit_steps_odd = []      # (log, MU line, level, class, steps) for creations with steps != 2
        self.rooms_e2e = []           # (log, RW0 line, room): predicted from the map seed, no draw in RW1..RW4
        self.populated_e2e = []       # (log, P0 line, level, room, creations) of those rooms
        self.room_e2e = self.room_predicted = False
        self.rw1_rs, self.rw0_line, self.rw0_room = None, 0, 0
        self.nspec_incr = 0
        self.closed_levels = set()
        self.room_rects, self.other_rs = {}, {}
        self.wnd_hits = {}
        self.results = {}
        self.rooms_pred = self.rooms_logseed = 0
        self.levels, self.seeds_used, self.diffs = set(), set(), set()
        self.regions_checked = {}
        self.world = collision.World(root, self.t)
        # plan 0048 Phase 1, oracle 14: the unit seed at MU from Init(step(game).low), MonRegionFindAdd on the tracked
        # regions (tools/mon_sweep.py findadd, plan 0038 S3a) and MonStatsInit's draws (tools/monstats.py init_seed)
        self.msm = monstats.Model(monstats.Tables(excel))
        self.n_super = len(read_bin(find_file(excel, "superuniques", ".bin"))[0])
        self.regions = {}             # (log, game, diff, exp) -> {level id: [[class, rarity, sets]]}, appends applied
        self.unit_seed_model = UNIT_SEED_MODEL
        self.game_L = GAME_L
        self.opu_confirmed = set()    # plan 0048 oracle 16: (log, OPUX line) of every preset monster the model reached
        self.opu_pending = None
        self.game_de = {}             # log -> (difficulty, expansion) of its games (an input: the game's settings)
        self.room_lid_cur, self.mt_room_cur, self.game_cur = {}, None, None
        self.room_state, self.active_pred_cur = {}, {}
        self.room_state_model = ROOM_STATE_MODEL
        self.obj_grid = {}            # plan 0027: tools/objects.py's grid-model counters over the logs
        self.obj_oracles = {}         # plan 0048: tools/objects.py's oracle counters over the logs
        self.obj_stats = {}           # and its other counters
        # plan 0018
        self.sp = monspecial.Data(excel)
        self.new_tags = False
        self.mods_drawn, self.ns_pred = {}, {}
        self.presets, self.supers = [], []
        self.client = []
        self.client_stats = {}
        self.aura_level_diff = []

    def fail_(self, msg):
        self.fail += 1
        print("MISMATCH " + msg)

    def ok(self, cond, msg):
        self.checks += 1
        if not cond:
            self.fail_(msg)

    def oracle(self, name):
        self.oracles[name] = self.oracles.get(name, 0) + 1

    def wnd(self, d):
        what = WND_PCS.get(d["pc"])
        key = "%s level %d at %s" % (d["what"], d["lid"], what or ("UNEXPECTED pc 0x%08x" % d["pc"]))
        self.wnd_hits[key] = self.wnd_hits.get(key, 0) + 1
        self.ok(what is not None, "MonWndr watchpoint hit outside the two known accesses: %s" % d)

    def tracked_regions(self, P):
        key = (P.path, P.game, P.diff, P.exp)
        regs = self.regions.get(key)
        if regs is None:
            low = monpool.first_draw_low(self.n_seed, 1).low
            regs = {lid: [[c, r, [bytes.fromhex(v) for v in sets]] for c, r, sets in reg["ents"]]
                    for lid, reg, _ in monpool.build_all(self.t.pool, low, P.diff, P.exp)}
            self.regions[key] = regs
        return regs

    def region_snapshot(self, P, reg):
        """Every logged region snapshot (P0, SU0, PM0) against the tracked region (the monpool model of the game plus
        every FindAdd append so far): the class list must match."""
        if not self.unit_seed_model or reg is None or self.n_seed is None:
            return
        tr = self.tracked_regions(P).setdefault(reg["lid"], [])
        want = [e[0] for e in tr]
        got = [e[0] for e in reg["ents"]]
        if len(got) > len(want) and got[:len(want)] == want:
            # appended by a creation the model did not run (a preset monster of the presets window, before oracle 16
            # is chained, or a unit of another path): the class is taken from the snapshot, its variant sets are not
            # known (None), so a later creation of that class takes its unit seed from the log
            for c in got[len(want):]:
                tr.append([c, 0, None])
                self.append_src.setdefault((P.path, reg["lid"], c), "no creation logged (first seen in a region snapshot)")
                self.oracle("region append by a creation outside the model (class from the snapshot, sets unknown)")
            want = got
        self.ok(want == got, "%s: region of level %d at the pass entry %s, tracked model %s" % (P.path, reg["lid"], got, want))
        k = "region snapshots equal to the tracked region (FindAdd appends applied)"
        self.stats[k] = self.stats.get(k, 0) + 1

    def on_aroom(self, d):
        """An activation (in log order): the active room's seed is the roomk model's prediction, when it made one."""
        p = self.active_pred_cur.get(d["aroom"]) if self.active_pred_cur else None
        if p is not None:
            self.room_state[d["aroom"]] = p
        else:
            self.room_state.pop(d["aroom"], None)

    def note_unmodelled(self, path, mu, ln):
        """A creation the model did not run (an MU line outside the modelled windows: a monster-spawning InitFn, an
        operate spawn, a preset window kept as an oracle). Its FindAdd effect on the tracked region is applied with
        the sets unknown, so that a later creation of the class is not mispredicted as an append."""
        u = mu.get("unit")
        if not u or u.get("type", 1) != 1 or not self.unit_seed_model or self.n_seed is None:
            return
        de = self.game_de.get(path)
        lid = self.room_lid_cur.get(self.mt_room_cur)
        if de is None or lid is None or self.game_cur is None:
            self.oracle("creation outside the model with no level known (region not updated)")
            return

        class _P:
            pass
        P = _P()
        P.path, P.game, P.diff, P.exp = path, self.game_cur, de[0], de[1]
        reg = self.tracked_regions(P).setdefault(lid, [])
        cls = u["cls"]
        if cls in mon_sweep.FINDADD_NONE or any(e[0] == cls for e in reg) or len(reg) > 12:
            return
        m2 = self.t.pool.ms2rec(cls)
        if m2 is None or m2[0xEC] <= 2:
            return
        reg.append([cls, 0, None])
        # plan 0048 Phase 2: the creation that appended the class, for the remainder of oracle 14
        self.append_src[(path, lid, cls)] = "%s MU line %d (class %d, outside a modelled window)" % (
            os.path.basename(path), ln, cls)
        self.oracle("region append by a creation outside the model (an MU line not in a modelled window; sets unknown)")

    def unit_seed(self, P, cls, us0, logged):
        """Oracle 14 retired: predict the unit seed SUnitCreate leaves (MU) and compare it with the log."""
        if not self.unit_seed_model or self.n_seed is None:
            self.oracle("unit seed after SUnitCreate (taken from MU)")
            return
        reg = self.tracked_regions(P).setdefault(P.lid, [])
        s = monpool.Seed(*us0)
        kind, e = mon_sweep.findadd(self.t.pool, reg, cls, s)
        k = "unit seeds: FindAdd %s" % kind
        self.stats[k] = self.stats.get(k, 0) + 1
        if e is not None and e[2] is None:
            self.oracle("unit seed after SUnitCreate (region entry appended outside the model: sets unknown)")
            src = self.append_src.get((P.path, P.lid, cls), "appender not recorded")
            self.unit_seed_taken[(cls, P.lid, src)] = self.unit_seed_taken.get((cls, P.lid, src), 0) + 1
            return
        nvar = len(e[2]) if e is not None else 0
        ms = monstats.Seed((s.low, s.high))
        try:
            self.msm.init_seed(ms, cls, P.lid, P.diff, 1 if P.exp else 0, self.game_L, nvar)
        except monstats.MonEquipOracle:
            self.oracle("MonEquipInit item creation (oracle 13; unit seed taken from MU)")
            return
        if fmt(ms.t()) != logged:
            raise Mismatch("unit seed after SUnitCreate class %d level %d (FindAdd %s, nvar %d): log %s, model %s"
                           % (cls, P.lid, kind, nvar, logged, fmt(ms.t())))
        self.checks += 1
        k = "unit seeds after SUnitCreate predicted (oracle 14 retired)"
        self.stats[k] = self.stats.get(k, 0) + 1
        if self.msm.equip_items:
            k = "MonEquipInit items (oracle 13, [I] model)"
            self.stats[k] = self.stats.get(k, 0) + self.msm.equip_items
        return self.msm.equip_items

    def region_check(self, path, reg, diff, exp):
        if reg is None:
            return
        want = self.pool_regions.get((diff, exp))
        if want is None:
            return
        w = want.get(reg["lid"])
        self.ok(w is not None, "%s: region of level %s not modelled" % (path, reg["lid"]))
        if w is None:
            return
        got = ([e[0] for e in reg["ents"]], reg["npool"], reg["rsum"], reg["umin"], reg["umax"], reg["wndr"])
        exp_ = ([e[0] for e in w["ents"]], w["n"], w["rsum"], w["umin"], w["umax"], w["wndr"])
        if reg["lid"] not in self.regions_checked.setdefault((path, diff), set()):
            self.regions_checked[(path, diff)].add(reg["lid"])
            self.ok(got[1:] == exp_[1:] and got[0][:w["n"]] == exp_[0][:w["n"]] and min(reg["den"], 10**9) == w["den"],
                    "%s: region of level %d %s, monpool model %s (den %d vs %d)" % (path, reg["lid"], got, exp_, reg["den"], w["den"]))

    def run(self, path):
        lines = []
        has_ogc = False
        n_seed = None
        for ln, line in enumerate(open(path, errors="replace"), 1):
            if line.startswith("# d2run seed="):
                n_seed = int(line.split("seed=")[1].split()[0])
            tag, _, rest = line.partition(" ")
            if tag == "LOGERR":
                self.fail_("%s:%d logger error %s" % (path, ln, rest.strip()))
                continue
            if tag == "OGC":
                has_ogc = True
            if tag in SPAWN_TAGS or tag in SIDE_TAGS or tag in ("LC0", "RL", "AROOM", "RRESEED"):
                try:
                    lines.append((tag, json.loads(rest), ln))
                except ValueError:
                    pass
        self.seeds_used.add(n_seed)
        self.n_seed = n_seed
        for tg, dd, _ln in lines:
            if tg in ("P0", "SU0", "PM0") and "diff" in dd:
                self.game_de[path] = (dd["diff"], dd["exp"])
                break
        # plan 0023: logs written with tools/gdb/objects.gdb carry the objects window; tools/objects.py predicts it.
        # mon-spawn.py's RW lines carry "os" since plan 0023 whatever else is loaded, so the objects logger is known by
        # its OGC line (plan 0027 Phase 3: tools/gdb/mon-stats.gdb logs have "os" and no objects window)
        self.obj_pred = set()
        self.obj_rw4_oracles = {}
        if has_ogc and any(tg == "RW1" and "os" in d for tg, d, _ln in lines):
            oc = objects.Checker(self.excel, self.root, False)
            oc.run(path)
            self.obj_pred = oc.pred_rw4
            self.obj_rw4_oracles = oc.rw4_oracles
            # plan 0027: the objects window on the grid model (object marks and COLL_WHTest predicted by tools/objects.py)
            for k, v in oc.stats.items():
                if k.startswith(("position tests predicted", "object marks", "gold-pile room tests", "marks applied from the log")):
                    self.obj_grid[k] = self.obj_grid.get(k, 0) + v
            for k, v in oc.stats.items():
                self.obj_stats[k] = self.obj_stats.get(k, 0) + v
            for k, v in oc.oracles.items():
                self.obj_oracles[k] = self.obj_oracles.get(k, 0) + v       # plan 0048: every objects.py oracle
                if k.startswith("position test result"):
                    self.obj_grid["ORACLE " + k] = self.obj_grid.get("ORACLE " + k, 0) + v
            self.ok(oc.fail == 0, "%s: tools/objects.py has %d mismatches on this log" % (path, oc.fail))
        self.new_tags = any(tg in ("HD0", "MPK", "SU0", "PM0") for tg, _d, _ln in lines)
        self.client = []
        self.world.reset_process()
        # DRLG models on the same log: +0x04 (gen) and k / the active seed (roomk)
        data = drlg.Data(self.root, drlg.DEFAULT_EXE)
        gm = drlg.GenModel(data, False, False, drlg.PresetUnitData(self.root, drlg.DEFAULT_EXE))
        gm.rl_pred = []
        gm.run(path)
        self.world.wp_pred = gm.wp_by_level         # plan 0022 Phase 2: the warp points each build leaves
        rm = drlg.Model(drlg.Data(self.root, drlg.DEFAULT_EXE), False)
        rm.aroom_pred = []
        drlg.run_log(rm, path, gm.prep_pred or None)     # plan 0027: type-1 first-LvlSub grids from GenModel when it predicted them
        print("%s: drlg gen %d checks %d mismatches; roomk %d checks %d mismatches" % (path, gm.checks, gm.fail, rm.checks, rm.fail))
        self.ok(gm.fail == 0 and rm.fail == 0, "%s: the DRLG models have mismatches on this log" % path)
        # regions from the -seed value (tools/monpool.py)
        self.pool_regions = {}
        # first walk, in line order: the DRLG predictions (+0x04 from gen, the active seed from roomk)
        rl_i = ar_i = 0
        r04_pred = {}           # DRLG room -> predicted +0x04 (or None)
        active_pred = {}        # active room -> predicted active seed (lo, hi) or None
        rw0_pred = {}           # line of an RW0 -> the prediction for its room at that point
        base_want = step(n_seed & MASK, INIT_HIGH)[0] if n_seed else None
        for tag, d, ln in lines:
            if tag == "LC0":
                self.ok(d["base"] == base_want, "%s:%d act base %08x, model step(Init(%s)).low %08x" % (path, ln, d["base"], n_seed, base_want or 0))
            elif tag == "RL":
                room, lo, _lid = gm.rl_pred[rl_i]
                rl_i += 1
                self.ok(room == d["room"], "%s:%d RL order" % (path, ln))
                r04_pred[room] = lo
            elif tag == "AROOM":
                r, a, r04, seedlo, k = rm.aroom_pred[ar_i]
                ar_i += 1
                self.ok((r, a) == (d["room"], d["aroom"]), "%s:%d AROOM order" % (path, ln))
                ok = r04_pred.get(r) is not None and r04_pred[r] == r04 and d["aseed"] == fmt((seedlo, INIT_HIGH))
                active_pred[a] = (seedlo, INIT_HIGH) if ok else None
            elif tag == "RW0":
                rw0_pred[ln] = active_pred.get(d["room"])
        # second walk: the room driver and the passes (collision events go to the collision model in line order)
        W = self.world
        i = 0
        self.room_lid_cur, self.mt_room_cur, self.game_cur = {}, None, None
        self.init_fn_cur = None
        self.room_state, self.active_pred_cur = (STATE_FROZEN or dict)(), active_pred
        while i < len(lines):
            tag, d, ln = lines[i]
            if "room" in d and "lid" in d and isinstance(d.get("room"), int):
                self.room_lid_cur[d["room"]] = d["lid"]
            if tag in ("MT0", "P0", "SU0", "PM0") and "game" in d:
                self.game_cur = d["game"]
            if tag == "MT0":
                self.mt_room_cur = d["room"]
            if tag in collision.COLL_TAGS or tag == "RRESEED":
                W.event(tag, d, ln, path)
            if tag == "AROOM":
                self.on_aroom(d)
            if tag == "RW0":
                pred = rw0_pred.get(ln)
                if pred is not None:
                    self.ok(d["rs"] == fmt(pred), "%s:%d room %08x seed before the wanderer tick %s, predicted from the map seed %s"
                            % (path, ln, d["room"], d["rs"], fmt(pred)))
                    self.rooms_pred += 1
                    self.room_predicted = True
                else:
                    self.rooms_logseed += 1
                    self.room_predicted = False
                j = i + 1
                # RW1: one tick draw unless a wanderer roll ran
                nxt = [x for x in lines[j:j + 6] if x[0] in ("RW1", "WRL")]
                self.rw0_line, self.rw0_room = ln, d["room"]
                self.rw1_rs = nxt[0][1]["rs"] if nxt and nxt[0][0] == "RW1" else None
                self.room_e2e = False
                self.window_clean = False
                if nxt and nxt[0][0] == "RW1":
                    lo, hi = step(*seed_t(d["rs"]))
                    self.ok(nxt[0][1]["rs"] == fmt((lo, hi)), "%s:%d wanderer tick: one room draw (%s -> %s)"
                            % (path, ln, d["rs"], nxt[0][1]["rs"]))
                    if lo & 0x7FFF == 0:
                        self.stats["tick low & 0x7FFF = 0 without a wanderer roll"] = self.stats.get("tick low & 0x7FFF = 0 without a wanderer roll", 0) + 1
                elif nxt:
                    self.stats["wanderer roll (oracle)"] = self.stats.get("wanderer roll (oracle)", 0) + 1
            elif tag == "RW4" and (path, ln) in self.obj_pred:
                # plan 0023: tools/objects.py predicted this window (presets, restore, objects) from RW1
                self.stats["presets / restore / objects window predicted by tools/objects.py"] = self.stats.get(
                    "presets / restore / objects window predicted by tools/objects.py", 0) + 1
                # plan 0048: the window counts as predicted with no oracle inside when every oracle exit
                # tools/objects.py took in it is one this checker predicted (a preset monster's OPUX)
                left = [o for o in self.obj_rw4_oracles.get((path, ln), [])
                        if not (o[0] in ("OPUX", "MTX") and (path, o[1]) in self.opu_confirmed)]
                k = ("windows RW1 -> RW4 with no oracle left inside" if not left else
                     "windows RW1 -> RW4 with an oracle left inside: " + ", ".join(sorted({
                         "InitFn %d" % o[2] if o[0] == "OIX" else o[0] for o in left})))
                self.stats[k] = self.stats.get(k, 0) + 1
                self.window_clean = not left
                self.room_e2e = bool(self.room_predicted and self.rw1_rs is not None)
                if self.room_e2e:
                    self.rooms_e2e.append((path, self.rw0_line, self.rw0_room))
                if i + 1 < len(lines) and lines[i + 1][0] == "P0":
                    p0 = lines[i + 1][1]
                    self.ok((p0["rs"], p0["gs"]) == (d["rs"], d["gs"]), "%s:%d RW4 seeds differ from the pass entry" % (path, ln))
            elif tag == "RW4":
                self.oracle("presets / inactive restore / objects (RW1..RW4, room and game seed)")
                # F7: the pass-entry room seed is predicted end to end iff the room was predicted and the
                # presets / restore / objects window drew nothing on it
                self.room_e2e = bool(self.room_predicted and self.rw1_rs is not None and self.rw1_rs == d["rs"])
                self.window_clean = self.room_e2e
                if self.room_e2e:
                    self.rooms_e2e.append((path, self.rw0_line, self.rw0_room))
                if i + 1 < len(lines) and lines[i + 1][0] == "P0":
                    p0 = lines[i + 1][1]
                    self.ok((p0["rs"], p0["gs"]) == (d["rs"], d["gs"]), "%s:%d RW4 seeds differ from the pass entry" % (path, ln))
            elif tag == "P0":
                if d["reg"] is not None and (d["diff"], d["exp"]) not in self.pool_regions:
                    low = monpool.first_draw_low(n_seed, 1).low
                    regs = {lid: reg for lid, reg, _ in monpool.build_all(self.t.pool, low, d["diff"], d["exp"])}
                    self.pool_regions[(d["diff"], d["exp"])] = regs
                self.room_rects[d["room"]] = d["rect"]
                self.diffs.add(d["diff"])
                end = i + 1
                while end < len(lines) and lines[end][0] != "PX":
                    end += 1
                win = lines[i:end + 1]
                P = Pass(self, win, self.t, path)
                f_pass = self.fail
                e2e, self.room_e2e = self.room_e2e, False
                wclean, self.window_clean = getattr(self, "window_clean", False), False
                o_pass = sum(self.oracles.values())
                n_cr = len(self.creations)
                try:
                    res = P.run()
                    if self.fail == f_pass:
                        self.room_state[P.room] = P.rs.t()
                        for r_, s_ in P.other_rs.items():
                            self.room_state[r_] = s_.t()
                    else:
                        self.room_state.pop(P.room, None)
                    self.results[res] = self.results.get(res, 0) + 1
                    if res in ("populated", "empty"):
                        self.levels.add((d["lid"], d["diff"]))
                    if e2e and res == "populated":
                        self.populated_e2e.append((path, ln, d["lid"], d["room"], len(self.creations) - n_cr))
                    # plan 0048 Phase 2: a room population end to end from the game seed with no seed oracle in its
                    # window (objects window clean) nor in the pass (no oracle counter moved, no mismatch)
                    if (e2e and wclean and res == "populated" and self.fail == f_pass
                            and sum(self.oracles.values()) == o_pass):
                        self.populated_clean.append((path, ln, d["lid"], d["room"], d["diff"], d["exp"],
                                                     len(self.creations) - n_cr))
                    elif e2e and res == "populated":
                        why = ("window" if not wclean else "pass oracle" if sum(self.oracles.values()) != o_pass
                               else "mismatch")
                        self.populated_unclean[why] = self.populated_unclean.get(why, 0) + 1
                    if P.i < len(win):
                        rest = [w[0] for w in win[P.i:] if w[0] not in SIDE_TAGS]
                        self.ok(not rest, "%s:%d %d line(s) of the pass not consumed by the model: %s" % (path, ln, len(rest), rest[:8]))
                    for tg, dd, ll in win[P.i:]:
                        if tg in SIDE_TAGS:
                            P.side(tg, dd, ll)
                    self.ok(not P.sci, "%s:%d %d special-count increments not modelled" % (path, ln, len(P.sci)))
                    if self.verbose and res == "populated":
                        print("  %s:%d level %d room %08x: %s" % (path, ln, d["lid"], d["room"], P.groups))
                except (Mismatch, collision.CollMismatch) as e:
                    self.fail_("%s:%d level %s room %08x: %s" % (path, ln, d["lid"], d["room"], e))
                    self.results["mismatch"] = self.results.get("mismatch", 0) + 1
                    for tg, dd, ll in win[P.i:]:
                        if tg in collision.COLL_TAGS or tg == "RRESEED":
                            W.event(tg, dd, ll, path)
                        elif tg in CLIENT_TAGS:
                            self.client.append((tg, dd, ll))
                W.pass_end()
                i = end
            elif tag == "OPU0" and d["type"] == 1:
                i = self.preset_monster(lines, i, path)
                continue
            elif tag == "OI0":
                self.init_fn_cur = d["fn"]
            elif tag == "OIX":
                self.init_fn_cur = None
            elif tag == "MT0" and self.init_fn_cur == 46:
                i = self.request(lines, i, path, "InitFn 46")
                continue
            elif tag == "OPU0" and d["type"] == 5:
                i = self.preset_tile(lines, i, path)
                continue
            elif tag == "OPUX" and self.opu_pending is not None and self.opu_pending[0] == ln:
                _l, f0, ok0 = self.opu_pending
                self.opu_pending = None
                if ok0 and self.fail == f0:
                    self.opu_confirmed.add((path, ln))
                    self.stats["preset monsters (special case): OPUX seeds equal to the special's exit"] = \
                        self.stats.get("preset monsters (special case): OPUX seeds equal to the special's exit", 0) + 1
            elif tag in ("SU0", "PM0"):
                # plan 0018: a special spawned in the presets window
                close = "SUX" if tag == "SU0" else "PMX"
                end = i + 1
                while end < len(lines) and lines[end][0] != close:
                    end += 1
                win = lines[i:end + 1]
                P = PresetPass(self, win, self.t, path)
                try:
                    res = P.run()
                    self.results[res] = self.results.get(res, 0) + 1
                    rest = [w[0] for w in win[P.i:] if w[0] not in SIDE_TAGS]
                    self.ok(not rest, "%s:%d %d line(s) of the preset special not consumed by the model: %s" % (path, ln, len(rest), rest[:8]))
                    for tg, dd, ll in win[P.i:]:
                        if tg in SIDE_TAGS:
                            P.side(tg, dd, ll)
                except (Mismatch, collision.CollMismatch) as e:
                    self.fail_("%s:%d preset special (%s) level %s room %08x: %s" % (path, ln, tag, d["lid"], d["room"], e))
                    self.results["mismatch"] = self.results.get("mismatch", 0) + 1
                    for tg, dd, ll in win[P.i:]:
                        if tg in collision.COLL_TAGS or tg == "RRESEED":
                            W.event(tg, dd, ll, path)
                        elif tg in CLIENT_TAGS:
                            self.client.append((tg, dd, ll))
                W.pass_end()
                i = end
            elif tag in CLIENT_TAGS:
                self.client.append((tag, d, ln))
            elif tag in ("MT0", "MTX", "MC0", "MC"):
                self.window_cell_test(tag, d, ln, path)
            elif tag == "MU":
                self.note_unmodelled(path, d, ln)
            elif tag == "WND":
                self.wnd(d)
            elif tag == "PDEAD":
                self.fail_("%s:%d the dead type-1 branch ran" % (path, ln))
            i += 1
        self.client_check(path)

    def preset_monster(self, lines, i, path):
        """Plan 0048 oracle 16: a preset unit of type 1 in the presets window (OPU0 .. OPUX). A superunique (SU0 .. SUX)
        or MonPlace 2 / 3 (PM0 .. PMX) inside is modelled by PresetPass; its entry and exit seeds must equal OPU0's
        and OPUX's. A MonStats class runs PresetMonPass. A MonPlace row with no request inside must leave the seeds
        alone. Returns the index after the window (or the next line, for the special case, whose lines the loop
        walks). Each OPUX the model reached is added to opu_confirmed; tools/objects.py's windows whose every preset
        monster OPUX is confirmed are counted as predicted with no oracle."""
        tag, d, ln = lines[i]
        end = i + 1
        while end < len(lines) and lines[end][0] != "OPUX":
            end += 1
        if end >= len(lines):
            self.oracle("preset monster window not closed in the log")
            return i + 1
        inner = lines[i + 1:end]
        dx = lines[end][1]
        sp = [x for x in inner if x[0] in ("SU0", "PM0")]
        if sp:
            s0 = sp[0][1]
            closer = "SUX" if sp[0][0] == "SU0" else "PMX"
            sx = [x for x in inner if x[0] == closer]
            ok = (s0["rs"], s0["gs"]) == (d["rs"], d["gs"]) and len(sp) == 1 and len(sx) == 1 and \
                (sx[0][1]["rs"], sx[0][1]["gs"]) == (dx["rs"], dx["gs"])
            self.ok(ok, "%s:%d preset special: entry or exit seeds differ from OPU0 / OPUX" % (path, ln))
            self.opu_pending = (lines[end][2], self.fail, ok)
            return i + 1
        if d["id"] >= len(self.t.ms) and not any(x[0] == "MT0" for x in inner):
            self.ok((dx["rs"], dx["gs"]) == (d["rs"], d["gs"]), "%s:%d preset id %d placed nothing but moved a seed"
                    % (path, ln, d["id"]))
            self.opu_confirmed.add((path, lines[end][2]))
            self.stats["preset monsters (MonPlace row or superunique, nothing placed): seeds unchanged"] = \
                self.stats.get("preset monsters (MonPlace row or superunique, nothing placed): seeds unchanged", 0) + 1
            self.skip_side(lines[i + 1:end + 1], path)
            return end + 1
        win = lines[i:end + 1]
        P = PresetMonPass(self, win, self.t, path)
        f0 = self.fail
        try:
            P.run()
            rest = [w[0] for w in win[P.i:] if w[0] not in SIDE_TAGS]
            self.ok(not rest, "%s:%d %d line(s) of the preset monster not consumed: %s" % (path, ln, len(rest), rest[:8]))
            for tg, dd, ll in win[P.i:]:
                if tg in SIDE_TAGS:
                    P.side(tg, dd, ll)
            if self.fail == f0:
                self.opu_confirmed.add((path, lines[end][2]))
                self.stats["preset monsters (class case) predicted OPU0 -> OPUX"] = \
                    self.stats.get("preset monsters (class case) predicted OPU0 -> OPUX", 0) + 1
        except NotModelled as e:
            self.oracle("preset monster not modelled: %s" % e)
            self.skip_side(win[P.i:], path)
        except (Mismatch, collision.CollMismatch) as e:
            self.fail_("%s:%d preset monster class %d level %d room %08x: %s" % (path, ln, d["id"], d["lid"], d["room"], e))
            self.results["mismatch"] = self.results.get("mismatch", 0) + 1
            self.skip_side(win[P.i:], path)
        return end + 1

    def request(self, lines, i, path, what):
        """A MonSpawnTry request (MT0 .. MTX) of a caller tools/objects.py models: RequestPass predicts it; the MTX line
        is added to opu_confirmed (the objects window's accounting) when it does."""
        end = i + 1
        while end < len(lines) and lines[end][0] != "MTX":
            end += 1
        win = lines[i:end + 1]
        P = RequestPass(self, win, self.t, path)
        f0 = self.fail
        k = "requests of %s predicted MT0 -> MTX" % what
        try:
            P.run()
            if self.fail == f0:
                self.opu_confirmed.add((path, lines[end][2]))
                self.stats[k] = self.stats.get(k, 0) + 1
        except NotModelled as e:
            self.oracle("request of %s not modelled: %s" % (what, e))
            self.skip_side(win[P.i:], path)
        except (Mismatch, collision.CollMismatch) as e:
            self.fail_("%s:%d request of %s: %s" % (path, lines[i][2], what, e))
            self.skip_side(win[P.i:], path)
        return end + 1

    def preset_tile(self, lines, i, path):
        """Plan 0048: a preset unit of type 5 (a tile unit) in the presets window: PresetUnitDispatch creates it with
        SUnitCreate (rng/seeds 7a: one game-seed step, unit seed Init(low)); nothing else draws (the room and
        object-region seeds are unchanged). OPUX must show exactly that."""
        tag, d, ln = lines[i]
        end = i + 1
        while end < len(lines) and lines[end][0] != "OPUX":
            end += 1
        if end >= len(lines):
            self.oracle("preset tile window not closed in the log")
            return i + 1
        dx = lines[end][1]
        g = step(*seed_t(d["gs"]))
        o = dx.get("o") or {}
        ok = (dx["rs"] == d["rs"] and dx["gs"] == fmt(g) and o.get("us") == fmt((g[0], INIT_HIGH))
              and not any(x[0] in ("MT0", "MU0") for x in lines[i + 1:end]))
        self.ok(ok, "%s:%d preset tile unit %d: OPUX %s, model gs %s us %s" % (path, ln, d["id"], dx, fmt(g),
                                                                                fmt((g[0], INIT_HIGH))))
        if ok:
            self.opu_confirmed.add((path, lines[end][2]))
            self.stats["preset tile units (type 5): one game-seed step, unit seed Init(low)"] = \
                self.stats.get("preset tile units (type 5): one game-seed step, unit seed Init(low)", 0) + 1
        self.skip_side(lines[i + 1:end + 1], path)
        return end + 1

    def skip_side(self, win, path):
        for tg, dd, ll in win:
            if tg == "MT0":
                self.mt_room_cur = dd["room"]
                self.game_cur = dd.get("game", self.game_cur)
            elif tg == "MU":
                self.note_unmodelled(path, dd, ll)
            if tg in collision.COLL_TAGS or tg == "RRESEED":
                self.world.event(tg, dd, ll, path)
            elif tg in CLIENT_TAGS:
                self.client.append((tg, dd, ll))
            elif tg in ("MT0", "MTX", "MC0", "MC"):
                self.window_cell_test(tg, dd, ll, path)

    def window_cell_test(self, tag, d, ln, path):
        """plan 0038 batch H4b (spawn 42): a MonSpawnTry outside a pass (the presets window: DS1 preset monsters such
        as sarcophagi, evil huts and nests) for a class whose BaseId has an offset-cell SpawnClassCellTest: the
        result is predicted by the collision model on the activation-model grids (the window's own marks are not
        applied). The request itself stays an oracle there."""
        st = self.__dict__.setdefault("_win_mt", [])
        if tag == "MT0":
            st.append(d)
        elif tag == "MTX":
            if st:
                st.pop()
        elif tag == "MC0" and st:
            cls = st[-1]["cls"]
            b = self.t.m(cls, 0x02, "<h") if self.t.valid(cls) else -1
            self._win_mc = None
            if b in collision.CLASS_CELL or b == 298:
                try:
                    with self.world.model_state():      # the activation model: there is no pass snapshot here
                        self._win_mc = (cls, self.world.spawn_class_cell_test(cls, d["room"], d["x"], d["y"], 1))
                except collision.NotLogged as e:
                    self.oracle("presets window SpawnClassCellTest (model needs %s)" % str(e).split(" of room")[0])
        elif tag == "MC" and getattr(self, "_win_mc", None):
            cls, r = self._win_mc
            self._win_mc = None
            self.ok((1 if d["r"] else 0) == r, "%s:%d presets window SpawnClassCellTest class %d: %s, model %d" % (
                path, ln, cls, d["r"], r))
            k = "presets window SpawnClassCellTest class %d predicted (result %d)" % (cls, r)
            self.stats[k] = self.stats.get(k, 0) + 1

    def client_check(self, path):
        """The client name roll (sub_004AC870_ClientMonNameBuild): the name seed it receives must be the one the
        model predicted on the server for the same unit id, and its draws follow monspecial.name_roll."""
        cs = self.client_stats
        ev = sorted(self.client, key=lambda e: e[2])
        j = 0
        while j < len(ev):
            tg, d, ln = ev[j]
            j += 1
            if tg != "CN0":
                self.fail_("%s:%d client %s without a CN0 before it" % (path, ln, tg))
                continue
            pred = self.ns_pred.get((path, d["id"]))
            if pred is None:
                cs["client name rolls of a unit the model did not create (not checked)"] = cs.get(
                    "client name rolls of a unit the model did not create (not checked)", 0) + 1
                while j < len(ev) and ev[j][0] != "CN0":
                    j += 1
                continue
            ns, what, diff = pred
            self.ok(d["ns"] == monspecial.client_name_seed(ns), "%s:%d client name seed %04x, server model %04x & 0xFF (unit id %d)"
                    % (path, ln, d["ns"], ns, d["id"]))
            want = [] if d["cls"] in self.sp.name_fixed else self.sp.name_roll(ns)
            got = []
            while j < len(ev) and ev[j][0] != "CN0":
                tg2, d2, ln2 = ev[j]
                j += 1
                if tg2 == "CNR" and d2["u"] == d["u"]:
                    got.append((d2["k"], d2["idx"]))
                elif tg2 == "CNH" and d2["u"] == d["u"]:
                    got.append(("R", d2["r"]))
            self.ok(got == want, "%s:%d client name roll %s, model %s (name seed %04x)" % (path, ln, got, want, ns))
            k = "client name rolls checked (%s)" % ("fixed name, no roll" if not want else
                                                   ("with appellation" if len(want) > 3 else "prefix and suffix"))
            cs[k] = cs.get(k, 0) + 1


def sp_report(c):
    """Plan 0018 coverage."""
    def by(rows, kd, ke):
        out = {}
        for r in rows:
            k = "%s %s" % (("normal", "nightmare", "hell")[r[kd]], "expansion" if r[ke] else "classic")
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items()))
    print("plan 0018: champion packs %d %s" % (len(c.champions), by(c.champions, 5, 6)))
    print("plan 0018: unique groups %d %s (pass %d, MonPlace 2 %d)" % (
        len(c.uniques), by(c.uniques, 4, 5), sum(1 for u in c.uniques if u[6] == "pass"),
        sum(1 for u in c.uniques if u[6] == "MonPlace 2")))
    placed = [s_ for s_ in c.supers if s_[6] == "placed"]
    print("plan 0018: superuniques placed %d %s; SuperUniqueSpawn calls without a unit %d" % (
        len(placed), by(placed, 4, 5), len(c.supers) - len(placed)))
    for pth, lid, i, info, diff, exp, _ in placed:
        print("  %s level %d diff %d exp %d: superunique %d class %d at %s (preset %s, AutoPos %d), mods %s, extra picks %s, "
              "minions %s%s" % (os.path.basename(pth), lid, diff, exp, i, info["cls"], info["pos"], info["preset"],
                                info["autopos"], info.get("mods"), info.get("extra"), info.get("minions"),
                                ", Radament escorts %d" % info["radament"] if "radament" in info else ""))
    print("plan 0018: MonPlace presets %s" % sorted((p[2], p[4], p[5], p[6]) for p in c.presets))
    for k in sorted(c.mods_drawn):
        print("  %-60s %d" % (k, c.mods_drawn[k]))
    for pth, ln, cls, diff, exp, got, want in c.aura_level_diff:
        print("  aura level differs: %s:%d class %d diff %d exp %d: logged %d, MonStatsInit + 3 = %d" % (
            os.path.basename(pth), ln, cls, diff, exp, got, want))
    for k in sorted(c.client_stats):
        print("  %-60s %d" % (k, c.client_stats[k]))


def cmd_check(argv):
    excel, root, verbose, paths = DEFAULT_EXCEL, drlg.DEFAULT_DATA, False, []
    it = iter(argv)
    for a in it:
        if a == "--excel":
            excel = next(it)
        elif a == "--root":
            root = next(it)
        elif a == "-v":
            verbose = True
        else:
            paths.append(a)
    if not paths:
        print(__doc__)
        return 2
    c = Checker(excel, root, verbose)
    for p in paths:
        c.run(p)
    print("passes: %s" % dict(sorted(c.results.items())))
    print("rooms with the seed predicted from the map seed: %d; from the log only: %d" % (c.rooms_pred, c.rooms_logseed))
    print("pass-entry room seed predicted end to end (RW1..RW4 drew nothing, or tools/objects.py predicted it): %d rooms, %d populated" % (
        len(c.rooms_e2e), len(c.populated_e2e)))
    for pth, ln, lid, room, n in c.populated_e2e:
        print("  %s:%d level %d room %08x: %d creations" % (os.path.basename(pth), ln, lid, room, n))
    print("seeds %s, difficulties %s, populated/empty levels %s" % (sorted(c.seeds_used), sorted(c.diffs), sorted(c.levels)))
    print("closed MonDen gates on levels %s" % sorted(c.closed_levels))
    print("creations %d; group sizes %d; champions %d %s; uniques %d %s" % (
        len(c.creations), len(c.group_sizes), len(c.champions), c.champions[:6], len(c.uniques), c.uniques[:6]))
    tr = c.type_rolls
    umax = [d for r in tr for d in r["draws"] if d[0] == "umax"]
    print("type rolls %d: special %d; MonUMax draws %d (r = 5: %d, r <= 5: %d); MonUMin draws %d" % (
        len(tr), sum(1 for r in tr if r["res"] == 0), len(umax), sum(1 for d in umax if d[1] == 5),
        sum(1 for d in umax if d[1] <= 5), sum(1 for r in tr for d in r["draws"] if d[0] == "umin")))
    print("champion rolls %s; special-count increments %d" % (c.champ_rolls, c.nspec_incr))
    print("unit-seed steps after Init(step(game).low) at MU: %s" % dict(sorted((str(k), v) for k, v in c.unit_steps.items())))
    for pth, ln, lid, cls, j in c.unit_steps_odd:
        print("  %s:%d level %d class %d: %d steps" % (os.path.basename(pth), ln, lid, cls, j))
    for k in sorted(c.stats):
        print("  %-60s %d" % (k, c.stats[k]))
    for k in sorted(c.oracles):
        print("  oracle %-53s %d calls" % (k, c.oracles[k]))
    for k in sorted(c.wnd_hits):
        print("  MonWndr watch: %-50s %d" % (k, c.wnd_hits[k]))
    sp_report(c)
    if c.obj_grid:
        print("objects window on the grid model (tools/objects.py with tools/collision.py, plan 0027):")
        for k in sorted(c.obj_grid):
            print("  %-96s %d" % (k, c.obj_grid[k]))
    c.world.report()
    print("monspawn: %d checks, %d mismatches; collision: %d checks, %d mismatches" % (
        c.checks, c.fail, c.world.checks, c.world.fail))
    return 1 if (c.fail or c.world.fail) else 0


def main(argv):
    if len(argv) < 2 or argv[1] != "check":
        print(__doc__)
        return 2
    return cmd_check(argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
