"""Survey of the animation and timing data (plan 0050 Phase 0): the tables' tokens joined with animdata.d2.

Usage:
  python3 -I tools/anim_survey.py players  <root>      per class (plrtype Token) and mode (plrmode Token): the weapon
                                                       classes with an animdata record, frames and speed of each
  python3 -I tools/anim_survey.py monsters <root>      per MonStats row: Code + each mode its MonStats2 m<mode> flag
                                                       sets + BaseW (else HTH); the record found, or the miss; and
                                                       the game's rule (anim/0001 section 2), mon_rule_miss
  python3 -I tools/anim_survey.py objects  <root>      per Objects row: Token + each mode its Mode<k> flag sets + HTH;
                                                       FrameCnt<k> and FrameDelta<k> against the record; the same
                                                       join with the ObjType token (OBJTYPE lines, obj_objtype_*)
  python3 -I tools/anim_survey.py skills   <root>      Skills rows per anim, monanim, seqtrans, seqnum, seqinput; the
                                                       delay/perdelay cells; the rate stats and their users
  python3 -I tools/anim_survey.py monseq   <root>      per monseq sequence: rows, modes, frames, event frames, users
                                                       (MonStats Sk<k>seq), and each user's record frames
  python3 -I tools/anim_survey.py ratemin  <root>      the stock sources writing a rate-bonus stat (93, 96, 99, 102,
                                                       105) and their lowest values (anim/0002 open question 3)
  python3 -I tools/anim_survey.py twoframe <root>      the two-frame S1-S4 records with an event, and the MonStats
                                                       rows whose Code names them: class, m<mode>, <mode>mv,
                                                       Velocity, the derived walk base (plan 0050 P1.2 review)
  python3 -I tools/anim_survey.py summary  <root>      the counts of every section only

<root> is a merged data tree (workspace/merged): the tables come from <root>/data/global/excel, the records from
<root>/data/global/animdata.d2 (tools/animdata.py). Table values come from the .bin records decoded with
tools/excel_layouts.py; blank cells from the .txt. The joins use the record name rule of docs/formats/animdata.md
(token + mode token + weapon class, upper case); the name the game builds and its fallback are
docs/findings/anim/0001-modes-frames.md section 2 (the monster and ObjType counts above follow it). Every command ends with `SURVEY anim key=value ...`; tools/gate.py --full
compares the summary line with its baseline. Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import animdata  # noqa: E402
import excel_bin as eb  # noqa: E402
from combat_survey import Table, hist  # noqa: E402

RATE_STATS = ("velocitypercent", "attackrate", "other_animrate", "item_fasterattackrate", "item_fastermovevelocity",
              "item_fastergethitrate", "item_fasterblockrate", "item_fastercastrate", "item_slow")
MON_MODES = ["DT", "NU", "WL", "GH", "A1", "A2", "BL", "SC", "S1", "S2", "S3", "S4", "DD", "KB", "SQ", "RN"]


class Data:
    def __init__(self, root):
        self.excel = os.path.join(root, "data", "global", "excel")
        self.refs = eb.Refs(self.excel)
        self.t = {}
        for name in ("plrmode", "monmode", "objmode", "monstats", "monstats2", "objects", "skills", "itemstatcost",
                     "states", "monseq", "hitclass", "weapons", "charstats", "objtype"):
            self.t[name] = Table(self.excel, name, self.refs)
        self.recs = animdata.load(os.path.join(root, "data", "global", "animdata.d2"))
        self.by = collections.defaultdict(list)
        for r in self.recs:
            self.by[r.name].append(r)
        _h, rows = eb.read_txt(eb.find_file(self.excel, "plrtype", ".txt"))
        self.ptokens = [(r[0], r[1]) for r in rows if r[1]]
        _h, rows = eb.read_txt(eb.find_file(self.excel, "weaponclass", ".txt"))
        self.wclasses = [r[1] for r in rows if r[1]]
        self.pmode_tok = [r["Token"] for r in self.t["plrmode"].rec]
        self.pmode_code = [r["Code"] for r in self.t["plrmode"].txt]
        self.mmode_tok = [r["token"] for r in self.t["monmode"].rec]
        self.mmode_code = [r["code"] for r in self.t["monmode"].txt]
        self.omode_tok = [r["Token"] for r in self.t["objmode"].rec]
        self.skills = [r["skill"] for r in self.t["skills"].txt]
        self.stats = [r["Stat"] for r in self.t["itemstatcost"].txt]

    def rec(self, name):
        rs = self.by.get(name.upper())
        return rs[0] if rs else None


def fr(r):
    return "%d/%d" % (r.frames, r.speed) + ("" if not animdata.events_of(r) else
                                           "@" + ",".join("%d:%d" % e for e in animdata.events_of(r)))


def mode_table(title, codes, per):
    """Lines: per mode the rows (or class x wclass cells) that name it, the distinct records joined, their frames
    and speed ranges and event bytes (value: count, first..last frame)."""
    out = [title]
    for k, code in enumerate(codes):
        n, rs = per.get(k, (0, set()))
        if not n and not rs:
            continue
        fr_ = [r.frames for r in rs]
        sp = [r.speed for r in rs]
        evf = collections.defaultdict(list)
        for r in rs:
            for f, v in animdata.events_of(r):
                evf[v].append(f)
        out.append("  %2d %-2s named %4d  records %4d  frames %-8s speed %-8s events %s" % (
            k, code, n, len(rs), ("%d..%d" % (min(fr_), max(fr_))) if rs else "-",
            ("%d..%d" % (min(sp), max(sp))) if rs else "-",
            "; ".join("%d: %d, frames %d..%d" % (v, len(evf[v]), min(evf[v]), max(evf[v])) for v in sorted(evf)) or "-"))
    return out


# ---------------------------------------------------------------- sections: each returns (lines, kv)

def sec_players(d):
    out, kv = [], collections.OrderedDict()
    pairs = hits = 0
    per = {}
    per_mode = collections.Counter()
    ev_modes = collections.Counter()
    for cname, tok in d.ptokens:
        out.append("class %s (%s):" % (tok, cname))
        for m, mtok in enumerate(d.pmode_tok):
            if m in (18, 19):   # Sequence and Knock back store token GH: the same names as row 4
                continue
            found = []
            for w in d.wclasses:
                r = d.rec(tok + mtok + w)
                if r:
                    found.append((w, r))
            hits += len(found)
            pairs += 1
            n0, rs0 = per.get(m, (0, set()))
            per[m] = (n0 + len(found), rs0 | {r for _w, r in found})
            per_mode[d.pmode_code[m]] += len(found)
            for _w, r in found:
                for _f, v in animdata.events_of(r):
                    ev_modes["%s:%d" % (d.pmode_code[m], v)] += 1
            if found:
                frames = sorted({r.frames for _w, r in found})
                speeds = sorted({r.speed for _w, r in found})
                out.append("  %-2s %-12s %2d wclass  frames %s  speed %s  | %s" % (
                    d.pmode_code[m], d.t["plrmode"].rec[m]["Name"], len(found), frames, speeds,
                    " ".join("%s=%s" % (w, fr(r)) for w, r in found)))
            else:
                out.append("  %-2s %-12s none" % (d.pmode_code[m], d.t["plrmode"].rec[m]["Name"]))
    own = sum(1 for n in d.by if n[:2] in {t for _c, t in d.ptokens})
    out.append("player record names (name starts with a class token): %d; joined by class x mode x weaponclass: %d" % (
        own, hits))
    out.append("records per mode: %s" % hist(per_mode.elements()))
    out += mode_table("per mode (named = class x weapon class cells with a record):", d.pmode_code, per)
    out.append("event bytes per mode (mode:value): %s" % hist(ev_modes.elements()))
    kv["plr_classes"] = len(d.ptokens)
    kv["plr_class_modes"] = pairs
    kv["plr_records"] = own
    kv["plr_joined"] = hits
    kv["plr_unjoined"] = own - hits
    kv["plr_modes_none"] = sum(1 for m, c in enumerate(d.pmode_code) if m not in (18, 19) and per_mode[c] == 0)
    return out, kv


def sec_monsters(d):
    out, kv = [], collections.OrderedDict()
    ms, m2 = d.t["monstats"], d.t["monstats2"]
    rows = hit_base = hit_hth = miss = modes_n = sq_flag = rule_miss = 0
    per = {}
    miss_mode = collections.Counter()
    used = set()
    misses = []
    ev = collections.Counter()
    frames_ev = 0
    for i, r in enumerate(ms.rec):
        if ms.blank(i, "MonStatsEx") or ms.txt[i]["Code"] == "":
            continue
        rows += 1
        x = m2.rec[r["MonStatsEx"]]
        tok, base = r["Code"], x["BaseW"] or "hth"
        for k, mt in enumerate(MON_MODES):
            if not x["m" + mt]:
                continue
            n0, rs0 = per.get(k, (0, set()))
            per[k] = (n0 + 1, rs0)
            if mt == "SQ":   # the sequence mode: no record of its own (a sequence names other modes, monseq)
                sq_flag += 1
                continue
            modes_n += 1
            name = tok + d.mmode_tok[k] + base
            rec = d.rec(name)
            if rec:
                hit_base += 1
                used.add(rec.name)
            else:
                rec = d.rec(tok + d.mmode_tok[k] + "hth")
                if rec:
                    hit_hth += 1
                    used.add(rec.name)
                else:
                    miss += 1
                    miss_mode[d.mmode_code[k]] += 1
                    misses.append("%s(%d) %s %s" % (ms.txt[i]["Id"], i, d.mmode_code[k], name.upper()))
            # findings/anim/0001 section 2: the game's name takes hth in DT (0) and DD (12) unless compositeDeath,
            # else BaseW; a name with no record gets the built-in fallback record (no HTH retry)
            gw = base if (k not in (0, 12) or x["compositeDeath"]) else "hth"
            if not d.rec(tok + d.mmode_tok[k] + gw):
                rule_miss += 1
                misses.append("RULE %s(%d) %s %s" % (ms.txt[i]["Id"], i, d.mmode_code[k], (tok + d.mmode_tok[k] + gw).upper()))
            if rec:
                per[k][1].add(rec)
                for _f, v in animdata.events_of(rec):
                    ev["%s:%d" % (d.mmode_code[k], v)] += 1
                frames_ev += 1
    toks = {ms.txt[i]["Code"].upper() for i in range(len(ms.rec)) if ms.txt[i]["Code"]}
    own = sum(1 for n in d.by if n[:2] in toks)
    out.append("MonStats rows with a Code and MonStatsEx: %d; flagged modes %d: record with BaseW %d, with HTH %d, "
               "none %d" % (rows, modes_n, hit_base, hit_hth, miss))
    out.append("m%s set on %d rows (not joined); misses per mode: %s" % ("SQ", sq_flag, hist(miss_mode.elements())))
    out.append("distinct record names used: %d of %d whose name starts with a MonStats Code" % (len(used), own))
    out.append("by the game's rule (anim/0001 section 2: hth in DT/DD without compositeDeath, else BaseW): flagged "
               "modes with no record %d" % rule_miss)
    out.append("event bytes per mode (mode:value), per flagged mode of a row: %s" % hist(ev.elements()))
    out += mode_table("per mode (named = MonStats rows whose MonStats2 m<mode> is set; records = distinct records):",
                      d.mmode_code, per)
    for m in misses[:80]:
        out.append("  MISS " + m)
    if len(misses) > 80:
        out.append("  ... %d more" % (len(misses) - 80))
    kv["mon_rows"] = rows
    kv["mon_modes"] = modes_n
    kv["mon_hit_basew"] = hit_base
    kv["mon_hit_hth"] = hit_hth
    kv["mon_miss"] = miss
    kv["mon_msq"] = sq_flag
    kv["mon_records_used"] = len(used)
    kv["mon_rule_miss"] = rule_miss
    return out, kv


def sec_objects(d):
    out, kv = [], collections.OrderedDict()
    ob = d.t["objects"]
    rows = modes_n = hit = miss = cnt_eq = dlt_eq = 0
    miss_mode = collections.Counter()
    pm = collections.defaultdict(collections.Counter)
    misses, diffs = [], []
    for i, r in enumerate(ob.rec):
        tok = r["Token"]
        if not tok:
            continue
        rows += 1
        for k in range(8):
            if not r["Mode%d" % k]:
                continue
            modes_n += 1
            name = tok + d.omode_tok[k] + "hth"
            rec = d.rec(name)
            c = pm[k]
            c["flag"] += 1
            if rec:
                fc, fd = r["FrameCnt%d" % k], r["FrameDelta%d" % k]
                c["record"] += 1
                c["cnt_eq"] += fc == rec.frames
                c["cnt_lt"] += fc < rec.frames
                c["cnt_gt"] += fc > rec.frames
                c["delta_eq"] += fd == rec.speed
                c["delta_0"] += fd == 0
                c["speed_256"] += rec.speed == 256
            if not rec:
                miss += 1
                miss_mode[d.omode_tok[k]] += 1
                misses.append("%s(%d) %s %s" % (ob.txt[i]["Name"], i, d.omode_tok[k], name.upper()))
                continue
            hit += 1
            c, dl = r["FrameCnt%d" % k], r["FrameDelta%d" % k]
            cnt_eq += c == rec.frames
            dlt_eq += dl == rec.speed
            if c != rec.frames or dl != rec.speed:
                diffs.append("%s(%d) mode %s: FrameCnt %d frames %d | FrameDelta %d speed %d" % (
                    ob.txt[i]["Name"], i, d.omode_tok[k], c, rec.frames, dl, rec.speed))
    out.append("Objects rows with a Token: %d; flagged modes %d: record %d, none %d; FrameCnt == frames %d, "
               "FrameDelta == speed %d" % (rows, modes_n, hit, miss, cnt_eq, dlt_eq))
    out.append("misses per mode: %s" % hist(miss_mode.elements()))
    out.append("per mode: flagged, with a record, FrameCnt = / < / > record frames, FrameDelta = record speed, "
               "FrameDelta 0, record speed 256")
    for k in sorted(pm):
        c = pm[k]
        out.append("  %d %s flagged %3d record %3d  cnt = %3d < %3d > %d  delta = %3d  delta 0 %3d  speed 256 %3d" % (
            k, d.omode_tok[k], c["flag"], c["record"], c["cnt_eq"], c["cnt_lt"], c["cnt_gt"], c["delta_eq"],
            c["delta_0"], c["speed_256"]))
    for m in misses:
        out.append("  MISS " + m)
    for x in diffs[:60]:
        out.append("  DIFF " + x)
    if len(diffs) > 60:
        out.append("  ... %d more" % (len(diffs) - 60))
    # findings/anim/0001 section 2: the object record name takes the object-type token (objtype +0x020, row = the
    # Objects row), not the Objects Token. The same join with that token: rows whose two tokens differ, and the
    # flagged modes with a record under it.
    ot = d.t["objtype"].rec
    tok_ne = ot_hit = 0
    for i, r in enumerate(ob.rec):
        otok = ot[i]["Token"].strip() if i < len(ot) else ""
        if otok.lower() != r["Token"].lower():
            tok_ne += 1
            out.append("  OBJTYPE %s(%d) Objects %s objtype %s" % (ob.txt[i]["Name"], i, r["Token"], otok))
        for k in range(8):
            if r["Mode%d" % k] and otok and d.rec(otok + d.omode_tok[k] + "hth"):
                ot_hit += 1
    out.append("objtype token: rows whose Token differs from Objects Token %d; flagged modes with a record under the "
               "objtype token %d" % (tok_ne, ot_hit))
    kv["obj_objtype_token_ne"] = tok_ne
    kv["obj_objtype_hit"] = ot_hit
    kv["obj_rows"] = rows
    kv["obj_modes"] = modes_n
    kv["obj_hit"] = hit
    kv["obj_miss"] = miss
    kv["obj_framecnt_eq"] = cnt_eq
    kv["obj_framedelta_eq"] = dlt_eq
    kv["obj_framecnt_gt"] = sum(c["cnt_gt"] for c in pm.values())
    kv["obj_sync"] = sum(1 for r in ob.rec if r["Sync"])
    # objects spec G2: Sync 0 -> a unit-seed draw Range(seed, FrameDelta[mode] >> 3) at each animation start, none
    # when the bound is < 1: the rows and the (row, flagged mode) pairs whose start would draw
    kv["obj_sync0_draw_rows"] = sum(1 for r in ob.rec if not r["Sync"] and any(
        r["Mode%d" % k] and r["FrameDelta%d" % k] >> 3 >= 1 for k in range(8)))
    kv["obj_sync0_draw_modes"] = sum(1 for r in ob.rec if not r["Sync"] for k in range(8)
                                     if r["Mode%d" % k] and r["FrameDelta%d" % k] >> 3 >= 1)
    out.append("Sync 0 rows %d; with a flagged mode whose FrameDelta >> 3 >= 1: rows %d, (row, mode) pairs %d" % (
        sum(1 for r in ob.rec if not r["Sync"]), kv["obj_sync0_draw_rows"], kv["obj_sync0_draw_modes"]))
    kv["obj_cycleanim"] = sum(1 for r in ob.rec for k in range(8) if r["CycleAnim%d" % k])
    return out, kv


def sec_skills(d):
    out, kv = [], collections.OrderedDict()
    sk = d.t["skills"]
    n = len(sk.rec)
    anim = collections.Counter(d.pmode_code[r["anim"]] for i, r in enumerate(sk.rec) if not sk.blank(i, "anim"))
    monanim = collections.Counter(d.mmode_code[r["monanim"]] for i, r in enumerate(sk.rec)
                                  if not sk.blank(i, "monanim"))
    seqtrans = collections.Counter(d.pmode_code[r["seqtrans"]] for i, r in enumerate(sk.rec)
                                   if not sk.blank(i, "seqtrans"))
    seqnum = collections.Counter(r["seqnum"] for i, r in enumerate(sk.rec) if not sk.blank(i, "seqnum"))
    seqinput = collections.Counter(r["seqinput"] for i, r in enumerate(sk.rec) if not sk.blank(i, "seqinput"))
    out.append("Skills rows %d; anim set %d: %s" % (n, sum(anim.values()), hist(anim.elements())))
    out.append("monanim set %d: %s" % (sum(monanim.values()), hist(monanim.elements())))
    out.append("seqtrans set %d: %s" % (sum(seqtrans.values()), hist(seqtrans.elements())))
    out.append("seqnum set %d: %s" % (sum(seqnum.values()), hist(seqnum.elements())))
    out.append("seqinput set %d: %s" % (sum(seqinput.values()), hist(seqinput.elements())))
    sq = [i for i, r in enumerate(sk.rec) if not sk.blank(i, "anim") and d.pmode_code[r["anim"]] == "SQ"]
    sq_num = collections.Counter(sk.rec[i]["seqnum"] for i in sq)
    out.append("anim SQ rows %d, per seqnum: %s" % (len(sq), hist(sq_num.elements())))
    for v in sorted(sq_num):
        rows = [i for i in sq if sk.rec[i]["seqnum"] == v]
        out.append("  seqnum %2d (%d rows): %s" % (v, len(rows), ", ".join(
            "%s[%s,%s,in %s]" % (d.skills[i], d.pmode_code[sk.rec[i]["seqtrans"]] if not sk.blank(i, "seqtrans")
                                else "-", "cls " + (sk.txt[i]["charclass"] or "-"), sk.txt[i]["seqinput"] or "-")
            for i in rows[:12])) + (" ..." if len(rows) > 12 else ""))
    mq = [i for i, r in enumerate(sk.rec) if not sk.blank(i, "monanim") and d.mmode_code[r["monanim"]] == "xx"]
    nonsq_seqnum = sum(1 for i, r in enumerate(sk.rec) if not sk.blank(i, "seqnum") and i not in set(sq))
    delay = sum(1 for i in range(n) if not sk.blank(i, "delay"))
    perdelay = sum(1 for i in range(n) if not sk.blank(i, "perdelay"))
    out.append("monanim xx rows %d; seqnum set outside anim SQ %d; delay set %d; perdelay set %d" % (
        len(mq), nonsq_seqnum, delay, perdelay))
    # the rate stats: ItemStatCost rows, UpdateAnimRate, and the Skills / States columns that name them
    isc = d.t["itemstatcost"]
    uar = [d.stats[i] for i, r in enumerate(isc.rec) if r["UpdateAnimRate"]]
    out.append("ItemStatCost UpdateAnimRate rows %d: %s" % (len(uar), ", ".join("%s(%d)" % (s, d.stats.index(s))
                                                                                for s in uar)))
    users = collections.defaultdict(list)
    for i, r in enumerate(sk.rec):
        for col in ["aurastat%d" % k for k in range(1, 7)] + ["passivestat%d" % k for k in range(1, 6)]:
            if not sk.blank(i, col):
                s = d.stats[r[col]]
                if s in RATE_STATS or s in uar:
                    users[s].append("%s.%s" % (d.skills[i], col))
    st = d.t["states"]
    st_users = collections.defaultdict(list)
    for i, r in enumerate(st.rec):
        if not st.blank(i, "stat"):
            s = d.stats[r["stat"]]
            if s in RATE_STATS or s in uar:
                st_users[s].append(st.txt[i]["state"])
    for s in RATE_STATS + tuple(x for x in uar if x not in RATE_STATS):
        out.append("  stat %-26s (%3d) UpdateAnimRate %d | Skills %d: %s | States.stat %d: %s" % (
            s, d.stats.index(s), int(s in uar), len(users[s]), ", ".join(users[s][:8]) + (" ..." if len(users[s]) > 8
                                                                                         else ""),
            len(st_users[s]), ", ".join(st_users[s])))
    kv["sk_rows"] = n
    kv["sk_anim"] = sum(anim.values())
    kv["sk_anim_sq"] = len(sq)
    kv["sk_monanim"] = sum(monanim.values())
    kv["sk_monanim_xx"] = len(mq)
    kv["sk_seqtrans"] = sum(seqtrans.values())
    kv["sk_seqnum"] = sum(seqnum.values())
    kv["sk_seqnum_distinct"] = len(seqnum)
    kv["sk_seqnum_nonsq"] = nonsq_seqnum
    kv["sk_seqinput"] = sum(seqinput.values())
    kv["sk_delay"] = delay
    kv["sk_perdelay"] = perdelay
    kv["isc_updateanimrate"] = len(uar)
    kv["rate_stat_skill_cells"] = sum(len(v) for v in users.values())
    kv["rate_stat_states"] = sum(len(v) for v in st_users.values())
    return out, kv


def sec_monseq(d):
    out, kv = [], collections.OrderedDict()
    mq = d.t["monseq"]
    names = []
    for r in mq.txt:
        if r["sequence"] not in names:
            names.append(r["sequence"])
    seqs = collections.OrderedDict((n, []) for n in names)
    for i, r in enumerate(mq.txt):
        seqs[r["sequence"]].append(i)
    ms = d.t["monstats"]
    users = collections.defaultdict(list)
    for i, r in enumerate(ms.rec):
        for k in range(1, 9):
            v = r["Sk%dseq" % k]
            if v >= 0 and not ms.blank(i, "Sk%dmode" % k):
                users[v].append((i, k))
    over = checked = none = 0
    ev_cmp = collections.Counter()
    ev_total = collections.Counter()
    for si, (name, rows) in enumerate(seqs.items()):
        modes = []
        for i in rows:
            m = d.mmode_code[mq.rec[i]["mode"]]
            if not modes or modes[-1][0] != m:
                modes.append([m, []])
            modes[-1][1].append(mq.rec[i]["frame"])
        evs = [(j, d.mmode_code[mq.rec[i]["mode"]], mq.rec[i]["frame"], mq.rec[i]["event"])
               for j, i in enumerate(rows) if mq.rec[i]["event"]]
        for e in evs:
            ev_total[e[3]] += 1
        us = users.get(si, [])
        # each user's record frames per mode: monseq frames must stay below the record's frames
        u_over = u_none = 0
        for (mi, _k) in us:
            x = d.t["monstats2"].rec[ms.rec[mi]["MonStatsEx"]]
            tok, base = ms.rec[mi]["Code"], x["BaseW"] or "hth"
            for i in rows:
                mm = mq.rec[i]["mode"]
                rec = d.rec(tok + d.mmode_tok[mm] + base) or d.rec(tok + d.mmode_tok[mm] + "hth")
                checked += 1
                if rec is None:
                    u_none += 1
                elif mq.rec[i]["frame"] >= rec.frames:
                    u_over += 1
                else:
                    a, b = mq.rec[i]["event"], rec.events[mq.rec[i]["frame"]]
                    ev_cmp["same_set" if a and a == b else "same_zero" if a == b else
                           "seq_only" if not b else "rec_only" if not a else "both_differ"] += 1
        over += u_over
        none += u_none
        def span(fs):
            if fs == list(range(fs[0], fs[-1] + 1)):
                return "%d..%d" % (fs[0], fs[-1])
            return ",".join(str(f) for f in fs)
        unames = sorted({ms.txt[i]["Id"] for i, _k in us})
        out.append("seq %2d %-22s rows %3d  %s  events %s  users %d%s%s" % (
            si, name or "(blank)", len(rows), " ".join("%s[%s]" % (m, span(fs)) for m, fs in modes),
            " ".join("#%d=%s%d:%d" % (j, m, f, e) for j, m, f, e in evs) or "-", len(us),
            (" (%s)" % ", ".join(unames[:8]) + (" ..." if len(unames) > 8 else "")) if us else "",
            (" FRAME>=RECORD %d" % u_over if u_over else "") + (" NO-RECORD %d" % u_none if u_none else "")))
    kv["seq_rows"] = len(mq.rec)
    kv["seq_sequences"] = len(seqs)
    kv["seq_events"] = sum(ev_total.values())
    for v in sorted(ev_total):
        kv["seq_event%d" % v] = ev_total[v]
    kv["seq_dir_set"] = sum(1 for i in range(len(mq.rec)) if not mq.blank(i, "dir"))
    kv["seq_users"] = sum(len(v) for v in users.values())
    kv["seq_used"] = len(users)
    kv["seq_user_frames_checked"] = checked
    kv["seq_user_frame_past_record"] = over
    kv["seq_user_no_record"] = none
    out.append("monseq event against the user's record event byte at the same frame (user rows x sequence rows): %s"
               % ", ".join("%s %d" % (k, ev_cmp[k]) for k in ("same_set", "same_zero", "seq_only", "rec_only",
                                                              "both_differ")))
    for k in ("same_set", "same_zero", "seq_only", "rec_only", "both_differ"):
        kv["seq_ev_" + k] = ev_cmp[k]
    return out, kv


RATE_BONUS = (("item_fasterattackrate", 120), ("item_fastermovevelocity", 150), ("item_fastergethitrate", 120),
              ("item_fasterblockrate", 120), ("item_fastercastrate", 120))


def sec_ratemin(d):
    """The stock sources that write a rate-bonus stat (93, 96, 99, 102, 105) and their lowest values.

    findings/anim/0002 sections 2 and 3.1-3.2: the factor goes negative (the wrap to the cap) for FHR and FBR at
    s <= -36 and for FCR (and FBR under holyshield) at s <= -55; s = -k divides by zero. Sources: the property blocks
    of tools/prop_survey.py SOURCES, cubemain mod 1..5, monprop prop1..6 (all three difficulties), Skills
    aurastat1..6 / passivestat1..5, States stat, Misc stat1..3 and ItemStatCost op stat1..3."""
    import prop_survey as ps
    out, kv = [], collections.OrderedDict()
    pd = ps.Data(d.excel)
    names = [s for s, _k in RATE_BONUS]
    codes = {}   # property code (lower case) -> the rate stats its slots write
    for i, c in enumerate(pd.pcode):
        w = [pd.stat(s) for _f, s, _st, _v in pd.slots(i) if pd.stat(s) in names]
        if w:
            codes[c.lower()] = w
    out.append("property codes writing a rate stat: %s" % ", ".join("%s->%s" % (c, "/".join(v))
                                                                    for c, v in sorted(codes.items())))
    blocks = collections.defaultdict(list)   # stat -> [(source, row, code, min, max)]
    for name in pd.uses:
        for r, ok, bl in pd.uses[name]:
            for _k, code, _par, lo, hi in bl:
                for s in codes.get(code.lower(), []):
                    blocks[s].append((name if ok else name + "(not live)", r, code, lo, hi))
    cells, n = ps.txt_cells(d.excel, "cubemain")
    for r in range(n):
        for k in range(1, 6):
            for s in codes.get(cells["mod %d" % k][r].lower(), []):
                blocks[s].append(("cubemain", r, cells["mod %d" % k][r], cells["mod %d min" % k][r],
                                  cells["mod %d max" % k][r]))
    cells, n = ps.txt_cells(d.excel, "monprop")
    for r in range(n):
        for suf in ("", " (N)", " (H)"):
            for k in range(1, 7):
                c = cells["prop%d%s" % (k, suf)][r]
                for s in codes.get(c.lower(), []):
                    blocks[s].append(("monprop" + suf, r, c, cells["min%d%s" % (k, suf)][r],
                                      cells["max%d%s" % (k, suf)][r]))
    other = collections.Counter()
    sk = d.t["skills"]
    for i, r in enumerate(sk.rec):
        for col in ["aurastat%d" % k for k in range(1, 7)] + ["passivestat%d" % k for k in range(1, 6)]:
            if not sk.blank(i, col) and d.stats[r[col]] in names:
                other["skills"] += 1
    st = d.t["states"]
    other["states"] = sum(1 for i, r in enumerate(st.rec) if not st.blank(i, "stat") and d.stats[r["stat"]] in names)
    cells, n = ps.txt_cells(d.excel, "misc")
    other["misc"] = sum(1 for r in range(n) for k in (1, 2, 3) if cells["stat%d" % k][r] in names)
    isc = d.t["itemstatcost"]
    other["isc_op"] = sum(1 for i in range(len(isc.rec)) for k in (1, 2, 3)
                          if isc.txt[i].get("op stat%d" % k, "") in names)
    out.append("cells naming a rate stat outside the property blocks: %s" % ", ".join(
        "%s %d" % (k, other[k]) for k in ("skills", "states", "misc", "isc_op")))
    lowest_all = None
    neg = reach = nonint_all = 0
    for s, k in RATE_BONUS:
        b = blocks[s]
        vals = [int(v) for _n, _r, _c, lo, hi in b for v in (lo, hi) if ps.is_int(v.strip())]
        nonint = sum(1 for _n, _r, _c, lo, hi in b for v in (lo, hi) if not ps.is_int(v.strip()))
        nonint_all += nonint
        lo = min(vals) if vals else 0
        lowest_all = lo if lowest_all is None else min(lowest_all, lo)
        neg += sum(1 for v in vals if v < 0)
        thr = -55 if s == "item_fastercastrate" else -36
        reach += int(lo <= thr)
        per = collections.Counter(x[0] for x in b)
        out.append("  stat %-24s (%3d, k %3d): blocks %3d (%s); min..max %d..%d; negative cells %d; non-integer %d; "
                   "factor < 0 needs s <= %d, divide fault s = -%d" % (
                       s, d.stats.index(s), k, len(b), ", ".join("%s %d" % x for x in sorted(per.items())), lo,
                       max(vals) if vals else 0, sum(1 for v in vals if v < 0), nonint, thr, k))
        for x in sorted(b, key=lambda x: (min(int(v) for v in x[3:] if ps.is_int(v.strip()))
                                          if any(ps.is_int(v.strip()) for v in x[3:]) else 0))[:3]:
            out.append("      lowest: %s row %d %s %s..%s" % x)
    kv["rate_src_blocks"] = sum(len(v) for v in blocks.values())
    kv["rate_src_other_cells"] = sum(other.values())
    kv["rate_src_negative"] = neg
    kv["rate_src_nonint"] = nonint_all
    kv["rate_src_lowest"] = lowest_all or 0
    kv["rate_src_reach_wrap"] = reach
    return out, kv


def sec_twoframe(d):
    """The two-frame S1-S4 records with a frame event, and the MonStats rows whose Code names one.

    Class < 410 takes the moving branch in S1-S4 (findings/anim/0002 section 1, the monster mode-class table);
    the walk base is MonStats +0x36 (section 3.5): the record (Code of BaseId, WL, BaseW)'s speed, scaled by
    Velocity(i) / Velocity(BaseId) when BaseId != i and Velocity(BaseId) > 0."""
    out, kv = [], collections.OrderedDict()
    ms, m2 = d.t["monstats"], d.t["monstats2"]
    ids = [r["Id"] for r in ms.txt]
    smodes = [k for k, m in enumerate(MON_MODES) if m in ("S1", "S2", "S3", "S4")]
    recs = []
    for r in d.recs:
        if r.frames == 2 and any(True for _f, _v in animdata.events_of(r)) and r.name[2:4] in \
                [d.mmode_tok[k].upper() for k in smodes]:
            recs.append(r)
    recs.sort(key=lambda r: r.name)
    out.append("two-frame S1-S4 records with an event: %d: %s" % (len(recs), ", ".join(
        "%s(spd %d, events %s)" % (r.name, r.speed, " ".join("%d:%d" % e for e in animdata.events_of(r)))
        for r in recs)))
    toks = sorted({r.name[:2] for r in recs})
    rows = classic = classic_flag = 0
    for i, r in enumerate(ms.rec):
        if r["Code"].upper() not in toks or ms.blank(i, "MonStatsEx"):
            continue
        rows += 1
        x = m2.rec[r["MonStatsEx"]]
        b = r["BaseId"] if 0 <= r["BaseId"] < len(ms.rec) else i
        bx = m2.rec[ms.rec[b]["MonStatsEx"]]
        wl = d.rec(ms.rec[b]["Code"] + d.mmode_tok[MON_MODES.index("WL")] + (bx["BaseW"] or "hth"))
        if wl is None:
            walk = "no WL record"
        else:
            v_i, v_b = r["Velocity"], ms.rec[b]["Velocity"]
            w = (v_i * wl.speed) // v_b if (b != i and v_b > 0) else wl.speed
            walk = "%d (%s spd %d%s)" % (min(w, 0x7FFF), wl.name, wl.speed,
                                         ", x %d/%d" % (v_i, v_b) if (b != i and v_b > 0) else "")
        named = []
        for k in smodes:
            m = MON_MODES[k]
            nm = (r["Code"] + d.mmode_tok[k] + (x["BaseW"] or "hth")).upper()
            if any(nm == q.name for q in recs):
                named.append("%s m%s %d %smv %d" % (nm, m, x["m" + m], m, x.get(m + "mv", 0)))
                if i < 410 and x["m" + m]:
                    classic_flag += 1
        classic += int(i < 410)
        out.append("  %3d %-18s Code %-3s class %s 410; base %3d %-18s; Velocity %2d Run %2d; npc %d; walk base %s; "
                   "%s" % (i, ids[i], r["Code"], "<" if i < 410 else ">=", b, ids[b], r["Velocity"], r["Run"],
                           int(bool(r["npc"])), walk, "; ".join(named) or "no S1-S4 record of the list"))
    kv["twoframe_records"] = len(recs)
    kv["twoframe_rows"] = rows
    kv["twoframe_rows_classic"] = classic
    kv["twoframe_classic_flagged"] = classic_flag
    return out, kv


SECTIONS = collections.OrderedDict([("players", sec_players), ("monsters", sec_monsters), ("objects", sec_objects),
                                    ("skills", sec_skills), ("monseq", sec_monseq), ("ratemin", sec_ratemin),
                                    ("twoframe", sec_twoframe)])


def main(argv):
    if len(argv) != 2 or argv[0] not in list(SECTIONS) + ["summary"]:
        print(__doc__)
        return 2
    d = Data(argv[1])
    kv = collections.OrderedDict()
    for name, fn in SECTIONS.items():
        lines, k = fn(d)
        kv.update(k)
        if argv[0] == name:
            print("\n".join(lines))
    if argv[0] == "summary":
        for k, v in kv.items():
            print("%-28s %d" % (k, v))
    print("SURVEY anim " + " ".join("%s=%d" % x for x in kv.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
