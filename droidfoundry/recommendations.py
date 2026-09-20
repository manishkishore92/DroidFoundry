from __future__ import annotations

from pathlib import Path

from .hardware import build_hardware_map
from .issues import detect_issues
from .scoring import compute_readiness_score


def recommended_next_steps(dump: Path | str) -> list[str]:
    issues = detect_issues(dump)
    score = compute_readiness_score(dump)
    hardware = build_hardware_map(dump)
    steps: list[str] = []

    if score.percentage < 60:
        steps.append("Re-check the firmware dump extraction. The readiness score is low, so important partition data may be missing.")
    if any(issue.code == "missing-vendor-partition" for issue in issues):
        steps.append("Extract vendor.img or super.img fully before generating final proprietary blob lists.")
    if any(issue.code == "missing-vintf" for issue in issues):
        steps.append("Find vendor/system/product VINTF XML files and compare them with your ROM source compatibility matrix.")
    if any(issue.code == "missing-fstab" for issue in issues):
        steps.append("Extract boot or vendor_boot ramdisk to recover fstab entries for mount, encryption and logical partition flags.")
    missing_hardware = [entry.name for entry in hardware if entry.status == "Missing"]
    if missing_hardware:
        steps.append("Review missing hardware areas before first boot test: " + ", ".join(missing_hardware) + ".")
    steps.extend(
        [
            "Review generated BoardConfig hints manually before copying them into a production device tree.",
            "Use the generated proprietary-files.txt as a starting point, then prune unnecessary blobs after extraction tests.",
            "Build once, save the full log, and use Android ES or DroidFoundry reports to track remaining bring-up issues.",
        ]
    )
    return steps
