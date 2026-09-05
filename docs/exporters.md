# Exporters

DroidFoundry can export firmware intelligence to other maintainer workflows.

## ROM Harbor

```bash
droidfoundry export-rom-harbor ./firmware-dump --output rom-harbor-export
```

Creates:

- `rom-harbor-device.json`
- `rom-harbor-hardware-map.json`
- `rom-harbor-release-notes.md`

## Android ES

```bash
droidfoundry export-android-es ./firmware-dump --output android-es-export --rom lineage
```

Creates:

- `android-es-profile.conf`
- `android-es-report.md`

Use these files as starting points for release dashboards and Android build workflow tools.
