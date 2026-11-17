"""Tests of the schematic mode of tools/maze_anim.py and tools/tc_anim.py (ADR-0036, plan 0070 Phase 2b).

Run: python3 -I tools/test_anim_schematic.py     (needs workspace/merged: skipped without it; stdlib only)

Each tool runs in schematic mode in a child process with the art decoders blocked: importing dt1, dc6, item_art, palette
or maze_render raises, opening a .dt1, .dc6, .dcc or .pl2 file or anything under a palette folder raises, and the ds1
tile-layer entry points (_Tiles, _scan_cells, ds1_files, and the "layers" key of a parsed file) raise. The preset-unit
model (tools/drlg.py PresetUnitData.ds1) reads a DS1's object list and its floor0 cell values for the draw counts of
the map scan, so the .ds1 file may be opened and that one caller may read the layers; no drawing code may.
The run must succeed. Then: every output file carries the marker, schematic.json matches the files' sha256, the palette
is ours, the full mode writes no marker and no schematic.json, and the steps (text and calculations) of the two modes
are equal for the same arguments, apart from the lines that come from the art (warp lines, the icon line).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "workspace", "merged")
OUT = os.path.join(ROOT, "workspace", "render", "test-anim")
sys.path.insert(0, HERE)
import anim_common  # noqa: E402

BLOCKED = ("dt1", "dc6", "item_art", "palette", "maze_render")
ART_SUFFIX = (".dt1", ".dc6", ".dcc", ".pl2")
ART_LINES = ("Warp", "This preset holds a warp", "Inventory icon", "Name card")    # lines that come from the art


def child(tool, args):
    """Run tool.main(args) with the art decoders blocked. Used under --child only."""
    import builtins
    import importlib.abc
    import io

    class Block(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name.split(".")[0] in BLOCKED:
                raise ImportError("art decoder %s blocked" % name)
    sys.meta_path.insert(0, Block())
    import ds1

    def no(*_a, **_k):
        raise RuntimeError("ds1 tile-layer entry point blocked")
    for n in ("_Tiles", "_scan_cells", "ds1_files"):
        setattr(ds1, n, no)
    real_parse = ds1.parse

    def model_call(depth=2):
        """True when the caller is the preset-unit model of tools/drlg.py (PresetUnitData.ds1): it parses the DS1 for
        its object list (the map scan's keep/drop draws) and keeps a copy of floor0 in its cache. That is model input,
        not drawing; no other caller may parse a DS1 or read a layer."""
        f = sys._getframe(depth)
        return f.f_code.co_name == "ds1" and os.path.basename(f.f_code.co_filename) == "drlg.py"

    class Hidden(dict):
        """A dict whose secret keys are out of the mapping (no items, values, iteration or copy reaches them) and
        whose __getitem__ hands them out only to the callers `ok` admits."""
        def __init__(self, d, secret, ok, what):
            dict.__init__(self, {k: v for k, v in d.items() if k not in secret})
            self._s, self._ok, self._what = {k: d[k] for k in secret if k in d}, ok, what

        def __getitem__(self, k):
            if k in self._s:
                if not self._ok():
                    raise RuntimeError(self._what)
                return self._s[k]
            return dict.__getitem__(self, k)

        def get(self, k, d=None):
            return self[k] if k in self._s or k in self else d

    def parse(data):
        if not model_call():
            raise RuntimeError("ds1.parse outside the preset-unit model blocked")
        return Hidden(real_parse(data), ("layers",), model_call, "ds1 tile layers blocked")
    ds1.parse = parse
    import drlg
    real_pu = drlg.PresetUnitData.ds1

    def in_drlg():
        return os.path.basename(sys._getframe(2).f_code.co_filename) == "drlg.py"

    def pu_ds1(self, cell):     # the cached floor0 copy reaches no caller outside tools/drlg.py
        d = real_pu(self, cell)
        return d if isinstance(d, Hidden) else Hidden(d, ("floor0",), in_drlg, "floor0 outside tools/drlg.py blocked")
    drlg.PresetUnitData.ds1 = pu_ds1
    real_open = builtins.open

    def guard_open(file, *a, **k):
        p = os.fsdecode(file) if isinstance(file, (str, bytes, os.PathLike)) else ""
        low = p.lower().replace("\\", "/")
        if low.endswith(ART_SUFFIX) or "/palette/" in low:
            raise RuntimeError("art file %s blocked" % p)
        return real_open(file, *a, **k)
    builtins.open = io.open = guard_open
    mod = __import__(tool[:-3])
    rc = mod.main(args)
    bad = [m for m in BLOCKED if m in sys.modules]
    if bad:
        raise SystemExit("blocked modules were imported: %s" % bad)
    return rc


def run(tool, args, blocked):
    cmd = [sys.executable, "-I", os.path.join(HERE, "test_anim_schematic.py")] + (
        ["--child", tool] if blocked else ["--plain", tool]) + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)


def steps_of(out, schematic):
    with open(os.path.join(out, "steps.json")) as fh:
        d = json.load(fh)
    return d["steps"] if schematic else d


def keep(caps):
    return [dict(text=c["text"], calc=[x for x in c["calc"] if not x.startswith(ART_LINES)]) for c in caps]


@unittest.skipUnless(os.path.isdir(DATA), "no workspace/merged (game data)")
class SchematicModes(unittest.TestCase):
    cases = {
        "maze_anim.py": (["36", "0xc0ffee"], "maze.gif"),
        "tc_anim.py": (["andariel", "0xc0ffee", "--difficulty", "2", "--mf", "200"], "tc.gif"),
    }

    @classmethod
    def setUpClass(cls):
        cls.out = {}
        for tool, (args, _gif) in cls.cases.items():
            for mode in ("schematic", "full"):
                out = os.path.join(OUT, "%s-%s" % (tool[:-3], mode))
                os.makedirs(out, exist_ok=True)
                for f in os.listdir(out):
                    os.unlink(os.path.join(out, f))
                a = [DATA] + args + ["--out", out] + (["--schematic"] if mode == "schematic" else [])
                r = run(tool, a, blocked=(mode == "schematic"))
                cls.out[tool, mode] = (out, r)

    def test_schematic_runs_with_art_decoders_blocked(self):
        for tool in self.cases:
            out, r = self.out[tool, "schematic"]
            self.assertEqual(r.returncode, 0, "%s: %s" % (tool, r.stderr[-800:]))
            self.assertTrue(os.path.isfile(os.path.join(out, "schematic.json")))

    def test_marker_in_every_file_and_list_matches(self):
        for tool, (args, gif) in self.cases.items():
            out, _r = self.out[tool, "schematic"]
            with open(os.path.join(out, "schematic.json")) as fh:
                sj = json.load(fh)
            self.assertEqual(sj["marker"], anim_common.MARKER)
            self.assertEqual(sj["tool"], tool[:-3])
            self.assertEqual(sj["args"], [str(int(a, 16)) if a.startswith("0x") else a for a in args])
            names = sorted(os.listdir(out))
            self.assertEqual(names, sorted(list(sj["files"]) + ["schematic.json"]))
            for fname, sha in sj["files"].items():
                f = dict(name=fname, sha256=sha)
                with open(os.path.join(out, f["name"]), "rb") as fh:
                    data = fh.read()
                self.assertEqual(hashlib.sha256(data).hexdigest(), f["sha256"], f["name"])
                if f["name"].endswith(".png"):
                    self.assertIn(b"tEXt" + anim_common.MARKER_NAME.encode() + b"\0" + anim_common.MARKER.encode(), data)
                elif f["name"].endswith(".gif"):
                    self.assertIn(b"\x21\xfe", data[:1200])
                    self.assertIn(anim_common.MARKER.encode(), data[:1200])
                elif f["name"] == "index.html":
                    self.assertIn("<!-- %s" % anim_common.MARKER, data.decode())
                    self.assertNotIn("<meta", data.decode())
                    data.decode("ascii")
                    self.assertIn("setAttribute('src'", data.decode())
                elif f["name"] == "steps.json":
                    self.assertEqual(json.loads(data)["schematic_only"], anim_common.MARKER)
                else:
                    self.fail("unexpected file %s" % f["name"])

    def test_palette_is_ours(self):
        _idx, pal = anim_common.schem_palette()
        for tool in self.cases:
            out, _r = self.out[tool, "schematic"]
            for n in sorted(os.listdir(out)):
                if n.endswith(".png"):
                    with open(os.path.join(out, n), "rb") as fh:
                        data = fh.read()
                    m = re.search(rb"PLTE", data)
                    self.assertEqual(data[m.end():m.end() + 768], pal, n)
                    self.assertNotIn(b"tRNS", data)

    def test_full_mode_never_marks(self):
        for tool, (_args, _gif) in self.cases.items():
            out, r = self.out[tool, "full"]
            self.assertEqual(r.returncode, 0, "%s: %s" % (tool, r.stderr[-800:]))
            self.assertFalse(os.path.exists(os.path.join(out, "schematic.json")))
            for n in os.listdir(out):
                with open(os.path.join(out, n), "rb") as fh:
                    data = fh.read()
                self.assertNotIn(anim_common.MARKER.encode(), data, "%s/%s" % (tool, n))
                self.assertNotIn(anim_common.MARKER_NAME.encode(), data, "%s/%s" % (tool, n))
                self.assertNotIn(b"schematic_only", data, "%s/%s" % (tool, n))
            self.assertIsInstance(steps_of(out, False), list)

    def test_steps_equal_between_modes(self):
        for tool in self.cases:
            s = steps_of(self.out[tool, "schematic"][0], True)
            f = steps_of(self.out[tool, "full"][0], False)
            self.assertEqual(len(s), len(f), tool)
            self.assertEqual(keep(s), keep(f), tool)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] in ("--child", "--plain"):
        tool, rest = sys.argv[2], sys.argv[3:]
        sys.path.insert(0, HERE)
        if sys.argv[1] == "--child":
            sys.exit(child(tool, rest))
        sys.exit(__import__(tool[:-3]).main(rest))
    unittest.main()
