#!/usr/bin/env python3
"""Plan 0066 batch S1b (`lane/n66c`): the catalogue blocks of docs/specs/monsters/ai/catalogue.md as models, checked call
by call against the logged AI decisions.

    python3 -I tools/ai_model_check.py check [LOG ...] [--logs LIST] [--rows R3,R4,S11] [--out FILE]
    python3 -I tools/ai_model_check.py list                       # the entries this tool models
    python3 -I tools/test_ai_model_check.py                       # the engine on synthetic decisions

What is compared. Each model below is one entry's pseudocode block, transcribed from the spec text (never from
tools/ai_resume.py's interpreter or a decompile). A decision is the logged AID line with its boundary calls (AIB, the
think function's own, `ai_resume.top_level`) and their returns (AIR). The model starts from the AID line's words (the
unit seed at the think call, `t`, `dist`, `melee`, `v14`/`v18`/`v1C`, `aip` of the game's difficulty, the frame `T`,
`MonsterData+0x54`, the skill words, the parameter-list head) and runs the block. At each call it makes of a function the
logger treats as a boundary it is compared with the next logged call: the callee, every argument word the block names
(registers and stack, by the convention table `CONV`), the unit seed (the model's own draws since the last oracle) and
the three control words `v14`, `v18`, `v1C` (the model's own stores since the last oracle). The logged return then
feeds the model as an ADR-0004 oracle: `EAX`, the unit seed after the call, the control words after it, and the words a
search wrote through a stack pointer (AIR `bl`). When the block returns, the logged calls must be used up and the model's
seed must equal the AIX line's exit seed (so a draw after the last call is compared too). Call sites are not predicted:
the tool lists, per block call (its label), the distinct logged return addresses (`SITE` lines), and a label with two
sites, or two labels with one site, is a finding against the transcription.

Unknowns. A branch the block takes on a value the log does not hold is a fork: both sides are run and the decision
matches if one does. Such a decision cannot fail at the fork, so every control below counts the fork-free decisions only
(review-fixes rule 10). A decision stops (no verdict) when a call has no AIR line, the logger's cap of calls per decision
was reached, or the 600-call limit fired.

Controls, over each entry's fork-free matched decisions: every named branch, and every store the block makes to `v14`,
`v18`, `v1C` or `Unit+0xC4` (`set ...`), reversed or skipped alone (`FLIP`: the decisions that then fail, in the decision
or, for a store, at the same unit's next logged decision of the same think, whose AID control words must equal the
model's at return; n the decisions that ran it); `le` (each draw test `<=` for `<`); `lecmp` (each other `<` compare
`<=`); `d0` (every `aip` from the Normal column); for R43 only, `sdiv` (the idle's `low mod 10` as a signed remainder). A branch or store that fails none cannot be told from its reverse by
these logs. `ARM`: each branch's outcomes over the fork-free decisions. `EDGE`: the fork-free decisions in which a
compare met an equal pair, the only kind that tells `<` from `<=`. `NEXT`: the model's control words at return against
the unit's next decision (same think), with how often the model had moved a word. `VALS`: values a branch compared.

Plug-in. `--logs` takes a file of log paths (one per line, relative to the current directory), so a later run's logs
(the bestiary tour, plan 0066 question 3 (c)) are checked with the same models; `--rows` picks entries by name.
Stdlib, tools/ai.py (the parser) and tools/ai_resume.py (`top_level`, the think's own calls).
"""
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_resume as R  # noqa: E402

M32 = 0xFFFFFFFF
SKIP = object()          # a word the model does not compare


def u32(v):
    return v & M32


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


class NeedChoice(Exception):
    pass


class Mismatch(Exception):
    pass


class Stop(Exception):
    pass


class Ret:
    def __init__(self, eax, bl):
        self.eax = eax
        self.bl = bl or {}

    def out(self, arg, word=0):
        """The word `word` of the block the call's stack argument `arg` pointed at, after the call (AIR `bl`)."""
        blk = self.bl.get(str(arg))
        if blk is None:
            raise Stop("no output block for argument %d" % arg)
        return blk[word]


# Calling conventions of the boundary functions the blocks call: name -> (address, ecx, edx, stack argument names).
# "G" and "U" are the game and the unit; other names are the block's arguments, in the block's order. Taken from the
# first-boundary emulation families of tools/ai_cat_emu*.py where they model the call (their maps are [C], run:2026-10-30-
# ai-cat-emu-1 ff.) and else from machinery § B's argument order with the game and unit in ECX and EDX.
CONV = {
    "SetModeAtUnit": (0x005DDF90, "G", "U", ("mode", "t")),
    "SetMode": (0x005DDFC0, "G", "U", ("mode", "x", "y")),
    "Idle": (0x005DE080, "G", "U", ("n",)),
    "Delay": (0x005DE0F0, "G", "U", ("n",)),
    "Ring": (0x005DE200, "G", "U", ("r",)),
    "Walk": (0x005DEC80, "G", "U", ("t", "flags")),
    "WalkZ": (0x005DECA0, "G", "U", ("t", "flags")),
    "WalkStop": (0x005DEF80, "G", "U", ("t", "n")),
    "RunToUnit": (0x005DED20, "G", "U", ("t",)),
    "RunFlags": (0x005DED00, "G", "U", ("t", "flags")),
    "Walk13": (0x005DED40, "G", "U", ("t", "flags")),
    "WalkToPoint": (0x005DED90, "G", "U", ("x", "y")),
    "RunStop": (0x005DEFB0, "G", "U", ("t", "stop")),
    "StepAway": (0x005DEFE0, "G", "U", ("t", "d", "flag")),
    "T56": (0x005DF7D0, "G", "U", ("t", "byte", "flag")),
    "Ovr": (0x005DE190, "U", "type", ("param", "byte")),
    "St3or19": (0x005DD2B0, "U", None, ()),
    "LifePct": (0x005DD280, "U", None, ()),
    "FindHostile": (0x005DDC30, "G", "U", ("pd", "pm")),
    "UnitGetRoom": (0x00620BB0, None, None, ("u",)),
    "RoomGetLevelId": (0x0061A1B0, None, None, ("room",)),
    "UseSkill": (0x005DEAD0, "G", "U", ("mode", "skill", "t", "x", "y")),
    "UseSeqSkill": (0x005DE000, "G", "U", ("skill", "t", "x", "y")),
    "WanderNear": (0x005DF530, "G", "U", ("u", "r")),
    "Toward": (0x005DE6D0, "G", "U", ("t", "max", "ring")),
    "StepAwayXY": (0x005DF140, "G", "U", ("t", "n", "f")),
    "TakeOff": (0x005F2EB0, "G", "U", ()),
    "Land": (0x005F2FC0, "G", "U", ()),
    "UnitLifePct": (0x00621F20, None, None, ("u",)),
    "HasState": (0x00639DF0, None, None, ("u", "state")),
    "StateSet": (0x00639DB0, None, None, ("u", "state", "v")),
    "SkillFindByOwner": (0x006439B0, "u", "skill", ("n",)),
    "GetUnitSkill": (0x006439F0, "u", "skill", ()),
    "GetSkillLevel": (0x006442A0, None, None, ("u", "s", "b")),
    "UnitSearch": (0x005DD0B0, "G", "U", ("ps", "cb", "kind")),
    "HelpBlock": (0x0058F730, "G", "U", ("pblk",)),
    "SkillTargetOk": (0x005FD470, "G", "U", ("skill", "u", "a", "b")),
    "GameFindUnit": (0x00552F60, "G", "type", ("guid",)),
    "ParamsHead": (0x0058EE80, "U", None, ()),
    "ParamsPop": (0x0058ED10, "G", "U", ()),
    "MonsterOwner": (0x0058F0D0, "U", None, ()),
    "ClassChainPos": (0x006510C0, None, None, ("cls", "a", "b")),
    "ClassChainStep": (0x0054DA60, "cls", "pos", ()),
    "UnitAlignGet": (0x006259B0, None, None, ("u",)),
    "VileMotherSpawn": (0x005F9E30, "G", "U", ("t", "M")),
    "SpawnClassCellTest": (0x005FD350, "cls", "room", ("x", "y", "z")),
    "ApproachPointTest": (0x005DC640, "u", "t", ()),
    "UnitDirToPoint": (0x00621DC0, None, None, ("u", "x", "y")),
    "SetPathTargetUnit": (0x00620C10, None, None, ("u", "t")),
    "PathSetFacing": (0x006488A0, None, None, ("path", "facing")),
    "GetTargetUnit": (0x00553540, "G", "U", ()),
    "RoomIsTown": (0x0061AB00, None, None, ("room",)),
    "InMeleeRange": (0x00622C40, None, None, ("u", "t", "z")),
    "FindTarget": (0x005DD7F0, "G", "U", ("ctl", "pd", "pm")),
    "CancelEvents": (0x00540E60, "G", "U", ("kind", "z")),
    "QueueEvent": (0x005417D0, "G", "U", ("kind", "frame", "a", "b")),
    "MonAiInit": (0x005B0E00, "G", "U", ("ctl", "state")),
    "UnitDistSq": (0x005B0BD0, "u", "t", ()),
    "RangePow2": (0x00472210, "seedp", "n", ()),
    "PathDist": (0x005DC5C0, "u", "x", ("y",)),
    "MoveToPoint": (0x005DE440, "G", "U", ("x", "y", "n")),
}


class Run:
    """One pass of a model over one logged decision, with a fixed list of choices for the unknown branches."""

    def __init__(self, dec, choices=(), flip=None, ctl=None):
        self.dec = dec
        a = self.aid = dec["aid"]
        self.log = R.top_level(dec)
        self.i = 0
        self.seed = ai.seedval(a["s"])
        cb = bytes.fromhex(a["ctl"])
        w = lambda off: s32(int.from_bytes(cb[off:off + 4], "little"))
        self.v = {0x14: w(0x14), 0x18: w(0x18), 0x1C: w(0x1C)}
        self.ctlw = w
        self.c4 = a["c4"]
        self.ctlp = a["ctlp"]
        self.x, self.y = a["x"], a["y"]
        tt = a.get("t") or [None] * 7
        self.ttype, self.tid, self.tx, self.ty = tt[0], tt[2], tt[4], tt[5]
        self.cls = a["c"]
        self.ms = a["ms"]
        self.ms2 = a["ms2"]
        head = bytes.fromhex(a["head"]) if a.get("head") else None
        self.head = [int.from_bytes(head[k:k + 4], "little") for k in range(0, 0x1C, 4)] if head else None
        self.choices = list(choices)
        self.ci = 0
        self.flip = flip
        self.ctl = ctl
        self.arms = []            # (branch, value) in order, known branches only
        self.labels = []          # (label, logged ra) per compared call
        self.vals = []            # (branch, compared value)
        self.edges = []           # branches decided on an equal pair
        self.G, self.U = a["g"], a["u"]
        self.t = a["ctx"][2]
        self.dist = s32(a["ctx"][5])
        self.melee = a["ctx"][6]
        self.T = a["fr"]
        self.m54 = a["md"]
        diff = 0 if ctl == "d0" else a["diff"]
        aipv = [ai.s16(x) for x in ai.le16(a["aip"], 24)]
        self._aip = [aipv[3 * k + diff] for k in range(8)]
        skb = bytes.fromhex(a["sk"])
        self.skill = [ai.s16(int.from_bytes(skb[2 * k:2 * k + 2], "little")) for k in range(8)]
        self.skmode = list(skb[16:24])

    # ---- inputs
    def aip(self, k):
        return self._aip[k - 1]

    # ---- branches
    def br(self, name, cond, val=None):
        """A branch on a known value. `val`: the compared value, listed in the report (`VALS`)."""
        v = bool(cond)
        if name == self.flip:
            v = not v
        self.arms.append((name, v))
        if val is not None:
            self.vals.append((name, val))
        return v

    def less(self, name, a, b, draw=False):
        """The branch `a < b` (signed). An equal pair is an edge case: the only kind that tells `<` from `<=`
        (`EDGE` lines). `draw`: a draw test, which the `le` control makes `<=`."""
        if a == b:
            self.edges.append(name)
        le = (draw and self.ctl == "le") or (not draw and self.ctl == "lecmp")
        return self.br(name, a <= b if le else a < b)

    def store(self, name, key, value):
        """A store of the block to `v14`, `v18`, `v1C` (key 0x14, 0x18, 0x1C) or `Unit+0xC4` ("c4"), as the branch-like
        step `name`: the flip control skips it."""
        self.arms.append((name, True))
        if name == self.flip:
            return
        if key == "c4":
            self.c4 = value
        else:
            self.v[key] = s32(value)

    def unknown(self, name):
        if self.ci < len(self.choices):
            v = self.choices[self.ci]
            self.ci += 1
            return v
        raise NeedChoice(name)

    # ---- draws on the unit seed
    def step(self):
        self.seed = ai.step(self.seed)
        return self.seed[0]

    def d100(self):
        return self.step() % 100

    def chance(self, name, k):
        """`chance(K)`: `D100() < aip(K)`, one draw, as the branch `name`."""
        return self.less(name, self.d100(), self.aip(k), draw=True)

    def rchance(self, name, n, lim):
        """`Range(n) < lim`, one draw (none for n < 1), as the branch `name`."""
        return self.less(name, self.rng(n), lim, draw=True)

    def rng(self, n):
        if n < 1:
            return 0
        return self.step() % n

    # ---- calls
    def call(self, label, name, blk=None, **kw):
        """A boundary call. `kw`: the block's argument words by CONV name; `blk`: {argument index: {word: value}},
        words of the block a stack argument points at, before the call (AIB `b`)."""
        fn, ecx, edx, names = CONV[name]
        if self.i >= len(self.log):
            raise Mismatch("%s: the model calls %s, the log has no further call" % (label, name))
        b = self.log[self.i]
        diffs = []
        if b["fn"] != fn:
            raise Mismatch("%s: the model calls %s %08x, the log %08x@%08x" % (label, name, fn, b["fn"], b["ra"]))

        def want(spec):
            if spec is None:
                return SKIP
            if spec == "G":
                return self.G
            if spec == "U":
                return self.U
            return kw.get(spec, SKIP)
        for reg, spec in (("ecx", ecx), ("edx", edx)):
            v = want(spec)
            if v is not SKIP and v is not None and u32(v) != b[reg]:
                diffs.append("%s %x/%x" % (reg, u32(v), b[reg]))
        for k, nm in enumerate(names):
            v = kw.get(nm, SKIP)
            if v is not SKIP and v is not None and u32(v) != b["a"][k]:
                diffs.append("%s %x/%x" % (nm, u32(v), b["a"][k]))
        for i, words in (blk or {}).items():
            got = (b.get("b") or {}).get(str(i))
            if got is None:
                diffs.append("no block at argument %d" % i)
                continue
            for k, v in words.items():
                if u32(v) != got[k]:
                    diffs.append("blk%d[%d] %x/%x" % (i, k, u32(v), got[k]))
        if self.c4 is not None and self.c4 != b["c4"]:
            diffs.append("c4 %x/%x" % (self.c4, b["c4"]))
        if "%08x:%08x" % self.seed != b["s"]:
            diffs.append("seed %08x:%08x/%s" % (self.seed + (b["s"],)))
        for k, off in enumerate((0x14, 0x18, 0x1C)):
            if self.v[off] is not None and u32(self.v[off]) != b["c"][k]:
                diffs.append("v%x %x/%x" % (off, u32(self.v[off]), b["c"][k]))
        if diffs:
            raise Mismatch("%s: %s %s" % (label, name, ", ".join(diffs)))
        r = self.dec["air"].get(b["n"])
        if r is None:
            raise Stop("%s: no AIR line" % label)
        self.labels.append((label, b["ra"]))
        self.i += 1
        self.seed = ai.seedval(r["s"])
        for k, off in enumerate((0x14, 0x18, 0x1C)):
            self.v[off] = s32(r["c"][k])
        self.c4 = r["c4"]
        return Ret(r["eax"], r.get("bl"))

    def finish(self):
        d = self.dec
        if self.i < len(self.log):
            b = self.log[self.i]
            raise Mismatch("end: the model returns, the log has %08x@%08x" % (b["fn"], b["ra"]))
        if len(d["aib"]) >= d.get("bmax", 48):
            raise Stop("capped")
        if any(x.get("pend") == 0 for x in d.get("ail", [])):
            raise Stop("AIL")
        if d["aix"] is None:
            raise Stop("no AIX line")
        if "%08x:%08x" % self.seed != d["aix"]["s"]:
            raise Mismatch("end: exit seed %08x:%08x/%s" % (self.seed + (d["aix"]["s"],)))


class Outcome:
    def __init__(self):
        self.status = None        # ok, mismatch, stop
        self.why = ""
        self.forks = 0            # unknown branches on the matching path
        self.run = None           # the matching Run


def next_diff(run, nextd):
    """The control words the model holds at return that differ from the same unit's next decision's AID words (that
    decision's think the same), or None when there is no such decision."""
    if nextd is None or nextd["aid"]["th"] != run.aid["th"]:
        return None
    cb = bytes.fromhex(nextd["aid"]["ctl"])
    out = []
    for off in (0x14, 0x18, 0x1C):
        if run.v[off] is not None and u32(run.v[off]) != int.from_bytes(cb[off:off + 4], "little"):
            out.append("v%x" % off)
    return out


def check(model, dec, flip=None, ctl=None, limit=64):
    """Run every choice path of the model on one decision. ok if one path matches to the end."""
    out = Outcome()
    todo = [()]
    mism, stops, n = [], [], 0
    while todo and n < limit:
        ch = todo.pop()
        n += 1
        r = Run(dec, ch, flip, ctl)
        try:
            model(r)
            r.finish()
        except NeedChoice:
            todo.append(ch + (True,))
            todo.append(ch + (False,))
            continue
        except Mismatch as e:
            mism.append(str(e))
            continue
        except Stop as e:
            stops.append(str(e))
            continue
        out.status, out.forks, out.run = "ok", len(ch), r
        return out
    if stops:
        out.status, out.why = "stop", stops[0]
    elif todo:
        out.status, out.why = "stop", "fork limit"
    else:
        out.status, out.why = "mismatch", mism[0] if mism else "no path"
    return out


# ------------------------------------------------------------------------------------------------------------ models
# Each model is the entry's block as the spec states it, at b5999f5e. Labels name the block's step; branch names are
# `<entry>.<step>` and state what is tested.

def m_r1(r):
    """R100 (and R1's text): `if U has a room: Idle(200)`. R1's think, 0x005B0CD0, lies outside the logger's return-address
    windows, so its calls are never logged and it has no entry here."""
    room = r.call("room", "UnitGetRoom", u=r.U).eax
    if r.br("has-room", room != 0):
        r.call("idle", "Idle", n=200)


def m_r3(r):
    """R3 Zombie."""
    if r.br("1.melee", r.melee):
        mode = 4 if r.chance("1.chance(4)", 4) else 5
        r.call("1.setmode", "SetModeAtUnit", mode=mode, t=r.t)
        return
    if not r.br("2.St3or19", r.call("2.st3or19", "St3or19", U=r.U).eax):
        near = r.less("2.dist<aip(2)", r.dist, r.aip(2))
        if not (near and r.chance("2.chance(1)", 1)):
            room = r.call("2.room", "UnitGetRoom", u=r.U).eax
            lvl = r.call("2.level", "RoomGetLevelId", room=room).eax
            if r.br("2.level!=17", lvl != 17, val=lvl):
                r.call("2.ring", "Ring", r=3)
                return
    r.call("3.ovr", "Ovr", type=0, param=100, byte=0)
    r.call("3.run", "RunToUnit", t=r.t)


def m_r4(r):
    """R4 Bighead."""
    if r.br("1.melee", r.melee):
        pass
    elif r.br("1.St3or19", r.call("1.st3or19", "St3or19", U=r.U).eax):
        r.call("1.setmode5", "SetModeAtUnit", mode=5, t=r.t)
        return
    life = r.call("2.lifepct", "LifePct", U=r.U).eax
    if not r.less("3.life<aip(1)", s32(life), r.aip(1)):
        if r.br("3.melee", r.melee):
            r.call("3.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        if r.less("3.dist<15", r.dist, 15):
            if r.br("3.found", r.call("3.findhostile", "FindHostile").eax):
                if r.rchance("3.Range<aip(3)", 100, r.aip(3)):
                    r.call("3.setmode5", "SetModeAtUnit", mode=5, t=r.t)
                    return
        r.call("3.walk", "Walk", t=r.t, flags=7)
        return
    if r.less("4.dist<3", r.dist, 3):
        r.call("4.ovr", "Ovr", type=0, param=50, byte=0)
        if not r.br("4.stepped", r.call("4.stepaway", "StepAway", t=r.t, d=5, flag=1).eax):
            r.call("4.setmode5", "SetModeAtUnit", mode=5, t=r.t)
        return
    if r.less("5.15<dist", 15, r.dist):
        r.call("5.walkstop", "WalkStop", t=r.t, n=6)
        return
    if r.br("6.found", r.call("6.findhostile", "FindHostile").eax):
        if r.rchance("6.Range<aip(4)", 100, r.aip(4)):
            r.call("6.setmode5", "SetModeAtUnit", mode=5, t=r.t)
            return
    if r.rchance("7.Range<aip(2)", 100, r.aip(2)):
        r.call("7.t56", "T56", t=r.t, byte=3, flag=0)
    else:
        r.call("7.idle", "Idle", n=10)


def m_r5(r):
    """R5 BloodHawk."""
    if r.br("1.v14=1", r.v[0x14] == 1, val=r.v[0x14]) and r.br("1.melee", r.melee):
        r.store("set v14=0", 0x14, 0)
        r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    r.store("set v14=0#2", 0x14, 0)
    if not r.br("3.melee", r.melee):
        if r.chance("3.chance(1)", 1):
            r.call("3.ovr-swoop", "Ovr", type=0, param=r.aip(5), byte=r.dist)
            r.store("set v14=1", 0x14, 1)
            r.call("3.walk", "Walk", t=r.t, flags=0)
            return
        if r.less("3.3<dist", 3, r.dist):
            if r.chance("3.chance(2)", 2):
                r.call("3.ovr-50", "Ovr", type=0, param=-50, byte=0)
                r.call("3.ring4", "Ring", r=4)
                return
            r.call("3.ovr0", "Ovr", type=0, param=0, byte=0)
            r.call("3.ring3", "Ring", r=3)
            return
    elif r.chance("3.chance(3)", 3):
        r.call("3.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    r.call("4.ovr", "Ovr", type=0, param=r.aip(4), byte=0)
    if not r.br("4.stepped", r.call("4.stepaway", "StepAway", t=r.t, d=4, flag=1).eax):
        r.call("4.setmode4", "SetModeAtUnit", mode=4, t=r.t)


def m_r12(r):
    """R12 Goatman and R19 Swarm (the same block)."""
    if not r.br("1.melee", r.melee):
        if r.chance("1.chance(1)", 1):
            r.call("1.walk", "Walk", t=r.t, flags=7)
            return
    elif r.chance("1.chance(3)", 3):
        r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    r.call("2.idle", "Idle", n=r.aip(2))


def use_skill(r, label, k, target, x=0, y=0):
    """`UseSkillK(x)`: `MonAiUseSkill(SkKmode, SkillK, x, 0, 0)`."""
    return r.call(label, "UseSkill", mode=r.skmode[k - 1], skill=r.skill[k - 1], t=target, x=x, y=y)


def m_r15(r):
    """R15 SandMaggot, the think. `DelayE` is not a boundary (0x005DE130 is not logged): its calls are not compared."""
    ret = r.call("1.findhostile", "FindHostile", pm=0)
    h, hd = ret.eax, s32(ret.out(0))
    ph = r.v[0x14]
    if r.br("2.ph=3", ph == 3, val=ph) and r.less("2.v18<T", r.v[0x18], r.T) and r.br("2.Skill1>=0", r.skill[0] >= 0):
        use_skill(r, "2.useskill1", 1, r.t)
        r.store("set v18=T + aip(5)", 0x18, r.T + r.aip(5)); r.store("set v14=1", 0x14, 1)
        return
    if ph == 3:
        return
    life = s32(r.call("4.lifepct", "LifePct", U=r.U).eax)
    if (r.less("4.life<25", life, 25) and r.br("4.Skill2>=0", r.skill[1] >= 0) and r.less("4.hd<7", hd, 7)
            and r.less("4.v18<T", r.v[0x18], r.T) and r.rchance("4.Range<20", 100, 20)):
        use_skill(r, "4.useskill2", 2, r.t)
        r.store("set v18=T + aip(5)#2", 0x18, r.T + r.aip(5)); r.store("set v14=3", 0x14, 3)
        return
    if r.br("5.melee", r.melee) and r.chance("5.chance(4)", 4):
        r.call("5.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    if h == 0:
        r.vals.append(("hd when h=0", hd))
    if r.br("6.h", h != 0) and r.less("6.hd<15", hd, 15) and r.rchance("6.Range<aip(2)", 100, r.aip(2)):
        r.vals.append(("6.A2 target h=t", h == r.t))
        r.call("6.setmode5", "SetModeAtUnit", mode=5, t=h)
        return
    if r.less("7.D100<20", r.d100(), 20, draw=True):
        r.call("7.t56", "T56", t=r.t, byte=6, flag=0)
        return
    if r.less("8.v1C<aip(3)", r.v[0x1C], r.aip(3)) and r.rchance("8.Range<aip(1)", 100, r.aip(1)):
        if r.br("8.ph!=2|Skill3<0", ph != 2 or r.skill[2] < 0):
            r.call("8.t56", "T56", t=r.t, byte=6, flag=0)
            r.store("set v14=2", 0x14, 2)
            return
        r.store("set v1c+=1", 0x1C, r.v[0x1C] + 1)
        r.store("set v14=1#2", 0x14, 1)
        use_skill(r, "8.useskill3", 3, r.t)
        return


def m_r26(r):
    """R26 Arach."""
    life = s32(r.call("1.lifepct", "UnitLifePct", u=r.U).eax)
    if r.br("2.v14=1", r.v[0x14] == 1, val=r.v[0x14]):
        r.store("set v18=0", 0x18, 0)
        if r.less("2.75<life", 75, life):
            r.store("set v14=0", 0x14, 0)
            if r.chance("2.chance(3)", 3):
                r.store("set v14=2", 0x14, 2)
                r.call("2.walk13", "Walk13", t=r.t, flags=0)
                return
            r.call("2.t56", "T56", t=r.t, byte=6, flag=0)
            return
        if (r.br("2.melee", r.melee) and r.less("2.25<aip(1)", 25, r.aip(1))
                and r.rchance("2.Range<aip(1)-25", 100, r.aip(1) - 25)):
            r.call("2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        if not r.less("2.dist<aip(4)", r.dist, r.aip(4)) and not r.br("2.St3or19", r.call("2.st3or19", "St3or19", U=r.U).eax):
            r.store("set v14=0#2", 0x14, 0)
            r.call("2.t56b", "T56", t=r.t, byte=12, flag=0)
            return
        r.call("2.stepaway", "StepAway", t=r.t, d=4, flag=0)
        return
    if not r.br("3.melee", r.melee):
        if r.br("3.St3or19", r.call("3.st3or19", "St3or19", U=r.U).eax) or r.br("3.v18=1", r.v[0x18] == 1):
            r.store("set v18=1", 0x18, 1)
            r.call("3.walk13", "Walk13", t=r.t, flags=0)
            return
        r.store("set v1c+=1", 0x1C, r.v[0x1C] + 1)
        if r.less("3.20<v1C", 20, r.v[0x1C]):
            r.store("set v1c=0", 0x1C, 0)
        r.store("set v18=0#2", 0x18, 0)
        if r.br("3.v1C=1", r.v[0x1C] == 1) and r.rchance("3.Range<aip(3)", 100, r.aip(3)):
            r.store("set v18=1#2", 0x18, 1)
            r.call("3.walk13b", "Walk13", t=r.t, flags=0)
            return
        if r.rchance("3.Range<20", 100, 20):
            r.call("3.ring6", "Ring", r=6)
            return
        r.call("3.idle", "Idle", n=15)
        return
    r.store("set v14=2#2", 0x14, 2)
    if r.chance("5.chance(1)", 1):
        r.call("5.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    if not r.less("6.life<aip(5)", life, r.aip(5)):
        if r.rchance("6.Range<aip(2)", 100, r.aip(2)):
            r.call("6.t56", "T56", t=r.t, byte=4, flag=0)
            return
        r.call("6.idle", "Idle", n=15)
        return
    r.store("set v14=1", 0x14, 1)
    if r.br("8.Skill1>=0", r.skill[0] >= 0) and not r.br("8.state22", r.call("8.hasstate", "HasState", u=r.U, state=22).eax):
        use_skill(r, "8.useskill1", 1, 0)
        return
    r.call("9.stepaway", "StepAway", t=r.t, d=8, flag=0)


def m_r43(r):
    """R43 FoulCrowNest, the think (the init is not a think call, so it is not logged)."""
    if r.less("1.20<dist", 20, r.dist):
        r.call("1.idle", "Idle", n=25)
        return
    if not r.less("2.v18<aip(3)", r.v[0x18], r.aip(3)):
        r.store("set c4|=0x20000", "c4", r.c4 | 0x20000)
        r.call("2.die", "SetMode", mode=0, x=0, y=0)
        return
    e = s32(r.T - r.v[0x14])
    if e < 0:
        e = s32(-e)
    if r.br("4.Skill1>=0", r.skill[0] >= 0) and not r.less("4.e<aip(1)", e, r.aip(1)):
        r.store("set v14=T", 0x14, r.T)
        cls = 206 if r.ms2 > 206 else -1
        room = r.call("4.room", "UnitGetRoom", u=r.U).eax
        if r.br("4.cell", r.call("4.celltest", "SpawnClassCellTest", cls=cls, room=room, x=r.x, y=r.y, z=0).eax):
            r.store("set v18+=1", 0x18, r.v[0x18] + 1)
            use_skill(r, "4.useskill1", 1, r.t)
            return
    low = r.step()
    r.vals.append(("5.low>=2^31", low >= 0x80000000))
    if r.ctl == "sdiv":                                  # control: the remainder of a signed division
        q = abs(s32(low)) % 10
        r.call("5.idle", "Idle", n=20 + (-q if s32(low) < 0 else q))
        return
    r.call("5.idle", "Idle", n=20 + low % 10)


def m_r52(r):
    """R52 FrogDemon, the think. The cell test's address is not in the block: a call of it stops the decision."""
    if r.br("1.v1C=0", r.v[0x1C] == 0, val=r.v[0x1C]):
        if r.br("1.Skill1>=0", r.skill[0] >= 0) and r.less("1.12<dist", 12, r.dist):
            use_skill(r, "1.useskill1", 1, r.t)
            r.call("1.delay8", "Delay", n=8)
            r.store("set v1c=1", 0x1C, 1)
            r.call("1.takeoff", "TakeOff")
            return
        if r.br("1.Skill2>=0", r.skill[1] >= 0) and r.br("1.land", r.call("1.land", "Land").eax):
            use_skill(r, "emerge", 2, r.U)
            r.store("set v1c=2", 0x1C, 2)
            return
        raise Stop("1.cell test: not a modelled call")
    if r.br("2.v1C=1", r.v[0x1C] == 1):
        if r.br("2.Skill2>=0", r.skill[1] >= 0):
            em = False
            if r.less("2.dist<aip(8)", r.dist, r.aip(8)) and r.br("2.land", r.call("2.land", "Land").eax):
                em = True
            elif (r.less("2.dist<20", r.dist, 20) and r.less("2.64<v18", 64, r.v[0x18])
                  and r.br("2.land2", r.call("2.land2", "Land").eax)):
                em = True
            if em:
                use_skill(r, "emerge", 2, r.U)
                r.store("set v1c=2#2", 0x1C, 2)
                return
        r.call("2.takeoff", "TakeOff")
        r.call("2.delay24", "Delay", n=24)
        r.store("set v18+=1", 0x18, r.v[0x18] + 1)
        r.store("set v1c=1#2", 0x1C, 1)
        return
    if r.br("3.t=0", r.t == 0):
        r.call("3.delay32", "Delay", n=32)
        return
    if r.br("4.melee", r.melee):
        if r.rchance("4.Range<aip(2)", 100, r.aip(2)):
            r.call("4.setmode5", "SetModeAtUnit", mode=5, t=r.t)
            return
        if r.rchance("4.Range<aip(1)", 100, r.aip(1)):
            r.call("4.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        if r.rchance("4.Range<aip(3)", 100, r.aip(3)):
            r.call("4.t56", "T56", t=r.t, byte=3, flag=0)
            return
        r.call("4.delay", "Delay", n=r.aip(7))
        return
    if r.less("5.dist<aip(6)", r.dist, r.aip(6)):
        if r.rchance("5.Range<aip(5)", 100, r.aip(5)):
            r.call("5.setmode5", "SetModeAtUnit", mode=5, t=r.t)
            return
        if r.rchance("5.Range<aip(4)", 100, r.aip(4)):
            r.call("5.t56", "T56", t=r.t, byte=4, flag=0)
            return
        r.call("5.delay", "Delay", n=r.aip(7))
        return
    if r.rchance("6.Range<aip(4)", 100, r.aip(4)):
        r.call("6.t56", "T56", t=r.t, byte=3, flag=0)
        return
    r.call("7.walkstop", "WalkStop", t=r.t, n=4)


FACING4 = ((57, 63, 31), (0, 8, 31), (9, 24, 49), (25, 40, 0), (41, 56, 17))   # R63a's map of the low byte, as stated


def m_r63(r):
    """R63 GargoyleTrap. U's and t's positions are the AID line's x, y and t's x, y (the logger's words)."""
    if r.less("1.0<v14", 0, r.v[0x14]):
        r.call("1.idle", "Idle", n=r.v[0x14])
        r.store("set v14=0", 0x14, 0)
        return
    r.call("2.pathtarget", "SetPathTargetUnit", u=r.U, t=r.t)
    dx, dy = r.tx - r.x, r.ty - r.y
    if r.less("3.|dx|<|dy|", abs(dx), abs(dy)):
        px, py = r.x, r.ty
    else:
        px, py = r.tx, r.y
    d = r.call("4.dir", "UnitDirToPoint", u=r.U, x=px, y=py).eax & 0xFF
    r.vals.append(("4.dir", d))
    f = None
    for lo, hi, v in FACING4:
        if lo <= d <= hi:
            f = v
    r.call("4.facing", "PathSetFacing", facing=f)
    if ((r.br("5.|dx|<=5", abs(dx) <= 5) or r.br("5.|dy|<=5", abs(dy) <= 5)) and r.br("5.Skill1>=0", r.skill[0] >= 0)
            and r.less("5.dist<aip(1)", r.dist, r.aip(1)) and r.chance("5.chance(2)", 2)):
        use_skill(r, "5.useskill1", 1, r.t)
        r.store("set v14=aip(3)", 0x14, r.aip(3))
        return
    r.call("6.idle", "Idle", n=r.aip(4))


def m_r65(r):
    """R65 FetishShaman, the think."""
    n = 1
    if r.br("1.Skill1>=0", r.skill[0] >= 0):
        s = r.call("1.skillfind", "SkillFindByOwner", u=r.U, skill=r.skill[0], n=-1).eax
        if r.br("1.s!=0", s != 0):
            lv = s32(r.call("1.level", "GetSkillLevel", u=r.U, s=s, b=1).eax)
            r.vals.append(("1.lv", lv))
            if r.less("1.0<lv", 0, lv):
                n = lv
    if (r.br("2.Skill1>=0", r.skill[0] >= 0) and r.less("2.dist<n", r.dist, n)
            and not r.br("2.state12", r.call("2.hasstate", "HasState", u=r.U, state=12).eax)):
        tg, tt = (r.tid, r.ttype) if r.t else (-1, 6)
        r.call("2.helpblock", "HelpBlock", blk={0: {2: 1, 3: tg, 4: tt}})
        use_skill(r, "2.useskill1", 1, r.t)
        return
    if r.br("3.state12", r.call("3.hasstate", "HasState", u=r.U, state=12).eax):
        r.call("3.stateclear", "StateSet", u=r.U, state=12, v=0)
    ret = r.call("4.search", "UnitSearch", cb=0x005F99A0, kind=1,
                 blk={0: {0: 0, 1: 0x7FFFFFFF, 2: r.aip(5) * r.aip(5), 3: 0, 4: 0x7FFFFFFF, 5: 0, 6: r.aip(2)}})
    dead, deadd2 = ret.out(0, 0), s32(ret.out(0, 1))
    if (r.br("5.dead", dead != 0) and r.chance("5.chance(1)", 1)
            and r.br("5.targetok", r.call("5.targetok", "SkillTargetOk", skill=r.skill[2], u=dead, a=0, b=0).eax)):
        r.call("5.helpblock", "HelpBlock", blk={0: {2: 14, 4: 1}})
        r.vals.append(("5.deadD2:aip(3)", "%d:%d" % (deadd2, r.aip(3))))
        if r.less("5.aip(3)<deadD2", r.aip(3), deadd2):
            r.call("5.wandernear", "WanderNear", u=dead, r=10)
            return
        r.call("5.seqskill", "UseSeqSkill", skill=r.skill[2], t=dead, x=0, y=0)
        return
    if r.chance("6.chance(4)", 4):
        r.call("6.t56", "T56", t=r.t, byte=4, flag=0)
        return
    r.call("7.idle", "Idle", n=10)


def m_r68(r):
    """R68 VileMother."""
    pos = r.call("1.chainpos", "ClassChainPos", cls=r.cls if r.U else -1, a=0, b=0).eax
    child = r.call("2.chainstep", "ClassChainStep", cls=301 if r.ms2 > 301 else -1, pos=pos).eax
    if (r.less("3.v14<aip(1)", r.v[0x14], r.aip(1)) and r.br("3.align=0", r.call("3.align", "UnitAlignGet", u=r.U).eax == 0)
            and r.chance("3.chance(3)", 3)):
        ret = r.call("3.search", "UnitSearch", cb=0, kind=12, blk={0: {0: child, 1: 25, 2: 0}})
        if (r.less("3.count<aip(2)", s32(ret.out(0, 2)), r.aip(2))
                and r.br("3.spawned", r.call("3.spawn", "VileMotherSpawn", t=r.t, M=r.ms).eax)):
            r.store("set v14+=1", 0x14, r.v[0x14] + 1)
            return
    if r.br("4.melee", r.melee):
        if r.chance("4.chance(4)", 4):
            r.call("4.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        r.call("4.idle", "Idle", n=r.aip(7))
        return
    if r.less("5.v14<aip(1)", r.v[0x14], r.aip(1)) and not r.less("5.D100<aip(5)", r.d100(), r.aip(5), draw=True):
        if r.chance("5.chance(6)", 6):
            r.call("5.t56", "T56", t=r.t, byte=4, flag=0)
            return
        r.call("5.idle", "Idle", n=15)
        return
    r.call("6.walk", "Walk", t=r.t, flags=7)


def m_r69(r):
    """R69 VileDog."""
    if r.br("1.v14=0", r.v[0x14] == 0, val=r.v[0x14]):
        r.store("set v14=1", 0x14, 1)
        r.call("1.idle", "Idle", n=5)
        return
    if r.br("2.melee", r.melee):
        if r.chance("2.chance(1)", 1):
            r.call("2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        r.call("2.idle", "Idle", n=r.aip(2))
        return
    if r.chance("3.chance(3)", 3):
        r.call("3.walk", "Walk", t=r.t, flags=7)
        return
    r.call("4.idle", "Idle", n=10)


def m_r70(r):
    """R70 FingerMage. `p` (step 2) is read from MonStats words the log does not hold; it is used only as the
    override's parameter, which is therefore not compared."""
    life = s32(r.call("1.lifepct", "UnitLifePct", u=r.U).eax)
    if r.br("3.St3or19", r.call("3.st3or19", "St3or19", U=r.U).eax):
        r.store("set v14=0", 0x14, 0)
        if r.br("3.melee", r.melee):
            r.call("3.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        if r.br("3.Skill1>=0", r.skill[0] >= 0) and r.less("3.dist<aip(5)", r.dist, r.aip(5)):
            use_skill(r, "3.useskill1", 1, r.t)
            return
    if r.br("4.v14=1", r.v[0x14] == 1, val=r.v[0x14]):
        r.store("set v18+=1", 0x18, r.v[0x18] + 1)
        if (r.less("4.aip(3)<life", r.aip(3), life) or r.less("4.D100<25", r.d100(), 25, draw=True)
                or r.less("4.aip(6)<v18", r.aip(6), r.v[0x18])):
            r.store("set v14=0#2", 0x14, 0)
        elif r.less("4.dist<14", r.dist, 14):
            r.call("4.ovr", "Ovr", type=0, byte=0)
            r.call("4.stepaway", "StepAway", t=r.t, d=14, flag=0)
            return
        r.call("4.idle", "Idle", n=15)
        return
    if r.br("5.owner=0", r.call("5.owner", "MonsterOwner", U=r.U).eax == 0) and r.less("5.life<aip(4)", life, r.aip(4)):
        r.store("set v14=1", 0x14, 1); r.store("set v18=0", 0x18, 0)
        r.call("5.stepaway", "StepAway", t=r.t, d=9, flag=0)
        return
    if r.br("6.melee", r.melee):
        if r.chance("6.chance(1)", 1):
            r.call("6.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        if r.br("6.Skill1>=0", r.skill[0] >= 0) and r.rchance("6.Range<aip(2)", 100, r.aip(2)):
            use_skill(r, "6.useskill1", 1, r.t)
            return
        r.call("6.t56", "T56", t=r.t, byte=5, flag=0)
        return
    if not r.less("7.dist<aip(5)", r.dist, r.aip(5)):
        if r.less("7.dist<aip(7)", r.dist, r.aip(7)):
            r.call("7.walk", "Walk", t=r.t, flags=7)
            return
        r.call("7.idle", "Idle", n=15)
        return
    if r.br("8.Skill1>=0", r.skill[0] >= 0) and r.rchance("8.Range<aip(2)", 100, r.aip(2)):
        use_skill(r, "8.useskill1", 1, r.t)
        return
    if r.br("9.state84", r.call("9.hasstate", "HasState", u=r.t, state=84).eax):
        r.call("9.walk", "Walk", t=r.t, flags=0)
        return
    r.call("10.idle", "Idle", n=r.aip(8))


def arrow_kind(r):
    """`AiTrapArrowKind` (R78's block): the region word is not logged, so whether it is set, and its value, fork."""
    room = r.call("k.room", "UnitGetRoom", u=r.U).eax
    lvl = s32(r.call("k.level", "RoomGetLevelId", room=room).eax)
    if r.unknown("k.region<0"):
        if r.less("k.lvl<40", lvl, 40):
            return 0
        return r.rng(3)
    return 1 if r.unknown("k.region=1") else 0


def trap_arrow(r, axis):
    if r.less("1.dist<aip(1)", r.dist, r.aip(1)) or r.less("1.aip(2)<dist", r.aip(2), r.dist):
        r.call("1.idle", "Idle", n=40)
        return
    a = (r.x - r.tx) if axis == "x" else (r.y - r.ty)
    a = s32(a)
    if r.br("4.|a|<=2", abs(a) <= 2, val=abs(a) if abs(a) < 4 else None) and r.less("4.v14<T", r.v[0x14], r.T):
        r.store("set v14=T + aip(3)", 0x14, r.T + r.aip(3))
        if r.br("4.kind!=1", arrow_kind(r) != 1):
            r.call("4.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        if r.br("4.Skill1>=0", r.skill[0] >= 0):
            r.store("set v1c=T + aip(4)", 0x1C, r.T + r.aip(4))
            use_skill(r, "4.useskill1", 1, r.t)
            return
    r.call("5.idle", "Idle", n=30)


def m_r78(r):
    """R78 Trap-RightArrow. `UnitGetPos` (0x00620870) is not a boundary: the positions are the AID line's x, y and t's x, y."""
    trap_arrow(r, "x")


def m_r79(r):
    """R79 Trap-LeftArrow: row 78's code with y for x."""
    trap_arrow(r, "y")


def m_r78y(r):
    """Control: row 78's block with y for x. It must fail where the axes disagree."""
    trap_arrow(r, "y")


def m_r79x(r):
    """Control: row 79's block with x for y."""
    trap_arrow(r, "x")


def m_r95(r):
    """R95 PantherJavelin."""
    ret = r.call("1.findhostile", "FindHostile", pm=0, blk={0: {0: r.dist}})
    h, d = ret.eax, s32(ret.out(0))
    if r.less("2.d<8", d, 8) and r.chance("2.chance(4)", 4):
        r.call("2.stepaway", "StepAway", t=r.t, d=16, flag=1)
        return
    if r.less("3.aip(6)-6<d", r.aip(6) - 6, d) and r.chance("3.chance(1)", 1):
        r.call("3.wandernear", "WanderNear", u=r.t, r=4)
        return
    if r.br("4.h", h != 0) and r.less("4.d<aip(6)", d, r.aip(6)):
        if r.chance("4.chance(2)", 2):
            r.call("4.setmode4", "SetModeAtUnit", mode=4, t=h)
        else:
            r.call("4.idle", "Idle", n=r.aip(5))
        return
    ret = r.call("5.search", "UnitSearch", cb=0x005B0D00, kind=1, blk={0: {0: 0, 1: 0x7FFFFFFF}})
    unit, d2 = ret.out(0, 0), s32(ret.out(0, 1))
    if r.br("6.unit", unit != 0) and r.less("6.aip(3)<d2", r.aip(3), d2):
        r.call("6.walk", "Walk", t=unit, flags=7)
        return
    r.call("7.idle", "Idle", n=r.aip(5))


def m_r96(r):
    """R96 FetishBlowgun. The head record's words are the AID line's `head` (AiCtl+0x20's record at the think call)."""
    def clear():
        r.store("set v14=0", 0x14, 0); r.store("set v18=0", 0x18, 0)
    p = r.call("1.head", "ParamsHead", U=r.U).eax
    if r.br("1.p", p != 0):
        if r.head is None:
            raise Stop("no head record logged")
        kind, guid, typ = r.head[2], r.head[3], r.head[4]
        for k, lb in ((1, "k1"), (14, "k14")):
            if r.br("1.kind=%d" % k, kind == k, val=kind):
                u = r.call("1.%s.find" % lb, "GameFindUnit", type=typ, guid=guid).eax
                if r.br("1.%s.found" % lb, u != 0):
                    clear()
                    if k == 1:
                        r.call("1.k1.setmode4", "SetModeAtUnit", mode=4, t=u)
                    else:
                        r.call("1.k14.ovr", "Ovr", type=13, param=50, byte=0)
                        r.call("1.k14.walk", "Walk", t=u, flags=0)
                    r.call("1.%s.pop" % lb, "ParamsPop")
                    return
        r.call("1.pop", "ParamsPop")
    hunt = False
    if not r.br("2.melee", r.melee):
        if r.less("2.aip(1)<dist", r.aip(1), r.dist):
            r.call("2.ovr", "Ovr", type=0, param=50, byte=0)
            r.call("2.wandernear", "WanderNear", u=r.t, r=6)
            return
        hunt = not r.less("2.dist<6", r.dist, 6)
    if not hunt and r.chance("3.chance(2)", 2):
        r.store("set v14=2", 0x14, 2)
    h = r.call("4.findhostile", "FindHostile", pm=0).eax
    st = r.v[0x14]
    r.vals.append(("5.switch v14", st))
    if st == 0:
        r.store("set v18+=1", 0x18, r.v[0x18] + 1)
        if r.less("5.0.(r%3)+3<v18", r.step() % 3 + 3, r.v[0x18]):
            r.store("set v14=1", 0x14, 1); r.store("set v18=0#2", 0x18, 0)
        if r.br("5.0.h", h != 0):
            r.call("5.0.setmode4", "SetModeAtUnit", mode=4, t=h)
        else:
            r.call("5.0.t56", "T56", t=r.t, byte=4, flag=0)
    elif st == 1:
        clear()
        r.call("5.1.ovr", "Ovr", type=0, param=50, byte=0)
        if not r.br("5.1.t56", r.call("5.1.t56", "T56", t=r.t, byte=6, flag=1).eax):
            r.call("5.1.idle", "Idle", n=10)
    elif st == 2:
        if r.less("5.2.dist<13", r.dist, 13):
            r.call("5.2.ovr", "Ovr", type=2, param=50, byte=0)
            if not r.br("5.2.stepped", r.call("5.2.stepaway", "StepAway", t=r.t, d=14, flag=1).eax):
                r.call("5.2.setmode4", "SetModeAtUnit", mode=4, t=h)
                clear()
            return
        if r.rchance("5.2.Range<20", 100, 20) and r.br("5.2.t56", r.call("5.2.t56", "T56", t=r.t, byte=4, flag=1).eax):
            return
        clear()
        r.call("5.2.idle", "Idle", n=10)
    else:
        r.call("5.idle", "Idle", n=10)


def m_r114(r):
    """R114 ReanimatedHorde."""
    r.store("set c4|=0xE", "c4", r.c4 | 0xE)
    if r.br("2.melee", r.melee):
        if r.chance("2.chance(1)", 1):
            r.call("2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        else:
            r.call("2.idle", "Idle", n=r.aip(2))
        return
    if (r.br("3.Skill2>=0", r.skill[1] >= 0)
            and r.br("3.approach", r.call("3.approach", "ApproachPointTest", u=r.U, t=r.t).eax)
            and r.less("3.dist<aip(3)", r.dist, r.aip(3)) and r.less("3.5<dist", 5, r.dist)
            and r.rchance("3.Range<aip(4)", 100, r.aip(4))):
        use_skill(r, "3.useskill2", 2, r.t)
        return
    if r.chance("4.chance(5)", 5):
        r.call("4.walk", "Walk", t=r.t, flags=0)
        return
    if r.chance("5.chance(6)", 6):
        r.call("5.toward", "Toward", t=r.t, max=4, ring=0)
        return
    r.call("6.idle", "Idle", n=r.aip(7))


def m_r118(r):
    """R118 Succubus. `StatListFindFlag` (0x00625760) is not a boundary: its result forks."""
    if (not r.unknown("1.flag0x20") and r.less("1.dist<aip(4)", r.dist, r.aip(4)) and r.chance("1.chance(3)", 3)):
        if r.less("1.0<Skill1", 0, r.skill[0]) and not r.less(
                "1.tlife<aip(7)", s32(r.call("1.tlife", "UnitLifePct", u=r.t).eax), r.aip(7)):
            use_skill(r, "1.useskill1", 1, r.t)
            return
        raise Stop("1: the later curse tests are not modelled")
    if r.br("2.melee", r.melee):
        if r.chance("2.chance(1)", 1):
            r.call("2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        else:
            r.call("2.idle", "Idle", n=r.aip(5))
        return
    if r.less("3.0<Skill5", 0, r.skill[4]) and r.less("3.0<aip(8)", 0, r.aip(8)):
        raise Stop("3: the bolt arm is not modelled")
    if r.chance("4.chance(2)", 2):
        r.call("4.walk", "Walk", t=r.t, flags=0)
    else:
        r.call("4.idle", "Idle", n=r.aip(6))


def m_r124(r):
    """R124 FrozenHorror."""
    lv = 0
    if r.br("1.Skill1>=0", r.skill[0] >= 0):
        s = r.call("1.getskill", "GetUnitSkill", u=r.U, skill=r.skill[0]).eax
        if r.br("1.s!=0", s != 0):
            lv = s32(r.call("1.level", "GetSkillLevel", u=r.U, s=s, b=1).eax)
            r.vals.append(("1.lv", lv))
    if (r.br("2.Skill1>=0", r.skill[0] >= 0) and r.less("2.dist<max(lv,0)", r.dist, max(lv, 0))
            and r.chance("2.chance(3)", 3)
            and not r.br("2.state12", r.call("2.hasstate", "HasState", u=r.U, state=12).eax)):
        use_skill(r, "2.useskill1", 1, r.t)
        return
    if r.br("3.state12", r.call("3.hasstate", "HasState", u=r.U, state=12).eax):
        r.call("3.stateclear", "StateSet", u=r.U, state=12, v=0)
    if r.br("4.melee", r.melee):
        if r.chance("4.chance(1)", 1):
            r.call("4.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        else:
            r.call("4.idle", "Idle", n=r.aip(4))
        return
    if r.chance("5.chance(2)", 2):
        r.call("5.walkz", "WalkZ", t=r.t)
    else:
        r.call("5.idle", "Idle", n=r.aip(4))


def m_r130(r):
    """R130 DeathMauler."""
    if r.br("1.melee", r.melee):
        if r.chance("1.chance(1)", 1):
            r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        else:
            r.call("1.idle", "Idle", n=15)
        return
    if r.br("2.Skill1>=0", r.skill[0] >= 0) and r.less("2.dist<aip(3)", r.dist, r.aip(3)) and r.chance("2.chance(4)", 4):
        use_skill(r, "2.useskill1", 1, r.t)
        return
    if r.chance("3.chance(2)", 2):
        r.call("3.walk", "Walk", t=r.t, flags=0)
        return
    r.call("4.idle", "Idle", n=15)


def m_r99(r):
    """R99 TrappedSoul. Step 5's positions are the AID line's x, y and t's x, y."""
    r.store("set c4|=0x20000", "c4", r.c4 | 0x20000)
    if r.br("2.t=0", r.t == 0) or not r.less("2.dist<5", r.dist, 5):
        if r.br("2.v14!=0", r.v[0x14] != 0):
            r.call("2.setmode8", "SetModeAtUnit", mode=8, t=r.t)
        else:
            r.call("2.idle", "Idle", n=15)
        return
    if r.br("3.v14=0", r.v[0x14] == 0):
        r.store("set v14=1", 0x14, 1); r.store("set v18=T", 0x18, r.T)
        r.call("3.setmode9", "SetModeAtUnit", mode=9, t=r.t)
        return
    if not r.br("4.melee", r.melee) or not r.less("4.v18<T", r.v[0x18], r.T):
        r.call("4.setmode8", "SetModeAtUnit", mode=8, t=r.t)
        return
    ux, uy, tx, ty = u32(r.x), u32(r.y), u32(r.tx), u32(r.ty)
    if r.br("5.a", ux >= tx and uy <= ty):
        r.call("5.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        r.store("set v18=T + 35", 0x18, r.T + 35)
    elif r.br("5.b", ux > tx or uy < ty):
        r.call("5.setmode8", "SetModeAtUnit", mode=8, t=r.t)
        r.store("set v18=T + 5", 0x18, r.T + 5)
    else:
        r.call("5.setmode5", "SetModeAtUnit", mode=5, t=r.t)
        r.store("set v18=T + 35#2", 0x18, r.T + 35)


def m_r54(r):
    """R54 NpcStationary. `AiNearestPlayer`, `PlayerIsBusy`, `NpcInteractAny` and `AiDistUnits` are not boundaries."""
    if r.unknown("2.p"):
        if r.unknown("2.busy") or r.unknown("2.interact"):
            r.call("2.idle10", "Idle", n=10)
            return
        r.v[0x18] = None
        r.call("2.idle20", "Idle", n=20)
        return
    if r.cls in (251, 406) and r.unknown("3.special"):
        r.call("3.setmode0", "SetMode", mode=0, x=0, y=0)
        raise Stop("3: the class call after it is not modelled")
    r.call("4.idle", "Idle", n=20)


def m_s10(r):
    """S10, the think of states 10 and 17. The class-interact and mode tests read data the log does not hold."""
    if r.br("1.melee", r.melee) and r.unknown("1.interact") and r.unknown("1.mode4"):
        r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    if r.less("2.D100<20", r.d100(), 20, draw=True):
        r.call("2.ring3", "Ring", r=3)
    else:
        r.call("2.idle", "Idle", n=10)


def m_s11(r):
    """S11, the think (the init is not a think call). `p` is the override's parameter, not compared (MonStats words);
    `MonModeAllowed`, `MONSTATS_FlagTest` and `MonForcedTargetClear` are not boundaries."""
    if not r.br("1.state56", r.call("1.hasstate", "HasState", u=r.U, state=56).eax):
        r.call("1.init", "MonAiInit", ctl=r.ctlp, state=0)
        r.call("1.cancel", "CancelEvents", kind=2, z=0)
        r.call("1.queue", "QueueEvent", kind=2, frame=r.T + 1, a=0, b=0)
    lim = r.v[0x14] if r.v[0x14] != 0 else 30
    r.vals.append(("2.v14", r.v[0x14]))
    if r.less("2.lim<dist", lim, r.dist):
        r.call("2.idle", "Idle", n=10)
        return

    def away(lb, f):
        if r.unknown(lb + ".mode15"):
            return r.call(lb + ".awayxy", "StepAwayXY", t=r.t, n=30, f=f).eax
        return r.call(lb + ".away", "StepAway", t=r.t, d=30, flag=f).eax
    if r.br("4.v1C=0", r.v[0x1C] == 0):
        r.store("set v1c=1", 0x1C, 1)
        r.call("4.cancel", "CancelEvents", kind=2, z=0)
        r.call("4.ovr", "Ovr", type=2, byte=0)
        away("4", 0)
        return
    if r.br("5.melee", r.melee) and r.unknown("5.flag9") and r.unknown("5.mode4"):
        r.call("5.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    r.call("6.ovr", "Ovr", type=2, byte=0)
    if not r.br("6.away", away("6", 1)):
        r.call("6.ring6", "Ring", r=6)


def m_s12(r):
    """S12. `MonAiTargetOrIdle`'s search (`MonAiFindTarget`, logged from inside it) gives `u`; its no-target arm is
    README D4's, not this block's, and stops the decision."""
    tp = r.call("1.gettarget", "GetTargetUnit").eax
    town = False
    if not r.br("2.t'=0", tp == 0):
        room = r.call("2.room", "UnitGetRoom", u=tp).eax
        town = r.br("2.town", r.call("2.town", "RoomIsTown", room=room).eax)
    if tp == 0 or town:
        r.call("2.init", "MonAiInit", ctl=r.ctlp, state=0)
        r.call("2.cancel", "CancelEvents", kind=2, z=0)
        r.call("2.queue", "QueueEvent", kind=2, frame=r.T + 1, a=0, b=0)
        return
    if r.br("3.v14=0", r.v[0x14] == 0):
        r.store("set v14=1", 0x14, 1)
        r.call("3.walk13", "Walk13", t=tp, flags=7)
        return
    if r.br("4.melee", r.call("4.inmelee", "InMeleeRange", u=r.U, t=tp, z=0).eax):
        r.call("4.setmode4", "SetModeAtUnit", mode=4, t=tp)
        return
    ret = r.call("5.findtarget", "FindTarget", ctl=r.ctlp)
    u = ret.eax
    if u == 0:
        raise Stop("5: MonAiTargetOrIdle's no-target arm")
    if r.br("5.m", ret.out(2)):
        r.store("set v14=0", 0x14, 0)
        r.call("5.setmode4", "SetModeAtUnit", mode=4, t=u)
        return
    r.store("set v14=1#2", 0x14, 1)
    r.call("6.pathtarget", "SetPathTargetUnit", u=r.U, t=tp)
    r.call("6.walk13", "Walk13", t=tp, flags=7)


def m_r23(r, loop="point"):
    """R23 Vulture. `MoveToUnitDist` (0x005DE4E0) is not a boundary and draws nothing (machinery B12): its calls are not
    compared. `FreeNearFallback` (0x0064E7B0) is not a boundary: whether it finds a point, and the point, fork.
    The circling point's loop, "step x and y one away from U's position; if at it, both + 1", has two readings: "point"
    (the default) steps an equal axis by 0 and adds 1 to both only when the point is U's; "axis" steps an equal axis
    by + 1 (entry R23x, kept as the other reading)."""
    fly = r.v[0x14]
    far = r.less("1.144<distsq", 144, s32(r.call("1.distsq", "UnitDistSq", u=r.U, t=r.t).eax))
    rt = r.call("1.room-t", "UnitGetRoom", u=r.t).eax
    ru = r.call("1.room-u", "UnitGetRoom", u=r.U).eax
    if r.br("2.rooms-differ", rt != ru) and far:
        if r.less("2.fly<1", fly, 1):
            r.call("2.toward", "Toward", t=r.t, max=9, ring=0)
            return
        if r.br("2.land", r.call("2.land", "Land").eax):
            r.c4 = None                                  # MoveToUnitDist(U, 9, 2, 3): its command sets Unit+0xC4
            r.call("2.delay12", "Delay", n=12)
            r.store("set v14=-1", 0x14, -1)
            return
    if (r.br("3.fly=0", fly == 0, val=fly) and r.br("3.owner=0", r.call("3.owner", "MonsterOwner", U=r.U).eax == 0)
            and far and r.rchance("3.Range<60", 100, 60)):
        r.call("3.takeoff", "TakeOff")
        r.store("set v14=24+Pow2(8)", 0x14, 24 + r.call("3.pow2", "RangePow2", seedp=r.U + 0x20, n=8).eax)
        r.c4 = None                                      # MoveToUnitDist(t, 8, 8, 8)
        r.call("3.delay12", "Delay", n=12)
        return
    ret = r.call("4.search", "UnitSearch", cb=0x005F30F0, kind=1, blk={0: {0: 0, 1: 121, 2: r.aip(3)}})
    found = ret.out(0, 0)
    land = False
    if r.less("5.1<fly", 1, fly):
        if r.br("5.found", found != 0) or (r.less("5.dist<6", r.dist, 6) and r.rchance("5.Range<15", 100, 15)):
            r.store("set v14=1", 0x14, 1)
            land = True
        else:
            r.call("5.takeoff", "TakeOff")
            new = r.br("5.v18=0", r.v[0x18] == 0) or r.br("5.v1C=0", r.v[0x1C] == 0)
            if not new:
                new = r.less("5.pathdist<2", s32(r.call("5.pathdist", "PathDist", u=r.U, x=r.v[0x18], y=r.v[0x1C]).eax), 2)
            if new:
                c = fly + 8
                x = r.tx - c + r.rng(2 * c)
                y = r.ty - c + r.rng(2 * c)
                rad = min(max(2 * c, 12), 36)
                n = 0
                while r.less("5.loop", s32(r.call("5.loopdist", "PathDist", u=r.U, x=x, y=y).eax), rad):
                    n += 1
                    if n > 64:
                        raise Stop("5: the loop runs past 64 steps")
                    if loop == "axis":
                        x = x + 1 if x >= r.x else x - 1
                        y = y + 1 if y >= r.y else y - 1
                    else:
                        if (x, y) == (r.x, r.y):
                            x, y = x + 1, y + 1
                        else:
                            x = x + (x > r.x) - (x < r.x)
                            y = y + (y > r.y) - (y < r.y)
                r.store("set v18=x", 0x18, x); r.store("set v1c=y", 0x1C, y)
                r.call("5.ovr1", "Ovr", type=1, param=0, byte=0)
                r.call("5.movepoint", "MoveToPoint", x=x, y=y, n=8)
                r.call("5.delay12", "Delay", n=12)
                r.store("set v14-=1", 0x14, r.v[0x14] - 1)
                return
            r.call("5.fb-room-t", "UnitGetRoom", u=r.t)
            if r.unknown("5.fallback"):
                r.v[0x18] = r.v[0x1C] = None
            r.store("set v14-=1#2", 0x14, r.v[0x14] - 1)
            r.call("5.ovr7", "Ovr", type=7, param=0, byte=0)
            r.call("5.movepoint-fb", "MoveToPoint", x=r.v[0x18], y=r.v[0x1C], n=8)
            r.call("5.delay12-fb", "Delay", n=12)
            return
    if land or r.br("6.fly=1", fly == 1):
        if r.br("6.land", r.call("6.land", "Land").eax):
            r.c4 = None                                  # MoveToUnitDist(t, 9, 2, 3)
            r.call("6.delay12", "Delay", n=12)
            r.store("set v14=-1#2", 0x14, -1)
            return
        r.store("set v14=8", 0x14, 8)
        r.call("6.delay12-noroom", "Delay", n=12)
    if r.br("7.melee", r.melee):
        if r.chance("7.chance(1)", 1):
            r.call("7.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        r.call("7.delay", "Delay", n=r.aip(2))
        return
    if r.br("8.fly!=-1", fly != -1) and not r.rchance("8.Range<aip(5)", 100, r.aip(5)):
        r.call("8.delay", "Delay", n=r.aip(2))
        return
    if r.rchance("9.Range<aip(4)", 100, r.aip(4)):
        r.call("9.t56", "T56", t=r.t, byte=6, flag=0)
    else:
        r.call("9.toward", "Toward", t=r.t, max=9, ring=0)
    r.store("set v14=0", 0x14, 0)
    r.call("10.delay12", "Delay", n=12)


def m_r23x(r):
    """R23 with the loop's "axis" reading (see m_r23)."""
    m_r23(r, loop="axis")


MODELS = {
    "R3": (0x005EFE20, m_r3, "catalogue 17, 18"),
    "R4": (0x005EFF50, m_r4, "catalogue 20, 21"),
    "R5": (0x005F00E0, m_r5, "catalogue 23, 24"),
    "R12": (0x005F12A0, m_r12, "catalogue 44, 45"),
    "R15": (0x005F1800, m_r15, "catalogue 49, 50, 51"),
    "R19": (0x005F2460, m_r12, "catalogue 68"),
    "R23": (0x005F3170, m_r23, "catalogue 70, 71"),
    "R23x": (0x005F3170, m_r23x, "catalogue 70, 71: the loop's other reading"),
    "R26": (0x005F4510, m_r26, "catalogue 93, 94"),
    "R43": (0x005F6650, m_r43, "catalogue 113, 114, 115"),
    "R52": (0x005F8260, m_r52, "catalogue 138, 139, 140"),
    "R54": (0x005E73A0, m_r54, "catalogue 466, 467"),
    "R63": (0x005F9490, m_r63, "catalogue 147, 148"),
    "R65": (0x005F9A80, m_r65, "catalogue 150, 151, 152, 153, 156"),
    "R68": (0x005FA010, m_r68, "catalogue 161, 162, 163"),
    "R69": (0x005FA280, m_r69, "catalogue 165"),
    "R70": (0x005FA380, m_r70, "catalogue 167, 168"),
    "R78": (0x005FB6C0, m_r78, "catalogue 193, 195"),
    "R79": (0x005FB7E0, m_r79, "catalogue 198, 199"),
    "R78y": (0x005FB6C0, m_r78y, "control for 193, 195: y for x"),
    "R79x": (0x005FB7E0, m_r79x, "control for 198, 199: x for y"),
    "R95": (0x005E1080, m_r95, "catalogue 320, 321"),
    "R96": (0x005E1250, m_r96, "catalogue 323, 324"),
    "R99": (0x005E9F10, m_r99, "catalogue 485, 486"),
    "R100": (0x005E7F50, m_r1, "catalogue 489"),
    "R114": (0x005E1540, m_r114, "catalogue 335, 336"),
    "R118": (0x005E1E00, m_r118, "catalogue 347, 348"),
    "R124": (0x005E3530, m_r124, "catalogue 369, 370"),
    "R130": (0x005EE260, m_r130, "catalogue 388"),
    "S10": (0x005E8020, m_s10, "catalogue 498"),
    "S11": (0x005E8140, m_s11, "catalogue 500, 501"),
    "S12": (0x005E8340, m_s12, "catalogue 504, 505"),
}


# ------------------------------------------------------------------------------------------------------------ report
def run_check(paths, names, out):
    decs = defaultdict(list)
    ths = defaultdict(list)
    for n in names:
        ths[MODELS[n][0]].append(n)
    nxt = {}                  # id(decision) -> the same unit's next logged decision in the same log
    for p in paths:
        last = {}
        for d in ai.parse(p)["dec"]:
            key = (d["aid"]["u"], d["aid"]["id"])
            if key in last:
                nxt[id(last[key])] = d
            last[key] = d
            if d.get("trunc"):
                continue
            for n in ths.get(d["aid"]["th"], ()):
                decs[n].append(d)
    lines = []
    for n in names:
        th, model, rows = MODELS[n]
        ds = decs[n]
        res = [(d, check(model, d)) for d in ds]
        cnt = Counter(o.status for _, o in res)
        free = [(d, o) for d, o in res if o.status == "ok" and o.forks == 0]
        forked = [(d, o) for d, o in res if o.status == "ok" and o.forks]
        calls = sum(len(o.run.labels) for _, o in free)
        past = sum(max(0, len(o.run.labels) - 1) for _, o in free)
        lines.append("ENTRY %s think %08x (inventory %s): decisions %d, ok %d (fork-free %d, forked %d), mismatch %d, stop %d"
                     % (n, th, rows, len(ds), cnt["ok"], len(free), len(forked), cnt["mismatch"], cnt["stop"]))
        lines.append("  CALLS fork-free: %d compared, %d past the first" % (calls, past))
        for d, o in res:
            if o.status == "mismatch":
                lines.append("  MISMATCH %s n=%d: %s" % (os.path.basename(d["log"]), d["aid"]["n"], o.why))
        why = Counter(o.why.split(":")[-1].strip() for _, o in res if o.status == "stop")
        for w, k in sorted(why.items()):
            lines.append("  STOP %d %s" % (k, w))
        sites = defaultdict(Counter)
        arms = Counter()
        ran = Counter()
        for _, o in free:
            for lb, ra in o.run.labels:
                sites[lb][ra] += 1
            for b, v in set(o.run.arms):
                arms[(b, v)] += 1
            for b in {b for b, _ in o.run.arms}:
                ran[b] += 1
        # the control words at return against the same unit's next decision (same think), outside the decision
        nc = Counter()
        for d, o in free:
            d2 = nxt.get(id(d))
            if d2 is None or d2["aid"]["th"] != th:
                continue
            cb = bytes.fromhex(d2["aid"]["ctl"])
            w0 = bytes.fromhex(d["aid"]["ctl"])
            for off in (0x14, 0x18, 0x1C):
                mv = o.run.v[off]
                if mv is None:
                    continue
                got = int.from_bytes(cb[off:off + 4], "little")
                was = int.from_bytes(w0[off:off + 4], "little")
                tag = "v%x" % off
                nc[(tag, "n")] += 1
                nc[(tag, "eq")] += u32(mv) == got
                nc[(tag, "moved")] += u32(mv) != was
                nc[(tag, "moved-eq")] += u32(mv) != was and u32(mv) == got
        for tag in ("v14", "v18", "v1c"):
            if nc[(tag, "n")]:
                lines.append("  NEXT %s: equal %d of %d; the model moved it in %d, equal in %d of those" % (
                    tag, nc[(tag, "eq")], nc[(tag, "n")], nc[(tag, "moved")], nc[(tag, "moved-eq")]))
        for lb in sorted(sites):
            lines.append("  SITE %s %s" % (lb, " ".join("%08x:%d" % kv for kv in sorted(sites[lb].items()))))
        for b in sorted(ran):
            lines.append("  ARM %s true %d false %d" % (b, arms[(b, True)], arms[(b, False)]))
        edges, vals = Counter(), defaultdict(Counter)
        for _, o in free:
            for b in set(o.run.edges):
                edges[b] += 1
            for b, v in o.run.vals:
                vals[b][v] += 1
        for b in sorted(edges):
            lines.append("  EDGE %s %d" % (b, edges[b]))
        for b in sorted(vals):
            lines.append("  VALS %s %s" % (b, " ".join("%s:%d" % kv for kv in sorted(vals[b].items())[:12])))
        for b in sorted(ran):
            sub = [d for d, o in free if any(x == b for x, _ in o.run.arms)]
            st = Counter()
            for d in sub:
                o2 = check(model, d, flip=b)
                st[o2.status] += 1
                if o2.status == "ok" and next_diff(o2.run, nxt.get(id(d))):
                    st["next"] += 1
            lines.append("  FLIP %s fail %d of %d (in the decision %d, at the next decision %d; stop %d)" % (
                b, st["mismatch"] + st["next"], len(sub), st["mismatch"], st["next"], st["stop"]))
        for c in ("le", "lecmp", "d0") + (("sdiv",) if n == "R43" else ()):
            st = Counter(check(model, d, ctl=c).status for d, _ in free)
            lines.append("  CONTROL %s fail %d of %d (stop %d)" % (c, st["mismatch"], len(free), st["stop"]))
    txt = "\n".join(lines) + "\n"
    if out:
        with open(out, "w") as fh:
            fh.write(txt)
    sys.stdout.write(txt)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("logs", nargs="*")
    c.add_argument("--logs", dest="loglist")
    c.add_argument("--rows")
    c.add_argument("--out")
    sub.add_parser("list")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for n, (th, _, rows) in MODELS.items():
            print("%s %08x %s" % (n, th, rows))
        return 0
    paths = list(a.logs)
    if a.loglist:
        with open(a.loglist) as fh:
            paths += [x.strip() for x in fh if x.strip()]
    names = a.rows.split(",") if a.rows else list(MODELS)
    run_check(paths, names, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
