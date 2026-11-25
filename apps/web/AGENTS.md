# Agent Instructions: `apps/web/`

The root `AGENTS.md` applies in full. These rules add web-specific interaction conventions.

**Browser (Playwright) tests are in `e2e/*.e2e.ts`**, run with `pnpm --dir apps/web test:browser`,
signed out so no server is needed. They use the shared checks in `@armada/ui-tests`: read
`packages/ui-tests/AGENTS.md` before adding one. Vitest tests stay beside the code in `src/`.

## Interactive controls

- Make controls recognizable before interaction, including on touch devices. Do not rely on
  hover, a cursor, or color alone to communicate an action or state.
- Use native buttons for actions, links for navigation, and appropriate form controls. Give
  controls accessible names and preserve their expected keyboard behavior.
- Give enabled actions and links a pointer cursor and visible hover feedback. Use a cursor
  appropriate to the operation for other controls, such as a text cursor for text entry. Keep
  hover feedback consistent with the control's purpose and use semantic theme tokens.
- Match feedback to the actual interactive area. Do not give noninteractive content an action
  cursor or hover treatment. Associated form labels normally activate their control; preserve
  that native behavior unless the interaction explicitly requires otherwise.
- Keep keyboard focus visibly distinct, including when hover is unavailable. Do not remove the
  browser's focus indicator without providing an accessible replacement.
- Distinguish disabled controls from enabled controls, and do not show enabled hover or pointer
  feedback on disabled controls. Explain how to proceed when the reason is not apparent.
- Ensure visual cues needed to identify controls and their states meet WCAG AA contrast against
  adjacent colors. Give pointer targets sufficient size or spacing under WCAG AA.

References: [WCAG focus visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html),
[non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html),
[use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html),
[target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html),
[MDN cursors](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/cursor),
and [form labels](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/label).
