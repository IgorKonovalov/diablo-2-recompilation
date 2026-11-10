#!/usr/bin/env python3
"""How often the server's act clock pass sends packet 0x53 (plan 0063 Phase 2a, reading 3).

    python3 -I tools/act_clock.py <game.exe> [--cycles 2]

Reads the clock tables of the pinned image (scale table 0x007443E4, row tables 0x007443F0, 0x00744438, 0x00744480;
rows are (start, type, colour) dwords) and runs frame/0001 § 3.1's clock step and tick, the emulated map of
`sub_0061BEE0_ClockStep` and `sub_0061C040_ActClockTick`, from the state each server writer leaves:

  * `DUNGEON_ActCreate` -> 0x0061BE40: index 0, k = scale[0], p = 2, c = k * T0[2].start, flag 0, b = 0;
  * `A2Q3` eclipse on -> 0x0061C450: index 1, k = scale[1], p = 0, flag 1, c = k * T2[0].start (0x0061BDF0).

For each act index and state it prints the frames of one day (c back to its start), the frames on which the tick
returns 1 (a 0x53 send and every player's equipment refresh), split into bucket returns (|c / k - b| > 16) and row
returns ((p, v) changed), and the shortest and longest gap between sends over the cycles run. Integer semantics: c,
k and the products are int32 (no product here comes near 2^31: k <= 128, start <= 350); c / k truncates toward zero
on non-negative values. Reads the image only; writes nothing.
"""
import struct
import sys


def va2off(exe, va):
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    n = struct.unpack_from("<H", exe, pe + 6)[0]
    o = struct.unpack_from("<H", exe, pe + 20)[0]
    for i in range(n):
        _vs, ra, sz, ptr = struct.unpack_from("<IIII", exe, pe + 24 + o + 40 * i + 8)
        if ra <= va - 0x400000 < ra + sz:
            return ptr + va - 0x400000 - ra
    raise ValueError(hex(va))


def rows(exe, va):
    off = va2off(exe, va)
    return [struct.unpack_from("<iii", exe, off + 12 * i) for i in range(6)]


def step(s, a, T0, T1, T2):
    """sub_0061BEE0_ClockStep on state s (dict p, v, c, k, f) for act index a."""
    s["c"] += 1
    if s["f"] == 0:
        if a == 3:
            s["c"] += 15
        elif T0[s["p"]][1] == 2:
            s["c"] += 1
            if a == 2:
                s["c"] += 8
    k = s["k"]
    if s["c"] >= k * 360:
        s["c"] = 0
    n = 0 if s["p"] + 1 > 5 else s["p"] + 1
    T = T0 if s["f"] == 0 else (T1 if a == 3 else T2)
    if s["c"] > T[n][0] * k:
        s["p"] = n
        R = T0 if s["f"] == 0 else T2
        s["v"], s["c"] = R[n][1], R[n][0] * k


def tick(s, a, T0, T1, T2):
    """sub_0061C040_ActClockTick: 'b' for a bucket return, 'r' for a row return, None for 0."""
    p0, v0 = s["p"], s["v"]
    step(s, a, T0, T1, T2)
    if s["k"] != 0:
        q = int(s["c"] / s["k"])
        if abs(q - s["b"]) > 16:
            s["b"] = q
            return "b"
    return "r" if (s["p"], s["v"]) != (p0, v0) else None


def run(state, a, T0, T1, T2, cycles):
    s = dict(state)
    start = (s["p"], s["c"])
    frame, day, sends, last, gaps = 0, None, {"b": 0, "r": 0}, None, []
    days = 0
    while days < cycles and frame < 10_000_000:
        frame += 1
        r = tick(s, a, T0, T1, T2)
        if r:
            sends[r] += 1
            if last is not None:
                gaps.append(frame - last)
            last = frame
        if (s["p"], s["c"]) == start or (s["c"] == 0 and start[1] == 0 and s["p"] == start[0]):
            days += 1
            if day is None:
                day = frame
    return day, sends, (min(gaps) if gaps else None), (max(gaps) if gaps else None), frame


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    exe = open(argv[1], "rb").read()
    cycles = int(argv[argv.index("--cycles") + 1]) if "--cycles" in argv else 2
    scale = struct.unpack_from("<3i", exe, va2off(exe, 0x007443E4))
    T0, T1, T2 = rows(exe, 0x007443F0), rows(exe, 0x00744438), rows(exe, 0x00744480)
    print("scale table 0x007443E4:", scale)
    print("T0 (start, type):", [r[:2] for r in T0])
    print("T1 (start, type):", [r[:2] for r in T1])
    print("T2 (start, type):", [r[:2] for r in T2])
    k0, k1 = scale[0], scale[1]
    create = {"p": 2, "v": T0[2][1], "c": k0 * T0[2][0], "k": k0, "f": 0, "b": 0}
    eclipse = {"p": 0, "v": T2[0][1], "c": k1 * T2[0][0], "k": k1, "f": 1, "b": 0}
    print("state act a frames/day sends(bucket,row) per %d days  gap min..max  frames run" % cycles)
    for name, st, acts in (("create", create, range(5)), ("eclipse", eclipse, (1,))):
        for a in acts:
            day, sends, gmin, gmax, frames = run(st, a, T0, T1, T2, cycles)
            print("%-7s a=%d day=%s sends=%d (%d,%d) gap=%s..%s frames=%d"
                  % (name, a, day, sends["b"] + sends["r"], sends["b"], sends["r"], gmin, gmax, frames))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
