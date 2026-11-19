"""Animate one quest word's bits as events arrive (docs/specs/quests/progression.md sections A, D and the word 1 and word 41
tables): the words of Akara's quest, the Den of Evil's reward, and of the Hell respec offer it carries, followed through a
save, a load, the reward talk, a save and a second load, one bit at a time. Schematic only (ADR-0036): boxes and text in our
own palette.

Usage:
  python3 -I tools/quest_anim.py <root> [--theme dark|light] [--out DIR] [--schematic]

<root> is accepted for the export builder and read for nothing: the model needs no table. --theme: dark or light palette
values. --schematic is accepted for the export builder and changes nothing. DIR defaults to workspace/render/anim/
quest-schematic/ and must stay under workspace/. Outputs: frame-NNN.png, quest.gif, index.html, steps.json, schematic.json.

Steps: the words in the save (word 1 holds only bit 1, the reward not yet taken; word 41 is empty); the load rule (A3); the
four writes the reward message makes (NPC 148, message 0x4C, with bit 1 of word 1 set), one per frame, in call order; the
ClearSteps that ends the message (A2, D7); Save and Exit (A4); the next load. The words and every write come from the
model of tools/quests.py: rec_load is the loader's rule, talk_writes the writes a message makes on the record before it
(from the talk-step table and the second-word table), rec_apply the record functions' bit operations. The start (word 1 =
0x0002, word 41 = 0) is the spec's worked example. Not shown: the first join's switch-off of the quest and the game record's
bit (the game record is a separate record), the player's stat 5 point the reward adds, the other 40 words. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import quests  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 372
CW = 46                          # a bit cell's width
BX = 124                         # the first bit cell's x (bit 15)
NPC, MSG = 148, 0x4C
START = {1: 0x0002, 41: 0x0000}  # the saved words (the spec's worked example 3)
BIT_NAMES = (("B0", "DONE"), ("B1", "REWARD PENDING"), ("B2-11", "LOG STEPS"), ("B12", "SEEN"), ("B13", "DONE IN GAME"),
             ("B14", "FAILED IN GAME"), ("B15", "PENDING SAVED"))
HELP = """<li>Each row is one quest word, 16 bits, bit 15 at the left and bit 0 at the right. A lit cell is a set bit.</li>
<li>The cell outlined in yellow is the bit the step just wrote or the loader just changed.</li>
<li>Word 1 is the Den of Evil's quest. Word 41 is the second word of the same quest object: the offer of a free skill reset in Hell.</li>
<li>Every value is computed by our model from the spec's rules, not observed in the game.</li>"""


def hx(w):
    return "0x%04X" % w


def bits_on(w):
    return [b for b in range(16) if w >> b & 1]


def model():
    """The steps of the walk: [(title, kind, words after, changed {(word, bit)}, where, text, calc)]. All values come from
    the model's functions; the record is one list of the 48 words with only words 1 and 41 non-zero."""
    rec = [0] * 48
    for q, v in START.items():
        rec[q] = v
    out = []

    def diff(a, b):
        return {(q, bt) for q in (1, 41) for bt in range(16) if (a[q] ^ b[q]) >> bt & 1}

    out.append(dict(title="THE SAVE FILE", where="IN THE SAVE FILE", words=dict(START), ch=set(),
                    text="The save holds word 1 with only bit 1 set, the reward not yet taken, and word 41 empty.",
                    calc=["progression A4: each word is written as it stands at Save and Exit; the file holds word 1 = %s and "
                          "word 41 = %s." % (hx(rec[1]), hx(rec[41])),
                          "progression A: bit 1 = done in a game, reward not yet taken."]))
    prev = list(rec)
    for q in range(42):                                  # A3 over the quests 0 to 41
        rec[q] = quests.rec_load(rec[q])
    out.append(dict(title="THE LOAD", where="IN THE PLAYER'S RECORD", words={1: rec[1], 41: rec[41]}, ch=diff(prev, rec),
                    text="Loading clears bits 13 and 14 of each word of quests 0 to 41 and sets bit 15 when bit 1 is set, so "
                         "word 1 gains bit 15.",
                    calc=["progression A3: w = saved word; clear bits 13 and 14; if bit 1 of w: set bit 15 of w.",
                          "word 1: %s -> %s; word 41: %s -> %s." % (hx(prev[1]), hx(rec[1]), hx(prev[41]), hx(rec[41]))]))
    writes = quests.talk_writes(rec, NPC, MSG)
    assert [(w, t, b) for w, t, b, _ in writes] == [(1, "QS", 0), (1, "QC", 1), (41, "QS", 13), (41, "QS", 1), (1, "QK", None)], writes
    names = {("QS", 0): "sets bit 0 of word 1, done",
             ("QC", 1): "clears bit 1 of word 1, the reward pending",
             ("QS", 13): "sets bit 13 of word 41, with bit 1 the offer of a free skill reset in Hell",
             ("QS", 1): "sets bit 1 of word 41, with bit 13 the offer of a free skill reset in Hell",
             ("QK", None): "ends with ClearSteps on word 1, which clears its bits 2 to 11, the log steps"}
    for k, (q, t, b, _site) in enumerate(writes):
        prev = list(rec)
        rec[q] = quests.rec_apply(rec[q], t, b)
        key = (t, b if t != "QK" else None)
        what = {"QS": "SET", "QC": "CLEAR", "QK": "CLEARSTEPS"}[t]
        title = "AKARA'S REWARD TALK: %s" % (("%s BIT %d OF WORD %d" % (what, b, q)) if t != "QK" else "CLEARSTEPS ON WORD 1")
        last = t == "QK"
        txt = ("Akara's reward message, with bit 1 of word 1 set, %s." % names[key]) if k == 0 else (
            "The same message %s%s." % (names[key], "; no step bit was set here, so the word does not change" if last and rec[q] == prev[q] else ""))
        call = ("progression D7: the reward message with bit 1 set sets bit 0 and clears bit 1; word 1's reward also "
                "clears the log steps." if k < 2 else
                "progression word 41: the same message sets bits 13 and 1 of word 41." if q == 41 else
                "progression A2: ClearSteps clears bits 2 to 11 of the word.")
        out.append(dict(title=title, where="IN THE PLAYER'S RECORD", words={1: rec[1], 41: rec[41]}, ch=diff(prev, rec),
                        text=txt, calc=[call, "word %d: %s -> %s." % (q, hx(prev[q]), hx(rec[q]))]))
    saved = {1: rec[1], 41: rec[41]}
    out.append(dict(title="SAVE AND EXIT", where="IN THE SAVE FILE", words=dict(saved), ch=set(),
                    text="Save and Exit writes each word as it stands: word 1 = %s and word 41 = %s." % (hx(rec[1]), hx(rec[41])),
                    calc=["progression A4: the written record is the loaded record after every server write, in order.",
                          "word 1 = %s, word 41 = %s." % (hx(rec[1]), hx(rec[41]))]))
    prev = list(rec)
    for q in range(42):
        rec[q] = quests.rec_load(rec[q])
    out.append(dict(title="THE NEXT LOAD", where="IN THE PLAYER'S RECORD", words={1: rec[1], 41: rec[41]}, ch=diff(prev, rec),
                    text="Loading again turns word 41's bit 13 off and sets its bit 15 from its bit 1, so the offer is pending "
                         "from an earlier game; word 1 stays done.",
                    calc=["progression A3: clear bits 13 and 14; if bit 1: set bit 15.",
                          "word 1: %s -> %s; word 41: %s -> %s." % (hx(prev[1]), hx(rec[1]), hx(prev[41]), hx(rec[41]))]))
    return out


def build(theme):
    steps = model()
    n = len(steps)
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    for i, st in enumerate(steps):
        k.text(20, 12, st["title"], "acc", 2, True)
        k.text(20, 36, st["where"], "dim", 2)
        k.tape(20, 64, [str(j + 1) for j in range(n)], 30, 26, cur=i, sc=1)
        for j in range(16):                                   # the bit numbers, 15 at the left
            b = 15 - j
            k.text_c(BX + j * CW + CW // 2, 108, str(b), "dim", 2)
        for r, q in enumerate((1, 41)):
            y = 134 + r * 90
            w = st["words"][q]
            k.text(20, y + 8, "WORD %d" % q, "txt", 2, True)
            k.text(20, y + 34, hx(w), "acc", 2)
            for j in range(16):
                b = 15 - j
                on = w >> b & 1
                chg = (q, b) in st["ch"]
                k.box(BX + j * CW, y, CW + 1, 56, ["1" if on else "0"], "qd_set" if on else "panel", "acc" if chg else "grey",
                      "good" if on else "dim", 3, 3 if chg else 1, bold=bool(on))
        k.legend(20, 318, [("qd_set", "SET"), ("panel", "CLEAR"), ("acc", "JUST CHANGED")], sc=1)
        k.text(20, 340, "B0 DONE  B1 REWARD PENDING  B2-11 LOG STEPS  B12 SEEN  B13 DONE IN GAME  B14 FAILED IN GAME  "
                        "B15 PENDING SAVED", "dim", 1)
        k.caption(st["text"], CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text=st["text"], calc=st["calc"]))
    return frames, caps, k.pal


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "quest-schematic")
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal = build(opts["--theme"])
    K.write_illustration(out, "quest", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "quest word animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
