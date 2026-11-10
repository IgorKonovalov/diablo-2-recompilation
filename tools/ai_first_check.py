#!/usr/bin/env python3
"""Plan 0066 batch S1d (`lane/n66d`): first-boundary hand maps for the catalogue rows that tools/ai.py has no model of, checked
against the kept AI logs. No game.

    python3 -I tools/ai_first_check.py check [LOG ...] [--logs LIST] [--rows R10,R11] [--out FILE]
    python3 -I tools/ai_first_check.py list

Why a separate tool. tools/ai.py check is the hashed checker behind the kept first-boundary outputs of run:2026-11-03-ai,
run:2026-11-03-ai-3, run:2026-11-04-ai-r5 and run:2026-11-04-r72; it stays unchanged, so those outputs still reproduce. Its
"unmodelled" rows (decisions in a think with no emulated family, or a family whose inputs the AID line does not carry) are
the ones this tool maps.

The maps. A map is the head of the entry's pseudocode block (docs/specs/monsters/ai/catalogue.md at b5999f5e) up to its
first call of a function in the logger's boundary set (tools/gdb/ai.py BND), the same block transcription as
tools/ai_model_check.py: the S1b models are reused where they exist (R15, R23, R26, R96, R99, R100, R130), and new heads are
written below for R10's think, R11, R15's alt, R48, R49 and R56 (S13's head is ai_model_check.m_s13, S1c). A hand map stays
a reading (README G5): what a match confirms is the logged first call. The run stops at that first call: the callee, its
call site (the return address), the words the block names by tools/ai_model_check.CONV, the unit seed (the map's own draws
since the think call), the AI control words +0x14/+0x18/+0x1C and `Unit+0xC4`. Its return is not used. A map that returns
before any call matches a decision with no logged call whose exit seed (AIX) equals the map's.

The call sites (`SITES`) are not taken from the logs. Each is the return address of the one call instruction to that
callee in the think's code (objdump of the pinned game.exe, the think's range from the spec anchor), or, where the think
calls the callee from several sites, the site of the emulated family of the same think (tools/ai_cat_emu10.py `m_mauler`,
tools/ai_cat_emu12.py `m_soul`, `m_buffy`), whose maps are [C] in their emulation runs.

Unknowns fork as in tools/ai_model_check.py; a forked decision supports nothing (review-fixes rule 10).

Controls over each entry's fork-free matched decisions: `site` (every predicted site + 1: every decision must fail), each
branch the map runs before its first call reversed alone (`FLIP`), `le` (each draw `<=` for `<`).
"""
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_model_check as MC  # noqa: E402


class First(Exception):
    pass


class FirstRun(MC.Run):
    """A model run that stops at its first boundary call, with that call's site compared."""

    def __init__(self, dec, sites, choices=(), flip=None, ctl=None, shift=0):
        MC.Run.__init__(self, dec, choices, flip, ctl)
        self.sites, self.shift, self.first = sites, shift, None

    def call(self, label, name, blk=None, **kw):
        if self.i < len(self.log):
            b = self.log[self.i]
            want = self.sites.get(label)
            if want is None:
                raise MC.Mismatch("%s: the map names no site for this call" % label)
            if b["fn"] == MC.CONV[name][0] and want + self.shift != b["ra"]:
                raise MC.Mismatch("%s: site %08x, the log %08x" % (label, want + self.shift, b["ra"]))
        try:
            MC.Run.call(self, label, name, blk, **kw)
        except MC.Stop as e:
            if "no AIR line" not in str(e):
                raise
        self.first = (label, self.sites[label])
        raise First()


def check(model, dec, sites, flip=None, ctl=None, shift=0, limit=64):
    out = MC.Outcome()
    todo = [()]
    mism, stops, n = [], [], 0
    while todo and n < limit:
        ch = todo.pop()
        n += 1
        r = FirstRun(dec, sites, ch, flip, ctl, shift)
        try:
            model(r)
            if r.log:
                raise MC.Mismatch("the map returns, the log has %08x@%08x" % (r.log[0]["fn"], r.log[0]["ra"]))
            if dec["aix"] is None:
                raise MC.Stop("no AIX line")
            if "%08x:%08x" % r.seed != dec["aix"]["s"]:
                raise MC.Mismatch("return: exit seed %08x:%08x/%s" % (r.seed + (dec["aix"]["s"],)))
            r.first = ("return", None)
        except First:
            pass
        except MC.NeedChoice:
            todo.append(ch + (True,))
            todo.append(ch + (False,))
            continue
        except MC.Mismatch as e:
            mism.append(str(e))
            continue
        except MC.Stop as e:
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


# ------------------------------------------------------------------------------------------------------- new heads
def m_r10(r):
    """R10 CorruptRogue's think: step 1, `MonPlayerBonus(G, &pb, UnitGetRoom(U), U)`; `MonPlayerBonus` (0x00573930) is not
    in the logger's set, `UnitGetRoom` is."""
    r.call("1.room", "UnitGetRoom", u=r.U)


def m_r11(r):
    """R11 Baboon: step 1, `life <- UnitLifePct(U)`."""
    r.call("1.lifepct", "UnitLifePct", u=r.U)


def m_r15alt(r):
    """R15's alt (0x005F1750): `rec <- AiCtlParamGet(kind 14)`, not a logged call; `rec+0x18` is not logged, so the
    branch forks unless Skill1 < 0."""
    if r.br("alt.Skill1>=0", r.skill[0] >= 0) and r.unknown("alt.rec18=1"):
        r.call("alt.target", "GetTargetUnit")
        return
    cb = bytes.fromhex(r.aid["ctl"])
    r.call("alt.init", "MonAiInit", ctl=r.ctlp, state=int.from_bytes(cb[0:4], "little"))


def m_r48(r):
    """R48 ZakarumZealot: step 1 reads MonStats words only; step 2, `life <- UnitLifePct(U)`."""
    r.call("2.lifepct", "UnitLifePct", u=r.U)


def m_r49(r):
    """R49 ZakarumPriest: step 1, `life <- UnitLifePct(U)`."""
    r.call("1.lifepct", "UnitLifePct", u=r.U)


def m_r56(r):
    """R56 Tentacle: step 1, `o <- MonsterOwner(U)`."""
    r.call("1.owner", "MonsterOwner", U=r.U)


# name: (think, model, sites, the catalogue line and inventory row)
ENTRIES = {
    "R10": (0x005F0B00, m_r10, {"1.room": 0x005F0B2C}, "R10l (line 327, row 38): this think"),
    "R10s13": (0x005E5C50, MC.m_s13, {"1.room": 0x005E5C77}, "R10l (line 327, row 38): its state-13 decisions"),
    "R11": (0x005F0CD0, m_r11, {"1.lifepct": 0x005F0D06}, "R11l (line 381, row 43)"),
    "R15": (0x005F1800, MC.m_r15, {"1.findhostile": 0x005F1833}, "R15l (line 482, row 54): the think"),
    "R15alt": (0x005F1750, m_r15alt, {"alt.target": 0x005F178D, "alt.init": 0x005F17DB}, "R15l (line 482, row 54): the alt"),
    "R23": (0x005F3170, MC.m_r23, {"1.distsq": 0x005F31C9}, "R23l (line 692, row 75)"),
    "R26": (0x005F4510, MC.m_r26, {"1.lifepct": 0x005F4544}, "R26l (line 881, row 96)"),
    "R48": (0x005F6E60, m_r48, {"2.lifepct": 0x005F6ECB}, "R48l (line 1185, row 130)"),
    "R49": (0x005F72D0, m_r49, {"1.lifepct": 0x005F72FE}, "R49l (line 1223, row 136)"),
    "R56": (0x005F8F80, m_r56, {"1.owner": 0x005F8FB1}, "R56l (line 1304, row 144)"),
    "R96": (0x005E1250, MC.m_r96, {"1.head": 0x005E1281}, "R96l (line 3116, row 325)"),
    "R99": (0x005E9F10, MC.m_r99, {"2.setmode8": 0x005EA060, "2.idle": 0x005EA070, "3.setmode9": 0x005E9F83,
                                   "4.setmode8": 0x005EA042, "5.setmode4": 0x005E9FCD, "5.setmode8": 0x005EA01E,
                                   "5.setmode5": 0x005E9FFA}, "R99l (line 4455, row 487)"),
    "R100": (0x005E7F50, MC.m_r1, {"room": 0x005E7F5C}, "R100l (line 4467, row 490)"),
    "R130": (0x005EE260, MC.m_r130, {"1.setmode4": 0x005EE2CE, "1.idle": 0x005EE3AD, "2.useskill1": 0x005EE34A,
                                     "3.walk": 0x005EE39D, "4.idle": 0x005EE3AD}, "R130l (line 3627, row 389)"),
}


def run_of(path):
    b = os.path.basename(path)
    for pre, name in (("2026-11-03-ai-3-", "ai-3"), ("2026-11-03-ai-s2-", "ai"), ("2026-11-04-ai-r5-", "ai-r5"),
                      ("owner-", "r72")):
        if b.startswith(pre):
            return name
    return "other"


def run_check(paths, names, out):
    by_th = defaultdict(list)
    for n in names:
        by_th[ENTRIES[n][0]].append(n)
    decs = defaultdict(list)
    for p in paths:
        for d in ai.parse(p)["dec"]:
            if d.get("trunc"):
                continue
            for n in by_th.get(d["aid"]["th"], ()):
                decs[n].append(d)
    if "R10s13" in names:
        MC.s13_counts(decs["R10s13"])
    lines = []
    for n in names:
        th, model, sites, what = ENTRIES[n]
        ds = decs[n]
        res = [(d, check(model, d, sites)) for d in ds]
        cnt = Counter(o.status for _, o in res)
        free = [(d, o) for d, o in res if o.status == "ok" and o.forks == 0]
        per = Counter(run_of(d["log"]) for d in ds)
        lines.append("ENTRY %s think %08x (%s): decisions %d (%s), ok %d (fork-free %d, forked %d), mismatch %d, stop %d" % (
            n, th, what, len(ds), " + ".join("%s %d" % kv for kv in sorted(per.items())), cnt["ok"], len(free),
            cnt["ok"] - len(free), cnt["mismatch"], cnt["stop"]))
        revs = Counter(d["rev"] for d in ds)
        lines.append("  REVS %s" % " ".join("%s:%d" % (k, v) for k, v in sorted(revs.items(), key=lambda kv: str(kv[0]))))
        for d, o in res:
            if o.status == "mismatch":
                lines.append("  MISMATCH %s n=%d: %s" % (os.path.basename(d["log"]), d["aid"]["n"], o.why))
        why = Counter(o.why for _, o in res if o.status == "stop")
        for w, k in sorted(why.items()):
            lines.append("  STOP %d %s" % (k, w))
        outc = Counter(o.run.first for _, o in free)
        for (lb, site), k in sorted(outc.items(), key=lambda kv: str(kv[0])):
            lines.append("  FIRST %s %s %d" % (lb, "%08x" % site if site else "-", k))
        lines.append("  OUTCOMES fork-free %d" % len(outc))
        arms, ran = Counter(), Counter()
        for _, o in free:
            for b, v in set(o.run.arms):
                arms[(b, v)] += 1
            for b in {b for b, _ in o.run.arms}:
                ran[b] += 1
        for b in sorted(ran):
            lines.append("  ARM %s true %d false %d" % (b, arms[(b, True)], arms[(b, False)]))
        for b in sorted(ran):
            sub = [d for d, o in free if any(x == b for x, _ in o.run.arms)]
            st = Counter(check(model, d, sites, flip=b).status for d in sub)
            lines.append("  FLIP %s fail %d of %d (stop %d)" % (b, st["mismatch"], len(sub), st["stop"]))
        st = Counter(check(model, d, sites, shift=1).status for d, _ in free)
        lines.append("  CONTROL site fail %d of %d (stop %d)" % (st["mismatch"], len(free), st["stop"]))
        st = Counter(check(model, d, sites, ctl="le").status for d, _ in free)
        lines.append("  CONTROL le fail %d of %d (stop %d)" % (st["mismatch"], len(free), st["stop"]))
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
        for n, (th, _, sites, what) in ENTRIES.items():
            print("%s %08x %s sites %s" % (n, th, what, " ".join("%s=%08x" % kv for kv in sorted(sites.items()))))
        return 0
    paths = list(a.logs)
    if a.loglist:
        with open(a.loglist) as fh:
            paths += [x.strip() for x in fh if x.strip()]
    names = a.rows.split(",") if a.rows else list(ENTRIES)
    run_check(paths, names, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
