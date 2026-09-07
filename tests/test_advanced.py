from __future__ import annotations

from pathlib import Path

from droidfoundry.boardconfig import build_boardconfig_hints
from droidfoundry.classifier import classify_blob, classify_blobs
from droidfoundry.doctor import run_doctor
from droidfoundry.init_scan import analyze_init_and_fstab
from droidfoundry.vintf import analyze_vintf


def make_dump(tmp_path: Path) -> Path:
    root = tmp_path / "dump"
    (root / "system").mkdir(parents=True)
    (root / "vendor/etc/vintf").mkdir(parents=True)
    (root / "vendor/etc/init").mkdir(parents=True)
    (root / "vendor/lib64/hw").mkdir(parents=True)
    (root / "vendor/firmware").mkdir(parents=True)
    (root / "system/build.prop").write_text(
        "\n".join(
            [
                "ro.product.brand=Xiaomi",
                "ro.product.device=sweet",
                "ro.product.model=Redmi Note 10 Pro",
                "ro.build.version.release=15",
                "ro.build.version.sdk=35",
                "ro.build.version.security_patch=2026-07-05",
                "ro.board.platform=sm6150",
                "ro.product.first_api_level=30",
            ]
        ),
        encoding="utf-8",
    )
    (root / "vendor/etc/vintf/manifest.xml").write_text(
        '<manifest><hal><name>android.hardware.camera.provider</name><transport>hwbinder</transport><version>2.4</version></hal></manifest>',
        encoding="utf-8",
    )
    (root / "vendor/etc/init/init.camera.rc").write_text(
        "service vendor.camera /vendor/bin/hw/camera\n  class hal\n", encoding="utf-8"
    )
    (root / "vendor/etc/fstab.qcom").write_text(
        "/dev/block/by-name/userdata /data f2fs noatime wait,slotselect\n", encoding="utf-8"
    )
    (root / "boot.img").write_bytes(b"")
    (root / "vendor/lib64/hw/camera.qcom.so").write_bytes(b"camera")
    (root / "vendor/firmware/modem.mbn").write_bytes(b"modem")
    return root


def test_classifier_groups_hardware_paths() -> None:
    assert classify_blob("vendor/lib64/hw/camera.qcom.so") == "Camera"
    assert classify_blob("vendor/firmware/modem.mbn") == "Radio"
    groups = classify_blobs(["vendor/lib64/hw/audio.primary.qcom.so", "vendor/firmware/modem.mbn"])
    assert "Audio" in groups
    assert "Radio" in groups


def test_doctor_and_boardconfig(tmp_path: Path) -> None:
    dump = make_dump(tmp_path)
    checks = run_doctor(dump)
    assert any(check.name == "Property files" and check.status == "OK" for check in checks)
    hints = build_boardconfig_hints(dump)
    assert "TARGET_BOARD_PLATFORM := sm6150" in hints
    assert "TARGET_OTA_ASSERT_DEVICE := sweet" in hints


def test_vintf_and_init_scan(tmp_path: Path) -> None:
    dump = make_dump(tmp_path)
    hals = analyze_vintf(dump)
    services, fstabs = analyze_init_and_fstab(dump)
    assert hals[0].name == "android.hardware.camera.provider"
    assert services[0].name == "vendor.camera"
    assert fstabs[0].mount_point == "/data"
