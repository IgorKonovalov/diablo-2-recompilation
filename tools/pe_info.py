"""Print identifying facts about a PE file: machine, timestamp, image base, sections, version resource.

Usage: python3 -I tools/pe_info.py <file.exe> [...]

Stdlib only. Read-only. Used to check that the pinned Game.exe is the stock Blizzard build.
"""
import datetime
import hashlib
import struct
import sys


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def parse(path):
    data = open(path, "rb").read()
    out = {"path": path, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    if data[:2] != b"MZ":
        raise ValueError("no MZ header")
    pe = u32(data, 0x3C)
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("no PE signature")
    coff = pe + 4
    machine, nsec, ts = u16(data, coff), u16(data, coff + 2), u32(data, coff + 4)
    optsz, chars = u16(data, coff + 16), u16(data, coff + 18)
    opt = coff + 20
    magic = u16(data, opt)
    if magic != 0x10B:
        raise ValueError("not PE32 (magic %#x)" % magic)
    out.update(
        machine=machine,
        timestamp=ts,
        timestamp_utc=datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).isoformat(),
        characteristics=chars,
        linker="%d.%d" % (data[opt + 2], data[opt + 3]),
        entry_rva=u32(data, opt + 16),
        image_base=u32(data, opt + 28),
        size_of_image=u32(data, opt + 56),
        checksum=u32(data, opt + 64),
        subsystem=u16(data, opt + 68),
    )
    ndirs = u32(data, opt + 92)
    dirs = [(u32(data, opt + 96 + 8 * i), u32(data, opt + 100 + 8 * i)) for i in range(ndirs)]
    sections = []
    so = opt + optsz
    for i in range(nsec):
        o = so + 40 * i
        name = data[o:o + 8].rstrip(b"\0").decode("latin-1")
        vsize, va, rsize, rptr = struct.unpack_from("<IIII", data, o + 8)
        sections.append(dict(name=name, va=va, vsize=vsize, raw=rptr, rsize=rsize,
                             flags=u32(data, o + 36),
                             sha256=hashlib.sha256(data[rptr:rptr + rsize]).hexdigest()))
    out["sections"] = sections
    out["overlay"] = len(data) - max((s["raw"] + s["rsize"]) for s in sections)

    def rva2off(rva):
        for s in sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rsize"]):
                return rva - s["va"] + s["raw"]
        return None

    out["imports"] = imports(data, dirs, rva2off) if len(dirs) > 1 else []
    out["version"] = version(data, dirs, rva2off) if len(dirs) > 2 else {}
    return out


def imports(data, dirs, rva2off):
    rva, _ = dirs[1]
    off = rva2off(rva) if rva else None
    dlls = []
    while off is not None:
        name_rva = u32(data, off + 12)
        if name_rva == 0:
            break
        no = rva2off(name_rva)
        dlls.append(data[no:data.index(b"\0", no)].decode("latin-1"))
        off += 20
    return dlls


def version(data, dirs, rva2off):
    """Find RT_VERSION (type 16) and decode VS_FIXEDFILEINFO plus the StringFileInfo pairs."""
    rva, _ = dirs[2]
    if not rva:
        return {}
    base = rva2off(rva)

    def entries(off):
        named, ids = u16(data, off + 12), u16(data, off + 14)
        for i in range(named + ids):
            e = off + 16 + 8 * i
            yield u32(data, e), u32(data, e + 4)

    for ident, tgt in entries(base):
        if ident != 16:
            continue
        node = tgt
        while node & 0x80000000:  # descend name/lang levels to the first leaf
            node = next(entries(base + (node & 0x7FFFFFFF)))[1]
        drva, dsize = u32(data, base + node), u32(data, base + node + 4)
        blob = data[rva2off(drva):rva2off(drva) + dsize]
        res = {}
        i = blob.find(struct.pack("<I", 0xFEEF04BD))
        if i >= 0:
            ms, ls, pms, pls = struct.unpack_from("<IIII", blob, i + 8)
            res["FileVersion(fixed)"] = "%d.%d.%d.%d" % (ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF)
            res["ProductVersion(fixed)"] = "%d.%d.%d.%d" % (pms >> 16, pms & 0xFFFF, pls >> 16, pls & 0xFFFF)
        text = blob.decode("utf-16-le", "replace")
        for key in ("CompanyName", "FileDescription", "FileVersion", "InternalName",
                    "LegalCopyright", "OriginalFilename", "ProductName", "ProductVersion"):
            k = text.find(key + "\0")
            if k >= 0:
                v = text[k + len(key):].lstrip("\0").split("\0", 1)[0]
                res[key] = v
        return res
    return {}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    for p in argv:
        info = parse(p)
        for k, v in info.items():
            if k == "sections":
                print("sections:")
                for s in v:
                    print("  %-8s va=%#010x vsize=%#09x raw=%#09x rsize=%#09x flags=%#010x sha256=%s"
                          % (s["name"], s["va"], s["vsize"], s["raw"], s["rsize"], s["flags"], s["sha256"]))
            elif k == "imports":
                print("imports: " + ", ".join(v))
            elif k == "version":
                for vk, vv in v.items():
                    print("version.%s: %s" % (vk, vv))
            elif isinstance(v, int) and k not in ("size", "overlay", "timestamp"):
                print("%s: %#x" % (k, v))
            else:
                print("%s: %s" % (k, v))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
