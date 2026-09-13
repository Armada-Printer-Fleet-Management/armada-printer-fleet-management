# `apps/desktop/shell/` — the pywebview host

The Python process that opens the native window, serves the built frontend into it, and exposes
what a browser cannot reach: the local filesystem, printer discovery on the local network, and
offline domain logic from `packages/core-domain/`.

**Belongs here:** window lifecycle, the Python-to-JavaScript bridge, and the adapter wiring for
the desktop build.
