from __future__ import annotations

from pathlib import Path

from .boardconfig import write_boardconfig_hints
from .classifier import write_grouped_blobs
from .exporters import export_android_es, export_rom_harbor
from .hardware import write_hardware_json, write_hardware_markdown
from .html_report import write_html_report
from .init_scan import write_init_report
from .issues import write_issues_json, write_issues_markdown
from .manifest import ManifestInput, write_manifest
from .partitions import write_partition_report
from .properties_intel import write_properties_json, write_properties_markdown
from .report import write_report
from .scanner import FirmwareScanner
from .scoring import write_score_json, write_score_markdown
from .utils import normalize_name, write_json, write_text
from .vintf import write_vintf_report


def run_intelligence_report(
    dump: Path | str,
    output: Path | str,
    github: str = "manishkishore92",
    rom: str = "lineage",
    branch: str = "lineage-22.2",
) -> list[Path]:
    out = Path(output).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    scan = FirmwareScanner(dump).scan()
    brand = normalize_name(scan.metadata.brand)
    device = normalize_name(scan.metadata.device)
    files: list[Path] = []

    writers = [
        (out / "device-summary.md", lambda p: write_report(dump, p)),
        (out / "properties.md", lambda p: write_properties_markdown(dump, p)),
        (out / "properties.json", lambda p: write_properties_json(dump, p)),
        (out / "bringup-score.md", lambda p: write_score_markdown(dump, p)),
        (out / "bringup-score.json", lambda p: write_score_json(dump, p)),
        (out / "issues.md", lambda p: write_issues_markdown(dump, p)),
        (out / "issues.json", lambda p: write_issues_json(dump, p)),
        (out / "hardware-map.md", lambda p: write_hardware_markdown(dump, p)),
        (out / "hardware-map.json", lambda p: write_hardware_json(dump, p)),
        (out / "partition-report.md", lambda p: write_partition_report(dump, p)),
        (out / "vintf-report.md", lambda p: write_vintf_report(dump, p)),
        (out / "init-fstab-report.md", lambda p: write_init_report(dump, p)),
        (out / "BoardConfig.hints.mk", lambda p: write_boardconfig_hints(dump, p, brand=brand, device=device)),
        (out / "proprietary-files.txt", lambda p: write_grouped_blobs(dump, p)),
        (out / "index.html", lambda p: write_html_report(dump, p)),
    ]
    for target, func in writers:
        func(target)
        files.append(target)

    manifest_path = out / "roomservice.xml"
    write_manifest(ManifestInput(github=github, brand=brand, device=device, branch=branch), manifest_path)
    files.append(manifest_path)

    summary = {
        "device": device,
        "brand": brand,
        "model": scan.metadata.model,
        "android_version": scan.metadata.android_version,
        "security_patch": scan.metadata.security_patch,
        "files": [path.name for path in files],
    }
    write_json(out / "summary.json", summary)
    files.append(out / "summary.json")

    exported_rh = export_rom_harbor(dump, out / "exports" / "rom-harbor")
    exported_aes = export_android_es(dump, out / "exports" / "android-es", rom=rom)
    files.extend(exported_rh + exported_aes)

    readme = [
        "# DroidFoundry Intelligence Report",
        "",
        f"Device: `{device}`",
        f"Brand: `{brand}`",
        f"Android: `{scan.metadata.android_version}`",
        "",
        "Open `index.html` for the offline visual report. Use the Markdown and JSON files for maintainer workflows and automation.",
        "",
    ]
    write_text(out / "README.md", "\n".join(readme))
    files.append(out / "README.md")
    return files
