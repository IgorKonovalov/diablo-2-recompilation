#!/usr/bin/env python3
"""Plan 0069 Phase 2: a per-log summary of a rev 7 AI log, for the run record's predictions.

    python3 -I tools/ai_tour_words.py LOG [LOG ...]       # one block per log
    python3 -I tools/ai_tour_words.py --list LOGLIST      # the logs named in a file, one per line, relative to it

Per log: the logger's revision, the decisions per MonStats AI row (the AID line's "ai"), the R7W lines per key, the number of
decisions that carry each key (a decision with two lines of a key counts once; the first line is the one the models read), the
AII and AIQ lines per init function, and the LOGERR and CAP lines. Stdlib and tools/ai.py only; nothing is written.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402


def summary(path):
    """The summary of one log as a dict (the printing is `render`)."""
    res = ai.parse(path)
    rows = collections.Counter(d["aid"]["ai"] for d in res["dec"])
    lines = collections.Counter()
    carrying = collections.Counter()
    for d in res["dec"]:
        keys = set()
        for w in d.get("r7all", []):
            lines[w["key"]] += 1
            keys.add(w["key"])
        carrying.update(keys)
    inits = collections.Counter()
    for tag, d in res["inits"]:
        inits[(tag, d.get("fn"))] += 1
    armed, other = None, collections.Counter()
    with open(path, errors="replace") as fh:
        for ln in fh:
            if ln.startswith("AI logger armed"):
                armed = armed or ln.strip()
            elif ln.startswith("LOGERR"):
                other["LOGERR"] += 1
            elif ln.startswith("CAP "):
                other["CAP"] += 1
    return {"armed": armed, "decisions": len(res["dec"]), "rows": rows, "word_lines": lines, "carrying": carrying,
            "inits": inits, "other": other}


def render(path, s):
    out = ["LOG %s" % os.path.basename(path), "  ARMED %s" % s["armed"], "  DECISIONS %d" % s["decisions"],
           "  ROWS " + " ".join("%s:%d" % (k, v) for k, v in sorted(s["rows"].items(), key=lambda kv: (kv[0] is None, kv[0])))]
    for k in sorted(s["word_lines"]):
        out.append("  WORD %-18s lines %4d decisions %4d" % (k, s["word_lines"][k], s["carrying"][k]))
    for (tag, fn), n in sorted(s["inits"].items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        out.append("  INIT %s fn 0x%08X lines %d" % (tag, fn or 0, n))
    if s["other"]:
        out.append("  OTHER " + " ".join("%s:%d" % kv for kv in sorted(s["other"].items())))
    return "\n".join(out)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--list":
        base = os.path.dirname(os.path.abspath(argv[1]))
        paths = [os.path.join(base, ln.strip()) for ln in open(argv[1]) if ln.strip()]
    else:
        paths = argv
    for p in paths:
        print(render(p, summary(p)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
