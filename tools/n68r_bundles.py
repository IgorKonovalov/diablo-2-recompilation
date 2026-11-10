#!/usr/bin/env python3
"""Plan 0068 Phase 2 item 4 check: the COF bundles (`chars_cof.d2`, `cmncof_a1..a7.d2`) read with the layout of
the game's bundle loader (docs/findings/data/0006-loaded-tables-and-bundles.md § 4), then each embedded COF compared
with the loose `.cof` of the same name and with the `animdata.d2` record of the same name.

    python3 -I tools/n68r_bundles.py <root> [--list]        e.g. workspace/merged

--list adds one DIFF line per COF whose frames or event bytes differ from animdata.d2, and per COF that differs
from its loose file.

Loader layout (fn 0x0046DDF0): no file header; records back to back to the end of the file, each a 0x18-byte header
{u32 next (runtime), u32 flags (runtime), u32 size, char name[8] (NUL within the 8), u32 data (runtime)} and `size`
bytes of COF. The loader refuses a name of more than 7 characters (source line 0x79) and a COF whose byte 2
(directions) is above 0x40 (line 0x126).

Prints one line per bundle and ends with
    BUNDLES files=N records=N errors=N loose_same=N loose_diff=N loose_absent=N
            ad_frames_same=N ad_frames_diff=N ad_events_same=N ad_events_diff=N ad_absent=N
where `ad_events` compares the COF's non-zero frame bytes (frame, value) with animdata's non-zero event bytes.
Stdlib only, read-only.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import animdata  # noqa: E402
import cof  # noqa: E402

BUNDLES = ["chars_cof.d2"] + ["cmncof_a%d.d2" % k for k in range(1, 8)]


def records(data):
    """-> ([(name, cof bytes)], error or None) in file order."""
    out, off = [], 0
    while off < len(data):
        if off + 0x18 > len(data):
            return out, "header past end at 0x%X" % off
        size = struct.unpack_from("<I", data, off + 8)[0]
        raw = data[off + 0xC:off + 0x14]
        nul = raw.find(b"\0")
        if nul <= 0:
            return out, "name not NUL-terminated within 8 at 0x%X" % off
        if off + 0x18 + size > len(data):
            return out, "body past end at 0x%X" % off
        body = data[off + 0x18:off + 0x18 + size]
        if len(body) < 3 or body[2] > 0x40:
            return out, "directions > 0x40 at 0x%X" % off
        out.append((raw[:nul].decode("latin-1"), body))
        off += 0x18 + size
    return out, None


def main(root, listing=False):
    base = os.path.join(root, "data", "global")
    loose = animdata.cof_index(root)
    ad = {}
    for r in animdata.load(os.path.join(base, "animdata.d2")):
        ad.setdefault(r.name, r)  # first in file order
    t = dict(files=0, records=0, errors=0, loose_same=0, loose_diff=0, loose_absent=0, ad_frames_same=0,
             ad_frames_diff=0, ad_events_same=0, ad_events_diff=0, ad_absent=0)
    for fn in BUNDLES:
        path = os.path.join(base, fn)
        if not os.path.exists(path):
            print("%-14s absent" % fn)
            continue
        data = open(path, "rb").read()
        recs, err = records(data)
        t["files"] += 1
        t["records"] += len(recs)
        t["errors"] += 1 if err else 0
        local = dict(same=0, diff=0, absent=0, fdiff=0, ediff=0, adabs=0)
        for name, body in recs:
            paths = loose.get(name.upper(), [])
            if not paths:
                local["absent"] += 1
                t["loose_absent"] += 1
            elif any(open(p, "rb").read() == body for p in paths):
                local["same"] += 1
                t["loose_same"] += 1
            else:
                local["diff"] += 1
                t["loose_diff"] += 1
                if listing:
                    print("DIFF loose %s %s" % (fn, name))
            r = ad.get(name.upper())
            if r is None:
                local["adabs"] += 1
                t["ad_absent"] += 1
                continue
            try:
                c = cof.parse(body)
            except cof.COFError:
                t["errors"] += 1
                continue
            if c["frames_per_dir"] == r.frames:
                t["ad_frames_same"] += 1
            else:
                local["fdiff"] += 1
                t["ad_frames_diff"] += 1
                if listing:
                    print("DIFF frames %s %s cof=%d animdata=%d" % (fn, name, c["frames_per_dir"], r.frames))
            cev = [(i, v) for i, v in enumerate(c["frame_bytes"]) if v]
            if cev == animdata.events_of(r):
                t["ad_events_same"] += 1
            else:
                local["ediff"] += 1
                t["ad_events_diff"] += 1
                if listing:
                    print("DIFF events %s %s cof=%s animdata=%s" % (fn, name, cev, animdata.events_of(r)))
        print("%-14s bytes=%d records=%d error=%s loose same=%d diff=%d absent=%d animdata absent=%d "
              "frames_diff=%d events_diff=%d"
              % (fn, len(data), len(recs), err, local["same"], local["diff"], local["absent"], local["adabs"],
                 local["fdiff"], local["ediff"]))
    print("BUNDLES " + " ".join("%s=%d" % kv for kv in t.items()))
    return 0 if t["errors"] == 0 else 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--list"]
    if len(args) != 1:
        sys.exit(__doc__)
    sys.exit(main(args[0], "--list" in sys.argv[1:]))
