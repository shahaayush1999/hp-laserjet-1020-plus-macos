// Searches for queue table initialization evidence around runtime table 0x1002c918.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class MapHp1020QueueTableInit extends GhidraScript {
    private static final long QUEUE_TABLE_BASE = 0x1002c918L;
    private static final long QUEUE_TABLE_END = 0x1002ca40L;
    private static final long QUEUE_CREATE = 0x10017f18L;
    private static final long QUEUE_CREATE_CORE = 0x100199a4L;
    private static final long INDEXED_SEND = 0x10013668L;

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020QueueTableInit <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();
        List<FunctionHit> hits = scanFunctions();
        decompileHitFunctions(hits, decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "queue-table-init.md")))) {
            writeReport(out, hits);
        }
    }

    private void applyLabels() {
        label(INDEXED_SEND, "hp1020_queue_send_indexed_candidate");
        label(QUEUE_CREATE, "threadx_queue_create_candidate");
        label(QUEUE_CREATE_CORE, "threadx_queue_create_core_candidate");
        label(0x10013658L, "hp1020_queue_send_candidate");
        label(0x100180dcL, "threadx_queue_send_candidate");
        label(0x1001809cL, "threadx_queue_receive_wait_candidate");
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAtOrCreate(rawAddress, name);
        if (fn == null) {
            return;
        }
        labels.put(fn, name);
        if (fn.getName().startsWith("FUN_") || fn.getName().startsWith("threadx_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Local label map still works.
            }
        }
    }

    private List<FunctionHit> scanFunctions() {
        List<FunctionHit> hits = new ArrayList<>();
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function fn = functions.next();
            FunctionHit hit = scan(fn);
            if (!hit.lines.isEmpty() || !hit.calls.isEmpty()) {
                hits.add(hit);
            }
        }
        hits.sort(Comparator.comparing(h -> h.function.getEntryPoint().getOffset()));
        return hits;
    }

    private FunctionHit scan(Function fn) {
        FunctionHit hit = new FunctionHit(fn);
        InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
        while (instructions.hasNext()) {
            Instruction instruction = instructions.next();
            for (Reference ref : instruction.getReferencesFrom()) {
                Address to = ref.getToAddress();
                if (to == null) {
                    continue;
                }
                Function callee = currentProgram.getFunctionManager().getFunctionAt(to);
                if (callee != null && ref.getReferenceType().isCall()) {
                    long target = callee.getEntryPoint().getOffset();
                    if (target == QUEUE_CREATE || target == QUEUE_CREATE_CORE || target == INDEXED_SEND) {
                        hit.calls.add(String.format("`%s` calls `0x%08x` `%s`", instruction.getAddress(), target, displayName(callee)));
                    }
                }
                captureValue(hit, instruction, to.getOffset(), "ref");
            }
            for (int i = 0; i < instruction.getNumOperands(); i++) {
                for (Object obj : instruction.getOpObjects(i)) {
                    if (obj instanceof Scalar) {
                        captureValue(hit, instruction, ((Scalar) obj).getUnsignedValue(), "scalar");
                    }
                }
            }
        }
        return hit;
    }

    private void captureValue(FunctionHit hit, Instruction instruction, long value, String source) {
        if (value == 0x100066f0L || value == QUEUE_TABLE_BASE || (value >= QUEUE_TABLE_BASE && value < QUEUE_TABLE_END)) {
            hit.lines.add(String.format("`%s` `%s` `%s` -> %s `0x%08x`",
                instruction.getAddress(), instruction.getMnemonicString(), compact(instruction.toString()), source, value));
        }
    }

    private void writeReport(PrintWriter out, List<FunctionHit> hits) throws Exception {
        out.println("# HP 1020 Queue Table Initializer Search");
        out.println();
        out.printf("- queue table base: `0x%08x`%n", QUEUE_TABLE_BASE);
        out.printf("- scanned table window: `0x%08x` through `0x%08x`%n", QUEUE_TABLE_BASE, QUEUE_TABLE_END);
        out.println();
        out.println("## Hits");
        out.println();
        out.println("| Function | Calls | Table references |");
        out.println("|---:|---|---|");
        for (FunctionHit hit : hits) {
            out.printf("| `0x%08x` `%s` | %s | %s |%n",
                hit.function.getEntryPoint().getOffset(),
                displayName(hit.function),
                compact(String.join("<br>", first(hit.calls, 8))),
                compact(String.join("<br>", first(hit.lines, 12))));
        }
        out.println();
        out.println("## Interpretation");
        out.println();
        out.println("- A direct constant reference to `0x1002c918` is expected in `hp1020_queue_send_indexed_candidate` because that function indexes the queue table for sends.");
        out.println("- If no other direct hit appears, the table is likely populated through a pointer copied from descriptor data or through a boot/runtime descriptor loop that does not embed `0x1002c918` as an immediate in each write.");
        out.println("- The next fallback is to map descriptor initialization routines that call `threadx_queue_create_candidate` and then assign queue objects into the table indirectly.");
    }

    private void decompileHitFunctions(List<FunctionHit> hits, File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        int emitted = 0;
        for (FunctionHit hit : hits) {
            if (emitted >= 60) {
                break;
            }
            Function fn = hit.function;
            DecompileResults results = decompiler.decompileFunction(fn, 30, monitor);
            File outFile = new File(decompDir, fn.getEntryPoint() + "_" + displayName(fn) + ".c");
            try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
                out.println("/* Function: " + fn.getEntryPoint() + " " + displayName(fn) + " */");
                out.println();
                if (results.decompileCompleted() && results.getDecompiledFunction() != null) {
                    out.println(results.getDecompiledFunction().getC());
                }
                else {
                    out.println("/* Decompilation failed: " + results.getErrorMessage() + " */");
                }
            }
            emitted++;
        }
        decompiler.dispose();
    }

    private List<String> first(Set<String> values, int limit) {
        List<String> result = new ArrayList<>();
        int count = 0;
        for (String value : values) {
            if (count++ >= limit) {
                break;
            }
            result.add(value);
        }
        return result;
    }

    private Function functionAtOrCreate(long rawAddress, String fallbackName) {
        Address address = addr(rawAddress);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn != null) {
            return fn;
        }
        fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        if (fn != null) {
            return fn;
        }
        MemoryBlock block = currentProgram.getMemory().getBlock(address);
        if (block == null || !block.isExecute()) {
            return null;
        }
        try {
            createFunction(address, fallbackName);
            return currentProgram.getFunctionManager().getFunctionAt(address);
        }
        catch (Exception ignored) {
            return currentProgram.getFunctionManager().getFunctionAt(address);
        }
    }

    private Address addr(long value) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(value);
    }

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
    }

    private String compact(String value) {
        String s = value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").trim();
        return s.length() > 240 ? s.substring(0, 237) + "..." : s;
    }

    private static class FunctionHit {
        final Function function;
        final Set<String> lines = new LinkedHashSet<>();
        final Set<String> calls = new LinkedHashSet<>();

        FunctionHit(Function function) {
            this.function = function;
        }
    }
}

