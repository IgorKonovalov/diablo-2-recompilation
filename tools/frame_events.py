#!/usr/bin/env python3
"""Plan 0055 phase 1.2 (the server frame: the unit events and the queue, `lane/r55b`): byte-level surveys of the
pinned Game.exe for frame/0002. No game run, no Ghidra; stdlib and `objdump`, read-only.

    python3 -I tools/frame_events.py tables            the type-to-list map and the five types' event dispatch tables
    python3 -I tools/frame_events.py kinds [--xrefs F] the event kind pushed at every call of the queue entry points
                                                       (F: a `tools/ghidra.sh xrefs` output naming each site's function)

`tables`: `g_UnitTypeEventList` (0x006E0B9C, 7 dwords read: unit types 0..5 and the null-unit index 6) and, per
dispatch table, the first 15 dwords (the kind bound of the player and monster dispatch, `kind < 15`), each named from
re/symbols.csv when it is a function entry there, `text` when it points into .text, else the raw value.

`kinds`: for each direct call to a queue entry point (from `objdump -d` of the image), the event kind: the entry's
first stack argument for `UnitQueueEvent` (0x005417D0, game in ECX, unit in EDX, then kind, frame, a, b), for
`0x00541800` (kind, frame, callback, a, b) and for `UnitQueueEveryFrame` (0x00541650: kind, a, b), that is the push
nearest before the call (walking back over at most 12 non-push instructions, stopping at a jump, call or return). A
constant push gives the kind; a register push `reg`, a memory push `mem`, no push found `none`. For `EventQueueAt` (0x005416B0) the kind is ECX and for
`EventQueueEveryFrame` (0x005415E0) EBX: the scan reports the wrappers' own sites (the only callers, by `xrefscan`).
Per entry it prints one line per site and a histogram of the kinds. Needs `objdump` (binutils).
"""
import argparse
import bisect
import csv
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
CSV = os.path.join(ROOT, "re", "symbols.csv")

TYPE_LIST = 0x006E0B9C
TABLES = [
    ("g_PlayerEventFuncs", 0x006E1810),
    ("g_MonEventFuncs", 0x006E2490),
    ("g_ObjEventFns", 0x006E19B0),
    ("g_ItemEventFuncs", 0x006E117C),
]
ENTRIES = [
    ("UnitQueueEvent", 0x005417D0),
    ("UnitQueueEventCb", 0x00541800),
    ("UnitQueueEveryFrame", 0x00541650),
    ("UnitQueueEveryFrameCb", 0x00541680),
]


def load_pe():
    d = open(EXE, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    optsz = struct.unpack_from("<H", d, pe + 20)[0]
    base = struct.unpack_from("<I", d, pe + 24 + 28)[0]
    so = pe + 24 + optsz
    secs = []
    for i in range(nsec):
        o = so + 40 * i
        name = d[o:o + 8].rstrip(b"\0").decode("latin-1")
        vsize, va, rsize, rptr = struct.unpack_from("<IIII", d, o + 8)
        flags = struct.unpack_from("<I", d, o + 36)[0]
        secs.append((name, base + va, vsize, rptr, rsize, flags))
    return d, secs


def va2off(secs, va):
    for name, sva, vsize, rptr, rsize, flags in secs:
        if sva <= va < sva + min(vsize, rsize):
            return rptr + va - sva
    return None


def symbols():
    out = {}
    for r in csv.DictReader(open(CSV)):
        out[int(r["address"], 16)] = (r["name"], r["kind"], r["confidence"])
    return out


def in_text(secs, v):
    return any(f & 0x20000000 and sva <= v < sva + vsize for _, sva, vsize, _, _, f in secs)


def cmd_tables():
    d, secs = load_pe()
    syms = symbols()
    off = va2off(secs, TYPE_LIST)
    vals = struct.unpack_from("<7i", d, off)
    print("TYPELIST 0x%08X %s" % (TYPE_LIST, " ".join("%d:%d" % (i, v) for i, v in enumerate(vals))))
    for name, va in TABLES:
        off = va2off(secs, va)
        print("TABLE %s 0x%08X" % (name, va))
        for k in range(15):
            v = struct.unpack_from("<I", d, off + 4 * k)[0]
            if v in syms:
                desc = "%s [%s]" % (syms[v][0], syms[v][2])
            elif v == 0:
                desc = "null"
            elif in_text(secs, v):
                desc = "text (unnamed)"
            else:
                desc = "not code"
            print("  %s[%d] = 0x%08X %s" % (name, k, v, desc))


def read_xrefs(path):
    site2fn = {}
    if not path:
        return site2fn
    for ln in open(path):
        p = ln.split()
        if len(p) >= 5 and p[0] == "to":
            site2fn[int(p[1], 16)] = p[4]
    return site2fn


def objdump_text():
    """`objdump -d -M intel --no-show-raw-insn` of the image: [(va, mnemonic, operands)] in address order."""
    import re
    import subprocess
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", EXE], capture_output=True,
                         text=True, check=True).stdout
    rx = re.compile(r"^\s+([0-9a-f]+):\s+(\S+)\s*(.*)$")
    ins = []
    for ln in out.splitlines():
        m = rx.match(ln)
        if m:
            ins.append((int(m.group(1), 16), m.group(2), m.group(3).strip()))
    return ins


def first_push_before(ins, i, limit=12):
    """The operand of the push nearest before instruction i (the callee's first stack argument), walking back over
    non-push instructions; None at a control transfer or after `limit` instructions."""
    for j in range(i - 1, max(-1, i - 1 - limit), -1):
        va, mn, op = ins[j]
        if mn == "push":
            return op
        if mn.startswith("j") or mn in ("call", "ret", "int3"):
            return None
    return None


def cmd_kinds(xrefs):
    site2fn = read_xrefs(xrefs)
    ins = objdump_text()
    for ename, target in ENTRIES:
        hist = {}
        lines = []
        for i, (va, mn, op) in enumerate(ins):
            if mn != "call" or not op.startswith("0x"):
                continue
            try:
                if int(op.split()[0], 16) != target:
                    continue
            except ValueError:
                continue
            o = first_push_before(ins, i)
            if o is None:
                k = "none"
            elif o.startswith("0x"):
                k = "%d" % int(o, 16)
            elif o in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"):
                k = "reg"
            else:
                k = "mem"
            hist[k] = hist.get(k, 0) + 1
            lines.append("  SITE 0x%08X kind=%s push=%s fn=%s" % (va, k, o, site2fn.get(va, "?")))
        print("ENTRY %s 0x%08X sites=%d" % (ename, target, len(lines)))
        for ln in lines:
            print(ln)
        print("  HIST %s" % " ".join("%s:%d" % (k, hist[k]) for k in sorted(hist, key=lambda x: (len(x), x))))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["tables", "kinds"])
    ap.add_argument("--xrefs")
    a = ap.parse_args(argv)
    if a.cmd == "tables":
        cmd_tables()
    else:
        cmd_kinds(a.xrefs)


if __name__ == "__main__":
    main(sys.argv[1:])
