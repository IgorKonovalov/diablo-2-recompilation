#!/usr/bin/env python3
"""Plan 0052 Phase 2, lane/p52b Tier A review: tools/ai_resume.py at e0e45d03 with the review's six model fixes, by name.

    python3 -I tools/ai_resume_review.py check FIXES LOG [LOG ...] [--controls]     # FIXES: P,B,C,N,E,D or -
    python3 -I tools/ai_resume_review.py classify KEPT_OUTPUT LOG [LOG ...]         # the smallest fix set clearing each RMISMATCH

This is the reviewer's check of a classification, not the model: the next lane folds the fixes into tools/ai_resume.py with
no-game tests and reruns the kept check (plan 0052 log, the lane/p52b review). What each name changes:

  P  init_state protects only the return address: [ebp+8] of a think is its own stack slot, and a search's output block there
     (0x005DDC30's distance at SkeletonMage's 0x005F96DB) was dropped by apply_result as a protected word.
  B  the opaque 0x00620870 forgets the 8 bytes it writes, not up to 64 up to EBP: at 0x005FB81F the block is [ebp-0xC], and the
     wider forget lost the control pointer [ebp-4], so the write of c0 at 0x005FB862 went through an unknown pointer.
  C  an opaque callee makes Unit+0xC4 unknown (0x005DE4E0 at 0x005F32A0 and elsewhere commands a mode; the word changes in it).
  N  a logged call between a decision's MSM0 and MSM1 lines was made inside the command (0x00552F60@0x0058F0FF), not by the think.
  E  RNG_RandLoHi 0x004BC500 is executed: the opaque call at 0x005FB69D draws from the unit seed, which the model then missed.
  D  the operand ds:0xADDR is parsed (the model stopped on the operand itself), and g_pDataTables + 0xA80 is AID's logged `ms2`.

A row 23 mismatch that no fix clears ("the decision ended") is the logger's: see ai/0017 section 7, the review's note.
Stdlib and objdump only.
"""
import itertools
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_resume as R  # noqa: E402

FIX = set()
CUR = {}
BASE_EXEC = R.EXEC
DT = 0x7A800000
orig_op, orig_init, orig_top, orig_check = R.parse_op, R.init_state, R.top_level, R.check_decision


def parse_op(t):
    m = re.match(r"\s*(?:(BYTE|WORD|DWORD) PTR )?ds:(0x[0-9a-f]+)\s*$", t)
    if m and "D" in FIX:
        return ("m", R.SIZES[m.group(1)] if m.group(1) else 4, None, None, 1, int(m.group(2), 16))
    return orig_op(t)


def init_state(aid):
    st = orig_init(aid)
    if "P" in FIX:
        st.prot = set(range(R.STK_TOP, R.STK_TOP + 4))
    if "D" in FIX:
        st.wr(0x00744304, 4, DT)
        st.wr(DT + 0xA80, 4, aid["ms2"] & R.M32)
    return st


def top_level(dec):
    log = orig_top(dec)
    if "N" in FIX:
        spans = [(a["n"], b["n"]) for a, b in dec.get("msm", []) if b]
        log = [b for b in log if not any(lo < b["n"] < hi for lo, hi in spans)]
    return log


def check_decision(m, dec):
    CUR["u"] = dec["aid"]["u"]
    R.EXEC = BASE_EXEC + ((0x004BC500,) if "E" in FIX else ())
    return orig_check(m, dec)


class Machine(R.Machine):
    def do_call(self, st, tgt, ra):
        fn = int(tgt, 16) if tgt.startswith("0x") else None
        in_win = any(lo <= ra < hi for lo, hi in self.windows)
        opaque = fn is not None and not (fn in self.bnd and in_win) and not (
            fn in R.EXEC or any(lo <= fn < hi for lo, hi in R.EXEC_WINDOWS))
        if "B" in FIX and fn == 0x00620870:
            sp = st.r["esp"]
            st.forget(st.rd(sp + 4, 4), 8)
            st.r["eax"] = st.r["ecx"] = st.r["edx"] = None
            st.f.update({"ZF": None, "SF": None, "CF": None, "OF": None})
            st.r["esp"] = (sp + self.code.ret_imm(fn)) & R.M32
            st.eip = ra
            return [st]
        out = super().do_call(st, tgt, ra)
        if "C" in FIX and opaque:
            st.wr(CUR["u"] + 0xC4, 4, None)
        return out


R.parse_op, R.init_state, R.top_level, R.check_decision = parse_op, init_state, top_level, check_decision


def set_fix(names):
    FIX.clear()
    FIX.update(names)


def cmd_check(argv):
    set_fix([] if argv[0] == "-" else argv[0].split(","))
    controls = "--controls" in argv
    paths = [a for a in argv[1:] if a != "--controls"]
    R.EXAMPLES = 500
    decs, res = R.run_resume(paths, None, controls, R.Code(), Machine)
    print("REVIEW fixes=%s" % ",".join(sorted(FIX)))
    print(R.report(decs, res), end="")
    return 0


def cmd_classify(argv):
    kept, paths = argv[0], argv[1:]
    want = {}
    for line in open(kept):
        m = re.match(r"RMISMATCH (\S+) n=(\d+) row=(\d+) (.*)", line)
        if m:
            want[(m.group(1), int(m.group(2)))] = (int(m.group(3)), m.group(4))
    m = Machine(R.Code(), R.bnd_set())
    seen = {}
    names = ["P", "B", "C", "N", "E", "D"]
    for p in paths:
        base = os.path.basename(p)
        for d in ai.parse(p)["dec"]:
            key = (base, d["aid"]["n"])
            if key not in want:
                continue
            found = None
            for k in range(0, len(names) + 1):
                for sub in itertools.combinations(names, k):
                    set_fix(sub)
                    if R.check_decision(m, d).status != "mismatch":
                        found = sub
                        break
                if found is not None:
                    break
            seen[key] = found
            row, why = want[key]
            print("RCLASS %s n=%d row=%d fixes=%s | %s" % (base, key[1], row, "+".join(found) if found else "NONE", why))
    print("RCLASSUM decisions=%d of %d" % (len(seen), len(want)))
    tally = {}
    for key, found in seen.items():
        k = (want[key][0], "+".join(found) if found else "NONE")
        tally[k] = tally.get(k, 0) + 1
    for (row, f), n in sorted(tally.items()):
        print("RCLASSROW row=%d fixes=%s n=%d" % (row, f, n))
    return 0


def main(argv):
    if len(argv) < 3 or argv[0] not in ("check", "classify"):
        print(__doc__)
        return 2
    return cmd_check(argv[1:]) if argv[0] == "check" else cmd_classify(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
