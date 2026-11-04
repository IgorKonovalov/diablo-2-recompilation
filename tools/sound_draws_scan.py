#!/usr/bin/env python3
"""Plan 0062 / backlog -ns priority: draw sites reachable from the sound path of the pinned Game.exe (python3 -I).

Usage: sound_draws_scan.py <game.exe> <section> [args] [> out]
  gate                what the two config readers (0x00405E09, 0x004DCA38) and the three sound gates read
  closure ROOT...     recursive descent from each ROOT (hex): reached code, direct callees, draw sites, indirect calls,
                      imports, and every immediate that points at code (address-taken, not followed unless --taken)
  writers ADDR...     every instruction with an absolute operand on ADDR (hex)
  skipped             draw sites in the closure of each body the gates skip under -ns (SKIPPED), with the library
                      tail common to every body subtracted and reported as its own closure
  leak                absolute globals written by the sound core (CORE) and touched outside it
  api                 every function in CORE called from outside it, with its largest caller (client against server)
  taint               every call site outside CORE that consumes a return of a state query (QUERY), iterated through
                      wrappers that return the value; each branch's two sides are closed and their draws differenced
  pointers            dwords in the data sections equal to a CORE function start (a call the direct scan can't see)
  playerseed          draw sites on the client player's seed (0x00463DD0 result +0x20), with the gate they sit behind
  control             the same closure and taint machinery on bodies known to draw, and on a planted gate
Disassembly is objdump's linear sweep; descent walks it, so bytes it misreads can hide an instruction. Jump tables
`jmp [reg*4+imm]` are read from the file while the entries point into .text. Every other indirect call or jump is
printed as unfollowed, never assumed empty.
"""
import re, struct, subprocess, sys, collections

TEXT = (0x401000, 0x6CC000)
MULT = "0x6ac690c5"
# the out-of-line primitives of docs/specs/rng/README.md § Primitives, by symbols.csv name
PRIM = {0x45C370: "RNG_Step", 0x45C390: "RNG_Range", 0x45C3E0: "RNG_RangeB", 0x472210: "RNG_RangePow2",
        0x472240: "RNG_RangePow2Plus", 0x472280: "RNG_RangeOffset", 0x4BC500: "RNG_RandLoHi"}
INIT = {0x650E30: "RNG_SeedInitOne", 0x650E40: "RNG_SeedInit", 0x650DE0: "RNG_EntropySeed"}
LINE = re.compile(r"^\s*([0-9a-f]+):\t[0-9a-f ]+\t(.*)$")
HEX = re.compile(r"0x([0-9a-f]+)")


class Img:
    def __init__(self, path):
        self.path = path
        self.raw = open(path, "rb").read()
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=%#x" % TEXT[0],
                              "--stop-address=%#x" % TEXT[1], path], capture_output=True, text=True).stdout
        self.ins = {}
        self.order = []
        for l in out.splitlines():
            m = LINE.match(l)
            if m and m[2].strip():
                a = int(m[1], 16)
                self.ins[a] = " ".join(m[2].split())
                self.order.append(a)
        self.next = {a: b for a, b in zip(self.order, self.order[1:])}
        self.idx = {a: i for i, a in enumerate(self.order)}
        pe = struct.unpack_from("<I", self.raw, 0x3C)[0]
        n = struct.unpack_from("<H", self.raw, pe + 6)[0]
        opt = struct.unpack_from("<H", self.raw, pe + 20)[0]
        self.secs = []
        for i in range(n):
            s = pe + 24 + opt + i * 40
            vs, va, rs, rp = struct.unpack_from("<IIII", self.raw, s + 8)
            self.secs.append((0x400000 + va, max(vs, rs), rp))

    def dword(self, va):
        for b, sz, rp in self.secs:
            if b <= va < b + sz:
                return struct.unpack_from("<I", self.raw, va - b + rp)[0]
        return None

    def table(self, va):
        got = []
        for i in range(512):
            v = self.dword(va + 4 * i)
            if v is None or not TEXT[0] <= v < TEXT[1] or v not in self.ins:
                break
            got.append(v)
        return got


def is_text(v):
    return TEXT[0] <= v < TEXT[1]


def closure(im, roots, stop=()):
    """Descent over direct edges. Returns reached instructions and call edges. `stop` targets are not entered."""
    seen, work, calls = set(), list(roots), collections.defaultdict(set)
    ind, jt, taken, imports, entries = [], [], set(), set(), set(roots)
    while work:
        a = work.pop()
        while a not in seen:
            t = im.ins.get(a)
            if t is None:
                ind.append((a, "address not an instruction start"))
                break
            seen.add(a)
            op = t.split()[0]
            for h in HEX.findall(t):
                v = int(h, 16)
                if is_text(v) and op not in ("call", "jmp") and not op.startswith("j") and v in im.ins:
                    taken.add((a, v))
            if op == "call":
                m = re.fullmatch(r"call 0x([0-9a-f]+)", t)
                if m:
                    v = int(m[1], 16)
                    calls[a].add(v)
                    if v not in stop:
                        entries.add(v)
                        work.append(v)
                else:
                    m = re.search(r"ds:0x([0-9a-f]+)", t)
                    if m:
                        imports.add((a, int(m[1], 16)))
                    else:
                        ind.append((a, t))
            elif op == "jmp" or op.startswith("j"):
                m = re.fullmatch(r"\S+ 0x([0-9a-f]+)", t)
                if m:
                    v = int(m[1], 16)
                    if v in stop:
                        calls[a].add(v)
                    else:
                        work.append(v)
                else:
                    m = re.search(r"\*4\+0x([0-9a-f]+)\]", t)
                    if m:
                        ents = im.table(int(m[1], 16))
                        jt.append((a, int(m[1], 16), len(ents)))
                        work.extend(e for e in ents)
                    else:
                        m = re.search(r"ds:0x([0-9a-f]+)", t)
                        if m:
                            imports.add((a, int(m[1], 16)))
                        else:
                            ind.append((a, t))
                if op == "jmp":
                    break
            elif op in ("ret", "retn", "int3", "hlt", "ud2"):
                break
            a = im.next.get(a)
            if a is None:
                break
    return dict(seen=seen, calls=calls, ind=ind, jt=jt, taken=taken, imports=imports, entries=entries)


def seed_operand(im, a, reg="ecx", back=14):
    """The instruction that last set reg (in linear order) before a; a reading aid, not a proof."""
    i = im.idx[a]
    for j in range(i - 1, max(i - back, -1), -1):
        t = im.ins[im.order[j]]
        if re.match(r"(lea|mov) %s," % reg, t):
            return "%08X %s" % (im.order[j], t)
        if t.split()[0] in ("call", "ret"):
            break
    return "?"


def draws(im, c):
    out = []
    for a in sorted(c["seen"]):
        t = im.ins[a]
        if MULT in t:
            out.append((a, "inline", t))
        for v in c["calls"].get(a, ()):
            if v in PRIM:
                out.append((a, PRIM[v], seed_operand(im, a)))
            elif v in INIT:
                out.append((a, INIT[v] + " (no step)", seed_operand(im, a)))
    return out


def report(im, name, roots, stop=()):
    c = closure(im, roots, stop)
    print("== %s roots=%s" % (name, " ".join("0x%08X" % r for r in roots)))
    print("reached instructions=%d direct entries=%d indirect-unfollowed=%d jump-tables=%d import-calls=%d taken=%d" % (
        len(c["seen"]), len(c["entries"]), len(c["ind"]), len(c["jt"]), len(c["imports"]), len(c["taken"])))
    print("entries:", " ".join("%08X" % e for e in sorted(c["entries"])))
    for a, kind, x in draws(im, c):
        print("DRAW %08X %s | %s" % (a, kind, x))
    for a, t in sorted(c["ind"]):
        print("IND  %08X %s" % (a, t))
    for a, b, n in sorted(c["jt"]):
        print("JT   %08X table %08X entries %d" % (a, b, n))
    for a, b in sorted(c["taken"]):
        print("TAKE %08X -> %08X | %s" % (a, b, im.ins[a]))
    print("IMPORTS", " ".join(sorted({"%08X" % b for _, b in c["imports"]})))
    return c


# The sound core: code that exists to serve the mixer, its list and its tick. Named by what reads the gates, see the finding.
CORE = [(0x481700, 0x482CA0), (0x4B93A0, 0x4BABF0), (0x4DCA30, 0x4DCE60), (0x4DF630, 0x4E0700), (0x4E40A0, 0x4E4700),
        (0x513A20, 0x516CF0)]
# Bodies skipped under -ns: (gate address, gated entry)
SKIPPED = [("0x00405E15 config +0x220", 0x514530), ("0x0048226A 0x881768 (init)", 0x481950), ("0x0048226A", 0x4E0050),
           ("0x0048226A", 0x4B9D00), ("0x0048226A", 0x4DCA30), ("0x0048226A", 0x4CA280),
           ("0x004DCA3E config +0x220", 0x4DCA41),
           ("0x00482C27 0x7C8C78 (tick)", 0x4E42E0), ("0x00482C27", 0x4DCAA0), ("0x00482C27", 0x482B40),
           ("0x00482C27", 0x4BA020), ("0x00482C27", 0x4DF890),
           ("0x004B9A16 0x7C545C (play)", 0x4B9A21), ("0x00482947 0x881768 (close)", 0x4DF800), ("0x00482947", 0x4BAAB0)]
# Returns that differ under -ns because the list at 0x7C5458 is empty, the play gate 0x7C545C is 0, or 0x7C8C78 is 0.
QUERY = [0x4B9A00, 0x4B9B20, 0x4B9590, 0x4B95C0, 0x4B9610, 0x4B9BE0, 0x4B9C20, 0x4B9C60, 0x4B9CA0, 0x4B9D50, 0x4B9E90,
         0x4B9700, 0x4B9760, 0x4B9690, 0x4DF880, 0x4DF870, 0x4DF940, 0x4DF960, 0x4DF980, 0x4DF9B0, 0x513B50, 0x513B60,
         0x481860, 0x481890, 0x4818C0, 0x4818F0, 0x481920, 0x4817D0, 0x482680,  # the table pointers 0x7BC9A0, 0x7BC9A8 stay null
         0x513B70, 0x515060]


SEND = 0x52AE50  # the client's outgoing message call: size, 0, buffer; its 9 callers are 0x00477D88..0x00478525


def in_core(a):
    return any(l <= a < h for l, h in CORE)


def call_map(im):
    m = collections.defaultdict(list)
    for a in im.order:
        x = re.fullmatch(r"(call|jmp) 0x([0-9a-f]+)", im.ins[a])
        if x:
            m[int(x[2], 16)].append(a)
    return m


def func_start(im, cm, a):
    """Nearest earlier call target, or the instruction after int3 padding."""
    i = im.idx[a]
    while i > 0:
        v = im.order[i]
        if v in cm and any(im.ins[c].startswith("call") for c in cm[v]):
            return v
        if im.ins[im.order[i - 1]].startswith("int3"):
            return v
        i -= 1
    return a


def consume(im, a):
    """What the instructions after a call do with eax: ret, branch (with the jcc), store, arg, none."""
    cur = a
    touched = False
    for _ in range(8):
        cur = im.next[cur]
        t = im.ins[cur]
        op = t.split()[0]
        if op.startswith("ret"):
            return "ret", cur
        if op.startswith("j") and op != "jmp":
            return ("branch", cur) if touched else ("none", cur)
        if op in ("call", "jmp"):
            return ("arg", cur) if touched else ("none", cur)
        if re.search(r"\b(eax|al|ax)\b", t):
            if re.match(r"(xor eax,eax|lea eax,(?!.*eax)|pop eax|mov eax,(?!.*eax))", t):
                return "none", cur
            touched = True
            if re.match(r"mov (DWORD PTR )?(ds:|\[)", t) and t.endswith("eax") and "ds:" in t:
                return "store-global", cur
            if re.match(r"mov DWORD PTR \[", t) and t.endswith("eax"):
                return "store-field", cur
        if re.match(r"mov (e[a-z]+),eax", t):
            touched = True
    return "other", cur


def taint(im, roots=QUERY, verbose=True):
    cm = call_map(im)
    seen, work, rows = set(roots), list(roots), []
    while work:
        q = work.pop()
        for s in cm.get(q, []):
            if not im.ins[s].startswith("call"):
                continue
            kind, where = consume(im, s)
            fn = func_start(im, cm, s)
            row = dict(site=s, query=q, fn=fn, kind=kind, where=where, only=[])
            if kind == "ret" and fn not in seen and not in_core(fn):
                seen.add(fn)
                work.append(fn)
            if kind == "branch":
                t = im.ins[where]
                x = re.fullmatch(r"\S+ 0x([0-9a-f]+)", t)
                a = closure(im, [int(x[1], 16)])
                b = closure(im, [im.next[where]])
                da = {d[0]: d for d in draws(im, a) if "no step" not in d[1]}
                db = {d[0]: d for d in draws(im, b) if "no step" not in d[1]}
                row["only"] = sorted(set(da) ^ set(db))
                row["detail"] = {k: (da.get(k) or db.get(k)) for k in row["only"]}
                row["send"] = (SEND in a["entries"]) != (SEND in b["entries"])
            rows.append(row)
    return rows, seen


def main():
    im = Img(sys.argv[1])
    sec = sys.argv[2]
    args = sys.argv[3:]
    print("# instructions in .text sweep: %d; multiplier immediates: %d" % (
        len(im.order), sum(MULT in t for t in im.ins.values())))
    if sec == "gate":
        for lo, hi, why in ((0x405E09, 0x405E36, "InitGame: config +0x220 and the sound start"),
                            (0x4DCA30, 0x4DCA41, "the one global-held config reader"),
                            (0x482260, 0x48226C, "client init: device word 0x881768"),
                            (0x482940, 0x482949, "client close: device word 0x881768"),
                            (0x482C20, 0x482C60, "client tick: mixer word 0x7C8C78"),
                            (0x4E42E0, 0x4E42F6, "environment tick: mixer word again"),
                            (0x4B9A00, 0x4B9A21, "play: list word 0x7C545C"),
                            (0x482680, 0x482688, "group pick: sounds table pointer 0x7BC9A0")):
            print("== %s" % why)
            for a in im.order[im.idx[lo]:im.idx[hi]]:
                print("%08X %s" % (a, im.ins[a]))
    elif sec == "closure":
        report(im, "closure", [int(x, 16) for x in args])
    elif sec == "writers":
        for x in args:
            n = "0x%x" % int(x, 16)
            print("== %s" % x)
            for a in im.order:
                t = im.ins[a]
                if re.search(r"(ds:|\[|,|\+|push )%s\b" % n, t):
                    print("%08X %s" % (a, t))
    elif sec == "skipped":
        all_d, ind_all, taken_all = set(), {}, set()
        for gate, e in SKIPPED:
            c = closure(im, [e])
            d = [x for x in draws(im, c) if "no step" not in x[1]]
            print("%s -> %08X reach=%d entries=%d indirect=%d import-calls=%d draws=%d send=%s" % (
                gate, e, len(c["seen"]), len(c["entries"]), len(c["ind"]), len(c["imports"]), len(d), SEND in c["entries"]))
            for x in d:
                print("   %08X %s | %s" % x)
                all_d.add(x[0])
            for a, t in sorted(c["ind"]):
                ind_all[a] = t
            for a in c["taken"]:
                taken_all.add(a)
        print("distinct draw sites: %d" % len(all_d))
        print("indirect calls unfollowed, union over the bodies: %d" % len(ind_all))
        by = collections.Counter("core" if in_core(a) else "%02Xxxxx" % (a >> 20 << 4) for a in ind_all)
        print("by range:", dict(sorted(by.items())))
        for a, t in sorted(ind_all.items()):
            if in_core(a) or 0x420000 <= a < 0x520000:
                print("   IND %08X %s" % (a, t))
        print("code addresses taken in core:")
        for a, v in sorted(taken_all):
            if in_core(a):
                d2 = [x for x in draws(im, closure(im, [v])) if "no step" not in x[1]]
                print("   %08X -> %08X (%s) closure draws=%d" % (a, v, im.ins[a], len(d2)))
    elif sec == "api":
        cm = call_map(im)
        for t in sorted(cm):
            if in_core(t):
                e = [c for c in cm[t] if not in_core(c)]
                if e:
                    print("%08X outside-callers=%d largest=%08X" % (t, len(e), max(e)))
    elif sec == "leak":
        wr, rd = collections.defaultdict(list), collections.defaultdict(list)
        for a in im.order:
            t = im.ins[a]
            m = re.search(r"0x([0-9a-f]{6})\b", t)
            if not m or not 0x705000 <= int(m[1], 16) < 0x9A0000:
                continue
            v = int(m[1], 16)
            w = re.match(r"(mov|add|sub|inc|dec|and|or|xor|neg|not|fstp|fst)\b.*(ds:|\[)0x%s" % m[1], t) and not re.match(r"\S+ \w+,", t)
            (wr if w else rd)[v].append(a)
        n = 0
        for v in sorted(wr):
            w = [a for a in wr[v] if in_core(a)]
            if w:
                n += 1
                out = [a for a in rd[v] + wr[v] if not in_core(a)]
                if out:
                    print("%08X core-writers=%d outside: %s" % (v, len(w), " ".join("%08X" % a for a in out[:12])))
        print("globals written by core: %d" % n)
    elif sec == "pointers":
        cm = call_map(im)
        starts = {t for t in cm if in_core(t)} | set(QUERY) | {0x4B9EB0, 0x4E40A0, 0x4E4100, 0x4E4120, 0x473910}
        n = 0
        for b, sz, rp in im.secs:
            if b == 0x401000:
                continue
            for off in range(0, min(sz, len(im.raw) - rp) - 3, 4):
                v = struct.unpack_from("<I", im.raw, rp + off)[0]
                if v in starts:
                    n += 1
                    print("%08X = %08X" % (b + off, v))
        print("pointer hits: %d over %d starts" % (n, len(starts)))
        imm = 0
        for a in im.order:
            for h in HEX.findall(im.ins[a]):
                v = int(h, 16)
                if v in starts and not im.ins[a].startswith(("call", "jmp", "j")):
                    imm += 1
                    print("immediate %08X %s" % (a, im.ins[a]))
        print("immediate hits: %d" % imm)
    elif sec == "taint":
        rows, seen = taint(im)
        kinds = collections.Counter(r["kind"] for r in rows)
        print("query set after ret propagation: %d; call sites: %d; %s" % (len(seen), len(rows), dict(kinds)))
        print("largest consumer %08X" % max(r["site"] for r in rows))
        for r in sorted(rows, key=lambda r: r["site"]):
            if r["kind"] in ("none",):
                continue
            print("%08X -> %08X in %08X %s @%08X %s" % (r["site"], r["query"], r["fn"], r["kind"], r["where"], im.ins[r["where"]]))
            for k in r["only"]:
                print("     one-sided draw %08X %s | %s" % r["detail"][k])
            if r.get("send"):
                print("     one-sided client send (reaches 0x0052AE50 on one side only)")
    elif sec == "playerseed":
        cm = call_map(im)
        n = 0
        for s in cm[0x463DD0]:
            i = im.idx[s]
            ins = [im.ins[im.order[j]] for j in range(i + 1, i + 7)]
            if any(re.search(r"(add e[a-z]+,0x20$|\[e[a-z]+\+0x20\])", x) for x in ins) and any(
                    MULT in x or x.startswith("call 0x45c3") or "add ecx,0x20" in x for x in ins):
                n += 1
                print("%08X in %08X | %s" % (s, func_start(im, cm, s), "; ".join(ins)))
        print("sites: %d; 0x00463DD0 calls: %d; largest %08X" % (n, len(cm[0x463DD0]), max(cm[0x463DD0])))
        for t in (0x4E40A0, 0x4E4100, 0x4E4120):
            print("%08X callers: %s" % (t, " ".join("%08X/%08X" % (c, func_start(im, cm, c)) for c in cm[t])))
    elif sec == "control":
        # closure control: bodies a spec says draw must show draws here
        for name, e in (("DRLG_ActCreate", 0x642DA0), ("DRLG_RoomCreate", 0x66B3E0), ("UnitSeedInit", 0x552DF0)):
            c = closure(im, [e])
            d = [x for x in draws(im, c) if "no step" not in x[1]]
            print("closure control %s %08X reach=%d draws=%d first=%s" % (name, e, len(c["seen"]), len(d), "%08X" % d[0][0] if d else "NONE"))
        # taint control: a query the code really branches on with a draw on one side only
        rows, seen = taint(im, [0x4B9E90])
        for r in rows:
            print("taint control %08X %s @%08X one-sided=%s" % (r["site"], r["kind"], r["where"], " ".join("%08X" % k for k in r["only"])))
        # the planted negative: a query with no consumer gives no rows
        rows, seen = taint(im, [0x4B9B50])
        print("query with void callers: %s" % dict(collections.Counter(r["kind"] for r in rows)))
    else:
        sys.exit("unknown section")


if __name__ == "__main__":
    main()
