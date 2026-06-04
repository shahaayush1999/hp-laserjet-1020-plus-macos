// Maps the indexed firmware data-store used by PJL/status, job, video, and engine paths.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public class MapHp1020DataStore extends GhidraScript {
    private static final long LOCK_TABLE_PTR_WORD = 0x10006464L;
    private static final long DATA_TABLE_PTR_WORD = 0x1000647cL;
    private static final int DATA_ENTRY_SIZE = 0x18;
    private static final int LOCK_ENTRY_SIZE = 0x1c;
    private static final int MAX_ENTRIES = 0x40;

    private static final long GET_VALUE = 0x10011178L;
    private static final long LOCK_ENTRY = 0x100111b4L;
    private static final long UNLOCK_ENTRY = 0x100111d8L;

    private static final Map<Integer, String> WORKING_NAMES = new LinkedHashMap<>();
    static {
        WORKING_NAMES.put(0x04, "event-flag slot used by JAMRECOVERY/status flag path");
        WORKING_NAMES.put(0x09, "TIMEOUT status variable backing slot");
        WORKING_NAMES.put(0x0a, "AUTOCONT status variable backing slot");
        WORKING_NAMES.put(0x0d, "TONEREXP/status variable backing slot");
        WORKING_NAMES.put(0x0f, "DENSITY/status variable backing slot");
        WORKING_NAMES.put(0x10, "SETERROR/status variable backing slot");
        WORKING_NAMES.put(0x11, "MEDIA513/status variable backing slot");
        WORKING_NAMES.put(0x12, "MEDIA514/status variable backing slot");
        WORKING_NAMES.put(0x13, "MEDIA515/status variable backing slot");
        WORKING_NAMES.put(0x14, "MEDIA516/status variable backing slot");
        WORKING_NAMES.put(0x18, "PJL ONLINE boolean used by USTATUS DEVICE builder");
        WORKING_NAMES.put(0x19, "USB/status notification enable flag");
        WORKING_NAMES.put(0x1a, "PJL DISPLAY string pointer used by USTATUS DEVICE builder");
        WORKING_NAMES.put(0x1b, "StatusMgr USTATUS timing/enable slot");
        WORKING_NAMES.put(0x1d, "PJL INFO capability/state aggregate");
        WORKING_NAMES.put(0x1e, "PJL command parser writable aggregate");
        WORKING_NAMES.put(0x1f, "status-code lookup state object pointer");
        WORKING_NAMES.put(0x20, "video/page preparation config value");
        WORKING_NAMES.put(0x24, "JAMRECOVERY/status alternate backing slot");
        WORKING_NAMES.put(0x25, "PAPERLESS/status variable backing slot");
    }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020DataStore <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "data-store-decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();

        Memory memory = currentProgram.getMemory();
        long dataBaseRaw = Integer.toUnsignedLong(memory.getInt(addr(DATA_TABLE_PTR_WORD)));
        long lockBaseRaw = Integer.toUnsignedLong(memory.getInt(addr(LOCK_TABLE_PTR_WORD)));
        List<DataEntry> entries = readEntries(dataBaseRaw, lockBaseRaw);
        Map<Long, List<CallUse>> uses = collectHelperUses();

        decompile(functionAt(GET_VALUE), new File(decompDir, "10011178_hp1020_datastore_get_value_candidate.c"));
        decompile(functionAt(LOCK_ENTRY), new File(decompDir, "100111b4_hp1020_datastore_lock_entry_candidate.c"));
        decompile(functionAt(UNLOCK_ENTRY), new File(decompDir, "100111d8_hp1020_datastore_unlock_entry_candidate.c"));

        writeEntriesTsv(entries, new File(outDir, "data-store-table.tsv"));
        writeUsesTsv(uses, new File(outDir, "data-store-helper-uses.tsv"));
        writeReport(entries, uses, dataBaseRaw, lockBaseRaw, new File(outDir, "data-store-map.md"));
    }

    private void applyLabels() {
        label(GET_VALUE, "hp1020_datastore_get_value_candidate");
        label(LOCK_ENTRY, "hp1020_datastore_lock_entry_candidate");
        label(UNLOCK_ENTRY, "hp1020_datastore_unlock_entry_candidate");
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAt(rawAddress);
        if (fn == null || !fn.getName().startsWith("FUN_")) {
            return;
        }
        try {
            fn.setName(name, SourceType.ANALYSIS);
        }
        catch (Exception ignored) {
            // Report output still uses the working label names.
        }
    }

    private List<DataEntry> readEntries(long dataBaseRaw, long lockBaseRaw) throws Exception {
        List<DataEntry> entries = new ArrayList<>();
        Memory memory = currentProgram.getMemory();
        for (int i = 0; i < MAX_ENTRIES; i++) {
            Address entry = addr(dataBaseRaw + (long) i * DATA_ENTRY_SIZE);
            if (!memory.contains(entry.add(DATA_ENTRY_SIZE - 1L))) {
                break;
            }
            long[] words = new long[6];
            for (int j = 0; j < words.length; j++) {
                words[j] = Integer.toUnsignedLong(memory.getInt(entry.add(j * 4L)));
            }
            if (words[0] != i) {
                break;
            }
            String value = readCurrentValue(words[1], (int) words[2]);
            String pointerString = safeAscii(words[1]);
            String note = WORKING_NAMES.getOrDefault(i, "");
            entries.add(new DataEntry(i, entry, lockBaseRaw + (long) i * LOCK_ENTRY_SIZE, words, value, pointerString, note));
        }
        return entries;
    }

    private String readCurrentValue(long valuePointerRaw, int type) {
        Memory memory = currentProgram.getMemory();
        Address valuePointer = addr(valuePointerRaw);
        try {
            if (!memory.contains(valuePointer)) {
                return "";
            }
            if (type == 0) {
                return "u8:" + Byte.toUnsignedInt(memory.getByte(valuePointer));
            }
            if (type == 1) {
                return "u16:" + Short.toUnsignedInt(memory.getShort(valuePointer));
            }
            if (type == 2) {
                return "u32:0x" + Long.toHexString(Integer.toUnsignedLong(memory.getInt(valuePointer)));
            }
            if (type == 3 || type == 4) {
                return "ptr/string:" + safeAscii(valuePointerRaw);
            }
        }
        catch (Exception ignored) {
            return "";
        }
        return "";
    }

    private Map<Long, List<CallUse>> collectHelperUses() {
        Map<Long, List<CallUse>> result = new TreeMap<>();
        collectUsesFor(GET_VALUE, "get", result);
        collectUsesFor(LOCK_ENTRY, "lock", result);
        collectUsesFor(UNLOCK_ENTRY, "unlock", result);
        return result;
    }

    private void collectUsesFor(long helperAddress, String helperName, Map<Long, List<CallUse>> result) {
        for (Reference ref : getReferencesTo(addr(helperAddress))) {
            Address from = ref.getFromAddress();
            Function fn = getFunctionContaining(from);
            if (fn == null) {
                continue;
            }
            Integer id = findNearbyImmediateId(from);
            if (id == null) {
                continue;
            }
            result.computeIfAbsent(Integer.toUnsignedLong(id), ignored -> new ArrayList<>())
                .add(new CallUse(id, helperName, from, fn));
        }
    }

    private Integer findNearbyImmediateId(Address callAddress) {
        Address cursor = callAddress;
        for (int i = 0; i < 8; i++) {
            Instruction previous = getInstructionBefore(cursor);
            if (previous == null) {
                return null;
            }
            cursor = previous.getAddress();
            String text = previous.toString().toLowerCase();
            if (!text.contains("a10,")) {
                continue;
            }
            Integer value = immediateFromText(text);
            if (value != null) {
                return value;
            }
        }
        return null;
    }

    private Integer immediateFromText(String text) {
        int hash = text.lastIndexOf("0x");
        if (hash >= 0) {
            int end = hash + 2;
            while (end < text.length() && isHex(text.charAt(end))) {
                end++;
            }
            try {
                int value = Integer.parseUnsignedInt(text.substring(hash + 2, end), 16);
                if (value >= 0 && value < MAX_ENTRIES) {
                    return value;
                }
            }
            catch (NumberFormatException ignored) {
            }
        }
        int comma = text.lastIndexOf(',');
        if (comma >= 0) {
            String tail = text.substring(comma + 1).trim();
            try {
                int value = Integer.parseInt(tail);
                if (value >= 0 && value < MAX_ENTRIES) {
                    return value;
                }
            }
            catch (NumberFormatException ignored) {
            }
        }
        return null;
    }

    private boolean isHex(char c) {
        return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
    }

    private void decompile(Function fn, File outFile) throws Exception {
        if (fn == null) {
            return;
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        DecompileResults results = decompiler.decompileFunction(fn, 30, monitor);
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.printf("/* Function: %s %s */%n%n", fn.getEntryPoint(), fn.getName());
            if (results != null && results.decompileCompleted()) {
                out.println(results.getDecompiledFunction().getC());
            }
            else {
                out.println("/* decompile failed */");
            }
        }
        decompiler.dispose();
    }

    private void writeEntriesTsv(List<DataEntry> entries, File outFile) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("index\tentry_address\tlock_address\tword0\tvalue_pointer\ttype\tword3\tword4\tword5\tcurrent_value\tpointer_string\tworking_note");
            for (DataEntry entry : entries) {
                out.printf("0x%02x\t%s\t0x%x\t0x%x\t0x%x\t%d\t0x%x\t0x%x\t0x%x\t%s\t%s\t%s%n",
                    entry.index, entry.entryAddress, entry.lockAddress,
                    entry.words[0], entry.words[1], entry.words[2], entry.words[3], entry.words[4], entry.words[5],
                    tsv(entry.currentValue), tsv(entry.pointerString), tsv(entry.note));
            }
        }
    }

    private void writeUsesTsv(Map<Long, List<CallUse>> uses, File outFile) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("index\thelper\tcall_address\tfunction_address\tfunction_name");
            for (List<CallUse> callUses : uses.values()) {
                callUses.sort(Comparator.comparing(use -> use.callAddress.toString()));
                for (CallUse use : callUses) {
                    out.printf("0x%02x\t%s\t%s\t%s\t%s%n",
                        use.index, use.helper, use.callAddress, use.function.getEntryPoint(), use.function.getName());
                }
            }
        }
    }

    private void writeReport(List<DataEntry> entries, Map<Long, List<CallUse>> uses, long dataBaseRaw, long lockBaseRaw, File outFile) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("# HP 1020 Data-Store Map");
            out.println();
            out.println("This maps the indexed state table used by the helper trio around `0x10011178`.");
            out.println();
            out.println("## Helper Trio");
            out.println();
            out.println("| Address | Working label | Behavior |");
            out.println("|---:|---|---|");
            out.println("| `0x10011178` | `hp1020_datastore_get_value_candidate` | reads an indexed entry and returns an integer value for byte/halfword/word entries |");
            out.println("| `0x100111b4` | `hp1020_datastore_lock_entry_candidate` | locks the matching mutex entry and returns the entry's value pointer |");
            out.println("| `0x100111d8` | `hp1020_datastore_unlock_entry_candidate` | unlocks the matching mutex entry |");
            out.println();
            out.printf("- data descriptor table pointer word: `0x%x -> 0x%x`%n", DATA_TABLE_PTR_WORD, dataBaseRaw);
            out.printf("- lock/mutex table pointer word: `0x%x -> 0x%x`%n", LOCK_TABLE_PTR_WORD, lockBaseRaw);
            out.printf("- data entry size: `0x%x`; lock entry size: `0x%x`%n", DATA_ENTRY_SIZE, LOCK_ENTRY_SIZE);
            out.println();
            out.println("## Important Entries");
            out.println();
            out.println("| Index | Type | Current/static value | Pointer string | Working note | Helper uses |");
            out.println("|---:|---:|---|---|---|---:|");
            for (DataEntry entry : entries) {
                if (entry.note.isEmpty() && !uses.containsKey((long) entry.index)) {
                    continue;
                }
                int useCount = uses.getOrDefault((long) entry.index, List.of()).size();
                out.printf("| `0x%02x` | `%d` | `%s` | `%s` | %s | `%d` |%n",
                    entry.index, entry.words[2], md(entry.currentValue), md(entry.pointerString), md(entry.note), useCount);
            }
            out.println();
            out.println("## Interpretation");
            out.println();
            out.println("- `DISPLAY=\"...\"` in USTATUS DEVICE is built from data-store entry `0x1a`, not from the numeric `CODE=` conversion table.");
            out.println("- `ONLINE=` in the same response is read through entry `0x18`.");
            out.println("- Status command-table rows such as `PAPERLESS`, `TONEREXP`, and media variables read backing values through this table.");
            out.println("- The helper trio is therefore a central firmware state/config API, not just PJL parsing glue.");
        }
    }

    private String safeAscii(long rawAddress) {
        Address address = addr(rawAddress);
        if (!currentProgram.getMemory().contains(address)) {
            return "";
        }
        StringBuilder out = new StringBuilder();
        try {
            for (int i = 0; i < 96; i++) {
                int b = Byte.toUnsignedInt(currentProgram.getMemory().getByte(address.add(i)));
                if (b == 0) {
                    break;
                }
                if (b < 0x20 || b > 0x7e) {
                    return "";
                }
                out.append((char) b);
            }
        }
        catch (Exception ignored) {
            return "";
        }
        return out.toString();
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

    private Function functionAt(long rawAddress) {
        return getFunctionAt(addr(rawAddress));
    }

    private static class DataEntry {
        final int index;
        final Address entryAddress;
        final long lockAddress;
        final long[] words;
        final String currentValue;
        final String pointerString;
        final String note;

        DataEntry(int index, Address entryAddress, long lockAddress, long[] words, String currentValue, String pointerString, String note) {
            this.index = index;
            this.entryAddress = entryAddress;
            this.lockAddress = lockAddress;
            this.words = words;
            this.currentValue = currentValue;
            this.pointerString = pointerString;
            this.note = note;
        }
    }

    private static class CallUse {
        final int index;
        final String helper;
        final Address callAddress;
        final Function function;

        CallUse(int index, String helper, Address callAddress, Function function) {
            this.index = index;
            this.helper = helper;
            this.callAddress = callAddress;
            this.function = function;
        }
    }
}
