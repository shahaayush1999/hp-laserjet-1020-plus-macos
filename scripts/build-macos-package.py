#!/usr/bin/env python3
"""Build a private, self-contained Apple Silicon installer without installing it.

Build tools: macOS, Xcode command-line tools, Python 3. No Homebrew required.
The output includes the pinned dependency archives and corresponding local source.
"""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "packaging/macos"
VERSION = "1.0.0"
INSTALLER_NAME = f"HP-LaserJet-1020-Plus-{VERSION}-Apple-Silicon.pkg"
REMOVER_NAME = "Remove-HP-LaserJet-1020-Plus.pkg"
DISK_IMAGE_NAME = f"HP-LaserJet-1020-Plus-{VERSION}-Apple-Silicon.dmg"
IDENTIFIER = "com.aayush.hp1020.driver"
PREFIX = "/Library/Printers/hp1020"
ARCHIVES = {
    "ghostpdl-10.07.0.tar.xz": (
        "https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10070/ghostpdl-10.07.0.tar.xz",
        "ba1366006a93b91e615f74aad9c0905fae503d3f5b04078ce2ddbe360bd2f9df",
    ),
    "sed-4.10.tar.xz": (
        "https://ftp.gnu.org/gnu/sed/sed-4.10.tar.xz",
        "b8e72182b2ec96a3574e2998c47b7aaa64cc20ce000d8e9ac313cc07cecf28c7",
    ),
}
GS_CONFIGURE = [
    f"--prefix={PREFIX}/runtime", "--disable-cups", "--disable-gtk",
    "--disable-dbus", "--disable-fontconfig", "--without-tesseract",
    "--without-libidn", "--without-libpaper", "--without-x",
    "--without-pdftoraster", "--without-ijs", "--without-urf",
    "--with-drivers=pbmraw,pgmraw,png16m,pdfwrite", "--without-versioned-path",
]
SED_CONFIGURE = [
    f"--prefix={PREFIX}/runtime", "--program-prefix=g", "--disable-nls",
    "--disable-dependency-tracking",
]
FLAGS = "-O2 -arch arm64 -mmacosx-version-min=11.0"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(args, *, cwd=None, env=None, log=None):
    if log:
        with Path(log).open("w") as out:
            subprocess.run([str(x) for x in args], cwd=cwd, env=env,
                           stdout=out, stderr=subprocess.STDOUT, check=True)
    else:
        subprocess.run([str(x) for x in args], cwd=cwd, env=env, check=True)


def copy(source, dest, mode=0o644):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    dest.chmod(mode)


def sources(cache):
    cache.mkdir(parents=True, exist_ok=True)
    for name, (url, sha) in ARCHIVES.items():
        path = cache / name
        if not path.exists():
            partial = cache / (name + ".part")
            run(["/usr/bin/curl", "--fail", "--location", "--retry", "2",
                 "--connect-timeout", "20", "--output", partial, url])
            if digest(partial) != sha:
                raise RuntimeError(f"Checksum mismatch: {partial}")
            partial.replace(path)
        if digest(path) != sha:
            raise RuntimeError(f"Checksum mismatch: {path}; refusing to build")


def extract(cache, work, name):
    directory = work / name.removesuffix(".tar.xz")
    stamp = directory / ".hp1020-source-sha256"
    expected = ARCHIVES[name][1]
    if not stamp.exists() or stamp.read_text().strip() != expected:
        # Only these two fixed, disposable build directories are replaced.
        if directory.exists():
            shutil.rmtree(directory)
        run(["/usr/bin/tar", "-xf", cache / name, "-C", work])
        stamp.write_text(expected + "\n")
    return directory


def binary_audit(path):
    arch = subprocess.check_output(["/usr/bin/lipo", "-archs", path], text=True).strip()
    if arch != "arm64":
        raise RuntimeError(f"Unexpected architecture for {path}: {arch}")
    libraries = subprocess.check_output(["/usr/bin/otool", "-L", path], text=True)
    for line in libraries.splitlines()[1:]:
        dep = line.strip().split(" (", 1)[0]
        if not (dep.startswith("/usr/lib/") or dep.startswith("/System/Library/")):
            raise RuntimeError(f"Non-system dependency: {path}: {dep}")
    load_commands = subprocess.check_output(["/usr/bin/otool", "-l", path], text=True)
    if "minos 11.0" not in load_commands:
        raise RuntimeError(f"Unexpected deployment target for {path}")
    run(["/usr/bin/codesign", "--verify", "--strict", path])
    return {"sha256": digest(path), "architecture": arch, "minimum_macos": "11.0",
            "libraries": libraries.splitlines()[1:]}


def build_runtime(work, cache, jobs, reuse):
    runtime = work / "runtime-binaries"
    stamp = runtime / "build.json"
    foo_files = [ROOT / "vendor/foo2zjs-source" / name for name in
                 ("foo2zjs.c", "zjs.h", "jbig.c", "jbig.h", "jbig_ar.c", "jbig_ar.h")]
    inputs = {str(p.relative_to(ROOT)): digest(p) for p in foo_files}
    recipe = {"archives": ARCHIVES, "flags": FLAGS, "gs": GS_CONFIGURE,
              "sed": SED_CONFIGURE, "foo2zjs": inputs}
    recipe = json.loads(json.dumps(recipe))
    if reuse:
        saved = json.loads(stamp.read_text())
        if saved["recipe"] != recipe:
            raise RuntimeError("Cached runtime recipe changed; rebuild without --reuse-runtime")
        for name, metadata in saved["binaries"].items():
            if binary_audit(runtime / name) != metadata:
                raise RuntimeError(f"Cached runtime changed: {name}")
        return runtime, saved
    gs = extract(cache, work, "ghostpdl-10.07.0.tar.xz")
    sed = extract(cache, work, "sed-4.10.tar.xz")
    env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
           "MACOSX_DEPLOYMENT_TARGET": "11.0", "CC": "/usr/bin/clang",
           "CXX": "/usr/bin/clang++", "CFLAGS": FLAGS, "CXXFLAGS": FLAGS,
           "LC_ALL": "C", "TMPDIR": str(work / "tmp")}
    Path(env["TMPDIR"]).mkdir(exist_ok=True)
    print("Building Ghostscript from the verified source archive...", flush=True)
    run(["./configure", *GS_CONFIGURE], cwd=gs, env=env, log=work / "gs-configure.log")
    run(["/usr/bin/make", f"-j{jobs}", "gs"], cwd=gs, env=env, log=work / "gs-build.log")
    print("Building GNU sed and foo2zjs...", flush=True)
    run(["./configure", *SED_CONFIGURE], cwd=sed, env=env, log=work / "sed-configure.log")
    run(["/usr/bin/make", f"-j{jobs}"], cwd=sed, env=env, log=work / "sed-build.log")
    runtime.mkdir(exist_ok=True)
    copy(gs / "bin/gs", runtime / "gs", 0o755)
    copy(sed / "sed/sed", runtime / "gsed", 0o755)
    foo = ROOT / "vendor/foo2zjs-source"
    run(["/usr/bin/clang", *FLAGS.split(), "-I", foo, "-o", runtime / "foo2zjs",
         foo / "foo2zjs.c", foo / "jbig.c", foo / "jbig_ar.c"], env=env,
        log=work / "foo2zjs-build.log")
    metadata = {}
    for name in ("gs", "gsed", "foo2zjs"):
        run(["/usr/bin/codesign", "--force", "--sign", "-", runtime / name])
        metadata[name] = binary_audit(runtime / name)
    saved = {"recipe": recipe, "binaries": metadata}
    stamp.write_text(json.dumps(saved, indent=2) + "\n")
    return runtime, saved


def patched_wrapper():
    original = (ROOT / "assets/runtime/foo2zjs-wrapper").read_text()
    # Preserve conversion flags and algorithms. Propagate pipeline failures,
    # and accept a document filename containing spaces.
    edits = [
        ("#!/bin/sh\n", "#!/bin/bash\nset -o pipefail\n"),
        ("exec < $1", 'exec < "$1"'),
        ("#\n#\tLog the command line, for debugging and problem reports\n#\nif [ -x /usr/bin/logger ]; then",
         "pipeline_status=$?\n[ \"$pipeline_status\" -eq 0 ] || exit \"$pipeline_status\"\n\n"
         "#\n#\tLog the command line, for debugging and problem reports\n#\nif [ -x /usr/bin/logger ]; then"),
    ]
    for before, after in edits:
        if original.count(before) != 1:
            raise RuntimeError(f"Unexpected foo2zjs wrapper content: {before!r}")
        original = original.replace(before, after)
    # The original cleanup's last test can return 1 after successful conversion.
    return original + "\nexit 0\n"


def source_files():
    files = set()
    for folder in ("packaging/macos", "assets/runtime", "assets/licenses", "vendor/foo2zjs-source"):
        files.update(p for p in (ROOT / folder).rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.name != "validation-report.json")
    for name in ("scripts/build-macos-package.py", "scripts/validate-macos-package.py",
                 "scripts/inspect-zjs-stream.py", "files/cups/filter/hp1020passthrough",
                 "files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd", "NOTICE.md", "REDISTRIBUTION.md"):
        files.add(ROOT / name)
    return sorted(files)


def page(path, title, content):
    path.write_text('<!doctype html><html><head><meta charset="utf-8"><style>'
                    'body{font:14px -apple-system,Helvetica,sans-serif;line-height:1.5;margin:28px}'
                    'h1{font-size:23px}</style></head><body><h1>' + html.escape(title) +
                    '</h1>' + content + '</body></html>')


def product(work, output, component, remove=False):
    label = "Remove HP LaserJet 1020 Plus" if remove else "HP LaserJet 1020 Plus"
    resource = work / ("remove-resources" if remove else "install-resources")
    resource.mkdir(exist_ok=True)
    if remove:
        welcome = '<p>This removes the packaged printer setup and its pending or retained failed documents.</p><p>Finish printing before continuing. Other printers are left alone.</p>'
        conclusion = '<p>The packaged HP LaserJet 1020 Plus printer setup has been removed.</p>'
    else:
        welcome = '<p>Print to your HP LaserJet 1020 Plus from this Mac.</p><p>Everything is included. No Homebrew, Terminal commands, account or internet connection is needed.</p><p>You will be asked for your Mac administrator password. You can leave the printer disconnected during installation.</p><p>For Apple Silicon Macs. This is a private compatibility package using the original HP firmware, not an official HP installer.</p>'
        conclusion = '<p><b>Connect the printer to this Mac by USB and turn it on.</b></p><p>Open a document, choose Print, and select <b>HP LaserJet 1020 Plus</b>. Try one page first.</p><p>Use a USB adapter if your Mac needs one. This setup does not add Wi-Fi or require another computer to stay on.</p><p>If macOS asks whether to allow the USB accessory, choose Allow.</p>'
    page(resource / "welcome.html", label, welcome)
    page(resource / "conclusion.html", "Ready" if not remove else "Removed", conclusion)
    identifier = IDENTIFIER + (".remove" if remove else "")
    distribution = work / ("remove.xml" if remove else "install.xml")
    distribution.write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2">
 <title>{label}</title>
 <welcome file="welcome.html" mime-type="text/html"/>
 <conclusion file="conclusion.html" mime-type="text/html"/>
 <options customize="never" require-scripts="false" hostArchitectures="arm64"/>
 <domains enable_anywhere="false" enable_currentUserHome="false" enable_localSystem="true"/>
 <volume-check><allowed-os-versions><os-version min="11.0"/></allowed-os-versions></volume-check>
 <choices-outline><line choice="driver"/></choices-outline>
 <choice id="driver" title="{label}" visible="false"><pkg-ref id="{identifier}"/></choice>
 <pkg-ref id="{identifier}" version="{VERSION}" onConclusion="none">{component.name}</pkg-ref>
</installer-gui-script>
''')
    run(["/usr/bin/productbuild", "--distribution", distribution, "--resources", resource,
         "--package-path", work, output])


def handoff_files(output):
    return {
        "Install HP LaserJet 1020 Plus.pkg": output / INSTALLER_NAME,
        "Remove HP LaserJet 1020 Plus.pkg": output / REMOVER_NAME,
        "Start Here.txt": PACKAGE / "Start Here.txt",
    }


def disk_image(work, output):
    # A fresh folder keeps build reports and unrelated files out of the handoff.
    with tempfile.TemporaryDirectory(prefix="handoff-", dir=work) as temporary:
        folder = Path(temporary)
        for name, source in handoff_files(output).items():
            copy(source, folder / name)
        run(["/usr/bin/hdiutil", "create", "-ov", "-format", "UDZO",
             "-fs", "HFS+", "-volname", "HP LaserJet 1020 Plus", "-nospotlight",
             "-srcfolder", folder, output / DISK_IMAGE_NAME])


def build(args):
    if os.uname().sysname != "Darwin" or os.uname().machine != "arm64":
        raise RuntimeError("Build on an Apple Silicon Mac")
    work, cache, output = args.work.resolve(), args.sources.resolve(), args.output.resolve()
    for directory in (work, cache, output):
        directory.mkdir(parents=True, exist_ok=True)
    sources(cache)
    runtime, runtime_info = build_runtime(work, cache, args.jobs, args.reuse_runtime)
    stage = work / "payload"
    if stage.exists():
        shutil.rmtree(stage)
    base = stage / PREFIX.lstrip("/")
    base.mkdir(parents=True)
    for name in ("gs", "gsed", "foo2zjs"):
        copy(runtime / name, base / "runtime/bin" / name, 0o755)
    wrapper = base / "runtime/bin/foo2zjs-wrapper"
    wrapper.write_text(patched_wrapper())
    wrapper.chmod(0o755)
    copy(ROOT / "assets/runtime/foo2zjs-pstops", base / "runtime/bin/foo2zjs-pstops", 0o755)
    copy(ROOT / "assets/runtime/sihp1020.dl", base / "runtime/sihp1020.dl")
    copy(PACKAGE / "hp1020-convert", base / "runtime/bin/hp1020-convert", 0o755)
    for name in ("hp1020-print", "hp1020-root-spool-worker"):
        copy(PACKAGE / name, base / name, 0o755)
    copy(PACKAGE / "hp1020queue", stage / "usr/libexec/cups/backend/hp1020queue", 0o700)
    copy(ROOT / "files/cups/filter/hp1020passthrough", stage / "usr/libexec/cups/filter/hp1020passthrough", 0o755)
    copy(ROOT / "files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd", base / "HP-LaserJet_1020-Plus-hp1020zjs.ppd")
    copy(PACKAGE / "com.aayush.hp1020-root-spool-worker.plist", stage / "Library/LaunchDaemons/com.aayush.hp1020-root-spool-worker.plist")
    (base / "package-version").write_text(VERSION + "\n")
    for filename in ARCHIVES:
        copy(cache / filename, base / "Sources" / filename)
    copy(ROOT / "assets/licenses/foo2zjs-COPYING", base / "Licenses/foo2zjs-GPL-2.0.txt")
    # License texts come from the verified source archives even on a cached build.
    for filename, member, dest in (
        ("ghostpdl-10.07.0.tar.xz", "ghostpdl-10.07.0/LICENSE", "Ghostscript-AGPL-3.0.txt"),
        ("sed-4.10.tar.xz", "sed-4.10/COPYING", "GNU-sed-GPL-3.0.txt"),
    ):
        with tarfile.open(cache / filename) as archive:
            data = archive.extractfile(member).read()
        (base / "Licenses" / dest).write_bytes(data)
    files = source_files()
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in files}
    source_archive = base / "Sources/hp1020-package-source.tar.gz"
    with tarfile.open(source_archive, "w:gz") as archive:
        for path in files:
            archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    copy(PACKAGE / "README.md", base / "README.md")
    info = {"version": VERSION, "identifier": IDENTIFIER, "runtime": runtime_info,
            "source_sha256": source_hashes, "local_source_archive_sha256": digest(source_archive),
            "firmware_sha256": digest(base / "runtime/sihp1020.dl"),
            "signing": "Mach-O binaries ad-hoc signed; installer unsigned and not notarized",
            "physical_installation_and_print_test": "not performed"}
    (base / "build-info.json").write_text(json.dumps(info, indent=2) + "\n")
    # Keep the package permissions independent of the invoking user's umask.
    for directory in (stage, *(p for p in stage.rglob("*") if p.is_dir())):
        directory.chmod(0o755)
    for action in ("install", "remove"):
        script_dir = work / (action + "-scripts")
        script_dir.mkdir(exist_ok=True)
        for name in ("preinstall", "postinstall"):
            copy(PACKAGE / action / name, script_dir / name, 0o755)
            run(["/bin/zsh", "-n", script_dir / name])
        component = work / (action + ".pkg")
        command = ["/usr/bin/pkgbuild", "--identifier", IDENTIFIER + (".remove" if action == "remove" else ""),
                   "--version", VERSION, "--scripts", script_dir]
        if action == "install":
            command += ["--root", stage, "--install-location", "/", "--ownership", "recommended"]
        else:
            command += ["--nopayload"]
        run([*command, component])
        name = INSTALLER_NAME if action == "install" else REMOVER_NAME
        product(work, output / name, component, remove=(action == "remove"))
    copy(PACKAGE / "Start Here.txt", output / "Start Here.txt")
    copy(base / "build-info.json", output / "build-info.json")
    disk_image(work, output)
    artifacts = [output / name for name in (INSTALLER_NAME, REMOVER_NAME, DISK_IMAGE_NAME)]
    sums = "".join(f"{digest(p)}  {p.name}\n" for p in sorted(artifacts))
    (output / "SHA256SUMS").write_text(sums)
    print(f"Copy to the other Mac: {output / DISK_IMAGE_NAME}")
    print("No software was installed and no printer was contacted.")
    print(f"Validate next: python3 scripts/validate-macos-package.py --work {work} --output {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=ROOT / ".build/macos-package")
    parser.add_argument("--sources", type=Path, default=ROOT / ".build/macos-package-sources")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/HP-LaserJet-1020-Plus")
    parser.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 2))
    parser.add_argument("--reuse-runtime", action="store_true", help="Reuse only a runtime with matching recipe and verified binary hashes")
    build(parser.parse_args())
