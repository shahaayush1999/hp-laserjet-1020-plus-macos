// Extracts queue-send call sites and the best static message ID evidence near each send.

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
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MapHp1020QueueSendCensus extends GhidraScript {
    private static final Pattern CALL_PATTERN = Pattern.compile(
        "\\b(hp1020_queue_send_message4_candidate|FUN_10010218|" +
        "hp1020_queue_send_candidate|FUN_10013658|" +
        "hp1020_send_or_raise_engine_msg_candidate|FUN_10013620)\\s*\\((.*)\\)\\s*;"
    );

    private static final Pattern SIMPLE_ASSIGN_PATTERN = Pattern.compile(
        "^\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(0x[0-9a-fA-F]+|\\d+)\\s*;"
    );

    private static final Pattern ARRAY_ZERO_ASSIGN_PATTERN = Pattern.compile(
        "^\\s*([A-Za-z_][A-Za-z0-9_]*)\\[0\\]\\s*=\\s*(0x[0-9a-fA-F]+|\\d+)\\s*;"
    );

    private final Map<Long, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020QueueSendCensus <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        initLabels();
        applyLabels();

        List<SendSite> sites = collectSendSites(decompDir);
        writeTsv(new File(outDir, "queue-send-sites.tsv"), sites);
        writeReport(new File(outDir, "queue-send-census.md"), sites);
    }

    private void initLabels() {
        labels.put(0x10010218L, "hp1020_queue_send_message4_candidate");
        labels.put(0x10013620L, "hp1020_send_or_raise_engine_msg_candidate");
        labels.put(0x10013658L, "hp1020_queue_send_candidate");
        labels.put(0x10013668L, "hp1020_queue_send_indexed_candidate");
        labels.put(0x1000e414L, "hp1020_job_mgr_thread_candidate");
        labels.put(0x1000f324L, "hp1020_print_mgr_thread_candidate");
        labels.put(0x1000f574L, "hp1020_print_mgr_schedule_or_advance_candidate");
        labels.put(0x1000f814L, "hp1020_print_mgr_return_work_to_jobmgr_candidate");
        labels.put(0x1000fcb0L, "hp1020_print_mgr_datastore_notify_state_candidate");
        labels.put(0x100100a8L, "hp1020_print_mgr_status_aux_candidate");
        labels.put(0x10010230L, "hp1020_print_mgr_idle_or_restart_candidate");
        labels.put(0x10010590L, "hp1020_status_mgr_thread_candidate");
        labels.put(0x10010fd0L, "hp1020_datastore_write_notify_unlock_candidate");
        labels.put(0x10013c18L, "hp1020_video_thread_candidate");
        labels.put(0x10013d4cL, "hp1020_video_reset_dispatch_candidate");
        labels.put(0x10015c68L, "hp1020_engine_status_io_candidate");
        labels.put(0x10015df8L, "hp1020_engine_status_poll_candidate");
        labels.put(0x100160a8L, "hp1020_engine_preflight_candidate");
        labels.put(0x10016164L, "hp1020_engine_message_dispatch_candidate");
        labels.put(0x1001635cL, "hp1020_engine_delay_thread_candidate");
        labels.put(0x100163b0L, "hp1020_engine_thread_candidate");
    }

    private void applyLabels() {
        for (Map.Entry<Long, String> entry : labels.entrySet()) {
            Function fn = functionAt(entry.getKey());
            if (fn == null) {
                continue;
            }
            try {
                fn.setName(entry.getValue(), SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // The generated report uses local labels if Ghidra keeps an existing name.
            }
        }
    }

    private Function functionAt(long rawAddress) {
        Address address = addr(rawAddress);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        if (fn == null) {
            try {
                disassemble(address);
                fn = createFunction(address, labels.getOrDefault(rawAddress, "hp1020_fn_" + Long.toHexString(rawAddress)));
            }
            catch (Exception ignored) {
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
        }
        return fn;
    }

    private List<SendSite> collectSendSites(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);

        List<SendSite> sites = new ArrayList<>();
        FunctionIterator iterator = currentProgram.getFunctionManager().getFunctions(true);
        while (iterator.hasNext()) {
            Function fn = iterator.next();
            DecompileResults result = decompiler.decompileFunction(fn, 30, monitor);
            if (result == null || !result.decompileCompleted() || result.getDecompiledFunction() == null) {
                continue;
            }
            String c = clean(result.getDecompiledFunction().getC());
            List<SendSite> found = traceFunction(fn, c);
            if (!found.isEmpty()) {
                sites.addAll(found);
                writeDecompiled(decompDir, fn, c);
            }
        }
        decompiler.dispose();

        sites.sort(Comparator
            .comparing((SendSite site) -> site.functionAddress)
            .thenComparingInt(site -> site.lineNumber));
        return sites;
    }

    private List<SendSite> traceFunction(Function fn, String c) {
        List<SendSite> sites = new ArrayList<>();
        String[] lines = c.split("\\R");
        ArrayDeque<String> history = new ArrayDeque<>();

        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            int startLine = i + 1;
            if (containsSendHelper(line) && !line.contains(";")) {
                StringBuilder joined = new StringBuilder(line);
                while (i + 1 < lines.length && !joined.toString().contains(";")) {
                    i++;
                    joined.append(' ').append(lines[i].trim());
                }
                line = joined.toString();
            }

            Matcher matcher = CALL_PATTERN.matcher(line);
            if (matcher.find()) {
                String helper = canonicalHelper(matcher.group(1));
                String[] args = splitArgs(matcher.group(2));
                if (args.length >= 2) {
                    String queueArg = args[0].trim();
                    String messageArg = messageArg(helper, args, history);
                    String confidence = confidence(helper, queueArg, messageArg);
                    sites.add(new SendSite(
                        fn.getEntryPoint().toString(),
                        labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName()),
                        startLine,
                        helper,
                        queueArg,
                        messageArg,
                        queueName(queueArg),
                        confidence,
                        line,
                        String.join("\\n", history)
                    ));
                }
            }
            if (!line.isEmpty()) {
                history.add(line);
                while (history.size() > 40) {
                    history.removeFirst();
                }
            }
        }
        return sites;
    }

    private boolean containsSendHelper(String line) {
        return line.contains("hp1020_queue_send_message4_candidate") ||
               line.contains("FUN_10010218") ||
               line.contains("hp1020_queue_send_candidate") ||
               line.contains("FUN_10013658") ||
               line.contains("hp1020_send_or_raise_engine_msg_candidate") ||
               line.contains("FUN_10013620");
    }

    private String messageArg(String helper, String[] args, ArrayDeque<String> history) {
        if ("hp1020_queue_send_message4_candidate".equals(helper) && args.length >= 2) {
            return args[1].trim();
        }
        String payload = normalizePayloadArg(args[1]);
        if (payload.isEmpty()) {
            return "unknown";
        }
        String found = findPayloadWordZero(payload, history);
        return found.isEmpty() ? "unknown" : found;
    }

    private String findPayloadWordZero(String payload, ArrayDeque<String> history) {
        List<String> lines = new ArrayList<>(history);
        for (int i = lines.size() - 1; i >= 0; i--) {
            String line = lines.get(i);

            Matcher arrayMatcher = ARRAY_ZERO_ASSIGN_PATTERN.matcher(line);
            if (arrayMatcher.find() && arrayMatcher.group(1).equals(payload)) {
                return arrayMatcher.group(2);
            }

            Matcher simpleMatcher = SIMPLE_ASSIGN_PATTERN.matcher(line);
            if (simpleMatcher.find() && simpleMatcher.group(1).equals(payload)) {
                return simpleMatcher.group(2);
            }
        }
        return "";
    }

    private String normalizePayloadArg(String arg) {
        String value = arg.trim();
        while (value.startsWith("&")) {
            value = value.substring(1).trim();
        }
        if (value.startsWith("(")) {
            int close = value.indexOf(')');
            if (close >= 0 && close + 1 < value.length()) {
                value = value.substring(close + 1).trim();
            }
        }
        return value.replaceAll("\\[0\\]$", "");
    }

    private String canonicalHelper(String helper) {
        if ("FUN_10010218".equals(helper)) {
            return "hp1020_queue_send_message4_candidate";
        }
        if ("FUN_10013658".equals(helper)) {
            return "hp1020_queue_send_candidate";
        }
        if ("FUN_10013620".equals(helper)) {
            return "hp1020_send_or_raise_engine_msg_candidate";
        }
        return helper;
    }

    private String confidence(String helper, String queueArg, String messageArg) {
        boolean queueConstant = isNumber(queueArg);
        boolean messageKnown = isNumber(messageArg);
        if ("hp1020_queue_send_message4_candidate".equals(helper) && queueConstant && messageKnown) {
            return "high_direct_wrapper";
        }
        if (queueConstant && messageKnown) {
            return "medium_payload_history";
        }
        if (messageKnown) {
            return "low_dynamic_queue_known_message";
        }
        if (queueConstant) {
            return "low_known_queue_unknown_message";
        }
        return "low_dynamic";
    }

    private String queueName(String queueArg) {
        if (!isNumber(queueArg)) {
            return "dynamic";
        }
        long value = parseNumber(queueArg);
        if (value == 1) {
            return "PrintMgrQueue";
        }
        if (value == 0) {
            return "engMsgQ";
        }
        if (value == 3) {
            return "Job Mgr Queue";
        }
        if (value == 8) {
            return "Video Queue";
        }
        if (value == 10) {
            return "StatusMgrQueue";
        }
        if (value == 0x0f) {
            return "DelayMgr Msg Queue";
        }
        return "queue_" + queueArg;
    }

    private void writeTsv(File outFile, List<SendSite> sites) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("function\tfunction_name\tline\thelper\tqueue_arg\tqueue_name\tmessage_arg\tconfidence\tcall");
            for (SendSite site : sites) {
                out.printf("%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\t%s%n",
                    site.functionAddress,
                    tsv(site.functionName),
                    site.lineNumber,
                    site.helper,
                    tsv(site.queueArg),
                    tsv(site.queueName),
                    tsv(site.messageArg),
                    site.confidence,
                    tsv(site.callLine));
            }
        }
    }

    private void writeReport(File outFile, List<SendSite> sites) throws Exception {
        int directPrintMgr2d = 0;
        int datastore2d = 0;
        for (SendSite site : sites) {
            if ("1".equals(site.queueArg) && isSameNumber(site.messageArg, 0x2d)) {
                directPrintMgr2d++;
            }
            if (site.functionAddress.equals("10010fd0") && isSameNumber(site.messageArg, 0x2d)) {
                datastore2d++;
            }
        }

        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("# HP 1020 Queue Send Census");
            out.println();
            out.println("This pass decompiles every recovered function and extracts calls to the firmware queue-send wrappers.");
            out.println();
            out.println("## Main Result");
            out.println();
            out.printf("- total queue-send call sites found: `%d`%n", sites.size());
            out.printf("- direct static sends of message `0x2d` to queue `1` / PrintMgrQueue: `%d`%n", directPrintMgr2d);
            out.printf("- data-store writer `0x10010fd0` still emits message `0x2d` through subscriber-selected queue ids: `%d` matching site(s)%n", datastore2d);
            out.println("- Datastore notifications select queue 1 through registered subscribers; lack of a direct constant send does not imply an absent PrintMgr producer.");
            out.println();
            out.println("## Queue 1 / PrintMgr Constant Sends");
            out.println();
            writeFilteredTable(out, sites, "1");
            out.println();
            out.println("## Message 0x2d Sites");
            out.println();
            writeMessageTable(out, sites, 0x2d);
            out.println();
            out.println("## Notes");
            out.println();
            out.println("- `high_direct_wrapper` means the small 4-word wrapper carries the queue and message constants directly in its arguments.");
            out.println("- `medium_payload_history` means the raw queue-send call used a local payload variable whose first word was assigned nearby.");
            out.println("- `unknown` means the send uses a dynamic payload or the assignment is outside the small local history window.");
            out.println("- This is a static pass, so dynamic branch conditions and computed queue ids still need manual follow-up.");
        }
    }

    private void writeFilteredTable(PrintWriter out, List<SendSite> sites, String queueArg) {
        out.println("| Function | Line | Message | Confidence | Call |");
        out.println("|---|---:|---:|---|---|");
        for (SendSite site : sites) {
            if (!site.queueArg.equals(queueArg)) {
                continue;
            }
            out.printf("| `%s` `%s` | %d | `%s` | %s | `%s` |%n",
                site.functionAddress, md(site.functionName), site.lineNumber, md(site.messageArg),
                site.confidence, md(site.callLine));
        }
    }

    private void writeMessageTable(PrintWriter out, List<SendSite> sites, long message) {
        out.println("| Function | Line | Queue | Confidence | Call |");
        out.println("|---|---:|---|---|---|");
        for (SendSite site : sites) {
            if (!isSameNumber(site.messageArg, message)) {
                continue;
            }
            out.printf("| `%s` `%s` | %d | `%s` `%s` | %s | `%s` |%n",
                site.functionAddress, md(site.functionName), site.lineNumber, md(site.queueArg),
                md(site.queueName), site.confidence, md(site.callLine));
        }
    }

    private void writeDecompiled(File decompDir, Function fn, String c) throws Exception {
        String filename = fn.getEntryPoint() + "_" + sanitize(labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName())) + ".c";
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(decompDir, filename)))) {
            out.println("/* Function: " + fn.getEntryPoint() + " " + labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName()) + " */");
            out.println();
            out.print(c);
        }
    }

    private String[] splitArgs(String args) {
        List<String> values = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        int depth = 0;
        for (int i = 0; i < args.length(); i++) {
            char ch = args.charAt(i);
            if (ch == '(') {
                depth++;
            }
            else if (ch == ')' && depth > 0) {
                depth--;
            }
            if (ch == ',' && depth == 0) {
                values.add(current.toString());
                current.setLength(0);
            }
            else {
                current.append(ch);
            }
        }
        values.add(current.toString());
        return values.toArray(new String[0]);
    }

    private boolean isSameNumber(String value, long expected) {
        return isNumber(value) && parseNumber(value) == expected;
    }

    private boolean isNumber(String value) {
        if (value == null) {
            return false;
        }
        return value.matches("0x[0-9a-fA-F]+|\\d+");
    }

    private long parseNumber(String value) {
        if (value.startsWith("0x") || value.startsWith("0X")) {
            return Long.parseLong(value.substring(2), 16);
        }
        return Long.parseLong(value);
    }

    private String clean(String value) {
        return value.replaceAll("[ \\t]+\\n", "\n").replaceAll("\\n+\\z", "\n");
    }

    private String sanitize(String name) {
        return name.replaceAll("[^A-Za-z0-9_.-]+", "_");
    }

    private String tsv(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("\t", " ").replace("\n", "\\n");
    }

    private String md(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("|", "\\|").replace("`", "'");
    }

    private Address addr(long rawAddress) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(rawAddress);
    }

    private static class SendSite {
        final String functionAddress;
        final String functionName;
        final int lineNumber;
        final String helper;
        final String queueArg;
        final String messageArg;
        final String queueName;
        final String confidence;
        final String callLine;
        final String history;

        SendSite(
            String functionAddress,
            String functionName,
            int lineNumber,
            String helper,
            String queueArg,
            String messageArg,
            String queueName,
            String confidence,
            String callLine,
            String history
        ) {
            this.functionAddress = functionAddress;
            this.functionName = functionName;
            this.lineNumber = lineNumber;
            this.helper = helper;
            this.queueArg = queueArg;
            this.messageArg = messageArg;
            this.queueName = queueName;
            this.confidence = confidence;
            this.callLine = callLine;
            this.history = history;
        }
    }
}
