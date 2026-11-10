# @armada/slicer-engine

CuraEngine compiled to WebAssembly, as the web and desktop apps load it. The engine is built and released by
[armada-slicer-engine](https://github.com/Armada-Printer-Fleet-Management/armada-slicer-engine); this package
pins a release and gives the apps a loader and a Vite plugin.

```bash
python scripts/fetch_slicer_engine.py    # fetch and verify the pinned release into gen/
pnpm --dir packages/slicer-engine test   # smoke test: the engine loads and reports its version
```

How it fits together: [`docs/slicer-engine.html`](../../docs/slicer-engine.html). Rules: [`AGENTS.md`](AGENTS.md).
