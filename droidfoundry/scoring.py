from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .blobs import BlobGenerator
from .classifier import classify_blobs
from .scanner import FirmwareScanner
from .utils import write_json, write_text


@dataclass(slots=True)
class ScoreSection:
    name: str
    score: int
    maximum: int
    note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ReadinessScore:
    total: int
    maximum: int
    sections: list[ScoreSection]

    @property
    def percentage(self) -> int:
        return round((self.total / self.maximum) * 100) if self.maximum else 0

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "maximum": self.maximum,
            "percentage": self.percentage,
            "sections": [section.to_dict() for section in self.sections],
        }


def _cap(value: int, maximum: int) -> int:
    return max(0, min(value, maximum))


def compute_readiness_score(dump: Path | str) -> ReadinessScore:
    scan = FirmwareScanner(dump).scan()
    blobs = BlobGenerator(dump).collect()
    groups = classify_blobs(blobs)
    image_names = {p.name.lower() for p in scan.images}

    sections: list[ScoreSection] = []
    prop_score = 0
    prop_score += 4 if scan.property_files else 0
    prop_score += 2 if scan.metadata.device != "unknown" else 0
    prop_score += 2 if scan.metadata.android_version != "unknown" else 0
    prop_score += 2 if scan.metadata.fingerprint != "unknown" else 0
    sections.append(ScoreSection("Build properties", _cap(prop_score, 10), 10, f"{len(scan.property_files)} property file(s) detected"))

    blob_score = 0
    blob_score += 8 if blobs else 0
    blob_score += min(len(groups), 8)
    blob_score += 2 if "Camera" in groups else 0
    blob_score += 2 if "Audio" in groups else 0
    sections.append(ScoreSection("Vendor blobs", _cap(blob_score, 20), 20, f"{len(blobs)} candidate blob(s), {len(groups)} category group(s)"))

    partition_score = 0
    partition_score += 5 if scan.partitions else 0
    partition_score += 3 if "vendor" in scan.partitions else 0
    partition_score += 3 if "system" in scan.partitions else 0
    partition_score += 3 if "boot.img" in image_names else 0
    partition_score += 3 if "vendor_boot.img" in image_names else 0
    partition_score += 3 if "super.img" in image_names or len(scan.partitions) >= 3 else 0
    sections.append(ScoreSection("Partitions and images", _cap(partition_score, 20), 20, f"{len(scan.partitions)} extracted partition folder(s), {len(scan.images)} image file(s)"))

    vintf_score = 0
    vintf_score += 8 if scan.vintf_files else 0
    vintf_score += 4 if any("manifest" in p.name.lower() for p in scan.vintf_files) else 0
    vintf_score += 3 if any("compatibility_matrix" in p.name.lower() for p in scan.vintf_files) else 0
    sections.append(ScoreSection("VINTF files", _cap(vintf_score, 15), 15, f"{len(scan.vintf_files)} VINTF XML file(s)"))

    init_score = 0
    init_score += 7 if scan.init_files else 0
    init_score += 6 if scan.fstab_files else 0
    init_score += 2 if scan.sepolicy_paths else 0
    sections.append(ScoreSection("Init, fstab and sepolicy", _cap(init_score, 15), 15, f"{len(scan.init_files)} init file(s), {len(scan.fstab_files)} fstab file(s), {len(scan.sepolicy_paths)} sepolicy folder(s)"))

    kernel_score = 0
    kernel_score += 3 if "boot.img" in image_names else 0
    kernel_score += 2 if "dtbo.img" in image_names else 0
    kernel_score += 2 if "vendor_boot.img" in image_names else 0
    kernel_score += 1 if scan.metadata.platform != "unknown" else 0
    sections.append(ScoreSection("Kernel and boot hints", _cap(kernel_score, 10), 10, "Boot, vendor_boot, DTBO and platform hints"))

    generated_score = 10 if scan.property_files and blobs and scan.vintf_files else 6 if scan.property_files and blobs else 3 if scan.property_files else 0
    sections.append(ScoreSection("Generation readiness", generated_score, 10, "Estimated readiness for starter tree generation"))

    total = sum(section.score for section in sections)
    maximum = sum(section.maximum for section in sections)
    return ReadinessScore(total=total, maximum=maximum, sections=sections)


def build_score_markdown(dump: Path | str) -> str:
    score = compute_readiness_score(dump)
    lines = [
        "# Bring-up Readiness Score",
        "",
        f"**Score:** {score.total}/{score.maximum} ({score.percentage}%)",
        "",
        "| Area | Score | Notes |",
        "| --- | ---: | --- |",
    ]
    for section in score.sections:
        lines.append(f"| {section.name} | {section.score}/{section.maximum} | {section.note} |")
    lines.extend(
        [
            "",
            "## How to read this score",
            "",
            "The score is a bring-up quality hint, not a guarantee that a ROM will boot. Always verify partition layout, kernel sources, vendor blobs and device-specific flags manually.",
            "",
        ]
    )
    return "\n".join(lines)


def write_score_markdown(dump: Path | str, output: Path | str) -> ReadinessScore:
    write_text(Path(output), build_score_markdown(dump))
    return compute_readiness_score(dump)


def write_score_json(dump: Path | str, output: Path | str) -> ReadinessScore:
    score = compute_readiness_score(dump)
    write_json(Path(output), score.to_dict())
    return score
