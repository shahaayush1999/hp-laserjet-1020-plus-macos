// Exports queue routing evidence: queue table, send helper, receivers, and queue-init candidate.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.LinkedHashMap;
import java.util.Map;

public class MapHp1020QueueRouting extends GhidraScript {
    private final Map<Long, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020QueueRouting <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "queue-decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "queue-routing.md")))) {
            writeReport(out, decompDir);
        }
    }

    private void applyLabels() {
        labels.put(0x1000e414L, "hp1020_job_mgr_thread_candidate");
        labels.put(0x1000f324L, "hp1020_print_mgr_thread_candidate");
        labels.put(0x10010590L, "hp1020_status_mgr_thread_candidate");
        labels.put(0x10010b0cL, "hp1020_delay_mgr_receive_thread_candidate");
        labels.put(0x10013620L, "hp1020_send_or_raise_engine_msg_candidate");
        labels.put(0x10013658L, "hp1020_queue_send_candidate");
        labels.put(0x10013668L, "hp1020_queue_send_indexed_candidate");
        labels.put(0x100136d8L, "hp1020_calibration_control_queue_worker_candidate");
        labels.put(0x10013c18L, "hp1020_video_thread_candidate");
        labels.put(0x10013d4cL, "hp1020_video_reset_dispatch_candidate");
        labels.put(0x1001635cL, "hp1020_engine_delay_thread_candidate");
        labels.put(0x100163b0L, "hp1020_engine_thread_candidate");
        labels.put(0x1001809cL, "threadx_queue_receive_wait_candidate");
        labels.put(0x100180dcL, "threadx_queue_send_wait_candidate");

        for (Map.Entry<Long, String> entry : labels.entrySet()) {
            label(entry.getKey(), entry.getValue());
        }
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAtOrCreate(rawAddress, name);
        if (fn == null) {
            return;
        }
        if (fn.getName().startsWith("FUN_") || fn.getName().startsWith("hp1020_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Report uses local label map.
            }
        }
    }

    private void writeReport(PrintWriter out, File decompDir) throws Exception {
        out.println("# HP 1020 Queue Routing Generated Map");
        out.println();
        out.println("This generated pass preserves queue routing evidence and decompiler output for the queue send helper and known queue consumers.");
        out.println();
        out.println("## Queue Table");
        out.println();
        out.println("- `0x10013668` indexes `DAT_100066f0` by queue number.");
        out.printf("- word at `0x100066f0`: `0x%08x`%n", readWord(0x100066f0L));
        out.println("- candidate runtime queue table base: `0x1002c918`");
        out.println();

        out.println("## Candidate Queue IDs");
        out.println();
        out.println("| Queue ID | Candidate owner | Consumer function | Receive/control object |");
        out.println("|---:|---|---|---|");
        out.println("| `0` | `PrintMgrQueue` | `0x1000f324` `hp1020_print_mgr_thread_candidate` | `0x10028a74` |");
        out.println("| `1` | `engMsgQ` | `0x100163b0` `hp1020_engine_thread_candidate` | `0x1002f134` |");
        out.println("| `3` | `Job Mgr Queue` | `0x1000e414` `hp1020_job_mgr_thread_candidate` | `0x1002386c` |");
        out.println("| `8` | `Video Queue` candidate | `0x10013c18` `hp1020_video_thread_candidate` | `0x1002ee38` |");
        out.println("| `10` | `StatusMgrQueue` | `0x10010590` `hp1020_status_mgr_thread_candidate` | `0x10028adc` |");
        out.println("| `0x0f` | `DelayMgr Msg Queue` | `0x10010b0c` `hp1020_delay_mgr_receive_thread_candidate` | `0x1001d694` candidate |");
        out.println();

        out.println("## Decompiled Evidence");
        out.println();
        long[] functions = {
            0x10013668L,
            0x100136d8L,
            0x1000f324L,
            0x1000e414L,
            0x10010590L,
            0x10013c18L,
            0x10013d4cL,
            0x1001635cL,
            0x100163b0L,
            0x10010b0cL
        };
        for (long raw : functions) {
            Function fn = functionAtOrCreate(raw, labelFor(raw));
            if (fn == null) {
                out.printf("### `0x%08x` `%s`%n%n", raw, labelFor(raw));
                out.println("- function unavailable");
                out.println();
                continue;
            }
            out.printf("### `%s` `%s`%n%n", fn.getEntryPoint(), labelFor(raw));
            String c = decompile(fn, decompDir);
            writeInterestingLines(out, c);
        }
    }

    private void writeInterestingLines(PrintWriter out, String c) {
        if (c.isEmpty()) {
            out.println("- decompilation failed");
            out.println();
            return;
        }
        String[] lines = c.split("\\R");
        boolean wrote = false;
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            if (line.contains("queue") || line.contains("Queue") ||
                line.contains("1002c918") || line.contains("DAT_100066f0") ||
                line.contains("hp1020_queue_send") || line.contains("hp1020_send_or_raise") ||
                line.contains("threadx_queue_receive") || line.contains("threadx_queue_send") ||
                line.contains("FUN_100180dc") || line.contains("FUN_1001809c")) {
                if (!wrote) {
                    out.println("```c");
                    wrote = true;
                }
                out.println(line);
            }
        }
        if (wrote) {
            out.println("```");
        }
        else {
            out.println("- no queue-specific decompiler lines found");
        }
        out.println();
    }

    private String decompile(Function fn, File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        DecompileResults results = decompiler.decompileFunction(fn, 30, monitor);
        String c = "";
        if (results.decompileCompleted() && results.getDecompiledFunction() != null) {
            c = results.getDecompiledFunction().getC();
        }
        File outFile = new File(decompDir, fn.getEntryPoint() + "_" + labelFor(fn.getEntryPoint().getOffset()) + ".c");
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("/* Function: " + fn.getEntryPoint() + " " + labelFor(fn.getEntryPoint().getOffset()) + " */");
            out.println();
            if (c.isEmpty()) {
                out.println("/* Decompilation failed: " + results.getErrorMessage() + " */");
            }
            else {
                out.println(c);
            }
        }
        decompiler.dispose();
        return c;
    }

    private long readWord(long rawAddress) throws Exception {
        return Integer.toUnsignedLong(currentProgram.getMemory().getInt(addr(rawAddress)));
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

    private String labelFor(long raw) {
        return labels.getOrDefault(raw, "FUN_" + Long.toHexString(raw));
    }
}
