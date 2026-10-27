#!/usr/bin/env python3
"""Checker of plan 0038 batch H1a (run:2026-10-27-sweep-d2s-load): the loads of tool-built saves logged by
tools/gdb/d2s-h1a.gdb through tools/h1a_sessions.py.

    python3 -I tools/sweep_h1a.py check <excel-dir> <cases-dir> <log> [<log> ...]

For every log it first runs `tools/d2sio.py check` (every write and read the d2s-io model covers, with its own
MISMATCH lines), then, per case of the log's <stem>.marks.jsonl (the runner's record of where each case starts),
compares the case's lines with what save/0001 reads in the code:

  - the swapped file (<cases-dir>/<swap>/<name>.d2s) is the buffer the server read (RHDR hex, or RSV's byte count
    when D2S_ReadSave refused it before D2S_ReadHeader);
  - the code of each step: D2S_ReadSave (RSV), the header (RHRET), D2S_CheckStatus (RCST), the failure exit
    (RERR: internal and mapped through g_D2sLoadErrorMap), the code the join tests (PLD), predicted by `model()`
    below from the file, the listed file (the client's status and difficulty) and the game fields logged;
  - per case, the fields the case was built for (act clamp, quest and waypoint records after the read, skill count
    and the section cursor after the skills, the old stat form, the item fields, the written file).
Prints one line per comparison group, MISMATCH lines, a total, and exits 0 only when nothing mismatched. Stdlib only.
"""
import hashlib
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import d2s  # noqa: E402
import d2sio  # noqa: E402

DIFF = {"normal": 0, "nightmare": 1, "hell": 2, "none": 0}


class Ck:
    def __init__(self):
        self.n = 0
        self.bad = 0

    def eq(self, what, got, want):
        self.n += 1
        if got != want:
            self.bad += 1
            print("  MISMATCH %s: logged %r, expected %r" % (what, got, want))


def events(path):
    out = []
    for k, line in enumerate(open(path, encoding="latin1")):
        tag, _, rest = line.partition(" ")
        if rest.startswith("{"):
            try:
                out.append((k, tag, json.loads(rest)))
            except ValueError:
                pass
    return out


def header_model(buf, list_status, diff, client_name):
    """D2S_ReadSave (0x00534330) and D2S_ReadHeader (0x0056A090) on a buffer, for a single-player game the client
    made from the listed file: returns (D2S_ReadSave's own code or None, ReadHeader code or None, CheckStatus code
    or None). The game is expansion iff the listed status has bit 5, hardcore iff it has bit 2 (the client makes the
    game from the character it lists); its difficulty is the one chosen."""
    if len(buf) < 8 or struct.unpack_from("<I", buf, 0)[0] != d2s.MAGIC:
        return 9, None, None
    if struct.unpack_from("<I", buf, 4)[0] <= 91:
        return "legacy", None, None
    c = d2sio.file_code(buf)
    if c:
        return None, c, None
    name = buf[0x14:0x23].split(b"\0")[0].decode("latin1")
    if name.lower() != client_name.lower():
        return None, 7, None
    st = struct.unpack_from("<H", buf, 0x24)[0]
    exp_game, hc_game = bool(list_status & 0x20), bool(list_status & 0x04)
    if st & 0x20 and not exp_game:
        cs = 8
    elif not st & 0x20 and exp_game:
        cs = 9
    elif st & 0x04 and st & 0x08:
        cs = 10
    elif st & 0x04 and not hc_game:
        cs = 11
    elif not st & 0x04 and hc_game:
        cs = 12
    else:
        prog = (st >> 8) & 0x1F
        cs = 0
        if diff > 1 and prog < (10 if st & 0x20 else 8):
            cs = 14
        elif diff == 1 and prog < (5 if st & 0x20 else 4):
            cs = 13
    if cs:
        return None, cs, cs
    if buf[0x28] > 7:
        return None, 4, 0
    if st & 1:
        return None, 2, 0
    return None, 0, 0


def check_case(ck, mark, ev, cases, cname, isc, kinds, keep_dir):
    case = mark["case"]
    lst = open(os.path.join(cases, mark["list"], cname + ".d2s"), "rb").read()
    buf = open(os.path.join(cases, mark["swap"], cname + ".d2s"), "rb").read()
    diff = DIFF[mark["diff"]]
    tags = {}
    for _, t, d in ev:
        tags.setdefault(t, []).append(d)
    first = lambda t: tags.get(t, [None])[0]  # noqa: E731
    n0 = ck.n
    read = buf[:0x2000]  # PLRSAVE_ReadFile's fread cap (0x0053441F)
    rsv_code, hdr_code, cs_code = header_model(read, struct.unpack_from("<H", lst, 0x24)[0], diff, cname)
    rsv = first("RSV")
    pld = first("PLD")
    if rsv_code == 9:
        ck.eq(case + ": RSV code (D2S_ReadSave's length or magic test)", rsv and rsv["code"], 9)
        ck.eq(case + ": RSV bytes read", rsv and rsv["nread"], len(read))
        ck.eq(case + ": no RHDR (D2S_ReadHeader not reached)", "RHDR" in tags, False)
        ck.eq(case + ": PLD code", pld and pld["code"], 9)
        return ck.n - n0, "refused by D2S_ReadSave (9)"
    if rsv_code == "legacy":
        leg = first("LEG")
        ck.eq(case + ": LEG (the legacy reader) version", leg and leg["version"], struct.unpack_from("<I", buf, 4)[0])
        ck.eq(case + ": no RHDR", "RHDR" in tags, False)
        legr = first("LEGR")
        ck.eq(case + ": RSV code = LEGR code", rsv and rsv["code"], legr and legr["code"])
        ck.eq(case + ": PLD code = RSV code", pld and pld["code"], rsv and rsv["code"])
        return ck.n - n0, "legacy reader, code %s" % (legr and legr["code"])
    if case in HALTS:
        note = HALTS[case](ck, case, buf, tags, ev)
        return ck.n - n0, note
    rhdr = first("RHDR")
    ck.eq(case + ": RHDR bytes = the file's first 0x2000", rhdr and rhdr["sha256"], hashlib.sha256(read).hexdigest())
    ck.eq(case + ": RSV bytes read", rsv and rsv["nread"], len(read))
    if len(buf) != len(read):
        ck.eq(case + ": RHDR length (the 0x2000 cap)", rhdr and rhdr["len"], 0x2000)
    rhret = first("RHRET")
    ck.eq(case + ": RHRET code", rhret and rhret["code"], hdr_code)
    if cs_code is not None:
        rcst = first("RCST")
        ck.eq(case + ": RCST code (D2S_CheckStatus)", rcst and rcst["code"], cs_code)
        if rcst:
            ck.eq(case + ": RCST status word = the file's", rcst["status"], struct.unpack_from("<H", buf, 0x24)[0])
            ck.eq(case + ": RCST game expansion = the listed file's bit 5",
                  int(rcst["g70"] != 0), int(bool(struct.unpack_from("<H", lst, 0x24)[0] & 0x20)))
            ck.eq(case + ": RCST game difficulty", rcst["g6d"], diff)
    else:
        ck.eq(case + ": no RCST (the status test not reached)", "RCST" in tags, False)
    rerr = first("RERR")
    if hdr_code and not (hdr_code == 2 and len(read) == 0x14F):
        ck.eq(case + ": RERR internal", rerr and rerr["internal"], hdr_code)
        ck.eq(case + ": RERR mapped", rerr and rerr["mapped"], d2sio.LOAD_ERROR_MAP[hdr_code])
        ck.eq(case + ": PLD code = mapped", pld and pld["code"], d2sio.LOAD_ERROR_MAP[hdr_code])
        return ck.n - n0, "header code %d, mapped %d" % (hdr_code, d2sio.LOAD_ERROR_MAP[hdr_code])
    if hdr_code == 2:
        ck.eq(case + ": no RERR (the stub path)", rerr, None)
        ck.eq(case + ": PLD code", pld and pld["code"], 0)
        written = os.path.join(keep_dir, case, cname + ".d2s")
        note = ""
        if case in CASES and os.path.exists(written):
            note = "; " + CASES[case](ck, case, buf, open(written, "rb").read(), tags, {}, isc, kinds)
        return ck.n - n0, "stub: new character" + note
    # header passed: the case's own fields
    note = []
    if case == "wpbad":
        rwp = first("RWP")
        ck.eq(case + ": RWP code (marker 0x0303)", rwp and rwp["code"], 16)
        ck.eq(case + ": RERR internal", rerr and rerr["internal"], 16)
        ck.eq(case + ": RERR mapped", rerr and rerr["mapped"], d2sio.LOAD_ERROR_MAP[16])
        ck.eq(case + ": PLD", pld and pld["code"], d2sio.LOAD_ERROR_MAP[16])
        return ck.n - n0, "waypoint marker: 16, mapped 3"
    if case == "setbad":
        # the set item whose id has no SETITEMS record: ITEMS_ReadFull flags it (0x0062D1A3), sub_00558CB0 frees the
        # unit and stores the byte count (0x00558D2D, 0x00558D6C), the list goes on: the next item gets the freed
        # unit's address, the load does not fail, and the write that follows has no such item
        rix = tags.get("RIX", [])
        bad = [k for k, d in enumerate(rix) if d.get("q") == 5]
        ck.eq(case + ": one set item read", len(bad), 1)
        if bad:
            k = bad[0]
            ck.eq(case + ": the next item reuses the set item's unit (freed)", k + 1 < len(rix) and
                  rix[k + 1]["unit"] == rix[k]["unit"], True)
            ck.eq(case + ": the set item's byte count", rix[k]["nbytes"], 31)
        ck.eq(case + ": no RERR", rerr, None)
        ck.eq(case + ": PLD code", pld and pld["code"], 0)
        sb = [d for d in tags.get("SBIT", []) if d.get("final")]
        wd = tags.get("WDONE", [])
        if wd:
            n_items = len(sb) // len(wd)
            ck.eq(case + ": items in each write (14 read, the set item dropped)", n_items, 13)
            ck.eq(case + ": no set item written", [d for d in sb if d.get("q") == 5], [])
        return ck.n - n0, "set id 4000: the item dropped, the load goes on"
    ck.eq(case + ": PLD code", pld and pld["code"], 0)
    ck.eq(case + ": no RERR", rerr, None)
    written = os.path.join(keep_dir, case, cname + ".d2s")
    out = open(written, "rb").read() if os.path.exists(written) else None
    wdone = [d for d in tags.get("WDONE", [])]
    if mark["then"] == "savexit":
        ck.eq(case + ": the kept file is the case's last logged write", out is not None and wdone and
              hashlib.sha256(out).hexdigest() == wdone[-1]["sha256"], True)
    rsec = {}
    for d in tags.get("RSEC", []):
        rsec.setdefault(d["sec"], d["off"])
    fn = CASES.get(case)
    if fn:
        note.append(fn(ck, case, buf, out, tags, rsec, isc, kinds))
    return ck.n - n0, "loaded" + ("; " + "; ".join(n for n in note if n) if note else "")


def quest_model(rec):
    """0x0065C4D0 with its flag 1 (D2S_ReadQuests pushes 1, 0x0056A3B7): for each word 0..41 (bit index esi = 14 +
    16 w up to 0x2AE, 0x0065C50E-0x0065C54D) bits 13 and 14 cleared, then bit 15 set when bit 1 is set."""
    rec = bytearray(rec)
    for w in range(42):
        v = struct.unpack_from("<H", rec, 2 * w)[0] & ~0x6000
        if v & 2:
            v |= 0x8000
        struct.pack_into("<H", rec, 2 * w, v)
    return bytes(rec)


def wp_model(rec):
    """WAYPOINT_Load 0x00661030: a marker 0 or 0x0101 zeroes all 16 bytes (the 0x0102 stored at 0x00661086 is
    overwritten by the dword at 0x0066108B); then g_WaypointBits[0] (word 1, mask 1, 0x00746428) is ORed in."""
    rec = bytearray(rec)
    if struct.unpack_from("<H", rec, 0)[0] != 0x0102:
        rec[:] = bytes(16)
    struct.pack_into("<H", rec, 2, struct.unpack_from("<H", rec, 2)[0] | 1)
    return bytes(rec)


def case_fields(ck, case, buf, out, tags, rsec, isc, kinds):
    ract = tags.get("RACT", [None])[0]
    ck.eq(case + ": RACT file byte", ract and ract["file"], buf[0xA8])
    ck.eq(case + ": RACT act (5 or more read as 0)", ract and ract["act"], 0)
    rqw = tags.get("RQW", [None])[0]
    rwp = tags.get("RWP", [None])[0]
    for d in range(3):
        q = buf[d2s.QUEST_OFF + 10 + 0x60 * d:d2s.QUEST_OFF + 10 + 0x60 * (d + 1)]
        ck.eq(case + ": RQW record %d = the quest model" % d, rqw and rqw["recs"][d], quest_model(q).hex())
        o = d2s.WP_BLOCK0 + d * d2s.WP_BLOCK_SIZE
        ck.eq(case + ": RWP record %d = the waypoint model" % d, rwp and rwp["recs"][d], wp_model(buf[o:o + 16]).hex())
        if out:
            ck.eq(case + ": written quest block %d = RQW" % d,
                  out[d2s.QUEST_OFF + 10 + 0x60 * d:d2s.QUEST_OFF + 10 + 0x60 * (d + 1)].hex(), rqw and rqw["recs"][d])
            # WAYPOINT_Save (0x006610B0) stores the marker 0x0102 into a record whose marker is 0 or 0x0101
            # (0x006610EB), then copies the 16 bytes
            want = bytearray.fromhex(rwp["recs"][d]) if rwp else None
            if want is not None and struct.unpack_from("<H", want, 0)[0] in (0, 0x0101):
                struct.pack_into("<H", want, 0, 0x0102)
            ck.eq(case + ": written waypoint block %d = RWP, marker 0x0102" % d, out[o:o + 16].hex(),
                  want.hex() if want is not None else None)
    if out:
        gfx = tags.get("GFX", [])
        ck.eq(case + ": written 0x88..0xA7 = the writer's image (GFX)", out[0x88:0xA8].hex(),
              gfx[-1]["bytes"] if gfx else None)
        ck.eq(case + ": written graphics differ from the file's", out[0x88:0x98] != buf[0x88:0x98], True)
        ck.eq(case + ": written colours differ from the file's", out[0x98:0xA8] != buf[0x98:0xA8], True)
        ck.eq(case + ": written last_played != the file's", struct.unpack_from("<I", out, 0x30)[0] != 0x11111111, True)
        ck.eq(case + ": written unk_34", struct.unpack_from("<I", out, 0x34)[0], 0xFFFFFFFF)
        ck.eq(case + ": written 0xCF (read back from client +0x480)", out[0xCF], 0x5A)
        ck.eq(case + ": written unk_bf rest is 0", out[0xBF:0xCF] + out[0xD0:0x14F], bytes(0x14F - 0xBF - 1))
        ck.eq(case + ": written difficulty bytes (act 0, bit 7)", out[0xA8:0xAB].hex(), "800000")
    rhret = tags.get("RHRET", [None])[0]
    ck.eq(case + ": client +0x480..482 after the read", rhret and rhret["c480"], "5a0000")
    return "act %s, quests and waypoints as modelled" % (ract and ract["act"])


def case_skills29(ck, case, buf, out, tags, rsec, isc, kinds):
    rskc = tags.get("RSKC", [None])[0]
    ck.eq(case + ": RSKC count = header 0x2A", rskc and rskc["count"], buf[0x2A])
    ck.eq(case + ": item list cursor = skills cursor + 2 + 29", rsec.get("items", 0) - rsec.get("skills", 0), 2 + 29)
    if out:
        f = d2s.parse(out, isc, kinds)
        sk = list(buf[rsec["skills"] + 2:rsec["skills"] + 2 + 29]) + [0]
        ck.eq(case + ": written skills (30 bytes; the 29 read, then 0)", f["skills"], sk)
        ck.eq(case + ": written 0x2A", out[0x2A], 30)
        ck.eq(case + ": written name (the client's)", f["header"]["name"], "qitsor")
    return "29 skill bytes read"


def case_items(ck, case, buf, out, tags, rsec, isc, kinds):
    rix = [d for d in tags.get("RIX", [])]
    ear = [d for d in rix if d.get("flags", 0) & 0x10000]
    ck.eq(case + ": one ear read", len(ear), 1)
    if ear:
        ck.eq(case + ": ear class (item data +0x28)", ear[0]["fidx"], 3)
        ck.eq(case + ": ear level (item data +0x48)", ear[0]["b48"], 42)
        ck.eq(case + ": ear name (item data +0x4A)", ear[0]["name"], "earname")
    pers = [d for d in rix if d.get("flags", 0) & 0x1000000 and not d["flags"] & 0x10000]
    ck.eq(case + ": one personalized item read", len(pers), 1)
    if pers:
        ck.eq(case + ": personalized name (item data +0x4A)", pers[0]["name"], "Hoarder")
    realm = [d for d in rix if d.get("realm", [0, 0]) != [0, 0]]
    ck.eq(case + ": realm pair (item data +0x1C, +0x20)", [d["realm"] for d in realm], [[0x11223344, 0x55667788]])
    if out:
        # the written records, as a multiset (the writer puts the hand items last, in the unit list's order): each
        # read record again, the realm item's third u32 written as 0 (ITEMS_WriteFull and ITEMS_WriteCompact write
        # the pair and a 0, 0x0062B36E-0x0062B387)
        import h1a_saves
        f = d2s.parse(open(os.path.join(os.path.dirname(HERE), "workspace", "samples", "d2s", "qitsor.d2s"), "rb").read(),
                      isc, kinds)
        want = []
        for it in f["items"]["items"]:
            it = dict(it)
            it["flags"] &= ~0x2000  # bit 13 is cleared on every item read from a save (0x00558D46-0x00558D4C)
            if it.get("code", "").strip() == "cap":
                it["flags"] |= 1 << 24
                it["pname"] = "Hoarder"
            elif it.get("code", "").strip() == "lgl":
                it["realm"] = h1a_saves.Realm(0x11223344, 0x55667788, 0)
            want.append(h1a_saves.encode(it, isc, kinds))
        want.append(h1a_saves.encode_ear(dict(flags=(1 << 4) | (1 << 16) | (1 << 21) | (1 << 23), version=101,
                                              location=0, body=0, x=0, y=0, store=1, ear_class=3, ear_level=42,
                                              ear_name="earname")))
        lo = d2s.parse_stats(out, d2s.HEADER_SIZE, isc)[1] + 32
        cnt = struct.unpack_from("<H", out, lo + 2)[0]
        got = []
        body = out[lo + 4:]
        rest = list(want)
        k = 0
        while rest and k < len(body):
            hit = next((r for r in rest if body.startswith(r, k)), None)
            if hit is None:
                break
            got.append(hit)
            rest.remove(hit)
            k += len(hit)
        ck.eq(case + ": written item count", cnt, len(want))
        ck.eq(case + ": written records = the read ones (realm third u32 0), none left over", len(rest), 0)
        ck.eq(case + ": the written list ends at the corpse list", body[k:k + 4], b"JM\x00\x00")
        return "%d written records matched" % len(got)
    return ""


def case_uniqbad(ck, case, buf, out, tags, rsec, isc, kinds):
    rix = [d for d in tags.get("RIX", []) if d.get("q") == 7]
    ck.eq(case + ": a unique read with file index -1 (id 4000 >= the unique count)",
          sorted(d["fidx"] for d in rix)[0] if rix else None, -1)
    if out:
        f = d2s.parse(out, isc, kinds)
        ck.eq(case + ": the -1 written as 0xFFF (12 bits)", sorted(it["qid"] for it in f["items"]["items"]
                                                                if it.get("quality") == 7), [71, 0xFFF])
    return "unique ids read: %s" % [d["fidx"] for d in rix]


def case_v94(ck, case, buf, out, tags, rsec, isc, kinds):
    rstv = tags.get("RSTV", [None])[0]
    ck.eq(case + ": RSTV version", rstv and rstv["version"], 94)
    ck.eq(case + ": RSTV count (header 0x29)", rstv and rstv["count"], buf[0x29])
    p = rsec["stats"]
    n = buf[0x29]
    mask = int.from_bytes(buf[p + 2:p + 2 + (n + 7) // 8], "little")
    vals, k = {}, 0
    for i in range(n):
        if mask >> i & 1:
            vals[i] = struct.unpack_from("<I", buf, p + 4 + 4 * k)[0]
            k += 1
    rstl = [(d["id"], d["value"] & 0xFFFFFFFF, d["param"]) for d in tags.get("RSTL", [])]
    ck.eq(case + ": RSTL = one SetStat per stat 0..count-1, the u32 or 0", rstl, [(i, vals.get(i, 0), 0) for i in range(n)])
    ck.eq(case + ": skills cursor = stats cursor + 2 + bitmask bytes + 4 x bits", rsec.get("skills", 0) - p,
          2 + (n + 7) // 8 + 4 * k)
    if out:
        f = d2s.parse(out, isc, kinds)
        ck.eq(case + ": written version", f["header"]["version"], 96)
        ws = {i: v for i, _, v in f["stats"]}
        ck.eq(case + ": written stats 0..count-1 = the old form's non-zero values", {i: v for i, v in ws.items() if i < n},
              {i: v for i, v in vals.items() if v})
        if n < 16:
            ck.eq(case + ": stat 12 (level) not read with count 12: absent from the write, header level 0",
                  (ws.get(12), f["header"]["level"]), (None, 0))
        durs = sorted((it["code"], it.get("dur")) for it in f["items"]["items"] if "dur" in it)
        base = d2s.parse(open(os.path.join(os.path.dirname(HERE), "workspace", "samples", "d2s", "qitsor.d2s"), "rb")
                         .read(), isc, kinds)
        ck.eq(case + ": written current durabilities = the 8-bit values built (read with 8 bits, version <= 95)",
              durs, sorted((it["code"], it.get("dur")) for it in base["items"]["items"] if "dur" in it))
        ck.eq(case + ": written item count", len(f["items"]["items"]), len(base["items"]["items"]))
        return "written durabilities %s" % durs
    return ""


def case_param(ck, case, buf, out, tags, rsec, isc, kinds):
    # RIST (d2s-h1b.py) logs each loaded item's full stat array (its property lists folded in); only the staff holds
    # stat 107 in this save
    got = sorted({tuple(e) for d in tags.get("RIST", []) for e in (d.get("full") or []) if e[0] == 107})
    ck.eq(case + ": the staff's stat 107 entry read (id, param, value)", got, [(107, 270, 1)])
    if out:
        f = d2s.parse(out, isc, kinds)
        props = [it["props"] for it in f["items"]["items"] if it.get("code", "").strip() == "sst"]
        ck.eq(case + ": written staff properties", props, [[(107, 270, [1])]])
    return "param 270 read unsigned"


def case_slots8(ck, case, buf, out, tags, rsec, isc, kinds):
    rstv = tags.get("RSTV", [None])[0]
    ck.eq(case + ": RSTV version / count", rstv and (rstv["version"], rstv["count"]), (96, 8))
    ck.eq(case + ": no old-form SetStat (RSTL)", "RSTL" in tags, False)
    ck.eq(case + ": RSTAT ids read = the file's gf list (all of them, not 8)",
          [d["id"] for d in tags.get("RSTAT", [])], [i for i, _, _ in d2s.parse(buf, isc, kinds)["stats"]])
    if out:
        ck.eq(case + ": written 0x29", out[0x29], 16)
    return "0x29 = 8 had no effect on the version-96 stats"


def case_act6(ck, case, buf, out, tags, rsec, isc, kinds):
    ract = tags.get("RACT", [None])[0]
    ck.eq(case + ": RACT file byte", ract and ract["file"], 0x86)
    ck.eq(case + ": RACT act (6 read as 0; a modulo 5 would give 1)", ract and ract["act"], 0)
    if out:
        ck.eq(case + ": written difficulty bytes", out[0xA8:0xAB].hex(), "800000")
    return "act 6 read as 0"


def case_mercmf(ck, case, buf, out, tags, rsec, isc, kinds):
    f = d2s.parse(buf, isc, kinds)
    n = len(f.get("merc_items", {}).get("items", []))
    ck.eq(case + ": the file has mercenary items", n > 0, True)
    mrx = tags.get("MRX", [None])[0]
    ck.eq(case + ": D2S_ReadMercHeader made a mercenary (MRX eax)", bool(mrx and mrx.get("eax")), True)
    ck.eq(case + ": the mercenary item list cursor = the file's jf + 2", rsec.get("merc_items"),
          f["corpses_end"])
    if out:
        g = d2s.parse(out, isc, kinds)
        key = lambda it: (it["code"], it.get("seed"), it.get("quality"), it["body"])  # noqa: E731
        ck.eq(case + ": written mercenary items = the file's (code, seed, quality, body)",
              sorted(map(key, g.get("merc_items", {}).get("items", []))),
              sorted(map(key, f.get("merc_items", {}).get("items", []))))
    return "%d mercenary items in the file" % n


def halt_class7(ck, case, buf, tags, ev):
    """A class-7 file passes D2S_ReadHeader's class test (0x0056A172: unsigned > 7); the player unit is not created
    and sub_00553180 halts with line 1210 (0x4BA: a null unit, 0x00553187) from 0x00569F20 (the crash report,
    workspace/logs/h1a/class7-crash/Crash.txt): the logged lines stop after the map-seed step and the process ends."""
    rcst = (tags.get("RCST") or [None])[0]
    rmap = (tags.get("RMAP") or [None])[0]
    ck.eq(case + ": RCST code", rcst and rcst["code"], 0)
    ck.eq(case + ": the client class after the class test (RMAP cls)", rmap and rmap["cls"], 7)
    ck.eq(case + ": RHDR = the file", (tags.get("RHDR") or [{}])[0].get("sha256"), hashlib.sha256(buf).hexdigest())
    ck.eq(case + ": no RHRET, no PLD (the read never returned)", ("RHRET" in tags, "PLD" in tags), (False, False))
    return "class 7 passed the class test; the load halted (no player unit)"


def exp_rows(excel):
    """experience.txt as {Level: [the 7 class columns, ExpRatio]} (MaxLvl skipped)."""
    rows = [l.rstrip("\r").split("\t") for l in open(os.path.join(excel, "experience.txt"), encoding="latin1")
            if l.strip()]
    return {int(r[0]): [int(x) for x in r[1:9]] for r in rows[1:] if r[0].isdigit()}


EXCEL = [None]


def case_class7(ck, case, buf, out, tags, rsec, isc, kinds):
    rhret = tags.get("RHRET", [None])[0]
    ck.eq(case + ": class 7 passes the header (client class)", rhret and rhret.get("cls"), 7)
    lfx0, lfx = tags.get("LFX0", [None])[0], tags.get("LFX", [None])[0]
    ck.eq(case + ": EXP_GetThreshold called with class 7", lfx0 and lfx0["cls"], 7)
    if lfx0 and lfx:
        row = exp_rows(EXCEL[0])[lfx0["level"]]
        ck.eq(case + ": its result = column 0 of row Level (class >= 7 read as 0, 0x00611808-0x0061180F)",
              lfx["exp"], row[0])
        ck.eq(case + ": not the unclamped dword (row Level's ExpRatio)", lfx["exp"] != row[7], True)
    if out:
        ck.eq(case + ": written class", out[0x28], 7)
    return "class 7 loaded; threshold %s" % (lfx and lfx["exp"])


def case_stub7(ck, case, buf, out, tags, rsec, isc, kinds):
    if out:
        f = d2s.parse(out, isc, kinds)
        st = {i: v for i, _, v in f["stats"]}
        ck.eq(case + ": written class", f["header"]["cls"], 7)
        ck.eq(case + ": no attributes (stats 0-3)", [st.get(i, 0) for i in range(4)], [0, 0, 0, 0])
        ck.eq(case + ": no items", len(f["items"]["items"]), 0)
        ck.eq(case + ": no skill", [x for x in f["skills"] if x], [])
        return "class-7 new character: stats %s" % sorted(st.items())
    return ""


def halt_stub7(ck, case, buf, tags, ev):
    """A class-7 stub passes the header (2, the stub path), and sub_00569F80_NewCharFromStub halts the same way:
    line 1210 from 0x00569FB8 (workspace/logs/h1a/stub7-crash/Crash.txt)."""
    rhret = (tags.get("RHRET") or [None])[0]
    ck.eq(case + ": RCST code", (tags.get("RCST") or [{}])[0].get("code"), 0)
    ck.eq(case + ": RHRET code 2 (the stub path)", rhret and rhret["code"], 2)
    ck.eq(case + ": no RERR, no PLD (NewCharFromStub never returned)", ("RERR" in tags, "PLD" in tags), (False, False))
    return "class-7 stub: the header passed; the new character halted (no player unit)"


def case_name15(ck, case, buf, out, tags, rsec, isc, kinds):
    ck.eq(case + ": the file's byte 0x23 (the 16th name byte) is not 0", buf[0x23] != 0, True)
    rhret = tags.get("RHRET", [None])[0]
    ck.eq(case + ": the load passed with the 15-character client name", rhret and rhret.get("name"), "qitsorfifteenzz")
    if out:
        ck.eq(case + ": written name field (15 characters, then 0)", out[0x14:0x24], b"qitsorfifteenzz\0")
    return "byte 0x23 'Z' forced to 0 before the name test"


HALTS = {"class7": halt_class7, "stub7": halt_stub7}

CASES = {"name15": case_name15, "class7": case_class7, "stub7": case_stub7, "param": case_param, "slots8": case_slots8, "v94s12": case_v94, "act6": case_act6, "mercmf": case_mercmf, "fields": case_fields, "skills29": case_skills29, "items": case_items, "uniqbad": case_uniqbad,
         "v94": case_v94}


def main(argv):
    if len(argv) < 4 or argv[0] != "check":
        print(__doc__)
        return 2
    excel, cases, logs = argv[1], argv[2], argv[3:]
    EXCEL[0] = excel
    isc, kinds = d2s.load_isc(excel), d2s.load_kinds(excel)
    ck = Ck()
    d2sio_bad = 0
    for log in logs:
        print("=== %s" % log)
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "d2sio.py"), "check", excel, log],
                           capture_output=True, text=True)
        tail = [ln for ln in r.stdout.splitlines() if ln.startswith("TOTAL") or "MISMATCH" in ln or
                ln.startswith("READ") or ln.startswith("WRITE") or "UNPARSED" in ln]
        for ln in tail:
            print("  d2sio: " + ln)
        if r.returncode:
            d2sio_bad += 1
        marks_path = log[:-4] + ".marks.jsonl"
        marks = [json.loads(ln) for ln in open(marks_path)]
        ev = events(log)
        for j, m in enumerate(marks):
            end = marks[j + 1]["line"] if j + 1 < len(marks) else 1 << 60
            seg = [e for e in ev if m["line"] <= e[0] < end]
            name = next((fn[:-4] for fn in os.listdir(os.path.join(cases, m["swap"])) if fn.endswith(".d2s")), None)
            n, note = check_case(ck, m, seg, cases, name, isc, kinds, log[:-4] + "-saves")
            print("CASE %-10s list=%-8s swap=%-9s diff=%-9s %3d comparisons: %s" % (
                m["case"], m["list"], m["swap"], m["diff"], n, note))
    print("TOTAL H1A %d comparisons, %d failing; d2sio logs failing %d" % (ck.n, ck.bad, d2sio_bad))
    return 0 if ck.bad == 0 and d2sio_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
