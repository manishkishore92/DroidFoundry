from __future__ import annotations

from pathlib import Path

from .blobs import BlobGenerator
from .models import FirmwareScan
from .scanner import FirmwareScanner
from .template_engine import render_template
from .utils import file_size_human, relative_posix, write_text


def build_report(scan: FirmwareScan, blob_count: int | None = None) -> str:
    if blob_count is None:
        blob_count = len(BlobGenerator(scan.root).collect())
    return render_template(
        "bringup-report.md.j2",
        scan=scan,
        metadata=scan.metadata,
        blob_count=blob_count,
        file_size_human=file_size_human,
        rel=lambda p: relative_posix(p, scan.root),
    )


def write_report(dump: Path | str, output: Path | str) -> FirmwareScan:
    scan = FirmwareScanner(dump).scan()
    report = build_report(scan)
    write_text(Path(output), report)
    return scan

