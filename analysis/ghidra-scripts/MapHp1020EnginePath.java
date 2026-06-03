// Maps the HP 1020 print engine/video dispatch path and hardware touch points.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Queue;
import java.util.Set;

public class MapHp1020EnginePath extends GhidraScript {
    private static final long[] SEED_ADDRESSES = {
        0x1000f324L,
        0x10013c18L,
        0x10014910L,
        0x10015214L,
        0x10015438L,
        0x10015458L,
        0x10015df8L,
        0x10016024L,
        0x100160a8L,
        0x10016164L,
        0x1001635cL,
        0x100163b0L,
        0x100165a4L
    };

    private static final long[] TABLE_WINDOWS = {
        0x100048f0L,
        0x100056f0L,
        0x10006784L,
        0x10006920L,
        0x100069b4L,
        0x100069f0L
    };

    private final Map<Function, String> labels = new LinkedHashMap<>();
    private final Map<Function, FunctionRecord> records = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020EnginePath <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "engine-decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();

        Set<Function> seeds = seedFunctions();
        Set<Function> neighborhood = expand(seeds, 2);
        for (Function fn : neighborhood) {
            records.put(fn, scan(fn));
        }
        decompile(neighborhood, decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "engine-path.md")))) {
            writeReport(out, seeds, neighborhood);
        }
    }

    private void applyLabels() {
        label(0x1000f324L, "hp1020_print_mgr_thread_candidate");
        label(0x10011258L, "hp1020_register_event_handler_candidate");
        label(0x1001214cL, "hp1020_task_ready_or_init_candidate");
        label(0x10012184L, "hp1020_task_ready_done_candidate");
        label(0x10013620L, "hp1020_send_or_raise_engine_msg_candidate");
        label(0x10013658L, "hp1020_queue_send_candidate");
        label(0x10013c18L, "hp1020_video_thread_candidate");
        label(0x10014910L, "hp1020_video_prepare_page_candidate");
        label(0x10015214L, "hp1020_video_render_or_dma_candidate");
        label(0x10015438L, "hp1020_video_alt_render_candidate");
        label(0x10015458L, "hp1020_video_reset_or_flush_candidate");
        label(0x10015df8L, "hp1020_engine_status_poll_candidate");
        label(0x10016024L, "hp1020_engine_init_step_candidate");
        label(0x100160a8L, "hp1020_engine_preflight_candidate");
        label(0x10016164L, "hp1020_engine_message_dispatch_candidate");
        label(0x1001635cL, "hp1020_engine_delay_thread_candidate");
        label(0x100163b0L, "hp1020_engine_thread_candidate");
        label(0x100165a4L, "hp1020_engine_register_handlers_candidate");
        label(0x1001766cL, "threadx_sleep_candidate");
        label(0x1001809cL, "threadx_queue_receive_wait_candidate");
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAtOrCreate(rawAddress, name);
        if (fn == null) {
            return;
        }
        labels.put(fn, name);
        if (fn.getName().startsWith("FUN_") || fn.getName().startsWith("hp1020_task_entry_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Local labels are enough for generated reports.
            }
        }
    }

    private Set<Function> seedFunctions() {
        Set<Function> result = new LinkedHashSet<>();
        for (long raw : SEED_ADDRESSES) {
            Function fn = functionAtOrCreate(raw, "hp1020_engine_seed_" + Long.toHexString(raw));
            if (fn != null) {
                result.add(fn);
            }
        }
        return result;
    }

    private Set<Function> expand(Set<Function> seeds, int depth) {
        Set<Function> seen = new LinkedHashSet<>(seeds);
        Queue<FnDepth> queue = new ArrayDeque<>();
        for (Function fn : seeds) {
            queue.add(new FnDepth(fn, 0));
        }
        while (!queue.isEmpty()) {
            FnDepth current = queue.remove();
            if (current.depth >= depth) {
                continue;
            }
            for (Function next : neighbors(current.fn)) {
                if (seen.add(next)) {
                    queue.add(new FnDepth(next, current.depth + 1));
                }
            }
        }
        return seen;
    }

    private Set<Function> neighbors(Function fn) {
        Set<Function> result = new LinkedHashSet<>();
        InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
        while (instructions.hasNext()) {
            Instruction instruction = instructions.next();
            for (Reference ref : instruction.getReferencesFrom()) {
                if (!ref.getReferenceType().isCall()) {
                    continue;
                }
                Function target = currentProgram.getFunctionManager().getFunctionAt(ref.getToAddress());
                if (target == null) {
                    target = currentProgram.getFunctionManager().getFunctionContaining(ref.getToAddress());
                }
                if (target != null && !target.equals(fn)) {
                    result.add(target);
                }
            }
        }
        for (Reference ref : getReferencesTo(fn.getEntryPoint())) {
            if (!ref.getReferenceType().isCall()) {
                continue;
            }
            Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
            if (caller != null && !caller.equals(fn)) {
                result.add(caller);
            }
        }
        return result;
    }

    private FunctionRecord scan(Function fn) {
        FunctionRecord record = new FunctionRecord(fn);
        AddressSetView body = fn.getBody();
        record.size = body.getNumAddresses();
        InstructionIterator instructions = currentProgram.getListing().getInstructions(body, true);
        while (instructions.hasNext()) {
            Instruction instruction = instructions.next();
            for (Reference ref : instruction.getReferencesFrom()) {
                Address to = ref.getToAddress();
                if (to == null) {
                    continue;
                }
                Function callee = currentProgram.getFunctionManager().getFunctionAt(to);
                if (callee != null && ref.getReferenceType().isCall()) {
                    record.calls.add(callee.getEntryPoint() + " " + displayName(callee));
                }
                captureDataReference(record, to);
            }
            for (int i = 0; i < instruction.getNumOperands(); i++) {
                for (Object obj : instruction.getOpObjects(i)) {
                    if (obj instanceof ghidra.program.model.scalar.Scalar) {
                        classifyValue(record, ((ghidra.program.model.scalar.Scalar) obj).getUnsignedValue());
                    }
                }
            }
        }
        for (Reference ref : getReferencesTo(fn.getEntryPoint())) {
            if (ref.getReferenceType().isCall()) {
                Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                if (caller != null) {
                    record.callers.add(caller.getEntryPoint() + " " + displayName(caller));
                }
            }
        }
        return record;
    }

    private void captureDataReference(FunctionRecord record, Address to) {
        Data data = currentProgram.getListing().getDataAt(to);
        if (data != null) {
            StringDataInstance s = StringDataInstance.getStringDataInstance(data);
            if (s != null && s.getStringValue() != null) {
                record.strings.add(compact(s.getStringValue()));
            }
        }
        classifyValue(record, to.getOffset());
        try {
            MemoryBlock block = currentProgram.getMemory().getBlock(to);
            if (block != null && block.isInitialized() && block.isRead()) {
                long literal = Integer.toUnsignedLong(currentProgram.getMemory().getInt(to));
                classifyValue(record, literal);
            }
        }
        catch (Exception ignored) {
            // Many references are not 32-bit literal slots.
        }
    }

    private void classifyValue(FunctionRecord record, long value) {
        if (isMmio(value)) {
            record.mmioRefs.add(String.format("0x%08x", value));
        }
        if (value >= 0x90000000L && value < 0x90100000L) {
            record.sramRefs.add(String.format("0x%08x", value));
        }
    }

    private boolean isMmio(long value) {
        return value >= 0xb0000000L && value < 0xb4000000L;
    }

    private void decompile(Set<Function> functions, File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        List<Function> sorted = new ArrayList<>(functions);
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        int emitted = 0;
        for (Function fn : sorted) {
            if (emitted >= 100) {
                break;
            }
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

    private void writeReport(PrintWriter out, Set<Function> seeds, Set<Function> neighborhood) throws Exception {
        out.println("# HP 1020 Engine And Video Path Map");
        out.println();
        out.println("This maps the queue-driven print-engine/video path starting from the task descriptors.");
        out.println();
        out.printf("- Seed functions: `%d`%n", seeds.size());
        out.printf("- Neighborhood through call depth 2: `%d`%n", neighborhood.size());
        out.println();

        out.println("## Seed Functions");
        out.println();
        for (Function fn : sortFunctions(seeds)) {
            out.printf("- `%s` `%s`%n", fn.getEntryPoint(), displayName(fn));
        }
        out.println();

        out.println("## Descriptor And Switch Table Windows");
        out.println();
        for (long raw : TABLE_WINDOWS) {
            writeWindow(out, raw, 24);
        }

        out.println("## Function Neighborhood");
        out.println();
        List<FunctionRecord> sorted = new ArrayList<>(records.values());
        sorted.sort(Comparator
            .comparing((FunctionRecord r) -> !labels.containsKey(r.function))
            .thenComparing((FunctionRecord r) -> -r.size)
            .thenComparing(r -> r.function.getEntryPoint().toString()));
        for (FunctionRecord record : sorted) {
            out.printf("### `%s` `%s`%n%n", record.function.getEntryPoint(), displayName(record.function));
            out.printf("- size: `%d`%n", record.size);
            out.printf("- callers: `%d`; calls: `%d`%n", record.callers.size(), record.calls.size());
            if (!record.calls.isEmpty()) {
                out.printf("- calls: `%s`%n", compact(String.join("`, `", first(record.calls, 10))));
            }
            if (!record.strings.isEmpty()) {
                out.printf("- strings: `%s`%n", compact(String.join("`, `", first(record.strings, 10))));
            }
            if (!record.mmioRefs.isEmpty()) {
                out.printf("- MMIO refs: `%s`%n", compact(String.join("`, `", first(record.mmioRefs, 14))));
            }
            if (!record.sramRefs.isEmpty()) {
                out.printf("- SRAM refs: `%s`%n", compact(String.join("`, `", first(record.sramRefs, 14))));
            }
            out.println();
        }

        out.println("## Interpretation");
        out.println();
        out.println("- `hp1020_engine_thread_candidate` is the main engine task entry and receives engine queue messages.");
        out.println("- `hp1020_engine_message_dispatch_candidate` is the next key dispatch function to understand.");
        out.println("- `hp1020_video_thread_candidate` receives video queue messages and calls the raster/video functions around `0x10014910`-`0x10015458`.");
        out.println("- MMIO references in this report are still partial but are now concentrated around engine/video functions instead of the whole firmware.");
    }

    private void writeWindow(PrintWriter out, long rawAddress, int words) throws Exception {
        Address start = addr(rawAddress);
        out.printf("### Window at `0x%08x`%n%n", rawAddress);
        for (int i = 0; i < words; i++) {
            Address wordAddress = start.add((long) i * 4);
            MemoryBlock block = currentProgram.getMemory().getBlock(wordAddress);
            if (block == null || !block.isInitialized()) {
                continue;
            }
            long value = Integer.toUnsignedLong(currentProgram.getMemory().getInt(wordAddress));
            out.printf("- `%s`: `0x%08x` %s%n", wordAddress, value, describeValue(value));
        }
        out.println();
    }

    private String describeValue(long value) {
        if (value == 0) {
            return "zero";
        }
        if (isMmio(value)) {
            return "MMIO-looking address";
        }
        if (value >= 0x90000000L && value < 0x90100000L) {
            return "SRAM/DMA-looking address";
        }
        if (value >= 0x10000000L && value < 0x10200000L) {
            Address address = addr(value);
            Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
            if (fn != null) {
                return "function " + displayName(fn);
            }
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
            if (fn != null) {
                return "inside function " + displayName(fn) + "+" + Long.toHexString(address.subtract(fn.getEntryPoint()));
            }
            Data data = currentProgram.getListing().getDataAt(address);
            if (data != null) {
                StringDataInstance s = StringDataInstance.getStringDataInstance(data);
                if (s != null && s.getStringValue() != null) {
                    return "string \"" + compact(s.getStringValue()) + "\"";
                }
            }
            MemoryBlock block = currentProgram.getMemory().getBlock(address);
            if (block != null) {
                return "program " + block.getName();
            }
            return "program address";
        }
        return "constant";
    }

    private List<Function> sortFunctions(Set<Function> functions) {
        List<Function> sorted = new ArrayList<>(functions);
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        return sorted;
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

    private Function functionAtOrCreate(long rawAddress, String name) {
        Address address = addr(rawAddress);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        if (fn == null) {
            MemoryBlock block = currentProgram.getMemory().getBlock(address);
            if (block == null || !block.isExecute() || block.getName().contains("Vectors")) {
                return null;
            }
            try {
                createFunction(address, name);
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
            catch (Exception ignored) {
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
        }
        return fn;
    }

    private Address addr(long value) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(value);
    }

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
    }

    private String compact(String value) {
        String s = value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").trim();
        return s.length() > 180 ? s.substring(0, 177) + "..." : s;
    }

    private static class FnDepth {
        final Function fn;
        final int depth;

        FnDepth(Function fn, int depth) {
            this.fn = fn;
            this.depth = depth;
        }
    }

    private static class FunctionRecord {
        final Function function;
        long size;
        final Set<String> callers = new LinkedHashSet<>();
        final Set<String> calls = new LinkedHashSet<>();
        final Set<String> strings = new LinkedHashSet<>();
        final Set<String> mmioRefs = new LinkedHashSet<>();
        final Set<String> sramRefs = new LinkedHashSet<>();

        FunctionRecord(Function function) {
            this.function = function;
        }
    }
}
