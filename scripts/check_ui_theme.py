"""Check that the UI theme meets WCAG standards.

WCAG AA contrast between the theme's colour tokens, and no literal colours or
fonts outside the theme, since a literal escapes the contrast check.

    python scripts/check_ui_theme.py              both checks
    python scripts/check_ui_theme.py contrast     token contrast only (--verbose lists every pair)
    python scripts/check_ui_theme.py literals     literal colours and fonts only

    contrast
      theme/*.css ──parse :root──▶ tokens {name: value}
                                     │ resolve per theme: var(), light-dark(), color-mix(), hex
                                     ▼
      pairs by naming convention ──▶ WCAG ratio, light and dark ──▶ below 4.5 (text) or 3 (UI)?

    literals
      frontend sources ──each line──▶ hex, rgb()/hsl()/oklch(), palette class, dark:, font-family?

A literal on a line that also says theme-check: allow, with a reason, is skipped.

Standard library only: this runs from git hooks before dependencies exist.

References:
    [1] W3C, "Understanding SC 1.4.3: Contrast (Minimum) (Level AA)," WCAG 2.2. Holds the 4.5:1
        minimum and the glossary's relative luminance and contrast ratio formulas.
        https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
    [2] W3C, "Understanding SC 1.4.11: Non-text Contrast (Level AA)," WCAG 2.2. The 3:1 minimum for
        user interface components, including focus indicators.
        https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html
    [3] W3C, "CSS Color Module Level 5," Working Draft, section color-mix(): how mix percentages
        are normalised, and why a mix whose percentages sum below 100% is translucent.
        https://www.w3.org/TR/css-color-5/#color-mix
    [4] W3C, "CSS Color Module Level 5," Working Draft, section light-dark(): the first colour for a
        light color-scheme, the second for dark. https://www.w3.org/TR/css-color-5/#light-dark
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME_FOLDER = Path("packages", "ui-kit", "src", "theme")
THEME = ROOT / THEME_FOLDER
THEME_FILES = ("defaults.css", "fixed.css")

MODES = ("light", "dark")
# Minimum contrast ratios at WCAG AA. They are thresholds, never rounded: 4.49:1 fails.
TEXT = 4.5  # normal-size text [1]
UI = 3.0  # focus indicators and other user interface components [2]

# The relative luminance formula [1]. A channel's 8-bit value is divided by CHANNEL_MAX, then
# linearised by the sRGB transfer function: dark values scale linearly (divide by
# SRGB_LINEAR_SLOPE), lighter ones follow a 2.4 power curve. WCAG 2.x printed the threshold as
# 0.03928 before May 2021; it has no practical effect on results [1].
CHANNEL_MAX = 255
SRGB_THRESHOLD = 0.04045
SRGB_LINEAR_SLOPE = 12.92
SRGB_OFFSET = 0.055
SRGB_SCALE = 1.055
SRGB_GAMMA = 2.4
# How bright each linear channel looks to the eye; green dominates [1].
RED_WEIGHT, GREEN_WEIGHT, BLUE_WEIGHT = 0.2126, 0.7152, 0.0722
# Added to both luminances in the contrast ratio, which keeps black from dividing by zero; the
# ratio then runs from 1:1 to 21:1 [1].
FLARE = 0.05

SURFACES = ("background", "card", "secondary", "sidebar")
TEXT_ON_SURFACES = ("foreground", "muted-foreground", "primary")
STATUSES = ("error", "warning", "success", "info")

# Pairs the naming convention does not cover, or covers wrongly, each with its reason.
EXTRA_PAIRS: tuple[tuple[str, str, float, str], ...] = ()
SKIPPED_PAIRS: dict[tuple[str, str], str] = {}

SOURCES = (
    "apps/web/src",
    "apps/web/index.html",
    "apps/desktop/frontend/src",
    "apps/desktop/frontend/index.html",
    "packages/ui-kit/src",
    "packages/slicer/src",
)
SOURCE_SUFFIXES = {".ts", ".tsx", ".css", ".html"}
SKIPPED_PARTS = {"gen", "node_modules"}
SKIPPED_NAME_ENDINGS = (".test.ts", ".test.tsx", ".d.ts")
ALLOW_MARKER = "theme-check: allow"

# Tailwind's built-in colour names, and the utilities that take a colour. Together they match a
# palette class such as hover:bg-red-500/50, which would bypass the theme's tokens.
PALETTE = (
    "slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue"
    "|indigo|violet|purple|fuchsia|pink|rose|white|black"
)
UTILITIES = (
    "bg|text|border(?:-[trblxyse])?|ring|ring-offset|outline|fill|stroke|divide|placeholder"
    "|accent|caret|decoration|from|via|to|shadow"
)
LITERALS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Matches:  color: #cf0722;   bg-[#fff]   '#ffffff80'
    # Ignores:  '#root' (not hex digits)   page#section and &#123; (a letter, & or / before the #)
    (
        "hex colour",
        re.compile(
            r"(?<![\w&/-])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b"
        ),
    ),
    # Matches:  rgb(0 0 0)   rgba(0,0,0,.5)   hsl(210 40% 50%)   oklch(0.7 0.1 200)
    # Ignores:  color-mix(...) and var(...), which only combine tokens
    ("colour function", re.compile(r"\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch)\(")),
    # Matches:  text-slate-600   hover:bg-red-500/50   border-t-gray-200   text-white
    # Ignores:  text-primary-foreground   bg-card   border-border (theme tokens)
    (
        "palette class",
        re.compile(
            rf"(?<![\w-])(?:{UTILITIES})-(?:{PALETTE})(?:-\d{{2,3}})?(?:/\d+)?(?![\w-])"
        ),
    ),
    # A variant runs straight into its class; an object key has a space after the colon.
    # Matches:  dark:bg-card   dark:[--x:1]   dark:!text-white
    # Ignores:  { dark: ThemePreference.DARK }
    ("dark: variant", re.compile(r"(?<![\w-])dark:(?=[\w\[!-])")),
    # Matches:  font-family: Inter;   style={{ fontFamily: 'Inter' }}   font-[Inter]
    # Ignores:  font-sans   font-mono   font-semibold (theme fonts and weights)
    ("font family", re.compile(r"font-family\s*:|fontFamily\s*:|(?<![\w-])font-\[")),
)


class ThemeError(ValueError):
    """A token value the checker cannot resolve to a colour."""


# ── Contrast ─────────────────────────────────────────────────────────────────────────────────


def tokens(css: str) -> dict[str, str]:
    """Every custom property declared in a plain :root block. Blocks scoped to a data-theme only
    switch color-scheme, so their declarations carry no colours."""
    # Removes /* a comment */, including one over several lines.
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    found: dict[str, str] = {}
    # Matches the body of  :root { ... }  but not  :root[data-theme='dark'] { ... }
    for block in re.finditer(r":root\s*\{(.*?)\}", css, flags=re.DOTALL):
        # Matches  --card: #f9fbfd;  as ("card", "#f9fbfd"), and a value wrapped over lines.
        for name, value in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", block.group(1)):
            found[name] = " ".join(value.split())
    return found


def theme_tokens(theme: Path = THEME) -> dict[str, str]:
    merged: dict[str, str] = {}
    for name in THEME_FILES:
        merged.update(tokens((theme / name).read_text(encoding="utf-8")))
    return merged


type Rgb = tuple[float, float, float]


def split_arguments(inner: str) -> list[str]:
    """Splits a function's arguments on the commas outside nested brackets."""
    parts: list[str] = []
    depth, start = 0, 0
    for index, char in enumerate(inner):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(inner[start:index].strip())
            start = index + 1
    parts.append(inner[start:].strip())
    return parts


def call(value: str) -> tuple[str, list[str]] | None:
    # Matches  light-dark(#fff, var(--x))  as ("light-dark", "#fff, var(--x)"); not  #fff
    match = re.fullmatch(r"([\w-]+)\((.*)\)", value.strip(), flags=re.DOTALL)
    if not match:
        return None
    return match.group(1), split_arguments(match.group(2))


def hex_colour(value: str) -> Rgb:
    """A CSS hex colour: #rgb, #rgba, #rrggbb or #rrggbbaa. The short forms double each digit, and
    an alpha byte other than ff is refused, because a translucent colour's contrast depends on
    what is drawn beneath it."""
    digits = value.strip().lstrip("#")
    if len(digits) in (3, 4):
        digits = "".join(c * 2 for c in digits)
    # Accepts  cf0722  and  FFFFFF;  refuses  foobar  (not hex digits)
    if len(digits) not in (6, 8) or not re.fullmatch(r"[0-9a-fA-F]+", digits):
        raise ThemeError(f"{value!r} is not a colour this check understands")
    if len(digits) == 8 and digits[6:].lower() != "ff":
        raise ThemeError(
            f"{value!r} is translucent; its contrast depends on what lies beneath"
        )
    return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))


def resolve(
    value: str, mode: str, table: dict[str, str], seen: tuple[str, ...] = ()
) -> Rgb:
    """The colour a token value draws in one theme."""
    value = value.strip()
    if value.startswith("#"):
        return hex_colour(value)
    parsed = call(value)
    if parsed is None:
        raise ThemeError(f"{value!r} is not a colour this check understands")
    function, arguments = parsed
    if function == "var":
        name = arguments[0].removeprefix("--")
        if name in seen:
            raise ThemeError(f"--{name} refers to itself")
        if name in table:
            return resolve(table[name], mode, table, (*seen, name))
        if len(arguments) > 1:
            return resolve(", ".join(arguments[1:]), mode, table, seen)
        raise ThemeError(f"--{name} is not defined and has no fallback")
    if function == "light-dark":  # [4]
        return resolve(
            arguments[0] if mode == "light" else arguments[1], mode, table, seen
        )
    if function == "color-mix":
        return mix(arguments, mode, table, seen)
    raise ThemeError(f"{function}() is not supported by this check")


def mix(
    arguments: list[str], mode: str, table: dict[str, str], seen: tuple[str, ...]
) -> Rgb:
    """color-mix(in srgb, A p%, B [q%]): mixes the gamma-encoded channels, as the browser does [3].
    No percentages mixes half and half; one percentage leaves the rest to the other colour; two
    that sum above 100% are scaled down to it; two that sum below 100% are refused as translucent."""
    if arguments[0].replace(" ", "") != "insrgb":
        raise ThemeError(f"color-mix({arguments[0]}) is not supported; mix in srgb")

    def part(text: str) -> tuple[Rgb, float | None]:
        # Matches  var(--primary) 85%  as ("var(--primary)", "85"); a colour with no percentage
        # such as  var(--foreground)  does not match and gets None.
        match = re.fullmatch(r"(.*?)\s+(\d+(?:\.\d+)?)%", text.strip())
        if match:
            return resolve(match.group(1), mode, table, seen), float(
                match.group(2)
            ) / 100
        return resolve(text, mode, table, seen), None

    (first, p), (second, q) = part(arguments[1]), part(arguments[2])
    if p is None and q is None:
        p = q = 0.5
    elif p is None:
        p = 1 - (q or 0)
    elif q is None:
        q = 1 - p
    total = p + (q or 0)
    if total < 1:
        # The browser makes such a mix partly transparent, so its contrast depends on what is below.
        raise ThemeError(f"color-mix({', '.join(arguments)}) is translucent")
    weight = p / total
    return (
        first[0] * weight + second[0] * (1 - weight),
        first[1] * weight + second[1] * (1 - weight),
        first[2] * weight + second[2] * (1 - weight),
    )


def luminance(colour: Rgb) -> float:
    """WCAG relative luminance, from 0 for black to 1 for white [1]."""

    def channel(value: float) -> float:
        value /= CHANNEL_MAX
        if value <= SRGB_THRESHOLD:
            return value / SRGB_LINEAR_SLOPE
        return ((value + SRGB_OFFSET) / SRGB_SCALE) ** SRGB_GAMMA

    r, g, b = (channel(c) for c in colour)
    return RED_WEIGHT * r + GREEN_WEIGHT * g + BLUE_WEIGHT * b


def contrast(first: Rgb, second: Rgb) -> float:
    """WCAG contrast ratio, (lighter + 0.05) / (darker + 0.05), from 1 to 21 [1]."""
    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + FLARE) / (darker + FLARE)


def pairs(table: dict[str, str]) -> Iterator[tuple[str, str, float]]:
    """(text token, background token, minimum ratio) for every pair the theme draws together."""
    for name in table:
        base = name.removesuffix("-foreground")
        if base != name and base in table:
            yield name, base, TEXT
            if f"{base}-hover" in table:
                yield name, f"{base}-hover", TEXT
    for text in (*TEXT_ON_SURFACES, *STATUSES):
        for surface in SURFACES:
            yield text, surface, TEXT
    for status in STATUSES:
        yield status, f"{status}-tint", TEXT
        yield "foreground", f"{status}-tint", TEXT
    for surface in SURFACES:
        yield "ring", surface, UI
    for text, background, minimum, _reason in EXTRA_PAIRS:
        yield text, background, minimum


@dataclass(frozen=True)
class Ratio:
    text: str
    background: str
    mode: str
    ratio: float
    minimum: float

    @property
    def passes(self) -> bool:
        return self.ratio >= self.minimum

    def __str__(self) -> str:
        verdict = "ok" if self.passes else "FAILS"
        return (
            f"{self.mode:5}  --{self.text} on --{self.background}: "
            f"{self.ratio:.2f}:1, needs {self.minimum:g}:1  {verdict}"
        )


def ratios(table: dict[str, str]) -> list[Ratio]:
    found: list[Ratio] = []
    for text, background, minimum in pairs(table):
        if (text, background) in SKIPPED_PAIRS:
            continue
        for name in (text, background):
            if name not in table:
                raise ThemeError(f"--{name} is paired by convention but not defined")
        for mode in MODES:
            ratio = contrast(
                resolve(table[text], mode, table),
                resolve(table[background], mode, table),
            )
            found.append(Ratio(text, background, mode, ratio, minimum))
    return found


def check_contrast(table: dict[str, str], verbose: bool = False) -> list[str]:
    try:
        results = ratios(table)
    except ThemeError as error:
        return [f"theme: {error}"]
    if verbose:
        for result in results:
            print(f"  {result}")
    return [f"theme: {result}" for result in results if not result.passes]


# ── Literals ─────────────────────────────────────────────────────────────────────────────────


def source_files(root: Path = ROOT) -> Iterator[Path]:
    for entry in SOURCES:
        path = root / entry
        candidates: Iterable[Path] = (
            [path] if path.is_file() else sorted(path.rglob("*"))
        )
        for file in candidates:
            if not file.is_file() or file.suffix not in SOURCE_SUFFIXES:
                continue
            relative = file.relative_to(root)
            if SKIPPED_PARTS & set(relative.parts) or file.name.endswith(
                SKIPPED_NAME_ENDINGS
            ):
                continue
            if relative.is_relative_to(THEME_FOLDER):
                continue
            yield file


def literals_in(text: str) -> Iterator[tuple[int, str, str]]:
    """(line number, kind, matched text) for every literal colour or font in a file."""
    for number, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        for kind, pattern in LITERALS:
            for match in pattern.finditer(line):
                yield number, kind, match.group(0)


def check_literals(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    for file in source_files(root):
        relative = file.relative_to(root).as_posix()
        for number, kind, text in literals_in(file.read_text(encoding="utf-8")):
            problems.append(
                f"{relative}:{number}: {kind} {text!r}; use a theme token instead"
            )
    return problems


# ── Command line ─────────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "check", nargs="?", choices=("contrast", "literals"), help="run only one"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="list every contrast pair"
    )
    args = parser.parse_args(argv)

    problems: list[str] = []
    if args.check in (None, "contrast"):
        problems += check_contrast(theme_tokens(), args.verbose)
    if args.check in (None, "literals"):
        problems += check_literals()

    if problems:
        print("The UI theme check failed:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print(
            "Rules: packages/ui-kit/AGENTS.md. Fix the colour, or add a pair or exception with "
            "its reason in scripts/check_ui_theme.py.",
            file=sys.stderr,
        )
        return 1
    print("UI theme meets WCAG standards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
