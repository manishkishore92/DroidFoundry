from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .scanner import FirmwareScanner
from .utils import relative_posix, safe_read_text, write_text


@dataclass(slots=True)
class FstabEntry:
    file: str
    mount_point: str
    block_device: str
    fs_type: str
    flags: str


@dataclass(slots=True)
class InitService:
    file: str
    name: str
    command: str


def parse_fstab_line(line: str) -> tuple[str, str, str, str] | None:
    clean = line.strip()
    if not clean or clean.startswith("#"):
        return None
    parts = re.split(r"\s+", clean)
    if len(parts) < 4:
        return None
    return parts[0], parts[1], parts[2], ",".join(parts[3:])


def analyze_init_and_fstab(dump: Path | str) -> tuple[list[InitService], list[FstabEntry]]:
    scan = FirmwareScanner(dump).scan()
    services: list[InitService] = []
    fstabs: list[FstabEntry] = []
    for path in scan.init_files:
        for line in safe_read_text(path, limit=2_000_000).splitlines():
            stripped = line.strip()
            if stripped.startswith("service "):
                parts = stripped.split(None, 2)
                if len(parts) >= 3:
                    services.append(InitService(relative_posix(path, scan.root), parts[1], parts[2]))
    for path in scan.fstab_files:
        for line in safe_read_text(path, limit=2_000_000).splitlines():
            parsed = parse_fstab_line(line)
            if parsed:
                block, mount, fs_type, flags = parsed
                fstabs.append(FstabEntry(relative_posix(path, scan.root), mount, block, fs_type, flags))
    return services, fstabs


def build_init_report(dump: Path | str) -> str:
    scan = FirmwareScanner(dump).scan()
    services, fstabs = analyze_init_and_fstab(dump)
    lines = [
        "# Init and Fstab Report",
        "",
        f"Device: `{scan.metadata.device}`",
        f"Android: `{scan.metadata.android_version}`",
        "",
        "## Init files",
        "",
    ]
    if scan.init_files:
        lines.extend(f"- `{relative_posix(path, scan.root)}`" for path in scan.init_files)
    else:
        lines.append("- No init rc files were detected.")
    lines.extend(["", "## Services", "", "| Service | Command | File |", "| --- | --- | --- |"])
    if not services:
        lines.append("| No services parsed | - | - |")
    for service in services[:120]:
        lines.append(f"| `{service.name}` | `{service.command}` | `{service.file}` |")
    if len(services) > 120:
        lines.append(f"| ... | {len(services) - 120} more services | - |")
    lines.extend(["", "## Fstab entries", "", "| Mount point | Block device | FS | Flags | File |", "| --- | --- | --- | --- | --- |"])
    if not fstabs:
        lines.append("| No fstab entries parsed | - | - | - | - |")
    for entry in fstabs:
        lines.append(f"| `{entry.mount_point}` | `{entry.block_device}` | `{entry.fs_type}` | `{entry.flags}` | `{entry.file}` |")
    lines.extend(
        [
            "",
            "## Bring-up notes",
            "",
            "- Review encryption, verity and logical partition flags carefully before copying values into a device tree.",
            "- Init services can reveal required vendor daemons, permissions and sepolicy work.",
            "",
        ]
    )
    return "\n".join(lines)


def write_init_report(dump: Path | str, output: Path | str) -> str:
    report = build_init_report(dump)
    write_text(Path(output), report)
    return report
