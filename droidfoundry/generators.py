from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .blobs import BlobGenerator
from .classifier import render_grouped_proprietary_files
from .manifest import ManifestInput, generate_manifest
from .boardconfig import build_boardconfig_hints
from .partitions import build_partition_report
from .vintf import build_vintf_report
from .init_scan import build_init_report
from .models import FirmwareScan, ProjectConfig
from .scanner import FirmwareScanner
from .template_engine import render_template
from .utils import file_size_human, normalize_name, relative_posix, write_json, write_text


@dataclass(slots=True)
class GenerationResult:
    output_root: Path
    device_tree: Path
    vendor_tree: Path
    files: list[Path]


class BringupGenerator:
    def __init__(self, dump: Path | str, config: ProjectConfig):
        self.dump = Path(dump).expanduser().resolve()
        self.config = config

    def generate(self, force: bool = False) -> GenerationResult:
        scan = FirmwareScanner(self.dump).scan()
        brand = normalize_name(self.config.brand if self.config.brand != "unknown" else scan.metadata.brand)
        device = normalize_name(self.config.device if self.config.device != "unknown" else scan.metadata.device)
        vendor = normalize_name(self.config.vendor if self.config.vendor != "unknown" else brand)
        rom = normalize_name(self.config.rom, "aosp")
        branch = self.config.branch
        github = self.config.github

        output_root = Path(self.config.output).expanduser().resolve()
        device_tree = output_root / "device" / vendor / device
        vendor_tree = output_root / "vendor" / vendor / device

        if output_root.exists() and any(output_root.iterdir()) and not force:
            raise FileExistsError(
                f"Output directory is not empty: {output_root}. Use --force to write into it."
            )

        blobs = BlobGenerator(self.dump).collect()
        context = {
            "scan": scan,
            "metadata": scan.metadata,
            "brand": brand,
            "device": device,
            "vendor": vendor,
            "rom": rom,
            "branch": branch,
            "github": github,
            "rom_product": f"{rom}_{device}",
            "blob_count": len(blobs),
            "file_size_human": file_size_human,
            "rel": lambda p: relative_posix(p, scan.root),
        }

        files: list[Path] = []
        file_map = {
            device_tree / "AndroidProducts.mk": "AndroidProducts.mk.j2",
            device_tree / "BoardConfig.mk": "BoardConfig.mk.j2",
            device_tree / "device.mk": "device.mk.j2",
            device_tree / f"{rom}_{device}.mk": "rom_device.mk.j2",
            device_tree / "vendorsetup.sh": "vendorsetup.sh.j2",
            device_tree / "extract-files.sh": "extract-files.sh.j2",
            device_tree / "setup-makefiles.sh": "setup-makefiles.sh.j2",
            device_tree / "README.md": "device-readme.md.j2",
            vendor_tree / f"{device}-vendor.mk": "vendor-device.mk.j2",
            output_root / ".repo" / "local_manifests" / "roomservice.xml": None,
            output_root / "reports" / "bringup-report.md": "bringup-report.md.j2",
            output_root / "metadata" / "scan.json": None,
        }

        for target, template in file_map.items():
            if template is None:
                if target.name == "roomservice.xml":
                    manifest = generate_manifest(
                        ManifestInput(
                            github=github,
                            brand=vendor,
                            device=device,
                            branch=branch,
                        )
                    )
                    write_text(target, manifest)
                elif target.name == "scan.json":
                    write_json(target, scan.to_dict())
                else:
                    continue
            else:
                write_text(target, render_template(template, **context))
            if target.suffix == ".sh":
                target.chmod(0o755)
            files.append(target)

        proprietary = render_grouped_proprietary_files(blobs)
        prop_path = device_tree / "proprietary-files.txt"
        write_text(prop_path, proprietary)
        files.append(prop_path)

        advanced_reports = {
            output_root / "reports" / "BoardConfig.hints.mk": build_boardconfig_hints(self.dump, brand=vendor, device=device),
            output_root / "reports" / "partition-report.md": build_partition_report(self.dump),
            output_root / "reports" / "vintf-report.md": build_vintf_report(self.dump),
            output_root / "reports" / "init-fstab-report.md": build_init_report(self.dump),
        }
        for target, content in advanced_reports.items():
            write_text(target, content)
            files.append(target)

        return GenerationResult(output_root=output_root, device_tree=device_tree, vendor_tree=vendor_tree, files=files)
