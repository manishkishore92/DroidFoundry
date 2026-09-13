from __future__ import annotations

from html import escape
from pathlib import Path

from .hardware import build_hardware_map
from .issues import detect_issues
from .recommendations import recommended_next_steps
from .scanner import FirmwareScanner
from .scoring import compute_readiness_score
from .utils import file_size_human, write_text


def _badge(value: str) -> str:
    lower = value.lower()
    cls = "ok" if lower in {"detected", "ok"} else "warn" if lower in {"unknown", "medium", "low"} else "bad"
    return f'<span class="badge {cls}">{escape(value)}</span>'


def build_html_report(dump: Path | str) -> str:
    scan = FirmwareScanner(dump).scan()
    score = compute_readiness_score(dump)
    issues = detect_issues(dump)
    hardware = build_hardware_map(dump)
    steps = recommended_next_steps(dump)
    meta = scan.metadata
    issue_rows = "".join(
        f"<tr><td>{_badge(issue.severity)}</td><td><strong>{escape(issue.title)}</strong><br><small>{escape(issue.detail)}</small></td><td>{escape(issue.recommendation)}</td></tr>"
        for issue in issues
    ) or '<tr><td colspan="3">No obvious blockers were detected.</td></tr>'
    hardware_rows = "".join(
        f"<tr><td>{escape(entry.name)}</td><td>{_badge(entry.status)}</td><td>{escape('; '.join(entry.evidence) if entry.evidence else '-')}</td></tr>"
        for entry in hardware
    )
    section_rows = "".join(
        f"<tr><td>{escape(section.name)}</td><td>{section.score}/{section.maximum}</td><td>{escape(section.note)}</td></tr>"
        for section in score.sections
    )
    step_items = "".join(f"<li>{escape(step)}</li>" for step in steps)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DroidFoundry Report - {escape(meta.device)}</title>
<style>
:root {{ color-scheme: dark; --bg:#0d1117; --panel:#151b23; --text:#e6edf3; --muted:#8b949e; --line:#30363d; --accent:#7c3aed; --green:#2ea043; --yellow:#d29922; --red:#f85149; }}
* {{ box-sizing:border-box; }} body {{ margin:0; font-family:Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; background:var(--bg); color:var(--text); }}
main {{ max-width:1100px; margin:0 auto; padding:42px 20px 64px; }}
.hero {{ padding:28px; border:1px solid var(--line); border-radius:24px; background:linear-gradient(135deg, rgba(124,58,237,.25), rgba(21,27,35,.95)); }}
h1 {{ margin:0; font-size:40px; }} p {{ color:var(--muted); line-height:1.7; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin-top:18px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:18px; }}
.card span {{ color:var(--muted); font-size:13px; }} .card strong {{ display:block; margin-top:6px; font-size:20px; }}
table {{ width:100%; border-collapse:collapse; margin-top:12px; overflow:hidden; border-radius:12px; }} th,td {{ border-bottom:1px solid var(--line); padding:12px; text-align:left; vertical-align:top; }} th {{ color:var(--muted); font-weight:600; }}
section {{ margin-top:30px; }} h2 {{ font-size:24px; }} .badge {{ border-radius:999px; padding:4px 9px; font-size:12px; font-weight:700; }} .ok {{ background:rgba(46,160,67,.18); color:#56d364; }} .warn {{ background:rgba(210,153,34,.18); color:#e3b341; }} .bad {{ background:rgba(248,81,73,.18); color:#ff7b72; }}
.score {{ font-size:54px; font-weight:800; color:#c4b5fd; }} code {{ color:#c4b5fd; }}
</style>
</head>
<body><main>
<div class="hero"><h1>DroidFoundry Report</h1><p>Firmware intelligence and Android bring-up analysis for <strong>{escape(meta.device)}</strong>.</p></div>
<div class="grid">
<div class="card"><span>Device</span><strong>{escape(meta.brand)} {escape(meta.model)}</strong></div>
<div class="card"><span>Codename</span><strong>{escape(meta.device)}</strong></div>
<div class="card"><span>Android</span><strong>{escape(meta.android_version)}</strong></div>
<div class="card"><span>Security Patch</span><strong>{escape(meta.security_patch)}</strong></div>
<div class="card"><span>Files</span><strong>{scan.stats.total_files}</strong></div>
<div class="card"><span>Dump Size</span><strong>{file_size_human(scan.stats.total_size)}</strong></div>
</div>
<section><h2>Bring-up Readiness</h2><div class="score">{score.total}/{score.maximum}</div><table><thead><tr><th>Area</th><th>Score</th><th>Notes</th></tr></thead><tbody>{section_rows}</tbody></table></section>
<section><h2>Hardware Map</h2><table><thead><tr><th>Area</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{hardware_rows}</tbody></table></section>
<section><h2>Detected Issues</h2><table><thead><tr><th>Priority</th><th>Issue</th><th>Recommended action</th></tr></thead><tbody>{issue_rows}</tbody></table></section>
<section><h2>Recommended Next Steps</h2><ol>{step_items}</ol></section>
</main></body></html>
"""


def write_html_report(dump: Path | str, output: Path | str) -> str:
    content = build_html_report(dump)
    write_text(Path(output), content)
    return content
