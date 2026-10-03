#!/usr/bin/env python3
"""Cross-check the current offline HP 1020 reverse-engineering conclusions."""

from __future__ import annotations

import csv
import hashlib
import json
import runpy
import tarfile
import tempfile
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT_DIR / "analysis/offline-consistency/offline-consistency.json"
OUT_MD = ROOT_DIR / "analysis/offline-consistency/offline-consistency.md"
USB_BULK_PROBE_DIR = "analysis/open-firmware-probes/usb-bulk-parser-draft"

EXPECTED_BULK_PROBE_REPORTS = {
    "combined_contract": "analysis/usb-path/usb-bulk-probe-contract.json",
    "parser_model": f"{USB_BULK_PROBE_DIR}/parser-model.json",
    "deterministic_results": f"{USB_BULK_PROBE_DIR}/deterministic-test-results.json",
    "safety_scan": f"{USB_BULK_PROBE_DIR}/safety-scan.json",
    "usb_contract_scan": f"{USB_BULK_PROBE_DIR}/usb-contract-scan.json",
    "usb_mmio_access_scan": f"{USB_BULK_PROBE_DIR}/usb-mmio-access-scan.json",
    "memory_boundary_scan": f"{USB_BULK_PROBE_DIR}/memory-boundary-scan.json",
    "source_contract_check": f"{USB_BULK_PROBE_DIR}/source-contract-check.json",
    "status_descriptor_check": f"{USB_BULK_PROBE_DIR}/status-descriptor-check.json",
    "config_descriptor_check": f"{USB_BULK_PROBE_DIR}/config-descriptor-check.json",
    "reproducibility_check": f"{USB_BULK_PROBE_DIR}/reproducibility-check.json",
}

EXPECTED_BULK_GENERATED_SAMPLES = {
    "generated::matrix-a4_2400x600",
    "generated::matrix-a4_600x600",
    "generated::matrix-a4_cardstock_media",
    "generated::matrix-a4_default",
    "generated::matrix-a4_draft",
    "generated::matrix-a4_logical_clip",
    "generated::matrix-a4_manual_feed",
    "generated::matrix-a4_two_copies",
    "generated::matrix-legal_default",
    "generated::matrix-letter_default",
    "generated::minimal-page-a4",
}

EXPECTED_BULK_MATRIX_CASES = {
    *(f"header_split_{index:02d}_of_16" for index in range(1, 16)),
    *(f"magic_split_{index:02d}_of_4" for index in range(1, 4)),
    "payload_split_across_four_boundaries",
    "multiple_chunks_single_transfer",
    "stock_types_outside_probe_scope_are_unknown",
    "valid_zero_payload_chunks",
    "zero_size_chunk_recovery",
    "oversize_chunk_policy_recovery",
    "bad_signature_recovery",
    "reserved_exceeds_payload_recovery",
    "unknown_chunk_is_counted_and_skipped",
    "ring_and_descriptor_wrap_boundary",
    "payload_crosses_ring_wrap_boundary",
    "three_repeated_documents",
    "truncated_chunk_header_at_eof",
    "truncated_chunk_payload_at_eof",
    "zero_byte_receive_descriptors",
}

EXPECTED_BULK_REPORT_STATUSES = {
    "config_descriptors",
    "layout",
    "safety",
    "usb_contract",
    "usb_mmio",
    "endpoint0_sequence",
    "memory_boundary",
    "endpoint0_length",
    "endpoint0_rearm",
    "source_contract",
    "status_descriptor",
    "parser_model",
}

EXPECTED_BULK_SIDE_EFFECTS = {
    "usb_device_opens": 0,
    "usb_transfers_submitted": 0,
    "mmio_reads": 0,
    "mmio_writes": 0,
    "video_commands": 0,
    "engine_commands": 0,
    "mechanical_actions": 0,
}

EXPECTED_BULK_REGISTERS = {
    "0xb3000200",
    "0xb3000220",
    "0xb3000224",
    "0xb300022c",
    "0xb3000234",
    "0xb3000404",
    "0xb3000418",
    "0xb3010000",
}

EXPECTED_STATUS_DESCRIPTOR = (
    "HP1020 B=00000000 D=00000000 C=00000000 E=00000000 U=00000000"
)


def read_json(rel: str) -> Any:
    return json.loads((ROOT_DIR / rel).read_text())


def read_text(rel: str) -> str:
    return (ROOT_DIR / rel).read_text()


def read_tsv(rel: str) -> list[dict[str, str]]:
    with (ROOT_DIR / rel).open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [{key.lstrip("# ").strip(): value for key, value in row.items()} for row in reader]


def check(name: str, ok: bool, detail: str, *, evidence: str) -> dict[str, str]:
    return {
        "name": name,
        "severity": "watch" if ok else "fail",
        "detail": detail,
        "evidence": evidence,
    }


def severity_count(items: list[dict[str, Any]], severity: str) -> int:
    return sum(item.get("severity") == severity for item in items)


def nested_fail_count(value: Any) -> int:
    """Count explicit fail markers in dict- and list-shaped generated reports."""

    if isinstance(value, list):
        return sum(nested_fail_count(item) for item in value)
    if not isinstance(value, dict):
        return 0
    count = int(value.get("severity") == "fail" or value.get("status") == "fail")
    return count + sum(
        nested_fail_count(item)
        for key, item in value.items()
        if key not in {"severity", "status"}
    )


def report_status(value: Any) -> str:
    if isinstance(value, dict) and value.get("status") in {"pass", "fail"}:
        return value["status"]
    return "fail" if nested_fail_count(value) else "pass"


def report_check_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict) and isinstance(value.get("checks"), list):
        return [item for item in value["checks"] if isinstance(item, dict)]
    return []


def setup_retirement_consistency_gate(root):
    import ast
    import hashlib
    import json
    from pathlib import Path
    import re
    import struct

    root = Path(root)
    detail = (
        "50 conditional post-dispatch tails and 32 pre-peripheral guards per engine "
        "must preserve independently reconstructed ordered accesses, registers and "
        "all mutable RAM, including legitimate writes before a rejected access. "
        "The supplied bulk-size word at 0x1001bc50 controls an unsigned <=512 branch. "
        "Fifteen excluded PCs, no ENTRY and no actual peripheral access establish "
        "neither hardware stall clearing, rearm/quiescence nor a physical USB transfer."
    )

    def need(ok, label):
        if not ok:
            raise ValueError(label)

    def digest(raw):
        return hashlib.sha256(raw).hexdigest()

    try:
        report = json.loads((root / "analysis/usb-path/setup-retirement.json").read_text())
        stock = (root / "analysis/sihp1020.elf").read_bytes()
        stock_sha = "2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d"
        need(report["stock_elf_sha256"] == digest(stock) == stock_sha, "stock ELF hash")

        # Parse only the standard ELF section table here, never its experiment
        # decoder. Fixed mappings below belong to the immutable stock hash.
        need(stock[:6] == b"\x7fELF\x01\x02", "ELF32 big-endian identity")
        shoff = struct.unpack_from(">I", stock, 32)[0]
        shsize, shnum, shstr = struct.unpack_from(">HHH", stock, 46)
        need(shsize == 40 and shstr < shnum and shoff + shsize * shnum <= len(stock),
             "ELF section table bounds")
        headers = [struct.unpack_from(">10I", stock, shoff + i * 40) for i in range(shnum)]
        names_header = headers[shstr]
        names = stock[names_header[4]:names_header[4] + names_header[5]]
        sections = {names[h[0]:].split(b"\0", 1)[0].decode("ascii"): h for h in headers}
        need(sections[".text"][3:6] == (0x10005c80, 0x31e0, 0x15f0f), "pinned .text mapping")
        original_ram = tuple(sorted((h[3], h[3] + h[5]) for h in headers if h[2] & 3 == 3))
        need(original_ram == ((0x10000370, 0x1000049c),
                              (0x1001bb90, 0x1001d640),
                              (0x1001d640, 0x100351e0)), "complete original writable sections")

        def original(address, size):
            need(0x10005c80 <= address < address + size <= 0x1001bb8f, "original .text read")
            offset = 0x31e0 + address - 0x10005c80
            return stock[offset:offset + size]

        # Every instruction of [0x1000985c,0x1000992e), not just selected anchors.
        # Decimal operands are register numbers/immediates; hex operands are
        # literal/branch addresses. This is a static table, not a second executor.
        instruction_rows = """
1000985c 692124 bnei 2,1,0x10009884
1000985f 16f171 l32r 6,0x10005e24
10009862 0c0200 memw -
10009865 8860 l32i.n 8,6,0
10009867 19f18a l32r 9,0x10005e90
1000986a 028802 or 8,8,2
1000986d 0c0200 memw -
10009870 9860 s32i.n 8,6,0
10009872 d990 mov.n 9,9
10009874 0c0200 memw -
10009877 8890 l32i.n 8,9,0
10009879 028802 or 8,8,2
1000987c 0c0200 memw -
1000987f 9890 s32i.n 8,9,0
10009881 220a00 movi 2,0
10009884 18f199 l32r 8,0x10005ee8
10009887 288200 l32i 8,8,0
1000988a 0c0200 memw -
1000988d 238600 s32i 3,8,0
10009890 18f19a l32r 8,0x10005ef8
10009893 0c0200 memw -
10009896 8b80 l32i.n 11,8,0
10009898 2ab000 l8ui 10,11,0
1000989b 29b001 l8ui 9,11,1
1000989e 08aa10 slli 10,10,24
100098a1 009911 slli 9,9,16
100098a4 28b002 l8ui 8,11,2
100098a7 0a9902 or 9,9,10
100098aa 088811 slli 8,8,8
100098ad 2ab003 l8ui 10,11,3
100098b0 098802 or 8,8,9
100098b3 08aa02 or 10,10,8
100098b6 18f15e l32r 8,0x10005e30
100098b9 19f15e l32r 9,0x10005e34
100098bc 08a801 and 8,10,8
100098bf 798936 bne 8,9,0x100098f9
100098c2 18f18a l32r 8,0x10005eec
100098c5 8880 l32i.n 8,8,0
100098c7 0c0200 memw -
100098ca 298000 l8ui 9,8,0
100098cd c098 movi.n 9,8
100098cf 0c0200 memw -
100098d2 298400 s8i 9,8,0
100098d5 0c0200 memw -
100098d8 298001 l8ui 9,8,1
100098db 0c0200 memw -
100098de 238401 s8i 3,8,1
100098e1 0c0200 memw -
100098e4 298002 l8ui 9,8,2
100098e7 0c0200 memw -
100098ea 238402 s8i 3,8,2
100098ed 0c0200 memw -
100098f0 298003 l8ui 9,8,3
100098f3 0c0200 memw -
100098f6 238403 s8i 3,8,3
100098f9 16f14a l32r 6,0x10005e24
100098fc 2a1a00 movi 10,256
100098ff 19f14e l32r 9,0x10005e38
10009902 0c0200 memw -
10009905 8860 l32i.n 8,6,0
10009907 8990 l32i.n 9,9,0
10009909 0a8802 or 8,8,10
1000990c 0c0200 memw -
1000990f 9860 s32i.n 8,6,0
10009911 262a00 movi 6,512
10009914 796310 bltu 6,9,0x10009928
10009917 19f156 l32r 9,0x10005e70
1000991a 0c0200 memw -
1000991d 8890 l32i.n 8,9,0
1000991f 0a8802 or 8,8,10
10009922 0c0200 memw -
10009925 289600 s32i 8,9,0
10009928 18f14f l32r 8,0x10005e64
1000992b 238400 s8i 3,8,0
"""
        instructions = {}
        next_pc = 0x1000985c
        for row in instruction_rows.strip().splitlines():
            address, encoded, op, operands = row.split()
            pc, raw = int(address, 16), bytes.fromhex(encoded)
            args = [] if operands == "-" else [int(v, 0) for v in operands.split(",")]
            need(pc == next_pc and raw == original(pc, len(raw)), "full instruction byte/operand table")
            instructions[hex(pc)] = dict(op=op, args=args, bytes=encoded)
            next_pc += len(raw)
        need(next_pc == 0x1000992e, "exact 210-byte code range")
        code = original(0x1000985c, 210)
        code_sha = "1de51b81705babf558e94f732621f10677f423c86a0a6bac3fe1c84e54eaf1b0"
        audit = report["original_byte_audit"]
        need(audit["begin"] == "0x1000985c" and audit["end"] == "0x1000992e"
             and audit["bytes"] == code.hex() and audit["sha256"] == digest(code) == code_sha
             and audit["instructions"] == instructions, "reported complete original-byte audit")

        extra_pcs = (
            0x1000985c, 0x10009865, 0x10009870, 0x10009877, 0x1000987f, 0x10009881,
            0x1000988d, 0x10009896, 0x10009898, 0x100098bc, 0x100098bf, 0x100098c5,
            0x100098ca, 0x100098d2, 0x100098de, 0x100098ea, 0x100098f6, 0x10009905,
            0x1000990f, 0x10009914, 0x1000991d, 0x10009925, 0x1000992b,
        )
        extra = {hex(pc): [instructions[hex(pc)][k] for k in ("op", "args", "bytes")] for pc in extra_pcs}
        extra.update({
            "0x1000992e": ["j", [0x10009347], "63fa15"],
            "0x1000912d": ["movi.n", [7, 0], "c070"],
            "0x10009286": ["mov.n", [3, 7], "d370"],
        })
        need(audit["extra_anchors"] == extra and all(
            original(int(pc, 16), len(bytes.fromhex(row[2]))) == bytes.fromhex(row[2])
            for pc, row in extra.items()), "audited-only zero definitions and final excluded jump")
        literals = {
            0x10005e24: 0xb3000200, 0x10005e30: 0xc0000000, 0x10005e34: 0x80000000,
            0x10005e38: 0x1001bc50, 0x10005e64: 0x1001bc72, 0x10005e70: 0xb3000220,
            0x10005e90: 0xb3000000, 0x10005ee8: 0x1001bbc0, 0x10005eec: 0x1001bc60,
            0x10005ef8: 0xb3000214,
        }
        redirects = {0x10005e24: 0x22a00100, 0x10005e90: 0x22a00120,
                     0x10005ef8: 0x22a00160, 0x10005e70: 0x22a00140}
        need(audit["literal_originals"] == {hex(a): hex(v) for a, v in literals.items()}
             and all(original(a, 4) == v.to_bytes(4, "big") for a, v in literals.items())
             and report["private_literal_redirects"] == {
                 hex(a): dict(original=hex(literals[a]), ram=hex(v)) for a, v in redirects.items()},
             "all original literals and four named private RAM redirects")

        reference_dir = "analysis/usb-path/controller-reference/linux-v6.12/"
        linux_commit = "adc218676eef25575469234709c2d87185ca223a"
        reference_sha = {
            "amd5536udc.h": "8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648",
            "snps_udc_core.c": "c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf",
            "provenance.json": "023d10e246e4852c1b9415cdc3d591006edcedeba467a56b95b22b994d4a08e4",
        }
        need(audit["linux_commit"] == linux_commit and audit["linux_source_sha256"] == reference_sha
             and audit["linux_control_out_isr_url"] ==
             f"https://github.com/torvalds/linux/blob/{linux_commit}/drivers/usb/gadget/udc/snps_udc_core.c#L2422-L2610"
             and all(digest((root / reference_dir / n).read_bytes()) == h for n, h in reference_sha.items()),
             "immutable Linux reference")
        provenance = json.loads((root / reference_dir / "provenance.json").read_text())
        need(provenance["repository"] == "https://github.com/torvalds/linux"
             and provenance["requested_ref"] == "v6.12" and provenance["commit"] == linux_commit,
             "Linux pin provenance")
        for name in ("amd5536udc.h", "snps_udc_core.c"):
            path = "drivers/usb/gadget/udc/" + name
            rows = [r for r in provenance["files"] if r["path"] == path]
            need(len(rows) == 1 and rows[0]["sha256"] == reference_sha[name]
                 and rows[0]["bytes"] == len((root / reference_dir / name).read_bytes())
                 and rows[0]["url"] == f"https://raw.githubusercontent.com/torvalds/linux/{linux_commit}/{path}",
                 "Linux per-file provenance: " + name)
        header = (root / reference_dir / "amd5536udc.h").read_text()
        for name, value in (("UDC_EPCTL_S", 0), ("UDC_EPCTL_CNAK", 8),
                            ("UDC_EPCTL_NAK", 6), ("UDC_EPCTL_SNAK", 7),
                            ("UDC_DMA_STP_STS_BS_HOST_READY", 0), ("UDC_DMA_STP_STS_BS_DMA_DONE", 2)):
            need(re.search(r"^#define\s+" + name + r"\s+" + str(value) + r"\s*$", header, re.M),
                 "reference bit/value: " + name)

        sources = {"analysis/sihp1020.elf", "scripts/validate-hp1020-usb-setup-retirement.py",
                   *(reference_dir + n for n in reference_sha),
                   *("scripts/" + n + ".py" for n in (
                       "hp1020_qemu_multitask", "hp1020_qemu_ram", "hp1020_qemu_stock_parser",
                       "hp1020_stock_parser_harness", "hp1020_stock_stop", "hp1020_xtensa_call0",
                       "hp1020_xtensa_properties", "hp1020_xtensa_stock"))}
        need(len(sources) == 13 and set(report["source_sha256"]) == set(report["source_origins"]) == sources,
             "exact 13-source closure")
        need(all(digest((root / n).read_bytes()) == h for n, h in report["source_sha256"].items()),
             "current bytes equal exact tested source hashes")
        need(all(isinstance(p, str) and Path(p).is_absolute() and Path(p).as_posix().endswith("/" + n)
                 for n, p in report["source_origins"].items()), "source origin labels")
        # Source origin strings may name the original checkout. Never load those
        # arbitrary paths; current repository bytes above are the hash authority.
        pending, imported = ["scripts/validate-hp1020-usb-setup-retirement.py"], set()
        while pending:
            name = pending.pop()
            if name in imported:
                continue
            imported.add(name)
            for node in ast.walk(ast.parse((root / name).read_text())):
                modules = ([n.name for n in node.names] if isinstance(node, ast.Import) else
                           [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
                for module in modules:
                    dependency = "scripts/" + module.split(".", 1)[0] + ".py"
                    if (root / dependency).is_file() and dependency not in imported:
                        pending.append(dependency)
        need(imported == {n for n in sources if n.endswith(".py")}, "local import closure")

        # Explicit independent matrix. ``available`` is retained only because it
        # is the report's field spelling for the supplied word at 0x1001bc50.
        def base(name, seed, stall=0, owner=2, bulk_size=512):
            return dict(name=name, kind="primary_linked_records", seed=seed, stall=stall,
                        owner=owner, rx=0, low_bits=0x08432105 if seed else 0, available=bulk_size,
                        separate=False, other_status=0x4b654321,
                        out0=0x13570220 | (owner & 1) | ((owner & 2) << 5),
                        in0=0xa55a0210 | ((owner & 2) >> 1) | ((owner & 1) << 6),
                        out1=0x96a50220 | (owner & 1) | ((owner & 2) << 5))

        direct_guards = (
            ("out0-stall-read", 0x10009865, 6, 0xb3000200),
            ("out0-stall-write", 0x10009870, 6, 0xb3000200),
            ("in0-stall-read", 0x10009877, 9, 0xb3000000),
            ("in0-stall-write", 0x1000987f, 9, 0xb3000000),
            ("out0-desptr-read", 0x10009896, 8, 0xb3000214),
            ("out0-cnak-read", 0x10009905, 6, 0xb3000200),
            ("out0-cnak-write", 0x1000990f, 6, 0xb3000200),
            ("out1-cnak-read", 0x1000991d, 9, 0xb3000220),
            ("out1-cnak-write", 0x10009925, 9, 0xb3000220),
        )
        inputs = []
        for seed in (0, 204):
            for stall in (0, 1):
                for owner in range(4):
                    for bulk_size in (512, 513):
                        inputs.append(base(f"linked-f{seed}-s{stall}-o{owner}-n{bulk_size}", seed, stall, owner, bulk_size))
            for rx in range(4):
                row = base(f"rx-independent-f{seed}-rx{rx}", seed, 0, 2, 513)
                row.update(kind="owner_only_rx_and_low_bits_control", rx=rx, low_bits=0x0fffffff)
                inputs.append(row)
            for bulk_size in (0, 0xffffffff):
                row = base(f"unsigned-count-f{seed}-n{bulk_size}", seed, 1, 2, bulk_size)
                row["kind"] = "unsigned_available_boundary"
                inputs.append(row)
            row = base(f"noncanonical-stall-f{seed}", seed, 2)
            row["kind"] = "noncanonical_stall_intent_is_not_one"
            inputs.append(row)
            for owner, target_owner in ((2, 1), (1, 2)):
                row = base(f"mismatched-f{seed}-observed{owner}-target{target_owner}", seed, 1, owner)
                row.update(kind="conditional_mismatched_observed_and_target_records", separate=True,
                           other_status=(target_owner << 30) | 0x0b654321)
                inputs.append(row)
            for label, literal, pc in (("out0", 0x10005e24, 0x10009865),
                                       ("in0", 0x10005e90, 0x10009877),
                                       ("desptr", 0x10005ef8, 0x10009896),
                                       ("out1", 0x10005e70, 0x1000991d)):
                row = base(f"unredirected-{label}-f{seed}", seed, 1)
                row.update(kind="removed_literal_redirect", skip_literal=literal, reject_pc=pc)
                inputs.append(row)
            for label, field, pc in (("setup-target", "bad_setup", 0x1000988d),
                                     ("observed-header", "bad_observed", 0x10009898),
                                     ("rearm-target", "bad_target", 0x100098ca)):
                row = base(f"pointer-escape-{label}-f{seed}", seed, 1)
                row.update(kind="peripheral_pointer_escape", reject_pc=pc, **{field: True})
                inputs.append(row)
            for label, pc, register, address in direct_guards:
                row = base(f"guard-{label}-f{seed}", seed)
                row.update(kind="standalone_peripheral_instruction", entry=pc, reject_pc=pc,
                           registers={str(register): address})
                inputs.append(row)
        counts = dict(primary_linked=32, rx_low_bits=8, unsigned_count=4, noncanonical_stall=2,
                      mismatched_records=4, removed_redirect=8, escaped_pointer=6, standalone_mmio=18)
        need(len(inputs) == 82 and [r["input"] for r in report["cases"]] == inputs
             and report["counts"] == counts, "exact ordered 50 conditional +32 guard input matrix")

        spans = original_ram + ((0x21000000, 0x21020000), (0x22a00000, 0x22a02000))
        templates = {(seed, a, b): bytes((seed + (a >> 8) + i * 17 + (i >> 4) * 3) & 255
                                       for i in range(b - a))
                     for seed in (0, 204) for a, b in spans}

        def ram_read(memory, address, size):
            for (a, b), raw in memory.items():
                if a <= address and address + size <= b:
                    return bytes(raw[address - a:address - a + size])
            raise ValueError("oracle read outside independent RAM: " + hex(address))

        def ram_put(memory, address, data):
            for (a, b), raw in memory.items():
                if a <= address and address + len(data) <= b:
                    raw[address - a:address - a + len(data)] = data
                    return
            raise ValueError("oracle write outside independent RAM: " + hex(address))

        def manifest(memory):
            return [dict(begin=hex(a), end=hex(b), bytes=b - a, sha256=digest(raw))
                    for (a, b), raw in sorted(memory.items())]

        all_pcs = sorted(int(pc, 16) for pc in instructions)
        excluded = (0x10008ff0, 0x1000912d, 0x10009286, 0x10009347, 0x10009358,
                    0x1000935b, 0x1000941d, 0x100096a9, 0x10009859, 0x1000992e,
                    0x10008208, 0x10008f40, 0x10009a10, 0x10009a70, 0x10008c24)

        for case, supplied in zip(report["cases"], inputs):
            label = supplied["name"]
            seed, stall, owner = (supplied[k] for k in ("seed", "stall", "owner"))
            bulk_size = supplied["available"]
            stop = supplied.get("reject_pc", 0x1000992e)
            rejected = "reject_pc" in supplied
            direct = supplied["kind"] == "standalone_peripheral_instruction"
            setup_pointer = 0xb3000300 if supplied.get("bad_setup") else 0x22a00300
            observed_pointer = 0xb3000300 if supplied.get("bad_observed") else 0x22a00400
            target_pointer = (0xb3000300 if supplied.get("bad_target") else
                              0x22a00500 if supplied["separate"] else 0x22a00400)
            status_word = (owner << 30) | (supplied["rx"] << 28) | supplied["low_bits"]
            target_word = supplied["other_status"] if supplied["separate"] else status_word
            literal_values = dict(literals)
            before = {(a, b): bytearray(templates[seed, a, b]) for a, b in spans}
            for address, value in redirects.items():
                if address != supplied.get("skip_literal"):
                    before[address, address + 4] = bytearray(value.to_bytes(4, "big"))
                    literal_values[address] = value
            for address, value in (
                (0x22a00100, supplied["out0"]), (0x22a00120, supplied["in0"]),
                (0x22a00140, supplied["out1"]), (0x22a00160, observed_pointer),
                (0x1001bbc0, setup_pointer), (0x1001bc60, target_pointer), (0x1001bc50, bulk_size),
            ):
                ram_put(before, address, value.to_bytes(4, "big"))
            ram_put(before, 0x1001bc72, bytes([0xa5 ^ seed]))
            ram_put(before, 0x22a00300, bytes.fromhex("8e123456d3c2b1a0a100341256789abc"))
            ram_put(before, 0x22a00400, status_word.to_bytes(4, "big") + bytes.fromhex("1234fedc81726354a5b6c7d8"))
            ram_put(before, 0x22a00500, supplied["other_status"].to_bytes(4, "big") + bytes.fromhex("6789abcd9283746501b2c3d4"))

            # Build a fixed semantic access list from inputs, not reported reads,
            # decoded instructions, executor registers or the generator oracle.
            events = []

            def event(pc, kind, address, value, size=4):
                events.append(dict(pc=hex(pc), kind=kind, address=hex(address), size=size, value=hex(value)))

            def literal(pc, address):
                event(pc, "read", address, literal_values[address])

            if not direct:
                if stall == 1:
                    literal(0x1000985f, 0x10005e24)
                    event(0x10009865, "read", literal_values[0x10005e24], supplied["out0"])
                    literal(0x10009867, 0x10005e90)
                    event(0x10009870, "write", literal_values[0x10005e24], supplied["out0"] | 1)
                    event(0x10009877, "read", literal_values[0x10005e90], supplied["in0"])
                    event(0x1000987f, "write", literal_values[0x10005e90], supplied["in0"] | 1)
                literal(0x10009884, 0x10005ee8)
                event(0x10009887, "read", 0x1001bbc0, setup_pointer)
                event(0x1000988d, "write", setup_pointer, 0)
                literal(0x10009890, 0x10005ef8)
                event(0x10009896, "read", literal_values[0x10005ef8], observed_pointer)
                for offset, pc in enumerate((0x10009898, 0x1000989b, 0x100098a4, 0x100098ad)):
                    event(pc, "read", observed_pointer + offset, (status_word >> (24 - 8 * offset)) & 255, 1)
                literal(0x100098b6, 0x10005e30)
                literal(0x100098b9, 0x10005e34)
                if owner == 2:
                    literal(0x100098c2, 0x10005eec)
                    event(0x100098c5, "read", 0x1001bc60, target_pointer)
                    for offset, rd, wr, value in (
                        (0, 0x100098ca, 0x100098d2, 8), (1, 0x100098d8, 0x100098de, 0),
                        (2, 0x100098e4, 0x100098ea, 0), (3, 0x100098f0, 0x100098f6, 0),
                    ):
                        event(rd, "read", target_pointer + offset, (target_word >> (24 - 8 * offset)) & 255, 1)
                        event(wr, "write", target_pointer + offset, value, 1)
                literal(0x100098f9, 0x10005e24)
                literal(0x100098ff, 0x10005e38)
                out0_after_stall = supplied["out0"] | int(stall == 1)
                event(0x10009905, "read", literal_values[0x10005e24], out0_after_stall)
                event(0x10009907, "read", 0x1001bc50, bulk_size)
                event(0x1000990f, "write", literal_values[0x10005e24], out0_after_stall | 0x100)
                if bulk_size <= 512:
                    literal(0x10009917, 0x10005e70)
                    event(0x1000991d, "read", literal_values[0x10005e70], supplied["out1"])
                    event(0x10009925, "write", literal_values[0x10005e70], supplied["out1"] | 0x100)
                literal(0x10009928, 0x10005e64)
                event(0x1000992b, "write", 0x1001bc72, 0, 1)
                if rejected:
                    boundary = next(i for i, e in enumerate(events) if e["pc"] == hex(stop))
                    need(0xb0000000 <= int(events[boundary]["address"], 16) < 0xc0000000,
                         label + ": rejection addresses real peripheral space")
                    events = events[:boundary]

            after = {span: raw.copy() for span, raw in before.items()}
            for e in events:
                address, size, value = int(e["address"], 16), e["size"], int(e["value"], 16)
                need(not (address < 0xc0000000 and address + size > 0xb0000000), label + ": no accepted MMIO event")
                if e["kind"] == "write":
                    ram_put(after, address, value.to_bytes(size, "big"))
                else:
                    wanted = (literal_values[address] if address in literals and size == 4 else
                              int.from_bytes(ram_read(after, address, size), "big"))
                    need(value == wanted, label + ": independent read sees prior writes")

            # Complete retired-PC paths are conditional slices of the static
            # table. This excludes missing non-memory instructions as well.
            retired = [] if direct else [pc for pc in all_pcs if
                not (0x1000985f <= pc < 0x10009884 and stall != 1) and
                not (0x100098c2 <= pc < 0x100098f9 and owner != 2) and
                not (0x10009917 <= pc < 0x10009928 and bulk_size > 512) and pc < stop]
            need(not set(retired).intersection(excluded), label + ": no excluded instruction retired")
            registers = [(0x13579bdf + i * 0x10203 + seed * 0x01010101) & 0xffffffff for i in range(16)]
            registers[0:4] = [0xfffffffc, 0x2101fef0, stall, 0]
            for index, value in supplied.get("registers", {}).items():
                registers[int(index)] = value
            if not rejected:
                updates = {2: 0 if stall == 1 else stall, 6: 512, 8: 0x1001bc72,
                           9: 0x22a00140 if bulk_size <= 512 else bulk_size, 10: 256, 11: 0x22a00400}
            elif direct:
                updates = {}
                args = instructions[hex(stop)]["args"]
                need(0xb0000000 <= registers[args[1]] + args[2] < 0xc0000000,
                     label + ": direct guard supplied address")
            else:
                # Independently derived final registers *before* each rejected
                # instruction. The experiment itself only compared the engines
                # for these 14 prefixes; this gate also checks literal outcomes.
                partial = {
                    0x10009865: {6: 0xb3000200},
                    0x10009877: {6: 0x22a00100, 8: supplied["out0"] | 1, 9: 0xb3000000},
                    0x1000988d: {2: 0, 6: 0x22a00100, 8: 0xb3000300, 9: 0x22a00120},
                    0x10009896: {2: 0, 6: 0x22a00100, 8: 0xb3000214, 9: 0x22a00120},
                    0x10009898: {2: 0, 6: 0x22a00100, 8: 0x22a00160, 9: 0x22a00120, 11: 0xb3000300},
                    0x100098ca: {2: 0, 6: 0x22a00100, 8: 0xb3000300, 9: 0x80000000,
                                 10: status_word, 11: 0x22a00400},
                    0x1000991d: {2: 0, 6: 512, 8: supplied["out0"] | 0x101,
                                 9: 0xb3000220, 10: 256, 11: 0x22a00400},
                }
                updates = partial[stop]
            for index, value in updates.items():
                registers[index] = value
            registers = [hex(v) for v in registers]
            before_manifest, after_manifest = manifest(before), manifest(after)
            need(case["status"] == "pass", label + ": paired result status")
            for engine in ("interpreter", "qemu"):
                record = case[engine]
                where = label + ": " + engine
                reason = ("MMIO forbidden" if rejected else
                          ("execution outside selected stock routines: " if engine == "interpreter" else
                           "native tasks left selected code: ") + hex(stop))
                need(record["status"] == "pass" and record["engine"] == engine
                     and record["entry"] == hex(supplied.get("entry", 0x1000985c))
                     and record["stop_before"] == hex(stop)
                     and record["failure"] == dict(type="ValueError", reason=reason, pc=hex(stop)), where + ": stop/failure")
                need(record["registers"] == registers
                     and record["expected_registers"] == (None if rejected else registers)
                     and record["independent_final_registers_checked"] is (not rejected), where + ": exact registers")
                need(record["before_memory"] == before_manifest
                     and record["expected_memory"] == record["actual_memory"] == after_manifest,
                     where + ": entire original RAM, stack, redirects and guarded arena")
                need(record["expected_accesses"] == record["accesses"] == events,
                     where + ": all ordered reads/writes, including partial effects")
                need(all(record[field] == ram_read(after, address, 16).hex() for field, address in (
                    ("setup_record_hex", 0x22a00300), ("observed_record_hex", 0x22a00400),
                    ("other_record_hex", 0x22a00500))), where + ": record bytes and untouched packet words")
                need(record["original_instructions_retired"] == [hex(pc) for pc in retired]
                     and record["engine_steps"] == len(retired) + int(engine == "interpreter" and rejected),
                     where + ": exact retired instruction path and guard-before-execution")
                need(record["actual_peripheral_accesses"] == 0 and all(record[k] is True for k in (
                    "all_mutable_and_guard_ram_equal", "independent_ordered_read_and_write_trace_equal",
                    "original_code_unchanged")), where + ": capture assertions and zero peripheral access")

        need(report["excluded_code_controls"] == [dict(pc=hex(pc),
             status="rejected before instruction execution in both engines") for pc in excluded],
             "all 15 exact excluded-code boundary controls")
        need(report["status"] == "pass" and isinstance(report["qemu_version"], str)
             and report["qemu_version"].startswith("QEMU emulator version "), "completed differential report")
        need(all(report[k] == 0 for k in ("actual_peripheral_accesses", "completed_usb_control_transfers",
                                         "completed_native_page_lifecycles"))
             and report["original_entry_executed"] is False
             and report["omitted_startup_admission_dispatch_and_sender"] is True
             and report["hardware_stall_clear_established"] is False
             and report["controller_rearm_or_quiescence_established"] is False
             and report["supplied_services"] == [], "explicit omitted prefixes and zero hardware/physical claims")
        need(report["scope"] == (
            "Original post-dispatch tail, conditional on supplied a2 stall intent, a3 zero, globals and ordinary RAM control images. "
            "Exact SETUP-status return, separate owner-only OUT0 header reset, CNAK command intent and idle-latch clear; "
            "all mutable RAM, registers and ordered reads/writes agree in both engines."), "conditional scope statement")
        need(all(text in report["limits"] for text in (
            "No ENTRY, request admission/dispatch, sender, IRQ, event wait, timer, cache, controller or physical USB operation executes.",
            "Stores are plain RAM writes, not W1C or self-clearing hardware commands.",
            "This tail preserves an existing S bit; CNAK does not prove stall clearing or transfer settlement.",
            "Owner-only OUT0 rearm does not validate RX/count or establish safe reuse.",
            "Current SETUP bytes and older EP0 packet ownership remain separate responsibilities.",
            "Physical mapping, event ordering, rearm, stalls/toggles, cancellation, boot and printing remain unproved.",
        )), "material limitations retained")
        return True, detail
    except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration, struct.error) as error:
        return False, "SETUP retirement consistency failure: " + str(error)


def usb_irq_capture_consistency_gate(root):
    import ast
    import hashlib
    import json
    from pathlib import Path
    import re
    import struct

    root = Path(root)
    detail = (
        "44 conditional cuts and 38 pre-peripheral guards per engine must preserve "
        "separate sample/scan/wake boundaries, original suffix-mask selection, all "
        "ordered accesses, complete guarded RAM, registers/SAR and supplied native "
        "CPU state. All 75 excluded-PC controls remain pre-execution rejections. "
        "Saved pending bits, RAM acknowledgement intent and a proposed wake carry "
        "no physical event chronology, SETUP acquisition/overwrite protection, "
        "controller settlement or completed USB transfer."
    )

    def need(condition, label):
        if not condition:
            raise ValueError(label)

    def sha(raw):
        return hashlib.sha256(raw).hexdigest()

    try:
        report = json.loads((root / "analysis/usb-path/irq-capture.json").read_text())
        stock = (root / "analysis/sihp1020.elf").read_bytes()
        stock_sha = "2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d"
        need(report["stock_elf_sha256"] == sha(stock) == stock_sha, "pinned stock ELF")
        need(stock[:6] == b"\x7fELF\x01\x02", "ELF32 big-endian identity")
        shoff = struct.unpack_from(">I", stock, 32)[0]
        shsize, shnum, shstr = struct.unpack_from(">HHH", stock, 46)
        need(shsize == 40 and shstr < shnum and shoff + shsize * shnum <= len(stock), "ELF section bounds")
        headers = [struct.unpack_from(">10I", stock, shoff + i * 40) for i in range(shnum)]
        string_header = headers[shstr]
        names = stock[string_header[4]:string_header[4] + string_header[5]]
        sections = {names[h[0]:].split(b"\0", 1)[0].decode("ascii"): h for h in headers}
        need(sections[".text"][3:6] == (0x10005c80, 0x31e0, 0x15f0f), "pinned .text mapping")
        original_ram = tuple(sorted((h[3], h[3] + h[5]) for h in headers if h[2] & 3 == 3))
        need(original_ram == ((0x10000370, 0x1000049c), (0x1001bb90, 0x1001d640),
                              (0x1001d640, 0x100351e0)), "all original writable ELF sections")

        def original(address, size):
            need(0x10005c80 <= address < address + size <= 0x1001bb8f, "original byte address")
            offset = 0x31e0 + address - 0x10005c80
            return stock[offset:offset + size]

        phases = {
            "samples": dict(entry=0x10008208, code=[[0x10008208, 0x10008240]],
                            stops=[0x1000833c, 0x10008240], original_entry=True),
            "lanes": dict(entry=0x1000837e,
                code=[[0x1000837e, 0x100083cf], [0x100083e0, 0x1000841a],
                      [0x10008439, 0x1000845c], [0x100084a9, 0x100084b4],
                      [0x100084b7, 0x100084c5], [0x100086c3, 0x100086ed]],
                stops=[0x100084b4, 0x100084c5, 0x100086ed], original_entry=False),
            "out0_common_wake": dict(entry=0x100084c8,
                code=[[0x100084c8, 0x100084ce], [0x100086b0, 0x100086c0]],
                stops=[0x100086c0], original_entry=False),
        }
        need(report["phase_definitions"] == phases, "exact independent phase entries/ranges/stops")
        ranges = sorted(tuple(span) for p in phases.values() for span in p["code"])
        # Transcribed from pinned original disassembly, independently of the
        # experiment. Used for byte/operand metadata and fixed path blocks only.
        rows = """
10008208 6c1006 entry 1,48
1000820b 1af6f6 l32r 10,0x10005de4
1000820e 18f6f6 l32r 8,0x10005de8
10008211 0c0200 memw -
10008214 85a0 l32i.n 5,10,0
10008216 0c0200 memw -
10008219 8880 l32i.n 8,8,0
1000821b c098 movi.n 9,8
1000821d 9810 s32i.n 8,1,0
1000821f 795802 bany 5,9,0x10008225
10008222 600116 j 0x1000833c
10008225 18f6f1 l32r 8,0x10005dec
10008228 0c0200 memw -
1000822b 99a0 s32i.n 9,10,0
1000822d 0c0200 memw -
10008230 8980 l32i.n 9,8,0
10008232 280a10 movi 8,16
10008235 089701 and 7,9,8
10008238 ce78 bnez.n 7,0x10008264
1000823a 2a0a15 movi 10,21
1000823d 011102 or 1,1,1
1000837e c030 movi.n 3,0
10008380 c021 movi.n 2,1
10008382 d430 mov.n 4,3
10008384 18f69f l32r 8,0x10005e00
10008387 19f698 l32r 9,0x10005de8
1000838a 0c0200 memw -
1000838d 8a80 l32i.n 10,8,0
1000838f 8e10 l32i.n 14,1,0
10008391 c78f movi.n 8,-1
10008393 08aa03 xor 10,10,8
10008396 9a11 s32i.n 10,1,4
10008398 0c0200 memw -
1000839b 9e90 s32i.n 14,9,0
1000839d 8e11 l32i.n 14,1,4
1000839f c050 movi.n 5,0
100083a1 004004 ssr 4
100083a4 0e0819 srl 8,14
100083a7 08084f extui 8,8,0,16
100083aa 8e10 l32i.n 14,1,0
100083ac 9812 s32i.n 8,1,8
100083ae 004004 ssr 4
100083b1 0e0819 srl 8,14
100083b4 08084f extui 8,8,0,16
100083b7 9813 s32i.n 8,1,12
100083b9 8e12 l32i.n 14,1,8
100083bb 64e31c beqz 14,0x100086db
100083be 2e1203 l32i 14,1,12
100083c1 7fef02 bbsi 14,31,0x100083c7
100083c4 6002fb j 0x100086c3
100083c7 cd35 bnez.n 3,0x100083e0
100083c9 19f68e l32r 9,0x10005e04
100083cc 600013 j 0x100083e3
100083e0 19f68a l32r 9,0x10005e08
100083e3 0b5811 slli 8,5,5
100083e6 a987 add.n 7,8,9
100083e8 0c0200 memw -
100083eb 8670 l32i.n 6,7,0
100083ed 282a00 movi 8,512
100083f0 786004 bnone 6,8,0x100083f8
100083f3 0c0200 memw -
100083f6 9870 s32i.n 8,7,0
100083f8 280a80 movi 8,128
100083fb 786005 bnone 6,8,0x10008404
100083fe 0c0200 memw -
10008401 287600 s32i 8,7,0
10008404 c480 movi.n 8,64
10008406 78602f bnone 6,8,0x10008439
10008409 0c0200 memw -
1000840c 9870 s32i.n 8,7,0
1000840e 054808 add 8,4,5
10008411 008104 ssl 8
10008414 00281a sll 8,2
10008417 69821e bnei 8,2,0x10008439
10008439 c380 movi.n 8,48
1000843b 086801 and 8,6,8
1000843e c884 beqz.n 8,0x10008446
10008440 0c0200 memw -
10008443 287600 s32i 8,7,0
10008446 284a00 movi 8,1024
10008449 78606a bnone 6,8,0x100084b7
1000844c 0c0200 memw -
1000844f 9870 s32i.n 8,7,0
10008451 a548 add.n 8,4,5
10008453 008104 ssl 8
10008456 00271a sll 7,2
10008459 69724c bnei 7,2,0x100084a9
100084a9 1af65b l32r 10,0x10005e18
100084ac db70 mov.n 11,7
100084ae 2c0a00 movi 12,0
100084b1 011102 or 1,1,1
100084b7 683102 beqi 3,1,0x100084bd
100084ba 600205 j 0x100086c3
100084bd 18f657 l32r 8,0x10005e1c
100084c0 8a80 l32i.n 10,8,0
100084c2 011102 or 1,1,1
100084c8 685102 beqi 5,1,0x100084ce
100084cb 6001e1 j 0x100086b0
100086b0 1af5da l32r 10,0x10005e18
100086b3 a54b add.n 11,4,5
100086b5 00b104 ssl 11
100086b8 002b1a sll 11,2
100086bb c0c0 movi.n 12,0
100086bd 011102 or 1,1,1
100086c3 8e12 l32i.n 14,1,8
100086c5 b155 addi.n 5,5,1
100086c7 0e1e14 srli 14,14,1
100086ca 9e12 s32i.n 14,1,8
100086cc 8e13 l32i.n 14,1,12
100086ce c08f movi.n 8,15
100086d0 0e1e14 srli 14,14,1
100086d3 9e13 s32i.n 14,1,12
100086d5 758302 bltu 8,5,0x100086db
100086d8 63fcdd j 0x100083b9
100086db 244c10 addi 4,4,16
100086de 233c01 addi 3,3,1
100086e1 6f3202 bgeui 3,2,0x100086e7
100086e4 63fcb5 j 0x1000839d
100086e7 2a0a04 movi 10,4
100086ea 011102 or 1,1,1
"""
        instructions = {}
        for row in rows.strip().splitlines():
            at, encoded, op, operands = row.split()
            pc = int(at, 16)
            need(pc not in instructions, "unique independent instruction PC")
            instructions[pc] = dict(op=op, args=[] if operands == "-" else
                                    [int(x, 0) for x in operands.split(",")], bytes=encoded)
            need(original(pc, len(bytes.fromhex(encoded))).hex() == encoded, "independent instruction bytes")
        wanted_chunks, covered = [], set()
        for a, b in ranges:
            pc, table = a, {}
            while pc < b:
                instruction = instructions[pc]
                size = len(bytes.fromhex(instruction["bytes"]))
                need(size in (2, 3) and pc + size <= b, "complete selected instruction boundaries")
                table[hex(pc)] = instruction
                covered.add(pc)
                pc += size
            need(pc == b, "selected range closes exactly")
            raw = original(a, b - a)
            wanted_chunks.append(dict(begin=hex(a), end=hex(b), bytes=raw.hex(), sha256=sha(raw), instructions=table))
        need(covered == set(instructions), "no added or omitted instruction-table range")
        audit = report["original_byte_audit"]
        need(audit["chunks"] == wanted_chunks, "all original selected bytes/operands and range hashes")
        anchor_pcs = (0x10008208, 0x10008214, 0x10008219, 0x1000821d, 0x1000822b, 0x10008230,
                      0x1000838d, 0x1000839b, 0x100083bb, 0x100083c1, 0x100083eb, 0x100083f6,
                      0x10008401, 0x1000840c, 0x10008443, 0x1000844f, 0x100084c8, 0x100084cb,
                      0x100086b0, 0x100086db, 0x100086de)
        anchors = {hex(pc): [instructions[pc][k] for k in ("op", "args", "bytes")] for pc in anchor_pcs}
        anchors.update({
            "0x10008240": ["call8", [0x10011178], "5823cd"],
            "0x100084b4": ["call8", [0x10017dac], "583e3d"],
            "0x100084c5": ["call8", [0x10007c5c], "5bfde5"],
            "0x100086c0": ["call8", [0x10017dac], "583dba"],
            "0x100086ed": ["call8", [0x100171e0], "583abc"],
            "0x10007c69": ["call8", [0x10017dac], "584050"],
        })
        need(audit["anchors"] == anchors and all(original(int(a, 16), len(bytes.fromhex(v[2]))).hex() == v[2]
             for a, v in anchors.items()), "exact static call and branch anchors")
        literals = {0x10005de4: 0xb300040c, 0x10005de8: 0xb3000414, 0x10005dec: 0xb3010004,
                    0x10005e00: 0xb3000418, 0x10005e04: 0xb3000004, 0x10005e08: 0xb3000204,
                    0x10005e18: 0x10021318, 0x10005e1c: 0x100212d4}
        need(audit["literal_originals"] == {hex(a): hex(v) for a, v in literals.items()}
             and all(original(a, 4) == v.to_bytes(4, "big") for a, v in literals.items()), "all original literal words")
        redirect_by_phase = {
            "samples": {0x10005de4: 0x22b00100, 0x10005de8: 0x22b00120, 0x10005dec: 0x22b00140},
            "lanes": {0x10005de8: 0x22b00120, 0x10005e00: 0x22b00160,
                      0x10005e04: 0x22b00400, 0x10005e08: 0x22b00800},
            "out0_common_wake": {},
        }
        reference_dir = "analysis/usb-path/controller-reference/linux-v6.12/"
        commit = "adc218676eef25575469234709c2d87185ca223a"
        reference_sha = {
            "amd5536udc.h": "8dbf2ebffe7de042bdfea1c5e4e0d7e7ca334cb821fbfaa1cf9ccfeeae302648",
            "snps_udc_core.c": "c1b09e8f69d3340f2afd3a033d77a42775b52716d45b1aceb211dcaab89127bf",
            "provenance.json": "023d10e246e4852c1b9415cdc3d591006edcedeba467a56b95b22b994d4a08e4",
        }
        need(audit["linux_commit"] == commit and audit["linux_source_sha256"] == reference_sha
             and all(sha((root / reference_dir / n).read_bytes()) == h for n, h in reference_sha.items()),
             "immutable Linux reference bytes")
        provenance = json.loads((root / reference_dir / "provenance.json").read_text())
        need(provenance["repository"] == "https://github.com/torvalds/linux"
             and provenance["requested_ref"] == "v6.12" and provenance["commit"] == commit, "Linux provenance pin")
        for name in ("amd5536udc.h", "snps_udc_core.c"):
            path = "drivers/usb/gadget/udc/" + name
            records = [r for r in provenance["files"] if r["path"] == path]
            need(len(records) == 1 and records[0]["sha256"] == reference_sha[name]
                 and records[0]["bytes"] == len((root / reference_dir / name).read_bytes())
                 and records[0]["url"] == f"https://raw.githubusercontent.com/torvalds/linux/{commit}/{path}",
                 "reference path/length/hash/URL: " + name)
        header = (root / reference_dir / "amd5536udc.h").read_text()
        for name, value in (("UDC_DEVINT_UR", "3"), ("UDC_DEVINT_ADDR", "0x40c"),
                            ("UDC_EPINT_ADDR", "0x414"), ("UDC_EPINT_MSK_ADDR", "0x418"),
                            ("UDC_EPSTS_TDC", "10"), ("UDC_EPSTS_OUT_SETUP_CLEAR", "0x20")):
            need(re.search(r"^#define\s+" + name + r"\s+" + value + r"\s*$", header, re.M), "reference definition: " + name)

        generator = "scripts/validate-hp1020-usb-irq-capture.py"
        sources = {generator, "analysis/sihp1020.elf", *(reference_dir + n for n in reference_sha),
                   *("scripts/" + n + ".py" for n in (
                       "hp1020_qemu_multitask", "hp1020_qemu_ram", "hp1020_qemu_stock_parser",
                       "hp1020_stock_parser_harness", "hp1020_stock_stop", "hp1020_xtensa_call0",
                       "hp1020_xtensa_properties", "hp1020_xtensa_stock"))}
        need(len(sources) == 13 and set(report["source_sha256"]) == set(report["source_origins"]) == sources,
             "exact 13-source closure")
        need(all(sha((root / name).read_bytes()) == digest for name, digest in report["source_sha256"].items()),
             "current source bytes equal tested closure")
        need(all(isinstance(origin, str) and Path(origin).is_absolute() and Path(origin).as_posix().endswith("/" + name)
                 for name, origin in report["source_origins"].items()), "source origin labels")
        pending, imported = [generator], set()
        while pending:
            name = pending.pop()
            if name in imported:
                continue
            imported.add(name)
            for node in ast.walk(ast.parse((root / name).read_text())):
                modules = ([n.name for n in node.names] if isinstance(node, ast.Import) else
                           [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
                for module in modules:
                    dependency = "scripts/" + module.split(".", 1)[0] + ".py"
                    if (root / dependency).is_file() and dependency not in imported:
                        pending.append(dependency)
        need(imported == {n for n in sources if n.endswith(".py")}, "closed local import set without executing it")

        # Scope/schema comes from the proposed fixture; the literal visit plans
        # and effects below were derived separately from the original bytes.
        def base(phase, name, fill):
            return dict(phase=phase, name=name, kind="conditional_phase", fill=fill,
                        devint=8, epint=0x30001, live_epint=0xa5c31234 ^ (fill * 0x01010101),
                        wrapper=0x96a50020, endpoint_mask=0xfffcfffe,
                        in0_status=0x400, out0_status=0x20, out1_status=0x10,
                        transfer_handle=0x5a000008 ^ (fill << 16))

        profiles = (
            ("no-pending", dict(epint=0)),
            ("in0-tdc", dict(epint=1)),
            ("in0-no-tdc", dict(epint=1, in0_status=0)),
            ("out0-setup", dict(epint=0x10000)),
            ("out0-data", dict(epint=0x10000, out0_status=0x10)),
            ("out0-setup-tdc", dict(epint=0x10000, out0_status=0x420)),
            ("out1-data", dict(epint=0x20000)),
            ("in0-out0-co-pending", dict(epint=0x10001)),
            ("in0-no-tdc-then-out0", dict(epint=0x10001, in0_status=0x40)),
            ("out0-out1-co-pending", dict(epint=0x30000)),
            ("out0-all-flags", dict(epint=0x10000, out0_status=0x6f0)),
            ("out0-errors-without-tdc", dict(epint=0x10000, out0_status=0x2f0)),
            ("out0-zero-status", dict(epint=0x10000, out0_status=0)),
            ("conditional-out0-masked-out1-enabled", dict(epint=0x10000, endpoint_mask=0xfffdffff)),
            ("conditional-out0-masked-with-tdc", dict(epint=0x10000, endpoint_mask=0xfffdffff, out0_status=0x420)),
            ("conditional-out1-above-last-enabled", dict(epint=0x20000, endpoint_mask=0xfffeffff)),
            ("conditional-all-out-masked", dict(epint=0x10000, endpoint_mask=0xfffffffe)),
        )
        removed = (
            ("samples", 0x10005de4, 0x10008214, 0x30001),
            ("samples", 0x10005de8, 0x10008219, 0x30001),
            ("samples", 0x10005dec, 0x10008230, 0x30001),
            ("lanes", 0x10005e00, 0x1000838d, 1),
            ("lanes", 0x10005de8, 0x1000839b, 1),
            ("lanes", 0x10005e04, 0x100083eb, 1),
            ("lanes", 0x10005e08, 0x100083eb, 0x10000),
        )
        direct_guards = (
            ("samples", "devint-read", 0x10008214, 10, 0xb300040c),
            ("samples", "epint-read", 0x10008219, 8, 0xb3000414),
            ("samples", "reset-ack-write", 0x1000822b, 10, 0xb300040c),
            ("samples", "wrapper-read", 0x10008230, 8, 0xb3010004),
            ("lanes", "endpoint-mask-read", 0x1000838d, 8, 0xb3000418),
            ("lanes", "saved-epint-ack-write", 0x1000839b, 9, 0xb3000414),
            ("lanes", "lane-status-read", 0x100083eb, 7, 0xb3000204),
            ("lanes", "he-ack-write", 0x100083f6, 7, 0xb3000204),
            ("lanes", "bna-ack-write", 0x10008401, 7, 0xb3000204),
            ("lanes", "in-ack-write", 0x1000840c, 7, 0xb3000204),
            ("lanes", "out-type-ack-write", 0x10008443, 7, 0xb3000204),
            ("lanes", "tdc-ack-write", 0x1000844f, 7, 0xb3000204),
        )
        inputs = []
        for fill in (0, 204):
            for reset in (0, 8):
                for saved in (0, 0x30001):
                    case = base("samples", f"samples-f{fill}-reset{reset}-ep{saved:x}", fill)
                    case.update(devint=reset, epint=saved)
                    inputs.append(case)
            for name, fields in profiles:
                case = base("lanes", f"lanes-f{fill}-{name}", fill)
                case.update(fields, profile=name)
                inputs.append(case)
            inputs.append(base("out0_common_wake", f"out0-common-wake-f{fill}", fill))
            for phase, literal, pc, saved in removed:
                case = base(phase, f"unredirected-{literal:x}-{phase}-f{fill}", fill)
                case.update(kind="removed_literal_redirect", skip_literal=literal, reject_pc=pc, epint=saved)
                inputs.append(case)
            for phase, name, pc, register, address in direct_guards:
                case = base(phase, f"guard-{name}-f{fill}", fill)
                case.update(kind="standalone_peripheral_instruction", entry=pc, reject_pc=pc,
                            registers={str(register): address})
                inputs.append(case)
        need(len(inputs) == 82 and len({c["name"] for c in inputs}) == 82
             and [c["input"] for c in report["cases"]] == inputs
             and report["counts"] == dict(samples=8, lanes=34, out0_common_wake=2,
                                           removed_redirect=14, standalone_mmio=24), "exact ordered 82-case matrix")

        excluded_common = {0x10008240, 0x10008264, 0x1000829f, 0x100082c6, 0x100082f0,
            0x100083d4, 0x1000841a, 0x10008428, 0x10008470, 0x100084b4, 0x100084c5,
            0x100084ce, 0x100086ad, 0x100086c0, 0x100086ed, 0x10007c5c, 0x10017dac,
            0x10011178, 0x1001bb5c, 0x100171e0, 0x100086f4, 0x1000935b, 0x10009884}
        excluded = {name: sorted(excluded_common | {other["entry"] for n, other in phases.items() if n != name})
                    for name in phases}
        excluded_rows = [dict(phase=name, pc=hex(pc), status="rejected before instruction execution in both engines")
                         for name in phases for pc in excluded[name]]
        need(len(excluded_rows) == 75 and report["excluded_code_controls"] == excluded_rows
             and all(not any(a <= pc < b for a, b in phases[name]["code"])
                     for name in phases for pc in excluded[name]), "all 75 exact pre-execution phase exclusions")

        # Literal endpoint visits: each direction supplies (E-half, P-half,
        # visits), each visit is (index, remaining E, remaining P, action).
        # 'zero' never reads P; 'skip' advances; 'in' reads IN0 then advances;
        # 'event'/'out' stop before the corresponding original call.
        in_empty = (1, 0, ((0, 1, 0, "skip"), (1, 0, 0, "zero")))
        in_masked = (0, 0, ((0, 0, 0, "zero"),))
        in_event = (1, 1, ((0, 1, 1, "event"),))
        in_continue = (1, 1, ((0, 1, 1, "in"), (1, 0, 0, "zero")))
        out_empty = (3, 0, ((0, 3, 0, "skip"), (1, 1, 0, "skip"), (2, 0, 0, "zero")))
        plans = {
            "no-pending": (in_empty, out_empty),
            "in0-tdc": (in_event,),
            "in0-no-tdc": (in_continue, out_empty),
            "out0-setup": (in_empty, (3, 1, ((0, 3, 1, "out"),))),
            "out0-data": (in_empty, (3, 1, ((0, 3, 1, "out"),))),
            "out0-setup-tdc": (in_empty, (3, 1, ((0, 3, 1, "event"),))),
            "out1-data": (in_empty, (3, 2, ((0, 3, 2, "skip"), (1, 1, 1, "out")))),
            "in0-out0-co-pending": (in_event,),
            "in0-no-tdc-then-out0": (in_continue, (3, 1, ((0, 3, 1, "out"),))),
            "out0-out1-co-pending": (in_empty, (3, 3, ((0, 3, 3, "out"),))),
            "out0-all-flags": (in_empty, (3, 1, ((0, 3, 1, "event"),))),
            "out0-errors-without-tdc": (in_empty, (3, 1, ((0, 3, 1, "out"),))),
            "out0-zero-status": (in_empty, (3, 1, ((0, 3, 1, "out"),))),
            "conditional-out0-masked-out1-enabled": (in_masked, (2, 1, ((0, 2, 1, "out"),))),
            "conditional-out0-masked-with-tdc": (in_masked, (2, 1, ((0, 2, 1, "event"),))),
            "conditional-out1-above-last-enabled": (in_masked, (1, 2, ((0, 1, 2, "skip"), (1, 0, 1, "zero")))),
            "conditional-all-out-masked": (in_empty, (0, 1, ((0, 0, 1, "zero"),))),
        }
        selection = {
            "no-pending": (0x100086ed, (), None),
            "in0-tdc": (0x100084b4, (0x22b00400,), 1),
            "in0-no-tdc": (0x100086ed, (0x22b00400,), None),
            "out0-setup": (0x100084c5, (0x22b00800,), None),
            "out0-data": (0x100084c5, (0x22b00800,), None),
            "out0-setup-tdc": (0x100084b4, (0x22b00800,), 0x10000),
            "out1-data": (0x100084c5, (0x22b00820,), None),
            "in0-out0-co-pending": (0x100084b4, (0x22b00400,), 1),
            "in0-no-tdc-then-out0": (0x100084c5, (0x22b00400, 0x22b00800), None),
            "out0-out1-co-pending": (0x100084c5, (0x22b00800,), None),
            "out0-all-flags": (0x100084b4, (0x22b00800,), 0x10000),
            "out0-errors-without-tdc": (0x100084c5, (0x22b00800,), None),
            "out0-zero-status": (0x100084c5, (0x22b00800,), None),
            "conditional-out0-masked-out1-enabled": (0x100084c5, (0x22b00800,), None),
            "conditional-out0-masked-with-tdc": (0x100084b4, (0x22b00800,), 0x10000),
            "conditional-out1-above-last-enabled": (0x100086ed, (), None),
            "conditional-all-out-masked": (0x100086ed, (), None),
        }

        spans = original_ram + ((0x21000000, 0x21020000), (0x22b00000, 0x22b02000))
        templates = {(fill, a, b): bytes((fill + (a >> 8) + i * 17 + (i >> 4) * 3) & 255
                                       for i in range(b - a))
                     for fill in (0, 204) for a, b in spans}
        all_pcs = sorted(instructions)
        sp = 0x2101fef0

        def read_ram(memory, address, size):
            for (a, b), raw in memory.items():
                if a <= address and address + size <= b:
                    return bytes(raw[address - a:address - a + size])
            raise ValueError("independent oracle read outside RAM: " + hex(address))

        def put_ram(memory, address, data):
            for (a, b), raw in memory.items():
                if a <= address and address + len(data) <= b:
                    raw[address - a:address - a + len(data)] = data
                    return
            raise ValueError("independent oracle write outside RAM: " + hex(address))

        def manifest(memory):
            return [dict(begin=hex(a), end=hex(b), bytes=b - a, sha256=sha(raw))
                    for (a, b), raw in sorted(memory.items())]

        for paired, case in zip(report["cases"], inputs):
            label, phase, fill = case["name"], case["phase"], case["fill"]
            direct = case["kind"] == "standalone_peripheral_instruction"
            rejected = "reject_pc" in case
            original_entry = phase == "samples" and not direct
            literal_values = dict(literals)
            before = {(a, b): bytearray(templates[fill, a, b]) for a, b in spans}
            if not direct:
                for address, value in redirect_by_phase[phase].items():
                    if address != case.get("skip_literal"):
                        before[address, address + 4] = bytearray(value.to_bytes(4, "big"))
                        literal_values[address] = value
            for address, value in (
                (0x22b00100, case["devint"]),
                (0x22b00120, case["epint"] if phase == "samples" else case["live_epint"]),
                (0x22b00140, case["wrapper"]), (0x22b00160, case["endpoint_mask"]),
                (0x22b00400, case["in0_status"]), (0x22b00800, case["out0_status"]),
                (0x22b00820, case["out1_status"]), (0x100212d4, case["transfer_handle"]),
                (0x1001bbc0, 0x22b00d00), (0x1001bc48, 0x22b00e00),
            ):
                put_ram(before, address, value.to_bytes(4, "big"))
            put_ram(before, 0x22b00d00, bytes.fromhex("8e123456d3c2b1a0a100341256789abc"))
            put_ram(before, 0x22b00e00, bytes.fromhex("800000400123456789abcdef76543210"))
            if phase == "lanes":
                put_ram(before, sp, case["epint"].to_bytes(4, "big"))

            initial_registers = [(0x13579bdf + i * 0x10203 + fill * 0x01010101) & 0xffffffff for i in range(16)]
            initial_registers[0:2] = [0xfffffffc, sp]
            if phase == "out0_common_wake":
                initial_registers[2:6] = [1, 1, 16, 0]
            for index, value in case.get("registers", {}).items():
                initial_registers[int(index)] = value
            events, path, updates = [], [], {}
            sar, proposed, stop = 0, None, None

            def event(pc, kind, address, value):
                events.append(dict(pc=hex(pc), kind=kind, address=hex(address), size=4, value=hex(value)))

            def literal(pc, address):
                event(pc, "read", address, literal_values[address])

            def block(a, b):
                # Append independently transcribed PCs, including repeated loop
                # blocks. No instruction is interpreted and no report PC is used.
                pcs = [pc for pc in all_pcs if a <= pc < b]
                need(pcs and pcs[0] == a and pcs[-1] + len(bytes.fromhex(instructions[pcs[-1]]["bytes"])) == b,
                     label + ": fixed path block bounds")
                path.extend(pcs)

            if direct:
                stop = case["reject_pc"]
                args = instructions[stop]["args"]
                address = initial_registers[args[1]] + args[2]
                need(0xb0000000 <= address < 0xc0000000, label + ": standalone guard pointer")
            elif phase == "samples":
                d, p, w = case["devint"], case["epint"], case["wrapper"]
                block(0x10008208, 0x10008222)
                literal(0x1000820b, 0x10005de4)
                literal(0x1000820e, 0x10005de8)
                event(0x10008214, "read", literal_values[0x10005de4], d)
                event(0x10008219, "read", literal_values[0x10005de8], p)
                event(0x1000821d, "write", sp - 48, p)
                updates = {1: sp - 48, 5: d, 8: p, 9: 8, 10: literal_values[0x10005de4]}
                if d & 8:
                    need(w & 0x10 == 0, label + ": supplied wrapper condition")
                    block(0x10008225, 0x10008240)
                    literal(0x10008225, 0x10005dec)
                    event(0x1000822b, "write", literal_values[0x10005de4], 8)
                    event(0x10008230, "read", literal_values[0x10005dec], w)
                    updates.update({7: 0, 8: 16, 9: w, 10: 21})
                    stop, proposed = 0x10008240, dict(target="0x10011178", a10=21)
                else:
                    block(0x10008222, 0x10008225)
                    stop = 0x1000833c
            elif phase == "out0_common_wake":
                block(0x100084c8, 0x100084ce)
                block(0x100086b0, 0x100086c0)
                literal(0x100086b0, 0x10005e18)
                updates, sar = {10: 0x10021318, 11: 0x10000, 12: 0}, 16
                stop, proposed = 0x100086c0, dict(target="0x10017dac", a10=0x10021318, a11=0x10000, a12=0)
            else:
                # Removed-redirect profiles use exactly these underlying visits;
                # the trace is truncated before their first forbidden access.
                profile = case.get("profile", "in0-tdc" if case["epint"] == 1 else "out0-setup")
                plan = plans[profile]
                p, e = case["epint"], case["endpoint_mask"] ^ 0xffffffff
                block(0x1000837e, 0x1000839d)
                literal(0x10008384, 0x10005e00)
                literal(0x10008387, 0x10005de8)
                event(0x1000838d, "read", literal_values[0x10005e00], case["endpoint_mask"])
                event(0x1000838f, "read", sp, p)
                event(0x10008396, "write", sp + 4, e)
                event(0x1000839b, "write", literal_values[0x10005de8], p)
                last_status = None
                for direction, (enabled_half, pending_half, visits) in enumerate(plan):
                    need(enabled_half == ((e >> (16 * direction)) & 0xffff)
                         and pending_half == ((p >> (16 * direction)) & 0xffff), label + ": literal direction plan")
                    block(0x1000839d, 0x100083b9)
                    event(0x1000839d, "read", sp + 4, e)
                    event(0x100083aa, "read", sp, p)
                    event(0x100083ac, "write", sp + 8, enabled_half)
                    event(0x100083b7, "write", sp + 12, pending_half)
                    for index, enabled_tail, pending_tail, action in visits:
                        need(enabled_tail == enabled_half >> index and pending_tail == pending_half >> index,
                             label + ": fixed shifted visit words")
                        block(0x100083b9, 0x100083be)
                        event(0x100083b9, "read", sp + 8, enabled_tail)
                        if action == "zero":
                            need(enabled_tail == 0, label + ": literal zero-mask exit")
                            block(0x100086db, 0x100086e4)
                            if direction == 0:
                                block(0x100086e4, 0x100086e7)
                            else:
                                block(0x100086e7, 0x100086ed)
                                stop, proposed, sar = 0x100086ed, dict(target="0x100171e0", a10=4), 16
                                updates = {2: 1, 3: 2, 4: 32, 5: index,
                                           8: 15 if index else pending_half, 9: literal_values[0x10005de8],
                                           10: 4, 14: 0}
                                if last_status is not None:
                                    need(last_status[0:2] == (0, 0), label + ": only IN0 can continue past status")
                                    updates.update({6: last_status[2], 7: literal_values[0x10005e04],
                                                    9: literal_values[0x10005e04]})
                            continue
                        need(enabled_tail != 0, label + ": nonzero remaining enabled word")
                        block(0x100083be, 0x100083c4)
                        event(0x100083be, "read", sp + 12, pending_tail)
                        if action == "skip":
                            need(pending_tail & 1 == 0, label + ": literal absent pending bit")
                            block(0x100083c4, 0x100083c7)
                        else:
                            need(action in ("in", "out", "event") and pending_tail & 1,
                                 label + ": literal selected endpoint")
                            block(0x100083c7, 0x100083c9)
                            if direction == 0:
                                block(0x100083c9, 0x100083cf)
                                literal(0x100083c9, 0x10005e04)
                                status_base = literal_values[0x10005e04]
                                t = case["in0_status"]
                                need(index == 0, label + ": IN0-only profile")
                            else:
                                block(0x100083e0, 0x100083e3)
                                literal(0x100083e0, 0x10005e08)
                                status_base = literal_values[0x10005e08]
                                need(index in (0, 1), label + ": bounded OUT profile")
                                t = case["out0_status"] if index == 0 else case["out1_status"]
                            status_address = status_base + index * 32
                            last_status = (direction, index, t)
                            block(0x100083e3, 0x100083f3)
                            event(0x100083eb, "read", status_address, t)
                            if t & 0x200:
                                block(0x100083f3, 0x100083f8)
                                event(0x100083f6, "write", status_address, 0x200)
                            block(0x100083f8, 0x100083fe)
                            if t & 0x80:
                                block(0x100083fe, 0x10008404)
                                event(0x10008401, "write", status_address, 0x80)
                            block(0x10008404, 0x10008409)
                            if t & 0x40:
                                block(0x10008409, 0x1000841a)
                                event(0x1000840c, "write", status_address, 0x40)
                            block(0x10008439, 0x10008440)
                            if t & 0x30:
                                block(0x10008440, 0x10008446)
                                event(0x10008443, "write", status_address, t & 0x30)
                            block(0x10008446, 0x1000844c)
                            if action == "event":
                                need(t & 0x400, label + ": independently selected TDC boundary")
                                block(0x1000844c, 0x1000845c)
                                event(0x1000844f, "write", status_address, 0x400)
                                block(0x100084a9, 0x100084b4)
                                literal(0x100084a9, 0x10005e18)
                                bit = 1 << (16 * direction + index)
                                updates = {2: 1, 3: direction, 4: 16 * direction, 5: index,
                                           6: t, 7: bit, 8: 16 * direction + index, 9: status_base,
                                           10: 0x10021318, 11: bit, 12: 0, 14: pending_tail}
                                sar = 32 - ((16 * direction + index) & 31)
                                stop, proposed = 0x100084b4, dict(target="0x10017dac", a10=0x10021318, a11=bit, a12=0)
                                continue
                            need(t & 0x400 == 0, label + ": no hidden TDC branch")
                            block(0x100084b7, 0x100084ba)
                            if action == "out":
                                need(direction == 1, label + ": OUT-helper direction")
                                block(0x100084bd, 0x100084c5)
                                literal(0x100084bd, 0x10005e1c)
                                event(0x100084c0, "read", 0x100212d4, case["transfer_handle"])
                                updates = {2: 1, 3: 1, 4: 16, 5: index, 6: t, 7: status_address,
                                           8: 0x100212d4, 9: status_base, 10: case["transfer_handle"], 14: pending_tail}
                                sar = 32 - ((16 + index) & 31) if t & 0x40 else 16
                                stop, proposed = 0x100084c5, dict(target="0x10007c5c", a10=case["transfer_handle"])
                                continue
                            need(action == "in" and direction == 0, label + ": continuing IN0 path")
                            block(0x100084ba, 0x100084bd)
                        # A literal skip or non-TDC IN0 advances exactly once.
                        block(0x100086c3, 0x100086db)
                        event(0x100086c3, "read", sp + 8, enabled_tail)
                        event(0x100086ca, "write", sp + 8, enabled_tail >> 1)
                        event(0x100086cc, "read", sp + 12, pending_tail)
                        event(0x100086d3, "write", sp + 12, pending_tail >> 1)
                expected_stop, status_reads, expected_event = selection[profile]
                need(stop == expected_stop and tuple(int(e["address"], 16) for e in events if e["pc"] == "0x100083eb") ==
                     tuple((literal_values[0x10005e04] if a == 0x22b00400 else
                            literal_values[0x10005e08] + a - 0x22b00800) for a in status_reads),
                     label + ": separate literal lane selection")
                if expected_event is not None:
                    need(proposed == dict(target="0x10017dac", a10=0x10021318, a11=expected_event, a12=0),
                         label + ": separate literal event mask")

            if rejected and not direct:
                stop = case["reject_pc"]
                event_boundary = next(i for i, e in enumerate(events) if e["pc"] == hex(stop))
                need(0xb0000000 <= int(events[event_boundary]["address"], 16) < 0xc0000000,
                     label + ": removed redirect reaches peripheral guard")
                events = events[:event_boundary]
                path = path[:path.index(stop)]
                proposed, sar = None, 0
                if phase == "samples":
                    partial = {
                        0x10008214: {1: sp - 48, 8: 0x22b00120, 10: 0xb300040c},
                        0x10008219: {1: sp - 48, 5: 8, 8: 0xb3000414, 10: 0x22b00100},
                        0x10008230: {1: sp - 48, 5: 8, 8: 0xb3010004, 9: 8, 10: 0x22b00100},
                    }
                    updates = partial[stop]
                elif stop == 0x1000838d:
                    updates = {2: 1, 3: 0, 4: 0, 8: 0xb3000418, 9: 0x22b00120}
                elif stop == 0x1000839b:
                    updates = {2: 1, 3: 0, 4: 0, 8: 0xffffffff, 9: 0xb3000414,
                               10: 0x30001, 14: 1}
                else:
                    need(stop == 0x100083eb, label + ": known partial lane boundary")
                    direction = int(case["skip_literal"] == 0x10005e08)
                    address = 0xb3000204 if direction else 0xb3000004
                    updates = {2: 1, 3: direction, 4: direction * 16, 5: 0, 7: address,
                               8: 0, 9: address, 10: 0x30001, 14: 1}
                    sar = direction * 16

            need(stop is not None and stop not in path and all(
                 pc not in excluded[phase] and any(a <= pc < b for a, b in phases[phase]["code"]) for pc in path),
                 label + ": exact phase-contained path stops before excluded code")
            after = {span: raw.copy() for span, raw in before.items()}
            for e in events:
                address, value = int(e["address"], 16), int(e["value"], 16)
                need(not (address < 0xc0000000 and address + 4 > 0xb0000000), label + ": no accepted peripheral access")
                need(all(address + 4 <= lo or address >= hi for lo, hi in (
                    (0x22b00d00, 0x22b00d10), (0x22b00e00, 0x22b00e10),
                    (0x1001bbc0, 0x1001bbc4), (0x1001bc48, 0x1001bc4c),
                    (0x90021340, 0x90021350))), label + ": no acquisition or ownership return")
                if e["kind"] == "write":
                    put_ram(after, address, value.to_bytes(4, "big"))
                else:
                    wanted = literal_values[address] if address in literals else int.from_bytes(read_ram(after, address, 4), "big")
                    need(value == wanted, label + ": ordered read sees independent prior RAM writes")
            registers = initial_registers.copy()
            for index, value in updates.items():
                registers[index] = value
            register_hex = [hex(value) for value in registers]
            before_manifest, after_manifest = manifest(before), manifest(after)
            cpu = dict(processor_status=0x40000 if original_entry else 0,
                       windowbase=0, windowstart=1, sar=sar, lbeg=0, lend=0, lcount=0)
            need(paired["status"] == "pass", label + ": paired status")
            for engine in ("interpreter", "qemu"):
                result = paired[engine]
                where = label + ": " + engine
                reason = ("MMIO forbidden" if rejected else
                          ("execution outside selected stock routines: " if engine == "interpreter" else
                           "native tasks left selected code: ") + hex(stop))
                need(result["status"] == "pass" and result["engine"] == engine and result["phase"] == phase
                     and result["entry"] == hex(case.get("entry", phases[phase]["entry"]))
                     and result["stop_before"] == hex(stop)
                     and result["failure"] == dict(type="ValueError", reason=reason, pc=hex(stop)), where + ": exact stop/failure")
                need(result["registers"] == result["expected_registers"] == register_hex
                     and result["sar"] == result["expected_sar"] == sar
                     and result["proposed_call"] == proposed, where + ": independent registers/SAR/pre-call proposal")
                need(result["expected_native_cpu_state"] == cpu
                     and result["native_cpu_state"] == (cpu if engine == "qemu" else None)
                     and result["interpreter_models_physical_window_registers"] is False,
                     where + ": distinct native special-register evidence")
                need(result["before_memory"] == before_manifest
                     and result["expected_memory"] == result["actual_memory"] == after_manifest
                     and result["accesses"] == result["expected_accesses"] == events,
                     where + ": entire RAM/stack/redirect guards and exact ordered accesses")
                need(result["setup_record_hex"] == "8e123456d3c2b1a0a100341256789abc"
                     and result["bulk_record_hex"] == "800000400123456789abcdef76543210",
                     where + ": byte-exact untouched acquisition canaries")
                need(result["original_instructions_retired"] == [hex(pc) for pc in sorted(set(path))]
                     and result["engine_steps"] == len(path) + int(engine == "interpreter" and rejected)
                     and result["original_entry_executed"] is original_entry
                     and (0x10008208 in path) is original_entry,
                     where + ": full path coverage, repeated step count and ENTRY separation")
                need(all(result[k] is True for k in (
                    "independent_full_registers_equal", "independent_ordered_accesses_equal", "all_mutable_ram_equal",
                    "no_setup_record_or_pointer_access", "no_record_ownership_return", "original_code_unchanged"))
                     and result["omitted_helpers_executed"] is False
                     and result["actual_peripheral_accesses"] == result["completed_usb_transfers"] == 0,
                     where + ": bounded evidence and zero hardware/helper execution")

        need(report["status"] == "pass" and isinstance(report["qemu_version"], str)
             and report["qemu_version"].startswith("QEMU emulator version "), "completed paired report")
        need(report["original_entry_executed_only_in_samples"] is True and report["independent_phases"] is True
             and report["original_entry_supplied_cpu"] == dict(ps_woe=1, ps_callinc=0, windowbase=0,
                 windowstart=1, initial_sar=0, stack_adjustment=48, synthetic_caller_executed=False,
                 actual_interrupt_entry_established=False), "conditional CPU setup and unconnected phases")
        need(report["omitted_helpers_executed"] is False and report["supplied_services"] == []
             and all(report[k] == 0 for k in ("actual_peripheral_accesses", "completed_usb_control_transfers",
                                              "completed_native_page_lifecycles"))
             and all(report[k] is False for k in ("physical_event_order_established", "coherent_setup_capture_established",
                                                   "overwrite_prevention_established", "controller_settlement_established")),
             "explicit physical, acquisition and lifecycle exclusions")
        need(report["scope"] == (
            "Three independent original-instruction RAM cuts: ordered DEVINT/EPINT sampling and reset-ack intent; "
            "literal endpoint acknowledgements and pre-call lane selection; a separately seeded OUT0 common-wake proposal. "
            "Complete RAM, ordered accesses and all logical registers/SAR are checked against supplied-state oracles."),
             "independent-cut scope statement")
        need(all(s in report["limits"] for s in (
            "No uninterrupted IRQ lifecycle is executed.",
            "Only the prefix runs original ENTRY, from supplied WOE1/CALLINC0/WB0/WS1 with no artificial caller; this is not actual interrupt entry.",
            "Later phases begin with explicit registers/stack and no ENTRY.",
            "No configuration, timer, kernel, wakeup, bulk service/rearm, request dispatch or descriptor return helper executes.",
            "Peripheral literals point to private RAM; stores do not model W1C, timing, DMA, masks, cache visibility or physical interrupts.",
            "A mask/pending mismatch is a conditional software predicate, not a demonstrated reachable hardware bug or lost event.",
            "Co-pending bits and scan order provide no chronology or reset generation for SETUP.",
            "No selected cut acquires/copies/returns the SETUP record;",
            "No real USB completion, physical cancellation, hardware stall clearing, boot or printing is established.",
        )), "material evidence limits retained")
        return True, detail
    except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration, struct.error) as error:
        return False, "IRQ capture consistency failure: " + str(error)


def usb_offload_consistency_gate(root, capture_root=None):
    """Check saved evidence; optional capture_root also seals raw saved files."""
    import hashlib
    import json
    import re
    from pathlib import Path

    root = Path(root)
    path = root / 'analysis/usb-path/udc-offload/validation.json'
    bad = set()

    def need(value, reason):
        if not value:
            bad.add(reason)

    def packed(words):
        return b''.join(v.to_bytes(4, 'big') for v in words)

    def digest(raw):
        return hashlib.sha256(raw).hexdigest()

    def fnv(raw):
        value = 2166136261
        for byte in raw:
            value = ((value ^ byte) * 16777619) & 0xffffffff
        return value

    def safe_path(name):
        p = Path(name)
        return not p.is_absolute() and '..' not in p.parts and p.as_posix() == name

    # Independent test images: 32x8 black, and the specified 64x12 edge pattern.
    # This is the uncompressed input definition, not the replacement's decoder.
    small = bytes([255]) * 32
    slim = bytes(sum((((x // 11) ^ (y // 3) ^ (x == y) ^ (x == 63-y)) & 1)
                     << (7 - x % 8) for x in range(byte*8, byte*8+8))
                 for y in range(12) for byte in range(8))
    terminals = {'sequence-exhaustion', 'transport-identity-exhaustion'}
    second_generation = {
        'grant-cookie-identity', 'deconfigure-repeat-reconfigure',
        'reset-retry-held-offload', 'reset-after-grant',
        'held-offload-blocks-deferred-reset', 'unsupported/config2',
        'unsupported/alt1', 'unsupported/interface1', 'unsupported/out-of-domain',
        'current-owner-fault', 'current-owner-success-rejected',
        'same-config-recovers-fault'}
    interfaces = {'interface-reselection', 'interface-halt-reselection'}

    def output_contract(name):
        # Generations are from the scripted input/recovery schedule. The initial
        # generation is fixed at 1; it is not inferred from an observed success.
        if name in terminals:
            return b'', [], 2
        if name == 'repeat-configuration-recovery':
            return small + slim + small, [[3,1,0,1,0], [3,2,1,0,0],
                                         [3,3,1,1,0], [4,1,0,1,0]], 4
        if name in interfaces:
            return small + small, [[2,1,0,1,0], [3,1,0,1,0]], 3
        generation = 3 if name in second_generation else 2
        return small, [[generation,1,0,1,0]], generation

    def packet_contract(name):
        # Preserve individual zero-length packets: joining bytes alone erases
        # a missing or duplicate status packet. No typed event adds a packet.
        return {
            'repeat-configuration-recovery': [('', 'raw-repeat-configuration-status')],
            'interface-halt-reselection': [('', 'halt-OUT-before-interface-reselection'),
                                          ('', 'halt-IN-before-interface-reselection')],
            'new-raw-held-blocks-grant': [('01', 'configuration-after-automatic-owner')],
            'raw-programming-failure-IN': [('', 'raw-config-after-explicit-programming-cleanup')],
        }.get(name, [])

    try:
        report = json.loads(path.read_bytes())
        target = report['target']
        need(report['status'] == target['status'] == 'pass', 'paired status')
        sources = report['source_sha256']
        required = {
            'scripts/validate-hp1020-udc-offload.py',
            'scripts/build-hp1020-udc-offload-target.sh',
            'open-firmware/udc-offload-test/fixture.c',
            'open-firmware/udc-offload-test/host-check.c',
            'open-firmware/udc-offload-test/target-check.ld',
            'open-firmware/udc-composed-test/fixture.c',
            'open-firmware/udc-setup/hp1020_udc_setup.c',
            'open-firmware/udc-setup/hp1020_udc_setup.h',
            'open-firmware/udc-out/hp1020_udc_acquire.h',
            'open-firmware/tinyusb-printer-adapter/hp1020_tusb_adapter.c',
            'open-firmware/tinyusb-printer-adapter/hp1020_tusb_adapter.h',
            'open-firmware/tinyusb-device/patches/protocol-compatibility.patch',
            'vendor/tinyusb-0.21.0/src/device/usbd.c',
        }
        need(required <= sources.keys(), 'implementation and reusable stack source closure')
        components = {
            'image-core': ('image', 'image_page', 'image_stream', 'image_ring', 'image_output'),
            'semantic-core': ('semantic', 'page_plan'),
            'usb-receive-core': ('usb_receive', 'usb_document'),
            'usb-printer-class': ('usb_printer',),
            'udc-ep0': ('udc_ep0',), 'udc-out': ('udc_out',),
        }
        need(all('open-firmware/'+directory+'/hp1020_'+stem+'.'+suffix in sources
                 for directory, stems in components.items() for stem in stems
                 for suffix in ('c', 'h')), 'complete receive, decoder, document and descriptor sources')
        need(all(name in sources for name in (
            'scripts/prepare-hp1020-tinyusb.py', 'scripts/validate-hp1020-udc-composed.py',
            'scripts/validate-hp1020-udc-ep0.py', 'scripts/validate-hp1020-udc-out.py',
            'scripts/validate-hp1020-tinyusb-printer.py', 'scripts/validate-hp1020-continuous-printer.py',
            'scripts/hp1020_qemu_ram.py', 'scripts/check-hp1020-c-compiler-profile.py',
            'open-firmware/tinyusb-device/patches/manifest.json',
            'open-firmware/tinyusb-printer-test/fixture.c',
            'open-firmware/udc-ep0-test/fixture.c', 'open-firmware/udc-out-test/fixture.c')),
             'actual fixture, imported oracle and tool closure')
        for name, expected_digest in {**sources, **report['fixture_sha256']}.items():
            relative = Path(name)
            need(not relative.is_absolute() and '..' not in relative.parts and
                 relative.as_posix() == name and re.fullmatch('[0-9a-f]{64}', expected_digest),
                 'safe exact source paths')
            need(hashlib.sha256((root / relative).read_bytes()).hexdigest() == expected_digest,
                 'current exact tested sources and fixtures')
        need(len(report['fixture_sha256']) == 6, 'six independent document fixtures')
        expected_fixtures = {
            'analysis/open-firmware-model/image-core/fixtures/32x8-stripe4-black.jbg',
            'analysis/open-firmware-model/image-core/fixtures/9600x132-stripe128-edges.jbg',
            'analysis/open-firmware-model/image-core/fixtures/16384x4-stripe128-edges.jbg',
            'analysis/open-firmware-model/image-core/output-fixtures/1024x260-stripe128-repeat.jbg',
            'analysis/open-firmware-model/image-core/output-fixtures/64x12-stripe4-edges.jbg',
            'analysis/samples/generated/matrix-a4_default.zjs'}
        need(set(report['fixture_sha256']) == expected_fixtures, 'exact independent fixture set')

        effective = report['effective_source']
        patch_path = 'open-firmware/tinyusb-device/patches/'
        manifest = json.loads((root / (patch_path+'manifest.json')).read_bytes())
        need(effective['patched'] is True and effective['upstream_commit'] ==
             manifest['upstream_commit'] == 'dae3f9a366bfcddbf9dcf1b48d7500286a849539' and
             effective['patch_manifest'] == manifest and manifest['patch_sha256'] ==
             sources[patch_path+'protocol-compatibility.patch'], 'pinned exact effective patch')
        vendor_prefix = 'vendor/tinyusb-0.21.0/'
        originals = {n[len(vendor_prefix):]: d for n,d in sources.items()
                     if n.startswith(vendor_prefix) and not n.endswith('/PROVENANCE.json')}
        wanted_effective = originals.copy()
        need(len(originals) == 19 and set(manifest['files']) ==
             {'src/device/usbd.c', 'src/device/usbd_pvt.h'}, 'exact upstream and patched file sets')
        for name, entry in manifest['files'].items():
            need(originals[name] == entry['original_sha256'], 'patch input matches captured upstream')
            wanted_effective[name] = entry['result_sha256']
        need(effective['effective_sha256'] == wanted_effective, 'all effective-source result bytes bound')
        built = root / 'analysis/usb-path/udc-offload/target'
        need(json.loads((built/'effective-source.json').read_bytes()) == effective,
             'host and target use identical effective source')
        artifacts = target['captured_artifact_sha256']
        need({'target-check.elf', 'target-check.map', 'effective-source.json', 'disassembly.txt',
              'symbols.txt', 'annotated-disassembly.txt'} <= artifacts.keys(), 'target artifact closure')
        for name, claimed in artifacts.items():
            need(safe_path(name) and Path(name).name == name and
                 bool(re.fullmatch('[0-9a-f]{64}', claimed)), 'safe target artifact identity')
            # This listing is generated by the audit of the captured ELF, only
            # inside the saved run. Do not claim a nonexistent shared listing.
            if name != 'annotated-disassembly.txt':
                need(digest((built/name).read_bytes()) == claimed, 'exact current target artifacts')
        need(target['elf_sha256'] == artifacts['target-check.elf'], 'executed ELF hash binding')
        for reference in report['original_reference'].values():
            need(reference['newly_executed_stock_instructions'] == 0 and
                 reference['stock_sha256'] == sources['analysis/sihp1020.elf'] and
                 reference['report_sha256'] == sources[reference['report']],
                 'reused original evidence and zero new original execution')
        snapshot = Path(capture_root) if capture_root is not None else None
        if snapshot is not None:
            need(json.loads((snapshot/'validation.json').read_bytes()) == report,
                 'saved report is current report')
            need(json.loads((snapshot/'source-sha256.json').read_bytes()) == sources and
                 json.loads((snapshot/'fixture-sha256.json').read_bytes()) == report['fixture_sha256'] and
                 json.loads((snapshot/'target-sha256.json').read_bytes()) == artifacts,
                 'saved source, fixture and target manifests')
            for name, claimed in sources.items():
                need(digest((snapshot/'source'/name).read_bytes()) == claimed, 'exact saved source bytes')
            for name, claimed in report['fixture_sha256'].items():
                need(digest((snapshot/'tested-fixtures'/name).read_bytes()) == claimed,
                     'exact saved independent fixture bytes')
            for name, claimed in artifacts.items():
                need(digest((snapshot/'target'/name).read_bytes()) == claimed,
                     'exact saved target and audit-derived listing')
            for name, claimed in wanted_effective.items():
                need(digest((snapshot/'effective-source'/name).read_bytes()) == claimed,
                     'exact saved effective source bytes')
        mode = report['offload_mode_evidence']
        need(set(mode) == {
            'analysis/usb-path/controller-reference/manuals/README.md',
            'analysis/usb-path/controller-reference/manuals/offload-mode-review.json',
            'analysis/usb-path/controller-reference/manuals/offload-mode-review.tar.gz',
            'analysis/usb-path/controller-reference/manuals/usb2-spec-provenance.json'},
             'bounded original mode evidence')
        need(all(sources[n] == digest for n,digest in mode.items()), 'mode evidence captured')
        need(report['hp_dynamic_csr_capability_established'] is False and
             report['automatic_grants_are_acknowledgments'] is False and
             report['controller_quiescence_established'] is False and
             report['actual_peripheral_accesses'] == report['usb_transfers'] ==
             report['completed_native_page_lifecycles'] == 0, 'explicit supplied hardware scope')

        cases = report['cases']
        need(len(cases) == len(target['cases']) and bool(cases), 'complete paired matrix')
        expected_names = {
            'capture-facts', 'configuration-delayed-grant', 'grant-before-recovery',
            'grant-cookie-identity', 'repeat-configuration-recovery',
            'deconfigure-repeat-reconfigure', 'interface-reselection',
            'interface-halt-reselection', 'new-raw-held-blocks-grant',
            'reset-retry-held-offload', 'reset-after-grant',
            'held-offload-blocks-deferred-reset', 'unsupported/config2',
            'unsupported/alt1', 'unsupported/interface1', 'unsupported/unconfigured-SI',
            'unsupported/out-of-domain', 'programming-failure/OUT',
            'programming-failure/IN', 'cleanup-replay-new-failure',
            'raw-programming-failure-IN', 'status-submission-failure/before-bind',
            'status-submission-failure/after-bind', 'current-owner-fault',
            'current-owner-success-rejected', 'same-config-recovers-fault',
            'old-generation-fault-and-success', 'sequence-exhaustion',
            'transport-identity-exhaustion'}
        need(len(sources) == 127 and len(cases) == 58, 'frozen source and profile closure')
        seen = set()
        totals = dict(captures=0, binds=0, grants=0, cancellations=0)
        for case_index, (case, native) in enumerate(zip(cases, target['cases'])):
            need(native['adapter_state_and_memory_bytes'] == 128588 and
                 native['component_and_allocation_bytes'] == {'ep0':296, 'bulk':80, 'setup':96},
                 'measured target component sizes')
            key = (case['scenario'], case['fill'], case['interface'])
            need(key not in seen and case['fill'] in (0,204) and case['interface'] == 0
                 and case['capacity'] == 64, 'bounded unique profiles')
            seen.add(key)
            name = case['scenario']
            need(case['case'] == f'{name}/fill={case["fill"]}/capacity=64/interface=0',
                 'case identity describes its actual profile')
            need(case['case'] == native['case'] and case['status'] == native['status'] == 'pass'
                 and native['all_steps_equal'] is True
                 and native['typed_captures_original_cookies_and_grants_equal'] is True
                 and native['all_pixels_wire_notifications_descriptors_and_storage_equal'] is True,
                 'paired execution and exact captures')
            need(case['capture_sha256'] == native['capture_sha256'] and
                 set(case['capture_sha256']) == {'pixels','wire','receive','output','documents',
                                               'ep0','bulk_descriptor','setup_record'},
                 'complete guarded storage and output captures')
            rows, erows, brows, srows, orows, events = (case[n] for n in
                ('steps','ep0_steps','bulk_steps','setup_steps','offload_steps','events'))
            need(bool(rows) and len({len(a) for a in (rows,erows,brows,srows,orows,events)}) == 1,
                 'complete 368-word transcript')
            prev, pe, pb, ps, po = (case[n] for n in
                ('initial','initial_ep0','initial_bulk','initial_setup','initial_offload'))
            need(prev[32] == 1 and prev[42:48] == [0]*6 and prev[90:94] == [0]*4,
                 'fresh document and recovery generation')
            wanted_pixels, wanted_documents, wanted_generation = output_contract(name)
            wanted_packets = packet_contract(name)
            need(case['pixels_bytes'] == len(wanted_pixels) and
                 case['expected_pixels_sha256'] == digest(wanted_pixels) == case['capture_sha256']['pixels'],
                 'independent full image bytes and length')
            need(case['expected_documents'] == wanted_documents and
                 digest(b''.join(packed(record) for record in case['expected_documents'])) ==
                 case['capture_sha256']['documents'], 'independent original-generation document bytes')
            wire = b''.join(bytes.fromhex(raw) for raw, label in wanted_packets)
            need(digest(wire) == case['capture_sha256']['wire'], 'literal complete wire bytes')
            packets = case['packet_oracles']
            need(len(packets) == len(wanted_packets), 'individual literal packets including ZLPs')
            offset, packet_steps = 0, []
            for packet, (raw, label) in zip(packets, wanted_packets):
                step = packet['step']
                need(packet['expected_hex'] == raw and packet['label'] == label and
                     packet['offset'] == offset and 0 <= step < len(rows),
                     'packet payload, role, offset and step')
                offset += len(bytes.fromhex(raw))
                packet_steps.append(step)
                r, e = rows[step], erows[step]
                need(r[28] != 0 and r[29] == len(bytes.fromhex(raw)) and r[24] == offset and
                     e[78] == r[28] and e[61] == len(bytes.fromhex(raw)),
                     'literal packet has an actual IN descriptor owner')
            need(packet_steps == sorted(set(packet_steps)), 'ordered unique packets, even empty ones')
            typed, owners, granted = {}, {}, set()
            bind_steps, grant_steps, capture_steps = set(), set(), set()
            raw_captures, admissions, tickets = {}, {}, {}
            last_record, injected_open, injected_submit = None, 0, 0
            failures, cleanups, bindings, restarts = [], [], [], []
            witness, controls = set(), set()
            ep0_prepares, ep0_publications, ep0_owners = [], [], {}
            known_ingress = 0
            for i,(r,e,b,s,o,event) in enumerate(zip(rows,erows,brows,srows,orows,events)):
                need([len(a) for a in (r,e,b,s,o)] == [96,104,48,40,80] and
                     r[15:17] == [0,1] and e[2:5] == [0,1,1] and b[7:10] == [0,1,1]
                     and s[12:15] == [0,1,3] and o[11:13] == [0,1] and o[76:80] == [0]*4,
                     'row shapes, ownership and guards')
                op,a,arg_b,arg_c,arg_d = event['words']
                result = event['result']
                controls.add((op,a,arg_b,arg_c,arg_d,result))
                need(r[0] == result and op not in (0,2,3,4,5,13,19), 'ordered typed/component ingress')
                if op in (81,83,100) and 0 < a <= 0xffffffff:
                    known_ingress = max(known_ingress, a)
                if op == 80 and result == 0:
                    last_record = bytes.fromhex(event['data_hex'])
                    need(len(last_record) == 16, 'literal immutable raw SETUP record')
                if op == 81 and result == 0:
                    need(last_record is not None and packed(s[32:36]) == last_record,
                         'raw capture equals caller-supplied bytes')
                    raw_captures[a] = last_record[8:]
                if op in (82,101) and result == 0:
                    need(r[2] == prev[2]+1 and r[2] <= 0xffffffff and s[6:8] == [a,r[2]],
                         'admission has a fresh nonwrapping original control epoch')
                    if op == 82:
                        request = raw_captures[a]
                        original_sequence = 0
                    else:
                        original = typed[a]
                        request = bytes.fromhex('0009010000000000' if original[1:3] == [1,1]
                                  else '0009000000000000' if original[1:3] == [1,0]
                                  else '010b000000000000')
                        original_sequence = a
                    admissions[r[2]] = (original_sequence, request)
                    if prev[44:46] == [1,7] and request in (
                            bytes.fromhex('0009010000000000'), bytes.fromhex('010b000000000000')):
                        need(r[44:46] == [0,0] and r[32] == prev[32],
                             'destructive admission invalidates complete old promises before new binding')
                        witness.add('superseded-complete-promises')
                    if request == bytes.fromhex('0009010000000000') and prev[10]:
                        need(r[7] == r[36] == 1 and r[32] == prev[32],
                             'same configuration fences before dispatch')
                        if prev[30] and prev[50] == 0:
                            witness.add('repeat-with-unfinished-input')
                    if request == bytes.fromhex('0009000000000000') and prev[10]:
                        need(r[7] == r[36] == 1, 'deconfiguration fences admission')
                if op == 83 and result == 0:
                    admissions[r[2]] = (0, None)
                    need(r[32] == prev[32], 'actual reset notification is not document restart')
                    if po[59]:
                        witness.add('reset-retains-dirty-ticket')
                    if po[13] and po[15]:
                        witness.add('reset-after-grant')
                if op == 83 and result == 1 and arg_c == 1:
                    need(s[2:4] == [2,a] and r[2] == prev[2], 'reset WAIT retains exact original retry')
                    witness.add('reset-busy-retry')
                if op in (82,101) and result in (1,3,4):
                    clear_supplied = (arg_c == 1) if op == 82 else ((arg_b & 255) == 1)
                    need(r[2:11]+r[12:] == prev[2:11]+prev[12:] and
                         r[11] == (prev[11] & ~3 if clear_supplied else prev[11]),
                         'unadmitted requests preserve adapter; supplied clear only changes DCD EP0 mask')
                if op == 101 and result == 4:
                    need(s[2:4] == [3,a], 'unsupported typed request remains held')
                    witness.add('unsupported-held')
                if op == 100 and result == 1 and a > ps[4]:
                    witness.add('newer-offer-wait')

                # The three original-ticket promises are separate events. No
                # status grant, cleanup, SETUP or reset may invent a restart.
                if r[42] != prev[42]:
                    need(r[42] == prev[42]+1 and r[42] <= 0xffffffff and
                         r[43] == prev[32] and r[44:46] == [1,0] and r[36] == 1,
                         'new recovery ticket clears every prior promise')
                if op == 10 and result == 0:
                    need(r[44] == 1 and r[42] != 0 and r[43] == r[32],
                         'saved original recovery ticket')
                    tickets[a] = tuple(r[42:44])
                if op == 11 and result == 0:
                    need(arg_b in (1,2,4) and tickets.get(a) == tuple(prev[42:44]) and
                         prev[44] == 1 and prev[43] == prev[32] and
                         r[42:45] == prev[42:45] and r[45] == (prev[45] | arg_b),
                         'one explicitly supplied current-ticket promise')
                if op == 11 and result == 2:
                    need((tickets.get(a) != tuple(prev[42:44]) or not prev[44] or
                          prev[43] != prev[32] or prev[2] != prev[3] or prev[4] != prev[5]) and
                         r[32:48] == prev[32:48],
                         'old recovery promise cannot authorize a new generation')
                    witness.add('stale-recovery-promise')
                if op == 15:
                    need(r[32:48] == prev[32:48], 'endpoint defaults are not a document promise')
                    if prev[82] and prev[84]:
                        need(r[81:85] == [0]*4, 'explicit supplied defaults clear both core halts')
                        witness.add('bulk-defaults-after-halt')
                if r[32] != prev[32]:
                    need(op == 12 and result == 0 and tickets.get(a) == tuple(prev[42:44]) and
                         prev[44:46] == [1,7] and prev[43] == prev[32] and
                         ps[11] == 7 and prev[2] == prev[3] and
                         r[32] == prev[32]+1 and r[32] <= 0xffffffff and
                         r[36] == r[44] == r[45] == 0,
                         'restart requires all three original-ticket promises and current ingress')
                    restarts.append((i,prev[32],r[32]))
                elif op == 12 and result == 0:
                    need(False, 'successful restart must advance exactly once')
                if op == 12 and result == 2:
                    need((tickets.get(a) != tuple(prev[42:44]) or not prev[44] or
                          prev[43] != prev[32] or prev[2] != prev[3] or prev[4] != prev[5]) and
                         r[32:48] == prev[32:48],
                         'old finish identity is rejected without state change')
                    witness.add('stale-recovery-finish')
                if op == 12 and result == 1 and prev[45] == 7 and ps[11] == 0:
                    witness.add('held-ingress-blocks-finish')
                if op in (1,6,7,8,9,12) and ps[11] == 0:
                    need(result == 1 and r[2:] == prev[2:], 'held ingress blocks forward service')

                # A controller-owned packet must settle before endpoint reopens.
                if any(prev[j] for j in (26,28,30)):
                    need(o[49:56] == po[49:56], 'no endpoint reprogramming with retained DCD owner')
                if op == 106 and result == 0:
                    need(a in (1,2), 'named OUT/IN programming-failure injection')
                    injected_open = a
                if op == 14 and result == 0:
                    injected_submit = a
                if op == 1 and prev[2] != prev[3] and r[2] == r[3]:
                    original_sequence, request = admissions[r[2]]
                    if request is None:
                        need(r[68] == r[8] == r[10] == 0, 'actual stack reset clears connection')
                    elif request in (bytes.fromhex('0009010000000000'), bytes.fromhex('010b000000000000')):
                        # Successful binding is recognized by an actually
                        # retained status owner and fresh recovery, not result
                        # alone: raw failed open legitimately returns core OK.
                        if r[28] and r[44] and r[42] == prev[42]+1:
                            need(r[68] == 1 and r[8] == r[10] == 1 and r[45] == 0,
                                 'successful selection preserves connection and begins recovery')
                            if request[1] == 9:
                                repeated = po[66] == 1
                                need(o[49:53] == [v+1 for v in po[49:53]] and
                                     o[55] == po[55]+int(repeated) and o[67] == 15 and
                                     o[72] == po[75]+1+int(repeated) and o[73] == o[72]+1 and
                                     o[75] == o[73] and
                                     (not repeated or o[74] == po[75]+1),
                                     'selection opens OUT then IN after required close-all')
                                if repeated:
                                    witness.add('typed-repeat' if original_sequence else 'raw-repeat')
                            else:
                                need(o[49:56] == po[49:56] and o[67:76] == po[67:76],
                                     'SI reselection does not masquerade as endpoint open callbacks')
                                witness.add('interface-recovery')
                            bindings.append((i, original_sequence, request.hex()))
                    elif request == bytes.fromhex('0009000000000000') and r[28]:
                        need(r[68] == 1 and r[8] == r[10] == r[44] == 0 and
                             r[42] == prev[42] and o[49:53] == po[49:53] and
                             o[55] == po[55]+int(po[66] != 0) and o[67] == 3,
                             'SC0 preserves connection, closes only an existing binding and creates no recovery')
                        if po[66] == 0:
                            witness.add('repeat-zero')

                # Ordinary EP0 packet proposals are checked independently of
                # the auto-owner ledger. Even zero-byte proposals need owners.
                for slot in (0,1):
                    p, old_p = e[8+48*slot:56+48*slot], pe[8+48*slot:56+48*slot]
                    if p[31] != old_p[31]:
                        cookie = [r[21],r[3],r[32],0,slot*128]
                        length = p[5]
                        dma = (0x3579bdf0,0xb68ace00)[slot]
                        literal = packed([0x08000000 | length,0,dma,0])
                        need(p[31] == old_p[31]+1 and p[6:11] == cookie and
                             p[14:18] == [0x08000000 | length,0,dma,0] and p[46] == int(length == 0),
                             'ordinary packet exact descriptor, original cookie and ZLP')
                        ep0_owners[cookie[0]] = (cookie,slot,length,literal.hex())
                        ep0_prepares.append((i,cookie[0]))
                    if p[32] != old_p[32]:
                        cookie, owner_slot, length, literal = ep0_owners[p[22]]
                        need(p[32] == old_p[32]+1 and owner_slot == slot and
                             p[22:27] == cookie and packed(p[18:22]).hex() == literal and
                             p[47] == int(length == 0), 'ordinary packet publication uses original descriptor')
                        ep0_publications.append((i,slot,cookie[0],length))
                if 100 <= op <= 107:
                    need(event['data_hex'] == '', 'typed commands have no raw payload')
                if op == 100 and (result == 0 or (result == 6 and a == 0xffffffff)):
                    original = [a,arg_b,(arg_c >> 16)&255,(arg_c >> 8)&255,arg_c&255]
                    need(a not in typed and o[21:26] == original and r[2:] == prev[2:]
                         and s[32:36] == ps[32:36], 'typed copy is not raw capture or dispatch')
                    typed[a] = original
                    capture_steps.add(i)
                if o[6] != po[6]:
                    token = o[16]
                    original = typed[o[26]]
                    cookie = [r[21],r[3],r[32],0,128]
                    canonical = bytes.fromhex('0009010000000000' if original[1:3] == [1,1]
                                else '0009000000000000' if original[1:3] == [1,0]
                                else '010b000000000000')
                    need(o[6] == po[6]+1 and token not in owners and token > 0 and
                         o[16:21] == cookie and o[26:31] == original and
                         original[1] in (1,2) and original[2] in (0,1) and original[3:] == [0,0]
                         and (original[1] != 2 or original[2] == 1) and
                         packed(o[64:66]) == canonical and r[28:30] == [token,0]
                         and o[13] == 1 and o[32:35] == [1,0,1] and r[77] == 0 and r[68] == 1,
                         'original no-buffer owner and literal canonical request')
                    need(e[56] == 0 and e[39:41] == pe[39:41] and e[87:89] == pe[87:89]
                         and r[24:26] == prev[24:26] and o[57] == po[57],
                         'auto bind creates no descriptor, wire or status callback')
                    owners[token] = (cookie,original)
                    bind_steps.add(i)
                if op == 1 and result == 5 and injected_submit:
                    need(injected_submit in (1,2) and o[59] == 0 and r[44] == 0 and
                         r[7] == r[36] == 1 and o[35] == 0,
                         'failed automatic status submission does not begin recovery')
                    if injected_submit == 1:
                        need(o[6] == po[6] and o[13] == r[28] == 0,
                             'pre-bind failure creates no owner')
                    else:
                        need(o[6] == po[6]+1 and o[13:15] == [1,1] and
                             o[32:36] == [1,0,1,0] and r[28] == o[16],
                             'post-bind failure retains original owner despite cleared core BUSY')
                    witness.add('submit-failure-'+str(injected_submit))
                    injected_submit = 0
                if o[13]:
                    need(owners[o[16]][0] == o[16:21], 'held owner never retagged')
                if op == 102:
                    need(r[2:] == prev[2:] and e == pe and b == pb and o[57] == po[57],
                         'grant never completes, publishes or restarts anything')
                    if result == 0:
                        cookie,original = owners[arg_b]
                        need(arg_d == 0 and arg_c == 0x0101 and a == original[0] and
                             arg_b not in granted and o[7] == po[7]+1 and
                             o[37:42] == original and o[42:47] == cookie and
                             o[13] == o[15] == o[33] == 1 and
                             o[14] == 0 and o[34] == 1 and s[11] == 7 and
                             a == s[6] == s[4] == known_ingress and
                             cookie[1] == r[2] == r[3] and o[31] == r[4] and not r[86] and
                             (original[2] == 0 or (r[82] == r[84] == 0)),
                             'one current exact-original status proposal')
                        granted.add(arg_b)
                        grant_steps.add(i)
                        if r[44] and r[32] == cookie[2]:
                            witness.add('grant-before-recovery')
                        if r[32] == cookie[2]+1:
                            witness.add('grant-after-recovery')
                    else:
                        need(o[7] == po[7] and o[37:47] == po[37:47], 'rejected grant retains output')
                        if result == 1 and prev[82] and prev[84] and po[27] == 2:
                            witness.add('halt-blocks-interface-grant')
                        if result == 1 and ps[11] == 0 and ps[2] == 1:
                            witness.add('held-raw-blocks-old-grant')
                if op in (103,104,105):
                    need(o[57] == po[57] and r[24:26] == prev[24:26] and e == pe,
                         'auto settlement/fault never emits a protocol ACK')
                    if arg_d or result == 2:
                        need(result == 2 and r[2:] == prev[2:] and o[13:37] == po[13:37],
                             'stale/mutated original cookie has no ownership or generation effect')
                if op == 103 and result == 0:
                    need(arg_b == 1 and arg_d == 0 and po[13] == 1 and a == po[16] and
                         o[13] == r[28] == 0 and o[34] == 2 and
                         r[32] == prev[32] and o[8] == po[8]+1,
                         'supplied exact cancellation retires original owner without a restart')
                    if not po[14] and po[17] == prev[2] and po[18] == prev[32]:
                        # A current unsolicited ABORTED event is a fault, even
                        # when the external ingress sequence is terminal. It
                        # invalidates recovery; it never completes a lifecycle.
                        need(r[7] == r[36] == 1 and r[4] == prev[4]+1 and r[44:46] == [0,0],
                             'unsolicited current cancellation fences and invalidates recovery')
                    else:
                        need(r[32:48] == prev[32:48] and r[4] == prev[4],
                             'requested or superseded cancellation preserves document recovery')
                if op == 104 and po[13] and a == po[16] and not arg_d:
                    if po[18] < prev[32]:
                        need(result == 2 and r[2:] == prev[2:], 'old generation fault cannot stop current document')
                        witness.add('old-generation-fault')
                    elif po[18] == prev[32] and po[17] == prev[2] and result == 0:
                        need(o[13:15] == [1,1] and r[7] == r[36] == 1,
                             'current fault fences without fictitious cancellation')
                        witness.add('current-owner-fault')
                if op == 105:
                    need(result != 0 and o[13] == po[13] and r[28:30] == prev[28:30],
                         'generic auto success cannot retire ownership')
                    if result == 3 and po[13] and a == po[16] and not arg_d:
                        witness.add('auto-success-rejected')
                if o[59] and not po[59]:
                    sequence, request = admissions[prev[2]]
                    original_ticket = [sequence,prev[2],prev[4]]
                    need(op == 1 and injected_open in (1,2) and request == bytes.fromhex('0009010000000000') and
                         o[60:63] == o[69:72] == original_ticket and o[68] == 1 and o[61] > 0 and
                         o[67] == (7 if injected_open == 2 else 3) and
                         r[8] == r[10] == r[44] == 0 and r[4] > original_ticket[2] and
                         o[49:53] == [po[49]+1,po[50]+int(injected_open == 2),
                                      po[51]+int(injected_open == 2),po[52]] and
                         o[72] == po[75]+1 and o[75] == po[75]+injected_open and
                         (injected_open == 1 or o[73] == po[75]+2),
                         'independent original partial-programming failure')
                    failures.append((i, injected_open, original_ticket))
                    injected_open = 0
                if po[59] and not o[59]:
                    need(op == 107 and result == 0 and arg_d == 1 and
                         [a,arg_b,arg_c] == po[60:63] and o[67] == 3 and o[68] == 0
                         and r[8] == r[10] == r[13] == r[77] == r[85] == 0 and
                         prev[13] == prev[77] == prev[85] == 0 and
                         r[7] == r[36] == 1 and r[32:48] == prev[32:48] and
                         o[58] == po[58]+1 and o[60:63] == po[60:63] and o[69:72] == po[69:72],
                         'only exact explicit cleanup clears retained programming')
                    cleanups.append((i,[a,arg_b,arg_c]))
                if po[59] and o[59]:
                    need(o[60:63] == po[60:63] and o[49:53] == po[49:53],
                         'dirty programming retains identity and prevents new opens')
                if op == 107 and result != 0:
                    need(r[2:] == prev[2:] and o[58:63] == po[58:63] and
                         o[67:72] == po[67:72], 'rejected cleanup preserves partial programming and promises')
                    if result == 2 and failures and [a,arg_b,arg_c] == failures[0][2] and len(failures) > 1:
                        witness.add('old-cleanup-replay')
                prev,pe,pb,ps,po = r,e,b,s,o
            need(po[2] == len(capture_steps) and po[6] == len(owners) and po[7] == len(granted),
                 'complete capture, bind and grant ledgers')
            for kind, indices in (('typed_capture',capture_steps),('auto_bind',bind_steps),('auto_grant',grant_steps)):
                need({item['step'] for item in case['offload_oracles'] if item['kind'] == kind} == indices,
                     'independent oracle coverage')
            need(prev[32] == wanted_generation and len(restarts) == wanted_generation-1 and
                 prev[50:52] == [len(wanted_pixels),fnv(wanted_pixels)] and
                 prev[24:26] == [len(wire),fnv(wire)] and
                 prev[90:92] == [len(wanted_documents)]*2 and po[57] == len(wanted_packets),
                 'final generation, full byte counts, hashes and notification/ordinary ACK counts')
            need([(step,length) for step,slot,token,length in ep0_publications if slot == 1] ==
                 [(packet['step'],len(bytes.fromhex(raw))) for packet,(raw,label) in zip(packets,wanted_packets)],
                 'every ordinary IN publication has one literal packet oracle including ZLP')
            outs = [(step,token,length) for step,slot,token,length in ep0_publications if slot == 0]
            need(len(outs) == int(name == 'new-raw-held-blocks-grant') and
                 all(length == 0 and step > packet_steps[0] for step,token,length in outs),
                 'exact ordinary OUT status after GET_CONFIGURATION data')
            wanted_descriptors = []
            for kind, records in (('prepare',ep0_prepares),
                                  ('publish',[(step,token) for step,slot,token,length in ep0_publications])):
                for step, token in records:
                    cookie, slot, length, literal = ep0_owners[token]
                    wanted_descriptors.append((step,kind,tuple(cookie),slot,length,literal))
            observed_descriptors = [(item['step'],item['kind'],tuple(item['cookie']),item['slot'],
                                     item['requested'],item['descriptor']) for item in case['descriptor_oracles']]
            need(sorted(observed_descriptors) == sorted(wanted_descriptors),
                 'complete original-cookie literal ordinary descriptor oracle ledger')

            # Require purposeful behavioral witnesses, not just 29 distinct
            # labels attached to copies of the same happy-path transcript.
            required_witnesses = {
                'capture-facts': {'newer-offer-wait', 'repeat-zero'},
                'configuration-delayed-grant': {'grant-after-recovery'},
                'grant-before-recovery': {'grant-before-recovery'},
                'repeat-configuration-recovery': {'repeat-with-unfinished-input','typed-repeat','raw-repeat'},
                'deconfigure-repeat-reconfigure': {'repeat-zero'},
                'interface-reselection': {'interface-recovery'},
                'interface-halt-reselection': {'interface-recovery','halt-blocks-interface-grant','bulk-defaults-after-halt'},
                'new-raw-held-blocks-grant': {'held-raw-blocks-old-grant'},
                'reset-retry-held-offload': {'reset-busy-retry','newer-offer-wait'},
                'reset-after-grant': {'reset-after-grant'},
                'held-offload-blocks-deferred-reset': {'held-ingress-blocks-finish','superseded-complete-promises',
                                                       'stale-recovery-promise','stale-recovery-finish'},
                'programming-failure/OUT': {'reset-retains-dirty-ticket'},
                'programming-failure/IN': {'reset-retains-dirty-ticket'},
                'cleanup-replay-new-failure': {'old-cleanup-replay'},
                'status-submission-failure/before-bind': {'submit-failure-1'},
                'status-submission-failure/after-bind': {'submit-failure-2'},
                'current-owner-fault': {'current-owner-fault'},
                'current-owner-success-rejected': {'auto-success-rejected'},
                'same-config-recovers-fault': {'current-owner-fault','typed-repeat'},
                'old-generation-fault-and-success': {'old-generation-fault','auto-success-rejected'},
            }.get(name, set())
            if name.startswith('unsupported/'):
                required_witnesses.add('unsupported-held')
                unsupported = {
                    'config2':[1,2,0,0], 'alt1':[2,1,0,1], 'interface1':[2,1,1,0],
                    'unconfigured-SI':[2,1,0,0], 'out-of-domain':[1,255,0,0]}[name.split('/')[1]]
                need(any(original[1:] == unsupported for original in typed.values()),
                     'actual unsupported typed input matches profile')
            need(required_witnesses <= witness, 'scenario witnesses: '+name+' '+','.join(sorted(required_witnesses-witness)))
            expected_failure_positions = {
                'programming-failure/OUT':[1], 'programming-failure/IN':[2],
                'cleanup-replay-new-failure':[2,2], 'raw-programming-failure-IN':[2]}.get(name, [])
            need([slot for step,slot,ticket in failures] == expected_failure_positions and
                 [ticket for step,slot,ticket in failures] == [ticket for step,ticket in cleanups],
                 'required failures each receive one original-attempt cleanup')
            need(all((ticket[0] == 0) == (name == 'raw-programming-failure-IN')
                     for step,slot,ticket in failures), 'raw/typed failure provenance stays distinct')
            if name == 'capture-facts':
                for shift in (24,16,8,0):
                    missing = 0x01010101 & ~(255 << shift)
                    invalid = missing | (2 << shift)
                    need(any(op == 101 and facts == missing and result == 1
                             for op,a,facts,busy,d,result in controls) and
                         any(op == 101 and facts == invalid and result == 3
                             for op,a,facts,busy,d,result in controls),
                         'each capture fact has an independent missing and invalid control')
            if name == 'grant-cookie-identity':
                for op in (102,103,104,105):
                    for mutation in range(1,6):
                        need(any(command == op and mutant == mutation and result == 2
                                 for command,a,b,c,mutant,result in controls),
                             'each original cookie field rejects mutation at every ingress')
            if name in terminals:
                need(ps[11] == 0 and po[13] == 0 and po[34] == 2 and prev[36] == 1 and
                     not wanted_documents and not wanted_pixels,
                     'exhaustion settles controller only, leaving fenced pending adapter ownership')
                if name == 'sequence-exhaustion':
                    need(ps[2:5] == [3,0xffffffff,0xffffffff] and ps[10] == 1 and
                         any(op == 100 and a == 0xffffffff and result == 6 for op,a,b,c,d,result in controls),
                         'external sequence exhaustion retains original terminal event')
                else:
                    need(prev[4] == 0xffffffff and prev[86] == 1 and ps[10] == 2 and
                         (20,0,0xffffffff,0,0,0) in controls,
                         'transport exhaustion is the explicitly seeded distinct terminal path')

            if snapshot is not None:
                directory = snapshot / f'case-{case_index:03}'
                need((directory/'case-name').read_text().strip() == case['case'], 'saved raw case identity')
                filenames = {'ep0':'output.ep0-descriptors','bulk_descriptor':'output.udc-descriptor',
                             'setup_record':'output.setup-record'}
                for kind, claimed in case['capture_sha256'].items():
                    need(digest((directory/filenames.get(kind,kind)).read_bytes()) == claimed and
                         digest((directory/('target-'+kind)).read_bytes()) == native['capture_sha256'][kind],
                         'exact saved host and target raw captures')
                need((directory/'pixels').read_bytes() == wanted_pixels and
                     (directory/'wire').read_bytes() == wire and
                     (directory/'documents').read_bytes() == b''.join(packed(doc) for doc in wanted_documents),
                     'saved raw bytes equal independent pixel, packet and document definitions')
                need((directory/'events.bin').read_bytes() ==
                     b''.join(packed(ev['words']+[len(bytes.fromhex(ev['data_hex']))])+
                              bytes.fromhex(ev['data_hex']) for ev in events),
                     'saved original event stream matches report inputs')
                host_rows = [json.loads(line) for line in (directory/'host-steps.jsonl').read_text().splitlines()]
                target_rows = [json.loads(line) for line in (directory/'target-steps.jsonl').read_text().splitlines()]
                need(host_rows == rows and len(target_rows) == len(rows), 'complete raw host and target row streams')
                for row, expected in zip(target_rows, (r+e+b+s+o for r,e,b,s,o in zip(rows,erows,brows,srows,orows))):
                    need(len(row) == 368 and row[59] == 128588 and
                         row[:59]+row[60:] == expected[:59]+expected[60:],
                         'all raw native words equal recorded host words except measured native footprint')
            guard = bytes([case['fill']])*16
            need(hashlib.sha256(guard+packed(brows[-1][24:28])+guard).hexdigest() ==
                 case['capture_sha256']['bulk_descriptor'] and
                 hashlib.sha256(guard+packed(srows[-1][28:32])+guard).hexdigest() ==
                 case['capture_sha256']['setup_record'], 'complete guarded live records')
            totals['captures'] += len(capture_steps)
            totals['binds'] += len(owners)
            totals['grants'] += len(granted)
            totals['cancellations'] += po[8]
        need(seen == {(n,f,0) for n in expected_names for f in (0,204)}, 'complete intended matrix')
        need(all(value > 0 for value in totals.values()), 'positive typed-path coverage')
    except (OSError, ValueError, KeyError, TypeError, IndexError, OverflowError) as error:
        return False, 'offload transcript incomplete: '+str(error)
    return not bad, '; '.join(sorted(bad)) if bad else 'paired typed offload owners, grants, original identities and guarded captures agree; no physical USB claim'


def entry_capture_archive_gate(root):
    """Check committed raw evidence without relying on disposable run paths."""
    try:
        root = Path(root)
        folder = root / "analysis/boot-handoff/entry-ram"
        manifest = json.loads((folder / "capture-manifest.json").read_text())
        payload = folder / "capture.tar.gz"
        if (manifest["schema"] != "hp1020-entry-capture-v1"
                or payload.stat().st_size != manifest["archive_bytes"]
                or payload.stat().st_size > 32 * 1024 * 1024
                or hashlib.sha256(payload.read_bytes()).hexdigest() != manifest["archive_sha256"]):
            raise ValueError("exact bounded entry capture archive seal")
        with tempfile.TemporaryDirectory(prefix="hp1020-entry-evidence-") as directory:
            capture = Path(directory)
            with tarfile.open(payload, "r:gz") as archive:
                members = archive.getmembers()
                names = [m.name for m in members]
                if (len(names) != len(set(names)) or len(names) != manifest["members"]
                        or set(names) != set(manifest["member_sha256"])
                        or sum(m.size for m in members) > 128 * 1024 * 1024):
                    raise ValueError("exact bounded entry archive members")
                for item in members:
                    name = Path(item.name)
                    if (not item.isfile() or name.is_absolute() or ".." in name.parts
                            or item.size > 32 * 1024 * 1024):
                        raise ValueError("ordinary relative entry archive member")
                    raw = archive.extractfile(item).read()
                    if hashlib.sha256(raw).hexdigest() != manifest["member_sha256"][item.name]:
                        raise ValueError("entry archive member byte seal: " + item.name)
                    destination = capture / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(raw)
            if (capture / "validation.json").read_bytes() != (folder / "validation.json").read_bytes():
                raise ValueError("published entry report must be the exact archived report")
            checker = runpy.run_path(str(root / "scripts/check-hp1020-entry-ram.py"))["check_capture"]
            ok, detail = checker(capture, source_root=root)
            if not ok:
                return False, detail
            saved = json.loads((capture / "independent-gate.json").read_text())
            if saved != dict(ok=ok, detail=detail):
                raise ValueError("saved independent entry gate differs from recovered raw check")
            return True, detail
    except Exception as error:
        return False, "Entry capture archive consistency failure: " + str(error)


def build_report() -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    dispatch_md = read_text("analysis/engine-dispatch-cfg/engine-dispatch-cfg.md")
    registration = read_json("analysis/queue-routing/registration.json")
    registered = {r["queue"]: (r["name"], r["object"]) for r in registration["registrations"]}
    checks.append(check("engine_0x17_dispatch_is_default",
                        "| `0x17` | `100162aa` | default return/no-op |" in dispatch_md,
                        "Engine queue 0 has no 0x17 command case; actual status producers target PrintMgr queue 1.",
                        evidence="analysis/engine-dispatch-cfg/engine-dispatch-cfg.md"))
    checks.append(check("stock_queue_registration",
                        registered[0] == ("engMsgQ", "0x1002f134")
                        and registered[1] == ("PrintMgrQueue", "0x10028a74")
                        and registered[3] == ("Job Mgr Queue", "0x10023e40")
                        and len(registered) == 7 and len(registration["helper_cases"]) == 48
                        and registration["source_sha256"] == hashlib.sha256((ROOT_DIR/"scripts/audit-hp1020-queue-registration.py").read_bytes()).hexdigest(),
                        "Stock constructor control flow must preserve the corrected queue identities and independent registration-helper audit.",
                        evidence="analysis/queue-routing/registration.json"))

    pipeline = read_json("analysis/open-firmware-model/stock-execution/pipeline.json")
    checks.append(check("original_native_pipeline_execution",
                        pipeline["status"] == "pass" and pipeline["total_cases"] == 32
                        and pipeline["completed_lifecycles"] == 26
                        and pipeline["reproduced_conditional_stops"] == 6
                        and sum(c["status"] == "pass" for c in pipeline["cases"]) == 26
                        and sum(c["status"] == "reproduced_conditional_null_read"
                                and c["pc"] == "0x1000e9f4" and c["head"] == "0x0"
                                and c["cancel"] == 1 and not c["lifecycle_completed"]
                                for c in pipeline["cases"]) == 6
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h
                                for p,h in pipeline["source_sha256"].items()),
                        "Completed native lifecycles and conditional original null reads must remain separate, reproducible outcomes.",
                        evidence="analysis/open-firmware-model/stock-execution/pipeline.json"))

    for name, total in (("printmgr",40),("notifications",12),("stop",90),("cancellation",48),("status-publication",15),("queue",80),("status-queue",8),("context",180),("scheduler",80),("scheduled-status",30),("pool",93),("timers",44),("retirement",28)):
        execution = read_json(f"analysis/open-firmware-model/stock-execution/{name}.json")
        checks.append(check(f"original_{name}_execution",
                            execution["status"] == "pass" and execution["total_cases"] == total
                            and all(c["status"] == "pass" for c in execution["cases"])
                            and (name != "stop" or execution["prefix_gate"]["status"] == "blocked"
                                 and execution["instruction_span_gate"]["status"] == "blocked")
                            and (name != "retirement" or sum(c["outcome"] == "blocked_next_path"
                                 and c["stop"] == "native tasks left selected code: 0x1001434b"
                                 for c in execution["cases"]) == 2)
                            and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h
                                    for p,h in execution["source_sha256"].items()),
                            "Original routing and allocation ownership must agree with QEMU and explicit fixture oracles.",
                            evidence=f"analysis/open-firmware-model/stock-execution/{name}.json"))

    pages = read_json("analysis/open-firmware-model/stock-execution/pages.json")
    checks.append(check("original_native_page_execution",
                        pages["status"] == "pass" and pages["total_cases"] == 18
                        and pages["completed_lifecycles"] == 18 and len(pages["cases"]) == 18
                        and {(c["documents"], c["pages"], c["fill"], c["ticks_per_page"],
                              c["consumed_cleanup_event"]) for c in pages["cases"]}
                            == {(d,p,f,t,e) for d,p in ((1,1),(1,3),(3,3))
                                for f in (0,204) for t,e in ((0,False),(2,False),(2,True))}
                        and all(c["status"] == "pass"
                                and c["scheduled_work"] == c["completed_work"]
                                and c["delivered_ticks"] == c["ticks_per_page"] * c["pages"]
                                and c["cleanup_before_completion"]
                                    == [bool(c["ticks_per_page"]) and not c["consumed_cleanup_event"]] * c["pages"]
                                and c["remaining_allocation_bytes"] == 20
                                for c in pages["cases"])
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h
                                for p,h in pages["source_sha256"].items()),
                        "Supplied FIFO consumption and controlled timed cleanup must retain separate causal controls and current source provenance.",
                        evidence="analysis/open-firmware-model/stock-execution/pages.json"))

    fragments = read_json("analysis/open-firmware-model/stock-execution/page-fragments.json")
    fragment_stop = read_json("analysis/open-firmware-model/stock-execution/page-fragment-limit.json")
    checks.append(check("original_native_fragment_execution",
                        fragments["status"] == "pass" and fragments["total_cases"] == 18
                        and fragments["completed_lifecycles"] == 18 and len(fragments["cases"]) == 18
                        and {(c["raster_chunks"],c["fill"],c["ticks_per_page"],c["consumed_cleanup_event"])
                             for c in fragments["cases"]}
                            == {(n,f,t,e) for n in (6,13,64) for f in (0,204)
                                for t,e in ((0,False),(2,False),(2,True))}
                        and all(c["status"] == "pass" and c["instructions"] < c["instruction_budget"]
                                and c["instruction_budget"] == (250000 if c["raster_chunks"] == 64 else 200000)
                                and len(c["reference_decrements"]) == len(c["event_calls"]) == c["raster_chunks"]
                                and c["remaining_allocation_bytes"] == 20 for c in fragments["cases"])
                        and fragment_stop["outcome"] == "instruction_budget_exhausted"
                        and fragment_stop["steps"] == 200000 and not fragment_stop["lifecycle_completed"]
                        and fragments["baseline_page_report_sha256"]
                            == hashlib.sha256((ROOT_DIR/"analysis/open-firmware-model/stock-execution/pages.json").read_bytes()).hexdigest()
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h
                                for p,h in fragments["source_sha256"].items()),
                        "Larger raster lists must retain explicit budgets, complete ownership checks and a separate historical budget stop.",
                        evidence="analysis/open-firmware-model/stock-execution/page-fragments.json"))

    event_rows = read_tsv("analysis/engine-events/engine-0x17-events.tsv")
    status_corr = read_json("analysis/status-path/status-code-correlation.json")
    direct_counts = status_corr.get("direct_converter_class_counts", {})
    checks.append(
        check(
            "status_correlation_event_count_matches_source",
            status_corr.get("event_count") == len(event_rows) == 21,
            "Status correlation must account for every currently cataloged engine 0x17 event word.",
            evidence="analysis/status-path/status-code-correlation.json",
        )
    )
    checks.append(
        check(
            "engine_events_are_not_direct_pjl_codes",
            direct_counts == {"not a proven direct input to CODE converter": 21},
            "Raw engine event words must not be mislabeled as final PJL CODE values.",
            evidence="analysis/status-path/status-code-correlation.json",
        )
    )

    invariants = read_json("analysis/open-firmware-model/model-invariants.json")
    invariant_cases = {item.get("case") for item in invariants}
    expected_cases = {
        "base",
        "a4_2400x600",
        "a4_600x600",
        "a4_cardstock_media",
        "a4_default",
        "a4_draft",
        "a4_logical_clip",
        "a4_manual_feed",
        "a4_two_copies",
        "legal_default",
        "letter_default",
    }
    checks.append(
        check(
            "print_model_invariants_have_no_failures",
            severity_count(invariants, "fail") == 0 and len(invariants) >= 200,
            "Offline ZjStream model invariants must remain green across generated print-path variants.",
            evidence="analysis/open-firmware-model/model-invariants.json",
        )
    )
    checks.append(
        check(
            "print_model_variant_coverage",
            expected_cases.issubset(invariant_cases),
            "Invariant coverage must include paper size, resolution, copy, draft, source, media, and clip variants.",
            evidence="analysis/open-firmware-model/model-invariants.json",
        )
    )

    minimal_scope = read_json("analysis/open-firmware-model/minimal-print-scope.json")
    usb_bulk_receive = read_json("analysis/usb-path/usb-bulk-receive-model.json")
    usb_bulk_callbacks = read_json("analysis/usb-path/usb-bulk-callbacks-model.json")
    usb_bulk_rearm = read_json("analysis/usb-path/usb-bulk-rearm-model.json")
    usb_parser_shim = read_json("analysis/usb-path/usb-parser-shim-contract.json")
    usb_interrupt_events_for_bulk = read_json("analysis/usb-path/usb-interrupt-events.json")
    bulk_probe_reports = {
        name: read_json(path) for name, path in EXPECTED_BULK_PROBE_REPORTS.items()
    }
    bulk_probe_contract = bulk_probe_reports["combined_contract"]
    bulk_parser_model = bulk_probe_reports["parser_model"]
    bulk_deterministic = bulk_probe_reports["deterministic_results"]
    bulk_safety = bulk_probe_reports["safety_scan"]
    bulk_usb_contract = bulk_probe_reports["usb_contract_scan"]
    bulk_usb_mmio = bulk_probe_reports["usb_mmio_access_scan"]
    bulk_memory = bulk_probe_reports["memory_boundary_scan"]
    bulk_source_contract = bulk_probe_reports["source_contract_check"]
    bulk_status_descriptor = bulk_probe_reports["status_descriptor_check"]
    bulk_config_descriptor = bulk_probe_reports["config_descriptor_check"]
    bulk_reproducibility = bulk_probe_reports["reproducibility_check"]
    bulk_summary = read_text(f"{USB_BULK_PROBE_DIR}/summary.md")
    bulk_hardware_plan = read_text(f"{USB_BULK_PROBE_DIR}/hardware-test-plan.md")
    bulk_report_statuses = {
        name: report_status(report) for name, report in bulk_probe_reports.items()
    }
    bulk_report_fail_counts = {
        name: nested_fail_count(report) for name, report in bulk_probe_reports.items()
    }
    usb_bulk_checks = usb_bulk_receive.get("checks", [])
    usb_bulk_callback_checks = usb_bulk_callbacks.get("checks", [])
    usb_bulk_rearm_checks = usb_bulk_rearm.get("checks", [])
    scope_components = {
        item.get("component"): item
        for item in minimal_scope.get("components", [])
        if isinstance(item, dict)
    }
    scope_evidence = minimal_scope.get("stock_evidence", {})
    open_probe_evidence = minimal_scope.get("open_probe_evidence", {})
    checks.append(
        check(
            "minimal_print_scope_keeps_parser_mapped_and_hardware_blocked",
            scope_evidence.get("missing_required_messages") == []
            and scope_evidence.get("model_invariant_failures") == 0
            and scope_evidence.get("endpoint0_data_cases") == 24
            and scope_evidence.get("usb_bulk_lane_event_bit") == "0x00020000"
            and scope_evidence.get("usb_bulk_lane_status_register") == "0xb3000224"
            and scope_evidence.get("usb_bulk_lane_control_register") == "0xb3000220"
            and scope_evidence.get("usb_tdc_status_bit") == "0x400"
            and scope_evidence.get("usb_wake_is_successful_completion") is False
            and scope_evidence.get("usb_bulk_receive_status") == "pass"
            and scope_evidence.get("usb_bulk_transfer_record_stride") == "0x58"
            and scope_evidence.get("usb_bulk_receive_buffer_allocation") == "0x400 bytes"
            and scope_evidence.get("usb_bulk_parser_entry") == "0x10009d34"
            and scope_evidence.get("usb_bulk_parser_reads_via_callback") is True
            and scope_evidence.get("usb_bulk_callback_status") == "pass"
            and scope_evidence.get("usb_bulk_event_bit") == "0x00020000"
            and scope_evidence.get("usb_bulk_endpoint_ack_register") == "0xb3000220"
            and scope_evidence.get("usb_bulk_rearm_status") == "pass"
            and scope_evidence.get("usb_bulk_descriptor_pool") == "0x90021370"
            and scope_evidence.get("usb_bulk_descriptor_submit_register") == "0xb3000234"
            and scope_components.get("ZjStream parser and JobMgr object model", {}).get("current_status") == "mapped"
            and scope_components.get("USB bulk receive to ZjStream parser", {}).get("current_status")
            == "implemented and offline validated"
            and "no print handoff"
            in scope_components.get("USB bulk receive to ZjStream parser", {}).get("replacement_need", "")
            and scope_components.get("Video sideband policy", {}).get("current_status") == "direct START_PAGE source verified"
            and scope_components.get("Video sideband policy", {}).get("risk") == "high"
            and scope_components.get("Video/raw-band hardware feed", {}).get("risk") == "high"
            and scope_components.get("Engine paper/fuser/motor coordination", {}).get("risk") == "high"
            and scope_evidence.get("sideband_access_hits") == 19
            and scope_evidence.get("sideband_0x26_risk") == "critical"
            and scope_evidence.get("remaining_units_source_gap") is False
            and open_probe_evidence.get("status") == "implemented and offline validated"
            and open_probe_evidence.get("offline_validated") is True
            and open_probe_evidence.get("mechanically_inert_cases") is True
            and open_probe_evidence.get("hardware_contact") is False
            and open_probe_evidence.get("recognized_chunk_types")
            == ["0x00", "0x01", "0x02", "0x03", "0x04", "0x05", "0x06"]
            and open_probe_evidence.get("status_descriptor_address") == "0x10003400"
            and set(open_probe_evidence.get("generated_sample_cases", []))
            == EXPECTED_BULK_GENERATED_SAMPLES
            and set(open_probe_evidence.get("matrix_cases", [])) == EXPECTED_BULK_MATRIX_CASES
            and open_probe_evidence.get("report_statuses") == bulk_report_statuses
            and open_probe_evidence.get("report_fail_counts") == bulk_report_fail_counts
            and all(status == "pass" for status in open_probe_evidence.get("report_statuses", {}).values())
            and all(count == 0 for count in open_probe_evidence.get("report_fail_counts", {}).values())
            and "printing, semantic JobMgr/raster handoff, and all engine/video behavior remain unimplemented"
            in minimal_scope.get("current_decision", ""),
            "The generated narrow-scope report must mark only the inert USB bulk receive/framing component implemented offline, retain semantic parser and engine/video blockers, and carry exact probe evidence.",
            evidence="analysis/open-firmware-model/minimal-print-scope.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_receive_model_preserves_parser_handoff",
            usb_bulk_receive.get("status") == "pass"
            and usb_bulk_receive.get("transfer_record", {}).get("record_stride") == "0x58"
            and usb_bulk_receive.get("transfer_record", {}).get("buffer_allocation") == "0x400 bytes"
            and usb_bulk_receive.get("parser_handoff", {}).get("parser_entry_literal") == "0x10005fdc"
            and usb_bulk_receive.get("parser_handoff", {}).get("parser_registration_call") == "0x10009b45"
            and usb_bulk_receive.get("usb2thread_creation", {}).get("call_site") == "0x10009a08"
            and usb_bulk_receive.get("constants", {}).get("usb2thread_name") == "0x10003530"
            and usb_bulk_receive.get("constants", {}).get("usb_saved_out1_nak_word") == "0x10021588"
            and usb_bulk_receive.get("constants", {}).get("out1_max_packet_register") == "0xb300022c"
            and usb_bulk_receive.get("adjacent_literals_are_not_a_task_descriptor") is True
            and len(usb_bulk_receive.get("original_byte_checks", [])) == 46
            and all(item.get("status") == "present" for item in usb_bulk_receive.get("original_byte_checks", []))
            and usb_bulk_receive.get("parser_handoff", {}).get("parser_entry") == "0x10009d34"
            and usb_bulk_receive.get("parser_handoff", {}).get("parser_reads_via_param_0x0c_callback") is True
            and usb_bulk_receive.get("parser_handoff", {}).get("parser_sends_jobmgr_queue") == 3
            and all(item.get("status") == "present" for item in usb_bulk_checks),
            "The USB bulk receive model must keep the stock transfer-record registration, 0x400-byte receive buffer, and parser read-callback handoff mapped.",
            evidence="analysis/usb-path/usb-bulk-receive-model.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_callback_model_preserves_event_and_rearm_path",
            usb_bulk_callbacks.get("status") == "pass"
            and usb_bulk_callbacks.get("constants", {}).get("bulk_event_bit") == "0x00020000"
            and usb_bulk_callbacks.get("constants", {}).get("usb_endpoint_ack_register") == "0xb3000220"
            and usb_bulk_callbacks.get("constants", {}).get("usb_status_register") == "0xb3000418"
            and usb_bulk_callbacks.get("constants", {}).get("pending_transfer_list") == "0x10022740"
            and any(item.get("address") == "0x100087b8" and item.get("name") == "bulk_rx_read" for item in usb_bulk_callbacks.get("callback_roles", []))
            and any(item.get("address") == "0x10008bac" and item.get("name") == "bulk_rx_complete" for item in usb_bulk_callbacks.get("callback_roles", []))
            and all(item.get("status") == "present" for item in usb_bulk_callback_checks),
            "The USB bulk callback model must preserve the read/copy callback, completion queue callback, event bit, endpoint ack register, and status-bit clear.",
            evidence="analysis/usb-path/usb-bulk-callbacks-model.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_rearm_model_preserves_descriptor_submit",
            usb_bulk_rearm.get("status") == "pass"
            and usb_bulk_rearm.get("constants", {}).get("descriptor_pool") == "0x90021370"
            and usb_bulk_rearm.get("constants", {}).get("bulk_buffer_base") == "0x900216f0"
            and usb_bulk_rearm.get("constants", {}).get("descriptor_submit_register") == "0xb3000234"
            and usb_bulk_rearm.get("constants", {}).get("bulk_done_byte") == "0x1001bc70"
            and usb_bulk_rearm.get("constants", {}).get("bulk_rx_done_flag") == "0x1001bc72"
            and all(item.get("status") == "present" for item in usb_bulk_rearm_checks),
            "The USB bulk re-arm model must preserve descriptor pool, buffer base, submit register, and done-flag behavior.",
            evidence="analysis/usb-path/usb-bulk-rearm-model.json",
        )
    )
    shim_contract = usb_parser_shim.get("implementation_contract", {})
    checks.append(
        check(
            "usb_parser_shim_contract_preserves_next_software_target",
            usb_parser_shim.get("status") == "pass"
            and shim_contract.get("parser_boundary", {}).get("parser_entry") == "0x10009d34"
            and shim_contract.get("parser_boundary", {}).get("parser_read_callback_slot") == "param_1 + 0x0c"
            and shim_contract.get("bulk_read_state", {}).get("wait_event_bit") == "0x00020000"
            and shim_contract.get("hardware_receive_lane", {}).get("lane_status_register") == "0xb3000224"
            and shim_contract.get("descriptor_rearm", {}).get("descriptor_pool") == "0x90021370"
            and shim_contract.get("descriptor_rearm", {}).get("descriptor_submit_register") == "0xb3000234",
            "The synthesized USB parser-shim contract must keep the next target anchored to parser callback, bulk event bit, hardware lane, and descriptor re-arm facts.",
            evidence="analysis/usb-path/usb-parser-shim-contract.json",
        )
    )

    bulk_contract_checks = {
        item.get("name"): item
        for item in bulk_probe_contract.get("checks", [])
        if isinstance(item, dict)
    }
    bulk_source_checks = {
        item.get("name"): item for item in report_check_items(bulk_source_contract)
    }
    bulk_status_checks = {
        item.get("name"): item for item in report_check_items(bulk_status_descriptor)
    }
    bulk_config_checks = {
        item.get("name"): item for item in report_check_items(bulk_config_descriptor)
    }
    bulk_generated_samples = bulk_parser_model.get("generated_samples", [])
    bulk_matrix_cases = bulk_parser_model.get("test_matrix", [])
    bulk_all_cases = [*bulk_generated_samples, *bulk_matrix_cases]
    bulk_coverage = bulk_parser_model.get("coverage", {})
    bulk_probe_type_rows = bulk_parser_model.get("probe_recognized_chunk_types", [])
    bulk_probe_types = [
        (item.get("type"), item.get("type_hex"), item.get("name"))
        for item in bulk_probe_type_rows
        if isinstance(item, dict)
    ]
    bulk_mmio_accesses = {
        (item.get("register"), item.get("access"))
        for item in bulk_usb_mmio
        if isinstance(item, dict)
    }
    bulk_memory_accesses = {
        (item.get("kind"), item.get("access"))
        for item in bulk_memory
        if isinstance(item, dict)
    }
    interrupt_bulk_lane = (
        usb_interrupt_events_for_bulk.get("event_scan", {}).get("bulk_receive_lane", {})
    )
    probe_registers = bulk_probe_contract.get("registers", {})
    probe_allowed_memory = bulk_probe_contract.get("allowed_memory", {})
    deterministic_reports = bulk_deterministic.get("reports", {})
    deterministic_artifacts = bulk_deterministic.get("artifacts", {})
    reproduction_files = {
        item.get("file"): item
        for item in bulk_reproducibility.get("files", [])
        if isinstance(item, dict)
    }

    checks.append(
        check(
            "usb_bulk_probe_all_required_reports_pass",
            set(bulk_report_statuses) == set(EXPECTED_BULK_PROBE_REPORTS)
            and all(status == "pass" for status in bulk_report_statuses.values())
            and set(bulk_report_fail_counts) == set(EXPECTED_BULK_PROBE_REPORTS)
            and all(count == 0 for count in bulk_report_fail_counts.values())
            and bulk_deterministic.get("status") == "pass"
            and set(deterministic_reports) == EXPECTED_BULK_REPORT_STATUSES
            and all(status == "pass" for status in deterministic_reports.values())
            and bulk_deterministic.get("hardware_contact") is False
            and len(bulk_source_checks) == 43
            and all(item.get("severity") == "pass" for item in bulk_source_checks.values())
            and "mechanically inert" in bulk_summary
            and "was not uploaded to a printer" in bulk_summary
            and "guarded" in bulk_hardware_plan.lower(),
            "Every required bulk-parser report must exist, carry a passing status or zero fail markers, agree with the deterministic rollup, and retain offline-only handoff documents.",
            evidence=f"{USB_BULK_PROBE_DIR}/deterministic-test-results.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_lane_contract_matches_stock_models",
            bulk_probe_contract.get("status") == "pass"
            and set(bulk_probe_contract.get("bulk_registers", [])) == EXPECTED_BULK_REGISTERS
            and set(bulk_contract_checks)
            == {
                "bulk_lane_matches_interrupt_model",
                "descriptor_submit_matches_rearm_model",
                "callback_ack_matches_contract",
                "all_bulk_registers_are_usb_only",
                "stock_elf_contains_resolved_bulk_literals",
                "saved_decompilation_preserves_bulk_contract",
            }
            and all(item.get("status") == "present" for item in bulk_contract_checks.values())
            and interrupt_bulk_lane.get("event_bit") == "0x00020000"
            and interrupt_bulk_lane.get("lane_status_register") == "0xb3000224"
            and interrupt_bulk_lane.get("lane_control_register") == "0xb3000220"
            and usb_bulk_callbacks.get("constants", {}).get("bulk_event_bit") == "0x00020000"
            and usb_bulk_callbacks.get("constants", {}).get("usb_endpoint_ack_register")
            == "0xb3000220"
            and shim_contract.get("bulk_read_state", {}).get("wait_event_bit") == "0x00020000"
            and shim_contract.get("hardware_receive_lane", {}).get("lane_status_register")
            == "0xb3000224"
            and shim_contract.get("hardware_receive_lane", {}).get("lane_control_register")
            == "0xb3000220"
            and {"0xb3000220", "0xb3000224"}.issubset(probe_registers)
            and ("0xb3000224", "read") in bulk_mmio_accesses
            and ("0xb3000224", "write") in bulk_mmio_accesses
            and ("0xb3000220", "write") in bulk_mmio_accesses
            and all(
                bulk_source_checks.get(name, {}).get("severity") == "pass"
                for name in (
                    "bulk_completion_poll",
                    "bulk_completion_ack_and_control",
                    "bulk_rearm_paths",
                )
            ),
            "The combined allowlist and probe disassembly must preserve the stock bank-1/lane-1 event bit, status register, and acknowledgement register without substituting another USB lane.",
            evidence="analysis/usb-path/usb-bulk-probe-contract.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_descriptor_buffer_submit_contract_matches",
            usb_bulk_rearm.get("constants", {}).get("descriptor_pool") == "0x90021370"
            and usb_bulk_rearm.get("constants", {}).get("bulk_buffer_base") == "0x900216f0"
            and usb_bulk_rearm.get("constants", {}).get("descriptor_submit_register")
            == "0xb3000234"
            and shim_contract.get("descriptor_rearm", {}).get("descriptor_pool") == "0x90021370"
            and shim_contract.get("descriptor_rearm", {}).get("bulk_buffer_base") == "0x900216f0"
            and shim_contract.get("descriptor_rearm", {}).get("descriptor_submit_register")
            == "0xb3000234"
            and probe_allowed_memory.get("bulk_descriptor")
            == {"start": "0x90021370", "end": "0x9002137f"}
            and probe_allowed_memory.get("bulk_buffer")
            == {"start": "0x900216f0", "end": "0x90021aef"}
            and probe_registers.get("0xb3000234", {}).get("allowed_write_values")
            == ["0x90021370"]
            and ("0xb3000234", "write") in bulk_mmio_accesses
            and ("usb_bulk_transfer_descriptor", "write") in bulk_memory_accesses
            and ("usb_bulk_receive_buffer", "read") in bulk_memory_accesses
            and all(
                bulk_source_checks.get(name, {}).get("severity") == "pass"
                for name in (
                    "exact_16_byte_descriptor_construction",
                    "descriptor_alignment",
                    "descriptor_submit",
                )
            ),
            "The stock re-arm model, shim contract, combined allowlist, memory scan, and disassembly must agree on descriptor 0x90021370, buffer 0x900216f0, and submit register 0xb3000234.",
            evidence=f"{USB_BULK_PROBE_DIR}/memory-boundary-scan.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_exact_parser_scope_and_matrix_pass",
            bulk_parser_model.get("status") == "pass"
            and bulk_parser_model.get("failures") == []
            and bulk_coverage
            == {
                "assertions": 425,
                "assertions_passed": 425,
                "generated_samples_discovered": 11,
                "generated_samples_passed": 11,
                "synthetic_cases": 33,
                "synthetic_cases_passed": 33,
                "total_cases": 44,
                "total_cases_passed": 44,
            }
            and set(item.get("name") for item in bulk_generated_samples)
            == EXPECTED_BULK_GENERATED_SAMPLES
            and set(item.get("name") for item in bulk_matrix_cases) == EXPECTED_BULK_MATRIX_CASES
            and len(bulk_generated_samples) == len(EXPECTED_BULK_GENERATED_SAMPLES)
            and len(bulk_matrix_cases) == len(EXPECTED_BULK_MATRIX_CASES)
            and all(item.get("status") == "pass" for item in bulk_all_cases)
            and bulk_probe_types
            == [
                (0, "0x00", "ZJT_START_DOC"),
                (1, "0x01", "ZJT_END_DOC"),
                (2, "0x02", "ZJT_START_PAGE"),
                (3, "0x03", "ZJT_END_PAGE"),
                (4, "0x04", "ZJT_JBIG_BIH"),
                (5, "0x05", "ZJT_JBIG_BID"),
                (6, "0x06", "ZJT_END_JBIG"),
            ]
            and all(
                item.get("status") == "pass"
                for item in bulk_parser_model.get("evidence_checks", [])
            )
            and any(
                item.get("name") == "probe_scope_matches_controlled_sample_types_0x00_through_0x06"
                and item.get("status") == "pass"
                for item in bulk_parser_model.get("evidence_checks", [])
            )
            and bulk_source_checks.get("recognized_type_bound_7", {}).get("severity") == "pass"
            and all(
                bulk_source_checks.get(f"counter_update_{name}", {}).get("severity") == "pass"
                for name in (
                    "bytes_received",
                    "receive_descriptors_completed",
                    "recognized_chunks",
                    "parser_errors",
                    "unknown_chunks",
                )
            )
            and bulk_deterministic.get("parser_coverage") == bulk_coverage,
            "The executable model and deterministic rollup must preserve exactly 11 generated samples, 33 boundary/error cases, 425 assertions, and recognized types 0x00 through 0x06.",
            evidence=f"{USB_BULK_PROBE_DIR}/parser-model.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_has_no_mechanical_or_print_side_effects",
            bulk_parser_model.get("scope", {}).get("execution") == "offline host-side only"
            and bulk_parser_model.get("scope", {}).get("hardware_access")
            == "none; no USB device, MMIO, video, or engine path exists in this model"
            and bulk_parser_model.get("scope", {}).get("mechanical_behavior")
            == "none; payloads are length-counted and discarded"
            and bulk_all_cases
            and all(
                item.get("parser_state", {}).get("side_effects") == EXPECTED_BULK_SIDE_EFFECTS
                for item in bulk_all_cases
            )
            and bool(bulk_safety)
            and nested_fail_count(bulk_safety) == 0
            and all(item.get("kind") == "usb_mmio" for item in bulk_safety)
            and bool(bulk_usb_contract)
            and nested_fail_count(bulk_usb_contract) == 0
            and all(item.get("kind") == "mapped_usb_mmio" for item in bulk_usb_contract)
            and bool(bulk_usb_mmio)
            and nested_fail_count(bulk_usb_mmio) == 0
            and all(item.get("register") in probe_registers for item in bulk_usb_mmio)
            and bool(bulk_memory)
            and nested_fail_count(bulk_memory) == 0
            and all(item.get("kind") != "unclassified_hardware_alias" for item in bulk_memory)
            and bulk_source_checks.get("no_engine_video_mechanical_mmio", {}).get("severity")
            == "pass"
            and bulk_source_checks.get("hardware_alias_literal_allowlist", {}).get("severity")
            == "pass"
            and bulk_source_checks.get("no_alternate_xqx_magic", {}).get("severity") == "pass"
            and bulk_source_checks.get(
                "polling_masks_cpu_interrupts_before_usb_setup", {}
            ).get("severity")
            == "pass"
            and "never reaches engine, video, laser, fuser, motor, or paper-feed code"
            in bulk_summary,
            "Offline parser cases and every source/disassembly boundary scan must show zero USB-host contact, print dispatch, video, engine, or mechanical side effects.",
            evidence=f"{USB_BULK_PROBE_DIR}/safety-scan.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_status_descriptor_exposes_all_counters",
            bulk_status_descriptor.get("status") == "pass"
            and bulk_status_descriptor.get("descriptor_text") == EXPECTED_STATUS_DESCRIPTOR
            and bulk_status_descriptor.get("section", {}).get("address") == 0x10003400
            and bulk_status_descriptor.get("section", {}).get("size") == 0x7C
            and bulk_status_descriptor.get("section", {}).get("flags", 0) & 0x1 == 0x1
            and set(bulk_status_checks)
            == {
                "descriptor_bytes",
                "descriptor_address",
                "descriptor_writable",
                "length_constant",
                "local_pointer",
                "hardware_alias",
                "counter_patch_calls",
                "product_selects_status_alias",
            }
            and all(item.get("status") == "pass" for item in bulk_status_checks.values())
            and set(bulk_parser_model.get("counter_definitions", {}))
            == {
                "bytes_received",
                "receive_descriptors_completed",
                "recognized_chunks",
                "parser_errors",
                "unknown_chunks",
            }
            and bulk_source_checks.get("dynamic_status_counter_macro", {}).get("severity")
            == "pass"
            and bulk_source_checks.get("dynamic_product_status_counter_calls", {}).get("severity")
            == "pass",
            "The writable product string must expose B/D/C/E/U as the parser model's bytes, descriptors, recognized chunks, errors, and unknown chunks counters.",
            evidence=f"{USB_BULK_PROBE_DIR}/status-descriptor-check.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_config_descriptors_match_controller_speed",
            bulk_config_descriptor.get("status") == "pass"
            and set(bulk_config_checks)
            == {
                "descriptor_section_address",
                "descriptor_section_size",
                "high_speed_config_shape",
                "full_speed_config_shape",
                "high_speed_bulk_packets",
                "full_speed_bulk_packets",
                "high_speed_alias",
                "full_speed_alias",
                "speed_bit_branch",
            }
            and all(item.get("status") == "pass" for item in bulk_config_checks.values())
            and bulk_config_descriptor.get("section", {}).get("address") == 0x10003300
            and bulk_source_checks.get("speed_specific_config_alias_selection", {}).get("severity")
            == "pass"
            and probe_registers.get("0xb3010000", {}).get("allowed_write_masks")
            == ["or 0x00000005"],
            "The linked printer-class configurations must advertise 512-byte high-speed and 64-byte full-speed bulk endpoints, selected from the same b3010000 speed bit used by receive setup.",
            evidence=f"{USB_BULK_PROBE_DIR}/config-descriptor-check.json",
        )
    )
    checks.append(
        check(
            "usb_bulk_probe_rebuild_is_reproducible",
            bulk_reproducibility.get("status") == "pass"
            and bulk_reproducibility.get("clean_generated_output_between_builds") is True
            and bulk_reproducibility.get("required_missing") == []
            and bulk_reproducibility.get("compared_files") == len(reproduction_files)
            and len(reproduction_files) > 0
            and all(
                item.get("status") == "pass"
                and item.get("first_sha256") == item.get("second_sha256")
                and isinstance(item.get("first_sha256"), str)
                and len(item["first_sha256"]) == 64
                for item in reproduction_files.values()
            )
            and all(
                reproduction_files.get(f"hp1020-usb-bulk-parser-draft.{suffix}", {}).get(
                    "second_sha256"
                )
                == deterministic_artifacts.get(suffix, {}).get("sha256")
                and deterministic_artifacts.get(suffix, {}).get("bytes", 0) > 0
                for suffix in ("elf", "img", "dl", "map")
            ),
            "Two clean builds must produce byte-identical generated files, and the second-build firmware hashes must match the deterministic artifact rollup.",
            evidence=f"{USB_BULK_PROBE_DIR}/reproducibility-check.json",
        )
    )
    raster_fields = read_json("analysis/open-firmware-model/raster-field-semantics.json")
    raster_semantics = {
        item.get("field"): item
        for item in raster_fields.get("field_semantics", [])
        if isinstance(item, dict)
    }
    raster_cases = {
        item.get("case"): item
        for item in raster_fields.get("case_matrix", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "raster_field_semantics_keep_host_to_video_chain",
            raster_fields.get("status") == "pass"
            and len(raster_cases) >= 11
            and {"work +0x84", "work +0x88", "work +0x8c", "work +0x90", "payload +0x48", "payload +0x54"}.issubset(
                raster_semantics
            )
            and raster_cases.get("a4_default", {}).get("work_0x84_0x88_0x8c_0x90") == "9600/6824/128/0x5c"
            and raster_cases.get("a4_600x600", {}).get("work_0x84_0x88_0x8c_0x90") == "4864/6824/128/0x5c"
            and raster_cases.get("legal_default", {}).get("payload_0x48") == 6388
            and all(item.get("status") == "present" for item in raster_fields.get("checks", [])),
            "Raster field semantics must preserve the host ZjStream/JBIG to work/raster object chain consumed by video hardware.",
            evidence="analysis/open-firmware-model/raster-field-semantics.json",
        )
    )

    boundary = read_json("analysis/hardware-boundary/hardware-boundary.json")
    unsafe_functions = {
        item["function"]
        for item in boundary.get("function_boundaries", [])
        if item.get("must_avoid_in_custom_probe")
    }
    required_unsafe_tokens = [
        "0x10015214 hp1020_video_render_or_dma_candidate",
        "0x100140f8 hp1020_video_refresh_raw_bands_candidate",
        "0x10014910 hp1020_video_prepare_page_candidate",
        "0x10015c68 hp1020_engine_status_io_candidate",
        "0x10015df8 hp1020_engine_status_poll_candidate",
        "0x10016164 hp1020_engine_message_dispatch_candidate",
    ]
    checks.append(
        check(
            "hardware_boundary_keeps_engine_video_unsafe",
            all(token in unsafe_functions for token in required_unsafe_tokens),
            "The do-not-touch boundary for early custom firmware must still include video and engine paths.",
            evidence="analysis/hardware-boundary/hardware-boundary.json",
        )
    )

    first_page = read_json("analysis/hardware-boundary/first-page-hardware-sequence.json")
    register_semantics = read_json("analysis/hardware-boundary/video-engine-register-semantics.json")
    sequence_by_step = {
        item.get("step"): item
        for item in first_page.get("sequence", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "first_page_sequence_keeps_video_engine_registers_ordered",
            first_page.get("source_case") == "a4_default"
            and first_page.get("source_reports", {}).get("engine_topology")
            == "analysis/hardware-boundary/engine-print-topology.json"
            and first_page.get("source_reports", {}).get("video_prepare_projection")
            == "analysis/hardware-boundary/video-prepare-projection.json"
            and first_page.get("source_reports", {}).get("video_refill_topology")
            == "analysis/hardware-boundary/video-refill-topology.json"
            and sequence_by_step.get(2, {}).get("risk") == "high"
            and sequence_by_step.get(5, {}).get("projected_state", {}).get("stride_plus_0xb8") == 1200
            and sequence_by_step.get(5, {}).get("projected_state", {}).get("state_plus_0xbc") == 1200
            and sequence_by_step.get(5, {}).get("projected_state", {}).get("state_plus_0xc8_state_200") == 2
            and sequence_by_step.get(6, {}).get("projected_registers", {}).get("0xb2000008", {}).get("value") == 9600
            and "0x10014244 -> 0x10013f34" in sequence_by_step.get(7, {}).get("function", "")
            and "0xb2080004"
            in sequence_by_step.get(7, {}).get("projected_registers", {}).get("normal_refill_unsafe_registers", {}).get("value", "")
            and "+0xdc"
            in sequence_by_step.get(7, {}).get("projected_registers", {}).get("normal_refill_state_fields", {}).get("value", "")
            and len(first_page.get("remaining_unknowns", [])) >= 4,
            "The first-page hardware sequence must preserve the ordered engine/video/refill risk boundary.",
            evidence="analysis/hardware-boundary/first-page-hardware-sequence.json",
        )
    )
    video_dataflow = read_json("analysis/hardware-boundary/video-dataflow-contract.json")
    dataflow_stages = {
        item.get("stage"): item
        for item in video_dataflow.get("contract_stages", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_dataflow_contract_keeps_a4_default_path",
            video_dataflow.get("status") == "pass"
            and video_dataflow.get("source_case") == "a4_default"
            and dataflow_stages.get("host_raster_fields", {}).get("known_values", {}).get("work +0x84") == 9600
            and dataflow_stages.get("host_raster_fields", {}).get("known_values", {}).get("payload +0x48") == 6364
            and dataflow_stages.get("video_prepare_geometry", {}).get("known_values", {}).get("video state +0xb8 stride") == 1200
            and dataflow_stages.get("render_initial_transfer", {}).get("known_values", {}).get("0xb2040008") == 6364
            and dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("video state +0xcc max chunk units") == 4
            and dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("video state +0xd0") == 6824
            and dataflow_stages.get("helper_channel_b_refill", {}).get("remaining_unknown")
            == "live counter decrement/completion behavior; the VIDEO_Y source is statically proven"
            and dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("0xb2080008 first refill") == 4800
            and "min(4, +0xd0) * stride(1200)"
            == dataflow_stages.get("helper_channel_b_refill", {}).get("known_values", {}).get("0xb2080008")
            and "A pointer plus dual-output window(1200) when dual-block mode is active"
            == dataflow_stages.get("raw_band_queue_feed", {}).get("known_values", {}).get("0xb1000108")
            and all(item.get("status") == "present" for item in video_dataflow.get("checks", [])),
            "The video dataflow contract must preserve concrete a4_default values through render/refill boundary formulas.",
            evidence="analysis/hardware-boundary/video-dataflow-contract.json",
        )
    )
    direct_work = read_json("analysis/hardware-boundary/zjs-direct-work.json")
    semantic_core = read_json("analysis/open-firmware-model/semantic-core/validation.json")
    checks.append(check("direct_start_page_and_native_semantics_verified",
                        direct_work["status"] == "pass" and len(direct_work["checks"]) == 43
                        and all(c["status"] == "present" for c in direct_work["checks"])
                        and semantic_core["status"] == "pass" and semantic_core["total_cases"] >= 509
                        and semantic_core["sideband_source_known"] is True
                        and set(semantic_core["sanitizers"]) == {"address", "undefined"},
                        "Direct stock ELF work creation and native semantic parser must both pass.",
                        evidence="analysis/hardware-boundary/zjs-direct-work.json"))
    target_c = read_json("analysis/open-firmware-model/semantic-target/validation.json")
    image = read_json("analysis/open-firmware-model/image-core/validation.json")
    image_target = image.get("target") or {}
    checks.append(check("open_streaming_image_decoder_verified",
                        image["status"] == image_target.get("status") == "pass"
                        and len(image["cases"]) == 176 and len(image["normalization"]) == 21
                        and len(image["mutations"]) == 32 and len(image_target.get("cases", [])) == 66
                        and image_target.get("reproducible") is True
                        and image_target.get("a4_state_history_band_bytes") == 11512
                        and image_target.get("interpreter", {}).get("status") == "pass"
                        and all(c["status"] == "pass" for c in image["cases"] + image_target.get("cases", []))
                        and image_target.get("elf_sha256") == hashlib.sha256((ROOT_DIR/"analysis/open-firmware-model/image-core/target/target-check.elf").read_bytes()).hexdigest()
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in {**image["source_sha256"], **image["fixture_sha256"], **image["sample_sha256"]}.items()),
                        "Open packed-row decoding must match full host pixel oracles and bounded target execution; it is separate from engine integration and printing.",
                        evidence="analysis/open-firmware-model/image-core/validation.json"))
    image_pages = read_json("analysis/open-firmware-model/image-core/page-validation.json")
    page_target = image_pages.get("target") or {}
    checks.append(check("open_complete_file_image_path_verified",
                        image_pages["status"] == page_target.get("status") == "pass"
                        and len(image_pages["cases"]) == 57 and len(page_target.get("cases", [])) == 35
                        and page_target.get("elf_sha256") == image_target.get("elf_sha256")
                        and all(c["status"] == "pass" for c in image_pages["cases"] + page_target.get("cases", []))
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in {**image_pages["source_sha256"], **image_pages["fixture_sha256"], **image_pages["sample_sha256"]}.items()),
                        "Complete-file parser/planner/decoder output and default padding must agree with host pixel oracles and target checks, separately from physical output.",
                        evidence="analysis/open-firmware-model/image-core/page-validation.json"))
    image_stream = read_json("analysis/open-firmware-model/image-core/stream-validation.json")
    stream_target = image_stream.get("target") or {}
    detailed_page = image_stream.get("generated_detailed_page", {})
    detailed_target = [c for c in stream_target.get("cases", []) if c["case"].startswith("detailed-legal/")]
    checks.append(check("open_bounded_stream_image_path_verified",
                        image_stream["status"] == stream_target.get("status") == "pass"
                        and len(image_stream["cases"]) == 66 and len(stream_target.get("cases", [])) == 44
                        and len(image_stream["retained_mode_controls"]) == 3
                        and sum(c.get("retained_rasters") == 128 and c["result"] == 3 for c in image_stream["retained_mode_controls"]) == 2
                        and sum(c.get("retained_pages") == 16 and c["result"] == 3 for c in image_stream["retained_mode_controls"]) == 1
                        and any(c["case"] == "page-metadata-reuse/65" and c["stats"][0] == 0 and c["stats"][2] == 65 for c in image_stream["cases"])
                        and stream_target.get("elf_sha256") == image_target.get("elf_sha256")
                        and stream_target.get("state_and_memory_bytes") == 91032
                        and detailed_page.get("raw_bytes") == 10112256
                        and detailed_page.get("raw_sha256") == "1bd14b6f517eb823062ce9652aaeaaca887efd11dec7158669419f67daa8c2ce"
                        and detailed_page.get("bie_sha256") == "91accfaa54aff62fa845646818c82ad151665c08de973fa7b8ee843e1fe0f8b8"
                        and detailed_page.get("zjs_sha256") == "b52e5309b482464832f738075f8865964ba5c9af09a2c279b396ca26b5946bcd"
                        and len(detailed_target) == 2
                        and all(c["stats"][0] == 0 and c["stats"][5] == 10112256 and c["stats"][7] == 161
                                and c["stats"][8] <= 65552 and c["stats"][9] == 0 for c in detailed_target)
                        and all(c["status"] == "pass" for c in image_stream["cases"] + stream_target.get("cases", []))
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in {**image_stream["source_sha256"], **image_stream["fixture_sha256"], **image_stream["sample_sha256"]}.items()),
                        "Bounded stream consumption must preserve large source images with reused packets/chunks, validated errors and legacy retained-mode limits. Fixed software storage is not engine or printing evidence.",
                        evidence="analysis/open-firmware-model/image-core/stream-validation.json"))
    checks.append(check("compiled_semantic_target_verified",
                        target_c["status"] == "pass" and target_c["total_cases"] == 78
                        and target_c["negative_control_payload_cases"] == 12
                        and read_json("analysis/open-firmware-model/semantic-target/reproducibility.json")["status"] == "pass"
                        and target_c["executed_instructions"] > 19000000
                        and target_c["negative_memory_checks"] == 4
                        and read_json("analysis/toolchain-probe/c-compiler-profile.json")["status"] == "pass"
                        and not {"quou","quos","loop","loopnez","entry","retw","retw.n","cust0","minu","maxu","min","max","sext","abs","mul16u","mul16s"}.intersection(target_c["executed_opcodes"]),
                        "Actual BE/call0 parser and planner must agree with native and independent model expectations in RAM-only execution.",
                        evidence="analysis/open-firmware-model/semantic-target/validation.json"))
    original = read_json("analysis/open-firmware-model/stock-execution/validation.json")
    checks.append(check("original_parser_differential_execution",
                        original["status"] == "pass" and original["totals"]["parser_agreement"] == 59
                        and sum(original["totals"].values()) == 9841
                        and all(c["status"] == "pass" for c in original["checks"])
                        and any(c["name"] == "be_bit_branch_regression" for c in original["checks"]),
                        "Original parser and libc bytes must agree with independent oracles, with environment substitutes explicit.",
                        evidence="analysis/open-firmware-model/stock-execution/validation.json"))
    qemu = read_json("analysis/open-firmware-model/semantic-target/qemu.json")
    checks.append(check("independent_qemu_execution",
                        qemu["status"] == "pass" and qemu["target_cases"] == target_c["total_cases"]
                        and qemu["libc_cases"] == {k: original["totals"][k] for k in ("memset","memcpy","memmove","strlen")}
                        and qemu["arithmetic_cases"] == {k:768 for k in ("signed_divide","signed_remainder","unsigned_divide","unsigned_remainder")}
                        and len(qemu["parser_cases"]) == original["totals"]["parser_agreement"]
                        and len(qemu["lifecycle_cases"]) == 12 and qemu["lifecycle_counterexample"]["status"] == "reproduced"
                        and qemu["windows"]["total_cases"] == 90 and all(qemu["windows"]["vector_entries"].values())
                        and qemu["windows"]["mutation"]["status"] == "detected"
                        and qemu["notification_receiver_word_indices"] == {"46":[2,3],"47":[3]}
                        and qemu["elf_sha256"] == target_c["elf_sha256"]
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h for p,h in qemu["source_sha256"].items()),
                        "Independent QEMU must agree on target C, original parser/lifecycle, arithmetic and six window handlers; source provenance must be current.",
                        evidence="analysis/open-firmware-model/semantic-target/qemu.json"))
    admission = read_json("analysis/open-firmware-model/stock-execution/admission.json")
    checks.append(check("original_stream_admission_execution",
                        admission["status"] == "pass" and admission["total_cases"] == 79
                        and admission["reproduced_counterexamples"] == 8
                        and all(c["status"] == "pass" for c in admission["cases"])
                        and all(len(c["parser_entries"]) == 2 and c["pc"] == "0x1000e7dd" for c in admission["counterexamples"])
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/p).read_bytes()).hexdigest() == h for p,h in admission["source_sha256"].items()),
                        "Original language recognition and buffering must preserve normal admission and reproduce the conditional delayed-empty-document witness.",
                        evidence="analysis/open-firmware-model/stock-execution/admission.json"))
    original_status = read_json("analysis/hardware-boundary/stock-status-execution.json")
    checks.append(check("original_status_differential_execution",
                        original_status["status"] == "pass" and original_status["cases"] >= 133941
                        and not original_status["counterexamples"]
                        and original_status["all_instructions_covered"] and original_status["all_branch_outcomes_covered"],
                        "Original status decision instructions must agree with the model; I/O and command intent boundaries remain intercepted.",
                        evidence="analysis/hardware-boundary/stock-status-execution.json"))
    page_plan = read_json("analysis/open-firmware-model/page-plan.json")
    checks.append(check("portable_page_plan_boundary",
                        page_plan["status"] == "pass" and page_plan["total_cases"] == 1398
                        and page_plan["bands_checked"] > 5000000
                        and page_plan["generated_cases"]["a4_default"]["bands"] == 1706
                        and page_plan["generated_cases"]["a4_2400x600"]["result"] == 2
                        and page_plan["generated_cases"]["a4_logical_clip"]["result"] == 1,
                        "Native page planning must retain corrected window arithmetic and reject unsupported/mismatched fixtures.",
                        evidence="analysis/open-firmware-model/page-plan.json"))
    metadata = read_json("analysis/open-firmware-model/metadata-bounds.json")
    checks.append(check("stock_metadata_split_boundary_explicit",
                        metadata["status"] == "pass" and metadata["bounded_cases"] == 10 and metadata["invalid_cases"] == 1
                        and [c["case"] for c in metadata["cases"] if c["status"] == "invalid"] == ["matrix-a4_logical_clip"],
                        "The logical-clip full-payload model must not be mistaken for bounded stock metadata handling.",
                        evidence="analysis/open-firmware-model/metadata-bounds.json"))
    callbacks = read_json("analysis/hardware-boundary/raster-callbacks.json")
    bypass = read_json("analysis/hardware-boundary/raster-bypass.json")
    callback_scenario = dict(datastore_32=0,work_plus_0x36=0,lane_selector=0,secondary_output=False)
    page_config_cases = [c for name in ("pages","page-fragments")
                         for c in read_json(f"analysis/open-firmware-model/stock-execution/{name}.json")["cases"]]
    checks.append(check("stock_value_selects_bounded_raster_bypass",
                        bypass["status"] == "pass" and bypass["stock_entry"]["value"] == 1
                        and bypass["total_cases"] == 42 and bypass["raw_buffer_selections"] == 34
                        and bypass["custom_call_boundary_stops"] == 8
                        and bypass["custom_callbacks_executed"] == bypass["completed_lifecycles"] == 0
                        and len(bypass["relocation_cases"]) == 2
                        and all(c["entry_32_unchanged"] and c["changed_entries"] == list(range(23))
                                for c in bypass["relocation_cases"])
                        and all(c["band"]["outcome"] == "raw_buffer_selected"
                                for c in bypass["cases"] if c["config_source"] == "file_backed_stock")
                        and all(c["raw_and_output_buffers_unchanged"] and len(c["rejected_pc_controls"]) == 4
                                for c in bypass["cases"])
                        and all(hashlib.sha256((ROOT_DIR/"scripts"/name).read_bytes()).hexdigest() == digest
                                for name,digest in bypass["source_sha256"].items())
                        and len(page_config_cases) == 36
                        and all(c["stock_raster_config"] == dict(index=32,value_before=1,value_after=1,
                                                               descriptor_unchanged=True,boot_proven=False)
                                for c in page_config_cases)
                        and video_dataflow["assumed_runtime_config"] == first_page["assumed_runtime_config"] == callback_scenario
                        and callbacks["stock_datastore_32"]["file_value"] == 1
                        and callbacks["stock_datastore_32"]["live_value_proven"] is False,
                        "The file-backed bypass, excluded callback boundaries and conditional model configuration must remain distinct from boot, page lifecycles and physical printing.",
                        evidence="analysis/hardware-boundary/raster-bypass.json"))
    raw_contract = read_json("analysis/hardware-boundary/raw-buffer-contract.json")
    raw_cases = sum((raw_contract[name] for name in
                    ("builder_cases", "dispatch_cases", "selection_cases", "retirement_cases")), [])
    raw_findings = [c for c in raw_contract["retirement_cases"]
                    if c["outcome"] == "conditional_unprefixed_release_address"]
    checks.append(check("stock_raw_buffer_contract_fragments_verified",
                        raw_contract["status"] == "pass"
                        and [len(raw_contract[name]) for name in
                             ("builder_cases", "dispatch_cases", "selection_cases", "retirement_cases", "raw_mode_controls")] == [8,22,14,24,2]
                        and all(c["status"] == "pass" for c in raw_cases)
                        and raw_contract["completed_lifecycles"] == raw_contract["custom_callbacks_executed"] == 0
                        and raw_contract["allocator_executed"] is False
                        and all(c["source_kind"] == (1 if c["input_kind"] == 1 else 2)
                                and c["result_pointer"] == (c["supplied_pointer"] if c["input_kind"] == 1 else "0x0")
                                for c in raw_contract["builder_cases"])
                        and sum(c["alternate"] is not None for c in raw_contract["dispatch_cases"]) == 8
                        and sum(c["empty_head"] for c in raw_contract["selection_cases"]) == 2
                        and all(c["selector"] == 2 for c in raw_contract["selection_cases"] if c["selector_source"] == "stock_file")
                        and all(c["stop"] == "0x10014560" for c in raw_contract["raw_mode_controls"])
                        and len(raw_findings) == 2 and all(c["free_requests"] == ["0x22703ff0", "0x22700200"] for c in raw_findings)
                        and raw_contract["image_band"]["bytes"] == 4800
                        and raw_contract["image_band"]["sha256"] == "a48ef1518cc7f900888d02f1ee9a4713b0acd580a9516500f82f0566bcca3351"
                        and raw_contract["image_band"]["image_elf_sha256"] == image_target.get("elf_sha256")
                        and raw_contract["stock_elf_sha256"] == hashlib.sha256((ROOT_DIR/"analysis/sihp1020.elf").read_bytes()).hexdigest()
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in raw_contract["source_sha256"].items()),
                        "Raw producer, dispatch, pointer and conditional retirement fragments must retain separate selectors and prefix/free-request findings; they do not establish allocator ownership, physical output or completed lifecycles.",
                        evidence="analysis/hardware-boundary/raw-buffer-contract.json"))
    raw_producer = read_json("analysis/hardware-boundary/raw-producer.json")
    admitted_raw = sum((raw_producer[name] for name in
                       ("producer_admission_cases", "reference_cases", "metadata_controls")), [])
    checks.append(check("stock_raw_producer_and_admission_verified",
                        raw_producer["status"] == "pass"
                        and [len(raw_producer[name]) for name in
                             ("producer_admission_cases", "reference_cases", "metadata_controls", "release_cases")] == [32,16,4,8]
                        and raw_producer["completed_lifecycles"] == 0
                        and all(c["status"] == "pass" and c["allocator_and_queue_executed"]
                                and c["engines"] == ["bounded_interpreter", "independent_qemu"]
                                and c["message_type"] == 9
                                and c["message_selector"] == (3,0,1,2)[c["selector"]]
                                and c["appended"] == (c["selector"] == 0)
                                and c["producer_reference_bytes"] == c["fill"]*257
                                and c["image_and_inputs_unchanged"] for c in admitted_raw)
                        and all(c["result_references"] ==
                                (1 if c["active"] == 1 else
                                 ((c["copies"] or 1)*2)&65535 if c["duplex"] == 1 and c["document_source"] != 1 else
                                 (c["copies"] or 1)) for c in admitted_raw)
                        and all(c["status"] == "pass" and c["allocator_executed"] and c["queue_executed"]
                                and c["completed_lifecycles"] == 0 and c["supplied_image_prefix_bytes"] == 16
                                and c["remaining_references"] == c["initial_references"]-1
                                and c["remaining_allocations"] ==
                                (2 if c["initial_references"] > 1 else 0 if c["input_kind"] == 1 else 1)
                                and c["raw_refresh_stop"] == "0x1001455a"
                                and len(c["rejected_before_execution"]) == 6 for c in raw_producer["release_cases"])
                        and raw_producer["stock_elf_sha256"] == raw_contract["stock_elf_sha256"]
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in raw_producer["source_sha256"].items()),
                        "Original raw construction and queue admission must retain explicit owner/prefix assumptions, 16-bit reference behavior and separate one-completion allocator results; they are not completed page lifecycles.",
                        evidence="analysis/hardware-boundary/raw-producer.json"))
    raw_parser = read_json("analysis/hardware-boundary/raw-parser.json")
    raw_parser_admitted = [c for c in raw_parser["cases"] if c["admission_executed"]]
    raw_parser_empty = [c for c in raw_parser["cases"] if not c["admission_executed"]]
    checks.append(check("stock_chunk12_parser_and_raw_admission_verified",
                        raw_parser["status"] == "pass"
                        and raw_parser["admission_cases"] == len(raw_parser_admitted) == 22
                        and raw_parser["metadata_only_controls"] == len(raw_parser_empty) == 2
                        and raw_parser["completed_lifecycles"] == 0
                        and all(c["status"] == "pass" and c["completed_lifecycles"] == 0
                                and not c["standalone_helper_entered"]
                                and c["engines"] == ["bounded_interpreter", "independent_qemu"]
                                and c["input_bytes"] == c["consumed_bytes"]
                                and hashlib.sha256(bytes.fromhex(c["input_hex"])).hexdigest() == c["input_sha256"]
                                for c in raw_parser["cases"])
                        and all(c["outcome"] == "raw_message_admitted"
                                and c["message_types"] == [1,3,5]+([41] if c["separate_bih_chunk"] else [])+[9,6,2]
                                and c["message_selector"] == 3
                                and len(c["data_allocations"]) == (2 if c["separate_bih_chunk"] else 1)
                                and c["data_allocations"][-1] == dict(size=16,kind=0,pointer=c["input_pointer"])
                                and (not c["separate_bih_chunk"] or
                                     (c["data_allocations"][0]["size"] == 20 and c["data_allocations"][0]["kind"] == 0
                                      and c["bih_source_freed"] is True))
                                and c["work_bih_fields"] == ([32,4,4] if c["separate_bih_chunk"] and c["page_bitmap"] == 1 else [0,0,0])
                                and c["source_kind"] == (1 if c["bitmap"] == 0 else 0)
                                and c["pointer_delta_from_allocation"] == c["raw_irq_flag"] == 0
                                and c["admitted_references"] == c["copies"]
                                and c["pending_message_types"] == [6,2]
                                and c["owner_hierarchy_origin"] == "original queued document/page/work messages"
                                for c in raw_parser_admitted)
                        and sum(c["fallback_dimensions"] for c in raw_parser_admitted) == 2
                        and sum(c["separate_bih_chunk"] for c in raw_parser_admitted) == 8
                        and sum(c["source_kind"] == 1 and c["work_bih_fields"] == [32,4,4] for c in raw_parser_admitted) == 2
                        and all(c["outcome"] == "metadata_only_no_raw_message" and c["empty_data"]
                                and c["message_types"] == [1,3,5,6,2] and c["data_allocations"] == []
                                for c in raw_parser_empty)
                        and raw_parser["stock_elf_sha256"] == raw_producer["stock_elf_sha256"]
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in raw_parser["source_sha256"].items()),
                        "Actual chunk-12 parsing must retain original ownership construction, unchanged allocation cursor, zero raw-IRQ flag and queued endings; admission is not raw completion, another model's support or a completed page lifecycle.",
                        evidence="analysis/hardware-boundary/raw-parser.json"))
    raw_handoffs = raw_parser["handoff_cases"]
    raw_prepared = [c for c in raw_handoffs if c["outcome"] == "pre_peripheral_prepare"]
    raw_no_dimensions = [c for c in raw_handoffs if c["outcome"] == "zero_stride_predivision_stop"]
    checks.append(check("stock_chunk12_serialized_prepare_boundary_verified",
                        raw_parser["handoff_prepare_cases"] == len(raw_prepared) == 8
                        and raw_parser["handoff_dimension_controls"] == len(raw_no_dimensions) == 4
                        and len(raw_handoffs) == 12
                        and "scripts/hp1020_raw_handoff.py" in raw_parser["source_sha256"]
                        and raw_parser["immediate_raw_mode_byte_stores"] ==
                            [dict(pc="0x1000f271",bytes="292474",operands=[9,2,116])]
                        and {(c["fill"],c["bitmap"],c["copies"]) for c in raw_prepared} ==
                            {(f,b,n) for f in (0,204) for b in (0,1) for n in (1,2)}
                        and {(c["fill"],c["page_bitmap"],c["separate_bih_chunk"]) for c in raw_no_dimensions} ==
                            {(f,p,p == 0) for f in (0,204) for p in (0,1)}
                        and all(c["status"] == "pass" and c["completed_lifecycles"] == 0
                                and c["engines"] == ["bounded_interpreter","independent_qemu"]
                                and c["image_unchanged"] and len(c["rejected_before_execution"]) == 13
                                and [s["phase"] for s in c["stages"]] ==
                                    ["admission","job_endings","printmgr_request","video_queued","prepare_boundary"]
                                and all(s["raw_irq_flag"] == 0 and s["references"] == c["copies"]
                                        and s["input_pointer"] == c["stages"][0]["input_pointer"]
                                        and s["payload_sha256"] == c["stages"][0]["payload_sha256"]
                                        and s["source_kind"] == (1 if c["bitmap"] == 0 else 0)
                                        for s in c["stages"])
                                and all(w["field"] == "video_irq_mode" and w["pc"] == "0x10014bac"
                                        for w in c["tracked_stores"])
                                for c in raw_handoffs)
                        and all(c["prepare_stop"] == "0x10014baf" and c["prepare_stride"] == 4
                                and c["page_bitmap"] == 1 and c["separate_bih_chunk"]
                                and c["video_mode_word"] == 0
                                and c["output_layout"]["all_spans_inside_original_allocations"]
                                and c["output_layout"]["buffers_unchanged"]
                                and c["output_layout"]["first_slot_bytes"] == 8192
                                and c["output_layout"]["second_slot_bytes"] == 16384
                                and c["output_layout"]["first_unused_tail"] == 6400
                                and len(c["tracked_stores"]) == 1 for c in raw_prepared)
                        and all(c["prepare_stop"] == "0x10014a51" and c["prepare_stride"] == 0
                                and c["tracked_stores"] == [] and c["output_layout"] is None
                                for c in raw_no_dimensions),
                        "Serialized original handoffs must preserve the actual image cursor and zero raw mode through RAM preparation using original output allocations; supplied task/media state and pre-peripheral stops do not establish native page completion or physical output.",
                        evidence="analysis/hardware-boundary/raw-parser.json"))
    buffer_cases = raw_parser["video_buffer_cases"]
    buffer_release = [c for c in buffer_cases if "release_and_reuse" in c]
    buffer_limits = [c for c in buffer_cases if "release_and_reuse" not in c]
    initialized = [c["video_initialization"] for c in raw_handoffs]+buffer_release
    checks.append(check("stock_video_buffer_initialization_and_ownership_verified",
                        raw_parser["video_buffer_release_cases"] == len(buffer_release) == 2
                        and raw_parser["video_buffer_capacity_controls"] == len(buffer_limits) == 4
                        and "scripts/hp1020_video_buffers.py" in raw_parser["source_sha256"]
                        and {(c["pool_size"],c["fill"]) for c in buffer_cases} ==
                            {(n,f) for n in (131072,16384,65536) for f in (0,204)}
                        and all(c["status"] == "pass" and c["completed_lifecycles"] == 0
                                and c["engines"] == ["bounded_interpreter","independent_qemu"]
                                and c["parser_owners_and_image_unchanged"]
                                and not c["hardware_tail_executed"] and not c["retry_executed"]
                                and len(c["rejected_before_execution"]) == 6 for c in buffer_cases)
                        and all(c["outcome"] == "initialized_before_peripherals"
                                and c["stop"] == "0x100147e3" and c["pool_size"] == 131072
                                and [a["size"] for a in c["allocations"]] == [39168,65536]
                                and len(c["registered_handlers"]) == 5 for c in initialized)
                        and all(c["release_and_reuse"]["same_addresses_reused"]
                                and c["release_and_reuse"]["original_live_allocations_unchanged"]
                                and c["release_and_reuse"]["final_video_pointers"] == [0,0]
                                and c["release_and_reuse"]["completed_page_lifecycles"] == 0
                                for c in buffer_release)
                        and all(c["outcome"] == "allocation_failed_before_retry"
                                and c["stop"] == ("0x1001486c" if c["pool_size"] == 16384 else "0x100148ad")
                                and len(c["allocations"]) == (0 if c["pool_size"] == 16384 else 1)
                                and c["registered_handlers"] == {} for c in buffer_limits),
                        "Original buffer allocation, idle initialization, release and reuse must remain distinct from page lifecycles; smaller synthetic pools stop before retry scheduling and all constructor hardware remains excluded.",
                        evidence="analysis/hardware-boundary/raw-parser.json"))
    software_ring = read_json("analysis/hardware-boundary/software-ring.json")
    checks.append(check("decoded_pixels_in_original_ring_storage_verified",
                        software_ring["status"] == "pass"
                        and software_ring["buffer_transfer_cases"] == len(software_ring["cases"]) == 8
                        and software_ring["completed_page_lifecycles"] == 0
                        and software_ring["stock_elf_sha256"] == raw_parser["stock_elf_sha256"]
                        and software_ring["raw_parser_report_sha256"] == hashlib.sha256(
                            (ROOT_DIR/"analysis/hardware-boundary/raw-parser.json").read_bytes()).hexdigest()
                        and software_ring["image"]["bytes"] == 4800
                        and software_ring["image"]["rows"] == 4 and software_ring["image"]["stride"] == 1200
                        and software_ring["image"]["bie_sha256"] == hashlib.sha256(
                            (ROOT_DIR/"analysis/open-firmware-model/image-core/fixtures/9600x132-stripe128-edges.jbg").read_bytes()).hexdigest()
                        and software_ring["image"]["target_elf_sha256"] == image["target"]["elf_sha256"]
                        and set(software_ring["bands"]) == {"1","4"}
                        and all(software_ring["bands"][str(r)]["rows"] == r
                                and software_ring["bands"][str(r)]["bytes"] == r*1200 for r in (1,4))
                        and software_ring["bands"]["4"]["sha256"] == software_ring["image"]["sha256"]
                        and {(c["fill"],c["initial_index"],c["image_rows"]) for c in software_ring["cases"]} ==
                            {(f,i,r) for f in (0,204) for i in (0,3) for r in (1,4)}
                        and all(c["status"] == "pass" and c["completed_page_lifecycles"] == c["hardware_transfers"] == 0
                                and c["engines"] == ["bounded_interpreter","independent_qemu"]
                                and c["final_index"] == (c["initial_index"]+1)&3
                                and c["all_image_bytes_equal"] and c["only_selected_slot_changed"]
                                and c["source_owners_and_pool_unchanged"] and c["image_bytes"] == c["image_rows"]*1200
                                and c["image_sha256"] == software_ring["bands"][str(c["image_rows"])]["sha256"]
                                and c["occupied_guard_stop"] == c["no_remaining_guard_stop"] == "0x1001429a"
                                and c["nonfinal_collision_stop"] == "0x100140f6"
                                and len(c["rejected_before_execution"]) == 13
                                and len(c["supplied_boundaries"]) == 5
                                and [s["phase"] for s in c["stages"]] ==
                                    ["prepared","claimed_before_pixels","software_pixels_copied","fill_published",
                                     "final_buffer_selected","output_accounted","descriptor_released"]
                                and c["stages"][1]["descriptor"] == [1,1,c["image_rows"]]
                                and c["stages"][1]["target_sha256"] == c["stages"][0]["target_sha256"]
                                and all(s["target_sha256"] == c["image_sha256"] for s in c["stages"][2:])
                                and c["stages"][-1]["descriptor"] == [0,1,c["image_rows"]]
                                and c["stages"][-1]["indices"] == [c["final_index"]]*3
                                and c["stages"][-1]["remaining"] == [0,0]
                                for c in software_ring["cases"])
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in software_ring["source_sha256"].items()),
                        "Decoded pixels must match every selected-slot byte through explicitly supplied fill/acceptance/completion boundaries; claimed buffers, host-selected wrap indices and released descriptors do not prove native page lifecycles or physical output.",
                        evidence="analysis/hardware-boundary/software-ring.json"))
    checks.append(check("decoded_pixels_continuous_ring_ownership_verified",
                        software_ring["sequence_cases"] == len(software_ring["sequences"]) == 2
                        and software_ring["sequence_buffer_transfers"] == 10
                        and software_ring["sequence_image"]["rows"] == 17
                        and software_ring["sequence_image"]["bytes"] == 20400
                        and {c["fill"] for c in software_ring["sequences"]} == {0,204}
                        and all(c["status"] == "pass" and c["completed_page_lifecycles"] == c["hardware_transfers"] == 0
                                and c["engines"] == ["bounded_interpreter","independent_qemu"]
                                and c["buffer_transfers"] == len(c["produced"]) == len(c["selected"]) == 5
                                and [p["index"] for p in c["produced"]] == [p["index"] for p in c["selected"]]
                                    == c["retired"] == [0,1,2,3,0]
                                and [p["rows"] for p in c["produced"]] == [p["rows"] for p in c["selected"]] == [4,4,4,4,1]
                                and [p["source_offset"] for p in c["produced"]] ==
                                    [p["source_offset"] for p in c["selected"]] == [0,4800,9600,14400,19200]
                                and [p["sha256"] for p in c["produced"]] == [p["sha256"] for p in c["selected"]]
                                and c["image_bytes"] == 20400 and c["image_rows"] == 17
                                and c["image_sha256"] == c["output_sha256"] == software_ring["sequence_image"]["sha256"]
                                and c["all_image_bytes_equal"] and c["whole_buffer_guards_equal"]
                                and c["source_owners_and_pool_unchanged"]
                                and c["final_indices"] == [1,1,1] and c["final_remaining"] == [0,0]
                                and len(c["supplied_boundaries"]) == 6 and len(c["rejected_before_execution"]) == 13
                                and c["events"][0]["indices"] == [0,0,0]
                                and c["events"][0]["remaining"] == [17,17]
                                and {e["phase"] for e in c["events"]} >=
                                    {"nonfinal_withheld","full_ring_producer_blocked","accepted_without_completion_still_blocked",
                                     "descriptor_released","no_remaining_data"}
                                and all(e["descriptors"][0][0] == 1 for e in c["events"]
                                        if e["phase"] in ("full_ring_producer_blocked","accepted_without_completion_still_blocked"))
                                and all(e["descriptors"][e["index"]][0] == 1 for e in c["events"]
                                        if e["phase"] == "output_accounted_still_owned")
                                and all(d[0] == 0 for d in c["events"][-1]["descriptors"])
                                for c in software_ring["sequences"]),
                        "Original ring indices must wrap only after actual claims/publications/accounting/releases; a full ring and accepted-but-uncompleted slot retain ownership, while physical readiness and completion remain supplied.",
                        evidence="analysis/hardware-boundary/software-ring.json"))
    submission = read_json("analysis/hardware-boundary/output-submission.json")
    submission_cases = submission["cases"]
    submission_excluded = {"0x10013f4c", "0x10013ff9", "0x1001402b", "0x10014037",
                           "0x10014052", "0x10014063", "0x10014071", "0x10014076",
                           "0x10014083", "0x1001409c", "0x100140ac", "0x100140c7",
                           "0x100140eb", "0x10015648"}
    submission_phases = {False: ["single_pointer", "single_count"],
                         True: ["dual_pointer_a", "dual_pointer_b", "dual_quotient", "dual_count"]}
    checks.append(check("original_output_submission_arithmetic_before_mmio_verified",
                        submission["status"] == "pass" and len(submission_cases) == 30
                        and submission["completed_native_page_lifecycles"] == submission["usb_transfers"]
                            == submission["peripheral_instructions_executed"] == 0
                        and submission["stock_elf_sha256"] == hashlib.sha256(
                            (ROOT_DIR/"analysis/sihp1020.elf").read_bytes()).hexdigest()
                        and len(submission["instruction_anchors"]) == 23
                        and len(submission["original_byte_ranges"]) == 3
                        and {c["case"]["fill"] for c in submission_cases} == {0,204}
                        and sum(c["case"]["dual"] for c in submission_cases) == 14
                        and sum(c["case"]["zero_divisor_control"] for c in submission_cases) == 4
                        and sum(c["case"]["count_flag_overlap_control"] for c in submission_cases) == 4
                        and all(c["interpreter"]["observed"] == c["qemu"]["observed"]
                                and c["interpreter"]["arena_sha256"] == c["qemu"]["arena_sha256"]
                                and [p["observed"] for p in c["interpreter"]["phases"]]
                                    == [p["observed"] for p in c["qemu"]["phases"]]
                                and c["case"]["geometry_source"] == "supplied_arithmetic_controls"
                                and c["case"]["selector_source"] ==
                                    ("explicit_RAM_value_1" if c["case"]["dual"] else "file_backed_value_2")
                                for c in submission_cases)
                        and all(c[e]["status"] == "pass" and c[e]["observed"] == c[e]["oracle"]
                                and c[e]["all_nonstack_ram_unchanged"]
                                and c[e]["peripheral_instructions_executed"] == 0
                                and set(c[e]["rejected_before_execution"]) == submission_excluded
                                and [p["phase"] for p in c[e]["phases"]] == submission_phases[c["case"]["dual"]]
                                and sum(p["divide_executed"] for p in c[e]["phases"]) == 1
                                and all(p["original_entry"] == "0x10013f34"
                                        and p["original_entry"] in p["visited"] and p["resume"] in p["visited"]
                                        and p["stop_before"] not in p["visited"]
                                        and not (set(p["visited"]) & submission_excluded)
                                        and p["all_nonstack_ram_unchanged"] and p["other_a2_through_a15_zero"]
                                        for p in c[e]["phases"])
                                for c in submission_cases for e in ("interpreter", "qemu"))
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in submission["source_sha256"].items()),
                        "Original output address/count construction must stop before every peripheral instruction; explicit register cuts, synthetic geometry, selector overrides and omitted readiness remain separate from native lifecycles, pixel packing and physical acceptance.",
                        evidence="analysis/hardware-boundary/output-submission.json"))
    image_ring = read_json("analysis/open-firmware-model/image-core/ring-validation.json")
    ring_target = image_ring.get("target") or {}
    ring_trace_phases = {"prepared":0,"fill_published":1,"nonfinal_withheld":2,
                        "full_ring_producer_blocked":3,"output_accounted_still_owned":4,
                        "accepted_without_completion_still_blocked":5,"descriptor_released":6,"no_remaining_data":7}
    original_ring_traces = {c["fill"]:[[ring_trace_phases[e["phase"]],*e["indices"],*e["remaining"],
                            *[v for d in e["descriptors"] for v in d]]
                            for e in c["events"] if e["phase"] in ring_trace_phases]
                            for c in software_ring["sequences"]}
    checks.append(check("compiled_decoder_to_software_output_ring_verified",
                        image_ring["status"] == ring_target.get("status") == "pass"
                        and len(image_ring["cases"]) == len(ring_target.get("cases",[])) == 36
                        and image_ring["completed_native_page_lifecycles"] == 0
                        and image_ring["stock_ring_report_sha256"] == hashlib.sha256(
                            (ROOT_DIR/"analysis/hardware-boundary/software-ring.json").read_bytes()).hexdigest()
                        and image_ring["stock_ring_source_sha256"] == software_ring["source_sha256"]
                        and ring_target.get("elf_sha256") == image_target.get("elf_sha256")
                        and ring_target.get("api_controls") == len(image_ring["api_controls"]) == 11
                        and {c["case"] for c in image_ring["api_controls"]} == set(range(11))
                        and all(c["status"] == "pass" and c["sticky_error"] and c["owned_storage_preserved"]
                                for c in image_ring["api_controls"])
                        and {(c["width_bits"],c["rows"],c["fill"],c["fragment"]) for c in image_ring["cases"]} ==
                            {(w,r,f,n) for w,r in ((9600,17),(9600,132),(1024,129),(512,33),(32,8),(16384,4))
                             for f in (0,204) for n in (1,7,65536)}
                        and sum(c["original_trace_equal"] for c in image_ring["cases"]) == 6
                        and all(c["trace"] == original_ring_traces[c["fill"]]
                                for c in image_ring["cases"] if c["original_trace_equal"])
                        and all(c["status"] == "pass" and c["stats"][0:5] == [2,0,c["rows"],c["rows"],c["rows"]]
                                and c["stats"][10:12] == [0,1] and c["stats"][17:19] == [0,1]
                                and c["stats"][9] == max(0,c["stats"][5]-4)
                                and c["stats"][21:24] == [c["stats"][5]&3]*3 for c in image_ring["cases"])
                        and all(t["status"] == "pass" and t["case"] == c["case"]
                                and t["all_output_bytes_equal"] and t["all_storage_bytes_equal"]
                                and t["ownership_trace_equal"]
                                and t["stats"][:14]+t["stats"][16:] == c["stats"][:14]+c["stats"][16:]
                                for c,t in zip(image_ring["cases"],ring_target.get("cases",[])))
                        and ring_target.get("a4_component_storage_bytes") == image_target.get("a4_state_history_band_bytes")
                            +19200+ring_target.get("a4_ring_state_bytes",0)
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in {**image_ring["source_sha256"],**image_ring["fixture_sha256"]}.items()),
                        "One compiled C decoder/ring fixture must preserve all pixels, whole-buffer guards, backpressure and the original bounded ownership trace; its explicit software consumer does not establish native page cleanup or physical output.",
                        evidence="analysis/open-firmware-model/image-core/ring-validation.json"))
    image_output = read_json("analysis/open-firmware-model/image-core/output-validation.json")
    output_target = image_output.get("target") or {}
    output_cases = image_output.get("cases",[])
    checks.append(check("bounded_documents_to_software_output_verified",
                        image_output["status"] == output_target.get("status") == "pass"
                        and len(output_cases) == len(output_target.get("cases",[])) == 45
                        and image_output["completed_native_page_lifecycles"] == 0
                        and output_target.get("elf_sha256") == image_target.get("elf_sha256")
                        and sum(c["expected_result"] == 0 for c in output_cases) == 31
                        and all(c["status"] == "pass" and c["source_prefix_equal"]
                                and c["stats"][0] == c["expected_result"]
                                and c["stats"][32] == c["completed_documents"] == c["expected_completed_documents"]
                                and c["stats"][10:12] == [0,1] and c["stats"][19] == 1
                                and (c["stats"][23] == 0 and c["stats"][26] == 1 if c["expected_result"] else
                                     c["full_output_equal"] and c["stats"][23] == 1 and c["stats"][18] == 0
                                     and c["stats"][2] == c["stats"][17] == c["stats"][28])
                                for c in output_cases)
                        and all(c["consumer_mode"] in (0,1,2,3) for c in output_cases)
                        and {c["seed_counter"] for c in output_cases if c["case"].startswith("counter-overflow/")} == {1,2,3,4}
                        and all(c["stats"][0] == 3 and c["stats"][5] == 0 for c in output_cases if c["seed_counter"])
                        and sum(c["stats"][17] == 65 and c["stats"][23] == 1 for c in output_cases) == 2
                        and {c["consumer_mode"] for c in output_cases if not c["expected_result"]} == {0,1,2}
                        and any(c["case"] == "missing-end-doc" and c["stats"][5] == 158400
                                and c["stats"][17] == 1 and c["stats"][7:9] == [33,33]
                                and c["stats"][18] == c["stats"][22] == c["stats"][32] == 0
                                and c["expected_result"] == 5 and c["full_output_equal"] for c in output_cases)
                        and all(c["stats"][13] == 3 and c["stats"][18] == 1 and c["stats"][32] == 0
                                for c in output_cases if c["case"].startswith("final-drain/"))
                        and any(c["case"] == "consumer/after=1" and c["stats"][7:9] == [1,0]
                                and c["stats"][18] == 4 for c in output_cases)
                        and all(t["status"] == "pass" and t["case"] == c["case"]
                                and t["all_output_bytes_equal"] and t["all_storage_bytes_equal"]
                                and t["page_and_write_traces_equal"]
                                and t["stats"][:14]+t["stats"][15:] == c["stats"][:14]+c["stats"][15:]
                                for c,t in zip(output_cases,output_target.get("cases",[])))
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in {**image_output["source_sha256"],**image_output["fixture_sha256"],
                                                    **image_output["sample_sha256"]}.items()),
                        "Whole-document output must preserve exact pixels across geometry changes, completion ordering and reused input; late input/consumer failures retain ownership and cannot be reported as successful printing.",
                        evidence="analysis/open-firmware-model/image-core/output-validation.json"))
    receive = read_json("analysis/usb-path/receive-core/validation.json")
    receive_cases = receive.get("cases", [])
    receive_target = receive.get("target") or {}
    checks.append(check("bounded_receive_document_ownership_and_restart_verified",
                        receive["status"] == receive_target.get("status") == "pass"
                        and receive["usb_transfers"] == receive["completed_native_page_lifecycles"] == 0
                        and len(receive_cases) == len(receive_target.get("cases", [])) == 75
                        and receive_target.get("state_and_memory_bytes") == 128200
                        and receive_target.get("elf_sha256") == hashlib.sha256(
                            (ROOT_DIR/"analysis/usb-path/receive-core/target/target-check.elf").read_bytes()).hexdigest()
                        and all(c["status"] == "pass" and c["event_count"] == len(c["steps"])
                                and all(s[23:25] == [0,1] for s in c["steps"])
                                and c["steps"][-1][11] == c["output_bytes"]
                                and c["completed_documents"] == c["steps"][-1][48]
                                and all(len(row) == 49 for row in c["steps"]) for c in receive_cases)
                        and any(c["case"] == "document/truncated" and c["output_bytes"] == 158400
                                and not c["source_prefix_only"] and c["completed_documents"] == 0
                                and c["steps"][-1][13:16] == [33,33,0]
                                and c["steps"][-1][18:20] == [1,1] and c["steps"][-1][25] == 0
                                for c in receive_cases)
                        and all(t["status"] == "pass" and t["case"] == c["case"]
                                and t["all_steps_equal"] and t["all_pixels_and_storage_equal"]
                                and t["state_and_memory_bytes"] == 128200
                                for c,t in zip(receive_cases,receive_target.get("cases",[])))
                        and sum(c["case"].startswith("status/") for c in receive_cases) == 32
                        and sum(c["case"].startswith("endpoint-wide-fault/") for c in receive_cases) == 4
                        and sum(c["case"].startswith("cancel/") for c in receive_cases) == 6
                        and sum(c["case"].startswith("document/mixed/") and c["steps"][-1][10] == 1
                                for c in receive_cases) == 6
                        and sum(c["case"].startswith("document/output-failure-recovery/")
                                and c["steps"][-1][1] == 2 and c["steps"][-1][10] == 1
                                and any(s[0] == 8 and s[13:16] == [1,0,1] for s in c["steps"])
                                for c in receive_cases) == 2
                        and any(c["case"] == "document/65-changing-pages" and c["steps"][-1][18:20] == [65,65]
                                for c in receive_cases)
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in {**receive["source_sha256"],**receive["fixture_sha256"],
                                                    **receive["sample_sha256"]}.items()),
                        "Bounded receive ownership must preserve FIFO data, exact pixels and stopped storage, reject stale events, and require both external quiescence acknowledgements before restart. Software transfer observations do not establish hardware USB/reset/printing.",
                        evidence="analysis/usb-path/receive-core/validation.json"))
    checks.append(check("raster_callback_argument_and_unknown_isa_boundary",
                        callbacks["status"] == "pass" and callbacks["call_contract"]["argument_count"] == 4
                        and [len(f["unknown_instructions"]) for f in callbacks["functions"]] == [16,40,84],
                        "Stock raster callbacks must preserve fourth stride argument and explicit unresolved ISA effects.",
                        evidence="analysis/hardware-boundary/raster-callbacks.json"))
    for variant in ("minimal-idle","usb-register-snapshot","usb-marker-draft","usb-bulk-parser-draft"):
        gate = read_json(f"analysis/open-firmware-probes/{variant}/instruction-gate.json")
        checks.append(check(f"{variant}_reachable_instructions_defined",
                            gate["status"] == "pass" and gate["unknown_instructions"] == 0
                            and len(gate["roots"]) == 7 and len(gate["rejected_mutations"]) == 5,
                            "Inert probes may execute only defined allowed instructions and proven constant trampolines.",
                            evidence=f"analysis/open-firmware-probes/{variant}/instruction-gate.json"))
    queue_payload_chain = read_json("analysis/hardware-boundary/video-queue-payload-chain.json")
    queue_chain_checks = {
        item.get("name"): item
        for item in queue_payload_chain.get("checks", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_queue_payload_chain_identifies_prepare_work_object",
            queue_payload_chain.get("status") == "pass"
            and queue_payload_chain.get("conclusion", {}).get("prepare_argument_identity")
            == "0x94-byte video/page work object"
            and "direct START_PAGE builder writes VIDEO_Y to active work +0x26"
            in queue_payload_chain.get("conclusion", {}).get("effect_on_remaining_units", "")
            and len(queue_payload_chain.get("stages", [])) == 10
            and queue_chain_checks.get("pending_node_payload_is_direct_param_2", {}).get("status") == "present"
            and queue_chain_checks.get("list_helpers_do_not_rewrite_payload_word", {}).get("status") == "present"
            and queue_chain_checks.get("printmgr_moves_same_node_pending_to_active", {}).get("status") == "present"
            and queue_chain_checks.get("video_thread_uses_payload_as_prepare_argument", {}).get("status") == "present"
            and queue_chain_checks.get("work_populate_does_not_copy_page_param_0x26", {}).get("status") == "present"
            and all(item.get("status") == "present" for item in queue_payload_chain.get("checks", [])),
            "The video queue payload chain must preserve that prepare receives the 0x94 work object, with VIDEO_Y written directly into work +0x26.",
            evidence="analysis/hardware-boundary/video-queue-payload-chain.json",
        )
    )
    prepare_fields = read_json("analysis/hardware-boundary/video-prepare-argument-fields.json")
    prepare_field_rows = {
        item.get("field"): item
        for item in prepare_fields.get("fields", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_prepare_argument_fields_resolve_direct_sources",
            prepare_fields.get("status") == "pass"
            and prepare_fields.get("prepare_argument_identity") == "0x94-byte video/page work object"
            and prepare_field_rows.get("+0x84/+0x88/+0x8c/+0x90", {}).get("source_status") == "sourced"
            and prepare_field_rows.get("+0x26", {}).get("source_status") == "sourced"
            and prepare_field_rows.get("+0x30", {}).get("source_status") == "sourced"
            and prepare_field_rows.get("+0x32", {}).get("source_status") == "sourced"
            and prepare_field_rows.get("+0x74", {}).get("source_status") == "default_zero_for_current_path"
            and prepare_fields.get("field_status_counts", {}).get("unsourced_active_work", 0) == 0
            and all(item.get("status") == "present" for item in prepare_fields.get("checks", [])),
            "The prepare argument field model must keep render geometry sourced with +0x26/+0x30/+0x32 sourced directly on active work.",
            evidence="analysis/hardware-boundary/video-prepare-argument-fields.json",
        )
    )
    sideband_census = read_json("analysis/hardware-boundary/video-sideband-write-census.json")
    census_checks = {
        item.get("name"): item
        for item in sideband_census.get("checks", [])
        if isinstance(item, dict)
    }
    census_roles = sideband_census.get("role_counts", {})
    overlap_roles = sideband_census.get("overlap_role_counts", {})
    checks.append(
        check(
            "video_sideband_write_census_rules_out_false_leads",
            sideband_census.get("status") == "pass"
            and sideband_census.get("corpus_summary", {}).get("files_scanned", 0) >= 600
            and census_roles.get("direct_work_writer") == 3
            and census_roles.get("active_work_consumer") == 4
            and census_roles.get("scaled_index_false_lead") == 1
            and census_roles.get("runtime_byte_to_work_0x90") == 2
            and len(sideband_census.get("active_work_writer_hits", [])) == 3
            and len(sideband_census.get("ghidra_sideband_overlap_store_scan", {}).get("hits", [])) == 103
            and overlap_roles.get("direct_work_exact_store") == 3
            and overlap_roles.get("video_state_ring_clear") == 1
            and census_checks.get("child_record_0x13_is_not_work_0x26", {}).get("status") == "present"
            and census_checks.get("runtime_byte_0x13_feeds_work_0x90_not_sideband", {}).get("status") == "present"
            and census_checks.get("ghidra_overlap_scan_finds_no_work_populate_or_jobmgr_sideband_writer", {}).get("status")
            == "present"
            and census_checks.get("direct_active_work_writers_found", {}).get("status") == "present"
            and all(item.get("status") == "present" for item in sideband_census.get("checks", [])),
            "The sideband write census must preserve that selected +0x26/+0x30/+0x32 hits and overlap hits include three direct active work-object writers alongside consumers and false leads.",
            evidence="analysis/hardware-boundary/video-sideband-write-census.json",
        )
    )
    sideband_copy = read_json("analysis/hardware-boundary/video-sideband-copy-direction.json")
    checks.append(
        check(
            "video_sideband_copy_direction_rules_out_hidden_source",
            sideband_copy.get("status") == "pass"
            and sideband_copy.get("helper", {}).get("argument_order") == "destination, source, length"
            and sideband_copy.get("sideband_call", {}).get("interpreted_as")
            == "memcpy(dst=PTR_DAT_10006304 runtime block, src=iStack_84 BIH payload, len=0x14)"
            and set(sideband_copy.get("effect_on_prepare_fields", {}).get("still_unsourced", []))
            == set()
            and all(item.get("status") == "present" for item in sideband_copy.get("checks", [])),
            "The sideband copy-direction model must preserve that case 0x29 copies BIH payload out to runtime block, not into work +0x26/+0x30/+0x32.",
            evidence="analysis/hardware-boundary/video-sideband-copy-direction.json",
        )
    )
    sideband_impact = read_json("analysis/hardware-boundary/video-sideband-default-impact.json")
    sideband_impacts = {
        item.get("work_field"): item
        for item in sideband_impact.get("field_impacts", [])
        if isinstance(item, dict)
    }
    sideband_access_hits = sideband_impact.get("ghidra_video_state_access_scan", {}).get("hits", [])
    sideband_access_roles = {item.get("role") for item in sideband_access_hits if isinstance(item, dict)}
    e8_access_hits = [
        item
        for item in sideband_access_hits
        if isinstance(item, dict) and item.get("offset") == "0xe8"
    ]
    checks.append(
        check(
            "video_sideband_default_impact_keeps_0x26_critical",
            sideband_impact.get("status") == "pass"
            and sideband_impacts.get("+0x26", {}).get("risk") == "critical"
            and sideband_impacts.get("+0x32", {}).get("risk") == "mode_critical"
            and sideband_impacts.get("+0x30", {}).get("risk") == "unknown_low_in_current_static_view"
            and len(sideband_access_hits) == 19
            and {"channel_b_refill_counter", "descriptor_final_accounting", "descriptor_b_flag", "raw_refresh_b_flag", "stack_local_false_positive"}.issubset(
                sideband_access_roles
            )
            and len(e8_access_hits) == 1
            and e8_access_hits[0].get("role") == "prepare_seed"
            and all(item.get("status") == "present" for item in sideband_impact.get("checks", [])),
            "The sideband default-impact model must keep +0x26 as print-path critical, +0x32 mode-critical, +0x30 lower priority, and classify the exact-offset Ghidra access scan.",
            evidence="analysis/hardware-boundary/video-sideband-default-impact.json",
        )
    )
    zero_sideband = read_json("analysis/hardware-boundary/video-zero-sideband-scenario.json")
    zero_steps = {
        item.get("step"): item
        for item in zero_sideband.get("scenario", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_zero_sideband_scenario_keeps_refill_blocker_narrow",
            zero_sideband.get("status") == "pass"
            and "initial_channel_a_still_arms" in zero_steps
            and "channel_b_refill_skipped" in zero_steps
            and "raw_band_final_logic_becomes_ambiguous" in zero_steps
            and any(
                "not an immediate proof that render setup cannot start" in item
                for item in zero_sideband.get("practical_conclusion", [])
            )
            and any(
                "channel B is not seeded" in item
                for item in zero_sideband.get("practical_conclusion", [])
            )
            and all(item.get("status") == "present" for item in zero_sideband.get("checks", [])),
            "The zero-sideband scenario must keep the refined conclusion: initial channel A can arm, but channel-B refill/descriptor state is not seeded.",
            evidence="analysis/hardware-boundary/video-zero-sideband-scenario.json",
        )
    )
    remaining_units = read_json("analysis/hardware-boundary/video-remaining-units.json")
    remaining_cases = {
        item.get("case"): item
        for item in remaining_units.get("case_matrix", [])
        if isinstance(item, dict)
    }
    copy_gap = {
        item.get("stage"): item
        for item in remaining_units.get("source_chain", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_remaining_units_direct_source_verified",
            remaining_units.get("status") == "pass"
            and copy_gap.get("direct_builder", {}).get("status") == "ELF-byte verified"
            and remaining_cases.get("a4_default", {}).get("video_y_from_zji_0x12") == 6824
            and remaining_cases.get("a4_default", {}).get("first_channel_b_length") == 4800
            and remaining_cases.get("letter_default", {}).get("video_y_from_zji_0x12") == 6408
            and remaining_cases.get("legal_default", {}).get("video_y_from_zji_0x12") == 8208
            and all(item.get("status") == "present" for item in remaining_units.get("checks", [])),
            "Video remaining-unit model must preserve the direct VIDEO_Y-to-work-to-counter chain.",
            evidence="analysis/hardware-boundary/video-remaining-units.json",
        )
    )
    chunk_sizing = read_json("analysis/hardware-boundary/video-chunk-sizing.json")
    chunk_cases = {
        item.get("case"): item
        for item in chunk_sizing.get("case_matrix", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_chunk_sizing_projects_stride_and_cc",
            chunk_sizing.get("status") == "pass"
            and chunk_sizing.get("helper_contract", {}).get("verified_behavior")
            == "for denominator >= 2, returns floor(numerator / denominator)"
            and chunk_sizing.get("constants", {}).get("chunk_budget_bytes_DAT_10005dc8") == 8192
            and chunk_cases.get("a4_default", {}).get("stride_plus_0xb8") == 1200
            and chunk_cases.get("a4_default", {}).get("max_chunk_units_plus_0xcc") == 4
            and chunk_cases.get("a4_600x600", {}).get("stride_plus_0xb8") == 608
            and chunk_cases.get("a4_600x600", {}).get("max_chunk_units_plus_0xcc") == 12
            and all(item.get("status") == "present" for item in chunk_sizing.get("checks", [])),
            "Video chunk sizing must preserve the stride-derived +0xcc projection and helper caveat.",
            evidence="analysis/hardware-boundary/video-chunk-sizing.json",
        )
    )
    helper_disassembly = read_json("analysis/hardware-boundary/video-helper-disassembly.json")
    checks.append(
        check(
            "video_helper_unsigned_division_instruction_verified",
            helper_disassembly.get("status") == "pass"
            and helper_disassembly.get("helper", {}).get("working_name") == "unsigned_divide"
            and helper_disassembly.get("conclusion", {}).get("status") == "instruction_verified"
            and helper_disassembly.get("validation", {}).get("executions", 0) >= 131072
            and all(item.get("status") == "present" for item in helper_disassembly.get("checks", [])),
            "Unsigned floor division must be verified against complete ELF-matched helper instructions, including loop execution.",
            evidence="analysis/hardware-boundary/video-helper-disassembly.json",
        )
    )
    semantic_sequences = {
        item.get("name"): item
        for item in register_semantics.get("semantic_sequences", [])
        if isinstance(item, dict)
    }
    semantic_registers = {
        item.get("register")
        for item in register_semantics.get("mmio_literals", [])
        if isinstance(item, dict)
    }
    semantic_registers.update(
        item.get("register")
        for item in register_semantics.get("manual_literal_cells", {}).values()
        if isinstance(item, dict) and item.get("register")
    )
    checks.append(
        check(
            "video_engine_register_semantics_resolved",
            register_semantics.get("status") == "pass"
            and {"0xb050000c", "0xb0500004", "0xb1000008", "0xb100010c", "0xb2000000", "0xb2040000", "0xb2080000"}.issubset(
                semantic_registers
            )
            and "engine_command_status_handshake" in semantic_sequences
            and "raw_band_feed" in semantic_sequences
            and all(check.get("status") == "present" for check in register_semantics.get("checks", [])),
            "The video/engine register-semantics report must keep the key engine, video, channel, and raw-band roles resolved.",
            evidence="analysis/hardware-boundary/video-engine-register-semantics.json",
        )
    )
    video_prepare_modes = read_json("analysis/hardware-boundary/video-prepare-modes.json")
    prepare_tables = {
        item.get("name"): item
        for item in video_prepare_modes.get("table_blocks", [])
        if isinstance(item, dict)
    }
    prepare_literal_values = video_prepare_modes.get("literal_values", {})
    checks.append(
        check(
            "video_prepare_modes_keep_timing_tables",
            video_prepare_modes.get("status") == "pass"
            and prepare_literal_values.get("setup_a_timing") == "0xb1000020"
            and prepare_literal_values.get("timing_table_0") == "0xb1000400"
            and len(video_prepare_modes.get("timing_modes", [])) == 8
            and len(prepare_tables.get("single_plane_1200_table", {}).get("words", [])) == 16
            and all(check.get("status") == "present" for check in video_prepare_modes.get("checks", [])),
            "The video-prepare mode model must preserve the branch-dependent 0xb100 timing/setup table evidence.",
            evidence="analysis/hardware-boundary/video-prepare-modes.json",
        )
    )
    engine_command_status = read_json("analysis/hardware-boundary/engine-command-status.json")
    engine_literals = engine_command_status.get("literal_values", {})
    engine_calls = {
        item.get("value"): item
        for item in engine_command_status.get("status_io_calls", [])
        if isinstance(item, dict)
    }
    engine_events = {
        item.get("event")
        for item in engine_command_status.get("event_decisions", [])
        if isinstance(item, dict)
    }
    engine_sequences = {
        item.get("name")
        for item in engine_command_status.get("command_sequences", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "engine_command_status_model_resolved",
            engine_command_status.get("status") == "pass"
            and engine_literals.get("engine_status_register") == "0xb050000c"
            and engine_literals.get("engine_command_register") == "0xb0500004"
            and engine_literals.get("engine_state_base") == "0x1002f0c4"
            and {
                "0x1",
                "0x20",
                "0x2",
                "0x16",
                "0x13",
                "0x0000501a",
                "0x00005043",
                "0x00003a13",
                "0x00006012",
            }.issubset(engine_calls)
            and {
                "0xe6100a01",
                "0xfe001401",
                "0x14000a04",
                "0xf6000300",
                "0xe6000d03",
            }.issubset(engine_events)
            and {
                "engine_status_io_handshake",
                "preflight_start",
                "print_dispatch_start_commands",
                "poll_transition_side_effects",
            }.issubset(engine_sequences)
            and all(check.get("status") == "present" for check in engine_command_status.get("checks", [])),
            "The engine command/status model must preserve the stock 0xb050 register pair, command IDs, state fields, and event branches.",
            evidence="analysis/hardware-boundary/engine-command-status.json",
        )
    )
    engine_decisions = read_json("analysis/hardware-boundary/engine-status-decisions.json")
    decision_scenarios = {
        item.get("name"): item
        for item in engine_decisions.get("scenarios", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "engine_status_decision_model_resolved",
            engine_decisions.get("status") == "pass"
            and engine_decisions.get("scenario_count") == 21
            and engine_decisions.get("scenario_failures") == 0
            and decision_scenarios.get("ready_rewrite", {}).get("result", {}).get("stored_event") == "0x14000a04"
            and decision_scenarios.get("substatus_0x16_ready_0x40_with_status_2_0x4040", {})
            .get("result", {})
            .get("side_effect_commands")
            == ["0x0000501a"]
            and decision_scenarios.get("leave_e6100800_sends_0x5043", {}).get("result", {}).get("side_effect_commands")
            == ["0x00005043"]
            and decision_scenarios.get("previous_0x0100_to_ready_extra_emit", {}).get("result", {}).get(
                "extra_emitted_events"
            )
            == ["0xe6100a01"]
            and all(check.get("status") == "present" for check in engine_decisions.get("checks", [])),
            "The executable engine status decision model must preserve ready rewrite, 0x501a/0x5043 side effects, and previous-event extra emit behavior.",
            evidence="analysis/hardware-boundary/engine-status-decisions.json",
        )
    )
    engine_topology = read_json("analysis/hardware-boundary/engine-print-topology.json")
    engine_topology_stages = {
        item.get("name")
        for item in engine_topology.get("topology", [])
        if isinstance(item, dict)
    }
    engine_topology_commands = engine_topology.get("important_commands", {})
    checks.append(
        check(
            "engine_print_topology_model_resolved",
            engine_topology.get("status") == "pass"
            and engine_topology.get("registers", {}).get("engine_status") == "0xb050000c"
            and engine_topology.get("registers", {}).get("engine_command") == "0xb0500004"
            and {
                "engine_thread_startup",
                "page_work_acceptance",
                "status_poll_and_recovery",
                "completion_and_deferred_work",
            }.issubset(engine_topology_stages)
            and engine_topology_commands.get("page_start_normal") == "0x00006012"
            and engine_topology_commands.get("page_start_reset_latch") == "0x00003a13"
            and engine_topology_commands.get("substatus_side_effect") == "0x0000501a"
            and engine_topology_commands.get("leave_e6100800_side_effect") == "0x00005043"
            and all(check.get("status") == "present" for check in engine_topology.get("checks", [])),
            "The engine print topology must preserve startup/preflight, page acceptance, polling/recovery, completion/deferred-work stages, and key stock engine commands.",
            evidence="analysis/hardware-boundary/engine-print-topology.json",
        )
    )
    video_feedback = read_json("analysis/hardware-boundary/video-engine-feedback.json")
    video_literals = video_feedback.get("literal_values", {})
    feedback_sequences = {
        item.get("name"): item
        for item in video_feedback.get("feedback_sequences", [])
        if isinstance(item, dict)
    }
    feedback_messages = [
        message
        for sequence in video_feedback.get("feedback_sequences", [])
        if isinstance(sequence, dict)
        for message in sequence.get("messages", [])
        if isinstance(message, dict)
    ]
    feedback_message_pairs = {(item.get("message"), item.get("payload")) for item in feedback_messages}
    checks.append(
        check(
            "video_engine_feedback_model_resolved",
            video_feedback.get("status") == "pass"
            and {
                "normal_video_done",
                "video_reset_or_flush",
                "reset_dispatch_complete_active",
                "reset_dispatch_event_words",
            }.issubset(feedback_sequences)
            and ("0x10", "original video queue payload") in feedback_message_pairs
            and ("0x25", "no event word in word 1") in feedback_message_pairs
            and ("0x11", "completion/advance") in feedback_message_pairs
            and ("0x0b", "deferred video work when present") in feedback_message_pairs
            and {"0xe6e01201", "0xe6e01202", "0xeee01b01", "0xeee01b02", "0xeee01b04"}.issubset(
                set(video_literals.values())
            )
            and all(check.get("status") == "present" for check in video_feedback.get("checks", [])),
            "The video-to-engine feedback model must preserve normal completion, reset/flush, requeue, and video event-word behavior.",
            evidence="analysis/hardware-boundary/video-engine-feedback.json",
        )
    )
    video_ring = read_json("analysis/hardware-boundary/video-transfer-ring.json")
    ring_literals = video_ring.get("literal_values", {})
    ring_sequences = {
        item.get("name")
        for item in video_ring.get("ownership_sequences", [])
        if isinstance(item, dict)
    }
    ring_scenarios = {
        item.get("name"): item
        for item in video_ring.get("ring_scenarios", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_transfer_ring_model_resolved",
            video_ring.get("status") == "pass"
            and ring_literals.get("video_state_base") == "0x1002efc0"
            and ring_literals.get("ring_descriptor_base") == "0x1002efe0"
            and ring_literals.get("channel_a_pointer") == "0xb2040004"
            and ring_literals.get("channel_b_pointer") == "0xb2080004"
            and {
                "prepare_initializes_ring",
                "render_claims_next_slot",
                "render_starts_first_transfer",
                "band_helper_refills_channel_b",
                "irq_band_done_advances_or_refills",
            }.issubset(ring_sequences)
            and ring_scenarios.get("producer_0_consumer_1", {}).get("render_result") == "busy_error_0x1003"
            and ring_scenarios.get("producer_0_consumer_0", {}).get("producer_after") == 1
            and all(check.get("status") == "present" for check in video_ring.get("checks", [])),
            "The video transfer ring model must preserve producer/consumer collision behavior, channel A/B descriptors, and IRQ refill evidence.",
            evidence="analysis/hardware-boundary/video-transfer-ring.json",
        )
    )
    video_irq = read_json("analysis/hardware-boundary/video-irq-decisions.json")
    irq_scenarios = {
        item.get("name"): item
        for item in video_irq.get("scenarios", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_irq_decision_model_resolved",
            video_irq.get("status") == "pass"
            and video_irq.get("scenario_count") == 11
            and video_irq.get("scenario_failures") == 0
            and video_irq.get("branch_priority", [None])[0] == "0x20 band done/refill"
            and irq_scenarios.get("priority_0x20_over_0x02", {}).get("decision", {}).get("category") == "band_done"
            and irq_scenarios.get("bit_0x02_reset_case_0", {}).get("decision", {}).get("reset_dispatch_param") == 0
            and irq_scenarios.get("bit_0x08_reset_case_3", {}).get("decision", {}).get("reset_dispatch_param") == 3
            and irq_scenarios.get("bit_0x10_reset_case_4", {}).get("decision", {}).get("reset_dispatch_param") == 4
            and irq_scenarios.get("bit_0x01_dispatch_case_7_when_idle", {}).get("decision", {}).get(
                "reset_dispatch_param"
            )
            == 7
            and all(check.get("status") == "present" for check in video_irq.get("checks", [])),
            "The video IRQ decision model must preserve branch priority, refill, and reset-dispatch cases 0/3/4/7.",
            evidence="analysis/hardware-boundary/video-irq-decisions.json",
        )
    )
    video_band_queue = read_json("analysis/hardware-boundary/video-band-queue.json")
    band_literals = video_band_queue.get("literal_values", {})
    band_sequences = {
        item.get("name")
        for item in video_band_queue.get("queue_sequences", [])
        if isinstance(item, dict)
    }
    band_scenarios = {
        item.get("name"): item
        for item in video_band_queue.get("loop_scenarios", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_band_queue_model_resolved",
            video_band_queue.get("status") == "pass"
            and band_literals.get("video_state_base") == "0x1002efc0"
            and band_literals.get("ring_descriptor_base") == "0x1002efe0"
            and band_literals.get("raw_band_a_pointer") == "0xb1000008"
            and band_literals.get("raw_band_b_pointer") == "0xb1000108"
            and band_literals.get("raw_band_a_flags") == "0xb100000c"
            and band_literals.get("raw_band_b_flags") == "0xb100010c"
            and {
                "queue_loop_gate",
                "optional_callback_and_padding",
                "raw_band_single_block_write",
                "raw_band_dual_block_write",
                "advance_queue_side",
            }.issubset(band_sequences)
            and band_scenarios.get("dc_0_e0_1_final_0", {}).get("loop_decision") == "stop_before_e0_collision"
            and band_scenarios.get("dc_0_e0_1_final_1", {}).get("loop_decision") == "queue_descriptor"
            and all(check.get("status") == "present" for check in video_band_queue.get("checks", [])),
            "The video band queue model must preserve +0xdc/+0xe0 collision behavior and raw-band A/B register writes.",
            evidence="analysis/hardware-boundary/video-band-queue.json",
        )
    )
    video_mode_flag = read_json("analysis/hardware-boundary/video-mode-flag.json")
    mode_literals = video_mode_flag.get("literal_values", {})
    mode_sequences = {
        item.get("name")
        for item in video_mode_flag.get("branch_sequences", [])
        if isinstance(item, dict)
    }
    mode_cases = {
        item.get("mode"): item
        for item in video_mode_flag.get("mode_cases", [])
        if isinstance(item, dict)
    }
    checks.append(
        check(
            "video_mode_flag_model_resolved",
            video_mode_flag.get("status") == "pass"
            and mode_literals.get("high_bit") == "0x80000000"
            and mode_literals.get("high_bit_clear_mask") == "0x7fffffff"
            and mode_literals.get("video_state_base") == "0x1002efc0"
            and mode_literals.get("work_object_mode_flag_offset") == "+0x74"
            and mode_literals.get("video_state_mode_flag_offset") == "+0xfc"
            and {
                "prepare_copies_work_flag_to_state_sign",
                "irq_band_done_selects_refill_family",
                "reset_dispatch_depends_on_same_sign_bit",
            }.issubset(mode_sequences)
            and mode_cases.get("descriptor_queue_mode", {}).get("work_object_plus_0x74") == 0
            and mode_cases.get("descriptor_queue_mode", {}).get("state_plus_0xfc_is_negative") is False
            and mode_cases.get("raw_linked_list_mode", {}).get("work_object_plus_0x74") == 1
            and mode_cases.get("raw_linked_list_mode", {}).get("state_plus_0xfc_is_negative") is True
            and all(check.get("status") == "present" for check in video_mode_flag.get("checks", [])),
            "The video mode-flag model must preserve the work +0x74 to state +0xfc sign-bit fork between descriptor queue and raw linked-list refill.",
            evidence="analysis/hardware-boundary/video-mode-flag.json",
        )
    )
    video_refill_topology = read_json("analysis/hardware-boundary/video-refill-topology.json")
    refill_paths = {
        item.get("name"): item
        for item in video_refill_topology.get("topology", [])
        if isinstance(item, dict)
    }
    refill_checks = video_refill_topology.get("checks", [])
    checks.append(
        check(
            "video_refill_topology_model_resolved",
            video_refill_topology.get("status") == "pass"
            and {
                "analysis/hardware-boundary/video-mode-flag.json",
                "analysis/hardware-boundary/video-irq-decisions.json",
                "analysis/hardware-boundary/video-transfer-ring.json",
                "analysis/hardware-boundary/video-band-queue.json",
            }.issubset(set(video_refill_topology.get("source_reports", [])))
            and "normal_descriptor_queue_refill" in refill_paths
            and "alternate_raw_linked_list_refill" in refill_paths
            and "+0xd8" in refill_paths.get("normal_descriptor_queue_refill", {}).get("state_fields", [])
            and "+0xdc" in refill_paths.get("normal_descriptor_queue_refill", {}).get("state_fields", [])
            and "0xb2080004" in refill_paths.get("normal_descriptor_queue_refill", {}).get("unsafe_registers", [])
            and "+0xa0" in refill_paths.get("alternate_raw_linked_list_refill", {}).get("state_fields", [])
            and all(check.get("status") == "present" for check in refill_checks),
            "The video refill topology must preserve the normal descriptor-queue path and the alternate raw linked-list path as separate unsafe video refills.",
            evidence="analysis/hardware-boundary/video-refill-topology.json",
        )
    )
    video_prepare_projection = read_json("analysis/hardware-boundary/video-prepare-projection.json")
    prepare_projection_rows = video_prepare_projection.get("projections", [])
    callback_states = []
    for projection in prepare_projection_rows:
        for scenario in projection.get("scenarios", []):
            if (
                scenario.get("datastore_0x20_zero") is True
                and scenario.get("lane_selector") == 0
                and scenario.get("secondary_output_state_plus_0xec_nonzero") is False
            ):
                callback_states.append(scenario.get("derived_state", {}))
    checks.append(
        check(
            "video_prepare_projection_narrows_generated_variants",
            video_prepare_projection.get("status") == "pass"
            and video_prepare_projection.get("projection_count") == 10
            and video_prepare_projection.get("scenario_count") == 80
            and all(projection.get("resolution") == "600x600" for projection in prepare_projection_rows)
            and all(state.get("nbie") == 1 for state in callback_states)
            and {state.get("video_bpp") for state in callback_states} == {1, 2, 4}
            and all(state.get("state_plus_0xc8_state_200") == (2 if state["video_bpp"] == 1 else state["video_bpp"]) for state in callback_states)
            and all(state.get("state_plus_0xf4") == (2 if state["video_bpp"] in (1, 2) else 0) for state in callback_states)
            and all(state.get("state_plus_0xbc") == state.get("stride_plus_0xb8") * (2 if state["video_bpp"] == 1 else 1) for state in callback_states)
            and all(check.get("status") == "present" for check in video_prepare_projection.get("checks", [])),
            "The video prepare projection must keep the generated host variants at 600dpi with distinct BPP1/2/4 setup branches, sourced independently of NBIE.",
            evidence="analysis/hardware-boundary/video-prepare-projection.json",
        )
    )
    checks.append(
        check(
            "usb_family_remains_only_low_risk_target",
            any(
                item.get("family") == "0xb300...." and item.get("risk") == "lower"
                for item in boundary.get("register_families", [])
            ),
            "USB 0xb300 must remain the only plausible early open-firmware hardware target.",
            evidence="analysis/hardware-boundary/hardware-boundary.json",
        )
    )

    pjl_contract = read_json("analysis/non-printing-status-probe/pjl-status-contract.json")
    queries = {query["name"]: query for query in pjl_contract.get("queries", [])}
    checks.append(
        check(
            "pjl_first_query_is_echo",
            pjl_contract.get("first_recommended_query") == "echo"
            and queries.get("echo", {}).get("payload_bytes") == 49
            and queries.get("echo", {}).get("stock_response_markers") == ["HP1020_STATUS_PROBE"],
            "The first stock/open comparison must remain the non-printing PJL ECHO probe.",
            evidence="analysis/non-printing-status-probe/pjl-status-contract.json",
        )
    )
    checks.append(
        check(
            "pjl_contract_is_non_printing",
            {"no PDF", "no PostScript", "no ZjStream raster", "no engine/video command from host", "no paper required"}.issubset(
                set(pjl_contract.get("safety_scope", []))
            ),
            "The status query contract must stay outside print/video/engine execution.",
            evidence="analysis/non-printing-status-probe/pjl-status-contract.json",
        )
    )

    marker_descriptor = read_json("analysis/open-firmware-probes/usb-marker-draft/marker-descriptor-check.json")
    marker_len = read_json("analysis/open-firmware-probes/usb-marker-draft/marker-length-flow-check.json")
    marker_rearm = read_json("analysis/open-firmware-probes/usb-marker-draft/marker-rearm-flow-check.json")
    marker_sequence = read_json("analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.json")
    marker_contract = read_json("analysis/open-firmware-probes/usb-marker-draft/usb-contract-scan.json")
    marker_behavior = read_json("analysis/open-firmware-probes/usb-marker-draft/behavior-model.json")
    marker_memory = read_json("analysis/open-firmware-probes/usb-marker-draft/memory-boundary-scan.json")
    checks.append(
        check(
            "usb_marker_descriptor_is_stable",
            marker_descriptor.get("descriptor_text") == "HP1020 OPEN MARKER"
            and marker_descriptor.get("section", {}).get("size") == 38
            and severity_count(marker_descriptor.get("checks", []), "fail") == 0,
            "The open marker descriptor bytes and length must remain fixed.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/marker-descriptor-check.json",
        )
    )
    checks.append(
        check(
            "usb_marker_length_flow_passes",
            severity_count(marker_len, "fail") == 0
            and len(marker_len) == 6
            and any(item.get("name") == "descriptor_word_uses_clipped_length" for item in marker_len)
            and any(item.get("name") == "selected_descriptor_length_preserved" for item in marker_len),
            "The marker draft must keep host wLength clipping connected to the selected descriptor length, endpoint-0 response state, and descriptor word.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/marker-length-flow-check.json",
        )
    )
    checks.append(
        check(
            "usb_marker_rearm_flow_passes",
            severity_count(marker_rearm, "fail") == 0
            and len(marker_rearm) == 5
            and any(item.get("name") == "rearm_returns_to_poll_loop" for item in marker_rearm),
            "The marker draft must wait for USB setup gates to clear and then return to polling after one response.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/marker-rearm-flow-check.json",
        )
    )
    checks.append(
        check(
            "usb_marker_sequence_matches_endpoint0_contract",
            severity_count(marker_sequence, "fail") == 0
            and len([item for item in marker_sequence if item.get("kind") == "endpoint0_sequence_write"]) >= 17,
            "The marker draft's USB writes must remain limited to the extracted endpoint-0 sequence.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.json",
        )
    )
    checks.append(
        check(
            "usb_marker_data_stage_submit_present",
            any(
                item.get("register") == "0xb3000014"
                and item.get("value") == "0x900226f0"
                and item.get("sequence") == "data_stage_submit"
                for item in marker_sequence
            )
            and any(
                item.get("register") == "0xb3000000"
                and item.get("value") == "0x00000108"
                and item.get("kind") == "endpoint0_or_write"
                for item in marker_sequence
            ),
            "The marker draft must submit the control-IN descriptor ring and kick the transfer path.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/endpoint0-sequence-scan.json",
        )
    )
    checks.append(
        check(
            "usb_marker_contract_has_no_engine_video_mmio",
            severity_count(marker_contract, "fail") == 0
            and all(item.get("kind") == "mapped_usb_mmio" for item in marker_contract),
            "The marker draft must stay USB-only and avoid engine/video MMIO.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/usb-contract-scan.json",
        )
    )
    checks.append(
        check(
            "usb_marker_memory_boundary_has_descriptor_ring",
            len(
                [
                    item
                    for item in marker_memory
                    if item.get("kind") == "usb_transfer_descriptor_ring" and item.get("access") == "write"
                ]
            )
            == 4
            and any(
                item.get("kind") == "usb_staging_buffer" and item.get("access") == "write"
                for item in marker_memory
            ),
            "The memory boundary scan must show the marker copy into USB staging RAM and the four descriptor-ring writes.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/memory-boundary-scan.json",
        )
    )
    marker_responses = [
        scenario
        for scenario in marker_behavior.get("scenarios", [])
        if scenario.get("decision", {}).get("result") == "marker_response"
    ]
    marker_poll_continue = [
        scenario
        for scenario in marker_behavior.get("scenarios", [])
        if scenario.get("decision", {}).get("result") == "poll_continue"
    ]
    marker_descriptors = {item["decision"].get("descriptor") for item in marker_responses}
    marker_product_responses = [
        item for item in marker_responses if item["decision"].get("descriptor") == "open marker product"
    ]
    checks.append(
        check(
            "usb_marker_behavior_models_descriptor_responder",
            {"device", "configuration", "language", "manufacturer", "open marker product"} <= marker_descriptors
            and {item["decision"].get("sequence") for item in marker_product_responses}
            == {"sequence_a", "sequence_b"}
            and any(
                item["decision"].get("descriptor") == "open marker product"
                and item["decision"].get("response_len") == 4
                for item in marker_responses
            )
            and any(
                item["decision"].get("descriptor") == "configuration"
                and item["decision"].get("response_len") == 9
                for item in marker_responses
            )
            and len(marker_poll_continue) >= 2,
            "The host-side marker model must cover standard USB descriptors, both stock product gates, clipped host length, and polling continuation for non-matching setup/gate states.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/behavior-model.json",
        )
    )
    checks.append(
        check(
            "usb_marker_behavior_models_data_stage",
            all(
                scenario["decision"].get("data_stage", {}).get("descriptor_submit_register") == "0xb3000014"
                and scenario["decision"].get("data_stage", {}).get("descriptor_submit_value") == "0x900226f0"
                and scenario["decision"].get("data_stage", {}).get("transfer_kick_or") == "0x00000108"
                and scenario["decision"].get("post_response", {}).get("after_submit") == "wait_for_gate_clear"
                and scenario["decision"].get("post_response", {}).get("when_clear") == "return_to_poll_loop"
                for scenario in marker_responses
            ),
            "The marker behavior model must include the descriptor submit register, transfer kick, and post-response rearm plan, not just the setup decision.",
            evidence="analysis/open-firmware-probes/usb-marker-draft/behavior-model.json",
        )
    )

    open_endpoint0 = read_json("analysis/usb-path/open-endpoint0-model.json")
    setup_source = read_json("analysis/usb-path/usb-setup-source.json")
    control_in = read_json("analysis/usb-path/control-in-data-stage.json")
    control_completion = read_json("analysis/usb-path/control-completion-event.json")
    usb_interrupt_events = read_json("analysis/usb-path/usb-interrupt-events.json")
    open_marker_cases = [
        scenario
        for scenario in open_endpoint0.get("scenarios", [])
        if scenario.get("open_marker") and scenario.get("label") == "product string"
    ]
    checks.append(
        check(
            "host_endpoint0_model_has_open_marker_product_string",
            any(
                "HP1020 OPEN MARKER" in scenario.get("result", {}).get("response_text", "")
                or "48 00 50 00 31 00 30 00 32 00 30 00" in scenario.get("result", {}).get("response_hex", "")
                for scenario in open_marker_cases
            ),
            "The pure host endpoint-0 model must include the open marker string response case.",
            evidence="analysis/usb-path/open-endpoint0-model.json",
        )
    )
    checks.append(
        check(
            "usb_setup_source_narrowed_to_direct_buffer",
            setup_source.get("setup_packet_base_candidate") == "0x90021348"
            and {"0x2", "0x6", "0x7"}.issubset(set(setup_source.get("stock_descriptor_branch_offsets_seen", [])))
            and setup_source.get("setup_descriptor_pointer_register") == "0xb3000210"
            and setup_source.get("out0_data_descriptor_pointer_register") == "0xb3000214"
            and setup_source.get("setup_admission") == {
                "owner_mask": "0xc0000000", "owner_value": "0x80000000", "rx_mask": "0x30000000", "rx_value": "0x00000000"}
            and setup_source.get("raw_wire_fields", {}).get("6") == "wLength low"
            and setup_source.get("stock_post_conversion_fields", {}).get("6") == "wLength high (after stock conversion)",
            "Original SETUP admission uses SUBPTR, owner 2 and RX zero; stock post-conversion fields differ from raw wire bytes and ordinary OUT0 DESPTR.",
            evidence="analysis/usb-path/usb-setup-source.json",
        )
    )
    checks.append(
        check(
            "usb_marker_reads_required_setup_fields",
            {"0x0", "0x1", "0x2", "0x3", "0x6", "0x7"}.issubset(
                set(setup_source.get("open_marker_offsets_read", []))
            ),
            "The open marker draft must read request type, request, descriptor selector, and host length before responding.",
            evidence="analysis/usb-path/usb-setup-source.json",
        )
    )
    control_constants = control_in.get("constants", {})
    scenarios_by_len = {item["response_len"]: item for item in control_in.get("scenarios", [])}
    checks.append(
        check(
            "control_in_data_stage_constants_resolved",
            control_constants.get("descriptor_flag") == "0x08000000"
            and control_constants.get("descriptor_base") == "0x900226f0"
            and control_constants.get("staging_buffer") == "0x90022bd0"
            and control_constants.get("descriptor_submit_register") == "0xb3000014"
            and control_constants.get("descriptor_submit_value") == "0x900226f0"
            and control_constants.get("initial_descriptor_submit_value") == "0x100226f0"
            and "descriptor_hardware_alias_flag" not in control_constants
            and control_in["pointer_dataflow"]["physical_address_translation_established"] is False
            and control_in["pointer_dataflow"]["pointer_controls"] == [
                {"supplied": "0x100226f0", "active": "0x100226f0", "initial": "0x900226f0"},
                {"supplied": "0x900226f0", "active": "0x900226f0", "initial": "0x100226f0"}]
            and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                    for n,h in control_in["source_sha256"].items()),
            "Byte-anchored active control-IN submissions preserve their supplied pointer. Separate HOST_BUSY initialization uses modulo-32-bit ADD, not OR; neither establishes physical address translation.",
            evidence="analysis/usb-path/control-in-data-stage.json",
        )
    )
    checks.append(
        check(
            "control_completion_event_model_resolved",
            control_completion.get("status") == "pass"
            and control_completion.get("event_object") == "0x10021318"
            and control_completion.get("control_in_wait", {}).get("requested_bits") == "0x00000001"
            and control_completion.get("usb2_thread_wait", {}).get("requested_bits") == "0x00010000",
            "The control completion path must remain modeled as event flags, with separate control-IN and USB2Thread wake bits.",
            evidence="analysis/usb-path/control-completion-event.json",
        )
    )
    checks.append(
        check(
            "usb_interrupt_event_model_resolved",
            usb_interrupt_events.get("status") == "pass"
            and usb_interrupt_events.get("constants", {}).get("usb_event_flags") == "0x10021318"
            and usb_interrupt_events.get("event_scan", {}).get("tdc_status_bit") == "0x400"
            and usb_interrupt_events.get("event_scan", {}).get("wake_hints_may_repeat") is True
            and usb_interrupt_events.get("event_scan", {}).get("wake_without_tdc_possible") is True
            and usb_interrupt_events.get("event_scan", {}).get("wake_is_successful_completion") is False
            and usb_interrupt_events.get("event_scan", {}).get("lane_stride") == "0x20"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_receive_lane", {}).get("event_bit")
            == "0x00020000"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_receive_lane", {}).get("lane_status_register")
            == "0xb3000224"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_receive_lane", {}).get("lane_control_register")
            == "0xb3000220"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_receive_lane", {}).get("descriptor_initial")
            == "0x90021370"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_receive_lane", {}).get("control_snak_mask") == "0x80"
            and usb_interrupt_events.get("event_scan", {}).get("bulk_receive_lane", {}).get("status_ack_masks")
                == ["0x200", "0x80", "0x40", "0x30", "0x400"]
            and usb_interrupt_events.get("event_scan", {}).get("bulk_buffer_updates", {}).get(
                "available_size_word"
            )
            == "0x1001bc50",
            "USB task wake hints may repeat or occur without TDC; keep status acknowledgements distinct from OUT1 control commands and from successful completions.",
            evidence="analysis/usb-path/usb-interrupt-events.json",
        )
    )
    checks.append(
        check(
            "control_in_open_marker_descriptor_shape",
            scenarios_by_len.get(38, {}).get("batches", [{}])[0].get("descriptor_count") == 1
            and scenarios_by_len.get(38, {}).get("batches", [{}])[0].get("descriptors", [{}])[0].get("control_word")
            == 0x08000026,
            "A 38-byte open marker response should model as one flagged control-IN descriptor.",
            evidence="analysis/usb-path/control-in-data-stage.json",
        )
    )
    checks.append(
        check(
            "control_in_large_response_batches",
            len(scenarios_by_len.get(321, {}).get("batches", [])) == 2
            and [batch.get("descriptor_count") for batch in scenarios_by_len.get(321, {}).get("batches", [])]
            == [5, 1],
            "Large control-IN responses should preserve the modeled five-descriptor batch limit before another kick.",
            evidence="analysis/usb-path/control-in-data-stage.json",
        )
    )

    usb_family = read_json("analysis/usb-path/controller-family.json")
    usb_rearm_cases = usb_family["rearm_cases"]
    usb_status_cases = usb_family["status_decoding_cases"]
    checks.append(check("stock_usb_descriptor_software_and_family_reference_verified",
                        usb_family["status"] == "pass"
                        and usb_family["upstream_commit"] == "adc218676eef25575469234709c2d87185ca223a"
                        and usb_family["completed_native_page_lifecycles"] == 0
                        and len(usb_family["comparisons"]) == 24
                        and all(c["status"] == "match" and c["stock_value"] == c["expected_value"]
                                and c["load_sites"] for c in usb_family["comparisons"])
                        and len(usb_family["instructions"]) == 18
                        and len(usb_family["ownership_boundary_instructions"]) == 11
                        and len(usb_family["software_drain_cases"]) == 6
                        and {(c["fill"],c["nodes"]) for c in usb_family["software_drain_cases"]} ==
                            {(f,n) for f in (0,204) for n in (0,1,4)}
                        and all(c["status"] == "pass" and c["queue_empty"]
                                and c["busy_descriptor_and_entire_arena_unchanged"]
                                and len(c["supplied_service_calls"]) == 2+2*c["nodes"]
                                for c in usb_family["software_drain_cases"])
                        and len(usb_rearm_cases) == 12
                        and {(c["fill"],c["offset"],c["next_pointer"]) for c in usb_rearm_cases} ==
                            {(f,o,p) for f in (0,204) for o in (0,37) for p in ("0x0","0x22340567","0x22340560")}
                        and all(c["status"] == "pass" and c["entire_guarded_arena_equal"]
                                and c["flags"][1:] == [0,1,0] for c in usb_rearm_cases)
                        and len(usb_status_cases) == 51
                        and all(c["status"] == "pass" and c["guarded_arena_unchanged"]
                                and c["owner_admitted"] == (c["owner"] == 2)
                                and c["decoded_count"] == (c["encoded_count"] if c["owner"] == 2 else None)
                                and c["stop"] == ("0x10008542" if c["owner"] == 2 else "0x1000867c")
                                for c in usb_status_cases)
                        and {(c["owner"],c["last"],c["encoded_count"]) for c in usb_status_cases
                             if c["receive_status"] == 0} ==
                            {(o,l,n) for o in range(4) for l in (0,1) for n in (0,1,64,512,1024,65535)}
                        and {c["receive_status"] for c in usb_status_cases if c["receive_status"]} == {1,2,3}
                        and len(usb_family["excluded_controls"]) == 2
                        and {c["engine"] for c in usb_family["excluded_controls"]} == {"interpreter","QEMU"}
                        and all(c["status"] == "rejected before execution" and c["pc"] == "0x10008762"
                                and c["effective_address"] == "0xb3000234" for c in usb_family["excluded_controls"])
                        and all(hashlib.sha256((ROOT_DIR/name).read_bytes()).hexdigest() == digest
                                for name,digest in usb_family["source_sha256"].items()),
                        "Pinned open-controller definitions and original RAM-only descriptor behavior must agree; family compatibility remains an inference, with no live USB transfer or printer lifecycle claim.",
                        evidence="analysis/usb-path/controller-family.json"))

    output_format = read_json("analysis/hardware-boundary/output-format.json")
    format_cases = output_format["cases"]
    format_tables = {"bpp1-selector0": [0,0xffffffff], "bpp1-selector1": [0,0xffffffff],
                     "bpp1-selector2": [0,31], "bpp2-selector0": [0,31,511,8191],
                     "bpp2-selector1": [0,32640,524280,4194303], "bpp2-selector2": [0,7,31,127]}
    checks.append(check("original_output_format_fragments_before_mmio_verified",
                        output_format["status"] == "pass" and len(format_cases) == 12
                        and output_format["independent_table_oracle"] == format_tables
                        and output_format["completed_native_page_lifecycles"] == output_format["usb_transfers"]
                            == output_format["peripheral_instructions_executed"] == 0
                        and len(output_format["instruction_anchors"]) == 37
                        and len(output_format["original_byte_ranges"]) == 4 and len(output_format["literals"]) == 15
                        and output_format["stock_elf_sha256"] == hashlib.sha256(
                            (ROOT_DIR/"analysis/sihp1020.elf").read_bytes()).hexdigest()
                        and {(c["case"]["bpp"],c["case"]["selector"],c["case"]["old_word"]) for c in format_cases}
                            == {(b,s,w) for b in (1,2) for s in (0,1,2) for w in (0,0xffffffff)}
                        and all(c["interpreter"]["observed"] == c["qemu"]["observed"]
                                and c["interpreter"]["memory_regions"] == c["qemu"]["memory_regions"]
                                and [w["word"] for w in c["interpreter"]["observed"]["table_words"]]
                                    == format_tables[f'bpp{c["case"]["bpp"]}-selector{c["case"]["selector"]}']
                                and c["interpreter"]["observed"]["control_mask_value"]["value"]
                                    == ((c["case"]["old_word"] & 0xfcffffff) | (0x1000000 if c["case"]["bpp"] == 2 else 0))
                                and c["interpreter"]["observed"]["stride_mask_value"]["value"]
                                    == ((c["case"]["old_word"] & 0xffff0000) | 1200)
                                for c in format_cases)
                        and all(c[e]["status"] == "pass" and c[e]["exact_nonstack_memory_match"]
                                and c[e]["peripheral_instructions_executed"] == 0
                                and len(c[e]["rejected_before_execution"]) == 29
                                and len(c[e]["phases"]) == (4 if c["case"]["bpp"] == 1 else 8)
                                and all(p["original_entry"] == "0x10014910"
                                        and p["original_entry"] in p["visited"] and p["resume"] in p["visited"]
                                        and p["stop_before"] not in p["visited"] and p["exact_nonstack_memory_match"]
                                        and not (set(p["visited"]) & set(c[e]["rejected_before_execution"]))
                                        for p in c[e]["phases"])
                                for c in format_cases for e in ("interpreter","qemu"))
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for n,h in output_format["source_sha256"].items()),
                        "Original format tables and masks must agree at explicit pre-MMIO cuts; no peripheral configuration, physical pixel meaning, polarity or output acceptance is established.",
                        evidence="analysis/hardware-boundary/output-format.json"))

    class_reset = read_json("analysis/usb-path/class-reset.json")
    reset_cases = class_reset["cases"]
    checks.append(check("original_class_reset_before_control_transfer_verified",
                        class_reset["status"] == "pass" and len(reset_cases) == 20
                        and len(class_reset["instruction_anchors"]) == 18
                        and len(class_reset["original_byte_ranges"]) == 9
                        and class_reset["completed_native_page_lifecycles"] == class_reset["usb_transfers"]
                            == class_reset["completed_usb_control_transfers"] == class_reset["peripheral_instructions_executed"] == 0
                        and class_reset["stock_elf_sha256"] == hashlib.sha256(
                            (ROOT_DIR/"analysis/sihp1020.elf").read_bytes()).hexdigest()
                        and sum(c["case"]["reset"] for c in reset_cases) == 16
                        and sum(c["case"]["noncanonical_fields"] for c in reset_cases) == 4
                        and {c["case"]["handle"] for c in reset_cases} == {1,2}
                        and {c["case"]["nodes"] for c in reset_cases} == {0,1,4}
                        and all(all(c["interpreter"][f] == c["qemu"][f] for f in
                                ("supplied_service_calls","stop_before","stall_intent","packet_after",
                                 "control_count","queue_empty","nonstack_memory")) for c in reset_cases)
                        and all(c[e]["status"] == "pass" and c[e]["exact_nonstack_ram_equal"]
                                and c[e]["supplied_busy_status_word_unchanged"]
                                and c[e]["original_registry_and_drain_executed"] == c["case"]["reset"]
                                and c[e]["stall_intent"] != c["case"]["reset"]
                                and c[e]["stop_before"] == ("0x100096a9" if c["case"]["reset"] else "0x1000985c")
                                and (c[e]["queue_empty"] and c[e]["control_count"] == 0
                                     and len(c[e]["supplied_service_calls"]) == 2+2*c["case"]["nodes"]
                                     if c["case"]["reset"] else not c[e]["supplied_service_calls"])
                                and class_reset["original_entry"] in c[e]["visited"]
                                and class_reset["resume"] in c[e]["visited"]
                                and c[e]["stop_before"] not in c[e]["visited"]
                                and len(c[e]["rejected_before_execution"]) == 10
                                and not (set(c[e]["visited"]) & set(c[e]["rejected_before_execution"]))
                                for c in reset_cases for e in ("interpreter","qemu"))
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for n,h in class_reset["source_sha256"].items()),
                        "Original request dispatch, registration clearing and list draining stop before transmission; supplied frees and a standalone busy word do not establish actual DMA/reset quiescence.",
                        evidence="analysis/usb-path/class-reset.json"))

    printer_class = read_json("analysis/usb-path/printer-class/validation.json")
    printer_cases, printer_target = printer_class["cases"], printer_class.get("target") or {}
    checks.append(check("bounded_printer_class_document_recovery_verified",
                        printer_class["status"] == printer_target.get("status") == "pass"
                        and len(printer_cases) == len(printer_target.get("cases",[])) == 82
                        and sum(c["case"].startswith("automatic/") for c in printer_cases) == 9
                        and printer_class["completed_native_page_lifecycles"] == printer_class["usb_transfers"]
                            == printer_class["completed_usb_control_transfers"] == 0
                        and printer_target.get("state_and_memory_bytes") == 128256
                        and printer_target.get("elf_sha256") == hashlib.sha256(
                            (ROOT_DIR/"analysis/usb-path/printer-class/target/target-check.elf").read_bytes()).hexdigest()
                        and all(c["status"] == "pass" and c["event_count"] == len(c["steps"])
                                and all(len(s) == 64 and s[34:36] == [0,1] for s in c["steps"])
                                and c["steps"][-1][26] == c["output_bytes"]
                                and c["steps"][-1][42] == c["control_reply_bytes"] for c in printer_cases)
                        and all(t["status"] == "pass" and t["case"] == c["case"] and t["all_steps_equal"]
                                and t["all_pixels_storage_and_control_replies_equal"]
                                and t["state_and_memory_bytes"] == 128256
                                for c,t in zip(printer_cases,printer_target.get("cases",[])))
                        and sum(c["case"].startswith("reset/type=") for c in printer_cases) == 24
                        and sum(c["case"].startswith("repeated-reset/") for c in printer_cases) == 6
                        and sum(c["case"].startswith("superseded-reset/") for c in printer_cases) == 6
                        and sum(c["case"].startswith("accepted-output-reset-fresh-document/")
                                and c["interrupted_source_prefix_bytes"] == 148800 and c["output_bytes"] == 148832
                                and c["steps"][-1][16] == 2 and c["steps"][-1][25] == 1 for c in printer_cases) == 12
                        and any(c["case"] == "generation-exhaustion-retains-accepted-output"
                                and c["output_bytes"] == 148800 and c["steps"][-1][7] == 1
                                and c["steps"][-1][16] == 0xffffffff for c in printer_cases)
                        and any(c["case"] == "request-identity-exhaustion-retains-ep0"
                                and c["steps"][-1][7] == 1 and c["control_reply_bytes"] == 1 for c in printer_cases)
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for n,h in {**printer_class["source_sha256"],**printer_class["fixture_sha256"],
                                            **printer_class["sample_sha256"]}.items()),
                        "Wire parsing, EP0 response lifetime and document reset require independent identities and explicit receive/output/transport promises; passing software composition tests does not prove physical status, USB traffic or printing.",
                        evidence="analysis/usb-path/printer-class/validation.json"))

    port_status = read_json("analysis/usb-path/port-status.json")
    port_cases = port_status["cases"]
    checks.append(check("original_usb_port_status_constant_before_transmission_verified",
                        port_status["status"] == "pass" and len(port_cases) == 28
                        and len(port_status["instruction_anchors"]) == 21
                        and len(port_status["literal_anchors"]) == 5 and len(port_status["original_byte_ranges"]) == 6
                        and port_status["completed_native_page_lifecycles"] == port_status["usb_transfers"]
                            == port_status["completed_usb_control_transfers"] == port_status["peripheral_instructions_executed"] == 0
                        and port_status["stock_elf_sha256"] == hashlib.sha256(
                            (ROOT_DIR/"analysis/sihp1020.elf").read_bytes()).hexdigest()
                        and sum(c["case"]["port_status"] for c in port_cases) == 24
                        and sum(c["case"]["noncanonical_fields"] for c in port_cases) == 18
                        and {c["case"]["status_seed"] for c in port_cases} == {0,0xffffffff,0xe6101100}
                        and all(all(c["interpreter"][f] == c["qemu"][f] for f in
                                ("stop_before","explicit_cuts","stack_pointer","constant_a3","constant_a7",
                                 "stall_intent","control_pointer","control_count","prepared_byte",
                                 "response_frame","packet_after","nonstack_memory","selected_visited"))
                                for c in port_cases)
                        and all(c[e]["status"] == "pass" and c[e]["exact_nonstack_ram_equal"]
                                and c[e]["response_frame_matches_independent_oracle"]
                                and c[e]["constant_a3"] == c[e]["constant_a7"] == 0
                                and [p["resume"] for p in c[e]["explicit_cuts"]]
                                    == ["0x1000912d","0x10009286","0x10009399"]
                                and c[e]["peripheral_instructions_executed"] == 0
                                and not c[e]["supplied_service_calls"]
                                and (c[e]["prepared_byte"] == 0 and c[e]["control_count"] == 1
                                     and c[e]["stop_before"] == "0x100096a9"
                                     if c["case"]["port_status"] else c[e]["stall_intent"]
                                     and c[e]["stop_before"] == "0x1000985c")
                                and len(c[e]["rejected_before_execution"]) == 16
                                and not (set(c[e]["selected_visited"]) & set(c[e]["rejected_before_execution"]))
                                and c[e]["stop_before"] not in c[e]["selected_visited"]
                                for c in port_cases for e in ("interpreter","qemu"))
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for n,h in port_status["source_sha256"].items()),
                        "Original isolated zero definitions and status-response construction must produce the fixed byte before sender entry; unrelated supplied status RAM is not physical calibration or observed USB traffic.",
                        evidence="analysis/usb-path/port-status.json"))

    usb_pause = read_json("analysis/usb-path/pause-resume.json")
    pause_cases = usb_pause["cases"]
    checks.append(check("original_usb_pause_restore_intent_without_quiescence_claim",
                        usb_pause["status"] == "pass" and len(pause_cases) == 46
                        and usb_pause["controller_quiescence_established"] is False
                        and usb_pause["actual_peripheral_accesses"] == usb_pause["completed_native_page_lifecycles"]
                            == usb_pause["completed_usb_control_transfers"] == 0
                        and len(usb_pause["private_literal_redirects"]) == 3
                        and len(usb_pause["original_byte_ranges"]) == 2
                        and len(usb_pause["unredirected_controls"]) == 6
                        and len(usb_pause["excluded_code_controls"]) == 9
                        and usb_pause["direct_call_sites"] == {"0x10009a10": ["0x100121f3"], "0x10009a70": []}
                        and all(not x for x in usb_pause["aligned_function_pointer_literals"].values())
                        and [c["argument"] for c in usb_pause["supplied_services"]] == [200000]
                        and sum(c["kind"] == "pause_then_supplied_resume" for c in pause_cases) == 32
                        and sum(c["kind"] == "conditional_resume_with_supplied_saved_words" for c in pause_cases) == 6
                        and sum(c["kind"] == "second_pause_overwrites_saved_state" for c in pause_cases) == 8
                        and all(a["supplied_before_call"] == b["supplied_before_call"]
                                and all(a["observation"][k] == b["observation"][k] for k in
                                        ("entry", "trace", "nonstack_memory", "expected_memory", "original_instructions_visited"))
                                and all(x["observation"]["status"] == "pass"
                                        and x["observation"]["trace"] == x["observation"]["expected_trace"]
                                        and x["observation"]["nonstack_memory"] == x["observation"]["expected_memory"]
                                        and x["observation"]["descriptor_payload_and_other_nonstack_bytes_preserved"]
                                        for x in (a,b))
                                for c in pause_cases for a,b in zip(c["interpreter"], c["qemu"]))
                        and all(c[e]["status"] == "pass"
                                and c[e]["failure"] == {"reason": "MMIO forbidden", "pc": c["rejected_before_memory_access"]}
                                and c[e]["trace"] == c[e]["expected_trace"]
                                and c[e]["nonstack_memory"] == c[e]["expected_memory"]
                                for c in usb_pause["unredirected_controls"] for e in ("interpreter", "qemu"))
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for n,h in usb_pause["source_sha256"].items()),
                        "Original command intent uses three private RAM redirects and a supplied delay; saved NAK state and TDE changes do not establish DMA cancellation, real register effects or a recovered reset lifecycle.",
                        evidence="analysis/usb-path/pause-resume.json"))

    for patched, report_name, count in ((False, "upstream-baseline", 52), (True, "patched-validation", 160)):
        path = f"analysis/usb-path/tinyusb-device/{report_name}.json"
        protocol = read_json(path)
        target = protocol.get("target") or {}
        rows = protocol["cases"]
        source = protocol["effective_source"]
        target_path = "patched-target" if patched else "target"
        common = (protocol["patched"] is patched and source["patched"] is patched
                  and protocol["upstream_commit"] == source["upstream_commit"]
                      == "dae3f9a366bfcddbf9dcf1b48d7500286a849539"
                  and len(rows) == len(target.get("cases", [])) == count
                  and len(source["effective_sha256"]) == 19 and len(protocol["source_sha256"]) == 68
                  and protocol["usb_transfers"] == protocol["completed_usb_control_transfers"]
                      == protocol["completed_native_page_lifecycles"] == 0
                  and target.get("elf_sha256") == hashlib.sha256(
                      (ROOT_DIR/f"analysis/usb-path/tinyusb-device/{target_path}/target-check.elf").read_bytes()).hexdigest()
                  and source == read_json(f"analysis/usb-path/tinyusb-device/{target_path}/effective-source.json")
                  and all(t["case"] == c["case"] and t["all_nonwire_states_equal"]
                          and t["component_state_and_memory_bytes"] == 128256
                          and all(len(s) == 72 and s[11:13] == [0,1]
                                  and s[61] == c["initial"][61] for s in c["steps"])
                          for c,t in zip(rows, target.get("cases", [])))
                  and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                          for n,h in protocol["source_sha256"].items()))
        if patched:
            specific = (protocol["status"] == "pass" and not protocol["observed_protocol_limitations"]
                        and not protocol["observed_big_endian_mismatches"]
                        and all(c["host_status"] == t["status"] == "pass" and not t["wire_mismatches"]
                                and c["capture_sha256"] == t["capture_sha256"]
                                for c,t in zip(rows, target.get("cases", [])))
                        and sum(c["scenario"].startswith("failed-ep0/") for c in rows) == 100
                        and {int(c["scenario"].rsplit("/",1)[1]) for c in rows
                             if c["scenario"].startswith("failed-ep0/")} == {1,2,3,4,5}
                        and sum(c["scenario"] == "claimed-routing-rejection-is-final" for c in rows) == 4
                        and sum(c["scenario"] == "late-failure-does-not-stop-current-generation" for c in rows) == 4
                        and len(source["patch_manifest"]["files"]) == 2
                        and source["patch_manifest"]["patch_sha256"] == hashlib.sha256(
                            (ROOT_DIR/"open-firmware/tinyusb-device/patches/protocol-compatibility.patch").read_bytes()).hexdigest())
        else:
            specific = (protocol["status"] == "upstream_compatibility_findings"
                        and len(protocol["observed_protocol_limitations"]) == 18
                        and len(protocol["observed_big_endian_mismatches"]) == 40
                        and source["patch_manifest"] is None
                        and {f["kind"] for f in protocol["observed_protocol_limitations"]} == {
                            "unsupported_custom_driver_high_byte_interface", "unsupported_legacy_reset_recipient",
                            "ignored_current_ep0_failure", "configuration_reset_erases_control_request",
                            "repeated_nonzero_configuration_preserves_endpoint_halt"}
                        and source["effective_sha256"] == {
                            name: record["sha256"] for name, record in protocol["upstream_provenance"]["upstream_files"].items()})
        checks.append(check("patched_reusable_usb_protocol_verified" if patched else "unchanged_upstream_usb_limitations_preserved",
                            common and specific,
                            "Independent USB wire oracles, original event tokens, deferred reset gates and failed-request recovery execute in a synthetic DCD; unchanged upstream findings remain separate. No physical USB, bulk traffic, controller quiescence or printing is proved.",
                            evidence=path))

    ingress = read_json("analysis/usb-path/setup-ingress.json")
    ingress_cases = ingress["cases"]
    checks.append(check("original_usb_setup_admission_and_wire_conversion",
                        ingress["status"] == "pass" and len(ingress_cases) == 70
                        and len(ingress["peripheral_rejection_controls"]) == 6
                        and len(ingress["excluded_code_controls"]) == 14
                        and ingress["private_literal_redirect"] == {
                            "address": "0x10005ef4", "guarded_ram": "0x22700100", "original": "0xb3000210"}
                        and ingress["original_entry"] == "0x10008ff0"
                        and ingress["explicit_cut_resume"] == "0x1000935b"
                        and ingress["actual_peripheral_accesses"] == ingress["completed_native_page_lifecycles"]
                            == ingress["completed_usb_control_transfers"] == 0
                        and ingress["supplied_service_calls"] == []
                        and ingress["controller_quiescence_established"] is False
                        and sum(not c["case"]["separate_pointer"] for c in ingress_cases) == 64
                        and all(c[e]["status"] == "pass" and c[e]["failure"] is None
                                and c[e]["exact_nonstack_memory_equal"] and c[e]["original_code_unchanged"]
                                and c[e]["nonstack_memory"] == c[e]["expected_memory"]
                                and c[e]["descriptor_status_passes_oracle"] ==
                                    (c["case"]["owner"] == 2 and c["case"]["rx"] == 0)
                                and c[e]["stop_before"] == ("0x1000941d" if
                                    c["case"]["owner"] == 2 and c["case"]["rx"] == 0 else "0x10009890")
                                for c in ingress_cases for e in ("interpreter", "qemu"))
                        and all(c["interpreter"][k] == c["qemu"][k] for c in ingress_cases for k in
                                ("status_record_after", "other_record_after", "raw_wire_fields", "nonstack_memory",
                                 "register_a1_to_a15", "original_instructions_visited", "explicit_cuts"))
                        and all(c[e]["status"] == "pass" and c[e]["failure"] == {
                                    "type": "ValueError", "reason": "MMIO forbidden", "pc": hex(c["case"]["reject_pc"])}
                                and c[e]["actual_peripheral_accesses"] == 0
                                and c[e]["nonstack_memory"] == c[e]["expected_memory"]
                                for c in ingress["peripheral_rejection_controls"] for e in ("interpreter", "qemu"))
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for n,h in ingress["source_sha256"].items()),
                        "Original guarded SETUP prefix uses an explicit cut and supplied stable RAM records; it does not execute request dispatch, IRQs, descriptor return or USB control transfers. TinyUSB needs original wire bytes.",
                        evidence="analysis/usb-path/setup-ingress.json"))

    composition = read_json("analysis/usb-path/tinyusb-printer/validation.json")
    composed_target = composition.get("target") or {}
    composed_cases = composition["cases"]
    checks.append(check("reusable_usb_printer_decodes_exact_document_pixels",
                        composition["status"] == composed_target.get("status") == "pass"
                        and len(composed_cases) == len(composed_target.get("cases", [])) == 132
                        and sum(c["scenario"].startswith("automatic/") for c in composed_cases) == 18
                        and sum(c["scenario"].startswith("initial-standard/") for c in composed_cases) == 16
                        and len(composition["source_sha256"]) == 76
                        and composition["effective_source"]["patched"] is True
                        and composition["effective_source"] == read_json(
                            "analysis/usb-path/tinyusb-printer/target/effective-source.json")
                        and composition["completed_native_page_lifecycles"] == composition["usb_transfers"] == 0
                        and sum(c["scenario"].startswith("failed-follow-on/") for c in composed_cases) == 16
                        and sum(c["scenario"].startswith("malformed-control-out/") for c in composed_cases) == 24
                        and sum(c["scenario"] == "halt-owned-out/17" for c in composed_cases) == 2
                        and all(c["status"] == t["status"] == "pass" and c["case"] == t["case"]
                                and t["all_steps_equal"] and t["all_pixels_wire_and_storage_equal"]
                                and t["component_state_and_memory_bytes"] == 128588
                                and c["capture_sha256"] == t["capture_sha256"]
                                and c["expected_pixels_sha256"] == c["capture_sha256"]["pixels"]
                                and all(len(s) == 96 and s[15:17] == [0,1] for s in c["steps"])
                                for c,t in zip(composed_cases, composed_target.get("cases", [])))
                        and composed_target.get("elf_sha256") == hashlib.sha256(
                            (ROOT_DIR/"analysis/usb-path/tinyusb-printer/target/target-check.elf").read_bytes()).hexdigest()
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for key in ("source_sha256", "fixture_sha256") for n,h in composition[key].items()),
                        "The reusable software adapter preserves original transfer identities, exact USB reply proposals and independent decoded pixels in both engines. Automatic configuration and real reset keep independent identities; synthetic controller settlement remains supplied. Continuous document boundaries are checked separately; no physical USB or printing is established.",
                        evidence="analysis/usb-path/tinyusb-printer/validation.json"))

    idle = read_json("analysis/usb-path/idle-receive.json")
    idle_cases = idle["cases"]
    checks.append(check("original_usb_idle_receive_enable_requires_separate_quiescence",
                        idle["status"] == "pass" and len(idle_cases) == 58
                        and len(idle["unredirected_controls"]) == 6
                        and len(idle["excluded_code_controls"]) == 15
                        and len(idle["source_sha256"]) == 13
                        and idle["original_entry"] == "0x10008f40"
                        and idle["original_end_exclusive"] == "0x10008fb0"
                        and idle["mid_function_pc_cuts"] == [] and idle["omitted_startup_prefix"] is False
                        and idle["controller_quiescence_established"] is False
                        and idle["completed_usb_control_transfers"] == idle["completed_native_page_lifecycles"]
                            == idle["actual_peripheral_accesses"] == 0
                        and len(idle["private_literal_redirects"]) == len(idle["supplied_services"]) == 3
                        and idle["direct_call_sites"] == ["0x10009937"]
                        and sum(len(c["interpreter"]) for c in idle_cases) == 62
                        and sum(c["kind"] == "supplied_delay_return_replaces_devctl" for c in idle_cases) == 8
                        and all(len(c["interpreter"]) == len(c["qemu"]) for c in idle_cases)
                        and all(p["observation"]["status"] == "pass"
                                and p["observation"]["failure"] is None
                                and p["observation"]["exact_nonstack_mutable_memory_equal"]
                                and p["observation"]["original_code_unchanged"]
                                and p["observation"]["trace"] == p["observation"]["expected_trace"]
                                and p["observation"]["nonstack_memory"] == p["observation"]["expected_memory"]
                                for c in idle_cases for engine in ("interpreter", "qemu") for p in c[engine])
                        and all(a["observation"][key] == b["observation"][key]
                                for c in idle_cases for a,b in zip(c["interpreter"], c["qemu"])
                                for key in ("trace", "nonstack_memory", "original_instructions_visited"))
                        and all(c[e]["failure"] == {"type": "ValueError", "reason": "MMIO forbidden",
                                    "pc": c["rejected_before_memory_access"]}
                                and c[e]["status"] == "pass" and c[e]["actual_peripheral_accesses"] == 0
                                and c[e]["nonstack_memory"] == c[e]["expected_memory"]
                                for c in idle["unredirected_controls"] for e in ("interpreter", "qemu"))
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for n,h in idle["source_sha256"].items()),
                        "Original helper intent can re-enable receiving after a supplied delay-return register change. Three RAM redirects and supplied services do not establish a reachable scheduling race, actual DMA behavior, cancellation settlement or quiescence.",
                        evidence="analysis/usb-path/idle-receive.json"))

    continuous = read_json("analysis/usb-path/continuous-printer/validation.json")
    continuous_target = continuous.get("target") or {}
    continuous_cases = continuous["cases"]
    checks.append(check("continuous_printer_document_boundaries_without_transport_eof",
                        continuous["status"] == continuous_target.get("status") == "pass"
                        and len(continuous_cases) == len(continuous_target.get("cases", [])) == 34
                        and len(continuous["source_sha256"]) == 77
                        and continuous["effective_source"] == composition["effective_source"]
                        and continuous["completed_native_page_lifecycles"] == continuous["usb_transfers"] == 0
                        and {c["scenario"] for c in continuous_cases} >= {
                            "continuous/page-before-document", "continuous/empty-boundaries",
                            "failure/truncated-document", "failure/after-first-document",
                            "failure/document-notification", "failure/page-output/0", "failure/page-output/1",
                            "failure/completion-counter-limit", "continuous/copies-still-metadata"}
                        and all(c["status"] == t["status"] == "pass" and c["case"] == t["case"]
                                and t["all_steps_equal"] and t["all_pixels_wire_notifications_and_storage_equal"]
                                and t["component_state_and_memory_bytes"] == 128588
                                and c["capture_sha256"] == t["capture_sha256"]
                                and c["expected_pixels_sha256"] == c["capture_sha256"]["pixels"]
                                and hashlib.sha256(b"".join(int(v).to_bytes(4,"big") for event in
                                    c["expected_documents"] for v in event)).hexdigest() == c["capture_sha256"]["documents"]
                                and all(len(row) == 96 and row[15:17] == [0,1] for row in c["steps"])
                                and c["steps"][-1][90] == len(c["expected_documents"])
                                and c["steps"][-1][91] == sum(event[4] == 0 for event in c["expected_documents"])
                                for c,t in zip(continuous_cases, continuous_target.get("cases", [])))
                        and continuous_target.get("elf_sha256") == composed_target.get("elf_sha256")
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for key in ("source_sha256", "fixture_sha256") for n,h in continuous[key].items()),
                        "Validated END_PAGE drains and exactly-once END_DOC observations retain their original receive generation. Ordinary documents need no EOF or reset; notification/output failures stop input without erasing prior observations. Supplied settlement and synchronous output remain limits, not physical printing proof.",
                        evidence="analysis/usb-path/continuous-printer/validation.json"))

    udc = read_json("analysis/usb-path/udc-out/validation.json")
    udc_target = udc.get("target") or {}
    udc_cases = udc["cases"]
    reference = udc["original_reference"]
    checks.append(check("original_cookie_bulk_descriptor_to_document_pipeline",
                        udc["status"] == udc_target.get("status") == "pass"
                        and len(udc_cases) == len(udc_target.get("cases", [])) == 34
                        and len(udc["source_sha256"]) == 98 and len(udc["fixture_sha256"]) == 6
                        and "open-firmware/udc-out/hp1020_udc_acquire.h" in udc["source_sha256"]
                        and udc["effective_source"] == composition["effective_source"]
                        and udc["effective_source"] == read_json("analysis/usb-path/udc-out/target/effective-source.json")
                        and udc["actual_peripheral_accesses"] == udc["completed_native_page_lifecycles"]
                            == udc["usb_transfers"] == 0
                        and udc["controller_quiescence_established"] is False
                        and reference["completed_rearm_cases_reused"] == 12
                        and reference["completed_status_cases_reused"] == 51
                        and reference["newly_executed_stock_instructions"] == 0
                        and reference["original_reserves_bytes_4_to_7"] is True
                        and reference["replacement_initializes_reserved_to_zero"] is True
                        and reference["replacement_rx_last_capacity_body_policy_is_stricter"] is True
                        and reference["report"] == "analysis/usb-path/controller-family.json"
                        and reference["report_sha256"] == hashlib.sha256((ROOT_DIR/reference["report"]).read_bytes()).hexdigest()
                        and reference["stock_sha256"] == hashlib.sha256((ROOT_DIR/"analysis/sihp1020.elf").read_bytes()).hexdigest()
                        and {c["scenario"] for c in udc_cases} == {
                            "document/1", "document/64", "status-owner/0", "status-owner/1",
                            "status-owner/2", "status-owner/3", "completion-facts", "publication-facts",
                            "cancel/prepared", "cancel/exposed", "cancel/late-success",
                            "body-and-endpoint-faults", "submission-rejections", "initial-span-probes",
                            "original-cookie-after-reuse"}
                        and sum(c["scenario"].startswith("document/") for c in udc_cases) == 8
                        and sum(c["scenario"].startswith("status-owner/") for c in udc_cases) == 8
                        and all(c["status"] == t["status"] == "pass" and c["case"] == t["case"]
                                and t["all_steps_equal"] and t["all_pixels_wire_notifications_descriptors_and_storage_equal"]
                                and t["adapter_state_and_memory_bytes"] == 128588
                                and t["descriptor_component_bytes"] == 80
                                and c["capture_sha256"] == t["capture_sha256"]
                                and c["expected_pixels_sha256"] == c["capture_sha256"]["pixels"]
                                and hashlib.sha256(b"".join(int(v).to_bytes(4,"big") for event in
                                    c["expected_documents"] for v in event)).hexdigest() == c["capture_sha256"]["documents"]
                                and len(c["steps"]) == len(c["udc_steps"]) == len(c["events"])
                                and all(len(s) == 96 and s[15:17] == [0,1] for s in c["steps"])
                                and all(len(s) == 48 and s[7:10] == [0,1,1] for s in c["udc_steps"])
                                and all(o["cookie"][4] == 1 and 0 <= o["slot"] < 4
                                        and o["descriptor_hex"] == b"".join(v.to_bytes(4,"big") for v in
                                            (0x08000000, 0, 0x24681340 + o["slot"] * 0x1000, 0)).hex()
                                        for o in c["descriptor_oracles"])
                                for c,t in zip(udc_cases, udc_target.get("cases", [])))
                        and udc_target.get("elf_sha256") == hashlib.sha256(
                            (ROOT_DIR/"analysis/usb-path/udc-out/target/target-check.elf").read_bytes()).hexdigest()
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for key in ("source_sha256", "fixture_sha256") for n,h in udc[key].items()),
                        "A single controller-format OUT record retains the original adapter cookie through exact pages and document notifications. Immutable observations, mode, CPU/DMA mapping, visibility and settlement are supplied; raw descriptor bits never acknowledge global quiescence. No physical DCD or printing is established.",
                        evidence="analysis/usb-path/udc-out/validation.json"))

    # One gate for the executed mid-function stock cuts. Do not import their
    # generator: these byte, address, profile and pointer oracles are independent.
    ep0_construction = read_json("analysis/usb-path/ep0-construction.json")
    ep0_stock = (ROOT_DIR/"analysis/sihp1020.elf").read_bytes()
    ep0_stock_sha = "2111560068db47ceca21fa550db4c7c34f5595b5a5d137ae4a19631e40e3601d"
    ep0_sources = {
        "analysis/sihp1020.elf", "scripts/validate-hp1020-usb-ep0-construction.py",
        *("scripts/"+name+".py" for name in (
            "hp1020_qemu_multitask", "hp1020_qemu_ram", "hp1020_qemu_stock_parser",
            "hp1020_stock_parser_harness", "hp1020_stock_stop", "hp1020_xtensa_call0",
            "hp1020_xtensa_properties", "hp1020_xtensa_stock")),
    }
    ep0_ranges = {
        "in-zero": [(0x10008c7e,0x10008d0c)],
        "in-small": [(0x10008d3f,0x10008d48),(0x10008e04,0x10008e9e),(0x10008f08,0x10008f1b)],
        "out-zero": [(0x10009136,0x100091a5)],
        "active-zero-pointer": [(0x10008d02,0x10008d0c)],
        "active-small-pointer": [(0x10008f11,0x10008f1b)],
        "initial-add-pointer": [(0x100092aa,0x100092ba)],
    }
    ep0_mmio = (
        ("zero-mps-read",0x10008c7c,{"8":0xb300000c}),
        ("zero-submit",0x10008d0c,{"8":0x22900100,"9":0xb3000014}),
        ("small-submit",0x10008f1b,{"8":0x22900100,"9":0xb3000014}),
        ("out-mps-write",0x10009129,{"5":64,"8":0xb300020c}),
        ("out-setup-submit",0x100091b0,{"8":0x22900100,"9":0xb3000210}),
        ("out-normal-submit",0x100091c7,{"8":0x22900100,"11":0xb3000214}),
        ("initial-in-submit",0x100092ba,{"8":0x100226f0,"11":0xb3000014}),
    )
    ep0_inputs = []
    for seed in (0x31,0xcc):
        for pointer in (0x11223340,0x91b2c3d0,0x01234567):
            for length in (0,1,18,63,64):
                kind = "in-zero" if length == 0 else "in-small"
                ep0_inputs.append(dict(name=f"{kind}-n{length}-p{pointer:08x}-s{seed:02x}",
                    kind=kind,seed=seed,length=length,pointer=pointer,effect="descriptor"))
            ep0_inputs.append(dict(name=f"out-zero-p{pointer:08x}-s{seed:02x}",
                kind="out-zero",seed=seed,length=0,pointer=pointer,effect="descriptor"))
        for kind in ("active-zero-pointer","active-small-pointer","initial-add-pointer"):
            for pointer in (0x100226f0,0x900226f0):
                ep0_inputs.append(dict(name=f"{kind}-p{pointer:08x}-s{seed:02x}",
                    kind=kind,seed=seed,length=0,pointer=pointer,effect="pointer"))
        ep0_inputs.append(dict(name=f"excluded-multi-descriptor-n65-s{seed:02x}",
            kind="in-small",seed=seed,length=65,pointer=0x11223340,effect="none",stop=0x10008d48))
        for label,pc,registers in ep0_mmio:
            ep0_inputs.append(dict(name=f"mmio-{label}-s{seed:02x}",kind="mmio-instruction",
                seed=seed,length=0,pointer=0x11223340,effect="none",entry=pc,stop=pc,
                registers=registers,reject_mmio=True))
        ep0_inputs.append(dict(name=f"mmio-small-mps-read-s{seed:02x}",kind="in-small",
            seed=seed,length=18,pointer=0x11223340,effect="none",stop=0x10008e0f,
            registers={"6":0xb300000c},reject_mmio=True))
    ep0_excluded = {
        0x10008c24,0x10008c35,0x10008c44,0x10008c69,0x10008c7c,0x10008d0c,
        0x10008d25,0x10008d48,0x10008e9e,0x10008f1b,0x10008f30,0x10009129,
        0x10009132,0x10009134,0x100091a5,0x100091b0,0x100091c7,0x100092ba,
    }
    ep0_literals = {
        0x10005e18:0x10021318,0x10005e34:0x80000000,0x10005e80:0x08000000,
        0x10005ea0:0xb3000014,0x10005eac:0xb3010000,
        0x10005eec:0x1001bc60,0x10005ef0:0x1001bc68,
    }
    # Fixed .text mapping belongs to the pinned ELF hash above, not a mutable
    # report's claimed address-to-file mapping.
    def ep0_original_bytes(address: int, size: int) -> bytes:
        if not (0x10005c80 <= address <= address+size <= 0x1001bb8f):
            return b""
        offset = 0x31e0 + address - 0x10005c80
        return ep0_stock[offset:offset+size]

    ep0_audit = ep0_construction["original_byte_audit"]
    ep0_audit_ranges = {(int(r["begin"],16),int(r["end"],16)) for r in ep0_audit["ranges"]}
    ep0_expected_ranges = {span for ranges in ep0_ranges.values() for span in ranges}
    ep0_expected_ranges.update((pc,pc+2) for _,pc,_ in ep0_mmio)
    ep0_audit_ok = (len(ep0_audit["ranges"]) == len(ep0_expected_ranges)
        and ep0_audit_ranges == ep0_expected_ranges
        and ep0_audit["literals"] == {hex(a):hex(v) for a,v in ep0_literals.items()}
        and all(ep0_original_bytes(a,4) == v.to_bytes(4,"big") for a,v in ep0_literals.items())
        and all(bytes.fromhex(r["bytes"]) == ep0_original_bytes(int(r["begin"],16),int(r["end"],16)-int(r["begin"],16))
                and hashlib.sha256(bytes.fromhex(r["bytes"])).hexdigest() == r["sha256"]
                for r in ep0_audit["ranges"]))
    ep0_allowed = {"l32i","l8ui","s32i","s8i","l32r","movi","mov","add","addi",
                   "slli","mull","extui","memw","bltu","bnei","j"}
    ep0_instruction_pcs = set()
    for begin,end in ep0_expected_ranges:
        pc = begin
        while pc < end:
            instruction = ep0_audit["instructions"][hex(pc)]
            raw = bytes.fromhex(instruction["bytes"])
            ep0_audit_ok &= (len(raw) in (2,3) and pc+len(raw) <= end
                and raw == ep0_original_bytes(pc,len(raw))
                and instruction["op"].removesuffix(".n") in ep0_allowed)
            ep0_instruction_pcs.add(pc)
            if not raw:
                break
            pc += len(raw)
        ep0_audit_ok &= pc == end
    ep0_audit_ok &= set(ep0_audit["instructions"]) == {hex(pc) for pc in ep0_instruction_pcs}
    ep0_audit_ok &= all(bytes.fromhex(anchor[2]) == ep0_original_bytes(int(pc,16),len(bytes.fromhex(anchor[2])))
                        for pc,anchor in ep0_audit["static_extra_anchors"].items())
    ep0_audit_ok &= all(ep0_audit["static_extra_anchors"].get(hex(pc)) == anchor for pc,anchor in {
        0x10008d42:["bltu",[8,9,0x10008d48],"798302"],
        0x10008e9b:["j",[0x10008f08],"600069"],
        0x1000912d:["movi.n",[7,0],"c070"],
        0x10009179:["movi.n",[4,8],"c048"],
        0x100092aa:["l32i.n",[8,11,0],"88b0"],
        0x100092b2:["add.n",[8,8,9],"a988"],
    }.items())
    ep0_spans = ((0x10000370,0x1000049c),(0x1001bb90,0x1001d640),
                 (0x1001d640,0x100351e0),(0x21000000,0x21020000),(0x22900000,0x22901000))
    ep0_templates = {(seed,a,b):bytes((seed+(a>>8)+i*17+(i>>4)*3)&255 for i in range(b-a))
                     for seed in (0x31,0xcc) for a,b in ep0_spans}
    ep0_stores = {
        "in-zero": (0x10008c83,0x10008c89,0x10008c8f,0x10008c92,0x10008c99,0x10008c9c,
                    0x10008c9f,0x10008ca2,0x10008ca7,0x10008caa,0x10008cad,0x10008cb0,
                    0x10008cc8,0x10008cd9,0x10008cea,0x10008cf9),
        "in-small": (0x10008e20,0x10008e26,0x10008e2c,0x10008e2f,0x10008e36,0x10008e39,
                     0x10008e3c,0x10008e3f,0x10008e46,0x10008e49,0x10008e4c,0x10008e4f,
                     0x10008e69,0x10008e78,0x10008e87,0x10008e96),
        "out-zero": (0x10009143,0x10009149,0x1000914f,0x10009152,0x10009157,0x1000915a,
                     0x1000915d,0x10009160,0x10009165,0x10009168,0x1000916b,0x1000916e,
                     0x1000917e,0x1000918a,0x10009196,0x100091a2),
    }

    def ep0_memory_put(memory: dict, address: int, data: bytes) -> None:
        for (begin,end),raw in memory.items():
            if begin <= address and address+len(data) <= end:
                raw[address-begin:address-begin+len(data)] = data
                return
        raise ValueError("EP0 consistency oracle write outside its fixed RAM")

    def ep0_manifest(memory: dict) -> list[dict]:
        return [dict(begin=hex(a),end=hex(b),bytes=b-a,sha256=hashlib.sha256(raw).hexdigest())
                for (a,b),raw in sorted(memory.items())]

    ep0_cases_ok = [c["input"] for c in ep0_construction["cases"]] == ep0_inputs
    for case,given in zip(ep0_construction["cases"],ep0_inputs):
        kind,effect = given["kind"],given["effect"]
        before = {(a,b):bytearray(ep0_templates[given["seed"],a,b]) for a,b in ep0_spans}
        descriptor_pointer = given["pointer"] if effect == "pointer" else 0x22900100
        for address,value in ((0x22900040,descriptor_pointer),(0x22900044,given["pointer"]),
                              (0x22900048,64),(0x2290033c,given["length"]),
                              (0x1001bc60,0x22900100),(0x1001bc68,given["pointer"])):
            ep0_memory_put(before,address,value.to_bytes(4,"big"))
        after = {span:raw.copy() for span,raw in before.items()}
        wanted = b"".join(v.to_bytes(4,"big") for v in (0x08000000+given["length"],0,given["pointer"],0))
        expected_writes = []
        if effect == "descriptor":
            ep0_memory_put(after,0x22900100,wanted)
            for pc,offset in zip(ep0_stores[kind],(8,9,10,11,4,5,6,7,12,13,14,15,0,1,2,3)):
                expected_writes.append(dict(pc=hex(pc),kind="write",address=hex(0x22900100+offset),size=1,value=hex(wanted[offset])))
            if kind != "out-zero":
                ep0_memory_put(after,0x2290033c,bytes(4))
                expected_writes.append(dict(pc=hex(0x10008cfc if kind == "in-zero" else 0x10008e99),
                    kind="write",address="0x2290033c",size=4,value="0x0"))
        ranges = ep0_ranges[kind] if kind != "mmio-instruction" else [(given["entry"],given["entry"]+2)]
        entry,stop = ranges[0][0],given.get("stop",ranges[-1][1])
        before_manifest,after_manifest = ep0_manifest(before),ep0_manifest(after)
        descriptor_hex = bytes(after[0x22900000,0x22901000][0x100:0x110]).hex()
        ep0_cases_ok &= case["status"] == "pass"
        for engine in ("interpreter","qemu"):
            record = case[engine]
            retired = [int(pc,16) for pc in record["original_instructions_retired"]]
            reason = "MMIO forbidden" if given.get("reject_mmio") else (
                "execution outside selected stock routines: " if engine == "interpreter" else
                "native tasks left selected code: ")+hex(stop)
            ep0_cases_ok &= (record["status"] == "pass" and record["engine"] == engine
                and record["entry"] == hex(entry) and record["stop_before"] == hex(stop)
                and record["failure"] == dict(type="ValueError",reason=reason,pc=hex(stop))
                and record["actual_peripheral_accesses"] == 0
                and all(record[key] is True for key in ("all_mutable_and_guard_ram_equal","ordered_write_trace_equal","original_code_unchanged"))
                and record["literal_descriptor_checked"] is (effect == "descriptor")
                and record["pointer_oracle_checked"] is (effect == "pointer")
                and record["before_memory"] == before_manifest
                and record["expected_memory"] == record["actual_memory"] == after_manifest
                and record["descriptor_hex"] == descriptor_hex
                and record["expected_descriptor_hex"] == (wanted.hex() if effect == "descriptor" else None)
                and record["expected_writes"] == [a for a in record["accesses"] if a["kind"] == "write"] == expected_writes
                and len(record["registers"]) == 16 and record["registers"][:2] == ["0xfffffffc","0x2101fef0"]
                and record["pointer_register_a8"] == record["registers"][8]
                and retired == sorted(set(retired)) and stop not in retired
                and not ep0_excluded.intersection(retired)
                and all(any(a <= pc < b for a,b in ranges) and pc in ep0_instruction_pcs for pc in retired)
                and 0 <= record["engine_steps"] <= 256
                and record["engine_steps"] == len(retired)+int(engine == "interpreter" and given.get("reject_mmio",False)))
            if effect in ("descriptor","pointer"):
                pointer = 0x22900100 if effect == "descriptor" else given["pointer"]
                if kind == "initial-add-pointer":
                    pointer = (pointer+0x80000000)&0xffffffff
                ep0_cases_ok &= record["pointer_register_a8"] == hex(pointer)
            # Check reads against the initial RAM plus earlier observed writes;
            # no encoded payload pointer, peripheral address or arbitrary RAM is read.
            memory = {span:raw.copy() for span,raw in before.items()}
            for event in record["accesses"]:
                address,size,value = int(event["address"],16),event["size"],int(event["value"],16)
                ep0_cases_ok &= int(event["pc"],16) in retired
                if event["kind"] == "write":
                    ep0_memory_put(memory,address,value.to_bytes(size,"big"))
                else:
                    if address in ep0_literals and size == 4:
                        expected_value = ep0_literals[address]
                    elif ((size == 4 and address in (0x22900040,0x22900044,0x22900048,0x2290033c,0x1001bc60,0x1001bc68))
                          or (size == 1 and 0x22900100 <= address < 0x22900110)):
                        raw = next(raw[address-a:address-a+size] for (a,b),raw in memory.items() if a <= address and address+size <= b)
                        expected_value = int.from_bytes(raw,"big")
                    else:
                        expected_value = None
                    ep0_cases_ok &= event["kind"] == "read" and value == expected_value
        ep0_cases_ok &= all(case["interpreter"][key] == case["qemu"][key] for key in (
            "registers","accesses","original_instructions_retired","before_memory","actual_memory","expected_writes"))
    checks.append(check("original_ep0_construction_cuts_preserve_bytes_and_hardware_exclusions",
                        ep0_construction["status"] == "pass" and ep0_cases_ok and ep0_audit_ok
                        and ep0_construction["counts"] == dict(construction=36,pointer_only=12,mmio_rejections=16,excluded_multi_descriptor=2)
                        and ep0_construction["stock_elf_sha256"] == hashlib.sha256(ep0_stock).hexdigest() == ep0_stock_sha
                        and ep0_construction["actual_peripheral_accesses"] == ep0_construction["completed_usb_control_transfers"]
                            == ep0_construction["completed_native_page_lifecycles"] == 0
                        and ep0_construction["controller_quiescence_established"] is False
                        and ep0_construction["omitted_startup_prefix"] is True
                        and ep0_construction["original_entry_executed"] is False
                        and ep0_construction["private_literal_redirects"] == ep0_construction["supplied_services"] == []
                        and len(ep0_construction["excluded_code_controls"]) == len(ep0_excluded)
                        and {int(r["pc"],16) for r in ep0_construction["excluded_code_controls"]} == ep0_excluded
                        and all(r["status"] == "rejected before instruction execution in both engines" for r in ep0_construction["excluded_code_controls"])
                        and set(ep0_construction["source_sha256"]) == set(ep0_construction["source_origins"]) == ep0_sources
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h for n,h in ep0_construction["source_sha256"].items()),
                        "Original IN0/OUT0 construction cuts must retain literal BE descriptors, exact ordered writes and complete RAM guards. Active pointers pass through unchanged; initialization uses a separate wrapped ADD. Supplied registers/MPS and pre-MMIO cuts establish no control transfer, mapping, cache visibility or settlement.",
                        evidence="analysis/usb-path/ep0-construction.json"))

    def usb_packet_capture_equal(case: dict, target: dict, documents: bool = False) -> bool:
        wire = bytearray()
        for oracle in case["packet_oracles"]:
            data = bytes.fromhex(oracle["expected_hex"])
            row = case["steps"][oracle["step"]]
            if oracle["offset"] != len(wire) or not row[28] or row[29] != len(data):
                return False
            wire.extend(data)
        captures = case["capture_sha256"]
        ok = (case["status"] == target["status"] == "pass" and case["case"] == target["case"]
            and target["all_steps_equal"] is True and captures == target["capture_sha256"]
            and set(captures) == ({"pixels","wire","receive","output","documents","ep0"} if documents else {"pixels","wire","receive","output"})
            and hashlib.sha256(wire).hexdigest() == captures["wire"] and len(wire) == case["steps"][-1][24]
            and case["expected_pixels_sha256"] == captures["pixels"] and case["pixels_bytes"] == case["steps"][-1][50]
            and len(case["steps"]) == len(case["events"])
            and all(len(row) == 96 and row[15:17] == [0,1] and row[0] == event["result"]
                    for row,event in zip(case["steps"],case["events"])))
        if documents:
            expected = b"".join(v.to_bytes(4,"big") for record in case["expected_documents"] for v in record)
            ok &= (hashlib.sha256(expected).hexdigest() == captures["documents"]
                and case["steps"][-1][90:92] == [len(case["expected_documents"]),sum(d[4] == 0 for d in case["expected_documents"])])
        return ok

    packet_fault = read_json("analysis/usb-path/tinyusb-printer/packet-fault-validation.json")
    packet_fault_target = packet_fault.get("target") or {}
    packet_fault_names = {"packet-fault/"+name for name in ("current-in-data","current-out-status","pending-recovery",
        "direct-address","identity-and-busy","settled-and-reused","superseded-setup","older-generation","bulk","transport-limit")}
    packet_fault_retains = True
    for case in packet_fault["cases"]:
        for before,row,event in zip([case["initial"]]+case["steps"],case["steps"],case["events"]):
            if event["words"][0] != 19:
                continue
            packet_fault_retains &= (row[13] == before[13] and row[17:20] == before[17:20]
                and row[24:36] == before[24:36] and row[50:62] == before[50:62])
            if row[0] in (1,2) or event["words"][2] == 0:
                packet_fault_retains &= row[1:] == before[1:]
            elif row[0] == 0 and before[7] == 0:
                packet_fault_retains &= row[4] == before[4]+1 and row[7] == row[9] == row[36] == 1 and row[14] == before[13]
    checks.append(check("retained_packet_faults_preserve_original_ownership_and_reject_stale_identities",
                        packet_fault["status"] == packet_fault_target.get("status") == "pass" and packet_fault_retains
                        and len(packet_fault["cases"]) == len(packet_fault_target.get("cases",[])) == 20
                        and {(c["scenario"],c["fill"],c["capacity"],c["interface"]) for c in packet_fault["cases"]}
                            == {(name,fill,64,3) for name in packet_fault_names for fill in (0,204)}
                        and packet_fault["usb_transfers"] == packet_fault["completed_native_page_lifecycles"] == 0
                        and len(packet_fault["source_sha256"]) == 77
                        and set(packet_fault["source_sha256"]) == set(composition["source_sha256"]) | {"scripts/validate-hp1020-tinyusb-packet-fault.py"}
                        and packet_fault["fixture_sha256"] == composition["fixture_sha256"] and len(packet_fault["fixture_sha256"]) == 6
                        and packet_fault["effective_source"] == composition["effective_source"] == read_json("analysis/usb-path/tinyusb-printer/target/effective-source.json")
                        and all(usb_packet_capture_equal(c,t) and t["all_pixels_wire_and_storage_equal"] is True
                                and t["measured_target_state_and_memory_bytes"] == 128588
                                for c,t in zip(packet_fault["cases"],packet_fault_target.get("cases",[])))
                        and packet_fault_target.get("elf_sha256") == packet_fault_target["captured_artifact_sha256"]["target-check.elf"]
                            == hashlib.sha256((ROOT_DIR/"analysis/usb-path/tinyusb-printer/target/target-check.elf").read_bytes()).hexdigest()
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for key in ("source_sha256","fixture_sha256") for n,h in packet_fault[key].items()),
                        "Exact current packet faults fence input while retaining borrowed packets, bytes and completion counts; stale identities remain inert. These focused recovery documents use explicit stream close, separately from continuous-document evidence. Faults do not establish controller settlement or reset promises.",
                        evidence="analysis/usb-path/tinyusb-printer/packet-fault-validation.json"))

    ep0 = read_json("analysis/usb-path/udc-ep0/validation.json")
    ep0_target,ep0_reference = ep0.get("target") or {},ep0["original_reference"]
    ep0_profiles = {("protocol",fill,64,interface) for fill in (0,204) for interface in (0,3)}
    ep0_names = {"direct-address","older-generation-fault","data-zlp","initial-spans","prepare-rejection","old-cookie","superseded-fault"}
    ep0_names |= {f"status/{role}/{owner}" for role in ("in","out") for owner in range(4)}
    ep0_names |= {f"{kind}/{role}" for kind in ("facts","publication","cancel","fault") for role in ("in","out")}
    ep0_profiles |= {(name,fill,64,3) for name in ep0_names for fill in (0,204)}
    ep0_expected_sources = set(composition["source_sha256"]) | set(ep0_construction["source_sha256"]) | {
        "analysis/usb-path/ep0-construction.json", "scripts/validate-hp1020-continuous-printer.py",
        "scripts/validate-hp1020-udc-ep0.py", "scripts/build-hp1020-udc-ep0-target.sh",
        *("open-firmware/udc-ep0-test/"+name for name in ("fixture.c","host-check.c","target-check.ld")),
        *("open-firmware/udc-ep0/"+name for name in ("hp1020_udc_ep0.c","hp1020_udc_ep0.h")),
    }
    ep0_descriptors_ok = True
    for case in ep0["cases"]:
        prepared,published = {},set()
        for oracle in case["descriptor_oracles"]:
            slot,n,cookie = oracle["slot"],oracle["requested"],oracle["cookie"]
            row = case["steps"][oracle["step"]]
            p = case["ep0_steps"][oracle["step"]][8+48*slot:56+48*slot]
            desc_dma,packet_dma = ((0x13579bd0,0x3579bdf0),(0xa468ace0,0xb68ace00))[slot]
            wanted = b"".join(v.to_bytes(4,"big") for v in (0x08000000|n,0,packet_dma,0))
            ep0_descriptors_ok &= (slot in (0,1) and 0 <= n <= 64 and (slot == 1 or n == 0)
                and len(cookie) == 5 and all(v > 0 for v in cookie[:3]) and cookie[3:] == [0,slot*0x80]
                and oracle["descriptor"] == wanted.hex() and p[11:14] == [desc_dma,packet_dma,64])
            if oracle["kind"] == "prepare":
                ep0_descriptors_ok &= (cookie[0] not in prepared and cookie == [row[21],row[3],row[32],0,slot*0x80]
                    and row[22:24] == [slot*0x80,n] and p[0] in (1,2) and p[5:11] == [n]+cookie
                    and b"".join(v.to_bytes(4,"big") for v in p[14:18]) == wanted and p[46] == int(n == 0))
                prepared[cookie[0]] = (cookie,n,slot)
            else:
                ep0_descriptors_ok &= (oracle["kind"] == "publish" and cookie[0] not in published
                    and prepared.get(cookie[0]) == (cookie,n,slot) and p[22:31] == cookie+[desc_dma,packet_dma,n,64]
                    and b"".join(v.to_bytes(4,"big") for v in p[18:22]) == wanted and p[47] == int(n == 0))
                published.add(cookie[0])
        for slot in (0,1):
            p = case["ep0_steps"][-1][8+48*slot:56+48*slot]
            ep0_descriptors_ok &= p[31:33] == [sum(v[2] == slot for v in prepared.values()),sum(prepared[i][2] == slot for i in published)]
    checks.append(check("original_cookie_ep0_descriptors_preserve_publication_fault_and_recovery_boundaries",
                        ep0["status"] == ep0_target.get("status") == "pass" and ep0_descriptors_ok
                        and len(ep0["cases"]) == len(ep0_target.get("cases",[])) == 50
                        and {(c["scenario"],c["fill"],c["capacity"],c["interface"]) for c in ep0["cases"]} == ep0_profiles
                        and ep0["actual_peripheral_accesses"] == ep0["usb_transfers"] == ep0["completed_native_page_lifecycles"] == 0
                        and ep0["controller_quiescence_established"] is False
                        and [ep0_reference[k] for k in ("completed_construction_cases_reused","completed_pointer_cases_reused","pre_mmio_controls_reused","out_of_profile_controls_reused","excluded_pc_controls_reused")] == [36,12,16,2,18]
                        and ep0_reference["newly_executed_stock_instructions"] == 0 and ep0_reference["original_entry_executed"] is False
                        and ep0_reference["active_pointer_preserved"] is True and ep0_reference["initial_pointer_add_modulo32"] is True
                        and ep0_reference["completion_count_visibility_and_settlement_supplied"] is True and ep0_reference["physical_address_translation_established"] is False
                        and ep0_reference["report"] == "analysis/usb-path/ep0-construction.json"
                        and ep0_reference["report_sha256"] == hashlib.sha256((ROOT_DIR/ep0_reference["report"]).read_bytes()).hexdigest()
                        and ep0_reference["stock_sha256"] == ep0_stock_sha
                        and ep0_reference["original_descriptor_vectors"] == [dict(kind=c["input"]["kind"],length=c["input"]["length"],pointer=c["input"]["pointer"],bytes=c["interpreter"]["descriptor_hex"]) for c in ep0_construction["cases"] if c["input"]["effect"] == "descriptor"]
                        and len(ep0["source_sha256"]) == 92 and set(ep0["source_sha256"]) == ep0_expected_sources
                        and ep0["fixture_sha256"] == packet_fault["fixture_sha256"] and len(ep0["fixture_sha256"]) == 6
                        and ep0["effective_source"] == packet_fault["effective_source"] == read_json("analysis/usb-path/udc-ep0/target/effective-source.json")
                        and all(usb_packet_capture_equal(c,t,True) and t["all_pixels_wire_notifications_descriptors_and_storage_equal"] is True
                                and t["adapter_state_and_memory_bytes"] == 128588 and t["descriptor_component_bytes"] == 296
                                and len(c["ep0_steps"]) == len(c["steps"])
                                and all(len(row) == 104 and row[2:5] == [0,1,1] for row in c["ep0_steps"])
                                for c,t in zip(ep0["cases"],ep0_target.get("cases",[])))
                        and ep0_target.get("elf_sha256") == ep0_target["captured_artifact_sha256"]["target-check.elf"]
                            == hashlib.sha256((ROOT_DIR/"analysis/usb-path/udc-ep0/target/target-check.elf").read_bytes()).hexdigest()
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                                for key in ("source_sha256","fixture_sha256") for n,h in ep0[key].items()),
                        "Two EP0 records preserve exact cookies, supplied DMA addresses, literal descriptor bytes and real NULL/zero original buffers. Prepared and published storage remains distinct; wire, pixels and document observations agree across both engines. Actual IN count, visibility, mapping and settlement remain supplied, with normalized bulk input and no physical DCD or printing.",
                        evidence="analysis/usb-path/udc-ep0/validation.json"))

    EXPECTED_UDC_COMPOSED_SOURCE_COUNT = 118
    EXPECTED_UDC_SETUP_COMPONENT_BYTES = 96
    uc = read_json("analysis/usb-path/udc-composed/validation.json")
    uc_target, uc_ref = uc.get("target") or {}, uc["original_reference"]
    uc_names = {"snapshot-replay", "capture-wait-newer-retry", "capture-facts", "raw-admission",
        "held-capture-blocks-reset-ack", "held-capture-blocks-publication", "superseded-control",
        "soft-reset-held", "bus-reset-retained-capture", "reset-admission-wait",
        "terminal-drains-admitted-reset", "sequence-limit/capture", "sequence-limit/reset",
        "descriptor-fault/in", "descriptor-fault/bulk"}
    uc_profiles = {("protocol", f, 64, i) for f in (0, 204) for i in (0, 3)} | {
        (n, f, 64, 3) for n in uc_names for f in (0, 204)}
    uc_profiles |= raw_si_composed_profiles()
    uc_sources = set(ep0["source_sha256"]) | set(udc["source_sha256"]) | set(ingress["source_sha256"]) | {
        "analysis/usb-path/setup-ingress.json", "scripts/validate-hp1020-udc-composed.py",
        "scripts/build-hp1020-udc-composed-target.sh",
        *("open-firmware/udc-composed-test/"+n for n in ("fixture.c", "host-check.c", "target-check.ld")),
        *("open-firmware/udc-setup/"+n for n in ("hp1020_udc_setup.c", "hp1020_udc_setup.h")),
    }
    uc_bad: set[str] = set()
    # Independent intended fixture pixels: 32x8 black and 64x12 edge pattern.
    uc_small, uc_slim = bytes([255])*32, bytearray(96)
    for y in range(12):
        for x in range(64):
            if ((x//11) ^ (y//3) ^ (x == y) ^ (x == 63-y)) & 1:
                uc_slim[y*8+x//8] |= 0x80 >> (x & 7)

    def uc_need(ok: bool, reason: str) -> None:
        if not ok:
            uc_bad.add(reason)

    uc_raw_si_ok, uc_raw_si_detail = raw_si_composed_consistency(uc)
    uc_need(uc_raw_si_ok, "raw-SI rejection contracts: " + uc_raw_si_detail)

    def uc_bytes(words: list[int]) -> bytes:
        return b"".join(v.to_bytes(4, "big") for v in words)

    def uc_forward(row: list[int]) -> list[int]:
        return row[17:18]+row[24:26]+row[50:59]+row[90:96]

    for c, t in zip(uc["cases"], uc_target.get("cases", [])):
        rows, erows, brows, srows, events = (c[k] for k in
            ("steps", "ep0_steps", "bulk_steps", "setup_steps", "events"))
        lengths = [len(v) for v in (rows, erows, brows, srows, events)]
        uc_need(lengths[0] > 0 and len(set(lengths)) == 1, "complete 288-word event transcript")
        if not lengths[0] or len(set(lengths)) != 1:
            continue
        initial, ie, ib, ist = (c[k] for k in ("initial","initial_ep0","initial_bulk","initial_setup"))
        uc_need(len(initial) == 96 and initial[:2] == [0,0] and initial[15:17] == [0,1]
                and len(ie) == 104 and ie[1:5] == [1,0,1,1]
                and len(ib) == 48 and ib[1:3] == [1,0] and ib[7:10] == [0,1,1] and ib[44] == 0
                and len(ist) == 40 and ist[:15] == [0,1,0,0,0,0,0,0,0,0,0,7,0,1,3],
                "first-use state before any ingress")
        uc_need(all(len(r) == 96 and r[15:17] == [0,1] and r[0] == ev["result"]
                    for r,ev in zip(rows,events))
                and all(len(e) == 104 and e[2:5] == [0,1,1] for e in erows)
                and all(len(b) == 48 and b[7:10] == [0,1,1] for b in brows)
                and all(len(s) == 40 and s[12:15] == [0,1,3] for s in srows),
                "row shape, result, ownership and guards")
        # Existing packet/document helper remains unchanged for its old users;
        # check the two extra captures separately before using its six-key form.
        captures = c["capture_sha256"]
        uc_need(set(captures) == {"pixels","wire","receive","output","documents","ep0",
                                 "bulk_descriptor","setup_record"}
                and captures == t["capture_sha256"], "all host/target capture hashes")
        small_c = dict(c, capture_sha256={k:v for k,v in captures.items()
                                          if k not in ("bulk_descriptor","setup_record")})
        small_t = dict(t, capture_sha256={k:v for k,v in t["capture_sha256"].items()
                                          if k not in ("bulk_descriptor","setup_record")})
        uc_need(usb_packet_capture_equal(small_c,small_t,True)
                and t["all_pixels_wire_notifications_descriptors_and_storage_equal"] is True
                and t["adapter_state_and_memory_bytes"] == 128588
                and t["component_and_allocation_bytes"] == {
                    "ep0":296, "bulk":80, "setup":EXPECTED_UDC_SETUP_COMPONENT_BYTES},
                "exact wire, pixels, notifications and measured target sizes")
        empty_profile = c["scenario"] in {"reset-admission-wait","sequence-limit/capture",
                                           "sequence-limit/reset","terminal-drains-admitted-reset"}
        pixels = uc_small+bytes(uc_slim)+uc_small if c["scenario"] == "protocol" else b"" if empty_profile else uc_small
        documents = ([[2,1,0,1,0],[2,2,1,0,0],[2,3,1,1,0],[3,1,0,1,0]] if c["scenario"] == "protocol"
                     else [] if empty_profile else [[rows[-1][32],1,0,1,0]])
        uc_need(c["expected_pixels_sha256"] == hashlib.sha256(pixels).hexdigest()
                and c["pixels_bytes"] == len(pixels) and c["expected_documents"] == documents,
                "independent intended page bytes and exactly-once document boundaries")
        guard = bytes([c["fill"]])*16
        uc_need(hashlib.sha256(guard+uc_bytes(brows[-1][24:28])+guard).hexdigest() == captures["bulk_descriptor"]
                and hashlib.sha256(guard+uc_bytes(srows[-1][28:32])+guard).hexdigest() == captures["setup_record"],
                "complete separately guarded live descriptor/SETUP captures")

        # Literal descriptor bytes, immutable cookies, exactly-once publication.
        prepared, published = {}, set()
        for o in c["descriptor_oracles"]:
            i, slot, n, cookie = o["step"], o["slot"], o["requested"], o["cookie"]
            if not (0 <= i < len(rows) and slot in (0,1) and len(cookie) == 5):
                uc_need(False, "EP0 oracle index/identity"); continue
            r, p = rows[i], erows[i][8+48*slot:56+48*slot]
            dd, dma = ((0x13579bd0,0x3579bdf0),(0xa468ace0,0xb68ace00))[slot]
            wanted = uc_bytes([0x08000000|n,0,dma,0])
            uc_need(0 <= n <= 64 and (slot == 1 or n == 0)
                    and all(v > 0 for v in cookie[:3]) and cookie[3:] == [0,slot*0x80]
                    and o["descriptor"] == wanted.hex() and p[11:14] == [dd,dma,64],
                    "independent EP0 BE descriptor and DMA allocation")
            if o["kind"] == "prepare":
                uc_need(cookie[0] not in prepared and cookie == [r[21],r[3],r[32],0,slot*0x80]
                        and r[22:24] == [slot*0x80,n] and p[5:11] == [n]+cookie
                        and p[0] in (1,2) and uc_bytes(p[14:18]) == wanted and p[46] == int(n == 0),
                        "EP0 original bind and true NULL/zero buffer")
                prepared[cookie[0]] = (cookie,n,slot)
            else:
                uc_need(o["kind"] == "publish" and cookie[0] not in published
                        and prepared.get(cookie[0]) == (cookie,n,slot)
                        and p[22:31] == cookie+[dd,dma,n,64] and uc_bytes(p[18:22]) == wanted
                        and p[47] == int(n == 0), "EP0 publication is original and one-shot")
                published.add(cookie[0])
        wire_ids = [rows[o["step"]][28] for o in c["packet_oracles"]]
        uc_need(len(wire_ids) == len(set(wire_ids))
                and set(wire_ids) == {i for i in published if prepared[i][2] == 1},
                "every actual IN publication including ZLP has one wire oracle")
        for slot in (0,1):
            p = erows[-1][8+48*slot:56+48*slot]
            uc_need(p[31:33] == [sum(v[2] == slot for v in prepared.values()),
                                 sum(prepared[i][2] == slot for i in published)],
                    "complete EP0 preparation/publication ledger")
        bulk_prepared, bulk_published = {}, set()
        for o in c["bulk_descriptor_oracles"]:
            i, cookie, slot = o["step"], o["cookie"], o["slot"]
            if not (0 <= i < len(rows) and len(cookie) == 5 and 0 <= slot < 4):
                uc_need(False, "OUT oracle index/identity"); continue
            r, b = rows[i], brows[i]
            dma = 0x24681340+0x1000*slot
            wanted = uc_bytes([0x08000000,0,dma,0])
            uc_need(all(v > 0 for v in cookie[:4]) and cookie[4] == 1
                    and slot == (cookie[3]-1)%4 and o["dma"] == dma
                    and o["descriptor_hex"] == wanted.hex(), "independent OUT BE descriptor and original receive slot")
            if o["kind"] == "prepare":
                uc_need(cookie[0] not in bulk_prepared and cookie == [r[21],r[5],r[32],r[33],1]
                        and b[2] in (1,2) and b[16:24] == cookie+[0x579bdf10,dma,64]
                        and b[47] == slot and uc_bytes(b[24:28]) == wanted, "OUT exact original submission")
                bulk_prepared[cookie[0]] = (cookie,slot,dma)
            else:
                uc_need(o["kind"] == "publish" and cookie[0] not in bulk_published
                        and bulk_prepared.get(cookie[0]) == (cookie,slot,dma)
                        and b[28:33] == cookie and b[37:40] == [0x579bdf10,dma,64]
                        and uc_bytes(b[33:37]) == wanted, "OUT publication is original and one-shot")
                bulk_published.add(cookie[0])
        uc_need(brows[-1][10:12] == [len(bulk_prepared),len(bulk_published)], "complete OUT publication ledger")

        live = bytes([c["fill"]])*16
        capture, capture_meta = bytes(16), [0,0,0,0]
        accepted, admitted, pending_external = {}, set(), {}
        blocked, blocked_indices, pending_at_terminal = set(), [], []
        admission_controls, reset_retries = set(), 0
        prev, pe, pb, ps = (c[k] for k in ("initial","initial_ep0","initial_bulk","initial_setup"))
        for i, (r,e,b,s,ev) in enumerate(zip(rows,erows,brows,srows,events)):
            op,a,arg_b,arg_c,arg_d = ev["words"]
            raw = bytes.fromhex(ev["data_hex"])
            uc_need(op not in (0,2,3,4,5,13,19), "no normalized setup/reset/completion/fault bypass")
            states = [(b[44] >> (8*j)) & 255 for j in range(3)]
            uc_need(all(v in (0,1,2) for v in states) and b[44] >> 24 == 0
                    and [v == 1 for v in states] == [bool(r[j]) for j in (26,28,30)]
                    and [v != 0 for v in (e[8],e[56],b[2])] == [v == 1 for v in states],
                    "component controller ownership versus adapter pending notifications")
            needed = 1 if op == 1 else 2 if op == 6 else 4 if op == 7 else 7 if op in (8,9,12,41,61) else 0
            if needed and ps[11] & needed != needed:
                uc_need(r[0] == 1 and r[2:96] == prev[2:96]
                        and [e[40],e[88],b[11]] == [pe[40],pe[88],pb[11]]
                        and s[27] == ps[27]+1, "held ingress blocks all forward work, old ACK and publication")
                blocked.add(op); blocked_indices.append(i)
            if op == 80:
                uc_need(len(raw) == 16, "complete raw SETUP source write")
                live = raw
            elif op == 81:
                observation = (live,[a,arg_b,arg_c,arg_d])
                copied = s[17] == ps[17]+1
                uc_need(r[2:96] == prev[2:96], "SETUP offer cannot invoke adapter/protocol")
                if copied:
                    uc_need(ps[2] == 0 and not ps[10] and a > ps[4] and arg_b == 0x79bdf130
                            and r[0] == (6 if a == 0xffffffff else 0)
                            and s[2:5] == [1,a,a], "strict original SETUP sequence and one capture")
                    if a in pending_external:
                        uc_need(pending_external[a] == observation, "WAIT retry retains original external bytes/status/sequence")
                    capture,capture_meta = observation
                    accepted[a] = observation
                else:
                    uc_need(r[0] != 0 and s[17] == ps[17], "rejected SETUP never replaces held capture")
                    if r[0] == 1:
                        pending_external.setdefault(a,observation)
            elif op == 82:
                status = int.from_bytes(capture[:4],"big")
                if ps[2:4] == [1,a] and not ps[10]:
                    facts = [arg_b >> 16, (arg_b >> 8) & 255, arg_b & 255, arg_c]
                    reset_wait = bool(ps[8] and ps[7] == ps[8] and prev[3] != ps[8])
                    expected = (3 if any(v > 1 for v in facts) else 1 if not all(facts)
                                else 4 if capture_meta[2] else 1 if status >> 30 != 2
                                else 4 if status & 0x30000000 else 1 if reset_wait else 0)
                    uc_need(r[0] == expected, "independent owner/RX/fault/visibility/stall-clear result")
                    admission_controls.add((status >> 30,(status >> 28) & 3,capture_meta[2],arg_b,arg_c,r[0]))
                if r[0] == 0:
                    uc_need(ps[2:4] == [1,a] and capture_meta[0] == a and a in accepted and a not in admitted
                            and arg_b == 0x010101 and arg_c == 1 and not capture_meta[2]
                            and status >> 30 == 2 and status & 0x30000000 == 0 and not ps[10]
                            and s[2:4] == [0,0] and s[6] == a and s[19] == ps[19]+1
                            and r[2] == prev[2]+1 and r[3] == prev[3] and uc_forward(r) == uc_forward(prev),
                            "raw owner/RX/facts admission copies only the retained original request")
                    admitted.add(a)
                else:
                    uc_need(r[2:11]+r[12:96] == prev[2:11]+prev[12:96]
                            and s[2:9] == ps[2:9] and s[19] == ps[19],
                            "stale or unproved dispatch retains request and invalidates no newer work")
            elif op == 83:
                if r[0] == 0:
                    uc_need(a > ps[4] and arg_b == 0 and s[2:6] == [0,0,a,a]
                            and s[7:9] == [r[2],r[2]] and r[2] == prev[2]+1
                            and uc_forward(r) == uc_forward(prev), "actual reset advances one original ordered barrier")
                    if ps[2] == 2:
                        uc_need(a == ps[3], "only original deferred reset identity can retry")
                        reset_retries += 1
                elif r[0] == 1:
                    uc_need(r[2] == prev[2] and s[2:4] == [2,ps[3] if ps[2] == 2 else a],
                            "reset WAIT retains exact pending reset")
                elif r[0] == 6 and not ps[10]:
                    uc_need(a == 0xffffffff and s[2:4] == [2,a] and s[10] == 1 and r[2:96] == prev[2:96],
                            "terminal reset cannot wrap or fabricate adapter admission")
            uc_need(uc_bytes(s[28:32]) == live and uc_bytes(s[32:36]) == capture
                    and s[22:26] == capture_meta, "live-record reuse never mutates immutable captured bytes or identity")
            if s[10] and b[44] == 0x020200:
                pending_at_terminal.append(i)
                uc_need(e[56] == b[2] == 0 and not any(r[j] for j in (26,28,30)),
                        "terminal settled controller records retain adapter PENDING")
            prev,pe,pb,ps = r,e,b,s

        # Counterpart report oracles must cover every successful offered/admitted
        # event. Local MAX is deliberately a retained terminal event, not an OK.
        capture_oracles = {o["sequence"]:o for o in c["setup_oracles"] if o["kind"] == "capture"}
        admit_oracles = {o["sequence"]:o for o in c["setup_oracles"] if o["kind"] == "admit"}
        uc_need(set(capture_oracles) == set(accepted)-{0xffffffff} and set(admit_oracles) == admitted
                and len(capture_oracles)+len(admit_oracles) == len(c["setup_oracles"]), "complete immutable SETUP/admission oracles")
        for seq,o in capture_oracles.items():
            raw,meta = accepted[seq]
            uc_need(o["record_hex"] == raw.hex() and [seq,o["record_dma"],o["endpoint_fault"],
                        (o["printer_status"][0]<<8)|o["printer_status"][1]] == meta,
                    "SETUP oracle anchored to original input bytes/status")
        for seq,o in admit_oracles.items():
            uc_need(o["record_hex"] == accepted[seq][0].hex(), "admitted raw wire bytes never host-swapped")
        name = c["scenario"]
        if name in ("capture-wait-newer-retry","reset-admission-wait"):
            uc_need(bool(pending_external) and set(pending_external) <= set(accepted),
                    "deferred newer SETUP retries its original identity")
        if name == "reset-admission-wait":
            uc_need(reset_retries == 1, "busy reset retries original tag exactly once")
        if name == "capture-facts":
            uc_need({(2,0,0,f,stall,result) for f,stall,result in (
                (0,1,1),(0x000101,1,1),(0x010001,1,1),(0x010100,1,1),(0x010101,0,1),
                (0x020101,1,3),(0x010201,1,3),(0x0101ff,1,3),(0x010101,2,3))} <= admission_controls,
                "every distinct missing/malformed capture promise remains exercised")
        if name == "raw-admission":
            uc_need({(owner,rx,fault,0x010101,1,result) for owner,rx,fault,result in (
                (0,0,0,1),(1,0,0,1),(3,0,0,1),(2,1,0,4),(2,2,0,4),(2,3,0,4),(2,0,0x80,4))}
                <= admission_controls, "owner/RX/independent-endpoint-fault refusal controls")
        if name == "held-capture-blocks-publication":
            uc_need({41,61} <= blocked, "both prepared lanes refuse delayed publication")
            for i in blocked_indices:
                if events[i]["words"][0] == 41:
                    uc_need(events[i]["words"][1] not in published, "superseded unpublished control never reaches wire")
                elif events[i]["words"][0] == 61:
                    uc_need(events[i]["words"][1] in bulk_published, "same original bulk owner can publish after nondestructive admission")
        if name == "held-capture-blocks-reset-ack":
            stopped = [i for i in blocked_indices if events[i]["words"][0] == 12]
            later = [i for i,ev in enumerate(events) if stopped and i > stopped[0] and ev["words"][0] == 12 and rows[i][0] == 0]
            uc_need(bool(stopped) and len(later) == 1, "deferred reset-ACK refusal and later recovery control")
            for i in later:
                uc_need(rows[i][17] == rows[i-1][17] and rows[i][32] == rows[i-1][32]+1
                        and not rows[i][28] and rows[i-1][45] == 7, "superseded reset recovery emits no old ACK")
        if name.startswith("sequence-limit/") or name == "terminal-drains-admitted-reset":
            uc_need(bool(pending_at_terminal) and srows[-1][10:12] == [1,0], "terminal state preserves explicit stop boundary")
            terminal = next(i for i,s in enumerate(srows) if s[10])
            uc_need(all(uc_forward(r) == uc_forward(rows[terminal]) for r in rows[terminal:]), "terminal boundary creates no forward work")
            if name.startswith("sequence-limit/"):
                uc_need(brows[-1][44] == 0x020200, "terminal local stop is not complete adapter retirement")
            else:
                drain = [i for i in range(pending_at_terminal[0]+1,len(rows))
                         if events[i]["words"][0] == 1 and srows[i-1][11] == 1 and rows[i][0] == 0 and brows[i][44] == 0]
                uc_need(len(drain) == 1 and brows[-1][44] == 0
                        and rows[-1][2] == rows[-1][3] == srows[-1][8], "only previously admitted reset drains pending terminal notifications")

    uc_artifacts = uc_target.get("captured_artifact_sha256", {})
    uc_setup_ref = uc_ref["setup"]
    checks.append(check("composed_raw_setup_ep0_and_bulk_records_preserve_admission_and_ownership",
                        uc["status"] == uc_target.get("status") == "pass" and not uc_bad
                        and len(uc["cases"]) == len(uc_target.get("cases",[])) == 62
                        and {(c["scenario"],c["fill"],c["capacity"],c["interface"]) for c in uc["cases"]} == uc_profiles
                        and uc["actual_peripheral_accesses"] == uc["usb_transfers"] == uc["completed_native_page_lifecycles"] == 0
                        and uc["controller_quiescence_established"] is False
                        and uc_ref["ep0"] == ep0["original_reference"] and uc_ref["bulk"] == udc["original_reference"]
                        and uc_setup_ref["report"] == "analysis/usb-path/setup-ingress.json"
                        and uc_setup_ref["report_sha256"] == hashlib.sha256((ROOT_DIR/uc_setup_ref["report"]).read_bytes()).hexdigest()
                        and uc_setup_ref["stock_sha256"] == ep0_stock_sha
                        and [uc_setup_ref[k] for k in ("source_closure_files","conditional_cases_reused","primary_same_record_cases_reused",
                             "primary_admitted_cases_reused","conditional_separate_pointer_cases_reused","pre_mmio_controls_reused",
                             "excluded_pc_controls_reused","newly_executed_stock_instructions")] == [15,70,64,4,6,6,14,0]
                        and uc_setup_ref["adapter_must_pass_original_wire_bytes"] is True
                        and uc_setup_ref["single_coherent_record_is_supplied_replacement_contract"] is True
                        and uc_setup_ref["physical_mapping_or_snapshot_stability_proved"] is False
                        and uc_setup_ref["controller_quiescence_established"] is False
                        and set(uc_setup_ref["source_paths"]) == set(ingress["source_sha256"]) | {"analysis/usb-path/setup-ingress.json"}
                        and len(uc["source_sha256"]) == EXPECTED_UDC_COMPOSED_SOURCE_COUNT and set(uc["source_sha256"]) == uc_sources
                        and uc["fixture_sha256"] == ep0["fixture_sha256"] == udc["fixture_sha256"] and len(uc["fixture_sha256"]) == 6
                        and uc["effective_source"] == ep0["effective_source"] == read_json("analysis/usb-path/udc-composed/target/effective-source.json")
                        and {"target-check.elf","target-check.map","disassembly.txt","symbols.txt","effective-source.json","annotated-disassembly.txt"} <= set(uc_artifacts)
                        and uc_target.get("elf_sha256") == uc_artifacts.get("target-check.elf") == hashlib.sha256(
                            (ROOT_DIR/"analysis/usb-path/udc-composed/target/target-check.elf").read_bytes()).hexdigest()
                        and all(Path(n).name == n and len(h) == 64 and (n == "annotated-disassembly.txt" or hashlib.sha256(
                            (ROOT_DIR/"analysis/usb-path/udc-composed/target"/n).read_bytes()).hexdigest() == h) for n,h in uc_artifacts.items())
                        and all(hashlib.sha256((ROOT_DIR/n).read_bytes()).hexdigest() == h
                            for key in ("source_sha256","fixture_sha256") for n,h in uc[key].items()),
                        "Raw SETUP captures, exact original EP0/OUT descriptors and deferred reset barriers must preserve immutable identities, supplied-fact gates and separate controller/adapter ownership. Wire (including ZLP), pixels and notifications agree across host/QEMU; reused original-byte evidence adds no stock execution or physical printing."
                            + (" Failed predicates: "+", ".join(sorted(uc_bad)) if uc_bad else ""),
                        evidence="analysis/usb-path/udc-composed/validation.json"))

    retirement_ok, retirement_detail = setup_retirement_consistency_gate(ROOT_DIR)
    checks.append(check(
        "original_setup_retirement_preserves_partial_effects_and_hardware_exclusions",
        retirement_ok, retirement_detail,
        evidence="analysis/usb-path/setup-retirement.json"))

    irq_ok, irq_detail = usb_irq_capture_consistency_gate(ROOT_DIR)
    checks.append(check(
        "original_irq_cuts_preserve_snapshot_selection_and_phase_exclusions",
        irq_ok, irq_detail, evidence="analysis/usb-path/irq-capture.json"))

    offload_ok, offload_detail = usb_offload_consistency_gate(ROOT_DIR)
    checks.append(check(
        "typed_offload_preserves_original_status_owners_and_explicit_cleanup",
        offload_ok, offload_detail, evidence="analysis/usb-path/udc-offload/validation.json"))

    program_gate = runpy.run_path(str(ROOT_DIR / "scripts/check-hp1020-udc-program.py"))["check_program_report"]
    program_ok, program_detail = program_gate(
        read_json("analysis/usb-path/udc-program/validation.json"), source_root=ROOT_DIR)
    checks.append(check(
        "controller_programming_preserves_exact_commands_original_failures_and_status_ownership",
        program_ok, program_detail, evidence="analysis/usb-path/udc-program/validation.json"))

    publish_gate = runpy.run_path(str(ROOT_DIR / "scripts/check-hp1020-udc-publish.py"))["check_publish_report"]
    publish_ok, publish_detail = publish_gate(
        read_json("analysis/usb-path/udc-publish/validation.json"), source_root=ROOT_DIR)
    checks.append(check(
        "bulk_publication_preserves_preflight_exact_ranges_original_owner_and_cleanup",
        publish_ok, publish_detail, evidence="analysis/usb-path/udc-publish/validation.json"))

    acquire_gate = runpy.run_path(str(ROOT_DIR / "scripts/check-hp1020-udc-acquire.py"))["check_acquire_report"]
    acquire_ok, acquire_detail = acquire_gate(
        read_json("analysis/usb-path/udc-acquire/validation.json"), source_root=ROOT_DIR)
    checks.append(check(
        "bulk_acquisition_preserves_original_owner_ordered_cpu_visibility_and_recovery",
        acquire_ok, acquire_detail, evidence="analysis/usb-path/udc-acquire/validation.json"))

    entry_ok, entry_detail = entry_capture_archive_gate(ROOT_DIR)
    checks.append(check(
        "single_entry_establishes_own_cpu_stack_bss_and_continuous_ram_document",
        entry_ok, entry_detail, evidence="analysis/boot-handoff/entry-ram/validation.json"))

    fail_count = severity_count(checks, "fail")
    return {
        "summary": "Cross-report consistency gate for the current offline reverse-engineering state.",
        "status": "pass" if fail_count == 0 else "fail",
        "check_count": len(checks),
        "fail_count": fail_count,
        "high_level_result": (
            "The inert USB bulk receive/framing implementation is internally consistent offline; guarded hardware execution and controller behavior remain unproven, and printing is not implemented."
            if fail_count == 0
            else "Offline analysis has drifted; inspect failed checks before doing hardware work."
        ),
        "checks": checks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Offline Analysis Consistency Check",
        "",
        "This report cross-checks the generated reverse-engineering artifacts against the conclusions we are relying on.",
        "It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- checks: `{report['check_count']}`",
        f"- failures: `{report['fail_count']}`",
        f"- meaning: {report['high_level_result']}",
        "",
        "## Checks",
        "",
        "| Check | Severity | Detail | Evidence |",
        "|---|---|---|---|",
    ]
    for item in report["checks"]:
        lines.append(
            f"| `{item['name']}` | `{item['severity']}` | {item['detail']} | `{item['evidence']}` |"
        )
    lines.extend(
        [
            "",
            "## Practical Meaning",
            "",
            "The mechanically inert USB bulk receive/framing implementation now passes the offline cross-report gate. The next USB unknown is guarded printer-side execution and real controller completion/re-arm behavior; semantic print dispatch, raster output, video transfer, and engine control remain unimplemented or unproven.",
            "",
        ]
    )
    return "\n".join(lines)


def raw_si_composed_profiles():
    names = {
        'raw-si/live-partial', 'raw-si/retained-ep0', 'raw-si/field-controls',
        'raw-si/existing-fault', 'raw-si/pending-reset', 'raw-si/bulk-halt',
        'raw-si/unconfigured',
    }
    return {(name, fill, 64, interface)
            for name in names for fill in (0, 204) for interface in (0, 3)}


def raw_si_composed_consistency(report):
    """Supplement, never replace, the composed capture/closure/identity gate.

    The expected requests, packets, decoded black pixels and notification
    generation are literal test intentions. Event inputs and immutable original
    cookies locate transitions; producer labels and returned scenario summaries
    are not oracles. All controller facts are supplied synthetic observations.
    """
    failures = set()

    def need(ok, reason):
        if not ok:
            failures.add(reason)

    def wire_request(kind, request, value=0, index=0, length=0):
        return (bytes((kind, request)) + value.to_bytes(2, 'little') +
                index.to_bytes(2, 'little') + length.to_bytes(2, 'little'))

    def be_words(words):
        return b''.join(value.to_bytes(4, 'big') for value in words)

    def slot(ep0, number):
        return ep0[8 + 48*number:56 + 48*number]

    def unaffected_bulk(row, bulk):
        # Separate semantic groups, deliberately excluding control identity,
        # borrowed EP0 reply storage, EP0 BUSY/STALL and diagnostic result words.
        # In particular dispatch(stalls_cleared=1) may clear fixture EP0 STALL
        # before adapter admission; its low two mask bits are not a bulk effect.
        return (row[4:6], row[7:11], row[12], row[13] & 4, row[14] & 4,
                row[11] & 12, row[30:46], row[50:62], row[69:77], row[81:85],
                row[90:96], bulk[2:7], bulk[10:40])

    def reply_progress(row, ep0):
        # Cancellation is separate from transfer completion or a new proposal.
        return (row[17:19], row[24:26], slot(ep0, 0)[31:34],
                slot(ep0, 1)[31:34])

    selected = [case for case in report['cases']
                if case['scenario'].startswith('raw-si/')]
    matrix = [(case['scenario'], case['fill'], case['capacity'], case['interface'])
              for case in selected]
    need(len(matrix) == 28 and len(set(matrix)) == 28 and
         set(matrix) == raw_si_composed_profiles(), 'raw-SI exact 28-profile matrix')

    for case in selected:
        name, interface = case['scenario'], case['interface']
        tag = f"{name}/fill={case['fill']}/interface={interface}: "

        def check(ok, reason):
            need(ok, tag + reason)

        rows, ep0, bulk, setup, events = (case[key] for key in
            ('steps', 'ep0_steps', 'bulk_steps', 'setup_steps', 'events'))
        shapes = (len(rows), len(ep0), len(bulk), len(setup), len(events))
        if not shapes[0] or len(set(shapes)) != 1 or not all(
                len(r) == 96 and len(e) == 104 and len(b) == 48 and len(s) == 40
                and len(event['words']) == 5
                for r, e, b, s, event in zip(rows, ep0, bulk, setup, events)):
            check(False, 'complete existing 288-word event schema')
            continue

        def before(index):
            if index:
                return rows[index-1], ep0[index-1], bulk[index-1], setup[index-1]
            return (case['initial'], case['initial_ep0'], case['initial_bulk'],
                    case['initial_setup'])

        def op(index):
            return events[index]['words'][0]

        def data(index):
            return bytes.fromhex(events[index]['data_hex'])

        # All seven scopes use existing normalized adapter operations only
        # through the real composed bridges. No direct completion/setup/reset,
        # seeded counters, close/EOF, offload grant or injected submit shortcut.
        allowed = {1, 6, 7, 10, 11, 12, 15, 43, 44, 46, 62, 64, 65, 80, 81, 82, 83}
        check(all(op(i) in allowed for i in range(len(events))),
              'no alternate ingress, EOF, seed or offload bypass')

        set_config = wire_request(0, 9, 1)
        si = wire_request(1, 11, index=interface)
        get_interface = wire_request(0x81, 10, index=interface, length=1)
        port_status = wire_request(0xa1, 1, index=interface, length=1)
        soft_reset = wire_request(0x21, 2, index=interface)
        get_id = wire_request(0xa1, 0, index=interface << 8, length=400)
        halt_out, halt_in = (wire_request(2, 3, index=endpoint) for endpoint in (1, 0x81))
        status_out, status_in = (wire_request(0x82, 0, index=endpoint, length=2)
                                for endpoint in (1, 0x81))
        get_config = wire_request(0x80, 8, length=1)
        get_device = wire_request(0x80, 6, value=0x100, length=18)
        fields = [wire_request(1, 11, value=1, index=interface),
                  wire_request(1, 11, value=0x100, index=interface),
                  wire_request(1, 11, index=0 if interface else 1),
                  wire_request(1, 11, index=0x100 | interface),
                  wire_request(0x81, 11, index=interface),
                  wire_request(1, 11, index=interface, length=1),
                  wire_request(0x81, 11, index=interface, length=1)]
        wanted_requests = {
            'raw-si/live-partial': [set_config, si, get_interface, port_status],
            'raw-si/retained-ep0': [set_config, get_id, si, get_interface, port_status],
            'raw-si/field-controls': [set_config] +
                [raw for request in fields for raw in (request, get_interface, port_status)],
            'raw-si/existing-fault': [set_config, si, get_interface, port_status, soft_reset],
            'raw-si/pending-reset': [set_config, soft_reset, si, get_interface, port_status],
            'raw-si/bulk-halt': [set_config, halt_out, halt_in, si, get_interface,
                                 port_status, status_out, status_in, soft_reset],
            'raw-si/unconfigured': [si, get_config, get_device, set_config,
                                    get_interface, port_status],
        }
        if name not in wanted_requests:
            check(False, 'known raw-SI profile')
            continue

        # Locate actual admitted bytes from the immutable saved record BEFORE
        # dispatch, not setup_oracles or the mutable live source record.
        admitted = []
        for i, event in enumerate(events):
            if op(i) == 82 and event['result'] == 0:
                prev, _, _, held = before(i)
                raw_record = be_words(held[32:36])
                check(held[2:4] == [1, event['words'][1]] and
                      raw_record[:8] == bytes.fromhex('87ff7fffa5c33ca5') and
                      held[22:26] == [event['words'][1], 0x79bdf130, 0, 0] and
                      event['words'][2:] == [0x010101, 1, 0] and
                      rows[i][2] == prev[2] + 1,
                      'literal coherent raw record and supplied admission facts')
                admitted.append((i, rows[i][2], raw_record[8:]))
        check([raw for _, _, raw in admitted] == wanted_requests[name],
              'exact standard/class raw request sequence and complete field controls')
        epochs = {epoch: (i, raw) for i, epoch, raw in admitted}
        check(len(epochs) == len(admitted), 'distinct checked control identities')

        # Literal replies and full EP0 packet shapes, including every zero-size
        # IN status proposal and OUT status owner. The cancelled ID has only its
        # first 64-byte packet; the superseded class reset has no status owner.
        first_id = b'\x01\x90' + b'ABCDEFGHIJKLMNOPQRSTUVWXYZ' * 2 + b'ABCDEFGHIJ'
        device = bytes.fromhex('1201000200000040feca0040000100000001')
        wanted_packets, wanted_shapes = [], {}
        for _, epoch, raw in admitted:
            if (raw[0] & 0x7f) == 1 and raw[1] == 11:
                packets, shapes_for_epoch = [], []
            elif raw == get_id:
                packets, shapes_for_epoch = [first_id], [(1, 64)]
            elif raw in (get_interface, port_status, get_config, get_device,
                         status_out, status_in):
                payload = (b'\x18' if raw == port_status else device if raw == get_device
                           else b'\x01\x00' if raw in (status_out, status_in) else b'\x00')
                packets, shapes_for_epoch = [payload], [(1, len(payload)), (0, 0)]
            elif raw == soft_reset and name == 'raw-si/pending-reset':
                packets, shapes_for_epoch = [], []
            else:
                check(raw in (set_config, soft_reset, halt_out, halt_in),
                      'every reply has a named independent request contract')
                packets, shapes_for_epoch = [b''], [(1, 0)]
            wanted_packets.extend((epoch, packet) for packet in packets)
            wanted_shapes[epoch] = shapes_for_epoch

        prepared = {}
        actual_shapes = {epoch: [] for epoch in epochs}
        for oracle in case['descriptor_oracles']:
            if oracle['kind'] != 'prepare':
                continue
            cookie = oracle['cookie']
            token, epoch = cookie[0], cookie[1]
            check(token not in prepared and epoch in epochs,
                  'EP0 owners belong to one actual admitted raw request')
            prepared[token] = oracle
            actual_shapes.setdefault(epoch, []).append((oracle['slot'], oracle['requested']))
        check(actual_shapes == wanted_shapes, 'literal complete EP0 data/status shapes; rejected SI has none')

        actual_packets, wire, last_packet_step = [], bytearray(), -1
        for oracle in case['packet_oracles']:
            i = oracle['step']
            if not 0 <= i < len(rows):
                check(False, 'packet event index')
                continue
            token, payload = rows[i][28], bytes.fromhex(oracle['expected_hex'])
            check(token in prepared and i >= last_packet_step and
                  oracle['offset'] == len(wire) and rows[i][29] == len(payload) and
                  rows[i][24] == len(wire) + len(payload),
                  'ordered literal packet offsets, lengths and original IN owner')
            if token in prepared:
                actual_packets.append((prepared[token]['cookie'][1], payload))
            wire.extend(payload)
            last_packet_step = i
        check(actual_packets == wanted_packets and
              bytes(wire) == b''.join(packet for _, packet in wanted_packets) and
              len(wire) == rows[-1][24] and
              hashlib.sha256(wire).hexdigest() == case['capture_sha256']['wire'],
              'literal complete wire bytes including separately counted ZLP packets')

        # Every noncancelled EP0 packet is settled by its original identity and
        # explicit all-facts observation, not an invented status/ACK callback.
        old_id_tokens = {token for token, oracle in prepared.items()
                         if epochs.get(oracle['cookie'][1], (None, None))[1] == get_id}
        ep0_completions = {}
        for i, event in enumerate(events):
            if op(i) != 44:
                continue
            token = event['words'][1]
            check(token in prepared and token not in old_id_tokens,
                  'no completion or ACK for cancelled old ID/SI without an owner')
            if token not in prepared:
                continue
            oracle = prepared[token]
            number, length = oracle['slot'], oracle['requested']
            dma = (0x3579bdf0, 0xb68ace00)[number]
            wanted = be_words([0x8800ffff if number else 0x88000000, 0, dma, 0, length])
            prev, pe, _, _ = before(i)
            check(event['words'][2:] == [0x01010101, 0, 0] and data(i) == wanted and
                  event['result'] == 0 and slot(pe, number)[6:11] == oracle['cookie'] and
                  rows[i][18] == prev[18] + 1,
                  'exact EP0 success snapshot, actual length and original cookie')
            ep0_completions[token] = ep0_completions.get(token, 0) + 1
        check(ep0_completions == {token: 1 for token in prepared if token not in old_id_tokens},
              'exactly one supplied completion per noncancelled EP0 owner')

        # All intended image data is one 32-by-8 black page. Generation is an
        # independent policy expectation, never copied from the final row.
        recovered = name in {'raw-si/existing-fault', 'raw-si/pending-reset', 'raw-si/bulk-halt'}
        final_generation = 3 if recovered else 2
        pixels, documents = b'\xff' * 32, [[final_generation, 1, 0, 1, 0]]
        check(case['expected_documents'] == documents and
              case['capture_sha256']['documents'] == hashlib.sha256(be_words(documents[0])).hexdigest() and
              case['pixels_bytes'] == rows[-1][50] == 32 and
              case['expected_pixels_sha256'] == case['capture_sha256']['pixels'] ==
                  hashlib.sha256(pixels).hexdigest() and
              rows[-1][32] == final_generation and rows[-1][90:94] == [1, 1, 1, final_generation] and
              rows[-1][95] == 1 and rows[-1][7] == rows[-1][36] == rows[-1][40] == 0,
              'literal pixels and exactly-once original-generation END_DOC without EOF')

        si_windows = []
        for i, epoch, raw in admitted:
            if not ((raw[0] & 0x7f) == 1 and raw[1] == 11):
                continue
            prev, pe, pb, _ = before(i)
            stop = next((j for j in range(i+1, len(rows)) if op(j) == 1 and
                         rows[j][0] == 0 and rows[j][2:4] == [epoch, epoch] and
                         rows[j][11] & 3 == 3), None)
            check(stop is not None, 'actual service reaches explicit EP0 STALL')
            if stop is None:
                continue
            check(not any(op(j) in (80, 81, 82, 83) for j in range(i+1, stop+1)),
                  'rejection belongs to this original SI before any newer request')
            end = stop
            while end+1 < len(events) and op(end+1) == 1:
                end += 1
            for j in range(i, end+1):
                check(unaffected_bulk(rows[j], bulk[j]) == unaffected_bulk(prev, pb),
                      'SI preserves bulk identity, storage, fault/fence and exact reset ticket/promises')
                check(reply_progress(rows[j], ep0[j]) == reply_progress(prev, pe) and
                      rows[j][80] == prev[80] and rows[j][47] == 0,
                      'SI neither creates a class request/status/completion nor revives deferred ACK')
            check(rows[stop][26] == rows[stop][28] == rows[stop][77] == 0 and
                  slot(ep0[stop], 0)[0] == slot(ep0[stop], 1)[0] == 0,
                  'rejection retains no EP0 owner or borrowed reply')
            si_windows.append((i, stop, end, prev, pe, pb, epoch))
        check(len(si_windows) == (7 if name == 'raw-si/field-controls' else 1),
              'every intended SI has a verified rejection window')
        if not si_windows:
            continue

        # Recovery uses one saved current ticket and all THREE separate
        # acknowledgements. A raw SI cannot advance generation; callbacks from
        # decoded END_DOC continue to carry that original receive generation.
        tickets, ticket_steps, finished = {}, {}, []
        for i, event in enumerate(events):
            operation, index, part, _, _ = event['words']
            prev, _, _, held = before(i)
            row = rows[i]
            if operation == 10 and event['result'] == 0:
                check(prev[44] == 1 and prev[43] == prev[32] and prev[42] != 0,
                      'saved recovery ticket is active and from current receive generation')
                tickets[index], ticket_steps[index] = prev[42:44], i
            if operation == 11:
                check(event['result'] == 0 and tickets.get(index) == prev[42:44] and
                      prev[44] == 1 and prev[43] == prev[32] and part in (1, 2, 4) and
                      prev[45] & part == 0 and row[45] == prev[45] | part and
                      row[32] == prev[32] and row[42:45] == prev[42:45],
                      'independent promise uses original active ticket without retagging')
                if part == 4:
                    check(any(op(j) == 15 and events[j]['result'] == 0
                              for j in range(ticket_steps.get(index, i), i)),
                          'transport promise follows separately supplied bulk defaults/settlement')
            if operation == 12 and event['result'] == 0:
                check(tickets.get(index) == prev[42:44] and prev[44:46] == [1, 7] and
                      prev[32] == prev[43] and row[32] == prev[32]+1 and
                      row[35] == row[36] == row[7] == row[44] == row[45] == 0,
                      'restart requires all promises for the original ticket exactly once')
                finished.append(i)
            elif row[32] != prev[32]:
                check(False, 'generation changes only on explicitly completed real recovery')
        check(bool(finished) and len(finished) == (2 if recovered else 1) and
              rows[finished[0]][32] == 2,
              'configuration recovery and any separate real recovery are counted independently')

        si_first, si_last = si_windows[0][0], si_windows[-1][2]
        successful_resets = [i for i, event in enumerate(events)
                             if op(i) == 83 and event['result'] == 0]
        check(len(successful_resets) == (2 if name == 'raw-si/unconfigured' else 1) and
              successful_resets[0] < si_first,
              'actual bus reset observations are distinct from raw SI')

        healthy = name in {'raw-si/live-partial', 'raw-si/retained-ep0', 'raw-si/field-controls'}
        if healthy:
            original = si_windows[0][5][16:21]
            token = original[0]
            check(token != 0 and original[2:] == [2, 2, 1],
                  'partially received page owns original second receive reservation')
            for _, _, _, prev, _, pb, _ in si_windows:
                check(prev[7] == prev[36] == prev[44] == 0 and prev[32] == 2 and
                      prev[30] == token and pb[2] == 2 and pb[3] == 0 and
                      pb[16:21] == original and original[1] == prev[5],
                      'healthy live OUT is neither stopped, cancelled nor retagged by any SI')
            settlements = [i for i, event in enumerate(events)
                           if op(i) == 62 and event['words'][1] == token]
            check(len(settlements) == 1 and settlements[0] > si_last and
                  not any(op(i) == 64 and events[i]['words'][1] == token for i in range(len(events))),
                  'same original OUT completes normally after all rejection/control requests')
            if len(settlements) == 1:
                j = settlements[0]
                prev, _, pb, _ = before(j)
                check(all(rows[k][7] == rows[k][36] == rows[k][44] == 0 and
                          rows[k][32] == 2 and rows[k][30] == token and
                          bulk[k][16:21] == original and rows[k][5] == original[1]
                          for k in range(si_first, j)),
                      'same healthy receive owner remains live through intervening control recovery')
                check(events[j]['words'][2:] == [0x010101, 0, 0] and events[j]['result'] == 0 and
                      data(j) == be_words([0x8800001f, 0, pb[22], 0]) and
                      prev[30] == token and pb[16:21] == original and
                      rows[j][32] == 2 and rows[j][30] == 0 and bulk[j][44] >> 16 == 2,
                      'original 31-byte partial buffer settles before adapter notification')

        ep0_cancel = [i for i in range(len(events)) if op(i) == 43]
        bulk_cancel = [i for i in range(len(events)) if op(i) == 64]
        check(len(ep0_cancel) == (2 if name == 'raw-si/retained-ep0' else 0) and
              len(bulk_cancel) == (2 if name == 'raw-si/existing-fault' else 0),
              'only specifically retained original owners require cancellation settlement')

        if name == 'raw-si/retained-ep0':
            _, stop, _, prev, pe, _, epoch = si_windows[0]
            old = slot(pe, 1)
            token = prev[28]
            check(old_id_tokens == {token} and old[0] == 2 and old[5] == 64 and
                  old[6:11] == prepared[token]['cookie'] and old[7] < epoch and prev[77] == 1,
                  'cancelled ID retains its older original epoch and borrowed 64-byte source')
            if len(ep0_cancel) == 2:
                wait, settle = ep0_cancel
                check(si_first < wait < settle < stop and
                      events[wait]['words'] == [43, token, 0, 0, 0] and events[wait]['result'] == 1 and
                      events[settle]['words'] == [43, token, 1, 0, 0] and events[settle]['result'] == 0,
                      'explicit missing-then-present original EP0 settlement')
                for j in range(si_first, settle):
                    p = slot(ep0[j], 1)
                    check(rows[j][3] == prev[3] and rows[j][28] == token and rows[j][77] == 1 and
                          p[0] == 2 and p[1] == 1 and p[6:11] == old[6:11] and
                          p[14:18] == old[14:18] and p[42] == old[42] and rows[j][11] & 3 == 0,
                          'protocol dispatch waits while original descriptor/source/staging remain owned')
                check(any(op(j) == 1 and events[j]['result'] == 1 for j in range(si_first+1, settle)) and
                      rows[settle][28] == 0 and slot(ep0[settle], 1)[0] == 0 and
                      rows[settle][77] == 1 and
                      (bulk[settle][44] >> 8) & 255 == 2 and rows[settle][3] == prev[3] and
                      (bulk[stop][44] >> 8) & 255 == 0,
                      'controller settlement leaves PENDING until later service, never fictitious retirement')

        if name == 'raw-si/existing-fault':
            _, _, _, prev, _, pb, _ = si_windows[0]
            token, original = prev[30], pb[16:21]
            faults = [i for i, event in enumerate(events) if op(i) == 62 and
                      event['words'][1:] == [token, 0, 0x80, 0]]
            check(len(faults) == 1 and faults[0] < si_first and events[faults[0]]['result'] == 4 and
                  data(faults[0]) == be_words([0x48000000, 0, pb[22], 0]) and
                  prev[7] == prev[36] == pb[3] == 1 and prev[44] == 0 and original[2] == 2,
                  'independent endpoint fault is retained; rejection is not recovery')
            recovery_step = next((i for i, _, raw in admitted if raw == soft_reset), None)
            check(recovery_step is not None and recovery_step > si_last and
                  any(op(j) == 6 and events[j]['result'] == 1
                      for j in range(si_last+1, recovery_step if recovery_step is not None else si_last+1)),
                  'input remains blocked until separately admitted class SOFT_RESET')
            if recovery_step is not None:
                check(all(unaffected_bulk(rows[j], bulk[j]) == unaffected_bulk(prev, pb)
                          for j in range(si_first, recovery_step)),
                      'ordinary control recovery cannot clear the existing bulk fault or stop fence')
            if len(bulk_cancel) == 2 and recovery_step is not None:
                wait, settle = bulk_cancel
                check(recovery_step < wait < settle and
                      events[wait]['words'] == [64, token, 0, 0, 0] and events[wait]['result'] == 1 and
                      events[settle]['words'] == [64, token, 1, 0, 0] and events[settle]['result'] == 0 and
                      bulk[wait][16:21] == original and rows[wait][30] == token and
                      rows[settle][30] == 0 and bulk[settle][2] == 0 and bulk[settle][44] >> 16 == 2 and
                      bool(finished) and finished[-1] > settle,
                      'separate recovery settles exact old bulk before restarting with new generation')

        if name == 'raw-si/pending-reset':
            _, stop, _, prev, pe, pb, _ = si_windows[0]
            check(prev[44:48] == [1, 7, 0, 1] and prev[32] == 2,
                  'pre-existing reset has all promises and an older deferred status')
            held_finishes = [i for i in range(si_first) if op(i) == 12 and
                             events[i]['result'] == 1 and before(i)[3][2] == 1 and
                             before(i)[0][44:46] == [1, 7]]
            check(len(held_finishes) == 1 and
                  rows[held_finishes[0]][2:96] == before(held_finishes[0])[0][2:96],
                  'captured but unadmitted SI already blocks the old status/restart')
            after = [i for i in finished if i > stop]
            check(len(after) == 1, 'exact original recovery finishes once after rejection')
            if len(after) == 1:
                j = after[0]
                prior = before(j)[0]
                check(prior[42:46] == prev[42:46] and prior[47] == 0 and
                      not any(op(k) in (80, 81, 82, 83) for k in range(stop+1, j)) and
                      reply_progress(rows[j], ep0[j]) == reply_progress(prev, pe) and
                      rows[j][26] == rows[j][28] == 0,
                      'SI alone suppresses old deferred ACK while original ticket later restarts input')

        if name == 'raw-si/bulk-halt':
            _, _, _, prev, _, _, _ = si_windows[0]
            recovery_step = next((i for i, _, raw in admitted if raw == soft_reset), None)
            check(prev[81:85] == [1, 1, 1, 1] and prev[7] == prev[36] == 1 and prev[44] == 0,
                  'raw SI arrives with independently established bulk HALTs and no recovery')
            if recovery_step is not None:
                check(all(rows[j][81:85] == [1, 1, 1, 1] and rows[j][32] == 2
                          for j in range(si_first, recovery_step)) and
                      not any(op(j) == 15 for j in range(si_first, recovery_step)) and
                      bool(finished) and finished[-1] > recovery_step,
                      'both endpoint HALTs survive SI and control queries until separately requested reset')
            else:
                check(False, 'separately admitted real recovery after retained HALTs')

        if name == 'raw-si/unconfigured':
            _, stop, _, prev, _, _, _ = si_windows[0]
            configuration_step = next((i for i, _, raw in admitted if raw == set_config), None)
            check(prev[32] == 1 and prev[8] == prev[10] == prev[44] == 0 and
                  configuration_step is not None and configuration_step > stop,
                  'unconfigured SI cannot create configuration or a document recovery')
            if configuration_step is not None:
                check(all(row[32] == 1 and row[8] == row[10] == row[44] == 0
                          for row in rows[stop:configuration_step]) and
                      any(op(j) == 10 and events[j]['result'] == 1 for j in range(stop, configuration_step)) and
                      any(op(j) == 6 and events[j]['result'] == 1 for j in range(stop, configuration_step)) and
                      bool(finished) and finished[0] > configuration_step,
                      'configuration query/device reply do not unlock input; real configuration does')

    return not failures, '; '.join(sorted(failures))


def main() -> int:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(report) + "\n")
    print(f"checks={report['check_count']} fail={report['fail_count']}")
    print(OUT_MD)
    return 1 if report["fail_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
