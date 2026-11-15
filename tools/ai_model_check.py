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

Revision 2 (plan 0066 S1c, `lane/n66d`): R44 (Duriel) and S13 (state row 13) added, with their calls in `CONV`; S13's path
count is a given word per unit read from its logged fires (`S13_COUNT`, as tools/ai_s13_check.py takes it). The entries of
revision 1 are unchanged: `--rows` with S1b's 32 names reproduces `sweep2-s1b/model-check.txt` byte for byte (from
revision 3, without the SEP lines: `regress`).
tools/ai_first_check.py (S1d) runs these models to their first call only.

Revision 3 (plan 0069 Phase 1a, `lane/n69a`): CONV gains the boundaries the tour's thinks call (positional names, from
tools/ai_tour.py's caller read); each entry ends with a `SEP` line, its number of distinct predicted outcomes (ADR-0028
item 7); `regress` reruns S1b's check over its 38 logs and compares it, without the SEP lines, with the kept
`sweep2-s1b/model-check.txt` (exit 1 on any difference):

    python3 -I tools/ai_model_check.py regress [--base workspace/logs/ai/sweep2-s1b] [--logs-dir workspace/logs/ai] [--out F]

Revision 4 (plan 0069 Phase 1b, `lane/n69b`): the 29 models of batches H1a (R8, R16, R142, R17, R18, R24, R25, R27, R72,
R74), H1b (R115, R116, R117, S15, R119, R120, R122, R123, S16, R126, R129, R136, R137) and H1d (S5, S6, R41, R42, R58,
R60), grouped per entry above `MODELS`. Engine additions, used only by them: a call's ECX or EDX given by the model when
the block calls on another unit (`_ecx`, `_edx`); `Run.opaque` for a command that is neither a boundary nor executed and
may draw (the next call takes the logged seed); `SELECT`, which splits a shared think between its table row and its state
row by the AID line's state; `check --no-select`. Row 122's and state 16's fixed records 492..495 are read from the game's
monstats.bin (`imp_rec`), row 25's tables from the catalogue's text (`wisp_tables`). The entries of revisions 1 to 3 are
unchanged (`regress`).

Revision 5 (plan 0069 Phase 1c, `lane/n69c`): the 31 models of batches H1c (R38, R45, R66, R77, R80, R92, R50, R53, R55,
R59, R85, R94, R128), H1g (R7, R11, R14, R33, R36, R39, R40, R49, R56, R57, R71, R93, R98, and the Reimplementation notes
row as `NOTES` on `m_r7`) and H1h (R1 as `m_r1w`, R10, R32, R48, R73), grouped per entry above `MODELS`. Engine additions,
used only by them: `r7`/`known`, a rev 7 word of the decision (`dec["r7"]`, which Phase 2's tools/ai.py fills) or else a
fork, so the H1h models run on rev 6 logs and take their word from a rev 7 one; `store_unknown`, a store of a word the
log does not hold (compared only when flipped); `unit_set_event`, `UnitSetEvent`'s `Unit+0xC4 |= 0x400` (0x005533B9);
`sweep_table` and `step_xy`, R94's `SWEEP` table and `STEP` rule read from the catalogue's text. The entries of revisions
1 to 4 are unchanged (`regress`; the 29 revision 4 entries' check over the 38 logs is byte-identical to Phase 1b's).
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
    # plan 0066 S1c (`lane/n66d`): R44's and S13's calls; the words tools/ai_s13_check.py compares for S13's (r72 record)
    "GetRightSkill": (0x006201D0, None, None, ("u",)),
    "UnitSkillAdd": (0x0056DEB0, None, None, ()),
    "PlayerSetSkill": (0x005701B0, None, None, ()),
    "ParamsFind": (0x0058EEF0, "U", "kind", ("z",)),
    "LogicRegionId": (0x0061B130, None, None, ("room", "x", "y")),
    "PathOvrSet": (0x005A6260, None, "a", ("b", "c")),
    "RunToPoint": (0x005DEDE0, "G", "U", ("x", "y")),
    # plan 0069 Phase 1a (`lane/n69a`): the boundaries the tour's thinks call that CONV lacked (`tools/ai_tour.py audit`,
    # CONV-MISSING). Source: the caller read of `tools/ai_tour.py conv` (ECX or EDX written, and the pushes, between the
    # previous call and each call site in the logger's windows; a register set at most sites is an argument), which agrees
    # with 64 of the 68 entries above (workspace/logs/n69a/conv.txt). The names are positional: "c" ECX, "d" EDX, "s1".. the
    # stack words in push order reversed (the first argument first), at most the six the AIB line logs; the push count is an
    # upper bound where the caller saves a register on the stack. A model that names a word here and mismatches on it
    # corrects the entry with its own source (plan 0069 § How the S1b checker is reused, gap 2).
    "RoomAtSubtile": (0x00463740, "c", "d", ()),
    "MissileRec": (0x0046ACE0, "c", None, ()),
    "SkillGetParam5": (0x004E6C70, "c", None, ()),
    "UnitEventFirstFrame": (0x005415A0, "c", "d", ("s1",)),
    "SpawnPosPick": (0x0054DC40, "c", "d", ("s1", "s2", "s3", "s4", "s5")),
    "UnitGetOwner": (0x00552FD0, "c", "d", ()),
    "UnitGetGame": (0x00554010, "c", None, ()),
    "UnitIsDead": (0x005541B0, "c", None, ()),
    "UnitsHostile": (0x00554200, "c", "d", ("s1",)),
    "UnitTeleport": (0x00554EA0, "c", "d", ("s1",)),
    "UnitKilled": (0x0057CCB0, "c", "d", ("s1", "s2")),
    "AiParamsPush": (0x0058EF40, "c", "d", ("s1",)),
    "A2Q5_BossSeen": (0x0059C330, None, "d", ("s1", "s2", "s3", "s4")),
    "SpawnAtPos": (0x005B2F20, "c", "d", ("s1", "s2", "s3", "s4", "s5", "s6")),
    "A4Q1_IzualSeen": (0x005B4390, "c", "d", ()),
    "AiDistUnits": (0x005DC380, "c", "d", ()),
    "AiDistToPointSized": (0x005DC480, "c", "d", ("s1",)),
    "AiLineClear": (0x005DD290, "c", "d", ()),
    "MonAiRunNearUnit": (0x005DF680, "c", "d", ("s1", "s2")),
    "AiImpSetHost": (0x005E17E0, "c", "d", ()),
    "AiMephistoPickTarget": (0x005F77C0, "c", "d", ("s1", "s2")),
    "UnitSetOverlayStat": (0x00621E40, None, None, ("s1", "s2", "s3", "s4", "s5")),
    "UnitGetPlayerData": (0x006221A0, "c", None, ("s1",)),
    "UnitLineBlocked": (0x00622AA0, None, None, ("s1", "s2", "s3")),
    "StatsGetUnitStat": (0x00625480, None, None, ("s1", "s2", "s3")),
    "UnitGetMaxHp": (0x00625D10, None, None, ("s1",)),
    "UnitGetMaxMana": (0x00625D60, None, None, ("s1",)),
    "Dir64To8": (0x0063E7A0, None, None, ("s1",)),
    "MonIsDeathMode": (0x0063EA40, None, None, ("s1",)),
    "LevelClassVariant": (0x0063EC70, None, None, ("s1", "s2")),
    "SpawnClassByBase": (0x0063EFA0, "c", "d", ("s1", "s2", "s3", "s4", "s5", "s6")),
    "UnitEdgeDistance": (0x006416D0, None, None, ("s1", "s2")),
    "PathSetTargetPoint": (0x00648AD0, "c", "d", ("s1", "s2", "s3")),
    "PathSetStopDist": (0x00649070, "c", "d", ("s1", "s2")),
    "CollCellTestAt": (0x0064CB30, None, None, ("s1",)),
}
# the entries revision 3 added (their source is the caller read itself, so tools/ai_tour.py conv checks its method on the others)
CONV_REV3 = ("RoomAtSubtile", "MissileRec", "SkillGetParam5", "UnitEventFirstFrame", "SpawnPosPick", "UnitGetOwner", "UnitGetGame", "UnitIsDead", "UnitsHostile", "UnitTeleport", "UnitKilled", "AiParamsPush", "A2Q5_BossSeen", "SpawnAtPos", "A4Q1_IzualSeen", "AiDistUnits", "AiDistToPointSized", "AiLineClear", "MonAiRunNearUnit", "AiImpSetHost", "AiMephistoPickTarget", "UnitSetOverlayStat", "UnitGetPlayerData", "UnitLineBlocked", "StatsGetUnitStat", "UnitGetMaxHp", "UnitGetMaxMana", "Dir64To8", "MonIsDeathMode", "LevelClassVariant", "SpawnClassByBase", "UnitEdgeDistance", "PathSetTargetPoint", "PathSetStopDist", "CollCellTestAt")


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
        if self.seed is None:
            raise Stop("a draw after an opaque call (the seed is unknown)")
        self.seed = ai.step(self.seed)
        return self.seed[0]

    def opaque(self, name):
        """Revision 4: a call the block makes of a function that is neither a boundary nor executed, and that may move the
        unit's seed (a command such as `MonAiWalkToPointCmd`). The seed is unknown from here: the next compared call does not
        compare it and takes the logged one (its AIR line), and a block that returns before any call skips the exit seed. A
        draw before that resync stops the decision. Used only by the revision 4 models."""
        self.vals.append(("opaque", name))
        self.seed = None

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

        def want(spec, reg=None):
            if spec is None:
                return SKIP
            if spec in ("G", "U") and "_" + reg in kw:      # revision 4: a call on another unit or game word
                return kw["_" + reg]
            if spec == "G":
                return self.G
            if spec == "U":
                return self.U
            return kw.get(spec, SKIP)
        for reg, spec in (("ecx", ecx), ("edx", edx)):
            v = want(spec, reg)
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
        if self.seed is not None and "%08x:%08x" % self.seed != b["s"]:
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
        if self.seed is not None and "%08x:%08x" % self.seed != d["aix"]["s"]:
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


# ---- plan 0066 batch S1c (`lane/n66d`): R44 and S13, transcribed from the spec blocks at b5999f5e like the rest.

def m_r44(r):
    """R44 Duriel. Step 1's grant is modelled as its two logged boundary calls (`UnitSkillAdd`, `PlayerSetSkill`, both in
    the logger's BND), their words not compared: no log reaches them."""
    if r.br("1.Skill4>=0", r.skill[3] >= 0, val=r.skill[3]):
        rs = r.call("1.rightskill", "GetRightSkill", u=r.U).eax
        if r.br("1.rightskill=0", rs == 0):
            r.call("1.skilladd", "UnitSkillAdd")
            r.call("1.setskill", "PlayerSetSkill")
    if not r.br("2.melee", r.melee):
        if r.br("2.Skill1>=0", r.skill[0] >= 0) and r.chance("2.chance(5)", 5):
            use_skill(r, "2.useskill1", 1, r.t)
            return
        r.call("2.ovr", "Ovr", type=13, param=0, byte=0)
        r.call("2.walk", "Walk", t=r.t, flags=7)
        return
    if r.br("3.Skill3>=0", r.skill[2] >= 0) and r.chance("3.chance(2)", 2):
        use_skill(r, "3.useskill3", 3, r.t)
        return
    if r.br("4.Skill2>=0", r.skill[1] >= 0) and r.chance("4.chance(3)", 3):
        use_skill(r, "4.useskill2", 2, r.t)
        return
    if r.chance("5.chance(4)", 4):
        r.call("5.setmode5", "SetModeAtUnit", mode=5, t=r.t)
        return
    r.call("6.setmode4", "SetModeAtUnit", mode=4, t=r.t)


# S13's path list (AiCtl +0x38) is not logged. Its count is a given word per (log, unit): the highest index fired + 1, read
# from the logged fires (the `v14` word of each `MonAiUseSkill` call the think makes), as tools/ai_s13_check.py takes it
# (README H1b's given words). `v14 < count` can then fail only below that index. Filled by run_check before S13 runs.
S13_COUNT = {}


def s13_counts(decs):
    for d in decs:
        for b in R.top_level(d):
            if b["fn"] == CONV["UseSkill"][0]:
                key = (d["log"], d["aid"]["u"])
                S13_COUNT[key] = max(S13_COUNT.get(key, 0), s32(b["c"][0]) + 1)


def s13_step(r, lb):
    """AiPathSkillStep: True when it fired. The point's x, y are not compared (the list is not logged)."""
    cnt = S13_COUNT.get((r.dec["log"], r.U))
    if cnt is None:
        lt = r.unknown(lb + ".v14<count")
    else:
        lt = r.less(lb + ".v14<count", r.v[0x14], cnt)
    if lt:
        if not r.br(lb + ".skill1-ok", r.skill[0] >= 0, val=r.skill[0]):
            return False
        r.call(lb + ".fire", "UseSkill", mode=4, skill=r.skill[0], t=0)
        r.store(lb + ".set v14+=1", 0x14, r.v[0x14] + 1)
        r.store(lb + ".set v18=T", 0x18, r.T)
        return True
    if r.br(lb + ".|T-v18|>700", abs(s32(r.T - r.v[0x18])) > 700, val=abs(s32(r.T - r.v[0x18]))):
        r.store(lb + ".set v14=0", 0x14, 0)
    return False


def s13_runhome(r, lb, hx, hy):
    """RunHome: True when the run was accepted (the event ends)."""
    r.call(lb + ".pathset", "PathOvrSet", a=1, b=0, c=0)
    ok = r.call(lb + ".runpt", "RunToPoint", x=hx, y=hy).eax
    if r.br(lb + ".run-ok", ok != 0):
        return True
    r.call(lb + ".cancel", "CancelEvents", kind=2, z=0)
    return False


def m_s13(r):
    """S13, state row 13 (the Countess). M is the AiCtx's MonStats word (ctx[7]); home is the record the find returns,
    whose words are the AID line's `head` when the returned pointer is the logged `hp`."""
    if not r.br("1.M!=0", r.aid["ctx"][7] != 0):
        return
    room = r.call("1.room", "UnitGetRoom", u=r.U).eax
    if not r.br("1.room!=0", room != 0):
        return
    hp = r.call("2.home", "ParamsFind", kind=10, z=0).eax
    if not r.br("2.home!=0", hp != 0):
        raise Stop("2: the push is not reached")
    if hp != r.aid["hp"] or r.head is None:
        raise Stop("2: the home record is not the logged head")
    hx, hy = r.head[3], r.head[4]
    if not r.br("2.words!=0", hx != 0 and hy != 0):
        raise Stop("2: the refill is not reached")
    rh = r.call("3.region-home", "LogicRegionId", room=room, x=hx, y=hy).eax
    ru = r.call("3.region-u", "LogicRegionId", room=room, x=r.x, y=r.y).eax
    if r.br("3.differ", rh != ru) and s13_runhome(r, "3", hx, hy):
        return
    rt = r.call("4.region-t", "LogicRegionId", room=room, x=r.tx, y=r.ty).eax
    if r.br("4.differ", rt != rh):
        if r.br("4.at-home", r.x == hx and r.y == hy):
            if r.less("4.dist<25", r.dist, 25) and s13_step(r, "4.step"):
                return
            r.call("4.idle10", "Idle", n=10)
            return
        if s13_runhome(r, "4", hx, hy):
            return
    hd = r.call("5.homedist", "PathDist", u=r.U, x=hx, y=hy).eax
    if r.br("5.homedist>40", u32(hd) > 40, val=u32(hd)) and s13_runhome(r, "5", hx, hy):
        return
    if s13_step(r, "6.step"):
        return
    v = r.rng(100)
    if r.br("8.melee", r.melee):
        if r.less("8.r<aip(3)+10", v, r.aip(3) + 10, draw=True):
            r.call("8.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        else:
            r.call("8.idle", "Idle", n=r.aip(2))
    elif r.less("8.r<aip(1)", v, r.aip(1), draw=True):
        r.call("8.ovr", "Ovr", type=0, param=100, byte=0)
        r.call("8.run", "RunToUnit", t=r.t)
    else:
        r.call("8.idle#2", "Idle", n=r.aip(2))


# ---- plan 0069 Phase 1b (`lane/n69b`), revision 4: the models of batches H1a, H1b and H1d, transcribed from the catalogue
# blocks at b5999f5e (the catalogue is unchanged from there to 7b7f20e9) and, where a block names a table or a callback by
# address only, from its finding (named per model). Grouped per entry; Phase 1c adds its own after these.

def s8(v):
    v &= 0xFF
    return v - 0x100 if v & 0x80 else v


def tmode(r):
    """The target's mode, the AID line's `t[3]` (None without a target)."""
    return (r.aid.get("t") or [None] * 7)[3]


def diff(r):
    """`d` (Game+0x6D), the Normal column under the `d0` control as `aip`."""
    return 0 if r.ctl == "d0" else r.aid["diff"]


# ---- H1a R8 SandRaider (catalogue 263; AiNearAllyCb 0x005F06B0, ai/0002)
def m_r8(r):
    """R8 SandRaider. `aidel[d]` is logged for Normal only (AID `ad[0]`, MonStats+0x4F): step 3's wait is compared in
    Normal and not compared in the other two."""
    one = r.aip(6) == 1
    if r.br("1.v14=0", r.v[0x14] == 0, val=r.v[0x14]):
        r.call("1.state90", "StateSet", u=r.U, state=90, v=0)
        r.call("1.state91", "StateSet", u=r.U, state=91, v=0)
        r.store("set v18=0", 0x18, 0)
    r.store("set v14+=1", 0x14, r.v[0x14] + 1)
    n = r.v[0x14]
    if r.br("3.n=aip(5)", n == r.aip(5)):
        r.call("3.overlay", "UnitSetOverlayStat", s1=r.U, s2=150 if r.br("3.aip(6)=1", one) else 46, s3=0)
        wait = r.aid["ad"][0] + 1 if r.aid["diff"] == 0 and r.aid.get("ad") else None
        r.call("3.idle", "Idle", n=wait)
        return
    if r.less("4.aip(5)<n", r.aip(5), n):
        r.call("4.state", "StateSet", u=r.U, state=90 if r.br("4.aip(6)=1", one) else 91, v=1)
        r.store("set v18=1", 0x18, 1)
    if r.less("5.v1C<7", r.v[0x1C], 7):
        life = s32(r.call("5.lifepct", "LifePct", U=r.U).eax)
        if r.less("5.life<aip(1)", life, r.aip(1)):
            ret = r.call("5.search", "UnitSearch", cb=0x005F06B0, kind=1, blk={0: {0: 0, 1: 0x7FFFFFFF}})
            best = ret.out(0, 0)
            if r.br("5.best", best != 0):
                r.call("5.walk", "Walk", t=best, flags=0)
                return
            r.store("set v1c+=1", 0x1C, r.v[0x1C] + 1)
    if r.less("6.4<dist", 4, r.dist) and r.br("6.v18=0", r.v[0x18] == 0) and r.chance("6.chance(2)", 2):
        r.call("6.t56", "T56", t=r.t, byte=0, flag=0)
        return
    if not r.br("7.melee", r.melee):
        if r.br("7.v18!=0", r.v[0x18] != 0) or r.chance("7.chance(4)", 4):
            r.call("7.walk", "Walk", t=r.t, flags=0)
            return
    else:
        if r.br("8.v18=1", r.v[0x18] == 1) and r.br("8.Skill1>=0", r.skill[0] >= 0):
            use_skill(r, "8.useskill1", 1, r.t)
            r.store("set v14=0", 0x14, 0); r.store("set v18=0#2", 0x18, 0)
            return
        if r.chance("9.chance(3)", 3):
            a1 = not r.less("9.Range<aip(7)", r.rng(100), r.aip(7), draw=True)
            r.call("9.setmode", "SetModeAtUnit", mode=4 if a1 else 5, t=r.t)
            return
    k = 6 if r.less("10.24-aip(5)<6", 24 - r.aip(5), 6) else 24 - r.aip(5)
    if r.less("10.aip(5)+k<v14", r.aip(5) + k, r.v[0x14]):
        r.store("set v14=0#2", 0x14, 0); r.store("set v18=0#3", 0x18, 0)
    r.call("11.idle", "Idle", n=15)


# ---- H1a R16 ClawViper and R142 ClawViperEx (catalogue 497, 526)
def viper_state(r, lb, v):
    """`if aip(6) ≠ 0: State(aip(6) = 2 ? 91 : 90, v)`."""
    if r.br(lb + ".aip(6)!=0", r.aip(6) != 0):
        r.call(lb + ".state", "StateSet", u=r.U, state=91 if r.br(lb + ".aip(6)=2", r.aip(6) == 2) else 90, v=v)


def viper_charge(r, lb):
    """Row 16's step 3 (row 142's step 4): the charge."""
    if (r.br(lb + ".Skill1>=0", r.skill[0] >= 0) and r.less(lb + ".dist<aip(2)", r.dist, r.aip(2))
            and r.chance(lb + ".chance(1)", 1)
            and r.br(lb + ".targetok", r.call(lb + ".targetok", "SkillTargetOk", skill=r.skill[0], u=r.t, a=r.tx, b=r.ty).eax)):
        use_skill(r, lb + ".useskill1", 1, r.t)
        viper_state(r, lb, 1)
        r.store("set v14=1", 0x14, 1)
        return True
    return False


def viper_walk(r, lb):
    if r.less(lb + ".D100<50", r.d100(), 50, draw=True):
        r.call(lb + ".walk", "Walk", t=r.t, flags=7)
    else:
        r.call(lb + ".idle", "Idle", n=r.aip(5))


def m_r16(r):
    """R16 ClawViper."""
    if r.br("1.v14!=0", r.v[0x14] != 0, val=r.v[0x14]):
        viper_state(r, "1", 0)
    if r.br("2.melee", r.melee):
        if not r.chance("2.chance(3)", 3):
            r.call("2.idle", "Idle", n=r.aip(5))
            return
        r.call("2.setmode", "SetModeAtUnit", mode=4 if r.chance("2.chance(4)", 4) else 5, t=r.t)
        return
    if viper_charge(r, "3"):
        return
    viper_walk(r, "4")


def m_r142(r):
    """R142 ClawViperEx."""
    if r.br("1.v14!=0", r.v[0x14] != 0, val=r.v[0x14]):
        viper_state(r, "1", 0)
    if r.br("2.melee", r.melee):
        if r.chance("2.chance(3)", 3):
            r.call("2.setmode5", "SetModeAtUnit", mode=5, t=r.t)
            return
        r.call("2.idle", "Idle", n=r.aip(5))
        return
    if r.less("3.dist<aip(7)", r.dist, r.aip(7)) and r.chance("3.chance(4)", 4):
        if r.less("3.v18<T", r.v[0x18], r.T):
            r.call("3.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            r.store("set v18=T + aip(8)", 0x18, r.T + r.aip(8))
            return
        r.call("3.idle", "Idle", n=r.aip(5))
        return
    if viper_charge(r, "4"):
        return
    viper_walk(r, "5")


# ---- H1a R17 SandLeaper (catalogue 560)
def m_r17(r):
    """R17 SandLeaper."""
    if (r.br("1.Skill1>=0", r.skill[0] >= 0) and r.less("1.dist<5", r.dist, 5) and r.chance("1.chance(1)", 1)
            and r.br("1.targetok", r.call("1.targetok", "SkillTargetOk", skill=r.skill[0], u=r.t, a=0, b=0).eax)):
        use_skill(r, "1.useskill1", 1, r.t)
        return
    if not r.br("2.melee", r.melee):
        if r.less("2.10<dist", 10, r.dist):
            r.call("2.ovr", "Ovr", type=0, param=75, byte=0)
            r.call("2.wandernear", "WanderNear", u=r.t, r=5)
            return
        if r.chance("2.chance(3)", 3):
            r.call("2.walk", "Walk", t=r.t, flags=7)
            return
        if r.chance("2.chance(4)", 4):
            r.call("2.t56", "T56", t=r.t, byte=4, flag=0)
            return
    elif r.chance("2.chance(2)", 2):
        r.call("2.setmode5", "SetModeAtUnit", mode=5, t=r.t)
        return
    r.call("3.idle", "Idle", n=10)


# ---- H1a R18 PantherWoman (catalogue 586; AiSameBaseNearCb 0x005B0D00)
def m_r18(r):
    """R18 PantherWoman."""
    if r.br("1.melee", r.melee):
        if r.chance("1.chance(2)", 2):
            r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        r.call("1.idle", "Idle", n=r.aip(4))
        return
    if r.chance("2.chance(1)", 1):
        r.call("2.ovr", "Ovr", type=0, param=75, byte=0)
        r.call("2.walk13", "Walk13", t=r.t, flags=7)
        return
    ret = r.call("3.search", "UnitSearch", cb=0x005B0D00, kind=1, blk={0: {0: 0, 1: 0x7FFFFFFF}})
    unit, best = ret.out(0, 0), s32(ret.out(0, 1))
    if r.br("4.unit", unit != 0) and r.less("4.aip(3)^2<best", r.aip(3) * r.aip(3), best):
        r.call("4.ovr", "Ovr", type=0, param=75, byte=0)
        r.call("4.walk", "Walk", t=unit, flags=7)
        return
    if r.less("5.D100<25", r.d100(), 25, draw=True):
        r.call("5.t56", "T56", t=r.t, byte=3, flag=0)
    else:
        r.call("5.idle", "Idle", n=r.aip(4))


# ---- H1a R24 Mosquito (catalogue 704)
def m_r24(r):
    """R24 Mosquito."""
    if r.br("1.melee", r.melee):
        if r.chance("1.chance(3)", 3) or r.br("1.v18=0", r.v[0x18] == 0, val=r.v[0x18]):
            r.store("set v18+=1", 0x18, r.v[0x18] + 1)
            if r.br("1.Skill1>=0", r.skill[0] >= 0) and r.chance("1.chance(4)", 4):
                use_skill(r, "1.useskill1", 1, r.t)
                return
            r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        if r.less("1.20<D100", 20, r.d100(), draw=True):
            r.call("1.idle", "Idle", n=15)
            return
        r.store("set v14=2", 0x14, 2); r.store("set v18=0", 0x18, 0)
    v = r.v[0x14]
    r.vals.append(("2.switch v14", v))
    if r.br("2.v14=0", v == 0):
        r.call("2.0.ovr", "Ovr", type=13, param=100, byte=0)
        r.call("2.0.walk", "Walk", t=r.t, flags=0)
    elif r.br("2.v14=1", v == 1):
        r.call("2.1.ovr", "Ovr", type=0, param=50, byte=0)
        r.call("2.1.ring", "Ring", r=4)
        r.store("set v18+=1#2", 0x18, r.v[0x18] + 1)
        if r.less("2.1.aip(5)<v18", r.aip(5), r.v[0x18]):
            r.store("set v14=0", 0x14, 0); r.store("set v18=0#2", 0x18, 0)
    elif r.br("2.v14=2", v == 2):
        r.call("2.2.ovr", "Ovr", type=2, param=100, byte=0)
        r.call("2.2.stepaway", "StepAway", t=r.t, d=10, flag=1)
        r.store("set v14=1", 0x14, 1); r.store("set v18=0#3", 0x18, 0)
    else:
        r.store("set v14=0#2", 0x14, 0); r.store("set v18=0#4", 0x18, 0)
        r.call("2.idle", "Idle", n=10)


# ---- H1a R25 WillOWisp (catalogue 735-836; AiWispCb 0x005F3960, ai/0003)
WISP = None


def wisp_tables():
    """`A`, `B` and `A5` as the catalogue lists them (R25, *The tables*), read from the spec text so that the model is the
    block; `B5[p] = A5[((p + 1) mod 5) + 1]` by its rule. {(v14, place): (x, y)} for `A` and `B`, {place: (x, y)} for the
    five-wisp tables."""
    global WISP
    if WISP is not None:
        return WISP
    import re
    path = os.path.join(os.path.dirname(HERE), "docs", "specs", "monsters", "ai", "catalogue.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read().replace("−", "-")
    pair = re.compile(r"\((-?\d+),\s*(-?\d+)\)")
    tabs = {}
    for name in ("A", "B"):
        m = re.search(r"^%s\[v14, place\].*?\n(.*?)```" % name, text, re.S | re.M)
        rows = {}
        for ln in m.group(1).splitlines():
            mm = re.match(r"\s*(\d+):(.*)$", ln)
            if mm:
                for k, (x, y) in enumerate(pair.findall(mm.group(2))):
                    rows[(int(mm.group(1)), k + 1)] = (int(x), int(y))
        tabs[name] = rows
    m = re.search(r"`A5\[1\.\.5\]` = (.*?)\.\n", text)
    a5 = {k + 1: (int(x), int(y)) for k, (x, y) in enumerate(pair.findall(m.group(1)))}
    b5 = {p: a5[((p + 1) % 5) + 1] for p in range(1, 6)}
    WISP = {"A": tabs["A"], "B": tabs["B"], "A5": a5, "B5": b5}
    return WISP


def wisp_grant(r):
    """R25's grant. `STATLIST_Alloc`'s result is not logged: it forks."""
    if r.br("g.t", r.t != 0) and r.br("g.player", r.ttype == 0, val=r.ttype):
        if not r.br("g.dead", r.call("g.dead", "UnitIsDead", c=r.t).eax):
            if r.unknown("g.alloc"):
                end = u32(r.T + 1728000)
                r.call("g.queue", "QueueEvent", _edx=r.t, kind=12, frame=end, a=0, b=0)


def m_r25(r):
    """R25 WillOWisp. State 4's room search (RoomUnitSearchInit and the walk of its result) is not a boundary: its count
    forks, and a gather of four or five wisps (each wisp's `AiCtlSetVar` and `Idle`) stops the decision. The block's
    "a room unit search around U" is taken to begin with `UnitGetRoom(U)` (0x005F3E62, the audit's first call of the
    arm). `MoveToPointNoStop` (0x005DE490) is not a boundary: it is opaque (`Run.opaque`)."""
    T, d = r.T, diff(r)
    if r.br("0.t", r.t != 0) and r.less("0.v1C<T", r.v[0x1C], T):
        dsq = s32(r.call("0.distsq", "UnitDistSq", u=r.U, t=r.t).eax)
        if (r.less("0.dsq<1024", dsq, 1024) and r.less("0.v14<4", r.v[0x14], 4)
                and not r.less("0.d+2<Range(1000)", d + 2, r.rng(1000), draw=True)):
            r.store("set v14=4", 0x14, 4)
    v14 = r.v[0x14]
    r.vals.append(("v14", v14))
    if r.br("4.v14=4", v14 == 4):
        r.call("4.room", "UnitGetRoom", u=r.U)
        if r.unknown("4.found 4 or 5"):
            raise Stop("4: a gather of four or five wisps is not modelled")
        r.store("set v14=2#4", 0x14, 2)
        r.call("4.idle8", "Idle", n=8)
        return
    if r.br("d.v14=5", v14 == 5) or r.less("d.5<v14", 5, v14):
        five = v14 == 5
        p = r.v[0x1C]
        if r.less("1.lim<v1C", 5 if five else 4, p):
            r.store("set v14=2#1", 0x14, 2)
            r.call("1.idle8", "Idle", n=8)
            return
        if r.t == 0:
            raise Stop("2: the dance reads the target's position, and there is none")
        W = wisp_tables()
        key = p if five else (v14, p)
        a = (W["A5"] if five else W["A"]).get(key)
        b = (W["B5"] if five else W["B"]).get(key)
        if a is None:
            raise Stop("2: index outside the tables (v14 %d, v1C %d)" % (v14, p))
        px, py = u32(r.tx + a[0]), u32(r.ty + a[1])
        if r.br("3.pd>3", u32(r.call("3.pathdist", "PathDist", u=r.U, x=px, y=py).eax) > 3):
            if r.rchance("3.Range<34", 100, 34):
                r.call("3.ring4", "Ring", r=4)
            else:
                r.opaque("3.MoveToPointNoStop")
            return
        if r.br("4.T%67!=0", T % 67 != 0):
            r.call("4.idle67", "Idle", n=67 - T % 67)
            return
        if r.less("5.v18<3", r.v[0x18], 3):
            if r.br("5.B=(0,0)", b == (0, 0)):
                r.store("set v18+=1", 0x18, r.v[0x18] + 1)
                r.call("5.idle", "Idle", n=(337 - T % 337) if five else 67)
            else:
                r.call("5.setmode7", "SetMode", mode=7, x=u32(r.tx + b[0]), y=u32(r.ty + b[1]))
                r.store("set v18+=1#2", 0x18, r.v[0x18] + 1)
            return
        if five:
            r.store("set v14=2#6", 0x14, 2); r.store("set v1c=T+1800", 0x1C, T + 1800)
            r.call("6.idle", "Idle", n=337 - T % 337)
            return
        r.store("set v14+=1", 0x14, r.v[0x14] + 1); r.store("set v18=0#7", 0x18, 0)
        if r.less("7.12<v14", 12, r.v[0x14]):
            r.store("set v14=2#7", 0x14, 2); r.store("set v1c=T+1800#7", 0x1C, T + 1800)
        r.call("7.idle", "Idle", n=337 - T % 337)
        wisp_grant(r)
        return
    if r.br("s1.v14=1", v14 == 1):
        if not r.less("s1.1.0<v18", 0, r.v[0x18]):
            if r.br("s1.1.melee", r.melee):
                r.call("s1.1.setmode8", "SetModeAtUnit", mode=8, t=0)
                r.store("set v14=3", 0x14, 3)
                return
            if r.chance("s1.1.chance(1)", 1):
                r.call("s1.1.setmode8b", "SetModeAtUnit", mode=8, t=0)
                r.store("set v14=2#s1", 0x14, 2)
                return
        r.store("set v18-=1", 0x18, r.v[0x18] - 1); r.store("set v14=1#s1", 0x14, 1)
        if r.rchance("s1.2.Range<aip(3)", 100, r.aip(3)):
            r.call("s1.2.walk", "Walk", t=r.t, flags=0)
        else:
            r.call("s1.2.ring6", "Ring", r=6)
        return
    if not r.br("p.1.melee", r.melee) and (r.br("p.1.v14=2", v14 == 2) or r.chance("p.1.chance(1)", 1)):
        r.call("p.1.setmode7", "SetModeAtUnit", mode=7, t=r.t)
        r.store("set v14=0#p1", 0x14, 0)
        return
    if r.br("p.2.melee", r.melee) and (r.br("p.2.v14=3", v14 == 3) or r.chance("p.2.chance(2)", 2)):
        r.call("p.2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        r.store("set v14=0#p2", 0x14, 0)
        return
    r.store("set v14=1#p", 0x14, 1)
    if r.rchance("p.3.Range<aip(3)", 100, r.aip(3)):
        r.call("p.3.walk", "Walk", t=r.t, flags=0)
    else:
        r.call("p.3.ring4", "Ring", r=4)
    r.store("set v18=3", 0x18, 3)


# ---- H1a R27 ThornHulk (catalogue 896)
def hulk_frenzy(r, lb):
    """`MonAiUseSkill(5, Skill1, t, 0, 0)`, then the delay to the mode's first event."""
    r.call(lb + ".useskill", "UseSkill", mode=5, skill=r.skill[0], t=r.t, x=0, y=0)
    f = s32(r.call(lb + ".firstframe", "UnitEventFirstFrame", c=r.G, d=r.U, s1=1).eax)
    if r.less(lb + ".T<f", s32(r.T), f):
        r.call(lb + ".delay", "Delay", n=r.aip(5) - s32(r.T) + f)


def m_r27(r):
    """R27 ThornHulk."""
    if not r.br("1.melee", r.melee):
        r.store("set v14=0", 0x14, 0)
        r.call("1.walk13", "Walk13", t=r.t, flags=7)
        return
    if r.less("2.v14<1", r.v[0x14], 1):
        if not r.chance("2.chance(1)", 1):
            if r.rchance("2.Range<aip(3)", 100, r.aip(3)):
                r.call("2.t56", "T56", t=r.t, byte=4, flag=0)
                return
            r.call("2.idle", "Idle", n=15)
            return
        if r.less("2.v18<1", r.v[0x18], 1) and r.rchance("2.Range<aip(4)", 100, r.aip(4)):
            hulk_frenzy(r, "2")
            r.store("set v14=aip(6)", 0x14, r.aip(6))
            return
        r.store("set v18-=1", 0x18, r.v[0x18] - 1)
        a2 = r.rchance("2.Range<aip(2)", 100, r.aip(2))
        r.call("2.setmode", "SetModeAtUnit", mode=5 if a2 else 4, t=r.t)
        return
    hulk_frenzy(r, "3")
    r.store("set v14-=1", 0x14, r.v[0x14] - 1)
    if r.less("5.v14<1", r.v[0x14], 1):
        r.store("set v18=3", 0x18, 3)


# ---- H1a R72 DoomKnight (catalogue 1572)
def m_r72(r):
    """R72 DoomKnight."""
    if not r.br("1.melee", r.melee):
        if r.chance("1.chance(3)", 3):
            r.call("1.walk13", "Walk13", t=r.t, flags=7)
            return
        r.call("1.idle", "Idle", n=r.aip(4))
        return
    if r.chance("2.chance(1)", 1):
        r.call("2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    r.call("3.idle", "Idle", n=r.aip(2))


# ---- H1a R74 OblivionKnight (catalogue 1619; AiOblivionKnightCb 0x005FAE40, ai/0005)
def m_r74(r):
    """R74 OblivionKnight. Skills' row count and `auratargetstate` are not logged (step 2 forks on them, and `HasState`'s
    state is not compared); `MonsterData+0x0E` is not logged (step 4's `Skill1` arm forks)."""
    ret = r.call("1.search", "UnitSearch", cb=0x005FAE40, kind=1,
                 blk={0: {0: 0, 1: 0, 2: 2500, 3: 0x7FFFFFFF, 4: 0x7FFFFFFF}})
    knight = ret.out(0, 0)
    curse = None
    if r.less("2.dist<aip(1)", r.dist, r.aip(1)):
        if (r.br("2.Skill4>0", r.skill[3] > 0) and r.unknown("2.Skill4<count and st>0")
                and not r.br("2.hasstate", r.call("2.hasstate", "HasState", u=r.t).eax)):
            curse = 4
        else:
            if r.br("2.knight", knight != 0):
                dsq = s32(r.call("2.distsq", "UnitDistSq", u=knight, t=r.t).eax)
                if (r.less("2.dist^2<dsq", s32(r.dist * r.dist), dsq)
                        and r.br("2.walked", r.call("2.walk", "Walk", t=knight, flags=4).eax)):
                    return
            r.call("2.ovr", "Ovr", type=2, param=50, byte=0)
            if r.br("2.stepped", r.call("2.stepaway", "StepAway", t=r.t, d=10, flag=1).eax):
                return
            if r.br("2.Skill3>=0", r.skill[2] >= 0):
                use_skill(r, "2.useskill3", 3, r.t)
                return
    if curse is None:
        ret = r.call("3.findhostile", "FindHostile", pm=0)
        h = ret.eax
        if r.br("4.h", h != 0) and r.less("4.d2<aip(2)", s32(ret.out(0)), r.aip(2)):
            if (r.br("4.Skill6>0", r.skill[5] > 0) and r.less("4.v14<T", r.v[0x14], r.T)
                    and r.rchance("4.Range<aip(4)", 100, r.aip(4))):
                curse = 6
            elif r.chance("4.chance(5)", 5):
                if r.br("4.Skill3>=0", r.skill[2] >= 0) and r.rchance("4.Range<aip(6)", 100, r.aip(6)):
                    use_skill(r, "4.useskill3", 3, h)
                    return
                if r.br("4.Skill1>=0", r.skill[0] >= 0) and not r.unknown("4.MonsterData+0x0E>=4"):
                    use_skill(r, "4.useskill1", 1, h)
                    return
    if curse == 4:
        use_skill(r, "c4.useskill4", 4, r.t)
        r.store("set v14=T + aip(3)", 0x14, r.T + r.aip(3))
        return
    if curse == 6:
        use_skill(r, "c6.useskill6", 6, r.t)
        r.store("set v14=T + aip(3)#6", 0x14, r.T + r.aip(3))
        return
    if r.less("5.aip(8)<dist", r.aip(8), r.dist) and r.chance("5.chance(7)", 7):
        r.call("5.wandernear", "WanderNear", u=r.t, r=6)
        return
    if r.less("6.69<D100", 69, r.d100(), draw=True):
        r.call("6.idle", "Idle", n=10)
        return
    r.call("7.t56", "T56", t=r.t, byte=3, flag=0)


# ---- H1b R115 SiegeBeast (catalogue 3200; AiImpNearCb 0x005E1720, ai/0009)
def m_r115(r):
    """R115 SiegeBeast."""
    o = r.call("1.owner", "UnitGetOwner", c=r.G, d=r.U).eax
    if r.br("2.death", r.call("2.deathmode", "MonIsDeathMode", s1=r.U).eax):
        return
    if r.br("3.o=0", o == 0) and r.br("3.align=0", r.call("3.align", "UnitAlignGet", u=r.U).eax == 0):
        imp = r.call("3.search", "UnitSearch", cb=0x005E1720, kind=1, blk={0: {0: r.aip(1) * r.aip(1)}}).eax
        if r.br("3.imp", imp != 0):
            r.call("3.sethost", "AiImpSetHost", c=imp, d=r.U)
    if r.br("4.melee", r.melee):
        if r.br("4.Skill1>=0", r.skill[0] >= 0) and r.chance("4.chance(3)", 3):
            r.call("4.stomp", "UseSkill", mode=r.skmode[0], skill=r.skill[0], t=0, x=0, y=0)
            return
        if r.chance("4.chance(2)", 2):
            r.call("4.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        else:
            r.call("4.idle", "Idle", n=r.aip(4))
        return
    if (r.br("5.Skill1>=0", r.skill[0] >= 0)
            and r.less("5.dist<p5", r.dist, s32(r.call("5.param5", "SkillGetParam5", c=r.skill[0]).eax))
            and r.rchance("5.Range<aip(5)", 100, r.aip(5))):
        r.call("5.useskill", "UseSkill", mode=r.skmode[0], skill=r.skill[0], t=0, x=0, y=0)
        return
    if (r.br("6.approach", r.call("6.approach", "ApproachPointTest", u=r.U, t=r.t).eax)
            and r.chance("6.chance(6)", 6)):
        r.call("6.ovr", "Ovr", type=0, param=min(max(r.aip(7), 0), 127), byte=0)
        r.call("6.toward", "Toward", t=r.t, max=12, ring=0)
        return
    r.call("7.toward", "Toward", t=r.t, max=12, ring=0)


# ---- H1b R116 Minion (catalogue 3231)
def m_r116(r):
    """R116 Minion. The head record is the AID line's `head` (AiCtl+0x20's record at the think call): kind `+0x08`, type
    `+0x0C`, guid `+0x10`, expiry `+0x14` (machinery E4; R116a's order)."""
    f, t, melee = 0, r.t, r.melee
    p = r.call("2.head", "ParamsHead", U=r.U).eax
    if r.br("2.p", p != 0):
        if r.head is None:
            raise Stop("no head record logged")
        kind, typ, guid, exp = r.head[2], r.head[3], r.head[4], s32(r.head[5])
        found = False
        if r.br("2.kind=1", kind == 1, val=kind) and r.less("2.T<exp", s32(r.T), exp):
            u = r.call("2.find", "GameFindUnit", type=typ, guid=guid).eax
            if r.br("2.found", u != 0) and not r.br("2.dead", r.call("2.dead", "UnitIsDead", c=u).eax):
                found, f = True, 1
                if r.br("2.u!=t", u != t):
                    t = u
                    r.call("2.edge", "UnitEdgeDistance", s1=r.U, s2=u)
                    melee = r.call("2.inmelee", "InMeleeRange", u=r.U, t=u, z=0).eax
        if not found:
            r.call("2.pop", "ParamsPop")
    if r.br("3.melee", melee):
        if r.br("3.f=0", f == 0) and not r.chance("3.chance(1)", 1):
            r.call("3.idle", "Idle", n=r.aip(2))
            return
        r.call("3.setmode", "SetModeAtUnit", mode=5 if r.chance("3.chance(2)", 2) else 4, t=t)
        return
    if r.br("4.f=0", f == 0) and not r.chance("4.chance(3)", 3):
        r.call("4.idle", "Idle", n=r.aip(4))
        return
    r.call("5.walk", "Walk", t=t, flags=0)


# ---- H1b R117 SuicideMinion, and S15 (its alias; catalogue 3259, 3480)
def m_r117(r):
    """R117 SuicideMinion (and state 15, the same think)."""
    if r.br("1.v14!=0", r.v[0x14] != 0, val=r.v[0x14]):
        if r.less("1.v14<T", r.v[0x14], s32(r.T)):
            r.call("1.setmode0", "SetModeAtUnit", mode=0, t=r.t)
        else:
            r.call("1.idle", "Idle", n=r.aip(2))
        return
    if r.br("2.melee", r.melee):
        r.store("set v14=T + aip(5)", 0x14, r.T + r.aip(5))
        r.call("2.idle", "Idle", n=r.aip(2))
        return
    if r.chance("3.chance(3)", 3):
        r.call("3.walk", "Walk", t=r.t, flags=0)
    else:
        r.call("3.idle", "Idle", n=r.aip(2))


# ---- H1b R119 SuccubusWitch (catalogue 3306)
def m_r119(r):
    """R119 SuccubusWitch. `StatListFindFlag(t, 0x20)` is not a boundary here (0x005E2157): it forks."""
    dist = r.dist
    if (r.br("1.t", r.t != 0) and not r.unknown("1.flag0x20") and r.less("1.dist<aip(4)", dist, r.aip(4))
            and r.chance("1.chance(3)", 3)):
        if (r.br("1.Skill1>0", r.skill[0] > 0)
                and not r.less("1.lifeT<aip(7)", s32(r.call("1.lifet", "UnitLifePct", u=r.t).eax), r.aip(7))):
            use_skill(r, "1.useskill1", 1, r.t)
            return
        if (r.br("1.Skill2>0", r.skill[1] > 0)
                and not r.less("1.aip(8)<lifeU", r.aip(8), s32(r.call("1.lifeu", "UnitLifePct", u=r.U).eax))):
            use_skill(r, "1.useskill2", 2, r.t)
            return
        if r.br("1.Skill3>0", r.skill[2] > 0):
            hp = s32(r.call("1.maxhp", "UnitGetMaxHp", s1=r.t).eax)
            mana = s32(r.call("1.maxmana", "UnitGetMaxMana", s1=r.t).eax)
            if r.less("1.mana<hp", mana, hp) or r.br("1.ttype!=0", r.ttype != 0):
                use_skill(r, "1.useskill3", 3, r.t)
                return
        if r.br("1.Skill4>0", r.skill[3] > 0) and r.br("1.ttype=0", r.ttype == 0):
            use_skill(r, "1.useskill4", 4, r.t)
            return
    step = r.aip(4) & 0xFF
    if r.br("2.melee", r.melee):
        if r.chance("2.chance(3)", 3) and r.br("2.stepped", r.call("2.stepaway", "StepAway", t=r.t, d=step, flag=1).eax):
            return
        if r.chance("2.chance(1)", 1):
            r.call("2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        else:
            r.call("2.idle", "Idle", n=r.aip(6))
        return
    if r.br("3.Skill5>=0", r.skill[4] >= 0) and r.less("3.0<aip(8)", 0, r.aip(8)) and r.chance("3.chance(5)", 5):
        ret = r.call("3.findhostile", "FindHostile", pm=0, blk={0: {0: dist}})
        dist = s32(ret.out(0))
        if r.br("3.h", ret.eax != 0) and r.rchance("3.Range<aip(8)", 100, r.aip(8)):
            use_skill(r, "3.useskill5", 5, ret.eax)
            return
    if (r.less("4.dist<aip(4)", dist, r.aip(4)) and r.chance("4.chance(3)", 3)
            and r.br("4.stepped", r.call("4.stepaway", "StepAway", t=r.t, d=step, flag=1).eax)):
        return
    if r.br("5.Skill5<0", r.skill[4] < 0):
        ret = r.call("5.findhostile", "FindHostile", pm=0, blk={0: {0: dist}})
        if r.br("5.h", ret.eax != 0) and r.chance("5.chance(5)", 5):
            r.call("5.setmode9", "SetModeAtUnit", mode=9, t=ret.eax)
            return
    if r.chance("6.chance(2)", 2):
        r.call("6.walk", "Walk", t=r.t, flags=0)
        return
    if r.less("7.D100<50", r.d100(), 50, draw=True) and r.br("7.t56", r.call("7.t56", "T56", t=r.t, byte=6, flag=1).eax):
        return
    r.call("8.idle", "Idle", n=r.aip(6))


# ---- H1b R120 Overseer (catalogue 3336; AiOverseerMinionCb 0x005E26D0, ai/0010)
def overseer_stored(r):
    """`AiStoredHostile` (R120a), run: `U+0xC8` and the stored unit are not logged, so whether there is one, and its
    kind and mode, fork; a monster's `UnitsHostile` is compared with its unit word unnamed. -> (non-zero, unit or None)."""
    if not r.unknown("2.c8&0x20000 and stored"):
        return False, None
    if r.unknown("2.player live"):
        return True, None
    if not r.unknown("2.monster live"):
        return False, None
    return r.br("2.hostile", r.call("2.hostile", "UnitsHostile", c=r.G, d=r.U).eax != 0), None


def m_r120(r):
    """R120 Overseer. The quest hook 0x00587900 is not a boundary and nothing in the block reads its result: not
    modelled (a draw of it would show at the next compared seed). `MonHasSkill` (0x005DD2D0) is not a boundary: it forks."""
    wnz, w = overseer_stored(r)
    if (r.br("3.Skill1>=0", r.skill[0] >= 0) and r.br("3.St3or19", r.call("3.st3or19", "St3or19", U=r.U).eax)
            and r.less("3.v14<T", r.v[0x14], s32(r.T)) and r.br("3.w", wnz) and r.unknown("3.hasskill1")):
        use_skill(r, "3.useskill1", 1, w)
        r.store("set v14=T + aip(1)", 0x14, r.T + r.aip(1))
        return
    if r.br("4.melee", r.melee) and r.chance("4.chance(6)", 6):
        r.call("4.setmode", "SetModeAtUnit", mode=5 if r.chance("4.chance(7)", 7) else 4, t=r.t)
        return
    ret = r.call("5.search", "UnitSearch", cb=0x005E26D0, kind=1, blk={0: {0: 576, 1: 400, 2: 50, 3: 0, 4: 0, 5: 0}})
    weak, whip, count = ret.out(0, 3), ret.out(0, 4), ret.out(0, 5)
    if (r.br("6.Skill2>=0", r.skill[1] >= 0) and r.br("6.weak", weak != 0) and r.chance("6.chance(2)", 2)
            and r.unknown("6.hasskill2")):
        use_skill(r, "6.useskill2", 2, weak)
        return
    if (r.br("7.Skill3!=0", r.skill[2] != 0) and r.br("7.whip", whip != 0) and r.chance("7.chance(3)", 3)
            and r.br("7.align!=2", r.call("7.align", "UnitAlignGet", u=r.U).eax != 2) and r.unknown("7.hasskill3")):
        use_skill(r, "7.useskill3", 3, whip)
        return
    if r.br("8.count", count != 0):
        if r.less("8.dist<aip(4)-aip(5)", r.dist, r.aip(4) - r.aip(5)):
            r.call("8.stepaway", "StepAway", t=r.t, d=(r.aip(4) - r.dist) & 0xFF, flag=0)
            return
        if r.less("8.aip(4)+aip(5)<dist", r.aip(4) + r.aip(5), r.dist):
            r.call("8.walk", "Walk", t=r.t, flags=0)
            return
        if r.rchance("8.Range<50", 100, 50):
            r.call("8.t56", "T56", t=r.t, byte=5, flag=0)
        else:
            r.call("8.idle", "Idle", n=10)
        return
    if r.less("9.D100<60", r.d100(), 60, draw=True):
        r.call("9.walk", "Walk", t=r.t, flags=0)
    else:
        r.call("9.idle", "Idle", n=10)


# ---- H1b R122 Imp and S16 (catalogue 3393, 3415, 3498): the fixed records 492..495 and AiUseSkillNearSelf
IMP_RECS = None          # {k: (aip[24], skills[8], modes[8])} for R1..R4 (classes 492..495); tests set it


def imp_rec(k):
    """R`k` of row 122 (MonStats record 491 + k), read from the game's monstats.bin (as tools/monstats.py reads it)."""
    global IMP_RECS
    if IMP_RECS is None:
        from excel_bin import find_file, read_bin
        excel = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
        recs, sz = read_bin(find_file(excel, "monstats", ".bin"))
        assert sz == 0x1A8, sz
        IMP_RECS = {}
        for j in range(1, 5):
            b = recs[491 + j]
            aip = [ai.s16(int.from_bytes(b[0x56 + 2 * i:0x58 + 2 * i], "little")) for i in range(24)]
            sk = [ai.s16(int.from_bytes(b[0x170 + 2 * i:0x172 + 2 * i], "little")) for i in range(8)]
            IMP_RECS[j] = (aip, sk, list(b[0x180:0x188]))
    return IMP_RECS[k]


def raip(r, k, slot):
    """`Rk.aip(slot)` at the game's difficulty (Normal under `d0`)."""
    return imp_rec(k)[0][3 * (slot - 1) + diff(r)]


def near_self(r, lb, rad, skill, mode):
    """`AiUseSkillNearSelf(U, rad, skill, mode)` (0x005DF850), run: its `UnitGetGame` and `MonAiUseSkill` are logged
    (the helper's window)."""
    n = s32(2 * rad)

    def jitter():
        if n > 0:
            low = r.step()
            return low & (n - 1) if n & (n - 1) == 0 else low % n
        return 0
    ox = jitter()
    oy = jitter()
    game = r.call(lb + ".game", "UnitGetGame", c=r.U).eax
    r.call(lb + ".useskill", "UseSkill", _ecx=game, mode=mode, skill=skill, t=0,
           x=u32(r.x + ox - rad), y=u32(r.y + oy - rad))


def m_r122(r):
    """R122 Imp. `R1..R4` are MonStats records 492..495 (`imp_rec`); `Skill1`, `Skill4` and `Sk1mode` the imp's own."""
    if r.br("1.v14!=-1", r.v[0x14] != -1, val=r.v[0x14]) and r.br("1.align=0", r.call("1.align", "UnitAlignGet", u=r.U).eax == 0):
        h = r.call("1.find", "GameFindUnit", type=1, guid=r.v[0x14]).eax
        if (r.br("1.h", h != 0) and not r.br("1.dead", r.call("1.dead", "UnitIsDead", c=h).eax)
                and r.br("1.owner=0", r.call("1.owner", "UnitGetOwner", c=r.G, d=h).eax == 0)
                and r.br("1.halign=0", r.call("1.halign", "UnitAlignGet", u=h).eax == 0)):
            dsq = s32(r.call("1.distsq", "UnitDistSq", u=r.U, t=h).eax)
            if r.less("1.R2a1^2<dsq", raip(r, 2, 1) * raip(r, 2, 1), dsq):
                r.call("1.walk", "Walk", t=h, flags=0)
                return
            if r.br("1.Skill1>=0", r.skill[0] >= 0):
                use_skill(r, "1.useskill1", 1, h)
                return
        else:
            r.store("set v14=-1", 0x14, -1)
    if r.br("2.melee", r.melee):
        if (r.br("2.Skill1>=0", r.skill[0] >= 0)
                and r.less("2.life<R1a1", s32(r.call("2.lifepct", "LifePct", U=r.U).eax), raip(r, 1, 1))):
            near_self(r, "2.near", raip(r, 1, 2), r.skill[0], s8(r.skmode[0]))
            return
        if (r.less("2.D100<R3a2", r.d100(), raip(r, 3, 2), draw=True)
                and r.br("2.stepped", r.call("2.stepaway", "StepAway", t=r.t, d=5, flag=1).eax)):
            return
    if r.br("3.Skill1>=0", r.skill[0] >= 0) and r.less("3.D100<R1a3", r.d100(), raip(r, 1, 3), draw=True):
        near_self(r, "3.near", raip(r, 1, 2), r.skill[0], s8(r.skmode[0]))
        return
    if r.less("4.dist<R3a1", r.dist, raip(r, 3, 1)) and r.less("4.D100<R3a2", r.d100(), raip(r, 3, 2), draw=True):
        r.call("4.stepaway", "StepAway", t=r.t, d=5, flag=0)
        return
    if r.br("5.Skill4>=0", r.skill[3] >= 0):
        ret = r.call("5.findhostile", "FindHostile", pm=0, blk={0: {0: r.dist}})
        h = ret.eax
        if r.br("5.h", h != 0):
            dist = s32(ret.out(0))
            if r.less("5.dist<R3a3", dist, raip(r, 3, 3)):
                if r.rchance("5.Range<R3a4", 100, raip(r, 3, 4)):
                    use_skill(r, "5.useskill4", 4, h)
                    return
            elif r.less("5.dist<R4a3", dist, raip(r, 4, 3)) and r.rchance("5.Range<R4a4", 100, raip(r, 4, 4)):
                use_skill(r, "5.useskill4b", 4, h)
                return
    if r.less("6.D100<33", r.d100(), 33, draw=True):
        r.call("6.walkstop", "WalkStop", t=r.t, n=4)
        return
    if r.less("7.D100<20", r.d100(), 20, draw=True):
        r.call("7.ring8", "Ring", r=8)
        return
    r.call("8.idle", "Idle", n=10)


def m_s16(r):
    """S16, the think (the init is not a think call). Slots of `R1` and `R2` (records 492, 493); the skill and its mode
    are `R1`'s at slot `v18`."""
    o = r.call("1.owner", "UnitGetOwner", c=r.G, d=r.U).eax
    st = r.call("2.hasstate", "HasState", u=r.U, state=143).eax
    if not r.br("2.state143", st) or r.br("2.o=0", o == 0):
        r.call("2.init", "MonAiInit", ctl=r.ctlp, state=0)
        r.call("2.idle", "Idle", n=1)
        return
    if (r.less("3.24<dist", 24, r.dist) or r.br("3.odead", r.call("3.odead", "UnitIsDead", c=o).eax)
            or r.br("3.oalign!=0", r.call("3.oalign", "UnitAlignGet", u=o).eax != 0)
            or r.br("3.v18=0", r.v[0x18] == 0, val=r.v[0x18])):
        r1 = imp_rec(1)
        near_self(r, "3.near", raip(r, 1, 2), r1[1][0], s8(r1[2][0]))
        r.store("set v14=-1", 0x14, -1)
        return
    if r.less("4.dist<R2a2", r.dist, raip(r, 2, 2)) and r.rchance("4.Range<R2a3", 100, raip(r, 2, 3)):
        if r.br("4.v1C!=0", r.v[0x1C] != 0):
            r.rng(2 * raip(r, 2, 4))
            r.rng(2 * raip(r, 2, 4))
        k = r.v[0x18]
        if not 0 <= k < 8:
            raise Stop("4: slot v18 %d outside the record's eight skills" % k)
        r1 = imp_rec(1)
        s = r1[1][k]
        if r.br("4.s>=0", s >= 0):
            r.call("4.useskill", "UseSkill", mode=r1[2][k], skill=s, t=r.t, x=0, y=0)
        else:
            r.call("4.idle", "Idle", n=20)
        return
    if r.rchance("5.Range<50", 100, 50):
        r.call("5.setmode8", "SetModeAtUnit", mode=8, t=r.t)
    else:
        r.call("5.idle", "Idle", n=20)


# ---- H1b R123 Catapult (catalogue 3435)
def m_r123(r):
    """R123 Catapult."""
    if r.chance("1.chance(1)", 1):
        r.call("1.setmode4", "SetModeAtUnit", mode=4, t=0)
    else:
        r.call("1.idle", "Idle", n=15)


# ---- H1b R126 CatapultSpotter (catalogue 3529; g_AiSpotterSkills 0x006E3514, ai/0011: 287, 288, 303, 304, 305)
SPOTTER_SKILLS = (287, 288, 303, 304, 305)


def m_r126(r):
    """R126 CatapultSpotter. `SpotterCatapultDead` (0x005EDF70) is run: its `UnitGetRoom(U)` is logged, its result forks.
    `FreeNearStep` is not a boundary: whether it finds a point forks, and the point it writes is not logged, so the
    strike's x and y are not compared (its draws are, by the seed at the call)."""
    if r.br("1.v1C=0", r.v[0x1C] == 0, val=r.v[0x1C]) or r.less("1.D100<3", r.d100(), 3, draw=True):
        r.call("1.room", "UnitGetRoom", u=r.U)
        if r.unknown("1.dead"):
            r.call("1.setmode0", "SetModeAtUnit", mode=0, t=r.t)
            return
    if r.br("2.v1C=0", r.v[0x1C] == 0):
        r.store("set v1c=1", 0x1C, 1)
    if r.less("3.0<aip(2)-T+v1C", 0, s32(r.aip(2) - r.T + r.v[0x1C])):
        r.call("3.idle", "Idle", n=r.aip(2))
        return
    if not r.br("4.t", r.t != 0) or not r.chance("4.chance(1)", 1):
        r.call("4.idle", "Idle", n=r.aip(2))
        return
    if r.less("5.0<v18", 0, r.v[0x18]):
        k = r.v[0x14]
        r.store("set v18-=1", 0x18, r.v[0x18] - 1)
    else:
        k = r.rng(5)
        r.store("set v14=k", 0x14, k); r.store("set v18=aip(5)", 0x18, r.aip(5))
    a4 = r.aip(4)
    r.rng(2 * a4)
    r.rng(2 * a4)
    r.call("7.room", "UnitGetRoom", u=r.U)
    if not r.unknown("7.freenear"):
        r.call("7.idle", "Idle", n=15)
        return
    r.vals.append(("8.k", k))
    skill = SPOTTER_SKILLS[k] if 0 <= k < 5 else None
    r.call("8.useskill", "UseSkill", mode=4, skill=skill, t=0)
    r.store("set v1c=T", 0x1C, r.T)


# ---- H1b R129 GenericSpawner (catalogue 3582)
def m_r129(r):
    """R129 GenericSpawner. `v3C` is the AID line's `ctl` word +0x3C. The pick's region (`MonRegionGet`, 0x00573520) is not
    a boundary: whether its count is above 0, and so whether it draws, forks. The pick returns 1 on every path, so step 2's
    death arm is never taken."""
    if not r.br("1.t", r.t != 0):
        r.call("1.idle", "Idle", n=20)
        return
    if r.br("2.v3C=-1", r.ctlw(0x3C) == -1):
        if r.unknown("2.n>0"):
            r.step()
        if not r.br("2.picked", True):
            r.store("set c4|=0x20000", "c4", r.c4 | 0x20000)
            r.call("2.die", "SetMode", mode=0)
            return
    if r.less("3.20<dist", 20, r.dist):
        r.call("3.idle", "Idle", n=20)
        return
    if not r.less("4.v18<aip(3)", r.v[0x18], r.aip(3)):
        r.store("set c4|=0x20000#4", "c4", r.c4 | 0x20000)
        r.call("4.die", "SetMode", mode=0, x=0, y=0)
        return
    e = s32(r.T - r.v[0x14])
    if e < 0:
        e = s32(-e)
    if r.less("5.e<aip(1)", e, r.aip(1)):
        r.call("5.idle", "Idle", n=20)
        return
    r.store("set v14=T", 0x14, r.T)
    cls = 528 if r.ms2 > 528 else -1
    room = r.call("7.room", "UnitGetRoom", u=r.U).eax
    if r.br("7.cell", r.call("7.celltest", "SpawnClassCellTest", cls=cls, room=room, x=r.x, y=r.y, z=0).eax):
        r.store("set v18+=1", 0x18, r.v[0x18] + 1)
        r.call("7.nest", "UseSeqSkill", skill=167, t=r.t, x=0, y=0)
        return
    r.call("8.idle", "Idle", n=20)


# ---- H1b R136 BaalTaunt (catalogue 3775)
def m_r136(r):
    """R136 BaalTaunt. `UnitTeleport`'s words (the room, X(t), Y(t), 0, 0) are not compared: revision 3's caller read
    names three positional words and the block five, with no source that maps them."""
    if not r.br("1.t", r.t != 0):
        r.call("1.idle", "Idle", n=25)
        return
    still = r.br("2.still", r.ttype in (0, 1) and tmode(r) == 1, val=tmode(r))
    fire = False
    if still:
        r.store("set v14+=1", 0x14, r.v[0x14] + 1)
        fire = r.less("2.aip(2)<v14", r.aip(2), r.v[0x14])
    if fire or not still:
        r.store("set v14=0", 0x14, 0)
    if fire:
        r.call("3.taunt", "UseSkill", mode=4, skill=284, t=r.t, x=0, y=0)
        return
    if r.less("4.aip(3)<dist", r.aip(3), r.dist):
        r.call("4.room", "UnitGetRoom", u=r.t)
        if r.br("4.teleported", r.call("4.teleport", "UnitTeleport").eax):
            r.call("4.idle", "Idle", n=25)
            return
    if r.less("5.aip(1)<dist", r.aip(1), r.dist):
        r.call("5.walkz", "WalkZ", t=r.t)
        return
    r.call("6.idle", "Idle", n=25)


# ---- H1b R137 PutridDefiler (catalogue 3797; AiDefilerTargetCb 0x005EFA50, ai/0011)
def m_r137(r):
    """R137 PutridDefiler."""
    if r.br("1.t", r.t != 0) and r.br("1.melee", r.melee):
        r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    u = r.call("2.search", "UnitSearch", cb=0x005EFA50, kind=1, blk={0: {0: 0, 1: 25}}).eax
    if r.br("3.u", u != 0):
        if r.br("3.inmelee", r.call("3.inmelee", "InMeleeRange", u=r.U, t=u, z=0).eax):
            r.call("3.impregnate", "UseSkill", mode=8, skill=300, t=u, x=0, y=0)
        else:
            r.call("3.walkz", "WalkZ", t=u)
        return
    if r.less("4.dist<aip(1)", r.dist, r.aip(1)):
        r.call("4.stepaway", "StepAway", t=r.t, d=r.aip(2) & 0xFF, flag=0)
    else:
        r.call("4.idle", "Idle", n=25)


# ---- H1d S5 (and R60, its alias; catalogue 2557, 4345)
def m_s5(r):
    """S5, the think of state 5 and row 60. U.mode is the AID line's `m` (Unit+0x10); `U = 0` cannot reach a think call."""
    if r.br("1.mode!=1", r.aid["m"] != 1, val=r.aid["m"]):
        r.call("1.idle5", "Idle", n=5)
        return
    room = r.call("2.room", "UnitGetRoom", u=r.U).eax
    if not r.br("2.town", r.call("2.town", "RoomIsTown", room=room).eax):
        ret = r.call("2.findhostile", "FindHostile")
        h = ret.eax
        if r.br("2.h", h != 0) and r.less("2.e<20", s32(ret.out(0)), 20):
            if r.rchance("2.Range<30", 100, 30):
                if r.br("2.class=271", r.cls == 271, val=r.cls):
                    use_skill(r, "2.useskill1", 1, h)
                else:
                    r.call("2.setmode4", "SetModeAtUnit", mode=4, t=h)
                return
            if r.rchance("2.Range<30#2", 100, 30):
                r.call("2.t56", "T56", t=h, byte=4, flag=0)
                return
            r.call("2.idle10", "Idle", n=10)
            return
    if r.less("3.D100<20", r.d100(), 20, draw=True):
        r.call("3.ring5", "Ring", r=5)
        return
    r.call("4.idle", "Idle", n=10)


# ---- H1d S6 (catalogue 2581)
def m_s6(r):
    """S6, the think of state 6."""
    if r.br("1.mode!=1", r.aid["m"] != 1, val=r.aid["m"]):
        r.call("1.idle5", "Idle", n=5)
        return
    room = r.call("2.room", "UnitGetRoom", u=r.U).eax
    if not r.br("2.town", r.call("2.town", "RoomIsTown", room=room).eax):
        ret = r.call("2.findtarget", "FindTarget", ctl=r.ctlp)
        h = ret.eax
        if r.br("2.h", h != 0):
            v = r.rng(100)
            if r.br("2.m=0", ret.out(2) == 0):
                if r.less("2.r<30", v, 30, draw=True):
                    r.call("2.walk", "Walk", t=h, flags=7)
                else:
                    r.call("2.idle10", "Idle", n=10)
            else:
                if r.less("2.r<80", v, 80, draw=True):
                    r.call("2.setmode4", "SetModeAtUnit", mode=4, t=h)
                else:
                    r.call("2.idle10b", "Idle", n=10)
            return
    if r.less("3.D100<20", r.d100(), 20, draw=True):
        r.call("3.ring5", "Ring", r=5)
        return
    r.call("4.idle", "Idle", n=10)


# ---- H1d R41 Towner (catalogue 4269): row 32's chain without AiNpcNearPlayer (catalogue 4154). The chain's words (home,
# the kind-4, 5, 7 records, the path list's nodes) are not logged: they fork. Phase 1c's R32 reuses these three helpers.
def npc_save_home(r):
    """`AiNpcSaveHome` (0x005E6800): `AiCtlParamGet(10)` is not a boundary, so whether home is unset forks."""
    if r.unknown("h.home unset"):
        r.call("h.idle20", "Idle", n=20)
        return True
    return False


def npc_script_step(r):
    """`AiNpcScriptStep` (0x005E6AE0). The records' words fork; `MonAiWalkToPointCmd` is not a boundary (opaque, and
    whether it succeeds forks); the point a distance is taken to is not compared; `PathSetDir` changes no word compared."""
    R4 = r.call("s.find4", "ParamsFind", U=r.U, kind=4).eax
    if r.br("s.R4", R4 != 0) and r.unknown("s.R4+0x14>0"):
        if r.unknown("s.R4 x,y!=0") and r.br("s.R4 far", u32(r.call("s.pathdist4", "PathDist", u=r.U).eax) > 3):
            r.call("s.ovr4", "Ovr", param=0, byte=0)
            r.opaque("s.WalkPtCmd")
        else:
            r.call("s.idle4", "Idle")
        return True
    R5 = r.call("s.find5", "ParamsFind", U=r.U, kind=5).eax
    if r.br("s.R5", R5 != 0):
        if r.unknown("s.a>0"):
            if r.unknown("s.a odd"):
                r.call("s.ring5", "Ring")
                return True
            if r.unknown("s.R5+0x14>0"):
                r.call("s.idle5", "Idle")
                return True
        elif r.unknown("s.R5+0x14>0#2"):
            r.call("s.idle5b", "Idle")
            return True
    R7 = r.call("s.find7", "ParamsFind", U=r.U, kind=7).eax
    if r.br("s.R7", R7 != 0) and r.unknown("s.m!=0"):
        if r.unknown("s.m not 8..11"):
            r.call("s.idle50", "Idle", n=50)
            return True
        D = s32(r.call("s.pathdist7", "PathDist", u=r.U).eax)
        if r.less("s.0<D", 0, D) and r.unknown("s.R7+0x18>0"):
            r.call("s.ovr7", "Ovr", type=7, param=0, byte=0)
            if not r.unknown("s.walkptcmd"):
                r.opaque("s.WalkPtCmd7")
                r.call("s.idle25", "Idle", n=25)
            else:
                r.opaque("s.WalkPtCmd7")
            return True
        m_zero = r.less("s.1<D", 1, D)
        if r.br("s.class=0x1FF", r.cls == 0x1FF):
            if r.less("s.4<Range", 4, r.rng(100), draw=True):
                r.call("s.idle50b", "Idle", n=50)
                return True
        if not m_zero:
            if r.unknown("s.mode=m"):
                r.call("s.idle50c", "Idle", n=50)
                return True
            r.call("s.setmode", "SetModeAtUnit", t=r.U)
            return True
        if r.br("s.class=0xB2", r.cls == 0xB2):
            r.rng(100)
    return False


def npc_path_pick(r):
    """`AiNpcPathPick` (0x005E7080). The list pointer is the AID line's `ctl` word +0x38; its count and nodes are not
    logged (fork). Running an action (an indirect call, 0x005E6DE0..) stops the decision: the action's own calls are not in
    the block."""
    if not r.br("p.list", r.ctlw(0x38) != 0):
        return False
    if not r.less("p.D100<66", r.d100(), 66, draw=True) or not r.unknown("p.count!=0"):
        return False
    r.step()                                   # k ← RNG_RangeB(U's seed, count): one step, count unknown
    if not r.unknown("p.action runs"):
        return False
    raise Stop("p: a path action is not modelled")


def m_r41(r):
    """R41 Towner."""
    if npc_save_home(r) or npc_script_step(r) or npc_path_pick(r):
        return
    r.call("i.idle12", "Idle", n=12)


# ---- H1d R42 Vendor (catalogue 4279)
def m_r42(r):
    """R42 Vendor."""
    if r.less("1.D100<20", r.d100(), 20, draw=True):
        r.call("1.setmode8", "SetMode", mode=8, x=0, y=0)
    else:
        r.call("1.idle", "Idle", n=30)


# ---- H1d R58 Navi (catalogue 4322)
def m_r58(r):
    """R58 Navi. `NpcInteractAny`, `AiNearestPlayer`, `PlayerIsBusy` and `UnitSetEvent` are not boundaries: their
    results fork, and `UnitSetEvent` is taken to draw nothing."""
    if r.unknown("1.interact"):
        r.call("1.idle10", "Idle", n=10)
        return
    if r.unknown("3.p player not busy"):
        if r.br("3.Range(3)!=0", r.rng(3) != 0) and r.unknown("3.f"):
            v = r.v[0x18]
            if r.br("3.v18=0", v == 0, val=v):
                r.store("set v18=60", 0x18, 60)
            elif r.less("3.v18<0", v, 0):
                r.store("set v18=0", 0x18, 0)
            else:
                r.store("set v18-=1", 0x18, v - 1)
            r.call("3.idle20", "Idle", n=20)
            return
    ret = r.call("4.findhostile", "FindHostile")
    u = ret.eax
    if r.br("5.u", u != 0) and r.less("5.dist<25", s32(ret.out(0)), 25):
        r.call("5.setmode4", "SetModeAtUnit", mode=4, t=u)
        return
    r.call("6.idle50", "Idle", n=50)


# ---- plan 0069 Phase 1c (`lane/n69c`), revision 5: the models of batches H1c, H1g and H1h, transcribed from the catalogue
# blocks at b5999f5e (the catalogue is unchanged from there to 684332ee) like Phase 1b's. A word the logs do not hold forks,
# as in Phase 1b; the H1h models take their rev 7 word from the decision (`r7`) and fork only without it. A target position
# the AID line does not hold (no target) is not compared (`tpos`).

def r7(r, key):
    """Revision 5: the rev 7 word `key` of this decision, or None on a rev 6 log. Phase 2's tools/ai.py puts the words of
    the rev 7 list in `dec["r7"]`, by these keys: `MonPlayerBonus` (R10: the block's `pb.difficulty`), `MonsterOwnerRef`
    (R48: the pair (guid, type) the call writes), `AiNearestPlayer` (R32: the pair (p, f)), `R73.aurastate` (the Skills
    `aurastate` of `Skill2`, or None when `Skill2` is outside the table) and `R73.md0e` (`MonsterData+0x0E`), `owner.mode`
    (R56: the owner's mode at `MonsterOwner`'s return), `found.mode` (R71: the mode of `GameFindUnit`'s unit)."""
    return (r.dec.get("r7") or {}).get(key)


def known(r, name, key, test):
    """A branch on the rev 7 word `key`: `test(word)` when the decision holds it, else a fork."""
    w = r7(r, key)
    if w is None:
        return r.unknown(name)
    return r.br(name, test(w), val=w)


def tpos(r):
    """t's x, y (the AID line's `t`), None without a target."""
    return r.tx, r.ty


def add(a, b):
    return None if a is None or b is None else u32(a + b)


def tdiv(a, b):
    """Signed 32-bit division toward zero (`idiv`, `cdq`)."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def store_unknown(r, name, key):
    """A store of a value the log does not hold (a found unit's guid): the word is not compared after it (None). The flip
    control skips it, so the old word is compared."""
    r.arms.append((name, True))
    if name != r.flip:
        r.v[key] = None


def clamp(r, lb, v, lo, hi):
    """`clamp(v, lo, hi)` as two named compares."""
    if r.less(lb + ".v<" + str(lo), v, lo):
        return lo
    if r.less(lb + "." + str(hi) + "<v", hi, v):
        return hi
    return v


# ---- H1g R7 Brute, and the Reimplementation notes row (catalogue 517: row 7's second aip(3) draw)
def m_r7(r):
    """R7 Brute. The notes row is this block's step 3."""
    if not r.br("1.melee", r.melee):
        p = clamp(r, "1.p", s32(r.call("1.lifepct", "UnitLifePct", u=r.U).eax), 40, 100)
        r.call("1.ovr", "Ovr", type=0, param=100 - p, byte=0)
        r.call("1.walk13", "Walk13", t=r.t, flags=7)
        return
    if r.chance("2.chance(3)", 3):
        r.call("2.setmode", "SetModeAtUnit", mode=4 if r.chance("2.chance(4)", 4) else 5, t=r.t)
        return
    if r.chance("3.chance(3)", 3):
        r.call("3.t56", "T56", t=r.t, byte=4, flag=0)
        return
    r.call("4.idle", "Idle", n=15)


# ---- H1h R10 CorruptRogue (catalogue 300; MonPlayerBonus 0x00573930, rev 7 item 8)
def m_r10(r):
    """R10 CorruptRogue. `MonPlayerBonus` is not a boundary: `pb.difficulty` is the rev 7 word `MonPlayerBonus`; without it
    step 2 forks. With it, `VALS 2.pb=min(d,2)` lists whether it equals the block's comment."""
    r.call("1.room", "UnitGetRoom", u=r.U)
    pd = r7(r, "MonPlayerBonus")
    if pd is not None:
        r.vals.append(("2.pb=min(d,2)", pd == min(r.aid["diff"], 2)))
        far = r.less("2.20-3pb<dist", 20 - 3 * s32(pd), r.dist)
    else:
        far = r.unknown("2.far")
    if far:
        r.call("2.ovr", "Ovr", type=13, param=r.aip(4), byte=0)
        r.call("2.runstop", "RunStop", t=r.t, stop=3)
        return
    if r.br("3.melee", r.melee):
        if r.chance("3.chance(3)", 3):
            r.call("3.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        r.call("3.idle", "Idle", n=r.aip(2))
        return
    if not r.chance("4.chance(1)", 1):
        r.call("4.idle", "Idle", n=r.aip(2))
        return
    if r.chance("5.chance(5)", 5):
        r.call("5.ovr", "Ovr", type=13, param=r.aip(4), byte=0)
        r.call("5.runstop", "RunStop", t=r.t, stop=3)
        return
    r.call("6.walk", "Walk", t=r.t, flags=7)


# ---- H1g R11 Baboon (catalogue 330)
def m_r11(r):
    """R11 Baboon. The run bonus is read from MonStats `Velocity` and `Run`, which the log does not hold: it is used only as
    the override's parameter, which is not compared. `UnitSetStat` is not a boundary (it draws nothing, taken)."""
    life = s32(r.call("1.lifepct", "UnitLifePct", u=r.U).eax)
    bonus = None
    if r.br("3.v14=0", r.v[0x14] == 0, val=r.v[0x14]):
        if not r.br("3.melee", r.melee):
            r.call("3.walk13", "Walk13", t=r.t, flags=7)
            return
        if r.br("3.St3or19", r.call("3.st3or19", "St3or19", U=r.U).eax):
            if r.less("3.life<aip(1)", life, r.aip(1)) and r.rchance("3.Range<50", 100, 50):
                r.store("set v14=Range(5)+2", 0x14, r.rng(5) + 2)
                s = s32(r.call("3.stat74", "StatsGetUnitStat", s1=r.U, s2=74, s3=0).eax)
                r.store("set v1c", 0x1C, tdiv(s32(r.aip(5) * s), 8) if r.br("3.s!=0", s != 0) else 0)
                r.call("3.ovr", "Ovr", type=2, param=bonus, byte=0)
                r.call("3.stepaway", "StepAway", t=r.t, d=15, flag=0)
                return
            if r.br("3.v18!=0", r.v[0x18] != 0) and r.rchance("3.Range<20", 100, 20):
                r.call("3.t56", "T56", t=r.t, byte=3, flag=0)
                r.store("set v18=0", 0x18, 0)
                return
        if r.br("3.v18!=0#2", r.v[0x18] != 0) and not r.chance("3.chance(3)", 3):
            if r.rchance("3.Range<aip(2)", 100, r.aip(2)):
                r.call("3.t56b", "T56", t=r.t, byte=3, flag=0)
                r.store("set v18=0#2", 0x18, 0)
            r.call("3.idle", "Idle", n=15)
            return
        r.store("set v18=1", 0x18, 1)
        r.call("3.setmode", "SetModeAtUnit", mode=4 if r.chance("3.chance(4)", 4) else 5, t=r.t)
        return
    r.store("set v14-=1", 0x14, r.v[0x14] - 1)
    r.store("set v18=0#3", 0x18, 0)
    if r.br("5.v14=0", r.v[0x14] == 0) or r.less("5.75<life", 75, life):
        r.call("5.stat74", "StatsGetUnitStat", s1=r.U, s2=74, s3=0)
    if not r.br("6.melee", r.melee):
        if r.less("6.75<life", 75, life):
            r.store("set v14=0", 0x14, 0)
            r.call("6.ovr", "Ovr", type=13, param=bonus, byte=0)
            r.call("6.walk13", "Walk13", t=r.t, flags=7)
            return
    elif r.less("6.D100<33", r.d100(), 33, draw=True):
        r.call("6.setmode", "SetModeAtUnit", mode=4 if r.chance("6.chance(4)", 4) else 5, t=r.t)
        return
    if r.less("7.23<dist", 23, r.dist) and not r.br("7.St3or19", r.call("7.st3or19", "St3or19", U=r.U).eax):
        if r.rchance("7.Range<33", 100, 33):
            r.call("7.t56", "T56", t=r.t, byte=4, flag=0)
        r.call("7.idle", "Idle", n=20)
        return
    r.call("8.ovr", "Ovr", type=2, param=bonus, byte=0)
    if not r.br("8.stepped", r.call("8.stepaway", "StepAway", t=r.t, d=15, flag=1).eax):
        if not r.br("8.melee", r.melee):
            r.call("8.ring", "Ring", r=5)
            return
        r.call("8.setmode", "SetModeAtUnit", mode=4 if r.rchance("8.Range<aip(4)", 100, r.aip(4)) else 5, t=r.t)


# ---- H1g R14 QuillRat (catalogue 410)
def m_r14(r):
    """R14 QuillRat. The head record's `+0x0C` and `+0x10` are the AID line's `head` words 3 and 4. The ring argument is
    the target pointer with its low byte replaced (R14a)."""
    rec = r.call("1.head", "ParamsHead", U=r.U).eax
    if r.br("1.rec", rec != 0):
        hw = r.head or [None] * 7
        if r.br("1.found", r.call("1.find", "GameFindUnit", type=hw[3], guid=hw[4]).eax != 0):
            r.call("1.setmode5", "SetModeAtUnit", mode=5, t=r.t)
            r.call("1.pop", "ParamsPop")
            return
        r.call("1.pop2", "ParamsPop")
    if r.br("2.melee", r.melee):
        r.call("2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    if r.br("3.St3or19", r.call("3.st3or19", "St3or19", U=r.U).eax):
        r.call("3.setmode5", "SetModeAtUnit", mode=5, t=r.t)
        return
    if r.less("4.dist<aip(1)", r.dist, r.aip(1)):
        if r.chance("4.chance(2)", 2):
            r.call("4.setmode5", "SetModeAtUnit", mode=5, t=r.t)
            return
        if r.br("4.stepped", r.call("4.stepaway", "StepAway", t=r.t, d=r.aip(4) & 0xFF, flag=1).eax):
            return
        if r.less("4.dist<4", r.dist, 4):
            r.call("4.setmode5b", "SetModeAtUnit", mode=5, t=r.t)
            return
    ring = 3 if r.less("5.aip(4)<3", r.aip(4), 3) else r.aip(4) & 0xFF
    r.call("5.ring", "Ring", r=(u32(r.t) & 0xFFFFFF00) | ring)


# ---- H1g R33 HellMeteor (catalogue 934)
def m_r33(r):
    """R33 HellMeteor. U's position is the AID line's x, y."""
    if r.br("1.Skill1>=0", r.skill[0] >= 0) and r.chance("1.chance(1)", 1):
        a = r.aip(3)
        x = r.x + r.rng(2 * a) - a
        y = r.y + r.rng(2 * a) - a
        use_skill(r, "1.useskill1", 1, 0, x=u32(x), y=u32(y))
        return
    r.call("2.idle", "Idle", n=r.aip(2))


# ---- H1g R36 CorruptLancer (catalogue 956)
def m_r36(r):
    """R36 CorruptLancer. `MeleeRng` (MonStats2 +0x0E) and the path are not logged: `PathSetStopDist`'s words and
    `RunStop`'s stop distance are not compared."""
    if r.less("1.aip(5)<dist", r.aip(5), r.dist):
        r.call("1.stopdist", "PathSetStopDist")
        r.call("1.ovr", "Ovr", type=13, param=100, byte=0)
        r.call("1.runstop", "RunStop", t=r.t)
        r.store("set v14=1", 0x14, 1)
        return
    if not r.br("2.melee", r.melee):
        if not r.chance("2.chance(1)", 1):
            r.call("2.idle", "Idle", n=r.aip(3))
            return
        r.call("2.stopdist", "PathSetStopDist")
        if not r.chance("2.chance(4)", 4):
            r.call("2.walkstop", "WalkStop", t=r.t, n=3)
            return
        r.call("2.ovr", "Ovr", type=13, param=100, byte=0)
        r.call("2.runstop", "RunStop", t=r.t)
        return
    if r.br("3.v14=0", r.v[0x14] == 0, val=r.v[0x14]) and not r.chance("3.chance(2)", 2):
        r.call("3.idle", "Idle", n=r.aip(3))
        return
    r.store("set v14=0", 0x14, 0)
    if r.br("5.Skill1>=0", r.skill[0] >= 0) and r.chance("5.chance(6)", 6):
        use_skill(r, "5.useskill1", 1, r.t)
        return
    if r.br("6.Skill2>=0", r.skill[1] >= 0) and r.rchance("6.Range<aip(7)", 100, r.aip(7)):
        use_skill(r, "6.useskill2", 2, r.t)
        return
    if r.br("7.Skill3>=0", r.skill[2] >= 0) and r.rchance("7.Range<aip(8)", 100, r.aip(8)):
        use_skill(r, "7.useskill3", 3, r.t)
        return
    r.call("8.setmode4", "SetModeAtUnit", mode=4, t=r.t)


# ---- H1c R38 MaggotLarva (catalogue 986)
def m_r38(r):
    """R38 MaggotLarva."""
    if not r.br("1.melee", r.melee):
        r.store("set v14=0", 0x14, 0)
        if r.chance("1.chance(3)", 3):
            r.call("1.walk", "Walk", t=r.t, flags=1)
            return
        r.call("1.idle", "Idle", n=r.aip(4))
        return
    if r.br("2.v14=0", r.v[0x14] == 0, val=r.v[0x14]) and r.chance("2.chance(1)", 1):
        r.store("set v14=1", 0x14, 1)
        r.call("2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    r.store("set v14=0#2", 0x14, 0)
    r.call("3.idle", "Idle", n=r.aip(2))


# ---- H1g R39 PinHead (catalogue 1006)
def m_r39(r):
    """R39 PinHead."""
    if not r.br("1.melee", r.melee):
        r.store("set v14=0", 0x14, 0)
        if r.chance("1.chance(3)", 3):
            r.call("1.walk", "Walk", t=r.t, flags=7)
            return
        r.call("1.idle", "Idle", n=r.aip(4))
        return
    if r.br("2.v14!=0", r.v[0x14] != 0, val=r.v[0x14]) and not r.chance("2.chance(1)", 1):
        r.call("2.idle", "Idle", n=r.aip(2))
        return
    r.store("set v14=1", 0x14, 1)
    if r.br("4.Skill1>=0", r.skill[0] >= 0) and r.chance("4.chance(5)", 5):
        use_skill(r, "4.useskill1", 1, r.t)
        return
    if r.br("5.Skill2>=0", r.skill[1] >= 0) and r.chance("5.chance(6)", 6):
        use_skill(r, "5.useskill2", 2, r.t)
        return
    r.call("6.setmode4", "SetModeAtUnit", mode=4, t=r.t)


# ---- H1g R40 MaggotEgg (catalogue 1028)
def m_r40(r):
    """R40 MaggotEgg. `UnitKilled`'s words are revision 3's positional names: ECX the game, EDX the unit, then the killer
    and 1 (the block's order)."""
    if (r.br("1.Skill1>=0", r.skill[0] >= 0) and r.br("1.v14!=1", r.v[0x14] != 1, val=r.v[0x14])
            and r.chance("1.chance(2)", 2)):
        use_skill(r, "1.useskill1", 1, r.t)
        r.call("1.delay", "Delay", n=r.aip(1))
        r.store("set v14=1", 0x14, 1)
        return
    if r.br("2.v14=1", r.v[0x14] == 1):
        k = r.call("2.gettarget", "GetTargetUnit").eax
        r.call("2.killed", "UnitKilled", c=r.G, d=r.U, s1=k, s2=1)
    r.call("3.idle", "Idle", n=r.aip(1))


# ---- H1c R45 Sarcophagus (catalogue 1072)
def m_r45(r):
    """R45 Sarcophagus, the think (its init 0x005F6630 is not a think call). U's position is the AID line's x, y."""
    if r.less("1.25<dist", 25, r.dist):
        r.call("1.idle", "Idle", n=25)
        return
    if r.less("2.aip(3)<v18", r.aip(3), r.v[0x18]):
        r.store("set c4|=0x20000", "c4", r.c4 | 0x20000)
        r.call("2.die", "SetMode", mode=0, x=0, y=0)
        return
    e = s32(r.T - r.v[0x14])
    if e < 0:
        e = s32(-e)
    if r.br("4.Skill1>=0", r.skill[0] >= 0) and not r.less("4.e<aip(1)", e, r.aip(1)):
        cls = 228 if r.ms2 > 228 else -1
        room = r.call("4.room", "UnitGetRoom", u=r.U).eax
        if r.br("4.cell", r.call("4.celltest", "SpawnClassCellTest", cls=cls, room=room, x=r.x, y=r.y, z=0).eax):
            r.store("set v18+=1", 0x18, r.v[0x18] + 1)
            r.store("set v14=T", 0x14, r.T)
            use_skill(r, "4.useskill1", 1, r.t)
            return
    low = r.step()
    r.call("5.idle", "Idle", n=20 + low % 10)


# ---- H1h R48 ZakarumZealot (catalogue 1138; MonsterOwnerRef 0x0058F090, rev 7 item 10)
def m_r48(r):
    """R48 ZakarumZealot. The run bonus (MonStats `Velocity`, `Run`) is not logged: the override's parameter is not
    compared. `MonsterOwnerRef` is not a boundary: its (guid, type) is the rev 7 word `MonsterOwnerRef`, else the type
    forks and the guid is not compared. `DRLG_ActFromLevelId` and `QUESTRECORD_GetState` are not boundaries: they fork.
    `COLL_CellTestAt`'s words are not compared (revision 3's caller read names one stack word for the block's four)."""
    run = None
    life = s32(r.call("2.lifepct", "UnitLifePct", u=r.U).eax)
    if r.br("3.t", r.t != 0):
        p, ptype0 = r.t, r.ttype == 0
        if r.br("3.t.type=1", r.ttype == 1, val=r.ttype):
            w = r7(r, "MonsterOwnerRef")
            if w is not None:
                own0 = r.br("3.ownertype=0", w[1] == 0, val=w[1])
                guid = w[0]
            else:
                own0, guid = r.unknown("3.ownertype=0"), None
            if own0:
                p = r.call("3.find", "GameFindUnit", type=0, guid=guid).eax
                ptype0 = True                           # a unit found by type 0
        if r.br("3.p", p != 0) and r.br("3.p.type=0", ptype0):
            room = r.call("3.room", "UnitGetRoom", u=r.U).eax
            r.call("3.level", "RoomGetLevelId", room=room)
            if r.unknown("3.act=2"):
                r.call("3.pdata", "UnitGetPlayerData", s1=p)
                if r.unknown("3.quest21"):
                    r.call("3.ovr", "Ovr", type=0, param=run, byte=0)
                    if r.br("3.stepped", r.call("3.stepaway", "StepAwayXY", t=r.t, n=8, f=1).eax):
                        return
                    r.call("3.ring", "Ring", r=6)
                    return
    if r.br("4.St3or19", r.call("4.st3or19", "St3or19", U=r.U).eax):
        if r.br("4.v18=0", r.v[0x18] == 0, val=r.v[0x18]) and r.less("4.life<aip(3)", life, r.aip(3)):
            r.store("set v14=0", 0x14, 0)
            r.call("4.ovr", "Ovr", type=0, param=run, byte=0)
            if r.br("4.stepped", r.call("4.stepaway", "StepAwayXY", t=r.t, n=8, f=1).eax):
                return
            r.store("set v18=5", 0x18, 5)
        room = r.call("4.room", "UnitGetRoom", u=r.U).eax
        if r.br("4.cell", r.call("4.celltest", "CollCellTestAt").eax):
            if r.br("4.melee", r.melee):
                r.call("4.t56", "T56", t=r.t, byte=4, flag=0)
            else:
                r.call("4.walk", "Walk", t=r.t, flags=7)
            return
    if r.br("5.v18!=0", r.v[0x18] != 0):
        r.store("set v18-=1", 0x18, r.v[0x18] - 1)
    if not r.br("6.melee", r.melee):
        r.store("set v14=0#2", 0x14, 0)
        if not r.chance("6.chance(4)", 4):
            r.call("6.walk", "Walk", t=r.t, flags=7)
            return
        r.call("6.ovr", "Ovr", type=0, param=run, byte=0)
        r.call("6.run", "RunToUnit", t=r.t)
        return
    if r.br("7.v14!=0", r.v[0x14] != 0, val=r.v[0x14]) and not r.chance("7.chance(1)", 1):
        r.store("set v14=0#3", 0x14, 0)
        if r.rchance("7.Range<80", 100, 80):
            r.call("7.idle", "Idle", n=10)
            return
        r.call("7.t56", "T56", t=r.t, byte=4, flag=0)
        return
    r.store("set v14=1", 0x14, 1)
    r.call("9.setmode", "SetModeAtUnit", mode=5 if r.chance("9.chance(2)", 2) else 4, t=r.t)


# ---- H1g R49 ZakarumPriest (catalogue 1188; AiZakarumHealCb 0x005F7240)
def m_r49(r):
    """R49 ZakarumPriest. U's position is the AID line's x, y and t's its `t` words; the offset is taken as a 32-bit
    difference (R49a: a u16 difference that `<< 2` cannot wrap)."""
    life = s32(r.call("1.lifepct", "UnitLifePct", u=r.U).eax)
    melee = r.br("2.melee", r.melee)
    if melee or r.br("2.St3or19", r.call("2.st3or19", "St3or19", U=r.U).eax):
        if (r.br("2.Skill3>=0", r.skill[2] >= 0) and r.less("2.life<33", life, 33)
                and r.less("2.v14<T", r.v[0x14], r.T)):
            r.store("set v14=T+4aip(5)", 0x14, r.T + 4 * r.aip(5))
            s = 2 if melee else 0
            tx, ty = tpos(r)
            x = None if tx is None else u32(tx + ((tx - r.x) << s))
            y = None if ty is None else u32(ty + ((ty - r.y) << s))
            if r.br("2.targetok", r.call("2.targetok", "SkillTargetOk", skill=r.skill[2], u=0, a=x, b=y).eax):
                use_skill(r, "2.useskill3", 3, 0, x=x, y=y)
                return
        if melee and r.chance("2.chance(1)", 1):
            r.call("2.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
    ret = r.call("3.search", "UnitSearch", cb=0x005F7240, kind=1,
                 blk={0: {0: 0, 1: 0, 2: 0x7FFFFFFF, 3: r.aip(6) * r.aip(6)}})
    unit = ret.out(0, 0)
    if (r.br("4.Skill1>=0", r.skill[0] >= 0) and r.br("4.unit", unit != 0)
            and r.less("4.D100<25", r.d100(), 25, draw=True)):
        use_skill(r, "4.useskill1", 1, unit)
        return
    blizzard = False
    if not r.br("5.clear", r.call("5.lineclear", "AiLineClear", c=r.U, d=r.t).eax):
        if (r.chance("5.chance(1)", 1) and r.br("5.Skill4>=0", r.skill[3] >= 0) and r.less("5.v18<T", r.v[0x18], r.T)
                and r.rchance("5.Range<aip(2)", 100, r.aip(2))):
            blizzard = True
    elif r.chance("5.chance(4)", 4):
        if (r.br("5.Skill4>=0#2", r.skill[3] >= 0) and r.less("5.v18<T#2", r.v[0x18], r.T)
                and r.rchance("5.Range<aip(2)#2", 100, r.aip(2))):
            blizzard = True
        elif (r.br("5.Skill2>=0", r.skill[1] >= 0) and r.less("5.v1C<T", r.v[0x1C], r.T)
              and r.rchance("5.Range<aip(3)", 100, r.aip(3))):
            use_skill(r, "5.useskill2", 2, r.t)
            r.store("set v1c=T+20", 0x1C, r.T + 20)
            return
    if blizzard:
        use_skill(r, "5.useskill4", 4, r.t)
        r.store("set v18=T+aip(5)", 0x18, r.T + r.aip(5))
        return
    if r.less("6.D100<30", r.d100(), 30, draw=True):
        r.call("6.t56", "T56", t=r.t, byte=4, flag=0)
        return
    r.call("7.idle", "Idle", n=20)


# ---- H1c R50 Mephisto (catalogue 2633; AiMephistoPickTarget 0x005F77C0)
def m_r50(r):
    """R50 Mephisto. `AiMephistoPickTarget` is a boundary: its words are revision 3's positional names, compared as the
    block's (G, U, M, t). The difficulty tests are `d > 0` (`jbe`)."""
    life = s32(r.call("1.lifepct", "UnitLifePct", u=r.U).eax)
    L = tdiv(100 - life, 5)
    if r.less("1.L<0", L, 0):
        L = 0
    st = r.v[0x1C]
    move = False
    if r.br("2.melee", r.melee):
        if r.less("2.aip(1)<D100", r.aip(1), r.d100(), draw=True):
            st = 3
        else:
            st = 2
            r.store("set v14=step%3+3", 0x14, r.step() % 3 + 3)
    elif r.less("2.20<dist", 20, r.dist):
        st = 4
    elif r.br("2.v1C>4u", u32(r.v[0x1C]) > 4, val=r.v[0x1C]):
        move = True
    elif r.br("2.v1C=0", r.v[0x1C] == 0):
        if (not r.less("2.20<life", 20, life) and r.less("2.dist<5", r.dist, 5)
                and r.less("2.D100<40", r.d100(), 40, draw=True)):
            st = 1
        elif r.less("2.D100<L+50", r.d100(), L + 50, draw=True):
            st = 2
            r.store("set v14=step%3+3#2", 0x14, r.step() % 3 + 3)
        else:
            move = True
    if move:
        if not r.less("m.D100<65", r.d100(), 65, draw=True):
            r.store("set v1c=0", 0x1C, 0)
            r.call("m.idle", "Idle", n=10)
            return
        if not r.less("m.D100<65#2", r.d100(), 65, draw=True) and not r.less("m.5<dist", 5, r.dist):
            r.call("m.ovr", "Ovr", type=0, param=0, byte=4)
            r.call("m.walk", "Walk", t=r.t, flags=7)
        else:
            r.call("m.t56", "T56", t=r.t, byte=4, flag=0)
        r.store("set v1c=0#2", 0x1C, 0)
        return
    r.vals.append(("3.st", st))
    if st == 0:
        r.call("c0.idle", "Idle", n=5)
        r.store("set v1c=4", 0x1C, 4)
        return
    if st == 1:
        r.call("c1.ovr", "Ovr", type=0, param=50, byte=0)
        if r.br("c1.stepped", r.call("c1.stepaway", "StepAway", t=r.t, d=8, flag=1).eax):
            r.store("set v1c=0#3", 0x1C, 0)
            return
        if r.br("c1.melee", r.melee):
            use_skill(r, "c1.useskill3", 3, r.t)
            r.store("set v1c=0#4", 0x1C, 0)
            return
        st = 0
    if st in (0, 2):
        r.store("set v14-=1", 0x14, r.v[0x14] - 1)
        if r.br("c2.v14=0", r.v[0x14] == 0):
            st = 0
        if r.br("c2.v18=0", r.v[0x18] == 0, val=r.v[0x18]):
            r.store("set v18=2", 0x18, 2)
            if not r.br("c2.t56", r.call("c2.t56", "T56", t=r.t, byte=3, flag=1).eax):
                r.call("c2.ring12", "Ring", r=12)
            r.store("set v1c=st", 0x1C, st)
            return
        r.store("set v18+=1", 0x18, r.v[0x18] + 1)
        t2 = r.call("c2.pick", "AiMephistoPickTarget", c=r.G, d=r.U, s1=r.ms, s2=r.t).eax
        n = 0
        while n < 8 and r.skill[n] >= 0:
            n += 1
        if r.less("c2.n<=0", n, 1):
            r.call("c2.ring6", "Ring", r=6)
        else:
            q = 100 // n
            rr = r.d100()
            dd = r.br("c2.d>0", diff(r) > 0)
            if dd and ((r.br("c2.t2", t2 != 0)
                        and r.br("c2.blocked", r.call("c2.blocked", "UnitLineBlocked", s1=r.U, s2=t2, s3=4).eax))
                       or r.less("c2.30<dist", 30, r.dist)):
                use_skill(r, "c2.useskill6", 6, t2)
            elif r.less("c2.dist<15", r.dist, 15) and r.less("c2.r<q", rr, q, draw=True) and r.br("c2.d>0#2", diff(r) > 0):
                use_skill(r, "c2.useskill5", 5, t2)
            elif r.less("c2.r<2q", rr, 2 * q, draw=True):
                use_skill(r, "c2.useskill4", 4, t2)
            elif r.less("c2.r<3q", rr, 3 * q, draw=True):
                use_skill(r, "c2.useskill2", 2, t2)
            else:
                use_skill(r, "c2.useskill1", 1, t2)
        if r.less("c2.D100<50-L", r.d100(), 50 - L, draw=True):
            r.store("set v18=0", 0x18, 0)
        r.store("set v1c=st#2", 0x1C, st)
        return
    if st == 3:
        if r.rchance("c3.Range<L+80", 100, L + 80):
            if r.rchance("c3.Range<80-L", 100, 80 - L):
                r.call("c3.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            else:
                use_skill(r, "c3.useskill3", 3, r.t)
        else:
            r.call("c3.ovr", "Ovr", type=0, param=50, byte=0)
            if not r.br("c3.t56", r.call("c3.t56", "T56", t=r.t, byte=3, flag=1).eax):
                r.call("c3.ring12", "Ring", r=12)
        r.store("set v1c=0#5", 0x1C, 0)
        return
    if st == 4:
        r.call("c4.ovr", "Ovr", type=0, param=50, byte=0)
        if not r.br("c4.wander", r.call("c4.wander", "WanderNear", u=r.t, r=6).eax):
            r.call("c4.cancel", "CancelEvents", kind=2, z=0)
            if not r.br("c4.toward", r.call("c4.toward", "Toward", t=r.t, max=12, ring=6).eax):
                r.call("c4.ring12", "Ring", r=12)
        r.store("set v1c=0#6", 0x1C, 0)
        return
    raise Stop("3: the dispatch word %d is outside the five-word table" % st)


# ---- H1c R53 Summoner (catalogue 2703)
def m_r53(r):
    """R53 Summoner. `UseSkillK(a)` here takes t's x, y (the AID line's `t`). `A2Q5_BossSeen`'s words are not compared
    (revision 3's names are positional and the block gives two for its five)."""
    tx, ty = tpos(r)

    def sk(lb, k, a):
        use_skill(r, lb, k, a, x=tx, y=ty)
    if r.br("1.v14=0", r.v[0x14] == 0, val=r.v[0x14]):
        r.call("1.seen", "A2Q5_BossSeen")
        r.store("set v14=1", 0x14, 1)
    if r.less("2.dist<5", r.dist, 5) and r.less("2.D100<aip(6)", r.d100(), r.aip(6), draw=True):
        r.call("2.stepaway", "StepAway", t=r.t, d=6, flag=0)
    a = s32(r.call("3.cold", "StatsGetUnitStat", s1=r.t, s2=43, s3=0).eax)
    b = s32(r.call("3.fire", "StatsGetUnitStat", s1=r.t, s2=39, s3=0).eax)
    cold = not r.less("3.fire<cold", b, a)
    if r.less("4.D100<aip(1)", r.d100(), r.aip(1), draw=True):
        if r.br("4.Skill5>=0", r.skill[4] >= 0) and r.less("4.D100<aip(2)", r.d100(), r.aip(2), draw=True):
            sk("4.useskill5", 5, r.t)
            return
        t2 = r.call("4.findhostile", "FindHostile", pm=0).eax
        if r.less("4.aip(3)<D100", r.aip(3), r.d100(), draw=True):
            cold = not cold
        nova = False
        if r.br("4.cold", cold):
            if (r.br("4.Skill2>=0", r.skill[1] >= 0) and r.less("4.v18<T", r.v[0x18], r.T)
                    and r.less("4.dist<aip(7)", r.dist, r.aip(7))):
                nova = True
            elif (r.br("4.Skill1>=0", r.skill[0] >= 0) and r.br("4.t2", t2 != 0)
                  and r.less("4.dist<aip(8)", r.dist, r.aip(8))):
                sk("4.useskill1", 1, t2)
                return
        if not nova:
            if r.br("4.Skill4>=0", r.skill[3] >= 0) and r.less("4.v1C<T", r.v[0x1C], r.T):
                r.store("set v1c=T+aip(5)", 0x1C, r.T + r.aip(5))
                sk("4.useskill4", 4, r.t)
                return
            if (r.br("4.Skill3>=0", r.skill[2] >= 0) and r.br("4.t2#2", t2 != 0)
                    and r.less("4.dist<aip(8)#2", r.dist, r.aip(8))):
                sk("4.useskill3", 3, t2)
                return
            if (not cold and r.br("4.Skill2>=0#2", r.skill[1] >= 0) and r.less("4.v18<T#2", r.v[0x18], r.T)
                    and r.less("4.dist<aip(7)#2", r.dist, r.aip(7))):
                nova = True
        if nova:
            r.store("set v18=T+aip(4)", 0x18, r.T + r.aip(4))
            sk("4.useskill2", 2, r.t)
            return
        if r.br("4.Skill5>=0#2", r.skill[4] >= 0):
            sk("4.useskill5b", 5, r.t)
            return
    r.call("5.ring", "Ring", r=4)


# ---- H1c R55 Izual (catalogue 2735)
def m_r55(r):
    """R55 Izual. The cast's x, y are read by the getters at the think's entry (0x005F89F1, 0x005F8A29), of a unit the
    block does not name: not compared. `aidel` is logged for Normal only (AID `ad[0]`): its idles are compared in Normal."""
    aidel = r.aid["ad"][0] if r.aid["diff"] == 0 and r.aid.get("ad") else None

    def cast():
        use_skill(r, "c.useskill1", 1, r.t, x=None, y=None)
        r.store("set v18=aip(5)", 0x18, r.aip(5))
        r.store("set v1c=aip(6)", 0x1C, r.aip(6))
    if r.br("1.v14=0", r.v[0x14] == 0, val=r.v[0x14]):
        r.store("set v14=1", 0x14, 1)
        r.call("1.seen", "A4Q1_IzualSeen", c=r.G)
    if r.br("2.v18!=0", r.v[0x18] != 0, val=r.v[0x18]):
        r.call("2.idle", "Idle", n=r.v[0x18])
        r.store("set v18=0", 0x18, 0)
        return
    if r.br("3.melee", r.melee):
        if r.less("3.v1C<1", r.v[0x1C], 1) and not r.less("3.D100<aip(1)", r.d100(), r.aip(1), draw=True):
            r.store("set v1c=0", 0x1C, 0)
            if not r.br("3.Skill1>=0", r.skill[0] >= 0) or not r.rchance("3.Range<aip(4)", 100, r.aip(4)):
                r.call("3.idle", "Idle", n=aidel)
                return
            cast()
            return
        if r.less("3.0<v1C", 0, r.v[0x1C]):
            r.store("set v1c-=1", 0x1C, r.v[0x1C] - 1)
        r.call("3.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    if r.br("4.Skill1>=0", r.skill[0] >= 0) and r.less("4.dist<10", r.dist, 10):
        if r.less("4.0<v1C", 0, r.v[0x1C]):
            r.call("4.walk", "Walk", t=r.t, flags=7)
            return
        if r.rchance("4.Range<aip(3)", 100, r.aip(3)):
            cast()
            return
    if r.less("5.v1C<1", r.v[0x1C], 1) and not r.less("5.D100<aip(2)", r.d100(), r.aip(2), draw=True):
        if r.less("5.dist<11", r.dist, 11):
            r.call("5.idle", "Idle", n=aidel)
        else:
            r.call("5.toward", "Toward", t=r.t, max=6, ring=9)
        return
    r.call("6.walk", "Walk", t=r.t, flags=7)


# ---- H1g R56 Tentacle (catalogue 1274)
def m_r56(r):
    """R56 Tentacle. The owner's mode is not logged: the rev 7 word `owner.mode` (proposed), else its tests fork."""
    o = r.call("1.owner", "MonsterOwner", U=r.U).eax
    if not r.br("2.o", o != 0):
        r.call("2.killed", "UnitKilled", c=r.G, d=r.U, s1=0, s2=1)
        return
    if known(r, "3.o.mode=12", "owner.mode", lambda m: m == 12) and r.less("3.D100<40", r.d100(), 40, draw=True):
        k = r.call("3.gettarget", "GetTargetUnit", _edx=o).eax
        r.call("3.killed", "UnitKilled", c=r.G, d=r.U, s1=k, s2=1)
        return

    def submerge(lb):
        use_skill(r, lb + ".useskill1", 1, r.t)
        r.call(lb + ".delay8", "Delay", n=8)
        r.store("set v18=T+25aip(3)", 0x18, r.T + 25 * r.aip(3))
        r.store("set v1c=1", 0x1C, 1)
    if r.br("4.Skill1>=0", r.skill[0] >= 0):
        if r.br("4.v1C=0", r.v[0x1C] == 0, val=r.v[0x1C]):
            submerge("4a")
            return
        if (r.br("4.v1C=2", r.v[0x1C] == 2) and r.less("4.v18<T", r.v[0x18], r.T)
                and (r.less("4.aip(6)<dist", r.aip(6), r.dist)
                     or (not r.br("4.melee", r.melee) and r.rchance("4.Range<aip(2)", 100, r.aip(2)))
                     or (known(r, "4.o.mode=14", "owner.mode", lambda m: m == 14) and r.rchance("4.Range<50", 100, 50)))):
            submerge("4b")
            return
    act = False
    if r.br("5.Skill2>=0", r.skill[1] >= 0):
        if not r.br("5.v1C=1", r.v[0x1C] == 1):
            act = True
        elif (r.less("5.v18<T", r.v[0x18], r.T)
              and (r.br("5.melee", r.melee) or r.less("5.dist<aip(6)", r.dist, r.aip(6))
                   or (not known(r, "5.o.mode=14", "owner.mode", lambda m: m == 14)
                       and r.rchance("5.Range<5", 100, 5)))):
            r.call("5.useskill2", "UseSkill", mode=r.skmode[1], skill=r.skill[1], t=r.U, x=0, y=0)
            r.store("set v18=T+25aip(4)", 0x18, r.T + 25 * r.aip(4))
            r.store("set v1c=2", 0x1C, 2)
            return
    if not act and r.br("6.v1C=1", r.v[0x1C] == 1):
        r.call("6.delay", "Delay", n=r.aip(5))
        return
    if r.br("7.melee", r.melee) and r.rchance("7.Range<aip(1)", 100, r.aip(1)):
        r.call("7.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    r.call("8.idle", "Idle", n=r.aip(5))


# ---- H1g R57 TentacleHead (catalogue 1306)
def m_r57(r):
    """R57 TentacleHead."""
    if r.br("1.Skill1>=0", r.skill[0] >= 0):
        armed = False
        if r.br("1.v1C=0", r.v[0x1C] == 0, val=r.v[0x1C]):
            use_skill(r, "1.useskill1", 1, r.t)
            r.call("1.delay8", "Delay", n=8)
            armed = True
        elif (r.br("1.v1C=2", r.v[0x1C] == 2) and r.less("1.v18<T", r.v[0x18], r.T)
              and (r.less("1.aip(6)<dist", r.aip(6), r.dist)
                   or (not r.br("1.melee", r.melee) and r.rchance("1.Range<aip(2)", 100, r.aip(2))))):
            use_skill(r, "1.useskill1b", 1, r.t)
            r.call("1.delay20", "Delay", n=20)
            armed = True
        if armed:
            r.store("set v18=T+25aip(3)", 0x18, r.T + 25 * r.aip(3))
            r.store("set v1c=1", 0x1C, 1)
            return
    if (r.br("2.Skill2>=0", r.skill[1] >= 0) and r.br("2.v1C=1", r.v[0x1C] == 1) and r.less("2.v18<T", r.v[0x18], r.T)
            and (r.br("2.melee", r.melee) or r.less("2.dist<aip(6)", r.dist, r.aip(6)))):
        r.call("2.useskill2", "UseSkill", mode=r.skmode[1], skill=r.skill[1], t=r.U, x=0, y=0)
        r.store("set v18=T+25aip(4)", 0x18, r.T + 25 * r.aip(4))
        r.store("set v1c=2", 0x1C, 2)
        return
    if r.br("3.v1C=1", r.v[0x1C] == 1):
        r.call("3.delay", "Delay", n=r.aip(5))
        return
    h = r.call("4.findhostile", "FindHostile", pm=0, blk={0: {0: r.dist}}).eax
    if r.chance("5.chance(1)", 1):
        r.call("5.setmode4", "SetModeAtUnit", mode=4, t=h)
        return
    r.call("6.idle", "Idle", n=r.aip(5))


# ---- H1c R59 BloodRaven (catalogue 2766)
def m_r59(r):
    """R59 BloodRaven, the think (the init is not a think call). The home record's words, `AiParamsPush`'s block and the
    distance helpers' point words are not logged: not compared; `AiDistToPointSized` is compared by its ECX unit.
    `MonAiRunNearUnit`'s words are revision 3's positional names: the block's (t, n) as the two stack words."""
    h = r.call("1.find", "ParamsFind", U=r.U, kind=10, z=0).eax
    if not r.br("1.h", h != 0):
        r.call("1.push", "AiParamsPush")
        h = r.call("1.find2", "ParamsFind", U=r.U, kind=10, z=0).eax
    hd = 0
    if r.br("2.h", h != 0):
        hd = s32(r.call("2.hd", "AiDistToPointSized", c=r.t).eax)
        if r.less("2.45<dist", 45, r.dist):
            r.call("2.idle", "Idle", n=5)
            return
        if (r.less("2.49<hd", 49, hd)
                or r.br("2.50<ud", u32(r.call("2.ud", "AiDistToPointSized", c=r.U).eax) > 50)):
            r.store("set v1c=1", 0x1C, 1)
            r.call("2.ovr", "Ovr", type=7, param=100, byte=0)
            if r.br("2.ran", r.call("2.run", "RunToPoint").eax):
                return
            r.call("2.cancel", "CancelEvents", kind=2, z=0)
        if (r.br("2.v1C!=0", r.v[0x1C] != 0, val=r.v[0x1C])
                and r.br("2.5<ud", u32(r.call("2.ud2", "AiDistToPointSized", c=r.U).eax) > 5)):
            r.call("2.ovr2", "Ovr", type=7, param=100, byte=0)
            if r.br("2.ran2", r.call("2.run2", "RunToPoint").eax):
                return
            r.call("2.cancel2", "CancelEvents", kind=2, z=0)
        r.store("set v1c=0", 0x1C, 0)
    dist = r.dist
    if r.less("3.20<dist", 20, dist) and r.less("3.hd<50", hd, 50):
        dist = 12 if r.less("3.(dist>>1)<12", dist >> 1, 12) else dist >> 1
        r.call("3.ovr", "Ovr", type=7, param=100, byte=0)
        if r.br("3.ran", r.call("3.runnear", "MonAiRunNearUnit", s1=r.t, s2=dist).eax):
            return
        r.call("3.cancel", "CancelEvents", kind=2, z=0)
    r.store("set v14+=3", 0x14, r.v[0x14] + 3)
    if (r.br("5.Skill1>=0", r.skill[0] >= 0) and not r.br("5.melee", r.melee)
            and r.less("5.v18<2d+8", r.v[0x18], 2 * diff(r) + 8) and r.rchance("5.Range<v14", 100, r.v[0x14])):
        a = r.rng(15) + 5
        if r.br("5.pow2=0", r.call("5.pow2a", "RangePow2", seedp=r.U + 0x20, n=2).eax == 0):
            dx, dy = r.rng(a), a
        else:
            dx, dy = a, r.rng(a)
        if r.br("5.negx", r.call("5.pow2b", "RangePow2", seedp=r.U + 0x20, n=2).eax != 0):
            dx = -dx
        if r.br("5.negy", r.call("5.pow2c", "RangePow2", seedp=r.U + 0x20, n=2).eax != 0):
            dy = -dy
        tx, ty = tpos(r)
        use_skill(r, "5.useskill1", 1, 0, x=add(tx, dx), y=add(ty, dy))
        r.store("set v18+=1", 0x18, r.v[0x18] + 1)
        r.store("set v14=0", 0x14, 0)
        return
    if r.less("6.5<dist", 5, dist):
        if r.less("6.D100<5", r.d100(), 5, draw=True) and r.less("6.hd<50", hd, 50):
            r.call("6.ovr7", "Ovr", type=7, param=100, byte=0)
            r.call("6.runnear", "MonAiRunNearUnit", s1=r.t, s2=12)
            return
        h2 = r.call("6.findhostile", "FindHostile").eax
        if (r.br("6.h2", h2 != 0) and not r.br("6.St3or19", r.call("6.st3or19", "St3or19", U=r.U).eax)
                and r.rchance("6.Range<80", 100, 80)):
            if r.br("6.Skill2>=0", r.skill[1] >= 0) and r.rchance("6.Range<(d+4)10", 100, (diff(r) + 4) * 10):
                use_skill(r, "6.useskill2", 2, h2)
                return
            r.call("6.setmode4", "SetModeAtUnit", mode=4, t=h2)
            return
        r.call("6.ovr0", "Ovr", type=0, param=50, byte=0)
        if r.br("6.t56", r.call("6.t56", "T56", t=r.t, byte=4, flag=1).eax):
            return
    if r.less("7.D100<30", r.d100(), 30, draw=True) and r.less("7.dist<12", dist, 12):
        r.call("7.ovr", "Ovr", type=7, param=100, byte=0)
        if r.br("7.stepped", r.call("7.stepaway", "StepAwayXY", t=r.t, n=12 - dist, f=0).eax):
            return
        r.call("7.cancel", "CancelEvents", kind=2, z=0)
    r.call("8.setmode4", "SetModeAtUnit", mode=4, t=r.t)


# ---- H1c R66 SandMaggotQueen (catalogue 1406)
def m_r66(r):
    """R66 SandMaggotQueen. `SpawnClassByBase`'s seven words and the spawn's out words are not compared (revision 3's
    names are positional); `RoomAtSubtile`'s room and point neither. U's position is the AID line's x, y."""
    if r.br("1.v1C!=0", r.v[0x1C] != 0, val=r.v[0x1C]):
        r.call("1.idle", "Idle", n=s32(25 * r.aip(2)))
        r.store("set v1c=0", 0x1C, 0)
        return
    if r.br("2.v18=0", r.v[0x18] == 0, val=r.v[0x18]):
        if r.less("2.v14<aip(1)", r.v[0x14], r.aip(1)):
            r.call("2.move", "MoveToPoint", x=r.x, y=r.y, n=8)
            r.call("2.delay", "Delay", n=r.aip(2))
            r.store("set v18=1", 0x18, 1)
        return
    r.call("3.spawnclass", "SpawnClassByBase")
    room = r.call("4.room", "UnitGetRoom", u=r.U).eax
    room2 = r.call("4.subroom", "RoomAtSubtile").eax
    if r.br("4.room", room2 != 0):
        m = r.call("4.spawn", "SpawnAtPos").eax
        if r.br("4.m", m != 0):
            r.store("set v14+=1", 0x14, r.v[0x14] + 1)
    r.call("5.delay", "Delay", n=r.aip(2))
    r.store("set v18=0", 0x18, 0)
    r.store("set v1c=1", 0x1C, 1)


# ---- H1g R71 Regurgitator (catalogue 1515; AiRegurgitatorCb 0x005FA690)
def m_r71(r):
    """R71 Regurgitator. A found unit's mode is not logged (the rev 7 word `found.mode`, proposed, else a fork), nor its guid:
    a store of it is not compared after it (`store_unknown`)."""
    def clear(sfx):
        r.store("set v14=0" + sfx, 0x14, 0)
        r.store("set v18=0" + sfx, 0x18, 0)
        r.store("set v1c=0" + sfx, 0x1C, 0)
    v = r.v[0x14]
    if r.br("1.v14=5", v == 5, val=v):
        r.call("5.stepaway", "StepAway", t=r.t, d=16, flag=1)
        r.store("set v14=0", 0x14, 0)
        return
    if r.br("1.v14=2", v == 2):
        m = r.call("2.find", "GameFindUnit", type=1, guid=r.v[0x18]).eax
        if not r.br("2.m", m != 0) or not known(r, "2.m.mode=12", "found.mode", lambda w: w == 12):
            clear("#2")
            r.call("2.ring", "Ring", r=8)
            return
        if r.less("2.4<distsq", 4, s32(r.call("2.distsq", "UnitDistSq", u=r.U, t=m).eax)):
            if not r.less("2.v1C<6", r.v[0x1C], 6):
                clear("#2b")
                r.call("2.ring2", "Ring", r=8)
                return
            r.call("2.walkstop", "WalkStop", t=m, n=1)
            r.store("set v1c+=1", 0x1C, r.v[0x1C] + 1)
        r.store("set v14=3", 0x14, 3)
        r.call("2.idle", "Idle", n=8)
        return
    if r.br("1.v14=3", v == 3):
        m = r.call("3.find", "GameFindUnit", type=1, guid=r.v[0x18]).eax
        if (r.br("3.Skill1>=0", r.skill[0] >= 0) and r.br("3.m", m != 0)
                and known(r, "3.m.mode=12", "found.mode", lambda w: w == 12)):
            use_skill(r, "3.useskill1", 1, m)
            r.store("set v14=4", 0x14, 4)
            return
        clear("#3")
        r.call("3.ring", "Ring", r=8)
        return
    if r.br("1.v14=4", v == 4):
        if not r.br("4.melee", r.melee):
            r.call("4.setmode5", "SetModeAtUnit", mode=5, t=r.t)
            r.store("set v14=5", 0x14, 5)
            return
        r.call("4.stepaway", "StepAway", t=r.t, d=8, flag=1)
        return
    found = r.call("s.search", "UnitSearch", cb=0x005FA690, kind=1, blk={0: {0: 0, 1: r.aip(6) * r.aip(6)}}).out(0, 0)
    if r.br("s.v14=1", v == 1):
        if r.br("s.found", found != 0):
            store_unknown(r, "set v18=guid", 0x18)
            if r.less("s.2<distsq", 2, s32(r.call("s.distsq", "UnitDistSq", u=r.U, t=found).eax)):
                r.call("s.walkstop", "WalkStop", t=found, n=1)
                r.store("set v14=2", 0x14, 2)
                r.store("set v1c=0#s", 0x1C, 0)
                return
            r.call("s.idle", "Idle", n=8)
            r.store("set v14=3#s", 0x14, 3)
            r.store("set v1c=0#s2", 0x1C, 0)
            return
        if r.rchance("s.Range<20", 100, 20):
            clear("#s")
            return
        r.call("s.ring", "Ring", r=8)
        return
    eat = False
    if r.br("4.found", found != 0):
        if (r.less("4.distsq<9", s32(r.call("4.distsq", "UnitDistSq", u=r.U, t=found).eax), 9)
                and r.rchance("4.rchance(2)", 100, r.aip(2))):
            eat = True
        elif r.rchance("4.rchance(5)", 100, r.aip(5)):
            eat = True
    if not eat:
        rr = r.rng(100)
        if r.br("6.melee", r.melee):
            if r.less("6.r<aip(1)", rr, r.aip(1), draw=True):
                r.call("6.setmode4", "SetModeAtUnit", mode=4, t=r.t)
                return
            r.call("6.idle", "Idle", n=15)
            return
        if r.less("7.r<aip(3)", rr, r.aip(3), draw=True):
            r.call("7.walk", "Walk", t=r.t, flags=0)
            return
        if not (r.br("8.found", found != 0) and r.rchance("8.rchance(4)", 100, r.aip(4))):
            r.call("9.idle", "Idle", n=8)
            return
    r.call("e.walkstop", "WalkStop", t=found, n=1)
    r.store("set v14=2#e", 0x14, 2)
    store_unknown(r, "set v18=guid#e", 0x18)
    r.store("set v1c=0#e", 0x1C, 0)


# ---- H1h R73 AbyssKnight (catalogue 1584; rev 7 item 11)
def m_r73(r):
    """R73 AbyssKnight. Step 2's aura state (Skills `aurastate` of `Skill2`) and step 5's `MonsterData+0x0E` are data reads
    the rev 6 logs do not hold: the rev 7 words `R73.aurastate` and `R73.md0e`, else forks. U is a monster, so step 5's
    type test holds. Step 7's override word is compared whole: the logged byte argument is the new low word with its low
    byte replaced by `6 + (low & 1)` (`and al,1; add al,6` leaves EAX's upper 24 bits in place, R73a; the same form as
    R14a's ring argument)."""
    life = s32(r.call("1.lifepct", "UnitLifePct", u=r.U).eax)
    if r.br("2.Skill2>=0", r.skill[1] >= 0):
        w = r7(r, "R73.aurastate")
        if w is None:
            ok, st = r.unknown("2.st>=0"), None
        else:
            ok, st = r.br("2.st>=0", w >= 0, val=w), w
        if (ok and not r.br("2.hasstate", r.call("2.hasstate", "HasState", u=r.U, state=st).eax)
                and r.less("2.life<aip(1)", life, r.aip(1)) and r.rchance("2.rchance(2)", 100, r.aip(2))):
            r.call("2.useskill2", "UseSkill", mode=r.skmode[1], skill=r.skill[1], t=0, x=0, y=0)
            return
    if r.br("3.melee", r.melee):
        if r.chance("3.chance(3)", 3):
            r.call("3.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        r.call("3.idle", "Idle", n=r.aip(4))
        return
    if r.less("4.dist<aip(5)", r.dist, r.aip(5)) and not r.less("4.0<v14", 0, r.v[0x14]):
        r.store("set v14=aip(6)", 0x14, r.aip(6))
    if (r.br("5.Skill1>=0", r.skill[0] >= 0) and r.br("5.v14=0", r.v[0x14] == 0, val=r.v[0x14])
            and not known(r, "5.md0e>=4", "R73.md0e", lambda w: w >= 4)):
        use_skill(r, "5.useskill1", 1, r.t)
        r.store("set v14=aip(6)#2", 0x14, r.aip(6))
        return
    if r.less("6.0<v14", 0, r.v[0x14]):
        r.store("set v14-=1", 0x14, r.v[0x14] - 1)
    if r.chance("7.chance(7)", 7):
        low = r.step()
        r.call("7.ovr", "Ovr", type=2, param=0, byte=(u32(low) & 0xFFFFFF00) | (6 + (low & 1)))
        r.call("7.walk", "Walk", t=r.t, flags=7)
        return
    if r.less("8.dist<aip(8)", r.dist, r.aip(8)):
        r.call("8.t56", "T56", t=r.t, byte=3, flag=0)
        return
    r.call("9.idle", "Idle", n=15)


# ---- H1c R77 Trap-Missile, R80 Trap-Poison and R92 Trap-Nova (catalogue 1702, 1776, 1810)
def trap_shot(r, skill):
    if (r.br("1.t", r.t != 0) and not r.less("1.aip(1)<dist", r.aip(1), r.dist)
            and r.less("1.v14<aip(2)", r.v[0x14], r.aip(2))):
        if r.br("1.v18=0", r.v[0x18] == 0, val=r.v[0x18]) and (not skill or r.br("1.Skill1>=0", r.skill[0] >= 0)):
            if skill:
                use_skill(r, "1.useskill1", 1, r.t)
            else:
                r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            r.store("set v14+=1", 0x14, r.v[0x14] + 1)
            r.store("set v18=1", 0x18, 1)
            return
        r.store("set v18=0", 0x18, 0)
        r.call("1.idle", "Idle", n=r.aip(3))
        return
    if r.br("2.U", r.U != 0):
        r.store("set c4|=0x20000", "c4", r.c4 | 0x20000)
    r.call("3.die", "SetMode", mode=0, x=0, y=0)


def m_r77(r):
    """R77 Trap-Missile."""
    trap_shot(r, False)


def m_r80(r):
    """R80 Trap-Poison and R92 Trap-Nova (the same block)."""
    trap_shot(r, True)


# ---- H1c R85 HighPriest (catalogue 2924; AiPriestHealCb 0x005E0430; CORNER 0x006E337C, R85a)
CORNER = ((-5, -5), (5, -5), (5, 5), (-5, 5))


def m_r85(r):
    """R85 HighPriest. MonStats `MissS1` and the missile record's `Range` are not logged: `MissS1 > 0` and the range test
    fork, and `MissileRec`'s word is not compared."""
    tx, ty = tpos(r)
    if r.br("1.v14=0", r.v[0x14] == 0, val=r.v[0x14]):
        if r.br("1.melee", r.melee):
            if r.chance("1.chance(1)", 1):
                r.store("set v14=1", 0x14, 1)
                r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
                return
            r.call("1.stepaway", "StepAway", t=r.t, d=6, flag=1)
            return
        if (r.br("1.Skill2>=0", r.skill[1] >= 0) and r.less("1.v18<T", r.v[0x18], r.T)
                and r.rchance("1.rchance(2)", 100, r.aip(2))):
            u = r.call("1.search", "UnitSearch", cb=0x005E0430, kind=1, blk={0: {0: 0, 1: 75, 2: 2500}}).out(0, 0)
            if r.br("1.unit", u != 0):
                r.store("set v18=T+aip(3)", 0x18, r.T + r.aip(3))
                use_skill(r, "1.useskill2", 2, u)
                return
        if (r.br("1.Skill1>=0", r.skill[0] >= 0) and r.less("1.v18<T#2", r.v[0x18], r.T)
                and r.less("1.dist<aip(8)", r.dist, r.aip(8)) and r.rchance("1.rchance(4)", 100, r.aip(4))):
            k = r.call("1.pow2", "RangePow2", seedp=r.U + 0x20, n=4).eax & 3
            use_skill(r, "1.useskill1", 1, r.t, x=add(tx, CORNER[k][0]), y=add(ty, CORNER[k][1]))
            r.store("set v18=T+100", 0x18, r.T + 100)
            return
        if (r.less("1.0<aip(5)", 0, r.aip(5)) and r.unknown("1.MissS1>0")
                and r.br("1.m", r.call("1.missile", "MissileRec").eax != 0) and r.unknown("1.dist<Range-2")
                and r.rchance("1.rchance(5)", 100, r.aip(5))):
            r.call("1.setmode8", "SetModeAtUnit", mode=8, t=r.t)
            return
        if r.less("1.D100<80", r.d100(), 80, draw=True):
            if not r.less("1.aip(8)<dist", r.aip(8), r.dist):
                r.call("1.t56", "T56", t=r.t, byte=3, flag=0)
            else:
                r.call("1.walkstop", "WalkStop", t=r.t, n=6)
            return
    r.store("set v14=1#2", 0x14, 1)
    if r.br("3.melee", r.melee):
        if r.chance("3.chance(7)", 7):
            r.call("3.setmode8", "SetModeAtUnit", mode=8, t=r.t)
            return
        if r.chance("3.chance(6)", 6):
            r.call("3.stepaway", "StepAway", t=r.t, d=6, flag=1)
            r.store("set v14=0", 0x14, 0)
            return
        if r.rchance("3.Range<90", 100, 90):
            r.call("3.setmode4", "SetModeAtUnit", mode=4, t=r.t)
            return
        r.call("3.idle", "Idle", n=10)
        return
    if r.less("4.dist<6", r.dist, 6) and r.chance("4.chance(7)", 7):
        r.call("4.setmode8", "SetModeAtUnit", mode=8, t=r.t)
        return
    if r.chance("5.chance(6)", 6):
        r.store("set v14=0#2", 0x14, 0)
        r.call("5.idle", "Idle", n=10)
        return
    if r.less("6.D100<70", r.d100(), 70, draw=True):
        r.call("6.walk", "Walk", t=r.t, flags=7)
        return
    r.call("7.ring", "Ring", r=12)


# ---- H1g R93 ArcaneTower (catalogue 2970)
def m_r93(r):
    """R93 ArcaneTower."""
    if r.br("1.v18=0", r.v[0x18] == 0, val=r.v[0x18]):
        r.store("set v18=aip(1)", 0x18, r.aip(1))
    if r.less("2.T<v1C", r.T, r.v[0x1C]):
        r.call("2.idle", "Idle", n=10)
        return
    if r.br("3.Skill1>=0", r.skill[0] >= 0) and r.br("3.v14=0", r.v[0x14] == 0, val=r.v[0x14]):
        use_skill(r, "3.useskill1", 1, r.t)
        r.store("set v18-=1", 0x18, r.v[0x18] - 1)
        if r.less("3.v18<1", r.v[0x18], 1):
            r.store("set v14=1", 0x14, 1)
            r.store("set v18=aip(4)", 0x18, r.aip(4))
            r.store("set v1c=T+aip(3)", 0x1C, r.T + r.aip(3))
        else:
            r.store("set v1c=T+aip(2)", 0x1C, r.T + r.aip(2))
        return
    r.call("4.setmode4", "SetModeAtUnit", mode=4, t=r.t)
    r.store("set v18-=1#2", 0x18, r.v[0x18] - 1)
    if r.less("5.v18<1", r.v[0x18], 1):
        r.store("set v14=0", 0x14, 0)
        r.store("set v18=aip(1)#2", 0x18, r.aip(1))
        r.store("set v1c=T+aip(5)", 0x1C, r.T + r.aip(5))
    else:
        r.store("set v1c=T+aip(6)", 0x1C, r.T + r.aip(6))


# ---- H1c R94 DesertTurret (catalogue 2994; SWEEP 0x006E33E0 read from the catalogue's table, STEP by its rule)
SWEEP = None


def sweep_table():
    """`SWEEP[v + 8·d]` as the catalogue lists it (R94, the `d` \\ `v` table), read from the spec text, as `wisp_tables`."""
    global SWEEP
    if SWEEP is not None:
        return SWEEP
    import re
    path = os.path.join(os.path.dirname(HERE), "docs", "specs", "monsters", "ai", "catalogue.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r"^`SWEEP`, 0x006E33E0.*?\n\n(.*?)\n\n", text, re.S | re.M)
    rows = {}
    for ln in m.group(1).splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if cells and cells[0].isdigit():
            rows[int(cells[0])] = [int(c) for c in cells[1:9]]
    SWEEP = [rows[d][v] for d in range(8) for v in range(8)]
    return SWEEP


def step_xy(i):
    """`STEP[i]` by R94's rule: `j = (i + 1) mod 8`, `k = (i − 1) mod 8`, `clamp(2 − min(j, 8 − j))` per axis."""
    def c(a):
        return max(-1, min(1, a))
    j, k = (i + 1) % 8, (i - 1) % 8
    return c(2 - min(j, 8 - j)), c(2 - min(k, 8 - k))


def m_r94(r):
    """R94 DesertTurret. U's position is the AID line's x, y and t's its `t` words. `PathSetTargetPoint`'s words are not
    compared (revision 3's names are positional)."""
    if r.br("1.Skill1>=0", r.skill[0] >= 0) and r.br("1.v14=0", r.v[0x14] == 0, val=r.v[0x14]):
        r.call("1.useskill1", "UseSkill", mode=r.skmode[0], skill=r.skill[0], t=0, x=0, y=0)
        r.store("set v1c=0", 0x1C, 0)
        r.store("set v14=T", 0x14, r.T)
        return
    if r.less("2.T<v14", r.T, r.v[0x14]):
        r.call("2.idle", "Idle", n=10)
        return
    if r.less("3.aip(4)<dist", r.aip(4), r.dist):
        if r.less("3.0<v18", 0, r.v[0x18]):
            r.store("set v18-=1", 0x18, r.v[0x18] - 1)
        r.call("3.idle", "Idle", n=15)
        return
    tx, ty = tpos(r)
    d64 = r.call("4.dir", "UnitDirToPoint", u=r.U, x=tx, y=ty).eax
    dr = r.call("4.dir8", "Dir64To8", s1=d64).eax
    v = s32(r.v[0x1C])
    vm = abs(v) % 8 * (1 if v >= 0 else -1)            # the signed remainder (`cdq; idiv` shape, 0x005E0B0C)
    idx = vm + 8 * (dr & 7)
    if not 0 <= idx < 64:
        raise Stop("5: SWEEP index %d outside the table" % idx)
    r.vals.append(("5.sweep", "%d:%d" % (vm, dr & 7)))
    r.store("set v1c=SWEEP", 0x1C, sweep_table()[idx])
    vi = r.v[0x1C]
    if not 0 <= vi < 8:
        raise Stop("6: STEP index %d outside the table" % vi)
    sx, sy = step_xy(vi)
    x, y = u32(r.x + sx * r.aip(5)), u32(r.y + sy * r.aip(5))
    r.call("7.pathtarget", "SetPathTargetUnit", u=r.U, t=r.t)
    if (r.br("8.Skill1>=0", r.skill[0] >= 0)
            and r.br("8.ok1", r.call("8.targetok1", "SkillTargetOk", skill=r.skill[0], u=r.t, a=x, b=y).eax)
            and r.br("8.ok2", r.call("8.targetok2", "SkillTargetOk", skill=r.skill[0], u=r.t, a=tx, b=ty).eax)):
        r.call("8.useskill1", "UseSkill", mode=r.skmode[0], skill=r.skill[0], t=0, x=x, y=y)
        r.call("8.pathpoint", "PathSetTargetPoint")
        r.store("set v18+=1", 0x18, r.v[0x18] + 1)
        if r.less("8.aip(2)<v18", r.aip(2), r.v[0x18]):
            r.store("set v14=T+aip(3)", 0x14, r.T + r.aip(3))
            r.store("set v18=0", 0x18, 0)
        else:
            r.store("set v14=T+aip(1)", 0x14, r.T + r.aip(1))
        return
    if r.less("9.0<v18", 0, r.v[0x18]):
        r.store("set v18-=1#2", 0x18, r.v[0x18] - 1)
    r.call("10.idle", "Idle", n=10)


# ---- H1g R98 Smith (catalogue 3135)
def m_r98(r):
    """R98 Smith."""
    if r.br("1.melee", r.melee):
        r.call("1.setmode4", "SetModeAtUnit", mode=4, t=r.t)
        return
    L = clamp(r, "2.L", s32(r.call("2.lifepct", "UnitLifePct", u=r.U).eax), 0, 100)
    r.call("3.ovr", "Ovr", type=0, param=(100 - L) >> 1, byte=0)
    r.call("3.walk", "Walk", t=r.t, flags=7)


# ---- H1c R128 Nihlathak (catalogue 3939; AiOverseerMinionCb 0x005E26D0)
def m_r128(r):
    """R128 Nihlathak, the think. `A5Q4_NihlathakSeen`, the skill node's id and mode words, `CorpsePickNear` and
    `MonHasSkill` are not boundaries: taken to draw nothing; their results fork and the node's words are not compared.
    "U has it" is `GetUnitSkill(U, SkillK)` ≠ 0 (a boundary). `AiUseSkillNearSelf` is `near_self` (R122's)."""
    if r.br("2.state12", r.call("2.hasstate", "HasState", u=r.U, state=12).eax):
        r.call("2.stateclear", "StateSet", u=r.U, state=12, v=0)
    s1 = r.call("3.skill1", "GetUnitSkill", u=r.U, skill=r.skill[0]).eax
    if not r.br("4.t", r.t != 0):
        if r.br("4.s1", s1 != 0) and r.br("4.St3or19", r.call("4.st3or19", "St3or19", U=r.U).eax):
            near_self(r, "4.near", r.aip(2), None, None)
            return
        r.call("4.idle", "Idle", n=25)
        return
    if (r.br("5.s1", s1 != 0) and r.br("5.melee", r.melee)
            and r.less("5.D100<aip(1)", r.d100(), r.aip(1), draw=True)):
        near_self(r, "5.near", r.aip(2), None, None)
        return
    if (r.less("6.dist<aip(5)", r.dist, r.aip(5)) and r.less("6.D100<40", r.d100(), 40, draw=True)
            and r.br("6.stepped", r.call("6.stepaway", "StepAway", t=r.t, d=5, flag=1).eax)):
        return
    if (r.less("7.0<Skill3", 0, r.skill[2])
            and r.br("7.has3", (node := r.call("7.skill3", "GetUnitSkill", u=r.U, skill=r.skill[2]).eax) != 0)
            and r.less("7.D100<aip(3)", r.d100(), r.aip(3), draw=True)):
        r.call("7.level", "GetSkillLevel", u=r.U, s=node)
        if (r.unknown("7.corpse") and r.br("7.used", r.call("7.useskill3", "UseSkill", mode=r.skmode[2],
                                                                skill=r.skill[2], x=0, y=0).eax)):
            return
    if (r.less("8.0<Skill4", 0, r.skill[3])
            and r.br("8.has4", r.call("8.skill4", "GetUnitSkill", u=r.U, skill=r.skill[3]).eax != 0)
            and r.less("8.D100<60", r.d100(), 60, draw=True) and r.less("8.dist<14", r.dist, 14)):
        r.call("8.useskill4", "UseSkill", mode=r.skmode[3], skill=r.skill[3], t=r.t, x=0, y=0)
        return
    if (r.less("9.0<Skill2", 0, r.skill[1]) and r.less("9.D100<aip(4)", r.d100(), r.aip(4), draw=True)
            and r.unknown("9.hasskill2")):
        ret = r.call("9.search", "UnitSearch", cb=0x005E26D0, kind=1, blk={0: {0: 0, 1: 625, 2: 50, 3: 0, 4: 0, 5: 0}})
        u = ret.out(0, 4)
        if r.br("9.blk4", u != 0):
            r.call("9.useskill2", "UseSkill", mode=r.skmode[1], skill=r.skill[1], t=u, x=0, y=0)
            return
        if r.less("9.0<Skill5", 0, r.skill[4]):
            room = r.call("9.room", "UnitGetRoom", u=r.U).eax
            cls = 528 if r.ms2 > 528 else -1
            if r.br("9.cell", r.call("9.celltest", "SpawnClassCellTest", cls=cls, room=room, x=r.x, y=r.y, z=0).eax):
                room2 = r.call("9.room2", "UnitGetRoom", u=r.U).eax
                r.call("9.variant", "LevelClassVariant", s1=room2, s2=453 if r.ms2 > 453 else -1)
                r.call("9.useskill5", "UseSkill", mode=r.skmode[4], skill=r.skill[4], t=r.t, x=0, y=0)
                return
        r.call("9.ring", "Ring", r=6)
        return
    if (r.less("10.0<Skill4", 0, r.skill[3])
            and r.br("10.has4", r.call("10.skill4", "GetUnitSkill", u=r.U, skill=r.skill[3]).eax != 0)
            and r.less("10.dist<14", r.dist, 14)):
        r.call("10.useskill4", "UseSkill", mode=r.skmode[3], skill=r.skill[3], t=r.t, x=0, y=0)
        return
    if r.less("11.D100<60", r.d100(), 60, draw=True):
        r.call("11.walkz", "WalkZ", t=r.t)
    r.call("12.idle", "Idle", n=5)


# ---- H1h R32 Npc (catalogue 4154): Phase 1b's chain helpers with the class steps and AiNpcNearPlayer (rev 7 item 7)
def npc_home_leash(r, n):
    """`AiNpcHomeLeash(n)` (0x005E6860): the home record's find (a boundary, its words not compared), its distance
    (`PathDist`, unsigned against n), the push of R4 (not a boundary) and `Idle(10)`."""
    if not r.br("l.home", r.call("l.find", "ParamsFind", U=r.U).eax != 0):
        return npc_save_home(r)
    if not r.br("l.far", u32(r.call("l.dist", "PathDist", u=r.U).eax) > n):
        return False
    r.call("l.idle10", "Idle", n=10)
    return True


def unit_set_event(r, step):
    """`UnitSetEvent(U, …)` (0x00553380) is not a boundary and draws nothing; it ends with `Unit+0xC4 |= 0x400`
    (0x005533B9, unconditional after its null-unit assert), a store the next compared call sees. Found by the 38 kept logs
    (R32, `2026-11-03-ai-3-s2-5804-L4-fresh:a1-marsh.log` decision 1310: `c4` 0x302200B at entry, 0x302240B at the
    `Idle(20)` of 0x005E6A27). The catalogue's blocks name the call only."""
    if r.c4 is not None:
        r.store("set c4|=0x400 (%s.UnitSetEvent)" % step, "c4", r.c4 | 0x400)


def npc_near_player(r):
    """`AiNpcNearPlayer` (0x005E68F0). `AiNearestPlayer`'s (p, f) is the rev 7 word `AiNearestPlayer`; without it p is not
    compared and its tests fork. The interact list, `NpcInteractHas`, `NpcInteractAny` and the busy test are not logged:
    they fork. Step 7's `UnitSetEvent(U, 18, p)` runs when p is a player (`cmp [p], 0`, 0x005E6A11; a fork, the unit
    type is not logged) and sets `Unit+0xC4` bit 0x400 (`unit_set_event`); it draws nothing."""
    w = r7(r, "AiNearestPlayer")
    p = None if w is None else w[0]
    nn = s32(r.call("n.dist", "AiDistUnits", c=r.U, d=p).eax)
    if not r.unknown("n.L"):
        return False
    if r.unknown("n.any") or r.unknown("n.h") or r.less("n.0<v14", 0, r.v[0x14]):
        far = u32(r.call("n.pathdist", "PathDist", u=r.U, x=r.v[0x18], y=r.v[0x1C]).eax) > 2
        if r.br("n.far", far) and r.less("n.36<v14", 36, r.v[0x14]):
            r.call("n.walkpt", "WalkToPoint", x=r.v[0x18], y=r.v[0x1C])
        elif r.less("n.0<v14#2", 0, r.v[0x14]):
            r.call("n.idle8", "Idle", n=8)
        if r.less("n.v14<0", r.v[0x14], 0):
            r.store("set v14=0", 0x14, 0)
        else:
            r.store("set v14-=1", 0x14, r.v[0x14] - 1)
        return True
    if w is None:
        if r.unknown("n.p=0|p=U"):
            return False
    elif r.br("n.p=0|p=U", p == 0 or p == r.U):
        return False
    if not r.less("n.n<3", nn, 3) and not r.less("n.23<n", 23, nn):
        if npc_home_leash(r, 16):
            return True
        r.call("n.ovr", "Ovr", type=1, param=0, byte=0)
        r.call("n.toward", "Toward", t=p, max=3 if not r.less("n.n<5", nn, 5) else nn - 2, ring=2)
        return True
    v = r.v[0x18]
    if r.br("n.v18=0", v == 0, val=v):
        r.store("set v18=60", 0x18, 60)
        if r.unknown("n.p player"):
            unit_set_event(r, "n")
    elif r.less("n.v18<0", v, 0):
        r.store("set v18=0", 0x18, 0)
    else:
        r.store("set v18-=1", 0x18, v - 1)
    r.call("n.idle20", "Idle", n=20)
    return True


def m_r32(r):
    """R32 Npc. The class steps' quest helpers (0x0059F570, `A2Q4_GuardBlock`, 0x0059B6E0, 0x005BAD20, 0x005B9CA0,
    0x00594360, their actions and `A5Q4_RedPortalCreateAI`) are not boundaries: their results fork, and they are taken to
    draw nothing. `WalkPt(p)` is `MonAiWalkToPoint` (0x005DED90, a boundary); a quest point is not logged, so its words
    are not compared."""
    if npc_save_home(r):
        return
    c = r.cls
    if c == 201:
        if r.unknown("2.201.0059F570=0"):
            r.call("2.201.idle40", "Idle", n=40)
            return
        if r.unknown("2.201.a"):
            r.call("2.201.idle20", "Idle", n=20)
        if not r.unknown("2.201.b"):
            return
        if r.unknown("2.201.0059B6E0&home"):
            r.call("2.201.idle50", "Idle", n=50)
            return
    elif c == 254:
        if r.unknown("2.254.005BAD20"):
            r.call("2.254.setmode8", "SetMode", mode=8, x=0, y=0)
            return
    elif c == 255:
        if r.unknown("2.255.005B9CA0"):
            if r.br("2.255.far", u32(r.call("2.255.pathdist", "PathDist", u=r.U).eax) > 3):
                r.call("2.255.walkpt", "WalkToPoint")
                return
            r.call("2.255.setmode8", "SetMode", mode=8, x=0, y=0)
            return
    elif c == 265:
        if r.unknown("2.265.00594360"):
            if r.br("2.265.far", u32(r.call("2.265.pathdist", "PathDist", u=r.U).eax) > 2):
                r.call("2.265.walkpt", "WalkToPoint")
                return
    r.vals.append(("2.class", c if c in (201, 254, 255, 265, 512) else "other"))
    if npc_near_player(r) or npc_script_step(r) or npc_path_pick(r):
        return
    r.call("6.idle8", "Idle", n=8)


# ---- H1h R1 Idle (catalogue 101): R100's block, behind the rev 7 window
def m_r1w(r):
    """R1 Idle: `m_r1` once the think's calls are logged (rev 7 item 1: a return-address window over 0x005B0CD0). A rev 6
    log holds no call of this think, so the decision stops."""
    if (r.dec.get("rev") or 0) < 7:
        raise Stop("R1: the think 0x005B0CD0 is outside the rev 6 windows (rev 7 item 1)")
    m_r1(r)



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
    "R44": (0x005F67B0, m_r44, "catalogue 280, 281, 283 (S1c)"),
    "S13": (0x005E5C50, m_s13, "catalogue 507, 508, 509 (S1c)"),
    # plan 0069 Phase 1b (`lane/n69b`), revision 4: H1a
    "R8": (0x005F0700, m_r8, "catalogue 29, 30, 32, 34 (H1a)"),
    "R16": (0x005F1B60, m_r16, "catalogue 56, 57, 58 (H1a)"),
    "R142": (0x005F1DE0, m_r142, "catalogue 59, 60, 61 (H1a)"),
    "R17": (0x005F20A0, m_r17, "catalogue 62, 63, 64 (H1a)"),
    "R18": (0x005F22B0, m_r18, "catalogue 65, 67 (H1a)"),
    "R24": (0x005F3730, m_r24, "catalogue 77, 78, 79 (H1a)"),
    "R25": (0x005F39B0, m_r25, "catalogue 80-86, 88, 90-92 (H1a)"),
    "R27": (0x005F4850, m_r27, "catalogue 98, 99, 100 (H1a)"),
    "R72": (0x005FAA90, m_r72, "catalogue 174, 175 (H1a)"),
    "R74": (0x005FAF00, m_r74, "catalogue 179, 180, 181, 183 (H1a)"),
    # H1b
    "R115": (0x005E1900, m_r115, "catalogue 338, 339, 340 (H1b)"),
    "R116": (0x005E1B60, m_r116, "catalogue 341, 342, 343 (H1b)"),
    "R117": (0x005E1D30, m_r117, "catalogue 344, 345, 346 (H1b)"),
    "S15": (0x005E1D30, m_r117, "catalogue 373 (H1b)"),
    "R119": (0x005E2120, m_r119, "catalogue 351, 352, 353 (H1b)"),
    "R120": (0x005E27A0, m_r120, "catalogue 354, 355, 357 (H1b)"),
    "R122": (0x005E2FF0, m_r122, "catalogue 362, 363, 364, 365 (H1b)"),
    "R123": (0x005E34C0, m_r123, "catalogue 366, 367, 368 (H1b)"),
    "S16": (0x005E2D80, m_s16, "catalogue 374, 375, 376 (H1b)"),
    "R126": (0x005EE040, m_r126, "catalogue 377, 378, 379 (H1b)"),
    "R129": (0x005E61B0, m_r129, "catalogue 384, 386, 387 (H1b)"),
    "R136": (0x005EF710, m_r136, "catalogue 406, 407, 408 (H1b)"),
    "R137": (0x005EFA90, m_r137, "catalogue 409, 410, 411 (H1b)"),
    # H1d
    "S5": (0x005E7AC0, m_s5, "catalogue 276, 277 (H1d)"),
    "S6": (0x005E7C10, m_s6, "catalogue 278, 279 (H1d)"),
    "R41": (0x005E7540, m_r41, "catalogue 462, 463 (H1d)"),
    "R42": (0x005E9E00, m_r42, "catalogue 464, 465 (H1d)"),
    "R58": (0x005E7E20, m_r58, "catalogue 470, 472 (H1d)"),
    "R60": (0x005E7AC0, m_s5, "catalogue 474 (H1d)"),
    # plan 0069 Phase 1c (`lane/n69c`), revision 5: H1c
    "R38": (0x005F6220, m_r38, "catalogue 105, 106, 107 (H1c)"),
    "R45": (0x005F6A10, m_r45, "catalogue 117, 118, 119, 120 (H1c)"),
    "R66": (0x005F9CF0, m_r66, "catalogue 158, 159, 160 (H1c)"),
    "R77": (0x005FB5B0, m_r77, "catalogue 190, 191, 192 (H1c)"),
    "R80": (0x005FB900, m_r80, "catalogue 201, 202, 203 (H1c)"),
    "R92": (0x005FB9B0, m_r80, "catalogue 206, 207, 208 (H1c)"),
    "R50": (0x005F78B0, m_r50, "catalogue 285, 286, 287, 289, 290 (H1c)"),
    "R53": (0x005F85C0, m_r53, "catalogue 291, 292, 293 (H1c)"),
    "R55": (0x005F89B0, m_r55, "catalogue 294, 295, 296 (H1c)"),
    "R59": (0x005E6320, m_r59, "catalogue 297, 298, 299 (H1c)"),
    "R85": (0x005E0490, m_r85, "catalogue 312, 315 (H1c)"),
    "R94": (0x005E0980, m_r94, "catalogue 317, 318, 319 (H1c)"),
    "R128": (0x005EE5D0, m_r128, "catalogue 424, 425, 426 (H1c)"),
    # H1g
    "R7": (0x005EFB80, m_r7, "catalogue 26, 27, 28 (H1g)"),
    "NOTES": (0x005EFB80, m_r7, "catalogue 517 (H1g): the Reimplementation notes row, row 7's second aip(3) draw"),
    "R11": (0x005F0CD0, m_r11, "catalogue 40, 41 (H1g)"),
    "R14": (0x005F1140, m_r14, "catalogue 47, 48 (H1g)"),
    "R33": (0x005F56D0, m_r33, "catalogue 101, 102 (H1g)"),
    "R36": (0x005F5D50, m_r36, "catalogue 103, 104 (H1g)"),
    "R39": (0x005F6340, m_r39, "catalogue 108, 109 (H1g)"),
    "R40": (0x005F6530, m_r40, "catalogue 110, 111 (H1g)"),
    "R49": (0x005F72D0, m_r49, "catalogue 132, 133, 134, 137 (H1g)"),
    "R56": (0x005F8F80, m_r56, "catalogue 142, 143 (H1g)"),
    "R57": (0x005F9270, m_r57, "catalogue 145, 146 (H1g)"),
    "R71": (0x005FA710, m_r71, "catalogue 170, 173 (H1g)"),
    "R93": (0x005E0F60, m_r93, "catalogue 316 (H1g)"),
    "R98": (0x005E3890, m_r98, "catalogue 329 (H1g)"),
    # H1h
    "R1": (0x005B0CD0, m_r1w, "catalogue 12, 13 (H1h)"),
    "R10": (0x005F0B00, m_r10, "catalogue 35, 36, 39 (H1h)"),
    "R32": (0x005E7130, m_r32, "catalogue 450-458, 460, 461 (H1h)"),
    "R48": (0x005F6E60, m_r48, "catalogue 126, 127, 128, 129, 131 (H1h)"),
    "R73": (0x005FAB80, m_r73, "catalogue 176, 177, 178 (H1h)"),
}

# Revision 4: of two entries that share a think, each takes only the decisions of its AI state (the AID line's `st`,
# AiCtl+0x00, README E4/E5): the state row its own state, the table row state 0. No entry before this revision has one.
SELECT = {
    "R117": lambda a: a["st"] == 0, "S15": lambda a: a["st"] == 15,
    "R60": lambda a: a["st"] == 0, "S5": lambda a: a["st"] == 5,
}


# ------------------------------------------------------------------------------------------------------------ report
def sep_line(name, free):
    """ADR-0028 item 7 (plan 0069 gap 5): the number of distinct predicted outcomes over the entry's fork-free matched
    decisions. An outcome is the sequence of the block's compared calls (their labels) in the decision; a row with one
    outcome confirms that outcome, not a branch choice. The eight most common are listed with their counts."""
    paths = Counter(" ".join(lb for lb, _ in o.run.labels) or "(no call)" for _, o in free)
    top = " | ".join("%s: %d" % kv for kv in sorted(paths.items(), key=lambda kv: (-kv[1], kv[0]))[:8])
    return "  SEP %s outcomes %d over %d fork-free decisions%s" % (name, len(paths), len(free), (": " + top) if top else "")


def strip_sep(text):
    """The report without its SEP lines: what S1b's model-check.txt holds (the regression check of plan 0069 gap 6)."""
    return "".join(ln for ln in text.splitlines(True) if not ln.startswith("  SEP "))


def regress(base_dir, logs_dir, out):
    """Plan 0069 gap 6: S1b's check again, over its own log list, with its own entries, from the directory its paths are
    relative to; the output without the SEP lines must equal its kept model-check.txt byte for byte."""
    base = os.path.join(base_dir, "model-check.txt")
    with open(base) as fh:
        want = fh.read()
    names = [ln.split()[1] for ln in want.splitlines() if ln.startswith("ENTRY ")]
    with open(os.path.join(base_dir, "logs.txt")) as fh:
        paths = [x.strip() for x in fh if x.strip()]
    cwd = os.getcwd()
    os.chdir(logs_dir)
    try:
        import io
        buf, real = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            run_check(paths, names, None)
        finally:
            sys.stdout = real
    finally:
        os.chdir(cwd)
    got = buf.getvalue()
    if out:
        with open(out, "w") as fh:
            fh.write(got)
    same = strip_sep(got) == want
    nsep = sum(1 for ln in got.splitlines() if ln.startswith("  SEP "))
    print("REGRESS entries %d logs %d SEP lines %d: %s %s" % (len(names), len(paths), nsep,
                                                            "byte-identical to" if same else "DIFFERS from", base))
    return 0 if same else 1


def run_check(paths, names, out, select=True):
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
                if select and n in SELECT and not SELECT[n](d["aid"]):
                    continue
                decs[n].append(d)
    if "S13" in names:
        s13_counts(decs["S13"])
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
        lines.append(sep_line(n, free))
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
    c.add_argument("--no-select", action="store_true", help="revision 4: every decision of an entry's think, whatever its state")
    sub.add_parser("list")
    r = sub.add_parser("regress")
    r.add_argument("--base", default=os.path.join("workspace", "logs", "ai", "sweep2-s1b"))
    r.add_argument("--logs-dir", default=os.path.join("workspace", "logs", "ai"))
    r.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "regress":
        return regress(os.path.abspath(a.base), a.logs_dir, a.out)
    if a.cmd == "list":
        for n, (th, _, rows) in MODELS.items():
            print("%s %08x %s" % (n, th, rows))
        return 0
    paths = list(a.logs)
    if a.loglist:
        with open(a.loglist) as fh:
            paths += [x.strip() for x in fh if x.strip()]
    names = a.rows.split(",") if a.rows else list(MODELS)
    run_check(paths, names, a.out, select=not a.no_select)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
