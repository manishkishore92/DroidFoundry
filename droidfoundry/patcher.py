from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path

from .boardconfig import build_boardconfig_hints
from .classifier import render_grouped_proprietary_files
from .blobs import BlobGenerator
from .report import write_report
from .scanner import FirmwareScanner
from .utils import safe_read_text, write_text


@dataclass(slots=True)
class PatchResult:
    patches: list[Path]


def _patch_text(target_name: str, old_text: str, new_text: str) -> str:
    return "".join(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{target_name}",
            tofile=f"b/{target_name}",
        )
    )


def create_tree_patches(dump: Path | str, tree: Path | str, output: Path | str) -> PatchResult:
    tree_path = Path(tree).expanduser().resolve()
    out = Path(output).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    scan = FirmwareScanner(dump).scan()
    blobs = BlobGenerator(dump).collect()
    proposed: dict[str, str] = {
        "proprietary-files.txt": render_grouped_proprietary_files(blobs),
        "BoardConfig.hints.mk": build_boardconfig_hints(dump),
    }
    temp_report = out / ".tmp-bringup-report.md"
    write_report(dump, temp_report)
    proposed["DROIDFOUNDRY-REPORT.md"] = safe_read_text(temp_report)
    try:
        temp_report.unlink()
    except OSError:
        pass

    patches: list[Path] = []
    for index, (relative, new_text) in enumerate(proposed.items(), start=1):
        old_text = safe_read_text(tree_path / relative) if (tree_path / relative).exists() else ""
        if old_text == new_text:
            continue
        patch = _patch_text(relative, old_text, new_text)
        if not patch:
            continue
        patch_path = out / f"{index:04d}-{relative.replace('/', '-').replace('.', '-')}.patch"
        header = (
            f"# DroidFoundry patch for {relative}\n"
            f"# Device: {scan.metadata.device}\n"
            "# Review before applying. Generated patches are starter suggestions.\n\n"
        )
        write_text(patch_path, header + patch)
        patches.append(patch_path)
    return PatchResult(patches=patches)
