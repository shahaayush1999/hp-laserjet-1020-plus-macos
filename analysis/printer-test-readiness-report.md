# HP 1020 Printer Test Readiness

This checkpoint records why the reverse-engineering work is now ready to move from offline static
analysis to controlled printer-side testing when the printer is connected.

## What Is Now Known

The normal print path is mapped end-to-end at the firmware level:

```text
host PostScript/PDF
  -> foo2zjs-wrapper
  -> PJL prefix + JZJZ ZjStream
  -> firmware parser 0x10009d34
  -> JobMgr queue id 3 messages
  -> 0x94 video/page work object
  -> work +0x50 raster list
  -> VideoThread / raw-band hardware feed
```

The key parser messages are known:

| Host ZjStream chunk | Firmware effect |
|---|---|
| `ZJT_START_DOC` | JobMgr message `1` |
| `ZJT_START_PAGE` | JobMgr messages `3` and `5`; creates page/work objects |
| `ZJT_JBIG_BIH` | JobMgr message `0x29`; seeds video hardware fields |
| `ZJT_JBIG_BID` | JobMgr message `0x2a`; appends raster data to `work +0x50` |
| `ZJT_END_JBIG` | JobMgr message `0x2b` |
| `ZJT_END_PAGE` | JobMgr message `6` |
| `ZJT_END_DOC` | JobMgr message `2` |

## Offline Sample

A controlled sample page exists at:

- `analysis/samples/minimal-page.ps`

Regenerate and inspect its HP1020 ZjStream stream with:

```sh
scripts/generate-zjs-sample.sh
```

That writes:

- `analysis/samples/generated/minimal-page-a4.zjs`
- `analysis/samples/generated/minimal-page-a4-zjs-report.md`

The current parsed sample report shows the exact expected HP1020 stream sequence:

```text
START_DOC
START_PAGE
JBIG_BIH
JBIG_BID
END_JBIG
END_PAGE
END_DOC
```

For the generated A4 sample:

- `JZJZ` starts at byte `0x10c`
- `ZJT_START_PAGE` has 13 items
- `ZJT_JBIG_BIH` has `XD=9600`, `YD=6824`, `L0=128`
- one `ZJT_JBIG_BID` chunk carries `6364` compressed raster bytes

## Printer-Side Test Command

When the printer is connected and powered on, run:

```sh
scripts/run-printer-readiness-test.sh --send
```

Without `--send`, the same script is safe as an offline dry run:

```sh
scripts/run-printer-readiness-test.sh
```

The send path uses the installed working print script:

```text
/Users/aayush/bin/hp1020-print -p a4 analysis/samples/minimal-page.ps
```

That means the printer test exercises the real deployed macOS path:

```text
firmware preload -> foo2zjs conversion -> CUPS USB backend send
```

## What To Look For During Printer Testing

Use the worker log as source of truth:

```sh
tail -100 /Library/Printers/hp1020/spool-worker.log
```

Expected high-level result:

- firmware preload either succeeds or times out harmlessly after upload
- document conversion completes
- the sample page prints
- CUPS queue does not stay paused
- worker log does not show a failed conversion or failed USB backend send

If the page prints, the static parser/video mapping has enough coverage for the real path. The next
experiments should then mutate one variable at a time in the generated stream or wrapper options:

- A4 versus letter
- 600 dpi versus 1200x600
- altered page dimensions
- small versus larger raster payloads

## Remaining Offline Unknowns

The remaining unknowns are no longer blockers to printer testing:

- exact semantics of `work +0x84/+0x88/+0x8c/+0x90`
- exact semantics of raster payload `+0x20/+0x48/+0x4c/+0x50/+0x54`
- exact MMIO register names for the video/raw-band hardware path

Those can be refined after the controlled sample is tested on the actual printer.
