from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from .scanner import FirmwareScanner
from .utils import relative_posix, safe_read_text, write_text


@dataclass(slots=True)
class HalEntry:
    file: str
    name: str
    version: str = "unknown"
    transport: str = "unknown"
    interfaces: list[str] = field(default_factory=list)


def _strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _child_text(node: ET.Element, name: str) -> str:
    for child in list(node):
        if _strip_ns(child.tag) == name and child.text:
            return child.text.strip()
    return "unknown"


def analyze_vintf(dump: Path | str) -> list[HalEntry]:
    scan = FirmwareScanner(dump).scan()
    entries: list[HalEntry] = []
    for xml_path in scan.vintf_files:
        text = safe_read_text(xml_path, limit=2_000_000)
        if not text.strip():
            continue
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            continue
        for hal in root.iter():
            if _strip_ns(hal.tag) != "hal":
                continue
            interfaces: list[str] = []
            for child in hal.iter():
                if _strip_ns(child.tag) == "name" and child.text and child is not hal:
                    # Interface names also use <name>; keep non-HAL names as interface hints.
                    value = child.text.strip()
                    if value and value != _child_text(hal, "name"):
                        interfaces.append(value)
            entries.append(
                HalEntry(
                    file=relative_posix(xml_path, scan.root),
                    name=_child_text(hal, "name"),
                    version=_child_text(hal, "version"),
                    transport=_child_text(hal, "transport"),
                    interfaces=sorted(set(interfaces)),
                )
            )
    return entries


def build_vintf_report(dump: Path | str) -> str:
    scan = FirmwareScanner(dump).scan()
    entries = analyze_vintf(dump)
    files = [relative_posix(p, scan.root) for p in scan.vintf_files]
    lines = [
        "# VINTF Report",
        "",
        f"Device: `{scan.metadata.device}`",
        f"Android: `{scan.metadata.android_version}`",
        "",
        "## VINTF files",
        "",
    ]
    if files:
        lines.extend(f"- `{path}`" for path in files)
    else:
        lines.append("- No VINTF XML files were detected.")
    lines.extend(["", "## HAL entries", "", "| HAL | Version | Transport | File |", "| --- | --- | --- | --- |"])
    if not entries:
        lines.append("| No HAL entries parsed | - | - | - |")
    for entry in entries:
        lines.append(f"| `{entry.name}` | `{entry.version}` | `{entry.transport}` | `{entry.file}` |")
    lines.extend(
        [
            "",
            "## Review notes",
            "",
            "- Parsed entries are hints from available XML files only.",
            "- Always compare against the ROM source compatibility matrix before finalizing device bring-up.",
            "- Missing HALs can also be declared through framework/device-side XML files outside the vendor partition.",
            "",
        ]
    )
    return "\n".join(lines)


def write_vintf_report(dump: Path | str, output: Path | str) -> str:
    report = build_vintf_report(dump)
    write_text(Path(output), report)
    return report

