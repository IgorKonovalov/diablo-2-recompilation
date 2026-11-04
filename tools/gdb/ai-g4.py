# Plan 0052 Phase 2 case G4 (docs/findings/ai/0016-uber-event.md section 8): entry breakpoints on the seven helpers
# the static scan finds unreferenced, with nine live controls (the LIVE rows of that scan, entries reached by a table
# pointer or a direct call). Always armed, never stops the game. One G4 line per hit of a helper; for a control the
# 1st, 2nd, 4th, 8th ... hit (a count, so that the log stays small); n is the count so far in this process.
import gdb

G4_REV = 1
HELPERS = (0x005E9DD0, 0x005FD0F0, 0x005F7F10, 0x005DD140, 0x005F8010, 0x005FC130, 0x005E9750)
CONTROLS = (0x005E9DF0, 0x005FD200, 0x005F81C0, 0x005E8480, 0x005FB410, 0x005A3250, 0x005E0070, 0x005FCB60, 0x005B1CF0)


def _g4_main():
    count = {}

    class G4Bp(gdb.Breakpoint):
        def __init__(self, addr, control):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.addr, self.control = addr, control

        def stop(self):
            try:
                n = count.get(self.addr, 0) + 1
                count[self.addr] = n
                if not self.control or (n & (n - 1)) == 0:
                    gdb.write("G4 %s 0x%08X n=%d\n" % ("control" if self.control else "HELPER", self.addr, n))
            except Exception as e:
                gdb.write("LOGERR g4 %r\n" % (e,))
            return False

    for a in HELPERS:
        G4Bp(a, False)
    for a in CONTROLS:
        G4Bp(a, True)
    gdb.write("G4 armed rev %d helpers %d controls %d\n" % (G4_REV, len(HELPERS), len(CONTROLS)))


_g4_main()
