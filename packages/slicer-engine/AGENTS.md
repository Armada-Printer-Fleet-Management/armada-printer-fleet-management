# Agent Instructions: `packages/slicer-engine/`

The slicer engine (CuraEngine compiled to WebAssembly) as both frontends consume it.

## Two repositories

- **The sister repository
  [`armada-slicer-engine`](https://github.com/Armada-Printer-Fleet-Management/armada-slicer-engine) builds the
  engine**: its C++/Emscripten/Conan toolchain, patches, embind bindings and the generated `.d.ts`. It holds no
  Armada logic.
- **This repository holds every line of Armada logic, UI and interfaces that use the engine.**
- **A change to the engine's build or JavaScript API is made there and released as a tag**; here it is a pin bump.
- **The engine enters only through `scripts/fetch_slicer_engine.py`**, checked against `engine.pin.json` and the
  release's build attestation. Never commit, copy or hand-edit it.

## What runs where

- **The engine runs in the client's browser** (the web app, or the desktop's renderer). That covers slicing, and
  the toolpaths the 3D view draws.
- **Rules, validation and analysis (AI included) are Python domain logic in `core-domain`, never TypeScript.**
  The browser sends a small vendor-neutral summary of a slice: over IPC to the desktop backend, or over
  ConnectRPC to the server. Violations come back the same way. Toolpaths never cross IPC or the network.
- **The server is authoritative** and re-checks anything submitted to it. A server-side engine is an adapter
  behind a `plugin-api` port, never an import of this package.

## What is here

| Path | Owns |
| --- | --- |
| `engine.pin.json` | The engine release (sister repository and tag) and the SHA-256 of every file in it |
| `gen/` | The fetched release. Gitignored; written only by `scripts/fetch_slicer_engine.py`, never edited |
| `src/index.ts` | `slicerEngineUrl()` and `loadSlicerEngine()`, the only way an app reaches the engine |
| `vite.ts` | The Vite plugin both apps use: serves `gen/` in development, copies it unhashed into a build |

## Rules

- **One engine instance per URL, reused.** `loadSlicerEngine()` caches it; never instantiate the module
  yourself.
- **Never bundle, inline or rename the engine.** Apps import `<base>/slicer-engine/CuraEngine.js` at run
  time, so a deployed build's engine can be replaced without rebuilding the app.
- **Its JavaScript API is the sister repository's bindings** (`gen/CuraEngine.d.ts`). A new engine
  capability is added there and released, never patched in here.
- **Memory is capped at 4 GB**, the WebAssembly maximum; a model needing more aborts the slice.
- **A CSP with `script-src` must allow `'wasm-unsafe-eval'` and `'unsafe-eval'`.** The engine's progress
  callbacks are run through `eval`.

## Moving to a new engine release

1. Set `tag` to the new release in `engine.pin.json`, and replace every asset hash with the release's
   `SHA256SUMS`.
2. Run `python scripts/fetch_slicer_engine.py`. It must verify each file's attestation.
3. Run `pnpm --dir packages/slicer-engine test`, then commit the pin.

## Commands

| Task | Command |
| --- | --- |
| Fetch the pinned engine | `python scripts/fetch_slicer_engine.py` |
| Check what is fetched, offline | `python scripts/fetch_slicer_engine.py --check` |
| Smoke test (Node) | `pnpm --dir packages/slicer-engine test` |

Picture: `docs/slicer-engine.html`.
