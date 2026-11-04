#!/usr/bin/env python3
"""State row 13: tools/ai_resume_flip.py's census and single-branch reversal with the words `AiPathSkillStep` reads. No game.

tools/ai_resume.py carries as unknown four words the logger does not record, and forks at 0x005E5B93, 0x005E5BC8, 0x005E5BD3 and
0x005E5BE0 on each of them. Here they are given from sources other than the decision's own calls, in `init_state` only:

  the list's count     (AiCtl +0x38)[0]: the number of points of the path of DS1 FILE that the logged fires match, the file
                       being an input the logger did not read (PATH prints the match, with the offset)
  DataTables +0xA78    the MonStats base: AID's `ms` minus class x 0x1A8; BASE prints the values over the logs, which must be one
  DataTables +0xBA0    the Skills record count: --skills N, the record count of skills.bin, docs/tables/Skills.md (357)

Nothing else changes: the machine, the matching and the reversal are tools/ai_resume.py's and tools/ai_resume_flip.py's. Only
decisions with AID `st` 13 are taken. Reversing a branch that depends on a given word is a test of that word's use, not of the word.

    python3 -I tools/ai_s13_census.py --ds1 FILE --skills N LOG...

Controls (`lane/r72` review), each one wrong given word; a word the check cannot fail on says so by passing:
    --count N       the list's count N for the file's
    --base-delta D  the MonStats base moved by D bytes
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_resume as R  # noqa: E402
import ai_resume_flip as F  # noqa: E402
import ds1  # noqa: E402


def main(argv):
    logs, path, skills, k = [], None, None, 0
    force_count, base_delta = None, 0
    while k < len(argv):
        if argv[k] == "--ds1":
            path = argv[k + 1]; k += 2
        elif argv[k] == "--skills":
            skills = int(argv[k + 1]); k += 2
        elif argv[k] == "--count":
            force_count = int(argv[k + 1]); k += 2
        elif argv[k] == "--base-delta":
            base_delta = int(argv[k + 1], 0); k += 2
        else:
            logs.append(argv[k]); k += 1
    decs, fires = [], {}
    for p in logs:
        bases = set()
        for d in ai.parse(p)["dec"]:
            a = d["aid"]
            bases.add(a["ms"] - a["c"] * 0x1A8)
            if a["st"] == 13:
                decs.append(d)
                for b in R.top_level(d):
                    if b["fn"] == 0x005DEAD0 and b["ra"] == 0x005E5C02:
                        fires.setdefault(b["c"][0], set()).add((b["a"][3], b["a"][4]))
        print("BASE %s distinct_ms_minus_class_x_0x1A8=%d" % (os.path.basename(p), len(bases)))
    f = ds1.parse(open(path, "rb").read())
    idx = sorted(fires)
    print("FIRES indices=%s distinct_points_per_index=%s" % (idx, sorted({len(v) for v in fires.values()})))
    pts = [sorted(fires[i])[0] for i in idx]
    found = None
    for w in f["paths"]:
        q = [(a[0], a[1]) for a in w["points"]]
        if len(q) == len(pts) and {(x - u, y - v) for (x, y), (u, v) in zip(pts, q)} == {(pts[0][0] - q[0][0], pts[0][1] - q[0][1])}:
            found = (w, (pts[0][0] - q[0][0], pts[0][1] - q[0][1]))
    print("DS1 sha256=%s" % hashlib.sha256(open(path, "rb").read()).hexdigest())
    print("PATH file=%s paths_in_file=%d match=%s points=%d offset=%s" % (os.path.basename(path), len(f["paths"]), bool(found), len(found[0]["points"]) if found else 0, found[1] if found else None))
    if not found or skills is None:
        return 2
    count = len(found[0]["points"]) if force_count is None else force_count
    orig = R.init_state

    def init(aid):
        st = orig(aid)
        lst = int.from_bytes(bytes.fromhex(aid["ctl"])[0x38:0x3C], "little")
        if aid["st"] == 13 and lst:
            st.wr(lst, 4, count)
            st.wr(R.DATA_T + 0xA78, 4, (aid["ms"] - aid["c"] * 0x1A8 + base_delta) & R.M32)
            st.wr(R.DATA_T + 0xBA0, 4, skills)
        return st
    R.init_state = init
    code = R.Code()
    bnd = R.bnd_set()
    m = R.Machine(code, bnd)
    items, bad = [], 0
    for d in decs:
        r = R.check_decision(m, d)
        if r.status == "ok":
            items.append((d, r))
        else:
            bad += 1
            if bad <= 3:
                print("NOTOK %s fr=%d %s" % (r.status, d["aid"]["fr"], getattr(r, "why", "")))
    print("RESUME state=13 decisions=%d resumed=%d not_resumed=%d" % (len(decs), len(items), bad))
    print("\n".join(F.row_report(code, bnd, 10, items, 4, 1000000)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
