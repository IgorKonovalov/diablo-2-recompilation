#!/usr/bin/env python3
"""Plan 0068 Phase 3: the COF bundles (`chars_cof.d2`, `cmncof_a1..a7.d2`) read with the layout of
the game's bundle loader (docs/findings/data/0006-loaded-tables-and-bundles.md § 4), then each embedded COF compared
with the loose `.cof` of the same name and with the `animdata.d2` record of the same name.

    python3 -I tools/cofbundle.py survey <root> [--list]        e.g. workspace/merged
    python3 -I tools/cofbundle.py dump <file.d2>                one line per record

`survey` ends with the gate line
    SURVEY cofbundle files=N records=N errors=N cof_errors=N leftover_bytes=N dup_names=N rt_other=N
            name_pad_nonzero=N upper_names=N
(rt_other counts records whose runtime fields next/flags/data are not 0xFFFFFFFF/0/0xFFFFFFFF; name_pad_nonzero those with a non-zero byte
after the name's NUL; upper_names those whose name has an upper-case letter; dup_names the names repeated inside one file).

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


def _offsets(data):
    off = 0
    while off < len(data):
        yield off
        off += 0x18 + struct.unpack_from("<I", data, off + 8)[0]


def dump(path):
    data = open(path, "rb").read()
    recs, err = records(data)
    for off, (name, body) in zip(_offsets(data), recs):
        print("0x%08X %-8s size=%d layers=%d frames=%d dirs=%d" % (off, name, len(body), body[0], body[1], body[2]))
    print("records=%d error=%s" % (len(recs), err))
    return 0 if err is None else 1


def main(root, listing=False):
    base = os.path.join(root, "data", "global")
    loose = animdata.cof_index(root)
    ad = {}
    for r in animdata.load(os.path.join(base, "animdata.d2")):
        ad.setdefault(r.name, r)  # first in file order
    st = dict(cof_errors=0, leftover_bytes=0, dup_names=0, rt_other=0, name_pad_nonzero=0, upper_names=0)
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
        seen = set()
        for off_, (name, body) in zip(_offsets(data), recs):
            if name in seen:
                st["dup_names"] += 1
            seen.add(name)
            if (struct.unpack_from("<II", data, off_), struct.unpack_from("<I", data, off_ + 0x14)[0]) != \
                    ((0xFFFFFFFF, 0), 0xFFFFFFFF):
                st["rt_other"] += 1
            if any(data[off_ + 0xC + len(name) + 1:off_ + 0x14]):
                st["name_pad_nonzero"] += 1
            if name != name.lower():
                st["upper_names"] += 1
            try:
                st["leftover_bytes"] += cof.parse(body)["extra"]
            except cof.COFError:
                st["cof_errors"] += 1
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
    print("SURVEY cofbundle files=%d records=%d errors=%d cof_errors=%d leftover_bytes=%d dup_names=%d rt_other=%d "
          "name_pad_nonzero=%d upper_names=%d" % (t["files"], t["records"], t["errors"], st["cof_errors"],
                                                  st["leftover_bytes"], st["dup_names"], st["rt_other"],
                                                  st["name_pad_nonzero"], st["upper_names"]))
    return 0 if t["errors"] == 0 and st["cof_errors"] == 0 else 1


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--list"]
    if len(a) == 2 and a[0] == "survey":
        sys.exit(main(a[1], "--list" in sys.argv[1:]))
    if len(a) == 2 and a[0] == "dump":
        sys.exit(dump(a[1]))
    sys.exit(__doc__)
