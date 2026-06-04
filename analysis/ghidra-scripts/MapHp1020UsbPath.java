// Maps the HP 1020 USB/download path from known descriptor-table handlers.

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
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Queue;
import java.util.Set;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MapHp1020UsbPath extends GhidraScript {
    private static final long USB_THREAD = 0x10008ff0L;
    private static final long USB_IDLE_THREAD = 0x10009934L;
    private static final long ACL_DOWNLOAD = 0x1000ad44L;
    private static final long PJL_ECHO = 0x1000cdb0L;

    private final Map<Function, LinkedHashSet<Function>> outgoing = new LinkedHashMap<>();
    private final Map<Function, LinkedHashSet<Function>> incoming = new LinkedHashMap<>();
    private final Map<Function, String> labels = new LinkedHashMap<>();
    private final Map<Function, String> decompiled = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020UsbPath <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled-neighbors");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();
        buildCallGraph();

        List<Function> focus = focusFunctions();
        decompileFunctions(focus);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "usb-path-map.md")))) {
            writeReport(out, focus);
        }

        exportDecompiled(focus, decompDir);
    }

    private void applyLabels() {
        label(USB_THREAD, "hp1020_usb2_thread");
        label(USB_IDLE_THREAD, "hp1020_usb2_idle_thread");
        label(ACL_DOWNLOAD, "hp1020_acl_download");
        label(PJL_ECHO, "hp1020_pjl_echo_matcher");

        label(0x10007430L, "hp1020_format_into_buffer_candidate");
        label(0x100169d4L, "hp1020_strlen_like");
        label(0x1001693cL, "hp1020_copy_string_candidate");
        label(0x1001b544L, "hp1020_append_string_to_buffer_candidate");
        label(0x1000dc00L, "hp1020_alloc_buffer_candidate");
        label(0x1000d6b0L, "hp1020_pjl_read_or_poll_candidate");
        label(0x10008c24L, "hp1020_usb_control_tx_data_stage_candidate");
        label(0x10007c00L, "hp1020_usb_register_transfer_candidate");
        label(0x10008fb0L, "hp1020_usb_drain_pending_queue_candidate");
        label(0x10011178L, "hp1020_datastore_get_value_candidate");
        label(0x10017d28L, "threadx_queue_receive_candidate");
        label(0x10018274L, "threadx_thread_create_candidate");
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAt(rawAddress);
        if (fn == null) {
            return;
        }
        labels.put(fn, name);
        if (fn.getName().startsWith("FUN_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // The report uses labels even if Ghidra rejects a duplicate rename.
            }
        }
    }

    private void buildCallGraph() {
        var functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function fn = functions.next();
            LinkedHashSet<Function> callees = outgoing.computeIfAbsent(fn, k -> new LinkedHashSet<>());
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
                    if (target == null || target.equals(fn)) {
                        continue;
                    }
                    callees.add(target);
                    incoming.computeIfAbsent(target, k -> new LinkedHashSet<>()).add(fn);
                }
            }
        }
    }

    private List<Function> focusFunctions() {
        LinkedHashSet<Function> set = new LinkedHashSet<>();
        addIfPresent(set, USB_THREAD);
        addIfPresent(set, USB_IDLE_THREAD);
        addIfPresent(set, ACL_DOWNLOAD);
        addIfPresent(set, PJL_ECHO);

        for (long seed : new long[] { USB_THREAD, ACL_DOWNLOAD, PJL_ECHO }) {
            Function fn = functionAt(seed);
            if (fn == null) {
                continue;
            }
            addSorted(set, outgoing.get(fn));
            addSorted(set, incoming.get(fn));
        }

        Function usbThread = functionAt(USB_THREAD);
        if (usbThread != null) {
            for (Function callee : sorted(outgoing.get(usbThread))) {
                addSorted(set, outgoing.get(callee));
            }
        }

        List<Function> result = new ArrayList<>(set);
        result.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        return result;
    }

    private void decompileFunctions(List<Function> functions) {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (Function fn : functions) {
            DecompileResults results = decompiler.decompileFunction(fn, 30, monitor);
            if (results.decompileCompleted() && results.getDecompiledFunction() != null) {
                decompiled.put(fn, results.getDecompiledFunction().getC());
            }
            else {
                decompiled.put(fn, "/* Decompilation failed: " + results.getErrorMessage() + " */");
            }
        }
        decompiler.dispose();
    }

    private void writeReport(PrintWriter out, List<Function> focus) {
        out.println("# HP 1020 USB/Download Path Map");
        out.println();
        out.println("Seed handlers:");
        out.println("- `10008ff0` `hp1020_usb2_thread`");
        out.println("- `10009934` `hp1020_usb2_idle_thread`");
        out.println("- `1000ad44` `hp1020_acl_download`");
        out.println("- `1000cdb0` `hp1020_pjl_echo_matcher`");
        out.println("- internal labels `10009476` ... `100096e5` USB `GET_DESCRIPTOR` jump-table blocks");
        out.println();

        writeFunctionBlock(out, "USB2Thread", functionAt(USB_THREAD));
        writeFunctionBlock(out, "USB2IdleThread", functionAt(USB_IDLE_THREAD));
        writeFunctionBlock(out, "agiACLDownload", functionAt(ACL_DOWNLOAD));
        writeFunctionBlock(out, "@PJL ECHO matcher", functionAt(PJL_ECHO));

        out.println("## Focus Function List");
        out.println();
        for (Function fn : focus) {
            out.printf("- `%s` `%s` score=%d%n", fn.getEntryPoint(), displayName(fn), scoreFunction(fn));
        }

        out.println();
        out.println("## Register-Like Global Candidates");
        out.println();
        writeGlobalCandidates(out, focus);

        out.println();
        out.println("## Working Interpretation");
        out.println();
        out.println("- `hp1020_usb2_thread` is the main USB service/init loop. It touches many globals through `memw()` barriers, which strongly points to memory-mapped hardware registers or DMA descriptors.");
        out.println("- `hp1020_usb2_idle_thread` is a tight service loop around a nearby helper at `0x10008f40`.");
        out.println("- `hp1020_acl_download` sets bit `0x80` in two control-looking globals, then dispatches through a function pointer loaded from a table at `PTR_DAT_10006068`.");
        out.println("- `hp1020_pjl_echo_matcher` compares incoming bytes against the literal `@PJL ECHO` path and calls a polling/read helper.");
        out.println();
        out.println("## USB Setup Request Constants");
        out.println();
        out.println("Resolved from the literal table near `0x10005f64`:");
        out.println("- `0x8006`: standard USB `GET_DESCRIPTOR` request.");
        out.println("- `0x2102`: class/interface request shape, likely `SET_REPORT` or a related class control transfer.");
        out.println("- `0xa100`, `0xa101`, `0xc100`, `0xc101`: vendor/class IN request shapes used by this device.");
        out.println("- jump table at `0x10003500`: seven setup-request handlers reached from the `0x8006` path by request/index byte.");
        out.println();
        out.println("## ACL Dispatch");
        out.println();
        out.println("`PTR_DAT_10006068` resolves to data at `0x1001be90`. The first word there is `0x10000350`, which is outside the normal loaded `.text` functions and lines up with the zero-sized bootcode interface area. Current interpretation: `agiACLDownload` sets USB/control bits and dispatches into a resident bootcode/interface table rather than a normal firmware-local function.");
    }

    private void writeFunctionBlock(PrintWriter out, String title, Function fn) {
        out.println("## " + title);
        out.println();
        if (fn == null) {
            out.println("Function not found.");
            out.println();
            return;
        }
        out.printf("Entry: `%s` `%s`%n%n", fn.getEntryPoint(), displayName(fn));
        writeLinks(out, "Direct callees", outgoing.get(fn), 24);
        writeLinks(out, "Direct callers", incoming.get(fn), 24);
        out.println();
        out.println("Global/pointer symbols seen in decompiler output:");
        out.println(formatGlobalHits(fn));
        out.println();
    }

    private void writeLinks(PrintWriter out, String title, Set<Function> fns, int limit) {
        out.println(title + ":");
        List<Function> sorted = sorted(fns);
        if (sorted.isEmpty()) {
            out.println("- none found");
            return;
        }
        for (int i = 0; i < sorted.size() && i < limit; i++) {
            Function fn = sorted.get(i);
            out.printf("- `%s` `%s` score=%d%n", fn.getEntryPoint(), displayName(fn), scoreFunction(fn));
        }
        if (sorted.size() > limit) {
            out.println("- ... " + (sorted.size() - limit) + " more");
        }
    }

    private int scoreFunction(Function fn) {
        String code = decompiled.getOrDefault(fn, "");
        int score = 0;
        score += count(code, "memw()") * 3;
        score += count(code, "DAT_") * 2;
        score += count(code, "PTR_DAT_") * 2;
        score += count(code, "(*(code *)") * 5;
        score += count(code, "while") * 2;
        score += outgoing.getOrDefault(fn, new LinkedHashSet<>()).size();
        return score;
    }

    private void writeGlobalCandidates(PrintWriter out, List<Function> focus) {
        Map<String, Integer> counts = new TreeMap<>();
        Pattern p = Pattern.compile("\\b(?:PTR_)?DAT_1000[0-9a-fA-F]+\\b|\\bPTR_LAB_1000[0-9a-fA-F]+\\b");
        for (Function fn : focus) {
            Matcher m = p.matcher(decompiled.getOrDefault(fn, ""));
            while (m.find()) {
                counts.put(m.group(), counts.getOrDefault(m.group(), 0) + 1);
            }
        }

        List<Map.Entry<String, Integer>> entries = new ArrayList<>(counts.entrySet());
        entries.sort((a, b) -> {
            int cmp = Integer.compare(b.getValue(), a.getValue());
            if (cmp != 0) {
                return cmp;
            }
            return a.getKey().compareTo(b.getKey());
        });
        int limit = Math.min(80, entries.size());
        for (int i = 0; i < limit; i++) {
            Map.Entry<String, Integer> entry = entries.get(i);
            out.printf("- `%s` count=%d%n", entry.getKey(), entry.getValue());
        }
    }

    private String formatGlobalHits(Function fn) {
        String code = decompiled.getOrDefault(fn, "");
        Pattern p = Pattern.compile("\\b(?:PTR_)?DAT_1000[0-9a-fA-F]+\\b|\\bPTR_LAB_1000[0-9a-fA-F]+\\b");
        Map<String, Integer> counts = new TreeMap<>();
        Matcher m = p.matcher(code);
        while (m.find()) {
            counts.put(m.group(), counts.getOrDefault(m.group(), 0) + 1);
        }
        if (counts.isEmpty()) {
            return "- none found";
        }
        List<Map.Entry<String, Integer>> entries = new ArrayList<>(counts.entrySet());
        entries.sort((a, b) -> {
            int cmp = Integer.compare(b.getValue(), a.getValue());
            if (cmp != 0) {
                return cmp;
            }
            return a.getKey().compareTo(b.getKey());
        });
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < entries.size() && i < 20; i++) {
            Map.Entry<String, Integer> entry = entries.get(i);
            sb.append("- `").append(entry.getKey()).append("` count=").append(entry.getValue()).append("\n");
        }
        return sb.toString().trim();
    }

    private void exportDecompiled(List<Function> focus, File decompDir) throws Exception {
        for (Function fn : focus) {
            File outFile = new File(decompDir, fn.getEntryPoint() + "_" + displayName(fn) + ".c");
            try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
                out.println("/*");
                out.println("Function: " + fn.getEntryPoint() + " " + displayName(fn));
                out.println("Score: " + scoreFunction(fn));
                out.println("*/");
                out.println();
                out.println(decompiled.getOrDefault(fn, "/* no decompiler output */"));
            }
        }
    }

    private Function functionAt(long rawAddress) {
        Address address = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(rawAddress);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        if (fn == null && isExecutable(address)) {
            try {
                createFunction(address, "fn_" + address);
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
            catch (Exception ignored) {
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
        }
        return fn;
    }

    private boolean isExecutable(Address address) {
        var block = currentProgram.getMemory().getBlock(address);
        return block != null && block.isExecute();
    }

    private void addIfPresent(Set<Function> set, long rawAddress) {
        Function fn = functionAt(rawAddress);
        if (fn != null) {
            set.add(fn);
        }
    }

    private void addSorted(Set<Function> target, Set<Function> source) {
        for (Function fn : sorted(source)) {
            target.add(fn);
        }
    }

    private List<Function> sorted(Set<Function> fns) {
        List<Function> sorted = new ArrayList<>();
        if (fns != null) {
            sorted.addAll(fns);
        }
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        return sorted;
    }

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
    }

    private int count(String haystack, String needle) {
        int result = 0;
        int index = 0;
        while ((index = haystack.indexOf(needle, index)) >= 0) {
            result++;
            index += needle.length();
        }
        return result;
    }
}
