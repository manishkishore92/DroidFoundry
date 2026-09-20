from __future__ import annotations

from pathlib import Path

from .constants import BUILD_PROP_NAMES
from .models import DeviceMetadata
from .utils import first_non_empty, iter_files, safe_read_text


def parse_prop_text(text: str) -> dict[str, str]:
    props: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            props[key] = value
    return props


def parse_prop_file(path: Path) -> dict[str, str]:
    return parse_prop_text(safe_read_text(path))


def find_property_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in iter_files(root):
        name = path.name.lower()
        if name in BUILD_PROP_NAMES or name.endswith(".prop"):
            files.append(path)
    return sorted(files)


def collect_properties(root: Path) -> tuple[dict[str, str], list[Path]]:
    merged: dict[str, str] = {}
    files = find_property_files(root)
    # Later partition-specific files should be allowed to fill missing values,
    # but the first value remains useful when multiple partitions expose the same key.
    for path in files:
        for key, value in parse_prop_file(path).items():
            merged.setdefault(key, value)
    return merged, files


def metadata_from_props(props: dict[str, str]) -> DeviceMetadata:
    return DeviceMetadata(
        brand=first_non_empty(
            props.get("ro.product.brand"),
            props.get("ro.product.system.brand"),
            props.get("ro.product.vendor.brand"),
            props.get("ro.product.odm.brand"),
        ),
        manufacturer=first_non_empty(
            props.get("ro.product.manufacturer"),
            props.get("ro.product.system.manufacturer"),
            props.get("ro.product.vendor.manufacturer"),
            props.get("ro.product.odm.manufacturer"),
        ),
        device=first_non_empty(
            props.get("ro.product.device"),
            props.get("ro.product.system.device"),
            props.get("ro.product.vendor.device"),
            props.get("ro.product.odm.device"),
        ),
        model=first_non_empty(
            props.get("ro.product.model"),
            props.get("ro.product.system.model"),
            props.get("ro.product.vendor.model"),
            props.get("ro.product.odm.model"),
        ),
        product=first_non_empty(
            props.get("ro.product.name"),
            props.get("ro.product.system.name"),
            props.get("ro.product.vendor.name"),
            props.get("ro.product.odm.name"),
        ),
        android_version=first_non_empty(props.get("ro.build.version.release")),
        sdk=first_non_empty(props.get("ro.build.version.sdk")),
        security_patch=first_non_empty(props.get("ro.build.version.security_patch")),
        vendor_security_patch=first_non_empty(props.get("ro.vendor.build.security_patch")),
        build_id=first_non_empty(props.get("ro.build.id"), props.get("ro.system.build.id")),
        build_type=first_non_empty(props.get("ro.build.type"), props.get("ro.system.build.type")),
        build_tags=first_non_empty(props.get("ro.build.tags"), props.get("ro.system.build.tags")),
        fingerprint=first_non_empty(
            props.get("ro.build.fingerprint"),
            props.get("ro.system.build.fingerprint"),
            props.get("ro.vendor.build.fingerprint"),
        ),
        platform=first_non_empty(
            props.get("ro.board.platform"),
            props.get("ro.boot.hardware"),
            props.get("ro.hardware"),
        ),
        first_api_level=first_non_empty(
            props.get("ro.product.first_api_level"),
            props.get("ro.board.first_api_level"),
            props.get("ro.vendor.api_level"),
        ),
    )
