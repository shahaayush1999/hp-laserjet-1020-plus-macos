// Finds functions that reference the static descriptor regions used for task/queue setup.

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

public class MapHp1020DescriptorRefs extends GhidraScript {
    private static final long DESCRIPTOR_START = 0x10005f00L;
    private static final long DESCRIPTOR_END = 0x10006b80L;

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020DescriptorRefs <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();
        List<FunctionHit> hits = scanFunctions();
        decompileHitFunctions(hits, decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "descriptor-refs.md")))) {
            writeReport(out, hits);
        }
    }

    private void applyLabels() {
        label(0x10008ff0L, "hp1020_usb2_thread");
        label(0x10009934L, "hp1020_usb2_idle_thread");
        label(0x1000e414L, "hp1020_job_mgr_thread_candidate");
        label(0x1000f324L, "hp1020_print_mgr_thread_candidate");
        label(0x10010590L, "hp1020_status_mgr_thread_candidate");
        label(0x10010b0cL, "hp1020_delay_mgr_receive_thread_candidate");
        label(0x10013c18L, "hp1020_video_thread_candidate");
        label(0x100163b0L, "hp1020_engine_thread_candidate");
        label(0x10018274L, "threadx_thread_create_candidate");
        label(0x10017f18L, "threadx_queue_create_candidate");
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAtOrCreate(rawAddress, name);
        if (fn == null) {
            return;
        }
        labels.put(fn, name);
        if (fn.getName().startsWith("FUN_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Local label is enough.
            }
        }
    }

    private List<FunctionHit> scanFunctions() {
        List<FunctionHit> hits = new ArrayList<>();
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function fn = functions.next();
            FunctionHit hit = scan(fn);
            if (!hit.refs.isEmpty()) {
                hits.add(hit);
            }
        }
        hits.sort(Comparator
            .comparing((FunctionHit h) -> -h.refs.size())
            .thenComparing(h -> h.function.getEntryPoint().getOffset()));
        return hits;
    }

    private FunctionHit scan(Function fn) {
        FunctionHit hit = new FunctionHit(fn);
        InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
        while (instructions.hasNext()) {
            Instruction instruction = instructions.next();
            for (Reference ref : instruction.getReferencesFrom()) {
                if (ref.getToAddress() != null) {
                    capture(hit, instruction, ref.getToAddress().getOffset(), "ref");
                }
            }
            for (int i = 0; i < instruction.getNumOperands(); i++) {
                for (Object obj : instruction.getOpObjects(i)) {
                    if (obj instanceof Scalar) {
                        capture(hit, instruction, ((Scalar) obj).getUnsignedValue(), "scalar");
                    }
                }
            }
        }
        return hit;
    }

    private void capture(FunctionHit hit, Instruction instruction, long value, String source) {
        if (value >= DESCRIPTOR_START && value < DESCRIPTOR_END) {
            hit.refs.add(String.format("`%s` `%s` `%s` -> %s `0x%08x`",
                instruction.getAddress(), instruction.getMnemonicString(), compact(instruction.toString()), source, value));
        }
    }

    private void writeReport(PrintWriter out, List<FunctionHit> hits) {
        out.println("# HP 1020 Descriptor Reference Map");
        out.println();
        out.printf("- descriptor window: `0x%08x` through `0x%08x`%n", DESCRIPTOR_START, DESCRIPTOR_END);
        out.println();
        out.println("## Function Hits");
        out.println();
        out.println("| Function | Hit count | References |");
        out.println("|---:|---:|---|");
        for (FunctionHit hit : hits) {
            out.printf("| `0x%08x` `%s` | `%d` | %s |%n",
                hit.function.getEntryPoint().getOffset(),
                displayName(hit.function),
                hit.refs.size(),
                compact(String.join("<br>", first(hit.refs, 12))));
        }
        out.println();
        out.println("## Interpretation");
        out.println();
        out.println("- High-hit functions are descriptor consumers or descriptor-heavy task bodies.");
        out.println("- This scan is meant to locate generic descriptor loops that may indirectly create queues/threads.");
        out.println("- If task bodies dominate hits, queue/table initialization may happen before normal firmware execution or through boot/runtime code not obvious from direct descriptor references.");
    }

    private void decompileHitFunctions(List<FunctionHit> hits, File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        int emitted = 0;
        for (FunctionHit hit : hits) {
            if (emitted >= 50) {
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
        final Set<String> refs = new LinkedHashSet<>();

        FunctionHit(Function function) {
            this.function = function;
        }
    }
}

