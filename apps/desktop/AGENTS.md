# Agent Instructions: `apps/desktop/`

Path-scoped instructions for the desktop application. The root `AGENTS.md` still applies in full;
this file adds only what is specific to this app. The human-facing version, with diagrams, is
`docs/desktop.html`. Keep the two in step when either changes.

## What this app is

A Python process (`backend/`) opens a native window with pywebview and renders a React app
(`frontend/`) inside it. The frontend runs in its own WebView2 renderer process, so every call
between the two is real IPC through `window.pywebview.api`. There is no HTTP and no ConnectRPC
between them. The app is for printer administrators and operators; students use `apps/web/`.

**The frontend is a thin view; the Python backend holds the logic.** React never calls the
application server, the printer server or any other service directly: every call goes over IPC
to the backend, whose domain services and infrastructure do the work. The backend's domains
follow the root `AGENTS.md` DDD section.

Never import from `apps/web/`. Share UI through `packages/ui-kit/`.

## Tech stack

| Layer     | Stack                                                                                 |
| --------- | ------------------------------------------------------------------------------------- |
| Backend   | Python >=3.13, pywebview >=6.2,<7, protobuf >=7,<8, connectrpc >=0.12.1,<0.13, packaging; uv + hatchling |
| Frontend  | React 19, TypeScript 5 (strict, `noUncheckedIndexedAccess`), Vite 6, @bufbuild/protobuf 2; pnpm 12.3.4 |
| Contract  | `packages/proto/` via buf; `protoc` for Python, `protoc-gen-es` for TypeScript       |
| Quality   | ruff, pyright strict; ESLint 9 + typescript-eslint 8                                  |
| Packaging | PyInstaller >=6,<7 (onedir, Windows only); NSIS 3.12; WebView2 Runtime on the target |

Backend and frontend share no dependency graph: the backend is a uv project, the frontend a pnpm
project, each with its own manifest. Generated proto code is the only thing tying them together.

## Layout

| Path                              | Owns                                                                 |
| --------------------------------- | -------------------------------------------------------------------- |
| `backend/src/armada_app/`         | Entry point `desktop-backend` (`--target`), window lifecycle         |
| `backend/src/armada_app/composition.py` | Composition root: builds infrastructure and hands it to domain services |
| `backend/src/armada_ipc/`         | `Ipc` root object, `IpcModule` base, one module per capability       |
| `backend/src/armada_domains/`     | Domains: a repository port (reads, requests changes; never saves shared entities. Can save desktop specific entities) and a service per domain |
| `backend/src/armada_infrastructure/` | The backend's own I/O clients implementing those ports, e.g. `application_server/` over Connect |
| `backend/src/armada_runtime/`     | `Environment` (dev vs packaged paths), packaging names               |
| `packages/proto/utils/` (shared)  | Generated Python protobuf (`proto_utils.gen`) and entity mappers     |
| `frontend/src/ipc/`               | One TS module per backend capability, plus `pywebview.ts` and `global.d.ts` |
| `frontend/src/gen/`               | Generated protobuf. Gitignored, never edited                         |
| `backend/desktop_backend.spec`    | PyInstaller spec                                                     |
| `installer/installer.nsi`         | NSIS script. Holds no names; all arrive as `/D` defines              |
| `dev_run.py`, `build_run.py`, `installer_run.py` | Run, package, and build the installer             |

## Adding an IPC capability

Mirror one file on each side, named after the capability:

1. Shape every call like an RPC: **one request message in, one response message out.** Reuse a
   service's messages for a pass-through (`print_job` reuses `server.v1.GetPrintJobRequest`);
   define a message in `packages/proto/` only when the call diverges. Regenerate both sides.
2. `backend/src/armada_ipc/<name>.py`: a class extending `IpcModule`, taking its domain service in
   its constructor. Decorate a call that takes input with `@proto_call(RequestType)` and one that
   takes none with `@proto_response`; both return the message, which they encode.
3. Add one attribute to `Ipc.__init__` in `armada_ipc/__init__.py` and pass its service in from
   `armada_app/composition.py`. The attribute name is the JS namespace:
   `window.pywebview.api.<attr>.<method>()`. Do not restructure `Ipc`.
4. `frontend/src/ipc/<name>.ts`: augment the global `PywebviewIpc` interface with the namespace
   (declaration merging, never edit `global.d.ts`), await `waitForPywebviewIpc()`, send the
   request with `toJson`, and decode the reply with `fromJson(<Schema>, raw)`.

Getters are `x()` / `set_x()` on the Python side, because the bridged name is what callers see.

## Rules that are easy to break

- **Paths at runtime go through `armada_runtime.environment.Environment`.** Never check
  `sys.frozen` or build paths from `__file__` elsewhere.
- **A new runtime-read file, dynamic import, or package that reads its own metadata needs an entry
  in `desktop_backend.spec`** (`datas`, `hiddenimports`, `copy_metadata`, `collect_data_files`).
  Tests and type checks do not catch a missing one. Run `python apps/desktop/build_run.py` and
  launch the exe after changing backend dependencies or runtime-read files.
- **Names come from `packages/organization-info/organization.json`.** Window title, page
  `<title>`, exe name, and installer names all read it. Never hardcode them.
- **The uninstaller deletes only the exe, `_internal/` and itself.** If the bundle gains another
  top-level entry, add it to the `Uninstall` section of `installer.nsi`.
- **NSIS is pinned by version and SHA-256** in `scripts/install_nsis.py`. Change both together,
  with the hash from a source independent of your own download.
- **Vite `base` is `"./"`** because the default run mode loads `index.html` over `file://`.
- **Keep the `dedupe` in `vite.config.ts`.** Shared packages sit outside the frontend project,
  and without it they can load a second copy of React or protobuf.

## Commands

| Task                         | Command                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------- |
| Backend deps                 | `uv sync --project apps/desktop/backend`                                      |
| Frontend deps                | `pnpm install`; `/onboarding` says where to run it                            |
| Generate Python proto        | `uv run --project packages/proto/utils python scripts/generate_proto.py buf.gen.python.yaml` (shared) |
| Generate TS proto            | `python scripts/generate_proto.py buf.gen.desktop_ts.yaml --node-modules apps/desktop/frontend/node_modules` |
| Backend checks               | `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, `uv run lint-imports` (in `backend/`) |
| Frontend checks              | `pnpm exec tsc --noEmit`, `pnpm exec eslint .` (in `frontend/`)               |
| Run (built frontend)         | `python apps/desktop/dev_run.py`                                              |
| Run (hot reload, `:5173`)    | `python apps/desktop/dev_run.py --dev`                                        |
| Package exe                  | `python apps/desktop/build_run.py`                                            |
| Build installer              | `python apps/desktop/installer_run.py [--skip-build] [--smoke-test]`           |

CI is `.github/workflows/desktop.ci.yml`; the pre-push check is
`.githooks/pre-push.d/desktop/check.sh`. Both run the checks above; codegen runs first, once, for
every Python project.
