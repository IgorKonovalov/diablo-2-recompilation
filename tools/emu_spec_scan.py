"""Scan every emulator memory spec under a log tree for per-case directives the pre-fix scripts did not re-apply.

Plan 0055 (lane/r55e). EmuTrace.java, EmuBoundary.java and EmuCall.java re-write a spec's non-`const` directives
before every case. Before the lane/r55e fix they passed the same byte array each time, and Ghidra 12.1's
MemoryPageBank.setPage keeps that array as the page itself (no copy) when the write starts on a 4 KiB boundary and
is 0x1000 bytes or more: the emulated code's stores then went into the array, and the next case re-wrote them.
Only the first page of such a directive is kept by reference (a later whole page has a non-zero buffer offset and is
copied).

A file is taken as a memory spec when every non-comment line starts with load, dword, bytes, const, guard or observe.
Usage: python3 -I tools/emu_spec_scan.py <log root> [<repo root for relative load paths> [<skipped subdir>...]]
Output: one line per spec holding at least one affected directive (aligned, >= 0x1000, not const):
  AFFECTED <spec path> <directive> <hex addr> <hex len>
then the long directives that are not affected (unaligned or const), and a SUMMARY line.
"""
import os
import sys

KEYS = {"load", "dword", "bytes", "const", "guard", "observe"}


def directives(path):
    out = []
    try:
        with open(path, "r", encoding="ascii") as f:
            lines = f.read().splitlines()
    except (UnicodeDecodeError, OSError):
        return None
    for line in lines:
        t = line.split("#", 1)[0].strip()
        if not t:
            continue
        f = t.split()
        if f[0] not in KEYS:
            return None
        out.append(f)
    return out or None


def length(f, spec_dir, repo):
    kind = f[0]
    if kind == "dword":
        return 4
    if kind == "bytes":
        return len(f[2]) // 2
    if kind == "load":
        p = f[2]
        cands = [p] if os.path.isabs(p) else [os.path.join(b, p) for b in (repo, spec_dir, os.getcwd())]
        if "/workspace/" in p:  # an absolute path into another worktree's workspace symlink: the same shared tree
            cands.append(os.path.join(repo, "workspace", p.split("/workspace/", 1)[1]))
        for q in cands:
            if os.path.exists(q):
                return os.path.getsize(q)
        return -1
    return 0


def main():
    root = sys.argv[1]
    repo = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    skip = [os.path.join(root, x) for x in sys.argv[3:]]
    specs = affected_specs = 0
    affected, other = [], []
    for d, _, files in sorted(os.walk(root)):
        if any(d == x or d.startswith(x + os.sep) for x in skip):
            continue
        for name in sorted(files):
            p = os.path.join(d, name)
            if os.path.getsize(p) > 64 << 20:
                continue
            ds = directives(p)
            if ds is None:
                continue
            specs += 1
            hit = False
            for f in ds:
                const = f[0] == "const"
                g = f[1:] if const else f
                if g[0] in ("guard", "observe"):
                    continue
                a = int(g[1], 16)
                n = length(g, d, repo)
                if n == -1:
                    other.append(f"MISSING {p} {g[0]} {a:08x} {g[2]}")
                    continue
                if n < 0x1000:
                    continue
                if not const and a % 0x1000 == 0:
                    affected.append(f"AFFECTED {p} {g[0]} {a:08x} {n:x}")
                    hit = True
                else:
                    why = "const" if const else "unaligned"
                    other.append(f"LONG-{why.upper()} {p} {g[0]} {a:08x} {n:x}")
            affected_specs += hit
    for line in affected + other:
        print(line)
    print(f"SUMMARY specs={specs} affected_specs={affected_specs} affected_directives={len(affected)} other_long={len(other)}")


if __name__ == "__main__":
    main()
