# `apps/desktop/` — the desktop application

The app printer administrators and operators use to run the fleet. A Python backend (pywebview)
hosts a React frontend in a native window; students use `apps/web/` instead.

| Directory    | What it is                     |
| ------------ | ------------------------------ |
| `backend/`   | The Python pywebview host      |
| `frontend/`  | The React UI it displays       |
| `installer/` | The Windows setup wizard script |

- How the two halves talk, and how it is packaged: [`docs/desktop.html`](../../docs/desktop.html)
- The rules for working in it: [`AGENTS.md`](AGENTS.md)
- Logging, and where to find the log files: [`docs/desktop-logging.html`](../../docs/desktop-logging.html)

## Running it

- `python apps/desktop/dev_run.py` — builds the frontend and loads it via `file://`, the closest
  thing to the installed app.
- `python apps/desktop/dev_run.py --dev` — hot-reloading Vite dev server instead.
- `python apps/desktop/build_run.py` — packages the Windows executable.
- `python apps/desktop/installer_run.py` — builds that, then wraps it in a Windows setup wizard.
  Needs NSIS: `python scripts/install_nsis.py`.
