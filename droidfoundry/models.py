from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DeviceMetadata:
    brand: str = "unknown"
    manufacturer: str = "unknown"
    device: str = "unknown"
    model: str = "unknown"
    product: str = "unknown"
    android_version: str = "unknown"
    sdk: str = "unknown"
    security_patch: str = "unknown"
    vendor_security_patch: str = "unknown"
    build_id: str = "unknown"
    build_type: str = "unknown"
    build_tags: str = "unknown"
    fingerprint: str = "unknown"
    platform: str = "unknown"
    first_api_level: str = "unknown"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class ScanStats:
    total_files: int = 0
    total_size: int = 0
    shared_libraries: int = 0
    apk_files: int = 0
    jar_files: int = 0
    firmware_files: int = 0
    xml_files: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(slots=True)
class FirmwareScan:
    root: Path
    metadata: DeviceMetadata
    property_files: list[Path] = field(default_factory=list)
    partitions: list[str] = field(default_factory=list)
    images: list[Path] = field(default_factory=list)
    vintf_files: list[Path] = field(default_factory=list)
    init_files: list[Path] = field(default_factory=list)
    fstab_files: list[Path] = field(default_factory=list)
    sepolicy_paths: list[Path] = field(default_factory=list)
    stats: ScanStats = field(default_factory=ScanStats)
    warnings: list[str] = field(default_factory=list)
    properties: dict[str, str] = field(default_factory=dict)

    def rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "metadata": self.metadata.to_dict(),
            "property_files": [self.rel(p) for p in self.property_files],
            "partitions": self.partitions,
            "images": [self.rel(p) for p in self.images],
            "vintf_files": [self.rel(p) for p in self.vintf_files],
            "init_files": [self.rel(p) for p in self.init_files],
            "fstab_files": [self.rel(p) for p in self.fstab_files],
            "sepolicy_paths": [self.rel(p) for p in self.sepolicy_paths],
            "stats": self.stats.to_dict(),
            "warnings": self.warnings,
            "properties": self.properties,
        }


@dataclass(slots=True)
class ProjectConfig:
    brand: str = "unknown"
    device: str = "unknown"
    vendor: str = "unknown"
    rom: str = "aosp"
    branch: str = "android-15.0"
    github: str = "manishkishore92"
    output: str = "foundry-output"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
