# Intelligence Report

The intelligence report is the fastest way to run DroidFoundry on a firmware dump.

```bash
droidfoundry intelligence ./firmware-dump --output foundry-report
```

It creates Markdown reports, JSON automation data, an offline HTML report, BoardConfig hints, a grouped proprietary blob list, local manifest XML, and exports for ROM Harbor and Android ES.

## Output

```text
foundry-report/
├── index.html
├── summary.json
├── device-summary.md
├── properties.md
├── bringup-score.md
├── issues.md
├── hardware-map.md
├── partition-report.md
├── vintf-report.md
├── init-fstab-report.md
├── BoardConfig.hints.mk
├── proprietary-files.txt
├── roomservice.xml
└── exports/
```

`index.html` is a standalone report that can be opened locally and shared with other maintainers.

