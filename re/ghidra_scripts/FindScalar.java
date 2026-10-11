// Find instructions that use an immediate (scalar) operand, grouped by containing function.
// Usage (headless): -postScript FindScalar.java <out-file> <value> [<value> ...]
// <value> is decimal or 0x-hex; it is matched as an unsigned 32-bit value against every scalar
// operand of every instruction. Output, one line per function, sorted by function entry:
//   0x<entry> <name> size=<bytes> callers=<n> hits=<n> first=0x<addr>
// then one line for hits outside any function: "- (no function) hits=<n> first=0x<addr>".
// @category d2-recon

import java.io.PrintWriter;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.scalar.Scalar;

public class FindScalar extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) throw new IllegalArgumentException("usage: FindScalar.java <out-file> <value>...");
		Set<Long> wanted = new HashSet<>();
		for (int i = 1; i < args.length; i++) wanted.add(Long.decode(args[i]) & 0xFFFFFFFFL);
		TreeMap<Long, long[]> perFn = new TreeMap<>();   // entry -> {hits, firstAddr}
		long orphanHits = 0, orphanFirst = -1;
		InstructionIterator it = currentProgram.getListing().getInstructions(true);
		while (it.hasNext()) {
			Instruction ins = it.next();
			boolean hit = false;
			for (int op = 0; op < ins.getNumOperands() && !hit; op++) {
				for (Object o : ins.getOpObjects(op)) {
					if (o instanceof Scalar s && wanted.contains(s.getUnsignedValue() & 0xFFFFFFFFL)) { hit = true; break; }
				}
			}
			if (!hit) continue;
			long at = ins.getAddress().getOffset();
			Function fn = getFunctionContaining(ins.getAddress());
			if (fn == null) {
				orphanHits++;
				if (orphanFirst < 0) orphanFirst = at;
				continue;
			}
			long[] v = perFn.computeIfAbsent(fn.getEntryPoint().getOffset(), k -> new long[] { 0, at });
			v[0]++;
		}
		try (PrintWriter w = new PrintWriter(args[0])) {
			for (Map.Entry<Long, long[]> e : perFn.entrySet()) {
				Function fn = getFunctionAt(toAddr(e.getKey()));
				int callers = fn.getCallingFunctions(monitor).size();
				w.printf("0x%08X %s size=%d callers=%d hits=%d first=0x%08X%n", e.getKey(), fn.getName(),
					fn.getBody().getNumAddresses(), callers, e.getValue()[0], e.getValue()[1]);
			}
			if (orphanHits > 0) w.printf("- (no function) hits=%d first=0x%08X%n", orphanHits, orphanFirst);
		}
	}
}
