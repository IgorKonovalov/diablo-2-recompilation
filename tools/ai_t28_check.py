#!/usr/bin/env python3
"""Row 28 `Vampire`: the block of docs/specs/monsters/ai/machinery.md T28 against the kept logs (`lane/s52a` review).

The block was written from the instructions 0x005F4A70..0x005F4FCC at the review. This runs it as written, as a second
reading: for each logged decision of row 28, from the AID line's inputs and the logged results of the boundary calls, it
checks every boundary call (function and return address), the unit seed at each call and after the last draw, and
AiCtl +0x14, +0x18, +0x1C at each call. Logged paths only: PATH lines say which arms the logs reach. It tests the block's
draw order on those paths; it runs no game code, and an arm no log reaches is checked by nothing here.

Controls: --control NAME changes one rule of the block and must fail decisions.
  always-y    the draw of "bit 0, a hostile and a draw <= 30" made before the two tests
  b0-first    the draw of "a draw above 30 or bit 0 clear" made only with bit 0 set (an arm no kept log reaches: it passes,
              and that is what it says)
  no-second   the second draw inside 9 dropped
  byte3       T56's byte read as 3 (the walk's arguments)

    python3 -I tools/ai_t28_check.py [--control NAME] LOG...
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_resume  # noqa: E402

FIND, S319, LIFE = 0x005DDC30, 0x005DD2B0, 0x00621F20
OVR, AWAY, T56, WALK, MODE, SKILL, IDLE = 0x005DE190, 0x005DEFE0, 0x005DF7D0, 0x005DEC80, 0x005DDF90, 0x005DEAD0, 0x005DE080


class Mis(Exception):
    pass


class Stop(Exception):
    pass


def s32(v):
    return v - (1 << 32) if v >= (1 << 31) else v


def s16(v):
    return v - (1 << 16) if v >= (1 << 15) else v


class Run:
    def __init__(self, dec, bnd, control):
        self.dec, self.bnd, self.control = dec, bnd, control
        a = dec["aid"]
        self.calls = ai_resume.top_level(dec)
        self.i = 0
        self.seed = ai.seedval(a["s"])
        ctl = bytes.fromhex(a["ctl"])
        self.v14 = s32(int.from_bytes(ctl[0x14:0x18], "little"))
        self.v18 = s32(int.from_bytes(ctl[0x18:0x1C], "little"))
        self.v1c = s32(int.from_bytes(ctl[0x1C:0x20], "little"))
        raw = bytes.fromhex(a["aip"])
        self.aips = [s16(int.from_bytes(raw[i:i + 2], "little")) for i in range(0, len(raw), 2)]
        self.d = a["diff"]
        self.t = a["ctx"][2]
        self.dist = s32(a["ctx"][5])
        self.melee = a["ctx"][6]
        self.path = []

    def aip(self, k):
        return self.aips[3 * (k - 1) + self.d]

    def step(self):
        self.seed = ai.step(self.seed)
        return self.seed[0] % 100

    def call(self, fn, ra, args=None):
        if fn not in self.bnd:
            raise Stop("not a boundary: %x" % fn)
        if self.i >= len(self.calls):
            raise Stop("log ends")
        b = self.calls[self.i]
        self.i += 1
        if b["fn"] != fn or b["ra"] != ra:
            raise Mis("call %d: block %x@%x, log %x@%x" % (self.i, fn, ra, b["fn"], b["ra"]))
        if ai.seedval(b["s"]) != self.seed:
            raise Mis("call %d %x@%x: seed %s, log %s" % (self.i, fn, ra, self.seed, b["s"]))
        if list(b["c"]) != [self.v14, self.v18, self.v1c]:
            raise Mis("call %d %x@%x: ctl %s, log %s" % (self.i, fn, ra, [self.v14, self.v18, self.v1c], b["c"]))
        if args is not None and list(b["a"][:len(args)]) != list(args):
            raise Mis("call %d %x@%x: args %s, log %s" % (self.i, fn, ra, args, b["a"][:len(args)]))
        air = self.dec["air"].get(b["n"])
        if air is None:
            raise Stop("no return logged")
        self.seed = ai.seedval(air["s"])
        return air

    def pair(self, x):
        if self.step() < 50:
            self.path.append("pair-skill1")
            self.call(SKILL, 0x005F4D47)
        else:
            self.path.append("pair-skill4")
            self.call(SKILL, 0x005F4D69)

    def skills(self, x):
        """Returns True when a skill was used. The cooldown is written after the call."""
        if self.b1 and self.v1c <= 0 and self.step() < self.aip(4):
            self.path.append("skill2")
            self.call(SKILL, 0x005F4C92)
            self.v1c = 11
            return True
        if self.b2 and self.v1c <= 0 and self.step() < self.aip(4):
            self.path.append("skill3")
            self.call(SKILL, 0x005F4CEF)
            self.v1c = 11
            return True
        return False

    def t56(self, ra):
        self.path.append("t56@%x" % ra)
        byte = 3 if self.control == "byte3" else 4
        self.call(T56, ra, args=[self.t, byte, 0])

    def think(self):
        bits = self.aip(5)
        self.b0, self.b1, self.b2 = bits & 1, bits & 2, bits & 4
        if self.v1c > 0:
            self.v1c -= 1
        air = self.call(FIND, 0x005F4AD5)
        h = air["eax"]
        hd = s32(air["bl"]["0"][0]) if h and air.get("bl", {}).get("0") else 0x7FFFFFFF
        s = self.call(S319, 0x005F4ADF)["eax"]
        if s:
            if self.v14 == 0:
                self.v14 = 1
            if self.dist < 30 and self.dist > self.v18:
                self.v18 = self.dist
            if self.melee:
                if self.control == "b0-first":
                    do = self.b0 and self.step() <= 30
                else:
                    do = self.step() <= 30 and self.b0
                if do:
                    self.path.append("s-melee-pair")
                    self.pair(self.t)
                else:
                    self.path.append("s-melee-a1")
                    self.call(MODE, 0x005F4B6F)
                return
        life = self.call(LIFE, 0x005F4B7E)["eax"]
        if self.v14 == 2:
            if life >= 75:
                self.v14 = 1
                self.path.append("flee-back")
                self.call(WALK, 0x005F4BAA)
                return
            if self.dist < 14 or self.dist <= self.v18:
                self.path.append("flee-step")
                self.call(OVR, 0x005F4BFD) if OVR in self.bnd else None
                if self.call(AWAY, 0x005F4C0E)["eax"]:
                    return
            if self.dist >= self.aip(3) or self.step() >= self.aip(2):
                self.path.append("flee-wait")
                self.call(IDLE, 0x005F4FC6)
                return
            if self.skills(self.t):
                return
            if self.b0 and h and hd <= 20:
                self.path.append("flee-pair")
                self.pair(h)
                return
            self.t56(0x005F4D83)
            return
        if life < 33:
            self.v14 = 2
            self.path.append("engaged-flee")
            if self.call(AWAY, 0x005F4DA5)["eax"]:
                return
        if self.melee:
            self.v14 = 1
            x = self.step()
            if self.control == "always-y":
                y = self.step()
            if x < self.aip(1):
                if self.b0 and h:
                    if self.control != "always-y":
                        y = self.step()
                    if y > 30:
                        self.path.append("melee-a1")
                        self.call(MODE, 0x005F4B6F)
                        return
                    if hd <= 20:
                        self.path.append("melee-pair")
                        self.pair(h)
                        return
                else:
                    self.path.append("melee-a1")
                    self.call(MODE, 0x005F4B6F)
                    return
            if self.step() < 33:
                self.t56(0x005F4E55)
            else:
                self.path.append("melee-idle")
                self.call(IDLE, 0x005F4E67)
            return
        if self.dist >= self.aip(3):
            if self.v14 == 1:
                self.path.append("far-walk")
                self.call(WALK, 0x005F4F66)
            else:
                self.path.append("far-wait")
                self.call(IDLE, 0x005F4FC6)
            return
        self.v14 = 1
        if self.step() >= self.aip(2):
            if self.dist > 20:
                self.path.append("keep-walk")
                self.call(WALK, 0x005F4F66)
                return
            z = None
            if self.dist < 9:
                z = self.step()
                if z < 50:
                    self.path.append("keep-step")
                    self.call(AWAY, 0x005F4F97)
                    return
            if self.control == "no-second" and z is not None:
                pass
            else:
                z = self.step()
            if z < 50:
                self.t56(0x005F4E55)
            else:
                self.path.append("keep-idle")
                self.call(IDLE, 0x005F4E67)
            return
        if self.skills(self.t):
            return
        if not (self.b0 and h and hd <= 20):
            self.path.append("in-walk")
            self.call(WALK, 0x005F4BAA)
            return
        if self.step() < 75:
            self.path.append("in-pair")
            self.pair(h)
        else:
            self.t56(0x005F4F46)


def main(argv):
    control = None
    if argv and argv[0] == "--control":
        control = argv[1]
        argv = argv[2:]
    bnd = ai_resume.bnd_set()
    n = ok = mis = stop = 0
    paths, msgs = {}, []
    for p in argv:
        for dec in ai.parse(p)["dec"]:
            a = dec["aid"]
            if a["ai"] != 28 or a["st"] != 0:
                continue
            n += 1
            r = Run(dec, bnd, control)
            try:
                r.think()
                if r.i != len(r.calls):
                    raise Mis("%d logged calls left" % (len(r.calls) - r.i))
                x = dec.get("aix") or {}
                if x.get("s") and ai.seedval(x["s"]) != r.seed:
                    raise Mis("exit seed %s, log %s" % (r.seed, x["s"]))
                ok += 1
                for q in r.path:
                    paths[q] = paths.get(q, 0) + 1
            except Mis as e:
                mis += 1
                if len(msgs) < 6:
                    msgs.append("MIS %s k=%s %s" % (os.path.basename(p), a.get("n"), e))
            except Stop as e:
                stop += 1
                if len(msgs) < 6:
                    msgs.append("STOP %s k=%s %s" % (os.path.basename(p), a.get("n"), e))
    print("\n".join(msgs))
    for q in sorted(paths):
        print("PATH %s %d" % (q, paths[q]))
    print("SURVEY ai_t28_check control=%s decisions=%d ok=%d mismatches=%d stopped=%d" % (control, n, ok, mis, stop))


if __name__ == "__main__":
    main(sys.argv[1:])
