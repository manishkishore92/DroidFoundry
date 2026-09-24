from __future__ import annotations

from pathlib import Path

import typer

from .config import merge_config, ProjectConfig
from .console import console
from .generators import BringupGenerator
from .scanner import FirmwareScanner
from .utils import normalize_name


def run_wizard() -> None:
    console.print("[bold cyan]DroidFoundry Wizard[/bold cyan]")
    console.print("Generate a bring-up workspace from an extracted firmware dump.\n")
    dump = Path(typer.prompt("Firmware dump path", default="./firmware-dump")).expanduser()
    scan = FirmwareScanner(dump).scan()
    meta = scan.metadata
    brand = typer.prompt("Device brand/vendor", default=normalize_name(meta.brand))
    device = typer.prompt("Device codename", default=normalize_name(meta.device))
    vendor = typer.prompt("Vendor path name", default=normalize_name(brand))
    rom = typer.prompt("ROM product prefix", default="lineage")
    branch = typer.prompt("ROM branch", default="lineage-22.2")
    github = typer.prompt("GitHub username/org", default="manishkishore92")
    output = typer.prompt("Output folder", default="foundry-output")
    force = typer.confirm("Write into output folder if it already contains files?", default=False)
    config = merge_config(
        ProjectConfig(),
        {
            "brand": brand,
            "device": device,
            "vendor": vendor,
            "rom": rom,
            "branch": branch,
            "github": github,
            "output": output,
        },
    )
    result = BringupGenerator(dump, config).generate(force=force)
    console.print("\n[green]Generated bring-up workspace[/green]")
    console.print(f"Output: {result.output_root}")
    console.print(f"Device tree: {result.device_tree}")
    console.print(f"Vendor tree: {result.vendor_tree}")
    console.print(f"Files written: {len(result.files)}")

