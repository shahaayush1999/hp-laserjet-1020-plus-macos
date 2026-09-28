# Notice

This repository is a local compatibility package for an HP LaserJet 1020 Plus on macOS.

It includes:

- custom shell scripts, a Python print worker and a small C descriptor launcher
- a PPD describing the printer queue
- a built local copy of foo2zjs runtime files
- the foo2zjs source snapshot used for the local runtime
- `sihp1020.dl`, the HP LaserJet 1020 firmware blob used by foo2zjs
- firmware artifacts created while getting the printer working
- the JBIG-KIT 2.1 streaming subset and an experimental open image decoder

The foo2zjs files are GPLv2. See `assets/licenses/foo2zjs-COPYING`.

The installer obtains Ghostscript, GNU sed and Python from Homebrew. Their binaries and
source archives are not bundled in the current checkout.

The streaming JBIG subset and image component are GPL version 2 or later.
See `vendor/jbigkit-2.1/COPYING`, its source notices, `PROVENANCE.md` and the
complete `LOCAL-CHANGES.patch`. The original full foo2zjs decoder remains
unchanged as an offline comparison tool.

The repository is public at the owner's request. The original HP firmware and
firmware artifacts are preserved for reproducibility; this project's publication
does not grant a new license to HP's firmware. See `REDISTRIBUTION.md` for the
existing provenance and unresolved redistribution concerns.
