# Bundled runtime sources

These unmodified upstream archives accompany the prebuilt executables in
`assets/macos-arm64/`. The install script never downloads or compiles them.

| Archive | Upstream source | SHA-256 |
| --- | --- | --- |
| `ghostpdl-10.07.0.tar.xz` | [Artifex release gs10070](https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10070/ghostpdl-10.07.0.tar.xz) | `ba1366006a93b91e615f74aad9c0905fae503d3f5b04078ce2ddbe360bd2f9df` |
| `sed-4.10.tar.xz` | [GNU sed 4.10](https://ftp.gnu.org/gnu/sed/sed-4.10.tar.xz) | `b8e72182b2ec96a3574e2998c47b7aaa64cc20ce000d8e9ac313cc07cecf28c7` |

The pins and runtime recipe were preserved from the earlier local build. The
archives were fetched again on 2026-09-28 and verified against those pins before
extraction. Sources are ordinary Git files, so Download ZIP and clones contain
the complete archives without Git LFS or another download step.

The GhostPDL archive contains Ghostscript and the libraries/resources used in
its build, along with their individual copyright and license notices. Its
`LICENSE` notice is copied to `assets/licenses/Ghostscript-LICENSE.txt` and its
full `doc/COPYING` license to `assets/licenses/Ghostscript-AGPL-3.0.txt`. GNU sed's
`COPYING` is copied to `assets/licenses/GNU-sed-GPL-3.0.txt`. The corresponding
foo2zjs source and GPL text are in `vendor/foo2zjs-source/` and `assets/licenses/`.

Reproduction: run `zsh scripts/rebuild-runtime-from-vendor.sh` on an Apple Silicon
Mac with Python 3 and Apple command-line tools. It uses only the included sources
and standard build tools, with Homebrew excluded from the build PATH. Build
intermediates/logs default to `/tmp/hp1020-macos-runtime-build`; `--work PATH`
selects another disposable directory. No software is installed and no printer is
contacted. The exact flags, source hashes and compiler are recorded in the
bundle's generated `build-info.json`.

The installed wrapper is derived from the preserved original with narrow edits:
quote input filenames and propagate conversion-pipeline failures. The original
wrapper, encoder and firmware under `assets/runtime/` remain research references.

The binary checks and conversion fixtures do not establish physical printing,
complete driver-option support, or execution compatibility on every older Mac.
