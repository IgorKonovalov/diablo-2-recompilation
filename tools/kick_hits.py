#!/usr/bin/env python3
"""The Kick row's delivered hits in kept skills logs (backlog 2026-10-27 kick start-hit damage).

    python3 -I tools/kick_hits.py <log> [...] [--excel DIR]

For every `SDO0` of skill 1 (Kick; `"a"` = [id, lvl, ...]) in a log written by tools/gdb/skills.py, it takes the lines up
to the matching `SDO1` (`"k"` = the `SDO0`'s `"n"`) and decodes each `AD0` packet (COMBAT_ApplyDamage 0x0057C6C0 at
entry, `"p"` = the 0x70-byte DamagePacket, re/types/combat.h) whose attacker `"a"` is the do event's unit: flags
+0x00, result +0x04, phys +0x08 and the hit class +0x60. It also counts the `SST0` start events of skill 1 and their
`SST1` returns, and lists the skills.bin rows whose `Kick` bit (+0x05 & 0x02, the mask GetPhysMin tests at 0x00647BF0)
is set. The model compared is skills/0003 § 5's start 2: phys = MinDam << HitShift of the Kick row of
--excel's skills.bin (default workspace/merged/data/global/excel), result 9, hit class 1. A line per log, then a
`KICK` total line; exit 1 when any delivered packet differs from the model. Stdlib only. Read-only.
"""
import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
REC = 0x23C
KICK = 1


def kick_row(excel):
    with open(os.path.join(excel, "skills.bin"), "rb") as fh:
        b = fh.read()
    n = struct.unpack_from("<I", b, 0)[0]
    flagged = [i for i in range(n) if b[4 + REC * i + 0x05] & 0x02]  # the `Kick` bit, +0x05 bit 1 (excel_layouts)
    r = b[4 + REC * KICK:4 + REC * (KICK + 1)]
    return {"rows": n, "flagged": flagged, "HitShift": r[0x1A4], "SrcDam": r[0x1A5], "MinDam": struct.unpack_from("<i", r, 0x1A8)[0],
            "MaxDam": struct.unpack_from("<i", r, 0x1AC)[0]}


def parse(line):
    tag, _, rest = line.partition(" ")
    if not rest.startswith("{"):
        return tag, None
    try:
        return tag, json.loads(rest)
    except ValueError:
        return tag, None


def scan(path):
    out = {"st": 0, "st_ret": {}, "do": 0, "ad": [], "do_no_ad": 0}
    open_do = {}  # n -> (unit, lvl, ads)
    st_open = set()
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            tag, d = parse(line.rstrip("\n"))
            if d is None:
                continue
            if tag == "SST0" and d.get("a", [None])[0] == KICK:
                out["st"] += 1
                st_open.add(d["n"])
            elif tag == "SST1" and d.get("k") in st_open:
                st_open.discard(d["k"])
                out["st_ret"][d["r"]] = out["st_ret"].get(d["r"], 0) + 1
            elif tag == "SDO0" and d.get("a", [None])[0] == KICK:
                out["do"] += 1
                open_do[d["n"]] = (d["u"]["u"], d["a"][1], [])
            elif tag == "AD0":
                for unit, lvl, ads in open_do.values():
                    if d.get("a") == unit:
                        ads.append(bytes.fromhex(d["p"]))
            elif tag == "SDO1" and d.get("k") in open_do:
                unit, lvl, ads = open_do.pop(d["k"])
                if not ads:
                    out["do_no_ad"] += 1
                for p in ads:
                    flags, result = struct.unpack_from("<IH", p, 0)
                    phys = struct.unpack_from("<i", p, 0x08)[0]
                    hcls = struct.unpack_from("<I", p, 0x60)[0]
                    out["ad"].append((lvl, flags, result, phys, hcls))
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--excel", default=EXCEL)
    a = ap.parse_args(argv)
    row = kick_row(a.excel)
    model = row["MinDam"] << row["HitShift"]
    print("KICKBIT rows=%d flagged=%s" % (row["rows"], row["flagged"]))
    print("ROW Kick id=%d HitShift=%d SrcDam=%d MinDam=%d MaxDam=%d model_phys=%d" % (
        KICK, row["HitShift"], row["SrcDam"], row["MinDam"], row["MaxDam"], model))
    tot = {"st": 0, "do": 0, "ad": 0, "bad": 0, "do_no_ad": 0}
    seen = {}
    for path in a.logs:
        o = scan(path)
        bad = 0
        for lvl, flags, result, phys, hcls in o["ad"]:
            key = (lvl, "0x%X" % flags, result, phys, hcls)
            seen[key] = seen.get(key, 0) + 1
            if phys != model or result != 9 or hcls != 1:
                bad += 1
        print("LOG %s st=%d st_ret=%s do=%d ad=%d do_no_ad=%d bad=%d" % (
            os.path.basename(path), o["st"], json.dumps(o["st_ret"], sort_keys=True), o["do"], len(o["ad"]),
            o["do_no_ad"], bad))
        tot["st"] += o["st"]
        tot["do"] += o["do"]
        tot["ad"] += len(o["ad"])
        tot["bad"] += bad
        tot["do_no_ad"] += o["do_no_ad"]
    for key in sorted(seen):
        print("PKT lvl=%d flags=%s result=%d phys=%d hitclass=%d count=%d" % (key + (seen[key],)))
    print("KICK logs=%d st=%d do=%d ad=%d do_no_ad=%d bad=%d" % (
        len(a.logs), tot["st"], tot["do"], tot["ad"], tot["do_no_ad"], tot["bad"]))
    return 1 if tot["bad"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
