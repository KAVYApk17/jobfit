"""Prompts live in versioned files; the version string is stored with each result."""

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache
def load_prompt(version: str) -> str:
    return (PROMPTS_DIR / f"{version}.txt").read_text(encoding="utf-8")


def render_prompt(version: str, **values: str) -> str:
    # Plain replacement, not str.format: resume and JD text often contain braces.
    prompt = load_prompt(version)
    for key, value in values.items():
        prompt = prompt.replace("{" + key + "}", value)
    return prompt
