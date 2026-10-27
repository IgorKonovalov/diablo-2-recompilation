// Every way the image could reach an address: Ghidra references of any type, raw pointer bytes, immediate
// operands, relative branches in raw bytes, export entry points and fall-through from the previous instruction.
// Usage (headless): -postScript FindPointer.java <out-file> <addr> [<addr> ...]
// Per target, output lines (plan 0038 backlog entry r1h, the host-callback setter):
//   # 0x<target> <function name or "-"> rva=0x<rva>
//   ref    0x<from> <ref-type> <op-index> in <function>      every Reference to the target (getReferencesTo)
//   ptr    0x<at> <block> va|rva <function-or-"-">          4 LE bytes = VA or RVA, any alignment, every initialized block
//   scalar 0x<at> <function>                                  an instruction operand scalar = VA or RVA
//   rel    0x<at> <block> E8|E9|0F8x|EB|7x <function-or-"-">  raw bytes of a relative call/jump whose target is the address
//   entry  <name>                                             the address is an external entry point (export/entry)
//   fall   0x<prev> <instruction>                             the instruction before the target can fall through into it
//   counts ref=<n> ptr=<n> scalar=<n> rel=<n> entry=<n> fall=<n>
// @category d2-recon

import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;

public class FindPointer extends GhidraScript {

	private String fn(Address a) {
		Function f = getFunctionContaining(a);
		return f == null ? "-" : String.format("%s@0x%08X", f.getName(), f.getEntryPoint().getOffset());
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) throw new IllegalArgumentException("usage: FindPointer.java <out-file> <addr>...");
		long base = currentProgram.getImageBase().getOffset();
		try (PrintWriter w = new PrintWriter(args[0])) {
			for (int i = 1; i < args.length; i++) {
				long va = Long.decode(args[i]) & 0xFFFFFFFFL;
				long rva = va - base;
				Address t = toAddr(va);
				Function self = getFunctionAt(t);
				w.printf("# 0x%08X %s rva=0x%08X%n", va, self == null ? "-" : self.getName(), rva);
				int nRef = 0, nPtr = 0, nScalar = 0, nRel = 0, nEntry = 0, nFall = 0;
				for (Reference r : getReferencesTo(t)) {
					w.printf("ref    0x%08X %s op=%d in %s%n", r.getFromAddress().getOffset(), r.getReferenceType(),
						r.getOperandIndex(), fn(r.getFromAddress()));
					nRef++;
				}
				for (MemoryBlock b : currentProgram.getMemory().getBlocks()) {
					if (!b.isInitialized()) continue;
					long start = b.getStart().getOffset();
					int size = (int) b.getSize();
					byte[] bytes = new byte[size];
					b.getBytes(b.getStart(), bytes);
					for (int k = 0; k + 4 <= size; k++) {
						long v = (bytes[k] & 0xFFL) | (bytes[k + 1] & 0xFFL) << 8 | (bytes[k + 2] & 0xFFL) << 16
							| (bytes[k + 3] & 0xFFL) << 24;
						long at = start + k;
						if (v == va || v == rva) {
							w.printf("ptr    0x%08X %s %s %s%n", at, b.getName(), v == va ? "va" : "rva", fn(toAddr(at)));
							nPtr++;
						}
						if (!b.isExecute() || k + 5 > size) continue;
						int op = bytes[k] & 0xFF;
						long rel32 = (bytes[k + 1] & 0xFFL) | (bytes[k + 2] & 0xFFL) << 8 | (bytes[k + 3] & 0xFFL) << 16
							| (bytes[k + 4] & 0xFFL) << 24;
						if ((op == 0xE8 || op == 0xE9) && ((at + 5 + (int) rel32) & 0xFFFFFFFFL) == va) {
							w.printf("rel    0x%08X %s %02X %s%n", at, b.getName(), op, fn(toAddr(at)));
							nRel++;
						}
						if (op == 0x0F && k + 6 <= size && (bytes[k + 1] & 0xF0) == 0x80) {
							long r2 = (bytes[k + 2] & 0xFFL) | (bytes[k + 3] & 0xFFL) << 8 | (bytes[k + 4] & 0xFFL) << 16
								| (bytes[k + 5] & 0xFFL) << 24;
							if (((at + 6 + (int) r2) & 0xFFFFFFFFL) == va) {
								w.printf("rel    0x%08X %s 0F%02X %s%n", at, b.getName(), bytes[k + 1] & 0xFF, fn(toAddr(at)));
								nRel++;
							}
						}
						if ((op == 0xEB || (op & 0xF0) == 0x70) && ((at + 2 + bytes[k + 1]) & 0xFFFFFFFFL) == va) {
							w.printf("rel    0x%08X %s %02X %s%n", at, b.getName(), op, fn(toAddr(at)));
							nRel++;
						}
					}
				}
				InstructionIterator it = currentProgram.getListing().getInstructions(true);
				while (it.hasNext()) {
					Instruction ins = it.next();
					boolean hit = false;
					for (int op = 0; op < ins.getNumOperands() && !hit; op++)
						for (Object o : ins.getOpObjects(op))
							if (o instanceof Scalar s && ((s.getUnsignedValue() & 0xFFFFFFFFL) == va
								|| (s.getUnsignedValue() & 0xFFFFFFFFL) == rva)) { hit = true; break; }
					if (hit) {
						w.printf("scalar 0x%08X %s%n", ins.getAddress().getOffset(), fn(ins.getAddress()));
						nScalar++;
					}
				}
				AddressIterator ei = currentProgram.getSymbolTable().getExternalEntryPointIterator();
				while (ei.hasNext()) {
					Address e = ei.next();
					if (e.equals(t)) {
						w.printf("entry  %s%n", getSymbolAt(e) == null ? "-" : getSymbolAt(e).getName());
						nEntry++;
					}
				}
				Instruction prev = getInstructionBefore(t);
				if (prev != null && prev.getMaxAddress().next().equals(t) && prev.getFlowType().isFallthrough()) {
					w.printf("fall   0x%08X %s%n", prev.getAddress().getOffset(), prev);
					nFall++;
				}
				w.printf("counts ref=%d ptr=%d scalar=%d rel=%d entry=%d fall=%d%n", nRef, nPtr, nScalar, nRel, nEntry,
					nFall);
			}
		}
	}
}
