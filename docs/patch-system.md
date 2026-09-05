# Patch System

The patch command creates reviewable unified diff files instead of directly editing an existing device tree.

```bash
droidfoundry patch ./firmware-dump --tree ./device/xiaomi/sweet --output patches
```

Patch files may include updates for:

- `proprietary-files.txt`
- `BoardConfig.hints.mk`
- `DROIDFOUNDRY-REPORT.md`

Generated patches are starter suggestions. Review them before applying anything to a production device tree.
