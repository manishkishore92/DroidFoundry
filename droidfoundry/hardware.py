from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .blobs import BlobGenerator
from .classifier import classify_blobs
from .vintf import analyze_vintf
from .utils import write_json, write_text


@dataclass(slots=True)
class HardwareEntry:
    name: str
    status: str
    evidence: list[str]
    note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


HARDWARE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Camera": ("camera", "camx"),
    "Audio": ("audio", "sound", "microphone"),
    "Bluetooth": ("bluetooth", "bt"),
    "Wi-Fi": ("wifi", "wlan", "wcn"),
    "GPS": ("gps", "gnss", "location"),
    "Sensors": ("sensor", "sensors"),
    "Fingerprint": ("fingerprint", "biometrics"),
    "NFC": ("nfc", "secure_element"),
    "DRM": ("drm", "widevine", "oemcrypto"),
    "Graphics": ("graphics", "composer", "mapper", "gralloc", "vulkan", "egl"),
    "Radio": ("radio", "ril", "telephony", "ims", "qmi"),
    "Power": ("power", "health", "thermal"),
}


def build_hardware_map(dump: Path | str) -> list[HardwareEntry]:
    blobs = BlobGenerator(dump).collect()
    groups = classify_blobs(blobs)
    hals = analyze_vintf(dump)
    hal_texts = [" ".join([hal.name, hal.version, hal.transport, " ".join(hal.interfaces)]).lower() for hal in hals]
    entries: list[HardwareEntry] = []
    for hardware, keywords in HARDWARE_KEYWORDS.items():
        evidence: list[str] = []
        if hardware in groups:
            evidence.append(f"{len(groups[hardware])} classified blob(s)")
        matched_hals = [hal.name for hal, text in zip(hals, hal_texts) if any(keyword in text for keyword in keywords)]
        if matched_hals:
            evidence.append("HAL: " + ", ".join(sorted(set(matched_hals))[:4]))
        if evidence:
            status = "Detected"
            note = "Review detected files before assuming full hardware support."
        else:
            status = "Missing" if hardware in {"Camera", "Audio", "Wi-Fi", "Radio"} else "Unknown"
            note = "No obvious evidence found in blobs or VINTF files."
        entries.append(HardwareEntry(hardware, status, evidence, note))
    return entries


def build_hardware_markdown(dump: Path | str) -> str:
    entries = build_hardware_map(dump)
    lines = [
        "# Hardware Map",
        "",
        "This report combines VINTF declarations and proprietary blob classification. It is a hint map for ROM bring-up, not a hardware certification result.",
        "",
        "| Area | Status | Evidence | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for entry in entries:
        evidence = "; ".join(entry.evidence) if entry.evidence else "-"
        lines.append(f"| {entry.name} | {entry.status} | {evidence} | {entry.note} |")
    lines.append("")
    return "\n".join(lines)


def write_hardware_markdown(dump: Path | str, output: Path | str) -> list[HardwareEntry]:
    write_text(Path(output), build_hardware_markdown(dump))
    return build_hardware_map(dump)


def write_hardware_json(dump: Path | str, output: Path | str) -> list[HardwareEntry]:
    entries = build_hardware_map(dump)
    write_json(Path(output), [entry.to_dict() for entry in entries])
    return entries
