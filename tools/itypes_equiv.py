"""Backlog itemtypes-equiv-walk-form (plan 0064 Phase 4): the item-type equivalence matrix, built as the code builds it,
over the stock itemtypes.bin, and compared with a plain transitive closure of Equiv1/Equiv2.

The builder is the itemtypes loader (fn 0x006392D9 onward): n = the record count (0x0096C82C), W = (n + 31) / 32 dwords
per row (0x0096C830), the matrix at 0x0096C834, row i bit t = TypeIsOf(i, t) (sub 0x00638CD0) for every i, t in 0..n-1.
TypeIsOf is modelled here from the disassembly (labels are instruction addresses), including its stack bound, and
with a step cap so that a cycle that would loop forever in the game is reported instead.

Usage: python3 -I tools/itypes_equiv.py [<excel-dir>]   (default workspace/merged/data/global/excel)
Evidence: docs/findings/items/0005 § Plan 0064 (the Equiv matrix).
"""
import os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excel_bin       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")


def s16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def type_is_of(recs, i, t, stats):
    """sub_00638CD0: ECX = i, EDX = t."""
    n = len(recs)
    if t <= 0:                                  # 0x00638CD9 test edx, edx; jg
        return 1
    if i <= 0 or i >= n:                        # 0x00638CE6, 0x00638CF5
        return 0
    stack = [i]                                 # [ebp-0x200], 128 dwords; ecx = 1
    steps = 0
    while True:
        x = stack.pop()                         # 0x00638D10: eax = stack[ecx-1]; ecx--
        steps += 1
        if steps > 100000:
            stats["hang"] += 1
            return None
        if x == t:                              # 0x00638D1A
            return 1
        if x >= n:                              # 0x00638D1E: signed; a negative x would read before the records
            return 0
        if len(stack) > 0x7C:                   # 0x00638D22: the depth bound, 124 after the pop
            stats["depth bound"] += 1
            return 0
        if x < 0:
            stats["negative index read"] += 1
            return 0
        e1, e2 = s16(recs[x], 4), s16(recs[x], 6)
        if e1 > 0:                              # 0x00638D34 test si, si; jle: Equiv1 <= 0 skips both
            stack.append(e1)
            if e2 != 0:                         # 0x00638D4A test ax, ax; je: any non-zero Equiv2, negative too
                stack.append(e2)
        stats["max stack"] = max(stats["max stack"], len(stack))
        if not stack:                           # 0x00638D5C
            return 0


def closure(recs, i, t):
    """Plain reading: t is i or an Equiv1/Equiv2 ancestor of i (blank = 0 = none), with a visited set."""
    seen, todo = set(), [i]
    while todo:
        x = todo.pop()
        if x in seen or not (0 < x < len(recs)):
            continue
        if x == t:
            return 1
        seen.add(x)
        todo += [s16(recs[x], 4), s16(recs[x], 6)]
    return 0


def main(argv):
    excel = argv[1] if len(argv) > 1 else EXCEL
    recs, size = excel_bin.read_bin(os.path.join(excel, "itemtypes.bin"))
    n = len(recs)
    print("itemtypes.bin: %d records of %d bytes; W = (n + 31) / 32 = %d dwords per row" % (n, size, (n + 31) // 32))
    e1z_e2 = [x for x in range(n) if s16(recs[x], 4) <= 0 and s16(recs[x], 6) != 0]
    neg = [x for x in range(n) if s16(recs[x], 4) < 0 or s16(recs[x], 6) < 0]
    print("rows with Equiv1 <= 0 and Equiv2 != 0 (Equiv2 ignored): %d %s" % (len(e1z_e2), e1z_e2))
    print("rows with a negative Equiv word: %d %s" % (len(neg), neg))
    stats = {"hang": 0, "depth bound": 0, "negative index read": 0, "max stack": 0}
    diff, ones, bit0 = [], 0, 0
    for i in range(n):
        for t in range(n):
            m = type_is_of(recs, i, t, stats)
            c = 1 if t == 0 else closure(recs, i, t)
            ones += m == 1
            bit0 += t == 0 and m == 1
            if m != c:
                diff.append((i, t, m, c))
    print("matrix bits set: %d of %d; rows with bit 0 set: %d" % (ones, n * n, bit0))
    print("row 0 bits: %s" % [t for t in range(n) if type_is_of(recs, 0, t, stats)])
    print("walk stats: %s" % stats)
    print("differences from the closure (bit 0 taken as set in every row): %d %s"
          % (len(diff), diff[:10]))
    depth = 0
    for i in range(1, n):
        d, x, seen = 0, i, set()
        todo = [(i, 0)]
        while todo:
            x, d = todo.pop()
            if not (0 < x < n) or (x, d) in seen:
                continue
            seen.add((x, d))
            depth = max(depth, d)
            if s16(recs[x], 4) > 0:
                todo.append((s16(recs[x], 4), d + 1))
                if s16(recs[x], 6):
                    todo.append((s16(recs[x], 6), d + 1))
    print("longest Equiv chain (edges): %d" % depth)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
