# HP LaserJet 1020 Plus on macOS

Print over USB from an Apple Silicon Mac using the original HP firmware and foo2zjs. This is an unofficial compatibility setup.

## Install

Connect the printer by USB, turn it on, and run:

```sh
git clone --depth 1 https://github.com/shahaayush1999/hp-laserjet-1020-plus-macos.git
cd hp-laserjet-1020-plus-macos
zsh scripts/install.sh
```

The script installs Homebrew if needed, downloads Ghostscript and GNU sed, builds the small printer helper, and sets up the printer. Follow the Homebrew prompts and enter your Mac administrator password when asked. An internet connection is required.

If macOS first asks to install Apple's Command Line Tools when you run `git`, complete that installation and run the commands again. Use a macOS version [supported by Homebrew](https://docs.brew.sh/Installation#macos-requirements).

Once installed, print from any app and select **HP LaserJet 1020 Plus**. The normal printing path uses **A4 paper**. Start with one page.

## Uninstall

Finish printing, open Terminal in the cloned repository folder, and run:

```sh
zsh scripts/uninstall.sh
```

This removes the printer queue, background worker, helper files, logs and saved print jobs. It also removes the Homebrew packages this installer added, including their unused dependencies. Packages that were already installed or are now needed by other Homebrew packages are kept.

If this setup installed Homebrew, it also removes Homebrew when nothing else uses it. Existing Homebrew installations are kept. Run cleanup from the same Mac account used for installation; Homebrew removal may need internet access and your administrator password.

You can delete the cloned folder afterwards. If you lost it, clone the repository again and run the uninstall command. Deleting the folder alone does not uninstall the printer.

## Update

From the repository folder, after finishing any print jobs:

```sh
git pull
zsh scripts/install.sh
```

The installer remembers which packages it originally added, including across reinstalls. It does not require you to keep a separate cleanup file.

## Troubleshooting

Check that the printer is on, connected by a data-capable USB cable/adapter, and allowed as a USB accessory in macOS. Keep any Terminal error message.

```sh
zsh scripts/print-test.sh   # prints a test page
zsh scripts/diagnose.sh    # checks the queue and connected printer
```

If installation or cleanup fails, rerun the corresponding script after addressing the error. Cleanup retains its package record when it fails so it can be retried.

## Scope

This uses the working HP-based printing approach. The revised install/cleanup scripts have been checked with simulated Homebrew, system installation and USB calls; a fresh Mac installation and physical print test of this revision remain untested. Your Mac's existing printing setup is changed only when you run the scripts.

The original firmware, foo2zjs source and research evidence remain in the repository. Ghostscript and GNU sed come from Homebrew instead of a bundled software archive. See [NOTICE.md](NOTICE.md), [REDISTRIBUTION.md](REDISTRIBUTION.md) and [MANIFEST.md](MANIFEST.md) for provenance.

The separate open firmware replacement under `analysis/` is unfinished and cannot print yet. These scripts do not install it.
