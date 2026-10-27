"""Plan 0050 Phase 1b part 1: the community breakpoint formulas against the community breakpoint
tables, no game data and no game code (both sides are the sources' own claims; staged in
docs/findings/anim/leads.md).

For each (class or form, kind) the formula of src:maxroll-d2r-breakpoints is evaluated for every
percentage 0..700 and its frame thresholds compared with the table of src:maxroll-d2r-breakpoints and
of src:pd-breakpoints, up to each table's last row. A table the formula does not reproduce is then
searched for the base (10..21) that does. Prints one DIFF/ALT line per mismatch, the formula's
thresholds per case, and a last `SUMMARY` line.

Usage: python3 -I tools/anim_leads_check.py
       python3 -I tools/anim_leads_check.py code <merged root> <p50a-anim-scan.txt>

`code` (plan 0050 Phase 1b part 2, the verdicts): the same 39 community tables, and the other numeric
claims of anim/leads, against the code's model of anim/0001 and anim/0002 (tools/anim_rates.py: the
rate bonus, the cast, get-hit and block rates and the schedule loop of SUNIT_ScheduleModeEvents) over
the stock animdata.d2 records the code would look up, and against the stock tables. Sections, one line
each, then `SUMMARY anim_leads_code ...`:
  TAB   per table case: the records the case covers (name, frames, speed), the stat values where the
        code's mode length n changes (from 0 to the table's last row), whether they equal the table's,
        and the set of (table frames - n) over the table's rows
  BASIN per row of the Basin attack table (src:basin-wiki-animation rev 65669, transcribed as numbers):
        the record's frames and speed, the code's start frame (g_AttackStartFrames, anim/0001 § 4), the
        first code-1/2 event frame, each against the row, and the row's cycle against the code's n at factor X = 100
  CAST  per cast record: frames, speed and the first code-1/2 event frame (the cast action frame)
  DELAY Skills `delay` (frames) of every row with a charclass and a delay, against the seconds of D4
  SEQ   the player sequence lengths the A10, A12, A13 and C1 rows name (from the kept P1.1 scan)
  MOVE  CharStats walk/run per class; the shape classes' MonStats Velocity and MonStats2 mRN
  WSM   Weapons `speed` range and the three named bases; the item types whose `wclass` is 1hs
Read-only; game data stays in the workspace (the output prints numbers and record names only).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

def eff(x):
    return x * 120 // (x + 120)

def frames(kind, base, speed, pct, holy=False, lightning=False):
    e = eff(pct)
    if kind == "fcr":
        e = min(e, 75)
        r = speed * (100 + e) // 100
        v = 256 * base / r
        return math.ceil(v) if lightning else math.ceil(v - 1)
    if kind == "fbr" and holy:
        e += 50
    r = speed * (50 + e) // 100
    return math.ceil(256 * base / r - 1)

def thresholds(kind, base, speed, top, **kw):
    out, last = [], None
    for p in range(0, top + 1):
        f = frames(kind, base, speed, p, **kw)
        if f != last:
            out.append((p, f))
            last = f
    return out

# (name, kind, base, speed, kw, maxroll table [(pct, frames)], pd table or None)
CASES = [
    ("Amazon", "fcr", 20, 256, {}, [(0,19),(7,18),(14,17),(22,16),(32,15),(48,14),(68,13),(99,12),(152,11)],
     [(0,19),(7,18),(14,17),(22,16),(32,15),(48,14),(68,13),(99,12),(152,11)]),
    ("Assassin", "fcr", 17, 256, {}, [(0,16),(8,15),(16,14),(27,13),(42,12),(65,11),(102,10),(174,9)],
     [(0,16),(8,15),(16,14),(27,13),(42,12),(65,11),(102,10),(174,9)]),
    ("Barbarian", "fcr", 14, 256, {}, [(0,13),(9,12),(20,11),(37,10),(63,9),(105,8),(200,7)],
     [(0,13),(9,12),(20,11),(37,10),(63,9),(105,8),(200,7)]),
    ("Druid", "fcr", 16, 208, {}, [(0,18),(4,17),(10,16),(19,15),(30,14),(46,13),(68,12),(99,11),(163,10)],
     [(0,18),(4,17),(10,16),(19,15),(30,14),(46,13),(68,12),(99,11),(163,10)]),
    ("Werewolf", "fcr", 16, 229, {}, [(0,16),(6,15),(14,14),(26,13),(40,12),(60,11),(95,10),(157,9)],
     [(0,16),(6,15),(14,14),(26,13),(40,12),(60,11),(95,10),(157,9)]),
    ("Werebear", "fcr", 16, 228, {}, [(0,16),(7,15),(15,14),(26,13),(40,12),(63,11),(99,10),(163,9)],
     [(0,16),(7,15),(15,14),(26,13),(40,12),(63,11),(99,10),(163,9)]),
    ("Necromancer", "fcr", 15, 256, {}, [(0,15),(9,14),(18,13),(30,12),(48,11),(75,10),(125,9)],
     [(0,15),(9,14),(18,13),(30,12),(48,11),(75,10),(125,9)]),
    ("Vampire form", "fcr", 15, 160, {}, [(0,23),(6,22),(11,21),(18,20),(24,19),(35,18),(48,17),(65,16),(86,15),(120,14),(180,13)],
     [(0,23),(6,22),(11,21),(18,20),(24,19),(35,18),(48,17),(65,16),(86,15),(120,14),(180,13)]),
    ("Paladin", "fcr", 16, 256, {}, [(0,15),(9,14),(18,13),(30,12),(48,11),(75,10),(125,9)],
     [(0,15),(9,14),(18,13),(30,12),(48,11),(75,10),(125,9)]),
    ("Sorceress", "fcr", 14, 256, {}, [(0,13),(9,12),(20,11),(37,10),(63,9),(105,8),(200,7)],
     [(0,13),(9,12),(20,11),(37,10),(63,9),(105,8),(200,7)]),
    ("Sorceress Lightning", "fcr", 19, 256, {"lightning": True}, [(0,19),(7,18),(15,17),(23,16),(35,15),(52,14),(78,13),(117,12),(194,11)],
     [(0,19),(7,18),(15,17),(23,16),(35,15),(52,14),(78,13),(117,12),(194,11)]),
    ("Act 3 merc", "fcr", 18, 256, {}, [(0,17),(8,16),(15,15),(26,14),(39,13),(58,12),(86,11),(138,10)],
     [(0,17),(8,16),(15,15),(26,14),(39,13),(58,12),(86,11),(138,10)]),
    ("Amazon", "fhr", 6, 256, {}, [(0,11),(6,10),(13,9),(20,8),(32,7),(52,6),(86,5),(174,4)],
     [(0,11),(6,10),(13,9),(20,8),(32,7),(52,6),(86,5),(174,4),(600,3)]),
    ("Assassin", "fhr", 5, 256, {}, [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)],
     [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)]),
    ("Barbarian", "fhr", 5, 256, {}, [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)],
     [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)]),
    ("Druid 1H swing", "fhr", 7, 248, {}, [(0,14),(3,13),(7,12),(13,11),(19,10),(29,9),(42,8),(63,7),(99,6),(174,5),(456,4)],
     [(0,14),(3,13),(7,12),(13,11),(19,10),(29,9),(42,8),(63,7),(99,6),(174,5),(456,4)]),
    ("Druid other", "fhr", 7, 256, {}, [(0,13),(5,12),(10,11),(16,10),(26,9),(39,8),(56,7),(86,6),(152,5),(377,4)],
     [(0,13),(5,12),(10,11),(16,10),(26,9),(39,8),(56,7),(86,6),(152,5),(377,4)]),
    ("Werewolf", "fhr", 4, 256, {}, [(0,7),(9,6),(20,5),(42,4),(86,3),(280,2)],
     [(0,7),(9,6),(20,5),(42,4),(86,3),(280,2)]),
    ("Werebear", "fhr", 5, 184, {}, [(0,13),(5,12),(10,11),(16,10),(24,9),(37,8),(54,7),(86,6),(152,5),(360,4)],
     [(0,13),(5,12),(10,11),(16,10),(24,9),(37,8),(54,7),(86,6),(152,5),(360,4)]),
    ("Necromancer", "fhr", 7, 256, {}, [(0,13),(5,12),(10,11),(16,10),(26,9),(39,8),(56,7),(86,6),(152,5)],
     [(0,13),(5,12),(10,11),(16,10),(26,9),(39,8),(56,7),(86,6),(152,5),(377,4)]),
    ("Vampire form", "fhr", 4, 136, {}, [(0,15),(2,14),(6,13),(10,12),(16,11),(24,10),(34,9),(48,8),(72,7),(117,6),(208,5)],
     [(0,15),(2,14),(6,13),(10,12),(16,11),(24,10),(34,9),(48,8),(72,7),(117,6)]),
    ("Paladin spear/staff", "fhr", 5, 192, {}, [(0,13),(3,12),(7,11),(13,10),(20,9),(32,8),(48,7),(75,6),(129,5)],
     [(0,13),(3,12),(7,11),(13,10),(20,9),(32,8),(48,7),(75,6),(129,5),(280,4)]),
    ("Paladin other", "fhr", 5, 256, {}, [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)],
     [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)]),
    ("Sorceress", "fhr", 8, 256, {}, [(0,15),(5,14),(9,13),(14,12),(20,11),(30,10),(42,9),(60,8),(86,7),(142,6),(280,5)],
     [(0,15),(5,14),(9,13),(14,12),(20,11),(30,10),(42,9),(60,8),(86,7),(142,6),(280,5)]),
    ("Act 1 merc", "fhr", 6, 256, {}, [(0,11),(6,10),(13,9),(20,8),(32,7),(52,6),(86,5)],
     [(0,11),(6,10),(13,9),(20,8),(32,7),(52,6),(86,5),(174,4),(600,3)]),
    ("Act 2 merc", "fhr", 8, 256, {}, [(0,15),(5,14),(9,13),(14,12),(20,11),(30,10),(42,9),(60,8),(86,7),(142,6)],
     [(0,15),(5,14),(9,13),(14,12),(20,11),(30,10),(42,9),(60,8),(86,7),(142,6),(280,5)]),
    ("Act 3 merc", "fhr", 9, 256, {}, [(0,17),(5,16),(8,15),(13,14),(18,13),(24,12),(32,11),(46,10),(63,9),(86,8),(133,7),(232,6)],
     [(0,17),(5,16),(8,15),(13,14),(18,13),(24,12),(32,11),(46,10),(63,9),(86,8),(133,7),(232,6),(600,5)]),
    ("Act 5 merc", "fhr", 5, 256, {}, [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)],
     [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)]),
    ("Amazon 1H swing", "fbr", 3, 88, {}, [(0,17),(4,16),(6,15),(11,14),(15,13),(23,12),(29,11),(40,10),(56,9),(80,8),(120,7)],
     [(0,17),(4,16),(6,15),(11,14),(15,13),(23,12),(29,11),(40,10),(56,9),(80,8),(120,7),(200,6),(480,5)]),
    ("Amazon other", "fbr", 3, 256, {}, [(0,5),(13,4),(32,3),(86,2)], [(0,5),(13,4),(32,3),(86,2),(600,1)]),
    ("Assassin", "fbr", 3, 256, {}, [(0,5),(13,4),(32,3),(86,2)], [(0,5),(13,4),(32,3),(86,2),(600,1)]),
    ("Barbarian", "fbr", 4, 256, {}, [(0,7),(9,6),(20,5),(42,4),(86,3)], [(0,7),(9,6),(20,5),(42,4),(86,3),(280,2)]),
    ("Druid", "fbr", 6, 256, {}, [(0,11),(6,10),(13,9),(20,8),(32,7),(52,6),(86,5)],
     [(0,11),(6,10),(13,9),(20,8),(32,7),(52,6),(86,5),(174,4),(600,3)]),
    ("Werewolf", "fbr", 5, 256, {}, [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4)], [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)]),
    ("Werebear", "fbr", 5, 200, {}, [(0,12),(5,11),(10,10),(16,9),(27,8),(40,7),(65,6),(109,5)],
     [(0,12),(5,11),(10,10),(16,9),(27,8),(40,7),(65,6),(109,5),(223,4)]),
    ("Necromancer", "fbr", 6, 256, {}, [(0,11),(6,10),(13,9),(20,8),(32,7),(52,6),(86,5)],
     [(0,11),(6,10),(13,9),(20,8),(32,7),(52,6),(86,5),(174,4),(600,3)]),
    ("Paladin", "fbr", 3, 256, {}, [(0,5),(13,4),(32,3),(86,2)], [(0,5),(13,4),(32,3),(86,2),(600,1)]),
    ("Paladin Holy Shield", "fbr", 3, 256, {"holy": True}, [(0,2),(86,1)], [(0,2),(86,1)]),
    ("Sorceress", "fbr", 5, 256, {}, [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4)], [(0,9),(7,8),(15,7),(27,6),(48,5),(86,4),(200,3)]),
]

def main():
    agree = disagree = 0
    alts = 0
    for name, kind, base, speed, kw, mx, pd in CASES:
        top = 700
        calc = thresholds(kind, base, speed, top, **kw)
        for label, tab in (("maxroll", mx), ("pd", pd)):
            if tab is None:
                continue
            # compare only up to the table's last listed threshold
            lim = tab[-1][0]
            c = [t for t in calc if t[0] <= lim]
            ok = c == tab
            agree += ok
            disagree += not ok
            if not ok:
                print(f"DIFF {kind} {name} {label}: table={tab} formula={c}")
                for b in range(10, 22):
                    if [t for t in thresholds(kind, b, speed, top, **kw) if t[0] <= lim] == tab:
                        print(f"ALT {kind} {name} {label}: page base {base}, base {b} reproduces the table")
                        alts += 1
        # rows the tables omit past their last entry
        print(f"{kind} {name}: formula thresholds to {top}% = {calc}")
    print(f"SUMMARY anim_leads cases={len(CASES)} agree={agree} differ={disagree} alt_base_found={alts}")


# ------------------------------------------------------------------------------------ part 2: the code
WCLASSES = ("HTH", "BOW", "1HS", "1HT", "STF", "2HS", "2HT", "XBW", "1JS", "1JT", "1SS", "1ST", "HT1", "HT2")

# (kind, case name) -> (record prefix + mode token, weapon classes or None for every class present,
#                       classes excluded, sequence number or None). A sequence case takes its length from
# the player sequence table (anim/0001 § 5) and its speed from the mode-18 record, whose mode token is
# remapped to GH (anim/0001 § 2).
REC = {
    ("fcr", "Amazon"): ("AMSC", None, (), None),
    ("fcr", "Assassin"): ("AISC", None, (), None),
    ("fcr", "Barbarian"): ("BASC", None, (), None),
    ("fcr", "Druid"): ("DZSC", None, (), None),
    ("fcr", "Werewolf"): ("40SC", None, (), None),
    ("fcr", "Werebear"): ("TGSC", None, (), None),
    ("fcr", "Necromancer"): ("NESC", None, (), None),
    ("fcr", "Vampire form"): ("VASC", None, (), None),
    ("fcr", "Paladin"): ("PASC", None, (), None),
    ("fcr", "Sorceress"): ("SOSC", None, (), None),
    ("fcr", "Sorceress Lightning"): ("SOGH", None, (), 12),
    ("fcr", "Act 3 merc"): ("IWSC", None, (), None),
    ("fhr", "Amazon"): ("AMGH", None, (), None),
    ("fhr", "Assassin"): ("AIGH", None, (), None),
    ("fhr", "Barbarian"): ("BAGH", None, (), None),
    ("fhr", "Druid 1H swing"): ("DZGH", ("1HS",), (), None),
    ("fhr", "Druid other"): ("DZGH", None, ("1HS",), None),
    ("fhr", "Werewolf"): ("40GH", None, (), None),
    ("fhr", "Werebear"): ("TGGH", None, (), None),
    ("fhr", "Necromancer"): ("NEGH", None, (), None),
    ("fhr", "Vampire form"): ("VAGH", None, (), None),
    ("fhr", "Paladin spear/staff"): ("PAGH", ("STF", "2HT"), (), None),
    ("fhr", "Paladin other"): ("PAGH", None, ("STF", "2HT"), None),
    ("fhr", "Sorceress"): ("SOGH", None, (), None),
    ("fhr", "Act 1 merc"): ("RGGH", None, (), None),
    ("fhr", "Act 2 merc"): ("GUGH", None, (), None),
    ("fhr", "Act 3 merc"): ("IWGH", None, (), None),
    ("fhr", "Act 5 merc"): ("0AGH", None, (), None),
    ("fbr", "Amazon 1H swing"): ("AMBL", ("1HS",), (), None),
    ("fbr", "Amazon other"): ("AMBL", None, ("1HS",), None),
    ("fbr", "Assassin"): ("AIBL", None, (), None),
    ("fbr", "Barbarian"): ("BABL", None, (), None),
    ("fbr", "Druid"): ("DZBL", None, (), None),
    ("fbr", "Werewolf"): ("40BL", None, (), None),
    ("fbr", "Werebear"): ("TGBL", None, (), None),
    ("fbr", "Necromancer"): ("NEBL", None, (), None),
    ("fbr", "Paladin"): ("PABL", None, ("2HS",), None),
    ("fbr", "Paladin Holy Shield"): ("PABL", None, ("2HS",), None),
    ("fbr", "Sorceress"): ("SOBL", None, (), None),
}

# src:basin-wiki-animation "Attack speed" rev 65669 (re-fetched 2026-10-27, plan 0050 P1b part 2), as
# numbers: code, mode, wclass, FramesPerDirection, AnimationSpeed, StartingFrame, ActionFlagFrames, cycle.
BASIN = [
    ("AI", "A1", "HTH", 11, 256, 0, 6, 10), ("AI", "A1", "1HS", 15, 256, 0, 7, 14), ("AI", "A1", "2HS", 23, 256, 0, 11, 22),
    ("AI", "A1", "1HT", 15, 256, 0, 7, 14), ("AI", "A1", "2HT", 23, 256, 0, 10, 22), ("AI", "A1", "STF", 19, 256, 0, 9, 18),
    ("AI", "A1", "BOW", 16, 256, 0, 7, 15), ("AI", "A1", "XBW", 21, 256, 0, 10, 20), ("AI", "A1", "HT1", 11, 208, 0, 6, 13),
    ("AI", "A1", "HT2", 11, 208, 0, 6, 13),
    ("AM", "A1", "HTH", 13, 256, 1, 8, 11), ("AM", "A1", "1HS", 16, 256, 2, 10, 13), ("AM", "A1", "2HS", 20, 256, 2, 12, 17),
    ("AM", "A1", "1HT", 15, 256, 2, 9, 12), ("AM", "A1", "2HT", 18, 256, 2, 11, 15), ("AM", "A1", "STF", 20, 256, 2, 12, 17),
    ("AM", "A1", "BOW", 14, 256, 0, 6, 13), ("AM", "A1", "XBW", 20, 256, 0, 9, 19),
    ("BA", "A1", "HTH", 12, 256, 0, 6, 11), ("BA", "A1", "1HS", 16, 256, 0, 7, 15), ("BA", "A1", "2HS", 18, 256, 0, 8, 17),
    ("BA", "A1", "1HT", 16, 256, 0, 7, 15), ("BA", "A1", "2HT", 19, 256, 0, 9, 18), ("BA", "A1", "STF", 19, 256, 0, 9, 18),
    ("BA", "A1", "BOW", 15, 256, 0, 7, 14), ("BA", "A1", "XBW", 20, 256, 0, 10, 19), ("BA", "A1", "1JS", 16, 256, 0, 7, 15),
    ("BA", "A1", "1JT", 16, 256, 0, 7, 15), ("BA", "A1", "1SS", 16, 256, 0, 7, 15), ("BA", "A1", "1ST", 16, 256, 0, 7, 15),
    ("DZ", "A1", "HTH", 16, 256, 0, 8, 15), ("DZ", "A1", "1HS", 19, 256, 0, 9, 18), ("DZ", "A1", "2HS", 21, 256, 0, 10, 20),
    ("DZ", "A1", "1HT", 19, 256, 0, 8, 18), ("DZ", "A1", "2HT", 23, 256, 0, 9, 22), ("DZ", "A1", "STF", 17, 256, 0, 9, 16),
    ("DZ", "A1", "BOW", 16, 256, 0, 8, 15), ("DZ", "A1", "XBW", 20, 256, 0, 10, 19),
    ("NE", "A1", "HTH", 15, 256, 0, 8, 14), ("NE", "A1", "1HS", 19, 256, 0, 9, 18), ("NE", "A1", "2HS", 23, 256, 0, 11, 22),
    ("NE", "A1", "1HT", 19, 256, 0, 9, 18), ("NE", "A1", "2HT", 24, 256, 0, 10, 23), ("NE", "A1", "STF", 20, 256, 0, 11, 19),
    ("NE", "A1", "BOW", 18, 256, 0, 9, 17), ("NE", "A1", "XBW", 20, 256, 0, 11, 19),
    ("PA", "A1", "HTH", 14, 256, 0, 7, 13), ("PA", "A1", "1HS", 15, 256, 0, 7, 14), ("PA", "A1", "2HS", 18, 256, 0, 8, 17),
    ("PA", "A1", "1HT", 17, 256, 0, 8, 16), ("PA", "A1", "2HT", 20, 256, 0, 8, 19), ("PA", "A1", "STF", 18, 256, 0, 9, 17),
    ("PA", "A1", "BOW", 16, 256, 0, 8, 15), ("PA", "A1", "XBW", 20, 256, 0, 10, 19),
    ("SO", "A1", "HTH", 16, 256, 1, 9, 14), ("SO", "A1", "1HS", 20, 256, 2, 12, 17), ("SO", "A1", "2HS", 24, 256, 2, 14, 21),
    ("SO", "A1", "1HT", 19, 256, 2, 11, 16), ("SO", "A1", "2HT", 23, 256, 2, 13, 20), ("SO", "A1", "STF", 18, 256, 2, 11, 15),
    ("SO", "A1", "BOW", 17, 256, 0, 9, 16), ("SO", "A1", "XBW", 20, 256, 0, 11, 19),
    ("AI", "KK", "STF", 13, 256, 0, 4, 12), ("AM", "KK", "2HT", 12, 256, 0, 5, 11), ("BA", "KK", "XBW", 12, 256, 0, 4, 11),
    ("DZ", "KK", "2HT", 12, 256, 0, 5, 11), ("NE", "KK", "STF", 12, 256, 0, 6, 11), ("PA", "KK", "XBW", 12, 256, 0, 5, 11),
    ("SO", "KK", "1HS", 12, 256, 0, 6, 11),
]

# data:g_AttackStartFrames@0x006E8E60 as anim/0001 § 4 states it: classes Amazon and Sorceress only, for
# player modes A1, A2 (and S3/S4 while able to dual-wield), by the weapon's own class code.
START = {"HTH": 1, "1HS": 2, "1HT": 2, "STF": 2, "2HS": 2, "2HT": 2}

# D4 (src:basin-wiki-animation, Cast rate), seconds, keyed by the Skills.txt `skill` name.
D4 = {"Poison Javelin": 0.6, "Plague Javelin": 4, "Immolation Arrow": 1, "Valkyrie": 6, "Shock Field": 0.6,
      "Blade Sentinel": 2, "Shadow Warrior": 6, "Dragon Flight": 1, "Shadow Master": 6, "Wearwolf": 1,
      "Firestorm": 0.6, "Wearbear": 1, "Molten Boulder": 2, "Eruption": 2, "Volcano": 4, "Armageddon": 6,
      "Hurricane": 6, "Fist of the Heavens": 1, "Fire Wall": 1.4, "Meteor": 1.2, "Blizzard": 1.8, "Hydra": 1.6,
      "Frozen Orb": 1}


def first_event(r):
    for f, v in enumerate(r.events[:r.frames]):
        if v in (1, 2):
            return f
    return None


def seq_lengths(scan_path):
    """PSEQ <seqnum> <col> <addr> <frames> <length> lines of the kept P1.1 scan -> {(seqnum, col): length}."""
    out = {}
    with open(scan_path) as f:
        for line in f:
            p = line.split()
            if len(p) == 6 and p[0] == "PSEQ":
                out[(int(p[1]), int(p[2]))] = int(p[5])
    return out


def read_rows(path):
    import csv
    with open(path, encoding="latin-1") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def cmd_code(root, scan_path):
    import anim_rates as AR
    import animdata as AD
    recs = AD.load(os.path.join(root, "data", "global", "animdata.d2"))
    byname = {}
    for r in recs:
        byname.setdefault(r.name, r)          # the first record of a name wins (anim/0001 § 2.1)
    seqs = seq_lengths(scan_path)
    xd = os.path.join(root, "data", "global", "excel")
    n_tab = n_thr = n_off1 = n_off0 = 0

    # ---- TAB
    for name, kind, base, speed, kw, mx, pd in CASES:
        pre, only, excl, seq = REC[(kind, name)]
        names = [pre + w for w in WCLASSES if (only is None or w in only) and w not in excl and pre + w in byname]
        shapes = sorted({(byname[n].frames, byname[n].speed) for n in names})
        if seq is not None:
            shapes = sorted({(seqs[(seq, c)], s) for c in range(14) if (seq, c) in seqs for (_, s) in shapes})
        for F, spd in shapes:
            def n_at(p):
                if kind == "fcr":
                    r = AR.rate_cast(spd, AR.bonus(2, p))
                elif kind == "fhr":
                    r = AR.rate_gethit(spd, AR.bonus(1, p))
                else:
                    r = AR.rate_block(spd, AR.bonus(3, p), kw.get("holy", False))
                return AR.sched_len(F, 0, r)[0]
            for label, tab in (("maxroll", mx), ("pd", pd)):
                lim = tab[-1][0]
                thr, last = [], None
                for p in range(0, lim + 1):
                    v = n_at(p)
                    if v != last:
                        thr.append(p)
                        last = v
                offs = sorted({f - n_at(p) for p, f in tab})
                eq = int(thr == [p for p, _ in tab])
                n_tab += 1
                n_thr += eq
                n_off1 += int(offs == [-1])
                n_off0 += int(offs == [0])
                print("TAB %s %s %s records=%s F=%d spd=%d thresholds_equal=%d table_minus_n=%s code_thr=%s" % (
                    kind, name.replace(" ", "_"), label, ",".join(names) if seq is None else "seq%d(%s)" % (seq, ",".join(names)),
                    F, spd, eq, offs, thr))

    # ---- BASIN
    b_ok = 0
    for code, mode, wc, F, spd, S, act, cyc in BASIN:
        nm = code + mode + wc
        r = byname.get(nm)
        if r is None:
            print("BASIN %s missing" % nm)
            continue
        s_code = START.get(wc, 0) if (code in ("AM", "SO") and mode == "A1") else 0
        fe = first_event(r)
        n = AR.sched_len(r.frames, s_code, AR.rate_attack(r.speed, 100))[0]
        ok = (r.frames, r.speed, s_code, fe) == (F, spd, S, act)
        b_ok += ok
        print("BASIN %s frames=%d/%d speed=%d/%d start=%d/%d action=%s/%d match=%d cycle=%d n_at_x100=%d" % (
            nm, r.frames, F, r.speed, spd, s_code, S, fe, act, int(ok), cyc, n))

    # ---- CAST
    for pre in ("AMSC", "AISC", "BASC", "DZSC", "40SC", "TGSC", "NESC", "VASC", "PASC", "SOSC", "IWSC"):
        for w in WCLASSES:
            r = byname.get(pre + w)
            if r:
                print("CAST %s frames=%d speed=%d action=%s" % (r.name, r.frames, r.speed, first_event(r)))

    # ---- DELAY
    sk = read_rows(os.path.join(xd, "skills.txt"))
    d_ok = d_n = 0
    for row in sk:
        if row["charclass"] and row["delay"] not in ("", "0"):
            d_n += 1
            sec = D4.get(row["skill"])
            ok = sec is not None and round(sec * 25) == int(row["delay"])
            d_ok += ok
            print("DELAY %s %s delay=%s d4_seconds=%s match_at_25=%d" % (
                row["charclass"], row["skill"].replace(" ", "_"), row["delay"], sec, int(ok)))
    print("DELAY rows=%d match=%d d4_named=%d" % (d_n, d_ok, len(D4)))

    # ---- SEQ
    for nm, sq in (("Jab", 1), ("Impale", 8), ("Lightning/Chain_Lightning", 12), ("Charge", 4), ("Double_Swing/Frenzy", 11),
                   ("Double_Throw", 15), ("Leap_Attack", 14), ("Fists_of_Fire/Claws_of_Thunder/Blades_of_Ice", 16)):
        print("SEQ %s seqnum=%d lengths_by_column=%s" % (nm, sq, sorted({v for (s, c), v in seqs.items() if s == sq})))
    for row in sk:
        if row["skill"] in ("Jab", "Impale", "Lightning", "Chain Lightning", "Charge", "Double Swing", "Frenzy",
                            "Double Throw", "Leap Attack", "Fists of Fire", "Claws of Thunder", "Blades of Ice"):
            print("SKILL %s anim=%s seqtrans=%s seqnum=%s UseAttackRate=%s interrupt=%s" % (
                row["skill"].replace(" ", "_"), row["anim"], row["seqtrans"], row["seqnum"], row["UseAttackRate"] or 0,
                row["interrupt"] or 0))
    no_int = [row["skill"].replace(" ", "_") for row in sk if (row["charclass"] or row["Id"] in ("0", "1"))
              and row["interrupt"] != "1"]
    print("INTERRUPT player_rows_without=%d %s" % (len(no_int), ",".join(no_int)))

    # ---- MOVE
    for row in read_rows(os.path.join(xd, "charstats.txt")):
        if row["class"] != "Expansion":
            print("MOVE charstats %s WalkVelocity=%s RunVelocity=%s" % (row["class"], row["WalkVelocity"], row["RunVelocity"]))
    ms = [r for r in read_rows(os.path.join(xd, "monstats.txt")) if r["Id"] != "Expansion"]
    m2 = {r["Id"]: r for r in read_rows(os.path.join(xd, "monstats2.txt"))}
    for i in (430, 431, 135, 212):
        r = ms[i]
        print("MOVE shape class=%d %s Velocity=%s mRN=%s" % (i, r["Id"], r["Velocity"], m2[r["MonStatsEx"]]["mRN"] or 0))

    # ---- WSM
    wp = [r for r in read_rows(os.path.join(xd, "weapons.txt")) if r.get("code") and r["name"] != "Expansion"]
    sp = [int(r["speed"] or 0) for r in wp]
    print("WSM rows=%d speed_min=%d speed_max=%d %s" % (len(wp), min(sp), max(sp), " ".join(
        "%s=%s" % (r["name"].replace(" ", "_"), r["speed"] or 0) for r in wp if r["name"] in ("Axe", "Hand Axe", "Military Pick"))))
    t1 = sorted({r["type"] for r in wp if r["wclass"] == "1hs"})
    t1h = sorted({r["type"] for r in wp if r["wclass"] == "1hs" and r["2handed"] != "1"})
    print("WSM wclass_1hs_types=%s one_handed_only=%s" % (",".join(t1), ",".join(t1h)))
    print("SUMMARY anim_leads_code tab=%d thresholds_equal=%d table_minus_n_is_-1=%d table_minus_n_is_0=%d basin=%d basin_match=%d "
          "delay_rows=%d delay_match=%d" % (n_tab, n_thr, n_off1, n_off0, len(BASIN), b_ok, d_n, d_ok))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "code":
        cmd_code(sys.argv[2], sys.argv[3])
    else:
        main()
