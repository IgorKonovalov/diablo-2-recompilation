// Enumerate the static call graph under one or more roots and list every function in it that draws
// from an RNG: an inlined LCG step (the multiplier 0x6AC690C5 as an immediate) or a call to one of
// the named RNG functions. Each RNG-bearing function is matched against a classification file
// (function entry -> seed it steps); any that has no row is reported UNCLASSIFIED.
// Usage (headless): -postScript RngCallGraph.java <out-file> <class-file|-> <root> [<root> ...]
// <root>: 0x-hex address or function name, or table@0x<addr>:<n> for a table of n code pointers
//   (each target is a root; a target with no Ghidra function is scanned as a stub, linearly up to
//   the first return, int3 or address gap, and reported as "stub 0x<addr> insns=<n> lcg=<n> calls=<n>"),
//   or stop@0x<addr> (plan 0050 P1.1): a function the walk does not descend into; each direct call to it
//   is listed as a "stop" line. <class-file>: lines "0x<entry> <seed> [note...]", '#' comments.
// Output:
//   fn 0x<entry> <name> depth=<d> via=0x<parent> [rng] [class=<seed>]
//      lcg  0x<addr> <instruction>            (one per multiplier use)
//      call 0x<site> -> <RNG fn>              (one per call to an RNG function)
//      ctx  0x<addr> <instruction>            (the 6 instructions before each lcg/call line)
//      icall 0x<site> <instruction>           (indirect calls: their targets are not followed)
//      stop 0x<site> -> <fn>                  (a direct call to a stop@ function, not followed)
//   summary: functions=<n> rng=<n> unclassified=<n> indirect=<n>
// RNG functions are leaves: the walk does not descend into them.
// @category d2-recon

import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;

public class RngCallGraph extends GhidraScript {

	static final long LCG_MUL = 0x6AC690C5L;
	// RNG_Step, RNG_Range, RNG_RangeB, RNG_RangePow2, RNG_RangePow2Plus, RNG_SeedInitOne, RNG_SeedInit
	static final long[] RNG_FNS = { 0x0045C370L, 0x0045C390L, 0x0045C3E0L, 0x00472210L, 0x00472240L,
		0x00650E30L, 0x00650E40L };

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 3)
			throw new IllegalArgumentException("usage: RngCallGraph.java <out-file> <class-file|-> <root>...");
		Map<Long, String> cls = new HashMap<>();
		if (!args[1].equals("-")) {
			for (String line : Files.readAllLines(Path.of(args[1]))) {
				line = line.trim();
				if (line.isEmpty() || line.startsWith("#")) continue;
				String[] f = line.split("\\s+", 3);
				cls.put(Long.decode(f[0]), f.length > 1 ? f[1] : "?");
			}
		}
		Set<Long> rngFns = new TreeSet<>();
		for (long a : RNG_FNS) rngFns.add(a);

		// BFS over direct calls
		LinkedHashMap<Long, long[]> seen = new LinkedHashMap<>(); // entry -> {depth, parent}
		ArrayDeque<Function> q = new ArrayDeque<>();
		List<String> roots = new ArrayList<>();
		List<String> stubLines = new ArrayList<>();
		Set<Long> stopFns = new TreeSet<>();
		for (int i = 2; i < args.length; i++) {
			if (args[i].startsWith("stop@")) { stopFns.add(Long.decode(args[i].substring(5))); continue; }
			if (!args[i].startsWith("table@")) { roots.add(args[i]); continue; }
			String[] tp = args[i].substring(6).split(":");
			Address tab = toAddr(Long.decode(tp[0]));
			int n = Integer.parseInt(tp[1]);
			for (int k = 0; k < n; k++) {
				long tgt = getInt(tab.add(4L * k)) & 0xFFFFFFFFL;
				if (getFunctionAt(toAddr(tgt)) != null) { roots.add(String.format("0x%08X", tgt)); continue; }
				int ni = 0, nl = 0, nc = 0;
				Instruction ins = getInstructionAt(toAddr(tgt));
				if (ins == null) ins = disassembleStub(tgt);
				for (Instruction prev = null; ins != null && ni < 64; prev = ins, ins = ins.getNext(), ni++) {
					if (ins.getMnemonicString().equalsIgnoreCase("INT3")) break;
					if (prev != null && !ins.getAddress().equals(prev.getAddress().add(prev.getLength()))) break;
					for (int op = 0; op < ins.getNumOperands(); op++)
						for (Object o : ins.getOpObjects(op))
							if (o instanceof Scalar sc && (sc.getUnsignedValue() & 0xFFFFFFFFL) == LCG_MUL) nl++;
					if (ins.getFlowType().isCall()) nc++;
					if (ins.getFlowType().isTerminal()) { ni++; break; }
				}
				stubLines.add(String.format("stub 0x%08X table=0x%08X[%d] insns=%d lcg=%d calls=%d", tgt,
					tab.getOffset(), k, ni, nl, nc));
			}
		}
		for (String r : roots) {
			Function f = resolve(r);
			if (f == null) throw new IllegalArgumentException("no function for root " + r);
			long e = f.getEntryPoint().getOffset();
			if (!seen.containsKey(e)) { seen.put(e, new long[] { 0, -1 }); q.add(f); }
		}
		Map<Long, Function> fnOf = new HashMap<>();
		Map<Long, List<String>> lines = new HashMap<>();
		Map<Long, Boolean> isRng = new HashMap<>();
		int nIndirect = 0;
		while (!q.isEmpty()) {
			Function f = q.poll();
			long e = f.getEntryPoint().getOffset();
			long depth = seen.get(e)[0];
			fnOf.put(e, f);
			List<String> out = new ArrayList<>();
			boolean rng = false;
			InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
			while (it.hasNext()) {
				Instruction ins = it.next();
				boolean lcg = false;
				for (int op = 0; op < ins.getNumOperands() && !lcg; op++)
					for (Object o : ins.getOpObjects(op))
						if (o instanceof Scalar s && (s.getUnsignedValue() & 0xFFFFFFFFL) == LCG_MUL) { lcg = true; break; }
				if (lcg) {
					rng = true;
					ctx(out, ins);
					out.add(String.format("   lcg  0x%08X %s", ins.getAddress().getOffset(), ins));
				}
				if (!ins.getFlowType().isCall()) continue;
				boolean direct = false;
				for (Reference r : ins.getReferencesFrom()) {
					if (!r.getReferenceType().isCall()) continue;
					Function c = getFunctionAt(r.getToAddress());
					if (c == null) continue;
					direct = true;
					long ce = c.getEntryPoint().getOffset();
					if (rngFns.contains(ce)) {
						rng = true;
						ctx(out, ins);
						out.add(String.format("   call 0x%08X -> %s", ins.getAddress().getOffset(), c.getName()));
					} else if (stopFns.contains(ce)) {
						out.add(String.format("   stop 0x%08X -> %s", ins.getAddress().getOffset(), c.getName()));
					} else if (!seen.containsKey(ce)) {
						seen.put(ce, new long[] { depth + 1, e });
						q.add(c);
					}
				}
				if (!direct) {
					nIndirect++;
					out.add(String.format("   icall 0x%08X %s", ins.getAddress().getOffset(), ins));
				}
			}
			lines.put(e, out);
			isRng.put(e, rng);
		}
		int nRng = 0, nUncl = 0;
		try (PrintWriter w = new PrintWriter(args[0])) {
			for (String l : stubLines) w.println(l);
			for (Map.Entry<Long, long[]> en : seen.entrySet()) {
				long e = en.getKey();
				Function f = fnOf.get(e);
				boolean rng = isRng.get(e);
				String c = cls.get(e);
				if (rng) { nRng++; if (c == null) nUncl++; }
				w.printf("fn 0x%08X %s depth=%d via=%s%s%s%n", e, f.getName(), en.getValue()[0],
					en.getValue()[1] < 0 ? "root" : String.format("0x%08X", en.getValue()[1]),
					rng ? " rng" : "", rng ? (c == null ? " UNCLASSIFIED" : " class=" + c) : "");
				for (String l : lines.get(e)) w.println(l);
			}
			w.printf("summary: functions=%d rng=%d unclassified=%d indirect=%d%n", seen.size(), nRng, nUncl, nIndirect);
		}
	}

	private Instruction disassembleStub(long at) {
		disassemble(toAddr(at));   // in-memory only: the project is opened read-only
		return getInstructionAt(toAddr(at));
	}

	private void ctx(List<String> out, Instruction at) {
		ArrayDeque<String> buf = new ArrayDeque<>();
		Instruction p = at.getPrevious();
		for (int i = 0; i < 6 && p != null; i++, p = p.getPrevious())
			buf.addFirst(String.format("   ctx  0x%08X %s", p.getAddress().getOffset(), p));
		out.addAll(buf);
	}

	private Function resolve(String t) {
		if (t.startsWith("0x") || t.startsWith("0X")) {
			Address a = toAddr(Long.decode(t));
			Function f = getFunctionAt(a);
			return f != null ? f : getFunctionContaining(a);
		}
		List<Function> fs = getGlobalFunctions(t);
		return fs.isEmpty() ? null : fs.get(0);
	}
}
