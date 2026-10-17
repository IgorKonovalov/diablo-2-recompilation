#!/usr/bin/env python3
"""Plan 0043 Phase 2 session driver: hover sweeps and clicks in an open trade or gamble window.

Usage:
  python3 -I tools/economy_sessions.py --slot N act TOKEN...

Run it after `tools/d2pilot.py npc <log> <name> trade|gamble --stay` has opened the window. Each hover leaves the
pointer on a cell for --dwell seconds, during which the client prices the item under it every frame
(ITEMS_TradePriceCore, logged by tools/gdb/economy.py). Tokens:

  store[:T]      hover the 10 x 10 store grid of tab T (1..4; no T: every tab, clicking each tab first)
  grid           hover the 10 x 10 grid as it is (the gamble window has no tabs)
  inv            hover the 10 x 4 inventory grid
  equip          hover the ten paper-doll slots
  repair         click the repair button (single item), hover the inventory and paper doll, click it again
  repairall      hover the repair-all button, then click it (NpcRepair, packet bit 31)
  hoverall       hover the repair-all button only
  sell:c,r       pick up the inventory item at cell (c, r) and click it onto the store grid (a sale)
  buy:T:c,r      right-click the store cell (c, r) of tab T (a purchase)
  click:x,y      left click (window-relative);  rclick:x,y right click;  key:NAME;  sleep:S;  shot:PATH

Window-relative coordinates on the 800 x 600 frame, measured from screenshots (run:2026-10-17-economy): store cell
(c, r) at (110 + 29c, 138 + 29r), tabs at x 122, 200, 281, 361 and y 74; inventory cell (c, r) at
(432 + 29c, 330 + 29r); buttons at y 461: buy 213, sell 264, repair 315, repair all 366. The paper doll as
tools/d2pilot.py insert's `eq:` cells. Nothing here feeds a model.
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import slots  # noqa: E402
import xdrive  # noqa: E402

TABS = [(122, 74), (200, 74), (281, 74), (361, 74)]
EQUIP = {"head": (562, 92), "tors": (562, 177), "rarm": (447, 163), "larm": (678, 163), "neck": (620, 104),
         "glov": (447, 266), "belt": (562, 252), "feet": (678, 266), "rrin": (505, 252), "lrin": (620, 252)}
B_REPAIR, B_REPAIRALL = (315, 461), (366, 461)


def store_xy(c, r):
    return 110 + 29 * c, 138 + 29 * r


def inv_xy(c, r):
    return 432 + 29 * c, 330 + 29 * r


class Drv:
    def __init__(self, display, dwell):
        self.dpy = xdrive.Display(display)
        self.off = self.dpy.origin("Diablo II")
        self.dwell = dwell

    def move(self, x, y, dwell=None):
        self.dpy.move(self.off[0] + x, self.off[1] + y)
        time.sleep(self.dwell if dwell is None else dwell)

    def click(self, x, y, button=1):
        self.dpy.click(self.off[0] + x, self.off[1] + y, button=button, hold=0.12)
        time.sleep(0.3)

    def grid(self, xy, cols, rows):
        for r in range(rows):
            for c in range(cols):
                self.move(*xy(c, r))

    def equip(self):
        for xy in EQUIP.values():
            self.move(*xy)


def run(drv, tokens):
    for tok in tokens:
        kind, _, rest = tok.partition(":")
        if kind == "store":
            tabs = [int(rest)] if rest else [1, 2, 3, 4]
            for t in tabs:
                drv.click(*TABS[t - 1])
                drv.grid(store_xy, 10, 10)
        elif kind == "grid":
            drv.grid(store_xy, 10, 10)
        elif kind == "inv":
            drv.grid(inv_xy, 10, 4)
        elif kind == "equip":
            drv.equip()
        elif kind == "repair":
            drv.click(*B_REPAIR)
            drv.grid(inv_xy, 10, 4)
            drv.equip()
            drv.click(*B_REPAIR)
        elif kind == "hoverall":
            drv.move(*B_REPAIRALL, dwell=0.6)
        elif kind == "repairall":
            drv.move(*B_REPAIRALL, dwell=0.6)
            drv.click(*B_REPAIRALL)
            time.sleep(0.5)
        elif kind == "sell":
            c, r = (int(v) for v in rest.split(","))
            drv.click(*inv_xy(c, r))
            time.sleep(0.3)
            drv.click(250, 250)
            time.sleep(0.5)
        elif kind == "buy":
            t, cr = rest.split(":")
            c, r = (int(v) for v in cr.split(","))
            drv.click(*TABS[int(t) - 1])
            drv.click(*store_xy(c, r), button=3)
            time.sleep(0.5)
        elif kind in ("click", "rclick"):
            x, y = (int(v) for v in rest.split(","))
            drv.click(x, y, button=1 if kind == "click" else 3)
        elif kind == "key":
            drv.dpy.key(rest)
            time.sleep(0.3)
        elif kind == "sleep":
            time.sleep(float(rest))
        elif kind == "shot":
            drv.dpy.shot(rest, drv.off[0], drv.off[1], 800, 600)
        else:
            raise SystemExit("unknown token %r" % tok)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", type=int, required=True)
    ap.add_argument("--dwell", type=float, default=0.07)
    ap.add_argument("cmd", choices=["act"])
    ap.add_argument("tokens", nargs="+")
    a = ap.parse_args(argv)
    display = slots.display(a.slot) if hasattr(slots, "display") else ":%d" % (7 + a.slot)
    run(Drv(display, a.dwell), a.tokens)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
