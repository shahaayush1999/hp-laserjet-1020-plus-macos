# HP LaserJet 1020 Plus on macOS

Print over USB from an Apple Silicon Mac using the original HP firmware and foo2zjs. This is an unofficial driver integrated with macOS printing.

## Install

Connect the printer by USB, turn it on, and run:

```sh
git clone --depth 1 https://github.com/shahaayush1999/hp-laserjet-1020-plus-macos.git
cd hp-laserjet-1020-plus-macos
zsh scripts/install.sh
```

If macOS asks to install Apple's Command Line Tools when you run `git`, complete that installation and run the commands again. Enter your Mac administrator password when the installer asks.

The script builds the driver from the included source and adds the printer. No Homebrew packages, background app or separate worker are needed. Internet access is needed to clone the repository and obtain Apple's tools if missing; printing uses USB.

Once installed, print from your app and select **HP LaserJet 1020 Plus**. Choose **A4** or **US Letter** to match your paper. Copies, selected pages, page order and pages per sheet use the normal Mac print settings.

macOS manages the jobs directly. You can see waiting jobs and cancel them in the normal print queue. The driver reports paper, cover and jam conditions when the printer supplies that feedback. Those responses are tested with a simulated printer; compatibility with this physical printer still needs verification. Sending a document successfully does not, by itself, prove that the last sheet has printed.

## Uninstall

Finish printing, open Terminal in the cloned repository folder, and run:

```sh
zsh scripts/uninstall.sh
```

This removes the printer queue and installed driver files. It also cleans up helper files left by older versions. If an earlier installer added Homebrew packages, cleanup removes only those packages and dependencies that other software does not need. Pre-existing packages are kept. Run cleanup from the same account used for installation; removing an older Homebrew installation may require internet access.

You can delete the cloned folder afterwards. If you lost it, clone the repository again and run the uninstall command. Deleting the folder alone does not uninstall the printer.

## Update

After finishing any print jobs, run from the repository folder:

```sh
git pull
zsh scripts/install.sh
```

Updates remove the older background worker and extra rendering dependencies owned by this setup. If replacement fails, the installer restores the previous files and queue settings. Failed package cleanup retains its record for a later retry.

## Troubleshooting

Check that the printer is on, connected by a data-capable USB cable/adapter, and allowed as a USB accessory in macOS. Keep any Terminal error message.

```sh
zsh scripts/print-test.sh   # prints a test page
zsh scripts/diagnose.sh    # checks software and the queue; does not contact USB
```

An unplugged printer can be reconnected while its job waits. If a transfer fails after some data was sent, the job is held instead of automatically printing again. Check for partially printed pages before resuming it. Cancellation cannot undo sheets already printed.

Normal app printing and PDF files use macOS's renderer. Legacy `.ps`/`.eps` files need to be exported as PDF in an application that supports them before printing; this driver no longer installs a separate PostScript interpreter. [Apple also removed its built-in support for these formats](https://support.apple.com/en-ie/108775).

## Scope

The native redesign has passed offline rendering, simulated printer, setup and security checks. Its real macOS scheduler and administrator installation check is still pending; the owner’s existing installation has not been replaced. Details are recorded in [MANIFEST.md](MANIFEST.md). Physical output, device feedback and a fresh Mac installation remain separate checks; passing software tests does not establish those results.

Original firmware, foo2zjs source, licenses and research evidence remain included. See [NOTICE.md](NOTICE.md) and [REDISTRIBUTION.md](REDISTRIBUTION.md) for provenance.

The separate open firmware replacement under `analysis/` is unfinished and cannot print yet. These scripts do not install it.
