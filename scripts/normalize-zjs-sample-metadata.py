#!/usr/bin/env python3
"""Make offline ZjStream sample metadata reproducible."""

from __future__ import annotations

import argparse
from pathlib import Path


JOBATTR_PREFIX = b'@PJL SET JOBATTR="JobAttr4='
DEFAULT_JOBATTR4 = b"20050309122739"


def normalize(path: Path, value: bytes) -> None:
    data = bytearray(path.read_bytes())
    start = data.find(JOBATTR_PREFIX)
    if start < 0:
        raise SystemExit(f"{path}: missing JobAttr4 metadata")
    timestamp_start = start + len(JOBATTR_PREFIX)
    timestamp_end = timestamp_start + len(value)
    if data[timestamp_end : timestamp_end + 1] != b'"':
        raise SystemExit(f"{path}: JobAttr4 metadata is not a 14-byte value")
    if data.find(JOBATTR_PREFIX, timestamp_end) >= 0:
        raise SystemExit(f"{path}: multiple JobAttr4 metadata fields")
    data[timestamp_start:timestamp_end] = value
    path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument(
        "--jobattr4",
        default=DEFAULT_JOBATTR4.decode("ascii"),
        help="fixed 14-digit JobAttr4 value (default: %(default)s)",
    )
    args = parser.parse_args()
    value = args.jobattr4.encode("ascii")
    if len(value) != 14 or not value.isdigit():
        raise SystemExit("--jobattr4 must contain exactly 14 ASCII digits")
    for path in args.paths:
        normalize(path, value)
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
