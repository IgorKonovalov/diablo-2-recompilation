#!/usr/bin/env python3
"""Static scan for the state ids the code passes to the state setters and testers of the pinned Game.exe.

    python3 -I tools/state_setters.py [--exe workspace/install/app/game.exe] [--asm <objdump .text dump>]
                                      [--ids 0,6,12,...] [--all]

Plan 0041 P1 review follow-up (b) (stats/0002 § Phase 0 surprise (f)). For every direct `call` (rel32, found in a GNU
objdump disassembly of `.text`) to one of the functions below, it resolves the state argument when the code passes it
as an immediate:

  - stdcall (unit|list, state, ...) functions, state = 2nd argument = the 2nd `push` walking back from the call:
    STATE_Set 0x00639DB0, UNIT_SetStateBit 0x00625A70, UNIT_HasState 0x00639DF0, UNIT_TestStateBit 0x00625B70,
    UNIT_FindStatListByState 0x006256B0, sub_00625650_StatListFindByState 0x00625650, STATLIST_SetState 0x006252D0;
  - STATE_ApplyTimed 0x0056E970 (ECX = request), state = request +0x1C: the last `lea D(%B),%ecx` before the call,
    then the last store to D+0x1C(%B) before the call.

A pushed or stored register is resolved to the last `mov $imm,%reg` (or `xor %reg,%reg` = 0) before it with no other
write to that register in between (the argument walk stops at a call, ret, jmp or jcc; the register walk crosses a jcc
and says so, stops at a call, ret or jmp, and after 40 instructions). A value found across a jcc is a candidate, to be
read at the site: a jump target between the two instructions is not detected. Anything else is printed as `?` with the instruction, so the scan under-approximates: an id
computed at run time, taken from a table or a caller's argument, or written across a branch is not listed. Print
lines: `<call site> <callee> <state|?> [on=<3rd argument of STATE_Set / UNIT_SetStateBit>] <how>`; in the per-id
summary a STATE_Set site carries its on/off argument as `STATE_Set(1)` / `STATE_Set(0)` when it is an immediate. With --ids, only the listed ids (and a per-id summary); --all prints
the unresolved sites too. Stdlib only; runs objdump once unless --asm gives a saved dump. Read-only.
"""
import argparse
import collections
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(os.path.dirname(HERE), "workspace", "install", "app", "game.exe")

ARG2 = {
    0x00639DB0: "STATE_Set",
    0x00625A70: "UNIT_SetStateBit",
    0x00639DF0: "UNIT_HasState",
    0x00625B70: "UNIT_TestStateBit",
    0x006256B0: "UNIT_FindStatListByState",
    0x00625650: "sub_00625650_StatListFindByState",
    0x006252D0: "STATLIST_SetState",
}
APPLY = 0x0056E970
SETTERS = {"STATE_Set", "UNIT_SetStateBit", "STATLIST_SetState", "STATE_ApplyTimed"}

LINE = re.compile(r"^\s*([0-9a-f]+):\s+(\S+)\s*(.*)$")
STOP = re.compile(r"^(call|ret|jmp|loop)")
JCC = re.compile(r"^j[a-z]+$")
REGS = ["eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"]


def disasm(exe):
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-j", ".text", exe],
                         check=True, capture_output=True, text=True).stdout
    return out.splitlines()


def parse(lines):
    ins = []
    for ln in lines:
        m = LINE.match(ln)
        if m:
            ins.append((int(m.group(1), 16), m.group(2), m.group(3).split("#")[0].strip()))
    return ins


def dest(ops):
    """Destination operand of an AT&T instruction (last operand), or ''."""
    if not ops:
        return ""
    depth, parts, cur = 0, [], ""
    for ch in ops:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts[-1].strip()


def writes_reg(mn, ops, reg):
    if mn.startswith(("push", "cmp", "test")):
        return False
    d = dest(ops)
    if d == "%" + reg:
        return True
    sub = {"eax": ("%ax", "%al", "%ah"), "ebx": ("%bx", "%bl", "%bh"), "ecx": ("%cx", "%cl", "%ch"),
           "edx": ("%dx", "%dl", "%dh"), "esi": ("%si",), "edi": ("%di",), "ebp": ("%bp",)}[reg]
    if d in sub:
        return True
    if mn in ("cltd", "cdq") and reg == "edx":
        return True
    if mn in ("cwtl", "cwde") and reg == "eax":
        return True
    return False


def resolve_reg(ins, i, reg):
    """Value of %reg just before ins[i], walking back; (value|None, how). A conditional jump is crossed (it writes
    no register) and noted, since a label between the two instructions is not detected."""
    jcc = ""
    for j in range(i - 1, max(-1, i - 40), -1):
        a, mn, ops = ins[j]
        if STOP.match(mn):
            return None, "%s crosses %s at 0x%08X" % (reg, mn, a)
        if JCC.match(mn):
            jcc = " (crossed %s at 0x%08X)" % (mn, a)
            continue
        m = re.match(r"^\$0x([0-9a-f]+),%" + reg + "$", ops)
        if mn == "mov" and m:
            return int(m.group(1), 16), "mov $imm,%%%s at 0x%08X%s" % (reg, a, jcc)
        if mn == "xor" and ops == "%%%s,%%%s" % (reg, reg):
            return 0, "xor %%%s at 0x%08X%s" % (reg, a, jcc)
        if writes_reg(mn, ops, reg):
            return None, "%s %s at 0x%08X" % (mn, ops, a)
    return None, "%s: window" % reg


def operand_value(ins, i, op):
    m = re.match(r"^\$0x([0-9a-f]+)$", op)
    if m:
        return int(m.group(1), 16), "imm at 0x%08X" % ins[i][0]
    m = re.match(r"^%(e[a-z]{2})$", op)
    if m and m.group(1) in REGS:
        return resolve_reg(ins, i, m.group(1))
    return None, "%s at 0x%08X" % (op, ins[i][0])


def arg2(ins, i, k=2):
    n = 0
    for j in range(i - 1, max(-1, i - 40), -1):
        a, mn, ops = ins[j]
        if STOP.match(mn) or JCC.match(mn):
            return None, "call args cross %s at 0x%08X" % (mn, a)
        if mn in ("push", "pushl"):
            n += 1
            if n == k:
                return operand_value(ins, j, ops)
        elif mn == "pop":
            return None, "pop at 0x%08X" % a
    return None, "window"


def mem(op):
    m = re.match(r"^(-?0x[0-9a-f]+)?\((%e[a-z]{2})\)$", op)
    if not m:
        return None
    return int(m.group(1) or "0", 16), m.group(2)


def apply_state(ins, i):
    base = None
    for j in range(i - 1, max(-1, i - 60), -1):
        a, mn, ops = ins[j]
        if STOP.match(mn) or JCC.match(mn):
            return None, "lea not found before %s at 0x%08X" % (mn, a)
        if mn == "lea" and ops.endswith(",%ecx"):
            base = mem(ops[: -len(",%ecx")])
            break
        if mn == "mov" and dest(ops) == "%ecx":
            return None, "ecx = %s at 0x%08X" % (ops, a)
    if not base:
        return None, "no lea"
    want = (base[0] + 0x1C, base[1])
    for j in range(i - 1, max(-1, i - 60), -1):
        a, mn, ops = ins[j]
        if STOP.match(mn) or JCC.match(mn):
            break
        if mn in ("mov", "movl") and mem(dest(ops)) == want:
            src = ops[: len(ops) - len(dest(ops)) - 1]
            return operand_value(ins, j, src)
    return None, "no store to req+0x1C"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exe", default=EXE)
    ap.add_argument("--asm", help="saved `objdump -d --no-show-raw-insn -j .text` output")
    ap.add_argument("--ids", help="comma-separated state ids to report")
    ap.add_argument("--all", action="store_true", help="print unresolved sites too")
    a = ap.parse_args()
    lines = open(a.asm).read().splitlines() if a.asm else disasm(a.exe)
    ins = parse(lines)
    ids = {int(x) for x in a.ids.split(",")} if a.ids else None
    per = collections.defaultdict(list)
    total = resolved = 0
    for i, (addr, mn, ops) in enumerate(ins):
        if mn != "call":
            continue
        m = re.match(r"^0x([0-9a-f]+)$", ops)
        if not m:
            continue
        tgt = int(m.group(1), 16)
        if tgt in ARG2:
            name = ARG2[tgt]
            v, how = arg2(ins, i)
        elif tgt == APPLY:
            name = "STATE_ApplyTimed"
            v, how = apply_state(ins, i)
        else:
            continue
        total += 1
        if v is not None:
            resolved += 1
            per[v].append((addr, name))
        on = ""
        if name in ("STATE_Set", "UNIT_SetStateBit"):
            o, _ = arg2(ins, i, 3)
            on = " on=%s" % ("?" if o is None else o)
            if v is not None:
                per[v][-1] = (addr, name + ("" if o is None else "(%d)" % o))
        if (v is None and a.all) or (v is not None and (ids is None or v in ids)):
            print("0x%08X %-34s %s%s  %s" % (addr, name, "?" if v is None else v, on, how))
    print("# call sites %d, state resolved %d, unresolved %d" % (total, resolved, total - resolved))
    if ids is not None:
        for s in sorted(ids):
            sites = per.get(s, [])
            kinds = sorted({n.split("(")[0] for _, n in sites})
            tag = "set" if any(k in SETTERS for k in kinds) else ("tested" if sites else "none")
            print("# id %3d %-6s %s" % (s, tag, ", ".join("0x%08X %s" % (x, n) for x, n in sites) or "-"))


if __name__ == "__main__":
    sys.exit(main())
