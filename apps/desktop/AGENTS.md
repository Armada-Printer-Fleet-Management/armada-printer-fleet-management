# Agent Instructions: `apps/desktop/`

Path-scoped instructions for the desktop application. The root `AGENTS.md` still applies in full;
this file adds only what is specific to this app. The human-facing version, with diagrams, is
`docs/desktop.html`. Keep the two in step when either changes.

## What this app is

A Python process (`backend/`) opens a native window with pywebview and renders a React app
(`frontend/`) inside it. The frontend runs in its own WebView2 renderer process, so every call
between the two is real IPC through `window.pywebview.api`. There is no HTTP and no ConnectRPC
between them. The app is for printer administrators and operators; students use `apps/web/`.

Never import from `apps/web/`. Share UI through `packages/ui-kit/`.

## Tech stack

| Layer     | Stack                                                                                 |
| --------- | ------------------------------------------------------------------------------------- |
| Backend   | Python >=3.13, pywebview >=6.2,<7, protobuf >=7,<8, packaging; uv + hatchling         |
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
| `backend/src/armada_ipc/`         | `Ipc` root object, `IpcModule` base, one module per capability       |
| `backend/src/armada_runtime/`     | `Environment` (dev vs packaged paths), packaging names               |
| `backend/src/armada_gen/`         | Generated protobuf. Gitignored, never edited                         |
| `frontend/src/ipc/`               | One TS module per backend capability, plus `pywebview.ts` and `global.d.ts` |
| `frontend/src/gen/`               | Generated protobuf. Gitignored, never edited                         |
| `backend/desktop_backend.spec`    | PyInstaller spec                                                     |
| `installer/installer.nsi`         | NSIS script. Holds no names; all arrive as `/D` defines              |
| `dev_run.py`, `build_run.py`, `installer_run.py` | Run, package, and build the installer             |

## Adding an IPC capability

Mirror one file on each side, named after the capability:

1. If it carries data, define the message in `packages/proto/common/v1/` and regenerate both sides.
2. `backend/src/armada_ipc/<name>.py`: a class extending `IpcModule`. Methods return
   `message_to_dict(msg)` (from `proto_utils`), not the message itself.
3. Add one attribute to `Ipc.__init__` in `armada_ipc/__init__.py`. That attribute name is the JS
   namespace: `window.pywebview.api.<attr>.<method>()`. Do not restructure `Ipc`.
4. `frontend/src/ipc/<name>.ts`: augment the global `PywebviewIpc` interface with the namespace
   (declaration merging, never edit `global.d.ts`), await `waitForPywebviewIpc()`, and decode
   the reply with `fromJson(<Schema>, raw)`.

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
| Generate Python proto        | `python scripts/generate_proto.py buf.gen.desktop_python.yaml`                |
| Generate TS proto            | `python scripts/generate_proto.py buf.gen.desktop_ts.yaml --node-modules apps/desktop/frontend/node_modules` |
| Backend checks               | `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` (in `backend/`) |
| Frontend checks              | `pnpm exec tsc --noEmit`, `pnpm exec eslint .` (in `frontend/`)               |
| Run (built frontend)         | `python apps/desktop/dev_run.py`                                              |
| Run (hot reload, `:5173`)    | `python apps/desktop/dev_run.py --dev`                                        |
| Package exe                  | `python apps/desktop/build_run.py`                                            |
| Build installer              | `python apps/desktop/installer_run.py [--skip-build] [--smoke-test]`           |

CI is `.github/workflows/desktop.ci.yml`; the pre-push check is
`.githooks/pre-push.d/desktop/check.sh`. Both run the codegen and checks above.
