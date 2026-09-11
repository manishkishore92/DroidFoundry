from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .blobs import BlobGenerator
from .boardconfig import write_boardconfig_hints
from .classifier import classify_blobs, render_grouped_proprietary_files, write_grouped_blobs
from .compare import write_compare_report
from .config import load_config, merge_config, write_default_config
from .console import console, print_paths, print_scan_summary
from .doctor import doctor_score, run_doctor
from .generators import BringupGenerator
from .init_scan import write_init_report
from .intelligence import run_intelligence_report
from .issues import detect_issues, write_issues_json, write_issues_markdown
from .scoring import compute_readiness_score, write_score_json, write_score_markdown
from .hardware import build_hardware_map, write_hardware_json, write_hardware_markdown
from .html_report import write_html_report
from .properties_intel import property_summary, write_properties_json, write_properties_markdown
from .patcher import create_tree_patches
from .exporters import export_android_es, export_rom_harbor
from .manifest import ManifestInput, write_manifest
from .partitions import write_partition_report
from .report import write_report
from .scanner import FirmwareScanner
from .tree_inspector import build_tree_report, write_tree_report
from .updater import update_tree_from_dump
from .utils import write_json
from .vintf import write_vintf_report
from .wizard import run_wizard

app = typer.Typer(
    name="droidfoundry",
    help="Android device bring-up assistant for firmware dumps.",
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show DroidFoundry version and exit."),
) -> None:
    if version:
        console.print(f"DroidFoundry {__version__}")
        raise typer.Exit()


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Folder where foundry.yml should be created."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing foundry.yml."),
) -> None:
    """Create a starter DroidFoundry config file."""
    config_path = path / "foundry.yml"
    if config_path.exists() and not force:
        raise typer.BadParameter(f"Config already exists: {config_path}. Use --force to replace it.")
    write_default_config(config_path)
    console.print(f"[green]Created[/green] {config_path}")


@app.command()
def wizard() -> None:
    """Open an interactive bring-up workspace generator."""
    run_wizard()


@app.command()
def scan(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    json_out: Optional[Path] = typer.Option(None, "--json-out", help="Write full scan data as JSON."),
    show_files: bool = typer.Option(False, "--show-files", help="Show detected image, VINTF, init and fstab files."),
) -> None:
    """Scan a firmware dump and print detected device information."""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Scanning firmware dump...", total=None)
        result = FirmwareScanner(dump).scan()
        progress.remove_task(task)

    print_scan_summary(result)
    if show_files:
        print_paths("Images", result.images, result.root)
        print_paths("VINTF files", result.vintf_files, result.root)
        print_paths("Init files", result.init_files, result.root)
        print_paths("Fstab files", result.fstab_files, result.root)

    if json_out:
        write_json(json_out, result.to_dict())
        console.print(f"[green]Wrote scan JSON:[/green] {json_out}")


@app.command()
def doctor(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
) -> None:
    """Check whether a firmware dump has enough data for bring-up work."""
    checks = run_doctor(dump)
    ok, total = doctor_score(checks)
    table = Table(title=f"Firmware dump doctor: {ok}/{total} checks OK")
    table.add_column("Status", style="bold")
    table.add_column("Check")
    table.add_column("Detail", overflow="fold")
    table.add_column("Suggested fix", overflow="fold")
    for check in checks:
        style = "green" if check.status == "OK" else ("yellow" if check.status == "WARN" else "red")
        table.add_row(f"[{style}]{check.status}[/{style}]", check.name, check.detail, check.fix or "-")
    console.print(table)


@app.command()
def blobs(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write proprietary-files.txt."),
    limit: int = typer.Option(50, "--limit", help="Number of entries to preview."),
    grouped: bool = typer.Option(True, "--grouped/--flat", help="Group entries by likely hardware area."),
) -> None:
    """Generate a candidate proprietary-files list."""
    generator = BlobGenerator(dump)
    candidates = generator.collect()
    console.print(f"[bold]Candidate blobs:[/bold] {len(candidates)}")
    if grouped:
        groups = classify_blobs(candidates)
        for category, items in groups.items():
            console.print(f"\n[bold cyan]{category}[/bold cyan] ({len(items)})")
            for item in items[: min(limit, 15)]:
                console.print(f"  {item}")
            if len(items) > min(limit, 15):
                console.print(f"  ... {len(items) - min(limit, 15)} more")
    else:
        for item in candidates[:limit]:
            console.print(f"  {item}")
        if len(candidates) > limit:
            console.print(f"  ... {len(candidates) - limit} more")
    if output:
        if grouped:
            write_grouped_blobs(dump, output)
        else:
            generator.write(output)
        console.print(f"[green]Wrote blob list:[/green] {output}")


@app.command("classify-blobs")
def classify_blobs_command(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("proprietary-files.txt"), "--output", "-o", help="Output grouped proprietary-files.txt."),
) -> None:
    """Write a grouped proprietary-files.txt by hardware area."""
    groups = write_grouped_blobs(dump, output)
    console.print(f"[green]Wrote grouped blob list:[/green] {output}")
    for category, items in groups.items():
        console.print(f"- {category}: {len(items)}")


@app.command()
def boardconfig(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("BoardConfig.hints.mk"), "--output", "-o", help="Output BoardConfig hints file."),
    brand: Optional[str] = typer.Option(None, "--brand", help="Override detected brand/vendor."),
    device: Optional[str] = typer.Option(None, "--device", help="Override detected device codename."),
) -> None:
    """Generate BoardConfig hint lines from firmware metadata."""
    write_boardconfig_hints(dump, output, brand=brand, device=device)
    console.print(f"[green]Wrote BoardConfig hints:[/green] {output}")


@app.command()
def partitions(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("partition-report.md"), "--output", "-o", help="Output Markdown report."),
) -> None:
    """Analyze partition folders and image files."""
    write_partition_report(dump, output)
    console.print(f"[green]Wrote partition report:[/green] {output}")


@app.command()
def vintf(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("vintf-report.md"), "--output", "-o", help="Output Markdown report."),
) -> None:
    """Analyze VINTF manifest and compatibility matrix XML files."""
    write_vintf_report(dump, output)
    console.print(f"[green]Wrote VINTF report:[/green] {output}")


@app.command("init-scan")
def init_scan(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("init-fstab-report.md"), "--output", "-o", help="Output Markdown report."),
) -> None:
    """Scan init rc files and fstab entries."""
    write_init_report(dump, output)
    console.print(f"[green]Wrote init/fstab report:[/green] {output}")


@app.command("inspect-tree")
def inspect_tree(
    tree: Path = typer.Argument(..., help="Path to an existing Android device tree."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write Markdown report instead of only printing."),
) -> None:
    """Inspect an existing Android device tree and highlight missing review points."""
    if output:
        write_tree_report(tree, output)
        console.print(f"[green]Wrote device tree report:[/green] {output}")
    else:
        console.print(build_tree_report(tree))


@app.command()
def update(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    tree: Path = typer.Option(..., "--tree", help="Existing device tree to update."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Apply updates. Without this, existing files are backed up/skipped."),
) -> None:
    """Safely update proprietary-files and generated report in an existing tree."""
    result = update_tree_from_dump(dump, tree, yes=yes)
    console.print(f"[green]Changed:[/green] {len(result.changed)}")
    for path in result.changed:
        console.print(f"  {path}")
    if result.backups:
        console.print(f"[yellow]Backups:[/yellow] {len(result.backups)}")
        for path in result.backups:
            console.print(f"  {path}")
    if result.skipped:
        console.print(f"[dim]Skipped:[/dim] {len(result.skipped)}")


@app.command()
def compare(
    old_dump: Path = typer.Argument(..., help="Older firmware dump folder."),
    new_dump: Path = typer.Argument(..., help="Newer firmware dump folder."),
    output: Path = typer.Option(Path("firmware-compare.md"), "--output", "-o", help="Output Markdown report."),
) -> None:
    """Compare two firmware dumps for metadata, blob and file changes."""
    write_compare_report(old_dump, new_dump, output)
    console.print(f"[green]Wrote firmware comparison:[/green] {output}")


@app.command()
def manifest(
    github: str = typer.Option(..., "--github", help="GitHub username or organization."),
    brand: str = typer.Option(..., "--brand", help="Device vendor/brand, for example xiaomi."),
    device: str = typer.Option(..., "--device", help="Device codename, for example sweet."),
    branch: str = typer.Option("lineage-22.2", "--branch", help="Manifest revision/branch."),
    output: Path = typer.Option(Path("roomservice.xml"), "--output", "-o", help="Output XML file."),
) -> None:
    """Create a local manifest for device, kernel and vendor repos."""
    data = ManifestInput(github=github, brand=brand, device=device, branch=branch)
    write_manifest(data, output)
    console.print(f"[green]Wrote manifest:[/green] {output}")


@app.command()
def report(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("bringup-report.md"), "--output", "-o", help="Output report path."),
) -> None:
    """Write a maintainer bring-up report in Markdown."""
    scan_result = write_report(dump, output)
    console.print(f"[green]Wrote report:[/green] {output}")
    console.print(f"Device: [bold]{scan_result.metadata.device}[/bold]")


@app.command()
def generate(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    config: Optional[Path] = typer.Option(None, "--config", help="Optional foundry.yml file."),
    brand: Optional[str] = typer.Option(None, "--brand", help="Device brand/vendor."),
    device: Optional[str] = typer.Option(None, "--device", help="Device codename."),
    vendor: Optional[str] = typer.Option(None, "--vendor", help="Vendor path name. Defaults to brand."),
    rom: Optional[str] = typer.Option(None, "--rom", help="ROM product prefix, for example lineage or aosp."),
    branch: Optional[str] = typer.Option(None, "--branch", help="ROM source branch."),
    github: Optional[str] = typer.Option(None, "--github", help="GitHub username or organization."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output folder."),
    force: bool = typer.Option(False, "--force", help="Allow writing into a non-empty output folder."),
) -> None:
    """Generate a device tree skeleton, blob list, manifest and reports."""
    base_config = load_config(config) if config else load_config("foundry.yml")
    merged = merge_config(
        base_config,
        {
            "brand": brand,
            "device": device,
            "vendor": vendor,
            "rom": rom,
            "branch": branch,
            "github": github,
            "output": str(output) if output else None,
        },
    )

    result = BringupGenerator(dump, merged).generate(force=force)
    console.print("[green]Generated bring-up workspace[/green]")
    console.print(f"Output: {result.output_root}")
    console.print(f"Device tree: {result.device_tree}")
    console.print(f"Vendor tree: {result.vendor_tree}")
    console.print(f"Files written: {len(result.files)}")


@app.command()
def intelligence(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("foundry-report"), "--output", "-o", help="Output report folder."),
    github: str = typer.Option("manishkishore92", "--github", help="GitHub username or organization for generated manifest/export files."),
    rom: str = typer.Option("lineage", "--rom", help="ROM product prefix for generated exports."),
    branch: str = typer.Option("lineage-22.2", "--branch", help="ROM branch for generated manifest."),
) -> None:
    """Run the full DroidFoundry intelligence pipeline."""
    files = run_intelligence_report(dump, output, github=github, rom=rom, branch=branch)
    console.print(f"[green]Wrote intelligence report:[/green] {Path(output).resolve()}")
    console.print(f"Files written: {len(files)}")


@app.command()
def score(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write Markdown score report."),
    json_out: Optional[Path] = typer.Option(None, "--json-out", help="Write score data as JSON."),
) -> None:
    """Calculate a bring-up readiness score."""
    result = compute_readiness_score(dump)
    console.print(f"[bold]Bring-up readiness:[/bold] {result.total}/{result.maximum} ({result.percentage}%)")
    table = Table(title="Readiness sections")
    table.add_column("Area")
    table.add_column("Score", justify="right")
    table.add_column("Notes", overflow="fold")
    for section in result.sections:
        table.add_row(section.name, f"{section.score}/{section.maximum}", section.note)
    console.print(table)
    if output:
        write_score_markdown(dump, output)
        console.print(f"[green]Wrote score report:[/green] {output}")
    if json_out:
        write_score_json(dump, json_out)
        console.print(f"[green]Wrote score JSON:[/green] {json_out}")


@app.command()
def issues(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write Markdown issue report."),
    json_out: Optional[Path] = typer.Option(None, "--json-out", help="Write issues as JSON."),
) -> None:
    """Detect likely bring-up issues in a firmware dump."""
    found = detect_issues(dump)
    table = Table(title=f"Detected issues: {len(found)}")
    table.add_column("Severity")
    table.add_column("Issue", overflow="fold")
    table.add_column("Recommended action", overflow="fold")
    for issue in found:
        style = "red" if issue.severity == "HIGH" else "yellow" if issue.severity == "MEDIUM" else "cyan"
        table.add_row(f"[{style}]{issue.severity}[/{style}]", issue.title, issue.recommendation)
    console.print(table)
    if output:
        write_issues_markdown(dump, output)
        console.print(f"[green]Wrote issue report:[/green] {output}")
    if json_out:
        write_issues_json(dump, json_out)
        console.print(f"[green]Wrote issues JSON:[/green] {json_out}")


@app.command()
def props(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write Markdown property report."),
    json_out: Optional[Path] = typer.Option(None, "--json-out", help="Write property summary as JSON."),
) -> None:
    """Show Android property intelligence from build.prop files."""
    summary = property_summary(dump)
    table = Table(title="Android property intelligence")
    table.add_column("Field")
    table.add_column("Value", overflow="fold")
    for key, value in summary.items():
        table.add_row(key, value)
    console.print(table)
    if output:
        write_properties_markdown(dump, output)
        console.print(f"[green]Wrote property report:[/green] {output}")
    if json_out:
        write_properties_json(dump, json_out)
        console.print(f"[green]Wrote property JSON:[/green] {json_out}")


@app.command()
def hardware(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write Markdown hardware map."),
    json_out: Optional[Path] = typer.Option(None, "--json-out", help="Write hardware map as JSON."),
) -> None:
    """Create a hardware support map from blobs and VINTF files."""
    entries = build_hardware_map(dump)
    table = Table(title="Hardware map")
    table.add_column("Area")
    table.add_column("Status")
    table.add_column("Evidence", overflow="fold")
    for entry in entries:
        style = "green" if entry.status == "Detected" else "yellow" if entry.status == "Unknown" else "red"
        table.add_row(entry.name, f"[{style}]{entry.status}[/{style}]", "; ".join(entry.evidence) if entry.evidence else "-")
    console.print(table)
    if output:
        write_hardware_markdown(dump, output)
        console.print(f"[green]Wrote hardware map:[/green] {output}")
    if json_out:
        write_hardware_json(dump, json_out)
        console.print(f"[green]Wrote hardware JSON:[/green] {json_out}")


@app.command("html-report")
def html_report(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("foundry-report.html"), "--output", "-o", help="Output HTML file."),
) -> None:
    """Generate a standalone offline HTML intelligence report."""
    write_html_report(dump, output)
    console.print(f"[green]Wrote HTML report:[/green] {output}")


@app.command()
def patch(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    tree: Path = typer.Option(..., "--tree", help="Existing device tree folder."),
    output: Path = typer.Option(Path("patches"), "--output", "-o", help="Output patch folder."),
) -> None:
    """Create reviewable patches for an existing device tree."""
    result = create_tree_patches(dump, tree, output)
    console.print(f"[green]Generated patches:[/green] {len(result.patches)}")
    for path in result.patches:
        console.print(f"  {path}")


@app.command("update-assistant")
def update_assistant(
    old_dump: Path = typer.Argument(..., help="Older firmware dump folder."),
    new_dump: Path = typer.Argument(..., help="Newer firmware dump folder."),
    output: Path = typer.Option(Path("firmware-update-assistant.md"), "--output", "-o", help="Output Markdown report."),
) -> None:
    """Compare firmware updates and recommend maintainer actions."""
    write_compare_report(old_dump, new_dump, output)
    with output.open("a", encoding="utf-8") as handle:
        handle.write("\n## Recommended maintainer actions\n\n")
        handle.write("- Regenerate proprietary-files.txt from the newer dump.\n")
        handle.write("- Review VINTF changes before syncing device trees.\n")
        handle.write("- Re-extract vendor blobs and test camera, Wi-Fi, Bluetooth, fingerprint, radio and media.\n")
        handle.write("- Rebuild once and save logs for comparison with the previous build.\n")
    console.print(f"[green]Wrote update assistant report:[/green] {output}")


@app.command("export-rom-harbor")
def export_rom_harbor_command(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("rom-harbor-export"), "--output", "-o", help="Output folder."),
) -> None:
    """Export device and hardware metadata for ROM Harbor."""
    files = export_rom_harbor(dump, output)
    console.print(f"[green]Wrote ROM Harbor export:[/green] {Path(output).resolve()}")
    for path in files:
        console.print(f"  {path}")


@app.command("export-android-es")
def export_android_es_command(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
    output: Path = typer.Option(Path("android-es-export"), "--output", "-o", help="Output folder."),
    rom: str = typer.Option("lineage", "--rom", help="ROM product prefix for generated lunch target."),
) -> None:
    """Export an Android ES profile and report."""
    files = export_android_es(dump, output, rom=rom)
    console.print(f"[green]Wrote Android ES export:[/green] {Path(output).resolve()}")
    for path in files:
        console.print(f"  {path}")


@app.command()
def inspect(
    dump: Path = typer.Argument(..., help="Path to an extracted firmware dump."),
) -> None:
    """Print compact JSON metadata for scripts and automation."""
    result = FirmwareScanner(dump).scan()
    console.print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()
