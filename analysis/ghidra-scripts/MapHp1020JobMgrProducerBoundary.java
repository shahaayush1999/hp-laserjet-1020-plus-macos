// Scans for JobMgr message producers, including direct ThreadX queue-object sends.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class MapHp1020JobMgrProducerBoundary extends GhidraScript {
    private final Map<Long, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020JobMgrProducerBoundary <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        initLabels();
        applyLabels();

        List<Hit> hits = scan(decompDir);
        writeTsv(new File(outDir, "jobmgr-producer-hits.tsv"), hits);
        writeReport(new File(outDir, "jobmgr-producer-boundary.md"), hits);
    }

    private void initLabels() {
        labels.put(0x100062dcL, "hp1020_job_mgr_queue_object_ptr_word");
        labels.put(0x1000e414L, "hp1020_job_mgr_thread_candidate");
        labels.put(0x1000f814L, "hp1020_print_mgr_return_work_to_jobmgr_candidate");
        labels.put(0x10010338L, "hp1020_job_record_create_and_enqueue_candidate");
        labels.put(0x10010398L, "hp1020_child_page_record_create_candidate");
        labels.put(0x100103f8L, "hp1020_jobmgr_send_case_6_candidate");
        labels.put(0x1001040cL, "hp1020_jobmgr_send_case_2_candidate");
        labels.put(0x10010838L, "hp1020_status_state_update_candidate");
        labels.put(0x10013d4cL, "hp1020_video_reset_dispatch_candidate");
        labels.put(0x100144d0L, "hp1020_video_irq_or_band_done_candidate");
        labels.put(0x10017dacL, "threadx_queue_send_scalar_candidate");
        labels.put(0x10017d28L, "threadx_queue_receive_timed_candidate");
        labels.put(0x10013658L, "hp1020_queue_send_candidate");
        labels.put(0x100180dcL, "threadx_queue_send_candidate");
        labels.put(0x1001896cL, "threadx_queue_send_core_candidate");
        labels.put(0x10019408L, "threadx_queue_receive_core_candidate");
        labels.put(0x10023e28L, "hp1020_jobmgr_video_hw_runtime_block");
        labels.put(0x10023e40L, "hp1020_job_mgr_queue_object_candidate");
    }

    private void applyLabels() {
        for (Map.Entry<Long, String> entry : labels.entrySet()) {
            Address address = addr(entry.getKey());
            Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
            if (fn == null) {
                fn = currentProgram.getFunctionManager().getFunctionContaining(address);
            }
            if (fn != null) {
                try {
                    fn.setName(entry.getValue(), SourceType.ANALYSIS);
                }
                catch (Exception ignored) {
                    // Keep local label map even if Ghidra rejects a rename.
                }
            }
            else if (entry.getKey() >= 0x10000000L) {
                try {
                    currentProgram.getSymbolTable().createLabel(address, entry.getValue(), SourceType.ANALYSIS);
                }
                catch (Exception ignored) {
                    // Data labels are advisory in this scan.
                }
            }
        }
    }

    private List<Hit> scan(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        List<Hit> hits = new ArrayList<>();

        FunctionIterator iterator = currentProgram.getFunctionManager().getFunctions(true);
        while (iterator.hasNext()) {
            Function fn = iterator.next();
            DecompileResults result = decompiler.decompileFunction(fn, 30, monitor);
            if (result == null || !result.decompileCompleted() || result.getDecompiledFunction() == null) {
                continue;
            }
            String c = clean(result.getDecompiledFunction().getC());
            List<Hit> functionHits = scanFunction(fn, c);
            if ((c.contains("PTR_DAT_100062dc") || c.contains("hp1020_job_mgr_queue_object")) &&
                (c.contains("FUN_10017dac") || c.contains("threadx_queue_send_scalar_candidate"))) {
                functionHits.add(new Hit(
                    fn.getEntryPoint().toString(),
                    labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName()),
                    0,
                    "direct_jobmgr_scalar_send_function",
                    "function references JobMgr queue object and scalar queue-send helper"
                ));
            }
            if (!functionHits.isEmpty()) {
                hits.addAll(functionHits);
                writeDecompiled(decompDir, fn, c);
            }
        }
        decompiler.dispose();

        hits.sort(Comparator
            .comparing((Hit hit) -> hit.functionAddress)
            .thenComparingInt(hit -> hit.lineNumber)
            .thenComparing(hit -> hit.kind));
        return hits;
    }

    private List<Hit> scanFunction(Function fn, String c) {
        List<Hit> hits = new ArrayList<>();
        String[] lines = c.split("\\R");
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            if (line.isEmpty()) {
                continue;
            }
            String kind = classify(line);
            if (kind == null) {
                continue;
            }
            hits.add(new Hit(
                fn.getEntryPoint().toString(),
                labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName()),
                i + 1,
                kind,
                line
            ));
        }
        return hits;
    }

    private String classify(String line) {
        if (line.contains("hp1020_queue_send_candidate(3") || line.contains("FUN_10013658(3")) {
            return "queue_id_3_send";
        }
        if ((line.contains("PTR_DAT_100062dc") || line.contains("hp1020_job_mgr_queue_object")) &&
            (line.contains("FUN_10017dac") || line.contains("threadx_queue_send_scalar_candidate"))) {
            return "direct_jobmgr_scalar_send";
        }
        if (line.contains("PTR_DAT_100062dc") || line.contains("hp1020_job_mgr_queue_object") ||
            line.contains("0x10023e40")) {
            return "jobmgr_queue_object_ref";
        }
        if (line.contains("hp1020_jobmgr_video_hw_runtime_block") || line.contains("PTR_DAT_10006304") ||
            line.contains("0x10023e28")) {
            return "video_hw_runtime_block_ref";
        }
        if (line.startsWith("case 0x29:") || line.startsWith("case 41:")) {
            return "possible_msg_0x29_constant";
        }
        if (line.startsWith("case 9:") || line.startsWith("case 0x9:")) {
            return "possible_msg_9_constant";
        }
        if (line.matches(".*=\\s*(0x29|41)\\s*;.*") || line.matches(".*\\[0\\]\\s*=\\s*(0x29|41)\\s*;.*")) {
            return "possible_msg_0x29_constant";
        }
        if (line.matches(".*=\\s*(9|0x9)\\s*;.*") || line.matches(".*\\[0\\]\\s*=\\s*(9|0x9)\\s*;.*")) {
            return "possible_msg_9_constant";
        }
        return null;
    }

    private void writeTsv(File file, List<Hit> hits) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("function_address\tfunction_name\tline\tkind\tcode");
            for (Hit hit : hits) {
                out.printf("%s\t%s\t%d\t%s\t%s%n",
                    hit.functionAddress, hit.functionName, hit.lineNumber, hit.kind, hit.code.replace('\t', ' '));
            }
        }
    }

    private void writeReport(File file, List<Hit> hits) throws Exception {
        long queueId3 = hits.stream().filter(hit -> hit.kind.equals("queue_id_3_send")).count();
        long direct = hits.stream()
            .filter(hit -> hit.kind.equals("direct_jobmgr_scalar_send") ||
                           hit.kind.equals("direct_jobmgr_scalar_send_function"))
            .count();
        long msg9 = hits.stream().filter(hit -> hit.kind.equals("possible_msg_9_constant")).count();
        long msg29 = hits.stream().filter(hit -> hit.kind.equals("possible_msg_0x29_constant")).count();
        long runtimeBlock = hits.stream().filter(hit -> hit.kind.equals("video_hw_runtime_block_ref")).count();

        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("# HP 1020 JobMgr Producer Boundary");
            out.println();
            out.println("This pass scans decompiled firmware for JobMgr queue producers, direct queue-object sends, and the currently unresolved JobMgr messages `9` and `0x29`.");
            out.println();
            out.println("## Counts");
            out.println();
            out.printf("- queue-id `3` wrapper sends: `%d`%n", queueId3);
            out.printf("- direct JobMgr scalar sends: `%d`%n", direct);
            out.printf("- possible message `9` constants: `%d`%n", msg9);
            out.printf("- possible message `0x29` constants: `%d`%n", msg29);
            out.printf("- video hardware runtime block refs: `%d`%n", runtimeBlock);
            out.println();
            out.println("## Notable Hits");
            out.println();
            out.println("| Function | Line | Kind | Code |");
            out.println("|---:|---:|---|---|");
            for (Hit hit : hits) {
                if (isNotable(hit)) {
                    out.printf("| `%s` `%s` | `%d` | `%s` | `%s` |%n",
                        hit.functionAddress, hit.functionName, hit.lineNumber, hit.kind, escape(hit.code));
                }
            }
            out.println();
            out.println("## Interpretation");
            out.println();
            out.println("- The normal queue-id wrapper proves JobMgr messages `1`, `2`, `3`, `5`, `6`, `0x0f`, `0x21`, and `0x25` in earlier queue-send reports.");
            out.println("- Direct queue-object sends to JobMgr are real: video reset/interrupt paths call the scalar ThreadX send helper with message `8`.");
            out.println("- This scan still does not prove a normal static producer for JobMgr message `0x29`.");
            out.println("- Message `9` constants mostly occur in PJL/data-store parsing contexts and should not be blindly treated as JobMgr message `9` without queue evidence.");
            out.println("- The next target is broader parser-side tracing: find where the payload copied into JobMgr `0x29` is built, likely before it reaches a wrapper our current queue census recognizes.");
        }
    }

    private boolean isNotable(Hit hit) {
        return hit.kind.equals("queue_id_3_send") ||
               hit.kind.equals("direct_jobmgr_scalar_send") ||
               hit.kind.equals("direct_jobmgr_scalar_send_function") ||
               hit.kind.equals("video_hw_runtime_block_ref") ||
               hit.kind.equals("possible_msg_0x29_constant");
    }

    private void writeDecompiled(File decompDir, Function fn, String c) throws Exception {
        String label = labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName());
        File out = new File(decompDir, fn.getEntryPoint() + "_" + safe(label) + ".c");
        try (PrintWriter writer = new PrintWriter(new FileWriter(out))) {
            writer.println("/* Function: " + fn.getEntryPoint() + " " + label + " */");
            writer.println();
            writer.print(c.replaceAll("[ \\t]+\\n", "\n").replaceAll("\\n+\\z", "\n"));
        }
    }

    private Address addr(long raw) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(raw);
    }

    private String clean(String c) {
        return c.replace("\r\n", "\n").replace("\r", "\n");
    }

    private String safe(String name) {
        return name.replaceAll("[^A-Za-z0-9_.-]+", "_");
    }

    private String escape(String code) {
        return code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|");
    }

    private static class Hit {
        final String functionAddress;
        final String functionName;
        final int lineNumber;
        final String kind;
        final String code;

        Hit(String functionAddress, String functionName, int lineNumber, String kind, String code) {
            this.functionAddress = functionAddress;
            this.functionName = functionName;
            this.lineNumber = lineNumber;
            this.kind = kind;
            this.code = code;
        }
    }
}
