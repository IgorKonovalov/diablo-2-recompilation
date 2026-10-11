"""Write the edited charstats.txt and cubemain.txt used to make the D2S item samples (plan 0005 Phase 4).

Usage:
  python3 -I tools/d2s_samples.py <merged-excel-dir> <out-excel-dir> [variant]

variant (default `b`) picks the recipe set a sample was made with (docs/formats/d2s.md, "Samples"):
  b     the last state: qitama, qitasn, qitbarb, qitdru, qitnecb, qitpal, qitsor
  a     Necromancer `lsd,hiq,sock=3` / `cap,eth` / `buc,low` (qitnec) and Barbarian
        `lsd,mag,eth,sock=2` / `r01` / `gsv` (qitbar); the other classes as in `b`
  lvl1  `a` with every output at item level 1 instead of 99 (qit1ama; only the Amazon recipe,
        identical in every variant, reaches that save)

Reads the shipped .txt tables and writes two edited copies into <out-excel-dir>, which is the
data/global/excel directory of a separate game directory run with `-direct -txt`
(docs/formats/d2s.md, "Samples"). Edits:
  - charstats: every class also starts with a Horadric Cube (`box`), a ring, an amulet, a jewel and
    a small charm in the inventory (item6..item10);
  - cubemain: one recipe per class (`class` column), input one Scroll of Identify (`isc`), three
    outputs at item level 99 (1 in `lvl1`) that cover the item qualities and flags the save format branches on.
Stdlib only. Never writes into workspace/merged.
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
variant = sys.argv[3] if len(sys.argv) > 3 else "b"
if variant not in ("a", "b", "lvl1"):
    sys.exit("variant must be a, b or lvl1")
def rd(n):
    t = open(f"{src}/{n}", encoding="latin1", newline="").read()
    return [l.split("\t") for l in t.split("\r\n") if l]
def wr(n, rows):
    open(f"{dst}/{n}", "w", encoding="latin1", newline="").write("".join("\t".join(r) + "\r\n" for r in rows))
cs = rd("charstats.txt"); h = cs[0]; ix = {c: i for i, c in enumerate(h)}
extra = [("box", 1), ("rin", 1), ("amu", 1), ("jew", 1), ("cm1", 1)]
for r in cs[1:]:
    if r[0] == "Expansion":
        continue
    for k, (code, n) in enumerate(extra, start=6):
        r[ix[f"item{k}"]], r[ix[f"item{k}loc"]], r[ix[f"item{k}count"]] = code, "", str(n)
wr("charstats.txt", cs)
cm = rd("cubemain.txt"); h = cm[0]; ix = {c: i for i, c in enumerate(h)}
recipes = {
    "ama": ['"rin,uni"', '"amu,rar"', "Angelic Halo"],
    "sor": ['"cap,uni"', '"lgl,mag"', '"amu,uni"'],
    "nec": ['"cap,low"', '"buc,eth"', "aqv"],
    "pal": ['"jew,mag"', '"cm1,mag"', '"jew,rar"'],
    "bar": ['"lsd,nor,eth,sock=2"', "r03", "r01"],
    "dru": ['"rin,crf"', "key", "tbk"],
    "ass": ['"jav,mag"', '"lgl,uni"', "aqv"],
}
if variant in ("a", "lvl1"):
    recipes["nec"] = ['"lsd,hiq,sock=3"', '"cap,eth"', '"buc,low"']
    recipes["bar"] = ['"lsd,mag,eth,sock=2"', "r01", "gsv"]
lvl = "1" if variant == "lvl1" else "99"
for cls, (a, b, c) in recipes.items():
    r = [""] * len(h)
    r[ix["description"]] = f"sample {cls}"
    r[ix["enabled"]], r[ix["version"]], r[ix["class"]] = "1", "100", cls
    r[ix["numinputs"]], r[ix["input 1"]] = "1", "isc"
    r[ix["output"]], r[ix["output b"]], r[ix["output c"]] = a, b, c
    r[ix["lvl"]], r[ix["b lvl"]], r[ix["c lvl"]] = lvl, lvl, lvl
    r[ix["*eol"]] = "0"
    cm.append(r)
wr("cubemain.txt", cm)
print("ok", variant, len(cm) - 1, "recipes")
