from __future__ import annotations

from pathlib import Path

from droidfoundry.hardware import build_hardware_map
from droidfoundry.intelligence import run_intelligence_report
from droidfoundry.issues import detect_issues
from droidfoundry.patcher import create_tree_patches
from droidfoundry.scoring import compute_readiness_score
from droidfoundry.properties_intel import property_summary


def make_full_dump(tmp_path: Path) -> Path:
    root = tmp_path / "dump"
    (root / "system").mkdir(parents=True)
    (root / "vendor/etc/vintf").mkdir(parents=True)
    (root / "vendor/etc/init").mkdir(parents=True)
    (root / "vendor/etc/permissions").mkdir(parents=True)
    (root / "vendor/lib64/hw").mkdir(parents=True)
    (root / "vendor/firmware").mkdir(parents=True)
    (root / "system/build.prop").write_text(
        "\n".join(
            [
                "ro.product.brand=Xiaomi",
                "ro.product.device=sweet",
                "ro.product.model=Redmi Note 10 Pro",
                "ro.product.manufacturer=Xiaomi",
                "ro.build.version.release=15",
                "ro.build.version.sdk=35",
                "ro.build.version.security_patch=2026-07-05",
                "ro.vendor.build.security_patch=2026-07-05",
                "ro.build.fingerprint=xiaomi/sweet/sweet:15/AP3A/test:userdebug/test-keys",
                "ro.board.platform=sm6150",
                "ro.product.first_api_level=30",
            ]
        ),
        encoding="utf-8",
    )
    (root / "vendor/build.prop").write_text("ro.vendor.build.version.sdk=35\n", encoding="utf-8")
    (root / "vendor/etc/vintf/manifest.xml").write_text(
        '<manifest><hal><name>android.hardware.camera.provider</name><transport>hwbinder</transport><version>2.4</version></hal><hal><name>android.hardware.audio</name><transport>hwbinder</transport><version>7.0</version></hal></manifest>',
        encoding="utf-8",
    )
    (root / "vendor/etc/vintf/compatibility_matrix.xml").write_text("<compatibility-matrix />", encoding="utf-8")
    (root / "vendor/etc/init/init.camera.rc").write_text("service vendor.camera /vendor/bin/hw/camera\n", encoding="utf-8")
    (root / "vendor/etc/fstab.qcom").write_text("/dev/block/by-name/userdata /data f2fs noatime wait,slotselect\n", encoding="utf-8")
    (root / "vendor/etc/permissions/android.hardware.camera.xml").write_text("<permissions />", encoding="utf-8")
    (root / "boot.img").write_bytes(b"boot")
    (root / "vendor_boot.img").write_bytes(b"vendorboot")
    (root / "dtbo.img").write_bytes(b"dtbo")
    (root / "super.img").write_bytes(b"super")
    (root / "vendor/lib64/hw/camera.qcom.so").write_bytes(b"camera")
    (root / "vendor/lib64/hw/audio.primary.qcom.so").write_bytes(b"audio")
    (root / "vendor/lib64/hw/wifi.qcom.so").write_bytes(b"wifi")
    (root / "vendor/firmware/modem.mbn").write_bytes(b"modem")
    return root


def test_score_hardware_props_and_issues(tmp_path: Path) -> None:
    dump = make_full_dump(tmp_path)
    score = compute_readiness_score(dump)
    assert score.total > 70
    props = property_summary(dump)
    assert props["Device codename"] == "sweet"
    hardware = build_hardware_map(dump)
    assert any(entry.name == "Camera" and entry.status == "Detected" for entry in hardware)
    issues = detect_issues(dump)
    assert isinstance(issues, list)


def test_intelligence_and_patch_outputs(tmp_path: Path) -> None:
    dump = make_full_dump(tmp_path)
    report_dir = tmp_path / "report"
    files = run_intelligence_report(dump, report_dir, github="manishkishore92")
    assert (report_dir / "index.html").exists()
    assert (report_dir / "issues.json").exists()
    assert (report_dir / "exports" / "android-es" / "android-es-profile.conf").exists()
    assert len(files) >= 10

    tree = tmp_path / "device" / "xiaomi" / "sweet"
    tree.mkdir(parents=True)
    patches = create_tree_patches(dump, tree, tmp_path / "patches")
    assert patches.patches
