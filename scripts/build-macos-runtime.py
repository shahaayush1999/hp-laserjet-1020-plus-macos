#!/usr/bin/env python3
"""Rebuild the bundled Apple Silicon runtime offline. Never installs or contacts USB.

Requires Python 3 and Apple's command-line build tools on the maintainer's Mac.
The recipient Mac uses the checked-in binaries and does not run this builder.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent.parent
PREFIX = "/Library/Printers/hp1020"
OUTPUT = ROOT / "assets/macos-arm64"
SOURCES = ROOT / "vendor/runtime-sources"
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
    for name, (_, sha) in ARCHIVES.items():
        path = cache / name
        if not path.is_file() or digest(path) != sha:
            raise RuntimeError(f"Missing or incorrect pinned source: {path}")


def extract(cache, work, name):
    directory = work / name.removesuffix(".tar.xz")
    # Always start from the verified archive, not a potentially edited build tree.
    # Only these two fixed, disposable build directories are replaced.
    if directory.exists():
        shutil.rmtree(directory)
    run(["/usr/bin/tar", "-xf", cache / name, "-C", work])
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
              "sed": SED_CONFIGURE, "foo2zjs": inputs, "builder_sha256": digest(Path(__file__))}
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
    return original


def installation_inputs():
    paths = [
        *OUTPUT.glob("*"), *SOURCES.glob("*.tar.xz"),
        *(ROOT / "assets/licenses").glob("*"),
        ROOT / "scripts/install.sh", ROOT / "scripts/uninstall.sh",
        ROOT / "scripts/macos-common.sh", ROOT / "scripts/build-macos-runtime.py",
        ROOT / "scripts/rebuild-runtime-from-vendor.sh",
        ROOT / "scripts/diagnose.sh", ROOT / "scripts/print-test.sh",
        *(ROOT / "templates").glob("*.in"),
        ROOT / "files/cups/backend/hp1020queue",
        ROOT / "files/cups/filter/hp1020passthrough",
        ROOT / "files/ppd/HP-LaserJet_1020-Plus-hp1020zjs.ppd",
    ]
    return sorted(p for p in paths if p.is_file() and p.name != "SHA256SUMS")


def refresh_manifest():
    sums = "".join(f"{digest(p)}  {p.relative_to(ROOT)}\n" for p in installation_inputs())
    (OUTPUT / "SHA256SUMS").write_text(sums)


def main(args):
    sources(SOURCES)
    if args.refresh_manifest:
        refresh_manifest()
        return
    if os.uname().sysname != "Darwin" or os.uname().machine != "arm64":
        raise RuntimeError("Build on an Apple Silicon Mac")
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    runtime, info = build_runtime(work, SOURCES, args.jobs, args.reuse_runtime)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name in ("gs", "gsed", "foo2zjs"):
        copy(runtime / name, OUTPUT / name, 0o755)
    wrapper = OUTPUT / "foo2zjs-wrapper"
    wrapper.write_text(patched_wrapper())
    wrapper.chmod(0o755)
    copy(ROOT / "assets/runtime/foo2zjs-pstops", OUTPUT / "foo2zjs-pstops", 0o755)
    copy(ROOT / "assets/runtime/sihp1020.dl", OUTPUT / "sihp1020.dl")
    for filename, member, dest in (
        ("ghostpdl-10.07.0.tar.xz", "ghostpdl-10.07.0/LICENSE", "Ghostscript-LICENSE.txt"),
        ("ghostpdl-10.07.0.tar.xz", "ghostpdl-10.07.0/doc/COPYING", "Ghostscript-AGPL-3.0.txt"),
        ("sed-4.10.tar.xz", "sed-4.10/COPYING", "GNU-sed-GPL-3.0.txt"),
    ):
        with tarfile.open(SOURCES / filename) as archive:
            data = archive.extractfile(member).read()
        (ROOT / "assets/licenses" / dest).write_bytes(data)
    info["host_macos"] = subprocess.check_output(["/usr/bin/sw_vers", "-productVersion"], text=True).strip()
    info["compiler"] = subprocess.check_output(["/usr/bin/clang", "--version"], text=True).strip()
    info["sdk"] = subprocess.check_output(["/usr/bin/xcrun", "--show-sdk-version"], text=True).strip()
    info["signing"] = "ad-hoc signatures; no Developer ID or notarization"
    info["original_inputs"] = {str(p.relative_to(ROOT)): digest(p) for p in (
        ROOT / "assets/runtime/foo2zjs-wrapper", ROOT / "assets/runtime/foo2zjs-pstops",
        ROOT / "assets/runtime/sihp1020.dl")}
    (OUTPUT / "build-info.json").write_text(json.dumps(info, indent=2) + "\n")
    refresh_manifest()
    print(f"Built {OUTPUT}. Run python3 scripts/validate-macos-runtime.py next.")
    print("No installation or printer contact occurred.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=Path("/tmp/hp1020-macos-runtime-build"))
    parser.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 2))
    parser.add_argument("--reuse-runtime", action="store_true")
    parser.add_argument("--refresh-manifest", action="store_true", help="Refresh installation input checksums only; does not validate")
    main(parser.parse_args())
