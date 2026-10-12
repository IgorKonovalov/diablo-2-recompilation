"""Check a tools/gdb/d2s-io.gdb log (plan 0013 Phase 2, run:2026-10-12-d2s-io) against the saves it wrote and read.

Usage:
  python3 -I tools/d2sio.py check <excel-dir> <log> [<saved.d2s> ...]

For every save written (a WDONE line, with the WHDR/WLVL/WTIME/SBIT lines since its SAVE line):
  - parses the logged buffer with tools/d2s.py (layout of docs/formats/d2s.md) and compares every header field
    with the runtime value logged at write: magic, version, file_size (= bytes written), checksum
    (= rotate-left-1-and-add with the field zeroed), weapon_set (client +0x45C), name (client +0x0D), the u32
    status (client +0x0A | 0x20 expansion | 0x40 ladder), class (client +0x08), 0x29 = 16, 0x2A = 30, level
    (= stat 12 as read by the writer), unk_2c (client +0x488), last_played (= time() in the writer), unk_34,
    mouse skills (player data +0x70..+0x8C: skill id, item ref 0 for "no item"), difficulty bytes (game
    difficulty byte = client act | 0x80, the others 0), map_seed (game +0x7C), 0xCF (client +0x480), the other
    unk_bf bytes 0, and the character stats ('gf') against the unit's base stat list;
  - for every item serialised in the final pass (SBIT final=true), the file item at the logged offset:
    flags (runtime item-data flags with bit 19 cleared and bit 23 set; bit 21 may be added, compactsave),
    version, location (= unit mode), body, store (= inventory page + 1), code, and for extended items seed
    (= unit +0x28), ilvl, quality, gfx;
  - the item count (final-pass SBIT lines = items in the file);
  - for an item logged at its drop (CPOST, same unit and unit id), the saved seed, quality and ilvl against the
    values logged when the drop created it.
For every load (RHDR ... RHRET / RERR / LFIN2): checksum and size as logged; the reader's code predicted from the
file (6 if the model checksum differs from the stored one, else 5 if the size field differs from the length, else 0)
against D2S_ReadHeader's return (RHRET) and, on failure, the failure exit's internal code, with the mapped code 14; the map-seed branch (RMAP/RMAP2),
the client fields read (unk_2c, class, status, act, weapon switch, 0xCF), the stats read (RSTAT) against the file's
'gf' list, the items read (RITEM: seed, ilvl, quality, version, code, mode) against the file's items in order, the
act map seed against the game's, and D2S_LoadFinish's stats 7/9 (LFIN/LFIN2).
Each <saved.d2s> must hash to a logged WDONE buffer. Prints one line per check group, "MISMATCH" lines, and exits 0
only when nothing mismatched. Stdlib only.
"""
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import d2s  # noqa: E402


def events(path):
    out = []
    for line in open(path, encoding="latin1"):
        tag, _, rest = line.partition(" ")
        if rest.startswith("{"):
            try:
                out.append((tag, json.loads(rest)))
            except ValueError:
                pass
    return out


class Checker:
    def __init__(self):
        self.n = 0
        self.bad = 0

    def eq(self, what, got, want):
        self.n += 1
        if got != want:
            self.bad += 1
            print("  MISMATCH %s: file %r, runtime %r" % (what, got, want))


def check_write(ck, buf, whdr, wlvl, wtime, sbits, isc, kinds, drops=None):
    f = d2s.parse(buf, isc, kinds)
    h = f["header"]
    u32 = lambda o: struct.unpack_from("<I", buf, o)[0]  # noqa: E731
    u16 = lambda o: struct.unpack_from("<H", buf, o)[0]  # noqa: E731
    ck.eq("magic", u32(0), 0xAA55AA55)
    ck.eq("version", h["version"], 96)
    ck.eq("file_size", h["file_size"], len(buf))
    ck.eq("checksum", h["checksum"], d2s.checksum(buf))
    ck.eq("weapon_set bit 0", h["weapon_set"] & 1, int(whdr["wsw"] != 0))
    ck.eq("name", h["name"], whdr["name"])
    ck.eq("status u32", u32(0x24), whdr["status"] | (0x20 if whdr["g70"] else 0) | (0x40 if whdr["g74"] else 0))
    ck.eq("class", h["cls"], whdr["cls"])
    ck.eq("0x29", buf[0x29], 16)
    ck.eq("0x2A", buf[0x2A], 30)
    ck.eq("level 0x2B", h["level"], wlvl["stat12"] & 0xFF)
    ck.eq("unk_2c", h["unk_2c"], whdr["c488"])
    ck.eq("last_played", h["last_played"], wtime["time"])
    ck.eq("unk_34", h["unk_34"], 0xFFFFFFFF)
    pd = whdr.get("pd")
    if pd:
        # file slots left, right, swap A, swap B <- player data +0x74/+0x7C, +0x70/+0x78, +0x84/+0x8C, +0x80/+0x88
        for slot, (sk, ref) in enumerate(((1, 3), (0, 2), (5, 7), (4, 6))):
            ck.eq("mouse[%d] skill" % slot, u16(0x78 + 4 * slot), pd[sk] & 0xFFFF)
            if pd[ref] in (0, 0xFFFFFFFF):
                ck.eq("mouse[%d] item ref" % slot, u16(0x7A + 4 * slot), 0)
    want = bytearray(3)
    want[whdr["g6d"]] = whdr["act"] | 0x80
    ck.eq("difficulty", h["difficulty"], bytes(want))
    ck.eq("map_seed", h["map_seed"], whdr["g7c"])
    ck.eq("0xCF", buf[0xCF], int(whdr["c480"][:2], 16))
    ck.eq("unk_bf other bytes zero", bytes(buf[0xBF:0xCF]) + bytes(buf[0xD0:0x14F]), bytes(0x8F))
    rt = [(i, p if isc[i]["csv_param"] else None, v) for i, p, v in whdr["stats"] if isc.get(i, {}).get("csv_bits")]
    ck.eq("gf stats", [tuple(s) for s in f["stats"]], rt)
    items = {it["off"]: it for it in d2s.all_items(f)}
    final = [s for s in sbits if s["final"]]
    ck.eq("item count", len(final), len(items))
    for s in final:
        it = items.get(s["off"])
        if it is None:
            ck.eq("item at 0x%X" % s["off"], None, s.get("code"))
            continue
        tag = "item %s@0x%X" % (s.get("code"), s["off"])
        exp = (s["flags"] & ~0x80000) | 0x800000
        ck.eq(tag + " flags (bit 21 aside)", it["flags"] & ~0x200000, exp & ~0x200000)
        ck.eq(tag + " version", it["version"], s["ver"])
        ck.eq(tag + " location", it["location"], s["mode"])
        if s["mode"] not in (3, 5):
            ck.eq(tag + " body", it["body"], s["body"])
            ck.eq(tag + " store", it["store"], (s["page"] + 1) & 7)
        ck.eq(tag + " code", it.get("code"), s.get("code"))
        if not it["simple"]:
            ck.eq(tag + " seed", it["seed"], s["seed28"])
            ck.eq(tag + " ilvl", it["ilvl"], s["ilvl"])
            ck.eq(tag + " quality", it["quality"], s["q"])
            if it["has_gfx"]:
                ck.eq(tag + " gfx", it["gfx"], s["gfx"])
        drop = (drops or {}).get((s["unit"], s["id"]))
        if drop and not it["simple"]:
            print("  dropped item %s id %d at 0x%X: drop seed %d q %d ilvl %d; saved seed %d q %d ilvl %d" % (
                drop.get("code"), s["id"], s["off"], drop["seed28"], drop["q"], drop["ilvl"], it["seed"],
                it["quality"], it["ilvl"]))
            ck.eq(tag + " seed = drop's unit+0x28", it["seed"], drop["seed28"])
            ck.eq(tag + " quality = drop's", it["quality"], drop["q"])
            ck.eq(tag + " ilvl = drop's", it["ilvl"], drop["ilvl"])
    return f, len(final)


def check_read(ck, buf, ev, isc, kinds):
    """ev: the events of one load, from RHDR up to (not including) the next RHDR."""
    tags = [t for t, _ in ev]
    out = {}
    rsum = next((d for t, d in ev if t == "RSUM"), None)
    if rsum:
        out["checksum_ok"] = rsum["computed"] == rsum["stored"]
        ck.eq("RSUM computed == model", rsum["computed"], d2s.checksum(buf))
        out["size_ok"] = rsum["size_field"] == rsum["len"]
    rerr = next((d for t, d in ev if t == "RERR"), None)
    rhret = next((d for t, d in ev if t == "RHRET"), None)
    out["header_code"] = rhret["code"] if rhret else None
    out["err"] = rerr
    # The reader's code predicted from the file alone (D2S_ReadHeader: checksum first, then the size field).
    stored, size_field = struct.unpack_from("<II", buf, 0x08)[::-1]
    predicted = 6 if d2s.checksum(buf) != stored else 5 if size_field != len(buf) else 0
    out["predicted"] = predicted
    ck.eq("D2S_ReadHeader code (RHRET) = predicted", out["header_code"], predicted)
    if predicted:
        ck.eq("failure exit internal code (RERR) = predicted", rerr["internal"] if rerr else None, predicted)
    if rerr and rerr["internal"] != 0:
        ck.eq("failure exit mapped code (RERR)", rerr["mapped"], 14)
    if rerr or not rhret or rhret["code"] != 0:
        return out
    f = d2s.parse(buf, isc, kinds)
    h = f["header"]
    rmap = next(d for t, d in ev if t == "RMAP")
    rmap2 = next(d for t, d in ev if t == "RMAP2")
    reuse = rmap["g6a"] == 3 and rmap["g84"] == 0 and rmap["bit7"] != 0
    ck.eq("RMAP bit7 = difficulty byte & 0x80", rmap["bit7"], h["difficulty"][rmap["g6d"]] & 0x80)
    ck.eq("RMAP2 game+0x7C", rmap2["g7c"], h["map_seed"] if reuse else rmap["g7c"])
    out["reuse"] = reuse
    ck.eq("read unk_2c -> client +0x488", rhret["c488"], h["unk_2c"])
    ck.eq("read class", rhret["cls"], h["cls"])
    ck.eq("read status", rhret["status"], struct.unpack_from("<H", buf, 0x24)[0])
    ck.eq("read act", rhret["act"], (h["difficulty"][rmap["g6d"]] & 0x7F) % 5 if (h["difficulty"][rmap["g6d"]] & 0x7F) < 5 else 0)
    ck.eq("read weapon switch", int(rhret["wsw"] != 0), h["weapon_set"] & 1)
    ck.eq("read 0xCF -> client +0x480", int(rhret["c480"][:2], 16), buf[0xCF])
    rs = [(d["id"], d["param"], d["value"]) for t, d in ev if t == "RSTAT"]
    fs = [(i, p or 0, v - (1 << isc[i]["csv_bits"]) if isc[i]["csv_signed"] and v >> (isc[i]["csv_bits"] - 1) else v)
          for i, p, v in f["stats"]]
    ck.eq("RSTAT list", rs, fs)
    ri = [d for t, d in ev if t == "RITEM"]
    fi = list(d2s.all_items(f))
    ck.eq("RITEM count", len(ri), len(fi))
    for r, it in zip(ri, fi):
        tag = "read item %s@0x%X" % (it.get("code"), it["off"])
        ck.eq(tag + " code", r.get("code"), it.get("code"))
        ck.eq(tag + " version", r["ver"], it["version"])
        ck.eq(tag + " mode", r["mode"], it["location"])
        ck.eq(tag + " flags (bit 19, 25 aside)", r["flags"] & ~0x2080000, it["flags"] & ~0x2080000)
        if it["simple"]:
            ck.eq(tag + " seed (simple: 0)", r["seed28"], 0)
            ck.eq(tag + " ilvl (simple: 1)", r["ilvl"], 1)
            ck.eq(tag + " quality (simple: 2)", r["q"], 2)
        else:
            ck.eq(tag + " seed", r["seed28"], it["seed"])
            ck.eq(tag + " rng seed lo", int(r["rng20"].split(":")[0], 16), it["seed"])
            ck.eq(tag + " ilvl", r["ilvl"], it["ilvl"])
            ck.eq(tag + " quality", r["q"], it["quality"])
    acts = [d for t, d in ev if t == "ACT"]
    for a in acts:
        ck.eq("ACT map seed", a["map"], rmap2["g7c"])
    lfin = next((d for t, d in ev if t == "LFIN"), None)
    lfin2 = next((d for t, d in ev if t == "LFIN2"), None)
    file_stats = {i: v for i, p, v in f["stats"]}
    if lfin and lfin2:
        for sid in (7, 9):
            ck.eq("stat %d at D2S_LoadFinish entry" % sid, lfin["base"].get(str(sid)), file_stats.get(sid))
            ck.eq("stat %d after D2S_LoadFinish" % sid, lfin2["base"].get(str(sid)), file_stats.get(sid))
        out["lfin"] = (lfin, lfin2)
    out["nitems"] = len(ri)
    out["nstats"] = len(rs)
    return out


def check(excel, log, saved):
    isc, kinds = d2s.load_isc(excel), d2s.load_kinds(excel)
    ev = events(log)
    ck = Checker()
    written = {}
    nwrite = 0
    drops = {}
    cur = None
    for k, (t, d) in enumerate(ev):
        if t == "CPOST":
            drops[(d["unit"], d["id"])] = d
        elif t == "SAVE":
            cur = {"save": d, "sbits": [], "whdr": None, "wlvl": None, "wtime": None, "psave": None}
            if k and ev[k - 1][0] == "PSAVE":
                cur["psave"] = ev[k - 1][1]
        elif cur is not None and t in ("WHDR", "WLVL", "WTIME"):
            cur[t.lower()] = d
        elif cur is not None and t == "SBIT":
            cur["sbits"].append(d)
        elif cur is not None and t == "WDONE":
            buf = bytes.fromhex(d["hex"])
            n0 = ck.n
            nwrite += 1
            print("WRITE #%d %s ret=%08X caller=%s size=%d sha256=%s" % (
                nwrite, d["path"], cur["save"]["ret"],
                "%08X" % cur["psave"]["ret"] if cur["psave"] else "?", d["size"], d["sha256"][:16]))
            f, nitems = check_write(ck, buf, cur["whdr"], cur["wlvl"], cur["wtime"], cur["sbits"], isc, kinds, drops)
            print("  header, %d stats, %d items: %d comparisons" % (len(f["stats"]), nitems, ck.n - n0))
            written.setdefault(d["sha256"], buf)
            cur = None
    starts = [k for k, (t, _) in enumerate(ev) if t == "RHDR"]
    for j, k in enumerate(starts):
        end = starts[j + 1] if j + 1 < len(starts) else len(ev)
        d = ev[k][1]
        buf = bytes.fromhex(d["hex"])
        n0 = ck.n
        r = check_read(ck, buf, ev[k:end], isc, kinds)
        print("READ #%d len=%d sha256=%s checksum_ok=%s size_ok=%s predicted=%s header_code=%s err=%s reuse=%s items=%s stats=%s: "
              "%d comparisons" % (j + 1, d["len"], d["sha256"][:16], r.get("checksum_ok"), r.get("size_ok"),
                                  r.get("predicted"), r.get("header_code"), r.get("err"), r.get("reuse"), r.get("nitems"),
                                  r.get("nstats"), ck.n - n0))
    for p in saved:
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        ck.eq("%s is a logged WDONE buffer" % p, h in written, True)
    print("TOTAL %d comparisons, %d mismatches" % (ck.n, ck.bad))
    return 0 if ck.bad == 0 else 1


def main(argv):
    if len(argv) < 3 or argv[0] != "check":
        print(__doc__)
        return 2
    return check(argv[1], argv[2], argv[3:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
