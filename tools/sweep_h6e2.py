#!/usr/bin/env python3
"""Plan 0038 batch H6e2 (quest-items) checker over tools/gdb/quest-items.gdb logs.

Usage:
  python3 -I tools/sweep_h6e2.py check <excel-dir> <log> [<log> ...]

Models, each read from the code in docs/findings/items/0010-quest-drops.md (§ 5, § 9 and the H6e2 section), checked
against what the game logged (one stock case or more per claim; nothing here is a frequency):

  chest   a quest chest's or the altar's operate (QOW of class 354 box, 355 tr1, 356 msf, 405 qhr, 406 qbr, 407 qey,
          149 vip): with the object in mode 0, the script's gate for the one player (the operating player's record
          words on the QOW line, the PlayerFindItemByCode answers of the gate's own calls, PFI/PFX), then in code order
            box/tr1/msf/vip:  n x QDI (the code, quality 2 box / 7 tr1 msf vip) -> OCD -> QGS -> k x QDC('gld ', 2)
            qhr/qbr/qey:      QGS -> k x QDC('gld ', 2) -> n x QDI (quality 2) -> OCD
          with k = 5 + low32(lo * 0x6AC690C5 + hi) mod 5 on the QGS quest seed, n = 1 when the gate passes, else 0;
          tr1, msf, vip identified (flags bit 4, OCD's re-read of the created item); in mode != 0 nothing.
  object  Wirt's body (268: leg in mode 0, nothing after), the Inifuss tree (30: bks when word 4 bits 0, 1 clear, no
          bkd/bks held, mode 0), the Malus (108), the Lam Esen tome (193): the QDI line(s) inside the script.
  event7  each QOE (QUESTS_ObjectEvent entry): event index 7, the return into OBJ_EventDispatch (0x00586B1B), and the
          next QOT the class's target of items/0010 § 9 called from inside QUESTS_ObjectEvent.
  dup     each PlayerFindItemByCode call: a stat-356 read (PSX) is followed by an answer that holds the item only when
          the value is >= the difficulty.
  gate    each ItemQuestGate call (IQG, IQX): the gate of items/0010 § 5 on the item's code and the record words,
          without the 0x0055CA40 tail (IHD answers are read from the log, as inputs).
Prints one line per case and a SUMMARY line; exit 1 on any mismatch.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402

CHESTS = {  # class: (code, quality, fn lo, fn hi, kind, identified)
    354: ("box ", 2, 0x00599DF0, 0x00599EE0, "e1", False),
    355: ("tr1 ", 7, 0x00599C10, 0x00599CEC, "e1", True),
    356: ("msf ", 7, 0x00599CF0, 0x00599DE6, "e1", True),
    149: ("vip ", 7, 0x0059A7E0, 0x0059AC20, "e1", True),
    405: ("qhr ", 2, 0x005B8860, 0x005B8940, "kh", False),
    407: ("qey ", 2, 0x005B8940, 0x005B8A20, "kh", False),
    406: ("qbr ", 2, 0x005B8A20, 0x005B8B00, "kh", False),
}
OBJECTS = {268: ("leg ", 0x00583EA4), 30: ("bks ", 0x00593C16), 108: ("hdm ", 0x00591B9E), 193: ("bbb ", 0x005B7AF8)}
EVENT7 = {26: 0x00593290, 122: 0x0059B710, 268: 0x00594630, 341: 0x005BCAC0, 367: 0x005B85E0, 371: 0x005956C0,
          376: 0x005B6710, 459: 0x0058B940, 460: 0x0058A500, 461: 0x00589540, 474: 0x0058C0E0, 475: 0x0058C0E0,
          476: 0x0058C0E0}
QOE_LO, QOE_HI = 0x005449E0, 0x00544DA0


def bit(rec, w, b):
    return (rec[w] >> b) & 1 if rec else None


def k_gold(qs):
    lo, hi = (int(x, 16) for x in qs.split(":"))
    return 5 + ((lo * 0x6AC690C5 + hi) & 0xFFFFFFFF) % 5


def item_codes(excel):
    codes = []
    for t in ("weapons", "armor", "misc"):
        h, rows = excel_bin.read_txt(excel_bin.find_file(excel, t, ".txt"))
        ci = h.index("code")
        for r in rows:
            if r[ci]:
                codes.append(r[ci].ljust(4)[:4])
    return codes


def misc_quest(excel):
    """code -> (quest, questdiffcheck) over the three item tables."""
    out = {}
    for t in ("weapons", "armor", "misc"):
        h, rows = excel_bin.read_txt(excel_bin.find_file(excel, t, ".txt"))
        ci, qi = h.index("code"), h.index("quest")
        di = h.index("questdiffcheck") if "questdiffcheck" in h else None
        for r in rows:
            if r[ci]:
                q = int(r[qi]) if r[qi].strip() else 0
                d = int(r[di]) if di is not None and r[di].strip() else 0
                out[r[ci].ljust(4)[:4]] = (q, d)
    return out


PAIRS = {4: 3, 17: 18, 18: 19, 25: 27}      # g_QuestItemWordGate {word, quest}: quest -> word
def gate_model(code, quality, rec, quest, ihd):
    """sub_0055CC90_ItemQuestGate for a non-unique-row case: 0 refuse, 1 allow, None when the case needs an input the
    log does not carry (the unique-row +0x2C branch). ihd: the 0x0055CA40 answers of the call, in order."""
    if code == "ass " and not bit(rec, 9, 5):
        return 0
    if code == "j34 " and bit(rec, 20, 0):
        return 0
    if code == "xyz " and not bit(rec, 20, 5):
        return 0
    if code == "g33 " and (bit(rec, 19, 7) or bit(rec, 19, 8)):
        return 0
    if code == "tr2 " and (not bit(rec, 37, 8) or bit(rec, 37, 7)):
        return 0
    if quest:
        obj = quest - 1
        if obj == 9:
            if code != "box " and bit(rec, 10, 0):
                return 0
        elif obj == 4:
            if code != "leg " and bit(rec, 4, 0):
                return 0
        elif quest in PAIRS and bit(rec, PAIRS[quest], 0):
            return 0
    if any(ihd):
        return 0
    return 1


def check(excel, logs):
    codes = item_codes(excel)
    mq = misc_quest(excel)
    tot = {"chest": 0, "chest_bad": 0, "object": 0, "object_bad": 0, "event7": 0, "event7_bad": 0, "dup": 0,
           "dup_bad": 0, "gate": 0, "gate_bad": 0, "gate_skip": 0, "gold": 0}
    for path in logs:
        lines = []
        for ln in open(path, errors="replace"):
            t, _, j = ln.partition(" ")
            if t in ("QOW", "QDI", "QDX", "OCD", "QGS", "QDC", "QOE", "QOT", "PFI", "PFX", "PSX", "IQG", "IQX", "IHD",
                     "QGV", "QGX", "ORF", "OSP", "QS"):
                try:
                    lines.append((t, json.loads(j)))
                except ValueError:
                    pass
        name = os.path.basename(path)
        # ---- chests and objects: the lines from a QOW to the next QOW
        for i, (t, d) in enumerate(lines):
            if t != "QOW":
                continue
            j = i + 1
            seg = []
            while j < len(lines) and lines[j][0] != "QOW":
                seg.append(lines[j])
                j += 1
            cls = d["cls"]
            if cls in CHESTS:
                tot["chest"] += 1
                code, q, lo, hi, kind, ident = CHESTS[cls]

                def inside(x):
                    return lo <= int(x["ret"], 16) < hi

                mine = [(tt, x) for tt, x in seg if tt in ("QDI", "OCD", "QGS", "QDC") and inside(x)]
                pfx = []
                for a, (tt, x) in enumerate(seg):
                    # the gate callbacks' PlayerFindItemByCode calls (returns inside 0x005997xx / 0x005B87xx-0x005B88xx)
                    if tt == "PFI":
                        r = int(x["ret"], 16)
                        if 0x00599700 <= r < 0x005997F0 or 0x005B8700 <= r < 0x005B8860 or lo <= r < hi:
                            ans = next((y for tt2, y in seg[a + 1:] if tt2 == "PFX"), None)
                            pfx.append((x["code"], bool(ans and ans["item"])))
                rec = d["rec"]
                if d["mode"] != 0:
                    exp = []
                else:
                    if cls == 355:
                        ok = not bit(rec, 10, 0) and not bit(rec, 10, 3)
                    elif cls == 356:
                        ok = not bit(rec, 10, 0) and not any(h for _, h in pfx)
                    elif cls == 149:
                        ok = None
                    else:
                        ok = not any(h for _, h in pfx)
                    qgs = next((x for tt, x in mine if tt == "QGS"), None)
                    k = k_gold(qgs["qs"]) if qgs else None
                    n = 1 if ok else 0
                    items = [("QDI", code, q)] * n
                    gold = [("QGS",)] + [("QDC", "gld ", 2)] * (k or 0)
                    exp = items + [("OCD",)] + gold if kind == "e1" else gold + items + [("OCD",)]
                got = []
                for tt, x in mine:
                    if tt == "QDI":
                        got.append(("QDI", x["code"], x["q"]))
                    elif tt == "QDC":
                        got.append(("QDC", x["code"], x["q"]))
                    else:
                        got.append((tt,))
                bad = got != exp
                if not bad and ident and d["mode"] == 0 and exp and exp[0][0] == "QDI":
                    oc = next(x for tt, x in mine if tt == "OCD")
                    bad = not (int(oc["last"]["fl"], 16) & 0x10)
                tot["chest_bad"] += bad
                tot["gold"] += sum(1 for g in got if g[0] == "QDC")
                print("%s chest %d %s mode %d pfi %s: got %s %s" % (
                    "MISMATCH" if bad else "ok", cls, code.strip(), d["mode"], pfx,
                    " ".join(g[0] + ("" if len(g) == 1 else ":" + g[1].strip()) for g in got) or "-",
                    ("expected %s" % exp) if bad else "") + " [%s]" % name)
            elif cls in OBJECTS:
                tot["object"] += 1
                code, ret = OBJECTS[cls]
                qdi = [x for tt, x in seg if tt == "QDI" and (ret is None or int(x["ret"], 16) == ret)
                       and x["code"] == code]
                if cls == 268:
                    exp = 1 if d["mode"] == 0 else 0
                elif cls == 30:
                    pf = [(x["code"], next((y for tt2, y in seg[a + 1:] if tt2 == "PFX"), {}).get("item"))
                          for a, (tt, x) in enumerate(seg) if tt == "PFI" and 0x00593B00 <= int(x["ret"], 16) < 0x00593C00]
                    exp = 1 if (d["mode"] == 0 and not bit(d["rec"], 4, 0) and not bit(d["rec"], 4, 1)
                                and not any(h for _, h in pf)) else 0
                elif cls == 108:      # the Malus: word 3 bits 0, 1 clear, clvl >= 8 (every save here is clvl 80)
                    exp = 1 if (d["mode"] == 0 and not bit(d["rec"], 3, 0) and not bit(d["rec"], 3, 1)) else 0
                elif cls == 193:      # the Lam Esen tome: word 17 bit 0 clear
                    exp = 1 if (d["mode"] == 0 and not bit(d["rec"], 17, 0)) else 0
                else:
                    exp = None
                bad = exp is not None and len(qdi) != exp
                tot["object_bad"] += bad
                print("%s object %d %s mode %d: %d creation(s) %s [%s]" % (
                    "MISMATCH" if bad else ("ok" if exp is not None else "seen"), cls, code.strip(), d["mode"],
                    len(qdi), [(x["ret"], x["q"]) for x in qdi], name))
        # ---- object event 7
        for i, (t, d) in enumerate(lines):
            if t != "QOE":
                continue
            tot["event7"] += 1
            nxt = next((x for tt, x in lines[i + 1:i + 40] if tt == "QOT"), None)
            want = EVENT7.get(d["cls"])
            bad = (d["ev"] != 7 or d["ret"] != "00586b1b" or want is None or nxt is None
                   or int(nxt["fn"], 16) != want or not QOE_LO <= int(nxt["ret"], 16) < QOE_HI)
            tot["event7_bad"] += bad
            print("%s event7 cls %d ev %d ret %s r1 %s target %s [%s]" % (
                "MISMATCH" if bad else "ok", d["cls"], d["ev"], d["ret"], d["r1"], nxt and nxt["fn"], name))
        # ---- duplicates: the stat-356 comparison of PlayerFindItemByCode
        for i, (t, d) in enumerate(lines):
            if t != "PSX":
                continue
            ans = next((x for tt, x in lines[i + 1:i + 12] if tt == "PFX"), None)
            pfi = next((x for tt, x in reversed(lines[max(0, i - 12):i]) if tt == "PFI"), None)
            if ans is None or pfi is None:
                continue
            tot["dup"] += 1
            held = bool(ans["item"])
            # past the stat test the walk returns this item (s356 >= diff) or goes on (a later item may still match)
            bad = (d["s356"] >= d["diff"]) and not held
            tot["dup_bad"] += bad
            if bad or d["s356"] < d["diff"]:
                print("%s dup %s s356 %d diff %d -> %s [%s]" % ("MISMATCH" if bad else "ok", pfi["code"].strip(),
                                                               d["s356"], d["diff"], "held" if held else "none", name))
        # ---- the item-move gate
        for i, (t, d) in enumerate(lines):
            if t != "IQG":
                continue
            res = next((x for tt, x in lines[i + 1:i + 30] if tt == "IQX"), None)
            ihd = []
            for tt, x in lines[i + 1:i + 30]:
                if tt == "IHD":
                    ihd.append(x["r"])
                if tt == "IQX":
                    break
            it = d["item"]
            cls = it["u"][1]
            code = codes[cls] if 0 <= cls < len(codes) else "?"
            quest = mq.get(code, (0, 0))[0]
            if it.get("q") == 7:
                tot["gate_skip"] += 1
                print("seen gate %s (unique) -> %s [%s]" % (code.strip(), res and res["r"], name))
                continue
            m = gate_model(code, it.get("q"), d["rec"], quest, ihd)
            tot["gate"] += 1
            bad = res is None or m != (1 if res["r"] else 0)
            tot["gate_bad"] += bad
            print("%s gate %s quest %d site %s -> %s (model %s) ihd %s [%s]" % (
                "MISMATCH" if bad else "ok", code.strip(), quest, d["ret"], res and res["r"], m, ihd, name))
    bad = sum(v for k, v in tot.items() if k.endswith("_bad"))
    print("SUMMARY " + " ".join("%s=%d" % kv for kv in tot.items()) + " mismatches=%d" % bad)
    return 1 if bad else 0


def main(argv):
    if len(argv) < 3 or argv[0] != "check":
        print(__doc__)
        return 2
    return check(argv[1], argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
