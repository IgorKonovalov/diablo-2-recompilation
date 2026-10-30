# Plan 0056 Phase 2 probe logger: process state across games. Sourced after mon-special.py (tools/gdb/probe-0056.gdb).
# PST {"hc":g_HitClassCounter (byte, 0x0088CAD0), "po":g_PlayersOverride (u32, 0x00883D70), "t":wall seconds},
# at most one line per second, on the PLR breakpoint (COLL_PatternMark 0x0064EA90, a player's mark), so every game
# that has a player on the map writes some. HCP: HitClassPick 0x0057CE30 entry, the counter before the pick.
# A harness helper, not a model input.
import json
import struct
import time

import gdb


def _probe_main():
    inf = gdb.selected_inferior()
    last = [0.0]

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))
        gdb.flush()

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:
                gdb.write("LOGERR %r\n" % (e,))
            return False

    def on_plr():
        now = time.time()
        if now - last[0] < 1.0:
            return
        last[0] = now
        emit("PST", {"hc": mem(0x0088CAD0, 1)[0], "po": struct.unpack("<I", mem(0x00883D70, 4))[0],
                     "t": round(now, 1)})

    def on_hcp():
        emit("HCP", {"hc": mem(0x0088CAD0, 1)[0]})

    Bp(0x0064EA90, on_plr)
    Bp(0x0057CE30, on_hcp)
    gdb.write("PROBE0056 logger armed\n")


_probe_main()
