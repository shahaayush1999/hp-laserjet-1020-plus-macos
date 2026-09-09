// Maps the firmware data-store subscriber lists and known registration sites.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class MapHp1020DataStoreSubscribers extends GhidraScript {
    private static final long SUBSCRIBER_TABLE_PTR_WORD = 0x10006490L;

    private final Map<Long, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020DataStoreSubscribers <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        initLabels();
        applyLabels();

        long subscriberTableBase = readPtr(SUBSCRIBER_TABLE_PTR_WORD);
        List<Subscriber> subscribers = knownSubscribers();

        writeSubscribersTsv(subscribers, new File(outDir, "datastore-subscribers.tsv"));
        writeReport(subscriberTableBase, subscribers, new File(outDir, "datastore-subscriber-report.md"));
        exportDecompilerOutput(decompDir);
    }

    private void initLabels() {
        labels.put(0x10006490L, "hp1020_datastore_subscriber_table_ptr_word");
        labels.put(0x1002c56cL, "hp1020_datastore_subscriber_table_candidate");
        labels.put(0x10010fd0L, "hp1020_datastore_write_notify_unlock_candidate");
        labels.put(0x10011258L, "hp1020_datastore_register_callback_subscriber_candidate");
        labels.put(0x1001135cL, "hp1020_datastore_register_queue_subscriber_candidate");
        labels.put(0x1000f324L, "hp1020_print_mgr_thread_candidate");
        labels.put(0x10013764L, "hp1020_control_panel_datastore_callback_candidate");
        labels.put(0x100139e4L, "hp1020_control_panel_thread_candidate");
        labels.put(0x100162b0L, "hp1020_engine_lookup_media_record_candidate");
        labels.put(0x100162ccL, "hp1020_engine_datastore_media_callback_candidate");
        labels.put(0x10016318L, "hp1020_engine_event_0x0f_config_callback_candidate");
        labels.put(0x100163b0L, "hp1020_engine_thread_candidate");
        labels.put(0x10006738L, "hp1020_control_panel_datastore_callback_ptr_word");
        labels.put(0x100069b4L, "hp1020_engine_density_callback_ptr_word");
        labels.put(0x100069b8L, "hp1020_engine_media_callback_ptr_word");
    }

    private void applyLabels() {
        for (Map.Entry<Long, String> entry : labels.entrySet()) {
            Address address = addr(entry.getKey());
            Function function = currentProgram.getFunctionManager().getFunctionAt(address);
            if (function == null) {
                function = currentProgram.getFunctionManager().getFunctionContaining(address);
            }
            if (function == null && isKnownFunction(entry.getKey())) {
                try {
                    disassemble(address);
                    function = createFunction(address, entry.getValue());
                }
                catch (Exception ignored) {
                    function = currentProgram.getFunctionManager().getFunctionAt(address);
                }
            }
            if (function != null && isKnownFunction(entry.getKey())) {
                try {
                    function.setName(entry.getValue(), SourceType.ANALYSIS);
                    function.setComment("data-store subscriber mapping candidate");
                }
                catch (Exception ignored) {
                    // Output reports use the working labels even if the import already has a name.
                }
                continue;
            }
            try {
                currentProgram.getSymbolTable().createLabel(address, entry.getValue(), SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Existing labels are fine.
            }
        }
    }

    private boolean isKnownFunction(long rawAddress) {
        return rawAddress == 0x10010fd0L || rawAddress == 0x10011258L || rawAddress == 0x1001135cL ||
               rawAddress == 0x1000f324L || rawAddress == 0x10013764L || rawAddress == 0x100139e4L ||
               rawAddress == 0x100162b0L || rawAddress == 0x100162ccL ||
               rawAddress == 0x10016318L || rawAddress == 0x100163b0L;
    }

    private long readPtr(long rawAddress) {
        try {
            Memory memory = currentProgram.getMemory();
            return Integer.toUnsignedLong(memory.getInt(addr(rawAddress)));
        }
        catch (Exception ignored) {
            return 0;
        }
    }

    private List<Subscriber> knownSubscribers() {
        List<Subscriber> rows = new ArrayList<>();
        rows.add(new Subscriber(0x01, "queue", "1", "", 0x1000f324L, "Print manager registers queue notification"));
        rows.add(new Subscriber(0x18, "queue", "1", "", 0x1000f324L, "Print manager registers queue notification for ONLINE changes"));
        rows.add(new Subscriber(0x18, "callback", "", "0x10013764", 0x100139e4L, "Control-panel path updates LED/state bytes for ONLINE"));
        rows.add(new Subscriber(0x19, "callback", "", "0x10013764", 0x100139e4L, "Control-panel path translates status-notify bits into LED/state bytes"));
        rows.add(new Subscriber(0x0f, "callback", "", "0x10016318", 0x100163b0L, "Engine maps DENSITY value into engine state byte at offset 0x59"));
        rows.add(new Subscriber(0x10, "callback", "", "0x100162cc", 0x100163b0L, "Engine callback maps entry to id 0x200 and copies media/status record field"));
        rows.add(new Subscriber(0x11, "callback", "", "0x100162cc", 0x100163b0L, "Engine callback maps entry to id 0x201 and copies media/status record field"));
        rows.add(new Subscriber(0x12, "callback", "", "0x100162cc", 0x100163b0L, "Engine callback maps entry to id 0x202 and copies media/status record field"));
        rows.add(new Subscriber(0x13, "callback", "", "0x100162cc", 0x100163b0L, "Engine callback maps entry to id 0x203 and copies media/status record field"));
        rows.add(new Subscriber(0x14, "callback", "", "0x100162cc", 0x100163b0L, "Engine callback maps entry to id 0x204 and copies media/status record field"));
        return rows;
    }

    private void writeSubscribersTsv(List<Subscriber> rows, File outFile) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("entry_index\tsubscriber_kind\tqueue_id\tcallback\tregistrar\tregistrar_name\tnote");
            for (Subscriber row : rows) {
                out.printf("0x%02x\t%s\t%s\t%s\t0x%x\t%s\t%s%n",
                    row.entryIndex, row.kind, row.queueId, row.callback, row.registrar,
                    labels.getOrDefault(row.registrar, ""), tsv(row.note));
            }
        }
    }

    private void writeReport(long subscriberTableBase, List<Subscriber> rows, File outFile) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("# HP 1020 Data-Store Subscribers");
            out.println();
            out.println("This pass maps the publish/subscribe side of the indexed firmware data store.");
            out.println();
            out.println("## Mechanism");
            out.println();
            out.printf("- subscriber table pointer word: `0x%x -> 0x%x`%n", SUBSCRIBER_TABLE_PTR_WORD, subscriberTableBase);
            out.println("- `0x10011258` registers a callback subscriber for an entry.");
            out.println("- `0x1001135c` registers a queue subscriber for an entry.");
            out.println("- `0x10010fd0` writes the data-store value, then walks the subscriber list for that entry.");
            out.println();
            out.println("Subscriber records are allocated through runtime service `0x14` and then linked into the per-entry list:");
            out.println();
            out.println("| Record bytes | Meaning |");
            out.println("|---:|---|");
            out.println("| `0x00..0x03` | data-store entry index |");
            out.println("| `0x04..0x07` | queue id for queue subscribers |");
            out.println("| `0x08..0x0b` | callback function pointer for callback subscribers |");
            out.println("| `0x0c..` | intrusive linked-list node |");
            out.println();
            out.println("When a value changes, queue subscribers receive message `0x2d` with entry id, new value, and a type class.");
            out.println("Callback subscribers are called directly as `callback(entry_id, new_value)`.");
            out.println();
            out.println("## Known Subscriber Registrations");
            out.println();
            out.println("| Entry | Kind | Target | Registrar | Meaning |");
            out.println("|---:|---|---|---|---|");
            for (Subscriber row : rows) {
                String target = row.kind.equals("queue") ? "queue `" + row.queueId + "`" : "`" + row.callback + "`";
                out.printf("| `0x%02x` | %s | %s | `0x%x` `%s` | %s |%n",
                    row.entryIndex, row.kind, target, row.registrar,
                    labels.getOrDefault(row.registrar, ""), md(row.note));
            }
            out.println();
            out.println("## Current Interpretation");
            out.println();
            out.println("- Data-store entries `0x18` and `0x19` are not just PJL status fields; they also drive the control-panel/LED-ish state path.");
            out.println("- The PrintMgr subscribers use queue id `1`, whose constructor registers `PrintMgrQueue` object `0x10028a74`. Message `0x2d` reaches PrintMgr target `0x1000f497`; the older engine/no-op conclusion resulted from reversed queue IDs. See `analysis/queue-routing/registration.md`.");
            out.println("- Engine entries `0x0f..0x14` are live configuration/status inputs, because the engine thread registers direct callbacks before entering its receive loop.");
            out.println("- The shared engine callback at `0x100162cc` maps entries `0x10..0x14` to internal ids `0x200..0x204`, looks up both records through `0x100162b0`, then copies record field `+4` from the new value record to the mapped entry record.");
            out.println("- This gives a practical pruning method: for a print/status trace, prioritize entries with subscribers and then follow their callback/queue targets.");
        }
    }

    private void exportDecompilerOutput(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        long[] functions = {
            0x10010fd0L, 0x10011258L, 0x1001135cL, 0x1000f324L, 0x10013764L,
            0x100139e4L, 0x100162b0L, 0x100162ccL, 0x10016318L, 0x100163b0L
        };
        for (long rawAddress : functions) {
            Function function = currentProgram.getFunctionManager().getFunctionAt(addr(rawAddress));
            if (function == null) {
                function = currentProgram.getFunctionManager().getFunctionContaining(addr(rawAddress));
            }
            if (function == null) {
                continue;
            }
            DecompileResults result = decompiler.decompileFunction(function, 30, monitor);
            String c = result != null && result.decompileCompleted()
                    ? result.getDecompiledFunction().getC()
                    : "/* decompile failed */\n";
            c = cleanDecompilerOutput(c);
            String filename = Long.toHexString(rawAddress) + "_" + sanitize(labels.getOrDefault(rawAddress, function.getName())) + ".c";
            try (PrintWriter out = new PrintWriter(new FileWriter(new File(decompDir, filename)))) {
                out.println("/* Function: " + function.getEntryPoint() + " " + function.getName() + " */");
                out.println();
                out.print(c);
            }
        }
        decompiler.dispose();
    }

    private String cleanDecompilerOutput(String value) {
        String cleaned = value.replaceAll("[ \\t]+\\n", "\n");
        return cleaned.replaceAll("\\n+\\z", "\n");
    }

    private String sanitize(String name) {
        return name.replaceAll("[^A-Za-z0-9_.-]+", "_");
    }

    private String tsv(String value) {
        return value == null ? "" : value.replace("\t", " ").replace("\n", "\\n");
    }

    private String md(String value) {
        if (value == null || value.isEmpty()) {
            return "";
        }
        return value.replace("|", "\\|").replace("`", "'");
    }

    private Address addr(long rawAddress) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(rawAddress);
    }

    private static class Subscriber {
        final int entryIndex;
        final String kind;
        final String queueId;
        final String callback;
        final long registrar;
        final String note;

        Subscriber(int entryIndex, String kind, String queueId, String callback, long registrar, String note) {
            this.entryIndex = entryIndex;
            this.kind = kind;
            this.queueId = queueId;
            this.callback = callback;
            this.registrar = registrar;
            this.note = note;
        }
    }
}
