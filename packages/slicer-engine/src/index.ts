import type createEngine from '../gen/CuraEngine';

export type SlicerEngine = Awaited<ReturnType<typeof createEngine>>;

export const SLICER_ENGINE_FOLDER = 'slicer-engine';

export function slicerEngineUrl(base: string): URL {
  return new URL(
    `${SLICER_ENGINE_FOLDER}/CuraEngine.js`,
    new URL(base, document.baseURI),
  );
}

const engines = new Map<string, Promise<SlicerEngine>>();

/**
 * Loads the engine once per URL and returns that same instance on every call.
 * (Singleton per URL)
 *
 * The module is imported at run time from a plain URL rather than bundled, so the file shipped beside
 * the app can be replaced without rebuilding it.
 */
export function loadSlicerEngine(url: URL): Promise<SlicerEngine> {
  const key = url.href;
  let engine = engines.get(key);
  if (!engine) {
    engine = instantiate(url);
    engines.set(key, engine);
    // A failed load is not cached, so the next call can try again.
    engine.catch(() => engines.delete(key));
  }
  return engine;
}

async function instantiate(url: URL): Promise<SlicerEngine> {
  const module = (await import(/* @vite-ignore */ url.href)) as {
    default: typeof createEngine;
  };
  return module.default({ print: () => undefined, printErr: () => undefined });
}
