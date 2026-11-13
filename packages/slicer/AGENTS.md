# Agent Instructions: `packages/slicer/`

`@armada/slicer`: the one way either client turns a model, or G-code it already has, into a
`SliceResult` (G-code, toolpaths, a summary and violations). Headless; it holds no UI beyond the
feature gate. The root `AGENTS.md` and `packages/slicer-engine/AGENTS.md` still apply in full.

## Layout

| Path | Owns |
| --- | --- |
| `src/index.ts` | The public API. Import only from here, `./react` or (temporarily) `./temp` |
| `src/slicing/jobs.ts` | `sliceModel()` and `parseGcode()`, the two entry points |
| `src/slicing/run-in-worker.ts` | One fresh module worker per job, the memory budget, abort |
| `src/slicing/worker/` | `job-worker.ts` (the worker), `run-job.ts` (the job itself, runnable in Node), `protocol.ts`, `cura-cli.ts` |
| `src/slicing/gcode/` | The G-code parser, toolpath builder and per-slicer dialects |
| `src/slicing/mesh.ts`, `stl.ts` | A model's format (STL or OBJ, by content) and bounds, for placing it on the bed |
| `src/slicing/read-file.ts` | File reads that also work over `file://` |
| `src/validation/violations.ts` | `SlicerJobError` and the plain-language message for each `SlicerViolationCode` |
| `src/features/react.tsx` | `SlicerFeatureProvider`, `SlicerFeatureGate`, `useSlicerFeature` (`./react`) |
| `src/temp/` | TEMPORARY actions for both apps' dev page. Delete with `packages/ui-kit/src/temp/` |
| `src/gen/` | Generated from `buf.gen.slicer_ts.yaml`. Gitignored, never edited |
| `scripts/generate-test-gcode.*` | Writes the G-code test prints in `packages/sample-prints/test/` |

## Rules

- **Only `src/slicing/worker/cura-cli.ts` knows the engine's command line**: its arguments, callbacks
  and file system. Everything else talks in settings and bytes.
- **Every job runs in its own worker with its own engine**, terminated when the job settles. Never
  keep an engine between jobs or slice on the main thread.
- **`run-job.ts` touches no DOM and no worker API**, so tests run it directly in Node.
- **Settings come from the server** (`SlicerConfigurationService.GetSliceSettings`), never built in
  the client. The client passes them straight through as `SliceSettingsInput`.
- **The parser is the only source of `SliceSummary`**, for sliced and uploaded G-code alike. The
  engine's own report is kept as `engineReport` only. A browser summary is advisory: the server
  recomputes it.
- **Budgets stop a job before it hurts the browser.** The engine's memory budget is 3.5 GiB, lower
  where the browser reports the device's memory (half of it); over it, the worker is terminated
  and the job fails with `MODEL_TOO_LARGE`. The G-code budget is `DEFAULT_SEGMENT_BUDGET` moves;
  over it, `GCODE_TOO_LARGE`. Callers may lower either, never raise them past these.
- **Failures are `SlicerJobError`s carrying `SlicerViolation`s**, each wrapping `common.v1.Violation`
  with a plain-language message saying what to do. Add a case by appending a `SlicerViolationCode`
  and its message in `violations.ts`.
- **A new slicer's G-code is a new dialect** in `src/slicing/gcode/dialects/`, registered in its
  `index.ts`. G-code from an unknown slicer still parses, by geometry, as `EXTRUSION_UNKNOWN`.
- **Models are STL or OBJ, and the engine reads both itself.** Never convert between them here; a
  new format is supported only when the engine loads it, named by its extension in `cura-cli.ts`.
- **React stays in `./react`**, so the worker bundle never pulls React in.
- **Both apps need `worker: { format: 'es' }`** in `vite.config.ts`: the job worker is a module.

## Building on this

- **A 3D or layer view** reads `SliceResult.toolpaths`: typed arrays laid out as `types.ts` documents,
  with one `ToolpathFeature` per segment. Draw from them directly; never convert them to objects.
  Toolpaths never cross IPC or the network.
- **Progress** comes from `onProgress` (0 to 1, plus the engine's memory). Abort with `signal`.
- **Validation rules** are Python domain logic. They read the `SliceSummary`, never toolpaths, and
  return `print_preparation.validation.v1.PrintViolation`s. Never add a rule here.
- **A component that only some users may see** declares its `SlicerFeature` through
  `SlicerFeatureGate`; the app decides which features are on with `SlicerFeatureProvider`.

## The test prints

The prints `generate-test-gcode.ts` lists in `PRINTS` (`benchy-mk4s`, `voron-cube`, `extruder-idler`
in `packages/sample-prints/test/`) each hold a model, its G-code and `expected-summary.json`: what
the parser reads from that G-code. G-code never ships in an app; it is for tests only.

- **Regenerate them after changing the engine, the slice profile or the parser**, with the dev
  stack up: `pnpm --dir packages/slicer generate:test-gcode`. Review the summaries' diff before
  committing.
- **The engine is not byte-for-byte deterministic**: two runs differ in the last digit of some
  extrusion values. Compare a fresh slice within tolerances; compare the committed G-code's parse
  exactly.

## Commands

| Task | Command |
| --- | --- |
| Generate the code | `python scripts/generate_proto.py buf.gen.slicer_ts.yaml --node-modules packages/slicer/node_modules` |
| Tests | `pnpm --dir packages/slicer test` |
| Types, lint | `pnpm --dir packages/slicer typecheck`, `pnpm --dir packages/slicer lint` |
| Regenerate the test print | `pnpm --dir packages/slicer generate:test-gcode` (dev stack up) |

Picture: `docs/slicer-engine.html`.
