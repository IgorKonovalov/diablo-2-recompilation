"""The lane/r29 review's control on ADR-0029 rule (a): a `tools/ghidra.sh emuclobber` output against the kept `drop.out`.

Per case it compares what drop's checker uses (EAX, the dumps), the pop and the step count, which a changed path would move, and
for a whole run the executed set and the traced accesses. EDX is printed, not judged: the checker compares none and a clobber moves
it where nothing writes it after the last lock. A control only: no tag rests on it.
Usage: python3 -I tools/drop_clobber_compare.py <emuclobber out> <kept drop.out>
"""
import sys


def split(path):
    cases, rest, cur = [], {"P": [], "R": [], "W": []}, None
    with open(path, encoding="ascii") as f:
        for x in f.read().splitlines():
            if x.startswith("C "):
                cur = [x.split(), []]
                cases.append(cur)
            elif x.startswith("D "):
                cur[1].append(x)
            elif x[:2] in ("P ", "R ", "W "):
                rest[x[0]].append(x)
    return cases, rest


def main():
    a, ra = split(sys.argv[1])
    k, rk = split(sys.argv[2])
    same = dict(eax=0, edx=0, pop=0, steps=0, dump=0)
    stopped = differ = 0
    for x, y in zip(a, k):
        if x[0][3] == "STOP":
            stopped += 1
            differ += 1
            continue
        fx = {p.split("=")[0]: p for p in x[0] if "=" in p}
        fy = {p.split("=")[0]: p for p in y[0] if "=" in p}
        for f in ("eax", "edx", "pop", "steps"):
            same[f] += fx.get(f) == fy.get(f)
        same["dump"] += x[1] == y[1]
        differ += fx.get("eax") != fy.get("eax") or x[1] != y[1] or fx.get("steps") != fy.get("steps") or fx.get("pop") != fy.get("pop")
    print("CLOBBER cases=%d of=%d stopped=%d differ=%d same_eax=%d same_edx=%d same_pop=%d same_steps=%d same_dump=%d" % (len(a), len(k), stopped, differ, same["eax"], same["edx"], same["pop"], same["steps"], same["dump"]))
    if len(a) == len(k):
        print("CLOBBER executed_set_equal=%s executed=%d reads_equal=%s writes_equal=%s" % (ra["P"] == rk["P"] if rk["P"] else "n/a", len(ra["P"]), ra["R"] == rk["R"], ra["W"] == rk["W"]))


if __name__ == "__main__":
    main()
