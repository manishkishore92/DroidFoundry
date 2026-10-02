<div align="center">

# DroidFoundry

### Firmware intelligence and Android device bring-up automation toolkit

DroidFoundry is a Python CLI toolkit for Android ROM maintainers, kernel developers and device tree developers. It scans extracted firmware dumps, detects device information, classifies proprietary blobs, generates starter bring-up files, inspects existing trees, compares firmware updates, finds likely bring-up issues and produces maintainer-ready reports.

<br>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Typer](https://img.shields.io/badge/CLI-Typer-111827?style=for-the-badge)
![Rich](https://img.shields.io/badge/Terminal-Rich-4B5563?style=for-the-badge)
![Android](https://img.shields.io/badge/Android-ROM%20Bring--up-3DDC84?style=for-the-badge&logo=android&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

</div>

---

## What DroidFoundry does

Android device bring-up usually starts with an extracted stock firmware dump. That dump may contain thousands of files across `system`, `vendor`, `product`, `odm`, `system_ext`, boot images, VINTF files, init scripts, fstab files, firmware blobs, vendor libraries, permissions XML files and build properties.

Before writing a proper device tree, maintainers need answers to practical questions:

- What device, brand, model, platform and Android build was detected?
- Which partitions, images and ramdisk-related files are available?
- Which blobs look like camera, audio, display, radio, Wi-Fi, GPS, sensor or firmware files?
- Are VINTF manifests and compatibility matrices present?
- Which init services and fstab mount flags are visible?
- What BoardConfig values can be safely suggested as review hints?
- What changed between two firmware dumps?
- Does an existing device tree contain the expected files?
- What is missing before a first ROM bring-up attempt?

DroidFoundry automates the inspection work and writes structured outputs that a maintainer can review, edit and continue from.

DroidFoundry does **not** claim to create a complete booting ROM tree automatically. It creates strong starter files, reports and warnings so real maintainer work can move faster.

---

## Core features

### Firmware dump scanner

Scans extracted firmware folders and detects:

- Device brand, manufacturer, model and codename
- Android version, SDK level and security patch
- Vendor security patch
- Build ID, type, tags and fingerprint
- Platform / chipset hints
- Property files
- Partition folders
- Android image files
- VINTF XML files
- Init `.rc` files
- Fstab files
- SELinux policy folders
- File statistics and warnings

### Firmware dump doctor

Checks whether a dump has enough useful data for bring-up work.

It checks important inputs such as:

- `build.prop` and partition property files
- Vendor partition data
- `boot.img`, `vendor_boot.img`, `dtbo.img` and `vbmeta.img`
- VINTF XML files
- Init scripts
- Fstab files
- Permission XML files
- Firmware-like files
- Candidate proprietary blobs

Each check returns `OK`, `WARN` or `FAIL` with a direct fix suggestion.

### Bring-up readiness score

DroidFoundry can calculate a readiness score from dump quality.

The score covers:

- Build properties
- Vendor blobs
- Partitions and images
- VINTF files
- Init, fstab and sepolicy data
- Kernel and boot hints
- Generation readiness

This gives maintainers a fast way to understand whether the dump is usable or missing major pieces.

### Issue detection engine

DroidFoundry detects common bring-up blockers and writes them as Markdown or JSON.

Examples:

- Missing vendor partition data
- Missing boot or vendor boot image
- Missing VINTF files
- Missing init or fstab files
- No candidate blobs detected
- Missing hardware blob categories
- Suspicious empty files
- Broken symlinks
- Repeated blob names that need review

Issues are grouped by priority: `HIGH`, `MEDIUM` and `LOW`.

### Android property intelligence

Parses build properties and summarizes values useful during ROM bring-up:

- Device codename
- Brand and manufacturer
- Model
- Android release and SDK
- Security patch
- Build fingerprint
- Build date
- Build type and tags
- Platform / chipset hints
- Vendor API level
- Shipping API level
- Treble hints
- Dynamic partition hints
- A/B update hints
- VNDK version

### Hardware map

Combines VINTF declarations and blob classification to create a hardware support map.

Hardware areas include:

- Camera
- Audio
- Bluetooth
- Wi-Fi
- GPS
- Sensors
- Fingerprint
- NFC
- DRM
- Graphics
- Radio
- Power

The hardware map is a bring-up hint. It does not guarantee that a hardware feature works, but it helps maintainers quickly see what is visible in the dump.

### Grouped proprietary blob generator

Generates a candidate `proprietary-files.txt` and groups entries by likely hardware area.

Example groups:

- Camera
- Audio
- Display
- Graphics
- Bluetooth
- Wi-Fi
- Radio
- GPS
- Sensors
- Fingerprint
- NFC
- Power
- Thermal
- Media
- DRM
- VINTF and permissions
- Init and fstab
- Firmware
- Apps and framework

The output is easier to review than one long flat file.

### Device tree skeleton generator

Generates a starter Android device/vendor workspace containing:

- `AndroidProducts.mk`
- `BoardConfig.mk`
- `device.mk`
- ROM product makefile
- `vendorsetup.sh`
- `extract-files.sh`
- `setup-makefiles.sh`
- `proprietary-files.txt`
- Device README
- Starter vendor makefile
- Local manifest
- Scan metadata JSON
- Bring-up reports

Generated files are conservative and include review comments where values need maintainer confirmation.

### BoardConfig hint generator

Creates a reviewable `BoardConfig.hints.mk` using firmware metadata.

It can suggest:

- `BOARD_VENDOR`
- `TARGET_BOOTLOADER_BOARD_NAME`
- `TARGET_OTA_ASSERT_DEVICE`
- `TARGET_BOARD_PLATFORM`
- Partition output paths
- Dynamic partition hints
- A/B OTA hints
- Vendor boot hints
- Shipping API level hints

The file is a hint file, not a drop-in final BoardConfig.

### Partition analyzer

Creates a partition report from extracted folders and image files.

It detects:

- `boot.img`
- `vendor_boot.img`
- `dtbo.img`
- `vbmeta.img`
- `super.img`
- `system.img`
- `vendor.img`
- `product.img`
- `odm.img`
- `system_ext.img`
- Extracted partition folders
- Dynamic partition hints
- A/B partition hints

### VINTF analyzer

Scans VINTF XML files and extracts HAL information where possible.

It reports:

- VINTF files found
- HAL names
- HAL versions
- Transport type
- Source XML file
- Review notes for compatibility matrix work

### Init and fstab scanner

Scans init scripts and fstab files to help understand vendor services and mount behavior.

It reports:

- Init `.rc` files
- Parsed service names
- Service commands
- Fstab mount points
- Block devices
- File systems
- Mount flags
- Encryption / verity / logical partition hints where visible

### Device tree inspector

Inspects an existing Android device tree and highlights missing or review-worthy parts.

It checks for:

- `AndroidProducts.mk`
- `BoardConfig.mk`
- `device.mk`
- `vendorsetup.sh`
- `extract-files.sh`
- `setup-makefiles.sh`
- `proprietary-files.txt`
- ROM product makefile
- Sepolicy folders
- Overlay folders
- Rootdir / ramdisk folders
- Kernel path hints
- Vendor path hints
- Dynamic partition flags
- A/B OTA flags
- Recovery fstab files

### Safe tree updater and patch system

DroidFoundry can update generated files in an existing tree with backups, or create reviewable patch files instead of editing the tree directly.

Patch output can include:

- Updated `proprietary-files.txt`
- BoardConfig hint file
- Maintainer report

This makes changes easier to review before applying them.

### Firmware comparison and update assistant

Compares two firmware dumps and reports:

- Metadata changes
- Added blobs
- Removed blobs
- Changed common blobs
- Added / removed image files
- Added / removed VINTF files
- Added / removed init files
- Recommended maintainer actions for firmware updates

This is useful when updating proprietary blobs from a newer stock firmware release.

### Full intelligence report

The `intelligence` command runs the full analysis pipeline and creates a complete report folder.

It generates:

- Device summary
- Property report
- Bring-up readiness score
- Issue report
- Hardware map
- Partition report
- VINTF report
- Init/fstab report
- BoardConfig hints
- Grouped proprietary blob list
- Local manifest
- Offline HTML report
- JSON automation files
- ROM Harbor export
- Android ES export

### Offline HTML report

DroidFoundry can generate a standalone `index.html` report with:

- Device summary
- Readiness score
- Hardware map
- Detected issues
- Recommended next steps

It works without a server and can be shared with other maintainers.

### Exports for maintainer workflows

DroidFoundry can export data for related Android maintainer tools:

- ROM Harbor device metadata
- ROM Harbor hardware map
- ROM Harbor release notes
- Android ES profile
- Android ES report

---

## Installation

Clone the repository:

```bash
git clone https://github.com/manishkishore92/DroidFoundry.git
cd DroidFoundry
```

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install DroidFoundry:

```bash
pip install -e .
```

Check the CLI:

```bash
droidfoundry --help
```

Short alias:

```bash
dfoundry --help
```

---

## Quick start

Run the interactive wizard:

```bash
droidfoundry wizard
```

Or run a full intelligence report:

```bash
droidfoundry intelligence ./firmware-dump --output foundry-report
```

Open the generated HTML report:

```text
foundry-report/index.html
```

---

## Common commands

### Scan a firmware dump

```bash
droidfoundry scan ./firmware-dump --show-files
```

### Check dump quality

```bash
droidfoundry doctor ./firmware-dump
```

### Calculate readiness score

```bash
droidfoundry score ./firmware-dump --output bringup-score.md --json-out bringup-score.json
```

### Detect likely bring-up issues

```bash
droidfoundry issues ./firmware-dump --output issues.md --json-out issues.json
```

### Show Android property intelligence

```bash
droidfoundry props ./firmware-dump --output properties.md --json-out properties.json
```

### Generate hardware map

```bash
droidfoundry hardware ./firmware-dump --output hardware-map.md --json-out hardware-map.json
```

### Generate grouped proprietary files

```bash
droidfoundry classify-blobs ./firmware-dump --output proprietary-files.txt
```

### Generate BoardConfig hints

```bash
droidfoundry boardconfig ./firmware-dump --output BoardConfig.hints.mk
```

### Generate partition report

```bash
droidfoundry partitions ./firmware-dump --output partition-report.md
```

### Generate VINTF report

```bash
droidfoundry vintf ./firmware-dump --output vintf-report.md
```

### Generate init/fstab report

```bash
droidfoundry init-scan ./firmware-dump --output init-fstab-report.md
```

### Generate offline HTML report

```bash
droidfoundry html-report ./firmware-dump --output foundry-report.html
```

### Generate a local manifest

```bash
droidfoundry manifest \
  --github manishkishore92 \
  --brand xiaomi \
  --device sweet \
  --branch lineage-22.2 \
  --output roomservice.xml
```

### Generate a complete starter workspace

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

### Inspect an existing device tree

```bash
droidfoundry inspect-tree ./device/xiaomi/sweet --output tree-report.md
```

### Create reviewable patches for an existing tree

```bash
droidfoundry patch ./firmware-dump --tree ./device/xiaomi/sweet --output patches
```

### Update generated files in an existing tree

```bash
droidfoundry update ./firmware-dump --tree ./device/xiaomi/sweet --yes
```

### Compare two firmware dumps

```bash
droidfoundry compare ./old-firmware ./new-firmware --output firmware-compare.md
```

### Run firmware update assistant

```bash
droidfoundry update-assistant ./old-firmware ./new-firmware --output firmware-update-assistant.md
```

### Export for ROM Harbor

```bash
droidfoundry export-rom-harbor ./firmware-dump --output rom-harbor-export
```

### Export for Android ES

```bash
droidfoundry export-android-es ./firmware-dump --output android-es-export --rom lineage
```

---

## Intelligence report output

The full report command creates a structured folder:

```text
foundry-report/
├── README.md
├── index.html
├── summary.json
├── device-summary.md
├── properties.md
├── properties.json
├── bringup-score.md
├── bringup-score.json
├── issues.md
├── issues.json
├── hardware-map.md
├── hardware-map.json
├── partition-report.md
├── vintf-report.md
├── init-fstab-report.md
├── BoardConfig.hints.mk
├── proprietary-files.txt
├── roomservice.xml
└── exports/
    ├── android-es/
    │   ├── android-es-profile.conf
    │   └── android-es-report.md
    └── rom-harbor/
        ├── rom-harbor-device.json
        ├── rom-harbor-hardware-map.json
        └── rom-harbor-release-notes.md
```

---

## Generated workspace

The `generate` command creates a starter bring-up workspace:

```text
foundry-output/
├── .repo/
│   └── local_manifests/
│       └── roomservice.xml
├── device/
│   └── xiaomi/
│       └── sweet/
│           ├── AndroidProducts.mk
│           ├── BoardConfig.mk
│           ├── device.mk
│           ├── lineage_sweet.mk
│           ├── vendorsetup.sh
│           ├── extract-files.sh
│           ├── setup-makefiles.sh
│           ├── proprietary-files.txt
│           └── README.md
├── vendor/
│   └── xiaomi/
│       └── sweet/
│           └── sweet-vendor.mk
├── metadata/
│   └── scan.json
└── reports/
    ├── BoardConfig.hints.mk
    ├── bringup-report.md
    ├── init-fstab-report.md
    ├── partition-report.md
    └── vintf-report.md
```

---

## Configuration

Create a starter config file:

```bash
droidfoundry init
```

This writes `foundry.yml`:

```yaml
project:
  brand: xiaomi
  device: sweet
  vendor: xiaomi
  rom: lineage
  branch: lineage-22.2
  github: manishkishore92
  output: foundry-output
```

Use it with:

```bash
droidfoundry generate ./firmware-dump --config foundry.yml
```

Command-line options override config values.

---

## Firmware dump expectations

DroidFoundry works best with an extracted dump containing paths like:

```text
system/build.prop
vendor/build.prop
product/build.prop
odm/build.prop
system_ext/build.prop
vendor/etc/vintf/
vendor/etc/init/
vendor/etc/permissions/
vendor/lib/
vendor/lib64/
vendor/bin/
vendor/firmware/
boot.img
vendor_boot.img
dtbo.img
vbmeta.img
super.img
```

Partial dumps are supported, but fewer files means fewer hints and a lower readiness score.

---

## Command reference

| Command | Purpose |
| --- | --- |
| `init` | Create a starter `foundry.yml` config |
| `wizard` | Interactive bring-up workspace generator |
| `scan` | Scan firmware dump metadata and structure |
| `doctor` | Check firmware dump quality and missing inputs |
| `score` | Calculate bring-up readiness score |
| `issues` | Detect likely bring-up blockers |
| `props` | Summarize Android build properties |
| `hardware` | Generate hardware map from blobs and VINTF |
| `blobs` | Preview or write candidate proprietary files |
| `classify-blobs` | Write grouped proprietary files by hardware area |
| `boardconfig` | Generate reviewable BoardConfig hints |
| `partitions` | Generate partition layout report |
| `vintf` | Generate VINTF HAL report |
| `init-scan` | Generate init service and fstab report |
| `inspect-tree` | Inspect an existing Android device tree |
| `patch` | Create reviewable patches for an existing tree |
| `update` | Safely update generated files in an existing tree |
| `compare` | Compare two firmware dumps |
| `update-assistant` | Compare firmware updates and recommend maintainer actions |
| `manifest` | Generate local manifest XML |
| `report` | Generate Markdown bring-up report |
| `html-report` | Generate standalone offline HTML report |
| `intelligence` | Run the full report and export pipeline |
| `export-rom-harbor` | Export metadata for ROM Harbor |
| `export-android-es` | Export profile data for Android ES |
| `generate` | Generate starter device/vendor workspace |
| `inspect` | Print full scan JSON to terminal |

---

## Project structure

```text
DroidFoundry/
├── droidfoundry/
│   ├── cli.py
│   ├── scanner.py
│   ├── doctor.py
│   ├── scoring.py
│   ├── issues.py
│   ├── hardware.py
│   ├── properties_intel.py
│   ├── html_report.py
│   ├── exporters.py
│   ├── patcher.py
│   ├── blobs.py
│   ├── classifier.py
│   ├── boardconfig.py
│   ├── partitions.py
│   ├── vintf.py
│   ├── init_scan.py
│   ├── tree_inspector.py
│   ├── updater.py
│   ├── compare.py
│   ├── wizard.py
│   ├── generators.py
│   ├── manifest.py
│   ├── report.py
│   ├── properties.py
│   ├── config.py
│   ├── models.py
│   ├── utils.py
│   └── templates/
├── docs/
├── examples/
├── tests/
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Important notes

DroidFoundry is a bring-up assistant, not an automatic ROM porter.

Generated files need manual review. Device trees require knowledge of the target ROM source, kernel source, partition layout, SELinux policy, init behavior, VINTF requirements, proprietary blobs and real-device testing.

Use DroidFoundry to speed up inspection, reporting and starter-file generation. Continue the real maintainer work carefully.

---

## Development

Install development tools:

```bash
pip install -e . pytest
```

Run tests:

```bash
pytest
```

Run the CLI locally:

```bash
python -m droidfoundry --help
```

---

## Maintainer

Created and maintained by **Manish Kishore**.

GitHub: [@manishkishore92](https://github.com/manishkishore92)

---

<div align="center">

**DroidFoundry**  
Firmware intelligence for Android ROM bring-up.

</div>
