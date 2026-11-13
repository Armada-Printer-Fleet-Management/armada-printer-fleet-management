// dev_run.py sets this for every run from source, matching the backend's Environment.is_dev.
// A packaged build sets it only through installer_run.py --dev-tools, so development-only UI
// stays out of a release exe.
export function devToolsEnabled(): boolean {
  return import.meta.env.VITE_ARMADA_DEV_TOOLS === '1';
}
