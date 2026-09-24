from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from .constants import IGNORED_DIR_NAMES


def normalize_name(value: str | None, fallback: str = "unknown") -> str:
    if not value:
        return fallback
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_\-.]+", "-", value)
    value = value.strip("-._")
    return value or fallback


def first_non_empty(*values: str | None, default: str = "unknown") -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def safe_read_text(path: Path, limit: int | None = None) -> str:
    try:
        if limit is None:
            return path.read_text(encoding="utf-8", errors="replace")
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in IGNORED_DIR_NAMES for part in path.parts):
            continue
        if path.is_file():
            yield path


def iter_dirs(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in IGNORED_DIR_NAMES for part in path.parts):
            continue
        if path.is_dir():
            yield path


def relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def file_size_human(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_sorted(items: Iterable[str]) -> list[str]:
    return sorted({item for item in items if item})

