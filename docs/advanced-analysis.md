# Advanced analysis

DroidFoundry includes commands for deeper Android bring-up analysis beyond basic firmware scanning.

## Firmware dump doctor

Use the doctor command before generating files:

```bash
droidfoundry doctor ./firmware-dump
```

The doctor checks whether the dump contains useful bring-up inputs such as property files, vendor data, boot images, VINTF files, init scripts, fstab files, permission XML files, firmware files and candidate proprietary blobs.

A warning does not always mean the dump is unusable. Some devices do not expose every file in the same place. Treat warnings as review points.

## Grouped proprietary files

Use grouped blob classification when preparing `proprietary-files.txt`:

```bash
droidfoundry classify-blobs ./firmware-dump --output proprietary-files.txt
```

DroidFoundry groups entries by likely hardware area so the list is easier to review.

The classifier uses path and filename hints. It is not a substitute for maintainer review.

## BoardConfig hints

Generate reviewable BoardConfig hints:

```bash
droidfoundry boardconfig ./firmware-dump --output BoardConfig.hints.mk
```

This file is not meant to be copied blindly. It gives values that should be checked against the stock firmware, kernel source, ROM source and real device behavior.

## VINTF report

Generate a VINTF report:

```bash
droidfoundry vintf ./firmware-dump --output vintf-report.md
```

The report lists VINTF files and HAL declarations that could be parsed from XML files.

## Init and fstab report

Generate an init/fstab report:

```bash
droidfoundry init-scan ./firmware-dump --output init-fstab-report.md
```

Use this report when reviewing vendor daemons, mount points, encryption flags, verity flags and logical partition hints.

## Device tree inspection

Inspect an existing tree:

```bash
droidfoundry inspect-tree ./device/xiaomi/sweet --output tree-report.md
```

This helps identify missing files and review points before building.
