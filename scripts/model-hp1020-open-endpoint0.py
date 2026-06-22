#!/usr/bin/env python3
"""Model the pure endpoint-0 GET_DESCRIPTOR decision logic for HP 1020 open firmware."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DESCRIPTOR_MODEL = ROOT_DIR / "analysis/usb-path/usb-descriptor-response-model.json"
DEFAULT_JSON_OUTPUT = ROOT_DIR / "analysis/usb-path/open-endpoint0-model.json"
DEFAULT_MD_OUTPUT = ROOT_DIR / "analysis/usb-path/open-endpoint0-model.md"


@dataclass(frozen=True)
class SetupPacket:
    raw: bytes
    bm_request_type: int
    b_request: int
    w_value: int
    w_index: int
    w_length: int

    @property
    def descriptor_type(self) -> int:
        return self.w_value >> 8

    @property
    def descriptor_index(self) -> int:
        return self.w_value & 0xFF


def parse_hex(text: str) -> bytes:
    return bytes.fromhex(text)


def hexbytes(data: bytes) -> str:
    return data.hex(" ")


def parse_setup_packet(data: bytes) -> SetupPacket:
    if len(data) != 8:
        raise ValueError(f"USB setup packet must be 8 bytes, got {len(data)}")
    return SetupPacket(
        raw=data,
        bm_request_type=data[0],
        b_request=data[1],
        w_value=int.from_bytes(data[2:4], "little"),
        w_index=int.from_bytes(data[4:6], "little"),
        w_length=int.from_bytes(data[6:8], "little"),
    )


def load_descriptor_cases(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    descriptors: dict[str, Any] = {
        "device": None,
        "config_high": None,
        "config_full": None,
        "strings": {},
        "open_marker_string": None,
    }

    for case in data["cases"]:
        response = parse_hex(case["response_hex"])
        name = case["name"]
        if name == "GET_DESCRIPTOR DEVICE":
            descriptors["device"] = response
        elif name == "GET_DESCRIPTOR CONFIG high-speed-style":
            descriptors["config_high"] = response
        elif name == "GET_DESCRIPTOR CONFIG full-speed-style":
            descriptors["config_full"] = response
        elif name == "GET_DESCRIPTOR STRING index 0 language":
            descriptors["strings"][0] = response
        elif name == "GET_DESCRIPTOR STRING index 1 manufacturer":
            descriptors["strings"][1] = response
        elif name == "GET_DESCRIPTOR STRING index 2 product":
            descriptors["strings"][2] = response
        elif name == "FUTURE OPEN MARKER STRING example":
            descriptors["open_marker_string"] = response

    missing = [
        key
        for key in ("device", "config_high", "config_full", "open_marker_string")
        if descriptors[key] is None
    ]
    if missing:
        raise SystemExit(f"descriptor model missing required entries: {', '.join(missing)}")
    for index in (0, 1, 2):
        if index not in descriptors["strings"]:
            raise SystemExit(f"descriptor model missing string index {index}")
    return descriptors


def endpoint0_response(
    setup: SetupPacket,
    descriptors: dict[str, Any],
    *,
    speed: str,
    open_marker: bool,
) -> dict[str, Any]:
    if setup.bm_request_type != 0x80 or setup.b_request != 0x06:
        return {"status": "stall", "reason": "unsupported request"}

    descriptor_type = setup.descriptor_type
    descriptor_index = setup.descriptor_index
    source_name = ""
    payload: bytes | None = None

    if descriptor_type == 0x01 and descriptor_index == 0:
        source_name = "device"
        payload = descriptors["device"]
    elif descriptor_type == 0x02 and descriptor_index == 0:
        source_name = f"configuration-{speed}"
        payload = descriptors["config_high"] if speed == "high" else descriptors["config_full"]
    elif descriptor_type == 0x03:
        if descriptor_index == 2 and open_marker:
            source_name = "open-marker-product-string"
            payload = descriptors["open_marker_string"]
        else:
            source_name = f"string-{descriptor_index}"
            payload = descriptors["strings"].get(descriptor_index)

    if payload is None:
        return {
            "status": "stall",
            "reason": f"unsupported descriptor type=0x{descriptor_type:02x} index={descriptor_index}",
        }

    clipped = payload[: setup.w_length]
    return {
        "status": "data",
        "source": source_name,
        "descriptor_type": descriptor_type,
        "descriptor_index": descriptor_index,
        "requested_length": setup.w_length,
        "available_length": len(payload),
        "response_length": len(clipped),
        "response_hex": hexbytes(clipped),
    }


def sample_setups() -> list[tuple[str, str]]:
    return [
        ("device descriptor", "80 06 00 01 00 00 12 00"),
        ("config header clip", "80 06 00 02 00 00 09 00"),
        ("full config", "80 06 00 02 00 00 20 00"),
        ("language string", "80 06 00 03 00 00 04 00"),
        ("manufacturer string", "80 06 01 03 09 04 ff 00"),
        ("product string", "80 06 02 03 09 04 ff 00"),
        ("unsupported class request", "21 0a 00 00 00 00 00 00"),
    ]


def build_report(descriptors: dict[str, Any]) -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []
    for speed in ("full", "high"):
        for marker in (False, True):
            for label, setup_hex in sample_setups():
                setup = parse_setup_packet(parse_hex(setup_hex))
                result = endpoint0_response(setup, descriptors, speed=speed, open_marker=marker)
                scenarios.append(
                    {
                        "label": label,
                        "setup_hex": setup_hex,
                        "speed": speed,
                        "open_marker": marker,
                        "bm_request_type": f"0x{setup.bm_request_type:02x}",
                        "b_request": f"0x{setup.b_request:02x}",
                        "w_value": f"0x{setup.w_value:04x}",
                        "w_index": f"0x{setup.w_index:04x}",
                        "w_length": setup.w_length,
                        "result": result,
                    }
                )

    return {
        "purpose": "Pure endpoint-0 GET_DESCRIPTOR response model; excludes USB controller MMIO.",
        "hardware_scope": "none",
        "scenarios": scenarios,
        "porting_boundary": [
            "setup packet source is narrowed to 0x90021348, but live population after custom upload is unproven",
            "data-stage descriptor construction is modeled, but completion polling without ThreadX still needs live hardware confirmation",
            "engine/video MMIO remains out of scope",
            "this model is safe to run on the host only",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Open Endpoint-0 Model",
        "",
        "This is a host-side model of the pure USB control-request decision logic for a future open firmware marker.",
        "It does not touch or emulate the `0xb300....` USB controller registers.",
        "",
        "## What Is Solved",
        "",
        "- Decode an 8-byte USB setup packet.",
        "- Recognize standard `GET_DESCRIPTOR` requests.",
        "- Select stock device/config/string descriptors, or an open product-string marker.",
        "- Clip the response to host `wLength`.",
        "- Return `stall` for unsupported requests.",
        "",
        "## What Is Not Solved",
        "",
    ]
    for item in report["porting_boundary"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Scenario Matrix",
            "",
            "| Speed | Marker | Setup | Result | Bytes | Source / Reason |",
            "|---|---:|---|---|---:|---|",
        ]
    )

    for scenario in report["scenarios"]:
        result = scenario["result"]
        if result["status"] == "data":
            bytes_text = str(result["response_length"])
            source = result["source"]
        else:
            bytes_text = "0"
            source = result["reason"]
        lines.append(
            f"| `{scenario['speed']}` | `{str(scenario['open_marker']).lower()}` | "
            f"{scenario['label']} `{scenario['setup_hex']}` | `{result['status']}` | "
            f"{bytes_text} | {source} |"
        )

    lines.extend(
        [
            "",
            "## Practical Meaning",
            "",
            "The descriptor-response side is now small and deterministic enough to port to assembly later.",
            "The remaining risky work is not choosing bytes; it is proving the narrowed setup-buffer candidate is populated after upload and replacing the stock ThreadX completion wait with a safe USB polling loop.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--descriptor-model", type=Path, default=DEFAULT_DESCRIPTOR_MODEL)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()

    descriptors = load_descriptor_cases(args.descriptor_model)
    report = build_report(descriptors)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")

    data_cases = sum(1 for scenario in report["scenarios"] if scenario["result"]["status"] == "data")
    stall_cases = len(report["scenarios"]) - data_cases
    print(f"scenarios={len(report['scenarios'])} data={data_cases} stall={stall_cases}")
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
