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

The direct encoder conversion cases include `-n2`; they do not exercise print
dialog copy propagation, collation, the asynchronous queue or device status.
On September 28, read-only installed-script inspection and a relocated backend
reproduction confirmed that 1 and 4 requested copies enqueue the same single
document without copy metadata and return success before any worker runs.
The repository backend likewise drops the CUPS copy/options arguments. These
support defects remain unfixed; the saved validation report is not evidence of
complete driver behavior. CUPS documents the [backend argument and exit-status
contract](https://www.cups.org/doc/man-backend.html) and the separate
[scheduler status messages](https://openprinting.github.io/cups/doc/api-filter.html).
There is no implemented paper-out or physical-completion feedback path.

Firmware research keeps its own hashes and recovery instructions in
`analysis/README.md`. The abandoned self-contained runtime bundle and its build
machinery were removed; Git retains that history.
