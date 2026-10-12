// Decompile every function whose entry lies in [lo, hi) to one file, for grepping.
// Usage (headless): -postScript DecompileRange.java <out-file> <lo> <hi>
// <lo>/<hi> are 0x-prefixed hex. Output format is that of Decompile.java, one block per function:
//   // <name> @ 0x00XXXXXX  (<signature>)
//   <C>
// A full Game.exe code range takes tens of minutes; run it once per session and grep the file.
// @category d2-recon

import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompileRange extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length != 3) throw new IllegalArgumentException("usage: DecompileRange.java <out-file> <lo> <hi>");
		Address lo = toAddr(Long.decode(args[1]));
		long hi = Long.decode(args[2]);
		DecompInterface ifc = new DecompInterface();
		ifc.setOptions(new DecompileOptions());
		ifc.openProgram(currentProgram);
		int n = 0;
		try (PrintWriter w = new PrintWriter(args[0])) {
			FunctionIterator it = currentProgram.getFunctionManager().getFunctions(lo, true);
			while (it.hasNext() && !monitor.isCancelled()) {
				Function fn = it.next();
				if (fn.getEntryPoint().getOffset() >= hi) break;
				DecompileResults res = ifc.decompileFunction(fn, 60, monitor);
				w.printf("// %s @ 0x%08X  (%s)%n", fn.getName(), fn.getEntryPoint().getOffset(),
					fn.getSignature().getPrototypeString(true));
				if (res.decompileCompleted()) w.println(res.getDecompiledFunction().getC());
				else w.println("// decompile failed: " + res.getErrorMessage() + "\n");
				n++;
			}
		}
		ifc.dispose();
		println("DecompileRange: " + n + " functions");
	}
}
