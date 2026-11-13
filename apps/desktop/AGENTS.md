# Agent Instructions: `apps/desktop/`

Path-scoped instructions for the desktop application. The root `AGENTS.md` still applies in full;
this file adds only what is specific to this app. It holds the rules; `docs/desktop.html` holds
the pictures and the reasons, and never repeats what is here.

## What this app is

A Python process (`backend/`) opens a native window with pywebview and renders a React app
(`frontend/`) inside it. The frontend runs in its own WebView2 renderer process, so every call
between the two is real IPC through `window.pywebview.api`. There is no HTTP and no ConnectRPC
between them. The app is for printer administrators and operators; students use `apps/web/`.

**The frontend is a thin view; the Python backend holds the logic.** React never calls the
application server, the printer server or any other service directly: every call goes over IPC
to the backend, whose domain services and infrastructure do the work. The backend's domains
follow the root `AGENTS.md` DDD section.

**The currently on exception is the slicer engine**, which runs in the renderer: its toolpaths are drawn there and are
too large for IPC. Rules about a slice still live in the backend. See `packages/slicer-engine/AGENTS.md`.

Never import from `apps/web/`. Share UI through `packages/ui-kit/`.

## Tech stack

Versions are in the manifests, `backend/pyproject.toml` and `frontend/package.json`, and NSIS's in
`scripts/install_nsis.py`. Never restate them here.

| Layer     | Stack                                                                                 |
| --------- | ------------------------------------------------------------------------------------- |
| Backend   | Python, pywebview, protobuf (runtime for the generated classes), connectrpc (pinned in the root rules), packaging (parses the backend's own PEP 440 version), PyYAML (reads the settings file); uv + hatchling (wheel build of the `armada_*` packages) |
| Frontend  | React, TypeScript (strict, `noUncheckedIndexedAccess`), Vite (dev server on `:5173`), @bufbuild/protobuf (`fromJson` decodes bridge replies); pnpm, pinned in `packageManager` |
| Contract  | `packages/proto/` via buf. Python uses `protoc_builtin`, the locally installed `protoc` (an onboarding prerequisite, on protobuf's release line); TypeScript uses `local: protoc-gen-es` from `node_modules/.bin`. Both templates run fully offline |
| Shared    | `proto_utils` supplies `message_to_dict`; `@armada/ui-kit` supplies `AboutBox` and the other shared components |
| Quality   | ruff, pyright strict; ESLint + typescript-eslint                                      |
| Packaging | PyInstaller (onedir, Windows only); NSIS; WebView2 Runtime on the target, never bundled |

## Dependency isolation

Backend and frontend share no dependency graph, and neither imports the other's code:

- **Backend:** its own uv project with its own `backend/uv.lock`. It takes `packages/proto/utils`
  (the generated Python and the mappers, shared by every Python app) and
  `packages/organization-info/` as uv path dependencies.
- **Frontend:** a member of the root pnpm workspace (`pnpm-workspace.yaml`, locked by the root
  `pnpm-lock.yaml`), installed with `pnpm install` from the repo root. It imports
  `packages/organization-info/` and `packages/ui-kit/` as TypeScript source.
- **The contract ties them together.** Message shapes live once in `packages/proto/`; codegen
  writes the Python into the shared `proto_utils/gen/` and the TypeScript straight into
  `frontend/src/gen/`, so the two sides of the bridge cannot drift apart even though no RPC
  framework sits between them.

Picture: `docs/desktop.html#overview` and `docs/desktop.html#codegen`.

## Layout

| Path                              | Owns                                                                 |
| --------------------------------- | -------------------------------------------------------------------- |
| `backend/src/armada_app/`         | Entry point `desktop-backend` (`--target`), window lifecycle         |
| `backend/src/armada_app/composition.py` | Composition root: builds infrastructure and hands it to domain services |
| `backend/src/armada_ipc/`         | `Ipc` root object, `IpcModule` base, one module per capability       |
| `backend/src/armada_domains/`     | Domains: a repository port (reads, requests changes; never saves shared entities. Can save desktop specific entities) and a service per domain. Ports extend a `core_domain.ddd` `Abstract*Repository` base, and infrastructure inherits the port |
| `backend/src/armada_infrastructure/` | The backend's own I/O clients implementing those ports, e.g. `application_server/` over Connect |
| `backend/src/armada_runtime/`     | `Environment` (dev vs packaged paths), packaging names, the settings file loader |
| `packages/proto/utils/` (shared)  | Generated Python protobuf (`proto_utils.gen`) and entity mappers     |
| `frontend/src/ipc/`               | One TS module per backend capability, plus `pywebview.ts` and `global.d.ts` |
| `frontend/src/gen/`               | Generated protobuf. Gitignored, never edited                         |
| `backend/desktop_backend.spec`    | PyInstaller spec                                                     |
| `installer/installer.nsi`         | NSIS script. Holds no names; all arrive as `/D` defines              |
| `dev_run.py`, `build_run.py`, `installer_run.py` | Run, package, and build the installer             |

## The `ipc/` pattern

`armada_app/window.py` opens the native window and hands pywebview a single `Ipc` object, built by
`build_ipc()` in `armada_app/composition.py`, as its `js_api`. The frontend reaches it through `window.pywebview.api`, but only after pywebview's
`pywebviewready` event; `waitForPywebviewIpc()` in `frontend/src/ipc/pywebview.ts` waits for it.

Each capability is one file on each side, named after it and mirrored, such as
`backend/src/armada_ipc/application_info.py` and `frontend/src/ipc/application-info.ts`. Every
backend module extends `IpcModule` and is one attribute of `Ipc`. pywebview walks nested class
instances on the `js_api` object, so each module becomes its own JS namespace
(`window.pywebview.api.application_info.version()`) instead of a flat bag of methods on the root.
A new capability is therefore a new pair of files, never an edit to an existing module.

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

Picture: `docs/desktop.html#ipc`.

## Rules that are easy to break

- **Paths at runtime go through `armada_runtime.environment.Environment`.** Never check
  `sys.frozen` or build paths from `__file__` elsewhere. `Environment.is_dev` tells source from
  packaged; `resource_root()` is `apps/desktop/` from source and the bundle's `_internal/` when
  packaged, and `resource_path(...)` and `default_frontend_target()` build on it.
- **A new runtime-read file, dynamic import, or package that reads its own metadata needs an entry
  in `desktop_backend.spec`** (`datas`, `hiddenimports`, `copy_metadata`, `collect_data_files`).
  Tests and type checks do not catch a missing one. Run `python apps/desktop/build_run.py` and
  launch the exe after changing backend dependencies or runtime-read files. PyInstaller lists what
  it could not resolve in `backend/build/desktop_backend/warn-desktop_backend.txt` (most entries
  are harmless conditional imports); set `console=True` in the spec to see start-up errors.
- **The server address comes from the per-user settings file**, `Environment.settings_path()`:
  `%APPDATA%/<exe name>/settings.yaml`, or `settings.dev.yaml` from source. It is generated from
  `settings_template()` in `armada_runtime/settings.py` only when missing and never overwritten,
  so no template is bundled. Packaged, it starts empty, and calls raise `ServerNotConfigured`
  rather than failing at startup: each `application_server/` adapter builds its Connect client on
  first use. `DEV_SERVER_URL` must match `infra/dev/compose.yaml`; `tests/test_settings.py` checks
  it.
- **Names come from `packages/organization-info/organization.json`.** Window title, page
  `<title>`, exe name, and installer names all read it. Never hardcode them.
- **The uninstaller deletes only the exe, `_internal/` and itself.** If the bundle gains another
  top-level entry, add it to the `Uninstall` section of `installer.nsi`.
- **NSIS is pinned by version and SHA-256** in `scripts/install_nsis.py`. Change both together,
  with the hash from a source independent of your own download: SourceForge publishes no
  checksums and the setup program is unsigned, so the current hash was checked against winget's
  reviewed `NSIS.NSIS` manifest.
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
| Run (built frontend)         | `python apps/desktop/dev_run.py`: runs `pnpm build` and loads `dist/index.html` over `file://`, with no dev server, as the packaged app does |
| Run (hot reload, `:5173`)    | `python apps/desktop/dev_run.py --dev`: the window points at a Vite dev server; frontend edits reload without restarting Python |
| Package exe                  | `python apps/desktop/build_run.py`                                            |
| Build installer              | `python apps/desktop/installer_run.py [--skip-build] [--smoke-test] [--dev-tools]` |

CI is `.github/workflows/desktop.ci.yml`; the pre-push check is
`.githooks/pre-push.d/desktop/check.sh`. Both run the checks above; codegen runs first, once, for
every Python project.

Outputs: `build_run.py` runs `pnpm build` for the frontend, then PyInstaller bundles the backend
with that build into `backend/dist/<title>/` (`<title>.exe` beside `_internal/`); it prints
collapsible groups under GitHub Actions and step banners in a terminal. `installer_run.py` writes
`installer/dist/<title>-Setup-<version>.exe`, passing names and paths to `makensis` as `/D`
defines read from `armada_runtime.packaging.installer_info()`. `install_nsis.py` downloads the
official NSIS setup from SourceForge and installs it silently, with one administrator prompt on a
developer's machine; CI uses it too. `--skip-build` reuses a
bundle; `--smoke-test` installs silently for the current user, checks the app landed, and
uninstalls. `--dev-tools` (local testing only, never CI or a release) builds the frontend with
`VITE_ARMADA_DEV_TOOLS=1`, so the installed app shows the development-only UI, and names the setup
`<title>-Setup-<version>-dev.exe`; it cannot be combined with `--skip-build`.

Getting a build without your own machine's setup:

- **As CI runs it, locally:** on Windows,
  `act workflow_dispatch -W .github/workflows/desktop.ci.yml -j package -P windows-latest=-self-hosted`.
  It also runs the job's `needs` (`backend`, `frontend`), and its final artifact upload fails
  because `act` has no artifact service; the exe is under `~/.cache/act/`.
- **For a pull request:** `package` never runs on pull requests. Start **CI (desktop)** by hand
  from the Actions tab on the PR's branch; the build is the `desktop-windows` artifact.
- **Automatically:** every push to `main` or `release/**` uploads `desktop-windows` and, built
  with `--smoke-test`, `desktop-windows-installer`.

Picture: `docs/desktop.html#packaging` and `docs/desktop.html#installer`.
