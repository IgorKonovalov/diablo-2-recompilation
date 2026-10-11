// Decompile functions to C.
// Usage (headless): -postScript Decompile.java <out-file> <addr|name> [<addr|name> ...]
// <addr> is 0x-prefixed hex (any address inside the function works). <name> is a function name.
// Output goes to <out-file> (tools/ghidra.sh prints it), one block per target:
//   // <name> @ 0x00XXXXXX  (<signature>)
//   <C>
// @category d2-recon

import java.io.PrintWriter;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;

public class Decompile extends GhidraScript {

	Function resolve(String t) {
		if (t.startsWith("0x") || t.startsWith("0X")) return getFunctionContaining(toAddr(Long.decode(t)));
		List<Function> fs = getGlobalFunctions(t);
		return fs.isEmpty() ? null : fs.get(0);
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) throw new IllegalArgumentException("usage: Decompile.java <out-file> <addr|name>...");
		DecompInterface ifc = new DecompInterface();
		ifc.setOptions(new DecompileOptions());
		ifc.openProgram(currentProgram);
		try (PrintWriter w = new PrintWriter(args[0])) {
			for (int i = 1; i < args.length; i++) {
				Function fn = resolve(args[i]);
				if (fn == null) {
					w.println("// " + args[i] + ": no function there\n");
					continue;
				}
				DecompileResults res = ifc.decompileFunction(fn, 120, monitor);
				w.printf("// %s @ 0x%08X  (%s)%n", fn.getName(), fn.getEntryPoint().getOffset(),
					fn.getSignature().getPrototypeString(true));
				if (res.decompileCompleted()) w.println(res.getDecompiledFunction().getC());
				else w.println("// decompile failed: " + res.getErrorMessage() + "\n");
			}
		}
		ifc.dispose();
	}
}
