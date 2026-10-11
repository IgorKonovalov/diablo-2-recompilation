// Emulate a __fastcall(u32 *seed /*ECX*/, u32 edx) function of the program once per input line,
// using Ghidra's p-code emulator on the program's own bytes.
// Usage (headless): -postScript EmuFastcall.java <out-file> <function addr> <cases-file>
// Cases: one "low high edx" line each (hex u32). Before each call the 8-byte seed {low, high} is
// written to a scratch address, ECX points at it, EDX = edx, EAX = 0xDEADBEEF, and the return
// address on the stack is a sentinel with a breakpoint. Output: one "eax low high" line (hex u32)
// per case, read after the function returns to the sentinel. Fails if a call does not reach it.
// Used to corroborate tools/rng.py bit for bit (python3 -I tools/rng.py check ...).
// @category d2-recon

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintWriter;
import java.math.BigInteger;

import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;

public class EmuFastcall extends GhidraScript {

	static final long SEED = 0x7F000000L, STACK = 0x7FF00000L, SENTINEL = 0x7EEE0000L;

	static byte[] le32(long v) {
		return new byte[] { (byte) v, (byte) (v >> 8), (byte) (v >> 16), (byte) (v >> 24) };
	}

	static long rd32(byte[] b, int o) {
		return (b[o] & 0xFFL) | (b[o + 1] & 0xFFL) << 8 | (b[o + 2] & 0xFFL) << 16 | (b[o + 3] & 0xFFL) << 24;
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length != 3) throw new IllegalArgumentException("usage: EmuFastcall.java <out-file> <fn addr> <cases>");
		Address fn = toAddr(Long.decode(args[1]));
		Address seed = toAddr(SEED), ret = toAddr(SENTINEL);
		EmulatorHelper emu = new EmulatorHelper(currentProgram);
		int n = 0;
		try (BufferedReader r = new BufferedReader(new FileReader(args[2])); PrintWriter w = new PrintWriter(args[0])) {
			emu.setBreakpoint(ret);
			String line;
			while ((line = r.readLine()) != null) {
				if (line.isBlank()) continue;
				String[] f = line.trim().split("\\s+");
				long lo = Long.parseLong(f[0], 16), hi = Long.parseLong(f[1], 16), edx = Long.parseLong(f[2], 16);
				byte[] s = new byte[8];
				System.arraycopy(le32(lo), 0, s, 0, 4);
				System.arraycopy(le32(hi), 0, s, 4, 4);
				emu.writeMemory(seed, s);
				emu.writeMemory(toAddr(STACK), le32(SENTINEL));
				emu.writeRegister("ESP", BigInteger.valueOf(STACK));
				emu.writeRegister("ECX", BigInteger.valueOf(SEED));
				emu.writeRegister("EDX", BigInteger.valueOf(edx));
				emu.writeRegister("EAX", BigInteger.valueOf(0xDEADBEEFL));
				emu.writeRegister(emu.getPCRegister(), fn.getOffset());
				emu.run(monitor);
				if (!emu.getExecutionAddress().equals(ret))
					throw new IllegalStateException("case " + (n + 1) + ": stopped at " + emu.getExecutionAddress() + ": " + emu.getLastError());
				byte[] out = emu.readMemory(seed, 8);
				long eax = emu.readRegister("EAX").longValue() & 0xFFFFFFFFL;
				w.printf("%08x %08x %08x%n", eax, rd32(out, 0), rd32(out, 4));
				n++;
			}
		}
		finally {
			emu.dispose();
		}
		println("EmuFastcall: " + n + " calls of " + fn);
	}
}
