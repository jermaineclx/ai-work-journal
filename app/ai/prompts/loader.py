"""Loads versioned prompt templates from disk.

Prompts are first-class, version-controlled Markdown assets
(03_IMPLEMENTATION.md §19, "Prompt Organisation") — never embedded as
Python string literals. The filename stem (e.g. ``extract_entities_v1``)
*is* the prompt version, so every AI response can record exactly which
prompt produced it.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


@lru_cache
def load_prompt(name: str) -> str:
    """Load a prompt template by version-qualified name, e.g. 'extract_entities_v1'."""
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def latest_version(prefix: str) -> str:
    """Return the highest version name for a given prompt prefix, e.g. 'extract_entities'."""
    candidates = sorted(_PROMPTS_DIR.glob(f"{prefix}_v*.md"))
    if not candidates:
        raise FileNotFoundError(f"No prompt templates found for prefix '{prefix}'")
    return candidates[-1].stem


def render_prompt(template: str, **placeholders: str) -> str:
    """Substitute ``<<NAME>>`` markers in a prompt template.

    Deliberately not ``str.format`` — prompt templates contain literal
    JSON/curly-brace examples that would collide with format placeholders.
    """
    rendered = template
    for key, value in placeholders.items():
        rendered = rendered.replace(f"<<{key}>>", value if value else "(none)")
    return rendered
