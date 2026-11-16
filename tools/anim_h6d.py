"""Plan 0066 Phase 2 batch H6d: checks over the logger rev 7 lines of tools/gdb/anim.py (SR "x" "b" "l" "a44" "rp",
MSW, ALF, HAF) for the rows whose emulation route crosses COMPOSIT_BuildCofName's wsprintfA import (anim/timing 9, 11,
44, 80-84, 87, 88, 90, 91, 128, 129, 23, 29; anim/movement 4-6, 8, 13-15).

Usage:  python3 -I tools/anim_h6d.py check LOG [LOG ...]      # the families below, one `H6D ...` line each
        python3 -I tools/anim_h6d.py manifest DIR             # sha256 of every file under DIR (kept logs)
The existing checker (tools/anim.py check) is the control: the same rate model must hold on the same lines.

Families (every control must separate: `controls` names a variant of the model that has to disagree on the data):
  msw     every MonStats row's +0x36/+0x38 words read at the game start equal tools/anim.py Data.speeds(i) (anim/0002 §
          3.5); controls: the unscaled word of a later base class (row 14's order), the absent record taken as 0
  alf     every ANIMDATA_Lookup / name look-up that returned the fallback record: frames 2048, speed 256, name and 144
          event bytes zero; its name is absent from animdata.d2 (the model's table); the caller addresses
  rate    each SR line: the model's branch and result (anim.py's rate_model), the exit address per branch, the floors
          (moving x < 25, attack x < 15, block q < 1, q above 0x7FFF) counted with the least x met, the no-path moving
          calls (+0x4C kept, no path speed), the record pointer changed or not across the call, +0x48 and +0x44
          unchanged across the call, each by caller address
  haf     HumanAttackFrames returns: the absent-record return (45) and the result
"""
import collections
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import anim as AN  # noqa: E402

ROOT = os.path.dirname(HERE)
INIT_RA = (0x00624390, 0x00624500)        # UNIT_AnimInit's own rate calls (before it writes +0x48)


def parse(path):
    out = []
    with open(path, errors="replace") as f:
        for raw in f:
            tag, _, rest = raw.partition(" ")
            if rest.startswith("{"):
                try:
                    out.append((tag, json.loads(rest)))
                except ValueError:
                    pass
    return out


class H:
    def __init__(self, d):
        self.d = d
        self.t = collections.Counter()
        self.bad = collections.Counter()
        self.ex = collections.defaultdict(collections.Counter)    # branch -> exit address -> count
        self.msg = []
        self.minx = {}
        self.ra = collections.defaultdict(collections.Counter)

    def ok(self, k, cond, msg=None):
        self.t["ok-" + k] += 1
        if not cond:
            self.bad[k] += 1
            if len(self.msg) < 40:
                self.msg.append((k, msg))

    # --- msw ---------------------------------------------------------------------------------------------------
    def msw(self, lines):
        d = self.d
        for tag, x in lines:
            if tag != "MSW":
                continue
            self.t["msw-lines"] += 1
            self.ok("msw-n", len(x["w"]) == len(d.mon), (len(x["w"]), len(d.mon)))
            for i, (w36, w38) in enumerate(x["w"][:len(d.mon)]):
                m36, m38 = d.speeds(i)
                self.ok("msw-word", (w36 & 0xFFFF, w38 & 0xFFFF) == (m36, m38), (i, w36, w38, m36, m38))
                self.t["msw-rows"] += 1
                # controls: the walk record absent (the fallback's 256 reaches the word), a later base class
                b = d.mon[i]["BaseId"]
                nm, _, _, _, found = d.record(d.mon_name(b if b is not None and 0 <= b < len(d.mon) else i, 2))
                if not found:
                    self.t["msw-walk-absent"] += 1
                    if (w36, w38) != (0, 0):
                        self.t["msw-walk-absent-nonzero"] += 1
                    if b is None or b == i:
                        self.t["msw-absent-own"] += 1
                        self.t["msw-absent-own-w36-256"] += int(w36 == 256)
                    if w36 == 256 or b is not None and b != i:
                        self.t["msw-walk-absent-256-or-scaled"] += 1
                    self.t["ctl-absent-as-zero-differs"] += int(w36 != 0)
                if b is not None and b > i:
                    self.t["msw-base-later"] += 1
                    self.t["ctl-unscaled-differs"] += int(w36 != d.record(d.mon_name(b, 2))[2])
                if w36 == 256:
                    self.t["msw-w36-256"] += 1

    # --- alf ---------------------------------------------------------------------------------------------------
    def alf(self, lines):
        d = self.d
        for tag, x in lines:
            if tag != "ALF":
                continue
            self.t["alf-" + x["k"]] += 1
            self.ra[x["k"]]["0x%08X" % x["ra"]] += 1
            if x["k"] == "lookup":
                self.ok("alf-rec", x["rec"] == [2048, 256], x)
                self.ok("alf-zero", x.get("fb0") == 0, x)
                self.ok("alf-absent", x["name"].upper() not in d.anim, x)
            else:
                self.ok("alf-find-rec", x["out"] == [2048, 256], x)
                self.ok("alf-find-absent", (x["name"] or "").upper() not in d.anim, x)
            self.t["alf-name-%s" % x["name"]] += 1

    def sch(self, lines):
        for tag, x in lines:
            if tag == "SCH" and "a44" in x:
                self.t["sch-lines"] += 1
                self.t["sch-a44-zero"] += int(x["a44"] == 0)

    # --- haf ---------------------------------------------------------------------------------------------------
    def haf(self, lines):
        for tag, x in lines:
            if tag != "HAF":
                continue
            self.t["haf-" + x["k"]] += 1
            if x["k"] == "abs":
                self.ok("haf-abs-45", x["res"] == 45, x)
            else:
                self.ok("haf-spd", x["spd"] > 0, x)

    # --- rate --------------------------------------------------------------------------------------------------
    def rate(self, lines):
        d = self.d
        last48 = {}
        for tag, x in lines:
            if tag != "SR":
                continue
            u = x["u"]
            if "x" not in x:
                continue
            last_prev = last48.get(u["u"])
            res = AN.rate_model(d, x, last48.get(u["u"]))
            if x["rec"]:
                last48[u["u"]] = x["rec"][1] << 8
            br = res[4]
            kt = "p" if u["t"] == 0 else "m"
            self.ex[br][x["x"]] += 1
            ra = x["ra"]
            ini = INIT_RA[0] <= ra < INIT_RA[1]
            self.ra[br]["0x%08X" % ra] += 1
            # the call leaves +0x48 and +0x44 as they were; the record pointer changes when the name changes
            self.ok("l48-kept", x["b"][1] == x["l"], ("l48", x["n"], x["b"], x["l"]))
            self.ok("a44-kept", x["b"][0] == x["a44"], ("a44", x["n"], x["b"], x["a44"]))
            self.t["sr-%s-%s" % (kt, br)] += 1
            if x["rp"] != x["b"][3]:
                self.t["rp-changed"] += 1
                self.t["rp-changed-%s" % ("init" if ini else "mid")] += 1
                if x["b"][1] != 0 or x["l"] != 0:
                    self.t["rp-changed-l48-nonzero"] += 1
                    self.t["rp-changed-l48-kept"] += int(x["b"][1] == x["l"])
            else:
                self.t["rp-same"] += 1
            if ini and br == "attack" and last_prev is not None:
                self.t["prev48-init-attack"] += 1
                self.t["prev48-eq-last-record" if last_prev == x["b"][1] else "prev48-ne-last-record"] += 1
                # the model fed the live entry +0x48 (the strict form of the first-call claim)
                self.ok("rate-live-l48", AN.rate_model(d, x, x["b"][1])[1] == x["r"], ("l48", x["n"], x["b"], x["r"]))
                if x["c8"] & 8 and u["t"] == 0:
                    self.t["prev48-form-attack"] += 1
            if u["t"] == 1 and 8 <= u["m"] <= 11 and u["c"] < 410 and not (d.mon[u["c"]]["Velocity"] or 0):
                self.t["v0-s1-calls"] += 1
                self.ok("v0-s1-rate", res[1] == x["r"], x)
            if x["ra"] == 0x00553460:
                self.t["sunit-init-rate-calls"] += 1
                self.t["sunit-init-a44-zero"] += int(x["b"][0] == 0 and x["a44"] == 0)
            if x["c8"] & 8 and u["t"] == 0:
                self.t["form-br-%s" % br] += 1
            if not ini:
                self.t["mid-calls"] += 1
                self.t["mid-calls-l48-kept"] += int(x["b"][1] == x["l"])
                self.t["mid-calls-%s-%s" % (kt, "rp-changed" if x["rp"] != x["b"][3] else "rp-same")] += 1
            if u["c"] and x["c8"] & 8 and u["t"] == 0:
                self.t["form-calls"] += 1
                self.t["form-calls-%s" % ("init" if ini else "mid")] += 1
                self.t["form-calls-l48-kept"] += int(x["b"][1] == x["l"])
            if br == "move-nopath":
                self.t["nopath"] += 1
                self.ok("nopath-r-kept", x["b"][2] == x["r"], ("nopath", x["n"], x["b"], x["r"]))
                self.ok("nopath-pv-none", x["pv"] is None, x)
                self.t["nopath-%s" % kt] += 1
                self.t["nopath-r-differs-from-model-move"] += 1
                continue
            self.ok("rate", res[1] == x["r"], ("r", x["n"], br, res[1], x["r"], x["st"]))
            xx = x.get("_x")
            fc = AN.AR.floor0_cap
            if res[3] is not None and x.get("pv") is not None:
                self.ok("pathspeed", res[3] == x["pv"], ("pv", x["n"], br, res[3], x["pv"]))
                if br == "move" and xx is not None and xx < 25:
                    self.t["floor25-pathspeed-%s" % kt] += 1
                    c = dict(x)
                    c["st"] = dict(x["st"])
                    c["st"]["67"] = 100 - AN.bonus(4, int(x["st"].get("96", 0)))
                    pb = AN.rate_model(d, c)[3]
                    self.t["ctl-floor25-pathspeed-none-differs-%s" % kt] += int(AN.cdiv(AN.s32(pb * xx), 100) != x["pv"])
            if br == "move" and xx is not None:
                self.minx.setdefault("move-" + kt, xx)
                self.minx["move-" + kt] = min(self.minx["move-" + kt], xx)
                if xx < 25:
                    self.t["floor25-%s" % kt] += 1
                    self.ok("floor25", res[1] == x["r"], x)
                    # the controls: the moving factor floored at 24, at 26 and not floored (the base word from x = 100)
                    c = dict(x)
                    c["st"] = dict(x["st"])
                    c["st"]["67"] = 100 - AN.bonus(4, int(x["st"].get("96", 0)))
                    vb = AN.rate_model(d, c)[1]
                    for nm, f in (("24", 24), ("26", 26), ("none", xx)):
                        alt = fc(AN.cdiv(AN.s32(vb * f), 100))
                        self.t["ctl-floor25-%s-differs-%s" % (nm, kt)] += int(alt != x["r"])
                    if kt == "m":
                        self.t["floor25-m-x-lt0"] += int(xx < 0)
                    if x.get("pv") is not None:
                        self.t["floor25-with-pathspeed-%s" % kt] += 1
            if br == "attack" and xx is not None:
                self.minx.setdefault("attack-" + kt, xx)
                self.minx["attack-" + kt] = min(self.minx["attack-" + kt], xx)
                if xx < 15:
                    self.t["floor15-%s" % kt] += 1
                    self.ok("floor15", res[1] == x["r"], x)
                    for nm, f in (("14", 14), ("16", 16), ("none", xx)):
                        alt = fc(AN.AR.rate_u(res[7], f))
                        self.t["ctl-floor15-%s-differs-%s" % (nm, kt)] += int(alt != x["r"])
                if xx > 175:
                    self.t["cap175-%s" % kt] += 1
                    self.ok("cap175", res[1] == x["r"], x)
                    for nm, f in (("174", 174), ("176", 176), ("none", xx)):
                        alt = fc(AN.AR.rate_u(res[7], f))
                        self.t["ctl-cap175-%s-differs-%s" % (nm, kt)] += int(alt != x["r"])
            if br == "default":
                g69 = int(x["st"].get("69", 0))
                self.minx.setdefault("default-s69-" + kt, g69)
                self.minx["default-s69-" + kt] = min(self.minx["default-s69-" + kt], g69)
                if g69 < 15 or g69 > 175:
                    self.t["default-%s-%s" % ("lt15" if g69 < 15 else "gt175", kt)] += 1
                    self.ok("default-clamp", res[1] == x["r"], x)
                    for nm, f in (("lo14", 14), ("lo16", 16), ("hi174", 174), ("hi176", 176), ("none", g69)):
                        if (g69 < 15) != nm.startswith("lo") and nm != "none":
                            continue
                        alt = fc(AN.AR.rate_u(res[7], f))
                        self.t["ctl-default-%s-differs-%s" % (nm, kt)] += int(alt != x["r"])
            if br == "block":
                self.t["block-%s" % kt] += 1
                self.minx.setdefault("block-r", x["r"])
                self.minx["block-r"] = min(self.minx["block-r"], x["r"])
                if res[1] is not None and res[1] <= 0:
                    self.t["block-q-le0"] += 1
            if res[1] is not None and res[1] >= 0x7FFF:
                self.t["q-cap-0x7FFF"] += 1
            sk = x.get("eq") if u["t"] == 0 else None
            if sk and u["c"] in (4, 6) and d.dual(sk):
                self.t["dual-%s" % br] += 1
                self.t["dual-ok-%s" % br] += int(res[1] == x["r"])
                if br == "attack":
                    dw = d.dual(sk)
                    a, b = dw[0][0][3], dw[1][0][3]
                    g68 = int(x["st"].get("68", 0))
                    term = int((a + b) / 2) - a
                    self.t["dual-attack-hands-differ"] += int(a != b)
                    if a != b:
                        # stat 68 holds a base 100 and the linked weapon's 68 (+7 in some sessions: other items): the
                        # hand is inferred from g68 - 100 - 68(hand) in {0, 7}; an inference, not a logged fact
                        side = "left" if (g68 - 100 - b) in (0, 7) else ("right" if (g68 - 100 - a) in (0, 7) else "other")
                        self.t["dual-attack-linked-%s" % side] += 1
                        self.t["dual-attack-linked-%s-ok" % side] += int(res[1] == x["r"])
                        c = dict(x)
                        c["st"] = dict(x["st"])
                        c["st"]["68"] = g68 - term
                        alt = AN.rate_model(d, c)[1]
                        self.t["ctl-dual-noterm-differs-%s" % side] += int(alt != x["r"])

    def report(self):
        for k in sorted(self.t):
            if self.t[k]:
                print("H6D T %s %d" % (k, self.t[k]))
        for br in sorted(self.ex):
            print("H6D EXIT %s %s" % (br, " ".join("0x%08X:%d" % (a, n) for a, n in sorted(self.ex[br].items()))))
        for k in sorted(self.ra):
            print("H6D RA %s %s" % (k, " ".join("%s:%d" % (a, n) for a, n in sorted(self.ra[k].items()))))
        for k, v in sorted(self.minx.items()):
            print("H6D MINX %s %d" % (k, v))
        for k, m in self.msg[:20]:
            print("H6D MISMATCH %s %r" % (k, m))
        nbad = sum(self.bad.values())
        print("H6D total checks=%d bad=%d %s" % (sum(v for k, v in self.t.items() if k.startswith("ok-")), nbad,
                                                 " ".join("%s=%d" % kv for kv in sorted(self.bad.items()))))
        return 1 if nbad else 0


def manifest(dirp):
    rows = []
    for dp, _, fs in os.walk(dirp):
        for f in sorted(fs):
            p = os.path.join(dp, f)
            if f.startswith("manifest") or f.endswith(".out"):
                continue
            rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.relpath(p, dirp)))
    print("\n".join(sorted(rows, key=lambda r: r.split("  ", 1)[1])))
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "manifest":
        return manifest(argv[1])
    if argv[0] != "check":
        print(__doc__)
        return 2
    d = AN.Data(os.path.join(ROOT, "workspace", "merged"), os.path.join(ROOT, "workspace", "install", "app", "game.exe"))
    h = H(d)
    for p in argv[1:]:
        lines = parse(p)
        print("H6D FILE %s lines=%d" % (os.path.basename(p), len(lines)))
        h.msw(lines)
        h.alf(lines)
        h.haf(lines)
        h.sch(lines)
        h.rate(lines)
    return h.report()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
