"""Dry checks of harness session tables (plan 0047 Phase 1): no game, no slot, nothing written outside a temporary
directory. Used by tools/combat_sessions.py, tools/stats_sessions.py and tools/quest_sessions.py `check`.

For a session it checks that
  * the save has a recipe in tools/d2s_recipes/ (the recipe whose "name" is the save) and a base save in
    tools/test_d2s.py RECIPE_BASES, and that tools/d2s.py build makes it (the sha256 is printed and compared with the
    pinned one when RECIPE_BASES pins it);
  * the difficulty steps file tools/gdb/<steps>.steps exists;
  * every tools/d2pilot.py command is one of its sub-commands and every --option it passes is one d2pilot.py defines
    (read from its argparse calls, not by running it);
and it prints the staged stats a case needs: per stat id, the sum over the equipped items' property lists of the built
save (the values as the save stores them), and the recipe's skill levels. Stdlib only.
"""
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import d2s  # noqa: E402

RECIPES = os.path.join(HERE, "d2s_recipes")
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
_PILOT = None


def recipe_for(save):
    """The recipe file (basename without .json) whose "name" is the save."""
    for f in sorted(os.listdir(RECIPES)):
        if f.endswith(".json"):
            with open(os.path.join(RECIPES, f)) as fh:
                if json.load(fh).get("name") == save:
                    return f[:-5]
    return None


def pilot_spec():
    """(sub-commands, options) of tools/d2pilot.py, from its source."""
    global _PILOT
    if _PILOT is None:
        src = open(os.path.join(HERE, "d2pilot.py")).read()
        m = re.search(r'ap\.add_argument\("cmd", choices=\(([^)]*)\)', src)
        cmds = set(re.findall(r'"([a-z]+)"', m.group(1))) if m else set()
        opts = set(re.findall(r'ap\.add_argument\((?:"-\w", )?"(--[a-z0-9-]+)"', src))
        _PILOT = (cmds, opts)
    return _PILOT


def pilot_ok(args):
    """None if args (a d2pilot.py command line without the log and --slot) parses, else the reason."""
    cmds, opts = pilot_spec()
    if not args or args[0] not in cmds:
        return "unknown d2pilot command %r" % (args[0] if args else None)
    for a in args[1:]:
        if a.startswith("--") and a.split("=")[0] not in opts:
            return "unknown d2pilot option %s" % a
    return None


def build(save, tmp):
    """Build the save's recipe on its base into tmp; returns (recipe, path, sha256, pinned sha256 or None, error)."""
    import test_d2s
    rec = recipe_for(save)
    if rec is None:
        return None, None, None, None, "no recipe names %s" % save
    if rec not in test_d2s.RECIPE_BASES:
        return rec, None, None, None, "recipe %s has no base in tools/test_d2s.py RECIPE_BASES" % rec
    base, pinned = test_d2s.RECIPE_BASES[rec]
    if not os.path.exists(base):
        return rec, None, None, pinned, "base save %s missing" % base
    out = os.path.join(tmp, save + ".d2s")
    so = sys.stdout
    try:
        sys.stdout = open(os.devnull, "w")
        d2s.build(EXCEL, os.path.join(RECIPES, rec + ".json"), base, out)
    except (Exception, SystemExit) as e:      # the builder refuses with an error or an exit
        return rec, None, None, pinned, "build refused: %s" % e
    finally:
        sys.stdout.close()
        sys.stdout = so
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    return rec, out, h, pinned, None


def equipped_stats(path, ids):
    """{stat id: sum of the first value over the equipped items' main property lists} of a built save."""
    isc, kinds = d2s.load_isc(EXCEL), d2s.load_kinds(EXCEL)
    f = d2s.parse(open(path, "rb").read(), isc, kinds)
    out = {i: 0 for i in ids}
    for it in f["items"]["items"]:
        if it.get("location") != 1:
            continue
        for sid, param, vals in it.get("props", []):
            if sid in out:
                out[sid] += vals[0]
    return out


def check_session(name, save, steps, pilots, stat_ids=(), skills=(), tmp=None):
    """Print one session's dry check; returns the number of problems."""
    bad = []
    if save is None:
        rec = h = None
        line = "%s: no save (a new character)" % name
    else:
        rec, path, h, pinned, err = build(save, tmp)
        if err:
            bad.append(err)
        elif pinned and pinned != h:
            bad.append("built %s, pinned %s" % (h[:16], pinned[:16]))
        line = "%s: save %s (recipe %s) sha256 %s%s" % (name, save, rec, (h or "-")[:16],
                                                         " = pinned" if h and pinned == h else "")
        if not err and stat_ids:
            st = equipped_stats(path, stat_ids)
            line += "; equipped " + " ".join("%d=%d" % kv for kv in sorted(st.items()))
        if not err and skills:
            r = json.load(open(os.path.join(RECIPES, rec + ".json")))
            line += "; skills " + ", ".join("%s %s" % (s, r.get("skills", {}).get(s, 0)) for s in skills)
    if steps and not os.path.exists(os.path.join(HERE, "gdb", steps + ".steps")):
        bad.append("no steps file tools/gdb/%s.steps" % steps)
    for p in pilots:
        why = pilot_ok(p)
        if why:
            bad.append("%s: %s" % (" ".join(p[:2]), why))
    print(line + ("" if not bad else "\n  PROBLEM " + "\n  PROBLEM ".join(bad)))
    return len(bad)


def run(cases, unstaged, sessions_of, summary_tag):
    """cases: {case: (text, [session names], stat ids, skills)}; unstaged: {case: reason};
    sessions_of(name) -> (save, steps, [pilot arg lists]). Prints every case and session; returns the exit code."""
    probs = 0
    with tempfile.TemporaryDirectory() as tmp:
        for case, (text, names, ids, skills) in cases.items():
            print("CASE %s: %s" % (case, text))
            for n in names:
                save, steps, pilots = sessions_of(n)
                probs += check_session("  " + n, save, steps, pilots, ids, skills, tmp)
        for case, reason in unstaged.items():
            print("CASE %s: NOT STAGED: %s" % (case, reason))
    n_sess = sum(len(v[1]) for v in cases.values())
    print("SUMMARY %s cases_staged=%d cases_unstaged=%d sessions=%d problems=%d" % (
        summary_tag, len(cases), len(unstaged), n_sess, probs))
    return 0 if not probs else 1
