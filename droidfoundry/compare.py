from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .blobs import BlobGenerator
from .scanner import FirmwareScanner
from .utils import relative_posix, safe_read_text, sha256_file, write_text


@dataclass(slots=True)
class FirmwareComparison:
    metadata_changes: dict[str, tuple[str, str]]
    added_blobs: list[str]
    removed_blobs: list[str]
    common_blob_count: int
    changed_files: list[str]
    added_images: list[str]
    removed_images: list[str]
    added_vintf: list[str]
    removed_vintf: list[str]
    added_init: list[str]
    removed_init: list[str]


def _rel_set(paths: list[Path], root: Path) -> set[str]:
    return {relative_posix(p, root) for p in paths}


def _small_hashes(root: Path, paths: set[str], max_size: int = 16 * 1024 * 1024) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for rel in paths:
        path = root / rel
        try:
            if path.stat().st_size <= max_size:
                hashes[rel] = sha256_file(path)
            else:
                hashes[rel] = f"size:{path.stat().st_size}"
        except OSError:
            continue
    return hashes


def compare_firmware(old_dump: Path | str, new_dump: Path | str) -> FirmwareComparison:
    old_scan = FirmwareScanner(old_dump).scan()
    new_scan = FirmwareScanner(new_dump).scan()
    old_meta = old_scan.metadata.to_dict()
    new_meta = new_scan.metadata.to_dict()
    metadata_changes = {
        key: (old_meta.get(key, "unknown"), new_meta.get(key, "unknown"))
        for key in sorted(set(old_meta) | set(new_meta))
        if old_meta.get(key, "unknown") != new_meta.get(key, "unknown")
    }

    old_blobs = set(BlobGenerator(old_scan.root).collect())
    new_blobs = set(BlobGenerator(new_scan.root).collect())
    common = old_blobs & new_blobs
    old_hashes = _small_hashes(old_scan.root, common)
    new_hashes = _small_hashes(new_scan.root, common)
    changed = sorted(path for path in common if old_hashes.get(path) != new_hashes.get(path))

    old_images = _rel_set(old_scan.images, old_scan.root)
    new_images = _rel_set(new_scan.images, new_scan.root)
    old_vintf = _rel_set(old_scan.vintf_files, old_scan.root)
    new_vintf = _rel_set(new_scan.vintf_files, new_scan.root)
    old_init = _rel_set(old_scan.init_files, old_scan.root)
    new_init = _rel_set(new_scan.init_files, new_scan.root)
    return FirmwareComparison(
        metadata_changes=metadata_changes,
        added_blobs=sorted(new_blobs - old_blobs),
        removed_blobs=sorted(old_blobs - new_blobs),
        common_blob_count=len(common),
        changed_files=changed,
        added_images=sorted(new_images - old_images),
        removed_images=sorted(old_images - new_images),
        added_vintf=sorted(new_vintf - old_vintf),
        removed_vintf=sorted(old_vintf - new_vintf),
        added_init=sorted(new_init - old_init),
        removed_init=sorted(old_init - new_init),
    )


def _limited(items: list[str], limit: int = 80) -> list[str]:
    if len(items) <= limit:
        return items
    return items[:limit] + [f"... {len(items) - limit} more"]


def build_compare_report(old_dump: Path | str, new_dump: Path | str) -> str:
    result = compare_firmware(old_dump, new_dump)
    lines = [
        "# Firmware Comparison Report",
        "",
        f"Old dump: `{Path(old_dump).expanduser().resolve()}`",
        f"New dump: `{Path(new_dump).expanduser().resolve()}`",
        "",
        "## Metadata changes",
        "",
        "| Field | Old | New |",
        "| --- | --- | --- |",
    ]
    if not result.metadata_changes:
        lines.append("| No metadata changes detected | - | - |")
    for key, (old, new) in result.metadata_changes.items():
        lines.append(f"| `{key}` | `{old}` | `{new}` |")
    sections = [
        ("Added blobs", result.added_blobs),
        ("Removed blobs", result.removed_blobs),
        ("Changed common blobs", result.changed_files),
        ("Added images", result.added_images),
        ("Removed images", result.removed_images),
        ("Added VINTF files", result.added_vintf),
        ("Removed VINTF files", result.removed_vintf),
        ("Added init files", result.added_init),
        ("Removed init files", result.removed_init),
    ]
    for title, items in sections:
        lines.extend(["", f"## {title}", ""])
        if not items:
            lines.append("No changes detected.")
        else:
            lines.extend(f"- `{item}`" for item in _limited(items))
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Large files are compared by size to avoid slow hashing of full firmware images.",
            "- Review removed blobs carefully before updating proprietary-files.txt.",
            "",
        ]
    )
    return "\n".join(lines)


def write_compare_report(old_dump: Path | str, new_dump: Path | str, output: Path | str) -> str:
    report = build_compare_report(old_dump, new_dump)
    write_text(Path(output), report)
    return report
