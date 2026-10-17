// Emulate calls of the program's own functions with Ghidra's p-code emulator, a memory spec, per-case memory, dumps
// after each call, and a trace of every memory access outside the stack and the bytes the spec and the case wrote
// (ADR-0015 condition 2: the record accounts for each traced address). Plan 0038 batch S1e.
// Usage (headless): -postScript EmuTrace.java <out-file> <cases-file> <memory-spec>
// Memory spec, applied before every case, one directive per line ('#' comments):
//   load  <hex addr> <path>      write the file's bytes at addr
//   dword <hex addr> <hex value> write one u32
//   bytes <hex addr> <hex>       write the bytes
//   const <directive>            the same, written once before the first case; reads there are not traced and
//                                writes there are (a const range must stay unwritten)
// Cases file: blocks of lines, each ended by a call line:
//   w <hex addr> <hex bytes>     write before this call (this case only; the spec is re-applied before the next)
//   d <hex addr> <dec len>       dump these bytes after the call
//   s <hex addr> <dec len>       mark a range as case memory without writing it (reads there are not traced)
//   r <reg> <hex value>          set a register after the defaults (EAX, EBX, ESI, EDI: register arguments)
//   call <hex fn> <hex ecx> <hex edx> [<hex arg>...]   arguments pushed as for __stdcall/__fastcall (arg1 at [ESP+4])
// Output, per case:
//   C <n> <fn> eax=<hex> edx=<hex> pop=<dec> steps=<dec>      (pop = ESP after the return - entry ESP - 4)
//   C <n> <fn> STOP <pc> steps=<dec> <message>               (did not return: fault, limit or decode error)
//   D <hex addr> <hex bytes>
// and once at the end, every traced access, aggregated over all cases:
//   R <hex pc> <hex addr> <size> <count>                       (a read outside the stack, spec and case memory)
//   W <hex pc> <hex addr> <size> <count>                       (a write there)
// Instruction fetches are not traced. The return address is a sentinel with a breakpoint; on entry EAX = 0xDEADBEEF,
// EBX = ESI = EDI = 0 and EBP = 0x7FF00800, unless an r line sets them.
// Paired with tools/sweep_s1e.py.
// @category d2-recon

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintWriter;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.emulator.MemoryAccessFilter;
import ghidra.app.script.GhidraScript;
import ghidra.pcode.emulate.EmulateExecutionState;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;

public class EmuTrace extends GhidraScript {

	static final long STACK = 0x7FF00000L, SENTINEL = 0x7EEE0000L, STACK_LO = 0x7FE00000L, STACK_HI = 0x7FF01000L;
	static final long MAX_STEPS = 20_000_000L;

	static byte[] le32(long v) {
		return new byte[] { (byte) v, (byte) (v >> 8), (byte) (v >> 16), (byte) (v >> 24) };
	}

	static byte[] hex(String s) {
		byte[] b = new byte[s.length() / 2];
		for (int i = 0; i < b.length; i++) b[i] = (byte) Integer.parseInt(s.substring(2 * i, 2 * i + 2), 16);
		return b;
	}

	// declared ranges [lo, hi)
	final List<long[]> spec = new ArrayList<>(), constSpec = new ArrayList<>(), caseMem = new ArrayList<>();
	final Map<String, long[]> reads = new TreeMap<>(), writes = new TreeMap<>();
	EmulatorHelper helper;

	boolean declared(long a, int n, boolean write) {
		if (a >= STACK_LO && a + n <= STACK_HI) return true;
		if (!write) for (long[] r : constSpec) if (a >= r[0] && a + n <= r[1]) return true;
		for (long[] r : spec) if (a >= r[0] && a + n <= r[1]) return true;
		for (long[] r : caseMem) if (a >= r[0] && a + n <= r[1]) return true;
		return false;
	}

	void note(Map<String, long[]> m, long a, int n) {
		long pc = helper.getEmulator().getExecuteAddress().getOffset();
		String k = String.format("%08x %08x %d", pc, a, n);
		long[] c = m.get(k);
		if (c == null) m.put(k, new long[] { 1 });
		else c[0]++;
	}

	class Tracer extends MemoryAccessFilter {
		@Override
		protected void processRead(AddressSpace spc, long off, int size, byte[] values) {
			if (!spc.getName().equals("ram")) return;
			if (helper.getEmulator().getEmulateExecutionState() == EmulateExecutionState.INSTRUCTION_DECODE) return;
			if (!declared(off, size, false)) note(reads, off, size);
		}

		@Override
		protected void processWrite(AddressSpace spc, long off, int size, byte[] values) {
			if (!spc.getName().equals("ram")) return;
			if (!declared(off, size, true)) note(writes, off, size);
		}
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length != 3) throw new IllegalArgumentException("usage: EmuTrace.java <out-file> <cases> <memory-spec>");
		List<Address> where = new ArrayList<>(), whereOnce = new ArrayList<>();
		List<byte[]> what = new ArrayList<>(), whatOnce = new ArrayList<>();
		for (String line : Files.readAllLines(Paths.get(args[2]))) {
			String t = line.replaceAll("#.*", "").trim();
			if (t.isEmpty()) continue;
			boolean once = t.startsWith("const ");
			if (once) t = t.substring(6).trim();
			String[] f = t.split("\\s+");
			long a = Long.parseLong(f[1], 16);
			byte[] b;
			if (f[0].equals("load")) b = Files.readAllBytes(Paths.get(f[2]));
			else if (f[0].equals("dword")) b = le32(Long.parseLong(f[2], 16));
			else if (f[0].equals("bytes")) b = hex(f[2]);
			else throw new IllegalArgumentException("memory spec: " + line);
			(once ? whereOnce : where).add(toAddr(a));
			(once ? whatOnce : what).add(b);
			(once ? constSpec : spec).add(new long[] { a, a + b.length });
		}
		helper = new EmulatorHelper(currentProgram);
		Tracer tracer = new Tracer();
		helper.getEmulator().addMemoryAccessFilter(tracer);
		Address ret = toAddr(SENTINEL);
		helper.setBreakpoint(ret);
		for (int i = 0; i < whereOnce.size(); i++) helper.writeMemory(whereOnce.get(i), whatOnce.get(i));
		int n = 0;
		List<String[]> pre = new ArrayList<>();
		List<long[]> dumps = new ArrayList<>();
		try (BufferedReader r = new BufferedReader(new FileReader(args[1])); PrintWriter w = new PrintWriter(args[0])) {
			String line;
			while ((line = r.readLine()) != null) {
				String t = line.replaceAll("#.*", "").trim();
				if (t.isEmpty()) continue;
				String[] f = t.split("\\s+");
				if (f[0].equals("w") || f[0].equals("s") || f[0].equals("r")) { pre.add(f); continue; }
				if (f[0].equals("d")) { dumps.add(new long[] { Long.parseLong(f[1], 16), Long.parseLong(f[2]) }); continue; }
				if (!f[0].equals("call")) throw new IllegalArgumentException("cases: " + line);
				n++;
				caseMem.clear();
				for (int i = 0; i < where.size(); i++) helper.writeMemory(where.get(i), what.get(i));
				List<String[]> regs = new ArrayList<>();
				for (String[] p : pre) {
					if (p[0].equals("r")) { regs.add(p); continue; }
					long a = Long.parseLong(p[1], 16);
					if (p[0].equals("w")) {
						byte[] b = hex(p[2]);
						helper.writeMemory(toAddr(a), b);
						caseMem.add(new long[] { a, a + b.length });
					}
					else caseMem.add(new long[] { a, a + Long.parseLong(p[2]) });
				}
				long fn = Long.parseLong(f[1], 16);
				helper.writeMemory(toAddr(STACK), le32(SENTINEL));
				for (int i = 4; i < f.length; i++) helper.writeMemory(toAddr(STACK + 4L * (i - 3)), le32(Long.parseLong(f[i], 16)));
				helper.writeRegister("ESP", BigInteger.valueOf(STACK));
				helper.writeRegister("EBP", BigInteger.valueOf(0x7FF00800L));
				helper.writeRegister("ECX", BigInteger.valueOf(Long.parseLong(f[2], 16)));
				helper.writeRegister("EDX", BigInteger.valueOf(Long.parseLong(f[3], 16)));
				helper.writeRegister("EAX", BigInteger.valueOf(0xDEADBEEFL));
				for (String g : new String[] { "EBX", "ESI", "EDI" }) helper.writeRegister(g, BigInteger.ZERO);
				for (String[] p : regs) helper.writeRegister(p[1].toUpperCase(), BigInteger.valueOf(Long.parseLong(p[2], 16)));
				helper.writeRegister(helper.getPCRegister(), fn);
				long steps = 0;
				String stop = null;
				try {
					while (true) {
						Address pc = helper.getExecutionAddress();
						if (pc.equals(ret)) break;
						if (!currentProgram.getMemory().getExecuteSet().contains(pc)) { stop = "pc outside the image's code"; break; }
						if (steps >= MAX_STEPS) { stop = "step limit"; break; }
						if (!helper.step(monitor)) { stop = String.valueOf(helper.getLastError()); break; }
						steps++;
					}
				}
				catch (Exception e) {
					stop = e.getClass().getSimpleName() + ": " + e.getMessage();
				}
				if (stop != null) {
					w.printf("C %d %08x STOP %s steps=%d %s%n", n, fn, helper.getExecutionAddress(), steps, stop.replace('\n', ' '));
				}
				else {
					long esp = helper.readRegister("ESP").longValue() & 0xFFFFFFFFL;
					long eax = helper.readRegister("EAX").longValue() & 0xFFFFFFFFL;
					long edx = helper.readRegister("EDX").longValue() & 0xFFFFFFFFL;
					w.printf("C %d %08x eax=%08x edx=%08x pop=%d steps=%d%n", n, fn, eax, edx, esp - STACK - 4, steps);
				}
				for (long[] d : dumps) {
					byte[] b = helper.readMemory(toAddr(d[0]), (int) d[1]);
					StringBuilder sb = new StringBuilder();
					for (byte x : b) sb.append(String.format("%02x", x & 0xFF));
					w.printf("D %08x %s%n", d[0], sb);
				}
				pre.clear();
				dumps.clear();
			}
			for (Map.Entry<String, long[]> e : reads.entrySet()) w.printf("R %s %d%n", e.getKey(), e.getValue()[0]);
			for (Map.Entry<String, long[]> e : writes.entrySet()) w.printf("W %s %d%n", e.getKey(), e.getValue()[0]);
		}
		finally {
			helper.dispose();
		}
		println("EmuTrace: " + n + " calls");
	}
}
