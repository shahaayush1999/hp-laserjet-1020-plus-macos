#!/usr/bin/env python3
"""Wrap an HP 1020 date-prefixed firmware image in the ACL/PJL upload envelope."""

from __future__ import annotations

import argparse
from pathlib import Path


UEL = b"\x1b%-12345X"
PJL_ENTER_ACL = UEL + b"@PJL ENTER LANGUAGE=ACL\r\n"
ACL_MAGIC = bytes.fromhex("00 ac c0 de")


def wrap_image(image: bytes) -> bytes:
    if len(image) < 12:
        raise ValueError("image is too small to contain date prefix plus ELF header")
    if image[8:12] != b"\x7fELF":
        raise ValueError("expected date-prefixed image: bytes 8..11 must be ELF magic")

    elf_length = len(image) - 8
    return PJL_ENTER_ACL + ACL_MAGIC + elf_length.to_bytes(4, "big") + image + UEL


def inspect_upload(upload: bytes) -> str:
    lines = []
    lines.append(f"total_bytes={len(upload)}")
    if not upload.startswith(PJL_ENTER_ACL):
        lines.append("prefix=unexpected")
        return "\n".join(lines)

    header_offset = len(PJL_ENTER_ACL)
    image_offset = header_offset + 8
    magic = upload[header_offset : header_offset + 4]
    length = int.from_bytes(upload[header_offset + 4 : header_offset + 8], "big")
    trailer = upload[-len(UEL) :]
    image_length = len(upload) - image_offset - len(UEL)

    lines.append(f"pjl_prefix_bytes={len(PJL_ENTER_ACL)}")
    lines.append(f"acl_magic={magic.hex()}")
    lines.append(f"acl_elf_length={length}")
    lines.append(f"image_offset={image_offset}")
    lines.append(f"image_length={image_length}")
    lines.append(f"trailer={trailer.hex()}")
    if image_length >= 12:
        lines.append(f"date_prefix={upload[image_offset:image_offset + 8].decode('ascii', errors='replace')}")
        lines.append(f"elf_magic={upload[image_offset + 8:image_offset + 12].hex()}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="date-prefixed .img file, or .dl file with --inspect")
    parser.add_argument("output", type=Path, nargs="?", help="output .dl file")
    parser.add_argument("--inspect", action="store_true", help="inspect an existing .dl wrapper instead of writing one")
    args = parser.parse_args()

    data = args.input.read_bytes()
    if args.inspect:
        print(inspect_upload(data))
        return 0

    if args.output is None:
        parser.error("output is required unless --inspect is used")

    args.output.write_bytes(wrap_image(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
