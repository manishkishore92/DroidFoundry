from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from .blobs import BlobGenerator
from .classifier import classify_blobs
from .scanner import FirmwareScanner
from .utils import iter_files, relative_posix, write_json, write_text

Severity = Literal["HIGH", "MEDIUM", "LOW"]


@dataclass(slots=True)
class FoundryIssue:
    severity: Severity
    code: str
    title: str
    detail: str
    recommendation: str
    source: str = "firmware-dump"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


_REQUIRED_BLOB_CATEGORIES = {
    "Camera": ("Camera stack is not obvious", "Review camera HAL and camera provider blobs before bring-up."),
    "Audio": ("Audio stack is not obvious", "Check audio HAL, ACDB/pal/agm and mixer paths."),
    "Wi-Fi": ("Wi-Fi stack is not obvious", "Check WLAN firmware and vendor Wi-Fi configuration files."),
    "Radio": ("Radio/modem stack is not obvious", "Check IMS, RIL, modem and QMI blobs."),
}


def detect_issues(dump: Path | str) -> list[FoundryIssue]:
    root = Path(dump).expanduser().resolve()
    scan = FirmwareScanner(root).scan()
    blobs = BlobGenerator(root).collect()
    groups = classify_blobs(blobs)
    image_names = {p.name.lower() for p in scan.images}
    rel_files = {relative_posix(p, root) for p in iter_files(root)}
    issues: list[FoundryIssue] = []

    def add(severity: Severity, code: str, title: str, detail: str, recommendation: str, source: str = "firmware-dump") -> None:
        issues.append(FoundryIssue(severity, code, title, detail, recommendation, source))

    if not scan.property_files:
        add(
            "HIGH",
            "missing-properties",
            "No property files found",
            "DroidFoundry could not find build.prop, default.prop, or partition property files.",
            "Unpack system, vendor, product and odm partitions before scanning again.",
        )
    if not any("vendor/build.prop" in path or path.endswith("vendor/default.prop") for path in rel_files):
        add(
            "MEDIUM",
            "missing-vendor-props",
            "Vendor build properties are missing",
            "The dump does not appear to include vendor build properties.",
            "Make sure vendor.img is extracted into a vendor/ folder.",
        )
    if "vendor" not in scan.partitions and not any(blob.startswith("vendor/") for blob in blobs):
        add(
            "HIGH",
            "missing-vendor-partition",
            "Vendor partition data is missing",
            "No extracted vendor partition or vendor blob paths were detected.",
            "Extract vendor.img or super.img contents before generating a vendor tree.",
        )
    if "boot.img" not in image_names:
        add(
            "MEDIUM",
            "missing-boot-image",
            "boot.img is missing",
            "The dump does not contain boot.img.",
            "Keep boot.img from the stock package for kernel and ramdisk reference.",
        )
    if "vendor_boot.img" not in image_names:
        add(
            "MEDIUM",
            "missing-vendor-boot",
            "vendor_boot.img is missing",
            "Modern dynamic partition devices often use vendor_boot.img for vendor ramdisk content.",
            "Extract vendor_boot.img from the stock firmware if the device uses it.",
        )
    if not scan.vintf_files:
        add(
            "HIGH",
            "missing-vintf",
            "VINTF files are missing",
            "No vendor/system/product/odm VINTF manifest or compatibility matrix files were detected.",
            "Check */etc/vintf after unpacking all partitions.",
        )
    if not scan.init_files:
        add(
            "MEDIUM",
            "missing-init",
            "Init rc files are missing",
            "No init*.rc files were detected in the dump.",
            "Check vendor/etc/init, odm/etc/init and ramdisk extraction output.",
        )
    if not scan.fstab_files:
        add(
            "MEDIUM",
            "missing-fstab",
            "Fstab files are missing",
            "No fstab files were detected.",
            "Extract vendor_boot/boot ramdisk or vendor/odm partitions to find fstab entries.",
        )
    if not blobs:
        add(
            "HIGH",
            "no-candidate-blobs",
            "No candidate proprietary blobs found",
            "The blob scanner did not find vendor libraries, apps, firmware, XML, rc or configuration files.",
            "Unpack vendor, product and odm partitions before creating proprietary-files.txt.",
        )

    for category, (title, recommendation) in _REQUIRED_BLOB_CATEGORIES.items():
        if blobs and category not in groups:
            add(
                "LOW",
                f"missing-{category.lower().replace('-', '').replace(' ', '-')}-blobs",
                title,
                f"No files were classified under the {category} group.",
                recommendation,
                "blob-classifier",
            )

    empty_files = []
    broken_links = []
    for path in root.rglob("*"):
        try:
            if path.is_symlink() and not path.exists():
                broken_links.append(relative_posix(path, root))
            elif path.is_file() and path.stat().st_size == 0 and path.suffix.lower() not in {".img"}:
                empty_files.append(relative_posix(path, root))
        except OSError:
            continue
    if empty_files:
        add(
            "LOW",
            "empty-files",
            "Suspicious empty files detected",
            f"{len(empty_files)} empty file(s) were found. First entries: {', '.join(empty_files[:5])}",
            "Review empty files before using them in proprietary-files.txt.",
            "file-system",
        )
    if broken_links:
        add(
            "MEDIUM",
            "broken-symlinks",
            "Broken symlinks detected",
            f"{len(broken_links)} broken symlink(s) were found. First entries: {', '.join(broken_links[:5])}",
            "Fix or remove broken symlinks before generating a vendor tree.",
            "file-system",
        )

    basenames: dict[str, list[str]] = {}
    for blob in blobs:
        basenames.setdefault(Path(blob).name, []).append(blob)
    duplicate_basenames = {name: paths for name, paths in basenames.items() if len(paths) > 3 and name.endswith((".so", ".xml", ".conf"))}
    if duplicate_basenames:
        name = next(iter(duplicate_basenames))
        add(
            "LOW",
            "duplicate-blob-names",
            "Repeated blob names detected",
            f"Several blobs share the same filename, for example {name} appears {len(duplicate_basenames[name])} times.",
            "This is often normal, but review duplicate names when pruning proprietary-files.txt.",
            "blob-classifier",
        )

    return sorted(issues, key=lambda issue: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[issue.severity])


def build_issues_markdown(dump: Path | str) -> str:
    issues = detect_issues(dump)
    lines = ["# DroidFoundry Issue Report", ""]
    if not issues:
        lines.extend(["No obvious bring-up blockers were detected.", ""])
        return "\n".join(lines)
    for severity in ("HIGH", "MEDIUM", "LOW"):
        group = [issue for issue in issues if issue.severity == severity]
        if not group:
            continue
        lines.extend([f"## {severity} priority", ""])
        for issue in group:
            lines.extend(
                [
                    f"### {issue.title}",
                    "",
                    f"- Code: `{issue.code}`",
                    f"- Detail: {issue.detail}",
                    f"- Recommended action: {issue.recommendation}",
                    f"- Source: `{issue.source}`",
                    "",
                ]
            )
    return "\n".join(lines)


def write_issues_markdown(dump: Path | str, output: Path | str) -> str:
    content = build_issues_markdown(dump)
    write_text(Path(output), content)
    return content


def write_issues_json(dump: Path | str, output: Path | str) -> list[FoundryIssue]:
    issues = detect_issues(dump)
    write_json(Path(output), [issue.to_dict() for issue in issues])
    return issues
