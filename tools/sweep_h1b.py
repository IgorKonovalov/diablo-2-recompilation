#!/usr/bin/env python3
"""Checker for plan 0038 batch H1b (run:2026-10-27-sweep-d2s-play): the logs of tools/gdb/d2s-h1b.gdb and
d2s-h1b-hire.gdb (tools/gdb/d2s-io.py + tools/gdb/d2s-h1b.py) against the saves the game wrote and read in them.

    python3 -I tools/sweep_h1b.py check <excel-dir> <log> [<log> ...]

For each log: first tools/d2sio.py's own check (every header field, gf stream and item common part of every write,
every load), then the H1b groups, one "H1B <group> ..." line each with its counts and "MISMATCH" lines:
  who      PLRSAVE_Save's branch per call (PSV2 then SAVE = file, SVCL = client buffer, SVCB = host callback) against
           the one the code reads (game type 1/2 -> SVCL; else host callback 0 -> file; else SVCB); the callers'
           return addresses; AutosaveTick calls (AUTO) and whether any save returned into it; SaveAllOnShutdown
           entries (SHUT) and the saves after them
  join     the load chain (JCH) before every D2S_ReadHeader (RHDR): the functions and return addresses
  wsec     D2S_WriteSave's section offsets (WSEC final pass) against the sections of the buffer written (tools/d2s.py
           parse); the scratch pass's section sizes against the final pass's
  rsec     D2S_ReadSaveV92's section offsets (RSEC) against the sections of the buffer read, and the call order
  hotkeys  the 16 header hotkey words (0x38 + 4 i) against the client's slots (HOTK: skill | 0x8000 if the slot flag,
           0xFFFF for an empty slot) and the item refs the writer stored (HREF)
  gfx      header bytes 0x88..0xA7 against the image after 0x0063E510 (GFX)
  merc     header 0xAF..0xBE of every write against D2S_WriteMercHeader's sources (MHW1: seed = info +0x00,
           name = info +0x04 - record +0x114, id = info +0x08, experience = merc stat 13; MHWD: bit 16 = dead test)
           and its image (MHW2); a write without MHW1 against 16 zero bytes; every read's MRX against the bytes read;
           0x005726C0(1) (M5726) exactly when MRX returned a mercenary
  lfin     D2S_LoadFinish: gold/goldbank kept or 0 against the logged maximum (LFG/LFB), stamina = LFS, stats 6/8 =
           the values read before the items (LFIN args), 67/68/69 = 100, stat 30 = LFX = experience.txt (class column)
           at row L, the current level (the experience at which level L + 1 starts); row L + 1 reported beside it
  items    per loaded item (RIST, in file order): the property stats with ValShift (maxhp 7, maxmana 9) = file value
           << ValShift; stat 326 = 1 after a group-57 property; group 52 values; the weapon damage and speed stats
           (21-24, 159, 160, 67, 68) and the shield block (20) the reader rebuilt, against weapons.txt / armor.txt;
           per written item (SBX, final pass): stat >> ValShift = file value for 7 and 9; stat 356 = file quest_diff
           (the property checks use the full stat array, logged from the second logger revision on)
  rw       runeword: RWR (the 16 bits read) = file field = RIST item data +0x38; RWW (Runes record +0x82) = file field
  bit13    B13S / B13C / SETF / WTCH / COPY / GOLD lines: every clear of a dropped item's bit 13 (B13C) inside the
           game tick's ActUnitsFrameReset call (in_tick 1, ret 0x0053B049) with the item on the ground (mode 3);
           every watchpoint write to the watched flags from ITEMS_SetFlag (pc 0x006280F2 / 0x006280FE: after its or /
           and) or reported; the watched item's later saved flags
  corpse   corpses per write (count, items, their modes) and per read
Exits 0 only when nothing mismatched. Stdlib only.
"""
import contextlib
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import d2s  # noqa: E402
import d2sio  # noqa: E402

SETF_PCS = (0x006280F2, 0x006280FE)   # the instruction after ITEMS_SetFlag's `or [eax+0x18]` / `and [eax+0x18]`


class Ck:
    def __init__(self):
        self.n = self.bad = 0

    def eq(self, what, got, want):
        self.n += 1
        if got != want:
            self.bad += 1
            print("  MISMATCH %s: got %r, want %r" % (what, got, want))


def table(excel, name):
    text = open(os.path.join(excel, name), encoding="latin1").read()
    rows = [l.rstrip("\r").split("\t") for l in text.split("\n") if l.strip("\r")]
    hd = rows[0]
    return [dict(zip(hd, r + [""] * (len(hd) - len(r)))) for r in rows[1:]]


def ival(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        return 0


def sections(f, buf):
    """Section start offsets of a parsed save, in writer order."""
    out = {"header": 0, "quests": d2s.QUEST_OFF, "waypoints": d2s.WP_OFF, "npcs": d2s.NPC_OFF,
           "stats": d2s.HEADER_SIZE, "skills": f["skills_end"] - 32, "items": f["skills_end"],
           "corpses": f["items_end"], "merc": f["corpses_end"], "end": len(buf)}
    if "kf_off" in f:
        out["golem"] = f["kf_off"]
    return out


def check_log(excel, log, T):
    ck = Ck()
    ev = d2sio.events(log)
    isc, kinds, vshift, exp_rows, weapons, armor, codes = T
    name = os.path.basename(log)
    # --- who
    rets, branches, nauto = {}, {}, 0
    auto_ret = set()
    for k, (t, d) in enumerate(ev):
        if t == "AUTO":
            nauto = max(nauto, d["calls"])
            auto_ret.add(d["ret"])
        if t == "PSV2":
            rets[d["ret"]] = rets.get(d["ret"], 0) + 1
            want = "SVCL" if d["gtype"] in (1, 2) else ("SAVE" if d["hostcb"] == 0 else "SVCB")
            nxt = next((t2 for t2, _ in ev[k + 1:] if t2 in ("SAVE", "SVCL", "SVCB")), None)
            ck.eq("%s PLRSAVE_Save branch (game type %d, host callback %d)" % (name, d["gtype"], d["hostcb"]), nxt, want)
            branches[want] = branches.get(want, 0) + 1
    shut = [(k, d) for k, (t, d) in enumerate(ev) if t == "SHUT"]
    after_shut = sum(1 for k, _ in shut for t2, d2 in ev[k + 1:] if t2 == "PSV2" and d2["ret"] == 0x0052EA3D)
    print("H1B who %s: PLRSAVE_Save callers %s; branches %s; AutosaveTick calls %d (host callback %s), saves from "
          "it %d; SaveAllOnShutdown entries %d (ret %s), its saves %d" % (
              name, {"%08X" % r: n for r, n in sorted(rets.items())}, branches, nauto,
              sorted({d["hostcb"] for t, d in ev if t == "AUTO"}), rets.get(0x0052D3BA, 0) + rets.get(0x0052D3BF, 0),
              len(shut), sorted({"%08X" % d["ret"] for _, d in shut}), after_shut))
    # --- join chain
    rh = [k for k, (t, _) in enumerate(ev) if t == "RHDR"]
    chains = []
    for k in rh:
        ch, j = [], k - 1
        while j >= 0 and ev[j][0] in ("JCH", "RSEC", "RBASE"):
            if ev[j][0] == "JCH":
                ch.append("%s<-%08X" % (ev[j][1]["fn"], ev[j][1]["ret"]))
            j -= 1
        chains.append(" ".join(reversed(ch)))
    print("H1B join %s: %d loads; chains %s" % (name, len(rh), sorted(set(chains))))
    # --- writes: wsec, hotkeys, gfx, merc, items written, corpses
    cur = None
    nw = 0
    for t, d in ev:
        if t == "SAVE":
            cur = {"wsec": [], "hotk": None, "href": [], "gfx": None, "mhw1": None, "mhwd": None, "mhw2": None,
                   "sbx": [], "sbit": [], "whdr": None, "rww": []}
        elif cur is None:
            continue
        elif t == "WSEC":
            cur["wsec"].append(d)
        elif t == "HOTK":
            cur["hotk"] = d
        elif t == "HREF":
            cur["href"].append(d)
        elif t in ("GFX", "MHW1", "MHWD", "MHW2", "WHDR"):
            cur[t.lower()] = d
        elif t == "SBX":
            cur["sbx"].append(d)
        elif t == "SBIT":
            cur["sbit"].append(d)
        elif t == "RWW":
            cur["rww"].append(d)
        elif t == "WSKL":
            cur.setdefault("wskl", {})[d["slot"]] = d["skill"]
        elif t == "WDONE":
            nw += 1
            buf = bytes.fromhex(d["hex"])
            f = d2s.parse(buf, isc, kinds)
            tag = "%s write %d" % (name, nw)
            sec = sections(f, buf)
            fin = {w["sec"]: w["off"] for w in cur["wsec"] if w["pass"] in ("pre", "final")}
            for s, off in fin.items():
                ck.eq(tag + " section %s offset" % s, off, sec.get(s))
            scr = [w for w in cur["wsec"] if w["pass"] == "scratch"]
            fl = [w for w in cur["wsec"] if w["pass"] == "final"]
            ck.eq(tag + " scratch pass section sizes = final", [b["off"] - a["off"] for a, b in zip(scr, scr[1:])],
                  [b["off"] - a["off"] for a, b in zip(fl, fl[1:len(scr)])])
            hk = [struct.unpack_from("<HH", buf, 0x38 + 4 * i) for i in range(16)]
            if cur["hotk"]:
                for i, (sk, fl_, _) in enumerate(cur["hotk"]["slots"]):
                    want = 0xFFFF if sk < 0 else (sk | (0x8000 if fl_ else 0))
                    ck.eq(tag + " hotkey %d skill word" % i, hk[i][0], want)
                refs = {h["slot"]: h["ref"] for h in cur["href"]}
                for i in range(16):
                    if i in refs:
                        ck.eq(tag + " hotkey %d item ref" % i, hk[i][1], refs[i])
            ws = cur.get("wskl") or {}
            for slot, o in (("left", 0x78), ("right", 0x7C), ("swapA", 0x80), ("swapB", 0x84)):
                if slot in ws:
                    ck.eq(tag + " mouse %s skill = the writer's source" % slot, struct.unpack_from("<H", buf, o)[0],
                          ws[slot])
            if ws:
                print("H1B mouse %s: weapon set %d; sources %s; pd %s" % (
                    tag, cur["whdr"]["wsw"], ws, cur["whdr"].get("pd")))
            if cur["gfx"]:
                ck.eq(tag + " graphics/colour bytes 0x88..0xA7", buf[0x88:0xA8].hex(), cur["gfx"]["bytes"])
            mh = buf[0xAF:0xBF]
            if cur["mhw1"]:
                info = bytes.fromhex(cur["mhw1"]["info"])
                ck.eq(tag + " merc flags 0xAF", struct.unpack_from("<I", mh, 0)[0],
                      0x10000 if cur["mhwd"]["dead"] else 0)
                ck.eq(tag + " merc seed 0xB3 = info +0x00", mh[4:8], info[0:4])
                ck.eq(tag + " merc name 0xB7 = info +0x04 - rec +0x114", struct.unpack_from("<H", mh, 8)[0],
                      (struct.unpack_from("<H", info, 4)[0] - cur["mhw1"]["r114"]) & 0xFFFF)
                ck.eq(tag + " hireling id 0xB9 = info +0x08", mh[10:12], info[8:10])
                ck.eq(tag + " merc experience 0xBB = merc stat 13", struct.unpack_from("<I", mh, 12)[0],
                      cur["mhw1"]["s13"])
                ck.eq(tag + " merc header = D2S_WriteMercHeader's image", mh.hex(), cur["mhw2"]["hdr"])
                print("H1B merc %s: dead test %d, merc mode %d, class %d, header %s" % (
                    tag, cur["mhwd"]["dead"], cur["mhwd"]["mode"], cur["mhw1"]["mcls"], mh.hex()))
            else:
                ck.eq(tag + " no mercenary: header 0xAF..0xBE zero", mh, bytes(16))
            # items written: maxhp/maxmana shift, quest stat 356
            items = {it["off"]: it for it in d2s.all_items(f)}
            sb = [s for s in cur["sbit"] if s["final"]]
            sx = [s for s in cur["sbx"]]
            # SBX lines follow the SBIT lines one for one (same breakpoint address); keep the final-pass ones
            pairs = [(a, b) for a, b in zip(cur["sbit"], sx) if a["final"] and a["unit"] == b["unit"]]
            ck.eq(tag + " SBX lines pair with the final SBIT lines", len(pairs), len(sb))
            for s, x in pairs:
                it = items.get(s["off"])
                if it is None:
                    continue
                if "full" not in x:      # an earlier logger revision: the property stats were not logged
                    continue
                st = {(i, p): v for i, p, v in (x.get("full") or [])}
                for sid in (7, 9):
                    for p in it.get("props") or []:
                        if p[0] == sid and (sid, 0) in st:
                            ck.eq(tag + " item %s stat %d >> ValShift %d = file" % (s.get("code"), sid, vshift[sid]),
                                  st[(sid, 0)] >> vshift[sid], p[2][0])
                            cur.setdefault("vs", 0)
                            cur["vs"] += 1
                if "quest_diff" in it:
                    ck.eq(tag + " item %s stat 356 = file quest_diff" % s.get("code"), st.get((356, 0), 0),
                          it["quest_diff"])
                    print("H1B quest %s: %s stat 356 %d" % (tag, s.get("code"), it["quest_diff"]))
                if it.get("runeword"):
                    rwv = it["rw"][0] | it["rw"][1] << 12
                    for r in cur["rww"]:
                        ck.eq(tag + " runeword field = Runes +0x82", rwv, r["r82"])
                    print("H1B rw %s: %s field %d, RWW %s" % (tag, s.get("code"), rwv, [r["r82"] for r in cur["rww"]]))
            if f["corpses"]:
                print("H1B corpse %s: %d corpse(s), items %s, unk %s" % (
                    tag, len(f["corpses"]), [(i.get("code"), i["location"], i["body"]) for c in f["corpses"]
                                             for i in c["items"]["items"]], [c["unk"].hex() for c in f["corpses"]]))
            status = cur["whdr"]["status"] if cur["whdr"] else None
            print("H1B write %s: sections %s; status word 0x%04X; vshift items %d" % (
                tag, {s: fin.get(s) for s in sec}, status or 0, cur.get("vs", 0)))
            cur = None
    # --- reads
    for j, k in enumerate(rh):
        end = rh[j + 1] if j + 1 < len(rh) else len(ev)
        seg = ev[k:end]
        buf = bytes.fromhex(ev[k][1]["hex"])
        tag = "%s read %d" % (name, j + 1)
        rhret = next((d for t, d in seg if t == "RHRET"), None)
        if not rhret or rhret["code"] != 0:
            continue
        f = d2s.parse(buf, isc, kinds)
        sec = sections(f, buf)
        # the header call (0x0056B1BB) is logged just before D2S_ReadHeader's RHDR line, so it closes the previous
        # segment: take it from there
        pre = ev[k - 1] if k and ev[k - 1][0] == "RSEC" else None
        rs = ([(pre[1]["sec"], pre[1]["off"])] if pre else []) + [(d["sec"], d["off"]) for t, d in seg
                                                                    if t == "RSEC" and d["sec"] != "header"]
        order = [s for s, _ in rs]
        ck.eq(tag + " reader call order", order,
              ["header", "quests", "waypoints", "npcs", "stats", "skills", "items", "corpses", "merc_header",
               "merc_items"] + (["merc_5726c0"] if "merc_5726c0" in order else []) + ["golem", "loadfinish"])
        want = dict(sec, merc_header=sec["merc"], merc_items=sec["merc"], merc_5726c0=sec.get("golem"),
                    loadfinish=sec["end"])
        for s, off in rs:
            ck.eq(tag + " reader section %s offset" % s, off, want.get(s))
        # mouse words read (D2S_ReadHeader -> player data, logged at RHRET): left 0x078 -> +0x74/+0x7C, right 0x07C ->
        # +0x70/+0x78, swap A 0x080 -> +0x84/+0x8C, swap B 0x084 -> +0x80/+0x88
        pd = rhret.get("pd")
        if pd:
            for o, i in ((0x78, 1), (0x7C, 0), (0x80, 5), (0x84, 4)):
                ck.eq(tag + " mouse word 0x%03X skill -> player data +0x%02X" % (o, 0x70 + 4 * i), pd[i] & 0xFFFF,
                      struct.unpack_from("<H", buf, o)[0])
            print("H1B mouseread %s: weapon set %d, file %s, pd %s" % (
                tag, buf[0x10] & 1, [struct.unpack_from("<H", buf, o)[0] for o in (0x78, 0x7C, 0x80, 0x84)], pd))
        mrx = next((d for t, d in seg if t == "MRX"), None)
        m5 = [d for t, d in seg if t == "M5726"]
        if mrx:
            ck.eq(tag + " MRX header bytes = file 0xAF..0xBE", mrx["hdr"], buf[0xAF:0xBF].hex())
            ck.eq(tag + " 0x005726C0 called iff a mercenary was made", len(m5), 1 if mrx["eax"] else 0)
            for m in m5:
                ck.eq(tag + " 0x005726C0 argument", m["arg"], 1)
            print("H1B mercread %s: header %s -> merc %s; 0x005726C0 calls %d" % (
                tag, mrx["hdr"], "yes" if mrx["eax"] else "none", len(m5)))
        # LoadFinish
        fs = {i: v for i, p, v in f["stats"]}
        lfg = next((d for t, d in seg if t == "LFG"), None)
        lfb = next((d for t, d in seg if t == "LFB"), None)
        lfs = next((d for t, d in seg if t == "LFS"), None)
        lfx0 = next((d for t, d in seg if t == "LFX0"), None)
        lfx = next((d for t, d in seg if t == "LFX"), None)
        lfe = next((d for t, d in seg if t == "LFE"), None)
        lfin = next((d for t, d in seg if t == "LFIN"), None)
        if lfe and lfg and lfb and lfs and lfx and lfin:
            e = {i: v for i, p, v in lfe["stats"] if p == 0}
            for sid, d_, k_ in ((14, lfg, "gold"), (15, lfb, "bank")):
                v = d_[k_]
                vs = v - (1 << 32) if v & 0x80000000 else v
                ck.eq(tag + " stat %d read = file" % sid, v, fs.get(sid, 0))
                ck.eq(tag + " stat %d after LoadFinish (max %d)" % (sid, d_["max"]), e.get(sid, 0),
                      0 if vs < 0 or vs > d_["max"] else vs)
            ck.eq(tag + " stat 10 = stamina maximum", e.get(10), lfs["max"])
            ck.eq(tag + " stat 6 = value read before the items", e.get(6), lfin["arg6"])
            ck.eq(tag + " stat 8 = value read before the items", e.get(8), lfin["arg8"])
            for sid in (67, 68, 69):
                ck.eq(tag + " stat %d = 100" % sid, e.get(sid), 100)
            ck.eq(tag + " stat 30 = 0x00611800's result (absent = 0)", e.get(30, 0), lfx["exp"])
            lvl, cls = lfx0["level"], lfx0["cls"]
            ck.eq(tag + " level passed = stat 12", lvl, e.get(12))
            col = list(exp_rows[0].keys())[1 + cls]
            row = next(r for r in exp_rows if r["Level"] == str(lvl))
            nrow = next((r for r in exp_rows if r["Level"] == str(lvl + 1)), {})
            ck.eq(tag + " stat 30 = experience.txt row %d (%s; the threshold of level %d)" % (lvl, col, lvl + 1), lfx["exp"], ival(row[col]))
            print("H1B lfin %s: gold %d (max %d) -> %d; bank %d (max %d) -> %d; stamina %s; stat 30 %s = row %d "
                  "(%s), row %d is %s; experience %s" % (
                      tag, lfg["gold"], lfg["max"], e.get(14, 0), lfb["bank"], lfb["max"], e.get(15, 0), e.get(10),
                      e.get(30), lvl, row[col], lvl + 1, nrow.get(col), e.get(13)))
        # items read
        # the items of this load: the RIST lines before D2S_LoadFinish's exit (LFE); later ones are item copies
        # (sub_0055A2A0_ItemCopy recreates through the same function, e.g. the corpse's items at a death)
        kl = next((n for n, (t, _) in enumerate(seg) if t == "LFE"), len(seg))
        ri = [d for t, d in seg[:kl] if t == "RIST"]
        rw = [d for t, d in seg if t == "RWR"]
        fi = list(d2s.all_items(f))
        ck.eq(tag + " RIST count", len(ri), len(fi))
        nrw = 0
        for r, it in zip(ri, fi):
            itag = "%s item %s@0x%X" % (tag, it.get("code"), it["off"])
            st = {(i, p): v for i, p, v in (r["stats"] or [])}
            fu = {(i, p): v for i, p, v in (r.get("full") or [])}
            has_full = "full" in r     # logged from the logger revision with h1b_full only
            lists = [it.get("props") or []] + list(it.get("set_props") or []) + [it.get("rw_props") or []]
            mainp = it.get("props") or []
            for p in mainp:
                sid = p[0]
                if not has_full:
                    continue
                if sid in (7, 9):
                    ck.eq(itag + " stat %d = file << ValShift %d" % (sid, vshift[sid]), fu.get((sid, 0)),
                          p[2][0] << vshift[sid])
                    print("H1B vshift %s: stat %d file %d, runtime %s" % (itag, sid, p[2][0], fu.get((sid, 0))))
                if sid == 57:
                    ck.eq(itag + " stat 326 = 1 after group 57", fu.get((326, 0)), 1)
                    print("H1B poison %s: 57/58/59 = %s, 326 = %s" % (itag, p[2], fu.get((326, 0))))
                if sid == 52:
                    ck.eq(itag + " group 52 stats 52/53 = file", [fu.get((52, 0)), fu.get((53, 0))], p[2])
                    print("H1B magdmg %s: 52/53 = %s" % (itag, p[2]))
            if it.get("simple"):
                continue
            code = it.get("code", "").strip()
            w = weapons.get(code)
            if w:
                q = it["quality"]
                eth = it.get("ethereal")

                def adj(v):
                    v = v * 3 // 4 if q == 1 else v
                    return v * 3 // 2 if eth else v
                for sid, colw in ((21, "mindam"), (22, "maxdam"), (23, "2handmindam"), (24, "2handmaxdam"),
                                  (159, "minmisdam"), (160, "maxmisdam")):
                    if ival(w.get(colw)):
                        base = st.get((sid, 0))
                        ck.eq(itag + " rebuilt stat %d = weapons.%s" % (sid, colw), base, adj(ival(w[colw])))
                sp = ival(w.get("speed"))
                if sp:
                    ck.eq(itag + " rebuilt stat 68 = -speed", st.get((68, 0)), -sp)
                cur_w = sum(1 for sid in (21, 22, 23, 24, 159, 160, 68) if (sid, 0) in st)
                print("H1B weapon %s: q %d eth %d rebuilt %s" % (
                    itag, q, eth, {sid: st.get((sid, 0)) for sid in (20, 21, 22, 23, 24, 67, 68, 159, 160)
                                   if (sid, 0) in st}))
            a = armor.get(code)
            if a and ival(a.get("block")):
                ck.eq(itag + " rebuilt stat 20 = armor.block", st.get((20, 0)), ival(a["block"]))
            if it.get("runeword"):
                rwv = it["rw"][0] | it["rw"][1] << 12
                ck.eq(itag + " item data +0x38 = file runeword field", r["rw38"], rwv)
                nrw += 1
        for x in rw[:nrw]:
            ck.eq(tag + " RWR 16 bits = file runeword field", x["eax"], next(
                it["rw"][0] | it["rw"][1] << 12 for it in fi if it.get("runeword")))
        if f["corpses"]:
            print("H1B corpse %s: read %d corpse(s), %d items" % (tag, len(f["corpses"]),
                                                                  sum(c["items"]["count"] for c in f["corpses"])))
    # --- bit 13
    b13s = [d for t, d in ev if t == "B13S"]
    b13c = [d for t, d in ev if t == "B13C"]
    setf = [d for t, d in ev if t == "SETF"]
    wt = [d for t, d in ev if t == "WTCH"]
    w0 = next((d for t, d in ev if t == "WTCH0"), None)
    cps = [d for t, d in ev if t == "CPOST"]
    gold = [d for t, d in ev if t == "GOLD"]
    copy = [d for t, d in ev if t in ("COPY", "COPY2")]
    for d in b13c:
        ck.eq("%s B13C id %d in the tick's ActUnitsFrameReset call" % (name, d["id"]), (d["in_tick"], d["ret"]),
              (1, 0x0053B049))
        ck.eq("%s B13C id %d on the ground" % (name, d["id"]), d["mode"], 3)
    for d in b13s:
        ck.eq("%s B13S id %d: create parameters +0x2C = 0" % (name, d["id"]), d["p2c"], 0)
    cleared = {d["id"] for d in b13c}
    for c in cps:
        if c.get("flags", 0) & 0x2000:
            print("H1B bit13 %s: drop id %d %s flags 0x%X at creation; cleared by the ground pass: %s" % (
                name, c["id"], c.get("code"), c["flags"], c["id"] in cleared))
    off = [d for d in wt if d["pc"] not in SETF_PCS]
    if w0:
        bits = [(d["pc"], d["flags"] & 0x2000) for d in wt]
        changes = []
        prev = w0.get("flags", 0) & 0x2000
        for d in wt:
            b = d["flags"] & 0x2000
            if b != prev:
                changes.append(("%08X" % d["pc"], "set" if b else "clear", d["in_tick"]))
            prev = b
        ck.eq("%s watched flags: bit-13 changes outside ITEMS_SetFlag" % name,
              [c for c in changes if int(c[0], 16) not in SETF_PCS], [])
        print("H1B watch %s: unit id %s armed flags 0x%X; %d writes (%d from ITEMS_SetFlag); bit-13 changes %s" % (
            name, w0.get("id"), w0.get("flags", 0), len(wt), len(wt) - len(off), changes))
        del bits
    if b13s or b13c or setf or gold or copy:
        print("H1B bit13 %s: B13S %d, B13C %d (ids %s), SETF %d (rets %s), GOLD %d, COPY %d" % (
            name, len(b13s), len(b13c), sorted(cleared), len(setf),
            sorted({"%08X/%d" % (d["ret"], d["set"]) for d in setf}), len(gold), len(copy)))
    return ck


def main(argv):
    if len(argv) < 3 or argv[0] != "check":
        print(__doc__)
        return 2
    excel = argv[1]
    isc, kinds = d2s.load_isc(excel), d2s.load_kinds(excel)
    vshift = {ival(r["ID"]): ival(r["ValShift"]) for r in table(excel, "itemstatcost.txt") if r["ID"].strip()}
    exp_rows = table(excel, "experience.txt")
    weapons = {r["code"]: r for r in table(excel, "weapons.txt") if r.get("code")}
    armor = {r["code"]: r for r in table(excel, "armor.txt") if r.get("code")}
    T = (isc, kinds, vshift, exp_rows, weapons, armor, None)
    total = bad = 0
    for log in argv[2:]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = d2sio.check(excel, log, [])
        lines = buf.getvalue().splitlines()
        print("D2SIO %s: %s" % (os.path.basename(log), lines[-1] if lines else "?"))
        # d2sio.py compares the left/right mouse words of a write with player data +0x74/+0x70; after a weapon swap
        # the writer's source is the unit's current skill (0x00620190/0x006201D0), which the WSKL lines log and the
        # mouse group below compares. Those two d2sio comparisons are superseded when the log has WSKL lines.
        has_wskl = any(t == "WSKL" for t, _ in d2sio.events(log))
        other = 0
        # d2sio.py counts every RITEM of a load segment; item copies after the load (COPY lines: the corpse's items
        # at a death) add RITEM lines of their own. Its count mismatch is explained when the excess equals them.
        evs = d2sio.events(log)
        rhs = [k for k, (t, _) in enumerate(evs) if t == "RHDR"] + [len(evs)]
        explained = set()
        for a, b in zip(rhs, rhs[1:]):
            seg = evs[a:b]
            kl = next((n for n, (t, _) in enumerate(seg) if t == "LFIN2"), len(seg))
            nri, ncp = sum(1 for t, _ in seg[kl:] if t == "RITEM"), sum(1 for t, _ in seg[kl:] if t in ("COPY", "COPY2"))
            if nri and nri == ncp:
                explained.add(sum(1 for t, _ in seg if t == "RITEM"))
        for ln in lines:
            if "MISMATCH" in ln:
                sup = has_wskl and ("MISMATCH mouse[0] skill" in ln or "MISMATCH mouse[1] skill" in ln)
                if "MISMATCH RITEM count" in ln and int(ln.split("file ")[1].split(",")[0]) in explained:
                    sup = True
                print("  " + ln.strip() + ("   (superseded or explained: see the H1B groups)" if sup else ""))
                other += 0 if sup else 1
        rc = 1 if other else 0
        ck = check_log(excel, log, T)
        print("H1B TOTAL %s: %d comparisons, %d mismatches; d2sio rc %d" % (os.path.basename(log), ck.n, ck.bad, rc))
        total += ck.n
        bad += ck.bad + (1 if rc else 0)
    print("ALL %d H1B comparisons, %d failing (mismatches + d2sio failures)" % (total, bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
