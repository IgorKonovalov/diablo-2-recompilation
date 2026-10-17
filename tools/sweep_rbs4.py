#!/usr/bin/env python3
"""Static scans of the reverser sweep pass 4 (`lane/rbs4`) over the pinned Game.exe.

    python3 -I tools/sweep_rbs4.py tree 0xADDR [--depth N] [--stop 0xADDR ...]
    python3 -I tools/sweep_rbs4.py calls 0xFUNC [0xFUNC ...]
    python3 -I tools/sweep_rbs4.py regarg 0xADDR REG [--back N]
    python3 -I tools/sweep_rbs4.py stackfield 0xADDR K 0xOFF
    python3 -I tools/sweep_rbs4.py dwords 0xADDR N
    python3 -I tools/sweep_rbs4.py layouts [ACT ...]

Builds on tools/sweep_rbs3.py (same objdump disassembly, same function entries from re/symbols.csv and `int3`
padding). Every output starts with a `#` line that echoes the command, so a re-run reproduces the kept file byte for
byte.

- `tree ADDR`: the reverse call tree of ADDR: every function with a direct `call`/`jmp` to ADDR, then every function
  calling one of those, breadth first, to `--depth` levels (default 3). A function already listed is not expanded
  again (`seen`); a `--stop` function is listed but not expanded. Lines: `T <depth> <callee entry> <- <site>
  <caller entry> <name>`, then a count line per depth. Only direct calls: an indirect call (a vtable, a function
  pointer table) is not seen: use xrefscan.py for absolute references.
- `calls FUNC`: the direct calls a function makes, from its entry to the next entry: `C <site> <target> <name>`.
- `regarg ADDR REG [--back N]`: per direct call to ADDR, the last instruction within N (default 12) before the call
  that sets REG (`mov REG,…`, `lea REG,…`, `xor REG,REG`, `or REG,0xffffffff`): `R <site> <function> <name> <value>`;
  `?` when none is found inside the window (read the window). A branch into the window is not seen.
- `stackfield ADDR K OFF`: per direct call to ADDR whose K-th stack argument (1 = nearest push) is an `ebp`-based local
  (`lea REG,[ebp-M]` before the push, or `push` of such an address), every write in the calling function that touches
  byte OFF of that local: `mov`/`or`/`and` of a byte, word or dword at `[ebp-M+OFF-k]` for k < width. Lines:
  `F <site> <function> <name> local=<M>` then `W <write site> <instruction>`; `F … local=?` when the argument is
  not such a local (read the window). Writes through another register (a copy of the address) are not seen.
- `dwords ADDR N`: N little-endian dwords read from the image at ADDR: `D <index> <address> <value>`.
- `layouts [ACT ...]` (act indices 0, 1, 3, 4; default all four): every outdoor layout the act link builder can give,
  per difficulty, with the H5e (a) vertex-merge condition of `sweep_h5e.py` tested on each outdoor level. It runs
  `drlg.act_links` (the one model of `LevelLinkBuild`, checked in run:2026-10-15-drlg-maze) with the act seed replaced
  by a scripted one: every draw the builder makes is used only through its low bits (`& 7`, `& 3`, `& 1`, `~v & 1`),
  so each draw is enumerated over the values of the bits it is masked with, independently of the others. That is a
  superset of the layouts the LCG can reach (draws are not independent, and the two Act I tables start from the same
  act seed), so a condition met nowhere here is met by no seed. A draw used any other way stops the run (fatal). Act
  III (`act_links_a3`, the jungle layout with ranged draws and restarts) is not covered. Lines: `L <act> <diff>
  layouts <n> draws<=<max>`, `M <act> <diff> <level> <reason>` per layout and reason met (first 20), then per act and
  difficulty `O <act> <diff> <level> side <s> neighbour <nb> overlap min <a> max <b>` and the total `N`.

Stdlib only. Read-only.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sweep_rbs3  # noqa: E402


def callers_of(img, t):
    pat = re.compile(r"^(call|jmp) 0x%x$" % t)
    out = []
    for a, txt in img.ins:
        if pat.match(txt):
            e, name = img.func(a)
            out.append((a, e, name))
    return out


def cmd_tree(img, root, depth, stops):
    seen = {root}
    level = [root]
    for d in range(1, depth + 1):
        nxt = []
        nsites = 0
        for t in level:
            for a, e, name in callers_of(img, t):
                nsites += 1
                mark = ""
                if e in stops:
                    mark = " stop"
                elif e in seen:
                    mark = " seen"
                print("T %d 0x%08X <- 0x%08X 0x%08X %s%s" % (d, t, a, e, name, mark))
                if e not in seen:
                    seen.add(e)
                    if e not in stops:
                        nxt.append(e)
        print("N depth %d: %d sites, %d new functions" % (d, nsites, len(nxt)))
        level = nxt
        if not level:
            break


def cmd_calls(img, funcs):
    for f in funcs:
        i = img.entries.index(f) if f in img.entries else None
        if i is None:
            raise SystemExit("%#x is not a function entry" % f)
        end = img.entries[i + 1] if i + 1 < len(img.entries) else 1 << 32
        n = 0
        for a, txt in img.ins:
            if f <= a < end:
                m = re.match(r"^(call|jmp) 0x([0-9a-f]+)$", txt)
                if m:
                    t = int(m.group(2), 16)
                    if f <= t < end:
                        continue
                    n += 1
                    print("C 0x%08X 0x%08X %s %s" % (a, t, m.group(1), img.names.get(t, "-")))
        print("N 0x%08X %d calls out" % (f, n))


def cmd_regarg(img, target, reg, back):
    pat = re.compile(r"^(call|jmp) 0x%x$" % target)
    k = 0
    for i, (a, txt) in enumerate(img.ins):
        if not pat.match(txt):
            continue
        val = "?"
        for j in range(i - 1, max(-1, i - back - 1), -1):
            t = img.ins[j][1]
            if re.match(r"^(mov|lea|movzx|movsx) %s," % reg, t):
                val = t.split(",", 1)[1].replace(" ", "")
                break
            if t == "xor %s,%s" % (reg, reg):
                val = "0"
                break
            if t == "or %s,0xffffffff" % reg:
                val = "-1"
                break
            if t.startswith("call ") or t.startswith("ret"):
                val = "?call" if t.startswith("call ") else "?"
                break
        e, name = img.func(a)
        k += 1
        print("R 0x%08X 0x%08X %s %s" % (a, e, name, val))
    print("N 0x%08X %d calls (%s)" % (target, k, reg))


def func_range(img, a):
    e, name = img.func(a)
    i = img.entries.index(e)
    end = img.entries[i + 1] if i + 1 < len(img.entries) else 1 << 32
    return e, end, name


def cmd_stackfield(img, target, k, off):
    pat = re.compile(r"^call 0x%x$" % target)
    ncall = 0
    nw = 0
    for i, (a, txt) in enumerate(img.ins):
        if not pat.match(txt):
            continue
        ncall += 1
        e, end, name = func_range(img, a)
        got = 0
        reg = None
        m_local = None
        j = i - 1
        while j > i - 30:
            t = img.ins[j][1]
            if t.startswith("push "):
                got += 1
                if got == k:
                    reg = t[5:]
                    break
            j -= 1
        if reg is not None:
            if re.fullmatch(r"e[a-z]{2}", reg):
                for jj in range(j - 1, max(-1, j - 20), -1):
                    t = img.ins[jj][1]
                    m = re.match(r"^lea %s,\[ebp-0x([0-9a-f]+)\]$" % reg, t)
                    if m:
                        m_local = int(m.group(1), 16)
                        break
                    if re.match(r"^\w+ %s," % reg, t):
                        break
        if m_local is None:
            print("F 0x%08X 0x%08X %s local=? arg=%s" % (a, e, name, reg))
            continue
        print("F 0x%08X 0x%08X %s local=0x%x" % (a, e, name, m_local))
        want = m_local - off
        for b, t in img.ins:
            if not (e <= b < end):
                continue
            m = re.match(r"^(mov|or|and|xor|add|sub|inc|dec) (BYTE|WORD|DWORD) PTR \[ebp-0x([0-9a-f]+)\]", t)
            if not m:
                continue
            w = {"BYTE": 1, "WORD": 2, "DWORD": 4}[m.group(2)]
            d = int(m.group(3), 16)
            if d >= want > d - w:
                nw += 1
                print("W 0x%08X %s" % (b, t))
    print("N 0x%08X %d calls, %d writes to byte %#x of argument %d" % (target, ncall, nw, off, k))


class _Need(Exception):
    def __init__(self, mask):
        self.mask = mask


class _Probe(int):
    def __and__(self, m):
        if m not in (1, 3, 7):
            raise SystemExit("layouts: a draw masked with %r" % (m,))
        raise _Need(m)

    __rand__ = __and__

    def __invert__(self):
        raise _Need(1)

    def _other(self, *a):
        raise SystemExit("layouts: a draw used other than by a low-bit mask")

    __mod__ = __rshift__ = __add__ = __radd__ = __mul__ = __sub__ = __floordiv__ = __or__ = __xor__ = _other


class _Script:
    """A seed whose draws come from a shared script; past its end a draw is a probe."""

    def __init__(self, state):
        self.st = state
        self.n = 0

    def copy(self):
        return _Script(self.st)

    def step(self):
        st = self.st
        k = st["pos"]
        st["pos"] += 1
        self.n += 1
        if k < len(st["vals"]):
            return st["vals"][k]
        return _Probe(0)


def cmd_layouts(acts):
    import collections
    import drlg
    import sweep_h5e
    data = drlg.Data(drlg.DEFAULT_DATA, drlg.DEFAULT_EXE)
    drlg.load_outdoor(data.root, data.exe)
    out = {i for i in range(len(data.drlgtype)) if data.drlgtype[i] == 3}
    total_met = 0
    for acti in acts:
        for diff in (0, 1, 2):
            n = 0
            maxd = 0
            met = 0
            ov = {}
            stack = [[]]
            while stack:
                vals = stack.pop()
                A = drlg.Act(acti, 1, diff)
                st = {"vals": vals, "pos": 0}
                A.seed = _Script(st)
                try:
                    drlg.act_links(A)
                except _Need as e:
                    for v in range(e.mask, -1, -1):
                        stack.append(vals + [v])
                    continue
                n += 1
                maxd = max(maxd, st["pos"])
                for lid in sorted(A.rect):
                    if lid not in out or drlg.LV[lid]["act"] != acti:
                        continue
                    adj = A.adj.get(lid, [])
                    why = sweep_h5e.vertex_merge_condition(A.rect[lid], adj)
                    for w in why:
                        met += 1
                        if met <= 20:
                            print("M %d %d %d %s draws %s" % (acti, diff, lid, w, vals))
                    for nb, side, o in sweep_h5e.seam_overlaps(A.rect[lid], adj):
                        key = (lid, side, nb)
                        lo, hi = ov.get(key, (o, o))
                        ov[key] = (min(lo, o), max(hi, o))
            print("L %d %d layouts %d draws<=%d met %d" % (acti, diff, n, maxd, met))
            for (lid, side, nb), (lo, hi) in sorted(ov.items()):
                print("O %d %d %d side %d neighbour %d overlap min %d max %d" % (acti, diff, lid, side, nb, lo, hi))
            total_met += met
    print("N vertex-merge condition met %d" % total_met)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exe", default=sweep_rbs3.EXE)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("tree")
    p.add_argument("root")
    p.add_argument("--depth", type=int, default=3)
    p.add_argument("--stop", action="append", default=[])
    p = sub.add_parser("calls")
    p.add_argument("funcs", nargs="+")
    p = sub.add_parser("regarg")
    p.add_argument("target")
    p.add_argument("reg")
    p.add_argument("--back", type=int, default=12)
    p = sub.add_parser("stackfield")
    p.add_argument("target")
    p.add_argument("k", type=int)
    p.add_argument("off")
    p = sub.add_parser("layouts")
    p.add_argument("acts", nargs="*", type=int)
    p = sub.add_parser("dwords")
    p.add_argument("addr")
    p.add_argument("n", type=int)
    a = ap.parse_args(argv)
    print("# sweep_rbs4.py " + " ".join(argv))
    if a.cmd == "layouts":
        cmd_layouts(a.acts or [0, 1, 3, 4])
        return
    if a.cmd == "dwords":
        read = sweep_rbs3.image_reader(a.exe)
        base = int(a.addr, 16)
        for i in range(a.n):
            print("D %d 0x%08X 0x%08X" % (i, base + 4 * i, int.from_bytes(read(base + 4 * i, 4), "little")))
        return
    img = sweep_rbs3.Image(a.exe)
    if a.cmd == "tree":
        cmd_tree(img, int(a.root, 16), a.depth, {int(s, 16) for s in a.stop})
    elif a.cmd == "stackfield":
        cmd_stackfield(img, int(a.target, 16), a.k, int(a.off, 16))
    elif a.cmd == "regarg":
        cmd_regarg(img, int(a.target, 16), a.reg, a.back)
    else:
        cmd_calls(img, [int(f, 16) for f in a.funcs])


if __name__ == "__main__":
    main(sys.argv[1:])
