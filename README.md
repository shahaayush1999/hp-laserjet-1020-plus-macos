# HP LaserJet 1020 Plus on macOS

Print over USB from an **Apple Silicon Mac (M1 or newer)** using the original HP firmware and foo2zjs. This is an unofficial compatibility setup.

**Everything needed for installation is included in this repository.** After downloading it, installation needs no internet connection, Homebrew, extra downloads or developer tools. An administrator password is required.

## Install

1. On [the repository page](https://github.com/shahaayush1999/hp-laserjet-1020-plus-macos), choose **Code → Download ZIP**. Open the ZIP to extract it.
2. Connect the printer to the Mac by USB and turn it on. Allow the USB accessory if macOS asks. Disconnect other LaserJet 1020 printers while installing.
3. Open **Terminal** and run these two lines, assuming the extracted folder is in Downloads:

   ```sh
   cd ~/Downloads/hp-laserjet-1020-plus-macos-main
   zsh scripts/install.sh
   ```

4. Enter your Mac administrator password when prompted. Once installation finishes, print from any app and select **HP LaserJet 1020 Plus**.

If you put the folder elsewhere, type `cd ` in Terminal, drag the extracted folder into the window, and press Return. Then run `zsh scripts/install.sh`. If you cloned the repository, run the same script from your clone's folder.

The current normal printing path uses **A4 paper**. Start with one page. This setup does not add Wi-Fi, automatic duplex printing or support for other printer models.

## Remove

Finish printing first. Open Terminal in the repository folder as above and run:

```sh
zsh scripts/uninstall.sh
```

This removes this printer's queue, background worker, bundled tools, logs and saved print jobs. It also removes the older per-user HP1020 helper if present. Other printers and Homebrew software are left alone.

You can delete the downloaded repository folder afterwards. If you already deleted it, download it again to get the uninstall script. The folder is not needed for everyday printing; deleting it alone does not uninstall the driver.

## Updating an existing setup

Finish or cancel pending print jobs, download the current repository, and run `zsh scripts/install.sh` again. The script replaces this setup's files and removes its old per-user runtime. Previously installed Homebrew software is not removed automatically because other software may use it.

## If something goes wrong

Keep the Terminal error message. Check that the printer is powered on, connected directly by USB, and allowed as an accessory in macOS. An adapter must support data, not just charging.

For a test page after installation:

```sh
zsh scripts/print-test.sh
```

For diagnostics:

```sh
zsh scripts/diagnose.sh
```

These two commands access the connected printer. The test command prints a page.

## Compatibility and verification

The bundled executables target macOS 11 or newer on Apple Silicon. Offline checks ran on macOS 27; older macOS versions and a fresh physical installation of this bundled revision have not been tested. The earlier HP-based setup has printed successfully. The new checks cover conversion and simulated installation/removal, including downloaded-file attributes; they do not replace a real print test.

Installation checks the included files against saved SHA-256 checksums before using them. The executables have local ad-hoc signatures, without paid Apple Developer ID signing or notarization. After verification, the installer clears the downloaded-file quarantine only on its temporary copies of the bundled executables; no system security setting is changed.

## Included software and maintenance

- `assets/macos-arm64/`: bundled Ghostscript, GNU sed, foo2zjs, helpers and HP firmware used by installation.
- `vendor/runtime-sources/`: exact Ghostscript and GNU sed source archives and provenance.
- `vendor/foo2zjs-source/`: corresponding foo2zjs source.
- `assets/licenses/`: license texts. See [NOTICE.md](NOTICE.md) and [REDISTRIBUTION.md](REDISTRIBUTION.md) for third-party notices.
- [MANIFEST.md](MANIFEST.md): build and verification records.

Maintainers can rebuild the bundled tools **offline** on an Apple Silicon Mac with Python 3 and Apple's command-line build tools:

```sh
zsh scripts/rebuild-runtime-from-vendor.sh
python3 scripts/validate-macos-runtime.py
```

Those build tools are not required to install or use the printer setup.

The separate open firmware replacement under `analysis/` is unfinished and cannot print yet. It is not installed by these scripts. The original runtime under `assets/runtime/` remains preserved for that research; its files and the research evidence have not been replaced by the new bundle.
