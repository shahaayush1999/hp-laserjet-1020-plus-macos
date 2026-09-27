# Runtime and verification records

The installer obtains `ghostscript` and `gnu-sed` through Homebrew and compiles
foo2zjs from the preserved `vendor/foo2zjs-source/`. It copies the original
`sihp1020.dl` from `assets/runtime/`. The reference files under `assets/runtime/`
are not rebuilt or overwritten during installation.

The installed helper lives in `/Library/Printers/hp1020/`. Per-account package
ownership is recorded under `~/.local/state/hp1020/`, so the uninstall script can
remove additions without removing pre-existing packages. No global Homebrew
`autoremove` is run. Homebrew's dependency checks remain enabled.

`scripts/rebuild-runtime-from-vendor.sh OUTPUT_DIRECTORY` reproduces the small
native runtime for the current Apple Silicon Mac. Its wrapper changes quote
filenames and propagate conversion failures. It does not compile Ghostscript or
GNU sed, install software, or contact a printer.

Run `python3 scripts/validate-macos-setup.py` for the isolated maintainer checks.
It uses the host's existing Ghostscript/GNU sed for real conversion comparisons,
then simulates package management, installation, cleanup and USB calls. It records
exact tested source hashes and limitations in `assets/macos-setup-validation.json`.
Python is not required by the end-user install or uninstall scripts.

Firmware research keeps its own hashes and recovery instructions in
`analysis/README.md`. The abandoned self-contained runtime bundle and its build
machinery were removed; Git retains that history.
