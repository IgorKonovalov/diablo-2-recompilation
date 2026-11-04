"""Plan 0060 Phase 2 checker: predicts each logged case from tools/item_inventory.py BEFORE it is compared, then compares.

  python3 -I tools/inventory_check.py prior OUT.prior                    # a-priori potion table, before any session
  python3 -I tools/inventory_check.py predict OUT.pred LOG [LOG ...]    # inputs only: GDI windows, IPG items, SWP frames
  python3 -I tools/inventory_check.py check OUT.pred LOG [LOG ...] [--wrong CTL]
  python3 -I tools/inventory_check.py selftest                          # no-game tests (also tools/test_inventory_check.py)

`predict` reads only the lines a case's INPUTS are (GDI, IPG, DCI's item before its first sweep, the SWP frame list) and
writes one JSON line per case; the file is committed before `check` runs, so a prediction is never fitted to an output.
`check` prints the outcome mix per case kind and the live negative controls: every wrong reading in CONTROLS is predicted
for each ground search too, and a control that matches every kept case separates nothing and fails the check
(exit 1), as does any mismatch of the main prediction. `--wrong CTL` makes the main prediction use the named wrong
reading: the check must then fail (the deliberate-wrong test).

Case kinds:
  ground    GDI -> GDO: the cell, the room, with the model's search (item_inventory.ground_drop_cell) over the logged
            collision window; outcome classes by the ring the search ended in
  expiry    IPG -> IPX: item data +0x24 after ItemPlaceOnGround = ItemGroundExpiry(frame, ...)
  monster   DCI: item data +0x24 after a monster's or chest's ItemCreate: 0 predicted (items/0014 § 3); and every SWP
            dump after: still 0
  sweep     each placed item with e != 0: freed at the first SWP frame >= e (SWF), and monster items never freed
  potion    (revision 2) UP0 .. UP1 of a stock kind-3 potion (pSpell 3): the two draws from the logged seed (n, r1, r2, the
            doubling, the seed after), the amount, the list's end, the stored rate; the model is
            item_inventory.potion_scale and use_stat_entry's formulas; a use whose list already exists blends with the
            previous use's rate and end (the log's UAL line tells a fresh list from an existing one)
  restore   RV1 (and RV2): the item's +0x24 after InactiveItemRestoreOne = the saved word, or frame + 15000 when saved is
            non-zero and below it; SV1: the saved word = ItemGroundExpiry(frame, the item)
  keep      PKT .. PKR: the player's seed is unchanged across the request (no draw), or the difference is reported
"""
import base64
import csv
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import item_inventory as ii  # noqa: E402

ROOT = os.path.dirname(HERE)
FIELD_FILE = os.path.join(ROOT, "workspace", "merged", "data", "global", "expfield.d2")
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
CONTROLS = ("nooffset", "noitembit", "noline", "fixedbase", "capsfirst", "leq", "first", "offset32", "linecellmask")
SWEEP_PERIOD = 1500
REQUIRED = ("nooffset", "noitembit", "leq", "first")


class OutOfWindow(Exception):
    pass


class Cells:
    """The logged window of a room's cells; asking outside the window (inside the room) is an error, never a 0."""

    def __init__(self, rect, rows):
        self.rect = rect
        self.d = {}
        self.xr = None
        for y, xa, hx in rows:
            b = bytes.fromhex(hx)
            for i in range(len(b) // 2):
                self.d[(xa + i, y)] = b[2 * i] | (b[2 * i + 1] << 8)
        self.rows = rows

    def get(self, key, default=0):
        if key in self.d:
            return self.d[key]
        raise OutOfWindow(key)


def parse(path):
    out = []
    for line in open(path, errors="replace").read().splitlines():
        tag, _, rest = line.partition(" ")
        if tag not in ("GDI", "GDO", "IPG", "IPX", "DCI", "SWP", "SWF", "PKT", "PKR", "ARM", "PLR", "UP0", "UP1", "UD1", "UD2",
                   "UDV", "UAD", "UAL", "UQE", "USS", "RV1", "SV1", "RM"):
            continue
        try:
            out.append((tag, json.loads(rest)))
        except ValueError:
            pass
    return out


def build_rooms(z):
    rooms = {}
    for r in json.loads(zlib.decompress(base64.b64decode(z))):
        x0, y0, w, h = r["rect"]
        rm = ii.Room(x0, y0, w, h, None if r["nocells"] else Cells(r["rect"], r["rows"]))
        rm.ptr = r["r"]
        rm.near_ptrs = r["near"]
        rooms[r["r"]] = rm
    for rm in rooms.values():
        rm.near = [rooms.get(p) for p in rm.near_ptrs]
    return rooms


def field():
    return open(FIELD_FILE, "rb").read()[10:]


def search(case, fld, ctl=None):
    """-> (room ptr, x, y) of the model's search for a GDI record; raises OutOfWindow."""
    rooms = build_rooms(case["z"])
    room0 = rooms[case["room"]]
    rm, x, y = ii.ground_drop_cell(room0, case["x"], case["y"], fld, 1, ctl)
    return (rm.ptr if rm else 0), x, y


def ring_of(case, res):
    """The ring the search ended in, from the start the code used (offset start if its room exists, else the position)."""
    sx, sy = case["x"] + 2, case["y"] + 3
    d = max(abs(res[1] - sx), abs(res[2] - sy))
    return d


def item_classes():
    """class index (unit +4) -> (code, quest, type) over weapons, armor, misc, skipping the 'Expansion' rows."""
    out = []
    for n in ("weapons", "armor", "misc"):
        rows = list(csv.reader(open(os.path.join(EXCEL, n + ".txt"), encoding="latin1"), delimiter="\t"))
        h = rows[0]
        for r in rows[1:]:
            code = r[h.index("code")]
            if not code or code == "Expansion":
                continue
            out.append((code, r[h.index("quest")] if "quest" in h else "", r[h.index("type")]))
    return out


def predict_expiry(item, frame, classes):
    code, quest, typ = classes[item["c"]] if 0 <= item["c"] < len(classes) else ("?", "", "?")
    filler = typ in ("gem0", "gem1", "gem2", "gem3", "gem4", "gema", "gemb", "geme", "gems", "gemt", "gemr", "gemd",
                     "gemp", "gemz", "gemo", "rune", "jewl", "gemb", "gem")
    return ii.ground_expiry(frame, 1 if quest not in ("", "0") else 0, item.get("q", 0), 4 if typ == "gold" else 0, 0,
                            filler), code, typ, filler


def misc_rows():
    rows = list(csv.reader(open(os.path.join(EXCEL, "misc.txt"), encoding="latin1"), delimiter="\t"))
    h = rows[0]
    out = {}
    for r in rows[1:]:
        if len(r) > h.index("pSpell") and r[h.index("code")]:
            out[r[h.index("code")]] = {c: r[h.index(c)] for c in ("pSpell", "len", "stat1", "calc1", "state")
                                      if c in h}
    return out


def seed_of(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def restore_expect(saved, lim):
    """InactiveItemRestoreOne's write (0x005419E2-0x00541A04): the saved word when it is 0 or not below frame + 15000
    (signed), else frame + 15000."""
    return saved if (saved == 0 or saved >= lim) else lim


def potion_cases(ev, classes, misc):
    """One record per UP0..UP1 of a pSpell-3 potion, with the model's prediction from UP0's inputs and the previous
    use's list (carried through the log)."""
    out, lists = [], {}
    i = 0
    while i < len(ev):
        t, e = ev[i]
        if t != "UP0":
            i += 1
            continue
        j = next((k for k in range(i + 1, len(ev)) if ev[k][0] == "UP1"), None)
        if j is None:
            break
        code = classes[e["item"]["c"]][0] if e["item"] and 0 <= e["item"]["c"] < len(classes) else "?"
        row = misc.get(code)
        rec = {"i": i, "j": j, "code": code, "f": e["f"]}
        if not row or row["pSpell"] != "3":
            rec["kind"] = "other"
            out.append(rec)
            i = j + 1
            continue
        stat = ii.MANAREC if row["stat1"] == "manarecovery" else ii.HPREGEN
        calc, ln = int(row["calc1"]), int(row["len"])
        u = ii.Unit(typ=e["ut"], cls=e["ucls"], uid=e["uid"], low=seed_of(e["sd"])[0], high=seed_of(e["sd"])[1],
                    stats={ii.VIT: e["stats"]["3"] or 0, ii.ENE: e["stats"]["1"] or 0})
        n = u.stat(ii.ENE if stat == ii.MANAREC else ii.VIT)
        low0 = (u.low, u.high)
        v = ii.potion_scale(u, stat, calc)
        v = ii.i32(v << 0)
        seed_after = (u.low, u.high)
        # a list exists when the log shows no allocation (UAL) between UP0 and UP1
        fresh = any(ev[k][0] == "UAL" for k in range(i + 1, j))
        key = (e["uid"], stat)
        prev = lists.get(key)
        if fresh or prev is None or prev["end"] <= e["f"]:
            base, rem = 0, 0
        else:
            base, rem = prev["rate"], prev["end"] - e["f"]
        end = ii.i32(e["f"] + rem + ln)
        d = ii.i32(ln + rem)
        rate = ii.tdiv(ii.i32(ii.i32(base * rem) + v), d) if d > 0 else None
        lists[key] = {"end": end, "rate": rate}
        tot = ii.potion_total(e["ucls"], stat, calc)
        prior = [ii.tdiv(tot, ln), ii.tdiv(ii.i32(tot * 2), ln)] if ln > 0 else []
        rec.update(prior=prior, kind="potion", stat=stat, n=n, v=v, rate=rate, end=end, seed0="%08x:%08x" % low0,
                   seed1="%08x:%08x" % seed_after, fresh=fresh, doubled=None)
        out.append(rec)
        i = j + 1
    return out


def predict(logs, wrong=None):
    fld = field()
    classes = item_classes()
    preds = []
    for lg in logs:
        ev = parse(lg)
        name = os.path.basename(lg)
        if any(t == "UP0" for t, _ in ev):
            misc = misc_rows()
            for rec in potion_cases(ev, classes, misc):
                rec.update(log=name)
                if rec["kind"] == "potion" and wrong == "onedraw":
                    rec["seed1"] = rec["seed0"]
                preds.append(dict(rec, kind=rec["kind"] if rec["kind"] == "potion" else "usepot-other"))
        for i, (t, e) in enumerate(ev):
            if t == "RV1":
                preds.append({"log": name, "kind": "restore", "i": i, "pred": restore_expect(e["saved"], e["lim"]),
                              "lim": e["lim"], "f": e["f"]})
            elif t == "SV1":
                pe, code, typ, filler = predict_expiry(e["item"], e["f"], classes)
                preds.append({"log": name, "kind": "save", "i": i, "pred": pe, "f": e["f"], "code": code})
            elif t == "PKT":
                k = next((j for j in range(i + 1, len(ev)) if ev[j][0] == "PKR" and ev[j][1]["op"] == e["op"]), None)
                if k is not None and e.get("sd"):
                    preds.append({"log": name, "kind": "pktseed", "i": i, "j": k, "op": e["op"], "pred": e["sd"]})
        frames = sorted({e["f"] for t, e in ev if t == "SWP"})
        for i, (t, e) in enumerate(ev):
            if t == "GDI":
                p = {"log": name, "kind": "ground", "i": i, "f": e["f"]}
                try:
                    p["pred"] = search(e, fld, wrong)
                except OutOfWindow as ex:
                    p["oow"] = str(ex)
                p["ctl"] = {}
                for c in CONTROLS:     # a control that reads past the window is undecided for the case, not a failure
                    try:
                        p["ctl"][c] = search(e, fld, c)
                    except OutOfWindow:
                        p["ctl"][c] = None
                preds.append(p)
            elif t == "IPG":
                pe, code, typ, filler = predict_expiry(e["item"], e["f"], classes)
                if wrong == "noexpiry":
                    pe = 0
                preds.append({"log": name, "kind": "expiry", "i": i, "id": e["item"]["id"], "pred": pe, "code": code,
                              "type": typ, "filler": filler, "f": e["f"]})
                nxt = [f for f in frames if f >= pe] if pe else []
                preds.append({"log": name, "kind": "sweep", "i": i, "id": e["item"]["id"], "e": pe,
                              "pred": nxt[0] if nxt else None, "f": e["f"]})
            elif t == "ARM":
                k = next((j for j in range(i + 1, len(ev)) if ev[j][0] == "PKT" and ev[j][1]["op"] == e["op"]), None)
                if k is None:
                    continue
                pk = ev[k][1]
                raw = bytes.fromhex(pk["pkt"])
                iid = int.from_bytes(raw[1:5], "little")
                lid = next((x[1]["lid"] for x in reversed(ev[:k]) if x[0] == "PLR"), None)
                if e["op"] == 0x18:
                    occ = [(it[3], it[4]) for it in pk["inv"] if it != "err" and it[2] == 4]
                    pr = ii.pkt18_expect(e["now"], lid in ii.TOWN_LEVELS, int.from_bytes(raw[5:9], "little"),
                                         int.from_bytes(raw[9:13], "little"), 1, 1, True, occ,
                                         "stashopen" if wrong == "stashopen" else None)
                    preds.append({"log": name, "kind": "page4", "i": k, "id": iid, "pred": list(pr[:2]) + [list(pr[2]) if pr[2] else None],
                                  "lid": lid, "page": e["now"]})
                elif e["op"] == 0x23:
                    occ = [it[3] for it in pk["inv"] if it != "err" and it[5] == 2]
                    ok = ii.belt23_expect(e["now"], occ, 12, True, "numboxes" if wrong == "numboxes" else None)
                    preds.append({"log": name, "kind": "belt23", "i": k, "id": iid, "pred": ok, "box": e["now"], "occ": occ})
            elif t == "DCI":
                pm = 0 if wrong != "monster15000" else e["f"] + 15000
                preds.append({"log": name, "kind": "monster", "i": i, "id": e["item"]["id"], "pred": pm, "f": e["f"]})
    return preds


def check(preds, logs, show=True):
    rows = {}
    for lg in logs:
        rows[os.path.basename(lg)] = parse(lg)
    mism, mix, ctlfail, nct = [], {}, {c: 0 for c in CONTROLS}, 0
    ctlund = {c: 0 for c in CONTROLS}
    sep_cases = {c: [] for c in CONTROLS}
    oow = 0
    explained = []
    for p in preds:
        ev = rows[p["log"]]
        i = p["i"]
        if p["kind"] == "ground":
            if "oow" in p:
                oow += 1
                mism.append((p, "model touched a cell outside the logged window %s" % p["oow"]))
                continue
            go = next((e for t, e in ev[i + 1:] if t == "GDO"), None)
            gi = ev[i][1]
            obs = (go["room"], go["x"], go["y"])
            ring = ring_of(gi, obs)
            if ring == 0:
                cls = "ring 0 (start cell free)"
            elif ring <= 3:
                cls = "ring %d" % ring
            else:
                cls = "ring 4+"
            if (obs[1], obs[2]) == (gi["x"], gi["y"]) or obs[0] == 0:
                cls += ", at the position or null"
            if obs[1] - gi["x"] == 2 and obs[2] - gi["y"] == 3:
                cls = "offset start taken"
            nct += 1
            if tuple(p["pred"]) != obs:
                mism.append((p, "predicted %s observed %s" % (tuple(p["pred"]), obs)))
            for c in CONTROLS:
                if p["ctl"][c] is None:
                    ctlund[c] += 1
                elif tuple(p["ctl"][c]) != obs:
                    ctlfail[c] += 1
                    sep_cases[c].append(i)
            mix.setdefault("ground", {})
            mix["ground"][cls] = mix["ground"].get(cls, 0) + 1
        elif p["kind"] == "expiry":
            ix = next((e for t, e in ev[i + 1:] if t == "IPX"), None)
            obs = ix["item"]["e"]
            k = "expiry %s" % ("+15000" if p["pred"] - p["f"] == 15000 else "other")
            if p["filler"] and p["type"] in ("gem0", "gem1", "gem2", "gem3", "gem4", "rune", "jewl") and False:
                k += " (filler)"
            mix.setdefault("expiry", {})[k] = mix.setdefault("expiry", {}).get(k, 0) + 1
            if obs != p["pred"]:
                mism.append((p, "expiry predicted %d observed %d" % (p["pred"], obs)))
        elif p["kind"] in ("page4", "belt23"):
            pr = next((e for t, e in ev[i + 1:] if t == "PKR"), None)
            mine = [it for it in pr["inv"] if it != "err" and it[0] == p["id"]] if pr and pr["inv"] else []
            it = mine[0] if mine else None
            if p["kind"] == "page4":
                obs = [pr["eax"], it[2] if it else None, [it[3], it[4]] if it and it[2] == 4 else None]
                k = "page 4 in town (lid %s): handler returned %s" % (p["lid"], pr["eax"])
            else:
                obs = bool(it and it[5] == 2 and it[3] == p["box"])
                k = "belt box %d: %s" % (p["box"], "stays" if obs else "not placed (handler returned %s)" % pr["eax"])
            mix.setdefault(p["kind"], {})[k] = mix.setdefault(p["kind"], {}).get(k, 0) + 1
            if obs != p["pred"]:
                mism.append((p, "predicted %s observed %s" % (p["pred"], obs)))
        elif p["kind"] == "potion":
            i0, j0 = p["i"], p["j"]
            seg = ev[i0:j0 + 1]
            up1 = ev[j0][1]
            tags = [t for t, _ in seg]
            ud1 = next((e for t, e in seg if t == "UD1"), None)
            ud2 = next((e for t, e in seg if t == "UD2"), None)
            udv = next((e for t, e in seg if t == "UDV"), None)
            uss = next((e for t, e in seg if t == "USS"), None)
            ual = next((e for t, e in seg if t == "UAL"), None)
            bad = []
            if p["n"] > 0:
                if not ud1 or not ud2 or not udv:
                    bad.append("draw lines missing")
                else:
                    if ud1["n"] != p["n"]:
                        bad.append("n %s predicted %s" % (ud1["n"], p["n"]))
                    if ud1["sd"] != p["seed0"]:
                        bad.append("seed before draw 1 %s predicted %s" % (ud1["sd"], p["seed0"]))
                    if ud2["sd"] != p["seed1"]:
                        bad.append("seed after draw 2 %s predicted %s" % (ud2["sd"], p["seed1"]))
                    if up1["sd"] != p["seed1"]:
                        bad.append("seed at return %s predicted %s" % (up1["sd"], p["seed1"]))
                    dbl = ud2["r2"] < ud2["h"]
                    # the amount before the test is the scaled total; after it the same, doubled when r2 < r1 >> 1
                    p["doubled"] = dbl
                    if udv["v"] != (ud2["v"] * 2 if dbl else ud2["v"]):
                        bad.append("amount after the test %s vs %s doubled=%s" % (udv["v"], ud2["v"], dbl))
                    p["v_obs"] = udv["v"]
            elif ud1:
                bad.append("a draw with n = 0")
            if uss is None:
                bad.append("no SetStat")
            else:
                # the model's v is the value after its own two draws from the logged seed; the prior pair is the same
                # table computed before any session (the `prior` command's file)
                if uss["rate"] != p["rate"]:
                    bad.append("rate %s predicted %s" % (uss["rate"], p["rate"]))
                if p["fresh"] and uss["rate"] not in p["prior"]:
                    bad.append("rate %s not in the prior pair %s" % (uss["rate"], p["prior"]))
            if ual is not None and ual["a"][2] != p["end"]:
                bad.append("list end %s predicted %s" % (ual["a"][2], p["end"]))
            if up1["eax"] != 1:
                bad.append("returned %s" % up1["eax"])
            if p["n"] <= 0:
                kk = "potion n = 0: no draw, seed unchanged %s" % (up1["sd"] == p["seed0"])
            else:
                kk = "potion %s, n %s: %s" % (p["code"], "ene" if p["stat"] == ii.MANAREC else "vit",
                                              "doubled" if p["doubled"] else "not doubled")
            kk += ", %s list" % ("fresh" if p["fresh"] else "existing")
            mix.setdefault("potion", {})[kk] = mix.setdefault("potion", {}).get(kk, 0) + 1
            if bad:
                mism.append((p, "; ".join(bad)))
        elif p["kind"] == "usepot-other":
            ups = [e for t, e in ev[p["i"]:p["j"] + 1]]
            mix.setdefault("use, not a stock kind-3 potion (%s)" % p["code"], {})["seen"] = 1 + mix.get(
                "use, not a stock kind-3 potion (%s)" % p["code"], {}).get("seen", 0)
        elif p["kind"] == "restore":
            after = next((e for t, e in ev[p["i"] + 1:] if t in ("RV1",)), None)
            # the item's +0x24 after the write: the next dump (SWP) is the earliest independent read; here the item field
            # at RV1 is read before the write, so the write is compared with the first later SWP entry of the same cell
            rv = ev[p["i"]][1]
            k = "restore: saved %s, lim %s -> expect %s (%s)" % (
                "0" if rv["saved"] == 0 else "set", rv["lim"], p["pred"],
                "lim" if p["pred"] == rv["lim"] else "saved")
            key = "restore wrote " + ("lim (frame + 15000)" if p["pred"] == rv["lim"] and rv["saved"] != 0 else "saved word")
            mix.setdefault("restore", {})[key] = mix.setdefault("restore", {}).get(key, 0) + 1
            nxt = [x for t, e in ev[p["i"] + 1:] if t == "SWP" for x in e["items"]
                   if x[1] == rv["item"]["c"] and x[4] == rv["item"].get("x") and x[5] == rv["item"].get("y")]
            if nxt and nxt[0][3] != p["pred"]:
                mism.append((p, "restore predicted +0x24 %s, first later dump of the cell shows %s" % (p["pred"], nxt[0][3])))
            if not nxt:
                mix.setdefault("restore", {})["no later dump lists the cell (write unread)"] = 1 + mix["restore"].get(
                    "no later dump lists the cell (write unread)", 0)
            elif p["pred"] != 0:
                # the restored copy (a new id) is freed at the first sweep frame at or past its +0x24, when a dump
                # at or past it exists
                nid = next((x[0] for t, e in ev[i + 1:] if t == "SWP" for x in e["items"]
                            if x[1] == rv["item"]["c"] and x[4] == rv["item"].get("x") and x[5] == rv["item"].get("y")
                            and x[3] == p["pred"]), None)
                frames = sorted({e["f"] for t, e in ev[i + 1:] if t == "SWP"})
                want = next((f for f in frames if f >= p["pred"]), None)
                if nid is not None:
                    fr = [e for t, e in ev[i + 1:] if t == "SWF" and e["item"]["id"] == nid]
                    resaved = next((e["f"] for t, e in ev[i + 1:] if t == "SV1" and e["item"]["id"] == nid), None)
                    if want is not None and resaved is not None and resaved < want:
                        kk = "restored copy saved again with its released room (SV1) before the predicted sweep: not an active-room case"
                        mix.setdefault("restored sweep", {})[kk] = 1 + mix.get("restored sweep", {}).get(kk, 0)
                        explained.append(p)
                    elif want is None:
                        kk = "no sweep dump at or past the restored +0x24 (unresolved)"
                        mix.setdefault("restored sweep", {})[kk] = 1 + mix.get("restored sweep", {}).get(kk, 0)
                    else:
                        k2 = "restored copy freed at the predicted sweep" if fr and fr[0]["f"] == want else "mismatch"
                        mix.setdefault("restored sweep", {})[k2] = 1 + mix.get("restored sweep", {}).get(k2, 0)
                        if k2 == "mismatch":
                            mism.append((p, "restored copy %d predicted free at %s observed %s" % (
                                nid, want, fr[0]["f"] if fr else None)))
        elif p["kind"] == "save":
            sv = ev[p["i"]][1]
            k = "save: ItemGroundExpiry at the save"
            mix.setdefault("save", {})[k] = mix.setdefault("save", {}).get(k, 0) + 1
            if sv["saved"] != p["pred"]:
                mism.append((p, "saved %s predicted %s" % (sv["saved"], p["pred"])))
        elif p["kind"] == "pktseed":
            a, b = ev[p["i"]][1], ev[p["j"]][1]
            same = a.get("sd") == b.get("sd")
            k = "request 0x%02x: player seed %s" % (p["op"], "unchanged" if same else "advanced")
            mix.setdefault("pktseed", {})[k] = mix.setdefault("pktseed", {}).get(k, 0) + 1
            # reported, never a mismatch: no model says how many draws a move makes (items/0013 § 9)
        elif p["kind"] == "monster":
            dc = ev[i][1]["item"]
            obs = dc["e"]
            k = "monster/chest item +0x24 = %s at creation" % ("0" if obs == 0 else "non-zero")
            mix.setdefault("monster", {})[k] = mix.setdefault("monster", {}).get(k, 0) + 1
            if obs != p["pred"]:
                mism.append((p, "monster item e predicted %d observed %d" % (p["pred"], obs)))
            later = [x for t, e in ev[i + 1:] if t == "SWP" for x in e["items"] if x[0] == dc["id"]]
            k = "monster item in %d later sweep dump(s)" % len(later)
            mix.setdefault("monster", {})["later sweep dumps: items seen"] = (
                mix["monster"].get("later sweep dumps: items seen", 0) + len(later))
            bad = [x for x in later if x[3] != 0]
            if bad:
                mism.append((p, "monster item later non-zero %s" % bad[0]))
            freed = [e for t, e in ev[i + 1:] if t == "SWF" and e["item"]["id"] == dc["id"]]
            if freed:
                mism.append((p, "monster item freed by the sweep at frame %s" % freed[0]["f"]))
        elif p["kind"] == "sweep":
            saved_at = next((e["f"] for t, e in ev[i + 1:] if t == "SV1" and e["item"]["id"] == p["id"]), None)
            if saved_at is not None and (p["pred"] is None or saved_at < p["pred"]):
                # revision 2: the room's release is logged directly (SV1 is InactiveItemSave's call): the item left the
                # active room's list before the predicted sweep, so it is not an active-room sweep case; its restored copy
                # is predicted under "restore" and "restored sweep"
                k = "item saved with its released room (SV1) before the predicted sweep: not an active-room case"
                mix.setdefault("sweep", {})[k] = mix.setdefault("sweep", {}).get(k, 0) + 1
                explained.append(p)
                continue
            fr = [e for t, e in ev[i + 1:] if t == "SWF" and e["item"]["id"] == p["id"]]
            seen = [x for t, e in ev[i + 1:] if t == "SWP" for x in e["items"] if x[0] == p["id"]]
            if not seen and not fr and not any(t == "SWP" for t, _ in ev[i + 1:]):
                k = "no sweep dump after the drop (the session ended first): unresolved, not a case"
                mix.setdefault("sweep", {})[k] = mix.setdefault("sweep", {}).get(k, 0) + 1
                continue
            if not seen and not fr:
                # The class was added after the first check, which counted these as 6 failed predictions. It excludes an
                # item only on an independent record: the player's level (PLR lid) before every later sweep differs
                # from the level the drop was made on. Absence from the dumps alone is not accepted as inactivity.
                dlid = next((x[1]["lid"] for x in reversed(ev[:i]) if x[0] == "PLR"), None)
                later_lids = []
                last = None
                for t, e in ev[i + 1:]:
                    if t == "PLR":
                        last = e["lid"]
                    elif t == "SWP":
                        later_lids.append(last)
                if dlid is not None and later_lids and all(l is not None and l != dlid for l in later_lids):
                    k = ("player on another level at every later sweep, item in no dump and no free: not a sweep case "
                         "(a failed prediction at the first check; class added after it)")
                    mix.setdefault("sweep", {})[k] = mix.setdefault("sweep", {}).get(k, 0) + 1
                    explained.append(p)
                    continue
                mism.append((p, "not listed at any later sweep and not freed; the player's level does not show the room inactive"))
                continue
            if p["pred"] is None:
                k = "no sweep frame logged at or past the expiry (unresolved)"
                mix.setdefault("sweep", {})[k] = mix.setdefault("sweep", {}).get(k, 0) + 1
                if fr:
                    mism.append((p, "freed at %s, predicted no frame yet" % fr[0]["f"]))
                continue
            k = "freed at the predicted sweep" if fr and fr[0]["f"] == p["pred"] else "mismatch"
            mix.setdefault("sweep", {})[k] = mix.setdefault("sweep", {}).get(k, 0) + 1
            if not fr or fr[0]["f"] != p["pred"]:
                mism.append((p, "sweep: predicted free at %s observed %s" % (p["pred"], fr[0]["f"] if fr else None)))
    flat = [c for c in CONTROLS if nct and ctlfail[c] == 0]
    if show:
        print("cases: %d predictions" % len(preds))
        for k, d in mix.items():
            print("kind %s: %s" % (k, "; ".join("%s: %d" % kv for kv in sorted(d.items()))))
        if nct:
            print("controls over %d ground cases (observed differs from the wrong reading in n cases):" % nct)
            for c in CONTROLS:
                print("  %-12s fails %d%s%s" % (c, ctlfail[c], "" if ctlfail[c] else "  <-- separates nothing in this batch",
                                              ("  (undecided, read past the window: %d)" % ctlund[c]) if ctlund[c] else ""))
        # restored monster drops: a created item that reappears at the same class and cell under another id
        rest = []
        for p in preds:
            if p["kind"] != "monster":
                continue
            ev = rows[p["log"]]
            dc = ev[p["i"]][1]["item"]
            for t, e in ev[p["i"] + 1:]:
                if t == "SWP":
                    m = [x for x in e["items"] if x[1] == dc["c"] and x[4] == dc.get("x") and x[5] == dc.get("y") and x[0] != dc["id"]]
                    if m:
                        rest.append((dc["id"], m[0][0], e["f"], m[0][3]))
                        break
        if rest:
            print("monster drops met again under a new id at the same class and cell (restored from a record): %d: %s" % (
                len(rest), "; ".join("id %d -> %d at sweep %d, +0x24 %d" % r for r in rest)))
        print("mismatches: %d (excluded sweep predictions: %d, on the player's level record or the item's SV1 save line; these were failed predictions at the first check)" % (len(mism), len(explained)))
        for p, why in mism[:20]:
            print("  %s %s #%d: %s" % (p["log"], p["kind"], p["i"], why))
    return mism, flat


def prior():
    """The a-priori table, written before any session: for each stock kind-3 potion and each class, the total in stored
    units without and with the doubling, the stored rate (total / len, truncated) and the draw chance for a few n."""
    out = []
    for code, row in sorted(misc_rows().items()):
        if row["pSpell"] != "3":
            continue
        stat = ii.MANAREC if row["stat1"] == "manarecovery" else ii.HPREGEN
        calc, ln = int(row["calc1"]), int(row["len"])
        for cls in range(7):
            tot = ii.potion_total(cls, stat, calc)
            out.append({"code": code, "cls": ii.CLASS[cls], "stat": stat, "len": ln, "total": tot,
                        "total2": ii.i32(tot * 2), "rate": ii.tdiv(tot, ln), "rate2": ii.tdiv(ii.i32(tot * 2), ln)})
    return out


def prior_expiry():
    """The a-priori expiry delta (item data +0x24 - frame after ItemPlaceOnGround) of each distinct (code, quality) of the
    run's recipe, from the model alone (item_inventory.ground_expiry), before any session."""
    recipe = json.load(open(os.path.join(ROOT, "tools", "d2s_recipes", "inv-sor2.json")))
    classes = item_classes()
    codes = [c[0] for c in classes]
    qual = {"unique": 7, "set": 5, "rare": 6, "crafted": 8, "suffix": 4, "prefix": 4}
    uniq, out = set(), []
    for it in recipe["items"]:
        if it.get("store") != "inventory":
            continue
        code = it.get("code")
        if code is None:
            # a named unique or set item: its base code is in the table the builder reads; the quality is what matters,
            # and the base is the ring or amulet the recipe names (1 x 1, not a quest item, not a filler)
            code = "rin" if it.get("unique") == "Raven Frost" or it.get("set") == "Angelic Halo" else "amu"
        q = 2
        if "quality" in it:
            q = {"low": 1, "superior": 3}.get(it["quality"], 2)
        for k, v in qual.items():
            if k in it:
                q = v
        if (code, q) in uniq:
            continue
        uniq.add((code, q))
        pe, c, typ, filler = predict_expiry({"c": codes.index(code), "q": q}, 0, classes)
        out.append({"code": code, "quality": q, "type": typ, "filler": filler, "delta": pe})
    return out


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "prior":
        with open(argv[1], "w") as f:
            for r in prior():
                f.write(json.dumps(dict(r, kind="potion-prior"), separators=(",", ":")) + "\n")
            for r in prior_expiry():
                f.write(json.dumps(dict(r, kind="expiry-prior"), separators=(",", ":")) + "\n")
        print("wrote %d prior rows to %s" % (len(prior()) + len(prior_expiry()), argv[1]))
        return 0
    if argv[0] == "predict":
        preds = predict(argv[2:])
        with open(argv[1], "w") as f:
            for p in preds:
                f.write(json.dumps(p, separators=(",", ":")) + "\n")
        print("wrote %d predictions to %s" % (len(preds), argv[1]))
        return 0
    if argv[0] == "check":
        wrong = None
        args = argv[1:]
        if "--wrong" in args:
            i = args.index("--wrong")
            wrong = args[i + 1]
            del args[i:i + 2]
        preds = [json.loads(l) for l in open(args[0])]
        if wrong:
            preds = predict(args[1:], wrong)
        mism, flat = check(preds, args[1:])
        req = [c for c in flat if c in REQUIRED]
        if flat:
            print("controls that separated nothing in this batch (readings the batch does not decide): %s" % ", ".join(flat))
        if req:
            print("FAIL: required controls separated nothing: %s" % ", ".join(req))
        return 1 if mism or req else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
