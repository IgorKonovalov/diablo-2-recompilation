#!/usr/bin/env python3
"""Plan 0052's owner-played logs, late attach: what each log holds, and whether the AID fields no check compares hold. No game.

For each log: the header's seed and gdb file, the logger's rev, AGM, AIN, CAP, LOGERR, AIL lines, the frames and the states.
`t` (the target at AID): for a player target, its position against `pl`. `ctx[2]` against the target word the first boundary
call carries is left to the checks; here `t` is null-tested against `ctx[2]`.
`pl` (the first player at AID): against the latest PLR line before the AID line (PLR is the pilot's own line, a separate read of
the player's position; it is written on its own clock, so a distance is expected: DPL prints it).

Second part, --scan FILE...: every text in a logger's source that could write to the game: gdb's write_memory, `set var`, a
register assignment, a `set {`.

    python3 -I tools/ai_owner_fields.py LOG...
    python3 -I tools/ai_owner_fields.py --scan FILE...
    python3 -I tools/ai_owner_fields.py --setters EXE
"""
import json
import os
import re
import struct
import subprocess
import sys

WRITES = re.compile(r"write_memory|write_register|set\s+var|set\s+\{|set\s+\$|\.write\(\s*[^\"']|\$[a-z]{2,3}\s*=[^=]|\bcall\s+\(|\bprint\s+\$[a-z]+\s*=")


def scan(paths):
    for p in paths:
        hits = [(i + 1, ln.strip()[:100]) for i, ln in enumerate(open(p, errors="replace")) if WRITES.search(ln) and not ln.lstrip().startswith("#")]
        print("SCAN %s hits=%d" % (os.path.basename(p), len(hits)))
        for i, ln in hits:
            print("  %d: %s" % (i, ln))


def setters(exe):
    """Every direct call of MonAiInit 0x005B0E00, with the state argument: the last `push` before the call (stack order: state
    first pushed) as an immediate or a register. The table of SuperUniqueSpawn's switch at 0x005A4BF7 is read from the image."""
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x400000", "--stop-address=0x700000", exe], capture_output=True, text=True).stdout.splitlines()
    calls = [i for i, ln in enumerate(out) if ln.rstrip().endswith("call   0x5b0e00")]
    imm = {}
    for i in calls:
        pushes = []
        for ln in out[max(0, i - 24):i]:
            m = re.search(r"\tpush\s+(\S+)", ln)
            if m:
                pushes.append(m.group(1))
        k = pushes[-2] if len(pushes) >= 2 else "?"
        site = int(out[i].split(":")[0], 16)
        imm.setdefault(k, []).append(site)
    print("SETTERS direct_calls=%d" % len(calls))
    for k in sorted(imm):
        print("  state_push=%s calls=%d sites=%s" % (k, len(imm[k]), " ".join("%x" % v for v in imm[k][:8])))
    d = open(exe, "rb").read()
    pe = struct.unpack("<I", d[0x3C:0x40])[0]
    n, so = struct.unpack("<H", d[pe + 6:pe + 8])[0], struct.unpack("<H", d[pe + 20:pe + 22])[0]
    sec = [struct.unpack("<III", d[pe + 24 + so + 40 * i + 12:pe + 24 + so + 40 * i + 24]) for i in range(n)]

    def off(v):
        r = v - 0x400000
        return next(ra + r - va for va, sz, ra in sec if va <= r < va + sz)
    bytemap = d[off(0x005A4EA4):off(0x005A4EA4) + 0x39]
    tgt = [struct.unpack("<I", d[off(0x005A4E7C) + 4 * b:off(0x005A4E7C) + 4 * b + 4])[0] for b in bytemap]
    print("SWITCH 0x5A4BF7 cases=%d record_words_reaching_0x5A4BFE=%s" % (len(tgt), [i + 6 for i, t in enumerate(tgt) if t == 0x005A4BFE]))


def main(argv):
    if argv and argv[0] == "--scan":
        return scan(argv[1:])
    if argv and argv[0] == "--setters":
        return setters(argv[1])
    for p in argv:
        tags, states, rows, fr = {}, {}, {}, []
        head = ""
        plr = None
        tn = tbad = tnull = 0
        d_max, d_hist, ln_n = 0, {}, 0
        pl_null = 0
        rows61 = [0, 0]
        for ln in open(p, errors="replace"):
            if ln.startswith("# d2run"):
                head = ln.strip()
            tag = ln.split(" ", 1)[0].strip()
            if tag in ("AGM", "AIN", "CAP", "AIL", "LOGERR", "AID", "PLR"):
                tags[tag] = tags.get(tag, 0) + 1
            if tag == "PLR":
                try:
                    plr = json.loads(ln[4:])
                except ValueError:
                    pass
            if tag != "AID":
                continue
            a = json.loads(ln[4:])
            states[a["st"]] = states.get(a["st"], 0) + 1
            rows[a["ai"]] = rows.get(a["ai"], 0) + 1
            fr.append(a["fr"])
            t, pl = a.get("t"), a.get("pl")
            if bool(t) != bool(a["ctx"][2]):
                tnull += 1
            if t and t[0] == 0 and pl:
                tn += 1
                if [t[4], t[5]] != pl:
                    tbad += 1
            if pl is None:
                pl_null += 1
            elif plr:
                d = max(abs(pl[0] - plr["x"]), abs(pl[1] - plr["y"]))
                d_max = max(d_max, d)
                b = "0" if d == 0 else "1-5" if d <= 5 else "6-20" if d <= 20 else ">20"
                d_hist[b] = d_hist.get(b, 0) + 1
                if a["ai"] == 61:
                    rows61[0] += 1
                    rows61[1] += d <= 20
        seed = re.search(r"seed=(\d+)", head)
        gd = re.search(r"gdb=(\S+)", head)
        print("LOG %s seed=%s gdb=%s lines=%s frames=%s..%s states=%s rows=%s" % (
            os.path.basename(p), seed.group(1) if seed else None, gd.group(1) if gd else None, {k: tags.get(k, 0) for k in ("AGM", "AIN", "CAP", "AIL", "LOGERR", "AID", "PLR")},
            min(fr) if fr else None, max(fr) if fr else None, dict(sorted(states.items())), dict(sorted(rows.items()))))
        print("FIELDS %s t_vs_ctx2_bad=%d player_target=%d t_pos_ne_pl=%d pl_null=%d pl_vs_last_PLR=%s largest=%d row61_lines=%d row61_within20=%d" % (
            os.path.basename(p), tnull, tn, tbad, pl_null, dict(sorted(d_hist.items())), d_max, rows61[0], rows61[1]))


if __name__ == "__main__":
    main(sys.argv[1:])
