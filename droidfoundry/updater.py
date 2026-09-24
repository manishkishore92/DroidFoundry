from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .blobs import BlobGenerator
from .classifier import render_grouped_proprietary_files
from .report import build_report
from .scanner import FirmwareScanner
from .utils import write_text


@dataclass(slots=True)
class UpdateResult:
    changed: list[Path]
    backups: list[Path]
    skipped: list[Path]


def _backup(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak-{timestamp}")
    backup_path.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    return backup_path


def _write_if_changed(path: Path, content: str, yes: bool, backups: list[Path], changed: list[Path], skipped: list[Path]) -> None:
    if path.exists() and path.read_text(encoding="utf-8", errors="replace") == content:
        skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not yes:
        skipped.append(path)
        return
    if path.exists():
        backups.append(_backup(path))
    path.write_text(content, encoding="utf-8")
    changed.append(path)


def update_tree_from_dump(dump: Path | str, tree: Path | str, yes: bool = False) -> UpdateResult:
    dump_path = Path(dump).expanduser().resolve()
    tree_path = Path(tree).expanduser().resolve()
    if not tree_path.exists():
        raise FileNotFoundError(f"Device tree not found: {tree_path}")
    scan = FirmwareScanner(dump_path).scan()
    blobs = BlobGenerator(dump_path).collect()
    changed: list[Path] = []
    backups: list[Path] = []
    skipped: list[Path] = []
    _write_if_changed(tree_path / "proprietary-files.txt", render_grouped_proprietary_files(blobs), yes, backups, changed, skipped)
    _write_if_changed(tree_path / "DROIDFOUNDRY-REPORT.md", build_report(scan, blob_count=len(blobs)), yes, backups, changed, skipped)
    return UpdateResult(changed=changed, backups=backups, skipped=skipped)

