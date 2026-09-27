#!/usr/bin/env python3
"""Offline package, conversion and simulated installation checks. Never installs.

All system-service and USB calls in executable fixtures are replaced with local
mocks. The real Installer, CUPS scheduler and USB backend are never invoked.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import plistlib
import shutil
import stat
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("package_builder", ROOT / "scripts/build-macos-package.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def command(args, *, env=None, data=None, ok=True):
    result = subprocess.run([str(a) for a in args], input=data, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env, timeout=90)
    if ok and result.returncode:
        raise AssertionError(f"Failed {args}: {result.stderr.decode(errors='replace')[-3000:]}")
    return result


def write_script(path, contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)
    path.chmod(0o755)
    return path


def stream(data):
    """Strictly walk the actual output chunks, retaining compressed image bytes."""
    pos = data.index(b"JZJZ") + 4
    chunks = []
    while pos + 16 <= len(data):
        size, kind, count, reserved, signature = struct.unpack_from(">IIIHH", data, pos)
        assert size >= 16 and pos + size <= len(data) and signature == 0x5A5A
        payload = data[pos + 16:pos + size]
        items = {}
        cursor = 0
        for _ in range(count):
            length, ident, typ, param = struct.unpack_from(">IHBB", payload, cursor)
            assert length >= 8 and cursor + length <= len(payload)
            items[ident] = struct.unpack_from(">I", payload, cursor + 8)[0] if typ == 1 else payload[cursor + 8:cursor + length]
            cursor += length
        chunks.append((kind, items, payload))
        pos += size
        if kind == 1:
            break
    assert chunks[0][0] == 0 and chunks[-1][0] == 1
    assert sum(k == 2 for k, _, _ in chunks) == sum(k == 3 for k, _, _ in chunks) > 0
    assert any(k == 5 and body for k, _, body in chunks)
    return chunks


def raster_difference(left, right):
    def raster(path):
        with path.open("rb") as image:
            magic = image.readline().strip()
            assert magic in (b"P4", b"P5")
            line = image.readline()
            while line.startswith(b"#"):
                line = image.readline()
            dimensions = list(map(int, line.split()))
            width, height = dimensions[:2]
            if magic == b"P5":
                assert dimensions[2:] == [3]  # foo2zjs -z1 pairs two PBM bits.
            pixels = image.read()
        stride = width if magic == b"P5" else (width + 7) // 8
        assert len(pixels) == stride * height
        return magic, width, height, pixels
    magic, width, height, a = raster(left)
    magic2, w2, h2, b = raster(right)
    assert (magic, width, height) == (magic2, w2, h2)
    stride = width if magic == b"P5" else (width + 7) // 8
    changed = []
    for index, (x, y) in enumerate(zip(a, b)):
        xor = x ^ y
        if xor:
            if magic == b"P5":
                changed.append((index % stride, index // stride))
            else:
                changed.extend(((index % stride) * 8 + bit, index // stride)
                               for bit in range(8) if xor & (128 >> bit))
    def edge(pixels, x, y):
        values = {pixels[yy * stride + xx] if magic == b"P5" else bool(pixels[yy * stride + xx // 8] & (128 >> (xx % 8)))
                  for yy in range(y - 1, y + 2) for xx in range(x - 1, x + 2)}
        return len(values) > 1
    for x, y in changed:
        # Only the fixture's headings occupy these rows. Filled gray rectangle,
        # circle, whitespace, geometry and glyph interiors must remain identical.
        assert 0 < x < width - 1 and 0 < y < min(1400, height - 1)
        assert edge(a, x, y) and edge(b, x, y), (x, y)
    return {"width": width, "height": height, "different_pixels": len(changed),
            "classification": "single-pixel text edges" if changed else "identical",
            "difference_bounds": [min(x for x, y in changed), min(y for x, y in changed),
                                  max(x for x, y in changed), max(y for x, y in changed)] if changed else None}


def main(args):
    work, output = args.work.resolve(), args.output.resolve()
    payload = work / "payload"
    base = payload / builder.PREFIX.lstrip("/")
    runtime = base / "runtime/bin"
    info = json.loads((base / "build-info.json").read_text())
    checks = []
    def passed(name):
        checks.append(name)
        print(f"PASS: {name}", flush=True)

    for relative, sha in info["source_sha256"].items():
        assert builder.digest(ROOT / relative) == sha, relative
    assert builder.digest(base / "runtime/sihp1020.dl") == builder.digest(ROOT / "assets/runtime/sihp1020.dl")
    for name, meta in info["runtime"]["binaries"].items():
        assert builder.binary_audit(runtime / name) == meta
    for filename, (_, sha) in builder.ARCHIVES.items():
        assert builder.digest(base / "Sources" / filename) == sha
    assert builder.digest(base / "Sources/hp1020-package-source.tar.gz") == info["local_source_archive_sha256"]
    passed("source, original firmware, dependency archives, binary signatures and system-only linkage")

    shell_files = [p for p in payload.rglob("*") if p.is_file() and p.read_bytes()[:2] == b"#!"]
    for path in shell_files + list((ROOT / "packaging/macos/install").iterdir()) + list((ROOT / "packaging/macos/remove").iterdir()):
        shell = path.read_text().splitlines()[0][2:].split()[0]
        command([shell, "-n", path])
    plist = plistlib.loads((payload / "Library/LaunchDaemons/com.aayush.hp1020-root-spool-worker.plist").read_bytes())
    assert plist["QueueDirectories"] == ["/private/var/spool/cups/tmp/hp1020queue/ready"]
    assert stat.S_IMODE((payload / "usr/libexec/cups/backend/hp1020queue").stat().st_mode) == 0o700
    for path in shell_files:
        text = path.read_text()
        assert "/Users/aayush" not in text and "/opt/homebrew" not in text and "S43VYTP" not in text
    passed("script syntax, daemon configuration, portable paths and privileged backend permissions")

    with tempfile.TemporaryDirectory(prefix="hp1020-package-check-") as temporary:
        test = Path(temporary)
        for package in sorted(output.glob("*.pkg")):
            expanded = test / package.stem
            command(["/usr/sbin/pkgutil", "--expand-full", package, expanded])
            distribution = ET.parse(expanded / "Distribution").getroot()
            assert distribution.find("options").attrib["hostArchitectures"] == "arm64"
            components = list(expanded.glob("*.pkg"))
            assert len(components) == 1
            component = components[0]
            for name in ("preinstall", "postinstall"):
                action = "remove" if package.name.startswith("Remove") else "install"
                assert (component / "Scripts" / name).read_bytes() == (ROOT / "packaging/macos" / action / name).read_bytes()
            if action == "install":
                for path in payload.rglob("*"):
                    if path.is_file():
                        unpacked = component / "Payload" / path.relative_to(payload)
                        assert builder.digest(unpacked) == builder.digest(path), path
                bom = command(["/usr/bin/lsbom", "-p", "fmug", component / "Bom"]).stdout.decode()
                backend_row = next(row for row in bom.splitlines() if row.split()[0].endswith("/backend/hp1020queue"))
                assert backend_row.split()[1:] == ["100700", "0", "0"], backend_row
        passed("both final Installer archives expand; scripts, all payload bytes and root ownership match")

        clean_env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL": "C", "TMPDIR": str(test)}
        ps = test / "sample with spaces.ps"
        ps.write_text("%!PS-Adobe-3.0\n%%Pages: 2\n"
                      "/Helvetica findfont 20 scalefont setfont\n"
                      "72 720 moveto (HP 1020 portable package) show\n"
                      "0.3 setgray 72 500 240 90 rectfill showpage\n"
                      "0 setgray /Times-Roman findfont 16 scalefont setfont\n"
                      "72 700 moveto (Second page: 1234567890) show\n"
                      "100 300 75 0 360 arc stroke showpage\n%%EOF\n")
        pdf = test / "sample with spaces.pdf"
        command([runtime / "gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={pdf}", ps], env=clean_env)
        reference_env = dict(clean_env, PATH=f"{ROOT / 'assets/runtime'}:{runtime}:/usr/bin:/bin:/usr/sbin:/sbin",
                             GSBIN=str(runtime / "gs"))
        # Original sh wrapper does not quote a filename; feed its reference over stdin.
        cases = []
        for document in (ps, pdf):
            for paper, code, copies in (("a4", "9", "1"), ("letter", "1", "2")):
                converted = test / f"{document.suffix[1:]}-{paper}.zjs"
                command([runtime / "hp1020-convert", document, converted, paper, copies], env=clean_env)
                actual = stream(converted.read_bytes())
                reference = command([ROOT / "assets/runtime/foo2zjs-wrapper", "-P", "-z1", "-L0", f"-p{code}", f"-n{copies}"],
                                    env=reference_env, data=document.read_bytes(), ok=False)
                expected = stream(reference.stdout)
                assert actual == expected, f"Different output from original foo2zjs: {document.suffix} {paper}"
                pages = [items for kind, items, _ in actual if kind == 2]
                assert len(pages) == 2 and all(p[3] == int(code) and p[4] == int(copies) for p in pages)
                cases.append({"format": document.suffix, "paper": paper, "copies": int(copies),
                              "pages": len(pages), "sha256": builder.digest(converted)})
        passed("PDF and PostScript, two pages, A4/Letter and copies: image chunks match the original encoder")
        reference_gs = Path("/opt/homebrew/bin/gs")
        reference_comparison = False
        renderer_differences = []
        if reference_gs.exists() and command([reference_gs, "--version"]).stdout.strip() == b"10.07.0":
            decoder = test / "zjsdecode"
            foo = ROOT / "vendor/foo2zjs-source"
            command(["/usr/bin/clang", "-O2", "-I", foo, "-o", decoder,
                     foo / "zjsdecode.c", foo / "jbig.c", foo / "jbig_ar.c"])
            brew_env = dict(reference_env, GSBIN=str(reference_gs))
            for document in (ps, pdf):
                reference = command([ROOT / "assets/runtime/foo2zjs-wrapper", "-P", "-z1", "-L0", "-p9"],
                                    env=brew_env, data=document.read_bytes(), ok=False)
                actual_path = test / f"{document.suffix[1:]}-a4.zjs"
                actual, expected = stream(actual_path.read_bytes()), stream(reference.stdout)
                assert [(k, i) for k, i, _ in actual] == [(k, i) for k, i, _ in expected]
                assert [body for k, _, body in actual if k != 5] == [body for k, _, body in expected if k != 5]
                reference_path = test / f"reference-{document.suffix[1:]}.zjs"
                reference_path.write_bytes(reference.stdout)
                actual_prefix = test / f"actual-{document.suffix[1:]}"
                reference_prefix = test / f"reference-{document.suffix[1:]}"
                command([decoder, "-d", actual_prefix, actual_path])
                command([decoder, "-d", reference_prefix, reference_path])
                left = sorted(test.glob(actual_prefix.name + "-*.p?m"))
                right = sorted(test.glob(reference_prefix.name + "-*.p?m"))
                assert len(left) == len(right) == 2
                renderer_differences.extend(dict(format=document.suffix, page=i + 1, **raster_difference(a, b))
                                            for i, (a, b) in enumerate(zip(left, right)))
            reference_comparison = True
            passed("Homebrew comparison: page geometry and content match; measured differences only at single-pixel text edges")
        invalid = test / "broken.pdf"
        invalid.write_bytes(b"%PDF-1.7\nthis is deliberately invalid\n")
        assert command([runtime / "hp1020-convert", invalid, test / "broken.zjs", "a4", "1"], env=clean_env, ok=False).returncode != 0
        assert command([runtime / "hp1020-convert", ps, test / "bad-options.zjs", "a4", "0"], env=clean_env, ok=False).returncode != 0
        passed("invalid documents and invalid options fail conversion")

        # Isolated filesystem and command mocks: never run installed services.
        target = test / "target"
        shutil.copytree(payload, target)
        target_base = target / builder.PREFIX.lstrip("/")
        queue = target / "private/var/spool/cups/tmp/hp1020queue"
        mock = test / "mock-bin"
        mock.mkdir()
        calls = test / "commands.txt"
        env = dict(clean_env, MOCK_CALLS=str(calls), MOCK_TARGET=str(target))
        mock_common = '''#!/bin/zsh
print -r -- "${0:t} $*" >> "$MOCK_CALLS"
case "${0:t}" in
  id) print 0 ;;
  uname) print arm64 ;;
  lpstat)
    [[ "${MOCK_QUEUE_EXISTS:-0}" == 1 ]] || exit 1
    [[ "$1" != -o || "${MOCK_PENDING:-0}" != 1 ]] || print 'HP_LaserJet_1020_Plus-1 user 100'
    ;;
esac
exit 0
'''
        for tool in ("id", "uname", "lpstat", "chown", "lpadmin", "launchctl", "cupsaccept", "cupsenable", "cancel", "pkgutil"):
            write_script(mock / tool, mock_common)
        usb = write_script(target / "usr/libexec/cups/backend/usb", "#!/bin/sh\nexit 99\n")
        def relocated(source, destination):
            text = Path(source).read_text()
            for absolute in ("/Library/Printers/hp1020", "/Library/LaunchDaemons/com.aayush.hp1020-root-spool-worker.plist",
                             "/private/var/spool/cups/tmp/hp1020queue", "/usr/libexec/cups/backend/hp1020queue",
                             "/usr/libexec/cups/filter/hp1020passthrough", "/usr/libexec/cups/backend/usb"):
                text = text.replace(absolute, str(target / absolute.lstrip("/")))
            text = text.replace("export PATH=/usr/bin:/bin:/usr/sbin:/sbin", f'export PATH="{mock}:/usr/bin:/bin:/usr/sbin:/sbin"')
            assert 'USB_BACKEND="/usr/' not in text
            return write_script(destination, text)
        scripts = {}
        for action in ("install", "remove"):
            for name in ("preinstall", "postinstall"):
                scripts[action, name] = relocated(ROOT / "packaging/macos" / action / name, test / f"{action}-{name}")
        # Reject the legacy setup, then test a genuinely empty destination.
        marker = target_base / "package-version"
        marker.unlink()
        assert command([scripts["install", "preinstall"], "pkg", "/", "/"], env=env, ok=False).returncode != 0
        held = test / "held-payload"
        target_base.rename(held)
        cup_files = ("usr/libexec/cups/backend/hp1020queue", "usr/libexec/cups/filter/hp1020passthrough")
        for name in cup_files:
            (target / name).unlink()
        command([scripts["install", "preinstall"], "pkg", "/", "/"], env=env)
        assert command([scripts["install", "preinstall"], "pkg", "/", "/"], env=dict(env, MOCK_QUEUE_EXISTS="1"), ok=False).returncode != 0
        held.rename(target_base)
        for name in cup_files:
            shutil.copy2(payload / name, target / name)
        marker.write_text(builder.VERSION + "\n")
        command([scripts["install", "preinstall"], "pkg", "/", "/"], env=env)
        command([scripts["install", "postinstall"], "pkg", "/", "/"], env=env)
        assert stat.S_IMODE(queue.stat().st_mode) == 0o700
        assert "-o printer-is-shared=false" in calls.read_text()
        assert "usb" not in calls.read_text()
        assert command([scripts["install", "preinstall"], "pkg", "/", "/Volumes/Other"], env=env, ok=False).returncode != 0
        pending_env = dict(env, MOCK_QUEUE_EXISTS="1", MOCK_PENDING="1")
        assert command([scripts["install", "preinstall"], "pkg", "/", "/"], env=pending_env, ok=False).returncode != 0
        passed("simulated installation, private spool, manual-install conflict and pending-job/other-volume guards")

        backend = relocated(ROOT / "packaging/macos/hp1020queue", test / "backend")
        worker = relocated(ROOT / "packaging/macos/hp1020-root-spool-worker", test / "worker")
        received = test / "received"
        print_calls = test / "print-calls"
        env.update(MOCK_RECEIVED=str(received), MOCK_PRINT_CALLS=str(print_calls))
        write_script(target_base / "hp1020-print", '''#!/bin/zsh
printf '%s %s\n' "$2" "$3" >> "$MOCK_PRINT_CALLS"
cp "$1" "$MOCK_RECEIVED"
exit ${MOCK_PRINT_EXIT:-0}
''')
        command([worker], env=env)
        assert not print_calls.exists()
        command([backend, "17", "dad", "ordinary title", "2", "PageSize=Letter", ps], env=env)
        command([worker], env=env)
        assert received.read_bytes() == ps.read_bytes() and print_calls.read_text() == "letter 2\n"
        assert not list((queue / "ready").iterdir()) and not list((queue / "processing").iterdir())
        # Incomplete stdin is not visible to the daemon.
        process = subprocess.Popen([str(backend), "18", "dad", "$(touch ignored)", "1", "PageSize=A4"],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        process.stdin.write(b"partial document\n")
        process.stdin.flush()
        assert not list((queue / "ready").iterdir())
        process.stdin.close()
        assert process.wait(timeout=10) == 0
        command([worker], env=dict(env, MOCK_PRINT_EXIT="1"))
        failed = list((queue / "failed").iterdir())
        assert len(failed) == 1 and (failed[0] / "document").read_bytes() == b"partial document\n"
        old_calls = print_calls.read_bytes()
        command([worker], env=env)
        assert print_calls.read_bytes() == old_calls
        interrupted = queue / "processing/interrupted"
        interrupted.mkdir()
        command([worker], env=env)
        assert interrupted.exists() and print_calls.read_bytes() == old_calls
        assert command([scripts["install", "preinstall"], "pkg", "/", "/"], env=env, ok=False).returncode != 0
        passed("job bytes and options, atomic publication, successful cleanup and no automatic failed/interrupted retries")

        # Execute the real print orchestration only against this fake USB backend.
        usb_calls = test / "usb-calls"
        env["MOCK_USB_CALLS"] = str(usb_calls)
        write_script(usb, '''#!/bin/zsh
print -r -- "${DEVICE_URI:-discovery} $# $*" >> "$MOCK_USB_CALLS"
if [[ $# == 0 ]]; then
  case "${MOCK_USB_MODE:-one}" in
    one) print 'direct usb://Hewlett-Packard/HP%20LaserJet%201020?serial=FAMILY "HP"' ;;
    two) print 'direct usb://Hewlett-Packard/HP%20LaserJet%201020?serial=ONE "HP"'; print 'direct usb://Hewlett-Packard/HP%20LaserJet%201020?serial=TWO "HP"' ;;
  esac
fi
exit 0
''')
        printer = relocated(ROOT / "packaging/macos/hp1020-print", test / "printer")
        command([printer, ps, "a4", "1"], env=env)
        records = usb_calls.read_text().splitlines()
        assert len(records) == 3 and 'serial=FAMILY 6 1 root HP 1020 firmware' in records[1]
        assert 'serial=FAMILY 6 2 root HP 1020 document' in records[2]
        for mode in ("none", "two"):
            usb_calls.unlink()
            assert command([printer, ps, "a4", "1"], env=dict(env, MOCK_USB_MODE=mode), ok=False).returncode != 0
            assert len(usb_calls.read_text().splitlines()) == 1
        usb_calls.unlink()
        assert command([printer, invalid, "a4", "1"], env=env, ok=False).returncode != 0
        assert not usb_calls.exists()
        passed("mock USB discovery, firmware/document ordering, ambiguous/disconnected rejection and no USB after conversion failure")

        unrelated = target / "Library/Printers/Unrelated/keep"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("untouched")
        command([scripts["remove", "preinstall"], "pkg", "/", "/"], env=env)
        command([scripts["remove", "postinstall"], "pkg", "/", "/"], env=env)
        assert not target_base.exists() and not queue.exists() and unrelated.read_text() == "untouched"
        assert not usb_calls.exists()
        passed("simulated removal affects only this package and contacts no USB backend")

    report = {"checks_passed": checks, "count": len(checks), "conversion_cases": cases,
              "compared_existing_homebrew_renderer": reference_comparison,
              "renderer_differences": renderer_differences,
              "packages": {p.name: builder.digest(p) for p in sorted(output.glob("*.pkg"))},
              "source_sha256": {str(p.relative_to(ROOT)): builder.digest(p) for p in builder.source_files()},
              "host_macos": command(["/usr/bin/sw_vers", "-productVersion"]).stdout.decode().strip(),
              "actual_installation": False, "printer_contact": False, "physical_print_test": False}
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "packaging/macos/validation-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"All {len(checks)} offline package checks passed. No installation or printer contact.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=ROOT / ".build/macos-package")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/HP-LaserJet-1020-Plus")
    main(parser.parse_args())
