// Traces internal message IDs around PrintMgr, Video, and Engine queue paths.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
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
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MapHp1020MessageProducers extends GhidraScript {
    private static final long[] SEED_ADDRESSES = {
        0x1000e414L,
        0x1000f324L,
        0x10010590L,
        0x10013c18L,
        0x10013d4cL,
        0x10014910L,
        0x10015214L,
        0x10015df8L,
        0x10016164L,
        0x1001635cL,
        0x100163b0L
    };

    private static final Pattern CASE_PATTERN = Pattern.compile("^\\s*case\\s+(0x[0-9a-fA-F]+|\\d+)\\s*:");
    private static final Pattern ASSIGN_PATTERN = Pattern.compile("\\b([A-Za-z_][A-Za-z0-9_]*(?:\\[[^\\]]+\\])?)\\s*=\\s*(0x[0-9a-fA-F]+|\\d+)\\s*;");
    private static final Pattern SEND_PATTERN = Pattern.compile("(hp1020_queue_send_candidate|hp1020_send_or_raise_engine_msg_candidate|hp1020_register_event_handler_candidate|threadx_queue_receive_wait_candidate|FUN_10013668|FUN_1001809c)\\s*\\(");

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020MessageProducers <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "producer-decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();
        Set<Function> functions = expand(seedFunctions(), 2);

        List<FunctionTrace> traces = decompileAndTrace(functions, decompDir);
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "message-producers.md")))) {
            writeReport(out, traces);
        }
    }

    private void applyLabels() {
        label(0x1000e414L, "hp1020_job_mgr_thread_candidate");
        label(0x1000f324L, "hp1020_print_mgr_thread_candidate");
        label(0x10010590L, "hp1020_status_mgr_thread_candidate");
        label(0x10011258L, "hp1020_register_event_handler_candidate");
        label(0x10013620L, "hp1020_send_or_raise_engine_msg_candidate");
        label(0x10013658L, "hp1020_queue_send_candidate");
        label(0x10013c18L, "hp1020_video_thread_candidate");
        label(0x10013d4cL, "hp1020_video_reset_dispatch_candidate");
        label(0x10014910L, "hp1020_video_prepare_page_candidate");
        label(0x10015214L, "hp1020_video_render_or_dma_candidate");
        label(0x10015438L, "hp1020_video_alt_render_candidate");
        label(0x10015458L, "hp1020_video_reset_or_flush_candidate");
        label(0x10015c68L, "hp1020_engine_read_or_write_status_candidate");
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
        if (fn.getName().startsWith("FUN_") || fn.getName().startsWith("hp1020_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Generated report uses local labels either way.
            }
        }
    }

    private Set<Function> seedFunctions() {
        Set<Function> result = new LinkedHashSet<>();
        for (long raw : SEED_ADDRESSES) {
            Function fn = functionAtOrCreate(raw, "hp1020_message_seed_" + Long.toHexString(raw));
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

    private List<FunctionTrace> decompileAndTrace(Set<Function> functions, File decompDir) throws Exception {
        List<Function> sorted = new ArrayList<>(functions);
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));

        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        List<FunctionTrace> traces = new ArrayList<>();
        for (Function fn : sorted) {
            DecompileResults results = decompiler.decompileFunction(fn, 30, monitor);
            String c = "";
            if (results.decompileCompleted() && results.getDecompiledFunction() != null) {
                c = results.getDecompiledFunction().getC();
            }
            FunctionTrace trace = traceFunction(fn, c);
            if (!trace.cases.isEmpty() || !trace.assignments.isEmpty() || !trace.sendSites.isEmpty()) {
                traces.add(trace);
            }
            File outFile = new File(decompDir, fn.getEntryPoint() + "_" + displayName(fn) + ".c");
            try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
                out.println("/* Function: " + fn.getEntryPoint() + " " + displayName(fn) + " */");
                out.println();
                if (c.isEmpty()) {
                    out.println("/* Decompilation failed: " + results.getErrorMessage() + " */");
                }
                else {
                    out.println(c);
                }
            }
        }
        decompiler.dispose();
        return traces;
    }

    private FunctionTrace traceFunction(Function fn, String c) {
        FunctionTrace trace = new FunctionTrace(fn);
        String[] lines = c.split("\\R");
        ArrayDeque<String> history = new ArrayDeque<>();
        String currentCase = "";
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            Matcher caseMatcher = CASE_PATTERN.matcher(line);
            if (caseMatcher.find()) {
                currentCase = caseMatcher.group(1);
                trace.cases.add(currentCase);
            }
            Matcher assignMatcher = ASSIGN_PATTERN.matcher(line);
            while (assignMatcher.find()) {
                String value = assignMatcher.group(2);
                if (isInterestingValue(value)) {
                    trace.assignments.add(new Assignment(i + 1, currentCase, assignMatcher.group(1), value, line));
                }
            }
            Matcher sendMatcher = SEND_PATTERN.matcher(line);
            if (sendMatcher.find()) {
                trace.sendSites.add(new SendSite(i + 1, currentCase, sendMatcher.group(1), line, new ArrayList<>(history)));
            }
            if (!line.isEmpty()) {
                history.add(line);
                while (history.size() > 10) {
                    history.removeFirst();
                }
            }
        }
        return trace;
    }

    private boolean isInterestingValue(String value) {
        long parsed = parseNumber(value);
        return parsed == 0x0bL || parsed == 0x0dL || parsed == 0x0eL || parsed == 0x0fL ||
            parsed == 0x10L || parsed == 0x11L || parsed == 0x16L || parsed == 0x17L ||
            parsed == 0x18L || parsed == 0x19L || parsed == 0x1aL || parsed == 0x25L ||
            parsed == 0x40L || parsed == 0x43L;
    }

    private long parseNumber(String value) {
        if (value.startsWith("0x") || value.startsWith("0X")) {
            return Long.parseLong(value.substring(2), 16);
        }
        return Long.parseLong(value);
    }

    private void writeReport(PrintWriter out, List<FunctionTrace> traces) {
        out.println("# HP 1020 Message Producer Trace");
        out.println();
        out.println("This report extracts switch cases, message-ID assignments, and queue-send call sites from the decompiled print/job/status/video/engine neighborhood.");
        out.println();

        out.println("## Functions With Message Activity");
        out.println();
        for (FunctionTrace trace : traces) {
            out.printf("- `%s` `%s`: cases `%d`, interesting assignments `%d`, send/receive sites `%d`%n",
                trace.function.getEntryPoint(), displayName(trace.function), trace.cases.size(),
                trace.assignments.size(), trace.sendSites.size());
        }
        out.println();

        out.println("## Switch Cases");
        out.println();
        for (FunctionTrace trace : traces) {
            if (trace.cases.isEmpty()) {
                continue;
            }
            out.printf("### `%s` `%s`%n%n", trace.function.getEntryPoint(), displayName(trace.function));
            out.printf("- cases: `%s`%n%n", String.join("`, `", trace.cases));
        }

        out.println("## Interesting Message Assignments");
        out.println();
        for (FunctionTrace trace : traces) {
            if (trace.assignments.isEmpty()) {
                continue;
            }
            out.printf("### `%s` `%s`%n%n", trace.function.getEntryPoint(), displayName(trace.function));
            for (Assignment assignment : trace.assignments) {
                out.printf("- line `%d`", assignment.lineNumber);
                if (!assignment.caseValue.isEmpty()) {
                    out.printf(" case `%s`", assignment.caseValue);
                }
                out.printf(": `%s = %s` from `%s`%n", assignment.variable, assignment.value, assignment.sourceLine);
            }
            out.println();
        }

        out.println("## Queue Send/Receive Sites");
        out.println();
        for (FunctionTrace trace : traces) {
            if (trace.sendSites.isEmpty()) {
                continue;
            }
            out.printf("### `%s` `%s`%n%n", trace.function.getEntryPoint(), displayName(trace.function));
            for (SendSite site : trace.sendSites) {
                out.printf("#### line `%d` `%s`", site.lineNumber, site.helper);
                if (!site.caseValue.isEmpty()) {
                    out.printf(" case `%s`", site.caseValue);
                }
                out.println();
                out.println();
                out.println("Nearby decompiler context:");
                out.println();
                out.println("```c");
                for (String historyLine : site.history) {
                    out.println(historyLine);
                }
                out.println(site.sourceLine);
                out.println("```");
                out.println();
            }
        }

        out.println("## Interpretation");
        out.println();
        out.println("- Treat these as candidate producers, not final names. Decompiler variable names are temporary.");
        out.println("- The strongest evidence is a constant assignment immediately before `hp1020_queue_send_candidate` or `hp1020_send_or_raise_engine_msg_candidate`.");
        out.println("- Message IDs must be interpreted per queue. `0x0b` in `PrintMgrQueue`, video queue, and engine queue may not mean the exact same operation.");
    }

    private Function functionAtOrCreate(long rawAddress, String name) {
        Address address = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(rawAddress);
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

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
    }

    private static class FnDepth {
        final Function fn;
        final int depth;

        FnDepth(Function fn, int depth) {
            this.fn = fn;
            this.depth = depth;
        }
    }

    private static class FunctionTrace {
        final Function function;
        final List<String> cases = new ArrayList<>();
        final List<Assignment> assignments = new ArrayList<>();
        final List<SendSite> sendSites = new ArrayList<>();

        FunctionTrace(Function function) {
            this.function = function;
        }
    }

    private static class Assignment {
        final int lineNumber;
        final String caseValue;
        final String variable;
        final String value;
        final String sourceLine;

        Assignment(int lineNumber, String caseValue, String variable, String value, String sourceLine) {
            this.lineNumber = lineNumber;
            this.caseValue = caseValue;
            this.variable = variable;
            this.value = value;
            this.sourceLine = sourceLine;
        }
    }

    private static class SendSite {
        final int lineNumber;
        final String caseValue;
        final String helper;
        final String sourceLine;
        final List<String> history;

        SendSite(int lineNumber, String caseValue, String helper, String sourceLine, List<String> history) {
            this.lineNumber = lineNumber;
            this.caseValue = caseValue;
            this.helper = helper;
            this.sourceLine = sourceLine;
            this.history = history;
        }
    }
}
