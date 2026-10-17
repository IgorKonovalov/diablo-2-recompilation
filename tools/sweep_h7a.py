"""Table and log reads of plan 0038 batch H7a (drlg/0009 § 11.3).

Usage:
  python3 -I tools/sweep_h7a.py skills [--excel DIR]
  python3 -I tools/sweep_h7a.py rec400 <rooms log> [...]

- `skills`: the Skills rows of Teleport (54) and MonTeleport (184) with `srvdofunc`, every MonStats row that names
  either skill in a Skill1..Skill8 column (Id, hcIdx, AI), and the MonAI row index of each AI named (the
  g_MonAiTable index, 0x0073CA18 + 16 * index). Lines `S`, `M`, `A`.
- `rec400`: from tools/gdb/rooms.gdb logs, every monster record with flag 0x400 (MREC: unit id, class, record flags,
  alignment from the record bits, room record x, y, frame, the US line's mode and +0xD0) and every restore that meets
  one (MR0 with the same unit id: frame, level, then the next MRC / MRX: created or dropped). Lines `R` (record), `T`
  (restore), and a count line per log.

Stdlib only. Read-only.
"""
import csv
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")


def rows(path):
    with open(path, encoding="latin1") as f:
        r = list(csv.reader(f, delimiter="\t"))
    return r[0], r[1:]


def cmd_skills(excel):
    print("# sweep_h7a.py skills")
    h, rs = rows(os.path.join(excel, "skills.txt"))
    for x in rs:
        d = dict(zip(h, x))
        if d.get("Id") in ("54", "184"):
            print("S %s %s srvdofunc=%s" % (d["Id"], d["skill"], d["srvdofunc"]))
    h, rs = rows(os.path.join(excel, "monstats.txt"))
    sk = [c for c in h if c.lower().startswith("skill") and c[5:].isdigit()]
    ais = set()
    for x in rs:
        d = dict(zip(h, x))
        hit = [c for c in sk if d[c] in ("MonTeleport", "Teleport", "54", "184")]
        if hit:
            print("M %s hcIdx=%s AI=%s %s" % (d["Id"], d["hcIdx"], d["AI"], ",".join("%s=%s" % (c, d[c]) for c in hit)))
            ais.add(d["AI"])
    h, rs = rows(os.path.join(excel, "monai.txt"))
    for i, x in enumerate(rs):
        if x and x[0] in ais:
            print("A %s index=%d table=0x%08X" % (x[0], i, 0x0073CA18 + 16 * i))


def cmd_rec400(logs):
    print("# sweep_h7a.py rec400 " + " ".join(logs))
    for path in logs:
        recs, n_r, n_t = {}, 0, 0
        us = None
        lines = open(path, errors="replace").read().split("\n")
        for i, line in enumerate(lines):
            if line.startswith("US "):
                us = json.loads(line[3:])
            elif line.startswith("MREC "):
                d = json.loads(line[5:])
                b = bytes.fromhex(d["b"])
                uid = struct.unpack_from("<i", b, 0x0C)[0]
                cls = struct.unpack_from("<i", b, 0x08)[0]
                fl = struct.unpack_from("<I", b, 0x18)[0]
                if fl & 0x400:
                    al = 2 if fl & 0x100 else (1 if fl & 0x80 else 0)
                    recs[uid] = cls
                    n_r += 1
                    print("R %s:%d f=%d id=%d class=%d flags=0x%X align=%d room=%d,%d mode=%s d0=%s" % (
                        os.path.basename(path), i + 1, d["f"], uid, cls, fl, al, d["rx"], d["ry"],
                        us and us.get("m"), us and us.get("d0")))
            elif line.startswith("MR0 "):
                d = json.loads(line[4:])
                b = bytes.fromhex(d["b"])
                uid = struct.unpack_from("<i", b, 0x0C)[0]
                fl = struct.unpack_from("<I", b, 0x18)[0]
                if not fl & 0x400:
                    continue
                out = "?"
                for j in range(i + 1, min(i + 12, len(lines))):
                    if lines[j].startswith("MRC "):
                        out = "created"
                        break
                    if lines[j].startswith("MRX "):
                        out = "dropped" if json.loads(lines[j][4:]).get("dropped") else "not dropped"
                        break
                    if lines[j].startswith("MR0 "):
                        break
                n_t += 1
                print("T %s:%d f=%d id=%d flags=0x%X lid=%s %s%s" % (
                    os.path.basename(path), i + 1, d["f"], uid, fl, d.get("lid"), out,
                    "" if uid in recs else " (record not seen in this log)"))
        print("N %s records=%d restores=%d" % (os.path.basename(path), n_r, n_t))


def main(argv):
    if not argv or argv[0] not in ("skills", "rec400"):
        print(__doc__)
        return 2
    if argv[0] == "skills":
        excel = argv[argv.index("--excel") + 1] if "--excel" in argv else EXCEL
        cmd_skills(excel)
    else:
        cmd_rec400(argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
