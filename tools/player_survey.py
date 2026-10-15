"""Survey of CharStats, Experience and CharTemplate (plan 0034 Phase 0).

Usage:
  python3 -I tools/player_survey.py start     <excel-dir> [class]
  python3 -I tools/player_survey.py xp        <excel-dir>
  python3 -I tools/player_survey.py templates <excel-dir>
  python3 -I tools/player_survey.py summary   <excel-dir>

start      each class's start block as charstats.bin holds it (optionally one class, by name or record index):
           base attributes, stamina, hpadd, the per-level and per-attribute columns, ToHitFactor, BlockFactor,
           velocities, StatPerLevel, the five string keys with their text, the item slots in order (code, item
           name, body location, count), StartSkill and Skill 1..10 with their skills rows.
xp         experience.bin: the MaxLvl record per class, then every record with its .txt Level label, the value
           (one column when the seven class columns agree), the step from the previous record, and the ExpRatio
           runs (Level label ranges with the same ratio).
templates  chartemplate.bin: one line per record (Name, Class, Level, Act, attributes, Hitpoints, Mana, skills
           with levels, items).
summary    counts only.

Every command ends with `SURVEY player key=value ...`; tools/gate.py --full compares the summary line with its
baseline. Records are read from the .bin files with the layouts of tools/excel_layouts.py (what the game loads);
names come from the .txt key columns and the string tables next to the excel directory (tools/tbl.py).
Definitions (data only, docs/tables/Experience.md): experience record 0 is the MaxLvl row; record L + 1 is the
.txt row labelled L. Stdlib only. Read-only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
import excel_layouts as L  # noqa: E402

CLASSES = ["Amazon", "Sorceress", "Necromancer", "Paladin", "Barbarian", "Druid", "Assassin"]


def decode(excel_dir, table):
    _, _, recs, _ = eb.load_table(excel_dir, table)
    fields = [f for f in L.LAYOUTS[table]["fields"] if "col" in f]
    return [{f["col"]: eb.decode_field(b, f) for f in fields} for b in recs]


class Data:
    def __init__(self, excel_dir):
        self.cs = decode(excel_dir, "charstats")
        self.xp = decode(excel_dir, "experience")
        self.ct = decode(excel_dir, "chartemplate")
        refs = eb.Refs(excel_dir)
        self.skills = refs.column("skills", "skill")
        self.bodylocs = refs.column("bodylocs", "Code")
        self.pclass = refs.column("playerclass", "Code")
        self.strings = refs.strings()
        self.items = {}
        for t in ("weapons", "armor", "misc"):
            for c, n in zip(refs.column(t, "code"), refs.column(t, "name")):
                self.items.setdefault(c, n)

    def skill(self, i):
        return self.skills[i] if 0 <= i < len(self.skills) else "-"

    def slots(self, r, n):
        out = []
        for k in range(1, n + 1):
            code = r["item%d" % k]
            if code in ("", "0"):
                continue
            out.append((code, self.items.get(code), r["item%dloc" % k], r["item%dcount" % k]))
        return out


def cs_skills(r):
    return [r["Skill %d" % k] for k in range(1, 11)]


def cmd_start(d, argv):
    want = argv[0] if argv else None
    for i, r in enumerate(d.cs):
        if want is not None and want not in (str(i), r["class"]):
            continue
        print("record %d  %s" % (i, r["class"]))
        print("  attributes  str %d dex %d int %d vit %d  stamina %d  hpadd %d" % tuple(
            r[c] for c in ("str", "dex", "int", "vit", "stamina", "hpadd")))
        print("  percent     str %d int %d dex %d vit %d  ManaRegen %d" % tuple(
            r[c] for c in ("PercentStr", "PercentInt", "PercentDex", "PercentVit", "ManaRegen")))
        print("  per level   life %d stamina %d mana %d  StatPerLevel %d" % tuple(
            r[c] for c in ("LifePerLevel", "StaminaPerLevel", "ManaPerLevel", "StatPerLevel")))
        print("  per point   life/vit %d stamina/vit %d mana/energy %d" % tuple(
            r[c] for c in ("LifePerVitality", "StaminaPerVitality", "ManaPerMagic")))
        print("  combat      ToHitFactor %d BlockFactor %d  walk %d run %d RunDrain %d  baseWClass %s" % tuple(
            r[c] for c in ("ToHitFactor", "BlockFactor", "WalkVelocity", "RunVelocity", "RunDrain", "baseWClass")))
        for c in ("StrAllSkills", "StrSkillTab1", "StrSkillTab2", "StrSkillTab3", "StrClassOnly"):
            print("  %-13s %5d  %r" % (c, r[c], d.strings.text(r[c])))
        for k, (code, name, loc, cnt) in enumerate(d.slots(r, 10)):
            print("  item        %-4s %-22s loc %d (%s) count %d" % (code, name, loc, d.bodylocs[loc] or "-", cnt))
        ss = r["StartSkill"]
        print("  StartSkill  %s" % ("-" if ss == 0xFFFF else "%d %s" % (ss, d.skill(ss))))
        print("  Skill 1..10 %s" % ", ".join("%d %s" % (s, d.skill(s)) for s in cs_skills(r) if s != 0xFFFF))
    print(summary_line(d))


def cmd_xp(d, argv):
    cap = d.xp[0]
    print("MaxLvl  " + "  ".join("%s %d" % (c[:3], cap[c]) for c in CLASSES) + "  ExpRatio %d" % cap["ExpRatio"])
    prev = None
    for lvl, r in enumerate(d.xp[1:]):
        vals = [r[c] for c in CLASSES]
        thr = str(vals[0]) if len(set(vals)) == 1 else "/".join(map(str, vals))
        step = "" if prev is None else "  +%d" % (vals[0] - prev)
        print("record %3d  Level %3d  %12s%s  ExpRatio %d" % (lvl + 1, lvl, thr, step, r["ExpRatio"]))
        prev = vals[0]
    print("ExpRatio runs: " + ", ".join("%d..%d=%d" % run for run in ratio_runs(d)))
    print(summary_line(d))


def ratio_runs(d):
    runs = []
    for lvl, r in enumerate(d.xp[1:]):
        if runs and runs[-1][2] == r["ExpRatio"]:
            runs[-1] = (runs[-1][0], lvl, r["ExpRatio"])
        else:
            runs.append((lvl, lvl, r["ExpRatio"]))
    return runs


def cmd_templates(d, argv):
    for i, r in enumerate(d.ct):
        sk = ["%d %s L%d" % (r["Skill%d" % k], d.skill(r["Skill%d" % k]), r["SkillLevel%d" % k])
              for k in range(1, 10) if r["Skill%d" % k] or r["SkillLevel%d" % k]]
        it = ["%s@%d x%d" % (c, loc, n) for c, _, loc, n in d.slots(r, 15)]
        print("record %2d  %-9s %s L%d act %d  str %d dex %d int %d vit %d  hp %d mana %d  [%s]  {%s}" % (
            i, r["Name"], d.pclass[r["Class"]], r["Level"], r["Act"], r["str"], r["dex"], r["int"], r["vit"],
            r["Hitpoints"], r["Mana"], "; ".join(sk), " ".join(it)))
    print(summary_line(d))


def summary_line(d):
    cs, xp, ct = d.cs, d.xp, d.ct
    levels = xp[1:]
    same = sum(1 for r in levels if len({r[c] for c in CLASSES}) == 1)
    mono = all(levels[k][c] < levels[k + 1][c] for k in range(len(levels) - 1) for c in CLASSES)
    caps = sorted({xp[0][c] for c in CLASSES})
    slots = [len(d.slots(r, 10)) for r in cs]
    unknown_items = sum(1 for r in cs for s in d.slots(r, 10) if s[1] is None)
    unknown_items += sum(1 for r in ct for s in d.slots(r, 15) if s[1] is None)
    startskill = sum(1 for r in cs if r["StartSkill"] != 0xFFFF)
    cs_sk = sum(1 for r in cs for s in cs_skills(r) if s != 0xFFFF)
    ct_sk = sum(1 for r in ct for k in range(1, 10) if r["Skill%d" % k])
    kv = [("classes", len(cs)), ("item_slots", sum(slots)), ("item_slots_max", max(slots)),
          ("item_unresolved", unknown_items), ("startskill_set", startskill), ("class_skill_cells", cs_sk),
          ("xp_records", len(xp)), ("xp_levels", len(levels)), ("xp_class_cols_equal", same),
          ("xp_strictly_increasing", int(mono)), ("xp_cap_min", caps[0]), ("xp_cap_max", caps[-1]),
          ("xp_max", levels[-1]["Amazon"]), ("exp_ratio_runs", len(ratio_runs(d))),
          ("templates", len(ct)), ("template_level_min", min(r["Level"] for r in ct)), ("template_level_max", max(r["Level"] for r in ct)),
          ("template_skill_cells", ct_sk), ("template_item_slots", sum(len(d.slots(r, 15)) for r in ct))]
    return "SURVEY player " + " ".join("%s=%s" % p for p in kv)


def main(argv):
    if len(argv) < 2 or argv[0] not in ("start", "xp", "templates", "summary"):
        print(__doc__)
        return 2
    d = Data(argv[1])
    if argv[0] == "start":
        cmd_start(d, argv[2:])
    elif argv[0] == "xp":
        cmd_xp(d, argv[2:])
    elif argv[0] == "templates":
        cmd_templates(d, argv[2:])
    else:
        print(summary_line(d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
