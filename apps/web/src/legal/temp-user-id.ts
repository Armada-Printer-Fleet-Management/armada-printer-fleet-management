// TEMP stub: the web app has no sign-in yet, so each browser invents one random user ID and keeps
// it in localStorage, so legal agreements can be recorded on the server against it.
// Filling it in: once sign-in exists, the signed-in user's ID replaces tempUserId() in
// AgreementGate.tsx, this file is deleted, and the server makes AgreementService authenticated,
// taking the user from the caller instead of the request.
const KEY = 'armada.temp-user-id';

export function tempUserId(): string {
  try {
    const stored = localStorage.getItem(KEY);
    if (stored) return stored;
    const created = crypto.randomUUID();
    localStorage.setItem(KEY, created);
    return created;
  } catch {
    // Storage blocked, as in some private windows: asked again on every visit.
    return crypto.randomUUID();
  }
}
