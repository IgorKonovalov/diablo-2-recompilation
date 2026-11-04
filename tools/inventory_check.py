"""Plan 0060 Phase 2 checker: predicts each logged case from tools/item_inventory.py BEFORE it is compared, then compares.

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
    for line in open(path, errors="replace"):
        tag, _, rest = line.partition(" ")
        if tag not in ("GDI", "GDO", "IPG", "IPX", "DCI", "SWP", "SWF", "PKT", "PKR", "ARM", "PLR"):
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


def predict(logs, wrong=None):
    fld = field()
    classes = item_classes()
    preds = []
    for lg in logs:
        ev = parse(lg)
        name = os.path.basename(lg)
        frames = sorted({e["f"] for t, e in ev if t == "SWP"})
        for i, (t, e) in enumerate(ev):
            if t == "GDI":
                p = {"log": name, "kind": "ground", "i": i, "f": e["f"]}
                try:
                    p["pred"] = search(e, fld, wrong)
                    p["ctl"] = {c: search(e, fld, c) for c in CONTROLS}
                except OutOfWindow as ex:
                    p["oow"] = str(ex)
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
    sep_cases = {c: [] for c in CONTROLS}
    oow = 0
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
                if tuple(p["ctl"][c]) != obs:
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
            fr = [e for t, e in ev[i + 1:] if t == "SWF" and e["item"]["id"] == p["id"]]
            last = max([e["f"] for t, e in ev if t == "SWP"] or [0])
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
                print("  %-12s fails %d%s" % (c, ctlfail[c], "" if ctlfail[c] else "  <-- separates nothing in this batch"))
        print("mismatches: %d" % len(mism))
        for p, why in mism[:20]:
            print("  %s %s #%d: %s" % (p["log"], p["kind"], p["i"], why))
    return mism, flat


def main(argv):
    if not argv:
        print(__doc__)
        return 2
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
