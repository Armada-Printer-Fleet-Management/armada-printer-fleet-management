# Agent Instructions: `packages/sample-prints/`

Real 3D print files, both models and their G-code, that the project uses for more than one job:

- prints that ship inside the apps (education, training and starter files);
- the files tests and manual regression run against;
- files ready for trying the upload API by hand.

The root `AGENTS.md` still applies in full.

## Layout and what each part is for

```
packages/sample-prints/
  bundled/<print id>/   ships inside the web and desktop apps
  test/<print id>/      development and CI only; NEVER distributed
  src/                  the typed manifest (index.ts), its validator (manifest.ts), disk helpers (files.ts)
  vite.ts               serves bundled/ in development and copies it into a build
```

- **Ship or not is decided by the directory, never by a flag.** The Docker `.dockerignore` files and
  the desktop's PyInstaller spec are path allow-lists, so a directory boundary is the only one they
  can enforce. Never let `test/` into an app build, an image or the installer.
- **`bundled/`** is for prints a user may see or start from: demos, training pieces and calibration
  models. Keep it small, because every app build carries it.
- **`test/`** is for what tests and developers need:
  - happy-path prints;
  - prints that must fail validation (overhangs, models too large for the bed, broken meshes);
  - prints that are large on purpose, to exercise memory limits and parsing budgets;
  - prints in other slicers' G-code dialects.

  Name each folder after what it exercises, such as `test/overhang-fails/` or `test/large-gcode/`.

## A print folder

Every print is one folder holding its files and a `print.json`:

| Field | Holds |
| --- | --- |
| `title`, `description` | What the print is and what it is for, in plain language |
| `license` | `spdx` identifier, `source` URL of the original, `attribution` |
| `files[]` | `name`, `kind` (`model` or `gcode`), `sizeBytes`, `sha256`; for G-code also `printer` and `generator` (the slicer, its version and settings, so the file can be regenerated) |
| `arrangement[]` | Optional. Copies of a model file on the bed, each as `file` plus `xMm` and `yMm`, its footprint centred that far from the bed centre |

The folder name is the print's `id`. `parsePrint()` in `src/manifest.ts` defines the shape; change it
there, not here.

- **A model and its G-code live side by side** in the same folder, as reviewers see them.
- **`sizeBytes` and `sha256` are the file's real values**, so a client can build an upload request
  from them without reading the file.
- **A bundled print is also listed in `BUNDLED` in `src/index.ts`**, which is what the apps import.
- **The tests guard the ship boundary**: everything the Vite plugin ships comes from `bundled/`,
  and every file a bundled `print.json` lists is shipped.

## Adding a print

1. Create the folder under `bundled/` or `test/`.
2. Add the files. `.stl`, `.3mf`, `.gcode` and `.bgcode` here are stored in Git LFS by
   `.gitattributes`; never commit them as ordinary blobs.
3. Write `print.json`. `python scripts/upload_metadata.py <file>` prints a file's size and SHA-256.
4. For a bundled print, add it to `BUNDLED` in `src/index.ts`.
5. Run `pnpm --dir packages/sample-prints test`, and confirm `print.json`'s sizes and hashes by
   re-running step 3.

## Licences

- **Only add a print whose licence allows redistribution in a public AGPL-3.0 repository**: CC0,
  CC BY or CC BY-SA, or our own work. Never a no-derivatives or non-commercial licence, and never a
  file whose licence you cannot find.
- **Credit the source even when the licence doesn't require it.** CC0 waives attribution, but
  `license.attribution` is still filled in.
- **CC0 does not cover trademarks.** A name such as #3DBenchy describes the file; never use it to
  brand a feature.

## Git LFS

- **Clones need Git LFS** (`git lfs install`, then `git lfs pull`). Without it, these files are
  small pointer files. The Vite plugin detects a pointer and stops the build with that command.
- **Pushing uploads LFS files through `.githooks/pre-push`.** `core.hooksPath` replaces Git LFS's own
  hook, so the repository's hook calls `git lfs pre-push` itself.
- **The free plan's LFS bandwidth is limited.** It is 10 GiB a month for the repository owner, and
  every clone, fork and CI checkout counts against it. Only CI jobs and image builds that read these
  files check them out with `lfs: true`.

## Commands

| Task | Command |
| --- | --- |
| Check the ship boundary | `pnpm --dir packages/sample-prints test` |
| Size and SHA-256 of a file | `python scripts/upload_metadata.py <file>` |
| Fetch the LFS files after cloning | `git lfs pull` |
