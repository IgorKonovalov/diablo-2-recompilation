#!/usr/bin/env python3
"""path/0005 W1: which functions a set of starts reaches, by direct calls, that call a marking function. A static walk over objdump's listing of the pinned image;
indirect calls are not followed and a function's body ends at its first int3.

    python3 -I tools/path_reach.py IMAGE --depth 3 --targets 0x64EA90,0x649400,0x620A70,0x648C30 --from 0x53ABE0,0x5381F0,...
"""
import argparse
import bisect
import re
import subprocess


def listing(image):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x401000", "--stop-address=0x6CB5A1", image], capture_output=True, text=True, check=True).stdout
    ins = []
    for line in out.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\t[^\t]*\t(.+)", line)
        if m:
            ins.append((int(m.group(1), 16), m.group(2).strip()))
    return ins


def direct_calls(ins, addrs, fn, limit=2000):
    out = []
    i = bisect.bisect_left(addrs, fn)
    for a, t in ins[i:i + limit]:
        if t.startswith("int3"):
            break
        m = re.match(r"call\s+0x([0-9a-f]+)", t)
        if m:
            out.append((a, int(m.group(1), 16)))
    return out


def reach(ins, start, targets, depth):
    """Breadth first: every path from `start` that ends in a call to a target, as ([functions], call site, target)."""
    addrs = [a for a, _ in ins]
    seen, queue, hits = set(), [(start, 0, ())], []
    while queue:
        fn, d, trail = queue.pop(0)
        if fn in seen:
            continue
        seen.add(fn)
        for site, callee in direct_calls(ins, addrs, fn):
            if callee in targets:
                hits.append((trail + (fn,), site, callee))
            elif d < depth:
                queue.append((callee, d + 1, trail + (fn,)))
    return len(seen), hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--targets", required=True)
    ap.add_argument("--from", dest="starts", required=True)
    a = ap.parse_args()
    ins = listing(a.image)
    targets = {int(x, 16) for x in a.targets.split(",")}
    print("depth %d targets %s" % (a.depth, " ".join("%08x" % t for t in sorted(targets))))
    for s in a.starts.split(","):
        n, hits = reach(ins, int(s, 16), targets, a.depth)
        print("%08x functions walked %d, paths to a target %d" % (int(s, 16), n, len(hits)))
        for trail, site, callee in hits:
            print("  %s -> call at %08x to %08x" % (" ".join("%08x" % f for f in trail), site, callee))


if __name__ == "__main__":
    main()
