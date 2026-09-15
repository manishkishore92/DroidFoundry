from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .template_engine import render_template
from .utils import write_text


@dataclass(slots=True)
class ManifestInput:
    github: str
    brand: str
    device: str
    branch: str
    device_repo: str | None = None
    kernel_repo: str | None = None
    vendor_repo: str | None = None

    @property
    def device_project(self) -> str:
        return self.device_repo or f"{self.github}/android_device_{self.brand}_{self.device}"

    @property
    def kernel_project(self) -> str:
        return self.kernel_repo or f"{self.github}/android_kernel_{self.brand}_{self.device}"

    @property
    def vendor_project(self) -> str:
        return self.vendor_repo or f"{self.github}/proprietary_vendor_{self.brand}_{self.device}"


def generate_manifest(data: ManifestInput) -> str:
    return render_template("roomservice.xml.j2", data=data)


def write_manifest(data: ManifestInput, output: Path | str) -> None:
    write_text(Path(output), generate_manifest(data))
