"""Regenerate every rendered image under <out> (default workspace/render) from a merged data tree.

Usage:
  python3 -I tools/render_all.py <root> [out]

Runs, in order: palette swatches (palette.py swatch), DT1 tiles (dt1.py render), DS1 previews
(ds1.py render), DC6 frames (dc6.py render) and DCC frames (dcc.py render). Steps whose module or
render function is missing are skipped and named. Exit 0 only if every step that ran returned 0.
<out> is disposable (ADR-0005): delete it and rerun. Stdlib only.
"""
import importlib
import os
import sys

STEPS = [  # (module, function, takes_out_dir_as)
    ("palette", "swatch", "palette"),
    ("dt1", "render", ""),
    ("ds1", "render", ""),
    ("dc6", "render", ""),
    ("dcc", "render", ""),
]


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    root = argv[0]
    out = argv[1] if len(argv) > 1 else os.path.join(root, "..", "render")
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    rc = 0
    for mod, fn, sub in STEPS:
        try:
            f = getattr(importlib.import_module(mod), fn)
        except (ImportError, AttributeError):
            print("== skip %s.%s (not implemented)" % (mod, fn))
            continue
        print("== %s.%s" % (mod, fn))
        r = f(root, os.path.join(out, sub) if sub else out)
        rc = rc or r
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
