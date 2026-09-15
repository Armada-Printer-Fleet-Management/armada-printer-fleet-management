# `apps/desktop/backend/` — the desktop backend

The Python process that opens the native window, serves the built frontend into it, and exposes
what a browser cannot reach: the local filesystem, OS specific domain logic, and any additional logic from `packages/core-domain/`.

**Belongs here:** window lifecycle, the Python-to-JavaScript IPC bridge (`ipc/`), and the adapter
wiring for the desktop build.