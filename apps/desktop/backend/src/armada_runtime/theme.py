"""The per-user theme file: the light or dark choice, written by the app whenever it changes.

Kept apart from settings.yaml, which the user edits and the app never rewrites."""

import os
from enum import StrEnum
from pathlib import Path
from typing import cast

import yaml


class ThemePreference(StrEnum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class ThemeFile:
    """A missing or damaged file reads as SYSTEM, which only means following the OS again."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def theme_preference(self) -> ThemePreference:
        try:
            content: object = yaml.safe_load(self._path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return ThemePreference.SYSTEM
        if not isinstance(content, dict):
            return ThemePreference.SYSTEM
        value = cast(dict[str, object], content).get("preference")
        if not isinstance(value, str) or value not in ThemePreference.__members__.values():
            return ThemePreference.SYSTEM
        return ThemePreference(value)

    def set_theme_preference(self, preference: ThemePreference) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Written beside the target and swapped in, so a crash never leaves half a file.
        partial = self._path.with_name(f"{self._path.name}.partial")
        partial.write_text(
            "# Written by the app when you pick a theme. Delete it to follow your system again.\n"
            f"preference: {preference.value}\n",
            encoding="utf-8",
        )
        os.replace(partial, self._path)
