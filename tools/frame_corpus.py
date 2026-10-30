#!/usr/bin/env python3
"""Index and reader of the kept harness logs of plans 0037-0052 (plan 0055 Phase 0).

The logs stay under workspace/logs (no game data in git). This tool classifies them and reads the frame-stamped ones
as one event stream per session.

Usage:
  python3 -I tools/frame_corpus.py index   <logs-root> <out-dir>   classify every harness log, attribute it to the
                                       runs of plans 0037-0052 that name it, hash the attributed ones; writes
                                       <out-dir>/frame-corpus-logs.tsv and frame-corpus-tags.tsv; prints the block
  python3 -I tools/frame_corpus.py summary <logs-root>             the counts only (no hashing); ends with `SURVEY frame ...`
  python3 -I tools/frame_corpus.py read    <log> [limit]           the log's event stream, one TSV line per event:
                                       frame, kind, unit type, unit id, entry seeds, exit seeds
  python3 -I tools/frame_corpus.py check   <logs-root>             the reader against the index (every framed line is
                                       consumed) and against the combat run record's per-kind counts

Definitions.
  harness log   a file whose first line starts `# d2run` (tools/d2run.py header: seed, gdb script, slot, time).
  event line    `TAG {json}`; TAG is the logger's kind. A line is frame-stamped when its JSON holds `"fr":N` or
                `"frame":N` (the combat/skills `g` block); typed unit refs are `"<role>":{"u":addr,"t":type,...,"id":N}`.
  seed          a string `xxxxxxxx:xxxxxxxx` (hi:lo). A begin/end pair is TAG0 with TAG1 or TAGX in the same log; the
                begin line's seeds are the entry seeds, the end line's the exit seeds. Pairing: end.k == begin.n when
                both exist, else the latest open begin of the base (LIFO). A single event keeps its seeds as entry.
  run           a `## run:<id>` section of a docs/findings/*/experiments.md that a plan 0037-0052 file names. A log is
                attributed to a run when the section names it: by log name, by a glob, by a list (.lst) or manifest
                file the section names (its lines name the logs), or (weakest, flagged `dir`) by its directory.
Stdlib only. Read-only.
"""
import collections
import fnmatch
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RE_FR = re.compile(r'"fr":(\d+)')
RE_FRAME = re.compile(r'"frame":(\d+)')
RE_UNIT = re.compile(r'"(\w+)":\{"u":(\d+),"t":(\d+)(?:,"c":\d+)?,"id":(\d+)')
RE_UNIT_TOP = re.compile(r'^\{"u":(\d+),"t":(\d+)')
RE_SEED = re.compile(r'"(\w+)":"([0-9a-f]{8}:[0-9a-f]{8})"')
SEED = re.compile(r"^[0-9a-f]{8}:[0-9a-f]{8}$")
RE_RUN = re.compile(r"run:(\d{4}-\d\d-\d\d-[A-Za-z0-9_.-]*[A-Za-z0-9])")
PLAN_GLOBS = ["docs/plans/003[7-9]-*.md", "docs/plans/004?-*.md", "docs/plans/005[0-2]-*.md",
              "docs/plans/done/003[7-9]-*.md", "docs/plans/done/004?-*.md", "docs/plans/done/005[0-2]-*.md"]
ROLES = ("u", "a", "m", "o", "mi", "src", "ot", "d")


def read_runs(root=ROOT):
    """-> ({run id: section text} for the runs plans 0037-0052 name, [named runs with no section])."""
    named = set()
    for pat in PLAN_GLOBS:
        for p in glob.glob(os.path.join(root, pat)):
            with open(p, errors="replace") as fh:
                named.update(x.rstrip(".") for x in RE_RUN.findall(fh.read()))
    secs = {}
    for f in sorted(glob.glob(os.path.join(root, "docs/findings/*/experiments.md"))):
        with open(f, errors="replace") as fh:
            text = fh.read()
        parts = re.split(r"^## (?=run:)", text, flags=re.M)[1:]
        for p in parts:
            head, _, body = p.partition("\n")
            rid = head.split()[0][4:].rstrip(".")
            if rid in named:
                secs[rid] = secs.get(rid, "") + "\n" + p
    return secs, sorted(named - set(secs))


def header(line):
    h = {"harness": line.startswith("# d2run")}
    for k in ("seed", "slot", "t"):
        m = re.search(r"\b%s=(\S+)" % k, line)
        h[k] = m.group(1) if m else ""
    m = re.search(r"\bgdb=(\S+)", line)
    h["gdb"] = os.path.basename(m.group(1)) if m else "none"
    return h


def list_logs(logs_root):
    out = []
    for dp, dn, fn in os.walk(logs_root):
        dn.sort()
        for f in sorted(fn):
            if f.endswith(".log"):
                out.append(os.path.relpath(os.path.join(dp, f), logs_root))
    return out


def scan_log(path):
    """One pass over a log -> header dict, tag stats {tag: [lines, framed, typed unit, seeded]}, last frame."""
    stats = collections.defaultdict(lambda: [0, 0, 0, 0])
    last = 0
    with open(path, errors="replace") as fh:
        h = header(fh.readline())
        if not h["harness"]:
            return h, {}, 0
        for line in fh:
            i = line.find(" {")
            if i < 1 or i > 12:
                continue
            s = stats[line[:i]]
            s[0] += 1
            m = RE_FR.search(line) or RE_FRAME.search(line)
            if m:
                s[1] += 1
                f = int(m.group(1))
                if f > last:
                    last = f
            if RE_UNIT.search(line, i) or RE_UNIT_TOP.match(line, i + 1):
                s[2] += 1
            if RE_SEED.search(line, i):
                s[3] += 1
    return h, dict(stats), last


def pair_tags(tags):
    """{begin tag: end tag} for TAG0 with TAG1 or TAGX in the same log."""
    out = {}
    for t in tags:
        if t.endswith("0"):
            for e in (t[:-1] + "X", t[:-1] + "1"):
                if e in tags:
                    out[t] = e
                    break
    return out


# ---------------------------------------------------------------- run attribution

def attribute(logs, logs_root, secs):
    """-> {relpath: {run id: kind}}, kind in name, glob, list, dir (strongest first)."""
    by_base = collections.defaultdict(list)
    for r in logs:
        by_base[os.path.basename(r)].append(r)
    all_files = {}
    for dp, dn, fn in os.walk(logs_root):
        for f in fn:
            if f.endswith((".lst", ".sha256", ".txt", ".tsv")):
                all_files.setdefault(f, []).append(os.path.join(dp, f))
    dirs = collections.defaultdict(list)
    for r in logs:
        d = os.path.dirname(r)
        while d:
            dirs[d].append(r)
            d = os.path.dirname(d)
    att = collections.defaultdict(dict)
    rank = {"name": 0, "list": 1, "glob": 2, "dir": 3}

    def put(r, run, kind):
        old = att[r].get(run)
        if old is None or rank[kind] < rank[old]:
            att[r][run] = kind

    tok_re = re.compile(r"[A-Za-z0-9_./*{},\[\]+-]+")
    for run, text in secs.items():
        for tok in set(tok_re.findall(text)):
            tok = tok.strip(".,")
            if tok.startswith("workspace/logs/"):
                tok = tok[len("workspace/logs/"):]
            base = os.path.basename(tok)
            if tok.endswith((".lst", ".sha256", ".txt", ".tsv")) and "*" not in tok:
                for lf in all_files.get(base, []):
                    if not os.path.relpath(lf, logs_root).endswith(tok):
                        continue
                    with open(lf, errors="replace") as fh:
                        for ln in fh:
                            for w in re.findall(r"[A-Za-z0-9_./-]+\.log\b", ln):
                                wb = os.path.basename(w)
                                cand = by_base.get(wb, [])
                                near = [c for c in cand if os.path.dirname(c) == os.path.relpath(os.path.dirname(lf), logs_root)]
                                for c in (near or cand):
                                    put(c, run, "list")
            elif tok.endswith(".log") and ("*" in tok or "{" in tok):
                if len(re.sub(r"[*{},\[\]]|\.log$", "", base)) < 4:
                    continue  # a bare `*.log` names no run's logs
                for r in logs:
                    if fnmatch.fnmatch(r, tok) or fnmatch.fnmatch(os.path.basename(r), tok):
                        put(r, run, "glob")
            elif tok.endswith(".log"):
                if tok in logs:
                    put(tok, run, "name")
                else:
                    for c in by_base.get(base, []):
                        put(c, run, "name")
            elif tok.endswith("/") and tok.rstrip("/") in dirs:
                for c in dirs[tok.rstrip("/")]:
                    put(c, run, "dir")
    return att


# ---------------------------------------------------------------- reader

Event = collections.namedtuple("Event", "frame kind utype uid units entry exit line sub")


def _units(o):
    out = {}
    for k, v in o.items():
        if isinstance(v, dict) and "id" in v and "t" in v and "u" in v:
            out[k] = (v["t"], v["id"])
    if "u" in o and isinstance(o["u"], int) and "t" in o:
        out.setdefault("u", (o["t"], None))
    return out


def _seeds(o, prefix=""):
    out = {}
    for k, v in o.items():
        if isinstance(v, str) and SEED.match(v):
            out[prefix + k] = v
        elif isinstance(v, dict):
            out.update(_seeds(v, prefix + k + "."))
    return out


def _frame(o):
    if isinstance(o.get("fr"), int):
        return o["fr"]
    if isinstance(o.get("frame"), int):
        return o["frame"]
    g = o.get("g")
    if isinstance(g, dict) and isinstance(g.get("frame"), int):
        return g["frame"]
    return None


def _exit_key(k):
    """The end line's key for a begin line's seed path: `d.s` -> `sd`, `s` -> `s`, others as they are."""
    if k.endswith(".s") and "." not in k[:-2]:
        return "s" + k[:-2][0]
    return k


def read_events(path, stats=None):
    """Yield Event for every frame-stamped line of a harness log (begin/end pairs fold into one event).
    Returns through `stats` (a dict) the counts: lines (frame-stamped lines consumed), bad (unparsable), open (begins
    never ended)."""
    if stats is None:
        stats = {}
    stats.update(lines=0, bad=0, open=0)
    h, tagstats, _last = scan_log(path)
    if not h["harness"]:
        return
    ends = pair_tags(tagstats)
    end_to_begin = {}
    for b, e in ends.items():
        end_to_begin[e] = b
    open_by_n = {}
    open_stack = collections.defaultdict(list)
    with open(path, errors="replace") as fh:
        fh.readline()
        for ln, line in enumerate(fh, 2):
            i = line.find(" {")
            if i < 1 or i > 12:
                continue
            tag = line[:i]
            if not (RE_FR.search(line) or RE_FRAME.search(line)) and tag not in end_to_begin:
                continue
            try:
                o = json.loads(line[i + 1:])
            except ValueError:
                stats["bad"] += 1
                continue
            if not isinstance(o, dict):
                stats["bad"] += 1
                continue
            fr = _frame(o)
            if tag in end_to_begin:
                base = end_to_begin[tag]
                bev = None
                if "k" in o and o["k"] in open_by_n:
                    bev = open_by_n.pop(o["k"])
                    if bev in open_stack[base]:
                        open_stack[base].remove(bev)
                elif open_stack[base]:
                    bev = open_stack[base].pop()
                if bev is None:
                    if fr is None:
                        continue
                    stats["lines"] += 1
                    yield Event(fr, tag, None, None, {}, {}, _seeds(o), ln, None)
                    continue
                if fr is not None:
                    stats["lines"] += 1
                bfr, bkind, bunits, bentry, bline, bsub = bev
                ex = _seeds(o)
                yield Event(bfr if bfr is not None else fr, bkind, *_prim(bunits), bunits, bentry, ex, bline, bsub)
                continue
            stats["lines"] += 1
            if tag in ends:
                key = (fr, tag, _units(o), _seeds(o), ln, o["k"] if isinstance(o.get("k"), str) else None)
                if "n" in o:
                    open_by_n[o["n"]] = key
                open_stack[tag].append(key)
                continue
            u = _units(o)
            yield Event(fr, tag, *_prim(u), u, _seeds(o), {}, ln, o["k"] if isinstance(o.get("k"), str) else None)
    for base, st in open_stack.items():
        for key in st:
            stats["open"] += 1
            yield Event(key[0], key[1], *_prim(key[2]), key[2], key[3], {}, key[4], key[5])


def _prim(units):
    for r in ROLES:
        if r in units:
            return units[r]
    return (None, None)


# ---------------------------------------------------------------- index

def build(logs_root, with_hash):
    secs, unsectioned = read_runs()
    logs = list_logs(logs_root)
    att = attribute(logs, logs_root, secs)
    rows = []
    tagrows = []
    for r in logs:
        p = os.path.join(logs_root, r)
        h, st, last = scan_log(p)
        row = {"path": r, "bytes": os.path.getsize(p), "harness": h["harness"], "gdb": h["gdb"], "slot": h["slot"],
               "t": h["t"][:10], "seed": h["seed"]}
        n = sum(s[0] for s in st.values())
        fr = sum(s[1] for s in st.values())
        row.update(lines=n, framed=fr, last_frame=last, tags=len(st),
                   framed_tags=sum(1 for s in st.values() if s[1]),
                   unit_lines=sum(s[2] for s in st.values() if s[1]),
                   seed_lines=sum(s[3] for s in st.values() if s[1]))
        ends = pair_tags(st)
        row["pairs_seeded"] = sum(1 for b, e in ends.items() if st[b][3] and st[e][3] and (st[b][1] or st[e][1]))
        runs = att.get(r, {})
        strong = sorted(k for k, v in runs.items() if v != "dir")
        row["runs"] = ",".join(strong)
        row["runs_dir_only"] = ",".join(sorted(k for k, v in runs.items() if v == "dir" and k not in strong))
        row["sha256"] = ""
        if with_hash and (strong or row["runs_dir_only"]) and h["harness"]:
            hs = hashlib.sha256()
            with open(p, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    hs.update(chunk)
            row["sha256"] = hs.hexdigest()
        rows.append(row)
        for t, s in sorted(st.items()):
            tagrows.append((r, t, s[0], s[1], s[2], s[3], ends.get(t, "")))
    return rows, tagrows, secs, unsectioned


def summarize(rows, secs, unsectioned):
    H = [r for r in rows if r["harness"]]
    inscope = [r for r in H if r["runs"]]
    framed = [r for r in H if r["framed"]]
    fin = [r for r in framed if r["runs"]]
    s = collections.OrderedDict()
    s["logs"] = len(rows)
    s["harness"] = len(H)
    s["not_harness"] = len(rows) - len(H)
    s["runs_named"] = len(secs) + len(unsectioned)
    s["runs_unsectioned"] = len(unsectioned)
    s["runs_with_logs"] = len({x for r in inscope for x in r["runs"].split(",")})
    s["runs_no_logs"] = len(secs) - s["runs_with_logs"]
    s["inscope_logs"] = len(inscope)
    s["inscope_dir_only"] = sum(1 for r in H if not r["runs"] and r["runs_dir_only"])
    s["unattributed_harness"] = sum(1 for r in H if not r["runs"] and not r["runs_dir_only"])
    s["framed_logs"] = len(framed)
    s["framed_inscope"] = len(fin)
    s["unframed_inscope"] = len(inscope) - len(fin)
    s["framed_lines"] = sum(r["framed"] for r in framed)
    s["framed_lines_inscope"] = sum(r["framed"] for r in fin)
    s["framed_unit_lines"] = sum(r["unit_lines"] for r in framed)
    s["framed_seed_lines"] = sum(r["seed_lines"] for r in framed)
    s["framed_logs_pairs_seeded"] = sum(1 for r in framed if r["pairs_seeded"])
    s["framed_logs_no_unit"] = sum(1 for r in framed if not r["unit_lines"])
    s["inscope_framed_loggers"] = len({r["gdb"] for r in fin})
    s["loggers"] = len({r["gdb"] for r in H})
    s["framed_loggers"] = len({r["gdb"] for r in framed})
    return s


# keys that describe the corpus (the logs the run records name); the others move whenever a lane writes a log
CORPUS_KEYS = ("runs_named", "runs_unsectioned", "runs_with_logs", "runs_no_logs", "inscope_logs", "framed_inscope",
               "unframed_inscope", "framed_lines_inscope", "inscope_framed_loggers")


def emit_survey(s):
    print("SURVEY frame " + " ".join("%s=%d" % (k, s[k]) for k in CORPUS_KEYS))


def cmd_index(logs_root, out_dir):
    rows, tagrows, secs, unsec = build(logs_root, True)
    os.makedirs(out_dir, exist_ok=True)
    cols = ["path", "bytes", "harness", "gdb", "slot", "t", "seed", "lines", "framed", "last_frame", "tags",
            "framed_tags", "unit_lines", "seed_lines", "pairs_seeded", "runs", "runs_dir_only", "sha256"]
    with open(os.path.join(out_dir, "frame-corpus-logs.tsv"), "w") as fh:
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")
    with open(os.path.join(out_dir, "frame-corpus-tags.tsv"), "w") as fh:
        fh.write("log\ttag\tlines\tframed\tunit\tseeded\tend_tag\n")
        for t in tagrows:
            fh.write("\t".join(str(x) for x in t) + "\n")
    s = summarize(rows, secs, unsec)
    for k, v in s.items():
        print("%s\t%d" % (k, v))
    print("unsectioned:", ",".join(unsec))
    emit_survey(s)


def cmd_summary(logs_root):
    rows, _t, secs, unsec = build(logs_root, False)
    emit_survey(summarize(rows, secs, unsec))


def cmd_read(path, limit):
    st = {}
    n = 0
    for ev in read_events(path, st):
        n += 1
        if n <= limit:
            print("\t".join(str(x) for x in (ev.frame, ev.kind, ev.utype, ev.uid,
                                            json.dumps(ev.entry, sort_keys=True), json.dumps(ev.exit, sort_keys=True))))
    print("events=%d lines=%d bad=%d open=%d" % (n, st["lines"], st["bad"], st["open"]))


def cmd_check(logs_root):
    rows, _t, secs, unsec = build(logs_root, False)
    bad = 0
    ev_total = 0
    for r in rows:
        if not (r["harness"] and r["framed"]):
            continue
        st = {}
        n = sum(1 for _ in read_events(os.path.join(logs_root, r["path"]), st))
        ev_total += n
        if st["bad"] or st["open"]:
            print("note %s bad=%d open=%d" % (r["path"], st["bad"], st["open"]))
        if st["lines"] != r["framed"] and st["lines"] != r["framed"] + 0:
            # unframed end lines of pairs are not counted by the index; the reader counts only framed lines
            print("MISMATCH %s index framed=%d reader lines=%d" % (r["path"], r["framed"], st["lines"]))
            bad += 1
    print("events=%d mismatches=%d" % (ev_total, bad))
    rec_bad = check_records(logs_root)
    print("SURVEY frame_check events=%d mismatches=%d record_mismatches=%d" % (ev_total, bad, rec_bad))


def _closed(path, kind):
    """Events of `kind` in a log, less the begins the log ends without (the checkers count only ended events)."""
    st = {}
    evs = [e for e in read_events(path, st) if e.kind == kind]
    return len(evs), sum(1 for e in evs if not e.exit and kind.endswith("0"))


def check_records(logs_root):
    """The reader's per-kind counts against the counts two run records state (combat 0037 P2, skills 2026-10-27)."""
    bad = 0
    # combat: c37p2-check.txt `events per kind` over c37p2-run.lst
    d = os.path.join(logs_root, "combat")
    lst, chk = os.path.join(d, "c37p2-run.lst"), os.path.join(d, "c37p2-check.txt")
    if os.path.exists(lst) and os.path.exists(chk):
        want = {}
        for ln in open(chk):
            m = re.match(r'\s+(ha|ma|mas|md|pa|pm)\s+\{.*?"events": (\d+)', ln)
            if m:
                want[m.group(1)] = int(m.group(2))
        have = collections.Counter()
        for ln in open(lst):
            p = os.path.join(d, os.path.basename(ln.strip()))
            for e in read_events(p):
                if e.kind == "EV0" and e.sub in ("ha", "ma", "pa"):
                    have[e.sub] += 1
                elif e.kind == "MS0" and e.sub in ("md", "pm"):
                    have[e.sub] += 1
                elif e.kind == "MAS0":
                    have["mas"] += 1
        for k in sorted(want):
            ok = have[k] == want[k]
            bad += not ok
            print("record combat/c37p2 %-4s record=%d reader=%d %s" % (k, want[k], have[k], "ok" if ok else "MISMATCH"))
    # skills 2026-10-27: skills-check.txt checks MAS.seed, CU.code, MC.owner over the manifest's logs
    d = os.path.join(logs_root, "skills")
    man, chk = os.path.join(d, "2026-10-27-skills-manifest.sha256"), os.path.join(d, "2026-10-27-skills-check.txt")
    if os.path.exists(man) and os.path.exists(chk):
        want = {}
        for ln in open(chk):
            m = re.match(r"\s+(MAS\.seed|CU\.code|MC\.owner)\s+(\d+)\s+(\d+)", ln)
            if m:
                want[m.group(1)] = int(m.group(2)) + int(m.group(3))
        have = collections.Counter()
        for ln in open(man):
            w = re.findall(r"\S+\.log\b", ln)
            if not w:
                continue
            p = os.path.join(d, os.path.basename(w[0]))
            for kind, key in (("MAS0", "MAS.seed"), ("CU0", "CU.code"), ("MC0", "MC.owner")):
                n, op = _closed(p, kind)
                have[key] += n - (op if key == "MC.owner" else 0)
        for k in sorted(want):
            ok = have[k] == want[k]
            bad += not ok
            print("record skills/2026-10-27 %-9s record=%d reader=%d (begins with no end excluded for MC) %s"
                  % (k, want[k], have[k], "ok" if ok else "MISMATCH"))
    return bad


def main(argv):
    if len(argv) >= 4 and argv[1] == "index":
        cmd_index(argv[2], argv[3])
    elif len(argv) >= 3 and argv[1] == "summary":
        cmd_summary(argv[2])
    elif len(argv) >= 3 and argv[1] == "read":
        cmd_read(argv[2], int(argv[3]) if len(argv) > 3 else 20)
    elif len(argv) >= 3 and argv[1] == "check":
        cmd_check(argv[2])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
