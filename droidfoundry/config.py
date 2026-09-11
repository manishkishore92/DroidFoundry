from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import ProjectConfig
from .utils import write_text


def load_config(path: Path | str) -> ProjectConfig:
    config_path = Path(path)
    if not config_path.exists():
        return ProjectConfig()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    project = raw.get("project", raw)
    return ProjectConfig(
        brand=str(project.get("brand", "unknown")),
        device=str(project.get("device", "unknown")),
        vendor=str(project.get("vendor", project.get("brand", "unknown"))),
        rom=str(project.get("rom", "aosp")),
        branch=str(project.get("branch", "android-15.0")),
        github=str(project.get("github", "manishkishore92")),
        output=str(project.get("output", "foundry-output")),
    )


def write_default_config(path: Path | str) -> None:
    content = """project:\n  brand: xiaomi\n  device: sweet\n  vendor: xiaomi\n  rom: lineage\n  branch: lineage-22.2\n  github: manishkishore92\n  output: foundry-output\n"""
    write_text(Path(path), content)


def merge_config(config: ProjectConfig, overrides: dict[str, Any]) -> ProjectConfig:
    data = config.to_dict()
    for key, value in overrides.items():
        if value is not None and str(value).strip():
            data[key] = str(value)
    return ProjectConfig(**data)
