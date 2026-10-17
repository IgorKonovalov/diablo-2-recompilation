"""Model of the room lifecycle (plan 0040 Phase 2), checked against runtime logs, from
docs/findings/drlg/0009-room-lifecycle.md.

Usage:
  python3 -I tools/rooms.py check <run.log> [...] [--excel DIR] [--json OUT] [-v]

<run.log> is written by tools/d2run.py with tools/gdb/rooms.gdb (tools/gdb/rooms.py on top of tools/gdb/pilot.py).
Every line carries the game frame "f". The model predicts, per log, in log order:

  * references (RM0 .. RMX, finding section 2): DrlgRefMove(old, new) replayed on the RM0 snapshot (refs at the four
    near-list distances, status), with the near lists of the RMX snapshot (DrlgRefAddNear builds a missing list
    before it walks it); the sequence of enter/leave callbacks (RCB, room and kind, each with the refs and status at
    its entry), the activations they make (ACTA after e1 when +0x30 = 0 and +0x28 has no 0x100000), and the refs and
    status of every snapshot room at RMX. The callbacks' own inputs (+0x28 DT1/DS1/built bits, +0x30, the type) are
    taken from the RCB line;
  * client lists (CRC, CE, CL; section 2): the enter calls for the rooms of the new near list not in the old one, in
    list order, then the leave calls; +0x78 before each; at every RP, +0x78 of each room = 1 if the room is in the
    near list of the client's current room, else 0 (one client);
  * the release pass (RP, RT, FREE; section 4): idle counts carried from one pass to the next (0 with a client, +1
    without; a new room starts at 0), the release test (portal pin 0x400000, status >= 2, a town or level 120 needs
    every room of the level at status >= 2, act +0x50 = 0), the rooms freed (idle + 1 > 10 and the test), and the
    release frame against the frame its +0x78 last fell to 0 (120..131 when the first eligible pass frees it);
  * the tiles release (TR0, TRX): a server release has EDX 1 and ends with 0x200000 set, a client one EDX 0 and
    0x200000 clear;
  * the save rule (US, USD; section 5): save and kept per unit from the logged inputs (UnitIsDead, SaveMonsters, the
    udead state test, the alignment, MonTypeFlag 0x18, the owner and pet tests, MonStats2 restore, Objects
    Restore/RestoreVirgins, the sparkle and state-7 tests), the mode-12 room draw (seed out = step(seed in), low mod 3,
    and the room seed chained unit to unit), and a record line exactly when saved;
  * the records (MREC, UREC, IREC): the monster record's fields from the unit (x, y, class, id, +0xC4, +0xC8, frame,
    stats 13 and 6, the logged UnitGetMaxHp, the flag bits from the monster flags, the logged alignment, +0xD0 and the
    mode, the mod bytes); the unit record's (x, y, type, class, frame, +0xC4, +0xC8); the item expiry from its logged
    inputs (0 quest; frame + 30000 magic; 45000 qualities 5..9; base type 4 with stat 14 > 10000 45000; else 15000,
    30000 for a socket filler not of base type 4);
  * the new-rooms walk (WG, POP, RS0): the wanderer gate's draw (out = step(in), pass iff low & 0x7FFF = 0, the roll
    WR only if it passes, +0x78 = 0 and Levels MonWndr != 0), and per walked room: populated (+0x34 bit 0 clear:
    RS0 then POP), restored (bit 0 set, bit 1 clear: RS0 only) or nothing;
  * the restore (RS0 .. RSX; section 6): per monster record (MR0) the outcome (kept, dropped by the 0x400 rule or the
    level-108 rule, else created on the minion, special or exact path, the exact path falling back to radius 5,
    SpawnPosPick and the spiral), the created unit's id and class (the record's) and mode (12 for a flag-4 record on
    the exact path, else 1), the game-seed draws (one per created unit, SUnitCreate; the unit's +0x28 is the low word
    after it), the room draws of an exact placement (3), the position of an exact placement (the record's), stats 13
    and 7 (the record's), 6 (the saved life within 7500 frames, else the saved maximum), 12 (the monsters/stats model's
    level for a plain monster; the first instance's for a special), the +0xC4/+0xC8 bits written back, and the region
    counts MonRegionUnitLeave moves; the item list (IL: a record with a non-zero expiry below the frame is dropped,
    every other one restored in list order), each item's game-seed draws, seed and position against its save (IS0,
    matched by the serialised bytes), and the expiry written back (max(saved, frame + 15000), 0 kept); the unit records
    (UR0) re-created (URC) with their type, class and position, or kept (URK);
  * the preset path (PSU0, PSUX): moved out of the preset unit (left 0) into the AI control +0x38;
  * the town-follow case: a monster of alignment 0 in a room of a town level at the release, not saved, and its id
    never seen again (MON lines, MR0, US).

Exit 0 only if every check holds. Stdlib only. Read-only.
"""
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from rng import step  # noqa: E402

DEFAULT_EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
M32 = 0xFFFFFFFF
TOWNS = {1, 40, 75, 103, 109}
TAGS = {"GP", "RM0", "RMX", "RCB", "ACTA", "RAB", "DRA", "CRC", "CE", "CL", "RP", "RT", "FREE", "TR0", "TRX", "US",
        "USD", "MREC", "UREC", "IS0", "IREC", "RS0", "RSM", "RSI", "RSX", "MR0", "MRC", "MRS", "MRE", "MRX", "IL",
        "IR0", "IRC", "IRX", "UR0", "URC", "URK", "WG", "WR", "WS", "POP", "PSU0", "PSUX", "PIN", "MON", "LOGERR",
        "PLR"}


def seed_t(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def steps_between(a, b, limit=64):
    """k >= 0 with step^k(a) = b, or None."""
    x = a
    for k in range(limit + 1):
        if x == b:
            return k
        x = step(*x)
    return None


def nth(a, k):
    for _ in range(k):
        a = step(*a)
    return a


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


# ---- the reference model (finding section 2) ---------------------------------------------------------------------

class RefModel:
    """refs[4] and status per DRLG room, and the callback sequence of DrlgRefMove."""

    def __init__(self, before, after):
        self.r = {}
        for k, v in before.items():
            self.r[int(k)] = {"refs": list(v[0:4]), "st": v[4]}
        self.near = {}
        for k, v in after.items():
            self.near[int(k)] = list(v[10])
        for k, v in before.items():
            if int(k) not in self.near or not self.near[int(k)]:
                self.near[int(k)] = list(v[10])
        self.calls = []        # (kind, room, refs at entry, status at entry)
        self.unknown = set()

    def room(self, d):
        if d not in self.r:
            self.unknown.add(d)
            self.r[d] = {"refs": [0, 0, 0, 0], "st": 4}
        return self.r[d]

    def call(self, kind, d):
        R = self.room(d)
        self.calls.append((kind, d, list(R["refs"]), R["st"]))
        return len(self.calls) - 1

    def recompute(self, R):
        if R["st"] < 4 and R["refs"][R["st"]] != 0:
            return
        s = 0
        while s < 4 and R["refs"][s] == 0:
            s += 1
        R["st"] = s

    def enter(self, d, k, cbinfo):
        """g_DrlgRefEnterFns[k](d); cbinfo(i) gives the logged RCB line of call i (its +0x28, +0x30, type)."""
        R = self.room(d)
        i = self.call("e%d" % k, d)
        info = cbinfo(i)
        if k == 0:
            R["st"] = 0
        elif k == 1:
            if R["st"] > 1:
                R["st"] = 1
        elif k == 2:
            fl, ty = (info["fl"], info["ty"]) if info else (0, 0)
            if fl & 0x1000000 and not (ty == 2 and not fl & 0x2000000) and R["st"] > 2:
                R["st"] = 2
                if R["refs"][1] != 0:
                    self.enter(d, 1, cbinfo)
        elif k == 3:
            if R["st"] > 3:
                R["st"] = 3

    def enter_test(self, d, k, cbinfo):
        R = self.room(d)
        if R["st"] >= k and all(R["refs"][j] == 0 for j in range(k + 1)):
            self.enter(d, k, cbinfo)

    def leave(self, d, k):
        R = self.room(d)
        self.call("l%d" % k, d)
        if k < 3:
            self.recompute(R)
        elif R["st"] != 4:
            self.recompute(R)

    def add_near(self, d, k, cbinfo):
        for n in self.near.get(d, []):
            if k < 3:
                self.add_near(n, k + 1, cbinfo)
            self.enter_test(n, k, cbinfo)
            N = self.room(n)
            N["refs"][k] = (N["refs"][k] + 1) & 0xFFFF

    def ref_add(self, d, k, cbinfo):
        self.add_near(d, k + 1, cbinfo)
        self.enter_test(d, k, cbinfo)
        R = self.room(d)
        R["refs"][k] = (R["refs"][k] + 1) & 0xFFFF

    def remove_near(self, d, k):
        for n in self.near.get(d, []):
            if not n:
                continue
            N = self.room(n)
            N["refs"][k] = (N["refs"][k] - 1) & 0xFFFF
            self.leave(n, k)
            if k < 3:
                self.remove_near(n, k + 1)

    def move(self, old, new, cbinfo):
        if old == new:
            return
        if new:
            self.ref_add(new, 0, cbinfo)
        if old:
            R = self.room(old)
            if R["refs"][0]:
                R["refs"][0] -= 1
                self.leave(old, 0)
                self.remove_near(old, 1)


# ---- the save rule (finding section 5) ---------------------------------------------------------------------------

def monster_save(u, sub):
    """(save, kept) of InactiveMonsterSaveTest from the US line u and the logged sub-results."""
    save = 1 if (sub.get("sm") or u["c4"] & 0x2000000) else 0
    dead = sub.get("dead", 0)
    if u["m"] == 12:
        rem = sub["draw"][0] if "draw" in sub else None
        if rem is None or rem != 0:
            save = 0
    if dead:
        if sub.get("ud"):
            save = 0
        if sub.get("al") == 2:
            save = 0
    if u.get("d0", 11) < 8:
        save = 0 if dead else 1
    elif dead and u["c"] in (363, 364):
        save = 0
    if sub.get("mt18") and dead:
        save = 0
    kept = 0
    if u["c4"] & 0x80000000:
        own = sub.get("own")
        if own and own[0] and own[1] == 0:
            kept = sub.get("pet", 0)
        save = 0
    if u["c4"] & 0x200:
        save = 0
    rb = sub.get("rb")
    if rb is None or rb == 0:
        save = 0
    elif rb == 2:
        save = 1
    return save, 1 if kept else 0


def other_save(u, sub):
    """(save, kept) of InactiveUnitSaveTest for types 0, 2..5."""
    t = u["t"]
    flag = 1 if (sub.get("sm") or u["c4"] & 0x2000000) else 0
    if t == 2:
        if u["c"] in (59, 60):
            return 1, 1
        orow = sub.get("orow")
        if orow is not None:
            if orow[0] == 0 or (sub.get("spk", 0) & 2):
                flag = 0
            if orow[1] and u["m"] != 0:
                flag = 0
        return flag, 0
    if t == 0:
        if sub.get("s7"):
            return 1, 1
        return flag, 0
    if t in (4, 5):
        return 1, 0
    return 0, 0


def item_expiry(f, sub):
    """ItemGroundExpiry 0x00558A10 from its logged inputs."""
    if sub.get("quest"):
        return 0
    q = sub.get("q")
    if q == 4:
        return (f + 30000) & M32
    if q is not None and 5 <= q <= 9:
        return (f + 45000) & M32
    if sub.get("bt") == 4:
        return (f + 45000) & M32 if s32(sub.get("gold", 0)) > 10000 else (f + 15000) & M32
    if sub.get("filler"):
        return (f + 30000) & M32
    return (f + 15000) & M32


def mrec_parse(h):
    b = bytes.fromhex(h)
    x, y, c, uid, c4, c8, fl, lead, ai34, path, aist, m58 = struct.unpack_from("<iiiiIIIiiIii", b, 0)
    ns, = struct.unpack_from("<H", b, 0x30)
    mods = list(b[0x32:0x3B])
    suid, = struct.unpack_from("<H", b, 0x3C)
    s13, maxhp, hp, a4c, a50, fr = struct.unpack_from("<iiiiii", b, 0x40)
    return {"x": x, "y": y, "c": c, "id": uid, "c4": c4, "c8": c8, "fl": fl, "lead": lead, "path": path,
            "m58": m58, "ns": ns, "mods": mods, "suid": suid, "s13": s13, "maxhp": maxhp, "hp": hp, "fr": fr & M32}


def urec_parse(h):
    b = bytes.fromhex(h)
    x, y, t, c, m, fr, c4, c8, a20, a24 = struct.unpack_from("<iiiiiiIIii", b, 0)
    return {"x": x, "y": y, "t": t, "c": c, "m": m, "fr": fr, "c4": c4, "c8": c8, "a20": a20, "inter": b[0x28]}


def rec_align(fl):
    return 2 if fl & 0x100 else (1 if fl & 0x80 else 0)


class Tables:
    def __init__(self, excel):
        import monpool
        self.pool = monpool.Tables(excel)
        self.monpool = monpool
        try:
            import monstats
            self.mst = monstats.Model(monstats.Tables(excel))
        except Exception:      # tables missing: stat 12 is then compared with the first instance only
            self.mst = None

    def monwndr(self, lid):
        lv = self.pool.lv
        return lv[lid][0x2E] if 0 <= lid < len(lv) else 0

    def level(self, cls, lid, diff, exp):
        if self.mst is None:
            return None
        return self.mst.level(cls, lid, diff, exp)[0]


# ---- the checker -------------------------------------------------------------------------------------------------

class Checker:
    def __init__(self, T, verbose=False):
        self.T = T
        self.v = verbose
        self.n = collections.Counter()
        self.mis = collections.Counter()
        self.examples = collections.defaultdict(list)
        self.hist = collections.defaultdict(collections.Counter)

    def ok(self, key, cond, where, detail=""):
        self.n[key] += 1
        if not cond:
            self.mis[key] += 1
            if len(self.examples[key]) < 5:
                self.examples[key].append("%s %s" % (where, detail))
            if self.v:
                print("MISMATCH %s %s %s" % (key, where, detail))
        return cond

    def run(self, path):
        lines = []
        for k, line in enumerate(open(path, errors="replace")):
            sp = line.find(" ")
            tag = line[:sp]
            if tag not in TAGS:
                continue
            try:
                d = json.loads(line[sp + 1:])
            except ValueError:
                continue
            lines.append((k + 1, tag, d))
        self.log(os.path.basename(path), lines)

    # one log
    def log(self, name, L):
        diff, exp = None, None
        for _, tag, d in L:
            if tag == "RP":
                diff, exp = d.get("diff"), d.get("exp")
                break
        self.n["logs"] += 1
        if any(tag == "LOGERR" for _, tag, _ in L):
            self.ok("logger errors", False, name, "%d LOGERR lines" % sum(1 for _, t, _ in L if t == "LOGERR"))
        self.refs(name, L)
        self.clients(name, L)
        self.release(name, L)
        self.saves(name, L)
        self.walk(name, L)
        self.restore(name, L, diff, exp)
        self.misc(name, L)
        self.hist["logs by acts with active rooms"][",".join(str(a + 1) for a in sorted(self.acts_of(L)))] += 1
        self.hist["logs by difficulty and game"]["%s %s" % (diff, "expansion" if exp else "classic")] += 1

    def acts_of(self, L):
        out = set()
        for _, tag, d in L:
            if tag == "RP":
                for a, act in enumerate(d["acts"]):
                    if act and act["rooms"]:
                        out.add(a)
        return out

    # -- references
    def refs(self, name, L):
        i = 0
        while i < len(L):
            ln, tag, d = L[i]
            if tag != "RM0":
                i += 1
                continue
            j = i + 1
            cbs = []
            actas = []
            while j < len(L) and L[j][1] != "RMX":
                if L[j][1] == "RCB" and L[j][2].get("in"):
                    cbs.append(L[j][2])
                if L[j][1] == "ACTA" and L[j][2].get("in"):
                    actas.append((len(cbs), L[j][2]))
                if L[j][1] == "RM0":
                    break
                j += 1
            if j >= len(L) or L[j][1] != "RMX":
                self.ok("ref moves closed", False, "%s:%d" % (name, ln))
                i = j
                continue
            x = L[j][2]
            M = RefModel(d["s"], x["s"])
            M.move(d["old"], d["new"], lambda k: cbs[k] if k < len(cbs) else None)
            where = "%s:%d" % (name, ln)
            self.n["ref moves"] += 1
            self.ok("ref callbacks: count", len(M.calls) == len(cbs), where, "%d predicted, %d logged" % (
                len(M.calls), len(cbs)))
            for k, (kind, room, refs, stt) in enumerate(M.calls[:len(cbs)]):
                c = cbs[k]
                if not self.ok("ref callbacks: kind and room", (c["k"], c["d"]) == (kind, room), where,
                               "#%d predicted %s %d, logged %s %d" % (k, kind, room, c["k"], c["d"])):
                    break
                self.ok("ref callbacks: refs and status at entry", (c["refs"], c["st"]) == (refs, stt), where,
                        "#%d %s %d model %s/%d log %s/%d" % (k, kind, room, refs, stt, c["refs"], c["st"]))
                self.hist["callbacks"][kind] += 1
            # activations: an e1 on a room with no active room and no 0x100000
            pred = [k for k, c in enumerate(cbs) if c["k"] == "e1" and c["a30"] == 0 and not c["fl"] & 0x100000]
            got = [k - 1 for k, _ in actas]
            self.ok("activations (ACTA after e1)", pred == got, where, "pred %s got %s" % (pred, got))
            self.n["activations predicted"] += len(pred)
            for k, v in x["s"].items():
                R = M.r.get(int(k))
                if R is None:
                    continue
                self.ok("refs and status at RMX", (R["refs"], R["st"]) == (list(v[0:4]), v[4]), where,
                        "room %s model %s/%d log %s/%d" % (k, R["refs"], R["st"], v[0:4], v[4]))
            self.n["rooms reached outside the RM0 snapshot"] += len(M.unknown)
            i = j + 1

    # -- client lists
    def clients(self, name, L):
        n78 = {}
        cur_near = {}       # client -> near list of its current room
        expect = []
        for ln, tag, d in L:
            where = "%s:%d" % (name, ln)
            if tag == "CRC":
                if expect:
                    self.ok("client list calls", False, where, "%d expected calls missing" % len(expect))
                on, nn = d["on"], d["nn"]
                expect = [("CE", r) for r in nn if r not in on] + [("CL", r) for r in on if r not in nn]
                cur_near[d["c"]] = nn
                self.n["client room changes"] += 1
            elif tag in ("CE", "CL"):
                e = expect.pop(0) if expect else None
                self.ok("client list calls", e == (tag, d["r"]), where, "expected %s, got %s %d" % (e, tag, d["r"]))
                if d["r"] in n78:
                    self.ok("+0x78 before CE/CL", n78[d["r"]] == d["n78"], where,
                            "model %d log %d" % (n78[d["r"]], d["n78"]))
                n78[d["r"]] = d["n78"] + (1 if tag == "CE" else -1)
            elif tag == "RP":
                near = set()
                for v in cur_near.values():
                    near.update(v)
                nclients = len(cur_near)
                for act in d["acts"]:
                    if not act:
                        continue
                    for r, dr, idle, x78, fl34, status, fl28, lid, mn in act["rooms"]:
                        if r in n78:
                            self.ok("+0x78 at RP (model)", n78[r] == x78, where, "room %d model %d log %d" % (
                                r, n78[r], x78))
                        n78[r] = x78
                        if nclients == 1:
                            self.ok("+0x78 = clients whose room's near list holds the room",
                                    x78 == (1 if r in near else 0), where, "room %d +0x78 %d in near %s" % (
                                        r, x78, r in near))
            elif tag == "FREE":
                n78.pop(d["r"], None)

    # -- the release pass
    def release(self, name, L):
        idle = {}
        last_leave = {}      # room -> frame its +0x78 fell to 0
        in78 = {}
        pending = None       # (frame, {room: predicted release}) of the last RP
        rt_pred = {}
        freed_rooms = set()
        tr_pending = []
        for ln, tag, d in L:
            where = "%s:%d" % (name, ln)
            f = d.get("f")
            if tag == "CL" and d["n78"] == 1:
                last_leave[d["r"]] = f
            elif tag == "CE":
                last_leave.pop(d["r"], None)
            if tag == "RP":
                if pending is not None:
                    self.close_pass(pending, freed_rooms, where)
                self.ok("RP frame % 12 = 0", f is not None and f % 12 == 0, where, "f %s" % f)
                self.n["release passes"] += 1
                pred = {}
                for a, act in enumerate(d["acts"]):
                    if not act:
                        continue
                    self.ok("act +0x50 = 0 on the server", act["a50"] == 0, where)
                    for r, dr, idl, x78, fl34, status, fl28, lid, mn in act["rooms"]:
                        if r in idle:
                            self.ok("idle count carried to the next pass", idle[r] == idl, where,
                                    "room %d model %d log %d" % (r, idle[r], idl))
                        else:
                            self.ok("a new room's idle count is 0", idl == 0, where, "room %d idle %d" % (r, idl))
                        n = 0 if x78 else idl + 1
                        test = None
                        if n > 10:
                            test = int(not (fl28 & 0x400000) and status >= 2 and
                                       (lid not in TOWNS and lid != 120 or (mn is not None and mn >= 2)))
                            rt_pred[r] = (test, lid, fl28 & 0x400000, status, mn)
                        pred[r] = (n, test, dr, lid)
                        idle[r] = n
                pending = (f, pred)
                freed_rooms = set()
            elif tag == "RT":
                p = rt_pred.pop(d["r"], None)
                self.ok("release test (RT)", p is not None and p[0] == (1 if d["ok"] else 0), where,
                        "room %d pred %s log %d" % (d["r"], p, d["ok"]))
                self.n["release tests"] += 1
                if p and not d["ok"]:
                    self.hist["release test refusals"]["pin" if p[2] else ("status" if p[3] < 2 else "town")] += 1
            elif tag == "FREE":
                freed_rooms.add(d["r"])
                idle.pop(d["r"], None)
                self.n["releases"] += 1
                pf = pending[1].get(d["r"]) if pending else None
                if pf:
                    self.hist["released levels"][pf[3]] += 1
                lf = last_leave.pop(d["r"], None)
                if lf is not None:
                    dt = f - lf
                    self.hist["release frames after the last leave"][dt if dt <= 131 else ">131"] += 1
                    first = -(-lf // 12) * 12 + 120
                    if pf and pf[1] == 1 and pf[0] == 11:
                        self.ok("release at the first eligible pass: 120..131 frames", f == first and
                                120 <= dt <= 131, where, "room %d leave %d free %d" % (d["r"], lf, f))
                tr_pending.append(d.get("d"))
            elif tag == "TR0":
                if d["cl"]:
                    self.ok("client tiles release: EDX 0", d["edx"] == 0, where)
                    self.n["client tiles releases"] += 1
                else:
                    self.ok("server tiles release comes from a FREE", d["d"] in tr_pending, where)
                    if d["d"] in tr_pending:
                        tr_pending.remove(d["d"])
                    self.ok("server tiles release: EDX 1", d["edx"] == 1, where)
                    self.n["server tiles releases"] += 1
            elif tag == "TRX":
                if d["cl"]:
                    self.ok("client release leaves 0x200000 clear", not d["fl"] & 0x200000, where)
                else:
                    self.ok("server release sets 0x200000", bool(d["fl"] & 0x200000), where)
            elif tag in ("GP",):
                idle, pending = {}, None
        if pending is not None:
            self.close_pass(pending, freed_rooms, name + ":end", final=True)

    def close_pass(self, pending, freed, where, final=False):
        f, pred = pending
        want = {r for r, (n, test, dr, lid) in pred.items() if n > 10 and test}
        if final and not freed and want:
            return       # the log ended inside the pass
        self.ok("rooms freed by the pass", want == freed, where, "pred %s log %s" % (sorted(want), sorted(freed)))

    # -- the save rule and the records
    def saves(self, name, L):
        ctx = None
        room_seed = {}
        for ln, tag, d in L:
            where = "%s:%d" % (name, ln)
            if tag in ("US", "RP", "RS0", "WG", "CRC", "RM0", "FREE"):
                if ctx is not None:
                    self.save_one(ctx, room_seed)
                    ctx = None
            if tag == "RP":
                room_seed = {}
            if tag == "US":
                ctx = {"u": d, "usd": None, "recs": [], "where": where}
            elif ctx is not None and tag in ("USD", "MREC", "UREC", "IREC", "IS0"):
                if tag == "USD":
                    ctx["usd"] = d
                else:
                    ctx["recs"].append((tag, d, where))
        if ctx is not None:
            self.save_one(ctx, room_seed)

    def save_one(self, ctx, room_seed):
        u, d, where = ctx["u"], ctx["usd"], ctx["where"]
        if d is None:
            self.ok("save decision logged (USD)", False, where)
            return
        if u.get("rs"):
            if u["r"] in room_seed:
                self.ok("room seed chained unit to unit in a release", room_seed[u["r"]] == u["rs"], where)
            room_seed[u["r"]] = u["rs"]
        sub = d["sub"]
        recs = ctx["recs"]
        kinds = [t for t, _, _ in recs if t != "IS0"]
        if u["t"] == 1:
            save, kept = monster_save(u, sub)
            self.ok("monster save rule: save", save == d["save"], where, "pred %d log %d sub %s" % (
                save, d["save"], sub))
            self.ok("monster save rule: kept", kept == (1 if d["kept"] else 0), where)
            if u["m"] == 12:
                self.n["mode-12 room draws"] += 1
                if "draw" in sub and u.get("rs"):
                    out = nth(seed_t(u["rs"]), 1)
                    self.ok("mode-12 draw: seed out = step(seed in)", "%08x:%08x" % out == sub["draw"][1], where)
                    self.ok("mode-12 draw: low mod 3", out[0] % 3 == sub["draw"][0], where)
                    room_seed[u["r"]] = sub["draw"][1]
                else:
                    self.ok("mode-12 draw logged", False, where)
            self.hist["monster saves"][("saved" if d["save"] else "freed") + (" kept" if d["kept"] else "")
                                      + (" dead" if sub.get("dead") else "")] += 1
            self.ok("a monster record exactly when saved", kinds == (["MREC"] if d["save"] else []), where,
                    "save %d records %s" % (d["save"], kinds))
            if u["lid"] in TOWNS and not d["save"] and not sub.get("dead") and not d["kept"]:
                self.town_follow.append((ctx["where"].split(":")[0], u))
            for t, r, w in recs:
                if t == "MREC":
                    self.check_mrec(u, r, w)
            return
        save, kept = other_save(u, sub)
        if d["k"] == "kept":
            self.ok("unit save rule: kept path", kept == 1, where, "type %d class %d" % (u["t"], u["c"]))
        elif u["t"] == 2:
            self.ok("object save rule (B4)", save == (1 if d["flag"] else 0), where,
                    "class %d pred %d log %d sub %s" % (u["c"], save, d["flag"], sub))
        self.hist["unit saves"]["type %d %s%s" % (u["t"], "saved" if save else "freed", " kept" if kept else "")] += 1
        want = []
        if save:
            want = ["IREC"] if u["t"] == 4 else ["UREC"]
        self.ok("a unit record exactly when saved", kinds == want, where, "type %d save %d records %s" % (
            u["t"], save, kinds))
        for t, r, w in recs:
            if t == "UREC":
                rr = urec_parse(r["b"])
                self.n["unit records"] += 1
                self.ok("unit record: x, y, type, class", (rr["x"], rr["y"], rr["t"], rr["c"]) == (
                    u["x"], u["y"], u["t"], u["c"]), w)
                self.ok("unit record: frame, +0xC4", (rr["fr"], rr["c4"]) == (u["f"], u["c4"]), w)
                self.ok("unit record: +0xC8 (0x100 when kept)", rr["c8"] == (u["c8"] | (0x100 if kept else 0)), w,
                        "rec %x unit %x" % (rr["c8"], u["c8"]))
                if u["t"] == 2 and u["m"] != 0:
                    self.n["objects saved that were operated"] += 1
            elif t == "IREC":
                self.n["item records"] += 1
                pe = item_expiry(r["f"], r["sub"] or {})
                self.ok("item expiry", pe == r["exp"] & M32, w, "pred %d log %d sub %s" % (pe, r["exp"], r["sub"]))
                is0 = next((x for tt, x, _ in recs if tt == "IS0"), None)
                self.item_bytes[r["b"]] = (r, is0)

    def check_mrec(self, u, d, where):
        r = mrec_parse(d["b"])
        self.n["monster records"] += 1
        self.ok("monster record: x, y, class, id", (r["x"], r["y"], r["c"], r["id"]) == (u["x"], u["y"], u["c"],
                                                                                       u["id"]), where)
        self.ok("monster record: frame", r["fr"] == u["f"], where)
        self.ok("monster record: +0xC4, +0xC8", (r["c4"], r["c8"] & ~0x100) == (u["c4"], u["c8"] & ~0x100), where,
                "rec %x/%x unit %x/%x" % (r["c4"], r["c8"], u["c4"], u["c8"]))
        st = u.get("st", {})
        self.ok("monster record: stat 13, stat 6", (r["s13"], r["hp"]) == (st.get("13", 0), st.get("6", 0)), where,
                "rec %d/%d unit %s" % (r["s13"], r["hp"], st))
        mh = d.get("in", {}).get("maxhp")
        if mh is not None:
            self.ok("monster record: max life = UnitGetMaxHp", r["maxhp"] == s32(mh), where)
        self.ok("monster record: max life = stat 7", r["maxhp"] == st.get("7", 0), where,
                "rec %d stat 7 %s" % (r["maxhp"], st.get("7")))
        self.ok("monster record: mods", r["mods"] == u.get("mods"), where)
        mf = u.get("mf") or 0
        fl = 0
        fl |= 0x2 if mf & 4 else 0
        fl |= 0x800 if mf & 2 else 0
        fl |= 0x1 if mf & 1 else 0
        fl |= 0x20 if mf & 0x10 else 0
        al = d.get("in", {}).get("al")
        if al is not None:
            fl |= {2: 0x100, 0: 0x200, 1: 0x80}.get(al, 0)
        fl |= 0x400 if u.get("d0", 11) != 11 and u.get("d0", 11) >= 8 else 0
        fl |= 0x4 if u["m"] in (12, 0) else 0
        mask = 0x2 | 0x800 | 0x1 | 0x20 | 0x380 | 0x400 | 0x4
        self.ok("monster record: flag bits", r["fl"] & mask == fl, where, "rec %x pred %x (mf %x)" % (
            r["fl"] & mask, fl, mf))
        self.mrecs[(r["id"], r["fr"])] = (r, u)
        if r["fl"] & 0x4 and r["fl"] & 0x2:
            self.n["dead champions saved"] += 1

    # -- the new-rooms walk and the wanderer gate
    def walk(self, name, L):
        i = 0
        while i < len(L):
            ln, tag, d = L[i]
            where = "%s:%d" % (name, ln)
            if tag != "WG":
                i += 1
                continue
            si, so = seed_t(d["si"]), seed_t(d["so"])
            self.ok("wanderer gate: out = step(in)", step(*si) == so, where)
            self.n["wanderer gate draws"] += 1
            passed = (so[0] & 0x7FFF) == 0
            roll = passed and d["n78"] == 0 and self.T.monwndr(d["lid"]) != 0
            self.n["wanderer gate passes"] += 1 if passed else 0
            if d["n78"] == 0 and self.T.monwndr(d["lid"]):
                self.n["wanderer gate draws with +0x78 = 0 and MonWndr"] += 1
            # the lines up to the next WG (or the end of the walk) belong to this room
            j = i + 1
            seen = []
            while j < len(L) and L[j][1] not in ("WG", "RP", "CRC", "RM0"):
                if L[j][1] in ("WR", "WS", "POP", "RS0"):
                    seen.append((L[j][1], L[j][2].get("r")))
                j += 1
            got_wr = any(t == "WR" for t, _ in seen)
            self.ok("wanderer roll iff the gate passes with +0x78 = 0 and MonWndr", got_wr == roll, where)
            fl = d["fl"]
            if not fl & 1:
                want = [("RS0", d["r"]), ("POP", d["r"])]
                self.n["walk: populated"] += 1
            elif not fl & 2:
                want = [("RS0", d["r"])]
                self.n["walk: restored"] += 1
            else:
                want = []
            got = [(t, r) for t, r in seen if t in ("RS0", "POP")]
            self.ok("new-rooms walk: populate / restore / nothing", got == want, where, "want %s got %s" % (want, got))
            i += 1

    # -- the restore
    def restore(self, name, L, diff, exp):
        frame_of = {}
        freed = set()
        drlg_pop = {}
        last_dra = {}
        i = 0
        cur = None
        for k, (ln, tag, d) in enumerate(L):
            where = "%s:%d" % (name, ln)
            if tag == "FREE":
                freed.add(d.get("d"))
            elif tag == "DRA":
                last_dra[d["d"]] = d
                if d["d"] in freed:
                    self.ok("re-activated room keeps its populated bit (DRLG +0x60)", d["pop"] & 1 == 1, where)
                    self.n["re-activations"] += 1
            elif tag == "RS0":
                cur = {"r": d["r"], "lid": d["lid"], "re": d["d"] in freed, "mons": 0, "items": 0, "units": 0}
                dra = last_dra.get(d["d"])
                if dra:
                    self.hist["restore frames after the activation"][d["f"] - dra["f"]] += 1
                self.n["restores run"] += 1
                if cur["re"]:
                    self.n["restores of a re-activated room"] += 1
                    self.lids_restored[d["lid"]] += 1
            elif tag == "MR0":
                self.restore_monster(name, L, k, diff, exp)
            elif tag == "IL":
                self.restore_items(name, L, k)
            elif tag == "UR0":
                r = urec_parse(d["b"])
                nxt = L[k + 1] if k + 1 < len(L) else None
                self.n["unit records restored"] += 1
                if r["c8"] & 0x100:
                    self.ok("kept unit found (URK)", nxt is not None and nxt[1] == "URK", where)
                elif nxt is not None and nxt[1] == "URC":
                    u = nxt[2]
                    self.ok("unit re-created: type, class", u.get("u") and (u["t"], u["c"]) == (r["t"], r["c"]), where,
                            "rec %s unit %s" % ((r["t"], r["c"], r["x"], r["y"]), u))
                    if u.get("u"):
                        self.hist["unit re-created at the record position"][(u["x"], u["y"]) == (r["x"], r["y"])] += 1
                    if r["t"] == 2:
                        self.n["objects restored"] += 1
                        if r["m"] != 0:
                            self.n["objects restored that were operated"] += 1
                else:
                    self.ok("unit record restored", False, where, "no URC after UR0")
            elif tag == "PSU0":
                nxt = L[k + 1] if k + 1 < len(L) else None
                if d["pp"]:
                    self.n["preset paths moved"] += 1
                    self.ok("preset path moved (PSUX: preset 0, AI +0x38 = the path)",
                            nxt is not None and nxt[1] == "PSUX" and nxt[2]["pp"] == 0 and nxt[2]["ai38"] == d["pp"],
                            where)

    def restore_monster(self, name, L, k, diff, exp):
        ln, _, d = L[k]
        where = "%s:%d" % (name, ln)
        r = mrec_parse(d["b"])
        f = d["f"]
        j = k + 1
        mrc = mrs = mre = mrx = None
        while j < len(L) and L[j][1] not in ("MR0", "RSM"):
            t = L[j][1]
            if t == "MRC" and mrc is None:
                mrc = L[j][2]
            elif t == "MRS" and mrs is None:
                mrs = L[j][2]
            elif t == "MRE" and mre is None:
                mre = L[j][2]
            elif t == "MRX" and mrx is None:
                mrx = L[j][2]
                break
            j += 1
        self.n["monster records restored"] += 1
        fl = r["fl"]
        lid = d.get("lid")
        if lid == 108 and d.get("q23") and not fl & 4 and r["c"] != 243:
            outcome = "dropped (108)"
        elif r["c8"] & 0x100:
            outcome = "kept"
        elif fl & 0x400 and fl & 0x180:
            outcome = "dropped (0x400)"
        elif fl & 0x20:
            outcome = "minion"
        elif fl & 1:
            outcome = "special"
        else:
            outcome = "exact"
        self.hist["monster restore paths"][outcome] += 1
        if outcome.startswith("dropped") or outcome == "kept":
            self.ok("monster restore: no creation (%s)" % outcome, mrc is None and mrx is not None and mrx["dropped"],
                    where)
            return
        if mrc is None:
            self.ok("monster restore: creation logged", False, where)
            return
        self.ok("monster restore: path", mrc["path"] and mrc["path"][0] == outcome, where,
                "pred %s log %s" % (outcome, mrc["path"]))
        u = mrc.get("u")
        if not u:
            self.n["monster restore: creation failed"] += 1
            return
        mode = 12 if (fl & 4 and outcome == "exact") else 1
        self.ok("monster restore: id, class, mode", (mrc["id"], mrc["c"], mrc["m"]) == (r["id"], r["c"], mode), where,
                "rec %s pred mode %d unit %s" % ((r["id"], r["c"]), mode, (mrc["id"], mrc["c"], mrc["m"])))
        gs0, gs1 = seed_t(d["gs"]), seed_t(mrc["gs"])
        kg = steps_between(gs0, gs1)
        self.hist["monster restore: game-seed draws (%s)" % outcome][kg] += 1
        self.ok("monster restore: one game-seed draw (SUnitCreate)", kg == 1, where, "k %s" % kg)
        if kg == 1:
            self.ok("monster restore: unit +0x28 = the game seed's low word", mrc["u28"] == gs1[0], where)
            self.ok("monster restore: unit seed = Init(that low word)", mrc["s"] is not None, where)
        kr = steps_between(seed_t(d["rs"]), seed_t(mrc["rs"]), 400)
        self.hist["monster restore: room draws (%s, %s)" % (outcome, "+".join(mrc["path"]))][kr] += 1
        if mrc["path"] == ["exact"]:
            self.ok("exact placement: 3 room draws", kr == 3, where, "k %s" % kr)
            self.ok("exact placement: at the record's x, y", (mrc["x"], mrc["y"]) == (r["x"], r["y"]), where)
        if fl & 1 and fl & 2 and fl & 4:
            self.n["dead champions restored"] += 1
            self.ok("a dead champion comes back alive (mode 1)", mrc["m"] == 1, where)
        if mrs:
            st = mrs["st"]
            late = ((f - r["fr"]) & M32) >= 7500
            hp = r["maxhp"] if late else r["hp"]
            self.hist["7500-frame rule"]["over" if late else "under"] += 1
            self.ok("restored stats 13 and 7 (the record's)", (st.get("13", 0), st.get("7", 0)) == (r["s13"], r["maxhp"]),
                    where, "rec %d/%d unit %s" % (r["s13"], r["maxhp"], st))
            self.ok("restored stat 6 (7500-frame rule)", st.get("6", 0) == hp, where,
                    "pred %d (late %s, dt %d) unit %s" % (hp, late, (f - r["fr"]) & M32, st))
            if r["hp"] != r["maxhp"]:
                self.n["restored monsters damaged before the release"] += 1
        if mre:
            st = mre["st"]
            self.ok("stats 13, 7, 6 unchanged after the write", (st.get("13", 0), st.get("7", 0), st.get("6", 0)) == (
                mrs["st"].get("13", 0), mrs["st"].get("7", 0), mrs["st"].get("6", 0)) if mrs else False, where)
            first = self.mrecs.get((r["id"], r["fr"]))
            lvl = self.T.level(r["c"], lid, diff, exp) if diff is not None else None
            if outcome == "exact" and lvl is not None:
                self.ok("stat 12: the monsters/stats level", st.get("12") == lvl, where, "model %s unit %s" % (
                    lvl, st.get("12")))
                self.n["stat 12 predicted by the monsters/stats model"] += 1
            if first:
                fst = first[1].get("st", {})
                self.ok("stat 12 = the first instance's", st.get("12") == fst.get("12"), where)
            self.ok("+0xC4 gets 0x3000000 and the record's 0x20000", mre["c4"] & 0x3020000 == (
                0x3000000 | (r["c4"] & 0x20000)), where)
            if r["c8"] & 0x200:
                self.ok("+0xC8 gets 0x200", bool(mre["c8"] & 0x200), where)
            al = rec_align(fl)
            self.ok("MonRegionUnitLeave args", (mre["m58"], mre["al"], mre["dead"], mre["f40"]) == (
                r["m58"], al, 1 if mode == 12 else 0, fl & 0x40), where)
            if mrx and mre["reg"] and mrx["reg"]:
                pred = {k: list(v) for k, v in mre["reg"].items() if v}
                cur = str(mre["cur"])
                if mre["f40"] == 0 and al == 0 and cur in pred:
                    pred[cur][2] -= 1
                    if (mre["mf"] or 0) & 1:
                        pred[cur][1] -= 1
                self.ok("region counts after MonRegionUnitLeave", {k: v for k, v in mrx["reg"].items() if v} == pred,
                        where, "pred %s log %s" % (pred, mrx["reg"]))
            self.n["monsters restored"] += 1
            if (mre["mf"] or 0) & 0x1E or fl & 0x23:
                self.n["special monsters restored (champion, unique, superunique, minion)"] += 1

    def restore_items(self, name, L, k):
        ln, _, d = L[k]
        where = "%s:%d" % (name, ln)
        f = d["f"]
        want = [rec for rec, ex, n in d["recs"] if not (ex != 0 and s32(f) > s32(ex))]
        dropped = len(d["recs"]) - len(want)
        self.n["item records dropped (expired)"] += dropped
        j = k + 1
        got = []
        while j < len(L) and L[j][1] not in ("IL", "UR0", "RSX", "RS0", "MR0"):
            ln2, t, e = L[j]
            w2 = "%s:%d" % (name, ln2)
            if t == "IR0":
                got.append(e["rec"])
                saved = self.item_bytes.get(e["b"])
                ex = e["exp"]
                irc = L[j + 1][2] if j + 1 < len(L) and L[j + 1][1] == "IRC" else None
                irx = None
                for jj in range(j + 1, min(j + 6, len(L))):
                    if L[jj][1] == "IRX":
                        irx = L[jj][2]
                        break
                self.n["items restored"] += 1
                if irc and irc.get("it"):
                    kg = steps_between(seed_t(e["gs"]), seed_t(irc["gs"]))
                    self.hist["item restore: game-seed draws"][kg] += 1
                    self.ok("item restore: two game-seed draws (SUnitCreate, type 4)", kg == 2, w2, "k %s" % kg)
                    self.ok("item restore: unit seed = Init(+0x28)", irc["s"] == "%08x:%08x" % (irc["u28"], 666), w2)
                    if saved and saved[1]:
                        s0 = saved[1]
                        simple = struct.unpack_from("<I", bytes.fromhex(e["b"]), 2)[0] & 0x200000
                        self.hist["item restore: simple (compact) items"][bool(simple)] += 1
                        self.ok("item restore: the saved start seed (+0x28), 0 for a simple item",
                                irc["u28"] == (0 if simple else s0["u28"]), w2,
                                "save %s restore %s simple %s" % (s0["u28"], irc["u28"], bool(simple)))
                        self.hist["item restore: same unit id"][irc["id"] == s0["id"]] += 1
                        self.hist["item restore: same x, y"][(irc["x"], irc["y"]) == (s0["x"], s0["y"])] += 1
                    else:
                        self.n["items restored without their save in the log"] += 1
                if irx:
                    pe = ex if ex == 0 or s32(ex) >= s32(f + 15000) else (f + 15000) & M32
                    self.ok("item restore: expiry max(saved, frame + 15000), 0 kept", irx["exp"] & M32 == pe & M32, w2,
                            "pred %d log %d" % (pe, irx["exp"]))
            j += 1
        self.ok("items restored: list order, expired ones dropped", got == want, where, "want %s got %s" % (
            want, got))

    def misc(self, name, L):
        seen_ids = collections.defaultdict(list)
        for ln, tag, d in L:
            if tag == "MON":
                for m in d.get("m", []):
                    seen_ids[m["id"]].append(ln)
            elif tag in ("MR0",):
                seen_ids[mrec_parse(d["b"])["id"]].append(ln)
            elif tag == "US":
                seen_ids[d["id"]].append(ln)
            elif tag == "PIN":
                self.hist["pin calls (server)" if not d["cl"] else "pin calls (client)"][
                    "%s %s" % ("clear" if d["arg"] else "set", hex(d["outer"] or d["caller"]))] += 1
            elif tag == "RAB":
                self.hist["RoomActivateB callers"][hex(d["caller"])] += 1
        tf = [(n, u) for n, u in self.town_follow if n == name]
        for n, u in tf:
            uline = next((ln for ln, tag, d in L if tag == "US" and d["u"] == u["u"] and d["id"] == u["id"]), 0)
            later = [x for x in seen_ids.get(u["id"], []) if x > uline]
            self.n["town-follow: monsters in a town room freed at the release"] += 1
            self.ok("town-follow: absent after the release", not later, "%s:%d" % (name, uline),
                    "class %d id %d seen again at %s" % (u["c"], u["id"], later[:3]))

    def report(self):
        print("rooms check: %d logs" % self.n["logs"])
        for k in sorted(self.n):
            if k == "logs":
                continue
            m = self.mis.get(k, 0)
            print("  %-80s %7d%s" % (k, self.n[k], ("  MISMATCHES %d" % m) if m else ""))
        for k in sorted(self.hist):
            print("  %s: %s" % (k, dict(sorted(self.hist[k].items(), key=lambda kv: str(kv[0])))))
        if self.mis:
            print("mismatch examples:")
            for k in sorted(self.mis):
                for e in self.examples[k]:
                    print("  %s: %s" % (k, e))
        tot = sum(self.mis.values())
        events = sum(v for k, v in self.n.items() if k != "logs")
        print("SUMMARY mismatches=%d checks=%d" % (tot, events))
        return tot


def cmd_check(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="rooms.py check")
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--excel", default=DEFAULT_EXCEL)
    ap.add_argument("--json")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    C = Checker(Tables(a.excel), a.verbose)
    C.town_follow = []
    C.items_saved = []
    C.item_bytes = {}
    C.mrecs = {}
    C.lids_restored = collections.Counter()
    for p in a.logs:
        C.run(p)
    C.hist["levels with a restore of a re-activated room"] = C.lids_restored
    tot = C.report()
    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"counts": dict(C.n), "mismatches": dict(C.mis),
                       "hist": {k: {str(x): y for x, y in v.items()} for k, v in C.hist.items()}}, fh, indent=1,
                      sort_keys=True)
    return 1 if tot else 0


def main(argv):
    if not argv or argv[0] != "check":
        print(__doc__)
        return 2
    return cmd_check(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
