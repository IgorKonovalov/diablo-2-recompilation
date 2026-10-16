"""Survey of the travel columns of Levels and Objects (plan 0042 Phase 0): waypoints, towns, quest flags, portals.

Usage:
  python3 -I tools/travel_survey.py levels  <excel-dir>
  python3 -I tools/travel_survey.py objects <excel-dir> [--exe <game.exe>]
  python3 -I tools/travel_survey.py summary <excel-dir>

levels   one line per level with a travel cell set (Waypoint != 255, QuestFlag/QuestFlagEx != 0, Portal, Position,
         Teleport != 1, a town), then per act the waypoint indices in index order with their level.
objects  the object classes the travel code is expected to touch: SubClass bit 2 (0x04), bit 4 (0x10) or bit 6
         (0x40), or OperateFn 23 (the waypoint operate) or the OperateFn of a bit-4 row; per row Id, Name, SubClass,
         InitFn, OperateFn, PopulateFn, ClientFn, Parm0..1. With --exe (default workspace/install/app/game.exe when it
         exists), the handler each index selects: the u32 entry of g_ObjInitFns (0x00731BC0) and g_ObjOperateFns
         (0x00732D18) read from the file (docs/tables/Objects.md § Code semantics).
summary  counts only.

Every command ends with `SURVEY travel key=value ...`; tools/gate.py --full compares it with its baseline.
Levels fields are read from levels.bin and leveldefs.bin, Objects from objects.bin, with the layouts of
tools/excel_layouts.py; level names from levels.txt (the marker row dropped). The town list (1, 40, 75, 103, 109) is
the code's (fn:sub_006426A0_LevelIsTown@0x006426A0, drlg/0004), not a column. Stdlib only. Read-only.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
import excel_layouts as L  # noqa: E402

TOWNS = (1, 40, 75, 103, 109)
EXE = os.path.join(os.path.dirname(HERE), "workspace", "install", "app", "game.exe")
G_INIT, G_OPERATE = 0x00731BC0, 0x00732D18
OP_WAYPOINT = 23
LEVEL_COLS = ("Act", "Waypoint", "QuestFlag", "QuestFlagEx", "Portal", "Position", "Teleport", "IsInside", "Quest",
              "SubWaypoint", "DrlgType")
OBJ_COLS = ("SubClass", "InitFn", "OperateFn", "PopulateFn", "ClientFn", "Parm0", "Parm1")


def decode(excel_dir, table, cols):
    _, _, recs, _ = eb.load_table(excel_dir, table)
    fs = {f["col"]: f for f in L.LAYOUTS[table]["fields"] if "col" in f}
    return [{c: eb.decode_field(r, fs[c]) for c in cols if c in fs} for r in recs]


class Data:
    def __init__(self, excel_dir):
        lv = decode(excel_dir, "levels", LEVEL_COLS)
        ld = decode(excel_dir, "leveldefs", LEVEL_COLS)
        self.levels = [dict(a, **b) for a, b in zip(lv, ld)]
        h, rows = eb.read_txt(eb.find_file(excel_dir, "levels", ".txt"))
        names = [dict(zip(h, r)).get("Name", "") for r in rows]
        self.names = [n for n in names if n != "Expansion"]
        self.objects = decode(excel_dir, "objects", OBJ_COLS + ("Name",))

    def wp(self):
        """{waypoint index: level id}"""
        return {L_["Waypoint"]: i for i, L_ in enumerate(self.levels) if L_["Waypoint"] != 255}

    def travel_objects(self):
        portal_ops = {o["OperateFn"] for o in self.objects if o["SubClass"] & 0x10}
        return [(i, o) for i, o in enumerate(self.objects)
                if o["SubClass"] & 0x54 or o["OperateFn"] == OP_WAYPOINT or o["OperateFn"] in portal_ops]


class Exe:
    def __init__(self, path):
        with open(path, "rb") as fh:
            self.b = fh.read()
        pe = struct.unpack_from("<I", self.b, 0x3C)[0]
        n, opt = struct.unpack_from("<H", self.b, pe + 6)[0], struct.unpack_from("<H", self.b, pe + 20)[0]
        self.secs = [struct.unpack_from("<IIII", self.b, pe + 24 + opt + 40 * k + 8) for k in range(n)]

    def u32(self, va):
        rva = va - 0x400000
        for vs, a, rs, ra in self.secs:
            if a <= rva < a + min(vs, rs):
                return struct.unpack_from("<I", self.b, ra + rva - a)[0]
        raise ValueError("0x%08X not in a raw section" % va)


def cmd_levels(d):
    for i, v in enumerate(d.levels):
        if (v["Waypoint"] != 255 or v["QuestFlag"] or v["QuestFlagEx"] or v["Portal"] or v["Position"]
                or v["Teleport"] != 1 or i in TOWNS):
            print("level %3d %-28s act %d wp %3s QuestFlag %2d/%2d Portal %d Position %d Teleport %d IsInside %d "
                  "Quest %2d SubWaypoint %2d DrlgType %d%s" % (
                      i, d.names[i], v["Act"], v["Waypoint"] if v["Waypoint"] != 255 else "-", v["QuestFlag"],
                      v["QuestFlagEx"], v["Portal"], v["Position"], v["Teleport"], v["IsInside"], v["Quest"],
                      v["SubWaypoint"], v["DrlgType"], "  town" if i in TOWNS else ""))
    wp = d.wp()
    for act in range(5):
        idx = sorted(n for n, lv in wp.items() if d.levels[lv]["Act"] == act)
        print("act %d waypoints %d..%d: %s" % (act + 1, idx[0], idx[-1], ", ".join("%d=%d" % (n, wp[n]) for n in idx)))


def cmd_objects(d, exe):
    for i, o in d.travel_objects():
        line = "object %3d %-14s SubClass 0x%02X InitFn %2d OperateFn %2d PopulateFn %d ClientFn %d Parm0 %d Parm1 %d" % (
            i, o["Name"], o["SubClass"], o["InitFn"], o["OperateFn"], o["PopulateFn"], o["ClientFn"], o["Parm0"],
            o["Parm1"])
        if exe:
            line += "  init 0x%08X operate 0x%08X" % (exe.u32(G_INIT + 4 * o["InitFn"]) if o["InitFn"] else 0,
                                                       exe.u32(G_OPERATE + 4 * o["OperateFn"]) if o["OperateFn"] else 0)
        print(line)


def summary_line(d):
    wp = d.wp()
    lv = d.levels
    per_act = [sum(1 for n in wp if lv[wp[n]]["Act"] == a) for a in range(5)]
    # waypoint indices increase with the act: every index of act a is below every index of act a + 1
    ordered = all(max(n for n in wp if lv[wp[n]]["Act"] == a) < min(n for n in wp if lv[wp[n]]["Act"] == a + 1)
                  for a in range(4))
    town_first = all(lv[t]["Waypoint"] == min(n for n in wp if lv[wp[n]]["Act"] == lv[t]["Act"]) for t in TOWNS)
    objs = d.objects
    kv = [("levels", len(lv)),
          ("wp_levels", len(wp)),
          ("wp_cells", sum(1 for v in lv if v["Waypoint"] != 255)),
          ("wp_max", max(wp)),
          ("wp_contiguous", int(sorted(wp) == list(range(len(wp))))),
          ("wp_act_ordered", int(ordered)),
          ("wp_town_first", int(town_first)),
          ] + [("wp_act%d" % (a + 1), per_act[a]) for a in range(5)] + [
          ("wp_outdoor", sum(1 for n in wp if lv[wp[n]]["DrlgType"] == 3)),
          ("wp_maze", sum(1 for n in wp if lv[wp[n]]["DrlgType"] == 1)),
          ("wp_preset", sum(1 for n in wp if lv[wp[n]]["DrlgType"] == 2)),
          ("subwaypoint_levels", sum(1 for v in lv if v["SubWaypoint"] > 0)),
          ("subwaypoint_without_wp", sum(1 for v in lv if v["SubWaypoint"] > 0 and v["Waypoint"] == 255)),
          ("questflag_levels", sum(1 for v in lv if v["QuestFlag"])),
          ("questflag_values", len({v["QuestFlag"] for v in lv if v["QuestFlag"]})),
          ("questflagex_levels", sum(1 for v in lv if v["QuestFlagEx"])),
          ("questflag_ex_differs", sum(1 for v in lv if v["QuestFlag"] != v["QuestFlagEx"])),
          ("portal_levels", sum(1 for v in lv if v["Portal"])),
          ("position_levels", sum(1 for v in lv if v["Position"])),
          ("teleport_not1", sum(1 for v in lv if v["Teleport"] != 1)),
          ("towns_position", sum(1 for t in TOWNS if lv[t]["Position"])),
          ("towns_portal", sum(1 for t in TOWNS if lv[t]["Portal"])),
          ("obj_subclass_bit2", sum(1 for o in objs if o["SubClass"] & 0x04)),
          ("obj_subclass_bit4", sum(1 for o in objs if o["SubClass"] & 0x10)),
          ("obj_subclass_bit6", sum(1 for o in objs if o["SubClass"] & 0x40)),
          ("obj_op_waypoint", sum(1 for o in objs if o["OperateFn"] == OP_WAYPOINT)),
          ("obj_bit6_op_waypoint", sum(1 for o in objs if o["SubClass"] & 0x40 and o["OperateFn"] == OP_WAYPOINT)),
          ("obj_travel_rows", len(d.travel_objects()))]
    return "SURVEY travel " + " ".join("%s=%s" % p for p in kv)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2 or args[0] not in ("levels", "objects", "summary"):
        print(__doc__)
        return 2
    exe_path = EXE
    if "--exe" in argv:
        k = argv.index("--exe")
        exe_path = argv[k + 1]
        args = [a for a in args if a != exe_path]
    d = Data(args[1])
    if args[0] == "levels":
        cmd_levels(d)
    elif args[0] == "objects":
        cmd_objects(d, Exe(exe_path) if os.path.exists(exe_path) else None)
    print(summary_line(d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
