# `apps/desktop/` — the desktop application

A Python backend (using pywebview) hosting a React frontend. It runs on machines that communicate
with the local server controlling the printers and the remote server controlling student prints.
This is an application for the administrators and operators of the printers, not the students who
submit print jobs. Students use the web application instead.

| Directory   | What it is                |
| ----------- | -------------------------- |
| `backend/`  | The Python pywebview host  |
| `frontend/` | The React UI it displays   |

Separate from `apps/web/`, and never imported by it.

## How the two halves talk

`backend` opens the native window and hands pywebview a single `Ipc` object; `frontend` calls it
through `window.pywebview.api`, waiting for pywebview's `pywebviewready` event first. This is a
real inter-process bridge, not an in-process function call — the rendered frontend runs inside its
own WebView2 (or platform-equivalent) renderer process, separate from the Python host process. No
HTTP, no ConnectRPC. Simple and Efficient.

## Why protobuf, given IPC and not API

Message shapes live once in `packages/proto/common/v1/`. `buf generate` produces a matching
Python class and TypeScript class from that same source, so the two sides of the bridge can't
quietly drift apart even without an RPC framework sitting between them.

## The `ipc/` pattern

One file per capability, named after it, mirrored between `backend/src/backend/ipc/application_info.py` and
`frontend/src/ipc/application-info.ts`. Every concrete backend module extends the shared
`IpcModule` base; pywebview walks nested class instances automatically, so each module becomes its
own namespace in JS (`window.pywebview.api.application_info.version()`) rather than one
flat bag of methods. Adding a new domain means adding a new file, not changing an existing one. This improves maintainability and discoverability.

## Running it

- `python apps/desktop/dev_run.py` — builds the frontend and loads it via `file://`, the closest
  thing to the installed app.
- `python apps/desktop/dev_run.py --dev` — hot-reloading Vite dev server instead.
- `python apps/desktop/build_run.py` — packages the Windows executable, named after the
  organization title (`backend/dist/<Title-Case-Name>/`).

See `docs/desktop.html` for the full picture with diagrams.

## Dependency isolation

`backend` and `frontend` each have their own manifest and lock — no shared root workspace. Proto
codegen (`scripts/generate_proto.py`) writes straight into each app's own tree, not through a
shared installed package.