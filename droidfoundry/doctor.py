from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .blobs import BlobGenerator
from .scanner import FirmwareScanner
from .utils import relative_posix


@dataclass(slots=True)
class DoctorCheck:
    name: str
    status: str
    detail: str
    fix: str = ""

    @property
    def passed(self) -> bool:
        return self.status == "OK"


def _exists_any(root: Path, candidates: list[str]) -> bool:
    return any((root / candidate).exists() for candidate in candidates)


def run_doctor(dump: Path | str) -> list[DoctorCheck]:
    root = Path(dump).expanduser().resolve()
    scan = FirmwareScanner(root).scan()
    blobs = BlobGenerator(root).collect()
    image_names = {p.name.lower() for p in scan.images}
    checks: list[DoctorCheck] = []

    def add(name: str, ok: bool, detail: str, fix: str = "", warn: bool = False) -> None:
        status = "OK" if ok else ("WARN" if warn else "FAIL")
        checks.append(DoctorCheck(name, status, detail, fix))

    add(
        "Property files",
        bool(scan.property_files),
        f"{len(scan.property_files)} property file(s) found" if scan.property_files else "No build.prop/default.prop files found",
        "Extract system, vendor, product or odm partitions before scanning.",
    )
    add(
        "Vendor partition",
        "vendor" in scan.partitions or any(p.startswith("vendor/") for p in blobs),
        "Vendor partition data found" if "vendor" in scan.partitions else "Vendor folder not detected",
        "Make sure vendor.img is unpacked into a vendor/ folder.",
        warn=True,
    )
    add(
        "Boot image",
        "boot.img" in image_names,
        "boot.img found" if "boot.img" in image_names else "boot.img missing",
        "Keep boot.img from stock firmware for kernel/recovery bring-up reference.",
        warn=True,
    )
    add(
        "Vendor boot image",
        "vendor_boot.img" in image_names,
        "vendor_boot.img found" if "vendor_boot.img" in image_names else "vendor_boot.img missing",
        "Dynamic/modern devices often need vendor_boot.img for ramdisk and vendor kernel modules.",
        warn=True,
    )
    add(
        "DTBO image",
        "dtbo.img" in image_names,
        "dtbo.img found" if "dtbo.img" in image_names else "dtbo.img missing",
        "Keep dtbo.img if the device uses DT overlays.",
        warn=True,
    )
    add(
        "VBMeta image",
        "vbmeta.img" in image_names,
        "vbmeta.img found" if "vbmeta.img" in image_names else "vbmeta.img missing",
        "vbmeta.img helps identify verified boot layout.",
        warn=True,
    )
    add(
        "VINTF files",
        bool(scan.vintf_files),
        f"{len(scan.vintf_files)} VINTF XML file(s) found" if scan.vintf_files else "No VINTF XML files found",
        "Check vendor/etc/vintf and system/etc/vintf after unpacking partitions.",
    )
    add(
        "Init scripts",
        bool(scan.init_files),
        f"{len(scan.init_files)} init rc file(s) found" if scan.init_files else "No init*.rc files found",
        "Check vendor/etc/init, odm/etc/init and root ramdisk contents.",
        warn=True,
    )
    add(
        "Fstab files",
        bool(scan.fstab_files),
        f"{len(scan.fstab_files)} fstab file(s) found" if scan.fstab_files else "No fstab files found",
        "Fstab files are useful for encryption, logical partition and mount flag hints.",
        warn=True,
    )
    add(
        "Candidate proprietary files",
        bool(blobs),
        f"{len(blobs)} candidate blob(s) found" if blobs else "No candidate proprietary blobs found",
        "Unpack vendor/product/odm partitions and scan again.",
    )
    add(
        "Permissions XML",
        any("permissions" in relative_posix(p, root).lower() and p.suffix == ".xml" for p in root.rglob("*.xml")),
        "Permission XML files found" if _exists_any(root, ["vendor/etc/permissions", "system/etc/permissions", "product/etc/permissions"]) else "No permissions folder detected",
        "Permission XML files are usually under */etc/permissions.",
        warn=True,
    )
    add(
        "Firmware files",
        scan.stats.firmware_files > 0,
        f"{scan.stats.firmware_files} firmware-like file(s) found" if scan.stats.firmware_files else "No firmware-like files detected",
        "Check vendor/firmware, vendor/etc/firmware and modem firmware folders.",
        warn=True,
    )
    return checks


def doctor_score(checks: list[DoctorCheck]) -> tuple[int, int]:
    ok = sum(1 for item in checks if item.status == "OK")
    return ok, len(checks)
