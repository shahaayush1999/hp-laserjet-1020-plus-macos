# Redistribution Notes

This is not legal advice. It is a practical summary of the redistribution posture for this repo.

## Summary

This repository is public at the owner's request and includes the runtime and
sources needed for installation without additional downloads. Publication is
not a resolution of the HP firmware redistribution concerns below.

For a public repo, the risky part is not the custom scripts or foo2zjs. The risky part is the HP firmware blob and related firmware artifacts:

- `assets/runtime/sihp1020.dl`
- `assets/firmware-source/sihp1020.dl`
- `assets/firmware-source/sihp1020.img`
- `assets/firmware-source/sihp1020.tar.gz`

The printer being old, unsupported, out of warranty, or no longer sold does not itself remove copyright or license restrictions on the firmware. Those facts are good preservation arguments, but they are not the same thing as redistribution permission.

## Components

### Custom macOS/CUPS Glue

Files written for this setup:

- `files/cups/backend/hp1020queue`
- `files/cups/filter/hp1020passthrough`
- `templates/hp1020-print.in`
- `templates/hp1020-root-spool-worker.in`
- `templates/com.aayush.hp1020-root-spool-worker.plist.in`
- `scripts/*.sh`

These can be released under a license chosen by the repo owner.

### foo2zjs

The foo2zjs project is free software. OpenPrinting describes `foo2zjs` as a free software driver and lists it as the recommended driver for HP LaserJet 1020.

This repo includes:

- built runtime files in `assets/runtime/`
- the rebuilt installation runtime in `assets/macos-arm64/`
- source snapshot in `vendor/foo2zjs-source/`
- GPLv2 text in `assets/licenses/foo2zjs-COPYING`

If distributing the built foo2zjs binaries, keep the corresponding source and GPL license text available in the same repo.

### Ghostscript and GNU sed

The installation bundle now includes Ghostscript 10.07.0 and GNU sed 4.10.
Their unmodified source archives are in `vendor/runtime-sources/`; its README
records upstream URLs and verified SHA-256 pins. The offline build recipe is
`scripts/build-macos-runtime.py`, with the resulting configuration recorded in
`assets/macos-arm64/build-info.json`.

Ghostscript's main AGPLv3 license and GNU sed's GPLv3 license are copied into
`assets/licenses/`. The GhostPDL source archive also preserves all included
library/font/resource notices. Keep the sources, build recipe and notices with
the bundled executables.

### HP Firmware

The HP LaserJet 1020 needs firmware uploaded after power-on. OpenPrinting documents that requirement and the `sihp1020.dl` filename.

The firmware is not authored by this repo. The foo2zjs source/download tooling identifies it as HP-copyrighted firmware. Debian's patched `getweb` source also labels `sihp1020` firmware as `(c) Copyright Hewlett-Packard 2005`.

HP's EULA language for HP software generally grants use, backup/archive copies, and transfer under restrictions, but says users do not have the right to distribute the Software Product. HP's website terms also restrict copying/distribution of HP materials unless expressly permitted.

That means public redistribution of the firmware blob is the legal risk.

## References

- OpenPrinting HP LaserJet 1020 page: https://www.openprinting.org/printer/hp/hp-laserjet_1020
- OpenPrinting foo2zjs driver page: https://www.openprinting.org/driver/foo2zjs/
- Debian foo2zjs package: https://packages.debian.org/sid/text/printer-driver-foo2zjs
- Debian getweb patch showing HP firmware copyright labels: https://sources.debian.org/patches/foo2zjs/20200505dfsg0-2/0027-getweb-use-quirinux.org-mirror-as-the-original-site-.patch/
- HP EULA page: https://h30670.www3.hp.com/portal/swdepot/html/disclaimer.html
- HP Terms of Use: https://www.hp.com/us-en/terms-of-use.html
