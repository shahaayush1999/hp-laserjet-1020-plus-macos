#!/usr/bin/env python3
"""Exercise a mechanically inert HP 1020 USB/ZjStream parser model offline.

The model accepts deterministic host-side receive descriptors, copies them
through a 0x400-byte circular buffer, recognizes ZjStream framing, and updates
counters. It never opens a USB device and has no video, engine, or mechanical
output path.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
SAMPLES_DIR = ROOT_DIR / "analysis/samples/generated"
OUT_DIR = ROOT_DIR / "analysis/open-firmware-probes/usb-bulk-parser-draft"
OUT_JSON = OUT_DIR / "parser-model.json"
OUT_MD = OUT_DIR / "parser-model.md"

MAGIC = b"JZJZ"
CHUNK_HEADER = struct.Struct(">IIIHH")
CHUNK_HEADER_BYTES = CHUNK_HEADER.size
CHUNK_SIGNATURE = 0x5A5A
RECEIVE_BUFFER_BYTES = 0x400
MAX_CHUNK_BYTES = 16 * 1024 * 1024

REQUIRED_COUNTERS = (
    "bytes_received",
    "receive_descriptors_completed",
    "recognized_chunks",
    "parser_errors",
    "unknown_chunks",
)

EXPECTED_STOCK_TYPES = {
    0x00: "ZJT_START_DOC",
    0x01: "ZJT_END_DOC",
    0x02: "ZJT_START_PAGE",
    0x03: "ZJT_END_PAGE",
    0x04: "ZJT_JBIG_BIH",
    0x05: "ZJT_JBIG_BID",
    0x06: "ZJT_END_JBIG",
    0x07: "ZJT_SIGNATURE",
    0x08: "ZJT_RAW_IMAGE",
    0x09: "ZJT_START_PLANE",
    0x0A: "ZJT_END_PLANE",
    0x0B: "ZJT_2600N_PAUSE",
    0x0C: "ZJT_2600N",
}

PROBE_RECOGNIZED_TYPES = tuple(range(0x00, 0x07))

DAILY_SAMPLE_SEQUENCE = (0x00, 0x02, 0x04, 0x05, 0x06, 0x03, 0x01)


@dataclass
class ParserCounters:
    bytes_received: int = 0
    receive_descriptors_completed: int = 0
    recognized_chunks: int = 0
    parser_errors: int = 0
    unknown_chunks: int = 0

    def as_dict(self) -> dict[str, int]:
        return {name: int(getattr(self, name)) for name in REQUIRED_COUNTERS}


class CircularReceiveBuffer:
    """Fixed-size byte ring used between descriptor completion and parsing."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._storage = bytearray(capacity)
        self.read_index = 0
        self.write_index = 0
        self.occupancy = 0
        self.peak_occupancy = 0
        self.read_wraps = 0
        self.write_wraps = 0

    def write(self, data: bytes) -> None:
        if len(data) > self.capacity - self.occupancy:
            raise BufferError(
                f"receive ring overflow: bytes={len(data)} free={self.capacity - self.occupancy}"
            )
        if not data:
            return

        old_index = self.write_index
        first = min(len(data), self.capacity - old_index)
        self._storage[old_index : old_index + first] = data[:first]
        remainder = len(data) - first
        if remainder:
            self._storage[:remainder] = data[first:]
        self.write_wraps += (old_index + len(data)) // self.capacity
        self.write_index = (old_index + len(data)) % self.capacity
        self.occupancy += len(data)
        self.peak_occupancy = max(self.peak_occupancy, self.occupancy)

    def read_byte(self) -> int:
        if self.occupancy == 0:
            raise BufferError("read from empty receive ring")
        value = self._storage[self.read_index]
        self.read_index += 1
        if self.read_index == self.capacity:
            self.read_index = 0
            self.read_wraps += 1
        self.occupancy -= 1
        return value


class InertZjStreamParser:
    """Streaming framing parser with no print-path side effects."""

    SEEK_MAGIC = "seek_magic"
    READ_HEADER = "read_header"
    SKIP_PAYLOAD = "skip_payload"

    def __init__(self, known_types: dict[int, str]) -> None:
        self.known_types = dict(known_types)
        self.counters = ParserCounters()
        self.ring = CircularReceiveBuffer(RECEIVE_BUFFER_BYTES)
        self.state = self.SEEK_MAGIC
        self._magic_window = bytearray()
        self._seek_run_bytes = 0
        self._header = bytearray()
        self._payload_remaining = 0
        self._current_chunk: dict[str, int] | None = None
        self._document_open = False
        self._finalized = False

        self.documents_started = 0
        self.documents_completed = 0
        self.documents_aborted = 0
        self.envelope_bytes_discarded = 0
        self.total_chunks = 0
        self.chunk_type_sequence: list[int] = []
        self.recognized_by_type: Counter[int] = Counter()
        self.error_kinds: Counter[str] = Counter()

    def feed_descriptor(self, data: bytes) -> None:
        if self._finalized:
            raise RuntimeError("cannot feed a finalized parser")
        if len(data) > RECEIVE_BUFFER_BYTES:
            raise ValueError(
                f"descriptor exceeds 0x{RECEIVE_BUFFER_BYTES:x}-byte receive buffer: {len(data)}"
            )

        self.counters.bytes_received += len(data)
        self.counters.receive_descriptors_completed += 1
        self.ring.write(data)
        while self.ring.occupancy:
            self._consume_byte(self.ring.read_byte())

    def finalize(self) -> None:
        if self._finalized:
            return
        if self.state == self.READ_HEADER and self._document_open:
            self._record_error("truncated_chunk_header")
        elif self.state == self.SKIP_PAYLOAD:
            self._record_error("truncated_chunk_payload")
        if self.state == self.SEEK_MAGIC:
            self.envelope_bytes_discarded += self._seek_run_bytes
            self._seek_run_bytes = 0
        self._finalized = True

    def snapshot(self) -> dict[str, Any]:
        return {
            **self.counters.as_dict(),
            "documents_started": self.documents_started,
            "documents_completed": self.documents_completed,
            "documents_aborted": self.documents_aborted,
            "total_chunks": self.total_chunks,
            "envelope_bytes_discarded": self.envelope_bytes_discarded,
            "ring_capacity": self.ring.capacity,
            "ring_peak_occupancy": self.ring.peak_occupancy,
            "ring_read_index": self.ring.read_index,
            "ring_write_index": self.ring.write_index,
            "ring_read_wraps": self.ring.read_wraps,
            "ring_write_wraps": self.ring.write_wraps,
            "ring_occupancy": self.ring.occupancy,
            "final_state": self.state,
            "chunk_type_sequence": [f"0x{chunk_type:02x}" for chunk_type in self.chunk_type_sequence],
            "recognized_by_type": {
                f"0x{chunk_type:02x} {self.known_types[chunk_type]}": count
                for chunk_type, count in sorted(self.recognized_by_type.items())
            },
            "error_kinds": dict(sorted(self.error_kinds.items())),
            "side_effects": {
                "usb_device_opens": 0,
                "usb_transfers_submitted": 0,
                "mmio_reads": 0,
                "mmio_writes": 0,
                "video_commands": 0,
                "engine_commands": 0,
                "mechanical_actions": 0,
            },
        }

    def _consume_byte(self, value: int) -> None:
        if self.state == self.SEEK_MAGIC:
            self._consume_magic_byte(value)
        elif self.state == self.READ_HEADER:
            self._header.append(value)
            if len(self._header) == CHUNK_HEADER_BYTES:
                self._begin_chunk()
        elif self.state == self.SKIP_PAYLOAD:
            self._payload_remaining -= 1
            if self._payload_remaining == 0:
                self._complete_chunk()
        else:
            raise AssertionError(f"unknown parser state: {self.state}")

    def _consume_magic_byte(self, value: int) -> None:
        self._seek_run_bytes += 1
        self._magic_window.append(value)
        if len(self._magic_window) > len(MAGIC):
            del self._magic_window[0]
        if bytes(self._magic_window) != MAGIC:
            return

        self.envelope_bytes_discarded += self._seek_run_bytes - len(MAGIC)
        self._seek_run_bytes = 0
        self._magic_window.clear()
        self.documents_started += 1
        self._document_open = True
        self._header.clear()
        self.state = self.READ_HEADER

    def _begin_chunk(self) -> None:
        size, chunk_type, item_count, reserved, signature = CHUNK_HEADER.unpack(self._header)
        self._header.clear()
        payload_bytes = size - CHUNK_HEADER_BYTES

        if size < CHUNK_HEADER_BYTES:
            self._record_error("chunk_size_below_header")
            return
        if size > MAX_CHUNK_BYTES:
            self._record_error("chunk_size_above_model_limit")
            return
        if signature != CHUNK_SIGNATURE:
            self._record_error("bad_chunk_signature")
            return
        if reserved > payload_bytes:
            self._record_error("reserved_bytes_exceed_payload")
            return

        self._current_chunk = {
            "size": size,
            "type": chunk_type,
            "item_count": item_count,
            "reserved": reserved,
            "payload_bytes": payload_bytes,
        }
        self._payload_remaining = payload_bytes
        if payload_bytes:
            self.state = self.SKIP_PAYLOAD
        else:
            self._complete_chunk()

    def _complete_chunk(self) -> None:
        if self._current_chunk is None:
            raise AssertionError("chunk completion without a current header")
        chunk_type = self._current_chunk["type"]
        self.total_chunks += 1
        self.chunk_type_sequence.append(chunk_type)
        if chunk_type in self.known_types:
            self.counters.recognized_chunks += 1
            self.recognized_by_type[chunk_type] += 1
        else:
            # The narrow probe counts every framed type outside 0x00..0x06 as unknown.
            self.counters.unknown_chunks += 1

        self._current_chunk = None
        self._payload_remaining = 0
        if chunk_type == 0x01:
            self.documents_completed += 1
            self._document_open = False
            self.state = self.SEEK_MAGIC
        else:
            self.state = self.READ_HEADER

    def _record_error(self, kind: str) -> None:
        self.counters.parser_errors += 1
        self.error_kinds[kind] += 1
        if self._document_open:
            self.documents_aborted += 1
        self._document_open = False
        self._header.clear()
        self._payload_remaining = 0
        self._current_chunk = None
        self._magic_window.clear()
        self._seek_run_bytes = 0
        self.state = self.SEEK_MAGIC


@dataclass(frozen=True)
class CaseSpec:
    name: str
    category: str
    description: str
    data: bytes
    transfers: tuple[bytes, ...]
    expected_counters: dict[str, int]
    expected_exact: dict[str, Any] = field(default_factory=dict)
    expected_minimum: dict[str, int] = field(default_factory=dict)
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT_DIR))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_stock_types() -> tuple[dict[int, str], list[dict[str, Any]]]:
    path = ROOT_DIR / "analysis/zjs-parser-boundary/zjs-switch-table.tsv"
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            chunk_type = int(row["type"], 16)
            rows.append(
                {
                    "type": chunk_type,
                    "type_hex": f"0x{chunk_type:02x}",
                    "name": row["zjs_name"],
                    "parser_target": row["target"],
                }
            )
    return {row["type"]: row["name"] for row in rows}, rows


def probe_known_types(stock_types: dict[int, str]) -> dict[int, str]:
    return {chunk_type: stock_types[chunk_type] for chunk_type in PROBE_RECOGNIZED_TYPES}


def make_chunk(
    chunk_type: int,
    payload: bytes = b"",
    *,
    item_count: int = 0,
    reserved: int = 0,
    signature: int = CHUNK_SIGNATURE,
    declared_size: int | None = None,
) -> bytes:
    size = CHUNK_HEADER_BYTES + len(payload) if declared_size is None else declared_size
    return CHUNK_HEADER.pack(size, chunk_type, item_count, reserved, signature) + payload


def make_document(chunks: Iterable[bytes]) -> bytes:
    return MAGIC + b"".join(chunks)


def fixed_transfers(data: bytes, size: int = RECEIVE_BUFFER_BYTES) -> tuple[bytes, ...]:
    return tuple(data[offset : offset + size] for offset in range(0, len(data), size))


def split_at_offsets(data: bytes, offsets: Sequence[int]) -> tuple[bytes, ...]:
    points = [0, *offsets, len(data)]
    if points != sorted(points) or len(set(points)) != len(points):
        raise ValueError(f"split offsets must be unique and ascending: {offsets}")
    return tuple(data[start:end] for start, end in zip(points, points[1:]))


def patterned_transfers(data: bytes, pattern: Sequence[int]) -> tuple[bytes, ...]:
    if not pattern or any(size <= 0 or size > RECEIVE_BUFFER_BYTES for size in pattern):
        raise ValueError(f"invalid descriptor pattern: {pattern}")
    transfers: list[bytes] = []
    offset = 0
    pattern_index = 0
    while offset < len(data):
        size = pattern[pattern_index % len(pattern)]
        transfers.append(data[offset : offset + size])
        offset += size
        pattern_index += 1
    return tuple(transfers)


def required_expectation(
    data: bytes,
    transfers: Sequence[bytes],
    *,
    recognized: int,
    errors: int = 0,
    unknown: int = 0,
) -> dict[str, int]:
    return {
        "bytes_received": len(data),
        "receive_descriptors_completed": len(transfers),
        "recognized_chunks": recognized,
        "parser_errors": errors,
        "unknown_chunks": unknown,
    }


def inspect_complete_sample(data: bytes, known_types: dict[int, str]) -> dict[str, Any]:
    """Whole-buffer oracle independent of the streaming/ring implementation."""

    magic_offset = data.find(MAGIC)
    if magic_offset < 0:
        raise ValueError("sample has no JZJZ magic")
    position = magic_offset + len(MAGIC)
    sequence: list[int] = []
    documents = 0
    document_end = None

    while position + CHUNK_HEADER_BYTES <= len(data):
        size, chunk_type, _items, reserved, signature = CHUNK_HEADER.unpack_from(data, position)
        if size < CHUNK_HEADER_BYTES:
            raise ValueError(f"sample chunk at 0x{position:x} has invalid size {size}")
        if position + size > len(data):
            raise ValueError(f"sample chunk at 0x{position:x} is truncated")
        if signature != CHUNK_SIGNATURE:
            raise ValueError(f"sample chunk at 0x{position:x} has signature 0x{signature:04x}")
        if reserved > size - CHUNK_HEADER_BYTES:
            raise ValueError(f"sample chunk at 0x{position:x} has reserved/payload underflow")
        sequence.append(chunk_type)
        position += size
        if chunk_type == 0x01:
            documents += 1
            document_end = position
            break

    if documents != 1 or document_end is None:
        raise ValueError("sample does not contain one complete ZjStream document")
    return {
        "magic_offset": magic_offset,
        "document_bytes": document_end - magic_offset,
        "trailing_envelope_bytes": len(data) - document_end,
        "chunk_type_sequence": [f"0x{value:02x}" for value in sequence],
        "chunk_name_sequence": [known_types.get(value, f"UNKNOWN_0x{value:08x}") for value in sequence],
        "recognized_chunks": sum(value in known_types for value in sequence),
        "unknown_chunks": sum(value not in known_types for value in sequence),
        "documents": documents,
    }


def sample_cases(known_types: dict[int, str]) -> list[CaseSpec]:
    cases: list[CaseSpec] = []
    for path in sorted(SAMPLES_DIR.rglob("*.zjs")):
        data = path.read_bytes()
        transfers = fixed_transfers(data)
        oracle = inspect_complete_sample(data, known_types)
        cases.append(
            CaseSpec(
                name=f"generated::{path.stem}",
                category="generated_sample",
                description="Full checked-in host sample, including PJL envelope, in 0x400-byte descriptors.",
                source=relative(path),
                data=data,
                transfers=transfers,
                expected_counters=required_expectation(
                    data,
                    transfers,
                    recognized=oracle["recognized_chunks"],
                    unknown=oracle["unknown_chunks"],
                ),
                expected_exact={
                    "documents_completed": 1,
                    "chunk_type_sequence": [f"0x{value:02x}" for value in DAILY_SAMPLE_SEQUENCE],
                    "ring_occupancy": 0,
                },
                metadata={"sha256": sha256(data), "oracle": oracle},
            )
        )
    return cases


def synthetic_cases() -> list[CaseSpec]:
    cases: list[CaseSpec] = []
    minimal = make_document((make_chunk(0x00), make_chunk(0x01)))
    minimal_sequence = ["0x00", "0x01"]

    split_doc = make_document((make_chunk(0x00, b"header-split"), make_chunk(0x01)))
    for split in range(1, CHUNK_HEADER_BYTES):
        boundary = len(MAGIC) + split
        transfers = split_at_offsets(split_doc, (boundary,))
        cases.append(
            CaseSpec(
                name=f"header_split_{split:02d}_of_16",
                category="header_split",
                description=f"First chunk header is split after byte {split} of 16.",
                data=split_doc,
                transfers=transfers,
                expected_counters=required_expectation(split_doc, transfers, recognized=2),
                expected_exact={"documents_completed": 1, "chunk_type_sequence": minimal_sequence},
            )
        )

    for split in range(1, len(MAGIC)):
        transfers = split_at_offsets(minimal, (split,))
        cases.append(
            CaseSpec(
                name=f"magic_split_{split:02d}_of_4",
                category="header_split",
                description=f"JZJZ magic is split after byte {split} of 4.",
                data=minimal,
                transfers=transfers,
                expected_counters=required_expectation(minimal, transfers, recognized=2),
                expected_exact={"documents_completed": 1, "chunk_type_sequence": minimal_sequence},
            )
        )

    payload = bytes((index * 37 + 11) & 0xFF for index in range(257))
    payload_doc = make_document((make_chunk(0x05, payload), make_chunk(0x01)))
    payload_offsets = (
        len(MAGIC) + CHUNK_HEADER_BYTES + 1,
        len(MAGIC) + CHUNK_HEADER_BYTES + 17,
        len(MAGIC) + CHUNK_HEADER_BYTES + 129,
        len(MAGIC) + CHUNK_HEADER_BYTES + 256,
    )
    transfers = split_at_offsets(payload_doc, payload_offsets)
    cases.append(
        CaseSpec(
            name="payload_split_across_four_boundaries",
            category="payload_split",
            description="A deterministic 257-byte BID payload is split four times before END_DOC.",
            data=payload_doc,
            transfers=transfers,
            expected_counters=required_expectation(payload_doc, transfers, recognized=2),
            expected_exact={"documents_completed": 1, "chunk_type_sequence": ["0x05", "0x01"]},
        )
    )

    daily_doc = make_document(
        (
            make_chunk(0x00, bytes(12), item_count=1, reserved=12),
            make_chunk(0x02, bytes(24), item_count=2, reserved=24),
            make_chunk(0x04, bytes(range(20))),
            make_chunk(0x05, bytes((index * 13) & 0xFF for index in range(64))),
            make_chunk(0x06),
            make_chunk(0x03),
            make_chunk(0x01),
        )
    )
    transfers = (daily_doc,)
    cases.append(
        CaseSpec(
            name="multiple_chunks_single_transfer",
            category="multiple_chunks",
            description="All seven HP 1020 daily-path chunks arrive in one receive descriptor.",
            data=daily_doc,
            transfers=transfers,
            expected_counters=required_expectation(daily_doc, transfers, recognized=7),
            expected_exact={
                "documents_completed": 1,
                "chunk_type_sequence": [f"0x{value:02x}" for value in DAILY_SAMPLE_SEQUENCE],
            },
        )
    )

    all_known_sequence = (0x00, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x01)
    all_known_doc = make_document(make_chunk(chunk_type) for chunk_type in all_known_sequence)
    transfers = (all_known_doc,)
    cases.append(
        CaseSpec(
            name="stock_types_outside_probe_scope_are_unknown",
            category="known_chunks",
            description="All stock switch-table types are framed, while the narrow probe recognizes only controlled-sample types 0x00..0x06.",
            data=all_known_doc,
            transfers=transfers,
            expected_counters=required_expectation(all_known_doc, transfers, recognized=7, unknown=6),
            expected_exact={
                "documents_completed": 1,
                "chunk_type_sequence": [f"0x{value:02x}" for value in all_known_sequence],
            },
        )
    )

    empty_payload_doc = make_document(
        (make_chunk(0x00), make_chunk(0x06), make_chunk(0x03), make_chunk(0x01))
    )
    transfers = (empty_payload_doc,)
    cases.append(
        CaseSpec(
            name="valid_zero_payload_chunks",
            category="zero_length",
            description="Size 16 is valid framing and completes known chunks with zero payload bytes.",
            data=empty_payload_doc,
            transfers=transfers,
            expected_counters=required_expectation(empty_payload_doc, transfers, recognized=4),
            expected_exact={
                "documents_completed": 1,
                "chunk_type_sequence": ["0x00", "0x06", "0x03", "0x01"],
            },
        )
    )

    zero_size = MAGIC + make_chunk(0x04, declared_size=0) + minimal
    transfers = patterned_transfers(zero_size, (7, 3, 19, 5))
    cases.append(
        CaseSpec(
            name="zero_size_chunk_recovery",
            category="malformed_chunk",
            description="A declared size of zero is rejected, then the parser resynchronizes at the next JZJZ.",
            data=zero_size,
            transfers=transfers,
            expected_counters=required_expectation(zero_size, transfers, recognized=2, errors=1),
            expected_exact={
                "documents_started": 2,
                "documents_completed": 1,
                "documents_aborted": 1,
                "chunk_type_sequence": minimal_sequence,
                "error_kinds": {"chunk_size_below_header": 1},
            },
        )
    )

    oversize = MAGIC + make_chunk(0x05, declared_size=MAX_CHUNK_BYTES + 1) + minimal
    transfers = patterned_transfers(oversize, (4, 9, 2, 31))
    cases.append(
        CaseSpec(
            name="oversize_chunk_policy_recovery",
            category="malformed_chunk",
            description="A declared size above the probe's 16 MiB resource policy is rejected before payload tracking, then parsing resynchronizes.",
            data=oversize,
            transfers=transfers,
            expected_counters=required_expectation(oversize, transfers, recognized=2, errors=1),
            expected_exact={
                "documents_started": 2,
                "documents_completed": 1,
                "documents_aborted": 1,
                "chunk_type_sequence": minimal_sequence,
                "error_kinds": {"chunk_size_above_model_limit": 1},
            },
        )
    )

    bad_signature = MAGIC + make_chunk(0x00, signature=0x1234) + minimal
    transfers = patterned_transfers(bad_signature, (5, 11, 2, 23))
    cases.append(
        CaseSpec(
            name="bad_signature_recovery",
            category="malformed_chunk",
            description="A non-0x5a5a signature is rejected before a valid recovery document.",
            data=bad_signature,
            transfers=transfers,
            expected_counters=required_expectation(bad_signature, transfers, recognized=2, errors=1),
            expected_exact={
                "documents_completed": 1,
                "documents_aborted": 1,
                "error_kinds": {"bad_chunk_signature": 1},
            },
        )
    )

    reserved_underflow = MAGIC + make_chunk(0x00, b"abc", reserved=4) + minimal
    transfers = patterned_transfers(reserved_underflow, (13, 1, 17))
    cases.append(
        CaseSpec(
            name="reserved_exceeds_payload_recovery",
            category="malformed_chunk",
            description="Stock-style reserved-byte subtraction is guarded against unsigned underflow.",
            data=reserved_underflow,
            transfers=transfers,
            expected_counters=required_expectation(reserved_underflow, transfers, recognized=2, errors=1),
            expected_exact={
                "documents_completed": 1,
                "documents_aborted": 1,
                "error_kinds": {"reserved_bytes_exceed_payload": 1},
            },
        )
    )

    unknown_doc = make_document(
        (make_chunk(0x00), make_chunk(0xDEADBEEF, b"unknown-type"), make_chunk(0x01))
    )
    transfers = patterned_transfers(unknown_doc, (9, 4, 7, 31))
    cases.append(
        CaseSpec(
            name="unknown_chunk_is_counted_and_skipped",
            category="unknown_chunk",
            description="A complete type outside 0x00..0x0c is skipped without becoming a parser error.",
            data=unknown_doc,
            transfers=transfers,
            expected_counters=required_expectation(unknown_doc, transfers, recognized=2, unknown=1),
            expected_exact={
                "documents_completed": 1,
                "chunk_type_sequence": ["0x00", "0xdeadbeef", "0x01"],
            },
        )
    )

    wrap_prefix = b"P" * (RECEIVE_BUFFER_BYTES - len(MAGIC) - 2)
    wrap_data = wrap_prefix + daily_doc
    transfers = fixed_transfers(wrap_data)
    cases.append(
        CaseSpec(
            name="ring_and_descriptor_wrap_boundary",
            category="ring_wrap",
            description="The first chunk header has two bytes before the 0x400 boundary and fourteen after it.",
            data=wrap_data,
            transfers=transfers,
            expected_counters=required_expectation(wrap_data, transfers, recognized=7),
            expected_exact={
                "documents_completed": 1,
                "chunk_type_sequence": [f"0x{value:02x}" for value in DAILY_SAMPLE_SEQUENCE],
                "ring_occupancy": 0,
                "ring_peak_occupancy": RECEIVE_BUFFER_BYTES,
            },
            expected_minimum={"ring_read_wraps": 1, "ring_write_wraps": 1},
        )
    )

    payload_wrap_prefix = b"Q" * (
        RECEIVE_BUFFER_BYTES - len(MAGIC) - CHUNK_HEADER_BYTES - 4
    )
    payload_wrap_doc = make_document(
        (make_chunk(0x05, bytes((index * 29) & 0xFF for index in range(64))), make_chunk(0x01))
    )
    payload_wrap_data = payload_wrap_prefix + payload_wrap_doc
    transfers = fixed_transfers(payload_wrap_data)
    cases.append(
        CaseSpec(
            name="payload_crosses_ring_wrap_boundary",
            category="ring_wrap",
            description="A BID payload starts four bytes before the 0x400 boundary and completes after wrap.",
            data=payload_wrap_data,
            transfers=transfers,
            expected_counters=required_expectation(payload_wrap_data, transfers, recognized=2),
            expected_exact={
                "documents_completed": 1,
                "chunk_type_sequence": ["0x05", "0x01"],
                "ring_occupancy": 0,
                "ring_peak_occupancy": RECEIVE_BUFFER_BYTES,
            },
            expected_minimum={"ring_read_wraps": 1, "ring_write_wraps": 1},
        )
    )

    repeated = daily_doc + b"\x1b%-12345X@PJL EOJ\n" + daily_doc + b"gap" + daily_doc
    transfers = patterned_transfers(repeated, (1, 3, 7, 15, 31, 63, 127, 255))
    cases.append(
        CaseSpec(
            name="three_repeated_documents",
            category="repeated_documents",
            description="Three complete documents share one parser instance with deterministic envelope gaps.",
            data=repeated,
            transfers=transfers,
            expected_counters=required_expectation(repeated, transfers, recognized=21),
            expected_exact={
                "documents_started": 3,
                "documents_completed": 3,
                "documents_aborted": 0,
                "chunk_type_sequence": [
                    f"0x{value:02x}" for value in DAILY_SAMPLE_SEQUENCE * 3
                ],
            },
        )
    )

    truncated_header = MAGIC + make_chunk(0x00)[:7]
    transfers = patterned_transfers(truncated_header, (2, 4, 5))
    cases.append(
        CaseSpec(
            name="truncated_chunk_header_at_eof",
            category="malformed_chunk",
            description="Finalize reports an incomplete 16-byte chunk header.",
            data=truncated_header,
            transfers=transfers,
            expected_counters=required_expectation(truncated_header, transfers, recognized=0, errors=1),
            expected_exact={
                "documents_aborted": 1,
                "error_kinds": {"truncated_chunk_header": 1},
            },
        )
    )

    truncated_payload = MAGIC + make_chunk(0x05, bytes(12), declared_size=CHUNK_HEADER_BYTES + 100)
    transfers = patterned_transfers(truncated_payload, (4, 16, 3, 9))
    cases.append(
        CaseSpec(
            name="truncated_chunk_payload_at_eof",
            category="malformed_chunk",
            description="Finalize reports a payload shorter than the declared chunk size.",
            data=truncated_payload,
            transfers=transfers,
            expected_counters=required_expectation(truncated_payload, transfers, recognized=0, errors=1),
            expected_exact={
                "documents_aborted": 1,
                "error_kinds": {"truncated_chunk_payload": 1},
            },
        )
    )

    zero_transfers = (b"", minimal, b"")
    cases.append(
        CaseSpec(
            name="zero_byte_receive_descriptors",
            category="zero_length",
            description="Zero-byte descriptor completions affect only the descriptor counter.",
            data=minimal,
            transfers=zero_transfers,
            expected_counters=required_expectation(minimal, zero_transfers, recognized=2),
            expected_exact={"documents_completed": 1, "chunk_type_sequence": minimal_sequence},
        )
    )

    return cases


def assertion(name: str, expected: Any, actual: Any, operator: str = "eq") -> dict[str, Any]:
    if operator == "eq":
        passed = actual == expected
    elif operator == "ge":
        passed = isinstance(actual, int) and actual >= expected
    else:
        raise ValueError(f"unsupported assertion operator: {operator}")
    return {
        "name": name,
        "operator": operator,
        "expected": expected,
        "actual": actual,
        "status": "pass" if passed else "fail",
    }


def run_case(spec: CaseSpec, known_types: dict[int, str]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    parser = InertZjStreamParser(known_types)
    caught: str | None = None
    try:
        if b"".join(spec.transfers) != spec.data:
            raise ValueError("descriptor bytes do not reconstruct case input")
        for transfer in spec.transfers:
            parser.feed_descriptor(transfer)
        parser.finalize()
    except Exception as exc:  # A model exception is a deterministic test failure.
        caught = f"{type(exc).__name__}: {exc}"
    snapshot = parser.snapshot()

    if caught is not None:
        checks.append(assertion("model_exception", None, caught))
    for name, expected in spec.expected_counters.items():
        checks.append(assertion(name, expected, snapshot.get(name)))
    for name, expected in spec.expected_exact.items():
        checks.append(assertion(name, expected, snapshot.get(name)))
    for name, expected in spec.expected_minimum.items():
        checks.append(assertion(name, expected, snapshot.get(name), "ge"))
    checks.append(assertion("ring_drained", 0, snapshot["ring_occupancy"]))
    checks.append(
        assertion(
            "mechanically_inert",
            True,
            all(value == 0 for value in snapshot["side_effects"].values()),
        )
    )

    return {
        "name": spec.name,
        "category": spec.category,
        "description": spec.description,
        "source": spec.source,
        "input_bytes": len(spec.data),
        "input_sha256": sha256(spec.data),
        "transfer_lengths": [len(transfer) for transfer in spec.transfers],
        "expected_counters": spec.expected_counters,
        "actual_counters": {name: snapshot[name] for name in REQUIRED_COUNTERS},
        "parser_state": {key: value for key, value in snapshot.items() if key not in REQUIRED_COUNTERS},
        "metadata": spec.metadata,
        "assertions": checks,
        "status": "pass" if all(check["status"] == "pass" for check in checks) else "fail",
    }


def evidence_checks(
    stock_types: dict[int, str], recognized_types: dict[int, str]
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def contains(path: str, needles: Sequence[str], name: str) -> None:
        text = (ROOT_DIR / path).read_text(encoding="utf-8")
        missing = [needle for needle in needles if needle not in text]
        checks.append(
            {
                "name": name,
                "source": path,
                "detail": "all framing needles present" if not missing else f"missing: {missing}",
                "status": "pass" if not missing else "fail",
            }
        )

    contains(
        "vendor/foo2zjs-source/zjs.h",
        (
            "total record size, includes sizeof(ZJ_HEADER)",
            "WORD reserved",
            "WORD signature",
            "ZJT_START_DOC",
            "ZJT_2600N",
        ),
        "vendor_header_layout",
    )
    contains(
        "vendor/foo2zjs-source/foo2zjs.c",
        (
            "chunk.size = be32(sizeof(ZJ_HEADER) + size);",
            "chunk.signature = 0x5a5a;",
            'char\theader[4] = "JZJZ";',
        ),
        "vendor_writer_framing",
    )
    contains(
        "analysis/zjs-parser-boundary/decompiled/10009d34_hp1020_zjs_parser_entry_candidate.c",
        (
            "param_1 + 0xc",
            "uStack_70 = 0x10;",
            "uVar2 < 0xd",
            "hp1020_zjs_signature_word_candidate",
        ),
        "stock_parser_read_and_bounds_checks",
    )

    shim = json.loads(
        (ROOT_DIR / "analysis/usb-path/usb-parser-shim-contract.json").read_text(encoding="utf-8")
    )
    allocation = shim["implementation_contract"]["transfer_registration"]["buffer_allocation"]
    parser_entry = shim["implementation_contract"]["parser_boundary"]["parser_entry"]
    checks.append(
        {
            "name": "usb_shim_buffer_and_parser_contract",
            "source": "analysis/usb-path/usb-parser-shim-contract.json",
            "detail": f"buffer={allocation}, parser_entry={parser_entry}",
            "status": "pass"
            if allocation == "0x400 bytes" and parser_entry == "0x10009d34"
            else "fail",
        }
    )
    checks.append(
        {
            "name": "switch_table_matches_stock_0x00_through_0x0c",
            "source": "analysis/zjs-parser-boundary/zjs-switch-table.tsv",
            "detail": f"loaded {len(stock_types)} chunk types",
            "status": "pass" if stock_types == EXPECTED_STOCK_TYPES else "fail",
        }
    )
    checks.append(
        {
            "name": "probe_scope_matches_controlled_sample_types_0x00_through_0x06",
            "source": "analysis/samples/generated/**/*.zjs",
            "detail": f"probe recognizes {sorted(recognized_types)}",
            "status": "pass"
            if tuple(sorted(recognized_types)) == PROBE_RECOGNIZED_TYPES
            else "fail",
        }
    )
    return checks


def build_report() -> dict[str, Any]:
    stock_types, known_rows = load_stock_types()
    recognized_types = probe_known_types(stock_types)
    evidence = evidence_checks(stock_types, recognized_types)
    specs = [*sample_cases(recognized_types), *synthetic_cases()]
    results = [run_case(spec, recognized_types) for spec in specs]
    generated = [result for result in results if result["category"] == "generated_sample"]
    matrix = [result for result in results if result["category"] != "generated_sample"]
    assertions = [check for result in results for check in result["assertions"]]
    failures = [
        f"{result['name']}: {check['name']} expected {check['operator']} {check['expected']!r}, got {check['actual']!r}"
        for result in results
        for check in result["assertions"]
        if check["status"] == "fail"
    ]
    failures.extend(
        f"evidence::{check['name']}: {check['detail']}"
        for check in evidence
        if check["status"] == "fail"
    )
    if not generated:
        failures.append(f"no generated .zjs samples found below {relative(SAMPLES_DIR)}")

    aggregate = {
        name: sum(result["actual_counters"][name] for result in results)
        for name in REQUIRED_COUNTERS
    }
    status = "pass" if not failures else "fail"
    return {
        "summary": "Executable host-side model of a mechanically inert HP 1020 USB bulk/ZjStream parser.",
        "status": status,
        "scope": {
            "execution": "offline host-side only",
            "sample_glob": "analysis/samples/generated/**/*.zjs",
            "receive_buffer_bytes": RECEIVE_BUFFER_BYTES,
            "receive_descriptor_max_bytes": RECEIVE_BUFFER_BYTES,
            "mechanical_behavior": "none; payloads are length-counted and discarded",
            "hardware_access": "none; no USB device, MMIO, video, or engine path exists in this model",
        },
        "format_contract": {
            "stream_magic_ascii": MAGIC.decode("ascii"),
            "stream_magic_hex": MAGIC.hex(" "),
            "byte_order": "big-endian",
            "chunk_header_format": ">IIIHH",
            "chunk_header_bytes": CHUNK_HEADER_BYTES,
            "chunk_fields": ["total_size", "type", "item_count", "reserved", "signature"],
            "chunk_signature": f"0x{CHUNK_SIGNATURE:04x}",
            "minimum_chunk_size": CHUNK_HEADER_BYTES,
            "maximum_model_chunk_size": MAX_CHUNK_BYTES,
            "unknown_type_policy": "count and skip a completely framed chunk; do not increment parser_errors",
            "malformed_policy": "increment parser_errors, abort the active document, and scan for the next JZJZ",
            "zero_length_distinction": "a 16-byte chunk with zero payload is valid; a declared total size below 16 is malformed",
        },
        "counter_definitions": {
            "bytes_received": "Bytes delivered by completed host-side receive descriptors, including PJL envelope bytes.",
            "receive_descriptors_completed": "Every feed_descriptor call, including a zero-byte completion.",
            "recognized_chunks": "Completely received chunks whose type is in the controlled-sample probe scope 0x00..0x06.",
            "parser_errors": "Invalid or truncated framing incidents; semantic print validation is intentionally out of scope.",
            "unknown_chunks": "Completely received chunks outside the narrow probe scope, skipped without error.",
        },
        "probe_recognized_chunk_types": [
            {
                "type": chunk_type,
                "type_hex": f"0x{chunk_type:02x}",
                "name": recognized_types[chunk_type],
            }
            for chunk_type in sorted(recognized_types)
        ],
        "known_chunk_types": known_rows,
        "coverage": {
            "generated_samples_discovered": len(generated),
            "generated_samples_passed": sum(item["status"] == "pass" for item in generated),
            "synthetic_cases": len(matrix),
            "synthetic_cases_passed": sum(item["status"] == "pass" for item in matrix),
            "total_cases": len(results),
            "total_cases_passed": sum(item["status"] == "pass" for item in results),
            "assertions": len(assertions),
            "assertions_passed": sum(item["status"] == "pass" for item in assertions),
        },
        "aggregate_counters": aggregate,
        "evidence_checks": evidence,
        "generated_samples": generated,
        "test_matrix": matrix,
        "failures": failures,
    }


def render_markdown(report: dict[str, Any]) -> str:
    coverage = report["coverage"]
    lines = [
        "# HP 1020 USB Bulk Parser Draft Model",
        "",
        "This generated report executes a host-side receive-ring and ZjStream framing model. It reads checked-in files only; it does not open USB, touch MMIO, send video/engine commands, or cause mechanical activity.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- generated samples: `{coverage['generated_samples_passed']}/{coverage['generated_samples_discovered']}` passed",
        f"- synthetic matrix: `{coverage['synthetic_cases_passed']}/{coverage['synthetic_cases']}` passed",
        f"- assertions: `{coverage['assertions_passed']}/{coverage['assertions']}` passed",
        f"- receive ring/descriptor size: `0x{report['scope']['receive_buffer_bytes']:x}` bytes",
        "- hardware side effects: `0`",
        "",
        "## Framing Contract",
        "",
        "- The full host stream may contain a PJL envelope. The model scans it for big-endian `JZJZ`, matching the stock HP 1020 parser handoff boundary. The distinct XQX format is intentionally rejected.",
        "- Every chunk starts with `>IIIHH`: total size, type, item count, reserved bytes, and signature.",
        "- Total size includes the 16-byte header; the required signature is `0x5a5a`.",
        "- A size-16 chunk has a valid zero-byte payload. A declared size below 16 is malformed.",
        "- Complete types outside the controlled-sample scope `0x00..0x06` increment `unknown_chunks` and are skipped without invoking print behavior.",
        "- Malformed/truncated framing increments `parser_errors`, aborts the current document, and seeks the next stream marker.",
        "",
        "## Required Counters",
        "",
        "| Counter | Aggregate | Definition |",
        "|---|---:|---|",
    ]
    for name in REQUIRED_COUNTERS:
        lines.append(
            f"| `{name}` | `{report['aggregate_counters'][name]}` | {report['counter_definitions'][name]} |"
        )

    lines.extend(
        [
            "",
            "## Stock And Probe Chunk Types",
            "",
            "The stock table is derived from `analysis/zjs-parser-boundary/zjs-switch-table.tsv`. The inert probe deliberately recognizes only `0x00..0x06`, the types emitted by the controlled samples; other framed types are counted as unknown.",
            "",
            "| Type | Name | Stock parser target |",
            "|---:|---|---:|",
        ]
    )
    for row in report["known_chunk_types"]:
        lines.append(f"| `{row['type_hex']}` | `{row['name']}` | `{row['parser_target']}` |")

    lines.extend(
        [
            "",
            "## Generated Samples",
            "",
            "Every checked-in generated `.zjs` file is fed in complete 0x400-byte receive descriptors, including its PJL prefix and suffix.",
            "",
            "| Sample | Bytes | Descriptors | Magic | Chunks | Errors | Status |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in report["generated_samples"]:
        oracle = item["metadata"]["oracle"]
        actual = item["actual_counters"]
        lines.append(
            f"| `{item['source']}` | `{item['input_bytes']}` | `{actual['receive_descriptors_completed']}` | `0x{oracle['magic_offset']:x}` | `{actual['recognized_chunks']}` | `{actual['parser_errors']}` | `{item['status']}` |"
        )

    lines.extend(
        [
            "",
            "## Deterministic Matrix",
            "",
            "| Case | Category | Bytes | Descriptors | Recognized | Errors | Unknown | Status |",
            "|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in report["test_matrix"]:
        actual = item["actual_counters"]
        lines.append(
            f"| `{item['name']}` | `{item['category']}` | `{item['input_bytes']}` | `{actual['receive_descriptors_completed']}` | `{actual['recognized_chunks']}` | `{actual['parser_errors']}` | `{actual['unknown_chunks']}` | `{item['status']}` |"
        )

    lines.extend(
        [
            "",
            "## Evidence Checks",
            "",
            "| Check | Source | Detail | Status |",
            "|---|---|---|---|",
        ]
    )
    for item in report["evidence_checks"]:
        lines.append(
            f"| `{item['name']}` | `{item['source']}` | {item['detail']} | `{item['status']}` |"
        )

    if report["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in report["failures"])
    else:
        lines.extend(
            [
                "",
                "## Safety Boundary",
                "",
                "All cases stop after framing and counter updates. Payload bytes are never decoded into page/work objects, and no USB, MMIO, video, engine, or mechanical function exists in the executable model.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")

    coverage = report["coverage"]
    print(
        f"status={report['status']} "
        f"samples={coverage['generated_samples_passed']}/{coverage['generated_samples_discovered']} "
        f"matrix={coverage['synthetic_cases_passed']}/{coverage['synthetic_cases']} "
        f"assertions={coverage['assertions_passed']}/{coverage['assertions']}"
    )
    print(args.json_output)
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
