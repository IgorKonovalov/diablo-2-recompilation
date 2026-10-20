#!/usr/bin/env python3
"""Checks of plan 0044 Phase 2 (two clients, ADR-0008) that no earlier checker covers.

    python3 -I tools/mp_check.py xpshare <log> [<log> ...] [-v]
    python3 -I tools/mp_check.py gates <log> [<log> ...] [-v]
    python3 -I tools/mp_check.py aura <log> [<log> ...]
    python3 -I tools/mp_check.py quests <log> [--word W --join-bits B,B|none --host-bits B,B]

xpshare: the party share of kill experience (docs/findings/player/0001-creation.md, the Party bullet; spec
docs/specs/player/creation.md J4; case MP16 of docs/findings/multiplayer/0001-cases.md), from a host log of
tools/gdb/two-kills.gdb. For every XP_OnMonsterKill (the PLRK line of tools/gdb/two-players.py, then the XK0 line of
tools/gdb/player.py, both at 0x0057E990) it predicts, from the logged players before the kill:
  - the credited player: the killer when it is a player (XK0 ktype 0); a monster killer (a minion) is counted and
    not predicted;
  - the members XP_PartyShare collects: the credited player alone when it is in no party; else every member of its
    party that is alive (dead bit 0), in the same level id and within squared distance 6400 (sub-tiles) of the
    credited player, the credited player included;
  - the XP_Compute calls that follow (XC0 lines on the same thread, up to the next XK0): one per member, each on that
    member's unit (PLRS "u" = XC0 "unit"); with one member the input experience is the monster's experience (its base
    stat 13 in XK0 "mb"); with n >= 2, total = E + ((n - 1) * E * 89) // 256 (signed 32-bit), q = (f32) total /
    (f32) sum of the members' levels (each XC0's clvl), and member i's input = trunc(level_i * q). The product is
    taken exactly (x87) and, as a separate count, the cases where rounding it to f32 first would give another value.
What XP_Compute and PLAYER_AddExperience do with each input is tools/player.py check's (the same log).

gates: case MP24 (docs/findings/multiplayer/0001-cases.md § 4), from a host log with tools/gdb/two-players.py's
HD0..GPP lines and its PLRS lines (each player's PlayerData +0x160 "tk" and pair list "hl"):
  - the declaration (HD0): an early refusal (HDO) is counted with the declarer's level id (a town or not); the pair
    stamp compare (HDR) refuses iff stamp > now (u32); after a refusal no HDS follows; after a pass, HDS's stamp is
    now' + 60000 with now' >= HDR's now, the declarer's next logged tk lies in [now', now' + 1000] and its pair entry
    for the other player holds the stamp;
  - the waypoint gate (GW): lim = the player's last logged tk + 10000 (u32), and the outcome line (GWR refused, GWP
    passed) is the one lim > now predicts;
  - the portal operate: PH (hostile to any) then, when non-zero, PO (operator id vs owner id): a hostile operator that
    does not own the portal is refused before the gate, so no GP follows; else GP: lim = tk + 5000, outcome as above.
aura: case MP25 (multiplayer/0001 § 4, *MP25 prediction*), from the AF lines of tools/gdb/two-players.py (a player
  source's SkillUnitFilter result on another player): with the target alive (mode not 0 or 0x11) and outside town (its
  logged level id not a town), a filter with 0x10000 passes iff the two share a party (PLRS "pty"), and one with 0x8000
  passes iff the pair is hostile (from the HD0/HDS lines: hostile after an HDS of the pair, neutral after an HD0
  hostile=0 of either side); the other bits are not modelled here, so a line whose filter has neither is only counted.
quests: whose quest record each quest-bit write (QS set / QC clear of tools/gdb/quests.py) touches, from the PLRS "qr"
  pointers (PlayerData +0x10 + 4 * difficulty, QUESTS_PlayerRecord 0x00543520), with both players' presence at the
  write; with --word, the bits set in that word on each player's record are compared with --host-bits / --join-bits
  (a case's prediction, e.g. MP28 (a): the Den of Evil's word 1 bits 1 and 13 on the partied joiner's record).
Prints one SURVEY line per check; exit 1 on any mismatch. Stdlib only; reads only the logs named.
"""
import collections
import json
import struct
import sys

PARTY_D2 = 6400


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def i32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def ftol(x):
    return int(x)          # CRT_ftol2 truncates toward zero


def share_inputs(E, levels):
    """The XP_Compute inputs J4 predicts for the members' levels (in any order); and, per member, whether rounding
    the product to f32 before the truncation would change it."""
    n = len(levels)
    if n == 1:
        return [E], [False]
    total = i32(E + i32((n - 1) * E * 89) // 256) if E >= 0 else i32(E + -((-(n - 1) * E * 89) // 256))
    q = f32(f32(total) / f32(sum(levels)))
    out, sep = [], []
    for lv in levels:
        exact = ftol(float(lv) * q)
        out.append(exact)
        sep.append(ftol(f32(float(lv) * q)) != exact)
    return out, sep


def events(path):
    with open(path, errors="replace") as f:
        for line in f:
            tag, _, rest = line.rstrip("\n").partition(" ")
            if tag not in ("PLRK", "XK0", "XC0", "XA0"):
                continue
            try:
                yield tag, json.loads(rest)
            except ValueError:
                continue


def stat(entries, sid):
    for s, p, v in entries or []:
        if s == sid and p == 0:
            return v
    return None


def check_xpshare(paths, verbose):
    S = collections.Counter()
    bad = []
    for path in paths:
        snap = None
        open_k = None

        def close(k):
            if k is None:
                return
            S["kills (XK0)"] += 1
            if k["skip"]:
                S["  not predicted: %s" % k["skip"]] += 1
                return
            want = k["members"]
            got = k["xc"]
            ids_by_u = k["ids_by_u"]
            got_ids = sorted(ids_by_u.get(x["unit"], "u%x" % x["unit"]) for x in got)
            if sorted(want) != got_ids:
                bad.append("%s: kill of monster %s by %s: members predicted %s, XP_Compute on %s (%s)" % (
                    path, k["mid"], k["kid"], sorted(want), got_ids, k["why"]))
                return
            S["  members predicted = XP_Compute calls"] += 1
            S["  n = %d (%s)" % (len(want), k["kind"])] += 1
            levels = [x["clvl"] for x in got]
            pred, sep = share_inputs(k["E"], levels)
            for x, p, s in zip(got, pred, sep):
                if x["exp"] != p:
                    bad.append("%s: kill of monster %s: member %s level %d: XP_Compute input %d, predicted %d (E %d, "
                               "levels %s)" % (path, k["mid"], ids_by_u.get(x["unit"]), x["clvl"], x["exp"], p, k["E"],
                                               levels))
                else:
                    S["  XP_Compute inputs predicted" + (" (party share, n >= 2)" if len(want) > 1 else "")] += 1
                if s:
                    S["  f32-rounded product would differ (separates the x87 reading)"] += 1
            if verbose and len(want) > 1:
                print("share: monster %s E %d levels %s -> %s" % (k["mid"], k["E"], levels, [x["exp"] for x in got]))

        for tag, d in events(path):
            if tag == "PLRK":
                snap = d
                continue
            if tag == "XK0":
                close(open_k)
                open_k = {"mid": d.get("mid"), "kid": d.get("kid"), "xc": [], "skip": None, "members": [],
                          "ids_by_u": {}, "kind": "", "why": "", "th": d.get("th")}
                E = stat(d.get("mb"), 13)
                open_k["E"] = E
                if d.get("ktype") != 0:
                    open_k["skip"] = "killer not a player (ktype %s)" % d.get("ktype")
                    continue
                if snap is None:
                    open_k["skip"] = "no PLRK before the kill"
                    continue
                if E is None:
                    open_k["skip"] = "no monster experience (stat 13)"
                    continue
                pl = {e["id"]: e for e in snap["p"]}
                open_k["ids_by_u"] = {e.get("u"): e["id"] for e in snap["p"]}
                me = pl.get(d["kid"])
                if me is None:
                    open_k["skip"] = "credited player not in PLRK"
                    continue
                party = next((p["m"] for p in snap.get("pty", []) if me["id"] in p["m"]), None)
                if party is None:
                    open_k["members"] = [me["id"]]
                    open_k["kind"] = "not partied"
                    open_k["why"] = "no party"
                    continue
                mem, why = [], []
                for uid in party:
                    e = pl.get(uid)
                    if e is None:
                        why.append("%s not listed" % uid)
                        continue
                    if uid == me["id"]:
                        mem.append(uid)
                        continue
                    d2 = None if e["x"] is None or me["x"] is None else \
                        (e["x"] - me["x"]) ** 2 + (e["y"] - me["y"]) ** 2
                    if e["dead"] or e.get("mode") in (0, 17):
                        why.append("%s dead" % uid)
                        kind = "partied, other member dead"
                    elif e["lid"] != me["lid"]:
                        why.append("%s in level %s" % (uid, e["lid"]))
                        kind = "partied, other member in another level"
                    elif d2 is None or d2 > PARTY_D2:
                        why.append("%s at d2 %s" % (uid, d2))
                        kind = "partied, other member beyond d2 6400"
                    else:
                        mem.append(uid)
                        why.append("%s at d2 %d" % (uid, d2))
                        kind = "partied, other member alive, same level, d2 <= 6400"
                    S["  pair: " + kind] += 1
                    if d2 is not None and e["lid"] == me["lid"] and not e["dead"] and 5600 <= d2 <= 7200:
                        S["  pair within 800 of the 6400 bound (d2 %s)" % ("<= 6400" if d2 <= PARTY_D2 else "> 6400")] += 1
                open_k["members"] = mem
                open_k["kind"] = "partied"
                open_k["why"] = "; ".join(why)
                continue
            if tag == "XC0" and open_k is not None and d.get("th") == open_k["th"]:
                open_k["xc"].append(d)
        close(open_k)
    for b in bad[:30]:
        print("MISMATCH " + b)
    print("SURVEY mp_check xpshare logs=%d %s mismatches=%d" % (
        len(paths), " ".join("%s=%d" % (k.strip().replace(" ", "_"), v) for k, v in sorted(S.items())), len(bad)))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad else 0


TOWNS = {1, 40, 75, 103, 109}
M32 = 0xFFFFFFFF


def check_gates(paths, verbose):
    S = collections.Counter()
    bad = []
    for path in paths:
        tk, hl, lid = {}, {}, {}
        pend = None         # the open declaration or gate: dict with "kind"
        after_hds = []      # (player, now', stamp, other) waiting for the next PLRS

        def fail(msg):
            bad.append("%s: %s" % (path, msg))

        with open(path, errors="replace") as f:
            for line in f:
                tag, _, rest = line.rstrip("\n").partition(" ")
                if tag not in ("PLRS", "PLRK", "HD0", "HDR", "HDS", "HDO", "GW", "GWR", "GWP", "PH", "PO", "GP",
                               "GPR", "GPP"):
                    continue
                try:
                    d = json.loads(rest)
                except ValueError:
                    continue
                if tag in ("PLRS", "PLRK"):
                    for e in d["p"]:
                        tk[e["id"]] = e.get("tk")
                        hl[e["id"]] = {a: b for a, b in e.get("hl") or []}
                        lid[e["id"]] = e.get("lid")
                    for w in list(after_hds):
                        p, now1, stamp, o = w
                        if tk.get(p) is None:
                            continue
                        after_hds.remove(w)
                        if not (now1 <= tk[p] <= now1 + 1000):
                            fail("declaration by %s: +0x160 = %s, expected in [%d, %d]" % (p, tk[p], now1, now1 + 1000))
                        elif hl.get(p, {}).get(o) != stamp:
                            fail("declaration by %s: pair entry for %s = %s, expected the stamp %d" % (
                                p, o, hl.get(p, {}).get(o), stamp))
                        else:
                            S["declaration: +0x160 <- now and the pair stamp, as logged after"] += 1
                    continue
                if tag == "HD0":
                    S["declarations (HD0, hostile=%d)" % d["hostile"]] += 1
                    pend = {"kind": "hd", "p": d["p"], "o": d["o"], "hostile": d["hostile"]}
                    continue
                if tag == "HDO":
                    where = "in a town" if pend and lid.get(pend["p"]) in TOWNS else "outside town"
                    S["declaration refused early (town or level < 9), declarer %s" % where] += 1
                    pend = None
                    continue
                if tag == "HDR":
                    refused = d["stamp"] > d["now"]
                    pend = {"kind": "hdr", "p": d["p"], "o": d["o"], "refused": refused, "now": d["now"]}
                    S["pair-stamp compare: %s" % ("refused (stamp > now)" if refused else "passed")] += 1
                    if refused:
                        S["  refused %d ms before the 60 s stamp" % 0] += 0
                    continue
                if tag == "HDS":
                    if not pend or pend.get("kind") != "hdr":
                        S["HDS without HDR (first declaration of the pair)"] += 0
                        now0 = None
                    else:
                        now0 = pend["now"]
                        if pend["refused"]:
                            fail("HDS after a refused compare (p %s)" % d["p"])
                    now1 = (d["stamp"] - 60000) & M32
                    if now0 is not None and not (now0 <= now1 <= now0 + 1000):
                        fail("HDS stamp %d: now' %d not just after HDR's now %d" % (d["stamp"], now1, now0))
                    else:
                        S["new pair stamp = now + 60000"] += 1
                    after_hds.append((d["p"], now1, d["stamp"], d["o"]))
                    pend = None
                    continue
                if tag in ("GW", "GP"):
                    wait = 10000 if tag == "GW" else 5000
                    t = tk.get(d["id"])
                    if t is None:
                        fail("%s: no logged tk for player %s" % (tag, d["id"]))
                    elif (t + wait) & M32 != d["lim"]:
                        fail("%s: lim %d, predicted tk %d + %d" % (tag, d["lim"], t, wait))
                    else:
                        S["%s gate: lim = tk + %d" % ("waypoint" if tag == "GW" else "portal", wait)] += 1
                    pend = {"kind": tag, "refused": d["lim"] > d["now"], "tk": t, "now": d["now"]}
                    continue
                if tag in ("GWR", "GWP", "GPR", "GPP"):
                    kind = "GW" if tag[1] == "W" else "GP"
                    if not pend or pend.get("kind") != kind:
                        fail("%s without its compare line" % tag)
                        continue
                    got = tag.endswith("R")
                    if got != pend["refused"]:
                        fail("%s: outcome %s, predicted %s" % (kind, tag, "refused" if pend["refused"] else "passed"))
                    else:
                        since = "never declared" if not pend["tk"] else "%d ms after the declaration" % (
                            (pend["now"] - pend["tk"]) & M32)
                        S["%s gate %s as predicted (%s)" % ("waypoint" if kind == "GW" else "portal",
                                                            "refused" if got else "passed",
                                                            "never declared" if not pend["tk"] else
                                                            ("within" if got else "after") + " the wait")] += 1
                        if verbose:
                            print("%s %s: %s" % (kind, tag, since))
                    pend = None
                    continue
                if tag == "PH":
                    pend = {"kind": "ph", "id": d["id"], "hostile": d["hostile"]}
                    S["portal operate: hostile to any = %s" % ("yes" if d["hostile"] else "no")] += 1
                    continue
                if tag == "PO":
                    if not pend or pend.get("kind") != "ph" or not pend["hostile"]:
                        fail("PO without a hostile PH")
                        continue
                    own = d["op"] == d["owner"]
                    S["portal operate by a hostile player: %s" % ("its own portal" if own else "another's portal")] += 1
                    pend = {"kind": "po", "own": own}
                    continue
        # a hostile operator on another's portal must not reach the gate: checked as a PO followed by a GP
    # second pass for the PO -> GP order
    for path in paths:
        last = None
        with open(path, errors="replace") as f:
            for line in f:
                tag = line.split(" ", 1)[0]
                if tag == "PO":
                    d = json.loads(line.split(" ", 1)[1])
                    last = "own" if d["op"] == d["owner"] else "other"
                elif tag == "GP":
                    if last == "other":
                        bad.append("%s: a hostile operator on another's portal reached the gate" % path)
                    last = None
                elif tag == "PH":
                    if last == "other":
                        S["hostile operator on another's portal refused before the gate"] += 1
                    last = None
        if last == "other":
            S["hostile operator on another's portal refused before the gate"] += 1
    for b in bad[:30]:
        print("MISMATCH " + b)
    S = collections.Counter({k: v for k, v in S.items() if v})
    print("SURVEY mp_check gates logs=%d mismatches=%d" % (len(paths), len(bad)))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad else 0


def check_aura(paths):
    S = collections.Counter()
    bad = []
    for path in paths:
        players, pty, hostile = {}, [], set()
        with open(path, errors="replace") as f:
            for n, line in enumerate(f, 1):
                tag, _, rest = line.rstrip("\n").partition(" ")
                if tag not in ("PLRS", "PLRK", "HD0", "HDS", "AF"):
                    continue
                try:
                    d = json.loads(rest)
                except ValueError:
                    continue
                if tag in ("PLRS", "PLRK"):
                    players = {e["id"]: e for e in d["p"]}
                    pty = d.get("pty", [])
                    continue
                if tag == "HDS":
                    hostile.add(frozenset((d["p"], d["o"])))
                    continue
                if tag == "HD0":
                    if not d["hostile"]:
                        hostile.discard(frozenset((d["p"], d["o"])))
                    continue
                t = players.get(d["tgt"])
                if t is None or t.get("mode") in (0, 0x11) or t.get("lid") in TOWNS:
                    S["AF lines not predicted (target dead, in town or not listed)"] += 1
                    continue
                same = any(d["src"] in p["m"] and d["tgt"] in p["m"] for p in pty)
                hos = frozenset((d["src"], d["tgt"])) in hostile
                fl, got = d["filter"], bool(d["pass"])
                if fl & 0x10000:
                    want, why = same, "0x10000 (same party)"
                elif fl & 0x8000:
                    want, why = hos, "0x8000 (hostile)"
                else:
                    S["AF lines, filter 0x%X without 0x10000 or 0x8000 (counted only)" % fl] += 1
                    continue
                state = "partied" if same else ("hostile" if hos else "neither")
                if want != got:
                    bad.append("%s:%d: filter 0x%X, %s: pass %s, predicted %s" % (path, n, fl, state, got, want))
                else:
                    S["filter 0x%X %s: %s, %s as predicted" % (fl, why, state, "passed" if got else "refused")] += 1
    for b in bad[:30]:
        print("MISMATCH " + b)
    print("SURVEY mp_check aura logs=%d mismatches=%d" % (len(paths), len(bad)))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad else 0


def check_quests(paths, word, expect):
    S = collections.Counter()
    bad = []
    for path in paths:
        owner, present, roles, order = {}, set(), {}, []
        sets = collections.defaultdict(set)
        with open(path, errors="replace") as f:
            for line in f:
                tag, _, rest = line.rstrip("\n").partition(" ")
                if tag not in ("PLRS", "PLRK", "QS", "QC"):
                    continue
                try:
                    d = json.loads(rest)
                except ValueError:
                    continue
                if tag in ("PLRS", "PLRK"):
                    present = set()
                    for e in d["p"]:
                        if e["id"] not in order:
                            order.append(e["id"])
                        present.add(e["id"])
                        for r in e.get("qr") or []:
                            if r:
                                owner[r] = e["id"]
                    continue
                pid = owner.get(d["rec"])
                role = "unknown record" if pid is None else ("host" if pid == order[0] else "joiner")
                both = len(present) >= 2
                S["%s writes on the %s's record%s" % (tag, role, ", both players present" if both else "")] += 1
                S["  word %d bit %d %s on the %s's record" % (d["w"], d["b"], "set" if tag == "QS" else "cleared",
                                                               role)] += 1
                if tag == "QS" and pid is not None:
                    sets[(role, d["w"])].add(d["b"])
        if word is not None:
            for role in ("host", "joiner"):
                want = expect.get(role)
                if want is None:
                    continue
                got = sets.get((role, word), set())
                if set(want) != got:
                    bad.append("%s: word %d on the %s's record: bits set %s, predicted %s" % (
                        path, word, role, sorted(got), sorted(want)))
                else:
                    S["prediction held: word %d bits %s on the %s's record" % (word, sorted(want) or "none", role)] += 1
    for b in bad:
        print("MISMATCH " + b)
    print("SURVEY mp_check quests logs=%d mismatches=%d" % (len(paths), len(bad)))
    for k, v in sorted(S.items()):
        print("  %-90s %d" % (k, v))
    return 1 if bad else 0


def main(argv):
    if len(argv) >= 3 and argv[1] == "aura":
        return check_aura(argv[2:])
    if len(argv) >= 3 and argv[1] == "quests":
        args, word, expect, k = [], None, {}, 2
        while k < len(argv):
            a = argv[k]
            if a == "--word":
                word, k = int(argv[k + 1]), k + 2
            elif a in ("--join-bits", "--host-bits"):
                v = argv[k + 1]
                expect["joiner" if a == "--join-bits" else "host"] = [] if v == "none" else [int(x) for x in v.split(",")]
                k += 2
            else:
                args.append(a)
                k += 1
        return check_quests(args, word, expect)
    if len(argv) >= 3 and argv[1] == "gates":
        return check_gates([a for a in argv[2:] if a != "-v"], "-v" in argv)
    if len(argv) < 3 or argv[1] not in ("xpshare",):
        print(__doc__)
        return 2
    verbose = "-v" in argv
    paths = [a for a in argv[2:] if a != "-v"]
    return check_xpshare(paths, verbose)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
