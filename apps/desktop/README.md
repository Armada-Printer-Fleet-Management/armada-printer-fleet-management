# `apps/desktop/` — the desktop application

A pywebview shell hosting a React frontend. It runs on machines that communicate with the local server controlling the printers and the remote server controlling student prints. This is a application for the administrators and operators of the printers, not the students who submit print jobs. Students use the web application instead.

| Directory   | What it is                        |
| ----------- | --------------------------------- |
| `shell/`    | The Python pywebview host process |
| `frontend/` | The React UI it displays          |

Separate from `apps/web/`, and never imported by it.
