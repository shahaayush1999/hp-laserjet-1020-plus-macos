# Notice

This repository is a local compatibility package for an HP LaserJet 1020 Plus on macOS.

It includes:

- small custom shell scripts written for this setup
- a PPD describing the printer queue
- a built local copy of foo2zjs runtime files
- bundled Ghostscript 10.07.0 and GNU sed 4.10, with their exact source archives
- the foo2zjs source snapshot used for the local runtime
- `sihp1020.dl`, the HP LaserJet 1020 firmware blob used by foo2zjs
- firmware artifacts created while getting the printer working
- the JBIG-KIT 2.1 streaming subset and an experimental open image decoder

The foo2zjs files are GPLv2. See `assets/licenses/foo2zjs-COPYING`.

Ghostscript's main license is AGPLv3; see
`assets/licenses/Ghostscript-AGPL-3.0.txt`. Its included libraries, fonts and
resources retain their individual notices in the complete source archive under
`vendor/runtime-sources/`. GNU sed is GPLv3 or later; see
`assets/licenses/GNU-sed-GPL-3.0.txt` and the accompanying source archive.

The streaming JBIG subset and image component are GPL version 2 or later.
See `vendor/jbigkit-2.1/COPYING`, its source notices, `PROVENANCE.md` and the
complete `LOCAL-CHANGES.patch`. The original full foo2zjs decoder remains
unchanged as an offline comparison tool.

The repository is public at the owner's request. The original HP firmware and
firmware artifacts are preserved for reproducibility; this project's publication
does not grant a new license to HP's firmware. See `REDISTRIBUTION.md` for the
existing provenance and unresolved redistribution concerns.
