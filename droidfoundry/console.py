from __future__ import annotations

from pathlib import Path
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import FirmwareScan
from .utils import file_size_human, relative_posix

console = Console()


def print_scan_summary(scan: FirmwareScan) -> None:
    meta = scan.metadata
    table = Table(title="Firmware scan summary", show_lines=False)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", overflow="fold")
    rows = [
        ("Brand", meta.brand),
        ("Manufacturer", meta.manufacturer),
        ("Device", meta.device),
        ("Model", meta.model),
        ("Android", meta.android_version),
        ("SDK", meta.sdk),
        ("Security patch", meta.security_patch),
        ("Vendor patch", meta.vendor_security_patch),
        ("Build ID", meta.build_id),
        ("Build type", meta.build_type),
        ("Platform", meta.platform),
        ("Fingerprint", meta.fingerprint),
        ("Partitions", ", ".join(scan.partitions) if scan.partitions else "none"),
        ("Images", str(len(scan.images))),
        ("VINTF files", str(len(scan.vintf_files))),
        ("Candidate files", str(scan.stats.total_files)),
        ("Dump size", file_size_human(scan.stats.total_size)),
    ]
    for key, value in rows:
        table.add_row(key, value)
    console.print(table)

    if scan.warnings:
        console.print(Panel("\n".join(f"- {w}" for w in scan.warnings), title="Warnings", style="yellow"))


def print_paths(title: str, paths: Iterable[Path], root: Path, limit: int = 20) -> None:
    rows = list(paths)
    table = Table(title=title)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Path")
    for index, path in enumerate(rows[:limit], start=1):
        table.add_row(str(index), relative_posix(path, root))
    if len(rows) > limit:
        table.add_row("...", f"{len(rows) - limit} more")
    console.print(table)
