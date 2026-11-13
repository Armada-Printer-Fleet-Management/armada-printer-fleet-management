# @armada/sample-prints

Real 3D print files, as models and G-code, for demos, training, tests and trying the API by hand.
Prints in `bundled/` ship inside the apps as models only; prints in `test/`, and all G-code, are for
development and CI only.

The files are stored in Git LFS:

```bash
git lfs install && git lfs pull          # once, after cloning
pnpm --dir packages/sample-prints test   # check that only bundled/ prints ship
```

Rules and how to add a print: [`AGENTS.md`](AGENTS.md).
