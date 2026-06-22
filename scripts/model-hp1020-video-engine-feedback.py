#!/usr/bin/env python3
"""Model HP 1020 video-to-engine feedback.

This is offline analysis only. It records how the VideoThread and video reset
dispatch path send messages back toward the engine/status side after render,
flush, or video reset/error cases.
"""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-engine-feedback.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-engine-feedback.md"

SOURCES = {
    "video_thread": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10013c18_hp1020_video_thread_candidate.c",
    "reset_dispatch": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10013d4c_hp1020_video_reset_dispatch_candidate.c",
    "reset_flush": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015458_hp1020_video_reset_or_flush_candidate.c",
    "render": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015214_hp1020_video_render_or_dma_candidate.c",
    "engine_dispatch": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c",
}

LITERALS = {
    "video_reset_event_case_3": 0x100067A4,
    "video_reset_event_case_4": 0x100067A8,
    "video_reset_event_case_5": 0x100067AC,
    "video_reset_event_case_6": 0x100067B0,
    "video_reset_event_case_2_or_7": 0x100067B4,
    "video_transfer_status_control": 0x10006790,
    "video_channel_b_control": 0x10006794,
    "video_channel_a_control": 0x10006798,
    "video_channel_a_status": 0x1000679C,
    "video_channel_b_status": 0x100067A0,
    "video_channel_status_clear_mask": 0x1000628C,
    "video_block_a_status": 0x100067C0,
    "video_block_b_status": 0x100067D8,
    "video_block_a_control": 0x10006808,
    "video_block_b_control": 0x1000680C,
}

CHECKS = [
    ("video_queue_receive", "video_thread", "threadx_queue_receive_wait_candidate"),
    ("video_queue_message_0x0b", "video_thread", "if (aiStack_30[0] == 0xb) break"),
    ("video_queue_message_0x0f", "video_thread", "if (aiStack_30[0] == 0xf)"),
    ("video_active_slot_0x60", "video_thread", "*(undefined4 *)(puVar1 + 0x60) = uStack_24"),
    ("video_deferred_slot_0x64", "video_thread", "*(undefined4 *)(puVar1 + 100) = uStack_24"),
    ("video_normal_prepare", "video_thread", "hp1020_video_prepare_page_candidate(piVar3)"),
    ("video_normal_render", "video_thread", "hp1020_video_render_or_dma_candidate(piVar3)"),
    ("video_alt_render", "video_thread", "hp1020_video_alt_render_candidate(piVar3)"),
    ("video_done_engine_0x10", "video_thread", "aiStack_30[0] = 0x10"),
    ("video_done_send_engine_queue", "video_thread", "hp1020_queue_send_candidate(1,aiStack_30)"),
    ("reset_dispatch_case_0_engine_0x11", "reset_dispatch", "local_30 = 0x11"),
    ("reset_dispatch_requeue_0x0b", "reset_dispatch", "hp1020_send_or_raise_engine_msg_candidate(8,&local_30)"),
    ("reset_dispatch_case_1_0x25", "reset_dispatch", "local_30 = 0x25"),
    ("reset_dispatch_event_0x17", "reset_dispatch", "local_30 = 0x17"),
    ("reset_dispatch_clears_0x68", "reset_dispatch", "*(undefined4 *)(hp1020_video_state_ptr_word + 0x68) = 0"),
    ("reset_flush_calls_dispatch_1", "reset_flush", "hp1020_video_reset_dispatch_candidate(1)"),
    ("render_sets_state_0x6c_2", "render", "*(undefined4 *)(hp1020_video_state_ptr_word + 0x6c) = 2"),
    ("engine_case_0x11_receives_video_done", "engine_dispatch", "case 0x11:"),
]


@dataclass(frozen=True)
class ElfImage:
    data: bytes
    load_segments: list[tuple[int, int, int]]

    @classmethod
    def load(cls, path: Path) -> "ElfImage":
        data = path.read_bytes()
        if data[:4] != b"\x7fELF" or data[5] != 2:
            raise ValueError(f"{path} is not a big-endian ELF")
        phoff = struct.unpack(">I", data[28:32])[0]
        phentsize = struct.unpack(">H", data[42:44])[0]
        phnum = struct.unpack(">H", data[44:46])[0]
        load_segments = []
        for index in range(phnum):
            off = phoff + index * phentsize
            p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _p_flags, _p_align = struct.unpack(
                ">IIIIIIII", data[off : off + 32]
            )
            if p_type == 1:
                load_segments.append((p_offset, p_vaddr, p_filesz))
        return cls(data, load_segments)

    def read_u32(self, addr: int) -> int:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - 4:
                off = p_offset + (addr - p_vaddr)
                return struct.unpack(">I", self.data[off : off + 4])[0]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def read_sources() -> dict[str, str]:
    return {name: path.read_text(errors="replace") for name, path in SOURCES.items()}


def literal_values(elf: ElfImage) -> dict[str, str]:
    return {name: fmt32(elf.read_u32(addr)) for name, addr in LITERALS.items()}


def feedback_sequences(literals: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "name": "normal_video_done",
            "source": "0x10013c18 hp1020_video_thread_candidate",
            "trigger": "video queue message 0x0b with page work pointer",
            "state_slots": ["video_state +0x60 active work", "video_state +0x64 deferred work"],
            "messages": [
                {"target": "queue 1", "message": "0x10", "payload": "original video queue payload"},
            ],
            "meaning": "After prepare/render, VideoThread tells the engine side that video work reached the post-render checkpoint.",
        },
        {
            "name": "video_reset_or_flush",
            "source": "0x10013c18 -> 0x10015458 -> 0x10013d4c",
            "trigger": "video queue message 0x0f",
            "state_slots": ["clear video_state +0x60", "clear video_state +0x64"],
            "messages": [
                {"target": "queue 1 via wrapper", "message": "0x25", "payload": "no event word in word 1"},
            ],
            "meaning": "Flush/reset clears active/deferred video work and reports reset completion through the engine/status side.",
        },
        {
            "name": "reset_dispatch_complete_active",
            "source": "0x10013d4c hp1020_video_reset_dispatch_candidate(param=0)",
            "trigger": "engine poll/reset path calls video reset dispatch with param 0",
            "state_slots": [
                "clear video_state +0x60 active work",
                "if video_state +0x64 deferred work exists, requeue it as video queue message 0x0b then clear +0x64",
            ],
            "messages": [
                {"target": "wrapper target 0", "message": "0x11", "payload": "completion/advance"},
                {"target": "wrapper target 8", "message": "0x0b", "payload": "deferred video work when present"},
            ],
            "meaning": "This is the strongest current video-to-engine work-advance bridge.",
        },
        {
            "name": "reset_dispatch_event_words",
            "source": "0x10013d4c hp1020_video_reset_dispatch_candidate(param=2..7)",
            "trigger": "video reset dispatch error/status cases",
            "state_slots": ["clear video_state +0x68", "clear video_state +0x6c"],
            "messages": [
                {"target": "queue 1 via wrapper", "message": "0x17", "payload": literals["video_reset_event_case_2_or_7"], "case": "2 or 7"},
                {"target": "queue 1 via wrapper", "message": "0x17", "payload": literals["video_reset_event_case_3"], "case": "3"},
                {"target": "queue 1 via wrapper", "message": "0x17", "payload": literals["video_reset_event_case_4"], "case": "4"},
                {"target": "queue 1 via wrapper", "message": "0x17", "payload": literals["video_reset_event_case_5"], "case": "5"},
                {"target": "queue 1 via wrapper", "message": "0x17", "payload": literals["video_reset_event_case_6"], "case": "6"},
            ],
            "meaning": "Video reset/error states enter the same engine event word stream as mechanical status polling.",
        },
    ]


def state_fields() -> list[dict[str, str]]:
    return [
        {"offset": "+0x60", "field": "active video work pointer", "meaning": "work currently being prepared/rendered by VideoThread"},
        {"offset": "+0x64", "field": "deferred video work pointer", "meaning": "second work item held while active slot is occupied"},
        {"offset": "+0x68", "field": "reset/dispatch scratch slot", "meaning": "cleared at the end of video reset dispatch"},
        {"offset": "+0x6c", "field": "video state/mode flag", "meaning": "set to 2 after render reaches transfer-running state; cleared at reset dispatch end"},
        {"offset": "+0x94", "field": "video ring read/consumer index candidate", "meaning": "compared with +0x98 before descriptor handoff"},
        {"offset": "+0x98", "field": "video ring write/producer index candidate", "meaning": "advanced modulo 4 in render path"},
        {"offset": "+0x9c", "field": "active raster list pointer", "meaning": "set from work +0x50 before render"},
        {"offset": "+0xa0", "field": "raster/reset walk list", "meaning": "walked and drained during reset dispatch"},
        {"offset": "+0xa4", "field": "saved raster pointer", "meaning": "set when render captures the current raster list"},
        {"offset": "+0xfc", "field": "reset dispatch sign/latch field", "meaning": "gates a decompiler-broken reset-dispatch branch; exact meaning unresolved"},
    ]


def hardware_reset_registers(literals: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"register": literals["video_transfer_status_control"], "role": "transfer status/control bit 0 cleared during reset dispatch"},
        {"register": literals["video_channel_b_control"], "role": "channel B reset/enable toggled with bit 0x2"},
        {"register": literals["video_channel_a_control"], "role": "channel A reset/enable toggled with bit 0x2"},
        {"register": literals["video_channel_a_status"], "role": "channel A status bit 0 waited clear and masked with 0x7fffffff"},
        {"register": literals["video_channel_b_status"], "role": "channel B status bit 0 waited clear and masked with 0x7fffffff"},
        {"register": literals["video_block_a_control"], "role": "video block A control bit 0x100 cleared/set in reset flush"},
        {"register": literals["video_block_b_control"], "role": "video block B control bit 0x100 cleared/set in reset flush"},
        {"register": literals["video_block_a_status"], "role": "video block A busy bit 0x200 wait in reset flush"},
        {"register": literals["video_block_b_status"], "role": "video block B busy bit 0x200 wait in reset flush"},
    ]


def evidence_checks(sources: dict[str, str]) -> list[dict[str, str]]:
    return [
        {
            "name": name,
            "status": "present" if needle in sources[source_name] else "missing",
            "source": str(SOURCES[source_name].relative_to(ROOT_DIR)),
            "needle": needle,
        }
        for name, source_name, needle in CHECKS
    ]


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    sources = read_sources()
    literals = literal_values(elf)
    checks = evidence_checks(sources)
    missing = [check for check in checks if check["status"] != "present"]
    return {
        "summary": "Video-to-engine feedback model for first-page render completion and reset/error cases.",
        "status": "pass" if not missing else "fail",
        "literal_values": literals,
        "feedback_sequences": feedback_sequences(literals),
        "state_fields": state_fields(),
        "hardware_reset_registers": hardware_reset_registers(literals),
        "checks": checks,
        "open_firmware_implication": [
            "Printing firmware needs this feedback loop, not only parser and video register writes.",
            "The normal render path reports message 0x10 to engine queue 1 after prepare/render.",
            "Video reset/error cases produce engine event 0x17 words that share the status pipeline with mechanical engine polling.",
            "The next missing offline model is exact timing/ownership around the video transfer ring and interrupts, especially how +0x94/+0x98/+0x9c/+0xa0 advance.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Video-to-Engine Feedback Model",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: VideoThread completion, reset dispatch, and engine/status feedback messages",
        "",
        "## Key Literal Values",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["literal_values"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(["", "## Feedback Sequences", ""])
    for sequence in report["feedback_sequences"]:
        lines.extend(
            [
                f"### `{sequence['name']}`",
                "",
                f"- source: `{sequence['source']}`",
                f"- trigger: {sequence['trigger']}",
                f"- meaning: {sequence['meaning']}",
                "",
                "| Target | Message | Payload | Case |",
                "|---|---:|---:|---|",
            ]
        )
        for message in sequence["messages"]:
            lines.append(
                f"| `{message['target']}` | `{message['message']}` | `{message.get('payload', '-')}` | `{message.get('case', '-')}` |"
            )
        lines.extend(["", "State slots:"])
        for slot in sequence["state_slots"]:
            lines.append(f"- {slot}")
        lines.append("")

    lines.extend(["## Video State Fields", "", "| Offset | Field | Meaning |", "|---:|---|---|"])
    for item in report["state_fields"]:
        lines.append(f"| `{item['offset']}` | {item['field']} | {item['meaning']} |")

    lines.extend(["", "## Hardware Reset Registers", "", "| Register | Role |", "|---:|---|"])
    for item in report["hardware_reset_registers"]:
        lines.append(f"| `{item['register']}` | {item['role']} |")

    lines.extend(["", "## Evidence Checks", "", "| Check | Status | Source | Needle |", "|---|---|---|---|"])
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['name']}` | `{check['status']}` | `{check['source']}` | `{needle}` |")

    lines.extend(["", "## Open Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, default=ELF_PATH)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    report = build_report(args.elf)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(f"status={report['status']} checks={len(report['checks'])} sequences={len(report['feedback_sequences'])}")
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
