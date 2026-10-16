// Emulate one function of the program once per input line with given registers, stack arguments and memory, using
// Ghidra's p-code emulator on the program's own bytes. For pure-enough functions that read tables through a global
// pointer (patch the pointer to a scratch image).
// Usage (headless): -postScript EmuCall.java <out-file> <function addr> <cases-file> <memory-spec>
// Memory spec, applied before every case, one directive per line ('#' comments):
//   load  <hex addr> <path>      write the file's bytes at addr
//   dword <hex addr> <hex value> write one u32
// Cases: one "ecx edx arg1 ... argN" line each (hex u32; N may be 0); the arguments are pushed as for __stdcall /
// __fastcall (arg1 at [ESP+4]), the return address is a sentinel with a breakpoint, EAX = 0xDEADBEEF.
// Output: one "eax pop" line (hex u32, decimal) per case: EAX and the bytes the callee popped besides the return
// address (ESP after the return minus the entry ESP minus 4). Fails if a call does not reach the sentinel.
// Paired with a tools/ model (tools/calc_funcs.py misscalc).
// @category d2-recon

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintWriter;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;

public class EmuCall extends GhidraScript {

	static final long STACK = 0x7FF00000L, SENTINEL = 0x7EEE0000L;

	static byte[] le32(long v) {
		return new byte[] { (byte) v, (byte) (v >> 8), (byte) (v >> 16), (byte) (v >> 24) };
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length != 4) throw new IllegalArgumentException("usage: EmuCall.java <out-file> <fn addr> <cases> <memory-spec>");
		Address fn = toAddr(Long.decode(args[1]));
		Address ret = toAddr(SENTINEL);
		List<Address> where = new ArrayList<>();
		List<byte[]> what = new ArrayList<>();
		for (String line : Files.readAllLines(Paths.get(args[3]))) {
			String t = line.replaceAll("#.*", "").trim();
			if (t.isEmpty()) continue;
			String[] f = t.split("\\s+");
			Address a = toAddr(Long.parseLong(f[1], 16));
			if (f[0].equals("load")) what.add(Files.readAllBytes(Paths.get(f[2])));
			else if (f[0].equals("dword")) what.add(le32(Long.parseLong(f[2], 16)));
			else throw new IllegalArgumentException("memory spec: " + line);
			where.add(a);
		}
		EmulatorHelper emu = new EmulatorHelper(currentProgram);
		int n = 0;
		try (BufferedReader r = new BufferedReader(new FileReader(args[2])); PrintWriter w = new PrintWriter(args[0])) {
			emu.setBreakpoint(ret);
			String line;
			while ((line = r.readLine()) != null) {
				if (line.isBlank()) continue;
				String[] f = line.trim().split("\\s+");
				for (int i = 0; i < where.size(); i++) emu.writeMemory(where.get(i), what.get(i));
				emu.writeMemory(toAddr(STACK), le32(SENTINEL));
				for (int i = 2; i < f.length; i++) emu.writeMemory(toAddr(STACK + 4L * (i - 1)), le32(Long.parseLong(f[i], 16)));
				emu.writeRegister("ESP", BigInteger.valueOf(STACK));
				emu.writeRegister("ECX", BigInteger.valueOf(Long.parseLong(f[0], 16)));
				emu.writeRegister("EDX", BigInteger.valueOf(Long.parseLong(f[1], 16)));
				emu.writeRegister("EAX", BigInteger.valueOf(0xDEADBEEFL));
				emu.writeRegister(emu.getPCRegister(), fn.getOffset());
				emu.run(monitor);
				if (!emu.getExecutionAddress().equals(ret))
					throw new IllegalStateException("case " + (n + 1) + ": stopped at " + emu.getExecutionAddress() + ": " + emu.getLastError());
				long esp = emu.readRegister("ESP").longValue() & 0xFFFFFFFFL;
				long eax = emu.readRegister("EAX").longValue() & 0xFFFFFFFFL;
				w.printf("%08x %d%n", eax, esp - STACK - 4);
				n++;
			}
		}
		finally {
			emu.dispose();
		}
		println("EmuCall: " + n + " calls of " + fn);
	}
}
