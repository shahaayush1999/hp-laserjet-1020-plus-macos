// Extracts the stock USB bulk receive callback functions used by USB2Thread.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.LinkedHashMap;
import java.util.Map;

public class MapHp1020UsbBulkCallbacks extends GhidraScript {
    private static final long[] SEEDS = {
        0x1000807cL,
        0x100080f0L,
        0x100081f4L,
        0x100087b8L,
        0x10008bacL
    };

    private static final Map<Long, String> LABELS = new LinkedHashMap<>();
    static {
        LABELS.put(0x1000807cL, "hp1020_usb_transfer_prepare_callback_candidate");
        LABELS.put(0x100080f0L, "hp1020_usb_transfer_callback_a_candidate");
        LABELS.put(0x100081f4L, "hp1020_usb_transfer_callback_b_candidate");
        LABELS.put(0x100087b8L, "hp1020_usb_bulk_rx_callback_a_candidate");
        LABELS.put(0x10008bacL, "hp1020_usb_bulk_rx_callback_b_candidate");
    }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020UsbBulkCallbacks <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "bulk-callbacks-decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        Map<Long, Function> functions = new LinkedHashMap<>();
        for (long raw : SEEDS) {
            Address seedAddr = addr(raw);
            if (currentProgram.getListing().getInstructionAt(seedAddr) == null) {
                disassemble(seedAddr);
            }
            Function fn = functionAt(raw);
            if (fn == null && currentProgram.getFunctionManager().getFunctionContaining(seedAddr) == null) {
                try {
                    fn = createFunction(seedAddr, LABELS.get(raw));
                }
                catch (Exception ignored) {
                    // Fall back to containing-function lookup below.
                }
            }
            if (fn == null) {
                fn = currentProgram.getFunctionManager().getFunctionContaining(seedAddr);
            }
            if (fn != null) {
                label(fn, LABELS.get(raw));
                functions.put(raw, fn);
            }
        }

        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "usb-bulk-callbacks.md")))) {
            out.println("# HP 1020 USB Bulk Receive Callbacks");
            out.println();
            out.println("This is a Ghidra extraction from the stock firmware. It does not contact the printer.");
            out.println();

            for (Map.Entry<Long, Function> entry : functions.entrySet()) {
                long seed = entry.getKey();
                Function fn = entry.getValue();
                DecompileResults results = decompiler.decompileFunction(fn, 30, monitor);
                String code = "/* Decompilation failed: " + results.getErrorMessage() + " */";
                if (results.decompileCompleted() && results.getDecompiledFunction() != null) {
                    code = results.getDecompiledFunction().getC();
                }

                String fileName = String.format("%08x_%s.c", seed, LABELS.get(seed));
                try (PrintWriter c = new PrintWriter(new FileWriter(new File(decompDir, fileName)))) {
                    c.print(code);
                }

                out.printf("## `%08x` `%s`%n%n", seed, LABELS.get(seed));
                out.printf("- containing function: `%s` `%s`%n", fn.getEntryPoint(), fn.getName());
                out.printf("- decompiled file: `bulk-callbacks-decompiled/%s`%n", fileName);
                out.println();
                out.println("### References From Instructions");
                writeInstructionRefs(out, fn);
                out.println();
            }
        }
        decompiler.dispose();
    }

    private void label(Function fn, String name) {
        if (name == null) {
            return;
        }
        if (!fn.getName().equals(name)) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Keep extracting even if a duplicate label exists.
            }
        }
    }

    private void writeInstructionRefs(PrintWriter out, Function fn) {
        InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
        int emitted = 0;
        while (instructions.hasNext() && emitted < 120) {
            Instruction instruction = instructions.next();
            Reference[] refs = instruction.getReferencesFrom();
            if (refs.length == 0) {
                continue;
            }
            out.printf("- `%s` `%s`", instruction.getAddress(), instruction);
            for (Reference ref : refs) {
                out.printf(" -> `%s`/%s", ref.getToAddress(), ref.getReferenceType());
            }
            out.println();
            emitted++;
        }
        if (emitted == 0) {
            out.println("- no instruction references emitted");
        }
    }

    private Function functionAt(long rawAddress) {
        return currentProgram.getFunctionManager().getFunctionAt(addr(rawAddress));
    }

    private Address addr(long rawAddress) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(rawAddress);
    }
}
