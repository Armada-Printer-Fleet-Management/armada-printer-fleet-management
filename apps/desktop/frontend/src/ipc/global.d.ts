export {};
declare global {
  interface Window {
    // "api" is pywebview's own fixed property name, injected by the runtime.
    // PywebviewIpc is our name for its shape.
    pywebview?: { api: PywebviewIpc };
  }

  // Empty here on purpose: each ipc/*.ts module augments this with its own
  // namespace via declaration merging, so this file never has to list every
  // module's methods by hand.
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type -- extended via declaration merging in ipc/*.ts modules
  interface PywebviewIpc {}
}