// Maps the HP 1020 ZjStream parser boundary anchored by the USB2Thread descriptor.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class MapHp1020ZjsParserBoundary extends GhidraScript {
    private static final long USB2_DESCRIPTOR = 0x10005fc4L;
    private static final long USB2_THREAD = 0x10008ff0L;
    private static final long ZJS_PARSER_ENTRY = 0x10009d34L;
    private static final long ZJS_MAGIC = 0x1001bc78L;
    private static final long ZJS_TABLE_CANDIDATE = 0x1001bc80L;
    private static final long ZJS_SWITCH_TABLE = 0x100036f0L;
    private static final long ZJS_HEADER_BUFFER_PTR_WORD = 0x10005ffcL;
    private static final long ZJS_SIGNATURE_WORD = 0x10006000L;
    private static final long ZJS_SWITCH_PTR_WORD = 0x1000600cL;
    private static final long ZJS_PARSER_ERROR_FLAG = 0x10006010L;
    private static final long ZJS_AUX_TABLE_CANDIDATE = 0x1001be40L;
    private static final long JOBMGR_THREAD = 0x1000e414L;
    private static final long VIDEO_REFRESH_RAW_BANDS = 0x100140f8L;
    private static final long VIDEO_IRQ_OR_BAND_DONE = 0x100144d0L;

    private static final String[] ZJT_NAMES = {
        "ZJT_START_DOC",
        "ZJT_END_DOC",
        "ZJT_START_PAGE",
        "ZJT_END_PAGE",
        "ZJT_JBIG_BIH",
        "ZJT_JBIG_BID",
        "ZJT_END_JBIG",
        "ZJT_SIGNATURE",
        "ZJT_RAW_IMAGE",
        "ZJT_START_PLANE",
        "ZJT_END_PLANE",
        "ZJT_2600N_PAUSE",
        "ZJT_2600N"
    };

    private static final long[] DECOMPILE_TARGETS = {
        USB2_THREAD,
        ZJS_PARSER_ENTRY,
        0x1000a334L,
        0x1000ad44L,
        JOBMGR_THREAD,
        VIDEO_REFRESH_RAW_BANDS,
        0x10013f34L,
        0x10014244L,
        VIDEO_IRQ_OR_BAND_DONE
    };

    private final Map<Long, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020ZjsParserBoundary <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        File disasmDir = new File(outDir, "disasm");
        outDir.mkdirs();
        decompDir.mkdirs();
        disasmDir.mkdirs();

        initLabels();
        applyLabels();

        List<SwitchEntry> switchEntries = readSwitchEntries();
        writeSwitchTsv(new File(outDir, "zjs-switch-table.tsv"), switchEntries);
        writeBytesDump(new File(outDir, "zjs-data-window.md"));
        decompileTargets(decompDir);
        writeDisasmWindows(disasmDir, switchEntries);
        List<Hit> hits = scanParserReferences(decompDir);
        writeHitsTsv(new File(outDir, "zjs-parser-reference-hits.tsv"), hits);
        writeReport(new File(outDir, "zjs-parser-boundary.md"), switchEntries, hits);
    }

    private void initLabels() {
        labels.put(USB2_DESCRIPTOR, "hp1020_usb2_thread_descriptor");
        labels.put(USB2_THREAD, "hp1020_usb2_thread");
        labels.put(ZJS_PARSER_ENTRY, "hp1020_zjs_parser_entry_candidate");
        labels.put(ZJS_MAGIC, "hp1020_zjs_magic_jzjz");
        labels.put(ZJS_TABLE_CANDIDATE, "hp1020_zjs_descriptor_or_parser_table_candidate");
        labels.put(ZJS_SWITCH_TABLE, "hp1020_zjs_chunk_type_switch_table");
        labels.put(ZJS_HEADER_BUFFER_PTR_WORD, "hp1020_zjs_header_buffer_ptr_word");
        labels.put(ZJS_SIGNATURE_WORD, "hp1020_zjs_signature_word_candidate");
        labels.put(ZJS_SWITCH_PTR_WORD, "hp1020_zjs_switch_table_ptr_word");
        labels.put(ZJS_PARSER_ERROR_FLAG, "hp1020_zjs_parser_error_flag");
        labels.put(ZJS_AUX_TABLE_CANDIDATE, "hp1020_zjs_aux_table_candidate");
        labels.put(0x1000a334L, "hp1020_acl_or_peer_parser_entry_candidate");
        labels.put(0x1000ad44L, "hp1020_acl_download_candidate");
        labels.put(JOBMGR_THREAD, "hp1020_job_mgr_thread_candidate");
        labels.put(0x10013140L, "hp1020_alloc_with_retry_candidate");
        labels.put(0x10013408L, "hp1020_free_candidate");
        labels.put(0x10013658L, "hp1020_queue_send_candidate");
        labels.put(0x100169d4L, "hp1020_strlen_like");
        labels.put(0x1001b38cL, "hp1020_memcpy_candidate");
        labels.put(0x1001b56cL, "hp1020_memcmp_candidate");
        labels.put(VIDEO_REFRESH_RAW_BANDS, "hp1020_video_refresh_raw_bands_candidate");
        labels.put(0x10013f34L, "hp1020_video_band_queue_or_list_candidate");
        labels.put(0x10014244L, "hp1020_video_band_done_or_irq_helper_candidate");
        labels.put(VIDEO_IRQ_OR_BAND_DONE, "hp1020_video_irq_or_band_done_candidate");
    }

    private void applyLabels() {
        for (Map.Entry<Long, String> entry : labels.entrySet()) {
            Address address = addr(entry.getKey());
            Function fn = functionAtOrCreate(entry.getKey(), entry.getValue());
            if (fn != null) {
                try {
                    fn.setName(entry.getValue(), SourceType.ANALYSIS);
                }
                catch (Exception ignored) {
                    // Keep local label map even if the symbol already has another analysis name.
                }
            }
            else {
                try {
                    currentProgram.getSymbolTable().createLabel(address, entry.getValue(), SourceType.ANALYSIS);
                }
                catch (Exception ignored) {
                    // Advisory data label.
                }
            }
        }
    }

    private List<SwitchEntry> readSwitchEntries() throws Exception {
        List<SwitchEntry> entries = new ArrayList<>();
        Memory memory = currentProgram.getMemory();
        for (int type = 0; type < ZJT_NAMES.length; type++) {
            long target = Integer.toUnsignedLong(memory.getInt(addr(ZJS_SWITCH_TABLE + type * 4L)));
            entries.add(new SwitchEntry(type, ZJT_NAMES[type], target, functionNameContaining(target)));
        }
        return entries;
    }

    private void writeSwitchTsv(File file, List<SwitchEntry> entries) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("type\tzjs_name\ttarget\tfunction_containing_target");
            for (SwitchEntry entry : entries) {
                out.printf("0x%02x\t%s\t0x%08x\t%s%n", entry.type, entry.name, entry.target, entry.functionName);
            }
        }
    }

    private void writeBytesDump(File file) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("# HP 1020 ZjStream Data Windows");
            out.println();
            out.println("## USB2 Descriptor Words");
            out.println();
            dumpWords(out, USB2_DESCRIPTOR - 0x10, 0x80);
            out.println();
            out.println("## ZjStream Magic/Table Candidate");
            out.println();
            dumpBytes(out, ZJS_MAGIC - 0x10, 0xe0);
            out.println();
            out.println("## Auxiliary Parser Table Candidate");
            out.println();
            dumpBytes(out, ZJS_AUX_TABLE_CANDIDATE, 0x80);
        }
    }

    private void decompileTargets(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (long raw : DECOMPILE_TARGETS) {
            Function fn = functionAtOrContaining(raw);
            if (fn == null) {
                continue;
            }
            DecompileResults result = decompiler.decompileFunction(fn, 45, monitor);
            File out = new File(decompDir, fn.getEntryPoint() + "_" + safe(labels.getOrDefault(raw, fn.getName())) + ".c");
            try (PrintWriter writer = new PrintWriter(new FileWriter(out))) {
                writer.println("/* Function: " + fn.getEntryPoint() + " " + labels.getOrDefault(raw, fn.getName()) + " */");
                writer.println();
                if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
                    writer.print(clean(result.getDecompiledFunction().getC()));
                }
                else {
                    writer.println("/* Decompilation failed: " + (result == null ? "no result" : result.getErrorMessage()) + " */");
                }
            }
        }
        decompiler.dispose();
    }

    private void writeDisasmWindows(File disasmDir, List<SwitchEntry> entries) throws Exception {
        writeDisasmWindow(new File(disasmDir, "10009d34_parser_entry.txt"), ZJS_PARSER_ENTRY, 0x370);
        for (SwitchEntry entry : entries) {
            writeDisasmWindow(
                new File(disasmDir, String.format("%02x_%s_0x%08x.txt", entry.type, safe(entry.name), entry.target)),
                entry.target,
                0x90);
        }
    }

    private void writeDisasmWindow(File file, long rawStart, long length) throws Exception {
        Address start = addr(rawStart);
        Address end = addr(rawStart + length);
        AddressSet set = new AddressSet(start, end);
        InstructionIterator iterator = currentProgram.getListing().getInstructions(set, true);
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.printf("# Disassembly window 0x%08x..0x%08x%n%n", rawStart, rawStart + length);
            while (iterator.hasNext()) {
                Instruction instruction = iterator.next();
                out.printf("%s  %-8s %s%n",
                    instruction.getAddress(),
                    instruction.getMnemonicString(),
                    instruction.toString());
            }
        }
    }

    private List<Hit> scanParserReferences(File decompDir) throws Exception {
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
            List<Hit> functionHits = classifyHits(fn, c);
            if (!functionHits.isEmpty()) {
                hits.addAll(functionHits);
                if (functionHits.stream().anyMatch(hit -> hit.important)) {
                    writeDecompiled(decompDir, fn, c);
                }
            }
        }

        decompiler.dispose();
        hits.sort(Comparator
            .comparing((Hit hit) -> hit.functionAddress)
            .thenComparingInt(hit -> hit.lineNumber)
            .thenComparing(hit -> hit.kind));
        return hits;
    }

    private List<Hit> classifyHits(Function fn, String c) {
        List<Hit> hits = new ArrayList<>();
        String[] lines = c.split("\\R");
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            if (line.isEmpty()) {
                continue;
            }
            String kind = classifyLine(line);
            if (kind == null) {
                continue;
            }
            boolean important = kind.startsWith("zjs_") ||
                kind.equals("jobmgr_video_runtime_block") ||
                kind.equals("raw_band_video_consumer") ||
                kind.equals("jobmgr_queue_send");
            hits.add(new Hit(
                fn.getEntryPoint().toString(),
                labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName()),
                i + 1,
                kind,
                line,
                important
            ));
        }
        return hits;
    }

    private String classifyLine(String line) {
        if (line.contains("PTR_DAT_10005fe0") || line.contains("hp1020_zjs_magic_jzjz") ||
            line.contains("0x1001bc78")) {
            return "zjs_magic_ref";
        }
        if (line.contains("PTR_switchdataD_100036f0") || line.contains("hp1020_zjs_chunk_type_switch_table") ||
            line.contains("0x100036f0")) {
            return "zjs_chunk_switch_table_ref";
        }
        if (line.contains("PTR_DAT_10005ffc") || line.contains("hp1020_zjs_header_buffer_ptr_word")) {
            return "zjs_header_buffer_ref";
        }
        if (line.contains("+ 0xe") && (line.contains("DAT_10006000") || line.contains("0x5a5a"))) {
            return "zjs_signature_check";
        }
        if (line.contains("+ 0xc") && (line.contains("ushort") || line.contains("uStack_34"))) {
            return "zjs_item_or_reserved_size_read";
        }
        if (line.contains("uVar2 < 0xd") || line.contains("< 0xd")) {
            return "zjs_type_bounds_check";
        }
        if (line.contains("FUN_10013140") || line.contains("hp1020_alloc_with_retry_candidate")) {
            return "parser_alloc";
        }
        if (line.contains("FUN_10013408") || line.contains("hp1020_free_candidate")) {
            return "parser_or_queue_free";
        }
        if (line.contains("FUN_10013658(3") || line.contains("hp1020_queue_send_candidate(3")) {
            return "jobmgr_queue_send";
        }
        if (line.contains("PTR_DAT_10006304") || line.contains("0x10023e28") ||
            line.contains("hp1020_jobmgr_video_hw_runtime_block")) {
            return "jobmgr_video_runtime_block";
        }
        if (line.contains("refreshRawBands") || line.contains("pBidBlock") || line.contains("nBackloggedBands")) {
            return "raw_band_video_consumer";
        }
        return null;
    }

    private void writeHitsTsv(File file, List<Hit> hits) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("function_address\tfunction_name\tline\tkind\timportant\tcode");
            for (Hit hit : hits) {
                out.printf("%s\t%s\t%d\t%s\t%s\t%s%n",
                    hit.functionAddress,
                    hit.functionName,
                    hit.lineNumber,
                    hit.kind,
                    hit.important,
                    hit.code.replace('\t', ' '));
            }
        }
    }

    private void writeReport(File file, List<SwitchEntry> entries, List<Hit> hits) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("# HP 1020 ZjStream Parser Boundary");
            out.println();
            out.println("This pass maps the parser-side boundary between USB receive and the JobMgr/page/video objects already identified.");
            out.println();
            out.println("## Proven Anchors");
            out.println();
            out.println("- USB2Thread descriptor `0x10005fc4` points at task body `0x10008ff0`, parser entry `0x10009d34`, `JZJZ` magic `0x1001bc78`, and parser/table data near `0x1001bc80`.");
            out.println("- `0x10009d34` reads `strlen(\"JZJZ\")`, reads exactly that magic from the stream, compares it, then enters a 16-byte ZjStream chunk-header loop.");
            out.println("- The chunk loop checks the header signature word at offset `+0x0e` against the constant pointed to by `0x10006000`, which matches ZjStream's `ZZ` signature.");
            out.println("- For each chunk, it reads `size`, `type`, and `items` fields from the 16-byte header buffer at `0x10022ce0` via pointer word `0x10005ffc`.");
            out.println("- If `type < 0x0d`, it dispatches through the switch table at `0x100036f0`.");
            out.println();
            out.println("## ZjStream Type Switch Table");
            out.println();
            out.println("| Type | ZjStream name | Target | Containing function |");
            out.println("|---:|---|---:|---|");
            for (SwitchEntry entry : entries) {
                out.printf("| `0x%02x` | `%s` | `0x%08x` | `%s` |%n",
                    entry.type, entry.name, entry.target, escape(entry.functionName));
            }
            out.println();
            out.println("## Important Reference Hits");
            out.println();
            out.println("| Function | Line | Kind | Code |");
            out.println("|---:|---:|---|---|");
            for (Hit hit : hits) {
                if (hit.important) {
                    out.printf("| `%s` `%s` | `%d` | `%s` | `%s` |%n",
                        hit.functionAddress, escape(hit.functionName), hit.lineNumber, hit.kind, escape(hit.code));
                }
            }
            out.println();
            out.println("## Working Interpretation");
            out.println();
            out.println("- This identifies the main host print-stream parser. It is not scanner code, and it is not a generic macOS driver path; it is embedded firmware parsing ZjStream chunks.");
            out.println("- The firmware supports at least ZjStream chunk types `0..12`, matching the `foo2zjs` constants from `vendor/foo2zjs-source/zjs.h`.");
            out.println("- The parser cases are branch targets inside or adjacent to `0x10009d34`, not clean named C functions. That is why earlier function-level call clustering did not expose them cleanly.");
            out.println("- `ZJT_JBIG_BIH` at `0x1000a006` is the previously unresolved producer for JobMgr message `0x29`: it stores message id `0x29`, stores the chunk payload pointer in payload word 3, and sends queue id `3`.");
            out.println("- `ZJT_JBIG_BID` at `0x1000a014` builds a `0x78`-byte raster/list node, stores the chunk payload pointer at node payload `+0x54`, stores chunk length at `+0x48`, and sends JobMgr message `0x2a`.");
            out.println("- `ZJT_2600N` at `0x1000a05d` has a compatibility-looking path that can also send JobMgr message `9`; for HP 1020 daily printing the direct JBIG_BID `0x2a` path is the cleaner raster-data producer to follow first.");
            out.println("- The earlier JobMgr message `9` question was probably too narrow. The parser proves that raster-list traffic can arrive as `0x2a` as well, so the next JobMgr pass should include cases `9`, `0x29`, `0x2a`, and `0x2b` together.");
            out.println("- `0x100140f8` remains a later video/raw-band consumer. It is useful for output-side validation, but it is downstream of the parser.");
            out.println();
            out.println("## Case Body Summary");
            out.println();
            out.println("| ZjStream case | Parser target | Proven action | JobMgr message |");
            out.println("|---|---:|---|---:|");
            out.println("| `ZJT_START_DOC` | `0x10009efe` | allocates/parses a document object and sends it to JobMgr | `1` |");
            out.println("| `ZJT_END_DOC` | `0x1000a1b3` | sends document-end and closes parser state | `2` |");
            out.println("| `ZJT_START_PAGE` | `0x10009f86` | allocates `0x50` child/page object, creates `0x94` video work object, parses page items | `3`, then `5` |");
            out.println("| `ZJT_END_PAGE` | `0x1000a19e` | sends page-end | `6` |");
            out.println("| `ZJT_JBIG_BIH` | `0x1000a006` | sends first 20-byte JBIG BIH payload pointer | `0x29` |");
            out.println("| `ZJT_JBIG_BID` | `0x1000a014` | wraps compressed raster payload in a list node | `0x2a` |");
            out.println("| `ZJT_END_JBIG` | `0x1000a053` | sends end-of-JBIG marker | `0x2b` |");
            out.println("| `ZJT_END_PLANE` | `0x1000a173` | parses plane-end fields and sends plane/event message | `8` |");
            out.println();
            out.println("## Next Reverse-Engineering Step");
            out.println();
            out.println("Run a focused JobMgr pass for messages `0x29`, `0x2a`, and `0x2b`, then connect `0x2a`'s list-node shape to the `0x94` video work object's raster list at `+0x50`.");
        }
    }

    private void dumpWords(PrintWriter out, long rawStart, long length) throws Exception {
        Memory memory = currentProgram.getMemory();
        out.println("| Address | Word | Label/function if known |");
        out.println("|---:|---:|---|");
        for (long raw = rawStart; raw < rawStart + length; raw += 4) {
            long value = Integer.toUnsignedLong(memory.getInt(addr(raw)));
            out.printf("| `0x%08x` | `0x%08x` | `%s` |%n", raw, value, escape(labelOrFunction(value)));
        }
    }

    private void dumpBytes(PrintWriter out, long rawStart, long length) throws Exception {
        Memory memory = currentProgram.getMemory();
        out.println("```");
        for (long raw = rawStart; raw < rawStart + length; raw += 16) {
            StringBuilder hex = new StringBuilder();
            StringBuilder ascii = new StringBuilder();
            for (int i = 0; i < 16 && raw + i < rawStart + length; i++) {
                int b = Byte.toUnsignedInt(memory.getByte(addr(raw + i)));
                hex.append(String.format("%02x ", b));
                ascii.append(b >= 0x20 && b < 0x7f ? (char)b : '.');
            }
            out.printf("0x%08x  %-48s  %s%n", raw, hex.toString(), ascii.toString());
        }
        out.println("```");
    }

    private void writeDecompiled(File decompDir, Function fn, String c) throws Exception {
        File out = new File(decompDir, fn.getEntryPoint() + "_" + safe(labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName())) + ".c");
        try (PrintWriter writer = new PrintWriter(new FileWriter(out))) {
            writer.println("/* Function: " + fn.getEntryPoint() + " " + labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName()) + " */");
            writer.println();
            writer.print(c.replaceAll("[ \\t]+\\n", "\n").replaceAll("\\n+\\z", "\n"));
        }
    }

    private Function functionAtOrContaining(long raw) {
        Address address = addr(raw);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        return fn;
    }

    private Function functionAtOrCreate(long raw, String name) {
        Address address = addr(raw);
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
            disassemble(address);
            return createFunction(address, name);
        }
        catch (Exception ignored) {
            return currentProgram.getFunctionManager().getFunctionAt(address);
        }
    }

    private String functionNameContaining(long raw) {
        Function fn = functionAtOrContaining(raw);
        return fn == null ? "" : labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName());
    }

    private String labelOrFunction(long raw) {
        if (labels.containsKey(raw)) {
            return labels.get(raw);
        }
        Function fn = functionAtOrContaining(raw);
        if (fn != null) {
            return labels.getOrDefault(fn.getEntryPoint().getOffset(), fn.getName());
        }
        return "";
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

    private String escape(String text) {
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|");
    }

    private static class SwitchEntry {
        final int type;
        final String name;
        final long target;
        final String functionName;

        SwitchEntry(int type, String name, long target, String functionName) {
            this.type = type;
            this.name = name;
            this.target = target;
            this.functionName = functionName;
        }
    }

    private static class Hit {
        final String functionAddress;
        final String functionName;
        final int lineNumber;
        final String kind;
        final String code;
        final boolean important;

        Hit(String functionAddress, String functionName, int lineNumber, String kind, String code, boolean important) {
            this.functionAddress = functionAddress;
            this.functionName = functionName;
            this.lineNumber = lineNumber;
            this.kind = kind;
            this.code = code;
            this.important = important;
        }
    }
}
