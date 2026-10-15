"""Survey of the vendor columns of the item tables, Npc and Gamble (plan 0031 Phase 0).

Usage:
  python3 -I tools/vendor_survey.py bases   <excel-dir> <vendor> [normal|nightmare|hell]
  python3 -I tools/vendor_survey.py gamble  <excel-dir> [normal|nightmare|hell]
  python3 -I tools/vendor_survey.py npc     <excel-dir>
  python3 -I tools/vendor_survey.py summary <excel-dir>

bases    one line per item record whose <Vendor>Min, Max, MagicMin or MagicMax byte is non-zero: the record index in
         the combined item list (weapons, armor, misc), table, code, name, type, level (qlvl), version, the five
         vendor bytes, PermStoreItem, multibuy, and for nightmare / hell the NightmareUpgrade / HellUpgrade cell with
         the item it names ('xxx' names none). <vendor> is a vendor column group (Akara ... Drehya) or an npc.txt name
         (hratli is the Hralti group; nihlathak prints Larzuk's list with a note); case does not matter.
gamble   one line per gamble.txt record: code, the item it names, table, type, level, version, and the upgrade cell
         for the difficulty.
npc      one line per npc.txt record: the monstats row it names and the item vendor column group of the same name.
summary  counts only.

Every command ends with the line `SURVEY vendors key=value ...`; tools/gate.py --full compares the summary one with its
baseline. The vendor bytes are read from the item .bin records with the item layout of tools/excel_layouts.py (the
game loads the .bin: the dead HratliMagicLvl header of weapons/armor shows as 0 here, docs/tables/Weapons.md).
"Can stock" above is a data definition only (some vendor byte non-zero); what the game does with the bytes and with
the upgrade columns is not claimed (docs/tables/Weapons.md § Vendor columns). Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
import excel_layouts as L  # noqa: E402

DIFFS = ["normal", "nightmare", "hell"]
UPGRADE = [None, "NightmareUpgrade", "HellUpgrade"]
PARTS = ["Min", "Max", "MagicMin", "MagicMax", "MagicLvl"]
NPC_ALIAS = {"hratli": "Hralti"}   # npc.txt spelling -> item column group


class Data:
    def __init__(self, excel_dir):
        fields = {f["col"]: f for f in L.ITEM_FIELDS if "col" in f}
        self.items = []          # dicts, combined item list order
        self.by_code = {}
        for t in ("weapons", "armor", "misc"):
            header, rows, recs, _ = eb.load_table(excel_dir, t)
            ni = header.index("name")
            for row, rec in zip(rows, recs):
                it = {"table": t, "name": row[ni].strip(), "index": len(self.items)}
                for col in ["code", "type", "level", "version", "PermStoreItem", "multibuy",
                            "NightmareUpgrade", "HellUpgrade"] + [v + p for v in L.VENDORS for p in PARTS]:
                    it[col] = eb.decode_field(rec, fields[col])
                self.items.append(it)
                self.by_code.setdefault(it["code"], it)
        self.types = eb.Refs(excel_dir).column("itemtypes", "Code")
        for it in self.items:
            it["type"] = self.types[it["type"]] if 0 <= it["type"] < len(self.types) else "?"
        header, rows, recs, _ = eb.load_table(excel_dir, "npc")
        self.monstats = eb.Refs(excel_dir).column("monstats", "Id")
        npc_f = L.LAYOUTS["npc"]["fields"][0]
        self.npcs = [(row[0], eb.decode_field(rec, npc_f)) for row, rec in zip(rows, recs)]
        header, rows, recs, _ = eb.load_table(excel_dir, "gamble")
        self.gamble = [eb.decode_field(rec, L.LAYOUTS["gamble"]["fields"][0]) for rec in recs]

    def stocks(self, vendor):
        return [it for it in self.items if any(it[vendor + p] for p in PARTS[:4])]

    def upgrade(self, it, d):
        if d == 0:
            return None, None
        cell = it[UPGRADE[d]]
        return cell, self.by_code.get(cell)


def vendor_group(name):
    low = name.lower()
    low = NPC_ALIAS.get(low, low).lower()
    for v in L.VENDORS:
        if v.lower() == low:
            return v
    return None


def diff_arg(argv, i):
    d = argv[i].lower() if len(argv) > i else "normal"
    if d not in DIFFS:
        raise SystemExit("difficulty must be one of %s" % ", ".join(DIFFS))
    return DIFFS.index(d)


def up_text(data, it, d):
    cell, tgt = data.upgrade(it, d)
    if cell is None:
        return ""
    return "%s=%s(%s)" % (UPGRADE[d], cell, tgt["name"] if tgt else "-")


def cmd_bases(data, vendor, d):
    v = vendor_group(vendor)
    if v is None and vendor.lower() == "nihlathak":
        # items/0009 § Answer: class 514's store record takes list 15 (Larzuk); he is not in the trade menu, so the
        # list is never shown (he only gambles).
        v = "Larzuk"
        print("# nihlathak has no column group; his store record takes Larzuk's list, never shown (items/0009)")
    if v is None:
        raise SystemExit("no vendor column group for %r (groups: %s)" % (vendor, ", ".join(L.VENDORS)))
    rows = data.stocks(v)
    print("# %s, %s: %d item records with a non-zero %sMin/Max/MagicMin/MagicMax byte" % (v, DIFFS[d], len(rows), v))
    print("# index table code name | type level version | Min Max MagicMin MagicMax MagicLvl | Perm multibuy | upgrade")
    n_up = 0
    for it in rows:
        up = up_text(data, it, d)
        n_up += bool(up) and data.upgrade(it, d)[1] is not None
        print("%4d %-7s %-4s %-28s | %-4s %3d %3d | %d %d %d %d %3d | %d %d | %s" % (
            it["index"], it["table"], it["code"], it["name"][:28], it["type"], it["level"], it["version"],
            *[it[v + p] for p in PARTS], it["PermStoreItem"], it["multibuy"], up))
    by_t = collections.Counter(it["table"] for it in rows)
    print("SURVEY vendors vendor_bases=%d weapons=%d armor=%d misc=%d magic=%d upgraded=%d" % (
        len(rows), by_t["weapons"], by_t["armor"], by_t["misc"],
        sum(1 for it in rows if it[v + "MagicMin"] or it[v + "MagicMax"]), n_up))
    return 0


def cmd_gamble(data, d):
    missing = 0
    for code in data.gamble:
        it = data.by_code.get(code)
        if it is None:
            missing += 1
            print("%-4s (no item)" % code)
            continue
        print("%-4s %-28s %-7s %-4s %3d %3d %s" % (code, it["name"][:28], it["table"], it["type"], it["level"],
                                                  it["version"], up_text(data, it, d)))
    print("SURVEY vendors gamble_rows=%d unresolved=%d" % (len(data.gamble), missing))
    return 0


def cmd_npc(data):
    for name, mid in data.npcs:
        mon = data.monstats[mid] if 0 <= mid < len(data.monstats) else "-"
        print("%-10s monstats %3d %-10s group %s" % (name, mid, mon, vendor_group(name) or "-"))
    print("SURVEY vendors npc_rows=%d with_group=%d" % (len(data.npcs),
                                                      sum(1 for n, _ in data.npcs if vendor_group(n))))
    return 0


def cmd_summary(data):
    kv = collections.OrderedDict()
    npc_groups = {vendor_group(n) for n, _ in data.npcs}
    kv["npc_rows"] = len(data.npcs)
    kv["npc_with_group"] = sum(1 for n, _ in data.npcs if vendor_group(n))
    kv["npc_monstats_bad"] = sum(1 for n, mid in data.npcs
                                 if not (0 <= mid < len(data.monstats)) or data.monstats[mid].lower() != n.lower())
    kv["groups"] = len(L.VENDORS)
    kv["groups_without_npc"] = sum(1 for v in L.VENDORS if v not in npc_groups)
    kv["perm"] = sum(1 for it in data.items if it["PermStoreItem"])
    kv["multibuy"] = sum(1 for it in data.items if it["multibuy"])
    kv["multibuy_not_perm"] = sum(1 for it in data.items if it["multibuy"] and not it["PermStoreItem"])
    for d in (1, 2):
        cells = [it[UPGRADE[d]] for it in data.items]
        kv["%s_set" % DIFFS[d]] = sum(1 for c in cells if c and c != "xxx")
        kv["%s_unresolved" % DIFFS[d]] = sum(1 for c in cells if c and c != "xxx" and c not in data.by_code)
    kv["min_gt_max"] = 0
    for v in L.VENDORS:
        rows = data.stocks(v)
        kv["min_gt_max"] += sum(1 for it in rows if it[v + "Min"] > it[v + "Max"] or
                                it[v + "MagicMin"] > it[v + "MagicMax"])
        kv["%s_bases" % v.lower()] = len(rows)
        kv["%s_magic" % v.lower()] = sum(1 for it in rows if it[v + "MagicMin"] or it[v + "MagicMax"])
        kv["%s_lvl0" % v.lower()] = sum(1 for it in rows if it[v + "MagicLvl"] == 0)
        for d in (1, 2):
            kv["%s_up%d" % (v.lower(), d)] = sum(1 for it in rows if data.upgrade(it, d)[1] is not None)
    kv["gamble_rows"] = len(data.gamble)
    kv["gamble_unresolved"] = sum(1 for c in data.gamble if c not in data.by_code)
    for d in (1, 2):
        kv["gamble_up%d" % d] = sum(1 for c in data.gamble
                                    if c in data.by_code and data.upgrade(data.by_code[c], d)[1] is not None)
    for k, v in kv.items():
        if not k.startswith(tuple(x.lower() + "_" for x in L.VENDORS)):
            print("%-22s %d" % (k, v))
    print("# per vendor group: bases magic lvl0 up_nightmare up_hell")
    for v in L.VENDORS:
        lv = v.lower()
        print("  %-9s %3d %3d %3d %3d %3d" % (v, kv[lv + "_bases"], kv[lv + "_magic"], kv[lv + "_lvl0"],
                                             kv[lv + "_up1"], kv[lv + "_up2"]))
    print("SURVEY vendors " + " ".join("%s=%d" % kv_ for kv_ in kv.items()))
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, data = argv[0], Data(argv[1])
    if cmd == "bases" and len(argv) >= 3:
        return cmd_bases(data, argv[2], diff_arg(argv, 3))
    if cmd == "gamble":
        return cmd_gamble(data, diff_arg(argv, 2))
    if cmd == "npc":
        return cmd_npc(data)
    if cmd == "summary":
        return cmd_summary(data)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
