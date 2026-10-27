// dev_run.py sets this for every run from source, matching the backend's Environment.is_dev.
// The packaged build never sets it, so development-only UI stays out of the exe.
export function devToolsEnabled(): boolean {
  return import.meta.env.VITE_ARMADA_DEV_TOOLS === '1';
}
