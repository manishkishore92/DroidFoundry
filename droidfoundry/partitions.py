from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .scanner import FirmwareScanner
from .utils import file_size_human, relative_posix, write_text

KNOWN_IMAGES = (
    "boot.img",
    "vendor_boot.img",
    "recovery.img",
    "dtbo.img",
    "vbmeta.img",
    "vbmeta_system.img",
    "vbmeta_vendor.img",
    "super.img",
    "system.img",
    "vendor.img",
    "product.img",
    "system_ext.img",
    "odm.img",
    "payload.bin",
)


@dataclass(slots=True)
class PartitionEntry:
    name: str
    path: str
    size: int
    kind: str


def analyze_partitions(dump: Path | str) -> list[PartitionEntry]:
    scan = FirmwareScanner(dump).scan()
    entries: list[PartitionEntry] = []
    root = scan.root
    for image in scan.images:
        name = image.name.lower()
        if name in KNOWN_IMAGES or name.endswith(".img"):
            try:
                size = image.stat().st_size
            except OSError:
                size = 0
            entries.append(PartitionEntry(name=name, path=relative_posix(image, root), size=size, kind="image"))
    for part in scan.partitions:
        folder = root / part
        try:
            size = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
        except OSError:
            size = 0
        entries.append(PartitionEntry(name=part, path=part + "/", size=size, kind="folder"))
    return sorted(entries, key=lambda e: (e.kind, e.name, e.path))


def build_partition_report(dump: Path | str) -> str:
    scan = FirmwareScanner(dump).scan()
    entries = analyze_partitions(dump)
    image_names = {entry.name for entry in entries if entry.kind == "image"}
    has_dynamic = "super.img" in image_names or "system_ext" in scan.partitions
    fstab_text = "\n".join(p.read_text(encoding="utf-8", errors="replace").lower() for p in scan.fstab_files)
    has_ab = any(entry.name.endswith(("_a.img", "_b.img")) for entry in entries) or "slotselect" in fstab_text
    lines = [
        "# Partition Layout Report",
        "",
        f"Device: `{scan.metadata.device}`",
        f"Model: `{scan.metadata.model}`",
        f"Android: `{scan.metadata.android_version}`",
        "",
        "## Summary",
        "",
        f"- Dynamic partition hints: {'yes' if has_dynamic else 'not detected'}",
        f"- A/B partition hints: {'yes' if has_ab else 'not detected'}",
        f"- Image files detected: {sum(1 for e in entries if e.kind == 'image')}",
        f"- Extracted partition folders detected: {sum(1 for e in entries if e.kind == 'folder')}",
        "",
        "## Entries",
        "",
        "| Type | Name | Size | Path |",
        "| --- | --- | ---: | --- |",
    ]
    if not entries:
        lines.append("| - | No partition entries detected | - | - |")
    for entry in entries:
        lines.append(f"| {entry.kind} | `{entry.name}` | {file_size_human(entry.size)} | `{entry.path}` |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Review partition sizes from the real stock partition table before using them in BoardConfig.",
            "- Presence of `super.img` usually means dynamic partitions are involved.",
            "- A/B detection from filenames is only a hint and should be verified on-device.",
            "",
        ]
    )
    return "\n".join(lines)


def write_partition_report(dump: Path | str, output: Path | str) -> str:
    report = build_partition_report(dump)
    write_text(Path(output), report)
    return report
