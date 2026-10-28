// Vite sets DEV for `vite` and `vite dev` and clears it for `vite build`, so development-only UI
// stays out of the shipped bundle.
export function devToolsEnabled(): boolean {
  return import.meta.env.DEV;
}
