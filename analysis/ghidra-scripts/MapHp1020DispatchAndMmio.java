// Extracts HP 1020 dispatch tables and engine/video MMIO use sites.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
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

public class MapHp1020DispatchAndMmio extends GhidraScript {
    private static final long PRINT_TABLE = 0x100048f0L;
    private static final int PRINT_LOW = 0x0b;
    private static final int PRINT_COUNT = 0x39;

    private static final long VIDEO_RESET_TABLE = 0x10005710L;
    private static final int VIDEO_RESET_COUNT = 8;

    private static final long[] DECOMPILE_TARGETS = {
        0x1000f324L,
        0x10013c18L,
        0x10013d4cL,
        0x10014910L,
        0x10015214L,
        0x10015458L,
        0x10015c68L,
        0x10015df8L,
        0x100160a8L,
        0x10016164L,
        0x100163b0L,
        0x100165a4L
    };

    private static final long[] MMIO_SCAN_FUNCTIONS = {
        0x10014910L,
        0x10015214L,
        0x10015438L,
        0x10015458L,
        0x10015c68L,
        0x10015df8L,
        0x10016024L,
        0x100160a8L,
        0x10016164L,
        0x10016318L,
        0x100163b0L
    };

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020DispatchAndMmio <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();
        decompileTargets(decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "dispatch-mmio.md")))) {
            writeReport(out);
        }
    }

    private void applyLabels() {
        label(0x1000e414L, "hp1020_job_mgr_thread_candidate");
        label(0x1000f324L, "hp1020_print_mgr_thread_candidate");
        label(0x10010590L, "hp1020_status_mgr_thread_candidate");
        label(0x10013620L, "hp1020_send_or_raise_engine_msg_candidate");
        label(0x10013658L, "hp1020_queue_send_candidate");
        label(0x10013668L, "hp1020_queue_send_table_wrapper_candidate");
        label(0x100136d8L, "hp1020_calibration_control_queue_worker_candidate");
        label(0x10013c18L, "hp1020_video_thread_candidate");
        label(0x10013d4cL, "hp1020_video_reset_dispatch_candidate");
        label(0x10014910L, "hp1020_video_prepare_page_candidate");
        label(0x10015214L, "hp1020_video_render_or_dma_candidate");
        label(0x10015438L, "hp1020_video_alt_render_candidate");
        label(0x10015458L, "hp1020_video_reset_or_flush_candidate");
        label(0x10015c68L, "hp1020_engine_status_io_candidate");
        label(0x10015df8L, "hp1020_engine_status_poll_candidate");
        label(0x10016024L, "hp1020_engine_init_step_candidate");
        label(0x100160a8L, "hp1020_engine_preflight_candidate");
        label(0x10016164L, "hp1020_engine_message_dispatch_candidate");
        label(0x10016318L, "hp1020_engine_queue_send_0x18_candidate");
        label(0x1001635cL, "hp1020_engine_delay_thread_candidate");
        label(0x100163b0L, "hp1020_engine_thread_candidate");
        label(0x100165a4L, "hp1020_engine_register_handlers_candidate");
        label(0x1001809cL, "threadx_queue_receive_wait_candidate");
        label(0x100180dcL, "threadx_queue_send_candidate");
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAtOrCreate(rawAddress, name);
        if (fn == null) {
            return;
        }
        labels.put(fn, name);
        if (fn.getName().startsWith("FUN_") || fn.getName().startsWith("hp1020_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // The generated report still uses the local label map.
            }
        }
    }

    private void writeReport(PrintWriter out) throws Exception {
        out.println("# HP 1020 Dispatch And MMIO Map");
        out.println();
        out.println("This pass extracts the concrete switch table entries and MMIO use sites around the print/video/engine path.");
        out.println();
        writePrintMgrTable(out);
        writeVideoResetTable(out);
        writeEngineDispatchSummary(out);
        writeMmioSites(out);
        writeQueue8Evidence(out);
        writeInterpretation(out);
    }

    private void writePrintMgrTable(PrintWriter out) throws Exception {
        out.println("## Print Manager Dispatch Table");
        out.println();
        out.printf("- table: `0x%08x`%n", PRINT_TABLE);
        out.printf("- message range: `0x%02x` through `0x%02x`%n", PRINT_LOW, PRINT_LOW + PRINT_COUNT - 1);
        out.println();
        out.println("| Message | Target | Description |");
        out.println("|---:|---:|---|");
        for (int i = 0; i < PRINT_COUNT; i++) {
            int msg = PRINT_LOW + i;
            long target = readU32(PRINT_TABLE + (long) i * 4);
            out.printf("| `0x%02x` | `0x%08x` | %s |%n", msg, target, describeAddress(target));
        }
        out.println();
    }

    private void writeVideoResetTable(PrintWriter out) throws Exception {
        out.println("## Video Reset Dispatch Table");
        out.println();
        out.printf("- table: `0x%08x`%n", VIDEO_RESET_TABLE);
        out.println();
        out.println("| Case | Target | Description |");
        out.println("|---:|---:|---|");
        for (int i = 0; i < VIDEO_RESET_COUNT; i++) {
            long target = readU32(VIDEO_RESET_TABLE + (long) i * 4);
            out.printf("| `%d` | `0x%08x` | %s |%n", i, target, describeAddress(target));
        }
        out.println();
    }

    private void writeEngineDispatchSummary(PrintWriter out) {
        out.println("## Engine Dispatch Cases");
        out.println();
        out.println("The engine dispatch at `0x10016164` decompiles cleanly enough to identify these cases:");
        out.println();
        out.println("| Message | Working name | Evidence |");
        out.println("|---:|---|---|");
        out.println("| `0x0b` | page/engine work | stores current work pointer, computes state, calls engine status I/O |");
        out.println("| `0x0d` | convert-to-0x0e | rewrites first word to `0x0e` and resends queue `1` |");
        out.println("| `0x0f` | engine reset/clear | sends `0x25`, clears deferred work fields, calls reset helper |");
        out.println("| `0x11` | drain deferred work | polls status, sends delayed `0x11` or pending page `0x0b` |");
        out.println("| `0x18` | status poll | calls engine status poll with flag `1` |");
        out.println("| `0x19` | startup/ready event | sends `0x16` to queue `1` |");
        out.println("| `0x1a` | preflight/status refresh | calls preflight and status poll |");
        out.println("| `0x40` | force/start page path | sets state and falls through to `0x0b` |");
        out.println();
    }

    private void writeMmioSites(PrintWriter out) {
        Map<Long, List<String>> sites = new LinkedHashMap<>();
        for (long raw : MMIO_SCAN_FUNCTIONS) {
            Function fn = functionAtOrCreate(raw, "hp1020_decompile_target_" + Long.toHexString(raw));
            if (fn == null) {
                continue;
            }
            InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
            while (instructions.hasNext()) {
                Instruction instruction = instructions.next();
                Set<Long> values = new LinkedHashSet<>();
                for (Reference ref : instruction.getReferencesFrom()) {
                    if (ref.getToAddress() != null) {
                        long value = ref.getToAddress().getOffset();
                        if (isMmio(value)) {
                            values.add(value);
                        }
                    }
                }
                for (int i = 0; i < instruction.getNumOperands(); i++) {
                    for (Object obj : instruction.getOpObjects(i)) {
                        if (obj instanceof Scalar) {
                            long value = ((Scalar) obj).getUnsignedValue();
                            if (isMmio(value)) {
                                values.add(value);
                            }
                        }
                    }
                }
                for (long value : values) {
                    sites.computeIfAbsent(value, k -> new ArrayList<>())
                        .add(String.format("`%s` `%s` `%s`", instruction.getAddress(), displayName(fn), compact(instruction.toString())));
                }
            }
        }

        out.println("## Engine/Video MMIO Use Sites");
        out.println();
        out.println("These are direct literal/register references visible in selected engine/video functions. They are not final register names.");
        out.println();
        out.println("| MMIO address | Family | Sites |");
        out.println("|---:|---|---|");
        List<Long> sorted = new ArrayList<>(sites.keySet());
        sorted.sort(Comparator.naturalOrder());
        for (long value : sorted) {
            List<String> entries = sites.get(value);
            out.printf("| `0x%08x` | `%s` | %s |%n", value, mmioFamily(value), compact(String.join("<br>", first(entries, 6))));
        }
        out.println();
    }

    private void writeQueue8Evidence(PrintWriter out) {
        out.println("## Queue 8 Evidence");
        out.println();
        out.println("Queue `8` remains the least-resolved active queue in the print path.");
        out.println();
        out.println("Current evidence:");
        out.println();
        out.println("- `hp1020_video_reset_dispatch_candidate` can send message `0x0b` to queue `8`.");
        out.println("- `hp1020_video_thread_candidate` receives from pointer `PTR_DAT_1000676c`; the descriptor region around `0x10006784` contains `tVideo` and video MMIO constants.");
        out.println("- The direct queue ID -> queue object table lives in runtime BSS at `0x1002c918`, so the static file does not directly expose every queue slot value.");
        out.println();
        out.println("The next proof step is to identify the init path that populates `0x1002c918`, or to find every receive wrapper call and match queue object pointers to descriptor names.");
        out.println();
    }

    private void writeInterpretation(PrintWriter out) {
        out.println("## Interpretation");
        out.println();
        out.println("This pass reinforces the current model:");
        out.println();
        out.println("- `PrintMgr` is the high-level message dispatcher, but most entries beyond the early active range still need handler-level names.");
        out.println("- `Video` owns page/raster-band preparation and hardware transfer.");
        out.println("- `Engine` owns mechanical state gating and status-driven advancement.");
        out.println("- The MMIO families are now concentrated enough to support a dedicated register-semantics pass.");
        out.println();
        out.println("A minimal non-printing firmware experiment should wait until the boot/runtime ABI is mapped. A printing experiment should wait until at least the `0xb100`, `0xb200`, `0xb020`, and `0xb050` register families have behavioral names.");
    }

    private void decompileTargets(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (long raw : DECOMPILE_TARGETS) {
            Function fn = functionAtOrCreate(raw, "hp1020_mmio_scan_target_" + Long.toHexString(raw));
            if (fn == null) {
                continue;
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
        }
        decompiler.dispose();
    }

    private List<String> first(List<String> values, int limit) {
        List<String> result = new ArrayList<>();
        for (int i = 0; i < values.size() && i < limit; i++) {
            result.add(values.get(i));
        }
        return result;
    }

    private long readU32(long rawAddress) throws Exception {
        return Integer.toUnsignedLong(currentProgram.getMemory().getInt(addr(rawAddress)));
    }

    private String describeAddress(long value) {
        if (value == 0) {
            return "zero";
        }
        if (isMmio(value)) {
            return "MMIO-looking address";
        }
        if (value >= 0x10000000L && value < 0x10200000L) {
            Address address = addr(value);
            Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
            if (fn != null) {
                return "function `" + displayName(fn) + "`";
            }
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
            if (fn != null) {
                return "inside `" + displayName(fn) + "` + `0x" + Long.toHexString(address.subtract(fn.getEntryPoint())) + "`";
            }
            Data data = currentProgram.getListing().getDataAt(address);
            if (data != null) {
                StringDataInstance s = StringDataInstance.getStringDataInstance(data);
                if (s != null && s.getStringValue() != null) {
                    return "string `" + compact(s.getStringValue()) + "`";
                }
            }
            MemoryBlock block = currentProgram.getMemory().getBlock(address);
            if (block != null) {
                return "program block `" + block.getName() + "`";
            }
        }
        return "constant";
    }

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
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
        if (block == null || !block.isExecute() || block.getName().contains("Vectors")) {
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

    private boolean isMmio(long value) {
        return value >= 0xb0000000L && value < 0xb4000000L;
    }

    private String mmioFamily(long value) {
        return String.format("0x%04x....", (value >>> 16) & 0xffff);
    }

    private Address addr(long value) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(value);
    }

    private String compact(String value) {
        String s = value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").trim();
        return s.length() > 220 ? s.substring(0, 217) + "..." : s;
    }
}
