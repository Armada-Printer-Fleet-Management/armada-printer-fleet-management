"""Tests for scripts/check_ui_theme.py: token resolution, WCAG contrast pairs and literal scanning.

Standard library only, like the script:

    python -m unittest discover -s scripts/tests
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_ui_theme as theme

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class ParsingTests(unittest.TestCase):
    def test_reads_root_tokens_and_skips_comments_and_theme_blocks(self) -> None:
        css = """
        /* --ignored: #000000; */
        :root {
          color-scheme: light dark;
          --card: #ffffff;
          --muted-foreground: var(
            --brand-muted-foreground,
            light-dark(#4b5b6e, #aeb2ba)
          );
        }
        :root[data-theme='dark'] { color-scheme: dark; }
        """
        self.assertEqual(
            theme.tokens(css),
            {
                "card": "#ffffff",
                "muted-foreground": "var( --brand-muted-foreground, light-dark(#4b5b6e, #aeb2ba) )",
            },
        )

    def test_var_follows_a_token_and_falls_back_when_it_is_undefined(self) -> None:
        table = {"primary": "#112233", "link": "var(--primary)"}
        self.assertEqual(
            theme.resolve("var(--link)", "light", table), (0x11, 0x22, 0x33)
        )
        self.assertEqual(
            theme.resolve("var(--brand-primary, #445566)", "dark", table),
            (0x44, 0x55, 0x66),
        )

    def test_light_dark_picks_each_theme(self) -> None:
        value = "light-dark(#ffffff, #000000)"
        self.assertEqual(theme.resolve(value, "light", {}), WHITE)
        self.assertEqual(theme.resolve(value, "dark", {}), BLACK)

    def test_color_mix_matches_the_browser_in_srgb(self) -> None:
        self.assertEqual(
            theme.resolve("color-mix(in srgb, #ff0000 25%, #0000ff)", "light", {}),
            (63.75, 0, 191.25),
        )
        mixed = theme.resolve(
            "color-mix(in srgb, #ff0000 60%, #0000ff 60%)", "light", {}
        )
        for channel, expected in zip(mixed, (127.5, 0, 127.5), strict=True):
            self.assertAlmostEqual(channel, expected)
        with self.assertRaisesRegex(theme.ThemeError, "translucent"):
            theme.resolve("color-mix(in srgb, #ff0000 30%, #0000ff 10%)", "light", {})
        with self.assertRaisesRegex(theme.ThemeError, "mix in srgb"):
            theme.resolve("color-mix(in oklab, #ff0000 50%, #0000ff)", "light", {})

    def test_unresolvable_values_are_explained(self) -> None:
        cases = {
            "var(--missing)": "not defined and has no fallback",
            "var(--loop)": "refers to itself",
            "#ffffff80": "translucent",
            "hsl(0 0% 0%)": "hsl\\(\\) is not supported",
        }
        for value, message in cases.items():
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(theme.ThemeError, message),
            ):
                theme.resolve(value, "light", {"loop": "var(--loop)"})


class ContrastTests(unittest.TestCase):
    def test_known_wcag_ratios(self) -> None:
        self.assertAlmostEqual(theme.contrast(BLACK, WHITE), 21.0)
        self.assertAlmostEqual(theme.contrast(WHITE, WHITE), 1.0)
        # #767676 is the lightest grey that passes AA on white, at 4.54:1:
        # https://www.clairecodes.com/blog/2022-10-03-accessible-grey-colour-combinations/
        self.assertAlmostEqual(
            theme.contrast(theme.hex_colour("#767676"), WHITE), 4.54, places=2
        )

    def test_every_foreground_is_paired_with_its_base_and_hover(self) -> None:
        table = {
            "primary": "#000",
            "primary-foreground": "#fff",
            "primary-hover": "#111",
        }
        found = set(theme.pairs(table))
        self.assertIn(("primary-foreground", "primary", theme.TEXT), found)
        self.assertIn(("primary-foreground", "primary-hover", theme.TEXT), found)

    def test_text_meets_every_surface_and_status_meets_its_tint(self) -> None:
        found = set(theme.pairs({}))
        for surface in theme.SURFACES:
            self.assertIn(("muted-foreground", surface, theme.TEXT), found)
            self.assertIn(("error", surface, theme.TEXT), found)
            self.assertIn(("ring", surface, theme.UI), found)
        self.assertIn(("warning", "warning-tint", theme.TEXT), found)
        self.assertIn(("foreground", "warning-tint", theme.TEXT), found)

    def test_a_failing_pair_names_both_tokens_the_theme_and_the_ratio(self) -> None:
        table = {name: "#777777" for name in self.every_paired_token()}
        table.update(
            {"foreground": "light-dark(#000000, #808080)", "background": "#ffffff"}
        )
        problems = theme.check_contrast(table)
        self.assertIn(
            "theme: dark   --foreground on --background: 3.95:1, needs 4.5:1  FAILS",
            problems,
        )
        self.assertFalse(
            any("light  --foreground on --background" in p for p in problems)
        )

    @staticmethod
    def every_paired_token() -> set[str]:
        return {name for pair in theme.pairs({}) for name in pair[:2]}


class LiteralTests(unittest.TestCase):
    def kinds(self, text: str) -> list[str]:
        return [kind for _line, kind, _match in theme.literals_in(text)]

    def test_every_kind_is_caught(self) -> None:
        cases = {
            "color: #cf0722;": "hex colour",
            "box-shadow: 0 0 rgb(0 0 0);": "colour function",
            "border-color: oklch(0.7 0.1 200);": "colour function",
            "className='hover:bg-red-500/50'": "palette class",
            "className='text-white'": "palette class",
            "className='dark:bg-card'": "dark: variant",
            "font-family: Inter;": "font family",
            "style={{ fontFamily: 'Inter' }}": "font family",
            "className='font-[Inter]'": "font family",
        }
        for line, kind in cases.items():
            with self.subTest(line=line):
                self.assertEqual(self.kinds(line), [kind])

    def test_false_positives_stay_quiet(self) -> None:
        for line in (
            "document.getElementById('#root')",
            "const theme = { dark: ThemePreference.DARK };",
            "className='bg-primary text-primary-foreground border-border'",
            "href='https://example.org/page#section'",
        ):
            with self.subTest(line=line):
                self.assertEqual(self.kinds(line), [])

    def test_allow_marker_skips_only_its_own_line(self) -> None:
        text = "color: #ffffff; /* theme-check: allow brand sample */\ncolor: #000000;"
        self.assertEqual([line for line, _kind, _m in theme.literals_in(text)], [2])

    def test_skips_theme_generated_test_and_declaration_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skipped = (
                "packages/ui-kit/src/theme/defaults.css",
                "packages/ui-kit/src/gen/colours.ts",
                "apps/web/src/node_modules/lib/index.ts",
                "apps/web/src/App.test.tsx",
                "apps/web/src/env.d.ts",
            )
            for name in (*skipped, "apps/web/src/App.tsx"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("const red = '#ff0000';\n", encoding="utf-8")
            self.assertEqual(
                theme.check_literals(root),
                [
                    "apps/web/src/App.tsx:1: hex colour '#ff0000'; use a theme token instead"
                ],
            )


class CommandLineTests(unittest.TestCase):
    def test_the_real_theme_passes_wcag_aa(self) -> None:
        self.assertEqual(theme.check_contrast(theme.theme_tokens()), [])

    def test_exit_codes(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with (
            mock.patch.object(theme, "check_contrast", return_value=[]),
            mock.patch.object(theme, "check_literals", return_value=[]),
            redirect_stdout(out),
        ):
            self.assertEqual(theme.main([]), 0)
        self.assertIn("meets WCAG standards", out.getvalue())

        problem = (
            "apps/web/src/App.tsx:1: hex colour '#ff0000'; use a theme token instead"
        )
        with (
            mock.patch.object(theme, "check_contrast", return_value=[]),
            mock.patch.object(theme, "check_literals", return_value=[problem]),
            redirect_stderr(err),
        ):
            self.assertEqual(theme.main([]), 1)
        self.assertIn(problem, err.getvalue())
        self.assertIn("packages/ui-kit/AGENTS.md", err.getvalue())


if __name__ == "__main__":
    unittest.main()
