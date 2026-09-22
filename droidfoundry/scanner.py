from __future__ import annotations

from pathlib import Path

from .constants import IMAGE_NAMES, PARTITION_DIRS
from .models import FirmwareScan, ScanStats
from .properties import collect_properties, metadata_from_props
from .utils import iter_dirs, iter_files, relative_posix


class FirmwareScanner:
    """Scan Android firmware dump folders for bring-up information."""

    def __init__(self, root: Path | str):
        self.root = Path(root).expanduser().resolve()

    def scan(self) -> FirmwareScan:
        if not self.root.exists():
            raise FileNotFoundError(f"Firmware dump not found: {self.root}")
        if not self.root.is_dir():
            raise NotADirectoryError(f"Firmware dump path is not a directory: {self.root}")

        props, prop_files = collect_properties(self.root)
        metadata = metadata_from_props(props)
        partitions = self._detect_partitions()
        images = self._detect_images()
        vintf_files = self._detect_vintf_files()
        init_files = self._detect_init_files()
        fstab_files = self._detect_fstab_files()
        sepolicy_paths = self._detect_sepolicy_paths()
        stats = self._collect_stats()
        warnings = self._build_warnings(prop_files, partitions, images, vintf_files)

        return FirmwareScan(
            root=self.root,
            metadata=metadata,
            property_files=prop_files,
            partitions=partitions,
            images=images,
            vintf_files=vintf_files,
            init_files=init_files,
            fstab_files=fstab_files,
            sepolicy_paths=sepolicy_paths,
            stats=stats,
            warnings=warnings,
            properties=props,
        )

    def _detect_partitions(self) -> list[str]:
        found = []
        for name in PARTITION_DIRS:
            if (self.root / name).is_dir():
                found.append(name)
        return found

    def _detect_images(self) -> list[Path]:
        images: set[Path] = set()
        for path in iter_files(self.root):
            lower = path.name.lower()
            if lower in IMAGE_NAMES or lower.endswith(".img"):
                images.add(path)
        return sorted(images, key=lambda p: relative_posix(p, self.root))

    def _detect_vintf_files(self) -> list[Path]:
        files: list[Path] = []
        for path in iter_files(self.root):
            rel = relative_posix(path, self.root).lower()
            name = path.name.lower()
            if "vintf" in rel and path.suffix.lower() == ".xml":
                files.append(path)
            elif name.startswith("manifest") and path.suffix.lower() == ".xml":
                files.append(path)
            elif name.startswith("compatibility_matrix") and path.suffix.lower() == ".xml":
                files.append(path)
        return sorted(set(files), key=lambda p: relative_posix(p, self.root))

    def _detect_init_files(self) -> list[Path]:
        return sorted(
            [p for p in iter_files(self.root) if p.name.startswith("init") and p.suffix == ".rc"],
            key=lambda p: relative_posix(p, self.root),
        )

    def _detect_fstab_files(self) -> list[Path]:
        return sorted(
            [p for p in iter_files(self.root) if p.name.startswith("fstab")],
            key=lambda p: relative_posix(p, self.root),
        )

    def _detect_sepolicy_paths(self) -> list[Path]:
        names = {
            "sepolicy",
            "sepolicy_private",
            "sepolicy_public",
            "sepolicy_vendor",
            "vendor_sepolicy",
        }
        return sorted(
            [p for p in iter_dirs(self.root) if p.name in names or "sepolicy" in p.name],
            key=lambda p: relative_posix(p, self.root),
        )

    def _collect_stats(self) -> ScanStats:
        stats = ScanStats()
        firmware_exts = {".bin", ".mbn", ".elf", ".fw", ".dat"}
        for path in iter_files(self.root):
            stats.total_files += 1
            try:
                stats.total_size += path.stat().st_size
            except OSError:
                pass
            suffix = path.suffix.lower()
            if suffix == ".so":
                stats.shared_libraries += 1
            elif suffix == ".apk":
                stats.apk_files += 1
            elif suffix == ".jar":
                stats.jar_files += 1
            elif suffix == ".xml":
                stats.xml_files += 1
            elif suffix in firmware_exts or "/firmware/" in path.as_posix().lower():
                stats.firmware_files += 1
        return stats

    @staticmethod
    def _build_warnings(
        prop_files: list[Path], partitions: list[str], images: list[Path], vintf_files: list[Path]
    ) -> list[str]:
        warnings: list[str] = []
        if not prop_files:
            warnings.append("No build.prop or .prop files were found. Device metadata may be incomplete.")
        if "vendor" not in partitions:
            warnings.append("Vendor partition folder was not detected. Blob extraction may be incomplete.")
        if not images:
            warnings.append("No Android image files were detected.")
        if not vintf_files:
            warnings.append("No VINTF manifest or compatibility matrix files were detected.")
        return warnings
