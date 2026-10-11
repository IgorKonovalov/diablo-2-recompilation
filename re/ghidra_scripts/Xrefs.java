// Callers and callees of a function, or references to any address.
// Usage (headless): -postScript Xrefs.java <out-file> <addr|name> [...]
// Output lines:
//   to   0x<from> <ref-type> in <containing function>@0x<entry>
//   call 0x<callee entry> <callee name>        (only when the target is a function)
// @category d2-recon

import java.io.PrintWriter;
import java.util.List;
import java.util.TreeSet;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class Xrefs extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) throw new IllegalArgumentException("usage: Xrefs.java <out-file> <addr|name>...");
		try (PrintWriter w = new PrintWriter(args[0])) {
			for (int i = 1; i < args.length; i++) {
				String t = args[i];
				Address a;
				if (t.startsWith("0x") || t.startsWith("0X")) a = toAddr(Long.decode(t));
				else {
					List<Function> fs = getGlobalFunctions(t);
					if (fs.isEmpty()) { w.println("# " + t + ": no such function"); continue; }
					a = fs.get(0).getEntryPoint();
				}
				Function self = getFunctionAt(a);
				w.printf("# %s @ 0x%08X%n", self != null ? self.getName() : t, a.getOffset());
				for (Reference r : getReferencesTo(a)) {
					Function in = getFunctionContaining(r.getFromAddress());
					w.printf("to   0x%08X %s in %s%n", r.getFromAddress().getOffset(), r.getReferenceType(),
						in == null ? "-" : String.format("%s@0x%08X", in.getName(), in.getEntryPoint().getOffset()));
				}
				if (self != null) {
					TreeSet<String> callees = new TreeSet<>();
					for (Function c : self.getCalledFunctions(monitor))
						callees.add(String.format("call 0x%08X %s", c.getEntryPoint().getOffset(), c.getName()));
					for (String c : callees) w.println(c);
				}
			}
		}
	}
}
