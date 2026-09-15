// Waits for pywebview's `pywebviewready` event (fired once window.pywebview.api
// is injected) and returns the raw IPC root. Each ipc/*.ts module reaches into
// its own namespace off of this -- e.g. ipc.application_information.version().
export async function waitForPywebviewIpc(): Promise<NonNullable<Window["pywebview"]>["api"]> {
  const existing = window.pywebview;
  if (existing) return existing.api;

  await new Promise<void>((resolve) => {
    window.addEventListener("pywebviewready", () => resolve(), { once: true });
  });

  const ready = window.pywebview;
  if (!ready) throw new Error("pywebviewready fired but window.pywebview is still unset");
  return ready.api;
}