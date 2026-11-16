#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2be (`lane/n66sb`): the route reads behind the batch's catalogue rows (ruling R2,
ADR-0021, ADR-0029). The rows are the plan 0046 catalogue's `after:` parts: code past an observed boundary. Ruling R2
admits them as c-emu only when the callee runs whole on a declared read set; a callee that allocates, spawns or walks
rooms sends the row to the harness (b).

    python3 -I tools/skills_s2be_routes.py sites [--depth N]   per root: each direct call site, its callee's name
                                                                (re/symbols.csv) and whether the callee reaches the
                                                                pool allocator/free or an import within the depth
    python3 -I tools/skills_s2be_routes.py rows [--depth N]    per row: the gate call(s) on the claim's route (the
                                                                call the claim lies after), the callee's first pool
                                                                path, and the branches that land between the gate
                                                                and the claim's first address from outside that span
                                                                (none: every path to the claim crosses the gate)

The direct-call walker is tools/sweep2_s7e_routes.py's over tools/sweep_s4b.py's objdump bodies (indirect calls
counted, not followed), cut at the pool entries (0x0040B430, 0x0040B4B0, the free 0x0040B480, EventBlockNew
0x00540BB0) and the fatal handlers. A listing says which callees a route reaches; that a case reaches the gate is the
branch's reading, cited per row in the finding. Stdlib only, plus the objdump binary. Read-only.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as W  # noqa: E402
import sweep2_s7e_routes as R  # noqa: E402

ROOTS = [   # (entry, catalogue inventory rows)
    (0x005AE780, "13"), (0x005A9820, "15"), (0x005AEDA0, "16"), (0x005AF170, "17"), (0x005AF300, "18, 19"),
    (0x005B0940, "20"), (0x005AD8F0, "20"), (0x005AD910, "20"), (0x005AF540, "21"), (0x005AF620, "22"),
    (0x005B01F0, "23"), (0x005B0A40, "24"), (0x005AD450, "26"), (0x00621E40, "26"), (0x005A9A70, "27"),
    (0x005A9BF0, "28"), (0x005A9E10, "28"), (0x005AA250, "29"), (0x005A9FB0, "30"), (0x005ABB00, "31"),
    (0x005AA730, "32"), (0x005AC350, "33"), (0x005AC870, "34"), (0x005AC940, "35, 106"), (0x005C98F0, "37"),
    (0x005CA4D0, "38"), (0x005CA910, "39"), (0x005C9EA0, "40"), (0x0056BC80, "41"), (0x005DA940, "42"),
    (0x005DB1C0, "43"), (0x005DB150, "43"), (0x005DB850, "45"), (0x005DBE50, "45"), (0x005DBC60, "46, 107"),
    (0x005DC1E0, "47"), (0x005C4DF0, "49, 105"), (0x005C56C0, "50, 105"), (0x005C5100, "51"), (0x005CEDC0, "55"),
    (0x005CE9F0, "56"), (0x005D81C0, "60"), (0x005D8780, "60"), (0x005D83E0, "61"), (0x005D88B0, "62"),
    (0x005C6A80, "63"), (0x005C6EC0, "64"), (0x005C8190, "65"), (0x005C8520, "66"), (0x005C7040, "68"),
    (0x005C8080, "69"), (0x005D3140, "70"), (0x005D5A30, "70"), (0x005D4150, "71"), (0x005D5E10, "72"),
    (0x005D4DB0, "73"), (0x0055E170, "76"), (0x00562390, "76"), (0x005CA260, "77"), (0x005FDA80, "78, 81"),
    (0x00582DA0, "79"), (0x005830E0, "79"), (0x00583410, "79"), (0x005D0920, "105"), (0x005CAF30, "83"),
    (0x005CB940, "84"), (0x005CBE00, "84"), (0x005CAFA0, "85"), (0x005CCB10, "85"), (0x005CC4E0, "86"),
    (0x005CE670, "86"), (0x005CCD10, "88"), (0x005D1350, "88"), (0x005CDA00, "89"), (0x005CDC10, "89"),
    (0x005D1E10, "94"), (0x005D1C30, "95"), (0x005D2490, "95"), (0x005D21B0, "96"), (0x005D26F0, "96"),
    (0x005D18E0, "97"), (0x005D19D0, "97"), (0x005CC960, "97"), (0x005D2C20, "104"),
]

# Per row: (row, root, gate call sites, claim's first address, what the claim is past). Filled from the `sites`
# listing and objdump reads of each root; the claim's first address is the first instruction of the code the row's
# `after:` part describes.
ROWS = [
    # rows moved c-emu -> b (H2a): the claim lies after the gate, or is the gate callee's own work (claim None)
    ("13", 0x005AE780, [0x005AE879], None, "the re-plan is PathPlan's walk"),
    ("15", 0x005A9820, [0x005A9903, 0x005A9918], 0x005A9908, "the refusal follows COLL_CellTestAt's room read; "
                                                             "the creation, then mdo 1"),
    ("17", 0x005AF170, [0x005AF21C], 0x005AF223, "the stores after PathPlan"),
    ("18", 0x005AF300, [0x005AF3E6], 0x005AF3EE, "the +0x2C store after the chest drop"),
    ("19", 0x005AF300, [0x005AF474], 0x005AF518, "the gold pile after the free-cell search"),
    ("21", 0x005AF540, [0x005AF55C], 0x005AF564, "left <- 10 and mdo 1 after the re-target"),
    ("21", 0x005AF540, [0x005AF582], 0x005AF587, "the return 2 after the end-of-life hit"),
    ("22", 0x005AF620, [0x005AF744], 0x005AF764, "the second creation"),
    ("23", 0x005B01F0, [0x005B039B], 0x005B03B0, "the second creation"),
    ("24", 0x005B0A40, [0x005B0A7F], None, "the tyrael3 spawn and the room pin"),
    ("27", 0x005A9A70, [0x005A9BDC], 0x005A9BE1, "the return after AreaHitAt"),
    ("31", 0x005ABB00, [0x005ABBE8], 0x005ABBFB, "each bolt's stores after its creation"),
    ("32", 0x005AA730, [0x005AA814, 0x005AA87F], 0x005AA890, "the next bolt and its count after the search"),
    ("34", 0x005AC870, [0x005AC8F6], 0x005AC90F, "HitSubMissile2 after the first creation"),
    ("38", 0x005CA4D0, [0x005CA66D], 0x005CA681, "stats 350/351 after STATE_ApplyTimed"),
    ("38", 0x005CA4D0, [0x005CA5A5, 0x005CA5BD], 0x005CA5D1, "the srvmissilea and the hit after the search"),
    ("39", 0x005CA910, [0x005CAA9C], 0x005CAAB1, "the later spawns' set-up after the first"),
    ("40", 0x005C9EA0, [0x005C9EF8, 0x005C9FC1], 0x005C9FDB, "the cell test, then the three creations"),
    ("41", 0x0056BC80, [0x0056BCB5], None, "the count is SKILLS_ForUnitsInRange's walk"),
    ("45", 0x005DB850, [0x005DB8AE], 0x005DBA19, "the bolts after the delivery"),
    ("45", 0x005DBE50, [0x005DBEA6], 0x005DBFD4, "the chain after the delivery"),
    ("46", 0x005DBC60, [0x005DBDBD, 0x005DBDC9], 0x005DBDD2, "the count and next target after the hit"),
    ("47", 0x005DC1E0, [0x005DC2BA], 0x005DC2D4, "what follows the spawn"),
    ("50", 0x005C56C0, [0x005C5751, 0x005C5757], 0x005C57B5, "do 58's RangeB"),
    ("51", 0x005C5100, [0x005C51E3], 0x005C51FB, "the summon's set-up after the spawn"),
    ("55", 0x005CEDC0, [0x005CEE38, 0x005CEFF1], None, "the passivestate list's free"),
    ("61", 0x005D83E0, [0x005D8445], 0x005D8452, "the aura state after the 64 creations"),
    ("62", 0x005D88B0, [0x005D8943, 0x005D8952], 0x005D896E, "the stat 19 add after the creation"),
    ("63", 0x005C6A80, [0x005C6B6C], 0x005C6BBC, "the set-up after the spawn"),
    ("64", 0x005C6EC0, [0x005C6F8E], None, "the list is STATLIST_Alloc's, its callback set after it"),
    ("65", 0x005C8190, [0x005C8290], 0x005C82BF, "the list, events and the node store"),
    ("66", 0x005C8520, [0x005C8654], 0x005C8688, "do 146's re-seed and draws"),
    ("68", 0x005C7040, [0x005C713B], None, "the further creations"),
    ("69", 0x005C8080, [0x005C8148], 0x005C8162, "MISSDATA_SetSeedLow after the creation"),
    ("71", 0x005D4150, [0x005D4652], 0x005D4657, "the rings' remaining creations"),
    ("72", 0x005D5E10, [0x005D5FB2], 0x005D5FB7, "the summons' set-up"),
    ("76", 0x0055E170, [0x0055E1C1], 0x0055E25D, "the ItemUse call"),
    ("76", 0x00562390, [0x005623E1], 0x005624AF, "the ItemUse call"),
    ("77", 0x005CA260, [0x005CA32B], 0x005CA330, "MISSDATA_SetSeedLow after the creation"),
    ("79", 0x00582DA0, [0x00582E6D], 0x00582E72, "shrine 19 after the unit search"),
    ("79", 0x005830E0, [0x005831C7], 0x0058324C, "shrine 21's potions"),
    ("79", 0x005830E0, [0x005833E5], None, "shrine 21's further missiles"),
    ("79", 0x00583410, [0x005834F7], 0x0058357C, "shrine 22's potions"),
    ("79", 0x00583410, [0x00583715], None, "shrine 22's further missiles"),
    ("83", 0x005CAF30, [0x005CAF55], 0x005CAF5F, "QueuedHitRemove and SrvStart after the delivery"),
    ("84", 0x005CB940, [0x005CB9B4, 0x005CBB1B], None, "do 89's landing and path plan"),
    ("84", 0x005CBE00, [0x005CBE66, 0x005CBED0], None, "do 91's spawn"),
    ("85", 0x005CAFA0, [0x005CB039], 0x005CB080, "do 84's further spawns"),
    ("85", 0x005CCB10, [0x005CCBCD, 0x005CCBF5], 0x005CCC31, "do 97's path target and mode"),
    ("86", 0x005CC4E0, [0x005CC5D5], 0x005CC5DE, "do 95's frame and repeat"),
    ("86", 0x005CE670, [0x005CE6E4], 0x005CE6E9, "do 111's loop"),
    ("88", 0x005CCD10, [0x005CCE18], 0x005CCE25, "do 99's further creations"),
    ("88", 0x005D1350, [0x005D1489], 0x005D148E, "do 126's repeat"),
    ("94", 0x005D1E10, [0x005D1EA1], None, "the class change"),
    ("95", 0x005D1C30, [0x005D1CB5], 0x005D1CBA, "the vine's words after its creation"),
    ("95", 0x005D2490, [0x005D2530], 0x005D2539, "do 135's minion set-up"),
    ("97", 0x005D18E0, [0x005D195C], None, "the attach"),
    ("97", 0x005D19D0, [0x005D1A4B], None, "the detach"),
    ("97", 0x005D2490, [0x005D2530], 0x005D254E, "do 135's second try"),
    ("97", 0x005CC960, [0x005CC991, 0x005CC9DC], None, "start 61's revive"),
    ("106", 0x005AC940, [0x005ACA08], None, "what MissileCreate makes of the unwritten class word"),
]


ROOMS = {0x0056B7E0: "SKILLS_ForUnitsInRange", 0x00619790: "DUNGEON_GetNearRooms", 0x00463740: "RoomAtSubtile",
         0x0061A010: "DUNGEON_GetCollMap"}


def names():
    out = {}
    with open(os.path.join(ROOT, "re", "symbols.csv")) as f:
        for r in csv.DictReader(f):
            out[int(r["address"], 16)] = r["name"]
    return out


def first_pool(memo, A, t, depth):
    if t in R.POOL:
        return 0, [], R.POOL[t]
    if t not in memo:
        memo[t] = R.walk(A, t, depth)
    seen, pool, imports, ic, fatal = memo[t]
    first = sorted(pool.items(), key=lambda kv: kv[1][0])
    desc = ("first %s at %08X via %s" % (R.POOL[first[0][0]], first[0][1][0], first[0][1][1])) if first else "no pool"
    rooms = [n + " via " + R.path(seen, seen[a]) for a, n in sorted(ROOMS.items()) if a in seen and a != t]
    if t in ROOMS:
        rooms.append(ROOMS[t] + " itself")
    desc += "; rooms: " + ("; ".join(rooms) if rooms else "none")
    return len(seen), imports, desc


def cmd_sites(depth):
    A, N, memo = W.asm(), names(), {}
    print("S2BE-SITES depth=%d roots=%d" % (depth, len(ROOTS)))
    for root, rows in ROOTS:
        vas, calls, icalls = W.body(A, root)[:3]
        print("ROOT %08X %s (rows %s): direct=%d indirect=%d" % (root, N.get(root, "?"), rows, len(calls),
                                                                  len(icalls)))
        for site, t in sorted(calls):
            if t in R.FATAL:
                print("  SITE %08X -> %08X fatal" % (site, t))
                continue
            n, imports, desc = first_pool(memo, A, t, depth - 1)
            print("  SITE %08X -> %08X %s functions=%d imports=%d %s" % (site, t, N.get(t, "?"), n, len(imports),
                                                                         desc))
        for va in icalls:
            print("  ICALL %08X %s" % (va, A.at(va)[1]))
    return 0


def entries_into(A, vas, lo, hi):
    """Branches of the body whose target lies in (lo, hi] and whose source lies outside [lo, hi]."""
    out = []
    for va in sorted(vas):
        mn, ops = A.at(va)
        if not mn.startswith("j"):
            continue
        t = W.branch_target(ops)
        if t is not None and lo < t <= hi and not lo <= va <= hi:
            out.append((va, t))
    return out


def succ(A, va):
    mn, ops = A.at(va)
    nxt = A.next_va(va)
    if mn in ("ret", "retn", "iret", "hlt", "int3"):
        return []
    if mn == "call":
        t = W.branch_target(ops)
        return [] if t in R.FATAL else [nxt]
    if mn == "jmp":
        t = W.branch_target(ops)
        if t is not None:
            return [t]
        m = W.JTAB.match(ops)
        return list(W.switch_targets(A, va, int(m.group(1), 16))) if m else []
    if mn.startswith("j") or mn.startswith("loop"):
        t = W.branch_target(ops)
        return [nxt] + ([t] if t is not None else [])
    return [nxt]


def reaches_avoiding(A, root, claim, blocked):
    """Whether the claim's instruction is reachable from the function's entry on a path through none of the
    blocked call sites (the intra-procedural flow graph; calls fall through)."""
    seen, work = set(), [root]
    while work:
        va = work.pop()
        if va in seen or va in blocked or A.at(va) is None:
            continue
        if va == claim:
            return True
        seen.add(va)
        work.extend(succ(A, va))
    return False


def cmd_rows(depth):
    A, N, memo = W.asm(), names(), {}
    print("S2BE-ROWS depth=%d rows=%d" % (depth, len(ROWS)))
    for row, root, gates, claim, what in ROWS:
        vas, calls = W.body(A, root)[:2]
        cmap = dict(calls)
        print("ROW %s root %08X %s claim %s (%s)" % (row, root, N.get(root, "?"),
                                                     "%08X" % claim if claim else "in the callee", what))
        for g in gates:
            t = cmap.get(g)
            if t is None:
                print("  GATE %08X NOT A DIRECT CALL OF THE BODY" % g)
                continue
            n, imports, desc = first_pool(memo, A, t, depth - 1)
            ent = entries_into(A, vas, g, claim) if claim and g < claim else []
            print("  GATE %08X -> %08X %s; %s; imports=%d; entries between gate and claim: %s" % (
                g, t, N.get(t, "?"), desc, len(imports),
                " ".join("%08X->%08X" % e for e in ent) if ent else "none"))
        if claim:
            print("  CLAIM %08X reachable from %08X avoiding every gate: %s" % (
                claim, root, "yes" if reaches_avoiding(A, root, claim, set(gates)) else "no"))
    return 0


def main(argv):
    depth = int(argv[argv.index("--depth") + 1]) if "--depth" in argv else 4
    cmd = argv[0] if argv else "sites"
    return {"sites": cmd_sites, "rows": cmd_rows}[cmd](depth)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
