"""Shared helpers of the animation tools (tools/maze_anim.py, tools/tc_anim.py): the 5x7 bitmap font, text
wrapping, a stdlib LZW/GIF encoder, the local step-through HTML page and the output-directory guard.

Illustration helpers only: nothing here models the game. Outputs of the tools stay under workspace/ (safe_out).
Stdlib only.
"""
import hashlib
import json
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- 5x7 bitmap font (upper case only)
_F = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    ".": "00000 00000 00000 00000 00000 01100 01100", ",": "00000 00000 00000 00000 01100 00100 01000",
    ":": "00000 01100 01100 00000 01100 01100 00000", "=": "00000 00000 11111 00000 11111 00000 00000",
    "%": "11001 11010 00010 00100 01000 01011 10011", "#": "01010 01010 11111 01010 11111 01010 01010",
    "+": "00000 00100 00100 11111 00100 00100 00000", "-": "00000 00000 00000 11111 00000 00000 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000", "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000", ">": "10000 01000 00100 00010 00100 01000 10000",
    "<": "00001 00010 00100 01000 00100 00010 00001", "'": "00100 00100 01000 00000 00000 00000 00000",
    "_": "00000 00000 00000 00000 00000 00000 11111", " ": "00000 00000 00000 00000 00000 00000 00000",
    "{": "00110 00100 00100 01000 00100 00100 00110", "}": "01100 00100 00100 00010 00100 00100 01100",
    "[": "01110 01000 01000 01000 01000 01000 01110", "]": "01110 00010 00010 00010 00010 00010 01110",
    "!": "00100 00100 00100 00100 00100 00000 00100", "*": "00000 10101 01110 11111 01110 10101 00000",
    "&": "01100 10010 10100 01000 10101 10010 01101", "|": "00100 00100 00100 00100 00100 00100 00100",
    "\"": "01010 01010 00000 00000 00000 00000 00000", "~": "00000 00000 01000 10101 00010 00000 00000",
    "?": "01110 10001 00001 00010 00100 00000 00100", ";": "00000 01100 01100 00000 01100 00100 01000",
}
FONT = {c: [[int(b) for b in row] for row in g.split()] for c, g in _F.items()}


def text(canvas, W, H, x, y, s, idx, sc=2):
    for ch in s.upper():
        g = FONT.get(ch, FONT["?"])
        for gy in range(7):
            for gx in range(5):
                if g[gy][gx]:
                    for yy in range(sc):
                        for xx in range(sc):
                            px, py = x + gx * sc + xx, y + gy * sc + yy
                            if 0 <= px < W and 0 <= py < H:
                                canvas[py * W + px] = idx
        x += 6 * sc


def wrap(s, width_chars):
    lines, cur = [], ""
    for w in s.split():
        if cur and len(cur) + 1 + len(w) > width_chars:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    return lines + [cur] if cur else lines


# ---------------------------------------------------------------- GIF writer (LZW, stdlib)
def lzw_encode(indices, min_code=8):
    clear, end = 1 << min_code, (1 << min_code) + 1
    out, acc, nacc = bytearray(), 0, 0

    def emit(code, size):
        nonlocal acc, nacc
        acc |= code << nacc
        nacc += size
        while nacc >= 8:
            out.append(acc & 255)
            acc >>= 8
            nacc -= 8
    table, nxt, size = {}, end + 1, min_code + 1
    emit(clear, size)
    cur = None
    for b in indices:
        if cur is None:
            cur = b
            continue
        k2 = (cur, b)
        if k2 in table:
            cur = table[k2]
            continue
        emit(cur, size)
        if nxt < 4096:
            table[k2] = nxt
            if nxt == (1 << size) and size < 12:
                size += 1
            nxt += 1
        else:
            emit(clear, size)
            table, nxt, size = {}, end + 1, min_code + 1
        cur = b
    if cur is not None:
        emit(cur, size)
    emit(end, size)
    if nacc:
        out.append(acc & 255)
    return bytes(out)


def lzw_decode(data, min_code=8):
    """Inverse of lzw_encode (used by the test)."""
    clear, end = 1 << min_code, (1 << min_code) + 1
    acc = nacc = pos = 0
    size = min_code + 1
    table, out, prev = {}, bytearray(), None
    nxt = end + 1
    while True:
        while nacc < size and pos < len(data):
            acc |= data[pos] << nacc
            nacc += 8
            pos += 1
        if nacc < size:
            break
        code, acc, nacc = acc & ((1 << size) - 1), acc >> size, nacc - size
        if code == clear:
            table = {i: bytes([i]) for i in range(clear)}
            size, prev, nxt = min_code + 1, None, end + 1
            continue
        if code == end:
            break
        e = table[code] if code in table else prev + prev[:1]
        out += e
        if prev is not None and nxt < 4096:
            table[nxt] = prev + e[:1]
            nxt += 1
            if nxt == (1 << size) and size < 12:
                size += 1
        prev = e
    return bytes(out)


def _blocks(data):
    out = bytearray()
    for i in range(0, len(data), 255):
        c = data[i:i + 255]
        out.append(len(c))
        out += c
    return bytes(out) + b"\0"


def encode_gif(frames, W, H, pal, delays, comment=None):
    """frames: list of bytes (W*H indices); pal: 768 bytes. Frames after the first are cropped to the changed rows."""
    out = bytearray(b"GIF89a" + struct.pack("<HHBBB", W, H, 0xF7, 0, 0) + bytes(pal))
    out += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"
    if comment:                                     # comment extension (schematic marker)
        out += b"\x21\xFE" + _blocks(comment.encode("latin-1"))
    prev = None
    for f, d in zip(frames, delays):
        y0, y1 = 0, H
        if prev is not None:
            rows = [y for y in range(H) if f[y * W:(y + 1) * W] != prev[y * W:(y + 1) * W]]
            y0, y1 = (rows[0], rows[-1] + 1) if rows else (0, 1)
        out += b"\x21\xF9\x04\x04" + struct.pack("<HBB", d, 0, 0) + b"\0"
        out += b"\x2C" + struct.pack("<HHHHB", 0, y0, W, y1 - y0, 0)
        out += bytes([8]) + _blocks(lzw_encode(f[y0 * W:y1 * W]))
        prev = f
    return bytes(out) + b";"




def write_html(path, caps, W, H, title, help_html, marker=None):
    """Step-through page: caps = [{text, calc}], frame-NNN.png beside it. help_html: the <li> items of the box."""
    page = """<!doctype html><meta charset="utf-8"><title>@@TITLE@@</title>
<style>body{background:#111;color:#ddd;font:14px sans-serif;margin:0;padding:12px;text-align:center}
img{max-width:100%%;height:auto;image-rendering:pixelated;background:#000}button{font-size:16px;margin:4px;padding:4px 12px}
#cap{max-width:900px;margin:8px auto;min-height:2em;font-weight:bold}#s{width:60%%}
#calc{max-width:900px;margin:0 auto;text-align:left;font:13px/1.5 monospace;background:#1b1b22;padding:8px 14px;
border-radius:6px}#calc li{margin:2px 0}#help{max-width:900px;margin:8px auto;text-align:left;font-size:13px;color:#aaa}
#help summary{cursor:pointer;color:#ddd}</style>
<img id=f width=%d height=%d alt="frame"><div>
<button id=p>prev</button><button id=pl>play</button><button id=n>next</button>
<input id=s type=range min=0 value=0></div><div id=cap></div>
<div id=calc><b>Calculations for this step</b><ol id=cl></ol></div>
<details id=help><summary>How to read this</summary><ul>
@@HELP@@</ul></details>
<script>
var caps=%s,i=0,t=null,f=document.getElementById('f'),s=document.getElementById('s');
s.max=caps.length-1;
function show(k){i=Math.max(0,Math.min(caps.length-1,k));f.src='frame-'+('000'+i).slice(-3)+'.png';
s.value=i;document.getElementById('cap').textContent=(i+1)+'/'+caps.length+'  '+caps[i].text;
var cl=document.getElementById('cl');cl.innerHTML='';caps[i].calc.forEach(function(c){var li=document.createElement('li');
li.textContent=c;cl.appendChild(li);});}
function stop(){if(t){clearInterval(t);t=null;document.getElementById('pl').textContent='play';}}
document.getElementById('p').onclick=function(){stop();show(i-1)};
document.getElementById('n').onclick=function(){stop();show(i+1)};
document.getElementById('pl').onclick=function(){if(t){stop();return;}
 if(i>=caps.length-1)show(0);document.getElementById('pl').textContent='pause';
 t=setInterval(function(){if(i>=caps.length-1)stop();else show(i+1)},900)};
s.oninput=function(){stop();show(+s.value)};
document.onkeydown=function(e){if(e.key=='ArrowRight'){stop();show(i+1)}else if(e.key=='ArrowLeft'){stop();show(i-1)}
 else if(e.key==' '){e.preventDefault();document.getElementById('pl').click()}};
show(0);
</script>
""" % (W, H, json.dumps(caps))
    page = page.replace("@@TITLE@@", title).replace("@@HELP@@", help_html)
    if marker:                                      # schematic mode only
        # the export's check bars every <meta> element, so this page has none: it is pure ASCII (character references)
        page = page.replace('<meta charset="utf-8">', "", 1).replace(
            "<title>", '<!-- %s: schematic-only page, our own graphics -->\n<title>' % marker, 1)
        page = page.replace("f.src='frame-'+('000'+i).slice(-3)+'.png';",     # the check reads `src='...'` as a link
                            "f.setAttribute('src','frame-'+('000'+i).slice(-3)+'.png');")
        page = page.encode("ascii", "xmlcharrefreplace").decode("ascii")
    with open(path, "w") as fh:
        fh.write(page)


def safe_out(out):
    ws = os.path.realpath(os.path.join(HERE, "..", "workspace"))
    real = os.path.realpath(out)
    if real == ws or not real.startswith(ws + os.sep):
        raise SystemExit("refusing output dir %s: it must be under workspace/" % out)
    return real


# ---------------------------------------------------------------- schematic mode (ADR-0036)
# Our own fixed palette and marker. Nothing here comes from a game file. A schematic output is marked in every file
# it makes (PNG tEXt chunk, GIF comment, HTML comment, steps.json key) and listed with hashes in schematic.json.
MARKER_NAME = "schematic-only"
MARKER = "schematic-only/1"           # the byte string tools/export_check.py looks for in every file (own graphics, no game art)

SCHEM_UI = dict(                     # name -> RGB; the order is the palette order (index = position)
    bg=(16, 16, 22), panel=(30, 30, 40), txt=(225, 225, 225), dim=(130, 130, 145), acc=(240, 210, 80),
    good=(70, 200, 90), bad=(215, 70, 70), blue=(90, 140, 255), cur=(60, 60, 95), grey=(70, 70, 80),
    q_low=(150, 150, 150), q_normal=(235, 235, 235), q_superior=(200, 200, 200), q_magic=(110, 130, 255),
    q_set=(60, 220, 60), q_rare=(255, 240, 80), q_unique=(205, 160, 90), black=(0, 0, 0),
    qd_low=(48, 48, 52), qd_normal=(62, 62, 66), qd_superior=(56, 56, 60), qd_magic=(34, 40, 78),
    qd_set=(22, 66, 30), qd_rare=(74, 70, 22), qd_unique=(64, 50, 30),
    room=(60, 70, 110), roomdone=(78, 92, 140), edge=(150, 160, 220), door=(80, 220, 120), warp=(90, 230, 255))


def schem_palette():
    """-> (name -> palette index, 768 palette bytes) of SCHEM_UI."""
    idx = {k: i for i, k in enumerate(SCHEM_UI)}
    pal = bytearray()
    for rgb in SCHEM_UI.values():
        pal += bytes(rgb)
    return idx, bytes(pal) + bytes(768 - len(pal))


def write_steps_json(path, caps, schematic):
    """steps.json: the bare list in the full mode; in schematic mode an object that carries the marker key."""
    with open(path, "w") as fh:
        json.dump({"schematic_only": MARKER, "steps": caps} if schematic else caps, fh, indent=1)


def write_schematic_json(out, args, names):
    """schematic.json beside the files: the marker, the run's arguments (the data root and --out left out) and each
    file's name and sha256. No tool name: the file is published and ties nothing to the working repository. Schematic
    mode only; the full mode never writes it. A hex argument is written in decimal (the export's check, X1 and X3,
    fails a hex number of 6+ digits)."""
    args = [str(int(a, 16)) if a.lower().startswith("0x") else a for a in args]
    files = {}
    for n in sorted(names):
        with open(os.path.join(out, n), "rb") as fh:
            files[n] = hashlib.sha256(fh.read()).hexdigest()
    with open(os.path.join(out, "schematic.json"), "w") as fh:
        json.dump({"marker": MARKER, "args": list(args), "files": files}, fh, indent=1)
