# DroidFoundry Usage

DroidFoundry is a CLI toolkit for Android firmware dump inspection, bring-up file generation, issue detection and maintainer reporting.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Check the CLI:

```bash
droidfoundry --help
```

## Recommended flow

Start with a full intelligence report:

```bash
droidfoundry intelligence ./firmware-dump --output foundry-report
```

Then open:

```text
foundry-report/index.html
```

Use the Markdown and JSON files for device tree review, ROM Harbor export, Android ES profile export and automation.

## Quick inspection commands

```bash
droidfoundry scan ./firmware-dump --show-files
droidfoundry doctor ./firmware-dump
droidfoundry score ./firmware-dump
droidfoundry issues ./firmware-dump
droidfoundry props ./firmware-dump
droidfoundry hardware ./firmware-dump
```

## Generate useful files

```bash
droidfoundry classify-blobs ./firmware-dump -o proprietary-files.txt
droidfoundry boardconfig ./firmware-dump -o BoardConfig.hints.mk
droidfoundry partitions ./firmware-dump -o partition-report.md
droidfoundry vintf ./firmware-dump -o vintf-report.md
droidfoundry init-scan ./firmware-dump -o init-fstab-report.md
droidfoundry html-report ./firmware-dump -o foundry-report.html
```

## Generate a starter workspace

```bash
droidfoundry generate ./firmware-dump \
  --brand xiaomi \
  --device sweet \
  --vendor xiaomi \
  --rom lineage \
  --branch lineage-22.2 \
  --github manishkishore92 \
  --output foundry-output
```

## Work with existing trees

Inspect an existing device tree:

```bash
droidfoundry inspect-tree ./device/xiaomi/sweet -o tree-report.md
```

Create reviewable patches:

```bash
droidfoundry patch ./firmware-dump --tree ./device/xiaomi/sweet -o patches
```

Update generated files directly with backups:

```bash
droidfoundry update ./firmware-dump --tree ./device/xiaomi/sweet --yes
```

## Compare firmware dumps

```bash
droidfoundry compare ./old-firmware ./new-firmware -o firmware-compare.md
droidfoundry update-assistant ./old-firmware ./new-firmware -o firmware-update-assistant.md
```

## Export data

```bash
droidfoundry export-rom-harbor ./firmware-dump -o rom-harbor-export
droidfoundry export-android-es ./firmware-dump -o android-es-export --rom lineage
```
