"""Report MPQ archive signature status and basic header facts via the system StormLib.

Usage: python3 -I tools/mpq_verify.py <archive.mpq> [...]

For each archive prints: SFileVerifyArchive result (no / weak / strong signature, pass/fail),
plus the MPQ v1 header fields parsed directly (offset, header size, archive size, format version,
sector shift, hash/block table entry counts). Loads libstorm.so through ctypes (stdlib); opens
archives read-only. Signature result codes are from StormLib.h.
"""
import ctypes
import ctypes.util
import struct
import sys

VERIFY = {0: "no signature", 1: "verify error", 2: "weak signature OK", 3: "weak signature FAILED",
          4: "strong signature OK", 5: "strong signature FAILED"}
STREAM_FLAG_READ_ONLY = 0x00000100
MPQ_OPEN_NO_LISTFILE = 0x00010000


def header(path):
    """Find the 'MPQ\\x1a' header (searched at 512-byte boundaries) and decode the v1 fields."""
    with open(path, "rb") as f:
        off = 0
        while True:
            f.seek(off)
            b = f.read(32)
            if len(b) < 32:
                return {}
            if b[:4] == b"MPQ\x1a":
                v = struct.unpack("<4sIIHHIIII", b)
                return dict(offset=off, header_size=v[1], archive_size=v[2], format_version=v[3],
                            sector_shift=v[4], hash_entries=v[7], block_entries=v[8])
            off += 512


def load():
    name = ctypes.util.find_library("storm") or "libstorm.so"
    lib = ctypes.CDLL(name)
    lib.SFileOpenArchive.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)]
    lib.SFileOpenArchive.restype = ctypes.c_bool
    lib.SFileVerifyArchive.argtypes = [ctypes.c_void_p]
    lib.SFileVerifyArchive.restype = ctypes.c_uint
    lib.SFileCloseArchive.argtypes = [ctypes.c_void_p]
    lib.SFileCloseArchive.restype = ctypes.c_bool
    return lib


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    lib = load()
    for path in argv:
        h = ctypes.c_void_p()
        if not lib.SFileOpenArchive(path.encode(), 0, STREAM_FLAG_READ_ONLY | MPQ_OPEN_NO_LISTFILE, ctypes.byref(h)):
            print("%s: OPEN FAILED (errno %d)" % (path, ctypes.get_errno()))
            continue
        facts = header(path)
        res = lib.SFileVerifyArchive(h)
        lib.SFileCloseArchive(h)
        print("%s: %s | %s" % (path, VERIFY.get(res, res), " ".join("%s=%s" % kv for kv in facts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
