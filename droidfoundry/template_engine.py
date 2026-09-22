from __future__ import annotations

from importlib.resources import files
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def get_environment() -> Environment:
    template_root = files("droidfoundry") / "templates"
    return Environment(
        loader=FileSystemLoader(str(template_root)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template(name: str, **context: Any) -> str:
    env = get_environment()
    return env.get_template(name).render(**context)
