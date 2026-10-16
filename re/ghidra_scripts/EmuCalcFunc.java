// Emulate one calc-formula function (an entry of g_SkillsCalcFuncs, g_MissCalcFuncs or g_ItemCalcFuncs) once per
// input line, using Ghidra's p-code emulator on the program's own bytes.
// Usage (headless): -postScript EmuCalcFunc.java <out-file> <function addr> <cases-file>
// The calling convention is CALC_Eval's (docs/findings/data/0005-calc.md § 5): __fastcall(ECX = a, EDX = b), stack:
// c, ctx; callee pops 8. Cases: one "a b c ctx low high" line each (hex u32); ctx 0 passes NULL, any other value
// passes a scratch context block whose dword 0 points at a scratch unit. The 8-byte seed {low, high} is written both
// at unit+0x20 (the unit seed the skills and items rand use) and at ctx+0x20 (the missiles rand's address).
// Output: one "eax ulow uhigh clow chigh" line (hex u32) per case: EAX and the two seed copies after the return to
// a sentinel. Fails if a call does not reach it. Paired with tools/calc_funcs.py check.
// @category d2-recon

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintWriter;
import java.math.BigInteger;

import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;

public class EmuCalcFunc extends GhidraScript {

	static final long CTX = 0x7F100000L, UNIT = 0x7F200000L, STACK = 0x7FF00000L, SENTINEL = 0x7EEE0000L;

	static byte[] le32(long v) {
		return new byte[] { (byte) v, (byte) (v >> 8), (byte) (v >> 16), (byte) (v >> 24) };
	}

	static long rd32(byte[] b, int o) {
		return (b[o] & 0xFFL) | (b[o + 1] & 0xFFL) << 8 | (b[o + 2] & 0xFFL) << 16 | (b[o + 3] & 0xFFL) << 24;
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length != 3) throw new IllegalArgumentException("usage: EmuCalcFunc.java <out-file> <fn addr> <cases>");
		Address fn = toAddr(Long.decode(args[1]));
		Address ret = toAddr(SENTINEL), useed = toAddr(UNIT + 0x20), cseed = toAddr(CTX + 0x20);
		EmulatorHelper emu = new EmulatorHelper(currentProgram);
		int n = 0;
		try (BufferedReader r = new BufferedReader(new FileReader(args[2])); PrintWriter w = new PrintWriter(args[0])) {
			emu.setBreakpoint(ret);
			String line;
			while ((line = r.readLine()) != null) {
				if (line.isBlank()) continue;
				String[] f = line.trim().split("\\s+");
				long a = Long.parseLong(f[0], 16), b = Long.parseLong(f[1], 16), c = Long.parseLong(f[2], 16);
				long ctx = Long.parseLong(f[3], 16), lo = Long.parseLong(f[4], 16), hi = Long.parseLong(f[5], 16);
				byte[] s = new byte[8];
				System.arraycopy(le32(lo), 0, s, 0, 4);
				System.arraycopy(le32(hi), 0, s, 4, 4);
				emu.writeMemory(toAddr(CTX), le32(UNIT));
				emu.writeMemory(useed, s);
				emu.writeMemory(cseed, s);
				emu.writeMemory(toAddr(STACK), le32(SENTINEL));
				emu.writeMemory(toAddr(STACK + 4), le32(c));
				emu.writeMemory(toAddr(STACK + 8), le32(ctx == 0 ? 0 : CTX));
				emu.writeRegister("ESP", BigInteger.valueOf(STACK));
				emu.writeRegister("ECX", BigInteger.valueOf(a));
				emu.writeRegister("EDX", BigInteger.valueOf(b));
				emu.writeRegister("EAX", BigInteger.valueOf(0xDEADBEEFL));
				emu.writeRegister(emu.getPCRegister(), fn.getOffset());
				emu.run(monitor);
				if (!emu.getExecutionAddress().equals(ret))
					throw new IllegalStateException("case " + (n + 1) + ": stopped at " + emu.getExecutionAddress() + ": " + emu.getLastError());
				long esp = emu.readRegister("ESP").longValue() & 0xFFFFFFFFL;
				if (esp != STACK + 12)
					throw new IllegalStateException("case " + (n + 1) + ": ESP " + Long.toHexString(esp) + " after the return, want callee pop 8");
				byte[] u = emu.readMemory(useed, 8), cs = emu.readMemory(cseed, 8);
				long eax = emu.readRegister("EAX").longValue() & 0xFFFFFFFFL;
				w.printf("%08x %08x %08x %08x %08x%n", eax, rd32(u, 0), rd32(u, 4), rd32(cs, 0), rd32(cs, 4));
				n++;
			}
		}
		finally {
			emu.dispose();
		}
		println("EmuCalcFunc: " + n + " calls of " + fn);
	}
}
