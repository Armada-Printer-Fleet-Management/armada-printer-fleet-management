# @armada/slicer

Slices a model, or reads G-code that is already sliced, into the toolpaths, summary and problems
both the web and desktop apps show. Each job runs in its own worker on the
[slicer engine](../slicer-engine/README.md).

```bash
python scripts/generate_proto.py buf.gen.slicer_ts.yaml --node-modules packages/slicer/node_modules
pnpm --dir packages/slicer test
pnpm --dir packages/slicer generate:test-gcode   # regenerate the test print; needs the dev stack
```

How it fits together: [`docs/slicer-engine.html`](../../docs/slicer-engine.html). Rules:
[`AGENTS.md`](AGENTS.md).
