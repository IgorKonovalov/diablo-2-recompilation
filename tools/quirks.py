#!/usr/bin/env python3
"""The quirks index (plan 0057): harvest the *Reimplementation notes* of the specs, check the index.

    python3 -I tools/quirks.py harvest [--root DIR] [--spec PATH ...] [--full]
    python3 -I tools/quirks.py check [--root DIR]

harvest: every spec under docs/specs/ with a `## Reimplementation notes` section, its status, and each top-level
bullet of that section numbered n1, n2, ... in file order (indented lines belong to the bullet above), with the
tags and anchors the bullet holds. --full prints each bullet whole, else its first 160 characters.

check: reads docs/specs/quirks/README.md and verifies, for the plan's Phase 1 Done-when:
  Q1 every entry row (first cell `Q<n>`, ids unique) has one tag in its Tag cell, at least one anchor in its
     Anchors cell, and at least one source link `[..](../<spec>.md#<fragment>)` in its Source cell, each
     followed by note numbers (`n3`, `n3 n4`) when the fragment is `reimplementation-notes`;
  Q2 for each tagged source: the tag appears in the cited notes (or, for another fragment, in the section under
     that heading); every anchor of the Anchors cell (fn:/data: by name@address, run:, tbl:, struct:, src:, bare
     0x00XXXXXX addresses, and ../../ links into docs/findings or docs/tables, compared as written) appears in at least one tagged source of the row; a cited note that holds no tag at all
     is counted for coverage only and needs a tagged source (a section of its spec) in the same row;
  Q3 the coverage table (rows whose first cell links a spec, columns: spec | notes | taken | skipped ...)
     lists every spec that has a notes section, once; `notes` equals the harvest count; the note numbers
     named in the skip cells and the note numbers cited by entries are disjoint and together cover n1..nN;
     `taken` equals the number of notes cited.
Exit 1 on any error. Stdlib only; reads only docs/specs/.
"""

import argparse
import os
import re
import sys
import unicodedata

NOTES = "Reimplementation notes"
RE_TAG = re.compile(r"\[([CIL])\]")
RE_HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RE_ANCHOR = re.compile(
    r"\b(?:fn|data):[A-Za-z_][A-Za-z0-9_]*@0x[0-9A-Fa-f]+"
    r"|\brun:\d{4}-\d{2}-\d{2}-[A-Za-z0-9-]*[A-Za-z0-9]"
    r"|\btbl:[A-Za-z0-9_]+\.txt(?::[A-Za-z0-9_]+)?"
    r"|\bstruct:[A-Za-z_][A-Za-z0-9_]*(?:\+0x[0-9A-Fa-f]+)?"
    r"|\bsrc:[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?"
    r"|\b0x00[0-9A-Fa-f]{6}\b"
)
RE_DOCLINK = re.compile(r"\]\((\.\./\.\./[^)\s]+)\)")
RE_LINK = re.compile(r"\[[^\]]*\]\(\.\./([^)#\s]+\.md)#([^)\s]+)\)((?:\s*n\d+)*)")
RE_SPECLINK = re.compile(r"\[[^\]]*\]\(\.\./([^)#\s]+\.md)(?:#[^)\s]*)?\)")
RE_NOTE = re.compile(r"n(\d+)")


def slug(heading):
    """GitHub heading anchor, as tools/gate.py gh_slug computes it (E8)."""
    t = re.sub(r"!?\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\([^)]*\)", r"\1", heading)
    parts = re.split(r"(`+)(.+?)\1", t)
    t = "".join(re.sub(r"<[^>]+>", "", p) if k % 3 == 0 else (p if k % 3 == 2 else "")
                for k, p in enumerate(parts))
    kept = [c for c in t.lower()
            if c in "-_ " or unicodedata.category(c)[0] in "LNM" or unicodedata.category(c) == "Pc"]
    return "".join(kept).replace(" ", "-")


def strip_fm(text):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end > 0:
            return text[4:end], text[end + 5:]
    return "", text


def sections(body):
    """{slug: text} of every heading's section (to the next heading of the same or higher level)."""
    lines = body.split("\n")
    heads = []
    fenced = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fenced = not fenced
            continue
        m = None if fenced else RE_HEAD.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    out = {}
    for k, (i, lvl, h) in enumerate(heads):
        j = len(lines)
        for i2, lvl2, _ in heads[k + 1:]:
            if lvl2 <= lvl:
                j = i2
                break
        out.setdefault(slug(h), "\n".join(lines[i + 1:j]))
    return out


def notes_of(body):
    """Top-level bullets of the notes section, or None when the spec has none."""
    lines = body.split("\n")
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "## " + NOTES)
    except StopIteration:
        return None
    bullets = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if re.match(r"^[-*] ", line):
            bullets.append(line[2:])
        elif bullets and (line.startswith(" ") or line.startswith("\t")) and line.strip():
            bullets[-1] += "\n" + line
        elif bullets and not line.strip():
            bullets[-1] += "\n"
    return [b.strip() for b in bullets]


def spec_files(root):
    base = os.path.join(root, "docs", "specs")
    out = []
    for d, _, fs in os.walk(base):
        for f in fs:
            if f.endswith(".md"):
                rel = os.path.relpath(os.path.join(d, f), base)
                if rel not in ("README.md",) and not rel.startswith("quirks" + os.sep):
                    out.append(rel)
    return sorted(out)


def load(root, rel):
    with open(os.path.join(root, "docs", "specs", rel), encoding="utf-8") as fh:
        return strip_fm(fh.read())


def cmd_harvest(a):
    rels = a.spec or spec_files(a.root)
    total = 0
    nspec = 0
    for rel in rels:
        fm, body = load(a.root, rel)
        notes = notes_of(body)
        if notes is None:
            continue
        nspec += 1
        st = re.search(r"^status:\s*(\S+)", fm, re.M)
        print(f"== {rel} status={st.group(1) if st else '?'} notes={len(notes)}")
        for k, b in enumerate(notes, 1):
            total += 1
            tags = "".join(sorted(set(RE_TAG.findall(b))))
            text = b if a.full else b.replace("\n", " ")[:160]
            print(f"n{k} [{tags}] {text}")
            if a.full:
                print()
    print(f"SUMMARY specs={nspec} notes={total}")
    return 0


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def cmd_check(a):
    idx = os.path.join(a.root, "docs", "specs", "quirks", "README.md")
    with open(idx, encoding="utf-8") as fh:
        _, ibody = strip_fm(fh.read())
    errs = []
    cache = {}

    def spec(rel):
        if rel not in cache:
            try:
                _, body = load(a.root, rel)
            except OSError:
                cache[rel] = None
            else:
                cache[rel] = (notes_of(body), sections(body))
        return cache[rel]

    ids = set()
    cited = {}
    coverage = {}
    entries = 0
    for ln, line in enumerate(ibody.split("\n"), 1):
        if not line.startswith("|"):
            continue
        c = cells(line)
        if re.fullmatch(r"Q\d+", c[0]):
            entries += 1
            qid = c[0]
            if qid in ids:
                errs.append(f"{ln}: Q1 {qid} used twice")
            ids.add(qid)
            if len(c) < 5:
                errs.append(f"{ln}: Q1 {qid} needs 5 cells (id, quirk, tag, anchors, source)")
                continue
            tags = RE_TAG.findall(c[2])
            anchors = RE_ANCHOR.findall(c[3]) + RE_DOCLINK.findall(c[3])
            links = RE_LINK.findall(c[4])
            if len(tags) != 1:
                errs.append(f"{ln}: Q1 {qid} tag cell holds {len(tags)} tags")
                continue
            if not anchors:
                errs.append(f"{ln}: Q1 {qid} anchors cell holds no anchor")
            if not links:
                errs.append(f"{ln}: Q1 {qid} source cell holds no ../<spec>.md#<fragment> link")
            texts = []
            untagged = []
            for rel, frag, nums in links:
                s = spec(rel)
                if s is None:
                    errs.append(f"{ln}: Q2 {qid} {rel}: no such spec")
                    continue
                notes, secs = s
                if frag == "reimplementation-notes":
                    ns = [int(x) for x in RE_NOTE.findall(nums)]
                    if not ns:
                        errs.append(f"{ln}: Q1 {qid} {rel}: notes link without note numbers")
                        continue
                    bad = [n for n in ns if not notes or n > len(notes)]
                    if bad:
                        errs.append(f"{ln}: Q2 {qid} {rel}: no note n{bad[0]}")
                        continue
                    text = "\n".join(notes[n - 1] for n in ns)
                    for n in ns:
                        cited.setdefault(rel, set()).add(n)
                    if not RE_TAG.search(text):
                        untagged.append(f"{rel}{nums}")
                        continue
                else:
                    if frag not in secs:
                        errs.append(f"{ln}: Q2 {qid} {rel}#{frag}: no such section")
                        continue
                    text = secs[frag]
                texts.append(text)
                if f"[{tags[0]}]" not in text:
                    errs.append(f"{ln}: Q2 {qid} {rel}#{frag}{nums}: tag [{tags[0]}] not in the cited text")
            if untagged and not texts:
                errs.append(f"{ln}: Q2 {qid} untagged note {untagged[0]} cited with no tagged source beside it")
            if texts:
                for an in anchors:
                    if not any(an in t for t in texts):
                        errs.append(f"{ln}: Q2 {qid}: anchor {an} in none of the tagged cited texts")
        else:
            m = RE_SPECLINK.match(c[0])
            if m and len(c) >= 3 and c[1].isdigit():
                rel = m.group(1)
                if rel in coverage:
                    errs.append(f"{ln}: Q3 {rel} listed twice in the coverage table")
                skipped = set()
                for cc in c[3:]:
                    for x in RE_NOTE.findall(cc):
                        if int(x) in skipped:
                            errs.append(f"{ln}: Q3 {rel} n{x} skipped twice")
                        skipped.add(int(x))
                coverage[rel] = (ln, int(c[1]), int(c[2]) if c[2].isdigit() else -1, skipped)

    want = {}
    for rel in spec_files(a.root):
        _, body = load(a.root, rel)
        n = notes_of(body)
        if n is not None:
            want[rel] = len(n)
    for rel, n in want.items():
        if rel not in coverage:
            errs.append(f"Q3 {rel}: has {n} notes but no coverage row")
    for rel, (ln, n, taken, skipped) in coverage.items():
        if rel not in want:
            errs.append(f"{ln}: Q3 {rel}: coverage row for a spec with no notes section")
            continue
        if n != want[rel]:
            errs.append(f"{ln}: Q3 {rel}: notes {n} but the spec has {want[rel]}")
        c = cited.get(rel, set())
        both = c & skipped
        if both:
            errs.append(f"{ln}: Q3 {rel}: n{min(both)} both cited and skipped")
        miss = set(range(1, want[rel] + 1)) - c - skipped
        if miss:
            errs.append(f"{ln}: Q3 {rel}: n{min(miss)} neither cited nor skipped ({len(miss)} such)")
        if taken != len(c):
            errs.append(f"{ln}: Q3 {rel}: taken {taken} but entries cite {len(c)} notes")
    for e in errs:
        print("quirks:", e)
    print(f"SUMMARY entries={entries} specs={len(coverage)} notes={sum(want.values())} "
          f"taken={sum(len(v) for v in cited.values())} errors={len(errs)}")
    return 1 if errs else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sub = p.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("harvest")
    h.add_argument("--spec", action="append")
    h.add_argument("--full", action="store_true")
    sub.add_parser("check")
    a = p.parse_args()
    return cmd_harvest(a) if a.cmd == "harvest" else cmd_check(a)


if __name__ == "__main__":
    sys.exit(main())
