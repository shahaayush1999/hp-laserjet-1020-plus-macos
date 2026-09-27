# Runtime manifest

The installation bundle is `assets/macos-arm64/`. Its dependencies are included;
installation does not use Homebrew or download software.

| Component | Source/version | Purpose |
| --- | --- | --- |
| Ghostscript | GhostPDL 10.07.0 | Render PDF/PostScript; resources and fonts embedded |
| GNU sed | 4.10 | Process the foo2zjs PostScript stream |
| foo2zjs | Preserved `vendor/foo2zjs-source/`, including its JBIG encoder | Encode printer data |
| HP firmware | Original `assets/runtime/sihp1020.dl` | Stock device firmware |

The three native executables are arm64, target macOS 11.0, link only macOS system
libraries and carry ad-hoc signatures. This deployment target is not a claim of
execution testing on every macOS release.

- `assets/macos-arm64/build-info.json` records the actual compiler, SDK, build
  configuration, original source hashes and resulting executable hashes.
- `assets/macos-arm64/SHA256SUMS` covers the installation inputs, source archives
  and licenses. Run `shasum -a 256 -c assets/macos-arm64/SHA256SUMS` from the repo.
- `assets/macos-runtime-validation.json` records the exact sources and artifacts
  checked by `scripts/validate-macos-runtime.py`, including scope and limitations.
- `vendor/runtime-sources/README.md` records source URLs, pins and license locations.

`scripts/rebuild-runtime-from-vendor.sh` verifies the bundled source pins before
building. The builder generates the metadata and checksum list; the validator
generates its own report. Never edit tested hashes by hand. After intentional
installer/template edits, regenerate only the installation manifest with
`python3 scripts/build-macos-runtime.py --refresh-manifest`, then rerun the validator.

The historical whole-repository checksum list has been removed: it contained
outdated hashes and even a temporary manifest filename. Research evidence keeps
its own exact source/fixture hashes and recovery instructions in `analysis/README.md`.
