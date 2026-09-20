from __future__ import annotations

from pathlib import Path

from .scanner import FirmwareScanner
from .utils import first_non_empty, write_json, write_text

PROPERTY_KEYS = {
    "Device codename": ("ro.product.device", "ro.product.vendor.device", "ro.product.system.device"),
    "Brand": ("ro.product.brand", "ro.product.vendor.brand", "ro.product.system.brand"),
    "Manufacturer": ("ro.product.manufacturer", "ro.product.vendor.manufacturer"),
    "Model": ("ro.product.model", "ro.product.vendor.model", "ro.product.system.model"),
    "Android version": ("ro.build.version.release", "ro.system.build.version.release"),
    "SDK level": ("ro.build.version.sdk",),
    "Security patch": ("ro.build.version.security_patch", "ro.vendor.build.security_patch"),
    "Build fingerprint": ("ro.build.fingerprint", "ro.vendor.build.fingerprint", "ro.system.build.fingerprint"),
    "Build date": ("ro.build.date", "ro.system.build.date"),
    "Build type": ("ro.build.type",),
    "Build tags": ("ro.build.tags",),
    "Platform chipset": ("ro.board.platform", "ro.vendor.board.platform", "ro.soc.model"),
    "Vendor API level": ("ro.vendor.api_level", "ro.board.api_level"),
    "Shipping API level": ("ro.product.first_api_level", "ro.vendor.build.version.sdk"),
    "VNDK version": ("ro.vndk.version", "ro.product.vndk.version"),
    "Treble enabled": ("ro.treble.enabled",),
    "A/B update hint": ("ro.build.ab_update", "ro.virtual_ab.enabled", "ro.virtual_ab.compression.enabled"),
    "Dynamic partitions": ("ro.boot.dynamic_partitions", "ro.boot.dynamic_partitions_retrofit"),
}


def property_summary(dump: Path | str) -> dict[str, str]:
    scan = FirmwareScanner(dump).scan()
    props = scan.properties
    summary: dict[str, str] = {}
    for label, keys in PROPERTY_KEYS.items():
        summary[label] = first_non_empty(*(props.get(key) for key in keys), default="unknown")
    return summary


def build_properties_markdown(dump: Path | str) -> str:
    scan = FirmwareScanner(dump).scan()
    summary = property_summary(dump)
    lines = [
        "# Android Property Intelligence",
        "",
        f"Property files parsed: **{len(scan.property_files)}**",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(["", "## Source files", ""])
    if scan.property_files:
        lines.extend(f"- `{scan.rel(path)}`" for path in scan.property_files)
    else:
        lines.append("- No property files found.")
    lines.append("")
    return "\n".join(lines)


def write_properties_markdown(dump: Path | str, output: Path | str) -> dict[str, str]:
    write_text(Path(output), build_properties_markdown(dump))
    return property_summary(dump)


def write_properties_json(dump: Path | str, output: Path | str) -> dict[str, str]:
    summary = property_summary(dump)
    write_json(Path(output), summary)
    return summary

