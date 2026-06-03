# Open Source Options and Firmware Reality

This document explains what is open, what is proprietary, and why the macOS setup in this repo exists.

## Short Answer

The mature open source driver path for the HP LaserJet 1020/1020 Plus is `foo2zjs`. This repo already uses it.

The part that is not open source is the HP firmware blob that the printer needs after power-on. The printer is a host-based USB laser printer, not a modern driverless/AirPrint/IPP Everywhere printer and not a self-contained PostScript/PCL printer.

So the practical options are:

1. Use `foo2zjs` plus firmware loading.
2. Use HPLIP plus HP's proprietary plug-in/firmware path.
3. Put the printer behind a Linux/CUPS print server and expose it to macOS as a normal network printer.
4. Attempt an open firmware replacement, which is possible in theory but a serious reverse-engineering project.

## What Existing Open Source Software Exists?

### foo2zjs

OpenPrinting lists the HP LaserJet 1020 as supported by the `foo2zjs` free software printer driver and recommends `foo2zjs-z1`.

That is the host-side print translator. It converts the document stream into the printer's expected host-based wire format.

This repo bundles:

- built `foo2zjs` runtime files in `assets/runtime/`
- corresponding source in `vendor/foo2zjs-source/`
- GPLv2 text in `assets/licenses/foo2zjs-COPYING`

### HPLIP

HP's Linux support table lists the HP LaserJet 1020 as supported, but marks it as requiring a driver plug-in and as end-of-support.

HPLIP itself contains open source components, but HP states that HPLIP driver plug-ins are proprietary/non-open and not part of the HPLIP tarball. This is why many Linux distributions cannot simply package the complete working firmware/plugin path as normal free software.

### Gutenprint and Generic HP Drivers

Gutenprint and generic HP LaserJet drivers may appear as macOS options, and old HP/Apple driver packages may contain related drivers. They are not enough for this printer by themselves if the firmware has not been loaded and the job is not converted into the right host-based format.

That explains the symptom where macOS thinks printing succeeded, the printer stirs, and no page comes out.

### Linux/CUPS Print Server

The cleanest daily-use alternative is often a small Linux/CUPS print server:

- Linux host loads firmware using `foo2zjs`/udev/HPLIP behavior.
- Linux host owns the USB connection.
- macOS prints to the Linux host over IPP/AirPrint-style discovery.

This makes the Mac side feel normal, but it still does not remove the firmware blob from the system.

## Why This Repo Has macOS Glue

On Linux, `foo2zjs` historically used hotplug/udev scripts to upload firmware when the printer appears. macOS does not provide that exact udev path.

This repo implements the same idea in macOS terms:

- a CUPS queue
- a CUPS backend/filter
- a LaunchDaemon-backed worker
- firmware upload before print data
- `foo2zjs` conversion for the document stream

That is not random automation. It is a compatibility layer around a printer that requires host-loaded firmware.

## What Firmware Means Here

The HP LaserJet 1020 loses its working firmware on power-off. After power-on, the host must upload code before normal print jobs work.

In this repo:

- `assets/runtime/sihp1020.dl` is the downloadable firmware wrapper sent to the printer.
- `assets/firmware-source/sihp1020.img` is the underlying firmware image.
- `foo2zjs` tooling converts the `.img` into the `.dl` upload format.

Local inspection shows:

- `sihp1020.dl` starts as HP Printer Job Language data, including `@PJL ENTER LANGUAGE=ACL`.
- `sihp1020.img`, after its 8-byte date prefix, is an `ELF 32-bit MSB executable, Old Xtensa (unofficial), statically linked, stripped`.
- strings inside the image include `USB2Thread`, `agiACLDownload`, `FUSER`, `TONEREXP`, `FWVER`, and a 2005 build line.

So this is executable embedded code for the printer, not a normal macOS driver file or a simple configuration table.

## Could We Write Open Source Firmware?

In theory, yes. In practice, it is a real reverse-engineering project.

A credible open firmware effort would need to understand:

- the exact Xtensa CPU variant/configuration
- memory map and startup path
- USB behavior before and after firmware upload
- HP ACL/PJL download protocol
- page data protocol expected by the print engine
- motor, paper feed, fuser, laser, sensor, toner, and error-state control
- timing and safety behavior

The image is stripped, so there are no helpful function names. Hardware control also matters more than with many simpler reverse-engineering projects because a laser printer has moving parts, high heat, and paper handling.

The likely project shape would be:

1. Capture USB traffic from working firmware loads and print jobs.
2. Identify the embedded CPU and disassembly tooling.
3. Map the firmware's startup and command handlers.
4. Build a minimal replacement firmware that can enumerate and accept one known simple command.
5. Extend it into a safe print-engine controller.
6. Keep the host-side `foo2zjs` path unless also reimplementing a full PCL/PostScript interpreter.

That is possible, but it is not the same order of work as packaging a driver.

## Practical Public Release Strategy

For a freely redistributable public repo, the realistic path is:

1. Keep the open/custom code:
   - CUPS backend/filter
   - installer/uninstaller/diagnostics
   - PPD
   - `foo2zjs` source/runtime and GPL text
2. Remove HP firmware blobs:
   - `assets/runtime/sihp1020.dl`
   - `assets/firmware-source/`
3. Make install accept:
   - `HP1020_FIRMWARE=/path/to/sihp1020.dl`
   - or `HP1020_FIRMWARE_IMG=/path/to/sihp1020.img`
   - or a user-supplied HP package/archive that can be extracted locally
4. Document that the user must provide firmware for hardware they own.

For personal use, the current private repo remains intentionally self-contained.

## References

- OpenPrinting HP LaserJet 1020: https://www.openprinting.org/printer/hp/hp-laserjet_1020
- HP HPLIP supported devices table: https://developers.hp.com/hp-linux-imaging-and-printing/supported_devices/index
- HPLIP plug-in redistribution issue: https://bugs.launchpad.net/hplip/+bug/1214318
- HP LaserJet 1020 support downloads page: https://support.hp.com/us-en/drivers/hp-laserjet-1020-printer-series/model/439423
