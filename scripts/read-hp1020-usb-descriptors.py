#!/usr/bin/env python3
"""Read HP 1020 USB descriptors through libusb control transfers."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import json
from pathlib import Path
from typing import Any


DEFAULT_VENDOR_ID = 0x03F0
DEFAULT_PRODUCT_ID = 0x2B17
USB_DT_DEVICE = 0x01
USB_DT_CONFIG = 0x02
USB_DT_STRING = 0x03
LIBUSB_ENDPOINT_IN = 0x80
LIBUSB_REQUEST_GET_DESCRIPTOR = 0x06


class LibusbDeviceDescriptor(ctypes.Structure):
    _fields_ = [
        ("bLength", ctypes.c_uint8),
        ("bDescriptorType", ctypes.c_uint8),
        ("bcdUSB", ctypes.c_uint16),
        ("bDeviceClass", ctypes.c_uint8),
        ("bDeviceSubClass", ctypes.c_uint8),
        ("bDeviceProtocol", ctypes.c_uint8),
        ("bMaxPacketSize0", ctypes.c_uint8),
        ("idVendor", ctypes.c_uint16),
        ("idProduct", ctypes.c_uint16),
        ("bcdDevice", ctypes.c_uint16),
        ("iManufacturer", ctypes.c_uint8),
        ("iProduct", ctypes.c_uint8),
        ("iSerialNumber", ctypes.c_uint8),
        ("bNumConfigurations", ctypes.c_uint8),
    ]


def load_libusb(path: str | None = None) -> ctypes.CDLL:
    candidates = []
    if path:
        candidates.append(path)
    found = ctypes.util.find_library("usb-1.0")
    if found:
        candidates.append(found)
    candidates.extend(
        [
            "/opt/homebrew/lib/libusb-1.0.dylib",
            "/opt/homebrew/opt/libusb/lib/libusb-1.0.dylib",
            "/usr/local/lib/libusb-1.0.dylib",
            "/usr/local/opt/libusb/lib/libusb-1.0.dylib",
        ]
    )

    errors = []
    for candidate in candidates:
        try:
            lib = ctypes.CDLL(candidate)
            configure_libusb(lib)
            return lib
        except OSError as exc:
            errors.append(f"{candidate}: {exc}")
    raise RuntimeError("libusb-1.0 not found; tried " + "; ".join(errors))


def configure_libusb(lib: ctypes.CDLL) -> None:
    lib.libusb_init.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    lib.libusb_init.restype = ctypes.c_int
    lib.libusb_exit.argtypes = [ctypes.c_void_p]
    lib.libusb_exit.restype = None
    lib.libusb_get_device_list.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))]
    lib.libusb_get_device_list.restype = ctypes.c_ssize_t
    lib.libusb_free_device_list.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
    lib.libusb_free_device_list.restype = None
    lib.libusb_get_device_descriptor.argtypes = [ctypes.c_void_p, ctypes.POINTER(LibusbDeviceDescriptor)]
    lib.libusb_get_device_descriptor.restype = ctypes.c_int
    lib.libusb_open.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.libusb_open.restype = ctypes.c_int
    lib.libusb_close.argtypes = [ctypes.c_void_p]
    lib.libusb_close.restype = None
    lib.libusb_get_bus_number.argtypes = [ctypes.c_void_p]
    lib.libusb_get_bus_number.restype = ctypes.c_uint8
    lib.libusb_get_device_address.argtypes = [ctypes.c_void_p]
    lib.libusb_get_device_address.restype = ctypes.c_uint8
    lib.libusb_control_transfer.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint8,
        ctypes.c_uint8,
        ctypes.c_uint16,
        ctypes.c_uint16,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_uint16,
        ctypes.c_uint,
    ]
    lib.libusb_control_transfer.restype = ctypes.c_int


def hex_bytes(data: bytes) -> str:
    return " ".join(f"{byte:02x}" for byte in data)


def decode_usb_string(data: bytes) -> str:
    if len(data) < 2 or data[1] != USB_DT_STRING:
        return ""
    payload = data[2 : data[0] if data and data[0] <= len(data) else len(data)]
    try:
        return payload.decode("utf-16-le", errors="replace")
    except UnicodeDecodeError:
        return ""


def control_get_descriptor(
    lib: ctypes.CDLL,
    handle: ctypes.c_void_p,
    descriptor_type: int,
    descriptor_index: int,
    *,
    lang_id: int = 0,
    length: int = 255,
    timeout_ms: int = 1000,
) -> dict[str, Any]:
    buf = (ctypes.c_ubyte * length)()
    rc = lib.libusb_control_transfer(
        handle,
        LIBUSB_ENDPOINT_IN,
        LIBUSB_REQUEST_GET_DESCRIPTOR,
        (descriptor_type << 8) | descriptor_index,
        lang_id,
        buf,
        length,
        timeout_ms,
    )
    if rc < 0:
        return {
            "ok": False,
            "descriptor_type": descriptor_type,
            "descriptor_index": descriptor_index,
            "lang_id": f"0x{lang_id:04x}",
            "libusb_status": rc,
            "data_hex": "",
        }
    data = bytes(buf[:rc])
    item: dict[str, Any] = {
        "ok": True,
        "descriptor_type": descriptor_type,
        "descriptor_index": descriptor_index,
        "lang_id": f"0x{lang_id:04x}",
        "length": rc,
        "data_hex": hex_bytes(data),
    }
    if descriptor_type == USB_DT_STRING:
        item["text"] = decode_usb_string(data)
    return item


def descriptor_to_dict(desc: LibusbDeviceDescriptor) -> dict[str, Any]:
    return {
        "bcdUSB": f"0x{desc.bcdUSB:04x}",
        "idVendor": f"0x{desc.idVendor:04x}",
        "idProduct": f"0x{desc.idProduct:04x}",
        "bcdDevice": f"0x{desc.bcdDevice:04x}",
        "bMaxPacketSize0": desc.bMaxPacketSize0,
        "iManufacturer": desc.iManufacturer,
        "iProduct": desc.iProduct,
        "iSerialNumber": desc.iSerialNumber,
        "bNumConfigurations": desc.bNumConfigurations,
    }


def read_one_device(
    lib: ctypes.CDLL,
    dev: ctypes.c_void_p,
    cached_desc: LibusbDeviceDescriptor,
    *,
    timeout_ms: int,
) -> dict[str, Any]:
    handle = ctypes.c_void_p()
    rc = lib.libusb_open(dev, ctypes.byref(handle))
    report: dict[str, Any] = {
        "bus": int(lib.libusb_get_bus_number(dev)),
        "address": int(lib.libusb_get_device_address(dev)),
        "cached_device_descriptor": descriptor_to_dict(cached_desc),
        "open_status": rc,
        "control_reads": [],
    }
    if rc != 0:
        report["verdict"] = "open_failed"
        return report

    try:
        product_index = cached_desc.iProduct or 2
        manufacturer_index = cached_desc.iManufacturer
        serial_index = cached_desc.iSerialNumber
        if product_index:
            report["control_reads"].append(
                {
                    "name": "product_first",
                    **control_get_descriptor(
                        lib,
                        handle,
                        USB_DT_STRING,
                        product_index,
                        lang_id=0x0409,
                        length=255,
                        timeout_ms=timeout_ms,
                    ),
                }
            )
        device = control_get_descriptor(
            lib,
            handle,
            USB_DT_DEVICE,
            0,
            length=18,
            timeout_ms=timeout_ms,
        )
        report["control_reads"].append({"name": "device", **device})
        if device.get("ok"):
            raw = bytes.fromhex(device["data_hex"])
            if len(raw) >= 17:
                manufacturer_index = raw[14]
                product_index = raw[15]
                serial_index = raw[16]

        report["control_reads"].append(
            {
                "name": "configuration_header",
                **control_get_descriptor(
                    lib,
                    handle,
                    USB_DT_CONFIG,
                    0,
                    length=9,
                    timeout_ms=timeout_ms,
                ),
            }
        )
        report["control_reads"].append(
            {
                "name": "configuration_full",
                **control_get_descriptor(
                    lib,
                    handle,
                    USB_DT_CONFIG,
                    0,
                    length=64,
                    timeout_ms=timeout_ms,
                ),
            }
        )
        lang = control_get_descriptor(
            lib,
            handle,
            USB_DT_STRING,
            0,
            length=4,
            timeout_ms=timeout_ms,
        )
        report["control_reads"].append({"name": "language", **lang})
        lang_id = 0x0409
        if lang.get("ok"):
            raw = bytes.fromhex(lang["data_hex"])
            if len(raw) >= 4:
                lang_id = raw[2] | (raw[3] << 8)

        for name, index in (
            ("manufacturer", manufacturer_index),
            ("product", product_index),
            ("serial", serial_index),
        ):
            if index:
                report["control_reads"].append(
                    {
                        "name": name,
                        **control_get_descriptor(
                            lib,
                            handle,
                            USB_DT_STRING,
                            index,
                            lang_id=lang_id,
                            length=255,
                            timeout_ms=timeout_ms,
                        ),
                    }
                )
            else:
                report["control_reads"].append(
                    {
                        "name": name,
                        "ok": False,
                        "descriptor_type": USB_DT_STRING,
                        "descriptor_index": 0,
                        "lang_id": f"0x{lang_id:04x}",
                        "skipped": True,
                        "reason": "device descriptor index is zero",
                    }
                )
    finally:
        lib.libusb_close(handle)

    texts = [
        item.get("text", "")
        for item in report["control_reads"]
        if item.get("ok") and item.get("descriptor_type") == USB_DT_STRING
    ]
    report["string_texts"] = texts
    if any("HP1020 OPEN MARKER" in text or text.startswith("HP1020 B=") for text in texts):
        report["verdict"] = "marker_product_seen"
    elif any(item.get("ok") for item in report["control_reads"]):
        report["verdict"] = "descriptors_read_no_marker"
    else:
        report["verdict"] = "descriptor_read_failed"
    return report


def read_descriptors(vendor_id: int, product_id: int, *, libusb_path: str | None, timeout_ms: int) -> dict[str, Any]:
    try:
        lib = load_libusb(libusb_path)
    except Exception as exc:
        return {
            "status": "libusb_unavailable",
            "vendor_id": f"0x{vendor_id:04x}",
            "product_id": f"0x{product_id:04x}",
            "error": str(exc),
            "devices": [],
        }

    ctx = ctypes.c_void_p()
    rc = lib.libusb_init(ctypes.byref(ctx))
    if rc != 0:
        return {
            "status": "libusb_init_failed",
            "vendor_id": f"0x{vendor_id:04x}",
            "product_id": f"0x{product_id:04x}",
            "libusb_status": rc,
            "devices": [],
        }

    devs = ctypes.POINTER(ctypes.c_void_p)()
    reports: list[dict[str, Any]] = []
    try:
        count = lib.libusb_get_device_list(ctx, ctypes.byref(devs))
        if count < 0:
            return {
                "status": "device_list_failed",
                "vendor_id": f"0x{vendor_id:04x}",
                "product_id": f"0x{product_id:04x}",
                "libusb_status": int(count),
                "devices": [],
            }
        for idx in range(count):
            dev = devs[idx]
            desc = LibusbDeviceDescriptor()
            rc = lib.libusb_get_device_descriptor(dev, ctypes.byref(desc))
            if rc != 0:
                continue
            if desc.idVendor == vendor_id and desc.idProduct == product_id:
                reports.append(read_one_device(lib, dev, desc, timeout_ms=timeout_ms))
    finally:
        if devs:
            lib.libusb_free_device_list(devs, 1)
        lib.libusb_exit(ctx)

    verdicts = {device.get("verdict") for device in reports}
    if "marker_product_seen" in verdicts:
        status = "marker_product_seen"
    elif reports:
        status = "matching_device_no_marker"
    else:
        status = "no_matching_device"
    return {
        "status": status,
        "vendor_id": f"0x{vendor_id:04x}",
        "product_id": f"0x{product_id:04x}",
        "devices": reports,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Direct USB Descriptor Read",
        "",
        "This uses standard USB control-IN GET_DESCRIPTOR requests through libusb.",
        "It does not send print data, engine commands, video data, or PJL.",
        "",
        f"- status: `{report.get('status')}`",
        f"- target VID:PID: `{report.get('vendor_id')}:{report.get('product_id')}`",
        f"- matching devices: `{len(report.get('devices', []))}`",
    ]
    if report.get("error"):
        lines.append(f"- error: `{report['error']}`")
    lines.extend(["", "## Devices", ""])
    if not report.get("devices"):
        lines.append("- none")
    for device in report.get("devices", []):
        cached = device.get("cached_device_descriptor", {})
        lines.append(
            f"- bus=`{device.get('bus')}` address=`{device.get('address')}` "
            f"open_status=`{device.get('open_status')}` verdict=`{device.get('verdict')}` "
            f"cached_product_index=`{cached.get('iProduct')}`"
        )
        for item in device.get("control_reads", []):
            text = f" text=`{item.get('text')}`" if item.get("text") else ""
            status = "ok" if item.get("ok") else f"fail {item.get('libusb_status', item.get('reason', ''))}"
            lines.append(
                f"  - `{item.get('name')}` {status} type=`{item.get('descriptor_type')}` "
                f"index=`{item.get('descriptor_index')}` bytes=`{item.get('length', 0)}`{text}"
            )
    return "\n".join(lines) + "\n"


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor-id", type=parse_int, default=DEFAULT_VENDOR_ID)
    parser.add_argument("--product-id", type=parse_int, default=DEFAULT_PRODUCT_ID)
    parser.add_argument("--libusb", help="path to libusb-1.0 dylib")
    parser.add_argument("--timeout-ms", type=int, default=1000)
    parser.add_argument("-o", "--output", type=Path, help="write markdown report")
    parser.add_argument("--json", type=Path, help="write JSON report")
    parser.add_argument("--strict", action="store_true", help="exit non-zero unless the marker string is seen")
    args = parser.parse_args()

    report = read_descriptors(
        args.vendor_id,
        args.product_id,
        libusb_path=args.libusb,
        timeout_ms=args.timeout_ms,
    )
    text = render_markdown(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    if args.strict and report.get("status") != "marker_product_seen":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
