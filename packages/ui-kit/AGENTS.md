# Agent Instructions: `packages/ui-kit/`

The root `AGENTS.md` applies in full. This file holds the theme every frontend draws with, and the
accessibility rules checked on every push. **Read it before writing UI** in `apps/web/`,
`apps/desktop/frontend/` or here. `README.md` beside it covers building a component.

## Theme

- `src/theme/` holds the layers, imported in order by `src/styles.css`:
  - `fonts.css`: Figtree and JetBrains Mono, fixed by Armada in every theme and brand. Their
    licences are `THIRD_PARTY_LICENSE` legal documents in `organization.json`.
  - `defaults.css`: the tokens a brand may set. Each reads `--brand-<name>` first.
  - `fixed.css`: status, viewport and line-type colours. Never reads a `--brand-*` variable.
  - `tailwind.css`: the utility for each token (`bg-card`, `text-error`, `font-mono`).
- **Colours only from tokens.** No hex, `rgb()`/`hsl()`/`oklch()`, palette classes such as
  `text-slate-600`, `dark:` variants or `font-family` outside `src/theme/`. A new role is a new
  token in `defaults.css` or `fixed.css`, plus its utility in `tailwind.css`.
- Every colour is `light-dark(<Frost>, <Graphite>)`. `ThemeProvider` switches themes by setting
  `data-theme` on `<html>`; never pick a colour in code by checking the theme.
- **Names carry the pairing:** text on a fill `x` is `x-foreground`, and its hover is `x-hover`.

## Accessibility: WCAG AA

`python scripts/check_ui_theme.py` runs in the pre-push hook and CI. It fails on literal colours
and fonts, and on token contrast below 4.5:1 for text or 3:1 for the focus ring. `--verbose`
lists every pair.

- **Pairs follow the names:** `x-foreground` on `x` and `x-hover`; `foreground`,
  `muted-foreground`, `primary` and each status on every surface (`background`, `card`,
  `secondary`, `sidebar`); each status on its `-tint`; `ring` on every surface.
- A pair the names miss goes in `EXTRA_PAIRS` with its reason; one never drawn goes in
  `SKIPPED_PAIRS` with its reason.
- Fix a failing pair by changing the token's value. Mockup colours are a guide, not a rule.
- A literal that must stay carries `theme-check: allow <reason>` on its line.
- Controls are keyboard reachable with a visible focus ring. `apps/web/AGENTS.md` has the
  interactive-control rules.
