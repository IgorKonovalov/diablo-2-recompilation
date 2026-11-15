"""Plan 0066 batches S4c (items/inventory) and S4d (stats/aggregate, stats/README, stats/states): new checks over kept
logs, static second sources and full-table checks. No game run, no Ghidra.

Usage:
  python3 -I tools/sweep2_s4cd.py <section> [<section> ...]      # print the sections' lines
  python3 -I tools/sweep2_s4cd.py all                             # every section, in order

Sections (the inventory row each check serves is in its docstring):
  invlogs   the kept logs of run:2026-11-04-inventory (main) and run:2026-11-04-inventory-2 (pot, drops2, crowd)
  invstatic r2 and the raw-byte scan (tools/xrefscan.py) next to the objdump listings of run:2026-11-04-inventory-emu
            and run:2026-11-04-ground-emu (`static.txt`); the objdump walker of tools/sweep_s4b.py next to Ghidra's
            rngcallgraph (`rcg-*.txt`), with r2's own search for the LCG multiplier
  stlogs    the 18 logs of run:2026-10-17-stats (s1017-run.lst) and the 10 of run:2026-10-20-shortfalls (p47h-run.lst)
  ststatic  r2 and the raw-byte scan next to Ghidra's readings in stats/0001 and 0002; the objdump walker for draws
  tables    full-table checks over the excel .txt tables (Misc autobelt, Sets params, Skills aurastat, States bits)

Each section prints `S4 <section> <check> key=value ...` lines and detail lines; `bad=` counts an observation that
contradicts the statement the check tests. A statement with no stock case shows as a zero count, never as a failure.
The record is the "plan 0066 batches S4c and S4d" addenda of findings/items/experiments.md and
findings/stats/experiments.md.

Stdlib only, plus objdump (through tools/sweep_s4b.py) and r2 (radare2). Read-only.
"""
import base64
import bisect
import collections
import csv
import json
import os
import re
import struct
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as S  # noqa: E402

ROOT = S.ROOT
EXE = S.EXE
EXCEL = S.EXCEL
LOGS = S.LOGS
LCG_MUL = S.LCG_MUL
INV = os.path.join(LOGS, "inventory")
INV_LOGS = ["2026-11-04-inventory-s2-6001-main.log", "2026-11-04-inventory-2-s2-6001-pot.log",
            "2026-11-04-inventory-2-s2-6001-drops2.log", "2026-11-04-inventory-2-s2-6001-crowd.log"]
STATS = os.path.join(LOGS, "stats")


# ------------------------------------------------------------------------------------------------------------ helpers
class Rep:
    def __init__(self, sec, name):
        self.sec, self.name = sec, name
        self.c = collections.Counter()
        self.notes = []

    def add(self, k, n=1):
        self.c[k] += n

    def note(self, s):
        self.notes.append(s)

    def done(self):
        if "bad" not in self.c:
            self.c["bad"] += 0
        print("S4 %s %s %s" % (self.sec, self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        return self.c["bad"]


_FUNCS = None


def funcs():
    global _FUNCS
    if _FUNCS is None:
        out = []
        for ln in open(os.path.join(ROOT, "re", "symbols.csv")):
            f = ln.rstrip("\n").split(",")
            if len(f) > 2 and f[1] == "func":
                try:
                    out.append((int(f[0], 16), f[2]))
                except ValueError:
                    pass
        _FUNCS = sorted(out)
    return _FUNCS


def owner(va):
    """The nearest func symbol at or below va: (entry, name)."""
    F = funcs()
    i = bisect.bisect_right([a for a, _ in F], va) - 1
    return F[i] if i >= 0 else (0, "?")


def pad_entry(va):
    """The nearest address at or below va that follows int3 padding (0xCC) and is not itself 0xCC: an entry guess
    independent of re/symbols.csv."""
    data = S.image()[0]
    a = va
    while a > 0x401000:
        o = S.va_off(a)
        if data[o - 1] == 0xCC and data[o] != 0xCC:
            return a
        a -= 1
    return None


def raw(target):
    """(rel32 call/jmp sites, abs32 sites) of target from the raw bytes (tools/xrefscan.py)."""
    import xrefscan
    data = open(EXE, "rb").read()
    base, secs = xrefscan.sections(EXE)
    hits = xrefscan.scan(data, base, secs, target)
    rel = sorted(va for kind, va, _ in hits if not kind.startswith("abs"))
    calls = sorted(va for kind, va, _ in hits if kind.startswith("call"))
    ab = sorted(va for kind, va, _ in hits if kind.startswith("abs"))
    return rel, calls, ab


R2_CACHE = {}


def r2(cmd):
    if cmd not in R2_CACHE:
        R2_CACHE[cmd] = subprocess.run(["r2", "-q", "-e", "scr.color=0", "-e", "asm.bytes=false", "-e", "asm.lines=false",
                                        "-e", "asm.comments=false", "-e", "asm.xrefs=false", "-e", "asm.flags=false",
                                        "-c", cmd, EXE], capture_output=True, text=True).stdout
    return R2_CACHE[cmd]


R2_LINE = re.compile(r"^\s*0x([0-9a-f]{8})\s+(\S+)\s*(.*?)\s*$")


def r2_range(lo, hi):
    """[(va, mnemonic, operands)] from r2's linear disassembly of [lo, hi)."""
    out = []
    for ln in r2("pD %d @ 0x%x" % (hi - lo, lo)).splitlines():
        m = R2_LINE.match(ln)
        if m:
            out.append((int(m.group(1), 16), m.group(2), m.group(3)))
    return out


def r2_bytes(va, n):
    out = r2("p8 %d @ 0x%x" % (n, va)).strip()
    return bytes.fromhex(out)


def pushes_before(site, entry=None):
    """The push operands before the call at `site`, last push first (arg 0 first), stopping at an earlier call or
    ret, from r2's linear disassembly starting at the function's entry (the padded-block start)."""
    e = entry or pad_entry(site)
    ins = [x for x in r2_range(e, site + 1)]
    if not ins or ins[-1][0] != site:
        return None
    out = []
    for va, mn, ops in reversed(ins[:-1]):
        if mn in ("call", "ret", "retn"):
            break
        if mn == "push":
            out.append(ops)
    return out


def imm(s):
    s = s.strip()
    try:
        return int(s, 16) if s.startswith("0x") else int(s)
    except ValueError:
        return None


def jl(path):
    """(tag, dict) per JSON line of a logger file."""
    with open(path, errors="replace") as fh:
        for ln in fh:
            tag, _, rest = ln.partition(" ")
            if rest.startswith("{"):
                try:
                    yield tag, json.loads(rest)
                except ValueError:
                    continue


def unz(s):
    return json.loads(zlib.decompress(base64.b64decode(s)))


def r2_lcg_sites():
    """r2's own search for the multiplier's four bytes, each hit decoded by r2 (an instruction that holds it)."""
    hits = []
    for ln in r2("e search.in=bin.section.[x]; /x %s" % struct.pack("<I", LCG_MUL).hex()).splitlines():
        m = re.match(r"^0x([0-9a-f]+)", ln)
        if m:
            hits.append(int(m.group(1), 16))
    sites = set()
    for h in hits:
        # the instruction holding the immediate starts 2..6 bytes before it; take the decode r2 gives that covers h
        for back in range(1, 8):
            ins = r2_range(h - back, h + 4)
            if ins and ins[0][0] == h - back and "0x6ac690c5" in ins[0][2]:
                sites.add(h - back)
                break
    return sorted(hits), sorted(sites)


# ====================================================================================================== S4c: logs
def inv_events():
    for name in INV_LOGS:
        p = os.path.join(INV, name)
        for tag, d in jl(p):
            yield name, tag, d


def chk_invlogs():
    bad = 0
    # rows 3, 8, 29, 31, 61, 85, 88
    r3 = Rep("invlogs", "row3_monster_drop_caller")
    r8 = Rep("invlogs", "row8_modes")
    r29 = Rep("invlogs", "row29_61_pkt17")
    r31 = Rep("invlogs", "row31_pkt19")
    rsw = Rep("invlogs", "row85_88_sweep")
    for name in INV_LOGS:
        last_gdi = {}
        last_gdo = {}
        open17 = None
        open19 = None
        swp = []            # (frame, set of ids, [(id, e)])
        swf = []            # (frame, id, e)
        for tag, d in jl(os.path.join(INV, name)):
            th = d.get("th")
            if tag == "GDI":
                last_gdi[th] = d
                if open17 is not None:
                    open17["gdi"].append(d)
            elif tag == "GDO":
                last_gdo[th] = d
                if open17 is not None:
                    open17["gdo"].append(d)
            elif tag == "DCI":
                g = last_gdi.get(th)
                it = d["item"]
                r8.add("mode%d_dci_ground" % it["mode"])
                if it["mode"] != 3:
                    r8.add("bad")
                if g is None:
                    r3.add("no_gdi")
                    continue
                e, nm = owner(g["ret"])
                r3.add("drops")
                if e == 0x0055A550 and g["a1"] == 1 and g["a2"] == 1:
                    r3.add("via_DropCreateItem")
                else:
                    r3.add("bad")
                    r3.note("%s f=%d ret=0x%08X %s" % (name, d["f"], g["ret"], nm))
            elif tag in ("PKT", "PKR"):
                for ent in d.get("inv") or []:
                    if ent == "err":
                        continue
                    iid, cls, pg, x, y, mode = ent
                    if pg != 255:
                        k = "mode0_page%d" % pg
                        ok = mode == 0
                    elif mode == 1:
                        k, ok = "mode1_body", 1 <= x <= 10
                    elif mode == 2:
                        k, ok = "mode2_belt", 0 <= x <= 15
                    else:
                        k, ok = "mode%d_page255" % mode, False
                    r8.add(k)
                    if not ok:
                        r8.add("bad")
                if tag == "PKT" and d["op"] == 0x17:
                    open17 = {"pkt": d, "gdi": [], "gdo": [], "ipg": []}
                elif tag == "PKR" and d["op"] == 0x17 and open17 is not None:
                    o = open17
                    open17 = None
                    r29.add("pairs")
                    pk = bytes.fromhex(o["pkt"]["pkt"])
                    if pk[0] != 0x17:
                        r29.add("bad")
                    r29.add("eax%d" % d["eax"])
                    if len(o["gdi"]) != 1 or len(o["gdo"]) != 1 or len(o["ipg"]) != 1:
                        r29.add("shape_other")
                        r29.note("%s f=%d gdi=%d gdo=%d ipg=%d" % (name, d["f"], len(o["gdi"]), len(o["gdo"]),
                                                                     len(o["ipg"])))
                        continue
                    g, go, ip = o["gdi"][0], o["gdo"][0], o["ipg"][0]
                    ent, nm = owner(g["ret"])
                    ok = (ent == 0x00563C00 and g["a1"] == 1 and g["a2"] == 1 and go["room"] != 0
                          and ip["room"] == go["room"] and ip["x"] == go["x"] and ip["y"] == go["y"]
                          and ip["item"]["mode"] == 4 and ip["flag"] != 0)
                    ids_after = {e[0] for e in d["inv"] if e != "err"}
                    ids_before = {e[0] for e in o["pkt"]["inv"] if e != "err"}
                    held = ip["item"]["id"]
                    if held in ids_before or held in ids_after:
                        ok = False
                    if ids_before != ids_after:
                        r29.add("inv_list_changed")
                    if ok:
                        r29.add("cursordrop_search_place")
                    else:
                        r29.add("bad")
                        r29.note("%s f=%d ret=%s" % (name, d["f"], nm))
                    r8.add("mode4_cursor_at_place")
                    if ip["item"]["mode"] != 4:
                        r8.add("bad")
                if d["op"] == 0x19:
                    if tag == "PKT":
                        open19 = d
                    elif open19 is not None:
                        o, open19 = open19, None
                        r31.add("pairs")
                        pk = bytes.fromhex(o["pkt"])
                        guid = struct.unpack_from("<I", pk, 1)[0]
                        before = {e[0]: e for e in o["inv"] if e != "err"}
                        after = {e[0]: e for e in d["inv"] if e != "err"}
                        if guid in before:
                            r31.add("owned")
                            r31.add("page%d" % before[guid][2])
                            if before[guid][2] == 1:
                                r31.add("bad")
                        else:
                            r31.add("not_owned")
                        r31.add("eax%d" % d["eax"])
                        if guid not in after:
                            r31.add("left_list")     # the cursor item is not on Inventory +0x0C's list
                        if set(before) - {guid} != set(after):
                            r31.add("bad")
                            r31.note("%s f=%d other items changed" % (name, d["f"]))
            elif tag == "IPG":
                if open17 is not None:
                    open17["ipg"].append(d)
                if d["item"]["mode"] not in (3, 4):
                    pass
            elif tag == "IPX":
                r8.add("mode%d_after_place" % d["item"]["mode"])
                if d["item"]["mode"] != 3:
                    r8.add("bad")
            elif tag == "SWP":
                swp.append((d["f"], {it[0] for it in d["items"]}, [(it[0], it[3], it[2]) for it in d["items"]]))
                for it in d["items"]:
                    r8.add("mode%d_swept_list" % it[2])
                    if it[2] != 3:
                        r8.add("bad")
            elif tag == "SWF":
                swf.append((d["f"], d["item"]["id"], d["item"]["e"]))
        # sweep frames, frees and lag
        for f, ids, items in swp:
            rsw.add("sweeps")
            if f % 1500:
                rsw.add("bad")
                rsw.note("%s sweep at frame %d" % (name, f))
        freed = collections.defaultdict(list)
        for f, iid, e in swf:
            freed[f].append((iid, e))
            rsw.add("frees")
            lag = f - e
            if not (0 <= lag <= 1499) or f % 1500:
                rsw.add("bad")
                rsw.note("%s free f=%d e=%d" % (name, f, e))
            rsw.c["max_lag"] = max(rsw.c["max_lag"], lag)
            # listed at its own sweep's entry, and absent from every later sweep of the log
            here = [s for s in swp if s[0] == f]
            later = [s for s in swp if s[0] > f]
            if not here or iid not in here[0][1]:
                rsw.add("free_not_listed_at_entry")
            if any(iid in s[1] for s in later):
                rsw.add("bad")
                rsw.note("%s id %d freed at %d and listed later" % (name, iid, f))
            else:
                rsw.add("gone_from_later_sweeps")
            if later:
                rsw.add("later_sweep_exists")
        # every listed item with 0 < e <= f was freed at that sweep (only the type-4 units of the act listed)
        for f, ids, items in swp:
            fr = {i for i, _ in freed.get(f, [])}
            for iid, e, mode in items:
                if e and e <= f:
                    rsw.add("due_listed")
                    if iid not in fr:
                        rsw.add("bad")
                        rsw.note("%s id %d due e=%d at sweep %d not freed" % (name, iid, e, f))
                elif e:
                    rsw.add("not_due_listed")
                    if iid in fr:
                        rsw.add("bad")
                else:
                    rsw.add("zero_listed")
    for r in (r3, r8, r29, r31, rsw):
        bad += r.done()
    return bad


# ==================================================================================================== S4c: static
def rcg_summary(path):
    out = {}
    for ln in open(path):
        m = re.match(r"^0x([0-9A-Fa-f]+) \d+ summary: functions=(\d+) rng=(\d+) unclassified=(\d+) indirect=(\d+)", ln)
        if m:
            out[int(m.group(1), 16)] = tuple(int(m.group(k)) for k in range(2, 6))
    return out


def closure_check(rep, roots, rcg, lcg_sites):
    """Per root: the objdump walker's direct closure, its draws (inline LCG sites, calls of the RNG primitives), r2's
    LCG sites inside the walked bodies, and Ghidra's summary line."""
    A = S.asm()
    for r in roots:
        G = S.graph([r])
        R = S.rng_functions(G)
        vas = set()
        for e, v in G.items():
            vas |= v[2]
        r2in = sorted(s for s in lcg_sites if s in vas)
        gh = rcg.get(r)
        draws = sorted((hex(e), [hex(x) for x in v[0]], [(hex(s), n) for s, n in v[1]]) for e, v in R.items())
        rep.note("root 0x%08X objdump: functions=%d draw_functions=%d r2_lcg_in_bodies=%d %s | ghidra: %s" % (
            r, len(G), len(R), len(r2in), draws, "functions=%d rng=%d indirect=%d" % (gh[0], gh[1], gh[3]) if gh else "-"))
        rep.add("roots")
        if gh is not None and (gh[1] > 0) != (len(R) > 0):
            rep.add("bad")
        if r2in:
            rep.add("bad")
        rep.add("draw_functions", len(R))


def chk_invstatic():
    bad = 0
    A = S.asm()
    # row 2: the packet table rows of the moves
    rp = Rep("invstatic", "row2_packet_table")
    spec = {0x17: 0x0054AB40, 0x18: 0x0054ABB0, 0x19: 0x0054ACD0, 0x1F: 0x0054B0F0, 0x21: 0x0054B300,
            0x22: 0x0054B380, 0x23: 0x0054B3E0, 0x24: 0x0054B450, 0x25: 0x0054B4E0, 0x63: 0x0054D520}
    rows = {}
    for op in list(range(0x17, 0x20)) + list(range(0x21, 0x26)) + [0x63]:
        w = r2("pxw 8 @ 0x%x" % (0x006E0D18 + 8 * op)).split()
        h, f = int(w[1], 16), int(w[2], 16)
        rows[op] = (h, f)
        rp.add("rows")
        if op in spec and spec[op] != h:
            rp.add("bad")
        e, nm = owner(h)
        rp.note("op 0x%02X -> 0x%08X flag %d (%s)" % (op, h, f, nm if e == h else "no symbol at entry"))
    for op in (0x1A, 0x1B, 0x1C, 0x1D, 0x1E):
        rp.add("equip_rows_handler_in_text", int(0x00401000 <= rows[op][0] < 0x006CB000))
    rp.done()
    bad += rp.c["bad"]

    # rows 5, 6: the page sizes in the image
    rg = Rep("invstatic", "row5_6_page_sizes")
    b0 = r2_bytes(0x0074479C, 2)
    b1 = r2_bytes(0x007447B4, 2)
    rg.note("0x0074479C: width %d height %d; 0x007447B4: width %d height %d" % (b0[0], b0[1], b1[0], b1[1]))
    if (b0[0], b0[1]) != (13, 1) or (b1[0], b1[1]) != (16, 1):
        rg.add("bad")
    pg = [x for x in r2_range(0x0063ADD0, 0x0063AE40)]
    for va, mn, ops in pg:
        if "0x744794" in ops or "0x74479c" in ops or "0x7447a0" in ops or "shl" == mn or "add" == mn and "2" in ops:
            rg.note("InvPageGet 0x%08X %s %s" % (va, mn, ops))
    rg.done()
    bad += rg.c["bad"]

    # rows 4, 79, 80, 90, 100: the direct callers of the search, the pair form and the placement, with their pushes
    for row, tgt, want in (("row4_79_search", 0x00555DA0, 20), ("row80_100_pair_form", 0x0064E810, 7),
                           ("row90_place", 0x00558AA0, 12)):
        rx = Rep("invstatic", row)
        rel, calls, ab = raw(tgt)
        r2x = [int(m.group(1), 16) for m in re.finditer(r"0x([0-9a-f]+) \[CALL", r2("aa 2>/dev/null; axt @ 0x%x" % tgt))] \
            if False else []
        rx.add("raw_calls", len(calls))
        rx.add("raw_other_rel", len(rel) - len(calls))
        rx.add("abs32", len(ab))
        if len(calls) != want or len(rel) != len(calls) or ab:
            rx.add("bad")
        for s in calls:
            p = pushes_before(s)
            e, nm = owner(s)
            pe = pad_entry(s)
            rx.note("site 0x%08X in %s (pad entry 0x%08X) pushes %s" % (s, nm, pe or 0, p))
            if tgt == 0x00555DA0:
                # GroundDropCell(ECX room, EDX pos; out, size, fallback): the pushes after the out pointer
                if p is None or len(p) < 3 or imm(p[1]) != 1 or imm(p[2]) != 1:
                    rx.add("bad")
                else:
                    rx.add("size1_fallback1")
        rx.done()
        bad += rx.c["bad"]

    # row 18: the record readers' set argument
    rr = Rep("invstatic", "row18_record_readers")
    for tgt, nm in ((0x0065C1F0, "inventory"), (0x00660CB0, "belts")):
        rel, calls, ab = raw(tgt)
        lit0_hi, other_lo, other = 0, 0, []
        for s in calls:
            p = pushes_before(s)
            st = p[1] if p and len(p) > 1 else None
            lit = imm(st) if st else None
            if s >= 0x00500000:
                if lit == 0:
                    lit0_hi += 1
                else:
                    other.append("0x%08X:%s" % (s, st))
            else:
                if lit is None:
                    other_lo += 1
                else:
                    other.append("0x%08X:%s" % (s, st))
        rr.note("%s 0x%08X: calls %d (rel %d abs %d); at or above 0x00500000 with a literal 0 set: %d; below 0x00500000 "
                "with a register or memory set: %d; other: %s" % (nm, tgt, len(calls), len(rel), len(ab), lit0_hi,
                                                                  other_lo, other))
        rr.add("%s_calls" % nm, len(calls))
        rr.add("%s_hi_literal0" % nm, lit0_hi)
        rr.add("%s_lo_nonliteral" % nm, other_lo)
        if other:
            rr.add("bad")
    rr.done()
    bad += rr.c["bad"]

    # row 16: the page row's server callers listed in A1 push [reg + 0x70] as the third argument
    ra = Rep("invstatic", "row16_rowfor_expansion")
    rel, calls, ab = raw(0x00621050)
    ra.add("rowfor_calls", len(calls))
    for s in (0x00560297, 0x00560598, 0x0054D658):
        p = pushes_before(s)
        third = p[2] if p and len(p) > 2 else None
        ins = r2_range(s - 0x20, s)
        src = [o for va, mn, o in ins if mn == "mov" and third and o.startswith(third + ",")]
        ra.note("site 0x%08X pushes %s; the third's load %s" % (s, p, src[-1:] if src else "-"))
        if not (src and "+ 0x70]" in src[-1]):
            ra.add("bad")
        else:
            ra.add("plus70")
    ra.done()
    bad += ra.c["bad"]

    # row 21: the three search bodies, call displacements masked
    rb = Rep("invstatic", "row21_three_bodies")
    bodies = []
    for e in (0x0063B790, 0x0063B7D0, 0x0063B810):
        ins = r2_range(e, e + 0x40)
        end = next(va for va, mn, o in ins if mn in ("ret", "retn"))
        n = next(va for va, mn, o in r2_range(end, end + 8) if va > end) - e
        b = bytearray(r2_bytes(e, n))
        for va, mn, o in ins:
            if va < e + n and mn == "call":
                off = va - e
                b[off + 1:off + 5] = b"\0\0\0\0"
        bodies.append(bytes(b))
        rb.note("0x%08X: %d bytes, %s" % (e, n, [("0x%08X" % va, mn, o) for va, mn, o in ins if mn == "call"]))
    if not (bodies[0] == bodies[1] == bodies[2]):
        rb.add("bad")
    rb.add("bytes", len(bodies[0]))
    rb.done()
    bad += rb.c["bad"]

    # rows 35, 60: the 0x22 handler and the stub
    rs = Rep("invstatic", "row35_60_unstack")
    stub = r2_range(0x0055E9A0, 0x0055E9A5)
    rs.note("stub %s" % stub)
    if [(m, o) for _, m, o in stub] != [("xor", "eax, eax"), ("ret", "8")]:
        rs.add("bad")
    h = r2_range(0x0054B380, 0x0054B3E0)
    calls = [(hex(va), o) for va, mn, o in h if mn == "call"]
    rets = [(hex(va), o) for va, mn, o in h if mn.startswith("ret")]
    rs.note("handler calls %s rets %s" % (calls, rets))
    rs.note("handler %s" % ["0x%08X %s %s" % x for x in h])
    rs.done()
    bad += rs.c["bad"]

    # row 78: the field loader's halving of the 256
    rl = Rep("invstatic", "row78_field_loader")
    for va in (0x0066A344, 0x0066A3E0, 0x0066A61C):
        ins = r2_range(va - 6, va + 10)
        rl.note("0x%08X: %s" % (va, [(hex(a), m, o) for a, m, o in ins]))
    rl.done()

    # rows 76, 93, 94, 95: the closures
    rcg = {}
    for d in ("r60c", "r60b"):
        p = os.path.join(LOGS, d, "emu", "rcg-summary.txt")
        if os.path.exists(p):
            rcg.update(rcg_summary(p))
    hits, sites = r2_lcg_sites()
    oi, oraw = S.lcg_scan()
    rc = Rep("invstatic", "row76_93_95_closures")
    rc.note("LCG multiplier: r2 /x hits %d, r2-decoded sites %d; objdump instruction sites %d, raw bytes %d; "
            "r2 sites == objdump sites: %s" % (len(hits), len(sites), len(oi), len(oraw), sites == oi))
    if sites != oi:
        rc.add("bad")
    closure_check(rc, [0x00555DA0, 0x0066A670, 0x00558A10, 0x00641530, 0x00558AA0, 0x0063C600, 0x0063B950], rcg, sites)
    # row 95: the one step of the placement's closure
    for va, mn, o in r2_range(0x00624550, 0x006245A8):
        if mn in ("call", "cmp", "je", "jne") or va in (0x00624563, 0x0062459D):
            rc.note("UNIT_AnimInit 0x%08X %s %s" % (va, mn, o))
    rc.done()
    bad += rc.c["bad"]

    # row 97: the move bodies, own bodies only
    rm = Rep("invstatic", "row97_move_bodies")
    moves = [0x00563C00, 0x00560200, 0x00560420, 0x005606B0, 0x00563D20, 0x00560CD0, 0x00560F00, 0x00561220,
             0x00561B00, 0x0055E7C0, 0x0055E9B0, 0x00562250, 0x0055EB30]
    for e in moves:
        vas, cl, ic = S.body(A, e)
        lcg, rc_ = S.rng_sites(A, vas)
        r2l = [s for s in sites if s in vas]
        rm.add("bodies")
        if lcg or rc_ or r2l:
            rm.add("bad")
        rm.note("0x%08X %s: %d instructions, %d direct calls, %d indirect, lcg %s rng calls %s r2 %s" % (
            e, owner(e)[1], len(vas), len(cl), len(ic), lcg, rc_, r2l))
    rm.done()
    bad += rm.c["bad"]

    # row 82: inline steps in the 20 callers' bodies of the search
    rd = Rep("invstatic", "row82_callers_draws")
    rel, calls, ab = raw(0x00555DA0)
    seen = set()
    for s in calls:
        e = pad_entry(s)
        if e in seen:
            continue
        seen.add(e)
        vas, cl, ic = S.body(A, e)
        if s not in vas:
            rd.add("site_outside_walked_body")
        lcg, rc_ = S.rng_sites(A, vas)
        r2l = [x for x in sites if x in vas]
        rd.add("caller_bodies")
        if lcg or r2l:
            rd.add("with_inline_step")
            rd.note("0x%08X %s: lcg %s r2 %s rng calls %s" % (e, owner(e)[1], [hex(x) for x in lcg],
                                                              [hex(x) for x in r2l], rc_))
        elif rc_:
            rd.note("0x%08X %s: rng calls only %s" % (e, owner(e)[1], rc_))
    rd.done()
    bad += rd.c["bad"]
    return bad


# ============================================================================================================== main
SECTIONS = {"invlogs": chk_invlogs, "invstatic": chk_invstatic}   # checkpoint: stlogs, ststatic, tables not yet written


def main(argv):
    names = list(SECTIONS) if argv[1:] == ["all"] else argv[1:]
    if not names or any(n not in SECTIONS for n in names):
        print(__doc__)
        return 2
    bad = 0
    for n in names:
        bad += SECTIONS[n]()
    print("S4 total bad=%d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
