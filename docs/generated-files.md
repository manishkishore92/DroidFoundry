# Generated files

The `generate` command creates a starter bring-up workspace.

```text
foundry-output/
├── .repo/local_manifests/roomservice.xml
├── device/<vendor>/<device>/
│   ├── AndroidProducts.mk
│   ├── BoardConfig.mk
│   ├── device.mk
│   ├── <rom>_<device>.mk
│   ├── vendorsetup.sh
│   ├── extract-files.sh
│   ├── setup-makefiles.sh
│   ├── proprietary-files.txt
│   └── README.md
├── vendor/<vendor>/<device>/
│   └── <device>-vendor.mk
├── metadata/
│   └── scan.json
└── reports/
    ├── BoardConfig.hints.mk
    ├── bringup-report.md
    ├── init-fstab-report.md
    ├── partition-report.md
    └── vintf-report.md
```

## Device tree files

The generated device tree files are intentionally conservative. They are starter files for a maintainer to review and expand.

## Proprietary files

`proprietary-files.txt` is grouped by likely hardware area. It is still a candidate list and should be reviewed before use.

## Reports

The reports folder contains metadata and analysis useful during bring-up:

- `bringup-report.md` gives a general maintainer summary.
- `BoardConfig.hints.mk` suggests reviewable BoardConfig values.
- `partition-report.md` summarizes partitions and images.
- `vintf-report.md` summarizes VINTF files and HAL entries.
- `init-fstab-report.md` summarizes init services and fstab entries.

## Metadata

`scan.json` contains structured scan data that can be used by scripts or other tools.
