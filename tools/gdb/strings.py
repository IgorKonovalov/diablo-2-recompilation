# gdb Python logger for plan 0028 Phase 1 (string tables at run time): docs/findings/data/0003-string-tables.md.
# Sourced by tools/gdb/strings.gdb after tools/gdb/pilot.py. One line per event, "TAG {json}". Addresses refer to the
# pinned game.exe (image base 0x400000). Every line carries "th" (the gdb thread number). Rate limit: one line per
# distinct (index, tables loaded) and per distinct (key, tables loaded); repeats only count (SSTAT).
#
# Tables: file buffers g_pStringTbl 0x008829B4, g_pPatchStringTbl 0x008829D0, g_pExpStringTbl 0x008829D4; converted
# text arrays (one pointer per hash node) 0x008829B8, 0x008829BC, 0x008829C0. "t" names a table: "s" string,
# "p" patchstring, "x" expansionstring. "ld" = the tables loaded at the call, e.g. "spx" or "sp".
#
#   SIDX  STRTABLE_GetByIndex 0x00524A30 (CX = index) paired with its STRTABLE_EntryToString success exit 0x005249AD
#         (ECX = table buffer, EDX = text array, EAX = node; the entry argument [EBP+8] before the >= count -> 500
#         rule; return address [EBP+4] in GetByIndex): index in, ld, table, entry argument, node, the returned
#         UTF-16 text (u16 code units, as a string), its length, and the caller of GetByIndex
#   SKEY  STRTABLE_GetByKey 0x00524D30 (key [ESP+4], out [ESP+8]) up to its returns 0x00524D90 / 0x00524DB7 /
#         0x00524DE4 / 0x00524E13 (AX = index, *out = text): key (latin-1), ld, index returned, text returned, caller,
#         and "f": one record per STRTABLE_FindInTable 0x00524C60 call (EDI = table buffer) inside it: table, home
#         slot (EAX after STRTABLE_Hash, 0x00524C82), "n" the number of nodes examined and the result: at the match
#         exit 0x00524CEA the slot (EAX), the count ([EBP-8]) and the node's entry (u16 at nodes + 17 * slot + 1,
#         nodes = [EBP-4]); at the give-up exit 0x00524CDE the count (ESI) and null. The slots examined are home,
#         home + 1, ... (mod hash_size), so home and n name every one; a breakpoint per probe was too slow (a key
#         absent from patchstring examines all max_probes = 1 180 nodes of it, see SSTAT)
#   SSTAT every 30 s and at the first event: hits and distinct counts so far
import json
import struct
import time

import gdb


def _strings_main():
    inf = gdb.selected_inferior()
    TBL = {0x008829B4: "s", 0x008829D0: "p", 0x008829D4: "x"}
    TXT = {0x008829B8: "s", 0x008829BC: "p", 0x008829C0: "x"}
    GBI_RET = {0x00524A5D, 0x00524A84, 0x00524ABD}
    pend_i = {}    # thread -> (index, ld, caller)
    pend_k = {}    # thread -> {"key", "ld", "ra", "f": [...]}
    seen_i, seen_k = set(), set()
    st = {"idx_hits": 0, "key_hits": 0, "idx_lines": 0, "key_lines": 0, "t0": time.time(), "last": 0.0}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        d["th"] = thn()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"), ensure_ascii=True)))

    def stat(force=False):
        now = time.time()
        if force or now - st["last"] >= 30:
            st["last"] = now
            emit("SSTAT", {"t": round(now - st["t0"], 1), "idx_hits": st["idx_hits"], "key_hits": st["key_hits"],
                           "idx_lines": st["idx_lines"], "key_lines": st["key_lines"]})

    def loaded():
        return "".join(t for a, t in sorted(TBL.items(), key=lambda kv: "spx".index(kv[1])) if u32(a))

    def cstr(a, cap=1024):
        out = b""
        while len(out) < cap:
            chunk = mem(a + len(out), 64)
            z = chunk.find(b"\0")
            if z >= 0:
                return out + chunk[:z]
            out += chunk
        return out

    def wstr(a, cap=8192):
        units = []
        while len(units) < cap:
            chunk = mem(a + 2 * len(units), 128)
            for i in range(0, 128, 2):
                u = chunk[i] | chunk[i + 1] << 8
                if u == 0:
                    return units
                units.append(u)
        return units

    def utext(units):
        return "".join(chr(u) for u in units)

    def tname(buf):
        for a, t in TBL.items():
            if buf and u32(a) == buf:
                return t
        return "?%08x" % buf

    def aname(arr):
        for a, t in TXT.items():
            if arr and u32(a) == arr:
                return t
        return "?%08x" % arr

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR strings %r\n" % (e,))
            return False

    # --- index -> text -------------------------------------------------------------------------------------------
    def on_gbi():
        st["idx_hits"] += 1
        pend_i[thn()] = (reg("ecx") & 0xFFFF, loaded(), u32(reg("esp")))

    def on_ets_ok():
        ebp = reg("ebp")
        if u32(ebp + 4) not in GBI_RET:
            return
        p = pend_i.pop(thn(), None)
        if p is None:
            return
        idx, ld, ra = p
        if (idx, ld) in seen_i:
            return
        seen_i.add((idx, ld))
        node, arr = reg("eax"), reg("edx")
        units = wstr(u32(arr + 4 * node))
        st["idx_lines"] += 1
        emit("SIDX", {"idx": idx, "ld": ld, "t": tname(reg("ecx")), "ta": aname(arr), "entry": u16(ebp + 8),
                      "node": node, "len": len(units), "text": utext(units), "ra": ra})
        stat(st["idx_lines"] == 1)

    # --- key -> index --------------------------------------------------------------------------------------------
    def on_gbk():
        st["key_hits"] += 1
        esp = reg("esp")
        kp = u32(esp + 4)
        pend_k[thn()] = {"key": cstr(kp).decode("latin-1") if kp else None, "ld": loaded(), "ra": u32(esp),
                         "f": []}

    def on_fit():
        k = pend_k.get(thn())
        if k is not None:
            k["f"].append({"t": tname(reg("edi")), "home": None, "n": None, "res": None, "slot": None})

    def on_fit_home():
        k = pend_k.get(thn())
        if k is not None and k["f"]:
            k["f"][-1]["home"] = reg("eax")

    def on_fit_giveup():
        k = pend_k.get(thn())
        if k is not None and k["f"]:
            k["f"][-1]["n"] = reg("esi")

    def on_fit_found():
        k = pend_k.get(thn())
        if k is not None and k["f"]:
            ebp = reg("ebp")
            k["f"][-1].update({"n": u32(ebp - 8), "slot": reg("eax"), "res": u16(u32(ebp - 4) + 17 * reg("eax") + 1)})

    def on_gbk_ret():
        k = pend_k.pop(thn(), None)
        if k is None:
            return
        sig = (k["key"], k["ld"])
        if sig in seen_k:
            return
        seen_k.add(sig)
        outp = u32(reg("esp") + 8)
        tp = u32(outp) if outp else 0
        units = wstr(tp) if tp else []
        k.update({"idx": reg("eax") & 0xFFFF, "len": len(units), "text": utext(units[:200])})
        st["key_lines"] += 1
        emit("SKEY", k)
        stat(st["key_lines"] == 1)

    Bp(0x00524A30, on_gbi)
    Bp(0x005249AD, on_ets_ok)
    Bp(0x00524D30, on_gbk)
    Bp(0x00524C60, on_fit)
    Bp(0x00524C82, on_fit_home)
    Bp(0x00524CDE, on_fit_giveup)
    Bp(0x00524CEA, on_fit_found)
    for a in (0x00524D90, 0x00524DB7, 0x00524DE4, 0x00524E13):
        Bp(a, on_gbk_ret)
    gdb.write("STRINGS logger armed\n")


_strings_main()
