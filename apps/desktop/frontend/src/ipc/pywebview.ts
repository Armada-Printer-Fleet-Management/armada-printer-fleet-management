// The backend raises this, by class name, when a call needs the operator to sign in again.
const SIGN_IN_REQUIRED = 'SignInRequired';
export const SIGN_IN_REQUIRED_EVENT = 'armada:sign-in-required';

// Waits for pywebview's `pywebviewready` event (fired once window.pywebview.api
// is injected) and returns the IPC root. Each ipc/*.ts module reaches into
// its own namespace off of this -- e.g. ipc.application_info.version().
// Every call through it announces SignInRequired, so no module can forget to.
export async function waitForPywebviewIpc(): Promise<PywebviewIpc> {
  const existing = window.pywebview;
  if (existing) return announceSignInRequired(existing.api);

  await new Promise<void>((resolve) => {
    window.addEventListener('pywebviewready', () => resolve(), { once: true });
  });

  const ready = window.pywebview;
  if (!ready)
    throw new Error('pywebviewready fired but window.pywebview is still unset');
  return announceSignInRequired(ready.api);
}

function announce(error: unknown): never {
  if (error instanceof Error && error.name === SIGN_IN_REQUIRED) {
    window.dispatchEvent(
      new CustomEvent(SIGN_IN_REQUIRED_EVENT, { detail: error.message }),
    );
  }
  // Rethrown, so the caller still shows its own error state.
  throw error;
}

// A proxy rather than a copy: pywebview fills in the API's namespaces itself, and only the calls
// made through it need wrapping.
function announceSignInRequired(api: PywebviewIpc): PywebviewIpc {
  return new Proxy(api, {
    get(target, name, receiver) {
      const namespace: unknown = Reflect.get(target, name, receiver);
      if (typeof namespace !== 'object' || namespace === null) return namespace;
      return new Proxy(namespace, {
        get(methods, method, methodsReceiver) {
          const call: unknown = Reflect.get(methods, method, methodsReceiver);
          if (typeof call !== 'function') return call;
          return (...args: unknown[]) =>
            (Reflect.apply(call, methods, args) as Promise<unknown>).catch(
              announce,
            );
        },
      });
    },
  });
}
