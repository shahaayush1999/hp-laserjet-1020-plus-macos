# Redistribution Notes

This is not legal advice. It is a practical summary of the redistribution posture for this repo.

## Summary

For a private/personal repo, this package is intentionally self-contained.

For a public repo, the risky part is not the custom scripts or foo2zjs. The risky part is the HP firmware blob and related firmware artifacts:

- `assets/runtime/sihp1020.dl`
- `assets/firmware-source/sihp1020.dl`
- `assets/firmware-source/sihp1020.img`
- `assets/firmware-source/sihp1020.tar.gz`

Recommended posture:

- Private/personal repo: bundling the firmware is a practical preservation choice.
- Public repo: safest version removes HP firmware blobs and makes the installer download/extract/provision firmware from a user-supplied or officially obtained source.

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
- source snapshot in `vendor/foo2zjs-source/`
- GPLv2 text in `assets/licenses/foo2zjs-COPYING`

If distributing the built foo2zjs binaries, keep the corresponding source and GPL license text available in the same repo.

### HP Firmware

The HP LaserJet 1020 needs firmware uploaded after power-on. OpenPrinting documents that requirement and the `sihp1020.dl` filename.

The firmware is not authored by this repo. The foo2zjs source/download tooling identifies it as HP-copyrighted firmware. Debian's patched `getweb` source also labels `sihp1020` firmware as `(c) Copyright Hewlett-Packard 2005`.

HP's EULA language for HP software generally grants use, backup/archive copies, and transfer under restrictions, but says users do not have the right to distribute the Software Product. HP's website terms also restrict copying/distribution of HP materials unless expressly permitted.

That means public redistribution of the firmware blob is the legal risk.

## Safer Public Release Shape

If this repo is made public, consider:

1. Remove:
   - `assets/runtime/sihp1020.dl`
   - `assets/firmware-source/`
2. Keep:
   - custom scripts
   - CUPS backend/filter
   - PPD
   - foo2zjs source/runtime and GPL text
3. Add installer logic that accepts one of:
   - `HP1020_FIRMWARE=/path/to/sihp1020.dl`
   - a user-supplied HP driver package to extract firmware from
   - a download from an official HP URL if one is available
4. Document that users must obtain firmware for hardware they own.

## References

- OpenPrinting HP LaserJet 1020 page: https://www.openprinting.org/printer/hp/hp-laserjet_1020
- OpenPrinting foo2zjs driver page: https://www.openprinting.org/driver/foo2zjs/
- Debian foo2zjs package: https://packages.debian.org/sid/text/printer-driver-foo2zjs
- Debian getweb patch showing HP firmware copyright labels: https://sources.debian.org/patches/foo2zjs/20200505dfsg0-2/0027-getweb-use-quirinux.org-mirror-as-the-original-site-.patch/
- HP EULA page: https://h30670.www3.hp.com/portal/swdepot/html/disclaimer.html
- HP Terms of Use: https://www.hp.com/us-en/terms-of-use.html
