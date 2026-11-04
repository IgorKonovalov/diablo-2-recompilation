#!/usr/bin/env python3
"""Backlog -ns priority, route 2: logs of the same -seed, one sound-on run and one -ns run, compared where the map-seed
chain makes them independent of the player's inputs (python3 -I).

    sound_pair.py <sound.log> <ns.log> [<sound.log> <ns.log> ...]
    sound_pair.py stream <log> [<log> ...]         # the logged game seed values ("gs"), walked as one stream
    sound_pair.py mutate <log> <out> <tag> <field> # flip one bit of the first <field> seed on a <tag> line (the control)

For each pair, per (level id, client flag): the LC0 create seed, the LC0 base (levelSeedBase) and the sequence of RC room
seeds of each build (the `level` object of RC lines is tied to its id by the last LC0 or LI0 for that object). Two logs
of one seed were played differently, so only levels built in both are compared. A rebuild repeats its sequence
(drlg/experiments.md run:2026-10-12-drlg-gen); each log's set of distinct sequences is compared.

A control is built in: the same comparison of the sound log against the next pair's -ns log (a different seed) must
differ on every level both built, or the comparison separates nothing.
"""
import collections
import json
import re
import sys


def load(path):
    lc, base = {}, set()
    obj = {}
    rc = collections.defaultdict(lambda: collections.defaultdict(list))
    build = collections.Counter()
    with open(path, "rb") as h:
        for raw in h:
            tag = raw[:4]
            if tag not in (b"LC0 ", b"LI0 ", b"RC {"):
                continue
            line = raw.decode("latin1").rstrip()
            t, _, js = line.partition(" ")
            try:
                d = json.loads(js)
            except ValueError:
                continue
            if t in ("LC0", "LI0"):
                key = (d["id"], d["client"])
                if t == "LC0":
                    lc[key] = d["seed"]
                    base.add((d["client"], d["id"] // 1, d["base"]))
                build[key] += 1
                obj[d["level"]] = (key, build[key])
            elif t == "RC" and "level" in d and d["level"] in obj:
                key, b = obj[d["level"]]
                rc[key][b].append(d["seed"])
    seqs = {k: {tuple(v) for v in bs.values() if v} for k, bs in rc.items()}
    return lc, seqs


def compare(a, b):
    la, ra = a
    lb, rb = b
    both = sorted(set(la) & set(lb))
    same_seed = sum(la[k] == lb[k] for k in both)
    rk = sorted(set(ra) & set(rb))
    seqs_same = rooms = 0
    bad = []
    for k in rk:
        common = ra[k] & rb[k]
        if common:
            seqs_same += 1
            rooms += max(len(s) for s in common)
        else:
            bad.append(k)
    return len(both), same_seed, len(rk), seqs_same, rooms, bad


MULT = 0x6AC690C5
SEED = re.compile(r'"gs":"([0-9a-f]{8}):([0-9a-f]{8})"')


def stream(path, limit=4096):
    """Each logged game seed is reached from the one before by k Steps, or the stream is broken."""
    prev = None
    hist = collections.Counter()
    broken = n = 0
    with open(path, "rb") as h:
        for raw in h:
            m = SEED.search(raw.decode("latin1"))
            if not m:
                continue
            cur = (int(m[1], 16), int(m[2], 16))
            n += 1
            if prev is not None and cur != prev:
                lo, hi = prev
                for k in range(1, limit + 1):
                    v = lo * MULT + hi
                    lo, hi = v & 0xFFFFFFFF, v >> 32
                    if (lo, hi) == cur:
                        hist[k if k < 8 else ("8-63" if k < 64 else "64+")] += 1
                        break
                else:
                    broken += 1
            elif prev is not None:
                hist[0] += 1
            prev = cur
    return n, broken, hist


def mutate(src, out, tag, field):
    pat = re.compile(r'"%s":"([0-9a-f]{8}):' % field)
    done = False
    with open(src, "rb") as h, open(out, "wb") as w:
        for raw in h:
            if not done and raw.startswith(tag.encode() + b" "):
                line = raw.decode("latin1")
                m = pat.search(line)
                if m:
                    line = line[:m.start(1)] + "%08x" % (int(m[1], 16) ^ 1) + line[m.end(1):]
                    raw = line.encode("latin1")
                    done = True
            w.write(raw)
    print("mutated %s %s: %s" % (tag, field, done))


def main(argv):
    if argv[0] == "stream":
        for p in argv[1:]:
            n, broken, hist = stream(p)
            print("%s: gs values %d; breaks %d; steps between changes %s" % (p.rsplit("/", 1)[-1], n, broken, sorted(hist.items(), key=str)))
        return
    if argv[0] == "mutate":
        mutate(*argv[1:])
        return
    pairs = [(argv[i], argv[i + 1]) for i in range(0, len(argv), 2)]
    loaded = [(load(a), load(b)) for a, b in pairs]
    tot = [0] * 5
    for i, ((a, b), (la, lb)) in enumerate(zip(pairs, loaded)):
        r = compare(la, lb)
        for j in range(5):
            tot[j] += r[j]
        print("%s | %s" % (a.rsplit("/", 1)[-1], b.rsplit("/", 1)[-1]))
        print("  levels created in both %d, same create seed %d; levels with RC in both %d, a common room sequence %d (%d rooms); no common sequence: %s" % (
            r[0], r[1], r[2], r[3], r[4], r[5]))
        other = loaded[(i + 1) % len(loaded)][1]
        c = compare(la, other)
        print("  control, against the next pair's -ns log: levels %d, same create seed %d; levels with RC %d, a common room sequence %d" % (
            c[0], c[1], c[2], c[3]))
    print("total: levels created in both %d, same create seed %d; levels with RC in both %d, a common room sequence %d (%d rooms)" % tuple(tot))


if __name__ == "__main__":
    main(sys.argv[1:])
