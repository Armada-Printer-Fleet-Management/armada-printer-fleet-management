import type createEngine from '../gen/CuraEngine';

export type SlicerEngine = Awaited<ReturnType<typeof createEngine>>;

export const SLICER_ENGINE_FOLDER = 'slicer-engine';

/** The base printer and extruder definitions shipped beside the engine. */
export const SLICER_DEFINITION_FILES = [
  'fdmprinter.def.json',
  'fdmextruder.def.json',
] as const;

/** Where the engine is served, resolved against the page, so main thread only. */
export function slicerEngineUrl(base: string): URL {
  return new URL(
    `${SLICER_ENGINE_FOLDER}/CuraEngine.js`,
    new URL(base, document.baseURI),
  );
}

export interface SlicerEngineOutput {
  print?: (line: string) => void;
  printErr?: (line: string) => void;
}

const engines = new Map<string, Promise<SlicerEngine>>();

/**
 * Loads the engine once per URL and returns that same instance on every call.
 * (Singleton per URL, in this realm: the page, or one worker.)
 *
 * The module is imported at run time from a plain URL rather than bundled, so the file shipped beside
 * the app can be replaced without rebuilding it.
 */
export function loadSlicerEngine(url: URL): Promise<SlicerEngine> {
  const key = url.href;
  let engine = engines.get(key);
  if (!engine) {
    engine = instantiateSlicerEngine(url);
    engines.set(key, engine);
    // A failed load is not cached, so the next call can try again.
    engine.catch(() => engines.delete(key));
  }
  return engine;
}

/**
 * A fresh engine every call, for a job that runs once and is thrown away with its worker. The engine
 * runs its command line only once per instance.
 */
export async function instantiateSlicerEngine(
  url: string | URL,
  output: SlicerEngineOutput = {},
): Promise<SlicerEngine> {
  const href = typeof url === 'string' ? url : url.href;
  const module = (await import(/* @vite-ignore */ href)) as {
    default: typeof createEngine;
  };
  return module.default({
    print: output.print ?? (() => undefined),
    printErr: output.printErr ?? (() => undefined),
  });
}
