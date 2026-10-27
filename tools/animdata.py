"""Parse Diablo II animdata.d2 (the per-animation frame count, speed and frame event bytes).

Usage:
  python3 -I tools/animdata.py survey <root>                 parse <root>/data/global/animdata.d2, every check,
                                                             the COF join, histograms, the SURVEY line
  python3 -I tools/animdata.py dump <file.d2> [NAME ...]     one line per record (all, or the named COF names)
  python3 -I tools/animdata.py compare <a.d2> <b.d2>         records only in a, only in b, and changed
  python3 -I tools/animdata.py dups <file.d2>                the names held by more than one record

<root> is a merged data tree (e.g. workspace/merged). Layout in docs/formats/animdata.md:

  the file is 256 blocks in order, block b = u32 count, then count records of 160 bytes:
    +0x00 char[8]  name   the COF name (token + mode + weapon class), upper case, NUL padded
    +0x08 u32      frames frames per direction
    +0x0C u32      speed
    +0x10 u8[144]  event  one byte per frame; frames past `frames` are zero
  every record sits in block (sum of its name bytes) & 0xFF

survey checks that the blocks consume the file exactly, every name is NUL-terminated and NUL padded, every record is
in its hash block, and no event byte is set at or past `frames`; it joins each record with the .cof of the same name
(case-insensitive, any directory under data/global) and compares the COF's frames_per_dir, frame bytes and rate with
the record. It ends with one machine-readable line:
  SURVEY animdata records=N blocks=N empty_blocks=N names=N dup_names=N dup_differ=N hash_bad=N errors=N
         frames_max=N frames_over_144=N speed_distinct=N speed_zero=N ev1=N ev2=N ev3=N ev_other=N ev_past_frames=N recs_with_events=N
         cof_files=N cof_join=N rec_no_cof=N cof_multi=N
         cof_no_rec=N cof_frames_eq=N cof_events_eq=N cof_rate_eq=N
and exits 0 iff errors == 0. Meanings are [L] (no code anchor). Stdlib only. Read-only.
"""
import collections
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

BLOCKS = 256
RECORD = 160
NAME = 8
EVENTS = 144


class AnimDataError(ValueError):
    pass


Record = collections.namedtuple("Record", "block slot name frames speed events")


def name_hash(name):
    """Block index of a name: the sum of its bytes, low 8 bits (upper-case ASCII as stored)."""
    return sum(name.encode("ascii")) & 0xFF


def parse(data):
    """-> list of Record in file order. Raises AnimDataError on any structural fault."""
    off, recs = 0, []
    for b in range(BLOCKS):
        if off + 4 > len(data):
            raise AnimDataError("block %d: count past end of file" % b)
        n = struct.unpack_from("<I", data, off)[0]
        off += 4
        if off + n * RECORD > len(data):
            raise AnimDataError("block %d: %d records past end of file" % (b, n))
        for slot in range(n):
            raw = data[off:off + NAME]
            nul = raw.find(b"\0")
            if nul <= 0 or any(raw[nul:]):
                raise AnimDataError("block %d slot %d: name not NUL-terminated and padded: %r" % (b, slot, raw))
            frames, speed = struct.unpack_from("<II", data, off + NAME)
            ev = bytes(data[off + 16:off + RECORD])
            recs.append(Record(b, slot, raw[:nul].decode("ascii"), frames, speed, ev))
            off += RECORD
    if off != len(data):
        raise AnimDataError("%d bytes after block 255" % (len(data) - off))
    return recs


def load(path):
    with open(path, "rb") as f:
        return parse(f.read())


def lookup(recs, name):
    """All records named `name` (case-insensitive), in file order (the game's pick among duplicates is [L])."""
    u = name.upper()
    return [r for r in recs if r.name == u]


def events_of(r):
    """[(frame, byte)] of the non-zero event bytes."""
    return [(i, v) for i, v in enumerate(r.events) if v]


def fmt(r):
    ev = " ".join("%d:%d" % fv for fv in events_of(r)) or "-"
    return "%-8s block %3d slot %2d frames %3d speed %4d events %s" % (r.name, r.block, r.slot, r.frames, r.speed, ev)


def hist(vals, top=None):
    c = collections.Counter(vals).most_common(top)
    return ", ".join("%s x%d" % kv for kv in c)


def cof_index(root):
    """{upper-case cof basename: [path, ...]} over <root>/data/global."""
    idx = collections.defaultdict(list)
    base = os.path.join(root, "data", "global")
    for dp, _dn, fn in os.walk(base):
        for f in fn:
            if f.lower().endswith(".cof"):
                idx[f[:-4].upper()].append(os.path.join(dp, f))
    return idx


def cmd_survey(root):
    import cof
    path = os.path.join(root, "data", "global", "animdata.d2")
    kv = collections.OrderedDict()
    errors = 0
    try:
        recs = load(path)
    except (OSError, AnimDataError) as e:
        print("ERROR", e)
        print("SURVEY animdata records=0 errors=1")
        return 1
    hash_bad = sum(1 for r in recs if name_hash(r.name) != r.block)
    per_block = collections.Counter(r.block for r in recs)
    by_name = collections.defaultdict(list)
    for r in recs:
        by_name[r.name].append(r)
    dups = {n: rs for n, rs in by_name.items() if len(rs) > 1}
    dup_differ = sum(1 for rs in dups.values() if len({(r.frames, r.speed, r.events) for r in rs}) > 1)
    ev = collections.Counter()
    past = 0
    with_ev = 0
    for r in recs:
        e = events_of(r)
        with_ev += bool(e)
        for i, v in e:
            ev[v] += 1
            past += i >= r.frames
    zero_frames = sum(1 for r in recs if r.frames == 0)
    over = sum(1 for r in recs if r.frames > EVENTS)
    errors += hash_bad + zero_frames
    print("file %s: %d bytes, %d records in %d blocks (%d empty)" % (
        path, os.path.getsize(path), len(recs), BLOCKS, BLOCKS - len(per_block)))
    print("records per block: min %d max %d" % (min(per_block.get(b, 0) for b in range(BLOCKS)), max(per_block.values())))
    print("names: %d distinct, %d held by two or more records (%d of them differ in content)" % (
        len(by_name), len(dups), dup_differ))
    print("hash: %d records outside block (sum of name bytes) & 0xFF" % hash_bad)
    print("name length: %s" % hist(len(r.name) for r in recs))
    for r in recs:
        if r.frames > EVENTS:
            print("NOTE %s has frames %d, more than the %d event bytes" % (r.name, r.frames, EVENTS))
    print("frames: %d..%d; top %s; %d with frames > %d" % (
        min(r.frames for r in recs), max(r.frames for r in recs), hist((r.frames for r in recs), 10), over, EVENTS))
    print("speed: %d distinct, %d..%d; top %s" % (
        len({r.speed for r in recs}), min(r.speed for r in recs), max(r.speed for r in recs),
        hist((r.speed for r in recs), 12)))
    print("event bytes: %s; %d set at or past frames; records with events %d; per record %s" % (
        hist(sorted(ev.elements())), past, with_ev, hist(len(events_of(r)) for r in recs)))
    # the leading token class (first two chars) by COF directory family
    idx = cof_index(root)
    cof_files = sum(len(v) for v in idx.values())
    join = rec_no_cof = 0
    f_eq = e_eq = rate_eq = 0
    fam = collections.Counter()
    missing_fam = collections.Counter()
    diffs = []
    multi = 0
    for name, rs in sorted(by_name.items()):
        paths = idx.get(name)
        if not paths:
            rec_no_cof += 1
            missing_fam[name[:2]] += 0
            continue
        join += 1
        fam[os.path.relpath(paths[0], os.path.join(root, "data", "global")).split(os.sep)[0]] += 1
        cofs = []
        for p in paths:
            with open(p, "rb") as f:
                cofs.append(cof.parse(f.read()))
        multi += len(rs) > 1 or len(cofs) > 1
        pairs = [(r, c) for r in rs for c in cofs]
        fe = any(c["frames_per_dir"] == r.frames for r, c in pairs)
        ee = any([(i, v) for i, v in enumerate(c["frame_bytes"]) if v] == events_of(r) for r, c in pairs)
        re_ = any(c["rate"] == r.speed for r, c in pairs)
        f_eq += fe
        e_eq += ee
        rate_eq += re_
        if not (fe and ee and re_):
            for r, c in pairs:
                diffs.append((name, c["frames_per_dir"], r.frames, [(i, v) for i, v in enumerate(c["frame_bytes"]) if v],
                              events_of(r), c["rate"], r.speed))
    cof_no_rec = sorted(n for n in idx if n not in by_name)
    print("COF join (case-insensitive name): %d of %d names have a .cof (%s); %d names have none; "
          "%d .cof files (%d names) have no record" % (join, len(by_name), hist(fam.elements()), rec_no_cof,
                                                       cof_files, len(cof_no_rec)))
    print("  of the %d joined (%d with two or more records or .cof files; a field agrees when some pair agrees): "
          "frames_per_dir == frames %d, frame bytes == event bytes %d, rate == speed %d" % (
              join, multi, f_eq, e_eq, rate_eq))
    for d in diffs[:40]:
        print("  DIFF %-8s cof F %d rec %d | cof ev %s rec %s | cof rate %d rec speed %d" % (
            d[0], d[1], d[2], d[3], d[4], d[5], d[6]))
    if len(diffs) > 40:
        print("  ... %d more" % (len(diffs) - 40))
    print("  .cof names with no record: %s" % (" ".join(cof_no_rec[:60]) + (" ..." if len(cof_no_rec) > 60 else "")))
    names_no_cof = sorted(n for n in by_name if n not in idx)
    print("  record names with no .cof: %s" % (" ".join(names_no_cof[:60]) + (" ..." if len(names_no_cof) > 60 else "")))
    kv.update(records=len(recs), blocks=BLOCKS, empty_blocks=BLOCKS - len(per_block), names=len(by_name),
              dup_names=len(dups), dup_differ=dup_differ, hash_bad=hash_bad, errors=errors,
              frames_max=max(r.frames for r in recs), frames_over_144=over,
              speed_distinct=len({r.speed for r in recs}),
              speed_zero=sum(1 for r in recs if r.speed == 0),
              ev1=ev[1], ev2=ev[2], ev3=ev[3], ev_other=sum(n for k, n in ev.items() if k not in (1, 2, 3)),
              ev_past_frames=past, recs_with_events=with_ev, cof_files=cof_files, cof_join=join,
              rec_no_cof=rec_no_cof, cof_multi=multi, cof_no_rec=len(cof_no_rec), cof_frames_eq=f_eq, cof_events_eq=e_eq,
              cof_rate_eq=rate_eq)
    print("SURVEY animdata " + " ".join("%s=%d" % x for x in kv.items()))
    return 0 if errors == 0 else 1


def cmd_dump(path, names):
    recs = load(path)
    if names:
        for n in names:
            rs = lookup(recs, n)
            if not rs:
                print("%-8s (no record)" % n.upper())
            for r in rs:
                print(fmt(r))
    else:
        for r in recs:
            print(fmt(r))
    return 0


def cmd_dups(path):
    recs = load(path)
    by = collections.defaultdict(list)
    for r in recs:
        by[r.name].append(r)
    for n, rs in sorted(by.items()):
        if len(rs) > 1:
            same = len({(r.frames, r.speed, r.events) for r in rs}) == 1
            print("%s x%d %s" % (n, len(rs), "identical" if same else "DIFFER"))
            for r in rs:
                print("   " + fmt(r))
    return 0


def cmd_compare(a, b):
    ra, rb = load(a), load(b)
    da = {r.name: r for r in reversed(ra)}   # first record of a name
    db = {r.name: r for r in reversed(rb)}
    only_a = sorted(set(da) - set(db))
    only_b = sorted(set(db) - set(da))
    changed = collections.Counter()
    ex = collections.defaultdict(list)
    for n in sorted(set(da) & set(db)):
        x, y = da[n], db[n]
        for what, u, v in (("frames", x.frames, y.frames), ("speed", x.speed, y.speed),
                           ("events", events_of(x), events_of(y))):
            if u != v:
                changed[what] += 1
                ex[what].append("%s %s->%s" % (n, u, v))
    print("a: %d records %d names; b: %d records %d names" % (len(ra), len(da), len(rb), len(db)))
    print("only in a: %d (%s)" % (len(only_a), hist(n[:2] for n in only_a)))
    print("only in b: %d (%s)" % (len(only_b), hist(n[:2] for n in only_b)))
    print("in both: %d; changed frames %d, speed %d, events %d" % (
        len(set(da) & set(db)), changed["frames"], changed["speed"], changed["events"]))
    for what in ("frames", "speed", "events"):
        for line in ex[what][:15]:
            print("  %s %s" % (what, line))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[0] == "survey":
        return cmd_survey(argv[1])
    if len(argv) >= 2 and argv[0] == "dump":
        return cmd_dump(argv[1], argv[2:])
    if len(argv) == 2 and argv[0] == "dups":
        return cmd_dups(argv[1])
    if len(argv) == 3 and argv[0] == "compare":
        return cmd_compare(argv[1], argv[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
