from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .utils import iter_dirs, safe_read_text, write_text


@dataclass(slots=True)
class TreeCheck:
    name: str
    status: str
    detail: str


def inspect_device_tree(tree: Path | str) -> list[TreeCheck]:
    root = Path(tree).expanduser().resolve()
    checks: list[TreeCheck] = []

    def add(name: str, ok: bool, detail: str, warn: bool = False) -> None:
        checks.append(TreeCheck(name, "OK" if ok else ("WARN" if warn else "FAIL"), detail))

    required_files = [
        "AndroidProducts.mk",
        "BoardConfig.mk",
        "device.mk",
        "vendorsetup.sh",
        "extract-files.sh",
        "setup-makefiles.sh",
        "proprietary-files.txt",
    ]
    for filename in required_files:
        path = root / filename
        add(filename, path.exists(), "found" if path.exists() else "missing", warn=filename in {"vendorsetup.sh", "setup-makefiles.sh"})

    product_mks = sorted(root.glob("*.mk"))
    add("ROM product makefile", any(p.name not in {"AndroidProducts.mk", "device.mk", "BoardConfig.mk"} for p in product_mks), f"{len(product_mks)} mk file(s) found", warn=True)

    sepolicy_dirs = [p for p in iter_dirs(root) if "sepolicy" in p.name.lower() or "sepolicy" in p.as_posix().lower()]
    add("Sepolicy folders", bool(sepolicy_dirs), f"{len(sepolicy_dirs)} sepolicy-like folder(s) found", warn=True)

    overlay_dirs = [p for p in iter_dirs(root) if p.name.lower() == "overlay" or "/overlay/" in p.as_posix().lower()]
    add("Overlay folders", bool(overlay_dirs), f"{len(overlay_dirs)} overlay folder(s) found", warn=True)

    rootdir_dirs = [p for p in iter_dirs(root) if p.name.lower() in {"rootdir", "root", "ramdisk"}]
    add("Rootdir/ramdisk folders", bool(rootdir_dirs), f"{len(rootdir_dirs)} rootdir-like folder(s) found", warn=True)

    boardconfig = safe_read_text(root / "BoardConfig.mk")
    device_mk = safe_read_text(root / "device.mk")
    combined = f"{boardconfig}\n{device_mk}"
    add("Kernel path hint", "TARGET_KERNEL_SOURCE" in combined or "TARGET_PREBUILT_KERNEL" in combined, "kernel source/prebuilt hint found" if "TARGET_KERNEL" in combined else "no kernel path hint found", warn=True)
    add("Vendor path hint", "vendor/" in combined or "DEVICE_MANIFEST_FILE" in combined, "vendor/manifest hint found" if "vendor/" in combined else "no vendor path hint found", warn=True)
    add("Dynamic partitions", "BOARD_USES_DYNAMIC_PARTITIONS" in boardconfig, "dynamic partition flag found" if "BOARD_USES_DYNAMIC_PARTITIONS" in boardconfig else "dynamic partition flag not found", warn=True)
    add("A/B OTA", "AB_OTA_UPDATER" in boardconfig, "A/B flag found" if "AB_OTA_UPDATER" in boardconfig else "A/B flag not found", warn=True)
    add("Recovery fstab", any(p.name.startswith("fstab") for p in root.rglob("*")), "fstab-like file found" if any(p.name.startswith("fstab") for p in root.rglob("*")) else "no fstab-like file found", warn=True)
    return checks


def build_tree_report(tree: Path | str) -> str:
    root = Path(tree).expanduser().resolve()
    checks = inspect_device_tree(root)
    lines = [
        "# Device Tree Inspection Report",
        "",
        f"Tree: `{root}`",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        lines.append(f"| {check.name} | {check.status} | {check.detail} |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Missing optional folders are not always errors; some ROM/device targets do not need all of them.",
            "- Treat WARN entries as review points before building.",
            "",
        ]
    )
    return "\n".join(lines)


def write_tree_report(tree: Path | str, output: Path | str) -> str:
    report = build_tree_report(tree)
    write_text(Path(output), report)
    return report
