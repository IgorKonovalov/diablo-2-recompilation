// Arguments of every call to a function, as the decompiler sees them, plus where the return value goes.
// Usage (headless): -postScript CallArgs.java <out-file> <callee addr|name> [...]
// Output, one line per call site:
//   0x<site> in <caller>@0x<entry> | a1=<v> a2=<v> ... | ret-> <dest>[,<dest>...]
// Values: 0x<n> constant, "text" when the constant points at a C string, &0x<addr> address of a global,
// stk[<off>] address of a caller stack slot, ? anything else. ret-> lists globals the return value is
// stored to (COPY into ram, or STORE through a constant address).
// @category d2-recon

import java.io.PrintWriter;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.pcode.HighFunction;
import ghidra.program.model.pcode.PcodeOp;
import ghidra.program.model.pcode.PcodeOpAST;
import ghidra.program.model.pcode.Varnode;
import ghidra.program.model.symbol.Reference;

public class CallArgs extends GhidraScript {

	private String cstr(long off) {
		try {
			Address a = toAddr(off);
			if (!currentProgram.getMemory().contains(a)) return null;
			Data d = getDataAt(a);
			if (d != null && d.hasStringValue()) return "\"" + d.getValue() + "\"";
			StringBuilder sb = new StringBuilder();
			for (int i = 0; i < 64; i++) {
				byte b = getByte(a.add(i));
				if (b == 0) break;
				if (b < 0x20 || b > 0x7e) return null;
				sb.append((char) b);
			}
			return sb.length() >= 2 ? "\"" + sb + "\"" : null;
		} catch (Exception e) {
			return null;
		}
	}

	private String val(Varnode v, int depth) {
		if (v == null) return "?";
		if (v.isConstant()) {
			long c = v.getOffset();
			String s = c > 0x400000 ? cstr(c) : null;
			return s != null ? s : String.format("0x%X", c);
		}
		if (v.isAddress()) return String.format("[0x%08X]", v.getOffset());
		PcodeOp def = v.getDef();
		if (def == null || depth > 4) return "?";
		switch (def.getOpcode()) {
			case PcodeOp.COPY:
			case PcodeOp.CAST:
				return val(def.getInput(0), depth + 1);
			case PcodeOp.PTRSUB: {
				Varnode b = def.getInput(0), o = def.getInput(1);
				if (b.isConstant() && b.getOffset() == 0 && o.isConstant()) {
					String s = cstr(o.getOffset());
					return s != null ? s : String.format("&0x%08X", o.getOffset());
				}
				if (o.isConstant() && b.isRegister()) return String.format("stk[%d]", (int) o.getOffset());
				if (o.isConstant()) return String.format("stk[%d]", (int) o.getOffset());
				return "?";
			}
			case PcodeOp.PTRADD:
			case PcodeOp.INT_ADD: {
				Varnode b = def.getInput(0), o = def.getInput(1);
				if (b.isConstant() && o.isConstant()) return String.format("&0x%08X", b.getOffset() + o.getOffset());
				return "?";
			}
			default:
				return "?";
		}
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) throw new IllegalArgumentException("usage: CallArgs.java <out-file> <callee>...");
		DecompInterface di = new DecompInterface();
		di.openProgram(currentProgram);
		try (PrintWriter w = new PrintWriter(args[0])) {
			for (int i = 1; i < args.length; i++) {
				String t = args[i];
				Address target;
				if (t.startsWith("0x") || t.startsWith("0X")) target = toAddr(Long.decode(t));
				else {
					List<Function> fs = getGlobalFunctions(t);
					if (fs.isEmpty()) { w.println("# " + t + ": no such function"); continue; }
					target = fs.get(0).getEntryPoint();
				}
				w.printf("# calls to 0x%08X%n", target.getOffset());
				Map<Long, Function> callers = new TreeMap<>();
				Map<Long, Boolean> sites = new TreeMap<>();
				for (Reference r : getReferencesTo(target)) {
					if (!r.getReferenceType().isCall()) continue;
					Function f = getFunctionContaining(r.getFromAddress());
					if (f == null) { w.printf("0x%08X in - | (no function)%n", r.getFromAddress().getOffset()); continue; }
					callers.put(f.getEntryPoint().getOffset(), f);
					sites.put(r.getFromAddress().getOffset(), true);
				}
				for (Function f : callers.values()) {
					DecompileResults res = di.decompileFunction(f, 120, monitor);
					HighFunction hf = res.getHighFunction();
					if (hf == null) { w.printf("# %s: decompile failed%n", f.getName()); continue; }
					Map<Long, String> lines = new TreeMap<>();
					Iterator<PcodeOpAST> it = hf.getPcodeOps();
					while (it.hasNext()) {
						PcodeOpAST op = it.next();
						if (op.getOpcode() != PcodeOp.CALL) continue;
						Varnode tgt = op.getInput(0);
						if (tgt == null || !tgt.isAddress() || tgt.getOffset() != target.getOffset()) continue;
						StringBuilder sb = new StringBuilder();
						long site = op.getSeqnum().getTarget().getOffset();
						sb.append(String.format("0x%08X in %s@0x%08X |", site, f.getName(), f.getEntryPoint().getOffset()));
						for (int k = 1; k < op.getNumInputs(); k++) sb.append(String.format(" a%d=%s", k, val(op.getInput(k), 0)));
						sb.append(" | ret->");
						Varnode out = op.getOutput();
						if (out != null) {
							Iterator<PcodeOp> ds = out.getDescendants();
							while (ds.hasNext()) {
								PcodeOp d = ds.next();
								if (d.getOpcode() == PcodeOp.COPY && d.getOutput() != null && d.getOutput().isAddress())
									sb.append(String.format(" 0x%08X", d.getOutput().getOffset()));
								else if (d.getOpcode() == PcodeOp.STORE) {
									String a = val(d.getInput(1), 0);
									if (d.getInput(2) == out) sb.append(" *" + a);
								} else if (d.getOpcode() == PcodeOp.INDIRECT) {
									// ignore
								}
							}
						}
						lines.put(site, sb.toString());
						sites.remove(site);
					}
					for (String l : lines.values()) w.println(l);
				}
				for (Long s : sites.keySet()) w.printf("0x%08X | call not seen in decompiler output%n", s);
			}
		} finally {
			di.dispose();
		}
	}
}
