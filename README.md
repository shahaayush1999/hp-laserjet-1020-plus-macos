# HP LaserJet 1020 Plus on macOS

Print over USB from an Apple Silicon Mac using the original HP firmware and foo2zjs. This is an unofficial compatibility setup.

## Install

Connect the printer by USB, turn it on, and run:

```sh
git clone --depth 1 https://github.com/shahaayush1999/hp-laserjet-1020-plus-macos.git
cd hp-laserjet-1020-plus-macos
zsh scripts/install.sh
```

The script installs Homebrew if needed, downloads Ghostscript, GNU sed and Python, builds the printer helper, and sets up the printer. Follow the Homebrew prompts and enter your Mac administrator password when asked. An internet connection is required.

If macOS first asks to install Apple's Command Line Tools when you run `git`, complete that installation and run the commands again. Use a macOS version [supported by Homebrew](https://docs.brew.sh/Installation#macos-requirements).

Once installed, print from any app and select **HP LaserJet 1020 Plus**. Choose **A4** or **US Letter** to match your paper. Copies, selected pages, page order and pages per sheet use the normal Mac print settings.

Jobs stay in the Mac's queue while being prepared and sent. The worker also reads printer feedback for paper, cover and jam messages, and waits for completion when the printer provides it. If that feedback is unavailable, it explicitly reports that physical completion is unconfirmed. Paper alerts and completion feedback still need verification on the actual printer; the automated tests simulate those responses.

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

The installer remembers which packages it originally added, including across reinstalls. It checks that the new background service starts before finishing and restores the previous printer files if replacement fails. It does not require you to keep a separate cleanup file.

## Troubleshooting

Check that the printer is on, connected by a data-capable USB cable/adapter, and allowed as a USB accessory in macOS. Keep any Terminal error message.

```sh
zsh scripts/print-test.sh   # prints a test page
zsh scripts/diagnose.sh    # checks software and the queue; does not contact USB
```

You can cancel waiting or active jobs from the Mac's print queue. Cancellation cannot undo pages already printed. If a transfer fails after some data was sent, the job is held instead of automatically printing again. Check for partially printed pages before resuming it. An unplugged printer can be reconnected without submitting the job again.

If installation or cleanup fails, rerun the corresponding script after addressing the error. Cleanup retains its package record when it fails so it can be retried.

## Scope

This uses the working HP-based printing approach. Automated checks run real macOS document filters and conversion software, including multi-page copies, and simulate printer failures, feedback, cancellation, installation and removal. This revision has also been installed and started successfully on one Apple Silicon Mac, with four-copy conversion checked through its installed filters. Physical output, Mac print-queue UI behavior and a fresh Mac installation remain unverified. Your Mac's existing printing setup is changed only when you run the scripts.

The original firmware, foo2zjs source and research evidence remain in the repository. Supporting software comes from Homebrew instead of a bundled software archive. See [NOTICE.md](NOTICE.md), [REDISTRIBUTION.md](REDISTRIBUTION.md) and [MANIFEST.md](MANIFEST.md) for provenance.

The separate open firmware replacement under `analysis/` is unfinished and cannot print yet. These scripts do not install it.
