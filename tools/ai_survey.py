"""Survey of the monster AI index and the AI columns (plan 0052 Phase 0).

Usage:
  python3 -I tools/ai_survey.py index   <excel-dir> [<game.exe>]
  python3 -I tools/ai_survey.py rows    <excel-dir> [<AI name or index>]
  python3 -I tools/ai_survey.py states  <excel-dir> <game.exe>
  python3 -I tools/ai_survey.py hire    <excel-dir>
  python3 -I tools/ai_survey.py aiparms <excel-dir>
  python3 -I tools/ai_survey.py md      <excel-dir> [<game.exe>]
  python3 -I tools/ai_survey.py batches <excel-dir> [<game.exe>]
  python3 -I tools/ai_survey.py summary <excel-dir> [<game.exe>]

index    one line per row of the AI table (monai.txt, 148 rows; the MonStats `AI` cell compiles to the row index):
         the index, the name, the 16-byte g_MonAiTable row read from the pinned image when <game.exe> is given
         (0x0073CA18 + 16 * index, four u32), the MonStats records whose `AI` is the index (count and record ranges),
         and the reach marks: P the record is a pool class (Levels mon/nmon/umon), U a superunique's class
         (SuperUniques Class), S a summon (a Skills row with a `pettype` names it in `summon`, or a PetType `mclass`
         cell names it), H a hireling class (Hireling Class), - no stock MonStats record names the row.
states   the 18 rows of the second table g_MonAiStateRows (0x0073D358) read from the pinned image, indexed by the AI
         control's state word (docs/findings/ai/0001-machinery.md section 3): the state, the four u32 words
         (+0 kind, +4, +8, +C), and the first-table rows whose +8 word the state row repeats.
rows     one line per MonStats record (all, or those of one AI): record, Id, AI index and name, aidel per
         difficulty, aidist per difficulty, aip1..8 per difficulty (n/N/H), Skill1..8 with Sk<k>mode and Sk<k>lvl.
hire     one line per Hireling (Version, Id) group: its class and the class's AI, DefaultChance, and per skill slot
         Skill, Mode, Chance, ChancePerLvl over the group's level rows.
aiparms  the sections of the not-loaded Aiparms.txt (data/excel B1): title lines, the P<n> lines, and the monai rows a
         title matches, by the AI name or else by the display name (NameStr) of a record using the AI (case, spaces
         and punctuation ignored). A lead for parameter names only.
md       the index as the Markdown table of docs/tables/MonAI.md § The index (generated, not typed): per row the
         index, name, slot +8 word, record count, records, marks, the aip slots any record sets, aidel values per
         difficulty, the distinct skills its records name, and the batch.
batches  the Phase 1 batch proposal (rule in BATCH_RULE): one line per batch with its AI rows and record counts.
summary  counts only.

Every command ends with `SURVEY ai key=value ...`; tools/gate.py --full compares the summary line with its baseline.
Values come from the .bin records decoded with the layouts of tools/excel_layouts.py (what the game loads); a blank
cell is read from the .txt. The image is read only when its sha256 is the pinned one (docs/inventory.md). Meanings
are [L] unless a finding anchors them (docs/tables/MonAI.md). Stdlib only. Read-only.
"""
import collections
import hashlib
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
import excel_layouts as L  # noqa: E402

PINNED_SHA256 = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
AI_TABLE = 0x0073CA18      # data:g_MonAiTable (items/0001), 16-byte rows
AI_ROW = 16
AI_STATES = 0x0073D358     # data:g_MonAiStateRows (ai/0001 § 3), 18 rows of 16 bytes (MonAiInit refuses state >= 18)
AI_STATE_ROWS = 18
DIFF = ("", "(N)", "(H)")

BATCH_RULE = """\
Plan 0052 Phase 0 batch rule (a proposal; P1.1 regroups by shared code):
  machinery rows 0 `None` (no stock record) and 1 `Idle` (61 records; slot +8 words 0x005B0CC0 and 0x005B0CD0, apart
            from every other row's 0x005E0160..0x005FD210) go with P1.1
  summons   every other AI row with an S record and no H, P or U record, plus row 143 (no stock record; its slot +8
            word equals row 106's)
  hirelings every AI row with an H record, plus the AI of class 560 act5hire1 (recognised as a hireling class, no
            Hireling row)
  bosses    every other AI row with a record whose `boss` or `primeevil` bit is set, and no P record
  rest      every other row with a stock record, in table order, cut into consecutive batches of at most
            80 records (MAX_ROWS) and 18 AI rows (MAX_AIS) each"""
MAX_ROWS = 80
MAX_AIS = 18


# ---------------------------------------------------------------- the image

def ai_table_rows(exe, n):
    """The n 16-byte rows of g_MonAiTable as four u32 each, from the pinned image. -> list of 4-tuples."""
    data = open(exe, "rb").read()
    if hashlib.sha256(data).hexdigest() != PINNED_SHA256:
        raise SystemExit("ai_survey: %s is not the pinned Game.exe" % exe)
    return table_from_image(data, AI_TABLE, n)


def state_table_rows(exe):
    """The 18 rows of g_MonAiStateRows (four u32 each) from the pinned image."""
    data = open(exe, "rb").read()
    if hashlib.sha256(data).hexdigest() != PINNED_SHA256:
        raise SystemExit("ai_survey: %s is not the pinned Game.exe" % exe)
    return table_from_image(data, AI_STATES, AI_STATE_ROWS)


def table_from_image(data, va, n, row=AI_ROW):
    """Read n rows of `row` bytes (u32 words) at virtual address va of a PE32 image held in data."""
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    optsz = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    so = pe + 24 + optsz
    rva = va - base
    for i in range(nsec):
        vsize, sva, rsize, raw = struct.unpack_from("<IIII", data, so + 40 * i + 8)
        if sva <= rva and rva + n * row <= sva + min(max(vsize, rsize), rsize):
            off = raw + rva - sva
            return [struct.unpack_from("<%dI" % (row // 4), data, off + row * k) for k in range(n)]
    raise ValueError("0x%08X + %d rows not in a raw section" % (va, n))


# ---------------------------------------------------------------- the tables

def ranges(idx):
    """[3, 4, 5, 9] -> [(3, 5), (9, 9)]"""
    out = []
    for i in sorted(idx):
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return [tuple(r) for r in out]


class Table:
    def __init__(self, excel_dir, name, refs=None):
        self.header, self.rows, recs, _ = eb.load_table(excel_dir, name)
        fields = [f for f in L.LAYOUTS[name]["fields"] if "col" in f or "name" in f]
        self.rec = [{f.get("name", f.get("col")): eb.decode_field(b, f, refs) for f in fields} for b in recs]
        self.txt = [dict(zip(self.header, r)) for r in self.rows]

    def blank(self, i, col):
        return self.txt[i].get(col, "") == ""


class Data:
    def __init__(self, excel_dir, exe=None):
        self.excel_dir = excel_dir
        h, rows, recs, _ = eb.load_table(excel_dir, "monai")
        self.ai_names = [r[0] for r in rows]
        self.ai_comments = [dict(zip(h, r)) for r in rows]
        self.ai_recs = [struct.unpack("<H", b)[0] for b in recs]
        refs = eb.Refs(excel_dir)
        self.ms = Table(excel_dir, "monstats")
        self.sk = Table(excel_dir, "skills", refs)
        self.pt = Table(excel_dir, "pettype")
        self.hl = Table(excel_dir, "hireling")
        self.lv = Table(excel_dir, "levels")
        self.su = Table(excel_dir, "superuniques")
        self.skn = [t["skill"] for t in self.sk.txt]
        mh, mrows = eb.load_table(excel_dir, "monmode")[:2]
        self.mmode_code = [dict(zip(mh, r)).get("code", "") for r in mrows]
        self.ids = [t["Id"] for t in self.ms.txt]
        n = len(self.ms.rec)
        self.ai_of = [r["AI"] for r in self.ms.rec]
        self.users = collections.defaultdict(list)
        for i, a in enumerate(self.ai_of):
            self.users[a].append(i)
        self.mark = [set() for _ in range(n)]
        for r in self.lv.rec:
            for p in ("mon", "nmon", "umon"):
                for k in range(1, 11):
                    v = r["%s%d" % (p, k)]
                    if 0 <= v < n:
                        self.mark[v].add("P")
        for r in self.su.rec:
            if 0 <= r["Class"] < n:
                self.mark[r["Class"]].add("U")
        self.summon_by = collections.defaultdict(list)   # record -> [(skill row, pettype row)]
        for i, r in enumerate(self.sk.rec):
            if not self.sk.blank(i, "summon") and not self.sk.blank(i, "pettype") and 0 <= r["summon"] < n:
                self.mark[r["summon"]].add("S")
                self.summon_by[r["summon"]].append((i, r["pettype"]))
        self.mclass_by = collections.defaultdict(list)   # record -> [pettype row]
        for j, r in enumerate(self.pt.rec):
            for k in range(1, 5):
                if not self.pt.blank(j, "mclass%d" % k):
                    self.mark[r["mclass%d" % k]].add("S")
                    self.mclass_by[r["mclass%d" % k]].append(j)
        self.hire_classes = sorted({r["Class"] for r in self.hl.rec})
        for c in self.hire_classes:
            self.mark[c].add("H")
        self.table = ai_table_rows(exe, len(self.ai_names)) if exe else None
        self.states = state_table_rows(exe) if exe else None

    def skill_ok(self, v):
        return 0 <= v < len(self.skn)

    def ai_marks(self, a):
        m = set()
        for i in self.users.get(a, []):
            m |= self.mark[i]
        return m

    def row_text(self, a):
        us = self.users.get(a, [])
        return ", ".join("%d %s" % (x, self.ids[x]) if x == y else "%d-%d %s..%s" % (x, y, self.ids[x], self.ids[y])
                         for x, y in ranges(us))


def set_slots(d, idx, prefix, n):
    """The aip-like slots (1..n) with a non-zero value in any difficulty of any record in idx."""
    return [k for k in range(1, n + 1) if any(d.ms.rec[i]["%s%d%s" % (prefix, k, s)] for i in idx for s in DIFF)]


def skill_names(d, idx):
    out = []
    for i in idx:
        for k in range(1, 9):
            v = d.ms.rec[i]["Skill%d" % k]
            if 0 <= v < len(d.skn) and d.skn[v] not in out:
                out.append(d.skn[v])
    return out


# ---------------------------------------------------------------- batches

def boss_rec(d, i):
    r = d.ms.rec[i]
    return bool(r["boss"] or r["primeevil"])


def batches(d):
    """-> list of (name, [AI rows]) by BATCH_RULE."""
    n = len(d.ai_names)
    marks = [d.ai_marks(a) for a in range(n)]
    taken = set()
    out = []
    hire = sorted({a for a in range(n) if "H" in marks[a]}
                  | {d.ai_of[i] for i, t in enumerate(d.ids) if t == "act5hire1"})
    summ = sorted({a for a in range(2, n) if a not in hire and "S" in marks[a] and not marks[a] & {"P", "U"}}
                  | ({143} if 143 < n and not d.users.get(143) else set()))
    taken |= set(hire) | set(summ) | {0, 1}
    boss = [a for a in range(n) if a not in taken and "P" not in marks[a]
            and any(boss_rec(d, i) for i in d.users.get(a, []))]
    taken |= set(boss)
    rest = [a for a in range(n) if a not in taken and d.users.get(a)]
    cur, k = [], 1
    chunks = []
    for a in rest:
        if cur and (len(cur) >= MAX_AIS or sum(len(d.users[x]) for x in cur) + len(d.users[a]) > MAX_ROWS):
            chunks.append(cur)
            cur = []
        cur.append(a)
    if cur:
        chunks.append(cur)
    out.append(("machinery", [0, 1]))
    for c in chunks:
        out.append(("rest-%d" % k, c))
        k += 1
    out.append(("bosses", boss))
    out.append(("summons", summ))
    out.append(("hirelings", hire))
    return out


# ---------------------------------------------------------------- Aiparms.txt

def parse_aiparms(text):
    """Sections of Aiparms.txt. Each '-----' rule line closes a head block and opens a P block. The head block is the
    lines above the rule back to a '/*' line or the previous section's last line (a P, tab-led, `Missiles:` or
    `Skills:` line); a paragraph starting `Note:` there closes the previous section and is dropped; the first other
    paragraph (up to a blank line) is the titles, the rest the description. The P block is
    the lines `P<n>\t...` (a tab-led line continues the previous one) up to the next '/*' or rule.
    -> [dict(titles=[...], text=str, params={n: text}, missiles=str, skills=str)]"""
    lines = [ln.rstrip("\r") for ln in text.split("\n")]

    def ends_section(ln):
        return ln.startswith(("/*", "-----", "\t", "Missiles:", "Skills:")) or re.match(r"^P\d+\t", ln)

    out = []
    for i, ln in enumerate(lines):
        if not ln.startswith("-----"):
            continue
        head, j = [], i - 1
        while j >= 0 and not ends_section(lines[j]):
            head.insert(0, lines[j].strip())
            j -= 1
        paras, cur = [], []
        for x in head + [""]:
            if x:
                cur.append(x)
            elif cur:
                paras.append(cur)
                cur = []
        paras = [p for p in paras if not p[0].startswith("Note:")]   # a note closing the previous section
        sec = dict(titles=paras[0] if paras else [], text=" ".join(x for p in paras[1:] for x in p),
                   params=collections.OrderedDict(), missiles="", skills="")
        last = None
        for ln2 in lines[i + 1:]:
            if ln2.startswith(("-----", "/*")):
                break
            m = re.match(r"^P(\d+)\t(.*)$", ln2)
            if m:
                last = int(m.group(1))
                sec["params"][last] = m.group(2).strip()
            elif ln2.startswith("\t") and last is not None and ln2.strip():
                sec["params"][last] += " " + ln2.strip()
            elif ln2.startswith("Missiles:"):
                sec["missiles"] = ln2.split(":", 1)[1].strip()
            elif ln2.startswith("Skills:"):
                sec["skills"] = ln2.split(":", 1)[1].strip()
            elif not ln2.strip():
                last = None
            else:
                break       # the next section's head
        out.append(sec)
    return out


def norm(s):
    """'"Brute" Ai' -> 'brute'; 'Corrupt Rogue' -> 'corruptrogue'."""
    s = s.lower()
    if s.endswith(" ai"):
        s = s[:-3]
    return re.sub(r"[^a-z0-9]", "", s)


def aiparms_matches(secs, names, display=None):
    """Per section, the AI rows a title names: by the AI name (norm), else (display: {norm(display name): [AI rows]})
    by the display name of a MonStats record using the AI. -> [[(AI row, 'name'|'display')]]"""
    by = collections.defaultdict(list)
    for a, n in enumerate(names):
        by[norm(n)].append(a)
    res = []
    for s in secs:
        hit = []
        for t in s["titles"]:
            got = [(a, "name") for a in by.get(norm(t), [])] or [(a, "display") for a in (display or {}).get(norm(t), [])]
            for h in got:
                if h[0] not in [x[0] for x in hit]:
                    hit.append(h)
        res.append(hit)
    return res


def display_names(d):
    """{norm(display name of a MonStats record's NameStr): sorted AI rows of the records with that name}."""
    strs = eb.Refs(d.excel_dir).strings()
    out = collections.defaultdict(set)
    for i, r in enumerate(d.ms.rec):
        t = strs.text(r["NameStr"])
        if t:
            out[norm(t)].add(r["AI"])
    return {k: sorted(v) for k, v in out.items()}


# ---------------------------------------------------------------- commands

def cmd_index(d):
    print("# index name | g_MonAiTable +0 +4 +8 +C | records (count): ranges | marks")
    for a, nm in enumerate(d.ai_names):
        us = d.users.get(a, [])
        tb = " ".join("%08X" % w for w in d.table[a]) if d.table else "-"
        m = "".join(c for c in "PUSH" if c in d.ai_marks(a)) or ("-" if not us else "")
        print("%3d %-18s | %s | %3d: %s | %s" % (a, nm, tb, len(us), d.row_text(a) or "-", m))
    print("SURVEY ai index=%d" % len(d.ai_names))
    return 0


def cmd_states(d):
    if not d.states:
        raise SystemExit("ai_survey: states needs <game.exe>")
    print("# state | g_MonAiStateRows +0 +4 +8 +C | first-table rows with the same +8 word")
    for i, w in enumerate(d.states):
        same = [a for a, t in enumerate(d.table) if w[2] and t[2] == w[2]]
        print("%2d | %s | %s" % (i, " ".join("%08X" % x for x in w),
                                 " ".join("%d(%s)" % (a, d.ai_names[a]) for a in same) or "-"))
    print("SURVEY ai states=%d" % len(d.states))
    return 0


def cmd_rows(d, want):
    sel = None
    if want is not None:
        sel = int(want) if want.isdigit() else next(
            (a for a, n in enumerate(d.ai_names) if n.lower() == want.lower()), -1)
    n = 0
    for i, r in enumerate(d.ms.rec):
        a = r["AI"]
        if sel is not None and a != sel:
            continue
        n += 1
        aip = " ".join("%d/%d/%d" % tuple(r["aip%d%s" % (k, s)] for s in DIFF) for k in range(1, 9))
        sk = "; ".join("%s %s%s l%d" % (d.skn[r["Skill%d" % k]], d.mmode_code[r["Sk%dmode" % k]]
                                         if r["Sk%dmode" % k] < len(d.mmode_code) else "?",
                                         "" if r["Sk%dseq" % k] < 0 else "+seq%d" % r["Sk%dseq" % k],
                                         r["Sk%dlvl" % k])
                       for k in range(1, 9) if 0 <= r["Skill%d" % k] < len(d.skn))
        print("%3d %-18s ai %3d %-16s | del %d/%d/%d dist %d/%d/%d | aip %s | %s | %s" % (
            i, d.ids[i], a, d.ai_names[a] if 0 <= a < len(d.ai_names) else "?",
            r["aidel"], r["aidel(N)"], r["aidel(H)"], r["aidist"], r["aidist(N)"], r["aidist(H)"], aip, sk or "-",
            "".join(c for c in "PUSH" if c in d.mark[i]) or "-"))
    print("SURVEY ai rows=%d" % n)
    return 0


def cmd_hire(d):
    groups = collections.OrderedDict()
    for i, r in enumerate(d.hl.rec):
        groups.setdefault((r["Version"], r["Id"]), []).append(i)
    for (v, hid), idx in groups.items():
        r0 = d.hl.rec[idx[0]]
        c = r0["Class"]
        sk = []
        for k in range(1, 7):
            if r0["Skill%d" % k] < 0:
                continue
            sk.append("%s m%s c%s cpl%s" % (
                d.skn[r0["Skill%d" % k]], "/".join(str(d.hl.rec[i]["Mode%d" % k]) for i in idx),
                "/".join(str(d.hl.rec[i]["Chance%d" % k]) for i in idx),
                "/".join(str(d.hl.rec[i]["ChancePerLvl%d" % k]) for i in idx)))
        print("v%-3d id %2d class %3d %-10s ai %3d %-10s levels %-9s default %2d | %s" % (
            v, hid, c, d.ids[c], d.ai_of[c], d.ai_names[d.ai_of[c]],
            "/".join(str(d.hl.rec[i]["Level"]) for i in idx), r0["DefaultChance"], "; ".join(sk)))
    print("SURVEY ai hire_groups=%d" % len(groups))
    return 0


def read_aiparms(excel_dir):
    p = eb.find_file(excel_dir, "aiparms", ".txt")
    return open(p, "rb").read().decode("latin-1") if p else ""


def cmd_aiparms(d):
    secs = parse_aiparms(read_aiparms(d.excel_dir))
    hits = aiparms_matches(secs, d.ai_names, display_names(d))
    for k, (s, h) in enumerate(zip(secs, hits)):
        print("%2d %s -> %s | %s" % (k, " / ".join(s["titles"]) or "-",
                                     ", ".join("%d %s (%s)" % (a, d.ai_names[a], how) for a, how in h) or "no match",
                                     "; ".join("P%d %s" % kv for kv in s["params"].items())))
    print("SURVEY ai aiparms_sections=%d aiparms_matched=%d" % (len(secs), sum(1 for h in hits if h)))
    return 0


def cmd_md(d):
    bt = {a: name for name, rows in batches(d) for a in rows}
    print("| # | AI | slot `+8` | n | MonStats records | reach | `aip` set | `aidel` n/N/H | skills | batch |")
    print("|---:|---|---|---:|---|---|---|---|---|---|")
    for a, nm in enumerate(d.ai_names):
        us = d.users.get(a, [])
        dl = "/".join(",".join(str(v) for v in sorted({d.ms.rec[i]["aidel%s" % s] for i in us})) for s in DIFF)
        sl = set_slots(d, us, "aip", 8)
        sk = skill_names(d, us)
        print("| %d | `%s` | %s | %d | %s | %s | %s | %s | %s | %s |" % (
            a, nm, "`%08X`" % d.table[a][2] if d.table else "—", len(us), d.row_text(a) or "—",
            "".join(c for c in "PUSH" if c in d.ai_marks(a)) or ("**none**" if not us else "·"),
            ",".join(map(str, sl)) or "—", dl if us else "—", ", ".join(sk) or "—", bt.get(a, "—")))
    print("SURVEY ai md_rows=%d" % len(d.ai_names))
    return 0


def cmd_batches(d):
    print(BATCH_RULE)
    for name, rows in batches(d):
        print("%-10s %2d AIs %3d records: %s" % (name, len(rows), sum(len(d.users.get(a, [])) for a in rows),
                                                 ", ".join("%d %s" % (a, d.ai_names[a]) for a in rows)))
    print("SURVEY ai batches=%d" % len(batches(d)))
    return 0


def summary(d):
    kv = collections.OrderedDict()
    n = len(d.ai_names)
    kv["ai_rows"] = n
    kv["ai_bin_is_row"] = sum(1 for i, v in enumerate(d.ai_recs) if v == i)
    kv["ai_names_dup_nocase"] = n - len({x.lower() for x in d.ai_names})
    kv["ms_records"] = len(d.ms.rec)
    kv["ms_ai_blank"] = sum(1 for i in range(len(d.ms.rec)) if d.ms.blank(i, "AI"))
    kv["ms_ai_bad"] = sum(1 for a in d.ai_of if not 0 <= a < n)
    kv["ms_ai_name_mismatch"] = sum(1 for i, a in enumerate(d.ai_of)
                                    if 0 <= a < n and d.ai_names[a].lower() != d.ms.txt[i]["AI"].lower())
    kv["ai_used"] = sum(1 for a in range(n) if d.users.get(a))
    kv["ai_unused"] = n - kv["ai_used"]
    for c, k in (("P", "pool"), ("U", "superunique"), ("S", "summon"), ("H", "hireling")):
        kv["ai_reach_%s" % k] = sum(1 for a in range(n) if c in d.ai_marks(a))
        kv["ms_mark_%s" % k] = sum(1 for m in d.mark if c in m)
    kv["ai_reach_none_of_push"] = sum(1 for a in range(n) if d.users.get(a) and not d.ai_marks(a))
    kv["ai_one_record"] = sum(1 for a in range(n) if len(d.users.get(a, [])) == 1)
    kv["ai_max_records"] = max(len(v) for v in d.users.values())
    kv["ai_comment_cells"] = sum(1 for r in d.ai_comments for c, v in r.items() if c.startswith("*aip") and v)
    kv["ai_comment_rows"] = sum(1 for r in d.ai_comments if any(v for c, v in r.items() if c.startswith("*aip")))
    for k in range(1, 9):
        kv["aip%d_records" % k] = sum(1 for r in d.ms.rec if any(r["aip%d%s" % (k, s)] for s in DIFF))
    kv["aip_records_any"] = sum(1 for r in d.ms.rec if any(r["aip%d%s" % (k, s)] for k in range(1, 9) for s in DIFF))
    kv["aip_vary_by_diff"] = sum(1 for r in d.ms.rec if any(len({r["aip%d%s" % (k, s)] for s in DIFF}) > 1
                                                            for k in range(1, 9)))
    kv["aidel_zero"] = sum(1 for r in d.ms.rec if not r["aidel"])
    kv["aidel_vary_by_diff"] = sum(1 for r in d.ms.rec if len({r["aidel%s" % s] for s in DIFF}) > 1)
    kv["aidist_records"] = sum(1 for r in d.ms.rec if any(r["aidist%s" % s] for s in DIFF))
    ok = d.skill_ok
    kv["skill_records"] = sum(1 for r in d.ms.rec if any(ok(r["Skill%d" % k]) for k in range(1, 9)))
    kv["skill_cells"] = sum(1 for r in d.ms.rec for k in range(1, 9) if ok(r["Skill%d" % k]))
    kv["skill_cells_blank_txt"] = sum(1 for i in range(len(d.ms.rec)) for k in range(1, 9)
                                      if d.ms.blank(i, "Skill%d" % k))
    kv["skill_ai_rows"] = sum(1 for a in range(n) if any(ok(d.ms.rec[i]["Skill%d" % k])
                                                         for i in d.users.get(a, []) for k in range(1, 9)))
    kv["skill_lvl0_set"] = sum(1 for r in d.ms.rec for k in range(1, 9) if ok(r["Skill%d" % k]) and
                               not r["Sk%dlvl" % k])
    kv["skill_seq_mode"] = sum(1 for r in d.ms.rec for k in range(1, 9) if ok(r["Skill%d" % k]) and
                               r["Sk%dseq" % k] >= 0)
    # AIs whose records disagree on which aip slots are non-zero
    kv["ai_aip_slots_differ"] = sum(1 for a in range(n) if len({tuple(
        k for k in range(1, 9) if any(d.ms.rec[i]["aip%d%s" % (k, s)] for s in DIFF)) for i in d.users.get(a, [])}) > 1)
    kv["hire_classes"] = len(d.hire_classes)
    kv["hire_ais"] = len({d.ai_of[c] for c in d.hire_classes})
    kv["summon_records"] = sum(1 for m in d.mark if "S" in m)
    secs = parse_aiparms(read_aiparms(d.excel_dir))
    kv["aiparms_sections"] = len(secs)
    hits = aiparms_matches(secs, d.ai_names, display_names(d))
    kv["aiparms_matched"] = sum(1 for h in hits if h)
    kv["aiparms_ai_rows_matched"] = len({a for h in hits for a, _ in h})
    kv["aiparms_params"] = sum(len(x["params"]) for x in secs)
    bt = batches(d)
    kv["batches"] = len(bt)
    kv["batch_rows"] = sum(len(r) for _, r in bt)
    if d.table:
        t = d.table
        kv["tbl_rows"] = len(t)
        kv["tbl_fn8_set"] = sum(1 for w in t if w[2])
        kv["tbl_fn8_distinct"] = len({w[2] for w in t})
        kv["tbl_fn8_shared_rows"] = sum(1 for w in t if sum(1 for x in t if x[2] == w[2]) > 1)
        kv["tbl_fn4_set"] = sum(1 for w in t if w[1])
        kv["tbl_fn4_distinct"] = len({w[1] for w in t if w[1]})
        kv["tbl_fnc_set"] = sum(1 for w in t if w[3])
        kv["tbl_fnc_distinct"] = len({w[3] for w in t if w[3]})
        kv["tbl_w0_max"] = max(w[0] for w in t)
        for v in range(kv["tbl_w0_max"] + 1):
            kv["tbl_w0_%d" % v] = sum(1 for w in t if w[0] == v)
    if d.states:
        st = d.states
        kv["st_rows"] = len(st)
        kv["st_fn8_set"] = sum(1 for w in st if w[2])
        kv["st_fn8_distinct"] = len({w[2] for w in st if w[2]})
        kv["st_fn8_in_first"] = sum(1 for w in st if w[2] and any(t[2] == w[2] for t in d.table))
        kv["st_fn4_set"] = sum(1 for w in st if w[1])
        kv["st_fnc_set"] = sum(1 for w in st if w[3])
        for v in range(max(w[0] for w in st) + 1):
            kv["st_w0_%d" % v] = sum(1 for w in st if w[0] == v)
    return kv


def cmd_summary(d):
    kv = summary(d)
    for k, v in kv.items():
        print("%-26s %d" % (k, v))
    print("SURVEY ai " + " ".join("%s=%d" % x for x in kv.items()))
    return 0


def main(argv):
    if len(argv) < 2 or argv[0] not in ("index", "rows", "hire", "aiparms", "md", "batches", "summary", "states"):
        print(__doc__)
        return 2
    cmd, excel = argv[0], argv[1]
    exe = argv[2] if cmd in ("index", "md", "batches", "summary", "states") and len(argv) > 2 else None
    d = Data(excel, exe)
    if cmd == "index":
        return cmd_index(d)
    if cmd == "rows":
        return cmd_rows(d, argv[2] if len(argv) > 2 else None)
    if cmd == "states":
        return cmd_states(d)
    if cmd == "hire":
        return cmd_hire(d)
    if cmd == "aiparms":
        return cmd_aiparms(d)
    if cmd == "md":
        return cmd_md(d)
    if cmd == "batches":
        return cmd_batches(d)
    return cmd_summary(d)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
