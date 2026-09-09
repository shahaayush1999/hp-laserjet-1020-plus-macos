// Extracts the HP 1020 video work object lifecycle and nearby decompiled functions.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.LinkedHashMap;
import java.util.Map;

public class MapHp1020VideoWorkObject extends GhidraScript {
    private static final long[] TARGETS = {
        0x1000e414L,
        0x1000ed90L,
        0x1000eeb8L,
        0x1000efbcL,
        0x1000f030L,
        0x1000f0a8L,
        0x1000f128L,
        0x1000f204L,
        0x1000f228L,
        0x1000f280L,
        0x1000f574L,
        0x1000f84cL,
        0x10010338L,
        0x10010398L,
        0x100104c8L,
        0x10013c18L,
        0x10014910L,
        0x10015214L,
        0x10015438L,
        0x10016164L
    };

    private final Map<Long, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020VideoWorkObject <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        initLabels();
        applyLabels();
        decompileTargets(decompDir);
        writeReport(new File(outDir, "video-work-object.md"));
    }

    private void initLabels() {
        labels.put(0x1000e414L, "hp1020_job_mgr_thread_candidate");
        labels.put(0x1000ed90L, "hp1020_job_try_start_or_continue_candidate");
        labels.put(0x1000eeb8L, "hp1020_job_resume_or_enqueue_candidate");
        labels.put(0x1000efbcL, "hp1020_work_release_raster_list_candidate");
        labels.put(0x1000f030L, "hp1020_work_finalize_raster_list_candidate");
        labels.put(0x1000f0a8L, "hp1020_work_list_mark_or_send_candidate");
        labels.put(0x1000f128L, "hp1020_work_mark_page_done_candidate");
        labels.put(0x1000f204L, "hp1020_work_common_init_candidate");
        labels.put(0x1000f228L, "hp1020_video_work_create_candidate");
        labels.put(0x1000f280L, "hp1020_work_mode_normalize_candidate");
        labels.put(0x1000f574L, "hp1020_print_mgr_schedule_or_advance_candidate");
        labels.put(0x1000f84cL, "hp1020_print_mgr_media_select_candidate");
        labels.put(0x10010338L, "hp1020_job_record_create_and_enqueue_candidate");
        labels.put(0x10010398L, "hp1020_child_page_record_create_candidate");
        labels.put(0x100104c8L, "hp1020_work_populate_from_page_params_candidate");
        labels.put(0x10013c18L, "hp1020_video_thread_candidate");
        labels.put(0x10014910L, "hp1020_video_prepare_page_candidate");
        labels.put(0x10015214L, "hp1020_video_render_or_dma_candidate");
        labels.put(0x10015438L, "hp1020_video_alt_render_candidate");
        labels.put(0x10016164L, "hp1020_engine_message_dispatch_candidate");
        labels.put(0x10010218L, "hp1020_queue_send_message4_candidate");
        labels.put(0x10013658L, "hp1020_queue_send_candidate");
        labels.put(0x10013000L, "hp1020_list_append_tail_candidate");
        labels.put(0x10013050L, "hp1020_list_pop_head_candidate");
        labels.put(0x100130bcL, "hp1020_list_peek_head_candidate");
        labels.put(0x100130c4L, "hp1020_list_init_candidate");
        labels.put(0x10013140L, "hp1020_alloc_with_retry_candidate");
        labels.put(0x1001809cL, "threadx_queue_receive_wait_candidate");
    }

    private void applyLabels() {
        for (Map.Entry<Long, String> entry : labels.entrySet()) {
            Function fn = functionAt(entry.getKey(), entry.getValue());
            if (fn == null) {
                continue;
            }
            try {
                fn.setName(entry.getValue(), SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Keep going; generated reports also use the local label map.
            }
        }
    }

    private void decompileTargets(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (long raw : TARGETS) {
            Function fn = functionAt(raw, labels.getOrDefault(raw, "hp1020_fn_" + Long.toHexString(raw)));
            if (fn == null) {
                continue;
            }
            DecompileResults result = decompiler.decompileFunction(fn, 30, monitor);
            if (result == null || !result.decompileCompleted() || result.getDecompiledFunction() == null) {
                continue;
            }
            String c = clean(result.getDecompiledFunction().getC());
            File out = new File(decompDir, fn.getEntryPoint() + "_" + safe(labels.getOrDefault(raw, fn.getName())) + ".c");
            try (PrintWriter writer = new PrintWriter(new FileWriter(out))) {
                writer.println("/* Function: " + fn.getEntryPoint() + " " + labels.getOrDefault(raw, fn.getName()) + " */");
                writer.println();
                writer.println(c);
            }
        }
        decompiler.dispose();
    }

    private void writeReport(File file) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("# HP 1020 Video Work Object Static Pass");
            out.println();
            out.println("This pass exports the functions around the `0x94` video work object and records direct xrefs to the important helpers.");
            out.println();
            out.println("## Target Helpers");
            out.println();
            out.println("| Address | Label | Incoming refs |");
            out.println("|---:|---|---:|");
            long[] helpers = {0x1000f228L, 0x100104c8L, 0x1000f0a8L, 0x1000f128L, 0x1000efbcL};
            for (long raw : helpers) {
                out.printf("| `0x%08x` | `%s` | `%d` |%n", raw, labels.get(raw), countRefsTo(raw));
            }
            out.println();
            out.println("## Decompiled Targets");
            out.println();
            for (long raw : TARGETS) {
                out.printf("- `0x%08x` `%s`%n", raw, labels.getOrDefault(raw, "unknown"));
            }
            out.println();
            out.println("## Working Interpretation");
            out.println();
            out.println("- `0x1000f228` allocates a `0x94`-byte work object, initializes four embedded lists at `+0x50`, `+0x58`, `+0x60`, and `+0x68`, clears video DMA fields at `+0x84/+0x88/+0x8c/+0x90`, then calls common work initialization.");
            out.println("- `0x10010398` creates both a `0x50` child/page container and this `0x94` work object, then sends JobMgr messages `3` and `5`.");
            out.println("- JobMgr later stores this `0x94` object into child/page slot `+0x48`, sends it to PrintMgr queue `1` as message `0x0b`, and PrintMgr eventually sends it to video queue `8` as message `0x0b`.");
            out.println("- `0x100104c8` copies selected page-parameter halfwords into the work object: source `+0x22 -> +0x0c`, `+0x0a -> +0x0a`, `+0x06 -> +0x10`, `+0x12 -> +0x22`, `+0x16 -> +0x1e`, `+0x1a -> +0x14`, `+0x1e -> +0x16`, `+0x0e -> +0x0e`, and source word `+0x00 -> +0x00`.");
            out.println("- JobMgr case `0x29` copies a 20-byte incoming payload into runtime block `0x10023e28`; later JobMgr copies that block into work offsets `+0x84/+0x88/+0x8c/+0x90` before video starts.");
            out.println("- No producer for JobMgr message `0x29` is currently proven by the queue-send census, so the parser-side origin of that 20-byte runtime block remains the next unresolved boundary.");
        }
    }

    private long countRefsTo(long raw) {
        Address address = addr(raw);
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(address);
        long count = 0;
        while (refs.hasNext()) {
            Reference ignored = refs.next();
            count++;
        }
        return count;
    }

    private Function functionAt(long raw, String name) {
        Address address = addr(raw);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        if (fn == null) {
            try {
                disassemble(address);
                fn = createFunction(address, name);
            }
            catch (Exception ignored) {
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
        }
        return fn;
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
}
